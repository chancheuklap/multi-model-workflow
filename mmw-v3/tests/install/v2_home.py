"""A test home that holds what mmw-v2/install.sh leaves on a machine.

Written by hand in the shapes mmw-v2/install.sh writes (its skill links, its
`~/.mmw/skill-copies/`, its hook registrations on all five hosts, its prompt
links and generated AGENTS.md files, its installed-root), next to entries other
tools own that an install must leave alone. mmw-v2's own install.sh is never run.
"""

import hashlib
import json
from pathlib import Path

from install_home import GROK_GUARD, REPO, SKILLS, executable

V2_SKILL_LINKS = {
    # v3 lists these names; v2 pointed them at its own sources or at a copy.
    "tdd": "upstream/skills/engineering/tdd",
    "to-spec": "skills/to-spec",
    "diagram-design": "upstream-diagram-design/skills/diagram-design",
    "triage": "<copies>/triage",
    "wayfinder": "<copies>/wayfinder",
    # v3 does not list these.
    "grill-me": "upstream/skills/productivity/grill-me",
    "mmw": "skills/mmw",
    "memory-records": "skills/memory-records",
    "pstack-thing": "upstream-pstack/skills/pstack-thing",
}
GONE_NAMES = ("grill-me", "mmw", "memory-records", "pstack-thing")


def _json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _v2_agents_md(body: str, host: str) -> str:
    digest = hashlib.sha256(body.encode()).hexdigest()
    return (f"<!-- mmw prompt-sync: generated from mmw-v2/prompt/shared.md + "
            f"mmw-v2/prompt/hosts/{host}.md; edit those, not this file. "
            f"body-sha256={digest} -->\n") + body


