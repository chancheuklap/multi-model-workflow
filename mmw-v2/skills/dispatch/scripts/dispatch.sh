#!/usr/bin/env bash
#
# Start an agent on a ticket, move a spec's batch forward, or report on one.
#
#   dispatch.sh check <spec>
#   dispatch.sh advance <spec>
#   dispatch.sh land <n>
#   dispatch.sh start <n> worker|reviewer|verifier
#   dispatch.sh retract <n>
#   dispatch.sh wait <n> worker|reviewer|verifier
#   dispatch.sh resume <n> "<text>"
#   dispatch.sh status <spec>
#   dispatch.sh reverify <spec>
#   dispatch.sh summary <spec>
#   dispatch.sh suspend <spec>
#
# Every script this one calls is found by resolution, from this file's own path:
# `lease.py` of the drive-target skill and `verify-ticket.py` of the verify-ticket
# skill are in the `scripts/` of their own skills one directory over. One file belongs
# to the toolbox itself, not to any skill, and is taken from the toolbox root (this
# skill directory two levels up): `install.sh`. `--tools <directory>` is an override,
# repeatable: a directory given that way is searched before the resolved location.
#
# The ticket number and the kind of agent are the whole input for `start`. Which
# of the worker rows a worker session starts from is the ticket's own `*-worker`
# label, so one ticket keeps the same worker every time it is started. Which
# host, model and thinking level the session gets come from that
# row of the live table (~/.mmw/models.md), resolved against tonight's
# catalog and expanded into the fields `create_agent` accepts. `start`
# and `advance` always print one `create_agent` object per ticket. A second
# row for that agent is nested as `fallback`, itself a complete
# `create_agent` object; the caller strips `fallback` before the first call.
#
# Each command's exit codes are written beside that command, in the door that carries it;
# SKILL.md next to this script is the index of doors.

set -uo pipefail

LABEL_TITLE_CHARS=20         # how much of the ticket title fits on a workspace title

SELF="$(realpath "${BASH_SOURCE[0]}")"
SKILL_ROOT="$(dirname "$(dirname "$SELF")")"
if [ -n "${MMW_LIVE_MODELS:-}" ]; then
  MODELS="$MMW_LIVE_MODELS"
elif [ -n "${MMW_V2_HOME:-}" ]; then
  MODELS="$MMW_V2_HOME/.mmw/models.md"
else
  MODELS="$HOME/.mmw/models.md"
fi
export MMW_CATALOG_MODE="${MMW_CATALOG_MODE:-paseo}"
STATUS="$SKILL_ROOT/scripts/status.py"
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
# A `stop` that hangs would hold up the whole night, and a night is unattended.
STOP_TIMEOUT_S="${MMW_STOP_TIMEOUT_S:-300}"

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
       dispatch.sh land <n>
       dispatch.sh start <n> worker|reviewer|verifier
       dispatch.sh retract <n>
       dispatch.sh wait <n> worker|reviewer|verifier
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

# ------------------------------------------------------------------ live table

