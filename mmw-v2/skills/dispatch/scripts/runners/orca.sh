#!/usr/bin/env bash
#
# Orca adapter: the three verbs of the runner boundary, `stop`, and `self`.
#
#   runners/orca.sh start --host H --model M --effort E --cwd DIR [--skip-approval] [--title T] --prompt TEXT
#   runners/orca.sh send <session-id> <text>
#   runners/orca.sh liveness <session-id>
#   runners/orca.sh stop <session-id>
#   runners/orca.sh self
#   runners/orca.sh attach --cwd DIR --issue N
#
# start takes host, model, effort, cwd, skip-approval, and the first prompt, and
# prints a session id, or refuses with exit 1 and the reason on stderr. The worktree is
# already cut; this verb only starts a session at that absolute path, with one
# `terminal create --worktree path:<abs> --command 'exec <launch line>' --title <name>
# --json`. <name> is the title dispatch passes (`#<n> worker`, `#<n> reviewer`,
# `#<n> verifier`), so the sessions of one ticket, which share its worktree, have tabs
# that tell them apart; a start without a title is named after its worktree. The same
# name is the session name a host that takes one is given.
# The launch line is models.py `launch-line` with the first prompt: the host binary, its
# own flags from hosts.json, which carry the approval bypass, so `--skip-approval` is
# always honoured by those flags, and last the prompt, which each host takes as its first
# turn (`grok [PROMPT]`, `codex [PROMPT]`, `claude [prompt]`, `cursor-agent [prompt]`).
# The prompt is not typed into the terminal: for some programs Orca cannot report
# whether typed input started a turn (Grok, Orca 1.4.199: `input_accepted` with
# `observation` `unsupported`), so a typed first prompt could not be confirmed. A host
# with no launch block (today `pi`) is a refusal, not a start with no model, no effort
# and no bypass.
# Orca runs `--command` in a shell that stays at its prompt when the command ends, and a
# terminal whose shell is at its prompt is a running terminal to Orca. `exec` makes the
# host the terminal's own process, so the terminal ends when the host does: that is how
# start sees a host that quit, and how `liveness` answers `stopped` for one.
# After the create, start waits up to 3 s for the terminal to exit. A wait that times out
# is a host that is running, and the handle is printed. An exit in that time (satisfied,
# status `exited`, or the handle stale or not writable) is a host that quit at once: the
# refusal carries the terminal's last lines (`terminal read`, `result.terminal.tail`),
# which Orca 1.4.199 has already emptied once the terminal exited, so it also gives the
# command to run by hand to see why. An answer this cannot read falls back to `liveness`
# of the handle: `alive` is a start, anything else a refusal. A refused start closes its
# terminal: dispatch is about to say this ticket has no session, and a second start would
# put two agents on one worktree.
# A host started with a model it does not know does not exit (Grok, Claude and Codex show
# the error on screen and wait), so this wait cannot catch a bad model; the model has to
# be checked against the host's catalog before `start`.
# send: exit 0 the text was delivered (input_accepted and turn_started); 4 the text went
# into the terminal and no turn start was seen — the program is mid-turn and will read it
# when the turn ends, or it is one Orca cannot observe (`observation` `unsupported`) — or
# the receipt could not be read after the send: handed over, not confirmed, and not to be
# typed again; 3 nothing was typed — the list could not be read, the handle is past a
# truncated list, or Orca refused the send with an error of its own — so sending again
# is safe; 2 there is no such session (terminal_not_writable, or a complete list without
# it). The receipt's stages are `result.send.prompt.stages` and its warnings
# `result.warnings` (Orca 1.4.199, read 2026-09-10 off a real `terminal send --json`).
# liveness prints one of `alive`, `stopped`, `unknown` on stdout. A running process
# and an idle UI are two fields; idle is not what this verb answers.
# stop ends the session: exit 0 it is gone (or was already), 1 it could not be ended.
# self prints the id of the session this process itself runs in, the id `send` reaches:
# exit 0 printed; 3 this process runs in no session of this runner; 1 it does, and its id
# cannot be read (the reason on stderr). The main agent names itself to the relay with it.
# Orca sets ORCA_TERMINAL_HANDLE in every terminal it runs, and that handle is the one
# `terminal list` lists and `send` takes.
#
# MMW_USES: terminal create --worktree --command --title --json
# MMW_USES: terminal send --terminal --text --enter --wait-submit --json
# MMW_USES: terminal wait --terminal --for --timeout-ms --json
# MMW_USES: terminal read --terminal --json
# MMW_USES: terminal list --json
# MMW_USES: terminal close --terminal --json
# MMW_USES: worktree set --worktree --issue

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
START_EXIT_WAIT_MS=3000
START_TAIL_LINES=5
SEND_WAIT_S=30
LIVENESS_WAIT_MS=100

orca_() {
  env -u CLICOLOR_FORCE -u CLICOLOR orca "$@"
}

