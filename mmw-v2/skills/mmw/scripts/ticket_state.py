#!/usr/bin/env python3
"""Claim tickets, record criteria runs, and apply ticket state changes."""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import NamedTuple

import locations

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ticket_criteria", HERE.parents[1] / locations.VERIFY_TICKET_PY)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)


CAT_IN_TICKET_ITEM_RE = re.compile(
    r"^- (Standards|Spec|Tests|UI) \[([^\]]+)\] (\S+):(\d+) — (.+?) — source: (.+)$")


FILL = "<fill>"


HANDOFF_KINDS = ("failed", "stuck")
# How long a reverify waits for a product slot before it hands back exit 3, and how often
# it asks again in between. The bound stays under the time a host lets a command run
# before it moves it to the background; a reverify given back 3 is run again, and the wait
# goes on. The worker's own run does not wait here: it is woken when a slot is given back.
SLOT_WAIT_S = int(os.environ.get("MMW_SLOT_WAIT_S", "90"))
SLOT_BEAT_S = int(os.environ.get("MMW_SLOT_BEAT_S", "10"))


class SelfRead(NamedTuple):
    """One answer from the same-directory mode command `dispatch.sh self`.

    `returncode` is None when `path` is not a file. `error` is set when the script could
    not be run. `stdout` and `stderr` are whatever it printed.
    """

    path: str
    returncode: int | None
    stdout: str
    stderr: str
    error: str | None


def read_self() -> SelfRead:
    """Ask `dispatch.sh self` who this process is. Patched out in tests."""
    script = HERE / "dispatch.sh"
    path = str(script)
    if not script.is_file():
        return SelfRead(path, None, "", "", None)
    try:
        out = subprocess.run(["bash", path, "self"], capture_output=True, text=True,
                             timeout=60, env=engine.GH_ENV)
    except (OSError, subprocess.SubprocessError) as exc:
        return SelfRead(path, None, "", "", str(exc))
    return SelfRead(path, out.returncode, out.stdout, out.stderr, None)


def own_session(read: SelfRead) -> tuple[str, str] | None:
    """(runner, session) as `read` reports it, or None when it names neither.

    Patched out in tests. `run_claim` passes the `read_self` answer it just took.
    """
    if read.error is not None or read.returncode != 0:
        return None
    runner, _, session = read.stdout.strip().partition("\t")
    if runner and session:
        return (runner, session)
    return None


# `refusal.py` of the ui-acceptance skill. One line is capped here, above a hook's
# 256-character deny reason: `refusal` trims the cause and keeps the next step whole.
_REFUSAL_PY = HERE.parents[1] / locations.UI_ACCEPTANCE_REFUSAL_PY


_LINE_LIMIT = 2000


def _format_refusal(what: str, why: str, next_step: str) -> str:
    """The three parts on one line. With no `refusal.py`, the parts joined as they stand."""
    if not _REFUSAL_PY.is_file():
        return f"{what} {why} {next_step}"
    return engine._load("mmw_refusal", _REFUSAL_PY).refusal(what, why, next_step, limit=_LINE_LIMIT)


def unnamed_session_line(number: int, read: SelfRead) -> str:
    """Why this refusal could not name its session, and what to do next.

    The event is already posted without `runner` and `session`, so the hold does not end.
    """
    quoted = " ".join(f"{read.stdout} {read.stderr}".split()) or "no output"
    if read.error:
        what = f"dispatch.sh self at {read.path} could not be run ({read.error})."
    elif read.returncode is None:
        what = f"no dispatch.sh at {read.path}."
    else:
        what = f"dispatch.sh self exit {read.returncode}: {quoted}."
    why = f"This refusal does not end this session's hold on #{number}."
    next_step = f"dispatch.sh retract {number}, or during a night tell the orchestrator."
    return _format_refusal(what, why, next_step)


def assign_self(number: int) -> None:
    """Claim the ticket. Patched out in tests."""
    subprocess.run(["gh", "issue", "edit", str(number), "--add-assignee", "@me"], check=True, env=engine.GH_ENV)


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
    subprocess.run(["gh", "issue", "close", str(number), "--reason", "completed"], check=True, env=engine.GH_ENV)
    edit = subprocess.run(
        ["gh", "issue", "edit", str(number),
         "--remove-label", "ready-for-agent", "--remove-assignee", "@me"],
        capture_output=True, text=True, env=engine.GH_ENV,
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
    state = engine.events.fold(comments)
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
        check=True, env=engine.GH_ENV,
    )


def newest_worker_started(number: int, comments: list) -> tuple[dict | None, str | None]:
    """The newest readable `worker.started` payload, or the fact that none exists."""
    record = engine.events.newest(comments, "worker.started")
    if record:
        return record["payload"], None
    return None, (f"#{number} carries no readable worker.started event; run "
                  f"`dispatch.sh start {number} worker` so the ticket records one")


def worker_started_field(number: int, comments: list,
                         field: str) -> tuple[str | None, str | None]:
    """One required field of the newest readable `worker.started`."""
    started, problem = newest_worker_started(number, comments)
    if problem:
        return None, problem
    value = started.get(field)
    if isinstance(value, str) and value:
        return value, None
    return None, (f"#{number}'s newest worker.started carries no `{field}`; run "
                  f"`dispatch.sh start {number} worker` again so it records one")


