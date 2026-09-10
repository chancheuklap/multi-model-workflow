#!/usr/bin/env bash
#
# Start an agent on a ticket, move a spec's batch forward, or report on one.
#
#   dispatch.sh check <spec>
#   dispatch.sh open <spec>
#   dispatch.sh open-ticket <n>
#   dispatch.sh adopt <n>
#   dispatch.sh self
#   dispatch.sh advance <spec>
#   dispatch.sh land <n>
#   dispatch.sh start <n> worker|reviewer|verifier
#   dispatch.sh retract <n>
#   dispatch.sh wait <n> worker|reviewer|verifier
#   dispatch.sh ack <n> <event> | relay.recovered
#   dispatch.sh resume <n> "<text>"
#   dispatch.sh status <spec>
#   dispatch.sh reverify <spec>
#   dispatch.sh summary <spec>
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
# row of the live table (~/.mmw/models.md), resolved against the catalog of the runner
# that starts it (`use_catalog_of`). Tonight's runner is `models.py runner`: MMW_RUNNER,
# then the table's runner row, then the runner this process runs in, then orca.
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
if [ -n "${MMW_LIVE_MODELS:-}" ]; then
  MODELS="$MMW_LIVE_MODELS"
elif [ -n "${MMW_V2_HOME:-}" ]; then
  MODELS="$MMW_V2_HOME/.mmw/models.md"
else
  MODELS="$HOME/.mmw/models.md"
fi
STATUS="$SKILL_ROOT/scripts/status.py"
RELAY="$SKILL_ROOT/scripts/relay.py"
RUNNER=""
RUNNER_NAME=""
# The skill lives under mmw-v2/skills/<name> of the toolbox checkout, so `install.sh`
# is two directories up, and `verify-ticket.py` and `lease.py` are in the `scripts/` of
# their own skills one directory over. A `--tools` directory given on the command line
# is searched before those.
INSTALLER="$(dirname "$(dirname "$SKILL_ROOT")")/install.sh"
# `models.py` reads the live table, so it belongs to this skill and travels with it.
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

# Called once at the top of every command that talks to the runner, before any `$(…)`.
# The check cannot live in `runner()`: its callers run it inside `$(…)`, and a `refuse`
# there ends only that subshell — the command then carries on with an empty answer. With
# the adapter file gone that made `retract` archive a running worker's workspace and
# exit 0.
require_runner() {
  [ -f "$RUNNER" ] || refuse "no runner adapter for ${RUNNER_NAME:-this runner} at ${RUNNER:-scripts/runners/}; name paseo, orca or herdr in MMW_RUNNER or the runner row of $MODELS, or restore that file, then run the command again"
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
    || refuse "could not tell tonight's runner from MMW_RUNNER, $MODELS or this process"
  printf '%s\n' "$name"
}

# Which catalog `models.py` resolves a live-table row against: the runner that starts the
# session decides. Paseo is handed Paseo's own provider model ids; a runner that runs the
# host's CLI in a terminal (Orca, Herdr) is handed the CLI's own ids, so its row is
# resolved against the CLI's catalog, the one the table under the live table is copied
# from. Resolving against another runner's catalog either fails outright (Paseo's daemon is
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
       dispatch.sh adopt <n>
       dispatch.sh self
       dispatch.sh advance <spec>
       dispatch.sh land <n>
       dispatch.sh start <n> worker|reviewer|verifier
       dispatch.sh retract <n>
       dispatch.sh wait <n> worker|reviewer|verifier
       dispatch.sh ack <n> <event> | relay.recovered
       dispatch.sh resume <n> "<text>"
       dispatch.sh status <spec>
       dispatch.sh reverify <spec>
       dispatch.sh summary <spec>
       dispatch.sh suspend <spec>
       dispatch.sh route <ticket> <child> fixed|stale|became-ticket [<new ticket>]
USAGE
  exit 2
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

