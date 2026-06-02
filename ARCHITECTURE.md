# 🏛️ Architecture — Younify Distributed AI Inference System

## 🎯 Goal

Build a **highly available, horizontally scalable** distributed system that accepts AI inference requests via a central API, fans them out through a persistent message queue to a pool of heterogeneous worker nodes, and returns results asynchronously — supporting local and cloud-based model providers simultaneously.

---

## 🗺️ System Architecture (Current State)

```
                        ┌─────────────────────────────┐
  Browser / Client ────►│   FastAPI API Gateway        │
                        │   Port 3000                  │
                        │                              │
                        │  ┌────────────────────────┐  │
                        │  │   Web Dashboard SPA    │  │
                        │  │   Chat · Submit · Jobs │  │
                        │  │   Cluster · Settings   │  │
                        │  └────────────────────────┘  │
                        └──────────────┬──────────────┘
                                       │  LPUSH task
                                       ▼
                        ┌─────────────────────────────┐
                        │   Redis / Valkey Broker      │
                        │   Port 6379                  │
                        │                              │
                        │   Queue: inference_tasks     │
                        │   Keys:  inference_result:*  │
                        └──────┬──────────────┬────────┘
                               │ BRPOP        │ BRPOP
                    ┌──────────▼──┐      ┌────▼──────────┐
                    │  Worker A   │      │   Worker B    │   ...N workers
                    │  Machine 1  │      │   Machine 2   │
                    │             │      │               │
                    │  Ollama     │      │  Ollama       │
                    │  tinyllama  │      │  llama3:8b    │
                    └─────────────┘      └───────────────┘
```

Workers write results back to Redis under `inference_result:<job_id>`.  
The API Gateway polls Redis on `GET /api/v1/status/{job_id}` — no direct worker-to-gateway connection is needed.

---

## 🧩 Component Details

| Component | Technology | Responsibility | Scaling |
|---|---|---|---|
| **Web Dashboard** | Vanilla HTML/CSS/JS (SPA) | Chat UI, job submission, history, cluster view, settings | Stateless — served from gateway |
| **API Gateway** | FastAPI (Python) | Validates requests, enqueues tasks to Redis, serves dashboard, proxies status queries | Horizontal (stateless) |
| **Message Broker** | Redis / Valkey 7+ | Persistent FIFO task queue; job result storage | Redis Cluster for HA |
| **Worker Service** | Python | Blocks on `BRPOP`, runs inference via provider, writes result back to Redis | Horizontal — add workers freely |
| **Provider Layer** | Python (`providers.py`) | Abstracts Ollama, OpenRouter, OpenAI, vLLM behind a single `generate()` interface | Per-worker config via env vars |

---

## 🖥️ Web Dashboard — Panels

The dashboard is a fully client-side SPA served at `/` by the FastAPI gateway. No build step — all HTML, CSS, and JS are inlined in `api_gateway/dashboard.py`.

| Panel | Key Features |
|---|---|
| **Dashboard** | Live KPI cards, Chart.js throughput line chart, status doughnut chart, recent activity feed |
| **Chat** | Real-time conversation UI — user/assistant bubbles, animated typing indicator, per-message token/duration metadata, provider+model selector, auto-resize input |
| **Submit Job** | Advanced form with temperature & token sliders, quick-fill preset templates (Distributed Computing, Code Refactor, Creative Sci-Fi), provider+model dropdowns |
| **Jobs History** | Persistent `localStorage` log, search, status filter tabs, slide-out inspect drawer with raw JSON toggle |
| **Cluster Topology** | Gateway + Redis + Worker node status cards, installed Ollama model registry, supported backend integrations grid |
| **Settings** | Secure API key management for OpenRouter, OpenAI, vLLM — stored in `localStorage` only, injected per-job at dispatch time, show/hide eye toggles |

---

## 🔗 Provider Abstraction (`worker/providers.py`)

All providers implement a common `BaseProvider.generate()` interface:

```python
def generate(model, prompt, max_tokens, temperature, **kwargs) -> dict:
    # Returns: {model, completion, prompt_tokens, completion_tokens}
```

