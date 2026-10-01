#!/usr/bin/env python3
"""Measure U-7 in scratch repositories using existing host logins.

Measured 2026-10-01: Claude Code 2.1.286's stream-json system/init catalog
with --setting-sources project still listed code-review in an empty repository.
Codex 0.159.2 debug prompt-input and Grok 1.0.46 (2765805b9442) inspect --json
also listed measured skills from user level. All three groups were gated before
routing sessions: their tool-call event shapes have NOT been measured. The
Claude assistant/tool_use, Codex item.*/command_execution and Grok ACP
sessionUpdate parser fixtures are synthetic, not captured routing evidence.
"""

import argparse
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

from check_u7 import (BEFORE, CELL_LINE, CONFIG_PATHS, HERE, HOSTS, PHASES, ROOT,
                      read_sentences, reached, report)

SUFFIX = ("\n\n(This is an isolated routing probe in a scratch repository. Load and read whatever "
          "skill and instruction files you would follow for the request above, then stop before doing "
          "any of the work. Do not write files, run commands that change anything, or contact any service. "
          "End your reply with one line: LOADED: <the skills and files you read>.)")
STUBS = ("claude", "codex", "grok", "cursor-agent", "agent", "pi", "orca", "nmem",
         "paseo", "herdr", "gh", "uv", "launchctl")
MMW_TARGETS = ("/mmw-v2/upstream/skills/", "/mmw-v2/skills/",
               "/mmw-v2/upstream-diagram-design/skills/", "/mmw-v2/upstream-pstack/skills/",
               "/.mmw/skill-copies/")
# Tool inputs, never assistant prose or file contents, are searched for paths.
PATH_TOKEN = re.compile(r"(?:\$HOME|~|[A-Za-z0-9_./-])+/(?:SKILL\.md|[A-Za-z0-9_./*-]+)")
SKILL_PATH = re.compile(r"(?:^|/)(?:\.claude|\.agents)/skills/([a-z0-9-]+)(?:/|$)")
USER_SKILL_PATH = re.compile(r"/(?:skills|skill-copies)/([a-z0-9-]+)(?:/|$)")
CHECKOUT_PATH = re.compile(r"/mmw-v2/(?:upstream(?:-diagram-design|-pstack)?/)?skills/(?:[^/]+/)*")
PLAYBOOK_PATH = re.compile(r"/skills/mmw/playbooks/([a-z0-9-]+)\.md(?:$|[\s'\"])")


def short(value):
    return " ".join(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value).split())[:1000]


def run(argv, cwd=None, env=None, timeout=600, input=None):
    try:
        return subprocess.run(argv, cwd=cwd, env=env, input=input,
                              stdin=subprocess.DEVNULL if input is None else None,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(argv, 124, stdout, stderr + f"\nTimed out after {timeout}s")


@contextmanager
def temporary_directory():
    path = Path(subprocess.check_output(["mktemp", "-d"], text=True).strip()).resolve()
    try:
        yield path
    finally:
        shutil.rmtree(path)


def checksum():
    hashes = {}
    for name in CONFIG_PATHS:
        path = Path(name).expanduser()
        if not path.exists():
            hashes[name] = "absent"
        elif path.is_dir():
            entries = "".join(f"{entry.name}\t{os.readlink(entry) if entry.is_symlink() else 'entry'}\n"
                              for entry in sorted(path.iterdir(), key=lambda item: item.name))
            hashes[name] = hashlib.sha256(entries.encode()).hexdigest()
        else:
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def checksum_lines(phase, hashes):
    return [f"CHECKSUM {phase} {name} {hashes[name]}" for name in CONFIG_PATHS]


def child_env(mmw_home, host):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("MMW_") and key not in
           ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "PASEO_AGENT_CWD")}
    env["MMW_HOME"] = str(mmw_home)
    if host == "grok":
        env["GROK_FOLDER_TRUST"] = "0"
    return env


