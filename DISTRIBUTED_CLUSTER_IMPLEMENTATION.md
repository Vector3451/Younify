# Distributed Inference Cluster — Implementation Plan

## Overview

This document describes how to extend Younify so that **multiple machines pool their compute resources to run a single AI model together** — like Apple's Private Cloud Compute cluster mode. Workers contribute their VRAM/RAM to hold model layers, and token activations flow through the pipeline.

---

## Architecture

```
                              ┌──────────────────────────────────────┐
                              │         HEAD NODE                   │
                              │                                     │
                              │  ┌──────────────────────────────┐   │
                              │  │  Coordinator :8050            │   │
                              │  │  - worker registry            │   │
                              │  │  - POST /api/v1/generate      │   │
                              │  │  - GET  /api/v1/cluster/status│   │
                              │  └──────────┬───────────────────┘   │
                              │             │ proxies to             │
                              │  ┌──────────▼───────────────────┐   │
                              │  │  llama-server :8080           │   │
                              │  │  --rpc w1:5000               │   │
                              │  │  --rpc w2:5000               │   │
                              │  │  --rpc w3:5000               │   │
                              │  └──────────────────────────────┘   │
                              └──────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
          ┌─────────▼─────────┐   ┌──────────▼──────────┐   ┌─────────▼─────────┐
          │  WORKER NODE 1    │   │  WORKER NODE 2      │   │  WORKER NODE 3    │
          │                   │   │                     │   │                   │
          │  ┌─────────────┐  │   │  ┌─────────────┐   │   │  ┌─────────────┐  │
          │  │ llama-rpc   │  │   │  │ llama-rpc   │   │   │  │ llama-rpc   │  │
          │  │ -server     │  │   │  │ -server     │   │   │  │ -server     │  │
          │  │ :5000       │  │   │  │ :5000       │   │   │  │ :5000       │  │
          │  └─────────────┘  │   │  └─────────────┘   │   │  └─────────────┘  │
          │                   │   │                     │   │                   │
          │  Holds layers 1-10│   │  Holds layers 11-20 │   │  Holds layers 21-30
          └───────────────────┘   └─────────────────────┘   └───────────────────┘
```

### Key Difference from Standard Younify

**No job dispatch, no Redis queue.** This is not a producer-consumer system. Workers auto-connect and contribute their GPU/CPU to run a _single shared model_. Inference is synchronous and direct:

1. Workers run `cluster_worker.py` → auto-starts `llama-rpc-server` → registers with coordinator
2. Head node runs `cluster-llama-entrypoint.sh` → fetches RPC addrs → starts `llama-server` with all workers
3. Client sends `POST /api/v1/generate` to coordinator → coordinator proxies to `llama-server` → `llama-server` distributes layers across workers via RPC → returns result

### How Inference Flows

```
Client → POST /api/v1/generate → Coordinator :8050
                                         ↓
                              POST /v1/chat/completions → llama-server:8080
                                         ↓
                              llama-server shards the model:
                                layer 1  → worker1 (via RPC)
                                layer 2  → worker1 (via RPC)
                                ...
                                layer 11 → worker2 (via RPC)
                                ...
                                layer 21 → worker3 (via RPC)
                                         ↓
                              Activations flow through the pipeline:
                                worker1 → worker2 → worker3 → llama-server
                                         ↓
                              llama-server decodes → returns response
                                         ↓
                              Coordinator returns response to client
```

---

## Approach: llama.cpp RPC Backend (Recommended)

The most practical path uses **llama.cpp's built-in RPC backend**. This is a mature, well-tested feature that:

- Splits model layers across machines automatically
- Uses gRPC for fast tensor passing between workers
- Provides a standard OpenAI-compatible API
- Supports any GGUF model

### How It Works

1. Each worker machine runs `llama-rpc-server` — a lightweight binary that exposes its GPU/CPU memory
2. The head node runs `llama-server` with `--rpc` flags pointing to each worker
3. `llama-server` shards the model layers across all RPC workers
4. The Younify worker's provider layer talks to `llama-server` like any OpenAI-compatible API

---

## Files to Create

### 1. `coordinator/coordinator.py` — Coordinator (Single Entry Point)

