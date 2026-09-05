#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh check|advance|advanceconflict|advancedirty
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh start-worker|start-reviewer|start-verifier
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh resume|reverify|summary|start-json|start-norun
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh all
#
# A fake `paseo` and a fake `gh` sit in front of the real ones on PATH and write every
# call they receive to a log, one call per line, fields joined by ` :: `. What the
# script does to Paseo and to the tracker is therefore checkable without a daemon,
# a network, or a ticket. The last line of a passing run is the scenario's EXPECT
# string; everything before it says what was checked.

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$HERE")"
DISPATCH="$SKILL/scripts/dispatch.sh"

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/paseo-state"

cat > "$TMP/bin/paseo" <<'FAKE'
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path

log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("paseo" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")

args = sys.argv[1:]
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
state.mkdir(parents=True, exist_ok=True)
scenario = os.environ.get("MMW_FAKE_PASEO_SCENARIO", "")


def load(name):
    path = state / name
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save(name, rows):
    (state / name).write_text(json.dumps(rows), encoding="utf-8")


def opt(flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return ""


def labels_from_args():
    wanted = []
    i = 0
    while i < len(args):
        if args[i] == "--label" and i + 1 < len(args):
            wanted.append(args[i + 1])
            i += 2
            continue
        i += 1
    return wanted


if args[:2] == ["provider", "ls"]:
    grok = "unavailable" if scenario == "provider-down" else "available"
    print(json.dumps([
        {"provider": "grok", "status": grok, "label": "Grok"},
        {"provider": "claude", "status": "available", "label": "Claude"},
        {"provider": "codex", "status": "available", "label": "Codex"},
    ]))
    sys.exit(0)

if args[:2] == ["provider", "models"]:
    print(json.dumps([{"id": "grok-4.6", "thinkingOptionIds": ["high", "xhigh"]}]))
    sys.exit(0)

if args[:2] == ["project", "ls"]:
    root = os.environ.get("MMW_FAKE_PROJECT_PATH")
    if not root:
        try:
            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True).strip()
        except Exception:
            root = os.getcwd()
    print(json.dumps([{
        "projectId": "prj_test",
        "name": "repo",
        "kind": "git",
        "path": root,
    }]))
    sys.exit(0)

if args[:2] == ["workspace", "ls"]:
    print(json.dumps(load("workspaces.json")))
    sys.exit(0)

if args[:2] == ["workspace", "create"]:
    slug = opt("--worktree-slug") or "issue-0"
    path = opt("--path") or os.getcwd()
    mode = opt("--mode")
    title = opt("--title") or slug
    if mode == "branch-off":
        new_branch = opt("--new-branch")
        base = opt("--base")
        subprocess.run(["git", "-C", path, "branch", new_branch, base], check=False)
    ident = "wks_" + slug.replace("/", "_")
    cwd = str(state / slug)
    Path(cwd).mkdir(parents=True, exist_ok=True)
    rows = load("workspaces.json")
    rows.append({
        "workspaceId": ident,
        "project": "repo",
        "name": title,
        "isolation": "worktree",
        "cwd": cwd,
    })
    save("workspaces.json", rows)
    print(json.dumps({
        "workspaceId": ident,
        "project": "repo",
        "name": title,
        "isolation": "worktree",
        "cwd": cwd,
    }))
    sys.exit(0)

if args[:2] == ["workspace", "archive"]:
    ident = args[2] if len(args) > 2 else ""
    rows = [w for w in load("workspaces.json") if w.get("workspaceId") != ident]
    save("workspaces.json", rows)
    print(json.dumps({"workspaceId": ident, "archived": True}))
    sys.exit(0)

if args[:1] == ["run"]:
    title = opt("--title") or "agent"
    ident = "agt_" + title.replace("#", "").replace(" ", "_")
    labs = {}
    for item in labels_from_args():
        if "=" in item:
            k, v = item.split("=", 1)
            labs[k] = v
    prompt = args[-1] if args else ""
    rows = load("agents.json")
    rows.append({
        "id": ident,
        "name": title,
        "status": "running",
        "cwd": str(state / ("issue-" + labs.get("mmw.ticket", "0"))),
        "labels": labs,
        "prompt": prompt,
    })
    save("agents.json", rows)
    print(json.dumps({
        "agentId": ident,
        "status": "running",
        "provider": opt("--provider"),
        "cwd": str(state),
        "title": title,
    }))
    sys.exit(0)

if args[:1] == ["ls"]:
    wanted = {}
    for item in labels_from_args():
        if "=" in item:
            k, v = item.split("=", 1)
            wanted[k] = v
    out = []
    for row in load("agents.json"):
        have = row.get("labels") or {}
        if all(have.get(k) == v for k, v in wanted.items()):
            public = {k: v for k, v in row.items() if k != "labels"}
            out.append(public)
    print(json.dumps(out))
    sys.exit(0)

if args[:1] == ["send"]:
    print(json.dumps({"ok": True}))
    sys.exit(0)

if args[:1] == ["inspect"]:
    print(json.dumps({"LastUsage": None, "PendingPermissions": []}))
    sys.exit(0)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env bash
line=gh
for a in "$@"; do line="$line :: $a"; done
echo "$line" >> "$MMW_TEST_LOG"
case "$*" in
  *"--json state,labels,blockedBy,title,body"*|*"--json state,labels,blockedBy,title"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
want = os.environ.get("MMW_WANT", "")
body = os.environ.get("FAKE_GH_BODY", "## Parent\n\n#76, Implementation Decisions\n")
if path:
    rows = json.load(open(path))
    try:
        n = int(want)
    except Exception:
        n = None
    found = next((t for t in rows if t.get("number") == n), None)
    if found is not None:
        print(json.dumps({
            "state": found.get("state", "OPEN"),
            "labels": [{"name": n} for n in found.get("labels", ["ready-for-agent"])],
            "blockedBy": {"nodes": found.get("blockedBy", [])},
            "title": found.get("title", "a ticket"),
            "body": found.get("body", body),
        }))
        raise SystemExit
print(json.dumps({
    "state": os.environ.get("FAKE_GH_STATE", "OPEN"),
    "labels": [{"name": n} for n in os.environ.get("FAKE_GH_LABELS", "ready-for-agent").split(",") if n],
    "blockedBy": {"nodes": [{"number": int(b.split(":")[0]), "state": b.split(":")[1]}
                            for b in os.environ.get("FAKE_GH_BLOCKERS", "").split(",") if b]},
    "title": os.environ.get("FAKE_GH_TITLE",
                            "landing 7 of 15: a new skill called dispatch"),
    "body": body,
}))
' ;;
  *"/sub_issues"*)
    python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
