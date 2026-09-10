#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/tests/dispatch/test_dispatch.sh check|advance|advanceconflict|advancedirty
#   bash mmw-v2/tests/dispatch/test_dispatch.sh start-worker|start-reviewer|start-verifier|retract
#   bash mmw-v2/tests/dispatch/test_dispatch.sh resume|wait|reverify|summary
#   bash mmw-v2/tests/dispatch/test_dispatch.sh release|releaseother|releaselive|releasestanding|frontierwhy
#   bash mmw-v2/tests/dispatch/test_dispatch.sh instancegate|countfail|stopproduct|suspend|suspendbusy|status
#   bash mmw-v2/tests/dispatch/test_dispatch.sh runnerstart|runnersend|runnerliveness
#   bash mmw-v2/tests/dispatch/test_dispatch.sh runnerparity|herdrworkingsend|herdrliveness
#   bash mmw-v2/tests/dispatch/test_dispatch.sh orcasend|orcaclosed
#   bash mmw-v2/tests/dispatch/test_dispatch.sh worktreegit|worktreegoverned|worktreeremove|installorca
#   bash mmw-v2/tests/dispatch/test_dispatch.sh usesagree|usesmismatch|usesunreadable
#   bash mmw-v2/tests/dispatch/test_dispatch.sh paseostartdir|landarchivesagents
#   bash mmw-v2/tests/dispatch/test_dispatch.sh orcadoubledispatch|unreadableevents|startunrecorded
#   bash mmw-v2/tests/dispatch/test_dispatch.sh mergewithoutbranch|retractunreadable
#   bash mmw-v2/tests/dispatch/test_dispatch.sh open|openrefused|openticket|ack|unopened|runnerself|orcaunobserved
#   bash mmw-v2/tests/dispatch/test_dispatch.sh all
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
unset MMW_SPEC

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL="$(dirname "$(dirname "$HERE")")/skills/dispatch"
DISPATCH="$SKILL/scripts/dispatch.sh"

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
# A relay left running would go on polling a board that is gone, through whatever `gh`
# is next on PATH.
trap 'no_relay; rm -rf "$TMP"' EXIT
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
uses = os.environ.get("MMW_FAKE_USES", "agree")

PASEO_HELP_TOP = """Usage: paseo [options] [command]

Paseo CLI - control your AI coding agents from the command line

Options:
  --json                        output in JSON format
  -h, --help                    display help for command
"""

PASEO_HELP = {
    ("run",): """Usage: paseo run [options] <prompt>

Create and start an agent with a task

Options:
  -d, --background                  Run in background
  --title <title>                   Assign a title to the agent
  --provider <provider>             Agent provider, or provider/model
  --mode <mode>                     Provider-specific mode
  --thinking <id>                   Thinking option ID to use for this run
  --cwd <path>                      Working directory (default: current)
  --label <key=value>               Add label(s) to the agent (default: [])
  --json                            Output in JSON format
  -h, --help                        display help for command
""",
    ("archive",): """Usage: paseo archive [options] <id>

Archive an agent (soft-delete)

Options:
  --force               Interrupt the agent if it is running, then archive
  -h, --help            display help for command
""",
    ("send",): """Usage: paseo send [options] <id> [prompt]

Send a message/task to an existing agent

Options:
  --no-wait             Return immediately without waiting for completion
  --json                Output in JSON format
  -h, --help            display help for command
""",
    ("ls",): """Usage: paseo ls [options]

List agents. By default excludes archived agents.

Options:
  -g, --global         List agents across all directories
  --json               Output in JSON format
  -h, --help            display help for command
""",
}


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


if "-h" in args or "--help" in args:
    cmd = tuple(a for a in args if a not in ("-h", "--help"))
    if not cmd:
        print(PASEO_HELP_TOP)
        sys.exit(0)
    page = PASEO_HELP.get(cmd)
    if page is None:
        print(PASEO_HELP_TOP)
        sys.exit(0)
    print(page)
    sys.exit(0)

if args[:2] == ["provider", "ls"]:
    grok = "unavailable" if scenario == "provider-down" else "available"
    print(json.dumps([
        {"provider": "grok", "status": grok, "label": "Grok"},
        {"provider": "claude", "status": "available", "label": "Claude"},
        {"provider": "codex", "status": "available", "label": "Codex"},
        {"provider": "cursor", "status": "available", "label": "Cursor"},
    ]))
    sys.exit(0)

if args[:2] == ["provider", "models"]:
    print(json.dumps([{"id": "grok-4.6", "thinkingOptionIds": ["high", "xhigh"]}]))
    sys.exit(0)

# The real call refreshes the daemon's snapshot for one host and answers with a text
# blob; `check` reads it only to print under a refusal, so one line of it is enough.
if args[:2] == ["provider", "diagnostic"]:
    host = args[2] if len(args) > 2 else ""
    down = scenario == "provider-down" and host == "grok"
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
    if scenario == "run-fail":
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
    }
    with open(state / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(request) + "\n")
    rows.append({"id": ident, "name": request["title"] or ident, "status": "running",
                 "cwd": request["cwd"], "labels": labels})
    save("agents.json", rows)
    print(json.dumps({"agentId": ident, "status": "running", "cwd": request["cwd"]}))
    sys.exit(0)

if args[:1] == ["wait"]:
    ident = args[1] if len(args) > 1 else ""
    if scenario == "wait-timeout":
        sys.exit(1)
    ticket = ""
    rows = load("agents.json")
    for row in rows:
        if row.get("id") == ident:
            row["status"] = os.environ.get("MMW_FAKE_WAIT_STATUS", "idle")
            ticket = str((row.get("labels") or {}).get("mmw.ticket") or "")
    save("agents.json", rows)
    comment = os.environ.get("MMW_FAKE_WAIT_COMMENT", "")
    tickets_path = os.environ.get("FAKE_GH_TICKETS_FILE", "")
    if comment and tickets_path and Path(tickets_path).is_file() and ticket:
        tickets = json.loads(Path(tickets_path).read_text(encoding="utf-8"))
        for t in tickets:
            if str(t.get("number")) == ticket:
                t.setdefault("comments", []).append(comment)
                break
        Path(tickets_path).write_text(json.dumps(tickets), encoding="utf-8")
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
uses = os.environ.get("MMW_FAKE_USES", "agree")

HERDR_HELP_TOP = """herdr — terminal workspace manager for AI coding agents

Usage: herdr [options]
       herdr --session <name> [options]
       herdr agent start
       herdr tab create

Options:
  -h, --help
      --timeout <MS>
      --kind <KIND>
      --pane <ID>
      --wait
      --until <STATUS>
      --cwd <PATH>
"""

HERDR_HELP = {
    ("pane", "close"): """Close a pane

Usage: herdr pane close <pane_id>
""",
    ("tab", "create"): """Create a tab

Usage: herdr tab create [OPTIONS]

Options:
      --cwd <PATH>
      --no-focus
""",
    ("agent", "start"): """Start a supported interactive agent in an existing pane

Usage: herdr agent start <NAME> --kind <KIND> --pane <ID> [OPTIONS]

Options:
      --kind <KIND>
      --pane <ID>
      --timeout <MS>
""",
    ("agent", "prompt"): """Submit a prompt to an agent

Usage: herdr agent prompt <TARGET> <TEXT> [OPTIONS]

Options:
      --wait
      --until <STATUS>
      --timeout <MS>
""",
    ("agent", "list"): """List agents

Usage: herdr agent list
""",
}


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


if "-h" in args or "--help" in args:
    cmd = tuple(a for a in args if a not in ("-h", "--help"))
    if uses == "unreadable" and cmd:
        print(HERDR_HELP_TOP)
        sys.exit(0)
    if not cmd:
        print(HERDR_HELP_TOP)
        sys.exit(0)
    page = HERDR_HELP.get(cmd)
    if page is None:
        print(HERDR_HELP_TOP)
        sys.exit(0)
    if uses == "mismatch" and cmd == ("tab", "create"):
        page = page.replace("      --no-focus\n", "")
    print(page)
    sys.exit(0)

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
uses = os.environ.get("MMW_FAKE_USES", "agree")


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


if args[:1] == ["agent-context"]:
    wait_flags = ["help", "json", "pairing-code", "environment",
                  "terminal", "for", "timeout-ms"]
    if uses == "mismatch":
        wait_flags = [f for f in wait_flags if f != "for"]
    if uses == "orca-unreadable":
        wait_flags = "terminal for timeout-ms"
    print(json.dumps({
        "schemaVersion": 1,
        "commandCount": 5,
        "commands": [
            {"command": "terminal create",
             "flags": ["help", "json", "worktree", "command", "title"]},
            {"command": "terminal send",
             "flags": ["help", "json", "terminal", "text", "enter",
                       "wait-submit"]},
            {"command": "terminal wait", "flags": wait_flags},
            {"command": "terminal list",
             "flags": ["help", "json", "worktree"]},
            {"command": "terminal close",
             "flags": ["help", "json", "terminal"]},
        ],
    }))
    sys.exit(0)

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

if args[:2] == ["worktree", "ps"] or args[:2] == ["worktree", "rm"] \
        or args[:2] == ["worktree", "create"]:
    print(json.dumps({"ok": True, "result": {}}))
    sys.exit(0)

if args[:2] == ["terminal", "create"]:
    if scenario == "start-fail":
        print(json.dumps({"ok": False, "error": {"code": "create_failed"}}),
              file=sys.stderr)
        sys.exit(1)
    handle = "term_%s" % (len(load_terminals()) + 1)
    rows = load_terminals()
    rows.append({
        "handle": handle,
        "connected": True,
        "writable": True,
        "worktree": opt("--worktree"),
        "title": opt("--title"),
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

if args[:2] == ["terminal", "wait"]:
    if scenario == "wait-fail":
        sys.exit(1)
    if scenario == "wait-garbage":
        print("not-json")
        sys.exit(0)
    target = opt("--terminal")
    want = opt("--for")
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
                "result": {"satisfied": True, "status": "exited"},
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
            "result": {"satisfied": False, "status": "running"},
        }))
        sys.exit(0)
    print(json.dumps({
        "ok": True,
        "result": {"satisfied": True, "status": "running"},
    }))
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
  "repo view"*)
    printf '%s\n' "${FAKE_GH_REPO:-o/r}" ;;
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
    "title": found.get("title", "a ticket"),
    "createdAt": found.get("createdAt", "2026-08-30T00:00:00Z"),
    "closedAt": found.get("closedAt", ""),
}))
' ;;
  *"--json comments"*)
    MMW_WANT="$3" python3 -c '
import json, os
from pathlib import Path
path = os.environ.get("FAKE_GH_TICKETS_FILE")
rows = json.load(open(path)) if path else []
try:
    want = int(os.environ["MMW_WANT"])
except Exception:
    want = None
# Time passing while `wait` waits. `wait` reads the ticket, sleeps a beat, and reads it
# again; from the second read on, the agent has finished: MMW_FAKE_WAIT_COMMENT lands on
# the ticket and MMW_FAKE_WAIT_STATUS becomes every agent status. The first read sees
# neither, so a scenario can tell "already there" from "arrived while waiting".
state = os.environ.get("MMW_FAKE_PASEO_STATE")
if state and (os.environ.get("MMW_FAKE_WAIT_COMMENT") or os.environ.get("MMW_FAKE_WAIT_STATUS")):
    counter = Path(state) / "comment_reads"
    reads = int(counter.read_text()) + 1 if counter.is_file() else 1
    counter.write_text(str(reads))
    done = Path(state) / "wait_delivered"
    if reads >= 2 and not done.is_file():
        done.write_text("1")
        comment = os.environ.get("MMW_FAKE_WAIT_COMMENT", "")
        if comment and path:
            for t in rows:
                if t.get("number") == want:
                    t.setdefault("comments", []).append(comment)
            Path(path).write_text(json.dumps(rows), encoding="utf-8")
        status = os.environ.get("MMW_FAKE_WAIT_STATUS", "")
        agents = Path(state) / "agents.json"
        if status and agents.is_file():
            ag = json.loads(agents.read_text(encoding="utf-8"))
            for a in ag:
                a["status"] = status
            agents.write_text(json.dumps(ag), encoding="utf-8")