def install_env(home, target, stubs):
    if home.resolve() == target.resolve():
        raise ValueError("install HOME and MMW_V2_HOME must differ")
    stubs.mkdir(parents=True, exist_ok=True)
    for name in ("python3", "git"):
        binary = sys.executable if name == "python3" else shutil.which(name)
        if not binary:
            raise RuntimeError(f"{name} binary absent; cannot export skill sets")
        (stubs / name).symlink_to(Path(binary).resolve())
    for name in STUBS:
        path = stubs / name
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    (target / ".claude").mkdir(parents=True)
    return {"HOME": str(home), "MMW_V2_HOME": str(target),
            "PATH": f"{stubs}:/usr/bin:/bin:/usr/sbin:/sbin",
            "MMW_HOME": str(target / ".mmw"), "LANG": "en_US.UTF-8"}


def skill_list(source):
    skills = []
    for line in (source / "mmw-v2/skills.txt").read_text(encoding="utf-8").splitlines():
        tokens = line.split("#", 1)[0].split()
        if tokens:
            skills.append((tokens[0].rsplit("/", 1)[-1], "+model-invoked" in tokens[1:]))
    return skills


def install_set(commit, stack):
    source, home, target, stubs = [stack.enter_context(temporary_directory()) for _ in range(4)]
    archived = subprocess.run(["git", "archive", commit, "mmw-v2"], cwd=ROOT,
                              capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(source)], input=archived.stdout, check=True)
    env = install_env(home, target, stubs)
    installed = run(["env", "-i", *(f"{key}={value}" for key, value in env.items()),
                     "/bin/bash", str(source / "mmw-v2/install.sh")], source)
    skills = skill_list(source)
    missing = []
    for name, marked in skills:
        for directory in (".agents/skills", ".claude/skills"):
            if not (target / directory / name / "SKILL.md").is_file():
                missing.append(f"{directory}/{name}/SKILL.md")
        if marked and not (target / ".mmw/skill-copies" / name / "SKILL.md").is_file():
            missing.append(f".mmw/skill-copies/{name}/SKILL.md")
    if not skills or missing:
        raise RuntimeError("skill sets not laid out: " + ", ".join(missing)
                           + f"; install exit={installed.returncode}; {short(installed.stderr)}")
    print(f"U7 installed {commit[:8]}: {len(skills)} skills, "
          f"{sum(marked for _, marked in skills)} copies; install exit={installed.returncode}", flush=True)
    return target, {name for name, _ in skills}


def copy_skills(source, destination):
    destination.mkdir(parents=True)
    for entry in sorted(source.iterdir()):
        target = destination / entry.name
        shutil.copytree(entry.resolve(), target, symlinks=True)
        for directory, directories, filenames in os.walk(target, followlinks=False):
            for name in directories + filenames:
                link = Path(directory) / name
                if link.is_symlink():
                    original = entry.resolve() / link.relative_to(target)
                    absolute = original.resolve()
                    link.unlink()
                    link.symlink_to(absolute)


def prepare(repo, host, installed=None):
    made = run(["git", "init", "-q", str(repo)])
    if made.returncode:
        raise RuntimeError("git init failed: " + short(made.stderr))
    (repo / ".mmw").mkdir()
    if installed:
        relative = ".claude/skills" if host == "claude" else ".agents/skills"
        copy_skills(installed / relative, repo / relative)


def host_command(host, prompt, tools=None):
    if host == "claude":
        return ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
                "--setting-sources", "project", "--permission-mode", "bypassPermissions",
                "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools",
                "Read,Skill,Glob,Grep" if tools is None else tools,
                "--no-session-persistence", "--max-budget-usd", "1"]
    if host == "codex":
        return ["codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only",
                "-c", 'approval_policy="never"', prompt]
    return ["grok", "-p", prompt, "--output-format", "streaming-json", "--always-approve",
            "--max-turns", "12", "--no-subagents", "--tools", "read_file,list_dir"]


def json_lines(output):
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            yield value


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for entry in value:
            yield from strings(entry)
    elif isinstance(value, dict):
        for key, entry in value.items():
            if key not in ("output", "aggregated_output", "stdout", "stderr", "result"):
                yield from strings(entry)