usage() {
  echo "usage: runners/orca.sh start --host H --model M --effort E --cwd DIR [--skip-approval] [--title T] --prompt TEXT" >&2
  echo "       runners/orca.sh send <session-id> <text>" >&2
  echo "       runners/orca.sh liveness <session-id>" >&2
  echo "       runners/orca.sh stop <session-id>" >&2
  echo "       runners/orca.sh self" >&2
  echo "       runners/orca.sh attach --cwd DIR --issue N" >&2
  exit 2
}

attach() {
  local cwd="" issue=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cwd) [ "$#" -ge 2 ] || usage; cwd="$2"; shift 2 ;;
      --issue) [ "$#" -ge 2 ] || usage; issue="$2"; shift 2 ;;
      *) usage ;;
    esac
  done
  [ -d "$cwd" ] && [[ "$issue" =~ ^[0-9]+$ ]] || usage
  local abs
  abs="$(CDPATH='' cd -- "$cwd" && pwd -P)" || return 1
  orca_ worktree set --worktree "path:$abs" --issue "$issue" >/dev/null
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
    send = result.get("send") if isinstance(result.get("send"), dict) else {}
    prompt = send.get("prompt") if isinstance(send.get("prompt"), dict) else {}
    stages = prompt.get("stages") or []
    if not isinstance(stages, list):
        stages = []
    warnings = result.get("warnings") or []
    if not isinstance(warnings, list):
        warnings = [warnings]
    warning = " ".join(str(w) for w in warnings) or err.get("message") or ""
    observation = str(prompt.get("observation") or "")
    code = err.get("code") or data.get("code") or ""
    print("%s\t%s\t%s\t%s" % (code, ",".join(str(s) for s in stages), observation,
                                 " ".join(warning.split())))
elif kind == "wait":
    # A condition that was met is answered under result.wait, and a wait that ran out
    # as error.code `timeout` (Orca 1.4.199, read 2026-09-11 off a real
    # `terminal wait --for exit --json`).
    wait = result.get("wait") if isinstance(result.get("wait"), dict) else result
    code = err.get("code") or data.get("code") or ""
    satisfied = wait.get("satisfied")
    if satisfied is None:
        satisfied = data.get("satisfied")
    status = str(wait.get("status") or data.get("status") or "")
    flag = "true" if satisfied is True or str(satisfied).lower() == "true" else "false"
    print("%s\t%s\t%s" % (code, flag, status))
else:
    sys.exit(2)
' "$1"
}

host_command() {
  python3 "$(dirname "$HERE")/models.py" launch-line "$@"
}

# Prints the last lines the terminal holds, blank ones dropped, joined on one line;
# nothing when they cannot be read.
last_lines() {
  orca_ terminal read --terminal "$1" --json 2>/dev/null | MMW_KEEP="$START_TAIL_LINES" python3 -c '
import json, os, sys

try:
    tail = json.load(sys.stdin)["result"]["terminal"]["tail"]
    lines = [" ".join(str(line).split()) for line in tail]
    print(" | ".join([line for line in lines if line][-int(os.environ["MMW_KEEP"]):]))
except Exception:
    pass
'
}

start() {
  local host="" model="" effort="" cwd="" prompt="" title=""
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
      --title)
        [ "$#" -ge 2 ] || usage
        title="$2"
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
  name="$title"
  [ -n "$name" ] || name="$(basename -- "$abs")"
  [ -n "$name" ] && [ "$name" != "/" ] || name=mmw
  cmd="$(host_command "$host" "$model" "$effort" "$name" "$prompt")" || exit 1

  local err
  err="$(mktemp)"
  trap 'rm -f "$err"' EXIT
  if ! json="$(orca_ terminal create \
        --worktree "path:$abs" \
        --command "exec $cmd" \
        --title "$name" \
        --json 2>"$err")"; then
    # Orca answers a refusal as JSON on stdout (`ok: false`, `error.message`); stderr is
    # usually empty, so the reason is read from both.
    local reason
    reason="$( { tr '\n' ' ' < "$err"; printf '%s' "$json" | python3 -c '
import json, sys
try:
    error = json.load(sys.stdin).get("error") or {}
    print(error.get("message") or error.get("code") or "")
except Exception:
    pass
