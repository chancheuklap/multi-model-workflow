#!/usr/bin/env python3
"""Measure #611 in temporary repositories using the hosts' existing login."""

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
import uuid

from check_results import CONFIG_PATHS, SUBITEMS, check

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVENTS = ("SessionStart", "SubagentStart", "UserPromptSubmit")


@contextmanager
def temporary_directory():
    made = run(["mktemp", "-d"])
    if made.returncode:
        raise RuntimeError("mktemp -d failed: " + short(made.stderr))
    path = Path(made.stdout.strip()).resolve()
    try:
        yield path
    finally:
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
    marks = {event: marker() for event in EVENTS}
    hooks = {}
    for event in EVENTS:
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
            "--max-turns", "12", "--tools", tools or "read_file,list_dir", *extra]


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
    return [json.loads(line) for line in ctx["log"].read_text().splitlines()]


def capability(status_values, probe):
    expected = dict(SUBITEMS[probe])
    return "PASS" if status_values == expected else "FAIL"


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
            return u1, ("NEEDS-USER-CONFIG", "grok inspect --json project skills=" +
                        json.dumps(skill_rows) + "; untrusted-folder project discovery is gated; "
                        "trust grant writes ~/.grok/trusted_folders.toml (10-hooks.md Hook Locations)")
        nested = any(row["name"] in ("nested-playbook-probe", "nested-principle-probe")
                     for row in skill_rows)
        scan_evidence = "grok inspect --json project skills=" + json.dumps(skill_rows)
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
    return u1, (capability(values, "U-3"), items(values) + "; " + scan_evidence +
                f"; symlink reply={short(copied_answer)}; exit={copied.returncode}")


def probe_claude_hooks(ctx, env):
    prompt = ("Isolated hook probe. Do not read files, settings, logs, or run shell commands. "
              "Repeat the PROBE_ context markers visible in this session. Then use one "
              "general-purpose Agent to repeat ONLY the PROBE_ markers injected into its own "
              "context; do not give it any marker values. Wait for it to finish. "
              "Your final reply must contain both your markers and its returned markers.")
    session = str(uuid.uuid4())
    first = run(host_command("claude", prompt, ("--session-id", session), "Agent"), ctx["repo"], env)
    answer = response("claude", first.stdout)
    initial = records(ctx)
    values = {name: "yes" if first.returncode == 0 and ctx["marks"][event] in answer and
              any(row["event"] == event and row["in_mmw"] for row in initial) else "no"
              for (name, _), event in zip(SUBITEMS["U-2"], EVENTS)}
    compact = run(host_command("claude", "/compact", ("--resume", session), ""), ctx["repo"], env)
    compact_seen = any(row["event"] == "SessionStart" and row["source"] == "compact"
                       for row in records(ctx))
    after = run(host_command("claude", "Repeat your PROBE_ context markers. Do not use tools.",
                             ("--resume", session), ""), ctx["repo"], env)
    after_answer = response("claude", after.stdout)
    (ctx["repo"] / ".mmw").rmdir()
    outside = run(host_command("claude", "Repeat only PROBE_ context markers, or NONE if absent. "
                               "Do not use tools.", tools=""), ctx["repo"], env)
    (ctx["repo"] / ".mmw").mkdir()
    outside_answer = response("claude", outside.stdout)
    outside_ok = outside.returncode == 0 and not any(mark in outside_answer for mark in ctx["marks"].values())
    detail = (items(values) + f"; startup reply={short(answer)}; compact exit={compact.returncode},"
              f" SessionStart source=compact observed={compact_seen}, reply={short(after_answer)}; "
              f"without .mmw reply={short(outside_answer)}, suppressed={outside_ok}; "
              "hook via product mmw-v2/hook-launcher.py")
    if first.returncode or compact.returncode or after.returncode or outside.returncode:
        return "CANNOT-RUN-UNATTENDED", detail + "; error=" + short(first.stderr + compact.stderr + after.stderr + outside.stderr)
    compact_markers = [row["marker"] for row in records(ctx)
                       if row["event"] == "SessionStart" and row["source"] == "compact"]
    if not compact_seen or not any(mark in after_answer for mark in compact_markers) or not outside_ok:
        values["session-start"] = "no"
        detail = items(values) + detail[detail.index(";"):]
    return capability(values, "U-2"), detail


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

    def completed(self, thread):
        seen = self.notifications
        self.notifications = []
        while True:
            data = seen.pop(0) if seen else self.receive()
            params = data.get("params", {})
            if params.get("threadId") == thread:
                if data.get("method") == "turn/completed":
                    turn = params["turn"]
                    if turn.get("status") != "completed":
                        raise RuntimeError("codex probe turn did not complete: " + json.dumps(turn.get("error")))
                    return

    def turn(self, thread, prompt):
        self.call("turn/start", {"threadId": thread, "input": [{"type": "text", "text": prompt}]})
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
        values = {name: "yes" if ctx["marks"][event] in answer and any(
                  row["event"] == event and row["in_mmw"] for row in initial) else "no"
                  for (name, _), event in zip(SUBITEMS["U-2"], EVENTS)}
        server.call("thread/compact/start", {"threadId": thread})
        server.completed(thread)
        compact_seen = any(row["event"] == "SessionStart" and row["source"] == "compact"
                           for row in records(ctx))
        after = server.turn(thread, "Repeat your PROBE_ context markers without using tools.")
        (ctx["repo"] / ".mmw").rmdir()
        outside_thread = server.call("thread/start", {"cwd": str(ctx["repo"]), "approvalPolicy": "never",
                                     "sandbox": "danger-full-access", "ephemeral": True})["thread"]["id"]
        outside = server.turn(outside_thread, "Repeat only PROBE_ context markers or NONE if absent. Do not use tools.")
        (ctx["repo"] / ".mmw").mkdir()
        suppressed = not any(mark in outside for mark in ctx["marks"].values())
        compact_markers = [row["marker"] for row in records(ctx)
                           if row["event"] == "SessionStart" and row["source"] == "compact"]
        if not compact_seen or not any(mark in after for mark in compact_markers) or not suppressed:
            values["session-start"] = "no"
        return capability(values, "U-2"), (items(values) + f"; startup reply={short(answer)}; "
                f"thread/compact/start SessionStart source=compact observed={compact_seen}, reply={short(after)}; "
                f"without .mmw reply={short(outside)}, suppressed={suppressed}; hook via mmw-v2/hook-launcher.py")
    except RuntimeError as exc:
        # A failed capability measurement is still a result, never a simulated PASS.
        return "CANNOT-RUN-UNATTENDED", str(exc)
    finally:
        if server is not None:
            server.close()