The coordinator is the **only service you interact with**. No job queue, no Redis. Workers auto-connect, the coordinator proxies inference to llama-server (which distributes across workers).

```python
# See coordinator/coordinator.py for the full source
# Key endpoints:
#   POST /api/v1/workers/register    — workers auto-register on startup
#   POST /api/v1/workers/heartbeat   — keep-alive from workers
#   POST /api/v1/generate            — direct inference (no queue)
#   GET  /api/v1/cluster/status      — cluster health
#   GET  /api/v1/cluster/rpc-addrs   — RPC worker addresses
```

### 2. `worker/cluster_worker.py` — Worker Sidecar

A sidecar process that runs alongside the Younify worker on each machine. It:
1. Spawns/manages the `llama-rpc-server` process
2. Registers with the coordinator
3. Sends heartbeats
4. Reports available VRAM/RAM

```python
"""
cluster_worker.py — Distributed Cluster Worker Sidecar
=======================================================
Manages the llama-rpc-server process on this machine and
registers with the cluster coordinator.

Usage:
    python cluster_worker.py --coordinator http://head-node:8050
"""

import argparse
import os
import subprocess
import sys
import time
import json
import threading
import signal

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_RPC_PORT = 5000
HEARTBEAT_INTERVAL = 10


def get_system_memory():
    """Get available VRAM (NVIDIA) and RAM."""
    vram_mb = 0
    ram_mb = 0

    # Try nvidia-smi for VRAM
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            vrams = [int(x.strip()) for x in result.stdout.strip().split("\n") if x.strip()]
            vram_mb = sum(vrams)
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    # Fallback: check if nvidia-ml-py is available
    if vram_mb == 0:
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                vram_mb += info.free // (1024 * 1024)
        except (ImportError, Exception):
            pass

    # System RAM
    try:
        import psutil
        ram_mb = psutil.virtual_memory().available // (1024 * 1024)
    except ImportError:
        try:
            result = subprocess.run(
                ["free", "-m"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                parts = lines[1].split()
                ram_mb = int(parts[3])  # available
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError, IndexError):
            ram_mb = 0

    return vram_mb, ram_mb


def find_llama_rpc_server():
    """Find the llama-rpc-server binary."""
    # Check common locations
    candidates = [
        "llama-rpc-server",
        "./llama-rpc-server",
        os.path.expanduser("~/llama.cpp/build/bin/llama-rpc-server"),
        "/usr/local/bin/llama-rpc-server",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        # Also check if it's in PATH
        try:
            subprocess.run([c, "--help"], capture_output=True, timeout=5)
            return c
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


class ClusterWorker:
    def __init__(self, coordinator_url: str, rpc_port: int = DEFAULT_RPC_PORT,
                 llama_rpc_bin: str = None, label: str = ""):
        self.coordinator_url = coordinator_url.rstrip("/")
        self.rpc_port = rpc_port
        self.llama_rpc_bin = llama_rpc_bin or find_llama_rpc_server()
        self.label = label
        self.worker_id = None
        self.rpc_process = None
        self._running = False

    def start(self):
        # 1. Start llama-rpc-server
        if self.llama_rpc_bin:
            host = self._get_host_ip()
            cmd = [self.llama_rpc_bin, "--host", "0.0.0.0", "--port", str(self.rpc_port)]
            print(f"[CLUSTER] Starting: {' '.join(cmd)}")
            self.rpc_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(2)  # Wait for it to start
        else:
            host = self._get_host_ip()
            print(f"[CLUSTER] No llama-rpc-server binary found.")
            print(f"[CLUSTER] Run it manually on port {self.rpc_port}")
            print(f"[CLUSTER] Or set LLAMA_RPC_BIN environment variable")

        # 2. Register with coordinator
        vram_mb, ram_mb = get_system_memory()
        hostname = socket.gethostname() if not host else host

        try:
            resp = requests.post(
                f"{self.coordinator_url}/api/v1/workers/register",
                json={
                    "host": hostname,
                    "port": self.rpc_port,
                    "vram_mb": vram_mb,
                    "ram_mb": ram_mb,
                    "label": self.label or f"worker-{hostname}",
                },
                timeout=10,
            )
            data = resp.json()
            self.worker_id = data["worker_id"]
            print(f"[CLUSTER] Registered with coordinator. Worker ID: {self.worker_id}")
            print(f"[CLUSTER] VRAM: {vram_mb} MB, RAM: {ram_mb} MB")
        except requests.RequestException as e:
            print(f"[CLUSTER] Failed to register: {e}")
            return

        # 3. Start heartbeat loop
        self._running = True
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()

        print(f"[CLUSTER] Cluster worker running. PID: {os.getpid()}")
        print(f"[CLUSTER] RPC server on port {self.rpc_port}")
        print(f"[CLUSTER] Coordinator: {self.coordinator_url}")

    def _heartbeat_loop(self):
        while self._running:
            try:
                requests.post(
                    f"{self.coordinator_url}/api/v1/workers/heartbeat",
                    json={"worker_id": self.worker_id},
                    timeout=5,
                )
            except requests.RequestException:
                pass
            time.sleep(HEARTBEAT_INTERVAL)

    def stop(self):
        self._running = False
        if self.worker_id:
            try:
                requests.delete(
                    f"{self.coordinator_url}/api/v1/workers/{self.worker_id}",
                    timeout=5,
                )
            except requests.RequestException:
                pass
        if self.rpc_process:
            self.rpc_process.terminate()
            self.rpc_process.wait(timeout=10)

    @staticmethod
    def _get_host_ip():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip


if __name__ == "__main__":
    import socket

    parser = argparse.ArgumentParser(description="Younify Cluster Worker Sidecar")
    parser.add_argument("--coordinator", default=os.environ.get("COORDINATOR_URL", "http://localhost:8050"))
    parser.add_argument("--rpc-port", type=int, default=int(os.environ.get("RPC_PORT", DEFAULT_RPC_PORT)))
    parser.add_argument("--label", default=os.environ.get("WORKER_LABEL", ""))
    parser.add_argument("--llama-rpc-bin", default=os.environ.get("LLAMA_RPC_BIN", ""))
    args = parser.parse_args()

    worker = ClusterWorker(
        coordinator_url=args.coordinator,
        rpc_port=args.rpc_port,
        llama_rpc_bin=args.llama_rpc_bin or None,
        label=args.label,
    )

    def _signal_handler(signum, frame):
        print("\n[CLUSTER] Shutting down...")
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    worker.start()

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        worker.stop()
```

