#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh check|advance|advanceconflict|advancedirty
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh start-worker|start-reviewer|start-verifier
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh resume|reverify|summary
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh release|releaseother|releaselive|frontierwhy
#   bash mmw-v2/skills/dispatch/tests/test_dispatch.sh instancegate|suspend|suspendbusy|suspendnohb|status
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

if args[:1] == ["ls"]:
    if scenario == "ls-fail":
        sys.exit(1)
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

if args[:1] == ["stop"]:
    ident = args[1] if len(args) > 1 else ""
    rows = load("agents.json")
    for row in rows:
        if row.get("id") == ident:
            row["status"] = "idle"
    save("agents.json", rows)
    print(json.dumps({"id": ident, "status": "idle"}))
    sys.exit(0)

if args[:1] == ["archive"]:
    ident = args[1] if len(args) > 1 else ""
    rows = [a for a in load("agents.json") if a.get("id") != ident]
    save("agents.json", rows)
    print(json.dumps({"id": ident, "archived": True}))
    sys.exit(0)

if args[:2] == ["heartbeat", "delete"]:
    print(json.dumps({"ok": True}))
    sys.exit(0)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

cat > "$TMP/bin/gh" <<'FAKE'
#!/usr/bin/env bash
line=gh
for a in "$@"; do line="$line :: $a"; done
echo "$line" >> "$MMW_TEST_LOG"
body_next=0
for a in "$@"; do
  if [ "$body_next" = 1 ]; then
    printf '%s\n' "$a" > "$MMW_GH_LAST_BODY"
    break
  fi
  [ "$a" = "--body" ] && body_next=1
done
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
    MMW_SUB_ISSUES_URL="$*" python3 -c '
import json, os, re
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
url = os.environ.get("MMW_SUB_ISSUES_URL") or ""
found = re.search(r"/issues/(\d+)/sub_issues", url)
want = int(found.group(1)) if found else None
owned = {t["number"] for t in rows if "number" in t}
if want is None or want in owned:
    print("[]")
else:
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
  *"api user"*)
    printf '%s\n' "${FAKE_GH_LOGIN:-mmw-bot}" ;;
  *"issue edit"*)
    number="$3"
    remove=""
    skip=0
    for a in "$@"; do
      if [ "$skip" = 1 ]; then remove="$a"; skip=0; continue; fi
      [ "$a" = "--remove-assignee" ] && skip=1
    done
    if [ -n "$remove" ] && [ -n "${FAKE_GH_TICKETS_FILE:-}" ] && [ -f "$FAKE_GH_TICKETS_FILE" ]; then
      MMW_EDIT_N="$number" MMW_REMOVE="$remove" python3 -c '
import json, os
path = os.environ["FAKE_GH_TICKETS_FILE"]
n = int(os.environ["MMW_EDIT_N"])
who = os.environ["MMW_REMOVE"]
login = os.environ.get("FAKE_GH_LOGIN", "mmw-bot")
if who in ("@me", login):
    who = login
rows = json.load(open(path))
for t in rows:
    if t.get("number") == n:
        t["assignees"] = [a for a in t.get("assignees") or [] if a != who]
        break
json.dump(rows, open(path, "w"))
'
    fi
    echo '{}' ;;
  *) echo '{}' ;;
esac
FAKE

REAL_PYTHON="$(command -v python3)"
cat > "$TMP/bin/python3" <<WRAPPER
#!/bin/bash
for a in "\$@"; do
  case "\$a" in
    *status.py)
      flags=""
      for b in "\$@"; do
        case "\$b" in --*) flags="\$flags \$b" ;; esac
      done
      echo "status.py\$flags" >> "\${MMW_TEST_LOG}"
      break
      ;;
  esac
done
exec "$REAL_PYTHON" "\$@"
WRAPPER
chmod +x "$TMP/bin/python3" "$TMP/bin/paseo" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_FAKE_PASEO_STATE="$TMP/paseo-state"
export MMW_GH_LAST_BODY="$TMP/gh-last-body"
export MMW_HOME="$TMP/mmw-home"
export MMW_LEASE_PORT_STRIDE=20
export MMW_LEASE_PORT_BASE="$(python3 -c '
import os, socket
stride = int(os.environ.get("MMW_LEASE_PORT_STRIDE", "20"))
slots = int(os.environ.get("MMW_LEASE_SLOTS", "8"))
need = stride * slots
for base in range(22000, 60000 - need):
    held = []
    try:
        for port in range(base, base + need):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            held.append(sock)
        print(base)
        break
    except OSError:
        continue
    finally:
        for sock in held:
            sock.close()
else:
    raise SystemExit("no free port block of %s" % need)
')"
mkdir -p "$MMW_HOME"
: > "$MMW_GH_LAST_BODY"

git init -q -b main "$TMP/repo"
git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture

# ------------------------------------------------------------------ log reading

