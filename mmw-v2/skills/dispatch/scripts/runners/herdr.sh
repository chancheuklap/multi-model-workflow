#!/usr/bin/env bash
#
# Herdr adapter: the three verbs, and nothing else.
#
#   runners/herdr.sh start --host H --model M --effort E --cwd DIR [--skip-approval] --prompt TEXT
#   runners/herdr.sh send <session-id> <text>
#   runners/herdr.sh liveness <session-id>
#
# start takes host, model, effort, cwd, skip-approval, and the first prompt, and
# prints a session id, or refuses with exit 1 and one stderr line naming what failed.
# A pane is created first: `agent start` only runs in an existing pane. The launch
# flags come from models.py (`bypass-argv`); a host it cannot build them for is a
# refusal, not a start without a model.
# send: exit 0 the text was delivered; 3 the session is there and did not take it;
# 2 there is no such session; 4 unknown — already working, or the list could not
# be read, so a `--until working` match would not prove a new turn started.
# liveness prints one of `alive`, `stopped`, `unknown` on stdout. Stopped means
# the name is absent from `agent list`; a name still on that list is not stopped.
#
# MMW_USES: tab create --cwd --no-focus
# MMW_USES: agent start --kind --pane --timeout
# MMW_USES: agent prompt --wait --until --timeout
# MMW_USES: agent list

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
START_TIMEOUT_MS=30000
PROMPT_TIMEOUT_MS=30000

herdr_() {
  env -u CLICOLOR_FORCE -u CLICOLOR herdr "$@"
}

usage() {
  echo "usage: runners/herdr.sh start --host H --model M --effort E --cwd DIR [--skip-approval] --prompt TEXT" >&2
  echo "       runners/herdr.sh send <session-id> <text>" >&2
  echo "       runners/herdr.sh liveness <session-id>" >&2
  exit 2
}

# Prints the session's agent_status when list named it. Exit 0 found, 1 listed
# without that name, 2 list could not be asked or its answer could not be read.
list_status() {
  local ident="$1" json
  json="$(herdr_ agent list 2>/dev/null)" || return 2
  printf '%s' "$json" | MMW_IDENT="$ident" python3 -c '
import json, os, sys

# Exit 0 with the status when the name is on the list; 1 when the list was read and the
# name is not on it; 2 for everything else. Exit 1 is the one answer that means "gone",
# so nothing but a readable list may produce it: an answer in another shape, or any error
# while reading it, is "could not tell" (2), never "stopped". Python exits 1 on an
# uncaught error, which is why the whole read sits inside one try.
want = os.environ["MMW_IDENT"]
try:
    payload = json.load(sys.stdin)
    result = payload.get("result") if isinstance(payload, dict) else None
    agents = result.get("agents") if isinstance(result, dict) else None
    if not isinstance(agents, list):
        sys.exit(2)
    for row in agents:
        if isinstance(row, dict) and str(row.get("name") or "") == want:
            print(str(row.get("agent_status") or row.get("status") or ""))
            sys.exit(0)
except SystemExit:
    raise
except Exception:
    sys.exit(2)
sys.exit(1)
'
}

error_code() {
  printf '%s' "$1" | python3 -c '
import json, sys

raw = sys.stdin.read()
data = None
try:
    data = json.loads(raw)
except Exception:
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
            break
        except Exception:
            pass
if not isinstance(data, dict):
    sys.exit(0)
err = data.get("error")
if isinstance(err, dict):
    print(str(err.get("code") or ""))
'
}

host_argv() {
  python3 "$(dirname "$HERE")/models.py" bypass-argv "$@"
}
start() {
  local host="" model="" effort="" cwd="" prompt=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --host|--model|--effort|--cwd|--prompt)
        [ "$#" -ge 2 ] || usage
        case "$1" in
          --host) host="$2" ;;
          --model) model="$2" ;;
          --effort) effort="$2" ;;
          --cwd) cwd="$2" ;;
          --prompt) prompt="$2" ;;
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
  [ -n "$host" ] && [ -n "$cwd" ] && [ -n "$prompt" ] || usage

  local name pane json
  name="$(basename -- "$cwd")"
  [ -n "$name" ] && [ "$name" != "/" ] || name=mmw

  local err
  err="$(mktemp)"
  trap 'rm -f "$err"' EXIT
  if ! json="$(herdr_ tab create --cwd "$cwd" --no-focus 2>"$err")"; then
    echo "runners/herdr.sh: could not open a tab in $cwd: $(tr '\n' ' ' < "$err")" >&2
    exit 1
  fi
  pane="$(printf '%s' "$json" | python3 -c '
import json, sys

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print(str(((payload.get("result") or {}).get("root_pane") or {}).get("pane_id") or ""))
')"
  [ -n "$pane" ] || {
    echo "runners/herdr.sh: tab create answered without a root pane id, so there is nowhere to start $host" >&2
    exit 1
  }

  local -a argv=() extra=()
  local lines
  lines="$(host_argv "$host" "$model" "$effort" "$name")" || exit 1
  while IFS= read -r line; do
    [ -n "$line" ] && extra+=("$line")
  done <<< "$lines"
  argv=(agent start "$name" --kind "$host" --pane "$pane" --timeout "$START_TIMEOUT_MS")
  if [ "${#extra[@]}" -gt 0 ]; then
    argv+=(-- "${extra[@]}")
  fi
  if ! herdr_ "${argv[@]}" >/dev/null 2>"$err"; then
    echo "runners/herdr.sh: agent start refused $host in pane $pane: $(tr '\n' ' ' < "$err")" >&2
    exit 1
  fi
  if ! bash "$0" send "$name" "$prompt" >/dev/null; then
    echo "runners/herdr.sh: $host started in pane $pane as $name, but did not take its first prompt; that agent is still running there" >&2
    exit 1
  fi
  printf '%s\n' "$name"
  exit 0
}

send() {
  local ident="${1:-}" text="${2:-}" status rc out code
  [ -n "$ident" ] && [ -n "$text" ] || usage
  status="$(list_status "$ident")"
  rc=$?
  case "$rc" in
    1) exit 2 ;;
    2)
      printf '%s\n' unknown
      exit 4
      ;;
  esac
  case "$(printf '%s' "$status" | tr '[:upper:]' '[:lower:]')" in
    working|unknown|"")
      printf '%s\n' unknown
      exit 4
      ;;
  esac
  if out="$(herdr_ agent prompt "$ident" "$text" \
            --wait --until working --until blocked \
            --timeout "$PROMPT_TIMEOUT_MS" 2>&1)"; then
    exit 0
  fi
  code="$(error_code "$out")"
  printf '%s\n' "$out" >&2
  case "$code" in
    agent_not_found) exit 2 ;;
    agent_blocked|agent_prompt_stalled|timeout) exit 3 ;;
  esac
  printf '%s\n' unknown
  exit 4
}

liveness() {
  local ident="${1:-}" status rc
  [ -n "$ident" ] || usage
  status="$(list_status "$ident")"
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
    idle|working|blocked|done)
      printf '%s\n' alive
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
