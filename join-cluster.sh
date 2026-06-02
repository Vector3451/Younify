#!/usr/bin/env bash
# =============================================================================
# join-cluster.sh — One-command worker setup for lab machines
# =============================================================================
# Usage on the SECOND machine:
#   curl -fsSL https://raw.githubusercontent.com/Vector3451/Younify/main/join-cluster.sh | bash -s -- --redis 100.99.5.102
#
# Or manually:
#   bash join-cluster.sh --redis 100.99.5.102
# =============================================================================

set -euo pipefail

REDIS_HOST=""
BRANCH="main"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --redis) REDIS_HOST="$2"; shift 2 ;;
        --branch) BRANCH="$2"; shift 2 ;;
        -h|--help) sed -n '2,15p' "$0" | sed 's/^# \?//'; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$REDIS_HOST" ]]; then
    echo "Usage: bash join-cluster.sh --redis <HEAD_NODE_IP>"
    echo "Example: bash join-cluster.sh --redis 100.99.5.102"
    exit 1
fi

echo "============================================"
echo "  Younify Worker — Cluster Join"
echo "============================================"
echo "  Redis:     $REDIS_HOST:6379"

# Check Ollama
if command -v ollama &>/dev/null; then
    OLLAMA_URL="http://localhost:11434"
    if curl -sf "$OLLAMA_URL/api/tags" &>/dev/null; then
        MODELS=$(curl -sf "$OLLAMA_URL/api/tags" | python3 -c "
import sys,json; ms=json.load(sys.stdin).get('models',[]); print(len(ms))" 2>/dev/null || echo "?")
        echo "  Ollama:    OK ($MODELS model(s))"
    else
        echo "  Ollama:    Installed but not running. Start with: ollama serve"
        OLLAMA_URL=""
    fi
else
    echo "  Ollama:    Not installed. Install: curl -fsSL https://ollama.com/install.sh | sh"
    OLLAMA_URL=""
fi

echo "============================================"
echo ""

# Clone or update repo
REPO_DIR="$HOME/Younify"
if [[ -d "$REPO_DIR" ]]; then
    echo "[SETUP] Updating existing repo..."
    cd "$REPO_DIR" && git pull origin "$BRANCH" 2>/dev/null || true
else
    echo "[SETUP] Cloning repo..."
    git clone --branch "$BRANCH" https://github.com/Vector3451/Younify.git "$REPO_DIR"
fi

cd "$REPO_DIR"

# Install Python deps
echo "[SETUP] Installing Python dependencies..."
pip3 install -q redis requests 2>/dev/null || pip install -q redis requests

echo ""
echo "[START] Connecting to Redis at $REDIS_HOST:6379 ..."
echo "[START] Press Ctrl+C to disconnect."
echo ""

# Start worker
REDIS_HOST="$REDIS_HOST" OLLAMA_BASE_URL="${OLLAMA_URL:-http://localhost:11434}" \
    python3 worker/worker.py
