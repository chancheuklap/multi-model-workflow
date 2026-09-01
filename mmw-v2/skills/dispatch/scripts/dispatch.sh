#!/usr/bin/env bash
#
# Start an agent on a ticket, or wait for one to report back on that ticket.
#
#   dispatch.sh <ticket> <role> [base-commit]
#   dispatch.sh wait <ticket> "<first-line-regex>" [seconds]
#   dispatch.sh advance <spec> [--role R]
#   dispatch.sh run <spec> [--role R] [--max-hours H]
#
# The role and the ticket number are the whole input. Everything else — which Herdr
# name the session gets, whether it opens a tab or splits a pane, what it is told to
# work on — is decided by the shape of the pipeline, so it is written here rather than
# in the table. The table holds only what a person changes: the agent, the host, the
# model, the thinking level, and the arguments the host is started with.
#
# Exit codes are documented in SKILL.md next to this script.

set -uo pipefail

IDLE_TIMEOUT_MS=120000       # a session that is not ready by now is not coming up
PROMPT_TAKE_MS=15000         # a prompt that landed shows as working within this
TOKEN_TTL_MS=86400000        # a day, so a night's run never outlives its own metadata
WIDE_PANE_COLUMNS=160        # wider than this splits sideways, otherwise downwards
LABEL_TITLE_CHARS=20         # how much of the ticket title fits on a tab

WAIT_DEFAULT_SECONDS=1800
WAIT_SETTLED_GAP_SECONDS=5   # an agent that has already settled would spin otherwise
WAIT_POLL_SECONDS=30         # outside Herdr there is no lifecycle to block on

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS="$SKILL_ROOT/models.md"
BOARD="$SKILL_ROOT/scripts/board.py"
# The skill lives under mmw-v2/skills/<name>, so the installer is two directories up.
INSTALLER="$(dirname "$(dirname "$SKILL_ROOT")")/install.sh"

BOARD_TAB_LABEL="mmw board"
MERGE_TRIES=3                # the board opens worktrees while advance merges

# Herdr's agent names are unique among live agents across the whole server, not per
# workspace, so two repositories each holding a ticket #100 would collide on `issue-100`
# and the second `agent start` would simply fail — leaving that ticket unstartable for
# the rest of the night. The workspace id is short, stable, and already the prefix of
# every pane id in it. Outside Herdr the names are the bare ones. `board.py` builds the
# same prefix the same way; the two have to agree or it stops recognising our sessions.
herdr_name() {
  local ws="${HERDR_WORKSPACE_ID:-}"
  if [ -n "$ws" ]; then
    printf '%s-%s\n' "$(printf '%s' "$ws" | tr '[:upper:]' '[:lower:]')" "$1"
  else
    printf '%s\n' "$1"
  fi
}
MAIN_AGENT_NAME="$(herdr_name mmw-main)"
BOARD_RESTART_SECONDS=5      # it holds no state, so restarting it loses nothing

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into
# --json output under it, which no JSON reader can parse.
gh_() {
  env -u CLICOLOR_FORCE -u CLICOLOR gh "$@"
}

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

give_up() {
  echo "dispatch: $1" >&2
  exit 1
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh <ticket> <role> [base-commit]
       dispatch.sh wait <ticket> "<first-line-regex>" [seconds]
       dispatch.sh advance <spec> [--role R]
       dispatch.sh run <spec> [--role R] [--max-hours H]
USAGE
  exit 2
}

# ------------------------------------------------------------------ small helpers

# Reads one value out of a JSON document on stdin, by dotted path.
json_at() {
  MMW_JSON_PATH="$1" python3 -c '
import json, os, sys

try:
    node = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for key in os.environ["MMW_JSON_PATH"].strip(".").split("."):
    if not isinstance(node, dict) or key not in node:
        sys.exit(0)
    node = node[key]
if node is not None:
    print(node)
'
}

# Truncates stdin to a number of characters, not bytes: ticket titles are not ASCII.
head_chars() {
  MMW_HEAD_CHARS="$1" python3 -c '
import os, sys

print(sys.stdin.read().rstrip("\n")[:int(os.environ["MMW_HEAD_CHARS"])])
'
}

