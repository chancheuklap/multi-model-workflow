#!/usr/bin/env bash
#
# Tests for dispatch.sh. Run named scenarios or all:
#
#   bash mmw-v4/tests/dispatch/test_dispatch.sh <scenario> [<scenario> ...]|all
#   An unknown scenario prints the known names and exits 2.
#
# A fake `paseo`, a fake `herdr`, a fake `orca` and a fake `gh` sit in front of the
# real ones on PATH and write every call they receive to a log, one call per line,
# fields joined by ` :: `. What the script does to Paseo, to Herdr, to Orca and to
# the tracker is therefore checkable without a daemon, a network, or a ticket. The
# last line of a passing run is the scenario's EXPECT string; everything before it
# says what was checked.
#
# Every scenario runs with the night on spec 76 open: a live stand-in process holds the
# relay's lock in this run's state directory and records that it watches spec 76, so
# `start` and `advance` find the relay they refuse to work without. A scenario about
# opening, acking or refusing clears it first (`no_relay`), and the real relay `open`
# starts is stopped before the scenario ends.

set -uo pipefail
# The session running this suite may itself be a runner's session; the scenarios say
# which one they stand in, and nothing else may answer `self`.
unset PASEO_AGENT_ID ORCA_TERMINAL_HANDLE HERDR_PANE_ID
unset MMW_SPEC MMW_TASK_SCOPE
while IFS='=' read -r name _; do
  case "$name" in NMEM_*) unset "$name" ;; esac
done < <(env)

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$(dirname "$HERE")")/skills/dispatch"
DISPATCH="$SKILL/scripts/dispatch.sh"

setup_fixture() {
rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
# A relay left running would go on polling a tracker that is gone, through whatever `gh`
# is next on PATH.
trap 'stop_test_browsers; stop_test_listeners; stop_test_boards; no_relay; rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/paseo-state"

cat > "$TMP/bin/paseo" <<'FAKE'
#!/usr/bin/env python3
import json, os, re, subprocess, sys
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
    codex = "unavailable" if scenario == "provider-down" else "available"
    print(json.dumps([
        {"provider": "claude", "status": "available", "label": "Claude"},
        {"provider": "codex", "status": codex, "label": "Codex"},
    ]))
    sys.exit(0)

if args[:2] == ["provider", "models"]:
    print(json.dumps([{"id": "gpt-5.6-sol", "thinkingOptionIds": ["high", "xhigh"]}]))
    sys.exit(0)

# The real call refreshes the daemon's snapshot for one host and answers with a text
# blob; `check` reads it only to print under a refusal, so one line of it is enough.
if args[:2] == ["provider", "diagnostic"]:
    host = args[2] if len(args) > 2 else ""
    down = scenario == "provider-down" and host == "codex"
    print(json.dumps({
        "provider": host,
        "diagnostic": f"{host}\n  Resolved path: /fake/{host}\n"
                      + ("  Auth: not logged in\n  Status: Unavailable" if down
                         else "  Models: 2\n  Status: Ready"),
    }))
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

# Registering is idempotent in Paseo — an already-registered path answers with the
# project it already has — so one row is the whole of what this has to imitate. Set
# MMW_FAKE_PROJECT_UNREGISTRABLE to make the daemon refuse instead.
if args[:2] == ["project", "create"]:
    if os.environ.get("MMW_FAKE_PROJECT_UNREGISTRABLE"):
        print("Cannot reach the daemon", file=sys.stderr)
        sys.exit(1)
    print(json.dumps({
        "projectId": "prj_test",
        "name": "repo",
        "kind": "git",
        "path": args[2] if len(args) > 2 else os.getcwd(),
    }))
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
    if scenario == "ls-garbage":
        print("not-json")
        sys.exit(0)
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

# `paseo run -d --json … -- <prompt>`: records the request in the shape the checks read
# (runs.jsonl, newest last), lists the agent with its labels, answers with its id.
if args[:1] == ["run"]:
    if scenario == "run-fail" or (scenario == "run-fail-after-one" and (state / "runs.jsonl").exists()):
        print("Error: Failed to create agent: provider initialization failed", file=sys.stderr)
        sys.exit(1)
    rest = args[1:]
    prompt = rest[rest.index("--") + 1] if "--" in rest else rest[-1]
    def flag(name):
        return rest[rest.index(name) + 1] if name in rest else None
    labels = {}
    for i, a in enumerate(rest):
        if a == "--label" and i + 1 < len(rest) and "=" in rest[i + 1]:
            k, v = rest[i + 1].split("=", 1)
            labels[k] = v
    settings = {}
    if flag("--mode"):
        settings["modeId"] = flag("--mode")
    if flag("--thinking"):
        settings["thinkingOptionId"] = flag("--thinking")
    rows = load("agents.json")
    ident = "agt_run_%d" % (len(rows) + 1)
    request = {
        "id": ident,
        "background": "-d" in rest,
        "title": flag("--title"),
        "provider": flag("--provider"),
        "settings": settings,
        "labels": labels,
        "cwd": flag("--cwd"),
        "initialPrompt": prompt,
        "environment": [rest[i + 1] for i, value in enumerate(rest[:-1]) if value == "--env"],
    }
    with open(state / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(request) + "\n")
    rows.append({"id": ident, "name": request["title"] or ident, "status": "running",
                 "cwd": request["cwd"], "labels": labels})
    save("agents.json", rows)
    print(json.dumps({"agentId": ident, "status": "running", "cwd": request["cwd"]}))
    sys.exit(0)

if args[:1] == ["send"]:
    # MMW_FAKE_SEND_FAILS makes the daemon refuse the message the way it does when the
    # agent is in a turn: exit non-zero with the reason in one English sentence.
    if os.environ.get("MMW_FAKE_SEND_FAILS"):
        print(json.dumps({"error": {"code": "SEND_FAILED",
                                    "message": "Failed to send message: "
                                               "A foreground turn is already active"}}))
        sys.exit(1)
    print(json.dumps({"ok": True}))
    sys.exit(0)

if args[:1] == ["inspect"]:
    ident = args[1] if len(args) > 1 else ""
    row = next((a for a in load("agents.json") if a.get("id") == ident), {})
    print(json.dumps({"ParentAgentId": row.get("ParentAgentId")}))
    sys.exit(0)

# One answer for the whole daemon, which is what `status` reads it for.
if args[:2] == ["permit", "ls"]:
    print(json.dumps(load("permits.json")))
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
    # The real CLI refuses a running agent without --force ("Error: Agent <id> is
    # currently running") and only then interrupts it. This fake used to accept every
    # archive, which is how `suspend` shipped unable to stop the one thing it exists to
    # stop: a worker in the middle of a turn.
    force = "--force" in args
    if scenario == "archive-fail":
        print("Error: the daemon did not answer", file=sys.stderr)
        sys.exit(1)
    positional = [a for a in args[1:] if not a.startswith("--")]
    ident = positional[0] if positional else ""
    rows = load("agents.json")
    target = next((a for a in rows if a.get("id") == ident), None)
    if target is not None and target.get("status") == "running" and not force:
        print(f"Error: Agent {ident} is currently running", file=sys.stderr)
        sys.exit(1)
    save("agents.json", [a for a in rows if a.get("id") != ident])
    print(json.dumps({"id": ident, "archived": True}))
    sys.exit(0)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

cat > "$TMP/bin/herdr" <<'FAKE'
#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("herdr" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")

args = sys.argv[1:]
state = Path(os.environ["MMW_FAKE_HERDR_STATE"])
state.mkdir(parents=True, exist_ok=True)
scenario = os.environ.get("MMW_FAKE_HERDR_SCENARIO", "")


def load_agents():
    path = state / "agents.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save_agents(rows):
    (state / "agents.json").write_text(json.dumps(rows), encoding="utf-8")


def opt(flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return ""


if args[:2] == ["pane", "close"]:
    pane = args[2] if len(args) > 2 else ""
    save_agents([a for a in load_agents() if a.get("pane_id") != pane])
    print(json.dumps({"result": {"closed": pane}}))
    sys.exit(0)

if args[:2] == ["tab", "create"]:
    if scenario == "tab-fail":
        print(json.dumps({"error": {"code": "tab_create_failed", "message": "no pane"}}),
              file=sys.stderr)
        sys.exit(1)
    print(json.dumps({
        "id": "cli:tab:create",
        "result": {
            "tab": {"tab_id": "tab_1"},
            "root_pane": {"pane_id": "pane_1"},
        },
    }))
    sys.exit(0)

if args[:2] == ["agent", "start"]:
    if scenario == "start-fail":
        print(json.dumps({"error": {"code": "agent_not_ready", "message": "not ready"},
                          "id": "cli:agent:start"}))
        sys.exit(1)
    name = args[2] if len(args) > 2 else ""
    rows = load_agents()
    rows.append({"name": name, "agent_status": "idle", "pane_id": opt("--pane") or "pane_1"})
    save_agents(rows)
    print(json.dumps({
        "id": "cli:agent:start",
        "result": {"agent": {"name": name, "agent_status": "idle"}},
    }))
    sys.exit(0)

if args[:2] == ["agent", "list"]:
    if scenario == "list-fail":
        sys.exit(1)
    if scenario == "list-garbage":
        print("not-json")
        sys.exit(0)
    if scenario == "list-shape":
        print(json.dumps({"result": "x"}))
        sys.exit(0)
    print(json.dumps({
        "id": "cli:agent:list",
        "result": {"agents": load_agents(), "type": "agent_list"},
    }))
    sys.exit(0)

if args[:2] == ["agent", "prompt"]:
    target = args[2] if len(args) > 2 else ""
    row = next((a for a in load_agents() if a.get("name") == target), None)
    if row is None:
        print(json.dumps({
            "error": {"code": "agent_not_found",
                      "message": "agent target %s not found" % target},
            "id": "cli:agent:prompt",
        }))
        sys.exit(1)
    code = os.environ.get("MMW_FAKE_HERDR_PROMPT") or scenario
    if code in ("agent_blocked", "send-blocked"):
        print(json.dumps({"error": {"code": "agent_blocked", "message": "blocked"},
                          "id": "cli:agent:prompt"}))
        sys.exit(1)
    if code in ("agent_prompt_stalled", "send-stalled"):
        print(json.dumps({"error": {"code": "agent_prompt_stalled", "message": "stalled"},
                          "id": "cli:agent:prompt"}))
        sys.exit(1)
    if code in ("timeout", "send-timeout"):
        print(json.dumps({"error": {"code": "timeout", "message": "timeout"},
                          "id": "cli:agent:prompt"}))
        sys.exit(1)
    print(json.dumps({
        "id": "cli:agent:prompt",
        "result": {"status": "working"},
    }))
    sys.exit(0)

if args[:2] == ["agent", "wait"]:
    sys.exit(1)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

cat > "$TMP/bin/orca" <<'FAKE'
#!/usr/bin/env python3
import json, os, sys
from pathlib import Path

log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("orca" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")

args = sys.argv[1:]
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
state.mkdir(parents=True, exist_ok=True)
scenario = os.environ.get("MMW_FAKE_ORCA_SCENARIO", "")
send_mode = os.environ.get("MMW_FAKE_ORCA_SEND", "") or scenario


def load_terminals():
    path = state / "terminals.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def save_terminals(rows):
    (state / "terminals.json").write_text(json.dumps(rows), encoding="utf-8")


def opt(flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return ""


if args[:2] == ["project", "setups"]:
    path = state / "setups.json"
    rows = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            rows = loaded if isinstance(loaded, list) else []
        except Exception:
            rows = []
    if scenario == "setups-shape":
        print(json.dumps({"ok": True, "result": rows}))
        sys.exit(0)
    # Orca 1.4.199 answers with an object: {"ok": true, "result": {"setups": [...]}}.
    print(json.dumps({"ok": True, "result": {"setups": rows}}))
    sys.exit(0)

if args[:2] == ["project", "setup-update"]:
    setup_id = opt("--setup")
    base = opt("--worktree-base-path")
    path = state / "setups.json"
    rows = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            rows = loaded if isinstance(loaded, list) else []
        except Exception:
            rows = []
    for row in rows:
        if isinstance(row, dict) and str(row.get("id") or "") == setup_id:
            if base:
                row["worktreeBasePath"] = base
    path.write_text(json.dumps(rows), encoding="utf-8")
    print(json.dumps({"ok": True, "result": {"id": setup_id}}))
    sys.exit(0)

if args[:2] == ["repo", "list"]:
    path = state / "repos.json"
    rows = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            rows = loaded if isinstance(loaded, list) else []
        except Exception:
            rows = []
    print(json.dumps({"ok": True, "result": {"repos": rows}}))
    sys.exit(0)

if args[:2] == ["worktree", "set"]:
    if scenario == "worktree-set-fail":
        print(json.dumps({"ok": False, "error": {"code": "link_failed"}}))
        sys.exit(1)
    if scenario == "parent-cycle" and "--parent-worktree" in args:
        # What Orca 1.4.205 answers for a parent that would make a cycle (read 2026-09-18).
        print(json.dumps({"ok": False, "error": {"code": "LINEAGE_PARENT_CYCLE",
                                                 "message": "A worktree cannot parent itself."}}))
        sys.exit(1)
    print(json.dumps({"ok": True, "result": {}}))
    sys.exit(0)

if args[:2] == ["tab", "create"]:
    print(json.dumps({"ok": True, "result": {"tab": {"id": "tab_board"}}}))
    sys.exit(0)

if args[:2] == ["worktree", "ps"] or args[:2] == ["worktree", "rm"] \
        or args[:2] == ["worktree", "create"]:
    print(json.dumps({"ok": True, "result": {}}))
    sys.exit(0)

if args[:2] == ["terminal", "create"]:
    if scenario == "start-fail":
        print(json.dumps({"ok": False, "error": {"code": "create_failed"}}),
              file=sys.stderr)
        sys.exit(1)
    if scenario == "start-refused":
        # What Orca 1.4.199 really does: the refusal is JSON on stdout, stderr is empty.
        print(json.dumps({"ok": False, "error": {"code": "selector_not_found",
                                                 "message": "selector_not_found"}}))
        sys.exit(1)
    handle = "term_%s" % (len(load_terminals()) + 1)
    rows = load_terminals()
    rows.append({
        "handle": handle,
        "connected": True,
        "writable": True,
        "worktree": opt("--worktree"),
        "title": opt("--title"),
        "command": opt("--command"),
    })
    save_terminals(rows)
    print(json.dumps({
        "ok": True,
        "result": {"handle": handle, "connected": True, "writable": True},
    }))
    sys.exit(0)

if args[:2] == ["terminal", "list"]:
    if scenario == "list-fail":
        sys.exit(1)
    if scenario == "list-garbage":
        print("not-json")
        sys.exit(0)
    if scenario == "list-shape":
        print(json.dumps({"result": "x"}))
        sys.exit(0)
    if scenario == "list-truncated":
        # The page Orca returns under --limit, with the asked-for handle past its end.
        print(json.dumps({"ok": True, "result": {"terminals": [], "truncated": True}}))
        sys.exit(0)
    print(json.dumps({
        "ok": True,
        "result": {"terminals": load_terminals()},
    }))
    sys.exit(0)

if args[:2] == ["terminal", "close"]:
    handle = opt("--terminal") or ""
    save_terminals([t for t in load_terminals() if t.get("handle") != handle])
    print(json.dumps({"ok": True, "result": {"closed": handle}}))
    sys.exit(0)

# The receipt in the shape Orca 1.4.199 answers `terminal send --json` with (read off a
# real terminal on 2026-09-10): the stages under result.send.prompt, warnings a list.
def receipt(stages, warnings=(), provider="claude", observation=None):
    prompt = {"requestId": "req_1", "stages": list(stages), "provider": provider}
    if observation:
        prompt["observation"] = observation
    return {"ok": True, "result": {"send": {"handle": opt("--terminal"), "accepted": True,
                                            "prompt": prompt},
                                   "warnings": list(warnings)}}


if args[:2] == ["terminal", "send"]:
    if send_mode in ("accepted-only", "send-accepted"):
        print(json.dumps(receipt(["input_accepted"],
                                 ["input was accepted but no turn start was observed"])))
        sys.exit(0)
    if send_mode == "refused":
        print(json.dumps({"ok": False, "error": {"code": "runtime_unavailable",
                                                 "message": "the runtime is restarting"}}))
        sys.exit(1)
    if send_mode == "unobserved":
        print(json.dumps(receipt(
            ["input_accepted"],
            ["input was accepted, but this provider cannot report delivery. "
             "Inspect the terminal before retrying."],
            provider="unsupported", observation="unsupported")))
        sys.exit(0)
    if send_mode in ("not-writable", "send-closed", "terminal_not_writable"):
        print(json.dumps({
            "ok": False,
            "code": "terminal_not_writable",
            "error": {"code": "terminal_not_writable",
                      "message": "terminal_not_writable"},
        }))
        sys.exit(1)
    target = opt("--terminal")
    row = next((t for t in load_terminals() if t.get("handle") == target), None)
    if row is None:
        print(json.dumps({
            "ok": False,
            "error": {"code": "terminal_handle_stale",
                      "message": "terminal_handle_stale"},
        }))
        sys.exit(1)
    print(json.dumps(receipt(["input_accepted", "turn_started"])))
    sys.exit(0)

# A condition that was met is answered under result.wait, and a wait that ran out as
# error.code `timeout` (Orca 1.4.199, read off a real `terminal wait --json` on
# 2026-09-11). `exit` is met only under `exited`: the program in a terminal this fake
# creates keeps running.
if args[:2] == ["terminal", "wait"]:
    want = opt("--for")
    if scenario == "wait-fail":
        sys.exit(1)
    if scenario == "wait-garbage" or (scenario == "exit-wait-garbage" and want == "exit"):
        print("not-json")
        sys.exit(0)
    target = opt("--terminal")
    row = next((t for t in load_terminals() if t.get("handle") == target), None)
    if row is None:
        print(json.dumps({
            "ok": False,
            "error": {"code": "terminal_handle_stale",
                      "message": "terminal_handle_stale"},
        }))
        sys.exit(1)
    if want == "exit":
        if scenario == "exited":
            print(json.dumps({
                "ok": True,
                "result": {"wait": {"handle": target, "condition": "exit",
                                    "satisfied": True, "status": "exited"}},
            }))
            sys.exit(0)
        print(json.dumps({
            "ok": False,
            "error": {"code": "timeout", "message": "timeout"},
        }))
        sys.exit(1)
    if scenario == "wait-busy":
        print(json.dumps({
            "ok": True,
            "result": {"wait": {"handle": target, "condition": want,
                                "satisfied": False, "status": "running"}},
        }))
        sys.exit(0)
    print(json.dumps({
        "ok": True,
        "result": {"wait": {"handle": target, "condition": want,
                            "satisfied": True, "status": "running"}},
    }))
    sys.exit(0)

# What the terminal holds, in the shape of a real `terminal read --json` (Orca 1.4.199,
# 2026-09-11): result.terminal.tail, a list of lines. The tail is empty, as Orca's is
# once the program has exited, unless MMW_FAKE_ORCA_TAIL gives the lines.
if args[:2] == ["terminal", "read"]:
    target = opt("--terminal")
    row = next((t for t in load_terminals() if t.get("handle") == target), None)
    if row is None:
        print(json.dumps({
            "ok": False,
            "error": {"code": "terminal_handle_stale",
                      "message": "terminal_handle_stale"},
        }))
        sys.exit(1)
    tail = os.environ.get("MMW_FAKE_ORCA_TAIL")
    print(json.dumps({
        "ok": True,
        "result": {"terminal": {
            "handle": target,
            "status": "exited" if scenario == "exited" else "running",
            "tail": tail.split("\n") if tail is not None else [],
        }},
    }))
    sys.exit(0)

print("{}", file=sys.stderr)
sys.exit(2)
FAKE

cat > "$TMP/bin/fake-gh-state" <<'PY'
#!/usr/bin/env python3
"""Atomic shared state for the fake tracker used by concurrent dispatch scenarios."""

import fcntl
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def locked(path: Path):
    lock = path.with_name(path.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_json(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def replace(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def update_json(path: Path, default, change) -> None:
    with locked(path):
        rows = read_json(path, default)
        change(rows)
        replace(path, json.dumps(rows))


verb, *args = sys.argv[1:]
if verb == "comments-add":
    path, number, body = Path(args[0]), args[1], Path(args[2])
    update_json(path, {}, lambda rows: rows.setdefault(number, []).append(
        body.read_text(encoding="utf-8").rstrip("\n")))
elif verb == "comments-read":
    comments, reads, number = Path(args[0]), Path(args[1]), args[2]
    with locked(reads):
        count = int(reads.read_text(encoding="utf-8")) + 1 if reads.is_file() else 1
        replace(reads, str(count))
    print(json.dumps({"posted": read_json(comments, {}).get(number, []), "count": count}))
elif verb == "issue-state":
    path, number, state = Path(args[0]), args[1], args[2]
    update_json(path, {}, lambda rows: rows.update({number: state}))
elif verb == "ticket-reopen":
    path, number = Path(args[0]), int(args[1])

    def reopen(rows):
        for ticket in rows:
            if ticket.get("number") == number:
                ticket["state"] = "OPEN"
                break

    update_json(path, [], reopen)
elif verb == "ticket-edit":
    path = Path(args[0])
    number = int(args[1])
    who, add_label, remove_label = args[2:]
    login = os.environ.get("FAKE_GH_LOGIN", "mmw-bot")
    if who in ("@me", login):
        who = login

    def edit(rows):
        for ticket in rows:
            if ticket.get("number") != number:
                continue
            ticket["assignees"] = [a for a in ticket.get("assignees") or [] if a != who]
            if os.environ.get("FAKE_GH_MUTATES_ISSUES"):
                labels = [label for label in ticket.get("labels") or []
                          if label != remove_label]
                if add_label and add_label not in labels:
                    labels.append(add_label)
                ticket["labels"] = labels
            break

    update_json(path, [], edit)
else:
    raise SystemExit(f"unknown fake-gh-state verb: {verb}")
PY

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
  *"issues?state=all&labels=mmw%3Aspec&per_page=100"*)
    printf '%s\n' ${FAKE_GH_SPECS:-76} ;;
  "repo view --json url -q .url")
    [ "${FAKE_GH_URL_FAIL:-0}" = 1 ] && exit 1
    printf '%s\n' "${FAKE_GH_URL:-https://github.com/o/r}" ;;
  "repo view"*)
    printf '%s\n' "${FAKE_GH_REPO:-o/r}" ;;
  *"--json body -q .body")
    [ -z "${FAKE_GH_BODY_FAILS:-}" ] || { echo "HTTP 502" >&2; exit 1; }
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
print(next((t for t in rows if t.get("number") == want), {}).get("body", ""))
' ;;
  *"--json parent,labels,body"*|*"--json labels,body"*|*"--json labels"|*"--json title,body"|*"--json parent,title"|*"--json labels,title")
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((row for row in rows if row.get("number") == want), None)
if found is None:
    raise SystemExit(1)
print(json.dumps({
    "parent": found.get("parent"),
    "labels": [{"name": name} for name in found.get("labels", [])],
    "body": found.get("body", ""),
    "title": found.get("title", ""),
}))
' ;;
  *"--json state,labels,blockedBy,title,parent"*|*"--json state,labels,blockedBy,title,body"*|*"--json state,labels,blockedBy,title"*)
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
            "parent": found.get("parent", {"number": 76}),
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
    "parent": ({"number": int(os.environ.get("FAKE_GH_PARENT", "76"))}
               if os.environ.get("FAKE_GH_PARENT", "76") else None),
}))
' ;;
  "pr list --head "*)
    [ "${FAKE_GH_PR-7}" = none ] || printf '%s\n' "${FAKE_GH_PR-7}" ;;
  "pr list --base "*)
    if [ -n "${FAKE_GH_PERSIST_PR:-}" ] && [ -f "$MMW_FAKE_PASEO_STATE/pr-open" ]; then
      echo '[{"url":"https://github.com/o/r/pull/7"}]'
    else
      echo '[]'
    fi ;;
  "pr create "*)
    [ -z "${FAKE_GH_PR_CREATE_FAIL:-}" ] || { echo 'HTTP 502' >&2; exit 1; }
    if [ -n "${FAKE_GH_PERSIST_PR:-}" ]; then
      [ ! -f "$MMW_FAKE_PASEO_STATE/pr-open" ] || { echo 'already exists' >&2; exit 1; }
      touch "$MMW_FAKE_PASEO_STATE/pr-open"
    fi
    echo 'https://github.com/o/r/pull/7' ;;
  "pr checks "*)
    [ -z "${FAKE_GH_PR_CHECKS_FAIL:-}" ] || { echo 'HTTP 502' >&2; exit 1; }
    if [ -n "${FAKE_GH_PR_CHECKS_DELAY:-}" ]; then
      reads="$(cat "$MMW_FAKE_PASEO_STATE/pr-check-reads" 2>/dev/null || echo 0)"
      reads=$((reads + 1))
      echo "$reads" > "$MMW_FAKE_PASEO_STATE/pr-check-reads"
      [ "$reads" -gt "$FAKE_GH_PR_CHECKS_DELAY" ] || FAKE_GH_PR_CHECKS=''
    fi
    if [[ "$*" == *"--json name,bucket"* ]] && [[ "$*" != *"--jq"* ]]; then
      [ -n "${FAKE_GH_PR_CHECKS:-}" ] || { echo 'no checks reported on the branch' >&2; exit 1; }
      MMW_CHECKS="${FAKE_GH_PR_CHECKS:-}" python3 -c '
import json, os
rows = [line.rsplit(" ", 1) for line in os.environ["MMW_CHECKS"].splitlines() if line]
print(json.dumps([{"name": name, "bucket": bucket} for name, bucket in rows]))'
    elif [ -n "${FAKE_GH_PR_CHECKS:-}" ]; then
      printf '%s\n' "$FAKE_GH_PR_CHECKS"
      if [[ "$*" == *"--watch"* ]] && printf '%s\n' "$FAKE_GH_PR_CHECKS" | grep -Eq ' (fail|cancel)$'; then
        exit 1
      fi
    else
      echo 'no checks reported on the branch' >&2
      exit 1
    fi ;;
  "workflow run "*)
    [ -z "${FAKE_GH_WORKFLOW_FAIL:-}" ] || { echo 'workflow refused' >&2; exit 1; }
    touch "$MMW_FAKE_PASEO_STATE/dispatched-run"
    [ -n "${FAKE_GH_RUN_NO_URL:-}" ] || echo 'https://github.com/o/r/actions/runs/81' ;;
  "run list "*)
    if [ -f "$MMW_FAKE_PASEO_STATE/dispatched-run" ]; then
      echo '[{"databaseId": 81}, {"databaseId": 80}]'
    else
      echo '[{"databaseId": 80}]'
    fi ;;
  "run watch "*)
    [ -z "${FAKE_GH_RUN_WATCH_FAIL:-}" ] || { echo 'watch connection lost' >&2; exit 1; }
    [ "${FAKE_GH_RUN_CONCLUSION:-success}" = success ] ;;
  "run view "*)
    printf '%s\n' "${FAKE_GH_RUN_CONCLUSION:-success}" ;;
  "api graphql "*reviewThreads*)
    [ -z "${FAKE_GH_PR_THREADS:-}" ] || printf '%s\n' "$FAKE_GH_PR_THREADS" ;;
  "api graphql "*)
    # The tree of issues under `root=<n>`, the way `issue_tree.py` asks for it: any number that
    # is not one of the fixture tickets is the spec, whose children are every ticket; a
    # ticket's children are its own `children` numbers. FAKE_GH_TREE_SHORT answers with
    # one ticket fewer than the count it gives, the way a page left unread would.
    MMW_GRAPHQL_ARGS="$*" python3 -c '
import json, os, re
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
found = re.search(r"(?:^| )root=(\d+)", os.environ.get("MMW_GRAPHQL_ARGS") or "")
want = int(found.group(1)) if found else None
by_number = {t["number"]: t for t in rows if "number" in t}

def node(number, depth):
    t = by_number.get(number, {})
    out = {"number": number, "title": t.get("title", "a ticket"),
           "state": t.get("state", "OPEN")}
    if depth:
        kids = t.get("children", [])
        out["subIssuesSummary"] = {"total": len(kids), "completed": 0}
        out["subIssues"] = {"nodes": [node(k, depth - 1) for k in kids]}
    return out

if want in by_number:
    issue = node(want, 1)
else:
    tickets = [node(t["number"], 1) for t in rows if "number" in t]
    total = len(tickets)
    if os.environ.get("FAKE_GH_TREE_SHORT") and tickets:
        tickets = tickets[:-1]
    issue = {"number": want, "title": "the spec", "state": "OPEN",
             "subIssuesSummary": {"total": total, "completed": 0},
             "subIssues": {"nodes": tickets}}
print(json.dumps({"data": {"repository": {"issue": issue}}}))
' ;;
  *"/sub_issues"*)
    # The relay still reads a spec's children over REST: every fixture ticket is the
    # spec's, and a ticket has none.
    MMW_SUB_ISSUES_URL="$*" python3 -c '
import json, os, re
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
url = os.environ.get("MMW_SUB_ISSUES_URL") or ""
found = re.search(r"/issues/(\d+)/sub_issues", url)
want = int(found.group(1)) if found else None
owned = {t["number"] for t in rows if "number" in t}
page = [] if want is None or want in owned else [{"number": t["number"]} for t in rows]
if "--jq .[].number" in url:
    for row in page:
        print(row["number"])
else:
    print(json.dumps(page))
' ;;
  *"--json parent"*)
    # `parent_of` and `ticket_spec`: the issue this one sits under. A fixture ticket
    # names its own `parent`; any other number is the spec, which sits under nothing.
    MMW_WANT="$3" MMW_JQ="$*" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t.get("number") == want), None)
if found is not None:
    parent = found.get("parent", {"number": int(os.environ.get("FAKE_GH_PARENT") or 76)}
                       if os.environ.get("FAKE_GH_PARENT", "76") else None)
else:
    parent = None
if "--jq" in os.environ["MMW_JQ"]:
    print(parent["number"] if parent else "")
else:
    print(json.dumps({"parent": parent}))
' ;;
  *"--json state --jq"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
from pathlib import Path
states = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-issue-states.json"
changed = json.loads(states.read_text()) if states.is_file() else {}
print(changed.get(str(want), next((t for t in rows if t.get("number") == want), {}).get("state", "OPEN")))
' ;;
  *"--json labels --jq"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t.get("number") == want), {})
for name in found.get("labels", []):
    print(name)
' ;;
  "issue reopen "*)
    "$MMW_FAKE_GH_STATE_HELPER" issue-state "$MMW_FAKE_PASEO_STATE/gh-issue-states.json" "$3" OPEN
    if [ -n "${FAKE_GH_MUTATES_ISSUES:-}" ]; then
      "$MMW_FAKE_GH_STATE_HELPER" ticket-reopen "$FAKE_GH_TICKETS_FILE" "$3"
    fi
    echo "✓ Reopened issue #$3" ;;
  "issue close "*)
    # FAKE_GH_CLOSE_FAILS: the tracker refuses the close, the way a network drop does.
    [ -z "${FAKE_GH_CLOSE_FAILS:-}" ] || { echo "HTTP 502" >&2; exit 1; }
    "$MMW_FAKE_GH_STATE_HELPER" issue-state "$MMW_FAKE_PASEO_STATE/gh-issue-states.json" "$3" CLOSED
    echo "✓ Closed issue #$3" ;;
  *"--json state,stateReason,labels,assignees,blockedBy,parent"*)
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t["number"] == want), {})
print(json.dumps({
    "state": found.get("state", "OPEN"),
    "stateReason": found.get("stateReason"),
    "labels": [{"name": n} for n in found.get("labels", ["ready-for-agent"])],
    "assignees": [{"login": n} for n in found.get("assignees", [])],
    "blockedBy": {"nodes": found.get("blockedBy", [])},
    "parent": found.get("parent"),
}))
' ;;
  *"--json state,labels,assignees,blockedBy,comments"*)
    MMW_WANT="$3" python3 -c '
import json, os
from pathlib import Path
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
want = int(os.environ["MMW_WANT"])
found = next((t for t in rows if t["number"] == want), {})
state = os.environ.get("MMW_FAKE_PASEO_STATE")
store = Path(state or ".") / "gh-comments.json"
posted = json.loads(store.read_text()).get(str(want), []) if state and store.is_file() else []
print(json.dumps({
    "state": found.get("state", "OPEN"),
    "labels": [{"name": n} for n in found.get("labels", ["ready-for-agent"])],
    "assignees": [{"login": n} for n in found.get("assignees", [])],
    "blockedBy": {"nodes": found.get("blockedBy", [])},
    "comments": [{"body": b} for b in list(found.get("comments", [])) + posted],
    "body": found.get("body", ""),
    "title": found.get("title", "a ticket"),
    "createdAt": found.get("createdAt", "2026-08-30T00:00:00Z"),
    "closedAt": found.get("closedAt", ""),
}))
' ;;
  *"--json comments"*)
    if [ -n "${FAKE_GH_COMMENTS_MARKER:-}" ] && [ ! -e "$FAKE_GH_COMMENTS_MARKER.used" ]; then
      : > "$FAKE_GH_COMMENTS_MARKER.used"
      : > "$FAKE_GH_COMMENTS_MARKER"
      while [ ! -e "$FAKE_GH_COMMENTS_RELEASE" ]; do sleep 0.05; done
    fi
    comment_state="$("$MMW_FAKE_GH_STATE_HELPER" comments-read \
      "${MMW_FAKE_PASEO_STATE:-.}/gh-comments.json" \
      "${MMW_FAKE_PASEO_STATE:-.}/comment_reads" "$3")"
    MMW_WANT="$3" MMW_COMMENT_STATE="$comment_state" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
try:
    want = int(os.environ["MMW_WANT"])
except Exception:
    want = None
found = next((t for t in rows if t.get("number") == want), {})
comment_state = json.loads(os.environ["MMW_COMMENT_STATE"])
posted = comment_state["posted"]
count = comment_state["count"]
comments = list(found.get("comments", [])) + posted
if count == int(os.environ.get("FAKE_GH_UNREADABLE_ON_COMMENT_READ", "0")):
    comments.append("unreadable event\n\n<!-- mmw {\"v\":1,\"event\":\"ticket.passed\",\"commit\": -->")
print(json.dumps({
    "comments": [{"body": b} for b in comments],
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
    MMW_WANT="$3" python3 -c '
import json, os
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
try:
    want = int(os.environ["MMW_WANT"])
except Exception:
    want = None
print(next((t for t in rows if t.get("number") == want), {}).get("title", "a ticket"))
' ;;
  *"api user"*)
    printf '%s\n' "${FAKE_GH_LOGIN:-mmw-bot}" ;;
  "issue comment "*)
    # FAKE_GH_COMMENT_FAILS: the tracker refuses the comment, the way a network drop does.
    [ -z "${FAKE_GH_COMMENT_FAILS:-}" ] || { echo "HTTP 502" >&2; exit 1; }
    "$MMW_FAKE_GH_STATE_HELPER" comments-add \
      "$MMW_FAKE_PASEO_STATE/gh-comments.json" "$3" "$MMW_GH_LAST_BODY"
    echo "https://github.com/o/r/issues/$3#issuecomment-1" ;;
  *"issue edit"*)
    number="$3"
    remove="" add_label="" remove_label=""
    skip=0
    for a in "$@"; do
      if [ "$skip" = 1 ]; then remove="$a"; skip=0; continue; fi
      [ "$a" = "--remove-assignee" ] && skip=1
    done
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --add-label) add_label="$2"; shift 2 ;;
        --remove-label) remove_label="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    if [ -n "$remove" ] && [ -n "${FAKE_GH_TICKETS_FILE:-}" ] && [ -f "$FAKE_GH_TICKETS_FILE" ]; then
      "$MMW_FAKE_GH_STATE_HELPER" ticket-edit "$FAKE_GH_TICKETS_FILE" "$number" \
        "$remove" "$add_label" "$remove_label"
    fi
    echo '{}' ;;
  *) echo '{}' ;;
esac
FAKE

cat > "$TMP/bin/playwright-cli" <<'FAKE'
#!/usr/bin/env python3
import os, subprocess, sys, time
from pathlib import Path

with open(os.environ["MMW_TEST_LOG"], "a") as log:
    log.write("playwright-cli" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
if sys.argv[2] == "open":
    pidfile = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "browser-pids"
    ready = pidfile.with_name(sys.argv[1][3:] + ".ready")
    subprocess.Popen([sys.executable, str(Path(__file__).with_name("cliDaemon.js")),
                      sys.argv[1][3:], str(pidfile), str(ready)],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(200):
        if ready.exists():
            break
        time.sleep(.01)
    else:
        sys.exit("fake browser daemon did not start")
FAKE
cat > "$TMP/bin/cliDaemon.js" <<'FAKE'
import os, signal, subprocess, sys, time
from pathlib import Path

signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'])
with open(sys.argv[2], 'a') as log:
    log.write(f'{os.getpid()} {child.pid}\n')
Path(sys.argv[3]).touch()
time.sleep(300)
FAKE
chmod +x "$TMP/bin/playwright-cli"

stop_test_browsers() {
  local pid
  if [ -f "$TMP/paseo-state/browser-pids" ]; then
    for pid in $(cat "$TMP/paseo-state/browser-pids"); do
      kill -KILL "$pid" 2>/dev/null || true
    done
    rm -f "$TMP/paseo-state/browser-pids"
  fi
}

REAL_PYTHON="$(command -v python3)"
cat > "$TMP/bin/python3" <<WRAPPER
#!/bin/bash
for a in "\$@"; do
  case "\$a" in
    *supervisor.py)
      if [ -n "\${MMW_TEST_BOARD_LOCK:-}" ] && [ "\${MMW_TEST_BOARD_LOCK_HELD:-0}" != 1 ]; then
        exec "$REAL_PYTHON" - "\$@" <<'PYLOCK'
import fcntl, os, subprocess, sys
# Separate test registries still allocate ports in the same machine-wide namespace.
with open(os.environ["MMW_TEST_BOARD_LOCK"], "a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    sys.exit(subprocess.call([sys.executable, *sys.argv[1:]]))
PYLOCK
      fi
      ;;
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
chmod +x "$TMP/bin/python3" "$TMP/bin/paseo" "$TMP/bin/herdr" "$TMP/bin/orca" \
  "$TMP/bin/gh" "$TMP/bin/fake-gh-state"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_FAKE_PASEO_STATE="$TMP/paseo-state"
export MMW_FAKE_HERDR_STATE="$TMP/herdr-state"
export MMW_FAKE_ORCA_STATE="$TMP/orca-state"
export MMW_GH_LAST_BODY="$TMP/gh-last-body"
export MMW_FAKE_GH_STATE_HELPER="$TMP/bin/fake-gh-state"
export MMW_HOME="$TMP/mmw-home"
# Tonight's runner is pinned: the session running this suite may itself sit in Orca,
# Herdr or tmux, and runtime detection would pick that runner.
export MMW_RUNNER=paseo
export MMW_HOST_CATALOG="$HERE/catalog.json"
mkdir -p "$MMW_HOME"
: > "$MMW_GH_LAST_BODY"
# The models.json every scenario starts from. It is this suite's own fixture, not
# roles.json's defaults: what a fresh machine is given can change without changing what
# the scenarios exercise (a Codex junior row, a Claude senior row at xhigh, so the two
# worker grades differ in host, model and effort).
cat > "$MMW_HOME/models.json" <<'JSON'
{"version":1,"runner":"orca","rows":{"junior-worker":{"host":"codex","model":"gpt 5.6 sol","effort":"high"},"senior-worker":{"host":"claude","model":"sonnet 5","effort":"xhigh"},"reviewer":{"host":"claude","model":"opus 5","effort":"high"},"advisor":{"host":"claude","model":"fable 5.1","effort":"medium"},"researcher":{"host":"claude","model":"opus 5","effort":"high"},"candidate":{"host":"claude","model":"opus 5","effort":"xhigh"}}}
JSON
# Every other session role of roles.json gets one row the fixture catalog offers, so a role
# added to the table needs no change here.
python3 - "$SKILL/roles.json" "$MMW_HOME/models.json" <<'PY'
import json, sys
roles = [r["name"] for r in json.load(open(sys.argv[1]))["roles"]]
config = json.load(open(sys.argv[2]))
for role in roles:
    config["rows"].setdefault(role, {"host": "claude", "model": "opus 5", "effort": "high"})
json.dump(config, open(sys.argv[2], "w"))
PY

# The repository's own check, `scripts/check`, with <body> after its shebang: written
# executable into <repo> and staged. Every fixture repository starts with a green one.
put_check() {
  mkdir -p "$1/scripts"
  printf '#!/usr/bin/env bash\n%s\n' "$2" > "$1/scripts/check"
  chmod +x "$1/scripts/check"
  git -C "$1" add scripts/check
}

git init -q --bare -b main "$TMP/origin.git"
git init -q -b main "$TMP/repo"
put_check "$TMP/repo" 'exit 0'
git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture
git -C "$TMP/repo" remote add origin "$TMP/origin.git"
git -C "$TMP/repo" push -q -u origin main

# ------------------------------------------------------------------ log reading

# ------------------------------------------------------------------ the relay

RELAY_PY="$SKILL/scripts/relay.py"
STATE_DIR="$MMW_HOME/state/o__r"

# End whatever holds the relay's lock for o/r — the stand-in or a real relay — and clear
# the state directory.
no_relay() {
  python3 - "$SKILL/scripts" "$STATE_DIR" <<'PY'
import os, signal, sys, time
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import statedir
state = Path(sys.argv[2])
holder = statedir.holder(state / "relay.lock") if (state / "relay.lock").exists() else None
if holder:
    try:
        os.kill(holder["pid"], signal.SIGTERM)
    except OSError:
        pass
    for _ in range(100):
        if statedir.holder(state / "relay.lock") is None:
            break
        time.sleep(0.05)
PY
  rm -rf "$STATE_DIR"
}

# A stand-in for a running relay whose one watch is <watch> (default spec 76), opened by
# paseo session agt_main: a process of its own, detached so that nobody here has to reap
# it, whose pid and identity the lock record and relay.json name, and the watch written
# into watches.json. It never polls; only what `watching`, `start` and `stop` read of a
# running relay is imitated.
fake_relay() {
  local watch='{"spec": 76}'
  [ -z "${1:-}" ] || watch="$1"
  python3 - "$SKILL/scripts" "$STATE_DIR" "$watch" <<'PY'
import json, subprocess, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import statedir
state = Path(sys.argv[2])
state.mkdir(parents=True, exist_ok=True)
child = subprocess.Popen(["sleep", "100000"], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
identity = None
for _ in range(50):
    identity = statedir.process_identity(child.pid)
    if identity:
        break
record = {"pid": child.pid, "identity": identity, "since": "2026-09-10T00:00:00Z",
          "purpose": "a stand-in relay"}
(state / "relay.lock").write_text(json.dumps(record) + "\n")
(state / "relay.json").write_text(json.dumps({"pid": child.pid, "identity": identity}) + "\n")
watch = json.loads(sys.argv[3])
key = (f"spec:{watch['spec']}" if watch.get("spec")
       else "tickets:" + ",".join(str(n) for n in sorted(watch["tickets"])))
(state / "watches.json").write_text(json.dumps(
    {key: {**watch, "runner": "paseo", "session": "agt_main", "at": "2026-09-10T00:00:00Z"}}) + "\n")
PY
}

# The pid of the relay holding o/r's lock, and the watches it has open, each as its watch
# (`{"spec": N}` or `{"tickets": [...]}`); nothing when none runs.
relay_now() {
  python3 - "$SKILL/scripts" "$STATE_DIR" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import statedir
state = Path(sys.argv[2])
holder = statedir.holder(state / "relay.lock") if (state / "relay.lock").exists() else None
if holder:
    try:
        watches = json.loads((state / "watches.json").read_text())
    except Exception:
        watches = {}
    shown = [{k: w[k] for k in ("spec", "tickets") if k in w} for _, w in sorted(watches.items())]
    print(holder["pid"], " ".join(json.dumps(w, sort_keys=True) for w in shown))
PY
}

# The orchestrator of the open watch <key> (`spec:N` or `tickets:N`), "runner session";
# nothing when that watch is not open.
watch_main() {
  python3 - "$STATE_DIR/watches.json" "$1" <<'PY'
import json, sys
try:
    watch = json.load(open(sys.argv[1])).get(sys.argv[2])
except (OSError, ValueError):
    watch = None
if watch:
    print(watch["runner"], watch["session"])
PY
}

# A Paseo agent `paseo ls` lists as idle, standing in for the orchestrator's own session.
seed_main_agent() {
  MMW_ID="$1" python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({"id": os.environ["MMW_ID"], "name": "main", "status": "idle", "labels": {}})
path.write_text(json.dumps(rows))
'
}

reset_log() {
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  mkdir -p "$MMW_FAKE_PASEO_STATE" "$MMW_FAKE_HERDR_STATE" "$MMW_FAKE_ORCA_STATE"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/workspaces.json"
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
  rm -f "$MMW_FAKE_PASEO_STATE/comment_reads" "$MMW_FAKE_PASEO_STATE/wait_delivered" \
    "$MMW_FAKE_PASEO_STATE/gh-comments.json" "$MMW_FAKE_PASEO_STATE/runs.jsonl" \
    "$MMW_FAKE_PASEO_STATE/gh-issue-states.json" \
    "$MMW_FAKE_PASEO_STATE/dispatched-run" "$MMW_FAKE_PASEO_STATE/pr-check-reads" \
    "$MMW_FAKE_PASEO_STATE/pr-open"
  echo '[]' > "$MMW_FAKE_HERDR_STATE/agents.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/terminals.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/setups.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/repos.json"
  unset MMW_FAKE_HERDR_SCENARIO MMW_FAKE_HERDR_PROMPT MMW_FAKE_SEND_FAILS
  unset MMW_FAKE_ORCA_SCENARIO MMW_FAKE_ORCA_SEND
  no_relay
  fake_relay
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

BOARD_TEST_PORTS=""
BOARD_TEST_LISTENER_PIDS=""
stop_test_listeners() {
  local pid
  for pid in ${BOARD_TEST_LISTENER_PIDS:-}; do
    kill "$pid" >/dev/null 2>&1 || true
    wait "$pid" 2>/dev/null || true
  done
  BOARD_TEST_LISTENER_PIDS=""
}

start_test_listener() {
  local port="$1" ready="$TMP/listener-$1.ready" pid attempt
  rm -f "$ready"
  python3 - "$port" "$ready" <<'PY' &
import signal, socket, sys
from pathlib import Path

sock = socket.socket()
sock.bind(("0.0.0.0", int(sys.argv[1])))
sock.listen()
Path(sys.argv[2]).write_text("ready\n")
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
while True:
    connection, _ = sock.accept()
    connection.close()
PY
  pid=$!
  BOARD_TEST_LISTENER_PIDS="$BOARD_TEST_LISTENER_PIDS $pid"
  for attempt in $(seq 1 100); do
    [ -f "$ready" ] && return 0
    sleep 0.01
  done
  return 1
}

# Every board server this run started: the ports a scenario recorded, plus every port in
# the registry, since `dispatch.sh open` makes sure this repository's board answers and a
# scenario that only meant to open a night has one too.
stop_test_boards() {
  local registered
  registered="$(python3 - "$MMW_HOME/boards.json" <<'PY'
import json, sys
try:
    print(" ".join(str(p) for p in json.load(open(sys.argv[1])).values()))
except (OSError, ValueError):
    pass
PY
)"
  BOARD_TEST_PORTS="${BOARD_TEST_PORTS:-} $registered"
  [ -n "${BOARD_TEST_PORTS// /}" ] || return 0
  MMW_PORTS="$BOARD_TEST_PORTS" MMW_SERVER="$(dirname "$(dirname "$HERE")")/board/server.py" \
    python3 -c '
import os, signal, subprocess, time
server = os.environ["MMW_SERVER"]
ports = os.environ["MMW_PORTS"].split()
targets = []
for line in subprocess.check_output(["ps", "-axo", "pid=,command="], text=True).splitlines():
    fields = line.strip().split(None, 1)
    if len(fields) != 2 or server not in fields[1]:
        continue
    if any(("--port " + port) in fields[1] for port in ports):
        targets.append(int(fields[0]))
for pid in targets:
    try: os.kill(pid, signal.SIGTERM)
    except OSError: pass
for _ in range(50):
    alive = []
    for pid in targets:
        try: os.kill(pid, 0); alive.append(pid)
        except OSError: pass
    if not alive: break
    time.sleep(0.02)
' >/dev/null 2>&1 || true
}

board_registry_port() {
  python3 - "$MMW_HOME/boards.json" <<'PY'
import json, sys
values = list(json.load(open(sys.argv[1])).values())
assert len(values) == 1, values
print(values[0])
PY
}

fresh_board_registry() {
  stop_test_listeners
  stop_test_boards
  BOARD_TEST_PORTS=""
  rm -f "$MMW_HOME/boards.json" "$MMW_HOME/boards.json.lock" \
    "$MMW_HOME/board.log" "$MMW_HOME"/board-*.log
  reset_log
  fresh_repo
}

# One comment the way the pipeline's scripts write it, JSON-quoted for a tickets.json
# fixture: `ev <event> <ticket> <first line> [events.py emit options...]`.
EVENTS_PY="$(dirname "$SKILL")/verify-ticket/scripts/events.py"
ev() {
  local name="$1" ticket="$2" line="$3"
  shift 3
  python3 "$EVENTS_PY" emit "$name" --ticket "$ticket" --line "$line" "$@" \
    | python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))'
}

# Posts one event on ticket <n> in the fake tracker, as if a script had written it.
post_ev() {
  local n="$1"
  shift
  MMW_N="$n" MMW_BODY="$(python3 "$EVENTS_PY" emit "$@")" python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()) if store.is_file() else {}
posted.setdefault(os.environ["MMW_N"], []).append(os.environ["MMW_BODY"])
store.write_text(json.dumps(posted))
'
}

post_raw_comment() {
  local n="$1" body="$2"
  MMW_N="$n" MMW_BODY="$body" python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()) if store.is_file() else {}
posted.setdefault(os.environ["MMW_N"], []).append(os.environ["MMW_BODY"])
store.write_text(json.dumps(posted))
'
}

# The newest ticket.bounced comment posted on ticket <n>, body included.
bounced_comment() {
  local n="${1:-61}"
  MMW_N="$n" python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()).get(os.environ["MMW_N"], []) if store.is_file() else []
found = ""
for body in posted:
    if "\"event\":\"ticket.bounced\"" in body:
        found = body
if found:
    print(found)
'
}

# The events posted on ticket <n> during this run, one `name key=value...` per line, for
# the keys asked for: `posted_events 61 session runner`.
posted_events() {
  local n="$1"
  shift
  MMW_N="$n" MMW_KEYS="$*" python3 -c '
import importlib.util, json, os
from pathlib import Path
spec = importlib.util.spec_from_file_location("ev", os.environ["MMW_EVENTS_PY_FOR_TESTS"])
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()).get(os.environ["MMW_N"], []) if store.is_file() else []
keys = os.environ["MMW_KEYS"].split()
for body in posted:
    what, payload = ev.parse(body)
    if what != "event":
        print("UNREADABLE " + str(payload))
        continue
    values = [body.splitlines()[0] if k == "line" else payload.get(k) for k in keys]
    print(" ".join([payload["event"]] + [f"{k}={v}" for k, v in zip(keys, values)]))
'
}
export MMW_EVENTS_PY_FOR_TESTS="$(dirname "$SKILL")/verify-ticket/scripts/events.py"

# The comments posted on ticket <n> during this run, as `gh issue view --json comments`
# answers them, for handing to `events.py … --comments-file -`.
gh_comments_json() {
  MMW_N="$1" python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()).get(os.environ["MMW_N"], []) if store.is_file() else []
print(json.dumps({"comments": [{"body": b} for b in posted]}))
'
}

wt() { printf '%s/.worktrees/issue-%s\n' "$TMP/repo" "$1"; }
trees() { printf '%s/.worktrees\n' "$TMP/repo"; }
assert_wt() {
  local dest listed
  dest="$(wt "$1")"
  [ -d "$dest" ] || fail "missing worktree issue-$1 at $dest"
  dest="$(cd "$dest" && pwd -P)"
  listed="$(git -C "$TMP/repo" worktree list --porcelain)"
  printf '%s\n' "$listed" | grep -F "worktree $dest" >/dev/null \
    || fail "git does not list worktree issue-$1: $listed"
}
assert_no_wt() {
  [ ! -d "$(wt "$1")" ] || fail "worktree issue-$1 should be gone"
}
assert_branch() {
  git -C "$TMP/repo" show-ref --verify --quiet "refs/heads/issue-$1" \
    || fail "branch issue-$1 was deleted"
}
assert_remote_branch() {
  git -C "$TMP/origin.git" show-ref --verify --quiet "refs/heads/issue-$1" \
    || fail "origin branch issue-$1 was deleted"
}
assert_no_branch() {
  git -C "$TMP/repo" show-ref --verify --quiet "refs/heads/issue-$1" \
    && fail "local branch issue-$1 should be gone"
  git -C "$TMP/origin.git" show-ref --verify --quiet "refs/heads/issue-$1" \
    && fail "origin branch issue-$1 should be gone"
  return 0
}
assert_kept_branch() {
  assert_branch "$1"
  git -C "$TMP/origin.git" show-ref --verify --quiet "refs/heads/issue-$1" \
    && fail "origin branch issue-$1 should be gone"
  return 0
}
hasnt_runner_worktree() {
  hasnt "paseo :: workspace :: create"
  hasnt "paseo :: workspace :: archive"
  hasnt "orca :: worktree :: create"
  hasnt "orca :: worktree :: rm"
  hasnt "orca :: worktree :: ps"
}

never_ran() { hasnt "paseo :: run"; }
nothing_printed() { [ ! -s "$TMP/out" ] || fail "stdout should be empty: $(cat "$TMP/out")"; }

# One field of the newest `paseo run` request the fake recorded. Nested keys use one
# dot: `labels.mmw.ticket` is labels["mmw.ticket"], not three hops.
out_json() {
  MMW_JSON_PATH="$1" python3 -c '
import json, os, sys
from pathlib import Path
node = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
path = os.environ["MMW_JSON_PATH"]
if "." in path:
    top, rest = path.split(".", 1)
    node = node[top][rest]
else:
    node = node[path]
print(node)
' "$MMW_FAKE_PASEO_STATE/runs.jsonl"
}

started_once() {
  [ "$(count_of "paseo :: run")" = 1 ] \
    || fail "expected exactly one paseo run, got $(count_of "paseo :: run")"
}

# A start that went through: one session started in the ticket's worktree, stdout is
# its id, and the ticket carries the `<kind>.started` event the later commands read.
assert_started() {
  python3 -c '
import importlib.util, json, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("ev", os.environ["MMW_EVENTS_PY_FOR_TESTS"])
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
out = [l for l in Path(sys.argv[1]).read_text().splitlines() if l.strip()]
run = json.loads(Path(sys.argv[2]).read_text().splitlines()[-1])
assert out == [run["id"]], (out, run["id"])
for key in ("title", "provider", "initialPrompt", "cwd"):
    assert run.get(key), key
# Which ticket and which kind a session is for is its started event, not a runner label.
assert not run.get("labels"), run.get("labels")
ticket, kind = run["title"].lstrip("#").split(" ", 1)
assert run["cwd"].endswith("/.worktrees/issue-" + ticket), run["cwd"]
posted = json.loads(Path(sys.argv[3]).read_text()).get(ticket, [])
state = ev.fold(posted)
found = ev.session_of(state, kind)
assert found and found["session"] == run["id"] and found["runner"] == "paseo", (found, posted)
assert found["worktree"] == run["cwd"] and found["branch"] == "issue-" + ticket, found
' "$TMP/out" "$MMW_FAKE_PASEO_STATE/runs.jsonl" "$MMW_FAKE_PASEO_STATE/gh-comments.json"
}

JUNIOR_HOST=codex
JUNIOR_MODEL=gpt-5.6-sol
SENIOR_MODEL=claude-sonnet-5
one_line_reason() {
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "the reason should be one line: $(cat "$TMP/err")"
}

fresh_repo() {
  rm -rf "$TMP/repo" "$TMP/origin.git" "$TMP/other-clone"
  git init -q --bare -b main "$TMP/origin.git"
  git init -q -b main "$TMP/repo"
  put_check "$TMP/repo" 'exit 0'
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture
  git -C "$TMP/repo" remote add origin "$TMP/origin.git"
  git -C "$TMP/repo" push -q -u origin main
}

fresh_project_night() {
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night proj
  commit_file "$TMP/repo" night.txt night night
}

closed_night_spec() {
  local project="${1:-proj}" into="${2:-night}"
  post_ev 76 spec.opened --ticket '' --spec 76 --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field "into=$into" --field "project=$project"
  post_ev 76 spec.closed --ticket '' --spec 76 --line "NIGHT SUMMARY" --field date=2026-09-11
}

# The night on spec <spec> opened, into <into>: `open_night [<spec>] [<into>]`.
open_night() {
  post_ev "${1:-76}" spec.opened --ticket '' --spec "${1:-76}" --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field "into=${2:-main}" --field project=proj
}

summary_ready_fixture() {
  open_night "${1:-76}" "${2:-main}"
}

# A green reverify of ticket <n> on origin/<into>'s tip, as `reverify` records it.
reverified() {
  local into="${2:-main}"
  post_ev "$1" ticket.checked --ticket "$1" --line "Reverify" --actor main --stage regress \
    --field run=reverify --field "commit=$(git -C "$TMP/origin.git" rev-parse "$into")" \
    --field result=met
}

# A second clone is the other machine in origin-authority scenarios.
other_clone() {
  if [ ! -d "$TMP/other-clone/.git" ]; then
    git clone -q "$TMP/origin.git" "$TMP/other-clone"
    git -C "$TMP/other-clone" config user.email other@t
    git -C "$TMP/other-clone" config user.name other
  fi
  printf '%s\n' "$TMP/other-clone"
}

commit_file() {
  local repo="$1" file="$2" text="$3" message="$4"
  printf '%s\n' "$text" > "$repo/$file"
  git -C "$repo" add "$file"
  git -C "$repo" -c user.email=t@t -c user.name=t commit -q -m "$message"
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
  local commit61="" commit62="" event61 event62
  commit61="$(git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-61 2>/dev/null)" || true
  commit62="$(git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-62 2>/dev/null)" || true
  event61="$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main ${commit61:+--field "commit=$commit61"})"
  event62="$(ev ticket.passed 62 "ALL MET" --field branch=issue-62 --field into=main ${commit62:+--field "commit=$commit62"})"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z",
   "comments": ["self-run\\n3 met", $event61]},
  {"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T02:00:00Z",
   "assignees": ["alice"],
   "comments": [$event62]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n", "title": "frontier ticket"}
]
JSON
}

# Ticket <n> of the written batch as a red reverify leaves it: open again, unassigned,
# and wearing the label that run put on it — `needs-triage`, or whatever triage swapped
# in for it.
reopened_in_triage() {
  MMW_N="$1" MMW_LABEL="${2:-needs-triage}" python3 - "$TMP/tickets.json" <<'REOPEN'
import json, os, sys
rows = json.load(open(sys.argv[1]))
for row in rows:
    if row["number"] == int(os.environ["MMW_N"]):
        row.update(state="OPEN", labels=[os.environ["MMW_LABEL"]],
                   assignees=[], closedAt="")
json.dump(rows, open(sys.argv[1], "w"))
REOPEN
}

write_one_passed() {
  local number="$1" commit="$2" extra="${3:-}"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": $number, "state": "CLOSED", "labels": [],
   "closedAt": "2026-09-11T01:00:00Z", "assignees": ["mmw-bot"],
   "comments": [$(ev ticket.passed "$number" "ALL MET" --field "branch=issue-$number" \
     --field "commit=$commit" --field into=main)${extra:+, $extra}]}
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
  post_ev "$n" "$kind.started" --ticket "$n" --spec "$spec" \
    --line "$kind started on paseo: session agt_${n}_$kind" \
    --field "session=agt_${n}_$kind" --field runner=paseo \
    $(start_facts "$MMW_FAKE_PASEO_STATE/issue-$n" "$n" "$kind")
}

# The facts every start carries beyond its session and runner, for events seeded by hand:
# `start_facts <absolute worktree> <ticket> <kind>`.
start_facts() {
  local grade="$3"
  [ "$3" = worker ] && grade=junior-worker
  printf '%s\n' --field "machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
    --field host=codex --field model=gpt-5.6-sol --field effort=high \
    --field "grade=$grade" --field "worktree=$1" --field "branch=issue-$2" \
    --field "base=0000000000000000000000000000000000000000" --field into=main
}

# The `<kind>.started` event `start` writes on a ticket, for a session seeded by hand:
# `runner_line <n> <runner> <session> <kind>`.
runner_line() {
  post_ev "$1" "$4.started" --ticket "$1" --line "$4 started on $2: session $3" \
    --field "session=$3" --field "runner=$2" $(start_facts "$(wt "$1")" "$1" "$4")
}

seed_herdr_agent() {
  local name="$1" status="${2:-idle}"
  MMW_NAME="$name" MMW_STATUS="$status" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_HERDR_STATE"])
path = state / "agents.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({
    "name": os.environ["MMW_NAME"],
    "agent_status": os.environ["MMW_STATUS"],
    "pane_id": "pane_1",
})
path.write_text(json.dumps(rows))
'
}

seed_orca_terminal() {
  local handle="$1" connected="${2:-true}" writable="${3:-true}"
  MMW_HANDLE="$handle" MMW_CONNECTED="$connected" MMW_WRITABLE="$writable" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
path = state / "terminals.json"
rows = json.loads(path.read_text()) if path.is_file() else []
rows.append({
    "handle": os.environ["MMW_HANDLE"],
    "connected": os.environ["MMW_CONNECTED"] == "true",
    "writable": os.environ["MMW_WRITABLE"] == "true",
})
path.write_text(json.dumps(rows))
'
}

seed_workspace() {
  local n="$1" dest
  dest="$(wt "$n")"
  [ -d "$dest" ] && return 0
  mkdir -p "$(trees)"
  if git -C "$TMP/repo" rev-parse --verify --quiet "refs/heads/issue-$n" >/dev/null; then
    git -C "$TMP/repo" worktree add --quiet "$dest" "issue-$n"
  else
    git -C "$TMP/repo" worktree add --quiet -b "issue-$n" "$dest"
  fi
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

# The verify-ticket skill's scripts dispatch.sh runs are handed to it with --tools,
# the way the agent does; TOOLS holds those arguments for every call below.
TOOLS=(--tools "$TMP/fake/skills/verify-ticket/scripts" --tools "$(dirname "$SKILL")/verify-ticket/scripts")

skill_copy_for() {
  local copy="$TMP/fake/skills/$1"
  rm -rf "$TMP/fake"
  mkdir -p "$copy" "$TMP/fake/skills/verify-ticket/scripts"
  cp -R "$SKILL/hosts.json" "$SKILL/roles.json" "$SKILL/scripts" "$SKILL/references" "$copy/"
  cp "$(dirname "$SKILL")/verify-ticket/scripts/events.py" \
     "$(dirname "$SKILL")/verify-ticket/scripts/issue_tree.py" \
     "$TMP/fake/skills/verify-ticket/scripts/"
  printf '#!/usr/bin/env bash\nexit %s\n' "${2:-0}" > "$TMP/fake/install.sh"
  chmod +x "$TMP/fake/install.sh"
  printf '%s\n' "$copy"
}

}

# ------------------------------------------------------------------ scenarios

scenario_check() {
  local copy code
  copy="$(skill_copy_for check)"
  fresh_project_night

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

  echo "--- every host of the batch is refreshed once, however many rows share it"
  [ "$(count_of 'provider :: diagnostic')" = 2 ] \
    || fail "expected one diagnostic per distinct host, got $(count_of 'provider :: diagnostic'): $(grep 'provider :: diagnostic' "$MMW_TEST_LOG")"

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
  grep -q 'codex' "$TMP/err" || fail "the reason does not name the provider: $(cat "$TMP/err")"
  grep -q '#61' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" -ge 2 ] \
    || fail "expected one line per failing check: $(cat "$TMP/err")"

  echo "--- install.sh --check failing is a warning, not a refusal, and nothing is installed"
  copy="$(skill_copy_for check 1)"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker"]}
]
JSON
  printf '#!/usr/bin/env bash\necho "$*" >> "%s/install-calls"\n[ "${1:-}" = --check ] && { echo "缺 something"; exit 1; }\nexit 0\n' "$TMP" > "$TMP/fake/install.sh"
  rm -f "$TMP/install-calls"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "expected exit 0 when only install.sh --check fails, got $code: $(cat "$TMP/err")"
  [ "$(tr '\n' ' ' < "$TMP/install-calls")" = "--check " ] \
    || fail "check should run install.sh --check once and install nothing: $(cat "$TMP/install-calls" 2>&1)"

  echo "--- the installed checkout only checks too"
  rm -f "$TMP/install-calls"
  mkdir -p "$MMW_HOME"
  printf '%s\n' "$TMP/fake" > "$MMW_HOME/installed-root"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  rm -f "$MMW_HOME/installed-root"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(tr '\n' ' ' < "$TMP/install-calls")" = "--check " ] \
    || fail "check should run install.sh --check once and never install: $(cat "$TMP/install-calls")"

  echo "--- a row that does not resolve on tonight's runner is refused in the resolver's words, whatever the tickets carry"
  copy="$(skill_copy_for check)"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  python3 -c '
import json, sys
path = sys.argv[1]
catalog = json.load(open(path))
catalog["claude"] = [o for o in catalog["claude"] if o["id"] != "claude-opus-5"]
json.dump(catalog, open(sys.argv[2], "w"))
' "$HERE/catalog.json" "$TMP/catalog-no-opus.json"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_RUNNER=orca \
          MMW_HOST_CATALOG="$TMP/catalog-no-opus.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "a reviewer row that does not resolve is exit 2, got $code: $(cat "$TMP/err")"
  grep -qw "orca" "$TMP/err" && grep -qF "'opus 5'" "$TMP/err" \
    || fail "the refusal should name the row, the runner and the resolver's reason: $(cat "$TMP/err")"
  hasnt "paseo :: provider"

  echo "--- a runner this skill has no adapter for is refused before the night"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_RUNNER=tmux \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "a runner with no adapter is exit 2, got $code: $(cat "$TMP/err")"
  grep -qw "tmux" "$TMP/err" \
    || fail "the refusal should name the runner: $(cat "$TMP/err")"
}

scenario_checkrunsnocheck() {
  local copy code
  copy="$(skill_copy_for check)"
  fresh_project_night
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON

  echo "--- check opens no repository-check run, even with uncommitted changes"
  rm -f "$TMP/check-base"
  put_check "$TMP/repo" "printf '%s\\n' \"\$MMW_BASE_REF\" >> '$TMP/check-base'"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "check on a ready repository expected 0, got $code: $(cat "$TMP/err")"
  [ ! -e "$TMP/check-base" ] || fail "check must not run scripts/check: $(cat "$TMP/check-base")"
}

scenario_checkrefusesnocheck() {
  local copy code
  copy="$(skill_copy_for check)"
  fresh_project_night
  echo '[]' > "$TMP/tickets.json"

  echo "--- a scripts/check that is not executable, or absent, refuses the night"
  chmod -x "$TMP/repo/scripts/check"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "an unexecutable scripts/check expected 2, got $code: $(cat "$TMP/err")"
  grep -q 'scripts/check' "$TMP/err" || fail "the refusal does not name scripts/check: $(cat "$TMP/err")"
  git -C "$TMP/repo" rm -q -f scripts/check
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "no scripts/check expected 2, got $code: $(cat "$TMP/err")"
  grep -q 'scripts/check' "$TMP/err" || fail "the refusal does not name scripts/check: $(cat "$TMP/err")"
}

# A row resolves against the catalog of the runner that starts the session: Orca runs the
# host's CLI, which takes the CLI's own model id, and Paseo takes Paseo's. The catalog here
# gives the two sources different ids for one Codex model, so only the runner decides which
# one comes out.
scenario_catalogbyrunner() {
  local code catalog="$TMP/catalog-by-source.json"
  python3 - "$MMW_HOST_CATALOG" "$catalog" <<'PY'
import json, sys
paseo = json.load(open(sys.argv[1]))
cli = dict(paseo)
cli["codex"] = [{"id": "gpt-5.6-sol-cli", "name": "GPT-5.6-Sol", "thinkingOptionIds": ["high"]}]
json.dump({"cli": cli, "paseo": paseo}, open(sys.argv[2], "w"))
PY
  echo "--- on Orca the junior worker starts with the CLI's own model id"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_RUNNER=orca MMW_HOST_CATALOG="$catalog" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: create"
  grep -F "orca :: terminal :: create" "$MMW_TEST_LOG" | grep -qF -- "-m gpt-5.6-sol-cli" \
    || fail "the launch line should carry the CLI's id: $(grep -F 'orca :: terminal :: create' "$MMW_TEST_LOG")"
  posted_events 61 model | grep -qx "worker.started model=gpt-5.6-sol-cli" \
    || fail "the started event should record the id the session got: $(posted_events 61 model)"

  echo "--- on Paseo the same row starts with Paseo's id"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_RUNNER=paseo MMW_HOST_CATALOG="$catalog" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(out_json provider)" = "codex/gpt-5.6-sol" ] || fail "provider: $(out_json provider)"
}

scenario_advancerefused() {
  local code
  echo "--- a start the runner refuses is exit 4 from advance, naming the ticket and the reason"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\n\n#76\n", "title": "frontier ticket"}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_FAKE_PASEO_SCENARIO=run-fail \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 4 ] || fail "a refused start must not read as success, expected exit 4, got $code: $(cat "$TMP/err")"
  grep -q "started 0, refused 1" "$TMP/err" || fail "the tally should count the refusal: $(cat "$TMP/err")"
  [ "$(count_of "paseo :: run")" = 1 ] || fail "the refused start is tried once: $(count_of "paseo :: run") runs"
}

# Tickets outside any batch: what `land` was built for. #64 is finished, #65 was
# handed back, #66 is still being worked, #67 closed with its branch unmerged.
write_landable() {
  local commit64="" commit67="" event64 event67
  commit64="$(git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-64 2>/dev/null)" || true
  commit67="$(git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-67 2>/dev/null)" || true
  event64="$(ev ticket.passed 64 "ALL MET" --field branch=issue-64 --field into=main ${commit64:+--field "commit=$commit64"})"
  event67="$(ev ticket.passed 67 "ALL MET" --field branch=issue-67 --field into=main ${commit67:+--field "commit=$commit67"})"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 64, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T01:00:00Z",
   "assignees": ["mmw-bot"], "parent": null,
   "comments": ["reverify\\nALL MET (1 met)", $event64]},
  {"number": 65, "state": "OPEN", "labels": ["needs-triage"], "parent": null,
   "assignees": ["mmw-bot"],
   "comments": [$(ev ticket.returned 65 "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1")]},
  {"number": 66, "state": "OPEN", "labels": ["ready-for-agent"], "parent": null,
   "assignees": ["mmw-bot"], "comments": ["self-run\\nUNMET: 1 (met: 0)"]},
  {"number": 67, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T02:00:00Z",
   "parent": null, "comments": [$event67]},
  {"number": 68, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T03:00:00Z",
   "parent": null, "comments": [$(ev worker.started 68 "started" --field session=s68 --field runner=paseo \
     $(start_facts "$(wt 68)" 68 worker)), "voided: superseded by the spec"]},
  {"number": 69, "state": "OPEN", "labels": ["needs-triage"], "parent": null,
   "assignees": [], "comments": [$(ev ticket.returned 69 "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1")]}
]
JSON
}

scenario_land() {
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  reset_log
  fresh_repo
  make_branch issue-64 four.txt "from 64"
  git -C "$TMP/repo" push -q -u origin issue-64
  make_branch issue-67 seven.txt "from 67"
  write_landable
  seed_workspace 64
  seed_workspace 65
  seed_workspace 66
  local code

  echo "--- landing one finished ticket merges it, then removes its worktree"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:four.txt >/dev/null || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_no_branch 64
  hasnt_runner_worktree

  echo "--- and gives the claim back, which closing a ticket before this did not"
  has "gh :: issue :: edit :: 64 :: --remove-assignee :: @me"

  echo "--- both are events on the ticket, the landing recorded last, once the workspace is gone"
  [ "$(posted_events 64 branch reason | tr '\n' '|')" = "ticket.released branch=None reason=landed|ticket.landed branch=issue-64 reason=None|" ] \
    || fail "the land events are wrong: $(posted_events 64 branch reason)"

  echo "--- it takes a ticket number, never a spec: no batch was read"
  hasnt "sub_issues"

  echo "--- a ticket still being worked is held, and nothing is done to it"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 66)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt_runner_worktree
  hasnt "gh :: issue :: edit :: 66"

  echo "--- a ticket handed back keeps its worktree for the next start, and gives the claim back"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 65)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 65 :: --remove-assignee :: @me"
  assert_wt 65
  hasnt_runner_worktree

  echo "--- a closed ticket's passed commit is merged before its workspace is archived"
  reset_log
  seed_workspace 67
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 67)"
  git -C "$TMP/origin.git" show main:seven.txt >/dev/null \
    || fail "issue-67 should have been merged first"
  assert_no_wt 67
  assert_no_branch 67
  hasnt_runner_worktree

  echo "--- a ticket that needs nothing says so, rather than exiting 0 in silence"
  reset_log
  fresh_repo
  write_landable
  seed_workspace 69
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 69)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt_runner_worktree
  hasnt "gh :: issue :: edit :: 69"
  grep -q "#69" "$TMP/err" \
    || fail "a ticket needing nothing must be named, or it reads like one the plan forgot: $(cat "$TMP/err")"
  grep -q "already landed 1" "$TMP/err" \
    || fail "the tally should count it: $(cat "$TMP/err")"

  echo "--- a voided ticket is never merged, and so is never archived either"
  reset_log
  fresh_repo
  write_landable
  make_branch issue-68 eight.txt "from 68"
  seed_workspace 68
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 68)"
  [ "$code" = 1 ] || fail "expected exit 1 for a closed branch left unmerged, got $code: $(cat "$TMP/err")"
  ! git -C "$TMP/origin.git" cat-file -e main:eight.txt 2>/dev/null \
    || fail "a ticket that did not close ALL MET must not be merged"
  assert_wt 68
  hasnt_runner_worktree
}

scenario_advance() {
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  write_batch
  seed_workspace 61
  seed_workspace 62
  seed_foreign_workspace
  local code main_head
  main_head="$(git -C "$TMP/repo" rev-parse HEAD)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- both finished commits land on origin/main without moving the caller checkout"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:one.txt >/dev/null || fail "issue-61 was not merged"
  git -C "$TMP/origin.git" show main:two.txt >/dev/null || fail "issue-62 was not merged"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$main_head" ] || fail "the caller checkout moved"

  echo "--- in the order the tickets closed, each keeping a merge commit of its own"
  [ "$(git -C "$TMP/origin.git" log main --merges --first-parent --format='%s')" = "Merge branch 'issue-62'
Merge branch 'issue-61'" ] || fail "merge order is wrong"

  echo "--- a worktree is removed only after its branch is merged, then the frontier is created"
  assert_no_wt 61
  assert_no_wt 62
  assert_no_branch 61
  assert_no_branch 62
  assert_wt 63
  [ "$(git -C "$(wt 63)" rev-parse --abbrev-ref HEAD)" = issue-63 ] \
    || fail "frontier worktree should be on issue-63"
  hasnt_runner_worktree
  started_once
  assert_started || fail "the dispatched JSON is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#63 worker" ] || fail "title: $(out_json title)"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert obj["cwd"].endswith("/.worktrees/issue-63"), obj["cwd"]
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "the session must start in the ticket worktree"
  grep -q "advance #76:" "$TMP/err" || fail "the summary line should be on stderr: $(cat "$TMP/err")"

  echo "--- each merge is recorded on its ticket as ticket.landed"
  posted_events 61 branch | grep -qx "ticket.landed branch=issue-61" \
    || fail "#61 carries no ticket.landed: $(posted_events 61 branch)"
  posted_events 62 branch | grep -qx "ticket.landed branch=issue-62" \
    || fail "#62 carries no ticket.landed: $(posted_events 62 branch)"

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
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called for advance --json"
}

scenario_advancecap() {
  reset_log
  fresh_repo
  make_branch issue-61 held.txt held
  seed_workspace 61
  local code base held_event passed_event
  base="$(git -C "$TMP/repo" rev-parse main)"
  held_event="$(ev worker.started 61 'worker started' --field session=agt_61 --field runner=paseo \
    $(start_facts "$(wt 61)" 61 worker) --field "base=$base" --field into=main)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number":61,"state":"OPEN","labels":["ready-for-agent"],"comments":[$held_event]},
  {"number":64,"state":"OPEN","labels":["ready-for-agent"],"body":"## Parent\n\n#76\n"},
  {"number":62,"state":"OPEN","labels":["ready-for-agent"],"body":"## Parent\n\n#76\n"},
  {"number":63,"state":"OPEN","labels":["ready-for-agent"],"body":"## Parent\n\n#76\n"}
]
JSON
  cp "$MMW_HOME/models.json" "$TMP/models-before-cap.json"
  python3 - "$MMW_HOME/models.json" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
config = json.loads(path.read_text())
config["max_workers"] = 2
path.write_text(json.dumps(config))
PY
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "capped advance expected 0, got $code: $(cat "$TMP/err")"
  started_once
  [ "$(out_json title)" = '#62 worker' ] || fail "the smallest ready ticket did not start"
  grep -q 'started 1' "$TMP/err" || fail "advance did not report one start"
  for number in 63 64; do
    python3 - "$TMP/err" "$number" <<'PY'
import re, sys
from pathlib import Path
lines = Path(sys.argv[1]).read_text().splitlines()
assert any(f"#{sys.argv[2]}" in line and "max_workers" in line
           and re.search(r"\b2\b", line) and "#61" in line for line in lines), lines
PY
    [ "$?" = 0 ] || fail "waiting #$number does not name the cap and held #61"
  done
  assert_no_wt 63
  assert_no_wt 64

  passed_event="$(ev ticket.passed 61 'ALL MET' --field branch=issue-61 \
    --field "commit=$(git -C "$TMP/repo" rev-parse issue-61)" --field into=main)"
  MMW_PASS_EVENT="$passed_event" python3 - "$TMP/tickets.json" <<'PY'
import json, os, sys
from pathlib import Path
path = Path(sys.argv[1])
rows = json.loads(path.read_text())
for row in rows:
    if row["number"] == 61:
        row.update(state="CLOSED", labels=[], closedAt="2026-09-11T01:00:00Z")
        row["comments"].append(json.loads(os.environ["MMW_PASS_EVENT"]))
path.write_text(json.dumps(rows))
PY
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance after a pass expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:held.txt >/dev/null || fail "held #61 did not land"
  posted_events 61 | grep -q '^ticket.landed' || fail "#61 has no landed event"
  started_once
  [ "$(out_json title)" = '#63 worker' ] || fail "the next ticket did not start after landing"
  grep -q 'started 1' "$TMP/err" || fail "advance after landing did not report one start"
  assert_no_wt 64
  cp "$TMP/models-before-cap.json" "$MMW_HOME/models.json"
}

scenario_advancecapbadconfig() {
  reset_log
  fresh_repo
  make_branch issue-61 capped-pass.txt passed
  local code passed_event claim_event released_event
  passed_event="$(ev ticket.passed 61 'ALL MET' --field branch=issue-61 \
    --field "commit=$(git -C "$TMP/repo" rev-parse issue-61)" --field into=main)"
  claim_event="$(ev ticket.claimed 62 'Claimed #62' --field login=mmw-bot)"
  released_event="$(ev ticket.released 62 'Released #62' --field reason=worker-lost)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number":61,"state":"CLOSED","labels":[],"closedAt":"2026-09-11T01:00:00Z","comments":[$passed_event]},
  {"number":62,"state":"OPEN","labels":["ready-for-agent"],"assignees":["mmw-bot"],"comments":[$claim_event,$released_event],"body":"## Parent\n\n#76\n"},
  {"number":63,"state":"OPEN","labels":["ready-for-agent"],"body":"## Parent\n\n#76\n"}
]
JSON
  cp "$MMW_HOME/models.json" "$TMP/models-before-cap.json"
  python3 - "$MMW_HOME/models.json" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
config = json.loads(path.read_text())
config["max_workers"] = 0
path.write_text(json.dumps(config))
PY
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "advance with bad max_workers expected 2, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:capped-pass.txt >/dev/null || fail "passed #61 did not land"
  posted_events 61 | grep -q '^ticket.landed' || fail "#61 has no landed event"
  posted_events 62 | grep -q '^ticket.released' || fail "#62's ended claim was not given back"
  never_ran
  assert_no_wt 62
  assert_no_wt 63
  grep -q 'started 0' "$TMP/err" || fail "advance did not report no starts"
  grep -q -F 'models.py config set max_workers <n>' "$TMP/err" \
    || fail "advance did not carry the plan's correction command"
  cp "$TMP/models-before-cap.json" "$MMW_HOME/models.json"
}

scenario_advancedirty() {
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "from 61"
  local passed
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  printf 'unfinished\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared
  printf 'edited\n' > "$TMP/repo/shared.txt"

  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"

  echo "--- tracked edits in the caller checkout are outside the detached merge worktree"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  [ "$(cat "$TMP/repo/shared.txt")" = edited ] || fail "the caller's edit was changed"
  git -C "$TMP/origin.git" show main:one.txt >/dev/null || fail "the ticket was not merged"
}

seed_worker_started_for_integration() {
  local base="$1"
  post_ev 61 worker.started --ticket 61 --spec 76 --line "worker started" \
    --field session=agt_worker --field runner=paseo \
    $(start_facts "$TMP/repo" 61 worker) --field "base=$base" --field into=main
}

start_integrate_ticket() {
  local base
  base="$(git -C "$TMP/repo" rev-parse main)"
  git -C "$TMP/repo" checkout -q -b issue-61 main
  seed_worker_started_for_integration "$base"
}

merge_sibling_to_origin() {
  local number="$1" file="$2" value="$3" title="$4" clean_file="${5:-}" clean_value="${6:-}" other
  other="$(other_clone)"
  git -C "$other" checkout -q main
  git -C "$other" pull -q --ff-only origin main
  git -C "$other" checkout -q -b "issue-$number" main
  printf '%s\n' "$value" > "$other/$file"
  git -C "$other" add "$file"
  if [ -n "$clean_file" ]; then
    printf '%s\n' "$clean_value" > "$other/$clean_file"
    git -C "$other" add "$clean_file"
  fi
  git -C "$other" -c user.email=t@t -c user.name=t commit -q -m "ticket $number"
  git -C "$other" checkout -q main
  git -C "$other" merge -q --no-ff "issue-$number" -m "Merge branch 'issue-$number'"
  git -C "$other" push -q origin main
  FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_NUMBER="$number" MMW_TITLE="$title" python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["FAKE_GH_TICKETS_FILE"])
rows = json.loads(path.read_text()) if path.is_file() else []
rows = [row for row in rows if row.get("number") != int(os.environ["MMW_NUMBER"])]
rows.append({"number": int(os.environ["MMW_NUMBER"]), "title": os.environ["MMW_TITLE"]})
path.write_text(json.dumps(rows))
'
}

scenario_integrateuptodate() {
  local before code
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  start_integrate_ticket
  commit_file "$TMP/repo" ticket.txt ticket ticket-work
  before="$(git -C "$TMP/repo" rev-parse HEAD)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61)"
  [ "$code" = 0 ] || fail "up-to-date integrate expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$before" ] \
    || fail "an up-to-date integrate moved HEAD"
}

scenario_integrateclean() {
  local code original parents
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  start_integrate_ticket
  commit_file "$TMP/repo" ticket.txt ticket ticket-work
  original="$(git -C "$TMP/repo" rev-parse HEAD)"
  merge_sibling_to_origin 62 sibling.txt sibling "sibling feature"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61)"
  [ "$code" = 0 ] || fail "clean integrate expected 0, got $code: $(cat "$TMP/err")"
  [ -f "$TMP/repo/sibling.txt" ] || fail "origin/main was not merged into issue-61"
  [ "$(git -C "$TMP/repo" log -1 --format=%s)" = "Merge main into issue-61" ] \
    || fail "the integrate merge message is not fixed: $(git -C "$TMP/repo" log -1 --format=%s)"
  parents="$(git -C "$TMP/repo" show -s --format='%P' HEAD)"
  [ "$(printf '%s\n' "$parents" | wc -w | tr -d ' ')" = 2 ] \
    || fail "integrate did not create a two-parent merge commit: $parents"
  [ "${parents%% *}" = "$original" ] \
    || fail "the ticket commit is not the merge's first parent: $parents"
  [ "${parents#* }" = "$(git -C "$TMP/repo" rev-parse origin/main)" ] \
    || fail "origin/main is not the merge's second parent: $parents"
  git -C "$TMP/repo" merge-base --is-ancestor "$original" HEAD \
    || fail "the ticket's original commit left its history"
}

scenario_integratenamestickets() {
  local code
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  merge_sibling_to_origin 60 earlier.txt earlier "earlier ticket"
  git -C "$TMP/repo" pull -q --ff-only origin main
  start_integrate_ticket
  merge_sibling_to_origin 62 first.txt first "first sibling"
  merge_sibling_to_origin 63 second.txt second "second sibling"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61)"
  [ "$code" = 0 ] || fail "named integrate expected 0, got $code: $(cat "$TMP/err")"
  grep -q "#62" "$TMP/out" || fail "clean result did not name #62: $(cat "$TMP/out")"
  grep -q "#63" "$TMP/out" || fail "clean result did not name #63: $(cat "$TMP/out")"
  ! grep -q "#60" "$TMP/out" || fail "clean result named #60, landed before the worker started: $(cat "$TMP/out")"
}

scenario_integratedsincestart() {
  local code
  echo "--- integrated lists every ticket the base branch took in since this ticket's worker started, not one landed before it"
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  merge_sibling_to_origin 60 earlier.txt earlier "earlier ticket"
  git -C "$TMP/repo" pull -q --ff-only origin main
  start_integrate_ticket
  merge_sibling_to_origin 62 first.txt first "first sibling"
  merge_sibling_to_origin 63 second.txt second "second sibling"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrated 61)"
  [ "$code" = 0 ] || fail "integrated expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = "$(printf '62\n63\n')" ] \
    || fail "integrated should list #62 and #63, not #60 (landed before #61's worker started): $(cat "$TMP/out")"

  echo "--- a ticket with no recorded worker.started.base is refused, nothing printed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrated 99)"
  [ "$code" = 2 ] || fail "a ticket with no worker.started.base should refuse, got $code: $(cat "$TMP/err")"
  [ ! -s "$TMP/out" ] || fail "nothing should be printed on refusal: $(cat "$TMP/out")"
}

scenario_integrateconflict() {
  local code
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  printf 'base\n' > "$TMP/repo/shared.txt"
  git -C "$TMP/repo" add shared.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m shared-base
  git -C "$TMP/repo" push -q origin main
  start_integrate_ticket
  commit_file "$TMP/repo" shared.txt ticket ticket-change
  merge_sibling_to_origin 62 shared.txt sibling "conflicting sibling" clean.txt clean
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61)"
  [ "$code" = 3 ] || fail "conflicting integrate expected 3, got $code: $(cat "$TMP/err")"
  git -C "$TMP/repo" rev-parse -q --verify MERGE_HEAD >/dev/null \
    || fail "integrate aborted the conflicted merge"
  grep -q "#62" "$TMP/err" || fail "the report omitted #62: $(cat "$TMP/err")"
  grep -q "conflicting sibling" "$TMP/err" \
    || fail "the report omitted #62's title: $(cat "$TMP/err")"
  grep -q "shared.txt" "$TMP/err" \
    || fail "the report omitted the conflicted file: $(cat "$TMP/err")"
}

scenario_integratedirty() {
  local cached code head status
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  commit_file "$TMP/repo" tracked.txt original tracked-base
  git -C "$TMP/repo" push -q origin main
  start_integrate_ticket
  cached="$(git -C "$TMP/repo" rev-parse origin/main)"
  merge_sibling_to_origin 62 sibling.txt sibling "sibling feature"
  printf 'dirty\n' > "$TMP/repo/tracked.txt"
  head="$(git -C "$TMP/repo" rev-parse HEAD)"
  status="$(git -C "$TMP/repo" status --porcelain --untracked-files=no)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61)"
  [ "$code" = 2 ] || fail "dirty integrate expected 2, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$head" ] || fail "dirty integrate moved HEAD"
  [ "$(git -C "$TMP/repo" rev-parse origin/main)" = "$cached" ] \
    || fail "dirty integrate fetched origin before refusing"
  [ "$(git -C "$TMP/repo" status --porcelain --untracked-files=no)" = "$status" ] \
    || fail "dirty integrate changed the index or working tree"
  [ "$(cat "$TMP/repo/tracked.txt")" = dirty ] || fail "dirty integrate changed the tracked file"
}

put_env() {
  mkdir -p "$TMP/repo/scripts"
  cat > "$TMP/repo/scripts/env" <<'ENV'
#!/usr/bin/env bash
printf 'env :: %s :: %s :: %s\n' "$1" "$2" "$PWD" >> "$MMW_TEST_LOG"
if [ "$1" = "${MMW_TEST_ENV_FAIL:-}" ]; then
  echo "fixture environment failure for $1" >&2
  exit 7
fi
case "$1" in
  setup) touch "$2/.setup-ready" ;;
  up)
    [ -f "$2/.setup-ready" ] || exit 8
    touch "$2/.env-ready"
    echo "test-resource-$(basename "$2")" ;;
  down) rm -f "$2/.env-ready" ;;
esac
ENV
  chmod +x "$TMP/repo/scripts/env"
  printf '.setup-ready\n.env-ready\n' >> "$TMP/repo/.gitignore"
  git -C "$TMP/repo" add scripts/env .gitignore
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm 'repository environment'
  git -C "$TMP/repo" push -q origin main
}

scenario_envstartsetsup() {
  reset_log
  fresh_repo
  put_env
  local code tree
  tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/issue-61"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  [ "$(grep '^env ::' "$MMW_TEST_LOG")" = "$(printf 'env :: setup :: %s :: %s\nenv :: up :: %s :: %s' "$tree" "$tree" "$tree" "$tree")" ] \
    || fail "setup and up should run in the target checkout: $(cat "$MMW_TEST_LOG")"
  [ -f "$tree/.env-ready" ] || fail 'the worker environment is missing'
  [ "$(line_of '^env :: up')" -lt "$(line_of 'paseo :: run')" ] \
    || fail 'the environment should be ready before the worker starts'
  assert_started || fail "environment output changed the session id: $(cat "$TMP/out")"
}

scenario_envupfails() {
  local step code tree
  for step in setup up; do
    reset_log
    fresh_repo
    put_env
    tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/issue-61"
    code="$(run_dispatch env MMW_TEST_ENV_FAIL="$step" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
    [ "$code" = 2 ] || fail "$step failure expected 2, got $code: $(cat "$TMP/err")"
    grep -qF "scripts/env $step" "$TMP/err" || fail "the failing step is missing"
    grep -qF "$tree" "$TMP/err" || fail "the failing worktree is missing"
    grep -qF "fixture environment failure for $step" "$TMP/err" || fail "the script output is missing"
    never_ran
    [ "$step" != setup ] || hasnt "env :: up"

    reset_log
    fresh_repo
    put_env
    make_branch issue-61 ticket.txt ticket
    git -C "$TMP/repo" push -q origin issue-61
    write_one_passed 61 "$(git -C "$TMP/repo" rev-parse issue-61)"
    tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/merge-main"
    code="$(run_dispatch env MMW_TEST_ENV_FAIL="$step" FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
            bash "$DISPATCH" "${TOOLS[@]}" land 61)"
    [ "$code" = 2 ] || fail "merge $step failure expected 2, got $code: $(cat "$TMP/err")"
    grep -qF "scripts/env $step" "$TMP/err" || fail "the failing merge step is missing"
    grep -qF "$tree" "$TMP/err" || fail "the failing merge worktree is missing"
    has "env :: down :: $tree :: $tree"
    hasnt 'ticket.landed'
    if git -C "$TMP/origin.git" show main:ticket.txt >/dev/null 2>&1; then
      fail 'environment failure still landed the ticket'
    fi
  done

  reset_log
  fresh_repo
  put_env
  put_check "$TMP/repo" 'exit 2'
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm 'unrunnable repository check'
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q origin issue-61
  write_one_passed 61 "$(git -C "$TMP/repo" rev-parse issue-61)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 1 ] || fail "a repository-check failure must retain land's exit 1, got $code: $(cat "$TMP/err")"
  hasnt 'ticket.landed'
}

scenario_envdownonend() {
  local code tree
  reset_log
  fresh_repo
  put_env
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q origin issue-61
  seed_workspace 61
  tree="$(cd "$(wt 61)" && pwd -P)"
  write_one_passed 61 "$(git -C "$tree" rev-parse HEAD)"
  code="$(run_dispatch env MMW_TEST_ENV_FAIL=down FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "cleanup failure should not block land: $(cat "$TMP/err")"
  has "env :: down :: $tree :: $tree"
  grep -qF 'fixture environment failure for down' "$TMP/err" || fail 'cleanup failure was not reported'
  assert_no_wt 61
  git -C "$TMP/origin.git" show main:ticket.txt >/dev/null || fail 'the ticket was not landed'

  reset_log
  fresh_repo
  put_env
  write_open_batch
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start before suspend failed: $(cat "$TMP/err")"
  tree="$(cd "$(wt 61)" && pwd -P)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "suspend failed: $(cat "$TMP/err")"
  has "env :: down :: $tree :: $tree"
  [ ! -f "$tree/.env-ready" ] || fail 'suspend left the resources running'
  assert_wt 61

  reset_log
  fresh_repo
  put_env
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start before retract failed: $(cat "$TMP/err")"
  tree="$(cd "$(wt 61)" && pwd -P)"
  set_agent_status "$(cat "$TMP/out")" closed
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract failed: $(cat "$TMP/err")"
  has "env :: down :: $tree :: $tree"
  assert_no_wt 61
}

scenario_envmergeworktree() {
  reset_log
  fresh_repo
  put_env
  put_check "$TMP/repo" 'test -f .env-ready || exit 1
printf "merge-check :: %s\\n" "$PWD" >> "$MMW_TEST_LOG"'
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm 'check requires environment'
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q origin issue-61
  seed_workspace 61
  write_one_passed 61 "$(git -C "$(wt 61)" rev-parse HEAD)"
  local code tree orphan
  tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/merge-main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "land failed: $(cat "$TMP/err")"
  has "env :: setup :: $tree :: $tree"
  has "env :: up :: $tree :: $tree"
  has "merge-check :: $tree"
  [ "$(line_of '^env :: setup')" -lt "$(line_of '^env :: up')" ] || fail 'setup must precede up'
  [ "$(line_of '^env :: up')" -lt "$(line_of '^merge-check')" ] || fail 'up must precede merge checks'
  git -C "$TMP/origin.git" show main:ticket.txt >/dev/null || fail 'merge checks did not allow landing'

  printf '[]\n' > "$TMP/tickets.json"
  open_night
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "reverify preparation failed: $(cat "$TMP/err")"
  [ "$(grep '^env ::' "$MMW_TEST_LOG")" = "$(printf 'env :: setup :: %s :: %s\nenv :: up :: %s :: %s' "$tree" "$tree" "$tree" "$tree")" ] \
    || fail "reverify should prepare its detached merge worktree: $(cat "$MMW_TEST_LOG")"

  orphan="$(cd "$TMP/repo" && pwd -P)/.worktrees/merge-retired"
  git -C "$TMP/repo" worktree add -q --detach "$orphan" origin/main
  printf '[]\n' > "$TMP/tickets.json"
  code="$(run_dispatch env MMW_TEST_ENV_FAIL=down FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "orphan cleanup failed: $(cat "$TMP/err")"
  has "env :: down :: $orphan :: $orphan"
  [ ! -d "$orphan" ] || fail 'the orphan merge worktree was not removed'
  grep -qF 'fixture environment failure for down' "$TMP/err" || fail 'merge cleanup failure was hidden'

  setup_finish_closed
  put_env
  git -C "$TMP/repo" push -q origin proj
  tree="$(cd "$TMP/repo" && pwd -P)/.worktrees/merge-night"
  git -C "$TMP/repo" worktree add -q --detach "$tree" origin/proj
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish cleanup failed: $(cat "$TMP/err")"
  has "env :: down :: $tree :: $tree"
  [ ! -d "$tree" ] || fail 'finish left the base merge worktree'
}

scenario_envrestartaftersuspend() {
  reset_log
  fresh_repo
  put_env
  write_open_batch
  local code tree head
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "first start failed: $(cat "$TMP/err")"
  tree="$(cd "$(wt 61)" && pwd -P)"
  head="$(git -C "$tree" rev-parse HEAD)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "suspend failed: $(cat "$TMP/err")"
  fake_relay
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "restart failed: $(cat "$TMP/err")"
  [ "$(grep '^env ::' "$MMW_TEST_LOG")" = "$(printf 'env :: setup :: %s :: %s\nenv :: up :: %s :: %s' "$tree" "$tree" "$tree" "$tree")" ] \
    || fail "the standing worktree needs setup and up again: $(cat "$MMW_TEST_LOG")"
  [ -f "$tree/.env-ready" ] || fail 'restart did not restore the environment'
  [ "$(git -C "$tree" rev-parse HEAD)" = "$head" ] || fail 'restart changed the ticket work'
}

scenario_envabsent() {
  reset_log
  fresh_repo
  local code passed
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start without env failed: $(cat "$TMP/err")"
  assert_started || fail 'start output changed'
  ! grep -q 'scripts/env' "$TMP/out" "$TMP/err" || fail 'start without env should be silent'
  passed="$(git -C "$(wt 61)" rev-parse HEAD)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "land without env failed: $(cat "$TMP/err")"
  ! grep -q 'scripts/env' "$TMP/out" "$TMP/err" || fail 'absent env should be silent'
  assert_no_wt 61
}

scenario_start_worker() {
  local code
  echo "--- a ticket with no worker label starts one session on the default row and prints its id"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  assert_started || fail "the JSON line is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#61 worker" ] || fail "title: $(out_json title)"
  [ "$(out_json provider)" = "$JUNIOR_HOST/$JUNIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(posted_events 61 spec | grep '^worker.started')" = "worker.started spec=76" ] \
    || fail "the worker.started event should name spec 76: $(posted_events 61 spec)"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert obj["settings"].get("thinkingOptionId") == "high", obj["settings"]
assert obj["settings"].get("modeId") == "full-access", obj["settings"]
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "paseo run settings changed: $(cat "$TMP/out")"
  case "$(out_json initialPrompt)" in
    "Dispatched: worker, ticket #61, base "????????????????????????????????????????". Read the mmw-mode skill in full, then follow the mmw-mode skill's playbooks/work-a-ticket.md. It is your whole task: what came before it is done, and you start no agent it does not name.") ;;
    *) fail "the worker's prompt should be its dispatch line and what it follows: $(out_json initialPrompt)" ;;
  esac
  assert_wt 61
  [ "$(git -C "$(wt 61)" rev-parse --abbrev-ref HEAD)" = issue-61 ] \
    || fail "new worktree should be on issue-61"
  assert_branch 61
  hasnt_runner_worktree
  case "$(wt 61)" in
    */.worktrees/issue-61) ;;
    *) fail "worktree path must be <repo>/.worktrees/issue-n, got $(wt 61)" ;;
  esac
  case "$(wt 61)" in
    *paseo*|*orca*|*herdr*) fail "worktree path carries a runner name: $(wt 61)" ;;
  esac

  echo "--- an existing ticket branch is checked out, not cut again"
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "already there"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  assert_wt 61
  [ "$(git -C "$(wt 61)" rev-parse --abbrev-ref HEAD)" = issue-61 ] \
    || fail "existing branch should be checked out in the worktree"
  hasnt_runner_worktree

  echo "--- a senior-worker label starts that row instead"
  reset_log
  fresh_repo
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,senior-worker" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  [ "$(out_json provider)" = "claude/$SENIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(out_json settings.thinkingOptionId)" = xhigh ] || fail "effort: $(out_json settings.thinkingOptionId)"

  echo "--- two worker labels are refused, and nothing is started"
  reset_log
  code="$(run_dispatch env FAKE_GH_LABELS="ready-for-agent,junior-worker,senior-worker" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code"
  nothing_printed
  never_ran
  hasnt "workspace :: create"

  echo "--- a retired flag on start exits 2 and calls nothing"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker --json)"
  [ "$code" = 2 ] || fail "expected exit 2 for --json, got $code: $(cat "$TMP/err")"
  [ "$(count_of 'paseo ::')" = 0 ] || fail "paseo was called for start --json"
  [ "$(count_of 'gh ::')" = 0 ] || fail "gh was called for start --json"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker --run)"
  [ "$code" = 2 ] || fail "expected exit 2 for the retired flag, got $code: $(cat "$TMP/err")"


  echo "--- a start on a ticket whose worker is still live replaces it: stopped, worker.replaced, then worker.started"
  reset_log
  fresh_repo
  seed_agent 61 worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0 for a replacement, got $code: $(cat "$TMP/err")"
  has "paseo :: archive :: --force :: agt_61_worker"
  local new
  new="$(tail -n 1 "$TMP/out")"
  [ "$(posted_events 61 session runner by_session | tr '\n' '|')" = \
    "worker.started session=agt_61_worker runner=paseo by_session=None|worker.replaced session=agt_61_worker runner=paseo by_session=$new|worker.started session=$new runner=paseo by_session=None|" ] \
    || fail "replacement events: $(posted_events 61 session runner by_session)"
  [ "$(printf '%s' "$(gh_comments_json 61)" | python3 "$EVENTS_PY" live --kind worker --comments-file - 61)" = "paseo	$new" ] \
    || fail "after the replacement only the new worker is live: $(printf '%s' "$(gh_comments_json 61)" | python3 "$EVENTS_PY" live --kind worker --comments-file - 61)"

  echo "--- a live worker that will not stop is not replaced, and nothing is started beside it"
  reset_log
  fresh_repo
  seed_agent 61 worker
  code="$(run_dispatch env MMW_FAKE_PASEO_SCENARIO=archive-fail \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 when the live worker will not stop, got $code: $(cat "$TMP/err")"
  has "paseo :: archive :: --force :: agt_61_worker"
  never_ran
  [ "$(posted_events 61 | tr '\n' '|')" = "worker.started|" ] \
    || fail "nothing should be posted: $(posted_events 61)"

  echo "--- a copied skill still finds models.py"
  local copy
  copy="$(skill_copy_for start)"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "copied start expected exit 0, got $code: $(cat "$TMP/err")"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert obj["settings"].get("thinkingOptionId") == "high"
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "copied start settings are wrong: $(cat "$TMP/out")"
}

scenario_retract() {
  local code
  echo "--- usage lists retract"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}")"
  [ "$code" = 2 ] || fail "expected exit 2 for usage, got $code: $(cat "$TMP/err")"

  echo "--- retract after start removes the worktree and gives the claim back"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"]}]
JSON
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_branch 61
  hasnt_runner_worktree
  grep -q "retract #61: archived 1, claim given back 1" "$TMP/err" \
    || fail "the counters should match what was undone: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"

  echo "--- a second retract on the same ticket is a no-op"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "second retract expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "workspace :: archive"
  grep -q "retract #61: archived 0, claim given back 0" "$TMP/err" \
    || fail "a second retract should report zeros: $(cat "$TMP/err")"

  echo "--- a live agent on the ticket is refused, and the workspace stays"
  reset_log
  fresh_repo
  seed_workspace 61
  seed_agent 61 worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2 with a live agent, got $code: $(cat "$TMP/err")"
  hasnt "workspace :: archive"

  echo "--- a claim this pipeline does not hold is left alone"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["a-human"]}]
JSON
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  grep -q "claim given back 0" "$TMP/err" \
    || fail "someone else's claim must stay: $(cat "$TMP/err")"

}

scenario_start_reviewer() {
  local base code
  echo "--- a reviewer uses worker.started.base when the base branch was never integrated"
  reset_log
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  base="$(git -C "$TMP/repo" rev-parse main)"
  seed_worker_started_for_integration "$base"
  seed_workspace 61
  merge_sibling_to_origin 62 sibling.txt sibling "not integrated"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  [ "$(out_json title)" = "#61 reviewer" ] || fail "title: $(out_json title)"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert obj["provider"] == "claude/claude-opus-5", obj["provider"]
assert obj["settings"].get("thinkingOptionId") == "high"
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "reviewer payload: $(cat "$TMP/out")"
  [ "$(out_json initialPrompt)" = "Dispatched: reviewer, ticket #61, base $base. Read the mmw-mode skill in full, then follow the code-review skill's references/session.md. It is your whole task: what came before it is done, and you start no agent it does not name." ] \
    || fail "the reviewer dispatch line did not carry the recorded base commit: $(out_json initialPrompt)"
}

scenario_reviewerbaseafterintegrate() {
  local base code integrated tree
  reset_log
  fresh_repo
  echo '[]' > "$TMP/tickets.json"
  base="$(git -C "$TMP/repo" rev-parse main)"
  seed_worker_started_for_integration "$base"
  seed_workspace 61
  tree="$(wt 61)"
  merge_sibling_to_origin 62 sibling.txt sibling "sibling feature"
  code="$( (cd "$tree" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" integrate 61) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 0 ] || fail "integrate before reviewer expected 0, got $code: $(cat "$TMP/err")"
  integrated="$(git -C "$TMP/origin.git" rev-parse main)"
  : > "$MMW_TEST_LOG"
  rm -f "$MMW_FAKE_PASEO_STATE/runs.jsonl"
  code="$( (cd "$tree" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 0 ] || fail "replacement worker after integrate expected 0, got $code: $(cat "$TMP/err")"
  [ "$(posted_events 61 base | tail -n 1)" = "worker.started base=$base" ] \
    || fail "replacement worker moved worker.started.base: $(posted_events 61 base)"
  merge_sibling_to_origin 63 later.txt later "landed after integration"
  : > "$MMW_TEST_LOG"
  rm -f "$MMW_FAKE_PASEO_STATE/runs.jsonl"
  code="$( (cd "$tree" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 0 ] || fail "reviewer after integrate expected 0, got $code: $(cat "$TMP/err")"
  [ "$(out_json initialPrompt)" = "Dispatched: reviewer, ticket #61, base $integrated. Read the mmw-mode skill in full, then follow the code-review skill's references/session.md. It is your whole task: what came before it is done, and you start no agent it does not name." ] \
    || fail "reviewer did not use the integrated origin/main tip: $(out_json initialPrompt)"
}

# The batch directory of the newest batch `brief` made, or nothing.
newest_batch() {
  ls -1 "$STATE_DIR/briefs" 2>/dev/null | tail -n 1
}

# What the relay keeps for the watch <key>: "runner session", or nothing.
brief_watch() { watch_main "$1"; }

scenario_briefclosebrowsers() {
  local code packet batch n
  packet="$TMP/browser-close.md"
  echo 'Read the vendor page.' > "$packet"
  reset_log
  fresh_repo
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$packet")"
  [ "$code" = 0 ] || fail "send expected 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" brief close "$batch")"
  [ "$code" = 0 ] || fail "brief close expected 0, got $code: $(cat "$TMP/err")"
  for n in 1 2; do
    [ "$(count_of "playwright-cli :: -s=mmw-$batch-$n :: close")" = 1 ] \
      || fail "brief close did not close browser session $n exactly once"
  done
  hasnt 'close-all'
  hasnt 'kill-all'
}

scenario_briefclosekillsleftover() {
  local code packet batch other
  packet="$TMP/browser-leftover.md"
  echo 'Read the vendor page.' > "$packet"
  reset_log
  fresh_repo
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet")"
  [ "$code" = 0 ] || fail "send expected 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  other="mmw-19990101-000000-abcd-1"
  playwright-cli "-s=mmw-$batch-1" open
  playwright-cli "-s=$other" open
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" brief close "$batch")"
  [ "$code" = 0 ] || fail "brief close expected 0, got $code: $(cat "$TMP/err")"
  python3 - "$MMW_FAKE_PASEO_STATE/browser-pids" <<'PY' || fail "batch browser process isolation failed"
import subprocess, sys
from pathlib import Path

rows = [list(map(int, row.split())) for row in Path(sys.argv[1]).read_text().splitlines()]
assert len(rows) == 2, rows
def alive(pid):
    p = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True)
    return p.returncode == 0 and p.stdout.strip() and not p.stdout.strip().startswith('Z')
assert not any(alive(pid) for pid in rows[0]), f'closed batch processes survived: {rows[0]}'
assert all(alive(pid) for pid in rows[1]), f'other session was stopped: {rows[1]}'
PY
}

scenario_briefbrowsername() {
  local code packet batch n
  packet="$TMP/browser-brief.md"
  printf '%s\n' '## Task' 'Read the vendor page.' '## Known' 'It requires JavaScript.' '## For' 'A source check.' > "$packet"
  reset_log
  fresh_repo
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$packet")"
  [ "$code" = 0 ] || fail "send researcher expected 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  for n in 1 2; do
    grep -qF "playwright-cli -s=mmw-$batch-$n" "$STATE_DIR/briefs/$batch/$n/brief.md" \
      || fail "researcher $n was not given its named browser session"
  done
}

scenario_sendrefusesclosedbatch() {
  local code packet batch pointer valid expected
  packet="$TMP/previous-answer.md"
  echo 'Answer the question.' > "$packet"
  reset_log
  fresh_repo
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$packet")"
  [ "$code" = 0 ] || fail "first send expected 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  pointer="$STATE_DIR/briefs/$batch/1/result.md"
  echo 'The previous answer.' > "$pointer"
  printf '%s\n' '## Task' 'Continue the investigation.' '## Known' "Read [the previous answer]($pointer)." '## For' 'A decision.' > "$packet"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$packet")"
  [ "$code" = 0 ] || fail "reference to an open batch was refused: $(cat "$TMP/err")"
  cat "$packet" > "$TMP/repo/-notes.md"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" -notes.md)"
  [ "$code" = 0 ] || fail "reference to an open batch in -notes.md was refused: $(cat "$TMP/err")"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" brief close "$batch")"
  [ "$code" = 0 ] || fail "brief close expected 0, got $code: $(cat "$TMP/err")"
  valid="$TMP/valid-brief.md"
  echo 'Answer an independent question.' > "$valid"
  for pointer in "$pointer" "briefs/$batch/1/result.md" 'briefs/19990101-000000-abcd/1/result.md' \
      "$STATE_DIR/briefs/$batch:" "briefs/$batch;" "briefs/$batch]"; do
    expected="$batch"
    case "$pointer" in *19990101-000000-abcd*) expected=19990101-000000-abcd ;; esac
    printf '%s\n' '## Task' 'Continue the investigation.' '## Known' "Read $pointer." '## For' 'A decision.' > "$packet"
    : > "$MMW_TEST_LOG"
    code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$valid" "$packet")"
    [ "$code" = 2 ] || fail "dead batch reference expected 2, got $code: $(cat "$TMP/err")"
    hasnt 'paseo :: run'
    grep -qF '## Known' "$TMP/err" || fail "refusal does not explain how to preserve the answer"
    grep -qF "$expected" "$TMP/err" || fail "refusal does not name batch $expected"
  done
  cat "$packet" > "$TMP/repo/-notes.md"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" -notes.md)"
  [ "$code" = 2 ] || fail "dead batch reference in -notes.md expected 2, got $code: $(cat "$TMP/err")"
  hasnt 'paseo :: run'
  grep -qF -- '-notes.md' "$TMP/err" || fail "refusal does not name the leading-dash brief file"
  grep -qF "$batch" "$TMP/err" || fail "leading-dash brief refusal does not name batch $batch"
  grep -qF '## Known' "$TMP/err" || fail "leading-dash brief refusal does not explain how to preserve the answer"
}

scenario_briefproblems() {
  local code packet batch copy
  packet="$TMP/problem-brief.md"
  printf '%s\n' '## Task' 'Answer the question.' '## Known' 'The options are available.' '## For' 'A decision.' > "$packet"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$packet")"
  [ "$code" = 0 ] || fail "send advisor expected exit 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  copy="$STATE_DIR/briefs/$batch/1/brief.md"
  grep -q '## Problems' "$copy" || fail "the brief copy does not ask for a Problems section"
  [ "$rc" -ne 0 ] || echo 'the brief asks for a Problems section'
}

scenario_sendinto() {
  local code packet batch copy n branch dir
  packet="$TMP/research.txt"
  printf '%s\n' 'Compare the search options.' > "$packet"
  for branch in map-61 fix-61; do
    dir="efforts/$branch/research/61-search2-options/"
    reset_log
    fresh_repo
    git -C "$TMP/repo" checkout -qb "$branch"
    rm -rf "$STATE_DIR/briefs"
    seed_main_agent agt_main
    code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher \
      --follow "the research skill" --into "$dir" "$packet" "$packet")"
    [ "$code" = 0 ] || fail "send into expected 0, got $code: $(cat "$TMP/err")"
    [ -d "$TMP/repo/$dir" ] || fail "the question directory was not created"
    [ "$(count_of "paseo :: run")" = 2 ] || fail "expected two researcher sessions"
    batch="$(newest_batch)"
    for n in 1 2; do
      copy="$STATE_DIR/briefs/$batch/$n/brief.md"
      [ -f "$copy" ] || { fail "brief $n was not created"; continue; }
      grep -qF "write your whole answer to ${dir}brief-$n.md" "$copy" || fail "brief $n writes to the wrong answer path"
      grep -qF "${dir}brief-$n/" "$copy" || fail "brief $n lacks its evidence directory"
      grep -qF "report $batch/$n ${dir}brief-$n.md" "$copy" || fail "brief $n reports the wrong file"
    done
    [ "$(cut -f1 "$TMP/out" | tr '\n' ' ')" = "$batch/1 $batch/2 " ] || fail "batch output changed"
    [ "$(brief_watch "briefs:$batch")" = "paseo agt_main" ] || fail "batch wake recipient changed"
  done
  [ "$rc" -ne 0 ] || echo "each brief writes into its question directory"
}

scenario_sendintorefused() {
  local branch dir code packet="$TMP/research.txt"
  printf '%s\n' 'Compare the search options.' > "$packet"
  for branch in map-61 fix-61; do
    for dir in '' 'research/61-search' 'efforts/Notes/research/61-search/' \
      'efforts/notes/research/61-Search/' 'efforts/notes/research/issue-61-search/' \
      '/efforts/notes/research/61-search/' 'efforts/notes/research/61-search/../' \
      'efforts/notes_guide/research/61-search/' 'efforts/notes/research/61-search--options/'; do
      reset_log
      fresh_repo
      git -C "$TMP/repo" checkout -qb "$branch"
      rm -rf "$STATE_DIR/briefs"
      seed_main_agent agt_main
      local flags=()
      [ -z "$dir" ] || flags=(--into "$dir")
      code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher \
        --follow "the research skill" ${flags[@]+"${flags[@]}"} "$packet")"
      [ "$code" = 2 ] || fail "$branch with destination '$dir' expected 2, got $code"
      grep -qF -- '--into efforts/<effort>/research/<ticket number>-<slug>/' "$TMP/err" \
        || fail "refusal lacks the required directory shape: $(cat "$TMP/err")"
      never_ran
      nothing_printed
      [ -z "$(newest_batch)" ] || fail "a refused send created a batch"
      [ ! -e "$TMP/repo/efforts" ] || fail "a refused send created a directory"
    done
  done
  [ "$rc" -ne 0 ] || echo "send researcher on an effort branch without a question directory is refused"
}

scenario_sendintoreuse() {
  local code packet="$TMP/research.txt" dir="efforts/fix-61/research/61-search/" batch failure saved
  printf '%s\n' 'Compare the search options.' > "$packet"
  reset_log
  fresh_repo
  git -C "$TMP/repo" checkout -qb fix-61
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  mkdir -p "$TMP/repo/$dir"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher \
    --follow "the research skill" --into "$dir" "$packet")"
  [ "$code" = 0 ] || fail "an empty question directory expected 0, got $code: $(cat "$TMP/err")"
  started_once
  batch="$(newest_batch)"
  [ -n "$batch" ] || fail "reusing an empty directory made no batch"
  mkdir -p "$TMP/repo/${dir}brief-1"
  printf '%s\n' 'the original evidence' > "$TMP/repo/${dir}brief-1/source.txt"
  for saved in evidence answer; do
    if [ "$saved" = answer ]; then
      printf '%s\n' 'the original answer' > "$TMP/repo/${dir}brief-1.md"
    fi
    code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher \
      --follow "the research skill" --into "$dir" "$packet")"
    [ "$code" = 2 ] || fail "a second batch over saved $saved expected 2, got $code"
    [ "$(count_of "paseo :: run")" = 1 ] || fail "a second batch started over saved $saved"
    [ "$(cat "$TMP/repo/${dir}brief-1/source.txt")" = 'the original evidence' ] || fail "the kept evidence changed"
    grep -qF 'new <slug>' "$TMP/err" || fail "the $saved refusal does not name a new slug"
  done
  [ "$(cat "$TMP/repo/${dir}brief-1.md")" = 'the original answer' ] || fail "the kept answer changed"
  for failure in run-fail run-fail-after-one; do
    reset_log
    fresh_repo
    git -C "$TMP/repo" checkout -qb fix-61
    rm -rf "$STATE_DIR/briefs"
    seed_main_agent agt_main
    code="$(run_dispatch env PASEO_AGENT_ID=agt_main MMW_FAKE_PASEO_SCENARIO="$failure" \
      bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" \
      --into "$dir" "$packet" "$packet")"
    [ "$code" = 2 ] || fail "$failure expected 2, got $code"
    nothing_printed
    [ -d "$TMP/repo/$dir" ] || fail "$failure cleaned up the question directory"
    [ -z "$(newest_batch)" ] || fail "$failure left a batch"
    code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher \
      --follow "the research skill" --into "$dir" "$packet")"
    [ "$code" = 0 ] || fail "retry after $failure expected 0, got $code: $(cat "$TMP/err")"
  done
  [ "$rc" -ne 0 ] || echo "a question directory with an answer is refused and an empty one is reused"
}

scenario_installedrefusessend() {
  local code installed packet command
  fresh_repo
  reset_log
  installed="$TMP/repo/mmw-v4"
  mkdir -p "$installed/skills/dispatch"
  printf '%s\n' "$installed" > "$MMW_HOME/installed-root"
  packet="$TMP/installed-brief.txt"
  printf '%s\n' 'Investigate the product.' > "$packet"
  seed_main_agent agt_main
  code="$( (cd "$installed/skills/dispatch" && env PASEO_AGENT_ID=agt_main \
    bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet") \
    > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 2 ] || fail "send from the installed checkout expected 2, got $code: $(cat "$TMP/err")"
  grep -qF "$(git -C "$installed" rev-parse --show-toplevel)" "$TMP/err" \
    || fail "the refusal does not name the installed checkout: $(cat "$TMP/err")"
  never_ran
  nothing_printed
  [ -z "$(newest_batch)" ] || fail "the refused send created a brief batch"
  hasnt 'gh ::'

  for command in open open-ticket ack advance integrate integrated land start report retract wait resume reverify summary finish suspend route 'brief close'; do
    code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" $command 76)"
    [ "$code" = 2 ] || fail "$command from the installed checkout expected 2, got $code"
    grep -qF "$(git -C "$installed" rev-parse --show-toplevel)" "$TMP/err" \
      || fail "$command did not name the installed checkout: $(cat "$TMP/err")"
  done
  never_ran
  hasnt 'gh ::'
  rm -f "$MMW_HOME/installed-root"
}

scenario_installedallowsstatus() {
  local code
  fresh_repo
  reset_log
  write_open_batch
  mkdir -p "$TMP/repo/mmw-v4"
  printf '%s\n' "$TMP/repo/mmw-v4" > "$MMW_HOME/installed-root"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
    bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "status in the installed checkout expected 0, got $code: $(cat "$TMP/err")"
  grep -q 'spec #76' "$TMP/out" || fail "status did not print the spec table: $(cat "$TMP/out")"
  never_ran
  hasnt 'gh :: issue :: comment'
  rm -f "$MMW_HOME/installed-root"
}

scenario_installedothercheckoutsend() {
  local code installed packet
  fresh_repo
  reset_log
  installed="$TMP/installed checkout"
  git -C "$TMP/repo" worktree add -q --detach "$installed"
  mkdir -p "$installed/mmw-v4"
  printf '%s\n' "$installed/mmw-v4" > "$MMW_HOME/installed-root"
  packet="$TMP/other-checkout-brief.txt"
  printf '%s\n' 'Investigate the product.' > "$packet"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" \
    send researcher --follow "the research skill" "$packet")"
  [ "$code" = 0 ] || fail "send from another checkout expected 0, got $code: $(cat "$TMP/err")"
  started_once
  [ "$(out_json cwd)" = "$(git -C "$TMP/repo" rev-parse --show-toplevel)" ] \
    || fail "the researcher did not start in the calling checkout: $(out_json cwd)"
  rm -f "$MMW_HOME/installed-root"
}

scenario_sendbrief() {
  local code packet second batch dest copy
  packet="$TMP/packet.txt"
  second="$TMP/second.txt"
  printf '%s\n' 'the brief body' > "$packet"
  printf '%s\n' 'the second brief' > "$second"

  echo "--- send advisor starts the advisor row in the current worktree, as a batch this session is woken for"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$packet")"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  batch="$(newest_batch)"
  [ -n "$batch" ] || fail "no batch directory was made under $STATE_DIR/briefs"
  [ "$(cat "$TMP/out")" = "$batch/1"$'\t'"$(out_json id)" ] \
    || fail "stdout should be <batch>/1<TAB><session>: $(cat "$TMP/out")"
  [ "$(out_json provider)" = "claude/claude-fable-5-1" ] \
    || fail "send advisor did not start the advisor row: $(out_json provider)"
  [ "$(out_json settings.thinkingOptionId)" = medium ] \
    || fail "effort: $(out_json settings.thinkingOptionId)"
  copy="$STATE_DIR/briefs/$batch/1/brief.md"
  [ "$(out_json initialPrompt)" = "Dispatched: advisor, brief $copy. Read the mmw-mode skill in full, then follow the advisor skill. It is your whole task: what came before it is done, and you start no agent it does not name." ] \
    || fail "the prompt should name the role, the brief's copy and what it follows: $(out_json initialPrompt)"
  [ "$(head -1 "$copy")" = "the brief body" ] || fail "the copy should open with the brief: $(cat "$copy")"
  grep -q "report $batch/1 <file>" "$copy" || fail "the copy should end with how to report: $(cat "$copy")"
  dest="$(cd "$TMP/repo" && git rev-parse --show-toplevel)"
  [ "$(out_json cwd)" = "$dest" ] || fail "cwd: $(out_json cwd), want $dest"
  [ "$(brief_watch "briefs:$batch")" = "paseo agt_main" ] \
    || fail "the batch's watch should wake paseo agt_main: $(brief_watch "briefs:$batch")"
  grep -q "\"session\": \"$(out_json id)\"" "$STATE_DIR/briefs/$batch/1/started.json" \
    || fail "the brief's session is not recorded: $(cat "$STATE_DIR/briefs/$batch/1/started.json")"
  hasnt "gh :: issue :: comment"
  hasnt_runner_worktree

  echo "--- send researcher with two files starts two sessions of one batch, each told its own brief"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$second")"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(count_of "paseo :: run")" = 2 ] || fail "expected two paseo runs, got $(count_of "paseo :: run")"
  batch="$(newest_batch)"
  [ "$(cut -f1 "$TMP/out" | tr '\n' ' ')" = "$batch/1 $batch/2 " ] \
    || fail "stdout should name both briefs of one batch: $(cat "$TMP/out")"
  [ "$(out_json initialPrompt)" = "Dispatched: researcher, brief $STATE_DIR/briefs/$batch/2/brief.md. Read the mmw-mode skill in full, then follow the research skill. It is your whole task: what came before it is done, and you start no agent it does not name." ] \
    || fail "the second researcher's prompt is wrong: $(out_json initialPrompt)"
  grep -q "report $batch/2 <file>" "$STATE_DIR/briefs/$batch/2/brief.md" \
    || fail "the second copy should say how to report brief 2: $(cat "$STATE_DIR/briefs/$batch/2/brief.md")"
  [ "$(out_json provider)" = "claude/claude-opus-5" ] \
    || fail "send researcher did not start the researcher row: $(out_json provider)"

  echo "--- a brief send without --follow is refused, and nothing is started: the session would not know what it works by"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher "$packet")"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q -- '--follow' "$TMP/err" || fail "the refusal should name --follow: $(cat "$TMP/err")"
  never_ran
  nothing_printed
  [ -z "$(newest_batch)" ] || fail "no batch should be left: $(newest_batch)"

  echo "--- a role send does not know is refused, and nothing is started"
  reset_log
  fresh_repo
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send explainer --follow "the research skill" "$packet")"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran
  nothing_printed

  echo "--- a session no runner can name is refused before anything starts: nothing could wake it"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  code="$(run_dispatch env -u TERM_PROGRAM -u HERDR_ENV bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet")"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran
  nothing_printed
  [ -z "$(newest_batch)" ] || fail "no batch should be left: $(newest_batch)"

  echo "--- a start the runner refuses closes the batch: no batch, no watch, the reason kept"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main MMW_FAKE_PASEO_SCENARIO=run-fail \
          bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$packet")"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  started_once
  nothing_printed
  [ -z "$(newest_batch)" ] || fail "the batch should be removed: $(newest_batch)"
  grep -q '"briefs"' "$STATE_DIR/watches.json" && fail "the batch's watch should be closed: $(cat "$STATE_DIR/watches.json")"

  echo "--- the second of two starts refused stops the first session and closes the batch"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main MMW_FAKE_PASEO_SCENARIO=run-fail-after-one \
          bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$second")"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  has "paseo :: archive :: --force :: $(out_json id)"
  [ -z "$(newest_batch)" ] || fail "the batch should be removed: $(newest_batch)"
  nothing_printed

  echo "--- a missing or empty brief file is refused, and nothing is started"
  reset_log
  fresh_repo
  : > "$TMP/empty-packet.txt"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send advisor --follow "the advisor skill" "$TMP/nope.txt")"
  [ "$code" = 2 ] || fail "missing file expected exit 2, got $code: $(cat "$TMP/err")"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$TMP/empty-packet.txt")"
  [ "$code" = 2 ] || fail "empty file expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran
  nothing_printed

  echo "--- a missing row is refused, and nothing is started"
  reset_log
  fresh_repo
  local saved="$TMP/models.saved"
  cp "$MMW_HOME/models.json" "$saved"
  python3 - "$MMW_HOME/models.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
del data["rows"]["candidate"]
json.dump(data, open(path, "w"))
PY
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send candidate --follow "the brief" "$packet")"
  mv "$saved" "$MMW_HOME/models.json"
  [ "$code" = 2 ] || fail "missing candidate row expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran
  nothing_printed
}

scenario_send() {
  local code
  fresh_repo
  reset_log
  no_relay
  seed_main_agent agt_main
  seed_main_agent agt_worker
  echo '[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}]' > "$TMP/tickets.json"

  echo "--- send worker opens the ticket's watch for this session, then starts its worker"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" send worker 61)"
  [ "$code" = 0 ] || fail "send worker expected 0, got $code: $(cat "$TMP/err")"
  [ "$(watch_main tickets:61)" = "paseo agt_main" ] \
    || fail "#61's watch should wake agt_main: $(cat "$STATE_DIR/watches.json")"
  started_once
  [ "$(out_json title)" = "#61 worker" ] || fail "title: $(out_json title)"
  case "$(out_json initialPrompt)" in
    "Dispatched: worker, ticket #61, base "????????????????????????????????????????". Read the mmw-mode skill in full, then follow the mmw-mode skill's playbooks/work-a-ticket.md. It is your whole task: what came before it is done, and you start no agent it does not name.") ;;
    *) fail "the worker's prompt should be its dispatch line and what it follows: $(out_json initialPrompt)" ;;
  esac

  echo "--- send reviewer starts the reviewer and leaves the watch with the session that opened it"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_worker FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" send reviewer 61)"
  [ "$code" = 0 ] || fail "send reviewer expected 0, got $code: $(cat "$TMP/err")"
  [ "$(watch_main tickets:61)" = "paseo agt_main" ] \
    || fail "send reviewer must not take the watch: $(cat "$STATE_DIR/watches.json")"
  started_once
  [ "$(out_json title)" = "#61 reviewer" ] || fail "title: $(out_json title)"
  case "$(out_json initialPrompt)" in
    "Dispatched: reviewer, ticket #61, base "????????????????????????????????????????". Read the mmw-mode skill in full, then follow the code-review skill's references/session.md. It is your whole task: what came before it is done, and you start no agent it does not name.") ;;
    *) fail "the reviewer's prompt should be its dispatch line and what it follows: $(out_json initialPrompt)" ;;
  esac

  echo "--- a ticket number that is not digits is refused, and nothing is started"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send worker 6x1)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran
}

scenario_briefreport() {
  local code packet batch answer
  packet="$TMP/packet.txt"
  answer="$TMP/answer.md"
  printf '%s\n' 'the question' > "$packet"
  printf '%s\n' 'the cited findings' > "$answer"
  reset_log
  fresh_repo
  rm -rf "$STATE_DIR/briefs"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" send researcher --follow "the research skill" "$packet" "$packet")"
  [ "$code" = 0 ] || fail "brief expected exit 0, got $code: $(cat "$TMP/err")"
  batch="$(newest_batch)"
  local one two
  one="$(sed -n 1p "$TMP/out" | cut -f2)"
  two="$(sed -n 2p "$TMP/out" | cut -f2)"

  echo "--- the brief's own session reports, and the answer is kept in the batch"
  code="$(run_dispatch env PASEO_AGENT_ID="$one" bash "$DISPATCH" "${TOOLS[@]}" report "$batch/1" "$answer")"
  [ "$code" = 0 ] || fail "report expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$STATE_DIR/briefs/$batch/1/result.md")" = "the cited findings" ] \
    || fail "the result should be kept as written"

  echo "--- another session cannot report that brief"
  code="$(run_dispatch env PASEO_AGENT_ID="$one" bash "$DISPATCH" "${TOOLS[@]}" report "$batch/2" "$answer")"
  [ "$code" = 2 ] || fail "a report from the wrong session expected 2, got $code"

  echo "--- show lists each brief, its state and where its answer is"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" brief show "$batch")"
  [ "$code" = 0 ] || fail "show expected 0, got $code: $(cat "$TMP/err")"
  grep -q "^$batch/1"$'\t'"reported"$'\t'"researcher"$'\t'"paseo"$'\t'"$one"$'\t'".*/1/result.md$" "$TMP/out" \
    || fail "show should list brief 1 as reported with its result: $(cat "$TMP/out")"
  grep -q "^$batch/2"$'\t'"open" "$TMP/out" || fail "show should list brief 2 as open: $(cat "$TMP/out")"

  echo "--- no wake is queued while a brief is open, so an ack of the batch is refused"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack brief "$batch")"
  [ "$code" = 2 ] || fail "an early ack expected 2, got $code"

  echo "--- once both have reported, one relay cycle queues one wake, and the parent acks it by its batch"
  code="$(run_dispatch env PASEO_AGENT_ID="$two" bash "$DISPATCH" "${TOOLS[@]}" report "$batch/2" "$answer")"
  [ "$code" = 0 ] || fail "the second report expected 0, got $code: $(cat "$TMP/err")"
  python3 - "$SKILL/scripts" "$STATE_DIR" <<'PY' || fail "the relay did not queue the batch's wake"
import sys
sys.path.insert(0, sys.argv[1])
import relay
r = relay.Relay(__import__("pathlib").Path(sys.argv[2]))
r.poll_briefs()
r.poll_briefs()
rows = [w for w in r.rows() if w["event"] == relay.BRIEF_DONE]
assert len(rows) == 1 and rows[0]["session"] == "agt_main", rows
PY
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack brief "$batch")"
  [ "$code" = 0 ] || fail "the ack expected 0, got $code: $(cat "$TMP/err")"

  echo "--- close stops every session of the batch, closes its watch and removes it"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" brief close "$batch")"
  [ "$code" = 0 ] || fail "close expected 0, got $code: $(cat "$TMP/err")"
  has "paseo :: archive :: --force :: $one"
  has "paseo :: archive :: --force :: $two"
  [ ! -d "$STATE_DIR/briefs/$batch" ] || fail "the batch directory should be gone"
  [ -z "$(brief_watch "briefs:$batch")" ] || fail "the batch's watch should be closed"

  echo "--- a report to a closed batch is refused: nobody waits for it"
  code="$(run_dispatch env PASEO_AGENT_ID="$one" bash "$DISPATCH" "${TOOLS[@]}" report "$batch/1" "$answer")"
  [ "$code" = 2 ] || fail "a late report expected 2, got $code"
  [ ! -e "$STATE_DIR/briefs/$batch" ] || fail "a late report should write nothing: $(ls -R "$STATE_DIR/briefs/$batch")"
}

scenario_resume() {
  local code
  echo "--- a live worker is found by the worker.started event on its ticket and sent the text"
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
  runner_line 61 paseo agt_w61 worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: view :: 61 :: --json :: comments"
  has "paseo :: send :: --no-wait :: agt_w61 :: continue"

  echo "--- no matching worker is a refusal, and nothing is sent"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"

  echo "--- a started worker its runner no longer has is exit 2, and the refusal names retract"
  reset_log
  runner_line 61 paseo agt_gone61 worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q "run retract 61" "$TMP/err" \
    || fail "a worker gone from its runner still holds the ticket; the refusal must name retract: $(cat "$TMP/err")"

  echo "--- a worker that is there but will not take the message is exit 3, not 2"
  reset_log
  seed_agent 61 worker
  code="$(run_dispatch env MMW_FAKE_SEND_FAILS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 3 ] || fail "a busy worker must not read as a missing one, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_61_worker :: continue"

  echo "--- it names the way out that works on every runner: replacing the worker"
  grep -q "start 61 worker" "$TMP/err" \
    || fail "a caller that keeps hitting exit 3 needs the one command that settles it: $(cat "$TMP/err")"
  grep -q "get_agent_status" "$TMP/err" \
    && fail "a Paseo-only tool must not be the advice on every runner: $(cat "$TMP/err")"

  echo "--- a message handed over that the runner cannot confirm is exit 4, recorded, not to be sent again"
  reset_log
  seed_orca_terminal term_w61
  runner_line 61 orca term_w61 worker
  code="$(run_dispatch env MMW_FAKE_ORCA_SEND=unobserved \
          bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 4 ] || fail "an unconfirmed hand-over is exit 4, got $code: $(cat "$TMP/err")"
  [ "$(count_of "orca :: terminal :: send")" = 1 ] \
    || fail "the text is typed once: $(count_of "orca :: terminal :: send") sends"
  posted_events 61 session | grep -q "^worker.resumed session=term_w61" \
    || fail "the hand-over is recorded as worker.resumed: $(posted_events 61 session)"
}

# `resume` types into a worker only while no event on the ticket has ended its hold: the
# fold's holders, which is also what the watchdog reads when it says a ticket is held with
# no session to ask. The case that matters is a worker session its runner still lists
# after its hold ended, because the newest worker.started alone names it all the same
# (agentflow #754, where the watchdog found no session to ask and resume typed into one).
resume_after() {
  local ending="$1"
  shift
  reset_log
  seed_agent 61 worker
  post_ev 61 "$ending" --ticket 61 --spec 76 --line "$ending" "$@"
  run_dispatch env MMW_SPEC=76 bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue
}

refused_resume_names() {
  local ending="$1" next="$2" code="$3"
  [ "$code" = 2 ] || fail "resume after $ending expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"
  posted_events 61 | grep -q "^worker.resumed" \
    && fail "a refused resume must not post worker.resumed, which would make the ended hold live again: $(posted_events 61)"
  grep -q "$ending" "$TMP/err" || fail "the refusal should name $ending: $(cat "$TMP/err")"
  grep -qF -- "$next" "$TMP/err" || fail "the refusal after $ending should name $next: $(cat "$TMP/err")"
  nothing_printed
}

scenario_resumeendedhold() {
  local code
  echo "--- worker.lost ended the worker's hold: nothing is typed into the session, and start is named"
  code="$(resume_after worker.lost --actor judge --field session=agt_61_worker --field runner=paseo)"
  refused_resume_names worker.lost "dispatch.sh start 61 worker" "$code"
  grep -qF "dispatch.sh advance 76" "$TMP/err" || fail "inside a night the refusal should name advance: $(cat "$TMP/err")"

  echo "--- worker.retracted ended it the same way"
  code="$(resume_after worker.retracted --field session=agt_61_worker --field runner=paseo)"
  refused_resume_names worker.retracted "dispatch.sh start 61 worker" "$code"

  echo "--- a ticket.refused naming the worker ended it: fix the reason, then start"
  code="$(resume_after ticket.refused --field reason=dirty-tree --field session=agt_61_worker --field runner=paseo)"
  refused_resume_names ticket.refused "dispatch.sh start 61 worker" "$code"
  grep -q "dirty-tree" "$TMP/err" || fail "the refusal should carry the refusal's reason: $(cat "$TMP/err")"

  echo "--- ticket.returned ended every hold: the ticket is triage's, not a worker's to continue"
  code="$(resume_after ticket.returned)"
  refused_resume_names ticket.returned "needs-triage" "$code"

  echo "--- ticket.bounced ended every hold: the labels say whether advance takes it up or triage does"
  code="$(resume_after ticket.bounced --field reason=conflict --field commit=abc123)"
  refused_resume_names ticket.bounced "dispatch.sh advance 76" "$code"

  echo "--- ticket.landed ended every hold: the work is on the base branch"
  code="$(resume_after ticket.landed)"
  refused_resume_names ticket.landed "dispatch.sh status 76" "$code"

  echo "--- spec.suspended ended every hold: the night is taken up again with open, then advance"
  code="$(resume_after spec.suspended)"
  refused_resume_names spec.suspended "dispatch.sh open 76" "$code"

  echo "--- a worker replaced by a live one: the text goes to the live one"
  reset_log
  runner_line 61 paseo agt_old worker
  post_ev 61 worker.replaced --ticket 61 --spec 76 --line "replaced" --field session=agt_old --field runner=paseo
  seed_agent 61 worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 0 ] || fail "resume of the live replacement expected 0, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_61_worker :: continue"
  hasnt "agt_old :: continue"

  echo "--- a ticket whose events cannot be read sends nothing"
  reset_log
  seed_agent 61 worker
  post_raw_comment 61 "broken <!-- mmw {not json -->"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 2 ] || fail "unreadable events expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"
}

scenario_wait() {
  local code

  echo "--- a result already on the ticket is printed with the report's text, and wait is not called"
  reset_log
  printf '### Correctness\n- In-ticket: src/a.ts:12 drops the last row\n' > "$TMP/report.md"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "comments": [$(ev reviewer.reported 61 "REVIEW abcdef0123456789abcdef0123456789abcdef01..fedcba9876543210fedcba9876543210fedcba98" --field base=abcdef0123456789abcdef0123456789abcdef01 --text-file "$TMP/report.md")]}
]
JSON
  seed_agent 61 reviewer
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 reviewer)"
  [ "$code" = 0 ] || fail "expected exit 0 when the result is already there, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = "reviewer.reported base=abcdef0123456789abcdef0123456789abcdef01
REVIEW abcdef0123456789abcdef0123456789abcdef01..fedcba9876543210fedcba9876543210fedcba98

### Correctness
- In-ticket: src/a.ts:12 drops the last row" ] \
    || fail "stdout should be the event, its key fields, then the report's text: $(cat "$TMP/out")"
  hasnt "paseo :: wait"
  hasnt "gh :: issue :: comment"
  hasnt "paseo :: archive"
  hasnt "paseo :: send"

  echo "--- no result yet: exit 3 at once, one read of the ticket, no runner asked"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}
]
JSON
  seed_agent 61 reviewer
  local began ended
  began="$(date +%s)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 reviewer)"
  ended="$(date +%s)"
  [ "$code" = 3 ] || fail "no result yet is exit 3, got $code: $(cat "$TMP/err")"
  [ "$((ended - began))" -lt 5 ] \
    || fail "wait took $((ended - began))s: it waits for nothing and answers at once"
  [ "$(count_of 'gh :: issue :: view :: 61 :: --json :: comments')" -le 2 ] \
    || fail "wait reads the ticket and does not poll it: $(count_of 'gh :: issue :: view :: 61 :: --json :: comments') reads"
  hasnt "paseo :: wait"
  hasnt "paseo :: ls"
  [ ! -s "$TMP/out" ] || fail "stdout should be empty with no result: $(cat "$TMP/out")"

  echo "--- no matching agent is a refusal, exit 2, wait is not called"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 reviewer)"
  [ "$code" = 2 ] || fail "expected exit 2 with no agent, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: wait"
}

scenario_reverify() {
  local copy code
  copy="$(skill_copy_for reverify)"
  mkdir -p "$TMP/fake/skills/verify-ticket/scripts"
  # The real run posts its own `ticket.checked` on the ticket; this one posts the same
  # event straight into the fake tracker.
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("verify-ticket" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
number = sys.argv[1]
if number in os.environ.get("FAKE_VERIFY_UNRECORDED", "").split(","):
    sys.exit(4)
failing = {n for n in os.environ.get("FAKE_VERIFY_FAIL", "").split(",") if n}
failed = ["AC3"] if number in failing else []
# FAKE_VERIFY_CRASH: red exit with nothing posted, the way a crash after the run is.
if number in os.environ.get("FAKE_VERIFY_CRASH", "").split(","):
    sys.exit(1)
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
body = subprocess.run(
    [sys.executable, os.environ["MMW_EVENTS_PY_FOR_TESTS"], "emit", "ticket.checked",
     "--ticket", number, "--line", "Reverify", "--actor", "main", "--stage", "regress",
     "--field", "run=reverify", "--field", "commit=" + head,
     "--field", "result=" + ("unmet" if failed else "met"),
     "--json-field", "failed=" + json.dumps(failed)],
    capture_output=True, text=True, check=True).stdout
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()) if store.is_file() else {}
posted.setdefault(number, []).append(body)
store.write_text(json.dumps(posted))
print("UNMET: 1 (met: 4)" if failed else "ALL MET (5 met)")
sys.exit(1 if failed else 0)
PY
  chmod +x "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"

  fresh_repo
  write_batch
  reset_log
  open_night
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL=62 \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  echo "--- each run is the orchestrator's reverify, and a green one writes nothing but its own run"
  has "verify-ticket :: 61 :: --reverify :: --actor :: main"
  has "verify-ticket :: 62 :: --reverify :: --actor :: main"
  hasnt "gh :: issue :: comment :: 61"
  [ "$(posted_events 61 run actor | tr '\n' '|')" = "ticket.landed run=None actor=main|ticket.checked run=reverify actor=main|" ] \
    || fail "#61 should carry its landing and the reverify's ticket.checked only: $(posted_events 61 run actor)"
  has "gh :: issue :: reopen :: 62"
  has "gh :: issue :: edit :: 62 :: --add-label :: needs-triage :: --remove-assignee :: alice"
  grep -q "AC3" "$MMW_TEST_LOG" || fail "the failing criterion was not commented: $(cat "$MMW_TEST_LOG")"
  grep -q "reverify #76: 1 green, 1 red" "$TMP/out" \
    || fail "the summary line is missing: $(cat "$TMP/out")"
  echo "--- the red ticket's failing criteria come off its ticket.checked, not the run's printout"
  posted_events 62 failed | grep -qx "ticket.regressed failed=\['AC3'\]" \
    || fail "#62 should carry ticket.regressed naming AC3: $(posted_events 62 failed)"

  echo "--- a run whose result could not be written, or a red exit with no red run of HEAD on the ticket, is not a red ticket"
  local how
  for how in FAKE_VERIFY_UNRECORDED FAKE_VERIFY_CRASH; do
    reset_log
    open_night
    post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
    post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
    # An older red run is on #61: a reader of "the newest reverify" alone would reopen it.
    post_ev 61 ticket.checked --ticket 61 --line "Reverify" --actor main --field run=reverify \
      --field "commit=$(printf 'b%.0s' $(seq 40))" --field result=unmet --json-field 'failed=["AC9"]'
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" "$how=61" \
            bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
    [ "$code" = 2 ] || fail "$how: expected exit 2, got $code: $(cat "$TMP/err")"
    hasnt "gh :: issue :: reopen"
    ! posted_events 61 | grep -q ticket.regressed || fail "$how: #61 was regressed: $(posted_events 61)"
  done

  echo "--- a ticket that passed and has not landed is not run again on the base branch"
  reset_log
  open_night
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "verify-ticket :: 61 :: --reverify"
  hasnt "verify-ticket :: 62 :: --reverify"

  echo "--- all green exits 0"
  reset_log
  open_night
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: reopen"

  echo "--- a ticket an earlier reverify reopened is run again, and a green run closes it"
  reset_log
  open_night
  write_batch
  reopened_in_triage 62
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  post_ev 62 ticket.regressed --ticket 62 --line "Reverify failed: AC3" \
    --field "commit=$(printf 'c%.0s' $(seq 40))" --json-field 'failed=["AC3"]'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0 once the reopened ticket is green, got $code: $(cat "$TMP/err")"
  has "verify-ticket :: 62 :: --reverify :: --actor :: main"
  has "gh :: issue :: edit :: 62 :: --remove-label :: needs-triage"
  has "gh :: issue :: close :: 62 :: --reason :: completed"
  posted_events 62 commit | grep -q "^ticket.recovered commit=" \
    || fail "#62 should carry ticket.recovered: $(posted_events 62 commit)"
  grep -q "reverify #76: 2 green, 0 red, 1 recovered" "$TMP/out" \
    || fail "the summary line should count the recovery: $(cat "$TMP/out")"

  echo "--- a reopened ticket that is still red is left where it is, and is not regressed twice"
  reset_log
  open_night
  write_batch
  reopened_in_triage 62
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  post_ev 62 ticket.regressed --ticket 62 --line "Reverify failed: AC3" \
    --field "commit=$(printf 'c%.0s' $(seq 40))" --json-field 'failed=["AC3"]'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL=62 \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 1 ] || fail "expected exit 1 while the reopened ticket is red, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: reopen :: 62"
  hasnt "gh :: issue :: close :: 62"
  [ "$(posted_events 62 | grep -c ticket.regressed)" = 1 ] \
    || fail "#62 should carry one ticket.regressed, not a second: $(posted_events 62)"

  echo "--- a reopened ticket triage has handed to a worker is left alone"
  reset_log
  open_night
  write_batch
  reopened_in_triage 62 ready-for-agent
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  post_ev 62 ticket.regressed --ticket 62 --line "Reverify failed: AC3" \
    --field "commit=$(printf 'c%.0s' $(seq 40))" --json-field 'failed=["AC3"]'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "verify-ticket :: 62 :: --reverify"
  hasnt "gh :: issue :: close :: 62"
}

scenario_summary() {
  local when code copy other
  copy="$(skill_copy_for summary)"
  mkdir -p "$TMP/fake/skills/verify-ticket/scripts"
  # Like the real run, it posts its own `ticket.checked`, which is the whole record
  # of a reverify that summary reads.
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("verify-ticket" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
number = sys.argv[1]
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
body = subprocess.run(
    [sys.executable, os.environ["MMW_EVENTS_PY_FOR_TESTS"], "emit", "ticket.checked",
     "--ticket", number, "--line", "Reverify", "--actor", "main", "--stage", "regress",
     "--field", "run=reverify", "--field", "commit=" + head, "--field", "result=met"],
    capture_output=True, text=True, check=True).stdout
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()) if store.is_file() else {}
posted.setdefault(number, []).append(body)
store.write_text(json.dumps(posted))
print("ALL MET (5 met)")
sys.exit(0)
PY
  chmod +x "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"

  when="$(python3 -c 'from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc)-timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "$when",
   "createdAt": "2026-08-29T00:00:00Z",
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main),
                $(ev ticket.landed 61 "Landed issue-61 into main")]}
]
JSON
  reset_log
  fresh_repo
  post_ev 76 spec.opened --ticket '' --spec 76 --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field into=main --field project=proj
  echo "--- without a reverify of the base branch, summary refuses before it posts or closes the watch"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" --tools "$(dirname "$SKILL")/verify-ticket/scripts" summary 76)"
  [ "$code" = 2 ] || fail "missing reverify expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: comment :: 76 :: --body"

  echo "--- after reverify, the posted comment has a Reverify line matching that run"
  : > "$MMW_TEST_LOG"; : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "reverify expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "reverify #76: 1 green, 0 red" "$TMP/out" \
    || fail "reverify should report 1 green: $(cat "$TMP/out")"
  git -C "$TMP/repo" worktree add -q --detach "$TMP/linked-summary" HEAD
  : > "$MMW_TEST_LOG"; : > "$MMW_GH_LAST_BODY"
  other="$(other_clone)"
  commit_file "$other" after-reverify.txt changed after-reverify
  git -C "$other" push -q origin main
  code="$( (cd "$TMP/linked-summary" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" --tools "$(dirname "$SKILL")/verify-ticket/scripts" summary 76) \
          > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 2 ] || fail "an origin advance after reverify expected exit 2, got $code"
  grep -q "$(git -C "$TMP/origin.git" rev-parse main)" "$TMP/err" \
    || fail "the refusal should name the base commit it has no reverify of: $(cat "$TMP/err")"
  hasnt "gh :: issue :: comment :: 76 :: --body"

  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "second reverify expected exit 0: $(cat "$TMP/err")"
  : > "$MMW_TEST_LOG"; : > "$MMW_GH_LAST_BODY"
  code="$( (cd "$TMP/linked-summary" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" --tools "$(dirname "$SKILL")/verify-ticket/scripts" summary 76) \
          > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "^NIGHT SUMMARY " "$MMW_GH_LAST_BODY" \
    || fail "the posted comment should open NIGHT SUMMARY: $(cat "$MMW_GH_LAST_BODY")"
  grep -q "Reverify: 1 green on $(git -C "$TMP/origin.git" rev-parse main)" "$MMW_GH_LAST_BODY" \
    || fail "missing Reverify line matching that reverify: $(cat "$MMW_GH_LAST_BODY")"
  grep -q "Closed: #61 ALL MET" "$MMW_GH_LAST_BODY" \
    || fail "the closed line should carry the ticket's own result line: $(cat "$MMW_GH_LAST_BODY")"
  posted_events 76 date | grep -q "^spec.closed date=" \
    || fail "the summary should be the spec.closed event on #76: $(posted_events 76 date)"

  echo "--- summary stops the relay watching the spec, and leaves one watching another alone"
  post_ev 76 spec.opened --ticket '' --spec 76 --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field into=main --field project=proj
  no_relay
  fake_relay
  [ -n "$(relay_now)" ] || fail "the stand-in relay should be running before summary"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" --tools "$(dirname "$SKILL")/verify-ticket/scripts" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "summary should have stopped the relay: $(relay_now)"
  post_ev 76 spec.opened --ticket '' --spec 76 --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field into=main --field project=proj
  fake_relay '{"spec": 80}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" --tools "$(dirname "$SKILL")/verify-ticket/scripts" summary 76)"
  [ "$code" = 0 ] || fail "a relay watching another spec is not this summary's failure, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"spec": 80}'*) ;; *) fail "a relay watching spec 80 should be left running: $(relay_now)" ;; esac
  no_relay
}

scenario_summarycloseout() {
  local code
  reset_log; fresh_repo; summary_ready_fixture
  cat > "$TMP/tickets.json" <<JSON
[{"number":61,"state":"CLOSED","labels":[],
  "comments":[$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main)]}]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 2 ] || fail "passed-unlanded summary expected 2, got $code"
  grep -q '#61' "$TMP/err" \
    || fail "passed-unlanded refusal was not explicit: $(cat "$TMP/err")"
  hasnt "gh :: issue :: comment :: 76 :: --body"

  reset_log; summary_ready_fixture
  cat > "$TMP/tickets.json" <<JSON
[{"number":61,"state":"OPEN","labels":["ready-for-agent"],"assignees":["mmw-bot"],
  "comments":[$(ev worker.started 61 "worker started on orca: session term_7" --spec 76 \
    --field session=term_7 --field runner=orca $(start_facts "$(wt 61)" 61 worker))]}]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 2 ] || fail "live-worker summary expected 2, got $code"
  grep -q 'term_7' "$TMP/err" \
    || fail "the refusal should name the live worker term_7: $(cat "$TMP/err")"
  hasnt "gh :: issue :: comment :: 76 :: --body"
}

scenario_summaryholdsfindings() {
  local when code
  when="$(python3 -c 'from datetime import datetime, timezone, timedelta; print((datetime.now(timezone.utc)-timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "$when",
   "createdAt": "2026-08-29T00:00:00Z", "children": [90, 91],
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main),
                $(ev ticket.landed 61 "Landed issue-61 into main"),
                $(ev child.opened 61 "Opened #90 (finding)" --spec 76 --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --spec 76 --field child=91 --field kind=finding),
                $(ev child.closed 61 "Fixed #90" --spec 76 --field child=90 --field resolution=fixed)]},
  {"number": 90, "state": "CLOSED", "labels": ["mmw:child"], "parent": {"number": 61}},
  {"number": 91, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}}
]
JSON
  reset_log
  fresh_repo
  summary_ready_fixture
  reverified 61
  echo "--- a finding no route reached refuses the summary: nothing posted, the watch still open"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q "Findings routed: 2/1/0/0/0/1" "$TMP/err" \
    || fail "the refusal should quote the line it read: $(cat "$TMP/err")"
  hasnt "gh :: issue :: comment :: 76"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "a refused summary must leave the watch open: $(relay_now)" ;; esac

  echo "--- once every finding carries a route, the summary is posted and the watch closes"
  python3 - "$TMP/tickets.json" "$(ev child.closed 61 "Closed #91" --spec 76 --field child=91 --field resolution=stale --field reason=invalid)" <<'PY'
import json, sys
rows = json.load(open(sys.argv[1]))
rows[0]["comments"].append(json.loads(sys.argv[2]))
rows[2]["state"] = "CLOSED"
json.dump(rows, open(sys.argv[1], "w"))
PY
  reset_log
  summary_ready_fixture
  reverified 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: comment :: 76 :: --body"
  grep -q "Findings routed: 2/1/0/1/0/0" "$MMW_GH_LAST_BODY" \
    || fail "every finding should be routed now: $(cat "$MMW_GH_LAST_BODY")"
  [ -z "$(relay_now)" ] || fail "summary should have closed the watch: $(relay_now)"
  no_relay
}

# ------------------------------------------------------------------ orphaned claims

# #63 is claimed by <login>; its worker, started on Orca, has been reported lost.
write_claimed_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["$1"],
   "body": "## Parent\\n\\n#76\\n", "title": "claimed ticket",
   "comments": [$(ev worker.started 63 "worker started on orca: session term_3" \
                  --field session=term_3 --field runner=orca $(start_facts "$(wt 63)" 63 worker)),
                $(ev ticket.claimed 63 "Claimed #63"),
                $(ev worker.lost 63 "term_3 is gone" --field session=term_3 --field runner=orca)]}
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

  echo "--- a claim whose worker was reported lost, with no workspace behind it, is given back"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 63 :: --remove-assignee :: @me"
  grep -q "released 1" "$TMP/err" || fail "the summary does not count it: $(cat "$TMP/err")"

  echo "--- and never silently: the line names the ticket and says why"
  posted_events 63 reason | grep -qx "ticket.released reason=worker-lost" \
    || fail "#63 should carry ticket.released (worker-lost): $(posted_events 63 reason)"

  echo "--- the ticket it frees is dispatched by the same advance, not the next one"
  assert_wt 63
  hasnt_runner_worktree
  grep -q "started 1" "$TMP/err" || fail "it was freed and then left: $(cat "$TMP/err")"

  echo "--- a standing workspace does not keep the claim: the worker is gone, so it is released into that workspace"
  reset_log
  write_claimed_batch mmw-bot
  seed_workspace 63
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 63 :: --remove-assignee :: @me"
  grep -q "released 1" "$TMP/err" \
    || fail "the claim should have been given back: $(cat "$TMP/err")"
  grep -q "started 1" "$TMP/err" || fail "it was freed and then left: $(cat "$TMP/err")"
  hasnt "workspace :: create"
  [ "$(out_json title)" = "#63 worker" ] \
    || fail "it should re-dispatch into the standing workspace: $(cat "$TMP/out")"
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
  grep "#63" "$TMP/err" | grep -q "alice" || fail "the reason is not on stderr: $(cat "$TMP/err")"
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

  echo "--- and the ticket reads as held by that worker, not as an orphaned claim"
  grep "#63" "$TMP/err" | grep "mmw-bot" | grep "agt_63_worker" | grep -q "paseo" \
    || fail "stderr does not name the worker holding it: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "a second worker was started on it: $(cat "$TMP/err")"
}

scenario_releasestanding() {
  local code
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"],
   "body": "## Parent\\n\\n#76\\n", "title": "claimed ticket",
   "comments": [$(ev worker.started 61 "worker started on orca: session term_1" \
                  --field session=term_1 --field runner=orca $(start_facts "$(wt 61)" 61 worker)),
                $(ev worker.lost 61 "term_1 is gone" --field session=term_1 --field runner=orca)]}
]
JSON
  seed_workspace 61
  echo "--- assigned, its worker lost, workspace still standing: RELEASE then DISPATCH into that workspace"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  [ "$(out_json title)" = "#61 worker" ] \
    || fail "advance should dispatch #61: $(cat "$TMP/out")"
  hasnt "workspace :: create"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"
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
  grep "#61" "$TMP/err" | grep -q "alice" || fail "#61: $(cat "$TMP/err")"
  grep "#62" "$TMP/err" | grep -q "#61" || fail "#62: $(cat "$TMP/err")"
  grep "#63" "$TMP/err" | grep -q "agt_63_worker" || fail "#63: $(cat "$TMP/err")"
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
}

# ------------------------------------------------------------------ suspend

# #61 is a ticket under spec #76, and its events carry a child.opened for each of
# #90–#93 naming spec #76. #92 has already been moved under the spec, the way a route
# cut short after its move leaves it, and #76 itself sits under map #18 — so a route
# that read the spec off the tree would move #92 under the map. #80 is a ticket already
# under the spec; #95 is an issue under #61 that no event of #61 names.
write_route_batch() {
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 18, "state": "OPEN", "labels": ["mmw:map"], "parent": null},
  {"number": 76, "state": "OPEN", "labels": ["mmw:spec"], "parent": {"number": 18}, "children": [61]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "junior-worker", "mmw:ticket"], "parent": {"number": 76},
   "body": "## Parent\\n\\n#76, Implementation Decisions section 1\\n\\n## What to build\\n\\n1. Export the report. AC1.\\n\\n## Acceptance criteria\\n\\n- [ ] AC1: report exports\\n  CHECK: echo report-ok\\n  EXPECT: report-ok\\n  EVIDENCE: pending\\n",
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --spec 76 --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --spec 76 --field child=91 --field kind=finding),
                $(ev child.opened 61 "Opened #92 (finding)" --spec 76 --field child=92 --field kind=finding),
                $(ev child.opened 61 "Opened #93 (deferred)" --spec 76 --field child=93 --field kind=deferred)]},
  {"number": 80, "state": "OPEN", "labels": ["ready-for-agent"], "parent": {"number": 76}},
  {"number": 81, "state": "OPEN", "labels": ["mmw:lesson"], "parent": {"number": 76}},
  {"number": 82, "state": "OPEN", "labels": ["ready-for-agent", "mmw:ticket"], "parent": {"number": 76}},
  {"number": 83, "state": "OPEN", "labels": ["ready-for-agent", "mmw:problem"], "parent": {"number": 76}},
  {"number": 90, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 91, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 92, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 76}},
  {"number": 93, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 95, "state": "OPEN", "labels": ["needs-triage"], "parent": {"number": 61}}
]
JSON
}

route_in() { run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" "$@"; }

scenario_routeonekind() {
  local code
  reset_log
  fresh_repo
  write_route_batch

  echo "--- became-ticket onto a problem"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket 83)"
  [ "$code" = 0 ] || fail "a problem should become a ticket, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 83 :: --add-label :: mmw:ticket :: --remove-label :: mmw:problem"
  [ "$(grep -cF 'gh :: issue :: edit :: 83 ::' "$MMW_TEST_LOG")" = 1 ] \
    || fail "the problem's kind should change in one edit"
  has "gh :: issue :: close :: 90 :: --duplicate-of :: 83"

  echo "--- became-ticket onto a lesson"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 became-ticket 81)"
  [ "$code" = 0 ] || fail "a lesson should become a ticket, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 81 :: --add-label :: mmw:ticket :: --remove-label :: mmw:lesson"
  [ "$(grep -cF 'gh :: issue :: edit :: 81 ::' "$MMW_TEST_LOG")" = 1 ] \
    || fail "the lesson's kind should change in one edit"
  has "gh :: issue :: close :: 91 :: --duplicate-of :: 81"

  echo "--- run again on a target that is already a ticket"
  : > "$MMW_TEST_LOG"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 92 became-ticket 82)"
  [ "$code" = 0 ] || fail "an existing ticket should accept the route, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  has "gh :: issue :: close :: 92 :: --duplicate-of :: 82"
  : > "$MMW_TEST_LOG"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 92 became-ticket 82)"
  [ "$code" = 0 ] || fail "the repeated route should exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: close"
  [ "$(posted_events 61 child resolution became spec | tr '\n' '|')" = \
    "child.closed child=90 resolution=became-ticket became=83 spec=76|child.closed child=91 resolution=became-ticket became=81 spec=76|child.closed child=92 resolution=became-ticket became=82 spec=76|" ] \
    || fail "each conversion should record one route: $(posted_events 61 child resolution became spec)"
}

scenario_routerefusesmapspec() {
  local code target kind child
  reset_log
  fresh_repo
  write_route_batch

  while read -r target kind child; do
    echo "--- became-ticket onto a $kind: refused, nothing done"
    : > "$MMW_TEST_LOG"
    code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 "$child" became-ticket "$target")"
    [ "$code" = 2 ] || fail "a $kind should refuse to become a ticket, got $code: $(cat "$TMP/err")"
    grep -Fq "#$target carries mmw:$kind" "$TMP/err" \
      || fail "the refusal should name #$target and mmw:$kind: $(cat "$TMP/err")"
    hasnt "gh :: issue :: edit"
    hasnt "gh :: issue :: close"
    hasnt "gh :: issue :: comment"
  done <<'ROUTES'
18 map 90
76 spec 91
ROUTES
  [ -z "$(posted_events 61)" ] || fail "no child.closed should be posted: $(posted_events 61)"

  echo "--- without a spec, a map is refused as a duplicate target too"
  reset_log
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 18, "state": "OPEN", "labels": ["mmw:map"], "parent": null},
  {"number": 61, "state": "CLOSED", "labels": ["mmw:ticket"], "parent": null,
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --field child=90 --field kind=finding)]},
  {"number": 90, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}}
]
JSON
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket 18)"
  [ "$code" = 2 ] || fail "a map without a spec should refuse to become a ticket, got $code: $(cat "$TMP/err")"
  grep -Fq "#18 carries mmw:map" "$TMP/err" || fail "the refusal should name #18 and mmw:map: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: close"
  [ -z "$(posted_events 61)" ] || fail "no child.closed should be posted: $(posted_events 61)"
}

scenario_routenospec() {
  local code
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": ["mmw:ticket"], "parent": null,
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --field child=91 --field kind=finding)]},
  {"number": 90, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}},
  {"number": 91, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}},
  {"number": 80, "state": "OPEN", "labels": ["ready-for-agent", "mmw:ticket"], "parent": {"number": 76}}
]
JSON
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket 90)"
  [ "$code" = 0 ] || fail "a standalone finding should become a ticket, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 90 :: --add-label :: mmw:ticket :: --remove-parent :: --remove-label :: mmw:child"
  hasnt "gh :: issue :: close :: 90"
  hasnt ":: --parent ::"

  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 became-ticket 80)"
  [ "$code" = 0 ] || fail "a standalone finding should close as a duplicate, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: close :: 91 :: --duplicate-of :: 80"
  hasnt "gh :: issue :: edit :: 80"
  [ "$(posted_events 61 child resolution became spec | tr '\n' '|')" = \
    "child.closed child=90 resolution=became-ticket became=90 spec=None|child.closed child=91 resolution=became-ticket became=80 spec=None|" ] \
    || fail "standalone routes should record no spec: $(posted_events 61 child resolution became spec)"

  : > "$MMW_TEST_LOG"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket 90)"
  [ "$code" = 0 ] || fail "repeated standalone conversion should exit 0, got $code"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 became-ticket 80)"
  [ "$code" = 0 ] || fail "repeated duplicate routing should exit 0, got $code"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: close"
  [ "$(posted_events 61 | grep -c child.closed)" = 2 ] || fail "a repeated route posted another child.closed"

  reset_log
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": ["mmw:ticket"], "parent": {"number": 76},
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --field child=91 --field kind=finding)]},
  {"number": 90, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}},
  {"number": 91, "state": "OPEN", "labels": ["mmw:child"], "parent": {"number": 61}},
  {"number": 80, "state": "OPEN", "labels": ["mmw:ticket"], "parent": {"number": 76}}
]
JSON
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket 90)"
  [ "$code" = 2 ] || fail "a missing event spec on a spec-backed ticket should refuse, got $code"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 became-ticket 80)"
  [ "$code" = 2 ] || fail "a duplicate with a missing event spec should refuse, got $code"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: comment"
}

scenario_missingverifyticket() {
  local code copy expected
  reset_log
  fresh_repo
  copy="$(skill_copy_for missing-verify-ticket)"
  expected="$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" reverify 76)"
  [ "$code" = 2 ] || fail "a missing verify-ticket.py should exit 2, got $code: $(cat "$TMP/err")"
  grep -Fq "$expected" "$TMP/err" || fail "the refusal omits the searched path: $(cat "$TMP/err")"
  grep -Fq 'report that to the owner' "$TMP/err" || fail "the refusal omits the next step: $(cat "$TMP/err")"
  ! grep -Fq 'pass --tools' "$TMP/err" || fail "the refusal tells the caller to use a test override"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: comment"
}

scenario_routelint() {
  local code
  reset_log
  fresh_repo
  write_route_batch
  python3 - "$TMP/tickets.json" <<'PYFIX'
import json, sys
p = sys.argv[1]
rows = json.load(open(p))
ticket = next(row for row in rows if row["number"] == 61)
ticket["body"] = ("## Parent\n\n#76, Implementation Decisions section 1\n\n"
                  "## What to build\n\n1. Export the report.\n\n"
                  "## Acceptance criteria\n\n- [ ] AC1: report exports\n"
                  "  CHECK: echo report-ok\n  EXPECT: report-ok\n  EVIDENCE: pending\n")
json.dump(rows, open(p, "w"))
PYFIX
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 fixed)"
  [ "$code" = 2 ] || fail "route fixed on a lint error expected 2, got $code: $(cat "$TMP/out") $(cat "$TMP/err")"
  grep -q 'build-point-without-criterion' "$TMP/out" "$TMP/err" || fail "lint rule not passed through"
  grep -q 'Export the report' "$TMP/out" "$TMP/err" || fail "missing build point not named"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: edit"
  hasnt "gh :: issue :: comment"
  [ -z "$(posted_events 61)" ] || fail "refused route recorded an event"
  code="$(route_in env FAKE_GH_BODY_FAILS=1 bash "$DISPATCH" "${TOOLS[@]}" route 61 90 fixed)"
  [ "$code" = 2 ] || fail "route fixed when lint cannot read expected 2, got $code"
  grep -q 'HTTP 502' "$TMP/out" "$TMP/err" || fail "tracker error not passed through"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: comment"
  echo "route fixed refused on a lint error and closed nothing"
}

scenario_route() {
  local code
  reset_log
  fresh_repo
  write_route_batch
  echo "--- fixed: the child is closed as completed and child.closed goes on its ticket"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 fixed)"
  [ "$code" = 0 ] || fail "route fixed expected exit 0, got $code: $(cat "$TMP/out") $(cat "$TMP/err")"
  has "gh :: issue :: close :: 90 :: --reason :: completed"

  echo "--- stale: closed as not planned"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 stale invalid)"
  [ "$code" = 0 ] || fail "route stale expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: close :: 91 :: --reason :: not planned"

  echo "--- became-ticket as itself: relabelled mmw:ticket, left open, under the spec its child.opened names — never the map the tree would give"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 92 became-ticket 92)"
  [ "$code" = 0 ] || fail "route became-ticket expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: label :: create"
  has "gh :: issue :: edit :: 92 :: --add-label :: mmw:ticket :: --remove-label :: mmw:child"
  hasnt ":: --parent :: 18"
  hasnt "gh :: issue :: close :: 92"

  echo "--- became-ticket as another ticket already under the spec: no move, and the child closes as its duplicate"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 93 became-ticket 80)"
  [ "$code" = 0 ] || fail "route became-ticket to another ticket expected exit 0, got $code: $(cat "$TMP/err")"
  grep -Fxq 'gh :: issue :: edit :: 80 :: --add-label :: mmw:ticket' "$MMW_TEST_LOG" \
    || fail "the target without a kind should only gain mmw:ticket"
  hasnt "gh :: issue :: edit :: 80 :: --add-label :: mmw:ticket :: --parent"
  has "gh :: issue :: close :: 93 :: --duplicate-of :: 80"

  echo "--- each route is one child.closed on the ticket the child came from, naming the spec"
  [ "$(posted_events 61 child resolution became spec | tr '\n' '|')" = \
    "child.closed child=90 resolution=fixed became=None spec=76|child.closed child=91 resolution=stale became=None spec=76|child.closed child=92 resolution=became-ticket became=92 spec=76|child.closed child=93 resolution=became-ticket became=80 spec=76|" ] \
    || fail "child.closed events: $(posted_events 61 child resolution became spec)"
  posted_events 61 commit | head -n 1 | grep -Eq "^child.closed commit=[0-9a-f]{40}$" \
    || fail "a fixed child names the commit it was fixed on: $(posted_events 61 commit)"

  echo "--- run again, a route already recorded does nothing and says so"
  : > "$MMW_TEST_LOG"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 92 became-ticket 92)"
  [ "$code" = 0 ] || fail "a route already recorded should exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  [ "$(posted_events 61 | grep -c child.closed)" = 4 ] || fail "a second child.closed was posted"

  echo "--- routed another way already: refused, nothing done"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 stale invalid)"
  [ "$code" = 2 ] || fail "a child already routed fixed should refuse stale, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: close"

  echo "--- cut short after its tracker steps began, the same command finishes it"
  reset_log
  write_route_batch
  code="$(route_in env FAKE_GH_CLOSE_FAILS=1 bash "$DISPATCH" "${TOOLS[@]}" route 61 93 became-ticket 80)"
  [ "$code" = 1 ] || fail "a close the tracker refused should exit 1, got $code: $(cat "$TMP/err")"
  [ -z "$(posted_events 61)" ] || fail "no child.closed before the close: $(posted_events 61)"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 93 became-ticket 80)"
  [ "$code" = 0 ] || fail "the re-run should finish it, got $code: $(cat "$TMP/err")"
  hasnt ":: --parent :: 18"
  posted_events 61 child spec | grep -qx "child.closed child=93 spec=76" \
    || fail "the re-run records the spec its child.opened names: $(posted_events 61 child spec)"

  echo "--- a child the ticket did not open, and a resolution that is none of the three, change nothing"
  reset_log
  write_route_batch
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 95 fixed)"
  [ "$code" = 2 ] || fail "a child with no child.opened should exit 2, got $code: $(cat "$TMP/err")"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 done)"
  [ "$code" = 2 ] || fail "an unknown resolution should exit 2, got $code: $(cat "$TMP/err")"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket)"
  [ "$code" = 2 ] || fail "became-ticket with no ticket should exit 2, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: edit"
  [ -z "$(posted_events 61)" ] || fail "nothing should be posted: $(posted_events 61)"
}

# #61 is a ticket under spec #76 (spec #76 itself carries no row, so the tree's own
# root-children fallback treats every listed ticket as one of #76's own); its events
# carry a child.opened for each of #90-#93, and #93 is a deferred child, not a finding.
write_findings_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "children": [90, 91, 92, 93],
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --spec 76 --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --spec 76 --field child=91 --field kind=finding),
                $(ev child.opened 61 "Opened #92 (finding)" --spec 76 --field child=92 --field kind=finding),
                $(ev child.opened 61 "Opened #93 (deferred)" --spec 76 --field child=93 --field kind=deferred)]},
  {"number": 90, "state": "OPEN", "labels": ["mmw:child"]},
  {"number": 91, "state": "OPEN", "labels": ["mmw:child"]},
  {"number": 92, "state": "OPEN", "labels": ["mmw:child"]},
  {"number": 93, "state": "OPEN", "labels": ["mmw:child"]}
]
JSON
}

scenario_findings() {
  local code
  reset_log
  fresh_repo
  write_findings_batch
  echo "--- findings lists every open finding under the ticket whose fold names it, and skips the deferred child"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" findings 76)"
  [ "$code" = 0 ] || fail "findings expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(awk '{print $1, $2}' "$TMP/out" | sort)" = "$(printf '61 90\n61 91\n61 92\n' | sort)" ] \
    || fail "findings should list #90, #91 and #92 under #61, not the deferred #93: $(cat "$TMP/out")"

  echo "--- a finding the tracker shows closed drops out of the list"
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
path = sys.argv[1]
rows = json.load(open(path))
for row in rows:
    if row["number"] == 90:
        row["state"] = "CLOSED"
json.dump(rows, open(path, "w"))
PY
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" findings 76)"
  [ "$code" = 0 ] || fail "findings after a close expected 0, got $code: $(cat "$TMP/err")"
  [ "$(awk '{print $1, $2}' "$TMP/out" | sort)" = "$(printf '61 91\n61 92\n' | sort)" ] \
    || fail "findings should drop #90 once the tracker shows it closed: $(cat "$TMP/out")"
}

scenario_specfield() {
  local code
  echo "--- outside a batch command, the events a command writes still name the ticket's spec"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"], "parent": {"number": 76}}]
JSON
  seed_agent 61 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" resume 61 "continue")"
  [ "$code" = 0 ] || fail "resume expected exit 0, got $code: $(cat "$TMP/err")"
  set_agent_status agt_61_worker closed
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(posted_events 61 spec | tr '\n' '|')" = "worker.started spec=76|worker.resumed spec=76|worker.retracted spec=76|" ] \
    || fail "every event should carry spec 76: $(posted_events 61 spec)"
}

write_open_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n"},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"],
   "body": "## Parent\\n\\n#76\\n"},
  {"number": 65, "state": "OPEN", "labels": ["needs-triage"],
   "comments": [$(ev ticket.returned 65 "HANDOFF REQUIRED: 1 abandoned (decision), 0 unmet, 0 met of 1")]}
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

scenario_suspend() {
  local code
  fresh_repo
  reset_log
  write_open_batch
  open_a_night
  # The night's starts are real sessions now; this scenario seeds the one it wants.
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"

  [ -d "$TMP/repo/.worktrees/issue-61" ] || fail "the night did not open a worktree for #61"
  [ -d "$TMP/repo/.worktrees/issue-63" ] || fail "the night did not open a worktree for #63"
  seed_workspace 65

  seed_agent 61 worker
  seed_agent 99 worker 99
  seed_foreign_workspace
  git -C "$TMP/repo" worktree remove --force "$TMP/repo/.worktrees/issue-65" >/dev/null
  claim_tickets 61 63

  echo "--- suspend archives the live worker, comments, gives the claims back"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"

  # `--force` is the whole point: without it the real CLI refuses a running agent, and a
  # worker mid-turn is exactly what suspend exists to end.
  has "paseo :: archive :: --force :: agt_61_worker"
  hasnt "agt_99_worker"
  hasnt "paseo :: stop"
  has "gh :: issue :: view :: 61 :: --json :: comments"
  hasnt "wks_foreign_61"
  hasnt "workspace :: archive"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"
  [ "$(count_of "status.py --worker-grades")" = 1 ] \
    || fail "worker-grades should be read once, got $(count_of "status.py --worker-grades")"
  [ "$(count_of "gh :: api :: graphql")" = 1 ] \
    || fail "the batch should be read once, got $(count_of "gh :: api :: graphql")"
  hasnt "/sub_issues"
  [ -d "$TMP/repo/.worktrees/issue-61" ] || fail "the worktree for #61 was removed"
  [ -d "$TMP/repo/.worktrees/issue-63" ] || fail "the worktree for #63 was removed"
  git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-61 >/dev/null \
    || fail "branch issue-61 was removed"
  git -C "$TMP/repo" rev-parse --verify --quiet refs/heads/issue-63 >/dev/null \
    || fail "branch issue-63 was removed"

  echo "--- every ticket still in the agent queue carries one comment saying the night was suspended"
  has "gh :: issue :: comment :: 61 :: --body"
  has "gh :: issue :: comment :: 63 :: --body"
  has "gh :: issue :: comment :: 76 :: --body"
  [ "$(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")" = 3 ] \
    || fail "expected the spec and two tickets told, got $(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")"
  posted_events 61 interrupted | grep -qx "spec.suspended interrupted=agt_61_worker" \
    || fail "#61 should carry spec.suspended naming its worker: $(posted_events 61 interrupted)"
  posted_events 61 reason | grep -qx "ticket.released reason=suspended" \
    || fail "#61 should carry ticket.released (suspended): $(posted_events 61 reason)"
  hasnt "gh :: issue :: comment :: 65"

  echo "--- the summary line counts what was undone"
  grep -q 'suspend #76: stopped 1, commented 2, claims given back 2' "$TMP/out" \
    || fail "the summary line is wrong: $(cat "$TMP/out")"
  [ -z "$(relay_now)" ] || fail "suspend should have stopped the night's relay: $(relay_now)"

  # The night is opened again before it is taken up again.
  fake_relay

  echo "--- advance after suspend re-dispatches the same tickets into the standing workspaces"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance after suspend exited $code: $(cat "$TMP/err")"
  grep -q '"title": "#61 worker"' "$MMW_FAKE_PASEO_STATE/runs.jsonl" \
    || fail "advance after suspend should re-dispatch #61: $(cat "$TMP/out")"
  hasnt "workspace :: create"
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
  grep -q "spec #76" "$TMP/out" || fail "the spec is missing from the header: $(cat "$TMP/out")"

  echo "--- the table comes off the tickets alone: no runner is asked, and one that fails changes nothing"
  hasnt "paseo ::"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_PASEO_SCENARIO=ls-fail \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "expected exit 0 with paseo failing, got $code: $(cat "$TMP/err")"
  hasnt "paseo ::"

  echo "--- a live worker on the ticket's events shows on its row, with its runner and session"
  reset_log
  runner_line 61 orca term_4 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  grep -q "1 live" "$TMP/out" || fail "the header should count the live worker: $(cat "$TMP/out")"
  grep -E "^ #61 +orca +term_4 +live" "$TMP/out" >/dev/null \
    || fail "the row should name orca, term_4 and live: $(cat "$TMP/out")"

  echo "--- a non-numeric spec is a refusal, exit 2"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" status abc)"
  [ "$code" = 2 ] || fail "expected exit 2 for a non-numeric spec, got $code: $(cat "$TMP/err")"
}

RUNNER="$SKILL/scripts/runners/paseo.sh"

run_runner() {
  (cd "$TMP/repo" && bash "$RUNNER" "$@") > "$TMP/out" 2> "$TMP/err"
  echo "$?"
}

scenario_runnerstart() {
  local code copy
  echo "--- the adapter leaves no temporary file behind and says nothing on a clean start"
  reset_log
  fresh_repo
  mkdir -p "$TMP/tmpdir"
  rm -rf "$TMP/tmpdir"/*
  code="$(run_dispatch env TMPDIR="$TMP/tmpdir" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  ! grep -q "unbound variable" "$TMP/err" || fail "the adapter failed on its way out: $(cat "$TMP/err")"
  [ -z "$(ls -A "$TMP/tmpdir")" ] || fail "start leaked temporary files: $(ls -A "$TMP/tmpdir")"

  echo "--- without the adapter, start refuses and starts nothing"
  copy="$(skill_copy_for start)"
  rm -f "$copy/scripts/runners/paseo.sh"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 with no adapter, got $code: $(cat "$TMP/err")"
  grep -q "runners/paseo.sh" "$TMP/err" \
    || fail "the refusal should name the adapter: $(cat "$TMP/err")"
  nothing_printed
  never_ran
}

scenario_runnersend() {
  local code
  echo "--- the adapter itself maps delivered to exit 0"
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
    "labels": {"mmw.ticket": "61", "mmw.kind": "worker"},
}]))
'
  code="$(run_runner send agt_w61 continue)"
  [ "$code" = 0 ] || fail "adapter send delivered expected 0, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_w61 :: continue"

  echo "--- the adapter itself maps busy to exit 3"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_SEND_FAILS=1 run_runner send agt_61_worker continue)"
  [ "$code" = 3 ] || fail "adapter send busy expected 3, got $code: $(cat "$TMP/err")"

  echo "--- the adapter itself maps a missing session to exit 2 and does not send"
  reset_log
  code="$(run_runner send agt_missing continue)"
  [ "$code" = 2 ] || fail "adapter send missing expected 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"
}

scenario_runnerliveness() {
  local code answer
  echo "--- listed running is alive"
  reset_log
  seed_agent 61 worker
  code="$(run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" = alive ] || fail "running should be alive, got: $answer"

  echo "--- idle is alive (a turn that ended is still on the hook)"
  reset_log
  python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
path.write_text(json.dumps([{
    "id": "agt_61_worker",
    "name": "#61 worker",
    "status": "idle",
    "cwd": "/tmp/issue-61",
    "labels": {"mmw.ticket": "61", "mmw.kind": "worker"},
}]))
'
  code="$(run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = alive ] || fail "idle should be alive, got: $(cat "$TMP/out")"

  echo "--- not listed is stopped"
  reset_log
  code="$(run_runner liveness agt_missing)"
  [ "$code" = 0 ] || fail "liveness expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = stopped ] || fail "missing should be stopped, got: $(cat "$TMP/out")"

  echo "--- closed is stopped"
  reset_log
  python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
path.write_text(json.dumps([{
    "id": "agt_61_worker",
    "name": "#61 worker",
    "status": "closed",
    "cwd": "/tmp/issue-61",
    "labels": {"mmw.ticket": "61", "mmw.kind": "worker"},
}]))
'
  code="$(run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = stopped ] || fail "closed should be stopped, got: $(cat "$TMP/out")"

  echo "--- ls cannot be asked is unknown, not alive"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_PASEO_SCENARIO=ls-fail run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0 when it cannot ask, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "cannot-ask should be unknown, got: $answer"

  echo "--- unreadable ls output is unknown, not alive"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_PASEO_SCENARIO=ls-garbage run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0 on garbage, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "garbage should be unknown, got: $answer"

  echo "--- a listed agent with no recognisable status is unknown, not alive"
  reset_log
  python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
path.write_text(json.dumps([{
    "id": "agt_61_worker",
    "name": "#61 worker",
    "status": "",
    "cwd": "/tmp/issue-61",
    "labels": {"mmw.ticket": "61", "mmw.kind": "worker"},
}]))
'
  code="$(run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "empty status should be unknown, got: $answer"
}

PASEO_RUNNER="$SKILL/scripts/runners/paseo.sh"
HERDR_RUNNER="$SKILL/scripts/runners/herdr.sh"
ORCA_RUNNER="$SKILL/scripts/runners/orca.sh"

scenario_runnerparity() {
  local code
  echo "=== paseo adapter"
  RUNNER="$PASEO_RUNNER"

  echo "--- start succeeds"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd "$TMP/repo" --prompt hi --skip-approval)"
  [ "$code" = 0 ] || fail "paseo start expected 0, got $code: $(cat "$TMP/err")"

  echo "--- start takes no --label: a usage error, and nothing is started"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd "$TMP/repo" --prompt hi --label mmw.ticket=61)"
  [ "$code" = 2 ] || fail "paseo start with --label expected usage 2, got $code: $(cat "$TMP/err")"
  never_ran

  echo "=== herdr adapter"
  RUNNER="$HERDR_RUNNER"

  echo "--- start succeeds, pane exists before agent start"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd "$TMP/repo" --prompt hi --skip-approval)"
  [ "$code" = 0 ] || fail "herdr start expected 0, got $code: $(cat "$TMP/err")"
  has "herdr :: tab :: create"
  has "herdr :: agent :: start"
  local created started
  created="$(line_of 'herdr :: tab :: create')"
  started="$(line_of 'herdr :: agent :: start')"
  [ "$created" -gt 0 ] && [ "$started" -gt 0 ] && [ "$created" -lt "$started" ] \
    || fail "tab create must precede agent start"
  grep -q -- '--pane' "$MMW_TEST_LOG" || fail "agent start must name a pane"

  echo "--- the reviewer and the worker of one worktree get different session names"
  reset_log
  run_runner start --host codex --model gpt-5.6-sol --effort high \
    --cwd "$TMP/repo" --prompt hi --title "#61 reviewer" >/dev/null
  [ "$(cat "$TMP/out")" = repo-reviewer ] || fail "the session name should carry the kind: $(cat "$TMP/out")"
  hasnt "herdr :: pane :: split"
  hasnt "herdr :: pane :: rename"
  hasnt "herdr :: pane :: report-metadata"
  hasnt "herdr :: pane :: layout"
  hasnt "herdr :: tab :: close"
  hasnt "herdr :: pane :: close"

  echo "--- start takes no --label: a usage error, and no tab is opened"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd "$TMP/repo" --prompt hi --label mmw.ticket=61)"
  [ "$code" = 2 ] || fail "herdr start with --label expected usage 2, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: tab :: create"

  echo "--- send three states"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(run_runner send agt_w61 continue)"
  [ "$code" = 0 ] || fail "herdr delivered expected 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: prompt"
  has "--until :: working"
  has "--until :: blocked"
  has "--wait"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=send-blocked run_runner send agt_w61 continue)"
  [ "$code" = 3 ] || fail "herdr busy expected 3, got $code: $(cat "$TMP/err")"
  reset_log
  code="$(run_runner send agt_missing continue)"
  [ "$code" = 2 ] || fail "herdr missing expected 2, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: prompt"

  echo "=== orca adapter"
  RUNNER="$ORCA_RUNNER"

  echo "--- start succeeds, one create, path: selector, no worktree enumeration"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd . --prompt hi --skip-approval)"
  [ "$code" = 0 ] || fail "orca start expected 0, got $code: $(cat "$TMP/err")"
  [ -n "$(cat "$TMP/out")" ] || fail "orca start should print a session id"
  has "orca :: terminal :: create"
  [ "$(count_of 'orca :: terminal :: create')" = 1 ] \
    || fail "start must be one terminal create, got $(count_of 'orca :: terminal :: create')"
  has "--command"
  has "--title"
  has "--json"
  worktree="$(arg_after --worktree)"
  case "$worktree" in
    path:/*) ;;
    *) fail "start must address by path:<absolute>, got: $worktree" ;;
  esac
  hasnt "orca :: worktree :: ps"
  hasnt "orca :: worktree :: rm"
  hasnt "orca :: worktree :: create"
  hasnt "orca :: orchestration"
  [ "$(arg_after --title)" = "$(basename -- "${worktree#path:}")" ] \
    || fail "a start with no title should be named after its worktree, got: $(arg_after --title)"

  echo "--- the tab carries the title dispatch passes, so one ticket's sessions differ"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd . --prompt hi --skip-approval --title "#61 reviewer")"
  [ "$code" = 0 ] || fail "orca start with a title expected 0, got $code: $(cat "$TMP/err")"
  [ "$(arg_after --title)" = "#61 reviewer" ] \
    || fail "the tab should be named '#61 reviewer', got: $(arg_after --title)"

  echo "--- the first prompt is the last argument of the command exec runs, and nothing is typed"
  reset_log
  local first="Use the implement skill on #61. Don't ask 'Shall I…?'"
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd . --prompt "$first" --skip-approval)"
  [ "$code" = 0 ] || fail "orca start expected 0, got $code: $(cat "$TMP/err")"
  MMW_FIRST="$first" python3 -c '
import json, os, shlex, sys
argv = shlex.split(json.load(open(sys.argv[1]))[-1]["command"])
assert argv[:2] == ["exec", "codex"], argv
assert argv[-1] == os.environ["MMW_FIRST"], argv
' "$MMW_FAKE_ORCA_STATE/terminals.json" \
    || fail "the command should be exec codex … with the prompt last: $(arg_after --command)"
  hasnt "orca :: terminal :: send"
  hasnt "--for :: tui-idle"
  grep -q -- '--for :: exit' "$MMW_TEST_LOG" \
    || fail "start should wait for the host to exit: $(cat "$MMW_TEST_LOG")"

  echo "--- start takes no --label: a usage error, and no terminal is created"
  reset_log
  code="$(run_runner start --host codex --model gpt-5.6-sol --effort high \
          --cwd . --prompt hi --label mmw.ticket=61)"
  [ "$code" = 2 ] || fail "orca start with --label expected usage 2, got $code: $(cat "$TMP/err")"
  hasnt "orca :: terminal :: create"

  echo "--- send three states"
  reset_log
  seed_orca_terminal term_w61
  code="$(run_runner send term_w61 continue)"
  [ "$code" = 0 ] || fail "orca delivered expected 0, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: send"
  has "--enter"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=accepted-only run_runner send term_w61 continue)"
  [ "$code" = 4 ] || fail "orca took the text with no turn start: handed over, 4, got $code: $(cat "$TMP/err")"
  reset_log
  code="$(run_runner send term_missing continue)"
  [ "$code" = 2 ] || fail "orca missing expected 2, got $code: $(cat "$TMP/err")"
  hasnt "orca :: terminal :: send"

  echo "--- liveness three states"
  reset_log
  seed_orca_terminal term_w61
  code="$(run_runner liveness term_w61)"
  [ "$code" = 0 ] || fail "orca liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = alive ] || fail "orca listed should be alive, got: $(cat "$TMP/out")"
  has "orca :: terminal :: list"
  has "orca :: terminal :: wait"
  grep -q -- '--for :: tui-idle' "$MMW_TEST_LOG" \
    || fail "liveness must ask tui-idle: $(cat "$MMW_TEST_LOG")"
  grep -q -- '--for :: exit' "$MMW_TEST_LOG" \
    || fail "liveness must ask exit: $(cat "$MMW_TEST_LOG")"
  hasnt "orca :: worktree :: ps"
  reset_log
  code="$(run_runner liveness term_missing)"
  [ "$(cat "$TMP/out")" = stopped ] || fail "orca missing should be stopped, got: $(cat "$TMP/out")"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SCENARIO=list-fail run_runner liveness term_w61)"
  [ "$(cat "$TMP/out")" = unknown ] || fail "orca cannot-ask should be unknown, got: $(cat "$TMP/out")"

  echo "--- a running process whose UI is not idle is still alive"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SCENARIO=wait-busy run_runner liveness term_w61)"
  [ "$(cat "$TMP/out")" = alive ] \
    || fail "running-not-idle should be alive, got: $(cat "$TMP/out")"

  RUNNER="$PASEO_RUNNER"
}

scenario_herdrworkingsend() {
  local code answer
  RUNNER="$HERDR_RUNNER"
  echo "--- already working: nothing is sent, exit 3, so sending again is safe"
  reset_log
  seed_herdr_agent agt_w61 working
  code="$(run_runner send agt_w61 continue)"
  [ "$code" = 3 ] || fail "a working agent was sent nothing: 3, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: prompt"
  has "herdr :: agent :: list"

  echo "--- a prompt that stalled or timed out was typed: exit 4, never 3"
  for stall in send-stalled send-timeout; do
    reset_log
    seed_herdr_agent agt_w61 idle
    code="$(MMW_FAKE_HERDR_PROMPT="$stall" run_runner send agt_w61 continue)"
    [ "$code" = 4 ] || fail "$stall was handed over: 4, got $code: $(cat "$TMP/err")"
  done
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_PROMPT=send-blocked run_runner send agt_w61 continue)"
  [ "$code" = 3 ] || fail "an agent at an approval is sent nothing: 3, got $code"
  RUNNER="$PASEO_RUNNER"
}

scenario_herdrliveness() {
  local code answer
  RUNNER="$HERDR_RUNNER"

  echo "--- listed, even as done, is not stopped; the list is what was asked"
  reset_log
  seed_herdr_agent agt_w61 done
  code="$(run_runner liveness agt_w61)"
  [ "$code" = 0 ] || fail "liveness expected 0, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" != stopped ] || fail "a listed agent must not be stopped, got: $answer"
  has "herdr :: agent :: list"
  hasnt "herdr :: agent :: wait"
  hasnt "--until :: done"

  echo "--- listed idle is alive, still without agent wait"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(run_runner liveness agt_w61)"
  [ "$(cat "$TMP/out")" = alive ] || fail "listed idle should be alive, got: $(cat "$TMP/out")"
  hasnt "herdr :: agent :: wait"

  echo "--- not listed is stopped"
  reset_log
  code="$(run_runner liveness agt_missing)"
  [ "$(cat "$TMP/out")" = stopped ] || fail "missing should be stopped, got: $(cat "$TMP/out")"
  has "herdr :: agent :: list"
  hasnt "herdr :: agent :: wait"

  echo "--- list cannot be asked is unknown, not stopped"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=list-fail run_runner liveness agt_w61)"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "cannot-ask should be unknown, got: $answer"
  hasnt "herdr :: agent :: wait"

  RUNNER="$PASEO_RUNNER"
}

scenario_orcaunobserved() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a terminal whose program Orca cannot observe took the text: unknown, exit 4, said why"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=unobserved run_runner send term_w61 '#61 ticket.passed')"
  [ "$code" = 4 ] || fail "an unobserved terminal must answer unknown 4, got $code: $(cat "$TMP/err")"

  echo "--- a list that cannot be read sends nothing: 3, and terminal send is not run"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SCENARIO=list-fail run_runner send term_w61 '#61 ticket.passed')"
  [ "$code" = 3 ] || fail "an unreadable list expected 3, got $code: $(cat "$TMP/err")"
  hasnt "orca :: terminal :: send"

  echo "--- Orca refusing the send with an error of its own typed nothing: 3"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=refused run_runner send term_w61 '#61 ticket.passed')"
  [ "$code" = 3 ] || fail "a refused send expected 3, got $code: $(cat "$TMP/err")"

  echo "--- a host whose delivery Orca cannot report still starts: the handle, exit 0, its terminal kept"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SEND=unobserved run_runner start --host codex --model gpt-5.6-sol --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 0 ] || fail "an unobserved host is a start, expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = term_1 ] || fail "start should print the handle: $(cat "$TMP/out")"
  hasnt "orca :: terminal :: send"
  hasnt "orca :: terminal :: close"
  RUNNER="$PASEO_RUNNER"
}

scenario_runnerself() {
  local code
  echo "--- paseo: PASEO_AGENT_ID is the session; without it this is not a Paseo agent"
  reset_log
  RUNNER="$PASEO_RUNNER"
  code="$(PASEO_AGENT_ID=agt_main run_runner self)"
  [ "$code" = 0 ] && [ "$(cat "$TMP/out")" = agt_main ] || fail "paseo self should print agt_main, got $code: $(cat "$TMP/out") $(cat "$TMP/err")"
  code="$(run_runner self)"
  [ "$code" = 3 ] || fail "paseo self outside Paseo should be 3, got $code"

  echo "--- orca: ORCA_TERMINAL_HANDLE is the session; an Orca terminal without it is refused"
  RUNNER="$ORCA_RUNNER"
  code="$(ORCA_TERMINAL_HANDLE=term_main run_runner self)"
  [ "$code" = 0 ] && [ "$(cat "$TMP/out")" = term_main ] || fail "orca self should print term_main, got $code: $(cat "$TMP/out") $(cat "$TMP/err")"
  code="$(TERM_PROGRAM=Orca run_runner self)"
  [ "$code" = 1 ] || fail "an Orca terminal with no handle should be refused 1, got $code"
  code="$(env -u TERM_PROGRAM bash -c 'cd "$1" && bash "$2" self' _ "$TMP/repo" "$ORCA_RUNNER" 2>/dev/null; echo "$?")"
  [ "$code" = 3 ] || fail "orca self outside Orca should be 3, got $code"

  echo "--- herdr: the name of the agent in HERDR_PANE_ID is the session"
  RUNNER="$HERDR_RUNNER"
  echo '[{"name": "main-h", "agent_status": "idle", "pane_id": "w1:p2"}, {"name": "", "agent_status": "idle", "pane_id": "w1:p3"}]' \
    > "$MMW_FAKE_HERDR_STATE/agents.json"
  code="$(HERDR_ENV=1 HERDR_PANE_ID=w1:p2 run_runner self)"
  [ "$code" = 0 ] && [ "$(cat "$TMP/out")" = main-h ] || fail "herdr self should print main-h, got $code: $(cat "$TMP/out") $(cat "$TMP/err")"
  code="$(HERDR_ENV=1 HERDR_PANE_ID=w1:p3 run_runner self)"
  [ "$code" = 1 ] || fail "an unnamed agent should be refused 1, got $code"
  [ ! -s "$TMP/out" ] || fail "an unnamed agent should print no session: $(cat "$TMP/out")"
  code="$(HERDR_ENV=1 HERDR_PANE_ID=w1:p9 run_runner self)"
  [ "$code" = 1 ] || fail "a pane with no agent should be refused 1, got $code"
  code="$(HERDR_ENV=1 run_runner self)"
  [ "$code" = 1 ] || fail "HERDR_ENV without a pane should be refused 1, got $code"
  code="$(env -u HERDR_ENV bash -c 'cd "$1" && bash "$2" self' _ "$TMP/repo" "$HERDR_RUNNER" 2>/dev/null; echo "$?")"
  [ "$code" = 3 ] || fail "herdr self outside Herdr should be 3, got $code"
  RUNNER="$PASEO_RUNNER"

  echo "--- dispatch.sh self prints the pair, with no models.json needed"
  code="$(run_dispatch env MMW_HOME="$TMP/no-such-home" PASEO_AGENT_ID=agt_self bash "$DISPATCH" self)"
  [ "$code" = 0 ] || fail "self expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = "$(printf 'paseo\tagt_self')" ] || fail "self should print paseo<TAB>agt_self: $(cat "$TMP/out")"
  code="$(run_dispatch env -u TERM_PROGRAM -u HERDR_ENV bash "$DISPATCH" self)"
  [ "$code" = 2 ] || fail "self outside any runner expected 2, got $code"
}

scenario_open() {
  local code pid
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  echo "--- open opens the spec's watch with this session as its orchestrator, starts the relay, and writes spec.opened"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "spec 76's orchestrator should be agt_main: $(cat "$STATE_DIR/watches.json" 2>&1)"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "a relay should be watching spec 76: $(relay_now)" ;; esac
  posted_events 76 runner session | grep -qx "spec.opened runner=paseo session=agt_main" \
    || fail "#76 should carry spec.opened naming the orchestrator: $(posted_events 76 runner session)"

  echo "--- the relay open started reads the tracker on its own"
  for _ in $(seq 1 100); do
    grep -qF "repos/o/r/issues/76/sub_issues" "$MMW_TEST_LOG" && break
    sleep 0.1
  done
  has "gh :: api :: --paginate :: --slurp :: repos/o/r/issues/76/sub_issues?per_page=100"

  echo "--- opening the same night again keeps the one relay"
  pid="$(relay_now | cut -d' ' -f1)"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "a second open of #76 expected 0, got $code: $(cat "$TMP/err")"
  [ "$(relay_now | cut -d' ' -f1)" = "$pid" ] || fail "the relay should be the same process: $pid, now $(relay_now)"

  echo "--- another night in this repository, opened by another session, joins the one relay with its own orchestrator"
  seed_main_agent agt_other
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 77)"
  [ "$code" = 0 ] || fail "open 77 expected 0, got $code: $(cat "$TMP/err")"
  [ "$(relay_now | cut -d' ' -f1)" = "$pid" ] || fail "the second night should join relay $pid: $(relay_now)"
  [ "$(watch_main spec:77)" = "paseo agt_other" ] || fail "spec 77's orchestrator should be agt_other: $(cat "$STATE_DIR/watches.json")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "spec 76's orchestrator should still be agt_main: $(cat "$STATE_DIR/watches.json")"
  posted_events 77 runner session | grep -qx "spec.opened runner=paseo session=agt_other" \
    || fail "#77 should carry spec.opened naming its orchestrator: $(posted_events 77 runner session)"

  echo "--- a ticket of an open night is refused a watch of its own, and the night keeps its orchestrator"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 61)"
  [ "$code" = 2 ] || fail "open-ticket 61 expected 2, got $code"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "a refused open must not touch spec 76's orchestrator: $(cat "$STATE_DIR/watches.json")"
  [ -z "$(watch_main tickets:61)" ] || fail "no watch on #61 should be open: $(cat "$STATE_DIR/watches.json")"

  echo "--- summary closes its night's watch, and the relay goes on for the other night"
  cat > "$TMP/tickets.json" <<'JSON'
[{"number":61,"state":"CLOSED","labels":[],"comments":[]},
 {"number":63,"state":"CLOSED","labels":[],"comments":[]}]
JSON
  summary_ready_fixture 76 night
  summary_ready_fixture 77 night
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in "$pid "'{"spec": 77}') ;; *) fail "relay $pid should watch spec 77 alone: $(relay_now)" ;; esac

  echo "--- the last night's summary ends the relay"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 77)"
  [ "$code" = 0 ] || fail "summary 77 expected 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "summary should have stopped the relay: $(relay_now)"
  kill -0 "$pid" 2>/dev/null && fail "relay pid $pid should be gone"
  no_relay
}

scenario_openticketnocheck() {
  local code
  fresh_repo
  reset_log
  no_relay
  seed_main_agent agt_main
  git -C "$TMP/repo" rm -q scripts/check
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "no check"
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}]
JSON
  echo "--- open-ticket refuses a repository with no scripts/check, and opens no watch"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 61)"
  [ "$code" = 2 ] || fail "open-ticket expected 2, got $code: $(cat "$TMP/err")"
  grep -q 'scripts/check' "$TMP/err" || fail "the refusal does not name scripts/check: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "open-ticket started a relay: $(relay_now)"
  echo "--- so does send worker, before anything starts"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" send worker 61)"
  [ "$code" = 2 ] || fail "send worker expected 2, got $code: $(cat "$TMP/err")"
  never_ran
}

scenario_opentakeover() {
  local code
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"

  echo "--- status on an open night says whom its wakes go to, and that it is the session asking"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "status expected 0, got $code: $(cat "$TMP/err")"
  ! grep -qF "dispatch.sh open 76" "$TMP/out" \
    || fail "status from agt_main should not tell it to take the night over: $(tail -2 "$TMP/out")"

  echo "--- asked from another session, status says the wakes are not its own and names open"
  seed_main_agent agt_new
  code="$(run_dispatch env PASEO_AGENT_ID=agt_new FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "status expected 0, got $code: $(cat "$TMP/err")"
  grep -qF "dispatch.sh open 76" "$TMP/out" \
    || fail "status should say the wakes go elsewhere: $(tail -2 "$TMP/out")"

  echo "--- open from the new session takes the night's wakes"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_new FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "a second open of #76 from agt_new expected 0, got $code: $(cat "$TMP/err")"
  [ "$(watch_main spec:76)" = "paseo agt_new" ] \
    || fail "spec 76's orchestrator should now be agt_new: $(cat "$STATE_DIR/watches.json" 2>&1)"
  [ "$(posted_events 76 runner session | tail -1)" = "spec.opened runner=paseo session=agt_new" ] \
    || fail "#76's newest spec.opened should name agt_new: $(posted_events 76 runner session)"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_new FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" status 76)"
  [ "$code" = 0 ] || fail "status expected 0, got $code: $(cat "$TMP/err")"
  ! grep -qF "dispatch.sh open 76" "$TMP/out" \
    || fail "status from agt_new should not tell it to take the night over: $(tail -2 "$TMP/out")"
  no_relay
}

scenario_openrefused() {
  local code
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  write_open_batch
  echo "--- a session no adapter can name is refused, and nothing is opened"
  reset_log
  no_relay
  code="$(run_dispatch env -u TERM_PROGRAM -u HERDR_ENV FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code: $(cat "$TMP/err")"
  [ ! -f "$STATE_DIR/watches.json" ] || fail "no watch should be open: $(cat "$STATE_DIR/watches.json")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"
  hasnt "gh :: issue :: comment :: 76"

  echo "--- an Orca terminal whose handle cannot be read is refused by name"
  reset_log
  no_relay
  code="$(run_dispatch env -u HERDR_ENV TERM_PROGRAM=Orca FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  [ ! -f "$STATE_DIR/watches.json" ] || fail "no watch should be open: $(cat "$STATE_DIR/watches.json")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"

  echo "--- inside Herdr inside Orca, Herdr names the session: the inner runner is asked first"
  reset_log
  no_relay
  echo '[{"name": "", "agent_status": "idle", "pane_id": "w1:p3"}]' > "$MMW_FAKE_HERDR_STATE/agents.json"
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p3 ORCA_TERMINAL_HANDLE=term_outer TERM_PROGRAM=Orca \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "an unnamed Herdr agent expected 2, got $code"
  [ ! -f "$STATE_DIR/watches.json" ] || fail "the outer Orca terminal must not be made an orchestrator: $(cat "$STATE_DIR/watches.json")"

  echo "--- a session the runner shows stopped is refused"
  reset_log
  no_relay
  code="$(run_dispatch env PASEO_AGENT_ID=agt_gone FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  [ ! -f "$STATE_DIR/watches.json" ] || fail "no watch should be open: $(cat "$STATE_DIR/watches.json")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"

  echo "--- spec.opened that cannot be written closes the watch open opened, and the relay with it"
  reset_log
  no_relay
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_COMMENT_FAILS=1 FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "spec.opened" "$TMP/err" \
    || fail "the refusal should name the event that could not be written: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "the relay should have been stopped: $(relay_now)"
  [ -z "$(watch_main spec:76)" ] || fail "no watch on #76 should be open: $(cat "$STATE_DIR/watches.json")"
  no_relay
}

scenario_openticket() {
  local code
  fresh_repo
  reset_log
  no_relay
  seed_main_agent agt_main
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 90, "state": "CLOSED", "labels": [], "parent": null,
   "comments": [$(ev worker.started 90 "started" --field session=old --field runner=paseo \
                    $(start_facts "$(wt 90)" 90 worker)),
                $(ev ticket.passed 90 "ALL MET" --field branch=issue-90 --field into=main),
                $(ev ticket.landed 90 "Landed issue-90 into main" --field into=main)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  echo "--- open-ticket opens a watch of that ticket alone with this session as its orchestrator, and starts the relay"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 90)"
  [ "$code" = 0 ] || fail "open-ticket expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"tickets": [90]}'*) ;; *) fail "a relay should watch #90: $(relay_now)" ;; esac
  [ "$(watch_main tickets:90)" = "paseo agt_main" ] || fail "#90's orchestrator should be agt_main: $(cat "$STATE_DIR/watches.json")"
  hasnt "gh :: issue :: comment"

  echo "--- a ticket of a spec is not what this relay watches, so its start is refused"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start 61 expected 2, got $code"
  never_ran

  echo "--- land ends the relay open-ticket started for it"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" land 90)"
  [ "$code" = 0 ] || fail "land expected 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "land should have stopped the relay on #90: $(relay_now)"

  echo "--- land leaves a night's relay alone"
  fake_relay
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" land 90)"
  [ "$code" = 0 ] || fail "land with a night open expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "the night's relay should still run: $(relay_now)" ;; esac

  echo "--- a ticket outside the open night gets a watch of its own beside it, and the night keeps its orchestrator"
  local pid
  pid="$(relay_now | cut -d' ' -f1)"
  seed_main_agent agt_other
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 95)"
  [ "$code" = 0 ] || fail "open-ticket 95 beside the night expected 0, got $code: $(cat "$TMP/err")"
  [ "$(relay_now)" = "$pid "'{"spec": 76} {"tickets": [95]}' ] || fail "relay $pid should watch the night and #95: $(relay_now)"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "the night's orchestrator should still be agt_main: $(cat "$STATE_DIR/watches.json")"
  [ "$(watch_main tickets:95)" = "paseo agt_other" ] || fail "#95's orchestrator should be agt_other: $(cat "$STATE_DIR/watches.json")"
  no_relay
}

# A worktree on issue-61 with a commit of its own, and no `start` behind it.
self_picked_worktree() {
  mkdir -p "$(trees)"
  git -C "$TMP/repo" worktree add --quiet -b issue-61 "$(wt 61)" main
  printf 'work\n' > "$(wt 61)/work.txt"
  git -C "$(wt 61)" add work.txt
  git -C "$(wt 61)" -c user.email=t@t -c user.name=t commit -q -m work
}

# Rows in the queue the way the relay writes them, for `ack` to act on.
seed_queue() {
  mkdir -p "$STATE_DIR"
  python3 - "$STATE_DIR" <<'PY'
import json, sys
from pathlib import Path
state = Path(sys.argv[1])
at = "2026-09-10T01:00:00Z"
rows = [
    {"seq": 1, "key": "101:ticket.passed", "ticket": 61, "event": "ticket.passed", "to": "main",
     "runner": "paseo", "session": "agt_main", "at": at, "delivered": at},
    {"seq": 2, "key": "100:reviewer.reported", "ticket": 61, "event": "reviewer.reported",
     "to": "worker", "runner": "paseo", "session": "agt_wk", "at": at, "delivered": at},
    {"seq": 3, "key": "102:ticket.returned", "ticket": 62, "event": "ticket.returned", "to": "main",
     "runner": "paseo", "session": "agt_main", "at": at, "delivered": None},
]
(state / "queue.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
(state / "queue.seq").write_text("3\n")
(state / "seen.json").write_text(json.dumps({"tickets": {
    "61": {"keys": ["100:reviewer.reported", "101:ticket.passed"], "mark": at, "workers": []},
    "62": {"keys": ["102:ticket.returned"], "mark": at, "workers": []}}}))
PY
}

queue_seqs() {
  python3 -c '
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
print(" ".join(str(r["seq"]) for r in rows))
' "$STATE_DIR/queue.jsonl"
}

scenario_ack() {
  local code
  fresh_repo
  reset_log
  seed_queue
  echo "--- the orchestrator acks the wake it read, by ticket and event; the worker's row stays"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 61 ticket.passed)"
  [ "$code" = 0 ] || fail "ack expected 0, got $code: $(cat "$TMP/err")"
  [ "$(queue_seqs)" = "2 3" ] || fail "only row 1 should be gone: $(queue_seqs)"

  echo "--- the same wake acked again matches no row of this session: refused, nothing removed"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack '#61' ticket.passed)"
  [ "$code" = 2 ] || fail "a second ack expected 2, got $code: $(cat "$TMP/err")"
  grep -qF "#62 ticket.returned" "$TMP/err" || fail "the refusal should list what is queued for it: $(cat "$TMP/err")"
  [ "$(queue_seqs)" = "2 3" ] || fail "nothing more should go: $(queue_seqs)"

  echo "--- the orchestrator acking the worker's wake is refused: another session's row stays"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 61 reviewer.reported)"
  [ "$code" = 2 ] || fail "acking another session's wake expected 2, got $code"
  [ "$(queue_seqs)" = "2 3" ] || fail "the worker's row must stay: $(queue_seqs)"

  echo "--- a wake that was never queued is refused"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 99 ticket.passed)"
  [ "$code" = 2 ] || fail "ack of a wake never queued expected 2, got $code"
  [ "$(queue_seqs)" = "2 3" ] || fail "nothing should be removed: $(queue_seqs)"

  echo "--- the worker acks its own wake, named by its own session"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_wk bash "$DISPATCH" "${TOOLS[@]}" ack 61 reviewer.reported)"
  [ "$code" = 0 ] || fail "the worker's ack expected 0, got $code: $(cat "$TMP/err")"
  [ "$(queue_seqs)" = "3" ] || fail "the worker's row should be gone and main's stay: $(queue_seqs)"

  echo "--- a session no adapter can name cannot ack"
  code="$(run_dispatch env -u TERM_PROGRAM -u HERDR_ENV bash "$DISPATCH" "${TOOLS[@]}" ack 62 ticket.returned)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  [ "$(queue_seqs)" = "3" ] || fail "nothing should be acked: $(queue_seqs)"
}

scenario_unopened() {
  local code
  fresh_repo
  reset_log
  no_relay
  write_open_batch
  echo "--- advance refuses a night that is not open, and touches nothing"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "advance expected 2, got $code"
  never_ran
  assert_no_wt 61
  hasnt "status.py --advance-plan"

  echo "--- start refuses a ticket no relay watches, and starts nothing"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start expected 2, got $code"
  never_ran
  assert_no_wt 61

  echo "--- a relay watching another spec does not open this one"
  fake_relay '{"spec": 80}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start expected 2, got $code"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "advance expected 2, got $code"
  never_ran
  no_relay
}

# A reboot or a crash ends the relay and leaves the night open: advance restores the watch
# for the orchestrator spec.opened names instead of reading the night as never opened.
scenario_advancerestoreswatch() {
  local code
  fresh_repo
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  post_ev 76 spec.opened --ticket '' --spec 76 --line "NIGHT OPENED" \
    --field runner=paseo --field session=agt_main --field into=main --field project=proj
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance did not restore the watch: exit $code: $(cat "$TMP/err")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "spec 76 should be watched for agt_main: $(cat "$STATE_DIR/watches.json" 2>&1)"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "a relay should be watching spec 76: $(relay_now)" ;; esac
  no_relay
}

scenario_orcaclosed() {
  local code
  RUNNER="$ORCA_RUNNER"

  echo "--- terminal_not_writable maps to no such session, exit 2"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=not-writable run_runner send term_w61 continue)"
  [ "$code" = 2 ] || fail "closed session must be exit 2, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: send"

  RUNNER="$PASEO_RUNNER"
}

scenario_worktreegit() {
  local code dest
  echo "--- start cuts the worktree with git at <repo>/.worktrees/issue-<n>"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  dest="$(wt 61)"
  assert_wt 61
  [ "$(git -C "$dest" rev-parse --abbrev-ref HEAD)" = issue-61 ] \
    || fail "worktree HEAD should be issue-61"
  case "$dest" in
    "$TMP/repo/.worktrees/issue-61") ;;
    *) fail "path must be exactly <repo>/.worktrees/issue-61, got $dest" ;;
  esac
  hasnt_runner_worktree
  hasnt "paseo :: workspace :: ls"
  hasnt "paseo :: project :: create"

  echo "--- a second start reuses that directory and does not call a runner workspace command"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "reuse expected exit 0, got $code: $(cat "$TMP/err")"
  assert_wt 61
  hasnt_runner_worktree
}

scenario_worktreegoverned() {
  local code got dest hook
  echo "--- the worktree basename is issue-<n>, and tool-guard.py governed_ticket sees the ticket"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  dest="$(wt 61)"
  [ "$(basename "$dest")" = issue-61 ] || fail "basename should be issue-61, got $(basename "$dest")"
  hook="$SKILL/scripts/tool-guard.py"
  got="$(cd "$dest" && python3 - "$hook" <<'PY'
import importlib.util, sys
from pathlib import Path
path = Path(sys.argv[1])
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("mmw_tool_guard", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.governed_ticket())
PY
)"
  [ "$got" = 61 ] || fail "governed_ticket in the worktree should be 61, got $got"
  got="$(cd "$TMP/repo" && python3 - "$hook" <<'PY'
import importlib.util, sys
from pathlib import Path
path = Path(sys.argv[1])
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("mmw_tool_guard", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.governed_ticket())
PY
)"
  [ "$got" = None ] || fail "governed_ticket in the repo root should be None, got $got"
}

scenario_paseostartdir() {
  local code dest
  echo "--- start hands the ticket worktree to the runner as the session's directory"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  dest="$(cd "$TMP/repo" && git rev-parse --show-toplevel)/.worktrees/issue-61"
  [ "$(out_json cwd)" = "$dest" ] || fail "cwd: $(out_json cwd), want $dest"
}

scenario_startreadsmodelsjson() {
  local code
  echo "--- start reads models.json"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  [ "$(out_json provider)" = "codex/gpt-5.6-sol" ] \
    || fail "start did not use models.json: $(cat "$TMP/out")"
  [ "$(out_json settings.thinkingOptionId)" = "high" ] \
    || fail "start did not use the models.json effort: $(cat "$TMP/out")"
}

scenario_startnomodelsjson() {
  local code saved="$TMP/models.saved"
  mv "$MMW_HOME/models.json" "$saved"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "missing models.json expected 2, got $code"
  grep -q "models.json" "$TMP/err" \
    || fail "the refusal is not actionable: $(cat "$TMP/err")"
  never_ran
  mv "$saved" "$MMW_HOME/models.json"
}

MMW_CURRENT_ENTRY='{"id":"mem-current","title":"Current title","applies":"适用条件：current","space":"o__r"}'
MMW_RELATED_ENTRIES='{"id":"mem-path","title":"Names the owned path","applies":"适用条件：path","space":"o__r"}
{"id":"mem-a","title":"Often found","applies":"适用条件：a","space":"o__r"}
{"id":"mem-b","title":"Spec neighbour","applies":"适用条件：b","space":"o__r"}
{"id":"mmw-toolbox-mem-1","title":"Toolbox record","applies":"适用条件：toolbox","space":"mmw-toolbox"}'

scenario_orcaworktreelink() {
  local code actual expected destination
  reset_log; fresh_repo
  code="$(run_dispatch env MMW_RUNNER=orca bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "Orca start expected 0: $(cat "$TMP/err")"
  destination="$(cd "$(wt 61)" && pwd -P)"
  actual="$(grep '^orca :: worktree :: set' "$MMW_TEST_LOG")"
  expected="orca :: worktree :: set :: --worktree :: path:$destination :: --issue :: 61"
  [ "$actual" = "$expected" ] \
    || fail "worktree set was not exact: got '$actual', want '$expected'"
}

scenario_orcaworktreelinkfails() {
  local code
  reset_log; fresh_repo
  code="$(run_dispatch env MMW_RUNNER=orca MMW_FAKE_ORCA_SCENARIO=worktree-set-fail bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "link failure blocked the start: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = term_1 ] || fail "the session id was not returned"
  posted_events 61 | grep -q worker.started || fail "worker.started was not recorded"
}

# The Orca terminal the caller runs in, as `terminal list` names it: handle term_main in
# the worktree at $1 (Orca's id is <repo-id>::<absolute path>).
seed_orca_caller() {
  printf '[{"handle": "term_main", "connected": true, "writable": true, "worktreeId": "r1::%s"}]\n' "$1" \
    > "$MMW_FAKE_ORCA_STATE/terminals.json"
}

scenario_orcaworktreeparent() {
  local code main destination
  echo "--- a worker's worktree is filed under the worktree of the orchestrator that started it"
  reset_log; fresh_repo
  main="$(cd "$TMP/repo" && pwd -P)"
  seed_orca_caller "$main"
  code="$(run_dispatch env MMW_RUNNER=orca ORCA_TERMINAL_HANDLE=term_main bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "Orca start expected 0: $(cat "$TMP/err")"
  destination="$(cd "$(wt 61)" && pwd -P)"
  grep -qxF "orca :: worktree :: set :: --worktree :: path:$destination :: --issue :: 61" "$MMW_TEST_LOG" \
    || fail "the issue link is gone: $(grep 'worktree :: set' "$MMW_TEST_LOG")"
  grep -qxF "orca :: worktree :: set :: --worktree :: path:$destination :: --parent-worktree :: id:r1::$main :: --json" "$MMW_TEST_LOG" \
    || fail "the worktree was not filed under the caller's: $(grep 'worktree :: set' "$MMW_TEST_LOG")"
}

scenario_orcareviewernoparent() {
  local base code
  echo "--- a reviewer start files its worktree under nothing, whichever terminal runs it"
  reset_log; fresh_repo
  echo '[]' > "$TMP/tickets.json"
  base="$(git -C "$TMP/repo" rev-parse main)"
  seed_worker_started_for_integration "$base"
  seed_workspace 61
  seed_orca_caller "$(cd "$TMP/repo" && pwd -P)"
  code="$(run_dispatch env MMW_RUNNER=orca ORCA_TERMINAL_HANDLE=term_main bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 0 ] || fail "Orca reviewer start expected 0: $(cat "$TMP/err")"
  grep -q '^orca :: worktree :: set .* --issue :: 61' "$MMW_TEST_LOG" || fail "the reviewer start linked no issue"
  ! grep -q -- '--parent-worktree' "$MMW_TEST_LOG" || fail "a reviewer start set a parent: $(grep 'worktree :: set' "$MMW_TEST_LOG")"
}

scenario_orcaparentrefused() {
  local code
  echo "--- a parent Orca refuses is one stderr line; the issue link and the session stand"
  reset_log; fresh_repo
  seed_orca_caller "$(cd "$TMP/repo" && pwd -P)"
  code="$(run_dispatch env MMW_RUNNER=orca MMW_FAKE_ORCA_SCENARIO=parent-cycle ORCA_TERMINAL_HANDLE=term_main \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "a refused parent blocked the start: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = term_2 ] || fail "the session id was not returned: $(cat "$TMP/out")"
  grep -q '^orca :: worktree :: set .* --issue :: 61$' "$MMW_TEST_LOG" || fail "the issue link was not asked for"
  posted_events 61 | grep -q worker.started || fail "worker.started was not recorded"
}

scenario_orcaparentskips() {
  local code main
  RUNNER="$ORCA_RUNNER"
  main="$(cd "$TMP/repo" && pwd -P)"
  echo "--- a caller in no Orca terminal has nothing to file the worktree under"
  reset_log
  code="$(run_runner attach --cwd "$TMP/repo" --under-caller)"
  [ "$code" = 0 ] || fail "attach outside Orca expected 0, got $code: $(cat "$TMP/err")"
  ! grep -q 'worktree :: set' "$MMW_TEST_LOG" || fail "attach outside Orca set something: $(cat "$MMW_TEST_LOG")"
  echo "--- a caller in the target worktree itself is not made its parent"
  reset_log; seed_orca_caller "$main"
  code="$(ORCA_TERMINAL_HANDLE=term_main run_runner attach --cwd "$TMP/repo" --under-caller)"
  [ "$code" = 0 ] || fail "attach from the same worktree expected 0, got $code: $(cat "$TMP/err")"
  ! grep -q -- '--parent-worktree' "$MMW_TEST_LOG" || fail "the worktree was made its own parent"
  echo "--- a handle terminal list does not name is exit 1 with the handle in the reason"
  reset_log
  code="$(ORCA_TERMINAL_HANDLE=term_gone run_runner attach --cwd "$TMP/repo" --under-caller)"
  [ "$code" = 1 ] || fail "an unlisted caller expected 1, got $code"
  grep -q term_gone "$TMP/err" || fail "the reason should name the handle: $(cat "$TMP/err")"
  ! grep -q 'worktree :: set' "$MMW_TEST_LOG" || fail "an unlisted caller still set something"
  RUNNER="$PASEO_RUNNER"
}

scenario_orcamergeparent() {
  local code main merge_tree
  echo "--- the merge worktree is filed under the worktree of the orchestrator that lands"
  reset_log; fresh_repo
  make_branch issue-61 ticket.txt ticket
  write_one_passed 61 "$(git -C "$TMP/repo" rev-parse issue-61)"
  seed_workspace 61
  main="$(cd "$TMP/repo" && pwd -P)"
  seed_orca_caller "$main"
  code="$(run_dispatch env MMW_RUNNER=orca ORCA_TERMINAL_HANDLE=term_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0, got $code: $(cat "$TMP/err")"
  merge_tree="$(cd "$TMP/repo/.worktrees/merge-main" && pwd -P)"
  [ "$(grep -cxF "orca :: worktree :: set :: --worktree :: path:$merge_tree :: --parent-worktree :: id:r1::$main :: --json" "$MMW_TEST_LOG")" = 1 ] \
    || fail "the merge worktree was not filed once under the caller's: $(grep 'worktree :: set' "$MMW_TEST_LOG")"
}

scenario_worktreelinknoop() {
  local code name
  for name in paseo herdr; do
    fresh_repo
    reset_log
    code="$(run_dispatch env MMW_RUNNER="$name" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
    [ "$code" = 0 ] || fail "$name start expected 0, got $code: $(cat "$TMP/err")"
    posted_events 61 | grep -q worker.started || fail "$name start recorded no session"

    reset_log
    RUNNER="$SKILL/scripts/runners/$name.sh"
    code="$(run_runner attach --cwd "$TMP/repo" --issue 61)"
    [ "$code" = 0 ] || fail "$name attach expected 0, got $code"
    [ ! -s "$MMW_TEST_LOG" ] || fail "$name attach called a runner command: $(cat "$MMW_TEST_LOG")"
  done
  RUNNER="$PASEO_RUNNER"
}

scenario_startonce() {
  local code
  echo "--- a start the runner refuses is refused once: one paseo run, no second host"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_FAKE_PASEO_SCENARIO=run-fail bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  started_once
  nothing_printed
  assert_no_wt 61
}

scenario_runneronticket() {
  local code
  echo "--- a start writes the runner and its session id on the ticket"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  local want
  want="reviewer.started session=agt_run_1 runner=paseo host=claude model=claude-opus-5 effort=high grade=reviewer worktree=$(cd "$TMP/repo" && git rev-parse --show-toplevel)/.worktrees/issue-61 branch=issue-61"
  [ "$(posted_events 61 session runner host model effort grade worktree branch)" = "$want" ] \
    || fail "the reviewer.started event is wrong: $(posted_events 61 session runner host model effort grade worktree branch)"

  echo "--- a worker's start carries its base commit and this machine"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  posted_events 61 base | grep -qE "^worker.started base=[0-9a-f]{40}$" \
    || fail "the worker.started event should carry the base commit: $(posted_events 61 base)"
  posted_events 61 machine | grep -qx "worker.started machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
    || fail "the worker.started event should name this machine: $(posted_events 61 machine)"
}

# The double dispatch of 2026-09-10: a worker started on Orca is live, and its ticket is
# claimed by this pipeline. Nothing on Paseo lists it. The claim is its worker's, and
# `advance` neither gives it back nor starts a second worker beside it.
scenario_orcadoubledispatch() {
  local code
  echo "--- a live worker on Orca keeps its claim, and no second worker is started"
  reset_log
  fresh_repo
  seed_workspace 61
  seed_orca_terminal term_7
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"],
   "body": "## Parent\\n\\n#76\\n", "title": "claimed ticket",
   "comments": [$(ev worker.started 61 "worker started on orca: session term_7" --spec 76 \
                  --field session=term_7 --field runner=orca $(start_facts "$(wt 61)" 61 worker))]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          MMW_RUNNER=orca bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit :: 61 :: --remove-assignee"
  hasnt "orca :: terminal :: create"
  hasnt "paseo :: run"
  grep -q "released 0" "$TMP/err" || fail "the live worker's claim was given back: $(cat "$TMP/err")"
  grep -q "started 0" "$TMP/err" || fail "a second worker was started: $(cat "$TMP/err")"

  echo "--- once that start is retracted, the same ticket is freed and started again"
  : > "$MMW_TEST_LOG"
  post_ev 61 worker.retracted --ticket 61 --line "Retracted the start on #61" \
    --field session=term_7 --field runner=orca
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          MMW_RUNNER=orca bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"
  has "orca :: terminal :: create"
  grep -q "started 1" "$TMP/err" || fail "the freed ticket was not started: $(cat "$TMP/err")"
}

scenario_posteventshowsgherror() {
  reset_log
  fresh_repo
  local code
  code="$(run_dispatch env FAKE_GH_COMMENT_FAILS=1 bash "$DISPATCH" "${TOOLS[@]}" send reviewer 61)"
  [ "$code" = 2 ] || fail "a refused event write must exit 2, got $code: $(cat "$TMP/err")"
  grep -q 'reviewer.started' "$TMP/err" \
    || fail "the refusal must name the event: $(cat "$TMP/err")"
  grep -Fxq 'HTTP 502' "$TMP/err" \
    || fail "the refusal must preserve gh stderr: $(cat "$TMP/err")"
  has "gh :: issue :: comment :: 61 :: --body"
  has "paseo :: archive :: --force :: agt_run_1"
}

# A session whose start event cannot be written is a session no command can find, and
# `advance` would read its ticket as free. It is stopped again, and the start refused.
scenario_startunrecorded() {
  local code
  echo "--- a start whose event the tracker refuses stops the session it started"
  reset_log
  fresh_repo
  code="$(run_dispatch env FAKE_GH_COMMENT_FAILS=1 bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  started_once
  has "paseo :: archive :: --force :: agt_run_1"
  nothing_printed
  grep -q "worker.started" "$TMP/err" \
    || fail "the refusal should name the event that could not be written: $(cat "$TMP/err")"
}

# A pre-migration pass with no recorded commit cannot be guessed from a missing branch.
# The migration note requires landing these tickets with the old advance before switching.
scenario_mergewithoutbranch() {
  local code
  echo "--- a pass with no recorded commit is refused rather than landing an unverified tip"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 60, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z",
   "comments": [$(ev ticket.passed 60 "ALL MET" --field branch=issue-60)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "blockedBy": [{"number": 60, "state": "CLOSED"}]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "exit $code, not 2: $(cat "$TMP/err")"
  never_ran
  assert_no_wt 61
  [ -z "$(posted_events 60)" ] || fail "#60 must not be recorded landed: $(posted_events 60)"

  echo "--- the rest of the batch goes on: a ticket #60 does not block is started, and the run still exits 2"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 60, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T01:00:00Z",
   "comments": [$(ev ticket.passed 60 "ALL MET" --field branch=issue-60)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "blockedBy": [{"number": 60, "state": "CLOSED"}]},
  {"number": 62, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "exit $code, not 2: $(cat "$TMP/err")"
  assert_no_wt 61
  [ -d "$(wt 62)" ] || fail "#62 should have been started: $(cat "$TMP/err")"
  grep -q "started 1, refused 0, failed 1" "$TMP/err" || fail "the tally should count the failed landing: $(cat "$TMP/err")"
}

# `start` holds a ticket back on the rule the frontier and the worker's preflight use: a
# blocker lets go once its work has landed on the base branch, not when it closed.
scenario_startunlandedblocker() {
  local code
  echo "--- start refuses a ticket whose blocker passed and has not landed, and starts it once it has"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 60, "state": "CLOSED", "labels": [],
   "comments": [$(ev ticket.passed 60 "ALL MET" --field branch=issue-60)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "blockedBy": [{"number": 60, "state": "CLOSED"}]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  never_ran

  reset_log
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 60, "state": "CLOSED", "labels": [],
   "comments": [$(ev ticket.passed 60 "ALL MET" --field branch=issue-60),
                $(ev ticket.landed 60 "Landed issue-60 into main" --field branch=issue-60)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "blockedBy": [{"number": 60, "state": "CLOSED"}]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "#60 has landed, so #61 starts; exit $code: $(cat "$TMP/err")"
}

# A ticket carrying an event nobody can read has no answer: retract archives nothing.
scenario_retractunreadable() {
  local code
  echo "--- retract refuses on a ticket whose events cannot be read, and keeps the worktree"
  reset_log
  fresh_repo
  seed_workspace 61
  runner_line 61 paseo agt_old worker
  MMW_N=61 python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
posted = json.loads(store.read_text()) if store.is_file() else {}
posted.setdefault(os.environ["MMW_N"], []).append(
    "worker started again\n\n<!-- mmw {\"v\":1,\"event\":\"worker.started\",\"session\": -->")
store.write_text(json.dumps(posted))
'
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  assert_wt 61
  hasnt "paseo :: archive"
  hasnt "gh :: issue :: edit"
}

# A comment whose event block cannot be read is not a comment with no event.
scenario_unreadableevents() {
  local code
  echo "--- a ticket whose event cannot be read keeps its claim and stays off the frontier"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"],
   "body": "## Parent\n\n#76\n", "title": "claimed ticket",
   "comments": ["worker started\n\n<!-- mmw {\"v\":1,\"event\":\"worker.started\" -->"]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit :: 61 :: --remove-assignee"
  never_ran
  grep -q "#61" "$TMP/err" \
    || fail "the frontier should name the unreadable events: $(cat "$TMP/err")"
}

scenario_landarchivesagents() {
  local code left
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  echo "--- land takes the ticket's Paseo agents off the list and deletes its contained ticket branch"
  reset_log
  fresh_repo
  make_branch issue-64 four.txt "from 64"
  write_landable
  seed_workspace 64
  seed_agent 64 worker
  seed_agent 64 reviewer
  seed_agent 99 worker 99
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/repo" show origin/main:four.txt >/dev/null 2>&1 || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_no_branch 64
  has "paseo :: archive :: --force :: agt_64_worker"
  has "paseo :: archive :: --force :: agt_64_reviewer"
  hasnt "paseo :: archive :: --force :: agt_99_worker"
  hasnt "paseo :: workspace :: archive"
  left="$(python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
rows = json.loads(path.read_text()) if path.is_file() else []
print(" ".join(sorted(r["id"] for r in rows)))
')"
  [ "$left" = "agt_99_worker" ] \
    || fail "only the other ticket's agent should remain, got: $left"
}

# ------------------------------------------------------------------ entry

# Sets one fake Paseo agent's status. An unrecognised status is how a runner that
# cannot tell is reached: runners/paseo.sh answers `unknown` for it.
set_agent_status() {
  MMW_ID="$1" MMW_STATUS="$2" python3 -c '
import json, os
from pathlib import Path
path = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "agents.json"
rows = json.loads(path.read_text())
for r in rows:
    if r.get("id") == os.environ["MMW_ID"]:
        r["status"] = os.environ["MMW_STATUS"]
path.write_text(json.dumps(rows))
'
}

scenario_noadapterretract() {
  local code copy
  echo "--- adapter gone: retract refuses with exit 2 and archives nothing"
  reset_log
  seed_agent 61 worker
  copy="$(skill_copy_for retract)"
  rm -f "$copy/scripts/runners/paseo.sh"
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2 with the adapter gone, got $code: $(cat "$TMP/err")"
  grep -q "runners/paseo.sh" "$TMP/err" || fail "stderr should name the missing adapter: $(cat "$TMP/err")"
  hasnt "paseo :: archive"
}

scenario_noadapterwait() {
  local code copy
  echo "--- wait asks no runner: with the adapter gone it still reads the ticket and answers"
  reset_log
  printf '%s\n' '[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}]' > "$TMP/tickets.json"
  seed_agent 61 worker
  copy="$(skill_copy_for wait)"
  rm -f "$copy/scripts/runners/paseo.sh"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 3 ] || fail "no result yet is exit 3 whatever the adapter, got $code: $(cat "$TMP/err")"
  hasnt "paseo ::"
}

scenario_unknownnotalive() {
  local code
  echo "--- runner answers unknown: retract refuses and archives nothing"
  reset_log
  seed_agent 61 worker
  set_agent_status agt_61_worker not-a-status
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: archive"
}

# A worker whose session ended mid-turn leaves its edits uncommitted. The next start keeps
# them as a commit on the ticket branch, so the new worker's preflight finds a clean tree
# and continues from them; a retraction keeps them before it removes the worktree; a
# worktree no worker of the ticket had is left alone for the preflight to refuse.
scenario_keepunfinished() {
  local code head
  echo "--- a start after a lost worker commits the edits it left, naming who left them"
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "from 61"
  seed_workspace 61
  printf 'half written\n' >> "$(wt 61)/one.txt"
  runner_line 61 paseo agt_61_worker worker
  post_ev 61 worker.lost --ticket 61 --line "The worker is gone" \
    --field session=agt_61_worker --field runner=paseo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  [ -z "$(git -C "$(wt 61)" status --porcelain --untracked-files=no)" ] \
    || fail "the new worker's preflight needs a clean tree: $(git -C "$(wt 61)" status --porcelain)"
  head="$(git -C "$(wt 61)" log -1 --format=%s)"
  case "$head" in "wip(#61):"*agt_61_worker*worker.lost*) ;; *) false ;; esac \
    || fail "the commit should name who left the edits and how its hold ended: $head"
  git -C "$(wt 61)" show HEAD:one.txt | grep -q "half written" \
    || fail "the edit is not in the commit"

  echo "--- a worktree no worker of the ticket had keeps its edits, for the preflight to refuse"
  reset_log
  fresh_repo
  make_branch issue-62 two.txt "from 62"
  seed_workspace 62
  printf 'somebody else\n' >> "$(wt 62)/two.txt"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 62 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -n "$(git -C "$(wt 62)" status --porcelain --untracked-files=no)" ] \
    || fail "edits no worker of #62 left must not be committed"
  [ "$(git -C "$(wt 62)" log -1 --format=%s)" = "issue-62" ] \
    || fail "no commit should have been made on issue-62: $(git -C "$(wt 62)" log -1 --format=%s)"

  echo "--- a retraction commits the edits before it removes the worktree"
  reset_log
  fresh_repo
  make_branch issue-63 three.txt "from 63"
  seed_workspace 63
  printf 'half written\n' >> "$(wt 63)/three.txt"
  runner_line 63 paseo agt_63_worker worker
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 63)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  assert_no_wt 63
  head="$(git -C "$TMP/repo" log -1 --format=%s issue-63)"
  case "$head" in "wip(#63):"*agt_63_worker*) ;; *) false ;; esac \
    || fail "the retraction should have kept the edits on issue-63: $head"
  git -C "$TMP/repo" show issue-63:three.txt | grep -q "half written" \
    || fail "the edit is not on the branch"
}

scenario_herdrunreadablelist() {
  local code
  RUNNER="$HERDR_RUNNER"
  echo "--- a list in the wrong shape is unknown, never stopped"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=list-shape run_runner liveness agt_w61)"
  [ "$code" = 0 ] || fail "liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = unknown ] || fail "a list it cannot read must be unknown, got: $(cat "$TMP/out")"

  echo "--- send on a list in the wrong shape sends nothing (3), never 'no such session' (2)"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=list-shape run_runner send agt_w61 hi)"
  [ "$code" = 3 ] || fail "send on an unreadable list expected 3, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: prompt"

  echo "--- and a list that is not JSON at all is unknown too"
  reset_log
  seed_herdr_agent agt_w61 idle
  MMW_FAKE_HERDR_SCENARIO=list-garbage run_runner liveness agt_w61 >/dev/null
  [ "$(cat "$TMP/out")" = unknown ] || fail "a garbage list must be unknown, got: $(cat "$TMP/out")"
}

scenario_herdrnoeffort() {
  local code
  RUNNER="$HERDR_RUNNER"
  echo "--- an empty effort starts claude without --effort, never with a literal dash"
  reset_log
  fresh_repo
  code="$(run_runner start --host claude --model "opus 5" --effort "—" --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: start"
  if grep "herdr :: agent :: start" "$MMW_TEST_LOG" | grep -q -- "--effort"; then
    fail "empty effort must drop the flag: $(grep 'herdr :: agent :: start' "$MMW_TEST_LOG")"
  fi
  grep "herdr :: agent :: start" "$MMW_TEST_LOG" | grep -qF ":: opus 5 ::" \
    || fail "the model must still be passed: $(grep 'herdr :: agent :: start' "$MMW_TEST_LOG")"

  echo "--- a host with no launch block refuses instead of starting without a model"
  reset_log
  fresh_repo
  code="$(run_runner start --host nosuchhost --model m --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "an unknown host expected refusal 1, got $code"
  hasnt "herdr :: agent :: start"
}

scenario_herdrstartloud() {
  local code
  RUNNER="$HERDR_RUNNER"
  echo "--- a refused start says what failed, on stderr"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_HERDR_SCENARIO=tab-fail run_runner start --host codex --model "gpt 5.6 sol" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected 1, got $code"
  nothing_printed
  code="$(MMW_FAKE_HERDR_SCENARIO=start-fail run_runner start --host codex --model "gpt 5.6 sol" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected 1, got $code"
  nothing_printed
}

scenario_runnerstop() {
  local code
  echo "--- orca stop closes the terminal; a handle already gone is 0"
  reset_log
  RUNNER="$ORCA_RUNNER"
  seed_orca_terminal term_61 true true
  code="$(run_runner stop term_61)"
  [ "$code" = 0 ] || fail "orca stop expected 0, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: close :: --terminal :: term_61"
  code="$(run_runner stop term_61)"
  [ "$code" = 0 ] || fail "stopping a gone terminal expected 0, got $code"
  echo "--- herdr stop closes the agent's pane"
  reset_log
  RUNNER="$HERDR_RUNNER"
  seed_herdr_agent issue-61 working
  code="$(run_runner stop issue-61)"
  [ "$code" = 0 ] || fail "herdr stop expected 0, got $code: $(cat "$TMP/err")"
  has "herdr :: pane :: close :: pane_1"
  echo "--- a list it cannot read is not a stop"
  reset_log
  seed_herdr_agent issue-61 working
  code="$(MMW_FAKE_HERDR_SCENARIO=list-fail run_runner stop issue-61)"
  [ "$code" = 1 ] || fail "an unreadable list must not read as stopped, got $code"
  hasnt "herdr :: pane :: close"
}

scenario_orcarefusalreason() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a terminal create Orca refuses on stdout carries Orca's reason"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SCENARIO=start-refused run_runner start --host codex --model gpt-5.6-sol --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code"
  nothing_printed
}

scenario_nightfromtask() {
  local code task
  echo "--- a night run from a task-branch worktree cuts tickets from that branch, under the main worktree"
  reset_log
  fresh_repo
  git -C "$TMP/repo" checkout -q -b feature-x
  printf 'x\n' > "$TMP/repo/feat.txt"
  git -C "$TMP/repo" add feat.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m feature-x
  git -C "$TMP/repo" push -q -u origin feature-x
  git -C "$TMP/repo" checkout -q main
  task="$TMP/repo/.worktrees/task-x"
  git -C "$TMP/repo" worktree add -q "$task" feature-x
  code="$( (cd "$task" && bash "$DISPATCH" "${TOOLS[@]}" start 61 worker) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -d "$TMP/repo/.worktrees/issue-61" ] || fail "the ticket worktree should be under the main worktree's .worktrees"
  [ ! -d "$task/.worktrees/issue-61" ] || fail "no second .worktrees under the task worktree"
  [ -f "$TMP/repo/.worktrees/issue-61/feat.txt" ] || fail "issue-61 should be cut from feature-x, the branch the night runs on"
  posted_events 61 into | grep -qx "worker.started into=feature-x" \
    || fail "worker.started should record feature-x: $(posted_events 61 into)"

  echo "--- a directory named issue-<n> on another branch is not taken over"
  reset_log
  git -C "$TMP/repo" worktree add -q "$TMP/repo/.worktrees/issue-62" -b mine main
  code="$( (cd "$task" && bash "$DISPATCH" "${TOOLS[@]}" start 62 worker) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 2 ] || fail "expected refusal 2, got $code"
  [ "$(git -C "$TMP/repo/.worktrees/issue-62" rev-parse --abbrev-ref HEAD)" = mine ] || fail "the worktree on mine should be left on mine"
  never_ran
}

scenario_orcatruncated() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a handle past a truncated list is unknown, never stopped"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=list-truncated run_runner liveness term_61)"
  [ "$code" = 0 ] || fail "liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = unknown ] || fail "past a truncated list must be unknown, got: $(cat "$TMP/out")"
  echo "--- and a list in the wrong shape is unknown too"
  reset_log
  MMW_FAKE_ORCA_SCENARIO=list-shape run_runner liveness term_61 >/dev/null
  [ "$(cat "$TMP/out")" = unknown ] || fail "a list it cannot read must be unknown, got: $(cat "$TMP/out")"
}

scenario_orcanotconnected() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- listed with connected:false is not stopped on that field alone; the exit probe decides"
  reset_log
  seed_orca_terminal term_61 false false
  code="$(MMW_FAKE_ORCA_SCENARIO=wait-busy run_runner liveness term_61)"
  [ "$code" = 0 ] || fail "liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" != stopped ] || fail "connected:false alone must not read as stopped"
  has "orca :: terminal :: wait"
}

# How many terminals the fake Orca still has open.
orca_terminals_left() {
  python3 -c 'import json, sys; print(len(json.load(open(sys.argv[1]))))' \
    "$MMW_FAKE_ORCA_STATE/terminals.json"
}

scenario_orcanoorphan() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a host that exits as soon as it starts is refused, says why, and leaves no terminal"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SCENARIO=exited run_runner start --host codex --model "gpt 5.6 sol" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  nothing_printed
  one_line_reason
  grep -qF "codex -m 'gpt 5.6 sol' -c 'model_reasoning_effort=\"high\"'" "$TMP/err" \
    || fail "stderr should give the command to run by hand: $(cat "$TMP/err")"
  has "orca :: terminal :: read"
  has "orca :: terminal :: close"
  [ "$(orca_terminals_left)" = 0 ] || fail "a refused start left a terminal behind"

  echo "--- an exit wait this cannot read falls back to liveness: alive is a start"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=exit-wait-garbage run_runner start --host codex --model gpt-5.6-sol --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 0 ] || fail "a live handle is a start, expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = term_1 ] || fail "start should print the handle: $(cat "$TMP/out")"
  hasnt "orca :: terminal :: close"

  echo "--- and a liveness that is not alive is a refusal that closes the terminal"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=wait-garbage run_runner start --host codex --model gpt-5.6-sol --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  nothing_printed
  has "orca :: terminal :: close"
  [ "$(orca_terminals_left)" = 0 ] || fail "a refused start left a terminal behind"
}

scenario_orcanohosts() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a host with no launch block refuses before any terminal is created"
  reset_log
  fresh_repo
  code="$(run_runner start --host nohost --model m --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "nohost has no launch block, expected refusal 1, got $code"
  hasnt "orca :: terminal :: create"
}

# ------------------------------------------------------------------ origin authority

scenario_checknoorigin() {
  local code
  fresh_repo
  git -C "$TMP/repo" remote remove origin
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "check without origin expected 2, got $code"
}

scenario_checknopush() {
  local code
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" remote set-url --push origin "$TMP/no-such-parent/origin.git"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "check with no push path expected 2, got $code"
  grep -qw "proj" "$TMP/err" && grep -qw "night" "$TMP/err" \
    || fail "the branches whose dry-run push failed were not named: $(cat "$TMP/err")"
}

scenario_checkbasemissing() {
  local code copy
  copy="$(skill_copy_for check-base-missing)"
  fresh_project_night
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "check with a local-only base expected 0, got $code: $(cat "$TMP/err")"
  grep -qF "proj: 0 commit(s), night: 1 commit(s)" "$TMP/out" \
    || fail "the missing remote base was not reported as a pending push: $(cat "$TMP/out")"
}

scenario_checklocalahead() {
  local code copy other
  copy="$(skill_copy_for check-ahead)"
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  commit_file "$TMP/repo" ahead-1.txt one ahead-one
  commit_file "$TMP/repo" ahead-2.txt two ahead-two
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "check on an ahead base expected 0, got $code: $(cat "$TMP/err")"
  grep -qF "proj: 0 commit(s), night: 2 commit(s)" "$TMP/out" \
    || fail "the pending push count was not reported: $(cat "$TMP/out")"

  copy="$(skill_copy_for check-behind)"
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  other="$(other_clone)"
  git -C "$other" checkout -q night
  commit_file "$other" remote-ahead.txt remote remote-ahead
  git -C "$other" push -q origin night
  reset_log
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "a remote-ahead base cache should pass check, got $code: $(cat "$TMP/err")"
}

scenario_openinto() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night-base proj
  git -C "$TMP/repo" push -q -u origin night-base
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  posted_events 76 into | grep -qx "spec.opened into=night-base" \
    || fail "spec.opened should record night-base: $(posted_events 76 into)"
  no_relay
}

open_project_fixture() {
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
}

scenario_openprojectreflog() {
  local code
  fresh_project_night
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "reflog open failed: $(cat "$TMP/err")"
  posted_events 76 project | grep -qx 'spec.opened project=proj' \
    || fail "spec.opened did not record reflog project: $(posted_events 76 project)"
  no_relay
}

scenario_openprojectconfig() {
  local code
  fresh_project_night
  git -C "$TMP/repo" reflog expire --expire=now --all
  git -C "$TMP/repo" config branch.night.vscode-merge-base origin/proj
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "config open failed: $(cat "$TMP/err")"
  posted_events 76 project | grep -qx 'spec.opened project=proj' \
    || fail "spec.opened did not record config project: $(posted_events 76 project)"
  no_relay
}

scenario_openprojecthistory() {
  local code
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" branch issue-61 night
  git -C "$TMP/repo" push -q origin issue-61
  git -C "$TMP/repo" reflog expire --expire=now --all
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "history open failed: $(cat "$TMP/err")"
  posted_events 76 project | grep -qx 'spec.opened project=proj' \
    || fail "spec.opened did not record history project: $(posted_events 76 project)"
  no_relay
}

scenario_openprojecttie() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" shared.txt shared shared
  git -C "$TMP/repo" branch alt
  git -C "$TMP/repo" push -q origin proj alt
  git -C "$TMP/repo" checkout -q -b night proj
  commit_file "$TMP/repo" night.txt night night
  git -C "$TMP/repo" reflog expire --expire=now --all
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "history tie expected 2, got $code"
  grep -qw 'alt' "$TMP/err" && grep -qw 'proj' "$TMP/err" && grep -q 'vscode-merge-base' "$TMP/err" \
    || fail "tie refusal omitted branches or remedy: $(cat "$TMP/err")"
  [ -z "$(posted_events 76)" ] || fail "tie wrote spec.opened"
  no_relay
}

scenario_openrefusesdefault() {
  local code
  fresh_repo
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "default branch open expected 2, got $code"
  [ -z "$(posted_events 76)" ] || fail "default open wrote spec.opened"
}

scenario_openrefusesfromdefault() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b night main
  commit_file "$TMP/repo" night.txt night night
  git -C "$TMP/repo" reflog expire --expire=now --all
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "base from default expected 2, got $code"
  [ -z "$(posted_events 76)" ] || fail "from-default open wrote spec.opened"
}

# A base cut from origin/main records main in its reflog. main is never the project branch:
# the configured branch wins over the reflog, and without one the history decides, main
# left out even where the project branch has no commits of its own.
scenario_openprojectpastdefault() {
  local code
  fresh_repo
  git -C "$TMP/repo" branch proj main
  git -C "$TMP/repo" push -q origin proj
  git -C "$TMP/repo" checkout -q -b night main
  commit_file "$TMP/repo" night.txt night night
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "a base cut from main with proj on origin expected 0, got $code: $(cat "$TMP/err")"
  [ "$(posted_events 76 project | tail -1)" = 'spec.opened project=proj' ] \
    || fail "history should pick proj past main: $(posted_events 76 project)"
  no_relay

  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q origin proj
  git -C "$TMP/repo" checkout -q -b alt main
  commit_file "$TMP/repo" alt.txt alt alt
  git -C "$TMP/repo" push -q origin alt
  git -C "$TMP/repo" checkout -q -b night main
  git -C "$TMP/repo" merge -q proj
  git -C "$TMP/repo" config branch.night.vscode-merge-base origin/proj
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "config over a main reflog expected 0, got $code: $(cat "$TMP/err")"
  [ "$(posted_events 76 project | tail -1)" = 'spec.opened project=proj' ] \
    || fail "config should win over the reflog: $(posted_events 76 project)"
  no_relay
}

scenario_openpushes() {
  local code proj_tip night_tip
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" checkout -q -b night proj
  git -C "$TMP/repo" push -q -u origin night
  commit_file "$TMP/repo" one.txt one one
  commit_file "$TMP/repo" two.txt two two
  proj_tip="$(git -C "$TMP/repo" rev-parse proj)"; night_tip="$(git -C "$TMP/repo" rev-parse night)"
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "push open failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$proj_tip" ] || fail "project was not pushed"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$night_tip" ] || fail "base was not pushed"
  no_relay
}

scenario_openrefusesdiverged() {
  local code other project_remote night_remote
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  other="$(other_clone)"
  git -C "$other" checkout -q night
  commit_file "$other" remote.txt remote remote
  git -C "$other" push -q origin night
  commit_file "$TMP/repo" local.txt local local
  git -C "$TMP/repo" fetch -q origin
  project_remote="$(git -C "$TMP/origin.git" rev-parse proj)"; night_remote="$(git -C "$TMP/origin.git" rev-parse night)"
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "diverged open expected 2, got $code"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$project_remote" ] || fail "project changed on refusal"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$night_remote" ] || fail "base changed on refusal"
  [ -z "$(posted_events 76)" ] || fail "diverged open wrote spec.opened"
}

# The project branch moved on after the base branch was cut from it.
scenario_openbasefollowsproject() {
  local code other proj_tip merge
  echo "--- a base branch with nothing of its own is fast-forwarded to the project branch, and so is the checkout"
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night proj
  git -C "$TMP/repo" push -q -u origin night
  other="$(other_clone)"
  git -C "$other" fetch -q origin
  git -C "$other" checkout -q proj
  commit_file "$other" later.txt later later
  git -C "$other" push -q origin proj
  proj_tip="$(git -C "$other" rev-parse proj)"
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$proj_tip" ] || fail "origin/night was not fast-forwarded to proj"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$proj_tip" ] || fail "the checkout was not fast-forwarded: $(cat "$TMP/err"); $(git -C "$TMP/repo" status --short)"
  no_relay

  echo "--- a base branch with commits of its own merges the project branch"
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  rm -rf "$TMP/other-clone"
  other="$(other_clone)"
  git -C "$other" checkout -q proj
  commit_file "$other" later.txt later later
  git -C "$other" push -q origin proj
  proj_tip="$(git -C "$other" rev-parse proj)"
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse night)"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$proj_tip" "$merge" || fail "origin/night does not contain proj"
  [ "$(git -C "$TMP/origin.git" show -s --format=%s "$merge")" = "Merge branch 'proj' into night" ] || fail "wrong merge subject"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$merge" ] || fail "the checkout was not fast-forwarded to the merge"
  posted_events 76 | grep -q '^spec.opened' || fail "open did not write spec.opened"
  no_relay

  echo "--- check reports what the base would take and changes nothing"
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  rm -rf "$TMP/other-clone"
  other="$(other_clone)"
  git -C "$other" checkout -q proj
  commit_file "$other" later.txt later later
  git -C "$other" push -q origin proj
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check 76)"
  grep -qF " 1 commit(s)" "$TMP/out" || fail "check did not report the commits: $(cat "$TMP/out") $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$(git -C "$TMP/repo" rev-parse night)" ] || fail "check changed origin/night"
}

scenario_openbaseprojectconflict() {
  local code other night_remote
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  other="$(other_clone)"
  git -C "$other" checkout -q proj
  commit_file "$other" night.txt other clash
  git -C "$other" push -q origin proj
  night_remote="$(git -C "$TMP/origin.git" rev-parse night)"
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "a conflicting project branch expected 2, got $code: $(cat "$TMP/err")"
  grep -q "night.txt" "$TMP/err" || fail "the conflicted file was not named: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$night_remote" ] || fail "origin/night changed on conflict"
  [ -z "$(posted_events 76)" ] || fail "a conflicted open wrote spec.opened"
  no_relay
}

scenario_openkeepsproject() {
  local code
  fresh_project_night
  git -C "$TMP/repo" reflog expire --expire=now --all
  git -C "$TMP/repo" branch alt proj
  git -C "$TMP/repo" push -q origin alt
  open_project_fixture
  post_ev 76 spec.opened --ticket '' --spec 76 --line opened --field into=night --field project=proj
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "repeat open failed: $(cat "$TMP/err")"
  [ "$(posted_events 76 project | grep -c '^spec.opened ' | tr -d ' ')" = 2 ] \
    || fail "repeat open did not write a second spec.opened: $(posted_events 76 project)"
  [ "$(posted_events 76 project | tail -1)" = 'spec.opened project=proj' ] || fail "repeat open changed project"
  no_relay
}

scenario_openprojecthead() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night
  commit_file "$TMP/repo" night.txt night night
  open_project_fixture
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "plain checkout project inference failed: $(cat "$TMP/err")"
  [ "$(posted_events 76 project | tail -1)" = 'spec.opened project=proj' ] \
    || fail "HEAD was recorded instead of the current project branch: $(posted_events 76 project)"
  no_relay
}

scenario_checkproject() {
  local code copy before
  copy="$(skill_copy_for checkproject)"
  fresh_project_night
  before="$(git -C "$TMP/origin.git" show-ref | sort)"
  cat > "$TMP/tickets.json" <<'JSON'
[{"number":61,"state":"OPEN","labels":["ready-for-agent","junior-worker"]}]
JSON
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "check project failed: $(cat "$TMP/err")"
  grep -q 'project branch: proj (source: reflog)' "$TMP/out" || fail "check omitted project/source: $(cat "$TMP/out")"
  [ "$(git -C "$TMP/origin.git" show-ref | sort)" = "$before" ] || fail "check pushed a branch"
}

setup_finish_closed() {
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" checkout -q proj
  cat > "$TMP/tickets.json" <<'JSON'
[{"number":61,"state":"CLOSED","labels":[]}]
JSON
  reset_log
  closed_night_spec
}

scenario_finishsyncsprojectbranch() {
  local code mode local_state merge base tip
  for mode in merge recorded contained absent; do
    for local_state in missing behind; do
      setup_finish_closed
      if [ "$mode" != merge ]; then
        git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'night'" night
        git -C "$TMP/repo" push -q origin proj
        merge="$(git -C "$TMP/repo" rev-parse proj)"
        base="$(git -C "$TMP/repo" rev-parse "$merge^1")"
        if [ "$mode" = recorded ]; then
          post_ev 76 spec.merged --ticket '' --spec 76 --line merged --field into=night \
            --field project=proj --field "merge=$merge" --field "base=$base"
        elif [ "$mode" = absent ]; then
          git -C "$TMP/repo" push -q origin --delete night
        fi
      fi
      git -C "$TMP/repo" checkout -q main
      if [ "$local_state" = missing ]; then
        git -C "$TMP/repo" branch -D proj >/dev/null
      else
        git -C "$TMP/repo" branch -f proj main
      fi
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
      [ "$code" = 0 ] || fail "$mode/$local_state finish failed: $(cat "$TMP/err")"
      tip="$(git -C "$TMP/origin.git" rev-parse proj)"
      [ "$(git -C "$TMP/repo" rev-parse --verify refs/heads/proj)" = "$tip" ] \
        || fail "$mode/$local_state local project branch is not at origin/proj"
      git -C "$TMP/repo" show proj:night.txt >/dev/null 2>&1 || fail "$mode/$local_state project branch lost night's work"
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
      [ "$code" = 0 ] || fail "$mode/$local_state finish retry failed: $(cat "$TMP/err")"
      [ "$(git -C "$TMP/repo" rev-parse proj)" = "$tip" ] || fail "$mode/$local_state retry moved the project branch"
    done
  done
}

scenario_finishsyncsprojectworktree() {
  local code mode session tip status merge base
  for mode in clean dirty staged missing; do
    setup_finish_closed
    tip="$(git -C "$TMP/repo" rev-parse proj)"
    git -C "$TMP/repo" checkout -q main
    session="$TMP/repo/.worktrees/project session"
    git -C "$TMP/repo" worktree add -q "$session" proj
    session="$(CDPATH='' cd -- "$session" && pwd -P)"
    if [ "$mode" = missing ]; then
      git -C "$TMP/repo" checkout -q --detach origin/proj
      base="$(git -C "$TMP/repo" rev-parse HEAD)"
      git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'night'" night
      merge="$(git -C "$TMP/repo" rev-parse HEAD)"
      git -C "$TMP/repo" push -q origin HEAD:proj
      post_ev 76 spec.merged --ticket '' --spec 76 --line merged --field into=night \
        --field project=proj --field "merge=$merge" --field "base=$base"
      git -C "$TMP/repo" checkout -q main
      rm -rf "$session"
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
      [ "$code" = 2 ] || fail "missing project worktree expected exit 2, got $code"
      grep -qF "$session" "$TMP/err" || fail "missing worktree warning omitted its path"
      grep -q 'worktree prune --dry-run --expire now' "$TMP/err" || fail "missing worktree warning omitted the inspection command"
      grep -q 'worktree prune --expire now' "$TMP/err" || fail "missing worktree warning omitted the repair command"
      [ "$(git -C "$TMP/repo" rev-parse proj)" = "$tip" ] || fail "missing worktree branch moved"
      git -C "$TMP/repo" worktree list --porcelain | grep -qF "$session" || fail "finish silently pruned the missing worktree"
      [ "$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)" = OPEN ] \
        || fail "missing worktree failure closed the spec"
      git -C "$TMP/repo" worktree prune --expire now
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
      [ "$code" = 0 ] || fail "missing worktree repair did not allow retry: $(cat "$TMP/err")"
      [ "$(git -C "$TMP/repo" rev-parse proj)" = "$(git -C "$TMP/origin.git" rev-parse proj)" ] \
        || fail "repaired project branch did not synchronize"
      continue
    fi
    printf 'untracked\n' > "$session/untracked.txt"
    if [ "$mode" != clean ]; then
      printf 'unfinished\n' > "$session/project.txt"
      if [ "$mode" = staged ]; then
        git -C "$session" add project.txt
      fi
    fi
    status="$(git -C "$session" status --porcelain)"
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 0 ] || fail "$mode project worktree finish failed: $(cat "$TMP/err")"
    if [ "$mode" = clean ]; then
      [ "$(git -C "$session" rev-parse HEAD)" = "$(git -C "$TMP/origin.git" rev-parse proj)" ] \
        || fail "clean project worktree was not fast-forwarded"
      [ "$(cat "$session/night.txt" 2>/dev/null)" = night ] || fail "clean project worktree did not get night's files"
    else
      [ "$(git -C "$session" rev-parse HEAD)" = "$tip" ] || fail "$mode project worktree moved"
      [ "$(git -C "$session" status --porcelain)" = "$status" ] || fail "$mode project worktree status changed"
      [ "$(cat "$session/project.txt")" = unfinished ] || fail "$mode project worktree edits changed"
      grep -qF "$session" "$TMP/err" || fail "$mode warning omitted the worktree path"
      grep -q 'uncommitted' "$TMP/err" || fail "$mode warning omitted the uncommitted changes"
    fi
    [ "$(cat "$session/untracked.txt")" = untracked ] || fail "$mode finish changed an untracked file"
    [ "$(git -C "$session" branch --show-current)" = proj ] || fail "$mode finish detached the project worktree"
  done
}

scenario_finishkeepsunmergedproject() {
  local code mode session tip
  for mode in checked-out unchecked; do
    setup_finish_closed
    commit_file "$TMP/repo" local.txt unmerged local-only
    tip="$(git -C "$TMP/repo" rev-parse proj)"
    session="$(CDPATH='' cd -- "$TMP/repo" && pwd -P)"
    if [ "$mode" = unchecked ]; then
      git -C "$TMP/repo" checkout -q main
    fi
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 0 ] || fail "$mode unmerged project finish failed: $(cat "$TMP/err")"
    [ "$(git -C "$TMP/repo" rev-parse proj)" = "$tip" ] || fail "$mode finish moved local-only project work"
    [ "$(git -C "$TMP/repo" show proj:local.txt)" = unmerged ] || fail "$mode finish lost local-only project work"
    git -C "$TMP/origin.git" show proj:night.txt >/dev/null 2>&1 || fail "$mode finish did not merge the night"
    ! git -C "$TMP/origin.git" cat-file -e proj:local.txt 2>/dev/null || fail "$mode finish pushed local-only work"
    grep -q 'not in origin/proj' "$TMP/err" || fail "$mode warning omitted the unmerged project commits"
    if [ "$mode" = checked-out ]; then
      grep -qF "$session" "$TMP/err" || fail "unmerged project warning omitted its worktree path"
      [ "$(cat "$session/local.txt")" = unmerged ] || fail "finish changed the unmerged worktree"
    fi
  done
}

scenario_finishkeepslocalnight() {
  local code tip
  setup_finish_closed
  tip="$(git -C "$TMP/repo" rev-parse origin/night)"
  git -C "$TMP/repo" branch -f night "$tip^"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish failed: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "origin night remains"
  [ "$(git -C "$TMP/repo" rev-parse --verify refs/heads/night)" = "$tip" ] \
    || fail "local night was not fast-forwarded to the merged night tip"
}

scenario_finishrestoreslocalnight() {
  local code tip
  setup_finish_closed
  tip="$(git -C "$TMP/repo" rev-parse origin/night)"
  git -C "$TMP/repo" branch -D night >/dev/null
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish failed: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "origin night remains"
  [ "$(git -C "$TMP/repo" rev-parse --verify refs/heads/night)" = "$tip" ] \
    || fail "local night was not restored at the merged night tip"
}

scenario_finishleavescheckedoutnight() {
  local code session tip first_merge
  setup_finish_closed
  tip="$(git -C "$TMP/repo" rev-parse origin/night)"
  git -C "$TMP/repo" branch -f night "$tip^"
  tip="$(git -C "$TMP/repo" rev-parse night)"
  session="$TMP/repo/.worktrees/night-session"
  git -C "$TMP/repo" worktree add -q "$session" night
  session="$(CDPATH='' cd -- "$session" && pwd -P)"
  printf 'unfinished\n' > "$session/untracked.txt"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish failed: $(cat "$TMP/err")"
  [ "$(git -C "$session" rev-parse HEAD)" = "$tip" ] || fail "finish moved the checked-out night"
  [ "$(cat "$session/untracked.txt")" = unfinished ] || fail "finish disturbed the session worktree"
  grep -qF "git worktree remove $session" "$TMP/err" || fail "finish omitted the kept worktree removal command"
  ! grep -qF 'git branch -D' "$TMP/err" || fail "finish suggested deleting the local branch"
  first_merge="$(git -C "$TMP/origin.git" rev-parse proj)"
  git -C "$TMP/repo" worktree remove --force "$session"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish rerun failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse --verify refs/heads/night)" = "$tip" ] || fail "rerun moved or deleted the retained night"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$first_merge" ] || fail "rerun merged again"
}

scenario_finishkeepsmainworktree() {
  local code main_path tip hint
  setup_finish_closed
  git -C "$TMP/repo" checkout -q night
  main_path="$(CDPATH='' cd -- "$TMP/repo" && pwd -P)"
  tip="$(git -C "$TMP/repo" rev-parse night)"
  printf 'unfinished\n' > "$TMP/repo/untracked.txt"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish from the main worktree failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$tip" ] || fail "finish moved the main worktree"
  [ "$(git -C "$TMP/repo" branch --show-current)" = night ] || fail "finish switched the main worktree branch"
  [ "$(cat "$TMP/repo/untracked.txt")" = unfinished ] || fail "finish disturbed main worktree files"
  ! grep -qF "git worktree remove $main_path" "$TMP/err" || fail "finish suggested removing the main worktree"
  hint="git -C \"$main_path\" switch --detach"
  grep -qF "$hint" "$TMP/err" || fail "finish omitted a usable main worktree instruction"
  bash -c "$hint" >/dev/null 2>&1 || fail "the main worktree instruction failed"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$tip" ] || fail "the instruction moved HEAD"
  [ "$(git -C "$TMP/repo" rev-parse night)" = "$tip" ] || fail "the instruction changed the retained night branch"
  [ -z "$(git -C "$TMP/repo" branch --show-current)" ] || fail "the instruction did not release the checked-out branch"
}

scenario_finishkeepsunmergedlocalnight() {
  local code tip
  setup_finish_closed
  git -C "$TMP/repo" checkout -q night
  commit_file "$TMP/repo" local.txt unmerged local-only
  tip="$(git -C "$TMP/repo" rev-parse night)"
  git -C "$TMP/repo" checkout -q proj
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish with local-only work failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse night)" = "$tip" ] || fail "finish lost the local-only work"
  grep -qw 'night' "$TMP/err" || fail "finish did not explain the retained local work"
  ! grep -qF 'git branch -D' "$TMP/err" || fail "finish suggested deleting local-only work"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "contained origin night remains"
  return 0
}

scenario_finishclosesspec() {
  local code merge base mode closes state
  for mode in merge recorded contained absent closed; do
    setup_finish_closed
    if [ "$mode" = recorded ]; then
      git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'night'" night
      git -C "$TMP/repo" push -q origin proj
      merge="$(git -C "$TMP/repo" rev-parse proj)"
      base="$(git -C "$TMP/repo" rev-parse "$merge^1")"
      post_ev 76 spec.merged --ticket '' --spec 76 --line merged --field into=night \
        --field project=proj --field "merge=$merge" --field "base=$base"
    elif [ "$mode" = contained ] || [ "$mode" = absent ]; then
      git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'night'" night
      git -C "$TMP/repo" push -q origin proj
      if [ "$mode" = absent ]; then
        git -C "$TMP/repo" push -q origin --delete night
      fi
    elif [ "$mode" = closed ]; then
      "$MMW_FAKE_GH_STATE_HELPER" issue-state "$MMW_FAKE_PASEO_STATE/gh-issue-states.json" 76 CLOSED
    fi
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 0 ] || fail "$mode finish failed: $(cat "$TMP/err")"
    closes="$(count_of 'gh :: issue :: close :: 76 :: --reason :: completed')"
    if [ "$mode" = closed ]; then
      [ "$closes" = 0 ] || fail "finish closed an already-closed spec again"
    else
      [ "$closes" = 1 ] || fail "$mode finish did not close spec 76 once"
    fi
    state="$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)"
    [ "$state" = CLOSED ] || fail "$mode finish left spec 76 open"
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 0 ] || fail "$mode finish rerun failed: $(cat "$TMP/err")"
    [ "$(count_of 'gh :: issue :: close :: 76 :: --reason :: completed')" = "$closes" ] \
      || fail "$mode finish rerun closed spec 76 again"
  done
}

scenario_finishclosespecfails() {
  local code merge
  setup_finish_closed
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_CLOSE_FAILS=1 bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "close failure expected exit 2, got $code"
  grep -q '#76' "$TMP/err" || fail "close failure omitted the spec number"
  grep -q 'run finish again' "$TMP/err" || fail "close failure omitted the retry instruction"
  [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] || fail "close failure lost spec.merged"
  [ "$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)" = OPEN ] \
    || fail "failed close changed the spec state"
  merge="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "close retry failed: $(cat "$TMP/err")"
  [ "$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)" = CLOSED ] \
    || fail "retry did not close the spec"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$merge" ] || fail "close retry merged again"
  [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] || fail "close retry wrote spec.merged again"
  [ "$(count_of 'gh :: issue :: close :: 76 :: --reason :: completed')" = 2 ] || fail "close retry was not attempted once after the failure"
}

scenario_finishcleanupfails() {
  local code mode merge base lock session real_git
  local -a git_env
  for mode in fetch restore delete projectrestore projectadvance projectworktree projectlisting; do
    git_env=("PATH=$PATH")
    setup_finish_closed
    git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'night'" night
    git -C "$TMP/repo" push -q origin proj
    merge="$(git -C "$TMP/repo" rev-parse proj)"
    base="$(git -C "$TMP/repo" rev-parse "$merge^1")"
    post_ev 76 spec.merged --ticket '' --spec 76 --line merged --field into=night \
      --field project=proj --field "merge=$merge" --field "base=$base"
    case "$mode" in
      fetch) git -C "$TMP/repo" remote set-url origin "$TMP/no-origin.git" ;;
      restore)
        git -C "$TMP/repo" branch -D night >/dev/null
        lock="$TMP/repo/.git/refs/heads/night.lock"
        : > "$lock"
        ;;
      projectrestore | projectadvance | projectworktree)
        git -C "$TMP/repo" checkout -q main
        if [ "$mode" = projectrestore ]; then
          git -C "$TMP/repo" branch -D proj >/dev/null
        else
          git -C "$TMP/repo" branch -f proj "$base"
        fi
        if [ "$mode" = projectworktree ]; then
          session="$TMP/repo/.worktrees/project-session"
          git -C "$TMP/repo" worktree add -q "$session" proj
        fi
        lock="$TMP/repo/.git/refs/heads/proj.lock"
        : > "$lock"
        ;;
      projectlisting)
        git -C "$TMP/repo" checkout -q main
        git -C "$TMP/repo" branch -f proj "$base"
        real_git="$(command -v git)"
        mkdir -p "$TMP/listing-bin"
        cat > "$TMP/listing-bin/git" <<'SH'
#!/usr/bin/env bash
if [ "${3:-} ${4:-} ${5:-}" = 'worktree list --porcelain' ]; then
  echo 'worktree list failed' >&2
  exit 1
fi
exec "$MMW_REAL_GIT" "$@"
SH
        chmod +x "$TMP/listing-bin/git"
        git_env=("PATH=$TMP/listing-bin:$PATH" "MMW_REAL_GIT=$real_git")
        ;;
      delete)
        cat > "$TMP/origin.git/hooks/update" <<'SH'
#!/usr/bin/env bash
if [ "$1" = refs/heads/night ] && [ "$3" = 0000000000000000000000000000000000000000 ]; then
  echo 'night deletion refused' >&2
  exit 1
fi
SH
        chmod +x "$TMP/origin.git/hooks/update"
        ;;
    esac
    code="$(run_dispatch env "${git_env[@]}" FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 2 ] || fail "$mode cleanup failure expected exit 2, got $code"
    [ "$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)" = OPEN ] \
      || fail "$mode cleanup failure closed the spec"
    [ "$(count_of 'gh :: issue :: close :: 76')" = 0 ] || fail "$mode cleanup failure attempted to close the spec"
    git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night || fail "$mode cleanup failure lost origin/night"
    if [ "$mode" = projectlisting ]; then
      grep -q 'could not list worktrees' "$TMP/err" || fail "listing failure omitted its cause"
      [ "$(git -C "$TMP/repo" rev-parse proj)" = "$base" ] || fail "listing failure moved the project branch"
    fi
    case "$mode" in
      fetch) git -C "$TMP/repo" remote set-url origin "$TMP/origin.git" ;;
      restore | projectrestore | projectadvance | projectworktree) rm -f "$lock" ;;
      delete) rm -f "$TMP/origin.git/hooks/update" ;;
    esac
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
    [ "$code" = 0 ] || fail "$mode cleanup retry failed: $(cat "$TMP/err")"
    [ "$(env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" gh issue view 76 --json state --jq .state)" = CLOSED ] \
      || fail "$mode cleanup retry did not close the spec"
    [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$merge" ] || fail "$mode cleanup retry merged again"
    [ "$(git -C "$TMP/repo" rev-parse proj)" = "$merge" ] || fail "$mode cleanup retry did not sync the project branch"
    [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] || fail "$mode cleanup retry recorded a second merge"
    git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "$mode cleanup retry left origin/night"
  done
  return 0
}

scenario_finishmerges() {
  local code merge base
  setup_finish_closed
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish merge failed: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse proj)"; base="$(git -C "$TMP/origin.git" rev-parse "$merge^1")"
  [ "$(git -C "$TMP/origin.git" show -s --format=%s "$merge")" = "Merge branch 'night'" ] || fail "wrong merge subject"
  posted_events 76 into project merge base | grep -qx "spec.merged into=night project=proj merge=$merge base=$base" \
    || fail "spec.merged fields wrong: $(posted_events 76 into project merge base)"
  posted_events 76 line | grep -F "https://github.com/o/r/compare/$base...$merge" | grep -q '^spec.merged' \
    || fail "spec.merged omits the compare link: $(posted_events 76 line)"
  posted_events 76 line | grep -F "https://github.com/o/r/commit/$merge" | grep -q '^spec.merged' \
    || fail "spec.merged omits the merge commit link: $(posted_events 76 line)"
}

scenario_finishcleans() {
  local code main_path lock
  setup_finish_closed
  mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q "$TMP/repo/.worktrees/night-checkout" night
  git -C "$TMP/repo" worktree add -q --detach "$TMP/repo/.worktrees/merge-night" origin/night
  lock="$MMW_HOME/state/o__r/merge-night.lock"
  mkdir -p "$(dirname "$lock")"
  : > "$lock"
  main_path="$(git -C "$TMP/repo" worktree list --porcelain | head -1 | sed 's/^worktree //')"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish clean failed: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "origin night remains"
  [ -d "$TMP/repo/.worktrees/night-checkout" ] || fail "finish removed a worktree with the base branch checked out"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night \
    || fail "finish deleted the local base branch a worktree still has checked out"
  grep -q "night-checkout" "$TMP/err" \
    || fail "finish did not name the kept worktree: $(cat "$TMP/err")"
  [ ! -e "$TMP/repo/.worktrees/merge-night" ] || fail "base merge worktree remains"
  [ ! -e "$lock" ] || fail "base merge lock remains"
  [ -d "$main_path" ] || fail "main worktree was removed"
  return 0
}

# #913: the orchestrator's session lives in a worktree on the base branch, and a runner closes a
# session whose worktree disappears. finish, run from inside that worktree, must leave it and the
# session's current directory in place while cleaning everything the pipeline made.
scenario_finishkeepssession() {
  local session lock
  setup_finish_closed
  session="$TMP/repo/.worktrees/night-session"
  mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q "$session" night
  session="$(CDPATH='' cd -- "$session" && pwd -P)"
  git -C "$TMP/repo" worktree add -q --detach "$TMP/repo/.worktrees/merge-night" origin/night
  lock="$MMW_HOME/state/o__r/merge-night.lock"
  mkdir -p "$(dirname "$lock")"
  : > "$lock"
  (
    cd "$session" || exit 99
    env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
      bash "$DISPATCH" "${TOOLS[@]}" finish 76 > "$TMP/out" 2> "$TMP/err"
    printf '%s\n' "$?" > "$TMP/finish-code"
    git rev-parse --show-toplevel > "$TMP/current-root" 2>&1
  )
  [ "$(cat "$TMP/finish-code")" = 0 ] || fail "finish from the session worktree failed: $(cat "$TMP/err")"
  [ "$(cat "$TMP/current-root")" = "$session" ] \
    || fail "the session no longer resolves to its worktree: $(cat "$TMP/current-root")"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night \
    || fail "finish deleted the local base branch the session has checked out"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "origin night remains"
  [ ! -e "$TMP/repo/.worktrees/merge-night" ] || fail "base merge worktree remains"
  [ ! -e "$lock" ] || fail "base merge lock remains"
  grep -qF -- "$session" "$TMP/err" \
    || fail "finish did not name the session worktree it kept: $(cat "$TMP/err")"
  [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] \
    || fail "finish did not record exactly one merge"
}

# A refused finish touches nothing: every ref on origin and the local night branch stay as
# they were, no spec.merged is written, and stderr names the record that is missing, when
# that record is a fact (an event name, a ticket, a check); an empty name checks nothing there.
finish_refused() {
  local label="$1" names="$2" code before local_night
  before="$(git -C "$TMP/origin.git" show-ref | sort)"
  local_night="$(git -C "$TMP/repo" rev-parse night)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "$label: finish expected 2, got $code: $(cat "$TMP/err")"
  if [ -n "$names" ]; then
    grep -qF -- "$names" "$TMP/err" || fail "$label: the refusal should name $names: $(cat "$TMP/err")"
  fi
  [ "$(git -C "$TMP/origin.git" show-ref | sort)" = "$before" ] || fail "$label: finish changed origin"
  [ "$(git -C "$TMP/repo" rev-parse night)" = "$local_night" ] || fail "$label: finish changed the local night branch"
  if posted_events 76 | grep -q '^spec.merged'; then fail "$label: finish wrote spec.merged"; fi
}

scenario_finishrefuses() {
  echo "--- a night with no spec.closed"
  fresh_project_night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log
  post_ev 76 spec.opened --ticket '' --spec 76 --line opened --field into=night --field project=proj
  finish_refused "unclosed" "spec.closed"
}

scenario_finishrefusesnopr() {
  echo "--- a night with no open pull request to the project branch"
  setup_finish_closed
  FAKE_GH_PR=none finish_refused "no pull request" ""
}

scenario_finishrefusesredpr() {
  echo "--- a pull request whose checks are red or still running, or whose review threads are open"
  setup_finish_closed
  FAKE_GH_PR_CHECKS="build fail" finish_refused "red check" "build fail"
  FAKE_GH_PR_CHECKS="test pending" finish_refused "pending check" "test pending"
  FAKE_GH_PR_THREADS="src/app.py:12" finish_refused "open thread" "src/app.py:12"
}

scenario_finishrefusesopenticket() {
  echo "--- a ticket of the night still open"
  setup_finish_closed
  printf '%s\n' '[{"number":61,"state":"OPEN","labels":[]}]' > "$TMP/tickets.json"
  finish_refused "open ticket" "#61"
}

scenario_finishrefusesothernight() {
  local code before
  setup_finish_closed
  post_ev 77 spec.opened --ticket '' --spec 77 --line opened --field into=night --field project=proj
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_SPECS='76 77' FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "other-night finish expected 2, got $code"
  grep -q '#77' "$TMP/err" || fail "other night missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "other-night finish changed project"
}

scenario_finishrefusesnoproject() {
  local code before
  fresh_project_night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log
  post_ev 76 spec.opened --ticket '' --spec 76 --line opened --field into=night
  post_ev 76 spec.closed --ticket '' --spec 76 --line closed --field date=2026-09-11
  finish_refused "no project" ""
}

scenario_finishconflict() {
  local code before
  fresh_repo
  printf 'base\n' > "$TMP/repo/shared.txt"; git -C "$TMP/repo" add shared.txt; git -C "$TMP/repo" commit -q -m base; git -C "$TMP/repo" push -q origin main
  git -C "$TMP/repo" checkout -q -b proj; commit_file "$TMP/repo" shared.txt project project; git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night HEAD~1; commit_file "$TMP/repo" shared.txt night night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log; closed_night_spec
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 1 ] || fail "conflict finish expected 1, got $code: $(cat "$TMP/err")"
  grep -q 'shared.txt' "$TMP/err" || fail "conflict file missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "conflict changed project"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night || fail "local night deleted"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night || fail "origin night deleted"
}

scenario_finishred() {
  local code before
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  put_check "$TMP/repo" 'echo RED-CHECK >&2; echo "FAIL unit 0s"; exit 1'
  git -C "$TMP/repo" commit -q -m checks; git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night; commit_file "$TMP/repo" night.txt night night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log; closed_night_spec
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 1 ] || fail "red finish expected 1, got $code: $(cat "$TMP/err")"
  grep -q 'RED-CHECK' "$TMP/err" || fail "the check's last lines are missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "red finish changed project"
  posted_events 76 | grep -q spec.merged && fail "red finish wrote spec.merged"
  return 0
}

scenario_finishnocheck() {
  echo "--- a merge result with no scripts/check is not pushed"
  setup_finish_closed
  git -C "$TMP/repo" checkout -q night
  git -C "$TMP/repo" rm -q scripts/check
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "drop check"
  git -C "$TMP/repo" push -q origin night
  git -C "$TMP/repo" checkout -q proj
  finish_refused "no scripts/check" "scripts/check"
}

# The project branch is inside the base branch, and the base branch's tip is the merge
# commit `land` recorded for #61: the tree finish would merge is the one land checked.
setup_finish_over_landing() {
  local passed tip
  fresh_repo
  rm -f "$TMP/check-runs"
  git -C "$TMP/repo" checkout -q -b proj main
  put_check "$TMP/repo" "printf x >> '$TMP/check-runs'; exit 1"
  git -C "$TMP/repo" commit -q -m checks
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night proj
  git -C "$TMP/repo" checkout -q -b issue-61 night
  commit_file "$TMP/repo" ticket.txt ticket ticket
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" checkout -q night
  git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'issue-61'" issue-61
  tip="$(git -C "$TMP/repo" rev-parse night)"
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" checkout -q proj
  echo '[{"number":61,"state":"CLOSED","labels":[]}]' > "$TMP/tickets.json"
  reset_log
  closed_night_spec
  post_ev 61 ticket.landed --ticket 61 --spec 76 --line "Landed issue-61 into night" \
    --field branch=issue-61 --field into=night --field "commit=$passed" --field "merge=$tip" \
    --field "base=$(git -C "$TMP/repo" rev-parse proj)"
}

scenario_finishskipschecked() {
  local code
  setup_finish_over_landing
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish over a checked landing failed: $(cat "$TMP/err")"
  [ ! -e "$TMP/check-runs" ] || fail "finish ran the checks on a tree land had checked"
  [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] || fail "finish did not record the merge"
}

scenario_finishchecksbasepush() {
  local code before
  setup_finish_over_landing
  git -C "$TMP/repo" checkout -q night
  commit_file "$TMP/repo" fix.txt fix "closing-pass fix"
  git -C "$TMP/repo" push -q origin night
  git -C "$TMP/repo" checkout -q proj
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 1 ] || fail "a base pushed to after its last landing was not checked: $code $(cat "$TMP/err")"
  [ "$(cat "$TMP/check-runs" 2>/dev/null)" = x ] || fail "finish did not run the checks once"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "red finish changed project"
}

# The night's --all record on the base branch's tip after a closing-pass fix.
all_record() {
  local tip
  tip="$(git -C "$TMP/origin.git" rev-parse night)"
  post_ev 76 spec.checked --ticket '' --spec 76 --line "--all green" --field tier=all \
    --field "commit=$tip" --field "base=$tip" --field result=met \
    --field "machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
    --json-field 'steps=["unit"]'
}

scenario_finishreusesall() {
  local code
  setup_finish_over_landing
  git -C "$TMP/repo" checkout -q night
  commit_file "$TMP/repo" fix.txt fix "closing-pass fix"
  git -C "$TMP/repo" push -q origin night
  git -C "$TMP/repo" checkout -q proj

  echo "--- a tip the night's --all proved is not checked again by finish"
  all_record
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish over a tip --all proved failed: $(cat "$TMP/err")"
  [ ! -e "$TMP/check-runs" ] || fail "finish ran the checks on a tree --all had proved"
  grep -q 'passed --all on this machine' "$TMP/out" || fail "finish does not say which record it used: $(cat "$TMP/out")"
}

scenario_checkallisgone() {
  local code
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check-all 76)"
  [ "$code" = 2 ] || fail "an unknown command expected 2, got $code"
  grep -q '^usage:' "$TMP/err" || fail "an unknown command must print usage"
  if grep -q 'check-all' "$TMP/err"; then fail "usage still lists check-all"; fi
}

summary_check_fixture() {
  fresh_repo
  rm -f "$TMP/check-args"
  git -C "$TMP/repo" checkout -q -b night main
  put_check "$TMP/repo" "printf '%s\\n' \"\$*\" >> '$TMP/check-args'
$1"
  git -C "$TMP/repo" commit -q -m checks
  git -C "$TMP/repo" push -q -u origin night
  echo '[]' > "$TMP/tickets.json"
  reset_log
  summary_ready_fixture 76 night
}

scenario_summaryreusesspecchecked() {
  local code
  summary_check_fixture "echo 'FAIL unit 0s'; exit 1"
  all_record
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary should reuse spec.checked: $(cat "$TMP/err")"
  [ ! -e "$TMP/check-args" ] || fail "summary ran --all on a proved commit"
  [ "$(posted_events 76 | grep -c '^spec.checked')" = 1 ] || fail "summary wrote a second spec.checked"
  grep -q '^CHECK PASS all:' "$TMP/out" || fail "summary must print the reused full-check summary: $(cat "$TMP/out")"
}

scenario_summaryrefusesredall() {
  local code kind body
  for kind in red missing cannot-run; do
    case "$kind" in
      red) body="echo 'FAIL unit 0s'; echo 'FAIL lint 0s'; exit 1" ;;
      missing) body='exit 0' ;;
      cannot-run) body='echo missing-compiler >&2; exit 2' ;;
    esac
    summary_check_fixture "$body"
    if [ "$kind" = missing ]; then
      git -C "$TMP/repo" rm -q scripts/check
      git -C "$TMP/repo" commit -q -m missing
      git -C "$TMP/repo" push -q origin night
    fi
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
    [ "$code" = 2 ] || fail "$kind full check should refuse summary, got $code: $(cat "$TMP/err")"
    [ "$(posted_events 76)" = spec.opened ] || fail "$kind check posted an event: $(posted_events 76)"
    case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "$kind check closed the watch" ;; esac
    case "$kind" in
      red) grep -q unit "$TMP/err" && grep -q lint "$TMP/err" || fail "summary must name every red step" ;;
      missing) grep -q scripts/check "$TMP/err" || fail "summary must name the missing checker" ;;
      cannot-run) grep -q missing-compiler "$TMP/err" || fail "summary must name the missing tool" ;;
    esac
  done
}

scenario_summarye2eredopenticket() {
  local code
  summary_check_fixture "echo 'FAIL e2e-board 3s'; echo 'checks: 1 failed'; exit 1"
  cat > "$TMP/tickets.json" <<'JSON'
[{"number":61,"state":"OPEN","labels":["needs-triage"],
  "body":"## Acceptance criteria\n- [ ] AC1: board\n  CHECK: run tests/e2e/board/screen.test.ts\n  EXPECT: green"}]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "an unfinished UI ticket should allow summary: $(cat "$TMP/err")"
  [ "$(posted_events 76 | tail -1)" = spec.closed ] || fail "summary did not close"
  if posted_events 76 | grep -q '^spec.checked'; then fail "a red full check must not be recorded green"; fi
  grep -q 'e2e-board.*#61' "$MMW_GH_LAST_BODY" || fail "summary must name the red step and its open ticket: $(cat "$MMW_GH_LAST_BODY")"
  [ -z "$(relay_now)" ] || fail "summary did not close the watch"
}

scenario_summarye2eredrefuses() {
  local code variant
  for variant in none closed prose different-product mixed uncovered-product env; do
    summary_check_fixture "echo 'FAIL e2e-board 3s'; echo 'checks: 1 failed'; exit 1"
    python3 - "$variant" "$TMP/tickets.json" <<'PY'
import json, sys
variant, path = sys.argv[1:]
body = '## Acceptance criteria\n- [ ] AC1: UI\n  CHECK: run tests/e2e/board/screen.test.ts\n  EXPECT: green'
if variant == 'prose':
    body = '## Notes\nThe tests/e2e/board/ directory has tests.'
if variant == 'different-product':
    body = body.replace('/board/', '/other/')
rows = [] if variant == 'none' else [dict(number=61, state='CLOSED' if variant == 'closed' else 'OPEN', labels=['needs-triage'], body=body)]
json.dump(rows, open(path, 'w'))
PY
    if [ "$variant" = uncovered-product ]; then
      put_check "$TMP/repo" "echo 'FAIL e2e-board 3s'; echo 'FAIL e2e-other 1s'; exit 1"
      git -C "$TMP/repo" commit -q -m uncovered
      git -C "$TMP/repo" push -q origin night
    fi
    if [ "$variant" = env ]; then
      put_check "$TMP/repo" "echo 'FAIL e2e-board 3s'; echo 'ENV unit 1s'; echo 'CHECK FAIL all: 1 of 2 steps red (e2e-board); cannot run here: unit'; exit 1"
      git -C "$TMP/repo" commit -q -m env
      git -C "$TMP/repo" push -q origin night
    fi
    if [ "$variant" = mixed ]; then
      put_check "$TMP/repo" "echo 'FAIL e2e-board 3s'; echo 'FAIL unit 1s'; exit 1"
      git -C "$TMP/repo" commit -q -m mixed
      git -C "$TMP/repo" push -q origin night
    fi
    code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
    [ "$code" = 2 ] || fail "$variant must refuse summary, got $code: $(cat "$TMP/err")"
    [ "$(posted_events 76)" = spec.opened ] || fail "$variant posted an event: $(posted_events 76)"
    case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "$variant closed the watch" ;; esac
    grep -q e2e-board "$TMP/err" || fail "$variant must name the red step"
    if [ "$variant" = env ]; then
      grep -q 'ENV unit' "$TMP/err" || fail "summary must name the suite that could not run"
    fi
  done
}

scenario_summaryprintse2esteps() {
  local code
  summary_check_fixture "echo 'PASS e2e-board 3s'; echo 'PASS e2e-editor 4s'; echo 'checks: all green'; exit 0"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "green summary expected 0: $(cat "$TMP/err")"
  grep -qx 'PASS e2e-board 3s' "$TMP/out" && grep -qx 'PASS e2e-editor 4s' "$TMP/out" \
    || fail "summary must print each passing product step: $(cat "$TMP/out")"
  summary_ready_fixture 76 night
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "reused green summary expected 0: $(cat "$TMP/err")"
  grep -q '^PASS e2e-board ' "$TMP/out" && grep -q '^PASS e2e-editor ' "$TMP/out" \
    || fail "summary must print each reused product result: $(cat "$TMP/out")"
  [ "$(wc -l < "$TMP/check-args" | tr -d ' ')" = 1 ] || fail "printing reused steps ran --all again"
  summary_check_fixture "echo 'PASS e2e-editor 4s'; echo 'FAIL e2e-board 3s'; echo 'checks: 1 failed'; exit 1"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 2 ] || fail "red summary expected 2: $(cat "$TMP/err")"
  grep -qx 'FAIL e2e-board 3s' "$TMP/out" && grep -qx 'PASS e2e-editor 4s' "$TMP/out" \
    || fail "summary must print each product step even when refusing: $(cat "$TMP/out")"
}

scenario_summaryrunsall() {
  local code tip
  fresh_repo
  rm -f "$TMP/check-args"
  git -C "$TMP/repo" checkout -q -b night main
  put_check "$TMP/repo" "printf '%s\\n' \"\$*\" >> '$TMP/check-args'; echo 'PASS unit 0s'; echo 'checks: all green'; exit 0"
  git -C "$TMP/repo" commit -q -m checks
  git -C "$TMP/repo" push -q -u origin night
  tip="$(git -C "$TMP/repo" rev-parse night)"
  echo '[]' > "$TMP/tickets.json"; reset_log
  summary_ready_fixture 76 night
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/check-args" 2>/dev/null)" = "--all" ] || fail "scripts/check was not run with --all once"
  posted_events 76 tier commit steps | grep -qx "spec.checked tier=all commit=$tip steps=\['unit'\]" \
    || fail "the --all record is wrong: $(posted_events 76 tier commit steps)"
  [ "$(posted_events 76 | tail -2 | tr '\n' ' ')" = 'spec.checked spec.closed ' ] \
    || fail "summary must record the green check before closing: $(posted_events 76)"
  grep -qx 'checks: all green' "$TMP/out" || fail "the check summary line is missing: $(cat "$TMP/out")"
}

scenario_finishrerun() {
  local code dirty first_merge
  setup_finish_closed
  dirty="$TMP/repo/.worktrees/night-dirty"; mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q "$dirty" night
  printf 'dirty\n' > "$dirty/untracked.txt"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "first finish failed: $(cat "$TMP/err")"
  first_merge="$(git -C "$TMP/origin.git" rev-parse proj)"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night || fail "first finish deleted the checked-out local night"
  git -C "$TMP/repo" worktree remove --force "$dirty"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish rerun failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$first_merge" ] || fail "rerun made a second merge"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night || fail "rerun deleted local night"
  [ "$(posted_events 76 | grep -c '^spec.merged' | tr -d ' ')" = 1 ] || fail "rerun wrote another spec.merged"
}

scenario_finishcontained() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b proj main
  commit_file "$TMP/repo" project.txt project project
  git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night proj
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"
  reset_log
  closed_night_spec
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "already-contained finish failed: $(cat "$TMP/err")"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night || fail "contained local night was deleted"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "contained origin night remains"
  return 0
}

scenario_finishrefusesunreadablespec() {
  local code before
  setup_finish_closed
  post_raw_comment 77 'broken event <!-- mmw {"v":1,"event":"spec.opened","into": -->'
  before="$(git -C "$TMP/origin.git" show-ref | sort)"
  code="$(run_dispatch env FAKE_GH_SPECS='76 77' FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "unreadable-spec finish expected 2, got $code"
  grep -q '#77' "$TMP/err" || fail "unreadable spec was not named: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" show-ref | sort)" = "$before" ] || fail "unreadable-spec finish changed origin"
}

scenario_finishcleanupindependent() {
  local code merge base checked merge_wt orphan_wt orphan_lock
  setup_finish_closed
  merge="$(git -C "$TMP/repo" rev-parse proj)"
  base="$(git -C "$TMP/repo" rev-parse "$merge^1")"
  post_ev 76 spec.merged --ticket '' --spec 76 --line merged --field into=night \
    --field project=proj --field "merge=$merge" --field "base=$base"
  checked="$TMP/repo/.worktrees/night-clean"
  merge_wt="$TMP/repo/.worktrees/merge-night"
  mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q "$checked" night
  git -C "$TMP/repo" worktree add -q --detach "$merge_wt" origin/night
  git -C "$TMP/repo" branch gone proj
  git -C "$TMP/repo" push -q origin gone
  orphan_wt="$TMP/repo/.worktrees/merge-gone"
  git -C "$TMP/repo" worktree add -q --detach "$orphan_wt" origin/gone
  orphan_lock="$STATE_DIR/merge-gone.lock"
  mkdir -p "$STATE_DIR"
  : > "$orphan_lock"
  git -C "$TMP/repo" push -q origin --delete gone
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "independent cleanup failed: $(cat "$TMP/err")"
  [ -d "$checked" ] || fail "finish removed a worktree with the base branch checked out"
  [ ! -d "$merge_wt" ] || fail "base merge worktree was gated on branch containment"
  [ ! -d "$orphan_wt" ] || fail "finish left an orphan merge worktree"
  [ ! -e "$orphan_lock" ] || fail "finish left an orphan merge lock"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night || fail "uncontained local branch was deleted"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night || fail "uncontained origin branch was deleted"
}

scenario_startfromorigin() {
  local code other remote_head
  fresh_repo
  other="$(other_clone)"
  printf 'remote base\n' > "$other/remote.txt"
  git -C "$other" add remote.txt
  git -C "$other" commit -q -m remote-base
  git -C "$other" push -q origin main
  remote_head="$(git -C "$TMP/origin.git" rev-parse main)"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start from remote base expected 0, got $code: $(cat "$TMP/err")"
  [ -f "$(wt 61)/remote.txt" ] || fail "the ticket did not start from origin/main"
  [ "$(git -C "$(wt 61)" rev-parse HEAD)" = "$remote_head" ] \
    || fail "the new branch tip is not origin/main"
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$remote_head" ] \
    || fail "origin/issue-61 was not published at start"
  [ "$(git -C "$(wt 61)" rev-parse --abbrev-ref '@{upstream}')" = origin/issue-61 ] \
    || fail "issue-61 does not track origin/issue-61"
  posted_events 61 base | grep -qx "worker.started base=$remote_head" \
    || fail "worker.started did not record the fetched base: $(posted_events 61 base)"
}

scenario_startresumesorigin() {
  local code other base remote_head
  fresh_repo
  base="$(git -C "$TMP/repo" rev-parse main)"
  git -C "$TMP/repo" branch issue-61 "$base"
  other="$(other_clone)"
  git -C "$other" checkout -q -b issue-61 origin/main
  printf 'remote ticket\n' > "$other/ticket.txt"
  git -C "$other" add ticket.txt
  git -C "$other" commit -q -m remote-ticket
  git -C "$other" push -q -u origin issue-61
  remote_head="$(git -C "$TMP/origin.git" rev-parse issue-61)"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "resume from origin expected 0, got $code: $(cat "$TMP/err")"
  [ -f "$(wt 61)/ticket.txt" ] || fail "the remote ticket branch was not resumed"
  [ "$(git -C "$(wt 61)" rev-parse HEAD)" = "$remote_head" ] \
    || fail "the local ticket branch was not fast-forwarded to origin"

  fresh_repo
  git -C "$TMP/repo" branch issue-61 main
  git -C "$TMP/repo" worktree add -q "$(wt 61)" issue-61
  other="$(other_clone)"
  git -C "$other" checkout -q -b issue-61 origin/main
  commit_file "$other" standing.txt standing remote-standing
  git -C "$other" push -q -u origin issue-61
  remote_head="$(git -C "$TMP/origin.git" rev-parse issue-61)"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "resume a standing worktree expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$(wt 61)" rev-parse HEAD)" = "$remote_head" ] \
    || fail "the standing worktree was not fast-forwarded to origin"

  fresh_repo
  git -C "$TMP/repo" branch issue-61 main
  reset_log
  code="$(run_dispatch env MMW_FAKE_PASEO_SCENARIO=run-fail \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "a refused runner start expected 2, got $code"
  assert_no_wt 61

  fresh_repo
  git -C "$TMP/repo" branch issue-61 main
  git -C "$TMP/repo" worktree add -q "$(wt 61)" issue-61
  commit_file "$(wt 61)" local-ticket.txt local local-ticket
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "a standing local ticket branch expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$(git -C "$(wt 61)" rev-parse HEAD)" ] \
    || fail "a standing local ticket branch was not published"
}

scenario_startdiverged() {
  local code other
  fresh_repo
  other="$(other_clone)"
  git -C "$other" checkout -q -b issue-61 origin/main
  printf 'remote one\n' > "$other/shared.txt"
  git -C "$other" add shared.txt
  git -C "$other" commit -q -m remote-one
  git -C "$other" push -q -u origin issue-61
  git -C "$TMP/repo" fetch -q origin
  git -C "$TMP/repo" branch issue-61 origin/issue-61
  git -C "$TMP/repo" worktree add -q "$(wt 61)" issue-61
  commit_file "$(wt 61)" local.txt local local
  git -C "$TMP/repo" worktree remove "$(wt 61)"
  commit_file "$other" remote-two.txt two remote-two
  commit_file "$other" remote-three.txt three remote-three
  git -C "$other" push -q origin issue-61
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "diverged start expected 2, got $code"
  assert_no_wt 61
  never_ran
}

scenario_startintofromnight() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b spec-337 main
  printf 'spec\n' > "$TMP/repo/spec.txt"
  git -C "$TMP/repo" add spec.txt
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m spec
  git -C "$TMP/repo" push -q -u origin spec-337
  git -C "$TMP/repo" checkout -q main
  reset_log
  post_ev 76 spec.opened --spec 76 --line "NIGHT OPENED #76" --field into=spec-337
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "night start expected 0, got $code: $(cat "$TMP/err")"
  [ -f "$(wt 61)/spec.txt" ] || fail "the ticket was not cut from origin/spec-337"
  posted_events 61 into | tail -1 | grep -qx "worker.started into=spec-337" \
    || fail "worker.started did not preserve the night's into: $(posted_events 61 into)"
}

scenario_startintooutside() {
  local code
  fresh_repo
  git -C "$TMP/repo" checkout -q -b outside-base
  git -C "$TMP/repo" push -q -u origin outside-base
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "outside-night start expected 0, got $code: $(cat "$TMP/err")"
  posted_events 61 into | grep -qx "worker.started into=outside-base" \
    || fail "outside-night worker.started should record outside-base: $(posted_events 61 into)"

  fresh_repo
  git -C "$TMP/repo" checkout -q -b local-only
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "an unpushed outside-night base expected 2, got $code"
  grep -q "origin/local-only" "$TMP/err" \
    || fail "the missing remote base was not named: $(cat "$TMP/err")"
  assert_no_wt 61
}

scenario_startfromissuebranch() {
  local code tree
  echo "--- outside a night with no earlier worker, start from an issue branch names the branch to start from"
  fresh_repo
  reset_log
  self_picked_worktree
  tree="$(wt 61)"
  code="$( (cd "$tree" && bash "$DISPATCH" "${TOOLS[@]}" start 61 worker) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 2 ] || fail "start from issue-61 with no base branch expected 2, got $code"
}

scenario_startwithoutinto() {
  local code
  fresh_repo
  reset_log
  post_ev 61 worker.started --ticket 61 --line "old worker" \
    --field session=old --field runner=paseo \
    $(start_facts "$(wt 61)" 61 worker) --field into=
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "an old worker.started without into should fall back to the next source, got $code: $(cat "$TMP/err")"
  posted_events 61 into | tail -1 | grep -qx "worker.started into=main" \
    || fail "the new worker.started should record the fallback base branch: $(posted_events 61 into)"
}

# What is left at a ticket's workspace path when a worktree was deleted by hand.
scenario_startstrayworkspace() {
  local code
  echo "--- a worktree deleted by hand is still registered with git, and start makes it again"
  fresh_repo
  reset_log
  mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q -b issue-61 "$(wt 61)" main
  rm -rf "$(wt 61)"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start over a pruned registration expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$(wt 61)" rev-parse --abbrev-ref HEAD)" = issue-61 ] || fail "the workspace was not made again"

  echo "--- an empty directory there is removed and the worktree made"
  fresh_repo
  reset_log
  mkdir -p "$(wt 62)"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 62 worker)"
  [ "$code" = 0 ] || fail "start over an empty directory expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$(wt 62)" rev-parse --abbrev-ref HEAD)" = issue-62 ] || fail "the workspace was not made"

  echo "--- a directory holding files is refused as what it is, and kept"
  fresh_repo
  reset_log
  mkdir -p "$(wt 63)"
  printf 'keep\n' > "$(wt 63)/notes.txt"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 63 worker)"
  [ "$code" = 2 ] || fail "start over a directory with files expected 2, got $code: $(cat "$TMP/err")"
  [ -f "$(wt 63)/notes.txt" ] || fail "the files were not kept"
}

scenario_replacepushes() {
  local code other first
  fresh_repo
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "first start expected 0, got $code: $(cat "$TMP/err")"
  first="$(cat "$TMP/out")"
  printf 'handoff\n' > "$(wt 61)/handoff.txt"
  git -C "$(wt 61)" add handoff.txt
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "replacement expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show issue-61:handoff.txt | grep -qx handoff \
    || fail "replacement did not push the committed handoff"
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 | grep -q '^wip(#61):' \
    || fail "replacement did not push the named wip commit"
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 | grep -qF -- "$first" \
    || fail "the wip commit does not name the replaced session $first"

  commit_file "$(wt 61)" local-after.txt local local-after
  other="$(other_clone)"
  git -C "$other" fetch -q origin
  git -C "$other" checkout -q -b issue-61 origin/issue-61
  commit_file "$other" remote-after.txt remote remote-after
  git -C "$other" push -q origin issue-61
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "a divergent replacement expected 2, got $code"
  hasnt "paseo :: archive"
}

scenario_retractpushes() {
  local code session
  fresh_repo
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  session="$(cat "$TMP/out")"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  printf 'retract\n' > "$(wt 61)/retract.txt"
  git -C "$(wt 61)" add retract.txt
  set_agent_status "$session" closed
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show issue-61:retract.txt | grep -qx retract \
    || fail "retract did not push the committed handoff"
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 | grep -q '^wip(#61):' \
    || fail "retract did not push the named wip commit"
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 | grep -qF -- "$session" \
    || fail "the wip commit does not name session $session"
}

scenario_suspendpushes() {
  local code
  fresh_repo
  reset_log
  write_open_batch
  open_a_night
  printf 'suspend\n' > "$(wt 61)/suspend.txt"
  git -C "$(wt 61)" add suspend.txt
  printf 'also suspend\n' > "$(wt 63)/also-suspend.txt"
  git -C "$(wt 63)" add also-suspend.txt
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" suspend 76)"
  [ "$code" = 0 ] || fail "suspend expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show issue-61:suspend.txt | grep -qx suspend \
    || fail "suspend did not push the committed handoff"
  git -C "$TMP/origin.git" show issue-63:also-suspend.txt | grep -qx 'also suspend' \
    || fail "suspend did not push every interrupted ticket branch"
}

scenario_handoffpushrejected() {
  local code session other remote_head
  fresh_repo
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  session="$(cat "$TMP/out")"
  [ "$code" = 0 ] || fail "first start expected 0, got $code: $(cat "$TMP/err")"
  printf 'local work\n' > "$(wt 61)/local.txt"
  git -C "$(wt 61)" add local.txt
  other="$(other_clone)"
  git -C "$other" fetch -q origin
  git -C "$other" checkout -q -b issue-61 origin/issue-61
  commit_file "$other" remote.txt remote remote-first
  git -C "$other" push -q origin issue-61
  remote_head="$(git -C "$TMP/origin.git" rev-parse issue-61)"
  set_agent_status "$session" closed
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "rejected retract push expected 2, got $code"
  assert_wt 61
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$remote_head" ] \
    || fail "retract rewrote the commit another clone pushed"
}

# ------------------------------------------------------------------ origin landing

scenario_advancemergeworktree() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed caller_head caller_branch code merge_tree
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  caller_head="$(git -C "$TMP/repo" rev-parse HEAD)"
  caller_branch="$(git -C "$TMP/repo" rev-parse --abbrev-ref HEAD)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0, got $code: $(cat "$TMP/err")"
  merge_tree="$TMP/repo/.worktrees/merge-main"
  [ -d "$merge_tree" ] || fail "the persistent merge worktree was not created"
  [ "$(git -C "$merge_tree" rev-parse --abbrev-ref HEAD)" = HEAD ] \
    || fail "the merge worktree is not detached"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$caller_head" ] \
    || fail "the caller checkout HEAD moved"
  [ "$(git -C "$TMP/repo" rev-parse --abbrev-ref HEAD)" = "$caller_branch" ] \
    || fail "the local base branch moved"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "origin/main does not contain the passed commit"
}

scenario_advancepassedcommit() {
  reset_log
  fresh_repo
  make_branch issue-61 passed.txt passed
  local passed extra code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" checkout -q issue-61
  commit_file "$TMP/repo" extra.txt extra after-pass
  extra="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" checkout -q main
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "ticket.passed commit was not merged"
  git -C "$TMP/repo" fetch -q origin
  if git -C "$TMP/repo" merge-base --is-ancestor "$extra" origin/main; then
    fail "the commit after ticket.passed was merged"
  fi
  [ "$(git -C "$TMP/origin.git" log -1 --format=%s main)" = "Merge branch 'issue-61'" ] \
    || fail "the merge subject is not fixed"
}

scenario_advanceunreadableinto() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed before code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          FAKE_GH_UNREADABLE_ON_COMMENT_READ=2 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "an unreadable base-branch event expected exit 2, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] \
    || fail "an unreadable event fell back to the caller branch and moved origin/main"
}

scenario_advancewithoutpassedcommit() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local before code
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main)]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "ticket.passed without commit expected exit 2, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] \
    || fail "the unverified issue-61 tip moved origin/main"
}

setup_bounced_conflict() {
  local round="${1:-second}"
  reset_log
  fresh_repo
  commit_file "$TMP/repo" shared.txt base shared-base
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 shared.txt ticket
  local passed other
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  other="$(other_clone)"
  git -C "$other" pull -q --ff-only origin main
  commit_file "$other" shared.txt sibling sibling
  git -C "$other" push -q origin main
  write_one_passed 61 "$passed"
  post_ev 76 spec.opened --spec 76 --line opened --field into=main --field project=project
  if [ "$round" = second ] || [ "$round" = older ]; then
    MMW_BOUNCE_ROUND="$round" MMW_PREVIOUS_BOUNCE="$(ev ticket.bounced 61 "bounced once" --spec 76 \
      --field reason=conflict --field commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
      --field into=main --json-field 'files=["shared.txt"]')" python3 - "$TMP/tickets.json" <<'PY'
import json, os, sys
from pathlib import Path

path = Path(sys.argv[1])
rows = json.loads(path.read_text())
comment = json.loads(os.environ["MMW_PREVIOUS_BOUNCE"])
if os.environ.get("MMW_BOUNCE_ROUND") == "older":
    import re
    comment = re.sub(r'"at":"[^"]+"', '"at":"2000-01-01T00:00:00Z"', comment)
rows[0].setdefault("comments", []).insert(0, comment)
path.write_text(json.dumps(rows))
PY
  fi
  if [ "$round" = closed ]; then
    post_ev 76 spec.closed --spec 76 --line closed
  fi
  seed_workspace 61
}

scenario_advancecapbounce() {
  setup_bounced_conflict first
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
rows = json.loads(path.read_text())
rows.extend({"number": number, "state": "OPEN", "labels": ["ready-for-agent"],
             "body": "## Parent\n\n#76\n"} for number in (60, 59))
path.write_text(json.dumps(rows))
PY
  cp "$MMW_HOME/models.json" "$TMP/models-before-cap.json"
  python3 - "$MMW_HOME/models.json" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
config = json.loads(path.read_text())
config["max_workers"] = 2
path.write_text(json.dumps(config))
PY
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "capped bounce expected 0, got $code: $(cat "$TMP/err")"
  [ "$(count_of 'paseo :: run')" = 2 ] || fail "the bounce advance did not start exactly two workers"
  python3 - "$MMW_FAKE_PASEO_STATE/runs.jsonl" <<'PY'
import json, sys
from pathlib import Path
runs = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
assert [run["title"] for run in runs] == ["#59 worker", "#60 worker"], runs
PY
  [ "$?" = 0 ] || fail "advance restarted the bounce instead of the two smaller tickets"
  grep -q 'started 2' "$TMP/err" || fail "advance did not report two starts"
  python3 - "$TMP/err" <<'PY'
import re, sys
from pathlib import Path
lines = Path(sys.argv[1]).read_text().splitlines()
assert any("#61" in line and "max_workers" in line and re.search(r"\b2\b", line)
           and "#59" in line and "#60" in line for line in lines), lines
PY
  [ "$?" = 0 ] || fail "the bounce does not name the cap and both new holders"
  posted_events 61 reason | grep -q '^ticket.bounced reason=conflict$' \
    || fail "#61 was not bounced"
  assert_wt 61
  cp "$TMP/models-before-cap.json" "$MMW_HOME/models.json"
}

scenario_bounceretriesonce() {
  setup_bounced_conflict first
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a first bounce should return to the agent queue: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-label :: needs-triage :: --add-label :: ready-for-agent :: --remove-assignee :: @me"
  hasnt "gh :: issue :: edit :: 61 :: --remove-label :: ready-for-agent :: --add-label :: needs-triage"
  grep -q 'started 1' "$TMP/err" \
    || fail "the same advance should restart the ticket it just bounced, in a later separate computation (ADR 0027): $(cat "$TMP/err")"
  posted_events 61 reason | grep -q '^ticket.bounced reason=conflict$' \
    || fail "the first conflict posted no ticket.bounced event with its reason"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_MUTATES_ISSUES=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  grep -q 'started 0' "$TMP/err" \
    || fail "a ticket the previous advance already restarted should not be started again: $(cat "$TMP/err")"

  setup_bounced_conflict older
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a bounce from before this night should not consume its retry: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-label :: needs-triage :: --add-label :: ready-for-agent :: --remove-assignee :: @me"
  hasnt "gh :: issue :: edit :: 61 :: --remove-label :: ready-for-agent :: --add-label :: needs-triage"

  setup_bounced_conflict second
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a second bounce should be handed to triage: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-label :: ready-for-agent :: --add-label :: needs-triage :: --remove-assignee :: @me"
  hasnt "gh :: issue :: edit :: 61 :: --remove-label :: needs-triage :: --add-label :: ready-for-agent"

  setup_bounced_conflict closed
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "a landing outside an open night should be handed to triage: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-label :: ready-for-agent :: --add-label :: needs-triage :: --remove-assignee :: @me"
  hasnt "gh :: issue :: edit :: 61 :: --remove-label :: needs-triage :: --add-label :: ready-for-agent"
  echo "the first conflict returns once; the second goes to triage"
}

scenario_advancebouncedconflict() {
  setup_bounced_conflict
  make_branch issue-62 clean.txt clean
  local clean event code
  clean="$(git -C "$TMP/repo" rev-parse issue-62)"
  event="$(ev ticket.passed 62 "ALL MET" --field branch=issue-62 --field "commit=$clean" --field into=main)"
  MMW_EVENT="$event" python3 - "$TMP/tickets.json" <<'PY'
import json, os, sys
from pathlib import Path

path = Path(sys.argv[1])
rows = json.loads(path.read_text())
rows.append({"number": 62, "state": "CLOSED", "labels": [],
             "closedAt": "2026-09-11T03:00:00Z",
             "comments": [json.loads(os.environ["MMW_EVENT"])]})
path.write_text(json.dumps(rows))
PY
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a bounced conflict should let advance continue: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:clean.txt >/dev/null 2>&1 \
    || fail "the ticket after the conflict was not merged"
  has "gh :: issue :: reopen :: 61"
  has "gh :: issue :: edit :: 61 :: --remove-label :: ready-for-agent :: --add-label :: needs-triage :: --remove-assignee :: @me"
  posted_events 61 reason files | grep -q "ticket.bounced reason=conflict files=\['shared.txt'\]" \
    || fail "ticket.bounced does not name the conflict: $(posted_events 61 reason files)"
  [ -d "$TMP/repo/.worktrees/merge-main" ] || fail "the detached merge worktree was not kept"
  assert_wt 61
}

scenario_advancenohalfmerge() {
  setup_bounced_conflict
  local before code
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0: $(cat "$TMP/err")"
  ! git -C "$TMP/repo" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 \
    || fail "the caller checkout has MERGE_HEAD"
  ! git -C "$TMP/repo/.worktrees/merge-main" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 \
    || fail "the merge worktree has MERGE_HEAD"
  [ -d "$TMP/repo/.worktrees/merge-main" ] || fail "the merge worktree was not created"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "origin/main moved"
  posted_events 61 reason | grep -qx 'ticket.bounced reason=conflict' \
    || fail "the conflict was not recorded: $(posted_events 61 reason)"
}

# Ticket #61 passed, with a repository whose scripts/check runs <body>.
setup_checked_ticket() {
  reset_log
  fresh_repo
  put_check "$TMP/repo" "$1"
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m checks
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  local passed
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
}

scenario_bounceansitail() {
  setup_checked_ticket "printf '\033[32mFAIL lint-python\033[0m\n\\^[[32mpyrefly\\^[[0m\n'; exit 1"
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "colour output should bounce and continue: $(cat "$TMP/err")"
  gh_comments_json 61 | python3 "$EVENTS_PY" fold 61 --comments-file - > "$TMP/fold.json" \
    || fail "the ticket fold could not read the bounce"
  MMW_BOUNCE="$(bounced_comment 61)" python3 - "$TMP/fold.json" <<'PYTEST' || fail "the bounce must retain readable check output without colour codes"
import json, os, sys
from pathlib import Path
state = json.loads(Path(sys.argv[1]).read_text())
assert state["unreadable"] == [], state["unreadable"]
assert state["bounced"], state
raw = os.environ["MMW_BOUNCE"].split("<!-- mmw ", 1)[1].rsplit(" -->", 1)[0]
bounce = json.loads(raw)
assert bounce["reason"] == "checks", bounce
assert bounce["commands"][0]["tail"] == "FAIL lint-python\npyrefly", bounce
PYTEST
}

setup_landed_criterion_change() {
  reset_log
  fresh_repo
  rm -f "$TMP/selected" "$TMP/unselected" "$TMP/selection"
  open_night
  git -C "$TMP/repo" checkout -q -b issue-61
  mkdir -p "$TMP/repo/tests" "$TMP/repo/unaffected"
  printf 'echo run >> "%s"\n[ ! -e config-red ] && test "$1" = original && echo named-green\n' "$TMP/selected" > "$TMP/repo/tests/named.sh"
  printf 'echo unexpected-run >> "%s"\n' "$TMP/unselected" > "$TMP/repo/unaffected/other.sh"
  git -C "$TMP/repo" add tests unaffected
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm named-test
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" checkout -q main
  write_one_passed 61 "$passed"
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
rows = json.loads(p.read_text())
rows[0]["body"] = """## Acceptance criteria

- [ ] AC1: the named test runs
  CHECK: bash tests/named.sh original
  EXPECT: /named-green/
  EVIDENCE: pending
- [ ] AC2: an unrelated criterion
  CHECK: bash unaffected/other.sh
  EXPECT: /anything/
  EVIDENCE: pending
"""
p.write_text(json.dumps(rows))
PY
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "first ticket must land: $(cat "$TMP/err")"
  posted_events 61 | grep -qx ticket.landed || fail "first ticket did not land"
  git -C "$TMP/repo" fetch -q origin
  git -C "$TMP/repo" checkout -q -b issue-62 origin/main
  printf 'echo run >> "%s"\n[ ! -e config-red ] && test "$1" = renamed && echo named-green\n' "$TMP/selected" > "$TMP/repo/tests/named.sh"
  git -C "$TMP/repo" add tests/named.sh
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -qm rename-test
  passed="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" checkout -q main
  MMW_PASS="$(ev ticket.passed 62 'ALL MET' --field branch=issue-62 --field "commit=$passed" --field into=main)" \
    python3 - "$TMP/tickets.json" <<'PY'
import json, os, sys
from pathlib import Path
p = Path(sys.argv[1])
rows = json.loads(p.read_text())
rows.append({"number": 62, "state": "CLOSED", "labels": [],
             "closedAt": "2026-09-11T02:00:00Z", "comments": [json.loads(os.environ["MMW_PASS"])]})
p.write_text(json.dumps(rows))
PY
  seed_workspace 62
  rm -f "$TMP/unselected"
}

scenario_landrunsnolandedcriteria() {
  local command passed code
  for command in land advance; do
    setup_landed_criterion_change
    rm -f "$TMP/selected" "$TMP/unselected"
    passed="$(git -C "$(wt 62)" rev-parse HEAD)"
    if [ "$command" = land ]; then
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" land 62)"
    else
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
    fi
    [ "$code" = 0 ] || fail "$command failed: $(cat "$TMP/err")"
    git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main || fail "the ticket did not land"
    [ ! -e "$TMP/selected" ] || fail "landing ran a criterion of a landed ticket"
    [ ! -e "$TMP/unselected" ] || fail "landing ran an unrelated criterion"
    [ -z "$(posted_events 62 | grep '^ticket.bounced')" ] || fail "the ticket bounced"
    posted_events 62 | grep -qx ticket.landed || fail "the landing was not recorded"
  done
}

scenario_advancebouncedchecks() {
  setup_checked_ticket "printf 'red-%s\\n' tail; exit 1"
  local before code
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a red merge check should bounce and continue: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "origin/main moved"
  posted_events 61 reason commands | grep -q "ticket.bounced reason=checks" \
    || fail "ticket.bounced reason is wrong: $(posted_events 61 reason commands)"
  posted_events 61 commands | grep -q "red-tail" \
    || fail "ticket.bounced omits the command tail: $(posted_events 61 commands)"
}

scenario_recheckisgone() {
  local code rejected
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" recheck 76)"
  [ "$code" = 2 ] || fail "recheck must be an unknown command, got $code"
  rejected="$(cat "$TMP/err")"
  ! grep -q 'dispatch.sh recheck' "$TMP/err" || fail "usage still lists recheck"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}")"
  [ "$code" = 2 ] || fail "missing command must print usage and exit 2"
  [ "$rejected" = "$(cat "$TMP/err")" ] || fail "recheck did not take the unknown-command usage path"
  ! grep -q 'dispatch.sh recheck' "$TMP/err" || fail "usage still lists recheck"
}

scenario_landbouncesredonredbase() {
  local command before code
  for command in land advance; do
    rm -f "$TMP/check-runs"
    setup_checked_ticket "printf '%s\\n' \"\${1:-default}\" >> '$TMP/check-runs'
echo 'FAIL unit 0s'
exit 1"
    before="$(git -C "$TMP/origin.git" rev-parse main)"
    if [ "$command" = land ]; then
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" land 61)"
      [ "$code" = 0 ] || fail "land should record the bounce, got $code"
    else
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
      [ "$code" = 0 ] || fail "advance should bounce and continue: $(cat "$TMP/err")"
    fi
    [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "the red merge landed"
    posted_events 61 reason | grep -qx 'ticket.bounced reason=checks' || fail "the red merge did not bounce"
    [ "$(cat "$TMP/check-runs" 2>/dev/null)" = default ] || fail "landing compared a failure against the base"
    [ -z "$(posted_events 61 | grep '^ticket.landed')" ] || fail "a red merge has a ticket.landed record"
    assert_resume_quotes_posted_bounce 61
  done
}

# 29 lines, the failing test's name on line 10. The command builds that name at
# runtime, so the command text itself does not contain it.
twenty_nine_line_check() {
  cat <<'EOF'
python3 -c 'import sys; name="test_price_"+"rounds"; lines=["noise-%d"%i for i in range(1,30)]; lines[9]=name; sys.stdout.write("\n".join(lines)+"\n"); sys.exit(1)'
EOF
}

# The name counts only as an excerpt line after the command heading. A match inside
# the command, the summary, or the event block does not.
excerpt_has_name() {
  local body="$1" name="$2"
  MMW_BODY="$body" MMW_NAME="$name" python3 -c '
import os, sys
body = os.environ["MMW_BODY"]
name = os.environ["MMW_NAME"]
prose = body.split("<!--", 1)[0]
lines = prose.splitlines()
hits = [line for line in lines[1:] if name in line and "python3" not in line]
if not hits:
    sys.stderr.write("excerpt drops %s:\n%s\n" % (name, prose))
    sys.exit(1)
'
}

# Read the bounce the fake tracker holds, then claim that same ticket. The resume
# quotes the Failed checks slice of the comment that was posted.
assert_resume_quotes_posted_bounce() {
  local n="${1:-61}" body quote out err code commit shape
  body="$(bounced_comment "$n")"
  quote="$(printf '%s\n' "$body" | python3 -c '
import sys
for line in sys.stdin:
    at = line.find("Failed checks:")
    if at >= 0:
        print(line[at:].strip())
        raise SystemExit(0)
raise SystemExit(1)
')" || fail "the posted bounce has no Failed checks: line: $body"
  commit="$(git -C "$(wt "$n")" rev-parse HEAD)"
  # A worker's own run records the shape of the criteria it ran; preflight resumes only
  # from a run whose shape matches the ticket's criteria now.
  shape="$(cd "$(wt "$n")" && python3 - "$(dirname "$SKILL")/verify-ticket/scripts/verify-ticket.py" "$n" <<'SHAPE'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("vt", sys.argv[1])
vt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vt)
print(vt.shape_digest(vt.section(vt.fetch_body(int(sys.argv[2])), "Acceptance criteria")))
SHAPE
)" || fail "could not read #$n's criteria shape"
  post_ev "$n" ticket.checked --ticket "$n" --line "self run" \
    --field run=self --field "commit=$commit" --field result=met --field "shape=$shape"
  out="$TMP/preflight-$n.out"
  err="$TMP/preflight-$n.err"
  code="$(
    cd "$(wt "$n")" \
      && python3 "$(dirname "$SKILL")/verify-ticket/scripts/verify-ticket.py" "$n" --preflight \
         >"$out" 2>"$err"
    echo "$?"
  )"
  [ "$code" = 0 ] || fail "preflight on the bounced ticket exited $code: $(cat "$err") $(cat "$out")"
  MMW_QUOTE="$quote" MMW_OUT="$(cat "$out")" python3 -c '
import os, sys
out = os.environ["MMW_OUT"].splitlines()
quote = os.environ["MMW_QUOTE"]
resume = [i for i, line in enumerate(out) if line.startswith("RESUME:")]
if len(resume) != 1:
    sys.stderr.write("preflight did not print one RESUME line:\n%s\n" % os.environ["MMW_OUT"])
    sys.exit(1)
i = resume[0]
if not out[i].startswith("RESUME: Integrate and run every criterion"):
    sys.stderr.write("resume is not the bounce step: %s\n" % out[i])
    sys.exit(1)
following = out[i + 1] if i + 1 < len(out) else ""
if following != quote:
    sys.stderr.write("resume does not quote the posted bounce\nposted: %s\nresume: %s\n" % (quote, following))
    sys.exit(1)
' || fail "preflight did not quote the bounce posted on #$n"
}

scenario_advancebouncedkeepserrors() {
  local before code body
  setup_checked_ticket "$(twenty_nine_line_check)"
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a red merge check should bounce and continue: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "origin/main moved"
  body="$(bounced_comment 61)"
  excerpt_has_name "$body" test_price_rounds \
    || fail "ticket.bounced drops the test name on line 10 of a 29-line check"
}

scenario_advancebouncedsteps() {
  local before code body
  setup_checked_ticket 'echo "PASS lint 0s"; echo "alpha-line"; echo "FAIL unit 1s"; echo "FAIL e2e 2s"; exit 1'
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a red scripts/check should bounce and continue: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "origin/main moved"
  body="$(bounced_comment 61)"
  MMW_BODY="$body" python3 -c '
import os, sys
prose = os.environ["MMW_BODY"].split("<!--", 1)[0]
first = prose.splitlines()[0] if prose else ""
at = first.find("Failed checks:")
if at < 0:
    sys.stderr.write("the bounce line has no Failed checks: token:\n%s\n" % first)
    sys.exit(1)
quote = first[at:]
for token in ("scripts/check", "unit", "e2e"):
    if token not in quote:
        sys.stderr.write("Failed checks line omits %r:\n%s\n" % (token, quote))
        sys.exit(1)
if "lint" in quote:
    sys.stderr.write("Failed checks line names a step that passed:\n%s\n" % quote)
    sys.exit(1)
if "alpha-line" not in prose or ".scratch/checks/61/1.log" not in prose:
    sys.stderr.write("the bounce omits the last lines or the log path:\n%s\n" % prose)
    sys.exit(1)
' || fail "the bounce does not name the failing steps, their last lines and the log"
  assert_resume_quotes_posted_bounce 61
}

scenario_advancebouncedsavesoutput() {
  local before code body log
  setup_checked_ticket "$(twenty_nine_line_check)"
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a red merge check should bounce and continue: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "origin/main moved"
  log="$(wt 61)/.scratch/checks/61/1.log"
  [ -f "$log" ] || fail "the full check output is not at $log"
  [ "$(sed -n '10p' "$log")" = "test_price_rounds" ] \
    || fail "line 10 of the saved output is '$(sed -n '10p' "$log")'"
  [ "$(grep -c . "$log" | tr -d ' ')" = 29 ] \
    || fail "the saved output is not the full 29 lines: $(grep -c . "$log")"
  body="$(bounced_comment 61)"
  printf '%s\n' "$body" | grep -q '.scratch/checks/61/1.log' \
    || fail "ticket.bounced does not name the saved output: $body"
}

scenario_advancechecksonce() {
  rm -f "$TMP/check-runs"
  setup_checked_ticket "printf 'x\\n' >> '$TMP/check-runs'"
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" merge-base --is-ancestor origin/main "$passed" \
    || fail "the fixture's ticket does not contain origin/main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance failed: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "the ticket did not land"
  [ "$(wc -l < "$TMP/check-runs" 2>/dev/null | tr -d ' ')" = 1 ] \
    || fail "the merge result of a ticket on an unmoved base was not checked exactly once"
}

# A green repository check of ticket 61's passed commit, as the worker's run records it:
# `repository_record <base commit>`.
repository_record() {
  post_ev 61 ticket.checked --ticket 61 --line "Repository check" --actor worker --stage close \
    --field run=repository --field result=met --field tier=default \
    --field "commit=$(git -C "$TMP/repo" rev-parse issue-61)" --field "base=$1" \
    --field "machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
    --json-field 'steps=["unit"]' "${@:2}"
}


scenario_landcheckseverymerge() {
  local command passed code base
  for command in land advance; do
    rm -f "$TMP/check-runs"
    setup_checked_ticket "printf '%s %s %s %s\\n' \"\$#\" \"\$MMW_BASE_REF\" \"\$(git rev-parse HEAD^1)\" \"\$(git rev-parse HEAD^2)\" >> '$TMP/check-runs'"
    passed="$(git -C "$TMP/repo" rev-parse issue-61)"
    base="$(git -C "$TMP/origin.git" rev-parse main)"
    repository_record "$base"
    if [ "$command" = land ]; then
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" land 61)"
    else
      code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
    fi
    [ "$code" = 0 ] || fail "$command failed: $(cat "$TMP/err")"
    git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main || fail "the ticket did not land"
    [ "$(cat "$TMP/check-runs" 2>/dev/null)" = "0 origin/main $base $passed" ] \
      || fail "$command did not run the default tier exactly once on the merge result"
    gh_comments_json 61 | python3 -c '
import json, sys
for comment in json.load(sys.stdin)["comments"]:
    body = comment["body"]
    if "<!-- mmw " not in body:
        continue
    payload = json.loads(body.split("<!-- mmw ", 1)[1].split(" -->", 1)[0])
    if payload["event"] == "ticket.landed":
        assert not ({"base_red", "landed_base_red", "checked_by"} & payload.keys()), payload
' || fail "ticket.landed carries removed check fields"
  done
}

scenario_advancebaseref() {
  setup_checked_ticket 'printf "%s\\n" "$MMW_BASE_REF" > "$MMW_BASE_REF_FILE"'
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_BASE_REF_FILE="$TMP/base-ref" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "MMW_BASE_REF was not origin/main: $(cat "$TMP/err")"
  [ "$(cat "$TMP/base-ref" 2>/dev/null)" = origin/main ] \
    || fail "the check did not receive literal origin/main"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "the ticket did not land after the base-ref check"
  [ -z "$(posted_events 61 reason | grep '^ticket.bounced')" ] \
    || fail "the green base-ref check bounced the ticket"
}

# A ticket whose merge cannot be checked stays passed: not landed, not bounced, the
# merge worktree back on origin/<into>, and advance exits 2.
assert_held_not_bounced() {
  local label="$1" before="$2" code="$3"
  [ "$code" = 2 ] || fail "$label: advance expected 2, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "$label: origin/main moved"
  [ -z "$(posted_events 61 | grep -E '^ticket\.(bounced|landed)')" ] \
    || fail "$label: the ticket was bounced or landed: $(posted_events 61)"
  hasnt "gh :: issue :: reopen :: 61"
  [ "$(git -C "$TMP/repo/.worktrees/merge-main" rev-parse HEAD)" = "$before" ] \
    || fail "$label: the merge worktree was not reset to origin/main"
}

# Ticket #61 passed on a repository whose base has no scripts/check.
setup_unchecked_ticket() {
  reset_log
  fresh_repo
  git -C "$TMP/repo" rm -q scripts/check
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "no check"
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  write_one_passed 61 "$(git -C "$TMP/repo" rev-parse issue-61)"
  seed_workspace 61
}

scenario_advancenochecks() {
  local before code
  echo "--- no scripts/check refuses the landing: advance exits 2, the ticket is not bounced"
  setup_unchecked_ticket
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  assert_held_not_bounced "no scripts/check" "$before" "$code"
  grep -q 'scripts/check' "$TMP/err" || fail "the refusal does not name scripts/check: $(cat "$TMP/err")"

  echo "--- land <n> refuses it the same way"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" != 0 ] || fail "land without scripts/check exited 0: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "land moved origin/main"
  [ -z "$(posted_events 61 | grep -E '^ticket\.(bounced|landed)')" ] \
    || fail "land bounced or landed the ticket: $(posted_events 61)"
  grep -q 'scripts/check' "$TMP/err" || fail "land's refusal does not name scripts/check: $(cat "$TMP/err")"
}

scenario_advancecheckcannotrun() {
  local before code
  echo "--- scripts/check exit 2 on the merge: the ticket stays passed, advance stops with exit 2"
  setup_checked_ticket 'echo "uv: command not found" >&2; exit 2'
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  assert_held_not_bounced "exit 2" "$before" "$code"
  grep -q 'uv: command not found' "$TMP/err" \
    || fail "stderr does not carry what the check said: $(cat "$TMP/err")"
  grep -q '.scratch/checks/61/1.log' "$TMP/err" \
    || fail "stderr does not name the full output: $(cat "$TMP/err")"
  echo "--- once the machine is fixed, advance lands it"
  reset_log
  put_check "$TMP/repo" 'exit 0'
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m "fixed check"
  git -C "$TMP/repo" push -q origin main
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance after the fix expected 0, got $code: $(cat "$TMP/err")"
  posted_events 61 | grep -q '^ticket.landed' || fail "the ticket did not land after the fix"
}

scenario_advanceraced() {
  reset_log
  fresh_repo
  cat > "$TMP/repo/race-check.sh" <<'SH'
#!/usr/bin/env bash
set -e
if [ ! -e "$MMW_RACE_MARKER" ]; then
  git -C "$MMW_RACE_CLONE" pull -q --ff-only origin main
  printf 'race\n' > "$MMW_RACE_CLONE/race.txt"
  git -C "$MMW_RACE_CLONE" add race.txt
  git -C "$MMW_RACE_CLONE" commit -q -m race
  git -C "$MMW_RACE_CLONE" push -q origin main
  : > "$MMW_RACE_MARKER"
fi
SH
  put_check "$TMP/repo" 'exec bash race-check.sh'
  git -C "$TMP/repo" add race-check.sh
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m checks
  git -C "$TMP/repo" push -q origin main
  local other passed code
  other="$(other_clone)"
  make_branch issue-61 ticket.txt ticket
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_RACE_CLONE="$other" MMW_RACE_MARKER="$TMP/raced.once" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "the non-fast-forward race was not retried: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:race.txt >/dev/null || fail "the competing commit was lost"
  git -C "$TMP/origin.git" show main:ticket.txt >/dev/null || fail "the ticket commit was not retried"
}

scenario_advanceoverlap() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed first second waited code1 code2
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  first="$TMP/advance-first"
  second="$TMP/advance-second"
  (
    cd "$TMP/repo" || exit 99
    env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
      FAKE_GH_COMMENTS_MARKER="$first.ready" FAKE_GH_COMMENTS_RELEASE="$TMP/advance.release" \
      MMW_GH_LAST_BODY="$first.body" bash "$DISPATCH" "${TOOLS[@]}" advance 76 \
      > "$first.out" 2> "$first.err"
    printf '%s\n' "$?" > "$first.code"
  ) &
  first=$!
  (
    cd "$TMP/repo" || exit 99
    env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
      FAKE_GH_COMMENTS_MARKER="$second.ready" FAKE_GH_COMMENTS_RELEASE="$TMP/advance.release" \
      MMW_GH_LAST_BODY="$second.body" bash "$DISPATCH" "${TOOLS[@]}" advance 76 \
      > "$second.out" 2> "$second.err"
    printf '%s\n' "$?" > "$second.code"
  ) &
  second=$!
  waited=0
  until [ -e "$TMP/advance-first.ready" ] && [ -e "$TMP/advance-second.ready" ]; do
    sleep 0.05
    waited=$((waited + 1))
    [ "$waited" -lt 200 ] || fail "the two advances did not both read the pre-landing snapshot"
  done
  : > "$TMP/advance.release"
  wait "$first"; wait "$second"
  code1="$(cat "$TMP/advance-first.code")"
  code2="$(cat "$TMP/advance-second.code")"
  [ "$code1" = 0 ] && [ "$code2" = 0 ] \
    || fail "overlapping advances failed: first=$code1 $(cat "$TMP/advance-first.err"); second=$code2 $(cat "$TMP/advance-second.err")"
  [ "$(posted_events 61 | grep -c '^ticket\.landed' | tr -d ' ')" = 1 ] \
    || fail "overlapping advances wrote duplicate ticket.landed events: $(posted_events 61)"
}

scenario_advancelandedfields() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed code merge
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse main)"
  [ "$merge" != "$passed" ] || fail "a non-ancestor ticket was not kept as its own merge commit"
  posted_events 61 commit into merge | grep -qx \
    "ticket.landed commit=$passed into=main merge=$merge" \
    || fail "ticket.landed fields are wrong: $(posted_events 61 commit into merge)"
}

# Two nights on one repository, each landing into its own base branch at the same time.
# Each merge runs in its own merge worktree under its own lock, so the two overlap in
# time, and neither base branch receives the other night's ticket. The slow check marks
# when each merge's checks begin and end: both begin before either ends only when
# nothing serialises the two. Each night posts into its own fake tracker state and its
# own fake body file: the fake gh stages a comment body in a file before storing it, and
# two posts at the same instant would overwrite each other there. dispatch.sh itself
# passes the body to gh directly.
scenario_parallelbases() {
  reset_log
  fresh_repo
  python3 - "$STATE_DIR/watches.json" <<'PY'
import json, sys
watches = json.load(open(sys.argv[1]))
watches["spec:77"] = {**watches["spec:76"], "spec": 77}
json.dump(watches, open(sys.argv[1], "w"))
PY
  cat > "$TMP/repo/slow-check.sh" <<'SH'
#!/usr/bin/env bash
echo "start $MMW_BASE_REF" >> "$MMW_OVERLAP_LOG"
sleep 3
echo "end $MMW_BASE_REF" >> "$MMW_OVERLAP_LOG"
SH
  put_check "$TMP/repo" 'exec bash slow-check.sh'
  git -C "$TMP/repo" add slow-check.sh
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m checks
  git -C "$TMP/repo" push -q origin main
  git -C "$TMP/repo" checkout -q -b feature main
  commit_file "$TMP/repo" feature.txt feature "feature base"
  git -C "$TMP/repo" push -q -u origin feature
  git -C "$TMP/repo" checkout -q main
  make_branch issue-61 ticket-61.txt "lands on main"
  git -C "$TMP/repo" checkout -q -b issue-62 feature
  commit_file "$TMP/repo" ticket-62.txt "lands on feature" issue-62
  git -C "$TMP/repo" checkout -q main
  local passed61 passed62 side log="$TMP/overlap.log"
  passed61="$(git -C "$TMP/repo" rev-parse issue-61)"
  passed62="$(git -C "$TMP/repo" rev-parse issue-62)"
  cat > "$TMP/tickets-76.json" <<JSON
[{"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
  "assignees": ["mmw-bot"], "parent": {"number": 76},
  "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field "commit=$passed61" --field into=main)]}]
JSON
  cat > "$TMP/tickets-77.json" <<JSON
[{"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
  "assignees": ["mmw-bot"], "parent": {"number": 77},
  "comments": [$(ev ticket.passed 62 "ALL MET" --field branch=issue-62 --field "commit=$passed62" --field into=feature)]}]
JSON
  rm -f "$log"
  for side in 76 77; do
    rm -rf "$TMP/state-$side"
    cp -R "$MMW_FAKE_PASEO_STATE" "$TMP/state-$side"
    (cd "$TMP/repo" && env FAKE_GH_TICKETS_FILE="$TMP/tickets-$side.json" \
       MMW_FAKE_PASEO_STATE="$TMP/state-$side" MMW_GH_LAST_BODY="$TMP/gh-last-body-$side" \
       MMW_OVERLAP_LOG="$log" \
       bash "$DISPATCH" "${TOOLS[@]}" advance "$side" > "$TMP/out-$side" 2> "$TMP/err-$side"
     echo "$?" > "$TMP/code-$side") &
  done
  wait
  for side in 76 77; do
    [ "$(cat "$TMP/code-$side")" = 0 ] || fail "advance $side expected 0: $(cat "$TMP/err-$side")"
  done
  [ "$(sed -n '1p;2p' "$log" | cut -d' ' -f1 | tr '\n' ' ')" = "start start " ] \
    || fail "the two merges did not overlap; their checks ran in turn: $(cat "$log")"
  git -C "$TMP/origin.git" show main:ticket-61.txt >/dev/null || fail "main did not get #61"
  git -C "$TMP/origin.git" show feature:ticket-62.txt >/dev/null || fail "feature did not get #62"
  if git -C "$TMP/origin.git" show main:ticket-62.txt >/dev/null 2>&1; then fail "main got feature's #62"; fi
  if git -C "$TMP/origin.git" show feature:ticket-61.txt >/dev/null 2>&1; then fail "feature got main's #61"; fi
  [ -d "$TMP/repo/.worktrees/merge-main" ] && [ -d "$TMP/repo/.worktrees/merge-feature" ] \
    || fail "each base branch should have its own merge worktree: $(ls "$TMP/repo/.worktrees")"
  MMW_FAKE_PASEO_STATE="$TMP/state-76" posted_events 61 into | grep -qx "ticket.landed into=main" \
    || fail "#61 was not recorded landed into main: $(MMW_FAKE_PASEO_STATE="$TMP/state-76" posted_events 61 into)"
  MMW_FAKE_PASEO_STATE="$TMP/state-77" posted_events 62 into | grep -qx "ticket.landed into=feature" \
    || fail "#62 was not recorded landed into feature: $(MMW_FAKE_PASEO_STATE="$TMP/state-77" posted_events 62 into)"
}

scenario_advancealreadyin() {
  rm -f "$TMP/check-ran"
  setup_checked_ticket "printf 'ran\\n' > '$TMP/check-ran'; exit 1"
  local passed before code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" push -q origin "$passed:main"
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "an already-present commit should be recorded: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] || fail "a new merge was made"
  grep -q 'already in 1' "$TMP/err" || fail "the tally did not count already in"
  [ ! -e "$TMP/check-ran" ] || fail "checks ran after the passed commit was already in origin/main"
  [ -z "$(posted_events 61 reason | grep '^ticket.bounced')" ] \
    || fail "an already-present ticket was bounced"
  posted_events 61 commit merge base | grep -qx \
    "ticket.landed commit=$passed merge=None base=None" \
    || fail "the fast-forward landing invented a merge: $(posted_events 61 commit merge base)"
  assert_no_wt 61
}

landed_first_line() {
  posted_events "$1" line | sed -n 's/^ticket\.landed line=//p' | tail -1
}

scenario_landedlinks() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed base merge code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  base="$(git -C "$TMP/origin.git" rev-parse main)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          FAKE_GH_URL=https://github.example/o/r bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "landing with links failed: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse main)"
  landed_first_line 61 | grep -qF "https://github.example/o/r/compare/$base...$merge" \
    || fail "the compare link is wrong: $(landed_first_line 61)"
  landed_first_line 61 | grep -qF "https://github.example/o/r/commit/$merge" \
    || fail "the merge commit link is wrong: $(landed_first_line 61)"
  posted_events 61 base merge | grep -qx "ticket.landed base=$base merge=$merge" \
    || fail "landing event omitted base or merge: $(posted_events 61 base merge)"
  [ "$(count_of 'gh :: repo :: view :: --json :: url')" = 1 ] \
    || fail "repository URL was not asked once"
}

scenario_landednourl() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed base merge code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  base="$(git -C "$TMP/origin.git" rev-parse main)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_URL_FAIL=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "URL lookup changed landing success: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse main)"
  ! landed_first_line 61 | grep -q "https://" \
    || fail "a failed URL lookup left a partial link: $(landed_first_line 61)"
  posted_events 61 base merge | grep -qx "ticket.landed base=$base merge=$merge" \
    || fail "URL failure omitted landing fields: $(posted_events 61 base merge)"
  [ -s "$TMP/err" ] || fail "URL lookup failure was silent"
}

scenario_alreadyinmerge() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed base sibling_merge merge tip code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  base="$(git -C "$TMP/repo" rev-parse main)"
  git -C "$TMP/repo" checkout -q -b issue-62 main
  git -C "$TMP/repo" merge -q --no-ff -m "Merge main into issue-62" issue-61
  sibling_merge="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" checkout -q main
  git -C "$TMP/repo" merge -q --no-ff -m "Merge branch 'issue-61'" issue-62
  merge="$(git -C "$TMP/repo" rev-parse HEAD)"
  commit_file "$TMP/repo" after.txt after after
  tip="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" push -q origin main
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "already-in merge failed: $(cat "$TMP/err")"
  posted_events 61 commit merge base | grep -qx \
    "ticket.landed commit=$passed merge=$merge base=$base" \
    || fail "the prior merge/base were not recovered: $(posted_events 61 commit merge base)"
  [ "$sibling_merge" != "$merge" ] && [ "$merge" != "$tip" ] \
    || fail "fixture did not distinguish sibling merge, landing merge and base tip"
}

scenario_alreadyinfastforward() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed other tip code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" push -q origin "$passed:main"
  other="$(other_clone)"
  commit_file "$other" after.txt after after
  git -C "$other" push -q origin main
  tip="$(git -C "$TMP/origin.git" rev-parse main)"
  [ "$tip" != "$passed" ] || fail "fixture left passed commit at the base tip"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "fast-forward already-in landing failed: $(cat "$TMP/err")"
  posted_events 61 commit merge base | grep -qx \
    "ticket.landed commit=$passed merge=None base=None" \
    || fail "fast-forward landing invented a merge: $(posted_events 61 commit merge base)"
  landed_first_line 61 | grep -qF "https://github.com/o/r/commit/$passed" \
    || fail "fast-forward landing should link the passed commit: $(landed_first_line 61)"
}

scenario_landeddeletesbranch() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  assert_remote_branch 61
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance landing failed: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_no_branch 61
}

scenario_landedkeepsunmergedlocalbranch() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed tip code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  git -C "$TMP/repo" checkout -q issue-61
  commit_file "$TMP/repo" local.txt unmerged local-only
  tip="$(git -C "$TMP/repo" rev-parse HEAD)"
  git -C "$TMP/repo" checkout -q main
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "local-only landing failed: $(cat "$TMP/err")"
  assert_kept_branch 61
  [ "$(git -C "$TMP/repo" rev-parse issue-61)" = "$tip" ] || fail "landing lost local-only commits"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main || fail "the passed commit did not land"
  ! git -C "$TMP/origin.git" cat-file -e main:local.txt 2>/dev/null || fail "unpassed local work landed"
  grep -qw 'issue-61' "$TMP/err" || fail "landing did not explain retained local-only work"
}

scenario_bouncedkeepsbranch() {
  setup_bounced_conflict
  git -C "$TMP/repo" push -q -u origin issue-61
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "bounced landing failed: $(cat "$TMP/err")"
  posted_events 61 reason | grep -q '^ticket\.bounced reason=' \
    || fail "the ticket was not recorded bounced: $(posted_events 61 reason)"
  assert_wt 61
  assert_branch 61
  assert_remote_branch 61
}

scenario_bouncestopssessions() {
  setup_bounced_conflict
  seed_agent 61 worker
  seed_agent 61 reviewer
  local code kind
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "bounced landing failed: $(cat "$TMP/err")"
  for kind in worker reviewer; do
    [ "$(count_of "paseo :: archive :: --force :: agt_61_$kind")" = 1 ] \
      || fail "$kind was not stopped exactly once: $(cat "$MMW_TEST_LOG")"
  done
  assert_wt 61
}

scenario_returnedstopssessions() {
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["needs-triage"], "assignees": [],
   "comments": [$(ev ticket.returned 61 "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1")]}
]
JSON
  seed_workspace 61
  seed_agent 61 worker
  seed_agent 61 reviewer
  post_ev 61 ticket.returned --ticket 61 --spec 76 \
    --line "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1"
  local code kind
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance of a returned ticket failed: $(cat "$TMP/err")"
  for kind in worker reviewer; do
    [ "$(count_of "paseo :: archive :: --force :: agt_61_$kind")" = 1 ] \
      || fail "$kind was not stopped exactly once: $(cat "$MMW_TEST_LOG")"
  done
  assert_wt 61

  post_ev 61 ticket.claimed --ticket 61 --spec 76 --line claimed --field login=mmw-bot
  seed_agent 61 worker
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance after a returned ticket was restarted failed: $(cat "$TMP/err")"
  hasnt "paseo :: archive :: --force :: agt_61_worker"
}

orphan_merge_fixture() {
  reset_log
  fresh_repo
  git -C "$TMP/repo" checkout -q -b gone main
  commit_file "$TMP/repo" gone.txt gone gone
  git -C "$TMP/repo" push -q -u origin gone
  git -C "$TMP/repo" checkout -q main
  mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q --detach "$TMP/repo/.worktrees/merge-gone" origin/gone
  mkdir -p "$STATE_DIR"
  : > "$STATE_DIR/merge-gone.lock"
  git -C "$TMP/repo" push -q origin --delete gone
  printf '%s\n' '[]' > "$TMP/tickets.json"
}

scenario_sweepsorphanmerge() {
  orphan_merge_fixture
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance failed: $(cat "$TMP/err")"
  [ ! -e "$TMP/repo/.worktrees/merge-gone" ] || fail "orphan merge worktree remains"
  [ ! -e "$STATE_DIR/merge-gone.lock" ] || fail "orphan merge lock remains"
}

scenario_sweepkeepslockedmerge() {
  orphan_merge_fixture
  local ready="$TMP/merge-lock-ready" holder code
  python3 - "$SKILL/scripts/statedir.py" "$STATE_DIR/merge-gone.lock" "$ready" <<'PY' &
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("statedir", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.locked(Path(sys.argv[2]), wait=0, purpose="test held merge lock"):
    Path(sys.argv[3]).touch()
    time.sleep(30)
PY
  holder=$!
  while [ ! -e "$ready" ]; do sleep 0.05; done
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  kill "$holder" 2>/dev/null || true
  wait "$holder" 2>/dev/null || true
  [ "$code" = 0 ] || fail "advance failed: $(cat "$TMP/err")"
  [ -d "$TMP/repo/.worktrees/merge-gone" ] || fail "locked merge worktree was removed"
}

# A released merge lock leaves its file behind; one whose branch is gone from origin is swept
# even when no merge worktree is left beside it.
stale_merge_lock_fixture() {
  reset_log
  fresh_repo
  git -C "$TMP/repo" push -q origin main:feat/live main:gone
  git -C "$TMP/repo" push -q origin --delete gone
  mkdir -p "$STATE_DIR"
  printf '%s\n' '{"pid": 999999, "identity": "Thu Jan  1 00:00:00 1970", "since": "2026-10-01T00:00:00Z", "purpose": "landing into origin/gone"}' \
    > "$STATE_DIR/merge-gone.lock"
  : > "$STATE_DIR/merge-main.lock"
  : > "$STATE_DIR/merge-feat-live.lock"
  printf '%s\n' '[]' > "$TMP/tickets.json"
}

scenario_sweepsstalemergelock() {
  stale_merge_lock_fixture
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance failed: $(cat "$TMP/err")"
  [ ! -e "$STATE_DIR/merge-gone.lock" ] || fail "the lock of a branch gone from origin remains"
  [ -e "$STATE_DIR/merge-main.lock" ] || fail "the lock of origin/main was swept"
  [ -e "$STATE_DIR/merge-feat-live.lock" ] || fail "the lock of origin/feat/live was swept"
}

scenario_sweepkeepsheldmergelock() {
  stale_merge_lock_fixture
  local ready="$TMP/merge-lock-ready" holder code
  rm -f "$ready"
  python3 - "$SKILL/scripts/statedir.py" "$STATE_DIR/merge-gone.lock" "$ready" <<'PY' &
import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location("statedir", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.locked(Path(sys.argv[2]), wait=0, purpose="test held merge lock"):
    Path(sys.argv[3]).touch()
    time.sleep(30)
PY
  holder=$!
  while [ ! -e "$ready" ]; do sleep 0.05; done
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  kill "$holder" 2>/dev/null || true
  wait "$holder" 2>/dev/null || true
  [ "$code" = 0 ] || fail "advance failed: $(cat "$TMP/err")"
  [ -e "$STATE_DIR/merge-gone.lock" ] || fail "a merge lock a live process holds was swept"
}

scenario_landedkeepsunmerged() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  local passed other later code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  other="$(other_clone)"
  git -C "$other" checkout -q -b issue-61 origin/issue-61
  commit_file "$other" later.txt later later
  later="$(git -C "$other" rev-parse HEAD)"
  git -C "$other" push -q origin issue-61
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "landing with later remote work failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$later" ] \
    || fail "remote work beyond ticket.passed was changed or deleted"
  grep -q 'merged 1' "$TMP/err" || fail "landing was not counted: $(cat "$TMP/err")"
}

setup_branch_race_check() {
  fresh_repo
  cat > "$TMP/repo/branch-race.sh" <<'SH'
#!/usr/bin/env bash
set -e
[ -e "$MMW_RACE_MARKER" ] && exit 0
if [ "$MMW_RACE_ACTION" = delete ]; then
  git -C "$MMW_RACE_CLONE" push -q origin --delete issue-61
else
  git -C "$MMW_RACE_CLONE" fetch -q origin issue-61
  git -C "$MMW_RACE_CLONE" checkout -q -B issue-61 origin/issue-61
  printf 'later\n' > "$MMW_RACE_CLONE/later.txt"
  git -C "$MMW_RACE_CLONE" add later.txt
  git -C "$MMW_RACE_CLONE" commit -q -m later
  git -C "$MMW_RACE_CLONE" rev-parse HEAD > "$MMW_RACE_TIP_FILE"
  git -C "$MMW_RACE_CLONE" push -q origin issue-61
fi
: > "$MMW_RACE_MARKER"
SH
  put_check "$TMP/repo" 'exec bash branch-race.sh'
  git -C "$TMP/repo" add branch-race.sh
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m checks
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  BRANCH_RACE_CLONE="$(other_clone)"
  local passed
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
}

scenario_landedbranchraced() {
  reset_log
  setup_branch_race_check
  rm -f "$TMP/branch-raced.once"
  local code later
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_RACE_CLONE="$BRANCH_RACE_CLONE" MMW_RACE_MARKER="$TMP/branch-raced.once" \
          MMW_RACE_TIP_FILE="$TMP/branch-raced.tip" MMW_RACE_ACTION=update \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "branch race changed landing success: $(cat "$TMP/err")"
  later="$(cat "$TMP/branch-raced.tip")"
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$later" ] \
    || fail "the lease erased work pushed after fetch"
  grep -q 'merged 1' "$TMP/err" || fail "landing was not counted: $(cat "$TMP/err")"
}

scenario_landedbranchgone() {
  reset_log
  setup_branch_race_check
  rm -f "$TMP/branch-gone.once"
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_RACE_CLONE="$BRANCH_RACE_CLONE" MMW_RACE_MARKER="$TMP/branch-gone.once" \
          MMW_RACE_TIP_FILE="$TMP/unused.tip" MMW_RACE_ACTION=delete \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "already-gone remote changed landing success: $(cat "$TMP/err")"
  assert_no_branch 61
}

setup_delete_refused() {
  fresh_repo
  cat > "$TMP/origin.git/hooks/update" <<'SH'
#!/usr/bin/env bash
case "$1 $3" in
  "refs/heads/issue-61 0000000000000000000000000000000000000000")
    echo "protected branch refuses deletion" >&2
    exit 1 ;;
esac
SH
  chmod +x "$TMP/origin.git/hooks/update"
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  local passed
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
}

scenario_landeddeleterefused() {
  reset_log
  setup_delete_refused
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "delete refusal changed landing success: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show main:ticket.txt >/dev/null \
    || fail "the ticket commit did not land on origin/main"
  posted_events 61 branch | grep -qx 'ticket.landed branch=issue-61' \
    || fail "ticket.landed was not recorded: $(posted_events 61 branch)"
  grep -q 'merged 1' "$TMP/err" || fail "landing was not counted: $(cat "$TMP/err")"
  assert_remote_branch 61
  grep -q "git push origin --delete issue-61" "$TMP/err" \
    || fail "the manual deletion command was omitted: $(cat "$TMP/err")"
}

scenario_archiveunlandedkeepsbranch() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" checkout -q main
  git -C "$TMP/repo" merge -q --no-ff -m "integrated without landing event" issue-61
  git -C "$TMP/repo" push -q origin main
  git -C "$TMP/repo" push -q -u origin issue-61
  seed_workspace 61
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
   "comments": [$(ev worker.started 61 "started" --field session=old --field runner=paseo \
                    $(start_facts "$(wt 61)" 61 worker)),
                $(ev ticket.returned 61 "HANDOFF REQUIRED" --field reason=stuck)]}
]
JSON
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "archive-only ticket failed: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_branch 61
  assert_remote_branch 61
}

scenario_regressedrestart() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  assert_remote_branch 61
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "initial landing failed: $(cat "$TMP/err")"
  assert_no_branch 61
  post_ev 61 ticket.regressed --ticket 61 --line "REGRESSED" \
    --field reason=checks --field "commit=$passed"
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
path = sys.argv[1]
rows = json.load(open(path))
rows[0]["state"] = "OPEN"
rows[0]["labels"] = ["ready-for-agent"]
rows[0]["assignees"] = []
json.dump(rows, open(path, "w"))
PY
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "regressed ticket did not restart: $(cat "$TMP/err")"
  assert_wt 61
  assert_branch 61
  [ "$(git -C "$TMP/origin.git" rev-parse issue-61)" = "$(git -C "$TMP/origin.git" rev-parse main)" ] \
    || fail "the restarted origin branch was not cut from origin/main"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" issue-61 \
    || fail "the restarted branch lost the original passed commit"
}

# The shape of agentflow #731: a ticket lands, the base branch moves on — a sibling
# ticket's merge and a commit the orchestrator made straight on it — `reverify` finds the
# ticket red and reopens it, and it is started again. Its first run's work is in the base
# branch now, so the new worker's base is where the new branch leaves origin/main, and the
# `Outside Owns:` its own run computes from that base names none of the commits other
# hands put on the base branch in between.
scenario_regressedrestartbase() {
  reset_log
  fresh_repo
  local first_base passed code tip base owns other
  first_base="$(git -C "$TMP/repo" rev-parse main)"
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [],
   "closedAt": "2026-09-11T01:00:00Z", "assignees": ["mmw-bot"],
   "comments": [$(ev worker.started 61 "worker started" --field session=agt_first --field runner=paseo \
     --field "machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
     --field host=codex --field model=gpt-5.6-sol --field effort=high --field grade=junior-worker \
     --field "worktree=$(wt 61)" --field branch=issue-61 --field "base=$first_base" --field into=main),
     $(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field "commit=$passed" --field into=main)]}
]
JSON
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "initial landing failed: $(cat "$TMP/err")"
  assert_no_branch 61

  merge_sibling_to_origin 62 sibling.txt sibling "sibling landed after #61"
  other="$(other_clone)"
  git -C "$other" pull -q --ff-only origin main
  commit_file "$other" hotfix.txt hotfix "orchestrator's fix straight on the base branch"
  git -C "$other" push -q origin main
  tip="$(git -C "$TMP/origin.git" rev-parse main)"

  post_ev 61 ticket.regressed --ticket 61 --line "REGRESSED" \
    --field "commit=$tip" --json-field 'failed=["AC2"]'
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
path = sys.argv[1]
rows = json.load(open(path))
row = next(r for r in rows if r["number"] == 61)
row["state"] = "OPEN"
row["labels"] = ["ready-for-agent"]
row["assignees"] = []
json.dump(rows, open(path, "w"))
PY
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "regressed ticket did not restart: $(cat "$TMP/err")"
  base="$(posted_events 61 base | grep '^worker.started ' | tail -n 1)"
  [ "$base" = "worker.started base=$tip" ] \
    || fail "the restarted worker should record origin/main's tip $tip as its base, not the first run's $first_base: $base"
  base="${base#worker.started base=}"
  owns="$(MMW_VT="$(dirname "$SKILL")/verify-ticket/scripts/verify-ticket.py" \
          python3 - "$(wt 61)" "$base" <<'PY'
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("verify_ticket", os.environ["MMW_VT"])
vt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vt)
print(",".join(vt.outside_owns(["ticket.txt"], Path(sys.argv[1]), sys.argv[2])) or "None")
PY
)"
  [ "$owns" = None ] \
    || fail "the restarted worker's Outside Owns names files other hands put on the base branch: $owns"
}

scenario_advancesummaryline() {
  reset_log
  fresh_repo
  commit_file "$TMP/repo" shared.txt base shared-base
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 shared.txt first
  make_branch issue-62 shared.txt second
  local first second code
  first="$(git -C "$TMP/repo" rev-parse issue-61)"
  second="$(git -C "$TMP/repo" rev-parse issue-62)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field "commit=$first" --field into=main)]},
  {"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T02:00:00Z",
   "comments": [$(ev ticket.passed 62 "ALL MET" --field branch=issue-62 --field "commit=$second" --field into=main)]},
  {"number": 63, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"],
   "blockedBy": [{"number": 99, "state": "OPEN"}],
   "comments": [$(ev ticket.claimed 63 "claimed" --field login=mmw-bot),
                $(ev worker.started 63 "started" --field session=agt_63 --field runner=paseo \
                  $(start_facts "$(wt 63)" 63 worker)),
                $(ev worker.retracted 63 "retracted" --field session=agt_63 --field runner=paseo)]}
]
JSON
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance expected 0: $(cat "$TMP/err")"
  grep -q 'advance #76: merged 1, already in 0, bounced 1, released 1, started 0, refused 0' "$TMP/err" \
    || fail "the summary counts are wrong: $(cat "$TMP/err")"
}

scenario_bouncednotretried() {
  setup_bounced_conflict
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "first advance expected 0: $(cat "$TMP/err")"
  python3 - "$TMP/tickets.json" <<'PY'
import json, sys
from pathlib import Path

path = Path(sys.argv[1])
rows = json.loads(path.read_text())
rows[0]["state"] = "OPEN"
rows[0]["labels"] = ["needs-triage"]
rows[0]["assignees"] = []
path.write_text(json.dumps(rows))
PY
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "second advance expected 0: $(cat "$TMP/err")"
  grep -q 'merged 0, already in 0, bounced 0' "$TMP/err" \
    || fail "the bounced ticket was tried again: $(cat "$TMP/err")"
  grep -q 'started 0' "$TMP/err" || fail "the bounced ticket was dispatched again: $(cat "$TMP/err")"
  never_ran
  [ "$(posted_events 61 reason | grep -c ticket.bounced | tr -d ' ')" = 1 ] \
    || fail "a second ticket.bounced was written"
}

scenario_landviaorigin() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed caller_head code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  git -C "$TMP/repo" checkout -q -b caller main
  caller_head="$(git -C "$TMP/repo" rev-parse HEAD)"
  no_relay
  fake_relay '{"tickets":[61]}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "land from a non-base checkout expected 0: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" rev-parse HEAD)" = "$caller_head" ] || fail "caller moved"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "land did not update origin/main"

  setup_bounced_conflict
  no_relay
  fake_relay '{"tickets":[61]}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "a conflict should bounce, not fail land: $(cat "$TMP/err")"
  posted_events 61 reason | grep -qx 'ticket.bounced reason=conflict' \
    || fail "land did not write ticket.bounced"
  assert_wt 61
}

scenario_reverifyorigin() {
  local copy other remote_head passed code
  copy="$(skill_copy_for reverifyorigin)"
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
number = sys.argv[1]
head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
body = subprocess.check_output([
    sys.executable, os.environ["MMW_EVENTS_PY_FOR_TESTS"], "emit", "ticket.checked",
    "--ticket", number, "--line", "Reverify", "--actor", "main", "--stage", "regress",
    "--field", "run=reverify", "--field", "commit=" + head, "--field", "result=met"
], text=True)
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
rows = json.loads(store.read_text()) if store.is_file() else {}
rows.setdefault(number, []).append(body)
store.write_text(json.dumps(rows))
print("ALL MET (1 met)")
PY
  chmod +x "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  fresh_repo
  passed="$(git -C "$TMP/repo" rev-parse HEAD)"
  other="$(other_clone)"
  commit_file "$other" remote.txt remote remote
  git -C "$other" push -q origin main
  remote_head="$(git -C "$TMP/origin.git" rev-parse main)"
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "CLOSED", "labels": [], "closedAt": "2026-09-11T01:00:00Z",
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field "commit=$passed" --field into=main),
                $(ev ticket.landed 61 "landed" --field branch=issue-61 --field "commit=$passed" --field into=main --field "merge=$passed")]}
]
JSON
  reset_log
  open_night
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "reverify expected 0: $(cat "$TMP/err")"
  posted_events 61 run commit | grep -qx "ticket.checked run=reverify commit=$remote_head" \
    || fail "reverify did not run on origin/main: $(posted_events 61 run commit)"
}

scenario_summarybounced() {
  reset_log
  fresh_repo
  summary_ready_fixture
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["needs-triage"],
   "comments": [$(ev ticket.bounced 61 "bounced" --field reason=conflict \
     --field commit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa --field into=main --json-field 'files=["shared.txt"]')]}
]
JSON
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary expected 0: $(cat "$TMP/err")"
  grep -q '^Bounced: #61 (conflict)$' "$MMW_GH_LAST_BODY" \
    || fail "NIGHT SUMMARY omits the bounced ticket: $(cat "$MMW_GH_LAST_BODY")"
  grep -q '^Handed back to needs-triage: None$' "$MMW_GH_LAST_BODY" \
    || fail "the bounced ticket was counted again as handed back: $(cat "$MMW_GH_LAST_BODY")"
}

scenario_boardregisters() {
  local code port listening registered expected repository candidates
  echo "--- board skips a listening port and a registered port, then starts on the first free one"
  fresh_board_registry
  candidates="$(python3 - <<'PY'
import socket
found = []
for port in range(47100, 65536):
    sock = socket.socket()
    try:
        sock.bind(("0.0.0.0", port))
    except OSError:
        sock.close()
        continue
    sock.close()
    found.append(port)
    if len(found) == 3:
        break
print(*found)
PY
)"
  set -- $candidates
  listening="$1"; registered="$2"; expected="$3"
  start_test_listener "$listening" || fail "could not start the all-address listener"
  python3 - "$MMW_HOME/boards.json" "$registered" <<'PY'
import json, sys
with open(sys.argv[1], "w") as fh:
    json.dump({"/already/registered": int(sys.argv[2])}, fh)
PY
  MMW_PORT="$listening" python3 - <<'PY' || fail "the occupied candidate does not answer"
import os, socket
with socket.create_connection(("127.0.0.1", int(os.environ["MMW_PORT"])), timeout=1):
    pass
PY
  code="$(run_dispatch env MMW_RUNNER=paseo bash "$DISPATCH" board)"
  [ "$code" = 0 ] || fail "board expected 0: $(cat "$TMP/err")"
  repository="$(cd "$TMP/repo" && pwd -P)"
  port="$(MMW_REPOSITORY="$repository" python3 - "$MMW_HOME/boards.json" <<'PY'
import json, os, sys
print(json.load(open(sys.argv[1]))[os.environ["MMW_REPOSITORY"]])
PY
)"
  BOARD_TEST_PORTS="$port"
  MMW_REPOSITORY="$repository" MMW_PORT="$port" MMW_EXPECTED="$expected" \
    python3 - "$MMW_HOME/boards.json" <<'PY' || fail "boards.json has the wrong registration"
import json, os, sys
data = json.load(open(sys.argv[1]))
assert data[os.environ["MMW_REPOSITORY"]] == int(os.environ["MMW_PORT"]), data
assert len(data) == 2, data
assert int(os.environ["MMW_PORT"]) == int(os.environ["MMW_EXPECTED"]), data
PY
  [ "$(cat "$TMP/out")" = "http://127.0.0.1:$port" ] \
    || fail "unsupported runner should print the URL: $(cat "$TMP/out")"
  MMW_PORT="$port" python3 - <<'PY' || fail "the registered board does not answer"
import os, socket
with socket.create_connection(("127.0.0.1", int(os.environ["MMW_PORT"])), timeout=1):
    pass
PY
}

scenario_boardsameport() {
  local code port second repository
  echo "--- board reuses one main-checkout registration from another worktree"
  fresh_board_registry
  code="$(run_dispatch env MMW_RUNNER=paseo bash "$DISPATCH" board)"
  [ "$code" = 0 ] || fail "first board expected 0: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  git -C "$TMP/repo" worktree add -q -b board-other "$TMP/board-other"
  (cd "$TMP/board-other" && env MMW_RUNNER=paseo bash "$DISPATCH" board) \
    > "$TMP/out" 2> "$TMP/err"
  code=$?
  [ "$code" = 0 ] || fail "board from worktree expected 0: $(cat "$TMP/err")"
  second="$(board_registry_port)"
  [ "$second" = "$port" ] || fail "worktree got port $second instead of $port"
  repository="$(cd "$TMP/repo" && pwd -P)"
  MMW_REPOSITORY="$repository" python3 - "$MMW_HOME/boards.json" <<'PY' \
    || fail "worktree created a second registry key"
import json, os, sys
data = json.load(open(sys.argv[1]))
assert list(data) == [os.environ["MMW_REPOSITORY"]], data
PY
}

scenario_boardopenstab() {
  local code port workspace calls
  echo "--- board asks the Orca adapter for a tab tied to the current worktree"
  fresh_board_registry
  git -C "$TMP/repo" worktree add -q -b board-open "$TMP/board-open"
  (cd "$TMP/board-open" && env MMW_RUNNER=orca bash "$DISPATCH" board) \
    > "$TMP/out" 2> "$TMP/err"
  code=$?
  [ "$code" = 0 ] || fail "Orca board expected 0: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  workspace="$(cd "$TMP/board-open" && pwd -P)"
  calls="$(count_of 'orca :: tab :: create')"
  [ "$calls" = 1 ] || fail "expected one tab create, got $calls"
  has "orca :: tab :: create :: --url :: http://127.0.0.1:$port :: --worktree :: path:$workspace :: --json"
  [ ! -s "$TMP/out" ] || fail "successful tab creation should print nothing: $(cat "$TMP/out")"
  bash "$SKILL/scripts/runners/orca.sh" open-url --cwd "$TMP/no-such-workspace" \
    --url "http://127.0.0.1:$port" > "$TMP/out" 2> "$TMP/err"
  code=$?
  [ "$code" = 1 ] || fail "a bad Orca workspace must fail, got $code"
}

scenario_boardprintsurl() {
  local code port
  echo "--- board prints its URL when the selected adapter has no open-url action"
  fresh_board_registry
  code="$(run_dispatch env MMW_RUNNER=paseo bash "$DISPATCH" board)"
  [ "$code" = 0 ] || fail "Paseo board expected 0: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  [ "$(cat "$TMP/out")" = "http://127.0.0.1:$port" ] \
    || fail "stdout is not the exact board URL: $(cat "$TMP/out")"
  hasnt "paseo :: tab :: create"
  hasnt "orca :: tab :: create"
}

scenario_openstartsboard() {
  local code port copy
  echo "--- open registers this repository's board, starts it, and names its URL on the line that opens the night"
  fresh_board_registry
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  [ "$(cat "$TMP/out")" = "opened #76: wake-ups go to paseo session agt_main; task board http://127.0.0.1:$port" ] \
    || fail "open should name the board it started: $(cat "$TMP/out")"
  MMW_PORT="$port" python3 - <<'PY' || fail "the board open started does not answer"
import os, socket
socket.create_connection(("127.0.0.1", int(os.environ["MMW_PORT"])), timeout=2).close()
PY
  python3 - "$MMW_HOME/boards.json" "$(cd "$TMP/repo" && pwd -P)" <<'PY' \
    || fail "open should register the main worktree: $(cat "$MMW_HOME/boards.json")"
import json, sys
registry = json.load(open(sys.argv[1]))
assert list(registry) == [sys.argv[2]], registry
PY

  echo "--- a board that cannot be started is said so and does not stop the night"
  no_relay
  copy="$(skill_copy_for open-no-board)"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "a board that will not start must not fail the night, got $code: $(cat "$TMP/err")"
  grep -qx "opened #76: wake-ups go to paseo session agt_main" "$TMP/out" \
    || fail "the night still opens, without a board URL: $(cat "$TMP/out")"
  grep -q "no task board supervisor at" "$TMP/err" || fail "the reason should be named: $(cat "$TMP/err")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] \
    || fail "the watch should be open all the same: $(cat "$STATE_DIR/watches.json" 2>&1)"
  no_relay
}

scenario_openticketstartsboard() {
  local code port copy
  echo "--- open-ticket registers this repository's board, starts it, and names its URL on the line that opens the watch"
  fresh_board_registry
  no_relay
  seed_main_agent agt_main
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 90, "state": "OPEN", "labels": ["ready-for-agent"], "parent": null}]
JSON
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 90)"
  [ "$code" = 0 ] || fail "open-ticket expected 0, got $code: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  [ "$(cat "$TMP/out")" = "opened #90: wake-ups go to paseo session agt_main; task board http://127.0.0.1:$port" ] \
    || fail "open-ticket should name the board it started: $(cat "$TMP/out")"
  MMW_PORT="$port" python3 - <<'PY' || fail "the board open-ticket started does not answer"
import os, socket
socket.create_connection(("127.0.0.1", int(os.environ["MMW_PORT"])), timeout=2).close()
PY
  python3 - "$MMW_HOME/boards.json" "$(cd "$TMP/repo" && pwd -P)" <<'PY' \
    || fail "open-ticket should register the main worktree: $(cat "$MMW_HOME/boards.json")"
import json, sys
registry = json.load(open(sys.argv[1]))
assert list(registry) == [sys.argv[2]], registry
PY

  echo "--- a board that cannot be started is said so and the watch is open all the same"
  no_relay
  copy="$(skill_copy_for open-ticket-no-board)"
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" open-ticket 90)"
  [ "$code" = 0 ] || fail "a board that will not start must not fail open-ticket, got $code: $(cat "$TMP/err")"
  grep -qx "opened #90: wake-ups go to paseo session agt_main" "$TMP/out" \
    || fail "the watch still opens, without a board URL: $(cat "$TMP/out")"
  grep -q "no task board supervisor at" "$TMP/err" || fail "the reason should be named: $(cat "$TMP/err")"
  grep -q "the watch on #90 is open and its task board is not" "$TMP/err" \
    || fail "stderr should say the ticket has no board: $(cat "$TMP/err")"
  [ "$(watch_main tickets:90)" = "paseo agt_main" ] \
    || fail "the watch should be open all the same: $(cat "$STATE_DIR/watches.json" 2>&1)"
  no_relay
}

scenario_prgreen() {
  local code
  rm -rf "$TMP/repo/.github/workflows"
  mkdir -p "$TMP/repo/.github/workflows"
  printf 'on: pull_request\n' > "$TMP/repo/.github/workflows/ci.yml"
  printf 'PR body\n' > "$TMP/body.md"
  reset_log
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
    --base main --head night --title 'Night changes' --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "pr expected 0, got $code: $(cat "$TMP/err")"
  grep -qx 'https://github.com/o/r/pull/7' "$TMP/out" || fail 'PR link was not printed'
  grep -qx 'checks: green' "$TMP/out" || fail "missing green summary: $(cat "$TMP/out")"
  has "gh :: pr :: create :: --base :: main :: --head :: night :: --title :: Night changes :: --body-file :: $TMP/body.md"
  hasnt ' :: --draft'
  has 'gh :: pr :: checks :: 7 :: --watch'
  ! grep -q '^NOTE:' "$TMP/out" || fail 'CI runs for main, so no NOTE is expected'
}

scenario_prnotewhennoci() {
  local code workflow base pattern ci
  rm -rf "$TMP/repo/.github/workflows"
  mkdir -p "$TMP/repo/.github/workflows"
  printf 'PR body\n' > "$TMP/body.md"
  for workflow in \
    'on: {pull_request: {branches: [main]}}' \
    $'on:\n  pull_request:\n    branches:\n      - main' \
    $'on:\n  pull_request:\n    branches-ignore: [night]' ; do
    printf '%s\n' "$workflow" > "$TMP/repo/.github/workflows/pull-request.yaml"
    for base in night main; do
      code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
        --base "$base" --head feature --title Changes --body-file "$TMP/body.md")"
      [ "$code" = 0 ] || fail "expected 0, got $code: $(cat "$TMP/err")"
      if [ "$base" = night ]; then
        grep -qx 'NOTE: GitHub CI does not run for pull requests into night' "$TMP/out" \
          || fail "missing NOTE for $workflow"
      else
        ! grep -q '^NOTE:' "$TMP/out" || fail "unexpected NOTE for main with $workflow"
      fi
    done
  done
  for workflow in 'on: pull_request' 'on: pull_request # runs on every base' 'on: [push, pull_request]' \
    $'on:\n  - push\n  - pull_request' '"on": {pull_request: {}}' \
    $'on:\n  pull_request:\n    branches: []' $'on:\n  pull_request:\n    branches:' ; do
    printf '%s\n' "$workflow" > "$TMP/repo/.github/workflows/pull-request.yaml"
    code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
      --base night --head feature --title Changes --body-file "$TMP/body.md")"
    [ "$code" = 0 ] || fail "expected 0: $(cat "$TMP/err")"
    ! grep -q '^NOTE:' "$TMP/out" || fail "unexpected NOTE for unrestricted $workflow"
  done
  while IFS='|' read -r pattern base ci; do
    printf 'on: {pull_request: {branches: [%s]}}\n' "$pattern" > "$TMP/repo/.github/workflows/pull-request.yaml"
    code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
      --base "$base" --head feature --title Changes --body-file "$TMP/body.md")"
    [ "$code" = 0 ] || fail "branch filter expected 0: $(cat "$TMP/err")"
    if [ "$ci" = yes ]; then
      ! grep -q '^NOTE:' "$TMP/out" || fail "$pattern must cover $base"
    else
      grep -qx "NOTE: GitHub CI does not run for pull requests into $base" "$TMP/out" \
        || fail "$pattern must not cover $base"
    fi
  done <<'CASES'
'*'|fix/1|no
'*'|main|yes
'**'|fix/1|yes
'fix/*'|fix/1/extra|no
'fix/**'|fix/1/extra|yes
'v[12].[0-9]+.[0-9]+'|v1.10.1|yes
'v[12].[0-9]+.[0-9]+'|v3.10.1|no
'releases/**', '!releases/**-alpha'|releases/v1-alpha|no
CASES
  printf 'on: *unreadable\n' > "$TMP/repo/.github/workflows/pull-request.yaml"
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
    --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "unknown workflow should assume CI: $(cat "$TMP/err")"
  ! grep -q '^NOTE:' "$TMP/out" || fail 'unknown workflow must not assert no CI'
  grep -q 'pull-request.yaml.*could not read' "$TMP/out" || fail 'unknown workflow must name its file'
}

scenario_prdispatchesworkflow() {
  local code
  rm -rf "$TMP/repo/.github/workflows"
  mkdir -p "$TMP/repo/.github/workflows"
  printf 'PR body\n' > "$TMP/body.md"
  cat > "$TMP/repo/.github/workflows/ci.yml" <<'YAML'
on:
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      optional:
        required: false
YAML
  printf 'on: workflow_dispatch\n' > "$TMP/repo/.github/workflows/deploy.yaml"
  cat > "$TMP/repo/.github/workflows/required.yml" <<'YAML'
on:
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      target:
        required: true
YAML
  reset_log
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
    --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "expected 0, got $code: $(cat "$TMP/err")"
  grep -qx 'dispatched ci.yml: success' "$TMP/out" || fail "missing workflow result: $(cat "$TMP/out")"
  grep -q '^skipped deploy.yaml: .*pull_request' "$TMP/out" || fail 'deploy-only workflow must explain skip'
  grep -q '^skipped required.yml: .*required' "$TMP/out" || fail 'required input must explain skip'
  has 'gh :: workflow :: run :: ci.yml :: --ref :: feature'
  has 'gh :: run :: watch :: 81 :: --exit-status'
  hasnt 'gh :: workflow :: run :: deploy.yaml'
  hasnt 'gh :: workflow :: run :: required.yml'
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' FAKE_GH_RUN_CONCLUSION=failure \
    bash "$DISPATCH" pr --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 1 ] || fail "failed fallback run expected 1, got $code"
  grep -qx 'dispatched ci.yml: failure' "$TMP/out" || fail 'failed fallback must print its conclusion'
  grep -qx 'https://github.com/o/r/pull/7' "$TMP/out" || fail 'fallback failure must still open the PR'
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' FAKE_GH_RUN_WATCH_FAIL=1 \
    bash "$DISPATCH" pr --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 1 ] || fail 'a fallback watch failure must exit 1'
  grep -qx 'dispatched ci.yml: success' "$TMP/out" || fail 'the actual run conclusion must remain visible'
  grep -q 'watch connection lost' "$TMP/err" || fail 'a failed watch must retain its error'
  rm "$MMW_FAKE_PASEO_STATE/dispatched-run"
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' FAKE_GH_RUN_NO_URL=1 \
    MMW_PR_CHECKS_GRACE_SECONDS=0 bash "$DISPATCH" pr \
    --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "a dispatch without a run URL must find the new run: $(cat "$TMP/err")"
  grep -qx 'dispatched ci.yml: success' "$TMP/out" || fail 'new workflow run must be watched'
  hasnt 'gh :: run :: watch :: 80'
  reset_log
  code="$(run_dispatch env FAKE_GH_PERSIST_PR=1 FAKE_GH_PR_CHECKS_FAIL=1 \
    bash "$DISPATCH" pr --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 2 ] || fail 'a watch failure after opening the PR must exit 2'
  [ "$(count_of 'gh :: workflow :: run :: ci.yml')" = 1 ] || fail 'the first attempt must dispatch once'
  code="$(run_dispatch env FAKE_GH_PERSIST_PR=1 FAKE_GH_PR_CHECKS='build pass' \
    bash "$DISPATCH" pr --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 2 ] || fail 'an existing PR must be reported before opening another'
  [ "$(count_of 'gh :: workflow :: run :: ci.yml')" = 1 ] || fail 'retry must not dispatch the workflow twice'
  grep -q 'https://github.com/o/r/pull/7' "$TMP/err" || fail 'the refusal must identify the existing PR'
  reset_log
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "normal PR CI expected green: $(cat "$TMP/err")"
  hasnt 'gh :: workflow :: run'
}

scenario_prredandnone() {
  local code
  rm -rf "$TMP/repo/.github/workflows"
  mkdir -p "$TMP/repo/.github/workflows"
  printf 'PR body\n' > "$TMP/body.md"
  printf 'on: pull_request\n' > "$TMP/repo/.github/workflows/ci.yml"
  code="$(run_dispatch env FAKE_GH_PR_CHECKS=$'build fail\nunit tests cancel' bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 1 ] || fail "red checks expected 1, got $code"
  grep -qx 'checks: red build, unit tests' "$TMP/out" || fail "missing red names: $(cat "$TMP/out")"
  code="$(run_dispatch env MMW_PR_CHECKS_GRACE_SECONDS=0 FAKE_GH_PR_CHECKS='' bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 1 ] || fail "no checks with expected CI must exit 1, got $code"
  grep -qx 'checks: none' "$TMP/out" || fail "missing none with expected CI: $(cat "$TMP/out")"
  reset_log
  code="$(run_dispatch env MMW_PR_CHECKS_GRACE_SECONDS=3 FAKE_GH_PR_CHECKS_DELAY=2 \
    FAKE_GH_PR_CHECKS='build pass' bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "delayed checks expected green, got $code: $(cat "$TMP/err")"
  grep -qx 'checks: green' "$TMP/out" || fail 'checks that appear during grace must be read'
  [ "$(count_of 'gh :: pr :: checks :: 7 :: --watch')" -ge 2 ] || fail 'no checks must be retried'
  rm "$TMP/repo/.github/workflows/ci.yml"
  code="$(run_dispatch env FAKE_GH_PR_CHECKS='' bash "$DISPATCH" pr \
    --base night --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 0 ] || fail "no CI and no checks expected 0, got $code"
  grep -qx 'checks: none' "$TMP/out" || fail "missing none without CI: $(cat "$TMP/out")"
  code="$(run_dispatch bash "$DISPATCH" pr --base main)"
  [ "$code" = 2 ] || fail 'missing arguments must exit 2'
  code="$(run_dispatch env FAKE_GH_PR_CREATE_FAIL=1 bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 2 ] || fail 'failed PR creation must exit 2'
  grep -q 'opening pull request failed' "$TMP/err" || fail 'failed PR must explain why'
  code="$(run_dispatch env FAKE_GH_PR_CHECKS_FAIL=1 bash "$DISPATCH" pr \
    --base main --head feature --title Changes --body-file "$TMP/body.md")"
  [ "$code" = 2 ] || fail 'a GitHub failure must not be reported as no checks'
  grep -q 'HTTP 502' "$TMP/err" || fail 'a check read failure must explain why'
}


needs_exclusive_ports() {
  case "$1" in board*) return 0 ;; *) return 1 ;; esac
}

source "$HERE/parallel.sh"
run_scenarios "$0" "$@"