reset_log() {
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  mkdir -p "$MMW_FAKE_PASEO_STATE"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/workspaces.json"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
  rm -rf "$MMW_HOME/leases"
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

never_ran() { hasnt "paseo :: run"; }
nothing_printed() { [ ! -s "$TMP/out" ] || fail "stdout should be empty: $(cat "$TMP/out")"; }

# One field of the single JSON line dispatch printed. Nested keys use one
# dot: `labels.mmw.ticket` is labels["mmw.ticket"], not three hops.
out_json() {
  MMW_JSON_PATH="$1" python3 -c '
import json, os, sys
from pathlib import Path
lines = [l for l in Path(sys.argv[1]).read_text().splitlines() if l.strip()]
assert len(lines) == 1, lines
node = json.loads(lines[0])
path = os.environ["MMW_JSON_PATH"]
if "." in path:
    top, rest = path.split(".", 1)
    node = node[top][rest]
else:
    node = node[path]
print(node)
' "$TMP/out"
}

assert_create_shape() {
  python3 -c '
import json, sys
from pathlib import Path
raw = Path(sys.argv[1]).read_text()
lines = [l for l in raw.splitlines() if l.strip()]
assert len(lines) == 1, raw
obj = json.loads(lines[0])
for key in ("workspaceId", "title", "provider", "settings", "labels", "initialPrompt"):
    assert key in obj, key
assert "notifyOnFinish" not in obj
' "$TMP/out"
}

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
  local n="$1" kind="${2:-worker}" spec="${3:-76}"
  MMW_N="$n" MMW_KIND="$kind" MMW_SPEC_N="$spec" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
n = os.environ["MMW_N"]
kind = os.environ["MMW_KIND"]
spec = os.environ["MMW_SPEC_N"]
path = state / "agents.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({
    "id": "agt_" + n + "_" + kind,
    "name": "#" + n + " " + kind,
    "status": "running",
    "cwd": str(state / ("issue-" + n)),
    "labels": {"mmw.ticket": n, "mmw.kind": kind, "mmw.spec": spec},
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

# Prepend a workspace that matches the slug of ticket 61 but belongs to another
# project, so a filter that fails open would pick it first.
seed_foreign_workspace() {
  python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_PASEO_STATE"])
foreign = state / "other" / "issue-61"
foreign.mkdir(parents=True, exist_ok=True)
path = state / "workspaces.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.insert(0, {
    "workspaceId": "wks_foreign_61",
    "project": "other",
    "name": "#61 other",
    "isolation": "worktree",
    "cwd": str(foreign),
})
path.write_text(json.dumps(rows))
'
}

# The scripts of the two other skills dispatch.sh runs are handed to it with --tools,
# the way the agent does; TOOLS holds those arguments for every call below.
TOOLS=(--tools "$TMP/fake/skills/drive-target/scripts" --tools "$TMP/fake/skills/verify-ticket/scripts"
       --tools "$(dirname "$SKILL")/drive-target/scripts" --tools "$(dirname "$SKILL")/verify-ticket/scripts")

skill_copy_for() {
  local copy="$TMP/fake/skills/$1"
  rm -rf "$TMP/fake"
  mkdir -p "$copy" "$TMP/fake/skills/verify-ticket/scripts" "$TMP/fake/skills/drive-target/scripts"
  cp -R "$SKILL/models.md" "$SKILL/scripts" "$SKILL/references" "$copy/"
  cp "$(dirname "$SKILL")/drive-target/scripts/lease.py" \
     "$(dirname "$SKILL")/drive-target/scripts/refusal.py" \
     "$TMP/fake/skills/drive-target/scripts/"
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
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
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
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q 'grok' "$TMP/err" || fail "the reason does not name the provider: $(cat "$TMP/err")"
  grep -q '#61' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" -ge 2 ] \
    || fail "expected one line per failing check: $(cat "$TMP/err")"

  echo "--- install.sh --check failing is a refusal, exit 2"
  copy="$(skill_copy_for check 1)"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker"]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "expected exit 2 when install.sh --check fails, got $code: $(cat "$TMP/err")"
  grep -q 'install.sh --check' "$TMP/err" \
    || fail "the reason should name install.sh --check: $(cat "$TMP/err")"
}