print(json.dumps([{"number": t["number"]} for t in rows]))
' ;;
  *"--json state,labels,assignees,blockedBy,comments"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t["number"] == want), {})
print(json.dumps({
    "state": found.get("state", "OPEN"),
    "labels": [{"name": n} for n in found.get("labels", ["ready-for-agent"])],
    "assignees": [{"login": n} for n in found.get("assignees", [])],
    "blockedBy": {"nodes": found.get("blockedBy", [])},
    "comments": [{"body": b} for b in found.get("comments", [])],
    "title": found.get("title", "a ticket"),
    "createdAt": found.get("createdAt", "2026-08-30T00:00:00Z"),
    "closedAt": found.get("closedAt", ""),
}))
' ;;
  *"--json assignees"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t["number"] == want), {})
print(json.dumps({
    "assignees": [{"login": n} for n in found.get("assignees", [])],
}))
' ;;
  *"--json title"*)
    echo '{"title":"a ticket"}' ;;
  *) echo '{}' ;;
esac
FAKE

chmod +x "$TMP/bin/paseo" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_FAKE_PASEO_STATE="$TMP/paseo-state"

git init -q -b main "$TMP/repo"
git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture

# ------------------------------------------------------------------ log reading

reset_log() {
  : > "$MMW_TEST_LOG"
  mkdir -p "$MMW_FAKE_PASEO_STATE"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/workspaces.json"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
}
has() { grep -qF -- "$1" "$MMW_TEST_LOG" || fail "no call matching: $1"; }
hasnt() { grep -qF -- "$1" "$MMW_TEST_LOG" && fail "should not have called: $1"; return 0; }
count_of() { grep -cF -- "$1" "$MMW_TEST_LOG" | tr -d ' '; }
line_of() { grep -n -- "$1" "$MMW_TEST_LOG" | head -1 | cut -d: -f1 | grep . || echo 0; }

