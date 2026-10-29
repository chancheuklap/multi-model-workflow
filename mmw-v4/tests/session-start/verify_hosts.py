#!/usr/bin/env python3
"""Probe real CLI hook delivery using temporary configuration and glossary repositories.

Run from any checkout with both CLIs installed and already logged in. Codex auth.json
is copied with mode 0600. Claude uses an existing token or a keychain credential in
an environment variable. Neither credentials nor raw host logs enter the report.
Installation uses the install suite's fake system tools and throwaway home. Native
host events pass through capture wrappers to the actual candidate hook. The old
comparison replays the v4 hook at BASE in the same isolated setup, not a historical
installer. No live hook, installed-root, watch or login configuration is changed.

The JSON evidence records exact prompts, replies, hook payload fields and outputs.
Required cases fail closed. Compaction attempts have a separate limitations record.
This small sample is an observation, not a guarantee of future prose quality.
"""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

V4 = Path(__file__).resolve().parents[2]
BASE = "8cc6702d0b989477f70e1d7ba8487944d02fd30f"
QUESTIONS = [
    "What does a review packet contain? Answer in one short sentence.",
    "Give me a short implementation report for the review packet. The local check has passed "
    "and no release has happened.",
    "For the delivery window, should delivery run as soon as a packet passes or wait for the "
    "window? Choose the option consistent with the project's definition and explain why.",
    "Explain the delivery window page in two sentences. Tell me what a review packet on that "
    "page means without asking me to look back at another answer.",
]

CAPTURE = '''import json, os, subprocess, sys
from pathlib import Path
payload = json.load(sys.stdin)
event = payload["hook_event_name"]
mode = os.environ["MMW_PROBE_MODE"]
root = Path(os.environ["MMW_PROBE_ROOT"])
if event == "Stop":
    args = ([str(root / "old-reply.py"), "stop", sys.argv[1]] if mode == "old" else
            [os.environ["MMW_PROBE_GUARD"], "stop", sys.argv[1]])
else:
    args = [str(root / ("old-start.py" if mode == "old" else "session-context.py")), sys.argv[1]]
raw = "[" if (root / "fail").exists() and event != "Stop" else json.dumps(payload)
run = subprocess.run([sys.executable, *args], input=raw, text=True, capture_output=True)
row = {key: payload[key] for key in ("hook_event_name", "source", "stop_hook_active", "cwd")
       if key in payload}
row.update(exit=run.returncode, stdout=run.stdout, stderr=run.stderr)
with (root / "events.jsonl").open("a") as stream:
    stream.write(json.dumps(row) + "\\n")
sys.stdout.write(run.stdout)
sys.stderr.write(run.stderr)
sys.exit(run.returncode)
'''


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class JsonProcess:
    def __init__(self, command, cwd, env):
        self.errors = subprocess.DEVNULL
        self.proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=self.errors, text=True, bufsize=1)
        self.lines = queue.Queue()
        self.seen = []

        def read():
            for line in self.proc.stdout:
                try:
                    self.lines.put(json.loads(line))
                except ValueError:
                    self.lines.put({"invalid_json": True})
            self.lines.put(None)

        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()

    def send(self, value):
        self.proc.stdin.write(json.dumps(value) + "\n")
        self.proc.stdin.flush()

    def until(self, predicate, timeout=180):
        deadline = time.monotonic() + timeout
        while True:
            try:
                row = self.lines.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                raise RuntimeError("host did not complete its requested event before the timeout") from None
            require(row is not None, "host exited before its requested event")
            require("invalid_json" not in row, "host returned a non-JSON protocol line")
            self.seen.append(row)
            if predicate(row):
                return row
            require(time.monotonic() < deadline, "host event deadline exceeded")

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.reader.join(timeout=1)


class Codex(JsonProcess):
    def __init__(self, binary, cwd, env):
        super().__init__([binary, "app-server"], cwd, env)
        self.ident = 0
        self.call("initialize", {"clientInfo": {"name": "mmw_hook_probe", "version": "1"}})
        self.send({"method": "initialized"})
        self.thread = None

    def call(self, method, params):
        self.ident += 1
        self.send({"id": self.ident, "method": method, "params": params})
        row = self.until(lambda row: row.get("id") == self.ident)
        require("error" not in row, f"Codex rejected {method}")
        return row["result"]

    def start(self, cwd, instructions):
        result = self.call("thread/start", {"cwd": str(cwd), "approvalPolicy": "never",
                           "sandbox": "read-only", "developerInstructions": instructions,
                           "model": "gpt-6.1-sol", "config": {"model_reasoning_effort": "high"}})
        self.thread = result["thread"]["id"]

    def resume(self, thread):
        self.call("thread/resume", {"threadId": thread})
        self.thread = thread

    def prompt(self, text):
        start = len(self.seen)
        self.call("turn/start", {"threadId": self.thread,
                                "input": [{"type": "text", "text": text}]})
        row = self.until(lambda row: row.get("method") == "turn/completed")
        require(row["params"]["turn"]["status"] == "completed", "Codex turn failed")
        messages = [r["params"]["item"] for r in self.seen[start:]
                    if r.get("method") == "item/completed"]
        replies = [m["text"] for m in messages if m.get("type") == "agentMessage"]
        require(replies, "Codex completed without an answer")
        reads = [m.get("command", "") for m in messages if m.get("type") == "commandExecution"]
        return {"reply": replies[-1], "reads": reads}

    def compact(self):
        self.call("thread/compact/start", {"threadId": self.thread})
        self.until(lambda row: row.get("method") == "turn/completed")