found = next((t for t in rows if t.get("number") == want), {})
store = Path(state or ".") / "gh-comments.json"
posted = json.loads(store.read_text()).get(str(want), []) if state and store.is_file() else []
print(json.dumps({
    "comments": [{"body": b} for b in list(found.get("comments", [])) + posted],
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
  "issue comment "*)
    # FAKE_GH_COMMENT_FAILS: the tracker refuses the comment, the way a network drop does.
    [ -z "${FAKE_GH_COMMENT_FAILS:-}" ] || { echo "HTTP 502" >&2; exit 1; }
    MMW_N="$3" python3 -c '
import json, os
from pathlib import Path
store = Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json"
rows = json.loads(store.read_text()) if store.is_file() else {}
rows.setdefault(os.environ["MMW_N"], []).append(Path(os.environ["MMW_GH_LAST_BODY"]).read_text().rstrip("\n"))
store.write_text(json.dumps(rows))
'
    echo "https://github.com/o/r/issues/$3#issuecomment-1" ;;
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
chmod +x "$TMP/bin/python3" "$TMP/bin/paseo" "$TMP/bin/herdr" "$TMP/bin/orca" "$TMP/bin/gh"
export PATH="$TMP/bin:$PATH"
export MMW_TEST_LOG="$TMP/calls.log"
export MMW_FAKE_PASEO_STATE="$TMP/paseo-state"
export MMW_FAKE_HERDR_STATE="$TMP/herdr-state"
export MMW_FAKE_ORCA_STATE="$TMP/orca-state"
export MMW_GH_LAST_BODY="$TMP/gh-last-body"
export MMW_HOME="$TMP/mmw-home"
export MMW_LIVE_MODELS="$TMP/live-models.md"
# Tonight's runner is pinned: the session running this suite may itself sit in Orca,
# Herdr or tmux, and runtime detection would pick that runner.
export MMW_RUNNER=paseo
export MMW_HOST_CATALOG="$HERE/catalog.json"
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
python3 -c '
import importlib.util
from pathlib import Path
p = Path("'"$SKILL"'/scripts/models.py")
spec = importlib.util.spec_from_file_location("mmw_models", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
Path("'"$MMW_LIVE_MODELS"'").write_text(mod.default_live_markdown(), encoding="utf-8")
'

git init -q -b main "$TMP/repo"
git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q --allow-empty -m fixture

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

# A stand-in for a running relay that watches <watch> (default spec 76): a process of its
# own, detached so that nobody here has to reap it, whose pid and identity the lock record
# and relay.json name. It never polls; only what `watching`, `start` and `stop` read of a
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
(state / "relay.json").write_text(json.dumps({"pid": child.pid, "identity": identity,
                                              "watch": json.loads(sys.argv[3])}) + "\n")
PY
}

# The pid of the relay holding o/r's lock, and what relay.json says it watches; nothing
# when none runs.
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
        watch = json.loads((state / "relay.json").read_text()).get("watch")
    except Exception:
        watch = None
    print(holder["pid"], json.dumps(watch, sort_keys=True))
PY
}

# A Paseo agent `paseo ls` lists as idle, standing in for the main agent's own session.
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
    "$MMW_FAKE_PASEO_STATE/gh-comments.json" "$MMW_FAKE_PASEO_STATE/runs.jsonl"
  echo '[]' > "$MMW_FAKE_HERDR_STATE/agents.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/terminals.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/setups.json"
  echo '[]' > "$MMW_FAKE_ORCA_STATE/repos.json"
  unset MMW_FAKE_HERDR_SCENARIO MMW_FAKE_HERDR_PROMPT MMW_FAKE_SEND_FAILS
  unset MMW_FAKE_ORCA_SCENARIO MMW_FAKE_ORCA_SEND MMW_FAKE_USES
  rm -rf "$MMW_HOME/leases"
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
    print(" ".join([payload["event"]] + [f"{k}={payload.get(k)}" for k in keys]))
'
}
export MMW_EVENTS_PY_FOR_TESTS="$(dirname "$SKILL")/verify-ticket/scripts/events.py"

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
for key in ("title", "provider", "labels", "initialPrompt", "cwd"):
    assert run.get(key), key
kind = run["labels"]["mmw.kind"]
ticket = run["labels"]["mmw.ticket"]
assert run["cwd"].endswith("/.worktrees/issue-" + ticket), run["cwd"]
posted = json.loads(Path(sys.argv[3]).read_text()).get(ticket, [])
state = ev.fold(posted)
found = ev.session_of(state, kind)
assert found and found["session"] == run["id"] and found["runner"] == "paseo", (found, posted)
assert found["worktree"] == run["cwd"] and found["branch"] == "issue-" + ticket, found
' "$TMP/out" "$MMW_FAKE_PASEO_STATE/runs.jsonl" "$MMW_FAKE_PASEO_STATE/gh-comments.json"
}

row_host() { awk -F'|' -v want="$1" 'function t(s){gsub(/^[ \t`]+|[ \t`]+$/,"",s);return s} /^[ \t]*\|/ && NF==6 && t($2)==want {print t($3); exit}' "$MMW_LIVE_MODELS"; }
JUNIOR_HOST="$(row_host junior-worker)"
JUNIOR_MODEL=grok-4.6
SENIOR_MODEL=grok-4.6
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
   "comments": ["self-run\\n3 met", $(ev ticket.passed 61 "ALL MET" --field branch=issue-61)]},
  {"number": 62, "state": "CLOSED", "labels": [], "closedAt": "2026-08-31T02:00:00Z",
   "assignees": ["alice"],
   "comments": [$(ev ticket.passed 62 "ALL MET" --field branch=issue-62)]},
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
  printf '%s\n' --field host=grok --field model=grok-4.6 --field effort=high \
    --field "grade=$grade" --field "worktree=$1" --field "branch=issue-$2" \
    --field "base=0000000000000000000000000000000000000000"
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

# The scripts of the two other skills dispatch.sh runs are handed to it with --tools,
# the way the agent does; TOOLS holds those arguments for every call below.
TOOLS=(--tools "$TMP/fake/skills/drive-target/scripts" --tools "$TMP/fake/skills/verify-ticket/scripts"
       --tools "$(dirname "$SKILL")/drive-target/scripts" --tools "$(dirname "$SKILL")/verify-ticket/scripts")

skill_copy_for() {
  local copy="$TMP/fake/skills/$1"
  rm -rf "$TMP/fake"
  mkdir -p "$copy" "$TMP/fake/skills/verify-ticket/scripts" "$TMP/fake/skills/drive-target/scripts"
  cp -R "$SKILL/hosts.json" "$SKILL/scripts" "$SKILL/references" "$copy/"
  cp "$(dirname "$SKILL")/drive-target/scripts/lease.py" \
     "$(dirname "$SKILL")/drive-target/scripts/refusal.py" \
     "$TMP/fake/skills/drive-target/scripts/"
  cp "$(dirname "$SKILL")/verify-ticket/scripts/events.py" \
     "$TMP/fake/skills/verify-ticket/scripts/"
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

  echo "--- every host of the batch is refreshed once, however many rows share it"
  [ "$(count_of 'provider :: diagnostic')" = 3 ] \
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
  grep -q 'grok' "$TMP/err" || fail "the reason does not name the provider: $(cat "$TMP/err")"
  grep -q '#61' "$TMP/err" || fail "the reason does not name the ticket: $(cat "$TMP/err")"
  grep -q 'Auth: not logged in' "$TMP/err" \
    || fail "the refusal should carry the host's own account of why: $(cat "$TMP/err")"
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

# Tickets outside any batch: what `land` was built for. #64 is finished, #65 was
# handed back, #66 is still being worked, #67 closed with its branch unmerged.
write_landable() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 64, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T01:00:00Z",
   "assignees": ["mmw-bot"], "parent": null,
   "comments": ["reverify\\nALL MET (1 met)", $(ev ticket.passed 64 "ALL MET" --field branch=issue-64)]},
  {"number": 65, "state": "OPEN", "labels": ["needs-triage"], "parent": null,
   "assignees": ["mmw-bot"],
   "comments": [$(ev ticket.returned 65 "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1")]},
  {"number": 66, "state": "OPEN", "labels": ["ready-for-agent"], "parent": null,
   "assignees": ["mmw-bot"], "comments": ["self-run\\nUNMET: 1 (met: 0)"]},
  {"number": 67, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T02:00:00Z",
   "parent": null, "comments": [$(ev ticket.passed 67 "ALL MET" --field branch=issue-67)]},
  {"number": 68, "state": "CLOSED", "labels": [], "closedAt": "2026-09-07T03:00:00Z",
   "parent": null, "comments": ["voided: superseded by the spec"]},
  {"number": 69, "state": "OPEN", "labels": ["needs-triage"], "parent": null,
   "assignees": [], "comments": [$(ev ticket.returned 69 "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1")]}
]
JSON
}

scenario_land() {
  reset_log
  fresh_repo
  write_landable
  make_branch issue-64 four.txt "from 64"
  make_branch issue-67 seven.txt "from 67"
  seed_workspace 64
  seed_workspace 65
  seed_workspace 66
  local code

  echo "--- landing one finished ticket merges it, then removes its worktree"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -f "$TMP/repo/four.txt" ] || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_branch 64
  hasnt_runner_worktree

  echo "--- and gives the claim back, which closing a ticket before this did not"
  has "gh :: issue :: edit :: 64 :: --remove-assignee :: @me"

  echo "--- both are events on the ticket: landed, then the claim released as landed"
  [ "$(posted_events 64 branch reason | tr '\n' '|')" = "ticket.landed branch=issue-64 reason=None|ticket.released branch=None reason=landed|" ] \
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
  grep -q "open with no verdict" "$TMP/err" \
    || fail "the hold should say why: $(cat "$TMP/err")"

  echo "--- a ticket handed back keeps its worktree for the next start, and gives the claim back"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 65)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 65 :: --remove-assignee :: @me"
  assert_wt 65
  hasnt_runner_worktree

  echo "--- a closed ticket whose branch is not in HEAD is reported, not archived"
  reset_log
  seed_workspace 67
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 67)"
  [ -f "$TMP/repo/seven.txt" ] || fail "issue-67 should have been merged first"
  assert_no_wt 67
  assert_branch 67
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
  grep -q "#69 needs nothing" "$TMP/err" \
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
  [ ! -f "$TMP/repo/eight.txt" ] || fail "a ticket that did not close ALL MET must not be merged"
  assert_wt 68
  hasnt_runner_worktree
  grep -q "not in HEAD" "$TMP/err" \
    || fail "the refusal should name what is unmerged: $(cat "$TMP/err")"
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

  echo "--- a worktree is removed only after its branch is merged, then the frontier is created"
  assert_no_wt 61
  assert_no_wt 62
  assert_branch 61
  assert_branch 62
  assert_wt 63
  [ "$(git -C "$(wt 63)" rev-parse --abbrev-ref HEAD)" = issue-63 ] \
    || fail "frontier worktree should be on issue-63"
  hasnt_runner_worktree
  started_once
  assert_started || fail "the dispatched JSON is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#63 worker" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.ticket)" = 63 ] || fail "ticket: $(out_json labels.mmw.ticket)"
  [ "$(out_json labels.mmw.kind)" = worker ] || fail "kind: $(out_json labels.mmw.kind)"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert obj["cwd"].endswith("/.worktrees/issue-63"), obj["cwd"]
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "the session must start in the ticket worktree"
  grep -q "advance #76:" "$TMP/err" || fail "the summary line should be on stderr: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base)" = "$(git -C "$TMP/repo" rev-parse HEAD)" ] \
    || fail "mmw-base should be HEAD for a branch-off"
  [ "$(git -C "$TMP/repo" config --get branch.issue-63.mmw-base-branch)" = main ] \
    || fail "mmw-base-branch should be main"

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
  echo "--- a ticket with no worker label starts one session on the default row and prints its id"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  assert_started || fail "the JSON line is wrong: $(cat "$TMP/out")"
  [ "$(out_json title)" = "#61 worker" ] || fail "title: $(out_json title)"
  [ "$(out_json provider)" = "$JUNIOR_HOST/$JUNIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(out_json labels.mmw.ticket)" = 61 ] || fail "ticket label"
  [ "$(out_json labels.mmw.kind)" = worker ] || fail "kind label"
  [ "$(out_json labels.mmw.spec)" = 76 ] || fail "spec label"
  [ "$(out_json labels.mmw.autonomous)" = 1 ] || fail "autonomous label"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert "mmw.profile" not in obj["labels"], obj["labels"]
