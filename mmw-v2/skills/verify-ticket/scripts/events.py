#!/usr/bin/env python3
"""The event vocabulary of the landing pipeline, and the fold that turns a ticket's
comments into its state.

    events.py emit <event> --ticket N [--spec S] --line TEXT [--text-file F]
                   [--field KEY=VALUE]... [--json-field KEY=JSON]... [--actor A] [--stage S]
    events.py fold [<issue>] [--comments-file F|-]
    events.py session [<issue>] [--kind worker|reviewer|verifier] [--comments-file F|-]
    events.py sessions [<issue>] [--comments-file F|-]
    events.py result [<issue>] --kind worker|reviewer|verifier [--comments-file F|-]

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

`fold` and the three readers after it read the issue's comments from `gh issue view
<issue> --json comments`, or from `--comments-file` (`-` for stdin) when the caller has
already fetched them: a JSON object with a `comments` list, a list of comment objects,
or a list of bodies. Exit 0 answered, 2 the comments could not be read, 3 (`session`,
`sessions`, `result`) a comment carries an event block nobody can read, named on stderr.
`result` prints the event's name and its key fields (`verifier.failed commit=… failed=AC2`),
never its prose.
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
CHILD_KINDS = ("baseline", "outside-owns", "review", "decision", "pipeline")
ABANDON_KINDS = ("decision", "failed", "stuck")

EVENTS: dict[str, dict] = {
    "spec.opened":       {"stage": "night",    "actor": "main"},
    "spec.suspended":    {"stage": "night",    "actor": "main"},
    "spec.closed":       {"stage": "night",    "actor": "main"},

    "ticket.claimed":    {"stage": "intake",   "actor": "worker"},
    "ticket.refused":    {"stage": "intake",   "actor": "worker",
                          "required": ("reason",), "closed": {"reason": REFUSALS}},
    "ticket.passed":     {"stage": "close",    "actor": "worker"},
    "ticket.returned":   {"stage": "close",    "actor": "worker"},
    "ticket.released":   {"stage": "land",     "actor": "main",
                          "required": ("reason",), "closed": {"reason": RELEASE_REASONS}},
    "ticket.landed":     {"stage": "land",     "actor": "main"},
    "ticket.regressed":  {"stage": "regress",  "actor": "main", "required": ("commit",)},

    # Everything the ticket says about where its worker runs, so every later command and
    # every machine finds it there. `effort` is written `—` when the host takes none; the
    # worktree is an absolute path, since no runner is asked to find it.
    "worker.started":    {"stage": "dispatch", "actor": "main",
                          "required": ("session", "runner", "host", "model", "effort",
                                       "grade", "worktree", "branch", "base"),
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
    # The one event not written by the agent it is about: a dead agent cannot write its
    # own obituary. Which script writes it, and when, belongs to the liveness judge.
    "worker.lost":       {"stage": "work",     "actor": "judge",
                          "required": ("session", "runner")},

    "reviewer.started":  {"stage": "review",   "actor": "worker",
                          "required": ("session", "runner"),
                          "patterns": {"worktree": r"/.*"}},
    "reviewer.reported": {"stage": "review",   "actor": "reviewer"},

    "verifier.started":  {"stage": "verify",   "actor": "worker",
                          "required": ("session", "runner"),
                          "patterns": {"worktree": r"/.*"}},
    # A verdict covers one commit, written in full: a ticket closes on it being the
    # commit at HEAD, and two commits share a short prefix often enough to pass a draft
    # against a verdict on neither of them.
    "verifier.passed":   {"stage": "verify",   "actor": "verifier", "required": ("commit",),
                          "patterns": {"commit": r"[0-9a-f]{40}"}},
    "verifier.failed":   {"stage": "verify",   "actor": "verifier", "required": ("commit",),
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
# also ends a claim no started session has taken over, since it gives the claim back.
ENDS_ONE_HOLD = ("worker.retracted", "worker.lost", "worker.replaced")

# The fields `result` prints after an event's name.
RESULT_FIELDS = {
    "ticket.passed": ("commit",),
    "ticket.returned": (),
    "reviewer.reported": ("base", "head"),
    "verifier.passed": ("commit",),
    "verifier.failed": ("commit", "failed", "ran"),
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
            "slot": payload.get("slot"),
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
    elif name == "child.opened":
        child = payload.get("child")
        state["children"].setdefault(str(child), {"child": child}).update(
            kind=payload.get("kind"), title=payload.get("title"))
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


def sessions_of(state: dict) -> list[tuple[str, str]]:
    """Every (runner, session) pair the issue names, once each, oldest first."""
    seen: list[tuple[str, str]] = []
    for record in state["sessions"]:
        pair = (record.get("runner") or "", record.get("session") or "")
        if pair[1] and pair not in seen:
            seen.append(pair)
    return seen


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

    for name in ("fold", "session", "sessions", "result"):
        reader = sub.add_parser(name)
        reader.add_argument("issue", nargs="?", type=int)
        reader.add_argument("--comments-file")
        if name in ("session", "result"):
            reader.add_argument("--kind", choices=AGENT_KINDS, required=(name == "result"))

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
    record = state["results"].get(args.kind)
    if record:
        print(describe(record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
