#!/usr/bin/env python3
"""Run a ticket's acceptance criteria and post the result back to the ticket.

The ticket is the only state. Every run reads the `## Acceptance criteria` and
`## Owns` sections fresh from the issue, writes them to a throwaway ledger, hands
that ledger to unlazy's `gate-check.mjs`, and posts the updated ledger back as one
comment. Nothing is cached and no file is left behind.

    verify-ticket.py <n>              run the unmet criteria, comment `self-run`
    verify-ticket.py <n> --reverify   re-run every criterion, comment `reverify`
    verify-ticket.py <n> --lint       audit how the criteria are written; print only
    verify-ticket.py <n> --preflight  claim the ticket, or refuse and say why
    verify-ticket.py <n> --closeout <draft>  check the closing comment, then post it

Exit code follows gate-check: 0 all met, 1 unmet or abandoned, 2 usage or
infrastructure. `--preflight` exits 2 when it refuses; `--closeout` exits 1.
"""

from __future__ import annotations

import argparse
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
TTL_MS = "86400000"

ABANDON_KINDS = ("failed", "blocked", "impossible", "decision")
HANDOFF_KINDS = ("failed", "blocked", "impossible")
ABANDON_RE = re.compile(r"^ABANDON:\s+(\S+)\s+(\S+)\s*(.*)$")
COUNTS_RE = re.compile(
    r"^Counts:\s*(\d+)\s+met,\s*(\d+)\s+unmet,\s*(\d+)\s+abandoned,\s*(\d+)\s+manual of\s*(\d+)\s*$")
HANDOFF_RE = re.compile(
    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(([^)]*)\),\s*(\d+)\s+unmet,\s*(\d+)\s+met of\s*(\d+)\s*$")
VERDICT_RE = re.compile(r"^VERDICT\s+([0-9a-fA-F]{7,40})\b")
ISSUE_REF_RE = re.compile(r"#(\d+)")
EXPECT_LINE_RE = re.compile(r"^\s+EXPECT:\s*(.+?)\s*$")
CHECK_LINE_RE = re.compile(r"^\s+CHECK:\s*(.+?)\s*$")
ATTR_LINE_RE = re.compile(r"^\s+(CHECK|EXPECT|EVIDENCE|CWD|MANUAL):")
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
    """Close the ticket as done. Patched out in tests."""
    subprocess.run(["gh", "issue", "close", str(number), "--reason", "completed"], check=True, env=GH_ENV)


def hand_to_human(number: int) -> None:
    """Move the ticket out of the agent lane. Patched out in tests."""
    subprocess.run(
        ["gh", "issue", "edit", str(number),
         "--remove-label", "ready-for-agent", "--add-label", "ready-for-human"],
        check=True, env=GH_ENV,
    )


def fetch_sub_issues(spec: int) -> list[int]:
    """The tickets GitHub records under `spec`, in its own order. Patched out in tests."""
    out = subprocess.run(
        ["gh", "api", f"repos/{{owner}}/{{repo}}/issues/{spec}/sub_issues",
         "-q", "[.[] | .number] | @json"],
        capture_output=True, text=True, check=True, env=GH_ENV,
    )
    text = out.stdout.strip()
    return json.loads(text) if text else []


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
    """The ticket numbers in `## Blocked by`. `None (can start immediately)` is empty."""
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


def current_branch(root: Path | None = None) -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)


def dirty_tracked(root: Path | None = None) -> list[str]:
    """Uncommitted changes to tracked files. Untracked files do not count: a CHECK
    command writes its own evidence pages and cache directories as it runs."""
    out = git("status", "--porcelain", "--untracked-files=no", cwd=root)
    return [line for line in out.splitlines() if line.strip()]


def is_ancestor(commit: str, descendant: str, root: Path | None = None) -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, descendant],
        capture_output=True, text=True, cwd=root,
    )
    return result.returncode == 0


