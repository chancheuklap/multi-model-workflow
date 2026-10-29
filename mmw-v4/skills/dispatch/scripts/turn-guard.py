#!/usr/bin/env python3
"""Arm every open watch's watchdog at each host's turn end. Never hold a turn.

    turn-guard.py stop <claude|codex>     the host's turn-end payload is ignored

For every state directory under MMW_HOME/state with an open watch, call watchdog.arm
and append its result to guard.log. Arming does nothing when the watchdog is healthy.
An unsuccessful arm is logged and still lets the turn end.

own_brief, is_main and their runner identity lookup also serve reply-check.py, which
uses them without arming the watchdog or asking the tracker.

Exit 0 allows the turn, including unknown arguments. An error exits 1 with its reason
on stderr and does not request a continuation from the host.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import statedir  # noqa: E402
import briefs  # noqa: E402

HOSTS = ("claude", "codex")
ARM_WAIT = 5.0
SELF_TIMEOUT = 10


def load_watchdog():
    """`watchdog.py` beside this file, by path: a module of that name installed elsewhere
    must not answer for it. Loaded when arming or identifying an unattended session."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("mmw_watchdog", HERE / "watchdog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def runners_dir() -> Path:
    return Path(os.environ.get("MMW_RUNNERS_DIR") or (HERE / "runners"))


def open_states(dog) -> list[Path]:
    root = statedir.home() / "state"
    try:
        candidates = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError:
        return []
    return [p for p in candidates if dog.night_open(p)]


def _runner_session(runner: str, asked: dict | None = None) -> str | None:
    """The session this process runs in, as `runners/<runner>.sh self` reads it, or None.
    `asked` keeps the answers of one turn end, so each runner is asked once."""
    asked = {} if asked is None else asked
    if runner not in asked:
        asked[runner] = None
        adapter = runners_dir() / f"{runner}.sh"
        if adapter.is_file():
            try:
                run = subprocess.run(["bash", str(adapter), "self"], capture_output=True,
                                     text=True, timeout=SELF_TIMEOUT)
            except (OSError, subprocess.SubprocessError):
                run = None
            if run is not None and run.returncode == 0 and (run.stdout or "").strip():
                asked[runner] = run.stdout.strip()
    return asked[runner]


def is_main(state: Path, dog, asked: dict | None = None) -> bool:
    """True only when this process's own (runner, session), read by that runner's `self`,
    is the orchestrator of a watch open on `state`. Whatever cannot be established is False."""
    try:
        watches = dog.relay_mod.read_watches(state)
    except ValueError:
        return False
    mains = {dog.relay_mod.main_of(entry) for entry in watches.values()}
    asked = {} if asked is None else asked
    return any((runner, _runner_session(runner, asked)) in mains
               for runner in sorted({r for r, _ in mains}))


def own_brief(state: Path, asked: dict | None = None) -> dict | None:
    """The open brief on `state` this process is the session of, or None."""
    for child in briefs.open_children(state):
        runner = child.get("runner")
        if runner and _runner_session(runner, asked) == child.get("session"):
            return child
    return None


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(state: Path, host: str, why: str) -> None:
    try:
        with open(state / "guard.log", "a", encoding="utf-8") as fh:
            fh.write(f"{now_iso()} {host} allow {why}\n")
    except OSError:
        pass


def guard(host: str) -> None:
    dog = load_watchdog()
    for state in open_states(dog):
        healthy, why = dog.arm(state, dog.repo_of(state), ARM_WAIT)
        log(state, host, f"watchdog {'healthy' if healthy else 'unhealthy'}: {why}")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "stop" or argv[1] not in HOSTS:
        sys.stderr.write(f"usage: turn-guard.py stop <{'|'.join(HOSTS)}>\n")
        return 0
    try:
        guard(argv[1])
    except BaseException as exc:  # An import's SystemExit(2) must not hold a turn.
        sys.stderr.write(f"turn-guard: could not arm the watchdog: {exc!r}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
