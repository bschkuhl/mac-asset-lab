#!/usr/bin/env bash
# Copy results of one character into the Monkey on an Island repo (concepts, views, raw GLB).
# Usage: scripts/export_to_game.sh <name> <path-to-monkey-on-an-island>
set -euo pipefail
. "$(dirname "$0")/_env.sh"
name="${1:?name}"; game="${2:?path to game repo}"
src="$LAB/out/$name"
[ -d "$src" ] || { echo "no results: $src"; exit 1; }
mkdir -p "$game/assets/concepts/$name" "$game/assets/glb"
rsync -a --exclude 'model/' --exclude 'blender/' --exclude 'preview/' "$src/" "$game/assets/concepts/$name/"
# the low-poly export if there is one, else the newest generated model
glb="$(ls "$src/model/${name}_lowpoly.glb" 2>/dev/null || ls -t "$src"/model/*.glb 2>/dev/null | head -1 || true)"
if [ -n "$glb" ]; then
  # the game repo's model_pipeline.py expects this name, whichever 3D engine made the model
  cp "$glb" "$game/assets/glb/${name}_trellis_download.glb"
  echo "next, in the game repo:"
  echo "  python3 assets/scripts/model_pipeline.py import $name assets/glb/${name}_trellis_download.glb --tag trellis"
  echo "  python3 assets/scripts/model_pipeline.py lod $name"
fi
