#!/usr/bin/env python3
"""Run and print ticket criteria, lint tickets, and publish specs or ticket drafts."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
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
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str | Path):
    """Load the module at `filename`. A name with no directory is a file beside this one."""
    path = Path(filename)
    if not path.is_absolute():
        path = HERE / path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# `events.py`: the event vocabulary and the fold. `issue_tree.py`: the tree of issues
# under a spec, read with one query.
skills = HERE.parents[1]
locations = _load("verify_locations", skills / "mmw" / "scripts" / "locations.py")
events = _load("mmw_events", skills / locations.EVENTS_PY)
tree = _load("mmw_tree", "issue_tree.py")
GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"
GATE_LINT = HERE / "gate-check" / "gate-lint.mjs"
LEDGER_NAME = "AC.md"
# The summary line gate-check prints on its own stdout.
SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")
GATE_LINE_RE = re.compile(r"^- \[( |x|X)\] ([A-Za-z0-9][A-Za-z0-9._-]*):")
IMPLEMENTATION_DECISION_HEADING_RE = re.compile(r"^###\s+(\d+)\.")
SUB_ISSUE_KINDS = events.CHILD_KINDS
# The layer label every issue this pipeline opens carries beside its queue label: which
# layer of the tree it is, so a reader of the board never counts nesting to find out.
CLASS_LABELS = {
    "mmw:map": ("5319e7", "MMW layer: the map one discussion opened"),
    "mmw:spec": ("1d76db", "MMW layer: a spec, the container of one batch of tickets"),
    "mmw:ticket": ("0e8a16", "MMW layer: a ticket, one unit of work"),
    "mmw:child": ("c5def5", "MMW layer: a child issue a ticket opened"),
}
# The one of them `--lint` asks after by name: which number is a batch's container.
CLASS_SPEC = "mmw:spec"
# The other two label sets `docs/agents/issue-tracker.md` `## Three label sets` names:
# who a ticket is waiting on, and which `models.json` row starts its worker. Colour and
# description are defined once, here, for all three sets; `ensure_label` and `--publish`
# create whichever of them a repository lacks. `docs/agents/triage-labels.md` maps queue
# labels to this repository's own roles; it does not redefine them.
QUEUE_LABELS = {
    "needs-triage": ("F9D0C4", "还没评估过，不知道该不该做、怎么做"),
    "needs-info": ("B60205", "缺输入，等人补"),
    "ready-for-agent": ("FEF2C0", "已写清楚，可以直接派工人 AFK 跑"),
    "ready-for-human": ("BFDADC", "HITL 的活，不派工人"),
    "wontfix": ("ffffff", "This will not be worked on"),
}
GRADE_LABELS = {
    "junior-worker": ("C2E0C6", "worker grade: default row in models.json"),
    "senior-worker": ("E99695", "worker grade: silent-failure work"),
}
# The scripts of the ui-acceptance skill that run a command `.mmw/target.json` declares,
# under this worktree's lease. A criterion naming one needs the product, and so a slot.
# An oracle that starts the product, and so needs this worktree's slot. `story-parity.py`
# is not one: it starts the story service, which has no backend behind it and takes
# a port of its own.
PRODUCT_JUDGES = ("journey.py", "lease.py")
# Criteria whose CHECK names one of these are left off the claim-time baseline run:
# they start the product or the story service. Recorded on the event as `skipped`.
BASELINE_SKIP_JUDGES = (*PRODUCT_JUDGES, "story-parity.py")
# How long a reverify waits for a product slot before it hands back exit 3, and how often
# it asks again in between. The bound stays under the time a host lets a command run
# before it moves it to the background; a reverify given back 3 is run again, and the wait
# goes on. The worker's own run does not wait here: it is woken when a slot is given back.

# A criterion is abandoned for one of three reasons. `failed` ran and did not pass;
# `stuck` never ran or cannot be done; the two are told apart for whoever reads the
# ticket in the morning, and both hand the ticket back. `decision` needs a person to
# choose, and is the only one that still closes. How many rounds a criterion gets is
# the worker's own judgement, said on the `ABANDON:` line.
ABANDON_KINDS = events.ABANDON_KINDS
# Seconds one `CHECK:` may run. A ticket raises it per criterion with `TIMEOUT:`; the
# worker's own run and final `--reverify` read the same lines, so the two
# never disagree about it.
DEFAULT_TIMEOUT = 600
ABANDON_RE = re.compile(r"^ABANDON:\s+(\S+)\s+(\S+)\s*(.*)$")
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

# Grok Build hands its agents CLICOLOR_FORCE=1, and `gh` writes ANSI escapes into --json
# output under it, which json.loads cannot read. Every gh call here runs without it.
# The mode's `events.py`, loaded above through locations.py, computes the same filter;
# this file shares its value rather
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


# `refusal.py` of the ui-acceptance skill. One line is capped here, above a hook's
# 256-character deny reason: `refusal` trims the cause and keeps the next step whole.


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


# ------------------------------------------------------------ criterion ledger

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


def glob_covers(pattern: str, path: str) -> bool:
    """Whether an `## Owns` glob covers `path`."""
    pattern = pattern.rstrip("/")
    if pattern.endswith("/**"):
        root = pattern[:-3]
        return path == root or path.startswith(root + "/")
    return fnmatch.fnmatch(path, pattern) or path == pattern


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


def ensure_label(name: str) -> str | None:
    """Make sure the repository has label `name`, from any of the three sets defined
    above (layer, queue, grade); the reason when it could not.

    A label the repository lacks makes `gh issue create --label` fail outright, so the
    first issue that would carry it creates it instead. One that already exists is left
    exactly as it is. Patched out in tests.
    """
    color, description = (CLASS_LABELS.get(name) or QUEUE_LABELS.get(name)
                          or GRADE_LABELS.get(name) or (None, None))
    if color is None:
        raise KeyError(name)
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
    the same edge `docs/agents/issue-tracker.md` `## Wayfinding operations` adds by hand.
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
    return name in CLASS_LABELS or name in QUEUE_LABELS or name in GRADE_LABELS


def run_publish_spec(body_path: Path, title: str, map_number: int | None) -> int:
    """Publish a spec: one issue carrying the layer label `mmw:spec`, and, when
    `map_number` is given, a native sub-issue of that map — the link the board and the
    retro find a spec's map through; nothing written in the body stands in for it.

    A spec is a container for the tickets underneath it, not a piece of work, so it
    carries no triage label.
    """
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

def needs_product(body: str) -> bool:
    """Whether a criterion of this ticket runs the product: its `CHECK:` names a script
    that starts a command `.mmw/target.json` declares, under this worktree's lease."""
    return any(judge in check for _, check, _ in criteria_lines(body)
               for judge in PRODUCT_JUDGES)


