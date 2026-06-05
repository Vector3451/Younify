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

    def warmup(self, model: str) -> bool:
        """Preload model into VRAM so first real request is fast.
        Returns True if warmup succeeded."""
        return False

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
        self._vram_mb = self._detect_vram()
        # OLLAMA_NUM_GPU environment variable:
        #   -1 = auto (default) — Ollama offloads as many layers as VRAM allows
        #    0 = CPU only
        #    N = put N layers on GPU
        raw = os.environ.get("OLLAMA_NUM_GPU", "-1")
        try:
            self.num_gpu = int(raw) if raw.strip() else -1
        except ValueError:
            print(f"[OLLAMA] Invalid OLLAMA_NUM_GPU={raw!r}, defaulting to -1 (auto)")
            self.num_gpu = -1
        # Keep model warm in VRAM between requests (default 1 hour, set to -1 for indefinite)
        self.keep_alive = os.environ.get("OLLAMA_KEEP_ALIVE", "3600s")
        if self._vram_mb:
            print(f"[OLLAMA] Detected {self._vram_mb} MB free VRAM, num_gpu={self.num_gpu}")

    @staticmethod
    def _detect_vram() -> int:
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                vrams = [int(x.strip()) for x in result.stdout.strip().split("\n") if x.strip()]
                return sum(vrams)
        except Exception:
            pass
        return 0

    def warmup(self, model: str) -> bool:
        """Preload model into VRAM by sending a trivial prompt."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": "hello",
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {"num_predict": 1},
            }
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            print(f"[OLLAMA] Model '{model}' warmed up and kept alive ({self.keep_alive})")
            return True
        except Exception as e:
            print(f"[OLLAMA] Warmup failed for '{model}': {e}")
            return False

    def generate(self, model: str, prompt: str, max_tokens: int = 2048, temperature: float = 0.7, **kwargs) -> dict:
        url = f"{self.base_url}/api/generate"

        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
        }

        num_gpu = kwargs.get("num_gpu", self.num_gpu)
        if num_gpu >= 0:
            options["num_gpu"] = num_gpu

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": options,
        }

        resp = requests.post(url, json=payload, timeout=600)
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


# Import cluster_provider so it auto-registers with the registry
import cluster_provider  # noqa: F401
