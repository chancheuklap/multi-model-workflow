#!/usr/bin/env bash
#
# Tests for dispatch.sh. One scenario per run:
#
#   bash mmw-v2/tests/dispatch/test_dispatch.sh check|advance|advanceconflict|advancedirty
#   bash mmw-v2/tests/dispatch/test_dispatch.sh integrateuptodate|integrateclean|integratenamestickets
#   bash mmw-v2/tests/dispatch/test_dispatch.sh integrateconflict|integratedirty
#   bash mmw-v2/tests/dispatch/test_dispatch.sh start-worker|start-reviewer|start-verifier|retract
#   bash mmw-v2/tests/dispatch/test_dispatch.sh resume|wait|reverify|summary
#   bash mmw-v2/tests/dispatch/test_dispatch.sh release|releaseother|releaselive|releasestanding|frontierwhy
#   bash mmw-v2/tests/dispatch/test_dispatch.sh slotatclaim|route|specfield|stopproduct|suspend|suspendbusy|status
#   bash mmw-v2/tests/dispatch/test_dispatch.sh runnerstart|runnersend|runnerliveness
#   bash mmw-v2/tests/dispatch/test_dispatch.sh runnerparity|herdrworkingsend|herdrliveness
#   bash mmw-v2/tests/dispatch/test_dispatch.sh orcasend|orcaclosed
#   bash mmw-v2/tests/dispatch/test_dispatch.sh worktreegit|worktreegoverned|worktreeremove|installorca
#   bash mmw-v2/tests/dispatch/test_dispatch.sh boardregisters|boardsameport|boardopenstab|boardprintsurl
#   bash mmw-v2/tests/dispatch/test_dispatch.sh installboardagent|installcheckboardagent
#   bash mmw-v2/tests/dispatch/test_dispatch.sh usesagree|usesmismatch|usesunreadable
#   bash mmw-v2/tests/dispatch/test_dispatch.sh paseostartdir|landarchivesagents
#   bash mmw-v2/tests/dispatch/test_dispatch.sh orcadoubledispatch|unreadableevents|startunrecorded
#   bash mmw-v2/tests/dispatch/test_dispatch.sh mergewithoutbranch|retractunreadable
#   bash mmw-v2/tests/dispatch/test_dispatch.sh open|openrefused|openticket|ack|unopened|runnerself|orcaunobserved|adopt
#   bash mmw-v2/tests/dispatch/test_dispatch.sh keepunfinished|advancerefused|catalogbyrunner
#   bash mmw-v2/tests/dispatch/test_dispatch.sh startunlandedblocker
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
INSTALLER="$(dirname "$(dirname "$HERE")")/install.sh"

rc=0
fail() { echo "  FAILED: $1" >&2; rc=1; }

TMP="$(mktemp -d)"
# A relay left running would go on polling a board that is gone, through whatever `gh`
# is next on PATH.
trap 'stop_test_boards; no_relay; rm -rf "$TMP"' EXIT
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
    ("provider", "ls"): """Usage: paseo provider ls [options]

Options:
  --json                Output in JSON format
""",
    ("provider", "models"): """Usage: paseo provider models [options] <provider>

Options:
  --json                Output in JSON format
""",
    ("provider", "diagnostic"): """Usage: paseo provider diagnostic [options] <provider>

Options:
  --json                Output in JSON format
""",
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
        "commandCount": 8,
        "commands": [
            {"command": "tab create",
             "flags": ["help", "json", "url", "worktree"]},
            {"command": "terminal create",
             "flags": ["help", "json", "worktree", "command", "title"]},
            {"command": "terminal send",
             "flags": ["help", "json", "terminal", "text", "enter",
                       "wait-submit"]},
            {"command": "terminal wait", "flags": wait_flags},
            {"command": "terminal read",
             "flags": ["help", "json", "terminal", "cursor", "limit", "screen"]},
            {"command": "terminal list",
             "flags": ["help", "json", "worktree"]},
            {"command": "terminal close",
             "flags": ["help", "json", "terminal"]},
            {"command": "worktree set",
             "flags": ["help", "worktree", "issue"]},
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

if args[:2] == ["worktree", "set"]:
    if scenario == "worktree-set-fail":
        print(json.dumps({"ok": False, "error": {"code": "link_failed"}}))
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
  "api graphql "*)
    # The tree of issues under `root=<n>`, the way `tree.py` asks for it: any number that
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
print(next((t for t in rows if t.get("number") == want), {}).get("state", "OPEN"))
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
  "label create "*)
    # FAKE_GH_LABEL_EXISTS: the repository already has it, which `gh` reports as a failure.
    if [ -n "${FAKE_GH_LABEL_EXISTS:-}" ]; then
      echo "label with name \"$3\" already exists; use \`--force\` to update its color and description" >&2
      exit 1
    fi
    echo "✓ Label \"$3\" created" ;;
  "issue close "*)
    # FAKE_GH_CLOSE_FAILS: the tracker refuses the close, the way a network drop does.
    [ -z "${FAKE_GH_CLOSE_FAILS:-}" ] || { echo "HTTP 502" >&2; exit 1; }
    echo "✓ Closed issue #$3" ;;
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
state = os.environ.get("MMW_FAKE_PASEO_STATE")
found = next((t for t in rows if t.get("number") == want), {})
store = Path(state or ".") / "gh-comments.json"
posted = json.loads(store.read_text()).get(str(want), []) if state and store.is_file() else []
reads = Path(state or ".") / "comment_reads"
count = int(reads.read_text()) + 1 if reads.is_file() else 1
reads.write_text(str(count))
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
# Tonight's runner is pinned: the session running this suite may itself sit in Orca,
# Herdr or tmux, and runtime detection would pick that runner.
export MMW_RUNNER=paseo
export MMW_HOST_CATALOG="$HERE/catalog.json"
export MMW_LEASE_PORT_STRIDE=20
# The block is probed once here and not held, so a second run of this suite on the same
# machine (another checkout, another agent) that starts from the same first free block
# puts its real listeners (`stopproduct`, `suspendbusy`) on this run's slot ports, and a
# `lease.py release` here refuses a slot for a listener that is not this run's. Each run
# starts its search at its own offset, so two runs at once almost never share a block.
export MMW_LEASE_PORT_BASE="$(python3 -c '
import os, random, socket
stride = int(os.environ.get("MMW_LEASE_PORT_STRIDE", "20"))
slots = int(os.environ.get("MMW_LEASE_SLOTS", "8"))
need = stride * slots
start = 22000 + random.randrange(0, (45000 - 22000) // need) * need
for base in list(range(start, 48000 - need, need)) + list(range(22000, start, need)):
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
# The models.json every scenario starts from. It is this suite's own fixture, not
# hosts.json's defaults: what a fresh machine is given can change without changing what
# the scenarios exercise (a Cursor junior row with its effort inside the model id, a Grok
# senior row at xhigh).
cat > "$MMW_HOME/models.json" <<'JSON'
{"version":1,"runner":"orca","rows":{"junior-worker":{"host":"cursor","model":"grok 4.6","effort":"high"},"senior-worker":{"host":"grok","model":"grok 4.6","effort":"xhigh"},"reviewer":{"host":"claude","model":"opus 5","effort":"high"},"verifier":{"host":"claude","model":"sonnet 5","effort":"high"},"advisor":{"host":"claude","model":"fable 5.1","effort":"medium"}}}
JSON

git init -q --bare -b main "$TMP/origin.git"
git init -q -b main "$TMP/repo"
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

# The main agent of the open watch <key> (`spec:N` or `tickets:N`), "runner session";
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

BOARD_TEST_PORTS=""
stop_test_boards() {
  [ -n "${BOARD_TEST_PORTS:-}" ] || return 0
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
  stop_test_boards
  BOARD_TEST_PORTS=""
  rm -f "$MMW_HOME/boards.json" "$MMW_HOME/boards.json.lock" "$MMW_HOME"/board-*.log
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

JUNIOR_HOST=cursor
JUNIOR_MODEL=grok-4.6
SENIOR_MODEL=grok-4.6
one_line_reason() {
  [ "$(wc -l < "$TMP/err" | tr -d ' ')" = 1 ] \
    || fail "the reason should be one line: $(cat "$TMP/err")"
}

fresh_repo() {
  rm -rf "$TMP/repo" "$TMP/origin.git" "$TMP/other-clone"
  git init -q --bare -b main "$TMP/origin.git"
  git init -q -b main "$TMP/repo"
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
    --field host=grok --field model=grok-4.6 --field effort=high \
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
     "$(dirname "$SKILL")/verify-ticket/scripts/tree.py" \
     "$TMP/fake/skills/verify-ticket/scripts/"
  printf '#!/usr/bin/env bash\nexit %s\n' "${2:-0}" > "$TMP/fake/install.sh"
  chmod +x "$TMP/fake/install.sh"
  printf '%s\n' "$copy"
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
catalog["claude"] = [o for o in catalog["claude"] if o["id"] != "claude-sonnet-5"]
json.dump(catalog, open(sys.argv[2], "w"))
' "$HERE/catalog.json" "$TMP/catalog-no-sonnet.json"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_RUNNER=orca \
          MMW_HOST_CATALOG="$TMP/catalog-no-sonnet.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "a verifier row that does not resolve is exit 2, got $code: $(cat "$TMP/err")"
  grep -q "the verifier row of .* does not resolve on orca: 'sonnet 5'" "$TMP/err" \
    || fail "the refusal should name the row, the runner and the resolver's reason: $(cat "$TMP/err")"
  hasnt "paseo :: provider"

  echo "--- a runner this skill has no adapter for is refused before the night"
  reset_log
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_RUNNER=tmux \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "a runner with no adapter is exit 2, got $code: $(cat "$TMP/err")"
  grep -q "tonight's runner is tmux, and this skill has no adapter for it" "$TMP/err" \
    || fail "the refusal should name the runner: $(cat "$TMP/err")"
}

# A row resolves against the catalog of the runner that starts the session: Orca runs the
# host's CLI, which takes the CLI's own model id (Cursor's carries its effort,
# `cursor-grok-4.6-high`), and Paseo takes Paseo's (`grok-4.6`). The fixture catalog holds
# both shapes, so only the runner decides which one comes out.
scenario_catalogbyrunner() {
  local code
  echo "--- on Orca the junior worker starts with the CLI's own model id"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_RUNNER=orca bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "orca :: terminal :: create"
  grep -F "orca :: terminal :: create" "$MMW_TEST_LOG" | grep -qF -- "--model cursor-grok-4.6-high" \
    || fail "the launch line should carry the CLI's id: $(grep -F 'orca :: terminal :: create' "$MMW_TEST_LOG")"
  posted_events 61 model | grep -qx "worker.started model=cursor-grok-4.6-high" \
    || fail "the started event should record the id the session got: $(posted_events 61 model)"

  echo "--- on Paseo the same row starts with Paseo's model id"
  reset_log
  fresh_repo
  code="$(run_dispatch env MMW_RUNNER=paseo bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  has "paseo :: run"
  [ "$(out_json provider)" = "$JUNIOR_HOST/grok-4.6" ] || fail "provider: $(out_json provider)"
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
  grep -q "provider initialization failed" "$TMP/err" \
    || fail "stderr should carry the runner's own reason: $(cat "$TMP/err")"
  grep -q "did not start .* for #63 worker" "$TMP/err" \
    || fail "stderr should name the ticket: $(cat "$TMP/err")"
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
   "parent": null, "comments": ["voided: superseded by the spec"]},
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

  echo "--- both are events on the ticket, the landing recorded last, once the workspace and its slot are gone"
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
  ! git -C "$TMP/origin.git" cat-file -e main:eight.txt 2>/dev/null \
    || fail "a ticket that did not close ALL MET must not be merged"
  assert_wt 68
  hasnt_runner_worktree
  grep -q "no base branch in its events; not archiving" "$TMP/err" \
    || fail "the refusal should name the missing landing authority: $(cat "$TMP/err")"
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
  assert_no_retired_base_config "$TMP/repo" 63 advance

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
  setup_bounced_conflict
  local code
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  echo "--- a conflict is aborted in the merge worktree and handed to triage"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  posted_events 61 reason | grep -qx "ticket.bounced reason=conflict" \
    || fail "the conflict was not bounced"
  ! git -C "$TMP/repo/.worktrees/merge-main" rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 \
    || fail "the merge worktree kept MERGE_HEAD"
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

assert_no_retired_base_config() {
  local root="$1" number="$2" action="$3"
  [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base")" ] \
    || fail "$action wrote retired branch.issue-$number.mmw-base"
  [ -z "$(git -C "$root" config --get "branch.issue-$number.mmw-base-branch")" ] \
    || fail "$action wrote retired branch.issue-$number.mmw-base-branch"
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
  grep -q "already current with origin/main" "$TMP/out" \
    || fail "the no-op result was not named: $(cat "$TMP/out")"
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
  [ "$(cat "$TMP/out")" = "integrated origin/main into issue-61; incoming tickets: #62 #63" ] \
    || fail "clean result did not name exactly #62 and #63: $(cat "$TMP/out")"
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
  ! sed -n '/conflicted files:/,/^$/p' "$TMP/err" | grep -q "clean.txt" \
    || fail "the report listed a cleanly merged file as conflicted: $(cat "$TMP/err")"
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
  grep -q "uncommitted tracked changes" "$TMP/err" \
    || fail "the dirty refusal was not named: $(cat "$TMP/err")"
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
    *"--sub-issue fault"*) ;;
    *) fail "the pipeline-fault sentence is missing from the worker prompt" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"A fault in the pipeline itself is reported, not worked around: verify-ticket.py <n> --sub-issue fault <file>, then stop (rule 5 of that section)."*) ;;
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

  echo "--- a worker start takes no slot: writing code needs none, even with every slot claimed"
  reset_log
  fresh_repo
  seed_workspace 99
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-99" >/dev/null
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "a full machine must not stop a worker from starting, got $code: $(cat "$TMP/err")"
  started_once
  assert_wt 61
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "start took a slot: $(python3 "$LEASE_PY" list)"
  posted_events 61 slot port_base | grep -qx "worker.started slot=None port_base=None" \
    || fail "worker.started should carry no slot: $(posted_events 61 slot port_base)"
  python3 "$LEASE_PY" release "$TMP/repo/.worktrees/issue-99" >/dev/null

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
  grep -q "agt_61_worker on paseo is live on its events and could not be stopped" "$TMP/err" \
    || fail "the refusal should name the live worker: $(cat "$TMP/err")"
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
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "start should hold no slot, it holds $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  # The worker's first run of a criterion that needs the product claims it.
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$(wt 61)" >/dev/null
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

  echo "--- the freed slot is the one the next ticket's first product run takes"
  : > "$MMW_TEST_LOG"
  code="$(run_dispatch env MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" start 62 worker)"
  [ "$code" = 0 ] || fail "start after retract expected exit 0, got $code: $(cat "$TMP/err")"
  assert_wt 62
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$(wt 62)" >/dev/null \
    || fail "the slot retract gave back should be free for the next claim: $(python3 "$LEASE_PY" list)"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "the next claim should take the freed slot, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

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
  MMW_LEASE_SLOTS=1 python3 "$LEASE_PY" claim "$(wt 61)" >/dev/null
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
    || fail "the slot should be given back, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees"); retract said: $(cat "$TMP/err")"
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
  case "$(out_json initialPrompt)" in
    "Use the code-review skill to review ticket #61 from base commit $base."*) ;;
    *) fail "the reviewer dispatch line did not carry the recorded base commit: $(out_json initialPrompt)" ;;
  esac
  case "$(out_json initialPrompt)" in
    *"You are operating autonomously"*) ;;
    *) fail "the autonomous sentence is missing from the reviewer prompt" ;;
  esac
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
  case "$(out_json initialPrompt)" in
    "Use the code-review skill to review ticket #61 from base commit $integrated."*) ;;
    *) fail "reviewer did not use the integrated origin/main tip: $(out_json initialPrompt)" ;;
  esac
}

