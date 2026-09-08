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
        self.repo.write_journey("demo", self.reaches_the_product)

    # No fake stack has a product to reach, so a journey here depends on the product the
    # only way it can: on the address `discover` printed. The control pass moves that
    # address, so this script goes red there exactly as a real journey would.
    ADDRESS = "http://127.0.0.1:9"

    @property
    def reaches_the_product(self) -> str:
        return (f"echo script >> '{self.repo.log}'\n"
                "echo ORIGIN=$ORIGIN origin=[$origin] "
                "MMW_INSTANCE=$MMW_INSTANCE MMW_AUTOMATION=$MMW_AUTOMATION "
                f">> '{self.repo.root / '.mmw' / 'env'}'\n"
                f'[ "$ORIGIN" = "{self.ADDRESS}" ] || exit 9\n'
                "exit 0")

    def test_start_discover_script_stop_control_and_addresses_reach_the_script(self):
        code, out, _ = self.repo.run("demo")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK demo\n")
        # The control pass is the trailing `script`: it runs after `stop`, so the product
        # is already down when it runs.
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop", "script"])
        env = (self.repo.root / ".mmw" / "env").read_text(encoding="utf-8")
        self.assertIn("ORIGIN=http://127.0.0.1:9", env)
        self.assertIn("origin=[]", env)
        self.assertIn("MMW_AUTOMATION=1", env)
        self.assertRegex(env, r"MMW_INSTANCE=\S+")
        self.assertTrue((self.repo.root / ".mmw" / "stop-ran").is_file())

    def test_stop_sees_the_discovered_addresses(self):
        stop_env = self.repo.root / ".mmw" / "stop-env"
        self.repo.write_stack(
            stop=(
                f"echo ORIGIN=$ORIGIN MMW_INSTANCE=$MMW_INSTANCE >> '{stop_env}'\n"
                "echo stop-ran > .mmw/stop-ran"
            ),
        )
        code, out, _ = self.repo.run("demo")
        self.assertEqual(code, 0, out)
        env = stop_env.read_text(encoding="utf-8")
        self.assertIn("ORIGIN=http://127.0.0.1:9", env)
        self.assertRegex(env, r"MMW_INSTANCE=\S+")

    def test_stop_runs_when_the_script_fails(self):
        self.repo.write_journey(
            "demo", "echo first-of-script >&2\necho last-of-script >&2\nexit 7")
        code, out, _ = self.repo.run("demo")
        self.assertEqual(code, 1, out)
        self.assertEqual(out, "JOURNEY FAILED demo at last-of-script\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_a_failing_stop_does_not_replace_the_journey_verdict(self):
        self.repo.write_stack(stop="echo stop-broke >&2\nexit 3")
        self.repo.write_journey(
            "demo", "echo last-of-script >&2\nexit 7")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 1, err)
        self.assertEqual(out, "JOURNEY FAILED demo at last-of-script\n")
        self.assertNotIn("Traceback", err)
        self.assertNotIn("CompletedProcess", err)

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
            f"echo script >> '{self.repo.log}'; echo from-package; "
            f'[ "$ORIGIN" = "{self.ADDRESS}" ] || exit 9',
            package=True,
        )
        code, out, _ = self.repo.run("via-npm")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK via-npm\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop", "script"])

    def test_a_missing_start_runs_stop_and_is_exit_2(self):
        self.repo.write_target(extra={"start": ""})
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("no `start` command", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["stop"])

    def test_a_failing_discover_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="echo disc-out\necho disc-err >&2\nexit 1")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("disc-out", out)
        self.assertIn("disc-err", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_discover_that_prints_no_json_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="echo disc-plain-out\necho disc-plain-err >&2")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("disc-plain-out", out)
        self.assertIn("disc-plain-err", err)
        self.assertIn("discover printed no JSON object", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_discover_that_prints_an_array_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="printf %s '[1]'\necho disc-arr-err >&2")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("[1]", out)
        self.assertIn("disc-arr-err", err)
        self.assertIn("discover must print one JSON object", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_malformed_target_json_is_a_sentence_not_a_traceback(self):
        (self.repo.root / ".mmw" / "target.json").write_text("{bad\n", encoding="utf-8")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("cannot be read as JSON", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("JSONDecodeError", err)
        self.assertNotIn("JOURNEY OK", out)

    def test_a_target_json_array_is_a_sentence_not_a_traceback(self):
        (self.repo.root / ".mmw" / "target.json").write_text("[]\n", encoding="utf-8")
        code, out, err = self.repo.run("demo")
        self.assertEqual(code, 2)
        self.assertIn("must hold one JSON object", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("AttributeError", err)


class NegativeControl(unittest.TestCase):
    """A judge that cannot go red is not a judge. The control pass runs the script once
    more with the product stopped and every discovered address pointing nowhere."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.repo.write_target()
        self.repo.write_stack()

    def test_a_journey_that_asserts_nothing_is_caught(self):
        self.repo.write_journey("lazy", "exit 0")
        code, out, _ = self.repo.run("lazy")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("JOURNEY GREEN WITHOUT PRODUCT lazy at "), out)
        self.assertIn("product stopped", out)

    def test_a_journey_that_reaches_the_product_passes(self):
        self.repo.write_journey(
            "real", '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')
        code, out, _ = self.repo.run("real")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK real\n")

    def test_a_first_pass_that_fails_never_reaches_the_control(self):
        self.repo.write_journey(
            "broken",
            f"echo script >> '{self.repo.log}'\necho last-of-script >&2\nexit 7")
        code, out, _ = self.repo.run("broken")
        self.assertEqual(code, 1, out)
        self.assertEqual(out, "JOURNEY FAILED broken at last-of-script\n")
        self.assertEqual(
            self.repo.log.read_text(encoding="utf-8").splitlines().count("script"), 1)

    def test_the_control_moves_the_port_and_sets_its_own_variable(self):
        seen = self.repo.root / ".mmw" / "control-env"
        self.repo.write_journey(
            "watch",
            f"echo ORIGIN=$ORIGIN NEG=$MMW_JOURNEY_NEGATIVE "
            f"INSTANCE=$INSTANCE SLOT=$MMW_SLOT >> '{seen}'\n"
            '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')
        code, out, _ = self.repo.run("watch")
        self.assertEqual(code, 0, out)
        first, second = seen.read_text(encoding="utf-8").splitlines()
        self.assertIn("ORIGIN=http://127.0.0.1:9 ", first)
        self.assertIn("NEG= ", first)
        self.assertRegex(second, r"ORIGIN=http://127\.0\.0\.1:\d+ ")
        self.assertNotIn("ORIGIN=http://127.0.0.1:9 ", second)
        self.assertIn("NEG=1", second)
        # `instance` carries no port and is left alone; the lease is the same run's.
        self.assertIn("INSTANCE=t", second)
        self.assertRegex(second, r"SLOT=\d+")


class RepointingAnAddress(unittest.TestCase):
    """Which discover values the control pass moves, and which it must not touch."""

    def test_a_url_keeps_its_scheme_host_and_path(self):
        self.assertEqual(jy.repointed("http://127.0.0.1:5173/app", 41000),
                         "http://127.0.0.1:41000/app")

    def test_a_bare_host_and_port_is_moved_too(self):
        self.assertEqual(jy.repointed("127.0.0.1:9222", 41000), "127.0.0.1:41000")

    def test_a_value_with_no_port_is_left_alone(self):
        self.assertIsNone(jy.repointed("demo", 41000))
        self.assertIsNone(jy.repointed("GET /health -> .ok", 41000))

    def test_the_port_it_picks_is_one_nothing_listens_on(self):
        import socket
        port = jy.closed_port()
        with socket.socket() as probe:
            self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)


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

    def test_the_committed_demo_would_go_red_without_its_product(self):
        """The fixture is a miniature of a real target: `start` brings a product up on
        this run's own port, `stop` ends the pid it recorded, and the journey asserts
        something only that product answers. Its `JOURNEY OK` above therefore means the
        control pass went red, which is the whole point of committing it."""
        home = tempfile.mkdtemp(prefix="mmw-journey-neg-")
        self.addCleanup(shutil.rmtree, home, True)
        proc = subprocess.run(
            [sys.executable, str(FIXTURE / "repo" / ".mmw" / "journeys" / "demo" / "run")],
            cwd=FIXTURE / "repo" / ".mmw" / "journeys" / "demo",
            capture_output=True, text=True,
            env={**os.environ, "ORIGIN": f"http://127.0.0.1:{jy.closed_port()}"},
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout)


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