'; } | tr '\n' ' ')"
    echo "runners/orca.sh: terminal create refused $host at $abs: ${reason:-Orca gave no reason}" >&2
    exit 1
  fi
  handle="$(printf '%s' "$json" | parse_json handle)" || handle=""
  if [ -z "$handle" ]; then
    echo "runners/orca.sh: terminal create answered without a handle, so there is no session to report" >&2
    exit 1
  fi

  local out info code rest satisfied status
  out="$(orca_ terminal wait --terminal "$handle" --for exit \
        --timeout-ms "$START_EXIT_WAIT_MS" --json 2>&1)" || true
  info="$(printf '%s' "$out" | parse_json wait)" || info=""
  code="${info%%	*}"
  rest="${info#*	}"
  satisfied="${rest%%	*}"
  status="$(printf '%s' "${rest#*	}" | tr '[:upper:]' '[:lower:]')"
  if [ "$code" = timeout ]; then
    printf '%s\n' "$handle"
    exit 0
  fi
  case "$code" in
    terminal_handle_stale|terminal_not_writable) satisfied=true ;;
  esac
  if [ "$satisfied" = true ] || [ "$status" = exited ]; then
    local tail line
    tail="$(last_lines "$handle")"
    line="$(host_command "$host" "$model" "$effort" "$name" 2>/dev/null)"
    orca_ terminal close --terminal "$handle" --json >/dev/null 2>&1 || true
    echo "runners/orca.sh: $host exited within $((START_EXIT_WAIT_MS / 1000)) s of starting at $abs, so there is no session, and its terminal ($handle) was closed; its last lines: ${tail:-none, Orca kept no output}; to see why, run it by hand there: $line" >&2
    exit 1
  fi
  # An answer that says neither: the handle's own liveness decides.
  local answer
  answer="$(bash "$0" liveness "$handle" 2>/dev/null)" || answer=""
  if [ "$answer" = alive ]; then
    printf '%s\n' "$handle"
    exit 0
  fi
  orca_ terminal close --terminal "$handle" --json >/dev/null 2>&1 || true
  echo "runners/orca.sh: $host was started at $abs and whether it is still running could not be read (terminal wait answered: $(printf '%s' "$out" | tr '\n' ' ' | tr -s ' '); liveness answered ${answer:-nothing}), so its terminal ($handle) was closed" >&2
  exit 1
}

send() {
  local ident="${1:-}" text="${2:-}" rc out code stages observation warning receipt rest
  [ -n "$ident" ] && [ -n "$text" ] || usage
  list_row "$ident" >/dev/null
  rc=$?
  case "$rc" in
    1) exit 2 ;;
    2)
      echo "runners/orca.sh: could not tell from terminal list whether $ident is there; nothing was sent" >&2
      exit 3
      ;;
  esac
  out="$(orca_ terminal send --terminal "$ident" --text "$text" --enter \
        --wait-submit "$SEND_WAIT_S" --json 2>&1)" || true
  receipt="$(printf '%s' "$out" | parse_json send)" || {
    echo "runners/orca.sh: terminal send to $ident answered with no receipt this can read; the text may be in the terminal" >&2
    printf '%s\n' unknown
    exit 4
  }
  code="${receipt%%	*}"
  rest="${receipt#*	}"
  stages="${rest%%	*}"
  rest="${rest#*	}"
  observation="${rest%%	*}"
  warning="${rest#*	}"
  case "$code" in
    terminal_not_writable|terminal_handle_stale) exit 2 ;;
  esac
  case ",$stages," in
    *,turn_started,*) exit 0 ;;
  esac
  case ",$stages," in
    *,input_accepted,*)
      if [ "$observation" = unsupported ]; then
        echo "runners/orca.sh: $ident took the text, and Orca cannot observe the program in it, so whether a turn started is not known: $warning" >&2
      else
        echo "runners/orca.sh: $ident took the text and no turn start was seen; a program mid-turn reads it when the turn ends: $warning" >&2
      fi
      printf '%s\n' unknown
      exit 4
      ;;
  esac
  if [ -n "$code" ]; then
    echo "runners/orca.sh: Orca refused the send to $ident ($code); nothing was typed: $warning" >&2
    exit 3
  fi
  echo "runners/orca.sh: terminal send to $ident answered with no stage this can read; the text may be in the terminal: $warning" >&2
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

stop() {
  local ident="${1:-}"
  [ -n "$ident" ] || usage
  list_row "$ident" >/dev/null
  [ "$?" = 1 ] && exit 0
  orca_ terminal close --terminal "$ident" --json >/dev/null 2>&1 || exit 1
  exit 0
}

self_() {
  if [ -n "${ORCA_TERMINAL_HANDLE:-}" ]; then
    printf '%s\n' "$ORCA_TERMINAL_HANDLE"
    exit 0
  fi
  if [ "$(printf '%s' "${TERM_PROGRAM:-}" | tr '[:upper:]' '[:lower:]')" = orca ]; then
    echo "runners/orca.sh: this process runs in an Orca terminal (TERM_PROGRAM=Orca) and ORCA_TERMINAL_HANDLE is not set, so its terminal handle cannot be read" >&2
    exit 1
  fi
  echo "runners/orca.sh: neither ORCA_TERMINAL_HANDLE nor TERM_PROGRAM=Orca is set, so this process is not in an Orca terminal" >&2
  exit 3
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
  attach) attach "$@" ;;
  *) usage ;;
esac
