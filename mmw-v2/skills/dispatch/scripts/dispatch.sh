#!/usr/bin/env bash
#
# Start an agent on a ticket, move a spec's batch forward, or report on one.
#
#   dispatch.sh check <spec>
#   dispatch.sh open <spec>
#   dispatch.sh open-ticket <n>
#   dispatch.sh board
#   dispatch.sh adopt <n>
#   dispatch.sh self
#   dispatch.sh advance <spec>
#   dispatch.sh integrate <n>
#   dispatch.sh land <n>
#   dispatch.sh start <n> worker|reviewer|verifier
#   dispatch.sh retract <n>
#   dispatch.sh wait <n> worker|reviewer|verifier
#   dispatch.sh ack <n> <event> | relay.recovered
#   dispatch.sh resume <n> "<text>"
#   dispatch.sh status <spec>
#   dispatch.sh reverify <spec>
#   dispatch.sh summary <spec>
#   dispatch.sh finish <spec>
#   dispatch.sh suspend <spec>
#   dispatch.sh route <ticket> <child> fixed|stale|became-ticket [<new ticket>]
#
# Every script this one calls is found by resolution, from this file's own path:
# `lease.py` of the drive-target skill, and `verify-ticket.py` and `events.py` of the
# verify-ticket skill, are in the `scripts/` of their own skills one directory over. One
# file belongs to the toolbox itself, not to any skill, and is taken from the toolbox
# root (this skill directory two levels up): `install.sh`. `--tools <directory>` is an
# override, repeatable: a directory given that way is searched before the resolved
# location.
#
# Everything this script writes on a ticket is an event (`events.py`): a comment whose
# first line is for a person and whose trailing `<!-- mmw {...} -->` block is what every
# program reads. Everything it reads off a ticket is the fold of those events.
#
# The ticket number and the kind of agent are the whole input for `start`. Which
# of the worker rows a worker session starts from is the ticket's own `*-worker`
# label, so one ticket keeps the same worker every time it is started. Which
# host, model and thinking level the session gets come from that
# row of models.json under MMW_HOME, resolved against the catalog of the runner
# that starts it (`use_catalog_of`). Tonight's runner is `models.py runner`: MMW_RUNNER,
# then models.json, then, when its runner is auto, the runner this process runs in, then orca.
# `start` has that runner's adapter (scripts/runners/<runner>.sh) start the
# session, writes a `worker.started`, `reviewer.started` or `verifier.started` event
# on the ticket — session, runner, host, model, effort, grade, the worktree's absolute
# path, branch and base commit — and prints the session id. A worker takes no product
# slot here: the first run of its criteria that needs the product claims one
# (`verify-ticket.py`), and the worktree keeps it until the ticket lands. A start the
# adapter refuses is refused once: no retry, no other host, no other runner. A worker
# started on a ticket whose events still show a live worker replaces that one: the old
# session is stopped through its own runner and a `worker.replaced` naming it goes on
# the ticket before the new `worker.started`. A worker started in a standing worktree
# that an earlier worker of the ticket left with uncommitted edits first commits them on
# the ticket branch (`keep_unfinished_work`). `resume`, `retract`, `land` and `suspend`
# find the session in those events and ask the runner the event names; `wait` only reads
# the ticket.
#
# Nothing here tells anyone that a result landed. `relay.py`, beside this script, watches
# the board and wakes the session waiting on each result event through that session's
# runner's `send`. `open` (a night) and `open-ticket` (one ticket outside a night) open a
# watch on the relay whose main agent is the calling session — the runner and session its
# adapter's `self` reads — and start the relay when none runs; `summary` and `suspend`, or
# `land` for one ticket, close that watch, and the relay ends with its last. `start` and `advance`
# refuse a ticket no running relay watches, since its result would wake nobody. `ack` is
# how a woken session says it handled the wake it read. `adopt` makes a session that
# picked a ticket up itself that ticket's worker, as `start` would have. `self` prints the
# runner and session this process runs in.
#
# Each command's exit codes are written beside that command, in the door that carries it;
# SKILL.md next to this script is the index of doors.

set -uo pipefail

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS_JSON="${MMW_HOME:-$HOME/.mmw}/models.json"
STATUS="$SKILL_ROOT/scripts/status.py"
RELAY="$SKILL_ROOT/scripts/relay.py"
STATEDIR="$SKILL_ROOT/scripts/statedir.py"
RUNNER=""
RUNNER_NAME=""
REPO_URL=""
# The skill lives under mmw-v2/skills/<name> of the toolbox checkout, so `install.sh`
# is two directories up, and `verify-ticket.py` and `lease.py` are in the `scripts/` of
# their own skills one directory over. A `--tools` directory given on the command line
# is searched before those.
INSTALLER="$(dirname "$(dirname "$SKILL_ROOT")")/install.sh"
BOARD_SUPERVISOR="$(dirname "$(dirname "$SKILL_ROOT")")/board/supervisor.py"
BOARD_SERVER="$(dirname "$(dirname "$SKILL_ROOT")")/board/server.py"
# `models.py` reads models.json, so it belongs to this skill and travels with it.
MODELS_PY="$SKILL_ROOT/scripts/models.py"
VERIFY=""
LEASE=""

# The row a ticket with no `*-worker` label starts from.
DEFAULT_WORKER=junior-worker

MERGE_TRIES=3                # a worker's commit in its worktree can hold the .git lock while advance merges

AUTONOMOUS="You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work."
PIPELINE_FAULT="A fault in the pipeline itself is reported, not worked around: verify-ticket.py <n> --sub-issue fault <file>, then stop (rule 5 of that section)."
PRODUCT_RULES="Several tickets run on this machine at once. Before you start, reach or stop the product, read 'Five rules while the product is running' in the drive-target skill."

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into
# --json output under it, which no JSON reader can parse.
gh_() {
  env -u CLICOLOR_FORCE -u CLICOLOR gh "$@"
}

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

runner() {
  bash "$RUNNER" "$@"
}

# Invoke a named adapter without changing the adapter selected for the surrounding
# command. `check` uses this for Paseo-only provider diagnostics.
runner_call() {
  local name="$1"
  shift
  bash "$SKILL_ROOT/scripts/runners/$name.sh" "$@"
}

# Called once at the top of every command that talks to the runner, before any `$(…)`.
# The check cannot live in `runner()`: its callers run it inside `$(…)`, and a `refuse`
# there ends only that subshell — the command then carries on with an empty answer. With
# the adapter file gone that made `retract` archive a running worker's workspace and
# exit 0.
require_runner() {
  [ -f "$RUNNER" ] || refuse "no runner adapter for ${RUNNER_NAME:-this runner} at ${RUNNER:-scripts/runners/}; name paseo, orca or herdr in MMW_RUNNER or models.json, or restore that file, then run the command again"
}

# Points `runner` at one adapter. The name comes from `models.py runner` for a start,
# and from the session's `*.started` event on the ticket for everything after it.
use_runner() {
  RUNNER_NAME="$1"
  RUNNER="$SKILL_ROOT/scripts/runners/$1.sh"
  require_runner
}

tonight_runner() {
  local name
  name="$(python3 "$MODELS_PY" runner)" && [ -n "$name" ] \
    || refuse "could not tell tonight's runner from MMW_RUNNER, $MODELS_JSON or this process"
  printf '%s\n' "$name"
}

# Which catalog `models.py` resolves a models.json row against: the runner that starts the
# session decides. Paseo is handed Paseo's own provider model ids; a runner that runs the
# host's CLI in a terminal (Orca, Herdr) is handed the CLI's own ids, so its row is
# resolved against the CLI's catalog. Resolving against another runner's catalog either
# fails outright (Paseo's daemon is
# not running) or names a model the CLI does not have.
use_catalog_of() {
  case "$1" in
    paseo) export MMW_CATALOG_MODE=paseo ;;
    *) export MMW_CATALOG_MODE=cli ;;
  esac
}

# The ticket's comments as the tracker answers them. Exit non-zero, with the reason on
# stderr, when it could not be asked: an unanswered read is not a ticket with no events.
ticket_comments() {
  gh_ issue view "$1" --json comments 2>/dev/null \
    || { echo "dispatch: could not read the comments of #$1 from the tracker" >&2; return 2; }
}

# Asks `events.py` one question about the ticket's events: `session [--kind K]`,
# `sessions`, or `result --kind K`. A comment whose event cannot be read is named on
# stderr, and the answer is what the readable events say.
ticket_events() {
  local number="$1" json
  shift
  json="$(ticket_comments "$number")" || return 2
  printf '%s' "$json" | python3 "$EVENTS" "$@" "$number" --comments-file -
}

# Prints "runner<TAB>session" of the newest session of this kind started on the ticket
# (any kind when none is given), and nothing when there is none.
session_on_ticket() {
  local number="$1" kind="${2:-}"
  if [ -n "$kind" ]; then
    ticket_events "$number" session --kind "$kind"
  else
    ticket_events "$number" session
  fi
}

# Every session the ticket's events name, one "runner<TAB>session" per line.
sessions_on_ticket() {
  ticket_events "$1" sessions
}

# Every worker session whose hold no event on the ticket has ended, one
# "runner<TAB>session" per line, oldest first.
live_workers_on_ticket() {
  ticket_events "$1" live --kind worker
}

# Who left the uncommitted edits a ticket's standing worktree may hold: its newest worker
# session, as "worker <session> on <runner>, left when …" — the event that ended its hold,
# or that it was replaced (a replacement stops a live one just before). Nothing when no
# worker was ever started on the ticket; non-zero when its events could not be read.
last_worker_on_ticket() {
  ticket_events "$1" fold | python3 -c '
import json, sys
state = json.load(sys.stdin)
workers = [r for r in state.get("sessions") or [] if r.get("kind") == "worker"]
if not workers:
    raise SystemExit(0)
last = workers[-1]
how = ("it was replaced" if last.get("live")
       else "its hold ended with " + str(last.get("ended_by") or "an event"))
print("worker %s on %s, left when %s" % (last.get("session"), last.get("runner"), how))
'
}

# The value of one field on the newest named event. When several event names are given,
# the first is the active state and any later one ends it. Exit 0 prints the value, 3
# means no active event, 4 means its field is absent, and 2 means the comments cannot be
# read.
newest_field() {
  local number="$1" field="$2" json
  shift 2
  json="$(ticket_comments "$number")" || return 2
  printf '%s' "$json" | MMW_EVENT_NAMES="$*" MMW_FIELD="$field" MMW_N="$number" \
    python3 -c '
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("mmw_events", os.environ["MMW_EVENTS_PY"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    comments = mod.read_comments(None, "-")
except mod.Unreadable as exc:
    print("dispatch: " + str(exc), file=sys.stderr)
    raise SystemExit(2)
state = mod.fold(comments)
if mod.refuse_unreadable(state, int(os.environ["MMW_N"])):
    raise SystemExit(2)
names = os.environ["MMW_EVENT_NAMES"].split()
record = mod.newest(comments, *names)
if record is None or (len(names) > 1 and record["event"] != names[0]):
    raise SystemExit(3)
value = record["payload"].get(os.environ["MMW_FIELD"])
if value in (None, ""):
    raise SystemExit(4)
print(value)
'
}

# Read a field from the newest worker.started while preserving "there is no event" as
# exit 3 for callers that have another source. Every other failure is explained here.
newest_worker_field() {
  local number="$1" field="$2" value rc
  value="$(newest_field "$number" "$field" worker.started)"
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$value" ;;
    2) echo "dispatch: could not read #$number's events, so its $field is unknown" >&2; return 2 ;;
    3) return 3 ;;
    4) echo "dispatch: #$number's latest worker.started carries no $field; re-start the worker so it is recorded" >&2; return 2 ;;
    *) echo "dispatch: could not resolve #$number's $field from its worker.started event" >&2; return 2 ;;
  esac
}

base_commit() {
  git -C "$1" merge-base "origin/$2" "$3" 2>/dev/null
}

# Resolve worker.started.into first, then an open night's spec.opened.into, then the
# caller's explicit fallback. `start` supplies its current branch as that fallback;
# `adopt` supplies only --into. A worker.started with no into is refused; a new start
# records the base branch.
resolve_into() {
  local number="$1" spec="$2" fallback="$3" into rc
  into="$(newest_worker_field "$number" into)"
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$into"; return 0 ;;
    2) return 2 ;;
    3) ;;
  esac
  if [ -n "$spec" ]; then
    into="$(newest_field "$spec" into spec.opened spec.suspended spec.closed)"
    rc=$?
    case "$rc" in
      0) printf '%s\n' "$into"; return 0 ;;
      2) echo "dispatch: could not read whether the night on #$spec is open, so #$number's base branch is unknown" >&2; return 2 ;;
      4) echo "dispatch: the open night on #$spec carries no spec.opened.into; open it again so the base branch is recorded" >&2; return 2 ;;
      3) ;;
      *) echo "dispatch: could not resolve #$number's base branch from the night on #$spec" >&2; return 2 ;;
    esac
  fi
  [ -n "$fallback" ] || {
    echo "dispatch: #$number has no worker.started.into and is outside an open night; pass --into <base branch>" >&2
    return 2
  }
  printf '%s\n' "$fallback"
}

# The spec ticket <n> sits under — the parent link the tracker records — for the `spec`
# field of the events written on it. MMW_SPEC answers first when the caller set it (a
# batch command knows its spec). Prints nothing when the tracker records no parent or
# could not be asked: the event is written either way, and the field is left empty.
ticket_spec() {
  local found
  if [ -n "${MMW_SPEC:-}" ]; then
    printf '%s\n' "$MMW_SPEC"
    return 0
  fi
  found="$(gh_ issue view "$1" --json parent --jq '.parent.number // empty' 2>/dev/null | head -n 1)"
  case "$found" in "" | *[!0-9]*) return 0 ;; esac
  printf '%s\n' "$found"
}

# Post one event on issue <issue>. Everything after the issue number is `events.py
# emit`'s own arguments. Exit 0 posted, 1 the tracker did not take it, 2 the event could
# not be built (the reason is on stderr).
# This machine's hostname, as `socket.gethostname()` reads it — the same call the watchdog
# makes, so a session started here is asked about only from here.
machine_name() {
  python3 -c 'import socket; print(socket.gethostname())'
}

post_event() {
  local issue="$1" body
  shift
  body="$(python3 "$EVENTS" emit "$@")" || return 2
  gh_ issue comment "$issue" --body "$body" >/dev/null 2>&1 || return 1
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh check <spec>
       dispatch.sh open <spec>
       dispatch.sh open-ticket <n>
       dispatch.sh board
       dispatch.sh adopt <n> [--into <branch>]
       dispatch.sh self
       dispatch.sh advance <spec>
       dispatch.sh integrate <n>
       dispatch.sh land <n>
       dispatch.sh start <n> worker|reviewer|verifier
       dispatch.sh retract <n>
       dispatch.sh wait <n> worker|reviewer|verifier
       dispatch.sh ack <n> <event> | relay.recovered
       dispatch.sh resume <n> "<text>"
       dispatch.sh status <spec>
       dispatch.sh reverify <spec>
       dispatch.sh summary <spec>
       dispatch.sh finish <spec>
       dispatch.sh suspend <spec>
       dispatch.sh route <ticket> <child> fixed|stale|became-ticket [<new ticket>]
USAGE
  exit 2
}

# ------------------------------------------------------------------ task board

board_port_answers() {
  MMW_BOARD_PORT="$1" python3 -c '
import os, socket
try:
    with socket.create_connection(("127.0.0.1", int(os.environ["MMW_BOARD_PORT"])), timeout=0.2):
        pass
except OSError:
    raise SystemExit(1)
'
}

start_board_process() {
  local repository="$1" port="$2" log
  log="${MMW_HOME:-$HOME/.mmw}/board-$port.log"
  MMW_BOARD_CWD="$repository" MMW_BOARD_PORT="$port" MMW_BOARD_SERVER="$BOARD_SERVER" \
    MMW_BOARD_LOG="$log" python3 -c '
import os, subprocess, sys
log = open(os.environ["MMW_BOARD_LOG"], "ab", buffering=0)
subprocess.Popen(
    [sys.executable, "-u", os.environ["MMW_BOARD_SERVER"], "--port", os.environ["MMW_BOARD_PORT"]],
    cwd=os.environ["MMW_BOARD_CWD"], stdin=subprocess.DEVNULL, stdout=log,
    stderr=subprocess.STDOUT, start_new_session=True,
)
'
}

open_board() {
  [ -f "$BOARD_SUPERVISOR" ] || refuse "no task board supervisor at $BOARD_SUPERVISOR"
  [ -f "$BOARD_SERVER" ] || refuse "no task board server at $BOARD_SERVER"
  local repository current port url answer rc
  repository="$(main_checkout)"
  [ -n "$repository" ] || refuse "not inside a git repository, so there is no main checkout to register"
  repository="$(CDPATH='' cd -- "$repository" && pwd -P)"
  current="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$current" ] || refuse "not inside a git repository, so there is no workspace for the task board tab"
  current="$(CDPATH='' cd -- "$current" && pwd -P)"
  port="$(python3 "$BOARD_SUPERVISOR" --register "$repository")" \
    || refuse "could not register $repository in ${MMW_HOME:-$HOME/.mmw}/boards.json"
  if ! board_port_answers "$port"; then
    start_board_process "$repository" "$port" \
      || refuse "could not start the task board for $repository on 127.0.0.1:$port"
  fi
  local attempt
  for attempt in {1..100}; do
    board_port_answers "$port" && break
    sleep 0.1
  done
  board_port_answers "$port" \
    || refuse "the task board for $repository did not answer on 127.0.0.1:$port after 10 seconds; see ${MMW_HOME:-$HOME/.mmw}/board-$port.log"
  url="http://127.0.0.1:$port"
  use_runner "$(tonight_runner)"
  answer="$(runner open-url --cwd "$current" --url "$url" 2>&1)"
  rc=$?
  case "$rc" in
    0) return 0 ;;
    2) printf '%s\n' "$url"; return 0 ;;
    *) refuse "$RUNNER_NAME could not open $url in $current: ${answer:-the adapter gave no reason}" ;;
  esac
}

# ------------------------------------------------------------------ the relay
#
# Wake-ups come from the board, never from here: `relay.py` reads the tickets' events and
# hands each result to the session waiting on it through that session's runner's `send`.
# What these helpers do is open and close a watch — a night, or tickets outside one — with
# this session as its main agent, and ask whether the relay watches a ticket. One relay
# process serves every watch of the repository: it starts with the first and ends with the
# last.

# This repository as `gh` names it, owner/name: the relay keeps one state directory per
# repository. Exit 2, with the reason on stderr, when the tracker cannot say.
repo_slug() {
  local slug
  slug="$(gh_ repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null | tr -d '[:space:]')"
  if [ -z "$slug" ]; then
    echo "dispatch: the tracker could not say which repository this checkout is (gh repo view), so the relay's state for it cannot be found" >&2
    return 2
  fi
  printf '%s\n' "$slug"
}

