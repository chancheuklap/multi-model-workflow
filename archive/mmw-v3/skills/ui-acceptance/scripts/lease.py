#!/usr/bin/env python3
"""One ticket worktree's share of this machine.

    lease.py claim [<worktree>]           acquire (or return) this worktree's slot; 4 none free
    lease.py run [<worktree>] [--product <name>] -- CMD…
                                        start its needs, then run CMD in its segment
    lease.py release <worktree> [--stop]  give the slot back, with --stop after running the
                                          product's `stop`; 0 given back, 3 there was none
    lease.py remove-instance <worktree>   remove its data directory after its worktree is gone;
                                          0 removed or absent, 3 worktree exists/delete failed
    lease.py list                         every live lease

What a lease puts in the environment:

    MMW_INSTANCE     a stable, readable, machine-unique name for this run
    MMW_SLOT         the slot number
    MMW_PORT_BASE    first port of this run's block
    MMW_PORT_COUNT   how many ports the block holds
    MMW_DATA_DIR     a directory this run owns
    MMW_AUTOMATION   `1`, so a product can neutralise what would leave this machine
    MMW_WORKTREE_COMMIT  this worktree's `HEAD`, the build a product's `doctor` compares
                     against; empty outside a git checkout

With a named product, the port variables describe its segment in root products order,
MMW_DATA_DIR ends in that product's name and MMW_PRODUCT names it. Dependencies start
first. Their discovered keys use uppercase product prefixes, with hyphens replaced
by underscores. The registry records started products and discovered values so stop
commands receive the same addresses even after a dependent has stopped. When `run`'s
command returns and nothing listens on the product's own ports any longer (the command
was its `stop`, or a probe that started nothing), the product is no longer recorded as
started, so a journey from the same worktree is not refused for an instance nobody runs.

A repository reads these in the commands `.mmw/target.json` declares, and translates them
into whatever its own product needs — **at the moment it starts a process, never into the
session or test environment**. A test suite that asserts the product's registered port
number is right to; a derived port leaking into it turns a correct suite red.
"""

# The pipeline runs several agents at once on one machine: `dispatch` sends every startable
# ticket of a spec out together, each in its own git worktree. A worktree isolates files.
# Nothing isolated the machine — listening ports, the running application, the backing
# service behind it, the account inside that service — because `.mmw/target.json` never
# had a word for "this run's instance" and so no repository was ever asked to answer for
# one. On 2026-09-05 five workers shared three fixed ports and a night produced one
# worker's worth of work.
#
# A **lease** is that missing word. It is a registration of `worktree path -> slot`, and a
# slot is a block of ports and a data directory that no other slot overlaps. It is acquired
# once per worktree, by the first run of that worktree's criteria that needs the product,
# and lives until the ticket's work ends — landed, handed back, released, suspended or its
# start retracted: a worktree runs its criteria many times in a night — the worker's own
# run, the worker's final reverify — and they all want the same
# application, so the lease cannot be per run. Writing code takes no slot. A criterion or
# oracle run outside a ticket worktree gives back the slot **it acquired** when that run
# ends, and leaves a slot that was already held to whoever acquired it; `lease.py run`
# starts a product for a person or agent and leaves its lease in place.
#
# A machine holds `SLOTS` leases. With every slot taken `claim` exits 4 and prints who
# holds them, and the run that needed one reports its ticket blocked (the ui-acceptance
# skill's rule 4): a machine that is full is not waited on. A slot with no registry
# record is not issued while a port of its block is listening. When none can be issued,
# the exit-4 JSON names each slot's holder in full. The refusal names those same
# holders when they fit beside the blocked-ticket sentence, and one short token per
# slot when they do not, so the last slots are not the ones cut off.
#
# `claim` is atomic against other acquirers: the count and the take happen under one lock on
# the registry, and a slot is taken by creating its file with `O_CREAT | O_EXCL`, so two
# processes racing for the last slot cannot both win. There is no fallback to another slot
# on conflict — a worktree's slot is decided once and then it is simply looked up.
#
# Every verb answers a program or an agent; none of them formats for a person, because on
# this pipeline nobody reads a terminal. `claim`, `release`, `remove-instance` and `list`
# print JSON, and what a caller has to *decide* on is the exit code, never the wording. The one piece of prose here is the
# refusal a live listener earns, on stderr: its reader is an agent choosing what to do
# next, and it is written so that agent needs nothing else.
#
# **Nothing here ends a process except through the repository's own `stop`.** `release
# --stop` runs that command, which ends only what this run started, and ends the command
# itself if it runs past `MMW_STOP_TIMEOUT_S`. `release` refuses while anything still listens
# on the slot, and says which pid and which directory, because re-acquiring a slot from a live
# process is the same act as killing it.