assert obj["settings"].get("thinkingOptionId") == "true", obj["settings"]
assert obj["settings"].get("modeId") == "agent", obj["settings"]
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "paseo run settings changed: $(cat "$TMP/out")"
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
  [ "$(out_json provider)" = "grok/$SENIOR_MODEL" ] || fail "provider: $(out_json provider)"
  [ "$(out_json settings.thinkingOptionId)" = xhigh ] || fail "effort: $(out_json settings.thinkingOptionId)"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert "mmw.profile" not in obj["labels"], obj["labels"]
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "the senior-worker start carries a profile label"

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

  echo "--- a refused lease removes a worktree this start created, and keeps one that already stood"
  reset_log
  fresh_repo
  seed_workspace 99
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-99" >/dev/null
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 when the lease is refused, got $code: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_wt 99
  hasnt_runner_worktree
  grep -q 'issue-61:' "$TMP/err" || fail "the refusal should name the ticket: $(cat "$TMP/err")"
  grep -q 'instance slots' "$TMP/err" || fail "the refusal should carry lease.py's slot fact: $(cat "$TMP/err")"
  grep -q 'Report the ticket blocked and stop' "$TMP/err" \
    || fail "the refusal should carry lease.py's next step: $(cat "$TMP/err")"
  reset_log
  fresh_repo
  seed_workspace 61
  seed_workspace 99
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-99" >/dev/null
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 on a standing worktree, got $code: $(cat "$TMP/err")"
  assert_wt 61
  hasnt_runner_worktree
  grep -q 'issue-61:' "$TMP/err" || fail "the refusal should name the ticket: $(cat "$TMP/err")"

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
assert obj["settings"].get("thinkingOptionId") == "true"
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "copied start settings are wrong: $(cat "$TMP/out")"
}

scenario_retract() {
  local code
  echo "--- usage lists retract"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}")"
  [ "$code" = 2 ] || fail "expected exit 2 for usage, got $code: $(cat "$TMP/err")"
  grep -qF 'retract <n>' "$TMP/err" \
    || fail "usage should list retract: $(cat "$TMP/err")"

  echo "--- retract after start removes the worktree and gives the slot back"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"]}]
JSON
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "start should hold one slot, it holds $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_branch 61
  hasnt_runner_worktree
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "the slot should be free after retract, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  grep -q "retract #61: archived 1, slot given back 1, claim given back 1" "$TMP/err" \
    || fail "the counters should match what was undone: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 61 :: --remove-assignee :: @me"

  echo "--- a second retract on the same ticket is a no-op, not a lie about the slot"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "second retract expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "workspace :: archive"
  grep -q "retract #61: archived 0, slot given back 0, claim given back 0" "$TMP/err" \
    || fail "a second retract should report zeros: $(cat "$TMP/err")"

  echo "--- the freed slot is what the next start takes, not a second slot"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 62 worker)"
  [ "$code" = 0 ] || fail "start after retract expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "the next start should take the freed slot, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  assert_wt 62

  echo "--- a live agent on the ticket is refused, and the workspace stays"
  reset_log
  fresh_repo
  seed_workspace 61
  seed_agent 61 worker
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-61" >/dev/null
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2 with a live agent, got $code: $(cat "$TMP/err")"
  hasnt "workspace :: archive"
  grep -q "live agent" "$TMP/err" \
    || fail "the refusal should say a live agent is on the ticket: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "a refused retract must not give the slot back, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  echo "--- a claim this pipeline does not hold is left alone"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["a-human"]}]
JSON
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  grep -q "claim given back 0" "$TMP/err" \
    || fail "someone else's claim must stay: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "the slot should still be given back: $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  echo "--- with no lease.py to be found at all, retract refuses and the slot stays held"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  local copy
  copy="$(skill_copy_for retract)"
  rm -f "$TMP/fake/skills/drive-target/scripts/lease.py"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$copy/scripts/dispatch.sh" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2 without lease.py, got $code: $(cat "$TMP/err")"
  grep -q "lease.py" "$TMP/err" \
    || fail "the refusal should name lease.py: $(cat "$TMP/err")"
  hasnt "workspace :: archive"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "the slot must stay held when retract cannot see lease.py, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  echo "--- and with the drive-target skill next door, no --tools is needed to find it"
  : > "$MMW_TEST_LOG"
  cp "$(dirname "$SKILL")/drive-target/scripts/lease.py" "$TMP/fake/skills/drive-target/scripts/"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$copy/scripts/dispatch.sh" retract 61)"
  [ "$code" = 0 ] || fail "expected exit 0 with lease.py next door, got $code: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "the slot should be given back, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
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
  started_once
  [ "$(out_json title)" = "#61 reviewer" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.kind)" = reviewer ] || fail "kind label"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert "mmw.profile" not in obj["labels"], obj["labels"]
assert obj["provider"] == "claude/claude-opus-5", obj["provider"]
assert obj["settings"].get("thinkingOptionId") == "high"
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "reviewer payload: $(cat "$TMP/out")"
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
  local code
  reset_log
  fresh_repo
  seed_workspace 61
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 verifier)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  [ "$(out_json title)" = "#61 verifier" ] || fail "title: $(out_json title)"
  [ "$(out_json labels.mmw.kind)" = verifier ] || fail "kind label"
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
assert "mmw.profile" not in obj["labels"], obj["labels"]
assert obj["provider"] == "claude/claude-sonnet-5", obj["provider"]
assert obj["settings"].get("thinkingOptionId") == "high"
' "$MMW_FAKE_PASEO_STATE/runs.jsonl" || fail "verifier payload: $(cat "$TMP/out")"
  case "$(out_json initialPrompt)" in
    "Use the verdict skill to verify ticket #61."*) ;;
    *) fail "the verifier prompt does not name the verdict skill: $(out_json initialPrompt)" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"You are operating autonomously"*) ;;
    *) fail "the autonomous sentence is missing from the verifier prompt" ;;
  esac
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

  echo "--- a worker that is there but will not take the message is exit 3, not 2"
  reset_log
  seed_agent 61 worker
  code="$(run_dispatch env MMW_FAKE_SEND_FAILS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 3 ] || fail "a busy worker must not read as a missing one, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_61_worker :: continue"

  echo "--- and the refusal says to wait and run it again, not to stop sending"
  grep -q "run resume again" "$TMP/err" \
    || fail "the refusal should send the caller back to the same command: $(cat "$TMP/err")"

  echo "--- it names get_agent_status as the way to tell busy from stuck"
  grep -q "get_agent_status" "$TMP/err" \
    || fail "a caller that keeps hitting exit 3 needs the one field that settles it: $(cat "$TMP/err")"
}

scenario_wait() {
  local code

  echo "--- usage lists wait"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}")"
  [ "$code" = 2 ] || fail "expected exit 2 for usage, got $code: $(cat "$TMP/err")"
  grep -qF 'wait <n> worker|reviewer|verifier' "$TMP/err" \
    || fail "usage should list wait: $(cat "$TMP/err")"

  echo "--- a result already on the ticket is printed and wait is not called"
  reset_log
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"],
   "comments": [$(ev reviewer.reported 61 "REVIEW abcdef0123456789abcdef0123456789abcdef01..fedcba9876543210fedcba9876543210fedcba98" --field base=abcdef0123456789abcdef0123456789abcdef01)]}
]
JSON
  seed_agent 61 reviewer
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 reviewer)"
  [ "$code" = 0 ] || fail "expected exit 0 when the result is already there, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = "reviewer.reported base=abcdef0123456789abcdef0123456789abcdef01" ] \
    || fail "stdout should be the event and its key fields: $(cat "$TMP/out")"
  hasnt "paseo :: wait"
  hasnt "gh :: issue :: comment"
  hasnt "paseo :: archive"
  hasnt "paseo :: send"

  echo "--- wait then the result comment, printed, exit 0"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}
]
JSON
  seed_agent 61 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_WAIT_COMMENT="$(python3 "$EVENTS_PY" emit ticket.passed --ticket 61 --line "ALL MET")" \
          MMW_WAIT_S=6 MMW_WAIT_BEAT_S=1 \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0 after wait, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = "ticket.passed" ] \
    || fail "stdout should be ticket.passed: $(cat "$TMP/out")"
  hasnt "paseo :: wait"
  has "gh :: issue :: view :: 61 :: --json :: comments"
  hasnt "gh :: issue :: comment"
  hasnt "paseo :: archive"

  echo "--- the agent is gone with no result: exit 1, stderr names logs and the fallback"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}
]
JSON
  seed_agent 61 verifier
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_WAIT_STATUS=closed MMW_WAIT_S=6 MMW_WAIT_BEAT_S=1 \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 verifier)"
  [ "$code" = 1 ] || fail "expected exit 1 with no result, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: wait"
  grep -q "agt_61_verifier on #61 stopped with no verifier.passed or verifier.failed event; read its session on paseo" "$TMP/err" \
    || fail "stderr should name the session and its runner: $(cat "$TMP/err")"
  grep -q "verifier.passed" "$TMP/err" \
    || fail "stderr should name the missing verdict event: $(cat "$TMP/err")"
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "stderr should be one line: $(cat "$TMP/err")"
  [ ! -s "$TMP/out" ] || fail "stdout should be empty on exit 1: $(cat "$TMP/out")"

  echo "--- idle between turns with no result yet: exit 3, no fallback"
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
          MMW_WAIT_S=6 MMW_WAIT_BEAT_S=1 \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 reviewer)"
  ended="$(date +%s)"
  [ "$code" = 3 ] || fail "an idle reviewer is mid-job, expected exit 3, got $code: $(cat "$TMP/err")"
  grep -q "still working" "$TMP/err" \
    || fail "stderr should say still working: $(cat "$TMP/err")"
  grep -q "code-review skill" "$TMP/err" \
    && fail "an idle reviewer must not be sent to the fallback: $(cat "$TMP/err")"

  echo "--- and the budget was really spent, one ticket read per beat"
  [ "$((ended - began))" -ge 6 ] \
    || fail "wait returned after $((ended - began))s of a 6s budget, so exit 3 has no beat in it"
  [ "$(count_of 'gh :: issue :: view :: 61 :: --json :: comments')" -ge 2 ] \
    || fail "expected more than one ticket read inside the budget: $(count_of 'gh :: issue :: view :: 61 :: --json :: comments')"
  hasnt "paseo :: wait"

  echo "--- timeout while still running: exit 3"
  reset_log
  cat > "$TMP/tickets.json" <<'JSON'
