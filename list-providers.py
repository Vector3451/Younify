#!/usr/bin/env python3
"""
list-providers.py — Check which AI providers are configured and reachable.
Run this on a worker machine to verify your setup.

Usage:
    python3 list-providers.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker"))

from providers import _PROVIDER_REGISTRY, get_provider, parse_model_id


def check_provider(name):
    """Try to instantiate a provider and report status."""
    try:
        p = get_provider(name)
        return True, f"OK ({p.__class__.__name__})"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("=" * 55)
    print("  Younify Provider Status")
    print("=" * 55)

    for name in sorted(_PROVIDER_REGISTRY.keys()):
        ok, msg = check_provider(name)
        status = "✅" if ok else "❌"
        print(f"  {status} {name:12s} — {msg}")

    print()
    print("  Environment variables:")
    for var in ["OLLAMA_BASE_URL", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "VLLM_BASE_URL", "VLLM_API_KEY"]:
        val = os.environ.get(var, "")
        if val:
            # Mask API keys
            if "KEY" in val:
                val = val[:8] + "..." if len(val) > 8 else "***"
            print(f"    {var} = {val}")
        else:
            print(f"    {var} = (not set)")

    # Test Ollama reachability if configured
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"\n  Ollama ({ollama_url}):")
    try:
        import requests
        resp = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            if models:
                for m in models:
                    print(f"    📦 {m.get('name', 'unknown')}")
            else:
                print("    (no models loaded)")
        else:
            print(f"    ❌ HTTP {resp.status_code}")
    except Exception as e:
        print(f"    ❌ Unreachable: {e}")

    print()


if __name__ == "__main__":
    main()
