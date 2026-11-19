#!/usr/bin/env python3
"""Briefs: the record of sessions `dispatch.sh brief` starts without a ticket, and their results.

    briefs.py new --repo O/R --role ROLE --count N --runner R --session S
    briefs.py started --repo O/R --brief B/N --runner R --session S --host H --model M --effort E
    briefs.py forget --repo O/R --batch B
    briefs.py report --repo O/R --brief B/N --file F --runner R --session S
    briefs.py show --repo O/R --batch B

A worker hands its result back on its ticket, and the relay reads the ticket. An advisor, a
researcher, an explainer or a synthesizer has no ticket: it answers one session, the one
that briefed it. Its result is written here, in this machine's state directory for the
repository (statedir.py), never in the repository and never on the tracker.

**A batch** is what one `dispatch.sh brief <role> <file>...` call starts: one session per
brief file, all of one role, all answering one parent session. The relay keeps a watch on
the batch (`briefs:<batch>`, relay.py) with the parent as its orchestrator, and queues one
wake, `brief <batch> done`, once every brief in it has reported or is lost. One wake per
batch, not one per brief: a runner that delivers several wakes in one pass interrupts or
reopens the parent's turn once for each.

Files, under `<state>/briefs/<batch>/`:

    batch.json        role, count, the parent's runner and session, when it was made
    batch.lock        taken for every write below it
    <n>/started.json  the child's runner, session, host, model, effort, when it started
    <n>/result.md     what the child reported, copied from the file it named
    <n>/reported.json when it reported; written after result.md, so a reader that sees it
                      sees the whole result
    <n>/lost.json     when and why the child was found gone without reporting (watchdog.py)
    woken.json        the relay queued the batch's wake (relay.py)

A brief is open while it has neither `reported.json` nor `lost.json`. The directory is
removed when the relay closes the batch's watch: `dispatch.sh brief close <batch>`, or the
relay finding the parent gone for an hour. Nothing of a batch outlives it.

Exit codes: 0 done; 2 refused, the reason and the way out on stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import statedir  # noqa: E402

BATCH_RE = re.compile(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$")
LOCK_WAIT = 10.0


class Refusal(RuntimeError):
    """A request this module will not carry out; the message names the fact and the way out."""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------- where

def root(state: Path) -> Path:
    return Path(state) / "briefs"


def batch_dir(state: Path, batch: str) -> Path:
    if not BATCH_RE.match(batch or ""):
        raise Refusal(f"{batch!r} is not a batch name; a batch is named the way "
                      f"`dispatch.sh brief` printed it, e.g. 20261005-142233-a1f3")
    return root(state) / batch


def parse_brief(text: str) -> tuple[str, int]:
    """`<batch>/<n>` as (batch, n)."""
    batch, _, number = (text or "").partition("/")
    if not number.isdigit() or int(number) < 1:
        raise Refusal(f"{text!r} names no brief; a brief is `<batch>/<n>`, as the end of its "
                      f"prompt wrote it")
    batch_dir(Path("."), batch)
    return batch, int(number)


def _read(path: Path) -> dict | None:
    try:
        value = statedir.read_json(path, None)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _write(path: Path, value: dict) -> None:
    statedir.write_atomic(path, json.dumps(value, sort_keys=True) + "\n")


def _lock(directory: Path):
    return statedir.locked(directory / "batch.lock", wait=LOCK_WAIT, purpose="brief records")


# ----------------------------------------------------------------- reading

def batch_record(state: Path, batch: str) -> dict | None:
    return _read(batch_dir(state, batch) / "batch.json")


def briefs_of(state: Path, batch: str) -> list[dict]:
    """Each brief of the batch, in order: `n`, `state` (`starting`, `open`, `reported` or
    `lost`), what `started.json` says, `result` (the path, once reported) and `lost` (why).
    Empty when the batch is gone."""
    directory = batch_dir(state, batch)
    record = _read(directory / "batch.json")
    if record is None:
        return []
    out = []
    for n in range(1, int(record.get("count") or 0) + 1):
        here = directory / str(n)
        started = _read(here / "started.json")
        lost = _read(here / "lost.json")
        entry = {"n": n, "role": record.get("role"), "started": started, "result": None,
                 "lost": None}
        if (here / "reported.json").is_file():
            entry.update(state="reported", result=str(here / "result.md"))
        elif lost is not None:
            entry.update(state="lost", lost=lost.get("why"))
        elif started is not None:
            entry["state"] = "open"
        else:
            entry["state"] = "starting"
        out.append(entry)
    return out


def complete(state: Path, batch: str) -> bool:
    """Every brief of the batch has reported or is lost."""
    briefs = briefs_of(state, batch)
    return bool(briefs) and all(b["state"] in ("reported", "lost") for b in briefs)


def open_children(state: Path) -> list[dict]:
    """Every open brief on this state directory: `batch`, `n`, and its started record."""
    out = []
    try:
        batches = sorted(p.name for p in root(state).iterdir() if BATCH_RE.match(p.name))
    except OSError:
        return []
    for batch in batches:
        for entry in briefs_of(state, batch):
            if entry["state"] == "open":
                out.append({"batch": batch, "n": entry["n"], **entry["started"]})
    return out


# ----------------------------------------------------------------- writing

def create(state: Path, role: str, count: int, runner: str, session: str) -> str:
    """A new batch of `count` briefs of `role` for the parent (runner, session); its name."""
    if count < 1:
        raise Refusal("a batch needs at least one brief")
    root(state).mkdir(parents=True, exist_ok=True, mode=0o700)
    for _ in range(5):
        batch = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
        directory = batch_dir(state, batch)
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            continue
        for n in range(1, count + 1):
            (directory / str(n)).mkdir(mode=0o700)
        _write(directory / "batch.json", {"role": role, "count": count, "runner": runner,
                                          "session": session, "at": now_iso()})
        return batch
    raise Refusal(f"could not make a new batch directory under {root(state)}")


def mark_started(state: Path, batch: str, n: int, started: dict) -> None:
    directory = batch_dir(state, batch)
    if _read(directory / "batch.json") is None:
        raise Refusal(f"batch {batch} is gone; nothing was recorded")
    with _lock(directory):
        _write(directory / str(n) / "started.json", {**started, "at": now_iso()})


def report(state: Path, batch: str, n: int, source: Path, runner: str, session: str) -> Path:
    """Copy the child's result into the batch, then mark it reported. Only the session
    recorded as that brief's child may report it."""
    directory = batch_dir(state, batch)
    record = _read(directory / "batch.json")
    if record is None:
        raise Refusal(f"batch {batch} is closed: the session that briefed you closed it, or "
                      f"it was gone for an hour. Nobody is waiting for this result; end your "
                      f"turn.")
    if n > int(record.get("count") or 0):
        raise Refusal(f"batch {batch} has {record.get('count')} briefs, and no brief {n}")
    source = Path(source)
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Refusal(f"cannot read the result file {source}: {exc}. Write your whole answer "
                      f"to that file and report again.") from None
    if not text.strip():
        raise Refusal(f"the result file {source} is empty. Write your whole answer to it and "
                      f"report again.")
    here = directory / str(n)
    with _lock(directory):
        started = _read(here / "started.json") or {}
        if (started.get("runner"), started.get("session")) != (runner, session):
            raise Refusal(f"brief {batch}/{n} was started as {started.get('runner')} session "
                          f"{started.get('session')}, and this is {runner} session {session}. "
                          f"Only that session reports it.")
        if (here / "reported.json").is_file():
            raise Refusal(f"brief {batch}/{n} has reported already; the first report stands")
        lost = _read(here / "lost.json")
        if lost is not None:
            raise Refusal(f"brief {batch}/{n} was marked lost at {lost.get('at')} "
                          f"({lost.get('why')}), and the session that briefed you has been "
                          f"told so. This result is not taken.")
        statedir.write_atomic(here / "result.md", text)
        _write(here / "reported.json", {"at": now_iso(), "bytes": len(text.encode())})
    return here / "result.md"


