#!/usr/bin/env bash
#
# Orca adapter: the three verbs, and nothing else.
#
#   runners/orca.sh start --host H --model M --effort E --cwd DIR [--skip-approval] [--title T] [--label K=V]... --prompt TEXT
#   runners/orca.sh send <session-id> <text>
#   runners/orca.sh liveness <session-id>
#
# start takes host, model, effort, cwd, skip-approval, and the first prompt, and
# prints a session id, or refuses. One call: `terminal create --worktree path:<abs>
# --command <launch line> --title <name> --json`. The worktree is already cut; this
# verb only starts a session at that absolute path.
# The launch line is models.py `launch-line`: the host binary and its own flags from
# hosts.json, which carry the approval bypass, so `--skip-approval` is always honoured
# by those flags. A host with no launch block (today `pi`) is a refusal, not a start
# with no model, no effort and no bypass.
# send: exit 0 the text was delivered (input_accepted and turn_started); 3 the
# session is there and did not take it (input_accepted without turn_started); 2
# there is no such session (terminal_not_writable); 4 unknown — the list or the
# receipt could not be read, or the handle is past a truncated list.
# liveness prints one of `alive`, `stopped`, `unknown` on stdout. A running process
# and an idle UI are two fields; idle is not what this verb answers.
#
# MMW_USES: terminal create --worktree --command --title --json
# MMW_USES: terminal send --terminal --text --enter --wait-submit --json
# MMW_USES: terminal wait --terminal --for --timeout-ms --json
# MMW_USES: terminal list --json
# MMW_USES: terminal close --terminal --json

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
START_WAIT_MS=30000
SEND_WAIT_S=30
LIVENESS_WAIT_MS=100

orca_() {
  env -u CLICOLOR_FORCE -u CLICOLOR orca "$@"
}

usage() {
  echo "usage: runners/orca.sh start --host H --model M --effort E --cwd DIR [--skip-approval] [--title T] [--label K=V]... --prompt TEXT" >&2
  echo "       runners/orca.sh send <session-id> <text>" >&2
  echo "       runners/orca.sh liveness <session-id>" >&2
  exit 2
}

# Prints "connected writable" when list named the handle. Exit 0 found, 1 listed
# without that handle, 2 list could not be asked or its answer could not be read.
list_row() {
  local ident="$1" json
  json="$(orca_ terminal list --json 2>/dev/null)" || return 2
  printf '%s' "$json" | MMW_IDENT="$ident" python3 -c '
import json, os, sys

# Exit 0 with "<connected> <writable>" when the handle is listed; 1 when a complete list
# was read and the handle is not on it; 2 for everything else. Exit 1 is the one answer
# that becomes "stopped" and "no such session", so only a readable, untruncated list may
# give it: a handle past a truncated page is not known to be gone. Python exits 1 on an
# uncaught error, so the whole read sits inside one try.
want = os.environ["MMW_IDENT"]

def flag(value):
    if value is None:
        return "absent"
    return "true" if value is True or str(value).lower() == "true" else "false"

try:
    payload = json.load(sys.stdin)
    result = payload.get("result") if isinstance(payload, dict) else None
    rows = result.get("terminals") if isinstance(result, dict) else None
    if not isinstance(rows, list):
        sys.exit(2)
    for row in rows:
        if isinstance(row, dict) and str(row.get("handle") or "") == want:
            print("%s %s" % (flag(row.get("connected")), flag(row.get("writable"))))
            sys.exit(0)
    if result.get("truncated"):
        sys.exit(2)
except SystemExit:
    raise
except Exception:
    sys.exit(2)
sys.exit(1)
'
}

parse_json() {
  python3 -c '
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
    sys.exit(2)
kind = sys.argv[1]
result = data.get("result") if isinstance(data.get("result"), dict) else {}
err = data.get("error") if isinstance(data.get("error"), dict) else {}
if kind == "handle":
    handle = result.get("handle")
    terminal = result.get("terminal")
    if not handle and isinstance(terminal, dict):
        handle = terminal.get("handle")
    print(str(handle or data.get("handle") or ""))
elif kind == "send":
    stages = data.get("stages") or result.get("stages") or []
    if not isinstance(stages, list):
        stages = []
    warning = (
        data.get("warning")
        or result.get("warning")
        or err.get("message")
        or ""
    )
    code = err.get("code") or data.get("code") or ""
    print("%s\t%s\t%s" % (code, ",".join(str(s) for s in stages), warning))
elif kind == "wait":
    code = err.get("code") or data.get("code") or ""
    satisfied = result.get("satisfied")
    if satisfied is None:
        satisfied = data.get("satisfied")
    status = str(result.get("status") or data.get("status") or "")
    flag = "true" if satisfied is True or str(satisfied).lower() == "true" else "false"
    print("%s\t%s\t%s" % (code, flag, status))
else:
    sys.exit(2)
' "$1"
}

