"""boundary-check.py runs a command twice; the pass that skips interaction must go red.

Nothing here is stubbed. The judge is a real process and the commands are the
fixture scripts under fixtures/boundary/, which read MMW_NEGATIVE for their
exit code.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SCRIPT = (Path(__file__).resolve().parents[2]
          / "skills" / "drive-target" / "scripts" / "boundary-check.py")
FIX = Path("mmw-v2/tests/drive-target/fixtures/boundary")


def run_judge(*commands: str, extra_env: dict[str, str] | None = None,
              cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("MMW_NEGATIVE", None)
    if extra_env:
        env.update(extra_env)
    argv = [sys.executable, str(SCRIPT)]
    for command in commands:
        argv.extend(["--run", command])
    with tempfile.TemporaryDirectory(prefix="boundary-mmw-home-") as home:
        env["MMW_HOME"] = home
        return subprocess.run(argv, cwd=cwd or REPO, capture_output=True, text=True,
                              env=env)


class BoundaryCheck(unittest.TestCase):
    def assert_not_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertNotIn("BOUNDARY OK", result.stdout)

    def test_an_honest_command_prints_boundary_ok(self):
        result = run_judge(f"bash {FIX / 'honest.sh'}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^BOUNDARY OK 1/1$")

    def test_a_command_green_on_both_passes_is_green_without_interaction(self):
        result = run_judge(f"bash {FIX / 'always-green.sh'}")
        self.assertEqual(result.returncode, 1)
        self.assertRegex(
            result.stdout,
            r"(?m)^GREEN WITHOUT INTERACTION bash mmw-v2/tests/drive-target/"
            r"fixtures/boundary/always-green\.sh",
        )
        self.assert_not_ok(result)

    def test_a_command_red_on_the_first_pass_is_a_miss_of_its_last_twenty_lines(self):
        result = run_judge(f"bash {FIX / 'always-red.sh'}")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(
            result.stdout.startswith(
                "MISS bash mmw-v2/tests/drive-target/fixtures/boundary/always-red.sh — "
            ),
            result.stdout,
        )
        self.assertIn("red-line-6", result.stdout)
        self.assertIn("red-line-25", result.stdout)
        self.assertNotIn("red-line-1\n", result.stdout)
        self.assertNotIn("red-line-5\n", result.stdout)
        self.assertEqual(result.stdout.count("red-line-"), 20)
        self.assert_not_ok(result)

    def test_a_silent_first_pass_red_is_a_miss_of_no_output(self):
        result = run_judge(f"bash {FIX / 'silent-red.sh'}")
        self.assertEqual(result.returncode, 1)
        self.assertIn("MISS ", result.stdout)
        self.assertIn("(no output)", result.stdout)
        self.assert_not_ok(result)

    def test_a_command_that_does_not_exist_exits_2(self):
        result = run_judge("mmw-boundary-check-no-such-command")
        self.assertEqual(result.returncode, 2)
        self.assertIn("mmw-boundary-check-no-such-command", result.stderr)
        self.assertIn("was not found", result.stderr)
        self.assertIn("stop", result.stderr.lower())
        self.assert_not_ok(result)

    def test_unclosed_quotes_are_not_reported_as_a_missing_command(self):
        result = run_judge('pnpm vitest run "foo')
        self.assertEqual(result.returncode, 2)
        self.assertIn("do not close", result.stderr)
        self.assertNotIn("was not found", result.stderr)
        self.assert_not_ok(result)

    def test_an_empty_command_is_not_reported_as_a_missing_command(self):
        result = run_judge("")
        self.assertEqual(result.returncode, 2)
        self.assertIn("empty", result.stderr.lower())
        self.assertNotIn("was not found", result.stderr)
        self.assert_not_ok(result)

    def test_a_shell_composite_is_refused_and_not_judged(self):
        result = run_judge("cd mmw-v2 && echo hi")
        self.assertEqual(result.returncode, 2)
        self.assertIn("&&", result.stderr)
        self.assertNotIn("GREEN WITHOUT INTERACTION", result.stdout)
        self.assert_not_ok(result)

    def test_a_non_executable_command_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "noexec"
            path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            path.chmod(0o644)
            result = run_judge(str(path))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("was not found", result.stderr)
        self.assert_not_ok(result)

    def test_n_is_the_number_of_run_flags(self):
        honest = f"bash {FIX / 'honest.sh'}"
        result = run_judge(honest, honest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^BOUNDARY OK 2/2$")

    def test_a_false_green_among_several_commands_is_not_boundary_ok(self):
        honest = f"bash {FIX / 'honest.sh'}"
        green = f"bash {FIX / 'always-green.sh'}"
        later = run_judge(honest, green)
        self.assertEqual(later.returncode, 1)
        self.assertIn("GREEN WITHOUT INTERACTION", later.stdout)
        self.assert_not_ok(later)
        earlier = run_judge(green, honest)
        self.assertEqual(earlier.returncode, 1)
        self.assertIn("GREEN WITHOUT INTERACTION", earlier.stdout)
        self.assert_not_ok(earlier)

    def test_both_passes_share_cwd_and_only_the_second_sets_mmw_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log"
            work = Path(tmp) / "work"
            work.mkdir()
            record = (REPO / FIX / "record.sh").resolve()
            result = run_judge(
                f"bash {record}",
                extra_env={"MMW_BOUNDARY_LOG": str(log)},
                cwd=work,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2, lines)
        first_cwd, first_neg = lines[0].removeprefix("cwd=").split(" negative=", 1)
        second_cwd, second_neg = lines[1].removeprefix("cwd=").split(" negative=", 1)
        self.assertEqual(Path(first_cwd).resolve(), work.resolve())
        self.assertEqual(first_cwd, second_cwd)
        self.assertEqual(first_neg, "")
        self.assertEqual(second_neg, "1")


if __name__ == "__main__":
    unittest.main()
