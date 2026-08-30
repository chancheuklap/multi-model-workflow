#!/usr/bin/env bash
#
# Start an agent on a ticket, or wait for one to report back on that ticket.
#
#   dispatch.sh <ticket> <role> [base-commit]
#   dispatch.sh wait <ticket> "<first-line-regex>" [seconds]
#
# The role and the ticket number are the whole input. Everything else — which Herdr
# name the session gets, whether it opens a tab or splits a pane, what it is told to
# work on — is decided by the shape of the pipeline, so it is written here rather than
# in the table. The table holds only what a person changes: the agent, the harness, the
# model, the thinking level, and the arguments the harness is started with.
#
# Exit codes are documented in SKILL.md next to this script.

set -uo pipefail

IDLE_TIMEOUT_MS=120000       # a session that is not ready by now is not coming up
TOKEN_TTL_MS=86400000        # a day, so a night's run never outlives its own metadata
WIDE_PANE_COLUMNS=160        # wider than this splits sideways, otherwise downwards
LABEL_TITLE_CHARS=20         # how much of the ticket title fits on a tab

WAIT_DEFAULT_SECONDS=1800
WAIT_SETTLED_GAP_SECONDS=5   # an agent that has already settled would spin otherwise
WAIT_POLL_SECONDS=30         # outside Herdr there is no lifecycle to block on

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS="$SKILL_ROOT/models.md"

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
blockers = ["#" + str(b.get("number")) for b in ticket.get("blockedBy") or []
            if b.get("state") == "OPEN"]

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
    name="issue-$number-review"
    prompt="code-review $base #$number"
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
    name="issue-$number"
    prompt="implement #$number"
    local label tab_args
    label="$(printf '#%s %s' "$number" "$title" \
             | head_chars $(( LABEL_TITLE_CHARS + ${#number} + 2 )))"
    tab_args=()
    [ -n "${HERDR_WORKSPACE_ID:-}" ] && tab_args=(--workspace "$HERDR_WORKSPACE_ID")
    # MMW_TICKET is how the gates inside this pane know which ticket they guard.
    pane="$(herdr tab create ${tab_args[@]+"${tab_args[@]}"} --cwd "$root" \
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

  local human
  if [ "$reviewing" = 1 ]; then human="#$number reviewer"; else human="#$number worker"; fi
  herdr pane rename "$pane" "$human" >/dev/null 2>&1
  herdr pane report-metadata "$pane" --source mmw --token "model=$model" \
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
  herdr agent list 2>/dev/null | MMW_TICKET_NUMBER="$1" MMW_OWN_PANE="${HERDR_PANE_ID:-}" python3 -c '
import json, os, sys

number = os.environ["MMW_TICKET_NUMBER"]
own_pane = os.environ.get("MMW_OWN_PANE") or None
try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)
agents = (payload.get("result") or {}).get("agents") or payload.get("agents") or []
live = dict((a.get("name"), a.get("pane_id")) for a in agents if a.get("name"))

worker = "issue-" + number
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

# ------------------------------------------------------------------ entry

[ -f "$MODELS" ] || refuse "no table at $MODELS"

case "${1:-}" in
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
