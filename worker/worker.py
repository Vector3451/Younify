"""
Worker — Distributed AI Inference System
=========================================
Connects to Redis, blocks on the task queue,
processes inference jobs using configurable AI providers,
and writes results back.

Providers (model_id format):
    ollama/llama3:7b           → Local Ollama server
    openrouter/meta/llama-70b   → OpenRouter API
    openai/gpt-4o              → OpenAI API
    vllm/meta-llama/Llama-3-8B → Local vLLM server

Environment variables:
    REDIS_HOST          (default: localhost)
    REDIS_PORT          (default: 6379)
    OLLAMA_BASE_URL     (default: http://localhost:11434)
    OPENROUTER_API_KEY  (required for OpenRouter)
    OPENAI_API_KEY      (required for OpenAI)
    VLLM_BASE_URL       (default: http://localhost:8000)

Features:
    - Priority queues (high / default / low)
    - Worker auto-recovery: stale processing locks re-queued on startup
    - Connection pooling with health checks
    - Real-time heartbeat with resource metrics

Usage:
    python worker.py
"""

import json
import time
import sys
import os
import socket

import requests
import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from providers import run_inference, parse_model_id

# ---------------------------------------------------------------------------
# Redis setup
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
RESULT_PREFIX = "inference_result:"
PROCESSING_LOCK_PREFIX = "processing:lock:"
PROCESSING_TTL = 300  # 5 minutes before a task is considered stale

# Priority queues (checked in order)
QUEUE_HIGH = "inference_tasks:high"
QUEUE_DEFAULT = "inference_tasks:default"
QUEUE_LOW = "inference_tasks:low"
TASK_QUEUES = [QUEUE_HIGH, QUEUE_DEFAULT, QUEUE_LOW]

# ---------------------------------------------------------------------------
# Coordinator (for token reporting to cluster workers)
# ---------------------------------------------------------------------------
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "").rstrip("/")

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
_redis_pool = None


def get_redis():
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            protocol=2,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return redis.Redis(connection_pool=_redis_pool)


# ---------------------------------------------------------------------------
# Stale task reclaimer — re-queue tasks from crashed workers
# ---------------------------------------------------------------------------
def reclaim_stale_tasks(r: redis.Redis):
    reclaimed = 0
    cursor = 0
    while True:
        cursor, keys = r.scan(cursor, match=f"{PROCESSING_LOCK_PREFIX}*", count=100)
        for key in keys:
            raw = r.get(key)
            if raw is None:
                continue
            try:
                lock = json.loads(raw)
                lock_age = time.time() - lock.get("started_at", 0)
                if lock_age >= PROCESSING_TTL:
                    job_id = lock["job_id"]
                    task_json = r.getdel(f"processing:task:{job_id}")
                    if task_json:
                        # Re-queue to default queue
                        r.lpush(QUEUE_DEFAULT, task_json)
                        reclaimed += 1
                        print(f"[RECLAIM] Re-queued stale job {job_id} ({lock_age:.0f}s old)")
                    r.delete(key)
            except (json.JSONDecodeError, KeyError):
                r.delete(key)
        if cursor == 0:
            break
    return reclaimed


