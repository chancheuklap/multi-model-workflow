#!/usr/bin/env python3
"""Auxiliary context injection, not an ADR 0008 gate: failure is silent by design.

U-2 measured all three events on Claude Code 2.1.285 and Codex 0.159.2,
2026-09-30; Grok 1.0.45 could not inject them. See probe results and #613.
"""


def load_locations():
    import importlib.util
    from pathlib import Path

    here = Path(__file__).resolve().parent
    path = here / "locations.py"
    spec = importlib.util.spec_from_file_location("mode_hook_locations", path)
    locations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(locations)
    return path, locations


def main():
    try:
        import json
        import os
        import sys
        from pathlib import Path

        event, host = sys.argv[1:]
        if host not in ("claude", "codex"):
            return
        names = {"session-start": "SessionStart", "subagent-start": "SubagentStart",
                 "prompt-submit": "UserPromptSubmit"}
        if event not in names:
            return
        payload = json.load(sys.stdin)
        cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
        root = next((p for p in (cwd, *cwd.parents) if (p / ".git").exists()), cwd)
        if not (root / ".mmw").is_dir():
            return
        context = ("New task here? Playbook match or rigor needed → apply the mmw-mode skill. "
                   "Casual turn or user opts out → don't.")
        if event == "subagent-start":
            _, locations = load_locations()
            context = (f"Use the mmw-mode skill: read its `{locations.MODE_PRINCIPLES}` "
                       "and the step you serve.")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": names[event], "additionalContext": context}}))
    except BaseException:
        # No error in this auxiliary path may refuse a prompt or a turn.
        return


if __name__ == "__main__":
    main()
