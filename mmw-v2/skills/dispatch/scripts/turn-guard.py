#!/usr/bin/env python3
"""The turn guard: the first layer of liveness, a hook on the main agent's own turn end.

    turn-guard.py stop <host>      <host> is claude, codex, grok, cursor or pi;
                                   the host's turn-end payload is on stdin

The worst way a night dies is the main agent stopping by itself: its turn ends and nothing
ever starts another. The relay wakes it when a ticket has news, and the watchdog
(`watchdog.py`, beside this file) notices a ticket that went silent and a relay that died —
but the watchdog is one process, and when it dies, nothing notices that. This hook does. It
runs every time the main agent's turn ends, and:

1. re-arms the watchdog (`watchdog.arm`) when it is not healthy, and
2. keeps the turn from ending when tickets are held and the watchdog is still not healthy.

**Whose turn.** Only the main agent's. For every state directory under `$MMW_HOME/state`
with an open night (`watchdog.night_open`), the relay's `recipient.json` names the main
agent's runner and session; this process asks that runner's adapter `self` which session
it runs in, and acts only when the two are the same. A worker's turn end, or any session
on a machine with no open night, is let through after reading a few files. When `self`
cannot tell (exit 1), the session is taken to be the main agent: a guard run once too often
costs a check, a guard skipped costs the night.

**The predicate** (`verdict`): block when the watchdog is not healthy and the watchdog's
last heartbeat does not say that nothing is held. No heartbeat at all, or one from a round
that could not read every ticket, is not "nothing held". Healthy is the watchdog's own
test: its lock names a live process by pid and process identity, that process wrote the
heartbeat, and the heartbeat is within `max(300, poll + 60)` seconds.

**What each host can do at a turn end**:

    host     event            can it keep the turn from ending?     how this file answers
    claude   Stop             yes: exit 2, stderr to the model       exit 2 + stderr
    codex    Stop             yes: exit 2, stderr to the model       exit 2 + stderr
    pi       agent_settled    no; an extension sends one follow-up   exit 2 + stderr, which the
                              message, which starts another run      extension sends as a follow-up
    cursor   stop             no; exit 2 is ignored. One             exit 0, `{"followup_message":
                              `followup_message` on stdout starts    ...}` on stdout
                              another turn
    grok     Stop             no; the reason is fed back as a        exit 2 + stderr
                              message and the agent runs another
                              round

A block is asked for once per turn end: a stop that is already the continuation a block
forced (`stop_hook_active` for Claude and Codex, `stopHookActive` — or `stop_hook_active`
when the camel-case field is absent — for Grok, `loop_count` 1 or more for Cursor) re-arms
and is recorded like any other, and is let through; Grok's observe-only session-end fire
(`reason` other than `end_turn`) is not a turn and is not looked at.
The Pi extension keeps its own latch: it skips the `agent_settled` that follows its own
follow-up. The block itself re-armed the watchdog, and the text tells the agent the one
command to run when it did not come up.

**Three lessons about hooks that fire in the wrong host**, copied from firstmate
(`docs/turnend-guard.md`, `bin/fm-hook-host-lib.sh`), because each is a direct hit here:
Cursor and Grok both load `~/.claude/settings.json`, and Grok also loads
`~/.cursor/hooks.json`, so the copies registered for Claude and for Cursor run inside
those hosts as well.

1. The Claude-registered copy stands down when `GROK_AGENT` or `GROK_HOOK_EVENT` is set —
   both, because Grok 0.2.73 injects only the first and 1.0.0 only the second, so a guard
   on one of them stops working at an upgrade.
2. What that costs when it goes wrong is on record: with the guard failing, firstmate's
   Claude auto-arm ran synchronously under Grok, waited out its declared 28800 seconds, and
   that Grok turn never ended.
3. It never stands down on `GROK_SESSION_ID`: Grok injects that into every child process,
   so it survives into a Claude session Grok started and would switch off that Claude
   session's own guard. For the same reason the Cursor tests read the payload, never the
   environment: the Claude-registered copy stands down when the payload carries Cursor's
   own `cursor_version`, and the Cursor-registered copy acts only when it does — Cursor
   exports `CURSOR_VERSION` and friends into every child, so an environment test would
   also switch off a Claude session started by hand from a Cursor pane.

**It never breaks a host.** Arguments it does not know, an unreadable payload, or an error
of its own end in exit 0 (Cursor) or exit 1 with the reason on stderr — a hook error the
host shows, which never blocks. Exit 2 means only "held tickets and no healthy watchdog".
Each decision it makes for a main agent is appended to `guard.log` in that night's state
directory.

**Checked against the real hosts**, one short non-interactive session each, with the guard
registered in a throwaway home and a throwaway `MMW_HOME` whose night was open, whose
registered main agent was that session, and whose watchdog could not start
(`MMW_WATCHDOG_PY` naming a script that exits at once):

    (filled in below by the checks that were run)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import statedir  # noqa: E402

HOSTS = ("claude", "codex", "grok", "cursor", "pi")
ARM_WAIT = 5.0
SELF_TIMEOUT = 10
# Cursor's `loop_count` is 0 on the first stop after a real message and one more per
# follow-up-driven stop; a follow-up is asked for only on the first.
CURSOR_FOLLOWUPS = 1


# ----------------------------------------------------------------- the host's side (pure)

def read_payload(text: str) -> dict:
    try:
        value = json.loads(text) if text and text.strip() else {}
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def stands_down(host: str, payload: dict, env) -> str | None:
    """Why this copy of the hook must do nothing in this process, or None.

    The Claude-registered copy runs inside Grok and inside Cursor as well; the Cursor one
    runs inside Grok. Each stands down where another host's own registration owns the turn.
    """
    has_cursor_version = isinstance(payload.get("cursor_version"), str)
    if host == "claude":
        # Both Grok markers, and never GROK_SESSION_ID (see the header).
        if env.get("GROK_AGENT") or env.get("GROK_HOOK_EVENT"):
            return "Grok runs this Claude-registered copy; Grok's own registration owns its turns"
        if has_cursor_version:
            return "Cursor runs this Claude-registered copy; Cursor's own registration owns its turns"
    if host == "cursor" and not has_cursor_version:
        return "the payload carries no cursor_version, so Cursor did not send it"
    return None


def continuation(host: str, payload: dict) -> bool:
    """True when this stop is already the continuation that an earlier block forced."""
    if host in ("claude", "codex"):
        return payload.get("stop_hook_active") is True
    if host == "grok":
        if "stopHookActive" in payload:
            return payload.get("stopHookActive") is True
        return payload.get("stop_hook_active") is True
    if host == "cursor":
        try:
            return int(payload.get("loop_count") or 0) >= CURSOR_FOLLOWUPS
        except (TypeError, ValueError):
            return False
    return False


def session_end(host: str, payload: dict) -> bool:
    """Grok's observe-only `Stop` at session end: there is no turn left to keep."""
    return host == "grok" and payload.get("reason") not in (None, "end_turn")


