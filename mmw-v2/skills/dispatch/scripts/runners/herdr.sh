#!/usr/bin/env bash
#
# Herdr adapter: the three verbs, and nothing else.
#
#   runners/herdr.sh start --host H --model M --effort E --cwd DIR [--skip-approval] --prompt TEXT
#   runners/herdr.sh send <session-id> <text>
#   runners/herdr.sh liveness <session-id>
#
# start takes host, model, effort, cwd, skip-approval, and the first prompt, and
# prints a session id, or refuses. A pane is created first: `agent start` only
# runs in an existing pane.
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
HOSTS="$(dirname "$(dirname "$HERE")")/hosts.json"
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

want = os.environ["MMW_IDENT"]
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(2)
if not isinstance(payload, dict):
    sys.exit(2)
agents = (payload.get("result") or {}).get("agents") or payload.get("agents") or []
if not isinstance(agents, list):
    sys.exit(2)
for row in agents:
    if not isinstance(row, dict):
        continue
    if str(row.get("name") or "") == want:
        print(str(row.get("agent_status") or row.get("status") or ""))
        sys.exit(0)
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
  local host="$1" model="$2" effort="$3" name="$4"
  [ -f "$HOSTS" ] || return 0
  MMW_HOSTS="$HOSTS" MMW_HOST="$host" MMW_MODEL="$model" \
    MMW_EFFORT="$effort" MMW_NAME="$name" python3 -c '
import json, os, sys
from pathlib import Path

try:
    catalog = json.loads(Path(os.environ["MMW_HOSTS"]).read_text(encoding="utf-8"))
except Exception:
    sys.exit(0)
block = ((catalog.get("hosts") or {}).get(os.environ["MMW_HOST"]) or {}).get("herdr") or {}
argv = block.get("argv") or []
repl = {
    "{model}": os.environ.get("MMW_MODEL") or "",
    "{effort}": os.environ.get("MMW_EFFORT") or "",
    "{name}": os.environ.get("MMW_NAME") or "",
}
for part in argv:
    text = str(part)
    for token, value in repl.items():
        text = text.replace(token, value)
    print(text)
'
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

  if ! json="$(herdr_ tab create --cwd "$cwd" --no-focus 2>/dev/null)"; then
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
  [ -n "$pane" ] || exit 1

  local -a argv=() extra=()
  while IFS= read -r line; do
    [ -n "$line" ] && extra+=("$line")
  done < <(host_argv "$host" "$model" "$effort" "$name")
  argv=(agent start "$name" --kind "$host" --pane "$pane" --timeout "$START_TIMEOUT_MS")
  if [ "${#extra[@]}" -gt 0 ]; then
    argv+=(-- "${extra[@]}")
  fi
  if ! herdr_ "${argv[@]}" >/dev/null 2>&1; then
    exit 1
  fi
  if ! bash "$0" send "$name" "$prompt" >/dev/null; then
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
