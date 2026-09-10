#!/usr/bin/env python3
"""Run a ticket's acceptance criteria and post the result back to the ticket.

The ticket is the only state. Every run reads the `## Acceptance criteria` and
`## Owns` sections fresh from the issue, writes them to a ledger, hands
that ledger to unlazy's `gate-check`, and posts the updated ledger back as one
comment. Nothing is cached and no file is left behind.
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_events():
    """`events.py` beside this file: the event vocabulary and the fold."""
    spec = importlib.util.spec_from_file_location("mmw_events", HERE / "events.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load_events()
GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"
GATE_LINT = HERE / "gate-check" / "gate-lint.mjs"
LEDGER_NAME = "AC.md"
SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")
GATE_LINE_RE = re.compile(r"^- \[( |x|X)\] ([A-Za-z0-9][A-Za-z0-9._-]*):")
SUB_ISSUE_KINDS = events.CHILD_KINDS
FILL = "<fill>"

# A criterion is abandoned for one of three reasons. `failed` ran and did not pass;
# `stuck` never ran or cannot be done; the two are told apart for whoever reads the
# ticket in the morning, and both hand the ticket back. `decision` needs a person to
# choose, and is the only one that still closes. How many rounds a criterion gets is
# the worker's own judgement, said on the `ABANDON:` line.
ABANDON_KINDS = events.ABANDON_KINDS
HANDOFF_KINDS = ("failed", "stuck")
# Seconds one `CHECK:` may run. A ticket raises it per criterion with `TIMEOUT:`; the
# worker's own run and the verifier's `--reverify` read the same lines, so the two
# never disagree about it.
DEFAULT_TIMEOUT = 600
ABANDON_RE = re.compile(r"^ABANDON:\s+(\S+)\s+(\S+)\s*(.*)$")
COUNTS_RE = re.compile(
    r"^Counts:\s*(\d+)\s+met,\s*(\d+)\s+unmet,\s*(\d+)\s+abandoned of\s*(\d+)\s*$")
HANDOFF_RE = re.compile(
    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(([^)]*)\),\s*(\d+)\s+unmet,\s*(\d+)\s+met of\s*(\d+)\s*$")
# `owner/repo#n` and `repo#n` are another repository's issue, not this batch's spec.
ISSUE_REF_RE = re.compile(r"(?<![A-Za-z0-9_/])#(\d+)")
WORKER_LABEL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-worker$")
ATTR_LINE_RE = re.compile(r"^\s+(CHECK|EXPECT|EVIDENCE|CWD|TIMEOUT):")
# The one attribute gate-check does not know: it is read here and kept out of the ledger.
TIMEOUT_LINE_RE = re.compile(r"^\s+TIMEOUT:")
FENCE_OPEN_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`+|~+)[ \t]*$")
REGEX_EXPECT_RE = re.compile(r"^/([\s\S]*)/([a-z]*)$")
# A pattern author escapes a literal dollar or has none, so an unescaped one is
# the anchor. Same reading gate-lint gives an unescaped slash.
UNESCAPED_DOLLAR_RE = re.compile(r"(^|[^\\])\$")
STATEFUL_COMMAND_RE = re.compile(
    r"\bgit (checkout|switch|branch\s+-[Dd]|reset|stash|merge|rebase)\b"
    r"|\bgh issue (close|reopen|edit|create|delete)\b"
    r"|\bgh pr (create|close|merge)\b")


# ----------------------------------------------------------------- ticket text

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into --json
# output under it, which json.loads cannot read. Every gh call here runs without it.
GH_ENV = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}


def fetch_body(number: int) -> str:
    """The issue body, straight from the tracker. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "body", "-q", ".body"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    return out.stdout


def fetch_comments(number: int) -> list[str]:
    """Every comment body on the ticket, oldest first. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "comments"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    return [c.get("body", "") for c in json.loads(out.stdout).get("comments", [])]


def post_comment(number: int, body: str) -> None:
    """One comment per run. Patched out in tests."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        path = fh.name
    try:
        subprocess.run(["gh", "issue", "comment", str(number), "--body-file", path], check=True, env=GH_ENV)
    finally:
        os.unlink(path)


def post_prose(number: int, text: str) -> None:
    """Post a comment that is not an event: a run's ledger, `CHECKS FAILED`, `TOUCHED BY`.

    What it quotes — a command's output, a file path — may hold an `<!-- mmw` opener, and
    that would read on the ticket as an event nobody wrote. `events.neutralise` makes any
    such opener visible text.
    """
    post_comment(number, events.neutralise(text))


def post_event(number: int, event: str, line: str, text: str = "",
               spec: int | None = None, **fields) -> str:
    """Post one event on ticket `number`: `line` for a person, the block for the fold."""
    body = events.build(event, ticket=number, spec=spec, line=line, text=text, **fields)
    post_comment(number, body)
    return body


def spec_field(ticket: dict) -> int | None:
    """The spec a fetched ticket sits under, when the tracker answered with its parent."""
    parent = ticket.get("parent") if isinstance(ticket, dict) else None
    number = parent.get("number") if isinstance(parent, dict) else None
    return number if isinstance(number, int) else None


def fetch_ticket(number: int) -> dict:
    """State, labels, assignees, blockers and parent of the ticket. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json",
         "state,stateReason,labels,assignees,blockedBy,parent"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    return json.loads(out.stdout)


def gh_login() -> str:
    """The account `gh` is signed in as. Patched out in tests."""
    out = subprocess.run(["gh", "api", "user", "-q", ".login"], env=GH_ENV,
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def own_session() -> tuple[str, str] | None:
    """(runner, session) of the session this run is part of, as `dispatch.sh self` of the
    dispatch skill beside this one reads it, or None when it cannot say: outside any
    runner, or with that skill not there. Patched out in tests."""
    script = HERE.parents[1] / "dispatch" / "scripts" / "dispatch.sh"
    if not script.is_file():
        return None
    try:
        out = subprocess.run(["bash", str(script), "self"], capture_output=True, text=True,
                             timeout=60, env=GH_ENV)
    except (OSError, subprocess.SubprocessError):
        return None
    runner, _, session = out.stdout.strip().partition("\t")
    return (runner, session) if out.returncode == 0 and runner and session else None


def assign_self(number: int) -> None:
    """Claim the ticket. Patched out in tests."""
    subprocess.run(["gh", "issue", "edit", str(number), "--add-assignee", "@me"], check=True, env=GH_ENV)


def close_ticket(number: int) -> None:
    """Close the ticket, then take it out of the agent queue and take its claim off.

    The close comes first because it is the change `ticket.passed` announces: when it
    fails nothing has changed, and the closeout can simply be run again. The assignee
    comes off in the same edit as the label, for the same reason it does on the hand back
    to triage: a claim outlives the session that made it, and only that session knows it
    is done. `advance`'s give-a-claim-back reads open tickets alone, so a claim left on a
    closed one is one nothing else ever takes off — an edit that fails after the close is
    said on stderr, and the close stands. Patched out in tests.
    """
    subprocess.run(["gh", "issue", "close", str(number), "--reason", "completed"], check=True, env=GH_ENV)
    edit = subprocess.run(
        ["gh", "issue", "edit", str(number),
         "--remove-label", "ready-for-agent", "--remove-assignee", "@me"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if edit.returncode != 0:
        sys.stderr.write(f"#{number} is closed, and its ready-for-agent label or your claim could "
                         f"not be taken off: {' '.join((edit.stderr or edit.stdout).split())[:200]}\n")


def unannounced_change(ticket: dict, comments: list[str], me: str, first: str) -> str | None:
    """The state change a closeout of this worker's round made without posting its event:
    "closed" or "handed", or None.

    A closeout makes the change first and posts the event after it, so a post that fails
    leaves a ticket closed (or handed back) with no `ticket.passed` (or `ticket.returned`)
    — which the ordinary checks then refuse, since the ticket is no longer open and yours.
    It is this round's when the newest `ticket.claimed` is yours and no closing event
    follows it; a ticket closed as anything but completed is somebody else's decision.
    """
    state = events.fold(comments)
    names = [e["event"] for e in state["events"]]
    if "ticket.claimed" not in names or state.get("claimant") != me:
        return None
    last = len(names) - 1 - names[::-1].index("ticket.claimed")
    if any(name in ("ticket.passed", "ticket.returned") for name in names[last + 1:]):
        return None
    labels = {label.get("name") for label in ticket.get("labels") or []}
    assigned = any(a.get("login") == me for a in ticket.get("assignees") or [])
    if first == "ALL MET" and ticket.get("state") == "CLOSED" \
            and str(ticket.get("stateReason") or "").upper() == "COMPLETED":
        return "closed"
    if first.startswith("HANDOFF REQUIRED") and ticket.get("state") == "OPEN" and not assigned \
            and "needs-triage" in labels and "ready-for-agent" not in labels:
        return "handed"
    return None


def hand_back_for_triage(number: int) -> None:
    """Put the ticket back in the queue nobody has judged yet. Patched out in tests.

    A worker that could not finish has not established what the ticket needs next — a
    person, more information, another agent, or nothing at all. `needs-triage` is that
    state, and it is the one queue a skill picks up on its own.

    A ticket still assigned to the worker that gave up is a ticket `status.py`'s
    frontier will not dispatch again — it takes only unassigned tickets — so the
    assignee comes off in the same edit as the label.
    """
    subprocess.run(
        ["gh", "issue", "edit", str(number),
         "--remove-label", "ready-for-agent", "--add-label", "needs-triage",
         "--remove-assignee", "@me"],
        check=True, env=GH_ENV,
    )


def fetch_blocked_by(number: int) -> list[int]:
    """The tickets the tracker records as blocking `number`. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "blockedBy"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    data = json.loads(out.stdout) if out.stdout.strip() else {}
    return [b["number"] for b in (data.get("blockedBy") or {}).get("nodes", [])]


def gh_detail(out: subprocess.CompletedProcess) -> str:
    """The last line a failed `gh` call said, for the exception that carries it up.

    `gh` writes its reason on stderr and falls back to stdout; the last line is the
    one that names the failure, the rest being the request it was making.
    """
    detail = (out.stderr or out.stdout).strip().splitlines()
    return detail[-1] if detail else f"gh exited {out.returncode}"


class SubIssuesUnreadable(RuntimeError):
    """The tracker could not list the children of an issue.

    Distinct from an issue that has no children: that one is an empty list, this one
    means the question went unanswered.
    """


