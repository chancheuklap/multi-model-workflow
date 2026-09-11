#!/usr/bin/env python3
"""Keep one local task-board server running for every registered repository."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


SERVER = Path(__file__).resolve().with_name("server.py")
FIRST_PORT = 47100


def mmw_home() -> Path:
    return Path(os.environ.get("MMW_HOME") or Path.home() / ".mmw").expanduser()


def registry_path() -> Path:
    return mmw_home() / "boards.json"


def read_registry(path: Path | None = None) -> dict[str, int]:
    path = path or registry_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    result: dict[str, int] = {}
    for repository, port in value.items():
        if not isinstance(repository, str) or not repository or not isinstance(port, int):
            raise ValueError(f"{path} entries must map repository paths to integer ports")
        if not 1 <= port <= 65535:
            raise ValueError(f"{path} has invalid port {port!r} for {repository!r}")
        result[repository] = port
    return result


def port_available(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def port_answers(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def _replace_registry(path: Path, registry: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    scratch = path.with_name(path.name + ".tmp")
    fd = os.open(scratch, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(registry, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(scratch, path)


def register_repository(repository: Path) -> int:
    repository = repository.resolve()
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        registry = read_registry(path)
        key = str(repository)
        if key in registry:
            return registry[key]
        registered = set(registry.values())
        for port in range(FIRST_PORT, 65536):
            if port not in registered and port_available(port):
                registry[key] = port
                _replace_registry(path, registry)
                return port
    raise RuntimeError(f"no unregistered port is available from {FIRST_PORT} through 65535")


class Supervisor:
    def __init__(self, interval: float):
        self.interval = interval
        self.processes: dict[str, subprocess.Popen] = {}
        self.missing_reported: set[str] = set()
        self.stopping = False

    def stop(self, *_args) -> None:
        self.stopping = True

    def _start(self, repository: str, port: int) -> None:
        process = subprocess.Popen(
            [sys.executable, "-u", str(SERVER), "--port", str(port)],
            cwd=repository,
        )
        self.processes[repository] = process
        print(f"started task board for {repository} on 127.0.0.1:{port} as pid {process.pid}",
              flush=True)

    def reconcile(self) -> None:
        registry = read_registry()
        for repository, process in list(self.processes.items()):
            code = process.poll()
            if code is not None:
                print(f"task board for {repository} exited {code}; restarting", flush=True)
                del self.processes[repository]
        for repository, port in registry.items():
            if not Path(repository).is_dir():
                if repository not in self.missing_reported:
                    print(f"skipping missing repository {repository}", flush=True)
                    self.missing_reported.add(repository)
                continue
            self.missing_reported.discard(repository)
            if repository in self.processes or port_answers(port):
                continue
            self._start(repository, port)

    def shutdown(self) -> None:
        for process in self.processes.values():
            if process.poll() is None:
                process.terminate()
        for process in self.processes.values():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        try:
            while not self.stopping:
                try:
                    self.reconcile()
                except ValueError as exc:
                    print(f"supervisor: {exc}", file=sys.stderr, flush=True)
                time.sleep(self.interval)
        finally:
            self.shutdown()
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--register", type=Path, metavar="MAIN_CHECKOUT")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.register is not None:
        try:
            print(register_repository(args.register))
            return 0
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"supervisor: {exc}", file=sys.stderr)
            return 1
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    return Supervisor(args.interval).run()


if __name__ == "__main__":
    sys.exit(main())