scenario_reviewerbasefromstarted() {
  scenario_start_reviewer
}

scenario_nobaseconfig() {
  local code tree
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "worker start expected 0, got $code: $(cat "$TMP/err")"
  assert_no_retired_base_config "$TMP/repo" 61 start
  : > "$MMW_TEST_LOG"
  rm -f "$MMW_FAKE_PASEO_STATE/runs.jsonl"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer)"
  [ "$code" = 0 ] || fail "reviewer without base config expected 0, got $code: $(cat "$TMP/err")"
  started_once

  fresh_repo
  reset_log
  no_relay
  seed_main_agent agt_self
  self_picked_worktree
  tree="$(wt 61)"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61 --into main) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 0 ] || fail "adopt expected 0, got $code: $(cat "$TMP/err")"
  assert_no_retired_base_config "$TMP/repo" 61 adopt
  no_relay
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
  python3 -c '
import json, sys
from pathlib import Path
obj = json.loads(Path(sys.argv[1]).read_text().splitlines()[-1])
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
  grep -q "do not send it again" "$TMP/err" \
    || fail "the caller must be told not to send it again: $(cat "$TMP/err")"
  posted_events 61 session | grep -q "^worker.resumed session=term_w61" \
    || fail "the hand-over is recorded as worker.resumed: $(posted_events 61 session)"
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
  grep -q "no result of its reviewer yet" "$TMP/err" \
    || fail "stderr should say no result is there yet: $(cat "$TMP/err")"
  grep -q "end your turn" "$TMP/err" \
    || fail "stderr should send the caller to end its turn, not to wait again: $(cat "$TMP/err")"
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
  grep -q "no reviewer.started event" "$TMP/err" \
    || fail "stderr should say there is no session on the ticket: $(cat "$TMP/err")"
}

scenario_reverify() {
  local copy code
  copy="$(skill_copy_for reverify)"
  mkdir -p "$TMP/fake/skills/verify-ticket/scripts"
  # The real run posts its own `ticket.checked` on the ticket; this one posts the same
  # event straight into the fake tracker. FAKE_VERIFY_WAIT: it waited for a product slot
  # and none came free (exit 3), and posted nothing.
  cat > "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py" <<'PY'
#!/usr/bin/env python3
import json, os, subprocess, sys
from pathlib import Path
log = os.environ["MMW_TEST_LOG"]
with open(log, "a", encoding="utf-8") as fh:
    fh.write("verify-ticket" + "".join(" :: " + a for a in sys.argv[1:]) + "\n")
number = sys.argv[1]
if number in os.environ.get("FAKE_VERIFY_WAIT", "").split(","):
    sys.exit(3)
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
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_FAIL=62 \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 1 ] || fail "expected exit 1, got $code: $(cat "$TMP/err")"
  echo "--- each run is the main agent's reverify, and a green one writes nothing but its own run"
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

  echo "--- a run that waited for a slot and got none is not a red ticket"
  reset_log
  post_ev 61 ticket.landed --ticket 61 --line "Landed issue-61 into main"
  post_ev 62 ticket.landed --ticket 62 --line "Landed issue-62 into main"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_VERIFY_WAIT=61 \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 2 ] || fail "expected exit 2 when a run waited and could not start, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: reopen"
  grep -q "#61 could not be re-run on .*, so nothing was judged" "$TMP/err" \
    || fail "the run that could not start should be named: $(cat "$TMP/err")"

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
   "comments": [$(ev ticket.passed 61 "ALL MET" --field branch=issue-61 --field into=main),
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
  git -C "$TMP/repo" worktree add -q --detach "$TMP/linked-summary" HEAD
  reset_log
  code="$( (cd "$TMP/linked-summary" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" summary 76) \
          > "$TMP/out" 2> "$TMP/err"; echo "$?")"
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
  python3 "$LEASE_PY" claim "$(wt 63)" >/dev/null
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" FAKE_GH_LOGIN=mmw-bot \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "exit $code, not 0: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 63 :: --remove-assignee :: @me"
  echo "--- the release ends the lost worker's work, so the slot its worktree held goes back with the claim"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "#63's slot outlived its released claim: $(python3 "$LEASE_PY" list)"
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

scenario_slotatclaim() {
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  echo "--- a product capped at one run still has every frontier ticket started: code takes no slot"
  reset_log
  fresh_repo
  make_branch issue-61 one.txt "from 61"
  make_branch issue-62 two.txt "from 62"
  write_batch
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
  git -C "$TMP/repo" show origin/main:one.txt >/dev/null 2>&1 || fail "issue-61 was not merged"
  git -C "$TMP/repo" show origin/main:two.txt >/dev/null 2>&1 || fail "issue-62 was not merged"

  echo "--- a merged ticket's slot is given back before its worktree is removed: held until landing"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "issue-62's lease should be gone after archive, count is $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  assert_no_wt 62
  assert_no_branch 62
  hasnt_runner_worktree

  echo "--- the frontier ticket starts although the product's one slot is held, and takes none"
  assert_wt 63
  grep -q "started 1" "$TMP/err" || fail "the frontier ticket was not started: $(cat "$TMP/err")"
  ! grep -q "held" "$TMP/err" || fail "advance still holds tickets back: $(cat "$TMP/err")"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 1 ] \
    || fail "the start took a slot: $(python3 "$LEASE_PY" list)"

  echo "--- its first run that needs the product is the one told to wait: lease.py answers 4, full"
  cp "$TMP/repo/.mmw/target.json" "$(wt 63)/.mmw/target.json" 2>/dev/null \
    || { mkdir -p "$(wt 63)/.mmw" && cp "$TMP/repo/.mmw/target.json" "$(wt 63)/.mmw/target.json"; }
  local answer
  answer="$(python3 "$LEASE_PY" claim "$(wt 63)")"
  code=$?
  [ "$code" = 4 ] || fail "the claim past instance.max should exit 4, got $code: $answer"
  printf '%s' "$answer" | python3 -c '
import json, sys
got = json.load(sys.stdin)
assert got["claimed"] is False and got["reason"] == "product-full" and got["limit"] == 1, got
assert [h.endswith("issue-99") for h in got["holders"]] == [True], got
' || fail "the full answer should name the limit and who holds it: $answer"

  rm -f "$TMP/repo/.mmw/target.json"
  python3 "$LEASE_PY" release "$TMP/repo/.worktrees/issue-99" >/dev/null
}

# #61 is a ticket under spec #76, and its events carry a child.opened for each of
# #90–#93 naming spec #76. #92 has already been moved under the spec, the way a route
# cut short after its move leaves it, and #76 itself sits under map #18 — so a route
# that read the spec off the tree would move #92 under the map. #80 is a ticket already
# under the spec; #95 is an issue under #61 that no event of #61 names.
write_route_batch() {
  cat > "$TMP/tickets.json" <<JSON
[
  {"number": 18, "state": "OPEN", "labels": ["mmw:map"], "parent": null},
  {"number": 76, "state": "OPEN", "labels": ["mmw:spec"], "parent": {"number": 18}},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "mmw:ticket"], "parent": {"number": 76},
   "comments": [$(ev child.opened 61 "Opened #90 (finding)" --spec 76 --field child=90 --field kind=finding),
                $(ev child.opened 61 "Opened #91 (finding)" --spec 76 --field child=91 --field kind=finding),
                $(ev child.opened 61 "Opened #92 (finding)" --spec 76 --field child=92 --field kind=finding),
                $(ev child.opened 61 "Opened #93 (deferred)" --spec 76 --field child=93 --field kind=deferred)]},
  {"number": 80, "state": "OPEN", "labels": ["ready-for-agent"], "parent": {"number": 76}},
  {"number": 90, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 91, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 92, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 76}},
  {"number": 93, "state": "OPEN", "labels": ["needs-triage", "mmw:child"], "parent": {"number": 61}},
  {"number": 95, "state": "OPEN", "labels": ["needs-triage"], "parent": {"number": 61}}
]
JSON
}

