#!/usr/bin/env bash
# cluster-llama-entrypoint.sh — Start llama-server with auto-offload
# ================================================================
# Fetches RPC worker addresses AND a layer-distribution plan from
# the coordinator, then starts llama-server with GPU layers sized
# to fit available VRAM.  Excess layers spill automatically to
# system RAM on the head node.
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
#   N_GPU_LAYERS      (default: auto — computed from worker VRAM)
#   CTX_SIZE          (default: 4096)
#   MODEL_TOTAL_LAYERS(default: 80 — used for layer-plan when auto)
#   MODEL_SIZE_GB     (default: 8.0 — used for layer-plan when auto)

set -euo pipefail

COORDINATOR_URL="${COORDINATOR_URL:-http://localhost:8050}"
LLAMA_SERVER="${LLAMA_SERVER_BIN:-llama-server}"
MODEL_PATH="${MODEL_PATH:-}"
PORT="${LLAMA_SERVER_PORT:-8080}"
N_GPU_LAYERS="${N_GPU_LAYERS:-auto}"
CTX_SIZE="${CTX_SIZE:-4096}"
MODEL_TOTAL_LAYERS="${MODEL_TOTAL_LAYERS:-80}"
MODEL_SIZE_GB="${MODEL_SIZE_GB:-8.0}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)          MODEL_PATH="$2"; shift 2 ;;
        --coordinator)    COORDINATOR_URL="$2"; shift 2 ;;
        --port)           PORT="$2"; shift 2 ;;
        --ngl)            N_GPU_LAYERS="$2"; shift 2 ;;
        --ctx-size)       CTX_SIZE="$2"; shift 2 ;;
        --total-layers)   MODEL_TOTAL_LAYERS="$2"; shift 2 ;;
        --model-size-gb)  MODEL_SIZE_GB="$2"; shift 2 ;;
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

# ── Try to auto-detect model metadata from the GGUF file ──────────────
if [[ -f "$MODEL_PATH" ]]; then
    MODEL_FILE_SIZE_BYTES=$(stat -c%s "$MODEL_PATH" 2>/dev/null || echo 0)
    COMPUTED_MODEL_SIZE_GB=$(echo "scale=2; $MODEL_FILE_SIZE_BYTES / 1073741824" | bc -l 2>/dev/null || echo "$MODEL_SIZE_GB")
    if [[ "$COMPUTED_MODEL_SIZE_GB" != "$MODEL_SIZE_GB" ]] && (( $(echo "$COMPUTED_MODEL_SIZE_GB > 0" | bc -l) )); then
        MODEL_SIZE_GB="$COMPUTED_MODEL_SIZE_GB"
        echo "Detected model size: ${MODEL_SIZE_GB} GB"
    fi
fi

# ── Fetch layer plan from coordinator ─────────────────────────────────
if [[ "$N_GPU_LAYERS" == "auto" ]]; then
    echo "Querying coordinator for optimal layer distribution..."
    PLAN_JSON=$(curl -sf \
        "$COORDINATOR_URL/api/v1/cluster/layer-plan?total_layers=${MODEL_TOTAL_LAYERS}&model_size_gb=${MODEL_SIZE_GB}" \
        2>/dev/null || echo "")

    if [[ -n "$PLAN_JSON" ]]; then
        N_GPU_LAYERS=$(echo "$PLAN_JSON" | python3 -c "
import sys, json
plan = json.load(sys.stdin)
print(plan.get('suggested_n_gpu_layers', 0))
" 2>/dev/null || echo "0")

        echo "Layer plan received:"
        echo "$PLAN_JSON" | python3 -m json.tool 2>/dev/null || echo "$PLAN_JSON"
    else
        echo "WARNING: Coordinator unreachable — defaulting to 0 GPU layers (CPU only)."
        N_GPU_LAYERS=0
    fi
fi

echo "GPU layers:  $N_GPU_LAYERS"
echo ""

# ── Fetch RPC addresses ──────────────────────────────────────────────
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

# ── Build command ────────────────────────────────────────────────────
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
