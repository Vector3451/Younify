#!/usr/bin/env bash
# =============================================================================
# start.sh — Younify All-in-One Launcher
# =========================================
# Starts the complete stack: Redis, API Gateway (with Web UI), and local
# worker(s) — all from a single command.
#
# Usage:
#   bash start.sh              # Start everything with defaults
#   bash start.sh --workers 3  # Start with N local workers
#   bash start.sh --head-only  # Only start Redis + API (no local worker)
#   bash stop.sh               # Stop everything
#
# What it does:
#   1. Checks Docker is running
#   2. Starts Redis + API Gateway via Docker Compose
#   3. Waits for the API to be healthy
#   4. Installs Python dependencies if needed
#   5. Starts N local host workers (default: 1)
#   6. Prints the dashboard URL
#   7. Waits for Ctrl+C, then shuts everything down cleanly
#
# Dashboard: http://localhost:3000
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUM_WORKERS=1
HEAD_ONLY=false
CLUSTER_MODE=false
COORDINATOR_ONLY=false
API_PORT=3000
REDIS_PORT=6379

# ── Parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --workers|-w)  NUM_WORKERS="$2"; shift 2 ;;
        --head-only)   HEAD_ONLY=true; shift ;;
        --cluster)     CLUSTER_MODE=true; shift ;;
        --coordinator-only) COORDINATOR_ONLY=true; shift ;;
        --port|-p)     API_PORT="$2"; shift 2 ;;
        --redis-port)  REDIS_PORT="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,25p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$SCRIPT_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

