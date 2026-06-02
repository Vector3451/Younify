"""
cluster_provider.py — Cluster Inference Provider
=================================================
Sends inference requests directly to the coordinator, which
proxies to llama-server (running with RPC across all workers).

No job queue involved — direct inference.
"""

import os
import requests


class ClusterProvider:
    """Cluster provider — matches BaseProvider interface via duck typing."""

    name = "cluster"

    def __init__(self, coordinator_url: str = None):
        self.coordinator_url = (
            coordinator_url or os.environ.get("COORDINATOR_URL", "http://localhost:8050")
        ).rstrip("/")

    def generate(self, model: str, prompt: str, max_tokens: int = 2048,
                 temperature: float = 0.7, **kwargs) -> dict:
        url = f"{self.coordinator_url}/api/v1/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()
        data = resp.json()

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})

        return {
            "model": data.get("model", model),
            "completion": message.get("content", ""),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        }


# Register with the providers module (deferred import avoids circular dep)
from providers import register_provider  # noqa: E402
register_provider("cluster", lambda: ClusterProvider())