# Prints "host<TAB>resolved-model<TAB>effort" for the agent asked for.
row_for_role() {
  [ -f "$MODELS_PY" ] || refuse "no models.py at $MODELS_PY"
  MMW_MODELS_PY="$MODELS_PY" MMW_AGENT="$1" MMW_NTH="${2:-1}" python3 -c '
import importlib.util, os, sys
path = os.environ["MMW_MODELS_PY"]
spec = importlib.util.spec_from_file_location("mmw_models", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    print(mod.row_tsv(os.environ["MMW_AGENT"], int(os.environ["MMW_NTH"])))
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
# The batch is the parent link the tracker records, and nothing else. `## Parent` is
# prose written for a person: #193 opens that section with 「无 spec；本仓自建票。收口
# #188 的评审票外」, so any reader taking the first `#N` in it comes back with 188.
# That is how the three agents of #193 came to be labelled `mmw.spec=188`, where a
# `suspend 188` would have archived them. A ticket with no parent link belongs to no
# batch, and says so by carrying no spec label at all.
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

# The Paseo project this checkout belongs to, registering it when it is not registered
# yet. `paseo project create` answers with the existing project for a path it already
# knows, so asking which project a checkout is and asking for one to be made are the
# same call. Prints nothing when the daemon could not be asked.
ensure_project_id() {
  paseo project create "$1" --json 2>/dev/null | python3 -c '
import json, sys

try:
    row = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if isinstance(row, dict) and row.get("projectId"):
    print(row["projectId"])
'
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

# ticket<TAB>id<TAB>status for every live agent matching the `--label` filters.
# Callers pass `mmw.kind=<kind>` themselves; ticket and spec go first. Ticket is
# the issue-N cwd basename, empty when the cwd is not one.
agents_by_label() {
  { paseo ls -g --json "$@" 2>/dev/null || true; } | python3 -c '
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
    print(ticket + "\t" + row["id"] + "\t" + str(row.get("status") or ""))
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

# Whether an agent listing's status means it is still on the hook. `idle` is the
# subtle one: a reviewer that started its three axis subagents and ended its turn
# sits there for the whole of that work, so only an agent that is gone — `closed`,
# `error`, or not listed at all — has nobody left to do the job.
agent_is_live() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    running | initializing | idle) return 0 ;;
  esac
  return 1
}

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

# Give a finished ticket's slot back. Returns 0 released, 1 refused (something still
# listens), 3 no lease was registered for that path.
# The command `.mmw/target.json` names for taking this run's product down, or nothing
# when the repository declares none. A file that is there but cannot be read is a fault,
# not "none declared": the same rule `target_max_instances` follows.
target_stop_command() {
  python3 - "$1" <<'TARGET_STOP_PY'
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
value = data.get("stop") if isinstance(data, dict) else None
print(value if isinstance(value, str) and value.strip() else "")
TARGET_STOP_PY
}

# What a run leaves behind outlasts the run: the application's own processes, and the
# containers its stack brings up. The command that takes them down lives in the worktree
# and names that worktree's own compose project, so it runs only from inside — which
# means before the worktree is archived, because archiving deletes it. Nothing here ran
# it until 2026-09-07, and the shape of that was: the stack stays up, `lease.py` rightly
# refuses a slot something is still listening on, the worktree goes anyway, and the slot
# is held by a stack nothing can reach any more. Nine tickets and 36 containers had
# collected that way, and a night with two slots could only ever run one worker.
stop_product() {
  local cwd="$1" cmd out
  [ -n "$cwd" ] && [ -d "$cwd" ] || return 0
  cmd="$(target_stop_command "$cwd")" || return 2
  [ -n "$cmd" ] || return 0
  local -a runner=()
  command -v timeout >/dev/null 2>&1 && runner=(timeout "$STOP_TIMEOUT_S")
  if ! out="$(cd "$cwd" && "${runner[@]}" sh -c "$cmd" 2>&1)"; then
    printf 'dispatch: the product of %s did not stop: %s\n' "$cwd" \
      "$(printf '%s' "$out" | tail -3 | tr '\n' ' ')" >&2
    return 1
  fi
  return 0
}

# Stopping the product and giving its slot back are one act, and every caller wants both:
# a slot is free only once nothing listens on its ports, and `lease.py` is right to refuse
# one held by a live process rather than take it. Exit codes are `release_lease`'s.
give_slot_back() {
  stop_product "$1" || true
  release_lease "$1"
}

# `lease.py release` says which of the three outcomes happened in its exit code — 0 given
# back, 3 there was no lease to give back, anything else refused — so this reads the code
# and never the wording. It used to match the front of the sentence for "no lease", which
# meant `lease.py` could not reword its own output without silently breaking this caller.
release_lease() {
  local out rc
  out="$(python3 "$LEASE" release "$1" 2>&1)"
  rc=$?
  case "$rc" in
    0) return 0 ;;
    3) return 3 ;;
  esac
  printf 'dispatch: lease not released for %s: %s\n' "$1" "$out" >&2
  return 1
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
  project="$(ensure_project_id "$root")"
  [ -n "$project" ] \
    || { echo "dispatch: could not register a Paseo project for $root; ask the daemon what is wrong with \`paseo daemon status\`" >&2; return 1; }

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

# Archiving deletes the worktree, and the worktree is where the product's stop command
# lives — so a workspace whose slot did not come back is kept, not archived. Keeping it
# is recoverable (stop the product there and run this again); archiving it is not.
archive_workspace() {
  local number="$1" ident cwd row rc
  row="$(workspace_row_for "$number")"
  cwd="$(printf '%s\n' "$row" | cut -f2)"
  ident="$(printf '%s\n' "$row" | cut -f1)"
  if [ -n "$cwd" ] && [ -f "$LEASE" ]; then
    give_slot_back "$cwd"
    rc=$?
    if [ "$rc" = 1 ]; then
      echo "dispatch: #$number keeps its workspace — its product is still up, and archiving would delete the worktree its stop command lives in. Stop it in $cwd, then run this again" >&2
      return 1
    fi
  fi
  [ -n "$ident" ] || return 0
  paseo workspace archive "$ident" >/dev/null \
    || echo "dispatch: could not archive the workspace for #$number" >&2
}

# ------------------------------------------------------------------ dispatch payload

emit_create_json() {
  [ -f "$MODELS_PY" ] || refuse "no models.py at $MODELS_PY"
  MMW_MODELS_PY="$MODELS_PY" python3 -c '
import importlib.util, json, os, sys

path = os.environ["MMW_MODELS_PY"]
spec = importlib.util.spec_from_file_location("mmw_models", path)
if spec is None or spec.loader is None:
    print("dispatch: no models.py at " + path, file=sys.stderr)
    sys.exit(2)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def payload(host, model, effort):
    settings = mod.create_agent_settings(host)
    thinking = mod.thinking_option(host, effort)
    if thinking is not None:
        settings["thinkingOptionId"] = thinking
    body = {
        "workspaceId": os.environ["MMW_WORKSPACE"],
        "title": os.environ["MMW_TITLE"],
        "provider": host + "/" + model,
        "settings": settings,
        "notifyOnFinish": os.environ["MMW_KIND"] != "worker",
        "labels": {
            "mmw.ticket": os.environ["MMW_TICKET"],
            "mmw.kind": os.environ["MMW_KIND"],
            "mmw.autonomous": "1",
        },
        "initialPrompt": os.environ["MMW_PROMPT"],
    }
    if os.environ["MMW_SPEC"]:
        body["labels"]["mmw.spec"] = os.environ["MMW_SPEC"]
    return body

rows = [line for line in (os.environ.get("MMW_ROWS") or "").splitlines() if line.strip()]
if not rows:
    print("dispatch: no live-table row to emit", file=sys.stderr)
    sys.exit(2)

def parse_row(line):
    host, model, effort = line.split("\t")[:3]
    return host, model, effort

host, model, effort = parse_row(rows[0])
primary = payload(host, model, effort)
if len(rows) > 1:
    host, model, effort = parse_row(rows[1])
    primary["fallback"] = payload(host, model, effort)
print(json.dumps(primary, ensure_ascii=False))
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
  # A ticket outside any batch is startable: it is dispatched one at a time and landed
  # with `land <n>`, which asks for a ticket number and never a spec. What it does not
  # get is a spec label, so no batch command ever picks it up as one of its own.

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

  local row host model effort fb_row
  row="$(row_for_role "$profile")" || exit 2
  [ -n "$row" ] || refuse "#$number needs the $profile row, and $MODELS has none"
  IFS=$'\t' read -r host model effort <<<"$row"
  fb_row="$(row_for_role "$profile" 2)" || exit 2

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
      prompt="Use the verdict skill to verify ticket #$number. $AUTONOMOUS $PRODUCT_RULES" ;;
  esac

  local workspace cwd created ws_row
  ws_row="$(ensure_workspace "$number" "$root" "$title")" \
    || refuse "could not open a workspace for issue-$number"
  workspace="$(printf '%s\n' "$ws_row" | cut -f1)"
  cwd="$(printf '%s\n' "$ws_row" | cut -f2)"
  created="$(printf '%s\n' "$ws_row" | cut -f3)"

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

  local agent_title="#$number $kind" rows
  rows="$row"
  [ -z "$fb_row" ] || rows="$row"$'\n'"$fb_row"
  MMW_WORKSPACE="$workspace" MMW_TITLE="$agent_title" \
    MMW_ROWS="$rows" \
    MMW_TICKET="$number" MMW_KIND="$kind" MMW_SPEC="$spec" \
    MMW_PROMPT="$prompt" \
    emit_create_json
}

# ------------------------------------------------------------------ retract

# Undo what start left behind when create_agent never ran: archive the workspace,
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

  local live ident
  live="$(agents_by_label --label "mmw.ticket=$number" | head -n 1)"
  ident="$(printf '%s\n' "$live" | cut -f2)"
  if agent_is_live "$(printf '%s\n' "$live" | cut -f3)"; then
    refuse "#$number still has a live agent $ident; retract is for a start whose create_agent never ran"
  fi

  local cwd archived=0 slot=0 claim=0 rc
  cwd="$(workspace_cwd_for "$number")"
  [ -n "$cwd" ] || cwd="$(lease_worktree_for "$number")"
  if [ -n "$cwd" ]; then
    [ -f "$LEASE" ] \
      || refuse "no lease.py in any --tools directory, so the slot cannot be given back. Pass --tools <the drive-target skill's scripts directory>, then retract again"
    if give_slot_back "$cwd"; then
      slot=1
    fi
  fi
  if [ -n "$(workspace_id_for "$number")" ]; then
    archive_workspace "$number" && archived=1
  fi

  give_claim_back "$number"
  case "$?" in
    0) claim=1 ;;
    2) echo "dispatch: could not give back the claim on #$number" >&2 ;;
  esac

  echo "retract #$number: archived $archived, slot given back $slot, claim given back $claim" >&2
}