# The runner and session this process itself runs in, "runner<TAB>session", as that
# runner's adapter reads it (`self`). The innermost runner is asked first: an agent Paseo
# runs can sit in a terminal of Herdr or Orca, and Herdr can run inside an Orca terminal;
# a wake sent to the outer one would be typed into whatever that terminal shows. Exit 2,
# with the reason on stderr, when no adapter sees this process, or one sees it and cannot
# read its id: then nothing can be sent to it.
OWN_RUNNERS="paseo herdr orca"
own_session() {
  local name adapter out err rc asked=""
  err="$(mktemp)"
  for name in $OWN_RUNNERS; do
    adapter="$SKILL_ROOT/scripts/runners/$name.sh"
    [ -f "$adapter" ] || continue
    asked="$asked $name"
    out="$(bash "$adapter" self 2>"$err")"
    rc=$?
    case "$rc" in
      0)
        rm -f "$err"
        printf '%s\t%s\n' "$name" "$out"
        return 0
        ;;
      3) ;;
      *)
        echo "dispatch: this session cannot be named to the relay, so no wake could reach it: $(tr '\n' ' ' < "$err")" >&2
        rm -f "$err"
        return 2
        ;;
    esac
  done
  rm -f "$err"
  echo "dispatch: this session runs in no runner whose adapter can name it (asked:${asked:- none}), so no wake could reach it; run it inside a session of one of them" >&2
  return 2
}

# Exit 0 when a running relay sees ticket <n>'s events — a watch of the ticket's spec, or of
# the ticket — or, with no ticket, when it watches <spec>. Otherwise the reason on stderr.
relay_watches() {
  local number="$1" spec="$2" repo
  repo="$(repo_slug)" || return 2
  local -a which=()
  [ -z "$number" ] || which+=(--ticket "$number")
  [ -z "$spec" ] || which+=(--spec "$spec")
  python3 "$RELAY" watching --repo "$repo" "${which[@]}" >/dev/null
}

# Close the watch the arguments name (`--spec N` or `--tickets N`); the relay process ends
# with its last watch. Exit 0 closed, or nothing was watched; 3 that watch is not open, and
# the relay's other watches were left alone; 1 the relay did not end, the reason on stderr.
stop_relay() {
  local repo out rc
  repo="$(repo_slug)" || return 1
  out="$(python3 "$RELAY" stop --repo "$repo" "$@" 2>&1)"
  rc=$?
  case "$rc" in
    0)
      case "$out" in stopped*) echo "dispatch: $out" >&2 ;; esac
      return 0
      ;;
    3) return 3 ;;
  esac
  echo "dispatch: ${out#relay: }" >&2
  return 1
}

# Open the watch the arguments name (`--spec N` or `--tickets N`) with this session as its
# main agent, and make sure the relay runs. One call to `relay.py start`, which checks
# everything before it writes anything: a refused watch leaves every open watch, and its
# main agent, as it was. Prints "runner<TAB>session<TAB>started|running": `started` when
# this call opened the watch, `running` when it was open already and this session is now
# its main agent. Exit 2 with the reason on stderr.
open_relay() {
  local repo line runner session out
  repo="$(repo_slug)" || return 2
  line="$(own_session)" || return 2
  runner="${line%%$'\t'*}"
  session="${line#*$'\t'}"
  out="$(python3 "$RELAY" start --repo "$repo" "$@" --runner "$runner" --session "$session")" \
    || { echo "dispatch: the relay did not open the watch for $runner session $session (the reason is above), so nothing was opened" >&2; return 2; }
  printf '%s\n' "$out" | sed 's/^/dispatch: /' >&2
  case "$out" in
    "opened "*) printf '%s\t%s\tstarted\n' "$runner" "$session" ;;
    *) printf '%s\t%s\trunning\n' "$runner" "$session" ;;
  esac
}

# The repository's default branch, as origin advertises it. A local origin/HEAD is used
# when fetch has established one; a bare test origin and a newly-added remote may only
# answer through ls-remote.
default_branch() {
  local root="$1" ref
  ref="$(git -C "$root" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)" \
    && { printf '%s\n' "${ref#origin/}"; return 0; }
  ref="$(git -C "$root" ls-remote --symref origin HEAD 2>/dev/null \
    | awk '$1 == "ref:" { sub("refs/heads/", "", $2); print $2; exit }')"
  [ -n "$ref" ] || return 1
  printf '%s\n' "$ref"
}

project_remedy() {
  printf 'git config branch.%s.vscode-merge-base <project branch>' "$1"
}

# Print "project<TAB>source". The recorded event wins; otherwise the three sources are
# tried in the order fixed by #337 section 13.
project_for_night() {
  local root="$1" spec="$2" into="$3" project configured
  project="$(newest_field "$spec" project spec.opened 2>/dev/null)" || project=""
  if [ -n "$project" ]; then
    printf '%s\tevent\n' "$project"
    return 0
  fi

  project="$(git -C "$root" reflog show --format='%gs' "refs/heads/$into" 2>/dev/null \
    | sed -n 's/^branch: Created from //p' | tail -1)"
  project="${project#origin/}"
  project="${project#refs/heads/}"
  if [ -n "$project" ] && [ "$project" != HEAD ] \
     && { git -C "$root" show-ref --verify --quiet "refs/heads/$project" \
          || git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$project"; }; then
    printf '%s\treflog\n' "$project"
    return 0
  fi

  configured="$(git -C "$root" config --get "branch.$into.vscode-merge-base" 2>/dev/null)" || configured=""
  configured="${configured#origin/}"
  if [ -n "$configured" ]; then
    printf '%s\tconfig\n' "$configured"
    return 0
  fi

  local candidate name merge_base distance best="" best_distance="" ties=""
  while IFS= read -r candidate; do
    name="${candidate#refs/remotes/origin/}"
    case "$name" in HEAD|"$into"|issue-*) continue ;; esac
    merge_base="$(git -C "$root" merge-base "refs/heads/$into" "$candidate" 2>/dev/null)" || continue
    distance="$(git -C "$root" rev-list --count "$merge_base..refs/heads/$into" 2>/dev/null)" || continue
    if [ -z "$best_distance" ] || [ "$distance" -lt "$best_distance" ]; then
      best="$name"; best_distance="$distance"; ties="$name"
    elif [ "$distance" -eq "$best_distance" ]; then
      ties="$ties $name"
    fi
  done < <(git -C "$root" for-each-ref --format='%(refname)' refs/remotes/origin/)
  if [ -z "$best" ]; then
    echo "dispatch: project branch for $into could not be inferred; run $(project_remedy "$into")" >&2
    return 2
  fi
  if [ "$(printf '%s\n' $ties | wc -l | tr -d ' ')" -gt 1 ]; then
    echo "dispatch: project branch history for $into is tied between $(printf '%s' "$ties" | sed 's/^ //; s/ /, /g'); run $(project_remedy "$into")" >&2
    return 2
  fi
  printf '%s\thistory\n' "$best"
}

branch_sync_counts() {
  local root="$1" branch="$2" base_ref="${3:-}" local_ref="refs/heads/$2" remote_ref="refs/remotes/origin/$2" ahead
  if ! git -C "$root" show-ref --verify --quiet "$local_ref"; then
    if git -C "$root" show-ref --verify --quiet "$remote_ref"; then
      printf '0\t0\tremote-only\n'
      return 0
    fi
    echo "dispatch: project branch $branch exists neither locally nor on origin; run $(project_remedy "$(current_branch "$root")")" >&2
    return 2
  fi
  if ! git -C "$root" show-ref --verify --quiet "$remote_ref"; then
    if [ -n "$base_ref" ] && git -C "$root" rev-parse --verify --quiet "$base_ref" >/dev/null; then
      ahead="$(git -C "$root" rev-list --count "$base_ref..$local_ref")"
    else
      ahead="$(git -C "$root" rev-list --count "$local_ref" --not --remotes=origin)"
    fi
    printf '%s\t0\tmissing\n' "$ahead"
    return 0
  fi
  printf '%s\t%s\tpresent\n' \
    "$(git -C "$root" rev-list --count "$remote_ref..$local_ref")" \
    "$(git -C "$root" rev-list --count "$local_ref..$remote_ref")"
}

inspect_open_branches() {
  local root="$1" spec="$2" into="$3" default project source line ahead behind presence branch base_ref
  default="$(default_branch "$root")" || { echo "dispatch: origin did not advertise a default branch" >&2; return 2; }
  [ "$into" != "$default" ] \
    || { echo "dispatch: $into is the repository default branch; open a base branch cut from a project branch; run $(project_remedy "$into")" >&2; return 2; }
  line="$(project_for_night "$root" "$spec" "$into")" || return 2
  IFS=$'\t' read -r project source <<<"$line"
  [ "$project" != "$default" ] \
    || { echo "dispatch: project branch for $into resolved to the repository default branch $default; run $(project_remedy "$into")" >&2; return 2; }
  for branch in "$project" "$into"; do
    base_ref=""
    if [ "$branch" = "$into" ]; then
      if git -C "$root" show-ref --verify --quiet "refs/heads/$project"; then
        base_ref="refs/heads/$project"
      else
        base_ref="refs/remotes/origin/$project"
      fi
    fi
    line="$(branch_sync_counts "$root" "$branch" "$base_ref")" || return 2
    IFS=$'\t' read -r ahead behind presence <<<"$line"
    if [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ]; then
      echo "dispatch: $branch has diverged from origin/$branch: local has $ahead commit(s), origin has $behind commit(s); nothing was pushed" >&2
      return 2
    fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$project" "$source" "$branch" "$ahead" "$presence" "$behind"
  done
}

push_open_branches() {
  local root="$1" rows="$2" branch ahead presence behind output
  while IFS=$'\t' read -r _ _ branch ahead presence behind; do
    [ -n "$branch" ] || continue
    [ "$presence" = remote-only ] && continue
    if [ "$presence" = missing ] || [ "$ahead" -gt 0 ]; then
      output="$(git -C "$root" push origin "refs/heads/$branch:refs/heads/$branch" 2>&1)" \
        || { echo "dispatch: could not fast-forward origin/$branch: $(printf '%s' "$output" | tail -2 | tr '\n' ' ')" >&2; return 2; }
      git -C "$root" fetch -q origin "$branch:refs/remotes/origin/$branch" 2>/dev/null || true
    fi
  done <<<"$rows"
}

check_open_pushes() {
  local root="$1" rows="$2" branch ahead presence behind source output failed=0
  while IFS=$'\t' read -r _ _ branch ahead presence behind; do
    [ -n "$branch" ] || continue
    if [ "$presence" = missing ] || [ "$ahead" -gt 0 ]; then
      source="refs/heads/$branch"
    else
      source="refs/remotes/origin/$branch"
    fi
    output="$(git -C "$root" push --dry-run origin "$source:refs/heads/$branch" 2>&1)" \
      || { echo "dispatch: dry-run fast-forward of $branch failed: $(printf '%s' "$output" | tr '\n' ' ')" >&2; failed=1; }
  done <<<"$rows"
  [ "$failed" -eq 0 ]
}

# `open <spec>`: the night begins. The relay watches the spec's tickets with this session
# as the night's main agent, and `spec.opened` on the spec records who is woken. A
# spec.opened that could not be written closes the watch this call opened: a night that
# says nowhere that it is open is not opened.
open_night() {
  local spec="$1" root into opened runner session how rows project
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so the night has no base branch"
  into="$(current_branch "$root")" \
    || refuse "the checkout has no branch to record as spec.opened.into"
  fetch_origin "$root" || exit 2
  rows="$(inspect_open_branches "$root" "$spec" "$into")" || exit 2
  project="$(printf '%s\n' "$rows" | head -1 | cut -f1)"
  push_open_branches "$root" "$rows" || exit 2
  opened="$(open_relay --spec "$spec")" || exit 2
  IFS=$'\t' read -r runner session how <<<"$opened"
  if ! post_event "$spec" spec.opened --spec "$spec" \
       --line "NIGHT OPENED #$spec: wake-ups go to the main agent, $runner session $session" \
       --field "runner=$runner" --field "session=$session" --field "into=$into" \
       --field "project=$project"; then
    [ "$how" = started ] && stop_relay --spec "$spec"
    refuse "could not write the spec.opened event on #$spec, so the night is not open$([ "$how" = started ] && echo " and the watch this opened was closed again"); run open again once the tracker takes comments"
  fi
  echo "opened #$spec: wake-ups go to $runner session $session"
}

# `open-ticket <n>`: one ticket outside a night. The relay watches that ticket with this
# session as its main agent; `land <n>` closes the watch.
open_ticket() {
  local number="$1" opened runner session how
  opened="$(open_relay --tickets "$number")" || exit 2
  IFS=$'\t' read -r runner session how <<<"$opened"
  echo "opened #$number: wake-ups go to $runner session $session"
}

# `ack <n> <event>` or `ack relay.recovered`: the wake this session read is handled, and
# the relay sends it no more. The session is named the way its adapter's `self` reads it.
ack_wake() {
  local repo line runner session
  repo="$(repo_slug)" || exit 2
  line="$(own_session)" || exit 2
  runner="${line%%$'\t'*}"
  session="${line#*$'\t'}"
  if [ "$#" -eq 1 ]; then
    python3 "$RELAY" ack --repo "$repo" --runner "$runner" --session "$session" --event "$1" || exit 2
  else
    python3 "$RELAY" ack --repo "$repo" --runner "$runner" --session "$session" \
      --ticket "$1" --event "$2" || exit 2
  fi
}

# `adopt <n>`: the calling session becomes ticket <n>'s worker. A session that picked the
# ticket up itself was started by no `start`, so no `worker.started` names it: its
# reviewer's report would wake nobody, and `start <n> reviewer` would refuse. This writes
# that event with the session's own runner and session (its adapter's `self`) and the
# facts `start` writes — the grade's models.json row, this worktree, its branch and base,
# and no slot, which the first run of its criteria that runs the product claims — and makes sure a relay watches the ticket: the
# watch already covering it, or a watch of this ticket alone with this session as its main
# agent. Run it from the ticket's worktree, on branch issue-<n>, before claiming.
adopt_ticket() {
  local number="$1" explicit_into="${2:-}" line runner session
  line="$(own_session)" || exit 2
  runner="${line%%$'\t'*}"
  session="${line#*$'\t'}"

  local answer grades title spec
  answer="$(read_ticket "$number")"
  case "$answer" in
    "REFUSE "*) refuse "${answer#REFUSE }" ;;
    "") refuse "the tracker did not answer with a readable ticket #$number" ;;
  esac
  { IFS= read -r grades; IFS= read -r title; IFS= read -r spec; } <<<"$answer"

  local tree branch
  tree="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$tree" ] || refuse "not inside a git repository, so there is no worktree to adopt #$number in"
  tree="$(CDPATH='' cd -- "$tree" && pwd -P)"
  branch="$(git -C "$tree" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  [ "$branch" = "issue-$number" ] \
    || refuse "this worktree is on ${branch:-a detached HEAD}, and #$number is worked on branch issue-$number; adopt it from a worktree on issue-$number, where its preflight will claim it"

  # The event log is authoritative for the base branch. Outside a night, a
  # self-picked ticket with no prior start has no such event and must name --into.
  local base into
  into="$(resolve_into "$number" "$spec" "$explicit_into")" || exit 2
  fetch_origin "$tree" || exit 2
  require_origin_branch "$tree" "$into" || exit 2
  base="$(newest_worker_field "$number" base)"
  case "$?" in
    0) ;;
    3) base="$(base_commit "$tree" "$into" HEAD)" ;;
    *) exit 2 ;;
  esac
  [ -n "$base" ] || refuse "issue-$number and origin/$into share no commit, so there is no base to review from"

  local -a marked
  local profile row host model effort
  read -r -a marked <<<"$grades"
  case "${#marked[@]}" in
    0) profile="$DEFAULT_WORKER" ;;
    1) profile="${marked[0]}" ;;
    *) refuse "#$number carries ${#marked[@]} worker labels (${marked[*]}), and it takes one" ;;
  esac
  use_catalog_of "$runner"
  row="$(row_for_role "$profile")" || exit 2
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS_JSON has none"
  IFS=$'\t' read -r host model effort <<<"$row"

  # A worker that is still live on the ticket is somebody else's hold; this is not how a
  # running worker is replaced. The same session adopting again only refreshes the event.
  local holders
  holders="$(ticket_events "$number" fold | python3 -c '
import json, sys
state = json.load(sys.stdin)
for r in state.get("sessions") or []:
    if r.get("kind") == "worker" and r.get("live"):
        print(str(r.get("runner")) + "\t" + str(r.get("session")))
')" || refuse "could not read #$number's events, so whether a worker already holds it is unknown; nothing was adopted"
  local who already=""
  while IFS= read -r who; do
    [ -n "$who" ] || continue
    if [ "$who" = "$runner"$'\t'"$session" ]; then
      already=1
      continue
    fi
    refuse "#$number is held by worker ${who#*$'\t'} on ${who%%$'\t'*}; retract that start once its session is gone, then adopt again"
  done <<<"$holders"

  # A relay has to see this ticket, or the reviewer's report lands and wakes nobody.
  local started=""
  if ! relay_watches "$number" "$spec" 2>/dev/null; then
    local opened
    opened="$(open_relay --tickets "$number")" \
      || refuse "no relay watches #$number and no watch could be opened for it (the reason is above), so nothing was adopted"
    case "$opened" in *$'\t'started) started=1 ;; esac
  fi

  if [ -n "$already" ]; then
    echo "dispatch: #$number's worker.started already names $runner session $session" >&2
    printf '%s\n' "$session"
    return 0
  fi
  if ! post_event "$number" worker.started --ticket "$number" --spec "$spec" \
       --line "worker adopted on $runner: session $session, $host $model ($effort)" \
       --field "session=$session" --field "runner=$runner" \
       --field "machine=$(machine_name)" \
       --field "host=$host" --field "model=$model" --field "effort=${effort:-—}" \
       --field "grade=$profile" --field "worktree=$tree" --field "branch=issue-$number" \
       --field "base=$base" --field "into=$into" --json-field adopted=true; then
    [ -n "$started" ] && stop_relay --tickets "$number"
    refuse "could not write the worker.started event on #$number, so this session is not its worker$([ -n "$started" ] && echo " and the watch this opened was closed again"); adopt again once the tracker takes comments"
  fi
  printf '%s\n' "$session"
}

# ------------------------------------------------------------------ local model configuration

