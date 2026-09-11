#!/usr/bin/env python3
"""Lease-aware start, stop, and discovery commands for the local board."""

from __future__ import annotations

import json
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def start_command() -> str:
    return "python3 .mmw/harness/target.py start"


def lease_command() -> str:
    lease = "lease.py"
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / "lease.py"
        if candidate.is_file():
            lease = str(candidate.resolve())
            break
    return f"python3 {shlex.quote(lease)} run -- {start_command()}"


def missing_lease(name: str) -> str:
    return f"{name} is unset. Run: {lease_command()}"


def state_path() -> Path:
    raw = os.environ.get("MMW_DATA_DIR")
    if not raw:
        raise SystemExit(missing_lease("MMW_DATA_DIR"))
    path = Path(raw)
    path.mkdir(parents=True, exist_ok=True)
    return path / "board-process.json"


def read_state() -> dict | None:
    path = state_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def answering(origin: str) -> bool:
    try:
        with urllib.request.urlopen(origin, timeout=0.5) as response:
            return response.status == 200
    except OSError:
        return False


def page_token(origin: str) -> str | None:
    try:
        with urllib.request.urlopen(origin, timeout=0.5) as response:
            body = response.read().decode("utf-8")
    except OSError:
        return None
    match = re.search(r'<meta name="mmw-page-token" content="([^"]+)">', body)
    return match.group(1) if match else None


def owns(state: dict) -> bool:
    pid = state.get("pid")
    if not isinstance(pid, int):
        return False
    command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], text=True,
                             capture_output=True).stdout
    return bool(state.get("server")) and state["server"] in command


def port_holder(port: int) -> str:
    try:
        found = subprocess.run(
            ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fpc"],
            text=True, capture_output=True,
        )
    except FileNotFoundError:
        return "a process that this machine cannot identify because lsof is unavailable"
    pid = command = None
    for line in found.stdout.splitlines():
        if line.startswith("p"):
            pid = line[1:]
        elif line.startswith("c"):
            command = line[1:]
    if pid:
        return f"PID {pid} ({command or 'unknown command'})"
    return "a process that lsof could not identify"


def start() -> int:
    port_raw = os.environ.get("MMW_PORT_BASE")
    if not port_raw:
        sys.stderr.write(missing_lease("MMW_PORT_BASE") + "\n")
        return 2
    port = int(port_raw)
    origin = f"http://127.0.0.1:{port}"
    old = read_state()
    if (old and old.get("origin") == origin and owns(old)
            and old.get("token") == page_token(origin)):
        return 0
    if old:
        stop()
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", port))
    except OSError as exc:
        holder = port_holder(port)
        sys.stderr.write(
            f"127.0.0.1:{port} is held by {holder} ({exc}). Stop that PID, then rerun {start_command()}\n"
        )
        return 2
    finally:
        probe.close()

    env = os.environ.copy()
    env["PATH"] = str(ROOT / ".mmw" / "harness" / "bin") + os.pathsep + env.get("PATH", "")
    env["MMW_HOST_CATALOG"] = str(ROOT / ".mmw" / "harness" / "catalog.json")
    log_path = state_path().with_name("board.log")
    log = log_path.open("ab")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "mmw-v2" / "board" / "server.py"), "--port", str(port)],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    log.close()
    instance = os.environ.get("MMW_INSTANCE", f"board-{port}")
    state_path().write_text(json.dumps({"pid": process.pid, "origin": origin, "instance": instance,
                                       "server": str(ROOT / "mmw-v2" / "board" / "server.py")}) + "\n",
                            encoding="utf-8")
    for _ in range(50):
        token = page_token(origin)
        if token:
            current = read_state()
            current["token"] = token
            state_path().write_text(json.dumps(current) + "\n", encoding="utf-8")
            return 0
        if process.poll() is not None:
            sys.stderr.write(f"board exited {process.returncode}; read {log_path}\n")
            return 2
        time.sleep(0.1)
    sys.stderr.write(f"board did not answer at {origin}; read {log_path}\n")
    return 2


def stop() -> int:
    state = read_state()
    if not state:
        return 0
    pid = state.get("pid")
    if isinstance(pid, int):
        try:
            if owns(state):
                os.killpg(pid, signal.SIGTERM)
                for _ in range(30):
                    try:
                        os.kill(pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(0.05)
        except ProcessLookupError:
            pass
    state_path().unlink(missing_ok=True)
    return 0


def discover() -> int:
    state = read_state()
    actual_token = page_token(state.get("origin", "")) if state else None
    if not state or not owns(state) or not actual_token or actual_token != state.get("token"):
        fact = (f"the record at {state_path()} names PID {state.get('pid')} and token "
                f"{state.get('token')!r}" if state else f"no process record exists at {state_path()}")
        sys.stderr.write(f"discover found {fact}, but no matching board answers. Run: {start_command()}\n")
        return 2
    print(json.dumps({"origin": state["origin"], "instance": state["instance"],
                      "instance_check": f'dom:meta[name="mmw-page-token"][content="{actual_token}"]',
                      "instance_token": actual_token}))
    return 0


def main() -> int:
    commands = {"start": start, "stop": stop, "discover": discover}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.stderr.write("usage: target.py start|stop|discover\n")
        return 2
    return commands[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
