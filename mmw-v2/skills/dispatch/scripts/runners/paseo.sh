#!/usr/bin/env bash
#
# Paseo adapter: the three verbs, and nothing else.
#
#   runners/paseo.sh start --host H --model M --effort E --cwd DIR [--skip-approval] --prompt TEXT
#   runners/paseo.sh send <session-id> <text>
#   runners/paseo.sh liveness <session-id>
#
# start takes host, model, effort, cwd, skip-approval, and the first prompt, and
# prints a session id, or refuses. Paseo sessions are created by create_agent, so
# this verb succeeds without calling `paseo run`.
# send: exit 0 the text was delivered; 3 the session is there and did not take it;
# 2 there is no such session.
# liveness prints one of `alive`, `stopped`, `unknown` on stdout.
#
# MMW_USES: send --no-wait
# MMW_USES: ls -g --json

set -uo pipefail

paseo_() {
  env -u CLICOLOR_FORCE -u CLICOLOR paseo "$@"
}

usage() {
  echo "usage: runners/paseo.sh start --host H --model M --effort E --cwd DIR [--skip-approval] --prompt TEXT" >&2
  echo "       runners/paseo.sh send <session-id> <text>" >&2
  echo "       runners/paseo.sh liveness <session-id>" >&2
  exit 2
}

# Prints the session's status field when ls listed it. Exit 0 found, 1 listed
# without that id, 2 ls could not be asked or its answer could not be read.
ls_status() {
  local ident="$1" json
  json="$(paseo_ ls -g --json 2>/dev/null)" || return 2
  printf '%s' "$json" | MMW_IDENT="$ident" python3 -c '
import json, os, sys

want = os.environ["MMW_IDENT"]
try:
    rows = json.load(sys.stdin)
except Exception:
    sys.exit(2)
if not isinstance(rows, list):
    sys.exit(2)
for row in rows:
    if isinstance(row, dict) and row.get("id") == want:
        print(str(row.get("status") or ""))
        sys.exit(0)
sys.exit(1)
'
}

start() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --host|--model|--effort|--cwd|--prompt)
        [ "$#" -ge 2 ] || usage
        shift 2
        ;;
      --skip-approval)
        shift
        ;;
      *)
        usage
        ;;
    esac
  done
  exit 0
}

send() {
  local ident="${1:-}" text="${2:-}" rc out
  [ -n "$ident" ] && [ -n "$text" ] || usage
  ls_status "$ident" >/dev/null
  rc=$?
  case "$rc" in
    1) exit 2 ;;
    2) exit 3 ;;
  esac
  if out="$(paseo_ send --no-wait "$ident" "$text" 2>&1)"; then
    exit 0
  fi
  printf '%s\n' "$out" >&2
  exit 3
}

liveness() {
  local ident="${1:-}" status rc
  [ -n "$ident" ] || usage
  status="$(ls_status "$ident")"
  rc=$?
  case "$rc" in
    1)
      printf '%s\n' stopped
      exit 0
      ;;
    2)
      printf '%s\n' unknown
      exit 0
      ;;
  esac
  case "$(printf '%s' "$status" | tr '[:upper:]' '[:lower:]')" in
    running|initializing|idle)
      printf '%s\n' alive
      ;;
    closed|error)
      printf '%s\n' stopped
      ;;
    *)
      printf '%s\n' unknown
      ;;
  esac
  exit 0
}

[ "$#" -ge 1 ] || usage
verb="$1"
shift
case "$verb" in
  start) start "$@" ;;
  send) send "$@" ;;
  liveness) liveness "$@" ;;
  *) usage ;;
esac