# Prints "host<TAB>resolved-model<TAB>effort" for the agent asked for.
row_for_role() {
  [ -f "$MODELS_PY" ] || refuse "no models.py at $MODELS_PY"
  MMW_MODELS_PY="$MODELS_PY" MMW_AGENT="$1" python3 -c '
import importlib.util, os, sys
path = os.environ["MMW_MODELS_PY"]
spec = importlib.util.spec_from_file_location("mmw_models", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    print(mod.row_tsv(os.environ["MMW_AGENT"]))
except ValueError as exc:
    text = str(exc)
    if text.startswith("no row "):
        sys.exit(0)
    print(text, file=sys.stderr)
    sys.exit(2)
'
}

worker_roles() {
  [ -f "$MODELS_PY" ] || return 0
  MMW_MODELS_PY="$MODELS_PY" python3 -c '
import importlib.util, os, sys
path = os.environ["MMW_MODELS_PY"]
spec = importlib.util.spec_from_file_location("mmw_models", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    for name in mod.worker_role_names():
        print(name)
except ValueError as exc:
    print(exc, file=sys.stderr)
    sys.exit(2)
'
}

# ------------------------------------------------------------------ the ticket

# Prints three lines when the ticket is ready to be worked on — its worker labels,
# its title, then the spec number from `## Parent` — and one line prefixed with
# REFUSE when it is not. The worker labels are the ticket's own labels ending in
# `-worker`, space separated, and the first line is empty when it carries none.
read_ticket() {
  local number="$1" json
  json="$(gh_ issue view "$number" --json state,labels,blockedBy,title,parent 2>/dev/null)" \
    || { echo "REFUSE could not read ticket #$number from the tracker"; return; }
  printf '%s' "$json" | MMW_TICKET_NUMBER="$number" python3 -c '
import importlib.util, json, os, re, subprocess, sys

number = os.environ["MMW_TICKET_NUMBER"]
try:
    ticket = json.load(sys.stdin)
except Exception:
    print("REFUSE the tracker did not answer with a readable ticket #" + number)
    sys.exit(0)

where = importlib.util.spec_from_file_location("mmw_events", os.environ["MMW_EVENTS_PY"])
events = importlib.util.module_from_spec(where)
where.loader.exec_module(events)

# A blocker holds until its work has landed (`events.blocker_hold`), the rule the frontier
# and the worker`s --preflight both apply; a closed one is read for its events.
def blocker_fold(n):
    env = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}
    run = subprocess.run(["gh", "issue", "view", str(n), "--json", "comments"],
                         capture_output=True, text=True, env=env)
    try:
        return events.fold(json.loads(run.stdout).get("comments") or [], issue=int(n))
    except Exception:
        return None

state = (ticket.get("state") or "unreadable").lower()
labels = [label.get("name") for label in ticket.get("labels") or []]
nodes = (ticket.get("blockedBy") or {}).get("nodes") or []
blockers = []
for b in nodes:
    b_state = (b.get("state") or "").upper()
    why = events.blocker_hold(b_state, blocker_fold(b.get("number")) if b_state == "CLOSED" else None)
    if why:
        blockers.append("#" + str(b.get("number")) + ("" if why == "open" else " (" + why + ")"))
grades = sorted(name for name in labels if name and name.endswith("-worker"))
# The batch is the parent link the tracker records, and nothing else. `## Parent` is
# prose written for a person: #193 opens that section with 「无 spec；本仓自建票。收口
# #188 的评审票外」, so any reader taking the first `#N` in it comes back with 188. A
# ticket with no parent link belongs to no batch, and its events carry an empty `spec`.
parent = ticket.get("parent") or {}
spec = str(parent.get("number") or "")

if state != "open":
    print("REFUSE ticket #" + number + " is " + state + ", not open")
elif "ready-for-agent" not in labels:
    print("REFUSE ticket #" + number + " is not labelled ready-for-agent")
elif blockers:
    print("REFUSE ticket #" + number + " is still blocked by " + ", ".join(blockers))
else:
    print(" ".join(grades))
    print(ticket.get("title") or "")
    print(spec)
'
}

# ------------------------------------------------------------------ worktrees
#
# The protocol cuts and removes the worktree with git. The runner only receives
# the absolute directory. The location is always `<repo>/.worktrees/issue-<n>`:
# no runner name in the path, and the slug stays `issue-<n>` so hook.py's
# TICKET_DIR still governs the session.

# The repository's main checkout: where every ticket's worktree lives, whichever
# checkout — and whichever branch — a command runs from.
main_checkout() {
  git worktree list --porcelain 2>/dev/null | sed -n '1s/^worktree //p'
}

worktrees_root() {
  local root
  root="$(main_checkout)"
  [ -n "$root" ] || return 0
  printf '%s/.worktrees\n' "$root"
}

workspace_cwd_for() {
  local root dest
  root="$(worktrees_root)"
  [ -n "$root" ] || return 0
  dest="$root/issue-$1"
  [ -d "$dest" ] && printf '%s\n' "$dest"
}

# Read-only checks that must pass before a replacement stops the worker holding the
# ticket. `ensure_workspace` repeats them after the stop because origin may move between
# the check and the worktree update.
workspace_origin_ready() {
  local number="$1" root="$2" into="$3" dest branch local_left remote_left
  dest="$root/.worktrees/issue-$number"
  branch="issue-$number"
  fetch_origin "$root" || return 1
  require_origin_branch "$root" "$into" || return 1
  if [ -d "$dest" ]; then
    local on
    on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ "$on" = "$branch" ] || {
      echo "dispatch: $dest is on ${on:-no branch}, not $branch; it is not this ticket's worktree — move it or rename it, then start again" >&2
      return 1
    }
  fi
  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch" \
      && git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    read -r local_left remote_left <<<"$(git -C "$root" rev-list --left-right --count "$branch...origin/$branch")"
    if [ "$local_left" -gt 0 ] && [ "$remote_left" -gt 0 ]; then
      echo "dispatch: $branch and origin/$branch have diverged: local is $local_left commit(s) ahead and origin is $remote_left commit(s) ahead; reconcile them without force-push, then start again" >&2
      return 1
    fi
  fi
}

# Refresh origin before any branch decision. The remote is authoritative;
# a missing or unreadable origin is not replaced with the checkout's stale knowledge.
fetch_origin() {
  local root="$1" out
  if ! git -C "$root" remote get-url origin >/dev/null 2>&1; then
    echo "dispatch: this repository has no origin remote" >&2
    return 1
  fi
  if ! out="$(git -C "$root" fetch --prune origin 2>&1)"; then
    echo "dispatch: git fetch origin failed: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
    return 1
  fi
}

current_branch() {
  local branch
  branch="$(git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null)"
  case "$branch" in HEAD | "") return 1 ;; esac
  printf '%s\n' "$branch"
}

require_origin_branch() {
  local root="$1" branch="$2"
  git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch" && return 0
  echo "dispatch: origin/$branch does not exist; push the base branch to origin before continuing" >&2
  return 1
}

# Push a ticket branch without rewriting the remote. A rejection leaves the worktree and
# branch standing so the operator can reconcile the two histories and retry.
push_ticket_branch() {
  local number="$1" cwd="$2" out
  if ! out="$(git -C "$cwd" push --set-upstream origin "issue-$number" 2>&1)"; then
    echo "dispatch: git push origin issue-$number was rejected: $(printf '%s' "$out" | tr '\n' ' '); nothing was force-pushed" >&2
    return 1
  fi
  echo "dispatch: pushed issue-$number to origin" >&2
}


# The registered worktree for ticket `number`, even after its workspace has been
# archived: `lease.py` still holds the path. Used when `workspace_cwd_for` is empty.
# Matched under this checkout's worktrees_root, not by basename: two repositories
# can both have issue-<n>.
lease_worktree_for() {
  local number="$1" root
  root="$(worktrees_root)"
  [ -n "$root" ] || return 0
  MMW_LEASE_PY="$LEASE" MMW_SLUG="issue-$number" MMW_TREES="$root" python3 -c '
import importlib.util, os, sys
from pathlib import Path

path = os.environ["MMW_LEASE_PY"]
spec = importlib.util.spec_from_file_location("mmw_lease", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
want = os.environ["MMW_SLUG"]
root = Path(os.environ["MMW_TREES"]).resolve()
for rec in mod.claimed():
    tree = Path(rec.get("worktree") or "")
    if tree.name != want:
        continue
    try:
        resolved = tree.resolve()
    except OSError:
        resolved = tree
    if resolved == root / want or root in resolved.parents:
        print(rec["worktree"])
        break
' 2>/dev/null
}

# ------------------------------------------------------------------ slots
#
# Several runs share one machine. `lease.py` hands each worktree a block of ports and a
# directory nothing else uses. Nothing here takes a slot: a worker writes code without
# one, and the first run of its criteria that needs the product claims it, waiting while
# the product's `instance.max` or the machine's slots are all held. What this script does
# is give slots back — at landing, at a retraction, at a suspension — after taking the
# product down, since a slot is free only once nothing listens on its ports.

# Give a ticket's claim back, when this pipeline's own account holds it. Returns 0
# given back, 1 nothing to give back (no login, or someone else holds it), 2 the
# write failed. A ticket a person took for themselves is left exactly as it is.
give_claim_back() {
  local number="$1" login
  login="$(gh_ api user --jq .login 2>/dev/null | tr -d '[:space:]')"
  [ -n "$login" ] || return 1
  printf '%s' "$(gh_ issue view "$number" --json assignees 2>/dev/null)" \
    | MMW_LOGIN="$login" python3 -c '
import json, os, sys
login = os.environ["MMW_LOGIN"]
try:
    rows = (json.load(sys.stdin) or {}).get("assignees") or []
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if login in [a.get("login") for a in rows if isinstance(a, dict)] else 1)
' || return 1
  gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1 || return 2
  return 0
}

# Take a worktree's product down and give its slot back: `lease.py release --stop`, which
# runs the `stop` that worktree's `.mmw/target.json` declares, from inside it, and then
# releases the slot. The stop lives in the worktree and names that worktree's own compose
# project, so this runs before the worktree is archived; a stack left up holds its slot
# with nothing left to reach it. `lease.py` answers in its exit code, never its wording:
# 0 released, 3 no slot was held there, anything else kept — something still listens on
# the slot, or `.mmw/target.json` cannot be read, so the stop is unknown. Returns 0, 3, or
# 1 for kept, with `lease.py`'s reason on stderr.
give_slot_back() {
  local err rc
  err="$(python3 "$LEASE" release "$1" --stop 2>&1 >/dev/null)"
  rc=$?
  case "$rc" in
    0) [ -z "$err" ] || printf '%s\n' "$err" >&2
       return 0 ;;
    3) return 3 ;;
  esac
  printf 'dispatch: lease not released for %s: %s\n' "$1" "$err" >&2
  return 1
}

# Give ticket <n>'s slot back at the moment a released claim ends its work: a slot is
# held until the ticket's work ends, not until somebody next lands it. Returns 0 given
# back or none held, 1 still held (said on stderr).
give_ticket_slot_back() {
  local number="$1" cwd
  [ -f "$LEASE" ] \
    || { echo "dispatch: no lease.py in any --tools directory, so #$number's slot was not given back" >&2; return 1; }
  cwd="$(workspace_cwd_for "$number")"
  [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
  [ -n "$cwd" ] || return 0
  give_slot_back "$cwd"
  case "$?" in
    0 | 3) return 0 ;;
  esac
  echo "dispatch: #$number's claim is given back, but its slot is still held: stop its product in $cwd, then python3 $LEASE release $cwd" >&2
  return 1
}

# Prints dest<TAB>cwd<TAB>created. `into` is already resolved from events (or the current
# checkout outside a night). Every decision is made after fetching origin.
ensure_workspace() {
  local number="$1" root="$2" into="$3" dest branch remote local_left remote_left created=0
  dest="$root/.worktrees/issue-$number"
  branch="issue-$number"
  fetch_origin "$root" || return 1
  require_origin_branch "$root" "$into" || return 1
  if [ -d "$dest" ]; then
    local on
    on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ "$on" = "$branch" ] \
      || { echo "dispatch: $dest is on ${on:-no branch}, not $branch; it is not this ticket's worktree — move it or rename it, then start again" >&2; return 1; }
  fi
  remote=0
  git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$branch" && remote=1

  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch" && [ "$remote" = 1 ]; then
    read -r local_left remote_left <<<"$(git -C "$root" rev-list --left-right --count "$branch...origin/$branch")"
    if [ "$local_left" -gt 0 ] && [ "$remote_left" -gt 0 ]; then
      echo "dispatch: $branch and origin/$branch have diverged: local is $local_left commit(s) ahead and origin is $remote_left commit(s) ahead; reconcile them without force-push, then start again" >&2
      return 1
    fi
    if [ "$remote_left" -gt 0 ]; then
      if [ -d "$dest" ]; then
        git -C "$dest" merge --ff-only --quiet "origin/$branch" \
          || { echo "dispatch: could not fast-forward $branch to origin/$branch" >&2; return 1; }
      else
        git -C "$root" branch --force "$branch" "origin/$branch" >/dev/null \
          || { echo "dispatch: could not fast-forward $branch to origin/$branch" >&2; return 1; }
      fi
    fi
  fi

  if [ -d "$dest" ]; then
    if [ "$remote" = 0 ]; then
      push_ticket_branch "$number" "$dest" || return 1
    fi
    printf '%s\t%s\t0\n' "$dest" "$dest"
    return 0
  fi
  mkdir -p "$root/.worktrees"
  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    git -C "$root" worktree add --quiet "$dest" "$branch" \
      || { echo "dispatch: could not create a worktree for $branch" >&2; return 1; }
    created=1
  elif [ "$remote" = 1 ]; then
    git -C "$root" worktree add --quiet -b "$branch" "$dest" "origin/$branch" \
      || { echo "dispatch: could not create a worktree for $branch from origin/$branch" >&2; return 1; }
    created=1
  else
    git -C "$root" worktree add --quiet -b "$branch" "$dest" "origin/$into" \
      || { echo "dispatch: could not create a worktree for $branch from origin/$into" >&2; return 1; }
    created=1
  fi
  if [ "$remote" = 0 ]; then
    push_ticket_branch "$number" "$dest" || return 1
  fi
  printf '%s\t%s\t%s\n' "$dest" "$dest" "$created"
}

remove_worktree() {
  local root="$1" dest="$2"
  [ -n "$dest" ] || return 0
  git -C "$root" worktree remove --force "$dest" >/dev/null 2>&1 && return 0
  [ -d "$dest" ] || return 0
  echo "dispatch: could not remove the worktree at $dest" >&2
  return 1
}

