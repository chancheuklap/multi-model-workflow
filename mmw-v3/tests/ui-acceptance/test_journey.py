"""journey.py: fake start/stop/discover, a real lease registry.

The seam is the command line and the files the commands write. Nothing here stubs
lease.py: a slot is acquired because journey.py acquires one, under a MMW_HOME of this
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

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "ui-acceptance" / "scripts"
JOURNEY = SCRIPTS / "journey.py"
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
# The lease the driver acquires through, reached from the function `journey.py` itself
# imported: filling this registry is filling the one a run started here would acquire from,
# and it is this suite's own `MMW_HOME`, never the machine's.
LEASE = sys.modules[jy.ProductRun.__module__]


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
            "ports": 1,
            "start": str(self.root / ".mmw" / "start.sh"),
            "stop": str(self.root / ".mmw" / "stop.sh"),
            "discover": str(self.root / ".mmw" / "discover.sh"),
            "stories": "true",
            "leaves_machine": [],
        }
        if extra:
            cfg.update(extra)
        (self.root / ".mmw" / "target.json").write_text(
            json.dumps({"products": ["notes"]}), encoding="utf-8")
        (self.root / ".mmw" / "notes").mkdir(exist_ok=True)
        (self.root / ".mmw" / "notes" / "target.json").write_text(
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
        dest = self.root / ".mmw" / "notes" / "journeys" / name
        dest.mkdir(parents=True, exist_ok=True)
        if package:
            (dest / "package.json").write_text(
                json.dumps({"scripts": {"run": body}}), encoding="utf-8")
            return dest
        write_exec(dest / "run", "#!/bin/sh\n" + body + "\n")
        return dest

    def run(self, name: str, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        here = Path.cwd()
        os.chdir(self.root)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = jy.main(["run", name, *args])
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
        code, out, _ = self.repo.run("notes/demo")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK notes/demo\n")
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
        code, out, _ = self.repo.run("notes/demo")
        self.assertEqual(code, 0, out)
        env = stop_env.read_text(encoding="utf-8")
        self.assertIn("ORIGIN=http://127.0.0.1:9", env)
        self.assertRegex(env, r"MMW_INSTANCE=\S+")

    def test_a_run_that_leaves_something_listening_on_its_slot_is_not_ok(self):
        """The control pass runs with the product down, so a script that starts anything
        to reach it leaves that on the slot. Whoever is given the slot next starts onto
        occupied ports, and the only thing they can report is blocked."""
        pidfile = self.repo.root / ".mmw" / "leftover.pid"
        write_exec(self.repo.root / ".mmw" / "leftover.py", "\n".join([
            "#!/usr/bin/env python3",
            "import os, socket, sys",
            "sock = socket.socket()",
            "sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)",
            # Every address, which is where a container engine publishes a port.
            "sock.bind(('0.0.0.0', int(os.environ['MMW_PORT_BASE'])))",
            "sock.listen(1)",
            "open(sys.argv[1], 'w').write(str(os.getpid()))",
            "while True:",
            "    conn, _ = sock.accept()",
            "    conn.close()",
        ]))

        def kill_leftover():
            try:
                os.kill(int(pidfile.read_text(encoding="utf-8")), 9)
            except (OSError, ValueError):
                pass
        self.addCleanup(kill_leftover)
        pass_count = self.repo.root / ".mmw" / "pass-count"
        self.repo.write_journey("demo", "\n".join([
            f"echo script >> '{self.repo.log}'",
            f"count=$(cat '{pass_count}' 2>/dev/null || echo 0)",
            "count=$((count + 1))",
            f"echo $count > '{pass_count}'",
            "if [ $count -eq 2 ]; then",
            f"  python3 '{self.repo.root / '.mmw' / 'leftover.py'}' '{pidfile}' "
            f">/dev/null 2>&1 &",
            f"  for _ in $(seq 1 100); do [ -f '{pidfile}' ] && break; sleep 0.05; done",
            "fi",
            f'[ "$ORIGIN" = "{self.ADDRESS}" ] || exit 9',
        ]))
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("JOURNEY LEFT THE PRODUCT UP notes/demo"), out)
        self.assertIn(pidfile.read_text(encoding="utf-8").strip(), out, "no pid to go to")
        self.assertNotIn("JOURNEY OK", out)
        self.assertIn("still has a listener", err)
        # Repo.run returning proves the release refusal did not escape as SystemExit;
        # an escaped exception would make this test error before `code` existed.
        self.assertIsNotNone(LEASE.registered(LEASE.worktree_of(self.repo.root)))

    def test_a_release_refusal_cannot_leave_a_success_exit(self):
        class RefusingRun:
            def __enter__(self):
                return None

            def __exit__(self, *_):
                raise SystemExit("release refused")

        with mock.patch.object(jy, "judge_run", return_value=RefusingRun()), \
             mock.patch.object(jy, "_run_named", return_value=0), \
             redirect_stderr(io.StringIO()) as err:
            code = jy.run_named("demo", self.repo.root)
        self.assertEqual(code, 1)
        self.assertIn("release refused", err.getvalue())

    def test_stop_runs_when_the_script_fails(self):
        self.repo.write_journey(
            "demo", "echo first-of-script >&2\necho last-of-script >&2\nexit 7")
        code, out, _ = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out)
        failed_at = out.find("JOURNEY FAILED notes/demo at last-of-script")
        self.assertGreater(failed_at, 0, out)
        before = out[:failed_at]
        self.assertIn("first-of-script", before)
        self.assertIn("last-of-script", before)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_a_failing_stop_does_not_replace_the_journey_verdict(self):
        self.repo.write_stack(stop="echo stop-broke >&2\nexit 3")
        self.repo.write_journey(
            "demo", "echo last-of-script >&2\nexit 7")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        self.assertIn("JOURNEY FAILED notes/demo at last-of-script", out)
        self.assertNotIn("Traceback", out + err)
        self.assertNotIn("CompletedProcess", out + err)

    def test_start_failure_is_exit_2_and_prints_the_refusal_unchanged(self):
        self.repo.write_stack(start="echo Gateway points elsewhere >&2\nexit 1")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("Gateway points elsewhere", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertNotIn("JOURNEY FAILED", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "stop"])

    def test_a_missing_journey_prints_failed_and_is_exit_1(self):
        code, out, _ = self.repo.run("notes/no-such")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("JOURNEY FAILED notes/no-such at "), out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_a_package_json_run_script_is_the_journey(self):
        self.repo.write_journey(
            "via-npm",
            f"echo script >> '{self.repo.log}'; echo from-package; "
            f'[ "$ORIGIN" = "{self.ADDRESS}" ] || exit 9',
            package=True,
        )
        code, out, _ = self.repo.run("notes/via-npm")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK notes/via-npm\n")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop", "script"])

    def test_a_full_machine_is_exit_2_and_nothing_is_started(self):
        held = tempfile.TemporaryDirectory()
        self.addCleanup(held.cleanup)
        # `claim` sweeps before it takes a slot, and a slot only comes back when its
        # worktree is gone, so the directories that fill the table have to be real.
        for n in range(LEASE.SLOTS):
            tree = Path(held.name) / f"held-{n}"
            tree.mkdir()
            LEASE.claim(tree)
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertNotIn("JOURNEY", out)
        self.assertIn("A run needs one and none is free", err)
        self.assertFalse(self.repo.log.exists(), "a command ran on a full machine")

    def test_a_missing_stop_is_refused_before_start_and_is_exit_2(self):
        self.repo.write_target(extra={"stop": ""})
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("no `stop` command", err)
        self.assertNotIn("JOURNEY", out)
        self.assertFalse(self.repo.log.exists(), "the product was started anyway")

    def test_a_missing_start_runs_no_commands_and_is_exit_2(self):
        self.repo.write_target(extra={"start": ""})
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("no `start` command", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertFalse(self.repo.log.exists(), "nothing started, so nothing may be stopped")

    def test_a_failing_discover_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="echo disc-out\necho disc-err >&2\nexit 1")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("disc-out", out)
        self.assertIn("disc-err", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_discover_that_prints_no_json_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="echo disc-plain-out\necho disc-plain-err >&2")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("disc-plain-out", out)
        self.assertIn("disc-plain-err", err)
        self.assertIn("discover printed no JSON object", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_discover_that_prints_an_array_forwards_stdout_and_stderr_whole(self):
        self.repo.write_stack(discover="printf %s '[1]'\necho disc-arr-err >&2")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("[1]", out)
        self.assertIn("disc-arr-err", err)
        self.assertIn("discover must print one JSON object", err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop"])

    def test_malformed_target_json_is_a_sentence_not_a_traceback(self):
        (self.repo.root / ".mmw" / "target.json").write_text("{bad\n", encoding="utf-8")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("cannot be read as JSON", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("JSONDecodeError", err)
        self.assertNotIn("JOURNEY OK", out)

    def test_a_target_json_array_is_a_sentence_not_a_traceback(self):
        (self.repo.root / ".mmw" / "target.json").write_text("[]\n", encoding="utf-8")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2)
        self.assertIn("must hold one JSON object", err)
        self.assertNotIn("Traceback", err)
        self.assertNotIn("AttributeError", err)


class FailureReport(unittest.TestCase):
    """A failed journey shows the script output the worker would otherwise lose."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.repo.write_target()
        self.repo.write_stack()

    def test_a_failing_script_prints_its_whole_output(self):
        self.repo.write_journey("demo", "\n".join([
            "echo stdout-before",
            "echo 'AssertionError: selector .missing waited 5000ms'",
            "echo stdout-after",
            "echo stderr-before >&2",
            "echo stderr-after >&2",
            "exit 7",
        ]))
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        failed_at = out.find("JOURNEY FAILED notes/demo at ")
        self.assertGreater(failed_at, 0, out)
        before = out[:failed_at]
        self.assertIn("stdout-before", before)
        self.assertIn("AssertionError: selector .missing waited 5000ms", before)
        self.assertIn("stdout-after", before)
        self.assertIn("stderr-before", before)
        self.assertIn("stderr-after", before)
        self.assertIn("JOURNEY FAILED notes/demo at stderr-after", out)
        self.assertNotIn("JOURNEY OK", out + err)

    def test_colour_codes_are_stripped(self):
        self.repo.write_journey("demo", "\n".join([
            'if [ -n "${FORCE_COLOR+x}" ]; then echo FORCE_COLOR=present; else echo FORCE_COLOR=absent; fi',
            "printf '\\033[31mred failed\\033[0m\\n'",
            "echo plain middle assertion",
            "exit 1",
        ]))
        with mock.patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False):
            code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        self.assertIn("FORCE_COLOR=absent", out)
        self.assertNotIn("FORCE_COLOR=present", out)
        self.assertIn("red failed", out)
        self.assertIn("plain middle assertion", out)
        self.assertNotIn("\x1b", out + err)
        self.assertIn("JOURNEY FAILED notes/demo at plain middle assertion", out)

    def test_a_failure_names_the_data_dir(self):
        marker = self.repo.root / ".mmw" / "data-dir"
        self.repo.write_journey("demo", "\n".join([
            f"printf %s \"$MMW_DATA_DIR\" > '{marker}'",
            "echo last-of-script",
            "exit 1",
        ]))
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        recorded = marker.read_text(encoding="utf-8")
        self.assertTrue(recorded, "the script was not given MMW_DATA_DIR")
        self.assertTrue(Path(recorded).is_dir(), recorded)
        lines = out.splitlines()
        failed = next(i for i, line in enumerate(lines) if line.startswith("JOURNEY FAILED notes/demo at "))
        self.assertGreater(len(lines), failed + 1, out)
        self.assertIn(recorded, lines[failed + 1])
        self.assertNotIn("JOURNEY OK", out)

    def test_the_evidence_dir_is_given_and_listed(self):
        stale = self.repo.root / ".scratch" / "journeys" / "notes" / "demo" / "stale.png"
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"old")
        self.repo.write_journey("demo", "\n".join([
            'if [ -z "${MMW_EVIDENCE_DIR:-}" ]; then echo missing-evidence-dir; exit 1; fi',
            'if [ -n "$(ls -A "$MMW_EVIDENCE_DIR" 2>/dev/null)" ]; then echo was-not-empty; exit 1; fi',
            'printf %s "$MMW_EVIDENCE_DIR" > "$MMW_EVIDENCE_DIR/where.txt"',
            'echo kept > "$MMW_EVIDENCE_DIR/note.txt"',
            "echo assertion failed in the middle",
            "exit 1",
        ]))
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        self.assertNotIn("missing-evidence-dir", out + err)
        self.assertNotIn("was-not-empty", out + err)
        expected = (self.repo.root / ".scratch" / "journeys" / "notes" / "demo").resolve()
        where = (expected / "where.txt").read_text(encoding="utf-8")
        self.assertEqual(Path(where), expected)
        after = out[out.find("JOURNEY FAILED notes/demo at "):]
        self.assertIn("where.txt", after)
        self.assertIn("note.txt", after)
        self.assertNotIn("stale.png", out)
        self.assertFalse(stale.exists())

    def test_an_empty_evidence_dir_is_said(self):
        self.repo.write_journey("demo", "echo only-the-failure\nexit 1")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 1, out + err)
        evidence = (self.repo.root / ".scratch" / "journeys" / "notes" / "demo").resolve()
        self.assertTrue(evidence.is_dir())
        self.assertEqual([item for item in evidence.rglob("*") if item.is_file()], [])
        said = [line for line in out.splitlines() if "references/journey.md" in line]
        self.assertEqual(len(said), 1, out)
        self.assertIn(str(evidence), said[0])
        self.assertNotIn("JOURNEY OK", out + err)

    def test_the_break_pass_prints_only_when_it_passes(self):
        broken = self.repo.root / ".mmw" / "broken"
        secret = "SECOND-PASS-OUTPUT-token"
        self.repo.write_stack(start="\n".join([
            'if [ -n "$MMW_BREAK" ]; then',
            f"  touch '{broken}'",
            '  echo "BREAK ARMED $MMW_BREAK"',
            "else",
            f"  rm -f '{broken}'",
            "fi",
        ]))
        self.repo.write_journey("demo", "\n".join([
            f"if [ -f '{broken}' ]; then echo {secret}; exit 1; fi",
            "exit 0",
        ]))
        code, out, err = self.repo.run("notes/demo", "--break", "PUT /api/settings")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "JOURNEY OK notes/demo\n")
        self.assertNotIn(secret, out + err)

        first = "FIRST-PASS-TOKEN"
        second = "SECOND-PASS-TOKEN"
        self.repo.write_journey("demo", "\n".join([
            f"if [ -f '{broken}' ]; then echo {second}; echo second-pass-last; exit 0; fi",
            f"echo {first}",
            "exit 0",
        ]))
        code, out, err = self.repo.run("notes/demo", "--break", "PUT /api/settings")
        self.assertEqual(code, 1, out + err)
        self.assertIn(second, out)
        self.assertNotIn(first, out)
        self.assertLess(out.find(second), out.find("JOURNEY GREEN WITH BREAK notes/demo"))
        self.assertIn("second-pass-last", out)
        self.assertNotIn("JOURNEY OK", out)

    def test_a_silent_start_failure_is_named(self):
        marker = self.repo.root / ".mmw" / "data-dir"
        command = self.repo.root / ".mmw" / "start.sh"
        stale = self.repo.root / ".scratch" / "journeys" / "notes" / "demo" / "stale.png"
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"old")
        self.repo.write_stack(
            start=f"printf %s \"$MMW_DATA_DIR\" > '{marker}'\nexit 1")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2, out + err)
        text = out + err
        named = [line for line in text.splitlines()
                 if "start" in line.split() and str(command) in line and "1" in line.split()]
        self.assertEqual(len(named), 1, text)
        self.assertFalse(stale.exists(), "a failed start left the previous run's evidence")
        self.assertIn("(no output)", text)
        recorded = marker.read_text(encoding="utf-8")
        self.assertTrue(recorded)
        self.assertTrue(Path(recorded).is_dir(), recorded)
        self.assertIn(recorded, text)
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_a_start_failure_names_the_command_before_its_stderr(self):
        """A pipe that merges the two streams still shows the naming line first.

        stdout here holds writes until flush, which is what a pipe does. stderr
        lands immediately. Without a flush after the naming line, the command's
        own stderr comes out ahead of it.
        """
        self.repo.write_stack(start="echo Gateway points elsewhere >&2\nexit 1")
        chunks: list[str] = []

        class Hold(io.TextIOBase):
            def __init__(self, hold: bool):
                self.hold = hold
                self.buf: list[str] = []

            def write(self, s: str) -> int:
                if self.hold:
                    self.buf.append(s)
                else:
                    chunks.append(s)
                return len(s)

            def flush(self) -> None:
                if self.buf:
                    chunks.append("".join(self.buf))
                    self.buf.clear()

        stdout, stderr = Hold(True), Hold(False)
        here = Path.cwd()
        os.chdir(self.repo.root)
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = jy.main(["run", "notes/demo"])
        finally:
            os.chdir(here)
            stdout.flush()
        text = "".join(chunks)
        self.assertEqual(code, 2, text)
        header = text.find("start ")
        heard = text.find("Gateway points elsewhere")
        self.assertGreaterEqual(header, 0, text)
        self.assertGreater(heard, header, text)
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_an_empty_discover_is_named(self):
        marker = self.repo.root / ".mmw" / "data-dir"
        command = self.repo.root / ".mmw" / "discover.sh"
        self.repo.write_stack(
            discover=f"printf %s \"$MMW_DATA_DIR\" > '{marker}'\nexit 0")
        code, out, err = self.repo.run("notes/demo")
        self.assertEqual(code, 2, out + err)
        text = out + err
        named = [line for line in text.splitlines()
                 if "discover" in line.split() and str(command) in line and "0" in line.split()]
        self.assertEqual(len(named), 1, text)
        self.assertIn("(no output)", text)
        recorded = marker.read_text(encoding="utf-8")
        self.assertTrue(recorded)
        self.assertTrue(Path(recorded).is_dir(), recorded)
        self.assertIn(recorded, text)
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)


