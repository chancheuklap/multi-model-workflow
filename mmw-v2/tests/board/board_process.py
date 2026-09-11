"""Run the real task-board server behind reusable HTTP test helpers."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"


class RunningBoard:
    def __init__(self, *, environment=None, fixture=None):
        self.environment = dict(environment or {})
        self.fixture = fixture

    def __enter__(self):
        self.temp = None
        self.directory = None
        if self.fixture is not None:
            self.temp = tempfile.TemporaryDirectory()
            self.directory = Path(self.temp.name)
            self.write_fixture(self.fixture)
            self.environment["MMW_BOARD_FAKE_DIR"] = str(self.directory)
        env = os.environ.copy()
        env.update({key: str(value) for key, value in self.environment.items()})
        self.process = subprocess.Popen(
            ["python3", "-u", str(SERVER), "--port", "0"], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.origin = self.process.stdout.readline().strip()
        if not self.origin.startswith("http://127.0.0.1:"):
            raise RuntimeError(self.process.stderr.read())
        _, page = self.request("GET", "/")
        match = re.search(r'name="mmw-page-token" content="([^"]+)"', page)
        if not match:
            raise RuntimeError("board page did not contain mmw-page-token")
        self.token = match.group(1)
        return self

    def __exit__(self, *args):
        self.process.terminate()
        self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()
        if self.temp:
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