[
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}
]
JSON
  seed_agent 61 worker
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          MMW_FAKE_PASEO_SCENARIO=wait-timeout MMW_WAIT_S=6 MMW_WAIT_BEAT_S=1 \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 3 ] || fail "expected exit 3 on timeout, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: wait"
  [ "$(cat "$TMP/err")" = "still working: run wait again" ] \
    || fail "stderr should say run wait again: $(cat "$TMP/err")"
  [ ! -s "$TMP/out" ] || fail "stdout should be empty on timeout: $(cat "$TMP/out")"

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
  grep -q "no reviewer.started event" "$TMP/err" \
    || fail "stderr should say there is no session on the ticket: $(cat "$TMP/err")"
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
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
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
  posted_events 62 failed | grep -qx "ticket.regressed failed=\['AC3'\]" \
    || fail "#62 should carry ticket.regressed naming AC3: $(posted_events 62 failed)"

  echo "--- a ticket that passed and has not landed is not run again on the base branch"
  reset_log
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL= \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "verify-ticket :: 61 :: --reverify"
  hasnt "verify-ticket :: 62 :: --reverify"
  grep -q "#62 passed and has not landed" "$TMP/err" \
    || fail "the skipped ticket should be named: $(cat "$TMP/err")"

  echo "--- all green exits 0"
  reset_log
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
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
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61),
                $(ev ticket.landed 61 "Landed issue-61 into main")]}
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
  grep -q "Closed: #61 ALL MET" "$MMW_GH_LAST_BODY" \
    || fail "the closed line should carry the ticket's own result line: $(cat "$MMW_GH_LAST_BODY")"
  posted_events 76 date | grep -q "^spec.closed date=" \
    || fail "the summary should be the spec.closed event on #76: $(posted_events 76 date)"

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

  echo "--- summary stops the relay watching the spec, and leaves one watching another alone"
  no_relay
  fake_relay
  [ -n "$(relay_now)" ] || fail "the stand-in relay should be running before summary"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "summary should have stopped the relay: $(relay_now)"
  grep -q "stopped the relay for o/r" "$TMP/err" || fail "summary should say it stopped the relay: $(cat "$TMP/err")"
  fake_relay '{"spec": 80}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "a relay watching another spec is not this summary's failure, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"spec": 80}'*) ;; *) fail "a relay watching spec 80 should be left running: $(relay_now)" ;; esac
  grep -q "does not watch #76, so it was left running" "$TMP/err" || fail "summary should say why it left it: $(cat "$TMP/err")"
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
  grep -q "released the claim on #63" "$TMP/err" \
    || fail "the release was silent: $(cat "$TMP/err")"
  grep -q "the worker that claimed it is gone" "$TMP/err" \
    || fail "the line does not say why: $(cat "$TMP/err")"
  posted_events 63 reason | grep -qx "ticket.released reason=worker-lost" \
    || fail "#63 should carry ticket.released (worker-lost): $(posted_events 63 reason)"

  echo "--- the ticket it frees is dispatched by the same advance, not the next one"
  assert_wt 63
  hasnt_runner_worktree
  grep -q "started 1" "$TMP/err" || fail "it was freed and then left: $(cat "$TMP/err")"

  echo "--- in that order: released first, started after"
  local rel
  rel="$(line_of 'issue :: edit :: 63 :: --remove-assignee')"
  [ "$rel" -gt 0 ] || fail "the claim was never released"
  grep -q "started 1" "$TMP/err" || fail "dispatch summary came without a start"

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
  grep -q "#63 claimed by mmw-bot; held by the worker agt_63_worker on paseo" "$TMP/err" \
    || fail "stderr does not name the worker holding it: $(cat "$TMP/err")"
  grep -q "#63 keeps its claim: the worker agt_63_worker on paseo is live on its events" "$TMP/err" \
    || fail "stderr does not say why the claim is kept: $(cat "$TMP/err")"
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
  grep -q "3 open ticket(s) are still in the agent queue" "$TMP/err" \
    || fail "the count is wrong or missing: $(cat "$TMP/err")"
  grep -q "#61 claimed by alice" "$TMP/err" || fail "#61: $(cat "$TMP/err")"
  grep -q "#62 blocked by #61" "$TMP/err" || fail "#62: $(cat "$TMP/err")"
  grep -q "#63 held by the worker agt_63_worker on paseo" "$TMP/err" || fail "#63: $(cat "$TMP/err")"
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
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-99" >/dev/null
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-62" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 2 ] \
    || fail "setup should hold two slots, it holds $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"

  echo "--- the merges still happen: the gate is about starting, not about landing work"
  [ -f "$TMP/repo/one.txt" ] || fail "issue-61 was not merged"
  [ -f "$TMP/repo/two.txt" ] || fail "issue-62 was not merged"

  echo "--- a merged ticket's lease is released before its worktree is removed"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "issue-62's lease should be gone after archive, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  assert_no_wt 62
  assert_branch 62
  hasnt_runner_worktree

  echo "--- the frontier ticket is held back rather than sent onto a busy machine"
  grep -q "held 1" "$TMP/err" || fail "nothing was held back: $(cat "$TMP/err")"
  grep -q "held back" "$TMP/err" || fail "the reason was not reported: $(cat "$TMP/err")"
  assert_no_wt 63

  echo "--- it kept its label, so the next advance starts it once a slot is free"
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  python3 "$LEASE_PY" release "$TMP/repo/.worktrees/issue-99" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "issue-99 should be free before the second advance"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code on the second run: $(cat "$TMP/err")"
  assert_wt 63
  hasnt_runner_worktree

  rm -f "$TMP/repo/.mmw/target.json"
}

scenario_countfail() {
  local code
  echo "--- lease.py count failing is a refusal, not a silent open gate"
  reset_log
  fresh_repo
  write_batch
  mkdir -p "$TMP/repo/.mmw" "$TMP/fake-lease"
  printf '%s\n' '{"start":"true","discover":"true","reach":"true","instance":{"max":1,"why":"fixed host ports"}}' \
    > "$TMP/repo/.mmw/target.json"
  cat > "$TMP/fake-lease/lease.py" <<'PY'
#!/usr/bin/env python3
import sys
print("lease count failed", file=sys.stderr)
sys.exit(1)
PY
  chmod +x "$TMP/fake-lease/lease.py"
  seed_workspace 61
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" --tools "$TMP/fake-lease" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "expected exit 2 when count fails, got $code: $(cat "$TMP/err")"
  grep -q "could not count live instances" "$TMP/err" \
    || fail "the reason should say count failed: $(cat "$TMP/err")"
  hasnt "workspace :: create"
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
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-65" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 3 ] \
    || fail "the night should hold three slots, it holds $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  seed_agent 61 worker
  seed_agent 99 worker 99
  seed_foreign_workspace
  mkdir -p "$TMP/other-repo/issue-61"
  python3 "$LEASE_PY" claim "$TMP/other-repo/issue-61" >/dev/null
  # Directory gone, lease remains. Must happen after the other-repo claim: `lease.py claim`
  # sweeps slots whose directory is already gone.
  git -C "$TMP/repo" worktree remove --force "$TMP/repo/.worktrees/issue-65" >/dev/null
  claim_tickets 61 63

  echo "--- suspend archives the live worker, comments, gives the slots and claims back"
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
  [ "$(count_of "/sub_issues")" = 1 ] \
    || fail "the batch should be read once, got $(count_of "/sub_issues")"
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
  grep -qF 'Its worker agt_61_worker was interrupted' "$MMW_TEST_LOG" \
    || fail "the comment on #61 does not say its worker was interrupted"
  grep -qF 'No session of ours was working on it' "$MMW_TEST_LOG" \
    || fail "the comment on #63 does not say it had no session"
  hasnt "gh :: issue :: comment :: 65"

  echo "--- the slots the night held are back"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "slots are still held: $(python3 "$LEASE_PY" list)"
  [ "$(python3 "$LEASE_PY" count "$TMP/other-repo")" = 1 ] \
    || fail "a lease from another checkout was released: $(python3 "$LEASE_PY" list)"
  grep -q 'suspend #76: stopped 1, commented 2, slots given back 3, claims given back 2' "$TMP/out" \
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

scenario_stopproduct() {
  local code marker ws
  echo "--- the product is stopped before its slot is given back and its worktree deleted"
  reset_log
  fresh_repo
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "assignees": ["mmw-bot"]}]
JSON
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected exit 0, got $code: $(cat "$TMP/err")"
  # Retract is for a start whose session is gone, so the session is shown gone first.
  set_agent_status "$(cat "$TMP/out")" closed
  ws="$TMP/repo/.worktrees/issue-61"
  marker="$TMP/stopped-61"
  rm -f "$marker"
  mkdir -p "$ws/.mmw"
  printf '{"start":"true","discover":"true","reach":"true","stop":"touch %s"}\n' "$marker" \
    > "$ws/.mmw/target.json"

  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 0 ] || fail "retract expected exit 0, got $code: $(cat "$TMP/err")"
  [ -f "$marker" ] \
    || fail "the repository's stop command should have run before the worktree went: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_branch 61
  hasnt_runner_worktree
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "the slot should be free once the product is stopped"

  echo "--- a repository that declares no stop is not a failure"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 62 worker)"
  [ "$code" = 0 ] || fail "start 62 expected exit 0, got $code: $(cat "$TMP/err")"
  # Retract is for a start whose session is gone, so the session is shown gone first.
  set_agent_status "$(cat "$TMP/out")" closed
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 62)"
  [ "$code" = 0 ] || fail "retract 62 expected exit 0, got $code: $(cat "$TMP/err")"
  assert_no_wt 62
  assert_branch 62
  hasnt_runner_worktree

  echo "--- a product that will not go down keeps its worktree, and the refusal says where"
  reset_log
  fresh_repo
  local port hold listener waited
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 63 worker)"
  [ "$code" = 0 ] || fail "start 63 expected exit 0, got $code: $(cat "$TMP/err")"
  # Retract is for a start whose session is gone, so the session is shown gone first.
  set_agent_status "$(cat "$TMP/out")" closed
  ws="$TMP/repo/.worktrees/issue-63"
  mkdir -p "$ws/.mmw"
  printf '%s\n' '{"start":"true","discover":"true","reach":"true","stop":"true"}' \
    > "$ws/.mmw/target.json"
  # `claim` on a worktree that already has a slot is a lookup and prints the record, so
  # this reads #63's port without parsing `list`, which is the human view.
  port="$(python3 "$LEASE_PY" claim "$ws" \
          | python3 -c 'import json,sys; print(json.load(sys.stdin)["port_base"])')"
  [ -n "$port" ] || fail "could not read #63's port from lease.py claim"
  hold="$TMP/listener63.fifo"
  rm -f "$hold"; mkfifo "$hold"
  python3 -c '