route_in() { run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" "$@"; }

scenario_route() {
  local code
  reset_log
  fresh_repo
  write_route_batch
  echo "--- fixed: the child is closed as completed and child.closed goes on its ticket"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 fixed)"
  [ "$code" = 0 ] || fail "route fixed expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: close :: 90 :: --reason :: completed"

  echo "--- stale: closed as not planned"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 91 stale)"
  [ "$code" = 0 ] || fail "route stale expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: close :: 91 :: --reason :: not planned"

  echo "--- became-ticket as itself: relabelled mmw:ticket, left open, under the spec its child.opened names — never the map the tree would give"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 92 became-ticket 92)"
  [ "$code" = 0 ] || fail "route became-ticket expected exit 0, got $code: $(cat "$TMP/err")"
  has "gh :: label :: create :: mmw:ticket"
  has "gh :: issue :: edit :: 92 :: --add-label :: mmw:ticket :: --remove-label :: mmw:child"
  hasnt ":: --parent :: 18"
  hasnt "gh :: issue :: close :: 92"

  echo "--- became-ticket as another ticket already under the spec: no move, and the child closes as its duplicate"
  code="$(route_in env FAKE_GH_LABEL_EXISTS=1 bash "$DISPATCH" "${TOOLS[@]}" route 61 93 became-ticket 80)"
  [ "$code" = 0 ] || fail "a label that already exists should not stop the route, got $code: $(cat "$TMP/err")"
  has "gh :: issue :: edit :: 80 :: --add-label :: mmw:ticket"
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
  grep -q "already routed" "$TMP/err" || fail "it should say so: $(cat "$TMP/err")"
  hasnt "gh :: issue :: edit"
  [ "$(posted_events 61 | grep -c child.closed)" = 4 ] || fail "a second child.closed was posted"

  echo "--- routed another way already: refused, nothing done"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 stale)"
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
  grep -q "#61 carries no child.opened for #95" "$TMP/err" || fail "the refusal should say why: $(cat "$TMP/err")"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 done)"
  [ "$code" = 2 ] || fail "an unknown resolution should exit 2, got $code: $(cat "$TMP/err")"
  code="$(route_in bash "$DISPATCH" "${TOOLS[@]}" route 61 90 became-ticket)"
  [ "$code" = 2 ] || fail "became-ticket with no ticket should exit 2, got $code: $(cat "$TMP/err")"
  hasnt "gh :: issue :: close"
  hasnt "gh :: issue :: edit"
  [ -z "$(posted_events 61)" ] || fail "nothing should be posted: $(posted_events 61)"
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
  # The starts took no slot; each worker's first run that needs the product claims one.
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "the starts should hold no slot, they hold $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-61" >/dev/null
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-63" >/dev/null
  seed_workspace 65
  python3 "$LEASE_PY" claim "$TMP/repo/.worktrees/issue-65" >/dev/null
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 3 ] \
    || fail "the night should hold three slots, it holds $(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")"

  seed_agent 61 worker
  seed_agent 61 verifier
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
  # worker mid-turn is exactly what suspend exists to end. A verifier still running on the
  # ticket is ended too: left alone it keeps the product up after its slot is given back.
  has "paseo :: archive :: --force :: agt_61_worker"
  has "paseo :: archive :: --force :: agt_61_verifier"
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
  posted_events 61 interrupted | grep -qx "spec.suspended interrupted=agt_61_worker, agt_61_verifier" \
    || fail "#61 should carry spec.suspended naming its worker and verifier: $(posted_events 61 interrupted)"
  posted_events 61 reason | grep -qx "ticket.released reason=suspended" \
    || fail "#61 should carry ticket.released (suspended): $(posted_events 61 reason)"
  grep -qF 'Interrupted: agt_61_worker, agt_61_verifier.' "$MMW_TEST_LOG" \
    || fail "the comment on #61 does not say its sessions were interrupted"
  grep -qF 'No session of ours was working on it' "$MMW_TEST_LOG" \
    || fail "the comment on #63 does not say it had no session"
  hasnt "gh :: issue :: comment :: 65"

  echo "--- the slots the night held are back"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "slots are still held: $(python3 "$LEASE_PY" list)"
  [ "$(python3 "$LEASE_PY" count "$TMP/other-repo")" = 1 ] \
    || fail "a lease from another checkout was released: $(python3 "$LEASE_PY" list)"
  grep -q 'suspend #76: stopped 2, commented 2, slots given back 3, claims given back 2' "$TMP/out" \
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
  # The product runs only under a slot, which the first run of the worker's criteria claims.
  python3 "$LEASE_PY" claim "$ws" >/dev/null

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

  echo "--- start takes no --label: a usage error, and nothing is started"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
          --cwd "$TMP/repo" --prompt hi --label mmw.ticket=61)"
  [ "$code" = 2 ] || fail "paseo start with --label expected usage 2, got $code: $(cat "$TMP/err")"
  never_ran

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

  echo "--- start takes no --label: a usage error, and no tab is opened"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
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
  [ "$(arg_after --title)" = "$(basename -- "${worktree#path:}")" ] \
    || fail "a start with no title should be named after its worktree, got: $(arg_after --title)"

  echo "--- the tab carries the title dispatch passes, so one ticket's sessions differ"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
          --cwd . --prompt hi --skip-approval --title "#61 reviewer")"
  [ "$code" = 0 ] || fail "orca start with a title expected 0, got $code: $(cat "$TMP/err")"
  [ "$(arg_after --title)" = "#61 reviewer" ] \
    || fail "the tab should be named '#61 reviewer', got: $(arg_after --title)"

  echo "--- the first prompt is the last argument of the command exec runs, and nothing is typed"
  reset_log
  local first="Use the implement skill on #61. Don't ask 'Shall I…?'"
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
          --cwd . --prompt "$first" --skip-approval)"
  [ "$code" = 0 ] || fail "orca start expected 0, got $code: $(cat "$TMP/err")"
  MMW_FIRST="$first" python3 -c '
import json, os, shlex, sys
argv = shlex.split(json.load(open(sys.argv[1]))[-1]["command"])
assert argv[:2] == ["exec", "grok"], argv
assert argv[-1] == os.environ["MMW_FIRST"], argv
' "$MMW_FAKE_ORCA_STATE/terminals.json" \
    || fail "the command should be exec grok … with the prompt last: $(arg_after --command)"
  hasnt "orca :: terminal :: send"
  hasnt "--for :: tui-idle"
  grep -q -- '--for :: exit' "$MMW_TEST_LOG" \
    || fail "start should wait for the host to exit: $(cat "$MMW_TEST_LOG")"

  echo "--- start takes no --label: a usage error, and no terminal is created"
  reset_log
  code="$(run_runner start --host grok --model grok-4.6 --effort high \
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
  [ "$code" != 0 ] || fail "orca with no turn start must not read as confirmed"
  [ "$code" != 2 ] || fail "orca with no turn start must not read as missing"
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
  echo "--- already working: nothing is sent, exit 3, so sending again is safe"
  reset_log
  seed_herdr_agent agt_w61 working
  code="$(run_runner send agt_w61 continue)"
  [ "$code" = 3 ] || fail "a working agent was sent nothing: 3, got $code: $(cat "$TMP/err")"
  grep -q "nothing was sent" "$TMP/err" || fail "stderr should say nothing was sent: $(cat "$TMP/err")"
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

  echo "--- input_accepted without turn_started: the text is in the terminal, exit 4, never 3"
  reset_log
  seed_orca_terminal term_w61
  code="$(MMW_FAKE_ORCA_SEND=accepted-only run_runner send term_w61 continue)"
  [ "$code" = 4 ] || fail "accepted-only was typed, so 4 and not 3 (3 has the relay type it again), got $code: $(cat "$TMP/err")"
  grep -q "no turn start was seen" "$TMP/err" || fail "stderr should say no turn start was seen: $(cat "$TMP/err")"
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
  grep -q "Orca refused the send" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"

  echo "--- a host whose delivery Orca cannot report still starts: the handle, exit 0, its terminal kept"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SEND=unobserved run_runner start --host grok --model grok-4.6 --effort high --cwd "$TMP/repo" --prompt go)"
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
  echo "--- open opens the spec's watch with this session as its main agent, starts the relay, and writes spec.opened"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open expected 0, got $code: $(cat "$TMP/err")"
  grep -qx "opened #76: wake-ups go to paseo session agt_main" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "spec 76's main agent should be agt_main: $(cat "$STATE_DIR/watches.json" 2>&1)"
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

  echo "--- another night in this repository, opened by another session, joins the one relay with its own main agent"
  seed_main_agent agt_other
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 77)"
  [ "$code" = 0 ] || fail "open 77 expected 0, got $code: $(cat "$TMP/err")"
  grep -qx "opened #77: wake-ups go to paseo session agt_other" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  [ "$(relay_now | cut -d' ' -f1)" = "$pid" ] || fail "the second night should join relay $pid: $(relay_now)"
  [ "$(watch_main spec:77)" = "paseo agt_other" ] || fail "spec 77's main agent should be agt_other: $(cat "$STATE_DIR/watches.json")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "spec 76's main agent should still be agt_main: $(cat "$STATE_DIR/watches.json")"
  posted_events 77 runner session | grep -qx "spec.opened runner=paseo session=agt_other" \
    || fail "#77 should carry spec.opened naming its main agent: $(posted_events 77 runner session)"

  echo "--- a ticket of an open night is refused a watch of its own, and the night keeps its main agent"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 61)"
  [ "$code" = 2 ] || fail "open-ticket 61 expected 2, got $code"
  grep -q "#61 is a sub-issue of spec #76, which is watched with paseo session agt_main as its main agent" "$TMP/err" \
    || fail "the refusal should name the watch it overlaps: $(cat "$TMP/err")"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "a refused open must not touch spec 76's main agent: $(cat "$STATE_DIR/watches.json")"
  [ -z "$(watch_main tickets:61)" ] || fail "no watch on #61 should be open: $(cat "$STATE_DIR/watches.json")"

  echo "--- summary closes its night's watch, and the relay goes on for the other night"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 76)"
  [ "$code" = 0 ] || fail "summary expected 0, got $code: $(cat "$TMP/err")"
  grep -q "stopped watching spec #76 for o/r: the relay (pid $pid) goes on watching spec #77" "$TMP/err" \
    || fail "summary should say the relay goes on for #77: $(cat "$TMP/err")"
  case "$(relay_now)" in "$pid "'{"spec": 77}') ;; *) fail "relay $pid should watch spec 77 alone: $(relay_now)" ;; esac

  echo "--- the last night's summary ends the relay"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" summary 77)"
  [ "$code" = 0 ] || fail "summary 77 expected 0, got $code: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "summary should have stopped the relay: $(relay_now)"
  kill -0 "$pid" 2>/dev/null && fail "relay pid $pid should be gone"
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
  grep -q "runs in no runner whose adapter can name it (asked: paseo herdr orca)" "$TMP/err" \
    || fail "the refusal should name the runners asked: $(cat "$TMP/err")"
  [ ! -f "$STATE_DIR/watches.json" ] || fail "no watch should be open: $(cat "$STATE_DIR/watches.json")"
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
  [ ! -f "$STATE_DIR/watches.json" ] || fail "the outer Orca terminal must not be made a main agent: $(cat "$STATE_DIR/watches.json")"

  echo "--- a session the runner shows stopped is refused"
  reset_log
  no_relay
  code="$(run_dispatch env PASEO_AGENT_ID=agt_gone FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "session agt_gone is stopped" "$TMP/err" || fail "the refusal should say the session is stopped: $(cat "$TMP/err")"
  [ -z "$(relay_now)" ] || fail "no relay should run: $(relay_now)"

  echo "--- spec.opened that cannot be written closes the watch open opened, and the relay with it"
  reset_log
  no_relay
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_COMMENT_FAILS=1 FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 2 ] || fail "expected 2, got $code"
  grep -q "could not write the spec.opened event on #76, so the night is not open and the watch this opened was closed again" "$TMP/err" \
    || fail "the refusal should say the watch was closed: $(cat "$TMP/err")"
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
   "comments": [$(ev ticket.passed 90 "ALL MET" --field branch=issue-90 --field into=main),
                $(ev ticket.landed 90 "Landed issue-90 into main" --field into=main)]},
  {"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}
]
JSON
  echo "--- open-ticket opens a watch of that ticket alone with this session as its main agent, and starts the relay"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 90)"
  [ "$code" = 0 ] || fail "open-ticket expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"tickets": [90]}'*) ;; *) fail "a relay should watch #90: $(relay_now)" ;; esac
  [ "$(watch_main tickets:90)" = "paseo agt_main" ] || fail "#90's main agent should be agt_main: $(cat "$STATE_DIR/watches.json")"
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

  echo "--- a ticket outside the open night gets a watch of its own beside it, and the night keeps its main agent"
  local pid
  pid="$(relay_now | cut -d' ' -f1)"
  seed_main_agent agt_other
  code="$(run_dispatch env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open-ticket 95)"
  [ "$code" = 0 ] || fail "open-ticket 95 beside the night expected 0, got $code: $(cat "$TMP/err")"
  grep -qx "opened #95: wake-ups go to paseo session agt_other" "$TMP/out" || fail "stdout: $(cat "$TMP/out")"
  [ "$(relay_now)" = "$pid "'{"spec": 76} {"tickets": [95]}' ] || fail "relay $pid should watch the night and #95: $(relay_now)"
  [ "$(watch_main spec:76)" = "paseo agt_main" ] || fail "the night's main agent should still be agt_main: $(cat "$STATE_DIR/watches.json")"
  [ "$(watch_main tickets:95)" = "paseo agt_other" ] || fail "#95's main agent should be agt_other: $(cat "$STATE_DIR/watches.json")"
  no_relay
}