# Commit the uncommitted edits a ticket's worker left in its worktree, on the ticket
# branch, naming who left them (`left_by`). A worker whose session ended mid-turn — lost,
# stopped by a suspension, replaced, retracted — leaves its unfinished work that way, and
# it is the ticket's: the next worker's `--preflight` refuses a worktree with uncommitted
# changes to tracked files, and `git worktree remove --force` deletes them. Only tracked
# files are taken, the same set the preflight checks; the screenshots and caches a
# criteria run writes are untracked and stay out. The repository's own commit hooks are
# skipped: what is saved is half-written code, and a hook refusing it would stop the
# hand-over; the next worker's commits and the closeout's checks run them as usual.
# Exit 0 committed, or nothing to commit; 1 not committed, the reason on stderr.
keep_unfinished_work() {
  local number="$1" cwd="$2" left_by="$3" out
  [ -n "$cwd" ] && [ -d "$cwd" ] || return 0
  [ -n "$(git -C "$cwd" status --porcelain --untracked-files=no 2>/dev/null)" ] || return 0
  if ! out="$(git -C "$cwd" commit --all --no-verify --quiet \
        -m "wip(#$number): uncommitted work of $left_by" 2>&1)"; then
    echo "dispatch: $cwd holds uncommitted work of $left_by, and it could not be committed on issue-$number: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
    return 1
  fi
  echo "dispatch: committed the uncommitted work of $left_by on issue-$number" >&2
}

# End every session the ticket's events name, each through its own runner's `stop`.
# Git removes the worktree separately; no runner is asked to. Exit 1 when the ticket's
# events could not be read: then nobody knows which sessions run in the worktree, and
# the caller keeps it.
stop_ticket_agents() {
  local number="$1" live_only="${2:-0}" listed name ident state
  if [ "$#" -ge 3 ]; then
    listed="$3"
  else
    listed="$(sessions_on_ticket "$number")" || return 1
  fi
  while IFS=$'\t' read -r name ident; do
    [ -n "$ident" ] || continue
    use_runner "$name"
    if [ "$live_only" = 1 ]; then
      state="$(runner liveness "$ident")" || state=unknown
      [ "$state" = stopped ] && continue
    fi
    runner stop "$ident" \
      || echo "dispatch: could not stop $ident on #$number; it is still open on $name" >&2
  done <<<"$listed"
}

archive_ticket_agents() {
  stop_ticket_agents "$1"
}

# Stop sessions that are still present on their runner without removing the worktree.
# A bounced or returned ticket keeps that worktree for triage.
stop_live_ticket_agents() {
  stop_ticket_agents "$1" 1
}

latest_returned_sessions() {
  ticket_events "$1" fold | python3 -c '
import json, sys
state = json.load(sys.stdin)
if (state.get("last") or {}).get("event") != "ticket.returned":
    raise SystemExit(0)
for row in state.get("sessions") or []:
    print("{}\t{}".format(row.get("runner") or "", row.get("session") or ""))
'
}

stop_returned_ticket_agents() {
  local spec="$1" batch number listed
  batch="$(python3 "$STATUS" --worker-grades "$spec")" || return 1
  for number in $(printf '%s\n' "$batch" | awk '$1 == "BATCH" { print $2 }'); do
    listed="$(latest_returned_sessions "$number")" \
      || { echo "dispatch: could not read #$number after ticket.returned" >&2; continue; }
    [ -z "$listed" ] || stop_ticket_agents "$number" 1 "$listed"
  done
}

# Removing the worktree is where the product's stop command lives — so a worktree
# whose slot did not come back is kept, not removed. Keeping it is recoverable
# (stop the product there and run this again); deleting it is not. The sessions the
# ticket's events name are ended here as well: git worktree remove does not end them.
archive_workspace() {
  local number="$1" cwd rc root
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || true
  cwd="$(workspace_cwd_for "$number")"
  [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
  if [ -n "$cwd" ] && [ ! -f "$LEASE" ]; then
    echo "dispatch: #$number keeps its workspace — no lease.py was found, so its instance data cannot be removed safely" >&2
    return 1
  fi
  if [ -n "$cwd" ]; then
    give_slot_back "$cwd"
    rc=$?
    if [ "$rc" = 1 ]; then
      echo "dispatch: #$number keeps its workspace — its product is still up, and archiving would delete the worktree its stop command lives in. Stop it in $cwd, then run this again" >&2
      return 1
    fi
  fi
  if ! archive_ticket_agents "$number"; then
    echo "dispatch: #$number keeps its workspace — its events could not be read, so which sessions run in it is unknown. Run this again once the tracker answers" >&2
    return 1
  fi
  [ -n "$cwd" ] || return 0
  [ -n "$root" ] || root="$(dirname "$(dirname "$cwd")")"
  if remove_worktree "$root" "$cwd"; then
    python3 "$LEASE" remove-instance "$cwd" >/dev/null \
      || echo "dispatch: could not remove #$number's instance data after its worktree was removed" >&2
  else
    return 1
  fi
}

# ------------------------------------------------------------------ start

start_one() {
  local number="$1" kind="$2"
  use_runner "$(tonight_runner)"
  case "$kind" in
    worker|reviewer|verifier) ;;
    *) refuse "the second argument is worker, reviewer or verifier, got $kind" ;;
  esac

  local answer grades title spec
  answer="$(read_ticket "$number")"
  case "$answer" in
    "REFUSE "*) refuse "${answer#REFUSE }" ;;
    "") refuse "the tracker did not answer with a readable ticket #$number" ;;
  esac
  { IFS= read -r grades; IFS= read -r title; IFS= read -r spec; } <<<"$answer"
  if [ -n "${MMW_SPEC:-}" ]; then
    spec="$MMW_SPEC"
  fi
  # A ticket outside any batch is startable: it is dispatched one at a time and landed
  # with `land <n>`, which asks for a ticket number and never a spec. What it does not
  # get is a spec label, so no batch command ever picks it up as one of its own.

  # Whatever this session reports lands on the ticket, and only the relay turns that into
  # a wake for whoever waits on it. With no relay watching the ticket the result would
  # land and wake nobody, and the night would stop there without a word.
  local watched
  watched="$(relay_watches "$number" "$spec" 2>&1)" \
    || refuse "nothing would wake anyone when #$number's $kind reports: ${watched#relay: }. The main agent opens the night with open <spec>, or open-ticket <n> for a ticket outside a night; nothing was started"

  local profile
  case "$kind" in
    reviewer) profile=reviewer ;;
    verifier) profile=verifier ;;
    worker)
      local -a marked
      read -r -a marked <<<"$grades"
      case "${#marked[@]}" in
        0) profile="$DEFAULT_WORKER" ;;
        1) profile="${marked[0]}" ;;
        *) refuse "#$number carries ${#marked[@]} worker labels (${marked[*]}), and it takes one" ;;
      esac ;;
  esac

  local row host model effort
  use_catalog_of "$RUNNER_NAME"
  row="$(row_for_role "$profile")" || exit 2
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS_JSON has none"
  IFS=$'\t' read -r host model effort <<<"$row"

  local fallback into
  fallback="$(current_branch .)" || fallback=""
  case "$fallback" in issue-[0-9]* | "") fallback="" ;; esac
  into="$(resolve_into "$number" "$spec" "$fallback")" || exit 2

  # The checkout the night runs in, whichever worktree this runs from: a worker starts its
  # reviewer and its verifier from its own worktree, and `.worktrees/` cut under that one
  # would be a second worktree of the branch it already has checked out.
  local root
  root="$(main_checkout)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no working directory to give the session"

  workspace_origin_ready "$number" "$root" "$into" \
    || refuse "could not use origin to prepare issue-$number; an existing worker was not stopped"

  # A worker started on a ticket whose events still show a live worker replaces it. Two
  # workers in one worktree commit over each other, so the old session is stopped first,
  # through its own runner, and a start whose predecessor will not stop starts nothing.
  local -a replaced=()
  if [ "$kind" = worker ]; then
    local live_list old_runner old_ident
    live_list="$(live_workers_on_ticket "$number")" \
      || refuse "could not read #$number's events, so whether a worker already runs there is unknown; nothing was started"
    while IFS=$'\t' read -r old_runner old_ident; do
      [ -n "$old_ident" ] || continue
      use_runner "$old_runner"
      runner stop "$old_ident" \
        || refuse "#$number's worker $old_ident on $old_runner is live on its events and could not be stopped, so no second worker was started beside it; end it on $old_runner, then start again"
      replaced+=("$old_runner"$'\t'"$old_ident")
    done <<<"$live_list"
    use_runner "$(tonight_runner)"
  fi

  local cwd created ws_row
  ws_row="$(ensure_workspace "$number" "$root" "$into")" \
    || refuse "could not open a worktree for issue-$number"
  cwd="$(printf '%s\n' "$ws_row" | cut -f2)"
  created="$(printf '%s\n' "$ws_row" | cut -f3)"

  local base="" prompt
  case "$kind" in
    worker)
      base="$(newest_worker_field "$number" base)"
      case "$?" in
        0) ;;
        3) base="$(base_commit "$root" "$into" "issue-$number")" ;;
        *) exit 2 ;;
      esac
      [ -n "$base" ] \
        || refuse "issue-$number and origin/$into share no commit, so the worker has no base to record"
      prompt="Use the implement skill to work ticket #$number. $AUTONOMOUS $PRODUCT_RULES $PIPELINE_FAULT" ;;
    reviewer)
      base="$(base_commit "$root" "$into" "issue-$number")"
      if [ -z "$base" ]; then
        base="$(newest_worker_field "$number" base)" || base=""
      fi
      [ -n "$base" ] \
        || refuse "#${number}'s branch has no merge-base with origin/$into and worker.started carries no base, so the reviewer has no commit to start from"
      prompt="Use the code-review skill to review ticket #$number from base commit $base. $AUTONOMOUS" ;;
    verifier)
      base="$(base_commit "$root" "$into" "issue-$number")"
      if [ -z "$base" ]; then
        base="$(newest_worker_field "$number" base)" || base=""
      fi
      prompt="Use the verdict skill to verify ticket #$number. $AUTONOMOUS $PRODUCT_RULES" ;;
  esac

  # A standing worktree a worker of this ticket left — lost, stopped by a suspension, or
  # replaced a moment ago — can hold its uncommitted edits. They are this ticket's work,
  # and the new worker continues from them; left uncommitted, its `--preflight` would
  # refuse the worktree. A worktree no worker of this ticket has had is not touched: its
  # changes are somebody else's, and the preflight refuses them rather than take them.
  local publish=0
  if [ "$kind" = worker ] && [ "$created" = 0 ]; then
    local left_by
    left_by="$(last_worker_on_ticket "$number")" \
      || refuse "could not read #$number's events, so whose edits $cwd holds is unknown; nothing was started"
    if [ -n "$left_by" ]; then
      keep_unfinished_work "$number" "$cwd" "$left_by" \
        || refuse "the uncommitted work in $cwd was not saved (the reason is above), and a new worker cannot start on it; commit or set it aside on issue-$number, then start again. Nothing was started"
      publish=1
    fi
  fi
  [ "${#replaced[@]}" -eq 0 ] || publish=1
  if [ "$publish" = 1 ]; then
    push_ticket_branch "$number" "$cwd" \
      || refuse "#${number}'s previous worker was stopped, but its ticket branch was not pushed; reconcile issue-$number with origin/issue-$number and start again"
  fi

  local session
  if ! session="$(runner start --host "$host" --model "$model" --effort "$effort" \
       --cwd "$cwd" --prompt "$prompt" --skip-approval --title "#$number $kind")" \
     || [ -z "$session" ]; then
    if [ "$created" = 1 ] && [ -n "$cwd" ]; then
      remove_worktree "$root" "$cwd" \
        || echo "dispatch: could not remove the worktree for #$number" >&2
    fi
    refuse "$RUNNER_NAME did not start $host for #$number $kind (its reason is above); nothing was retried. Fix what it names, or change this agent's row in $MODELS_JSON, then start again"
  fi
  session="$(printf '%s\n' "$session" | tail -n 1)"

  if ! runner attach --cwd "$cwd" --issue "$number" 2>/dev/null; then
    echo "dispatch: $RUNNER_NAME started session $session for #$number, but did not attach the worktree to that issue; the session continues" >&2
  fi

  # The replaced sessions are closed on the ticket before the new one is recorded, so the
  # fold never reads two live workers. One whose event could not be written is stopped
  # but still reads live, and `status` names both; say so rather than leave it unsaid.
  local pair
  for pair in "${replaced[@]+"${replaced[@]}"}"; do
    old_runner="${pair%%$'\t'*}"
    old_ident="${pair#*$'\t'}"
    post_event "$number" worker.replaced --ticket "$number" --spec "$spec" \
        --line "Replaced the worker $old_ident on $old_runner with $session on $RUNNER_NAME" \
        --field "session=$old_ident" --field "runner=$old_runner" \
        --field "by_session=$session" --field "by_runner=$RUNNER_NAME" \
      || echo "dispatch: $old_ident on $old_runner is stopped, but the worker.replaced event on #$number was not written, so its events still read it as live beside $session; run retract once $session is done, or write it again" >&2
  done

  # The event is the only place this session is recorded: every later command finds
  # it there, and `advance` reads a ticket whose events show no hold as free.
  # So a session whose event could not be written is stopped again rather than left
  # running where nothing can find it — a second worker would be started beside it.
  if ! post_event "$number" "$kind.started" --ticket "$number" --spec "$spec" \
       --line "$kind started on $RUNNER_NAME: session $session, $host $model ($effort)" \
       --field "session=$session" --field "runner=$RUNNER_NAME" \
       --field "machine=$(machine_name)" \
       --field "host=$host" --field "model=$model" --field "effort=${effort:-—}" \
       --field "grade=$profile" --field "worktree=$cwd" --field "branch=issue-$number" \
       --field "base=$base" \
       --field "into=$into"; then
    if runner stop "$session"; then
      refuse "could not write the $kind.started event on #$number, so session $session on $RUNNER_NAME was stopped again rather than left running where no command can find it; start again once the tracker takes comments"
    fi
    refuse "could not write the $kind.started event on #$number, and session $session on $RUNNER_NAME could not be stopped either: it is running and no command can find it. End it on $RUNNER_NAME by hand"
  fi
  printf '%s\n' "$session"
}

# ------------------------------------------------------------------ retract

# Undo what start left behind when its session is gone: archive the workspace,
# give the slot back, give the claim back if this pipeline still holds it. The
# branch stays, so the next start reuses it. A live agent on the ticket is a
# running worker, not a failed start — refuse. `slot given back` is 1 only when
# lease.py actually released; a missing `lease.py` is a refusal, not a silent keep.
retract_one() {
  local number="$1"

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no workspace to retract"

  local line ident
  line="$(session_on_ticket "$number" worker)" \
    || refuse "could not read #$number's events, so whether a worker still runs there is unknown and nothing was archived"
  ident="$(printf '%s\n' "$line" | cut -f2)"
  [ -z "$line" ] || use_runner "$(printf '%s\n' "$line" | cut -f1)"
  # Archiving a workspace ends whatever runs in it, so only an agent the runner has shown
  # to be stopped lets this go on. Anything else — alive, unknown, or an answer this does
  # not recognise — refuses: a retract that cannot prove the agent is gone does nothing.
  if [ -n "$ident" ]; then
    case "$(runner liveness "$ident")" in
      stopped) ;;
      alive)
        refuse "#$number still has a live agent $ident on $RUNNER_NAME; retract is for a start whose session is gone"
        ;;
      *)
        refuse "cannot tell whether #$number's agent $ident is still running, so nothing was archived; retract only once that agent is shown to be stopped"
        ;;
    esac
  fi

  local cwd archived=0 slot=0 claim=0 rc
  cwd="$(workspace_cwd_for "$number")"
  [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
  # Archiving removes the worktree with --force, and its uncommitted edits with it. They
  # are the ticket's unfinished work, so they are saved on its branch first, and the
  # next start picks them up with the branch.
  if [ -n "$cwd" ] && [ -d "$cwd" ]; then
    local left_by="whoever claimed #$number with no session recorded on it"
    [ -z "$ident" ] || left_by="worker $ident on $RUNNER_NAME, left when its session stopped"
    keep_unfinished_work "$number" "$cwd" "$left_by" \
      || refuse "the uncommitted work in $cwd was not saved (the reason is above), and archiving would delete it; commit or set it aside on issue-$number, then retract again. Nothing was retracted"
    push_ticket_branch "$number" "$cwd" \
      || refuse "issue-$number was not pushed, so its worktree, slot and claim were kept; reconcile it with origin/issue-$number and retract again"
  fi
  if [ -n "$cwd" ]; then
    [ -f "$LEASE" ] \
      || refuse "no lease.py in any --tools directory, so the slot cannot be given back. Pass --tools <the drive-target skill's scripts directory>, then retract again"
    if give_slot_back "$cwd"; then
      slot=1
    fi
  fi
  if [ -n "$cwd" ] && [ -d "$cwd" ]; then
    archive_workspace "$number" && archived=1
  fi

  give_claim_back "$number"
  case "$?" in
    0) claim=1 ;;
    2) echo "dispatch: could not give back the claim on #$number" >&2 ;;
  esac

  # The retraction is what closes the start on the ticket's events: without it the
  # ticket would read as held by a worker that is gone, and never be started again.
  local -a named=()
  [ -z "$ident" ] || named=(--field "session=$ident" --field "runner=$RUNNER_NAME")
  post_event "$number" worker.retracted --ticket "$number" --spec "$(ticket_spec "$number")" \
      --line "Retracted the start on #$number: archived $archived, slot given back $slot, claim given back $claim" \
      ${named[@]+"${named[@]}"} \
      --json-field "archived=$([ "$archived" = 1 ] && echo true || echo false)" \
      --json-field "slot_given_back=$([ "$slot" = 1 ] && echo true || echo false)" \
      --json-field "claim_given_back=$([ "$claim" = 1 ] && echo true || echo false)" \
    || echo "dispatch: could not write the worker.retracted event on #$number, so its events still show the start as live and advance will not start it again; run retract again" >&2

  echo "retract #$number: archived $archived, slot given back $slot, claim given back $claim" >&2
}

# ------------------------------------------------------------------ resume

# Two ways this fails, and they call for opposite things. No such worker is final:
# nothing will change by sending again. A worker that is there but will not take the
# message is temporary: it is in a turn, and a turn ends.
#
# Which one it is, is the runner adapter's answer, not this function's reading of an
# error sentence: `send` answers 0 when the message was taken, 3 when the agent is there
# but in a turn, and 2 when there is no such session (#314 section 1). A fourth answer, 4,
# is a message the session was handed and whose turn start its runner cannot observe
# (Orca running Grok answers every send that way, and Grok reads each one, a busy Grok
# once its turn ends): the text is in the session, so it is recorded like a 0 and exits 4,
# which says not to send it again. Sending it again would have the worker read it twice.
#
# Telling "not there" from "in a turn" is worth it: reading both as "not there", whose
# documented meaning is "read status, do not send again", turns a three-minute wait into
# a permanent answer. On 2026-09-07 (#211) a worker was left unreachable that way and a
# five-hour session with 16 commits on its branch had to be killed.
resume_one() {
  local number="$1" text="$2" ident out
  [ -n "$text" ] || refuse "resume needs the text to send"
  local line
  line="$(session_on_ticket "$number" worker)" \
    || refuse "could not read #$number's events, so there is no session to send to"
  [ -n "$line" ] || refuse "#$number has no worker.started event, so there is no session to send to"
  use_runner "$(printf '%s\n' "$line" | cut -f1)"
  ident="$(printf '%s\n' "$line" | cut -f2)"
  out="$(runner send "$ident" "$text" 2>&1)"
  local rc=$?
  case "$rc" in
    0 | 4)
      post_event "$number" worker.resumed --ticket "$number" --spec "$(ticket_spec "$number")" \
          --line "Resumed the worker $ident on $RUNNER_NAME" \
          --field "session=$ident" --field "runner=$RUNNER_NAME" \
        || echo "dispatch: the worker $ident took the message, but the worker.resumed event on #$number was not written" >&2
      [ "$rc" = 0 ] && return 0
      echo "dispatch: the worker $ident on #$number was handed the message, and $RUNNER_NAME cannot show a turn starting on it; the text is in the session, so do not send it again" >&2
      exit 4 ;;
    2) refuse "#$number's worker $ident is not on $RUNNER_NAME any more" ;;
  esac
  echo "dispatch: the worker $ident on #$number did not take the message" >&2
  [ -n "$out" ] && printf '  %s\n' "$out" >&2
  echo "dispatch: it is most likely in a turn — wait, then run resume again. A worker that keeps refusing while nothing on its ticket moves is replaced with start $number worker, which stops it through its runner first" >&2
  exit 3
}

# ------------------------------------------------------------------ wait

# The newest result event of this kind — worker `ticket.passed` / `ticket.returned`,
# reviewer `reviewer.reported`, verifier `verifier.passed` / `verifier.failed` — as its
# name and key fields (`verifier.failed commit=… failed=AC2`). Nothing when there is
# none; non-zero when the ticket could not be read or carries an event nobody can read.
result_event() {
  ticket_events "$1" result --kind "$2"
}

# Print the newest result event of this kind on ticket <n>, by name and key fields: a
# read of the ticket, and nothing else. A caller runs it after the relay woke it with that
# event, so the result is there. It waits for nothing and asks no runner: a session that
# has not reported yet is heard from when its result lands, and one that died is the
# watchdog's to find. Writes nothing.
wait_one() {
  local number="$1" kind="$2"
  case "$kind" in
    worker|reviewer|verifier) ;;
    *) refuse "the second argument is worker, reviewer or verifier, got $kind" ;;
  esac

  local head
  head="$(result_event "$number" "$kind")" \
    || refuse "could not read #$number's events, so what its $kind reported is unknown"
  if [ -n "$head" ]; then
    printf '%s\n' "$head"
    return 0
  fi

  local line
  line="$(session_on_ticket "$number" "$kind")" \
    || refuse "could not read #$number's events, so what its $kind reported is unknown"
  [ -n "$line" ] || refuse "#$number has no $kind.started event, so there is no result to read"
  echo "dispatch: #$number carries no result of its $kind yet; the relay wakes you when it lands, so end your turn" >&2
  exit 3
}

# ------------------------------------------------------------------ check

check_machine() {
  local spec="$1"
  local failed=0

  local root into rows project source project_push=0 base_push=0 branch ahead presence
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  if [ -z "$root" ]; then
    echo "dispatch: not inside a git repository, so the project branch cannot be checked" >&2
    failed=1
  else
    into="$(current_branch "$root")" || into=""
    if [ -z "$into" ]; then
      echo "dispatch: the checkout has no current branch to use as the base branch" >&2
      failed=1
    elif fetch_origin "$root" && rows="$(inspect_open_branches "$root" "$spec" "$into")"; then
      project="$(printf '%s\n' "$rows" | head -1 | cut -f1)"
      source="$(printf '%s\n' "$rows" | head -1 | cut -f2)"
      while IFS=$'\t' read -r _ _ branch ahead presence _behind; do
        [ "$branch" = "$project" ] && project_push="$ahead"
        [ "$branch" = "$into" ] && base_push="$ahead"
      done <<<"$rows"
      check_open_pushes "$root" "$rows" || failed=1
      echo "project branch: $project (source: $source); open would push $project: $project_push commit(s), $into: $base_push commit(s)"
    else
      failed=1
    fi
  fi

  if [ ! -f "$INSTALLER" ]; then
    echo "dispatch: no install.sh at $INSTALLER" >&2
    failed=1
  elif ! bash "$INSTALLER" --check; then
    echo "dispatch: install.sh --check found something missing" >&2
    failed=1
  fi

  # Tonight's runner has to be one this skill has an adapter for, and every row `start`
  # reads — each worker grade, the reviewer, the verifier — has to resolve against the
  # catalog of that runner. A row that does not resolve refuses every start of its agent,
  # one ticket at a time, hours into the night; here it is one line before the night opens,
  # in the resolver's own words.
  local runner roles role out err_file
  runner="$(tonight_runner)"
  if [ ! -f "$SKILL_ROOT/scripts/runners/$runner.sh" ]; then
    echo "dispatch: tonight's runner is $runner, and this skill has no adapter for it (scripts/runners/$runner.sh); name paseo, orca or herdr in MMW_RUNNER or models.json" >&2
    failed=1
  fi
  use_catalog_of "$runner"
  roles="$(worker_roles | tr '\n' ' ')" \
    || { echo "dispatch: $MODELS_JSON cannot be read (the reason is above)" >&2; failed=1; roles=""; }
  err_file="$(mktemp)"
  for role in $roles reviewer verifier; do
    if ! out="$(row_for_role "$role" 2>"$err_file")"; then
      echo "dispatch: the $role row of $MODELS_JSON does not resolve on $runner: $(tr '\n' ' ' < "$err_file")" >&2
      failed=1
    elif [ -z "$out" ]; then
      echo "dispatch: $MODELS_JSON has no $role row, and every $role start reads one" >&2
      failed=1
    fi
  done
  rm -f "$err_file"

  # `provider ls` answers from a cached snapshot, and a host that was available when
  # that snapshot was taken can since have been logged out of or upgraded out from under
  # the daemon — a night that opens on that answer then fails one ticket at a time,
  # hours later, for a reason `check` was asked to catch. `provider diagnostic` refreshes
  # the snapshot for one host by really asking it: resolving the binary, reading its
  # version and its login, and for an ACP host opening and closing a session. So each
  # host is refreshed first and the verdict is then taken off the refreshed snapshot,
  # rather than off the English sentence the diagnostic prints. That sentence is what a
  # reader needs when the verdict is no, so it is kept and printed under the refusal.
  #
  # One diagnostic per host, not per row of models.json: several agents share a host, and
  # the call costs seconds (measured: claude 0.7s, pi 1.7s, grok 2.5s, cursor 6.7s).
  # Paseo's provider snapshot only says something about sessions Paseo starts.
  local host host_line hosts="" diag paseo_roles=""
  [ "$runner" = paseo ] && paseo_roles="$roles reviewer verifier"
  for role in $paseo_roles; do
    host_line="$(row_for_role "$role" 2>/dev/null)" || continue
    host="$(printf '%s\n' "$host_line" | cut -f1)"
    [ -n "$host" ] || continue
    case " $hosts " in *" $host "*) continue ;; esac
    hosts="$hosts $host"
    diag="$(runner_call paseo diagnostic "$host" 2>&1)" || diag=""
    MMW_HOST="$host" MMW_PROVIDERS="$(runner_call paseo catalog-status 2>/dev/null)" python3 -c '