host_command() {
  python3 "$(dirname "$HERE")/models.py" launch-line "$@"
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
      --title|--label)
        # Metadata for runners that keep it; this one names the session after its worktree.
        [ "$#" -ge 2 ] || usage
        shift 2
        ;;
      *)
        usage
        ;;
    esac
  done
  [ -n "$host" ] && [ -n "$cwd" ] && [ -n "$prompt" ] || usage

  local abs name cmd json handle
  abs="$(CDPATH='' cd -- "$cwd" && pwd -P)" || exit 1
  name="$(basename -- "$abs")"
  [ -n "$name" ] && [ "$name" != "/" ] || name=mmw
  cmd="$(host_command "$host" "$model" "$effort" "$name")" || exit 1

  local err
  err="$(mktemp)"
  trap 'rm -f "$err"' EXIT
  if ! json="$(orca_ terminal create \
        --worktree "path:$abs" \
        --command "$cmd" \
        --title "$name" \
        --json 2>"$err")"; then
    echo "runners/orca.sh: terminal create refused $host at $abs: $(tr '\n' ' ' < "$err")" >&2
    exit 1
  fi
  handle="$(printf '%s' "$json" | parse_json handle)" || handle=""
  if [ -z "$handle" ]; then
    echo "runners/orca.sh: terminal create answered without a handle, so there is no session to report" >&2
    exit 1
  fi

  orca_ terminal wait --terminal "$handle" --for tui-idle \
    --timeout-ms "$START_WAIT_MS" --json >/dev/null 2>&1 || true
  if ! bash "$0" send "$handle" "$prompt" >/dev/null; then
    # A refused start must not leave its agent behind: dispatch is about to say this
    # ticket has no session, and a second start would put two agents on one worktree.
    orca_ terminal close --terminal "$handle" --json >/dev/null 2>&1 || true
    echo "runners/orca.sh: $host started at $abs but did not take its first prompt; that terminal ($handle) was closed" >&2
    exit 1
  fi
  printf '%s\n' "$handle"
  exit 0
}

send() {
  local ident="${1:-}" text="${2:-}" rc out code stages warning
  [ -n "$ident" ] && [ -n "$text" ] || usage
  list_row "$ident" >/dev/null
  rc=$?
  case "$rc" in
    1) exit 2 ;;
    2)
      printf '%s\n' unknown
      exit 4
      ;;
  esac
  out="$(orca_ terminal send --terminal "$ident" --text "$text" --enter \
        --wait-submit "$SEND_WAIT_S" --json 2>&1)" || true
  receipt="$(printf '%s' "$out" | parse_json send)" || {
    printf '%s\n' unknown
    exit 4
  }
  code="${receipt%%	*}"
  rest="${receipt#*	}"
  stages="${rest%%	*}"
  warning="${rest#*	}"
  case "$code" in
    terminal_not_writable|terminal_handle_stale) exit 2 ;;
  esac
  case ",$stages," in
    *,turn_started,*) exit 0 ;;
  esac
  case ",$stages," in
    *,input_accepted,*) exit 3 ;;
  esac
  case "$warning" in
    *"no turn start was observed"*) exit 3 ;;
  esac
  printf '%s\n' unknown
  exit 4
}

liveness() {
  local ident="${1:-}" row rc connected writable
  local exit_out idle_out exit_info idle_info
  local exit_code exit_sat exit_status idle_code idle_sat idle_status
  [ -n "$ident" ] || usage
  row="$(list_row "$ident")"
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
  # A listed handle whose connected or writable is not true is not proven stopped: Orca
  # falls back to a background handle when its UI cannot adopt a terminal, which can show
  # as not connected while the process runs. The `terminal wait --for exit` probe below
  # decides; nothing is answered from those two fields alone.

  exit_out="$(orca_ terminal wait --terminal "$ident" --for exit \
              --timeout-ms "$LIVENESS_WAIT_MS" --json 2>&1)" || true
  idle_out="$(orca_ terminal wait --terminal "$ident" --for tui-idle \
              --timeout-ms "$LIVENESS_WAIT_MS" --json 2>&1)" || true
  exit_info="$(printf '%s' "$exit_out" | parse_json wait)" || exit_info=""
  idle_info="$(printf '%s' "$idle_out" | parse_json wait)" || idle_info=""
  if [ -z "$exit_info" ] && [ -z "$idle_info" ]; then
    printf '%s\n' unknown
    exit 0
  fi

  exit_code="${exit_info%%	*}"; rest="${exit_info#*	}"
  exit_sat="${rest%%	*}"; exit_status="${rest#*	}"
  idle_code="${idle_info%%	*}"; rest="${idle_info#*	}"
  idle_status="${rest#*	}"
  case "$exit_code$idle_code" in
    *terminal_handle_stale*|*terminal_not_writable*)
      printf '%s\n' stopped
      exit 0
      ;;
  esac
  if [ "$exit_sat" = true ]; then
    printf '%s\n' stopped
    exit 0
  fi
  # status=running is "the process is running". satisfied on tui-idle is "the UI
  # is idle". This verb answers the first, never the second.
  case "$(printf '%s' "$idle_status" | tr '[:upper:]' '[:lower:]')" in
    running)
      printf '%s\n' alive
      exit 0
      ;;
    exited)
      printf '%s\n' stopped
      exit 0
      ;;
  esac
  if [ "$exit_code" = timeout ]; then
    printf '%s\n' alive
    exit 0
  fi
  printf '%s\n' unknown
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
