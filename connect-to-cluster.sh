#!/usr/bin/env bash
# connect-to-cluster.sh — Connect this machine to a Younify cluster
# ==================================================================
# Run this on any WORKER machine to join a Younify cluster via Tailscale.
#
# Usage:
#   bash connect-to-cluster.sh <head-node-tailscale-ip>
#
# Example:
#   bash connect-to-cluster.sh 100.100.100.100
#
# What it does:
#   1. Installs Tailscale if not present
#   2. Connects to Tailscale
#   3. Clones / pulls the Younify repo
#   4. Installs Python dependencies
#   5. Starts the cluster worker sidecar (connect to coordinator)
#
# Environment:
#   YOUNIFY_REPO   (default: https://github.com/Vector3451/Younify.git)
#   RPC_PORT       (default: 5000)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

HEAD_IP="${1:-}"
REPO="${YOUNIFY_REPO:-https://github.com/Vector3451/Younify.git}"
RPC_PORT="${RPC_PORT:-5000}"

if [[ -z "$HEAD_IP" ]]; then
    echo ""
    echo -e "  ${RED}Usage: bash connect-to-cluster.sh <head-node-tailscale-ip>${NC}"
    echo ""
    echo "  The head node IP is printed when you run tailscale-setup.sh on the head node."
    echo "  Example: bash connect-to-cluster.sh 100.100.100.100"
    echo ""
    exit 1
fi

echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║   Connecting to Younify Cluster via Tailscale   ║${NC}"
echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
info "Head node IP: ${HEAD_IP}"

# ── 1. Install Tailscale if needed ──────────────────────────────────────────
if ! command -v tailscale &>/dev/null; then
    info "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    success "Tailscale installed."
fi

# ── 2. Connect to Tailscale ─────────────────────────────────────────────────
TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
if [[ -z "$TS_IP" ]]; then
    info "Starting Tailscale (authenticate in your browser)..."
    sudo tailscale up
    TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -z "$TS_IP" ]]; then
        error "Failed to connect to Tailscale. Run 'sudo tailscale up' manually."
        exit 1
    fi
    success "Tailscale connected. IP: ${TS_IP}"
else
    success "Tailscale already connected. IP: ${TS_IP}"
fi

# ── 3. Verify we can reach the head node ────────────────────────────────────
info "Checking connectivity to head node (${HEAD_IP}:8050)..."
if curl -sf "http://${HEAD_IP}:8050/api/v1/health" &>/dev/null; then
    success "Head node coordinator is reachable."
else
    warn "Coordinator not reachable at ${HEAD_IP}:8050"
    warn "Make sure the head node is running:"
    warn "  sudo tailscale up"
    warn "  python3 -m uvicorn coordinator.coordinator:coordinator_app --host 0.0.0.0 --port 8050"
    warn "Continuing anyway (will retry)..."
fi

# ── 4. Clone / update Younify repo ──────────────────────────────────────────
if [[ -d "Younify" ]]; then
    info "Younify directory exists. Updating..."
    cd Younify
    git pull --rebase 2>/dev/null || true
else
    info "Cloning Younify from ${REPO}..."
    git clone "${REPO}" || {
        error "Failed to clone repo. Check internet or YOUNIFY_REPO."
        exit 1
    }
    cd Younify
fi

# ── 5. Install Python dependencies ──────────────────────────────────────────
info "Installing Python dependencies..."
python3 -m pip install --quiet redis requests 2>/dev/null || true

# Check if llama-rpc-server is available; if not, try to build it
if ! command -v llama-rpc-server &>/dev/null && [[ ! -f "llama-rpc-server" ]]; then
    warn "llama-rpc-server not found."
    warn "To build it: git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && cmake -B build -DLLAMA_RPC=ON && cmake --build build --config Release -j"
    warn "Then: cp build/bin/llama-rpc-server ~/Younify/"
    warn "For now, starting without it (coordinator will see no RPC server)."
fi

# ── 6. Start cluster worker ─────────────────────────────────────────────────
info "Starting cluster worker (connecting to ${HEAD_IP}:8050)..."
echo ""
echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}  Worker connected to cluster at ${HEAD_IP}${NC}"
echo -e "  ${GREEN}  Press Ctrl+C to disconnect.${NC}"
echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"
echo ""

COORDINATOR_URL="http://${HEAD_IP}:8050" \
    python3 worker/cluster_worker.py \
    --coordinator "http://${HEAD_IP}:8050" \
    --rpc-port "${RPC_PORT}"