def outside_owns(globs: list[str], root: Path) -> list[str]:
    """Files changed since the branch left main that no `## Owns` glob covers."""
    base = git("merge-base", "main", "HEAD", cwd=root)
    if not base:
        return []
    args = ["diff", "--name-only", f"{base}..HEAD", "--", "."]
    args += [f":(glob,exclude){g}" for g in globs]
    out = git(*args, cwd=root)
    return [line for line in out.splitlines() if line.strip()]


# ------------------------------------------------------------------- ledger

def ledger_from_comment(comment: str) -> list[str]:
    """The ledger a previous run posted: from its first gate line to `Outside Owns:`."""
    lines = comment.splitlines()
    start = next((i for i, l in enumerate(lines) if GATE_LINE_RE.match(l)), None)
    if start is None:
        return []
    end = next((i for i, l in enumerate(lines[start:], start)
                if l.startswith("Outside Owns:")), len(lines))
    out = lines[start:end]
    while out and not out[-1].strip():
        out.pop()
    return out


def previous_ledger(number: int) -> list[str]:
    """The ledger from the newest `self-run` / `reverify` comment, if there is one.

    A re-verification re-runs what the last run ticked, and the ticket body is never
    edited, so the previous run's comment is where that state lives.
    """
    for comment in reversed(fetch_comments(number)):
        first = comment.strip().splitlines()[0].strip() if comment.strip() else ""
        if first in ("self-run", "reverify"):
            ledger = ledger_from_comment(comment)
            if ledger:
                return ledger
    return []


def write_ledger(body: str, directory: Path, lines: list[str] | None = None) -> Path:
    """The `## Acceptance criteria` section, verbatim, as a ledger file."""
    criteria = lines if lines is not None else section(body, "Acceptance criteria")
    path = directory / LEDGER_NAME
    path.write_text("\n".join(criteria) + "\n", encoding="utf-8")
    return path


def count_gates(ledger: Path) -> tuple[int, int]:
    """(met, total) read off the ledger: a met gate is ticked with real evidence."""
    met = total = 0
    lines = ledger.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = GATE_LINE_RE.match(line)
        if not m:
            continue
        total += 1
        if m.group(1) == " ":
            continue
        evidence = ""
        for follow in lines[i + 1:]:
            if GATE_LINE_RE.match(follow):
                break
            if follow.strip().startswith("EVIDENCE:"):
                evidence = follow.split("EVIDENCE:", 1)[1].strip()
                break
        if evidence and evidence != "pending":
            met += 1
    return met, total


# ------------------------------------------------------------- closing comment

def parse_criteria(text: str) -> list[dict]:
    """One record per criterion: its id, its tick, its evidence, and whether it is manual.

    A criterion ends where the next one begins, not where the indentation stops. A
    `CHECK:` may run to several lines and those lines are flush left (`12-decisions.md`
    G6), so reading a criterion by indentation stops at the first continuation line and
    never reaches the `EVIDENCE:` below it — every such criterion then looks ticked with
    nothing to show for it, and its ticket can never close. `count_gates` already breaks
    on the next criterion; this is the same reading.
    """
    out = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = GATE_LINE_RE.match(line)
        if not m:
            continue
        item = {"id": m.group(2), "ticked": m.group(1) != " ", "evidence": "", "manual": False}
        for follow in lines[i + 1:]:
            if GATE_LINE_RE.match(follow):
                break
            stripped = follow.strip()
            if stripped.startswith("EVIDENCE:"):
                item["evidence"] = stripped.split("EVIDENCE:", 1)[1].strip()
            elif stripped.startswith("MANUAL:"):
                item["manual"] = True
        out.append(item)
    return out


def parse_abandons(text: str) -> list[dict]:
    """The `ABANDON: AC<n> <kind> <reason>` lines, which sit flush left under their criterion."""
    out = []
    for line in text.splitlines():
        m = ABANDON_RE.match(line)
        if m:
            out.append({"ac": m.group(1), "kind": m.group(2), "reason": m.group(3).strip()})
    return out


