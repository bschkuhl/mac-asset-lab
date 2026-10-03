#!/usr/bin/env bash
# Download model files into vendor/ComfyUI/models. Resumable. Usage:
#   scripts/download_models.sh klein9b [--dry-run]
#   scripts/download_models.sh dev [--dry-run]     (also fetches the turbo LoRA)
set -euo pipefail
. "$(dirname "$0")/_env.sh"
engine="${1:-klein9b}"; dry="${2:-}"
M="$COMFY/models"

get() {  # repo file target_dir
  local repo="$1" file="$2" dir="$M/$3" base; base="$(basename "$file")"
  mkdir -p "$dir"
  if [ -f "$dir/$base" ]; then echo "have   $3/$base"; return; fi
  echo "fetch  $3/$base   (from $repo)"
  [ "$dry" = "--dry-run" ] && return
  hf download "$repo" "$file" --local-dir "$M/_dl"
  mv "$M/_dl/$file" "$dir/$base"
}

case "$engine" in
  klein9b)
    get "$KLEIN_UNET_REPO" "$KLEIN_UNET_FILE" diffusion_models
    get "$KLEIN_CLIP_REPO" "$KLEIN_CLIP_FILE" text_encoders
    get "$VAE_REPO" "$VAE_FILE" vae ;;
  dev)
    get "$DEV_UNET_REPO" "$DEV_UNET_FILE" diffusion_models
    get "$DEV_CLIP_REPO" "$DEV_CLIP_FILE" text_encoders
    get "$TURBO_LORA_REPO" "$TURBO_LORA_FILE" loras
    get "$VAE_REPO" "$VAE_FILE" vae ;;
  *) echo "unknown engine: $engine (klein9b | dev)"; exit 1 ;;
esac
[ -d "$M/_dl" ] && rm -rf "$M/_dl"
echo "ok"