### 3. `worker/cluster_provider.py` — Cluster Inference Provider

Optional provider for routing Younify jobs through the cluster. Normally you hit the coordinator directly; this exists for compatibility with the existing Younify worker system.

```python
# See worker/cluster_provider.py for the full source
# It sends POST /api/v1/generate to the coordinator (not llama-server directly)
```

### 4. `coordinator/Dockerfile` — Coordinator Container

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY coordinator/ ./coordinator/
COPY worker/cluster_provider.py ./worker/

EXPOSE 8050

CMD ["uvicorn", "coordinator.coordinator:coordinator_app", "--host", "0.0.0.0", "--port", "8050"]
```

### 5. `cluster-llama-entrypoint.sh` — Head Node Script

A script that starts llama-server with all RPC worker addresses.

```bash
#!/usr/bin/env bash
# cluster-llama-entrypoint.sh — Start llama-server with RPC workers
# ================================================================
# Fetches RPC worker addresses from the coordinator, then starts
# llama-server bound to all of them.
#
# Usage:
#   bash cluster-llama-entrypoint.sh \
#     --model /path/to/model.gguf \
#     --coordinator http://localhost:8050 \
#     --port 8080
#
# Environment variables:
#   COORDINATOR_URL   (default: http://localhost:8050)
#   LLAMA_SERVER_BIN  (default: llama-server)
#   MODEL_PATH        (path to GGUF model file)
#   LLAMA_SERVER_PORT (default: 8080)
#   N_GPU_LAYERS      (default: 99, offload all layers)
#   CTX_SIZE          (default: 4096)

set -euo pipefail