def fetch_sub_issues(number: int) -> list[int]:
    """The tickets GitHub records as children of any issue, in its own order, every
    page of them (GitHub pages the list at 30, and an issue past its thirtieth child
    would otherwise lose its newest children to every batch check). Called with a
    spec, that is the batch; called with a ticket, that is what the ticket opened.
    Raises `SubIssuesUnreadable` when the tracker could not be asked. Patched out in
    tests."""
    out = subprocess.run(
        ["gh", "api", "--paginate",
         f"repos/{{owner}}/{{repo}}/issues/{number}/sub_issues?per_page=100",
         "-q", ".[] | .number"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if out.returncode != 0:
        raise SubIssuesUnreadable(gh_detail(out))
    return [int(line) for line in out.stdout.split() if line.strip()]


class ParentUnreadable(RuntimeError):
    """The tracker could not say which spec a ticket sits under.

    Distinct from a ticket the tracker records no parent for: that one is ordinary and
    means there is no batch, this one means the question went unanswered.
    """


def fetch_parent(number: int) -> int | None:
    """The spec GitHub records `number` under, or `None` when it records none.

    This is the sub-issue link `fetch_sub_issues` reads from the other end, so a ticket
    and its batch always name each other. Raises `ParentUnreadable` when the tracker
    could not be asked. Patched out in tests.
    """
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "parent"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if out.returncode != 0:
        raise ParentUnreadable(gh_detail(out))
    try:
        parent = json.loads(out.stdout).get("parent")
        return int(parent["number"]) if parent else None
    except (AttributeError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ParentUnreadable(
            f"`gh issue view {number} --json parent` answered with nothing this can "
            f"read") from None


def fetch_outsider(number: int) -> dict:
    """Where a blocker outside this batch belongs, and whether it is closed.

    A blocking link always points at an issue that exists, so the question is not
    whether it is there but whether it is a ticket: an issue whose `## Parent` names a
    spec. `spec` is that number, or `None` for an issue that is something else.
    Patched out in tests.
    """
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "state,body"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if out.returncode != 0:
        return {"spec": None, "state": ""}
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"spec": None, "state": ""}
    return {"spec": parent_spec(data.get("body") or ""),
            "state": (data.get("state") or "").upper()}


def section(body: str, heading: str) -> list[str]:
    """The lines under `## <heading>`, up to the next `## ` heading."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def parent_spec(body: str) -> int | None:
    """The first spec number in `## Parent`, e.g. `#76, Implementation Decisions section 1`.

    This section is the copy the user reads, and one ticket may be written against
    sections of more than one spec, in whatever order suits the reader. Which batch the
    ticket belongs to is `spec_of`: the tracker's parent link, falling back to this.
    `repo#n` and `owner/repo#n` are another repository's issue and are not a spec here.
    """
    for line in section(body, "Parent"):
        m = ISSUE_REF_RE.search(line)
        if m:
            return int(m.group(1))
    return None


def spec_of(number: int) -> int | None:
    """The spec this ticket sits under: the tracker's parent link, else `## Parent`.

    A ticket written against sections of more than one spec names them all in `## Parent`,
    in reader order. The batch is the sub-issue link `fetch_parent` reads; only when the
    tracker records none does this fall back to `parent_spec`.
    """
    parent = fetch_parent(number)
    if parent is not None:
        return parent
    return parent_spec(fetch_body(number))


def owns_globs(body: str) -> list[str]:
    """The paths this ticket is allowed to write, from `## Owns`. `(new)` is a note.
    Wrapping backticks are stripped so a `:(glob,exclude)` pathspec matches the path.
    """
    globs = []
    for line in section(body, "Owns"):
        m = re.match(r"^\s*-\s+(\S+)", line)
        if not m:
            continue
        value = m.group(1)
        value = value.strip("`")
        if value.lower().startswith("none"):
            continue
        globs.append(value)
    return globs


# ------------------------------------------------------------------------ git

def git(*args: str, cwd: Path | None = None) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_root() -> Path:
    top = git("rev-parse", "--show-toplevel")
    return Path(top) if top else Path.cwd()


def outside_owns_line(number: int, globs: list[str], root: Path) -> str:
    """The comment's `Outside Owns:` line.

    The question it answers — did this ticket write outside what it owns — is asked of
    this ticket's own commits, so it can only be answered on this ticket's own branch.
    A re-run on the branch the tickets were merged into is walking every ticket's
    commits, which answers nothing and runs past the 65536 characters a comment holds.
    """
    branch = current_branch(root)
    if branch != f"issue-{number}":
        return (f"Outside Owns: not checked on {branch or '(detached)'}, which carries "
                f"more than this ticket")
    outside = outside_owns(globs, root)
    return "Outside Owns: " + (", ".join(outside) if outside else "None")


def current_branch(root: Path | None = None) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)


def base_ref(root: Path | None = None) -> str:
    """The commit this ticket's branch was cut from.

    `dispatch.sh` records it in `branch.issue-<n>.mmw-base` when it opens the worktree:
    the HEAD of whatever branch the dispatching session was on. A branch with no record
    falls back to `main`.
    """
    ref = git("config", f"branch.{current_branch(root)}.mmw-base", cwd=root)
    return ref or "main"


def dirty_tracked(root: Path | None = None) -> list[str]:
    """Uncommitted changes to tracked files. Untracked files do not count: a CHECK
    command writes its own screenshots and cache directories as it runs."""
    out = git("status", "--porcelain", "--untracked-files=no", cwd=root)
    return [line for line in out.splitlines() if line.strip()]


def is_ancestor(commit: str, descendant: str, root: Path | None = None) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, descendant],
        capture_output=True, text=True, cwd=root,
    )
    return result.returncode == 0


def outside_owns(globs: list[str], root: Path) -> list[str]:
    """Files this ticket's own commits changed that no `## Owns` glob covers.

    Only the commits made on this branch itself count: the first-parent chain since it
    left its base, merge commits excluded. A later ticket merges an earlier ticket's
    branch to build on it, and the files that ride in with that merge are the earlier
    ticket's work, not this one's.
    """
    base = git("merge-base", base_ref(root), "HEAD", cwd=root)
    if not base:
        return []
    args = ["log", "--first-parent", "--no-merges", "--name-only", "--format=",
            f"{base}..HEAD", "--", "."]
    args += [f":(glob,exclude){g}" for g in globs]
    out = git(*args, cwd=root)
    seen: list[str] = []
    for line in out.splitlines():
        if line.strip() and line not in seen:
            seen.append(line)
    return seen


# ------------------------------------------------------------------- ledger

def ledger_from_comment(comment: str) -> list[str]:
    """The ledger a previous run posted: from its first gate line to `Outside Owns:`."""
    lines = comment.splitlines()
    start = next((i for i, line in enumerate(lines) if GATE_LINE_RE.match(line)), None)
    if start is None:
        return []
    end = next((i for i, line in enumerate(lines[start:], start)
                if line.startswith("Outside Owns:")), len(lines))
    out = lines[start:end]
    while out and not out[-1].strip():
        out.pop()
    return out


EVIDENCE_LINE_RE = re.compile(r"^\s+EVIDENCE:")


def criteria_shape(lines: list[str]) -> list[str]:
    """A ledger's criteria as identity alone: each criterion's text and its command,
    with neither the tick nor the evidence any one run wrote."""
    out = []
    for line in lines:
        if EVIDENCE_LINE_RE.match(line) or TIMEOUT_LINE_RE.match(line):
            continue
        m = GATE_LINE_RE.match(line)
        out.append(f"- [ ] {line[6:]}" if m else line.rstrip())
    return out


def carried_ledger(number: int, body: str) -> list[str]:
    """The previous run's ledger, when it still describes the body's criteria.

    A criterion the ticket has since rewritten — a decision changed what this ticket
    must do, and the ticket says so — lives on the body and not in that comment, so a
    ledger that no longer matches is dropped and the criteria are read fresh. What is
    lost with it is the evidence of a run of the criteria as they used to be.
    """
    carried = previous_ledger(number)
    if not carried:
        return []
    if criteria_shape(carried) != criteria_shape(section(body, "Acceptance criteria")):
        return []
    return carried


def previous_ledger(number: int) -> list[str]:
    """The ledger from the newest `self-run` / `reverify` comment, if there is one.

    A re-verification re-runs what the last run ticked, so the previous run's comment is
    where that state lives.
    """
    for comment in reversed(fetch_comments(number)):
        first = comment.strip().splitlines()[0].strip() if comment.strip() else ""
        if first in ("self-run", "reverify"):
            ledger = ledger_from_comment(comment)
            if ledger:
                return ledger
    return []


def write_ledger(body: str, directory: Path, lines: list[str] | None = None) -> Path:
    """The `## Acceptance criteria` section as a ledger file.

    Verbatim but for `TIMEOUT:` lines, which gate-check does not read: they are this
    script's, taken off the ticket body by `check_timeout`.
    """
    criteria = lines if lines is not None else section(body, "Acceptance criteria")
    path = directory / LEDGER_NAME
    kept = [line for line in criteria if not TIMEOUT_LINE_RE.match(line)]
    path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    return path


def check_timeout(body: str, asked: int | None) -> int:
    """Seconds gate-check gets per `CHECK:` on this ticket.

    The largest of `DEFAULT_TIMEOUT`, every `TIMEOUT:` in `## Acceptance criteria`, and
    `--timeout` when given: a ticket can raise the limit and never lower it, and it is
    read off the ticket body whichever run this is, so the verifier's `--reverify` runs
    under the same number as the worker's own run.
    """
    values = [DEFAULT_TIMEOUT]
    for criterion in parse_criteria("\n".join(section(body, "Acceptance criteria"))):
        if criterion["timeout"].isdigit() and int(criterion["timeout"]) > 0:
            values.append(int(criterion["timeout"]))
    if asked:
        values.append(asked)
    return max(values)


# ------------------------------------------------------------- closing comment

def parse_criteria(text: str) -> list[dict]:
    """Every criterion in `text`, with the attributes written under it.

    One reader, because a ledger has one shape. Three readers, each deciding for itself
    where a criterion ends, is how a criterion came to be read three different ways and
    a ticket with a fenced `CHECK:` could not close.

    A `CHECK:` whose command needs more than a line carries it in a fenced block, and
    nothing inside that block is ledger syntax: a `- [ ]` line in a heredoc is text the
    command prints, not the next criterion. Every other fence in the text is skipped
    whole, the way a ticket quoting an example criterion has always been skipped.
    """
    out: list[dict] = []
    item = None
    fence = None
    last_attr = None
    for line in text.splitlines():
        previous_attr, last_attr = last_attr, None
        if fence is not None:
            close = FENCE_CLOSE_RE.match(line)
            if close and close.group(1)[0] == fence["char"] and len(close.group(1)) >= fence["length"]:
                if fence["item"] is not None:
                    indent = fence["indent"]
                    fence["item"]["check"] = "\n".join(
                        row[len(indent):] if row.startswith(indent) else row.lstrip()
                        for row in fence["body"])
                fence = None
            elif fence["item"] is not None:
                fence["body"].append(line)
            continue
        opened = FENCE_OPEN_RE.match(line)
        # A ``` line whose info string carries another backtick is not a fence, and
        # `gates.mjs` says so too. Two readers disagreeing about where a fence opens is
        # the fault this format was meant to end: one of them would swallow the next
        # criterion whole and the counts would stop matching.
        if opened and opened.group(2)[0] == "`" and "`" in opened.group(3):
            opened = None
        if opened:
            fence = {"char": opened.group(2)[0], "length": len(opened.group(2)),
                     "indent": opened.group(1), "body": [],
                     "item": item if previous_attr == "check" else None}
            continue
        gate = GATE_LINE_RE.match(line)
        if gate:
            item = {"id": gate.group(2), "ticked": gate.group(1) != " ",
                    "title": line[gate.end():].strip(),
                    "check": "", "expect": "", "evidence": "", "timeout": "",
                    "stray": False}
            out.append(item)
            continue
        if item is None:
            continue
        attr = ATTR_LINE_RE.match(line)
        if attr:
            key = attr.group(1).lower()
            value = line.split(":", 1)[1].strip()
            if key in ("check", "expect", "evidence", "timeout"):
                item[key] = value
            last_attr = key
            continue
        if previous_attr == "check" and line.strip():
            # `gates.mjs` refuses this ledger outright. Reading it here as a criterion
            # with a one-line command would put the two readers back where they were:
            # one running nothing, the other counting it as fine.
            item["stray"] = True
    return out


def count_gates(ledger: Path) -> tuple[int, int]:
    """(met, total) read off the ledger: a met gate is ticked with real evidence."""
    criteria = parse_criteria(ledger.read_text(encoding="utf-8"))
    met = sum(1 for c in criteria
              if c["ticked"] and c["evidence"] and c["evidence"] != "pending")
    return met, len(criteria)


def parse_abandons(text: str) -> list[dict]:
    """The `ABANDON: AC<n> <kind> <reason>` lines, which sit flush left under their criterion."""
    out = []
    for line in text.splitlines():
        m = ABANDON_RE.match(line)
        if m:
            out.append({"ac": m.group(1), "kind": m.group(2), "reason": m.group(3).strip()})
    return out


def tally(criteria: list[dict], abandons: list[dict]) -> dict:
    """Recount the draft. A tick with `EVIDENCE: pending` is unmet, not met."""
    abandoned_ids = {a["ac"] for a in abandons}
    counts = {"met": 0, "unmet": 0, "abandoned": 0, "total": len(criteria)}
    for c in criteria:
        filled = c["evidence"] and c["evidence"] != "pending"
        if c["id"] in abandoned_ids:
            counts["abandoned"] += 1
        elif c["ticked"] and filled:
            counts["met"] += 1
        else:
            counts["unmet"] += 1
    return counts


def draft_line(text: str, prefix: str) -> str | None:
    """The first line starting with `prefix`, without it."""
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def last_verdict(comments: list) -> str | None:
    """The commit the newest `verifier.passed` or `verifier.failed` event covers."""
    found = events.newest(comments, "verifier.passed", "verifier.failed")
    commit = (found or {}).get("payload", {}).get("commit")
    return commit if isinstance(commit, str) and commit else None


def newest_with_first_line(comments: list[str], *prefixes: str) -> str | None:
    """The newest comment whose first line is one of `prefixes`, `None` when none.

    A first line matches a prefix when it equals it or starts with that prefix
    plus a space.
    """
    for comment in reversed(comments):
        first = comment.strip().splitlines()[0].strip() if comment.strip() else ""
        if any(first == prefix or first.startswith(prefix + " ") for prefix in prefixes):
            return comment
    return None


def last_run(comments: list[str]) -> str | None:
    """The newest `self-run` or `reverify` comment on the ticket, `None` when none."""
    return newest_with_first_line(comments, "self-run", "reverify")


def last_reverify(comments: list[str]) -> str | None:
    """The newest `reverify` comment on the ticket, `None` when none.

    A `self-run` is the worker's own measurement of its own work; a `reverify` is the
    verifier's, of the same criteria on the same commit. The closing gate reads only
    this one, because the other is written by the party being judged.
    """
    return newest_with_first_line(comments, "reverify")


def run_summary(run: str | None) -> str | None:
    """The gate-check summary line of one run comment, `None` when it has none.

    A run comment opens with its own name and carries gate-check's summary on the line
    under it, so that line is what the run reports about the criteria.
    """
    if run is None:
        return None
    lines = run.strip().splitlines()
    summary = lines[1].strip() if len(lines) > 1 else ""
    return summary if SUMMARY_RE.match(summary) else None


def run_unmet(run: str | None) -> list[str]:
    """The criteria one run's ledger left unmet, by id."""
    if run is None:
        return []
    return [c["id"] for c in parse_criteria(run)
            if not (c["ticked"] and c["evidence"] and c["evidence"] != "pending")]


def last_run_summary(comments: list[str]) -> str | None:
    """The summary line of the newest `self-run` or `reverify` comment on the ticket."""
    return run_summary(last_run(comments))


def last_run_unmet(comments: list[str]) -> list[str]:
    """The criteria the newest run's ledger left unmet, by id."""
    return run_unmet(last_run(comments))


def draft_problems(draft: str, comments: list[str]) -> list[str]:
    """Everything wrong with the draft itself, in the order a reader would hit it."""
    problems = []
    lines = draft.strip().splitlines()
    first = lines[0].strip() if lines else ""
    handoff = HANDOFF_RE.match(first)
    if first != "ALL MET" and not handoff:
        return ["first line is neither `ALL MET` nor `HANDOFF REQUIRED: <n> abandoned "
                "(<kinds>), <m> unmet, <k> met of <total>`: " + (first or "(empty draft)")]
    if FILL in draft:
        problems.append("the draft still contains `<fill>`; replace the placeholders "
                        "in `skipped:` and `Decisions I made on my own`")

    criteria = parse_criteria(draft)
    ids = [c["id"] for c in criteria]
    abandons = parse_abandons(draft)
    for a in abandons:
        if a["kind"] not in ABANDON_KINDS:
            problems.append(f"ABANDON: {a['ac']} has kind `{a['kind']}`; "
                            f"it must be one of {', '.join(ABANDON_KINDS)}")
        if a["ac"] not in ids:
            problems.append(f"ABANDON: {a['ac']} points at a criterion the draft does not list")

    blocking = sorted({a["kind"] for a in abandons if a["kind"] in HANDOFF_KINDS})
    if first == "ALL MET" and blocking:
        problems.append(f"first line is `ALL MET` but the draft abandons a criterion as "
                        f"{', '.join(blocking)}; only `decision` may be abandoned and still "
                        f"close the ticket")

    for c in criteria:
        if c.get("stray"):
            problems.append(f"{c['id']} continues its CHECK onto another line; wrap the "
                            f"command in a fenced block under `CHECK:` instead")
        if c["ticked"] and (not c["evidence"] or c["evidence"] == "pending"):
            problems.append(f"{c['id']} is ticked but its EVIDENCE is pending; "
                            f"either fill in what proved it or untick it")

    counts = tally(criteria, abandons)
    if first == "ALL MET" and counts["unmet"]:
        problems.append(f"first line is `ALL MET` but {counts['unmet']} criteria are unmet")

    stated = draft_line(draft, "Counts:")
    m = COUNTS_RE.match("Counts: " + stated) if stated is not None else None
    if not m:
        problems.append("no `Counts: <k> met, <m> unmet, <n> abandoned of <total>` line")
    else:
        got = dict(zip(("met", "unmet", "abandoned", "total"),
                       (int(g) for g in m.groups())))
        if got != counts:
            problems.append(
                "Counts: says {met} met, {unmet} unmet, {abandoned} abandoned "
                "of {total}".format(**got) +
                "; the draft reads {met} met, {unmet} unmet, {abandoned} abandoned "
                "of {total}".format(**counts))
        if handoff:
            said = {"abandoned": int(handoff.group(1)), "unmet": int(handoff.group(3)),
                    "met": int(handoff.group(4)), "total": int(handoff.group(5))}
            off = [f"{k}: first line says {said[k]}, `Counts:` says {got[k]}"
                   for k in ("abandoned", "unmet", "met", "total") if said[k] != got[k]]
            if off:
                problems.append("the first line and the `Counts:` line disagree — "
                                + "; ".join(off))

    return problems


def verified_problems(draft: str, body: str, comments: list[str]) -> list[str]:
    """What an `ALL MET` draft lacks in independent verification, in reader order.

    Three facts, and all three are ones the worker cannot write for itself: the
    verifier's own run of the criteria, the commit that run was made on, and the
    criteria it ran. On 2026-09-06 #162 closed `ALL MET` with none of them holding —
    the verifier had posted `VERDICT … AC1 failed`, the worker then rewrote AC1's
    `CHECK:` into a command that passed, re-ran it itself, and closed on the same
    commit. Each check below is one of the three doors that let that through.

    `HANDOFF REQUIRED` reaches none of this. A worker whose verifier will not run must
    still be able to hand the ticket back; demanding an independent check before it may
    say "I could not do this" would leave it with no legal move at all.
    """
    problems = []
    lines = draft.strip().splitlines()
    first = lines[0].strip() if lines else ""
    if first != "ALL MET":
        return problems

    reverify = last_reverify(comments)
    if reverify is None:
        problems.append("the ticket carries no `reverify` comment, so nothing but this "
                        "ticket's own author has run its criteria. Dispatch the verifier; "
                        "if it cannot run, close out as `HANDOFF REQUIRED` instead and say so")
    else:
        # A run is generated from the ticket body, which carries no `ABANDON:` line, so a
        # criterion the draft abandons as `decision` still runs and still reports unmet.
        # That unmet is the one this draft is allowed to carry: the sub-issue is open and
        # the ticket closes on it. Any other unmet is a claim the draft cannot make.
        decided = {a["ac"] for a in parse_abandons(draft) if a["kind"] == "decision"}
        summary = run_summary(reverify)
        unmet = run_unmet(reverify)
        covered = (summary is not None and summary.startswith("UNMET:")
                   and unmet and set(unmet) <= decided)
        if summary and summary.startswith(("UNMET:", "HANDOFF REQUIRED:")) and not covered:
            problems.append("the verifier's newest `reverify` still reports unmet or "
                            "abandoned criteria — a `self-run` of your own does not settle "
                            "it. Dispatch the verifier again, or close out as "
                            "`HANDOFF REQUIRED`")
        # The criteria the verifier ran must be the criteria the ticket now states. A
        # ticket may legitimately rewrite one — a decision changed what it must do — but
        # then what stands is a verification of something else, and the verifier runs again.
        if criteria_shape(ledger_from_comment(reverify)) != \
                criteria_shape(section(body, "Acceptance criteria")):
            problems.append("the acceptance criteria have changed since the verifier ran: "
                            "its `reverify` ledger and the ticket body no longer describe "
                            "the same criteria. Dispatch the verifier again so the run and "
                            "the ticket agree")

    verdict = last_verdict(comments)
    if verdict is None:
        problems.append("the ticket carries no `VERDICT` — no verifier.passed or "
                        "verifier.failed event — so nothing but this ticket's own author "
                        "says the work is done. Dispatch the verifier; if it cannot run, "
                        "close out as `HANDOFF REQUIRED` instead and say so")
    elif not git("rev-parse", "HEAD").startswith(verdict):
        problems.append(f"the `VERDICT` is on {verdict} and HEAD has moved on. What was "
                        f"independently verified is not what would be merged; dispatch the "
                        f"verifier again on this commit")
    return problems


def event_problems(comments: list) -> list[str]:
    """Comments on the ticket whose event cannot be read.

    The closing gate decides from the ticket's events, so a comment that carries one
    this pipeline cannot read is a question left unanswered, not a comment to skip.
    """
    return [f"comment {item['comment']} (`{item['line'][:50]}`) carries an event this "
            f"pipeline cannot read: {item['reason']}"
            for item in events.fold(comments)["unreadable"]]


def git_problems(root: Path | None = None) -> list[str]:
    """The repository conditions a ticket must be in to close, plus one warning."""
    problems = []
    dirty = dirty_tracked(root)
    if dirty:
        problems.append(f"{len(dirty)} tracked files have uncommitted changes; "
                        f"commit them so the closing comment names a real commit")
    ref = base_ref(root)
    if not is_ancestor(ref, "HEAD", root):
        problems.append(f"this branch does not contain its base {ref}; run `git merge {ref}`. "
                        f"Do not rebase — the `VERDICT` on this ticket names one commit, and "
                        f"rewriting history throws it away")
        return problems
    base = git("merge-base", ref, "HEAD", cwd=root)
    if base and not git("diff", "--name-only", f"{base}..HEAD", cwd=root):
        sys.stderr.write("warning: this branch changes no files since it left its base branch\n")
    return problems


# ---------------------------------------------------------------- ticket graph
# `validate_dag`, `_detect_cycles`, `_trace_cycle` and `compute_levels` are
# grok-bundled's `execute-plan/scripts/validate-plan.py` L145-280, function for
# function. Only the shape of an entry changed: an id is an issue number rather
# than a `pr-<n>` string, and dependencies come from the tracker's blocking links.
#
# A plan's steps all lived in one plan; a ticket's blockers do not. A spec delivered in
# layers blocks its tickets on tickets under the spec before it, and an issue that is no
# ticket at all can be linked as a blocker too. Neither is an edge these four can order,
# so `in_batch` takes them out before the graph is built, and `blockers_not_tickets`,
# `cross_batch_findings` and `waiting_outside` say what was taken out and what it means.

def validate_dag(entries: list[dict]) -> list[str]:
    """Check unique ids and no cycles. Dependencies are already this batch's.

    A blocker outside the batch is not a dangling reference here: `in_batch` has taken
    it out, and `blockers_not_tickets` / `cross_batch_findings` say what it is.
    """
    errors = []

    seen = set()
    for entry in entries:
        if entry["id"] in seen:
            errors.append(f"duplicate ticket: #{entry['id']}  [duplicate-ticket]")
        seen.add(entry["id"])

    if not errors:
        errors.extend(_detect_cycles(entries))

    return errors


def _detect_cycles(entries: list[dict]) -> list[str]:
    """Kahn's algorithm for topological sort; returns cycle errors."""
    in_degree = {e["id"]: 0 for e in entries}
    children = defaultdict(list)
    dep_map = {e["id"]: e["dependencies"] for e in entries}

    for entry in entries:
        for dep in entry["dependencies"]:
            children[dep].append(entry["id"])
            in_degree[entry["id"]] += 1

    queue = deque(eid for eid, deg in in_degree.items() if deg == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if visited == len(entries):
        return []

    unvisited = [e["id"] for e in entries if in_degree[e["id"]] > 0]
    cycle = _trace_cycle(dep_map, unvisited)
    if cycle:
        return ["cycle detected: " + " -> ".join(f"#{i}" for i in cycle) + "  [cycle]"]
    return ["cycle detected involving: "
            + ", ".join(f"#{i}" for i in sorted(unvisited)) + "  [cycle]"]


def _trace_cycle(dep_map: dict, unvisited_ids: list) -> list | None:
    """Walk deps among *unvisited_ids* to report one cycle path."""
    unvisited = set(unvisited_ids)
    current = unvisited_ids[0]
    path = [current]
    visited_in_path = {current}

    while True:
        next_node = None
        for dep in dep_map.get(current, []):
            if dep in unvisited:
                next_node = dep
                break
        if next_node is None:
            break
        if next_node in visited_in_path:
            idx = path.index(next_node)
            return path[idx:] + [next_node]
        path.append(next_node)
        visited_in_path.add(next_node)
        current = next_node

    return None


def compute_levels(entries: list[dict]) -> dict:
    """Return ``{ticket: level}``; level 0 = nothing blocks it, so it starts first."""
    children = defaultdict(list)
    in_degree = {e["id"]: 0 for e in entries}

    for e in entries:
        for dep in e["dependencies"]:
            children[dep].append(e["id"])
            in_degree[e["id"]] += 1

    levels = {}
    queue = deque()
    for eid, deg in in_degree.items():
        if deg == 0:
            levels[eid] = 0
            queue.append(eid)

    while queue:
        node = queue.popleft()
        for child in children[node]:
            candidate = levels[node] + 1
            levels[child] = max(levels.get(child, 0), candidate)
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    return levels


def in_batch(entries: list[dict]) -> list[dict]:
    """The same entries with every dependency outside the batch dropped.

    A blocking link to another spec's ticket is a real edge, and `--preflight`,
    `dispatch.sh advance` and `status.py` all honour it — but it is not an edge this graph can
    order, because the other end has no entry here. Left in, it would hold that ticket's
    in-degree above zero forever, which Kahn's algorithm reads as a cycle and
    `compute_levels` reads as a ticket with no level at all.
    """
    ids = {e["id"] for e in entries}
    return [{**e, "dependencies": [d for d in e["dependencies"] if d in ids]}
            for e in entries]


def _outside(entry: dict, dep: int) -> dict:
    """What `ticket_entries` found out about one blocker outside the batch."""
    return ((entry.get("outside") or {}).get(dep)) or {}


def blockers_not_tickets(entries: list[dict]) -> list[str]:
    """Blocking links to issues that are not tickets under any spec.

    A blocking link always points at an issue that exists, so what is asked here is
    whether that issue is a ticket: one whose `## Parent` names a spec. An issue that
    names none — a bug, a note, a discussion — is a blocker no part of this pipeline
    will ever close, and the ticket waiting on it can never start.
    """
    ids = {e["id"] for e in entries}
    errors = []
    for entry in entries:
        for dep in entry["dependencies"]:
            if dep in ids or _outside(entry, dep).get("spec"):
                continue
            errors.append(f"#{entry['id']} is blocked by #{dep}, which is not a ticket "
                          f"under any spec  [blocker-not-a-ticket]")
    return errors


def cross_batch_findings(entries: list[dict]) -> list[str]:
    """Blocking links to tickets under another spec.

    Not a fault to fix: it is the shape a layered delivery has, and `--preflight`,
    `dispatch.sh advance` and `status.py` all refuse to start a ticket while one of these is
    open. It is reported because the start levels are built without it, so a reader who
    took them for the whole truth would miss that one of these tickets is waiting on a
    spec that is not in front of them.
    """
    findings = []
    for entry in entries:
        for dep, where in sorted((entry.get("outside") or {}).items()):
            if not where.get("spec"):
                continue
            findings.append(f"#{entry['id']} is blocked by #{dep}, a ticket under spec "
                            f"#{where['spec']} ({where.get('state') or 'unknown'}); the "
                            f"start levels below are this spec's own order only")
    return findings


def waiting_outside(entries: list[dict]) -> list[str]:
    """Tickets that cannot start yet because a ticket under another spec is still open.

    The start levels say where a ticket sits among its own batch. These lines say the
    batch is not the whole of what it waits on.
    """
    lines = []
    for entry in entries:
        for dep, where in sorted((entry.get("outside") or {}).items()):
            if where.get("spec") and where.get("state") != "CLOSED":
                lines.append(f"waiting on another spec: #{entry['id']} ← #{dep} "
                             f"({where.get('state') or 'unknown'}, spec #{where['spec']})")
    return lines


def ticket_entries(numbers: list[int]) -> list[dict]:
    """One entry per ticket: the blocking links the tracker records.

    `dependencies` is what the tracker records, and it is the graph every check below
    runs on — the same edges `--preflight` refuses on and `dispatch.sh advance` dispatches from.

    A dependency outside this batch is kept, and `outside` says what was found at the
    other end of it: `{number: {"spec": …, "state": …}}`. One lookup per distinct
    blocker rather than one per edge — several tickets of a batch commonly wait on the
    same one.
    """
    batch = set(numbers)
    entries = [{"id": n, "dependencies": fetch_blocked_by(n)} for n in numbers]
    found: dict[int, dict] = {}
    for entry in entries:
        for dep in entry["dependencies"]:
            if dep not in batch and dep not in found:
                found[dep] = fetch_outsider(dep)
    for entry in entries:
        entry["outside"] = {d: found[d] for d in entry["dependencies"] if d in found}
    return entries


# ---------------------------------------------------------- worker mechanical

def refuse(message: str) -> int:
    """Exit 2 with the reason on stderr. Nothing is posted."""
    sys.stderr.write(message.rstrip() + "\n")
    return 2


def outside_owns_from(text: str) -> str | None:
    """The `Outside Owns:` line in `text`, stripped, or `None` when absent."""
    for line in text.splitlines():
        if line.startswith("Outside Owns:"):
            return line.strip()
    return None


def markdown_h2(text: str) -> list[str]:
    """The `## ` heading titles in document order."""
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


def glob_covers(pattern: str, path: str) -> bool:
    """Whether an `## Owns` glob covers `path`."""
    pattern = pattern.rstrip("/")
    if pattern.endswith("/**"):
        root = pattern[:-3]
        return path == root or path.startswith(root + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern


def spec_judgement(review: str, path: str) -> str | None:
    """`reasonable` or `should not` for `path` from the Spec axis of a `REVIEW` comment.

    `None` when that axis names no line for the file — the run does not invent a
    judgement the reviewer did not write.
    """
    spec_axis = re.split(r"^## Tests", review, maxsplit=1, flags=re.M)[0]
    spec_axis = re.split(r"^## Spec", spec_axis, maxsplit=1, flags=re.M)[-1]
    for line in spec_axis.splitlines():
        if path in line:
            if "should not" in line:
                return "should not"
            if "reasonable" in line:
                return "reasonable"
    return None


def decisions_line_for(decisions: str | None, path: str, number: int) -> str:
    """The sentence in the `DECISIONS` comment that names `path`."""
    if not decisions:
        return f"no DECISIONS comment on #{number} yet"
    for line in decisions.splitlines():
        stripped = line.strip()
        if path in stripped and not stripped.startswith("Outside Owns:"):
            return stripped.lstrip("- ").strip()
    return path


def outside_owns_files(line: str | None) -> list[str]:
    """The paths on an `Outside Owns:` line; empty when `None` or not checked."""
    if not line:
        return []
    rest = line[len("Outside Owns:"):].strip()
    if rest == "None" or rest.startswith("not checked"):
        return []
    return [p.strip() for p in rest.split(",") if p.strip()]


def overlay_run_evidence(body: str, run: str | None) -> list[dict]:
    """Criteria from the ticket body, ticks and evidence from the newest `self-run`."""
    base = parse_criteria("\n".join(section(body, "Acceptance criteria")))
    ran = {c["id"]: c for c in parse_criteria(run or "")}
    for item in base:
        if item["id"] in ran:
            item["ticked"] = ran[item["id"]]["ticked"]
            if ran[item["id"]]["evidence"]:
                item["evidence"] = ran[item["id"]]["evidence"]
    return base


def criterion_block(item: dict) -> str:
    """The four ledger lines of one criterion."""
    tick = "x" if item["ticked"] else " "
    lines = [f"- [{tick}] {item['id']}: {item['title']}"]
    check = item["check"]
    if "\n" in check:
        lines.append("  CHECK:")
        lines.append("  ```")
        lines.extend(("  " + row) if row else "" for row in check.splitlines())
        lines.append("  ```")
    else:
        lines.append(f"  CHECK: {check}")
    lines.append(f"  EXPECT: {item['expect']}")
    evidence = item["evidence"] or "pending"
    lines.append(f"  EVIDENCE: {evidence}")
    return "\n".join(lines)


def run_decisions(number: int, path: Path) -> int:
    """Post the two-section file as a `DECISIONS` comment, or refuse."""
    comments = fetch_comments(number)
    if events.newest(comments, "worker.decided") is not None:
        return refuse(f"#{number} already carries a DECISIONS comment")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    headings = markdown_h2(text)
    expected_headings = ["Decisions I made on my own", "Outside Owns"]
    if headings != expected_headings:
        missing = [h for h in expected_headings if h not in headings]
        if missing:
            return refuse("the file is missing section"
                          + ("s " if len(missing) > 1 else " ")
                          + " and ".join(f"`{h}`" for h in missing))
        extra = [h for h in headings if h not in expected_headings]
        if extra:
            return refuse("the file has extra section"
                          + ("s " if len(extra) > 1 else " ")
                          + " and ".join(f"`{h}`" for h in extra)
                          + "; it must have exactly two sections, "
                          "`Decisions I made on my own` then `Outside Owns`")
        return refuse("the file must have exactly two sections, "
                      "`Decisions I made on my own` then `Outside Owns`")
    run = newest_with_first_line(comments, "self-run")
    if run is None:
        return refuse(f"#{number} carries no self-run comment to check Outside Owns against")
    want = outside_owns_from(run)
    got = outside_owns_from("\n".join(section(text, "Outside Owns")))
    if want != got:
        return refuse("the file's `Outside Owns` line does not match the newest self-run")
    post_event(number, "worker.decided", "DECISIONS", text.lstrip("\n"))
    print(f"DECISIONS: posted on #{number}")
    return 0


def open_children_owns(number: int) -> list[tuple[int, list[str]]]:
    """OPEN children of `number` and each child's `## Owns` globs, loaded once."""
    found = []
    for child in fetch_sub_issues(number):
        ticket = fetch_ticket(child)
        if (ticket.get("state") or "").upper() != "OPEN":
            continue
        found.append((child, owns_globs(fetch_body(child))))
    return found


REVIEW_HEAD_RE = re.compile(r"^REVIEW (\S+?)\.\.(\S+)")


def run_review(number: int, path: Path) -> int:
    """Post the review report on the ticket, as the `reviewer.reported` event.

    Nothing here tells the worker: the event on the ticket is what the relay of the
    dispatch skill turns into the worker's wake-up, so a report that lands is a report
    its worker hears about, however the reviewer's turns fell.

    The file opens `REVIEW <base commit>..<HEAD commit>`: that line becomes the
    comment's first line, and the two commits become the `reviewer.reported` event's
    `base` and `head`. A file that does not open with it is refused rather than posted,
    since a report that names no commits does not say which diff it read.
    """
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    stripped = text.strip()
    head = stripped.splitlines()[0].strip() if stripped else ""
    found = REVIEW_HEAD_RE.match(head)
    if not found:
        return refuse(
            "a review comment opens `REVIEW <base commit>..<HEAD commit>`, and this file "
            + (f"opens `{head[:60]}`" if head else "is empty"))
    rest = "\n".join(stripped.splitlines()[1:]).strip("\n")
    post_event(number, "reviewer.reported", head, rest,
               base=found.group(1), head=found.group(2))
    print(f"REVIEW: posted on #{number}")
    return 0


def run_touched(number: int) -> int:
    """Comment `TOUCHED BY #<n>` on open siblings whose `## Owns` covers a file."""
    comments = fetch_comments(number)
    review = (events.newest(comments, "reviewer.reported") or {}).get("body")
    if review is None:
        return refuse(f"#{number} carries no REVIEW comment")
    run = newest_with_first_line(comments, "self-run")
    if run is None:
        return refuse(f"#{number} carries no self-run comment")
    files = outside_owns_files(outside_owns_from(run))
    if not files:
        return 0
    decisions = (events.newest(comments, "worker.decided") or {}).get("body")
    try:
        spec = spec_of(number)
    except ParentUnreadable as exc:
        return refuse(f"#{number}: the tracker could not say which spec it sits under ({exc})")
    if spec is None:
        return refuse(f"#{number} has no parent link and no spec in `## Parent`")
    try:
        siblings = open_children_owns(spec)
    except SubIssuesUnreadable as exc:
        return refuse(f"#{number}: the tracker could not list the children of #{spec} ({exc})")
    posted_to: list[int] = []
    for path in files:
        sentence = decisions_line_for(decisions, path, number)
        judgement = spec_judgement(review, path)
        ac = ""
        found = re.search(r"\bAC\d+\b", sentence)
        if found:
            ac = found.group(0)
        lines = [
            f"TOUCHED BY #{number}",
            "",
            path,
            sentence,
        ]
        if ac:
            lines.append(ac)
        if judgement:
            lines.append(judgement)
        comment = "\n".join(lines) + "\n"
        for child, globs in siblings:
            if not any(glob_covers(g, path) for g in globs):
                continue
            post_prose(child, comment)
            posted_to.append(child)
    if posted_to:
        print("TOUCHED: " + ", ".join(f"#{n}" for n in posted_to))
    return 0


def run_draft(number: int, out_file: Path) -> int:
    """Write the closing-comment skeleton to `out_file`."""
    body = fetch_body(number)
    comments = fetch_comments(number)
    run = newest_with_first_line(comments, "self-run")
    criteria = overlay_run_evidence(body, run)
    abandons = parse_abandons(run or "")
    counts = tally(criteria, abandons)
    blocking = [a for a in abandons if a["kind"] in HANDOFF_KINDS]
    if blocking:
        kinds = ", ".join(k for k in HANDOFF_KINDS if any(a["kind"] == k for a in blocking))
        first = (f"HANDOFF REQUIRED: {counts['abandoned']} abandoned ({kinds}), "
                 f"{counts['unmet']} unmet, {counts['met']} met of {counts['total']}")
    else:
        first = "ALL MET"
    head = git("rev-parse", "HEAD")
    base_branch = git("config", f"branch.issue-{number}.mmw-base-branch") or "main"
    branch_line = (f"Branch: issue-{number} Commit: {head} PR: none — will be merged into "
                   f"{base_branch} by dispatch.sh advance")
    review = (events.newest(comments, "reviewer.reported") or {}).get("body") or ""
    files = outside_owns_files(outside_owns_from(run or ""))
    if files:
        judged = []
        for path in files:
            judgement = spec_judgement(review, path)
            judged.append(f"{path} ({judgement})" if judgement else path)
        outside = "Outside Owns: " + ", ".join(judged)
    else:
        outside = "Outside Owns: None"
    try:
        opened = [f"#{child}" for child in fetch_sub_issues(number)]
        sub = "Sub-issues opened: " + (", ".join(opened) if opened else "none")
    except SubIssuesUnreadable:
        sub = "Sub-issues opened: unknown (the tracker could not be asked)"
    counts_line = (f"Counts: {counts['met']} met, {counts['unmet']} unmet, "
                   f"{counts['abandoned']} abandoned of {counts['total']}")
    parts = [first, "", branch_line, ""]
    for item in criteria:
        parts.append(criterion_block(item))
        for abandon in abandons:
            if abandon["ac"] == item["id"]:
                reason = abandon["reason"]
                parts.append(f"ABANDON: {abandon['ac']} {abandon['kind']}"
                             + (f" {reason}" if reason else ""))
        parts.append("")
    parts += [
        outside, "",
        f"skipped: {FILL}", "",
        sub, "",
        counts_line, "",
        "Decisions I made on my own", "",
        FILL, "",
    ]
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"DRAFT: wrote {out_file}")
    return 0


def run_sub_issue(number: int, kind: str, path: Path) -> int:
    """Open a `needs-triage` sub-issue under this ticket, and record it on this ticket.

    The child's body opens with a line a person reads; which kind it is and where it
    came from is the `child.opened` event posted on this ticket, which is where the
    ticket's own fold finds its children. A child opened whose event could not be
    written exits 1 and says so: the child exists, and opening it again would make two.
    """
    if kind not in SUB_ISSUE_KINDS:
        return refuse(f"kind `{kind}` is not one of {', '.join(SUB_ISSUE_KINDS)}")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not text.strip():
        return refuse(f"{path} is empty")
    title = text.strip().splitlines()[0].strip()
    posted = f"SUB-ISSUE {kind} from #{number}\n" + text
    if not posted.endswith("\n"):
        posted += "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(posted)
        body_path = fh.name
    try:
        result = subprocess.run(
            ["gh", "issue", "create",
             "--parent", str(number),
             "--label", "needs-triage",
             "--title", title,
             "--body-file", body_path],
            capture_output=True, text=True, check=False, env=GH_ENV,
        )
    finally:
        os.unlink(body_path)
    if result.returncode != 0:
        sys.stderr.write((result.stderr or result.stdout or "gh issue create failed").rstrip() + "\n")
        return 2
    printed = (result.stdout or "").strip()
    found = re.search(r"/issues/(\d+)", printed)
    recorded = 0
    if not found:
        sys.stderr.write(f"opened a sub-issue of #{number} but `gh issue create` printed no "
                         f"issue number ({printed[:80] or 'nothing'}), so no child.opened "
                         f"event was written on #{number}; do not open it again\n")
        recorded = 1
    else:
        child = int(found.group(1))
        try:
            post_event(number, "child.opened", f"Opened #{child} ({kind}): {title}",
                       child=child, kind=kind, title=title)
        except (OSError, subprocess.CalledProcessError) as exc:
            sys.stderr.write(f"opened #{child} under #{number}, but the child.opened event "
                             f"on #{number} was not written ({exc}); do not open it again\n")
            recorded = 1
    print(found.group(1) if found else printed)
    return recorded


# ----------------------------------------------------------------- subcommands

def run_checks(number: int, reverify: bool, timeout: int | None) -> int:
    body = fetch_body(number)
    require_judges(body)
    root = repo_root()
    carried = carried_ledger(number, body) if reverify else []
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp), carried or None)
        cmd = ["node", str(GATE_CHECK), "--cwd", str(root)]
        if reverify:
            cmd.append("--reverify")
        cmd += ["--timeout", str(check_timeout(body, timeout))]
        cmd.append(str(ledger))
        env = os.environ.copy()
        env["MMW_TICKET"] = str(number)
        if TOOLS:
            env["PATH"] = os.pathsep.join([str(d) for d in TOOLS] + [env.get("PATH", "")])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        sys.stdout.write(printed)
        if result.returncode == 2:
            return 2
        summary = [line for line in printed.splitlines() if SUMMARY_RE.match(line)]
        updated = ledger.read_text(encoding="utf-8").rstrip("\n")

    comment = "\n".join([
        "reverify" if reverify else "self-run",
        *summary,
        "",
        updated,
        "",
        outside_owns_line(number, owns_globs(body), root),
    ])
    post_prose(number, comment)
    return result.returncode


def refusals(number: int, ticket: dict, me: str, branch: str,
             dirty: list[str]) -> list[tuple[str, str]]:
    """Why this ticket is not ready to be worked on, in the order a worker would hit it.

    Each refusal is `(reason, sentence)`: the reason is the `ticket.refused` event's
    `reason` field, one of `events.REFUSALS`, and the sentence is its first line.

    Every one of these ends in `stop`. The six conditions are set up before a worker
    exists — `dispatch.sh` opens the worktree on `issue-<n>` and checks the state, the
    labels and the blockers before it starts anyone — so a worker that sees one of these
    has found a fault upstream of itself, not a task. Working around it (switching
    branches, committing whatever is in the tree, taking someone else's ticket) does more
    damage than stopping. The comment this posts on the ticket is what the user reads in
    the morning.
    """
    out = []
    if branch != f"issue-{number}":
        out.append(("wrong-branch",
                    f"NOT_READY: branch is {branch or '(detached)'}, not issue-{number}; "
                    f"dispatch opens this worktree on issue-{number}, so you were started "
                    f"somewhere else — stop, do not switch branches yourself"))
    if dirty:
        out.append(("dirty-tree",
                    f"NOT_READY: {len(dirty)} tracked files already have uncommitted changes "
                    f"before any work started; they are not yours to commit or discard — "
                    f"stop and leave the tree as you found it"))
    state = ticket.get("state", "")
    if state != "OPEN":
        out.append(("not-open",
                    f"NOT_READY: #{number} is {state or 'unreadable'}, not OPEN; "
                    f"nothing for you to do here — stop, this comment is the record"))
    labels = [label.get("name", "") for label in ticket.get("labels", [])]
    if "ready-for-agent" not in labels:
        out.append(("not-ready",
                    f"NOT_READY: #{number} has no ready-for-agent label, so it has not been "
                    f"cleared for an agent yet; stop and leave it to whoever triages it"))
    blockers = [b for b in ticket.get("blockedBy", {}).get("nodes", [])
                if b.get("state") != "CLOSED"]
    if blockers:
        names = ", ".join(f"#{b['number']}" for b in blockers)
        out.append(("blocked",
                    f"NOT_READY: #{number} is blocked by {names}; stop — `dispatch.sh` "
                    f"starts this ticket again once those close, so do not wait or retry"))
    holders = [a.get("login", "") for a in ticket.get("assignees", [])]
    others = [h for h in holders if h != me]
    if others:
        out.append(("claimed-by-other",
                    f"NOT_READY: #{number} is assigned to {', '.join(others)}, not you ({me}); "
                    f"stop rather than work on someone else's ticket"))
    return out


def run_preflight(number: int) -> int:
    """Claim the ticket, or say on the ticket itself why it cannot be claimed.

    Either way one event lands on the ticket: `ticket.refused` with the first refusal's
    reason, or `ticket.claimed` once the claim is made. A claim whose event could not be
    written still holds — the tracker's assignee is the claim — and says so on stderr.
    """
    root = repo_root()
    ticket = fetch_ticket(number)
    me = gh_login()
    branch = current_branch(root)
    problems = refusals(number, ticket, me, branch, dirty_tracked(root))
    if problems:
        reason, sentence = problems[0]
        # The refusing session is named so its own hold ends with this event and the
        # ticket is free for the next start; a session that cannot name itself ends none.
        runner, session = own_session() or (None, None)
        post_event(number, "ticket.refused", sentence, spec=spec_field(ticket),
                   reason=reason, branch=branch or None, runner=runner, session=session)
        sys.stderr.write(sentence + "\n")
        return 2
    assign_self(number)
    try:
        post_event(number, "ticket.claimed", f"Claimed #{number} on {branch} as {me}",
                   spec=spec_field(ticket), login=me, branch=branch,
                   commit=git("rev-parse", "HEAD", cwd=root) or None)
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"#{number} is claimed, but its ticket.claimed event was not "
                         f"written ({exc})\n")
    print(f"READY: #{number} claimed on issue-{number}")
    return 0