# ------------------------------------------------------------------ resume

# Two ways this fails, and they call for opposite things. No such worker is final:
# nothing will change by sending again. A worker that is there but will not take the
# message is temporary: it is in a turn, and a turn ends.
#
# Which one it is comes from what this already knows rather than from reading the
# error text. `paseo send` reports every failure as `SEND_FAILED` with the reason in
# one English sentence (`Agent not found: …`, `A foreground turn is already active`),
# and matching on that sentence would break the day it is reworded. It is not needed:
# the agent was just found by label, so a failure after that is not "no such worker".
#
# The distinction is worth drawing because the old code gave both exit 2, whose
# documented meaning is "read status, do not send again" — turning a three-minute
# wait into a permanent answer. On 2026-09-07 (#211) a worker was left unreachable
# this way and a five-hour session with 16 commits on its branch had to be killed.
resume_one() {
  local number="$1" text="$2" ident out
  [ -n "$text" ] || refuse "resume needs the text to send"
  ident="$(agents_by_label --label "mmw.ticket=$number" --label mmw.kind=worker | head -n 1 | cut -f2)"
  [ -n "$ident" ] || refuse "no worker agent labelled mmw.ticket=$number"
  if out="$(paseo send --no-wait "$ident" "$text" 2>&1)"; then
    return 0
  fi
  echo "dispatch: the worker $ident on #$number did not take the message" >&2
  [ -n "$out" ] && printf '  %s\n' "$out" >&2
  echo "dispatch: it is most likely in a turn — wait, then run resume again. If it keeps refusing, ask \`get_agent_status\` for this agent: an \`activeTurn\` of null with the send still failing is a stuck session, and the only way out is to replace it" >&2
  exit 3
}