COORDINATOR_URL="${COORDINATOR_URL:-http://localhost:8050}"
LLAMA_SERVER="${LLAMA_SERVER_BIN:-llama-server}"
MODEL_PATH="${MODEL_PATH:-}"
PORT="${LLAMA_SERVER_PORT:-8080}"
N_GPU_LAYERS="${N_GPU_LAYERS:-99}"
CTX_SIZE="${CTX_SIZE:-4096}"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)       MODEL_PATH="$2"; shift 2 ;;
        --coordinator) COORDINATOR_URL="$2"; shift 2 ;;
        --port)        PORT="$2"; shift 2 ;;
        --ngl)         N_GPU_LAYERS="$2"; shift 2 ;;
        --ctx-size)    CTX_SIZE="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$MODEL_PATH" ]]; then
    echo "Error: --model or MODEL_PATH is required"
    exit 1
fi

echo "=== Cluster LLM Entrypoint ==="
echo "Model:      $MODEL_PATH"
echo "Coordinator: $COORDINATOR_URL"
echo "Port:       $PORT"
echo ""

# Fetch RPC addresses from coordinator
echo "Fetching RPC workers from coordinator..."
RPC_ADDRS=$(curl -sf "$COORDINATOR_URL/api/v1/rpc-addrs" | python3 -c "
import sys, json
data = json.load(sys.stdin)
addrs = data.get('addresses', [])
for a in addrs:
    print(f'--rpc {a}')
" 2>/dev/null || echo "")

if [[ -z "$RPC_ADDRS" ]]; then
    echo "WARNING: No RPC workers found from coordinator."
    echo "Starting llama-server in standalone mode (no distributed compute)."
else
    echo "RPC workers:"
    echo "$RPC_ADDRS" | tr ' ' '\n'
fi

# Build command
CMD=("$LLAMA_SERVER")
CMD+=("--model" "$MODEL_PATH")
CMD+=("--host" "0.0.0.0")
CMD+=("--port" "$PORT")
CMD+=("--n-gpu-layers" "$N_GPU_LAYERS")
CMD+=("--ctx-size" "$CTX_SIZE")

# Add RPC addresses
if [[ -n "$RPC_ADDRS" ]]; then
    while IFS= read -r rpc_arg; do
        if [[ -n "$rpc_arg" ]]; then
            CMD+=("$rpc_arg")
        fi
    done <<< "$RPC_ADDRS"
fi

echo ""
echo "Starting: ${CMD[*]}"
echo ""

exec "${CMD[@]}"
```

---

## Files to Modify

### 1. `worker/providers.py` — Register the Cluster Provider

Add this import near the top:

```python
from cluster_provider import ClusterProvider  # noqa: F401
```

The `cluster_provider` module auto-registers itself with the provider registry.

### 2. `worker/worker.py` — Add Cluster to Provider List

```python
print(f"  Providers: ollama, openrouter, openai, vllm, cluster")
```

### 3. `requirements.txt` — Add Dependencies

```
# GPU monitoring (optional, for cluster worker memory detection)
# pynvml; sys_platform != "darwin"
# psutil
```

### 4. `start.sh` — Add Cluster Launch Options

Add a `--cluster` mode flag that starts the coordinator and optional cluster worker:

```bash
# In the argument parsing section:
        --cluster)     CLUSTER_MODE=true; shift ;;
        --coordinator-only) COORDINATOR_ONLY=true; shift ;;

# In the launch section (after Docker stack starts):
if [[ "$CLUSTER_MODE" == true ]]; then
    # Start coordinator
    $PYTHON -m uvicorn coordinator.coordinator:coordinator_app \
        --host 0.0.0.0 --port 8050 &
    COORD_PID=$!
    info "Coordinator started (PID: $COORD_PID)"

    # Start cluster worker sidecar
    $PYTHON worker/cluster_worker.py \
        --coordinator http://localhost:8050 &
    CLUSTER_PID=$!
    info "Cluster worker started (PID: $CLUSTER_PID)"
    
    WORKER_PIDS="${WORKER_PIDS} $COORD_PID $CLUSTER_PID"
fi
```

### 5. `docker-compose.yml` — Add Coordinator Service

Add after the `worker` service:

```yaml
  coordinator:
    build:
      context: .
      dockerfile: coordinator/Dockerfile
    container_name: younify-coordinator
    ports:
      - "8050:8050"
