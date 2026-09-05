#!/usr/bin/env python3
"""Run a ticket's acceptance criteria and post the result back to the ticket.

The ticket is the only state. Every run reads the `## Acceptance criteria` and
`## Owns` sections fresh from the issue, writes them to a ledger, hands
that ledger to unlazy's `gate-check`, and posts the updated ledger back as one
comment. Nothing is cached and no file is left behind.

    verify-ticket.py <n>              run the unmet criteria, comment `self-run`
    verify-ticket.py <n> --reverify   re-run every criterion, comment `reverify`
    verify-ticket.py <n> --lint       audit how the criteria are written; print only
    verify-ticket.py <n> --preflight  claim the ticket, or refuse and say why
    verify-ticket.py <n> --closeout <draft>  check the closing comment, then post it
    verify-ticket.py <n> --decisions <file>  post the two-section file as `DECISIONS`
    verify-ticket.py <n> --touched    comment `TOUCHED BY` on open siblings that own a file
    verify-ticket.py <n> --draft <out-file>  write the closing-comment skeleton
    verify-ticket.py <n> --sub-issue <kind> <file>  open a needs-triage child of the spec

Exit code follows gate-check: 0 all met, 1 unmet or abandoned, 2 usage or
infrastructure. `--preflight` exits 2 when it refuses; `--closeout` exits 1.
`--decisions`, `--touched` and `--sub-issue` exit 2 when they refuse.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"
GATE_LINT = HERE / "gate-check" / "gate-lint.mjs"
LEDGER_NAME = "AC.md"
SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")
GATE_LINE_RE = re.compile(r"^- \[( |x|X)\] ([A-Za-z0-9][A-Za-z0-9._-]*):")
SUB_ISSUE_KINDS = ("baseline", "outside-owns", "review", "decision")
FILL = "<fill>"

# A criterion is abandoned for one of three reasons. `failed` ran and did not pass;
# `stuck` never ran or cannot be done; the two are told apart for whoever reads the
# ticket in the morning, and both hand the ticket back. `decision` needs a person to
# choose, and is the only one that still closes. How many rounds a criterion gets is
# the worker's own judgement, said on the `ABANDON:` line.
ABANDON_KINDS = ("decision", "failed", "stuck")
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
VERDICT_RE = re.compile(r"^VERDICT\s+([0-9a-fA-F]{40})\b")
ISSUE_REF_RE = re.compile(r"#(\d+)")
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


def fetch_ticket(number: int) -> dict:
    """State, labels, assignees and blockers of the ticket. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "state,labels,assignees,blockedBy"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    return json.loads(out.stdout)


