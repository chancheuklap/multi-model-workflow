#!/usr/bin/env bash
#
# Start an agent on a ticket, move a spec's batch forward, or report on one.
#
#   dispatch.sh check <spec>
#   dispatch.sh advance <spec>
#   dispatch.sh start <n> worker|reviewer|verifier
#   dispatch.sh resume <n> "<text>"
#   dispatch.sh status <spec>
#   dispatch.sh reverify <spec>
#   dispatch.sh summary <spec>
#
# The ticket number and the kind of agent are the whole input for `start`. Which
# of the worker rows a worker session starts from is the ticket's own `*-worker`
# label, so one ticket keeps the same worker every time it is started. Which
# host, model, thinking level and permissions the session gets come from that
# row of `models.md`, expanded into the fields `create_agent` accepts. `start`
# and `advance` always print one `create_agent` object per ticket.
#
# Exit codes are documented in SKILL.md next to this script.

set -uo pipefail

LABEL_TITLE_CHARS=20         # how much of the ticket title fits on a workspace title

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
MODELS="$SKILL_ROOT/models.md"
STATUS="$SKILL_ROOT/scripts/status.py"
VERIFIER_MD="$(realpath "$SKILL_ROOT/references/verifier.md" 2>/dev/null || true)"
# The skill lives under mmw-v2/skills/<name>, so `install.sh` is two directories up
# and `verify-ticket.py` is the sibling skill.
INSTALLER="$(dirname "$(dirname "$SKILL_ROOT")")/install.sh"
VERIFY="$(dirname "$SKILL_ROOT")/verify-ticket/scripts/verify-ticket.py"

# The row a ticket with no `*-worker` label starts from.
DEFAULT_WORKER=junior-worker

MERGE_TRIES=3                # a worker's commit in its worktree can hold the .git lock while advance merges

AUTONOMOUS="You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work."

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into
# --json output under it, which no JSON reader can parse.
gh_() {
  env -u CLICOLOR_FORCE -u CLICOLOR gh "$@"
}

refuse() {
  echo "dispatch: $1" >&2
  exit 2
}

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh check <spec>
       dispatch.sh advance <spec>
       dispatch.sh start <n> worker|reviewer|verifier
       dispatch.sh resume <n> "<text>"
       dispatch.sh status <spec>
       dispatch.sh reverify <spec>
       dispatch.sh summary <spec>
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

# ------------------------------------------------------------------ models.md

# Prints "host<TAB>model<TAB>effort<TAB>permissions" for the agent asked for: the
# first of its rows with `bypass`, since an agent that is both a session and a
# subagent (the reviewer) has one row per host and only one of them starts a
# session; when no row has any, the first row, so the caller's refusal can name it.
# Backticks are markdown, not part of any value.
row_for_role() {
  awk -F'|' -v want="$1" '
    function trim(s) { gsub(/^[ \t`]+/, "", s); gsub(/[ \t`]+$/, "", s); return s }
    /^[ \t]*\|/ && NF == 7 && trim($2) == want {
      row = trim($3) "\t" trim($4) "\t" trim($5) "\t" trim($6)
      if (first == "") first = row
      perm = trim($6)
      if (perm == "bypass") { print row; found = 1; exit }
    }
    END { if (!found && first != "") print first }
  ' "$MODELS"
}

# Prints every agent name in `models.md` a ticket may ask for by label, one per line.
worker_roles() {
  awk -F'|' '
    function trim(s) { gsub(/^[ \t`]+/, "", s); gsub(/[ \t`]+$/, "", s); return s }
    /^[ \t]*\|/ && NF == 7 {
      name = trim($2)
      if (name ~ /-worker$/ && !seen[name]++) print name
    }
  ' "$MODELS"
}

# ------------------------------------------------------------------ the ticket

