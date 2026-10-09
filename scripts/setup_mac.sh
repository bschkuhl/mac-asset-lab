#!/usr/bin/env bash
# One-time setup on an Apple Silicon Mac: ComfyUI (pinned) + GGUF node + Python env. Safe to re-run.
# Usage: scripts/setup_mac.sh            (ComfyUI only)
#        scripts/setup_mac.sh --trellis  (also TRELLIS.2 for Apple Silicon, needs a HuggingFace login)
set -euo pipefail
. "$(dirname "$0")/_env.sh"

[ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ] || { echo "This script is for Apple Silicon macOS."; exit 1; }
command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
for t in uv git; do command -v "$t" >/dev/null || brew install "$t"; done
command -v hf >/dev/null || uv tool install "huggingface_hub[cli]"

mkdir -p "$VENDOR"
if [ ! -d "$COMFY/.git" ]; then git clone "$COMFYUI_REPO" "$COMFY"; fi
git -C "$COMFY" fetch --quiet origin
git -C "$COMFY" checkout --quiet "$COMFYUI_REF"

if [ ! -x "$COMFY/.venv/bin/python" ]; then
  (cd "$COMFY" && uv venv --managed-python -p "$PYTHON_VERSION" .venv)
fi
PY="$COMFY/.venv/bin/python"
# default PyPI wheels for macOS arm64 include MPS
uv pip install --python "$PY" torch torchvision torchaudio
uv pip install --python "$PY" -r "$COMFY/requirements.txt"

NODES="$COMFY/custom_nodes"
if [ ! -d "$NODES/ComfyUI-GGUF/.git" ]; then git clone "$GGUF_NODE_REPO" "$NODES/ComfyUI-GGUF"; fi
git -C "$NODES/ComfyUI-GGUF" fetch --quiet origin
git -C "$NODES/ComfyUI-GGUF" checkout --quiet "$GGUF_NODE_REF"
uv pip install --python "$PY" -r "$NODES/ComfyUI-GGUF/requirements.txt"

if [ "${1:-}" = "--trellis" ]; then "$LAB/scripts/setup_trellis.sh"; fi

cat <<MSG

Done. Next:
  hf auth login                      (once; some model repos need accepted licenses)
  scripts/download_models.sh klein9b (about 27 GB; 'dev' = about 60 GB, see docs/PIPELINES.md)
  scripts/comfy_up.sh                (start ComfyUI in the background)
  ./pipeline.py doctor               (check everything)
Tip for big models: macOS lets the GPU use about 75 % of RAM. To allow about 56 GB until the next reboot:
  sudo sysctl iogpu.wired_limit_mb=57344
MSG
