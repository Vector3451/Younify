#!/usr/bin/env bash
# =============================================================================
# start.sh — Younify All-in-One Launcher
# =========================================
# Single entry point for everything: head node, worker node, Tailscale setup.
#
# Usage (HEAD NODE):
#   bash start.sh                    # Full stack: Redis + API + workers
#   bash start.sh --head-only        # Redis + API only (no local workers)
#   bash start.sh --cluster          # Full stack + coordinator + llama-server
#   bash start.sh --tailscale        # Install Tailscale and print connection info
#   bash start.sh --workers 3        # Start with N local workers
#
# Usage (WORKER NODE):
#   bash start.sh --worker <head-tailscale-ip>
#     Connects this machine to the head node's cluster via Tailscale.
#     Example: bash start.sh --worker 100.100.100.100
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NUM_WORKERS="${NUM_WORKERS:-1}"
HEAD_ONLY=false
CLUSTER_MODE=false
WORKER_MODE=false
WORKER_HEAD_IP=""
TAILSCALE_MODE=false
API_PORT=3000
REDIS_PORT=6379

# ── Parse args ───────────────────────────────────────────────────────────────
MODE="head"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --worker)      WORKER_MODE=true; MODE="worker"; WORKER_HEAD_IP="${2:-}"; shift 2 ;;
        --head-only)   HEAD_ONLY=true; shift ;;
        --cluster)     CLUSTER_MODE=true; shift ;;
        --tailscale)   TAILSCALE_MODE=true; shift ;;
        --workers|-w)  NUM_WORKERS="$2"; shift 2 ;;
        --port|-p)     API_PORT="$2"; shift 2 ;;
        --redis-port)  REDIS_PORT="$2"; shift 2 ;;
        -h|--help)
            sed -n '3,17p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

cd "$SCRIPT_DIR"

# ── Helpers ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }

get_python() {
    if [[ -f ".venv/bin/python3" ]]; then echo ".venv/bin/python3"
    elif command -v python3 &>/dev/null; then echo "python3"
    else echo ""; fi
}

cleanup() {
    echo ""; info "Shutting down..."
    if [[ -n "${WORKER_PIDS:-}" ]]; then
        for pid in $WORKER_PIDS; do kill "$pid" 2>/dev/null || true; done
        info "Processes stopped."
    fi
    if [[ "$MODE" == "head" ]]; then
        docker compose down --remove-orphans 2>/dev/null || true
        info "Docker stack stopped."
    fi
    success "Younify stopped. Goodbye!"; exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# =============================================================================
# WORKER MODE: connect to a head node via Tailscale
# =============================================================================
if [[ "$MODE" == "worker" ]]; then
    if [[ -z "$WORKER_HEAD_IP" ]]; then
        error "Usage: bash start.sh --worker <head-tailscale-ip>"
        exit 1
    fi

    echo ""; echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "  ${GREEN}║   Connecting to Younify Cluster via Tailscale   ║${NC}"
    echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"; echo ""

    # 1. Install Tailscale if needed
    if ! command -v tailscale &>/dev/null; then
        info "Installing Tailscale..."
        curl -fsSL https://tailscale.com/install.sh | sh
        success "Tailscale installed."
    fi

    # 2. Connect to Tailscale
    TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -z "$TS_IP" ]]; then
        info "Starting Tailscale (authenticate in your browser)..."
        sudo tailscale up
        TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
        if [[ -z "$TS_IP" ]]; then
            error "Tailscale connection failed. Run 'sudo tailscale up' manually."; exit 1
        fi
        success "Tailscale connected. IP: ${TS_IP}"
    else
        success "Tailscale already connected. IP: ${TS_IP}"
    fi

    # 3. Verify head node reachable
    info "Checking head node (${WORKER_HEAD_IP}:8050)..."
    if ! curl -sf "http://${WORKER_HEAD_IP}:8050/api/v1/health" &>/dev/null; then
        warn "Coordinator not reachable at ${WORKER_HEAD_IP}:8050"
        warn "Make sure the head node is running start.sh with --cluster"
    else
        success "Head node coordinator is reachable."
    fi

    # 4. Install Python deps
    PY=$(get_python)
    if [[ -z "$PY" ]]; then error "Python3 not found."; exit 1; fi
    info "Installing Python dependencies..."
    $PY -m pip install --quiet redis requests 2>/dev/null || true

    # 5. Build llama-rpc-server if not found
    if ! command -v llama-rpc-server &>/dev/null && [[ ! -f "./llama-rpc-server" ]]; then
        warn "llama-rpc-server not found. Building from llama.cpp..."
        if [[ ! -d "llama.cpp" ]]; then
            git clone --depth 1 https://github.com/ggerganov/llama.cpp 2>/dev/null || true
        fi
        if [[ -d "llama.cpp" ]]; then
            cd llama.cpp && cmake -B build -DLLAMA_RPC=ON 2>/dev/null && cmake --build build --config Release -j 2>/dev/null && cd ..
            cp llama.cpp/build/bin/llama-rpc-server ./ 2>/dev/null || true
        fi
    fi

    # 6. Start cluster worker
    info "Starting cluster worker -> ${WORKER_HEAD_IP}:8050"
    echo ""; echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"
    echo -e "  ${GREEN}  Worker connected to cluster at ${WORKER_HEAD_IP}${NC}"
    echo -e "  ${GREEN}  Press Ctrl+C to disconnect.${NC}"
    echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"; echo ""
    COORDINATOR_URL="http://${WORKER_HEAD_IP}:8050" \
        $PY worker/cluster_worker.py --coordinator "http://${WORKER_HEAD_IP}:8050"
    exit $?