# `open <spec>`: the night begins. The relay watches the spec's tickets with this session
# as the night's main agent, and `spec.opened` on the spec records who is woken. A
# spec.opened that could not be written closes the watch this call opened: a night that
# says nowhere that it is open is not opened.
open_night() {
  local spec="$1" opened runner session how
  opened="$(open_relay --spec "$spec")" || exit 2
  IFS=$'\t' read -r runner session how <<<"$opened"
  if ! post_event "$spec" spec.opened --spec "$spec" \
       --line "NIGHT OPENED #$spec: wake-ups go to the main agent, $runner session $session" \
       --field "runner=$runner" --field "session=$session"; then
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
# facts `start` writes — the grade's live-table row, this worktree, its branch and base,
# and no slot, which the first run of its criteria that runs the product claims — and makes sure a relay watches the ticket: the
# watch already covering it, or a watch of this ticket alone with this session as its main
# agent. Run it from the ticket's worktree, on branch issue-<n>, before claiming.
adopt_ticket() {
  local number="$1" line runner session
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

  # The base is the commit the branch was cut from the base branch at: what `start`
  # records when it cuts the branch, found here from the checkout the night runs in.
  local base base_branch
  base="$(git -C "$tree" config --get "branch.issue-$number.mmw-base")"
  base_branch="$(git -C "$tree" config --get "branch.issue-$number.mmw-base-branch")"
  [ -n "$base_branch" ] \
    || refuse "no base branch recorded for issue-$number, and which branch it merges into is not this script's guess. Record it with git config branch.issue-$number.mmw-base-branch <the branch the night merges into>, then adopt again"
  if [ -z "$base" ]; then
    base="$(git -C "$tree" merge-base HEAD "$base_branch" 2>/dev/null)"
    [ -n "$base" ] || refuse "issue-$number and $base_branch share no commit, so there is no base to review from"
  fi

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
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS has none"
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

  git -C "$tree" config "branch.issue-$number.mmw-base" "$base"
  git -C "$tree" config "branch.issue-$number.mmw-base-branch" "$base_branch"
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
       --field "base=$base" --json-field adopted=true; then
    [ -n "$started" ] && stop_relay --tickets "$number"
    refuse "could not write the worker.started event on #$number, so this session is not its worker$([ -n "$started" ] && echo " and the watch this opened was closed again"); adopt again once the tracker takes comments"
  fi
  printf '%s\n' "$session"
}

# ------------------------------------------------------------------ live table

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

# Fills `branch.issue-<n>.mmw-base` for a branch that exists without one, with the
# merge base of HEAD and that branch; `mmw-base-branch` likewise, with the branch HEAD
# is on. A value already there is left alone: it was recorded when the branch was cut
# and is the better answer.
# `base_branch` is the branch the ticket's branch was cut from: the one the night merges
# into. Recorded once, when the branch is cut; later starts leave it as it is.
record_base_if_missing() {
  local number="$1" root="$2" base_branch="$3" found
  [ -n "$base_branch" ] || return 0
  if [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base")" ]; then
    found="$(git -C "$root" merge-base "$base_branch" "issue-$number" 2>/dev/null)"
    [ -n "$found" ] && git -C "$root" config "branch.issue-$number.mmw-base" "$found"
  fi
  if [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base-branch")" ]; then
    git -C "$root" config "branch.issue-$number.mmw-base-branch" "$base_branch"
  fi
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

# Prints dest<TAB>cwd<TAB>created. dest is the absolute worktree path, and cwd is the
# same path: the directory the runner is told to start the session in.
ensure_workspace() {
  local number="$1" root="$2" dest base
  dest="$root/.worktrees/issue-$number"
  # The branch the command runs on is the one the night merges into, so a new ticket
  # branch is cut from it. A ticket branch is never a base: a worker starting its reviewer
  # runs on issue-<n>, and that branch already exists.
  base="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  case "$base" in HEAD | issue-[0-9]*) base="" ;; esac
  if [ -d "$dest" ]; then
    local on
    on="$(git -C "$dest" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    [ "$on" = "issue-$number" ] \
      || { echo "dispatch: $dest is on ${on:-no branch}, not issue-$number; it is not this ticket's worktree — move it or rename it, then start again" >&2; return 1; }
    record_base_if_missing "$number" "$root" "$base"
    printf '%s\t%s\t0\n' "$dest" "$dest"
    return 0
  fi
  mkdir -p "$root/.worktrees"
  if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
    git -C "$root" worktree add --quiet "$dest" "issue-$number" \
      || { echo "dispatch: could not create a worktree for issue-$number" >&2; return 1; }
  else
    [ -n "$base" ] \
      || { echo "dispatch: this checkout is on ${base:-a detached HEAD or a ticket branch}, so a new issue-$number has nothing to be cut from; run it from the branch the night merges into" >&2; return 1; }
    git -C "$root" worktree add --quiet -b "issue-$number" "$dest" "$base" \
      || { echo "dispatch: could not create a worktree for issue-$number" >&2; return 1; }
  fi
  record_base_if_missing "$number" "$root" "$base"
  printf '%s\t%s\t1\n' "$dest" "$dest"
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
archive_ticket_agents() {
  local number="$1" name ident listed
  listed="$(sessions_on_ticket "$number")" || return 1
  while IFS=$'\t' read -r name ident; do
    [ -n "$ident" ] || continue
    use_runner "$name"
    runner stop "$ident" \
      || echo "dispatch: could not stop $ident on #$number; it is still open on $name" >&2
  done <<<"$listed"
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
  if [ -n "$cwd" ] && [ -f "$LEASE" ]; then
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
  remove_worktree "$root" "$cwd"
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
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS has none"
  IFS=$'\t' read -r host model effort <<<"$row"

  # The checkout the night runs in, whichever worktree this runs from: a worker starts its
  # reviewer and its verifier from its own worktree, and `.worktrees/` cut under that one
  # would be a second worktree of the branch it already has checked out.
  local root
  root="$(main_checkout)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no working directory to give the session"

  local prompt
  case "$kind" in
    worker)
      prompt="Use the implement skill to work ticket #$number. $AUTONOMOUS $PRODUCT_RULES $PIPELINE_FAULT" ;;
    reviewer)
      local base
      base="$(git -C "$root" config --get "branch.issue-$number.mmw-base")"
      [ -n "$base" ] \
        || refuse "no branch.issue-$number.mmw-base, so the reviewer has no commit to start from"
      prompt="Use the code-review skill to review ticket #$number from base commit $base. $AUTONOMOUS" ;;
    verifier)
      prompt="Use the verdict skill to verify ticket #$number. $AUTONOMOUS $PRODUCT_RULES" ;;
  esac

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
  ws_row="$(ensure_workspace "$number" "$root")" \
    || refuse "could not open a worktree for issue-$number"
  cwd="$(printf '%s\n' "$ws_row" | cut -f2)"
  created="$(printf '%s\n' "$ws_row" | cut -f3)"

  # A standing worktree a worker of this ticket left — lost, stopped by a suspension, or
  # replaced a moment ago — can hold its uncommitted edits. They are this ticket's work,
  # and the new worker continues from them; left uncommitted, its `--preflight` would
  # refuse the worktree. A worktree no worker of this ticket has had is not touched: its
  # changes are somebody else's, and the preflight refuses them rather than take them.
  if [ "$kind" = worker ] && [ "$created" = 0 ]; then
    local left_by
    left_by="$(last_worker_on_ticket "$number")" \
      || refuse "could not read #$number's events, so whose edits $cwd holds is unknown; nothing was started"
    if [ -n "$left_by" ]; then
      keep_unfinished_work "$number" "$cwd" "$left_by" \
        || refuse "the uncommitted work in $cwd was not saved (the reason is above), and a new worker cannot start on it; commit or set it aside on issue-$number, then start again. Nothing was started"
    fi
  fi

  local session
  if ! session="$(runner start --host "$host" --model "$model" --effort "$effort" \
       --cwd "$cwd" --prompt "$prompt" --skip-approval --title "#$number $kind")" \
     || [ -z "$session" ]; then
    if [ "$created" = 1 ] && [ -n "$cwd" ]; then
      remove_worktree "$root" "$cwd" \
        || echo "dispatch: could not remove the worktree for #$number" >&2
    fi
    refuse "$RUNNER_NAME did not start $host for #$number $kind (its reason is above); nothing was retried. Fix what it names, or change this agent's row in $MODELS, then start again"
  fi
  session="$(printf '%s\n' "$session" | tail -n 1)"

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
       --field "base=$(git -C "$root" config --get "branch.issue-$number.mmw-base")"; then
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
    echo "dispatch: tonight's runner is $runner, and this skill has no adapter for it (scripts/runners/$runner.sh); name paseo, orca or herdr in MMW_RUNNER or the runner row of $MODELS" >&2
    failed=1
  fi
  use_catalog_of "$runner"
  roles="$(worker_roles | tr '\n' ' ')" \
    || { echo "dispatch: $MODELS cannot be read (the reason is above)" >&2; failed=1; roles=""; }
  err_file="$(mktemp)"
  for role in $roles reviewer verifier; do
    if ! out="$(row_for_role "$role" 2>"$err_file")"; then
      echo "dispatch: the $role row of $MODELS does not resolve on $runner: $(tr '\n' ' ' < "$err_file")" >&2
      failed=1
    elif [ -z "$out" ]; then
      echo "dispatch: $MODELS has no $role row, and every $role start reads one" >&2
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
  # One diagnostic per host, not per row of the live table: several agents share a host, and
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
    diag="$(paseo provider diagnostic "$host" --json 2>&1)" || diag=""
    MMW_HOST="$host" MMW_PROVIDERS="$(paseo provider ls --json 2>/dev/null)" python3 -c '
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
           *) echo "dispatch: #$number asks for ${marked[0]}, and $MODELS has no such row" >&2
              failed=1 ;;
         esac ;;
      *) echo "dispatch: #$number carries ${#marked[@]} worker labels (${marked[*]}), and it takes one" >&2
         failed=1 ;;
    esac
  done <<<"$grades"

  [ "$failed" -eq 0 ] || exit 2
}

