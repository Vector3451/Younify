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
TASK_QUEUE = "inference_tasks"
RESULT_PREFIX = "inference_result:"

# ---------------------------------------------------------------------------
# Coordinator (for token reporting to cluster workers)
# ---------------------------------------------------------------------------
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "").rstrip("/")


def connect_redis():
    client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
        decode_responses=True,
        protocol=2,  # Force RESP2 for compatibility with older redis-py clients
    )
    client.ping()
    return client


# ---------------------------------------------------------------------------
# Task processing
# ---------------------------------------------------------------------------
def process_task(r: redis.Redis, task: dict):
    job_id = task["job_id"]
    prompt = task["prompt"]
    max_tokens = task.get("max_tokens", 2048)
    temperature = task.get("temperature", 0.7)
    model_id = task.get("model_id", "default-model")

    logs: list[str] = []

    def log(msg: str):
        logs.append(msg)
        print(msg)

    # Resolve provider for logging
    provider_name, model_name = parse_model_id(model_id)
    log(f"[WORKER] Job {job_id} | Provider: {provider_name} | Model: {model_name}")
    log(f"[WORKER] Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

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


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    print("=" * 60)
    print("  Distributed AI Inference Worker (Multi-Provider)")
    print("=" * 60)
    print(f"  Redis:    {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
    print(f"  Queue:    {TASK_QUEUE}")
    print(f"  Worker:   {worker_id}")
    print("=" * 60)

    r = None
    last_heartbeat = 0
    while True:
        try:
            if r is None:
                r = connect_redis()
                print("[WORKER] Connected to Redis. Waiting for tasks...")

            # Write heartbeat every 10 seconds
            now = time.time()
            if now - last_heartbeat >= 10:
                r.setex(f"worker:heartbeat:{worker_id}", 30, json.dumps({
                    "host": socket.gethostname(),
                    "model": os.environ.get("OLLAMA_MODEL", "unknown"),
                    "last_seen": now,
                }))
                last_heartbeat = now

            item = r.brpop(TASK_QUEUE, timeout=5)
            if item:
                _, task_json = item
                task = json.loads(task_json)
                process_task(r, task)

        except KeyboardInterrupt:
            print("\n[WORKER] Shutting down.")
            # Clean up heartbeat on exit
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