# ------------------------------------------------------------------ the table

# Prints "host<TAB>model<TAB>effort<TAB>launch arguments" for the first row whose agent
# column is the role asked for. Backticks are markdown, not part of any value.
row_for_role() {
  awk -F'|' -v want="$1" '
    function trim(s) { gsub(/^[ \t`]+/, "", s); gsub(/[ \t`]+$/, "", s); return s }
    /^[ \t]*\|/ && NF == 7 {
      if (trim($2) == want) {
        print trim($3) "\t" trim($4) "\t" trim($5) "\t" trim($6)
        exit
      }
    }
  ' "$MODELS"
}

# ------------------------------------------------------------------ the ticket

# Prints the ticket title when the ticket is ready to be worked on, and a one-line
# reason prefixed with REFUSE when it is not.
read_ticket() {
  local number="$1" json
  json="$(gh_ issue view "$number" --json state,labels,blockedBy,title 2>/dev/null)" \
    || { echo "REFUSE could not read ticket #$number from the tracker"; return; }
  printf '%s' "$json" | MMW_TICKET_NUMBER="$number" python3 -c '
import json, os, sys

number = os.environ["MMW_TICKET_NUMBER"]
try:
    ticket = json.load(sys.stdin)
except Exception:
    print("REFUSE the tracker did not answer with a readable ticket #" + number)
    sys.exit(0)

state = (ticket.get("state") or "unreadable").lower()
labels = [label.get("name") for label in ticket.get("labels") or []]
nodes = (ticket.get("blockedBy") or {}).get("nodes") or []
blockers = ["#" + str(b.get("number")) for b in nodes if b.get("state") != "CLOSED"]

if state != "open":
    print("REFUSE ticket #" + number + " is " + state + ", not open")
elif "ready-for-agent" not in labels:
    print("REFUSE ticket #" + number + " is not labelled ready-for-agent")
elif blockers:
    print("REFUSE ticket #" + number + " is still blocked by " + ", ".join(blockers))
else:
    print(ticket.get("title") or "")
'
}

# ------------------------------------------------------------------ the worktree

# Prints the path of ticket `number`'s worktree, creating it when it is not there yet.
# The worktree is this script's to make: hosts differ in whether they can open one at
# all, so the launch arguments carry no worktree flag and the session simply starts
# inside it. Only the worker gets one — the reviewer runs inside the worker's worktree
# and the verifier is a subagent of the worker's session, so neither comes through here.
#
# A branch named issue-<n> that already exists is reused as it stands: that is a
# redispatch, and the new session resumes the work. Otherwise the branch is cut from
# HEAD — whatever branch the dispatching session is on, because that is where the day's
# discussion and spec work happened and the ticket builds on it — and the cut point is
# recorded in `branch.issue-<n>.mmw-base`, where `verify-ticket.py` and the code review
# read the base their diffs start from. Stale bookkeeping for a directory deleted by
# hand is pruned first, and a failed add leaves git's own error on stderr for the
# caller's refusal to carry.
worktree_for() {
  local number="$1" root="$2"
  local base="${MMW_WORKTREES:-$HOME/.mmw/worktrees}/$(basename "$root")"
  local path="$base/issue-$number"
  git -C "$root" worktree prune 2>/dev/null
  if [ -d "$path" ]; then
    printf '%s\n' "$path"
    return 0
  fi
  mkdir -p "$base" || return 1
  if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
    git -C "$root" worktree add "$path" "issue-$number" >/dev/null || return 1
  else
    git -C "$root" worktree add -b "issue-$number" "$path" HEAD >/dev/null || return 1
    git -C "$root" config "branch.issue-$number.mmw-base" "$(git -C "$root" rev-parse HEAD)"
    # The branch name as well as the commit: `advance` merges this branch back into
    # the one it was cut from once the ticket closes, and a sha cannot name a branch.
    git -C "$root" config "branch.issue-$number.mmw-base-branch" \
      "$(git -C "$root" rev-parse --abbrev-ref HEAD)"
  fi
  printf '%s\n' "$path"
}