def draft_summary(draft: str) -> tuple[str, dict]:
    """The first line and the `Counts:` line's numbers `--closeout` writes for this
    draft: whichever of `ALL MET` or `HANDOFF REQUIRED: …` its `ABANDON:` lines and
    unmet criteria make true, and the ledger's own count. A worker need not get this
    arithmetic right by hand; the closeout computes it from the draft every time.
    """
    criteria = engine.parse_criteria(draft)
    abandons = engine.parse_abandons(draft)
    counts = engine.tally(criteria, abandons)
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

    criteria = engine.parse_criteria(draft)
    ids = [c["id"] for c in criteria]
    abandons = engine.parse_abandons(draft)
    for a in abandons:
        if a["kind"] not in engine.ABANDON_KINDS:
            problems.append(f"ABANDON: {a['ac']} has kind `{a['kind']}`; "
                            f"it must be one of {', '.join(engine.ABANDON_KINDS)}")
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

    record = engine.newest_run(comments, "reverify", actor="worker")
    reverify = record["payload"] if record else None
    if reverify is None:
        problems.append("the ticket carries no worker reverify `ticket.checked` event. Run "
                        "`ticket_state.py <n> --run-and-record-criteria --reverify --actor worker` after the final "
                        "commit, or close out as `HANDOFF REQUIRED`")
    else:
        # A run is generated from the ticket body, which carries no `ABANDON:` line, so a
        # criterion the draft abandons as `decision` still runs and still reports unmet.
        # That unmet is the one this draft is allowed to carry: the decision child is open and
        # the ticket closes on it. Any other unmet is a claim the draft cannot make.
        decided = {a["ac"] for a in engine.parse_abandons(draft) if a["kind"] == "decision"}
        result = reverify.get("result")
        unmet = list(reverify.get("failed") or [])
        covered = result == "unmet" and unmet and set(unmet) <= decided
        if result != "met" and not covered:
            problems.append("the worker's final reverify still reports unmet or abandoned "
                            "criteria. Add the required `ABANDON:` lines and close out as "
                            "`HANDOFF REQUIRED`")
        if reverify.get("commit") != engine.git("rev-parse", "HEAD"):
            problems.append(f"the worker's final reverify is on {reverify.get('commit')} and "
                            "HEAD has moved on. Run `ticket_state.py <n> --run-and-record-criteria --reverify --actor worker` on HEAD")
        # The criteria the worker ran must be the criteria the ticket now states. A
        # ticket may legitimately rewrite one — a decision changed what it must do — but
        # then what stands is a verification of something else, and the final run runs again.
        if reverify.get("shape") != engine.shape_digest(engine.section(body, locations.ACCEPTANCE_CRITERIA_HEADING)):
            problems.append("the acceptance criteria have changed since the worker's final "
                            "run: run `ticket_state.py <n> --run-and-record-criteria --reverify --actor worker` again so the run and the "
                            "ticket agree")
    return problems


def event_problems(comments: list) -> list[str]:
    """Comments on the ticket whose event cannot be read.

    The closeout decides from the ticket's events, so a comment that carries one
    this pipeline cannot read is a question left unanswered, not a comment to skip.
    """
    return [f"comment {item['comment']} (`{item['line'][:50]}`) carries an event this "
            f"pipeline cannot read: {item['reason']}"
            for item in engine.events.fold(comments)["unreadable"]]


def git_problems(base: str, root: Path | None = None) -> list[str]:
    """The repository conditions a ticket must be in to close, plus one warning."""
    problems = []
    dirty = engine.dirty_tracked(root)
    if dirty:
        problems.append(f"{len(dirty)} tracked files have uncommitted changes; "
                        f"commit them so the closing comment names a real commit")
    if not engine.is_ancestor(base, "HEAD", root):
        problems.append(f"this branch does not contain its base {base}; run `git merge {base}`. "
                        f"Do not rebase because the ticket's recorded runs name commits")
        return problems
    fork = engine.git("merge-base", base, "HEAD", cwd=root)
    if fork and not engine.git("diff", "--name-only", f"{fork}..HEAD", cwd=root):
        sys.stderr.write("warning: this branch changes no files since it left its base branch\n")
    return problems


def outside_owns_from(text: str) -> str | None:
    """The `Outside Owns:` line in `text`, stripped, or `None` when absent."""
    for line in text.splitlines():
        if line.startswith("Outside Owns:"):
            return line.strip()
    return None


def markdown_h2(text: str) -> list[str]:
    """The `## ` heading titles in document order."""
    return [line[3:].strip() for line in text.splitlines() if line.startswith("## ")]


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