ROW_ID_RE = re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+\b")


def review_problems(draft: str, body: str, comments: list[str]) -> list[str]:
    """A `Missing` the Spec axis raised against a screen-contract row the ticket owns is
    settled by a commit or a sub-issue the draft names; a draft silent on it is refused.
    The row id is the handle: the reviewer writes it first, the draft repeats it."""
    m = SCREEN_CONTRACT_ROWS_RE.search("\n".join(section(body, "Read first")))
    if not m:
        return []
    rows = set(ROW_ID_RE.findall(m.group(1)))
    review = (events.newest(comments, "reviewer.reported") or {}).get("body")
    if not review:
        return []
    spec_axis = re.split(r"^## Tests", review, maxsplit=1, flags=re.M)[0]
    spec_axis = re.split(r"^## Spec", spec_axis, maxsplit=1, flags=re.M)[-1]
    problems = []
    for line in spec_axis.splitlines():
        if not re.search(r"Missing|缺失", line) and not re.search(r"^\s*\d+\.\s", line):
            continue
        for rid in ROW_ID_RE.findall(line):
            if rid in rows and rid not in draft:
                problems.append(f"the review's Spec axis reports a `Missing` against "
                                f"screen-contract row {rid} and the draft names no commit "
                                f"or sub-issue for it")
    return problems


