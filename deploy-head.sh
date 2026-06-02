#!/usr/bin/env bash
# =============================================================================
# deploy-head.sh
# =============================================================================
# Runs on the HEAD NODE: starts Redis + API Gateway.
# All worker machines connect to this machine's IP.
#
# Usage:
#   1. On the machine that will be the head node.
#   2. Edit NETWORK_INTERFACE if needed (defaults to first non-loopback IPv4).
#   3. Run: bash deploy-head.sh
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
REDIS_PORT="${REDIS_PORT:-6379}"
API_PORT="${API_PORT:-3000}"

# Auto-detect IP of the first non-loopback interface
MY_IP=$(hostname -I | awk '{print $1}')
echo "[HEAD] This machine's IP: ${MY_IP}"
echo "[HEAD] Redis will listen on: ${MY_IP}:${REDIS_PORT}"
echo "[HEAD] ⚠️  Use this IP in deploy-workers.sh on worker machines: HEAD_NODE_IP=${MY_IP}"
echo ""

# ── Stop existing stack ──────────────────────────────────────────────────────
docker compose down 2>/dev/null || true

# ── Start stack ──────────────────────────────────────────────────────────────
export REDIS_PORT API_PORT
echo "[HEAD] Building and starting Redis + API Gateway..."
docker compose up -d --build redis api

# ── Wait for health ──────────────────────────────────────────────────────────
echo "[HEAD] Waiting for API to be healthy..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT}/" > /dev/null 2>&1; then
        HEALTH=$(curl -sf "http://localhost:${API_PORT}/" 2>/dev/null)
        echo "[HEAD] API is up: ${HEALTH}"
        echo ""
        echo "======================================"
        echo "  HEAD NODE READY"
        echo "  IP:     ${MY_IP}"
        echo "  Redis:  ${REDIS_PORT}"
        echo "  API:    http://${MY_IP}:${API_PORT}"
        echo "======================================"
        exit 0
    fi
    sleep 1
done

echo "[HEAD] Warning: API did not respond within 30 seconds. Check logs:"
docker compose logs api
