from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SUPERVISOR = ROOT / "mmw-v2" / "board" / "supervisor.py"
FIXTURE_GH = ROOT / "mmw-v2" / "tests" / "board" / "github" / "gh"


def free_port(excluding: set[int] | None = None) -> int:
    import socket
    excluding = excluding or set()
    while True:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        if port not in excluding:
            return port


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.home = self.base / "mmw"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.processes = []
        wrapper = self.bin / "gh"
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import json, os\n"
            "from pathlib import Path\n"
            "mapping=json.loads(os.environ['MMW_TEST_REPO_FIXTURES'])\n"
            "os.environ['MMW_BOARD_FAKE_DIR']=mapping[str(Path.cwd())]\n"
            f"os.execv({str(FIXTURE_GH)!r}, [{str(FIXTURE_GH)!r}, *os.sys.argv[1:]])\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

    def tearDown(self):
        for process, log in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            log.close()
        self.temp.cleanup()

    def repository(self, name: str, slug: str) -> tuple[Path, Path]:
        repository = self.base / name
        repository.mkdir()
        fixture = self.base / f"fixture-{name}"
        fixture.mkdir()
        (fixture / "scenario.json").write_text(json.dumps({
            "repo": slug,
            "maps": [],
            "trees": [],
            "comments": {},
        }), encoding="utf-8")
        return repository, fixture

    def copied_supervisor(self) -> Path:
        """A copy of the board and the scripts it loads, so a test can change the code."""
        ignore = shutil.ignore_patterns("__pycache__", "node_modules")
        copy = self.base / "installed" / "mmw-v2"
        shutil.copytree(ROOT / "mmw-v2" / "board", copy / "board", ignore=ignore)
        for skill in ("dispatch", "verify-ticket"):
            shutil.copytree(ROOT / "mmw-v2" / "skills" / skill / "scripts",
                            copy / "skills" / skill / "scripts", ignore=ignore)
        return copy / "board" / "supervisor.py"

    def start(self, registry: dict[Path, int], fixtures: dict[Path, Path],
              supervisor: Path = SUPERVISOR):
        (self.home / "boards.json").write_text(json.dumps({
            str(path): port for path, port in registry.items()
        }), encoding="utf-8")
        log_path = self.base / f"supervisor-{len(self.processes)}.log"
        log = log_path.open("w+", encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "MMW_HOME": str(self.home),
            "PATH": str(self.bin) + os.pathsep + env["PATH"],
            "MMW_TEST_REPO_FIXTURES": json.dumps({
                str(path.resolve()): str(fixture) for path, fixture in fixtures.items()
            }),
        })
        process = subprocess.Popen(
            [sys.executable, "-u", str(supervisor), "--interval", "0.05"],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        self.processes.append((process, log))
        return process, log

    def board(self, port: int) -> dict:
        deadline = time.monotonic() + 10
        last = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/board",
                                            timeout=0.5) as response:
                    return json.load(response)
            except Exception as exc:
                last = exc
                time.sleep(0.05)
        self.fail(f"board on {port} did not answer: {last}")

    @staticmethod
    def child_pid(parent: int, port: int) -> int | None:
        output = subprocess.check_output(["ps", "-axo", "pid=,ppid=,command="], text=True)
        suffix = f"server.py --port {port}"
        for line in output.splitlines():
            fields = line.strip().split(None, 2)
            if len(fields) == 3 and int(fields[1]) == parent and suffix in fields[2]:
                return int(fields[0])
        return None

    def test_starts_a_board_per_registered_repo(self):
        first, first_fixture = self.repository("first", "fixture/first")
        second, second_fixture = self.repository("second", "fixture/second")
        first_port = free_port()
        second_port = free_port({first_port})
        self.start({first: first_port, second: second_port},
                   {first: first_fixture, second: second_fixture})
        self.assertEqual(self.board(first_port)["repo"], "fixture/first")
        self.assertEqual(self.board(second_port)["repo"], "fixture/second")

    def test_restarts_a_board_that_exits(self):
        repository, fixture = self.repository("repo", "fixture/restarted")
        port = free_port()
        supervisor, _ = self.start({repository: port}, {repository: fixture})
        self.board(port)
        old_pid = self.child_pid(supervisor.pid, port)
        self.assertIsNotNone(old_pid)
        os.kill(old_pid, signal.SIGTERM)
        deadline = time.monotonic() + 10
        new_pid = None
        while time.monotonic() < deadline:
            candidate = self.child_pid(supervisor.pid, port)
            if candidate is not None and candidate != old_pid:
                new_pid = candidate
                break
            time.sleep(0.05)
        self.assertIsNotNone(new_pid)
        self.assertEqual(self.board(port)["repo"], "fixture/restarted")

    def wait_for_new_child(self, supervisor: int, port: int, old_pid: int) -> int:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            candidate = self.child_pid(supervisor, port)
            if candidate is not None and candidate != old_pid:
                return candidate
            time.sleep(0.05)
        self.fail(f"no new board replaced pid {old_pid} on port {port}")

    def test_runs_the_new_code_after_the_installed_files_change(self):
        repository, fixture = self.repository("repo", "fixture/updated")
        port = free_port()
        copy = self.copied_supervisor()
        supervisor, log = self.start({repository: port}, {repository: fixture}, copy)
        self.board(port)
        old_pid = self.child_pid(supervisor.pid, port)
        self.assertIsNotNone(old_pid)
        events = copy.parents[1] / "skills" / "verify-ticket" / "scripts" / "events.py"
        events.write_text(events.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        new_pid = self.wait_for_new_child(supervisor.pid, port, old_pid)
        self.assertEqual(self.board(port)["repo"], "fixture/updated")
        self.assertIsNone(supervisor.poll(), "the supervisor must replace itself, not exit")
        log.flush()
        log.seek(0)
        self.assertIn("restarting the supervisor", log.read())
        with self.assertRaises(ProcessLookupError):
            os.kill(old_pid, 0)
        self.assertNotEqual(new_pid, old_pid)

    def test_a_board_started_outside_the_supervisor_exits_when_its_code_changes(self):
        repository, fixture = self.repository("repo", "fixture/orphan")
        copy = self.copied_supervisor()
        port = free_port()
        env = os.environ.copy()
        env.update({"MMW_HOME": str(self.home), "PATH": str(self.bin) + os.pathsep + env["PATH"],
                    "MMW_TEST_REPO_FIXTURES": json.dumps({str(repository.resolve()): str(fixture)})})
        log = (self.base / "server.log").open("w+", encoding="utf-8")
        server = subprocess.Popen(
            [sys.executable, "-u", str(copy.with_name("server.py")), "--port", str(port),
             "--watch-interval", "0.05"],
            cwd=repository, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        self.processes.append((server, log))
        self.assertEqual(self.board(port)["repo"], "fixture/orphan")
        gates = copy.with_name("gates.py")
        gates.write_text(gates.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        self.assertEqual(server.wait(timeout=10), 0)

    def test_skips_a_missing_repository(self):
        repository, fixture = self.repository("present", "fixture/present")
        missing = self.base / "missing-repository"
        port = free_port()
        _, log = self.start({repository: port, missing: free_port()}, {repository: fixture})
        self.assertEqual(self.board(port)["repo"], "fixture/present")
        deadline = time.monotonic() + 5
        text = ""
        while time.monotonic() < deadline:
            log.flush()
            log.seek(0)
            text = log.read()
            if str(missing) in text:
                break
            time.sleep(0.05)
        self.assertIn(str(missing), text)


if __name__ == "__main__":
    unittest.main()
