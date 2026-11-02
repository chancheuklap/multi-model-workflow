#!/usr/bin/env bash
# Role-routed session dispatch with assignment files and result notifications.
# Ticket reports and repository checks use the adjacent verify-ticket tool.
# Exit 0: completed the requested operation. Exit 2: refused, with a reason on stderr.
# Resume preserves adapter receipts: 3 means retryable; 4 means delivery is unconfirmed
# and must not be repeated.
set -uo pipefail

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
DISPATCH_SKILL="$(dirname "$(dirname "$SKILL_ROOT")")/skills/dispatch/SKILL.md"
MODELS_PY="$SKILL_ROOT/scripts/models.py"
BRIEFS="$SKILL_ROOT/scripts/briefs.py"
TRACKER="$SKILL_ROOT/scripts/tracker.py"
RELAY="$SKILL_ROOT/scripts/relay.py"
WATCHDOG="$SKILL_ROOT/scripts/watchdog.py"
BOARD_SUPERVISOR="$(dirname "$(dirname "$SKILL_ROOT")")/board/supervisor.py"
STATUS="$SKILL_ROOT/scripts/status.py"
STATEDIR="$SKILL_ROOT/scripts/statedir.py"
PR="$SKILL_ROOT/scripts/pr.py"
VERIFY="$(dirname "$SKILL_ROOT")/verify-ticket/scripts/verify-ticket.py"
EVENTS="$(dirname "$SKILL_ROOT")/verify-ticket/scripts/events.py"
export MMW_DISPATCH_EVENTS="$EVENTS"
MMW_HOME="$(python3 -c 'import os; from pathlib import Path; print(Path(os.environ.get("MMW_HOME") or "~/.mmw-v5").expanduser().resolve())')" || exit 2
export MMW_HOME
MODELS_JSON="$MMW_HOME/models.json"
RUNNER=""
RUNNER_NAME=""

gh_() { env -u CLICOLOR_FORCE -u CLICOLOR gh "$@"; }

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh open SPEC --into BASE --project PROJECT --worker-task FILE --reviewer-task FILE
       dispatch.sh board [--url]
       dispatch.sh open-ticket N --into BASE [--task FILE]
       dispatch.sh start N worker|reviewer --task FILE
       dispatch.sh send worker|reviewer N --task FILE [--into BASE]
       dispatch.sh advance SPEC
       dispatch.sh integrate|integrated|land|retract N
       dispatch.sh wait N worker|reviewer
       dispatch.sh resume N MESSAGE
       dispatch.sh status|findings|summary|finish|suspend SPEC
       dispatch.sh pr --base B --head H --title T --body-file FILE
       dispatch.sh route N CHILD fixed|stale|became-ticket --report FILE [--commit SHA|--reason REASON|--became TARGET]
       dispatch.sh send <role> [--cwd DIR] [--follow FILE] <task file>...
       dispatch.sh report <batch>/<n> <answer file>
       dispatch.sh brief show|close <batch>
       dispatch.sh resume <batch>/<n> <message>
       dispatch.sh stop <batch>/<n>
       dispatch.sh ack brief <batch> | <ticket> <event>
       dispatch.sh queue
       dispatch.sh wait-wake
       dispatch.sh watchdog arm|status
       dispatch.sh self
USAGE
  exit 2
}

runner() {
  bash "$RUNNER" "$@"
}

runner_call() {
  local name="$1"
  shift
  [ -f "$SKILL_ROOT/scripts/runners/$name.sh" ] || {
    echo "dispatch: no runner adapter for $name" >&2
    return 2
  }
  bash "$SKILL_ROOT/scripts/runners/$name.sh" "$@"
}

use_runner() {
  RUNNER_NAME="$1"
  RUNNER="$SKILL_ROOT/scripts/runners/$1.sh"
  [ -f "$RUNNER" ] || refuse "no runner adapter for $1 at $RUNNER; choose a runner with models.py config runner <name>"
}