# ------------------------------------------------------------------ dispatching

dispatch() {
  local number="$1" role="$2" base="${3:-}"

  [ "${HERDR_ENV:-}" = 1 ] \
    || refuse "not running inside Herdr, so there is nowhere to start a session"

  local row host model effort launch
  row="$(row_for_role "$role")"
  [ -n "$row" ] || refuse "no role named $role in $MODELS"
  IFS=$'\t' read -r host model effort launch <<<"$row"
  case "$launch" in
    "" | "—" | "-")
      refuse "$role is a subagent: it is started by the skill that needs it, not from here" ;;
  esac
  case "$launch" in
    *'{effort}'*)
      case "$effort" in
        "" | "—" | "-")
          refuse "the $role row asks for a thinking level but leaves its effort column empty" ;;
      esac ;;
  esac

  local reviewing=0
  [ "$role" = reviewer ] && reviewing=1
  if [ "$reviewing" = 1 ]; then
    [ -n "$base" ] || refuse "the reviewer needs the commit its review starts from"
  else
    [ -z "$base" ] || refuse "only the reviewer takes a base commit"
  fi

  local title
  title="$(read_ticket "$number")"
  case "$title" in
    "REFUSE "*) refuse "${title#REFUSE }" ;;
    "") refuse "the tracker did not answer with a readable ticket #$number" ;;
  esac

  launch="${launch//\{model\}/$model}"
  launch="${launch//\{effort\}/$effort}"
  launch="${launch//\{n\}/$number}"
  local args
  read -r -a args <<<"$launch"
  [ "${#args[@]}" -gt 0 ] || refuse "the $role row has no launch arguments"

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no working directory to give the session"

  local pane name prompt
  if [ "$reviewing" = 1 ]; then
    name="$(herdr_name "issue-$number-review")"
    prompt="Use the code-review skill to review ticket #$number from base commit $base"
    local caller="${HERDR_PANE_ID:-}"
    [ -n "$caller" ] || refuse "no calling pane to split, so the reviewer has nowhere to go"
    local width direction
    width="$(herdr pane layout --pane "$caller" | json_at .result.layout.area.width)"
    [ -n "$width" ] || refuse "could not measure pane $caller"
    if [ "$width" -ge "$WIDE_PANE_COLUMNS" ]; then direction=right; else direction=down; fi
    pane="$(herdr pane split --pane "$caller" --direction "$direction" --cwd "$root" --no-focus \
            | json_at .result.pane.pane_id)"
    [ -n "$pane" ] || refuse "could not split pane $caller"
  else
    name="$(herdr_name "issue-$number")"
    prompt="Use the implement skill to work ticket #$number"
    local worktree
    worktree="$(worktree_for "$number" "$root")" \
      || refuse "could not open a worktree for issue-$number under ${MMW_WORKTREES:-$HOME/.mmw/worktrees}"
    local label tab_args
    label="$(printf '#%s %s' "$number" "$title" \
             | head_chars $(( LABEL_TITLE_CHARS + ${#number} + 2 )))"
    tab_args=()
    [ -n "${HERDR_WORKSPACE_ID:-}" ] && tab_args=(--workspace "$HERDR_WORKSPACE_ID")
    # MMW_TICKET is how the gates inside this pane know which ticket they guard.
    pane="$(herdr tab create ${tab_args[@]+"${tab_args[@]}"} --cwd "$worktree" \
              --label "$label" --env "MMW_TICKET=$number" --no-focus \
            | json_at .result.root_pane.pane_id)"
    [ -n "$pane" ] || refuse "could not open a tab for ticket #$number"
  fi

  herdr agent start "$name" --kind "$host" --pane "$pane" -- "${args[@]}" >/dev/null \
    || refuse "could not start $name in pane $pane"

  herdr agent wait "$name" --until idle --until done --timeout "$IDLE_TIMEOUT_MS" >/dev/null 2>&1 \
    || give_up "$name is up in pane $pane but was not ready within $(( IDLE_TIMEOUT_MS / 1000 ))s; it has not been told anything"

  herdr agent prompt "$name" "$prompt" >/dev/null \
    || give_up "$name is up in pane $pane but would not take the prompt"

  # The prompt call says the text was sent, not that the session heard it: a host still
  # drawing its start screen swallows the first line without a trace. Turning working —
  # or blocked, a session that heard and hit a form — within a few seconds is what says
  # it landed; one resend covers the swallowed case.
  if ! herdr agent wait "$name" --until working --until blocked \
         --timeout "$PROMPT_TAKE_MS" >/dev/null 2>&1; then
    herdr agent prompt "$name" "$prompt" >/dev/null 2>&1
    herdr agent wait "$name" --until working --until blocked \
        --timeout "$PROMPT_TAKE_MS" >/dev/null 2>&1 \
      || give_up "$name is up in pane $pane but did not start on the prompt"
  fi

  # The ticket and the kind are written here rather than left to the first
  # `verify-ticket.py` run, so that a pane which stops before that run is still
  # readable as belonging to this ticket as a worker or as a reviewer. `kind` is not
  # the `<role>` this script takes: three roles start a session, and the two kinds are
  # what the session then is.
  local human token_kind
  if [ "$reviewing" = 1 ]; then
    human="#$number reviewer"
    token_kind=reviewer
  else
    human="#$number worker"
    token_kind=worker
  fi
  herdr pane rename "$pane" "$human" >/dev/null 2>&1
  herdr pane report-metadata "$pane" --source mmw \
    --token "ticket=$number" --token "kind=$token_kind" --token "model=$model" \
    --ttl-ms "$TOKEN_TTL_MS" >/dev/null 2>&1

  echo "$name is working on #$number in pane $pane on $model"
}

