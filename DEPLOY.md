# 🚀 Phase 3: Multi-Machine Deployment Guide

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HEAD NODE (1 machine)                                      │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │  API Gateway  │───►│    Redis     │◄──────────────────┐  │
│  │  :8000 (Docker)│   │  :6379 (Docker)│                  │  │
│  └──────────────┘    └──────────────┘                    │  │
│                                                          │  │
└──────────────────────────────────────────────────────────┼──┘
                                                           │
              ┌────────────────────────────────────────────┤
              │                                            │
        ┌─────▼─────┐                              ┌──────▼─────┐
        │  Worker M1  │                              │  Worker M2  │
        │             │                              │             │
        │  Ollama     │                              │  Ollama     │
        │  GPU        │                              │  GPU        │
        │  (host)     │                              │  (host)     │
        └─────────────┘                              └─────────────┘

        ┌─────────────┐        ...               ┌─────────────┐
        │  Worker M3   │                          │  Worker M30  │
        │             │                              │             │
        │  Ollama     │                              │  Ollama     │
        │  GPU        │                              │  GPU        │
        │  (host)     │                              │  (host)     │
        └─────────────┘                              └─────────────┘
```

**Key design decision:** Workers run **directly on the host** (not in Docker) so they have native access to Ollama, GPUs, and other hardware. Only the API Gateway and Redis run in Docker.

## Prerequisites

- **Head node:** Docker + Docker Compose installed
- **Worker machines:** Python 3.10+ and `pip` installed
- Ollama (or other AI backend) running on each worker machine
- All machines on the same network
- Port 6379 (Redis) and 8000 (API) open on the head node

## Step 1: Set Up the Head Node

On one machine that will act as the control plane:

```bash
cd /path/to/Younify

# Build images and start Redis + API Gateway
docker compose up -d --build redis api

# Note the machine's IP
hostname -I
```

Verify:
```bash
curl http://localhost:8000/
# → {"service":"AI Inference Gateway","redis_connected":true}
```

## Step 2: Deploy Workers on Each Machine

On **each worker machine** (all 29 of them):

```bash
# Install Python dependency
pip install redis requests

# Point to the head node and start a worker
REDIS_HEAD_IP=192.168.1.100 bash run-worker.sh
```

Or start multiple workers per machine:
```bash
REDIS_HEAD_IP=192.168.1.100 bash run-worker.sh 3
```

### Using Docker for workers (no Ollama/GPU needed)

For machines that only need queue processing without local AI:
```bash
docker compose -f docker-compose.worker.yml up -d --scale worker=2
```

## Step 3: Test the Cluster

```bash
# Submit a job
curl -X POST http://192.168.1.100:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello from the cluster!", "model_id": "ollama/llama3:7b"}'

# Poll for results
curl http://192.168.1.100:8000/api/v1/status/JOB_ID
```

## Model Routing (`model_id` format)

Jobs are routed to AI backends based on the `model_id` prefix:

| Prefix | Backend | Example |
| :--- | :--- | :--- |
| `ollama/` | Local Ollama server | `ollama/llama3:7b` |
| `openrouter/` | OpenRouter API | `openrouter/meta-llama/llama-3.1-70b-instruct` |
| `openai/` | OpenAI API | `openai/gpt-4o` |
| `vllm/` | Local vLLM server | `vllm/meta-llama/Llama-3-8B-Instruct` |
| *(none)* | Defaults to Ollama | `llama3:7b` |

## Scaling

- **Per machine:** `bash run-worker.sh N` runs N parallel workers
- **Per cluster:** Run `run-worker.sh` on each machine
- **Per Docker:** `docker compose up --scale worker=N`

Redis automatically load-balances — whichever worker is free first picks up the next job.

## Troubleshooting

| Problem | Fix |
|---|---|
| Worker can't reach Redis | `ufw allow 6379` on head node |
| Ollama connection refused | Verify Ollama: `curl localhost:11434/api/tags` |
| Job stuck in QUEUED | Check: `docker exec younify-redis redis-cli LLEN inference_tokens` |
| Worker crashes on start | Check Python deps: `pip install redis requests` |

## Adding a Custom Provider

Edit `worker/providers.py` and register a new provider:

```python
from providers import register_provider, OpenAICompatibleProvider

register_provider("mybackend", lambda: OpenAICompatibleProvider(
    name="mybackend",
    base_url="https://api.mybackend.com",
    api_key=os.environ.get("MY_BACKEND_KEY", ""),
))
```

Then use `"mybackend/model-name"` in your API requests.