# ------------------------------------------------------------------ advancing

ticket_branch() { printf 'issue-%s\n' "$1"; }

ticket_title() {
  gh_ issue view "$1" --json title -q .title 2>/dev/null | head -n 1
}

# Everything needed to resolve the merge sitting in the tree, in the order the
# `resolving-merge-conflicts` skill asks for it: the state of the merge first, then the
# primary source behind each side. Both sides are tickets — the branch being merged is
# one ticket's work, and the merge commits already on this branch name the others — so
# they are printed rather than left to be hunted for.
conflict_report() {
  local root="$1" remaining="${2:-}"
  local git_dir branch number title line
  git_dir="$(git -C "$root" rev-parse --git-dir)"
  branch="$(sed -n "s/^Merge branch '\([^']*\)'.*/\1/p" "$git_dir/MERGE_MSG" 2>/dev/null | head -n 1)"
  [ -n "$branch" ] || branch="(unknown)"

  echo "CONFLICT merging $branch into $(git -C "$root" rev-parse --abbrev-ref HEAD)"
  echo

  number="${branch#issue-}"
  case "$number" in
    *[!0-9]* | "") echo "  MERGE_HEAD  $branch" ;;
    *) title="$(ticket_title "$number")"
       echo "  MERGE_HEAD  $branch  ← $title (#$number)" ;;
  esac

  echo "  HEAD        already merged, most recent first:"
  git -C "$root" log --merges --first-parent -3 --format='%s' 2>/dev/null \
    | sed -n "s/^Merge branch '\([^']*\)'.*/\1/p" \
    | while read -r line; do
        number="${line#issue-}"
        case "$number" in
          *[!0-9]* | "") echo "                $line" ;;
          *) echo "                $line  ← $(ticket_title "$number") (#$number)" ;;
        esac
      done

  echo
  echo "  conflicted files:"
  git -C "$root" diff --name-only --diff-filter=U | sed 's/^/    /'

  if [ -n "$remaining" ]; then
    echo
    printf '  not merged yet: %s\n' "$(printf '%s' "$remaining" | tr '\n' ' ')"
  fi

  echo
  echo "  Resolve it with the resolving-merge-conflicts skill — never --abort — run this"
  echo "  repository's own checks, commit the merge, then run:"
  echo "    bash $SELF advance $MMW_ADVANCE_SPEC"
}