import socket, sys
held = socket.socket()
held.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
held.bind(("127.0.0.1", int(sys.argv[1])))
held.listen(1)
print("up", flush=True)
sys.stdin.read()
' "$port" < "$hold" > "$TMP/listener63.out" &
  listener=$!
  exec 8>"$hold"
  waited=0
  until grep -q up "$TMP/listener63.out" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    [ "$waited" -lt 50 ] || fail "the test listener never came up"
  done

  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 FAKE_GH_LOGIN=mmw-bot \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" retract 63)"
  hasnt "workspace :: archive"
  grep -q "keeps its workspace" "$TMP/err" \
    || fail "the refusal should say the workspace is kept: $(cat "$TMP/err")"
  grep -qF "$ws" "$TMP/err" \
    || fail "the refusal should name the worktree to stop it in: $(cat "$TMP/err")"

  exec 8>&-
  wait "$listener" 2>/dev/null || true
  python3 "$LEASE_PY" release "$ws" >/dev/null 2>&1 || true
}

scenario_suspendbusy() {
  local code port hold
  fresh_repo
  reset_log
  write_open_batch
  open_a_night
  # The night's starts are real sessions now; this scenario seeds the one it wants.
  echo '[]' > "$MMW_FAKE_PASEO_STATE/agents.json"
  seed_workspace 65
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-65" >/dev/null
  seed_agent 61 worker

  echo "--- something is still listening on #61's slot"
  port="$(python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-61" \
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
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "a slot with a live listener was taken anyway: $(python3 "$LEASE_PY" list)"

  echo "--- and the rest of the night is still suspended: workers archived, tickets told"
  has "paseo :: archive :: --force :: agt_61_worker"
  hasnt "paseo :: stop"
  [ "$(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")" = 3 ] \
    || fail "expected the spec and two tickets told, got $(grep -cF 'NIGHT SUSPENDED #76' "$MMW_TEST_LOG")"
  grep -q 'suspend #76: stopped 1, commented 2, slots given back' "$TMP/out" \
    || fail "the summary line is wrong: $(cat "$TMP/out")"

  exec 9>&-
  wait "$listener" 2>/dev/null
  rm -f "$hold"
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
  echo "--- start <n> worker goes through the adapter, and git owns the worktree"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  started_once
  assert_started || fail "start did not go through the adapter: $(cat "$TMP/out")"
  assert_wt 61
  hasnt_runner_worktree

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
  echo "--- delivered: resume exit 0, fake paseo recorded send"
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
  [ "$code" = 0 ] || fail "delivered must be exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_w61 :: continue"

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

  echo "--- busy: it is there and did not take the message, exit 3 not 2"
  reset_log
  seed_agent 61 worker
  code="$(run_dispatch env MMW_FAKE_SEND_FAILS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 3 ] || fail "a busy worker must not read as a missing one, got $code: $(cat "$TMP/err")"
  has "paseo :: send :: --no-wait :: agt_61_worker :: continue"

  echo "--- the adapter itself maps busy to exit 3"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_SEND_FAILS=1 run_runner send agt_61_worker continue)"
  [ "$code" = 3 ] || fail "adapter send busy expected 3, got $code: $(cat "$TMP/err")"

  echo "--- no such session: exit 2, nothing is sent"
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" resume 61 continue)"
  [ "$code" = 2 ] || fail "no such session must be exit 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"

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
  [ "$answer" != alive ] || fail "cannot-ask must not be rendered as alive"

  echo "--- unreadable ls output is unknown, not alive"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_PASEO_SCENARIO=ls-garbage run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "liveness expected exit 0 on garbage, got $code: $(cat "$TMP/err")"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "garbage should be unknown, got: $answer"
  [ "$answer" != alive ] || fail "garbage must not be rendered as alive"

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
  [ "$answer" != alive ] || fail "empty status must not be rendered as alive"
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
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
          --cwd "$TMP/repo" --prompt hi --skip-approval)"
  [ "$code" = 0 ] || fail "paseo start expected 0, got $code: $(cat "$TMP/err")"

  echo "--- send three states"
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
  [ "$code" = 0 ] || fail "paseo delivered expected 0, got $code: $(cat "$TMP/err")"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_SEND_FAILS=1 run_runner send agt_61_worker continue)"
  [ "$code" = 3 ] || fail "paseo busy expected 3, got $code: $(cat "$TMP/err")"
  reset_log
  code="$(run_runner send agt_missing continue)"
  [ "$code" = 2 ] || fail "paseo missing expected 2, got $code: $(cat "$TMP/err")"
  hasnt "paseo :: send"

  echo "--- liveness three states"
  reset_log
  seed_agent 61 worker
  code="$(run_runner liveness agt_61_worker)"
  [ "$code" = 0 ] || fail "paseo liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = alive ] || fail "paseo listed should be alive, got: $(cat "$TMP/out")"
  reset_log
  code="$(run_runner liveness agt_missing)"
  [ "$(cat "$TMP/out")" = stopped ] || fail "paseo missing should be stopped, got: $(cat "$TMP/out")"
  reset_log
  seed_agent 61 worker
  code="$(MMW_FAKE_PASEO_SCENARIO=ls-fail run_runner liveness agt_61_worker)"
  [ "$(cat "$TMP/out")" = unknown ] || fail "paseo cannot-ask should be unknown, got: $(cat "$TMP/out")"
  [ "$(cat "$TMP/out")" != alive ] || fail "paseo cannot-ask must not be alive"

  echo "=== herdr adapter"
  RUNNER="$HERDR_RUNNER"

  echo "--- start succeeds, pane exists before agent start"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
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
  run_runner start --host grok --model grok-4.6 --effort high \
    --cwd "$TMP/repo" --prompt hi --title "#61 reviewer" >/dev/null
  [ "$(cat "$TMP/out")" = repo-reviewer ] || fail "the session name should carry the kind: $(cat "$TMP/out")"
  hasnt "herdr :: pane :: split"
  hasnt "herdr :: pane :: rename"
  hasnt "herdr :: pane :: report-metadata"
  hasnt "herdr :: pane :: layout"
  hasnt "herdr :: tab :: close"
  hasnt "herdr :: pane :: close"

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
  [ "$code" != 2 ] || fail "herdr busy must not read as missing"
  reset_log
  code="$(run_runner send agt_missing continue)"
  [ "$code" = 2 ] || fail "herdr missing expected 2, got $code: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: prompt"

  echo "--- liveness three states"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(run_runner liveness agt_w61)"
  [ "$code" = 0 ] || fail "herdr liveness expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = alive ] || fail "herdr listed should be alive, got: $(cat "$TMP/out")"
  reset_log
  code="$(run_runner liveness agt_missing)"
  [ "$(cat "$TMP/out")" = stopped ] || fail "herdr missing should be stopped, got: $(cat "$TMP/out")"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=list-fail run_runner liveness agt_w61)"
  [ "$(cat "$TMP/out")" = unknown ] || fail "herdr cannot-ask should be unknown, got: $(cat "$TMP/out")"
  [ "$(cat "$TMP/out")" != alive ] || fail "herdr cannot-ask must not be alive"

  echo "=== orca adapter"
  RUNNER="$ORCA_RUNNER"

  echo "--- start succeeds, one create, path: selector, no worktree enumeration"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
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
  [ "$code" = 3 ] || fail "orca busy expected 3, got $code: $(cat "$TMP/err")"
  [ "$code" != 0 ] || fail "orca busy must not read as delivered"
  [ "$code" != 2 ] || fail "orca busy must not read as missing"
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
  [ "$(cat "$TMP/out")" != alive ] || fail "orca cannot-ask must not be alive"

  echo "--- a running process whose UI is not idle is still alive"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SCENARIO=wait-busy run_runner liveness term_w61)"
  [ "$(cat "$TMP/out")" = alive ] \
    || fail "running-not-idle should be alive, got: $(cat "$TMP/out")"
  [ "$(cat "$TMP/out")" != stopped ] || fail "UI-not-idle must not read as stopped"

  RUNNER="$PASEO_RUNNER"
}

scenario_herdrworkingsend() {
  local code answer
  RUNNER="$HERDR_RUNNER"
  echo "--- already working: unknown, not delivered, and prompt is not asked"
  reset_log
  seed_herdr_agent agt_w61 working
  code="$(run_runner send agt_w61 continue)"
  answer="$(cat "$TMP/out")"
  [ "$answer" = unknown ] || fail "working send should print unknown, got: $answer"
  [ "$code" != 0 ] || fail "working send must not be delivered (exit 0)"
  hasnt "herdr :: agent :: prompt"
  has "herdr :: agent :: list"

  echo "--- idle still delivers, so the hole is only the working case"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(run_runner send agt_w61 continue)"
  [ "$code" = 0 ] || fail "idle send should deliver, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: prompt"
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
  [ "$answer" != stopped ] || fail "cannot-ask must not be rendered as stopped"
  hasnt "herdr :: agent :: wait"

  RUNNER="$PASEO_RUNNER"
}

scenario_orcasend() {
  local code
  RUNNER="$ORCA_RUNNER"

  echo "--- both stages: delivered, exit 0"
  reset_log
  seed_orca_terminal term_w61
  code="$(run_runner send term_w61 continue)"
  [ "$code" = 0 ] || fail "both stages should deliver, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: send"
  has "--enter"

  echo "--- input_accepted without turn_started: busy, exit 3, not delivered"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=accepted-only run_runner send term_w61 continue)"
  [ "$code" = 3 ] || fail "accepted-only must be busy exit 3, got $code: $(cat "$TMP/err")"
  [ "$code" != 0 ] || fail "accepted-only must not read as delivered"
  has "orca :: terminal :: send"

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
  grep -q "cannot observe the program in it" "$TMP/err" || fail "stderr should say why it is unknown: $(cat "$TMP/err")"
  grep -q "cannot report delivery" "$TMP/err" || fail "stderr should carry Orca's own warning: $(cat "$TMP/err")"
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
  grep -q "ORCA_TERMINAL_HANDLE is not set" "$TMP/err" || fail "the refusal should name the variable: $(cat "$TMP/err")"
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
  grep -q "has no name" "$TMP/err" || fail "the refusal should say the agent has no name: $(cat "$TMP/err")"
  code="$(HERDR_ENV=1 HERDR_PANE_ID=w1:p9 run_runner self)"
  [ "$code" = 1 ] || fail "a pane with no agent should be refused 1, got $code"
  code="$(HERDR_ENV=1 run_runner self)"
  [ "$code" = 1 ] || fail "HERDR_ENV without a pane should be refused 1, got $code"
  code="$(env -u HERDR_ENV bash -c 'cd "$1" && bash "$2" self' _ "$TMP/repo" "$HERDR_RUNNER" 2>/dev/null; echo "$?")"
  [ "$code" = 3 ] || fail "herdr self outside Herdr should be 3, got $code"
  RUNNER="$PASEO_RUNNER"
}

scenario_open() {
  local code pid
  fresh_repo
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  echo "--- open registers the main agent, starts the relay on the spec, and writes spec.opened"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  grep -qx "opened #76: wake-ups go to paseo session agt_main" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  python3 -c 'import json,sys; r=json.load(open(sys.argv[1])); sys.exit(0 if (r["runner"], r["session"]) == ("paseo", "agt_main") else 1)' \
    "$STATE_DIR/recipient.json" || fail "the main agent should be registered: $(cat "$STATE_DIR/recipient.json" 2>&1)"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "a relay should be watching spec 76: $(relay_now)" ;; esac
  posted_events 76 runner session | grep -qx "spec.opened runner=paseo session=agt_main" \
    || fail "#76 should carry spec.opened naming the main agent: $(posted_events 76 runner session)"

  echo "--- the relay open started reads the board on its own"
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

  echo "--- another night in this repository is refused while this one's relay runs"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 77)"
  [ "$code" = 2 ] || fail "open 77 expected 2, got $code"
  grep -q "watching spec #76, and one repository has one relay" "$TMP/err" || fail "the refusal should name the running relay: $(cat "$TMP/err")"
  [ -z "$(posted_events 77)" ] || fail "#77 should carry nothing: $(posted_events 77)"

  echo "--- summary stops the relay open started"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary expected 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "summary should have stopped the relay: $(relay_now)"
  kill -0 "$pid" 2>/dev/null && fail "relay pid $pid should be gone"
  no_relay
}

