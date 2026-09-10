#!/usr/bin/env python3
"""One read-only view of every ticket under a spec, computed from the tickets' events.

    status.py --table <spec>            print one table and exit
    status.py --advance-plan <spec>     what `dispatch.sh advance` has to do, in order
    status.py --reverify-plan <spec>    the landed tickets `dispatch.sh reverify` runs again
    status.py --worker-grades <spec>    the worker-grade labels of every ticket in the queue
    status.py --summary <spec>          print the night summary; do not post it
    status.py --land-plan <n>...        what landing each of these tickets calls for

One program, six forms, reading one source, so there is never a second truth to
reconcile. The source is the tracker (`gh`): each ticket's state, labels, assignees and
blocking links, and its comments. Where a ticket stands — which agent sessions were
started on it and on which runner, whether its worker is still live, whether it passed,
landed or came back — is the fold of its comments' events, computed by `events.py` of
the verify-ticket skill (`MMW_EVENTS_PY` names it when `dispatch.sh` resolved it
somewhere else). Nothing here asks a runner what it is running: a runner answers for
one machine, and the ticket answers for all of them. Nothing this program does needs a
model, and nothing it does writes to the tracker. Each invocation is a full re-read.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_events():
    default = Path(__file__).resolve().parents[2] / "verify-ticket" / "scripts" / "events.py"
    path = Path(os.environ.get("MMW_EVENTS_PY") or default)
    if not path.is_file():
        sys.stderr.write(f"dispatch: no events.py at {path}; the verify-ticket skill has to "
                         f"sit beside this one, or MMW_EVENTS_PY has to name its events.py\n")
        raise SystemExit(2)
    spec = importlib.util.spec_from_file_location("mmw_events", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = _load_events()

# --------------------------------------------------------------------- reading

def gh(args: list[str]) -> str:
    """`gh` with the colour forcing some hosts inject stripped off its output.

    Grok Build hands its agents CLICOLOR_FORCE=1, under which `gh` writes ANSI escapes
    into --json output that no JSON reader can parse.
    """
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
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


def sub_issues(number: int) -> list[int]:
    """The issue's own children, followed through the tracker's native relation.

    Called with a spec, that is the batch. Called with a ticket, that is what
    the ticket opened.
    """
    rows = gh_json(["api", "--paginate", "--slurp",
                    f"repos/{{owner}}/{{repo}}/issues/{number}/sub_issues?per_page=100"], [])
    # `--slurp` answers with one array per page; a single page answered flat is read too.
    flat = [r for page in rows for r in (page if isinstance(page, list) else [page])]
    return [int(r["number"]) for r in flat if isinstance(r, dict) and r.get("number")]


def read_ticket(number: int) -> dict:
    """One ticket, in the shape the rest of this file expects."""
    fields = ("state,labels,assignees,blockedBy,comments,title,"
              "createdAt,closedAt,body")
    raw = gh_json(["issue", "view", str(number), "--json", fields], {})
    return normalise_ticket(number, raw)


def normalise_ticket(number: int, raw: dict) -> dict:
    labels = [l.get("name") for l in raw.get("labels") or [] if isinstance(l, dict)]
    nodes = (raw.get("blockedBy") or {}).get("nodes") or []
    comments = [c for c in raw.get("comments") or [] if isinstance(c, dict)]
    blocked_by = [{"number": int(n["number"]), "state": (n.get("state") or "").upper()}
                  for n in nodes if isinstance(n, dict) and n.get("number")]
    return {
        "number": number,
        "state": (raw.get("state") or "").upper(),
        "title": raw.get("title") or "",
        "body": raw.get("body") or "",
        "created": raw.get("createdAt") or "",
        "closed_at": raw.get("closedAt") or "",
        "labels": labels,
        "assignees": [a.get("login") for a in raw.get("assignees") or [] if isinstance(a, dict)],
        "blocked_by": blocked_by,
        "blockers": [b["number"] for b in blocked_by if b["state"] != "CLOSED"],
        "comments": [c.get("body") or "" for c in comments],
        "fold": events.fold(comments, issue=number),
        # `gh_json` answers `{}` when the call fails. That ticket still exists as a
        # number; reading it as an empty ticket would drop it from every decision.
        "unread_raw": not raw,
    }

# --------------------------------------------------------------------- the tickets

def first_line(text: str) -> str:
    stripped = (text or "").strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def newest_with_first_line(ticket: dict, *prefixes: str) -> str:
    """The newest comment whose first line starts with one of `prefixes`.

    Used for the criteria runs alone: `self-run` and `reverify` comments are the ledger
    each run posts, not events, and their counts are read off them.
    """
    for body in reversed(ticket.get("comments") or []):
        head = first_line(body)
        if any(head.startswith(p) for p in prefixes):
            return body
    return ""


def head_of(ticket: dict) -> str:
    """The line a person reads as where the ticket stands.

    The first line of the newest event, or, on a ticket that carries none, of the newest
    comment. It is shown and never decided on.
    """
    last = ticket["fold"]["last"]
    if last:
        return last["line"]
    comments = ticket.get("comments") or []
    return first_line(comments[-1]) if comments else ""


def outcome_line(ticket: dict) -> str:
    """The first line of the ticket's own result, `ticket.passed` or `ticket.returned`."""
    outcome = ticket["fold"]["outcome"]
    return outcome["line"] if outcome else head_of(ticket)


