#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "$0")/_env.sh"
f="$LAB/vendor/comfy.pid"
[ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null && rm -f "$f" && echo "stopped" || echo "not running (no pid file)"