scenario_advance() {
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  seed_workspace 61
  seed_workspace 62
  seed_foreign_workspace
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

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
  hasnt "wks_foreign_61"
  [ "$(count_of "paseo :: workspace :: ls")" = 4 ] \
    || fail "expected one list read for the advance plan, one per archive, and one for the frontier create, got $(count_of "paseo :: workspace :: ls")"
  has "paseo :: workspace :: create"
  has ":: --mode :: branch-off"
  has ":: --new-branch :: issue-63"
  has ":: --base :: main"
  has ":: --worktree-slug :: issue-63"
  local archived created
  archived="$(line_of 'workspace :: archive :: wks_issue-62')"
  created="$(line_of 'workspace :: create')"
  [ "$archived" -gt 0 ] && [ "$created" -gt 0 ] && [ "$archived" -lt "$created" ] \
    || fail "archive should precede workspace create"
  never_ran
  assert_create_shape || fail "the dispatched JSON is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#63 worker" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.ticket)" = 63 ] || fail "ticket: $(out_json labels.mmw.ticket)"
  [ "$(out_json labels.mmw.kind)" = worker ] || fail "kind: $(out_json labels.mmw.kind)"
  [ -n "$(out_json workspaceId)" ] || fail "workspaceId missing"
  grep -q "advance #76:" "$TMP/err" || fail "the summary line should be on stderr: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base)" = "$(git -C "$TMP/repo" rev-parse HEAD)" ] \
    || fail "mmw-base should be HEAD for a branch-off"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base-branch)" = main ] \
    || fail "mmw-base-branch should be main"

  echo "--- a second run has nothing left to merge and starts nothing new"
  reset_log
  seed_workspace 63
  seed_agent 63 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code on the second run: $(cat "$TMP/err")"
  grep -q "merged 0" "$TMP/err" || fail "the second run should report nothing merged: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "the second run should start nothing: $(cat "$TMP/err")"
  nothing_printed
  never_ran

  echo "--- a retired flag on advance exits 2 and calls nothing"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" advance 76 --json)"
  [ "$code" = 2 ] || fail "expected exit 2 for --json, got $code: $(cat "$TMP/err")"
  grep -q "no longer a flag" "$TMP/err" || fail "the reason should say no longer a flag: $(cat "$TMP/err")"
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called for advance --json"
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
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- a conflict stops the run with its own exit code"
  [ "$code" = 3 ] || fail "exit $code, not 3: $(cat "$TMP/err")"

  echo "--- the merge is left in the tree, never aborted"
  git -C "$TMP/repo" rev-parse -q --verify MERGE_HEAD >/dev/null \
    || fail "MERGE_HEAD is gone, so the merge was aborted"

  echo "--- and the report names both sides and the files"
  grep -q "CONFLICT merging issue-62" "$TMP/err" || fail "no CONFLICT line: $(cat "$TMP/err")"
  grep -q "MERGE_HEAD  issue-62" "$TMP/err" || fail "the incoming side is not named"
  grep -q "issue-61" "$TMP/err" || fail "the side already merged is not named"
  grep -q "shared.txt" "$TMP/err" || fail "the conflicted file is not named"

  echo "--- nothing is archived, created or started while the tree is half-merged"
  hasnt "workspace :: archive"
  hasnt "workspace :: create"
  nothing_printed
  never_ran
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
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- a tree with uncommitted work is refused before anything is merged"
  [ "$code" = 2 ] || fail "exit $code, not 2: $(cat "$TMP/err")"
  one_line_reason
  grep -q "uncommitted changes" "$TMP/err" || fail "the reason does not say why: $(cat "$TMP/err")"
  [ ! -f "$TMP/repo/one.txt" ] || fail "it merged despite the dirty tree"
  hasnt "workspace :: archive"
  hasnt "workspace :: create"
  nothing_printed
  never_ran
}