def build(home: Path, old_root: Path) -> dict:
    """Fill `home` as a v2 install from the checkout `old_root` (an mmw-v2 directory)
    would, and return the files a v3 install has to leave byte for byte as they are,
    with their text."""
    copies = home / ".mmw" / "skill-copies"
    launcher = home / ".mmw" / "bin" / "hook-launcher"

    # The v2 checkout the installed-root names. Its install.sh leaves a mark if anything runs it.
    (old_root / "prompt" / "hosts").mkdir(parents=True)
    (old_root / "prompt" / "shared.md").write_text("v2 shared prompt\n")
    (old_root / "prompt" / "hosts" / "claude.md").write_text("")
    executable(old_root / "install.sh",
               f"#!/bin/sh\necho ran > '{old_root / 'install-sh-ran'}'\necho V2-HANDOVER\nexit 0\n")

    for host in (".claude", ".codex", ".cursor", ".grok/hooks", ".pi/agent/extensions"):
        (home / host).mkdir(parents=True, exist_ok=True)
    (home / ".grok" / "config.toml").write_text("[compat.claude]\nagents = false\n")

    # Skills: v2's links in both install directories, the copies, a retired location.
    for name in ("triage", "wayfinder", "old-copy"):
        (copies / name).mkdir(parents=True)
        (copies / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: copy\n---\n")
    for dest in (home / ".agents" / "skills", home / ".claude" / "skills"):
        dest.mkdir(parents=True)
        for name, target in V2_SKILL_LINKS.items():
            target = (str(copies) + target[len("<copies>"):] if target.startswith("<copies>")
                      else str(old_root / target))
            (dest / name).symlink_to(target)
        (dest / "someone-else").symlink_to("/elsewhere/skills/someone-else")
        (dest / "my-own-skill").mkdir()
        (dest / "my-own-skill" / "SKILL.md").write_text("mine\n")
    for retired, target in ((home / ".cursor" / "skills", old_root / "upstream/skills/engineering/tdd"),
                            (home / ".codex" / "skills", copies / "triage")):
        retired.mkdir(parents=True)
        (retired / target.name).symlink_to(target)

    # Hooks, as v2 registers them.
    pretool = f"exec python3 '{launcher}' tool-guard pretool "
    question = f"exec python3 '{launcher}' tool-guard question "
    stop = f"exec python3 '{launcher}' turn-guard stop "

    def mode(host, argument):
        command = f"exec python3 '{launcher}' mode-hook {argument} {host}"
        return GROK_GUARD + command if host == "claude" else command

    def grouped(host, question_tool):
        guard = GROK_GUARD if host == "claude" else ""
        return {"hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [
                    {"type": "command", "command": guard + pretool + host, "timeout": 10},
                    {"type": "command", "command": "herdr hook pretool", "timeout": 5}]},
                {"matcher": question_tool, "hooks": [
                    {"type": "command", "command": guard + question + host, "timeout": 10}]},
            ],
            "Stop": [{"hooks": [{"type": "command", "command": guard + stop + host, "timeout": 30}]}],
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "nmem hook session-start", "timeout": 5}]},
                {"hooks": [{"type": "command", "command": mode(host, "session-start"), "timeout": 30}]},
            ],
            "SubagentStart": [{"hooks": [{"type": "command", "command": mode(host, "subagent-start"),
                                          "timeout": 10}]}],
            "UserPromptSubmit": [{"hooks": [{"type": "command", "command": mode(host, "prompt-submit"),
                                             "timeout": 10}]}],
        }}

    settings = grouped("claude", "AskUserQuestion")
    settings["permissions"] = {"allow": ["Bash(ls:*)"]}
    _json(home / ".claude" / "settings.json", settings)
    _json(home / ".codex" / "hooks.json", grouped("codex", "request_user_input"))
    (home / ".codex" / "config.toml").write_text(
        'model = "gpt-5"\n\n'
        f'[hooks.state."{home / ".codex" / "hooks.json"}:pre_tool_use:0:0"]\n'
        'trusted_hash = "sha256:' + "0" * 64 + '"\n')
    _json(home / ".cursor" / "hooks.json", {"version": 1, "hooks": {
        "beforeShellExecution": [{"command": pretool + "cursor", "timeout": 10}],
        "stop": [{"command": stop + "cursor", "timeout": 30, "loop_limit": 3}],
        "afterFileEdit": [{"command": "someone-else format", "timeout": 5}],
    }})
    _json(home / ".grok" / "hooks" / "mmw-verify-ticket.json", {"hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": pretool + "grok", "timeout": 10}]},
            {"matcher": "ask_user_question",
             "hooks": [{"type": "command", "command": question + "grok", "timeout": 10}]},
        ]}})
    _json(home / ".grok" / "hooks" / "mmw-turn-guard.json", {"hooks": {
        "Stop": [{"hooks": [{"type": "command", "command": stop + "grok", "timeout": 30}]}]}})
    _json(home / ".grok" / "hooks" / "someone-else.json", {"hooks": {
        "Stop": [{"hooks": [{"type": "command", "command": "someone-else stop", "timeout": 5}]}]}})
    for name in ("mmw-verify-ticket.ts", "mmw-turn-guard.ts"):
        (home / ".pi" / "agent" / "extensions" / name).write_text(
            f"// installed by mmw-v2/install.sh\nconst LAUNCHER = \"{launcher}\";\n")
    (home / ".pi" / "agent" / "extensions" / "someone-else.ts").write_text("// not ours\n")

    launcher.parent.mkdir(parents=True)
    launcher.write_bytes((REPO / "mmw-v2" / "hook-launcher.py").read_bytes())
    launcher.chmod(0o755)

    # Prompts: Claude Code's two links into v2, and the three files v2's render.py wrote.
    (home / ".claude" / "rules").mkdir()
    (home / ".claude" / "CLAUDE.md").symlink_to(old_root / "prompt" / "shared.md")
    (home / ".claude" / "rules" / "mmw-claude.md").symlink_to(old_root / "prompt" / "hosts" / "claude.md")
    shared = (old_root / "prompt" / "shared.md").read_text()
    for host, target in (("codex", home / ".codex" / "AGENTS.md"),
                         ("pi", home / ".pi" / "agent" / "AGENTS.md"),
                         ("grok", home / ".grok" / "AGENTS.md")):
        target.write_text(_v2_agents_md(shared, host))

    agents = home / "Library" / "LaunchAgents"
    agents.mkdir(parents=True)
    (agents / "com.mmw.prompt-sync.plist").write_text(f"<plist>{old_root / 'prompt'}</plist>\n")

    (home / ".mmw" / "installed-root").write_text(f"{old_root}\n")

    # models.json as v2 saved it: four rows, no researcher row.
    defaults = json.loads((SKILLS / "mmw-mode" / "hosts.json").read_text())["defaults"]
    rows = {row["agent"]: {key: row[key] for key in ("host", "model", "effort")}
            for row in defaults if row["agent"] != "researcher"}
    _json(home / ".mmw" / "models.json", {"version": 3, "runner": "orca", "rows": rows})

    # What other tools own on the same machine, and the saved models.json.
    kept = {
        home / ".mmw" / "models.json": (home / ".mmw" / "models.json").read_text(),
        agents / "com.mmw.board.plist": "<plist>board</plist>\n",
        home / ".mmw" / "board-bootstrapped-commit": "0" * 40 + "\n",
        home / ".mmw" / "boards.json": "{}\n",
        home / ".cursor" / "mcp.json": json.dumps({"mcpServers": {"nowledge-mem": {"url": "http://x"}}}) + "\n",
        home / ".pi" / "agent" / "extensions" / "someone-else.ts": "// not ours\n",
        home / ".grok" / "hooks" / "someone-else.json": (home / ".grok/hooks/someone-else.json").read_text(),
    }
    for path, text in kept.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return kept