import json, os, sys

host = os.environ["MMW_HOST"]
raw = os.environ.get("MMW_PROVIDERS") or ""
try:
    rows = json.loads(raw) if raw else []
except Exception:
    rows = []
ok = False
if isinstance(rows, list):
    for row in rows:
        if isinstance(row, dict) and row.get("provider") == host:
            ok = (row.get("status") == "available")
            break
if not ok:
    sys.exit(1)
' || {
      echo "dispatch: provider $host is not available" >&2
      printf '%s' "$diag" | python3 -c '
import json, sys

try:
    text = (json.load(sys.stdin) or {}).get("diagnostic") or ""
except Exception:
    text = ""
for line in text.splitlines():
    if line.strip():
        print("  " + line.rstrip())
' >&2
      failed=1
    }
  done

  local grades line number
  grades="$(python3 "$STATUS" --worker-grades "$spec")" \
    || { echo "dispatch: could not read the batch under #$spec" >&2; failed=1; grades=""; }
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    local -a fields marked
    read -r -a fields <<<"$line"
    [ "${fields[0]}" = "GRADE" ] || continue
    number="${fields[1]}"
    marked=("${fields[@]:2}")
    case "${#marked[@]}" in
      0) ;;
      1) case " $roles " in
           *" ${marked[0]} "*) ;;
           *) echo "dispatch: #$number asks for ${marked[0]}, and $MODELS_JSON has no such row" >&2
              failed=1 ;;
         esac ;;
      *) echo "dispatch: #$number carries ${#marked[@]} worker labels (${marked[*]}), and it takes one" >&2
         failed=1 ;;
    esac
  done <<<"$grades"

  [ "$failed" -eq 0 ] || exit 2
}

# ------------------------------------------------------------------ integrating

# Ticket numbers represented by first-parent merge commits in one revision range, in
# merge order. `advance` writes this exact subject when it lands a ticket on the base branch.
integrated_ticket_numbers() {
  git -C "$1" log --reverse --first-parent --format='%s' "$2" 2>/dev/null \
    | sed -n "s/^Merge branch 'issue-\([0-9][0-9]*\)'$/\1/p" \
    | awk '!seen[$0]++'
}

integrate_conflict_report() {
  local root="$1" number="$2" into="$3" tickets="$4" ticket title
  {
    echo "CONFLICT merging origin/$into into issue-$number"
    echo
    echo "  incoming tickets:"
    if [ -z "$tickets" ]; then
      echo "    none represented by Merge branch 'issue-<n>' commits"
    else
      while IFS= read -r ticket; do
        [ -n "$ticket" ] || continue
        title="$(ticket_title "$ticket")"
        echo "    #$ticket  $title"
      done <<<"$tickets"
    fi
    echo
    echo "  conflicted files:"
    git -C "$root" diff --name-only --diff-filter=U | sed 's/^/    /'
    echo
    echo "  Resolve this merge with the resolving-merge-conflicts skill, run the"
    echo "  repository checks affected by the merged tickets, commit the merge,"
    echo "  then run dispatch.sh integrate $number again."
  } >&2
}

# Bring the `origin/<base branch>` recorded by the newest worker.started into this
# ticket's branch. The command is run by that ticket's worker from its own worktree. It never
# pushes, rebases, or aborts a conflict.
integrate_ticket() {
  local number="$1" root branch into base tickets out
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is no issue-$number to integrate"
  branch="$(current_branch "$root")" || branch=""
  [ "$branch" = "issue-$number" ] \
    || refuse "integrate $number runs from branch issue-$number, not ${branch:-a detached HEAD}"
  [ -z "$(git -C "$root" status --porcelain --untracked-files=no)" ] \
    || refuse "issue-$number has uncommitted tracked changes; commit them before integrating the base branch"

  into="$(newest_worker_field "$number" into)"
  case "$?" in
    0) ;;
    3) refuse "#${number} has no worker.started event, so its base branch is unknown" ;;
    *) exit 2 ;;
  esac

  fetch_origin "$root" || exit 2
  require_origin_branch "$root" "$into" || exit 2
  if git -C "$root" merge-base --is-ancestor "origin/$into" HEAD; then
    echo "issue-$number is already current with origin/$into"
    return 0
  fi
  base="$(git -C "$root" merge-base HEAD "origin/$into" 2>/dev/null)"
  [ -n "$base" ] \
    || refuse "issue-$number and origin/$into share no commit, so they cannot be integrated"
  tickets="$(integrated_ticket_numbers "$root" "$base..origin/$into")"

  if out="$(git -C "$root" merge --no-ff -m "Merge $into into issue-$number" "origin/$into" 2>&1)"; then
    if [ -n "$tickets" ]; then
      printf 'integrated origin/%s into issue-%s; incoming tickets:' "$into" "$number"
      while IFS= read -r ticket; do
        [ -n "$ticket" ] && printf ' #%s' "$ticket"
      done <<<"$tickets"
      printf '\n'
    else
      echo "integrated origin/$into into issue-$number; incoming tickets: none"
    fi
    return 0
  fi
  if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    integrate_conflict_report "$root" "$number" "$into" "$tickets"
    return 3
  fi
  echo "dispatch: git merge origin/$into into issue-$number failed: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
  return 2
}

# ------------------------------------------------------------------ advancing

ticket_branch() { printf 'issue-%s\n' "$1"; }

ticket_title() {
  gh_ issue view "$1" --json title -q .title 2>/dev/null | head -n 1
}

merge_slug() { printf '%s\n' "${1//\//-}"; }

MERGE_LOCK=""
MERGE_LOCK_PID=""
MERGE_LOCK_READY=""
MERGE_ROOT=""
release_merge_lock() {
  if [ -n "$MERGE_LOCK_PID" ]; then
    kill "$MERGE_LOCK_PID" 2>/dev/null || true
    wait "$MERGE_LOCK_PID" 2>/dev/null || true
  fi
  [ -z "$MERGE_LOCK_READY" ] || rm -f "$MERGE_LOCK_READY"
  MERGE_LOCK=""
  MERGE_LOCK_PID=""
  MERGE_LOCK_READY=""
}

acquire_merge_lock() {
  local into="$1" slug state answer i
  slug="$(merge_slug "$into")"
  state="$(repository_state_dir)" || return 2
  MERGE_LOCK="$state/merge-$slug.lock"
  MERGE_LOCK_READY="$(mktemp)"
  python3 - "$STATEDIR" "$MERGE_LOCK" "$into" "$$" <<'PY' >"$MERGE_LOCK_READY" 2>&1 &
import importlib.util, os, sys, time
from pathlib import Path

script, lock, into, parent = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_statedir", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    with mod.locked(Path(lock), wait=6.0, purpose=f"landing into origin/{into}"):
        print("LOCKED", flush=True)
        while os.getppid() == int(parent):
            time.sleep(0.1)
except mod.LockHeld as exc:
    print(f"dispatch: another merge into {into} still holds {exc}", flush=True)
    raise SystemExit(2)
PY
  MERGE_LOCK_PID=$!
  for ((i = 1; i <= 70; i++)); do
    [ -s "$MERGE_LOCK_READY" ] && break
    kill -0 "$MERGE_LOCK_PID" 2>/dev/null || break
    sleep 0.1
  done
  answer="$(cat "$MERGE_LOCK_READY")"
  case "$answer" in
    LOCKED) trap release_merge_lock EXIT; return 0 ;;
    "") echo "dispatch: the merge lock helper for origin/$into did not answer" >&2 ;;
    *) printf '%s\n' "$answer" >&2 ;;
  esac
  release_merge_lock
  return 2
}

repository_state_dir() {
  local repo
  repo="$(repo_slug)" || return 2
  python3 - "$STATEDIR" "$repo" <<'PY'
import importlib.util, sys
from pathlib import Path

script, repo = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_statedir", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.state_dir(repo))
PY
}

# Remove persistent merge worktrees whose matching origin branch no longer exists.
# A slug cannot be reversed when a branch contains '-', so compare it with the set made
# by applying the same slug rule to every fetched origin branch.
sweep_orphan_merge_worktrees() {
  local root="$1" main state
  main="$(main_checkout)" || return 0
  [ -n "$main" ] || return 0
  fetch_origin "$root" || return 1
  state="$(repository_state_dir)" || return 1
  python3 - "$STATEDIR" "$root" "$main/.worktrees" "$state" <<'PY'
import importlib.util
import subprocess
import sys
from pathlib import Path

script, root, trees, state = sys.argv[1:]
spec = importlib.util.spec_from_file_location("mmw_statedir", script)
statedir = importlib.util.module_from_spec(spec)
spec.loader.exec_module(statedir)
refs = subprocess.run(
    ["git", "-C", root, "for-each-ref", "--format=%(refname:strip=3)",
     "refs/remotes/origin/"], capture_output=True, text=True, check=True
).stdout.splitlines()
active = {name.replace("/", "-") for name in refs if name and name != "HEAD"}
for path in sorted(Path(trees).glob("merge-*")):
    if not path.is_dir():
        continue
    slug = path.name.removeprefix("merge-")
    if slug in active:
        continue
    lock = Path(state) / f"merge-{slug}.lock"
    try:
        with statedir.locked(lock, wait=0, purpose=f"sweeping orphan merge-{slug}"):
            removed = subprocess.run(
                ["git", "-C", root, "worktree", "remove", "--force", str(path)],
                capture_output=True, text=True
            ).returncode == 0
    except statedir.LockHeld:
        continue
    if removed:
        lock.unlink(missing_ok=True)
    else:
        print(f"dispatch: could not remove orphan merge worktree {path}", file=sys.stderr)
PY
}

# One detached, persistent worktree per base branch. Reset changes tracked files only:
# ignored dependency directories and caches stay warm between landings.
prepare_merge_worktree() {
  local root="$1" into="$2" main slug dest
  main="$(main_checkout)"
  [ -n "$main" ] \
    || { echo "dispatch: could not resolve the main checkout from $root" >&2; return 2; }
  slug="$(merge_slug "$into")"
  dest="$main/.worktrees/merge-$slug"
  acquire_merge_lock "$into" || return 2

  fetch_origin "$root" || { release_merge_lock; return 2; }
  require_origin_branch "$root" "$into" || { release_merge_lock; return 2; }
  mkdir -p "$(dirname "$dest")"
  if [ -e "$dest" ]; then
    git -C "$dest" rev-parse --is-inside-work-tree >/dev/null 2>&1 \
      || { echo "dispatch: $dest exists and is not a git worktree" >&2; release_merge_lock; return 2; }
  else
    git -C "$root" worktree add --detach "$dest" "origin/$into" >/dev/null \
      || { echo "dispatch: could not create the merge worktree $dest" >&2; release_merge_lock; return 2; }
  fi
  git -C "$dest" merge --abort >/dev/null 2>&1 || true
  git -C "$dest" reset --hard "origin/$into" >/dev/null \
    || { echo "dispatch: could not reset $dest to origin/$into" >&2; release_merge_lock; return 2; }
  MERGE_ROOT="$dest"
}

ticket_passed_commit() {
  local number="$1" commit rc
  commit="$(newest_field "$number" commit ticket.passed)"
  rc=$?
  case "$rc" in
    0) printf '%s\n' "$commit" ;;
    2) echo "dispatch: could not read #$number's events, so its passed commit is unknown" >&2; return 2 ;;
    3) echo "dispatch: #$number carries no active ticket.passed event" >&2; return 2 ;;
    4) echo "dispatch: #$number's ticket.passed event carries no commit" >&2; return 2 ;;
    *) echo "dispatch: could not resolve #$number's passed commit" >&2; return 2 ;;
  esac
}

ticket_into() {
  local number="$1" spec="$2" into rc
  into="$(newest_field "$number" into ticket.passed)"; rc=$?
  case "$rc" in
    0) printf '%s\n' "$into"; return 0 ;;
    2) echo "dispatch: could not read #$number's events, so its base branch is unknown" >&2; return 2 ;;
    3 | 4) ;;
    *) return 2 ;;
  esac
  into="$(newest_worker_field "$number" into)"; rc=$?
  case "$rc" in
    0) printf '%s\n' "$into"; return 0 ;;
    2) return 2 ;;
    3) ;;
    *) return 2 ;;
  esac
  if [ -n "$spec" ]; then
    into="$(newest_field "$spec" into spec.opened spec.suspended spec.closed)"; rc=$?
    case "$rc" in
      0) printf '%s\n' "$into"; return 0 ;;
      2) echo "dispatch: could not read whether the night on #$spec is open, so #$number's base branch is unknown" >&2; return 2 ;;
      3) ;;
      4) echo "dispatch: the open night on #$spec carries no spec.opened.into" >&2; return 2 ;;
      *) return 2 ;;
    esac
  fi
  echo "dispatch: #$number carries no base branch in ticket.passed, worker.started, or its open night" >&2
  return 2
}

repo_checks_met() {
  local number="$1" commit="$2" field ran="" result=""
  for field in $(ticket_events "$number" checked --run repo-checks 2>/dev/null); do
    case "$field" in
      commit=*) ran="${field#commit=}" ;;
      result=*) result="${field#result=}" ;;
    esac
  done
  [ "$ran" = "$commit" ] && [ "$result" = met ]
}

MERGE_CHECKS_JSON=""
run_merge_checks() {
  local root="$1" into="$2"
  MERGE_CHECKS_JSON="$(python3 - "$VERIFY" "$root" "$into" <<'PY'
import importlib.util, json, sys
from pathlib import Path

script, root, into = sys.argv[1:]
sys.path.insert(0, str(Path(script).resolve().parent))
spec = importlib.util.spec_from_file_location("mmw_verify_ticket", script)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
print(json.dumps(mod.run_target_json_checks(Path(root), into), separators=(",", ":")))
PY
)" || return 2
  [ "$MERGE_CHECKS_JSON" != null ] || return 3
  MMW_CHECKS_JSON="$MERGE_CHECKS_JSON" python3 -c '
import json, os, sys
value = json.loads(os.environ["MMW_CHECKS_JSON"])
sys.exit(0 if not value.get("failed") and not value.get("problem") else 1)
'
}

bounce_ticket() {
  local root="$1" number="$2" spec="$3" into="$4" base="$5" reason="$6" detail="$7"
  local started siblings="" text failed_text fields=()
  started="$(newest_worker_field "$number" base 2>/dev/null)" || started=""
  if [ -n "$started" ] && git -C "$root" cat-file -e "$started^{commit}" 2>/dev/null; then
    siblings="$(integrated_ticket_numbers "$root" "$started..origin/$into" | awk -v n="$number" '$0 != n')"
  fi
  text="Tried to merge issue-$number into origin/$into at $base and handed it to triage."
  if [ -n "$siblings" ]; then
    text="$text Tickets landed after this ticket started: $(printf '#%s ' $siblings | sed 's/ $//')."
  else
    text="$text No sibling landing after this ticket started was found."
  fi
  if [ "$reason" = conflict ]; then
    text="$text Conflicted files: $(MMW_LIST="$detail" python3 -c 'import json, os; print(", ".join(json.loads(os.environ["MMW_LIST"])))')."
    fields=(--json-field "files=$detail")
  else
    failed_text="$(MMW_COMMANDS="$detail" python3 -c '
import json, os
rows = json.loads(os.environ["MMW_COMMANDS"])
print(" | ".join("{}: {}".format(row.get("command", "?"), row.get("tail", "")).rstrip()
                 for row in rows))
')"
    text="$text Failed checks: $failed_text."
    fields=(--json-field "commands=$detail")
  fi

  gh_ issue reopen "$number" >/dev/null 2>&1 \
    || { echo "dispatch: could not reopen #$number after its merge $reason" >&2; return 2; }
  gh_ issue edit "$number" --remove-label ready-for-agent --add-label needs-triage \
      --remove-assignee @me >/dev/null 2>&1 \
    || { echo "dispatch: #$number is open, but could not be labelled needs-triage and unassigned" >&2; return 2; }
  give_ticket_slot_back "$number" || true
  post_event "$number" ticket.bounced --ticket "$number" --spec "$spec" \
      --line "$text" --field "reason=$reason" --field "commit=$base" \
      --field "into=$into" "${fields[@]}" \
    || { echo "dispatch: #$number was handed to triage, but its ticket.bounced event was not written" >&2; return 2; }
  stop_live_ticket_agents "$number" \
    || echo "dispatch: #$number was bounced, but its sessions could not be read and stopped" >&2
}

# The repository web URL is presentation, not landing authority. Ask the tracker once
# per landing command; a failure removes only the links from the event's first line.
load_repo_url() {
  REPO_URL="$(gh_ repo view --json url -q .url 2>/dev/null | tr -d '[:space:]')"
  if [ -z "$REPO_URL" ]; then
    echo "dispatch: the tracker could not provide this repository's web URL; ticket.landed will be recorded without compare or commit links" >&2
  fi
}

# Find the first merge on the fetched base branch's first-parent line that introduced
# the passed commit. A direct fast-forward has no such merge and prints nothing.
landed_merge_and_base() {
  local root="$1" passed="$2" into="$3" candidate first_parent
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    first_parent="$(git -C "$root" rev-parse "$candidate^1" 2>/dev/null)" || continue
    if git -C "$root" merge-base --is-ancestor "$passed" "$candidate" \
       && ! git -C "$root" merge-base --is-ancestor "$passed" "$first_parent"; then
      printf '%s\t%s\n' "$candidate" "$first_parent"
      return 0
    fi
  done < <(git -C "$root" rev-list --first-parent --reverse --merges \
            "origin/$into" 2>/dev/null)
}

