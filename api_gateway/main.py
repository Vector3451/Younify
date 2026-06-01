"""
API Gateway + Web UI — Distributed AI Inference System
========================================================
Receives inference requests, enqueues them to Redis,
serves a web dashboard, and lets workers process jobs.

Usage:
    uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000
    Then open http://localhost:8000 in your browser.
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
TASK_QUEUE = "inference_tasks"
RESULT_PREFIX = "inference_result:"


def get_redis():
    """Create a fresh Redis connection."""
    return redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
    )


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
    api_key: Optional[str] = Field(None, description="Optional API key for the provider.")


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


@app.get("/api/v1/models", summary="List available models")
async def list_models():
    """Probe Ollama for available models. Returns empty list if Ollama is unreachable."""
    import requests as req
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        resp = req.get(f"{ollama_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            return {
                "ollama": [m["name"] for m in models],
                "openrouter": [],
                "openai": [],
                "vllm": [],
            }
    except Exception:
        pass
    return {"ollama": [], "openrouter": [], "openai": [], "vllm": []}


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
    task_payload = {
        "job_id": job_id,
        "prompt": request.prompt,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "model_id": request.model_id,
        "api_key": request.api_key,
        "submitted_at": time.time(),
    }

    try:
        client.lpush(TASK_QUEUE, json.dumps(task_payload))
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_gateway.main:app", host="0.0.0.0", port=8000, reload=True)