scenario_start_worker() {
  local code
  echo "--- a ticket with no worker label prints one create_agent object on the default row"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  never_ran
  assert_create_shape || fail "the JSON line is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#61 worker" ] || fail "title: $(out_json title)"
  [ "$(out_json provider)" = "$JUNIOR_HOST/$JUNIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(out_json labels.mmw.ticket)" = 61 ] || fail "ticket label"
  [ "$(out_json labels.mmw.kind)" = worker ] || fail "kind label"
  [ "$(out_json labels.mmw.spec)" = 76 ] || fail "spec label"
  [ "$(out_json labels.mmw.profile)" = junior-worker ] || fail "profile label"
  [ "$(out_json labels.mmw.autonomous)" = 1 ] || fail "autonomous label"
  [ "$(out_json settings.thinkingOptionId)" = high ] || fail "effort: $(out_json settings.thinkingOptionId)"
  case "$(out_json initialPrompt)" in
    "Use the implement skill to work ticket #61."*) ;;
    *) fail "the worker dispatch line is missing: $(out_json initialPrompt)" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"You are operating autonomously"*) ;;
    *) fail "the autonomous sentence is missing from the worker prompt" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"--sub-issue pipeline"*) ;;
    *) fail "the pipeline-fault sentence is missing from the worker prompt" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"A fault in the pipeline itself is reported, not worked around: verify-ticket.py <n> --sub-issue pipeline <file>, then stop (rule 5 of that section)."*) ;;
    *) fail "the shortened pipeline-fault sentence is missing: $(out_json initialPrompt)" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"Several tickets run on this machine at once. Before you start, reach or stop the product, read 'Five rules while the product is running' in the drive-target skill."*) ;;
    *) fail "the product-rules sentence is missing: $(out_json initialPrompt)" ;;
  esac
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads([l for l in Path(sys.argv[1]).read_text().splitlines() if l.strip()][0])
assert obj["settings"].get("thinkingOptionId") == "high"
assert obj["settings"].get("features") == {"auto_accept": True}, obj["settings"]
' "$TMP/out" || fail "create_agent settings changed: $(cat "$TMP/out")"
  has ":: --mode :: branch-off"
  has ":: --new-branch :: issue-61"
  has ":: --isolation :: worktree"
  has ":: --project :: prj_test"

  echo "--- workspace title is the ticket title cut to 20 characters, not bytes"
  reset_log
  fresh_repo
  code="$(run_dispatch env FAKE_GH_TITLE="一二三四五六七八九十一二三四五六七八九十再五字" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(arg_after --title)" = "#61 一二三四五六七八九十一二三四五六七八九十" ] \
    || fail "title should be cut to 20 characters: $(arg_after --title)"
  has ":: --isolation :: worktree"
  has ":: --project :: prj_test"

  echo "--- an existing ticket branch is checked out, not cut again"
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "already there"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  never_ran
  has ":: --mode :: checkout-branch"
  has ":: --branch :: issue-61"
  hasnt ":: --mode :: branch-off"

  echo "--- a senior-worker label starts that row instead"
  reset_log
  fresh_repo
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,senior-worker" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  never_ran
  [ "$(out_json provider)" = "grok/$SENIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(out_json settings.thinkingOptionId)" = xhigh ] || fail "effort: $(out_json settings.thinkingOptionId)"
  [ "$(out_json labels.mmw.profile)" = senior-worker ] || fail "profile: $(out_json labels.mmw.profile)"

  echo "--- two worker labels are refused, and nothing is started"
  reset_log
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,junior-worker,senior-worker" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  grep -q '2 worker labels' "$TMP/err" || fail "the reason does not name the labels: $(cat "$TMP/err")"
  nothing_printed
  never_ran
  hasnt "workspace :: create"

  echo "--- a retired flag on start exits 2 and calls nothing"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker --json)"
  [ "$code" = 2 ] || fail "expected exit 2 for --json, got $code: $(cat "$TMP/err")"
  grep -q "no longer a flag" "$TMP/err" || fail "the reason should say no longer a flag: $(cat "$TMP/err")"
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called for start --json"
  [ "$(count_of 'gh ::')" = 0 ] || fail "gh was called for start --json"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker --run)"
  [ "$code" = 2 ] || fail "expected exit 2 for the retired flag, got $code: $(cat "$TMP/err")"
  grep -q "no longer a flag" "$TMP/err" || fail "the reason should say no longer a flag: $(cat "$TMP/err")"

  echo "--- a refused lease archives a workspace this start created, and keeps one that already stood"
  reset_log
  fresh_repo
  seed_workspace 99
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-99" >/dev/null
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 when the lease is refused, got $code: $(cat "$TMP/err")"
  has "workspace :: create"
  has "workspace :: archive"
  grep -q 'issue-61:' "$TMP/err" || fail "the refusal should name the ticket: $(cat "$TMP/err")"
  grep -q 'instance slots' "$TMP/err" || fail "the refusal should carry lease.py's slot fact: $(cat "$TMP/err")"
  grep -q 'Report the ticket blocked and stop' "$TMP/err" \
    || fail "the refusal should carry lease.py's next step: $(cat "$TMP/err")"
  reset_log
  fresh_repo
  seed_workspace 61
  seed_workspace 99
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-99" >/dev/null
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 on a standing workspace, got $code: $(cat "$TMP/err")"
  hasnt "workspace :: create"
  hasnt "workspace :: archive"
  grep -q 'issue-61:' "$TMP/err" || fail "the refusal should name the ticket: $(cat "$TMP/err")"
}

scenario_start_reviewer() {
  local code
  echo "--- a reviewer with no mmw-base is refused and nothing is started"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 2 ] || fail "expected exit 2 without mmw-base, got $code: $(cat "$TMP/err")"
  grep -q 'mmw-base' "$TMP/err" || fail "the reason should name mmw-base: $(cat "$TMP/err")"
  nothing_printed
  never_ran
  hasnt "workspace :: create"

  reset_log
  fresh_repo
  git -C "$TMP/repo" config branch.issue-61.mmw-base abcdef0123456789abcdef0123456789abcdef01
  seed_workspace 61
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  never_ran
  [ "$(out_json title)" = "#61 reviewer" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.kind)" = reviewer ] || fail "kind label"
  [ "$(out_json labels.mmw.profile)" = reviewer ] || fail "profile label"
  case "$(out_json initialPrompt)" in
    "Use the code-review skill to review ticket #61 from base commit abcdef0123456789abcdef0123456789abcdef01."*) ;;
    *) fail "the reviewer dispatch line did not carry the recorded base commit: $(out_json initialPrompt)" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"You are operating autonomously"*) ;;
    *) fail "the autonomous sentence is missing from the reviewer prompt" ;;
  esac
}

