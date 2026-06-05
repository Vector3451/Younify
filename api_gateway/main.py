"""
API Gateway + Web UI — Distributed AI Inference System
========================================================
Receives inference requests, enqueues them to Redis,
serves a web dashboard, and lets workers process jobs.

Usage:
    uvicorn api_gateway.main:app --host 0.0.0.0 --port 8090
    Then open http://localhost:8090 in your browser.
"""

import json
import os
import time
from typing import Optional

import fastapi
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uuid

import redis
from redis.exceptions import ConnectionError as RedisConnectionError

from .dashboard import DASHBOARD_HTML

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))
RESULT_PREFIX = "inference_result:"

# Priority queues matching worker/worker.py
QUEUE_HIGH = "inference_tasks:high"
QUEUE_DEFAULT = "inference_tasks:default"
QUEUE_LOW = "inference_tasks:low"


_redis_pool = None

def get_redis():
    """Return a shared Redis client with connection pooling."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_keepalive=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=20,
        )
    return redis.Redis(connection_pool=_redis_pool)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Distributed AI Inference Gateway",
    version="1.0.0",
    description="Enqueues inference jobs to a Redis-backed queue for distributed processing.",
)


@app.on_event("startup")
def startup_event():
    """Wait for Redis to become available (up to 30 seconds)."""
    for attempt in range(30):
        try:
            client = get_redis()
            client.ping()
            print("[API GATEWAY] Connected to Redis.")
            return
        except RedisConnectionError:
            print(
                f"[API GATEWAY] Redis not ready (attempt {attempt + 1}/30). "
                f"Retrying in 1s..."
            )
            time.sleep(1)
    print("[API GATEWAY] WARNING: Could not connect to Redis after 30 attempts.")


# ---------------------------------------------------------------------------
# Pydantic models (matches api_contract.md)
# ---------------------------------------------------------------------------
class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The instruction or query for the model.")
    max_tokens: int = Field(2048, ge=1, description="Maximum tokens to generate.")
    temperature: float = Field(
        0.7, ge=0.0, le=1.0, description="Sampling temperature."
    )
    model_id: str = Field(
        "ollama/llama3",
        description='Provider-prefixed model ID. Format: "provider/model". '
        'Providers: ollama, openrouter, openai, vllm. '
        'Example: "ollama/llama3:7b".',
    )
    api_key: Optional[str] = Field(None, description="Deprecated — Younify uses Ollama for inference.")
    priority: str = Field(
        "default",
        description='Task priority: "high", "default", or "low". '
        'High-priority tasks are processed before default and low.',
    )


class JobAcceptedResponse(BaseModel):
    job_id: str
    status: str = "QUEUED"
    message: str


class JobResult(BaseModel):
    model: str = ""
    completion: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[JobResult] = None
    error: Optional[str] = None
    logs: Optional[list[str]] = None
    started: Optional[float] = None
    completed: Optional[float] = None


class ErrorResponse(BaseModel):
    error: str
    detail: str


# ---------------------------------------------------------------------------
# Web Dashboard
# ---------------------------------------------------------------------------
@app.get("/", response_class=fastapi.responses.HTMLResponse, include_in_schema=False)
async def dashboard():
    """Serve the web dashboard."""
    return DASHBOARD_HTML


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/v1/health", summary="Health check")
async def health_check():
    """Check API and Redis connectivity."""
    redis_ok = False
    try:
        client = get_redis()
        client.ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "service": "AI Inference Gateway",
        "version": "1.0.0",
        "redis_connected": redis_ok,
    }


@app.get("/api/v1/models", summary="List available Ollama models")
async def list_models():
    """Probe Ollama for available models. Returns empty list if Ollama is unreachable."""
    import requests as req
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = req.get(f"{base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return {
                "ollama": [m["name"] for m in models],
                "status": "ok",
                "count": len(models),
            }
        return {"ollama": [], "status": f"ollama returned {resp.status_code}", "count": 0}
    except req.ConnectionError as e:
        return {
            "ollama": [],
            "status": f"Ollama unreachable ({base_url}): {e}",
            "count": 0,
            "fix": "Run 'ollama serve' to start Ollama",
        }
    except Exception as e:
        return {"ollama": [], "status": f"error: {e}", "count": 0}


@app.post(
    "/api/v1/generate",
    response_model=JobAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an inference job",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request payload"},
        503: {"model": ErrorResponse, "description": "Redis unavailable"},
    },
)
async def submit_job(request: PromptRequest):
    """Accept an inference job, enqueue it to Redis, and return a job ID."""
    client = get_redis()

    job_id = str(uuid.uuid4())

    # Validate priority
    priority = request.priority.lower()
    if priority not in ("high", "default", "low"):
        priority = "default"
    queue_map = {"high": QUEUE_HIGH, "default": QUEUE_DEFAULT, "low": QUEUE_LOW}
    target_queue = queue_map[priority]

    task_payload = {
        "job_id": job_id,
        "prompt": request.prompt,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "model_id": request.model_id,
        "api_key": request.api_key,
        "priority": priority,
        "submitted_at": time.time(),
    }

    try:
        client.lpush(target_queue, json.dumps(task_payload))
    except RedisConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enqueue task. Redis connection lost.",
        )

    client.set(
        f"{RESULT_PREFIX}{job_id}",
        json.dumps({
            "job_id": job_id,
            "status": "QUEUED",
            "result": None,
            "error": None,
            "logs": None,
            "started": None,
            "completed": None,
            "submitted_at": task_payload["submitted_at"],
        }),
    )

    return JobAcceptedResponse(
        job_id=job_id,
        status="QUEUED",
        message="Job received and queued. Poll /api/v1/status/{job_id} for results.",
    )


@app.get(
    "/api/v1/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Check job status",
    responses={404: {"model": ErrorResponse}},
)
async def get_status(job_id: str):
    """Return the current status of a previously submitted job."""
    client = get_redis()

    raw = client.get(f"{RESULT_PREFIX}{job_id}")
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )

    data = json.loads(raw)
    return data


# ---------------------------------------------------------------------------
# Cluster Coordinator Proxy Endpoints
# ---------------------------------------------------------------------------
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "http://localhost:8050")


@app.get("/api/v1/cluster/status", summary="Cluster coordinator status")
async def cluster_status():
    """Proxy to coordinator for cluster status."""
    import requests as req
    try:
        resp = req.get(f"{COORDINATOR_URL}/api/v1/cluster/status", timeout=5)
        return resp.json()
    except Exception:
        return {
            "total_workers": 0,
            "alive_workers": 0,
            "workers": [],
            "error": "Coordinator unreachable",
        }


@app.get("/api/v1/cluster/workers", summary="Scan for active workers")
async def cluster_workers():
    """Proxy to coordinator for the cluster worker list."""
    import requests as req
    try:
        resp = req.get(f"{COORDINATOR_URL}/api/v1/cluster/status", timeout=5)
        return resp.json()
    except Exception:
        return {
            "total_workers": 0,
            "alive_workers": 0,
            "workers": [],
            "error": "Coordinator unreachable",
        }


@app.get("/api/v1/cluster/rpc-addrs", summary="Cluster RPC addresses")
async def cluster_rpc_addrs():
    """Proxy to coordinator for RPC addresses."""
    import requests as req
    try:
        resp = req.get(f"{COORDINATOR_URL}/api/v1/cluster/rpc-addrs", timeout=5)
        return resp.json()
    except Exception:
        return {"addresses": [], "error": "Coordinator unreachable"}


# ---------------------------------------------------------------------------
# OpenAI-Compatible Endpoints (Hermes / Open WebUI / Continue.dev etc.)
# ---------------------------------------------------------------------------
# These endpoints match the OpenAI Chat Completions API format so that any
# OpenAI-compatible client can use Younify as a drop-in provider.
#
# Flow:
#   Hermes → api_gateway:3000/v1/chat/completions
#     ├─ Coordinator available? → proxy to coordinator:8050/api/v1/generate
#     └─ else → proxy to Ollama:11434/v1/chat/completions
# ---------------------------------------------------------------------------


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Model ID, e.g. ollama/llama3 or cluster/my-model")
    messages: list[dict] = Field(..., description="Array of message objects with role + content")
    max_tokens: int = Field(2048, ge=1, description="Maximum tokens to generate")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: bool = Field(False, description="Whether to stream the response")


@app.post(
    "/v1/chat/completions",
    summary="OpenAI-compatible chat completions",
    description="Accepts the standard OpenAI Chat Completions request body. Routes through the "
    "Younify coordinator when available, otherwise falls back to Ollama.",
)
async def openai_chat_completions(req: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint.

    Extracts the last user message from `messages`, then routes through:
      1. Coordinator (cluster/distributed inference) if reachable
      2. Ollama (local inference) as fallback
    """
    # Extract prompt from messages
    prompt = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle multi-part content (text + images etc.)
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        prompt = part.get("text", "")
                        break
            else:
                prompt = content or ""
            break

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found in messages array",
        )

    # Parse model ID → extract provider and model name
    model_id = req.model
    provider = "ollama"
    model_name = model_id
    if "/" in model_id:
        provider, _, model_name = model_id.partition("/")

    import requests as req_lib

    # ── Try coordinator first ─────────────────────────────────────────────
    if provider == "cluster" or COORDINATOR_URL:
        coordinator_base = COORDINATOR_URL.rstrip("/")
        try:
            resp = req_lib.post(
                f"{coordinator_base}/api/v1/generate",
                json={
                    "prompt": prompt,
                    "model": model_name,
                    "max_tokens": req.max_tokens,
                    "temperature": req.temperature,
                },
                timeout=600,
            )
            resp.raise_for_status()
            data = resp.json()
            # Coordinator returns OpenAI-compatible format — patch model name
            data["model"] = req.model
            return data
        except req_lib.ConnectionError:
            # Coordinator unreachable — fall through to Ollama
            pass
        except req_lib.Timeout:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Coordinator inference timed out",
            )
        except req_lib.HTTPError:
            # Coordinator returned an error (e.g. 503 from missing llama-server)
            # — fall through to Ollama
            pass
        except req_lib.RequestException as e:
            # Genuine request error (e.g. invalid URL) — surface to caller
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Coordinator inference failed: {e}",
            )

    # ── Fallback: proxy to Ollama ─────────────────────────────────────────
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    try:
        resp = req_lib.post(
            f"{ollama_base}/v1/chat/completions",
            json={
                "model": model_name,
                "messages": req.messages,
                "max_tokens": req.max_tokens,
                "temperature": req.temperature,
                "stream": False,
            },
            timeout=600,
        )
        resp.raise_for_status()
        data = resp.json()
        data["model"] = req.model
        return data
    except req_lib.ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running. Start it with: ollama serve",
        )
    except req_lib.Timeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Ollama inference timed out",
        )
    except req_lib.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama inference failed: {e}",
        )


@app.get(
    "/v1/models",
    summary="OpenAI-compatible models list",
    description="Returns available models in OpenAI format for client discovery.",
)
async def openai_list_models():
    """List available models in OpenAI-compatible format."""
    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    data_models = []
    import requests as req_lib
    try:
        resp = req_lib.get(f"{ollama_base}/api/tags", timeout=5)
        if resp.status_code == 200:
            for m in resp.json().get("models", []):
                name = m.get("name", "unknown")
                data_models.append({
                    "id": f"ollama/{name}",
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ollama",
                })
    except Exception:
        pass

    return {"object": "list", "data": data_models}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_gateway.main:app", host="0.0.0.0", port=8090, reload=True)