| Provider Name | Backend | Auth |
|---|---|---|
| `ollama` | Local Ollama HTTP API | None (local) |
| `openrouter` | `https://openrouter.ai/api/v1` | Bearer token (`api_key` kwarg or `OPENROUTER_API_KEY` env) |
| `openai` | `https://api.openai.com/v1` | Bearer token (`api_key` kwarg or `OPENAI_API_KEY` env) |
| `vllm` | Configurable base URL | Optional Bearer token |

API keys can be provided two ways (in order of priority):
1. **Per-job** — passed in the task payload as `api_key` (set via the Settings panel in the UI)
2. **Environment variable** — `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `VLLM_API_KEY` on the worker host

---

## 📡 API Contract

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves the web dashboard SPA |
| `GET` | `/api/v1/health` | `{service, version, redis_connected}` |
| `GET` | `/api/v1/models` | `{ollama: [...], openrouter: [], openai: [], vllm: []}` |
| `POST` | `/api/v1/generate` | Submit job → `{job_id, status: "QUEUED", message}` |
| `GET` | `/api/v1/status/{job_id}` | `{job_id, status, result, error, started, completed}` |

**Job payload schema:**
```json
{
  "prompt":      "string (required)",
  "model_id":    "provider/model-name (required)",
  "max_tokens":  2048,
  "temperature": 0.7,
  "api_key":     "optional — overrides env var for this job only"
}
```

**Job status lifecycle:**  
`QUEUED` → `PROCESSING` → `COMPLETED` | `FAILED`

---

## 🌐 Distributed Deployment (Multi-Machine)

The architecture is **inherently distributed** via the Redis broker. Workers from any machine on the network can connect to the same Redis instance and pull jobs.

```
Head Node (runs Redis + API Gateway)
  │
  ├── valkey-server --bind 0.0.0.0 --port 6379
  └── uvicorn api_gateway.main:app --host 0.0.0.0 --port 3000

Worker Nodes (any number of machines)
  └── REDIS_HOST=<head_ip> python3 worker/worker.py
       (each worker uses its own local Ollama / vLLM)
```

**Docker Compose (worker nodes):**
```bash
HEAD_NODE_IP=192.168.1.100 \
docker compose -f docker-compose.worker.yml up -d --scale worker=4
```

---

## 🛣️ Development Roadmap

### ✅ Phase 1 — Redis Decoupling (Complete)
- Replaced in-memory queue with Redis/Valkey
- API Gateway publishes tasks; Workers consume via `BRPOP`
- Job results persisted in Redis with full status lifecycle

### ✅ Phase 2 — Web Dashboard (Complete)
- Premium glassmorphic SPA dashboard
- Chat panel with real-time conversation and polling
- Job history with localStorage persistence and inspect drawer
- Settings panel for secure per-browser API key management
- Analytics with Chart.js (throughput + status breakdown)

### 🔜 Phase 3 — Containerization
- Docker images for API Gateway and Worker
- `docker-compose.yml` for full local stack
- `docker-compose.worker.yml` for remote worker-only deployment

### 🔜 Phase 4 — Production Distribution
- Kubernetes `Deployment` manifests for gateway and worker pools
- Redis Cluster or managed Redis (ElastiCache / Upstash) for HA broker
- Horizontal Pod Autoscaler on worker deployment based on queue depth
- Nginx / cloud Load Balancer in front of stateless API Gateway replicas
- MinIO / S3 for shared model weight storage across worker nodes

---

## 🔒 Security Notes

- **API keys are never stored server-side.** The Settings panel writes keys to the browser's `localStorage`. They are included in job payloads only at dispatch time and travel encrypted over HTTPS in production.
- For production, the Redis port (6379) should be firewalled — accessible only from worker/gateway hosts, not the public internet.
- Consider adding an API key / JWT auth middleware to the FastAPI gateway before exposing it publicly.

---

*Stack: FastAPI · Redis/Valkey · Ollama · OpenRouter · OpenAI · vLLM · Vanilla JS · Chart.js*