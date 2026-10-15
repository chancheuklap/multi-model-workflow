#!/usr/bin/env python3
"""Three things a dispatched session may not do: take its ticket out of the agent queue
by hand, put a question on the screen, and end a process.

A ticket closes through `verify-ticket.py <n> --closeout <draft>`, which checks the
closing comment, posts it, and only then closes the ticket. `gh issue close` skips all
of that and leaves a closed ticket nobody can read in the morning. So every host asks
this file before running a shell command, and this file refuses that one command.

A question on the screen has nobody to answer it: nothing in this pipeline reads a
form. So every host asks this file before calling its question tool, and this file
refuses the call and says where the question goes instead — the default taken and
recorded, or `ABANDON: AC<n> decision` with a sub-issue.

Ending a process is never this session's to do. Several runs share one machine, and
another run's application is indistinguishable from a stuck one, so a session that is
free to end what looks stuck is free to end a neighbour's work one second before it
finished. A run stops its own product as its `verify-<product>` skill says;
everything else is somebody else's, and a run that cannot reach its product
reports the ticket blocked rather than clearing the way to it.

    tool-guard.py pretool <host>    the host is about to run a shell command
    tool-guard.py question <host>   the host is about to ask the user a question

`<host>` is claude or codex. It names the host's question tool; the refusal has the same
shape and the same sentence on both.

It refuses rather than checks. A worker typing `gh issue close` has by definition not
been through `--closeout`, so there is no draft of its to check; a hook that guessed
one and let the command through when the guess passed would produce exactly the
outcome it exists to prevent — the ticket closed with no closing comment on it.

Whether this session is governed is read off the process, the same way for both gates
and on every runner: the working directory's basename. `issue-<n>` (digits only) is
ticket `<n>`, and every session a runner starts on a ticket — worker and reviewer —
runs in that worktree, with nobody at its screen. Any other basename is not a
ticket worktree and is not refused. Nothing is asked of any runner.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

HOSTS = ("claude", "codex")
GATES = ("pretool", "question")
TICKET_DIR = re.compile(r"^issue-(\d+)$")

REFUSAL = (
    "Close #{n} with `verify-ticket.py {n} --closeout <draft>`, not by hand: it checks the "
    "closing comment, posts it, then closes the ticket. Write it to a file and run that. "
    "Unfinished work leaves the same way, first line `HANDOFF REQUIRED`."
)

# The same length rule. Nobody is at the screen; the two ways out are the ones the
# Work a ticket playbook gives.
NO_QUESTION = (
    "Nobody is at the screen. Take the likeliest option and note it under `Decisions I "
    "made on my own`; if the answer changes what the ticket delivers, write `ABANDON: "
    "AC<n> decision <question, options, default>` and open a needs-triage sub-issue."
)

# The tool each host calls to put a question on the screen.
QUESTION_TOOLS = {
    "claude": ("AskUserQuestion",),
    "codex": ("request_user_input",),
}


def read_event() -> dict:
    """The host's event, whatever it managed to send. An unreadable one is empty."""
    try:
        value = json.loads(sys.stdin.read())
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def command_of(event: dict) -> str | None:
    """The shell command this event is about: Claude Code and Codex both nest it under
    `tool_input`."""
    tool_input = event.get("tool_input")
    value = tool_input.get("command") if isinstance(tool_input, dict) else None
    return value if isinstance(value, str) and value else None


def tool_of(event: dict) -> str:
    """The tool this event is about."""
    value = event.get("tool_name")
    return value if isinstance(value, str) else ""


def governed_ticket() -> int | None:
    """The ticket this session belongs to, if it is a ticket worktree.

    The slug is `issue-<n>`. Reviewer and worker share that directory
    and are all governed. A session in no such directory is not.

    Two places say where the session is, and either one naming a ticket is enough.
    The host runs this file from the session's directory, so `getcwd` is the answer.
    `PASEO_AGENT_CWD`, the directory Paseo opened the session in, is the second: it
    still names the ticket when a hook runs from somewhere else.
    """
    for root in (os.getcwd(), os.environ.get("PASEO_AGENT_CWD", "").strip()):
        if not root:
            continue
        match = TICKET_DIR.fullmatch(os.path.basename(os.path.normpath(root)))
        if match:
            return int(match.group(1))
    return None


SHELL_OPERATORS = re.compile(r"\\[\\<>]|[<>]&|&>>?|(?P<boundary>[;\n]|&&|\|\||\||&)")
LEADING_ASSIGNMENTS = re.compile(r"^(?:\w+=\S*\s+)*")


