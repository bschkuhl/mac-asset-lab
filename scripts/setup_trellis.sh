#!/usr/bin/env bash
# TRELLIS.2 for Apple Silicon (community port, MPS). Needs: HuggingFace login + accepted licenses for
#   https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m
#   https://huggingface.co/briaai/RMBG-2.0
# Optional faster texture baking: xcodebuild -downloadComponent MetalToolchain   (skip with SKIP_METAL=1)
set -euo pipefail
. "$(dirname "$0")/_env.sh"
mkdir -p "$VENDOR"
T="$VENDOR/trellis-mac"
if [ ! -d "$T/.git" ]; then git clone "$TRELLIS_MAC_REPO" "$T"; fi
git -C "$T" fetch --quiet origin
git -C "$T" checkout --quiet "$TRELLIS_MAC_REF"
(cd "$T" && bash setup.sh)
echo "TRELLIS.2 ready: $T (weights download on the first run, about 15 GB)"