own_session() {
  local name out err rc asked=""
  err="$(mktemp)" || return 2
  for name in paseo herdr orca codex-app; do
    [ -f "$SKILL_ROOT/scripts/runners/$name.sh" ] || continue
    asked="$asked $name"
    out="$(runner_call "$name" self 2>"$err")"
    rc=$?
    case "$rc" in
      0)
        rm -f "$err"
        [ -n "$out" ] || { echo "dispatch: $name returned an empty session identity" >&2; return 2; }
        printf '%s\t%s\n' "$name" "$out"
        return 0 ;;
      3) ;;
      *)
        echo "dispatch: cannot identify this session on $name: $(tr '\n' ' ' < "$err")" >&2
        rm -f "$err"
        return 2 ;;
    esac
  done
  rm -f "$err"
  echo "dispatch: this process runs in no identifiable runner session (asked:$asked); run from a supported runner session" >&2
  return 2
}

repo_slug() {
  python3 "$TRACKER"
}

watch_batch() {
  local repo="$1" batch="$2" name="$3" session="$4"
  python3 "$RELAY" start --repo "$repo" --briefs "$batch" --runner "$name" --session "$session" >&2 || return 2
  if ! python3 "$WATCHDOG" arm --repo "$repo" >&2; then
    python3 "$RELAY" stop --repo "$repo" --briefs "$batch" --keep-briefs >&2
    echo "dispatch: watchdog could not be armed for batch $batch; no session was started. Inspect watchdog.log and retry" >&2
    return 2
  fi
}

close_batch_watch() {
  local repo="$1" batch="$2" keep="${3:-}" code
  local -a args=()
  [ -z "$keep" ] || args+=(--keep-briefs)
  python3 "$RELAY" stop --repo "$repo" --briefs "$batch" ${args[@]+"${args[@]}"} >&2
  code=$?
  case "$code" in 0|3) return 0 ;; *) return 2 ;; esac
}

brief_footer() {
  local brief="$1" command
  printf -v command 'MMW_HOME=%q bash %q report %q <answer-file>' "$MMW_HOME" "$SELF" "$brief"
  printf '%s\n' '---' "Result destination for brief $brief:" \
    'Write your answer to a UTF-8 file and replace <answer-file> with its path in this command:' \
    "$command"
}

start_session() {
  local role="$1" host="$2" model="$3" effort="$4" cwd="$5" prompt="$6" title="$7" session
  shift 7
  printf -v prompt 'Assigned role: %s. Read the dispatch skill at %q in full, then follow its route for your assigned role. Use the task files below as additional assignment input.\n\n%s' "$role" "$DISPATCH_SKILL" "$prompt"
  local -a extra=()
  local value
  for value in "$@"; do extra+=(--env "$value"); done
  session="$(runner start --host "$host" --model "$model" --effort "$effort" \
    --cwd "$cwd" --prompt "$prompt" --skip-approval --title "$title" \
    --env "GH_REPO=$GH_REPO" --env "MMW_HOME=$MMW_HOME" --env "MMW_RUNNER=$RUNNER_NAME" ${extra[@]+"${extra[@]}"})" \
    || return 2
  [ -n "$session" ] || return 2
  printf '%s\n' "$session" | tail -n 1
}

close_batch() {
  local batch="$1" keep="${2:-}" repo listed name state role run session rest failed=""
  repo="$(repo_slug)" || return 2
  listed="$(python3 "$BRIEFS" show --repo "$repo" --batch "$batch")" || return 2
  while IFS=$'\t' read -r name state role run session rest; do
    [ -n "$session" ] && [ "$session" != - ] || continue
    if runner_call "$run" stop "$session" >/dev/null; then
      if [ -n "$keep" ]; then
        python3 "$BRIEFS" lost --repo "$repo" --brief "$name" --reason 'Stopped after another session failed to start' || return 2
      fi
    else
      failed="$failed $run:$session"
    fi
  done <<<"$listed"
  if [ -n "$failed" ]; then
    echo "dispatch: batch $batch keeps its records and answers because sessions could not be stopped:$failed; resolve the runner error and retry brief close" >&2
    return 2
  fi
  close_batch_watch "$repo" "$batch" "$keep" || return 2
  [ -z "$keep" ] || return 0
  python3 "$BRIEFS" forget --repo "$repo" --batch "$batch" || return 2
  echo "dispatch: closed brief batch $batch" >&2
}

