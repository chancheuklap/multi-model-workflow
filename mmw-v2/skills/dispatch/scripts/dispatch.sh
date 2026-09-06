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
#   dispatch.sh suspend <spec>
#
# Every form takes `--tools <directory>`, repeatable: where the scripts of other skills
# are — `lease.py` of the drive-target skill, `verify-ticket.py` of the verify-ticket
# skill. Other skills' scripts are found only in those directories. Two files belong
# to the toolbox itself, not to any skill, and are taken from the toolbox root (this
# skill directory two levels up): `install.sh` and `agents/assemble.py`.
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
# The skill lives under mmw-v2/skills/<name> of the toolbox checkout, so `install.sh`
# is two directories up. `verify-ticket.py` and `lease.py` belong to other skills and
# are found only in the directories `--tools` names (see the entry at the bottom).
INSTALLER="$(dirname "$(dirname "$SKILL_ROOT")")/install.sh"
# assemble.py sits next to install.sh under agents/: both belong to the toolbox, not
# to a skill, so they are not passed in with `--tools`.
ASSEMBLE="$(dirname "$INSTALLER")/agents/assemble.py"
VERIFY=""
LEASE=""

# The row a ticket with no `*-worker` label starts from.
DEFAULT_WORKER=junior-worker

MERGE_TRIES=3                # a worker's commit in its worktree can hold the .git lock while advance merges

AUTONOMOUS="You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work."
PIPELINE_FAULT="A fault in the pipeline itself is reported, not worked around: verify-ticket.py <n> --sub-issue pipeline <file>, then stop (rule 5 of that section)."
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

usage() {
  cat >&2 <<'USAGE'
usage: dispatch.sh check <spec>
       dispatch.sh advance <spec>
       dispatch.sh start <n> worker|reviewer|verifier
       dispatch.sh resume <n> "<text>"
       dispatch.sh status <spec>
       dispatch.sh reverify <spec>
       dispatch.sh summary <spec>
       dispatch.sh suspend <spec>
USAGE
  exit 2
}

# ------------------------------------------------------------------ small helpers

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

# This checkout's workspaces as a JSON list. One read of the workspace list.
workspace_rows() {
  local root
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || true
  { paseo workspace ls --json 2>/dev/null || true; } | \
  MMW_ROOT="$root" python3 -c '
import json, os, subprocess, sys

own = set()
git_root = os.path.realpath(os.environ.get("MMW_ROOT") or "")
if git_root:
    try:
        for prow in json.loads(subprocess.check_output(
                ["paseo", "project", "ls", "--json"], text=True)):
            if isinstance(prow, dict) and os.path.realpath(prow.get("path") or "") == git_root:
                own.update(x for x in (prow.get("projectId"), prow.get("name")) if x)
    except Exception:
        pass
try:
    rows = json.load(sys.stdin)
except Exception:
    print("[]")
    sys.exit(0)
if not isinstance(rows, list):
    print("[]")
    sys.exit(0)
out = []
for row in rows:
    if not isinstance(row, dict):
        continue
    theirs = row.get("project") or ""
    if own and theirs and theirs not in own:
        continue
    out.append(row)
print(json.dumps(out))
' 2>/dev/null
}

# workspaceId<TAB>cwd for issue-<n>, one read of the list.
workspace_row_for() {
  workspace_rows | MMW_SLUG="issue-$1" python3 -c '
import json, os, sys
from pathlib import Path

want = os.environ["MMW_SLUG"]
try:
    rows = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(rows, list):
    sys.exit(0)
for row in rows:
    if not isinstance(row, dict):
        continue
    if Path(row.get("cwd") or "").name != want:
        continue
    print((row.get("workspaceId") or "") + "\t" + (row.get("cwd") or ""))
    break
'
}

workspace_id_for() {
  workspace_row_for "$1" | cut -f1
}

workspace_cwd_for() {
  workspace_row_for "$1" | cut -f2
}

# Parent of this checkout's issue-* workspaces. lease.py count compares resolved
# paths, and those worktrees are not inside the git repo.
worktrees_root() {
  workspace_rows | python3 -c '
import json, sys
from pathlib import Path

try:
    rows = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if not isinstance(rows, list):
    sys.exit(0)
for row in rows:
    if not isinstance(row, dict):
        continue
    cwd = Path(row.get("cwd") or "")
    if not cwd.name.startswith("issue-"):
        continue
    parent = str(cwd.parent.resolve()) if cwd.name else ""
    if parent:
        print(parent)
        break
'
}

