#!/usr/bin/env python3
"""Report a session's own turn state to Herdr, from the host's lifecycle hooks.

    turn.py <host>      the host's hook event is on stdin as JSON

`<host>` is one of claude, codex, grok. Each host registers this script on the
events its hook system fires, and each event maps to one lifecycle state and one
`turn` pane token:

    event                          report-agent   turn token
    SessionStart                   idle           ready
    UserPromptSubmit               working        working
    Stop  (grok: reason end_turn)  idle           ended
    StopFailure                    idle           failed:<error>
    StopCancelled                  idle           cancelled:<reason>
    Notification idle_prompt       idle           (unchanged)
    SessionEnd                     release        (cleared)

`report-agent` makes this script the pane's lifecycle authority: Herdr stops
reading the session's state off its screen for as long as the authority is held,
which is what makes `agent_status` a fact rather than a guess. The `turn` token is
what `board.py` reads to tell a turn that failed on the network from one the
session ended itself.

The script does nothing outside Herdr — no `HERDR_ENV`, no `HERDR_PANE_ID`, exit 0
— and nothing for a subagent's events, whose stop is not the session's. A report
for a turn older than the newest one started is dropped: a cancelled turn's report
can arrive after the next turn's `UserPromptSubmit`. A `SessionStart` that arrives
once a turn is already on the pane is dropped too: grok fires it with the first
prompt, not when the process starts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

HOSTS = ("claude", "codex", "grok")
TOKEN_TTL_MS = "86400000"       # a day, the same TTL every other pane token carries

# The lifecycle authority is one source per host, so a second copy of this script
# on the same pane — the reviewer's, the main agent's — reports under the same name.
SOURCE = "mmw:{host}"
TOKEN_SOURCE = "mmw"            # the source `dispatch.sh` and `verify-ticket.py` write tokens under


def read_event() -> dict:
    try:
        value = json.loads(sys.stdin.read())
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def event_name(event: dict) -> str:
    """The event's name in Claude Code's PascalCase, whichever host sent it.

    Grok writes both spellings, `hook_event_name` PascalCase and `hookEventName`
    snake_case; Claude Code and Codex write only the first.
    """
    name = event.get("hook_event_name")
    if isinstance(name, str) and name:
        return name
    name = event.get("hookEventName")
    if isinstance(name, str) and name:
        return "".join(part.capitalize() for part in name.split("_"))
    return ""


def field(event: dict, *names: str) -> str:
    for name in names:
        value = event.get(name)
        if isinstance(value, str) and value:
            return value
    return ""


def is_subagent(event: dict) -> bool:
    """A subagent's event: grok marks it `subagentType`, Claude Code `agent_id`."""
    return bool(event.get("subagentType") or event.get("agent_id"))


def herdr() -> str:
    return os.environ.get("HERDR_BIN_PATH") or "herdr"


def run(args: list[str]) -> None:
    try:
        subprocess.run([herdr(), *args], capture_output=True, text=True, timeout=5)
    except Exception:
        pass


def pane_tokens(pane: str) -> dict:
    try:
        out = subprocess.run([herdr(), "pane", "get", pane], capture_output=True,
                             text=True, timeout=5)
        payload = json.loads(out.stdout)
        pane_info = (payload.get("result") or payload).get("pane") or {}
        return pane_info.get("tokens") or {}
    except Exception:
        return {}


def report(pane: str, host: str, state: str) -> None:
    run(["pane", "report-agent", pane, "--source", SOURCE.format(host=host),
         "--agent", host, "--state", state, "--seq", str(time.time_ns())])


def tokens(pane: str, set_: dict[str, str], clear: list[str] = ()) -> None:
    cmd = ["pane", "report-metadata", pane, "--source", TOKEN_SOURCE]
    for key, value in set_.items():
        cmd += ["--token", f"{key}={value}"]
    for key in clear:
        cmd += ["--clear-token", key]
    cmd += ["--ttl-ms", TOKEN_TTL_MS]
    run(cmd)


def release(pane: str, host: str) -> None:
    run(["pane", "release-agent", pane, "--source", SOURCE.format(host=host),
         "--agent", host])
    tokens(pane, {}, clear=["turn", "turn_id"])


def decide(host: str, event: dict, pane: str) -> tuple[str, dict[str, str] | None] | None:
    """(state, tokens) for this event, tokens None to leave them, or None to do nothing."""
    name = event_name(event)
    if is_subagent(event):
        return None
    if name == "SessionStart":
        # Grok fires this with the first prompt rather than when the process starts,
        # so a `turn` token may already be on the pane; reporting `idle` over it would
        # end a turn that is under way.
        if pane_tokens(pane).get("turn"):
            return None
        return "idle", {"turn": "ready", "turn_id": ""}
    if name == "UserPromptSubmit":
        turn_id = field(event, "promptId") or str(time.time_ns())
        return "working", {"turn": "working", "turn_id": turn_id}
    if name == "Stop":
        reason = field(event, "reason")
        # Grok fires a second, observe-only Stop at session end; SessionEnd covers it.
        if host == "grok" and reason and reason != "end_turn":
            return None
        return "idle", {"turn": "ended"}
    if name == "StopFailure":
        return "idle", {"turn": "failed:" + (field(event, "error") or "unknown")}
    if name == "StopCancelled":
        return "idle", {"turn": "cancelled:" + (field(event, "reason") or "unknown")}
    if name == "Notification":
        kind = field(event, "notificationType", "notification_type")
        return ("idle", None) if kind == "idle_prompt" else None
    if name == "SessionEnd":
        return "release", None
    return None


def stale(pane: str, event: dict) -> bool:
    """A turn-end report for a turn older than the one that started last."""
    prompt_id = field(event, "promptId")
    if not prompt_id:
        return False
    current = pane_tokens(pane).get("turn_id") or ""
    return bool(current) and current != prompt_id


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1 or argv[0] not in HOSTS:
        sys.stderr.write(f"usage: turn.py <{'|'.join(HOSTS)}>\n")
        return 0
    host = argv[0]
    if os.environ.get("HERDR_ENV") != "1":
        return 0
    pane = os.environ.get("HERDR_PANE_ID") or ""
    if not pane:
        return 0
    event = read_event()
    decision = decide(host, event, pane)
    if decision is None:
        return 0
    state, set_ = decision
    if state == "release":
        release(pane, host)
        return 0
    if state == "idle" and set_ is not None and set_.get("turn") != "ready" \
            and stale(pane, event):
        return 0
    report(pane, host, state)
    if set_ is not None:
        clear = [k for k, v in set_.items() if v == ""]
        tokens(pane, {k: v for k, v in set_.items() if v != ""}, clear=clear)
    return 0


if __name__ == "__main__":
    sys.exit(main())
