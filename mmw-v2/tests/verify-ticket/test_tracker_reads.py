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
        self.assertIn("440", err.getvalue())
        self.assertIn("body", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())



if __name__ == "__main__":
    unittest.main()