# Count commits on one branch copy that the fetched base branch does not contain.
commits_outside_base() {
  git -C "$1" rev-list --count "origin/$3..$2" 2>/dev/null
}

# Remove the local and origin copies of a landed ticket branch. Both containment
# decisions use refs from the fetch that prepared the merge worktree; each copy can be
# kept independently, and the remote deletion is leased to that fetched tip.
delete_landed_ticket_branch() {
  local root="$1" number="$2" into="$3" branch remote_ref remote_tip ahead output probe_rc

  branch="$(ticket_branch "$number")"
  [[ "$branch" =~ ^issue-[0-9]+$ ]] || return 0
  [ "$branch" != "$into" ] || return 0
  remote_ref="refs/remotes/origin/$branch"

  if git -C "$root" worktree list --porcelain \
       | grep -Fx "branch refs/heads/$branch" >/dev/null; then
    echo "dispatch: keeping $branch because a worktree still has it checked out" >&2
    return 0
  fi

  if git -C "$root" show-ref --verify --quiet "refs/heads/$branch"; then
    ahead="$(commits_outside_base "$root" "refs/heads/$branch" "$into")" || ahead=""
    if [ -z "$ahead" ]; then
      echo "dispatch: keeping local $branch because its containment in origin/$into could not be checked" >&2
    elif [ "$ahead" -ne 0 ]; then
      echo "dispatch: keeping local $branch because it has $ahead commit(s) not in origin/$into" >&2
    elif ! output="$(git -C "$root" branch -D "$branch" 2>&1)"; then
      echo "dispatch: could not delete local $branch: $(printf '%s' "$output" | tail -2 | tr '\n' ' '); delete it manually with: git branch -D $branch" >&2
    fi
  fi

  git -C "$root" show-ref --verify --quiet "$remote_ref" || return 0
  remote_tip="$(git -C "$root" rev-parse "$remote_ref")"
  ahead="$(commits_outside_base "$root" "$remote_ref" "$into")" || ahead=""
  if [ -z "$ahead" ]; then
    echo "dispatch: keeping origin/$branch because its containment in origin/$into could not be checked" >&2
    return 0
  fi
  if [ "$ahead" -ne 0 ]; then
    echo "dispatch: keeping origin/$branch because it has $ahead commit(s) not in origin/$into" >&2
    return 0
  fi
  if output="$(git -C "$root" push \
      "--force-with-lease=refs/heads/$branch:$remote_tip" origin --delete "$branch" 2>&1)"; then
    return 0
  fi
  git -C "$root" ls-remote --exit-code origin "refs/heads/$branch" >/dev/null 2>&1
  probe_rc=$?
  if [ "$probe_rc" -eq 2 ]; then
    return 0
  fi
  [ "$probe_rc" -eq 0 ] \
    || output="$output The remote could not be checked after the failed deletion."
  echo "dispatch: could not delete origin/$branch: $(printf '%s' "$output" | tr '\n' ' '); after confirming its tip is contained in origin/$into, delete it manually with: git push origin --delete $branch" >&2
}

# Whether the ticket's complete event fold currently says it is landed.
ticket_is_landed() {
  local folded
  folded="$(ticket_events "$1" fold)" || return 1
  printf '%s\n' "$folded" | python3 -c '
import json, sys
raise SystemExit(0 if json.load(sys.stdin).get("landed") else 1)
'
}

# Release one-ticket resources, archive the workspace, record the landing, then remove
# branch copies only if both preceding state transitions succeeded.
finish_landing() {
  local root="$1" number="$2" spec="$3" into="$4" passed="$5"
  local merge_commit="$6" base="$7" mode="$8" archived=0
  if [ "$mode" = land ]; then
    gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1 \
      || echo "land: could not give #$number's claim back" >&2
    post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
        --line "Gave the claim on #$number back: its work is over" --field reason=landed \
      || echo "land: #$number's claim is given back, but its ticket.released event was not written" >&2
  fi
  archive_workspace "$number" && archived=1
  if record_landed "$number" "$spec" "$into" "$passed" "$merge_commit" "$base"; then
    [ "$archived" -eq 0 ] || delete_landed_ticket_branch "$root" "$number" "$into"
  fi
}

# Merge the exact ticket.passed commit, check the result, then fast-forward origin.
# 0 merged, 1 bounced, 2 could not complete, 3 was already in origin.
land_one_via_origin() {
  local root="$1" number="$2" spec="$3" into="$4" passed="$5" mode="${6:-advance}"
  local attempt merge_root base merge_commit landed_base rc files failed push_error=""
  for ((attempt = 1; attempt <= MERGE_TRIES; attempt++)); do
    prepare_merge_worktree "$root" "$into" || return 2
    merge_root="$MERGE_ROOT"
    base="$(git -C "$merge_root" rev-parse "origin/$into")"
    if git -C "$merge_root" merge-base --is-ancestor "$passed" "origin/$into"; then
      merge_commit=""
      landed_base=""
      IFS=$'\t' read -r merge_commit landed_base \
        < <(landed_merge_and_base "$merge_root" "$passed" "$into") || true
      finish_landing "$root" "$number" "$spec" "$into" "$passed" \
        "$merge_commit" "$landed_base" "$mode"
      release_merge_lock
      return 3
    fi
    if ! git -C "$merge_root" merge --no-ff -m "Merge branch 'issue-$number'" "$passed" >/dev/null 2>&1; then
        if git -C "$merge_root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
          files="$(git -C "$merge_root" diff --name-only --diff-filter=U \
            | python3 -c 'import json, sys; print(json.dumps([l.rstrip("\n") for l in sys.stdin if l.strip()]))')"
          git -C "$merge_root" merge --abort >/dev/null 2>&1 || true
          git -C "$merge_root" reset --hard "origin/$into" >/dev/null
          if ! bounce_ticket "$merge_root" "$number" "$spec" "$into" "$base" conflict "$files"; then
            release_merge_lock
            return 2
          fi
          release_merge_lock
          return 1
        fi
        release_merge_lock
        [ "$attempt" -lt "$MERGE_TRIES" ] && { sleep 2; continue; }
        echo "dispatch: could not merge ticket.passed commit $passed for #$number after $MERGE_TRIES tries" >&2
        return 2
    fi
    merge_commit="$(git -C "$merge_root" rev-parse HEAD)"

    if git -C "$merge_root" merge-base --is-ancestor "origin/$into" "$passed" \
       && repo_checks_met "$number" "$passed"; then
      :
    else
      run_merge_checks "$merge_root" "$into"; rc=$?
      if [ "$rc" -eq 3 ]; then
        echo "dispatch: 没有检查：.mmw/target.json 没声明 checks" >&2
      elif [ "$rc" -eq 1 ]; then
        failed="$(MMW_CHECKS_JSON="$MERGE_CHECKS_JSON" python3 -c '
import json, os
value = json.loads(os.environ["MMW_CHECKS_JSON"])
rows = value.get("failed") or []
if value.get("problem"):
    rows.append({"command": ".mmw/target.json", "tail": value["problem"]})
print(json.dumps(rows, separators=(",", ":")))
')"
        git -C "$merge_root" reset --hard "origin/$into" >/dev/null
        if ! bounce_ticket "$merge_root" "$number" "$spec" "$into" "$base" checks "$failed"; then
          release_merge_lock
          return 2
        fi
        release_merge_lock
        return 1
      elif [ "$rc" -ne 0 ]; then
        echo "dispatch: could not run repository checks for #$number" >&2
        release_merge_lock
        return 2
      fi
    fi

    if push_error="$(git -C "$merge_root" push origin "HEAD:$into" 2>&1)"; then
      finish_landing "$root" "$number" "$spec" "$into" "$passed" \
        "$merge_commit" "$base" "$mode"
      release_merge_lock
      return 0
    fi
    release_merge_lock
    [ "$attempt" -lt "$MERGE_TRIES" ] && continue
  done
  echo "dispatch: the fast-forward push of #$number to origin/$into was rejected after $MERGE_TRIES merge attempts; nothing was force-pushed: $(printf '%s' "$push_error" | tail -2 | tr '\n' ' ')" >&2
  return 2
}

# Record on ticket <n> that its passed commit is in the base branch now. Its events then show it
# landed, and that — not its closing — is what lets the tickets it blocks start: a
# ticket is cut from the base branch and has to find its blockers' work there.
record_landed() {
  local number="$1" spec="${2:-}" into="$3" commit="$4" merge="${5:-}" base="${6:-}" branch line
  local -a fields
  branch="$(ticket_branch "$number")"
  line="Landed $branch into $into"
  if [ -n "$REPO_URL" ] && [ -n "$merge" ] && [ -n "$base" ]; then
    line="$line: $REPO_URL/compare/$base...$merge (merge commit $REPO_URL/commit/$merge)"
  elif [ -n "$REPO_URL" ] && [ -z "$merge" ]; then
    line="$line: $REPO_URL/commit/$commit"
  fi
  fields=(--field "branch=$branch" --field "into=$into" --field "commit=$commit")
  [ -z "$merge" ] || fields+=(--field "merge=$merge")
  [ -z "$base" ] || fields+=(--field "base=$base")
  if ! post_event "$number" ticket.landed --ticket "$number" --spec "$spec" \
      --line "$line" "${fields[@]}"; then
    echo "dispatch: $commit is in origin/$into, but the ticket.landed event on #$number was not written; the tickets it blocks stay blocked until the next advance or land writes it" >&2
    return 1
  fi
}

advance() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to merge into"

  export MMW_SPEC="$spec"
  load_repo_url

  # A night that is not open has no relay, so a ticket landing would wake nobody.
  local watched
  watched="$(relay_watches "" "$spec" 2>&1)" \
    || refuse "the night on #$spec is not open: ${watched#relay: }. Nothing would wake you when a ticket lands, so nothing was merged or started; run open $spec first"

  # A reviewer can return a ticket while its worker session is still present. The
  # returned event gives the ticket back to triage; the next advance ends every
  # named session without removing the worktree that triage will inspect.
  stop_returned_ticket_agents "$spec" \
    || echo "dispatch: could not finish checking returned tickets under #$spec" >&2

  # The first plan says what to merge and which claims to give back. Its stderr repeats
  # in the second plan, which is the one read for what to start, so it is shown only
  # when the plan could not be made at all.
  local plan plan_err
  plan_err="$(mktemp)"
  plan="$(python3 "$STATUS" --advance-plan "$spec" 2>"$plan_err")" \
    || { cat "$plan_err" >&2; rm -f "$plan_err"; refuse "could not read the batch under #$spec"; }
  rm -f "$plan_err"

  local merged=0 skipped=0 bounced=0 number passed into rc
  for number in $(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }'); do
    passed="$(ticket_passed_commit "$number")" \
      || refuse "#${number}'s ticket.passed event carries no usable commit"
    into="$(ticket_into "$number" "$spec")" \
      || refuse "#${number}'s events carry no usable base branch"
    land_one_via_origin "$root" "$number" "$spec" "$into" "$passed"
    rc=$?
    case "$rc" in
      0)
        merged=$((merged + 1))
        echo "merged issue-$number into origin/$into" >&2
        ;;
      1) bounced=$((bounced + 1)) ;;
      3) skipped=$((skipped + 1)) ;;
      *) refuse "could not land #$number into origin/$into after $MERGE_TRIES tries" ;;
    esac
  done

  # A claim whose worker is gone keeps its ticket off the frontier for good: only the
  # closeout and the hand back to triage ever give a claim back, and the frontier takes
  # unassigned tickets alone. The plan names a claim only when an event on the ticket
  # has ended every hold on it — a retraction, a loss, a landing, a hand back, a release
  # or a suspension — so a worker started on any runner, on any machine, keeps its
  # claim, and so does one that claimed and has not had its start recorded yet.
  # `--remove-assignee @me` is the whole write, so a ticket a person took for themselves
  # is left exactly as it is.
  local released=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      released=$((released + 1))
      echo "released the claim on #$number: it is open in the agent queue and an event on it ended its worker's hold, so the worker that claimed it is gone" >&2
      give_ticket_slot_back "$number" || true
      post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
          --line "Gave the claim on #$number back: an event on it ended its worker's hold" \
          --field reason=worker-lost \
        || echo "dispatch: the claim on #$number is given back, but its ticket.released event was not written" >&2
    else
      echo "dispatch: could not take the claim off #$number, so it stays off the frontier" >&2
    fi
  done

  # What to start is read again, now that the merges above are recorded as landed and
  # the claims given back: a merge that could not happen and wrote no `ticket.landed`
  # left no `ticket.landed`, so the tickets it blocks stay blocked.
  plan="$(python3 "$STATUS" --advance-plan "$spec")" \
    || refuse "could not read the batch under #$spec again after its merges, so nothing was started"

  # Every ticket on the frontier is started: how many work at once is the frontier's
  # answer alone. How many run the product at once is `instance.max`'s, and it is asked
  # at the first run of each worker's criteria that needs the product, not here —
  # writing code takes no slot, so a worker is never kept from its code by a port.
  local started=0 refused=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    if bash "$SELF" ${TOOLS_ARGS[@]+"${TOOLS_ARGS[@]}"} start "$number" worker; then
      started=$((started + 1))
    else
      refused=$((refused + 1))
    fi
  done

  echo "advance #$spec: merged $merged, already in $skipped, bounced $bounced, released $released, started $started, refused $refused" >&2
  sweep_orphan_merge_worktrees "$root" \
    || echo "dispatch: could not sweep orphan merge worktrees after advancing #$spec" >&2
  # A refused start is its own exit code. Read as success it ends the main agent's turn,
  # and when nothing else of the batch is running no wake will ever come: the ticket sits
  # on the frontier, never started, and the night stops there without a word.
  [ "$refused" -eq 0 ] || exit 4
}

# ------------------------------------------------------------------ landing

# Land one ticket.
#
# Landing is what closing a ticket does not do: merge the passed commit and record
# `ticket.landed` on it, end every session its events name through that session's
# runner, remove the worktree with git, give the slot back, and give the claim back
# (`ticket.released`, reason `landed`). `advance` does it for a
# batch after a merge; this does it for one ticket, and asks for a ticket number
# rather than a spec — which is the whole point. A ticket dispatched outside a
# night belongs to no spec, so before this there was no command it could be
# landed with, and its agents, its worktree and its slot stayed until somebody
# noticed.
#
# Order is fixed: the worktree directory is where the product's stop command
# lives, so a passed commit not yet in origin has to be merged first or the work has to
# be rebuilt from the ticket branch to get it back. Agents are archived in the same
# step as the worktree, after that merge.
land_tickets() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to land into"
  load_repo_url

  local -a numbers=("$@")

  local plan
  plan="$(python3 "$STATUS" --land-plan "${numbers[@]}")" \
    || refuse "could not read $(printf '#%s ' "${numbers[@]}")from the tracker"

  local merged=0 already=0 bounced=0 kept=0 failed=0 number passed into archive_into rc spec
  local -a landed_numbers=() bounced_numbers=()
  while IFS= read -r number; do
    [ -n "$number" ] || continue
    passed="$(ticket_passed_commit "$number")" \
      || { echo "land: #$number has no usable ticket.passed commit" >&2; failed=$((failed + 1)); continue; }
    spec="$(ticket_spec "$number")"
    into="$(ticket_into "$number" "$spec")" \
      || { echo "land: #$number has no base branch in its events" >&2; failed=$((failed + 1)); continue; }
    land_one_via_origin "$root" "$number" "$spec" "$into" "$passed" land
    rc=$?
    case "$rc" in
      0)
        landed_numbers+=("$number")
        merged=$((merged + 1))
        ;;
      1) bounced=$((bounced + 1)); bounced_numbers+=("$number") ;;
      3) already=$((already + 1)); landed_numbers+=("$number") ;;
      *) failed=$((failed + 1)) ;;
    esac
  done < <(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }')

  # A handed-back ticket has no MERGE line, but land still gives back a claim left on
  # it and preserves its standing worktree for the next start.
  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    case " ${landed_numbers[*]-} ${bounced_numbers[*]-} " in *" $number "*) continue ;; esac
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      give_ticket_slot_back "$number" || true
      post_event "$number" ticket.released --ticket "$number" --spec "$(ticket_spec "$number")" \
          --line "Gave the claim on #$number back: its work is over" --field reason=landed \
        || echo "land: #$number's claim is given back, but its ticket.released event was not written" >&2
    else
      echo "land: could not give #$number's claim back" >&2
    fi
  done

  # A closed ticket with no pass is not silently archived while its branch still has
  # work that origin/<into> does not contain.
  for number in $(printf '%s\n' "$plan" | awk '$1 == "ARCHIVE" { print $2 }'); do
    case " ${landed_numbers[*]-} ${bounced_numbers[*]-} " in *" $number "*) continue ;; esac
    archive_into="$(ticket_into "$number" "$(ticket_spec "$number")")" \
      || { echo "land: #$number has no base branch in its events; not archiving it" >&2; failed=$((failed + 1)); continue; }
    fetch_origin "$root" \
      || { echo "land: could not fetch origin before deciding whether to archive #$number" >&2; failed=$((failed + 1)); continue; }
    if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null \
       && ! git -C "$root" merge-base --is-ancestor "refs/heads/issue-$number" \
            "origin/${archive_into}" 2>/dev/null; then
      echo "land: #$number is closed but issue-$number is not in origin/${archive_into}; not archiving it" >&2
      failed=$((failed + 1))
      continue
    fi
    if archive_workspace "$number"; then
      if ticket_is_landed "$number"; then
        delete_landed_ticket_branch "$root" "$number" "$archive_into"
      fi
    else
      failed=$((failed + 1))
    fi
  done

  while IFS= read -r line; do
    [ -n "$line" ] || continue
    echo "  $line" >&2
    kept=$((kept + 1))
  done < <(printf '%s\n' "$plan" | sed -n 's/^HOLD \(.*\)$/#\1/p')

  # A ticket that needs nothing is named too. Landing one and landing none print the
  # same tally otherwise, and the difference is the whole question the caller asked.
  local nothing=0
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    echo "  $line" >&2
    nothing=$((nothing + 1))
  done < <(printf '%s\n' "$plan" | sed -n 's/^NOTHING \([0-9]*\) \(.*\)$/#\1 needs nothing: \2/p')

  echo "land: merged $merged, already in $already, bounced $bounced, still working $kept, already landed $nothing, failed $failed" >&2

  # `land <n>` is the whole ending of a ticket outside a night, so the watch `open-ticket`
  # opened for it closes here, and the relay with it when it watched nothing else. A
  # night's watch is not this one and is left alone.
  local relay_left=0
  if [ "$kept" -eq 0 ]; then
    stop_relay --tickets "${numbers[0]}"
    [ "$?" = 1 ] && relay_left=1
  fi
  sweep_orphan_merge_worktrees "$root" \
    || echo "land: could not sweep orphan merge worktrees" >&2
  [ "$failed" -eq 0 ] && [ "$relay_left" -eq 0 ] || return 1
}