from __future__ import annotations

import argparse
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

from refusal import REASON_LIMIT, REPORT_BLOCKED, refusal  # noqa: E402

# The block every slot gets. 21000 is above the ranges a consuming repository already
# derives for its own long-lived services and below the ephemeral range macOS hands out.
PORT_BASE = int(os.environ.get("MMW_LEASE_PORT_BASE", "21000"))
PORT_STRIDE = int(os.environ.get("MMW_LEASE_PORT_STRIDE", "20"))
# How many runs this machine will hold. No lease goes past it; a machine that can hold
# more says so here rather than in any skill's code.
SLOTS = int(os.environ.get("MMW_LEASE_SLOTS", "8"))
# Seconds the product's `stop` gets before `release --stop` ends it and asks for the slot
# anyway.
STOP_TIMEOUT_S = int(os.environ.get("MMW_STOP_TIMEOUT_S", "300"))
# Seconds a connection to one loopback address of one port waits before the port counts
# as unanswered. A listener on this machine answers in well under a millisecond; the wait
# is for the one that has stopped accepting, which is held, not free.
PROBE_TIMEOUT_S = 0.5


# Where the registry and the instance directories live. Read at the moment one is
# needed, never bound once at import: a process that sets `MMW_HOME` after this module
# is in memory means it, and an empty value is no value — the same reading as `home()`
# in the `dispatch` skill's `statedir.py`, which is the canonical reader.
def home() -> Path:
    """The machine's MMW root: `MMW_HOME`, else `~/.mmw`."""
    return Path(os.environ.get("MMW_HOME") or (Path.home() / ".mmw"))


def registry() -> Path:
    """The directory holding every slot file and the lock they are taken under."""
    return home() / "leases"


def instances() -> Path:
    """The directory holding every run's data directory."""
    return home() / "instances"


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
    return instances() / instance_name(worktree)


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
    return registry() / f"slot-{slot}.json"