# ------------------------------------------------------------------ wait

# The first line of the newest comment whose first line is this kind's result:
# worker `ALL MET` / `HANDOFF REQUIRED`, reviewer `REVIEW `, verifier `VERDICT`.
result_first_line() {
  local number="$1" kind="$2"
  gh_ issue view "$number" --json comments 2>/dev/null | MMW_KIND="$kind" python3 -c '
import json, os, sys

kind = os.environ["MMW_KIND"]
prefixes = {
    "worker": ("ALL MET", "HANDOFF REQUIRED"),
    "reviewer": ("REVIEW ",),
    "verifier": ("VERDICT",),
}.get(kind) or ()
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
found = ""
for row in data.get("comments") or []:
    if isinstance(row, dict):
        body = row.get("body") or ""
    else:
        body = str(row or "")
    stripped = body.strip()
    head = stripped.splitlines()[0].strip() if stripped else ""
    if any(head.startswith(p) for p in prefixes):
        found = head
if found:
    print(found)
'
}

wait_no_result() {
  local number="$1" kind="$2" ident="$3"
  case "$kind" in
    reviewer)
      echo "dispatch: reviewer $ident on #$number stopped with no REVIEW comment: paseo logs $ident" >&2
      ;;
    verifier)
      echo "dispatch: verifier $ident on #$number stopped with no VERDICT comment: paseo logs $ident" >&2
      ;;
    *)
      echo "dispatch: worker $ident on #$number stopped with no ALL MET or HANDOFF REQUIRED comment: paseo logs $ident" >&2
      ;;
  esac
  exit 1
}