def tally(criteria: list[dict], abandons: list[dict]) -> dict:
    """Recount the draft. A tick with `EVIDENCE: pending` is unmet, not met; a manual
    criterion nobody has filled in is neither (`12-decisions.md` H6)."""
    abandoned_ids = {a["ac"] for a in abandons}
    counts = {"met": 0, "unmet": 0, "abandoned": 0, "manual": 0, "total": len(criteria)}
    for c in criteria:
        filled = c["evidence"] and c["evidence"] != "pending"
        if c["id"] in abandoned_ids:
            counts["abandoned"] += 1
        elif c["ticked"] and filled:
            counts["met"] += 1
        elif c["manual"] and not filled:
            counts["manual"] += 1
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
    """The commit on the newest `VERDICT <commit> <level> …` line the verifier left."""
    for comment in reversed(comments):
        for line in reversed(comment.splitlines()):
            m = VERDICT_RE.match(line.strip())
            if m:
                return m.group(1)
    return None


def draft_problems(draft: str, comments: list[str]) -> list[str]:
    """Everything wrong with the draft itself, in the order a reader would hit it."""
    problems = []
    lines = draft.strip().splitlines()
    first = lines[0].strip() if lines else ""
    handoff = HANDOFF_RE.match(first)
    if first != "ALL MET" and not handoff:
        return ["first line is neither `ALL MET` nor `HANDOFF REQUIRED: <n> abandoned "
                "(<kinds>), <m> unmet, <k> met of <total>`: " + (first or "(empty draft)")]

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
        if c["ticked"] and (not c["evidence"] or c["evidence"] == "pending"):
            problems.append(f"{c['id']} is ticked but its EVIDENCE is pending; "
                            f"either fill in what proved it or untick it")

    counts = tally(criteria, abandons)
    if first == "ALL MET" and counts["unmet"]:
        problems.append(f"first line is `ALL MET` but {counts['unmet']} criteria are unmet")

    opened = set(ISSUE_REF_RE.findall(draft_line(draft, "Sub-issues opened:") or ""))
    unfilled_manual = [c["id"] for c in criteria
                       if c["manual"] and (not c["evidence"] or c["evidence"] == "pending")]
    if len(opened) < len(unfilled_manual):
        problems.append(f"{len(unfilled_manual)} MANUAL criteria "
                        f"({', '.join(unfilled_manual)}) still need a person, but "
                        f"`Sub-issues opened:` lists {len(opened)} sub-issues; open one per "
                        f"criterion so the ticket itself can close")

    stated = draft_line(draft, "Counts:")
    m = COUNTS_RE.match("Counts: " + stated) if stated is not None else None
    if not m:
        problems.append("no `Counts: <k> met, <m> unmet, <n> abandoned, <j> manual of <total>` line")
    else:
        got = dict(zip(("met", "unmet", "abandoned", "manual", "total"),
                       (int(g) for g in m.groups())))
        if got != counts:
            problems.append(
                "Counts: says {met} met, {unmet} unmet, {abandoned} abandoned, {manual} manual "
                "of {total}".format(**got) +
                "; the draft reads {met} met, {unmet} unmet, {abandoned} abandoned, {manual} "
                "manual of {total}".format(**counts))
        if handoff:
            said = {"abandoned": int(handoff.group(1)), "unmet": int(handoff.group(3)),
                    "met": int(handoff.group(4)), "total": int(handoff.group(5))}
            off = [f"{k}: first line says {said[k]}, `Counts:` says {got[k]}"
                   for k in ("abandoned", "unmet", "met", "total") if said[k] != got[k]]
            if off:
                problems.append("the first line and the `Counts:` line disagree — "
                                + "; ".join(off))

    # The verifier's verdict is what a ticket needs to close as done, and only that.
    # Handing the ticket to a person is the way out of everything else, including a
    # verifier that never ran: `HANDOFF REQUIRED` claims nothing was finished, leaves
    # the ticket open under `ready-for-human`, and puts it in front of someone in the
    # morning. Demanding an independent check before a worker is allowed to say "I
    # could not do this" would leave it with no way out at all.
    if first == "ALL MET":
        verdict = last_verdict(comments)
        if verdict is None:
            problems.append("the ticket carries no `VERDICT <commit> <level> …` line, so "
                            "nothing but this ticket's own author says the work is done. "
                            "Dispatch the verifier; if it cannot run, close out as "
                            "`HANDOFF REQUIRED` instead and say so")
        elif not git("rev-parse", "HEAD").startswith(verdict) \
                and draft_line(draft, "Post-verdict:") is None:
            problems.append(f"the verdict is on {verdict} and HEAD has moved on; add a "
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
    if not is_ancestor("main", "HEAD", root):
        problems.append("this branch does not contain main; run `git merge main`. Do not "
                        "rebase — the verdict on this ticket names one commit, and rewriting "
                        "history throws it away")
        return problems
    base = git("merge-base", "main", "HEAD", cwd=root)
    if base and not git("diff", "--name-only", f"{base}..HEAD", cwd=root):
        sys.stderr.write("warning: this branch changes no files since it left main\n")
    return problems


# ---------------------------------------------------------------- ticket graph
# `validate_dag`, `_detect_cycles`, `_trace_cycle` and `compute_levels` are
# grok-bundled's `execute-plan/scripts/validate-plan.py` L145-280, function for
# function. Only the shape of an entry changed: an id is an issue number rather
# than a `pr-<n>` string, and dependencies come from `## Blocked by`.

def validate_dag(entries: list[dict]) -> list[str]:
    """Check unique ids, valid dependency references, and no cycles."""
    errors = []

    seen = set()
    for entry in entries:
        if entry["id"] in seen:
            errors.append(f"duplicate ticket: #{entry['id']}")
        seen.add(entry["id"])

    for entry in entries:
        for dep in entry["dependencies"]:
            if dep not in seen:
                errors.append(f"dangling dependency: #{entry['id']} is blocked by #{dep}, "
                              f"which is not a ticket under this spec")

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
        return ["cycle detected: " + " -> ".join(f"#{i}" for i in cycle)]
    return ["cycle detected involving: " + ", ".join(f"#{i}" for i in sorted(unvisited))]


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


def ticket_entries(numbers: list[int]) -> list[dict]:
    """One entry per ticket, its dependencies read off its own `## Blocked by`.

    A dependency on a ticket outside this batch is kept, so `validate_dag` reports it.
    """
    return [{"id": n, "dependencies": blocked_by(fetch_body(n))} for n in numbers]


# -------------------------------------------------------------------- herdr

def report_phase(ticket: int, phase: str, extra: dict[str, str] | None = None,
                 clear: list[str] | None = None) -> bool:
    """Publish where this ticket stands to the Herdr pane. Never fails a run."""
    if os.environ.get("HERDR_ENV") != "1":
        return False
    pane = os.environ.get("HERDR_PANE_ID")
    if not pane:
        return False
    cmd = [
        "herdr", "pane", "report-metadata", pane, "--source", "mmw",
        "--token", f"ticket={ticket}", "--token", "role=worker",
        "--token", f"phase={phase}", "--ttl-ms", TTL_MS,
    ]
    for key, value in (extra or {}).items():
        cmd += ["--token", f"{key}={value}"]
    for key in (clear or []):
        cmd += ["--clear-token", key]
    try:
        subprocess.run(cmd, capture_output=True, timeout=10, check=False)
    except Exception:
        return False
    return True


# ----------------------------------------------------------------- subcommands

def run_checks(number: int, reverify: bool, timeout: int | None) -> int:
    phase = "verify" if reverify else "selfcheck"
    report_phase(number, phase)
    body = fetch_body(number)
    root = repo_root()
    carried = previous_ledger(number) if reverify else []
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp), carried or None)
        cmd = ["node", str(GATE_CHECK), "--cwd", str(root)]
        if reverify:
            cmd.append("--reverify")
        if timeout:
            cmd += ["--timeout", str(timeout)]
        cmd.append(str(ledger))
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
        printed = (result.stdout or "") + (result.stderr or "")
        sys.stdout.write(printed)
        if result.returncode == 2:
            report_phase(number, phase)
            return 2
        summary = [l for l in printed.splitlines() if SUMMARY_RE.match(l)]
        updated = ledger.read_text(encoding="utf-8").rstrip("\n")
        met, total = count_gates(ledger)

    outside = outside_owns(owns_globs(body), root)
    comment = "\n".join([
        "reverify" if reverify else "self-run",
        *summary,
        "",
        updated,
        "",
        "Outside Owns: " + (", ".join(outside) if outside else "None"),
    ])
    post_comment(number, comment)
    report_phase(number, phase, {"ac": f"{met}/{total}"})
    return result.returncode


