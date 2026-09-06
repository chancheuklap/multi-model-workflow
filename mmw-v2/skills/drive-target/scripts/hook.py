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
finished. A run stops its own product through the `stop` command its repository
declares; everything else is somebody else's, and a run that cannot reach its product
reports the ticket blocked rather than clearing the way to it.

    hook.py pretool <host>    the host is about to run a shell command
    hook.py question <host>   the host is about to ask the user a question

`<host>` is one of claude, codex, grok, cursor, pi. It decides only the shape of the
answer; the decision and the sentence are the same for all five.

It refuses rather than checks. A worker typing `gh issue close` has by definition not
been through `--closeout`, so there is no draft of its to check; a hook that guessed
one and let the command through when the guess passed would produce exactly the
outcome it exists to prevent — the ticket closed with no closing comment on it.

Whether this session is governed is read off the process:

- pretool: the working directory's basename. `issue-<n>` (digits only) is ticket
  `<n>`; any other basename is not a ticket worktree and is not refused. No
  `paseo` call.
- question: `PASEO_AGENT_ID`. The gate asks
  `paseo ls -g --json --label mmw.autonomous=1` and refuses only when that id is
  in the returned list. No id, no `paseo` on PATH, a failed call, or an id that
  is not in the list: no refusal.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from refusal import refusal  # noqa: E402

HOSTS = ("claude", "codex", "grok", "cursor", "pi")
GATES = ("pretool", "question")
TICKET_DIR = re.compile(r"^issue-(\d+)$")

REFUSAL = (
    "Close #{n} with `verify-ticket.py {n} --closeout <draft>`, not by hand: it checks the "
    "closing comment, posts it, then closes the ticket. Write it to a file and run that. "
    "Unfinished work leaves the same way, first line `HANDOFF REQUIRED`."
)

# The same length rule. Nobody is at the screen; the two ways out are the ones the
# `implement` skill already gives.
NO_QUESTION = (
    "Nobody is at the screen. Take the likeliest option and note it under `Decisions I "
    "made on my own`; if the answer changes what the ticket delivers, write `ABANDON: "
    "AC<n> decision <question, options, default>` and open a needs-triage sub-issue."
)

# The tool each host calls to put a question on the screen.
QUESTION_TOOLS = {
    "claude": ("AskUserQuestion",),
    "codex": ("request_user_input",),
    "grok": ("ask_user_question",),
    "cursor": ("AskQuestion",),
    "pi": ("ask_user_question",),
}


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


def autonomous() -> bool:
    """Whether this process is a Paseo agent labelled `mmw.autonomous=1`."""
    agent_id = os.environ.get("PASEO_AGENT_ID", "").strip()
    if not agent_id:
        return False
    return agent_id in autonomous_agent_ids()


def autonomous_agent_ids() -> set[str]:
    """Ids from `paseo ls -g --json --label mmw.autonomous=1`.

    An unanswered or unreadable call is an empty set: the question gate then
    does not refuse, the same as a session with no `PASEO_AGENT_ID`.
    """
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    try:
        run = subprocess.run(
            ["paseo", "ls", "-g", "--json", "--label", "mmw.autonomous=1"],
            capture_output=True, text=True, env=env, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return set()
    if run.returncode != 0:
        return set()
    try:
        rows = json.loads(run.stdout)
    except Exception:
        return set()
    if not isinstance(rows, list):
        return set()
    ids: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            value = row.get("id")
            if isinstance(value, str) and value:
                ids.add(value)
    return ids


def tool_of(event: dict) -> str:
    """The tool this event is about, in whichever way its host spelled it."""
    for name in ("tool_name", "toolName"):
        value = event.get(name)
        if isinstance(value, str) and value:
            return value
    return ""


def governed_ticket() -> int | None:
    """The ticket this session belongs to, if it is a ticket worktree.

    The slug is `issue-<n>`. Reviewer, verifier and worker share that directory
    and are all governed. A session in no such directory is not.

    Two places say where the session is, and either one naming a ticket is enough.
    Most hosts run this file from the directory the command runs in, so `getcwd` is
    the answer. Cursor does not: it runs hooks from `~/.cursor` and sends an empty
    `cwd` in the event, so on that host `getcwd` names no ticket however deep in the
    worktree the command is, and the gate stayed open on every command it was
    installed to refuse (measured 2026-09-06, cursor-agent 2026.08.25). `PASEO_AGENT_CWD`
    is the directory Paseo opened the session in, and every host inherits it.
    """
    for root in (os.getcwd(), os.environ.get("PASEO_AGENT_CWD", "").strip()):
        if not root:
            continue
        match = TICKET_DIR.fullmatch(os.path.basename(os.path.normpath(root)))
        if match:
            return int(match.group(1))
    return None


SEPARATORS = re.compile(r"[;\n]|&&|\|\||\|")
LEADING_ASSIGNMENTS = re.compile(r"^(?:\w+=\S*\s+)*")


def pieces(command: str) -> list[str]:
    """Every piece of `command` a shell would run as a command of its own, leading
    variable assignments stripped."""
    return [LEADING_ASSIGNMENTS.sub("", piece.strip())
            for piece in SEPARATORS.split(command) if piece.strip()]


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


def no_kill(piece: str) -> str:
    """Why this command is refused and what the session does instead.

    The way out comes last and is never trimmed: a refusal that only diagnoses invites an
    autonomous agent to improvise, and on 2026-09-05 three of them improvised three
    different wrong answers to one correct error message.
    """
    return refusal(
        f"Refused `{piece}`.",
        "A run never ends a process it did not start.",
        "Stop your own product with the `stop` command in .mmw/target.json; if it is "
        "unreachable, report the ticket blocked and stop.",
    )


def run_pretool(host: str, event: dict) -> int:
    number = governed_ticket()
    if number is None:
        return 0
    command = command_of(event)
    if command is None:
        return 0
    piece = ends_a_process(command)
    if piece is not None:
        refuse(host, no_kill(piece))
        return 0
    if not leaves_the_agent_lane(command, number):
        return 0
    refuse(host, REFUSAL.format(n=number))
    return 0


def run_question(host: str, event: dict) -> int:
    if not autonomous():
        return 0
    if tool_of(event) not in QUESTION_TOOLS.get(host, ()):
        return 0
    refuse(host, NO_QUESTION)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] not in GATES or argv[1] not in HOSTS:
        sys.stderr.write(f"usage: hook.py <{'|'.join(GATES)}> <{'|'.join(HOSTS)}>\n")
        return 0
    if argv[0] == "question":
        return run_question(argv[1], read_event())
    return run_pretool(argv[1], read_event())


if __name__ == "__main__":
    sys.exit(main())
