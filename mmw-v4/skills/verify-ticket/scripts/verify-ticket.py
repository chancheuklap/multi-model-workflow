#!/usr/bin/env python3
"""Run a ticket's acceptance criteria and post the result back to the ticket.

The ticket is the only state. A normal run reads the `## Acceptance criteria` and
`## Owns` sections fresh from the issue, writes them to a ledger, hands
that ledger to unlazy's `gate-check`, and posts the result back as one
`ticket.checked` event. Nothing is cached. The ledger is removed when the run
ends. Each run replaces `.scratch/criteria/<ticket>/`, and a failing criterion's
output is `<id>.log` in that directory.

Claim-time baseline checkouts run their optional executable `scripts/env setup <worktree>`
and `up <worktree>` before criteria, then `down <worktree>` before removal, including a
failed preparation. Each command runs from the target checkout root with its absolute path.
Preparation failures exit 2; cleanup failures are reported without blocking removal.
Repositories without `scripts/env` run unchanged and print no environment messages.
"""

from __future__ import annotations

import argparse
import fcntl
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict, deque
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    """A module beside this file."""
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# `events.py`: the event vocabulary and the fold. `issue_tree.py`: the tree of issues
# under a spec, read with one query.
events = _load("mmw_events", "events.py")
tree = _load("mmw_tree", "issue_tree.py")
GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"
GATE_LINT = HERE / "gate-check" / "gate-lint.mjs"
LEDGER_NAME = "AC.md"
GITHUB_TITLE_LIMIT = 256
# The summary line gate-check prints on its own stdout.
SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")
GATE_LINE_RE = re.compile(r"^- \[( |x|X)\] ([A-Za-z0-9][A-Za-z0-9._-]*):")
CAT_IN_TICKET_ITEM_RE = re.compile(
    r"^- (Standards|Spec|Tests|Correctness|UI) \[([^\]]+)\] (\S+):(\d+) — (.+?) — source: (.+)$")
IMPLEMENTATION_DECISION_HEADING_RE = re.compile(r"^###\s+(\d+)\.")
SUB_ISSUE_KINDS = events.CHILD_KINDS
FILL = "<fill>"
CLASS_LABELS = {
    "mmw:map": ("5319e7", "MMW kind: the map one discussion opened"),
    "mmw:spec": ("1d76db", "MMW kind: a spec, the container of one batch of tickets"),
    "mmw:ticket": ("0e8a16", "MMW kind: a ticket, one unit of work"),
    "mmw:child": ("c5def5", "MMW kind: a child issue a ticket opened"),
    "mmw:lesson": ("8e44ad", "做法上的问题，等复盘"),
    "mmw:problem": ("f1c40f", "不在任何票里的产品问题，或计划还没批的 issue"),
}
# The one of them `--lint` asks after by name: which number is a batch's container.
CLASS_SPEC = "mmw:spec"
# The other two label sets the mmw-mode skill's `references/github-issues.md` names: who a
# ticket is waiting on, and which `models.json` row starts its worker. Colour and
# description are defined once, here, for every label the pipeline puts on an issue;
# `ensure_label` creates whichever of them a repository lacks, the first time one is used.
QUEUE_LABELS = {
    "needs-triage": ("F9D0C4", "等你决定：只有主人能让它离开"),
    "ready-for-agent": ("FEF2C0", "已写清楚，可以直接派工人 AFK 跑"),
    "ready-for-human": ("BFDADC", "HITL 的活，不派工人"),
    "wontfix": ("ffffff", "This will not be worked on"),
}
GRADE_LABELS = {
    "junior-worker": ("C2E0C6", "worker grade: default row in models.json"),
    "senior-worker": ("E99695", "worker grade: silent-failure work"),
}
# A map and the type of each decision ticket under it, as the mmw-mode skill's
# `references/wayfinder.md` names them.
WAYFINDER_LABELS = {
    "wayfinder:map": ("BFDADC", "这张 issue 是一张 map，不是一件待办"),
    "wayfinder:research": ("FEF2C0", "decision ticket，开一个 researcher 查一条事实就能解掉"),
    "wayfinder:prototype": ("BFD4F2", "decision ticket，要先做一个粗糙版本给用户走查"),
    "wayfinder:grilling": ("D93F0B", "decision ticket，靠跟人对谈解掉"),
    "wayfinder:task": ("5319E7", "decision ticket，某个决定做得出来之前必须先完成的手工操作"),
}
LABELS = {**CLASS_LABELS, **QUEUE_LABELS, **GRADE_LABELS, **WAYFINDER_LABELS}
# A criterion is abandoned for one of three reasons. `failed` ran and did not pass;
# `stuck` never ran or cannot be done; the two are told apart for whoever reads the
# ticket in the morning, and both hand the ticket back. `decision` needs a person to
# choose, and is the only one that still closes. How many rounds a criterion gets is
# the worker's own judgement, said on the `ABANDON:` line.
ABANDON_KINDS = events.ABANDON_KINDS
HANDOFF_KINDS = ("failed", "stuck")
# Seconds one `CHECK:` may run. A ticket raises it per criterion with `TIMEOUT:`; the
# worker's own run and final `--reverify` read the same lines, so the two
# never disagree about it.
DEFAULT_TIMEOUT = 600
ABANDON_RE = re.compile(r"^ABANDON:\s+(\S+)\s+(\S+)\s*(.*)$")
# `owner/repo#n` and `repo#n` are another repository's issue, not this batch's spec.
ISSUE_REF_RE = re.compile(r"(?<![A-Za-z0-9_/])#(\d+)")
WORKER_LABEL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-worker$")
ATTR_LINE_RE = re.compile(r"^\s+(CHECK|EXPECT|EVIDENCE|TIMEOUT):")
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
# A `grep` — plain, `git grep`, `egrep`, `fgrep` — as the command whose exit code the
# CHECK hands back. GNU and BSD grep both exit 1 when they selected no line.
GREP_STAGE_RE = re.compile(r"^(?:git\s+)?[ef]?grep\b")
COUNT_FLAG_RE = re.compile(r"(?<!\S)(?:--count\b|-[A-Za-z]*c)")
# Both of the command's streams thrown away, in the four spellings a CHECK uses.
DISCARDS_BOTH_RE = re.compile(
    r">\s*/dev/null\s+2>\s*(?:&1|/dev/null)"
    r"|2>\s*/dev/null\s+>\s*/dev/null"
    r"|&>\s*/dev/null")
# An `echo` or `printf` of the exit code as the CHECK's last command.
ECHOED_EXIT_RE = re.compile(r"^(?:echo|printf)\b.*\$\?")


# ----------------------------------------------------------------- ticket text

# Under an exported CLICOLOR_FORCE=1, `gh` writes ANSI escapes into --json output, which
# json.loads cannot read. Every gh call here runs without it.
# `events.py`, loaded above, computes the same filter; this file shares its value rather
# than filtering `os.environ` a second time.
GH_ENV = events.GH_ENV


class TrackerReadError(RuntimeError):
    """A named tracker read that the caller may safely retry."""

    def __init__(self, number: int, part: str, detail: str):
        self.number = number
        self.part = part
        self.detail = detail
        super().__init__(f"could not read #{number}'s {part} from the tracker ({detail})")


def tracker_failure(exc: BaseException) -> str:
    """The useful line from a failed tracker subprocess or parser."""
    if isinstance(exc, subprocess.CalledProcessError):
        return gh_detail(exc)
    return str(exc)


def fetch_body(number: int) -> str:
    """The issue body, straight from the tracker. Patched out in tests."""
    try:
        out = subprocess.run(
            ["gh", "issue", "view", str(number), "--json", "body", "-q", ".body"],
            capture_output=True, text=True, check=True, env=GH_ENV,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise TrackerReadError(number, "body", tracker_failure(exc)) from None
    return out.stdout


def fetch_comments(number: int) -> list[str]:
    """Every comment body on the ticket, oldest first. Patched out in tests."""
    try:
        out = subprocess.run(
            ["gh", "issue", "view", str(number), "--json", "comments"],
            capture_output=True, text=True, check=True, env=GH_ENV,
        )
        return [c.get("body", "") for c in json.loads(out.stdout).get("comments", [])]
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError,
            AttributeError, TypeError) as exc:
        raise TrackerReadError(number, "comments", tracker_failure(exc)) from None


def post_comment(number: int, body: str) -> None:
    """One comment per run. Patched out in tests."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        path = fh.name
    try:
        subprocess.run(["gh", "issue", "comment", str(number), "--body-file", path], check=True, env=GH_ENV)
    finally:
        os.unlink(path)


def post_event(number: int, event: str, line: str, text: str = "",
               spec: int | None = None, **fields) -> str:
    """Post one event on ticket `number`: `line` for a person, the block for the fold.

    `spec` is the spec the ticket sits under; left out, it is looked up with
    `ticket_spec`, so no event goes out without one the tracker could have given.
    """
    if spec is None:
        spec = ticket_spec(number)
    body = events.build(event, ticket=number, spec=spec, line=line, text=text, **fields)
    post_comment(number, body)
    return body


def ticket_spec(number: int) -> int | None:
    """The spec an event about ticket `number` names: `spec_of`, or None when the tracker
    could not say. An event is written either way — the spec field is a reader's
    convenience, and an unwritten event is the loss that matters. Patched out in tests."""
    try:
        return spec_of(number)
    except (ParentUnreadable, subprocess.CalledProcessError, OSError, TrackerReadError):
        return None


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
    """Hand the unfinished ticket back for the owner's decision. Patched out in tests.

    `needs-triage` records that the owner decides the ticket's next step.

    A ticket still assigned to the worker that gave up is a ticket `status.py`'s
    frontier will not dispatch again — it takes only unassigned tickets — so the
    assignee comes off in the same edit as the label.
    """
    missing = ensure_label("needs-triage")
    if missing:
        raise OSError(f"the repository has no `needs-triage` label and it could not be "
                      f"created ({missing})")
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


def gh_detail(out) -> str:
    """The last line a failed `gh` call said, for the exception that carries it up.

    `gh` writes its reason on stderr and falls back to stdout; the last line is the
    one that names the failure, the rest being the request it was making. Takes a
    completed process or a `subprocess.CalledProcessError`, whichever carries it — both
    have `stderr`, `stdout` and `returncode`.
    """
    detail = str(out.stderr or out.stdout or "").strip().splitlines()
    return detail[-1] if detail else f"gh exited {out.returncode}"


class SubIssuesUnreadable(RuntimeError):
    """The tracker could not list the children of an issue.

    Distinct from an issue that has no children: that one is an empty list, this one
    means the question went unanswered.
    """


def fetch_tree(number: int, root: str = "spec") -> dict:
    """The tree of issues under `number`, an issue of layer `root`, in one query
    (`issue_tree.py`, which runs its own `gh` calls, filtered the same way this file's
    `GH_ENV` is). Raises `SubIssuesUnreadable` when the tracker could not answer for the
    whole of it. Patched out in tests."""
    try:
        return tree.read(number, root)
    except tree.TreeUnreadable as exc:
        raise SubIssuesUnreadable(str(exc)) from None


def fetch_sub_issues(number: int, root: str = "spec") -> list[int]:
    """The issues GitHub records as children of `number`, in its own order. Called with
    a spec, that is the batch; called with a ticket (`root="ticket"`), that is what the
    ticket opened. Raises `SubIssuesUnreadable` when the tracker could not be asked, or
    answered with fewer children than it counts. Patched out in tests."""
    return [child["number"] for child in tree.children(fetch_tree(number, root))]


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

    A blocking edge always points at an issue that exists, so the question is not
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
    active = False
    fence = None
    out = []
    for line in body.splitlines():
        if fence is not None:
            if active:
                out.append(line)
            close = FENCE_CLOSE_RE.match(line)
            if close and close.group(1)[0] == fence[0] and len(close.group(1)) >= fence[1]:
                fence = None
            continue
        opened = FENCE_OPEN_RE.match(line)
        if opened and not (opened.group(2)[0] == "`" and "`" in opened.group(3)):
            fence = (opened.group(2)[0], len(opened.group(2)))
        elif active and line.startswith("## "):
            break
        elif not active and line.rstrip() == f"## {heading}":
            active = True
            continue
        if active:
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
        m = re.match(r"^\s*-\s+([^\s（]+)", line)
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


def outside_owns_fields(number: int, globs: list[str], root: Path,
                        base: str | None) -> dict:
    """What the worker's own run records about files outside `## Owns`: `outside_owns`,
    the list, or `outside_owns_unchecked`, the branch it could not be asked on.

    The question — did this ticket write outside what it owns — is asked of this ticket's
    own commits, so it can only be answered on this ticket's own branch. A re-run on the
    branch the tickets were merged into is walking every ticket's commits, which answers
    nothing and runs past the 65536 characters a comment holds.
    """
    branch = current_branch(root)
    if branch != f"issue-{number}" or not base:
        return {"outside_owns_unchecked": branch or "(detached)"}
    return {"outside_owns": outside_owns(globs, root, base)}


def outside_owns_text(payload: dict) -> str:
    """The `Outside Owns:` line a person reads, from a run's fields."""
    if "outside_owns" in payload:
        return "Outside Owns: " + (", ".join(payload["outside_owns"]) or "None")
    return (f"Outside Owns: not checked on {payload.get('outside_owns_unchecked')}, which "
            f"carries more than this ticket")


def current_branch(root: Path | None = None) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)


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


def outside_owns(globs: list[str], root: Path, base: str) -> list[str]:
    """Files this ticket's own commits changed that no `## Owns` glob covers.

    Only the commits made on this branch itself count: the first-parent chain since it
    left its base, merge commits excluded. A later ticket merges an earlier ticket's
    branch to build on it, and the files that ride in with that merge are the earlier
    ticket's work, not this one's.
    """
    fork = git("merge-base", base, "HEAD", cwd=root)
    if not fork:
        return []
    args = ["log", "--first-parent", "--no-merges", "--name-only", "--format=",
            f"{fork}..HEAD", "--", "."]
    args += [f":(glob,exclude){g}" for g in globs]
    out = git(*args, cwd=root)
    seen: list[str] = []
    for line in out.splitlines():
        if line.strip() and line not in seen:
            seen.append(line)
    return seen


# ------------------------------------------------------------------- ledger

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


def shape_digest(lines: list[str]) -> str:
    """One fingerprint of a ledger's criteria as identity alone (`criteria_shape`): the
    same criteria, whatever any run ticked, give the same digest."""
    return hashlib.sha256("\n".join(criteria_shape(lines)).encode("utf-8")).hexdigest()


def newest_run(comments: list, *runs: str, actor: str | None = None) -> dict | None:
    """The newest matching `ticket.checked`, as its event record, or None."""
    found = []
    for comment in events.normalise(comments):
        what, payload = events.parse(comment["body"])
        if (what == "event" and payload["event"] == "ticket.checked"
                and payload.get("run") in runs
                and (actor is None or payload.get("actor") == actor)):
            found.append({"comment": comment["id"] if comment["id"] is not None
                          else comment["position"], "payload": payload})
    return max(found, key=lambda record: record["comment"]) if found else None


def final_worker_run(comments: list) -> dict | None:
    """The worker run the closeout accepts and the closing comment quotes: the newest of
    the worker's own runs and its reverify runs. The closeout holds it to `HEAD`, so when
    nothing was committed after the worker's first run, that run is the final one."""
    runs = [record for record in (newest_run(comments, "self"),
                                  newest_run(comments, "reverify", actor="worker"))
            if record is not None]
    return max(runs, key=lambda record: record["comment"]) if runs else None


def ledger_with_results(lines: list[str], results: list[dict]) -> list[str]:
    """The ledger `lines` with each criterion ticked and its `EVIDENCE:` written the way
    one run left it: `results` is that run's `criteria`, `{id, met, evidence}` each.

    A fenced `CHECK:` is skipped over whole, so a `- [ ]` line inside a heredoc is never
    mistaken for a criterion, the same reading `parse_criteria` gives it.
    """
    by_id = {r.get("id"): r for r in results if isinstance(r, dict)}
    out: list[str] = []
    current = None
    fence = None

    def close_item():
        if current is not None and not current["evidence_seen"] and current["result"]:
            out.insert(current["insert_at"], "  EVIDENCE: " + current["result"]["evidence"])

    for line in lines:
        if fence is not None:
            out.append(line)
            close = FENCE_CLOSE_RE.match(line)
            if close and close.group(1)[0] == fence[0] and len(close.group(1)) >= fence[1]:
                fence = None
                if current is not None:
                    current["insert_at"] = len(out)
            continue
        opened = FENCE_OPEN_RE.match(line)
        if opened and not (opened.group(2)[0] == "`" and "`" in opened.group(3)):
            fence = (opened.group(2)[0], len(opened.group(2)))
            out.append(line)
            continue
        gate = GATE_LINE_RE.match(line)
        if gate:
            close_item()
            result = by_id.get(gate.group(2))
            if result:
                line = ("- [x]" if result.get("met") else "- [ ]") + line[5:]
                result = {"evidence": str(result.get("evidence") or "pending")}
            out.append(line)
            current = {"result": result, "evidence_seen": False, "insert_at": len(out)}
            continue
        if current is not None and EVIDENCE_LINE_RE.match(line):
            current["evidence_seen"] = True
            if current["result"]:
                indent = line[:len(line) - len(line.lstrip())]
                line = f"{indent}EVIDENCE: {current['result']['evidence']}"
        out.append(line)
        if current is not None and ATTR_LINE_RE.match(line):
            current["insert_at"] = len(out)
    close_item()
    return out