send_many() {
  [ "$#" -ge 2 ] || usage
  local role="$1" cwd="" follows="" file path prompt row host model effort
  local repo parent parent_runner parent_session batch copy session error n=0
  local -a files=() started=()
  shift
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --cwd|--follow)
        [ "$#" -ge 2 ] || usage
        case "$1" in --cwd) cwd="$2" ;; --follow) follows="$2" ;; esac
        shift 2 ;;
      --) shift; break ;;
      -*) usage ;;
      *) break ;;
    esac
  done
  [ "$#" -ge 1 ] || usage
  for file in "$@"; do
    [ -s "$file" ] && [ -f "$file" ] || refuse "no nonempty task file at $file; write the task before sending"
    path="$(realpath "$file")" || refuse "cannot resolve task file $file"
    files+=("$path")
  done
  if [ -n "$follows" ]; then
    [ -s "$follows" ] && [ -f "$follows" ] || refuse "no nonempty instructions file at $follows"
    follows="$(realpath "$follows")" || refuse "cannot resolve instructions file $follows"
  fi
  if [ -n "$cwd" ]; then
    cd -- "$cwd" || refuse "cannot enter working directory $cwd"
  fi
  if [ -z "$cwd" ]; then
    cwd="$(git rev-parse --show-toplevel 2>/dev/null)" || refuse "send needs a Git worktree"
    cd -- "$cwd" || refuse "cannot enter worktree $cwd"
  else
    git rev-parse --show-toplevel >/dev/null 2>&1 || refuse "send needs a Git worktree"
    cwd="$(pwd -P)"
  fi
  repo="$(repo_slug)" || return 2
  export GH_REPO="$repo"
  use_runner "$(python3 "$MODELS_PY" runner)"
  MMW_CATALOG_MODE="$(python3 "$MODELS_PY" catalog-source "$RUNNER_NAME")" || return 2
  export MMW_CATALOG_MODE
  row="$(python3 "$MODELS_PY" row "$role")" || return 2
  IFS=$'\t' read -r host model effort <<<"$row"
  [ -n "$host" ] && [ -n "$model" ] || refuse "no model row for $role in $MODELS_JSON"
  parent="$(own_session)" || return 2
  parent_runner="${parent%%$'\t'*}"
  parent_session="${parent#*$'\t'}"
  python3 "$BRIEFS" check-references --repo "$repo" -- "${files[@]}" || return 2
  batch="$(python3 "$BRIEFS" new --repo "$repo" --role "$role" --count "${#files[@]}" \
    --runner "$parent_runner" --session "$parent_session" --worktree "$cwd")" || return 2
  if ! watch_batch "$repo" "$batch" "$parent_runner" "$parent_session"; then
    close_batch_watch "$repo" "$batch" keep
    refuse "notifications could not start for batch $batch; its records were kept, and no child was started"
  fi
  for file in "${files[@]}"; do
    n=$((n + 1))
    copy="$(python3 "$BRIEFS" brief --repo "$repo" --brief "$batch/$n" --file "$file" \
      --footer "$(brief_footer "$batch/$n")")" || {
        close_batch "$batch"
        refuse "could not copy task $file into batch $batch"
      }
    printf -v prompt 'Read task file %q and carry out its instructions.' "$copy"
    if [ -n "$follows" ]; then
      printf -v prompt 'Read instructions file %q, then task file %q and carry out the task.' "$follows" "$copy"
    fi
    error="$(dirname "$copy")/start.stderr"
    session="$(start_session "$role" "$host" "$model" "$effort" "$cwd" "$prompt" "$role ${batch##*-}-$n" 2>"$error")" || {
      cat "$error" >&2
      python3 "$BRIEFS" lost --repo "$repo" --brief "$batch/$n" --reason "Startup failed; inspect $error" || true
      close_batch "$batch" keep
      refuse "$RUNNER_NAME did not confirm startup of $role for brief $batch/$n; records were kept at $(dirname "$copy"). Inspect start.stderr and any recovery identity before brief close; no retry or alternate runner was used"
    }
    rm -f "$error"
    if ! python3 "$BRIEFS" started --repo "$repo" --brief "$batch/$n" --runner "$RUNNER_NAME" \
      --session "$session" --host "$host" --model "$model" --effort "${effort:-—}"; then
      runner stop "$session" >/dev/null || refuse "could not record or stop $RUNNER_NAME session $session; batch $batch was kept. Stop the session before brief close"
      close_batch "$batch"
      refuse "could not record session $session for brief $batch/$n; the session was stopped"
    fi
    started+=("$batch/$n"$'\t'"$session")
  done
  printf '%s\n' "${started[@]}"
  echo "dispatch: brief batch $batch: ${#files[@]} sessions on $RUNNER_NAME; relay notifies $parent_runner session $parent_session when every answer is reported or lost" >&2
}