# Prints three lines when the ticket is ready to be worked on — its worker labels,
# its title, then the spec number from `## Parent` — and one line prefixed with
# REFUSE when it is not. The worker labels are the ticket's own labels ending in
# `-worker`, space separated, and the first line is empty when it carries none.
read_ticket() {
  local number="$1" json
  json="$(gh_ issue view "$number" --json state,labels,blockedBy,title,body 2>/dev/null)" \
    || { echo "REFUSE could not read ticket #$number from the tracker"; return; }
  printf '%s' "$json" | MMW_TICKET_NUMBER="$number" python3 -c '
import json, os, re, sys

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
grades = sorted(name for name in labels if name and name.endswith("-worker"))
body = ticket.get("body") or ""
found = re.search(r"(?ms)^## Parent\s*\n+.*?\#(\d+)", body)
spec = found.group(1) if found else ""

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
record_base_if_missing() {
  local number="$1" root="$2" found
  if [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base")" ]; then
    found="$(git -C "$root" merge-base HEAD "issue-$number" 2>/dev/null)"
    [ -z "$found" ] && found="$(git -C "$root" rev-parse HEAD 2>/dev/null)"
    [ -n "$found" ] && git -C "$root" config "branch.issue-$number.mmw-base" "$found"
  fi
  if [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base-branch")" ]; then
    git -C "$root" config "branch.issue-$number.mmw-base-branch" \
      "$(git -C "$root" rev-parse --abbrev-ref HEAD)"
  fi
}

# ------------------------------------------------------------------ Paseo

project_id_for() {
  local root="$1"
  MMW_ROOT="$root" python3 -c '
import json, os, subprocess, sys

root = os.path.realpath(os.environ["MMW_ROOT"])
raw = subprocess.check_output(["paseo", "project", "ls", "--json"], text=True)
try:
    rows = json.loads(raw)
except Exception:
    sys.exit(0)
if not isinstance(rows, list):
    sys.exit(0)
for row in rows:
    if not isinstance(row, dict):
        continue
    path = os.path.realpath(row.get("path") or "")
    if path == root:
        ident = row.get("projectId") or ""
        if ident:
            print(ident)
        break
' 2>/dev/null
}

workspace_id_for() {
  local number="$1"
  MMW_SLUG="issue-$number" python3 -c '
import json, os, subprocess, sys
from pathlib import Path

want = os.environ["MMW_SLUG"]
raw = subprocess.check_output(["paseo", "workspace", "ls", "--json"], text=True)
try:
    rows = json.loads(raw)
except Exception:
    sys.exit(0)
if not isinstance(rows, list):
    sys.exit(0)
for row in rows:
    if not isinstance(row, dict):
        continue
    if Path(row.get("cwd") or "").name == want:
        ident = row.get("workspaceId") or ""
        if ident:
            print(ident)
        break
' 2>/dev/null
}

ensure_workspace() {
  local number="$1" root="$2" title="$3" existing project base json ident
  existing="$(workspace_id_for "$number")"
  if [ -n "$existing" ]; then
    if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
      record_base_if_missing "$number" "$root"
    fi
    printf '%s\n' "$existing"
    return 0
  fi
  project="$(project_id_for "$root")"
  [ -n "$project" ] \
    || { echo "dispatch: no Paseo project whose path is $root" >&2; return 1; }

  local ws_title
  ws_title="$(printf '#%s %s' "$number" "$(printf '%s' "$title" | head_chars "$LABEL_TITLE_CHARS")")"

  local -a extra
  if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
    extra=(--mode checkout-branch --branch "issue-$number")
  else
    base="$(git -C "$root" rev-parse --abbrev-ref HEAD)"
    [ -n "$base" ] && [ "$base" != HEAD ] \
      || { echo "dispatch: not on a named branch, so --base would be rejected" >&2; return 1; }
    extra=(--mode branch-off --new-branch "issue-$number" --base "$base")
  fi

  json="$(paseo workspace create --isolation worktree --path "$root" --project "$project" \
            --worktree-slug "issue-$number" --title "$ws_title" --json "${extra[@]}")" \
    || { echo "dispatch: could not create a workspace for issue-$number" >&2; return 1; }
  ident="$(printf '%s' "$json" | json_at workspaceId)"
  [ -n "$ident" ] || { echo "dispatch: workspace create printed no workspaceId" >&2; return 1; }

  if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
    record_base_if_missing "$number" "$root"
  fi
  printf '%s\n' "$ident"
}

archive_workspace() {
  local number="$1" ident
  ident="$(workspace_id_for "$number")"
  [ -n "$ident" ] || return 0
  paseo workspace archive "$ident" >/dev/null \
    || echo "dispatch: could not archive the workspace for #$number" >&2
}

# ------------------------------------------------------------------ dispatch payload

# permissions → create_agent settings. One mapping.
host_permission_settings() {
  case "$1" in
    claude) printf '%s\n' '{"modeId":"bypassPermissions"}' ;;
    codex)  printf '%s\n' '{"modeId":"full-access"}' ;;
    *)      printf '%s\n' '{"features":{"auto_accept":true}}' ;;
  esac
}