def carried_ledger(body: str, comments: list) -> list[str]:
    """The criteria as the newest run left them, when it ran the criteria the body
    states now; empty otherwise.

    A re-verification re-runs what the last run ticked, so the newest `ticket.checked`
    of the worker's run or of a reverify is where that state lives. A criterion the
    ticket has since rewritten — a decision changed what this ticket must do, and the
    ticket says so — has a different fingerprint, so that run is dropped and the
    criteria are read fresh. What is lost with it is the evidence of a run of the
    criteria as they used to be.
    """
    record = newest_run(comments, "self", "reverify")
    if record is None:
        return []
    criteria = section(body, "Acceptance criteria")
    payload = record["payload"]
    if payload.get("shape") != shape_digest(criteria):
        return []
    return ledger_with_results(criteria, payload.get("criteria") or [])


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


def check_timeout(body: str) -> int:
    """Seconds gate-check gets per `CHECK:` on this ticket.

    The largest of `DEFAULT_TIMEOUT` and every `TIMEOUT:` in `## Acceptance criteria`: a
    ticket can raise the limit and never lower it, and it is read off the ticket body
    whichever run this is, so the final `--reverify` runs under the same number as the
    worker's own run.
    """
    values = [DEFAULT_TIMEOUT]
    for criterion in parse_criteria("\n".join(section(body, "Acceptance criteria"))):
        if criterion["timeout"].isdigit() and int(criterion["timeout"]) > 0:
            values.append(int(criterion["timeout"]))
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
    """(met, total) read off the ledger: a met criterion is ticked with real evidence."""
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


def newest_worker_started(number: int, comments: list) -> tuple[dict | None, str | None]:
    """The newest readable `worker.started` payload, or the fact that none exists."""
    record = events.newest(comments, "worker.started")
    if record:
        return record["payload"], None
    return None, (f"#{number} carries no readable worker.started event. Only worker "
                  f"dispatch writes this record, so its absence is a pipeline fault. "
                  f"Run `verify-ticket.py {number} --sub-issue fault <file>`, then stop.")


def worker_started_field(number: int, comments: list,
                         field: str) -> tuple[str | None, str | None]:
    """One required field of the newest readable `worker.started`."""
    started, problem = newest_worker_started(number, comments)
    if problem:
        return None, problem
    value = started.get(field)
    if isinstance(value, str) and value:
        return value, None
    return None, (f"#{number}'s newest worker.started carries no `{field}`. Only worker "
                  f"dispatch writes this field, so its absence is a pipeline fault. "
                  f"Run `verify-ticket.py {number} --sub-issue fault <file>`, then stop.")


def draft_summary(draft: str) -> tuple[str, dict]:
    """The first line and the `Counts:` line's numbers `--closeout` writes for this
    draft: whichever of `ALL MET` or `HANDOFF REQUIRED: …` its `ABANDON:` lines and
    unmet criteria make true, and the ledger's own count. A worker need not get this
    arithmetic right by hand; the closeout computes it from the draft every time.
    """
    criteria = parse_criteria(draft)
    abandons = parse_abandons(draft)
    counts = tally(criteria, abandons)
    blocking = sorted({a["kind"] for a in abandons if a["kind"] in HANDOFF_KINDS})
    if counts["unmet"] or blocking:
        kinds = ", ".join(k for k in HANDOFF_KINDS if k in blocking)
        first = (f"HANDOFF REQUIRED: {counts['abandoned']} abandoned ({kinds}), "
                 f"{counts['unmet']} unmet, {counts['met']} met of {counts['total']}")
    else:
        first = "ALL MET"
    return first, counts


def rewrite_summary(draft: str, first: str, counts: dict) -> str:
    """`draft` with its first line and `Counts:` line replaced by what `draft_summary`
    computed, so the comment that posts states only what the draft's own `ABANDON:`
    lines and criteria make true. A `Counts:` line the draft lacks is added."""
    lines = draft.split("\n")
    if lines:
        lines[0] = first
    counts_line = (f"Counts: {counts['met']} met, {counts['unmet']} unmet, "
                   f"{counts['abandoned']} abandoned of {counts['total']}")
    for i, line in enumerate(lines):
        if line.startswith("Counts:"):
            lines[i] = counts_line
            break
    else:
        lines.append(counts_line)
    return "\n".join(lines)


def draft_problems(draft: str, comments: list[str]) -> list[str]:
    """Everything wrong with the draft that its own `ABANDON:` lines cannot settle, in
    the order a reader would hit it. The first line and `Counts:` are computed by
    `draft_summary`, not checked here."""
    if not draft.strip():
        return ["the draft is empty"]
    problems = []
    if FILL in draft:
        problems.append("the draft still contains `<fill>`; replace the placeholders "
                        "in `skipped:`, `Review findings:`, `Green before work:` and "
                        "`Decisions I made on my own`")

    criteria = parse_criteria(draft)
    ids = [c["id"] for c in criteria]
    abandons = parse_abandons(draft)
    for a in abandons:
        if a["kind"] not in ABANDON_KINDS:
            problems.append(f"ABANDON: {a['ac']} has kind `{a['kind']}`; "
                            f"it must be one of {', '.join(ABANDON_KINDS)}")
        if a["ac"] not in ids:
            problems.append(f"ABANDON: {a['ac']} points at a criterion the draft does not list")

    for c in criteria:
        if c.get("stray"):
            problems.append(f"{c['id']} continues its CHECK onto another line; wrap the "
                            f"command in a fenced block under `CHECK:` instead")
        if c["ticked"] and (not c["evidence"] or c["evidence"] == "pending"):
            problems.append(f"{c['id']} is ticked but its EVIDENCE is pending; "
                            f"either fill in what proved it or untick it")

    return problems


def verified_problems(draft: str, body: str, comments: list[str], first: str) -> list[str]:
    """What an `ALL MET` draft lacks in the worker's final run. `first` is the one
    `draft_summary` computed, not necessarily the draft's own literal first line."""
    problems = []
    if first != "ALL MET":
        return problems

    record = final_worker_run(comments)
    reverify = record["payload"] if record else None
    if reverify is None:
        problems.append("the ticket carries no `ticket.checked` event of a worker run. Run "
                        "`verify-ticket.py <n> --reverify --actor worker` after the final "
                        "commit, or close out as `HANDOFF REQUIRED`")
    else:
        # A run is generated from the ticket body, which carries no `ABANDON:` line, so a
        # criterion the draft abandons as `decision` still runs and still reports unmet.
        # That unmet is the one this draft is allowed to carry: the sub-issue is open and
        # the ticket closes on it. Any other unmet is a claim the draft cannot make.
        decided = {a["ac"] for a in parse_abandons(draft) if a["kind"] == "decision"}
        result = reverify.get("result")
        unmet = list(reverify.get("failed") or [])
        covered = result == "unmet" and unmet and set(unmet) <= decided
        if result != "met" and not covered:
            problems.append("the worker's final run still reports unmet or abandoned "
                            "criteria. Add the required `ABANDON:` lines and close out as "
                            "`HANDOFF REQUIRED`")
        if reverify.get("commit") != git("rev-parse", "HEAD"):
            problems.append(f"the worker's final run is on {reverify.get('commit')} and "
                            "HEAD has moved on. Run `--reverify --actor worker` on HEAD")
        # The criteria the worker ran must be the criteria the ticket now states. A
        # ticket may legitimately rewrite one — a decision changed what it must do — but
        # then what stands is a verification of something else, and the final run runs again.
        if reverify.get("shape") != shape_digest(section(body, "Acceptance criteria")):
            problems.append("the acceptance criteria have changed since the worker's final "
                            "run: run `--reverify --actor worker` again so the run and the "
                            "ticket agree")
    return problems


def event_problems(comments: list) -> list[str]:
    """Comments on the ticket whose event cannot be read.

    The closeout decides from the ticket's events, so a comment that carries one
    this pipeline cannot read is a question left unanswered, not a comment to skip.
    """
    return [f"comment {item['comment']} (`{item['line'][:50]}`) carries an event this "
            f"pipeline cannot read: {item['reason']}"
            for item in events.fold(comments)["unreadable"]]


def git_problems(base: str, root: Path | None = None) -> list[str]:
    """The repository conditions a ticket must be in to close, plus one warning."""
    problems = []
    dirty = dirty_tracked(root)
    if dirty:
        problems.append(f"{len(dirty)} tracked files have uncommitted changes; "
                        f"commit them so the closing comment names a real commit")
    if not is_ancestor(base, "HEAD", root):
        problems.append(f"this branch does not contain its base {base}; run `git merge {base}`. "
                        f"Do not rebase because the ticket's recorded runs name commits")
        return problems
    fork = git("merge-base", base, "HEAD", cwd=root)
    if fork and not git("diff", "--name-only", f"{fork}..HEAD", cwd=root):
        sys.stderr.write("warning: this branch changes no files since it left its base branch\n")
    return problems


# ---------------------------------------------------------------- ticket graph
# `validate_dag`, `_detect_cycles`, `_trace_cycle` and `compute_levels` are
# grok-bundled's `execute-plan/scripts/validate-plan.py` L145-280, function for
# function. Only the shape of an entry changed: an id is an issue number rather
# than a `pr-<n>` string, and dependencies come from the tracker's blocking edges.
#
# A plan's steps all lived in one plan; a ticket's blockers do not. A spec delivered in
# layers blocks its tickets on tickets under the spec before it, and an issue that is no
# ticket at all can be linked as a blocker too. Neither is an edge these four can order,
# so `in_batch` takes them out before the graph is built, and `blockers_not_tickets`,
# `cross_batch_findings` and `waiting_outside` say what was taken out and what it means.

def ref(ticket: int | str) -> str:
    """How a ticket is named in a finding: `#<n>` for an issue, the bare name for a draft."""
    return f"#{ticket}" if isinstance(ticket, int) else str(ticket)


