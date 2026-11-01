#!/usr/bin/env python3
"""Read a spec's tickets, events, dependencies and currently eligible work.

No ticket-body acceptance format is parsed and no tracker data is written.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load(name: str, filename: str):
    default = Path(__file__).resolve().parents[2] / "verify-ticket" / "scripts" / "events.py"
    path = default.parent / filename
    if not path.is_file():
        sys.stderr.write(f"status: no {filename} at {path}; restore the adjacent v5 tool\n")
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load("mmw_events", "events.py")
tree = _load("mmw_tree", "issue_tree.py")

import tracker

# --------------------------------------------------------------------- reading

def gh(args: list[str]) -> str:
    """`gh` with colour forcing stripped from its environment.

    Under an exported CLICOLOR_FORCE=1, `gh` writes ANSI escapes into --json output that
    no JSON reader can parse.
    """
    env = tracker.environment()
    run = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    return run.stdout if run.returncode == 0 else ""


def gh_json(args: list[str], fallback):
    try:
        return json.loads(gh(args))
    except Exception:
        return fallback


def own_login() -> str:
    """The account `gh` is signed in as, or empty when it cannot be read.

    Empty is the safe answer. The one judgement that turns on it — whether a claim on
    a ticket was made by this pipeline rather than by a person — then decides that it
    was not, and no claim is given back.
    """
    return gh(["api", "user", "-q", ".login"]).strip()


def _gh_run(args: list[str]) -> tuple[int, str, str]:
    env = tracker.environment()
    run = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    return run.returncode, run.stdout, run.stderr


def spec_tree(spec: int) -> dict:
    """The spec's tickets and each ticket's children, in one query (`issue_tree.py`).

    A tree the tracker could not answer for whole raises `RuntimeError`: a batch read
    with a ticket missing looks exactly like a smaller batch, and every plan this
    program prints would be made on it.
    """
    try:
        return tree.read(spec, "spec", gh=_gh_run)
    except tree.TreeUnreadable as exc:
        raise RuntimeError(f"could not read the tree under #{spec}: {exc}") from None


def sub_issues(number: int) -> list[int]:
    """The spec's tickets, in the tracker's own order."""
    return [child["number"] for child in tree.children(spec_tree(number))]


def read_ticket(number: int) -> dict:
    """One ticket, in the shape the rest of this file expects."""
    fields = ("state,stateReason,labels,assignees,blockedBy,comments,title,"
              "createdAt,closedAt,body")
    raw = gh_json(["issue", "view", str(number), "--json", fields], {})
    return normalise_ticket(number, raw)


def normalise_ticket(number: int, raw: dict) -> dict:
    labels = [l.get("name") for l in raw.get("labels") or [] if isinstance(l, dict)]
    nodes = (raw.get("blockedBy") or {}).get("nodes") or []
    comments = [c for c in raw.get("comments") or [] if isinstance(c, dict)]
    blocked_by = [{"number": int(n["number"]), "state": (n.get("state") or "").upper()}
                  for n in nodes if isinstance(n, dict) and n.get("number")]
    landing_result = events.newest(comments, "ticket.bounced", "ticket.passed",
                                   "ticket.returned", "ticket.landed",
                                   "ticket.regressed")
    bounced = landing_result if (landing_result or {}).get("event") == "ticket.bounced" else None
    return {
        "number": number,
        "state": (raw.get("state") or "").upper(),
        "state_reason": raw.get("stateReason"),
        "title": raw.get("title") or "",
        "body": raw.get("body") or "",
        "created": raw.get("createdAt") or "",
        "closed_at": raw.get("closedAt") or "",
        "labels": labels,
        "assignees": [a.get("login") for a in raw.get("assignees") or [] if isinstance(a, dict)],
        "blocked_by": blocked_by,
        "blockers": [b["number"] for b in blocked_by if b["state"] != "CLOSED"],
        "fold": events.fold(comments, issue=number),
        "bounced_reason": ((bounced or {}).get("payload") or {}).get("reason"),
        # `gh_json` answers `{}` when the call fails. That ticket still exists as a
        # number; reading it as an empty ticket would drop it from every decision.
        "unread_raw": not raw,
    }

# --------------------------------------------------------------------- the tickets

def head_of(ticket: dict) -> str:
    """The line a person reads as where the ticket stands: the first line of the newest
    event. It is shown and never decided on; a comment carrying no event is prose and is
    not shown here."""
    last = ticket["fold"]["last"]
    return last["line"] if last else ""


def outcome_line(ticket: dict) -> str:
    """The first line of the ticket's own result, `ticket.passed` or `ticket.returned`."""
    outcome = ticket["fold"]["outcome"]
    return outcome["line"] if outcome else head_of(ticket)




