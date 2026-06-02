"""
providers.py — AI inference provider layer
===========================================
Unified interface for running inference. Currently supports
Ollama locally and cluster-based distributed inference.

Usage:
    provider = get_provider("ollama")
    result = provider.generate("llama3", "Hello!", max_tokens=256)

Model ID format:
    "ollama/llama3:7b"   → Ollama backend, model llama3:7b
    "cluster/my-model"   → Cluster distributed inference
    "llama3"             → Defaults to Ollama
"""

import os
import time
import json
from abc import ABC, abstractmethod

import requests

from cluster_provider import ClusterProvider  # noqa: F401


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(
        self,
        model: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        ...

    def _default_result(self, model: str, completion: str) -> dict:
        return {
            "model": model,
            "completion": completion,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def generate(self, model: str, prompt: str, max_tokens: int = 2048, temperature: float = 0.7, **kwargs) -> dict:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()

        return {
            "model": data.get("model", model),
            "completion": data.get("response", ""),
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }


_PROVIDER_REGISTRY = {
    "ollama": lambda: OllamaProvider(),
}


def register_provider(name: str, factory):
    _PROVIDER_REGISTRY[name] = factory


def get_provider(provider_name: str) -> BaseProvider:
    if provider_name not in _PROVIDER_REGISTRY:
        available = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available: {available}"
        )
    return _PROVIDER_REGISTRY[provider_name]()


def parse_model_id(model_id: str):
    if "/" in model_id:
        provider_name, _, model_name = model_id.partition("/")
        provider_name = provider_name.strip().lower()
        return provider_name, model_name.strip()
    return "ollama", model_id


def run_inference(
    model_id: str,
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    **kwargs,
) -> dict:
    provider_name, model_name = parse_model_id(model_id)
    provider = get_provider(provider_name)
    return provider.generate(
        model=model_name,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs,
    )
