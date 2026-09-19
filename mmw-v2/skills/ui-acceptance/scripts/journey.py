#!/usr/bin/env python3
"""Run one named journey against this repository's product, and prove it can fail.

    journey.py run <name> [--break "<METHOD> <route>"]

Claims or reuses this worktree's lease, runs `.mmw/target.json`'s `start` every
time, runs `discover` and puts each printed address into the environment under
its uppercase key (plus the lease variables), runs `<journeys>/<name>` (a `run`
executable, or the command `package.json` declares), and runs `stop` whether
the script succeeded or not.

With `--break`, it starts the product again with `MMW_BREAK` supplied only to `start`,
requires `BREAK ARMED <METHOD> <route>`, discovers the product again, and reruns the
script in the same environment. That pass must fail. Without `--break`, the contract
smoke journey keeps the product down, moves discovered addresses to a closed port, and
runs the same script again. A judge that cannot go red is not a
judge (`docs/adr/0008-silence-is-never-a-pass.md`).

Then `stop` runs once more and this run's slot must be quiet: a journey ends leaving the
machine as it found it, and anything still listening on the slot outlives the run and
blocks whichever run is given the slot next.

    JOURNEY OK <name>                                 exit 0
    JOURNEY FAILED <name> at <last line>              exit 1
    JOURNEY GREEN WITH BREAK <name> — <line>          exit 1
    JOURNEY GREEN WITHOUT PRODUCT <name> — <line>     exit 1
    JOURNEY LEFT THE PRODUCT UP <name> — <listeners>  exit 1
    the run never got as far as the script            exit 2
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from target_config import command_env, discover, repo_root, run_command, target_config  # noqa: E402
from lease import holder, judge_run, listener, ports_of, registered, worktree_of  # noqa: E402
from refusal import REPORT_BLOCKED, refusal  # noqa: E402

DEFAULT_JOURNEYS = ".mmw/journeys"
BREAK_RE = re.compile(r"[A-Z]+ /\S*")
RETIRED_PASS_SIGNAL = "MMW_" + "JOURNEY_NEGATIVE"


def last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def stop(cfg: dict, root: Path, env: dict[str, str]) -> None:
    command = cfg.get("stop")
    if not command:
        return
    run_command(command, root, env=env, check=False)


def still_up(root: Path) -> list[str]:
    """What still listens on this run's slot, once its `stop` has been run for the last
    time: one `port <n> pid <pid> cwd <dir>` line each, empty when the slot is quiet.

    A journey's last act is to leave the machine as it found it. A script that starts
    anything itself leaves that process behind on this slot. The next run given this slot
    then starts onto live ports and can report nothing but blocked, far from the journey
    that caused it, which is how agentflow spent a night in 2026-09-11. The run that left
    them says so itself instead.
    """
    record = registered(worktree_of(root))
    if record is None:
        return []
    left = []
    for port in ports_of(record["slot"]):
        pid = listener(port)
        if pid is not None:
            left.append(f"port {port} pid {pid} cwd {holder(pid)}")
    return left


def journey_command(dest: Path) -> list[str] | str | None:
    """How to run `<journeys>/<name>`: a `run` file, or `package.json`'s `scripts.run`."""
    runner = dest / "run"
    if runner.is_file() and os.access(runner, os.X_OK):
        return [str(runner)]
    package = dest / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"{package} cannot be read as JSON: {exc}")
        scripts = data.get("scripts") if isinstance(data, dict) else None
        command = scripts.get("run") if isinstance(scripts, dict) else None
        if isinstance(command, str) and command.strip():
            return command
    return None


def addresses_into(env: dict[str, str], data: dict) -> None:
    """Put each discover key into the environment under its uppercase spelling."""
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        env[str(key).upper()] = rendered


ADDRESS_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*://)?([^/:\s]+):(\d+)(.*)$")