# 0 merged, 1 left in conflict, 2 could not run it at all.
#
# A retry is for the lock, not for the conflict: every worktree shares one `.git`, so
# a worker committing in its own worktree while this runs holds the lock this merge
# needs for a moment. A conflict leaves MERGE_HEAD behind and no number of retries
# changes it.
merge_one() {
  local root="$1" branch="$2" i
  for ((i = 1; i <= MERGE_TRIES; i++)); do
    if git -C "$root" merge --no-ff --no-edit "$branch" >/dev/null 2>&1; then
      return 0
    fi
    if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
      return 1
    fi
    sleep 2
  done
  return 2
}

# Record on ticket <n> that its branch is in the base branch now. Its events then show it
# landed, and that — not its closing — is what lets the tickets it blocks start: a
# ticket is cut from the base branch and has to find its blockers' work there.
record_landed() {
  local number="$1" root="$2" spec="${3:-}" branch into
  branch="$(ticket_branch "$number")"
  into="$(git -C "$root" rev-parse --abbrev-ref HEAD)"
  post_event "$number" ticket.landed --ticket "$number" --spec "$spec" \
      --line "Landed $branch into $into" \
      --field "branch=$branch" --field "into=$into" \
      --field "commit=$(git -C "$root" rev-parse --verify --quiet "refs/heads/$branch")" \
    || echo "dispatch: $branch is in $into, but the ticket.landed event on #$number was not written; the tickets it blocks stay blocked until the next advance or land writes it" >&2
}