```

### 6. `api_gateway/dashboard.py` — Update Cluster Topology Panel

Add a Coordinator card showing status, worker count, and RPC nodes. The dashboard polls `GET /api/v1/cluster/status` on the coordinator.

### 7. `api_gateway/main.py` — Add Coordinator Proxy Endpoints

Add endpoints so the dashboard can show cluster status:

```python
COORDINATOR_URL = os.environ.get("COORDINATOR_URL", "http://localhost:8050")

@app.get("/api/v1/cluster/status")
async def cluster_status():
    import requests as req
    try:
        resp = req.get(f"{COORDINATOR_URL}/api/v1/cluster/status", timeout=5)
        return resp.json()
    except Exception:
        return {"total_workers": 0, "workers": [], "error": "Coordinator unreachable"}

@app.get("/api/v1/cluster/rpc-addrs")
async def cluster_rpc_addrs():
    import requests as req
    try:
        resp = req.get(f"{COORDINATOR_URL}/api/v1/cluster/rpc-addrs", timeout=5)
        return resp.json()
    except Exception:
        return {"addresses": [], "error": "Coordinator unreachable"}
```

---

## Environment Variables (New)

| Variable | Default | Description |
|---|---|---|
| Variable | Default | Description |
|---|---|---|
| `COORDINATOR_URL` | `http://localhost:8050` | URL of the coordinator service |
| `COORDINATOR_PORT` | `8050` | Port for the coordinator FastAPI app |
| `RPC_PORT` | `5000` | Port for llama-rpc-server on this machine |
| `CLUSTER_INFERENCE_URL` | `http://localhost:8080` | URL of the head llama-server (used by coordinator to proxy) |
| `LLAMA_SERVER_BIN` | `llama-server` | Path to llama-server binary |
| `LLAMA_RPC_BIN` | (auto-detect) | Path to llama-rpc-server binary |
| `WORKER_LABEL` | `worker-{hostname}` | Human-readable label for this worker |
| `N_GPU_LAYERS` | `99` | Number of layers to offload to GPU |
| `CTX_SIZE` | `4096` | Context size for the model |

---

## Step-by-Step Implementation

### Phase 1: Create New Files

1. **Create `coordinator/` directory** at project root
2. **Create `coordinator/__init__.py`** (empty)
3. **Create `coordinator/coordinator.py`** — the coordinator service
4. **Create `coordinator/Dockerfile`** — container for coordinator
5. **Create `worker/cluster_provider.py`** — cluster provider for Younify workers
6. **Create `worker/cluster_worker.py`** — sidecar for worker machines
7. **Create `cluster-llama-entrypoint.sh`** — head node launch script

### Phase 2: Modify Existing Files

8. **Edit `worker/providers.py`** — add import for `cluster_provider` (auto-registers)
9. **Edit `worker/worker.py`** — add "cluster" to provider list in banner
10. **Edit `requirements.txt`** — add optional GPU monitoring deps
11. **Edit `docker-compose.yml`** — add coordinator service
12. **Edit `api_gateway/main.py`** — add coordinator proxy endpoints for dashboard
13. **Edit `api_gateway/dashboard.py`** — add Coordinator card to cluster topology panel

### Phase 3: Setup llama.cpp on All Machines

14. **On each worker machine:** Build/install llama.cpp with RPC support:
    ```bash
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
    cmake -B build -DLLAMA_RPC=ON
    cmake --build build --config Release -j
    # The llama-rpc-server binary will be in build/bin/
    ```
15. **On the head node:** Build llama-server the same way (with `-DLLAMA_RPC=ON`)

### Phase 4: Deploy

16. **Head node:** Start coordinator + llama-server (which connects to all RPC workers)
17. **Worker machines:** Start cluster_worker.py (which runs llama-rpc-server and registers)

---

## Usage Flow

### Starting the Cluster

**On head node:**
```bash
# Start the coordinator
python3 -m uvicorn coordinator.coordinator:coordinator_app \
  --host 0.0.0.0 --port 8050 &

# Start llama-server with all RPC workers
bash cluster-llama-entrypoint.sh \
  --model /path/to/model.gguf \
  --coordinator http://localhost:8050 \
  --port 8080
```

**On each worker machine (auto-connects):**
```bash
# That's it — one command. It starts llama-rpc-server and registers.
python3 worker/cluster_worker.py \
  --coordinator http://head-node:8050
```

### Submitting an Inference Request