scenario_start_verifier() {
  local code path
  path="$(realpath "$SKILL/references/verifier.md")"
  reset_log
  fresh_repo
  seed_workspace 61
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 verifier)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  never_ran
  [ "$(out_json title)" = "#61 verifier" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.kind)" = verifier ] || fail "kind label"
  [ "$(out_json labels.mmw.profile)" = verifier ] || fail "profile label"
  [ "$(out_json initialPrompt)" = "verify #61 按 $path 行事" ] \
    || fail "the verifier prompt is missing the path: $(out_json initialPrompt)"
  case "$(out_json initialPrompt)" in
    *"You are operating autonomously"*) fail "the verifier prompt should not carry the autonomous sentence" ;;
  esac
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
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: ls :: -g :: --json :: --label :: mmw.ticket=61 :: --label :: mmw.kind=worker"
  has "paseo :: send :: --no-wait :: agt_w61 :: continue"

  echo "--- no matching worker is a refusal, and nothing is sent"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
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
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
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
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: reopen"
}

scenario_summary() {
  local when code copy
  copy="$(skill_copy_for summary)"
  mkdir -p "$TMP/fake/skills/verify-ticket/scripts"
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import os, sys
log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("verify-ticket" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
print("ALL MET (5 met)")
sys.exit(0)
PY
  chmod +x "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"

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
  echo "--- without a reverify this session, the posted comment opens NIGHT SUMMARY and has no Reverify"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: comment :: 76 :: --body"
  grep -q "^NIGHT SUMMARY " "$MMW_GH_LAST_BODY" \
    || fail "the posted comment should open NIGHT SUMMARY: $(cat "$MMW_GH_LAST_BODY")"
  grep -q "Reverify:" "$MMW_GH_LAST_BODY" \
    && fail "Reverify should be absent unless reverify ran: $(cat "$MMW_GH_LAST_BODY")"

  echo "--- after reverify, the posted comment has a Reverify line matching that run"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "reverify expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "reverify #76: 1 green, 0 red" "$TMP/out" \
    || fail "reverify should report 1 green: $(cat "$TMP/out")"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "^NIGHT SUMMARY " "$MMW_GH_LAST_BODY" \
    || fail "the posted comment should open NIGHT SUMMARY: $(cat "$MMW_GH_LAST_BODY")"
  grep -q "Reverify: 1/0" "$MMW_GH_LAST_BODY" \
    || fail "missing Reverify line matching that reverify: $(cat "$MMW_GH_LAST_BODY")"
}

# ------------------------------------------------------------------ orphaned claims

write_claimed_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["$1"],
   "body": "## Parent\\n\\n#76\\n", "title": "claimed ticket"}
]
JSON
}

scenario_release() {
  reset_log
  fresh_repo
  write_claimed_batch mmw-bot
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- a claim with no worker and no workspace behind it is given back"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 63 :: --remove-assignee :: @me"
  grep -q "released 1" "$TMP/err" || fail "the summary does not count it: $(cat "$TMP/err")"

  echo "--- and never silently: the line names the ticket and says why"
  grep -q "released the claim on #63" "$TMP/err" \
    || fail "the release was silent: $(cat "$TMP/err")"
  grep -q "the worker that claimed it is gone" "$TMP/err" \
    || fail "the line does not say why: $(cat "$TMP/err")"

  echo "--- the ticket it frees is dispatched by the same advance, not the next one"
  has "paseo :: workspace :: create"
  grep -q "started 1" "$TMP/err" || fail "it was freed and then left: $(cat "$TMP/err")"

  echo "--- in that order: released first, started after"
  local rel disp
  rel="$(line_of 'issue :: edit :: 63 :: --remove-assignee')"
  disp="$(line_of 'workspace :: create')"
  [ "$rel" -gt 0 ] || fail "the claim was never released"
  [ "$disp" -gt "$rel" ] || fail "dispatch at line $disp came before the release at line $rel"

  echo "--- a standing workspace keeps the claim even with no live worker"
  reset_log
  write_claimed_batch mmw-bot
  seed_workspace 63
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit :: 63 :: --remove-assignee"
  grep -q "released 0" "$TMP/err" \
    || fail "the claim was given back over a standing workspace: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "a second worker was started: $(cat "$TMP/err")"
  grep -q "#63 keeps its claim" "$TMP/err" \
    || fail "nothing on stderr says the claim was kept: $(cat "$TMP/err")"
}

scenario_releaseother() {
  reset_log
  fresh_repo
  write_claimed_batch alice
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- a ticket somebody else took is left exactly as it is"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit :: 63 :: --remove-assignee"
  grep -q "released 0" "$TMP/err" || fail "somebody else's claim was taken: $(cat "$TMP/err")"

  echo "--- so it stays off the frontier, and is not started"
  hasnt "workspace :: create"
  grep -q "started 0" "$TMP/err" || fail "it was dispatched anyway: $(cat "$TMP/err")"

  echo "--- and stderr says which condition holds it there"
  grep -q "#63 claimed by alice" "$TMP/err" || fail "the reason is not on stderr: $(cat "$TMP/err")"
}

