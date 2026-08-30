#!/usr/bin/env python3
"""The one thing a worker may not do by hand: take its ticket out of the agent lane.

A ticket closes through `verify-ticket.py <n> --closeout <draft>`, which checks the
closing comment, posts it, and only then closes the ticket. `gh issue close` skips all
of that and leaves a closed ticket nobody can read in the morning. So every host asks
this file before running a shell command, and this file refuses that one command.

    hook.py pretool <host>   the host is about to run a shell command

`<host>` is one of claude, codex, grok, cursor, pi. It decides only the shape of the
answer; the decision and the sentence are the same for all five.

It refuses rather than checks. A worker typing `gh issue close` has by definition not
been through `--closeout`, so there is no draft of its to check; a gate that guessed
one and let the command through when the guess passed would produce exactly the
outcome it exists to prevent — the ticket closed with no closing comment on it.

Whether this session is governed is not something this file works out. It is told:
the dispatcher sets `MMW_TICKET` on the worker's pane. No variable, no gate. So there
is no git to run, no `gh` to ask, no file to read, and nothing to get wrong about
which directory the host happened to start this process in.
"""

from __future__ import annotations

import json
import re
import os
import sys

HOSTS = ("claude", "codex", "grok", "cursor", "pi")
GATES = ("pretool",)

# Grok Build clips a deny reason at 256 characters and marks the rest `… [+N chars]`,
# and it spends 13 of those on a `Hook denied: ` of its own (2026-08-29, measured: a
# 350-character reason reached the model as its first 256). Everything a refused worker
# needs — the ticket, the command, the way out when the work is not finished — has to fit
# in what is left, for every ticket number this tracker will reach.
REASON_LIMIT = 256
HOST_PREFIX = len("Hook denied: ")

REFUSAL = (
    "Close #{n} with `verify-ticket.py {n} --closeout <draft>`, not by hand: it checks the "
    "closing comment, posts it, then closes the ticket. Write it to a file and run that. "
    "Unfinished work leaves the same way, first line `HANDOFF REQUIRED`."
)


def read_event() -> dict:
    """The host's event, whatever it managed to send. An unreadable one is empty."""
    try:
        value = json.loads(sys.stdin.read())
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def command_of(event: dict) -> str | None:
    """The shell command this event is about, in whichever way its host spelled it.

    Claude Code, Codex and the JSON pi's extension builds nest it under `tool_input`,
    Grok Build under `toolInput`, Cursor puts it at the top level. This is the only
    place those three spellings meet.
    """
    for name in ("tool_input.command", "toolInput.command", "command"):
        value = event
        for part in name.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        if isinstance(value, str) and value:
            return value
    return None


def governed_ticket() -> int | None:
    """The ticket this session was dispatched to work, if it was dispatched at all.

    `dispatch.sh` injects this when it opens the worker's tab. The main agent's
    session and an ordinary session of yours carry no such variable and are never
    governed. A reviewer session that inherited one is no exception worth making: it
    has no business closing the ticket either.
    """
    value = os.environ.get("MMW_TICKET", "").strip()
    return int(value) if value.isdigit() else None


SEPARATORS = re.compile(r"[;\n]|&&|\|\||\|")
LEADING_ASSIGNMENTS = re.compile(r"^(?:\w+=\S*\s+)*")


def runs(command: str) -> list[str]:
    """The pieces of `command` that a shell would run as commands of their own.

    Where the ticket number and the words `gh issue close` appear is not the same
    question as whether this command closes anything. A worker writing its closing
    comment says in it that it did not close the ticket by hand — and that sentence,
    inside the `cat` that writes the draft, is not a `gh` call. Splitting on the shell's
    own separators and keeping only the pieces that start with `gh` tells the two apart:
    prose lands mid-line, a command starts one. (2026-08-30: a worker hit exactly this
    on the first unconstrained run of the gate.)
    """
    out = []
    for piece in SEPARATORS.split(command):
        piece = LEADING_ASSIGNMENTS.sub("", piece.strip())
        if re.match(r"gh\b", piece):
            out.append(piece)
    return out


def leaves_the_agent_lane(command: str, number: int) -> bool:
    """True for the two commands that would finish ticket `number` without the closeout.

    Closing it, and taking off the label that says an agent is on it. Both are
    `--closeout`'s to make once the draft has passed.
    """
    for run in runs(command):
        if not re.search(rf"(?<!\d){number}(?!\d)", run):
            continue
        if re.match(r"gh\s+issue\s+close\b", run):
            return True
        if re.match(r"gh\s+issue\s+edit\b", run) \
                and re.search(r"--remove-label[=\s]+['\"]?ready-for-agent"
                              r"|--add-label[=\s]+['\"]?(needs-triage|ready-for-human)", run):
            return True
    return False


def refuse(host: str, reason: str) -> None:
    """Say no in this host's own vocabulary, on stdout, exiting 0 either way."""
    if host in ("claude", "codex"):
        answer = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                         "permissionDecision": "deny",
                                         "permissionDecisionReason": reason}}
    elif host == "grok":
        answer = {"decision": "deny", "reason": reason}
    elif host == "cursor":
        # `user_message` is what the client shows; `agent_message` is what the model
        # reads, and the model is the one that has to do something about it.
        answer = {"permission": "deny", "user_message": reason, "agent_message": reason}
    else:
        answer = {"block": True, "reason": reason}
    print(json.dumps(answer, ensure_ascii=False))


def run_pretool(host: str, event: dict) -> int:
    number = governed_ticket()
    if number is None:
        return 0
    command = command_of(event)
    if command is None or not leaves_the_agent_lane(command, number):
        return 0
    refuse(host, REFUSAL.format(n=number))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in GATES or argv[1] not in HOSTS:
        sys.stderr.write(f"usage: hook.py <{'|'.join(GATES)}> <{'|'.join(HOSTS)}>\n")
        return 0
    return run_pretool(argv[1], read_event())


if __name__ == "__main__":
    sys.exit(main())
