"""Run the real task-board server behind reusable HTTP test helpers."""

from __future__ import annotations

import json
import os
import re
import select
import sys
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v5" / "board" / "server.py"
FAKE_BIN = Path(__file__).resolve().parent / "github"


class RunningBoard:
    def __init__(self, *, environment=None, fixture=None, server=SERVER, repository=None):
        self.environment = dict(environment or {})
        self.fixture = fixture if fixture is not None else {"maps": [], "specs": [], "trees": [], "comments": {}}
        self.server_script = Path(server)
        self.repository = Path(repository) if repository is not None else None

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.directory = self.base / "fixture"
        self.write_fixture(self.fixture)
        catalog = self.base / "catalog.json"
        catalog.write_text(json.dumps({"cli": {}, "paseo": {}, "codex-app": {}}))
        env = os.environ.copy()
        env.update({"HOME": str(self.base / "user"), "MMW_HOME": str(self.base / "mmw-v5"),
                    "MMW_HOST_CATALOG": str(catalog), "MMW_BOARD_FAKE_DIR": str(self.directory),
                    "PATH": str(FAKE_BIN) + os.pathsep + env.get("PATH", "")})
        env.update({key: str(value) for key, value in self.environment.items()})
        Path(env["HOME"]).mkdir(parents=True, exist_ok=True)
        Path(env["MMW_HOME"]).mkdir(parents=True, exist_ok=True)
        repository = self.repository or self.base / "repository"
        repository.mkdir(parents=True, exist_ok=True)
        if not (repository / ".git").exists():
            subprocess.run(["git", "init", "-q", str(repository)], check=True, env=env)
            subprocess.run(["git", "-C", str(repository), "remote", "add", "origin",
                            "https://github.test/fixture/board.git"], check=True, env=env)
        self.process = subprocess.Popen(
            [sys.executable, "-u", str(self.server_script), "--port", "0"], cwd=repository, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            ready, _, _ = select.select([self.process.stdout], [], [], 10)
            if not ready:
                raise RuntimeError("board did not print a listening URL within ten seconds")
            self.origin = self.process.stdout.readline().strip()
            if not self.origin.startswith("http://127.0.0.1:"):
                raise RuntimeError(self.process.stderr.read())
            _, page = self.request("GET", "/")
            match = re.search(r'name="mmw-page-token" content="([^\"]+)"', page)
            if not match:
                raise RuntimeError("board page did not contain mmw-page-token")
            self.token = match.group(1)
            return self
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *args):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()
        self.temp.cleanup()

    @property
    def write_headers(self):
        return {"Origin": self.origin, "X-MMW-Token": self.token}

    def request(self, method="GET", path="/api/board", payload=None, headers=None):
        data = None if payload is None else json.dumps(payload).encode()
        request_headers = dict(headers or {})
        if data is not None:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.origin + path, data=data, headers=request_headers, method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.read().decode()

    def write_fixture(self, fixture):
        self.fixture = fixture
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "scenario.json").write_text(json.dumps(fixture))

    def fixture_calls(self):
        path = self.directory / "calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def fixture_state(self):
        return json.loads((self.directory / "state.json").read_text())