emit_create_json() {
  MMW_PERM_SETTINGS="$(host_permission_settings "$MMW_HOST")" python3 -c '
import json, os

host = os.environ["MMW_HOST"]
model = os.environ["MMW_MODEL"]
effort = os.environ["MMW_EFFORT"]
settings = json.loads(os.environ["MMW_PERM_SETTINGS"])
if effort and effort not in ("—", "-", ""):
    settings["thinkingOptionId"] = effort
payload = {
    "workspaceId": os.environ["MMW_WORKSPACE"],
    "title": os.environ["MMW_TITLE"],
    "provider": host + "/" + model,
    "settings": settings,
    "labels": {
        "mmw.ticket": os.environ["MMW_TICKET"],
        "mmw.kind": os.environ["MMW_KIND"],
        "mmw.spec": os.environ["MMW_SPEC"],
        "mmw.profile": os.environ["MMW_PROFILE"],
        "mmw.autonomous": "1",
    },
    "initialPrompt": os.environ["MMW_PROMPT"],
}
print(json.dumps(payload, ensure_ascii=False))
'
}

# ------------------------------------------------------------------ start

start_one() {
  local number="$1" kind="$2"
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
  [ -n "$spec" ] || refuse "ticket #$number has no spec number in ## Parent"

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

  local row host model effort perm
  row="$(row_for_role "$profile")"
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS has none"
  IFS=$'\t' read -r host model effort perm <<<"$row"
  case "$perm" in
    bypass) ;;
    *) refuse "$profile is a subagent: it is started by the skill that needs it, not from here" ;;
  esac

  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] \
    || refuse "not inside a git repository, so there is no working directory to give the session"

  local prompt
  case "$kind" in
    worker)
      prompt="Use the implement skill to work ticket #$number. $AUTONOMOUS" ;;
    reviewer)
      local base
      base="$(git -C "$root" config --get "branch.issue-$number.mmw-base")"
      [ -n "$base" ] \
        || refuse "no branch.issue-$number.mmw-base, so the reviewer has no commit to start from"
      prompt="Use the code-review skill to review ticket #$number from base commit $base. $AUTONOMOUS" ;;
    verifier)
      [ -n "$VERIFIER_MD" ] && [ -f "$VERIFIER_MD" ] \
        || refuse "no verifier prompt at $SKILL_ROOT/references/verifier.md"
      prompt="verify #$number 按 $VERIFIER_MD 行事" ;;
  esac

  local workspace
  workspace="$(ensure_workspace "$number" "$root" "$title")" \
    || refuse "could not open a workspace for issue-$number"

  local agent_title="#$number $kind"
  MMW_WORKSPACE="$workspace" MMW_TITLE="$agent_title" \
    MMW_HOST="$host" MMW_MODEL="$model" MMW_EFFORT="$effort" \
    MMW_TICKET="$number" MMW_KIND="$kind" MMW_SPEC="$spec" \
    MMW_PROFILE="$profile" MMW_PROMPT="$prompt" \
    emit_create_json
}

# ------------------------------------------------------------------ resume