def mark_lost(state: Path, batch: str, n: int, why: str) -> bool:
    """Mark an open brief lost. False when it has reported or is lost already, or the
    batch is gone."""
    directory = batch_dir(state, batch)
    if _read(directory / "batch.json") is None:
        return False
    here = directory / str(n)
    with _lock(directory):
        if (here / "reported.json").is_file() or (here / "lost.json").is_file():
            return False
        _write(here / "lost.json", {"at": now_iso(), "why": why})
    return True


def mark_woken(state: Path, batch: str) -> None:
    _write(batch_dir(state, batch) / "woken.json", {"at": now_iso()})


def woken(state: Path, batch: str) -> bool:
    return (batch_dir(state, batch) / "woken.json").is_file()


def remove(state: Path, batch: str) -> None:
    shutil.rmtree(batch_dir(state, batch), ignore_errors=True)


# ----------------------------------------------------------------- commands

def state_for(repo: str) -> Path:
    try:
        return statedir.state_dir(repo)
    except ValueError as exc:
        raise Refusal(f"{exc}. Pass --repo as owner/name.") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="briefs.py", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    new = sub.add_parser("new")
    new.add_argument("--repo", required=True)
    new.add_argument("--role", required=True)
    new.add_argument("--count", type=int, required=True)
    new.add_argument("--runner", required=True)
    new.add_argument("--session", required=True)

    started = sub.add_parser("started")
    started.add_argument("--repo", required=True)
    started.add_argument("--brief", required=True)
    for name in ("runner", "session", "host", "model", "effort"):
        started.add_argument(f"--{name}", required=True)

    forget = sub.add_parser("forget")
    forget.add_argument("--repo", required=True)
    forget.add_argument("--batch", required=True)

    rep = sub.add_parser("report")
    rep.add_argument("--repo", required=True)
    rep.add_argument("--brief", required=True)
    rep.add_argument("--file", required=True)
    rep.add_argument("--runner", required=True)
    rep.add_argument("--session", required=True)

    show = sub.add_parser("show")
    show.add_argument("--repo", required=True)
    show.add_argument("--batch", required=True)

    args = parser.parse_args(argv)
    try:
        state = state_for(args.repo)
        if args.command == "new":
            print(create(state, args.role, args.count, args.runner, args.session))
        elif args.command == "started":
            batch, n = parse_brief(args.brief)
            mark_started(state, batch, n, {k: getattr(args, k) for k in
                                           ("runner", "session", "host", "model", "effort")})
        elif args.command == "forget":
            remove(state, batch_dir(state, args.batch).name)
        elif args.command == "report":
            batch, n = parse_brief(args.brief)
            path = report(state, batch, n, Path(args.file), args.runner, args.session)
            print(f"reported brief {batch}/{n}: kept as {path}")
        elif args.command == "show":
            briefs = briefs_of(state, args.batch)
            if not briefs:
                raise Refusal(f"no batch {args.batch} is open for {args.repo}; it was closed, "
                              f"or never made")
            for entry in briefs:
                started = entry["started"] or {}
                where = entry["result"] or entry["lost"] or "-"
                print(f"{args.batch}/{entry['n']}\t{entry['state']}\t{entry['role']}\t"
                      f"{started.get('runner', '-')}\t{started.get('session', '-')}\t{where}")
        return 0
    except Refusal as exc:
        sys.stderr.write(f"briefs: {exc}\n")
        return 2
    except statedir.LockHeld as exc:
        sys.stderr.write(f"briefs: the brief records stayed locked for {LOCK_WAIT:.0f}s: {exc}. "
                         f"Run the command again.\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