# ------------------------------------------------------------------ waiting

# The newest comment on the ticket, or nothing when it has none.
newest_comment() {
  gh_ issue view "$1" --json comments 2>/dev/null | python3 -c '
import json, sys

try:
    comments = json.load(sys.stdin).get("comments") or []
except Exception:
    comments = []
if comments:
    sys.stdout.write(comments[-1].get("body") or "")
'
}

# The agent this ticket is waiting on. A worker can only be waiting on its own
# reviewer, and anyone else can only be waiting on the worker, so which one it is
# follows from who is calling. Prints nothing when that agent is not live, which
# leaves the caller waiting on the tracker alone.
awaited_agent() {
  herdr agent list 2>/dev/null \
    | MMW_TICKET_NUMBER="$1" MMW_OWN_PANE="${HERDR_PANE_ID:-}" \
      MMW_NAME_PREFIX="$(herdr_name "")" python3 -c '
import json, os, sys

number = os.environ["MMW_TICKET_NUMBER"]
own_pane = os.environ.get("MMW_OWN_PANE") or None
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
agents = (payload.get("result") or {}).get("agents") or payload.get("agents") or []
live = dict((a.get("name"), a.get("pane_id")) for a in agents if a.get("name"))

worker = os.environ.get("MMW_NAME_PREFIX", "") + "issue-" + number
caller_is_the_worker = own_pane is not None and live.get(worker) == own_pane
target = worker + "-review" if caller_is_the_worker else worker
if target in live:
    print(target)
'
}

wait_for() {
  local number="$1" pattern="$2" seconds="${3:-}"
  [ -n "$seconds" ] || seconds="$WAIT_DEFAULT_SECONDS"
  local deadline=$(( $(date +%s) + seconds ))
  local target=""
  [ "${HERDR_ENV:-}" = 1 ] && target="$(awaited_agent "$number")"

  while :; do
    local remaining=$(( deadline - $(date +%s) ))
    if [ -n "$target" ] && [ "$remaining" -gt 0 ]; then
      # Herdr holds the wait open until the agent settles, so the tracker is asked once
      # per lifecycle change rather than once per interval.
      herdr agent wait "$target" --timeout $(( remaining * 1000 )) >/dev/null 2>&1
    fi

    local comment first
    comment="$(newest_comment "$number")"
    first="$(printf '%s' "$comment" | head -n 1)"
    if [ -n "$comment" ] && printf '%s' "$first" | grep -Eq "$pattern"; then
      printf '%s\n' "$comment"
      return 0
    fi

    [ "$(date +%s)" -lt "$deadline" ] || break
    if [ -n "$target" ]; then sleep "$WAIT_SETTLED_GAP_SECONDS"; else sleep "$WAIT_POLL_SECONDS"; fi
    [ "$(date +%s)" -lt "$deadline" ] || break
  done

  local who="${target:-the agent on #$number}"
  gh_ issue comment "$number" \
    --body "$who did not report back within ${seconds}s. This round was skipped and the ticket carried on." \
    >/dev/null 2>&1
  give_up "$who did not report back within ${seconds}s"
}

