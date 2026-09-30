#!/usr/bin/env python3
"""Measure #611 in temporary repositories using the hosts' existing login.

Measurements, 2026-09-30:
Claude Code 2.1.285 returned fresh SessionStart (startup/resume/compact),
SubagentStart and UserPromptSubmit context markers; a fresh non-.mmw run returned NONE.
Grok 1.0.45 reads project skills/hooks with child-only GROK_FOLDER_TRUST=0,
without changing its folder-trust store; passive hook execution is not injection.
Codex 0.159.2 app-server initialize, thread/start, turn/start, item/completed
agentMessage, thread/compact/start and turn/completed ran with existing login,
ephemeral read-only threads: replies PROTOCOL-ONLY and PROTOCOL-AFTER surrounded
successful compaction. In a separate empty CODEX_HOME (no credentials copied),
the project trust and normalized hook hashes let SessionStart and UserPromptSubmit
run before the expected authentication failure. The full owner hook probe remains
unverified; these protocol checks do not prove its three capabilities.
Orca 1.4.215 refused temporary path selectors before host launch. Successful
Orca cleanup paths are exercised with a fake adapter, not claimed as real measurements.
Herdr 0.9.0's private headless server and a Grok 1.0.45 pane received two literal
lines in one UserPromptSubmit event; the pane and server were closed afterward.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from check_results import CONFIG_PATHS, SUBITEMS, report, verdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVENTS = ("SessionStart", "SubagentStart", "UserPromptSubmit")
RETAINED_DIRECTORIES = set()

# Read the machine selection before building a child's private MMW_HOME. This is
# the installed runtime, not the ticket's product copy, and never controls tickets.
sys.path.insert(0, str(Path("~/.agents/skills/dispatch/scripts").expanduser().resolve()))
import models
import statedir


@contextmanager
def temporary_directory():
    made = run(["mktemp", "-d"])
    if made.returncode:
        raise RuntimeError("mktemp -d failed: " + short(made.stderr))
    path = Path(made.stdout.strip()).resolve()
    try:
        yield path
    finally:
        if not any(directory.is_relative_to(path) for directory in RETAINED_DIRECTORIES):
            shutil.rmtree(path)


def run(argv, cwd=None, env=None):
    return subprocess.run(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True)


def short(text):
    return " ".join(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).split())


def checksum():
    return {name: hashlib.sha256(Path(name).expanduser().read_bytes()).hexdigest()
            if Path(name).expanduser().exists() else "absent" for name in CONFIG_PATHS}


def checksum_lines(phase, hashes):
    return [f"CHECKSUM {phase} {name} {value}" for name, value in hashes.items()]


def version(binary):
    if not shutil.which(binary):
        return "absent"
    result = run([binary, "--version"])
    return short(result.stdout or result.stderr).replace(" ", "_")


def marker():
    return "PROBE_" + uuid.uuid4().hex


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def prepare(host, repo, mmw_home):
    run(["git", "init", "-q", str(repo)])
    (repo / ".mmw").mkdir()
    skills = repo / (".claude/skills" if host == "claude" else ".agents/skills")
    playbook_mark, copy_mark = marker(), marker()
    description = "Use for the isolated mmw work-a-ticket#Claim probe."
    write(skills / "mmw/SKILL.md", f"---\nname: mmw\ndescription: {description}\n---\n"
          "# MMW probe\n\nFor mmw work-a-ticket#Claim, read playbooks/work-a-ticket.md "
          "relative to this skill directory and follow its Claim step.\n")
    write(skills / "mmw/playbooks/work-a-ticket.md",
          f"---\nname: nested-playbook-probe\ndescription: NESTED_PLAYBOOK_PROBE\n---\n"
          f"# Work a ticket\n\n## Claim\n\nReply with exactly {playbook_mark}.\n")
    write(skills / "mmw/principles/principle-probe.md",
          "---\nname: nested-principle-probe\ndescription: NESTED_PRINCIPLE_PROBE\n---\n"
          "# Principle probe\n\nThis is a principle, not a skill entry.\n")
    source = repo / "probe-source"
    write(source / "references/marker.md", copy_mark + "\n")
    write(skills / "probe-copy/SKILL.md", "---\nname: probe-copy\n"
          "description: Use for the isolated symlink-copy-readable probe.\n---\n"
          "# Copy probe\n\nRead references/marker.md relative to this skill directory "
          "and reply with its marker.\n")
    (skills / "probe-copy/references").mkdir()
    (skills / "probe-copy/references/marker.md").symlink_to(source / "references/marker.md")
    data = repo / "data.md"
    write(data, f"# Isolated data\n\nPlaybook: {skills / 'mmw/playbooks/work-a-ticket.md'}\n")
    fake_root = mmw_home / "product"
    write(fake_root / "skills/mmw/scripts/mode-hook.py", (HERE / "probe_hook.py").read_text())
    write(mmw_home / "installed-root", str(fake_root) + "\n")
    return {"repo": repo, "home": mmw_home, "skills": skills, "data": data,
            "playbook_mark": playbook_mark, "copy_mark": copy_mark}


def install_hooks(ctx, host):
    log = ctx["repo"] / "probe-events.jsonl"
    marks = {event: marker() for event in (*EVENTS, "Stop")}
    hooks = {}
    for event in (*EVENTS, "Stop"):
        command = shlex.join(["env", f"MMW_HOME={ctx['home']}", sys.executable,
                              str(ROOT / "mmw-v2/hook-launcher.py"), "mode-hook",
                              event, marks[event], str(log)])
        hooks[event] = [{"hooks": [{"type": "command", "command": command, "timeout": 10}]}]
    relative = {"claude": ".claude/settings.json", "codex": ".codex/hooks.json",
                "grok": ".grok/hooks/probe.json"}[host]
    path = ctx["repo"] / relative
    write(path, json.dumps({"hooks": hooks}, indent=2) + "\n")
    if host == "codex":
        write(ctx["repo"] / ".codex/config.toml", "# Isolated project hook source.\n")
    ctx.update(log=log, marks=marks, hook_path=path, hooks=hooks)


def host_command(host, prompt, extra=(), tools=None):
    if host == "claude":
        return ["claude", "-p", prompt, "--output-format", "json", "--permission-mode",
                "bypassPermissions", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--tools", "Read,Skill" if tools is None else tools, *extra]
    if host == "codex":
        # The bypass flag persists project trust into config.toml (0.159.2, 2026-09-30).
        return ["codex", "exec", "--json", "--sandbox", "read-only",
                "-c", 'approval_policy="never"', prompt, *extra]
    return ["grok", "-p", prompt, "--output-format", "json", "--always-approve",
            "--max-turns", "12", "--tools", "read_file,list_dir" if tools is None else tools, *extra]


def response(host, output):
    if host in ("claude", "grok"):
        try:
            data = json.loads(output)
            return data.get("result", data.get("text", ""))
        except json.JSONDecodeError:
            return ""
    messages = []
    for line in output.splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = data.get("item") or {}
        if item.get("type") == "agent_message":
            messages.append(item.get("text", ""))
    return "\n".join(messages)


def records(ctx):
    if not ctx["log"].exists():
        return []
    return [json.loads(line) for line in ctx["log"].read_text().splitlines(keepends=True)
            if line.endswith("\n")]


def measured(call, *args):
    try:
        return call(*args)
    except (OSError, ValueError, RuntimeError, StopIteration) as exc:
        return "CANNOT-RUN-UNATTENDED", f"{call.__name__}: {type(exc).__name__}: {exc}; no capability verified"


def items(values):
    return " ".join(f"{key}={value}" for key, value in values.items())


def probe_skills(host, ctx, env):
    prompt = ("Use the mmw skill. Role worker, ticket #611, unattended: "
              f"mmw work-a-ticket#Claim. Data: {ctx['data']}. "
              "This is an isolated read-only probe, not a real ticket. "
              "Only return the marker the Claim step asks for; do not write files or use external services.")
    first = run(host_command(host, prompt), ctx["repo"], env)
    answer = response(host, first.stdout)
    status = "PASS" if first.returncode == 0 and ctx["playbook_mark"] in answer else "FAIL"
    evidence = f"reply={short(answer)}; exit={first.returncode}"
    if first.returncode:
        evidence += "; error=" + short(first.stderr)
    u1 = status, evidence
    inspection = None
    if host == "grok":
        inspected = run(["grok", "inspect", "--json"], ctx["repo"], env)
        inspection = json.loads(inspected.stdout) if inspected.returncode == 0 else None
        # Keep the measurement excerpt restricted to skill names and paths, never config or auth.
        skill_rows = []

        def collect(value):
            if isinstance(value, dict):
                if "name" in value and isinstance(value.get("source"), dict):
                    source_path = str(value["source"].get("path", ""))
                    if str(ctx["repo"]) in source_path:
                        skill_rows.append({"name": value["name"], "path": source_path})
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
        collect(inspection)
        if not any(row["name"] == "mmw" for row in skill_rows):
            return ("CANNOT-RUN-UNATTENDED", "skill not advertised; " + evidence), (
                "CANNOT-RUN-UNATTENDED", "grok inspect --json project skills=" + json.dumps(skill_rows) +
                f"; exit={inspected.returncode}; GROK_FOLDER_TRUST=0; error={short(inspected.stderr)}")
        nested = any(row["name"] in ("nested-playbook-probe", "nested-principle-probe")
                     for row in skill_rows)
        scan_evidence = "GROK_FOLDER_TRUST=0; grok inspect --json project skills=" + json.dumps(skill_rows)
        u1 = status, evidence + "; project mmw skill advertised; GROK_FOLDER_TRUST=0"
    else:
        scan_prompt = ("Without opening any files or invoking skills, report whether your startup "
                       "skill catalog advertises each of these names: mmw, probe-copy, "
                       "nested-playbook-probe, nested-principle-probe. Reply exactly as "
                       "mmw=yes|no copy=yes|no playbook=yes|no principle=yes|no.")
        scan = run(host_command(host, scan_prompt, tools="Skill" if host == "claude" else None),
                   ctx["repo"], env)
        scan_answer = response(host, scan.stdout)
        match = re.search(r"mmw=(yes|no) copy=(yes|no) playbook=(yes|no) principle=(yes|no)", scan_answer)
        if scan.returncode or not match or match.group(1, 2) != ("yes", "yes"):
            return u1, ("CANNOT-RUN-UNATTENDED", f"startup catalog not established: reply={short(scan_answer)}; exit={scan.returncode}")
        nested = "yes" in match.group(3, 4)
        scan_evidence = "startup catalog reply=" + short(scan_answer)
    copied = run(host_command(host, "Use the probe-copy skill. Read its symlinked reference "
                              "and reply only with that reference's marker. Do not write files."),
                 ctx["repo"], env)
    copied_answer = response(host, copied.stdout)
    values = {"nested-md-scanned": "yes" if nested else "no",
              "symlink-copy-readable": "yes" if copied.returncode == 0 and ctx["copy_mark"] in copied_answer else "no"}
    return u1, (verdict("U-3", values), items(values) + "; " + scan_evidence +
                f"; symlink reply={short(copied_answer)}; exit={copied.returncode}")


@contextmanager
def without_mmw(ctx):
    path = ctx["repo"] / ".mmw"
    path.rmdir()
    try:
        yield
    finally:
        path.mkdir()


def hook_verdict(ctx, answer, initial, after, outside, compact_detail):
    values = {name: "yes" if any(row["event"] == event and row["in_mmw"] and
              row["marker"] in answer for row in initial) else "no"
              for (name, _), event in zip(SUBITEMS["U-2"], EVENTS)}
    compact_markers = [row["marker"] for row in records(ctx)
                       if row["event"] == "SessionStart" and row["source"] == "compact"]
    compact_injected = any(mark in after for mark in compact_markers)
    suppressed = not any(mark in outside for mark in ctx["marks"].values())
    return verdict("U-2", values), (items(values) + f"; startup reply={short(answer)}; "
            f"observed event/source={json.dumps([(row['event'], row['source']) for row in records(ctx)])}; "
            f"{compact_detail}, SessionStart source=compact observed={bool(compact_markers)}, "
            f"fresh compact context injected={compact_injected}, reply={short(after)}; "
            f"without .mmw reply={short(outside)}, suppressed={suppressed}; "
            "hook via product mmw-v2/hook-launcher.py")


def probe_native_hooks(host, ctx, env):
    prompt = ("Isolated hook probe. Do not read files, settings, logs, or run shell commands. "
              "Repeat the PROBE_ context markers visible in this session. Then use one "
              "general-purpose subagent to repeat ONLY the PROBE_ markers injected into its own "
              "context; do not give it any marker values. Wait for it to finish. "
              "Your final reply must contain both your markers and its returned markers.")
    session = str(uuid.uuid4())
    first = run(host_command(host, prompt, ("--session-id", session), "Agent" if host == "claude" else ""),
                ctx["repo"], env)
    answer = response(host, first.stdout)
    initial = records(ctx)
    compact = run(host_command(host, "/compact", ("--resume", session), ""), ctx["repo"], env)
    after = run(host_command(host, "Repeat your PROBE_ context markers. Do not use tools.",
                             ("--resume", session), ""), ctx["repo"], env)
    with without_mmw(ctx):
        outside = run(host_command(host, "Repeat only PROBE_ context markers, or NONE if absent. "
                                   "Do not use tools.", tools=""), ctx["repo"], env)
    result = hook_verdict(ctx, answer, initial, response(host, after.stdout),
                          response(host, outside.stdout), f"/compact exit={compact.returncode}")
    if any(proc.returncode for proc in (first, compact, after, outside)):
        return "CANNOT-RUN-UNATTENDED", result[1] + "; error=" + short(
            first.stderr + compact.stderr + after.stderr + outside.stderr)
    return result


class CodexServer:
    """A private stdio server, so the human probe can request real compaction."""

    def __init__(self, ctx, env):
        self.sequence = 0
        self.notifications = []
        self.error_log = tempfile.TemporaryFile(mode="w+")
        self.process = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=ctx["repo"],
                                       env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=self.error_log, text=True)
        try:
            self.call("initialize", {"clientInfo": {"name": "mmw-probe", "version": "1"},
                                     "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def send(self, data):
        self.process.stdin.write(json.dumps(data) + "\n")
        self.process.stdin.flush()

    def receive(self):
        line = self.process.stdout.readline()
        if not line:
            self.error_log.seek(0)
            raise RuntimeError("codex app-server exited: " + short(self.error_log.read()))
        data = json.loads(line)
        if "method" in data and "id" in data:
            raise RuntimeError("codex app-server requires a human request: " + data["method"])
        return data

    def call(self, method, params):
        self.sequence += 1
        self.send({"id": self.sequence, "method": method, "params": params})
        while True:
            data = self.receive()
            if data.get("id") == self.sequence:
                if "error" in data:
                    raise RuntimeError(method + ": " + json.dumps(data["error"]))
                return data["result"]
            self.notifications.append(data)

    def turn(self, thread, prompt):
        self.call("turn/start", {"threadId": thread, "input": [{"type": "text", "text": prompt}]})
        return self.completed(thread)

    def completed(self, thread):
        # Gather only assistant message notifications; marker-bearing hook commands are not evidence.
        pending = self.notifications
        self.notifications = []
        replies = []
        while True:
            data = pending.pop(0) if pending else self.receive()
            params = data.get("params", {})
            if params.get("threadId") != thread:
                continue
            item = params.get("item", {})
            if data.get("method") == "item/completed" and item.get("type") == "agentMessage":
                replies.append(item.get("text", ""))
            if data.get("method") == "turn/completed":
                if params["turn"].get("status") != "completed":
                    raise RuntimeError("codex probe turn failed: " + json.dumps(params["turn"].get("error")))
                return "\n".join(replies)

    def close(self):
        self.process.stdin.close()
        self.process.wait()
        self.process.stdout.close()
        self.error_log.close()


def probe_codex_hooks(ctx, env):
    server = None
    try:
        server = CodexServer(ctx, env)
        started = server.call("thread/start", {"cwd": str(ctx["repo"]), "approvalPolicy": "never",
                              "sandbox": "danger-full-access", "ephemeral": True})
        thread = started["thread"]["id"]
        answer = server.turn(thread, "Isolated hook probe. Do not read files, logs, settings, or run shell commands. "
                             "Repeat PROBE_ context markers. Spawn one subagent to repeat ONLY its own "
                             "injected PROBE_ context markers, without giving it marker values. Wait for it "
                             "to finish. Return your markers and its markers.")
        initial = records(ctx)
        server.call("thread/compact/start", {"threadId": thread})
        server.completed(thread)
        after = server.turn(thread, "Repeat your PROBE_ context markers without using tools.")
        with without_mmw(ctx):
            outside_thread = server.call("thread/start", {"cwd": str(ctx["repo"]), "approvalPolicy": "never",
                                         "sandbox": "danger-full-access", "ephemeral": True})["thread"]["id"]
            outside = server.turn(outside_thread, "Repeat only PROBE_ context markers or NONE if absent. Do not use tools.")
        return hook_verdict(ctx, answer, initial, after, outside, "thread/compact/start completed")
    except RuntimeError as exc:
        # A failed capability measurement is still a result, never a simulated PASS.
        return "CANNOT-RUN-UNATTENDED", str(exc)
    finally:
        if server is not None:
            server.close()


def frozen_runner(name="orca"):
    root = Path((statedir.home() / "installed-root").read_text().strip())
    return root / f"skills/dispatch/scripts/runners/{name}.sh"


def model_row(host):
    return next(row for row in models.session_rows() if row.host == host)


def start_probe(host, ctx, env, runner="orca", prompt=None, adapter=None):
    role = marker()
    row = model_row(host)
    adapter = adapter or frozen_runner(runner)
    argv = ["bash", str(adapter), "start", "--host", host, "--model", row.model,
            "--effort", row.effort, "--cwd", str(ctx["repo"]), "--title", "mmw-probe-" + host,
            "--env", f"MMW_ROLE={role}", "--env", f"MMW_HOME={ctx['home']}"]
    for key in ("PATH", "GROK_FOLDER_TRUST"):
        if key in env:
            argv += ["--env", f"{key}={env[key]}"]
    argv += ["--prompt", prompt or "Isolated environment probe. Reply PROBE-DONE without using tools."]
    return run(argv, ctx["repo"], env), role, adapter


def wait_finished(ctx, adapter, handle, env, previous_stops=0):
    # Never interrupt a working agent. Stop hooks are local completion evidence;
    # adapter liveness covers a host which exited before its hook could run.
    settled = None
    while True:
        logged = records(ctx)
        stops = sum(row["event"] == "Stop" for row in logged)
        prompts = sum(row["event"] == "UserPromptSubmit" for row in logged)
        if stops > previous_stops and stops >= prompts:
            if settled is None:
                settled = time.monotonic()
            elif time.monotonic() - settled >= 2:
                return "Stop hooks completed for all submitted turns"
        else:
            settled = None
        live = run(["bash", str(adapter), "liveness", handle], ctx["repo"], env)
        if live.returncode == 0 and live.stdout.strip() == "stopped":
            return "adapter liveness=stopped"
        time.sleep(1)


def finish_env(ctx, env, started, role, adapter):
    if started.returncode:
        # Preserve the adapter's original refusal, not a guessed reason.
        return "CANNOT-RUN-UNATTENDED", started.stderr.strip() or started.stdout.strip()
    handle = started.stdout.strip()
    completed = wait_finished(ctx, adapter, handle, env)
    found = [row for row in records(ctx) if row["event"] == "SessionStart"]
    closed = run(["bash", str(adapter), "stop", handle], ctx["repo"], env)
    if closed.returncode:
        closed = run(["bash", str(adapter), "stop", handle], ctx["repo"], env)
    if closed.returncode:
        RETAINED_DIRECTORIES.update((ctx["repo"], ctx["home"]))
        return "CANNOT-RUN-UNATTENDED", (f"probe-owned terminal={handle}; completed={completed}; "
                f"adapter stop exit={closed.returncode}; {short(closed.stderr)}; close this probe terminal through the adapter")
    inherited = any(row["MMW_ROLE"] == role for row in found)
    return "PASS" if inherited else "FAIL", (f"runner --env MMW_ROLE={role}; hook log={json.dumps(found)}; "
            f"terminal={handle}, completed={completed}, closed; hook via product mmw-v2/hook-launcher.py")


def probe_env(host, ctx, env):
    started, role, adapter = start_probe(host, ctx, env)
    return finish_env(ctx, env, started, role, adapter)


def probe_codex_env(ctx, env):
    # The terminal must exist before owner configuration is touched. A private
    # launch gate prevents Codex from reading hook trust before it is installed.
    gate = ctx["repo"] / "launch-codex"
    binary = shutil.which("codex")
    wrapper = ctx["repo"] / "bin/codex"
    write(wrapper, "#!/bin/sh\nwhile [ ! -f " + shlex.quote(str(gate)) +
          " ]; do sleep 1; done\nexec " + shlex.quote(binary) + ' "$@"\n')
    wrapper.chmod(0o700)
    gated_env = dict(env, PATH=str(wrapper.parent) + os.pathsep + env["PATH"])
    started, role, adapter = start_probe("codex", ctx, gated_env)
    if started.returncode:
        return finish_env(ctx, gated_env, started, role, adapter)
    try:
        with trusted_codex(ctx):
            gate.touch()
            return finish_env(ctx, gated_env, started, role, adapter)
    except BaseException:
        # Before the gate, there is no host or working agent to interrupt.
        if not gate.exists():
            run(["bash", str(adapter), "stop", started.stdout.strip()], ctx["repo"], gated_env)
        raise


def probe_herdr(env):
    if not shutil.which("herdr"):
        return "CANNOT-RUN-UNATTENDED", "herdr binary absent from PATH"
    with temporary_directory() as state, temporary_directory() as repo, temporary_directory() as home:
        private_env = {key: value for key, value in env.items() if not key.startswith("HERDR_")}
        private_env.update(HERDR_CONFIG_PATH=str(state / "config.toml"),
                           HERDR_SESSION="mmw-probe-" + uuid.uuid4().hex[:12],
                           HERDR_SOCKET_PATH=str(state / "probe.sock"))
        host = "grok"
        private_env["GROK_FOLDER_TRUST"] = "0"
        ctx = prepare(host, repo / "probe", home)
        install_hooks(ctx, host)
        adapter = ROOT / "mmw-v2/skills/dispatch/scripts/runners/herdr.sh"
        with (state / "server.log").open("w+") as output:
            server = subprocess.Popen(["bash", str(adapter), "probe-server", "start"], cwd=state, env=private_env,
                                      stdin=subprocess.DEVNULL, stdout=output, stderr=output)
            try:
                while not Path(private_env["HERDR_SOCKET_PATH"]).exists() and server.poll() is None:
                    time.sleep(0.1)
                if server.poll() is not None:
                    output.seek(0)
                    return "CANNOT-RUN-UNATTENDED", f"private herdr server exit={server.returncode}; {short(output.read())}"
                bootstrap = run(["bash", str(adapter), "probe-workspace", str(ctx["repo"])], state, private_env)
                if bootstrap.returncode:
                    return "CANNOT-RUN-UNATTENDED", "private workspace creation refused: " + short(bootstrap.stderr)
                initial, _, adapter = start_probe(host, ctx, private_env, "herdr",
                        "Isolated probe. Reply READY only and do not use tools.", adapter)
                if initial.returncode:
                    return "CANNOT-RUN-UNATTENDED", "private headless server started; " + short(initial.stderr)
                handle = initial.stdout.strip()
                wait_finished(ctx, adapter, handle, private_env)
                previous = sum(row["event"] == "Stop" for row in records(ctx))
                token = "U9_" + uuid.uuid4().hex
                prompt = f"Reply with only {token}_A.\nAlso include {token}_B. Do not use tools."
                sent = run(["bash", str(adapter), "send", handle, prompt], repo, private_env)
                completed = wait_finished(ctx, adapter, handle, private_env, previous)
                submissions = [row["probe_prompt"] for row in records(ctx) if "probe_prompt" in row]
                closed = run(["bash", str(adapter), "stop", handle], repo, private_env)
                evidence = (f"private headless herdr server; {host}={version(host)}; adapter send exit={sent.returncode}; "
                            f"observed UserPromptSubmit count={len(submissions)}, payloads={json.dumps(submissions)}; "
                            f"completed={completed}; pane closed exit={closed.returncode}; two-line input={json.dumps(prompt)}")
                if sent.returncode not in (0, 4) or closed.returncode:
                    return "CANNOT-RUN-UNATTENDED", evidence + "; " + short(sent.stderr + closed.stderr)
                return "PASS" if submissions == [prompt] else "FAIL", evidence
            finally:
                # The isolated server owns only probe panes; no owner's server is addressed.
                stopped = run(["bash", str(adapter), "probe-server", "stop"], state, private_env)
                server.wait()
                if stopped.returncode:
                    print("PROBES FAIL: private Herdr server stop refused: " + short(stopped.stderr), file=sys.stderr)


def cell(probe, host, result, versions):
    status, evidence = result
    day = datetime.now(timezone.utc).date().isoformat()
    runner = "herdr" if host == "herdr" else "orca"
    return f"{probe} {host} {status} {host}={versions[host]},{runner}={versions[runner]} {day} : {short(evidence)}"


@contextmanager
def trusted_codex(ctx):
    """Owner-only temporary trust; no authentication or user hooks file is copied."""
    import tomllib
    path = Path("~/.codex/config.toml").expanduser()
    original = path.read_bytes() if path.exists() else None
    old_mode = path.stat().st_mode & 0o777 if original is not None else 0o600
    text = original.decode("utf-8") if original is not None else ""
    tomllib.loads(text)
    added = [f"[projects.{json.dumps(str(ctx['repo']))}]\ntrust_level = \"trusted\"\n"]
    for event, groups in ctx["hooks"].items():
        handler = {**groups[0]["hooks"][0], "async": False}
        label = re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
        normal = {"event_name": label, "hooks": [handler]}
        digest = "sha256:" + hashlib.sha256(json.dumps(normal, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode()).hexdigest()
        key = f"{ctx['hook_path']}:{label}:0:0"
        added.append(f"[hooks.state.{json.dumps(key)}]\ntrusted_hash = {json.dumps(digest)}\n")
    changed = text.rstrip("\n") + "\n\n" + "\n".join(added)
    tomllib.loads(changed)
    path.parent.mkdir(parents=True, exist_ok=True)
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f"signal {signum}")
    saved_signals = {s: signal.signal(s, interrupted) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        path.write_text(changed, encoding="utf-8")
        path.chmod(old_mode)
        yield
    finally:
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)
            path.chmod(old_mode)
        for sig, previous in saved_signals.items():
            signal.signal(sig, previous)


def args_parse():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-config", nargs=2, metavar=("PROBE", "HOST"))
    parser.add_argument("--ticket", type=int)
    args = parser.parse_args()
    if args.user_config:
        if tuple(args.user_config) not in (("U-2", "codex"), ("U-17", "codex")) or not args.ticket or args.ticket < 1:
            parser.error("--user-config supports only U-2 codex or U-17 codex and requires --ticket <n>")
    elif args.ticket is not None:
        parser.error("--ticket requires --user-config")
    return args


def main():
    args = args_parse()  # Reject every bad mode before creating or writing any file.
    before = checksum()
    versions = {name: version(name) for name in ("claude", "codex", "grok", "orca", "herdr")}
    lines = []
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("MMW_") and key not in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "PASEO_AGENT_CWD")}
    try:
        with temporary_directory() as repo_dir, temporary_directory() as home_dir:
            if args.user_config:
                probe, host = args.user_config
                ctx = prepare(host, Path(repo_dir), Path(home_dir))
                install_hooks(ctx, host)
                env["MMW_HOME"] = str(ctx["home"])
                if probe == "U-17":
                    result = measured(probe_codex_env, ctx, env)
                else:
                    with trusted_codex(ctx):
                        result = measured(probe_codex_hooks, ctx, env)
                lines.append(cell(probe, host, result, versions))
            else:
                for host in ("claude", "codex", "grok"):
                    print(f"measuring {host}", flush=True)
                    ctx = prepare(host, Path(repo_dir) / host, Path(home_dir) / host)
                    env["MMW_HOME"] = str(ctx["home"])
                    if host == "grok":
                        env["GROK_FOLDER_TRUST"] = "0"
                    if versions[host] == "absent":
                        for probe in ("U-1", "U-2", "U-3", "U-17"):
                            lines.append(cell(probe, host, ("CANNOT-RUN-UNATTENDED", f"{host} binary absent from PATH"), versions))
                        continue
                    skill_result = measured(probe_skills, host, ctx, env)
                    u1, u3 = (skill_result, skill_result) if isinstance(skill_result[0], str) else skill_result
                    lines.extend((cell("U-1", host, u1, versions), cell("U-3", host, u3, versions)))
                    install_hooks(ctx, host)
                    if host == "codex":
                        reason = ("project .codex/hooks.json requires per-handler trusted_hash in "
                                  "~/.codex/config.toml; mmw-v2/install.sh codex_trust_wanted and "
                                  "AGENTS.md Gotchas; no user config or hook-trust bypass written")
                        u2 = u17 = "NEEDS-USER-CONFIG", reason
                    else:
                        u2 = measured(probe_native_hooks, host, ctx, env)
                        u17 = measured(probe_env, host, ctx, env)
                    lines.extend((cell("U-2", host, u2, versions), cell("U-17", host, u17, versions)))
                lines.append(cell("U-9", "herdr", measured(probe_herdr, env), versions))
    finally:
        after = checksum()
        lines.extend(checksum_lines("before", before))
        lines.extend(checksum_lines("after", after))
        if not args.user_config:
            write(HERE / "results.md", "# Host probe measurements\n\n" + "\n".join(lines) + "\n")
    if before != after:
        changed = ", ".join(name for name in before if before[name] != after[name])
        print(f"PROBES FAIL: user configuration changed: {changed}; isolation is not verified; "
              "compare these hashes and restore the named configuration before using the measurement", file=sys.stderr)
        print("\n".join(lines), file=sys.stderr)
        return 1
    if args.user_config:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md") as body:
            body.write("# Host probe measurement\n\n" + "\n".join(lines) + "\n")
            body.flush()
            posted = run(["gh", "issue", "comment", str(args.ticket), "--body-file", body.name], ROOT)
        if posted.returncode:
            print(posted.stderr, file=sys.stderr)
            print("\n".join(lines), file=sys.stderr)
            return 1
        print(posted.stdout.strip())
    else:
        return report(HERE / "results.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
