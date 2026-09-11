#!/usr/bin/env bash
#
# Paseo adapter: the three verbs of the runner boundary, `stop`, and `self`.
#
#   runners/paseo.sh start --host H --model M --effort E --cwd DIR [--skip-approval]
#                          [--title T] --prompt TEXT
#   runners/paseo.sh send <session-id> <text>
#   runners/paseo.sh liveness <session-id>
#   runners/paseo.sh stop <session-id>
#   runners/paseo.sh self
#   runners/paseo.sh attach --cwd DIR --issue N
#   runners/paseo.sh catalog-status
#   runners/paseo.sh catalog-models <host>
#   runners/paseo.sh diagnostic <host>
#
# start runs `paseo run -d` in DIR and prints the agent id Paseo answers with; exit 1,
# with the reason on stderr, when Paseo did not start it. The host's mode and thinking
# level come from `models.py paseo-args`.
# send: exit 0 the text was delivered; 3 the session is there and did not take it;
# 2 there is no such session.
# liveness prints one of `alive`, `stopped`, `unknown` on stdout.
# stop ends the session: exit 0 it is gone (or was already), 1 it could not be ended.
# self prints the id of the session this process itself runs in, the id `send` reaches:
# exit 0 printed; 3 this process runs in no session of this runner; 1 it does, and its id
# cannot be read (the reason on stderr). The main agent names itself to the relay with it.
# Paseo sets PASEO_AGENT_ID in every agent it runs, and that id is the one `send` takes.
#
# MMW_USES: run -d --json --provider --mode --thinking --cwd --title
# MMW_USES: send --no-wait
# MMW_USES: ls -g --json
# MMW_USES: archive --force
# MMW_USES: provider ls --json
# MMW_USES: provider models --json
# MMW_USES: provider diagnostic --json

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"

paseo_() {
  env -u CLICOLOR_FORCE -u CLICOLOR paseo "$@"
}

usage() {
  echo "usage: runners/paseo.sh start --host H --model M --effort E --cwd DIR [--skip-approval] [--title T] --prompt TEXT" >&2
  echo "       runners/paseo.sh send <session-id> <text>" >&2
  echo "       runners/paseo.sh liveness <session-id>" >&2
  echo "       runners/paseo.sh stop <session-id>" >&2
  echo "       runners/paseo.sh self" >&2
  echo "       runners/paseo.sh attach --cwd DIR --issue N" >&2
  echo "       runners/paseo.sh catalog-status" >&2
  echo "       runners/paseo.sh catalog-models <host>" >&2
  echo "       runners/paseo.sh diagnostic <host>" >&2
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
  local host="" model="" effort="" cwd="" prompt="" title=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --host|--model|--effort|--cwd|--prompt|--title)
        [ "$#" -ge 2 ] || usage
        case "$1" in
          --host) host="$2" ;;
          --model) model="$2" ;;
          --effort) effort="$2" ;;
          --cwd) cwd="$2" ;;
          --prompt) prompt="$2" ;;
          --title) title="$2" ;;
        esac
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
  [ -n "$host" ] && [ -n "$model" ] && [ -n "$cwd" ] && [ -n "$prompt" ] || usage

  local flags line err out ident
  local -a args=()
  flags="$(python3 "$(dirname "$HERE")/models.py" paseo-args "$host" "$model" "$effort")" || exit 1
  while IFS= read -r line; do
    [ -z "$line" ] || args+=("$line")
  done <<<"$flags"
  [ -z "$title" ] || args+=(--title "$title")
  # The temporary file is removed here, on both paths, and not by an EXIT trap: `err` is
  # local to this function and gone by the time the script exits, so a trap naming it
  # removed nothing and failed under `set -u`.
  err="$(mktemp)"
  # PASEO_WORKSPACE_ID from the caller's terminal would put the agent in that workspace
  # instead of DIR (`paseo run` ranks it above --cwd).
  if ! out="$(env -u PASEO_WORKSPACE_ID -u CLICOLOR_FORCE -u CLICOLOR paseo run -d --json \
        "${args[@]}" --cwd "$cwd" -- "$prompt" 2>"$err")"; then
    echo "runners/paseo.sh: paseo run refused $host in $cwd: $(tr '\n' ' ' < "$err")" >&2
    rm -f "$err"
    exit 1
  fi
  rm -f "$err"
  ident="$(printf '%s' "$out" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("agentId") or "")
except Exception:
    pass
')"
  if [ -z "$ident" ]; then
    echo "runners/paseo.sh: paseo run answered without an agentId, so there is no session to report: $out" >&2
    exit 1
  fi
  printf '%s\n' "$ident"
}

send() {
  local ident="${1:-}" text="${2:-}" rc out
  [ -n "$ident" ] && [ -n "$text" ] || usage
  ls_status "$ident" >/dev/null
  rc=$?
  case "$rc" in
    1) exit 2 ;;
    2)
      # Could not ask Paseo at all. That is not "no such session" (exit 2 tells the caller
      # never to send again), so it takes the retry answer, 3 — but says why, because 3
      # alone reads as "it is in a turn", which nobody checked.
      echo "runners/paseo.sh: could not ask Paseo whether $ident is there (paseo ls failed or answered in a shape this cannot read); nothing was sent" >&2
      exit 3
      ;;
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

stop() {
  local ident="${1:-}"
  [ -n "$ident" ] || usage
  ls_status "$ident" >/dev/null
  [ "$?" = 1 ] && exit 0
  # --force interrupts an agent mid-turn; plain archive refuses a running one.
  paseo_ archive --force "$ident" >/dev/null 2>&1 || exit 1
  exit 0
}

self_() {
  local ident="${PASEO_AGENT_ID:-}"
  ident="${ident//[[:space:]]/}"
  if [ -z "$ident" ]; then
    echo "runners/paseo.sh: PASEO_AGENT_ID is not set, so this process is not in a Paseo agent" >&2
    exit 3
  fi
  printf '%s\n' "$ident"
  exit 0
}

[ "$#" -ge 1 ] || usage
verb="$1"
shift
case "$verb" in
  start) start "$@" ;;
  send) send "$@" ;;
  liveness) liveness "$@" ;;
  stop) stop "$@" ;;
  self) self_ ;;
  attach) exit 0 ;;
  catalog-status) paseo_ provider ls --json ;;
  catalog-models)
    [ "$#" -eq 1 ] || usage
    paseo_ provider models "$1" --json ;;
  diagnostic)
    [ "$#" -eq 1 ] || usage
    paseo_ provider diagnostic "$1" --json ;;
  *) usage ;;
esac