def gh_login() -> str:
    """The account `gh` is signed in as. Patched out in tests."""
    out = subprocess.run(["gh", "api", "user", "-q", ".login"], env=GH_ENV,
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def assign_self(number: int) -> None:
    """Claim the ticket. Patched out in tests."""
    subprocess.run(["gh", "issue", "edit", str(number), "--add-assignee", "@me"], check=True, env=GH_ENV)


def close_ticket(number: int) -> None:
    """Take the ticket out of the agent queue and close it. Patched out in tests."""
    subprocess.run(
        ["gh", "issue", "edit", str(number), "--remove-label", "ready-for-agent"],
        check=True, env=GH_ENV,
    )
    subprocess.run(["gh", "issue", "close", str(number), "--reason", "completed"], check=True, env=GH_ENV)


def hand_back_for_triage(number: int) -> None:
    """Put the ticket back in the queue nobody has judged yet. Patched out in tests.

    A worker that could not finish has not established what the ticket needs next — a
    person, more information, another agent, or nothing at all. `needs-triage` is that
    state, and it is the one queue a skill picks up on its own.

    A ticket still assigned to the worker that gave up is a ticket `board.py` will not
    dispatch again — its frontier takes only unassigned tickets — so the assignee comes
    off in the same edit as the label.
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


def fetch_sub_issues(spec: int) -> list[int]:
    """The tickets GitHub records under `spec`, in its own order, every page of them
    (GitHub pages the list at 30, and a spec past its thirtieth ticket would otherwise
    lose its newest children to every batch check). Patched out in tests."""
    out = subprocess.run(
        ["gh", "api", "--paginate",
         f"repos/{{owner}}/{{repo}}/issues/{spec}/sub_issues?per_page=100",
         "-q", ".[] | .number"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    return [int(line) for line in out.stdout.split() if line.strip()]


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
    """The spec number in `## Parent`, e.g. `#76, Implementation Decisions section 1`."""
    for line in section(body, "Parent"):
        m = ISSUE_REF_RE.search(line)
        if m:
            return int(m.group(1))
    return None


def blocked_by(body: str) -> list[int]:
    """The ticket numbers in `## Blocked by`. `None (can start immediately)` is empty.

    This section is the copy the user reads. What the graph is checked against is the
    tracker's own blocking links, `fetch_blocked_by`.
    """
    out = []
    for line in section(body, "Blocked by"):
        for m in ISSUE_REF_RE.finditer(line):
            out.append(int(m.group(1)))
    return out


def owns_globs(body: str) -> list[str]:
    """The paths this ticket is allowed to write, from `## Owns`. `(new)` is a note."""
    globs = []
    for line in section(body, "Owns"):
        m = re.match(r"^\s*-\s+(\S+)", line)
        if not m:
            continue
        value = m.group(1)
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


def last_verdict(comments: list[str]) -> str | None:
    """The commit on the newest `VERDICT <commit> by <model> — <one line>` line."""
    for comment in reversed(comments):
        for line in reversed(comment.splitlines()):
            m = VERDICT_RE.match(line.strip())
            if m:
                return m.group(1)
    return None


def last_run(comments: list[str]) -> str | None:
    """The newest `self-run` or `reverify` comment on the ticket, `None` when none."""
    for comment in reversed(comments):
        lines = comment.strip().splitlines()
        if lines and lines[0].strip() in ("self-run", "reverify"):
            return comment
    return None


def last_run_summary(comments: list[str]) -> str | None:
    """The summary line of the newest `self-run` or `reverify` comment on the ticket.

    A run comment opens with its own name and carries gate-check's summary on the line
    under it, so that line is what the ticket currently reports about its criteria.
    `None` when no run has been posted, or when the newest one printed no summary.
    """
    run = last_run(comments)
    if run is None:
        return None
    lines = run.strip().splitlines()
    summary = lines[1].strip() if len(lines) > 1 else ""
    return summary if SUMMARY_RE.match(summary) else None


def last_run_unmet(comments: list[str]) -> list[str]:
    """The criteria the newest run's ledger left unmet, by id."""
    run = last_run(comments)
    if run is None:
        return []
    return [c["id"] for c in parse_criteria(run)
            if not (c["ticked"] and c["evidence"] and c["evidence"] != "pending")]


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

    # The verifier's `VERDICT` is what a ticket needs to close as done, and only that.
    # Handing the ticket back is the way out of everything else, including a verifier
    # that never ran: `HANDOFF REQUIRED` claims nothing was finished and leaves the
    # ticket open under `needs-triage`, where it is judged fresh. Demanding an
    # independent check before a worker is allowed to say "I could not do this" would
    # leave it with no way out at all.
    if first == "ALL MET":
        # A draft is written by hand and the runs are not, so `ALL MET` in the draft is a
        # claim and the newest run's summary is the measurement. Only the newest one is
        # read: a criterion the verifier found unmet and the worker then fixed is met
        # again on the self-run after the fix, and that run is the one this sees.
        # A run is generated from the ticket body, which carries no `ABANDON:` line, so a
        # criterion the draft abandons as `decision` still runs and still reports unmet.
        # That unmet is the one this draft is allowed to carry: the sub-issue is open and
        # the ticket closes on it. Any other unmet in that run is a claim the draft
        # cannot make.
        decided = {a["ac"] for a in abandons if a["kind"] == "decision"}
        summary = last_run_summary(comments)
        unmet = last_run_unmet(comments)
        covered = (summary is not None and summary.startswith("UNMET:")
                   and unmet and set(unmet) <= decided)
        if summary and summary.startswith(("UNMET:", "HANDOFF REQUIRED:")) and not covered:
            problems.append("the newest run on the ticket still reports unmet or abandoned "
                            "criteria — rerun until the summary line is `ALL MET (...)`, "
                            "or close out as `HANDOFF REQUIRED`")
        verdict = last_verdict(comments)
        if verdict is None:
            problems.append("the ticket carries no `VERDICT <commit> by <model> — …` line, "
                            "so nothing but this ticket's own author says the work is done. "
                            "Dispatch the verifier; if it cannot run, close out as "
                            "`HANDOFF REQUIRED` instead and say so")
        elif not git("rev-parse", "HEAD").startswith(verdict) \
                and draft_line(draft, "Post-verdict:") is None:
            problems.append(f"the `VERDICT` is on {verdict} and HEAD has moved on; add a "
                            f"`Post-verdict:` line naming every commit since it and where "
                            f"it came from")
    return problems


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
    """Check unique ids, valid dependency references, and no cycles."""
    errors = []

    seen = set()
    for entry in entries:
        if entry["id"] in seen:
            errors.append(f"duplicate ticket: #{entry['id']}  [duplicate-ticket]")
        seen.add(entry["id"])

    for entry in entries:
        for dep in entry["dependencies"]:
            if dep not in seen:
                errors.append(f"dangling dependency: #{entry['id']} is blocked by #{dep}, "
                              f"which is not a ticket under this spec  [dangling]")

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
    `dispatch.sh` and `board.py` all honour it — but it is not an edge this graph can
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
    `dispatch.sh` and `board.py` all refuse to start a ticket while one of these is
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
    """One entry per ticket: the tracker's blocking links, and the ticket's own copy.

    `dependencies` is what the tracker records, and it is the graph every check below
    runs on — the same edges `--preflight` refuses on and `board.py` dispatches from.
    `stated` is the `## Blocked by` section of the ticket body, carried alongside so
    `blocked_by_mismatch` can hold the two accounts of one edge against each other.

    A dependency outside this batch is kept, and `outside` says what was found at the
    other end of it: `{number: {"spec": …, "state": …}}`. One lookup per distinct
    blocker rather than one per edge — several tickets of a batch commonly wait on the
    same one.
    """
    batch = set(numbers)
    entries = [{"id": n, "dependencies": fetch_blocked_by(n), "stated": blocked_by(fetch_body(n))}
               for n in numbers]
    found: dict[int, dict] = {}
    for entry in entries:
        for dep in entry["dependencies"]:
            if dep not in batch and dep not in found:
                found[dep] = fetch_outsider(dep)
    for entry in entries:
        entry["outside"] = {d: found[d] for d in entry["dependencies"] if d in found}
    return entries


def blocked_by_mismatch(entries: list[dict]) -> list[str]:
    """Tickets whose `## Blocked by` section and blocking links do not name the same set.

    A reader of the ticket sees the section; every command in this pipeline sees the
    links. When the two differ, the ticket says one thing about what has to land first
    and the tracker says another, and neither the reader nor the graph can tell which
    the batch was planned around.
    """
    findings = []
    for entry in entries:
        native = set(entry["dependencies"])
        stated = set(entry.get("stated", []))
        if native == stated:
            continue
        sides = []
        if stated - native:
            sides.append("`## Blocked by` names "
                         + ", ".join(f"#{n}" for n in sorted(stated - native))
                         + ", which the tracker does not link")
        if native - stated:
            sides.append("the tracker links "
                         + ", ".join(f"#{n}" for n in sorted(native - stated))
                         + ", which `## Blocked by` does not name")
        findings.append(f"#{entry['id']}: " + "; ".join(sides)
                        + ". The graph is checked against the links, so fix whichever "
                          "side is wrong until both name the same tickets.")
    return findings


# ---------------------------------------------------------- worker mechanical

def refuse(message: str) -> int:
    """Exit 2 with the reason on stderr. Nothing is posted."""
    sys.stderr.write(message.rstrip() + "\n")
    return 2


def last_comment_opening(comments: list[str], prefix: str) -> str | None:
    """The newest comment whose first line is `prefix` or starts `prefix `."""
    for comment in reversed(comments):
        first = comment.strip().splitlines()[0].strip() if comment.strip() else ""
        if first == prefix or first.startswith(prefix + " "):
            return comment
    return None


def last_self_run(comments: list[str]) -> str | None:
    """The newest comment whose first line is `self-run`, `None` when none."""
    return last_comment_opening(comments, "self-run")


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


def decisions_line_for(decisions: str | None, path: str) -> str:
    """The sentence in the `DECISIONS` comment that names `path`."""
    if not decisions:
        return path
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
    if last_comment_opening(comments, "DECISIONS") is not None:
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
        return refuse("the file must have exactly two sections, "
                      "`Decisions I made on my own` then `Outside Owns`")
    run = last_self_run(comments)
    if run is None:
        return refuse(f"#{number} carries no self-run comment to check Outside Owns against")
    want = outside_owns_from(run)
    got = outside_owns_from("\n".join(section(text, "Outside Owns")))
    if want != got:
        return refuse("the file's `Outside Owns` line does not match the newest self-run")
    posted = "DECISIONS\n\n" + text.lstrip("\n")
    if not posted.endswith("\n"):
        posted += "\n"
    post_comment(number, posted)
    print(f"DECISIONS: posted on #{number}")
    return 0


def run_touched(number: int) -> int:
    """Comment `TOUCHED BY #<n>` on open siblings whose `## Owns` covers a file."""
    comments = fetch_comments(number)
    review = last_comment_opening(comments, "REVIEW")
    if review is None:
        return refuse(f"#{number} carries no REVIEW comment")
    run = last_self_run(comments)
    if run is None:
        return refuse(f"#{number} carries no self-run comment")
    files = outside_owns_files(outside_owns_from(run))
    if not files:
        return 0
    decisions = last_comment_opening(comments, "DECISIONS")
    spec = parent_spec(fetch_body(number))
    if spec is None:
        return refuse(f"#{number} has no spec in `## Parent`")
    posted_to: list[int] = []
    for path in files:
        sentence = decisions_line_for(decisions, path)
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
            ac,
        ]
        if judgement:
            lines.append(judgement)
        comment = "\n".join(lines) + "\n"
        for child in fetch_sub_issues(spec):
            ticket = fetch_ticket(child)
            if (ticket.get("state") or "").upper() != "OPEN":
                continue
            globs = owns_globs(fetch_body(child))
            if not any(glob_covers(g, path) for g in globs):
                continue
            post_comment(child, comment)
            posted_to.append(child)
    if posted_to:
        print("TOUCHED: " + ", ".join(f"#{n}" for n in posted_to))
    return 0


