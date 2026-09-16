"""Tracker read failures are refusals, never Python tracebacks."""

import io
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr
from pathlib import Path
from unittest import mock

from _load import load

vt = load()


class TestTrackerReadFailures(unittest.TestCase):
    def failed_read(self, part):
        return vt.subprocess.CalledProcessError(
            1, ["gh", "issue", "view", "440", "--json", part], stderr="HTTP 502")

    def test_body_read_failure_names_the_read_and_safe_retry(self):
        err = io.StringIO()
        with mock.patch.object(vt.subprocess, "run", side_effect=self.failed_read("body")), \
                redirect_stderr(err):
            code = vt.main(["440", "--lint"])
        self.assertEqual(code, 2)
        self.assertIn("could not read #440's body", err.getvalue())
        self.assertIn("retry the same command", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_comments_read_failure_names_the_read_and_safe_retry(self):
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "closeout.md"
            draft.write_text("ALL MET\n", encoding="utf-8")
            with mock.patch.object(vt, "repo_root", return_value=Path(tmp)), \
                    mock.patch.object(vt, "closeout_lock", return_value=nullcontext()), \
                    mock.patch.object(vt.subprocess, "run",
                                      side_effect=self.failed_read("comments")), \
                    redirect_stderr(err):
                code = vt.main(["440", "--closeout", str(draft)])
        self.assertEqual(code, 2)
        self.assertIn("could not read #440's comments", err.getvalue())
        self.assertIn("retry the same command", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