resume_one() {
  local number="$1" text="$2" ident
  [ -n "$text" ] || refuse "resume needs the text to send"
  ident="$(
    MMW_TICKET_NUMBER="$number" python3 -c '
import json, os, subprocess, sys

number = os.environ["MMW_TICKET_NUMBER"]
raw = subprocess.check_output(
    ["paseo", "ls", "-g", "--json",
     "--label", "mmw.ticket=" + number,
     "--label", "mmw.kind=worker"],
    text=True)
try:
    rows = json.loads(raw)
except Exception:
    sys.exit(0)
if not isinstance(rows, list):
    sys.exit(0)
for row in rows:
    if isinstance(row, dict) and row.get("id"):
        print(row["id"])
        break
' 2>/dev/null
  )"
  [ -n "$ident" ] || refuse "no worker agent labelled mmw.ticket=$number"
  paseo send --no-wait "$ident" "$text" >/dev/null \
    || refuse "could not send to $ident"
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

  local providers
  providers="$(paseo provider ls --json 2>/dev/null)" || providers=""
  local role host
  for role in $(worker_roles) reviewer verifier; do
    host="$(row_for_role "$role" | cut -f1)"
    [ -n "$host" ] || continue
    MMW_HOST="$host" MMW_PROVIDERS="$providers" python3 -c '
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
' || { echo "dispatch: provider $host is not available" >&2; failed=1; }
  done

  local grades line number
  grades="$(python3 "$STATUS" --worker-grades "$spec")" \
    || { echo "dispatch: could not read the batch under #$spec" >&2; failed=1; grades=""; }
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    local -a fields marked
    read -r -a fields <<<"$line"
    number="${fields[1]}"
    marked=("${fields[@]:2}")
    case "${#marked[@]}" in
      0) ;;
      1) [ -n "$(row_for_role "${marked[0]}")" ] \
           || { echo "dispatch: #$number asks for ${marked[0]}, and $MODELS has no such row" >&2; failed=1; } ;;
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

  local plan
  plan="$(python3 "$STATUS" --advance-plan "$spec")" \
    || refuse "could not read the batch under #$spec"

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

  local archived
  for archived in "${just_merged[@]+"${just_merged[@]}"}"; do
    archive_workspace "$archived"
  done

  local started=0 refused=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    if bash "$SELF" start "$number" worker; then
      started=$((started + 1))
    else
      refused=$((refused + 1))
    fi
  done

  echo "advance #$spec: merged $merged, already in $skipped, started $started, refused $refused" >&2
}

# ------------------------------------------------------------------ reverify / summary

failing_ac_ids() {
  python3 -c '
import re, sys

text = sys.stdin.read()
ids = []
for line in text.splitlines():
    found = re.match(r"^- \[ \] ([A-Za-z0-9][A-Za-z0-9._-]*):", line.strip())
    if found:
        ids.append(found.group(1))
print("\n".join(ids))
'
}

reverify_spec() {
  local spec="$1"
  case "$spec" in *[!0-9]* | "") refuse "the spec number must be digits only, got $spec" ;; esac
  [ -f "$VERIFY" ] || refuse "no verify-ticket.py at $VERIFY"

  local root git_dir commit plan number rc printed ids login
  root="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$root" ] || refuse "not inside a git repository"
  git_dir="$(git -C "$root" rev-parse --git-dir)"
  commit="$(git -C "$root" rev-parse HEAD)"

  plan="$(python3 "$STATUS" --advance-plan "$spec")" \
    || refuse "could not read the batch under #$spec"

  local green=0 red=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }'); do
    printed="$(python3 "$VERIFY" "$number" --reverify 2>&1)"
    rc=$?
    printf '%s\n' "$printed"
    if [ "$rc" -eq 0 ]; then
      gh_ issue comment "$number" --body "$commit" >/dev/null
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
      ids="$(printf '%s\n' "$printed" | failing_ac_ids)"
      gh_ issue comment "$number" --body "$(printf '%s\n%s\n' "$commit" "$ids")" >/dev/null
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
  gh_ issue comment "$spec" --body "$body" >/dev/null \
    || refuse "could not post the night summary on #$spec"
  printf '%s\n' "$body"
}

# ------------------------------------------------------------------ entry

[ -f "$MODELS" ] || refuse "no models.md at $MODELS"

POSITIONAL=()
for arg in "$@"; do
  if [ "$arg" != "${arg#--}" ]; then
    case "${arg#--}" in
      json|run) refuse "$arg is no longer a flag" ;;
    esac
  fi
  POSITIONAL+=("$arg")
done
set -- "${POSITIONAL[@]+"${POSITIONAL[@]}"}"

case "${1:-}" in
  check)
    [ "$#" -eq 2 ] || usage
    case "$2" in *[!0-9]* | "") refuse "the spec number must be digits only, got $2" ;; esac
    check_machine "$2"
    ;;
  advance)
    [ "$#" -eq 2 ] || usage
    advance "$2"
    ;;
  start)
    [ "$#" -eq 3 ] || usage
    case "$2" in *[!0-9]* | "") refuse "ticket number must be digits only, got $2" ;; esac
    start_one "$2" "$3"
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
    ;;
  reverify)
    [ "$#" -eq 2 ] || usage
    reverify_spec "$2"
    ;;
  summary)
    [ "$#" -eq 2 ] || usage
    summary_spec "$2"
    ;;
  "" | -h | --help)
    usage
    ;;
  *)
    usage
    ;;
esac