notification_command() {
  local action="$1" repo identity name session
  shift
  repo="$(repo_slug)" || return 2
  export GH_REPO="$repo"
  identity="$(own_session)" || return 2
  name="${identity%%$'\t'*}"
  session="${identity#*$'\t'}"
  case "$action" in
    ack)
      if [ "$1" = brief ]; then
        python3 "$RELAY" ack --repo "$repo" --runner "$name" --session "$session" --batch "$2"
      else
        python3 "$RELAY" ack --repo "$repo" --runner "$name" --session "$session" --ticket "${1#\#}" --event "$2"
      fi ;;
    queue) python3 "$RELAY" queue --repo "$repo" --runner "$name" --session "$session" ;;
    wait-wake) runner_call "$name" await-wake --repo "$repo" --session "$session" ;;
  esac
}

report_brief() {
  local repo parent
  repo="$(repo_slug)" || return 2
  parent="$(own_session)" || return 2
  python3 "$BRIEFS" report --repo "$repo" --brief "$1" --file "$2" \
    --runner "${parent%%$'\t'*}" --session "${parent#*$'\t'}"
}

session_command() {
  local action="$1" brief="$2" repo entry state name session
  repo="$(repo_slug)" || return 2
  entry="$(python3 "$BRIEFS" session --repo "$repo" --brief "$brief")" || return 2
  IFS=$'\t' read -r state name session <<<"$entry"
  [ "$session" != - ] && [ -n "$session" ] || refuse "brief $brief has no recorded session"
  if [ "$action" = resume ]; then
    [ "$state" = open ] || refuse "brief $brief is $state; only an open session accepts a continuation"
    runner_call "$name" send "$session" "$3"
  else
    runner_call "$name" stop "$session" || return 2
    python3 "$BRIEFS" lost --repo "$repo" --brief "$brief" --reason 'Stopped by caller' || return 2
  fi
}

ensure_board() {
  local repository port
  git rev-parse --show-toplevel >/dev/null 2>&1 || { echo 'dispatch: board needs a Git worktree' >&2; return 2; }
  repository="$(main_checkout)"
  [ -n "$repository" ] || return 2
  [ -f "$BOARD_SUPERVISOR" ] || { echo "dispatch: no board supervisor at $BOARD_SUPERVISOR" >&2; return 2; }
  port="$(env -u GH_REPO python3 "$BOARD_SUPERVISOR" --ensure "$repository")" || return 2
  case "$port" in ''|*[!0-9]*) echo 'dispatch: board supervisor returned no port' >&2; return 2 ;; esac
  printf 'http://127.0.0.1:%s\n' "$port"
}

open_board() {
  local url
  case "$#:${1:-}" in 0:|1:--url) ;; *) usage ;; esac
  url="$(ensure_board)" || return 2
  printf '%s\n' "$url"
  [ "${1:-}" != --url ] || return 0
  python3 - "$url" <<'PYBROWSER'
import sys,webbrowser
try:
    opened=webbrowser.open(sys.argv[1],new=2)
except (webbrowser.Error,OSError) as exc:
    print(f'dispatch: board is running at {sys.argv[1]}, but the browser could not open: {exc}',file=sys.stderr)
    raise SystemExit(2)
if not opened:
    print(f'dispatch: board is running at {sys.argv[1]}; open that URL or use board --url',file=sys.stderr)
    raise SystemExit(2)
PYBROWSER
}

