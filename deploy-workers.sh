#!/usr/bin/env bash
# =============================================================================
# deploy-workers.sh
# =============================================================================
# Deploys ONE worker container to THIS machine, pointed at the head node's Redis.
#
# Usage:
#   1. Copy this script to each worker machine.
#   2. Edit HEAD_NODE_IP below (or pass it as an argument).
#   3. Run: bash deploy-workers.sh [NUM_WORKERS]
#
# NUM_WORKERS defaults to 1 (containers per machine).
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
# IP of the machine running the API Gateway + Redis
# Override with: HEAD_NODE_IP=192.168.1.100 bash deploy-workers.sh
HEAD_NODE_IP="${HEAD_NODE_IP:-192.168.1.100}"
REDIS_PORT="${REDIS_PORT:-6379}"
IMAGE="younify-worker"
NUM_WORKERS="${1:-1}"

# Build the worker image on this machine
echo "[DEPLOY] Building ${IMAGE}..."
docker build -t "${IMAGE}" -f worker/Dockerfile .

# Pull the latest image if a registry is available (optional)
# docker pull your-registry/younify-worker:latest
# IMAGE="your-registry/younify-worker:latest"

echo "[DEPLOY] Head node: ${HEAD_NODE_IP}:${REDIS_PORT}"
echo "[DEPLOY] Starting ${NUM_WORKERS} worker container(s) on $(hostname)..."

for i in $(seq 1 "${NUM_WORKERS}"); do
    if docker ps -q --filter "name=younify-worker-${i}" | grep -q .; then
        echo "[DEPLOY] Worker ${i} already running, stopping old instance..."
        docker stop "younify-worker-${i}" 2>/dev/null || true
        docker rm "younify-worker-${i}" 2>/dev/null || true
    fi

    docker run -d \
        --name "younify-worker-${i}" \
        --restart unless-stopped \
        -e "REDIS_HOST=${HEAD_NODE_IP}" \
        -e "REDIS_PORT=${REDIS_PORT}" \
        -e "REDIS_DB=0" \
        "${IMAGE}"

    echo "[DEPLOY] Worker ${i} started (container: younify-worker-${i})"
done

echo "[DEPLOY] Done. ${NUM_WORKERS} worker(s) running on $(hostname)."
echo "[DEPLOY] Workers will auto-restart on reboot (unless-stopped)."
