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
once per worktree and lives as long as the worktree does: a worktree runs its criteria
many times in a night — self-run, reverify, the closeout checks — and they all want the
same application, so the lease cannot be per run.

    lease.py claim [<worktree>]        claim (or return) this worktree's slot
    lease.py env [<worktree>]          print the claim as KEY=VALUE lines
    lease.py run [<worktree>] -- CMD…  run CMD with the claim in its environment
    lease.py release <worktree>        give the slot back
    lease.py list                      what is claimed right now
    lease.py count <directory>         how many claims sit under a directory

`claim` is atomic against other claimers: a slot is taken by creating its file with
`O_CREAT | O_EXCL`, so two processes racing for the last slot cannot both win. There is
no fallback to another slot on conflict and no shared file that several processes have to
agree on — a worktree's slot is decided once and then it is simply looked up.

**Nothing here ever ends a process.** `release` refuses while anything still listens on
the slot, and says which pid and which directory, because reclaiming a slot from a live
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

import hashlib
import json
import os
import socket
import subprocess
import sys
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
# How many runs this machine will hold. The gate never dispatches past it; a machine that
# can hold more says so here rather than in any skill's code.
SLOTS = int(os.environ.get("MMW_LEASE_SLOTS", "8"))

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

    Without this a machine fills up and never empties: `dispatch.sh` prunes worktree
    registrations but never removes a worktree directory, and a night that dispatches
    more tickets than it merges would leave every slot claimed forever.

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


def claim(worktree: Path) -> dict:
    """This worktree's slot, taken now if it does not have one.

    Re-claiming is a lookup, so every command of a run agrees without a shared file to
    keep in step.
    """
    REGISTRY.mkdir(parents=True, exist_ok=True)
    target = str(worktree)
    for slot in range(SLOTS):
        record = read_slot(slot)
        if record and record.get("worktree") == target:
            return record
    sweep()

    record = {
        "worktree": target,
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

    raise SystemExit(refusal(
        f"All {SLOTS} instance slots on this machine are claimed.",
        "A run needs one and none is free.",
        REPORT_BLOCKED,
    ))


def release(worktree: Path) -> str:
    """Give this worktree's slot back. Refuses while anything still listens on it."""
    target = str(worktree)
    for slot in range(SLOTS):
        record = read_slot(slot)
        if not record or record.get("worktree") != target:
            continue
        held = busy(slot)
        if held:
            port, pid = held
            raise SystemExit(refusal(
                f"Slot {slot} still has a listener: port {port}, pid {pid}, cwd {holder(pid)}.",
                "Reclaiming a slot from a live process is the same act as killing it.",
                "Stop that process where it was started, then release again.",
            ))
        slot_file(slot).unlink(missing_ok=True)
        return f"released slot {slot} for {target}"
    return f"no lease for {target}"


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
    data_dir = INSTANCES / record["instance"]
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


# ----------------------------------------------------------------- entry
def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        sys.stderr.write(__doc__ or "")
        return 2
    verb, rest = argv[0], argv[1:]

    if verb == "list":
        for record in claimed():
            held = busy(record["slot"])
            mark = f"  (port {held[0]} held by pid {held[1]})" if held else ""
            print(f"slot {record['slot']:>2}  ports {record['port_base']}-"
                  f"{record['port_base'] + record['port_count'] - 1}  "
                  f"{record['instance']}  {record['worktree']}{mark}")
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
        env = dict(os.environ)
        env.update(leased_environment(worktree_of(head[0] if head else None)))
        return subprocess.run(command, env=env).returncode

    if verb == "count":
        if not rest:
            sys.stderr.write("usage: lease.py count <directory>\n")
            return 2
        print(count_under(Path(rest[0])))
        return 0

    tree = worktree_of(rest[0] if rest else None)
    if verb == "claim":
        print(json.dumps(claim(tree), ensure_ascii=False))
        return 0
    if verb == "env":
        for key, value in leased_environment(tree).items():
            print(f"{key}={value}")
        return 0
    if verb == "release":
        print(release(tree))
        return 0

    sys.stderr.write(f"unknown verb: {verb}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