arg_after() {
  MMW_FLAG="$1" python3 -c '
import os

flag = os.environ["MMW_FLAG"]
for line in open(os.environ["MMW_TEST_LOG"], encoding="utf-8"):
    fields = line.rstrip("\n").split(" :: ")
    if flag in fields:
        index = fields.index(flag)
        if index + 1 < len(fields):
            print(fields[index + 1])
        break
'
}

run_dispatch() { (cd "$TMP/repo" && "$@") > "$TMP/out" 2> "$TMP/err"; echo "$?"; }

row_host() { awk -F'|' -v want="$1" 'function t(s){gsub(/^[ \t`]+|[ \t`]+$/,"",s);return s} /^[ \t]*\|/ && NF==7 && t($2)==want {print t($3); exit}' "$SKILL/models.md"; }
row_model() { awk -F'|' -v want="$1" 'function t(s){gsub(/^[ \t`]+|[ \t`]+$/,"",s);return s} /^[ \t]*\|/ && NF==7 && t($2)==want {print t($4); exit}' "$SKILL/models.md"; }
JUNIOR_HOST="$(row_host junior-worker)"; JUNIOR_MODEL="$(row_model junior-worker)"
SENIOR_MODEL="$(row_model senior-worker)"
one_line_reason() {
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "the reason should be one line: $(cat "$TMP/err")"
}

fresh_repo() {
  rm -rf "$TMP/repo"
  git init -q -b main "$TMP/repo"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture
}

make_branch() {
  local name="$1" file="$2" text="$3"
  git -C "$TMP/repo" checkout -q -b "$name" main
  printf '%s\n' "$text" > "$TMP/repo/$file"
  git -C "$TMP/repo" add "$file"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "$name"
  git -C "$TMP/repo" checkout -q main
}

write_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z",
   "comments": ["self-run\\n3 met", "ALL MET\\nBranch: issue-61"]},
  {"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T02:00:00Z",
   "assignees": ["alice"],
   "comments": ["ALL MET\\nBranch: issue-62"]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n", "title": "frontier ticket"}
]
JSON
}

seed_agent() {
  local n="$1" kind="${2:-worker}"
  MMW_N="$n" MMW_KIND="$kind" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
n = os.environ["MMW_N"]
kind = os.environ["MMW_KIND"]
path = state / "agents.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({
    "id": "agt_" + n + "_" + kind,
    "name": "#" + n + " " + kind,
    "status": "running",
    "cwd": str(state / ("issue-" + n)),
    "labels": {"mmw.ticket": n, "mmw.kind": kind, "mmw.spec": "76"},
})
path.write_text(json.dumps(rows))
'
}

seed_workspace() {
  local n="$1"
  MMW_N="$n" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
n = os.environ["MMW_N"]
slug = "issue-" + n
cwd = str(state / slug)
Path(cwd).mkdir(parents=True, exist_ok=True)
path = state / "workspaces.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({
    "workspaceId": "wks_" + slug,
    "project": "repo",
    "name": "#" + n,
    "isolation": "worktree",
    "cwd": cwd,
})
path.write_text(json.dumps(rows))
'
}

