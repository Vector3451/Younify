"""
coordinator.py — Cluster Coordinator Service
=============================================
The single entry point for distributed inference. Workers auto-connect
and contribute compute. No job dispatch queue — inference is direct.

Flow:
  1. Workers start → automatically register with coordinator
  2. Head node runs llama-server with --rpc pointing at all workers
  3. Send POST /api/v1/generate → coordinator proxies to llama-server
     → llama-server distributes layers across workers → returns result
"""

import os
import time
import uuid
import threading
import socket

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

WORKER_TIMEOUT = 30


class WorkerRecord:
    def __init__(self, worker_id: str, host: str, port: int, vram_mb: int, ram_mb: int, label: str = ""):
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.vram_mb = vram_mb
        self.ram_mb = ram_mb
        self.label = label or f"worker-{worker_id[:8]}"
        self.last_heartbeat = time.time()
        self.layers_assigned = []
        self.status = "idle"
        self.tokens_processed = 0
        self._pending_reports: list[dict] = []

    def to_dict(self):
        return {
            "worker_id": self.worker_id,
            "host": self.host,
            "port": self.port,
            "vram_mb": self.vram_mb,
            "ram_mb": self.ram_mb,
            "label": self.label,
            "last_heartbeat": self.last_heartbeat,
            "layers_assigned": self.layers_assigned,
            "status": self.status,
            "tokens_processed": self.tokens_processed,
        }


class Coordinator:
    def __init__(self):
        self.workers: dict[str, WorkerRecord] = {}
        self._lock = threading.Lock()
        self._running = False

    def register_worker(self, host: str, port: int, vram_mb: int = 0, ram_mb: int = 0, label: str = "") -> str:
        worker_id = str(uuid.uuid4())
        with self._lock:
            self.workers[worker_id] = WorkerRecord(worker_id, host, port, vram_mb, ram_mb, label)
        return worker_id

    def heartbeat(self, worker_id: str) -> bool:
        with self._lock:
            record = self.workers.get(worker_id)
            if record is None:
                return False
            record.last_heartbeat = time.time()
            record.status = "ready"
            return True

    def unregister_worker(self, worker_id: str):
        with self._lock:
            self.workers.pop(worker_id, None)

    def record_inference(self, total_tokens: int):
        with self._lock:
            now = time.time()
            alive = [w for w in self.workers.values()
                     if now - w.last_heartbeat < WORKER_TIMEOUT]
            if not alive:
                return
            per_worker = total_tokens // len(alive)
            for w in alive:
                w.tokens_processed += per_worker
                w.status = "ready"

    def get_rpc_addrs(self) -> list[str]:
        with self._lock:
            alive = [w for w in self.workers.values()
                     if time.time() - w.last_heartbeat < WORKER_TIMEOUT]
            return [f"{w.host}:{w.port}" for w in alive]

    def get_cluster_status(self) -> dict:
        with self._lock:
            now = time.time()
            workers = []
            for w in self.workers.values():
                wdict = w.to_dict()
                wdict["alive"] = (now - w.last_heartbeat) < WORKER_TIMEOUT
                workers.append(wdict)
            return {
                "total_workers": len(workers),
                "alive_workers": sum(1 for w in workers if w["alive"]),
                "workers": workers,
            }

    def _monitor_loop(self):
        while self._running:
            time.sleep(5)
            with self._lock:
                now = time.time()
                for wid, w in list(self.workers.items()):
                    if now - w.last_heartbeat > WORKER_TIMEOUT:
                        w.status = "dead"

    def start_monitoring(self):
        self._running = True
        t = threading.Thread(target=self._monitor_loop, daemon=True)
        t.start()

    def stop_monitoring(self):
        self._running = False


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
coordinator_app = FastAPI(
    title="Younify Distributed Inference Coordinator",
    version="1.0.0",
    description="Workers auto-connect and pool compute. No job queue — direct inference.",
)

coordinator = Coordinator()
coordinator.start_monitoring()

LLAMA_SERVER_URL = os.environ.get("CLUSTER_INFERENCE_URL", "http://localhost:8080").rstrip("/")


# ── Worker Management ────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    host: str
    port: int = 5000
    vram_mb: int = 0
    ram_mb: int = 0
    label: str = ""


class HeartbeatRequest(BaseModel):
    worker_id: str


class TokenReport(BaseModel):
    label: str
    tokens: int
    prompt: str = ""


@coordinator_app.post("/api/v1/workers/register")
async def register(req: RegisterRequest):
    wid = coordinator.register_worker(req.host, req.port, req.vram_mb, req.ram_mb, req.label)
    return {"worker_id": wid, "status": "registered"}


@coordinator_app.post("/api/v1/workers/heartbeat")
async def worker_heartbeat(req: HeartbeatRequest):
    record = coordinator.workers.get(req.worker_id)
    if not record:
        raise HTTPException(404, "Worker not found")
    coordinator.heartbeat(req.worker_id)
    pending = []
    if record._pending_reports:
        pending = record._pending_reports
        record._pending_reports = []
    return {"status": "ok", "tokens_processed": record.tokens_processed, "reports": pending}


@coordinator_app.post("/api/v1/tokens/report")
async def report_tokens(req: TokenReport):
    with coordinator._lock:
        for w in coordinator.workers.values():
            if req.label in (w.label, w.host, w.worker_id):
                w.tokens_processed += req.tokens
                w._pending_reports.append({"tokens": req.tokens, "prompt": req.prompt[:120]})
                break
    return {"status": "recorded"}


@coordinator_app.delete("/api/v1/workers/{worker_id}")
async def unregister(worker_id: str):
    coordinator.unregister_worker(worker_id)
    return {"status": "unregistered"}


# ── Cluster Status ──────────────────────────────────────────────────────

@coordinator_app.get("/api/v1/cluster/status")
async def cluster_status():
    return coordinator.get_cluster_status()


@coordinator_app.get("/api/v1/cluster/rpc-addrs")
async def rpc_addrs():
    return {"addresses": coordinator.get_rpc_addrs()}


# ── Direct Inference (no job queue) ─────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "default"
    max_tokens: int = 2048
    temperature: float = 0.7


@coordinator_app.post("/api/v1/generate")
async def generate(req: GenerateRequest):
    url = f"{LLAMA_SERVER_URL}/v1/chat/completions"
    payload = {
        "model": req.model,
        "messages": [{"role": "user", "content": req.prompt}],
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        completion_tokens = usage.get("completion_tokens", 0)
        if completion_tokens > 0:
            coordinator.record_inference(completion_tokens)
        return data
    except requests.ConnectionError:
        raise HTTPException(503, "llama-server is not running. Start it with cluster-llama-entrypoint.sh")
    except requests.Timeout:
        raise HTTPException(504, "Inference timed out")
    except requests.RequestException as e:
        raise HTTPException(502, f"Inference failed: {e}")


@coordinator_app.get("/api/v1/health")
async def health():
    alive = len(coordinator.get_rpc_addrs())
    return {
        "service": "Younify Cluster Coordinator",
        "version": "1.0.0",
        "workers_alive": alive,
        "llama_server": LLAMA_SERVER_URL,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("COORDINATOR_PORT", 8050))
    uvicorn.run(coordinator_app, host="0.0.0.0", port=port)
