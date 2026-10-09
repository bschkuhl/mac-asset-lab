#!/usr/bin/env bash
# Pixal3D for Apple Silicon (community port, MPS): the default 3D engine. Weights (TencentARC/Pixal3D, MIT) and the
# MoGe-2 camera model download on the first run; DINOv3 and RMBG-2.0 need the same HuggingFace licenses as TRELLIS.
# Needs Python 3.10 and the Xcode Metal Toolchain (both installed here if missing). Re-runs skip the install when the
# native packages already import; REBUILD=1 forces it. Uses pip, because the port's own setup_mac.sh does.
set -euo pipefail
. "$(dirname "$0")/_env.sh"
mkdir -p "$VENDOR"
T="$VENDOR/pixal3d-mac"
if [ ! -d "$T/.git" ]; then git clone "$PIXAL3D_REPO" "$T"; fi
git -C "$T" fetch --quiet origin
git -C "$T" checkout --quiet "$PIXAL3D_REF"

PY="$T/.venv/bin/python"
if [ "${REBUILD:-0}" != 1 ] && [ -x "$PY" ] \
   && "$PY" -c "import torch, cumesh, flex_gemm, mtlbvh, mtldiffrast, o_voxel, natten_mps" 2>/dev/null; then
  echo "Pixal3D ready: $T (already installed; REBUILD=1 to reinstall)"
  exit 0
fi

PY3="$(command -v python3.10 || echo /opt/homebrew/opt/python@3.10/bin/python3.10)"
[ -x "$PY3" ] || brew install python@3.10 || { echo "Python 3.10 is required: brew install python@3.10"; exit 1; }
xcrun -sdk macosx metal --version >/dev/null 2>&1 || xcodebuild -downloadComponent MetalToolchain \
  || { echo "The Metal Toolchain is required: xcodebuild -downloadComponent MetalToolchain"; exit 1; }

# requirements-mac.txt pins natten, whose build needs torch, but pip builds it in isolation: put torch in first
pin() { grep -E "^$1==" "$T/requirements-mac.txt" || { echo "requirements-mac.txt has no $1 pin; update this script"; exit 1; }; }
torch="$(pin torch)"; vision="$(pin torchvision)"; natten="$(pin natten)"
[ -x "$PY" ] || "$PY3" -m venv "$T/.venv"
"$T/.venv/bin/pip" install -q "$torch" "$vision" setuptools wheel
MACOSX_DEPLOYMENT_TARGET=12.0 "$T/.venv/bin/pip" install -q "$natten" --no-build-isolation
(cd "$T" && MACOSX_DEPLOYMENT_TARGET=12.0 bash scripts/setup_mac.sh)
echo "Pixal3D ready: $T"