# The three summary lines gate-check prints, one of which is the second line of every
# `self-run` and `reverify` comment. Each stops at its own numbers rather than at the
# closing bracket, because the bracket may also hold the reverify counts or a scope.
ALL_MET_RE = re.compile(r"^ALL MET\s*\((\d+)\s+met\b")
UNMET_RE = re.compile(r"^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\b")
HANDOFF_RE = re.compile(
    r"^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(met:\s*(\d+)"
    r"(?:,\s*unmet:\s*(\d+))?")


def counted_ac(ticket: dict) -> str:
    """`<met>/<total>` off the newest self-run or reverify comment, or `-`.

    The total is every criterion the summary line accounts for: met, unmet, and, on a
    `HANDOFF REQUIRED:` line, abandoned as well. `ALL MET` accounts for none but the
    met ones, which is what makes it `ALL MET`.
    """
    body = newest_with_first_line(ticket, "self-run", "reverify")
    for raw in body.splitlines():
        line = raw.strip()
        found = ALL_MET_RE.match(line)
        if found:
            met = int(found.group(1))
            return f"{met}/{met}"
        found = HANDOFF_RE.match(line)
        if found:
            abandoned, met = int(found.group(1)), int(found.group(2))
            unmet = int(found.group(3) or 0)
            return f"{met}/{met + unmet + abandoned}"
        found = UNMET_RE.match(line)
        if found:
            unmet, met = int(found.group(1)), int(found.group(2))
            return f"{met}/{met + unmet}"
    return "-"


def phase_of(ticket: dict) -> str:
    """The newest event on the ticket, by name; `closed` or `-` on a ticket with none."""
    last = ticket["fold"]["last"]
    if last:
        return last["event"]
    return "closed" if ticket.get("state") == "CLOSED" else "-"


def in_flight(ticket: dict) -> bool:
    """Whether `land` may treat this ticket's work as still going on, read off the tracker.

        CLOSED                          not in flight — the worker wrote its verdict
        OPEN, handed back to triage     not in flight — it said it could not finish
        OPEN, no verdict either way     in flight

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
    """Why blocker `number` still holds its ticket back, or empty when it no longer does.

    A blocker lets go when its work is on the base branch, not when it closes: the
    ticket it blocks is cut from the base branch and has to find that work there. The
    signal is `ticket.landed`, read off the blocker's own events. A blocker closed without
    a pass — by a person, or as not planned — has nothing that will ever land, and lets
    go on closing.
    """
    if state != "CLOSED":
        return "open"
    blocker = tickets.get(number) or lookup(number)
    if blocker is None or blocker.get("unread_raw"):
        return "the tracker did not answer for it"
    if blocker["fold"]["unreadable"]:
        return "its events cannot be read"
    if not passed_unlanded(blocker):
        return ""
    return "passed, not landed"


def cached(read):
    seen: dict[int, dict] = {}

    def lookup(number: int) -> dict:
        if number not in seen:
            seen[number] = read(number)
        return seen[number]
    return lookup


def holder_of(fold: dict) -> dict | None:
    """What holds the ticket: its newest live session, or the claim no session has taken
    over yet, or None when nothing does."""
    if fold["holders"]:
        return fold["holders"][-1]
    if fold["claim_hold"]:
        return {"session": None, "runner": None, "started_at": None, "claim": True}
    return None


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
            "worker": holder_of(fold),
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
            "ac": counted_ac(ticket) or "-",
            "head": head_of(ticket),
            "outcome": outcome_line(ticket),
            "created": ticket.get("created") or "",
            "closed_at": ticket.get("closed_at") or "",
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
    if row["worker"] and row["worker"].get("claim"):
        return "claimed, no session started yet"
    if row["worker"]:
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
    """The rows a live worker holds."""
    return [r for r in rows if r["worker"]]

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
    worker = row["worker"]
    if worker is not None and worker.get("claim"):
        reasons.append("held by its ticket.claimed, which no started session has taken "
                       "over; if the worker that claimed it is gone, retract it")
    elif worker is not None:
        reasons.append(f"held by the worker {worker.get('session') or '?'} on "
                       f"{worker.get('runner') or '?'}, started "
                       f"{worker.get('started_at') or 'at an unrecorded time'}; if that "
                       f"session is gone, retract it")
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
           ("since", 22), ("phase", 19), ("ac", 7), ("note", 0))


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
            "ac": row["ac"],
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


def is_review_sub_issue(child: dict) -> bool:
    """A child its parent's `child.opened` event records as the `review` kind."""
    return child.get("kind") == "review"


