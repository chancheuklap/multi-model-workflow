#!/usr/bin/env bash
# MMW_RUNNER: {"catalog":"codex-app","launch":"codex-app","executor":"codex-app-tools.js"}
# Codex App adapter. Native control is confined to codex-app-tools.js; detached
# messages use the public queue and host hooks supply process-backed observations.
# start/send/state/liveness/stop/self keep the shared runner interface.

set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "${1:-}" in
  attach) exit 0 ;;
  open-url) exit 3 ;;
esac
exec python3 "$HERE/codex_app.py" "$@"