CHECKS_TAIL = 20


class TargetJsonChecksError(Exception):
    """`.mmw/target.json` is present and names `checks`, but the file cannot be read
    as the list of commands the gate expects."""


def target_json_checks(root: Path | None) -> list[tuple[str, int]] | None:
    """The `checks` of `.mmw/target.json` as `(command, timeout)` pairs — an entry is a
    string, held to `DEFAULT_TIMEOUT`, or `{"run": …, "timeout": …}` naming its own
    bound in seconds — or None when the key is absent —
    the closeout then behaves as it did before the key existed. `--reverify` and
    `--lint` never read this. A file that names `checks` but is not a JSON object
    with a list raises `TargetJsonChecksError` rather than looking like absence."""
    if root is None:
        return None
    path = Path(root) / ".mmw" / "target.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetJsonChecksError(f"{path} is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise TargetJsonChecksError(f"{path} is not an object")
    if "checks" not in data:
        return None
    raw = data["checks"]
    if not isinstance(raw, list):
        raise TargetJsonChecksError(f"{path} `checks` is not a list")
    commands: list[tuple[str, int]] = []
    for entry in raw:
        if isinstance(entry, str):
            commands.append((entry, DEFAULT_TIMEOUT))
            continue
        if isinstance(entry, dict) and isinstance(entry.get("run"), str):
            timeout = entry.get("timeout", DEFAULT_TIMEOUT)
            if not isinstance(timeout, int) or timeout <= 0:
                raise TargetJsonChecksError(
                    f"{path} `checks` entry {entry['run']!r}: `timeout` must be a positive integer")
            commands.append((entry["run"], timeout))
            continue
        raise TargetJsonChecksError(
            f"{path} `checks` entry {entry!r} is neither a string nor {{\"run\": …, \"timeout\": …}}")
    return commands