def parse_events(host, output, scratch, tested_names):
    result = {"skills": [], "playbooks": [], "leaks": [], "tool_calls": 0}
    seen = set()

    def add(key, name):
        if name not in result[key]:
            result[key].append(name)

    def paths(value, base_directory=False):
        for text in strings(value):
            for match in PATH_TOKEN.finditer(text):
                filename = match.group()
                expanded = filename.replace("$HOME/", str(Path.home()) + "/")
                path = Path(expanded).expanduser()
                inside = not path.is_absolute() or path.resolve().is_relative_to(scratch.resolve())
                skill = SKILL_PATH.search(filename)
                checkout = CHECKOUT_PATH.search(filename)
                user_skill = USER_SKILL_PATH.search(filename)
                if not inside and ((user_skill and user_skill[1] in tested_names) or checkout):
                    add("leaks", str(path))
                elif inside and skill and not base_directory:
                    add("skills", skill[1])
                    playbook = PLAYBOOK_PATH.search(filename)
                    if playbook:
                        add("playbooks", playbook[1])

    def call(identifier, value, skill=None):
        if identifier not in seen:
            seen.add(identifier)
            result["tool_calls"] += 1
        if skill:
            add("skills", skill.lstrip("/").split(":")[-1])
        paths(value)

    for number, event in enumerate(json_lines(output)):
        if host == "claude":
            message = event.get("message", {})
            content = message.get("content", []) if isinstance(message, dict) else []
            if not isinstance(content, list):
                continue
            for index, block in enumerate(content):
                if not isinstance(block, dict):
                    continue
                if event.get("type") == "assistant" and block.get("type") == "tool_use":
                    data = block.get("input", {})
                    skill = (data.get("skill") or data.get("command")) if block.get("name") == "Skill" else None
                    call(block.get("id", f"{number}:{index}"), data, skill)
                elif block.get("type") == "tool_result":
                    content = block.get("content", "")
                    # Only the skill's provenance line is evidence in a result block.
                    texts = ([content] if isinstance(content, str) else
                             [part.get("text", "") for part in content if isinstance(part, dict)]
                             if isinstance(content, list) else [])
                    for text in texts:
                        for match in re.finditer(r"Base directory for this skill:\s*([^\n]+)", text):
                            paths(match[1], base_directory=True)
        elif host == "codex" and event.get("type", "").startswith("item."):
            item = event.get("item", {})
            if isinstance(item, dict) and item.get("type") not in (None, "agent_message", "reasoning"):
                value = item.get("command", "") if item.get("type") == "command_execution" else item
                call(item.get("id", str(number)), value)
        elif host == "grok":
            # ACP updates may be carried directly or in a JSON-RPC params envelope.
            update = event.get("params", {}).get("update", event) if isinstance(event.get("params"), dict) else event
            if update.get("sessionUpdate") in ("tool_call", "tool_call_update"):
                call(update.get("toolCallId", str(number)),
                     [update.get(key, "") for key in ("title", "rawInput", "locations")])
    return result


def catalog_names(host, output):
    if host == "claude":
        for event in json_lines(output):
            if event.get("type") == "system" and event.get("subtype") == "init":
                values = event.get("skills", event.get("slash_commands", []))
                if not isinstance(values, list):
                    raise ValueError("init skills is not a list")
                return {entry if isinstance(entry, str) else entry.get("name", "")
                        for entry in values if isinstance(entry, (str, dict))}
        raise ValueError("no system/init catalog message")
    if host == "codex":
        json.loads(output)  # An unreadable prompt dump is not an empty catalog.
        return set(re.findall(r"/([^/\s\"]+)/SKILL\.md", output))
    data = json.loads(output)
    found = set()

    def visit(value):
        if isinstance(value, dict):
            source = value.get("source")
            if (isinstance(source, dict) and isinstance(source.get("path"), str)
                    and source["path"].endswith("SKILL.md") and isinstance(value.get("name"), str)):
                found.add(value["name"])
            for entry in value.values():
                visit(entry)
        elif isinstance(value, list):
            for entry in value:
                visit(entry)
    visit(data)
    return found