def frozen_runner():
    root = Path(Path("~/.mmw/installed-root").expanduser().read_text().strip())
    return root / "skills/dispatch/scripts/runners/orca.sh"


def model_row(host):
    config = json.loads(Path("~/.mmw/models.json").expanduser().read_text())
    rows = config.get("rows", config)
    for row in rows.values():
        if isinstance(row, dict) and row.get("host") == host:
            return row
    raise ValueError(f"no current model row for {host}")


def probe_env(host, ctx, env):
    role = marker()
    row = model_row(host)
    result = run(["bash", str(frozen_runner()), "start", "--host", host, "--model", row["model"],
                  "--effort", row.get("effort", "high"), "--cwd", str(ctx["repo"]),
                  "--title", "mmw-probe-U17-" + host, "--env", f"MMW_ROLE={role}",
                  "--env", f"MMW_HOME={ctx['home']}", "--prompt",
                  "Isolated environment probe. Reply PROBE-DONE without using tools, then exit."],
                 ctx["repo"], env)
    if result.returncode:
        return "CANNOT-RUN-UNATTENDED", f"path:{ctx['repo']}; runner start exit={result.returncode}; {short(result.stderr)}"
    handle = result.stdout.strip()
    # Wait for the probe to finish its turn before closing our own terminal.
    waited = run(["orca", "terminal", "wait", "--terminal", handle, "--for", "tui-idle",
                  "--timeout-ms", "60000", "--json"], ctx["repo"], env)
    wait_data = json.loads(waited.stdout)
    wait_result = wait_data.get("result", {}).get("wait", {})
    if not wait_result.get("satisfied"):
        raise RuntimeError(f"probe session {handle} did not finish: {short(waited.stdout)}; do not interrupt it")
    found = [r for r in records(ctx) if r["event"] == "SessionStart"]
    inherited = any(r["MMW_ROLE"] == role for r in found)
    closed = run(["bash", str(frozen_runner()), "stop", handle], ctx["repo"], env)
    if closed.returncode:
        raise RuntimeError(f"could not close probe-owned terminal {handle}: {short(closed.stderr)}")
    return ("PASS" if inherited else "FAIL", f"runner --env MMW_ROLE={role}; hook printed variable in "
            f"probe log={json.dumps(found)}; terminal={handle}, closed; hook via mmw-v2/hook-launcher.py")