# A worktree on issue-61 that a session picked up itself, with no `start` behind it.
self_picked_worktree() {
  mkdir -p "$(trees)"
  git -C "$TMP/repo" worktree add --quiet -b issue-61 "$(wt 61)" main
  printf 'work\n' > "$(wt 61)/work.txt"
  git -C "$(wt 61)" add work.txt
  git -C "$(wt 61)" -c user.email=t@t -c user.name=t commit -q -m work
}

scenario_adopt() {
  local code tree
  fresh_repo
  reset_log
  no_relay
  seed_main_agent agt_self
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent", "senior-worker"], "parent": null}]
JSON
  self_picked_worktree
  tree="$(cd "$(wt 61)" && pwd -P)"

  echo "--- outside a night with no prior worker, adopt asks for --into rather than guessing"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 2 ] || fail "adopt without a base branch expected 2, got $code"
  grep -q "pass --into <base branch>" "$TMP/err" \
    || fail "the refusal should ask for --into: $(cat "$TMP/err")"

  echo "--- a session that picked #61 up itself becomes its worker, and a relay watches #61"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61 --into main) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "adopt expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = agt_self ] || fail "adopt should print the session: $(cat "$TMP/out")"
  MMW_TREE="$tree" MMW_BASE="$(git -C "$TMP/repo" rev-parse main)" python3 -c '
import importlib.util, json, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("ev", os.environ["MMW_EVENTS_PY_FOR_TESTS"])
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)
posted = json.loads((Path(os.environ["MMW_FAKE_PASEO_STATE"]) / "gh-comments.json").read_text()).get("61", [])
state = ev.fold(posted)
w = ev.session_of(state, "worker")
want = {"runner": "paseo", "session": "agt_self", "grade": "senior-worker",
        "worktree": os.environ["MMW_TREE"], "branch": "issue-61", "base": os.environ["MMW_BASE"]}
bad = {k: (w or {}).get(k) for k in want if (w or {}).get(k) != want[k]}
assert not bad, bad
assert w["host"] and w["model"] and w["live"], w
assert w.get("slot") is None, w
' || fail "worker.started should name this session with the grade row and this worktree, and no slot: $(posted_events 61 session runner grade slot)"
  posted_events 61 machine | grep -qx "worker.started machine=$(python3 -c 'import socket; print(socket.gethostname())')" \
    || fail "the adopted worker.started should name this machine: $(posted_events 61 machine)"
  posted_events 61 into | grep -qx "worker.started into=main" \
    || fail "the adopted worker.started should name main as into: $(posted_events 61 into)"
  [ "$(python3 "$LEASE_PY" count "$TMP/repo/.worktrees")" = 0 ] \
    || fail "adopt took a slot; the first run that needs the product claims it: $(python3 "$LEASE_PY" list)"
  case "$(relay_now)" in *'{"tickets": [61]}'*) ;; *) fail "a relay should watch #61: $(relay_now)" ;; esac
  [ "$(watch_main tickets:61)" = "paseo agt_self" ] \
    || fail "the adopting session is the main agent of #61's watch: $(cat "$STATE_DIR/watches.json")"

  echo "--- and from there its reviewer can be started: the ticket can finish"
  code="$( (cd "$tree" && env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" start 61 reviewer) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "start 61 reviewer after adopt expected 0, got $code: $(cat "$TMP/err")"

  echo "--- adopting again from the same session writes no second worker.started"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "a second adopt expected 0, got $code: $(cat "$TMP/err")"
  [ "$(posted_events 61 | grep -c '^worker.started')" = 1 ] || fail "one worker.started: $(posted_events 61)"

  echo "--- another session cannot adopt a ticket a live worker holds"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_other FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 2 ] || fail "adopt over a live worker expected 2, got $code"
  grep -q "is held by worker agt_self on paseo" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  no_relay

  echo "--- adopt from a checkout not on issue-61 is refused, and nothing is written"
  reset_log
  no_relay
  code="$(run_dispatch env PASEO_AGENT_ID=agt_self FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61)"
  [ "$code" = 2 ] || fail "adopt on main expected 2, got $code"
  grep -q "is worked on branch issue-61" "$TMP/err" || fail "stderr: $(cat "$TMP/err")"
  [ -z "$(posted_events 61)" ] || fail "nothing should be posted: $(posted_events 61)"
  [ -z "$(relay_now)" ] || fail "no relay should be started: $(relay_now)"

  echo "--- inside a night, adopt keeps the night's relay and starts none"
  reset_log
  seed_main_agent agt_self
  post_ev 76 spec.opened --spec 76 --line "NIGHT OPENED #76" --field into=main
  cat > "$TMP/tickets.json" <<'JSON'
[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"]}]
JSON
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" adopt 61) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "adopt in a night expected 0, got $code: $(cat "$TMP/err")"
  case "$(relay_now)" in *'{"spec": 76}'*) ;; *) fail "the night's relay should be the one: $(relay_now)" ;; esac
  [ "$(watch_main spec:76)" = "paseo agt_main" ] && [ -z "$(watch_main tickets:61)" ] \
    || fail "the night's main agent is not this session's to take: $(cat "$STATE_DIR/watches.json")"
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

  echo "--- the same wake acked again matches no row of this session: refused, nothing removed"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack '#61' ticket.passed)"
  [ "$code" = 2 ] || fail "a second ack expected 2, got $code: $(cat "$TMP/err")"
  grep -q "Queued for this session: \`#62 ticket.returned\`" "$TMP/err" || fail "the refusal should list what is queued for it: $(cat "$TMP/err")"
  [ "$(queue_seqs)" = "2 3" ] || fail "nothing more should go: $(queue_seqs)"

  echo "--- the main agent acking the worker's wake is refused: another session's row stays"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 61 reviewer.reported)"
  [ "$code" = 2 ] || fail "acking another session's wake expected 2, got $code"
  [ "$(queue_seqs)" = "2 3" ] || fail "the worker's row must stay: $(queue_seqs)"

  echo "--- a wake that was never queued is refused"
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main bash "$DISPATCH" "${TOOLS[@]}" ack 99 ticket.passed)"
  [ "$code" = 2 ] || fail "ack of a wake never queued expected 2, got $code"
  grep -q "no wake \`#99 ticket.passed\` is queued for paseo session agt_main" "$TMP/err" || fail "the refusal should name the wake: $(cat "$TMP/err")"
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
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  echo "--- land removes the worktree with git and deletes the contained ticket branch"
  reset_log
  fresh_repo
  make_branch issue-64 four.txt "from 64"
  write_landable
  seed_workspace 64
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/repo" show origin/main:four.txt >/dev/null 2>&1 || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_no_branch 64
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

scenario_boardregisters() {
  local code port expected repository
  echo "--- board registers the main checkout on the first free port and starts it"
  fresh_board_registry
  expected="$(python3 - <<'PY'
import socket
for port in range(47100, 65536):
    sock = socket.socket()
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.close()
        continue
    sock.close()
    print(port)
    break
PY
)"
  code="$(run_dispatch env MMW_RUNNER=paseo bash "$DISPATCH" board)"
  [ "$code" = 0 ] || fail "board expected 0: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  repository="$(cd "$TMP/repo" && pwd -P)"
  MMW_REPOSITORY="$repository" MMW_PORT="$port" MMW_EXPECTED="$expected" \
    python3 - "$MMW_HOME/boards.json" <<'PY' || fail "boards.json has the wrong registration"
import json, os, sys
data = json.load(open(sys.argv[1]))
assert data == {os.environ["MMW_REPOSITORY"]: int(os.environ["MMW_PORT"])}, data
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
  local code port repository
  echo "--- board asks the Orca adapter for a tab tied to the current worktree"
  fresh_board_registry
  code="$(run_dispatch env MMW_RUNNER=orca bash "$DISPATCH" board)"
  [ "$code" = 0 ] || fail "Orca board expected 0: $(cat "$TMP/err")"
  port="$(board_registry_port)"
  BOARD_TEST_PORTS="$port"
  repository="$(cd "$TMP/repo" && pwd -P)"
  has "orca :: tab :: create :: --url :: http://127.0.0.1:$port :: --worktree :: path:$repository :: --json"
  [ ! -s "$TMP/out" ] || fail "successful tab creation should print nothing: $(cat "$TMP/out")"
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

scenario_installboardagent() {
  local home="$TMP/install-home" plist
  echo "--- install writes the board LaunchAgent in the test home without launchctl"
  rm -rf "$home"
  mkdir -p "$home"
  reset_log
  MMW_V2_HOME="$home" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  plist="$home/Library/LaunchAgents/com.mmw.board.plist"
  [ -f "$plist" ] || fail "install did not write $plist"
  python3 - "$plist" <<'PY' || fail "the board LaunchAgent has the wrong contract"
import plistlib, sys
with open(sys.argv[1], "rb") as fh:
    data = plistlib.load(fh)
assert data["Label"] == "com.mmw.board", data
assert data["KeepAlive"] is True, data
assert data["RunAtLoad"] is True, data
assert any(value.endswith("/mmw-v2/board/supervisor.py")
           for value in data["ProgramArguments"]), data
PY
  hasnt "launchctl"
}