scenario_releaselive() {
  reset_log
  fresh_repo
  write_claimed_batch mmw-bot
  seed_agent 63 worker
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- a claim whose worker is still alive is the owner's, and is not touched"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit :: 63 :: --remove-assignee"
  grep -q "released 0" "$TMP/err" || fail "a live worker's claim was taken: $(cat "$TMP/err")"
  ! grep -q "released the claim on #63" "$TMP/err" \
    || fail "it printed a release line for a claim it did not release: $(cat "$TMP/err")"

  echo "--- and the ticket reads as held by that worker, not as an orphaned claim"
  grep -q "#63 claimed by mmw-bot; held by the live worker #63 worker" "$TMP/err" \
    || fail "stderr does not name the worker holding it: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "a second worker was started on it: $(cat "$TMP/err")"
}

write_stuck_batch() {
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["alice"]},
  {"number": 62, "state": "OPEN", "labels": ["ready-for-agent"],
   "blockedBy": [{"number": 61, "state": "OPEN"}]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]},
  {"number": 64, "state": "OPEN", "labels": ["needs-triage"]}
]
JSON
}

scenario_frontierwhy() {
  reset_log
  fresh_repo
  write_stuck_batch
  seed_agent 63 worker
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- an empty frontier is an explanation, not a failure"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "something started: $(cat "$TMP/err")"

  echo "--- every queued ticket names the condition holding it, and only queued ones do"
  grep -q "3 open ticket(s) are still in the agent queue" "$TMP/err" \
    || fail "the count is wrong or missing: $(cat "$TMP/err")"
  grep -q "#61 claimed by alice" "$TMP/err" || fail "#61: $(cat "$TMP/err")"
  grep -q "#62 blocked by #61" "$TMP/err" || fail "#62: $(cat "$TMP/err")"
  grep -q "#63 held by the live worker #63 worker" "$TMP/err" || fail "#63: $(cat "$TMP/err")"
  ! grep -q "#64" "$TMP/err" || fail "a ticket out of the agent queue was reported: $(cat "$TMP/err")"

  echo "--- and a batch with nothing left in the queue says nothing at all"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z"}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code on the finished batch: $(cat "$TMP/err")"
  grep -q "advance #76:" "$TMP/err" || fail "the summary line is missing: $(cat "$TMP/err")"
  ! grep -q "agent queue" "$TMP/err" \
    || fail "a finished batch should not explain the frontier: $(cat "$TMP/err")"
}

# ------------------------------------------------------------------ instance gate / suspend

LEASE_PY="$(dirname "$SKILL")/drive-target/scripts/lease.py"

scenario_instancegate() {
  echo "--- a product that declares it cannot be isolated is serialised, not piled onto"
  reset_log
  fresh_repo
  write_batch
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  mkdir -p "$TMP/repo/.mmw"
  printf '%s\n' '{"start":"true","discover":"true","reach":"true","instance":{"max":1,"why":"fixed host ports"}}' \
    > "$TMP/repo/.mmw/target.json"
  seed_workspace 61
  seed_workspace 62
  seed_workspace 99
  python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-99" >/dev/null
  python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-62" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 2 ] \
    || fail "setup should hold two slots, it holds $(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")"

  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"

  echo "--- the merges still happen: the gate is about starting, not about landing work"
  [ -f "$TMP/repo/one.txt" ] || fail "issue-61 was not merged"
  [ -f "$TMP/repo/two.txt" ] || fail "issue-62 was not merged"

  echo "--- a merged ticket's lease is released before its workspace is archived"
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 1 ] \
    || fail "issue-62's lease should be gone after archive, count is $(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")"
  has "paseo :: workspace :: archive :: wks_issue-62"

  echo "--- the frontier ticket is held back rather than sent onto a busy machine"
  grep -q "held 1" "$TMP/err" || fail "nothing was held back: $(cat "$TMP/err")"
  grep -q "held back" "$TMP/err" || fail "the reason was not reported: $(cat "$TMP/err")"
  hasnt "workspace :: create"

  echo "--- it kept its label, so the next advance starts it once a slot is free"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  python3 "$LEASE_PY" release "$MMW_FAKE_PASEO_STATE/issue-99" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 0 ] \
    || fail "issue-99 should be free before the second advance"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code on the second run: $(cat "$TMP/err")"
  has "paseo :: workspace :: create"
  has ":: --new-branch :: issue-63"

  rm -f "$TMP/repo/.mmw/target.json"
}

write_open_batch() {
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n"},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n"},
  {"number": 65, "state": "OPEN", "labels": ["needs-triage"],
   "comments": ["HANDOFF REQUIRED\\nAC2 needs a person"]}
]
JSON
}

