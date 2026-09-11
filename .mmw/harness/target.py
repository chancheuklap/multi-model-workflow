#!/usr/bin/env python3
"""Lease-aware start, stop, and discovery commands for the local board."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def state_path() -> Path:
    raw = os.environ.get("MMW_DATA_DIR")
    if not raw:
        raise SystemExit("MMW_DATA_DIR is missing; run this command through lease.py")
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


def owns(state: dict) -> bool:
    pid = state.get("pid")
    if not isinstance(pid, int):
        return False
    command = subprocess.run(["ps", "-p", str(pid), "-o", "command="], text=True,
                             capture_output=True).stdout
    return bool(state.get("server")) and state["server"] in command


def start() -> int:
    port_raw = os.environ.get("MMW_PORT_BASE")
    if not port_raw:
        sys.stderr.write("MMW_PORT_BASE is missing; run this command through lease.py\n")
        return 2
    port = int(port_raw)
    origin = f"http://127.0.0.1:{port}"
    old = read_state()
    if old and old.get("origin") == origin and owns(old) and answering(origin):
        return 0
    if old:
        stop()
    probe = socket.socket()
    try:
        probe.bind(("127.0.0.1", port))
    except OSError as exc:
        sys.stderr.write(f"127.0.0.1:{port} is already occupied ({exc}); stop its owner or take another lease\n")
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
        if answering(origin):
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
    if not state or not answering(state.get("origin", "")):
        sys.stderr.write("this lease has no answering board; run the target start command\n")
        return 2
    print(json.dumps({"origin": state["origin"], "instance": state["instance"],
                      "instance_check": "dom:[data-board-root]"}))
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"start", "stop", "discover"}:
        sys.stderr.write("usage: target.py start|stop|discover\n")
        return 2
    return {"start": start, "stop": stop, "discover": discover}[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
