"""
run-worker.sh — Start a worker directly on the host (no Docker)
=================================================================
Use this on each lab machine that has Ollama or GPU access.
No container networking headaches — the worker accesses localhost directly.

Prerequisites:
    pip install redis requests

Usage:
    # Basic (connects to local Redis, uses local Ollama)
    bash run-worker.sh

    # Point to a remote Redis (head node)
    REDIS_HOST=192.168.1.100 bash run-worker.sh

    # Custom Ollama URL
    OLLAMA_BASE_URL=http://192.168.1.50:11434 bash run-worker.sh

    # Run multiple workers on this machine
    bash run-worker.sh 3
"""

set -euo pipefail

NUM_WORKERS="${1:-1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  Younify Host Worker Launcher"
echo "============================================"
echo "  Redis:    ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
echo "  Ollama:   ${OLLAMA_BASE_URL:-http://localhost:11434}"
echo "  Workers:  ${NUM_WORKERS}"
echo "============================================"

for i in $(seq 1 "${NUM_WORKERS}"); do
    echo "[LAUNCH] Starting worker ${i}/${NUM_WORKERS}..."
    python3 "${SCRIPT_DIR}/worker/worker.py" &
done

echo "[LAUNCH] All ${NUM_WORKERS} worker(s) started. Press Ctrl+C to stop."
wait
