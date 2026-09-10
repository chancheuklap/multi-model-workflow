#!/usr/bin/env python3
"""The event vocabulary of the landing pipeline, and the fold that turns a ticket's
comments into its state.

    events.py emit <event> --ticket N [--spec S] --line TEXT [--text-file F]
                   [--field KEY=VALUE]... [--json-field KEY=JSON]... [--actor A] [--stage S]
    events.py fold [<issue>] [--comments-file F|-]
    events.py session [<issue>] [--kind worker|reviewer|verifier] [--comments-file F|-]
    events.py sessions [<issue>] [--comments-file F|-]
    events.py result [<issue>] --kind worker|reviewer|verifier [--comments-file F|-]
    events.py checked [<issue>] [--run self|reverify|repo-checks] [--comments-file F|-]
    events.py live [<issue>] [--kind worker|reviewer|verifier] [--comments-file F|-]
    events.py child [<issue>] --child N [--comments-file F|-]

A ticket's state is stored nowhere. It is computed: every comment on the issue is read in
comment-id order, the events they carry are replayed from an empty state, and what comes
out is the state. The replay starts from empty every time and never updates a state it
computed before, because state goes backwards — a regression reopens a ticket, a
suspended night gives claims back, a retracted start is undone — and replaying needs no
inverse for any of them.

One event is one comment, in two parts:

    <first line: prose for a person, worded however its writer likes>
    <anything else a person should read>

    <!-- mmw {"v":1,"event":"ticket.passed","stage":"close","actor":"worker",...} -->

The trailing HTML comment is invisible on GitHub and is the whole of what a program
reads. The first line is never read by a program: rewording it breaks nothing. Every
event is written by a script — `verify-ticket.py` or `dispatch.sh` through `emit` — and
never typed by a model.

A comment that carries a block this module cannot read is not treated as absent: the
fold lists it under `unreadable`, and every caller that decides something from the fold
refuses to decide while that list is not empty (`docs/adr/0008-silence-is-never-a-pass.md`).

Ordering is by comment id, which GitHub hands out in increasing order; the timestamp is
not used, because two comments written in the same second carry the same one. A caller
that has no ids (a test fixture, a list of bodies) is replayed in the order given.

`fold` and the readers after it read the issue's comments from `gh issue view
<issue> --json comments`, or from `--comments-file` (`-` for stdin) when the caller has
already fetched them: a JSON object with a `comments` list, a list of comment objects,
or a list of bodies. Exit 0 answered, 2 the comments could not be read, 3 (every reader
but `fold`) a comment carries an event block nobody can read, named on stderr.
`result` prints the event's name and its key fields (`verifier.failed commit=… failed=AC2`),
never its prose. `checked` prints the newest `ticket.checked` the same way, of one run
when `--run` names it. `live` prints "runner<TAB>session" for every session of that kind
whose hold no event has ended, oldest first. `child` prints, for a child this issue's
`child.opened` names, "kind<TAB>spec<TAB>resolution<TAB>became" (`-` for none yet), and
nothing when no `child.opened` on this issue names it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
MARK = "mmw"

# ------------------------------------------------------------------ the vocabulary

# Every event of the pipeline: its stage, the role that writes it, the fields its payload
# must carry, and the fields whose value is one of a closed set. Names are
# `subject.verb`: a subject from SUBJECTS, a verb in the past tense, lower case, ASCII,
# no value ever inside the name — ticket numbers, commits, hosts and models are fields.
SUBJECTS = ("spec", "ticket", "worker", "reviewer", "verifier", "child")

AGENT_KINDS = ("worker", "reviewer", "verifier")

# The six refusals of `verify-ticket.py --preflight`, in the order it checks them.
REFUSALS = ("wrong-branch", "dirty-tree", "not-open", "not-ready", "blocked", "claimed-by-other")
RELEASE_REASONS = ("landed", "suspended", "worker-lost")
CHILD_RESOLUTIONS = ("fixed", "stale", "became-ticket")
# The five kinds of child, named for who can answer each: `finding`, a reviewer's defect
# outside the ticket's scope; `contract`, a baseline the ticket was told to follow that
# does not hold; `deferred`, work outside `## Owns` left for a later ticket; `decision`, a
# choice only a person can make; `fault`, the pipeline itself broken.
CHILD_KINDS = ("finding", "contract", "deferred", "decision", "fault")
ABANDON_KINDS = ("decision", "failed", "stuck")
# The three runs of a ticket's criteria and checks: the worker's own run, a second run of
# every criterion (the verifier's, or the main agent's on the base branch after landing),
# and the repository's own `checks` of `.mmw/target.json` at the closeout.
CHECK_RUNS = ("self", "reverify", "repo-checks")
CHECK_RESULTS = ("met", "unmet", "handoff")
# Why a run waits for a product slot: this product's `instance.max` is reached, or every
# slot of this machine is taken.
QUEUE_REASONS = ("product-full", "machine-full")

EVENTS: dict[str, dict] = {
    "spec.opened":       {"stage": "night",    "actor": "main"},
    "spec.suspended":    {"stage": "night",    "actor": "main"},
    "spec.closed":       {"stage": "night",    "actor": "main"},

    "ticket.claimed":    {"stage": "intake",   "actor": "worker"},
    # The session that refused is named when it could name itself, so its own hold ends
    # and the ticket is free for the next start; nobody else's hold is touched.
    "ticket.refused":    {"stage": "intake",   "actor": "worker",
                          "required": ("reason",), "closed": {"reason": REFUSALS},
                          "together": (("session", "runner"),)},
    "ticket.passed":     {"stage": "close",    "actor": "worker"},
    "ticket.returned":   {"stage": "close",    "actor": "worker"},
    "ticket.released":   {"stage": "land",     "actor": "main",
                          "required": ("reason",), "closed": {"reason": RELEASE_REASONS}},
    "ticket.landed":     {"stage": "land",     "actor": "main"},
    "ticket.regressed":  {"stage": "regress",  "actor": "main", "required": ("commit",)},

    # Everything the ticket says about where its worker runs, so every later command and
    # every machine finds it there. `effort` is written `—` when the host takes none; the
    # worktree is an absolute path, since no runner is asked to find it. `machine` is the
    # hostname of the machine the session was started on: a runner answers for its own
    # machine only, so only that machine may ask it whether the session is alive.
    "worker.started":    {"stage": "dispatch", "actor": "main",
                          "required": ("session", "runner", "machine", "host", "model",
                                       "effort", "grade", "worktree", "branch", "base"),
                          "patterns": {"worktree": r"/.*"}},
    "worker.resumed":    {"stage": "work",     "actor": "main",
                          "together": (("session", "runner"),)},
    "worker.retracted":  {"stage": "dispatch", "actor": "main",
                          "together": (("session", "runner"),)},
    # The session this names is the one replaced; the one replacing it is always a
    # `worker.started` of its own that follows.
    "worker.replaced":   {"stage": "dispatch", "actor": "main",
                          "required": ("session", "runner")},
    "worker.decided":    {"stage": "work",     "actor": "worker"},
    # A run of the criteria needed the product and no slot was free, so it waits for one:
    # the one state in which a worker is neither dead nor done. It ends at the next
    # `ticket.checked`, which names the slot the run got, or at any event that ends the
    # worker's hold.
    "worker.queued":     {"stage": "work",     "actor": "worker",
                          "required": ("reason", "run"),
                          "closed": {"reason": QUEUE_REASONS, "run": CHECK_RUNS}},
    # Files ticket `by` changed that this ticket's `## Owns` covers, posted on this ticket
    # so the worker that owns them reads what another ticket did to them.
    "worker.touched":    {"stage": "work",     "actor": "worker",
                          "required": ("by", "files")},
    # The three `*.lost` events are the only ones not written by the agent they are about:
    # a dead agent cannot write its own obituary. The liveness judge writes them, once the
    # session's own runner says it has stopped (the dispatch skill's watchdog.py).
    "worker.lost":       {"stage": "work",     "actor": "judge",
                          "required": ("session", "runner")},

    "reviewer.started":  {"stage": "review",   "actor": "worker",
                          "required": ("session", "runner", "machine"),
                          "patterns": {"worktree": r"/.*"}},
    "reviewer.reported": {"stage": "review",   "actor": "reviewer"},
    # A reviewer whose session stopped with no `reviewer.reported` after its start.
    "reviewer.lost":     {"stage": "review",   "actor": "judge",
                          "required": ("session", "runner")},

    "verifier.started":  {"stage": "verify",   "actor": "worker",
                          "required": ("session", "runner", "machine"),
                          "patterns": {"worktree": r"/.*"}},
    # A verdict covers one commit, written in full: a ticket closes on it being the
    # commit at HEAD, and two commits share a short prefix often enough to pass a draft
    # against a verdict on neither of them.
    "verifier.passed":   {"stage": "verify",   "actor": "verifier", "required": ("commit",),
                          "patterns": {"commit": r"[0-9a-f]{40}"}},
    "verifier.failed":   {"stage": "verify",   "actor": "verifier", "required": ("commit",),
                          "patterns": {"commit": r"[0-9a-f]{40}"}},
    # A verifier whose session stopped with no verdict after its start.
    "verifier.lost":     {"stage": "verify",   "actor": "judge",
                          "required": ("session", "runner")},

    # One run of the criteria or of the repository's checks, on one commit: its result,
    # its counts, each criterion's outcome, and — for the worker's own run on its own
    # branch — the files it changed outside `## Owns`. `repo-checks` carries each failed
    # command with its last lines. `slot` is the product slot the run held, when it
    # needed the product.
    "ticket.checked":    {"stage": "work",     "actor": "worker",
                          "required": ("run", "commit", "result"),
                          "closed": {"run": CHECK_RUNS, "result": CHECK_RESULTS},
                          "patterns": {"commit": r"[0-9a-f]{40}"}},

    "child.opened":      {"stage": "work",     "actor": "worker",
                          "required": ("child", "kind"), "closed": {"kind": CHILD_KINDS}},
    "child.closed":      {"stage": "close",    "actor": "main",
                          "required": ("child", "resolution"),
                          "closed": {"resolution": CHILD_RESOLUTIONS}},
}

COMMON = ("v", "event", "stage", "actor", "spec", "ticket", "at")

# A ticket is held from a `ticket.claimed` or any `*.started` until an event ends that
# hold. These end every hold on the ticket. `ticket.passed` ends none: until the ticket
# lands its worker may still be at work on it — a close that failed after the pass leaves
# the ticket open and the worker retrying. Labels never end a hold.
ENDS_EVERY_HOLD = ("ticket.landed", "ticket.returned", "ticket.released", "spec.suspended")
# These end the hold of the one session they name, matched by its (runner, session)
# pair and never by the id alone: two runners can hand out the same id. A retraction
# also ends a claim no started session has taken over, since it gives the claim back. A
# refusal ends the hold of the session that refused to claim, which does nothing more on
# the ticket; a refusal that names no session ends nothing.
ENDS_ONE_HOLD = ("worker.retracted", "worker.lost", "worker.replaced", "ticket.refused",
                 "reviewer.lost", "verifier.lost")
# A reviewer or verifier has done its work once its result is on the ticket, so its
# result ends its own hold: the session it names when it names one, else the newest live
# session of that kind — the one that was started to produce it. A finished reviewer that
# went on holding the ticket would keep it off the frontier after its worker is gone.
ENDS_OWN_HOLD = {"reviewer.reported": "reviewer", "verifier.passed": "verifier",
                 "verifier.failed": "verifier"}
# A worktree's product slot is held until its ticket's work ends, and given back at that
# moment: it lands, it is handed back, its claim is released, the night is suspended, or
# its start is retracted. A replaced or lost worker's worktree keeps its slot for the
# worker that carries on in it.
SLOT_ENDS = ("ticket.landed", "ticket.returned", "ticket.released", "spec.suspended",
             "worker.retracted")

# The fields `result` and `checked` print after an event's name.
RESULT_FIELDS = {
    "ticket.passed": ("commit",),
    "ticket.returned": (),
    "reviewer.reported": ("base", "head"),
    "verifier.passed": ("commit",),
    "verifier.failed": ("commit", "failed", "ran"),
    "ticket.checked": ("run", "commit", "result", "failed"),
}

# The result each kind of agent is started to produce.
RESULTS = {
    "worker": ("ticket.passed", "ticket.returned"),
    "reviewer": ("reviewer.reported",),
    "verifier": ("verifier.passed", "verifier.failed"),
}

BLOCK_RE = re.compile(r"<!--\s*" + MARK + r"\b(.*?)-->", re.S)
OPENER_RE = re.compile(r"<!--\s*" + MARK + r"\b")
COMMENT_ID_RE = re.compile(r"#issuecomment-(\d+)")


class EventError(ValueError):
    """An event that cannot be written: unknown name, or a payload the table refuses."""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check(event: str, payload: dict) -> str | None:
    """Why this payload is not a valid `event`, or None."""
    spec = EVENTS.get(event)
    if spec is None:
        return f"`{event}` is not an event of this pipeline"
    for key in spec.get("required", ()):
        if payload.get(key) in (None, ""):
            return f"`{event}` carries no `{key}`"
    for key, allowed in (spec.get("closed") or {}).items():
        value = payload.get(key)
        if value not in (None, "") and value not in allowed:
            return f"`{event}` has {key} `{value}`, which is not one of {', '.join(allowed)}"
    for key, pattern in (spec.get("patterns") or {}).items():
        value = payload.get(key)
        if value not in (None, "") and not re.fullmatch(pattern, str(value)):
            return f"`{event}` has {key} `{value}`, which is not the shape {pattern}"
    for group in spec.get("together") or ():
        given = [key for key in group if payload.get(key) not in (None, "")]
        if given and len(given) != len(group):
            missing = [key for key in group if key not in given]
            return (f"`{event}` names {', '.join(given)} without {', '.join(missing)}; "
                    f"they are one thing and come together")
    return None


# ------------------------------------------------------------------ writing

def block(payload: dict) -> str:
    """The trailing `<!-- mmw {...} -->` line for one payload.

    One line of JSON. `>` is written as `\\u003e` so no string inside it can close the
    HTML comment early; JSON reads the escape back as the same character.
    """
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"<!-- {MARK} " + text.replace(">", "\\u003e") + " -->"


def neutralise(prose: str) -> str:
    """`prose` with every `<!-- mmw` opener made visible text.

    A report that quotes an event — a review of this very code, a criterion's output —
    would otherwise carry a second block, and its ticket would read as holding an event
    nobody wrote. `&lt;!--` renders as `<!--` for a person and opens nothing.
    """
    return OPENER_RE.sub(lambda m: "&lt;!--" + m.group(0)[4:], prose or "")


def build(event: str, *, ticket: int | None, line: str, text: str = "",
          spec: int | None = None, actor: str | None = None, stage: str | None = None,
          at: str | None = None, **fields) -> str:
    """One comment body: the prose line, the rest of the prose, then the block.

    `ticket` is the ticket the event is about (None for an event about a whole spec),
    and `spec` the spec it sits under when the writer knows it. Fields whose value is
    None are left out. Raises EventError for an event or payload the table refuses.
    The prose is passed through `neutralise`, so the only block is the event's own.
    """
    table = EVENTS.get(event)
    if table is None:
        raise EventError(f"`{event}` is not an event of this pipeline")
    first = neutralise(line).strip().splitlines()
    if not first or not first[0].strip():
        raise EventError(f"`{event}` needs a first line a person can read")
    payload = {
        "v": VERSION,
        "event": event,
        "stage": stage or table["stage"],
        "actor": actor or table["actor"],
        "spec": spec,
        "ticket": ticket,
        "at": at or now(),
    }
    for key, value in fields.items():
        if key in COMMON:
            raise EventError(f"`{key}` is a common field, not a field of `{event}`")
        if value is not None and value != "":
            payload[key] = value
    problem = _check(event, payload)
    if problem:
        raise EventError(problem)
    parts = [first[0].strip()]
    rest = "\n".join(first[1:]).strip("\n")
    if rest:
        parts.append(rest)
    if text and text.strip():
        parts += ["", neutralise(text).strip("\n")]
    return "\n".join(parts) + "\n\n" + block(payload) + "\n"


# ------------------------------------------------------------------ reading one comment

def first_line(body: str) -> str:
    stripped = (body or "").strip()
    return stripped.splitlines()[0].strip() if stripped else ""


def parse(body: str) -> tuple[str, dict | str | None]:
    """What one comment body carries.

        ("event", payload)       one readable block
        ("none", None)           no block at all: prose, not an event
        ("unreadable", reason)   a block, or the start of one, that cannot be read
    """
    text = body or ""
    if not OPENER_RE.search(text):
        return "none", None
    found = BLOCK_RE.findall(text)
    if not found:
        return "unreadable", f"an `<!-- {MARK}` block that is never closed"
    if len(OPENER_RE.findall(text)) != len(found) or len(found) > 1:
        return "unreadable", (f"{len(OPENER_RE.findall(text))} `<!-- {MARK}` blocks in one "
                              f"comment; one comment is one event")
    raw = found[0].strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return "unreadable", f"the block is not JSON ({exc.msg} at column {exc.colno})"
    if not isinstance(payload, dict):
        return "unreadable", "the block is JSON but not an object"
    if payload.get("v") != VERSION:
        return "unreadable", (f"the block is version {payload.get('v')!r}, and this reader "
                              f"reads version {VERSION}")
    event = payload.get("event")
    if not isinstance(event, str):
        return "unreadable", "the block names no event"
    problem = _check(event, payload)
    if problem:
        return "unreadable", problem
    return "event", payload


# ------------------------------------------------------------------ the fold

def normalise(comments) -> list[dict]:
    """Comments as `{"id", "body", "position"}`, in replay order.

    Accepts comment objects (`gh issue view --json comments`, REST, or a fixture) and bare
    bodies. The id is the numeric comment id: `databaseId`, a numeric `id`, or the number
    in the comment's `#issuecomment-<id>` URL. When every comment has one, the order is
    by id; otherwise the order given. A comment is edited in place, so one id handed in
    twice — a later page, an incremental read — is the version with the newest
    `updated_at`.
    """
    out = []
    for position, item in enumerate(comments or [], start=1):
        if isinstance(item, str):
            out.append({"id": None, "body": item, "position": position})
            continue
        if not isinstance(item, dict):
            continue
        ident = item.get("databaseId")
        if not isinstance(ident, int):
            ident = item.get("id") if isinstance(item.get("id"), int) else None
        if ident is None:
            found = COMMENT_ID_RE.search(str(item.get("url") or item.get("html_url") or ""))
            ident = int(found.group(1)) if found else None
        updated = str(item.get("updated_at") or item.get("updatedAt")
                      or item.get("lastEditedAt") or item.get("created_at")
                      or item.get("createdAt") or "")
        out.append({"id": ident, "body": item.get("body") or "", "position": position,
                    "updated": updated})
    newest: dict[int, dict] = {}
    for comment in out:
        if comment["id"] is None:
            continue
        held = newest.get(comment["id"])
        if held is None or comment["updated"] >= held["updated"]:
            newest[comment["id"]] = comment
    out = [c for c in out if c["id"] is None or newest[c["id"]] is c]
    if out and all(c["id"] is not None for c in out):
        out.sort(key=lambda c: c["id"])
    return out


def empty_state(issue: int | None = None) -> dict:
    return {
        "issue": issue,
        "events": [],
        "last": None,
        "unreadable": [],
        "claimed": False,
        "claimant": None,
        "refused": None,
        "passed": False,
        "returned": False,
        "outcome": None,
        "landed": False,
        "released": None,
        "regressed": False,
        "suspended": False,
        "review": None,
        "verdict": None,
        "decided": 0,
        "results": {kind: None for kind in AGENT_KINDS},
        # The newest `ticket.checked` of each run.
        "checks": {run: None for run in CHECK_RUNS},
        # The `worker.queued` a run is still waiting under, or None.
        "waiting": None,
        # The product slot the newest run held, until an event in `SLOT_ENDS` gives it back.
        "slot": None,
        "touched": [],
        "children": {},
        "sessions": [],
        "claim_hold": False,
        "ever_held": False,
        "spec_opened": False,
        "spec_closed": False,
    }


def _summary(comment: dict, payload: dict) -> dict:
    return {
        "comment": comment["id"] if comment["id"] is not None else comment["position"],
        "event": payload["event"],
        "at": payload.get("at"),
        "actor": payload.get("actor"),
        "line": first_line(comment["body"]),
        "body": comment["body"],
        "payload": payload,
    }


def _end(state: dict, by: str, pair: tuple | None = None) -> None:
    """End the hold of the session `pair` names, or of every session when it is None."""
    for record in state["sessions"]:
        if not record["live"]:
            continue
        if pair is not None and (record["runner"], record["session"]) != pair:
            continue
        record["live"] = False
        record["ended_by"] = by


def apply(state: dict, event: dict) -> None:
    """Replay one event onto `state`. `event` is a `_summary` record."""
    name = event["event"]
    payload = event["payload"]
    kind, _, verb = name.partition(".")

    if verb == "started" and kind in AGENT_KINDS:
        state["sessions"].append({
            "kind": kind,
            "session": payload.get("session"),
            "runner": payload.get("runner"),
            "host": payload.get("host"),
            "model": payload.get("model"),
            "effort": payload.get("effort"),
            "grade": payload.get("grade"),
            "worktree": payload.get("worktree"),
            "branch": payload.get("branch"),
            "base": payload.get("base"),
            "machine": payload.get("machine"),
            "started_at": payload.get("at"),
            "comment": event["comment"],
            "live": True,
            "ended_by": None,
        })
        # A claim made before its session's start was recorded is that session's.
        state.update(claim_hold=False, ever_held=True)
        if kind == "worker":
            state["suspended"] = False
    elif name == "worker.resumed":
        workers = [r for r in state["sessions"] if r["kind"] == "worker"]
        wanted = (payload.get("runner"), payload.get("session"))
        target = next((r for r in reversed(workers)
                       if (r["runner"], r["session"]) == wanted), None) \
            if wanted[1] else (workers[-1] if workers else None)
        if target is not None:
            target["live"] = True
            target["ended_by"] = None
            state["ever_held"] = True
    elif name == "ticket.claimed":
        state["claimed"] = True
        state["claimant"] = payload.get("login")
        if not any(r["live"] for r in state["sessions"]):
            state["claim_hold"] = True
        state["ever_held"] = True
    elif name == "ticket.refused":
        state["refused"] = {"reason": payload.get("reason"), "line": event["line"]}
    elif name == "ticket.passed":
        # A pass after a landing is new work, and it has not landed yet.
        state.update(passed=True, landed=False, returned=False, claimed=False,
                     outcome=event)
    elif name == "ticket.returned":
        state.update(passed=False, returned=True, claimed=False, outcome=event)
    elif name == "ticket.released":
        state["claimed"] = False
        state["released"] = payload.get("reason")
    elif name == "ticket.landed":
        state["landed"] = True
    elif name == "ticket.regressed":
        state.update(passed=False, landed=False, regressed=True, outcome=None)
    elif name == "spec.suspended":
        state["suspended"] = True
    elif name == "spec.opened":
        state["spec_opened"] = True
    elif name == "spec.closed":
        state["spec_closed"] = True
    elif name == "reviewer.reported":
        state["review"] = event
    elif name in ("verifier.passed", "verifier.failed"):
        state["verdict"] = event
    elif name == "worker.decided":
        state["decided"] += 1
    elif name == "worker.queued":
        state["waiting"] = event
    elif name == "ticket.checked":
        state["checks"][payload.get("run")] = event
        state["waiting"] = None
        if payload.get("slot") is not None:
            state["slot"] = payload.get("slot")
    elif name == "worker.touched":
        state["touched"].append({"by": payload.get("by"), "files": payload.get("files"),
                                 "comment": event["comment"]})
    elif name == "child.opened":
        child = payload.get("child")
        state["children"].setdefault(str(child), {"child": child}).update(
            kind=payload.get("kind"), title=payload.get("title"), opened=True,
            spec=payload.get("spec"))
    elif name == "child.closed":
        child = payload.get("child")
        state["children"].setdefault(str(child), {"child": child}).update(
            resolution=payload.get("resolution"), ticket=payload.get("became"))

    if name in ENDS_EVERY_HOLD:
        _end(state, name)
        state["claim_hold"] = False
    elif name in ENDS_ONE_HOLD:
        if payload.get("session"):
            _end(state, name, (payload.get("runner"), payload.get("session")))
        if name == "worker.retracted":
            state["claim_hold"] = False
    if name in ENDS_OWN_HOLD:
        if payload.get("session"):
            _end(state, name, (payload.get("runner"), payload.get("session")))
        else:
            mine = [r for r in state["sessions"]
                    if r["kind"] == ENDS_OWN_HOLD[name] and r["live"]]
            if mine:
                _end(state, name, (mine[-1]["runner"], mine[-1]["session"]))
    # A run waits only while a worker is at work on the ticket: whatever ends a worker's
    # hold, or the worker's own result, ends the wait with it. A lost reviewer or verifier
    # ends only its own hold; the worker's run is still waiting.
    if name in ENDS_EVERY_HOLD or name in RESULTS["worker"] \
            or (name in ENDS_ONE_HOLD and name not in ("reviewer.lost", "verifier.lost")):
        state["waiting"] = None
    if name in SLOT_ENDS:
        state["slot"] = None
    for agent_kind, names in RESULTS.items():
        if name in names:
            state["results"][agent_kind] = event


def _records(comments):
    """Each comment in replay order, read: ("event", record) or ("unreadable", item).

    A comment with no block is prose and yields nothing, whatever its first line says.
    """
    for comment in normalise(comments):
        what, value = parse(comment["body"])
        if what == "event":
            yield "event", _summary(comment, value)
        elif what == "unreadable":
            yield "unreadable", {
                "comment": comment["id"] if comment["id"] is not None else comment["position"],
                "line": first_line(comment["body"]),
                "reason": value,
            }


def fold(comments, issue: int | None = None) -> dict:
    """The state of one issue: every event on it replayed, from empty, in id order."""
    state = empty_state(issue)
    for what, record in _records(comments):
        if what == "unreadable":
            state["unreadable"].append(record)
            continue
        state["events"].append({k: record[k] for k in
                                ("comment", "event", "at", "actor", "line")})
        state["last"] = record
        apply(state, record)

    workers = [r for r in state["sessions"] if r["kind"] == "worker"]
    state["worker"] = workers[-1] if workers else None
    state["live_workers"] = [r for r in workers if r["live"]]
    state["holders"] = [r for r in state["sessions"] if r["live"]]
    state["held"] = bool(state["holders"]) or state["claim_hold"]
    # Only a hold that an event ended says the ticket's claim is nobody's any more.
    state["hold_ended"] = state["ever_held"] and not state["held"]
    return state


def describe(record: dict) -> str:
    """An event as `result` prints it: its name, then its key fields."""
    payload = record["payload"]
    parts = [record["event"]]
    for key in RESULT_FIELDS.get(record["event"], ()):
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            value = ",".join(str(v) for v in value) or "-"
        elif isinstance(value, bool):
            value = "true" if value else "false"
        parts.append(f"{key}={value}")
    return " ".join(parts)


def newest(comments, *names: str) -> dict | None:
    """The newest event among `names` on these comments, body and payload included."""
    found = None
    for what, record in _records(comments):
        if what == "event" and record["event"] in names:
            found = record
    return found


def session_of(state: dict, kind: str | None = None) -> dict | None:
    """The newest session of `kind` (any kind when None) the issue names."""
    found = [r for r in state["sessions"] if kind is None or r["kind"] == kind]
    return found[-1] if found else None


def checked_of(state: dict, run: str | None = None) -> dict | None:
    """The newest `ticket.checked` of `run`, or of any run when None."""
    if run is not None:
        return state["checks"].get(run)
    found = [record for record in state["checks"].values() if record]
    return max(found, key=_order) if found else None


def _order(record: dict):
    comment = record.get("comment")
    return comment if isinstance(comment, int) else 0


def live_of(state: dict, kind: str | None = None) -> list[dict]:
    """Every session of `kind` (any kind when None) whose hold no event has ended."""
    return [r for r in state["sessions"]
            if r["live"] and (kind is None or r["kind"] == kind)]


def sessions_of(state: dict) -> list[tuple[str, str]]:
    """Every (runner, session) pair the issue names, once each, oldest first."""
    seen: list[tuple[str, str]] = []
    for record in state["sessions"]:
        pair = (record.get("runner") or "", record.get("session") or "")
        if pair[1] and pair not in seen:
            seen.append(pair)
    return seen


def blocker_hold(state: str, fold: dict | None) -> str:
    """Why a blocker still holds back the ticket it blocks, or empty when it has let go.

    `state` is the blocker's state on the tracker, `fold` its own events folded, or None
    when the tracker did not answer for them. A blocker lets go when its work is on the
    base branch, not when it closes: the ticket it blocks is cut from the base branch and
    has to find that work there. The signal is `ticket.landed`. A blocker closed without
    a pass — by a person, or as not planned — has nothing that will ever land, and lets go
    on closing. A closed blocker whose events cannot be read has not said which of the
    two it is, so it holds.
    """
    if state != "CLOSED":
        return "open"
    if fold is None:
        return "the tracker did not answer for it"
    if fold["unreadable"]:
        return "its events cannot be read"
    if fold["passed"] and not fold["landed"]:
        return "passed, not landed"
    return ""


# ------------------------------------------------------------------ command line

GH_ENV = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR_FORCE", "CLICOLOR")}


class Unreadable(RuntimeError):
    """The issue's comments could not be read."""