def read_slot(slot: int) -> dict | None:
    try:
        return json.loads(slot_file(slot).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def registered(worktree: Path) -> dict | None:
    """This worktree's lease as the registry has it, or None when it holds none."""
    target = str(worktree)
    for slot in range(SLOTS):
        record = read_slot(slot)
        if record and record.get("worktree") == target:
            return record
    return None


def claimed() -> list[dict]:
    """Every live lease, slot order."""
    out = []
    for slot in range(SLOTS):
        record = read_slot(slot)
        if record:
            out.append(record)
    return out


def ports_of(slot: int) -> range:
    first = PORT_BASE + slot * PORT_STRIDE
    return range(first, first + PORT_STRIDE)


def answers(port: int) -> bool:
    """Whether anything accepts a connection on `port`, on either loopback address.

    Both families are asked because a listener answers on the one it chose: a server
    told to listen on `localhost` under Node answers on `::1` and nothing else, and one
    told `0.0.0.0`, or a container engine publishing a port, answers on both.
    """
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        probe = socket.socket(family, socket.SOCK_STREAM)
        probe.settimeout(PROBE_TIMEOUT_S)
        try:
            if probe.connect_ex((host, port)) == 0:
                return True
        except OSError:
            continue
        finally:
            probe.close()
    return False


def listener(port: int) -> int | None:
    """The pid listening on `port`, or `None`.

    Two questions, because neither alone is the whole answer. *Does anything answer?* —
    `answers`, which sees a listener whatever address and family it is bound to. *Can
    this machine still hand the port out?* — a bind, which sees the one a connection
    cannot reach: a listener whose backlog is full, or one bound to this machine's
    network address and not to loopback.

    The bind alone was the whole check until 2026-09-12. With `SO_REUSEADDR` a bind of
    the specific `127.0.0.1` succeeds while something holds the wildcard `0.0.0.0`,
    which is where a container engine publishes a port on macOS, so a slot carrying a
    live Docker stack read as quiet and `release` and `sweep` took it back under the run
    using it. The bind keeps its `SO_REUSEADDR`: without it a port left in `TIME_WAIT`
    by a connection that has already closed reads as held, which would refuse a slot
    nobody is using.
    """
    if not answers(port):
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


def foreign_holder(slot: int) -> str | None:
    """Who listens on an unregistered slot, or None when the block is quiet.

    The registry has no record for this slot, so the listener is not a lease.
    `pid` is what a reader can check. When this machine will not say which
    process, the port is the fact.
    """
    held = busy(slot)
    if held is None:
        return None
    port, pid = held
    if pid > 0:
        return f"slot {slot} pid {pid}"
    return f"slot {slot} port {port}"


# ----------------------------------------------------------------- claim / release
def sweep() -> list[int]:
    """Slots whose worktree is gone and whose ports are quiet, given back.

    Without this a machine fills up and never empties: a worktree may be removed while
    its registration remains, and later leases need to recover that quiet slot.

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
    """Every slot of this machine is taken.

    `holders` names each one. A registered slot is its worktree path. A slot
    with no registry record whose ports are listening is `slot N pid P`, or
    `slot N port P` when the machine will not name the process.
    """

    def __init__(self, holders: list[str]):
        super().__init__(f"all {SLOTS} slots of this machine are held")
        self.holders = holders

    def as_json(self) -> dict:
        return {"claimed": False, "limit": SLOTS, "holders": self.holders}


class StopUnreadable(RuntimeError):
    """`.mmw/target.json` is there and cannot be read, so the product's `stop` is unknown."""


class TargetJSONError(Exception):
    """`.mmw/target.json` is there and is not one readable JSON object."""


# A product name is the directory `.mmw/<product>/`. It is also one path segment,
# so it allows only the characters the layout allows, and nothing that could climb out.
PRODUCT_NAME = re.compile(r"^[a-z0-9-]+$")
# The second segment of `<product>/<flow>`. That segment is a directory name.
FLOW_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def product_journey(name: str) -> tuple[str, str] | None:
    """`<product>/<flow>` when `name` is that shape, else None."""
    product, sep, flow = name.partition("/")
    if (not sep or "/" in flow or PRODUCT_NAME.fullmatch(product) is None
            or FLOW_NAME.fullmatch(flow) is None):
        return None
    return product, flow


# Keys that belong to one product. On the root file they mean the old layout,
# where that file is the one product.
PRODUCT_KEYS = frozenset({
    "start", "stop", "discover", "doctor", "ports", "stories",
    "journeys", "leaves_machine", "harness_markers",
})


class LegacyLayoutError(TargetJSONError):
    """Product answers on the root require an explicit migration."""


class TargetRead(dict):
    """One product's config. The root object is `.root`.

    Callers that read `start`, `discover` or `harness_markers` use the mapping,
    which is the product. `checks` is on `.root`. `error` is set when
    the product file is there and is not
    one JSON object. The root is still on `.root`.
    """

    def __init__(self, product: dict | None, root: dict, name: str | None, *,
                 present: bool, error: str | None = None):
        super().__init__(product or {})
        self.root = root
        self.name = name
        self.present = present
        self.error = error


def _read_json_object(path: Path, shown: str) -> dict | None:
    """The object at `path`, or None when the file is not there.

    `shown` is the short relative spelling. A refusal trims from the front to stay
    under the deny-reason limit, and an absolute temp path can trim away the words
    a caller matches.
    """
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetJSONError(f"{shown} cannot be read as JSON: {exc}") from None
    if not isinstance(data, dict):
        raise TargetJSONError(f"{shown} must hold one JSON object")
    return data


def read_target_json(root: Path, product: str | None = None) -> TargetRead | None:
    """The root config and one product's config, or None when the root file is absent.

    The product configuration is `.mmw/<product>/target.json`. With no name and
    exactly one listed product, that product is selected. Product keys on the root
    are refused with the migration command. A checks-only root has no product.

    Every reader parses the file this way, once, here. The function lives in
    `lease.py` because `target_config.py` imports `lease`, and the reverse would cycle.
    """
    data = _read_json_object(root / ".mmw" / "target.json", ".mmw/target.json")
    if data is None:
        return None
    if PRODUCT_KEYS.intersection(data):
        key = sorted(PRODUCT_KEYS.intersection(data))[0]
        raise LegacyLayoutError(refusal(
            f".mmw/target.json contains product key {key}.",
            "This is the old layout.",
            "Run `python3 ~/.agents/skills/setup-mmw/scripts/migrate_products.py <产品名>`.",
        ))
    names = data.get("products")
    chosen = product
    if (chosen is None and isinstance(names, list) and len(names) == 1
            and isinstance(names[0], str)):
        chosen = names[0]
    if not isinstance(chosen, str) or PRODUCT_NAME.fullmatch(chosen) is None:
        return TargetRead(None, data, chosen if isinstance(chosen, str) else None, present=False)
    shown = f".mmw/{chosen}/target.json"
    product_path = root / ".mmw" / chosen / "target.json"
    try:
        product_data = _read_json_object(product_path, shown)
    except TargetJSONError as exc:
        # The root was read. A product file that is not JSON must not hide it,
        # or a checks reader cannot see the root and --check exits 2.
        return TargetRead(None, data, chosen, present=False, error=str(exc))
    if product_data is None:
        return TargetRead(None, data, chosen, present=False)
    return TargetRead(product_data, data, chosen, present=True)


def product_names(value) -> list[str] | None:
    """The `products` entries when every one is a string, else None.

    An empty list is an empty list. A missing key, a non-list, or a non-string
    entry is None.
    """
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return list(value)


def product_gap(read: TargetRead | None, product: str | None, *,
                membership: bool = False) -> str | None:
    """Why `read` is not one product's config, or None when it is.

    `absent` — no root file. `error` — the product file is not JSON (`read.error`).
    `not-in-list` — `membership` is set and `product` is not one of `products`.
    `not-selected` — a name was passed and the read did not select it.
    `many` — the root lists more than one product and none was selected.
    `missing` — the selected product has no file.
    `discover` and `stories` are the caller's concern.
    """
    if read is None:
        return "absent"
    if (membership and product
            and product not in (product_names(read.root.get("products")) or [])):
        return "not-in-list"
    if read.error:
        return "error"
    if product is not None and read.name != product:
        return "not-selected"
    if read.name is None:
        return "many"
    if not read.present:
        return "missing"
    return None


def target_json(worktree: Path, unreadable: type[RuntimeError]):
    """What this worktree's `.mmw/target.json` holds, or None when it has none.

    Raises `unreadable` for a file that is there and is not one JSON object: what it
    declares is then unknown, and unknown is not "declares nothing".
    """
    try:
        read = read_target_json(worktree)
    except TargetJSONError as exc:
        raise unreadable(str(exc)) from None
    if read is not None and read.error:
        raise unreadable(read.error)
    return read


class _Locked:
    """An exclusive lock on the registry, held while acquiring counts and takes."""

    def __enter__(self):
        directory = registry()
        directory.mkdir(parents=True, exist_ok=True)
        self.handle = open(directory / ".lock", "a+")
        fcntl.flock(self.handle, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()


def try_claim(worktree: Path) -> dict:
    """This worktree's slot, taken now if it does not have one; `Full` when none is free.

    Re-acquiring is a lookup, so every command of a run agrees without a shared file to
    keep in step, and a worktree that already holds its slot is never refused one.
    A slot with no registry record is not issued while any port of its block is
    listening. That listener is not in the registry, and the next slot is tried.
    """
    product_segments(worktree)
    target = str(worktree)
    with _Locked():
        held = registered(worktree)
        if held:
            return held
        sweep()
        record = {
            "worktree": target,
            "instance": instance_name(worktree),
            "slot": None,
            "port_base": None,
            "port_count": PORT_STRIDE,
            "started": [],
            # So a slot that is still held in the morning can be read against the night.
            "claimed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        holders: list[str] = []
        for slot in range(SLOTS):
            record["slot"] = slot
            record["port_base"] = PORT_BASE + slot * PORT_STRIDE
            if slot_file(slot).exists():
                holders.append(_named_holder(slot))
                continue
            foreign = foreign_holder(slot)
            if foreign is not None:
                holders.append(foreign)
                continue
            payload = json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8")
            try:
                fd = os.open(slot_file(slot), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                continue
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            return record
        raise Full(holders)


def _named_holder(slot: int) -> str:
    """The worktree a slot file names, or which slot it is when the file cannot be read."""
    return (read_slot(slot) or {}).get("worktree") or f"slot {slot} record unreadable"


def _holder_fact(text: str) -> str:
    """The pid, the port, or the path's last name. Enough to check one holder."""
    parts = text.split()
    if (len(parts) == 4 and parts[0] == "slot" and parts[1].isdigit()
            and parts[3].isdigit()):
        if parts[2] == "pid":
            return "p" + parts[3]
        if parts[2] == "port":
            return parts[3]
    if not text or text.endswith("record unreadable"):
        return "?"
    return Path(text).name or "?"


_NONE_FREE = "A run needs one and none is free."


def _refusal_holders(holders: list[str]) -> str:
    """Every holder, written so `refusal` keeps the whole list.

    Part 1 is trimmed from the end to leave the blocked-ticket sentence whole.
    Eight worktree paths, and eight `slot N pid P` lines, are longer than the
    room that leaves, so the last slots would be the ones cut off. A list that
    does not fit is one token per slot instead: `<slot>:<fact>`.
    """
    full = ", ".join(holders)
    room = REASON_LIMIT - len(f" {_NONE_FREE} {REPORT_BLOCKED}")
    if len(full) <= room:
        return full
    count = len(holders)
    sep = ", "
    width = (room - len(sep) * (count - 1)) // count if count else room
    if width < 3:
        return full
    tokens = []
    for index, text in enumerate(holders):
        fact = _holder_fact(text)
        body = f"{index}:{fact}"
        if len(body) > width:
            keep = width - len(str(index)) - 1
            body = f"{index}:{fact[-keep:]}" if keep > 0 else body[:width]
        tokens.append(body)
    return sep.join(tokens)


def claim(worktree: Path) -> dict:
    """This worktree's slot, or the refusal a caller that cannot wait gets.

    The oracles of the ui-acceptance skill come here through `leased_environment` in the
    middle of a criterion: `verify-ticket.py` has already acquired the slot before the
    run began, so an oracle reaching this with no slot free is a run that skipped that step.
    When none is free, the refusal names each slot's holder.
    """
    try:
        return try_claim(worktree)
    except Full as full:
        raise SystemExit(refusal(
            _refusal_holders(full.holders),
            _NONE_FREE,
            REPORT_BLOCKED,
        )) from None


def stop_command(worktree: Path, product: str) -> str | None:
    """The `stop` this worktree's `.mmw/<product>/target.json` declares, or None when it declares
    none. Raises `StopUnreadable` for a file that is there and cannot be read."""
    try:
        data = read_target_json(worktree, product)
    except TargetJSONError as exc:
        raise StopUnreadable(str(exc)) from None
    if data is not None and (data.error or not data.present):
        raise StopUnreadable(data.error or f".mmw/{product}/target.json is missing")
    command = data.get("stop") if isinstance(data, dict) else None
    return command if isinstance(command, str) and command.strip() else None


def stop_product(worktree: Path, record: dict, product: str) -> str | None:
    """Run the product's `stop` from inside `worktree`, under the lease `record` it was
    started under; the reason when it did not stop cleanly, None when it did or declares
    no `stop`.

    Its output goes to a file rather than a pipe: a stop past `STOP_TIMEOUT_S` is ended,
    and a process it started that still held a pipe open would keep this waiting on it.
    """
    command = stop_command(worktree, product)
    if command is None:
        return None
    env = product_environment(record, product)
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
    the product starts only under a lease, so without one nothing of this run's is up.

    Returns what happened, as fields: `released`, the `slot` it was, and a `reason` when
    nothing came back. A live listener still earns the three-part refusal on stderr,
    because its reader is an agent deciding what to do next — but *which* of the three
    outcomes happened is the exit code, so no caller ever has to read that sentence to
    learn it, and the sentence can be reworded without breaking a caller.
    """
    target = str(worktree)
    record = registered(worktree)
    if record is None:
        return {"released": False, "worktree": target, "slot": None, "reason": "no-lease"}
    slot = record["slot"]
    if stop:
        target_json(worktree, StopUnreadable)
        names = list(record.get("started", []))
        # Read all stop commands before stopping any product. An unreadable declaration
        # must leave the lease untouched.
        for name in names:
            stop_command(worktree, name)
        stop_products(worktree, record, names)
    held = busy(slot)
    if held:
        port, pid = held
        product = product_at_port(record, port)
        raise SystemExit(refusal(
            f"Slot {slot} still has a listener: {product}port {port}, pid {pid}, cwd {holder(pid)}.",
            "Re-acquiring a slot from a live process is the same act as killing it.",
            "Stop that process where it was started, then release again.",
        ))
    slot_file(slot).unlink(missing_ok=True)
    return {"released": True, "worktree": target, "slot": slot, "reason": None}


def product_segments(worktree: Path) -> dict[str, tuple[int, int]]:
    """Offsets and counts in root products order, before any slot is acquired."""
    try:
        read = read_target_json(worktree)
        if read is None:
            return {}
        segments = {}
        offset = 0
        for name in read.root.get("products", []):
            one = read_target_json(worktree, name)
            if one is None or not one.present or one.error:
                raise TargetJSONError(one.error if one is not None and one.error
                                      else f".mmw/{name}/target.json is missing")
            count = one.get("ports")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise TargetJSONError(f".mmw/{name}/target.json ports must be a nonnegative integer")
            segments[name] = (offset, count)
            offset += count
        if offset > PORT_STRIDE:
            raise TargetJSONError(f"products need {offset} ports, slot holds {PORT_STRIDE}")
        return segments
    except LegacyLayoutError:
        raise
    except TargetJSONError as exc:
        raise SystemExit(refusal(
            str(exc), "The product port segments cannot fit this lease.",
            "Run `target_config.py --check` and correct the named configuration.",
        )) from None


def worktree_commit(root: Path) -> str:
    """The commit `doctor` compares a build against, or empty when `root` has none."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def environment(record: dict, product: str | None = None) -> dict[str, str]:
    data_dir = instance_data_dir(Path(record["worktree"]))
    env = {
        "MMW_INSTANCE": record["instance"],
        "MMW_SLOT": str(record["slot"]),
        "MMW_PORT_BASE": str(record["port_base"]),
        "MMW_PORT_COUNT": str(record["port_count"]),
        "MMW_DATA_DIR": str(data_dir),
        "MMW_AUTOMATION": "1",
        "MMW_WORKTREE_COMMIT": worktree_commit(Path(record["worktree"])),
    }
    if product is not None:
        segments = product_port_ranges(record)
        if product not in segments:
            raise SystemExit(refusal(
                f".mmw/target.json does not list product {product}.",
                "A command needs one declared product's port segment.",
                "Run `target_config.py --check` and select a listed --product.",
            ))
        ports = segments[product]
        env.update(MMW_PORT_BASE=str(ports.start),
                   MMW_PORT_COUNT=str(len(ports)), MMW_DATA_DIR=str(data_dir / product),
                   MMW_PRODUCT=product)
    return env


def product_port_ranges(record: dict) -> dict[str, range]:
    return {name: range(record["port_base"] + offset, record["port_base"] + offset + count)
            for name, (offset, count) in product_segments(Path(record["worktree"])).items()}


def dependency_order(worktree: Path, product: str) -> list[str]:
    read = read_target_json(worktree, product)
    needs = read.root.get("needs", {})
    order: list[str] = []
    visiting: set[str] = set()

    def visit(name: str):
        if name in order:
            return
        if name in visiting or name not in read.root.get("products", []):
            raise SystemExit(refusal(
                f".mmw/target.json needs cannot resolve product {name}.",
                "Dependencies must be listed products without cycles.",
                "Run `target_config.py --check` and correct needs.",
            ))
        visiting.add(name)
        for dependency in needs.get(name, []):
            visit(dependency)
        visiting.remove(name)
        order.append(name)

    visit(product)
    return order


def addresses_into(env: dict[str, str], data: dict, prefix: str = "") -> None:
    for key, value in data.items():
        env[prefix + str(key).upper()] = (json.dumps(value, ensure_ascii=False)
                                         if isinstance(value, (dict, list)) else str(value))


def product_environment(record: dict, product: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(environment(record, product))
    Path(env["MMW_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    data = record.get("discovered", {})
    env.pop("MMW_BREAK", None)
    for dependency in dependency_order(Path(record["worktree"]), product)[:-1]:
        addresses_into(env, data.get(dependency, {}), dependency.upper().replace("-", "_") + "_")
    addresses_into(env, data.get(product, {}))
    return env


def update_started(worktree: Path, product: str, *, data: dict | None = None,
                   stopped: bool = False) -> dict:
    with _Locked():
        record = registered(worktree)
        started = record.setdefault("started", [])
        if stopped:
            if product in started:
                started.remove(product)
        elif product not in started:
            started.append(product)
        if data is not None:
            record.setdefault("discovered", {})[product] = data
        fd, path = tempfile.mkstemp(dir=registry(), prefix=".slot-")
        try:
            with os.fdopen(fd, "w") as output:
                json.dump(record, output, ensure_ascii=False, indent=2)
            os.replace(path, slot_file(record["slot"]))
        finally:
            Path(path).unlink(missing_ok=True)
        return record


def product_at_port(record: dict, port: int) -> str:
    for name, ports in product_port_ranges(record).items():
        if port in ports:
            return f"product {name}, "
    return ""


def stop_products(worktree: Path, record: dict, names: list[str]) -> None:
    for name in reversed(names):
        problem = stop_product(worktree, record, name)
        if problem:
            sys.stderr.write(f"lease.py: product {name} did not stop cleanly "
                             f"({problem}); its ports are still checked\n")
        ports = product_port_ranges(record)[name]
        if not any(listener(port) is not None for port in ports):
            record = update_started(worktree, name, stopped=True)


class ProductCommandFailed(Exception):
    def __init__(self, product: str, kind: str, command: str, proc: subprocess.CompletedProcess):
        self.product, self.kind, self.command, self.proc = product, kind, command, proc
        super().__init__(f"product {product} {kind} {command} exit {proc.returncode}")


class ProductRun:
    """Dependencies and cleanup owned by one invocation, within a persistent lease."""

    def __init__(self, worktree: Path, product: str):
        self.worktree = worktree_of(worktree)
        self.product = product
        self.order = dependency_order(self.worktree, product)
        self.record = claim(self.worktree)
        self.initial_started = list(self.record.get("started", []))
        self.owned: list[str] = []

    def env(self, product: str | None = None) -> dict[str, str]:
        self.record = registered(self.worktree)
        return product_environment(self.record, product or self.product)

    def mark_started(self, product: str) -> None:
        self.record = registered(self.worktree)
        if product not in self.record.get("started", []):
            self.owned.append(product)
            # Register before launching so a partial start still has an owner and stop.
            self.record = update_started(self.worktree, product)

    def remember(self, product: str, data: dict) -> None:
        self.record = update_started(self.worktree, product, data=data)

    def start_needs(self) -> None:
        from target_config import discover, run_command, target_config

        for product in self.order[:-1]:
            cfg = target_config(self.worktree, product)
            if product not in registered(self.worktree).get("started", []):
                self.mark_started(product)
                try:
                    run_command(cfg["start"], self.worktree, env=self.env(product))
                except SystemExit as exc:
                    raise ProductCommandFailed(product, "start", cfg["start"], exc.code) from None
            try:
                data = discover(cfg, self.worktree, env=self.env(product))
            except SystemExit as exc:
                raise ProductCommandFailed(product, "discover", cfg["discover"], exc.code) from None
            self.remember(product, data)

    def forget_if_quiet(self) -> None:
        """Take the product off `started` when nothing listens on its own ports.

        A product with no ports gives no such evidence, so it stays recorded and
        `release --stop` still runs its `stop`.
        """
        self.record = registered(self.worktree)
        ports = product_port_ranges(self.record)[self.product]
        if len(ports) and not any(listener(port) is not None for port in ports):
            self.record = update_started(self.worktree, self.product, stopped=True)

    def stop(self) -> None:
        self.record = registered(self.worktree)
        stop_products(self.worktree, self.record, self.owned)
        self.record = registered(self.worktree)
        self.owned = [name for name in self.owned if name in self.record.get("started", [])]


def leased_environment(worktree: Path | None = None) -> dict[str, str]:
    """The lease for `worktree`, as environment. Used by the driver before it runs any
    command `.mmw/target.json` declares."""
    # Always through `worktree_of`: a caller passing a relative path (the driver runs
    # commands with `cwd=` whatever it was handed) would otherwise register a lease
    # under a name like "." that no later run can match or re-acquire.
    record = claim(worktree_of(worktree))
    env = environment(record)
    Path(env["MMW_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    return env


@contextmanager
def judge_run(worktree: Path | None = None, *, stop: bool = False):
    """Release the non-ticket lease this oracle acquired, and no other.

    Ticket worktrees keep one lease across the worker's and reviewer's runs.
    An oracle in any other checkout owns the lease it acquired itself, for this context
    only. A lease the worktree already held when the oracle started belongs to whoever
    acquired it — a product a person left running under `lease.py run`, a journey running
    from the same checkout — and giving that one back, with or without running the
    product's `stop`, ends a process this run never started. `stop=True` is for an outer
    criteria runner that must also clean up a product its own check left up.
    """
    tree = worktree_of(worktree)
    scope = "MMW_JUDGE_LEASE_OWNER"
    outer = scope not in os.environ
    ours = outer and registered(tree) is None
    if outer:
        os.environ[scope] = str(tree)
    try:
        yield
    finally:
        if outer:
            os.environ.pop(scope, None)
            if ours and not is_ticket_worktree(tree):
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
            sys.stderr.write("usage: lease.py run [<worktree>] [--product <name>] -- <command>…\n")
            return 2
        cut = rest.index("--")
        head, command = rest[:cut], rest[cut + 1:]
        if not command:
            sys.stderr.write("usage: lease.py run [<worktree>] [--product <name>] -- <command>…\n")
            return 2
        parser = argparse.ArgumentParser(prog="lease.py run")
        parser.add_argument("worktree", nargs="?")
        parser.add_argument("--product")
        args = parser.parse_args(head)
        tree = worktree_of(args.worktree)
        read = read_target_json(tree, args.product)
        product = read.name if read is not None else args.product
        if (read is not None and product is None
                and ("products" in read.root or "needs" in read.root)):
            raise SystemExit(refusal(
                ".mmw/target.json does not select a product for this command.",
                "The command needs one product's port segment.",
                "Run `lease.py run --product <name> -- <command>`.",
            ))
        run = None
        if product is not None:
            run = ProductRun(tree, product)
            try:
                run.start_needs()
            except ProductCommandFailed as exc:
                run.stop()
                print(f"{exc}\n{exc.proc.stdout}{exc.proc.stderr}", file=sys.stderr)
                return 2
            run.mark_started(product)
            env = run.env()
        else:
            env = dict(os.environ)
            env.update(leased_environment(tree))
        try:
            code = subprocess.run(command, env=env).returncode
        except OSError as exc:
            if run is not None:
                run.stop()
            print(refusal(
                f"Command {command[0]} could not run: {exc.strerror or exc}.",
                "No product command was completed.",
                "Correct the command and run `lease.py run` again.",
            ), file=sys.stderr)
            return 2
        if code != 0 and run is not None:
            run.stop()
        elif run is not None:
            run.forget_if_quiet()
        return code

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
        except Full as full:
            print(json.dumps(full.as_json(), ensure_ascii=False))
            return 4
        print(json.dumps(record, ensure_ascii=False))
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
    try:
        sys.exit(main())
    except LegacyLayoutError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
