#!/usr/bin/env bash
# TRELLIS.2 for Apple Silicon (community port, MPS). Needs: HuggingFace login + accepted licenses for
#   https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m
#   https://huggingface.co/briaai/RMBG-2.0
# Also installs the Xcode Metal Toolchain (about 700 MB) for the faster Metal backends (skip with SKIP_METAL=1).
set -euo pipefail
. "$(dirname "$0")/_env.sh"
mkdir -p "$VENDOR"
T="$VENDOR/trellis-mac"
if [ ! -d "$T/.git" ]; then git clone "$TRELLIS_MAC_REPO" "$T"; fi
git -C "$T" fetch --quiet origin
git -C "$T" checkout --quiet -- generate.py 2>/dev/null || true  # drop our patch below before switching refs
git -C "$T" checkout --quiet "$TRELLIS_MAC_REF"
# Let pipeline.py set the triangle target (TRELLIS_FACES, default 200000 as upstream); the texture is baked on that mesh.
sed -i '' 's/target_faces = min(200000, /target_faces = min(int(os.environ.get("TRELLIS_FACES", 200000)), /' "$T/generate.py"
grep -q TRELLIS_FACES "$T/generate.py" && python3 -m py_compile "$T/generate.py" \
  || { echo "generate.py changed upstream: TRELLIS_FACES patch failed"; exit 1; }

have_metal=0
if [ "${SKIP_METAL:-0}" != "1" ]; then
  xcrun -sdk macosx metal --version >/dev/null 2>&1 || xcodebuild -downloadComponent MetalToolchain \
    || echo "WARN: Metal Toolchain not installed; TRELLIS uses the slower fallbacks"
  xcrun -sdk macosx metal --version >/dev/null 2>&1 && have_metal=1
fi
(cd "$T" && bash setup.sh)

# Fixes for the Metal backends (setup.sh only warns when they fail and falls back to slower code):
# current PyTorch headers need C++20 (the packages ask for C++17), and o-voxel needs its Eigen submodule.
# Package and module names below match the pinned TRELLIS_MAC_REF. REBUILD=1 forces a rebuild.
PY="$T/.venv/bin/python"
check_metal() { "$PY" -c "import mtlbvh, mtldiffrast, cumesh, flex_gemm, o_voxel" 2>/dev/null; }
if [ "$have_metal" = 1 ] && { [ "${REBUILD:-0}" = 1 ] || ! check_metal; }; then
  D="$T/deps"
  git -C "$D/trellis2-apple" submodule update --init --depth 1 o-voxel/third_party/eigen \
    || echo "WARN: Eigen submodule missing; o-voxel will not build"
  uv pip install --python "$PY" setuptools wheel pybind11
  for p in "$D/mtlbvh" "$D/mtldiffrast" "$D/mtlmesh" "$D/mtlgemm" "$D/trellis2-apple/o-voxel"; do
    [ -f "$p/setup.py" ] || { echo "WARN: $p missing"; continue; }
    sed -i '' 's/-std=c++17/-std=c++20/g' "$p/setup.py"
    MACOSX_DEPLOYMENT_TARGET=12.0 uv pip install --python "$PY" --no-build-isolation "$p" \
      || echo "WARN: $(basename "$p") still fails to build"
  done
fi
if [ "$have_metal" = 1 ]; then
  check_metal && echo "Metal backends ok" || echo "WARN: some Metal backends missing; TRELLIS still runs with the slower fallbacks"
fi
echo "TRELLIS.2 ready: $T (weights download on the first run, about 15 GB)"