class NegativeControl(unittest.TestCase):
    """An oracle that cannot go red is not an oracle. The control pass runs the script once
    more with the product stopped and every discovered address pointing nowhere."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.repo.write_target()
        self.repo.write_stack()

    def write_arming_stack(self, start_log: Path | None = None) -> Path:
        broken = self.repo.root / ".mmw" / "broken"
        lines = []
        if start_log is not None:
            lines.append(f'echo "BREAK=[$MMW_BREAK]" >> \'{start_log}\'')
        lines.extend([
            'if [ -n "$MMW_BREAK" ]; then',
            f"  touch '{broken}'",
            '  echo "BREAK ARMED $MMW_BREAK"',
            "else",
            f"  rm -f '{broken}'",
            "fi",
        ])
        self.repo.write_stack(start="\n".join(lines))
        return broken

    def test_a_break_value_without_method_and_route_exits_2(self):
        for value in ("get /health", "GET health"):
            with self.subTest(value=value):
                code, out, err = self.repo.run("notes/lazy", "--break", value)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn(
                    "one uppercase method, one space, and a route starting with `/`", err)
                self.assertFalse(
                    self.repo.log.exists(), "start ran for an invalid --break value")

    def test_the_root_route_is_a_valid_break_value(self):
        broken = self.write_arming_stack()
        self.repo.write_journey("root", f"[ ! -f '{broken}' ]")

        code, out, err = self.repo.run("notes/root", "--break", "GET /")

        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "JOURNEY OK notes/root\n")

    def test_start_gets_mmw_break_only_on_the_second_pass(self):
        seen = self.repo.root / ".mmw" / "start-env"
        broken = self.write_arming_stack(start_log=seen)
        self.repo.write_journey(
            "write", f"echo script >> '{self.repo.log}'\n[ ! -f '{broken}' ]")

        code, out, err = self.repo.run("notes/write", "--break", "POST /items/{id}")

        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "JOURNEY OK notes/write\n")
        self.assertEqual(seen.read_text(encoding="utf-8").splitlines(),
                         ["BREAK=[]", "BREAK=[POST /items/{id}]"])
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(), [
            "start", "discover", "script", "stop",
            "start", "discover", "script", "stop",
        ])

    def test_a_start_that_fails_under_break_exits_2(self):
        self.repo.write_stack(start="\n".join([
            'if [ -n "$MMW_BREAK" ]; then',
            "  echo break-start-failed >&2",
            "  exit 7",
            "fi",
        ]))
        self.repo.write_journey(
            "real", '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')

        code, out, err = self.repo.run("notes/real", "--break", "GET /result/{id}")

        self.assertEqual(code, 2, out + err)
        self.assertNotIn("JOURNEY OK", out)
        self.assertIn("break-start-failed", err)
        self.assertIn("references/journey.md", err)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "stop", "start", "stop"])

    def test_a_start_that_does_not_arm_the_break_exits_2(self):
        self.repo.write_journey(
            "real", f"echo script >> '{self.repo.log}'\n"
                    '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')

        code, out, err = self.repo.run("notes/real", "--break", "GET /result/{id}")

        self.assertEqual(code, 2, out + err)
        self.assertIn("references/journey.md", err)
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(),
                         ["start", "discover", "script", "stop", "start", "stop"])

    def test_the_script_never_sees_which_pass_it_is_in(self):
        seen = self.repo.root / ".mmw" / "script-env"
        broken = self.write_arming_stack()
        self.repo.write_journey("watch", "\n".join([
            f"env | grep '^MMW_' | sort >> '{seen}'",
            f"echo pass-end >> '{seen}'",
            f"[ ! -f '{broken}' ]",
        ]))

        break_key = "MMW_BREAK"
        with mock.patch.dict(
            os.environ, {break_key: "inherited-break"},
            clear=False,
        ):
            code, out, err = self.repo.run("notes/watch", "--break", "GET /result/{id}")

        self.assertEqual(code, 0, out + err)
        first, _, second = seen.read_text(encoding="utf-8").partition("pass-end\n")
        second = second.removesuffix("pass-end\n")

        def without_evidence(text: str) -> str:
            return "".join(
                line + "\n" for line in text.splitlines()
                if not line.startswith("MMW_EVIDENCE_DIR=")
            )

        self.assertEqual(without_evidence(first), without_evidence(second))
        first_evidence = next(
            line for line in first.splitlines() if line.startswith("MMW_EVIDENCE_DIR="))
        second_evidence = next(
            line for line in second.splitlines() if line.startswith("MMW_EVIDENCE_DIR="))
        self.assertEqual(second_evidence, first_evidence + "/break")
        for pass_environment in (first, second):
            self.assertNotIn(f"{break_key}=", pass_environment)

    def test_a_journey_that_asserts_nothing_is_caught(self):
        self.repo.write_journey("lazy", "exit 0")
        code, out, _ = self.repo.run("notes/lazy")
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith("JOURNEY GREEN WITHOUT PRODUCT notes/lazy at "), out)
        self.assertIn("product stopped", out)

    def test_a_journey_that_reaches_the_product_passes(self):
        self.repo.write_journey(
            "real", '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')
        code, out, _ = self.repo.run("notes/real")
        self.assertEqual(code, 0, out)
        self.assertEqual(out, "JOURNEY OK notes/real\n")

    def test_a_first_pass_that_fails_never_reaches_the_control(self):
        self.repo.write_journey(
            "broken",
            f"echo script >> '{self.repo.log}'\necho last-of-script >&2\nexit 7")
        code, out, _ = self.repo.run("notes/broken")
        self.assertEqual(code, 1, out)
        self.assertIn("JOURNEY FAILED notes/broken at last-of-script", out)
        self.assertEqual(
            self.repo.log.read_text(encoding="utf-8").splitlines().count("script"), 1)

    def test_the_control_moves_the_port_and_sets_its_own_variable(self):
        seen = self.repo.root / ".mmw" / "control-env"
        self.repo.write_journey(
            "watch",
            f"echo pass-start >> '{seen}'\n"
            f"env | grep '^MMW_' | sort >> '{seen}'\n"
            f"echo ORIGIN=$ORIGIN INSTANCE=$INSTANCE SLOT=$MMW_SLOT >> '{seen}'\n"
            f"echo pass-end >> '{seen}'\n"
            '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9')
        code, out, _ = self.repo.run("notes/watch")
        self.assertEqual(code, 0, out)
        passes = seen.read_text(encoding="utf-8").split("pass-start\n")[1:]
        self.assertEqual(len(passes), 2)
        first, second = [item.split("pass-end\n", 1)[0] for item in passes]
        first_mmw = [line for line in first.splitlines() if line.startswith("MMW_")]
        second_mmw = [line for line in second.splitlines() if line.startswith("MMW_")]
        self.assertEqual(first_mmw, second_mmw)
        self.assertIn("ORIGIN=http://127.0.0.1:9 ", first)
        self.assertRegex(second, r"ORIGIN=http://127\.0\.0\.1:\d+ ")
        self.assertNotIn("ORIGIN=http://127.0.0.1:9 ", second)
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

    def copy_repo(self) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="mmw-journey-fixture-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "repo"
        shutil.copytree(FIXTURE / "repo", root)
        return root

    def run_fixture(self, root: Path, name: str, *args: str) -> subprocess.CompletedProcess:
        home = tempfile.mkdtemp(prefix="mmw-journey-ac-")
        self.addCleanup(shutil.rmtree, home, True)
        return subprocess.run(
            [sys.executable, str(JOURNEY), "run", name, *args],
            cwd=root, capture_output=True, text=True,
            env={**os.environ, "MMW_HOME": home},
        )

    def assert_demo_breaks(self, break_spec: str) -> Path:
        root = self.copy_repo()
        proc = self.run_fixture(root, "notes/demo", "--break", break_spec)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout, "JOURNEY OK notes/demo\n")
        return root

    def test_a_break_journey_that_reads_the_result_back_passes(self):
        self.assert_demo_breaks("POST /write/{id}")

    def test_a_break_journey_that_only_checks_the_page_is_green_with_break(self):
        root = self.copy_repo()
        write_exec(root / ".mmw" / "notes" / "journeys" / "weak" / "run", "\n".join([
            "#!/bin/sh",
            'curl -sf --max-time 5 "$ORIGIN/health" | grep -q \'^ok$\'',
        ]))

        proc = self.run_fixture(root, "notes/weak", "--break", "GET /result/{id}")

        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("JOURNEY GREEN WITH BREAK notes/weak —", proc.stdout)
        self.assertTrue((root / ".mmw" / "stop-ran").is_file())

    def test_the_committed_demo_passes_with_break(self):
        self.assert_demo_breaks("GET /result/{id}")

    def test_after_a_break_run_the_slot_is_empty(self):
        root = self.copy_repo()

        proc = self.run_fixture(root, "notes/demo", "--break", "GET /result/{id}")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue((root / ".mmw" / "stop-ran").is_file())
        for port in LEASE.ports_of(0):
            self.assertIsNone(LEASE.listener(port), f"port {port} still has a listener")

    def test_the_committed_demo_prints_ok_and_stop_ran(self):
        root = self.copy_repo()
        proc = self.run_fixture(root, "notes/demo")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.splitlines()[0], "JOURNEY OK notes/demo")
        self.assertIn("stop-ran", (root / ".mmw" / "stop-ran").read_text())

    def test_the_committed_demo_would_go_red_without_its_product(self):
        """The fixture is a miniature of a real product under test: `start` brings a product up on
        this run's own port, `stop` ends the pid it recorded, and the journey asserts
        something only that product answers. Its `JOURNEY OK` above therefore means the
        control pass went red, which is the whole point of committing it."""
        home = tempfile.mkdtemp(prefix="mmw-journey-neg-")
        self.addCleanup(shutil.rmtree, home, True)
        proc = subprocess.run(
            [sys.executable, str(FIXTURE / "repo" / ".mmw" / "notes" / "journeys" / "demo" / "run")],
            cwd=FIXTURE / "repo" / ".mmw" / "notes" / "journeys" / "demo",
            capture_output=True, text=True,
            env={**os.environ, "ORIGIN": f"http://127.0.0.1:{jy.closed_port()}"},
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout)


class NeededProducts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        fixture = Path(__file__).resolve().parent / "fixtures" / "products" / "repo"
        shutil.copytree(fixture, self.root)
        self.home = Path(self.tmp.name) / "mmw"
        self.env = dict(os.environ, MMW_HOME=str(self.home))
        self.addCleanup(subprocess.run, [sys.executable, str(SCRIPTS / "lease.py"),
                                        "release", str(self.root), "--stop"],
                        env=self.env, capture_output=True, text=True)

    def run_product(self):
        return subprocess.run([sys.executable, str(JOURNEY), "run", "parrot/open"],
                              cwd=self.root, env=self.env, capture_output=True, text=True)

    def events(self):
        return [json.loads(line) for line in
                (self.root / ".mmw" / "events.jsonl").read_text().splitlines()]

    def test_a_needed_product_starts_first_and_hands_its_address(self):
        proc = self.run_product()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("JOURNEY OK parrot/open", proc.stdout)
        events = self.events()
        starts = [e for e in events if e["verb"] == "start"]
        self.assertEqual([e["product"] for e in starts], ["gateway", "parrot"])
        gateway, parrot = starts
        expected = "http://127.0.0.1:" + gateway["env"]["MMW_PORT_BASE"] + "/discovered"
        self.assertEqual(parrot["env"]["GATEWAY_ORIGIN"], expected)
        for e in events:
            if e["product"] == "parrot":
                self.assertEqual(e["env"]["GATEWAY_ORIGIN"], expected)
        self.assertEqual([e["evidence_files"] for e in events if e["verb"] == "journey"],
                         [[], []])

    def test_a_journey_stops_its_needs_in_reverse_order(self):
        proc = self.run_product()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("JOURNEY OK parrot/open", proc.stdout)
        events = self.events()
        self.assertEqual([e["product"] for e in events if e["verb"] == "stop"],
                         ["parrot", "gateway"])
        listed = subprocess.run([sys.executable, str(SCRIPTS / "lease.py"), "list"],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)
        self.assertEqual(json.loads(listed.stdout), [])
        import socket
        for e in events:
            if e["verb"] != "start":
                continue
            env = e["env"]
            for port in range(int(env["MMW_PORT_BASE"]),
                              int(env["MMW_PORT_BASE"]) + int(env["MMW_PORT_COUNT"])):
                with socket.socket() as probe:
                    self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)

    def test_a_journey_keeps_a_dependency_started_before_it(self):
        proc = subprocess.run([sys.executable, str(SCRIPTS / "lease.py"), "run",
                               "--product", "gateway", "--", sys.executable,
                               ".mmw/product.py", "start"], cwd=self.root,
                              env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        proc = self.run_product()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("JOURNEY OK parrot/open", proc.stdout)
        events = self.events()
        self.assertEqual([e["product"] for e in events if e["verb"] == "start"],
                         ["gateway", "parrot"])
        self.assertEqual([e["product"] for e in events if e["verb"] == "stop"], ["parrot"])
        proc = subprocess.run([sys.executable, str(SCRIPTS / "lease.py"), "list"],
                              env=self.env, capture_output=True, text=True)
        record = json.loads(proc.stdout)[0]
        self.assertEqual(record["started"], ["gateway"])
        self.assertEqual(record["busy"]["port"], record["port_base"])

    def test_neither_product_inherits_a_break_from_the_parent_session(self):
        self.env["MMW_BREAK"] = "GET /"
        proc = self.run_product()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("JOURNEY OK parrot/open", proc.stdout)
        for e in self.events():
            if e["verb"] != "stop":
                self.assertNotIn("MMW_BREAK", e["env"])

    def test_a_journey_refuses_to_restart_a_product_owned_by_another_run(self):
        proc = subprocess.run([sys.executable, str(SCRIPTS / "lease.py"), "run",
                               "--product", "parrot", "--", sys.executable,
                               ".mmw/product.py", "start"], cwd=self.root,
                              env=self.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        before = self.events()
        proc = self.run_product()
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("parrot", proc.stderr)
        self.assertNotIn("JOURNEY OK", proc.stdout)
        self.assertEqual(self.events(), before)
        listed = subprocess.run([sys.executable, str(SCRIPTS / "lease.py"), "list"],
                                env=self.env, capture_output=True, text=True)
        record = json.loads(listed.stdout)[0]
        self.assertEqual(record["started"], ["gateway", "parrot"])
        self.assertIsNotNone(record["busy"])


class TwoProducts(unittest.TestCase):
    """A new-layout repository: each product has its own start and its own journey."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        (self.repo.root / ".mmw" / "target.json").write_text(
            json.dumps({"products": ["alpha", "beta"]}), encoding="utf-8")

    def write_product(self, name: str) -> None:
        base = self.repo.root / ".mmw" / name
        base.mkdir(parents=True)
        log = self.repo.log
        write_exec(base / "start.sh",
                   "#!/bin/sh\n" + f"echo {name}-start >> '{log}'\nexit 0\n")
        write_exec(base / "stop.sh",
                   "#!/bin/sh\n" + f"echo {name}-stop >> '{log}'\n")
        write_exec(base / "discover.sh",
                   "#!/bin/sh\n" + f"echo {name}-discover >> '{log}'\n"
                   + "printf %s '{\"origin\":\"http://127.0.0.1:9\",\"instance\":\"t\"}'\n")
        (base / "target.json").write_text(json.dumps({
            "ports": 1,
            "start": str(base / "start.sh"),
            "stop": str(base / "stop.sh"),
            "discover": str(base / "discover.sh"),
            "stories": "true",
            "leaves_machine": [],
            "harness_markers": [],
        }), encoding="utf-8")
        dest = base / "journeys" / "open"
        dest.mkdir(parents=True)
        write_exec(dest / "run",
                   "#!/bin/sh\n"
                   + f"echo {name}-script >> '{log}'\n"
                   + '[ "$ORIGIN" = "http://127.0.0.1:9" ] || exit 9\n')

    def test_a_product_journey_runs_with_its_own_start(self):
        self.write_product("alpha")
        self.write_product("beta")
        code, out, err = self.repo.run("alpha/open")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "JOURNEY OK alpha/open\n")
        lines = self.repo.log.read_text(encoding="utf-8").splitlines()
        self.assertIn("alpha-start", lines)
        self.assertNotIn("beta-start", lines)
        self.assertNotIn("beta-script", lines)
        # One product or two, a bare flow name is not a journey. The read point
        # would otherwise start the only product.
        started = lines.count("alpha-start")
        for label, products in (("two", ["alpha", "beta"]), ("one", ["alpha"])):
            (self.repo.root / ".mmw" / "target.json").write_text(
                json.dumps({"products": products}), encoding="utf-8")
            code, out, err = self.repo.run("open")
            self.assertEqual(code, 2, f"{label}: {out}{err}")
            self.assertIn("<product>/<flow>", err, label)
            self.assertNotIn("JOURNEY", out, label)
        self.assertEqual(
            self.repo.log.read_text(encoding="utf-8").count("alpha-start"), started)

    def test_a_held_lease_naming_a_product_no_longer_listed_still_finishes(self):
        self.write_product("alpha")
        self.write_product("beta")
        tree = LEASE.worktree_of(self.repo.root)
        LEASE.claim(tree)
        self.addCleanup(LEASE.release, tree)
        LEASE.update_started(tree, "gone")
        code, out, err = self.repo.run("alpha/open")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(out, "JOURNEY OK alpha/open\n")