claim_tickets() {
  MMW_TICKETS="$TMP/tickets.json" MMW_CLAIM="$*" python3 -c '
import json, os
path = os.environ["MMW_TICKETS"]
want = {int(n) for n in os.environ["MMW_CLAIM"].split()}
login = os.environ.get("FAKE_GH_LOGIN", "mmw-bot")
rows = json.load(open(path))
for t in rows:
    if t.get("number") in want:
        t["assignees"] = [login]
json.dump(rows, open(path, "w"))
'
}

open_a_night() {
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance exited $code: $(cat "$TMP/err")"
}

write_heartbeat() {
  printf 'hb_76\n' > "$(git -C "$TMP/repo" rev-parse --absolute-git-dir)/mmw-heartbeat-76"
}

scenario_suspend() {
  local code
  fresh_repo
  reset_log
  write_open_batch
  open_a_night

  [ -d "$MMW_FAKE_PASEO_STATE/issue-61" ] || fail "the night did not open a workspace for #61"
  [ -d "$MMW_FAKE_PASEO_STATE/issue-63" ] || fail "the night did not open a workspace for #63"
  seed_workspace 65
  python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-65" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 3 ] \
    || fail "the night should hold three slots, it holds $(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")"
  # The workspace is archived; the lease is not. suspend still has to give that slot back.
  (cd "$TMP/repo" && paseo workspace archive wks_issue-65 >/dev/null)

  seed_agent 61 worker
  seed_agent 99 worker 99
  seed_foreign_workspace
  write_heartbeat
  claim_tickets 61 63

  echo "--- suspend archives the live worker, comments, gives the slots and claims back, deletes the heartbeat"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  has "paseo :: archive :: agt_61_worker"
  hasnt "paseo :: archive :: agt_99_worker"
  hasnt "paseo :: stop"
  has "paseo :: ls :: -g :: --json :: --label :: mmw.spec=76 :: --label :: mmw.kind=worker"
  hasnt "wks_foreign_61"
  hasnt "workspace :: archive"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"
  [ "$(count_of "status.py --worker-grades")" = 1 ] \
    || fail "worker-grades should be read once, got $(count_of "status.py --worker-grades")"
  [ "$(count_of "/sub_issues")" = 1 ] \
    || fail "the batch should be read once, got $(count_of "/sub_issues")"
  [ -d "$MMW_FAKE_PASEO_STATE/issue-61" ] || fail "the workspace for #61 was removed"
  [ -d "$MMW_FAKE_PASEO_STATE/issue-63" ] || fail "the workspace for #63 was removed"
  git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-61 >/dev/null \
    || fail "branch issue-61 was removed"
  git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-63 >/dev/null \
    || fail "branch issue-63 was removed"

  echo "--- every ticket still in the agent queue carries one comment saying the night was suspended"
  has "gh :: issue :: comment :: 61 :: --body"
  has "gh :: issue :: comment :: 63 :: --body"
  [ "$(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")" = 2 ] \
    || fail "expected two suspend comments, got $(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")"
  grep -qF 'Its worker agt_61_worker was interrupted' "$MMW_TEST_LOG" \
    || fail "the comment on #61 does not say its worker was interrupted"
  grep -qF 'No session of ours was working on it' "$MMW_TEST_LOG" \
    || fail "the comment on #63 does not say it had no session"
  hasnt "gh :: issue :: comment :: 65"

  echo "--- the slots the night held are back, and the heartbeat is gone"
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 0 ] \
    || fail "slots are still held: $(python3 "$LEASE_PY" list)"
  has "paseo :: heartbeat :: delete :: hb_76"
  [ ! -f "$(git -C "$TMP/repo" rev-parse --absolute-git-dir)/mmw-heartbeat-76" ] \
    || fail "the heartbeat id file is still there"
  grep -q 'suspend #76: stopped 1, commented 2, slots given back 3, claims given back 2' "$TMP/out" \
    || fail "the summary line is wrong: $(cat "$TMP/out")"

  echo "--- advance after suspend re-dispatches the same tickets into the standing workspaces"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance after suspend exited $code: $(cat "$TMP/err")"
  grep -q '"title": "#61 worker"' "$TMP/out" \
    || fail "advance after suspend should re-dispatch #61: $(cat "$TMP/out")"
  hasnt "workspace :: create"
}

scenario_suspendbusy() {
  local code port hold
  fresh_repo
  reset_log
  write_open_batch
  open_a_night
  seed_workspace 65
  python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-65" >/dev/null
  seed_agent 61 worker
  write_heartbeat

  echo "--- something is still listening on #61's slot"
  port="$(python3 "$LEASE_PY" claim "$MMW_FAKE_PASEO_STATE/issue-61" \
          | python3 -c 'import json,sys; print(json.load(sys.stdin)["port_base"])')"
  hold="$TMP/listener.fifo"
  rm -f "$hold"; mkfifo "$hold"
  python3 -c '
import socket, sys
held = socket.socket()
held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
held.bind(("127.0.0.1", int(sys.argv[1])))
held.listen(1)
print("up", flush=True)
sys.stdin.read()
' "$port" < "$hold" > "$TMP/listener.out" &
  local listener=$!
  exec 9>"$hold"
  local waited=0
  until grep -q up "$TMP/listener.out" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    [ "$waited" -lt 50 ] || { fail "the listener never came up"; break; }
  done

  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"

  echo "--- the refusal is reported, never swallowed and never forced"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  grep -q 'lease not released' "$TMP/err" || fail "the refusal is not on stderr: $(cat "$TMP/err")"
  grep -q "port $port" "$TMP/err" || fail "the reason does not name the port: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$MMW_FAKE_PASEO_STATE")" = 1 ] \
    || fail "a slot with a live listener was taken anyway: $(python3 "$LEASE_PY" list)"

  echo "--- and the rest of the night is still suspended: workers archived, tickets told"
  has "paseo :: archive :: agt_61_worker"
  hasnt "paseo :: stop"
  [ "$(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")" = 2 ] \
    || fail "expected two suspend comments, got $(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")"
  grep -q 'suspend #76: stopped 1, commented 2, slots given back' "$TMP/out" \
    || fail "the summary line is wrong: $(cat "$TMP/out")"

  exec 9>&-
  wait "$listener" 2>/dev/null
  rm -f "$hold"
}

scenario_suspendnohb() {
  local code
  fresh_repo
  reset_log
  write_open_batch
  open_a_night
  seed_agent 61 worker
  echo "--- a missing heartbeat file is a normal close, not a failure"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "expected exit 0 without a heartbeat file, got $code: $(cat "$TMP/err")"
  ! grep -qi heartbeat "$TMP/err" \
    || fail "a missing heartbeat should not warn: $(cat "$TMP/err")"
  grep -q 'suspend #76:' "$TMP/out" || fail "the summary line is missing: $(cat "$TMP/out")"
}

scenario_status() {
  local code
  echo "--- status prints the table header and exits 0"
  reset_log
  fresh_repo
  write_open_batch
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "mmw status" "$TMP/out" || fail "the table header is missing: $(cat "$TMP/out")"
  grep -q "spec #76" "$TMP/out" || fail "the spec is missing from the header: $(cat "$TMP/out")"

  echo "--- a paseo that exits 1 becomes exit 2, one dispatch: line, no traceback"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_PASEO_SCENARIO=ls-fail \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 2 ] || fail "expected exit 2 when paseo fails, got $code: $(cat "$TMP/err")"
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "stderr should be exactly one line: $(cat "$TMP/err")"
  grep -q '^dispatch:' "$TMP/err" || fail "stderr should start with dispatch:: $(cat "$TMP/err")"
  ! grep -q Traceback "$TMP/err" || fail "stderr should not contain a traceback: $(cat "$TMP/err")"

  echo "--- a non-numeric spec is a refusal, exit 2"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" status abc)"
  [ "$code" = 2 ] || fail "expected exit 2 for a non-numeric spec, got $code: $(cat "$TMP/err")"
}

