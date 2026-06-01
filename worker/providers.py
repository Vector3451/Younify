"""
providers.py — Multi-provider AI inference layer
=================================================
Unified interface for calling different AI backends.

Supported providers:
    ollama     — Local Ollama server (http://localhost:11434)
    openrouter — OpenRouter API (https://openrouter.ai/api/v1)
    openai     — OpenAI API (https://api.openai.com/v1)
    vllm       — Local vLLM server (http://localhost:8000/v1)

Usage:
    provider = get_provider("ollama")
    result = provider.generate("llama3", "Hello!", max_tokens=256)

Model ID format in API requests:
    "ollama/llama3:7b"          → Ollama backend, model llama3:7b
    "openrouter/meta/llama-70b" → OpenRouter backend
    "openai/gpt-4o"             → OpenAI backend
    "vllm/meta-llama/Llama-3-8B" → vLLM backend

Configuration via environment variables:
    OLLAMA_BASE_URL     (default: http://localhost:11434)
    OPENROUTER_API_KEY  (required for OpenRouter)
    OPENAI_API_KEY      (required for OpenAI)
    VLLM_BASE_URL       (default: http://localhost:8000)
"""

import os
import time
import json
from abc import ABC, abstractmethod
from typing import Optional

import requests


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------
class BaseProvider(ABC):
    """Abstract base class for all inference providers."""

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
        """
        Run inference and return a standardized result dict.

        Returns:
            {
                "model": str,
                "completion": str,
                "prompt_tokens": int,
                "completion_tokens": int,
            }
        """
        ...

    def _default_result(self, model: str, completion: str) -> dict:
        """Helper to build a standardized result dict."""
        return {
            "model": model,
            "completion": completion,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        }


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------
class OllamaProvider(BaseProvider):
    """Talks to a local or remote Ollama server."""

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


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (works for OpenAI, vLLM, and any OpenAI-clone)
# ---------------------------------------------------------------------------
class OpenAICompatibleProvider(BaseProvider):
    """Generic OpenAI-compatible API client."""

    def __init__(self, name: str, base_url: str, api_key: str = ""):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session = requests.Session()
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    def generate(self, model: str, prompt: str, max_tokens: int = 2048, temperature: float = 0.7, **kwargs) -> dict:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = {}
        api_key = kwargs.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        resp = self._session.post(url, json=payload, headers=headers, timeout=300)
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


# ---------------------------------------------------------------------------
# Provider registry & factory
# ---------------------------------------------------------------------------

# Built-in provider constructors
_PROVIDER_REGISTRY = {
    "ollama": lambda: OllamaProvider(),
    "openrouter": lambda: OpenAICompatibleProvider(
        name="openrouter",
        base_url="https://openrouter.ai/api",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    ),
    "openai": lambda: OpenAICompatibleProvider(
        name="openai",
        base_url="https://api.openai.com",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    ),
    "vllm": lambda: OpenAICompatibleProvider(
        name="vllm",
        base_url=os.environ.get("VLLM_BASE_URL", "http://localhost:8000"),
        api_key=os.environ.get("VLLM_API_KEY", ""),
    ),
}


def register_provider(name: str, factory):
    """Register a custom provider. Call this at worker startup."""
    _PROVIDER_REGISTRY[name] = factory


def get_provider(provider_name: str) -> BaseProvider:
    """
    Get a provider instance by name.

    Args:
        provider_name: One of 'ollama', 'openrouter', 'openai', 'vllm',
                       or a custom-registered name.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    if provider_name not in _PROVIDER_REGISTRY:
        available = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
        raise ValueError(
            f"Unknown provider '{provider_name}'. Available: {available}"
        )
    return _PROVIDER_REGISTRY[provider_name]()


def parse_model_id(model_id: str):
    """
    Parse a model ID string into (provider_name, model_name).

    Format: "provider/model-name"
    Falls back to Ollama if no prefix is given.

    Examples:
        "ollama/llama3:7b"           → ("ollama", "llama3:7b")
        "openrouter/moonshotai/kimi" → ("openrouter", "moonshotai/kimi")
        "openai/gpt-4o"              → ("openai", "gpt-4o")
        "llama3"                     → ("ollama", "llama3")  [default]
    """
    if "/" in model_id:
        provider_name, _, model_name = model_id.partition("/")
        provider_name = provider_name.strip().lower()
        return provider_name, model_name.strip()
    # Default: treat as Ollama model
    return "ollama", model_id


def run_inference(
    model_id: str,
    prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    **kwargs,
) -> dict:
    """
    High-level convenience function: parse model_id, pick provider, run.

    Args:
        model_id: Provider-prefixed model ID, e.g. "ollama/llama3:7b"
        prompt:   The user's prompt
        max_tokens: Max tokens to generate
        temperature: Sampling temperature

    Returns:
        dict with keys: model, completion, prompt_tokens, completion_tokens
    """
    provider_name, model_name = parse_model_id(model_id)
    provider = get_provider(provider_name)
    return provider.generate(
        model=model_name,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs,
    )
