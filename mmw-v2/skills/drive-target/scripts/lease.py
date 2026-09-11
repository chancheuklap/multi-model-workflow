#!/usr/bin/env python3
"""One run's share of this machine.

The pipeline runs several agents at once on one machine: `dispatch` sends every startable
ticket of a spec out together, each in its own git worktree. A worktree isolates files.
Nothing isolated the machine — listening ports, the running application, the backing
service behind it, the account inside that service — because the target contract never
had a word for "this run's instance" and so no repository was ever asked to answer for
one. On 2026-09-05 five workers shared three fixed ports and a night produced one
worker's worth of work.

A **lease** is that missing word. It is a registration of `worktree path -> slot`, and a
slot is a block of ports and a data directory that no other slot overlaps. It is claimed
once per worktree, by the first run of that worktree's criteria that needs the product,
and lives until the ticket's work ends — landed, handed back, released, suspended or its
start retracted: a worktree runs its criteria many times in a night — the worker's own
run, the verifier's reverify, the closeout checks — and they all want the same
application, so the lease cannot be per run. Writing code takes no slot. A criterion or
judge run outside a ticket worktree gives its slot back when that run ends; `lease.py
run` starts a product for a person or agent and leaves its lease in place.

    lease.py claim [<worktree>]           claim (or return) this worktree's slot; 4 none free
    lease.py env [<worktree>]             print the claim as KEY=VALUE lines
    lease.py run [<worktree>] -- CMD…     run CMD with the claim in its environment
    lease.py release <worktree> [--stop]  give the slot back, with --stop after running the
                                          product's `stop`; 0 given back, 3 there was none
    lease.py remove-instance <worktree>   remove its data directory after its worktree is gone;
                                          0 removed or absent, 3 worktree exists/delete failed
    lease.py list                         every live claim
    lease.py count <directory>            how many claims sit under a directory

Two limits bound a claim. The machine's is `SLOTS`. The product's is `instance.max` in
the repository's `.mmw/target.json` — a product that cannot move its ports declares how
many copies of it can run at once — and it counts every claim made from that repository,
wherever its directory is: a ticket worktree, the main checkout running the night's
reverify, or any other checkout sharing the repository's git directory. Each claim
records that git directory, so the count holds after a worktree is gone. A claim past
either limit is not taken: `claim` exits 4 and prints which limit and
who holds the slots, because the caller waits and asks again rather than giving up
(`verify-ticket.py` does, and says on the ticket that it is waiting).

`claim` is atomic against other claimers: the count and the take happen under one lock on
the registry, and a slot is taken by creating its file with `O_CREAT | O_EXCL`, so two
processes racing for the last slot cannot both win. There is no fallback to another slot
on conflict — a worktree's slot is decided once and then it is simply looked up.

Every verb answers a program or an agent; none of them formats for a person, because on
this pipeline nobody reads a terminal. `claim`, `release`, `remove-instance` and `list`
print JSON, `env` prints `KEY=VALUE`, `count` prints a number, and what a caller has to
*decide* on is the exit code, never the wording. The one piece of prose here is the
refusal a live listener earns, on stderr: its reader is an agent choosing what to do
next, and it is written so that agent needs nothing else.

**Nothing here ends a process except through the repository's own `stop`.** `release
--stop` runs that command, which ends only what this run started, and ends the command
itself if it runs past `MMW_STOP_TIMEOUT_S`. `release` refuses while anything still listens
on the slot, and says which pid and which directory, because reclaiming a slot from a live
process is the same act as killing it.

What a claim puts in the environment:

    MMW_INSTANCE     a stable, readable, machine-unique name for this run
    MMW_SLOT         the slot number
    MMW_PORT_BASE    first port of this run's block
    MMW_PORT_COUNT   how many ports the block holds
    MMW_DATA_DIR     a directory this run owns
    MMW_AUTOMATION   `1`, so a product can neutralise what would leave this machine

A repository reads these in the commands `.mmw/target.json` declares, and translates them
into whatever its own product needs — **at the moment it starts a process, never into the
session or test environment**. A test suite that asserts the product's registered port
number is right to; a derived port leaking into it turns a correct suite red.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refusal import REPORT_BLOCKED, refusal  # noqa: E402

# The block every slot gets. 21000 is above the ranges a consuming repository already
# derives for its own long-lived services and below the ephemeral range macOS hands out.
PORT_BASE = int(os.environ.get("MMW_LEASE_PORT_BASE", "21000"))
PORT_STRIDE = int(os.environ.get("MMW_LEASE_PORT_STRIDE", "20"))
# How many runs this machine will hold. No claim goes past it; a machine that can hold
# more says so here rather than in any skill's code.
SLOTS = int(os.environ.get("MMW_LEASE_SLOTS", "8"))
# Seconds the product's `stop` gets before `release --stop` ends it and asks for the slot
# anyway.
STOP_TIMEOUT_S = int(os.environ.get("MMW_STOP_TIMEOUT_S", "300"))

ROOT = Path(os.environ.get("MMW_HOME", str(Path.home() / ".mmw")))
REGISTRY = ROOT / "leases"
INSTANCES = ROOT / "instances"


# ----------------------------------------------------------------- naming
def worktree_of(start: str | Path | None = None) -> Path:
    """The git worktree `start` is in, or `start` itself when it is not a repository."""
    start = Path(start) if start else Path.cwd()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=start,
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        return start.resolve()


def instance_name(worktree: Path) -> str:
    """Readable in a log, unique on this machine.

    The directory name alone is not unique: two repositories both dispatch a ticket #640
    and both call its worktree `issue-640`. Six hex of the absolute path settles it while
    keeping the part a person reads at the front.
    """
    digest = hashlib.sha256(str(worktree).encode("utf-8")).hexdigest()[:6]
    return f"{worktree.name}-{digest}"


def is_ticket_worktree(worktree: Path) -> bool:
    """Whether this is the persistent worktree of one ticket run."""
    return worktree.parent.name == ".worktrees" and re.fullmatch(
        r"issue-[0-9]+", worktree.name) is not None


def instance_data_dir(worktree: Path) -> Path:
    """The data directory deterministically assigned to `worktree`."""
    return INSTANCES / instance_name(worktree)


def remove_instance(worktree: Path) -> dict:
    """Remove a gone worktree's data directory; never remove one still in use."""
    target = worktree.resolve()
    data_dir = instance_data_dir(target)
    if target.exists():
        return {"removed": False, "worktree": str(target), "data_dir": str(data_dir),
                "reason": "worktree-exists"}
    try:
        shutil.rmtree(data_dir)
    except FileNotFoundError:
        pass
    except OSError as exc:
        return {"removed": False, "worktree": str(target), "data_dir": str(data_dir),
                "reason": str(exc)}
    return {"removed": True, "worktree": str(target), "data_dir": str(data_dir),
            "reason": None}


