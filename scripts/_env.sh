# sourced by the other scripts: loads config/models.env and sets paths
LAB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set -a
# shellcheck disable=SC1091
. "$LAB/config/models.env"
set +a
VENDOR="$LAB/vendor"
COMFY="$VENDOR/ComfyUI"