# ------------------------------------------------------------------ suspend

# The prose of the `spec.suspended` event a ticket still in the agent queue gets.
suspend_text() {
  local spec="$1" when="$2" ident="$3" number="$4"
  printf '%s\n' \
    "The night on spec #$spec was suspended at $when, so this ticket has no verdict: nothing here says whether its work is finished."
  if [ -n "$ident" ]; then
    printf '%s\n' "Interrupted: $ident. Its tracked edits were committed and issue-$number was pushed to origin before the hold ended. The batch is taken up again where it stands with advance."
  else
    printf '%s\n' "No session of ours was working on it at that moment. It keeps its label, so the next advance of #$spec starts it."
  fi
}

# Suspend the night without throwing its work away.
#
# Five things happen: every session still holding a ticket of the batch — worker,
# reviewer or verifier — that is not already stopped is ended through its own runner's
# `stop`, which interrupts a running agent (workspace and branch stay); every ticket
# still in the agent queue gets a `spec.suspended` event,
# and so does the spec; every OPEN ready-for-agent ticket assigned to this pipeline's
# account has that claim given back, with a `ticket.released` event (reason
# `suspended`); and every lease slot the batch holds is given back. A batch dispatched
# again from scratch would throw the night's work away along with the night; `advance`
# after this takes the same workspaces up where they stand.
#
# A ticket one of whose sessions could not be stopped gets none of that: `spec.suspended`
# would close that session on the ticket's events while it still runs, and the next
# `advance` would start a second worker beside it. It keeps its claim and its slot, and
# is counted as left behind.
#
# `lease.py` refuses a slot something still listens on, and that refusal is reported
# rather than forced: taking a slot off a live process is the same act as ending it.
suspend_night() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local root git_dir
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so this night's workspaces have no name"
  git_dir="$(git -C "$root" rev-parse --absolute-git-dir 2>/dev/null)"
  [ -n "$git_dir" ] || refuse "not inside a git repository, so this night's workspaces have no name"

  local grades queued batch left=0
  grades="$(python3 "$STATUS" --worker-grades "$spec")" \
    || refuse "could not read the batch under #$spec"
  queued="$(printf '%s\n' "$grades" | awk '$1 == "GRADE" { print $2 }')"
  batch="$(printf '%s\n' "$grades" | awk '$1 == "BATCH" { print $2 }')"

  # Every session still holding a ticket of the batch — its worker, and a reviewer or a
  # verifier whose result is not in — is ended through its own runner's `stop`, which
  # interrupts it mid-turn: a verifier left running keeps running the product, and the
  # slot is given back under it below. One already shown to be stopped is left alone. A
  # ticket whose events cannot be read, or one of whose sessions will not stop, is left as
  # it is: nobody can say nothing still runs on it.
  local live="" number ident name sessions stopped=0 kept="" push_failed=""
  for number in $batch; do
    if ! sessions="$(ticket_events "$number" live)"; then
      echo "dispatch: could not read #$number's events, so whether a session still runs on it is unknown; it is left as it is" >&2
      kept="$kept $number"
      left=$((left + 1))
      continue
    fi
    while IFS=$'\t' read -r name ident; do
      [ -n "$ident" ] || continue
      use_runner "$name"
      [ "$(runner liveness "$ident")" = stopped ] && continue
      if runner stop "$ident"; then
        stopped=$((stopped + 1))
        live="$live$number"$'\t'"$ident"$'\n'
      else
        echo "dispatch: could not stop $ident on #$number, so it is still running" >&2
        kept="$kept $number"
        left=$((left + 1))
        break
      fi
    done <<<"$sessions"
  done

  # A stopped session commits and pushes its ticket branch before its event hold, claim or slot is
  # released. If commit or push fails, that ticket stays held exactly as a session that
  # could not be stopped does; the rest of the night can still be suspended.
  local cwd left_by
  for number in $queued; do
    case " $kept " in *" $number "*) continue ;; esac
    printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { found=1 } END { exit !found }' \
      || continue
    cwd="$(workspace_cwd_for "$number")"
    [ -n "$cwd" ] || continue
    left_by="$(last_worker_on_ticket "$number")" || left_by=""
    [ -n "$left_by" ] || left_by="the suspended work on #$number"
    if ! keep_unfinished_work "$number" "$cwd" "$left_by" \
        || ! push_ticket_branch "$number" "$cwd"; then
      echo "dispatch: #$number could not commit and push its ticket branch, so its workspace, claim, slot and event hold are kept" >&2
      kept="$kept $number"
      push_failed="$push_failed $number"
      left=$((left + 1))
    fi
  done

  local when commented=0
  when="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  post_event "$spec" spec.suspended --spec "$spec" --line "NIGHT SUSPENDED #$spec" \
      --field "suspended_at=$when" \
    || { echo "dispatch: could not write the spec.suspended event on #$spec" >&2; left=$((left + 1)); }
  for number in $queued; do
    case " $kept " in *" $number "*) continue ;; esac
    ident="$(printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { ids = ids sep $2; sep = ", " } END { print ids }')"
    local -a interrupted=()
    [ -z "$ident" ] || interrupted=(--field "interrupted=$ident")
    if post_event "$number" spec.suspended --ticket "$number" --spec "$spec" \
         --line "NIGHT SUSPENDED #$spec" --text-file <(suspend_text "$spec" "$when" "$ident" "$number") \
         --field "suspended_at=$when" ${interrupted[@]+"${interrupted[@]}"}; then
      commented=$((commented + 1))
    else
      echo "dispatch: could not comment on #$number, so nothing on it says the night was suspended" >&2
      left=$((left + 1))
    fi
  done

  local claims=0
  for number in $queued; do
    [ -n "$number" ] || continue
    case " $kept " in *" $number "*) continue ;; esac
    give_claim_back "$number"
    case "$?" in
      0)
        claims=$((claims + 1))
        echo "gave back the claim on #$number: the night is suspended, so the next advance can start it again" >&2
        post_event "$number" ticket.released --ticket "$number" --spec "$spec" \
            --line "Gave the claim on #$number back: the night on #$spec is suspended" \
            --field reason=suspended \
          || echo "dispatch: the claim on #$number is given back, but its ticket.released event was not written" >&2
        ;;
      2)
        echo "dispatch: could not give back the claim on #$number" >&2
        left=$((left + 1))
        ;;
    esac
  done

  local back=0 rc
  if [ -f "$LEASE" ]; then
    [ -n "$(worktrees_root)" ] \
      || echo "dispatch: no workspace of this checkout is standing, so a lease can be matched to a ticket only through a standing workspace; python3 $LEASE list shows what is still held, and claim reclaims a lease whose directory is gone" >&2
    for number in $batch; do
      # A worker still running will start the product again, and the `stop` in between
      # tears up the record of what it started — leaving processes that stop can no
      # longer reach. So a ticket whose worker survived the archive keeps its slot: it
      # is already counted as left behind, and this only says why.
      case " $kept " in
        *" $number "*)
          case " $push_failed " in
            *" $number "*) echo "dispatch: #$number keeps its slot because its ticket branch could not be committed and pushed; reconcile issue-$number with origin/issue-$number, then suspend again" >&2 ;;
            *) echo "dispatch: #$number keeps its slot while a session may still run; stopping a product under a live session leaves processes its own stop cannot reach. End that agent, then suspend again" >&2 ;;
          esac
          continue
          ;;
      esac
      cwd="$(workspace_cwd_for "$number")"
      [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
      [ -n "$cwd" ] || continue
      give_slot_back "$cwd"
      rc=$?
      case "$rc" in
        0) back=$((back + 1)) ;;
        1) left=$((left + 1)) ;;
      esac
    done
  else
    echo "dispatch: no lease.py in any --tools directory, so this night's slots were not given back and the next night will read this machine as fuller than it is; pass --tools <the drive-target skill's scripts directory>" >&2
    left=$((left + 1))
  fi

  # A suspended night wakes nobody: its watch closes with it.
  stop_relay --spec "$spec"
  case "$?" in
    1) left=$((left + 1)) ;;
    3) echo "dispatch: the relay running for this repository does not watch #$spec, so it was left running" >&2 ;;
  esac

  echo "suspend #$spec: stopped $stopped, commented $commented, slots given back $back, claims given back $claims"
  [ "$left" -eq 0 ] || exit 1
}

# ------------------------------------------------------------------ reverify / summary

# The red reverify of ticket <n> on commit <c>: prints the criteria it left unmet, space
# separated — the `failed` field of the newest reverify `ticket.checked` — and returns 0
# only when that event is a run of <c> whose result is not `met`. Returns 1 when the
# ticket carries no such run, which is not a red ticket: nothing on it says what ran.
# Returns 2 when the ticket's events could not be read.
red_reverify_of() {
  local number="$1" commit="$2" line field ran="" result=""
  local -a failed=()
  line="$(ticket_events "$number" checked --run reverify)" || return 2
  for field in $line; do
    case "$field" in
      commit=*) ran="${field#commit=}" ;;
      result=*) result="${field#result=}" ;;
      failed=*) [ "${field#failed=}" = "-" ] || IFS=',' read -r -a failed <<<"${field#failed=}" ;;
    esac
  done
  [ "$ran" = "$commit" ] && [ -n "$result" ] && [ "$result" != met ] || return 1
  printf '%s\n' "${failed[*]+"${failed[*]}"}"
}

reverify_spec() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac
  [ -f "$VERIFY" ] || refuse "no verify-ticket.py in any --tools directory; pass --tools <the verify-ticket skill's scripts directory>"

  local caller_root root git_dir commit plan number rc printed ids login into first
  caller_root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$caller_root" ] || refuse "not inside a git repository"
  git_dir="$(git -C "$caller_root" rev-parse --git-common-dir)"

  plan="$(python3 "$STATUS" --reverify-plan "$spec")" \
    || refuse "could not read the batch under #$spec"
  first="$(printf '%s\n' "$plan" | awk '$1 == "REVERIFY" { print $2; exit }')"
  if [ -n "$first" ]; then
    into="$(ticket_into "$first" "$spec")" \
      || refuse "#${first}'s events carry no base branch for reverify"
    prepare_merge_worktree "$caller_root" "$into" || exit 2
    root="$MERGE_ROOT"
  else
    root="$caller_root"
    into=""
  fi
  commit="$(git -C "$root" rev-parse HEAD)"

  local green=0 red=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "REVERIFY" { print $2 }'); do
    # `--tools` is forwarded because the judges of a criterion are named bare and are
    # found only in the directories it names. Without it every interface criterion of
    # every ticket fails `command not found`, and the branch below would reopen and hand
    # back a whole night of finished work for a fault in this command line.
    # The run writes its own `ticket.checked` (run `reverify`, actor `main`), which is the
    # whole record of a green one.
    printed="$(cd "$root" && env MMW_BASE_REF="origin/$into" \
      python3 "$VERIFY" "$number" --reverify --actor main ${TOOLS_ARGS[@]+"${TOOLS_ARGS[@]}"} 2>&1)"
    rc=$?
    printf '%s\n' "$printed"
    # Red is exit 1 and a reverify ticket.checked of this HEAD that is not met; every
    # other answer — 2 the run could not start, 3 it waited for a product slot and none
    # came free, 4 its result could not be written, a crash, or a 1 the ticket holds no
    # red run of HEAD for — says nothing about the ticket. Reading one as a red ticket is
    # how one broken invocation reopens a batch of landed work.
    ids=""
    if [ "$rc" -eq 1 ]; then
      ids="$(red_reverify_of "$number" "$commit")" || rc=5
    fi
    if [ "$rc" -ne 0 ] && [ "$rc" -ne 1 ]; then
      echo "dispatch: #$number could not be re-run on $commit (exit $rc, or no red run of it is recorded on the ticket), so nothing was judged; the rest of this reverify is skipped" >&2
      exit 2
    fi
    if [ "$rc" -eq 0 ]; then
      green=$((green + 1))
    else
      red=$((red + 1))
      echo "dispatch: #$number reverify failed" >&2
      gh_ issue reopen "$number" >/dev/null 2>&1
      login="$(gh_ issue view "$number" --json assignees 2>/dev/null | python3 -c '
import json, sys
try:
    rows = json.load(sys.stdin).get("assignees") or []
except Exception:
    rows = []
print((rows[0].get("login") or "") if rows else "")
')"
      if [ -n "$login" ]; then
        gh_ issue edit "$number" --add-label needs-triage --remove-assignee "$login" >/dev/null
      else
        gh_ issue edit "$number" --add-label needs-triage >/dev/null
      fi
      post_event "$number" ticket.regressed --ticket "$number" --spec "$spec" \
          --line "Reverify on $commit failed${ids:+: $ids}; reopened for triage" \
          --field "commit=$commit" \
          --json-field "failed=$(printf '%s' "$ids" | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read().split()))')" \
        || echo "dispatch: #$number is reopened, but its ticket.regressed event was not written, so its events still read as passed and landed" >&2
    fi
  done

  printf '%s %s\n' "$green" "$red" > "$git_dir/mmw-reverify-$spec"
  release_merge_lock
  echo "reverify #$spec: $green green, $red red"
  [ "$red" -eq 0 ] || exit 1
}

summary_spec() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local body extra git_dir
  body="$(python3 "$STATUS" --summary "$spec")"
  git_dir="$(git rev-parse --git-common-dir 2>/dev/null || true)"
  extra=""
  if [ -n "$git_dir" ] && [ -f "$git_dir/mmw-reverify-$spec" ]; then
    extra="$(awk '{ printf "Reverify: %s/%s\n", $1, $2 }' "$git_dir/mmw-reverify-$spec")"
  fi
  if [ -n "$extra" ]; then
    body="$(printf '%s\n%s\n' "$body" "$extra")"
  fi
  local first rest
  first="$(printf '%s\n' "$body" | head -n 1)"
  rest="$(printf '%s\n' "$body" | tail -n +2)"
  post_event "$spec" spec.closed --spec "$spec" --line "$first" \
      --text-file <(printf '%s\n' "$rest") \
      --field "date=$(date +%Y-%m-%d)" \
    || refuse "could not post the night summary on #$spec"
  printf '%s\n' "$body"

  # The night is over, and so is its watch: nothing wakes its sessions any more.
  stop_relay --spec "$spec"
  case "$?" in
    1)
      echo "dispatch: the summary is posted on #$spec and its watch is closed, and the relay, which watched nothing else, is still running (the reason is above)" >&2
      exit 1
      ;;
    3) echo "dispatch: the relay running for this repository does not watch #$spec, so it was left running" >&2 ;;
  esac
}

# ------------------------------------------------------------------ finish

spec_numbers() {
  local slug
  slug="$(repo_slug)" || return 2
  gh_ api --paginate "repos/$slug/issues?state=all&labels=mmw%3Aspec&per_page=100" \
    --jq '.[].number' 2>/dev/null
}

spec_children() {
  local spec="$1" slug
  slug="$(repo_slug)" || return 2
  gh_ api --paginate "repos/$slug/issues/$spec/sub_issues?per_page=100" --jq '.[].number' 2>/dev/null
}

finish_preflight() {
  local spec="$1" into="$2" specs children other active seen child state open="" rc
  newest_field "$spec" at spec.closed spec.opened >/dev/null 2>&1 \
    || { echo "dispatch: #$spec carries no spec.closed; run summary before finish" >&2; return 2; }

  specs="$(spec_numbers)" || {
    echo "dispatch: could not list specs while checking whether $into is still in use" >&2
    return 2
  }
  for other in $specs; do
    [ "$other" = "$spec" ] && continue
    active="$(newest_field "$other" into spec.opened spec.suspended spec.closed 2>/dev/null)"; rc=$?
    case "$rc" in
      0) ;;
      2) echo "dispatch: could not read #$other while checking open nights into $into" >&2; return 2 ;;
      3 | 4) active="" ;;
      *) echo "dispatch: could not decide whether #$other is an open night into $into" >&2; return 2 ;;
    esac
    if [ "$active" = "$into" ]; then
      echo "dispatch: #$other is another open night into $into; finish or suspend it before finish $spec" >&2
      return 2
    fi
  done

  for other in $specs; do
    seen="$(newest_field "$other" into spec.opened 2>/dev/null)"; rc=$?
    case "$rc" in
      0) ;;
      2) echo "dispatch: could not read #$other while finding specs that used $into" >&2; return 2 ;;
      3 | 4) seen="" ;;
      *) echo "dispatch: could not decide whether #$other used $into" >&2; return 2 ;;
    esac
    [ "$seen" = "$into" ] || continue
    children="$(spec_children "$other")" || {
      echo "dispatch: could not list #$other's tickets while checking tickets into $into" >&2
      return 2
    }
    for child in $children; do
      state="$(gh_ issue view "$child" --json state --jq .state 2>/dev/null)" || {
        echo "dispatch: could not read #$child while checking tickets into $into" >&2
        return 2
      }
      [ "$state" = CLOSED ] || open="$open #$child"
    done
  done
  if [ -n "$open" ]; then
    echo "dispatch: tickets still open on $into:${open}; close them before finish $spec" >&2
    return 2
  fi
}

record_spec_merged() {
  local spec="$1" into="$2" project="$3" merge="$4" base="$5" line
  line="Merged $into into $project"
  if [ -n "$REPO_URL" ]; then
    line="$line: $REPO_URL/compare/$base...$merge (merge commit $REPO_URL/commit/$merge)"
  fi
  post_event "$spec" spec.merged --spec "$spec" --line "$line" \
    --field "into=$into" --field "project=$project" --field "merge=$merge" --field "base=$base"
}