def run_draft(number: int, out_file: Path) -> int:
    """Write the closing-comment skeleton to `out_file`."""
    body = fetch_body(number)
    comments = fetch_comments(number)
    run = last_self_run(comments)
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
    verdict = last_verdict(comments)
    chain = ""
    if verdict and head and not head.startswith(verdict):
        chain = git("log", "--first-parent", "--format=%H", f"{verdict}..HEAD")
    post = "Post-verdict: " + (", ".join(chain.split()) if chain else "None")
    review = last_comment_opening(comments, "REVIEW") or ""
    files = outside_owns_files(outside_owns_from(run or ""))
    if files:
        judged = []
        for path in files:
            judgement = spec_judgement(review, path)
            judged.append(f"{path} ({judgement})" if judgement else path)
        outside = "Outside Owns: " + ", ".join(judged)
    else:
        outside = "Outside Owns: None"
    spec = parent_spec(body)
    opened: list[str] = []
    if spec is not None:
        marker = re.compile(rf"^SUB-ISSUE \S+ from #{number}$")
        for child in fetch_sub_issues(spec):
            child_body = fetch_body(child)
            first_line = child_body.strip().splitlines()[0] if child_body.strip() else ""
            if marker.match(first_line):
                opened.append(f"#{child}")
    sub = "Sub-issues opened: " + (", ".join(opened) if opened else "none")
    counts_line = (f"Counts: {counts['met']} met, {counts['unmet']} unmet, "
                   f"{counts['abandoned']} abandoned of {counts['total']}")
    parts = [first, "", branch_line, "", post, ""]
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
    """Open a `needs-triage` sub-issue under the spec named in `## Parent`."""
    if kind not in SUB_ISSUE_KINDS:
        return refuse(f"kind `{kind}` is not one of {', '.join(SUB_ISSUE_KINDS)}")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not text.strip():
        return refuse(f"{path} is empty")
    spec = parent_spec(fetch_body(number))
    if spec is None:
        return refuse(f"#{number} has no spec in `## Parent`")
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
             "--parent", str(spec),
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
    print(found.group(1) if found else printed)
    return 0