scenario_installcheckboardagent() {
  local home="$TMP/install-home" code plist
  echo "--- install --check reports a missing board LaunchAgent in the test home"
  rm -rf "$home"
  mkdir -p "$home"
  reset_log
  MMW_V2_HOME="$home" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  plist="$home/Library/LaunchAgents/com.mmw.board.plist"
  rm -f "$plist"
  MMW_V2_HOME="$home" bash "$INSTALLER" --check > "$TMP/out" 2> "$TMP/err"
  code=$?
  [ "$code" = 1 ] || fail "missing board LaunchAgent expected exit 1, got $code"
  grep -q '^缺    .*com\.mmw\.board\.plist' "$TMP/err" \
    || fail "--check did not name the missing board LaunchAgent: $(cat "$TMP/err")"
  hasnt "launchctl"
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
  if grep -E '^没查    (orca|herdr|paseo)|^不一致  适配器' "$TMP/err" "$TMP/out"; then
    fail "agree should print neither 没查 nor 不一致: $(cat "$TMP/err") $(cat "$TMP/out")"
  fi
  if grep -q Traceback "$TMP/err"; then
    fail "the check crashed: $(cat "$TMP/err")"
  fi
  has "orca :: agent-context"
  has "herdr :: agent :: start :: --help"
  has "paseo :: send :: --help"
  has "paseo :: provider :: ls :: --help"
  has "paseo :: provider :: models :: --help"
  has "paseo :: provider :: diagnostic :: --help"
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
  grep -q '^不一致  适配器' "$TMP/err" \
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
  [ "${MMW_TEST_REUSE_INSTALL_HOME:-0}" = 1 ] || rm -rf "$home"
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

scenario_installkeepsnewestbackup() {
  reset_log
  seed_orca_projects 1 .worktrees show
  run_installer
  local config="$TMP/install-home/.paseo/config.json"
  [ -f "$config" ] || fail "the first install did not create $config"
  printf '%s\n' '{"version":999}' > "$config"
  : > "$config.bak-old"
  MMW_TEST_REUSE_INSTALL_HOME=1 run_installer
  [ "$(cat "$TMP/code")" = 0 ] || fail "the second install failed: $(cat "$TMP/err")"
  [ ! -e "$config.bak-old" ] || fail "the stale backup survived"
  grep -q '"version":999' "$TMP/install-home/.paseo/config.json.bak-"* \
    || fail "the surviving backup is not the configuration the install replaced"
  [ "$(find "$TMP/install-home/.paseo" -maxdepth 1 -name 'config.json.bak-*' | wc -l | tr -d ' ')" = 1 ] \
    || fail "install kept more than its newest backup: $(find "$TMP/install-home/.paseo" -maxdepth 1 -name 'config.json.bak-*' -print)"
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

scenario_startreadsmodelsjson() {
  local code legacy="$MMW_HOME/models.md"
  echo "--- start reads models.json and ignores a conflicting retired Markdown file"
  cat > "$legacy" <<'TABLE'
| runner | herdr |
| agent | host | model | effort |
| junior-worker | claude | opus 5 | max |
TABLE
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "start expected 0, got $code: $(cat "$TMP/err")"
  [ "$(out_json provider)" = "cursor/grok-4.6" ] \
    || fail "start did not use models.json: $(cat "$TMP/out")"
  [ "$(out_json settings.thinkingOptionId)" = "true" ] \
    || fail "start did not use the models.json effort: $(cat "$TMP/out")"
  rm -f "$legacy"
}

scenario_startnomodelsjson() {
  local code saved="$TMP/models.saved"
  mv "$MMW_HOME/models.json" "$saved"
  printf '%s\n' '| junior-worker | cursor | grok 4.6 | high |' > "$MMW_HOME/models.md"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "missing models.json expected 2, got $code"
  grep -q "no models.json.*run install.sh" "$TMP/err" \
    || fail "the refusal is not actionable: $(cat "$TMP/err")"
  never_ran
  rm -f "$MMW_HOME/models.md"
  mv "$saved" "$MMW_HOME/models.json"
}

scenario_installimportsmodelsmd() {
  local home="$TMP/import-home"
  rm -rf "$home"; mkdir -p "$home/.mmw"
  cat > "$home/.mmw/models.md" <<'TABLE'
| runner | herdr |
| agent | host | model | effort |
| junior-worker | cursor | grok 4.6 | high |
| senior-worker | grok | grok 4.6 | xhigh |
| reviewer | claude | opus 5 | high |
| verifier | claude | sonnet 5 | high |
| advisor | claude | fable 5.1 | medium |
TABLE
  MMW_V2_HOME="$home" MMW_HOME="$home/.mmw" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  [ -f "$home/.mmw/models.json" ] || fail "models.json was not imported"
  [ ! -e "$home/.mmw/models.md" ] || fail "the imported Markdown file was not deleted"
  python3 - "$home/.mmw/models.json" <<'PY' || fail "the import did not preserve values"
import json, sys
data = json.load(open(sys.argv[1]))
expected = {
    "junior-worker": {"host": "cursor", "model": "grok 4.6", "effort": "high"},
    "senior-worker": {"host": "grok", "model": "grok 4.6", "effort": "xhigh"},
    "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
    "verifier": {"host": "claude", "model": "sonnet 5", "effort": "high"},
    "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
}
assert data == {"version": 1, "runner": "herdr", "rows": expected}, data
PY
}

scenario_installinitialvalues() {
  local home="$TMP/initial-home"
  rm -rf "$home"; mkdir -p "$home"
  MMW_V2_HOME="$home" MMW_HOME="$home/.mmw" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  python3 - "$home/.mmw/models.json" "$SKILL/hosts.json" <<'PY' || fail "fresh defaults are wrong"
import json, sys
data = json.load(open(sys.argv[1]))
hosts = json.load(open(sys.argv[2]))
expected = {
    row["agent"]: {key: row[key] for key in ("host", "model", "effort")}
    for row in hosts["defaults"]
}
assert data["version"] == 1 and data["runner"] == "orca", data
assert data["rows"] == expected, data
PY
}

scenario_installkeepsmodelsjson() {
  local home="$TMP/keep-home" before after
  rm -rf "$home"; mkdir -p "$home/.mmw"
  cp "$MMW_HOME/models.json" "$home/.mmw/models.json"
  python3 - "$home/.mmw/models.json" <<'PY'
import json, sys
p=sys.argv[1]; d=json.load(open(p)); d["version"]=41; json.dump(d, open(p,"w"), separators=(",",":"))
PY
  printf '%s\n' '| junior-worker | claude | opus 5 | max |' > "$home/.mmw/models.md"
  before="$(shasum -a 256 "$home/.mmw/models.json" | cut -d' ' -f1)"
  MMW_V2_HOME="$home" MMW_HOME="$home/.mmw" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  after="$(shasum -a 256 "$home/.mmw/models.json" | cut -d' ' -f1)"
  [ "$before" = "$after" ] || fail "install rewrote an existing models.json"
  [ -f "$home/.mmw/models.md" ] || fail "install imported models.md beside existing JSON"
}

scenario_installcheckmodelsjson() {
  local home="$TMP/check-models-home" code
  rm -rf "$home"; mkdir -p "$home/.mmw"
  MMW_V2_HOME="$home" MMW_HOME="$home/.mmw" bash "$INSTALLER" --check > "$TMP/out" 2> "$TMP/err"; code=$?
  [ "$code" = 1 ] || fail "missing models.json expected check exit 1, got $code"
  grep -q "no models.json.*run install.sh" "$TMP/err" \
    || fail "check did not name the missing file: $(cat "$TMP/err")"

  rm -rf "$home"; mkdir -p "$home/.mmw"
  cp "$MMW_HOME/models.json" "$home/.mmw/models.json"
  python3 - "$home/.mmw/models.json" <<'PY'
import json, sys
p=sys.argv[1]; d=json.load(open(p)); del d["rows"]["reviewer"]; json.dump(d, open(p,"w"))
PY
  MMW_V2_HOME="$home" MMW_HOME="$home/.mmw" bash "$INSTALLER" --check > "$TMP/out" 2> "$TMP/err"; code=$?
  [ "$code" = 1 ] || fail "invalid models.json expected check exit 1, got $code"
  grep -q "models.json rows:.*missing reviewer" "$TMP/err" \
    || fail "check did not name the bad row: $(cat "$TMP/err")"
}

scenario_installmodelsjsonhome() {
  local home="$TMP/home-contract"
  rm -rf "$home"; mkdir -p "$home"
  MMW_V2_HOME="$home" MMW_HOME="$home/config" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  [ -f "$home/config/models.json" ] || fail "install did not honor MMW_HOME"
  [ ! -e "$home/.mmw/models.json" ] || fail "install also wrote HOME_DIR/.mmw"

  rm -rf "$home"; mkdir -p "$home"
  env -u MMW_HOME MMW_V2_HOME="$home" bash "$INSTALLER" > "$TMP/out" 2> "$TMP/err" || true
  [ -f "$home/.mmw/models.json" ] || fail "install did not default to HOME_DIR/.mmw"
}

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
  [ "$(grep -c 'did not attach the worktree' "$TMP/err")" = 1 ] \
    || fail "link failure should be one stderr line: $(cat "$TMP/err")"
  posted_events 61 | grep -q worker.started || fail "worker.started was not recorded"
}

scenario_worktreelinknoop() {
  local code name
  for name in paseo herdr; do
    fresh_repo
    reset_log
    code="$(run_dispatch env MMW_RUNNER="$name" bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
    [ "$code" = 0 ] || fail "$name start expected 0, got $code: $(cat "$TMP/err")"
    posted_events 61 | grep -q worker.started || fail "$name start recorded no session"
    ! grep -q 'did not attach' "$TMP/err" || fail "$name attach reported a failure"

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

  echo "--- a worker's start carries no slot: the first run that needs the product claims it"
  reset_log
  fresh_repo
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  posted_events 61 slot | grep -qx "worker.started slot=None" \
    || fail "the worker.started event should carry no slot: $(posted_events 61 slot)"
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
  grep -q "#60's ticket.passed event carries no usable commit" "$TMP/err" \
    || fail "stderr should name the unusable pass: $(cat "$TMP/err")"
  [ -z "$(posted_events 60)" ] || fail "#60 must not be recorded landed: $(posted_events 60)"
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
  grep -q "still blocked by #60 (passed, not landed)" "$TMP/err" \
    || fail "stderr should say #61 waits on #60's landing: $(cat "$TMP/err")"

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
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  echo "--- land takes the ticket's Paseo agents off the list and deletes its contained ticket branch"
  reset_log
  fresh_repo
  make_branch issue-64 four.txt "from 64"
  write_landable
  seed_workspace 64
  seed_agent 64 worker
  seed_agent 64 reviewer
  seed_agent 64 verifier
  seed_agent 99 worker 99
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "expected exit 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/repo" show origin/main:four.txt >/dev/null 2>&1 || fail "issue-64 was not merged"
  assert_no_wt 64
  assert_no_branch 64
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
  echo "--- wait asks no runner: with the adapter gone it still reads the ticket and answers"
  reset_log
  printf '%s\n' '[{"number": 61, "state": "OPEN", "labels": ["ready-for-agent"], "comments": []}]' > "$TMP/tickets.json"
  seed_agent 61 worker
  copy="$(skill_copy_for wait)"
  rm -f "$copy/scripts/runners/paseo.sh"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" wait 61 worker)"
  [ "$code" = 3 ] || fail "no result yet is exit 3 whatever the adapter, got $code: $(cat "$TMP/err")"
  grep -q "no result of its worker yet" "$TMP/err" || fail "stderr should say no result yet: $(cat "$TMP/err")"
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
  grep -q "cannot tell" "$TMP/err" || fail "retract should say it cannot tell: $(cat "$TMP/err")"
  if grep -q "still has a live agent" "$TMP/err"; then fail "unknown must not read as a live agent: $(cat "$TMP/err")"; fi
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
  [ "$head" = "wip(#61): uncommitted work of worker agt_61_worker on paseo, left when its hold ended with worker.lost" ] \
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
  [ "$head" = "wip(#63): uncommitted work of worker agt_63_worker on paseo, left when its session stopped" ] \
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

scenario_orcarefusalreason() {
  local code
  RUNNER="$ORCA_RUNNER"
  echo "--- a terminal create Orca refuses on stdout carries Orca's reason"
  reset_log
  fresh_repo
  code="$(MMW_FAKE_ORCA_SCENARIO=start-refused run_runner start --host grok --model grok-4.6 --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code"
  grep -q "terminal create refused grok .*selector_not_found" "$TMP/err" \
    || fail "the refusal should carry Orca's reason: $(cat "$TMP/err")"
}

scenario_nightfromtask() {
  local code task
  echo "--- a night run from a task-branch worktree cuts tickets from that branch, under the main checkout"
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
  [ -d "$TMP/repo/.worktrees/issue-61" ] || fail "the ticket worktree should be under the main checkout's .worktrees"
  [ ! -d "$task/.worktrees/issue-61" ] || fail "no second .worktrees under the task worktree"
  [ -f "$TMP/repo/.worktrees/issue-61/feat.txt" ] || fail "issue-61 should be cut from feature-x, the branch the night runs on"
  posted_events 61 into | grep -qx "worker.started into=feature-x" \
    || fail "worker.started should record feature-x: $(posted_events 61 into)"

  echo "--- a directory named issue-<n> on another branch is not taken over"
  reset_log
  git -C "$TMP/repo" worktree add -q "$TMP/repo/.worktrees/issue-62" -b mine main
  code="$( (cd "$task" && bash "$DISPATCH" "${TOOLS[@]}" start 62 worker) > "$TMP/out" 2> "$TMP/err"; echo $?)"
  [ "$code" = 2 ] || fail "expected refusal 2, got $code"
  grep -q "is on mine, not issue-62" "$TMP/err" || fail "the refusal should name the branch it found: $(cat "$TMP/err")"
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
  code="$(MMW_FAKE_ORCA_SCENARIO=exited run_runner start --host grok --model "grok 4.6" --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  nothing_printed
  one_line_reason
  grep -q "grok exited within 3 s of starting" "$TMP/err" || fail "stderr should say the host exited: $(cat "$TMP/err")"
  grep -q "its last lines: none, Orca kept no output" "$TMP/err" \
    || fail "an emptied terminal should be said to hold no output: $(cat "$TMP/err")"
  grep -qF "run it by hand there: grok -m 'grok 4.6' --reasoning-effort high" "$TMP/err" \
    || fail "stderr should give the command to run by hand: $(cat "$TMP/err")"
  has "orca :: terminal :: read"
  has "orca :: terminal :: close"
  [ "$(orca_terminals_left)" = 0 ] || fail "a refused start left a terminal behind"

  echo "--- the lines the terminal still holds go into the refusal"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=exited MMW_FAKE_ORCA_TAIL=$'\nerror: unexpected argument found\n' \
          run_runner start --host grok --model grok-4.6 --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  grep -q "its last lines: error: unexpected argument found;" "$TMP/err" \
    || fail "stderr should carry the terminal's last lines: $(cat "$TMP/err")"

  echo "--- an exit wait this cannot read falls back to liveness: alive is a start"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=exit-wait-garbage run_runner start --host grok --model grok-4.6 --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 0 ] || fail "a live handle is a start, expected 0, got $code: $(cat "$TMP/err")"
  [ "$(cat "$TMP/out")" = term_1 ] || fail "start should print the handle: $(cat "$TMP/out")"
  hasnt "orca :: terminal :: close"

  echo "--- and a liveness that is not alive is a refusal that closes the terminal"
  reset_log
  code="$(MMW_FAKE_ORCA_SCENARIO=wait-garbage run_runner start --host grok --model grok-4.6 --effort high --cwd "$TMP/repo" --prompt go)"
  [ "$code" = 1 ] || fail "expected refusal 1, got $code: $(cat "$TMP/err")"
  nothing_printed
  grep -q "whether it is still running could not be read" "$TMP/err" || fail "stderr should say why: $(cat "$TMP/err")"
  has "orca :: terminal :: close"
  [ "$(orca_terminals_left)" = 0 ] || fail "a refused start left a terminal behind"
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

# ------------------------------------------------------------------ origin authority

scenario_checknoorigin() {
  local code
  fresh_repo
  git -C "$TMP/repo" remote remove origin
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "check without origin expected 2, got $code"
  grep -q "no origin remote" "$TMP/err" || fail "missing origin was not named: $(cat "$TMP/err")"
}

scenario_checknopush() {
  local code
  fresh_project_night
  git -C "$TMP/repo" push -q -u origin night
  git -C "$TMP/repo" remote set-url --push origin "$TMP/no-such-parent/origin.git"
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" check 76)"
  [ "$code" = 2 ] || fail "check with no push path expected 2, got $code"
  grep -Eq "dry-run fast-forward of (proj|night) failed" "$TMP/err" \
    || fail "the dry-run push failure was not named: $(cat "$TMP/err")"
}

scenario_checkbasemissing() {
  local code copy
  copy="$(skill_copy_for check-base-missing)"
  fresh_project_night
  code="$(run_dispatch bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" check 76)"
  [ "$code" = 0 ] || fail "check with a local-only base expected 0, got $code: $(cat "$TMP/err")"
  grep -q "open would push proj: 0 commit(s), night: 1 commit(s)" "$TMP/out" \
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
  grep -q "open would push proj: 0 commit(s), night: 2 commit(s)" "$TMP/out" \
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

scenario_openpushesahead() {
  local code local_head
  fresh_project_night
  local_head="$(git -C "$TMP/repo" rev-parse night)"
  reset_log
  no_relay
  write_open_batch
  seed_main_agent agt_main
  code="$(run_dispatch env PASEO_AGENT_ID=agt_main FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" open 76)"
  [ "$code" = 0 ] || fail "open on an ahead base expected 0, got $code: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$local_head" ] \
    || fail "open did not push the local base branch"
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
  grep -q 'default branch' "$TMP/err" || fail "default refusal missing: $(cat "$TMP/err")"
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
  grep -q 'default branch main' "$TMP/err" || fail "from-default refusal missing: $(cat "$TMP/err")"
  [ -z "$(posted_events 76)" ] || fail "from-default open wrote spec.opened"
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
  grep -q 'local has 1 commit(s), origin has 1 commit(s)' "$TMP/err" || fail "divergence counts missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$project_remote" ] || fail "project changed on refusal"
  [ "$(git -C "$TMP/origin.git" rev-parse night)" = "$night_remote" ] || fail "base changed on refusal"
  [ -z "$(posted_events 76)" ] || fail "diverged open wrote spec.opened"
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

