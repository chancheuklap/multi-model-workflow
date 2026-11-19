from __future__ import annotations

import contextlib
import json
import os
import socket
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / ".mmw" / "harness" / "target.py"
GH = ROOT / ".mmw" / "harness" / "bin" / "gh"
GH_RESPONSES = ROOT / ".mmw" / "harness" / "github" / "responses.json"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def request_json(origin, method, path, payload=None, token=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Origin"] = origin
        headers["X-MMW-Token"] = token
    request = urllib.request.Request(origin + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, json.loads(response.read())


@contextlib.contextmanager
def running_target(*, armed_break=""):
    with tempfile.TemporaryDirectory() as directory:
        data_dir = Path(directory)
        env = os.environ.copy()
        env.update({
            "MMW_DATA_DIR": str(data_dir),
            "MMW_PORT_BASE": str(free_port()),
            "MMW_INSTANCE": "board-harness-test",
        })
        if armed_break:
            env["MMW_BREAK"] = armed_break
        else:
            env.pop("MMW_BREAK", None)
        started = subprocess.run(
            ["python3", str(TARGET), "start"], cwd=ROOT, env=env,
            text=True, capture_output=True,
        )
        if started.returncode != 0:
            raise AssertionError(started.stderr or started.stdout)
        state = json.loads((data_dir / "board-process.json").read_text())
        try:
            yield data_dir, env, state, started.stdout
        finally:
            stopped = subprocess.run(
                ["python3", str(TARGET), "stop"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
            if stopped.returncode != 0:
                raise AssertionError(stopped.stderr or stopped.stdout)


class HarnessTest(unittest.TestCase):
    def test_fake_gh_reads_exact_fixture_and_records_every_call(self):
        with tempfile.TemporaryDirectory() as data_dir:
            env = {**os.environ, "MMW_DATA_DIR": data_dir}
            known = subprocess.run([str(GH), "api", "test"], env=env, text=True,
                                   capture_output=True)
            self.assertEqual((known.returncode, known.stdout), (0, "fixture-ok\n"))
            missing = subprocess.run([str(GH), "api", "unknown"], env=env, text=True,
                                     capture_output=True)
            self.assertEqual(missing.returncode, 2)
            self.assertIn("no gh response", missing.stderr)
            calls = (Path(data_dir) / "gh-calls").read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls, [
                json.dumps(["api", "test"], separators=(",", ":")),
                json.dumps(["api", "unknown"], separators=(",", ":")),
            ])

    def test_start_gives_the_board_its_own_mmw_home(self):
        machine = Path.home() / ".mmw" / "models.json"
        before = (machine.exists(), machine.read_bytes() if machine.exists() else None,
                  machine.stat().st_mtime_ns if machine.exists() else None)
        with running_target() as (data_dir, _env, state, _stdout):
            private_home = Path(state["mmw_home"])
            self.assertTrue(private_home.is_relative_to(data_dir))
            self.assertTrue((private_home / "models.json").is_file())
            status, settings = request_json(state["origin"], "GET", "/api/settings")
            self.assertEqual(status, 200)
            self.assertEqual(settings["version"], 1)
        after = (machine.exists(), machine.read_bytes() if machine.exists() else None,
                 machine.stat().st_mtime_ns if machine.exists() else None)
        self.assertEqual(after, before)

    def test_start_returns_only_after_fixture_tasks_are_read(self):
        with running_target() as (_data_dir, _env, state, _stdout):
            status, board = request_json(state["origin"], "GET", "/api/board")
        self.assertEqual(status, 200)
        self.assertNotIn("read_failed", board)
        self.assertTrue(board["tasks"])

    def test_start_refuses_and_names_an_unanswered_gh_call(self):
        missing_call = ["repo", "view", "--json", "nameWithOwner", "--jq",
                        ".nameWithOwner"]
        missing_key = json.dumps(missing_call, separators=(",", ":"))
        catalog = json.loads(GH_RESPONSES.read_text(encoding="utf-8"))
        catalog.pop(missing_key, None)
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            (data_dir / "github-responses.json").write_text(
                json.dumps(catalog) + "\n", encoding="utf-8"
            )
            env = {
                **os.environ,
                "MMW_DATA_DIR": str(data_dir),
                "MMW_PORT_BASE": str(free_port()),
                "MMW_INSTANCE": "board-harness-missing-answer",
            }
            started = subprocess.run(
                ["python3", str(TARGET), "start"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
            subprocess.run(
                ["python3", str(TARGET), "stop"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
        self.assertNotEqual(started.returncode, 0)
        self.assertIn(missing_key, started.stderr)

    def test_start_offers_every_saved_cell(self):
        with running_target() as (_data_dir, _env, state, _stdout):
            status, settings = request_json(state["origin"], "GET", "/api/settings")
        self.assertEqual(status, 200)
        offered = settings["scan"]["hosts"]
        for role, row in settings["rows"].items():
            models = {item["model"]: item["efforts"]
                      for item in offered[row["host"]]["offered"]}
            self.assertIn(row["model"], models, role)
            self.assertIn(row["effort"], models[row["model"]], role)

    def test_start_offers_a_second_value_for_one_cell(self):
        with running_target() as (_data_dir, _env, state, _stdout):
            status, settings = request_json(state["origin"], "GET", "/api/settings")
        self.assertEqual(status, 200)
        hosts = settings["scan"]["hosts"]
        alternatives = []
        for row in settings["rows"].values():
            offered = hosts[row["host"]]["offered"]
            models = {item["model"]: item["efforts"] for item in offered}
            alternatives.append(len(models) > 1 or len(models.get(row["model"], [])) > 1)
        self.assertIn(True, alternatives)

    def test_start_arms_only_the_named_interface(self):
        broken = "PUT /api/settings"
        with running_target(armed_break=broken) as (_data_dir, _env, state, stdout):
            self.assertIn(f"BREAK ARMED {broken}", stdout)
            get_status, settings = request_json(state["origin"], "GET", "/api/settings")
            put_status, body = request_json(
                state["origin"], "PUT", "/api/settings", settings, state["token"],
            )
        self.assertEqual(get_status, 200)
        self.assertEqual(put_status, 503)
        self.assertIn(broken, body["error"])

    def test_start_succeeds_immediately_after_stop_following_page_traffic(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            env = {
                **os.environ,
                "MMW_DATA_DIR": str(data_dir),
                "MMW_PORT_BASE": str(free_port()),
                "MMW_INSTANCE": "board-harness-restart",
            }
            first = subprocess.run(
                ["python3", str(TARGET), "start"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            state = json.loads((data_dir / "board-process.json").read_text())
            for path in ("/", "/app.mjs", "/styles/tokens.css") * 3:
                with urllib.request.urlopen(state["origin"] + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    response.read()
            stopped = subprocess.run(
                ["python3", str(TARGET), "stop"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
            self.assertEqual(stopped.returncode, 0, stopped.stderr)
            restarted = subprocess.run(
                ["python3", str(TARGET), "start"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
            try:
                self.assertEqual(restarted.returncode, 0, restarted.stderr)
            finally:
                subprocess.run(
                    ["python3", str(TARGET), "stop"], cwd=ROOT, env=env,
                    text=True, capture_output=True,
                )

    def test_start_still_refuses_a_real_listener(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            env = {
                **os.environ,
                "MMW_DATA_DIR": directory,
                "MMW_PORT_BASE": str(port),
                "MMW_INSTANCE": "board-harness-held-port",
            }
            started = subprocess.run(
                ["python3", str(TARGET), "start"], cwd=ROOT, env=env,
                text=True, capture_output=True,
            )
        self.assertNotEqual(started.returncode, 0)
        self.assertIn(f"127.0.0.1:{port} is held by", started.stderr)


if __name__ == "__main__":
    unittest.main()