advance() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to merge into"

  export MMW_ADVANCE_SPEC="$spec"
  export MMW_SPEC="$spec"

  if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    conflict_report "$root" >&2
    exit 3
  fi

  local dirty
  dirty="$(git -C "$root" status --porcelain --untracked-files=no)"
  [ -z "$dirty" ] \
    || refuse "$(printf '%s' "$dirty" | wc -l | tr -d ' ') tracked files have uncommitted changes; a merge would carry them in — commit them or set them aside first"

  # A night that is not open has no relay, so a ticket landing would wake nobody.
  local watched
  watched="$(relay_watches "" "$spec" 2>&1)" \
    || refuse "the night on #$spec is not open: ${watched#relay: }. Nothing would wake you when a ticket lands, so nothing was merged or started; run open $spec first"

  # The first plan says what to merge and which claims to give back. Its stderr repeats
  # in the second plan, which is the one read for what to start, so it is shown only
  # when the plan could not be made at all.
  local plan plan_err
  plan_err="$(mktemp)"
  plan="$(python3 "$STATUS" --advance-plan "$spec" 2>"$plan_err")" \
    || { cat "$plan_err" >&2; rm -f "$plan_err"; refuse "could not read the batch under #$spec"; }
  rm -f "$plan_err"

  local merged=0 skipped=0 number branch left rc
  local -a just_merged=()
  for number in $(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }'); do
    branch="$(ticket_branch "$number")"
    if ! git -C "$root" rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
      skipped=$((skipped + 1))
      continue
    fi
    if git -C "$root" merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then
      skipped=$((skipped + 1))
      just_merged+=("$number")
      continue
    fi
    merge_one "$root" "$branch"
    rc=$?
    if [ "$rc" -eq 1 ]; then
      left="$(printf '%s\n' "$plan" | awk -v n="$number" '$1 == "MERGE" && seen { print "issue-" $2 } $2 == n { seen = 1 }')"
      conflict_report "$root" "$left" >&2
      exit 3
    fi
    [ "$rc" -eq 0 ] || refuse "could not merge $branch after $MERGE_TRIES tries; git said nothing this script can act on"
    echo "merged $branch" >&2
    merged=$((merged + 1))
    just_merged+=("$number")
  done

  # The workspace goes, its slot with it, before the landing is recorded: an event is
  # posted once the state it announces holds, and `ticket.landed` announces that the
  # ticket's work is over, its product slot included. The relay wakes every worker waiting
  # for a slot when it reads one, so a slot still held at that moment is a wake for nothing.
  local archived
  for archived in "${just_merged[@]+"${just_merged[@]}"}"; do
    archive_workspace "$archived"
    record_landed "$archived" "$root" "$spec"
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
  # the claims given back: a merge that could not happen — no branch here to merge —
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

  echo "advance #$spec: merged $merged, already in $skipped, released $released, started $started, refused $refused" >&2
  # A refused start is its own exit code. Read as success it ends the main agent's turn,
  # and when nothing else of the batch is running no wake will ever come: the ticket sits
  # on the frontier, never started, and the night stops there without a word.
  [ "$refused" -eq 0 ] || exit 4
}