# ----------------------------------------------------------------- subcommands

def run_checks(number: int, reverify: bool, timeout: int | None) -> int:
    body = fetch_body(number)
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
    post_comment(number, comment)
    return result.returncode


def refusals(number: int, ticket: dict, me: str, branch: str, dirty: list[str]) -> list[str]:
    """Why this ticket is not ready to be worked on, in the order a worker would hit it.

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
        out.append(f"NOT_READY: branch is {branch or '(detached)'}, not issue-{number}; "
                   f"dispatch opens this worktree on issue-{number}, so you were started "
                   f"somewhere else — stop, do not switch branches yourself")
    if dirty:
        out.append(f"NOT_READY: {len(dirty)} tracked files already have uncommitted changes "
                   f"before any work started; they are not yours to commit or discard — "
                   f"stop and leave the tree as you found it")
    state = ticket.get("state", "")
    if state != "OPEN":
        out.append(f"NOT_READY: #{number} is {state or 'unreadable'}, not OPEN; "
                   f"nothing for you to do here — stop, this comment is the record")
    labels = [label.get("name", "") for label in ticket.get("labels", [])]
    if "ready-for-agent" not in labels:
        out.append(f"NOT_READY: #{number} has no ready-for-agent label, so it has not been "
                   f"cleared for an agent yet; stop and leave it to whoever triages it")
    blockers = [b for b in ticket.get("blockedBy", {}).get("nodes", [])
                if b.get("state") != "CLOSED"]
    if blockers:
        names = ", ".join(f"#{b['number']}" for b in blockers)
        out.append(f"NOT_READY: #{number} is blocked by {names}; stop — `dispatch.sh` "
                   f"starts this ticket again once those close, so do not wait or retry")
    holders = [a.get("login", "") for a in ticket.get("assignees", [])]
    others = [h for h in holders if h != me]
    if others:
        out.append(f"NOT_READY: #{number} is assigned to {', '.join(others)}, not you ({me}); "
                   f"stop rather than work on someone else's ticket")
    return out


def run_preflight(number: int) -> int:
    """Claim the ticket, or say on the ticket itself why it cannot be claimed."""
    root = repo_root()
    problems = refusals(number, fetch_ticket(number), gh_login(),
                        current_branch(root), dirty_tracked(root))
    if problems:
        reason = problems[0]
        post_comment(number, reason)
        sys.stderr.write(reason + "\n")
        return 2
    assign_self(number)
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
    reviews = [c for c in comments if c.strip().startswith("REVIEW ")]
    if not reviews:
        return []
    spec_axis = re.split(r"^## Tests", reviews[-1], maxsplit=1, flags=re.M)[0]
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
    problems = draft_problems(draft, comments)
    problems += review_problems(draft, fetch_body(number), comments)
    problems += git_problems(repo_root())
    ticket = fetch_ticket(number)
    if ticket.get("state") != "OPEN":
        problems.append(f"#{number} is already {ticket.get('state', 'unreadable')}")
    me = gh_login()
    if not any(a.get("login") == me for a in ticket.get("assignees", [])):
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

    first = draft.strip().splitlines()[0].strip()
    if first == "ALL MET":
        ok, extra = run_target_json_checks(repo_root())
        if not ok:
            post_comment(number, extra)
            sys.stderr.write(extra.splitlines()[0] + "\n")
            return 1
        if extra:
            draft = draft.rstrip("\n") + "\n" + extra

    post_comment(number, draft)
    if draft.strip().splitlines()[0].strip() == "ALL MET":
        close_ticket(number)
        print(f"CLOSED: #{number}")
    else:
        hand_back_for_triage(number)
        print(f"HANDED BACK: #{number} is now needs-triage and stays open")
    return 0


def lint_ticket_graph(number: int, body: str) -> int:
    """Read the batch this ticket belongs to and check it is a startable graph."""
    spec = parent_spec(body)
    if spec is None:
        print("ticket graph: no `## Parent` section, so there is no batch to check")
        return 0
    numbers = fetch_sub_issues(spec)
    if not numbers:
        print(f"  ERROR #{spec} has no sub-issues — publish tickets as sub-issues of the "
              f"spec, or the graph cannot be checked  [no-sub-issues]")
        return 1
    entries = ticket_entries(numbers)
    # Printed before the errors, because an error returns here and a disagreement about
    # an edge is often what the error is: a cycle or a dangling link the section denies.
    for finding in blocked_by_mismatch(entries):
        print("  WARN  " + finding + "  [blocked-by-mismatch]")
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


def stated_worker(body: str) -> str:
    """The worker the `## Worker` section names, or "" when it names none."""
    for line in section(body, "Worker"):
        for word in re.findall(r"[a-z0-9-]+", line):
            if WORKER_LABEL_RE.match(word):
                return word
    return ""


def lint_worker(labels: list[str], body: str) -> tuple[list[str], list[str]]:
    """Which worker this ticket gets, said on the tracker and again in the body.

    `dispatch.sh` reads the label and nothing else, and a ticket carrying none is worked
    by whichever worker the default is rather than the one it was written for. The
    `## Worker` section is the reader's copy of the same answer; the two saying different
    things leaves nobody able to tell which the ticket was planned around.

    Returns `(errors, warnings)`. A ticket outside the agent queue gets neither: what it
    holds is one thing for the user to look at, and no worker is started on it.
    """
    if "ready-for-agent" not in labels:
        return [], []
    marked = sorted(name for name in labels if WORKER_LABEL_RE.match(name or ""))
    if len(marked) > 1:
        return ([f"carries {len(marked)} worker labels ({', '.join(marked)}), and it "
                 f"takes one"], [])
    if not marked:
        return (["carries no worker label: add `junior-worker` or `senior-worker`, so "
                 "every start puts it on the row it was written for"], [])
    stated = stated_worker(body)
    if not stated:
        return ([], [f"is labelled {marked[0]}, and no `## Worker` section says so"])
    if stated != marked[0]:
        return ([], [f"is labelled {marked[0]}, and `## Worker` says {stated}"])
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


def body_outside(body: str, heading: str) -> str:
    """The whole ticket except one `## <heading>` section."""
    lines = body.splitlines()
    kept, skipping = [], False
    for line in lines:
        if line.startswith("## "):
            skipping = line.strip() == f"## {heading}"
        if not skipping:
            kept.append(line)
    return "\n".join(kept)


def lint_edges(body: str) -> list[str]:
    """Blocking edges that nothing else on the ticket accounts for.

    A `## Blocked by` entry earns its place by being visible elsewhere: named in
    `## What to build`, listed under `## Read first`, needed by a criterion, or holding a
    file two tickets would otherwise both write. An edge that appears nowhere but the
    `## Blocked by` section is one nobody can check — it is as likely to be a dependency
    somebody forgot to explain as one that was never real. This narrows what to read; it
    does not decide which.
    """
    findings = []
    elsewhere = body_outside(body, "Blocked by")
    for ticket in blocked_by(body):
        if not re.search(rf"#{ticket}\b", elsewhere):
            findings.append(
                f"#{ticket} blocks this ticket, but nothing outside `## Blocked by` mentions "
                f"it. Say where the dependency bites — the criterion that needs its output, "
                f"or the file both tickets would write — or drop the edge.")
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
# The two scripts of this pipeline a criterion may run, and what each must be given.
# Their addresses come from the repository's `.mmw/target.json`, never from the line.
PIPELINE_SCRIPTS = {
    "visual-parity.py": {"required": ("--contract", "--mount"),
                         "retired": ("--baseline", "--impl", "--cdp", "--backend", "--seed",
                                     "--impl-title", "--viewports")},
    "wiring-check.py": {"required": ("--contract", "--rows"),
                        "retired": ("--cdp", "--impl", "--backend", "--seed", "--impl-title")},
}
SPEC_SECTION_SOURCE_RE = re.compile(r"^#(\d+) (Implementation Decisions|Testing Decisions)\s*(\d+)?")
ADR_SOURCE_RE = re.compile(r"^ADR-(\d{4})")
TICKET_SOURCE_RE = re.compile(r"^#(\d+)(?:\s|$)")
DOC_SOURCE_RE = re.compile(r"^(docs/\S+)")
STORY_SOURCE_RE = re.compile(r"^#\d+ story \d+")
_HELP_FLAGS: dict[str, set[str]] = {}


def script_segment(check: str, script: str) -> str:
    """The part of a CHECK from the script's name to the end of that command."""
    i = check.find(script)
    if i < 0:
        return ""
    rest = check[i + len(script):]
    return re.split(r"\s*(?:&&|\|\||;|\|)(?:\s|$)", rest, maxsplit=1)[0]


