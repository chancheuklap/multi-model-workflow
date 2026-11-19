#!/usr/bin/env python3
"""Run this checkout's task board on 127.0.0.1 with its own MMW_HOME, never the machine's ~/.mmw.

  board-instance.py serve --port N [--prototype MODULE] [--real-catalog]
      Foreground. A fresh MMW_HOME seeded from scripts/dev/board-fixtures/; the e2e runner starts this.
  board-instance.py up [--prototype MODULE] [--real-catalog] [--fresh]
      Background instance of this checkout, kept for trying by hand. Reuses a live one; prints
      `READY <url>`. Its MMW_HOME is .board-dev/home/, kept across restarts; --fresh reseeds it.
  board-instance.py down
      Stops this checkout's background instance.

Every `up` first stops the instances of checkouts that no longer exist (registry under
~/.local/state/mmw-board-dev/). Ticket state is read from GitHub with this machine's `gh`, read only.
--prototype MODULE mounts the prototype at MODULE (a path under efforts/); without it the product runs.
Host model catalogs come from board-fixtures/host-catalog.json unless --real-catalog asks the host CLIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "scripts" / "dev" / "board-fixtures"
SERVER = ROOT / "mmw-v4" / "board" / "server.py"
STATE = ROOT / ".board-dev"
REGISTRY = Path.home() / ".local" / "state" / "mmw-board-dev"


def seed(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name in ("models.json", "catalog.json"):
        shutil.copyfile(FIXTURES / name, home / name)


def environment(home: Path, prototype: str | None, real_catalog: bool) -> dict[str, str]:
    env = {**os.environ, "MMW_HOME": str(home)}
    env.pop("MMW_BOARD_PROTOTYPE", None)
    env.pop("MMW_HOST_CATALOG", None)
    if not real_catalog:
        env["MMW_HOST_CATALOG"] = str(FIXTURES / "host-catalog.json")
    if prototype:
        if not (ROOT / prototype).is_file():
            sys.exit(f"board-instance: no prototype module at {prototype} in {ROOT}")
        env["MMW_BOARD_PROTOTYPE"] = prototype
    return env


def serve(args) -> int:
    home = Path(tempfile.mkdtemp(prefix="board-serve-", dir=_runs()))
    seed(home)
    env = environment(home, args.prototype, args.real_catalog)
    try:
        return subprocess.call([sys.executable, str(SERVER), "--port", str(args.port)], cwd=ROOT, env=env)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _runs() -> Path:
    path = STATE / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _key() -> str:
    return hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/api/settings", timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def _stop(record: dict) -> None:
    pid = record.get("pid")
    if pid and _alive(pid):
        os.killpg(pid, signal.SIGTERM)


def collect() -> None:
    REGISTRY.mkdir(parents=True, exist_ok=True)
    for path in REGISTRY.glob("*.json"):
        record = json.loads(path.read_text())
        if not Path(record["checkout"]).exists():
            _stop(record)
            path.unlink()
            print(f"board-instance: stopped the instance of deleted checkout {record['checkout']}")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def up(args) -> int:
    collect()
    entry = REGISTRY / f"{_key()}.json"
    record = json.loads(entry.read_text()) if entry.exists() else {}
    wanted = {"prototype": args.prototype, "real_catalog": args.real_catalog}
    url = f"http://127.0.0.1:{record.get('port')}"
    if record and _alive(record["pid"]) and _answers(url) and record.get("mode") == wanted and not args.fresh:
        print(f"READY {url} (reused; MMW_HOME {STATE / 'home'})")
        return 0
    if record:
        _stop(record)
    home = STATE / "home"
    if args.fresh or not (home / "models.json").exists():
        shutil.rmtree(home, ignore_errors=True)
        seed(home)
    port = record.get("port") or _free_port()
    log = STATE / "server.log"
    process = subprocess.Popen(
        [sys.executable, str(SERVER), "--port", str(port)], cwd=ROOT,
        env=environment(home, args.prototype, args.real_catalog),
        stdout=log.open("a"), stderr=subprocess.STDOUT, start_new_session=True)
    url = f"http://127.0.0.1:{port}"
    entry.write_text(json.dumps({"checkout": str(ROOT), "pid": process.pid, "port": port,
                                 "mode": wanted}) + "\n")
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            sys.exit(f"board-instance: the server exited with {process.returncode}; see {log}")
        if _answers(url):
            print(f"READY {url} (MMW_HOME {home}; log {log})")
            return 0
        time.sleep(0.2)
    sys.exit(f"board-instance: {url} did not answer /api/settings within 15 seconds; see {log}")


def down(_args) -> int:
    entry = REGISTRY / f"{_key()}.json"
    if not entry.exists():
        print("board-instance: no instance for this checkout")
        return 0
    _stop(json.loads(entry.read_text()))
    entry.unlink()
    print("board-instance: stopped")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "up"):
        p = sub.add_parser(name)
        p.add_argument("--prototype", metavar="MODULE")
        p.add_argument("--real-catalog", action="store_true")
        if name == "serve":
            p.add_argument("--port", type=int, required=True)
        else:
            p.add_argument("--fresh", action="store_true")
    sub.add_parser("down")
    args = parser.parse_args()
    return {"serve": serve, "up": up, "down": down}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
