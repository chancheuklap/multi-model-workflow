#!/usr/bin/env python3
"""Add one MMW entry pointer to a host's SessionStart context.

    session-start.py <claude|codex>    SessionStart payload on stdin

Both hosts supply a JSON object with source. A compact source selects the re-read
pointer; every other source, including an absent one, selects the start pointer.
Both hosts accept one JSON line with hookSpecificOutput.hookEventName="SessionStart"
and hookSpecificOutput.additionalContext. Errors exit 0 without adding context.
No files, tracker or MMW state are read or written.

Checked against the real hosts
------------------------------
2026-10-27. An isolated SessionStart command captured each real payload, then passed
it to this script. Each payload contained hook_event_name="SessionStart" and
source="startup". Asked to quote only the hook's context without using tools, both
hosts replied exactly "Read the mmw-mode skill in full before anything else."

    claude 2.1.311   claude -p --setting-sources project --settings <temporary settings.json>
                    --no-session-persistence --tools '' -- <prompt>. Real HOME for
                    keychain login; temporary MMW_HOME and working directory.
    codex 0.163.0    codex exec --ephemeral --skip-git-repo-check -C <temporary directory>,
                    with temporary CODEX_HOME, an auth.json copy and features.hooks=true.
                    The canonical hooks.json path and install.sh's trusted_hash algorithm
                    enabled the registration without bypassing hook trust.

The compact, resume and clear payloads are process-test fixtures, not real-host
event captures. Claude's SessionStart contract lists startup, resume, clear and
compact at https://code.claude.com/docs/en/hooks#sessionstart. Codex's JSON context
contract is documented at https://learn.chatgpt.com/docs/hooks. The installed
runtime and its hooks were not changed. Repeat the real-host check after upgrades.
"""

import json
import sys


def main():
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in ("claude", "codex"):
            return 0
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        pointer = "Read the mmw-mode skill in full before anything else."
        if payload.get("source") == "compact":
            pointer = ("Your context was compacted: read the mmw-mode skill again in full, "
                       "then the file you work by and every file its current step names, "
                       "before you take that step.")
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                          "additionalContext": pointer}}
        sys.stdout.write(json.dumps(output) + "\n")
    except BaseException:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