scenario_openrefused() {
  local code
  fresh_repo
  write_open_batch
  echo "--- a session no adapter can name is refused, and nothing is opened"
  reset_log
  no_relay
  code="$(run_dispatch env -u TERM_PROGRAM -u HERDR_ENV FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code: $(cat "$TMP/err")"
  grep -q "runs in no runner whose adapter can name it (asked: paseo herdr orca)" "$TMP/err" \
    || fail "the refusal should name the runners asked: $(cat "$TMP/err")"
  [ ! -f "$STATE_DIR/recipient.json" ] || fail "nothing should be registered"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"
  hasnt "gh :: issue :: comment :: 76"

  echo "--- an Orca terminal whose handle cannot be read is refused by name"
  reset_log
  no_relay
  code="$(run_dispatch env -u HERDR_ENV TERM_PROGRAM=Orca FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "ORCA_TERMINAL_HANDLE is not set" "$TMP/err" || fail "the refusal should carry the adapter's reason: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"

  echo "--- inside Herdr inside Orca, Herdr names the session: the inner runner is asked first"
  reset_log
  no_relay
  echo '[{"name": "", "agent_status": "idle", "pane_id": "w1:p3"}]' > "$MMW_FAKE_HERDR_STATE/agents.json"
  code="$(run_dispatch env HERDR_ENV=1 HERDR_PANE_ID=w1:p3 ORCA_TERMINAL_HANDLE=term_outer TERM_PROGRAM=Orca \
          FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "an unnamed Herdr agent expected 2, got $code"
  grep -q "has no name" "$TMP/err" || fail "the refusal should be Herdr's, not an Orca registration: $(cat "$TMP/err")"
  [ ! -f "$STATE_DIR/recipient.json" ] || fail "the outer Orca terminal must not be registered"

  echo "--- a session the runner shows stopped is refused"
  reset_log
  no_relay
  code="$(run_dispatch env PASEO_AGENT_ID=agt_gone FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "session agt_gone is stopped" "$TMP/err" || fail "the refusal should say the session is stopped: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"

  echo "--- spec.opened that cannot be written stops the relay open started"
  reset_log
  no_relay
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_COMMENT_FAILS=1 FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "could not write the spec.opened event on #76, so the night is not open and the relay this started was stopped again" "$TMP/err" \
    || fail "the refusal should say the relay was stopped: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "the relay should have been stopped: $(relay_now)"
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
   "comments": [$(ev ticket.passed 90 "ALL MET" --field branch=issue-90),
                $(ev ticket.landed 90 "Landed issue-90 into main")]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  echo "--- open-ticket registers the main agent and starts a relay on that ticket alone"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 90)"
  [ "$code" = 0 ] || fail "open-ticket expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"tickets": [90]}'*) ;; *) fail "a relay should watch #90: $(relay_now)" ;; esac
  hasnt "gh :: issue :: comment"

  echo "--- a ticket of a spec is not what this relay watches, so its start is refused"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start 61 expected 2, got $code"
  grep -q "watches ticket #90, and #61, a ticket of spec #76, is not among them" "$TMP/err" \
    || fail "the refusal should say what the relay watches: $(cat "$TMP/err")"
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
  no_relay
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
  echo "--- the main agent acks the wake it read, by ticket and event; the worker's row stays"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 61 ticket.passed)"
  [ "$code" = 0 ] || fail "ack expected 0, got $code: $(cat "$TMP/err")"
  [ "$(queue_seqs)" = "2 3" ] || fail "only row 1 should be gone: $(queue_seqs)"

  echo "--- the same wake acked again is answered 0: it was acked already"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack '#61' ticket.passed)"
  [ "$code" = 0 ] || fail "a second ack expected 0, got $code: $(cat "$TMP/err")"
  grep -q "acked already" "$TMP/out" || fail "it should say it was acked already: $(cat "$TMP/out")"
  [ "$(queue_seqs)" = "2 3" ] || fail "nothing more should go: $(queue_seqs)"

  echo "--- a wake that was never queued is refused"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 99 ticket.passed)"
  [ "$code" = 2 ] || fail "ack of a wake never queued expected 2, got $code"
  grep -q "no wake \`#99 ticket.passed\` was ever queued" "$TMP/err" || fail "the refusal should name the wake: $(cat "$TMP/err")"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack relay.recovered)"
  [ "$code" = 2 ] || fail "ack of a relay.recovered never announced expected 2, got $code"

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
  grep -q "the night on #76 is not open: no relay is running for o/r" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  never_ran
  assert_no_wt 61
  hasnt "status.py --advance-plan"

  echo "--- start refuses a ticket no relay watches, and starts nothing"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start expected 2, got $code"
  grep -q "nothing would wake anyone when #61's worker reports: no relay is running for o/r" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  never_ran
  assert_no_wt 61

  echo "--- a relay watching another spec does not open this one"
  fake_relay '{"spec": 80}'
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "start expected 2, got $code"
  grep -q "watches spec #80, and #61, a ticket of spec #76, is not among them" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 2 ] || fail "advance expected 2, got $code"
  never_ran
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
  [ "$code" != 0 ] || fail "closed session must not read as delivered"
  [ "$code" != 3 ] || fail "closed session must not read as busy"
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
  echo "--- the worktree basename is issue-<n>, and hook.py governed_ticket sees the ticket"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  dest="$(wt 61)"
  [ "$(basename "$dest")" = issue-61 ] || fail "basename should be issue-61, got $(basename "$dest")"
  hook="$(dirname "$SKILL")/drive-target/scripts/hook.py"
  got="$(cd "$dest" && python3 - "$hook" <<'PY'
import importlib.util, sys
from pathlib import Path
path = Path(sys.argv[1])
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("mmw_hook", path)
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
spec = importlib.util.spec_from_file_location("mmw_hook", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.governed_ticket())
PY
)"
  [ "$got" = None ] || fail "governed_ticket in the repo root should be None, got $got"
}

scenario_worktreeremove() {
  local code
  echo "--- land removes the worktree with git and leaves the branch"
  reset_log
  fresh_repo
  write_landable
  make_branch issue-64 four.txt "from 64"
  seed_workspace 64
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -f "$TMP/repo/four.txt" ] || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_branch 64
  hasnt "orca :: worktree :: rm"
  hasnt "paseo :: workspace :: archive"
  hasnt_runner_worktree
}

scenario_installorca() {
  local code home installer
  installer="$(dirname "$(dirname "$HERE")")/install.sh"
  home="$TMP/install-home"
  rm -rf "$home"
  mkdir -p "$home"

  echo "--- --check with a wrong worktree-base-path is a miss, and does not write"
  reset_log
  python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
(state / "setups.json").write_text(json.dumps([{
    "id": "setup_1",
    "path": "/repo",
    "worktreeBasePath": "~/orca/workspaces",
}]))
(state / "repos.json").write_text(json.dumps([{
    "id": "repo_1",
    "path": "/repo",
    "externalWorktreeVisibility": "show",
}]))
'
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" --check > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
  grep -q "缺    orca worktree-base-path" "$TMP/err" \
    || fail "wrong base path should be 缺: $(cat "$TMP/err")"
  has "orca :: project :: setups"
  has "orca :: repo :: list"
  hasnt "orca :: project :: setup-update"

  echo "--- --check with .worktrees and show does not 缺 those two, and still does not write"
  python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
(state / "setups.json").write_text(json.dumps([{
    "id": "setup_1",
    "path": "/repo",
    "worktreeBasePath": ".worktrees",
}]))
(state / "repos.json").write_text(json.dumps([{
    "id": "repo_1",
    "path": "/repo",
    "externalWorktreeVisibility": "show",
}]))
'
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" --check > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
  if grep -q "orca worktree-base-path" "$TMP/err"; then
    fail "correct base path should not 缺: $(cat "$TMP/err")"
  fi
  if grep -q "orca externalWorktreeVisibility\|orca 没给" "$TMP/err"; then
    fail "show should not be reported: $(cat "$TMP/err")"
  fi
  hasnt "orca :: project :: setup-update"

  echo "--- --check with hidden visibility is a miss"
  python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
(state / "setups.json").write_text(json.dumps([{
    "id": "setup_1",
    "path": "/repo",
    "worktreeBasePath": ".worktrees",
}]))
(state / "repos.json").write_text(json.dumps([{
    "id": "repo_1",
    "path": "/repo",
    "externalWorktreeVisibility": "hide",
}]))
'
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" --check > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
  grep -q "缺    orca externalWorktreeVisibility" "$TMP/err" \
    || fail "hidden visibility should be 缺: $(cat "$TMP/err")"
  hasnt "orca :: project :: setup-update"

  echo "--- install writes worktree-base-path .worktrees via setup-update, never worktree rm"
  python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
(state / "setups.json").write_text(json.dumps([{
    "id": "setup_1",
    "path": "/repo",
}]))
(state / "repos.json").write_text(json.dumps([{
    "id": "repo_1",
    "path": "/repo",
    "externalWorktreeVisibility": "show",
}]))
'
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
  has "orca :: project :: setup-update"
  has ":: --setup :: setup_1"
  has ":: --worktree-base-path :: .worktrees"
  hasnt "orca :: worktree :: rm"
}

run_uses_check() {
  local installer home
  installer="$(dirname "$(dirname "$HERE")")/install.sh"
  home="$TMP/install-home"
  rm -rf "$home"
  mkdir -p "$home"
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" --check > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
}

scenario_usesagree() {
  echo "--- declared flags the binary has: --check is silent about MMW_USES"
  reset_log
  MMW_FAKE_USES=agree run_uses_check
  if grep -E '没查|不一致' "$TMP/err" "$TMP/out"; then
    fail "agree should print neither 没查 nor 不一致: $(cat "$TMP/err") $(cat "$TMP/out")"
  fi
  if grep -q Traceback "$TMP/err"; then
    fail "the check crashed: $(cat "$TMP/err")"
  fi
  has "orca :: agent-context"
  has "herdr :: agent :: start :: --help"
  has "paseo :: send :: --help"
}

scenario_usesmismatch() {
  echo "--- a declared flag the binary lacks: --check names that command and flag"
  reset_log
  MMW_FAKE_USES=mismatch run_uses_check
  grep -q '不一致' "$TMP/err" \
    || fail "mismatch should print 不一致: $(cat "$TMP/err")"
  grep -q '没查' "$TMP/err" \
    && fail "mismatch on a readable page is 不一致, not 没查: $(cat "$TMP/err")"
  grep -qE 'tab create --no-focus' "$TMP/err" \
    || fail "should name tab create --no-focus: $(cat "$TMP/err")"
  grep -qE '没有 no-focus' "$TMP/err" \
    || fail "should say the binary lacks no-focus: $(cat "$TMP/err")"
  grep -qE '^不一致  适配器说它要用 terminal wait --for，二进制的 flags 里没有 for：' "$TMP/err" \
    || fail "should name Orca's terminal wait --for: $(cat "$TMP/err")"
  [ "$(cat "$TMP/code")" = 1 ] || fail "a mismatch must exit 1, got $(cat "$TMP/code")"
}