def phase_of(ticket: dict) -> str:
    """The newest event on the ticket, by name; `closed` or `-` on a ticket with none."""
    last = ticket["fold"]["last"]
    if last:
        return last["event"]
    return "closed" if ticket.get("state") == "CLOSED" else "-"


def in_flight(ticket: dict) -> bool:
    """Whether `land` may treat this ticket's work as still going on, read off the tracker.

        CLOSED                          not in flight — the worker closed it
        OPEN, handed back to triage     not in flight — it said it could not finish
        OPEN, no outcome either way     in flight

    Only `land_plan` asks this. Whether a worker holds the ticket is the fold's `held`,
    and no label changes that answer.
    """
    if ticket.get("state") == "CLOSED":
        return False
    return "needs-triage" not in (ticket.get("labels") or [])


def passed_unlanded(ticket: dict) -> bool:
    """Closed with a `ticket.passed` that no `ticket.landed` has followed."""
    fold = ticket["fold"]
    return ticket.get("state") == "CLOSED" and fold["passed"] and not fold["landed"]


def landed(ticket: dict) -> bool:
    """Closed with a `ticket.passed`, and landed since."""
    fold = ticket["fold"]
    return ticket.get("state") == "CLOSED" and fold["passed"] and fold["landed"]




def unreadable_reason(ticket: dict) -> str:
    """Why this ticket's events cannot be decided on, or empty when they can."""
    if ticket.get("unread_raw"):
        return "the tracker did not answer for it"
    bad = ticket["fold"]["unreadable"]
    if not bad:
        return ""
    item = bad[0]
    more = f" (and {len(bad) - 1} more)" if len(bad) > 1 else ""
    return f"comment {item['comment']}: {item['reason']}{more}"

# --------------------------------------------------------------------- the rows

def blocker_reason(number: int, state: str, tickets: dict[int, dict], lookup) -> str:
    """Why blocker `number` still holds its ticket back, or empty when it no longer does:
    `events.blocker_hold`, the same answer the worker's `--preflight` gives. A blocker's
    events are read only once it is closed; an open one holds whatever they say.
    """
    blocker = (tickets.get(number) or lookup(number)) if state == "CLOSED" else None
    fold = None if blocker is None or blocker.get("unread_raw") else blocker["fold"]
    return events.blocker_hold(state, fold, blocker.get("state_reason") if blocker else None)


def cached(read):
    seen: dict[int, dict] = {}

    def lookup(number: int) -> dict:
        if number not in seen:
            seen[number] = read(number)
        return seen[number]
    return lookup


def holder_of(fold: dict) -> dict | None:
    """What holds the ticket: its newest live session, or the claim no session has taken
    over yet, or None when nothing does. A live session carries the `kind` of agent it
    is — `worker` or `reviewer` — and every sentence about it says which."""
    if fold["holders"]:
        return fold["holders"][-1]
    if fold["claim_hold"]:
        return {"session": None, "runner": None, "started_at": None, "claim": True}
    return None


def holder_text(record: dict) -> str:
    """One live session: which kind of agent it is, its id, its runner, and since when."""
    return (f"the {record.get('kind') or 'session'} {record.get('session') or '?'} on "
            f"{record.get('runner') or '?'}, started "
            f"{record.get('started_at') or 'at an unrecorded time'}")


def retract_advice(holders: list[dict]) -> str:
    """The sentence offering `retract`, or empty when it does not apply.

    `retract` takes back one worker's start. Offered about a reviewer it
    tells the reader to stop a session that is reading a diff, and
    offered about a ticket two workers hold it does not say which one to take back — so
    it is printed only when exactly one worker is among the live sessions, and it names
    that worker.
    """
    workers = [r for r in holders if r.get("kind") == "worker"]
    if len(workers) != 1:
        return ""
    return f"; if the worker {workers[0].get('session') or '?'} is gone, retract it"


