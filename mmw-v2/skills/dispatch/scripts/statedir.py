#!/usr/bin/env python3
"""This machine's state directory for one repository, and the lock every write to it takes.

    from statedir import state_dir, locked, holder, LockHeld, write_atomic, read_json

**One directory per repository**: `$MMW_HOME/state/<owner>__<name>/`, where `MMW_HOME`
defaults to `~/.mmw` — the same root `lease.py` of the drive-target skill keeps its
registry under. Owner and name are lowercased, because GitHub treats `Owner/Repo` and
`owner/repo` as one repository and two directories for it would be two truths. Every file
a long-running MMW process keeps about a repository lives in that directory; nothing about
a repository is kept anywhere else on the machine.

**A lock is a file in that directory.** Holding it means holding the kernel's advisory lock
(`flock`) on that file. The file's content says who holds it: one JSON object with the
holder's `pid`, its process `identity`, the time it took the lock and what for. The kernel
lock is what excludes; the record is for whoever wants to know who is in there without
taking the lock — a shell script (macOS has no `flock` command), a watchdog asking whether
a process is still up, a refusal that has to name the holder.

**A pid alone does not name a process.** The system hands a dead process's pid to the next
process that starts. So a record names a live holder only when its pid is running now *and*
that process's identity is the one recorded. The identity is the start time `ps -o lstart=`
prints, in UTC and the C locale so that every reader prints it alike: a process keeps it for
life, and a later process given the same pid has another.
A record whose pid is dead, or whose pid now belongs to a process that started at another
time, is stale and names nobody.

The kernel releases the lock when its holder dies, however it dies, so a stale record never
stands in anyone's way: the next holder overwrites it. A holder that exits normally empties
the record on the way out.
"""

from __future__ import annotations

import errno
import fcntl
import json
import os
import re
import subprocess
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

REPO_RE = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+)$")


class LockHeld(Exception):
    """Raised when a lock stayed taken for the whole wait. `record` is the live holder, or
    None when no live holder is recorded yet (it took the lock and has not written it)."""

    def __init__(self, path: Path, record: dict | None):
        self.path = path
        self.record = record
        who = (f"pid {record.get('pid')} (started {record.get('identity')}, "
               f"holding it since {record.get('since')} for {record.get('purpose') or 'no stated purpose'})"
               if record else "a process whose record is not written yet")
        super().__init__(f"{path} is held by {who}")


# ----------------------------------------------------------------- where

def home() -> Path:
    """The machine's MMW root: `MMW_HOME`, else `~/.mmw`."""
    return Path(os.environ.get("MMW_HOME") or (Path.home() / ".mmw"))


def slug(repo: str) -> str:
    """`owner/name` as one directory name: `owner__name`, lowercased.

    A GitHub owner cannot contain `_`, so the first `__` is always the split point.
    """
    found = REPO_RE.match(repo or "")
    if not found or found.group(2) in (".", ".."):
        raise ValueError(f"{repo!r} is not a GitHub repository in the form owner/name")
    return f"{found.group(1)}__{found.group(2)}".lower()


def state_dir(repo: str, create: bool = True) -> Path:
    """This repository's state directory. Created (mode 0700) unless `create` is False."""
    path = home() / "state" / slug(repo)
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


# ----------------------------------------------------------------- files

def write_atomic(path: Path, text: str) -> None:
    """Replace `path` with `text` in one step: a reader sees the old file or the new one."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_json(path: Path, default):
    """The JSON in `path`, or `default` when the file is absent.

    A file that is there but is not JSON raises: a state file that cannot be read is not the
    same answer as a state file that was never written.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return default
    if not text.strip():
        return default
    return json.loads(text)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------- who holds it

def process_identity(pid: int) -> str | None:
    """The start time of process `pid` as `ps -o lstart=` prints it, or None when there is
    no such process (or `ps` could not be asked)."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    # `ps` prints the start time in the caller's locale and time zone; pinned, a writer and a
    # reader under different settings still agree on one process.
    env = dict(os.environ, LC_ALL="C", LANG="C", TZ="UTC")
    try:
        run = subprocess.run(["ps", "-o", "lstart=", "-p", str(pid)],
                             capture_output=True, text=True, env=env, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    out = " ".join(run.stdout.split())
    return out if run.returncode == 0 and out else None


_OWN_IDENTITY: str | None = None


def own_identity() -> str | None:
    global _OWN_IDENTITY
    if _OWN_IDENTITY is None:
        _OWN_IDENTITY = process_identity(os.getpid())
    return _OWN_IDENTITY


def read_record(path: Path) -> dict | None:
    """The record in a lock file as written, live or not; None when empty or unreadable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "null")
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def holder(path: Path) -> dict | None:
    """The live holder of the lock at `path`, or None.

    Live means the recorded pid runs now and its identity is the recorded one. This reads
    the record only; it never takes the lock, so any process may ask.
    """
    record = read_record(path)
    if not record:
        return None
    pid = record.get("pid")
    recorded = record.get("identity")
    if not isinstance(pid, int) or not recorded:
        return None
    current = process_identity(pid)
    if current is None or current != recorded:
        return None
    return record


# ----------------------------------------------------------------- taking it

@contextmanager
def locked(path: Path, wait: float = 10.0, purpose: str = "") -> Iterator[None]:
    """Hold the lock at `path` for the body of the `with`.

    Waits up to `wait` seconds for a live holder to let go, then raises LockHeld naming it.
    `wait=0` asks once. While held, the file records this process's pid and identity.
    """
    path = Path(path)
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    deadline = time.monotonic() + max(wait, 0.0)
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EWOULDBLOCK, errno.EAGAIN, errno.EACCES):
                    raise
                if time.monotonic() >= deadline:
                    raise LockHeld(path, holder(path)) from None
                time.sleep(0.05)
        record = {"pid": os.getpid(), "identity": own_identity(),
                  "since": now_iso(), "purpose": purpose}
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, (json.dumps(record) + "\n").encode("utf-8"))
        os.fsync(fd)
        try:
            yield
        finally:
            os.ftruncate(fd, 0)
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