clean_base_worktrees() {
  local root="$1" into="$2" main path branch
  main="$(main_checkout)" || main=""
  while IFS=$'\t' read -r path branch; do
    [ "$branch" = "refs/heads/$into" ] || continue
    [ -n "$path" ] || continue
    if [ -n "$main" ] && [ "$(CDPATH='' cd "$path" 2>/dev/null && pwd -P)" = "$(CDPATH='' cd "$main" && pwd -P)" ]; then
      echo "dispatch: keeping the main checkout $path; switch it off $into, then run git branch -D $into" >&2
      continue
    fi
    case "$path" in "$main"/.worktrees/*) ;; *)
      echo "dispatch: keeping $path because it is outside $main/.worktrees" >&2
      continue ;;
    esac
    if [ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]; then
      echo "dispatch: keeping dirty worktree $path; clean it, then run git worktree remove $path" >&2
      continue
    fi
    git -C "$root" worktree remove "$path" >/dev/null 2>&1 \
      || echo "dispatch: could not remove $path; run git worktree remove $path" >&2
  done < <(git -C "$root" worktree list --porcelain | awk '
    /^worktree / { path=substr($0,10); branch="" }
    /^branch / { branch=substr($0,8); print path "\t" branch }
  ')
}

delete_base_branch() {
  local root="$1" into="$2" project="$3" remote="refs/remotes/origin/$into" tip ahead out rc
  if git -C "$root" show-ref --verify --quiet "refs/heads/$into"; then
    ahead="$(git -C "$root" rev-list --count "origin/$project..refs/heads/$into" 2>/dev/null)" || ahead=""
    if [ "$ahead" = 0 ]; then
      out="$(git -C "$root" branch -D "$into" 2>&1)" \
        || echo "dispatch: could not delete local $into: $out; run git branch -D $into" >&2
    else
      echo "dispatch: keeping local $into because its containment in origin/$project was not proved; after checking, run git branch -D $into" >&2
    fi
  fi
  git -C "$root" show-ref --verify --quiet "$remote" || return 0
  tip="$(git -C "$root" rev-parse "$remote")"
  ahead="$(git -C "$root" rev-list --count "origin/$project..$remote" 2>/dev/null)" || ahead=""
  if [ "$ahead" != 0 ]; then
    echo "dispatch: keeping origin/$into because its containment in origin/$project was not proved; after checking, run git push origin --delete $into" >&2
    return 0
  fi
  out="$(git -C "$root" push "--force-with-lease=refs/heads/$into:$tip" origin --delete "$into" 2>&1)" && return 0
  git -C "$root" ls-remote --exit-code origin "refs/heads/$into" >/dev/null 2>&1
  rc=$?
  [ "$rc" -eq 2 ] && return 0
  echo "dispatch: could not delete origin/$into: $(printf '%s' "$out" | tr '\n' ' '); run git push origin --delete $into" >&2
}

clean_base_merge_worktree() {
  local root="$1" into="$2" main dest state
  main="$(main_checkout)" || return 0
  dest="$main/.worktrees/merge-$(merge_slug "$into")"
  if [ -e "$dest" ]; then
    git -C "$root" worktree remove --force "$dest" >/dev/null 2>&1 \
      || echo "dispatch: could not remove $dest; run git worktree remove --force $dest" >&2
  fi
  state="$(repository_state_dir)" || return 0
  rm -f "$state/merge-$(merge_slug "$into").lock"
}

finish_cleanup() {
  local root="$1" into="$2" project="$3"
  fetch_origin "$root" || { echo "dispatch: merge was recorded, but origin could not be fetched for cleanup; run finish again" >&2; return 0; }
  clean_base_worktrees "$root" "$into"
  if git -C "$root" show-ref --verify --quiet "refs/remotes/origin/$into" \
     && ! git -C "$root" merge-base --is-ancestor "origin/$into" "origin/$project" 2>/dev/null; then
    echo "dispatch: keeping $into because origin/$project does not contain origin/$into; run finish again after reconciling the branches" >&2
  else
    delete_base_branch "$root" "$into" "$project"
  fi
  clean_base_merge_worktree "$root" "$into"
  sweep_orphan_merge_worktrees "$root" \
    || echo "dispatch: could not sweep orphan merge worktrees after finish" >&2
}

finish_spec() {
  local spec="$1" root into project merged merge base attempt rc out files failed
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository"
  into="$(newest_field "$spec" into spec.opened 2>/dev/null)" || into=""
  project="$(newest_field "$spec" project spec.opened 2>/dev/null)" || project=""
  [ -n "$project" ] || refuse "#${spec}'s spec.opened carries no project branch; run open $spec again before finish"
  [ -n "$into" ] || refuse "#${spec}'s spec.opened carries no base branch; run open $spec again before finish"
  finish_preflight "$spec" "$into" || exit 2
  load_repo_url

  merged="$(newest_field "$spec" merge spec.merged 2>/dev/null)" || merged=""
  if [ -n "$merged" ]; then
    finish_cleanup "$root" "$into" "$project"
    echo "finish #$spec: merge $merged was already recorded; cleanup checked"
    return 0
  fi

  for ((attempt = 1; attempt <= MERGE_TRIES; attempt++)); do
    prepare_merge_worktree "$root" "$project" || exit 2
    base="$(git -C "$MERGE_ROOT" rev-parse "origin/$project")"
    if ! git -C "$MERGE_ROOT" show-ref --verify --quiet "refs/remotes/origin/$into"; then
      if git -C "$root" show-ref --verify --quiet "refs/heads/$into" \
         && ! git -C "$root" merge-base --is-ancestor "refs/heads/$into" "origin/$project"; then
        release_merge_lock
        refuse "origin/$into is absent and the local $into is not contained in origin/$project; nothing was deleted"
      fi
      release_merge_lock
      finish_cleanup "$root" "$into" "$project"
      echo "finish #$spec: origin/$into was already absent; cleanup checked"
      return 0
    fi
    if git -C "$MERGE_ROOT" merge-base --is-ancestor "origin/$into" "origin/$project"; then
      merge=""
      IFS=$'\t' read -r merge base < <(landed_merge_and_base "$MERGE_ROOT" "origin/$into" "$project") || true
      if [ -n "$merge" ] && [ -n "$base" ]; then
        if ! record_spec_merged "$spec" "$into" "$project" "$merge" "$base"; then
          release_merge_lock
          refuse "origin/$project contains $into, but the spec.merged event on #$spec was not written; run finish again"
        fi
      fi
      release_merge_lock
      finish_cleanup "$root" "$into" "$project"
      echo "finish #$spec: origin/$project already contained $into; cleanup checked"
      return 0
    else
      if ! git -C "$MERGE_ROOT" merge --no-ff -m "Merge branch '$into'" "origin/$into" >/dev/null 2>&1; then
        files="$(git -C "$MERGE_ROOT" diff --name-only --diff-filter=U | paste -sd, -)"
        git -C "$MERGE_ROOT" merge --abort >/dev/null 2>&1 || true
        git -C "$MERGE_ROOT" reset --hard "origin/$project" >/dev/null
        release_merge_lock
        echo "dispatch: finish #$spec conflicts in ${files:-unknown files}; nothing was pushed or deleted" >&2
        exit 1
      fi
      merge="$(git -C "$MERGE_ROOT" rev-parse HEAD)"
      run_merge_checks "$MERGE_ROOT" "$project"; rc=$?
      if [ "$rc" -eq 1 ]; then
        failed="$(MMW_CHECKS_JSON="$MERGE_CHECKS_JSON" python3 -c 'import json,os; v=json.loads(os.environ["MMW_CHECKS_JSON"]); print(" | ".join((r.get("command") or ".mmw/target.json") + ": " + (r.get("tail") or v.get("problem") or "failed") for r in (v.get("failed") or [{}] if v.get("problem") else v.get("failed") or [])))')"
        git -C "$MERGE_ROOT" reset --hard "origin/$project" >/dev/null
        release_merge_lock
        echo "dispatch: finish #$spec repository checks failed: $failed; nothing was pushed or deleted" >&2
        exit 1
      elif [ "$rc" -eq 3 ]; then
        echo "dispatch: 没有检查：.mmw/target.json 没声明 checks" >&2
      elif [ "$rc" -ne 0 ]; then
        release_merge_lock
        refuse "could not run repository checks for finish #$spec"
      fi
      out="$(git -C "$MERGE_ROOT" push origin "HEAD:$project" 2>&1)"
      if [ "$?" -ne 0 ]; then
        release_merge_lock
        [ "$attempt" -lt "$MERGE_TRIES" ] && continue
        echo "dispatch: the fast-forward push to origin/$project was rejected after $MERGE_TRIES attempts; nothing was deleted: $(printf '%s' "$out" | tail -2 | tr '\n' ' ')" >&2
        exit 2
      fi
    fi
    if ! record_spec_merged "$spec" "$into" "$project" "$merge" "$base"; then
      release_merge_lock
      refuse "origin/$project contains $into, but the spec.merged event on #$spec was not written; run finish again"
    fi
    release_merge_lock
    finish_cleanup "$root" "$into" "$project"
    echo "finish #$spec: merged $into into origin/$project at $merge; cleanup checked"
    return 0
  done
}

# ------------------------------------------------------------------ route

# Make sure the repository has the layer label `$1`. A label the repository lacks makes
# every `gh issue edit --add-label` naming it fail, so the first issue of each layer
# creates it; one that already exists is left exactly as it is.
ensure_label() {
  local name="$1" color description out
  case "$name" in
    mmw:ticket) color=0e8a16; description="MMW layer: a ticket, one unit of work" ;;
    *) return 1 ;;
  esac
  out="$(gh_ label create "$name" --color "$color" --description "$description" 2>&1)" && return 0
  case "$out" in *"already exists"*) return 0 ;; esac
  echo "dispatch: the repository has no $name label and it could not be created: $out" >&2
  return 1
}

# Prints "<parent>" for issue <n>: the number of the issue the tracker records it under,
# or nothing when it records none. Non-zero when the tracker could not be asked.
parent_of() {
  local json
  json="$(gh_ issue view "$1" --json parent 2>/dev/null)" || return 2
  printf '%s' "$json" | python3 -c '
import json, sys
try:
    parent = (json.load(sys.stdin) or {}).get("parent") or {}
except Exception:
    raise SystemExit(2)
number = parent.get("number") if isinstance(parent, dict) else None
print(number if isinstance(number, int) else "")
'
}

# Route one child of a ticket, the closing pass's decision carried out: the child is
# closed (or, having become a ticket, moved), and a `child.closed` event naming how goes
# on the ticket it came from. That event is the one record of where the child went;
# the night summary counts findings by it.
#
#   fixed               the main agent fixed it in the recorded commit; closed as completed
#   stale               what it states no longer holds at HEAD; closed as not planned
#   became-ticket <m>   it is now ticket #<m>. When <m> is the child itself it stays open,
#                       its layer label goes from mmw:child to mmw:ticket, and its parent
#                       moves from the ticket to the spec — `verify-ticket.py` finds a
#                       ticket's spec through its direct parent alone, so a ticket left
#                       under a ticket would name that ticket as its spec. When <m> is
#                       another issue, the child is closed as a duplicate of it and #<m>
#                       gets the same label and the same parent.
#
# The ticket the child came from is named on the command line and must carry the
# `child.opened` for it; the spec is that event's `spec`. Both are facts fixed when the
# child was opened, and never read off the tree, which a became-ticket route itself
# changes — so a route cut short is run again as it was, and does only the steps not yet
# done: a child already closed is not closed twice, an issue already under the spec is
# not moved, and a child whose `child.closed` is on the ticket is routed already.
#
# Exit 0 routed and recorded, or already so. 1 the tracker took some of it and not the
# rest; stderr says which, nothing was undone, and the same command finishes it. 2
# nothing was done: the arguments are wrong, the ticket carries no `child.opened` for
# this child, the child was routed another way, or the tracker could not be asked.
route_child() {
  local ticket="$1" child="$2" resolution="$3" became="${4:-}"
  case "$ticket" in *[!0-9]* | "") refuse "the ticket number must be digits only, got $ticket" ;; esac
  case "$child" in *[!0-9]* | "") refuse "the child number must be digits only, got $child" ;; esac
  case "$resolution" in
    fixed | stale) [ -z "$became" ] || refuse "$resolution takes no ticket number" ;;
    became-ticket)
      case "$became" in *[!0-9]* | "") refuse "became-ticket needs the number of the ticket it became, digits only" ;; esac ;;
    *) refuse "the resolution is fixed, stale or became-ticket, got $resolution" ;;
  esac

  local opened kind spec done_resolution done_became
  opened="$(ticket_events "$ticket" child --child "$child")" \
    || refuse "could not read #$ticket's events, so whether it opened #$child is unknown; nothing was done"
  [ -n "$opened" ] \
    || refuse "#$ticket carries no child.opened for #$child, so #$child is not a child it opened; name the ticket that opened it. Nothing was done"
  IFS=$'\t' read -r kind spec done_resolution done_became <<<"$opened"
  [ "$spec" != "-" ] || spec=""
  if [ "$done_resolution" != "-" ]; then
    if [ "$done_resolution" = "$resolution" ] && { [ -z "$became" ] || [ "$done_became" = "$became" ]; }; then
      echo "route #$child: already routed $resolution${became:+ #$became}, recorded on #$ticket" >&2
      return 0
    fi
    refuse "#$child is already routed $done_resolution on #$ticket; nothing was done"
  fi
  if [ "$resolution" = became-ticket ] && [ -z "$spec" ]; then
    refuse "#$ticket's child.opened for #$child names no spec, so there is no spec for #$became to move under; nothing was done"
  fi

  local state
  state="$(gh_ issue view "$child" --json state --jq .state 2>/dev/null)" \
    || refuse "could not read #$child's state; nothing was done"

  local line
  case "$resolution" in
    fixed)
      [ "$state" = CLOSED ] || gh_ issue close "$child" --reason completed >/dev/null 2>&1 \
        || refuse "could not close #$child; nothing was recorded"
      line="Fixed #$child on the closing pass" ;;
    stale)
      [ "$state" = CLOSED ] || gh_ issue close "$child" --reason "not planned" >/dev/null 2>&1 \
        || refuse "could not close #$child; nothing was recorded"
      line="Closed #$child: what it states no longer holds" ;;
    became-ticket)
      ensure_label mmw:ticket || exit 2
      local current labels
      current="$(parent_of "$became")" || refuse "could not ask the tracker where #$became sits; nothing was done"
      labels="$(gh_ issue view "$became" --json labels --jq '.labels[].name' 2>/dev/null)" \
        || refuse "could not read #$became's labels; nothing was done"
      local -a edit=()
      printf '%s\n' "$labels" | grep -qx 'mmw:ticket' || edit+=(--add-label mmw:ticket)
      [ "$current" = "$spec" ] || edit+=(--parent "$spec")
      if printf '%s\n' "$labels" | grep -qx 'mmw:child'; then
        edit+=(--remove-label mmw:child)
      fi
      if [ "${#edit[@]}" -gt 0 ]; then
        gh_ issue edit "$became" "${edit[@]}" >/dev/null 2>&1 \
          || refuse "could not make #$became a ticket under #$spec; nothing was recorded"
      fi
      if [ "$became" != "$child" ] && [ "$state" != CLOSED ]; then
        if ! gh_ issue close "$child" --duplicate-of "$became" >/dev/null 2>&1; then
          echo "dispatch: #$became is a ticket under #$spec, but #$child could not be closed as its duplicate and no child.closed was written; run this again" >&2
          exit 1
        fi
      fi
      line="#$child became ticket #$became under #$spec" ;;
  esac

  local -a fields=(--field "child=$child" --field "resolution=$resolution")
  [ -z "$became" ] || fields+=(--json-field "became=$became")
  [ "$resolution" != fixed ] || fields+=(--field "commit=$(git rev-parse HEAD 2>/dev/null)")
  if ! post_event "$ticket" child.closed --ticket "$ticket" --spec "$spec" --line "$line" \
       "${fields[@]}"; then
    echo "dispatch: #$child is routed ($resolution) but the child.closed event on #$ticket was not written, so the night summary counts it unread; run this again" >&2
    exit 1
  fi
  echo "route #$child: $resolution${became:+ #$became}, recorded on #$ticket" >&2
}

# ------------------------------------------------------------------ entry

# `self` reads nothing but this process and its runner, so it answers without models.json:
# `verify-ticket.py` asks it for the session a refusal is written by.
if [ "${1:-}" = self ] && [ "$#" -eq 1 ]; then
  own_session
  exit $?
fi

[ -f "$MODELS_JSON" ] || refuse "no models.json at $MODELS_JSON; run install.sh"

# `--tools <dir>` may appear anywhere and any number of times. Everything else is
# positional. A script of another skill is looked up by basename in those directories,
# in the order given.
TOOLS=()
positional=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --tools)
      [ "$#" -ge 2 ] || refuse "--tools takes a directory"
      TOOLS+=("$2")
      shift 2
      ;;
    --tools=*)
      TOOLS+=("${1#--tools=}")
      shift
      ;;
    --json | --run) refuse "$1 is no longer a flag" ;;
    *)
      positional+=("$1")
      shift
      ;;
  esac
done
set -- ${positional[@]+"${positional[@]}"}

tool() {
  local dir
  for dir in ${TOOLS[@]+"${TOOLS[@]}"}; do
    if [ -f "$dir/$1" ]; then
      printf '%s\n' "$dir/$1"
      return 0
    fi
  done
  return 1
}
SKILLS_ROOT="$(dirname "$SKILL_ROOT")"
LEASE="$(tool lease.py || printf '%s\n' "$SKILLS_ROOT/drive-target/scripts/lease.py")"
VERIFY="$(tool verify-ticket.py || printf '%s\n' "$SKILLS_ROOT/verify-ticket/scripts/verify-ticket.py")"
EVENTS="$(tool events.py || printf '%s\n' "$SKILLS_ROOT/verify-ticket/scripts/events.py")"
[ -f "$EVENTS" ] \
  || refuse "no events.py at $EVENTS, so nothing on a ticket can be read or written; pass --tools <the verify-ticket skill's scripts directory>"
# `status.py` folds the same events, and reads them through the same file.
export MMW_EVENTS_PY="$EVENTS"
# `advance` runs `start` through this same script; the directories travel with it.
TOOLS_ARGS=()
for dir in ${TOOLS[@]+"${TOOLS[@]}"}; do
  TOOLS_ARGS+=(--tools "$dir")
done

case "${1:-}" in
  board)
    [ "$#" -eq 1 ] || usage
    open_board
    ;;
  check)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "the spec number must be digits only, got $2" ;; esac
    check_machine "$2"
    ;;
  open)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "the spec number must be digits only, got $2" ;; esac
    open_night "$2"
    ;;
  open-ticket)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    open_ticket "$2"
    ;;
  adopt)
    if [ "$#" -eq 2 ]; then
      into=""
    elif [ "$#" -eq 4 ] && [ "$3" = --into ]; then
      into="$4"
      [ -n "$into" ] || usage
    else
      usage
    fi
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    adopt_ticket "$2" "$into"
    ;;
  ack)
    if [ "$#" -eq 2 ] && [ "$2" = relay.recovered ]; then
      ack_wake relay.recovered
    elif [ "$#" -eq 3 ]; then
      # The wake reads `#<n> <event>`; the number is taken with or without its `#`.
      number="${2#\#}"
      case "$number" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
      ack_wake "$number" "$3"
    else
      usage
    fi
    ;;
  advance)
    [ "$#" -eq 2 ] || usage
    advance "$2"
    ;;
  integrate)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    integrate_ticket "$2"
    ;;
  land)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    land_tickets "$2"
    ;;
  start)
    [ "$#" -eq 3 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    start_one "$2" "$3"
    ;;
  retract)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    retract_one "$2"
    ;;
  wait)
    [ "$#" -eq 3 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    wait_one "$2" "$3"
    ;;
  resume)
    [ "$#" -eq 3 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    resume_one "$2" "$3"
    ;;
  status)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "the spec number must be digits only, got $2" ;; esac
    python3 "$STATUS" --table "$2"
    exit $?
    ;;
  reverify)
    [ "$#" -eq 2 ] || usage
    reverify_spec "$2"
    ;;
  summary)
    [ "$#" -eq 2 ] || usage
    summary_spec "$2"
    ;;
  finish)
    [ "$#" -eq 2 ] || usage
    finish_spec "$2"
    ;;
  suspend)
    [ "$#" -eq 2 ] || usage
    suspend_night "$2"
    ;;
  route)
    [ "$#" -eq 4 ] || [ "$#" -eq 5 ] || usage
    route_child "$2" "$3" "$4" "${5:-}"
    ;;
  "" | -h | --help)
    usage
    ;;
  *)
    usage
    ;;
esac
