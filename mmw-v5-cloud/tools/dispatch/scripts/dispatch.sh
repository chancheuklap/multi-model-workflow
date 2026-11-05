#!/usr/bin/env bash
# Cloud edition: native agents communicate; this entry only supplies mechanical tools.
set -euo pipefail
scripts="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
  status|land) command="$1"; shift; exec python3 "$scripts/$command.py" "$@" ;;
  open|show|row|spawn) command="$1"; shift; exec python3 "$scripts/models.py" "$command" "$@" ;;
  board) shift; exec python3 "$scripts/../../../board/server.py" "$@" ;;
  *) echo 'usage: dispatch.sh open --project NAME (--spec N | --ticket N) | show | row ROLE [--at COMMIT] | spawn worker --ticket N | spawn verifier | spawn review | spawn researcher --question FILE | status [N --into NIGHT [--ticket]] | land PR | board [--port PORT]' >&2; exit 2 ;;
esac