def validate_dag(entries: list[dict]) -> list[str]:
    """Check unique ids and no cycles. Dependencies are already this batch's.

    A blocker outside the batch is not a dangling reference here: `in_batch` has taken
    it out, and `blockers_not_tickets` / `cross_batch_findings` say what it is.
    """
    errors = []

    seen = set()
    for entry in entries:
        if entry["id"] in seen:
            errors.append(f"duplicate ticket: {ref(entry['id'])}  [duplicate-ticket]")
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
        return ["cycle detected: " + " -> ".join(ref(i) for i in cycle) + "  [cycle]"]
    return ["cycle detected involving: "
            + ", ".join(ref(i) for i in sorted(unvisited)) + "  [cycle]"]


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

    A blocking edge to another spec's ticket is a real edge, and `--preflight`,
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
    """Blocking edges to issues that are not tickets under any spec.

    A blocking edge always points at an issue that exists, so what is asked here is
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
            errors.append(f"{ref(entry['id'])} is blocked by {ref(dep)}, which is not a "
                          f"ticket under any spec  [blocker-not-a-ticket]")
    return errors


def cross_batch_findings(entries: list[dict]) -> list[str]:
    """Blocking edges to tickets under another spec.

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
            findings.append(f"{ref(entry['id'])} is blocked by #{dep}, a ticket under spec "
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
                lines.append(f"waiting on another spec: {ref(entry['id'])} ← #{dep} "
                             f"({where.get('state') or 'unknown'}, spec #{where['spec']})")
    return lines


def ticket_entries(numbers: list[int]) -> list[dict]:
    """One entry per ticket: the blocking edges the tracker records.

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


JUDGEMENT_WORDS = {"reasonable": re.compile(r"(?<![\w-])reasonable\b", re.I),
                   "should not": re.compile(r"\bshould not\b", re.I)}
NEGATED_JUDGEMENT_RE = re.compile(
    r"\b(?:no|not)\s+[`'\"*_]*(?:should not|reasonable)\b[`'\"*_]*", re.I)


def line_judgement(line: str) -> str | None:
    """The one judgement word `line` carries, or `None` when it carries neither or both.

    A negated word (`No should not.`, `not reasonable`) is no judgement: a reviewer
    who closes a line of `reasonable` decisions with `No should not.` has judged
    none of them `should not`.
    """
    text = NEGATED_JUDGEMENT_RE.sub(" ", line)
    found = {word for word, pattern in JUDGEMENT_WORDS.items() if pattern.search(text)}
    return found.pop() if len(found) == 1 else None


def spec_judgement(review: str, path: str) -> str | None:
    """`reasonable` or `should not` for `path` from the Spec axis of a `REVIEW` comment.

    The code-review Spec axis gives each `Outside Owns` file one line that starts with
    its path and carries exactly one judgement word; that line decides.
    `None` when that axis names no line for the file, or its lines carry
    both words or neither — the run does not invent a judgement the reviewer did not
    write.
    """
    spec_axis = re.split(r"^## Tests", review, maxsplit=1, flags=re.M)[0]
    spec_axis = re.split(r"^## Spec", spec_axis, maxsplit=1, flags=re.M)[-1]
    naming = [line for line in spec_axis.splitlines() if path in line]
    leads = re.compile(r"^\s*(?:[-*+]|\d+[.)])?\s*[`*_\"']*" + re.escape(path)
                       + r"(?![\w./-])")
    leading = [line for line in naming if leads.match(line)]
    judgements = {line_judgement(line) for line in leading}
    return judgements.pop() if len(judgements) == 1 else None


def decisions_line_for(decisions: str | None, path: str, number: int) -> str:
    """The sentence in the `DECISIONS` comment that names `path`."""
    if not decisions:
        return f"no DECISIONS comment on #{number} yet"
    for line in decisions.splitlines():
        stripped = line.strip()
        if path in stripped and not stripped.startswith("Outside Owns:"):
            return stripped.lstrip("- ").strip()
    return path


def overlay_run_evidence(body: str, run: dict | None) -> list[dict]:
    """Criteria from the ticket body, ticks and evidence from one run's `criteria`."""
    base = parse_criteria("\n".join(section(body, "Acceptance criteria")))
    ran = {c.get("id"): c for c in (run or {}).get("criteria") or [] if isinstance(c, dict)}
    for item in base:
        if item["id"] in ran:
            item["ticked"] = bool(ran[item["id"]].get("met"))
            if ran[item["id"]].get("evidence"):
                item["evidence"] = str(ran[item["id"]]["evidence"])
    return base


def in_ticket_findings(review: str, comment: int | str | None = None,
                       next_step: str = "correct the review report before writing a "
                                        "closeout draft") -> list[str]:
    """Each finding verbatim from `## In-ticket`; refuse a nonempty unknown row.

    A row carries its category and source, and its source and any unverified note remain
    in the one line handed to the worker. `next_step` ends the refusal: the reviewer
    posting the report and the worker drafting its closeout each have a different thing
    to do about the row.
    """
    rows = [row.strip() for row in section(review, "In-ticket")
            if row.strip() and not re.fullmatch(r"<!-- mmw \{.*\} -->", row.strip())]
    if rows in (["None"], ["None."]) or not rows:
        return []
    found = []
    for row in rows:
        if CAT_IN_TICKET_ITEM_RE.fullmatch(row):
            found.append(row)
        else:
            label = f"comment {comment}" if comment is not None else "review report"
            raise ValueError(f"{label} (`{review.splitlines()[0] if review else '(empty)'}`) "
                             f"has an unrecognized ## In-ticket row: {row}; {next_step}")
    return found


def require_in_ticket(review: str, comment: int | str | None, number: int) -> None:
    if section(review, "In-ticket"):
        return
    first = review.splitlines()[0] if review else "(empty)"
    raise ValueError(
        f"the newest review report (comment {comment}, `{first[:80]}`) has no readable ## In-ticket "
        f"content, so it cannot close as reviewed; open a "
        f"fault child with `verify-ticket.py {number} --sub-issue fault <file>`, its body "
        f"the report, and stop")


def review_findings_block(review: str, comment: int | str | None = None) -> str:
    items = in_ticket_findings(review, comment)
    if not items:
        return "Review findings:\nNone"
    lines = ["Review findings:"]
    for row in items:
        lines.append(f"{row} — {FILL}")
    return "\n".join(lines)


def green_before_work_block(comments: list) -> str:
    record = newest_run(comments, "baseline")
    if record is None:
        return "Green before work:\nnot run: no baseline `ticket.checked`"
    ids = []
    for item in record["payload"].get("criteria") or []:
        if isinstance(item, dict) and item.get("met") and item.get("id"):
            ids.append(str(item["id"]))
    if not ids:
        return "Green before work:\nNone"
    return "Green before work:\n" + "\n".join(f"- {i}: {FILL}" for i in ids)


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
    run = newest_run(comments, "self")
    if run is None:
        return refuse(f"#{number} carries no ticket.checked of your own run to check "
                      f"Outside Owns against")
    want = outside_owns_text(run["payload"])
    got = outside_owns_from("\n".join(section(text, "Outside Owns")))
    if want != got:
        return refuse(f"the file's `Outside Owns` line does not match your newest run, "
                      f"which says `{want}`")
    post_event(number, "worker.decided", "DECISIONS", text.lstrip("\n"))
    print(f"DECISIONS: posted on #{number}")
    return 0


def open_children_owns(number: int) -> list[tuple[int, list[str]]]:
    """OPEN children of spec `number` and each child's `## Owns` globs, loaded once."""
    found = []
    for child in tree.children(fetch_tree(number, "spec")):
        if child.get("state") != "OPEN":
            continue
        found.append((child["number"], owns_globs(fetch_body(child["number"]))))
    return found


REVIEW_HEAD_RE = re.compile(r"^REVIEW (\S+?)\.\.(\S+)")


def run_review(number: int, path: Path) -> int:
    """Post the review report on the ticket, as the `reviewer.reported` event.

    Nothing here tells the worker: the event on the ticket is what the relay of the
    dispatch skill turns into the worker's wake-up, so a report that lands is a report
    its worker hears about, however the reviewer's turns fell.

    The file opens `REVIEW <base-commit>..<HEAD commit>`: that line becomes the
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
            "a review report opens `REVIEW <base-commit>..<HEAD commit>`, and this file "
            + (f"opens `{head[:60]}`" if head else "is empty"))
    try:
        in_ticket_findings(stripped, next_step=(
            "rewrite that row as `- <Axis> [<category>] <path>:<line> — <claim> — "
            "source: <…>`, or write `None`, then run --review again"))
    except ValueError as exc:
        return refuse(str(exc))
    rest = "\n".join(stripped.splitlines()[1:]).strip("\n")
    post_event(number, "reviewer.reported", head, rest,
               base=found.group(1), head=found.group(2))
    print(f"REVIEW: posted on #{number}")
    return 0


def run_touched(number: int) -> int:
    """Post `worker.touched` on each open sibling whose `## Owns` covers a file this
    ticket changed outside its own, naming the files and why they were changed. A ticket
    outside any spec has no siblings: it posts nothing and exits 0."""
    comments = fetch_comments(number)
    review = (events.newest(comments, "reviewer.reported") or {}).get("body")
    if review is None:
        return refuse(f"#{number} carries no reviewer.reported event")
    run = newest_run(comments, "self")
    if run is None:
        return refuse(f"#{number} carries no ticket.checked of your own run")
    files = list(run["payload"].get("outside_owns") or [])
    if not files:
        return 0
    decisions = (events.newest(comments, "worker.decided") or {}).get("body")
    try:
        spec = spec_of(number)
    except ParentUnreadable as exc:
        return refuse(f"#{number}: the tracker could not say which spec it sits under ({exc})")
    if spec is None:
        # A ticket outside any spec has no batch, so no other ticket owns these files.
        sys.stderr.write(f"#{number} sits under no spec, so no other ticket owns "
                         f"{', '.join(files)}; nothing to tell\n")
        return 0
    try:
        siblings = open_children_owns(spec)
    except SubIssuesUnreadable as exc:
        return refuse(f"#{number}: the tracker could not list the children of #{spec} ({exc})")
    details = []
    for path in files:
        sentence = decisions_line_for(decisions, path, number)
        found = re.search(r"\bAC\d+\b", sentence)
        details.append({"path": path, "sentence": sentence,
                        "ac": found.group(0) if found else None,
                        "judgement": spec_judgement(review, path)})
    posted_to: list[int] = []
    for child, globs in siblings:
        if child == number:
            continue
        mine = [d for d in details if any(glob_covers(g, d["path"]) for g in globs)]
        if not mine:
            continue
        prose = []
        for d in mine:
            path_line = (d["path"] if d["judgement"] else
                         f"{d['path']} (REVIEW has no judgement line for it)")
            prose += ["", path_line, d["sentence"]]
            prose += [x for x in (d["ac"], d["judgement"]) if x]
        post_event(child, "worker.touched",
                   f"#{number} changed {len(mine)} file(s) this ticket owns",
                   "\n".join(prose).strip("\n"), spec=spec, by=number,
                   files=[d["path"] for d in mine],
                   details=[{k: v for k, v in d.items() if v} for d in mine])
        posted_to.append(child)
    if posted_to:
        print("TOUCHED: " + ", ".join(f"#{n}" for n in posted_to))
    return 0


def default_draft_path(number: int) -> Path:
    """A file of this run's own making, in a fresh directory outside every repository.

    The closing-comment draft recounts the ticket, so it carries every path and file name the ticket
    names — that is what a closing comment says. A draft written into the working tree is
    one more file the repository's own tools read: its guards, its hooks, a worker's run
    of its checks. A prior ticket with every criterion met stayed open because a
    repository guard found two reference file names in the closeout draft written inside
    its working tree. Every consuming repository with a guard over its own Markdown could
    meet the same wall, so the default landing place is outside all of them.
    """
    return Path(tempfile.mkdtemp(prefix=f"mmw-closeout-{number}-")) / f"closeout-{number}.md"


def run_draft(number: int, out_file: Path | None) -> int:
    """Write the closing-comment draft to `out_file`, or to a path of this run's own
    when it is None, printing the path either way."""
    body = fetch_body(number)
    comments = fetch_comments(number)
    into, problem = worker_started_field(number, comments, "into")
    if problem:
        return refuse(problem)
    record = final_worker_run(comments)
    run = record["payload"] if record else None
    criteria = overlay_run_evidence(body, run)
    abandons = list((run or {}).get("abandons") or [])
    counts = tally(criteria, abandons)
    blocking = [a for a in abandons if a["kind"] in HANDOFF_KINDS]
    if blocking:
        kinds = ", ".join(k for k in HANDOFF_KINDS if any(a["kind"] == k for a in blocking))
        first = (f"HANDOFF REQUIRED: {counts['abandoned']} abandoned ({kinds}), "
                 f"{counts['unmet']} unmet, {counts['met']} met of {counts['total']}")
    else:
        first = "ALL MET"
    head = git("rev-parse", "HEAD")
    branch_line = (f"Branch: issue-{number} Commit: {head} PR: none — will be merged into "
                   f"{into} by dispatch.sh")
    review_event = events.newest(comments, "reviewer.reported") or {}
    review = review_event.get("body") or ""
    try:
        if review_event:
            require_in_ticket(review, review_event.get("comment"), number)
        review_block = review_findings_block(review, review_event.get("comment"))
    except ValueError as exc:
        return refuse(str(exc))
    files = list((run or {}).get("outside_owns") or [])
    if files:
        judged = []
        for path in files:
            judgement = spec_judgement(review, path)
            judged.append(f"{path} ({judgement or 'REVIEW has no judgement line for it'})")
        outside = "Outside Owns: " + ", ".join(judged)
    else:
        outside = "Outside Owns: None"
    try:
        opened = [f"#{child}" for child in fetch_sub_issues(number, "ticket")]
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
        review_block, "",
        f"skipped: {FILL}", "",
        green_before_work_block(comments), "",
        sub, "",
        counts_line, "",
        "Decisions I made on my own", "",
        FILL, "",
    ]
    # After every refusal, so a run that writes nothing leaves no directory behind either.
    out_file = out_file or default_draft_path(number)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"DRAFT: wrote {out_file}")
    return 0


def ensure_label(name: str) -> str | None:
    """Make sure the repository has label `name`, from `LABELS`; the reason when it
    could not.

    A label the repository lacks makes `gh issue create --label` fail outright, so the
    first issue that would carry it creates it instead. One that already exists is left
    exactly as it is. Patched out in tests.
    """
    color, description = LABELS[name]
    out = subprocess.run(["gh", "label", "create", name, "--color", color,
                          "--description", description],
                         capture_output=True, text=True, env=GH_ENV)
    if out.returncode == 0 or "already exists" in (out.stderr or out.stdout or ""):
        return None
    return gh_detail(out)


def gh_issue_create(args: list[str], body: str) -> tuple[subprocess.CompletedProcess, int | None]:
    """Run `gh issue create <args> --body-file <body>`: the completed process, and the
    issue number `gh` printed, or None when there was none to parse from its output.
    Patched out in tests through `subprocess.run`."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        body_path = fh.name
    try:
        result = subprocess.run(["gh", "issue", "create", *args, "--body-file", body_path],
                                capture_output=True, text=True, env=GH_ENV)
    finally:
        os.unlink(body_path)
    printed = (result.stdout or "").strip()
    found = re.search(r"/issues/(\d+)", printed)
    return result, (int(found.group(1)) if found else None)


def run_sub_issue(number: int, kind: str, path: Path) -> int:
    """Open a child under this ticket with its kind's status, and record it here.

    Every child carries `mmw:child`. Only `decision` and `deferred` carry
    `needs-triage`; `finding`, `contract` and `fault` await the orchestrator.
    Its body opens with a line a person reads; which kind it is and where it came
    from is the
    `child.opened` event posted on this ticket, which is where the ticket's own fold finds
    its children. A child opened whose event could not be written exits 1 and says so:
    the child exists, and opening it again would make two.
    """
    if kind not in SUB_ISSUE_KINDS:
        return refuse(f"kind `{kind}` is not one of {', '.join(SUB_ISSUE_KINDS)}")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not text.strip():
        return refuse(f"{path} is empty")
    title = text.strip().splitlines()[0].strip()
    if len(title) > GITHUB_TITLE_LIMIT:
        title = title[:GITHUB_TITLE_LIMIT - 1] + "…"
    labels = ["mmw:child"]
    if kind in ("decision", "deferred"):
        labels.insert(0, "needs-triage")
    for label in labels:
        missing = ensure_label(label)
        if missing:
            return refuse(f"the repository has no `{label}` label and it could not be "
                          f"created ({missing}); nothing was opened")
    posted = f"A `{kind}` child of #{number}.\n\n" + text
    if not posted.endswith("\n"):
        posted += "\n"
    result, child = gh_issue_create(
        ["--parent", str(number), *[arg for label in labels for arg in ("--label", label)],
         "--title", title], posted)
    if result.returncode != 0:
        sys.stderr.write((result.stderr or result.stdout or "gh issue create failed").rstrip() + "\n")
        return 2
    printed = (result.stdout or "").strip()
    recorded = 0
    if child is None:
        sys.stderr.write(f"opened a sub-issue of #{number} but `gh issue create` printed no "
                         f"issue number ({printed[:80] or 'nothing'}), so no child.opened "
                         f"event was written on #{number}; do not open it again\n")
        recorded = 1
    else:
        try:
            post_event(number, "child.opened", f"Opened #{child} ({kind}): {title}",
                       child=child, kind=kind, title=title)
        except (OSError, subprocess.CalledProcessError) as exc:
            sys.stderr.write(f"opened #{child} under #{number}, but the child.opened event "
                             f"on #{number} was not written ({exc}); do not open it again\n")
            recorded = 1
    print(str(child) if child is not None else printed)
    return recorded


def issue_db_id(number: int) -> int:
    """The tracker's own numeric id of issue `number`, the one its dependency links use
    (never the `#number` or the GraphQL node id). Patched out in tests."""
    out = subprocess.run(
        ["gh", "api", f"repos/{{owner}}/{{repo}}/issues/{number}", "--jq", ".id"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if out.returncode != 0 or not out.stdout.strip():
        raise TrackerReadError(number, "database id", gh_detail(out))
    return int(out.stdout.strip())


def add_blocking_link(child: int, blocker: int) -> str | None:
    """Record `child` as blocked by `blocker` in the tracker's native issue dependencies,
    the same edge the mmw-mode skill's `references/github-issues.md` adds by hand.
    The reason when it could not be recorded, None when it was. Patched out in tests."""
    try:
        blocker_id = issue_db_id(blocker)
    except TrackerReadError as exc:
        return str(exc)
    out = subprocess.run(
        ["gh", "api", "--method", "POST",
         f"repos/{{owner}}/{{repo}}/issues/{child}/dependencies/blocked_by",
         "-F", f"issue_id={blocker_id}"],
        capture_output=True, text=True, env=GH_ENV,
    )
    if out.returncode != 0:
        return gh_detail(out)
    return None


def label_defined(name: str) -> bool:
    """Whether `name` is one this file knows the colour and description of."""
    return name in LABELS


def run_publish_spec(body_path: Path, title: str, map_number: int | None) -> int:
    """Publish a spec: one issue carrying the kind label `mmw:spec`, and, when
    `map_number` is given, a native sub-issue of that map — the link the board and the
    retro find a spec's map through; nothing written in the body stands in for it.

    A spec is a container for the tickets underneath it, not a piece of work, so it
    carries no status label.
    """
    if len(title) > GITHUB_TITLE_LIMIT:
        return refuse(f"--title has {len(title)} Unicode characters; the GitHub title "
                      f"limit is {GITHUB_TITLE_LIMIT}; shorten --title before publishing")
    text = body_path.read_text(encoding="utf-8") if body_path.is_file() else ""
    if not text.strip():
        return refuse(f"{body_path} is empty")
    missing = ensure_label(CLASS_SPEC)
    if missing:
        return refuse(f"the repository has no `{CLASS_SPEC}` label and it could not be "
                      f"created ({missing}); nothing was published")
    args = ["--title", title, "--label", CLASS_SPEC]
    if map_number is not None:
        args += ["--parent", str(map_number)]
    result, number = gh_issue_create(args, text)
    if result.returncode != 0:
        sys.stderr.write((result.stderr or result.stdout or "gh issue create failed").rstrip() + "\n")
        return 2
    if number is None:
        printed = (result.stdout or "").strip()
        return refuse(f"gh issue create printed no issue number ({printed[:80] or 'nothing'}); "
                      f"check the tracker directly for whether the spec was published")
    if map_number is not None:
        try:
            parent = fetch_parent(number)
        except ParentUnreadable as exc:
            print(str(number))
            sys.stderr.write(f"#{number} was published, but its native parent could not be "
                             f"confirmed ({exc}); check it by hand\n")
            return 1
        if parent != map_number:
            print(str(number))
            sys.stderr.write(f"#{number} was published, but its native parent is "
                             f"{('#' + str(parent)) if parent else 'unset'}, not #{map_number}; "
                             f"`## Sources`, the title and semantic similarity do not replace "
                             f"the native parent — check it by hand\n")
            return 1
    print(str(number))
    return 0


# ----------------------------------------------------------------- subcommands

def _refusal(what: str, why: str, next_step: str) -> str:
    """A refusal in three parts: what happened, why, and the command to run next."""
    return f"{what.strip()} {why.strip()} {next_step.strip()}"


def criterion_ids_on_lines(ledger: str, line_numbers: list[int]) -> list[str]:
    """The criterion that owns each of these 1-based ledger lines, in file order."""
    wanted = set(line_numbers)
    current = None
    found = []
    for index, line in enumerate(ledger.splitlines(), start=1):
        match = GATE_LINE_RE.match(line)
        if match:
            current = match.group(2)
        if index in wanted and current and current not in found:
            found.append(current)
    return found


def present_unrunnable(printed: str, number: int, tmp: str) -> str:
    """gate-check exited 2. Name the ticket and the criterion, and drop the ledger path.

    The ledger is a temporary file. Its path and its line numbers are not a place the
    worker can edit. The criterion is the one that owns the line gate-check named.
    """
    text = printed
    line_numbers = [int(n) for n in re.findall(r"\bline (\d+):", text)]
    ledger_file = Path(tmp) / LEDGER_NAME
    from_ledger = (criterion_ids_on_lines(ledger_file.read_text(encoding="utf-8"), line_numbers)
                   if ledger_file.is_file() else [])
    variants = {str(tmp), os.path.realpath(str(tmp))}
    variants |= ({path.removeprefix("/private") for path in variants}
                 | {"/private" + path for path in variants})
    for path in sorted(variants, key=len, reverse=True):
        if path:
            text = text.replace(path, "")
    text = re.sub(rf"/?{re.escape(LEDGER_NAME)}:?", "", text)
    text = re.sub(r"\bline \d+:\s*", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text).strip()
    from_text = re.findall(r"\bgate ([A-Za-z0-9][A-Za-z0-9._-]*)\b", text)
    ids = list(dict.fromkeys([*from_ledger, *from_text]))
    named = ", ".join(ids) if ids else "unknown"
    note = _refusal(
        f"ticket #{number} criterion {named}, gate-check exited 2",
        "the criterion could not be run, so nothing was judged",
        f"verify-ticket.py {number} --sub-issue contract <file>",
    )
    if text:
        return text + "\n" + note + "\n"
    return note + "\n"


def run_checks(number: int, reverify: bool, actor: str | None = None) -> int:
    return _run_checks(number, reverify, actor, fetch_body(number), repo_root())


def criterion_environment(number: int, into: str | None) -> dict[str, str]:
    env = os.environ.copy()
    env["MMW_TICKET"] = str(number)
    if into:
        env["MMW_BASE_REF"] = f"origin/{into}"
    return env


def _run_checks(number: int, reverify: bool,
                actor: str | None, body: str, root: Path) -> int:
    """Run the ticket's criteria and post the run as one `ticket.checked` event.

    Exit 0 every criterion met, 1 not, 2 the run could not start (nothing was judged and
    nothing was written), 4 the criteria ran and the ticket.checked recording them could
    not be written.
    """
    run = "reverify" if reverify else "self"
    actor = actor or "worker"
    head = git("rev-parse", "HEAD", cwd=root)
    if not re.fullmatch(r"[0-9a-f]{40}", head or ""):
        return refuse("could not read HEAD, so this run would name no commit. Nothing was "
                      "run and nothing was written.")
    comments = fetch_comments(number)
    started = events.newest(comments, "worker.started")
    started_payload = (started or {}).get("payload", {})
    # Every worker run can be the one the closeout accepts and quotes, so each records
    # Outside Owns; a reverify by the main agent runs on the merged branch, where the
    # question has no answer.
    worker = actor == "worker"
    base = started_payload.get("base") if worker else None
    into = started_payload.get("into")
    carried = carried_ledger(body, comments) if reverify else []
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp), carried or None)
        cmd = ["node", str(GATE_CHECK), "--cwd", str(root)]
        if reverify:
            cmd.append("--reverify")
        cmd += ["--timeout", str(check_timeout(body))]
        cmd.append(str(ledger))
        env = criterion_environment(number, into)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        if result.returncode == 2:
            sys.stdout.write(present_unrunnable(printed, number, tmp))
            return 2
        sys.stdout.write(printed)
        summary = next((line for line in printed.splitlines() if SUMMARY_RE.match(line)), "")
        updated = ledger.read_text(encoding="utf-8").rstrip("\n")

    criteria = parse_criteria(updated)
    abandons = parse_abandons(updated)
    results = [{"id": c["id"],
                "met": bool(c["ticked"] and c["evidence"] and c["evidence"] != "pending"),
                "evidence": c["evidence"] or "pending"} for c in criteria]
    outcome = check_run_outcome(result.returncode, summary)
    fields = (outside_owns_fields(number, owns_globs(body), root, base) if worker else {})
    prose = [updated]
    if worker:
        prose += ["", outside_owns_text(fields)]
    try:
        post_event(number, "ticket.checked",
                   f"{'Reverify' if reverify else 'Own run'} on {head[:12]}: "
                   f"{summary or outcome}",
                   "\n".join(prose), run=run, commit=head, result=outcome,
                   counts=tally(criteria, abandons),
                   criteria=results,
                   failed=[r["id"] for r in results if not r["met"]],
                   abandons=abandons or None,
                   shape=shape_digest(section(body, "Acceptance criteria")),
                   actor=actor, stage=events.checked_stage(run, actor),
                   **fields)
    except (OSError, subprocess.CalledProcessError) as exc:
        # The criteria ran, but nothing on the ticket says how. Every reader decides from
        # that event, so this run counts as one that did not happen — never as red.
        sys.stderr.write(f"#{number}: the run finished {outcome} on {head[:12]}, but its "
                         f"ticket.checked event could not be written ({exc}), so the ticket "
                         f"records no run. Run it again once the tracker takes comments.\n")
        recorded = False
    else:
        recorded = True
    return result.returncode if recorded else NOT_RECORDED


# The exit of a run whose criteria ran and whose result could not be written on the
# ticket. It is not 1: a caller reads 1 as "the criteria are red", and nothing says so.
NOT_RECORDED = 4


def blocker_fold(number: int) -> dict | None:
    """The events of blocker `number` folded, or None when the tracker did not answer."""
    try:
        return events.fold(fetch_comments(number), issue=number)
    except (OSError, ValueError, subprocess.CalledProcessError, TrackerReadError):
        return None


def refusals(number: int, ticket: dict, me: str, branch: str,
             dirty: list[str]) -> list[tuple[str, str]]:
    """Why this ticket is not ready to be worked on, in the order a worker would hit it.

    Each refusal is `(reason, sentence)`: the reason is the `ticket.refused` event's
    `reason` field, one of `events.REFUSALS`, and the sentence is its first line.

    A blocker holds until its work has landed, as `events.blocker_hold` reads it off the
    blocker's own events — the same answer the dispatch skill's frontier gives, so a
    ticket that skill starts is never refused here for a blocker it had let go.

    Every one of these ends in `stop`. Five of the six conditions are set up before a
    worker exists — `dispatch.sh` opens the worktree on `issue-<n>` and checks the state,
    the labels and the blockers before it starts anyone — so a worker that sees one of
    them has found a fault upstream of itself, not a task. Working around it (switching
    branches, taking someone else's ticket) does more damage than stopping.

    The sixth, the tree, is the one whose answer depends on who holds the ticket, because
    a worker comes through this run every time it enters the ticket — the turn it is
    prompted back into after a review included (Work a ticket's claim and `RESUME:`). On that turn
    the uncommitted tracked changes are its own work from an earlier turn, so the tree
    refuses only while the claim is not this account's: read as an upstream fault they
    end a live worker's hold, and the ticket then says `live: false` of a session that
    goes on posting events. What keeps them from reaching the base branch uncommitted is
    the closeout, which refuses a draft while a tracked file is uncommitted.

    The comment this posts on the ticket is what the user reads in the morning.
    """
    out = []
    if branch != f"issue-{number}":
        out.append(("wrong-branch",
                    f"NOT_READY: branch is {branch or '(detached)'}, not issue-{number}; "
                    f"dispatch opens this worktree on issue-{number}, so you were started "
                    f"somewhere else — stop, do not switch branches yourself"))
    holders = [a.get("login", "") for a in ticket.get("assignees", []) if a.get("login")]
    if dirty and me not in holders:
        out.append(("dirty-tree",
                    f"NOT_READY: {len(dirty)} tracked files have uncommitted changes and "
                    f"#{number} is claimed by {', '.join(holders) or 'nobody'}, not by you "
                    f"({me}); they were left here before your claim, and are not yours to "
                    f"commit or discard — stop and leave the tree as you found it"))
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
    holding = []
    for node in ticket.get("blockedBy", {}).get("nodes", []):
        state = node.get("state") or ""
        why = events.blocker_hold(state, blocker_fold(node["number"]) if state == "CLOSED"
                                  else None)
        if why:
            holding.append(f"#{node['number']}" + ("" if why == "open" else f" ({why})"))
    if holding:
        out.append(("blocked",
                    f"NOT_READY: #{number} is blocked by {', '.join(holding)}; stop — "
                    f"`dispatch.sh` starts this ticket again once those land, so do not "
                    f"wait or retry"))
    others = [h for h in holders if h != me]
    if others:
        out.append(("claimed-by-other",
                    f"NOT_READY: #{number} is assigned to {', '.join(others)}, not you ({me}); "
                    f"stop rather than work on someone else's ticket"))
    return out


def check_run_outcome(returncode: int, summary: str) -> str | None:
    """The `ticket.checked` result of one gate-check process, or None if it could not start."""
    if returncode == 2:
        return None
    if returncode == 0:
        return "met"
    if summary.startswith("HANDOFF REQUIRED:"):
        return "handoff"
    return "unmet"


def run_baseline_if_needed(number: int, root: Path) -> int:
    """Run the baseline once for the newest `worker.started.base`, if that run is missing.

    A red result does not refuse the claim. Checkout failures are written as an unmet
    `ticket.checked` of run `baseline` when the base commit is known, and otherwise named
    on stderr. Environment preparation failures return 2 and stop `--preflight`.
    """
    try:
        comments = fetch_comments(number)
    except TrackerReadError as exc:
        sys.stderr.write(f"#{number}: baseline run did not start ({exc})\n")
        return 0
    started = events.newest(comments, "worker.started")
    base = (started or {}).get("payload", {}).get("base")
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        sys.stderr.write(f"#{number}: baseline run did not start "
                         f"(no worker.started.base commit)\n")
        return 0
    existing = newest_run(comments, "baseline")
    if existing and existing["payload"].get("commit") == base:
        return 0
    try:
        body = fetch_body(number)
    except TrackerReadError as exc:
        sys.stderr.write(f"#{number}: baseline run did not start ({exc})\n")
        return 0
    return run_baseline(number, body, base, root, started["payload"].get("into"))


def run_worktree_environment(worktree: Path, step: str) -> int:
    script = worktree / "scripts" / "env"
    if not script.exists():
        return 0
    try:
        result = subprocess.run([str(script), step, str(worktree)], cwd=worktree,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace")
    except OSError as exc:
        output, status = str(exc), 2
    else:
        output, status = result.stdout, result.returncode
    if status:
        sys.stderr.write(f"scripts/env {step} failed for {worktree} (exit {status}); "
                         "fix scripts/env and retry\n")
        sys.stderr.write("\n".join(output.splitlines()[-10:]) + "\n")
        return 2
    if output:
        sys.stderr.write(output)
    return 0


def _remove_baseline_checkout(root: Path, worktree: Path) -> None:
    run_worktree_environment(worktree, "down")
    subprocess.run(["git", "worktree", "remove", "--force", "--force", str(worktree)],
                   cwd=root, capture_output=True, text=True)
    shutil.rmtree(worktree, ignore_errors=True)
    subprocess.run(["git", "worktree", "prune"],
                   cwd=root, capture_output=True, text=True)


def run_baseline(number: int, body: str, base: str, root: Path, into: str | None) -> int:
    """The criteria at `base`, in the main checkout's `.worktrees/baseline-<n>`."""
    items = parse_criteria("\n".join(section(body, "Acceptance criteria")))
    skipped = []
    runnable = items
    tmp = Path(tempfile.mkdtemp(prefix="mmw-baseline-"))
    worktree = None
    try:
        listed = subprocess.run(["git", "worktree", "list", "--porcelain"],
                                cwd=root, capture_output=True, text=True)
        main = next((line.removeprefix("worktree ") for line in listed.stdout.splitlines()
                     if line.startswith("worktree ")), "")
        short = base[:12]
        if listed.returncode != 0 or not main:
            why = (listed.stderr or listed.stdout or
                   "git worktree list returned no main checkout").strip()
            _post_baseline(number, body, base, runnable=[], skipped=[c["id"] for c in items],
                           outcome="unmet",
                           line=f"Baseline run on {short}: unmet ({why})")
            return 0
        worktree = Path(main) / ".worktrees" / f"baseline-{number}"
        worktree.parent.mkdir(parents=True, exist_ok=True)
        _remove_baseline_checkout(root, worktree)
        added = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), base],
            cwd=root, capture_output=True, text=True)
        if added.returncode != 0 or not worktree.is_dir():
            why = (added.stderr or added.stdout or "git worktree add failed").strip()
            _post_baseline(number, body, base, runnable=[], skipped=[c["id"] for c in items],
                           outcome="unmet",
                           line=f"Baseline run on {short}: unmet ({why})")
            return 0
        for step in ("setup", "up"):
            if run_worktree_environment(worktree, step):
                return 2
        if not runnable:
            _post_baseline(number, body, base, runnable=[], skipped=skipped, outcome="unmet",
                           line=f"Baseline run on {short}: nothing ran (all skipped)")
            return 0
        ledger_dir = tmp / "ledger"
        ledger_dir.mkdir()
        lines = []
        for item in runnable:
            pending = dict(item)
            pending["ticked"] = False
            pending["evidence"] = pending.get("evidence") or "pending"
            lines.extend(criterion_block(pending).splitlines())
            lines.append("")
        ledger = write_ledger(body, ledger_dir, lines)
        cmd = ["node", str(GATE_CHECK), "--cwd", str(worktree),
               "--timeout", str(check_timeout(body)), str(ledger)]
        env = criterion_environment(number, into)
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=worktree, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        summary = next((line for line in printed.splitlines() if SUMMARY_RE.match(line)), "")
        updated = ledger.read_text(encoding="utf-8").rstrip("\n") if ledger.is_file() else ""
        outcome = check_run_outcome(result.returncode, summary)
        if outcome is None:
            _post_baseline(number, body, base, runnable=[], skipped=[c["id"] for c in items],
                           outcome="unmet",
                           line=f"Baseline run on {short}: could not start")
            return 0
        ran = parse_criteria(updated) if updated else runnable
        _post_baseline(number, body, base, runnable=ran, skipped=skipped, outcome=outcome,
                       line=f"Baseline run on {short}: {summary or outcome}",
                       updated=updated)
    except (OSError, subprocess.CalledProcessError, events.EventError) as exc:
        sys.stderr.write(f"#{number}: baseline run did not complete ({exc})\n")
    finally:
        if worktree is not None:
            _remove_baseline_checkout(root, worktree)
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


