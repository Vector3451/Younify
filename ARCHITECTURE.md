# Architecture — Younify Distributed AI Inference System

## Goal

Build a distributed inference cluster where multiple machines pool their GPU/CPU compute to run one model collaboratively, without a job dispatch queue — workers auto-connect and contribute resources directly via llama.cpp RPC.

---

## System Architecture (Current State)

```
┌──────────────────────────────────────────────────────────────────┐
│                        HEAD NODE                                  │
│                                                                  │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐ │
│  │  Redis        │     │  API Gateway      │     │  Coordinator  │ │
│  │  Port 6379    │◄────│  Port 3000        │     │  Port 8050    │ │
│  │               │     │  ┌────────────┐   │     │               │ │
│  │  Task Queue   │     │  │ Dashboard  │   │     │  Worker       │ │
│  │  Job Results  │     │  │ (SPA)      │   │     │  Registry     │ │
│  └──────────────┘     │  └────────────┘   │     │  Health        │ │
│          ▲            └──────────────────┘     │  Monitor       │ │
│          │                │                     └───────┬───────┘ │
│          │                │  LPUSH tasks                │         │
│          │                ▼                             │         │
│          │     ┌──────────────────┐                     │         │
│          └─────┤  Local Workers   │                     │         │
│                │  (Ollama)        │                     │         │
│                └──────────────────┘                     │         │
│                                                         │         │
│  ┌──────────────────────────────────────────────────────┐│         │
│  │  llama-server (port 8080)                            ││         │
│  │  Runs model with --rpc <worker1>:5000 --rpc <w2>:.. ││         │
│  │  llama.cpp distributes layers across all workers     ││         │
│  └────────────────────────┬─────────────────────────────┘│         │
│                           │                              │         │
└───────────────────────────┼──────────────────────────────┼─────────┘
                            │                              │
                     Tailscale Mesh VPN                    │
                            │                              │
┌───────────────────────────┼──────────────────────────────┼─────────┐
│                    WORKER NODE ┌─────────────────────────┘         │
│                               ▼                                    │
│  ┌────────────────────┐  ┌────────────────────────────────────┐   │
│  │  llama-rpc-server  │  │  cluster_worker.py                  │   │
│  │  Port 5000          │  │  Registers with coordinator        │   │
│  │                     │  │  Sends heartbeats every 10s        │   │
│  │  Contributes VRAM   │  │  Starts llama-rpc-server           │   │
│  │  to head node       │  │                                    │   │
│  └────────────────────┘  └────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Two Independent Paths

1. **Redis Queue Path** — Jobs submitted via dashboard → Redis queue → worker polls and runs Ollama locally. Results written back to Redis. Used for single-machine or traditional distributed setups.

2. **Cluster Path** — No queue. Workers register directly with the coordinator. The head node runs `llama-server` with `--rpc` pointing at all workers. Inference is synchronous via `POST /api/v1/generate` on the coordinator, which proxies to `llama-server`. llama.cpp splits model layers across workers automatically.

---

## Component Details

| Component | Technology | Responsibility |
|---|---|---|
| **Web Dashboard** | Vanilla HTML/CSS/JS (SPA) | Chat UI, job history, cluster topology, settings |
| **API Gateway** | FastAPI (Python) | Validates requests, enqueues to Redis, serves dashboard, proxies coordinator status |
| **Message Broker** | Redis / Valkey 7+ | FIFO task queue + job result storage |
| **Worker Service** | Python (`worker.py`) | Blocks on `BRPOP`, runs Ollama inference, writes result back |
| **Cluster Coordinator** | FastAPI (Python) | Worker registry, heartbeat monitor, inference proxy to llama-server |
| **Cluster Worker** | Python (`cluster_worker.py`) | Sidecar — starts llama-rpc-server, registers with coordinator |
| **Inference Server** | llama.cpp (`llama-server`) | Runs the model, distributes layers via RPC to all workers |
| **Provider Layer** | Python (`providers.py`) | Ollama (`OllamaProvider`) and Cluster (`ClusterProvider`) |

---

## Provider Layer (`worker/providers.py`)

All providers implement a `generate()` interface:

```python
def generate(model, prompt, max_tokens, temperature, **kwargs) -> dict:
    # Returns: {model, completion, prompt_tokens, completion_tokens}
```

| Provider | Backend | Description |
|---|---|---|
| `ollama` | Local Ollama HTTP API | Default. Auto-discovers installed models. |
| `cluster` | Coordinator → llama-server | Sends request to coordinator which proxies to llama-server running with RPC across all workers. |

---

## Cluster Architecture (Coordinator)

The coordinator (`coordinator/coordinator.py`) is a lightweight FastAPI service:

- **Worker Registration** — `POST /api/v1/workers/register` — workers register with their host, RPC port, and available VRAM/RAM
- **Heartbeat** — `POST /api/v1/workers/heartbeat` — workers send heartbeats every 10s; stale workers are marked dead after 30s
- **Status** — `GET /api/v1/cluster/status` — returns all workers with alive/dead status
- **RPC Addresses** — `GET /api/v1/cluster/rpc-addrs` — returns `host:port` for alive workers (used by `cluster-llama-entrypoint.sh` to build `--rpc` flags)
- **Inference Proxy** — `POST /api/v1/generate` — proxies to `llama-server` on port 8080
- **Health** — `GET /api/v1/health` — coordinator health + alive worker count

No Redis needed for the coordinator itself — it uses an in-memory worker registry.

---

## Deployment (start.sh)

`start.sh` is the single entry point covering all modes:

| Command | What it does |
|---|---|
| `bash start.sh` | Head node: Docker stack + API + local Ollama workers |
| `bash start.sh --cluster` | Head node with cluster mode: adds coordinator + llama-server |
| `bash start.sh --tailscale` | One-time Tailscale setup on head node, prints IP |
| `bash start.sh --worker <ip>` | Worker node: Tailscale + deps + cluster_worker.py |
| `bash start.sh --head-only` | Redis + API only, no workers |

Workers connect via **Tailscale** for a zero-config mesh VPN across machines.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web dashboard SPA |
| `GET` | `/api/v1/health` | Gateway + Redis connectivity |
| `GET` | `/api/v1/models` | Ollama model list |
| `POST` | `/api/v1/generate` | Submit inference job → `job_id` |
| `GET` | `/api/v1/status/{job_id}` | Poll job result |
| `GET` | `/api/v1/cluster/status` | Coordinator worker status |
| `GET` | `/api/v1/cluster/rpc-addrs` | Coordinator RPC addresses |

---

## State & Configuration

- **Job state** persisted in Redis (queue + results)
- **API keys** removed — Younify uses Ollama (local) and Cluster (distributed), no cloud API keys needed
- **Worker registry** in-memory on coordinator (no persistence needed — workers re-register on reconnect)
- **Dashboard settings** simplified — no API key management, only informational

---

## Ports

| Port | Service |
|---|---|
| 3000 | Web Dashboard + API Gateway |
| 6379 | Redis / Valkey |
| 8050 | Cluster Coordinator |
| 8080 | llama-server (inference) |
| 5000 | llama-rpc-server (per worker) |
| 11434 | Ollama |