# ---------------------------------------------------------------------------
# Task processing
# ---------------------------------------------------------------------------
def process_task(r: redis.Redis, task: dict):
    job_id = task["job_id"]
    prompt = task["prompt"]
    max_tokens = task.get("max_tokens", 2048)
    temperature = task.get("temperature", 0.7)
    model_id = task.get("model_id", "default-model")
    priority = task.get("priority", "default")

    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)
        print(msg)

    provider_name, model_name = parse_model_id(model_id)
    log(f"[WORKER] Job {job_id} | Provider: {provider_name} | Model: {model_name} | Priority: {priority}")
    log(f"[WORKER] Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    # Set processing lock (auto-expires, so crashed tasks get re-queued)
    lock_key = f"{PROCESSING_LOCK_PREFIX}{job_id}"
    lock = json.dumps({
        "job_id": job_id,
        "worker": f"{socket.gethostname()}-{os.getpid()}",
        "started_at": time.time(),
        "priority": priority,
    })
    r.set(lock_key, lock, ex=PROCESSING_TTL)

    # Update status → PROCESSING
    r.set(f"{RESULT_PREFIX}{job_id}", json.dumps({
        "job_id": job_id,
        "status": "PROCESSING",
        "result": None,
        "error": None,
        "logs": logs,
        "started": time.time(),
        "completed": None,
    }))

    try:
        result = run_inference(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=task.get("api_key"),
        )

        token_count = result.get('completion_tokens', 0)
        log(f"[WORKER] Job {job_id} -> COMPLETED ({token_count} tokens)")

        r.set(f"{RESULT_PREFIX}{job_id}", json.dumps({
            "job_id": job_id,
            "status": "COMPLETED",
            "result": result,
            "error": None,
            "logs": logs,
            "started": time.time(),
            "completed": time.time(),
        }))

        if COORDINATOR_URL and token_count > 0:
            try:
                requests.post(
                    f"{COORDINATOR_URL}/api/v1/tokens/report",
                    json={"label": socket.gethostname(), "tokens": token_count, "prompt": prompt},
                    timeout=3,
                )
            except requests.RequestException:
                pass

    except ValueError as e:
        error_msg = f"Configuration error: {e}"
        log(f"[WORKER] Job {job_id} -> FAILED: {error_msg}")
        r.set(f"{RESULT_PREFIX}{job_id}", json.dumps({
            "job_id": job_id,
            "status": "FAILED",
            "result": None,
            "error": error_msg,
            "logs": logs,
            "started": time.time(),
            "completed": time.time(),
        }))
    except Exception as e:
        log(f"[WORKER] Job {job_id} -> FAILED: {e}")
        r.set(f"{RESULT_PREFIX}{job_id}", json.dumps({
            "job_id": job_id,
            "status": "FAILED",
            "result": None,
            "error": str(e),
            "logs": logs,
            "started": time.time(),
            "completed": time.time(),
        }))
    finally:
        # Remove processing lock so reclaimer doesn't re-queue a completed job
        r.delete(lock_key)
        r.delete(f"processing:task:{job_id}")


# ---------------------------------------------------------------------------
# Micro-batch: collect tasks from queue, process with warm provider
# ---------------------------------------------------------------------------
def collect_tasks(r: redis.Redis, max_batch: int = 3) -> list[tuple[str, dict]]:
    """Collect tasks from priority queues.
    Pops one task via brpop (short timeout), then tries to drain more
    via non-blocking lpop for micro-batching."""
    tasks = []
    for q in TASK_QUEUES:
        # Blocking pop for first task
        item = r.brpop(q, timeout=1)
        if item:
            queue_name, task_json = item
            tasks.append((queue_name, json.loads(task_json)))
            # Non-blocking drain of same queue
            for _ in range(max_batch - 1):
                extra = r.lpop(q)
                if extra is None:
                    break
                tasks.append((q, json.loads(extra)))
            break
    return tasks


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    print("=" * 60)
    print("  Distributed AI Inference Worker (Multi-Provider)")
    print("=" * 60)
    print(f"  Redis:    {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    print(f"  Queues:   {', '.join(TASK_QUEUES)} (priority order)")
    print(f"  Worker:   {worker_id}")
    print("=" * 60)

    r = None
    provider = None
    warm_model = os.environ.get("OLLAMA_MODEL", "")
    last_heartbeat = 0
    first_connect = True

    while True:
        try:
            if r is None:
                r = get_redis()
                print("[WORKER] Connected to Redis.")

                reclaimed = reclaim_stale_tasks(r)
                if reclaimed > 0:
                    print(f"[WORKER] Reclaimed {reclaimed} stale task(s) from crashed workers")

                if first_connect:
                    # Create provider once and warm the model
                    if warm_model:
                        from providers import get_provider, parse_model_id
                        pname, mname = parse_model_id(warm_model)
                        provider = get_provider(pname)
                        if provider.warmup(mname):
                            print(f"[WORKER] Model '{mname}' preloaded and kept warm")
                        else:
                            provider = None
                    print("[WORKER] Waiting for tasks...")
                    first_connect = False

            now = time.time()
            if now - last_heartbeat >= 10:
                heartbeat = {
                    "host": socket.gethostname(),
                    "model": warm_model or os.environ.get("OLLAMA_MODEL", "unknown"),
                    "last_seen": now,
                }
                try:
                    import psutil
                    heartbeat["cpu_percent"] = psutil.cpu_percent(interval=0.2)
                    mem = psutil.virtual_memory()
                    heartbeat["ram_available_mb"] = mem.available // (1024 * 1024)
                    heartbeat["ram_percent"] = mem.percent
                except ImportError:
                    pass
                r.set(f"worker:heartbeat:{worker_id}", json.dumps(heartbeat), ex=30)
                last_heartbeat = now

            # Collect tasks in micro-batches (up to 3 at a time)
            batch = collect_tasks(r, max_batch=3)
            if batch:
                print(f"[WORKER] Processing batch of {len(batch)} task(s)")
                for queue_name, task in batch:
                    job_id = task.get("job_id", "?")
                    r.set(f"processing:task:{job_id}", json.dumps(task), ex=PROCESSING_TTL)
                    process_task(r, task)

        except KeyboardInterrupt:
            print("\n[WORKER] Shutting down.")
            try:
                if r is not None:
                    r.delete(f"worker:heartbeat:{worker_id}")
            except Exception:
                pass
            sys.exit(0)
        except RedisConnectionError as e:
            print(f"[WORKER] Redis connection lost: {e}. Retrying in 5s...")
            r = None
            time.sleep(5)
        except Exception as e:
            print(f"[WORKER] Unexpected error: {e}. Reconnecting...")
            r = None
            time.sleep(2)


if __name__ == "__main__":
    main()