def build_rows(numbers: list[int], tickets: dict[int, dict], *, lookup=None) -> list[dict]:
    """One row per ticket: what the tracker says, and what its events fold to."""
    lookup = lookup or cached(read_ticket)
    rows = []
    for number in sorted(set(numbers)):
        ticket = tickets.get(number) or normalise_ticket(number, {})
        fold = ticket["fold"]
        blocking = []
        for node in ticket.get("blocked_by") or []:
            why = blocker_reason(node["number"], node["state"], tickets, lookup)
            if why:
                blocking.append((node["number"], why))
        shown = fold["worker"]
        rows.append({
            "ticket": number,
            "holder": holder_of(fold),
            "holders": fold["holders"],
            "live_workers": fold["live_workers"],
            "state": ticket["state"],
            "labels": ticket["labels"],
            "blockers": [n for n, _ in blocking],
            "blocking": blocking,
            "assignees": ticket["assignees"],
            "unreadable": unreadable_reason(ticket),
            "runner": (shown.get("runner") or "-") if shown else "-",
            "session": (shown.get("session") or "-") if shown else "-",
            "held": ("live" if shown["live"] else shown.get("ended_by") or "-") if shown else "-",
            "since": (shown.get("started_at") or "-") if shown else "-",
            "phase": phase_of(ticket),
            "head": head_of(ticket),
            "outcome": outcome_line(ticket),
            "created": ticket.get("created") or "",
            "closed_at": ticket.get("closed_at") or "",
            "bounced_reason": ticket.get("bounced_reason"),
        })
        rows[-1]["note"] = note_of(ticket, rows[-1])
    return rows


def blocking_text(blocking: list[tuple[int, str]]) -> str:
    return ", ".join(f"#{n}" + ("" if why == "open" else f" ({why})") for n, why in blocking)


def note_of(ticket: dict, row: dict) -> str:
    """One short phrase saying where this ticket stands, in the pipeline's own words.

    Blank means a worker is live on a ticket still in flight: nothing to say.
    """
    head = row["head"]
    if row["unreadable"]:
        return ("events unreadable: " + row["unreadable"])[:80]
    if len(row["live_workers"]) > 1:
        return (f"{len(row['live_workers'])} live workers: "
                + ", ".join(r.get("session") or "?" for r in row["live_workers"]))
    if row["holder"] and row["holder"].get("claim"):
        return "claimed, no session started yet"
    if row["holder"]:
        return ""
    if ticket.get("state") == "CLOSED":
        return head[:60]
    if row["blocking"]:
        return "waiting on " + blocking_text(row["blocking"])
    if "needs-triage" in (ticket.get("labels") or []):
        return head[:60] or "needs-triage"
    if "ready-for-agent" in (ticket.get("labels") or []):
        return "ready"
    return head[:60]


def held(rows: list[dict]) -> list[dict]:
    """The rows a live session — of any kind — or an untaken claim holds."""
    return [r for r in rows if r["holder"]]

# --------------------------------------------------------------------- the frontier

def off_frontier_reasons(row: dict) -> list[str]:
    """Which of `frontier`'s last four conditions this ticket fails, in that order.

    Read for a ticket already known to be open and in the agent queue, so the first
    two conditions are behind it.
    """
    reasons = []
    if row["unreadable"]:
        reasons.append("its events cannot be read — " + row["unreadable"])
    if row["blocking"]:
        reasons.append("blocked by " + blocking_text(row["blocking"]))
    if row["assignees"]:
        reasons.append("claimed by " + ", ".join(row["assignees"]))
    holder = row["holder"]
    holders = row.get("holders") or []
    if holder is not None and holder.get("claim"):
        reasons.append("held by its ticket.claimed, which no started session has taken "
                       "over; if the worker that claimed it is gone, retract it")
    elif holders:
        reasons.append("held by " + ", and by ".join(holder_text(r) for r in holders)
                       + retract_advice(holders))
    return reasons