Hit the coordinator directly — no job queue, no polling:
```bash
curl -X POST http://head-node:8050/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello from the cluster!",
    "model": "llama-3-70b",
    "max_tokens": 256
  }'
# Returns immediately with the completion (synchronous).
```

---

## Verification

1. **Check coordinator status:**
   ```bash
   curl http://head-node:8050/api/v1/cluster/status
   # Should show alive workers
   ```

2. **Check RPC addresses:**
   ```bash
   curl http://head-node:8050/api/v1/cluster/rpc-addrs
   # Should list all worker addresses
   ```

3. **Run inference through the cluster:**
   ```bash
   curl -X POST http://head-node:8050/api/v1/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello!", "model": "test"}'
   # Returns completion directly — no polling, no job ID
   ```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Workers not appearing in coordinator | Firewall blocking port 8050 | Open coordinator port |
| Worker shows "dead" | Heartbeat not reaching coordinator | Check network connectivity |
| llama-server won't start | Missing model or wrong path | Verify MODEL_PATH |
| RPC connection refused | llama-rpc-server not running on worker | Start cluster_worker.py |
| Inference slow | Too few workers for model size | Add more workers |
| Out of memory | Model too large for combined VRAM | Use smaller model or more workers |
| `model_id: "cluster/..."` fails | ClusterProvider not registered | Verify providers.py has the import |

---

## Architecture Diagram (Updated)

```
                              ┌──────────────────────────────────────┐
                              │         HEAD NODE                   │
                              │                                     │
                              │  ┌──────────────────────────────┐   │
                              │  │  Coordinator :8050            │   │
                              │  │  - POST /api/v1/generate      │   │
                              │  │  - GET  /api/v1/cluster/status│   │
                              │  └──────────┬───────────────────┘   │
                              │             │ proxies to             │
                              │  ┌──────────▼───────────────────┐   │
                              │  │  llama-server :8080           │   │
                              │  │  --rpc w1:5000               │   │
                              │  │  --rpc w2:5000               │   │
                              │  │  --rpc w3:5000               │   │
                              │  └──────────────────────────────┘   │
                              └──────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
          ┌─────────▼─────────┐   ┌──────────▼──────────┐   ┌─────────▼─────────┐
          │  WORKER NODE 1    │   │  WORKER NODE 2      │   │  WORKER NODE 3    │
          │                   │   │                     │   │                   │
          │  ┌─────────────┐  │   │  ┌─────────────┐   │   │  ┌─────────────┐  │
          │  │ llama-rpc   │  │   │  │ llama-rpc   │   │   │  │ llama-rpc   │  │
          │  │ -server     │  │   │  │ -server     │   │   │  │ -server     │  │
          │  │ :5000       │  │   │  │ :5000       │   │   │  │ :5000       │  │
          │  └─────────────┘  │   │  └─────────────┘   │   │  └─────────────┘  │
          │                   │   │                     │   │                   │
          │  Holds layers 1-10│   │  Holds layers 11-20 │   │  Holds layers 21-30
          └───────────────────┘   └─────────────────────┘   └───────────────────┘
```

---

## How the Cluster Fits with the Dashboard

The cluster operates independently of the Younify job queue. The dashboard's Cluster Topology panel shows:
- Coordinator health and worker count
- RPC addresses of connected workers

For cluster inference, hit the coordinator directly:
```bash
curl -X POST http://head-node:8050/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!", "model": "llama-3-70b"}'
```

If you want to use the cluster from within Younify's job system, use `model_id: "cluster/my-model"` — it routes through `ClusterProvider` → coordinator → llama-server.

---

## Alternative: Custom Distributed Approach (Without llama.cpp)

If you want full control without depending on llama.cpp, the alternative is:

### New Components
- **Model Sharder** — splits a model's layers and sends each shard to a worker
- **Activation Router** — passes tensor activations between workers via gRPC
- **Coordinator** (same as above) — manages which worker has which layers

### Key Differences from llama.cpp Approach
- You must implement the forward pass routing yourself
- You need a gRPC or socket-based activation passing protocol
- You need to handle model weight serialization/deserialization
- You're not limited to GGUF models (works with PyTorch, etc.)

This is significantly more complex and is only recommended if you absolutely cannot use llama.cpp.