cleanup() {
    echo ""
    info "Shutting down..."

    # Kill local workers
    if [[ -n "${WORKER_PIDS:-}" ]]; then
        for pid in $WORKER_PIDS; do
            kill "$pid" 2>/dev/null || true
        done
        info "Local workers stopped."
    fi

    # Stop Docker stack
    docker compose down --remove-orphans 2>/dev/null || true
    info "Docker stack stopped."
    success "Younify stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# ── Check Docker ─────────────────────────────────────────────────────────────
info "Checking Docker..."
if ! command -v docker &>/dev/null; then
    error "Docker is not installed. Install it first:"
    error "  sudo pacman -S docker"
    error "  sudo systemctl enable --now docker"
    exit 1
fi

if ! docker info &>/dev/null; then
    error "Docker daemon is not running. Start it:"
    error "  sudo systemctl start docker"
    exit 1
fi
success "Docker is running."

# ── Stop any existing stack ──────────────────────────────────────────────────
docker compose down --remove-orphans 2>/dev/null || true

# ── Start Docker stack (Redis + API Gateway) ─────────────────────────────────
info "Starting Redis + API Gateway (Docker)..."
docker compose up -d --build redis api

# ── Wait for API to be healthy ───────────────────────────────────────────────
info "Waiting for API to start (http://localhost:${API_PORT})..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT}/api/v1/health" &>/dev/null; then
        HEALTH=$(curl -sf "http://localhost:${API_PORT}/api/v1/health" 2>/dev/null)
        success "API is up: ${HEALTH}"
        break
    fi
    if [[ $i -eq 30 ]]; then
        error "API did not start within 30 seconds. Check logs:"
        docker compose logs api
        exit 1
    fi
    sleep 1
done

# ── Print dashboard URL ─────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║                                                  ║${NC}"
echo -e "  ${GREEN}║   ⚡ Younify is running!                        ║${NC}"
echo -e "  ${GREEN}║                                                  ║${NC}"
echo -e "  ${GREEN}║   Dashboard:  http://localhost:${API_PORT}             ║${NC}"
echo -e "  ${GREEN}║   API:        http://localhost:${API_PORT}/api/v1     ║${NC}"
echo -e "  ${GREEN}║   Redis:      localhost:${REDIS_PORT}                     ║${NC}"
echo -e "  ${GREEN}║                                                  ║${NC}"
echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── Start cluster coordinator ────────────────────────────────────────────────
if [[ "$CLUSTER_MODE" == true ]] || [[ "$COORDINATOR_ONLY" == true ]]; then
    PYTHON=""
    if [[ -f ".venv/bin/python3" ]]; then
        PYTHON=".venv/bin/python3"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
    fi

    if [[ -n "$PYTHON" ]]; then
        info "Starting Cluster Coordinator..."
        $PYTHON -m uvicorn coordinator.coordinator:coordinator_app \
            --host 0.0.0.0 --port 8050 &
        COORD_PID=$!
        info "Coordinator started (PID: $COORD_PID)"
        WORKER_PIDS="${WORKER_PIDS} $COORD_PID"
    fi
fi

# ── Start cluster worker sidecar ─────────────────────────────────────────────
if [[ "$CLUSTER_MODE" == true ]]; then
    if [[ -n "$PYTHON" ]]; then
        info "Starting Cluster Worker sidecar..."
        $PYTHON worker/cluster_worker.py \
            --coordinator "${COORDINATOR_URL:-http://localhost:8050}" &
        CLUSTER_PID=$!
        info "Cluster worker started (PID: $CLUSTER_PID)"
        WORKER_PIDS="${WORKER_PIDS} $CLUSTER_PID"
    fi
fi

# ── Start local workers ──────────────────────────────────────────────────────
if [[ "$HEAD_ONLY" == true ]] || [[ "$COORDINATOR_ONLY" == true ]]; then
    if [[ "$HEAD_ONLY" == true ]]; then
        info "Head-only mode — skipping local workers."
    else
        info "Coordinator-only mode — skipping local workers."
    fi
    info "To add workers, run on other machines:"
    info "  REDIS_HOST=$(hostname -I | awk '{print $1}') bash run-worker.sh"
else
    # Check Python deps
    PYTHON=""
    if [[ -f ".venv/bin/python3" ]]; then
        PYTHON=".venv/bin/python3"
    elif command -v python3 &>/dev/null; then
        PYTHON="python3"
        warn "No virtual environment found. Using system Python."
    else
        error "Python 3 not found. Install it first."
        exit 1
    fi

    # Install deps if needed
    if ! $PYTHON -c "import redis, requests" &>/dev/null 2>&1; then
        info "Installing Python dependencies (redis, requests)..."
        $PYTHON -m pip install redis requests 2>/dev/null || pip3 install redis requests
    fi

    success "Dependencies OK."

    # Check Ollama
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
    if curl -sf "${OLLAMA_URL}/api/tags" &>/dev/null; then
        MODELS=$(curl -sf "${OLLAMA_URL}/api/tags" | python3 -c "
import sys,json
models=json.load(sys.stdin).get('models',[])
print(len(models))
" 2>/dev/null || echo "?")
        success "Ollama is running (${MODELS} model(s) available)."
    else
        warn "Ollama not reachable at ${OLLAMA_URL}."
        warn "Workers using Ollama will fail. Install:"
        warn "  curl -fsSL https://ollama.com/install.sh | sh"
        warn "  ollama pull llama3"
    fi

    # Start workers
    info "Starting ${NUM_WORKERS} local worker(s)..."
    WORKER_PIDS=""
    for i in $(seq 1 "$NUM_WORKERS"); do
        REDIS_HOST=localhost OLLAMA_BASE_URL="$OLLAMA_URL" \
            $PYTHON worker/worker.py &
        WORKER_PIDS="${WORKER_PIDS} $!"
    done
    success "${NUM_WORKERS} worker(s) started (PIDs: ${WORKER_PIDS})."
fi

# ── Wait ─────────────────────────────────────────────────────────────────────
echo ""
info "Press Ctrl+C to stop everything."
echo ""

# Keep the script running and wait for Ctrl+C (handled by trap)
while true; do
    sleep 1
done