def _post_baseline(number: int, body: str, base: str, runnable: list[dict],
                   skipped: list[str], outcome: str, line: str,
                   updated: str = "") -> None:
    results = [{"id": c["id"],
                "met": bool(c.get("ticked") and c.get("evidence")
                            and c.get("evidence") != "pending"),
                "evidence": c.get("evidence") or "pending"} for c in runnable]
    abandons = parse_abandons(updated) if updated else []
    post_event(number, "ticket.checked", line, updated,
               run="baseline", commit=base, result=outcome,
               counts=tally(runnable, abandons) if runnable else {
                   "met": 0, "unmet": 0, "abandoned": 0, "total": 0},
               criteria=results, failed=[r["id"] for r in results if not r["met"]],
               abandons=abandons or None, skipped=skipped or None,
               shape=shape_digest(section(body, "Acceptance criteria")),
               actor="worker", stage=events.checked_stage("baseline", "worker"))


# The steps of mmw-mode's Work a ticket playbook a `RESUME:` line can name, by their
# titles there; the dispatch skill's `check-interfaces.py` finds each one in that file.
RESUME_STEPS = ("Integrate and run every criterion", "Post the decisions comment",
                "Start the reviewer", "Read the review", "Audit",
                "Run every criterion one final time")


def failed_checks_quote(record: dict | None) -> str | None:
    body = (record or {}).get("body") or ""
    for line in body.splitlines():
        stripped = line.strip()
        for token in ("Failed checks:", "Broken landed criteria:"):
            if stripped.startswith(token):
                return stripped
            at = line.find(token)
            if at >= 0:
                return line[at:]
    return None