def closed_port() -> int:
    """A port on this machine that nothing is listening on: bound, read, released."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def repointed(value: str, port: int) -> str | None:
    """`value` with its port replaced, or None when it carries no address."""
    found = ADDRESS_RE.match(value)
    if not found:
        return None
    scheme, host, _, rest = found.groups()
    return f"{scheme or ''}{host}:{port}{rest}"


def negative_env(env: dict[str, str], data: dict) -> dict[str, str]:
    """The environment the control pass gets: the same one, pointing nowhere.

    Only the keys `discover` printed are touched, and only those that carry a port —
    `instance` is left as it is, because a script may read it to say which run it is
    rather than to reach anything. The lease variables stay too: the control pass is
    the same run, not a different one.

    The script gets no pass-specific variable: it cannot tell the control from the real
    run and fail early instead of proving that its product assertion can go red.
    """
    port = closed_port()
    control = dict(env)
    for key in data:
        name = str(key).upper()
        moved = repointed(control.get(name, ""), port)
        if moved is not None:
            control[name] = moved
    return control


def _run_named(name: str, root: Path, break_spec: str | None = None) -> int:
    try:
        env = command_env(root)
        cfg = target_config(root)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    env.pop("MMW_BREAK", None)
    env.pop(RETIRED_PASS_SIGNAL, None)

    def bail(message: str | None = None,
             proc: subprocess.CompletedProcess | None = None) -> int:
        stop(cfg, root, env)
        if proc is not None:
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
        if message:
            print(message, file=sys.stderr)
        return 2

    start_cmd = cfg.get("start")
    if not isinstance(start_cmd, str) or not start_cmd.strip():
        return bail("`.mmw/target.json` has no `start` command")

    stop_cmd = cfg.get("stop")
    if not isinstance(stop_cmd, str) or not stop_cmd.strip():
        return bail("`.mmw/target.json` has no `stop` command")

    try:
        run_command(start_cmd, root, env=env)
        data = discover(cfg, root, env=env)
    except SystemExit as exc:
        return bail(proc=exc.code)
    addresses_into(env, data)

    journeys = cfg.get("journeys") or DEFAULT_JOURNEYS
    dest = (root / journeys / name).resolve()
    spec = journey_command(dest)
    if spec is None:
        stop(cfg, root, env)
        print(f"JOURNEY FAILED {name} at {dest} has no executable `run` "
              f"and no package.json scripts.run")
        return 1

    def attempt(environment: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            spec, shell=isinstance(spec, str), cwd=dest,
            capture_output=True, text=True, env=environment,
        )

    try:
        script = attempt(env)
    finally:
        stop(cfg, root, env)

    if script.returncode != 0:
        print(f"JOURNEY FAILED {name} at {last_line(script.stdout + script.stderr)}")
        return 1

    if break_spec is not None:
        start_env = dict(env)
        start_env["MMW_BREAK"] = break_spec
        try:
            armed = run_command(start_cmd, root, env=start_env)
        except SystemExit as exc:
            proc = exc.code
            return bail(refusal(
                f"`start` exited {proc.returncode} while arming {break_spec!r}.",
                "The break switch in references/journey.md did not come up.",
                REPORT_BLOCKED,
            ), proc=proc)
        expected_arm = f"BREAK ARMED {break_spec}"
        if expected_arm not in (armed.stdout + armed.stderr).splitlines():
            return bail(refusal(
                f"`start` exited 0 without printing `{expected_arm}`.",
                "The break switch in references/journey.md was not confirmed.",
                REPORT_BLOCKED,
            ))
        try:
            control_data = discover(cfg, root, env=env)
        except SystemExit as exc:
            return bail(proc=exc.code)
        addresses_into(env, control_data)
        control_env = env
        green_prefix = f"JOURNEY GREEN WITH BREAK {name} — "
        green_explanation = ""
    else:
        # The product is down and the addresses point nowhere. A journey that reached it
        # cannot pass this; one that asserted nothing passes it exactly as it passed above,
        # which is the whole difference the run is here to print.
        control_env = negative_env(env, data)
        green_prefix = f"JOURNEY GREEN WITHOUT PRODUCT {name} at "
        green_explanation = (
            " — it passed again with the product stopped and its addresses pointing "
            "nowhere. Make the journey assert something only the running product can "
            "satisfy."
        )
    try:
        control = attempt(control_env)
    finally:
        stop(cfg, root, env)
    if control.returncode == 0:
        print(f"{green_prefix}{last_line(control.stdout + control.stderr)}{green_explanation}")
        return 1
    left = still_up(root)
    if left:
        print(f"JOURNEY LEFT THE PRODUCT UP {name} — this run's slot still has "
              f"{len(left)} listener(s) after `stop`: {'; '.join(left)}. Whatever started "
              f"them outlives this run and blocks the next run given this slot. A journey "
              f"script starts nothing itself in either pass; "
              f"everything it needs is started by `start` and ended by `stop`.")
        return 1
    print(f"JOURNEY OK {name}")
    return 0


def run_named(name: str, start: Path | None = None, break_spec: str | None = None) -> int:
    root = repo_root(start)
    code: int | None = None
    try:
        with judge_run(root):
            code = _run_named(name, root, break_spec)
    except SystemExit as exc:
        if code is None:
            raise
        print(exc, file=sys.stderr)
        return max(code, 1)
    assert code is not None
    return code


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) not in (2, 4) or argv[0] != "run" or (len(argv) == 4 and argv[2] != "--break"):
        sys.stderr.write('usage: journey.py run <name> [--break "<METHOD> <route>"]\n')
        return 2
    if len(argv) == 4 and not BREAK_RE.fullmatch(argv[3]):
        print(refusal(
            f"--break value {argv[3]!r} does not have one uppercase method, one space, "
            "and a route starting with `/`.",
            "journey.py cannot identify one route to fail.",
            'Use a value such as `--break "POST /items/{id}"` and run the criterion again.',
        ), file=sys.stderr)
        return 2
    return run_named(argv[1], break_spec=argv[3] if len(argv) == 4 else None)


if __name__ == "__main__":
    sys.exit(main())