def catalog_gate(host, repo, env, tested_names):
    if not shutil.which(host):
        return "CANNOT-RUN-UNATTENDED", f"{host} binary absent from PATH; no session started"
    argv = (host_command(host, "Reply with OK only.", tools="") if host == "claude"
            else ["codex", "debug", "prompt-input"] if host == "codex"
            else ["grok", "inspect", "--json"])
    result = run(argv, repo, env)
    if result.returncode != 0 and host != "claude":
        return "CANNOT-RUN-UNATTENDED", f"empty-repository catalog exit={result.returncode}; {short(result.stderr)}; no session started"
    try:
        names = catalog_names(host, result.stdout)
    except (ValueError, TypeError) as exc:
        return "CANNOT-RUN-UNATTENDED", f"empty-repository catalog unreadable: {exc}; {short(result.stderr)}; no session started"
    overlap = sorted(names & tested_names)
    if overlap:
        return "NEEDS-USER-CONFIG", ("catalog of an empty repository already lists " + ",".join(overlap)
                                     + " from user level; no session started")
    return None


def measure(host, row, phase, repo, env, scratch, tested_names):
    result = run(host_command(host, row.text + SUFFIX), repo, env)
    parsed = parse_events(host, result.stdout, scratch, tested_names)
    if parsed["leaks"]:
        return ("NEEDS-USER-CONFIG", "user-level skill path read: " + ",".join(parsed["leaks"])), result
    expected = row.expected(phase)
    loaded = reached(expected, parsed["skills"], parsed["playbooks"])
    if result.returncode == 124 or (result.returncode != 0 and not loaded):
        return ("CANNOT-RUN-UNATTENDED", f"exit={result.returncode}; {short(result.stderr)}; expected={expected}"), result
    evidence = (f"skills={','.join(parsed['skills']) or 'none'} "
                f"playbooks={','.join(parsed['playbooks']) or 'none'}; "
                f"tool-calls={parsed['tool_calls']}; expected={expected}; exit={result.returncode}")
    return ("PASS" if loaded else "FAIL", evidence), result


def cell(row, host, phase, result, versions, commits):
    status, evidence = result
    return (f"U-7 {row.id} {host} {phase} {status} {host}={versions[host]} "
            f"{commits[phase]} {datetime.now(timezone.utc).date()} : {short(evidence)}")


@contextmanager
def moved_skills(home=None):
    home = Path.home() if home is None else Path(home)
    staging = Path(subprocess.check_output(["mktemp", "-d"], text=True).strip()).resolve()
    print(f"U7 OWNER staging: {staging}; if killed, move entries back to ~/.agents/skills "
          "or ~/.claude/skills (each staging subdirectory names its original location)", file=sys.stderr, flush=True)
    moved = []
    try:
        for relative in (".agents/skills", ".claude/skills"):
            directory = home / relative
            if not directory.is_dir():
                continue
            for entry in sorted(directory.iterdir()):
                if entry.is_symlink() and any(part in os.readlink(entry) for part in MMW_TARGETS):
                    destination = staging / relative / entry.name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    entry.rename(destination)
                    moved.append((entry, destination))
        yield staging
    finally:
        for original, destination in reversed(moved):
            if original.exists() or original.is_symlink():
                raise RuntimeError(f"cannot restore {original}: occupied; recover it from {staging}")
            destination.rename(original)
        shutil.rmtree(staging)