skill_copy_for() {
  local copy="$TMP/fake/skills/$1"
  rm -rf "$TMP/fake"
  mkdir -p "$copy"
  cp -R "$SKILL/models.md" "$SKILL/scripts" "$SKILL/references" "$copy/"
  printf '#!/usr/bin/env bash\nexit %s\n' "${2:-0}" > "$TMP/fake/install.sh"
  chmod +x "$TMP/fake/install.sh"
  printf '%s\n' "$copy"
}

# ------------------------------------------------------------------ scenarios

scenario_check() {
  local copy code
  copy="$(skill_copy_for check)"
  fresh_repo

  echo "--- a complete machine, one grade per queued ticket, exits 0"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker"]},
  {"number": 62, "state": "OPEN", "labels": ["ready-for-agent", "senior-worker"],
   "blockedBy": [{"number": 61, "state": "OPEN"}]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" check 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: provider :: ls :: --json"

  echo "--- a provider that is not available, and a ticket with two grades, each printed"
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker", "senior-worker"]}
]
JSON
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_PASEO_SCENARIO=provider-down \
          bash "$copy/scripts/dispatch.sh" check 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q 'grok' "$TMP/err" || fail "the reason does not name the provider: $(cat "$TMP/err")"
  grep -q '#61' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" -ge 2 ] \
    || fail "expected one line per failing check: $(cat "$TMP/err")"
}

scenario_advance() {
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  seed_workspace 61
  seed_workspace 62
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76 --run)"

  echo "--- both finished branches land on the main branch"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  [ -f "$TMP/repo/one.txt" ] || fail "issue-61 was not merged"
  [ -f "$TMP/repo/two.txt" ] || fail "issue-62 was not merged"

  echo "--- in the order the tickets closed, each keeping a merge commit of its own"
  [ "$(git -C "$TMP/repo" log --merges --first-parent --format='%s')" = "Merge branch 'issue-62'
Merge branch 'issue-61'" ] || fail "merge order is wrong"

  echo "--- a workspace is archived only after its branch is merged, then the frontier is created"
  has "paseo :: workspace :: archive :: wks_issue-61"
  has "paseo :: workspace :: archive :: wks_issue-62"
  has "paseo :: workspace :: create"
  has ":: --mode :: branch-off"
  has ":: --new-branch :: issue-63"
  has ":: --base :: main"
  has ":: --worktree-slug :: issue-63"
  local archived created started
  archived="$(line_of 'workspace :: archive :: wks_issue-62')"
  created="$(line_of 'workspace :: create')"
  started="$(line_of 'paseo :: run')"
  [ "$archived" -gt 0 ] && [ "$created" -gt 0 ] && [ "$archived" -lt "$created" ] \
    || fail "archive should precede workspace create"
  [ "$started" -gt "$created" ] || fail "the frontier should be started after its workspace exists"
  has "paseo :: run"
  has ":: --title :: #63 worker"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base)" = "$(git -C "$TMP/repo" rev-parse HEAD)" ] \
    || fail "mmw-base should be HEAD for a branch-off"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base-branch)" = main ] \
    || fail "mmw-base-branch should be main"

  echo "--- a second run has nothing left to merge and starts nothing new"
  reset_log
  seed_workspace 63
  seed_agent 63 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76 --run)"
  [ "$code" = 0 ] || fail "exit $code on the second run: $(cat "$TMP/err")"
  grep -q "merged 0" "$TMP/out" || fail "the second run should report nothing merged: $(cat "$TMP/out")"
  hasnt "paseo :: run"
}