def frontier(rows: list[dict]) -> list[dict]:
    """The tickets that may be started right now, in ticket order.

    Open, in the agent queue, events readable, every blocker landed, nobody has claimed
    it, and nothing holds it — no `ticket.claimed` and no started session that an event
    has not ended. The last of those is what keeps a second round from starting a second
    worker on a ticket the first one is still doing, on whichever runner and machine
    that worker was started.
    """
    return [r for r in rows
            if r["state"] == "OPEN"
            and "ready-for-agent" in r["labels"]
            and not off_frontier_reasons(r)]


def closeout_problems(rows: list[dict], tickets: dict[int, dict]) -> list[str]:
    """Conditions that make writing ``spec.closed`` unsafe.

    Tickets deliberately left for a person, triage, or an unresolved blocker are valid
    Night outcomes. A readable ticket that can still be dispatched, a live hold, or a
    passed change not yet present on the base branch is not.
    """
    problems = []
    for row in rows:
        if row["unreadable"]:
            problems.append(f"#{row['ticket']} cannot be checked: {row['unreadable']}")
    for row in frontier(rows):
        problems.append(f"#{row['ticket']} is still ready to dispatch")
    for row in held(rows):
        holder = row["holder"]
        if holder.get("claim"):
            problems.append(f"#{row['ticket']} still has an untaken claim")
        else:
            problems.append(
                f"#{row['ticket']} still has a live {holder.get('kind') or 'session'} "
                f"{holder.get('session') or '?'}")
    for number in sorted(tickets):
        if passed_unlanded(tickets[number]):
            problems.append(f"#{number} passed but has not landed")
    return problems


def why_not_on_frontier(row: dict) -> str:
    """Which of `frontier`'s conditions this ticket fails, in that function's order."""
    return ("; ".join(off_frontier_reasons(row))
            or "open, unclaimed, unblocked and unheld: it should have started")


def explain_empty_frontier(rows: list[dict], spec: int) -> None:
    """Say on stderr why nothing can start, one line per ticket still in the queue.

    A frontier that is empty because the batch is finished and a frontier that is empty
    because every ticket is stuck print the same thing — nothing — so whenever the
    batch still holds open tickets in the agent queue and none of them can start, each
    of those tickets names the condition holding it.
    """
    queued = [r for r in rows
              if r["state"] == "OPEN" and "ready-for-agent" in r["labels"]]
    if not queued:
        return
    sys.stderr.write(f"dispatch: nothing on #{spec}'s frontier, and {len(queued)} open "
                     "ticket(s) are still in the agent queue:\n")
    for row in queued:
        sys.stderr.write(f"  #{row['ticket']} {why_not_on_frontier(row)}\n")

# --------------------------------------------------------------------- output

COLUMNS = (("ticket", 8), ("runner", 8), ("session", 16), ("worker", 18),
           ("since", 22), ("phase", 19), ("note", 0))


def render_row(cells: dict) -> str:
    out = []
    for name, width in COLUMNS:
        value = str(cells.get(name, ""))
        out.append(value.ljust(width) if width else value)
    return (" " + "".join(out)).rstrip()


def render_table(rows: list[dict], spec: int | None, now: datetime) -> str:
    head = ["mmw status", now.strftime("%H:%M")]
    if spec:
        head.append(f"spec #{spec}")
    head.append(f"{len(rows)} tickets")
    head.append(f"{len(held(rows))} live")
    lines = [" · ".join(head), ""]
    lines.append(render_row({name: name for name, _ in COLUMNS}))
    for row in rows:
        lines.append(render_row({
            "ticket": f"#{row['ticket']}",
            "runner": row["runner"],
            "session": row["session"],
            "worker": row["held"],
            "since": row["since"],
            "phase": row["phase"],
            "note": row["note"],
        }))
    return "\n".join(lines)


NIGHT_SUMMARY = "NIGHT SUMMARY {date}"


def night_opened(now: datetime | None = None) -> str:
    """Sixteen hours before now, the window `--summary` treats as tonight.

    This program has no process that lives the night, so the window is a lookback long
    enough to cover a night that started in the evening and is summarised the next
    morning.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now.astimezone(timezone.utc) - timedelta(hours=16)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


ROUTE_SLOTS = "opened/fixed/became/skipped/unread/open"
ROUTES = {"fixed": "fixed", "became-ticket": "became", "stale": "skipped"}


def is_finding(child: dict) -> bool:
    """A child its parent's `child.opened` event records as the `finding` kind."""
    return child.get("kind") == "finding"