# ticket<TAB>id for every live worker. Extra `--label` arguments go first
# (ticket, spec); `mmw.kind=worker` is always last. Ticket is the issue-N
# cwd basename, empty when the cwd is not one.
agents_by_label() {
  { paseo ls -g --json "$@" --label mmw.kind=worker 2>/dev/null || true; } | python3 -c '
import json, re, sys
from pathlib import Path

try:
    rows = json.load(sys.stdin)
except Exception:
    rows = []
if not isinstance(rows, list):
    rows = []
issue = re.compile(r"^issue-(\d+)$")
for row in rows:
    if not isinstance(row, dict) or not row.get("id"):
        continue
    found = issue.match(Path(row.get("cwd") or "").name)
    ticket = found.group(1) if found else ""
    print(ticket + "\t" + row["id"])
'
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

# ------------------------------------------------------------------ the instance gate
#
# Several runs share one machine. `lease.py` hands each worktree a block of ports and a
# directory nothing else uses; this is the half that decides how many runs may be up at
# once, because only the dispatcher knows it is starting more than one.
#
# A repository that can isolate its product says nothing and gets the machine's limit. A
# repository that cannot — ports written into a container file, a callback registered at
# a fixed port, an installed product that hardcodes them — says so in `.mmw/target.json`:
#
#     "instance": {"max": 1, "why": "<what stops a second one>"}
#
# and its tickets are serialised. That is the honest fallback. The alternative is what
# 2026-09-05 did: five workers dispatched onto three fixed ports, one of them working.

# Prints `instance.max`, or nothing when the repository declares none. A file that is
# there but cannot be read is a fault, not "none declared": exit 2 with the reason.
target_max_instances() {
  python3 - "$1" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1]) / ".mmw" / "target.json"
if not path.exists():
    print("")
    sys.exit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, ValueError) as exc:
    print(f"dispatch: {path} cannot be read as JSON: {exc}", file=sys.stderr)
    sys.exit(2)
instance = data.get("instance") if isinstance(data, dict) else None
value = instance.get("max") if isinstance(instance, dict) else None
print(value if isinstance(value, int) and value > 0 else "")
PY
}

live_instances() {
  python3 "$LEASE" count "$1"
}

# Give a finished ticket's slot back. Returns 0 released, 1 refused (something still
# listens), 3 no lease was registered for that path.
release_lease() {
  local out
  if ! out="$(python3 "$LEASE" release "$1" 2>&1)"; then
    printf 'dispatch: lease not released for %s: %s\n' "$1" "$out" >&2
    return 1
  fi
  case "$out" in
    "no lease for"*) return 3 ;;
  esac
  return 0
}

# Prints workspaceId<TAB>cwd so start_one can claim a lease without a second list read.
ensure_workspace() {
  local number="$1" root="$2" title="$3" row existing project base json ident cwd
  row="$(workspace_row_for "$number")"
  existing="$(printf '%s\n' "$row" | cut -f1)"
  if [ -n "$existing" ]; then
    if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
      record_base_if_missing "$number" "$root"
    fi
    printf '%s\t0\n' "$row"
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
  ident="$(printf '%s' "$json" | python3 -c '
import json, sys
try:
    row = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((row.get("workspaceId") or "") + "\t" + (row.get("cwd") or ""))
')"
  cwd="$(printf '%s\n' "$ident" | cut -f2)"
  ident="$(printf '%s\n' "$ident" | cut -f1)"
  [ -n "$ident" ] || { echo "dispatch: workspace create printed no workspaceId" >&2; return 1; }

  if git -C "$root" rev-parse --verify --quiet "refs/heads/issue-$number" >/dev/null; then
    record_base_if_missing "$number" "$root"
  fi
  printf '%s\t%s\t1\n' "$ident" "$cwd"
}

archive_workspace() {
  local number="$1" ident cwd row
  row="$(workspace_row_for "$number")"
  cwd="$(printf '%s\n' "$row" | cut -f2)"
  ident="$(printf '%s\n' "$row" | cut -f1)"
  if [ -n "$cwd" ] && [ -f "$LEASE" ]; then
    release_lease "$cwd" || true
  fi
  [ -n "$ident" ] || return 0
  paseo workspace archive "$ident" >/dev/null \
    || echo "dispatch: could not archive the workspace for #$number" >&2
}

# ------------------------------------------------------------------ dispatch payload