scenario_advanceconflict() {
  reset_log
  fresh_repo
  write_batch
  printf 'base\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared
  make_branch issue-61 shared.txt "from 61"
  make_branch issue-62 shared.txt "from 62"
  seed_workspace 61
  seed_workspace 62

  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76 --run)"

  echo "--- a conflict stops the run with its own exit code"
  [ "$code" = 3 ] || fail "exit $code, not 3: $(cat "$TMP/err")"

  echo "--- the merge is left in the tree, never aborted"
  git -C "$TMP/repo" rev-parse -q --verify MERGE_HEAD >/dev/null \
    || fail "MERGE_HEAD is gone, so the merge was aborted"

  echo "--- and the report names both sides and the files"
  grep -q "CONFLICT merging issue-62" "$TMP/out" || fail "no CONFLICT line: $(cat "$TMP/out")"
  grep -q "MERGE_HEAD  issue-62" "$TMP/out" || fail "the incoming side is not named"
  grep -q "issue-61" "$TMP/out" || fail "the side already merged is not named"
  grep -q "shared.txt" "$TMP/out" || fail "the conflicted file is not named"

  echo "--- nothing is archived, created or started while the tree is half-merged"
  hasnt "workspace :: archive"
  hasnt "workspace :: create"
  hasnt "paseo :: run"
}

scenario_advancedirty() {
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  printf 'unfinished\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared
  printf 'edited\n' > "$TMP/repo/shared.txt"

  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" advance 76 --run)"

  echo "--- a tree with uncommitted work is refused before anything is merged"
  [ "$code" = 2 ] || fail "exit $code, not 2: $(cat "$TMP/err")"
  one_line_reason
  grep -q "uncommitted changes" "$TMP/err" || fail "the reason does not say why: $(cat "$TMP/err")"
  [ ! -f "$TMP/repo/one.txt" ] || fail "it merged despite the dirty tree"
  hasnt "workspace :: archive"
  hasnt "workspace :: create"
  hasnt "paseo :: run"
}

scenario_start_worker() {
  local code
  echo "--- a ticket with no worker label starts on the default row"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" start 61 worker --run)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: run"
  has ":: --provider :: $JUNIOR_HOST/$JUNIOR_MODEL"
  has ":: --title :: #61 worker"
  has ":: --label :: mmw.ticket=61"
  has ":: --label :: mmw.kind=worker"
  has ":: --label :: mmw.spec=76"
  has ":: --label :: mmw.profile=junior-worker"
  has ":: --label :: mmw.autonomous=1"
  grep -q "Use the implement skill to work ticket #61." "$MMW_TEST_LOG" \
    || fail "the worker dispatch line is missing"
  grep -q "You are operating autonomously" "$MMW_TEST_LOG" \
    || fail "the autonomous sentence is missing from the worker prompt"
  has ":: --mode :: branch-off"
  has ":: --new-branch :: issue-61"

  echo "--- an existing ticket branch is checked out, not cut again"
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "already there"
  code="$(run_dispatch bash "$DISPATCH" start 61 worker --run)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: --mode :: checkout-branch"
  has ":: --branch :: issue-61"
  hasnt ":: --mode :: branch-off"

  echo "--- a senior-worker label starts that row instead"
  reset_log
  fresh_repo
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,senior-worker" \
          bash "$DISPATCH" start 61 worker --run)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: --provider :: grok/$SENIOR_MODEL"
  has ":: --thinking :: xhigh"
  has ":: --label :: mmw.profile=senior-worker"

  echo "--- two worker labels are refused, and nothing is started"
  reset_log
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,junior-worker,senior-worker" \
          bash "$DISPATCH" start 61 worker --run)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  grep -q '2 worker labels' "$TMP/err" || fail "the reason does not name the labels: $(cat "$TMP/err")"
  hasnt "paseo :: run"
  hasnt "workspace :: create"
}

scenario_start_reviewer() {
  local code
  reset_log
  fresh_repo
  git -C "$TMP/repo" config branch.issue-61.mmw-base abcdef0123456789abcdef0123456789abcdef01
  seed_workspace 61
  code="$(run_dispatch bash "$DISPATCH" start 61 reviewer --run)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: run"
  has ":: --title :: #61 reviewer"
  has ":: --label :: mmw.kind=reviewer"
  has ":: --label :: mmw.profile=reviewer"
  grep -q "Use the code-review skill to review ticket #61 from base commit abcdef0123456789abcdef0123456789abcdef01." "$MMW_TEST_LOG" \
    || fail "the reviewer dispatch line did not carry the recorded base commit: $(cat "$MMW_TEST_LOG")"
  grep -q "You are operating autonomously" "$MMW_TEST_LOG" \
    || fail "the autonomous sentence is missing from the reviewer prompt"
}

