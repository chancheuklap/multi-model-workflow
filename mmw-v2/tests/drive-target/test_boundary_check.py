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


def run_judge(*commands: str, extra_env: dict[str, str] | None = None
              ) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("MMW_NEGATIVE", None)
    if extra_env:
        env.update(extra_env)
    argv = [sys.executable, str(SCRIPT)]
    for command in commands:
        argv.extend(["--run", command])
    return subprocess.run(argv, cwd=REPO, capture_output=True, text=True, env=env)


class BoundaryCheck(unittest.TestCase):
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
            r"fixtures/boundary/always-green\.sh$",
        )

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

    def test_a_command_that_does_not_exist_exits_2(self):
        result = run_judge("mmw-boundary-check-no-such-command")
        self.assertEqual(result.returncode, 2)
        self.assertIn("mmw-boundary-check-no-such-command", result.stderr)
        self.assertIn("stop", result.stderr.lower())

    def test_n_is_the_number_of_run_flags(self):
        honest = f"bash {FIX / 'honest.sh'}"
        result = run_judge(honest, honest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"(?m)^BOUNDARY OK 2/2$")

    def test_both_passes_share_cwd_and_only_the_second_sets_mmw_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "log"
            result = run_judge(
                f"bash {FIX / 'record.sh'}",
                extra_env={"MMW_BOUNDARY_LOG": str(log)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2, lines)
        first_cwd, first_neg = lines[0].removeprefix("cwd=").split(" negative=", 1)
        second_cwd, second_neg = lines[1].removeprefix("cwd=").split(" negative=", 1)
        self.assertEqual(Path(first_cwd).resolve(), REPO.resolve())
        self.assertEqual(first_cwd, second_cwd)
        self.assertEqual(first_neg, "")
        self.assertEqual(second_neg, "1")


if __name__ == "__main__":
    unittest.main()
