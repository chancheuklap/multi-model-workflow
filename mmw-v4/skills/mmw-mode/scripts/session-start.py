#!/usr/bin/env python3
"""Add advisory MMW context on SessionStart and UserPromptSubmit for either host.

    session-start.py <claude|codex>    hook payload on stdin

Input is an event, cwd and optional source. Output uses only the common
hookSpecificOutput.additionalContext contract. Unknown events add nothing.
SessionStart preserves the start/compact pointer and lists glossary entry paths.
UserPromptSubmit supplies the shared terminology reminder and those paths.
The nearest .git file or directory selects the consuming repository, or cwd
outside Git. The script's real location selects the installed MMW checkout.
Only entry-file availability is checked. Definitions are left to the agent.
Errors report a diagnostic without payload contents and return 0.

Real-host cases and limitations are recorded by tests/session-start/verify_hosts.py.
"""

import json
from pathlib import Path
import sys


REMINDER = (
    "Use the current subject's glossary source names and definitions already in "
    "context, and follow its Avoid guidance. If definitions are missing or the topic "
    "changes, read the "
    "relevant CONTEXT.md through the available glossary entries. A name list alone "
    "is not a definition. Make each reference in owner-facing prose understandable "
    "in its sentence or paragraph. Add paths only for source lookup or verification."
)


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ("claude", "codex"):
            raise ValueError("host argument")
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("payload object")
        event = payload.get("hook_event_name")
        if event not in ("SessionStart", "UserPromptSubmit"):
            return 0
        context = REMINDER
        if event == "SessionStart":
            context = "Read the mmw-mode skill in full before anything else."
            if payload.get("source") == "compact":
                context = ("Your context was compacted: read the mmw-mode skill again in full, "
                           "then the file you work by and every file its current step names, "
                           "before you take that step.")
        cwd = Path(payload.get("cwd") or Path.cwd()).resolve(strict=True)
        if not cwd.is_dir():
            raise ValueError("cwd directory")
        repo = next((root for root in (cwd, *cwd.parents)
                     if (root / ".git").exists()), cwd)
        mmw = Path(__file__).resolve().parents[4]
        entries = []
        for root in dict.fromkeys((repo, mmw)):
            for name in ("CONTEXT-MAP.md", "CONTEXT.md"):
                path = root / name
                if path.is_file():
                    with path.open("rb"):
                        pass
                    entries.append(str(path))
                    break
        if entries:
            context += "\nGlossary entries:\n" + "\n".join(entries)
        output = {"hookSpecificOutput": {"hookEventName": event,
                                          "additionalContext": context}}
        sys.stdout.write(json.dumps(output) + "\n")
    except Exception as exc:
        sys.stderr.write(f"session-start: could not add context ({type(exc).__name__}); "
                         "check the hook payload, host argument and glossary paths.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
