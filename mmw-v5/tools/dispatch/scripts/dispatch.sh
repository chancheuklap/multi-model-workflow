#!/usr/bin/env bash
# Session dispatch for caller-supplied task files. Results are local brief records;
# notifications and ticket/Git operations are separate capabilities.
# Exit 0: completed the requested operation. Exit 2: refused, with a reason on stderr.
# Resume preserves adapter receipts: 3 means retryable; 4 means delivery is unconfirmed
# and must not be repeated.
set -uo pipefail

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS_PY="$SKILL_ROOT/scripts/models.py"
BRIEFS="$SKILL_ROOT/scripts/briefs.py"
TRACKER="$SKILL_ROOT/scripts/tracker.py"
MMW_HOME="$(python3 -c 'import os; from pathlib import Path; print(Path(os.environ.get("MMW_HOME") or "~/.mmw-v5").expanduser().resolve())')" || exit 2
export MMW_HOME
MODELS_JSON="$MMW_HOME/models.json"
RUNNER=""
RUNNER_NAME=""

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh send <role> [--cwd DIR] [--follow FILE] <task file>...
       dispatch.sh report <batch>/<n> <answer file>
       dispatch.sh brief show|close <batch>
       dispatch.sh resume <batch>/<n> <message>
       dispatch.sh stop <batch>/<n>
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
  [ -f "$RUNNER" ] || refuse "no runner adapter for $1 at $RUNNER; choose a runner with models.py config set runner <name>"
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

brief_footer() {
  local brief="$1" command
  printf -v command 'MMW_HOME=%q bash %q report %q <answer-file>' "$MMW_HOME" "$SELF" "$brief"
  printf '%s\n' '---' "Result destination for brief $brief:" \
    'Write your answer to a UTF-8 file and replace <answer-file> with its path in this command:' \
    "$command"
}

start_session() {
  local host="$1" model="$2" effort="$3" cwd="$4" prompt="$5" title="$6" session
  session="$(runner start --host "$host" --model "$model" --effort "$effort" \
    --cwd "$cwd" --prompt "$prompt" --skip-approval --title "$title" \
    --env "GH_REPO=$GH_REPO" --env "MMW_HOME=$MMW_HOME" --env "MMW_RUNNER=$RUNNER_NAME")" \
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
    session="$(start_session "$host" "$model" "$effort" "$cwd" "$prompt" "$role ${batch##*-}-$n" 2>"$error")" || {
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
  echo "dispatch: brief batch $batch: ${#files[@]} sessions on $RUNNER_NAME; read answers with dispatch.sh brief show $batch. Notifications are not enabled by this command yet" >&2
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

case "${1:-}" in
  send) shift; send_many "$@" ;;
  report) [ "$#" -eq 3 ] || usage; report_brief "$2" "$3" ;;
  brief)
    [ "$#" -eq 3 ] || usage
    case "$2" in
      show) repo="$(repo_slug)" && python3 "$BRIEFS" show --repo "$repo" --batch "$3" ;;
      close) close_batch "$3" ;;
      *) usage ;;
    esac ;;
  resume) [ "$#" -eq 3 ] || usage; session_command resume "$2" "$3" ;;
  stop) [ "$#" -eq 2 ] || usage; session_command stop "$2" ;;
  self) [ "$#" -eq 1 ] || usage; own_session ;;
  *) usage ;;
esac