def overlay_run_evidence(body: str, run: dict | None) -> list[dict]:
    """Criteria from the ticket body, ticks and evidence from one run's `criteria`."""
    base = engine.parse_criteria("\n".join(engine.section(body, locations.ACCEPTANCE_CRITERIA_HEADING)))
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
    rows = [row.strip() for row in engine.section(review, "## In-ticket")
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


def review_findings_block(review: str, comment: int | str | None = None) -> str:
    items = in_ticket_findings(review, comment)
    if not items:
        return "Review findings:\nNone"
    lines = ["Review findings:"]
    for row in items:
        lines.append(f"{row} — {FILL}")
    return "\n".join(lines)


def green_before_work_block(comments: list) -> str:
    record = engine.newest_run(comments, "baseline")
    if record is None:
        return "Green before work:\nnot run: no baseline `ticket.checked`"
    ids = []
    for item in record["payload"].get("criteria") or []:
        if isinstance(item, dict) and item.get("met") and item.get("id"):
            ids.append(str(item["id"]))
    if not ids:
        return "Green before work:\nNone"
    return "Green before work:\n" + "\n".join(f"- {i}: {FILL}" for i in ids)


def run_decisions(number: int, path: Path) -> int:
    """Post the two-section file as a `DECISIONS` comment, or refuse."""
    comments = engine.fetch_comments(number)
    if engine.events.newest(comments, "worker.decided") is not None:
        return engine.refuse(f"#{number} already carries a DECISIONS comment")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    headings = markdown_h2(text)
    expected_headings = ["Decisions I made on my own", "Outside Owns"]
    if headings != expected_headings:
        missing = [h for h in expected_headings if h not in headings]
        if missing:
            return engine.refuse("the file is missing section"
                          + ("s " if len(missing) > 1 else " ")
                          + " and ".join(f"`{h}`" for h in missing))
        extra = [h for h in headings if h not in expected_headings]
        if extra:
            return engine.refuse("the file has extra section"
                          + ("s " if len(extra) > 1 else " ")
                          + " and ".join(f"`{h}`" for h in extra)
                          + "; it must have exactly two sections, "
                          "`Decisions I made on my own` then `Outside Owns`")
        return engine.refuse("the file must have exactly two sections, "
                      "`Decisions I made on my own` then `Outside Owns`")
    run = engine.newest_run(comments, "self")
    if run is None:
        return engine.refuse(f"#{number} carries no ticket.checked of your own run to check "
                      f"Outside Owns against")
    want = engine.outside_owns_text(run["payload"])
    got = outside_owns_from("\n".join(engine.section(text, "## Outside Owns")))
    if want != got:
        return engine.refuse(f"the file's `Outside Owns` line does not match your newest run, "
                      f"which says `{want}`")
    engine.post_event(number, "worker.decided", "DECISIONS", text.lstrip("\n"))
    print(f"DECISIONS: posted on #{number}")
    return 0


def open_children_owns(number: int) -> list[tuple[int, list[str]]]:
    """OPEN children of spec `number` and each child's Owns globs, loaded once."""
    found = []
    for child in engine.tree.children(engine.fetch_tree(number, "spec")):
        if child.get("state") != "OPEN":
            continue
        found.append((child["number"], engine.owns_globs(engine.fetch_body(child["number"]))))
    return found


REVIEW_HEAD_RE = re.compile(r"^REVIEW (\S+?)\.\.(\S+)")


def run_review(number: int, path: Path) -> int:
    """Post the review report on the ticket, as the `reviewer.reported` event.

    Nothing here tells the worker: the event on the ticket is what the relay of the
    mmw skill turns into the worker's wake-up, so a report that lands is a report
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
        return engine.refuse(
            "a review report opens `REVIEW <base-commit>..<HEAD commit>`, and this file "
            + (f"opens `{head[:60]}`" if head else "is empty"))
    try:
        in_ticket_findings(stripped, next_step=(
            "rewrite that row as `- <Axis> [<category>] <path>:<line> — <claim> — "
            "source: <…>`, or write `None`, then run --review again"))
    except ValueError as exc:
        return engine.refuse(str(exc))
    rest = "\n".join(stripped.splitlines()[1:]).strip("\n")
    engine.post_event(number, "reviewer.reported", head, rest,
               base=found.group(1), head=found.group(2))
    print(f"REVIEW: posted on #{number}")
    return 0


def run_touched(number: int) -> int:
    """Post `worker.touched` on each open sibling whose Owns covers a file this
    ticket changed outside its own, naming the files and why they were changed."""
    comments = engine.fetch_comments(number)
    review = (engine.events.newest(comments, "reviewer.reported") or {}).get("body")
    if review is None:
        return engine.refuse(f"#{number} carries no reviewer.reported event")
    run = engine.newest_run(comments, "self")
    if run is None:
        return engine.refuse(f"#{number} carries no ticket.checked of your own run")
    files = list(run["payload"].get("outside_owns") or [])
    if not files:
        return 0
    decisions = (engine.events.newest(comments, "worker.decided") or {}).get("body")
    try:
        spec = engine.spec_of(number)
    except engine.ParentUnreadable as exc:
        return engine.refuse(f"#{number}: the tracker could not say which spec it sits under ({exc})")
    if spec is None:
        return engine.refuse(f"#{number} has no parent link and no spec in `{locations.PARENT_HEADING}`")
    try:
        siblings = open_children_owns(spec)
    except engine.SubIssuesUnreadable as exc:
        return engine.refuse(f"#{number}: the tracker could not list the children of #{spec} ({exc})")
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
        mine = [d for d in details if any(engine.glob_covers(g, d["path"]) for g in globs)]
        if not mine:
            continue
        prose = []
        for d in mine:
            prose += ["", d["path"], d["sentence"]]
            prose += [x for x in (d["ac"], d["judgement"]) if x]
        engine.post_event(child, "worker.touched",
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
    names — that is what a closing comment says. `--closeout` then runs the repository's
    own `checks` over the working tree, and a draft written into that tree is one more
    file those checks read. A prior ticket with every criterion met stayed open because a
    repository guard found two reference file names in the closeout draft written inside
    its working tree. Every consuming repository with a guard over its own Markdown could
    meet the same wall, so the default landing place is outside all of them.
    """
    return Path(tempfile.mkdtemp(prefix=f"mmw-closeout-{number}-")) / f"closeout-{number}.md"


def run_closing_draft(number: int, out_file: Path | None) -> int:
    """Write the closing-comment draft to `out_file`, or to a path of this run's own
    when it is None, printing the path either way."""
    body = engine.fetch_body(number)
    comments = engine.fetch_comments(number)
    into, problem = worker_started_field(number, comments, "into")
    if problem:
        return engine.refuse(problem)
    record = engine.newest_run(comments, "self")
    run = record["payload"] if record else None
    criteria = overlay_run_evidence(body, run)
    abandons = list((run or {}).get("abandons") or [])
    counts = engine.tally(criteria, abandons)
    blocking = [a for a in abandons if a["kind"] in HANDOFF_KINDS]
    if blocking:
        kinds = ", ".join(k for k in HANDOFF_KINDS if any(a["kind"] == k for a in blocking))
        first = (f"HANDOFF REQUIRED: {counts['abandoned']} abandoned ({kinds}), "
                 f"{counts['unmet']} unmet, {counts['met']} met of {counts['total']}")
    else:
        first = "ALL MET"
    head = engine.git("rev-parse", "HEAD")
    branch_line = (f"Branch: issue-{number} Commit: {head} PR: none — will be merged into "
                   f"{into} by dispatch.sh advance")
    review_event = engine.events.newest(comments, "reviewer.reported") or {}
    review = review_event.get("body") or ""
    try:
        review_block = review_findings_block(review, review_event.get("comment"))
    except ValueError as exc:
        return engine.refuse(str(exc))
    files = list((run or {}).get("outside_owns") or [])
    if files:
        judged = []
        for path in files:
            judgement = spec_judgement(review, path)
            judged.append(f"{path} ({judgement})" if judgement else path)
        outside = "Outside Owns: " + ", ".join(judged)
    else:
        outside = "Outside Owns: None"
    try:
        opened = [f"#{child}" for child in engine.fetch_sub_issues(number, "ticket")]
        sub = "Sub-issues opened: " + (", ".join(opened) if opened else "none")
    except engine.SubIssuesUnreadable:
        sub = "Sub-issues opened: unknown (the tracker could not be asked)"
    counts_line = (f"Counts: {counts['met']} met, {counts['unmet']} unmet, "
                   f"{counts['abandoned']} abandoned of {counts['total']}")
    parts = [first, "", branch_line, ""]
    for item in criteria:
        parts.append(engine.criterion_block(item))
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


def run_open_child(number: int, kind: str, path: Path) -> int:
    """Open a `needs-triage` child under this ticket, and record it on this ticket.

    The child carries the layer label `mmw:child` beside its queue label. Its body opens
    with a line a person reads; which kind it is and where it came from is the
    `child.opened` event posted on this ticket, which is where the ticket's own fold finds
    its children. A child opened whose event could not be written exits 1 and says so:
    the child exists, and opening it again would make two.
    """
    if kind not in engine.SUB_ISSUE_KINDS:
        return engine.refuse(f"kind `{kind}` is not one of {', '.join(engine.SUB_ISSUE_KINDS)}")
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not text.strip():
        return engine.refuse(f"{path} is empty")
    title = text.strip().splitlines()[0].strip()
    missing = engine.ensure_label("mmw:child")
    if missing:
        return engine.refuse(f"the repository has no `mmw:child` label and it could not be "
                      f"created ({missing}); nothing was opened")
    posted = f"A `{kind}` child of #{number}.\n\n" + text
    if not posted.endswith("\n"):
        posted += "\n"
    result, child = engine.gh_issue_create(
        ["--parent", str(number), "--label", "needs-triage", "--label", "mmw:child",
         "--title", title], posted)
    if result.returncode != 0:
        sys.stderr.write((result.stderr or result.stdout or "gh issue create failed").rstrip() + "\n")
        return 2
    printed = (result.stdout or "").strip()
    recorded = 0
    if child is None:
        sys.stderr.write(f"opened a child of #{number} but `gh issue create` printed no "
                         f"issue number ({printed[:80] or 'nothing'}), so no child.opened "
                         f"event was written on #{number}; do not open it again\n")
        recorded = 1
    else:
        try:
            engine.post_event(number, "child.opened", f"Opened #{child} ({kind}): {title}",
                       child=child, kind=kind, title=title)
        except (OSError, subprocess.CalledProcessError) as exc:
            sys.stderr.write(f"opened #{child} under #{number}, but the child.opened event "
                             f"on #{number} was not written ({exc}); do not open it again\n")
            recorded = 1
    print(str(child) if child is not None else printed)
    return recorded


NOT_RECORDED = 4


def give_slot_back(root: Path) -> str | None:
    """Take this worktree's product down and give its slot back; the reason when that
    could not be done, None when it was or there was no slot to give.

    `lease.py` does both, as `release` with `stop`: the product's `stop` in
    `.mmw/target.json` runs first, from the worktree, because a slot is free only once
    nothing listens on its ports and `lease.py` rightly refuses one held by a live process.
    """
    lease = engine.load_lease()
    if lease is None:
        return "no directory in force holds lease.py"
    try:
        lease.release(lease.worktree_of(root), stop=True)
    except lease.StopUnreadable as exc:
        return f"{exc}, so the product's stop is unknown and the slot was kept"
    except SystemExit as exc:
        return str(exc)
    return None


def blocker_fold(number: int) -> dict | None:
    """The events of blocker `number` folded, or None when the tracker did not answer."""
    try:
        return engine.events.fold(engine.fetch_comments(number), issue=number)
    except (OSError, ValueError, subprocess.CalledProcessError, engine.TrackerReadError):
        return None


def refusals(number: int, ticket: dict, me: str, branch: str,
             dirty: list[str]) -> list[tuple[str, str]]:
    """Why this ticket is not ready to be worked on, in the order a worker would hit it.

    Each refusal is `(reason, sentence)`: the reason is the `ticket.refused` event's
    `reason` field, one of `events.REFUSALS`, and the sentence is its first line.

    A blocker holds until its work has landed, as `events.blocker_hold` reads it off the
    blocker's own events — the same answer `dispatch.sh`'s frontier gives, so a
    ticket it starts is never refused here for a blocker it had let go.

    Every one of these ends in `stop`. Five of the six conditions are set up before a
    worker exists — `dispatch.sh` opens the worktree on `issue-<n>` and checks the state,
    the labels and the blockers before it starts anyone — so a worker that sees one of
    them has found a fault upstream of itself, not a task. Working around it (switching
    branches, taking someone else's ticket) does more damage than stopping.

    The sixth, the tree, is the one whose answer depends on who holds the ticket, because
    a worker comes through this run every time it enters the ticket — the turn it is
    prompted back into after a review included (the worker's claim, run on every entry). On that turn
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
        why = engine.events.blocker_hold(state, blocker_fold(node["number"]) if state == "CLOSED"
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


def run_baseline_if_needed(number: int, root: Path) -> None:
    """Run the baseline once for the newest `worker.started.base`, if that run is missing.

    A red result does not refuse the claim. Failures of the throwaway worktree are written
    as an unmet `ticket.checked` of run `baseline` when the base commit is known, and
    otherwise named on stderr; they never raise into `--claim`.
    """
    try:
        comments = engine.fetch_comments(number)
    except engine.TrackerReadError as exc:
        sys.stderr.write(f"#{number}: baseline run did not start ({exc})\n")
        return
    started = engine.events.newest(comments, "worker.started")
    base = (started or {}).get("payload", {}).get("base")
    if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40}", base):
        sys.stderr.write(f"#{number}: baseline run did not start "
                         f"(no worker.started.base commit)\n")
        return
    existing = engine.newest_run(comments, "baseline")
    if existing and existing["payload"].get("commit") == base:
        return
    try:
        body = engine.fetch_body(number)
    except engine.TrackerReadError as exc:
        sys.stderr.write(f"#{number}: baseline run did not start ({exc})\n")
        return
    try:
        result = engine.run_baseline(number, body, base, root)
        if result is not None:
            _post_baseline(number, body, base, result)
    except (OSError, subprocess.CalledProcessError, engine.events.EventError) as exc:
        sys.stderr.write(f"#{number}: baseline run did not complete ({exc})\n")


def _post_baseline(number: int, body: str, base: str, result: engine.BaselineRun) -> None:
    results = engine.criteria_results(result.criteria)
    abandons = engine.parse_abandons(result.ledger) if result.ledger else []
    engine.post_event(number, "ticket.checked", result.summary, result.ledger,
               run="baseline", commit=base, result=result.outcome,
               counts=engine.tally(result.criteria, abandons),
               criteria=results, failed=[r["id"] for r in results if not r["met"]],
               abandons=abandons or None, skipped=result.skipped or None,
               shape=engine.shape_digest(engine.section(body, locations.ACCEPTANCE_CRITERIA_HEADING)),
               actor="worker", stage=engine.events.checked_stage("baseline", "worker"))


def run_claim(number: int) -> int:
    """Claim the ticket, or say on the ticket itself why it cannot be claimed.

    Either way one event lands on the ticket: `ticket.refused` with the first refusal's
    reason, or `ticket.claimed` once the claim is made. A claim whose event could not be
    written still holds — the tracker's assignee is the claim — and says so on stderr.
    After a successful claim, criteria that need no product slot are run once at the
    newest `worker.started.base` (a `ticket.checked` of run `baseline`) unless that run
    is already on the ticket; a red result does not refuse.
    """
    root = engine.repo_root()
    ticket = engine.fetch_ticket(number)
    me = engine.gh_login()
    branch = engine.current_branch(root)
    dirty = engine.dirty_tracked(root)
    problems = refusals(number, ticket, me, branch, dirty)
    if problems:
        reason, sentence = problems[0]
        # The refusing session is named so its own hold ends with this event and the
        # ticket is free for the next start. A session that cannot name itself ends
        # none, and stderr says why and what to do next.
        read = read_self()
        named = own_session(read)
        runner, session = named or (None, None)
        engine.post_event(number, "ticket.refused", sentence, spec=engine.spec_field(ticket),
                   reason=reason, branch=branch or None, runner=runner, session=session)
        sys.stderr.write(sentence + "\n")
        if named is None:
            sys.stderr.write(unnamed_session_line(number, read) + "\n")
        return 2
    assign_self(number)
    try:
        engine.post_event(number, "ticket.claimed", f"Claimed #{number} on {branch} as {me}",
                   spec=engine.spec_field(ticket), login=me, branch=branch,
                   commit=engine.git("rev-parse", "HEAD", cwd=root) or None)
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"#{number} is claimed, but its ticket.claimed event was not "
                         f"written ({exc})\n")
    run_baseline_if_needed(number, root)
    print(f"READY: #{number} claimed on issue-{number}")
    # Getting here with a dirty tree means the claim was already this account's, so the
    # changes came in under it: this is a worker back on its own work, and the only thing
    # left to say is where they have to be by the closing steps.
    if dirty:
        print(f"CARRIED: {len(dirty)} tracked files have uncommitted changes, made under "
              f"the claim you already held on #{number}; commit them on issue-{number} "
              f"before the closing steps — --closeout refuses a draft while a tracked "
              f"file is uncommitted.")
    return 0


def review_finding_problems(draft: str, comments: list[str]) -> list[str]:
    """The newest review's In-ticket rows must each have a handled draft row.

    Compare the whole source-bearing row, not just its path or claim. Counting rows
    prevents one response from silently standing in for duplicate findings.
    """
    review_event = engine.events.newest(comments, "reviewer.reported") or {}
    try:
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
            commands.append((entry, engine.DEFAULT_TIMEOUT))
            continue
        if isinstance(entry, dict) and isinstance(entry.get("run"), str):
            timeout = entry.get("timeout", engine.DEFAULT_TIMEOUT)
            if not isinstance(timeout, int) or timeout <= 0:
                raise TargetJsonChecksError(
                    f"{path} `checks` entry {entry['run']!r}: `timeout` must be a positive integer")
            commands.append((entry["run"], timeout))
            continue
        raise TargetJsonChecksError(
            f"{path} `checks` entry {entry!r} is neither a string nor {{\"run\": …, \"timeout\": …}}")
    return commands


def run_target_json_checks(root: Path | None, into: str) -> dict | None:
    """Run each `checks` command at the repository root, in order.

    None when the key is absent: nothing ran. Otherwise `{"total", "failed",
    "problem"}`: `failed` is `{"command", "tail"}` for each command that did not exit 0,
    with its last `CHECKS_TAIL` lines of output, and `problem` says why the file itself
    could not be read — a malformed file is a failure, not absence. A string entry is
    held to `DEFAULT_TIMEOUT`, the same bound as a `CHECK:`; an entry written as
    `{"run": …, "timeout": …}` is held to its own.
    """
    try:
        commands = target_json_checks(root)
    except TargetJsonChecksError as exc:
        return {"total": 0, "failed": [], "problem": str(exc)}
    if commands is None:
        return None
    failed: list[tuple[str, str]] = []
    env = os.environ.copy()
    env["MMW_BASE_REF"] = f"origin/{into}"
    for command, bound in commands:
        try:
            proc = subprocess.run(command, shell=True, cwd=root, capture_output=True,
                                  text=True, timeout=bound, env=env)
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
    return {"total": len(commands),
            "failed": [{"command": c, "tail": t} for c, t in failed], "problem": None}


def post_repo_checks(number: int, checks: dict, spec: int | None) -> bool:
    """Post the repository checks' run as a `ticket.checked` event; True when all passed."""
    ok = not checks["failed"] and not checks["problem"]
    total = checks["total"]
    lines = []
    if checks["problem"]:
        lines.append(checks["problem"])
    for failure in checks["failed"]:
        lines += ["", failure["command"]]
        if failure["tail"]:
            lines.append(failure["tail"])
    head = engine.git("rev-parse", "HEAD")
    engine.post_event(number, "ticket.checked",
               (f"Repository checks on {head[:12]}: {total - len(checks['failed'])}/{total} "
                f"passed" if not checks["problem"] else
                f"Repository checks on {head[:12]}: .mmw/target.json `checks` unreadable"),
               "\n".join(lines).strip("\n"), spec=spec, run="repo-checks", commit=head,
               result="met" if ok else "unmet", stage="close",
               counts={"passed": total - len(checks["failed"]), "total": total},
               commands=checks["failed"] or None, problem=checks["problem"])
    return ok


def push_ticket_branch(number: int, root: Path, commit: str) -> str | None:
    """Push the final-run commit to `origin/issue-<n>` without rewriting history."""
    engine.ref = f"refs/heads/issue-{number}"
    try:
        pushed = subprocess.run(
            ["git", "push", "origin", f"{commit}:{engine.ref}"], cwd=root,
            capture_output=True, text=True,
        )
        if pushed.returncode != 0:
            detail = " ".join((pushed.stderr or pushed.stdout).strip().splitlines())
            return (f"origin rejected {commit} for issue-{number}: "
                    f"{detail[:500] or f'git push exited {pushed.returncode}'}. The ticket "
                    f"remains open; resolve the rejection and run --closeout again. "
                    f"No force-push was used")
        remote = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", engine.ref], cwd=root,
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
    common = engine.git("rev-parse", "--git-common-dir", cwd=root)
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
    state = engine.events.fold(comments)
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
        with closeout_lock(engine.repo_root(), number):
            return _run_closeout(number, draft_path, check_only)
    except (CloseoutBusy, OSError) as exc:
        return engine.refuse(f"closeout refused: {exc}. Nothing was run or written; retry the "
                      "same command after the active closeout finishes")


def _run_closeout(number: int, draft_path: Path, check_only: bool) -> int:
    """Check the closing comment against the ticket and the repository, then post it."""
    raw = draft_path.read_text(encoding="utf-8")
    comments = engine.fetch_comments(number)
    # The first line and `Counts:` are computed here, from the draft's own `ABANDON:`
    # lines and criteria, and written into what posts — never taken as the worker wrote
    # them.
    first, counts = draft_summary(raw)
    draft = rewrite_summary(raw, first, counts)
    passed = first == "ALL MET"
    ticket = engine.fetch_ticket(number)
    head = engine.git("rev-parse", "HEAD")
    completed = completed_closeout(ticket, comments, first, head)
    if completed:
        action = "CLOSED" if completed == "closed" else "HANDED BACK"
        print(f"{action}: #{number} was already recorded at {head}")
        return 0
    body = engine.fetch_body(number)
    started, started_problem = newest_worker_started(number, comments)
    base = (started or {}).get("base")
    into = (started or {}).get("into") if passed else None
    problems = draft_problems(draft, comments)
    problems += verified_problems(draft, body, comments, first)
    problems += review_finding_problems(draft, comments)
    problems += event_problems(comments)
    if started_problem:
        problems.append(started_problem)
    elif passed and not into:
        problems.append(f"#{number}'s newest worker.started carries no `into`; run "
                        f"`dispatch.sh start {number} worker` again so it records one")
    if base:
        problems += git_problems(base, engine.repo_root())
    me = engine.gh_login()
    # A previous run of this closeout that closed (or handed back) the ticket and could not
    # post the event: this run posts it, and does nothing else.
    pending = unannounced_change(ticket, comments, me, first)
    if ticket.get("state") != "OPEN" and pending != "closed":
        problems.append(f"#{number} is already {ticket.get('state', 'unreadable')}")
    if pending is None and not any(a.get("login") == me for a in ticket.get("assignees", [])):
        problems.append(f"#{number} is not assigned to you ({me}); run --claim first")

    if problems:
        # The first line carries the total and the command that prints the rest, so a
        # worker sees the whole set at once. A refusal that named only the problem it hit
        # first would put it in a loop nobody has a cap on: fix one, run again, meet the
        # next.
        rest = (f" Run `ticket_state.py {number} --closeout {draft_path} --check-only` "
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
        checks = run_target_json_checks(engine.repo_root(), into)
        if checks is not None and not post_repo_checks(number, checks, engine.spec_field(ticket)):
            named = ", ".join(f["command"] for f in checks["failed"]) or checks["problem"]
            sys.stderr.write(f"closeout stopped: the repository's checks did not pass "
                             f"({named}); the ticket.checked event on #{number} carries "
                             f"each failed command and its last lines. Fix the code, run "
                             f"that suite yourself, commit, run ticket_state.py {number} "
                             f"--run-and-record-criteria --reverify --actor worker "
                             f"again, and run --closeout again\n")
            return 1
        problem = push_ticket_branch(number, engine.repo_root(), head)
        if problem:
            sys.stderr.write(f"closeout refused: {problem}\n")
            return 1

    # The draft is the comment: its first line for a person, the rest as written, and the
    # event block after it. `abandoned` carries every `ABANDON:` line — on a pass only
    # `decision` ones can be there, on a hand back they are the reason it came back.
    abandons = engine.parse_abandons(draft)
    event = "ticket.passed" if passed else "ticket.returned"
    fields = dict(spec=engine.spec_field(ticket), commit=head or None,
                  branch=engine.current_branch(engine.repo_root()) or None,
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
    # A handed-back ticket's work is over for the night, and `ticket.returned` says so —
    # its product slot free included: the relay wakes the workers queued for a slot on
    # that event. So the slot goes back before the event, on the run that hands back and
    # on one posting the event a previous run could not; a slot that will not come back
    # is said on stderr, and the ticket is still announced as returned.
    if not passed:
        problem = give_slot_back(engine.repo_root())
        if problem:
            sys.stderr.write(f"#{number} is handed back, but its product slot was not given "
                             f"back: {problem}\n")
    try:
        engine.post_event(number, event, first,
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



def run_and_record_criteria(number: int, reverify: bool, actor: str | None = None) -> int:
    """Run the shared engine and record one result, or one wait for a slot."""
    run = "reverify" if reverify else "self"
    actor = actor or "worker"
    announced = None
    spent = 0
    while True:
        result = engine.run_criteria(number, reverify)
        sys.stdout.write(result.output)
        if result.returncode != 3:
            break
        acquisition = result.acquisition
        if announced is None:
            announced = engine.events.fold(engine.fetch_comments(number))["waiting"] is not None
        if not announced:
            what = ("this product's instance.max" if acquisition.reason == "product-full"
                    else "every slot of this machine")
            try:
                engine.post_event(number, "worker.queued",
                                  f"Waiting for a product slot: {what} ({acquisition.limit}) is held",
                                  "\n".join(f"- {h}" for h in acquisition.holders),
                                  run=run, reason=acquisition.reason, limit=acquisition.limit,
                                  holders=acquisition.holders, worktree=acquisition.worktree, actor=actor)
            except (OSError, subprocess.CalledProcessError) as exc:
                sys.stderr.write(f"#{number}: no product slot is free and worker.queued "
                                 f"could not be written ({exc}); nothing ran. Run again.\n")
                return NOT_RECORDED
            announced = True
        if not reverify:
            sys.stderr.write(f"#{number}: no product slot is free ({acquisition.reason}); nothing ran. "
                             f"End your turn: the relay wakes you with `#{number} worker.queued` "
                             "when a slot is given back. Run the same command then.\n")
            return 3
        if spent >= SLOT_WAIT_S:
            sys.stderr.write(f"#{number}: no product slot came free in {spent}s ({acquisition.reason}); "
                             "nothing ran. Run the same command again to keep waiting.\n")
            return 3
        time.sleep(SLOT_BEAT_S)
        spent += SLOT_BEAT_S
    if result.returncode == 2:
        return 2
    criteria = engine.criteria_results(result.criteria)
    prose = [result.ledger]
    if not reverify:
        prose += ["", engine.outside_owns_text(result.outside_owns)]
    lease_record = result.acquisition.lease_record if result.acquisition else None
    try:
        engine.post_event(number, "ticket.checked",
                          f"{'Reverify' if reverify else 'Own run'} on {result.head[:12]}: "
                          f"{result.summary or result.outcome}", "\n".join(prose),
                          run=run, commit=result.head, result=result.outcome,
                          counts=engine.tally(result.criteria, result.abandons), criteria=criteria,
                          failed=[c["id"] for c in criteria if not c["met"]],
                          abandons=result.abandons or None, shape=result.shape,
                          slot=lease_record.get("slot") if lease_record else None,
                          port_base=lease_record.get("port_base") if lease_record else None,
                          actor=actor, stage=engine.events.checked_stage(run, actor),
                          **result.outside_owns)
    except (OSError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"#{number}: the run finished {result.outcome} on {result.head[:12]}, "
                         f"but its ticket.checked event could not be written ({exc}), so the "
                         "ticket records no run. Run it again once the tracker takes comments.\n")
        return NOT_RECORDED
    return result.returncode


EXIT_CODES = """exit codes:
  --run-and-record-criteria: 0 met; 1 unmet or abandoned; 2 could not start;
    3 no product slot free (worker.queued); 4 the run or wait could not be recorded.
  --claim: 0 claimed; 2 refused (NOT_READY is recorded as ticket.refused).
  --decisions, --review, --touched: 0 recorded or nothing to post; 2 refused.
  --closing-draft: 0 wrote the file and printed its path; 2 refused.
  --open-child: 0 opened and recorded; 1 opened but unrecorded; 2 refused.
  --closeout: 0 closed or returned and recorded, or --check-only passed;
    1 rejected or incomplete; 2 could not start.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, epilog=EXIT_CODES,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticket", type=int)
    jobs = parser.add_mutually_exclusive_group(required=True)
    jobs.add_argument("--claim", action="store_true")
    jobs.add_argument("--run-and-record-criteria", action="store_true")
    jobs.add_argument("--decisions", type=Path, metavar="FILE")
    jobs.add_argument("--review", type=Path, metavar="FILE")
    jobs.add_argument("--touched", action="store_true")
    jobs.add_argument("--closing-draft", nargs="?", const="", metavar="OUT")
    jobs.add_argument("--open-child", nargs=2, metavar=("KIND", "FILE"))
    jobs.add_argument("--closeout", type=Path, metavar="DRAFT")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--reverify", action="store_true")
    parser.add_argument("--actor", choices=engine.events.REVERIFY_ACTORS)
    parser.add_argument("--tools", action="append", type=Path, default=[], metavar="DIR")
    args = parser.parse_args(argv)
    if args.reverify and not args.run_and_record_criteria:
        parser.error("--reverify belongs to --run-and-record-criteria")
    if args.actor is not None and not args.reverify:
        parser.error("--actor belongs to --reverify")
    if args.reverify and args.actor is None:
        parser.error("--reverify requires --actor worker|main")
    if args.check_only and args.closeout is None:
        parser.error("--check-only belongs to --closeout")
    for flag in ("decisions", "review", "closeout"):
        path = getattr(args, flag)
        if path is not None and not path.is_file():
            parser.error(f"no file at {path}")
    engine.TOOLS[:] = ([d.resolve() for d in args.tools]
                      or [HERE.parents[1] / locations.UI_ACCEPTANCE_SCRIPTS])
    try:
        if args.claim:
            return run_claim(args.ticket)
        if args.run_and_record_criteria:
            return run_and_record_criteria(args.ticket, args.reverify, args.actor)
        if args.decisions is not None:
            return run_decisions(args.ticket, args.decisions)
        if args.review is not None:
            return run_review(args.ticket, args.review)
        if args.touched:
            return run_touched(args.ticket)
        if args.closing_draft is not None:
            return run_closing_draft(args.ticket,
                                     Path(args.closing_draft) if args.closing_draft else None)
        if args.open_child is not None:
            kind, file = args.open_child
            return run_open_child(args.ticket, kind, Path(file))
        return run_closeout(args.ticket, args.closeout, args.check_only)
    except engine.TrackerReadError as exc:
        return engine.refuse(f"ticket_state: {exc}. Nothing was run or written; retry the same command")
    except engine.JudgeUnreachable as exc:
        return engine.refuse(f"ticket_state: {exc}")


if __name__ == "__main__":
    sys.exit(main())
