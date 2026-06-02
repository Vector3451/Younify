# Younify — Distributed AI Inference System

A **distributed AI inference platform** that pools GPU/CPU compute across machines using llama.cpp RPC. Workers auto-connect via Tailscale and contribute resources to run a single model collaboratively.

---

## Quick Start

### Prerequisites
- Docker
- Python 3.10+
- [Ollama](https://ollama.com) (for local inference)
- [Tailscale](https://tailscale.com) (for multi-machine cluster)

### Head Node (one command)

```bash
bash start.sh
```

This starts the full stack:
1. Checks Docker is running, starts Redis + API Gateway via Docker Compose
2. Installs Python deps, starts coordinator on port 8050
3. Optionally starts llama-server if `MODEL_PATH` is set
4. Starts local Younify workers for Ollama inference
5. Prints dashboard URL and, if Tailscale is connected, the worker join command

Dashboard opens at **http://localhost:3000**.

### Cluster Mode (distributed inference across machines)

**Head node:**
```bash
bash start.sh --tailscale   # one-time: installs Tailscale, prints the head node IP
bash start.sh --cluster      # full stack + coordinator + cluster mode
```

**Worker node (one command per machine):**
```bash
bash start.sh --worker <head-tailscale-ip>
```

This:
1. Installs Tailscale if missing, connects, and authenticates
2. Verifies the head node coordinator is reachable via Tailscale
3. Installs Python deps, builds `llama-rpc-server` from llama.cpp if needed
4. Starts `cluster_worker.py` — auto-registers with the coordinator and contributes compute

The head node then runs `llama-server` with `--rpc <worker>:5000` for each worker, distributing model layers across all machines' VRAM.

### Other Modes

| Command | Description |
|---|---|
| `bash start.sh` | Head node, full stack (Redis + API + workers) |
| `bash start.sh --head-only` | Redis + API only (no local workers) |
| `bash start.sh --cluster` | Full stack + coordinator + cluster mode |
| `bash start.sh --tailscale` | Install Tailscale and print connection info |
| `bash start.sh --workers 3` | Start with N local workers |
| `bash start.sh --worker <ip>` | Connect this machine as a cluster worker |

The redundant `tailscale-setup.sh` and `connect-to-cluster.sh` have been removed — everything is unified in `start.sh`.

---

## Project Structure

```
Younify/
├── api_gateway/
│   ├── main.py               # FastAPI app — API endpoints + Redis queue
│   ├── dashboard.py          # SPA web dashboard (inline HTML/CSS/JS)
│   └── Dockerfile
│
├── coordinator/
│   ├── coordinator.py        # Cluster coordinator — worker registry + inference proxy
│   └── Dockerfile
│
├── worker/
│   ├── worker.py             # Redis queue consumer — Ollama inference
│   ├── cluster_worker.py     # Cluster worker sidecar — RPC server + coordinator registration
│   ├── cluster_provider.py   # Provider that calls coordinator for distributed inference
│   ├── providers.py          # Provider abstraction (Ollama + Cluster)
│   └── Dockerfile
│
├── cluster-llama-entrypoint.sh  # Fetches RPC addrs, starts llama-server with --rpc flags
├── start.sh                     # Unified launcher — head, worker, tailscale, cluster
├── docker-compose.yml           # Redis + API Gateway + Coordinator
├── .env.example                 # Configuration template
├── ARCHITECTURE.md
└── README.md
```

---

## Web Dashboard

The dashboard is served at **http://localhost:3000** and includes:

| Panel | Description |
|---|---|
| **Dashboard** | Live KPI cards (total jobs, active, completed, success rate) + Chart.js charts + recent activity feed |
| **Chat** | Real-time conversation — select a model, type a message, get a response |
| **Jobs History** | Searchable/filterable log of all jobs; click any row to open the inspect drawer |
| **Cluster Topology** | Node status cards (Gateway, Redis, Coordinator, Workers), installed Ollama models, backend integrations |
| **Settings** | Information about the local-only provider setup |

---

## Providers

| Name | Model ID Prefix | Backend | Description |
|---|---|---|---|
| **Ollama** | `ollama/` | Local Ollama HTTP API | Default provider. Models auto-detect in the dashboard. |
| **Cluster** | `cluster/` | Coordinator → llama-server with RPC | Distributes inference across all connected workers. |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web dashboard SPA |
| `GET` | `/api/v1/health` | Gateway + Redis connectivity check |
| `GET` | `/api/v1/models` | Lists models available from Ollama |
| `POST` | `/api/v1/generate` | Submits an inference job → returns `job_id` |
| `GET` | `/api/v1/status/{job_id}` | Polls job status and retrieves result |
| `GET` | `/api/v1/cluster/status` | Coordinator cluster status (workers alive, etc.) |
| `GET` | `/api/v1/cluster/rpc-addrs` | RPC addresses of connected workers |

---

## Docker

```bash
# Build and run full stack
docker compose up --build

# Scale workers
docker compose up --scale worker=4
```

---

## Configuration (`.env`)

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
OLLAMA_BASE_URL=http://localhost:11434
COORDINATOR_URL=http://localhost:8050
```

---

## Ports

| Port | Service |
|---|---|
| 3000 | Web Dashboard + API Gateway |
| 6379 | Redis / Valkey Message Broker |
| 8050 | Cluster Coordinator |
| 8080 | llama-server (inference endpoint) |
| 5000 | llama-rpc-server (per worker) |
| 11434 | Ollama (local model server) |
