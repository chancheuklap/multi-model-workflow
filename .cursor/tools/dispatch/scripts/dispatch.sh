#!/usr/bin/env bash
# Cloud edition: native agents communicate; this entry only supplies mechanical tools.
set -euo pipefail
scripts="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
  status|land) command="$1"; shift; exec python3 "$scripts/$command.py" "$@" ;;
  board) shift; exec python3 "$scripts/../../../board/server.py" "$@" ;;
  *) echo 'usage: dispatch.sh status N --into NIGHT [--ticket] | land PR --into NIGHT --head SHA | board [--port PORT]' >&2; exit 2 ;;
esac