class Claude(JsonProcess):
    def __init__(self, binary, cwd, env, settings, instructions, session=None):
        command = [binary, "-p", "--setting-sources", "", "--settings", str(settings),
                   "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                   "--include-hook-events", "--tools", "Read", "--allowedTools", "Read",
                   "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                   "--model", "sonnet", "--effort", "high", "--append-system-prompt", instructions]
        if session:
            command += ["--resume", session]
        super().__init__(command, cwd, env)
        self.session = session

    def prompt(self, text):
        start = len(self.seen)
        self.send({"type": "user", "message": {"role": "user", "content": text}})
        row = self.until(lambda row: row.get("type") == "result")
        if row.get("is_error"):
            if "This organization has been disabled" in row.get("result", ""):
                raise RuntimeError("Claude inference rejected the existing login because its organization is disabled")
            raise RuntimeError("Claude turn failed or authentication is unavailable")
        self.session = row["session_id"]
        reads = [part["input"].get("file_path", "") for r in self.seen[start:]
                 if r.get("type") == "assistant" for part in r.get("message", {}).get("content", [])
                 if part.get("type") == "tool_use" and part.get("name") == "Read"]
        return {"reply": row.get("result", ""), "reads": reads}


def fixture():
    spec = importlib.util.spec_from_file_location("install_fixture", V4 / "tests/install/test_install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    case = module.InstallTest()
    case.setUp()
    case.home = case.home.resolve()
    env = case.env()
    env.update(CODEX_HOME=str(case.home / ".codex"), MMW_HOME=str(case.home / ".mmw"))
    installed = case.run_install("v4", env=env)
    require(installed.returncode == 0, "isolated installer failed; run the installer suite")
    return case, env


def login(env):
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    auth = codex_home / "auth.json"
    require(auth.is_file(), "Codex auth.json is absent; log in to Codex before running the probe")
    target = Path(env["CODEX_HOME"]) / "auth.json"
    target.write_bytes(auth.read_bytes())
    target.chmod(0o600)
    if not env.get("CLAUDE_CODE_OAUTH_TOKEN") and not env.get("ANTHROPIC_API_KEY"):
        credentials = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / ".credentials.json"
        if credentials.is_file():
            data = json.loads(credentials.read_text())
        else:
            require(shutil.which("security"), "Claude login unavailable; set an existing login token")
            run = subprocess.run(["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                                 capture_output=True, text=True)
            require(run.returncode == 0, "Claude login is absent from the keychain")
            data = json.loads(run.stdout)
        token = data.get("claudeAiOauth", {}).get("accessToken")
        require(token, "Claude login has no access token")
        env["CLAUDE_CODE_OAUTH_TOKEN"] = token


def prepare(case, env, mode):
    root = case.home / "probe mmw"
    scripts = root / "mmw-v4/skills/mmw-mode/scripts"
    scripts.mkdir(parents=True)
    (root / "CONTEXT.md").write_text("# Probe MMW\n\n**host**:\nThe CLI running this isolated probe.\n")
    (scripts.parent / "SKILL.md").write_text(
        "# Isolated probe\n\nAnswer the owner's question about the temporary notes project. "
        "Read only the temporary project files. Start no agent and run no workflow.\n")
    shutil.copy2(V4 / "skills/mmw-mode/scripts/session-start.py", scripts / "session-context.py")
    for name, output in (("session-start.py", "old-start.py"), ("reply-check.py", "old-reply.py")):
        old = subprocess.run(["git", "show", f"{BASE}:mmw-v4/skills/mmw-mode/scripts/{name}"],
                             cwd=V4, capture_output=True, check=True)
        (scripts / output).write_bytes(old.stdout)
    skills = scripts.parents[1]
    for name in ("principle-anchor-every-reference", "principle-everything-at-hand"):
        (skills / name).symlink_to(V4 / "skills" / name, target_is_directory=True)
    (skills / "dispatch").symlink_to(V4 / "skills/dispatch", target_is_directory=True)
    neutral = case.home / ".agents/skills"
    (neutral / "mmw-mode").unlink()
    (neutral / "mmw-mode").symlink_to(scripts.parent)
    (scripts / "session-start.py").write_text(CAPTURE)
    dispatch = neutral / "dispatch"
    dispatch.unlink()
    (dispatch / "scripts").mkdir(parents=True)
    (dispatch / "scripts/turn-guard.py").write_text(CAPTURE)
    for config in (case.home / ".claude/settings.json", case.home / ".codex/hooks.json"):
        data = json.loads(config.read_text())
        data["hooks"] = {key: [g for g in groups if any(".agents/skills/" in h.get("command", "")
                                                      for h in g.get("hooks", []))]
                         for key, groups in data["hooks"].items()
                         if key in ("SessionStart", "UserPromptSubmit", "Stop")}
        if mode == "old":
            data["hooks"].pop("UserPromptSubmit", None)
        config.write_text(json.dumps(data))
    for prompt in (case.home / ".codex/AGENTS.md", case.home / ".claude/CLAUDE.md"):
        prompt.unlink(missing_ok=True)
    env.update(MMW_PROBE_ROOT=str(scripts), MMW_PROBE_MODE=mode,
               MMW_PROBE_GUARD=str(V4 / "skills/dispatch/scripts/turn-guard.py"),
               CLAUDE_CONFIG_DIR=str(case.home / ".claude"), PATH=os.environ["PATH"])
    repo = case.home / "notes project"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "CONTEXT-MAP.md").write_text(
        "# Notes project\n\n[Review](review/CONTEXT.md)\n[Delivery](delivery/CONTEXT.md)\n")
    for directory, text in (("review", "# Review\n\n**review packet**:\n"
                            "A checked note with its amber receipt, identified by cobalt-731. "
                            "It is ready for delivery but is not a release.\n_Avoid_: bundle\n"),
                            ("delivery", "# Delivery\n\n**delivery window**:\n"
                             "The owner's scheduled 17-minute delivery interval, identified by moss-482. "
                             "A passed review packet waits for this interval, rather than delivery immediately.\n"
                             "_Avoid_: queue slot\n")):
        (repo / directory).mkdir()
        (repo / directory / "CONTEXT.md").write_text(text)
    instructions = ("This is an isolated, read-only hook-delivery probe, not a workflow assignment. "
                    f"The mmw-mode skill for this probe is {scripts.parent / 'SKILL.md'}. "
                    "Answer the owner's questions about the temporary notes project. "
                    "Read only its files and this probe skill. Start no agents and change nothing.")
    return scripts, repo, instructions


def events(scripts):
    path = scripts / "events.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def run_host(host, binary, mode):
    case, env = fixture()
    clients = []
    try:
        login(env)
        scripts, repo, instructions = prepare(case, env, mode)

        def client(session=None):
            if host == "codex":
                value = Codex(binary, repo, env)
                clients.append(value)
                if session:
                    value.resume(session)
                else:
                    value.start(repo, instructions)
            else:
                value = Claude(binary, repo, env, case.home / ".claude/settings.json", instructions, session)
                clients.append(value)
            return value

        current = client()
        startup = current.prompt("Without using tools, quote only the first sentence supplied by the "
                                 "SessionStart hook. Ignore the UserPromptSubmit text for this quotation.")
        if mode == "new":
            require("Read the mmw-mode skill in full before anything else." in startup["reply"],
                    f"{host} did not receive SessionStart context")
        print(f"{host} {mode} startup turn completed", flush=True)
        per_turn = None
        if mode == "new":
            per_turn = current.prompt("Without using tools, quote only the first sentence supplied by the "
                                      "UserPromptSubmit hook for this turn.")
            require("source names and definitions" in per_turn["reply"],
                    f"{host} did not receive UserPromptSubmit context")
        answers = []
        for question in QUESTIONS:
            before = len(events(scripts))
            answer = current.prompt(question)
            answer["prompt"] = question
            answer["events"] = events(scripts)[before:]
            answers.append(answer)
            print(f"{host} {mode} owner question {len(answers)} completed", flush=True)
        session = current.thread if host == "codex" else current.session
        current.close()
        current = client(session)
        before = len(events(scripts))
        resumed = current.prompt("What does a review packet contain? Include its project identifier.")
        resumed["events"] = events(scripts)[before:]
        print(f"{host} {mode} resumed", flush=True)
        compaction = {"surface": "not attempted", "captured": False}
        if host == "codex" and mode == "new":
            try:
                current.compact()
                after_compact = current.prompt("Without tools, quote the hook sentence that tells you "
                                               "what to do after your context was compacted.")
                compaction = {"surface": "codex app-server thread/compact/start", "reply": after_compact["reply"],
                              "captured": any(e.get("source") == "compact" for e in events(scripts))}
            except RuntimeError as exc:
                compaction = {"surface": "codex app-server thread/compact/start", "captured": False,
                              "limitation": str(exc)}
        elif host == "claude" and mode == "new":
            try:
                compact_result = current.prompt("/compact")
                compaction = {"surface": "Claude print stream-json /compact", "reply": compact_result["reply"],
                              "captured": any(e.get("source") == "compact" for e in events(scripts))}
                if compaction["captured"]:
                    compaction["continuation"] = current.prompt(
                        "Without tools, quote the hook sentence about what to do after your context was compacted.")
                else:
                    compaction["limitation"] = "No SessionStart compact payload was observed. Process fixtures cover the schema."
            except RuntimeError as exc:
                compaction = {"surface": "Claude print stream-json /compact", "captured": False,
                              "limitation": str(exc)}
        failure = None
        if mode == "new":
            (scripts / "fail").touch()
            before = len(events(scripts))
            failure = current.prompt("Without tools, reply exactly AVAILABLE.")
            failure["events"] = events(scripts)[before:]
            require(failure["reply"].strip() == "AVAILABLE", f"{host} did not remain available on reminder failure")
            require(any(e["hook_event_name"] == "UserPromptSubmit" and e["exit"] == 0 and
                        e["stderr"] and not e["stdout"] for e in failure["events"]),
                    f"{host} failure probe did not exercise the advisory diagnostic")
            for index, token in ((0, "cobalt-731"), (2, "moss-482"), (3, "moss-482")):
                require(token in answers[index]["reply"], f"{host} did not use the requested glossary definition")
            require("cobalt-731" in resumed["reply"], f"{host} lost glossary use on resume")
            for answer in answers:
                require(any(e["hook_event_name"] == "Stop" and e["exit"] == 0 for e in answer["events"]),
                        f"{host} did not complete its turn through Stop")
                require(any(e["hook_event_name"] == "UserPromptSubmit" and 'Glossary entries:' in e["stdout"]
                            for e in answer["events"]), f"{host} did not deliver context on a successive turn")
            require(any(e.get("source") == "resume" for e in events(scripts)), f"{host} resume hook was not captured")
            require(not any(e.get("stop_hook_active") for e in events(scripts)),
                    f"{host} requested a Stop continuation with advisory hooks")
        all_events = events(scripts)
        if mode == "old":
            require(any(e["hook_event_name"] == "Stop" and e["exit"] == 2 for e in all_events),
                    f"{host} old comparison did not exercise reply-check")
            require(any(e.get("stop_hook_active") for e in all_events),
                    f"{host} old comparison did not capture a Stop continuation")
        return {"host": host, "mode": mode, "startup": startup, "per_turn": per_turn, "answers": answers, "resume": resumed,
                "failure": failure, "compaction": compaction, "events": all_events,
                "stop_blocks": sum(e["hook_event_name"] == "Stop" and e["exit"] == 2 for e in all_events),
                "continuations": sum(bool(e.get("stop_hook_active")) for e in all_events)}
    finally:
        for value in clients:
            value.close()
        case.tearDown()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=V4.parent / ".scratch/session-start-hosts/latest.json")
    parser.add_argument("--host", choices=("claude", "codex"), help="diagnose one host; never prints HOST CHECK PASS")
    parser.add_argument("--mode", choices=("new", "old"), help="diagnose one comparison; never prints HOST CHECK PASS")
    args = parser.parse_args()
    report = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "baseline": BASE,
              "versions": {}, "runs": []}
    try:
        for host in ((args.host,) if args.host else ("codex", "claude")):
            binary = shutil.which(host)
            require(binary, f"{host} is absent; install and log in before running the probe")
            version = subprocess.run([binary, "--version"], capture_output=True, text=True, check=True)
            report["versions"][host] = version.stdout.strip()
            for mode in ((args.mode,) if args.mode else ("new", "old")):
                print(f"Checking {host} {mode} hooks", flush=True)
                report["runs"].append(run_host(host, binary, mode))
        report["result"] = "diagnostic" if args.host or args.mode else "passed"
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        report["result"] = "failed"
        report["failure"] = str(exc)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"Evidence {args.evidence}")
    if report["result"] == "passed":
        print("HOST CHECK PASS")
        return 0
    if report["result"] == "failed":
        print(f"HOST CHECK FAIL {report['failure']}", file=sys.stderr)
        return 1
    print("Diagnostic complete; full two-host run required")
    return 0


if __name__ == "__main__":
    sys.exit(main())