def load_lease():
    """`lease.py` of the ui-acceptance skill, from the directories in force; None when
    none holds it."""
    path = tool("lease.py")
    if path is None:
        return None
    spec = importlib.util.spec_from_file_location("mmw_lease", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SlotAcquisition(NamedTuple):
    """An acquired lease, an unavailable slot, or a refusal before acquiring."""
    returncode: int
    slot: dict | None = None
    reason: str | None = None
    limit: int | None = None
    holders: list[str] | None = None
    worktree: str | None = None


class CriteriaRun(NamedTuple):
    """One engine run; callers print output and decide whether to record it."""
    returncode: int
    output: str = ""
    ledger: str = ""
    criteria: list[dict] | None = None
    abandons: list[dict] | None = None
    outcome: str | None = None
    head: str = ""
    shape: str = ""
    outside_owns: dict | None = None
    slot: SlotAcquisition | None = None
    summary: str = ""


def hold_slot(root: Path) -> SlotAcquisition:
    """Try acquiring this worktree's product slot without writing ticket state."""
    lease = load_lease()
    if lease is None:
        return SlotAcquisition(refuse(
            "a criterion runs the product and no directory in force holds lease.py; "
            "nothing ran. Pass --tools <the ui-acceptance skill's scripts directory> "
            "and run again."))
    worktree = lease.worktree_of(root)
    try:
        return SlotAcquisition(0, slot=lease.try_claim(worktree), worktree=str(worktree))
    except lease.CapUnreadable as exc:
        return SlotAcquisition(refuse(
            f"{exc}; the product's limit is unknown and nothing ran. Fix that file and run again."))
    except lease.Full as full:
        return SlotAcquisition(3, reason=full.reason, limit=full.limit,
                               holders=full.holders, worktree=str(worktree))


def run_checks(number: int, reverify: bool) -> int:
    """Print criteria results without writing any ticket event."""
    result = run_criteria(number, reverify)
    sys.stdout.write(result.output)
    if result.returncode == 3:
        sys.stderr.write(f"#{number}: no product slot is free ({result.slot.reason}); "
                         "nothing ran. Run the same command when a slot is available.\n")
    return result.returncode


def run_criteria(number: int, reverify: bool) -> CriteriaRun:
    """Run criteria under the lifetime of a non-ticket oracle lease; never post."""
    body = fetch_body(number)
    require_judges(body)
    root = repo_root()
    lease = load_lease() if needs_product(body) else None
    if lease is None:
        return _run_criteria(number, reverify, body, root)
    try:
        with lease.judge_run(root, stop=True):
            return _run_criteria(number, reverify, body, root)
    except lease.StopUnreadable as exc:
        sys.stderr.write(f"#{number}: {exc}; the oracle's product slot was kept\n")
        return CriteriaRun(2)
    except SystemExit as exc:
        sys.stderr.write(f"#{number}: the oracle's product slot was not given back: {exc}\n")
        return CriteriaRun(2)


def _run_criteria(number: int, reverify: bool, body: str, root: Path) -> CriteriaRun:
    """Return the gate-check result, ledger and lease facts without posting."""
    head = git("rev-parse", "HEAD", cwd=root)
    if not re.fullmatch(r"[0-9a-f]{40}", head or ""):
        return CriteriaRun(refuse("could not read HEAD, so this run would name no commit. Nothing was "
                      "run and nothing was written."))
    comments = fetch_comments(number)
    started = events.newest(comments, "worker.started")
    started_payload = (started or {}).get("payload", {})
    base = started_payload.get("base") if not reverify else None
    into = started_payload.get("into")
    slot = None
    if needs_product(body):
        slot = hold_slot(root)
        if slot.returncode:
            return CriteriaRun(slot.returncode, head=head, slot=slot)
    carried = carried_ledger(body, comments) if reverify else []
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp), carried or None)
        cmd = ["node", str(GATE_CHECK), "--cwd", str(root)]
        if reverify:
            cmd.append("--reverify")
        cmd += ["--timeout", str(check_timeout(body))]
        cmd.append(str(ledger))
        env = os.environ.copy()
        env["MMW_TICKET"] = str(number)
        if isinstance(into, str) and into:
            env["MMW_BASE_REF"] = f"origin/{into}"
        if TOOLS:
            env["PATH"] = os.pathsep.join([str(d) for d in TOOLS] + [env.get("PATH", "")])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        if result.returncode == 2:
            return CriteriaRun(2, output=printed, head=head, slot=slot)
        summary = next((line for line in printed.splitlines() if SUMMARY_RE.match(line)), "")
        updated = ledger.read_text(encoding="utf-8").rstrip("\n")

    criteria = parse_criteria(updated)
    abandons = parse_abandons(updated)
    outcome = check_run_outcome(result.returncode, summary)
    fields = ({} if reverify else
              outside_owns_fields(number, owns_globs(body), root, base))
    return CriteriaRun(result.returncode, output=printed, ledger=updated,
                       criteria=criteria, abandons=abandons, outcome=outcome, head=head,
                       shape=shape_digest(section(body, "Acceptance criteria")),
                       outside_owns=fields, slot=slot, summary=summary)


