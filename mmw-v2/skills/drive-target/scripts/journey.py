#!/usr/bin/env python3
"""Run one named journey against this repository's product, and prove it can fail.

    journey.py run <name>

Claims or reuses this worktree's lease, runs `.mmw/target.json`'s `start` every
time, runs `discover` and puts each printed address into the environment under
its uppercase key (plus the lease variables), runs `<journeys>/<name>` (a `run`
executable, or the command `package.json` declares), and runs `stop` whether
the script succeeded or not.

Then, with the product stopped, it runs the script one more time as its **negative
control**: same directory, same environment, except that every address `discover`
printed has its port replaced by one nothing listens on, and `MMW_JOURNEY_NEGATIVE=1`
is set. That pass must fail. A script that asserts nothing, or that never reaches the
product, passes it — and a judge that cannot go red is not a judge
(`docs/adr/0008-silence-is-never-a-pass.md`). Two independent reasons make the pass
red for a real journey: the product is down, and the addresses point nowhere.

    JOURNEY OK <name>                                 exit 0
    JOURNEY FAILED <name> at <last line>              exit 1
    JOURNEY GREEN WITHOUT PRODUCT <name> — <line>     exit 1
    start's own refusal, unchanged                    exit 2
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

from screen_driver import command_env, discover, repo_root, run_command, target_config  # noqa: E402

DEFAULT_JOURNEYS = ".mmw/journeys"


def last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def stop(cfg: dict, root: Path, env: dict[str, str]) -> None:
    command = cfg.get("stop")
    if not command:
        return
    run_command(command, root, env=env, check=False)


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
    `instance` and `instance_check` are left as they are, because a script may read them
    to say which run it is rather than to reach anything. The lease variables stay too:
    the control pass is the same run, not a different one.

    `MMW_JOURNEY_NEGATIVE=1` is set so a script that wants to can fail fast instead of
    waiting out its own timeouts. Whether the pass counts does not depend on the script
    reading it — the addresses are the mechanism, this is a courtesy. It is deliberately
    not `MMW_NEGATIVE`: that variable turns off the product test suite's shared
    interaction helper, and a journey sharing code with those tests would answer it by
    doing nothing at all, which is the one result this pass must not reward.
    """
    port = closed_port()
    control = dict(env)
    control["MMW_JOURNEY_NEGATIVE"] = "1"
    for key in data:
        name = str(key).upper()
        moved = repointed(control.get(name, ""), port)
        if moved is not None:
            control[name] = moved
    return control


def run_named(name: str, start: Path | None = None) -> int:
    root = repo_root(start)
    try:
        env = command_env(root)
        cfg = target_config(root)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2

    def bail(message: str | None = None,
             proc: subprocess.CompletedProcess | None = None) -> int:
        stop(cfg, root, env)
        if proc is not None:
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
        elif message:
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

    # The product is down and the addresses point nowhere. A journey that reached it
    # cannot pass this; one that asserted nothing passes it exactly as it passed above,
    # which is the whole difference the run is here to print.
    control = attempt(negative_env(env, data))
    if control.returncode == 0:
        print(f"JOURNEY GREEN WITHOUT PRODUCT {name} at "
              f"{last_line(control.stdout + control.stderr)} — it passed again with the "
              f"product stopped and its addresses pointing nowhere. Make the journey "
              f"assert something only the running product can satisfy.")
        return 1
    print(f"JOURNEY OK {name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] != "run":
        sys.stderr.write("usage: journey.py run <name>\n")
        return 2
    return run_named(argv[1])


if __name__ == "__main__":
    sys.exit(main())
