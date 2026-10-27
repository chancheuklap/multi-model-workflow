#!/usr/bin/env python3
"""Guard ticket closeout, unattended questions, process termination, brief git writes
and deletion of worktrees in use.

A ticket closes through `verify-ticket.py <n> --closeout <draft>`, which checks the
closing comment, posts it, and only then closes the ticket. `gh issue close` skips all
of that and leaves a closed ticket nobody can read in the morning. So every host asks
this file before running a shell command, and this file refuses that one command.

A question on the screen has nobody to answer it: nothing in this pipeline reads a
form. So every host asks this file before calling its question tool, and this file
refuses the call and says where the question goes instead — the default taken and
recorded, or `ABANDON: AC<n> decision` with a sub-issue.

Several runs share one machine. A session may end processes in its own host's process
tree with `kill [-<signal>] <pid>...`, but never a neighbour's or an unreadable tree.
The host is this hook's nearest ancestor whose executable basename equals <host>.
Host process names: claude and codex, checked with live ps comm on 2026-10-27.

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
ticket worktree and is not refused by those gates. They ask no runner.

Brief git writes and worktree deletions are guarded in every directory. Commands without
a git write ask no runner. File writes remain allowed so candidates can write into
the sender's checkout. Batch records keep the sender's worktree protected until
`dispatch.sh brief close <batch>` removes them, even after the children report.
Deletion also protects this process's working directory and its ancestors.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from pathlib import Path

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
SHELL_WORD = r'''(?:\\[^\n]|'[^']*'|"(?:\\[\s\S]|[^"\\])*"|[^\s\\'"<>&;|()])+'''
LEADING_SYNTAX = re.compile(
    rf"^(?:\s+|\\\n|\(|[{{!](?=\s|\\\n|$)|"
    rf"[A-Za-z_]\w*=(?:{SHELL_WORD}|[()])*|"
    rf"(?:\d+)?(?:&>>?|>>?|[<>]&|<)\s*{SHELL_WORD})+"
)
PREFIX_COMMANDS = {
    "command": ("", ()),
    "builtin": ("", ()),
    "exec": ("a", ()),
    "env": ("uCPS", ("--unset", "--chdir", "--split-string")),
    "sudo": ("uUgChpDrtRT", ("--user", "--group", "--host", "--prompt", "--close-from",
                              "--chdir", "--chroot", "--role", "--type", "--command-timeout")),
    "nohup": ("", ()),
    "time": ("fo", ("--format", "--output")),
    "nice": ("n", ("--adjustment",)),
}
WORD = re.compile(SHELL_WORD)


def strip_heredocs(command: str) -> str:
    result = []
    pending: list[tuple[str, bool]] = []
    quote = None
    offset = 0
    while offset < len(command):
        char = command[offset]
        if char == "\\" and quote != "'":
            result.append(command[offset:offset + 2])
            offset += 2
            continue
        if char == quote:
            quote = None
        elif quote is None and char in "\"'":
            quote = char
        elif quote is None and char == "#" and (
            offset == 0 or command[offset - 1].isspace() or command[offset - 1] in ";&|()"
        ):
            end = command.find("\n", offset)
            if end == -1:
                result.append(command[offset:])
                break
            result.append(command[offset:end])
            offset = end
            continue
        elif quote is None and command.startswith("<<<", offset):
            result.append("<<<")
            offset += 3
            continue
        elif quote is None and command.startswith("<<", offset):
            marker = re.match(r"<<(-?)[ \t]*(" + SHELL_WORD + ")", command[offset:])
            if marker:
                pending.append((shlex.split(marker[2])[0], bool(marker[1])))
                result.append(" ")
                offset += marker.end()
                continue
        result.append(char)
        offset += 1
        if char == "\n" and quote is None:
            for delimiter, tabs in pending:
                while offset < len(command):
                    end = command.find("\n", offset)
                    end = len(command) if end == -1 else end
                    line = command[offset:end]
                    offset = min(end + 1, len(command))
                    if (line.lstrip("\t") if tabs else line) == delimiter:
                        break
            pending.clear()
    return "".join(result)


def strip_command_prefixes(piece: str) -> str:
    while True:
        piece = LEADING_SYNTAX.sub("", piece).strip()
        program = WORD.match(piece)
        if program is None or program[0] not in PREFIX_COMMANDS:
            return piece
        short_values, long_values = PREFIX_COMMANDS[program[0]]
        rest = piece[program.end():].lstrip()
        options_ended = False
        while True:
            rest = LEADING_SYNTAX.sub("", rest).strip()
            option = WORD.match(rest)
            if option is None:
                break
            value = shlex.split(option[0])[0]
            if program[0] == "env" and (options_ended or not value.startswith("-")) \
                    and re.match(r"[^=]+=", value):
                rest = rest[option.end():].lstrip()
                continue
            if options_ended:
                break
            if value == "--":
                rest = rest[option.end():].lstrip()
                options_ended = True
                continue
            if value == "-" and program[0] == "env":
                rest = rest[option.end():].lstrip()
                continue
            if not value.startswith("-") or value == "-":
                break
            if value in ("--help", "--version") \
                    or (program[0] == "sudo" and value == "--list") or (
                program[0] == "command" and any(flag in value for flag in "vV")
            ):
                return piece
            option_name, separator, argument_value = value.partition("=")
            needs_value = option_name in long_values and not separator
            if not value.startswith("--"):
                for index, flag in enumerate(value[1:], 1):
                    if program[0] == "sudo" and flag == "l":
                        return piece
                    if flag in short_values:
                        option_name = flag
                        argument_value = value[index + 1:]
                        needs_value = index == len(value) - 1
                        break
            rest = rest[option.end():].lstrip()
            if needs_value:
                argument = WORD.match(rest)
                if argument is None:
                    return piece
                argument_value = shlex.split(argument[0])[0]
                rest = rest[argument.end():].lstrip()
            if program[0] == "env" and option_name in ("S", "--split-string"):
                try:
                    arguments = shlex.join(shlex.split(argument_value))
                except ValueError:
                    return piece
                rest = f"{arguments} {rest}".strip()
        piece = rest


def pieces(command: str, strip_prefixes: bool = True) -> list[str]:
    command = strip_heredocs(command)
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
            prefix = strip_command_prefixes(command[start:offset])
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
    return [strip_command_prefixes(piece) if strip_prefixes else piece
            for piece in parts if piece.strip()]


# This guards against accidental process termination behind assignments, groups,
# negation, redirections, continuations and PREFIX_COMMANDS. It is not a sandbox
# against deliberate evasion through eval, functions, aliases or python3 -c.
ENDS_A_PROCESS = re.compile(r"^(kill|pkill|killall|killall5)\b")
XARGS_KILL = re.compile(r"^xargs\b.*\bkill\b")


def ends_a_process(command: str, host: str) -> str | None:
    for piece in pieces(command):
        if (ENDS_A_PROCESS.match(piece) or XARGS_KILL.match(piece)) \
                and not kills_own_processes(piece, host):
            return piece
    return None


def kills_own_processes(piece: str, host: str) -> bool:
    words = shell_words(piece)
    if not words or words[0] != "kill":
        return False
    targets = words[1:]
    if targets and targets[0].startswith("-"):
        value = targets.pop(0)[1:]
        try:
            if value != "0":
                signal.Signals(int(value)) if value.isascii() and value.isdecimal() else signal.Signals[
                    value if value.startswith("SIG") else "SIG" + value]
        except (ValueError, KeyError):
            return False
    if not targets or any(re.fullmatch(r"[0-9]+", pid) is None for pid in targets):
        return False
    try:
        targets = [int(pid) for pid in targets]
        rows = subprocess.run(["ps", "-axo", "pid=,ppid=,comm="], capture_output=True,
                              text=True, check=True).stdout.splitlines()
        processes = {}
        for row in rows:
            pid, parent, executable = row.split(None, 2)
            processes[int(pid)] = (int(parent), os.path.basename(executable))
    except (OSError, ValueError, subprocess.SubprocessError):
        return False

    def ancestors(pid):
        seen = set()
        while pid in processes and pid not in seen:
            seen.add(pid)
            yield pid
            pid = processes[pid][0]

    owner = next((pid for pid in ancestors(os.getppid()) if processes[pid][1] == host), None)
    return owner is not None and all(
        pid in processes and owner in ancestors(processes[pid][0]) for pid in targets
    )


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


def edits_last_comment(command: str) -> str | None:
    for run in runs(command):
        words = shell_words(run)
        arguments = []
        edit_last = False
        options = iter(words[1:])
        for option in options:
            if option == "--":
                arguments.extend(options)
                break
            if option in ("--body", "-b", "--body-file", "-F", "--repo", "-R"):
                next(options, None)
            elif option.split("=", 1)[0] == "--edit-last":
                edit_last = True
            elif not option.startswith("-"):
                arguments.append(option)
        if arguments[:2] in (["issue", "comment"], ["pr", "comment"]) and edit_last:
            return run
    return None


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
    return (f"Refused `{piece}`. Only processes started by this session may be ended. "
            "Use kill [-<signal>] <numeric pid>... with a readable ancestry to this host. Stop your "
            "own product as its verify-<product> skill says; if it is unreachable, report "
            "the ticket blocked and stop.")


GIT_WRITES = {"commit", "checkout", "switch", "merge", "rebase", "reset", "push",
              "pull", "stash", "cherry-pick", "revert", "am", "tag"}
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
BRANCH_WRITES = {"--delete", "--move", "--copy", "--create-reflog", "--track", "--force",
                 "--set-upstream-to", "--unset-upstream", "--edit-description"}
BRANCH_QUERIES = {"--list", "--show-current", "--contains", "--no-contains", "--merged",
                  "--no-merged", "--points-at"}


def shell_words(piece: str) -> list[str]:
    lexer = shlex.shlex(piece, posix=True, punctuation_chars="()")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return [word for word in lexer if word not in ("(", ")")]
    except ValueError:
        return []


def expand_shell_variables(piece: str, values: dict[str, str]) -> str:
    result = []
    quote = None
    offset = 0
    while offset < len(piece):
        char = piece[offset]
        if char == "\\" and quote != "'":
            result.append(piece[offset:offset + 2])
            offset += 2
            continue
        if char == quote:
            quote = None
        elif quote is None and char in "\"'":
            quote = char
        if char == "$" and quote != "'":
            match = re.match(r"\$(?:([A-Za-z_]\w*)|\{([A-Za-z_]\w*)\})", piece[offset:])
            if match:
                name = match[1] or match[2]
                value = values.get(name, match[0])
                result.append(value.replace("\\", "\\\\").replace('"', '\\"')
                              if quote == '"' else shlex.quote(value))
                offset += len(match[0])
                continue
        result.append(char)
        offset += 1
    return "".join(result)


def command_contexts(command: str) -> list[tuple[str, str, Path]]:
    cwd = Path.cwd()
    values = {**os.environ, "PWD": str(cwd)}
    commands = []
    scopes = []
    for raw in pieces(command, strip_prefixes=False):
        expanded = expand_shell_variables(raw, values)
        groups = [match[0] for match in re.finditer(rf"{SHELL_WORD}|[()]", expanded)
                  if match[0] in ("(", ")")] if "$(" not in raw else []
        for group in groups:
            if group == "(":
                scopes.append((cwd, values.copy()))
        words = shell_words(expanded)
        while words and words[0] in ("{", "!"):
            words = words[1:]
        assignments = words[1:] if words[:1] == ["export"] else words
        if assignments and all(re.match(r"^[A-Za-z_]\w*=", word) for word in assignments):
            values.update(word.split("=", 1) for word in assignments)
        else:
            piece = strip_command_prefixes(expanded)
            words = shell_words(piece)
            if words[:1] == ["cd"]:
                args = [word for word in words[1:] if word not in ("-L", "-P", "--")]
                target = args[0] if args else values.get("HOME", str(cwd))
                if target == "-":
                    target = values.get("OLDPWD", str(cwd))
                previous = cwd
                cwd = (cwd / os.path.expanduser(target)).resolve()
                values.update(OLDPWD=str(previous), PWD=str(cwd))
            else:
                commands.append((strip_command_prefixes(raw), piece, cwd))
        for group in groups:
            if group == ")" and scopes:
                cwd, values = scopes.pop()
    return commands


def git_command(piece: str, cwd: Path | None = None) -> tuple[list[str], Path] | None:
    words = shell_words(piece)
    if not words or os.path.basename(words[0]) != "git":
        return None
    cwd = cwd or Path.cwd()
    index = 1
    while index < len(words) and words[index].startswith("-"):
        option = words[index]
        if option in ("--help", "--version"):
            return None
        if option == "--":
            index += 1
            break
        if option in GIT_VALUE_OPTIONS:
            index += 1
            if index == len(words):
                return None
            if option == "-C":
                cwd = (cwd / words[index]).resolve()
        elif option.startswith("-C"):
            cwd = (cwd / option[2:]).resolve()
        index += 1
    return words[index:], cwd


def git_write(args: list[str]) -> bool:
    if not args:
        return False
    verb, *flags = args
    if verb in GIT_WRITES:
        return True
    if verb == "worktree":
        return bool(flags) and flags[0] in ("add", "remove")
    if verb != "branch":
        return False
    options = iter(flags)
    flags = []
    for flag in options:
        if flag in ("--format", "--sort"):
            next(options, None)
        else:
            flags.append(flag)
    if any(flag.split("=", 1)[0] in BRANCH_WRITES or
           (flag.startswith("-") and not flag.startswith("--") and
            any(letter in flag[1:] for letter in "dDmMcCftu")) for flag in flags):
        return True
    if any(flag.split("=", 1)[0] in BRANCH_QUERIES or
           (flag.startswith("-") and not flag.startswith("--") and "l" in flag[1:])
           for flag in flags):
        return False
    return any(not flag.startswith("-") for flag in flags)


def session_guard():
    path = Path(__file__).resolve().with_name("turn-guard.py")
    spec = importlib.util.spec_from_file_location("mmw_tool_session_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def brief_git_refusal(piece: str) -> str | None:
    guard = session_guard()
    asked: dict = {}
    root = guard.statedir.home() / "state"
    for state in sorted(root.iterdir()) if root.is_dir() else []:
        child = guard.own_brief(state, asked)
        if child is not None:
            name = f"{child['batch']}/{child['n']}"
            return (f"Refused `{piece}` for open brief {name}. Brief sessions share the "
                    "sender's worktree and make no git write. Hand back your files with "
                    f"`dispatch.sh report {name} <file>`; the session that sent the brief "
                    "commits what you hand back.")
    return None


def removal_paths(piece: str, git: tuple[list[str], Path] | None,
                  cwd: Path | None = None) -> list[Path]:
    if git is not None:
        args, cwd = git
        if args[:2] != ["worktree", "remove"]:
            return []
        args = args[2:]
    else:
        words = shell_words(piece)
        if not words or os.path.basename(words[0]) != "rm":
            return []
        args, cwd = words[1:], cwd or Path.cwd()
    paths = []
    options = True
    for arg in args:
        if options and arg == "--":
            options = False
        elif arg and (not options or not arg.startswith("-")):
            paths.append((cwd / os.path.expanduser(arg)).resolve())
    return paths


def removal_refusal(piece: str, paths: list[Path]) -> str | None:
    guard = session_guard()
    root = guard.statedir.home() / "state"
    batches = [batch for state in sorted(root.iterdir()) if state.is_dir()
               for batch in guard.briefs.open_batches(state)] if root.is_dir() else []
    cwd = Path.cwd().resolve()
    for path in paths:
        held = [b for b in batches if b.get("worktree") and
                Path(b["worktree"]).resolve().is_relative_to(path)]
        current = cwd.is_relative_to(path)
        if not held and not current:
            continue
        why = f"It contains this process's working directory {cwd}. " if current else ""
        if held:
            names = ", ".join(b["batch"] for b in held)
            close = ", then ".join(f"`dispatch.sh brief close {b['batch']}`" for b in held)
            why += f"Open batches {names} use their recorded worktrees here. "
            way = f"Close the batches with {close} before removing their worktrees."
            if current:
                way += " Run cleanup from a session whose working directory is outside this path."
        else:
            way = "Run cleanup from a session whose working directory is outside this path."
        return f"Refused `{piece}` removing {path}. {why}{way}"
    return None


def run_pretool(event: dict, host: str) -> int:
    command = command_of(event)
    if command is None:
        return 0
    comment = edits_last_comment(command)
    if comment is not None:
        refuse(f"Refused `{comment}`. All agents share one GitHub account, so the last "
               "comment may be another agent's event. Use gh api to edit by comment id.")
        return 0
    number = governed_ticket()
    if number is not None:
        piece = ends_a_process(command, host)
        if piece is not None:
            refuse(no_kill(piece))
            return 0
        if leaves_the_agent_lane(command, number):
            refuse(REFUSAL.format(n=number))
            return 0
    for source, piece, cwd in command_contexts(command):
        git = git_command(piece, cwd)
        paths = removal_paths(piece, git, cwd)
        if paths:
            reason = removal_refusal(source, paths)
            if reason is not None:
                refuse(reason)
                return 0
        if git is not None and git_write(git[0]):
            reason = brief_git_refusal(source)
            if reason is not None:
                refuse(reason)
                return 0
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
    return run_pretool(event, argv[1])


if __name__ == "__main__":
    sys.exit(main())