def check_run_outcome(returncode: int, summary: str) -> str | None:
    """The `ticket.checked` result of one gate-check process, or None if it could not start."""
    if returncode == 2:
        return None
    if returncode == 0:
        return "met"
    if summary.startswith("HANDOFF REQUIRED:"):
        return "handoff"
    return "unmet"


def baseline_skipped(check: str) -> bool:
    """Whether this CHECK is left off the claim-time baseline run."""
    return any(name in (check or "") for name in BASELINE_SKIP_JUDGES)


def run_baseline(number: int, body: str, base: str, root: Path) -> dict | None:
    """Criteria that need no product slot, at `base`, in a throwaway detached worktree."""
    items = parse_criteria("\n".join(section(body, "Acceptance criteria")))
    skipped = [c["id"] for c in items if baseline_skipped(c.get("check", ""))]
    runnable = [c for c in items if c["id"] not in skipped]
    tmp = Path(tempfile.mkdtemp(prefix="mmw-baseline-"))
    worktree = tmp / "tree"
    try:
        added = subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), base],
            cwd=root, capture_output=True, text=True)
        short = base[:12]
        if added.returncode != 0 or not worktree.is_dir():
            why = (added.stderr or added.stdout or "git worktree add failed").strip()
            return dict(runnable=[], skipped=[c["id"] for c in items],
                           outcome="unmet",
                           line=f"Baseline run on {short}: unmet ({why})")
        if not runnable:
            return dict(runnable=[], skipped=skipped, outcome="unmet",
                           line=f"Baseline run on {short}: nothing ran (all skipped)")
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
        env = os.environ.copy()
        env["MMW_TICKET"] = str(number)
        if TOOLS:
            env["PATH"] = os.pathsep.join([str(d) for d in TOOLS] + [env.get("PATH", "")])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=worktree, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        summary = next((line for line in printed.splitlines() if SUMMARY_RE.match(line)), "")
        updated = ledger.read_text(encoding="utf-8").rstrip("\n") if ledger.is_file() else ""
        outcome = check_run_outcome(result.returncode, summary)
        if outcome is None:
            return dict(runnable=[], skipped=[c["id"] for c in items],
                           outcome="unmet",
                           line=f"Baseline run on {short}: could not start")
        ran = parse_criteria(updated) if updated else runnable
        return dict(runnable=ran, skipped=skipped, outcome=outcome,
                       line=f"Baseline run on {short}: {summary or outcome}",
                       updated=updated)
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"#{number}: baseline run did not complete ({exc})\n")
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree)],
                       cwd=root, capture_output=True, text=True)
        shutil.rmtree(tmp, ignore_errors=True)


ROW_ID_RE = re.compile(r"\b[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+\b")


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


def final_stage(check: str) -> str:
    """The command whose exit code a CHECK's shell hands back: the text after the last
    `|`, `;` or `&` the shell reads as a separator.

    Quoting is followed, because a grep pattern holds those characters as often as a
    shell does: `grep -c 'a\\|b' f` is one command, not two.
    """
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
        elif char in "|;&":
            start = index + 1
        index += 1
    return check[start:].strip()


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


SCREEN_CONTRACT_ROWS_RE = re.compile(r"screen-contract\.yaml\s+rows?:\s*([^\n]+)")
FETCH_STUB_RE = re.compile(
    r"stubGlobal\(\s*['\"]fetch['\"]|\bmsw\b|\bnock\b|\bfetch-mock\b",
    re.IGNORECASE,
)
FLAG_RE = re.compile(r"(?<!\S)(--[a-z][a-z0-9-]*)")
# The scripts of this pipeline a criterion may run, and the flags each call cannot leave
# out. `lint_pipeline_flags` reads it, so a script that takes no flags at all has nothing
# to assert here and is left out of it, which is why this holds fewer scripts than
# `JUDGES` below does.
# Their addresses come from the repository's `.mmw/target.json`, never from the line.
PIPELINE_SCRIPTS = {
    "story-parity.py": {"required": ("--contract", "--pages")},
    "boundary-check.py": {"required": ("--run",)},
}
# The oracles of the `ui-acceptance` skill: every script a `CHECK:` names by its bare name and
# that `require_judges` refuses a run for when the shell could not find it. The default place
# looked at is that skill's `scripts/`, resolved in `main()`; `--tools` overrides it.
JUDGES = ("story-parity.py", "boundary-check.py", "journey.py", "harness-guard.py")
SPEC_SECTION_SOURCE_RE = re.compile(r"^#(\d+) (Implementation Decisions|Testing Decisions)\s*(\d+)?")
ADR_SOURCE_RE = re.compile(r"^ADR-(\d{4})")
TICKET_SOURCE_RE = re.compile(r"^#(\d+)(?:\s|$)")
DOC_SOURCE_RE = re.compile(r"^(docs/\S+)")
STORY_SOURCE_RE = re.compile(r"^#\d+ story \d+")
_HELP_FLAGS: dict[str, set[str]] = {}
# Where the scripts other skills own are found: the `ui-acceptance` skill's `scripts/` by
# default, or the directories `--tools` named instead. A `CHECK:` names an oracle by its bare
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
    """A `CHECK:` names one of the oracles and no directory in force holds it."""


