#!/usr/bin/env bash
# cluster-llama-entrypoint.sh — Start llama-server with RPC workers
# ================================================================
# Fetches RPC worker addresses from the coordinator, then starts
# llama-server bound to all of them.
#
# Usage:
#   bash cluster-llama-entrypoint.sh \
#     --model /path/to/model.gguf \
#     --coordinator http://localhost:8050 \
#     --port 8080
#
# Environment variables:
#   COORDINATOR_URL   (default: http://localhost:8050)
#   LLAMA_SERVER_BIN  (default: llama-server)
#   MODEL_PATH        (path to GGUF model file)
#   LLAMA_SERVER_PORT (default: 8080)
#   N_GPU_LAYERS      (default: 99, offload all layers)
#   CTX_SIZE          (default: 4096)

set -euo pipefail

COORDINATOR_URL="${COORDINATOR_URL:-http://localhost:8050}"
LLAMA_SERVER="${LLAMA_SERVER_BIN:-llama-server}"
MODEL_PATH="${MODEL_PATH:-}"
PORT="${LLAMA_SERVER_PORT:-8080}"
N_GPU_LAYERS="${N_GPU_LAYERS:-99}"
CTX_SIZE="${CTX_SIZE:-4096}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)       MODEL_PATH="$2"; shift 2 ;;
        --coordinator) COORDINATOR_URL="$2"; shift 2 ;;
        --port)        PORT="$2"; shift 2 ;;
        --ngl)         N_GPU_LAYERS="$2"; shift 2 ;;
        --ctx-size)    CTX_SIZE="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

if [[ -z "$MODEL_PATH" ]]; then
    echo "Error: --model or MODEL_PATH is required"
    exit 1
fi

echo "=== Cluster LLM Entrypoint ==="
echo "Model:       $MODEL_PATH"
echo "Coordinator: $COORDINATOR_URL"
echo "Port:        $PORT"
echo ""

RPC_ADDRS=$(curl -sf "$COORDINATOR_URL/api/v1/cluster/rpc-addrs" | python3 -c "
import sys, json
data = json.load(sys.stdin)
addrs = data.get('addresses', [])
for a in addrs:
    print(f'--rpc {a}')
" 2>/dev/null || echo "")

if [[ -z "$RPC_ADDRS" ]]; then
    echo "WARNING: No RPC workers found from coordinator."
    echo "Starting llama-server in standalone mode."
else
    echo "RPC workers:"
    echo "$RPC_ADDRS"
fi

CMD=("$LLAMA_SERVER")
CMD+=("--model" "$MODEL_PATH")
CMD+=("--host" "0.0.0.0")
CMD+=("--port" "$PORT")
CMD+=("--n-gpu-layers" "$N_GPU_LAYERS")
CMD+=("--ctx-size" "$CTX_SIZE")

if [[ -n "$RPC_ADDRS" ]]; then
    while IFS= read -r rpc_arg; do
        if [[ -n "$rpc_arg" ]]; then
            CMD+=("$rpc_arg")
        fi
    done <<< "$RPC_ADDRS"
fi

echo ""
echo "Starting: ${CMD[*]}"
echo ""

exec "${CMD[@]}"