def run_target_json_checks(root: Path | None) -> tuple[bool, str]:
    """Run each `checks` command at the repository root, in order.

    Returns `(True, "")` when the key is absent; `(True, "CHECKS OK n/n\\n")` when
    every command exited 0; `(False, body)` when any did not — `body` starts with
    `CHECKS FAILED` and, for each failed command, the command and its last
    `CHECKS_TAIL` lines of output. A malformed file is a failure, not absence.
    A string entry is held to `DEFAULT_TIMEOUT`, the same bound as a `CHECK:`; an
    entry written as `{"run": …, "timeout": …}` is held to its own.
    """
    try:
        commands = target_json_checks(root)
    except TargetJsonChecksError as exc:
        return False, f"CHECKS FAILED\n{exc}\n"
    if commands is None:
        return True, ""
    failed: list[tuple[str, str]] = []
    for command, bound in commands:
        try:
            proc = subprocess.run(command, shell=True, cwd=root, capture_output=True,
                                  text=True, timeout=bound)
        except subprocess.TimeoutExpired as exc:
            combined = (exc.stdout or "") + (exc.stderr or "")
            if isinstance(combined, bytes):
                combined = combined.decode("utf-8", "replace")
            tail = "\n".join(str(combined).splitlines()[-CHECKS_TAIL:])
            note = f"timed out after {bound}s"
            failed.append((command, f"{note}\n{tail}".strip() if tail else note))
            continue
        except OSError as exc:
            failed.append((command, str(exc)))
            continue
        if proc.returncode != 0:
            combined = (proc.stdout or "") + (proc.stderr or "")
            tail = "\n".join(combined.splitlines()[-CHECKS_TAIL:])
            failed.append((command, tail))
    if failed:
        lines = ["CHECKS FAILED"]
        for command, tail in failed:
            lines.append(command)
            if tail:
                lines.append(tail)
        return False, "\n".join(lines) + "\n"
    return True, f"CHECKS OK {len(commands)}/{len(commands)}\n"