def resume_at(comments: list[str], head: str) -> str | None:
    integrate, decisions, start_reviewer, read_review, audit, final_run = RESUME_STEPS
    self_run = newest_run(comments, "self")
    reviewed = events.newest(comments, "reviewer.reported")
    reverify = newest_run(comments, "reverify", actor="worker")
    state = events.fold(comments)
    if not (self_run or reviewed or state["decided"] or reverify):
        return None
    ordered = state["events"]
    terminal = next((e["event"] for e in reversed(ordered)
                     if e["event"] in ("ticket.passed", "ticket.returned", "ticket.bounced")),
                    None)
    if terminal in ("ticket.returned", "ticket.bounced"):
        step = f"{integrate}, then {final_run} onward ({terminal})"
        if terminal == "ticket.bounced":
            quote = failed_checks_quote(events.newest(comments, "ticket.bounced"))
            if quote:
                return step + "\n" + quote
        return step
    if self_run is None:
        return f"{integrate} (no run of your own)"
    if not state["decided"]:
        return f"{decisions} (no worker.decided)"
    if reviewed is None:
        if events.live_of(state, "reviewer"):
            return f"{read_review} (reviewer.started, no reviewer.reported yet)"
        return f"{start_reviewer} (worker.decided, no reviewer.reported)"
    newest = final_worker_run(comments)
    if newest["comment"] <= reviewed["comment"]:
        return f"{read_review} (reviewer.reported, no run of your own since)"
    if newest["payload"].get("commit") != head:
        return f"{audit} (a run of your own since reviewer.reported, and commits after it)"
    if not ordered or newest["comment"] == ordered[-1]["comment"]:
        return f"{final_run} (a run of your own on HEAD since reviewer.reported)"
    return None


def run_preflight(number: int) -> int:
    """Claim the ticket, or say on the ticket itself why it cannot be claimed.

    Either way one event lands on the ticket: `ticket.refused` with the first refusal's
    reason, or `ticket.claimed` once the claim is made. A claim whose event could not be
    written still holds — the tracker's assignee is the claim — and says so on stderr.
    After a successful claim, the criteria are run once at the
    newest `worker.started.base` (a `ticket.checked` of run `baseline`) unless that run
    is already on the ticket; a red result does not refuse.
    """
    root = repo_root()
    ticket = fetch_ticket(number)
    me = gh_login()
    branch = current_branch(root)
    dirty = dirty_tracked(root)
    problems = refusals(number, ticket, me, branch, dirty)
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
    if run_baseline_if_needed(number, root) == 2:
        return 2
    print(f"READY: #{number} claimed on issue-{number}")
    try:
        comments = fetch_comments(number)
        own_run = newest_run(comments, "self")
        if own_run is not None and own_run["payload"].get("shape") != shape_digest(
                section(fetch_body(number), "Acceptance criteria")):
            resume = None
            sys.stderr.write(f"#{number}: acceptance criteria were recut since your newest "
                             f"own run; read the ticket and start from the code step\n")
        else:
            resume = resume_at(comments, git("rev-parse", "HEAD", cwd=root))
    except TrackerReadError as exc:
        resume = None
        sys.stderr.write(f"#{number}: could not read where to resume ({exc}); read the "
                         f"ticket's comments by hand\n")
    if resume:
        head_line, _, rest = resume.partition("\n")
        print(f"RESUME: {head_line}")
        if rest:
            print(rest)
    # Getting here with a dirty tree means the claim was already this account's, so the
    # changes came in under it: this is a worker back on its own work, and the only thing
    # left to say is where they have to be by the closing steps.
    if dirty:
        print(f"CARRIED: {len(dirty)} tracked files have uncommitted changes, made under "
              f"the claim you already held on #{number}; commit them on issue-{number} "
              f"before the closing steps — --closeout refuses a draft while a tracked "
              f"file is uncommitted.")
    return 0


def review_finding_problems(draft: str, comments: list[str], number: int) -> list[str]:
    """The newest review's In-ticket rows must each have a handled draft row.

    Compare the whole source-bearing row, not just its path or claim. Counting rows
    prevents one response from silently standing in for duplicate findings.
    """
    review_event = events.newest(comments, "reviewer.reported") or {}
    try:
        if review_event:
            require_in_ticket(review_event.get("body") or "", review_event.get("comment"),
                              number)
        required = in_ticket_findings(review_event.get("body") or "",
                                      review_event.get("comment"))
    except ValueError as exc:
        return [str(exc)]
    if not required:
        return []
    lines = draft.splitlines()
    start = next((i + 1 for i, line in enumerate(lines)
                  if line.strip() == "Review findings:"), None)
    shown = []
    if start is not None:
        for line in lines[start:]:
            if not line.strip():
                break
            shown.append(line.strip())
    matched = Counter()
    for line in shown:
        for row in required:
            prefix = row + " — "
            if not line.startswith(prefix):
                continue
            response = line[len(prefix):]
            if re.fullmatch(r"fixed \S+|refuted: .+", response):
                matched[row] += 1
            break
    needed = Counter(required)
    problems = []
    for row, count in needed.items():
        if matched[row] < count:
            problems.append(f"the newest review's ## In-ticket finding is missing or "
                            f"has no `fixed <commit>` / `refuted: <evidence>` response "
                            f"in `Review findings:`: {row}; copy the review row and "
                            "record its disposition in the closeout draft")
    return problems


# A repository check's bounce keeps the first ten error or path:line lines and the
# last thirty, then stops at what one GitHub issue comment can hold.
CHECKS_ERROR_LINES = 10
CHECKS_TAIL_LINES = 30
COMMENT_BODY_LIMIT = 65536
# One excerpt line, and one command's excerpt, stay under this so the failed-check
# JSON can travel in the environment to the bounce. The log holds the rest.
EXCERPT_LINE_LIMIT = 8000
EXCERPT_BUDGET = 48000
FAILURE_LINES = HERE / "gate-check" / "lib" / "failure-lines.mjs"


# The repository's own check, at its root: the default tier runs on every tree that
# lands. It exits 0 green, 1 red, 2 when this machine cannot run it.
REPOSITORY_CHECK = Path("scripts") / "check"
FAIL_STEP_RE = re.compile(r"^FAIL\s+(\S+)", re.M)


def repository_check_missing(root: Path) -> str | None:
    """Why `scripts/check` at `root` cannot be run, or None when it is an executable file."""
    path = Path(root) / REPOSITORY_CHECK
    if path.is_file() and os.access(path, os.X_OK):
        return None
    what = f"{path} is not executable" if path.exists() else f"{path} does not exist"
    return (f"{what}; write it with the Set up code checkers playbook, which the setup-mmw "
            "skill runs")


def _checks_excerpt(output: str) -> str:
    """The check's excerpt from `failure-lines.mjs`, or a short note when it cannot be built."""
    if not output.strip():
        return ""
    try:
        proc = subprocess.run(
            ["node", str(FAILURE_LINES), str(CHECKS_ERROR_LINES), str(CHECKS_TAIL_LINES)],
            input=output, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"could not build the excerpt: {exc}"
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip() or f"node exited {proc.returncode}"
        return f"could not build the excerpt: {detail[:500]}"
    return proc.stdout


def _cap_excerpt(text: str) -> str:
    """Keep the excerpt small enough to ride along to the bounce in the environment."""
    lines = [line[:EXCERPT_LINE_LIMIT] for line in text.splitlines()]
    while lines and sum(len(line) + 1 for line in lines) > EXCERPT_BUDGET:
        lines.pop()
    return "\n".join(lines)


def _failed_row(command: str, tail: str, exit_code: int | None = None,
                log: str | None = None) -> dict:
    row: dict = {"command": command, "tail": tail}
    if type(exit_code) is int:
        row["exit"] = exit_code
    if log:
        row["log"] = log
    return row


def _write_check_log(worktree: Path | str | None, ticket: str | int | None, seq: int,
                     raw: str, started: list[bool]) -> str | None:
    """The full output of one failed check, in the ticket worktree.

    The first failure of a run replaces `.scratch/checks/<ticket>/`. A missing worktree
    is left missing: the merge still bounces, and the excerpt is what the comment carries.
    A log that cannot be written does too — the red check is the event.
    """
    if worktree is None or ticket in (None, ""):
        return None
    root = Path(worktree)
    if not root.is_dir():
        return None
    folder = root / ".scratch" / "checks" / str(ticket)
    try:
        if not started[0]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True)
            started[0] = True
        (folder / f"{seq}.log").write_text(raw, encoding="utf-8")
    except OSError:
        return None
    return f".scratch/checks/{ticket}/{seq}.log"


def _check_heading(row: dict) -> str:
    command = " ".join(str(row.get("command") or "?").split())
    exit_code = row.get("exit")
    if type(exit_code) is int:
        command = f"{command} exit {exit_code}"
    steps = [str(step) for step in row.get("steps") or []]
    if steps:
        command = f"{command} (failed steps: {', '.join(steps)})"
    return command


def _comment_size(prefix_len: int, summary: str, rest: str, commands: list) -> int:
    """How long the bounce comment is, using a payload no smaller than a real one."""
    line = prefix_len + len(events.neutralise(f" Failed checks: {summary}."))
    cleaned = events.neutralise(rest or "").strip("\n")
    prose = line + (2 + len(cleaned) if cleaned else 0)
    payload = {
        "v": events.VERSION,
        "event": "ticket.bounced",
        "stage": "land",
        "actor": "main",
        "spec": 10**9,
        "ticket": 10**9,
        "at": "2026-01-01T00:00:00Z",
        "reason": "checks",
        "commit": "f" * 40,
        "into": "x" * 80,
        "commands": commands,
    }
    return prose + 2 + len(events.block(payload)) + 1


def _summary_of(rows: list[dict]) -> str:
    return "; ".join(_check_heading(row) for row in rows)


def _rest_of(rows: list[dict], excerpts: list[list[str]]) -> str:
    blocks = []
    for row, lines in zip(rows, excerpts):
        parts = [_check_heading(row)]
        log = row.get("log")
        if isinstance(log, str) and log:
            parts.extend(["", log])
        if lines:
            parts.extend(["", *lines])
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def _commands_of(rows: list[dict], excerpts: list[list[str]]) -> list[dict]:
    commands = []
    for row, lines in zip(rows, excerpts):
        item: dict = {"command": row.get("command", "?"), "tail": "\n".join(lines)}
        if type(row.get("exit")) is int:
            item["exit"] = row["exit"]
        if row.get("log"):
            item["log"] = row["log"]
        if row.get("steps"):
            item["steps"] = list(row["steps"])
        commands.append(item)
    return commands


def _fit_last_line(rows: list[dict], excerpts: list[list[str]], index: int,
                   prefix_len: int) -> None:
    original = excerpts[index][0]

    def size_with(text: str) -> int:
        excerpts[index] = [text] if text else []
        return _comment_size(prefix_len, _summary_of(rows), _rest_of(rows, excerpts),
                             _commands_of(rows, excerpts))

    if size_with(original) <= COMMENT_BODY_LIMIT:
        excerpts[index] = [original]
        return
    if size_with("") > COMMENT_BODY_LIMIT:
        excerpts[index] = []
        return
    lo, hi, best = 0, len(original), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if size_with(original[:mid]) <= COMMENT_BODY_LIMIT:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    excerpts[index] = [original[:best]] if best else []