# Print the first line of the result comment left by the agent labelled
# mmw.ticket=<n> mmw.kind=<kind>. The ticket is read first, so an agent that has
# already written its result returns at once — which is the whole of it on the
# ordinary path, since what wakes a caller is that agent finishing.
#
# When the comment is not there yet this waits MMW_WAIT_S seconds (default 90) and then
# exits 3, and running it again is how a host that stops waiting on a long command is
# survived. No host kills such a command: all of them move it to the background and hand
# back no exit code, and the bound has to stay under the shortest of those — 30 seconds
# on Cursor, 120 on Grok Build and Claude Code (measured 2026-09-06). Set MMW_WAIT_S
# below the host's own bound when it is shorter than this default.
#
# The waiting is this function's, not `paseo wait`'s. What `paseo wait` waits for is the
# agent going from busy to idle, and it returns at once for an agent that is already
# idle — which is the state of an agent between turns, doing exactly what it was told.
# Handing the whole budget to it therefore returns in milliseconds in the one case this
# fallback exists for, and `run it again` becomes a loop with no beat in it, spending one
# turn of the caller per round. So the budget is spent here: `paseo wait` for as long as
# the agent is busy, the ticket read after each round, and a fixed beat between rounds
# when it is not. Writes nothing: no ticket comment, no agent command but `paseo wait`.
wait_one() {
  local number="$1" kind="$2"
  case "$kind" in
    worker|reviewer|verifier) ;;
    *) refuse "the second argument is worker, reviewer or verifier, got $kind" ;;
  esac

  local head ident status
  head="$(result_first_line "$number" "$kind")"
  if [ -n "$head" ]; then
    printf '%s\n' "$head"
    return 0
  fi

  ident="$(agents_by_label --label "mmw.ticket=$number" --label "mmw.kind=$kind" | head -n 1 | cut -f2)"
  [ -n "$ident" ] || refuse "no $kind agent labelled mmw.ticket=$number"

  local budget="${MMW_WAIT_S:-90}" beat="${MMW_WAIT_BEAT_S:-10}" spent=0 round_start
  while [ "$spent" -lt "$budget" ]; do
    round_start="$(date +%s)"
    paseo wait "$ident" --timeout "$((budget - spent))" >/dev/null 2>&1 || true
    head="$(result_first_line "$number" "$kind")"
    if [ -n "$head" ]; then
      printf '%s\n' "$head"
      return 0
    fi
    spent=$((spent + $(date +%s) - round_start))
    [ "$spent" -lt "$budget" ] || break
    sleep "$beat"
    spent=$((spent + beat))
  done

  # An agent that is alive is still on the hook, whatever it is doing between turns.
  # `idle` is not idle: an agent that has handed work to subagents and ended its turn
  # sits there for the whole of that work, doing exactly what it was told. Reading that
  # as "stopped" sends the caller to a fallback while a healthy agent is mid-job; on
  # 2026-09-06 that closed #162 on a thinner review than the one that arrived 50 seconds
  # later, and did the same to #159. Only an agent that is gone — `closed`, `error`, or
  # no longer listed — has nobody left to do the job.
  status="$(agents_by_label --label "mmw.ticket=$number" --label "mmw.kind=$kind" | head -n 1 | cut -f3 | tr '[:upper:]' '[:lower:]')"
  if agent_is_live "$status"; then
    echo "still working: run wait again" >&2
    exit 3
  fi
  wait_no_result "$number" "$kind" "$ident"
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
  local role host host_line hosts="" diag
  for role in $(worker_roles) reviewer verifier; do
    host_line="$(row_for_role "$role")" || { failed=1; continue; }
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
      echo "dispatch: could not take the claim off #$number, so it stays off the frontier" >&2
    fi
  done

  local started=0 refused=0 held=0 live max_inst trees
  max_inst="$(target_max_instances "$root")" || exit 2
  # Every issue workspace of a checkout sits under one directory, so this is asked for
  # once rather than once per ticket — two Paseo calls each. It is asked again only
  # while the answer is still empty, which is the state before this checkout has any
  # workspace at all: the first `start` makes one, and from then on the count the gate
  # reads has somewhere to be counted. A repository that declares no cap never needs the
  # directory, and is not made to pay for finding it.
  trees=""
  [ -z "$max_inst" ] || trees="$(worktrees_root)"
  for number in $(printf '%s\n' "$plan" | awk '$1 == "DISPATCH" { print $2 }'); do
    if [ -n "$max_inst" ]; then
      [ -n "$trees" ] || trees="$(worktrees_root)"
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

# ------------------------------------------------------------------ landing