def read_comments(issue: int | None, source: str | None) -> list:
    if source:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    else:
        if issue is None:
            raise Unreadable("an issue number or --comments-file is needed")
        run = subprocess.run(["gh", "issue", "view", str(issue), "--json", "comments"],
                             capture_output=True, text=True, env=GH_ENV)
        if run.returncode != 0:
            detail = (run.stderr or run.stdout).strip().splitlines()
            raise Unreadable(f"`gh issue view {issue} --json comments` failed"
                             + (f": {detail[-1]}" if detail else ""))
        text = run.stdout
    try:
        data = json.loads(text) if text.strip() else None
    except json.JSONDecodeError as exc:
        raise Unreadable(f"the comments of #{issue} are not JSON: {exc.msg}") from None
    if isinstance(data, dict) and isinstance(data.get("comments"), list):
        return data["comments"]
    if isinstance(data, list):
        return data
    raise Unreadable(f"the comments of #{issue} came back in no shape this reads")


def refuse_unreadable(state: dict, issue: int | None) -> bool:
    """Name every unreadable comment on stderr; True when there was one."""
    for item in state["unreadable"]:
        sys.stderr.write(f"events: #{issue if issue is not None else '?'} comment "
                         f"{item['comment']} ({item['line'][:60]}): {item['reason']}; "
                         f"nothing is answered about this ticket until that comment is "
                         f"fixed\n")
    return bool(state["unreadable"])