def _shrink_until_it_fits(rows: list[dict], excerpts: list[list[str]], prefix_len: int) -> None:
    for _ in range(64):
        if _comment_size(prefix_len, _summary_of(rows), _rest_of(rows, excerpts),
                         _commands_of(rows, excerpts)) <= COMMENT_BODY_LIMIT:
            return
        index = max(range(len(rows)), key=lambda i: len(str(rows[i].get("command") or "")))
        command = " ".join(str(rows[index].get("command") or "").split())
        if len(command) > 8:
            rows[index]["command"] = command[: max(8, len(command) // 2)]
            continue
        if rows[index].get("log"):
            rows[index]["log"] = ""
            continue
        return


def checks_bounce_prose(rows: list | None, prefix_len: int = 0) -> dict:
    """The checks bounce: one summary line, one paragraph per command, and the JSON.

    `prefix_len` is the merge sentence already written before ` Failed checks:`. The
    returned `commands` carry the excerpt that still fits, so the posted comment stays
    inside `COMMENT_BODY_LIMIT`. The full output stays in the log the paragraph names.
    """
    copied = [dict(row) for row in (rows or []) if isinstance(row, dict)]
    excerpts = [(row.get("tail") or "").splitlines() for row in copied]
    original = [len(lines) for lines in excerpts]

    def over() -> bool:
        return _comment_size(prefix_len, _summary_of(copied), _rest_of(copied, excerpts),
                             _commands_of(copied, excerpts)) > COMMENT_BODY_LIMIT

    while over():
        index = next((i for i in range(len(excerpts) - 1, -1, -1) if excerpts[i]), None)
        if index is None:
            break
        if len(excerpts[index]) == 1:
            _fit_last_line(copied, excerpts, index, prefix_len)
            break
        excerpts[index].pop()
    _shrink_until_it_fits(copied, excerpts, prefix_len)
    summary = _summary_of(copied)
    rest = _rest_of(copied, excerpts)
    commands = _commands_of(copied, excerpts)
    dropped = sum(max(0, original[i] - len(excerpts[i])) for i in range(len(copied)))
    if dropped:
        note = f"+{dropped} more"
        candidate = rest + ("\n\n" if rest else "") + note
        if _comment_size(prefix_len, summary, candidate, commands) <= COMMENT_BODY_LIMIT:
            rest = candidate
    return {"summary": summary, "rest": rest, "commands": commands}


def _run(path: Path, root: Path, env: dict, *args: str) -> tuple[int, str]:
    """`(exit code, combined output)` of one run, however long it takes: no time limit
    turns a slow test into a failure."""
    proc = subprocess.run([str(path), *args], cwd=root, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace")
    return proc.returncode, proc.stdout or ""


def run_repository_check(root: Path | str, base_ref: str,
                         worktree: Path | str | None = None,
                         ticket: str | int | None = None, tier: str = "default") -> dict:
    """Run one tier of `scripts/check` at `root` with `MMW_BASE_REF=base_ref`: the
    default tier, or `--all` when `tier` is `all`.

    Returns `{"status", "failed", "detail", "proof"}`. `proof` identifies a green or red run,
    the fields of its record (`proof_fields`), or None: a run on a tree with uncommitted
    or untracked files proved nothing about any commit. `status` is `pass` (exit 0), `red` (exit 1), `cannot-run`
    (exit 2, any other exit, or the script would not start: this machine cannot run
    it, which says nothing about the tree) or `missing` (no executable `scripts/check`).
    `failed` is one row for a red run: `command`, `tail` (the excerpt), `exit`, `steps`
    (the `FAIL <step>` lines it printed), and `log` when the full output was written
    under `worktree`'s `.scratch/checks/<ticket>/`. `detail` says what happened, with
    the last lines and the log's path, for every status but `pass`.
    """
    root = Path(root)
    missing = repository_check_missing(root)
    if missing:
        return {"status": "missing", "failed": [], "detail": missing, "proof": None}
    path = root / REPOSITORY_CHECK
    env = os.environ.copy()
    env["MMW_BASE_REF"] = base_ref
    before = tree_identity(root, base_ref)
    try:
        code, output = _run(path, root, env, *(["--all"] if tier == "all" else []))
    except OSError as exc:
        return {"status": "cannot-run", "failed": [],
                "detail": f"{path} could not be started: {exc}", "proof": None}
    proof = None
    if code in (0, 1) and before is not None and tree_identity(root, base_ref) == before:
        steps = re.findall(r"^(?:PASS|FAIL)\s+(\S+)", output, re.M)
        proof = proof_fields(tier, *before, steps)
    if code == 0:
        return {"status": "pass", "failed": [], "detail": "", "proof": proof}
    log = _write_check_log(worktree, ticket, 1, output, [False])
    excerpt = _cap_excerpt(_checks_excerpt(output))
    where = f"; full output in {Path(worktree) / log}" if log else ""
    if code == 1:
        row = _failed_row(str(REPOSITORY_CHECK), excerpt, code, log)
        row["steps"] = FAIL_STEP_RE.findall(output)
        heading = _check_heading(row)
        return {"status": "red", "failed": [row], "proof": proof,
                "detail": f"{heading} in {root}{where}:\n{excerpt}".rstrip()}
    what = ("exited 2: this machine cannot run it" if code == 2 else
            f"exited {code}, which is none of 0 (green), 1 (red) and 2 (cannot run)")
    return {"status": "cannot-run", "failed": [], "proof": None,
            "detail": f"{path} {what}{where}:\n{excerpt}".rstrip()}


def tree_identity(root: Path, base_ref: str) -> tuple[str, str] | None:
    """`(commit, base commit)` of a clean checkout at `root`, or None: a checkout with
    uncommitted or untracked files is a tree no commit names, and an unreadable ref
    names nothing."""
    try:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                                capture_output=True, text=True, check=True).stdout
        head = git("rev-parse", "HEAD", cwd=root)
        base = git("rev-parse", "--verify", f"{base_ref}^{{commit}}", cwd=root)
    except (OSError, subprocess.CalledProcessError):
        return None
    if status.strip() or not all(re.fullmatch(r"[0-9a-f]{40}", v or "") for v in (head, base)):
        return None
    return head, base


def proof_fields(tier: str, commit: str, base: str, steps: list[str]) -> dict:
    return {"tier": tier, "commit": commit, "base": base,
            "machine": socket.gethostname(), "steps": steps}


def covering_proof(comments: list, event: str, commit: str, base: str) -> dict | None:
    """The newest green record among `comments` that proves the default tier of `commit`
    against `base` on this machine: a default-tier record of that exact commit and base,
    or an `all` record of that commit with any base, since `--all` runs everything any
    selection can. A `base_red` record is not green proof. None when no record covers
    it; the step then runs."""
    machine = socket.gethostname()
    found = None
    for comment in events.normalise(comments):
        what, payload = events.parse(comment["body"])
        if what != "event" or payload["event"] != event:
            continue
        if payload.get("base_red"):
            continue
        if event == "ticket.checked" and payload.get("run") != "repository":
            continue
        if (payload.get("result") == "met" and payload.get("commit") == commit
                and payload.get("machine") == machine
                and (payload.get("tier") == "all"
                     or (payload.get("tier") == "default" and payload.get("base") == base))):
            found = payload
    return found


def push_ticket_branch(number: int, root: Path, commit: str) -> str | None:
    """Push the final-run commit to `origin/issue-<n>` without rewriting history."""
    ref = f"refs/heads/issue-{number}"
    try:
        pushed = subprocess.run(
            ["git", "push", "origin", f"{commit}:{ref}"], cwd=root,
            capture_output=True, text=True,
        )
        if pushed.returncode != 0:
            detail = " ".join((pushed.stderr or pushed.stdout).strip().splitlines())
            return (f"origin rejected {commit} for issue-{number}: "
                    f"{detail[:500] or f'git push exited {pushed.returncode}'}. The ticket "
                    f"remains open; resolve the rejection and run --closeout again. "
                    f"No force-push was used")
        remote = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", ref], cwd=root,
            capture_output=True, text=True,
        )
    except OSError as exc:
        return (f"git could not reach origin for issue-{number} at final-run commit {commit}: "
                f"{exc}. The ticket remains open; fix Git access and run --closeout again")
    remote_commit = (remote.stdout.strip().split() or [""])[0]
    if remote.returncode != 0 or remote_commit != commit:
        detail = " ".join((remote.stderr or remote.stdout).strip().splitlines())
        resolved = remote_commit or "nothing"
        return (f"origin/issue-{number} could not be confirmed at final-run commit {commit}: "
                f"{detail[:500] or f'it resolved to {resolved}'}. The ticket "
                f"remains open; confirm the remote and run --closeout again")
    return None


class CloseoutBusy(RuntimeError):
    """Another closeout still owns this ticket's local critical section."""


@contextmanager
def closeout_lock(root: Path, number: int):
    """Exclude overlapping closeouts of one ticket in this repository."""
    common = git("rev-parse", "--git-common-dir", cwd=root)
    if not common:
        raise OSError("git could not locate this repository's common directory")
    directory = Path(common)
    if not directory.is_absolute():
        directory = root / directory
    path = directory / f"mmw-closeout-{number}.lock"
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise CloseoutBusy(f"another --closeout for #{number} is still running") from None
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def completed_closeout(ticket: dict, comments: list[str], first: str,
                       head: str) -> str | None:
    """The matching closeout result already recorded for this commit, if any."""
    state = events.fold(comments)
    outcome = state.get("outcome") or {}
    payload = outcome.get("payload") or {}
    if payload.get("commit") != head:
        return None
    if first == "ALL MET" and state.get("passed") \
            and ticket.get("state") == "CLOSED" \
            and str(ticket.get("stateReason") or "").upper() == "COMPLETED":
        return "closed"
    labels = {label.get("name") for label in ticket.get("labels") or []}
    assigned = bool(ticket.get("assignees"))
    if first.startswith("HANDOFF REQUIRED") and state.get("returned") \
            and ticket.get("state") == "OPEN" and not assigned \
            and "needs-triage" in labels and "ready-for-agent" not in labels:
        return "handed"
    return None


def run_closeout(number: int, draft_path: Path, check_only: bool) -> int:
    """Serialize one ticket's closeout, then check and apply it."""
    try:
        with closeout_lock(repo_root(), number):
            return _run_closeout(number, draft_path, check_only)
    except (CloseoutBusy, OSError) as exc:
        return refuse(f"closeout refused: {exc}. Nothing was run or written; retry the "
                      "same command after the active closeout finishes")


def _run_closeout(number: int, draft_path: Path, check_only: bool) -> int:
    """Check the closing comment against the ticket and the repository, then post it."""
    raw = draft_path.read_text(encoding="utf-8")
    comments = fetch_comments(number)
    # The first line and `Counts:` are computed here, from the draft's own `ABANDON:`
    # lines and criteria, and written into what posts — never taken as the worker wrote
    # them.
    first, counts = draft_summary(raw)
    draft = rewrite_summary(raw, first, counts)
    passed = first == "ALL MET"
    ticket = fetch_ticket(number)
    head = git("rev-parse", "HEAD")
    completed = completed_closeout(ticket, comments, first, head)
    if completed:
        action = "CLOSED" if completed == "closed" else "HANDED BACK"
        print(f"{action}: #{number} was already recorded at {head}")
        return 0
    body = fetch_body(number)
    started, started_problem = newest_worker_started(number, comments)
    base = (started or {}).get("base")
    into = (started or {}).get("into") if passed else None
    problems = draft_problems(draft, comments)
    problems += verified_problems(draft, body, comments, first)
    problems += review_finding_problems(draft, comments, number)
    problems += event_problems(comments)
    if started_problem:
        problems.append(started_problem)
    elif passed and not into:
        problems.append(f"#{number}'s newest worker.started carries no `into`. Only worker "
                        f"dispatch writes this field, so its absence is a pipeline fault. "
                        f"Run `verify-ticket.py {number} --sub-issue fault <file>`, then stop.")
    if base:
        problems += git_problems(base, repo_root())
    me = gh_login()
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

    if passed and pending is None:
        problem = push_ticket_branch(number, repo_root(), head)
        if problem:
            sys.stderr.write(f"closeout refused: {problem}\n")
            return 1

    # The draft is the comment: its first line for a person, the rest as written, and the
    # event block after it. `abandoned` carries every `ABANDON:` line — on a pass only
    # `decision` ones can be there, on a hand back they are the reason it came back.
    abandons = parse_abandons(draft)
    event = "ticket.passed" if passed else "ticket.returned"
    fields = dict(spec=spec_field(ticket), commit=head or None,
                  branch=current_branch(repo_root()) or None,
                  counts=counts,
                  abandoned=[{"ac": a["ac"], "kind": a["kind"], "reason": a["reason"]}
                             for a in abandons] or None)
    if passed:
        fields["into"] = into
    # The state change first, then the event that announces it: the event is what wakes
    # the orchestrator and what `advance` merges on, so it must never stand on a ticket the
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
                         f"not be posted ({exc}), so nothing wakes the orchestrator and nothing "
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


def lint_batch_graph(spec: int, numbers: list[int],
                     entries: list[dict] | None = None) -> int:
    """Check that `numbers`, the sub-issues of `spec`, form a startable graph.

    `entries` replaces the tracker's blocking edges with ones read elsewhere: the
    `BLOCKED BY:` headers of a directory of drafts, whose ids are draft names."""
    if not numbers and not entries:
        print(f"  ERROR #{spec} has no sub-issues — publish tickets as sub-issues of the "
              f"spec, or the graph cannot be checked  [no-sub-issues]")
        return 1
    if entries is None:
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
        print(f"level {level}: " + ", ".join(ref(t) for t in sorted(by_level[level])))
    for line in waiting_outside(entries):
        print(line)
    return 0


def criteria_lines(body: str) -> list[tuple[str, str, str]]:
    """`(id, CHECK, EXPECT)` per criterion; a missing attribute reads as an empty string."""
    return [(c["id"], c["check"], c["expect"])
            for c in parse_criteria("\n".join(section(body, "Acceptance criteria")))]


def lint_worker(labels: list[str]) -> tuple[list[str], list[str]]:
    """Which worker this ticket gets, as the tracker's labels say: (errors, warnings).

    `dispatch.sh` reads the label and nothing else. A ticket carrying both is one no start
    can place, an error. A ticket carrying none starts on the default row, which runs; it
    is a warning, because that row may not be the one the ticket was written for.

    A ticket outside the agent queue is clean either way: what it holds is one thing for the
    user to look at, and no worker is started on it.
    """
    if "ready-for-agent" not in labels:
        return [], []
    marked = sorted(name for name in labels if WORKER_LABEL_RE.match(name or ""))
    if len(marked) > 1:
        return [f"carries {len(marked)} worker labels ({', '.join(marked)}), and it takes one"], []
    if not marked:
        return [], ["carries no worker label, so it starts on the default row: add "
                    "`junior-worker` or `senior-worker` if it was written for another"]
    return [], []


def lint_expectations(body: str) -> list[str]:
    """`$` in an EXPECT regex without the `m` flag is a criterion that can never pass.

    gate-check hands the CHECK's whole output — stdout, then stderr — to the regex
    (`runCheck` in `gate-check.mjs`), and a command's output ends in a newline. JavaScript's `$`
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


def check_runners(check: str) -> set[str]:
    found = set()
    prefixes = {'uv': ('run',), 'pnpm': (), 'npx': ()}
    for stage in shell_stages(check):
        try:
            words = shlex.split(stage, comments=True)
        except ValueError:
            continue
        while words:
            command = Path(words[0]).name
            if re.match(r'^[A-Za-z_]\w*=', words[0]):
                words = words[1:]
            elif re.fullmatch(r'python(?:\d+(?:\.\d+)*)?', command) and words[1:2] == ['-m']:
                words = words[2:]
            elif command in prefixes and tuple(words[1:1 + len(prefixes[command])]) == prefixes[command]:
                words = words[1 + len(prefixes[command]):]
                if words[:1] == ['exec']:
                    words = words[1:]
                while words and words[0] in ('--yes', '-y', '--quiet', '-q', '--silent', '--'):
                    words = words[1:]
            else:
                if command in ('pytest', 'vitest'):
                    found.add(command)
                break
    return found


def lint_runner_expectations(body: str) -> list[str]:
    runners = json.loads((HERE / "runner-summaries.json").read_text(encoding="utf-8"))
    findings = []
    for gate_id, check, expect in criteria_lines(body):
        selected = check_runners(check)
        if len(selected) > 1:
            standards = '; '.join(f"{runner} EXPECT: {runners[runner]['expect']}"
                                  for runner in sorted(selected))
            findings.append(f"{gate_id}: CHECK runs pytest and vitest; write one criterion "
                            f"per runner. {standards}")
            continue
        for runner in selected:
            contract = runners[runner]
            if expect == contract["expect"]:
                continue
            script = r'''
const {expect, samples} = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
try {
  const parsed = expect.match(/^\/([\s\S]*)\/([a-z]*)$/);
  const wrong = samples.find(sample => {
    const matched = parsed
      ? new RegExp(parsed[1], parsed[2]).test(sample.output)
      : sample.output.includes(expect);
    return matched !== sample.success;
  });
  console.log(JSON.stringify(wrong ? {
    reason: wrong.success ? 'rejects success' : 'accepts failure',
    summary: wrong.summary
  } : {}));
} catch (error) {
  console.log(JSON.stringify({reason: 'is invalid', summary: error.message}));
}
'''
            try:
                result = subprocess.run(
                    ["node", "-e", script],
                    input=json.dumps({"expect": expect, "samples": contract["samples"]}),
                    capture_output=True, text=True, timeout=10, check=True,
                )
                wrong = json.loads(result.stdout)
                detail = (f" {wrong['reason']}: {wrong['summary']}."
                          if wrong else " is not the standard pattern.")
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                detail = f" could not be checked against recorded output ({exc})."
            findings.append(
                f"{gate_id}: {runner} EXPECT {expect}{detail} The standard EXPECT is "
                f"mandatory, including for count-pinned patterns and echoed markers. "
                f"Copy EXPECT: {contract['expect']} from runner-summaries.json.")
    return findings


def shell_stages(check: str) -> list[str]:
    stages = []
    start, quote, index = 0, "", 0
    while index < len(check):
        char = check[index]
        if quote:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "\\":
            index += 2
            continue
        elif char == "#" and (index == 0 or check[index - 1].isspace()):
            newline = check.find("\n", index)
            index = len(check) if newline == -1 else newline
            continue
        elif char in "|;&\n":
            stages.append(check[start:index].strip())
            start = index + 1
        index += 1
    stages.append(check[start:].strip())
    return stages


def final_stage(check: str) -> str:
    return shell_stages(check)[-1]


def expect_satisfied_by(expect: str, text: str) -> bool:
    """Whether `text` alone satisfies this EXPECT. A plain-text EXPECT is a substring
    test; a regex one is read with its anchors taken off, which is as far as this file
    goes into a JavaScript regex."""
    m = REGEX_EXPECT_RE.match(expect)
    if not m:
        return expect == text
    source = m.group(1)
    if source.startswith("^"):
        source = source[1:]
    if source.endswith("$") and not source.endswith("\\$"):
        source = source[:-1]
    return source == text


def lint_undecidable_checks(body: str) -> list[str]:
    """Two CHECK shapes that cannot decide the criterion they are written under.

    A criterion passes on exit 0 and a matched EXPECT together, so a command whose exit
    code and whose output do not both answer the criterion's question is not a check.

    The first shape ends in a `grep` and expects the output of a run that selected
    nothing. Measured on #449 AC9 (2026-09-19): `grep -c 'harness-guard' <file>` printed
    `0`, matched EXPECT `/^0$/m`, exited 1, and the run recorded the criterion unmet with
    no way for any code to satisfy it.

    The second throws the command's stdout and stderr away and matches a line the CHECK
    itself echoes from `$?`. Measured on #472 AC6 (2026-09-20): `bash .../run.sh --bogus
    >/dev/null 2>&1; echo "exit $?"` with EXPECT `/^exit 2$/m` passed on any runner that
    exits 2, including one with a syntax error, while the criterion's own text asked for
    a usage line the CHECK had discarded.
    """
    findings = []
    for gate_id, check, expect in criteria_lines(body):
        stage = final_stage(check)
        if GREP_STAGE_RE.match(stage):
            empty_run = "0" if COUNT_FLAG_RE.search(stage) else ""
            if expect_satisfied_by(expect, empty_run):
                findings.append(
                    f"{gate_id}: CHECK ends in `{stage}`, and grep exits 1 when it "
                    f"selected no line, while EXPECT {expect} is satisfied by exactly "
                    f"what that run prints. No code can make this criterion pass. Send "
                    f"the count through a stage of its own — "
                    f"`... | wc -l | tr -d ' '` — so the exit code is that stage's.")
        elif ECHOED_EXIT_RE.match(stage) and DISCARDS_BOTH_RE.search(check):
            findings.append(
                f"{gate_id}: CHECK sends the command's stdout and stderr to /dev/null "
                f"and ends in `{stage}`, so EXPECT {expect} is matched by a line the "
                f"CHECK writes itself from an exit code. Every command that exits that "
                f"way passes it, including one that failed for another reason. Keep the "
                f"output — `out=\"$(<command> 2>&1)\"; code=$?` — and require the line "
                f"the criterion names as well as the code.")
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


# A `CHECK:` that stubs the application's own network proves nothing about the product:
# `vi.stubGlobal('fetch')`, msw, nock, fetch-mock. Mocking the product's gateway is not that.
FETCH_STUB_RE = re.compile(
    r"stubGlobal\(\s*['\"]fetch['\"]|\bmsw\b|\bnock\b|\bfetch-mock\b",
    re.IGNORECASE,
)


def lint_network_stubs(body: str) -> list[str]:
    return [f"{gate_id}: CHECK stubs the application's own network; mock the product's "
            f"gateway instead"
            for gate_id, check, _ in criteria_lines(body) if FETCH_STUB_RE.search(check)]


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


def implementation_decision_numbers(spec_body: str) -> list[int]:
    """`### <n>.` headings under `## Implementation Decisions`, first occurrence of each."""
    numbers = []
    for line in section(spec_body, "Implementation Decisions"):
        m = IMPLEMENTATION_DECISION_HEADING_RE.match(line)
        if m:
            numbers.append(int(m.group(1)))
    return list(dict.fromkeys(numbers))