def refusals(number: int, ticket: dict, me: str, branch: str, dirty: list[str]) -> list[str]:
    """Why this ticket is not ready to be worked on, in the order a worker would hit it.

    Every one of these ends in `stop`. The four conditions are set up before a worker
    exists — the host opens the worktree on `issue-<n>`, the dispatcher checks the state,
    the labels and the blockers before it starts anyone — so a worker that sees one of
    these has found a fault upstream of itself, not a task. Working around it (switching
    branches, committing whatever is in the tree, taking someone else's ticket) does more
    damage than stopping. The comment this posts on the ticket is what someone reads in
    the morning.
    """
    out = []
    if branch != f"issue-{number}":
        out.append(f"NOT_READY: branch is {branch or '(detached)'}, not issue-{number}; "
                   f"the host opens this worktree on issue-{number}, so it started you "
                   f"somewhere else — stop, do not switch branches yourself")
    if dirty:
        out.append(f"NOT_READY: {len(dirty)} tracked files already have uncommitted changes "
                   f"before any work started; they are not yours to commit or discard — "
                   f"stop and leave the tree as you found it")
    state = ticket.get("state", "")
    if state != "OPEN":
        out.append(f"NOT_READY: #{number} is {state or 'unreadable'}, not OPEN; "
                   f"nothing for you to do here — stop, this comment is the record")
    labels = [l.get("name", "") for l in ticket.get("labels", [])]
    if "ready-for-agent" not in labels:
        out.append(f"NOT_READY: #{number} has no ready-for-agent label, so it has not been "
                   f"cleared for an agent yet; stop and leave it to whoever triages it")
    blockers = [b for b in ticket.get("blockedBy", {}).get("nodes", [])
                if b.get("state") != "CLOSED"]
    if blockers:
        names = ", ".join(f"#{b['number']}" for b in blockers)
        out.append(f"NOT_READY: #{number} is blocked by {names}; stop — the dispatcher "
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
    report_phase(number, "implement")
    print(f"READY: #{number} claimed on issue-{number}")
    return 0


def run_closeout(number: int, draft_path: Path, check_only: bool) -> int:
    """Check the closing comment against the ticket and the repository, then post it."""
    draft = draft_path.read_text(encoding="utf-8")
    problems = draft_problems(draft, fetch_comments(number))
    problems += git_problems(repo_root())
    ticket = fetch_ticket(number)
    if ticket.get("state") != "OPEN":
        problems.append(f"#{number} is already {ticket.get('state', 'unreadable')}")
    me = gh_login()
    if not any(a.get("login") == me for a in ticket.get("assignees", [])):
        problems.append(f"#{number} is not assigned to you ({me}); run --preflight first")

    if problems:
        # The pretool hook that stands between a worker and `gh issue close` relays only
        # the first line of this, so the first line carries the count and the way to read
        # the rest. Fixing them one per run is a loop nobody has a cap on.
        rest = (f" Run `verify-ticket.py {number} --closeout {draft_path} --check-only` "
                f"to see the other {len(problems) - 1}." if len(problems) > 1 else "")
        sys.stderr.write(f"closeout rejected, {len(problems)} problem"
                         f"{'s' if len(problems) > 1 else ''}: {problems[0]}{rest}\n")
        for problem in problems[1:]:
            sys.stderr.write("also: " + problem + "\n")
        report_phase(number, "closeout-rejected")
        return 1
    if check_only:
        print(f"CLOSEOUT OK: #{number} draft passes every check")
        return 0

    post_comment(number, draft)
    if draft.strip().splitlines()[0].strip() == "ALL MET":
        close_ticket(number)
        report_phase(number, "closed", clear=["ac"])
        print(f"CLOSED: #{number}")
    else:
        hand_to_human(number)
        report_phase(number, "handoff", clear=["ac"])
        print(f"HANDED OFF: #{number} is now ready-for-human and stays open")
    return 0


def lint_ticket_graph(number: int, body: str) -> int:
    """Read the batch this ticket belongs to and check it is a startable graph."""
    spec = parent_spec(body)
    if spec is None:
        print("ticket graph: no `## Parent` section, so there is no batch to check")
        return 0
    numbers = fetch_sub_issues(spec)
    if not numbers:
        print(f"ticket graph: #{spec} has no sub-issues, so there is no batch to check")
        return 0
    entries = ticket_entries(numbers)
    errors = validate_dag(entries)
    if errors:
        for error in errors:
            print(error)
        return 1
    levels = compute_levels(entries)
    by_level = defaultdict(list)
    for ticket, level in levels.items():
        by_level[level].append(ticket)
    for level in sorted(by_level):
        print(f"level {level}: " + ", ".join(f"#{t}" for t in sorted(by_level[level])))
    return 0


def criteria_lines(body: str) -> list[tuple[str, str, str]]:
    """`(id, CHECK, EXPECT)` per criterion; a missing line reads as an empty string."""
    out = []
    in_check = False
    for line in section(body, "Acceptance criteria"):
        gate = GATE_LINE_RE.match(line)
        if gate:
            out.append([gate.group(2), "", ""])
            in_check = False
            continue
        if not out:
            continue
        check = CHECK_LINE_RE.match(line)
        if check:
            out[-1][1] = check.group(1)
            in_check = True
            continue
        expect = EXPECT_LINE_RE.match(line)
        if expect:
            out[-1][2] = expect.group(1)
            in_check = False
            continue
        if ATTR_LINE_RE.match(line):
            in_check = False
            continue
        if in_check and line.strip():
            out[-1][1] += "\n" + line
    return [tuple(item) for item in out]


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


def run_lint(number: int) -> int:
    body = fetch_body(number)
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp))
        result = subprocess.run(
            ["node", str(GATE_LINT), "--strict", str(ledger)],
            capture_output=True, text=True,
        )
    sys.stdout.write((result.stdout or "") + (result.stderr or ""))

    broken = lint_expectations(body)
    for finding in broken:
        print("  ERROR " + finding + "  [dollar-without-m]")
    for finding in lint_check_effects(body):
        print("  WARN  " + finding + "  [shared-state]")
    for finding in lint_edges(body):
        print("  WARN  " + finding + "  [unexplained-edge]")

    graph = lint_ticket_graph(number, body)
    return result.returncode or graph or (1 if broken else 0)


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
    args = parser.parse_args(argv)
    chosen = [name for name, on in
              (("--lint", args.lint), ("--reverify", args.reverify),
               ("--preflight", args.preflight), ("--closeout", args.closeout is not None)) if on]
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
    if args.lint:
        return run_lint(args.ticket)
    return run_checks(args.ticket, args.reverify, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