def help_flags(script: str) -> set[str]:
    """The flags the installed script actually accepts, read from its `--help` once.
    This is the one place a criterion's reference to a capability that does not exist
    yet is caught at the moment it is written."""
    if script not in _HELP_FLAGS:
        path = HERE / script
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
        segment = script_segment(check, script)
        flags = set(FLAG_RE.findall(segment))
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


def mechanism_findings(number: int | None, body: str, doc: dict, row_ids: list[str],
                       mounts: list[str]) -> list[str]:
    """A ticket that uses mechanism M is blocked by M's `built_by`, unless it is that
    ticket. Uses: the `reach` of the rows it owns and of the scenes under its mounts."""
    raw = doc.get("mechanisms") or {}
    if isinstance(raw, list):
        return []
    mechanisms = {str(k): (v or {}) for k, v in raw.items()}
    rows = {str(r.get("id")): r for r in doc.get("rows") or []}
    used: set[str] = set()
    for rid in row_ids:
        r = rows.get(rid) or {}
        if r.get("reach"):
            used.add(str(r["reach"]))
    pages = doc.get("pages") or {}
    for name, decl in (doc.get("scenes") or {}).items():
        decl = decl or {}
        mount = decl.get("mount") or (pages.get(decl.get("page")) or {}).get("mount")
        if mount in mounts:
            used.update(str(x) for x in decl.get("reach") or [])
    blockers = set(blocked_by(body))
    findings = []
    for mech in sorted(used):
        built = str((mechanisms.get(mech) or {}).get("built_by") or "")
        m = re.match(r"^#(\d+)$", built)
        if not m:
            continue
        builder = int(m.group(1))
        if builder != number and builder not in blockers:
            findings.append(f"mechanism {mech} is built by #{builder}, which `## Blocked by` "
                            f"does not name")
    return findings