def print_uncovered_sections(spec: int, spec_body: str, named: set[int]) -> None:
    """WARN each Implementation Decisions section no ticket's Parent names; then the count.

    A WARN does not change the lint exit code.
    """
    numbers = implementation_decision_numbers(spec_body)
    for n in numbers:
        if n not in named:
            print(f"  WARN #{spec} Implementation Decisions section {n} is named by no "
                  f"ticket's ## Parent [uncovered-section]")
    covered = sum(1 for n in numbers if n in named)
    print(f"sections named by a ticket: {covered}/{len(numbers)}")


GATE_LINT_VERDICT_RE = re.compile(
    r"^LINT (?:OK(?: \((\d+) warning\(s\)\))?|FINDINGS: (\d+) error\(s\), (\d+) warning\(s\))\s*$")


def parent_order_findings(body: str, spec: int) -> list[str]:
    """`## Parent` names the spec this ticket sits under first.

    `parent_spec` reads the first issue number there as the ticket's spec, and it is
    what `spec_of` falls back to, what `fetch_outsider` asks of a blocker in another
    batch, and what `--drafts` has in place of a tracker link."""
    first = parent_spec(body)
    if first is None or first == spec:
        return []
    return [f"`## Parent` names #{first} first, but this ticket sits under spec #{spec}; "
            f"the first issue in `## Parent` is read as the ticket's spec; write "
            f"`#{spec}, Implementation Decisions sections <n>, <n>` first and an earlier "
            f"spec's sections after it (`; #{first} Implementation Decisions section <n>`)"]


def lint_build_points(body: str) -> list[str]:
    criteria = {item["id"] for item in parse_criteria(
        "\n".join(section(body, "Acceptance criteria")))}
    points: list[list[str]] = []
    fence = None
    for line in section(body, "What to build"):
        if fence is not None:
            close = FENCE_CLOSE_RE.match(line)
            if close and close.group(1)[0] == fence[0] and len(close.group(1)) >= fence[1]:
                fence = None
            continue
        opened = FENCE_OPEN_RE.match(line)
        if opened and not (opened.group(2)[0] == "`" and "`" in opened.group(3)):
            fence = (opened.group(2)[0], len(opened.group(2)))
            continue
        if re.match(r"^ {0,3}[0-9]+[.)]\s+", line):
            points.append([line])
        elif points:
            points[-1].append(line)
    if not points:
        return ["## What to build needs at least one numbered point naming an existing AC<n>"]
    findings = []
    for lines in points:
        named = set(re.findall(r"(?<![A-Za-z0-9_])AC[0-9]+(?![A-Za-z0-9_])", "\n".join(lines)))
        missing = named - criteria
        if not named:
            findings.append(f"## What to build point {lines[0]} names no AC<n>; "
                            "name the criterion that decides this point")
        elif missing:
            findings.append(f"## What to build point {lines[0]} names nonexistent "
                            f"{', '.join(sorted(missing))}; define each in ## Acceptance criteria "
                            "or correct the reference")
    return findings


def lint_criteria(number: int, body: str, labels: list[str],
                  spec: int | None = None, name: str | None = None) -> int:
    """Everything `--lint` says about one ticket's own text: its worker label, how its
    criteria are written. The batch graph is not here;
    `run_lint` checks that once per batch.

    `spec`, when known, is the spec this ticket sits under, and `## Parent` must name it
    first. `name` is how the ticket is named in what is printed: `#<number>` unless a
    draft's name stands in for it. The ticket's verdict is the last line printed for it
    and counts every finding above it: gate-lint's own `LINT OK` / `LINT FINDINGS` line
    covers only gate-lint's findings, so it is taken out and this one printed instead."""
    who = name or f"#{number}"
    worker_errors, worker_warnings = lint_worker(labels)
    counts = {"error": 0, "warn": 0}

    def say(level: str, finding: str, rule: str) -> None:
        label = "ERROR" if level == "error" else "WARN "
        print(f"  {label} {finding}  [{rule}]")
        counts[level] += 1

    def verdict() -> None:
        if counts["error"]:
            print(f"{who} LINT FINDINGS: {counts['error']} error(s), "
                  f"{counts['warn']} warning(s)")
        elif counts["warn"]:
            print(f"{who} LINT OK ({counts['warn']} warning(s))")
        else:
            print(f"{who} LINT OK")

    def report_worker_and_parent() -> None:
        for finding in worker_errors:
            say("error", f"{who} " + finding, "worker-label")
        for finding in worker_warnings:
            say("warn", f"{who} " + finding, "worker-label")
        if spec is not None:
            for finding in parent_order_findings(body, spec):
                say("error", f"{who} " + finding, "parent-order")

    for line in section(body, "Read first"):
        if re.search(r"(?<![\w.-])(?:www\.)?claude\.ai(?![\w-]|\.[\w-])", line, re.I):
            say("error", f"{who} ## Read first line `{line}` links to claude.ai; "
                "copy what the page settles into a file in the repository, commit it, "
                "and cite that path", "unreadable-read-first")

    # A `ready-for-human` ticket carries no criteria at all: what it holds is one thing
    # for the user to look at. gate-lint has nothing to say about it, and
    # saying "zero live gates" would report the ticket's correct shape as a fault.
    if not section(body, "Acceptance criteria"):
        print(f"{who} carries no `## Acceptance criteria`, so only its worker label "
              f"and its place in the batch are checked")
        if "ready-for-agent" in labels:
            say("error", f"{who} is labelled `ready-for-agent` and has no "
                f"`## Acceptance criteria` section, so a worker would have nothing to run "
                f"and the night would hand it back; write the section under exactly that "
                f"heading, or label the ticket `ready-for-human` when a person does it",
                "no-criteria")
        if not any(label in CLASS_LABELS for label in labels):
            say("warn", f"{who} carries no kind label, so its kind was read off "
                f"its place in the tree; the label on a spec is `{CLASS_SPEC}`, and "
                f"without it a spec attached to a map leaves its batch unlinted here",
                "layer-label")
        report_worker_and_parent()
        verdict()
        return 1 if counts["error"] else 0

    for finding in lint_build_points(body):
        say("error", f"{who} " + finding, "build-point-without-criterion")

    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp))
        result = subprocess.run(
            # No `--strict`: it fails the run on any warning, and a warning is the level
            # for findings the orchestrator weighs and may keep. The exit code says one thing —
            # there is an ERROR — which is what the read-back step converges on.
            ["node", str(GATE_LINT), str(ledger)],
            capture_output=True, text=True,
        )
    gate_verdict = None
    for line in ((result.stdout or "") + (result.stderr or "")).splitlines():
        found = GATE_LINT_VERDICT_RE.match(line)
        if found:
            gate_verdict = found
            continue
        print(line)
    if gate_verdict is not None:
        counts["warn"] += int(gate_verdict.group(1) or gate_verdict.group(3) or 0)
        counts["error"] += int(gate_verdict.group(2) or 0)
    elif result.returncode:
        # gate-lint could not read the ledger at all (exit 2), and said why above.
        counts["error"] += 1

    for finding in lint_expectations(body):
        say("error", finding, "dollar-without-m")
    for finding in lint_runner_expectations(body):
        say("error", finding, "runner-expect")
    for finding in lint_timeouts(body):
        say("error", finding, "bad-timeout")
    for finding in lint_network_stubs(body):
        say("error", finding, "network-stub")
    for finding in lint_undecidable_checks(body):
        say("error", finding, "undecidable-check")
    for finding in lint_check_effects(body):
        say("warn", finding, "shared-state")
    report_worker_and_parent()
    verdict()
    return result.returncode or (1 if counts["error"] else 0)


def ticket_labels(number: int) -> list[str]:
    return labels_of(fetch_ticket(number))


def labels_of(ticket: dict) -> list[str]:
    return [label.get("name") or "" for label in ticket.get("labels") or []]


def reads_as_spec(number: int, labels: list[str]) -> bool:
    """Whether `--lint` reads `number` as a spec — the container of a batch — rather
    than as a ticket that carries nothing to check.

    The kind label answers it, and its answer does not move when the spec is attached
    to its wayfinder map as a sub-issue, which is what the mmw-mode skill's
    `references/github-issues.md` asks for. Only an issue carrying no kind label at all falls back to the shape of
    the tree — no parent, and children of its own — which is what an issue opened
    before the kind labels existed is. That fallback cannot tell such a spec, once it is
    attached to a map, from a criteria-less ticket; `lint_criteria` names the missing
    label rather than let the answer pass for a read one.
    """
    if CLASS_SPEC in labels:
        return True
    if any(label in CLASS_LABELS for label in labels):
        return False
    return spec_of(number) is None and bool(fetch_sub_issues(number))


def run_lint(number: int) -> int:
    """`--lint` on a ticket lints that ticket and the graph of the batch it sits under.
    `--lint` on a spec — an issue with no `## Acceptance criteria` that `reads_as_spec`
    answers for — lints every one of its sub-issues, then the graph once. The night's
    pre-batch pass names the spec, so a spec number must not come back as a quiet 0."""
    body = fetch_body(number)
    labels = ticket_labels(number)
    if not section(body, "Acceptance criteria"):
        try:
            if reads_as_spec(number, labels):
                return lint_spec(number)
        except ParentUnreadable as exc:
            print(f"  ERROR the tracker could not say whether #{number} sits under a spec "
                  f"({exc})  [parent-unreadable]")
            return 1
        except SubIssuesUnreadable as exc:
            print(f"  ERROR the tracker could not list the children of #{number} "
                  f"({exc})  [sub-issues-unreadable]")
            return 1
    try:
        linked = fetch_parent(number)
    except ParentUnreadable:
        linked = None  # the graph step below reports it
    ticket_rc = lint_criteria(number, body, labels, spec=linked)
    graph = lint_ticket_graph(number, body)
    return 1 if (ticket_rc or graph) else 0


def lint_spec(spec: int) -> int:
    """Every sub-issue of the spec through `lint_criteria`, each under a line naming
    it, then the batch graph once. Exit 1 if an open ticket or the graph has an ERROR: a
    closed ticket is never started again, so its findings are printed and count for nothing."""
    numbers = fetch_sub_issues(spec)
    spec_body = fetch_body(spec)
    print(f"#{spec} is a spec with {len(numbers)} sub-issues; linting each, then the graph")
    failed: list[int] = []
    named: set[int] = set()
    for child in numbers:
        ticket = fetch_ticket(child)
        state = ticket.get('state') or 'state unknown'
        body = fetch_body(child)
        named |= set(parent_sections("\n".join(section(body, "Parent")))
                     .get(spec, {}).get("sections") or ())
        print(f"\n## #{child} ({state})")
        if lint_criteria(child, body, labels_of(ticket), spec=spec):
            if state == "CLOSED":
                print(f"  WARN  #{child} is closed, so the ERROR above does not stop the batch  [closed-ticket]")
            else:
                failed.append(child)
    print("\n## ticket graph")
    graph = lint_batch_graph(spec, numbers)
    print_uncovered_sections(spec, spec_body, named)
    if failed:
        print("  ERROR tickets with findings: " + ", ".join(f"#{n}" for n in failed))
    return 1 if (failed or graph) else 0


DRAFT_HEADER_RE = re.compile(r"^([A-Z][A-Z ]*[A-Z]):\s*(.*)$")
DRAFT_REQUIRED = ("TITLE", "LABELS", "BLOCKED BY")
DRAFT_ISSUE_RE = re.compile(r"^#(\d+)$")
# What `--lint` on a published batch checks and `--drafts` cannot, because only the
# tracker holds it. Printed at the end of every drafts run, so a clean run is not taken
# for the published batch's.
DRAFTS_NOT_CHECKED = (
    "that each ticket is a sub-issue of the spec and carries the labels on the tracker "
    "(the LABELS: header is checked instead)",
    "the blocking edges the tracker records (the BLOCKED BY: headers are checked instead)",
)


class DraftUnreadable(ValueError):
    """A draft file whose header cannot be read."""


def read_draft(path: Path) -> dict:
    """One draft: `KEY: value` header lines, a line `---`, then the issue body.

    `TITLE:`, `LABELS:` (comma-separated) and `BLOCKED BY:` (comma-separated draft names,
    or `#<n>` for a published issue, or `(none)`) are required; other header keys are
    the drafter's notes and are not read. The draft's name is its file name without
    `.md`, and it stands in for the issue number the ticket does not have yet."""
    text = path.read_text(encoding="utf-8")
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise DraftUnreadable(f"{path.name}: no `---` line between the header and the body")
    meta: dict[str, str] = {}
    for line in head.splitlines():
        if not line.strip():
            continue
        found = DRAFT_HEADER_RE.match(line)
        if not found:
            raise DraftUnreadable(f"{path.name}: header line `{line[:60]}` is not `KEY: value`")
        meta[found.group(1)] = found.group(2).strip()
    missing = [key for key in DRAFT_REQUIRED if key not in meta]
    if missing:
        raise DraftUnreadable(f"{path.name}: the header has no " + ", ".join(
            f"`{key}:`" for key in missing))
    blocked_raw = meta["BLOCKED BY"]
    blocked = ([] if blocked_raw.lower() in ("", "none", "(none)")
               else [x.strip() for x in blocked_raw.split(",") if x.strip()])
    return {"name": path.stem, "title": meta["TITLE"], "body": body,
            "labels": [x.strip() for x in meta["LABELS"].split(",") if x.strip()],
            "blocked": blocked}


def runner_summary_present(output: str, contract: dict) -> bool:
    output = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    return bool(re.search(contract["summary_pattern"], output, re.MULTILINE))


def lint_draft_base_checks(drafts: list[dict], root: Path, base: str) -> int:
    contracts = json.loads((HERE / "runner-summaries.json").read_text(encoding="utf-8"))
    errors = 0
    with tempfile.TemporaryDirectory(prefix="mmw-draft-base-") as temporary:
        tmp = Path(temporary)
        worktree = tmp / "checkout"
        try:
            added = subprocess.run(["git", "worktree", "add", "--detach", str(worktree), base],
                                   cwd=root, capture_output=True, text=True)
            if added.returncode:
                print(f"ERROR --base {base}: {added.stderr.strip()}; nothing ran")
                return 2
            for draft in drafts:
                name, body = draft["name"], draft["body"]
                items = parse_criteria("\n".join(section(body, "Acceptance criteria")))
                items = [dict(item, ticked=False, evidence="pending") for item in items
                         if item["check"]]
                if not items:
                    continue
                ledger_dir = tmp / "ledgers" / name
                ledger_dir.mkdir(parents=True)
                ledger = write_ledger(body, ledger_dir,
                                      [criterion_block(item) for item in items])
                results_path = ledger_dir / "results.json"
                env = dict(os.environ, MMW_BASE_REF=base, MMW_TICKET=name)
                run = subprocess.run(
                    ["node", str(GATE_CHECK), "--cwd", str(worktree),
                     "--timeout", str(check_timeout(body)), "--results", str(results_path),
                     str(ledger)], cwd=worktree, env=env, capture_output=True, text=True)
                if run.returncode not in (0, 1) or not results_path.is_file():
                    print(f"  ERROR {name}: gate-check could not run on --base {base} "
                          f"({run.stdout}{run.stderr}) [base-run]")
                    errors += 1
                    continue
                by_id = {item["id"]: item for item in items}
                for result in json.loads(results_path.read_text(encoding="utf-8")):
                    gate_id = result["id"]
                    outcome = "PASS" if result["ok"] else "FAIL"
                    print(f"  {name} {gate_id} {outcome} on {base}")
                    if result["error"]:
                        print(f"    {result['error']}")
                    output = result["output"]
                    for line in output.splitlines()[-5:]:
                        print("    " + re.sub(
                            r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u061c\u200e\u200f\u2028-\u202e\u2066-\u2069]",
                            " ", line))
                    if result["ok"]:
                        print(f"  WARN {name} {gate_id} passes on the base; it is either a pin "
                              "or a CHECK that cannot see this ticket's work [passes-on-base]")
                    for runner in check_runners(by_id[gate_id]["check"]):
                        if not runner_summary_present(output, contracts[runner]):
                            print(f"  ERROR {name} {gate_id}: {runner} printed no known summary "
                                  "line; change CHECK to print a runner summary "
                                  "[no-runner-summary]")
                            errors += 1
        except (OSError, ValueError) as exc:
            print(f"ERROR --base {base}: base run could not complete ({exc}) [base-run]")
            return 2
        finally:
            _remove_baseline_checkout(root, worktree)
    return 1 if errors else 0