def pieces(command: str) -> list[str]:
    """Every piece of `command` a shell would run as a command of its own, leading
    variable assignments stripped."""
    parts = []
    quote = None
    start = offset = 0
    while offset < len(command):
        char = command[offset]
        if char == "\\" and quote != "'":
            offset += 2
            continue
        if quote != "'" and (char == "`" or command.startswith("$(", offset)):
            break
        if quote is not None:
            if char == quote:
                quote = None
        elif char in "\"'":
            prefix = LEADING_ASSIGNMENTS.sub("", command[start:offset].strip())
            try:
                words = shlex.split(prefix)
            except ValueError:
                break
            if words and os.path.basename(words[0]) in ("sh", "bash", "dash", "ksh", "zsh"):
                break
            quote = char
        else:
            if command.startswith("<<", offset) or (
                char == "#" and (offset == start or command[offset - 1].isspace()
                                or command[offset - 1] in "&()")
            ):
                break
            operator = SHELL_OPERATORS.match(command, offset)
            if operator:
                if operator.group("boundary") is not None:
                    parts.append(command[start:offset])
                    start = operator.end()
                offset = operator.end()
                continue
        offset += 1
    if quote is not None or offset != len(command):
        parts = []
        start = 0
        for operator in SHELL_OPERATORS.finditer(command):
            if operator.group("boundary") is not None:
                parts.append(command[start:operator.start()])
                start = operator.end()
    parts.append(command[start:])
    return [LEADING_ASSIGNMENTS.sub("", piece.strip())
            for piece in parts if piece.strip()]


# `kill`, its two relatives, and the shape that reaches them through a pipe
# (`lsof -ti:5173 | xargs kill -9`). First word only: prose that mentions killing lands
# mid-line, a command starts one — the same test the `gh` gate below relies on.
ENDS_A_PROCESS = re.compile(r"^(kill|pkill|killall|killall5)\b")
XARGS_KILL = re.compile(r"^xargs\b.*\bkill\b")


def ends_a_process(command: str) -> str | None:
    """The piece of `command` that would end a process, or `None`."""
    for piece in pieces(command):
        if ENDS_A_PROCESS.match(piece) or XARGS_KILL.match(piece):
            return piece
    return None


def runs(command: str) -> list[str]:
    """The pieces of `command` that a shell would run as commands of their own.

    Where the ticket number and the words `gh issue close` appear is not the same
    question as whether this command closes anything. A worker writing its closing
    comment says in it that it did not close the ticket by hand — and that sentence,
    inside the `cat` that writes the draft, is not a `gh` call. Splitting on the shell's
    own separators and keeping only the pieces that start with `gh` tells the two apart:
    prose lands mid-line, a command starts one. (2026-08-30: a worker hit exactly this
    on the first unconstrained run of this hook.)
    """
    return [piece for piece in pieces(command) if re.match(r"gh\b", piece)]


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


def refuse(reason: str) -> None:
    """Say no the way Claude Code and Codex both read it, on stdout, exiting 0 either way."""
    answer = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "permissionDecision": "deny",
                                     "permissionDecisionReason": reason}}
    print(json.dumps(answer, ensure_ascii=False))


def no_kill(piece: str) -> str:
    """Why this command is refused and what the session does instead.

    The way out comes last: a refusal that only diagnoses invites an autonomous agent to
    improvise, and on 2026-09-05 three of them improvised three different wrong answers
    to one correct error message.
    """
    return (f"Refused `{piece}`. A run never ends a process it did not start. Stop your "
            "own product as its verify-<product> skill says; if it is unreachable, report "
            "the ticket blocked and stop.")


def run_pretool(event: dict) -> int:
    number = governed_ticket()
    if number is None:
        return 0
    command = command_of(event)
    if command is None:
        return 0
    piece = ends_a_process(command)
    if piece is not None:
        refuse(no_kill(piece))
        return 0
    if not leaves_the_agent_lane(command, number):
        return 0
    refuse(REFUSAL.format(n=number))
    return 0


def run_question(host: str, event: dict) -> int:
    if governed_ticket() is None:
        return 0
    if tool_of(event) not in QUESTION_TOOLS.get(host, ()):
        return 0
    refuse(NO_QUESTION)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in GATES or argv[1] not in HOSTS:
        sys.stderr.write(f"usage: tool-guard.py <{'|'.join(GATES)}> <{'|'.join(HOSTS)}>\n")
        return 0
    event = read_event()
    if argv[0] == "question":
        return run_question(argv[1], event)
    return run_pretool(event)


if __name__ == "__main__":
    sys.exit(main())