def scenes_by_mount(doc: dict) -> dict[str, list[str]]:
    pages = doc.get("pages") or {}
    out: dict[str, list[str]] = {}
    for name, decl in (doc.get("scenes") or {}).items():
        decl = decl or {}
        mount = str(decl.get("mount") or (pages.get(decl.get("page")) or {}).get("mount") or "")
        out.setdefault(mount, []).append(name)
    return out


NON_COMPARING_MODES = ("--addressing", "--render-only", "--shows-perturbation")


def parity_calls(body: str) -> list[tuple[str, list[str], list[str] | None]]:
    """`(gate_id, mounts, explicit scenes or None)` per criterion that compares with
    visual-parity.py. Its other modes (`--addressing`, `--render-only`,
    `--shows-perturbation`) cover no scene for the partition and are left out."""
    out = []
    for gate_id, check, _ in criteria_lines(body):
        if "visual-parity.py" not in check:
            continue
        segment = script_segment(check, "visual-parity.py")
        if any(mode in segment.split() for mode in NON_COMPARING_MODES):
            continue
        m = re.search(r"--mount\s+(\S+)", segment)
        mounts = [x for x in (m.group(1).split(",") if m else []) if x]
        s = re.search(r"--scenes\s+(\S+)", segment)
        explicit = [x for x in s.group(1).split(",") if x] if s else None
        out.append((gate_id, mounts, explicit))
    return out


