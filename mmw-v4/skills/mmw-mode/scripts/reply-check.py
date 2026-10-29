#!/usr/bin/env python3
"""Ask the writer to reread owner-facing replies and Artifact pages once.

    reply-check.py stop <claude|codex>     the host's Stop payload on stdin
    reply-check.py artifact claude        the Artifact PreToolUse payload on stdin

Every unexempted Stop exits 2 with one stderr line pointing to a checklist file read
from the anchor-reference principle and MMW's and the working repository's glossaries.
The host's stop_hook_active continuation passes. A null last_assistant_message, ticket
worktree, open brief session or open-watch orchestrator also passes. Session identity
uses the turn guard's own_brief and is_main predicates without arming a watchdog or
asking the tracker.

The Artifact entry reads tool_input.file_path as the page, except when tool_input.asset
is true. Actions without a file_path pass. Ticket worktrees and unattended sessions pass.
A new SHA-256 of the page bytes is recorded under MMW_HOME/state/reply-check and exits 2;
an unchanged retry passes. Its checklist also includes the everything-at-hand principle.
Checklists are written beside those fingerprints as checklist-<first 12 hex of SHA-256>.md;
unchanged checklists reuse their files. Each block writes one instruction line to stderr.

Checklist rules load at run time from the sibling principle skills. For MMW's checkout
and then the working repository, CONTEXT-MAP.md links to CONTEXT.md files select the
glossaries in link order. Without a map, only the root CONTEXT.md loads, if present.
The working repository is the nearest parent with a .git entry, or cwd without one.
Identical glossary text appears only once, keeping MMW's first. Every registered name
and its _Avoid_: line stays in its original language. No glossary is required.
The writer judges the text against the checklist file.

Exit 0 allows the event. Exit 2 sends the checklist file path on stderr to the writer for
rereading and rewriting. Any exception exits 1 with its reason on stderr and does not block.

Checked against the real hosts
------------------------------
2026-10-19. An isolated Stop command captured each payload, blocked the first stop with
exit 2 and stderr asking for NOTED, then allowed stop_hook_active. Both payloads carried
last_assistant_message="OK", then last_assistant_message="NOTED" with stop_hook_active=true.

    claude 2.1.303   claude -p --setting-sources project --settings <temporary settings.json>
                    --no-session-persistence --tools '' -- <prompt>. Real HOME for the
                    keychain login; temporary MMW_HOME and working directory. Replied NOTED.
    codex 0.163.0    codex exec --ephemeral --skip-git-repo-check -C <temporary directory>,
                    with temporary CODEX_HOME, an auth.json copy and features.hooks=true.
                    The trusted_hash used install.sh's algorithm, with the canonical path
                    to hooks.json, without bypassing hook trust. Stop Blocked, NOTED, then
                    Stop Completed. A /var alias for /private/var did not match hook trust.

The final check also ran through both hosts with install.sh's actual registrations in a
throwaway MMW_INSTALL_HOME, fake install tools and temporary MMW_HOME. Prompt: reply exactly
"see above"; if blocked, reply "The plan is complete." Neither host used tools. Both blocked
the first reply and ended with the rewritten reply. Codex reported Stop Blocked followed
by Stop Completed. The installed runtime and its hooks were not changed. Repeat the payload
and block check for each host upgrade.

2026-10-29. Artifact evidence from the owner's interactive Claude Code 2.1.312 session
03751731-80ce-4542-8cf0-f95e853607c1, signed in to claude.ai. The orchestrator inspected
~/.claude/projects/-Users-cheuklapchan-multi-model-workflow/
03751731-80ce-4542-8cf0-f95e853607c1.jsonl and recorded 21 tool_use blocks named Artifact:
https://github.com/chancheuklap/multi-model-workflow/issues/1427#issuecomment-6491508145
Publish inputs carry file_path with icon and description. Quickstart inputs carry action,
intent and design_systems without file_path. Asset uploads carry file_path and asset=true.
PreToolUse exposes the input as tool_input and the name as tool_name="Artifact".
This is interactive-session transcript evidence, not a captured hook run. The same host
version's claude -p exposes no Artifact tool, even with --tools Artifact; print mode cannot
verify this interactive-only capability. The installed runtime was not changed.

"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


def checklist(cwd: Path, artifact: bool = False) -> Path:
    skills = Path(__file__).resolve().parents[2]
    names = ["principle-anchor-every-reference"]
    if artifact:
        names.append("principle-everything-at-hand")
    parts = []
    for name in names:
        path = skills / name / "SKILL.md"
        pattern = path.read_text(encoding="utf-8").split("**Pattern:**\n", 1)[1]
        parts.append(f"{path}\n**Pattern:**\n" + pattern.lstrip("\n").split("\n\n", 1)[0])
    parts.extend(glossary_entries(cwd))
    parts.append("A name not registered above is written as a plain description, "
                 "or proposed to the owner before it is used.")
    content = "\n\n".join(parts) + "\n"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    state = turn_guard().statedir
    path = state.home() / "state/reply-check" / f"checklist-{digest}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        state.write_atomic(path, content)
    return path


def glossary_entries(cwd: Path) -> list[str]:
    repo = next((path for path in (cwd, *cwd.parents) if (path / ".git").exists()), None)
    mmw = Path(__file__).resolve().parents[4]
    paths = []
    for root in (mmw, repo or cwd):
        context_map = root / "CONTEXT-MAP.md"
        if context_map.is_file():
            for link in re.findall(r"\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)",
                                   context_map.read_text(encoding="utf-8")):
                path = context_map.parent / link.strip("<>").split("#", 1)[0]
                if path.name == "CONTEXT.md":
                    paths.append(path)
        elif (root / "CONTEXT.md").is_file():
            paths.append(root / "CONTEXT.md")
    entries = []
    seen = set()
    for path in paths:
        entry = [str(path)]
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"cannot read glossary {path}: {exc}") from exc
        if text in seen:
            continue
        seen.add(text)
        for line in text.splitlines():
            heading = re.match(r"^\*\*(.+?)\*\*", line)
            if heading:
                entry.append(heading.group(1))
            if line.startswith("_Avoid_:") and len(entry) > 1:
                entry.append(line)
        entries.append("\n".join(entry))
    return entries


def turn_guard():
    path = Path(__file__).resolve().parents[2] / "dispatch/scripts/turn-guard.py"
    spec = importlib.util.spec_from_file_location("mmw_reply_turn_guard", path)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    return guard


def unattended() -> bool:
    guard = turn_guard()
    root = guard.statedir.home() / "state"
    if not root.exists():
        return False
    dog = guard.load_watchdog()
    asked = {}
    for state in sorted(path for path in root.iterdir() if path.is_dir()):
        if guard.own_brief(state, asked) is not None or guard.is_main(state, dog, asked):
            return True
    return False


def check(entry: str) -> int:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("expected a hook payload object on stdin")
    if entry == "stop" and payload.get("stop_hook_active") is True:
        return 0
    cwd = Path(payload.get("cwd") or Path.cwd())
    if re.fullmatch(r"issue-[0-9]+", cwd.name):
        return 0
    if unattended():
        return 0
    if entry == "artifact":
        tool_input = payload.get("tool_input", {})
        if not tool_input.get("file_path") or tool_input.get("asset") is True:
            return 0
        page = Path(tool_input["file_path"])
        if not page.is_absolute():
            page = cwd / page
        digest = hashlib.sha256(page.read_bytes()).hexdigest()
        fingerprint = turn_guard().statedir.home() / "state/reply-check" / digest
        if fingerprint.exists():
            return 0
        checklist_path = checklist(cwd, artifact=True)
        fingerprint.parent.mkdir(parents=True, exist_ok=True)
        try:
            fingerprint.touch(exist_ok=False)
        except FileExistsError:
            return 0
        sys.stderr.write(f"MMW reply check: reread {page} against {checklist_path}, "
                         "rewrite what breaks it, then publish again.\n")
        return 2
    reply = payload["last_assistant_message"]
    if reply is None:
        return 0
    if not isinstance(reply, str):
        raise ValueError("expected last_assistant_message to be the reply text in the Stop payload")
    checklist_path = checklist(cwd)
    sys.stderr.write(f"MMW reply check: reread what you wrote for the owner against {checklist_path}, "
                     "rewrite what breaks it, then finish again.\n")
    return 2


def main() -> int:
    if len(sys.argv) != 3 or (sys.argv[1], sys.argv[2]) not in (
            ("stop", "claude"), ("stop", "codex"), ("artifact", "claude")):
        sys.stderr.write("usage: reply-check.py stop <claude|codex> | artifact claude\n")
        return 0
    try:
        return check(sys.argv[1])
    except BaseException as exc:
        sys.stderr.write(f"reply-check: could not check {sys.argv[1]}: {exc!r}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