source "$SKILL_ROOT/scripts/dispatch-worktrees.sh"
source "$SKILL_ROOT/scripts/dispatch-git.sh"
source "$SKILL_ROOT/scripts/dispatch-finish.sh"
source "$SKILL_ROOT/scripts/dispatch-ticket.sh"

case "${1:-}" in
  open|open-ticket|start|advance|integrate|integrated|retract|wait|status|findings|summary|finish|suspend|route)
    [[ "${2:-}" =~ ^[1-9][0-9]*$ ]] || refuse 'a positive issue number is required' ;;
  land)
    for number in "${@:2}"; do [[ "$number" =~ ^[1-9][0-9]*$ ]] || refuse 'land requires positive ticket numbers'; done ;;
esac

case "${1:-}" in
  self|brief|report|send|resume|stop|ack|queue|wait-wake|watchdog|board) ;;
  *) repo="$(repo_slug)" || exit 2; export GH_REPO="$repo" ;;
esac

case "${1:-}" in
  board) shift; open_board "$@" ;;
  open) [ "$#" -ge 2 ] || usage; shift; open_night "$@" ;;
  open-ticket) [ "$#" -ge 2 ] || usage; shift; open_ticket "$@" ;;
  start) [ "$#" -ge 3 ] || usage; shift; start_one "$@" ;;
  advance) [ "$#" -eq 2 ] || usage; export MMW_DISPATCH_ADVANCE=1; advance "$2" ;;
  integrate) [ "$#" -eq 2 ] || usage; integrate_ticket "$2" ;;
  integrated) [ "$#" -eq 2 ] || usage; integrated_since_start "$2" ;;
  land) [ "$#" -ge 2 ] || usage; shift; land_tickets "$@" ;;
  retract) [ "$#" -eq 2 ] || usage; retract_one "$2" ;;
  wait) [ "$#" -eq 3 ] || usage; wait_one "$2" "$3" ;;
  status) [ "$#" -eq 2 ] || usage; python3 "$STATUS" --table "$2" && night_orchestrator_line "$2" ;;
  findings) [ "$#" -eq 2 ] || usage; python3 "$STATUS" --findings "$2" ;;
  summary) [ "$#" -eq 2 ] || usage; summary_spec "$2" ;;
  finish) [ "$#" -eq 2 ] || usage; finish_spec "$2" ;;
  suspend) [ "$#" -eq 2 ] || usage; suspend_night "$2" ;;
  pr) shift; python3 "$PR" "$@" ;;
  route) [ "$#" -ge 4 ] || usage; number="$2"; child="$3"; resolution="$4"; shift 4; python3 "$VERIFY" "$number" --route "$child" "$resolution" "$@" ;;
  send)
    shift
    case "${1:-}" in
      worker|reviewer) repo="$(repo_slug)" || exit 2; export GH_REPO="$repo"; send_ticket "$@" ;;
      *) send_many "$@" ;;
    esac ;;
  report) [ "$#" -eq 3 ] || usage; report_brief "$2" "$3" ;;
  brief)
    [ "$#" -eq 3 ] || usage
    case "$2" in
      show) repo="$(repo_slug)" && python3 "$BRIEFS" show --repo "$repo" --batch "$3" ;;
      close) close_batch "$3" ;;
      *) usage ;;
    esac ;;
  resume)
    [ "$#" -eq 3 ] || usage
    case "$2" in */*) session_command resume "$2" "$3" ;; *) repo="$(repo_slug)" || exit 2; export GH_REPO="$repo"; resume_one "$2" "$3" ;; esac ;;
  stop) [ "$#" -eq 2 ] || usage; session_command stop "$2" ;;
  ack) [ "$#" -eq 3 ] || usage; notification_command ack "$2" "$3" ;;
  queue|wait-wake) [ "$#" -eq 1 ] || usage; notification_command "$1" ;;
  watchdog)
    [ "$#" -eq 2 ] || usage
    case "$2" in arm|status) repo="$(repo_slug)" && python3 "$WATCHDOG" "$2" --repo "$repo" ;; *) usage ;; esac ;;
  self) [ "$#" -eq 1 ] || usage; own_session ;;
  *) usage ;;
esac