# Land one ticket.
#
# Landing is what closing a ticket does not do: merge the branch, archive the
# workspace (which takes the agents inside it and deletes the worktree), give the
# slot back, and give the claim back. `advance` does it for a batch after a merge;
# this does it for one ticket, and asks for a ticket number rather than a spec —
# which is the whole point. A ticket dispatched outside a night belongs to no spec,
# so before this there was no command it could be landed with, and its agents, its
# worktree and its slot stayed until somebody noticed.
#
# Order is fixed and the reason is the measurement: archiving a workspace deletes
# its directory, so a branch not yet in HEAD has to be merged first or the work has
# to be rebuilt from the branch to get it back.
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

  local merged=0 archived=0 released=0 kept=0 unmerged=0 number branch rc
  while IFS= read -r number; do
    [ -n "$number" ] || continue
    branch="$(ticket_branch "$number")"
    if ! git -C "$root" rev-parse --verify --quiet "refs/heads/$branch" >/dev/null; then
      continue
    fi
    if git -C "$root" merge-base --is-ancestor "$branch" HEAD 2>/dev/null; then
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
  done < <(printf '%s\n' "$plan" | awk '$1 == "MERGE" { print $2 }')

  for number in $(printf '%s\n' "$plan" | awk '$1 == "RELEASE" { print $2 }'); do
    if gh_ issue edit "$number" --remove-assignee @me >/dev/null 2>&1; then
      released=$((released + 1))
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
  [ "$unmerged" -eq 0 ] || return 1
}

# ------------------------------------------------------------------ suspend

# ticket<TAB>id<TAB>status for every live worker labelled mmw.spec=<spec>.
live_workers() {
  agents_by_label --label "mmw.spec=$1" --label mmw.kind=worker | awk -F '\t' '$1 != ""'
}

suspend_comment() {
  local spec="$1" when="$2" ident="$3"
  printf '%s\n%s\n' \
    "NIGHT SUSPENDED #$spec" \
    "The night on spec #$spec was suspended at $when, so this ticket has no verdict: nothing here says whether its work is finished."
  if [ -n "$ident" ]; then
    printf '%s\n' "Its worker $ident was interrupted (\`paseo archive --force\`); its workspace and its branch are untouched. The batch is taken up again where it stands with advance."
  else
    printf '%s\n' "No session of ours was working on it at that moment. Its workspace and its branch, if it has them, are untouched, and it keeps its label, so the next advance of #$spec starts it."
  fi
}

# Suspend the night without throwing its work away.
#
# Four things happen: every live worker of the batch is archived (`paseo archive
# --force`, which interrupts a running agent and drops it from the live list, workspace
# and branch stay), every ticket still in the agent queue is told the night was
# suspended, every OPEN ready-for-agent ticket assigned to this pipeline's account
# has that claim given back, and every lease slot the batch holds is given back. A batch
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

  # `--force` is what interrupts a worker mid-turn: plain `paseo archive` refuses a
  # running agent and says to use it. Without it this loop archived only the workers that
  # happened to be between turns — and a worker in the middle of one is the whole reason
  # to suspend a night.
  local live number ident stopped=0 still_live=""
  live="$(live_workers "$spec")"
  while IFS=$'\t' read -r number ident _; do
    [ -n "$ident" ] || continue
    if paseo archive --force "$ident" >/dev/null 2>&1; then
      stopped=$((stopped + 1))
    else
      echo "dispatch: could not archive $ident on #$number, so its worker is still running" >&2
      still_live="$still_live $number"
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

  local claims=0
  for number in $queued; do
    [ -n "$number" ] || continue
    give_claim_back "$number"
    case "$?" in
      0)
        claims=$((claims + 1))
        echo "gave back the claim on #$number: the night is suspended, so the next advance can start it again" >&2
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
    # `--tools` is forwarded because the judges of a criterion are named bare and are
    # found only in the directories it names. Without it every interface criterion of
    # every ticket fails `command not found`, and the branch below would reopen and hand
    # back a whole night of finished work for a fault in this command line.
    printed="$(python3 "$VERIFY" "$number" --reverify ${TOOLS_ARGS[@]+"${TOOLS_ARGS[@]}"} 2>&1)"
    rc=$?
    printf '%s\n' "$printed"
    # 2 is `the run could not start`, which says nothing about the ticket. Reading it as
    # a red ticket is how one broken invocation becomes a batch of reopened tickets.
    if [ "$rc" -eq 2 ]; then
      echo "dispatch: #$number could not be re-run, so nothing was judged; the rest of this reverify is skipped" >&2
      exit 2
    fi
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
  "" | -h | --help)
    usage
    ;;
  *)
    usage
    ;;
esac