def route_of(child: dict) -> str:
    """`fixed`, `became`, `skipped`, `open`, or `unread`.

    The route is the `resolution` of the originating ticket's `child.closed` event for
    this child. A finding that became a ticket in place stays open — it is the ticket
    now — so `became-ticket` counts whatever its state; `fixed` and `stale` close the
    child, so an open one with either has not been routed through yet. An open child with
    no route is open; a closed one no event accounts for is unread.
    """
    resolution = child.get("resolution") or ""
    if resolution == "became-ticket":
        return ROUTES[resolution]
    if (child.get("state") or "").upper() != "CLOSED":
        return "open"
    return ROUTES.get(resolution, "unread")


def routed_counts(children: list[dict]) -> tuple[int, int, int, int, int, int]:
    """opened / fixed / became / skipped / unread / open among this batch's findings.

    opened is the `finding` children of the batch, plus any child the tracker could not
    answer for. The other five partition it: orchestrator fixed on the closing pass,
    became a ticket, left undone as stale, could not be classified (or read), and still
    open. The unread slot is what keeps an unreadable child from looking like a skipped
    one. The night window does not apply: this is the batch, not tonight's listing.
    """
    seen: Counter[str] = Counter()
    opened = 0
    for child in children:
        if child.get("unread_raw"):
            opened += 1
            seen["unread"] += 1
            continue
        if not is_finding(child):
            continue
        opened += 1
        seen[route_of(child)] += 1
    return (opened, seen["fixed"], seen["became"], seen["skipped"],
            seen["unread"], seen["open"])


def routed_line(counts: tuple[int, int, int, int, int, int]) -> str:
    """The summary line a person reads: slash counts, then the names of the slots.

    It says `Findings` because it counts only the `finding` kind of child. A batch also
    opens `contract`, `deferred`, `decision` and `fault` children, and those are listed
    by `Sub-issues opened tonight:` above without being routed here — so the two lines
    carry different totals on purpose, and the label is what says why."""
    return f"Findings routed: {'/'.join(str(n) for n in counts)} ({ROUTE_SLOTS})"


def summary(rows: list[dict], opened: str, now: datetime | None = None,
            children: list[dict] | None = None) -> str:
    """Ticket numbers and the first line of each one's result; sub-issues by title."""
    now = now or datetime.now()
    kids = list(children or ())
    closed = [f"#{r['ticket']} {r['outcome'][:80]}".strip()
              for r in rows if r["state"] == "CLOSED" and r["closed_at"] > opened]
    back = [f"#{r['ticket']} {r['outcome'][:80]}".strip()
            for r in rows if r["state"] == "OPEN" and "needs-triage" in r["labels"]
            and not r.get("bounced_reason")]
    bounced = [f"#{r['ticket']} ({r['bounced_reason']})"
               for r in rows if r.get("bounced_reason") and "needs-triage" in r["labels"]]
    waiting = [f"#{r['ticket']} blocked by " + blocking_text(r["blocking"])
               for r in rows if r["state"] == "OPEN" and r["blocking"]]
    fresh = [f"#{c['number']} {(c.get('title') or '')[:80]}".strip()
             for c in kids if (c.get("created") or "") > opened]
    return "\n".join([
        NIGHT_SUMMARY.format(date=now.strftime("%Y-%m-%d")),
        "",
        "Closed: " + (", ".join(closed) or "None"),
        "Handed back to needs-triage: " + (", ".join(back) or "None"),
        "Bounced: " + (", ".join(bounced) or "None"),
        "Not dispatched, a blocker stayed open: " + (", ".join(waiting) or "None"),
        "Sub-issues opened tonight: " + (", ".join(fresh) or "None"),
        routed_line(routed_counts(kids)),
    ])

# --------------------------------------------------------------- the command forms

def collect(spec: int) -> tuple[list[dict], dict[int, dict]]:
    """Everything one round needs: the rows, and the tickets behind them."""
    numbers = sub_issues(spec)
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    return build_rows(numbers, tickets), tickets