def require_judges(body: str) -> None:
    """Refuse, before anything runs, when a criterion names an oracle this run cannot reach.

    Without the directory, the criterion fails `command not found`, which reads exactly
    like a criterion that ran and did not pass: gate-check records it as one more unmet
    criterion and this run exits 1. On 2026-09-08 `dispatch.sh reverify` was found running
    with no `--tools` at all, which would have reopened and handed back every ticket of
    a batch whose criteria name an oracle, for a fault in the invocation. So the run
    stops here instead, names the script, and writes nothing to the ticket.

    `PATH` is the second place looked at: a directory put there by hand is a legitimate
    way to reach the oracles, and refusing it would refuse something that works.
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


RUN_VALUE_RE = re.compile(r"""--run(?:\s+|=)(?:"([^"]*)"|'([^']*)'|(\S+))""")
JOURNEY_NAME_RE = re.compile(r"^\s*run\s+(\S+)")
CD_PREFIX_RE = re.compile(r"^\s*cd\s+(\S+)\s*&&")
CRITICAL_FLOWS_RE = re.compile(r"Critical flows|关键流程", re.IGNORECASE)
JOURNEY_PATH_RE = re.compile(r"\.mmw/journeys/([a-z0-9][a-z0-9-]*)/?")


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
    """The flags of the oracle's own command line.

    `--run` carries a whole command as its value, and that command has flags of its
    own (`pnpm --dir desktop-chameleon exec vitest run …`). The shell hands a quoted
    value to the oracle as one word, so the words are cut the way the shell cuts them
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


def row_mount(row: dict, doc: dict) -> str:
    """The design-page mount this row makes the ticket claim.

    Ordinary rows belong to the Component page whose declaration owns their
    `component`. A cross-component row belongs to the App page its `app` column names.
    """
    pages = doc.get("pages") or {}
    app = str(row.get("app") or "")
    if app:
        return str((pages.get(app) or {}).get("mount") or "")
    for decl in pages.values():
        decl = decl or {}
        if str(decl.get("component") or "") == str(row.get("component") or ""):
            return str(decl.get("mount") or "")
    return ""


def row_needs_boundary(row: dict) -> bool:
    """Whether to-tickets requires a boundary criterion for this row."""
    calls = [str(value).lower() for value in (row.get("calls") or [])]
    return bool(row.get("app")) or calls != ["none"] or str(row.get("next") or "") != "stay"


def run_values(check: str) -> list[str]:
    """The `--run` values on a boundary-check.py criterion; empty when that script is absent."""
    if "boundary-check.py" not in check:
        return []
    segment = script_segment(check, "boundary-check.py")
    values = flag_values(segment, RUN_VALUE_RE)
    if "--run" in segment and not values:
        return [""]
    return values


TEST_FILE_SUFFIXES = (".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")


# `python -m unittest discover`: the flags that take a value, and which of them name the
# start directory and the file pattern. Its positionals are `[start] [pattern] [top]`.
DISCOVER_VALUE_FLAGS = ("-s", "--start-directory", "-p", "--pattern", "-t",
                        "--top-level-directory", "-k", "--durations")
DISCOVER_START_FLAGS = ("-s", "--start-directory")
DISCOVER_PATTERN_FLAGS = ("-p", "--pattern")
DISCOVER_DEFAULT_PATTERN = "test*.py"
# A runner flag whose value is the directory the rest of the command runs in, so a
# relative test file after it is read from there: `pnpm --dir <d>`, `npm --prefix <d>`,
# `yarn --cwd <d>`, `make -C <d>`.
CHDIR_FLAGS = ("--dir", "--prefix", "--cwd", "-C")


def _discover_paths(words: list[str], base: Path) -> tuple[list[Path], set[int]]:
    """The files `unittest discover` would load, and the indices of the words that said so.

    `-s <dir> -p <file>` (or `--start-directory`, `--pattern`, `=` forms, or discover's
    positional `<dir> <pattern>`) names one file as the two joined. A pattern with
    `*`, `?` or `[` names every file it matches in that directory; one that matches none
    is kept as written, so the caller reports it as not written yet rather than as a
    command that names no test."""
    if "discover" not in words:
        return [], set()
    start = pattern = None
    consumed: set[int] = set()
    positional: list[tuple[int, str]] = []
    j = words.index("discover") + 1
    while j < len(words):
        word = words[j]
        flag, eq, value = word.partition("=")
        if eq and flag in DISCOVER_VALUE_FLAGS:
            index = j
            j += 1
        elif word in DISCOVER_VALUE_FLAGS and j + 1 < len(words):
            flag, value, index = word, words[j + 1], j + 1
            j += 2
        else:
            if not word.startswith("-"):
                positional.append((j, word))
            j += 1
            continue
        if flag in DISCOVER_START_FLAGS:
            start = value
            consumed.add(index)
        elif flag in DISCOVER_PATTERN_FLAGS:
            pattern = value
            consumed.add(index)
    if start is None and positional:
        index, start = positional.pop(0)
        consumed.add(index)
    if pattern is None and positional:
        index, pattern = positional.pop(0)
        consumed.add(index)
    directory = base / (start or ".")
    pattern = pattern or DISCOVER_DEFAULT_PATTERN
    if any(ch in pattern for ch in "*?["):
        matches = sorted(path for path in directory.glob(pattern) if path.is_file())
        return (matches or [directory / pattern]), consumed
    return [directory / pattern], consumed


def boundary_test_paths(command: str, root: Path) -> list[Path]:
    """Test files named by one boundary `--run` command.

    A case suffix (`file.py::Case.test`) still names `file.py`. Existing paths are
    accepted even when their suffix is unusual; otherwise the standard script/test
    suffixes distinguish a future file from command names and case selectors.

    A runner that takes the directory and the file apart is read as the two joined:
    `unittest discover -s <dir> -p <file>` (`_discover_paths`), and a relative file
    after a flag that moves the command into another directory (`CHDIR_FLAGS`) is read
    from that directory when it is there, from the repository root otherwise.
    """
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    found: list[Path] = []

    def add(candidate: Path) -> None:
        if candidate not in found:
            found.append(candidate)

    base = root
    for i, word in enumerate(words[:-1]):
        flag, eq, value = word.partition("=")
        if eq and flag in CHDIR_FLAGS:
            base = root / value
        elif word in CHDIR_FLAGS:
            base = root / words[i + 1]
    discovered, consumed = _discover_paths(words, base)
    for path in discovered:
        add(path)
    after_chdir = False
    for i, word in enumerate(words):
        if i in consumed:
            continue
        flag = word.partition("=")[0]
        if flag in CHDIR_FLAGS:
            after_chdir = True
        value = word.split("::", 1)[0].rstrip(",;:")
        if value.startswith("-") or not value:
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            moved = base / candidate
            candidate = (moved if after_chdir and (moved.is_file() or
                                                  not (root / candidate).is_file())
                         else root / candidate)
        if candidate.is_file() or value.lower().endswith(TEST_FILE_SUFFIXES):
            add(candidate)
    return found


def help_flags(script: str) -> set[str]:
    """The flags the installed script actually accepts, read from its `--help` once.
    This is the one place a criterion's reference to a capability that does not exist
    yet is caught at the moment it is written. Looked for in the directories in force,
    then on PATH, the same two places a `CHECK:` itself resolves the script from."""
    if script not in _HELP_FLAGS:
        path = tool(script) or shutil.which(script)
        text = ""
        if path is not None:
            try:
                out = subprocess.run([str(path), "--help"], capture_output=True,
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
        known = help_flags(script)
        if known:
            for flag in sorted(flags - known):
                findings.append(f"{gate_id}: {script} does not accept {flag} (its --help "
                                f"does not list it; addresses come from .mmw/target.json, "
                                f"never from the line)")
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


def source_findings(row_ids: list[str], rows_by_id: dict[str, dict],
                    read_first: str, parent_text: str) -> list[str]:
    """Every baseline-class source of an owned row must be in `## Read first`; every
    spec-section source must be named by `## Parent`. A story reaches no worker and is
    reported as such."""
    findings = []
    parents = parent_sections(parent_text)
    seen: set[str] = set()
    for rid in row_ids:
        row = rows_by_id.get(rid)
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


CRITICAL_FLOW_SHAPE = "- `<flow>`: Implementation Decisions sections <n>, <n>"
LIST_ITEM_RE = re.compile(r"^(\s*)[-*+]\s")


def critical_flows(spec_body: str) -> tuple[dict[str, set[int]], list[str]]:
    """Flow name → Implementation Decisions sections from Testing Decisions.

    The **Critical flows** bullet holds one line per flow, in the shape
    `CRITICAL_FLOW_SHAPE`, nested under the marker or on the marker line itself: the
    flow is the backticked name (or `.mmw/journeys/<flow>/`, or the bare first word of
    the item), and the section numbers are the ones after the words
    `Implementation Decisions` (`sections 2 and 3 of Implementation Decisions` reads the
    same). The section is named by its heading in the spec, in English whatever language
    the rest of the spec is in, because that heading is what `## Parent` names too; a
    line without those words is returned as unreadable.

    A line that says only `none` is the spec saying the product has no such flow.

    The bullet ends where its own list ends: at the first non-blank line indented no
    deeper than the marker's own list item, or at a heading. A marker that is not a list
    item (a paragraph or a heading) owns the list items that follow it.
    """
    out: dict[str, set[int]] = {}
    unreadable: list[str] = []
    active = False
    marker_indent: int | None = None
    for raw in section(spec_body, "Testing Decisions"):
        line = raw
        marker = None if active else CRITICAL_FLOWS_RE.search(line)
        if marker:
            active = True
            item = LIST_ITEM_RE.match(line)
            marker_indent = len(item.group(1)) if item else None
            line = re.sub(r"^\*{0,2}\s*(?:\([^)]*\))?\s*[:：]?\s*", "",
                          line[marker.end():])
            if not line.strip():
                continue
        elif active:
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                break
            indent = len(line) - len(line.lstrip())
            if marker_indent is not None and indent <= marker_indent:
                break
            if marker_indent is None and not LIST_ITEM_RE.match(line) and indent == 0:
                break
        else:
            continue
        if re.fullmatch(r"[-*\s]*`?none`?[.。]?\s*", line, re.IGNORECASE):
            continue
        path = JOURNEY_PATH_RE.search(line)
        quoted = re.search(r"`([a-z0-9][a-z0-9-]*)`", line)
        plain = re.match(r"^\s*[-*]\s+([a-z0-9][a-z0-9-]*)\b", line)
        name = (path.group(1) if path else quoted.group(1) if quoted else
                plain.group(1) if plain else "")
        after = re.search(r"Implementation Decisions\s*(.+)$", line)
        before = re.search(r"sections?\s+(.+?)\s+of\s+Implementation Decisions", line,
                           re.IGNORECASE)
        decision = after.group(1) if after else before.group(1) if before else ""
        sections = {int(value) for value in re.findall(r"\d+", decision)}
        if name and sections:
            out[name] = sections
        else:
            unreadable.append(line.strip())
    return out, unreadable


def acceptance_journeys(
    parent_text: str, spec_bodies: dict[int, str]
) -> tuple[set[str], list[tuple[int, str]]]:
    """Critical-flow journeys whose decision sections this ticket's Parent names."""
    parents = parent_sections(parent_text)
    out: set[str] = set()
    unreadable: list[tuple[int, str]] = []
    for spec, parent in parents.items():
        body = spec_bodies.get(spec)
        if not body:
            continue
        flows, bad_lines = critical_flows(body)
        unreadable.extend((spec, line) for line in bad_lines)
        for name, required in flows.items():
            if required <= set(parent.get("sections") or ()):
                out.add(name)
    return out, unreadable