scenario_usesunreadable() {
  echo "--- herdr subcommand help falls back to the top page: 没查, not 不一致"
  reset_log
  MMW_FAKE_USES=unreadable run_uses_check
  grep -q '没查' "$TMP/err" \
    || fail "fallback help must print 没查: $(cat "$TMP/err")"
  grep -q '不一致' "$TMP/err" \
    && fail "fallback help must not print 不一致: $(cat "$TMP/err")"
  local row
  for row in "tab create" "agent start" "agent prompt" "agent list"; do
    grep -q "^没查    读不到 herdr $row 的帮助页（掉回了顶层用法页" "$TMP/err" \
      || fail "herdr $row should have its own 没查 line: $(cat "$TMP/err")"
  done
  has "herdr :: tab :: create :: --help"
}

# Writes setups.json and repos.json for the fake orca: $1 setups with ids setup_1..,
# path /repo<i>; $2 is the base path to give each ("" leaves the field out); $3 the
# visibility of every repo ("" leaves it out).
seed_orca_projects() {
  MMW_N="$1" MMW_BASE="$2" MMW_VIS="$3" python3 -c '
import json, os
from pathlib import Path
state = Path(os.environ["MMW_FAKE_ORCA_STATE"])
state.mkdir(parents=True, exist_ok=True)
n, base, vis = int(os.environ["MMW_N"]), os.environ["MMW_BASE"], os.environ["MMW_VIS"]
setups, repos = [], []
for i in range(1, n + 1):
    row = {"id": "setup_%d" % i, "path": "/repo%d" % i}
    if base:
        row["worktreeBasePath"] = base
    setups.append(row)
    repo = {"id": "repo_%d" % i, "path": "/repo%d" % i}
    if vis:
        repo["externalWorktreeVisibility"] = vis
    repos.append(repo)
(state / "setups.json").write_text(json.dumps(setups))
(state / "repos.json").write_text(json.dumps(repos))
'
}

run_installer() {
  local installer home
  installer="$(dirname "$(dirname "$HERE")")/install.sh"
  home="$TMP/install-home"
  rm -rf "$home"
  mkdir -p "$home"
  if [ -n "${MMW_TEST_ROOT_COPY:-}" ]; then
    mkdir -p "$home/.mmw"
    printf '%s\n' "$MMW_TEST_ROOT_COPY" > "$home/.mmw/installed-root"
  fi
  : > "$MMW_TEST_LOG"
  (MMW_V2_HOME="$home" bash "$installer" "$@" > "$TMP/out" 2> "$TMP/err"; echo $? > "$TMP/code")
}

scenario_installorcashape() {
  echo "--- install reads every setup out of result.setups and updates each one"
  reset_log
  seed_orca_projects 3 "" show
  run_installer
  [ "$(count_of "orca :: project :: setup-update")" = 3 ] \
    || fail "3 setups in, expected 3 setup-update calls, got $(count_of "orca :: project :: setup-update")"
  echo "--- --check reports every setup with no base path, and writes nothing"
  seed_orca_projects 3 "" show
  run_installer --check
  [ "$(grep -c '^缺    orca worktree-base-path 没设' "$TMP/err")" = 3 ] \
    || fail "3 unset setups should give 3 缺 lines: $(cat "$TMP/err")"
  grep -q "orca project setup-update --setup setup_2 --worktree-base-path .worktrees" "$TMP/err" \
    || fail "the 缺 line should give the command that fixes it: $(cat "$TMP/err")"
  [ "$(cat "$TMP/code")" = 1 ] || fail "--check with a miss must exit 1"
  hasnt "orca :: project :: setup-update"
  echo "--- a base path that resolves to <repo>/.worktrees passes; one elsewhere does not"
  seed_orca_projects 1 /repo1/.worktrees show
  run_installer --check
  if grep -q "orca worktree-base-path" "$TMP/err"; then fail "/repo1/.worktrees is the repo's own .worktrees: $(cat "$TMP/err")"; fi
  seed_orca_projects 1 /elsewhere/.worktrees show
  run_installer --check
  grep -q "^缺    orca worktree-base-path 应为 .worktrees 实为 /elsewhere/.worktrees" "$TMP/err" \
    || fail "/elsewhere/.worktrees is not this repo's .worktrees: $(cat "$TMP/err")"
  echo "--- a setups answer in any other shape is 没查, not a pass"
  seed_orca_projects 2 .worktrees show
  MMW_FAKE_ORCA_SCENARIO=setups-shape run_installer --check
  grep -q "^没查  读不出 orca project setups --json" "$TMP/err" \
    || fail "an unreadable setups list must say 没查: $(cat "$TMP/err")"
  [ "$(cat "$TMP/code")" = 1 ] || fail "没查 must exit 1"
  echo "--- a repo with no visibility of its own is 没查; hide is 缺"
  seed_orca_projects 1 .worktrees ""
  run_installer --check
  grep -q "^没查  orca 没给 /repo1 的 externalWorktreeVisibility" "$TMP/err" \
    || fail "no repo-level visibility must be 没查: $(cat "$TMP/err")"
  seed_orca_projects 1 .worktrees hide
  run_installer --check
  grep -q "^缺    orca externalWorktreeVisibility 应为 show 实为 hide（/repo1）：" "$TMP/err" \
    || fail "hide must be 缺: $(cat "$TMP/err")"
}

# A copy of this mmw-v2 that --check reads through installed-root, so a test can take
# the runners apart without touching the checkout.
root_copy() {
  local copy="$TMP/mmw-copy"
  rm -rf "$copy"
  cp -R "$(dirname "$(dirname "$HERE")")" "$copy"
  printf '%s\n' "$copy"
}

scenario_usesnorunners() {
  local copy
  echo "--- no runners directory: 没查, exit 1"
  reset_log
  seed_orca_projects 1 .worktrees show
  copy="$(root_copy)"
  rm -rf "$copy/skills/dispatch/scripts/runners"
  MMW_TEST_ROOT_COPY="$copy" run_installer --check
  grep -q "^没查    .*runners 下没有适配器，MMW_USES 一条都没核" "$TMP/err" \
    || fail "a missing runners/ must say 没查: $(cat "$TMP/err")"
  [ "$(cat "$TMP/code")" = 1 ] || fail "没查 must exit 1"
  echo "--- a runner with no MMW_USES: 没查 naming that file"
  copy="$(root_copy)"
  sed -i.bak '/^# MMW_USES:/d' "$copy/skills/dispatch/scripts/runners/paseo.sh"
  rm -f "$copy/skills/dispatch/scripts/runners/paseo.sh.bak"
  MMW_TEST_ROOT_COPY="$copy" run_installer --check
  grep -q "^没查    paseo.sh 一条 MMW_USES 声明都没有" "$TMP/err" \
    || fail "an undeclared runner must say 没查: $(cat "$TMP/err")"
  echo "--- a declaration line with no command: 没查"
  copy="$(root_copy)"
  printf '# MMW_USES: --json\n' >> "$copy/skills/dispatch/scripts/runners/paseo.sh"
  MMW_TEST_ROOT_COPY="$copy" run_installer --check
  grep -q "^没查    paseo.sh 有一行 MMW_USES 没有命令名（--json）" "$TMP/err" \
    || fail "a row without a command must say 没查: $(cat "$TMP/err")"
}

scenario_usesorcaunreadable() {
  echo "--- an Orca catalog row whose flags cannot be read: 没查, never 不一致"
  reset_log
  MMW_FAKE_USES=orca-unreadable run_uses_check
  grep -q "^没查    orca agent-context 里 terminal wait 那一行读不出 flags 列表" "$TMP/err" \
    || fail "an unreadable catalog row must say 没查: $(cat "$TMP/err")"
  if grep -q "不一致.*terminal wait" "$TMP/err"; then
    fail "an unreadable row is not a mismatch: $(cat "$TMP/err")"
  fi
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

scenario_startreturnssession() {
  local code
  echo "--- start prints the session id the runner answered with, and nothing else"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = agt_run_1 ] || fail "stdout should be the session id: $(cat "$TMP/out")"
  if grep -q '{' "$TMP/out"; then fail "stdout still carries an object: $(cat "$TMP/out")"; fi
}

scenario_startonce() {
  local code
  echo "--- a start the runner refuses is refused once: one paseo run, no second host"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_FAKE_PASEO_SCENARIO=run-fail bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  started_once
  grep -q "nothing was retried" "$TMP/err" || fail "the refusal should say it was not retried: $(cat "$TMP/err")"
  nothing_printed
  assert_no_wt 61
}

scenario_runneronticket() {
  local code
  echo "--- a start writes the runner and its session id on the ticket"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 2 ] || true
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 verifier)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: comment :: 61 :: --body :: verifier started on paseo: session agt_run_1"
  local want
  want="verifier.started session=agt_run_1 runner=paseo host=claude model=claude-sonnet-5 effort=high grade=verifier worktree=$(cd "$TMP/repo" && git rev-parse --show-toplevel)/.worktrees/issue-61 branch=issue-61"
  [ "$(posted_events 61 session runner host model effort grade worktree branch)" = "$want" ] \
    || fail "the verifier.started event is wrong: $(posted_events 61 session runner host model effort grade worktree branch)"

  echo "--- a worker's start carries its slot"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  posted_events 61 slot | grep -qE "^worker.started slot=[0-9]+$" \
    || fail "the worker.started event should carry the slot: $(posted_events 61 slot)"
  posted_events 61 base | grep -qE "^worker.started base=[0-9a-f]{40}$" \
    || fail "the worker.started event should carry the base commit: $(posted_events 61 base)"
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
  grep -q "#61 keeps its claim: the worker term_7 on orca is live on its events" "$TMP/err" \
    || fail "stderr should say which worker keeps the claim: $(cat "$TMP/err")"

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
  grep -q "could not write the worker.started event on #61" "$TMP/err" \
    || fail "the refusal should say the start was not recorded: $(cat "$TMP/err")"
  grep -q "was stopped again" "$TMP/err" \
    || fail "the refusal should say the session was stopped: $(cat "$TMP/err")"
}

# A passed ticket whose branch is not in this checkout cannot be merged, so it does not
# land, and the ticket it blocks is not started on a base branch that lacks its work.
scenario_mergewithoutbranch() {
  local code
  echo "--- a blocker that passed and could not be merged here does not unblock its ticket"
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
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  never_ran
  assert_no_wt 61
  grep -q "started 0" "$TMP/err" || fail "#61 was started on a base without #60: $(cat "$TMP/err")"
  grep -q "#61 blocked by #60 (passed, not landed)" "$TMP/err" \
    || fail "stderr should say #61 waits on #60's landing: $(cat "$TMP/err")"
  [ -z "$(posted_events 60)" ] || fail "#60 must not be recorded landed: $(posted_events 60)"
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
  grep -q "comment 2" "$TMP/err" || fail "stderr should name the unreadable comment: $(cat "$TMP/err")"
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
  grep -q "#61 keeps its claim: its events cannot be read" "$TMP/err" \
    || fail "the claim should be kept and the reason named: $(cat "$TMP/err")"
  grep -q "#61 its events cannot be read" "$TMP/err" \
    || fail "the frontier should name the unreadable events: $(cat "$TMP/err")"
}

scenario_landarchivesagents() {
  local code left
  echo "--- land takes the ticket's Paseo agents off the list and leaves another ticket's"
  reset_log
  fresh_repo
  write_landable
  make_branch issue-64 four.txt "from 64"
  seed_workspace 64
  seed_agent 64 worker
  seed_agent 64 reviewer
  seed_agent 64 verifier
  seed_agent 99 worker 99
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  [ -f "$TMP/repo/four.txt" ] || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_branch 64
  has "paseo :: archive :: --force :: agt_64_worker"
  has "paseo :: archive :: --force :: agt_64_reviewer"
  has "paseo :: archive :: --force :: agt_64_verifier"
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
  if grep -q "retract #61:" "$TMP/err"; then fail "a refused retract must not reach its summary: $(cat "$TMP/err")"; fi
  hasnt "paseo :: archive"
}