emit_create_json() {
  [ -f "$ASSEMBLE" ] || refuse "no assemble.py at $ASSEMBLE"
  MMW_ASSEMBLE="$ASSEMBLE" python3 -c '
import importlib.util, json, os, sys

path = os.environ["MMW_ASSEMBLE"]
spec = importlib.util.spec_from_file_location("mmw_assemble", path)
if spec is None or spec.loader is None:
    print("dispatch: no assemble.py at " + path, file=sys.stderr)
    sys.exit(2)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
host = os.environ["MMW_HOST"]
settings = mod.create_agent_settings(host, os.environ["MMW_PERM"])
effort = os.environ["MMW_EFFORT"]
if effort and effort not in ("—", "-", ""):
    settings["thinkingOptionId"] = effort
payload = {
    "workspaceId": os.environ["MMW_WORKSPACE"],
    "title": os.environ["MMW_TITLE"],
    "provider": host + "/" + os.environ["MMW_MODEL"],
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
      prompt="Use the implement skill to work ticket #$number. $AUTONOMOUS $PRODUCT_RULES $PIPELINE_FAULT" ;;
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

  local workspace cwd created row
  row="$(ensure_workspace "$number" "$root" "$title")" \
    || refuse "could not open a workspace for issue-$number"
  workspace="$(printf '%s\n' "$row" | cut -f1)"
  cwd="$(printf '%s\n' "$row" | cut -f2)"
  created="$(printf '%s\n' "$row" | cut -f3)"

  if [ "$kind" = worker ]; then
    [ -f "$LEASE" ] \
      || refuse "no lease.py in any --tools directory, so no run can be given its own share of this machine. Pass --tools <the drive-target skill's scripts directory>, then dispatch again"
    [ -n "$cwd" ] \
      || refuse "could not read the workspace cwd for issue-$number, so no lease can be claimed"
    local claim_err
    if ! claim_err="$(python3 "$LEASE" claim "$cwd" 2>&1 >/dev/null)"; then
      if [ "$created" = 1 ] && [ -n "$workspace" ]; then
        paseo workspace archive "$workspace" >/dev/null \
          || echo "dispatch: could not archive the workspace for #$number" >&2
      fi
      refuse "issue-$number: $claim_err"
    fi
  fi

  local agent_title="#$number $kind"
  MMW_WORKSPACE="$workspace" MMW_TITLE="$agent_title" \
    MMW_HOST="$host" MMW_MODEL="$model" MMW_EFFORT="$effort" MMW_PERM="$perm" \
    MMW_TICKET="$number" MMW_KIND="$kind" MMW_SPEC="$spec" \
    MMW_PROFILE="$profile" MMW_PROMPT="$prompt" \
    emit_create_json
}

# ------------------------------------------------------------------ resume

resume_one() {
  local number="$1" text="$2" ident
  [ -n "$text" ] || refuse "resume needs the text to send"
  ident="$(agents_by_label --label "mmw.ticket=$number" | head -n 1 | cut -f2)"
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
    [ "${fields[0]}" = "GRADE" ] || continue
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
  echo "    bash $SELF --tools <drive-target scripts> --tools <verify-ticket scripts> advance $MMW_ADVANCE_SPEC"
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

  # A claim whose worker is gone keeps its ticket off the frontier for good: only the
  # closeout and the hand back to triage ever give a claim back, and the frontier takes
  # unassigned tickets alone. `--remove-assignee @me` is the whole write, so a ticket a
  # person took for themselves is left exactly as it is. Every release says so, because
  # `paseo ls` answers for this machine and no other: a worker of the same account on a
  # second machine would read here as a claim whose owner is gone, and this line is
  # where that shows.
  local released=0
  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      released=$((released + 1))
      echo "released the claim on #$number: it is open in the agent queue with no running worker of ours on it, so the worker that claimed it is gone" >&2
    else
      echo "dispatch: could not release the claim on #$number, so it stays off the frontier" >&2
    fi
  done

  local started=0 refused=0 held=0 live max_inst trees
  max_inst="$(target_max_instances "$root")" || exit 2
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    if [ -n "$max_inst" ]; then
      trees="$(worktrees_root)"
      if [ -n "$trees" ]; then
        live="$(live_instances "$trees")" \
          || refuse "could not count live instances under $trees"
      else
        live=0
      fi
      if [ "$live" -ge "$max_inst" ]; then
        # Not a refusal: the ticket keeps its label and its place on the frontier, and
        # the next advance starts it. Dispatching past what the machine holds is how a
        # night ends up with one worker working and four waiting on a port that will
        # never free (2026-09-05).
        held=$((held + 1))
        continue
      fi
    fi
    if bash "$SELF" ${TOOLS_ARGS[@]+"${TOOLS_ARGS[@]}"} start "$number" worker; then
      started=$((started + 1))
    else
      refused=$((refused + 1))
    fi
  done

  echo "advance #$spec: merged $merged, already in $skipped, released $released, started $started, refused $refused, held $held" >&2
  if [ "$held" -gt 0 ]; then
    echo "  $held ticket(s) held back: this product declares max $max_inst concurrent run(s); they start at the next advance" >&2
  fi
}

# ------------------------------------------------------------------ suspend

# ticket<TAB>id for every live worker labelled mmw.spec=<spec>.
live_workers() {
  agents_by_label --label "mmw.spec=$1" | awk -F '\t' '$1 != ""'
}

suspend_comment() {
  local spec="$1" when="$2" ident="$3"
  printf '%s\n%s\n' \
    "NIGHT SUSPENDED #$spec" \
    "The night on spec #$spec was suspended at $when, so this ticket has no verdict: nothing here says whether its work is finished."
  if [ -n "$ident" ]; then
    printf '%s\n' "Its worker $ident was interrupted (\`paseo archive\`); its workspace and its branch are untouched. The batch is taken up again where it stands with advance."
  else
    printf '%s\n' "No session of ours was working on it at that moment. Its workspace and its branch, if it has them, are untouched, and it keeps its label, so the next advance of #$spec starts it."
  fi
}

# Suspend the night without throwing its work away.
#
# Five things happen: every live worker of the batch is archived (`paseo archive`,
# which interrupts a running agent and drops it from the live list, workspace and
# branch stay), every ticket still in the agent queue is told the night was
# suspended, every OPEN ready-for-agent ticket assigned to this pipeline's account
# has that claim given back, every lease slot the batch holds is given back, and
# the main agent's heartbeat is deleted when the id file is still there. A batch
# dispatched again from scratch would throw the night's work away along with the
# night; `advance` after this takes the same workspaces up where they stand.
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

  local live number ident stopped=0
  live="$(live_workers "$spec")"
  while IFS=$'\t' read -r number ident; do
    [ -n "$ident" ] || continue
    if paseo archive "$ident" >/dev/null 2>&1; then
      stopped=$((stopped + 1))
    else
      echo "dispatch: could not archive $ident on #$number" >&2
      left=$((left + 1))
    fi
  done <<<"$live"

  local when commented=0
  when="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for number in $queued; do
    ident="$(printf '%s\n' "$live" | awk -F '\t' -v n="$number" '$1 == n { print $2; exit }')"
    if gh_ issue comment "$number" --body "$(suspend_comment "$spec" "$when" "$ident")" >/dev/null 2>&1; then
      commented=$((commented + 1))
    else
      echo "dispatch: could not comment on #$number, so nothing on it says the night was suspended" >&2
      left=$((left + 1))
    fi
  done

  local login claims=0
  login="$(gh_ api user --jq .login 2>/dev/null | tr -d '[:space:]')"
  if [ -n "$login" ]; then
    for number in $queued; do
      [ -n "$number" ] || continue
      if printf '%s' "$(gh_ issue view "$number" --json assignees 2>/dev/null)" \
           | MMW_LOGIN="$login" python3 -c '
import json, os, sys
login = os.environ["MMW_LOGIN"]
try:
    rows = (json.load(sys.stdin) or {}).get("assignees") or []
except Exception:
    raise SystemExit(1)
raise SystemExit(0 if login in [a.get("login") for a in rows if isinstance(a, dict)] else 1)
'; then
        if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
          claims=$((claims + 1))
          echo "gave back the claim on #$number: the night is suspended, so the next advance can start it again" >&2
        else
          echo "dispatch: could not give back the claim on #$number" >&2
          left=$((left + 1))
        fi
      fi
    done
  fi

  local cwd back=0 rc
  if [ -f "$LEASE" ]; then
    [ -n "$(worktrees_root)" ] \
      || echo "dispatch: no workspace of this checkout is standing, so a lease can be matched to a ticket only through a standing workspace; python3 $LEASE list shows what is still held, and claim reclaims a lease whose directory is gone" >&2
    for number in $batch; do
      cwd="$(workspace_cwd_for "$number")"
      [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
      [ -n "$cwd" ] || continue
      release_lease "$cwd"
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

  local hb
  hb="$git_dir/mmw-heartbeat-$spec"
  if [ -f "$hb" ]; then
    ident="$(tr -d '[:space:]' < "$hb")"
    if [ -n "$ident" ] && paseo heartbeat delete "$ident" >/dev/null 2>&1; then
      rm -f "$hb"
    else
      echo "dispatch: could not delete heartbeat $ident for #$spec" >&2
      left=$((left + 1))
    fi
  fi

  echo "suspend #$spec: stopped $stopped, commented $commented, slots given back $back, claims given back $claims"
  [ "$left" -eq 0 ] || exit 1
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
  [ -f "$VERIFY" ] || refuse "no verify-ticket.py in any --tools directory; pass --tools <the verify-ticket skill's scripts directory>"

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

# `--tools <dir>` may appear anywhere and any number of times. Everything else is
# positional. A script of another skill is looked up by basename in those directories,
# in the order given, and nowhere else.
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
LEASE="$(tool lease.py || true)"
VERIFY="$(tool verify-ticket.py || true)"
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
  "" | -h | --help)
    usage
    ;;
  *)
    usage
    ;;
esac