fi

# =============================================================================
# TAILSCALE MODE: just set up Tailscale on head node
# =============================================================================
if [[ "$TAILSCALE_MODE" == true ]]; then
    echo ""; echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "  ${GREEN}║      Younify Tailscale Cluster Setup            ║${NC}"
    echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"; echo ""

    if ! command -v tailscale &>/dev/null; then
        info "Installing Tailscale..."
        curl -fsSL https://tailscale.com/install.sh | sh
        success "Tailscale installed."
    fi

    TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -z "$TS_IP" ]]; then
        info "Starting Tailscale (authenticate in your browser)..."
        sudo tailscale up
        TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
        if [[ -z "$TS_IP" ]]; then
            error "Tailscale connection failed."; exit 1
        fi
        success "Tailscale connected. IP: ${TS_IP}"
    else
        success "Tailscale already connected. IP: ${TS_IP}"
    fi

    echo "$TS_IP" > .tailscale-head-ip 2>/dev/null || true
    echo ""; echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"
    echo -e "  ${GREEN}  Head node Tailscale IP: ${TS_IP}${NC}"
    echo -e "  ${GREEN}════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  To connect a worker machine:"
    echo "    bash start.sh --worker ${TS_IP}"
    echo ""
    exit 0
fi

# =============================================================================
# HEAD NODE MODE: full stack
# =============================================================================
echo ""; echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║   Starting Younify Head Node                      ║${NC}"
echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"; echo ""

# ── Check Docker ─────────────────────────────────────────────────────────────
info "Checking Docker..."
if ! command -v docker &>/dev/null; then
    error "Docker not installed."; exit 1
fi
if ! docker info &>/dev/null; then
    error "Docker daemon not running."; exit 1
fi
success "Docker is running."

# ── Ensure Tailscale is connected (if --cluster) ────────────────────────────
if [[ "$CLUSTER_MODE" == true ]]; then
    TS_IP=$(tailscale ip -4 2>/dev/null || echo "")
    if [[ -z "$TS_IP" ]]; then
        warn "Tailscale not connected. Run 'bash start.sh --tailscale' first,"
        warn "or start Tailscale manually: sudo tailscale up"
        warn "Continuing without Tailscale (workers must connect via LAN IP)."
    else
        success "Tailscale connected. IP: ${TS_IP}"
        echo "$TS_IP" > .tailscale-head-ip 2>/dev/null || true
    fi