# ------------------------------------------------------------------ advancing

# The branch `worktree_for` cuts for a ticket. Only it hands out these names, so reading
# one back to a ticket number is exact.
ticket_branch() { printf 'issue-%s\n' "$1"; }

# A ticket's title, for the lines a person reads. Empty when the tracker cannot say.
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
# A retry is for the lock, not for the conflict: the board opens a worktree for a
# redispatch while this runs, and the two collide on the repository's index for a
# moment. A conflict leaves MERGE_HEAD behind and no number of retries changes it.
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

# Merge what the batch has finished, then start what it can start. One command because
# the order is the whole point: `worktree_for` cuts a branch from HEAD at the moment it
# opens, so a branch merged after the next ticket is dispatched is a branch that ticket
# cannot see.
advance() {
  local spec="$1"; shift
  local role=junior-worker
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --role) role="${2:-}"; shift 2 || usage ;;
      *) usage ;;
    esac
  done
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  [ "${HERDR_ENV:-}" = 1 ] \
    || refuse "not running inside Herdr, so there is nowhere to start a session"
  [ -f "$BOARD" ] || refuse "no board at $BOARD"
  [ -n "$(row_for_role "$role")" ] || refuse "no role named $role in $MODELS"

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository, so there is nothing to merge into"

  export MMW_ADVANCE_SPEC="$spec"

  # A merge left half-resolved stops everything: the tree is between two tickets, and a
  # worktree cut from it would hand the next worker neither one.
  if git -C "$root" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1; then
    conflict_report "$root"
    exit 3
  fi

  local dirty
  dirty="$(git -C "$root" status --porcelain --untracked-files=no)"
  [ -z "$dirty" ] \
    || refuse "$(printf '%s' "$dirty" | wc -l | tr -d ' ') tracked files have uncommitted changes; a merge would carry them in — commit them or set them aside first"

  local plan
  plan="$(python3 "$BOARD" --advance-plan "$spec")" \
    || refuse "could not read the batch under #$spec"

  local merged=0 skipped=0 number branch left rc
  for number in $(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }'); do
    branch="$(ticket_branch "$number")"
    if ! git -C "$root" rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
      skipped=$((skipped + 1))
      continue
    fi
    if git -C "$root" merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then
      skipped=$((skipped + 1))
      continue
    fi
    merge_one "$root" "$branch"
    rc=$?
    if [ "$rc" -eq 1 ]; then
      left="$(printf '%s\n' "$plan" | awk -v n="$number" '$1 == "MERGE" && seen { print "issue-" $2 } $2 == n { seen = 1 }')"
      conflict_report "$root" "$left"
      exit 3
    fi
    [ "$rc" -eq 0 ] || refuse "could not merge $branch after $MERGE_TRIES tries; git said nothing this script can act on"
    echo "merged $branch"
    merged=$((merged + 1))
  done

  local started=0 refused=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    # A subprocess, so one ticket that will not start does not take the rest with it.
    if bash "$SELF" "$number" "$role"; then
      started=$((started + 1))
    else
      refused=$((refused + 1))
    fi
  done

  echo "advance #$spec: merged $merged, already in $skipped, started $started, refused $refused"
}

# ------------------------------------------------------------------ the night