def scene_findings(body: str, doc: dict) -> list[str]:
    """An explicit `--scenes` list is a subset of what its `--mount` derives."""
    findings = []
    by_mount = scenes_by_mount(doc)
    for gate_id, mounts, explicit in parity_calls(body):
        if mounts == ["all"]:
            mounts = [m for m in by_mount if m]
        derived = {s for m in mounts for s in by_mount.get(m, [])}
        for m in mounts:
            if m not in by_mount:
                findings.append(f"{gate_id}: --mount {m} is declared by no page of the contract")
        if explicit:
            outside = [s for s in explicit if s not in derived]
            if outside:
                findings.append(f"{gate_id}: --scenes names scenes outside its mounts: "
                                f"{', '.join(outside)}")
    return findings


def lint_scene_partition(bodies: dict[int, str], doc: dict) -> list[str]:
    """Across a batch, the scenes the parity criteria cover — by mount, narrowed by an
    explicit `--scenes` — are the contract's scenes, each exactly once, and every page's
    mount is owned by some ticket. Two tickets ordered by `## Blocked by` are not a
    split: the later one re-runs the earlier one's scenes after changing something they
    rest on, so their overlap is a re-verification, not a double claim."""
    by_mount = scenes_by_mount(doc)
    all_scenes = {s for scenes in by_mount.values() for s in scenes}
    covered: dict[str, list[int]] = {}
    owned_mounts: set[str] = set()
    for number, body in bodies.items():
        for _, mounts, explicit in parity_calls(body):
            if mounts == ["all"]:
                mounts = [m for m in by_mount if m]
            owned_mounts.update(mounts)
            scenes = explicit if explicit else [s for m in mounts for s in by_mount.get(m, [])]
            for s in scenes:
                covered.setdefault(s, []).append(number)
    if not covered:
        return []
    findings = []
    for s in sorted(all_scenes - set(covered)):
        findings.append(f"scene {s} is covered by no ticket's parity criterion")
    blocks = {n: set(blocked_by(b)) for n, b in bodies.items()}

    def unordered(a: int, b: int) -> bool:
        return a not in blocks[b] and b not in blocks[a]

    for s, tickets in sorted(covered.items()):
        if any(unordered(a, b) for i, a in enumerate(tickets) for b in tickets[i + 1:]):
            findings.append(f"scene {s} is covered by more than one ticket: "
                            + ", ".join(f"#{t}" for t in tickets))
    for mount in sorted(set(by_mount) - owned_mounts):
        if mount:
            findings.append(f"mount {mount} is owned by no ticket in the batch")
    return findings