class Doctor(unittest.TestCase):
    """`doctor` runs after `discover` and before the journey script."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)

    def lay_out(self, products: list[str], needs: dict) -> None:
        (self.repo.root / ".mmw" / "target.json").write_text(json.dumps({
            "products": products,
            "needs": needs,
        }), encoding="utf-8")

    def add_product(self, name: str, doctor: str, script: str) -> Path:
        root = self.repo.root
        base = root / ".mmw" / name
        log = self.repo.log
        write_exec(base / "start.sh", f"#!/bin/sh\necho {name}-start >> '{log}'\nexit 0\n")
        write_exec(base / "stop.sh", f"#!/bin/sh\necho {name}-stop >> '{log}'\n")
        write_exec(base / "discover.sh",
                   "#!/bin/sh\n"
                   + f"echo {name}-discover >> '{log}'\n"
                   + "printf %s '{\"origin\":\"http://127.0.0.1:9\",\"instance\":\"t\"}'\n")
        command = base / "doctor.sh"
        write_exec(command, "#!/bin/sh\n" + doctor + "\n")
        (base / "target.json").write_text(json.dumps({
            "ports": 1,
            "start": str(base / "start.sh"),
            "stop": str(base / "stop.sh"),
            "discover": str(base / "discover.sh"),
            "doctor": str(command),
            "stories": "true",
            "leaves_machine": [],
            "harness_markers": [],
        }), encoding="utf-8")
        dest = base / "journeys" / "open"
        dest.mkdir(parents=True)
        write_exec(dest / "run", "#!/bin/sh\n" + f"echo {name}-script >> '{log}'\n" + script + "\n")
        return command

    def write_product(self, name: str, doctor: str, script: str) -> Path:
        self.lay_out([name], {})
        return self.add_product(name, doctor, script)

    def commit(self) -> str:
        root = self.repo.root
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "-c", "user.email=doctor@example.com", "-c", "user.name=doctor",
             "commit", "-m", "init"],
            cwd=root, check=True, capture_output=True, text=True,
        )
        found = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                               capture_output=True, text=True)
        return found.stdout.strip()

    def test_a_failing_doctor_stops_the_journey_before_the_script(self):
        heard = self.repo.root / ".mmw" / "commit"
        marker = self.repo.root / ".mmw" / "script-ran"
        command = self.write_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            f"printf %s \"$MMW_WORKTREE_COMMIT\" > '{heard}'",
            "echo doctor-says-no",
            "exit 1",
        ]), f"touch '{marker}'\nexit 0")
        sha = self.commit()
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertIn("doctor-says-no", text)
        self.assertNotEqual(code, 0, text)
        self.assertFalse(marker.exists(), text)
        lines = self.repo.log.read_text(encoding="utf-8").splitlines()
        self.assertLess(lines.index("parrot-discover"), lines.index("parrot-doctor"))
        self.assertNotIn("parrot-script", lines)
        named = [line for line in text.splitlines()
                 if str(command) in line and "1" in line.split()]
        self.assertEqual(len(named), 1, text)
        self.assertEqual(heard.read_text(encoding="utf-8"), sha)
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_a_doctor_without_a_pid_names_what_it_printed(self):
        marker = self.repo.root / ".mmw" / "script-ran"
        self.write_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            "printf '%s\\n' '{\"version\":\"t\"}'",
            "exit 0",
        ]), f"touch '{marker}'\nexit 0")
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertEqual(code, 2, text)
        self.assertFalse(marker.exists(), text)
        self.assertIn("product parrot doctor pid expected a pid actual no pid", out)
        self.assertIn('{"version":"t"}', out)
        self.assertLess(out.find("exit 0"), out.find("expected a pid"), out)
        self.assertLess(out.find("expected a pid"), out.find("MMW_DATA_DIR"), out)
        self.assertNotIn("parrot-script", self.repo.log.read_text(encoding="utf-8"))
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_a_silent_doctor_without_a_pid_names_the_gap(self):
        marker = self.repo.root / ".mmw" / "script-ran"
        self.write_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            "exit 0",
        ]), f"touch '{marker}'\nexit 0")
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertEqual(code, 2, text)
        self.assertFalse(marker.exists(), text)
        self.assertIn("product parrot doctor pid expected a pid actual none", out)
        self.assertIn("(no output)", out)
        self.assertLess(out.find("exit 0"), out.find("expected a pid"), out)
        self.assertLess(out.find("expected a pid"), out.find("(no output)"), out)
        self.assertNotIn("parrot-script", self.repo.log.read_text(encoding="utf-8"))
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_doctor_runs_again_after_a_failed_script(self):
        asked = self.repo.root / ".mmw" / "asked-pid"
        self.write_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            'if [ -n "${MMW_DOCTOR_PID+x}" ]; then',
            f"  printf %s \"$MMW_DOCTOR_PID\" > '{asked}'",
            "  printf '%s\\n' '{\"pid\":222,\"version\":\"t\",\"ports\":[9],\"note\":\"second-look\"}'",
            "else",
            "  printf '%s\\n' '{\"pid\":111,\"version\":\"t\",\"ports\":[9]}'",
            "fi",
            "exit 0",
        ]), "echo script-broke\nexit 1")
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertEqual(code, 1, text)
        self.assertIn("second-look", out)
        failed_at = out.find("JOURNEY FAILED parrot/open at ")
        self.assertGreater(failed_at, out.find("script-broke"), out)
        self.assertGreater(out.find("second-look"), failed_at, out)
        self.assertGreater(out.find("111"), failed_at, out)
        self.assertGreater(out.find("MMW_DATA_DIR"), out.find("second-look"), out)
        self.assertEqual(asked.read_text(encoding="utf-8"), "111")
        self.assertEqual(self.repo.log.read_text(encoding="utf-8").splitlines(), [
            "parrot-start", "parrot-discover", "parrot-doctor",
            "parrot-script", "parrot-doctor", "parrot-stop",
        ])
        self.assertNotIn("JOURNEY OK", text)

    def test_doctor_runs_for_every_started_product(self):
        marker = self.repo.root / ".mmw" / "script-ran"
        self.lay_out(["gateway", "parrot"], {"parrot": ["gateway"]})
        command = self.add_product("gateway", "\n".join([
            f"echo gateway-doctor >> '{self.repo.log}'",
            "echo gateway-unfit",
            "exit 1",
        ]), "exit 0")
        self.add_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            "printf '%s\\n' '{\"pid\":1,\"version\":\"t\",\"ports\":[9]}'",
            "exit 0",
        ]), f"touch '{marker}'\nexit 0")
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertIn("gateway-unfit", text)
        self.assertNotEqual(code, 0, text)
        self.assertFalse(marker.exists(), text)
        lines = self.repo.log.read_text(encoding="utf-8").splitlines()
        self.assertIn("gateway-start", lines)
        self.assertLess(lines.index("gateway-discover"), lines.index("gateway-doctor"))
        self.assertNotIn("parrot-script", lines)
        named = [line for line in text.splitlines()
                 if "gateway" in line.split() and str(command) in line and "1" in line.split()]
        self.assertEqual(len(named), 1, text)
        self.assertNotIn("JOURNEY OK", text)
        self.assertNotIn("JOURNEY FAILED", text)

    def test_a_failed_script_doctors_a_dependency_again(self):
        self.lay_out(["gateway", "parrot"], {"parrot": ["gateway"]})
        self.add_product("gateway", "\n".join([
            f"echo gateway-doctor >> '{self.repo.log}'",
            'if [ -n "${MMW_DOCTOR_PID+x}" ]; then',
            "  echo gateway-again",
            "fi",
            "printf '%s\\n' '{\"pid\":1,\"version\":\"t\",\"ports\":[9]}'",
            "exit 0",
        ]), "exit 0")
        self.add_product("parrot", "\n".join([
            f"echo parrot-doctor >> '{self.repo.log}'",
            "printf '%s\\n' '{\"pid\":9,\"version\":\"t\",\"ports\":[9]}'",
            "exit 0",
        ]), "echo script-broke\nexit 1")
        code, out, err = self.repo.run("parrot/open")
        text = out + err
        self.assertEqual(code, 1, text)
        failed_at = out.find("JOURNEY FAILED parrot/open at ")
        self.assertGreater(failed_at, out.find("script-broke"), out)
        self.assertGreater(out.find("gateway-again"), failed_at, out)
        lines = self.repo.log.read_text(encoding="utf-8").splitlines()
        first = lines.index("gateway-doctor")
        second = lines.index("gateway-doctor", first + 1)
        self.assertLess(lines.index("parrot-script"), second, lines)
        self.assertEqual(lines.count("gateway-doctor"), 2, lines)
        self.assertNotIn("JOURNEY OK", text)


if __name__ == "__main__":
    unittest.main()