def lint_drafts(spec: int, directory: Path, base: str | None = None) -> int:
    """`--lint` over the tickets of a batch before they are published.

    Every `*.md` in `directory` is one draft (`read_draft`). Each goes through the same
    `lint_criteria` a published ticket gets, with the labels of its header and `spec` as
    the spec it will sit under; then the graph its `BLOCKED BY:` headers make goes through
    `lint_batch_graph`, and the spec's Implementation Decisions sections are counted
    against every draft's `## Parent`. The spec itself, and any `#<n>` a draft is
    blocked by, are read from the tracker. What only a published batch can show is
    listed at the end as not checked."""
    root = repo_root()
    base = base or f"origin/{current_branch(root)}"
    resolved = subprocess.run(["git", "rev-parse", "--verify", f"{base}^{{commit}}"],
                              cwd=root, capture_output=True, text=True)
    if resolved.returncode:
        print(f"ERROR --base {base} does not name a commit; set --base to an existing ref; "
              "nothing ran")
        return 2
    paths = sorted(directory.glob("*.md"))
    if not paths:
        print(f"  ERROR {directory} holds no `*.md` drafts, so there is nothing to lint  "
              f"[no-drafts]")
        return 1
    drafts: list[dict] = []
    failed: list[str] = []
    for path in paths:
        try:
            drafts.append(read_draft(path))
        except (DraftUnreadable, OSError, UnicodeError) as exc:
            print(f"  ERROR {exc}; write the header as TITLE:, LABELS:, BLOCKED BY: lines, "
                  f"then `---`, then the body  [draft-unreadable]")
            failed.append(path.stem)
    try:
        spec_body = fetch_body(spec)
    except TrackerReadError as exc:
        spec_body = ""
        print(f"  WARN  spec #{spec} could not be read ({exc.detail}), so the section "
              f"count below did not run; restore tracker "
              f"access and run --drafts again  [spec-unreadable]")
    names = {d["name"] for d in drafts}
    print(f"#{spec}: {len(drafts)} drafts in {directory}; linting each, then the graph "
          f"their BLOCKED BY: headers make")
    named: set[int] = set()
    entries: list[dict] = []
    for draft in drafts:
        name = draft["name"]
        body = draft["body"]
        named |= set(parent_sections("\n".join(section(body, "Parent")))
                     .get(spec, {}).get("sections") or ())
        print(f"\n## {name} (draft)")
        dependencies: list[int | str] = []
        bad = False
        if len(draft["title"]) > GITHUB_TITLE_LIMIT:
            print(f"  ERROR {name}: TITLE has {len(draft['title'])} Unicode characters; "
                  f"the GitHub title limit is {GITHUB_TITLE_LIMIT}; shorten TITLE "
                  f"before publishing  [title-limit]")
            bad = True
        for blocker in draft["blocked"]:
            issue = DRAFT_ISSUE_RE.match(blocker)
            if issue:
                dependencies.append(int(issue.group(1)))
            elif blocker in names:
                dependencies.append(blocker)
            else:
                print(f"  ERROR {name} is blocked by `{blocker}`, which is neither a draft "
                      f"in {directory} nor `#<issue number>`; name a draft by its file name "
                      f"without `.md`  [unknown-draft]")
                bad = True
        if "mmw:ticket" not in draft["labels"]:
            print(f"  ERROR {name}: LABELS: has no `mmw:ticket`, the kind label every "
                  f"ticket is published with  [layer-label]")
            bad = True
        entries.append({"id": name, "dependencies": dependencies})
        if lint_criteria(0, body, draft["labels"], spec=spec, name=name) or bad:
            failed.append(name)
    base_rc = lint_draft_base_checks(drafts, root, base)
    if base_rc == 2:
        return 2
    found: dict[int, dict] = {}
    for entry in entries:
        for dep in entry["dependencies"]:
            if isinstance(dep, int) and dep not in found:
                found[dep] = fetch_outsider(dep)
        entry["outside"] = {d: found[d] for d in entry["dependencies"] if isinstance(d, int)}
    print("\n## ticket graph (from BLOCKED BY:)")
    graph = lint_batch_graph(spec, [], entries) if entries else 1
    if spec_body:
        print_uncovered_sections(spec, spec_body, named)
    print("\nnot checked on drafts; run --lint on the published spec for these:")
    for line in DRAFTS_NOT_CHECKED:
        print("  - " + line)
    if failed:
        print("  ERROR drafts with findings: " + ", ".join(failed))
    return 1 if (failed or graph or base_rc) else 0


def _draft_dependencies(draft: dict, names: set[str], directory: Path) -> list[int | str]:
    """A draft's `BLOCKED BY:` header read as the graph `validate_dag` and
    `compute_levels` take: an existing issue as its number, another draft in this batch
    by name. Raises `ValueError` naming the first blocker that is neither."""
    out: list[int | str] = []
    for blocker in draft["blocked"]:
        issue = DRAFT_ISSUE_RE.match(blocker)
        if issue:
            out.append(int(issue.group(1)))
        elif blocker in names:
            out.append(blocker)
        else:
            raise ValueError(f"{draft['name']} is blocked by `{blocker}`, which is "
                             f"neither a draft in {directory} nor `#<issue number>`")
    return out


def run_publish_drafts(spec: int, directory: Path) -> int:
    """Publish every draft in `directory` as a native sub-issue of `spec`: create each
    blocker before what it blocks, wire the blocking edges its `BLOCKED BY:` header
    names, print the draft name to issue number table, then run `--lint` on the
    published spec once, because only the tracker shows what publishing did.

    An overlong title, a cycle, or a blocker naming no draft and no `#<n>`, is refused
    before anything is created: publishing is deterministic given a valid batch, so an invalid one is
    reported, not half built. A `gh` failure partway through names every draft already
    published, so nothing has to be guessed from the tracker by hand.
    """
    paths = sorted(directory.glob("*.md"))
    if not paths:
        return refuse(f"{directory} holds no `*.md` drafts; nothing to publish")
    drafts: list[dict] = []
    for path in paths:
        try:
            drafts.append(read_draft(path))
        except (DraftUnreadable, OSError, UnicodeError) as exc:
            return refuse(str(exc))
    long_titles = [f"{draft['name']}: {len(draft['title'])} Unicode characters"
                   for draft in drafts if len(draft["title"]) > GITHUB_TITLE_LIMIT]
    if long_titles:
        return refuse(f"GitHub title limit is {GITHUB_TITLE_LIMIT}; "
                      + "; ".join(long_titles)
                      + "; shorten each draft's TITLE before publishing; nothing was published")
    names = {d["name"] for d in drafts}
    entries = []
    for draft in drafts:
        try:
            deps = _draft_dependencies(draft, names, directory)
        except ValueError as exc:
            return refuse(str(exc))
        entries.append({"id": draft["name"], "dependencies": deps})
    errors = validate_dag(in_batch(entries))
    if errors:
        return refuse("; ".join(error.split("  [")[0] for error in errors))
    entries_by_name = {entry["id"]: entry for entry in entries}
    levels = compute_levels(in_batch(entries))
    order = sorted(drafts, key=lambda d: (levels.get(d["name"], 0), d["name"]))

    def already_published(numbers: dict[str, int]) -> str:
        return ("; already published: "
                + ", ".join(f"{n} -> #{i}" for n, i in numbers.items()) if numbers else "")

    numbers: dict[str, int] = {}
    for draft in order:
        for label in draft["labels"]:
            if not label_defined(label):
                continue
            missing = ensure_label(label)
            if missing:
                return refuse(f"the repository has no `{label}` label and it could not "
                              f"be created ({missing}); {draft['name']} was not published"
                              + already_published(numbers))
        args = ["--parent", str(spec), "--title", draft["title"]]
        for label in draft["labels"]:
            args += ["--label", label]
        result, number = gh_issue_create(args, draft["body"])
        if result.returncode != 0:
            sys.stderr.write((result.stderr or result.stdout or "gh issue create failed")
                             .rstrip() + already_published(numbers) + "\n")
            return 2
        if number is None:
            printed = (result.stdout or "").strip()
            sys.stderr.write(f"gh issue create for {draft['name']} printed no issue number "
                             f"({printed[:80] or 'nothing'})" + already_published(numbers) + "\n")
            return 2
        numbers[draft["name"]] = number
        print(f"{draft['name']} -> #{number}")

    problems = []
    for draft in order:
        child = numbers[draft["name"]]
        for dep in entries_by_name[draft["name"]]["dependencies"]:
            blocker = numbers[dep] if isinstance(dep, str) else dep
            problem = add_blocking_link(child, blocker)
            if problem:
                problems.append(f"#{child} ({draft['name']}) could not be linked as "
                                f"blocked by #{blocker}: {problem}")
    for problem in problems:
        sys.stderr.write(problem + "\n")
    lint_result = lint_spec(spec)
    return 1 if problems else lint_result


EXIT_CODES = """\
exit codes:
  a criteria run (no flag, or --reverify --actor worker|main)
    0 every criterion met; 1 something unmet or abandoned; 2 the ticket could not be
    read or the run could not start, reason on stderr, nothing posted; 4 the criteria
    ran and the ticket.checked recording them could not be written: run it again
  --preflight
    0 the ticket is now yours; 2 refused, reason on stderr: a NOT_READY refusal is
    on the ticket as ticket.refused, any other posted nothing
  --lint
    0 nothing reported an ERROR; 1 a ticket or the graph has one (on a spec, any of
    its open sub-issues having one; a closed one's ERROR is printed and counts for
    nothing). No CHECK: runs and no comment is posted on any exit
  --decisions, --touched
    0 posted (for --touched, or nothing to post); 2 refused, nothing posted
  --draft
    0 the file was written and its path printed; 2 refused, no file written
  --sub-issue
    0 the sub-issue is open and recorded; 1 the sub-issue is open and its
    child.opened event could not be written, named on stderr — do not open it
    again; 2 a refusal, reason on stderr
  --review
    0 posted; 2 refused (the file does not open REVIEW <base>..<head>, or an
    ## In-ticket row is not recognized), reason on stderr
  --publish
    --spec-body: 0 published, printed as the issue number (with --map, its native
    parent was confirmed too); 1 published but the native parent could not be
    confirmed as --map, printed then said on stderr; 2 refused, nothing published
    --drafts: 0 every draft published, every blocking edge recorded, and --lint on
    the published spec reported no ERROR; 1 published with a blocking edge that
    could not be recorded, or --lint on the published spec found one; 2 refused
    before anything was created, or gh failed partway (stderr names what published)
  --closeout
    0 the ticket is closed (or handed back) and its event posted, or with
    --check-only the draft passes; 1 refused by a draft condition, the push, or the
    tracker, stderr saying what to resolve; 2 nothing was run or written
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], epilog=EXIT_CODES,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    # Optional only for `--publish --spec-body`, which creates an issue that has no
    # number yet; every other job needs one.
    parser.add_argument("ticket", type=int, nargs="?",
                        help="the ticket (or, with --publish --drafts, the spec) this run "
                             "is about; omit only for --publish --spec-body")
    parser.add_argument("--reverify", action="store_true",
                        help="re-run every criterion, including the ones already ticked")
    parser.add_argument("--lint", action="store_true",
                        help="audit how the criteria are written; runs no CHECK, posts no comment")
    parser.add_argument("--drafts", type=Path, metavar="DIR",
                        help="with --lint, the ticket being the spec: lint the unpublished "
                             "drafts in DIR (TITLE:/LABELS:/BLOCKED BY: header, `---`, body) "
                             "instead of the spec's sub-issues; with --publish, publish them "
                             "as native sub-issues of the spec")
    parser.add_argument("--publish", action="store_true",
                        help="publish a spec (--spec-body FILE --title T [--map N]) or a "
                             "batch of ticket drafts (--drafts DIR, the ticket being the "
                             "spec they publish under)")
    parser.add_argument("--spec-body", type=Path, metavar="FILE",
                        help="with --publish: the new spec's body")
    parser.add_argument("--title", metavar="TITLE",
                        help="with --publish --spec-body: the new spec's title")
    parser.add_argument("--map", type=int, metavar="N",
                        help="with --publish --spec-body: publish as a native sub-issue "
                             "of map N")
    parser.add_argument("--preflight", action="store_true",
                        help="claim the ticket, or refuse and say why on the ticket")
    parser.add_argument("--closeout", type=Path, metavar="DRAFT",
                        help="check this closing comment, then post it and close the ticket")
    parser.add_argument("--check-only", action="store_true",
                        help="with --closeout: check the closing-comment draft and change nothing")
    parser.add_argument("--decisions", type=Path, metavar="FILE",
                        help="post the two-section file as a DECISIONS comment")
    parser.add_argument("--touched", action="store_true",
                        help="post worker.touched on open siblings whose Owns covers a file")
    # The path is optional, and an empty string is what argparse leaves when the flag came
    # without one — a file of the run's own, outside the repository the checks read.
    parser.add_argument("--draft", nargs="?", const="", metavar="OUT",
                        help="write the closing-comment draft to this file; with no "
                             "path, to one of its own outside the repository, printed as "
                             "`DRAFT: wrote <path>`")
    parser.add_argument("--sub-issue", nargs=2, metavar=("KIND", "FILE"),
                        help="open an mmw:child under this ticket; only decision and "
                             "deferred also carry needs-triage; KIND is one of "
                             + ", ".join(SUB_ISSUE_KINDS))
    parser.add_argument("--actor", choices=events.REVERIFY_ACTORS,
                        help="required with --reverify: the worker's final run or the main "
                             "agent re-running a landed ticket on the base branch")
    parser.add_argument("--review", type=Path, metavar="FILE",
                        help="post the review report on the ticket")
    parser.add_argument("--base", metavar="REF",
                        help="with --lint --drafts: run CHECKs on REF, default origin/<current branch>")
    args = parser.parse_args(argv)
    chosen = [name for name, on in
              (("--lint", args.lint), ("--reverify", args.reverify),
               ("--preflight", args.preflight), ("--closeout", args.closeout is not None),
               ("--decisions", args.decisions is not None), ("--touched", args.touched),
               ("--draft", args.draft is not None),
               ("--sub-issue", args.sub_issue is not None),
               ("--review", args.review is not None), ("--publish", args.publish)) if on]
    if len(chosen) > 1:
        parser.error(f"{' and '.join(chosen)} are different jobs; pick one")
    if args.base is not None and not (args.lint and args.drafts is not None):
        parser.error("--base belongs to --lint --drafts")
    if args.drafts is not None and not (args.lint or args.publish):
        parser.error("--drafts belongs to --lint or --publish")
    if args.drafts is not None and not args.drafts.is_dir():
        parser.error(f"no directory at {args.drafts}")
    if args.check_only and args.closeout is None:
        parser.error("--check-only belongs to --closeout")
    if args.actor is not None and not args.reverify:
        parser.error("--actor belongs to --reverify")
    if args.reverify and args.actor is None:
        parser.error("--reverify requires --actor worker|main")
    if args.spec_body is not None and not args.publish:
        parser.error("--spec-body belongs to --publish")
    if args.title is not None and args.spec_body is None:
        parser.error("--title belongs to --publish --spec-body")
    if args.map is not None and args.spec_body is None:
        parser.error("--map belongs to --publish --spec-body")
    if args.publish and args.spec_body is None and args.drafts is None:
        parser.error("--publish needs --spec-body --title, or --drafts")
    if args.publish and args.spec_body is not None and args.drafts is not None:
        parser.error("--spec-body and --drafts are different forms of --publish; pick one")
    if args.publish and args.spec_body is not None:
        if args.ticket is not None:
            parser.error("--publish --spec-body creates a new issue; do not name a ticket number")
        if not args.title:
            parser.error("--publish --spec-body requires --title")
        if not args.spec_body.is_file():
            parser.error(f"no file at {args.spec_body}")
    elif args.ticket is None:
        parser.error("a ticket number is required")
    try:
        if args.publish and args.spec_body is not None:
            return run_publish_spec(args.spec_body, args.title, args.map)
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
            return run_draft(args.ticket, Path(args.draft) if args.draft else None)
        if args.sub_issue is not None:
            kind, file = args.sub_issue
            return run_sub_issue(args.ticket, kind, Path(file))
        if args.review is not None:
            if not args.review.is_file():
                parser.error(f"no file at {args.review}")
            return run_review(args.ticket, args.review)
        if args.publish:
            return run_publish_drafts(args.ticket, args.drafts)
        if args.lint and args.drafts is not None:
            return lint_drafts(args.ticket, args.drafts, args.base)
        if args.lint:
            return run_lint(args.ticket)
        return run_checks(args.ticket, args.reverify, args.actor)
    except TrackerReadError as exc:
        return refuse(f"verify-ticket: {exc}. Nothing was run or written; retry the same command")


if __name__ == "__main__":
    sys.exit(main())