scenario_start_verifier() {
  local code path
  path="$(realpath "$SKILL/references/verifier.md")"
  reset_log
  fresh_repo
  seed_workspace 61
  code="$(run_dispatch bash "$DISPATCH" start 61 verifier --run)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has ":: --title :: #61 verifier"
  has ":: --label :: mmw.kind=verifier"
  has ":: --label :: mmw.profile=verifier"
  grep -q "verify #61 按 $path 行事" "$MMW_TEST_LOG" \
    || fail "the verifier prompt is missing the path: $(cat "$MMW_TEST_LOG")"
  grep -q "You are operating autonomously" "$MMW_TEST_LOG" \
    && fail "the verifier prompt should not carry the autonomous sentence"
}

scenario_resume() {
  local code
  echo "--- a live worker is found by ticket and kind labels and sent the text"
  reset_log
  python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
path.write_text(json.dumps([{
    "id": "agt_w61",
    "name": "#61 worker",
    "status": "idle",
    "cwd": "/tmp/issue-61",
    "labels": {"mmw.ticket": "61", "mmw.kind": "worker", "mmw.spec": "76"},
}]))
'
  code="$(run_dispatch bash "$DISPATCH" resume 61 continue)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: ls :: -g :: --json :: --label :: mmw.ticket=61 :: --label :: mmw.kind=worker"
  has "paseo :: send :: --no-wait :: agt_w61 :: continue"

  echo "--- no matching worker is a refusal, and nothing is sent"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" resume 61 continue)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"
}

scenario_reverify() {
  local copy code
  copy="$(skill_copy_for reverify)"
  mkdir -p "$TMP/fake/skills/verify-ticket/scripts"
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import os, sys
log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("verify-ticket" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
number = sys.argv[1]
failing = {n for n in os.environ.get("FAKE_VERIFY_FAIL", "").split(",") if n}
if number in failing:
    print("UNMET: 1 (met: 4)")
    print("- [x] AC1: one")
    print("- [ ] AC3: three")
    sys.exit(1)
print("ALL MET (5 met)")
sys.exit(0)
PY
  chmod +x "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"

  fresh_repo
  write_batch
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL=62 \
          bash "$copy/scripts/dispatch.sh" reverify 76)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  has "verify-ticket :: 61 :: --reverify"
  has "verify-ticket :: 62 :: --reverify"
  has "gh :: issue :: reopen :: 62"
  has "gh :: issue :: edit :: 62 :: --add-label :: needs-triage :: --remove-assignee :: alice"
  grep -q "AC3" "$MMW_TEST_LOG" || fail "the failing criterion was not commented: $(cat "$MMW_TEST_LOG")"
  grep -q "reverify #76: 1 green, 1 red" "$TMP/out" \
    || fail "the summary line is missing: $(cat "$TMP/out")"

  echo "--- all green exits 0"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: reopen"
}

scenario_summary() {
  local when code
  when="$(python3 -c 'from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc)-timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "$when",
   "createdAt": "2026-08-29T00:00:00Z",
   "comments": ["ALL MET\\nBranch: issue-61"]}
]
JSON
  reset_log
  fresh_repo
  echo "--- without a reverify this session, the four lines are posted as NIGHT SUMMARY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "^NIGHT SUMMARY " "$TMP/out" || fail "stdout should open NIGHT SUMMARY: $(cat "$TMP/out")"
  grep -q "Reverify:" "$TMP/out" && fail "Reverify should be absent unless reverify ran"
  has "gh :: issue :: comment :: 76 :: --body"

  echo "--- after reverify, one extra Reverify line is posted"
  printf '2 1\n' > "$TMP/repo/.git/mmw-reverify-76"
  reset_log
  echo '[]' > "$MMW_FAKE_PASEO_STATE/workspaces.json"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "Reverify: 2/1" "$TMP/out" || fail "missing Reverify line: $(cat "$TMP/out")"
}