def _fields(pairs: list[str], typed: bool) -> dict:
    out = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise EventError(f"`{pair}` is not KEY=VALUE")
        if typed:
            try:
                out[key] = json.loads(value)
            except json.JSONDecodeError:
                raise EventError(f"`{pair}`: the value is not JSON") from None
        else:
            out[key] = value if value != "" else None
    return out


def _number(text: str | None) -> int | None:
    if text in (None, ""):
        return None
    try:
        return int(text)
    except ValueError:
        raise EventError(f"`{text}` is not an issue number") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="events.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    emit = sub.add_parser("emit", help="print one event comment body")
    emit.add_argument("event")
    emit.add_argument("--ticket", default="")
    emit.add_argument("--spec", default="")
    emit.add_argument("--line", required=True)
    emit.add_argument("--text-file")
    emit.add_argument("--field", action="append", default=[])
    emit.add_argument("--json-field", action="append", default=[])
    emit.add_argument("--actor")
    emit.add_argument("--stage")

    for name in ("fold", "session", "sessions", "result", "checked", "live", "child"):
        reader = sub.add_parser(name)
        reader.add_argument("issue", nargs="?", type=int)
        reader.add_argument("--comments-file")
        if name in ("session", "result", "live"):
            reader.add_argument("--kind", choices=AGENT_KINDS, required=(name == "result"))
        if name == "checked":
            reader.add_argument("--run", choices=CHECK_RUNS)
        if name == "child":
            reader.add_argument("--child", type=int, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "emit":
            text = Path(args.text_file).read_text(encoding="utf-8") if args.text_file else ""
            fields = _fields(args.field, typed=False)
            fields.update(_fields(args.json_field, typed=True))
            sys.stdout.write(build(args.event, ticket=_number(args.ticket),
                                   spec=_number(args.spec), line=args.line, text=text,
                                   actor=args.actor, stage=args.stage, **fields))
            return 0
        state = fold(read_comments(args.issue, args.comments_file), issue=args.issue)
    except EventError as exc:
        sys.stderr.write(f"events: {exc}\n")
        return 2
    except (Unreadable, OSError) as exc:
        sys.stderr.write(f"events: {exc}\n")
        return 2

    if args.command == "fold":
        print(json.dumps(state, ensure_ascii=False, indent=2, default=str))
        return 0
    # A ticket with an event nobody can read has no answer: any one given would be read
    # as the whole truth by a caller about to archive, send or wait.
    if refuse_unreadable(state, args.issue):
        return 3
    if args.command == "session":
        record = session_of(state, args.kind)
        if record and record.get("session"):
            print(f"{record.get('runner') or ''}\t{record['session']}")
        return 0
    if args.command == "sessions":
        for runner, session in sessions_of(state):
            print(f"{runner}\t{session}")
        return 0
    if args.command == "live":
        for record in live_of(state, args.kind):
            if record.get("session"):
                print(f"{record.get('runner') or ''}\t{record['session']}")
        return 0
    if args.command == "checked":
        record = checked_of(state, args.run)
        if record:
            print(describe(record))
        return 0
    if args.command == "child":
        entry = state["children"].get(str(args.child)) or {}
        if entry.get("opened"):
            print("\t".join("-" if entry.get(key) in (None, "") else str(entry[key])
                            for key in ("kind", "spec", "resolution", "ticket")))
        return 0
    record = state["results"].get(args.kind)
    if record:
        print(describe(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