fi

# ── Start Docker stack ───────────────────────────────────────────────────────
info "Starting Docker stack (Redis + API Gateway)..."
docker compose up -d --build redis api

# ── Wait for API ─────────────────────────────────────────────────────────────
info "Waiting for API (http://localhost:${API_PORT})..."
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT}/api/v1/health" &>/dev/null; then
        HEALTH=$(curl -sf "http://localhost:${API_PORT}/api/v1/health" 2>/dev/null)
        success "API is up: ${HEALTH}"; break
    fi
    if [[ $i -eq 30 ]]; then error "API didn't start."; docker compose logs api; exit 1; fi
    sleep 1
done

# ── Print dashboard URL ─────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "  ${GREEN}║   Younify is running!                        ║${NC}"
echo -e "  ${GREEN}║                                              ║${NC}"
echo -e "  ${GREEN}║   Dashboard:  http://localhost:${API_PORT}         ║${NC}"
echo -e "  ${GREEN}║   API:        http://localhost:${API_PORT}/api/v1 ║${NC}"
echo -e "  ${GREEN}║                                              ║${NC}"

if [[ "$CLUSTER_MODE" == true ]] && [[ -n "${TS_IP:-}" ]]; then
    echo -e "  ${GREEN}║   Tailscale:  ${TS_IP}                         ║${NC}"
    echo -e "  ${GREEN}║   Workers:    bash start.sh --worker ${TS_IP}   ║${NC}"
fi

echo -e "  ${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── Start coordinator (if --cluster) ────────────────────────────────────────
PY=$(get_python)
WORKER_PIDS=""

if [[ "$CLUSTER_MODE" == true ]]; then
    if [[ -z "$PY" ]]; then error "Python3 not found."; exit 1; fi

    # Install deps for coordinator
    $PY -m pip install --quiet fastapi uvicorn pydantic redis requests 2>/dev/null || true

    info "Starting Coordinator..."
    $PY -m uvicorn coordinator.coordinator:coordinator_app --host 0.0.0.0 --port 8050 &
    COORD_PID=$!; WORKER_PIDS="$WORKER_PIDS $COORD_PID"
    success "Coordinator started (PID: $COORD_PID)"

    # Start llama-server if model path provided
    if [[ -n "${MODEL_PATH:-}" ]]; then
        info "Starting llama-server with RPC workers..."
        bash cluster-llama-entrypoint.sh \
            --model "$MODEL_PATH" \
            --coordinator "http://localhost:8050" &
        LLAMA_PID=$!; WORKER_PIDS="$WORKER_PIDS $LLAMA_PID"
        success "llama-server started (PID: $LLAMA_PID)"
    else
        info "To start llama-server with all workers:"
        info "  MODEL_PATH=/path/to/model.gguf bash cluster-llama-entrypoint.sh"
    fi
fi

# ── Start local Younify workers ─────────────────────────────────────────────
if [[ "$HEAD_ONLY" != true ]] && [[ -n "$PY" ]]; then
    # Install deps
    $PY -m pip install --quiet redis requests 2>/dev/null || true

    # Check Ollama
    OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
    if curl -sf "${OLLAMA_URL}/api/tags" &>/dev/null; then
        MODELS=$(curl -sf "${OLLAMA_URL}/api/tags" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo "?")
        success "Ollama is running (${MODELS} model(s) available)."
    else
        warn "Ollama not reachable. Install: curl -fsSL https://ollama.com/install.sh | sh"
    fi

    info "Starting ${NUM_WORKERS} local worker(s)..."
    for i in $(seq 1 "$NUM_WORKERS"); do
        REDIS_HOST=localhost OLLAMA_BASE_URL="$OLLAMA_URL" $PY worker/worker.py &
        WORKER_PIDS="${WORKER_PIDS} $!"
    done
    success "${NUM_WORKERS} worker(s) started."
fi

# ── Wait ─────────────────────────────────────────────────────────────────────
echo ""; info "Press Ctrl+C to stop everything."; echo ""
while true; do sleep 1; done