def verdict(held, healthy: bool, why: str) -> tuple[bool, str]:
    """Block this turn end? `held` is the watchdog's last heartbeat's list of held tickets,
    or None when no heartbeat says (none written, or a round that could not read them all)."""
    if healthy:
        return False, why
    if isinstance(held, list) and not held:
        return False, f"nothing is held at the watchdog's last round, though {why}"
    return True, why


def answer(host: str, block: bool, text: str) -> tuple[int, str, str]:
    """(exit code, stdout, stderr) in the host's own terms."""
    if not block:
        return 0, "", ""
    if host == "cursor":
        return 0, json.dumps({"followup_message": text}) + "\n", ""
    return 2, "", text + "\n"


# ----------------------------------------------------------------- this machine's side

def load_watchdog():
    """`watchdog.py` beside this file, by path: a module of that name installed elsewhere
    must not answer for it. Loaded only once a turn end has to be judged."""
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


def is_main(state: Path) -> tuple[bool | None, str]:
    """Whether this process runs in the session registered as the night's main agent.
    (True/False/None for cannot tell, what was compared)."""
    try:
        record = statedir.read_json(state / "recipient.json", {})
    except ValueError:
        return None, f"{state / 'recipient.json'} is not JSON"
    runner = record.get("runner") if isinstance(record, dict) else None
    session = record.get("session") if isinstance(record, dict) else None
    if not runner or not session:
        return None, "no main agent is registered"
    adapter = runners_dir() / f"{runner}.sh"
    if not adapter.is_file():
        return None, f"no adapter {adapter} to ask"
    try:
        run = subprocess.run(["bash", str(adapter), "self"], capture_output=True, text=True,
                             timeout=SELF_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"{runner}.sh self could not be run: {exc}"
    me = (run.stdout or "").strip()
    if run.returncode == 0:
        return me == session, f"this session is {runner} {me}, the main agent is {runner} {session}"
    if run.returncode == 3:
        return False, f"this process runs in no {runner} session"
    return None, f"{runner}.sh self answered {run.returncode}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(state: Path, host: str, block: bool, held, why: str) -> None:
    try:
        with open(state / "guard.log", "a", encoding="utf-8") as fh:
            fh.write(f"{now_iso()} {host} {'block' if block else 'allow'} held={held} {why}\n")
    except OSError:
        pass


def guard(host: str, forced: bool = False) -> list[str]:
    """Every block this turn end calls for, one text per night; empty to let it end.

    `forced`: this stop is the continuation an earlier block forced. It still re-arms the
    watchdog and records its decision, and it never blocks.
    """
    dog = load_watchdog()

    blocks: list[str] = []
    for state in open_states(dog):
        main, compared = is_main(state)
        if main is False:
            continue
        repo = dog.repo_of(state)
        healthy, why, beat = dog.read_health(state)
        armed = ""
        if not healthy:
            healthy, armed = dog.arm(state, repo, ARM_WAIT)
            _, _, beat = dog.read_health(state)
            if not healthy:
                why = f"{why}; this hook tried to start it and {armed}"
        held = beat.get("held") if isinstance(beat, dict) else None
        block, reason = verdict(held, healthy, why)
        if forced and block:
            block, reason = False, f"the continuation an earlier block forced, still: {reason}"
        log(state, host, block, held, reason if main else f"{reason} ({compared})")
        if block:
            which = ", ".join(f"#{n}" for n in held) if isinstance(held, list) else \
                "which ones is not known: no watchdog round has read them all"
            blocks.append(
                f"MMW turn guard: the night on {repo} has tickets in flight ({which}) and its "
                f"watchdog is not healthy: {reason}. Until it is, nothing notices a worker "
                f"that dies or a relay that stops. Run `python3 {Path(dog.__file__).resolve()} "
                f"arm --repo {repo}`, act on what it prints, then end your turn."
            )
    return blocks


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "stop" or argv[1] not in HOSTS:
        sys.stderr.write(f"usage: turn-guard.py stop <{'|'.join(HOSTS)}>\n")
        return 0
    host = argv[1]
    try:
        payload = read_payload(sys.stdin.read())
    except (OSError, UnicodeDecodeError):
        payload = {}
    if stands_down(host, payload, os.environ) or session_end(host, payload):
        return 0
    try:
        blocks = guard(host, forced=continuation(host, payload))
    except BaseException as exc:  # noqa: BLE001 — an import's SystemExit(2) must not block
        sys.stderr.write(f"turn-guard: could not judge this turn end: {exc!r}\n")
        return 0 if host == "cursor" else 1
    code, out, err = answer(host, bool(blocks), "\n\n".join(blocks))
    sys.stdout.write(out)
    sys.stderr.write(err)
    return code


if __name__ == "__main__":
    sys.exit(main())