scenario_start_json() {
  local code
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" start 61 worker --json)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: run"
  python3 -c '
import json, sys
from pathlib import Path
raw = Path(sys.argv[1]).read_text()
lines = [l for l in raw.splitlines() if l.strip()]
assert len(lines) == 1, raw
obj = json.loads(lines[0])
for key in ("workspaceId", "title", "provider", "settings", "labels", "initialPrompt"):
    assert key in obj, key
assert obj["title"] == "#61 worker"
assert "grok" in obj["provider"]
assert obj["labels"]["mmw.ticket"] == "61"
assert obj["labels"]["mmw.kind"] == "worker"
assert obj["labels"]["mmw.spec"] == "76"
assert obj["labels"]["mmw.profile"] == "junior-worker"
assert obj["labels"]["mmw.autonomous"] == "1"
assert obj["initialPrompt"].startswith("Use the implement skill to work ticket #61.")
assert "notifyOnFinish" not in obj
' "$TMP/out" || fail "the JSON line is wrong: $(cat "$TMP/out")"
}

scenario_start_norun() {
  local code
  echo "--- start without a path flag exits 2 and calls nothing"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q -- '--json' "$TMP/err" || fail "the reason should name --json: $(cat "$TMP/err")"
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called with no path flag"
  [ "$(count_of 'gh ::')" = 0 ] || fail "gh was called with no path flag"

  echo "--- advance without a path flag exits 2 and calls nothing"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" advance 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called for advance with no path flag"
  [ "$(count_of 'gh ::')" = 0 ] || fail "gh was called for advance with no path flag"
}

# ------------------------------------------------------------------ entry

ALL="check advance advanceconflict advancedirty start-worker start-reviewer start-verifier resume reverify summary start-json start-norun"

case "${1:-}" in
  check|advance|advanceconflict|advancedirty|start-worker|start-reviewer|start-verifier|resume|reverify|summary|start-json|start-norun)
    wanted="$1" ;;
  all)
    wanted="$ALL" ;;
  *)
    echo "usage: test_dispatch.sh $(echo "$ALL" | tr ' ' '|')|all" >&2
    exit 2 ;;
esac

banner_for() {
  case "$1" in
    check) echo DISPATCH-CHECK-OK ;;
    advance) echo DISPATCH-ADVANCE-OK ;;
    advanceconflict) echo DISPATCH-ADVANCE-CONFLICT-OK ;;
    advancedirty) echo DISPATCH-ADVANCE-DIRTY-OK ;;
    start-worker) echo DISPATCH-START-WORKER-OK ;;
    start-reviewer) echo DISPATCH-START-REVIEWER-OK ;;
    start-verifier) echo DISPATCH-START-VERIFIER-OK ;;
    resume) echo DISPATCH-RESUME-OK ;;
    reverify) echo DISPATCH-REVERIFY-OK ;;
    summary) echo DISPATCH-SUMMARY-OK ;;
    start-json) echo DISPATCH-START-JSON-OK ;;
    start-norun) echo DISPATCH-START-NORUN-OK ;;
  esac
}

fn_for() {
  case "$1" in
    start-worker) echo scenario_start_worker ;;
    start-reviewer) echo scenario_start_reviewer ;;
    start-verifier) echo scenario_start_verifier ;;
    start-json) echo scenario_start_json ;;
    start-norun) echo scenario_start_norun ;;
    *) echo "scenario_$1" ;;
  esac
}

for name in $wanted; do
  echo "=== $name"
  "$(fn_for "$name")"
  if [ "$rc" -eq 0 ]; then
    banner_for "$name"
  else
    echo "$name failed" >&2
    exit 1
  fi
done