def run_closeout(number: int, draft_path: Path, check_only: bool) -> int:
    """Check the closing comment against the ticket and the repository, then post it."""
    draft = draft_path.read_text(encoding="utf-8")
    comments = fetch_comments(number)
    body = fetch_body(number)
    problems = draft_problems(draft, comments)
    problems += verified_problems(draft, body, comments)
    problems += review_problems(draft, body, comments)
    problems += event_problems(comments)
    problems += git_problems(repo_root())
    ticket = fetch_ticket(number)
    me = gh_login()
    first = (draft.strip().splitlines() or [""])[0].strip()
    # A previous run of this closeout that closed (or handed back) the ticket and could not
    # post the event: this run posts it, and does nothing else.
    pending = unannounced_change(ticket, comments, me, first)
    if ticket.get("state") != "OPEN" and pending != "closed":
        problems.append(f"#{number} is already {ticket.get('state', 'unreadable')}")
    if pending is None and not any(a.get("login") == me for a in ticket.get("assignees", [])):
        problems.append(f"#{number} is not assigned to you ({me}); run --preflight first")

    if problems:
        # The first line carries the total and the command that prints the rest, so a
        # worker sees the whole set at once. A refusal that named only the problem it hit
        # first would put it in a loop nobody has a cap on: fix one, run again, meet the
        # next.
        rest = (f" Run `verify-ticket.py {number} --closeout {draft_path} --check-only` "
                f"to see the other {len(problems) - 1}." if len(problems) > 1 else "")
        sys.stderr.write(f"closeout rejected, {len(problems)} problem"
                         f"{'s' if len(problems) > 1 else ''}: {problems[0]}{rest}\n")
        for problem in problems[1:]:
            sys.stderr.write("also: " + problem + "\n")
        return 1
    if check_only:
        print(f"CLOSEOUT OK: #{number} draft passes every check")
        return 0

    if first == "ALL MET" and pending is None:
        ok, extra = run_target_json_checks(repo_root())
        if not ok:
            post_prose(number, extra)
            sys.stderr.write(extra.splitlines()[0] + "\n")
            return 1
        if extra:
            draft = draft.rstrip("\n") + "\n" + extra

    # The draft is the comment: its first line for a person, the rest as written, and the
    # event block after it. `abandoned` carries every `ABANDON:` line — on a pass only
    # `decision` ones can be there, on a hand back they are the reason it came back.
    abandons = parse_abandons(draft)
    passed = first == "ALL MET"
    event = "ticket.passed" if passed else "ticket.returned"
    fields = dict(spec=spec_field(ticket), commit=git("rev-parse", "HEAD") or None,
                  branch=current_branch(repo_root()) or None,
                  counts=tally(parse_criteria(draft), abandons),
                  abandoned=[{"ac": a["ac"], "kind": a["kind"], "reason": a["reason"]}
                             for a in abandons] or None)
    # The state change first, then the event that announces it: the event is what wakes
    # the main agent and what `advance` merges on, so it must never stand on a ticket the
    # tracker did not close or hand back.
    if pending is None:
        try:
            if passed:
                close_ticket(number)
            else:
                hand_back_for_triage(number)
        except (OSError, subprocess.CalledProcessError) as exc:
            act = "close" if passed else "hand back to needs-triage"
            sys.stderr.write(f"closeout refused: the tracker did not {act} #{number} ({exc}), so "
                             f"no {event} event was posted and nothing reads the ticket as "
                             f"{'passed' if passed else 'returned'}. Read #{number} on the "
                             f"tracker for what the edit left done, then run --closeout again\n")
            return 1
    try:
        post_event(number, event, first,
                   "\n".join(draft.strip("\n").splitlines()[1:]).strip("\n"), **fields)
    except (OSError, subprocess.CalledProcessError) as exc:
        done = "closed" if passed else "handed back to needs-triage"
        sys.stderr.write(f"closeout incomplete: #{number} is {done}, and its {event} event could "
                         f"not be posted ({exc}), so nothing wakes the main agent and nothing "
                         f"reads the ticket as {'passed' if passed else 'returned'} yet. Run "
                         f"--closeout again with the same draft: it sees the {done} ticket and "
                         f"posts the missing event\n")
        return 1
    note = f" (posted the {event} event a previous run could not)" if pending else ""
    if passed:
        print(f"CLOSED: #{number}{note}")
    else:
        print(f"HANDED BACK: #{number} is now needs-triage and stays open{note}")
    return 0


def run_verdict(number: int, line: str, model: str) -> int:
    """Post the verifier's verdict on HEAD: `verifier.passed` or `verifier.failed`.

    The verifier writes one line and names its model; which of the two events it is,
    and the commit it covers, are read here rather than typed. A line opening `could not
    start` is a failure whose criteria never ran. Otherwise the verifier's own newest
    `reverify` run decides: `ALL MET` is a pass, anything else a failure naming the
    criteria it left unmet — so a verdict can never say more than the run it reports.
    """
    line = " ".join((line or "").split())
    if not line:
        return refuse("--verdict needs the one line that says what the run proved")
    if not (model or "").strip():
        return refuse("--verdict needs --model, the model this verifier runs on")
    commit = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        return refuse("could not read HEAD, so there is no commit for the verdict to cover")
    reverify = last_reverify(fetch_comments(number))
    ran = not line.lower().startswith("could not start")
    if ran and reverify is None:
        return refuse(f"#{number} carries no `reverify` comment, so there is no run for this "
                      f"verdict to report. Run --reverify first; if it could not start, "
                      f"say `could not start` in the line")
    summary = run_summary(reverify) if ran else None
    passed = bool(summary and summary.startswith("ALL MET"))
    post_event(number, "verifier.passed" if passed else "verifier.failed",
               f"VERDICT {commit} by {model.strip()} — {line}",
               commit=commit, model=model.strip(), says=line, ran=ran,
               failed=(run_unmet(reverify) if ran and not passed else None) or None)
    print(f"VERDICT: {'passed' if passed else 'failed'} on {commit[:12]}, posted on #{number}")
    return 0


def lint_ticket_graph(number: int, body: str) -> int:
    """Read the batch this ticket belongs to and check it is a startable graph."""
    try:
        spec = spec_of(number)
    except ParentUnreadable as exc:
        print(f"  ERROR the tracker could not say which spec #{number} sits under "
              f"({exc}), so the batch graph was not checked  [parent-unreadable]")
        return 1
    if spec is None:
        print("ticket graph: no parent link and no spec in `## Parent`, so there is "
              "no batch to check")
        return 0
    try:
        numbers = fetch_sub_issues(spec)
    except SubIssuesUnreadable as exc:
        print(f"  ERROR the tracker could not list the children of #{spec} "
              f"({exc}), so the batch graph was not checked  [sub-issues-unreadable]")
        return 1
    return lint_batch_graph(spec, numbers)


def lint_batch_graph(spec: int, numbers: list[int]) -> int:
    """Check that `numbers`, the sub-issues of `spec`, form a startable graph."""
    if not numbers:
        print(f"  ERROR #{spec} has no sub-issues — publish tickets as sub-issues of the "
              f"spec, or the graph cannot be checked  [no-sub-issues]")
        return 1
    entries = ticket_entries(numbers)
    # Printed before the errors, because an error returns here and a disagreement about
    # an edge is often what the error is: a cycle, or a blocker that is no ticket.
    for finding in cross_batch_findings(entries):
        print("  WARN  " + finding + "  [cross-batch]")
    inside = in_batch(entries)
    errors = blockers_not_tickets(entries) + validate_dag(inside)
    if errors:
        # The start levels stay unprinted on purpose. What reaches here is a cycle, a
        # duplicate, or a blocker that is no ticket, and none of the three has levels to
        # print: Kahn's algorithm drains none of them, so the table would come out
        # missing exactly the tickets the error is about.
        for error in errors:
            print("  ERROR " + error)
        return 1
    levels = compute_levels(inside)
    by_level = defaultdict(list)
    for ticket, level in levels.items():
        by_level[level].append(ticket)
    for level in sorted(by_level):
        print(f"level {level}: " + ", ".join(f"#{t}" for t in sorted(by_level[level])))
    for line in waiting_outside(entries):
        print(line)
    return 0


def criteria_lines(body: str) -> list[tuple[str, str, str]]:
    """`(id, CHECK, EXPECT)` per criterion; a missing attribute reads as an empty string."""
    return [(c["id"], c["check"], c["expect"])
            for c in parse_criteria("\n".join(section(body, "Acceptance criteria")))]


def lint_worker(labels: list[str]) -> list[str]:
    """Which worker this ticket gets, as the tracker's labels say.

    `dispatch.sh` reads the label and nothing else, so a ticket carrying none is worked by
    whichever worker the default is rather than the one it was written for, and one carrying
    both is a ticket no start can place.

    A ticket outside the agent queue is clean either way: what it holds is one thing for the
    user to look at, and no worker is started on it.
    """
    if "ready-for-agent" not in labels:
        return []
    marked = sorted(name for name in labels if WORKER_LABEL_RE.match(name or ""))
    if len(marked) > 1:
        return [f"carries {len(marked)} worker labels ({', '.join(marked)}), and it takes one"]
    if not marked:
        return ["carries no worker label: add `junior-worker` or `senior-worker`, so "
                "every start puts it on the row it was written for"]
    return []


def lint_expectations(body: str) -> list[str]:
    """`$` in an EXPECT regex without the `m` flag is a criterion that can never pass.

    gate-check hands the CHECK's whole output — stdout, then stderr — to the regex
    (`gate-check.mjs:586`), and a command's output ends in a newline. JavaScript's `$`
    does not match the position before that newline, so `/OK$/` never matches the `OK`
    a passing test run prints.
    """
    findings = []
    for gate_id, _, expect in criteria_lines(body):
        m = REGEX_EXPECT_RE.match(expect)
        if not m:
            continue
        source, flags = m.group(1), m.group(2)
        if UNESCAPED_DOLLAR_RE.search(source) and "m" not in flags:
            head = source if source.startswith("^") else "^" + source
            anchored = "/" + head.rstrip("$") + "$/" + flags + "m"
            findings.append(
                f"{gate_id}: EXPECT {expect} ends at `$` without the `m` flag, and a "
                f"CHECK's output ends in a newline, so `$` never matches. Write "
                f"{anchored} to match that text as a whole line.")
    return findings


def lint_timeouts(body: str) -> list[str]:
    """A `TIMEOUT:` that is not a positive whole number of seconds is a criterion whose
    limit nobody can read."""
    findings = []
    for criterion in parse_criteria("\n".join(section(body, "Acceptance criteria"))):
        value = criterion["timeout"]
        if value and not (value.isdigit() and int(value) > 0):
            findings.append(f"{criterion['id']}: TIMEOUT is `{value}`; write a whole "
                            f"number of seconds greater than zero, such as `TIMEOUT: 1200`")
    return findings


