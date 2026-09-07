"""journey.py and harness-guard.py: fake start/stop/discover, a real lease registry.

The seam is the command line and the files the commands write. Nothing here stubs
lease.py: a slot is claimed because journey.py claims one, under a MMW_HOME of this
suite's own.
"""

from __future__ import annotations

import atexit
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts"
JOURNEY = SCRIPTS / "journey.py"
GUARD = SCRIPTS / "harness-guard.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "journey"
HOME = tempfile.mkdtemp(prefix="mmw-journey-home-")
atexit.register(shutil.rmtree, HOME, True)


def load(name: str, path: Path):
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location(f"mmw_{name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


jy = load("journey", JOURNEY)
hg = load("harness_guard", GUARD)


def write_exec(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class Repo:
    """A temporary consuming repository with fake start/stop/discover and one journey."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        (self.root / ".mmw").mkdir()
        self.log = self.root / ".mmw" / "order"

    def close(self):
        self.tmp.cleanup()

    def write_target(self, extra=None):
        cfg = {
            "start": str(self.root / ".mmw" / "start.sh"),
            "stop": str(self.root / ".mmw" / "stop.sh"),
            "discover": str(self.root / ".mmw" / "discover.sh"),
            "stories": "true",
            "leaves_machine": [],
        }
        if extra:
            cfg.update(extra)
        (self.root / ".mmw" / "target.json").write_text(
            json.dumps(cfg), encoding="utf-8")

    def write_stack(self, *, start="exit 0", stop=None, discover=None):
        if stop is None:
            stop = "echo stop-ran > .mmw/stop-ran"
        if discover is None:
            discover = 'printf %s \'{"origin":"http://127.0.0.1:9","instance":"t"}\''
        write_exec(self.root / ".mmw" / "start.sh",
                   "#!/bin/sh\n" + f"echo start >> '{self.log}'\n" + start + "\n")
        write_exec(self.root / ".mmw" / "stop.sh",
                   "#!/bin/sh\n" + f"echo stop >> '{self.log}'\n" + stop + "\n")
        write_exec(self.root / ".mmw" / "discover.sh",
                   "#!/bin/sh\n" + f"echo discover >> '{self.log}'\n" + discover + "\n")

    def write_journey(self, name: str, body: str, *, package=False):
        dest = self.root / ".mmw" / "journeys" / name
        dest.mkdir(parents=True, exist_ok=True)
        if package:
            (dest / "package.json").write_text(
                json.dumps({"scripts": {"run": body}}), encoding="utf-8")
            return dest
        write_exec(dest / "run", "#!/bin/sh\n" + body + "\n")
        return dest

    def run(self, name: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        here = Path.cwd()
        os.chdir(self.root)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = jy.main(["run", name])
        finally:
            os.chdir(here)
        return code, out.getvalue(), err.getvalue()


class JourneyOrder(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.repo.write_target()
        self.repo.write_stack()
        self.repo.write_journey(
            "demo",
            f"echo script >> '{self.repo.log}'\n"
            "echo ORIGIN=$ORIGIN MMW_INSTANCE=$MMW_INSTANCE MMW_AUTOMATION=$MMW_AUTOMATION "
            f">> '{self.repo.root / '.mmw' / 'env'}'\n"
            "exit 0",
        )

    def test_start_discover_script_stop_and_lease_and_addresses_reach_the_script(self):
        code, out, _ = self.repo.run("demo")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK demo\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop"])
        env = (self.repo.root / ".mmw" / "env").read_text(encoding="utf-8")
        self.assertIn("ORIGIN=http://127.0.0.1:9", env)
        self.assertIn("MMW_AUTOMATION=1", env)
        self.assertRegex(env, r"MMW_INSTANCE=\S+")
        self.assertTrue((self.repo.root / ".mmw" / "stop-ran").is_file())

    def test_stop_runs_when_the_script_fails(self):
        self.repo.write_journey(
            "demo", "echo first-of-script >&2\necho last-of-script >&2\nexit 7")
        code, out, _ = self.repo.run("demo")
        self.assertEqual(code, 1, out)
        self.assertEqual(out, "JOURNEY FAILED demo at last-of-script\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_start_failure_is_exit_2_and_prints_the_refusal_unchanged(self):
        self.repo.write_stack(start="echo Gateway points elsewhere >&2\nexit 1")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("Gateway points elsewhere", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertNotIn("JOURNEY FAILED", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "stop"])

    def test_a_missing_journey_prints_failed_and_is_exit_1(self):
        code, out, _ = self.repo.run("no-such")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("JOURNEY FAILED no-such at "), out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_a_package_json_run_script_is_the_journey(self):
        self.repo.write_journey(
            "via-npm",
            f"echo script >> '{self.repo.log}'; echo from-package; exit 0",
            package=True,
        )
        code, out, _ = self.repo.run("via-npm")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK via-npm\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop"])


class FixtureRepo(unittest.TestCase):
    """The committed fixture is what AC1 and AC2 run against."""

    def test_the_committed_demo_prints_ok_and_stop_ran(self):
        home = tempfile.mkdtemp(prefix="mmw-journey-ac-")
        self.addCleanup(shutil.rmtree, home, True)
        stop_ran = FIXTURE / "repo" / ".mmw" / "stop-ran"
        stop_ran.unlink(missing_ok=True)
        self.addCleanup(stop_ran.unlink, missing_ok=True)
        proc = subprocess.run(
            [sys.executable, str(JOURNEY), "run", "demo"],
            cwd=FIXTURE / "repo",
            capture_output=True, text=True,
            env={**os.environ, "MMW_HOME": home},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[0], "JOURNEY OK demo")
        self.assertIn("stop-ran", stop_ran.read_text())


class HarnessGuard(unittest.TestCase):
    def test_the_leaky_fixture_names_the_leak_and_not_the_legal_hit(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = hg.main([str(FIXTURE / "leaky")])
        self.assertEqual(code, 1)
        text = out.getvalue()
        self.assertRegex(text, r"^HARNESS LEAK ")
        self.assertIn("src/app.js", text)
        self.assertNotIn("src/note.js", text)
        self.assertNotIn("tests/", text)
        self.assertNotIn("scripts/dev/", text)
        self.assertNotIn("tools/opened.py", text)

    def test_a_clean_repo_prints_ok(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = hg.main([str(FIXTURE / "repo")])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "HARNESS OK\n")


if __name__ == "__main__":
    unittest.main()