def worker_grades(spec: int) -> int:
    """The worker-grade labels of every ticket the night could dispatch.

    One `BATCH` line per child of the spec, then one `GRADE` line per ticket that is
    `OPEN` and labelled `ready-for-agent`, blocked or not:

        BATCH <ticket>
        GRADE <ticket> [<label> ...]

    The labels are the ticket's own ending in `-worker`, in name order, and a ticket
    carrying none prints the number alone. `dispatch.sh check` reads the `GRADE` lines
    before the night opens, and refuses the night when a label names a row models.json
    lacks or a ticket carries two — the same refusals a dispatch would make, brought
    to the one moment somebody is here to fix them. `dispatch.sh suspend` reads the
    `BATCH` lines as the spec's children, so that list is not fetched a second time.
    """
    for number in sub_issues(spec):
        print(f"BATCH {number}")
        ticket = read_ticket(number)
        if ticket["state"] != "OPEN" or "ready-for-agent" not in ticket["labels"]:
            continue
        grades = sorted(l for l in ticket["labels"] if l and l.endswith("-worker"))
        print(" ".join(["GRADE", str(number), *grades]))
    return 0


def table(spec: int) -> int:
    rows, _ = collect(spec)
    print(render_table(rows, spec, datetime.now()))
    return 0


def batch_children(spec: int, batch: dict | None = None) -> list[dict]:
    """Every child this batch's tickets name, once each.

    A ticket's own fold names its children by `child.opened`, plus any the tree holds
    under it that no event names; each child's kind and route are its owner's events.
    Where a child sits now decides nothing: a finding that became a ticket has moved
    from under its ticket to under the spec. Each child dict carries its owner ticket
    number under `"owner"`, the one whose fold lists it and the one `route` posts to.
    Pass an already-read `batch` (from `spec_tree`) to avoid a second read of the tree.
    """
    if batch is None:
        batch = spec_tree(spec)
    numbers = [t["number"] for t in tree.children(batch)]
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    children: list[dict] = []
    seen: set[int] = set()
    for node in tree.children(batch):
        number = node["number"]
        known = tickets[number]["fold"]["children"] if number in tickets else {}
        named = [int(k) for k, v in known.items() if v.get("opened") and str(k).isdigit()]
        for child_number in named + [c["number"] for c in tree.children(node)]:
            if child_number in seen:
                continue
            seen.add(child_number)
            child = read_ticket(child_number)
            recorded = known.get(str(child_number)) or {}
            if recorded.get("kind"):
                child["kind"] = recorded["kind"]
            if recorded.get("resolution"):
                child["resolution"] = recorded["resolution"]
            child["owner"] = number
            children.append(child)
    return children


def print_summary(spec: int) -> int:
    """The night summary, from one read of the spec's tree and its tickets' events."""
    batch = spec_tree(spec)
    numbers = [t["number"] for t in tree.children(batch)]
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    rows = build_rows(numbers, tickets)
    print(summary(rows, night_opened(), children=batch_children(spec, batch)))
    return 0


def open_findings(spec: int) -> list[tuple[int, int, str]]:
    """(<ticket>, <child>, title) for every finding under this batch that `route` has
    not yet closed. `<ticket>` is the one `route` posts to, the one whose fold lists it."""
    return [(child["owner"], child["number"], child.get("title") or "")
            for child in batch_children(spec)
            if is_finding(child) and route_of(child) == "open"]


def print_findings(spec: int) -> int:
    for number, child_number, title in open_findings(spec):
        print(f"{number} {child_number} {title}")
    return 0





# --------------------------------------------------------------------- entry





def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    forms = parser.add_mutually_exclusive_group(required=True)
    for flag in ("table", "frontier", "summary", "findings", "worker-grades"):
        forms.add_argument("--" + flag, action="store_true")
    parser.add_argument("spec", type=int)
    args = parser.parse_args(argv)
    try:
        if args.frontier:
            rows, _ = collect(args.spec)
            unread = [r for r in rows if r["unreadable"]]
            if unread:
                raise RuntimeError("cannot determine eligible work: " + "; ".join(
                    f"#{r['ticket']}: {r['unreadable']}" for r in unread))
            for row in frontier(rows):
                print(row["ticket"])
            return 0
        if args.summary:
            return print_summary(args.spec)
        if args.findings:
            return print_findings(args.spec)
        if args.worker_grades:
            return worker_grades(args.spec)
        return table(args.spec)
    except (RuntimeError, OSError, ValueError, tracker.RepositoryError) as exc:
        print(f"status: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
