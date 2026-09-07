#!/usr/bin/env python3
"""Run one named journey against this repository's product.

    journey.py run <name>

Claims or reuses this worktree's lease, runs `.mmw/target.json`'s `start` every
time, runs `discover` and puts the printed addresses plus the lease variables
into the environment, runs `<journeys>/<name>` (a `run` executable, or the
command `package.json` declares), and runs `stop` whether the script succeeded
or not.

    JOURNEY OK <name>                         exit 0
    JOURNEY FAILED <name> at <last line>      exit 1
    start's own refusal, unchanged            exit 2
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lease import leased_environment, worktree_of  # noqa: E402

DEFAULT_JOURNEYS = ".mmw/journeys"


def find_repo(start: Path | None = None) -> Path:
    """The directory that holds `.mmw/target.json`, walking up from `start`."""
    here = (start or Path.cwd()).resolve()
    for path in (here, *here.parents):
        if (path / ".mmw" / "target.json").is_file():
            return path
    raise SystemExit(
        f"no .mmw/target.json above {here}: the repository has not said how "
        f"its product is started. Run `screen_driver.py target --check`."
    )


def load_target(root: Path) -> dict:
    path = root / ".mmw" / "target.json"
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{path} cannot be read as JSON: {exc}")
    if not isinstance(cfg, dict):
        raise SystemExit(f"{path} must hold one JSON object")
    return cfg


def last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def run_declared(command: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        shlex.split(command), cwd=cwd, capture_output=True, text=True, env=env,
    )


def stop(cfg: dict, root: Path, env: dict[str, str]) -> None:
    command = cfg.get("stop")
    if not command:
        return
    subprocess.run(shlex.split(command), cwd=root, capture_output=True, text=True, env=env)


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
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = str(value)
        env[str(key)] = rendered
        env[str(key).upper()] = rendered


def run_named(name: str, start: Path | None = None) -> int:
    root = find_repo(start)
    cfg = load_target(root)
    env = dict(os.environ)
    env.update(leased_environment(worktree_of(root)))

    start_cmd = cfg.get("start")
    if not isinstance(start_cmd, str) or not start_cmd.strip():
        print("`.mmw/target.json` has no `start` command", file=sys.stderr)
        return 2

    started = run_declared(start_cmd, root, env)
    if started.returncode != 0:
        stop(cfg, root, env)
        if started.stdout:
            sys.stdout.write(started.stdout)
        if started.stderr:
            sys.stderr.write(started.stderr)
        return 2

    discover_cmd = cfg.get("discover")
    if not isinstance(discover_cmd, str) or not discover_cmd.strip():
        stop(cfg, root, env)
        print("`.mmw/target.json` has no `discover` command", file=sys.stderr)
        return 2
    discovered = run_declared(discover_cmd, root, env)
    if discovered.returncode != 0:
        stop(cfg, root, env)
        if discovered.stdout:
            sys.stdout.write(discovered.stdout)
        if discovered.stderr:
            sys.stderr.write(discovered.stderr)
        return 2
    try:
        data = json.loads(discovered.stdout.strip())
    except json.JSONDecodeError as exc:
        stop(cfg, root, env)
        print(f"discover printed no JSON object: {discovered.stdout[:200]!r} ({exc})",
              file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        stop(cfg, root, env)
        print("discover must print one JSON object", file=sys.stderr)
        return 2
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