def lint_screen_contract(
    body: str,
    number: int | None = None,
    root: Path | str | None = None,
    spec_bodies: dict[int, str] | None = None,
    fetch_spec_body: Callable[[int], str] | None = None,
) -> tuple[list[str], list[str]]:
    """The UI rules of `to-tickets`, made mechanical.

    A `screen-contract.yaml rows: …` line makes this a page ticket. Its rows
    determine the required Component or App story mounts and boundary criteria, and
    each readable boundary test file must contain the row's trigger. A
    `boundary-check.py --run` is a non-empty command; a `journey.py run <name>` exists
    under `.mmw/journeys/` unless this ticket's `## Owns` covers that directory;
    critical-flow journeys require `--break`, while a user-named journey without it is
    a warning;
    no `CHECK:` may stub the application's own network (`vi.stubGlobal('fetch')`, msw,
    nock, fetch-mock) — mocking the product's gateway is not that; the
    pipeline scripts are given what they need and nothing they retired; every
    baseline-class source of an owned row is under `## Read first` and every
    spec-section source is named by `## Parent`.
    """
    findings: list[str] = []
    warning_findings: list[str] = []
    repo = Path(root) if root is not None else repo_root()
    read_first = "\n".join(section(body, "Read first"))
    parent_text = "\n".join(section(body, "Parent"))
    owns = owns_globs(body)
    checks = criteria_lines(body)
    loaded_spec_bodies = dict(spec_bodies or {})
    acceptance: set[str] | None = None
    acceptance_readable: bool | None = None
    unreadable_specs_reported: set[int] = set()
    contract_runtime = all(
        any(glob_covers(pattern, required) for pattern in owns)
        for required in (".mmw/target.json", ".mmw/stories")
    )

    def load_acceptance_journeys() -> tuple[set[str], bool]:
        """Read parent specs once; False means at least one could not be read."""
        readable = True
        parents = parent_sections(parent_text)
        for spec in parents:
            if spec not in loaded_spec_bodies and fetch_spec_body is not None:
                loaded_spec_bodies[spec] = fetch_spec_body(spec)
            if not loaded_spec_bodies.get(spec):
                readable = False
                if spec not in unreadable_specs_reported:
                    findings.append(
                        f"spec #{spec} could not be read, so --lint cannot decide whether "
                        f"this journey is a Critical flow; restore tracker access and run "
                        f"--lint again")
                    unreadable_specs_reported.add(spec)
        journeys, unreadable_lines = acceptance_journeys(parent_text, loaded_spec_bodies)
        for spec, line in unreadable_lines:
            findings.append(
                f"spec #{spec} Critical flows line `{line}` could not be read, so --lint "
                f"cannot decide whether this journey needs --break; write each flow as "
                f"`{CRITICAL_FLOW_SHAPE}`, with the words Implementation Decisions in "
                f"English, as `## Parent` names them")
        return journeys, readable and not unreadable_lines

    for gate_id, check, _ in checks:
        findings.extend(lint_pipeline_flags(gate_id, check))
        if FETCH_STUB_RE.search(check):
            findings.append(f"{gate_id}: CHECK stubs the application's own network; mock "
                            f"the product's gateway instead")
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
        journey_segment = script_segment(check, "journey.py")
        journey_has_break = "--break" in segment_flags(journey_segment)
        for name in JOURNEY_NAME_RE.findall(journey_segment):
            if (base / ".mmw" / "journeys" / name).exists():
                exists_or_owned = True
            else:
                # A ticket whose `## Owns` covers the directory is the ticket that creates
                # it, so it is absent until this ticket's own work lands. The rule asks
                # after a journey someone else was to have built.
                path = "/".join(p for p in (prefix, ".mmw", "journeys", name) if p)
                exists_or_owned = any(glob_covers(g, path) for g in owns)
            if not exists_or_owned:
                findings.append(f"{gate_id}: journey.py run {name} is not under .mmw/journeys/")
                continue
            if journey_has_break or name == "smoke" or contract_runtime:
                continue
            if acceptance is None:
                acceptance, acceptance_readable = load_acceptance_journeys()
            if not acceptance_readable:
                continue
            if name in acceptance:
                findings.append(
                    f"{gate_id}: critical-flow journey `{name}` has no --break; its Critical "
                    f"flows entry makes a negative control mandatory; add --break "
                    f"\"<METHOD> <route>\" for the flow's last write")
            else:
                warning_findings.append(
                    f"{gate_id}: user-named journey `{name}` has no --break, so this "
                    f"journey cannot be broken and cannot reject a script that only reads "
                    f"a success message; add --break when the flow has a write to isolate")
    m = SCREEN_CONTRACT_ROWS_RE.search(read_first)
    interface_ticket = any("story-parity.py" in check for _, check, _ in checks)
    if not m:
        if interface_ticket:
            findings.append("page ticket (a criterion runs story-parity.py) names no "
                            "`screen-contract.yaml rows: <id, id>` line under `## Read first`")
        return findings, warning_findings
    row_ids = ROW_ID_RE.findall(m.group(1))
    doc, contract_path = load_contract_doc(read_first)
    if doc is None and contract_path:
        findings.append(f"the screen contract {contract_path} could not be read from here (not in "
                        f"the working tree, or neither pyyaml nor uv is available); the "
                        f"source rules did not run")
    if doc is not None:
        mounts_of = page_mounts(doc)
        rows_by_id = {str(row.get("id") or ""): row for row in doc.get("rows") or []
                      if isinstance(row, dict)}
        missing_rows = [row_id for row_id in row_ids if row_id not in rows_by_id]
        for row_id in missing_rows:
            findings.append(
                f"screen-contract.yaml rows names `{row_id}`, but the screen contract has no such "
                f"row; no page or boundary requirement can be derived; correct the row id "
                f"under `## Read first`")
        rows = [rows_by_id[row_id] for row_id in row_ids if row_id in rows_by_id]
        for gate_id, check, _ in checks:
            if "story-parity.py" not in check:
                continue
            for mount in story_mounts(check):
                page = mounts_of.get(mount)
                if page is None:
                    findings.append(f"{gate_id}: --pages {mount} is declared by no page "
                                    f"of the screen contract")
        story_mount_set = {mount for _, check, _ in checks for mount in story_mounts(check)}
        expected_pages: dict[str, list[str]] = defaultdict(list)
        for row in rows:
            mount = row_mount(row, doc)
            if mount:
                expected_pages[mount].append(str(row.get("id") or ""))
        for mount, ids in expected_pages.items():
            if mount not in story_mount_set:
                findings.append(
                    f"screen-contract rows {', '.join(ids)} claim page mount `{mount}`, but "
                    f"no story criterion names it; those rows make this a page ticket; "
                    f"add one story-parity.py criterion whose --pages includes `{mount}`")

        boundary_present = False
        missing_boundary_files: list[tuple[str, Path]] = []
        readable_boundary_files: list[tuple[Path, str]] = []

        def shown(path: Path) -> str:
            try:
                return str(path.relative_to(repo))
            except ValueError:
                return str(path)

        for gate_id, check, _ in checks:
            for command in run_values(check):
                if not command.strip():
                    continue
                boundary_present = True
                paths = boundary_test_paths(command, repo)
                if not paths:
                    findings.append(
                        f"{gate_id}: boundary-check.py --run names no test file, so no "
                        f"screen-contract trigger can be checked; a boundary criterion must "
                        f"name the test it runs; add that test file path to --run")
                    continue
                for path in paths:
                    if not path.exists():
                        missing_boundary_files.append((gate_id, path))
                        continue
                    try:
                        text = path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as exc:
                        findings.append(
                            f"{gate_id}: boundary test file {shown(path)} could not be read "
                            f"({exc}); an unreadable test cannot prove which rows it covers; "
                            f"replace it with a readable UTF-8 test file and run --lint again")
                        continue
                    readable_boundary_files.append((path, text))

        boundary_rows: list[tuple[str, str, str]] = []
        for row in rows:
            if not row_needs_boundary(row):
                continue
            rid = str(row.get("id") or "")
            kind = "cross-component row" if row.get("app") else "screen-contract row"
            trigger_value = row.get("trigger")
            if not isinstance(trigger_value, str):
                findings.append(
                    f"{kind} {rid} trigger is not a string, so its data-ui id cannot be "
                    f"checked against a boundary test; the screen-contract row is unreadable to "
                    f"this rule; write `trigger` as the closing-comment draft's data-ui id string")
                continue
            trigger = trigger_value
            boundary_rows.append((kind, rid, trigger))
            if not boundary_present:
                findings.append(
                    f"{kind} {rid} has no boundary criterion; its calls/next/app columns "
                    f"require an interaction check; add boundary-check.py --run for the "
                    f"test that exercises `{trigger}`")
                continue
            if any(trigger in text for _, text in readable_boundary_files):
                continue
            if not readable_boundary_files:
                continue
            named = ", ".join(shown(path) for path, _ in readable_boundary_files)
            findings.append(
                f"{kind} {rid} trigger `{trigger}` does not appear in the boundary test "
                f"file(s) {named or '(none)'}; without the data-ui id no criterion is tied "
                f"to this row; add `{trigger}` to the test named by boundary-check.py --run")

        unchecked_rows = [rid for _, rid, trigger in boundary_rows
                          if not any(trigger in text for _, text in readable_boundary_files)]
        for gate_id, path in missing_boundary_files:
            rows_text = ", ".join(unchecked_rows) or "none"
            warning_findings.append(
                f"{gate_id}: boundary test file {shown(path)} is not written yet, so rows "
                f"{rows_text} were not checked for their data-ui ids; batch publication "
                f"precedes implementation; write the file with each owned row's trigger")
        findings.extend(source_findings(row_ids, rows_by_id, read_first, parent_text))
    return findings, warning_findings


