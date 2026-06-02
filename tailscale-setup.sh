#!/usr/bin/env bash
# tailscale-setup.sh — Set up Tailscale for Younify cluster
# =========================================================
# Run this on the HEAD NODE to install Tailscale, authenticate,
# and print the connection command for worker machines.
#
# Usage:
#   bash tailscale-setup.sh
#
# What it does:
#   1. Installs Tailscale if not present
#   2. Starts Tailscale and prompts for auth
#   3. Prints the cluster's Tailscale IP
#   4. Generates the worker connection command
#
# On each worker, run the printed command (or use connect-to-cluster.sh).

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

echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║      Younify Tailscale Cluster Setup            ║${NC}"
echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── 1. Check / install Tailscale ────────────────────────────────────────────
if command -v tailscale &>/dev/null; then
    success "Tailscale is already installed."
else
    info "Installing Tailscale..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://tailscale.com/install.sh | sh
    else
        error "curl is required. Install it first."
        exit 1
    fi
    success "Tailscale installed."
fi

# ── 2. Check if Tailscale is already up ──────────────────────────────────────
TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
if [[ -n "$TS_IP" ]]; then
    success "Tailscale is already connected. IP: $TS_IP"
else
    info "Starting Tailscale (you may need to authenticate in your browser)..."
    sudo tailscale up
    TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -z "$TS_IP" ]]; then
        error "Failed to get Tailscale IP. Run 'sudo tailscale up' manually."
        exit 1
    fi
    success "Tailscale connected. IP: $TS_IP"
fi

# ── 3. Print cluster info ────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║         Cluster is ready on Tailscale           ║${NC}"
echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Head node Tailscale IP:${NC}  ${TS_IP}"
echo ""
echo -e "  ${YELLOW}To connect a worker machine, run:${NC}"
echo ""
echo -e "    curl -sfL https://raw.githubusercontent.com/Vector3451/Younify/main/connect-to-cluster.sh | bash -s -- ${TS_IP}"
echo ""
echo -e "  ${YELLOW}Or manually:${NC}"
echo ""
echo -e "    bash <(curl -sfL https://raw.githubusercontent.com/Vector3451/Younify/main/connect-to-cluster.sh) ${TS_IP}"
echo ""

# ── 4. Save the IP for later reference ──────────────────────────────────────
echo "$TS_IP" > .tailscale-head-ip 2>/dev/null || true
info "Saved head node IP to .tailscale-head-ip"
echo ""
info "Done! Workers can now connect to ${TS_IP} to join the cluster."