def route_of(child: dict) -> str:
    """`fixed`, `became`, `skipped`, `open`, or `unread`.

    The route is the `resolution` of the parent's `child.closed` event for this child.
    Only a CLOSED child has one; a child that is still open has not been routed yet,
    which is a different state from a closed one no event accounts for.
    """
    if (child.get("state") or "").upper() != "CLOSED":
        return "open"
    return ROUTES.get(child.get("resolution") or "", "unread")


def routed_counts(children: list[dict]) -> tuple[int, int, int, int, int, int]:
    """opened / fixed / became / skipped / unread / open among this batch's review sub-issues.

    opened is the review sub-issues of the batch, plus any child the tracker could not
    answer for. The other five partition it: main agent fixed on the closing pass,
    folded into a new ticket, left undone as stale, could not be classified (or read),
    and still open. The unread slot is what keeps an unreadable child from looking like
    a skipped one. The night window does not apply: this is the batch, not tonight's
    listing.
    """
    seen: Counter[str] = Counter()
    opened = 0
    for child in children:
        if child.get("unread_raw"):
            opened += 1
            seen["unread"] += 1
            continue
        if not is_review_sub_issue(child):
            continue
        opened += 1
        seen[route_of(child)] += 1
    return (opened, seen["fixed"], seen["became"], seen["skipped"],
            seen["unread"], seen["open"])


def routed_line(counts: tuple[int, int, int, int, int, int]) -> str:
    """The summary line a person reads: slash counts, then the names of the slots.

    It says `Review` because it counts only the `review` kind of child. A batch also
    opens `outside-owns`, `baseline`, `decision` and `pipeline` children, and those are
    listed by `Sub-issues opened tonight:` above without being routed here — so the two
    lines carry different totals on purpose, and the label is what says why."""
    return f"Review sub-issues routed: {'/'.join(str(n) for n in counts)} ({ROUTE_SLOTS})"