def lint_check_effects(body: str) -> list[str]:
    """Which criteria leave the repository or the ticket somewhere new.

    Every CHECK runs in its own shell, so a `cd` reaches nobody else, but the branch,
    the ticket and the working tree are shared: gate-check runs the criteria one at a
    time in ledger order (`--jobs` defaults to 1), and `--reverify` runs them all a
    second time. A criterion that changes shared state has to set up what it needs and
    put back what it changed, or the criteria after it — and its own second run — start
    somewhere its author never saw.
    """
    findings = []
    for gate_id, check, _ in criteria_lines(body):
        m = STATEFUL_COMMAND_RE.search(check)
        if m:
            findings.append(
                f"{gate_id}: CHECK runs `{m.group(0)}`, which the criteria after it and "
                f"its own --reverify run all inherit. Set up what it needs and put back "
                f"what it changes.")
    return findings


SCREEN_CONTRACT_ROWS_RE = re.compile(r"screen-contract\.yaml\s+rows?:\s*([^\n]+)")
FETCH_STUB_RE = re.compile(r"stubGlobal\(\s*['\"]fetch['\"]|msw|nock\(|fetch-mock", re.IGNORECASE)
FLAG_RE = re.compile(r"(?<!\S)(--[a-z][a-z0-9-]*)")
# The scripts of this pipeline a criterion may run, and what each call must carry: the flags
# it cannot leave out, and the ones that have been retired. `lint_pipeline_flags` reads it, so a
# script that takes no flags at all has nothing to assert here and is left out of it, which is
# why this holds fewer scripts than `JUDGES` below does.
# Their addresses come from the repository's `.mmw/target.json`, never from the line.
PIPELINE_SCRIPTS = {
    "story-parity.py": {"required": ("--contract", "--pages"),
                        "retired": ("--baseline", "--impl", "--cdp", "--backend", "--seed",
                                    "--impl-title", "--viewports", "--mount")},
    "boundary-check.py": {"required": ("--run",), "retired": ()},
}
# The judges of the `drive-target` skill: every script a `CHECK:` names by its bare name and
# that `require_judges` refuses a run for when the shell could not find it. The default place
# looked at is that skill's `scripts/`, resolved in `main()`; `--tools` overrides it.
JUDGES = ("story-parity.py", "boundary-check.py", "journey.py", "harness-guard.py")
SPEC_SECTION_SOURCE_RE = re.compile(r"^#(\d+) (Implementation Decisions|Testing Decisions)\s*(\d+)?")
ADR_SOURCE_RE = re.compile(r"^ADR-(\d{4})")
TICKET_SOURCE_RE = re.compile(r"^#(\d+)(?:\s|$)")
DOC_SOURCE_RE = re.compile(r"^(docs/\S+)")
STORY_SOURCE_RE = re.compile(r"^#\d+ story \d+")
_HELP_FLAGS: dict[str, set[str]] = {}
# Where the scripts other skills own are found: the `drive-target` skill's `scripts/` by
# default, or the directories `--tools` named instead. A `CHECK:` names a judge by its bare
# name (`story-parity.py …`), and this process puts these directories on the PATH of the
# shell that runs it. Nothing here looks for such a script by any other route.
TOOLS: list[Path] = []


def tool(script: str) -> Path | None:
    for directory in TOOLS:
        candidate = directory / script
        if candidate.is_file():
            return candidate
    return None


class JudgeUnreachable(RuntimeError):
    """A `CHECK:` names one of the judges and no directory in force holds it."""


def require_judges(body: str) -> None:
    """Refuse, before anything runs, when a criterion names a judge this run cannot reach.

    Without the directory, the criterion fails `command not found`, which reads exactly
    like a criterion that ran and did not pass: gate-check records it as one more unmet
    gate and this run exits 1. On 2026-09-08 `dispatch.sh reverify` was found running
    with no `--tools` at all, which would have reopened and handed back every interface
    ticket of a batch for a fault in the invocation. So the run stops here instead,
    names the script, and writes nothing to the ticket.

    `PATH` is the second place looked at: a directory put there by hand is a legitimate
    way to reach the judges, and refusing it would refuse something that works.
    """
    missing = sorted({judge
                      for _, check, _ in criteria_lines(body)
                      for judge in JUDGES
                      if judge in check
                      and tool(judge) is None and shutil.which(judge) is None})
    if missing:
        raise JudgeUnreachable(
            ", ".join(missing) + ": named by a `CHECK:` and in none of the directories "
            "this run searched and not on PATH. Nothing was run and nothing was written. Pass "
            "--tools <a directory holding it> and run again.")


APP_PAGE_PREFIX = "App · "
RUN_VALUE_RE = re.compile(r"""--run(?:\s+|=)(?:"([^"]*)"|'([^']*)'|(\S+))""")
JOURNEY_NAME_RE = re.compile(r"^\s*run\s+(\S+)")
CD_PREFIX_RE = re.compile(r"^\s*cd\s+(\S+)\s*&&")


OPERATOR_RE = re.compile(r"(?:&&|\|\||;|\|)(?:\s|$)")


def script_segment(check: str, script: str) -> str:
    """The part of a CHECK from the script's name to the end of that command.

    An operator inside a quoted value belongs to the command that value carries, not
    to the shell reading this line, so the end of the command is looked for outside
    the quotes."""
    i = check.find(script)
    if i < 0:
        return ""
    rest = check[i + len(script):]
    quote = ""
    for j, ch in enumerate(rest):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif OPERATOR_RE.match(rest, j):
            return rest[:j].rstrip()
    return rest


def segment_flags(segment: str) -> set[str]:
    """The flags of the judge's own command line.

    `--run` carries a whole command as its value, and that command has flags of its
    own (`pnpm --dir desktop-chameleon exec vitest run …`). The shell hands a quoted
    value to the judge as one word, so the words are cut the way the shell cuts them
    and only a word that is itself a flag is read; a line whose quotes do not balance
    is cut on whitespace instead, which is what this did before shell words."""
    try:
        words = shlex.split(segment)
    except ValueError:
        words = segment.split()
    out: set[str] = set()
    for word in words:
        m = FLAG_RE.match(word)
        if m:
            out.add(m.group(1))
    return out


PAGES_VALUE_RE = re.compile(r"""--pages(?:\s+|=)(?:"([^"]*)"|'([^']*)'|(\S+))""")


def flag_values(segment: str, pattern: re.Pattern) -> list[str]:
    """Every value `pattern` matches in `segment`, double-quoted, single-quoted or bare.

    The three alternatives are one capture group each, so which one carried the value
    is the caller's question in every flag regex here; asking it once is the point."""
    out: list[str] = []
    for m in pattern.finditer(segment):
        out.append(m.group(1) if m.group(1) is not None
                   else m.group(2) if m.group(2) is not None
                   else m.group(3) or "")
    return out


def story_mounts(check: str) -> list[str]:
    """The `--pages` mounts a story-parity.py criterion names."""
    segment = script_segment(check, "story-parity.py")
    out: list[str] = []
    for raw in flag_values(segment, PAGES_VALUE_RE):
        out.extend(x for x in raw.split(",") if x)
    return out


def page_mounts(doc: dict) -> dict[str, str]:
    """`pages.<page>.mount` → the page key."""
    out: dict[str, str] = {}
    for name, decl in (doc.get("pages") or {}).items():
        mount = str((decl or {}).get("mount") or "")
        if mount:
            out[mount] = str(name)
    return out


def run_values(check: str) -> list[str]:
    """The `--run` values on a boundary-check.py criterion; empty when that script is absent."""
    if "boundary-check.py" not in check:
        return []
    segment = script_segment(check, "boundary-check.py")
    values = flag_values(segment, RUN_VALUE_RE)
    if "--run" in segment and not values:
        return [""]
    return values


def help_flags(script: str) -> set[str]:
    """The flags the installed script actually accepts, read from its `--help` once.
    This is the one place a criterion's reference to a capability that does not exist
    yet is caught at the moment it is written."""
    if script not in _HELP_FLAGS:
        path = tool(script)
        text = ""
        if path is not None:
            try:
                out = subprocess.run([sys.executable, str(path), "--help"], capture_output=True,
                                     text=True, timeout=60)
                text = (out.stdout or "") + (out.stderr or "")
            except (OSError, subprocess.TimeoutExpired):
                text = ""
        _HELP_FLAGS[script] = set(FLAG_RE.findall(text))
    return _HELP_FLAGS[script]


def lint_pipeline_flags(gate_id: str, check: str) -> list[str]:
    findings = []
    for script, rules in PIPELINE_SCRIPTS.items():
        if script not in check:
            continue
        flags = segment_flags(script_segment(check, script))
        for flag in rules["required"]:
            if flag not in flags:
                findings.append(f"{gate_id}: {script} without {flag}")
        for flag in rules["retired"]:
            if flag in flags:
                findings.append(f"{gate_id}: {script} names {flag}; addresses and the seed "
                                f"come from .mmw/target.json and the contract, not the line")
        known = help_flags(script)
        if known:
            for flag in sorted(flags - known - set(rules["retired"])):
                findings.append(f"{gate_id}: {script} does not accept {flag} (its --help "
                                f"does not list it)")
    return findings


def parent_sections(parent_text: str) -> dict[int, dict]:
    """Per spec named in `## Parent`: the Implementation Decisions section numbers and
    whether Testing Decisions is named, in either the English or the Chinese shape."""
    out: dict[int, dict] = {}
    for m in re.finditer(r"#(\d+)(.*?)(?=#\d+|$)", parent_text, re.S):
        spec, seg = int(m.group(1)), m.group(2)
        entry = out.setdefault(spec, {"sections": set(), "testing": False})
        idm = re.search(r"Implementation Decisions[^\d#]{0,12}((?:\d+[^\d#]{0,6})+)", seg)
        if idm:
            entry["sections"].update(int(n) for n in re.findall(r"\d+", idm.group(1)))
        if "Testing Decisions" in seg:
            entry["testing"] = True
    return out


