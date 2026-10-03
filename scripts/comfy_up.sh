#!/usr/bin/env bash
# Start ComfyUI in the background (127.0.0.1 only). Log: vendor/ComfyUI/server.log. Stop: scripts/comfy_down.sh
set -euo pipefail
. "$(dirname "$0")/_env.sh"
if curl -s -m 2 "$COMFYUI_URL/system_stats" >/dev/null 2>&1; then echo "already running at $COMFYUI_URL"; exit 0; fi
cd "$COMFY"
export PYTORCH_ENABLE_MPS_FALLBACK=1
nohup .venv/bin/python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch ${COMFY_ARGS:-} > server.log 2>&1 &
echo $! > "$LAB/vendor/comfy.pid"
for _ in $(seq 1 60); do
  curl -s -m 2 "$COMFYUI_URL/system_stats" >/dev/null 2>&1 && { echo "up (pid $(cat "$LAB/vendor/comfy.pid"))"; exit 0; }
  sleep 1
done
echo "did not start; see $COMFY/server.log"; exit 1
