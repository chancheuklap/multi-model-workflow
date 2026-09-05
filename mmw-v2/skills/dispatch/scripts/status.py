#!/usr/bin/env python3
"""One read-only view of every ticket under a spec and every Paseo agent on one.

    status.py --table <spec>          print one table and exit
    status.py --advance-plan <spec>   what `dispatch.sh advance` has to do, in order
    status.py --worker-grades <spec>  the worker-grade labels of every ticket in the queue
    status.py --summary <spec>        print the night summary; do not post it

One program, four forms, reading the same two sources, so there is never a second
truth to reconcile. `--table` is what an agent runs when it wants the whole picture
in one screen. Nothing this program does needs a model, and nothing it does writes
to the tracker or to Paseo.

The two sources are the tracker (`gh`) and Paseo (`paseo ls` / `paseo inspect`), and
nothing else. There is no state file: each invocation is a full re-read.

Which ticket an agent belongs to is the basename of its `cwd`: `issue-<n>`. Kind is
the `--label mmw.kind=` filter that returned the row — CLI `paseo ls --json` does
not carry labels in the body, so the script asks once per kind. `phase` and the
criteria count come off the ticket's comments.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def paseo(args: list[str]) -> str:
    """`paseo` with the same colour stripping as `gh`."""
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    run = subprocess.run(["paseo", *args], capture_output=True, text=True, env=env,
                         timeout=20)
    if run.returncode != 0:
        raise RuntimeError(f"paseo {' '.join(args)}: exit {run.returncode}")
    return run.stdout


def paseo_json(args: list[str]):
    text = paseo(args)
    if not text.strip():
        raise RuntimeError(f"paseo {' '.join(args)}: no answer")
    return json.loads(text)


AGENT_KINDS = ("worker", "reviewer", "verifier")


def live_agents(spec: int) -> list[dict]:
    """Every live agent labelled `mmw.spec=<spec>`, with inspect fields merged in.

    `paseo ls --json` has no labels in the body, so both filters are `--label` on
    the call: one `ls` per `mmw.kind`. Each agent is then inspected once for
    `LastUsage` and `PendingPermissions`. Raises when `ls` itself could not be
    asked: an unanswered call is not an empty list.
    """
    out = []
    seen: set[str] = set()
    for kind in AGENT_KINDS:
        rows = paseo_json([
            "ls", "-g", "--json",
            "--label", f"mmw.spec={spec}",
            "--label", f"mmw.kind={kind}",
        ])
        if not isinstance(rows, list):
            raise RuntimeError("paseo ls: expected a list")
        for row in rows:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            agent_id = row["id"]
            if agent_id in seen:
                continue
            seen.add(agent_id)
            try:
                detail = paseo_json(["inspect", agent_id, "--json"])
            except Exception:
                detail = {}
            if not isinstance(detail, dict):
                detail = {}
            merged = dict(row)
            merged["kind"] = kind
            merged["LastUsage"] = detail.get("LastUsage")
            merged["PendingPermissions"] = detail.get("PendingPermissions") or []
            out.append(merged)
    return out


def sub_issues(number: int) -> list[int]:
    """The issue's own children, followed through the tracker's native relation.

    Called with a spec, that is the batch. Called with a ticket, that is what
    the ticket opened. A sub-issue a worker opened during the night is in the
    ticket's list, told apart by when it appeared.
    """
    rows = gh_json(["api", "--paginate", "--slurp",
                    f"repos/{{owner}}/{{repo}}/issues/{number}/sub_issues?per_page=100"], [])
    # `--slurp` answers with one array per page; a single page answered flat is read too.
    flat = [r for page in rows for r in (page if isinstance(page, list) else [page])]
    return [int(r["number"]) for r in flat if isinstance(r, dict) and r.get("number")]


def read_ticket(number: int) -> dict:
    """One ticket, in the shape the rest of this file expects."""
    fields = ("state,labels,assignees,blockedBy,comments,title,"
              "createdAt,closedAt")
    raw = gh_json(["issue", "view", str(number), "--json", fields], {})
    return normalise_ticket(number, raw)


def normalise_ticket(number: int, raw: dict) -> dict:
    labels = [l.get("name") for l in raw.get("labels") or [] if isinstance(l, dict)]
    nodes = (raw.get("blockedBy") or {}).get("nodes") or []
    bodies = [c.get("body") or "" for c in raw.get("comments") or [] if isinstance(c, dict)]
    return {
        "number": number,
        "state": (raw.get("state") or "").upper(),
        "title": raw.get("title") or "",
        "created": raw.get("createdAt") or "",
        "closed_at": raw.get("closedAt") or "",
        "labels": labels,
        "assignees": [a.get("login") for a in raw.get("assignees") or [] if isinstance(a, dict)],
        "blockers": [int(n["number"]) for n in nodes
                     if isinstance(n, dict) and n.get("state") != "CLOSED" and n.get("number")],
        "comments": bodies,
    }

# --------------------------------------------------------------------- the tickets

def first_line(text: str) -> str:
    stripped = (text or "").strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def last_first_line(ticket: dict) -> str:
    """The first line of the ticket's newest comment: the pipeline's protocol slot."""
    comments = ticket.get("comments") or []
    return first_line(comments[-1]) if comments else ""


def newest_with_first_line(ticket: dict, *prefixes: str) -> str:
    """The newest comment whose first line starts with one of `prefixes`."""
    for body in reversed(ticket.get("comments") or []):
        head = first_line(body)
        if any(head.startswith(p) for p in prefixes):
            return body
    return ""


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


# The protocol-slot prefixes that name a `phase`. Newest matching comment wins.
PHASE_MARKERS = (
    ("self-run", "self-run"),
    ("reverify", "reverify"),
    ("VERDICT", "VERDICT"),
    ("DECISIONS", "DECISIONS"),
    ("REVIEW", "REVIEW"),
    ("ALL MET", "ALL MET"),
    ("HANDOFF REQUIRED", "HANDOFF REQUIRED"),
)


def phase_of(ticket: dict) -> str:
    """Where the ticket stands, read off the newest protocol-slot comment, or `-`."""
    body = newest_with_first_line(ticket, *[prefix for prefix, _ in PHASE_MARKERS])
    head = first_line(body)
    for prefix, label in PHASE_MARKERS:
        if head.startswith(prefix):
            return label
    if ticket.get("state") == "CLOSED":
        return "closed"
    return "-"

# --------------------------------------------------------------------- the sessions

ISSUE_DIR = re.compile(r"^issue-(\d+)$")


def ticket_of_cwd(cwd: str) -> int | None:
    """The ticket number encoded as the basename of a worktree, or None."""
    base = Path((cwd or "").rstrip("/")).name
    found = ISSUE_DIR.fullmatch(base)
    return int(found.group(1)) if found else None


def sessions(agents: list[dict]) -> list[dict]:
    """The spec's live agents, each named as a ticket and a kind.

    A live agent whose `cwd` basename is not `issue-<n>` is not ours. Kind is
    whatever `live_agents` set from the `mmw.kind` filter; a missing kind is a
    worker, which is what a test fixture that only names the ticket produces.
    """
    found = []
    for agent in agents:
        number = ticket_of_cwd(agent.get("cwd") or "")
        if number is None:
            continue
        kind = agent.get("kind") or "worker"
        if kind not in AGENT_KINDS:
            kind = "worker"
        found.append({
            "ticket": number,
            "kind": kind,
            "name": agent.get("name") or "",
            "id": agent.get("id") or "",
            "status": agent.get("status") or "-",
            "cwd": agent.get("cwd") or "",
            "created": agent.get("created") or "",
            "LastUsage": agent.get("LastUsage"),
            "PendingPermissions": agent.get("PendingPermissions") or [],
        })
    return found


def worker_on(sessions_: list[dict], number: int) -> dict | None:
    for s in sessions_:
        if s["ticket"] == number and s["kind"] == "worker":
            return s
    return None


def held(rows: list[dict]) -> list[dict]:
    """The rows whose worker is a live Paseo agent of this spec."""
    return [r for r in rows if r["worker"]]

# --------------------------------------------------------------------- the rows

def build_rows(numbers: list[int], tickets: dict[int, dict],
               sessions_: list[dict]) -> list[dict]:
    """One row per ticket, joining what the tracker says to what Paseo sees."""
    rows = []
    for number in sorted(set(numbers)):
        ticket = tickets.get(number) or {"number": number, "state": "", "labels": [],
                                         "assignees": [], "blockers": [], "comments": []}
        worker = worker_on(sessions_, number)
        rows.append({
            "ticket": number,
            "worker": worker,
            "state": ticket["state"],
            "labels": ticket["labels"],
            "blockers": ticket["blockers"],
            "assignees": ticket["assignees"],
            "agent": worker["name"] if worker else "-",
            "status": worker["status"] if worker else "-",
            "agent_id": (worker["id"][:7] if worker and worker["id"] else "-"),
            "age": worker["created"] if worker and worker["created"] else "-",
            "phase": phase_of(ticket),
            "ac": counted_ac(ticket) or "-",
            "note": note_of(ticket, worker),
            "head": last_first_line(ticket),
            "created": ticket.get("created") or "",
            "closed_at": ticket.get("closed_at") or "",
        })
    return rows


def note_of(ticket: dict, worker: dict | None) -> str:
    """One short phrase saying where this ticket stands, in the pipeline's own words."""
    head = last_first_line(ticket)
    if worker:
        if worker.get("PendingPermissions"):
            return "needs permission"
        return ""
    if ticket.get("state") == "CLOSED":
        return head[:60]
    if ticket.get("blockers"):
        return "waiting on " + ", ".join(f"#{b}" for b in ticket["blockers"])
    if "needs-triage" in (ticket.get("labels") or []):
        return head[:60] or "needs-triage"
    if "ready-for-agent" in (ticket.get("labels") or []):
        return "ready"
    return head[:60]