def load_yaml_file(path: str) -> dict | None:
    """The file as a mapping. `pyyaml` when this interpreter has it; else through `uv`,
    which every `CHECK:` of this pipeline already relies on; else `None`, and the caller
    says so rather than passing a rule it could not run."""
    try:
        import yaml  # noqa: PLC0415
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass
    except OSError:
        return None
    try:
        out = subprocess.run(
            ["uv", "run", "--with", "pyyaml", "python", "-c",
             "import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], "
             "encoding='utf-8')) or {}))", path],
            capture_output=True, text=True, timeout=120, env=GH_ENV)
        if out.returncode == 0:
            return json.loads(out.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def load_contract_doc(read_first: str) -> tuple[dict | None, str | None]:
    m = re.search(r"([\w./-]*screen-contract\.yaml)", read_first)
    if not m:
        return None, None
    return load_yaml_file(m.group(1)), m.group(1)


def source_findings(row_ids: list[str], doc: dict, read_first: str, parent_text: str) -> list[str]:
    """Every baseline-class source of an owned row must be in `## Read first`; every
    spec-section source must be named by `## Parent`. A story reaches no worker and is
    reported as such."""
    findings = []
    rows = {str(r.get("id")): r for r in doc.get("rows") or []}
    parents = parent_sections(parent_text)
    seen: set[str] = set()
    for rid in row_ids:
        row = rows.get(rid)
        if row is None:
            continue
        for src in row.get("source") or []:
            src = str(src).strip()
            key = src
            m = SPEC_SECTION_SOURCE_RE.match(src)
            if m:
                spec, kind, num = int(m.group(1)), m.group(2), m.group(3)
                key = f"{spec} {kind} {num}"
                if key in seen:
                    continue
                seen.add(key)
                entry = parents.get(spec)
                if kind == "Testing Decisions":
                    if not (entry and entry["testing"]):
                        findings.append(f"row {rid} source `{src}`: `## Parent` does not name "
                                        f"#{spec} Testing Decisions")
                elif num and not (entry and int(num) in entry["sections"]):
                    findings.append(f"row {rid} source `{src}`: `## Parent` does not name "
                                    f"#{spec} Implementation Decisions section {num}")
                continue
            if STORY_SOURCE_RE.match(src):
                continue
            m = ADR_SOURCE_RE.match(src)
            if m:
                num = m.group(1)
                key = f"ADR-{num}"
                if key in seen:
                    continue
                seen.add(key)
                if f"ADR-{num}" not in read_first and f"/{num}-" not in read_first:
                    findings.append(f"row {rid} source `{src}`: ADR-{num} is not under "
                                    f"`## Read first`")
                continue
            m = TICKET_SOURCE_RE.match(src)
            if m:
                key = f"#{m.group(1)}"
                if key in seen:
                    continue
                seen.add(key)
                if not re.search(rf"#{m.group(1)}(?!\d)", read_first):
                    findings.append(f"row {rid} source `{src}`: {key} is not under "
                                    f"`## Read first`")
                continue
            m = DOC_SOURCE_RE.match(src)
            if m:
                path = m.group(1).rstrip("),;:")
                if path in seen:
                    continue
                seen.add(path)
                if path not in read_first:
                    findings.append(f"row {rid} source `{src}`: {path} is not under "
                                    f"`## Read first`")
    return findings


def lint_screen_contract(body: str, number: int | None = None,
                         root: Path | str | None = None) -> list[str]:
    """The interface rules of `to-tickets`, made mechanical.

    An interface ticket names its screen-contract rows under `## Read first`; each
    `--pages` mount is a non-`App · ` page of that contract; a `boundary-check.py --run`
    is a non-empty command; a `journey.py run <name>` exists under `.mmw/journeys/`
    unless this ticket's `## Owns` covers that directory;
    no `CHECK:` may stub the application's own network (`vi.stubGlobal('fetch')`, msw,
    nock, fetch-mock) — mocking the product's API client module is not that; the
    pipeline scripts are given what they need and nothing they retired; every
    baseline-class source of an owned row is under `## Read first` and every
    spec-section source is named by `## Parent`.
    """
    findings: list[str] = []
    repo = Path(root) if root is not None else repo_root()
    read_first = "\n".join(section(body, "Read first"))
    parent_text = "\n".join(section(body, "Parent"))
    owns = owns_globs(body)
    checks = criteria_lines(body)
    for gate_id, check, _ in checks:
        findings.extend(lint_pipeline_flags(gate_id, check))
        if FETCH_STUB_RE.search(check):
            findings.append(f"{gate_id}: CHECK stubs the application's own network; mock "
                            f"the product's API client module instead")
        for value in run_values(check):
            if not value.strip():
                findings.append(f"{gate_id}: boundary-check.py --run is empty")
                break
        # `journeys` is read from where the command will run, not from the repository
        # root: a criterion that drives journey.py against a fixture `cd`s into it first,
        # and the journey it names is under that directory's `.mmw/`.
        base, prefix = repo, ""
        cdm = CD_PREFIX_RE.search(check)
        if cdm:
            candidate = (repo / cdm.group(1)).resolve()
            if candidate.is_dir():
                base = candidate
                prefix = cdm.group(1).removeprefix("./").strip("/")
        for name in JOURNEY_NAME_RE.findall(script_segment(check, "journey.py")):
            if (base / ".mmw" / "journeys" / name).exists():
                continue
            # A ticket whose `## Owns` covers the directory is the ticket that creates
            # it, so it is absent until this ticket's own work lands. The rule asks
            # after a journey someone else was to have built.
            path = "/".join(p for p in (prefix, ".mmw", "journeys", name) if p)
            if any(glob_covers(g, path) for g in owns):
                continue
            findings.append(f"{gate_id}: journey.py run {name} is not under .mmw/journeys/")
    m = SCREEN_CONTRACT_ROWS_RE.search(read_first)
    interface_ticket = any("story-parity.py" in check for _, check, _ in checks)
    if not m:
        if interface_ticket:
            findings.append("interface ticket (a criterion runs story-parity.py) names no "
                            "`screen-contract.yaml rows: <id, id>` line under `## Read first`")
        return findings
    row_ids = ROW_ID_RE.findall(m.group(1))
    doc, contract_path = load_contract_doc(read_first)
    if doc is None and contract_path:
        findings.append(f"the contract {contract_path} could not be read from here (not in "
                        f"the working tree, or neither pyyaml nor uv is available); the "
                        f"source rules did not run")
    if doc is not None:
        mounts_of = page_mounts(doc)
        for gate_id, check, _ in checks:
            if "story-parity.py" not in check:
                continue
            for mount in story_mounts(check):
                page = mounts_of.get(mount)
                if page is None:
                    findings.append(f"{gate_id}: --pages {mount} is declared by no page "
                                    f"of the contract")
                elif page.startswith(APP_PAGE_PREFIX):
                    findings.append(f"{gate_id}: --pages {mount} names an App page; story "
                                    f"criteria cover Component pages")
        findings.extend(source_findings(row_ids, doc, read_first, parent_text))
    return findings


def lint_criteria(number: int, body: str, labels: list[str]) -> int:
    """Everything `--lint` says about one ticket's own text: its worker label, how its
    criteria are written, and the three criterion shapes. The batch graph is not here;
    `run_lint` checks that once per batch."""
    require_judges(body)
    worker_errors = lint_worker(labels)

    def report_worker() -> None:
        for finding in worker_errors:
            print(f"  ERROR #{number} " + finding + "  [worker-label]")

    # A `ready-for-human` ticket carries no criteria at all: what it holds is one thing
    # for the user to look at. gate-lint has nothing to say about it, and
    # saying "zero live gates" would report the ticket's correct shape as a fault.
    if not section(body, "Acceptance criteria"):
        print(f"#{number} carries no `## Acceptance criteria`, so only its worker label "
              f"and its place in the batch are checked")
        report_worker()
        return 1 if worker_errors else 0

    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp))
        result = subprocess.run(
            # No `--strict`: it fails the run on any warning, and a warning is the level
            # for findings the main agent weighs and may keep. The exit code says one thing —
            # there is an ERROR — which is what the read-back step converges on.
            ["node", str(GATE_LINT), str(ledger)],
            capture_output=True, text=True,
        )
    sys.stdout.write((result.stdout or "") + (result.stderr or ""))

    broken = lint_expectations(body)
    for finding in broken:
        print("  ERROR " + finding + "  [dollar-without-m]")
    bad_timeouts = lint_timeouts(body)
    for finding in bad_timeouts:
        print("  ERROR " + finding + "  [bad-timeout]")
    broken = broken + bad_timeouts
    contract_findings = lint_screen_contract(body, number)
    for finding in contract_findings:
        print("  ERROR " + finding + "  [screen-contract]")
    broken = broken + contract_findings
    for finding in lint_check_effects(body):
        print("  WARN  " + finding + "  [shared-state]")
    report_worker()
    return result.returncode or (1 if broken or worker_errors else 0)


def ticket_labels(number: int) -> list[str]:
    return labels_of(fetch_ticket(number))


def labels_of(ticket: dict) -> list[str]:
    return [label.get("name") or "" for label in ticket.get("labels") or []]


def run_lint(number: int) -> int:
    """`--lint` on a ticket lints that ticket and the graph of the batch it sits under.
    `--lint` on a spec — an issue with no `## Acceptance criteria`, no parent, and
    sub-issues — lints every one of those sub-issues, then the graph once. The night's
    pre-batch pass names the spec, so a spec number must not come back as a quiet 0."""
    body = fetch_body(number)
    if not section(body, "Acceptance criteria"):
        try:
            is_spec = spec_of(number) is None and bool(fetch_sub_issues(number))
        except ParentUnreadable as exc:
            print(f"  ERROR the tracker could not say whether #{number} sits under a spec "
                  f"({exc})  [parent-unreadable]")
            return 1
        except SubIssuesUnreadable as exc:
            print(f"  ERROR the tracker could not list the children of #{number} "
                  f"({exc})  [sub-issues-unreadable]")
            return 1
        if is_spec:
            return lint_spec(number)
    ticket_rc = lint_criteria(number, body, ticket_labels(number))
    graph = lint_ticket_graph(number, body)
    return 1 if (ticket_rc or graph) else 0


def lint_spec(spec: int) -> int:
    """Every sub-issue of the spec through `lint_criteria`, each under a line naming
    it, then the batch graph once. Exit 1 if any ticket or the graph has an ERROR."""
    numbers = fetch_sub_issues(spec)
    print(f"#{spec} is a spec with {len(numbers)} sub-issues; linting each, then the graph")
    failed: list[int] = []
    for child in numbers:
        ticket = fetch_ticket(child)
        print(f"\n## #{child} ({ticket.get('state') or 'state unknown'})")
        if lint_criteria(child, fetch_body(child), labels_of(ticket)):
            failed.append(child)
    print("\n## ticket graph")
    graph = lint_batch_graph(spec, numbers)
    if failed:
        print("  ERROR tickets with findings: " + ", ".join(f"#{n}" for n in failed))
    return 1 if (failed or graph) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ticket", type=int)
    parser.add_argument("--reverify", action="store_true",
                        help="re-run every criterion, including the ones already ticked")
    parser.add_argument("--lint", action="store_true",
                        help="audit how the criteria are written; runs no CHECK, posts no comment")
    parser.add_argument("--preflight", action="store_true",
                        help="claim the ticket, or refuse and say why on the ticket")
    parser.add_argument("--closeout", type=Path, metavar="DRAFT",
                        help="check this closing comment, then post it and close the ticket")
    parser.add_argument("--check-only", action="store_true",
                        help="with --closeout: check the draft and change nothing")
    parser.add_argument("--timeout", type=int, help="per-CHECK timeout in seconds")
    parser.add_argument("--decisions", type=Path, metavar="FILE",
                        help="post the two-section file as a DECISIONS comment")
    parser.add_argument("--touched", action="store_true",
                        help="comment TOUCHED BY on open siblings whose Owns covers a file")
    parser.add_argument("--draft", type=Path, metavar="OUT",
                        help="write the closing-comment skeleton to this file")
    parser.add_argument("--sub-issue", nargs=2, metavar=("KIND", "FILE"),
                        help="open a needs-triage sub-issue under this ticket")
    parser.add_argument("--review", type=Path, metavar="FILE",
                        help="post the review report on the ticket")
    parser.add_argument("--verdict", metavar="LINE",
                        help="post the verifier's verdict on HEAD, read off its newest reverify")
    parser.add_argument("--model", help="with --verdict: the model this verifier runs on")
    parser.add_argument("--tools", action="append", type=Path, default=[], metavar="DIR",
                        help="a directory holding scripts of other skills (the drive-target "
                             "skill's scripts/); put on the PATH of every CHECK; repeatable")
    args = parser.parse_args(argv)
    # The judges live in the `drive-target` skill, beside this one under `skills/`, so this
    # file's own location answers where they are and no caller has to know. `--tools`
    # overrides that for a run against a copy somewhere else.
    TOOLS[:] = ([d.resolve() for d in args.tools]
                or [HERE.parents[1] / "drive-target" / "scripts"])
    chosen = [name for name, on in
              (("--lint", args.lint), ("--reverify", args.reverify),
               ("--preflight", args.preflight), ("--closeout", args.closeout is not None),
               ("--decisions", args.decisions is not None), ("--touched", args.touched),
               ("--draft", args.draft is not None),
               ("--sub-issue", args.sub_issue is not None),
               ("--review", args.review is not None),
               ("--verdict", args.verdict is not None)) if on]
    if len(chosen) > 1:
        parser.error(f"{' and '.join(chosen)} are different jobs; pick one")
    if args.check_only and args.closeout is None:
        parser.error("--check-only belongs to --closeout")
    if args.model is not None and args.verdict is None:
        parser.error("--model belongs to --verdict")
    if args.verdict is not None:
        return run_verdict(args.ticket, args.verdict, args.model or "")
    if args.preflight:
        return run_preflight(args.ticket)
    if args.closeout is not None:
        if not args.closeout.is_file():
            parser.error(f"no draft at {args.closeout}")
        return run_closeout(args.ticket, args.closeout, args.check_only)
    if args.decisions is not None:
        if not args.decisions.is_file():
            parser.error(f"no file at {args.decisions}")
        return run_decisions(args.ticket, args.decisions)
    if args.touched:
        return run_touched(args.ticket)
    if args.draft is not None:
        return run_draft(args.ticket, args.draft)
    if args.sub_issue is not None:
        kind, file = args.sub_issue
        return run_sub_issue(args.ticket, kind, Path(file))
    if args.review is not None:
        if not args.review.is_file():
            parser.error(f"no file at {args.review}")
        return run_review(args.ticket, args.review)
    try:
        if args.lint:
            return run_lint(args.ticket)
        return run_checks(args.ticket, args.reverify, args.timeout)
    except JudgeUnreachable as exc:
        print(f"verify-ticket: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