def args_parse(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", action="store_true")
    parser.add_argument("--ticket", type=int)
    args = parser.parse_args(argv)
    if args.owner and (args.ticket is None or args.ticket < 1):
        parser.error("--owner requires --ticket with a positive issue number")
    if args.ticket is not None and not args.owner:
        parser.error("--ticket is only valid with --owner")
    return args


def measure_sets(hosts, rows, commits):
    lines = []
    with ExitStack() as stack:
        sets = {phase: install_set(commit, stack) for phase, commit in commits.items()}
        scratch = stack.enter_context(temporary_directory())
        tested_names = set().union(*(names for _, names in sets.values()))
        for host in hosts:
            env_home = scratch / (host + "-mmw")
            env_home.mkdir()
            env = child_env(env_home, host)
            version = run([host, "--version"]) if shutil.which(host) else None
            versions = {host: short(version.stdout or version.stderr).replace(" ", "_") if version else "absent"}
            empty_repo = scratch / (host + "-catalog")
            prepare(empty_repo, host)
            print(f"U7 catalog {host} {versions[host]}", flush=True)
            gate = catalog_gate(host, empty_repo, env, tested_names)
            if gate:
                print(f"U7 {host}: {gate[0]}: {gate[1]}", flush=True)
                lines.extend(cell(row, host, phase, gate, versions, commits) for row in rows for phase in PHASES)
                continue
            repos = {}
            for phase in PHASES:
                repos[phase] = scratch / f"{host}-{phase}"
                prepare(repos[phase], host, sets[phase][0])
            # S07 after is also its actual measurement, not a 67th paid session.
            first = next(row for row in rows if row.id == "S07")
            first_result, raw = measure(host, first, "after", repos["after"], env, scratch, tested_names)
            parsed = parse_events(host, raw.stdout, scratch, tested_names)
            print(f"U7 event sample {host} S07 after: {first_result[0]}; "
                  f"tool-calls={parsed['tool_calls']}", flush=True)
            print(raw.stdout, flush=True)
            claims = re.findall(r"LOADED:\s*([^\n\"\\]+)", raw.stdout)
            claims_read = any(claim.strip().lower() not in ("none", "nothing", "no files") for claim in claims)
            if parsed["tool_calls"] == 0 and claims_read:
                raise RuntimeError(f"{host} S07 after reply contains LOADED but no tool calls parsed; "
                                   "inspect the event sample and correct the parser before measuring more cells")
            for row in rows:
                for phase in PHASES:
                    result = first_result if row.id == "S07" and phase == "after" else measure(
                        host, row, phase, repos[phase], env, scratch, tested_names)[0]
                    line = cell(row, host, phase, result, versions, commits)
                    print(line, flush=True)
                    lines.append(line)
    return lines


def main(argv=None):
    args = args_parse(argv)  # No directories or user-level changes before validation.
    rows = read_sentences()
    hosts = list(HOSTS)
    if args.owner:
        path = HERE / "results-u7.md"
        if not path.is_file():
            print(f"U7 FAIL: {path} does not exist; run the unattended U-7 probe first")
            return 1
        hosts = sorted({match[2] for line in path.read_text(encoding="utf-8").splitlines()
                        if (match := CELL_LINE.fullmatch(line)) and
                        match[4] in ("NEEDS-USER-CONFIG", "CANNOT-RUN-UNATTENDED")})
        if not hosts:
            print("U7 OWNER nothing to re-measure in results-u7.md")
            return 0
    clean = run(["git", "status", "--porcelain", "--", "mmw-v2"], ROOT)
    if clean.returncode or clean.stdout:
        print("U7 FAIL: mmw-v2 has uncommitted changes; commit the measured skill set first")
        return 1
    commits = {"before": BEFORE, "after": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    before = checksum()
    previous = {}

    def interrupted(signum, frame):
        raise RuntimeError(f"interrupted by signal {signum}; no measurement written")

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, interrupted)
        with ExitStack() as stack:
            if args.owner:
                stack.enter_context(moved_skills())
            lines = measure_sets(hosts, rows, commits)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"U7 FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        after = checksum()
        if before != after:
            changed = ", ".join(name for name in CONFIG_PATHS if before[name] != after[name])
            print(f"U7 FAIL: user-level paths changed: {changed}; compare the hashes before using this measurement",
                  file=sys.stderr)
            print("\n".join(checksum_lines("before", before) + checksum_lines("after", after)), file=sys.stderr)
    if before != after:
        return 1
    lines.extend(checksum_lines("before", before) + checksum_lines("after", after))
    text = "# U-7 measurements\n\n" + "\n".join(lines) + "\n"
    if args.owner:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".md") as body:
            body.write(text)
            body.flush()
            posted = run(["gh", "issue", "comment", str(args.ticket), "--body-file", body.name], ROOT)
        if posted.returncode:
            print(f"U7 FAIL: issue comment exit={posted.returncode}; {short(posted.stderr)}", file=sys.stderr)
            print(text, file=sys.stderr)
            return 1
        print(posted.stdout.strip())
        return 0
    path = HERE / "results-u7.md"
    path.write_text(text, encoding="utf-8")
    return report(path)


if __name__ == "__main__":
    sys.exit(main())