def probe_herdr(env):
    # #611 authorizes only a new isolated session, never the user's focused session.
    with temporary_directory() as state:
        session = "mmw-probe-" + uuid.uuid4().hex[:12]
        private_env = dict(env, HERDR_CONFIG_PATH=str(state / "config.toml"))
        attempted = run(["herdr", "--session", session], state, private_env)
        stopped = run(["herdr", "--session", session, "session", "stop", session], state, private_env)
        return "CANNOT-RUN-UNATTENDED", (f"isolated herdr --session {session} exit={attempted.returncode}; "
                f"stdout={short(attempted.stdout)}, stderr={short(attempted.stderr)}; "
                f"stdin-is-terminal={sys.stdin.isatty()}; isolated-session cleanup exit={stopped.returncode}; "
                "no agent prompt submission was possible, no owner's session reused")


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
        handler = dict(groups[0]["hooks"][0], async_=False)
        handler["async"] = handler.pop("async_")
        label = re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower()
        normal = {"event_name": label, "hooks": [handler]}
        digest = "sha256:" + hashlib.sha256(json.dumps(normal, sort_keys=True,
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
                with trusted_codex(ctx):
                    result = probe_codex_hooks(ctx, env) if probe == "U-2" else probe_env(host, ctx, env)
                lines.append(cell(probe, host, result, versions))
            else:
                for host in ("claude", "codex", "grok"):
                    print(f"measuring {host}", flush=True)
                    ctx = prepare(host, Path(repo_dir) / host, Path(home_dir) / host)
                    env["MMW_HOME"] = str(ctx["home"])
                    if versions[host] == "absent":
                        for probe in ("U-1", "U-2", "U-3", "U-17"):
                            lines.append(cell(probe, host, ("CANNOT-RUN-UNATTENDED", f"{host} binary absent from PATH"), versions))
                        continue
                    u1, u3 = probe_skills(host, ctx, env)
                    lines.extend((cell("U-1", host, u1, versions), cell("U-3", host, u3, versions)))
                    install_hooks(ctx, host)
                    if host == "codex":
                        reason = ("project .codex/hooks.json requires per-handler trusted_hash in "
                                  "~/.codex/config.toml; mmw-v2/install.sh codex_trust_wanted and "
                                  "AGENTS.md Gotchas; no user config or hook-trust bypass written")
                        u2 = u17 = "NEEDS-USER-CONFIG", reason
                    elif host == "grok":
                        u2 = "NEEDS-USER-CONFIG", ("project .grok/hooks/*.json requires folder trust; "
                              "grant writes ~/.grok/trusted_folders.toml; installed 10-hooks.md Hook Locations; "
                              "no grant or trust bypass used")
                        u17 = probe_env(host, ctx, env)
                    else:
                        u2 = probe_claude_hooks(ctx, env)
                        u17 = probe_env(host, ctx, env)
                    lines.extend((cell("U-2", host, u2, versions), cell("U-17", host, u17, versions)))
                lines.append(cell("U-9", "herdr", probe_herdr(env), versions))
    finally:
        after = checksum()
        lines.extend(checksum_lines("before", before))
        lines.extend(checksum_lines("after", after))
        if not args.user_config:
            write(HERE / "results.md", "# Host probe measurements\n\n" + "\n".join(lines) + "\n")
    if before != after:
        print("PROBES FAIL: user configuration changed; see checksum rows", file=sys.stderr)
        return 1
    if args.user_config:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md") as body:
            body.write("# Host probe measurement\n\n" + "\n".join(lines) + "\n")
            body.flush()
            posted = run(["gh", "issue", "comment", str(args.ticket), "--repo",
                          "chancheuklap/multi-model-workflow", "--body-file", body.name], ROOT)
        if posted.returncode:
            print(posted.stderr, file=sys.stderr)
            print("\n".join(lines), file=sys.stderr)
            return 1
        print(posted.stdout.strip())
    else:
        errors = check(HERE / "results.md")
        if errors:
            print("PROBES FAIL\n" + "\n".join(errors))
            return 1
        print("PROBES OK 13 cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
