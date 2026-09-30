#!/usr/bin/env python3
"""Auxiliary context injection, not an ADR 0008 gate: failure is silent by design.

U-2 measured all three events on Claude Code 2.1.285 and Codex 0.159.2,
2026-09-30; Grok 1.0.45 could not inject them. See probe results and #613.
"""


def load_locations():
    import importlib.util
    from pathlib import Path

    here = Path(__file__).resolve().parent
    candidates = (here / "locations.py",
                  here.parents[2].joinpath("skills", "dispatch", "scripts", "locations.py"))
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("mode_hook_locations", path)
    locations = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(locations)
    return path, locations


def dispatch_context(cwd):
    import re
    import sys

    path, locations = load_locations()
    scripts = path.parents[2] / locations.DISPATCH_SCRIPTS
    dispatch = scripts / "dispatch.sh"
    if not dispatch.is_file():
        raise FileNotFoundError(dispatch)
    governed = any(re.fullmatch(locations.GOVERNED_TICKET_DIR_PATTERN, directory.name)
                   for directory in (cwd, *cwd.parents))
    if not governed:
        identity = run_dispatch(dispatch, "self", cwd, 5)
        if identity is None:
            return None
        runner, session = identity.rstrip("\n").split("\t")
        if not runner or not session:
            raise ValueError("empty session identity")
        sys.path.insert(0, str(scripts))
        from statedir import repo_state_dirs
        from relay import read_watches

        governed = any(watch.get("runner") == runner and watch.get("session") == session
                       for directory in repo_state_dirs()
                       for watch in read_watches(directory).values())
    if not governed:
        return None
    answer = run_dispatch(dispatch, "where", cwd, 20)
    if answer is None:
        raise ValueError("where failed")
    lines = answer.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        raise ValueError("where did not return one line")
    return lines[0]


def run_dispatch(dispatch, command, cwd, timeout):
    import os
    import signal
    import subprocess

    # The group contains only our child and its descendants. Terminating all of
    # them also releases pipes held by a stalled gh after bash has timed out.
    with subprocess.Popen(["bash", str(dispatch), command], cwd=cwd,
                          stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True, start_new_session=True) as child:
        try:
            stdout, _ = child.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.communicate()
            raise
        return stdout if child.returncode == 0 else None


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
        if not (root / ".mmw").is_dir() and not (root / "docs/agents/issue-tracker.md").is_file():
            return
        context = ("New task here? Playbook match or rigor needed → apply the mmw skill. "
                   "Casual turn or user opts out → don't.")
        if event == "subagent-start":
            _, locations = load_locations()
            context = f"Use the mmw skill: read its `{locations.MODE_PRINCIPLES}` and the step you serve."
        elif event == "session-start":
            context = dispatch_context(cwd) or context
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": names[event], "additionalContext": context}}))
    except BaseException:
        # No error in this auxiliary path may refuse a prompt or a turn.
        return


if __name__ == "__main__":
    main()