# --------------------------------------------------------------------- the frontier

def frontier(rows: list[dict]) -> list[dict]:
    """The tickets that may be started right now, in ticket order.

    Open, in the agent queue, every blocker closed, nobody has claimed it, and no live
    worker already holds it. The last of those is what keeps a second round from
    starting a second worker on a ticket the first one is still doing.
    """
    return [r for r in rows
            if r["state"] == "OPEN"
            and "ready-for-agent" in r["labels"]
            and not r["blockers"]
            and not r["assignees"]
            and r["worker"] is None]

# --------------------------------------------------------------------- output

COLUMNS = (("ticket", 8), ("agent", 18), ("id", 8), ("agent_status", 14),
           ("age", 16), ("phase", 19), ("ac", 7), ("note", 0))


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
            "agent": row["agent"],
            "id": row["agent_id"],
            "agent_status": row["status"],
            "age": row["age"],
            "phase": row["phase"],
            "ac": row["ac"],
            "note": row["note"],
        }))
    return "\n".join(lines)


NIGHT_SUMMARY = "NIGHT SUMMARY {date}"


def night_opened(now: datetime | None = None) -> str:
    """Sixteen hours before now, the window `--summary` treats as tonight.

    The old board process used the moment it started. This program has no process
    that lives the night, so the window is a lookback long enough to cover a night
    that started in the evening and is summarised the next morning.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now.astimezone(timezone.utc) - timedelta(hours=16)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def summary(rows: list[dict], opened: str, now: datetime | None = None,
            children: list[dict] | None = None) -> str:
    """Ticket numbers and first lines. What each says is on the ticket itself."""
    now = now or datetime.now()
    closed = [f"#{r['ticket']} {r['head'][:80]}".strip()
              for r in rows if r["state"] == "CLOSED" and r["closed_at"] > opened]
    back = [f"#{r['ticket']} {r['head'][:80]}".strip()
            for r in rows if r["state"] == "OPEN" and "needs-triage" in r["labels"]]
    waiting = [f"#{r['ticket']} blocked by "
               + ", ".join(f"#{b}" for b in r["blockers"])
               for r in rows if r["state"] == "OPEN" and r["blockers"]]
    fresh = [f"#{c['number']} {last_first_line(c)[:80]}".strip()
             for c in (children or ()) if (c.get("created") or "") > opened]
    return "\n".join([
        NIGHT_SUMMARY.format(date=now.strftime("%Y-%m-%d")),
        "",
        "Closed: " + (", ".join(closed) or "None"),
        "Handed back to needs-triage: " + (", ".join(back) or "None"),
        "Not dispatched, a blocker stayed open: " + (", ".join(waiting) or "None"),
        "Sub-issues opened tonight: " + (", ".join(fresh) or "None"),
    ])

# --------------------------------------------------------------- the command forms

def collect(spec: int) -> tuple[list[dict], list[dict]]:
    """Everything one round needs: the rows, and the live sessions behind them."""
    agents = live_agents(spec)
    sessions_ = sessions(agents)
    numbers = list(sub_issues(spec))
    numbers += [s["ticket"] for s in sessions_]
    tickets = {n: read_ticket(n) for n in sorted(set(numbers))}
    return build_rows(numbers, tickets, sessions_), sessions_


def advance_plan(spec: int) -> int:
    """What the main agent's next `dispatch.sh advance` has to do, in order.

    Two kinds of line and nothing else on stdout, because a script reads this:

        MERGE <ticket>      closed with `ALL MET`, the one that closed first at the top
        DISPATCH <ticket>   on the frontier, in ticket order

    The merge order is the order the tickets closed, which is already the order their
    blockers imposed: `--preflight` refuses a ticket whose blocker is open, so none of
    them can have closed before the ones it waited on.

    Whether a branch exists and whether it is already in the base branch are git's
    questions, and git is not one of this program's two sources. `dispatch.sh` asks
    them, and skips what it finds already merged.
    """
    numbers = sub_issues(spec)
    tickets = {n: read_ticket(n) for n in numbers}
    done = [t for t in tickets.values()
            if t["state"] == "CLOSED"
            and first_line(newest_with_first_line(t, "ALL MET")).startswith("ALL MET")]
    for ticket in sorted(done, key=lambda t: t["closed_at"]):
        print(f"MERGE {ticket['number']}")
    rows = build_rows(numbers, tickets, sessions(live_agents(spec)))
    for row in frontier(rows):
        print(f"DISPATCH {row['ticket']}")
    return 0


def worker_grades(spec: int) -> int:
    """The worker-grade labels of every ticket the night could dispatch.

    One line per ticket that is `OPEN` and labelled `ready-for-agent`, blocked or not:

        GRADE <ticket> [<label> ...]

    The labels are the ticket's own ending in `-worker`, in name order, and a ticket
    carrying none prints the number alone. `dispatch.sh check` reads this before the
    night opens, and refuses the night when a label names a row `models.md` lacks or a
    ticket carries two — the same refusals a dispatch would make, brought to the one
    moment somebody is here to fix them.
    """
    for number in sub_issues(spec):
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


def children_of(numbers: list[int]) -> list[dict]:
    """Each ticket's sub-issues, in ticket order, as `read_ticket` returns them."""
    found = []
    for number in numbers:
        for child in sub_issues(number):
            found.append(read_ticket(child))
    return found


def print_summary(spec: int) -> int:
    rows, _ = collect(spec)
    children = children_of([r["ticket"] for r in rows])
    print(summary(rows, night_opened(), children=children))
    return 0

# --------------------------------------------------------------------- entry

def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="status.py",
        description="The read-only view over one spec's tickets and their agents.")
    forms = parser.add_mutually_exclusive_group(required=True)
    forms.add_argument("--table", action="store_true",
                       help="print one table and exit")
    forms.add_argument("--advance-plan", action="store_true",
                       help="print what `dispatch.sh advance` has to do, in order")
    forms.add_argument("--worker-grades", action="store_true",
                       help="print the worker-grade labels of every ticket in the agent queue")
    forms.add_argument("--summary", action="store_true",
                       help="print the night summary and do not post it")
    parser.add_argument("spec", type=int,
                        help="the spec issue whose sub-issues are tonight's tickets")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.advance_plan:
        return advance_plan(args.spec)
    if args.worker_grades:
        return worker_grades(args.spec)
    if args.summary:
        return print_summary(args.spec)
    return table(args.spec)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
