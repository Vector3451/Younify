# ⚡ Younify — Distributed AI Inference System

A **distributed, multi-provider AI inference platform** built on FastAPI, Redis/Valkey, and a premium glassmorphic web dashboard. Submit inference jobs from one machine and have them processed by a pool of workers running across your entire network.

---

## 🗂️ Project Structure

```
Younify/
├── api_gateway/
│   ├── __init__.py           # Python package marker
│   ├── main.py               # FastAPI app — API endpoints + request validation
│   ├── dashboard.py          # Full SPA web dashboard (HTML/CSS/JS, served inline)
│   ├── api_contract.md       # API specification document
│   └── Dockerfile            # Builds API Gateway container image
│
├── worker/
│   ├── worker.py             # Redis consumer — picks up jobs and runs inference
│   ├── providers.py          # Multi-provider abstraction (Ollama, OpenRouter, OpenAI, vLLM)
│   └── Dockerfile            # Builds Worker container image
│
├── tests/
│   └── test_api_flow.py      # End-to-end integration tests
│
├── ARCHITECTURE.md           # System architecture & phased roadmap
├── README.md                 # This file
├── DEPLOY.md                 # Multi-machine deployment guide
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Full stack: Redis + API Gateway + Worker
├── docker-compose.worker.yml # Workers-only compose (point at remote Redis)
├── .env.example              # Configuration template — copy to .env
├── start.sh                  # One-command launcher (dev mode)
├── stop.sh                   # Graceful shutdown
├── deploy-head.sh            # Head-node setup script
├── deploy-workers.sh         # Docker-based worker deployment to remote machines
├── run-worker.sh             # Host-based (non-Docker) worker launcher
└── list-providers.py         # Diagnostic — check which providers are reachable
```

---

## 🚀 Quick Start (One Command)

```bash
# Start everything: Redis + API Gateway + Web UI + local worker
bash start.sh

# With 3 local workers
bash start.sh --workers 3

# Head-only (no local worker — for multi-machine setups)
bash start.sh --head-only

# Stop everything
bash stop.sh
```

Dashboard opens at **http://localhost:3000**.

---

## 🚀 Quick Start (Local / Development)

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed locally (for local inference)
- [Valkey](https://valkey.io) or Redis 7+ running on port 6379

### 1. Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the message broker
```bash
# Valkey (Redis-compatible)
valkey-server --port 6379 --daemonize yes

# Or standard Redis
redis-server --daemonize yes
```

### 3. Pull a model (first time only)
```bash
ollama pull tinyllama
# or any model: ollama pull llama3, mistral, etc.
```

### 4. Start the API Gateway
```bash
.venv/bin/uvicorn api_gateway.main:app --host 0.0.0.0 --port 3000
```

### 5. Start one or more workers
```bash
# In a new terminal (or multiple terminals for more workers)
.venv/bin/python3 worker/worker.py
```

### 6. Open the dashboard
```
http://localhost:3000
```

---

## 🌐 Distributed Setup (Multiple Machines)

The system is designed from the ground up for multi-machine distribution. Every worker connects to the **same Redis instance** on the head node.

**Head Node (Machine A):**
```bash
# Expose Redis to the LAN
valkey-server --port 6379 --bind 0.0.0.0 --daemonize yes

# Start the API Gateway
.venv/bin/uvicorn api_gateway.main:app --host 0.0.0.0 --port 3000
```

**Worker Nodes (Machine B, C, D...):**
```bash
# Clone the repo, then:
REDIS_HOST=<HEAD_NODE_LAN_IP> \
OLLAMA_BASE_URL=http://localhost:11434 \
.venv/bin/python3 worker/worker.py
```

**Scale with Docker Compose (per worker machine):**
```bash
HEAD_NODE_IP=192.168.1.100 \
docker compose -f docker-compose.worker.yml up -d --scale worker=4
```

Workers connect to the shared Redis queue, pick up jobs, run inference on their own local model server (Ollama, vLLM, etc.), and write results back — all transparently visible in the dashboard on Machine A.

---

## 💻 Web Dashboard

The dashboard is served at `http://localhost:3000` and includes:

| Panel | Description |
|---|---|
| **Dashboard** | Live KPI cards (total jobs, active, completed, success rate) + Chart.js charts |
| **Chat** | Live conversation interface — type a message, get a response in real time |
| **Submit Job** | Advanced job form with temperature/token sliders and prompt presets |
| **Jobs History** | Searchable/filterable log of all jobs; click any row to open the inspect drawer |
| **Cluster Topology** | Node status cards, installed model registry, backend integrations info |
| **Settings** | Securely store OpenRouter, OpenAI, and vLLM API keys in browser localStorage |

---

## 🔑 API Keys (Cloud Providers)

Open **Settings** in the sidebar. Keys are:
- Stored in your **browser's `localStorage`** only — never sent to or stored on the server
- **Automatically injected** into job payloads when you submit a Chat message or Submit Job targeting that provider
- Cleared when you click *Clear All Keys* or clear your browser data

---

## 🧩 Model ID Format

All job requests use a provider-prefixed model ID:

| Format | Provider | Example |
|---|---|---|
| `ollama/<model>` | Local Ollama | `ollama/tinyllama:latest` |
| `openrouter/<model>` | OpenRouter cloud | `openrouter/meta-llama/llama-3.1-70b-instruct` |
| `openai/<model>` | OpenAI API | `openai/gpt-4o` |
| `vllm/<model>` | Local vLLM server | `vllm/meta-llama/Llama-3-8B` |

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the web dashboard SPA |
| `GET` | `/api/v1/health` | Gateway + Redis connectivity check |
| `GET` | `/api/v1/models` | Lists models available from Ollama |
| `POST` | `/api/v1/generate` | Submits an inference job → returns `job_id` |
| `GET` | `/api/v1/status/{job_id}` | Polls job status and retrieves result |

**Submit Job payload:**
```json
{
  "prompt": "What is the capital of France?",
  "model_id": "ollama/tinyllama:latest",
  "max_tokens": 512,
  "temperature": 0.7,
  "api_key": "sk-or-v1-..."
}
```

---

## ⚙️ Configuration (`.env`)

Copy `.env.example` to `.env` and fill in values:

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional — only needed for the respective provider
OLLAMA_BASE_URL=http://localhost:11434
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-proj-...
VLLM_BASE_URL=http://localhost:8001
```

---

## 🐳 Docker (Full Stack)

```bash
# Build and run everything
docker compose up --build

# Scale workers
docker compose up --scale worker=4

# Workers only (pointing at an external head node)
HEAD_NODE_IP=192.168.1.100 docker compose -f docker-compose.worker.yml up -d --scale worker=3
```

---

## 🧪 Running Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

---

## 📋 Ports

| Port | Service |
|---|---|
|| `3000` | Web Dashboard + API Gateway |
| `6379` | Redis / Valkey Message Broker |
| `11434` | Ollama (local model server) |