scenario_noadapterwait() {
  local code copy
  echo "--- adapter gone: wait refuses with exit 2, never exit 3"
  reset_log
  printf '%s\n' '[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}]' > "$TMP/tickets.json"
  seed_agent 61 worker
  copy="$(skill_copy_for wait)"
  rm -f "$copy/scripts/runners/paseo.sh"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_WAIT_S=2 MMW_WAIT_BEAT_S=1 \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 2 ] || fail "expected exit 2 with the adapter gone, got $code: $(cat "$TMP/err")"
  grep -q "runners/paseo.sh" "$TMP/err" || fail "stderr should name the missing adapter: $(cat "$TMP/err")"
  if grep -q "^still working:" "$TMP/err"; then fail "a missing adapter must not read as still working: $(cat "$TMP/err")"; fi
}

scenario_unknownnotalive() {
  local code
  echo "--- runner answers unknown: wait retries but says it cannot tell"
  reset_log
  printf '%s\n' '[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}]' > "$TMP/tickets.json"
  seed_agent 61 worker
  set_agent_status agt_61_worker not-a-status
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_WAIT_S=2 MMW_WAIT_BEAT_S=1 \
          bash "$DISPATCH" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 3 ] || fail "unknown still retries: expected exit 3, got $code: $(cat "$TMP/err")"
  grep -q "cannot tell" "$TMP/err" || fail "wait should say it cannot tell: $(cat "$TMP/err")"
  if grep -q "^still working:" "$TMP/err"; then fail "unknown must not read as still working: $(cat "$TMP/err")"; fi

  echo "--- runner answers unknown: retract refuses and archives nothing"
  reset_log
  seed_agent 61 worker
  set_agent_status agt_61_worker not-a-status
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" retract 61)"
  [ "$code" = 2 ] || fail "expected exit 2, got $code: $(cat "$TMP/err")"
  grep -q "cannot tell" "$TMP/err" || fail "retract should say it cannot tell: $(cat "$TMP/err")"
  if grep -q "still has a live agent" "$TMP/err"; then fail "unknown must not read as a live agent: $(cat "$TMP/err")"; fi
  hasnt "paseo :: archive"
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

  echo "--- send on a list in the wrong shape is unknown (4), never 'no such session' (2)"
  reset_log
  seed_herdr_agent agt_w61 idle
  code="$(MMW_FAKE_HERDR_SCENARIO=list-shape run_runner send agt_w61 hi)"
  [ "$code" = 4 ] || fail "send on an unreadable list expected 4, got $code: $(cat "$TMP/err")"

  echo "--- and a list that is not JSON at all is unknown too"
  reset_log
  seed_herdr_agent agt_w61 idle
  MMW_FAKE_HERDR_SCENARIO=list-garbage run_runner liveness agt_w61 >/dev/null
  [ "$(cat "$TMP/out")" = unknown ] || fail "a garbage list must be unknown, got: $(cat "$TMP/out")"
}

scenario_herdrnoeffort() {
  local code
  RUNNER="$HERDR_RUNNER"
  echo "--- an empty effort starts grok without --reasoning-effort, never with a literal dash"
  reset_log
  fresh_repo
  code="$(run_runner start --host grok --model "grok 4.6" --effort "—" --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  has "herdr :: agent :: start"
  if grep "herdr :: agent :: start" "$MMW_TEST_LOG" | grep -q -- "--reasoning-effort"; then
    fail "empty effort must drop the flag: $(grep 'herdr :: agent :: start' "$MMW_TEST_LOG")"
  fi
  grep "herdr :: agent :: start" "$MMW_TEST_LOG" | grep -qF ":: grok 4.6 ::" \
    || fail "the model must still be passed: $(grep 'herdr :: agent :: start' "$MMW_TEST_LOG")"

  echo "--- a host with no launch block refuses instead of starting without a model"
  reset_log
  fresh_repo
  code="$(run_runner start --host nosuchhost --model m --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "an unknown host expected refusal 1, got $code"
  grep -q "cannot build the launch line" "$TMP/err" || fail "stderr should say why: $(cat "$TMP/err")"
  hasnt "herdr :: agent :: start"
}

scenario_herdrstartloud() {
  local code
  RUNNER="$HERDR_RUNNER"
  echo "--- a refused start says what failed, on stderr"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_HERDR_SCENARIO=tab-fail run_runner start --host grok --model "grok 4.6" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected 1, got $code"
  grep -q "could not open a tab" "$TMP/err" || fail "stderr should name the failed tab create: $(cat "$TMP/err")"
  code="$(MMW_FAKE_HERDR_SCENARIO=start-fail run_runner start --host grok --model "grok 4.6" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected 1, got $code"
  grep -q "agent start refused" "$TMP/err" || fail "stderr should name the refused agent start: $(cat "$TMP/err")"
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

scenario_orcanoorphan() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a start whose first prompt is not taken closes its terminal and says so"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SEND=accepted-only run_runner start --host grok --model "grok 4.6" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: close"
  grep -q "was closed" "$TMP/err" || fail "stderr should say the terminal was closed: $(cat "$TMP/err")"
}

scenario_orcanohosts() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a host with no launch block refuses before any terminal is created"
  reset_log
  fresh_repo
  code="$(run_runner start --host pi --model m --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "pi has no launch block, expected refusal 1, got $code"
  grep -q "cannot build the launch line" "$TMP/err" || fail "stderr should say why: $(cat "$TMP/err")"
  hasnt "orca :: terminal :: create"
}

ALL="check advance advanceconflict advancedirty land start-worker start-reviewer start-verifier retract resume wait reverify summary release releaseother releaselive releasestanding frontierwhy instancegate countfail stopproduct suspend suspendbusy status runnerstart runnersend runnerliveness runnerparity herdrworkingsend herdrliveness orcasend orcaclosed worktreegit worktreegoverned worktreeremove installorca usesagree usesmismatch usesunreadable paseostartdir landarchivesagents noadapterretract noadapterwait unknownnotalive herdrunreadablelist herdrnoeffort herdrstartloud orcatruncated orcanotconnected orcanoorphan orcanohosts installorcashape usesnorunners usesorcaunreadable startreturnssession startonce runneronticket runnerstop orcadoubledispatch unreadableevents startunrecorded mergewithoutbranch retractunreadable open openrefused openticket ack unopened runnerself orcaunobserved"

# One list of scenario names, ALL; a name on the command line is accepted when it is in it.
case " $ALL all " in
  *" ${1:-} "*) ;;
  *)
    echo "usage: test_dispatch.sh $(echo "$ALL" | tr ' ' '|')|all" >&2
    exit 2 ;;
esac
if [ "$1" = all ]; then wanted="$ALL"; else wanted="$1"; fi

banner_for() {
  case "$1" in
    check) echo DISPATCH-CHECK-OK ;;
    advance) echo DISPATCH-ADVANCE-OK ;;
    advanceconflict) echo DISPATCH-ADVANCE-CONFLICT-OK ;;
    advancedirty) echo DISPATCH-ADVANCE-DIRTY-OK ;;
    land) echo DISPATCH-LAND-OK ;;
    start-worker) echo DISPATCH-START-WORKER-OK ;;
    start-reviewer) echo DISPATCH-START-REVIEWER-OK ;;
    start-verifier) echo DISPATCH-START-VERIFIER-OK ;;
    retract) echo DISPATCH-RETRACT-OK ;;
    resume) echo DISPATCH-RESUME-OK ;;
    wait) echo DISPATCH-WAIT-OK ;;
    reverify) echo DISPATCH-REVERIFY-OK ;;
    summary) echo DISPATCH-SUMMARY-OK ;;
    release) echo DISPATCH-RELEASE-OK ;;
    releaseother) echo DISPATCH-RELEASE-OTHER-OK ;;
    releaselive) echo RELEASE-LIVE-OK ;;
    releasestanding) echo RELEASE-STANDING-OK ;;
    frontierwhy) echo DISPATCH-FRONTIER-WHY-OK ;;
    instancegate) echo DISPATCH-INSTANCE-GATE-OK ;;
    countfail) echo DISPATCH-COUNT-FAIL-OK ;;
    stopproduct) echo STOP-PRODUCT-OK ;;
    suspend) echo SUSPEND-OK ;;
    suspendbusy) echo SUSPEND-BUSY-OK ;;
    status) echo DISPATCH-STATUS-OK ;;
    runnerstart) echo RUNNER-START-OK ;;
    noadapterretract) echo NO-ADAPTER-RETRACT-OK ;;
    noadapterwait) echo NO-ADAPTER-WAIT-OK ;;
    unknownnotalive) echo UNKNOWN-NOT-ALIVE-OK ;;
    herdrunreadablelist) echo HERDR-UNREADABLE-LIST-OK ;;
    herdrnoeffort) echo HERDR-NO-EFFORT-OK ;;
    herdrstartloud) echo HERDR-START-LOUD-OK ;;
    orcatruncated) echo ORCA-TRUNCATED-OK ;;
    orcanotconnected) echo ORCA-NOT-CONNECTED-OK ;;
    orcanoorphan) echo ORCA-NO-ORPHAN-OK ;;
    orcanohosts) echo ORCA-NO-HOSTS-OK ;;
    installorcashape) echo INSTALL-ORCA-SHAPE-OK ;;
    usesnorunners) echo USES-NO-RUNNERS-OK ;;
    usesorcaunreadable) echo USES-ORCA-UNREADABLE-OK ;;
    startreturnssession) echo START-RETURNS-SESSION-OK ;;
    startonce) echo START-ONCE-OK ;;
    runneronticket) echo RUNNER-ON-TICKET-OK ;;
    runnerstop) echo RUNNER-STOP-OK ;;
    runnersend) echo RUNNER-SEND-OK ;;
    runnerliveness) echo RUNNER-LIVENESS-OK ;;
    runnerparity) echo RUNNER-PARITY-OK ;;
    herdrworkingsend) echo HERDR-WORKING-SEND-OK ;;
    herdrliveness) echo HERDR-LIVENESS-OK ;;
    orcasend) echo ORCA-SEND-OK ;;
    orcaclosed) echo ORCA-CLOSED-OK ;;
    worktreegit) echo WORKTREE-GIT-OK ;;
    worktreegoverned) echo WORKTREE-GOVERNED-OK ;;
    worktreeremove) echo WORKTREE-REMOVE-OK ;;
    installorca) echo INSTALL-ORCA-OK ;;
    usesagree) echo USES-AGREE-OK ;;
    usesmismatch) echo USES-MISMATCH-OK ;;
    usesunreadable) echo USES-UNREADABLE-OK ;;
    paseostartdir) echo PASEO-START-DIR-OK ;;
    landarchivesagents) echo LAND-ARCHIVES-AGENTS-OK ;;
    orcadoubledispatch) echo ORCA-DOUBLE-DISPATCH-OK ;;
    unreadableevents) echo UNREADABLE-EVENTS-OK ;;
    startunrecorded) echo START-UNRECORDED-OK ;;
    mergewithoutbranch) echo MERGE-WITHOUT-BRANCH-OK ;;
    retractunreadable) echo RETRACT-UNREADABLE-OK ;;
    open) echo OPEN-OK ;;
    openrefused) echo OPEN-REFUSED-OK ;;
    openticket) echo OPEN-TICKET-OK ;;
    ack) echo ACK-OK ;;
    unopened) echo UNOPENED-OK ;;
    runnerself) echo RUNNER-SELF-OK ;;
    orcaunobserved) echo ORCA-UNOBSERVED-OK ;;
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
