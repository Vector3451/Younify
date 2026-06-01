# 🤖 AI Model Service API Contract (v1)

This document serves as the definitive contract for the Asynchronous Inference Service API.

## 1. Core Endpoint Specification

| Detail | Value |
| :--- | :--- |
| **Base URL** | `https://api.yourdomain.com/api/v1/` |
| **Submit Endpoint** | `/generate` |
| **Status Endpoint** | `/status/{job_id}` |
| **HTTP Method** | `POST` (generate), `GET` (status) |
| **Content-Type** | `application/json` |

## 2. Request Body (Input Payload)

| Field | Type | Required | Validation Rules | Description |
| :--- | :--- | :--- | :--- | :--- |
| `prompt` | `string` | **Yes** | Non-empty string | The core instruction or text query. |
| `max_tokens` | `integer` | No | Must be > 0 | Maximum tokens to generate. Default: `2048`. |
| `temperature` | `number` | No | Range: `0.0` to `1.0` | Controls creativity. Default: `0.7`. |
| `model_id` | `string` | No | Format: `provider/model` | See provider table below. Default: `ollama/llama3`. |

### Model ID Format

The `model_id` field uses the format `provider/model-name` to route inference:

| Prefix | Provider | Example `model_id` |
| :--- | :--- | :--- |
| `ollama/` | Local Ollama server | `ollama/llama3:7b`, `ollama/gemma2:9b` |
| `openrouter/` | OpenRouter API | `openrouter/meta-llama/llama-3.1-70b-instruct` |
| `openai/` | OpenAI API | `openai/gpt-4o`, `openai/gpt-4o-mini` |
| `vllm/` | Local vLLM server | `vllm/meta-llama/Llama-3-8B-Instruct` |

If no prefix is given, `ollama/` is assumed as the default.

## 3. Response Bodies

### A. Submit Response (HTTP 202 Accepted)

```json
{
  "job_id": "msg_a1b2c3d4e5",
  "status": "QUEUED",
  "message": "Job received and queued. Poll /api/v1/status/{job_id} for results."
}
```

### B. Status Response — Processing States

**QUEUED** (waiting for a worker):
```json
{
  "job_id": "msg_a1b2c3d4e5",
  "status": "QUEUED",
  "result": null,
  "error": null
}
```

**PROCESSING** (worker is running inference):
```json
{
  "job_id": "msg_a1b2c3d4e5",
  "status": "PROCESSING",
  "result": null,
  "error": null,
  "started": 1717000000.0,
  "completed": null
}
```

**COMPLETED** (inference finished successfully):
```json
{
  "job_id": "msg_a1b2c3d4e5",
  "status": "COMPLETED",
  "result": {
    "model": "llama3:7b",
    "completion": "The capital of France is Paris.",
    "prompt_tokens": 12,
    "completion_tokens": 8
  },
  "error": null,
  "started": 1717000000.5,
  "completed": 1717000002.3
}
```

**FAILED** (inference errored):
```json
{
  "job_id": "msg_a1b2c3d4e5",
  "status": "FAILED",
  "result": null,
  "error": "Connection refused: Ollama not reachable",
  "started": 1717000000.5,
  "completed": 1717000001.0
}
```

### C. Error Responses

| HTTP Code | Meaning | Example |
| :--- | :--- | :--- |
| `400` | Invalid payload | Missing `prompt`, invalid `temperature` |
| `404` | Job not found | Unknown `job_id` |
| `503` | Redis unavailable | Broker connection lost |
