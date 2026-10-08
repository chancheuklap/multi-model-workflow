#!/usr/bin/env python3
"""SessionStart hook: in a repository MMW has onboarded, have the session read the mode.

    mode-hook.py session-start claude|codex

The host hands the session's payload on stdin. When the repository the session works in
(the nearest directory up from `cwd` with a `.git`) has a `.mmw/` directory, which
setup-mmw gives every repository it onboards, this prints the host's SessionStart answer
with one line of added context: read this skill's SKILL.md in full before any work. It
names the file by path so that every session there reads the mode, whether or not
the model would load the skill on its own. Outside such a
repository it prints nothing.

It only adds context and never decides anything, so every failure is silent: no error
here may hold up a session.
"""

import json
import os
import sys
from pathlib import Path

EVENTS = {"session-start": "SessionStart"}
HOSTS = ("claude", "codex")


def main(argv):
    try:
        event, host = argv
        if event not in EVENTS or host not in HOSTS:
            return
        payload = json.load(sys.stdin)
        # Cursor also reads ~/.claude/settings.json and runs this entry; its payload carries
        # cursor_version, and its answer has another shape, so the hook stands down.
        if "cursor_version" in payload:
            return
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
        root = next((p for p in (cwd, *cwd.parents) if (p / ".git").exists()), None)
        if root is None or not (root / ".mmw").is_dir():
            return
        # The path the host called this script by: under ~/.agents/skills, so it names the
        # installed skill whichever checkout the install points at.
        mode = Path(sys.argv[0]).absolute().parent.parent / "SKILL.md"
        context = (f"This repository uses MMW. Before any work, read the mmw-mode skill's "
                   f"SKILL.md in full: {mode}")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": EVENTS[event], "additionalContext": context}}))
    except BaseException:
        return


if __name__ == "__main__":
    main(sys.argv[1:])
