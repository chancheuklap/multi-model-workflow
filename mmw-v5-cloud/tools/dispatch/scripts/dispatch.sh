#!/usr/bin/env bash
# Cloud edition: native agents communicate; this entry only supplies mechanical tools.
set -euo pipefail
scripts="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
  status|land) command="$1"; shift; exec python3 "$scripts/$command.py" "$@" ;;
  open|show|row|spawn) command="$1"; shift; exec python3 "$scripts/models.py" "$command" "$@" ;;
  board) shift; exec python3 "$scripts/../../../board/server.py" "$@" ;;
  *) echo 'usage: dispatch.sh open --project NAME (--spec N | --ticket N) | show --host HOST | row ROLE --host HOST | spawn worker --ticket N --host HOST | spawn verifier --host HOST | spawn review --host HOST | spawn researcher --prompt FILE --host HOST | status [N --into NIGHT [--ticket]] | land PR | board --host HOST [--port PORT]; HOST is cursor or codex' >&2; exit 2 ;;
esac