# ------------------------------------------------------------------ landing

# Land one ticket.
#
# Landing is what closing a ticket does not do: merge the branch and record
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
# lives, so a branch not yet in HEAD has to be merged first or the work has to
# be rebuilt from the branch to get it back. Agents are archived in the same
# step as the worktree, after that merge.
land_tickets() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to land into"

  if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    conflict_report "$root" >&2
    exit 3
  fi
  local dirty
  dirty="$(git -C "$root" status --porcelain --untracked-files=no)"
  [ -z "$dirty" ] \
    || refuse "$(printf '%s' "$dirty" | wc -l | tr -d ' ') tracked files have uncommitted changes; a merge would carry them in — commit them or set them aside first"

  local -a numbers=("$@")

  local plan
  plan="$(python3 "$STATUS" --land-plan "${numbers[@]}")" \
    || refuse "could not read $(printf '#%s ' "${numbers[@]}")from the tracker"

  # A branch in HEAD is recorded as landed only after its workspace, and the slot with it,
  # has gone below: `ticket.landed` announces the ticket's work is over, and the relay
  # wakes the workers waiting for a slot when it reads one.
  local merged=0 archived=0 released=0 kept=0 unmerged=0 number branch rc
  local -a in_head=()
  while IFS= read -r number; do
    [ -n "$number" ] || continue
    branch="$(ticket_branch "$number")"
    if ! git -C "$root" rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
      echo "land: #$number passed, and there is no $branch here to land" >&2
      continue
    fi
    if git -C "$root" merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then
      in_head+=("$number")
      continue
    fi
    merge_one "$root" "$branch"
    rc=$?
    if [ "$rc" -eq 1 ]; then
      conflict_report "$root" >&2
      exit 3
    fi
    [ "$rc" -eq 0 ] || refuse "could not merge $branch after $MERGE_TRIES tries; git said nothing this script can act on"
    echo "merged $branch" >&2
    merged=$((merged + 1))
    in_head+=("$number")
  done < <(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }')

  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      released=$((released + 1))
      give_ticket_slot_back "$number" || true
      post_event "$number" ticket.released --ticket "$number" --spec "$(ticket_spec "$number")" \
          --line "Gave the claim on #$number back: its work is over" \
          --field reason=landed \
        || echo "land: #$number's claim is given back, but its ticket.released event was not written" >&2
    else
      echo "land: could not give #$number's claim back" >&2
    fi
  done

  # A closed ticket whose branch is not in HEAD is the one case where archiving
  # destroys something: the directory goes and the work is only on the branch. Say so
  # and leave it standing — silence here would read exactly like a finished sweep.
  for number in $(printf '%s\n' "$plan" | awk '$1 == "ARCHIVE" { print $2 }'); do
    branch="$(ticket_branch "$number")"
    if git -C "$root" rev-parse --verify --quiet "refs/heads/$branch" >/dev/null \
       && ! git -C "$root" merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then
      echo "land: #$number is closed but $branch is not in HEAD; not archiving it — merge it or decide it is abandoned" >&2
      unmerged=$((unmerged + 1))
      continue
    fi
    archive_workspace "$number" && archived=$((archived + 1))
  done

  for number in "${in_head[@]+"${in_head[@]}"}"; do
    record_landed "$number" "$root" "$(ticket_spec "$number")"
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

  echo "land: merged $merged, archived $archived, released $released, still working $kept, already landed $nothing, left unmerged $unmerged" >&2

  # `land <n>` is the whole ending of a ticket outside a night, so the watch `open-ticket`
  # opened for it closes here, and the relay with it when it watched nothing else. A
  # night's watch is not this one and is left alone.
  local relay_left=0
  if [ "$kept" -eq 0 ]; then
    stop_relay --tickets "${numbers[0]}"
    [ "$?" = 1 ] && relay_left=1
  fi
  [ "$unmerged" -eq 0 ] && [ "$relay_left" -eq 0 ] || return 1
}

# ------------------------------------------------------------------ suspend