def lint_screen_contract(body: str, number: int | None = None) -> list[str]:
    """The interface rules of `to-tickets`, made mechanical.

    An interface ticket names its screen-contract rows under `## Read first`; a row with
    calls needs a wiring criterion (a `CHECK:` running `wiring-check.py` that names the
    row id); no `CHECK:` may stub the application's own network; the two pipeline scripts
    are given what they need and nothing they retired; every mechanism the ticket uses
    is built by a ticket it is blocked by; every baseline-class source of an owned row is
    under `## Read first` and every spec-section source is named by `## Parent`; an
    explicit `--scenes` list stays inside its `--mount`.
    """
    findings: list[str] = []
    read_first = "\n".join(section(body, "Read first"))
    parent_text = "\n".join(section(body, "Parent"))
    checks = criteria_lines(body)
    for gate_id, check, _ in checks:
        findings.extend(lint_pipeline_flags(gate_id, check))
        if FETCH_STUB_RE.search(check):
            findings.append(f"{gate_id}: CHECK stubs the application's own network; a "
                            f"wiring criterion reads the backend instead")
    m = SCREEN_CONTRACT_ROWS_RE.search(read_first)
    interface_ticket = any("visual-parity.py" in check for _, check, _ in checks)
    if not m:
        if interface_ticket:
            findings.append("interface ticket (a criterion runs visual-parity.py) names no "
                            "`screen-contract.yaml rows: <id, id>` line under `## Read first`")
        return findings
    row_ids = ROW_ID_RE.findall(m.group(1))
    doc, contract_path = load_contract_doc(read_first)
    if doc is None and contract_path:
        findings.append(f"the contract {contract_path} could not be read from here (not in "
                        f"the working tree, or neither pyyaml nor uv is available); the "
                        f"source, mechanism and scene rules did not run")
    rows_with_calls = set(row_ids)
    if doc is not None:
        try:
            rows_with_calls = {r["id"] for r in doc.get("rows") or []
                               if r["id"] in row_ids and (r.get("calls") or []) != ["none"]}
        except (KeyError, TypeError):
            pass
    wiring_checks = [check for _, check, _ in checks if "wiring-check.py" in check]
    for rid in sorted(rows_with_calls):
        if not any(rid in check for check in wiring_checks):
            findings.append(f"row {rid} has calls but no criterion runs wiring-check.py naming it")
    if doc is not None:
        mounts = [m for _, ms, _ in parity_calls(body) for m in ms]
        findings.extend(source_findings(row_ids, doc, read_first, parent_text))
        findings.extend(mechanism_findings(number, body, doc, row_ids, mounts))
        findings.extend(scene_findings(body, doc))
    return findings


def lint_batch_scenes(number: int, body: str) -> list[str]:
    """The scene partition across the batch, read when this ticket runs visual-parity.py."""
    if not parity_calls(body):
        return []
    doc, _ = load_contract_doc("\n".join(section(body, "Read first")))
    if doc is None:
        return []
    spec = parent_spec(body)
    if spec is None:
        return []
    bodies = {number: body}
    for n in fetch_sub_issues(spec):
        if n == number:
            continue
        try:
            if fetch_outsider(n).get("state") == "CLOSED":
                continue  # a closed ticket's criteria cover nothing any more
            bodies[n] = fetch_body(n)
        except Exception:  # noqa: BLE001
            continue
    return lint_scene_partition(bodies, doc)


def run_lint(number: int) -> int:
    body = fetch_body(number)
    labels = [label.get("name") or "" for label in fetch_ticket(number).get("labels") or []]
    worker_errors, worker_warnings = lint_worker(labels, body)

    def report_worker() -> None:
        for finding in worker_errors:
            print(f"  ERROR #{number} " + finding + "  [worker-label]")
        for finding in worker_warnings:
            print(f"  WARN  #{number} " + finding + "  [worker-mismatch]")

    # A `ready-for-human` ticket carries no criteria at all: what it holds is one thing
    # for the user to look at. gate-lint has nothing to say about it, and
    # saying "zero live gates" would report the ticket's correct shape as a fault. Its
    # place in the batch is still worth checking, so the graph check runs.
    if not section(body, "Acceptance criteria"):
        print(f"#{number} carries no `## Acceptance criteria`, so only the ticket graph "
              f"is checked here")
        report_worker()
        return lint_ticket_graph(number, body) or (1 if worker_errors else 0)

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
    for finding in lint_batch_scenes(number, body):
        print("  ERROR " + finding + "  [screen-contract]")
        broken.append(finding)
    for finding in lint_check_effects(body):
        print("  WARN  " + finding + "  [shared-state]")
    for finding in lint_edges(body):
        print("  WARN  " + finding + "  [unexplained-edge]")
    report_worker()

    graph = lint_ticket_graph(number, body)
    return result.returncode or graph or (1 if broken or worker_errors else 0)


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
                        help="open a needs-triage sub-issue under the spec")
    args = parser.parse_args(argv)
    chosen = [name for name, on in
              (("--lint", args.lint), ("--reverify", args.reverify),
               ("--preflight", args.preflight), ("--closeout", args.closeout is not None),
               ("--decisions", args.decisions is not None), ("--touched", args.touched),
               ("--draft", args.draft is not None),
               ("--sub-issue", args.sub_issue is not None)) if on]
    if len(chosen) > 1:
        parser.error(f"{' and '.join(chosen)} are different jobs; pick one")
    if args.check_only and args.closeout is None:
        parser.error("--check-only belongs to --closeout")
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
    if args.lint:
        return run_lint(args.ticket)
    return run_checks(args.ticket, args.reverify, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