# ------------------------------------------------------------------ entry

ALL="check advance advanceconflict advancedirty start-worker start-reviewer start-verifier resume reverify summary release releaseother releaselive frontierwhy instancegate suspend suspendbusy suspendnohb status"

case "${1:-}" in
  check|advance|advanceconflict|advancedirty|start-worker|start-reviewer|start-verifier|resume|reverify|summary|release|releaseother|releaselive|frontierwhy|instancegate|suspend|suspendbusy|suspendnohb|status)
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
    release) echo DISPATCH-RELEASE-OK ;;
    releaseother) echo DISPATCH-RELEASE-OTHER-OK ;;
    releaselive) echo RELEASE-LIVE-OK ;;
    frontierwhy) echo DISPATCH-FRONTIER-WHY-OK ;;
    instancegate) echo DISPATCH-INSTANCE-GATE-OK ;;
    suspend) echo SUSPEND-OK ;;
    suspendbusy) echo SUSPEND-BUSY-OK ;;
    suspendnohb) echo SUSPEND-NOHB-OK ;;
    status) echo DISPATCH-STATUS-OK ;;
  esac
}

fn_for() {
  case "$1" in
    start-worker) echo scenario_start_worker ;;
    start-reviewer) echo scenario_start_reviewer ;;
    start-verifier) echo scenario_start_verifier ;;
    *) echo "scenario_$1" ;;
  esac
}

for name in $wanted; do
  echo "=== $name"
  declare -F "$(fn_for "$name")" >/dev/null \
    || { echo "$name failed: this file has no $(fn_for "$name")" >&2; exit 1; }
  "$(fn_for "$name")"
  code=$?
  [ "$code" -eq 0 ] \
    || { echo "$name failed: $(fn_for "$name") exited $code without reporting" >&2; exit 1; }
  if [ "$rc" -eq 0 ]; then
    banner_for "$name"
  else
    echo "$name failed" >&2
    exit 1
  fi
done