scenario_finishmerges() {
  local code merge base
  setup_finish_closed
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish merge failed: $(cat "$TMP/err")"
  merge="$(git -C "$TMP/origin.git" rev-parse proj)"; base="$(git -C "$TMP/origin.git" rev-parse "$merge^1")"
  [ "$(git -C "$TMP/origin.git" show -s --format=%s "$merge")" = "Merge branch 'night'" ] || fail "wrong merge subject"
  posted_events 76 into project merge base line | grep -qx "spec.merged into=night project=proj merge=$merge base=$base line=Merged night into proj: https://github.com/o/r/compare/$base...$merge (merge commit https://github.com/o/r/commit/$merge)" \
    || fail "spec.merged fields or links wrong: $(posted_events 76 into project merge base line)"
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
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night && fail "local night remains"
  git -C "$TMP/origin.git" show-ref --verify --quiet refs/heads/night && fail "origin night remains"
  [ ! -e "$TMP/repo/.worktrees/night-checkout" ] || fail "base worktree remains"
  [ ! -e "$TMP/repo/.worktrees/merge-night" ] || fail "base merge worktree remains"
  [ ! -e "$lock" ] || fail "base merge lock remains"
  [ -d "$main_path" ] || fail "main checkout was removed"
  return 0
}

scenario_finishrefusesunclosed() {
  local code before local_night
  fresh_project_night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log
  post_ev 76 spec.opened --ticket '' --spec 76 --line opened --field into=night --field project=proj
  before="$(git -C "$TMP/origin.git" show-ref | sort)"
  local_night="$(git -C "$TMP/repo" rev-parse night)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "unclosed finish expected 2, got $code"
  grep -q 'spec.closed' "$TMP/err" || fail "unclosed refusal missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" show-ref | sort)" = "$before" ] || fail "unclosed finish changed origin"
  [ "$(git -C "$TMP/repo" rev-parse night)" = "$local_night" ] || fail "unclosed finish changed local night"
}

scenario_finishrefusesopenticket() {
  local code before
  setup_finish_closed
  printf '%s\n' '[{"number":61,"state":"OPEN","labels":[]}]' > "$TMP/tickets.json"
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "open-ticket finish expected 2, got $code"
  grep -q '#61' "$TMP/err" || fail "open ticket number missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "open-ticket finish changed project"
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
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 2 ] || fail "no-project finish expected 2, got $code"
  grep -q 'open 76 again' "$TMP/err" || fail "no-project remedy missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "no-project finish changed project"
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
  mkdir -p "$TMP/repo/.mmw"; printf '%s\n' '{"checks":["echo RED-CHECK >&2; false"]}' > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json; git -C "$TMP/repo" commit -q -m checks; git -C "$TMP/repo" push -q -u origin proj
  git -C "$TMP/repo" checkout -q -b night; commit_file "$TMP/repo" night.txt night night; git -C "$TMP/repo" push -q -u origin night; git -C "$TMP/repo" checkout -q proj
  echo '[]' > "$TMP/tickets.json"; reset_log; closed_night_spec
  before="$(git -C "$TMP/origin.git" rev-parse proj)"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 1 ] || fail "red finish expected 1, got $code: $(cat "$TMP/err")"
  grep -q 'echo RED-CHECK' "$TMP/err" || fail "failed command missing: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$before" ] || fail "red finish changed project"
  posted_events 76 | grep -q spec.merged && fail "red finish wrote spec.merged"
  return 0
}

scenario_finishkeepsdirty() {
  local code dirty
  setup_finish_closed
  dirty="$TMP/repo/.worktrees/night-dirty"; mkdir -p "$TMP/repo/.worktrees"
  git -C "$TMP/repo" worktree add -q "$dirty" night
  printf 'dirty\n' > "$dirty/untracked.txt"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "dirty cleanup changed success: $(cat "$TMP/err")"
  [ -d "$dirty" ] || fail "dirty worktree was removed"
  grep -q "$dirty" "$TMP/err" || fail "dirty worktree path missing: $(cat "$TMP/err")"
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
  rm -f "$dirty/untracked.txt"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" bash "$DISPATCH" "${TOOLS[@]}" finish 76)"
  [ "$code" = 0 ] || fail "finish rerun failed: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse proj)" = "$first_merge" ] || fail "rerun made a second merge"
  [ ! -d "$dirty" ] || fail "rerun did not finish cleanup"
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night && fail "rerun left local night"
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
  git -C "$TMP/repo" show-ref --verify --quiet refs/heads/night && fail "contained local night remains"
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
  [ ! -d "$checked" ] || fail "clean base worktree was gated on branch containment"
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
  grep -q "local is 1 commit(s) ahead and origin is 2 commit(s) ahead" "$TMP/err" \
    || fail "both divergence counts were not reported: $(cat "$TMP/err")"
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
  grep -q "origin/local-only does not exist" "$TMP/err" \
    || fail "the missing remote base was not named: $(cat "$TMP/err")"
  assert_no_wt 61
}

scenario_adoptinto() {
  local code tree
  fresh_repo
  git -C "$TMP/repo" checkout -q -b adopted-base
  git -C "$TMP/repo" push -q -u origin adopted-base
  git -C "$TMP/repo" checkout -q main
  reset_log
  no_relay
  seed_main_agent agt_self
  self_picked_worktree
  tree="$(wt 61)"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self bash "$DISPATCH" "${TOOLS[@]}" adopt 61) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 2 ] || fail "adopt without --into expected 2, got $code"
  grep -q "pass --into <base branch>" "$TMP/err" \
    || fail "adopt did not ask for --into: $(cat "$TMP/err")"
  code="$( (cd "$tree" && env PASEO_AGENT_ID=agt_self bash "$DISPATCH" "${TOOLS[@]}" adopt 61 --into adopted-base) > "$TMP/out" 2> "$TMP/err"; echo "$?")"
  [ "$code" = 0 ] || fail "adopt --into expected 0, got $code: $(cat "$TMP/err")"
  posted_events 61 into | grep -qx "worker.started into=adopted-base" \
    || fail "adopt did not record into=adopted-base: $(posted_events 61 into)"
  assert_no_retired_base_config "$TMP/repo" 61 adopt
  no_relay
}

scenario_startwithoutinto() {
  local code
  fresh_repo
  reset_log
  post_ev 61 worker.started --ticket 61 --line "old worker" \
    --field session=old --field runner=paseo \
    $(start_facts "$(wt 61)" 61 worker) --field into=
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 2 ] || fail "old worker.started without into expected 2, got $code"
  grep -q "carries no into; re-start the worker" "$TMP/err" \
    || fail "the migration refusal was not actionable: $(cat "$TMP/err")"
  never_ran
}

