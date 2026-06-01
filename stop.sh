#!/usr/bin/env bash
# =============================================================================
# stop.sh — Stop everything
# =============================================================================
# Stops the Docker stack and kills any local worker processes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}[INFO]${NC} Stopping Younify..."

# Stop Docker stack
docker compose down --remove-orphans 2>/dev/null || true

# Kill any lingering worker processes
pkill -f "python3 worker/worker.py" 2>/dev/null || true
pkill -f "python worker/worker.py" 2>/dev/null || true

echo -e "${GREEN}[OK]${NC} Everything stopped."