def summary(rows: list[dict], opened: str, now: datetime | None = None,
            children: list[dict] | None = None) -> str:
    """Ticket numbers and the first line of each one's result; sub-issues by title."""
    now = now or datetime.now()
    kids = list(children or ())
    closed = [f"#{r['ticket']} {r['outcome'][:80]}".strip()
              for r in rows if r["state"] == "CLOSED" and r["closed_at"] > opened]
    back = [f"#{r['ticket']} {r['outcome'][:80]}".strip()
            for r in rows if r["state"] == "OPEN" and "needs-triage" in r["labels"]]
    waiting = [f"#{r['ticket']} blocked by " + blocking_text(r["blocking"])
               for r in rows if r["state"] == "OPEN" and r["blocking"]]
    fresh = [f"#{c['number']} {(c.get('title') or '')[:80]}".strip()
             for c in kids if (c.get("created") or "") > opened]
    return "\n".join([
        NIGHT_SUMMARY.format(date=now.strftime("%Y-%m-%d")),
        "",
        "Closed: " + (", ".join(closed) or "None"),
        "Handed back to needs-triage: " + (", ".join(back) or "None"),
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


def advance_plan(spec: int) -> int:
    """What the main agent's next `dispatch.sh advance` has to do, in order.

    Three kinds of line and nothing else on stdout, because a script reads this, in the
    order `dispatch.sh` acts on them:

        MERGE <ticket>      closed with a pass that has not landed, the one that
                            closed first at the top
        RELEASE <ticket>    in the agent queue and claimed by this pipeline, and an
                            event has ended every hold on it: the worker is gone
        DISPATCH <ticket>   on the frontier as the tracker stands now, in ticket order

    The frontier reads the tracker as it stands: a merge this plan asks for unblocks
    nothing until its `ticket.landed` is on the ticket. `dispatch.sh` therefore asks for
    the plan a second time after its merges and releases, and starts only what that
    second plan's DISPATCH lines name.

    A ticket is held from its `ticket.claimed` or any `*.started` until an event ends
    the hold (`events.ENDS_EVERY_HOLD`, `events.ENDS_ONE_HOLD`); no runner is asked and
    no label is read. A claim is given back only after such an event: a claim no event
    ever showed a worker holding is kept, since nothing shows its worker gone. A ticket
    whose events cannot be read is neither merged nor released nor dispatched, and says
    why.

    Whether a branch exists and whether it is already in the base branch are git's
    questions, and git is not this program's source. `dispatch.sh` asks them.

    What no line accounts for goes to stderr: an empty frontier with tickets still in
    the agent queue names every one of them and the condition holding it.
    """
    numbers = sub_issues(spec)
    tickets = {n: read_ticket(n) for n in numbers}
    done = []
    for ticket in tickets.values():
        if not passed_unlanded(ticket):
            continue
        if unreadable_reason(ticket):
            print(f"#{ticket['number']} is not merged: its events cannot be read "
                  f"({unreadable_reason(ticket)})", file=sys.stderr)
            continue
        done.append(ticket)
    for ticket in sorted(done, key=lambda t: t["closed_at"]):
        print(f"MERGE {ticket['number']}")
    rows = build_rows(numbers, tickets)
    login = own_login()
    for row in rows:
        if row["state"] != "OPEN" or "ready-for-agent" not in row["labels"]:
            continue
        if not login or login not in row["assignees"]:
            continue
        if row["unreadable"]:
            print(f"#{row['ticket']} keeps its claim: its events cannot be read "
                  f"({row['unreadable']})", file=sys.stderr)
            continue
        worker = row["worker"]
        if worker is not None and worker.get("claim"):
            print(f"#{row['ticket']} keeps its claim: its ticket.claimed is still a hold, "
                  f"and no event has ended it", file=sys.stderr)
            continue
        if worker is not None:
            print(f"#{row['ticket']} keeps its claim: the worker "
                  f"{worker.get('session')} on {worker.get('runner')} "
                  f"is live on its events", file=sys.stderr)
            continue
        if not tickets[row["ticket"]]["fold"]["hold_ended"]:
            print(f"#{row['ticket']} keeps its claim: no event on it ever showed a worker "
                  f"holding it, so none shows that worker gone", file=sys.stderr)
            continue
        print(f"RELEASE {row['ticket']}")
        row["assignees"] = [a for a in row["assignees"] if a != login]
    ready = frontier(rows)
    for row in ready:
        print(f"DISPATCH {row['ticket']}")
    if not ready:
        explain_empty_frontier(rows, spec)
    return 0


def reverify_plan(spec: int) -> int:
    """The tickets `dispatch.sh reverify` runs again on the base branch, in closing order.

        REVERIFY <ticket>   closed with a pass, and landed

    A ticket that passed and has not landed is not on the base branch, so running its
    criteria there would fail it for work that is not there yet; it is named on stderr
    instead.
    """
    tickets = [read_ticket(n) for n in sub_issues(spec)]
    for ticket in sorted(tickets, key=lambda t: t["closed_at"]):
        if unreadable_reason(ticket):
            print(f"#{ticket['number']} is not re-run: its events cannot be read "
                  f"({unreadable_reason(ticket)})", file=sys.stderr)
        elif landed(ticket):
            print(f"REVERIFY {ticket['number']}")
        elif passed_unlanded(ticket):
            print(f"#{ticket['number']} passed and has not landed, so it is not re-run "
                  f"on the base branch", file=sys.stderr)
    return 0


def land_plan(numbers: list[int]) -> int:
    """What landing each of these tickets calls for, in the order `dispatch.sh` acts.

    Five kinds of line and nothing else on stdout, because a script reads this:

        MERGE <ticket>        closed with a pass that has not landed: its branch belongs
                              in the base branch
        RELEASE <ticket>      this pipeline still holds the claim, and the work is over
        ARCHIVE <ticket>      its workspace, the agents inside it and its slot may all go
        HOLD <ticket> <why>   still being worked, or its events cannot be read: nothing
                              may be done to it yet
        NOTHING <ticket> <why>  over, and already landed: there is nothing left to do

    Every ticket gets at least one line. A ticket that needs nothing is the case that
    reads exactly like a ticket the plan forgot — so it says so.

    A ticket handed back to triage is over as a piece of work, but its worktree is what
    the next `start` reuses, and archiving a workspace deletes that directory. So a hand
    back gives the claim back and keeps the workspace; only a closed ticket has both
    taken away.
    """
    login = own_login()
    for number in numbers:
        ticket = read_ticket(number)
        if not ticket["state"]:
            print(f"HOLD {number} the tracker could not be asked about this ticket")
            continue
        bad = unreadable_reason(ticket)
        if bad:
            print(f"HOLD {number} its events cannot be read ({bad})")
            continue
        if in_flight(ticket):
            head = head_of(ticket)
            print(f"HOLD {number} it is open with no verdict on it"
                  + (f" (newest: {head[:50]})" if head else ""))
            continue
        closed = ticket["state"] == "CLOSED"
        asked = False
        if closed and ticket["fold"]["passed"] and not ticket["fold"]["landed"]:
            print(f"MERGE {number}")
            asked = True
        if login and login in ticket["assignees"]:
            print(f"RELEASE {number}")
            asked = True
        if closed:
            print(f"ARCHIVE {number}")
            asked = True
        if not asked:
            print(f"NOTHING {number} handed back to triage, unclaimed, and its workspace "
                  f"is kept for the next start")
    return 0


def worker_grades(spec: int) -> int:
    """The worker-grade labels of every ticket the night could dispatch.

    One `BATCH` line per child of the spec, then one `GRADE` line per ticket that is
    `OPEN` and labelled `ready-for-agent`, blocked or not:

        BATCH <ticket>
        GRADE <ticket> [<label> ...]

    The labels are the ticket's own ending in `-worker`, in name order, and a ticket
    carrying none prints the number alone. `dispatch.sh check` reads the `GRADE` lines
    before the night opens, and refuses the night when a label names a row the live table
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


def print_summary(spec: int) -> int:
    rows, tickets = collect(spec)
    children = []
    for number in (r["ticket"] for r in rows):
        known = tickets[number]["fold"]["children"] if number in tickets else {}
        for child_number in sub_issues(number):
            child = read_ticket(child_number)
            recorded = known.get(str(child_number)) or {}
            if recorded.get("kind"):
                child["kind"] = recorded["kind"]
            if recorded.get("resolution"):
                child["resolution"] = recorded["resolution"]
            children.append(child)
    print(summary(rows, night_opened(), children=children))
    return 0

# --------------------------------------------------------------------- entry

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="status.py",
        description="The read-only view over one spec's tickets, from their events.")
    forms = parser.add_mutually_exclusive_group(required=True)
    forms.add_argument("--table", action="store_true",
                       help="print one table and exit")
    forms.add_argument("--advance-plan", action="store_true",
                       help="print what `dispatch.sh advance` has to do, in order")
    forms.add_argument("--reverify-plan", action="store_true",
                       help="print the landed tickets `dispatch.sh reverify` runs again")
    forms.add_argument("--worker-grades", action="store_true",
                       help="print the worker-grade labels of every ticket in the agent queue")
    forms.add_argument("--summary", action="store_true",
                       help="print the night summary and do not post it")
    forms.add_argument("--land-plan", action="store_true",
                       help="print what landing each of these tickets calls for")
    parser.add_argument("spec", type=int, nargs="+",
                        help="the spec issue whose sub-issues are tonight's tickets, or "
                             "with --land-plan the ticket numbers to land")
    args = parser.parse_args(argv)
    if not args.land_plan and len(args.spec) != 1:
        parser.error("only --land-plan takes more than one number")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(list(sys.argv[1:] if argv is None else argv))
        if args.land_plan:
            return land_plan(args.spec)
        if args.advance_plan:
            return advance_plan(args.spec[0])
        if args.reverify_plan:
            return reverify_plan(args.spec[0])
        if args.worker_grades:
            return worker_grades(args.spec[0])
        if args.summary:
            return print_summary(args.spec[0])
        return table(args.spec[0])
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"dispatch: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