# Starts the night: checks the machine, names this pane so the board can reach it,
# opens the monitor tab, and leaves board.py --watch running in it. Everything after
# this is the board's; the caller goes back to reading tickets.
run_night() {
  local spec="$1"; shift
  local role=junior-worker max_hours=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --role) role="${2:-}"; shift 2 || usage ;;
      --max-hours) max_hours="${2:-}"; shift 2 || usage ;;
      *) usage ;;
    esac
  done
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac

  [ "${HERDR_ENV:-}" = 1 ] \
    || refuse "not running inside Herdr, so there is nowhere to open the monitor tab"
  local caller="${HERDR_PANE_ID:-}"
  [ -n "$caller" ] || refuse "no calling pane, so the board would have nobody to report to"
  [ -f "$BOARD" ] || refuse "no board at $BOARD"

  # The same refusal every dispatch would make, brought forward to the one moment
  # somebody is here: a subagent row starts no session, so a night on it never
  # dispatches a ticket and never runs out of them either.
  local night_row night_launch
  night_row="$(row_for_role "$role")"
  [ -n "$night_row" ] || refuse "no role named $role in $MODELS"
  night_launch="$(printf '%s' "$night_row" | cut -f4)"
  case "$night_launch" in
    "" | "—" | "-")
      refuse "$role is a subagent: it is started by the skill that needs it, so a night on it would start nothing" ;;
  esac

  # A night nobody is watching cannot notice that the skills or the gate went missing
  # from this machine, so it is checked at the one moment somebody is here.
  [ -f "$INSTALLER" ] || refuse "no installer at $INSTALLER"
  bash "$INSTALLER" --check >/dev/null \
    || refuse "install.sh --check found something missing; run install.sh before the night"

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository"

  herdr agent rename "$caller" "$MAIN_AGENT_NAME" >/dev/null 2>&1 \
    || refuse "could not rename this pane $MAIN_AGENT_NAME, so the board could not reach it"

  # The same workspace the workers go to. Every board sees every pane on the server and
  # tells its own apart by workspace, so a board started in somebody else's would filter
  # by the wrong one — and the label carries the spec number because several of these
  # tabs are open on a night when several projects run.
  local pane tab_args
  tab_args=()
  [ -n "${HERDR_WORKSPACE_ID:-}" ] && tab_args=(--workspace "$HERDR_WORKSPACE_ID")
  pane="$(herdr tab create ${tab_args[@]+"${tab_args[@]}"} --cwd "$root" \
            --label "$BOARD_TAB_LABEL #$spec" --no-focus \
          | json_at .result.root_pane.pane_id)"
  [ -n "$pane" ] || refuse "could not open the $BOARD_TAB_LABEL tab"

  local watch="python3 $BOARD --watch $spec --role $role"
  [ -n "$max_hours" ] && watch="$watch --max-hours $max_hours"
  # It keeps no state, so a crash costs nothing but the wait; it exits 0 once the night
  # is over, and that is what ends the loop.
  herdr pane run "$pane" "until $watch; do sleep $BOARD_RESTART_SECONDS; done" >/dev/null \
    || refuse "could not start the board in pane $pane"

  echo "$MAIN_AGENT_NAME is this pane; the board is watching #$spec in pane $pane"
  # The board announces a frontier by prompting this pane, and a focused pane takes no
  # prompt — which is what a pane that just typed this command is. So the first batch is
  # the caller's to start.
  echo "Now advance #$spec yourself: the board cannot prompt a focused pane, so the first frontier is yours to start."
}

# ------------------------------------------------------------------ entry

[ -f "$MODELS" ] || refuse "no table at $MODELS"

case "${1:-}" in
  run)
    [ "$#" -ge 2 ] || usage
    shift
    run_night "$@"
    ;;
  advance)
    [ "$#" -ge 2 ] || usage
    shift
    advance "$@"
    ;;
  wait)
    [ "$#" -ge 3 ] && [ "$#" -le 4 ] || usage
    wait_for "$2" "$3" "${4:-}"
    ;;
  "" | -h | --help)
    usage
    ;;
  *)
    [ "$#" -ge 2 ] && [ "$#" -le 3 ] || usage
    case "$1" in
      *[!0-9]* | "") refuse "ticket number must be digits only, got $1" ;;
    esac
    dispatch "$1" "$2" "${3:-}"
    ;;
esac
