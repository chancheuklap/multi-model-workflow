from __future__ import annotations

import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

MODULE = Path(__file__).resolve().parents[2] / "tools" / "verify-ticket" / "scripts" / "repository_checks.py"
_spec = importlib.util.spec_from_file_location("repository_checks_under_test", MODULE)
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)

def write_check(root: Path, body: str, executable: bool = True) -> Path:
    """A consuming repository's `scripts/check`: a bash script with `body`."""
    path = root / "scripts" / "check"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755 if executable else 0o644)
    return path


def python_lines(lines, code):
    """A script body that prints `lines` and exits `code`."""
    source = ("import sys; sys.stdout.write(" + json.dumps("\n".join(lines) + "\n")
              + f"); sys.exit({code})")
    return "python3 -c " + json.dumps(source)


class TestRepositoryCheck(unittest.TestCase):
    """`run_repository_check` runs the repository's `scripts/check` (its default tier) at
    a given root with `MMW_BASE_REF`, preserving exit status and useful failure evidence."""

    def run_in(self, body, base="origin/spec-337", executable=True, **kwargs):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_check(root, body, executable)
            return vt.run_repository_check(root, base, **kwargs)

    def test_a_red_check_names_the_failing_step_and_keeps_its_last_lines(self):
        lines = [str(i) for i in range(1, 26)] + ["PASS lint 1s", "FAIL unit 2s"]
        result = self.run_in(python_lines(lines, 1))
        self.assertEqual(result["status"], "red")
        self.assertEqual(len(result["failed"]), 1)
        row = result["failed"][0]
        self.assertEqual((row["command"], row["exit"], row["steps"]),
                         ("scripts/check", 1, ["unit"]))
        tail = row["tail"].splitlines()
        self.assertEqual((tail[0], tail[-1]), ("1", "FAIL unit 2s"))
        prose = vt.checks_bounce_prose(result["failed"], prefix_len=80)
        self.assertIn("unit", prose["summary"])

    def test_an_early_error_line_is_kept_ahead_of_the_tail(self):
        lines = ["AssertionError: price"] + [f"noise-{i}" for i in range(1, 41)]
        tail = self.run_in(python_lines(lines, 1))["failed"][0]["tail"].splitlines()
        self.assertIn("AssertionError: price", tail)
        self.assertNotIn("noise-2", tail)
        self.assertIn("noise-40", tail)
        self.assertNotIn("noise-10", tail)

    def test_an_early_source_location_is_kept_ahead_of_the_tail(self):
        lines = ["src/file.py:7 contract mismatch"] + [f"noise-{i}" for i in range(1, 41)]
        tail = self.run_in(python_lines(lines, 1))["failed"][0]["tail"].splitlines()
        self.assertIn("src/file.py:7 contract mismatch", tail)
        self.assertNotIn("noise-2", tail)
        self.assertIn("noise-40", tail)

    def test_only_ten_error_lines_are_kept_before_the_tail(self):
        lines = [f"error-{i}" for i in range(1, 13)] + [f"noise-{i}" for i in range(1, 41)]
        tail = self.run_in(python_lines(lines, 1))["failed"][0]["tail"].splitlines()
        self.assertIn("error-1", tail)
        self.assertIn("error-10", tail)
        self.assertNotIn("error-11", tail)
        self.assertNotIn("error-12", tail)
        self.assertNotIn("noise-1", tail)
        self.assertIn("noise-40", tail)

    def test_the_saved_log_keeps_the_markers_the_excerpt_hides(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "wt"
            work.mkdir()
            write_check(root, python_lines(["error LINT OK"], 1))
            result = vt.run_repository_check(root, "origin/spec-337", worktree=work, ticket=61)
            log = (work / ".scratch" / "checks" / "61" / "1.log").read_text(encoding="utf-8")
        self.assertIn("LINT OK", log)
        self.assertNotIn("LINT OK", result["failed"][0]["tail"])
        self.assertIn("error", result["failed"][0]["tail"])
        self.assertEqual(result["failed"][0]["log"], ".scratch/checks/61/1.log")

    def test_a_missing_worktree_is_not_created_for_the_log(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "absent"
            write_check(root, "exit 1")
            result = vt.run_repository_check(root, "origin/spec-337", worktree=missing, ticket=61)
            self.assertFalse(missing.exists())
        self.assertNotIn("log", result["failed"][0])

    def test_each_failed_command_opens_its_own_paragraph(self):
        rows = [
            {"command": "python3 -c 'import sys; sys.exit(1)'", "tail": "", "exit": 1},
            {"command": "python3 -c 'import sys; sys.exit(3)'", "tail": "", "exit": 3},
        ]
        prose = vt.checks_bounce_prose(rows, prefix_len=80)
        self.assertEqual(
            prose["summary"],
            "python3 -c 'import sys; sys.exit(1)' exit 1; "
            "python3 -c 'import sys; sys.exit(3)' exit 3",
        )
        self.assertEqual(prose["rest"].splitlines(), [
            "python3 -c 'import sys; sys.exit(1)' exit 1",
            "",
            "python3 -c 'import sys; sys.exit(3)' exit 3",
        ])

    def test_a_huge_excerpt_line_stays_inside_a_comment(self):
        source = "import sys; sys.stdout.write('x' * 100000); sys.exit(1)"
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "wt"
            work.mkdir()
            write_check(root, "python3 -c " + json.dumps(source))
            result = vt.run_repository_check(root, "origin/spec-337", worktree=work, ticket=61)
            log = (work / ".scratch" / "checks" / "61" / "1.log").read_text(encoding="utf-8")
        self.assertGreaterEqual(len(log), 100000)
        prose = vt.checks_bounce_prose(
            [{"command": "python3 -c 'print(1)'", "tail": "y" * 100000, "exit": 1}],
            prefix_len=400,
        )
        self.assertIn("python3 -c 'print(1)'", prose["summary"])
        rendered = ("x" * 400) + " Failed checks: " + prose["summary"] + ".\n\n" + prose["rest"]
        rendered += json.dumps(prose["commands"])
        self.assertLess(len(rendered), 65536)
        self.assertLess(len(result["failed"][0]["tail"]), 65536)

    def test_the_check_sees_mmw_base_ref_and_a_green_run_passes(self):
        result = self.run_in('[ "$MMW_BASE_REF" = origin/spec-337 ]')
        self.assertEqual((result["status"], result["failed"]), ("pass", []))

    def test_exit_2_cannot_run_and_names_what_the_script_said(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            work = root / "wt"
            work.mkdir()
            write_check(root, "echo 'uv: command not found' >&2; exit 2")
            result = vt.run_repository_check(root, "origin/spec-337", worktree=work, ticket=61)
            log = work / ".scratch" / "checks" / "61" / "1.log"
            self.assertTrue(log.is_file())
        self.assertEqual((result["status"], result["failed"]), ("cannot-run", []))
        self.assertIn("uv: command not found", result["detail"])
        self.assertIn(str(log), result["detail"])

    def test_an_exit_outside_0_1_2_cannot_run_rather_than_passing_or_bouncing(self):
        result = self.run_in("exit 3")
        self.assertEqual((result["status"], result["failed"]), ("cannot-run", []))

    def test_an_absent_or_unexecutable_check_is_missing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = vt.run_repository_check(root, "origin/spec-337")
            self.assertEqual(result["status"], "missing")
            self.assertIn(str(root / "scripts" / "check"), result["detail"])
            write_check(root, "exit 0", executable=False)
            result = vt.run_repository_check(root, "origin/spec-337")
            self.assertEqual(result["status"], "missing")
            self.assertIn(str(root / "scripts" / "check"), result["detail"])