# The prose of the `spec.suspended` event a ticket still in the agent queue gets.
suspend_text() {
  local spec="$1" when="$2" ident="$3"
  printf '%s\n' \
    "The night on spec #$spec was suspended at $when, so this ticket has no verdict: nothing here says whether its work is finished."
  if [ -n "$ident" ]; then
    printf '%s\n' "Interrupted: $ident. Its workspace and its branch are untouched, and the next worker's start commits any edit left uncommitted. The batch is taken up again where it stands with advance."
  else
    printf '%s\n' "No session of ours was working on it at that moment. Its workspace and its branch, if it has them, are untouched, and it keeps its label, so the next advance of #$spec starts it."
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
  local live="" number ident name sessions stopped=0 still_live=""
  for number in $batch; do
    if ! sessions="$(ticket_events "$number" live)"; then
      echo "dispatch: could not read #$number's events, so whether a session still runs on it is unknown; it is left as it is" >&2
      still_live="$still_live $number"
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
        still_live="$still_live $number"
        left=$((left + 1))
        break
      fi
    done <<<"$sessions"
  done

  local when commented=0
  when="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  post_event "$spec" spec.suspended --spec "$spec" --line "NIGHT SUSPENDED #$spec" \
      --field "suspended_at=$when" \
    || { echo "dispatch: could not write the spec.suspended event on #$spec" >&2; left=$((left + 1)); }
  for number in $queued; do
    case " $still_live " in *" $number "*) continue ;; esac
    ident="$(printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { ids = ids sep $2; sep = ", " } END { print ids }')"
    local -a interrupted=()
    [ -z "$ident" ] || interrupted=(--field "interrupted=$ident")
    if post_event "$number" spec.suspended --ticket "$number" --spec "$spec" \
         --line "NIGHT SUSPENDED #$spec" --text-file <(suspend_text "$spec" "$when" "$ident") \
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
    case " $still_live " in *" $number "*) continue ;; esac
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

  local cwd back=0 rc
  if [ -f "$LEASE" ]; then
    [ -n "$(worktrees_root)" ] \
      || echo "dispatch: no workspace of this checkout is standing, so a lease can be matched to a ticket only through a standing workspace; python3 $LEASE list shows what is still held, and claim reclaims a lease whose directory is gone" >&2
    for number in $batch; do
      # A worker still running will start the product again, and the `stop` in between
      # tears up the record of what it started — leaving processes that stop can no
      # longer reach. So a ticket whose worker survived the archive keeps its slot: it
      # is already counted as left behind, and this only says why.
      case " $still_live " in
        *" $number "*)
          echo "dispatch: #$number keeps its slot while its worker runs; stopping a product under a live worker leaves processes its own stop cannot reach. End that agent, then suspend again" >&2
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

  local root git_dir commit plan number rc printed ids login
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository"
  git_dir="$(git -C "$root" rev-parse --git-dir)"
  commit="$(git -C "$root" rev-parse HEAD)"

  plan="$(python3 "$STATUS" --reverify-plan "$spec")" \
    || refuse "could not read the batch under #$spec"

  local green=0 red=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "REVERIFY" { print $2 }'); do
    # `--tools` is forwarded because the judges of a criterion are named bare and are
    # found only in the directories it names. Without it every interface criterion of
    # every ticket fails `command not found`, and the branch below would reopen and hand
    # back a whole night of finished work for a fault in this command line.
    # The run writes its own `ticket.checked` (run `reverify`, actor `main`), which is the
    # whole record of a green one.
    printed="$(python3 "$VERIFY" "$number" --reverify --actor main ${TOOLS_ARGS[@]+"${TOOLS_ARGS[@]}"} 2>&1)"
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
  echo "reverify #$spec: $green green, $red red"
  [ "$red" -eq 0 ] || exit 1
}

summary_spec() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  local body extra git_dir
  body="$(python3 "$STATUS" --summary "$spec")"
  git_dir="$(git rev-parse --git-dir 2>/dev/null || true)"
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
#   fixed               the main agent fixed it on this branch; closed as completed
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

# `self` reads nothing but this process and its runner, so it answers without a live
# table: `verify-ticket.py` asks it for the session a refusal is written by.
if [ "${1:-}" = self ] && [ "$#" -eq 1 ]; then
  own_session
  exit $?
fi

[ -f "$MODELS" ] || refuse "no live table at $MODELS; run install.sh"

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
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    adopt_ticket "$2"
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