GATE_LINT_VERDICT_RE = re.compile(
    r"^LINT (?:OK(?: \((\d+) warning\(s\)\))?|FINDINGS: (\d+) error\(s\), (\d+) warning\(s\))\s*$")


def parent_order_findings(body: str, spec: int) -> list[str]:
    """`## Parent` names the spec this ticket sits under first.

    `parent_spec` reads the first issue number there as the ticket's spec, and it is
    what `spec_of` falls back to, what `fetch_outsider` asks of a blocker in another
    batch, and what `--drafts` has in place of a tracker link. An earlier spec whose
    sections a screen-contract row cites as its source is named after it, in the same words."""
    first = parent_spec(body)
    if first is None or first == spec:
        return []
    return [f"`## Parent` names #{first} first, but this ticket sits under spec #{spec}; "
            f"the first issue in `## Parent` is read as the ticket's spec; write "
            f"`#{spec}, Implementation Decisions sections <n>, <n>` first and an earlier "
            f"spec's sections after it (`; #{first} Implementation Decisions section <n>`)"]


def lint_criteria(number: int, body: str, labels: list[str],
                  spec_bodies: dict[int, str] | None = None,
                  fetch_spec_body: Callable[[int], str] | None = None,
                  spec: int | None = None, name: str | None = None) -> int:
    """Everything `--lint` says about one ticket's own text: its worker label, how its
    criteria are written, and their UI rules. The batch graph is not here;
    `run_lint` checks that once per batch.

    `spec`, when known, is the spec this ticket sits under, and `## Parent` must name it
    first. `name` is how the ticket is named in what is printed: `#<number>` unless a
    draft's name stands in for it. The ticket's verdict is the last line printed for it
    and counts every finding above it: gate-lint's own `LINT OK` / `LINT FINDINGS` line
    covers only gate-lint's findings, so it is taken out and this one printed instead."""
    require_judges(body)
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

    # A `ready-for-human` ticket carries no criteria at all: what it holds is one thing
    # for the user to look at. gate-lint has nothing to say about it, and
    # saying "zero live gates" would report the ticket's correct shape as a fault.
    if not section(body, "Acceptance criteria"):
        print(f"{who} carries no `## Acceptance criteria`, so only its worker label "
              f"and its place in the batch are checked")
        if not any(label in CLASS_LABELS for label in labels):
            say("warn", f"{who} carries no layer label, so its layer was read off "
                f"its place in the tree; the label on a spec is `{CLASS_SPEC}`, and "
                f"without it a spec attached to a map leaves its batch unlinted here",
                "layer-label")
        report_worker_and_parent()
        verdict()
        return 1 if counts["error"] else 0

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
    for finding in lint_timeouts(body):
        say("error", finding, "bad-timeout")
    contract_findings, contract_warnings = lint_screen_contract(
        body, number, spec_bodies=spec_bodies, fetch_spec_body=fetch_spec_body)
    for finding in contract_findings:
        say("error", finding, "screen-contract")
    for finding in contract_warnings:
        say("warn", finding, "screen-contract")
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

    The layer label answers it, and its answer does not move when the spec is attached
    to its wayfinder map as a sub-issue, which is what `docs/agents/issue-tracker.md`
    asks for. Only an issue carrying no layer label at all falls back to the shape of
    the tree — no parent, and children of its own — which is what an issue opened
    before the layer labels existed is. That fallback cannot tell such a spec, once it is
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
    ticket_rc = lint_criteria(number, body, labels, fetch_spec_body=fetch_body, spec=linked)
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
        if lint_criteria(child, body, labels_of(ticket), {spec: spec_body}, spec=spec):
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


