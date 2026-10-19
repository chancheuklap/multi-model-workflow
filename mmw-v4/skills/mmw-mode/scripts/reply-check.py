#!/usr/bin/env python3
"""Check the reply at an owner-facing session's Stop event.

    reply-check.py stop <claude|codex>     the host's Stop payload on stdin

Both hosts supply the final reply in `last_assistant_message` and the session's working
directory in `cwd`. Ticket worktrees, open brief sessions, open-watch orchestrators and
`stop_hook_active` continuations end unchecked. Session identity is read through the turn
guard's own_brief and is_main predicates, without arming a watchdog or writing state.

A hit maps the phrase to its replacement instruction. Pointer phrases call for the content
itself in place. Chinese _Avoid_ wordings in docs/contexts/*/CONTEXT.md call for the entry's
name. English wordings and parenthesized qualifications are not matched. The repository is
the nearest parent with a .git entry, or cwd when there is none. No glossary is required.

Exit 0 allows the stop. Exit 2 lists the hits and replacements on stderr, which both hosts
send to the model to continue the turn. An error of this check exits 1 with the reason on
stderr and never blocks. The check writes no files and asks no tracker.

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
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys

POINTERS = re.compile(
    r"上一条|上面列的|前面列的|"
    r"如上(?=$|[^\u3400-\u9fff]|所|述|文|面)|"
    r"见上(?=$|[^\u3400-\u9fff]|文|面|述|图|表|节|一条)|"
    r"(?:上文|前文)(?![档件字本])|"
    r"\b(?:the ones above|as above|see above|point\s+[0-9]+)\b", re.IGNORECASE)


def avoided_wordings(cwd: Path) -> dict[str, str]:
    repo = next((path for path in (cwd, *cwd.parents) if (path / ".git").exists()), cwd)
    avoided = {}
    for path in sorted(repo.glob("docs/contexts/*/CONTEXT.md")):
        term = None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"cannot read glossary {path}: {exc}") from exc
        for line in lines:
            heading = re.match(r"^\*\*(.+?)\*\*", line)
            if heading:
                term = heading.group(1)
            if term and line.startswith("_Avoid_:"):
                wordings = re.sub(r"\([^)]*\)|（[^）]*）", "", line.removeprefix("_Avoid_:"))
                for wording in re.split(r"[,;，；、]", wordings):
                    wording = wording.strip().strip("`")
                    if re.search(r"[\u3400-\u9fff]", wording):
                        avoided[wording] = term
    return avoided


def unattended() -> bool:
    path = Path(__file__).resolve().parents[2] / "dispatch/scripts/turn-guard.py"
    spec = importlib.util.spec_from_file_location("mmw_reply_turn_guard", path)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    root = guard.statedir.home() / "state"
    if not root.exists():
        return False
    dog = guard.load_watchdog()
    asked = {}
    for state in sorted(path for path in root.iterdir() if path.is_dir()):
        if guard.own_brief(state, asked) is not None or guard.is_main(state, dog, asked):
            return True
    return False


def check() -> int:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("expected a Stop payload object on stdin")
    if payload.get("stop_hook_active") is True:
        return 0
    cwd = Path(payload.get("cwd") or Path.cwd())
    if re.fullmatch(r"issue-[0-9]+", cwd.name):
        return 0
    if unattended():
        return 0
    reply = payload.get("last_assistant_message")
    if not isinstance(reply, str):
        raise ValueError("expected last_assistant_message to be the reply text in the Stop payload")
    hits = {match.group(): "write the content itself here, in place"
            for match in POINTERS.finditer(reply)}
    for wording, term in avoided_wordings(cwd).items():
        if wording in reply:
            hits[wording] = f"use {term}"
    if hits:
        sys.stderr.write("MMW reply check: rewrite the reply before ending this turn.\n")
        for phrase, replacement in hits.items():
            sys.stderr.write(f"- {phrase!r}: {replacement}.\n")
        return 2
    return 0


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "stop" or sys.argv[2] not in ("claude", "codex"):
        sys.stderr.write("usage: reply-check.py stop <claude|codex>\n")
        return 0
    try:
        return check()
    except BaseException as exc:
        sys.stderr.write(f"reply-check: could not check this reply: {exc!r}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