scenario_replacepushes() {
  local code other
  fresh_repo
  reset_log
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "first start expected 0, got $code: $(cat "$TMP/err")"
  printf 'handoff\n' > "$(wt 61)/handoff.txt"
  git -C "$(wt 61)" add handoff.txt
  code="$(run_dispatch bash "$DISPATCH" "${TOOLS[@]}" start 61 worker)"
  [ "$code" = 0 ] || fail "replacement expected 0, got $code: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" show issue-61:handoff.txt | grep -qx handoff \
    || fail "replacement did not push the committed handoff"
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 \
    | grep -q '^wip(#61): uncommitted work of worker .* on paseo, left when it was replaced$' \
    || fail "replacement did not push the named wip commit"

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
  git -C "$TMP/origin.git" log -1 --format=%s issue-61 | grep -q '^wip(#61): uncommitted work of ' \
    || fail "retract did not push the named wip commit"
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
  grep -q "nothing was force-pushed" "$TMP/err" \
    || fail "the rejection did not state the no-force rule: $(cat "$TMP/err")"
  grep -Eq 'fetch first|non-fast-forward|rejected' "$TMP/err" \
    || fail "the git rejection reason was cut off: $(cat "$TMP/err")"
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
  seed_workspace 61
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

setup_checked_ticket() {
  local check="$1"
  reset_log
  fresh_repo
  mkdir -p "$TMP/repo/.mmw"
  printf '{"checks":[%s]}\n' "$(MMW_VALUE="$check" python3 -c 'import json, os; print(json.dumps(os.environ["MMW_VALUE"]))')" \
    > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m checks
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  local passed
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
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

scenario_advanceskipsecondcheck() {
  setup_checked_ticket "echo ran > '$TMP/check-ran'; exit 1"
  local passed checked code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  checked="$(ev ticket.checked 61 "Repository checks passed" --field run=repo-checks \
    --field "commit=$passed" --field result=met)"
  write_one_passed 61 "$passed" "$checked"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "the proven tree should land without a second check: $(cat "$TMP/err")"
  [ ! -e "$TMP/check-ran" ] || fail "the repository check ran a second time"

  setup_checked_ticket "printf 'reran\\n' > '$TMP/check-ran'"
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  checked="$(ev ticket.checked 61 "Repository checks passed" --field run=repo-checks \
    --field "commit=$passed" --field result=met)"
  write_one_passed 61 "$passed" "$checked"
  local other
  other="$(other_clone)"
  commit_file "$other" sibling.txt sibling sibling
  git -C "$other" push -q origin main
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a changed origin base should be rechecked: $(cat "$TMP/err")"
  [ "$(cat "$TMP/check-ran" 2>/dev/null)" = reran ] \
    || fail "the repository check was reused after origin/main advanced"
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

scenario_advancenochecks() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  local passed code
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "a repository without checks should land: $(cat "$TMP/err")"
  grep -q '没有检查：.mmw/target.json 没声明 checks' "$TMP/err" \
    || fail "the absence of checks was silent: $(cat "$TMP/err")"
  git -C "$TMP/origin.git" merge-base --is-ancestor "$passed" main \
    || fail "the ticket did not land without repository checks"

  reset_log
  fresh_repo
  mkdir -p "$TMP/repo/.mmw"
  printf '%s\n' '[]' > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json
  git -C "$TMP/repo" -c user.email=t@t -c user.name=t commit -q -m malformed-target
  git -C "$TMP/repo" push -q origin main
  make_branch issue-61 ticket.txt ticket
  local before
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  before="$(git -C "$TMP/origin.git" rev-parse main)"
  write_one_passed 61 "$passed"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "an unreadable checks declaration should bounce: $(cat "$TMP/err")"
  [ "$(git -C "$TMP/origin.git" rev-parse main)" = "$before" ] \
    || fail "a top-level non-object target.json moved origin/main"
  posted_events 61 reason commands | grep -q 'ticket.bounced reason=checks' \
    || fail "the malformed target.json was treated as no checks"
}

scenario_advanceraced() {
  reset_log
  fresh_repo
  mkdir -p "$TMP/repo/.mmw"
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
  printf '{"checks":["bash race-check.sh"]}\n' > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json race-check.sh
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
  mkdir -p "$TMP/repo/.mmw"
  cat > "$TMP/repo/slow-check.sh" <<'SH'
#!/usr/bin/env bash
echo "start $MMW_BASE_REF" >> "$MMW_OVERLAP_LOG"
sleep 3
echo "end $MMW_BASE_REF" >> "$MMW_OVERLAP_LOG"
SH
  printf '{"checks":["bash slow-check.sh"]}\n' > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json slow-check.sh
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
  [ "$(landed_first_line 61)" = "Landed issue-61 into main: https://github.example/o/r/compare/$base...$merge (merge commit https://github.example/o/r/commit/$merge)" ] \
    || fail "landing links are wrong: $(landed_first_line 61)"
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
  [ "$(landed_first_line 61)" = "Landed issue-61 into main" ] \
    || fail "a failed URL lookup left a partial link: $(landed_first_line 61)"
  posted_events 61 base merge | grep -qx "ticket.landed base=$base merge=$merge" \
    || fail "URL failure omitted landing fields: $(posted_events 61 base merge)"
  grep -q "without compare or commit links" "$TMP/err" \
    || fail "URL lookup failure was silent: $(cat "$TMP/err")"
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
  [ "$(landed_first_line 61)" = "Landed issue-61 into main: https://github.com/o/r/commit/$passed" ] \
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

scenario_landdeletesbranch() {
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
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "one-ticket landing failed: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_no_branch 61
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
  seed_agent 61 verifier
  local code kind
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "bounced landing failed: $(cat "$TMP/err")"
  for kind in worker reviewer verifier; do
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
  seed_agent 61 verifier
  post_ev 61 ticket.returned --ticket 61 --spec 76 \
    --line "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1"
  local code kind
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "advance of a returned ticket failed: $(cat "$TMP/err")"
  for kind in worker reviewer verifier; do
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

scenario_archiveremovesinstance() {
  rm -f "$TMP/fake/skills/verify-ticket/scripts/verify-ticket.py"
  reset_log
  fresh_repo
  make_branch issue-64 four.txt "from 64"
  write_landable
  seed_workspace 64
  local data code
  data="$(python3 "$LEASE_PY" env "$(wt 64)" | sed -n 's/^MMW_DATA_DIR=//p')"
  [ -d "$data" ] || fail "the fixture did not create its instance data directory"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" land 64)"
  [ "$code" = 0 ] || fail "land failed: $(cat "$TMP/err")"
  [ ! -e "$data" ] || fail "archiving left instance data at $data"
}

scenario_bouncekeepsinstance() {
  setup_bounced_conflict
  local data code
  data="$(python3 "$LEASE_PY" env "$(wt 61)" | sed -n 's/^MMW_DATA_DIR=//p')"
  [ -d "$data" ] || fail "the fixture did not create its instance data directory"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "bounce failed: $(cat "$TMP/err")"
  posted_events 61 reason | grep -q '^ticket\.bounced reason=' \
    || fail "the ticket was not recorded bounced: $(posted_events 61 reason)"
  [ -d "$data" ] || fail "bouncing removed instance data at $data"
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
  grep -q "origin/issue-61.*1 commit(s) not in origin/main" "$TMP/err" \
    || fail "stderr did not quantify the retained work: $(cat "$TMP/err")"
}

setup_branch_race_check() {
  fresh_repo
  mkdir -p "$TMP/repo/.mmw"
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
  printf '{"checks":["bash branch-race.sh"]}\n' > "$TMP/repo/.mmw/target.json"
  git -C "$TMP/repo" add .mmw/target.json branch-race.sh
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
  grep -q "could not delete origin/issue-61" "$TMP/err" \
    || fail "lease rejection was not reported: $(cat "$TMP/err")"
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
  grep -Eq 'keeping (local |origin/)?issue-61|could not delete .*issue-61' "$TMP/err" \
    && fail "an already-gone remote was reported as retained: $(cat "$TMP/err")"
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
}

scenario_landeddeleterefusedsays() {
  scenario_landeddeleterefused
  grep -q "protected branch refuses deletion" "$TMP/err" \
    || fail "the remote reason was omitted: $(cat "$TMP/err")"
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

scenario_landedworktreekept() {
  reset_log
  fresh_repo
  make_branch issue-61 ticket.txt ticket
  git -C "$TMP/repo" push -q -u origin issue-61
  assert_remote_branch 61
  local passed code ws port listener
  passed="$(git -C "$TMP/repo" rev-parse issue-61)"
  write_one_passed 61 "$passed"
  seed_workspace 61
  ws="$(wt 61)"
  mkdir -p "$ws/.mmw"
  printf '%s\n' '{"stop":"true"}' > "$ws/.mmw/target.json"
  port="$(python3 "$LEASE_PY" claim "$ws" | python3 -c 'import json,sys; print(json.load(sys.stdin)["port_base"])')"
  python3 -m http.server "$port" --bind 127.0.0.1 --directory "$TMP" >/dev/null 2>&1 &
  listener=$!
  local waited=0
  until python3 - "$port" <<'PY'
import socket, sys
try:
    socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=0.1).close()
except OSError:
    raise SystemExit(1)
PY
  do
    sleep 0.1
    waited=$((waited + 1))
    [ "$waited" -lt 50 ] || { fail "the test listener never came up"; break; }
  done
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" advance 76)"
  [ "$code" = 0 ] || fail "kept workspace changed landing success: $(cat "$TMP/err")"
  assert_wt 61
  assert_branch 61
  assert_remote_branch 61
  grep -q "keeps its workspace" "$TMP/err" \
    || fail "kept workspace was not reported: $(cat "$TMP/err")"
  kill "$listener" 2>/dev/null || true
  wait "$listener" 2>/dev/null || true
  : > "$MMW_TEST_LOG"
  : > "$MMW_GH_LAST_BODY"
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" MMW_LEASE_SLOTS=1 \
          bash "$DISPATCH" "${TOOLS[@]}" land 61)"
  [ "$code" = 0 ] || fail "archive retry failed: $(cat "$TMP/err")"
  assert_no_wt 61
  assert_no_branch 61
  [ "$(posted_events 61 | grep -c '^ticket\.landed' | tr -d ' ')" = 1 ] \
    || fail "archive retry wrote a second ticket.landed: $(posted_events 61)"
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
  code="$(run_dispatch env FAKE_GH_TICKETS_FILE="$TMP/tickets.json" \
          bash "$copy/scripts/dispatch.sh" "${TOOLS[@]}" reverify 76)"
  [ "$code" = 0 ] || fail "reverify expected 0: $(cat "$TMP/err")"
  posted_events 61 run commit | grep -qx "ticket.checked run=reverify commit=$remote_head" \
    || fail "reverify did not run on origin/main: $(posted_events 61 run commit)"
}

scenario_summarybounced() {
  reset_log
  fresh_repo
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

ALL="boardregisters boardsameport boardopenstab boardprintsurl installboardagent installcheckboardagent startreadsmodelsjson startnomodelsjson installimportsmodelsmd installinitialvalues installkeepsmodelsjson installcheckmodelsjson installmodelsjsonhome installkeepsnewestbackup orcaworktreelink orcaworktreelinkfails worktreelinknoop check checknoorigin checknopush checkbasemissing checklocalahead advance advanceconflict advancedirty advancemergeworktree advancepassedcommit advanceunreadableinto advancewithoutpassedcommit advancebouncedconflict advancenohalfmerge advancebouncedchecks advanceskipsecondcheck advancebaseref advancenochecks advanceraced advancelandedfields parallelbases advancealreadyin landedlinks landednourl alreadyinmerge alreadyinfastforward landeddeletesbranch landdeletesbranch bouncedkeepsbranch bouncestopssessions returnedstopssessions archiveremovesinstance bouncekeepsinstance sweepsorphanmerge sweepkeepslockedmerge landedkeepsunmerged landedbranchraced landedbranchgone landeddeleterefused landeddeleterefusedsays archiveunlandedkeepsbranch landedworktreekept regressedrestart advancesummaryline bouncednotretried landviaorigin reverifyorigin summarybounced integrateuptodate integrateclean integratenamestickets integrateconflict integratedirty reviewerbaseafterintegrate reviewerbasefromstarted nobaseconfig land start-worker start-reviewer start-verifier startfromorigin startresumesorigin startdiverged startintofromnight startintooutside startwithoutinto replacepushes retract retractpushes resume wait reverify summary release releaseother releaselive releasestanding frontierwhy slotatclaim route specfield stopproduct suspend suspendpushes suspendbusy handoffpushrejected status runnerstart runnersend runnerliveness runnerparity herdrworkingsend herdrliveness orcasend orcaclosed worktreegit worktreegoverned worktreeremove installorca usesagree usesmismatch usesunreadable paseostartdir landarchivesagents noadapterretract noadapterwait unknownnotalive herdrunreadablelist herdrnoeffort herdrstartloud orcatruncated orcanotconnected orcanoorphan orcanohosts installorcashape usesnorunners usesorcaunreadable startreturnssession startonce runneronticket runnerstop orcadoubledispatch unreadableevents startunrecorded mergewithoutbranch retractunreadable open openinto openpushesahead openprojectreflog openprojectconfig openprojecthistory openprojecttie openrefusesdefault openrefusesfromdefault openpushes openrefusesdiverged openkeepsproject checkproject openrefused openticket ack unopened runnerself orcaunobserved adopt adoptinto orcarefusalreason nightfromtask keepunfinished advancerefused catalogbyrunner startunlandedblocker"
ALL="$ALL openprojecthead finishmerges finishcleans finishrefusesunclosed finishrefusesopenticket finishrefusesothernight finishrefusesnoproject finishconflict finishred finishkeepsdirty finishrerun finishcontained finishrefusesunreadablespec finishcleanupindependent"

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
    boardregisters) echo BOARD-REGISTERS-OK ;;
    boardsameport) echo BOARD-SAME-PORT-OK ;;
    boardopenstab) echo BOARD-OPENS-TAB-OK ;;
    boardprintsurl) echo BOARD-PRINTS-URL-OK ;;
    installboardagent) echo INSTALL-BOARD-AGENT-OK ;;
    installcheckboardagent) echo INSTALL-CHECK-BOARD-AGENT-OK ;;
    startreadsmodelsjson) echo START-READS-MODELS-JSON-OK ;;
    startnomodelsjson) echo START-NO-MODELS-JSON-OK ;;
    installimportsmodelsmd) echo INSTALL-IMPORTS-MODELS-MD-OK ;;
    installinitialvalues) echo INSTALL-INITIAL-VALUES-OK ;;
    installkeepsmodelsjson) echo INSTALL-KEEPS-MODELS-JSON-OK ;;
    installcheckmodelsjson) echo INSTALL-CHECK-MODELS-JSON-OK ;;
    installmodelsjsonhome) echo INSTALL-MODELS-JSON-HOME-OK ;;
    installkeepsnewestbackup) echo INSTALL-KEEPS-NEWEST-BACKUP-OK ;;
    orcaworktreelink) echo ORCA-WORKTREE-LINK-OK ;;
    orcaworktreelinkfails) echo ORCA-WORKTREE-LINK-FAILS-OK ;;
    worktreelinknoop) echo WORKTREE-LINK-NOOP-OK ;;
    check) echo DISPATCH-CHECK-OK ;;
    checknoorigin) echo CHECK-NO-ORIGIN-OK ;;
    checknopush) echo CHECK-NO-PUSH-OK ;;
    checkbasemissing) echo CHECK-BASE-MISSING-OK ;;
    checklocalahead) echo CHECK-LOCAL-AHEAD-OK ;;
    advance) echo DISPATCH-ADVANCE-OK ;;
    advanceconflict) echo DISPATCH-ADVANCE-CONFLICT-OK ;;
    advancedirty) echo DISPATCH-ADVANCE-DIRTY-OK ;;
    advancemergeworktree) echo ADVANCE-MERGE-WORKTREE-OK ;;
    advancepassedcommit) echo ADVANCE-PASSED-COMMIT-OK ;;
    advanceunreadableinto) echo ADVANCE-UNREADABLE-INTO-OK ;;
    advancewithoutpassedcommit) echo ADVANCE-WITHOUT-PASSED-COMMIT-OK ;;
    advancebouncedconflict) echo ADVANCE-BOUNCED-CONFLICT-OK ;;
    advancenohalfmerge) echo ADVANCE-NO-HALF-MERGE-OK ;;
    advancebouncedchecks) echo ADVANCE-BOUNCED-CHECKS-OK ;;
    advanceskipsecondcheck) echo ADVANCE-SKIP-SECOND-CHECK-OK ;;
    advancebaseref) echo ADVANCE-BASE-REF-OK ;;
    advancenochecks) echo ADVANCE-NO-CHECKS-OK ;;
    advanceraced) echo ADVANCE-RACED-OK ;;
    advancelandedfields) echo ADVANCE-LANDED-FIELDS-OK ;;
    advancealreadyin) echo ADVANCE-ALREADY-IN-OK ;;
    landedlinks) echo LANDED-LINKS-OK ;;
    landednourl) echo LANDED-NO-URL-OK ;;
    alreadyinmerge) echo ALREADY-IN-MERGE-OK ;;
    alreadyinfastforward) echo ALREADY-IN-FAST-FORWARD-OK ;;
    landeddeletesbranch) echo LANDED-DELETES-BRANCH-OK ;;
    landdeletesbranch) echo LAND-DELETES-BRANCH-OK ;;
    bouncedkeepsbranch) echo BOUNCED-KEEPS-BRANCH-OK ;;
    bouncestopssessions) echo BOUNCE-STOPS-SESSIONS-OK ;;
    returnedstopssessions) echo RETURNED-STOPS-SESSIONS-OK ;;
    archiveremovesinstance) echo ARCHIVE-REMOVES-INSTANCE-OK ;;
    bouncekeepsinstance) echo BOUNCE-KEEPS-INSTANCE-OK ;;
    sweepsorphanmerge) echo SWEEPS-ORPHAN-MERGE-OK ;;
    sweepkeepslockedmerge) echo SWEEP-KEEPS-LOCKED-MERGE-OK ;;
    landedkeepsunmerged) echo LANDED-KEEPS-UNMERGED-OK ;;
    landedbranchraced) echo LANDED-BRANCH-RACED-OK ;;
    landedbranchgone) echo LANDED-BRANCH-GONE-OK ;;
    landeddeleterefused) echo LANDED-DELETE-REFUSED-OK ;;
    landeddeleterefusedsays) echo LANDED-DELETE-REFUSED-SAYS-OK ;;
    archiveunlandedkeepsbranch) echo ARCHIVE-UNLANDED-KEEPS-BRANCH-OK ;;
    landedworktreekept) echo LANDED-WORKTREE-KEPT-OK ;;
    regressedrestart) echo REGRESSED-RESTART-OK ;;
    parallelbases) echo PARALLEL-BASES-OK ;;
    advancesummaryline) echo ADVANCE-SUMMARY-LINE-OK ;;
    bouncednotretried) echo BOUNCED-NOT-RETRIED-OK ;;
    landviaorigin) echo LAND-VIA-ORIGIN-OK ;;
    reverifyorigin) echo REVERIFY-ORIGIN-OK ;;
    summarybounced) echo SUMMARY-BOUNCED-OK ;;
    integrateuptodate) echo INTEGRATE-UP-TO-DATE-OK ;;
    integrateclean) echo INTEGRATE-CLEAN-OK ;;
    integratenamestickets) echo INTEGRATE-NAMES-TICKETS-OK ;;
    integrateconflict) echo INTEGRATE-CONFLICT-OK ;;
    integratedirty) echo INTEGRATE-DIRTY-OK ;;
    reviewerbaseafterintegrate) echo REVIEWER-BASE-AFTER-INTEGRATE-OK ;;
    reviewerbasefromstarted) echo REVIEWER-BASE-FROM-STARTED-OK ;;
    nobaseconfig) echo NO-BASE-CONFIG-OK ;;
    land) echo DISPATCH-LAND-OK ;;
    start-worker) echo DISPATCH-START-WORKER-OK ;;
    start-reviewer) echo DISPATCH-START-REVIEWER-OK ;;
    start-verifier) echo DISPATCH-START-VERIFIER-OK ;;
    startfromorigin) echo START-FROM-ORIGIN-OK ;;
    startresumesorigin) echo START-RESUMES-ORIGIN-OK ;;
    startdiverged) echo START-DIVERGED-OK ;;
    startintofromnight) echo START-INTO-FROM-NIGHT-OK ;;
    startintooutside) echo START-INTO-OUTSIDE-OK ;;
    startwithoutinto) echo START-WITHOUT-INTO-OK ;;
    replacepushes) echo REPLACE-PUSHES-OK ;;
    retract) echo DISPATCH-RETRACT-OK ;;
    retractpushes) echo RETRACT-PUSHES-OK ;;
    resume) echo DISPATCH-RESUME-OK ;;
    wait) echo DISPATCH-WAIT-OK ;;
    reverify) echo DISPATCH-REVERIFY-OK ;;
    summary) echo DISPATCH-SUMMARY-OK ;;
    release) echo DISPATCH-RELEASE-OK ;;
    releaseother) echo DISPATCH-RELEASE-OTHER-OK ;;
    releaselive) echo RELEASE-LIVE-OK ;;
    releasestanding) echo RELEASE-STANDING-OK ;;
    frontierwhy) echo DISPATCH-FRONTIER-WHY-OK ;;
    slotatclaim) echo SLOT-AT-CLAIM-OK ;;
    route) echo ROUTE-OK ;;
    specfield) echo SPEC-FIELD-OK ;;
    stopproduct) echo STOP-PRODUCT-OK ;;
    suspend) echo SUSPEND-OK ;;
    suspendpushes) echo SUSPEND-PUSHES-OK ;;
    suspendbusy) echo SUSPEND-BUSY-OK ;;
    handoffpushrejected) echo HANDOFF-PUSH-REJECTED-OK ;;
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
    orcarefusalreason) echo ORCA-REFUSAL-REASON-OK ;;
    nightfromtask) echo NIGHT-FROM-TASK-OK ;;
    keepunfinished) echo KEEP-UNFINISHED-OK ;;
    advancerefused) echo ADVANCE-REFUSED-OK ;;
    catalogbyrunner) echo CATALOG-BY-RUNNER-OK ;;
    startunlandedblocker) echo START-UNLANDED-BLOCKER-OK ;;
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
    openinto) echo OPEN-INTO-OK ;;
    openpushesahead) echo OPEN-PUSHES-AHEAD-OK ;;
    openprojectreflog) echo OPEN-PROJECT-REFLOG-OK ;;
    openprojectconfig) echo OPEN-PROJECT-CONFIG-OK ;;
    openprojecthistory) echo OPEN-PROJECT-HISTORY-OK ;;
    openprojecttie) echo OPEN-PROJECT-TIE-OK ;;
    openrefusesdefault) echo OPEN-REFUSES-DEFAULT-OK ;;
    openrefusesfromdefault) echo OPEN-REFUSES-FROM-DEFAULT-OK ;;
    openpushes) echo OPEN-PUSHES-OK ;;
    openrefusesdiverged) echo OPEN-REFUSES-DIVERGED-OK ;;
    openkeepsproject) echo OPEN-KEEPS-PROJECT-OK ;;
    checkproject) echo CHECK-PROJECT-OK ;;
    openprojecthead) echo OPEN-PROJECT-HEAD-OK ;;
    finishmerges) echo FINISH-MERGES-OK ;;
    finishcleans) echo FINISH-CLEANS-OK ;;
    finishrefusesunclosed) echo FINISH-REFUSES-UNCLOSED-OK ;;
    finishrefusesopenticket) echo FINISH-REFUSES-OPEN-TICKET-OK ;;
    finishrefusesothernight) echo FINISH-REFUSES-OTHER-NIGHT-OK ;;
    finishrefusesnoproject) echo FINISH-REFUSES-NO-PROJECT-OK ;;
    finishconflict) echo FINISH-CONFLICT-OK ;;
    finishred) echo FINISH-RED-OK ;;
    finishkeepsdirty) echo FINISH-KEEPS-DIRTY-OK ;;
    finishrerun) echo FINISH-RERUN-OK ;;
    finishcontained) echo FINISH-CONTAINED-OK ;;
    finishrefusesunreadablespec) echo FINISH-REFUSES-UNREADABLE-SPEC-OK ;;
    finishcleanupindependent) echo FINISH-CLEANUP-INDEPENDENT-OK ;;
    openrefused) echo OPEN-REFUSED-OK ;;
    openticket) echo OPEN-TICKET-OK ;;
    ack) echo ACK-OK ;;
    unopened) echo UNOPENED-OK ;;
    runnerself) echo RUNNER-SELF-OK ;;
    orcaunobserved) echo ORCA-UNOBSERVED-OK ;;
    adopt) echo ADOPT-OK ;;
    adoptinto) echo ADOPT-INTO-OK ;;
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
