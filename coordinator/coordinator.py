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

Features:
    - Resource-aware dispatch: workers report real-time CPU%, GPU%, VRAM
    - Heterogeneous worker support: GPU name, compute capability tracked
    - Health monitoring with stale worker detection
"""

import os
import time
import uuid
import hashlib
import threading
import socket
from collections import OrderedDict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

WORKER_TIMEOUT = 30
CACHE_MAX_SIZE = 128
CACHE_TTL = 300  # 5 minutes


class WorkerRecord:
    def __init__(self, worker_id: str, host: str, port: int,
                 vram_mb: int, ram_mb: int, label: str = "",
                 gpu_name: str = "", gpu_compute_cap: str = ""):
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
        # GPU metadata (heterogeneous support)
        self.gpu_name = gpu_name
        self.gpu_compute_cap = gpu_compute_cap
        # Real-time resource metrics (updated every heartbeat)
        self.cpu_percent = 0.0
        self.gpu_util = 0.0
        self.vram_free_mb = vram_mb
        self.ram_available_mb = ram_mb
        self.ram_percent = 0

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
            "gpu_name": self.gpu_name,
            "gpu_compute_cap": self.gpu_compute_cap,
            "cpu_percent": self.cpu_percent,
            "gpu_util": self.gpu_util,
            "vram_free_mb": self.vram_free_mb,
            "ram_available_mb": self.ram_available_mb,
            "ram_percent": self.ram_percent,
        }


class Coordinator:
    def __init__(self):
        self.workers: dict[str, WorkerRecord] = {}
        self._lock = threading.Lock()
        self._running = False

    def register_worker(self, host: str, port: int, vram_mb: int = 0, ram_mb: int = 0,
                         label: str = "", gpu_name: str = "", gpu_compute_cap: str = "") -> str:
        worker_id = str(uuid.uuid4())
        with self._lock:
            self.workers[worker_id] = WorkerRecord(
                worker_id, host, port, vram_mb, ram_mb, label,
                gpu_name=gpu_name, gpu_compute_cap=gpu_compute_cap,
            )
        return worker_id

    def heartbeat(self, worker_id: str, cpu_percent: float = 0, gpu_util: float = 0,
                  vram_free_mb: int = 0, ram_available_mb: int = 0, ram_percent: int = 0) -> bool:
        with self._lock:
            record = self.workers.get(worker_id)
            if record is None:
                return False
            record.last_heartbeat = time.time()
            record.status = "ready"
            # Update real-time resource metrics
            if cpu_percent:
                record.cpu_percent = cpu_percent
            if gpu_util:
                record.gpu_util = gpu_util
            if vram_free_mb:
                record.vram_free_mb = vram_free_mb
            if ram_available_mb:
                record.ram_available_mb = ram_available_mb
            if ram_percent:
                record.ram_percent = ram_percent
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
# Result cache (simple LRU with TTL)
# ---------------------------------------------------------------------------
class ResultCache:
    def __init__(self, max_size: int = CACHE_MAX_SIZE, ttl: int = CACHE_TTL):
        self._cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.Lock()

    def _make_key(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        raw = f"{prompt}|{model}|{max_tokens}|{temperature}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, prompt: str, model: str, max_tokens: int, temperature: float) -> dict | None:
        key = self._make_key(prompt, model, max_tokens, temperature)
        with self._lock:
            if key not in self._cache:
                return None
            timestamp, data = self._cache[key]
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return data

    def set(self, prompt: str, model: str, max_tokens: int, temperature: float, data: dict):
        key = self._make_key(prompt, model, max_tokens, temperature)
        with self._lock:
            self._cache[key] = (time.time(), data)
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def stats(self) -> dict:
        with self._lock:
            return {"size": len(self._cache), "max_size": self._max_size, "ttl": self._ttl}


result_cache = ResultCache()


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
    gpu_name: str = ""
    gpu_compute_cap: str = ""


class HeartbeatRequest(BaseModel):
    worker_id: str
    cpu_percent: float = 0
    gpu_util: float = 0
    vram_free_mb: int = 0
    ram_available_mb: int = 0
    ram_percent: int = 0


class TokenReport(BaseModel):
    label: str
    tokens: int
    prompt: str = ""


@coordinator_app.post("/api/v1/workers/register")
async def register(req: RegisterRequest):
    wid = coordinator.register_worker(
        req.host, req.port, req.vram_mb, req.ram_mb, req.label,
        gpu_name=req.gpu_name, gpu_compute_cap=req.gpu_compute_cap,
    )
    return {"worker_id": wid, "status": "registered"}


@coordinator_app.post("/api/v1/workers/heartbeat")
async def worker_heartbeat(req: HeartbeatRequest):
    record = coordinator.workers.get(req.worker_id)
    if not record:
        raise HTTPException(404, "Worker not found")
    coordinator.heartbeat(
        req.worker_id,
        cpu_percent=req.cpu_percent,
        gpu_util=req.gpu_util,
        vram_free_mb=req.vram_free_mb,
        ram_available_mb=req.ram_available_mb,
        ram_percent=req.ram_percent,
    )
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


@coordinator_app.get("/api/v1/cluster/layer-plan")
async def layer_plan(total_layers: int = 80, model_size_gb: float = 8.0):
    """
    Compute optimal layer distribution across all workers.

    Uses each worker's reported VRAM and RAM to figure out how many
    model layers can fit on each GPU. The remainder spill to system
    RAM on the head node.

    Query params:
        total_layers   — total number of layers in the model (default 80)
        model_size_gb  — total model file size in GB (default 8.0)
    """
    now = time.time()
    gb_per_layer = model_size_gb / max(total_layers, 1)

    plan = []
    assigned = 0
    head_gpu_layers_estimate = 0

    # Collect head-node VRAM if available on this machine
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            vrams = [int(x.strip()) for x in result.stdout.strip().split("\n") if x.strip()]
            head_vram_mb = sum(vrams)
            # Reserve 10% headroom for runtime buffers
            usable_vram_mb = int(head_vram_mb * 0.9)
            head_gpu_layers_estimate = int(usable_vram_mb / 1024 / gb_per_layer) if gb_per_layer > 0 else 0
            head_gpu_layers_estimate = min(head_gpu_layers_estimate, total_layers)
    except Exception:
        head_vram_mb = 0

    with coordinator._lock:
        alive = [w for w in coordinator.workers.values()
                 if now - w.last_heartbeat < WORKER_TIMEOUT]

        # Sort by compute capability descending (heterogeneous support)
        alive.sort(key=lambda w: (w.gpu_compute_cap or "0", w.vram_mb), reverse=True)

        for w in alive:
            # Use real-time VRAM from heartbeat if available, else registration VRAM
            effective_vram = w.vram_free_mb if w.vram_free_mb > 0 else w.vram_mb
            usable_vram_mb = effective_vram * 0.9
            layers_in_gpu = int(usable_vram_mb / 1024 / gb_per_layer) if gb_per_layer > 0 else 0
            layers_in_gpu = max(min(layers_in_gpu, total_layers - assigned), 0)
            plan.append({
                "worker_id": w.worker_id,
                "host": w.host,
                "port": w.port,
                "vram_mb": w.vram_mb,
                "vram_free_mb": w.vram_free_mb,
                "ram_mb": w.ram_mb,
                "gpu_name": w.gpu_name,
                "gpu_compute_cap": w.gpu_compute_cap,
                "cpu_percent": w.cpu_percent,
                "gpu_layers": layers_in_gpu,
                "device": "gpu" if layers_in_gpu > 0 else "cpu",
            })
            assigned += layers_in_gpu

    total_gpu = sum(p["gpu_layers"] for p in plan) + head_gpu_layers_estimate
    cpu_layers = max(total_layers - total_gpu, 0)

    return {
        "total_layers": total_layers,
        "model_size_gb": model_size_gb,
        "gb_per_layer": round(gb_per_layer, 4),
        "head_node": {
            "vram_mb": head_vram_mb,
            "gpu_layers": head_gpu_layers_estimate,
        },
        "workers": plan,
        "total_gpu_layers": total_gpu,
        "cpu_layers": cpu_layers,
        "suggested_n_gpu_layers": min(head_gpu_layers_estimate, total_layers),
    }


# ── Direct Inference (no job queue) ─────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "default"
    max_tokens: int = 2048
    temperature: float = 0.7


@coordinator_app.post("/api/v1/generate")
async def generate(req: GenerateRequest):
    # Check cache first
    cached = result_cache.get(req.prompt, req.model, req.max_tokens, req.temperature)
    if cached is not None:
        return cached

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
        # Cache the result
        result_cache.set(req.prompt, req.model, req.max_tokens, req.temperature, data)
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
        "cache": result_cache.stats(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("COORDINATOR_PORT", 8050))
    uvicorn.run(coordinator_app, host="0.0.0.0", port=port)
