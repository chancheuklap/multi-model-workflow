#!/usr/bin/env python3
"""Run one named journey against this repository's product.

    journey.py run <name>

Claims or reuses this worktree's lease, runs `.mmw/target.json`'s `start` every
time, runs `discover` and puts each printed address into the environment under
its uppercase key (plus the lease variables), runs `<journeys>/<name>` (a `run`
executable, or the command `package.json` declares), and runs `stop` whether
the script succeeded or not.

    JOURNEY OK <name>                         exit 0
    JOURNEY FAILED <name> at <last line>      exit 1
    start's own refusal, unchanged            exit 2
"""

from __future__ import annotations

import json
import os
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


def run_named(name: str, start: Path | None = None) -> int:
    root = repo_root(start)
    env = command_env(root)
    try:
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

    started = run_command(start_cmd, root, env=env, check=False)
    if started.returncode != 0:
        return bail(proc=started)

    try:
        data = discover(cfg, root)
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
    try:
        script = subprocess.run(
            spec, shell=isinstance(spec, str), cwd=dest,
            capture_output=True, text=True, env=env,
        )
    finally:
        stop(cfg, root, env)

    if script.returncode == 0:
        print(f"JOURNEY OK {name}")
        return 0
    print(f"JOURNEY FAILED {name} at {last_line(script.stdout + script.stderr)}")
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] != "run":
        sys.stderr.write("usage: journey.py run <name>\n")
        return 2
    return run_named(argv[1])


if __name__ == "__main__":
    sys.exit(main())