# ----------------------------------------------------------------- the registry
def slot_file(slot: int) -> Path:
    return REGISTRY / f"slot-{slot}.json"


def read_slot(slot: int) -> dict | None:
    try:
        return json.loads(slot_file(slot).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def claimed() -> list[dict]:
    """Every live claim, slot order."""
    out = []
    for slot in range(SLOTS):
        record = read_slot(slot)
        if record:
            out.append(record)
    return out


def ports_of(slot: int) -> range:
    first = PORT_BASE + slot * PORT_STRIDE
    return range(first, first + PORT_STRIDE)


def listener(port: int) -> int | None:
    """The pid listening on `port`, or `None`. A port nothing answers on binds."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", port))
        return None
    except OSError:
        pass
    finally:
        probe.close()
    try:
        out = subprocess.run(["lsof", "-tnP", f"-iTCP:{port}", "-sTCP:LISTEN"],
                             capture_output=True, text=True, timeout=10).stdout.split()
        return int(out[0]) if out else -1
    except (OSError, subprocess.SubprocessError, ValueError):
        return -1  # something holds it; this machine will not say what


def holder(pid: int) -> str:
    """The working directory of `pid`, for a refusal that names a fact."""
    if pid <= 0:
        return "?"
    try:
        out = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                             capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return "?"
    for line in out.splitlines():
        if line.startswith("n"):
            return line[1:]
    return "?"


def busy(slot: int) -> tuple[int, int] | None:
    """`(port, pid)` of the first port of `slot` something listens on."""
    for port in ports_of(slot):
        pid = listener(port)
        if pid is not None:
            return port, pid
    return None


# ----------------------------------------------------------------- claim / release
def sweep() -> list[int]:
    """Slots whose worktree is gone and whose ports are quiet, given back.

    Without this a machine fills up and never empties: a worktree may be removed while
    its registration remains, and later claims need to recover that quiet slot.

    A slot is only taken back when **both** are true — the directory is gone *and*
    nothing listens on the block. A live process on a slot whose directory somebody
    deleted is still a live process, and taking its ports would be the same act as
    ending it.
    """
    freed = []
    for slot in range(SLOTS):
        record = read_slot(slot)
        if not record:
            continue
        if Path(record.get("worktree", "")).exists():
            continue
        if busy(slot):
            continue
        slot_file(slot).unlink(missing_ok=True)
        freed.append(slot)
    return freed


class Full(Exception):
    """No slot can be taken now: `reason` is `product-full` (this repository's
    `instance.max` is reached) or `machine-full` (every slot of this machine is taken).
    `limit` is the limit reached and `holders` the worktrees holding its slots."""

    def __init__(self, reason: str, limit: int, holders: list[str]):
        super().__init__(f"{reason}: {len(holders)} of {limit} slots held")
        self.reason = reason
        self.limit = limit
        self.holders = holders

    def as_json(self) -> dict:
        return {"claimed": False, "reason": self.reason, "limit": self.limit,
                "holders": self.holders}


class CapUnreadable(RuntimeError):
    """`.mmw/target.json` is there and cannot be read, so the product's limit is unknown."""


class StopUnreadable(RuntimeError):
    """`.mmw/target.json` is there and cannot be read, so the product's `stop` is unknown."""


def target_json(worktree: Path, unreadable: type[RuntimeError]):
    """What this worktree's `.mmw/target.json` holds, or None when it has none.

    Raises `unreadable` for a file that is there and is not JSON: what it declares is then
    unknown, and unknown is not "declares nothing".
    """
    path = worktree / ".mmw" / "target.json"
    if not path.is_file():
        return None
    # Short, so the refusal built on it keeps its whole first part: the reader needs to
    # know which file and why, and the worktree it sits in is the one it is running in.
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise unreadable(f".mmw/target.json cannot be read as JSON ({exc.msg}, line "
                         f"{exc.lineno})") from None
    except OSError as exc:
        raise unreadable(f".mmw/target.json cannot be read: {exc.strerror}") from None


def _git(worktree: Path, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True,
                             text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def repository_of(worktree: Path) -> str | None:
    """The git directory every checkout of this worktree's repository shares, or None
    outside a repository. It is what a claim is counted against a product's limit by."""
    common = _git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return None
    try:
        return str(Path(common).resolve())
    except OSError:
        return common


def product_cap(worktree: Path) -> tuple[int, str] | None:
    """`(instance.max, the repository's shared git directory)` for this worktree, or None
    when it declares no limit or sits in no repository.

    Raises `CapUnreadable` for a `.mmw/target.json` that is there and is not JSON: a limit
    nobody can read is not "no limit", and taking a slot past it is how 2026-09-05 went.
    """
    data = target_json(worktree, CapUnreadable)
    instance = data.get("instance") if isinstance(data, dict) else None
    limit = instance.get("max") if isinstance(instance, dict) else None
    if not isinstance(limit, int) or limit <= 0:
        return None
    repo = repository_of(worktree)
    return (limit, repo) if repo else None


class _Locked:
    """An exclusive lock on the registry, held while a claim counts and takes."""

    def __enter__(self):
        REGISTRY.mkdir(parents=True, exist_ok=True)
        self.handle = open(REGISTRY / ".lock", "a+")
        fcntl.flock(self.handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()


def try_claim(worktree: Path) -> dict:
    """This worktree's slot, taken now if it does not have one; `Full` when no slot may be.

    Re-claiming is a lookup, so every command of a run agrees without a shared file to
    keep in step, and a worktree that already holds its slot is never refused one.
    """
    target = str(worktree)
    with _Locked():
        for slot in range(SLOTS):
            record = read_slot(slot)
            if record and record.get("worktree") == target:
                return record
        sweep()

        cap = product_cap(worktree)
        if cap is not None:
            limit, repo = cap
            held = [r["worktree"] for r in claimed() if r.get("repo") == repo]
            if len(held) >= limit:
                raise Full("product-full", limit, held)

        record = {
            "worktree": target,
            "repo": cap[1] if cap is not None else repository_of(worktree),
            "instance": instance_name(worktree),
            "slot": None,
            "port_base": None,
            "port_count": PORT_STRIDE,
            # So a slot that is still held in the morning can be read against the night.
            "claimed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        for slot in range(SLOTS):
            record["slot"] = slot
            record["port_base"] = PORT_BASE + slot * PORT_STRIDE
            payload = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                fd = os.open(slot_file(slot), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                continue
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            return record
        raise Full("machine-full", SLOTS, [r.get("worktree", "") for r in claimed()])


def claim(worktree: Path) -> dict:
    """This worktree's slot, or the refusal a caller that cannot wait gets.

    The judges of the drive-target skill come here through `leased_environment` in the
    middle of a criterion, where there is nobody to wait: `verify-ticket.py` has already
    claimed the slot before the run began, and waited for it when none was free, so a
    judge reaching this with no slot free is a run that skipped that step.
    """
    try:
        return try_claim(worktree)
    except CapUnreadable as exc:
        raise SystemExit(refusal(str(exc), "The product's limit is unknown.",
                                 REPORT_BLOCKED)) from None
    except Full as full:
        if full.reason == "product-full":
            raise SystemExit(refusal(
                f"This product's instance.max of {full.limit} is reached: "
                f"{', '.join(full.holders)}.",
                "A run needs one and none is free.",
                REPORT_BLOCKED,
            )) from None
        raise SystemExit(refusal(
            f"All {SLOTS} instance slots on this machine are claimed.",
            "A run needs one and none is free.",
            REPORT_BLOCKED,
        )) from None


def stop_command(worktree: Path) -> str | None:
    """The `stop` this worktree's `.mmw/target.json` declares, or None when it declares
    none. Raises `StopUnreadable` for a file that is there and cannot be read."""
    data = target_json(worktree, StopUnreadable)
    command = data.get("stop") if isinstance(data, dict) else None
    return command if isinstance(command, str) and command.strip() else None


def stop_product(worktree: Path, record: dict) -> str | None:
    """Run the product's `stop` from inside `worktree`, under the claim `record` it was
    started under; the reason when it did not stop cleanly, None when it did or declares
    no `stop`.

    Its output goes to a file rather than a pipe: a stop past `STOP_TIMEOUT_S` is ended,
    and a process it started that still held a pipe open would keep this waiting on it.
    """
    command = stop_command(worktree)
    if command is None:
        return None
    env = dict(os.environ)
    env.update(environment(record))
    with tempfile.TemporaryFile() as out:
        try:
            proc = subprocess.run(command, shell=True, cwd=worktree, env=env, stdout=out,
                                  stderr=subprocess.STDOUT, timeout=STOP_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return f"its stop did not finish in {STOP_TIMEOUT_S}s"
        except OSError as exc:
            return f"its stop could not be run: {exc.strerror or exc}"
        if proc.returncode == 0:
            return None
        out.seek(0)
        said = [line for line in out.read().decode("utf-8", "replace").splitlines()
                if line.strip()]
    return f"its stop exited {proc.returncode}" + (f": {' '.join(said[-3:])}" if said else "")


def release(worktree: Path, stop: bool = False) -> dict:
    """Give this worktree's slot back. Refuses while anything still listens on it.

    With `stop`, the product's `stop` in `.mmw/target.json` runs first, because a slot is
    free only once nothing listens on its ports. A stop that fails or does not finish is
    said on stderr and the slot is still asked for: the listener check is what keeps a
    live product's slot, whatever the stop did. A `.mmw/target.json` that cannot be read
    raises `StopUnreadable` and gives nothing back. A worktree with no slot runs no stop:
    the product starts only under a claim, so without one nothing of this run's is up.

    Returns what happened, as fields: `released`, the `slot` it was, and a `reason` when
    nothing came back. A live listener still earns the three-part refusal on stderr,
    because its reader is an agent deciding what to do next — but *which* of the three
    outcomes happened is the exit code, so no caller ever has to read that sentence to
    learn it, and the sentence can be reworded without breaking a caller.
    """
    target = str(worktree)
    for slot in range(SLOTS):
        record = read_slot(slot)
        if not record or record.get("worktree") != target:
            continue
        if stop:
            problem = stop_product(worktree, record)
            if problem:
                sys.stderr.write(f"lease.py: the product of {target} did not stop cleanly "
                                 f"({problem}); giving slot {slot} back is still tried\n")
        held = busy(slot)
        if held:
            port, pid = held
            raise SystemExit(refusal(
                f"Slot {slot} still has a listener: port {port}, pid {pid}, cwd {holder(pid)}.",
                "Reclaiming a slot from a live process is the same act as killing it.",
                "Stop that process where it was started, then release again.",
            ))
        slot_file(slot).unlink(missing_ok=True)
        return {"released": True, "worktree": target, "slot": slot, "reason": None}
    return {"released": False, "worktree": target, "slot": None, "reason": "no-lease"}


def count_under(prefix: Path) -> int:
    """How many live claims sit under `prefix`.

    Both sides are resolved before they are compared. A registry stores the resolved
    path and a caller usually has the unresolved one, and on macOS `/var` is a symlink
    to `/private/var` — comparing the two as text answers "none" every time, which in a
    gate means the gate is open and nobody is told. A safety check that fails silently is
    the shape of defect this whole file exists to remove, so the comparison lives here,
    once, next to the writer of those paths.
    """
    try:
        root = prefix.resolve()
    except OSError:
        root = prefix
    total = 0
    for record in claimed():
        try:
            tree = Path(record.get("worktree", "")).resolve()
        except OSError:
            continue
        if tree == root or root in tree.parents:
            total += 1
    return total


def environment(record: dict) -> dict[str, str]:
    data_dir = instance_data_dir(Path(record["worktree"]))
    return {
        "MMW_INSTANCE": record["instance"],
        "MMW_SLOT": str(record["slot"]),
        "MMW_PORT_BASE": str(record["port_base"]),
        "MMW_PORT_COUNT": str(record["port_count"]),
        "MMW_DATA_DIR": str(data_dir),
        "MMW_AUTOMATION": "1",
    }


def leased_environment(worktree: Path | None = None) -> dict[str, str]:
    """The claim for `worktree`, as environment. Used by the driver before it runs any
    command `.mmw/target.json` declares."""
    # Always through `worktree_of`: a caller passing a relative path (the driver runs
    # commands with `cwd=` whatever it was handed) would otherwise register a lease
    # under a name like "." that no later run can match or reclaim.
    record = claim(worktree_of(worktree))
    env = environment(record)
    Path(env["MMW_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    return env


@contextmanager
def judge_run(worktree: Path | None = None, *, stop: bool = False):
    """Release a judge's non-ticket lease after its own product cleanup.

    Ticket worktrees keep one lease across the worker's, reviewer's and verifier's runs.
    A judge in any other checkout owns its lease only for this context. `stop=True` is
    for an outer criteria runner that must also clean up a product its check left up.
    """
    tree = worktree_of(worktree)
    scope = "MMW_JUDGE_LEASE_OWNER"
    outer = scope not in os.environ
    if outer:
        os.environ[scope] = str(tree)
    try:
        yield
    finally:
        if outer:
            os.environ.pop(scope, None)
            if not is_ticket_worktree(tree):
                release(tree, stop=stop)


# ----------------------------------------------------------------- entry
def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        sys.stderr.write(__doc__ or "")
        return 2
    verb, rest = argv[0], argv[1:]

    if verb == "list":
        rows = []
        for record in claimed():
            held = busy(record["slot"])
            row = dict(record)
            row["busy"] = None if held is None else {
                "port": held[0], "pid": held[1], "cwd": holder(held[1])}
            rows.append(row)
        print(json.dumps(rows, ensure_ascii=False))
        return 0

    if verb == "run":
        if "--" not in rest:
            sys.stderr.write("usage: lease.py run [<worktree>] -- <command>…\n")
            return 2
        cut = rest.index("--")
        head, command = rest[:cut], rest[cut + 1:]
        if not command:
            sys.stderr.write("usage: lease.py run [<worktree>] -- <command>…\n")
            return 2
        tree = worktree_of(head[0] if head else None)
        env = dict(os.environ)
        env.update(leased_environment(tree))
        return subprocess.run(command, env=env).returncode

    if verb == "count":
        if not rest:
            sys.stderr.write("usage: lease.py count <directory>\n")
            return 2
        print(count_under(Path(rest[0])))
        return 0

    if verb == "remove-instance":
        if not rest:
            sys.stderr.write("usage: lease.py remove-instance <worktree>\n")
            return 2
        result = remove_instance(worktree_of(rest[0]))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["removed"] else 3

    stop = verb == "release" and "--stop" in rest
    if stop:
        rest.remove("--stop")
    tree = worktree_of(rest[0] if rest else None)
    if verb == "claim":
        try:
            record = try_claim(tree)
        except CapUnreadable as exc:
            sys.stderr.write(f"{exc}\n")
            return 2
        except Full as full:
            print(json.dumps(full.as_json(), ensure_ascii=False))
            return 4
        print(json.dumps(record, ensure_ascii=False))
        return 0
    if verb == "env":
        for key, value in leased_environment(tree).items():
            print(f"{key}={value}")
        return 0
    if verb == "release":
        try:
            result = release(tree, stop=stop)
        except StopUnreadable as exc:
            sys.stderr.write(f"{exc}; the product's stop is unknown, so nothing was stopped "
                             f"and the slot was not given back\n")
            return 2
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["released"] else 3

    sys.stderr.write(f"unknown verb: {verb}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