def lint_drafts(spec: int, directory: Path) -> int:
    """`--lint` over the tickets of a batch before they are published.

    Every `*.md` in `directory` is one draft (`read_draft`). Each goes through the same
    `lint_criteria` a published ticket gets, with the labels of its header and `spec` as
    the spec it will sit under; then the graph its `BLOCKED BY:` headers make goes through
    `lint_batch_graph`, and the spec's Implementation Decisions sections are counted
    against every draft's `## Parent`. The spec itself, and any `#<n>` a draft is
    blocked by, are read from the tracker. What only a published batch can show is
    listed at the end as not checked."""
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
        print(f"  WARN  spec #{spec} could not be read ({exc.detail}), so the Critical "
              f"flows rule and the section count below did not run; restore tracker "
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
            print(f"  ERROR {name}: LABELS: has no `mmw:ticket`, the layer label every "
                  f"ticket is published with  [layer-label]")
            bad = True
        entries.append({"id": name, "dependencies": dependencies})
        if lint_criteria(0, body, draft["labels"], {spec: spec_body} if spec_body else {},
                         spec=spec, name=name) or bad:
            failed.append(name)
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
    return 1 if (failed or graph) else 0


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

    A cycle, or a blocker naming no draft and no `#<n>`, is refused before anything is
    created: publishing is deterministic given a valid batch, so an invalid one is
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


EXIT_CODES = """exit codes:
  criteria run: 0 every criterion met; 1 unmet or abandoned; 2 could not start;
    3 no product slot was free, nothing ran. No criteria run writes an event.
  --lint: 0 no ERROR; 1 a ticket or graph has an ERROR; 2 could not start.
  --publish --spec-body: 0 published; 1 parent unconfirmed; 2 refused or failed.
  --publish --drafts: 0 published and linted; 1 links or lint failed;
    2 refused or failed (stderr names any drafts already published).
  retired state flags: 2, one line naming ticket_state.py; nothing ran or written.
"""


def retired_state_command(argv: list[str]) -> str | None:
    """A retired flag redirects before parsing or any tracker access."""
    replacements = {
        "--preflight": "--claim", "--draft": "--closing-draft [OUT]",
        "--sub-issue": "--open-child KIND FILE", "--closeout": "--closeout DRAFT",
        "--check-only": "--closeout DRAFT --check-only", "--decisions": "--decisions FILE",
        "--review": "--review FILE", "--touched": "--touched",
        "--actor": "--run-and-record-criteria --reverify --actor worker|main",
    }
    number = next((word for word in argv if word.isdigit()), "<n>")
    for word in argv:
        flag = word.partition("=")[0]
        if flag in replacements:
            return (f"{flag} belongs to ticket_state.py, not this criteria printer; "
                    f"run ticket_state.py {number} {replacements[flag]}")
    return None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    retired = retired_state_command(argv)
    if retired is not None:
        return refuse(retired)
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
    parser.add_argument("--tools", action="append", type=Path, default=[], metavar="DIR",
                        help="a directory holding scripts of other skills (the ui-acceptance "
                             "skill's scripts/); put on the PATH of every CHECK; repeatable")
    args = parser.parse_args(argv)
    # The oracles live in the `ui-acceptance` skill, beside this one under `skills/`, so this
    # file's own location answers where they are and no caller has to know. `--tools`
    # overrides that for a run against a copy somewhere else.
    TOOLS[:] = ([d.resolve() for d in args.tools]
                or [skills / locations.UI_ACCEPTANCE_SCRIPTS])
    chosen = [name for name, on in (("--lint", args.lint),
              ("--reverify", args.reverify), ("--publish", args.publish)) if on]
    if len(chosen) > 1:
        parser.error(f"{' and '.join(chosen)} are different jobs; pick one")
    if args.drafts is not None and not (args.lint or args.publish):
        parser.error("--drafts belongs to --lint or --publish")
    if args.drafts is not None and not args.drafts.is_dir():
        parser.error(f"no directory at {args.drafts}")
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
        if args.publish:
            return run_publish_drafts(args.ticket, args.drafts)
        if args.lint and args.drafts is not None:
            return lint_drafts(args.ticket, args.drafts)
        if args.lint:
            return run_lint(args.ticket)
        return run_checks(args.ticket, args.reverify)
    except TrackerReadError as exc:
        return refuse(f"verify-ticket: {exc}. Nothing was run or written; retry the same command")
    except JudgeUnreachable as exc:
        print(f"verify-ticket: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
