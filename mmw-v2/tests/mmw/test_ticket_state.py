"""Ticket state CLI boundaries against disposable tracker fixtures."""
import io
import tempfile
import unittest
from contextlib import nullcontext, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock
from _load import load
vt = load()

class TestStateReads(unittest.TestCase):
    def failed_read(self, part):
        return vt.subprocess.CalledProcessError(1, ["gh", "issue", "view", "440", "--json", part], stderr="HTTP 502")

    def test_comments_read_failure_names_the_read_and_safe_retry(self):
        err = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "closeout.md"
            draft.write_text("ALL MET\n", encoding="utf-8")
            with mock.patch.object(vt.engine, "repo_root", return_value=Path(tmp)), \
                    mock.patch.object(vt, "closeout_lock", return_value=nullcontext()), \
                    mock.patch.object(vt.subprocess, "run",
                                      side_effect=self.failed_read("comments")), \
                    redirect_stderr(err):
                code = vt.main(["440", "--closeout", str(draft)])
        self.assertEqual(code, 2)
        self.assertIn("440", err.getvalue())
        self.assertIn("comments", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())



class TestSharedEngine(unittest.TestCase):
    def test_print_only_run_and_recorded_run_give_the_same_results(self):
        import json
        import os
        import re
        import subprocess
        import sys
        from _load import SCRIPT

        body = """## Owns

- src/**

## Acceptance criteria

- [ ] AC1: matching output passes
  CHECK: echo matched
  EXPECT: matched
  EVIDENCE: pending
- [ ] AC2: unmatched output fails
  CHECK: echo unmatched
  EXPECT: expected
  EVIDENCE: pending
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c",
                            "user.email=test@example.com", "commit", "-qm", "base", "--allow-empty"], check=True)
            fixtures = root / "tracker"
            fixtures.mkdir()
            (fixtures / "body").write_text(body)
            (fixtures / "posts").write_text("[]")
            fake = fixtures / "gh"
            fake.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
root = Path(os.environ["TEST_TRACKER"])
args = sys.argv[1:]
if args[:2] == ["issue", "view"]:
    part = args[args.index("--json") + 1]
    if part == "body": print((root / "body").read_text())
    elif part == "comments": print('{"comments": []}')
    elif part == "parent": print('{"parent": null}')
    else: raise SystemExit("unexpected read: " + part)
elif args[:2] == ["issue", "comment"]:
    store = root / "posts"
    comments = json.loads(store.read_text())
    comments.append(Path(args[args.index("--body-file") + 1]).read_text())
    store.write_text(json.dumps(comments))
else: raise SystemExit("unexpected gh command")
''')
            fake.chmod(0o755)
            env = dict(os.environ, TEST_TRACKER=str(fixtures),
                       PATH=str(fixtures) + os.pathsep + os.environ["PATH"])
            printer = SCRIPT.parents[2] / "verify-ticket" / "scripts" / "verify-ticket.py"
            printed = subprocess.run([sys.executable, str(printer), "991"], cwd=root,
                                     env=env, capture_output=True, text=True)
            self.assertEqual(json.loads((fixtures / "posts").read_text()), [])
            recorded = subprocess.run([sys.executable, str(SCRIPT), "991", "--run-and-record-criteria"],
                                      cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual((printed.returncode, recorded.returncode), (1, 1),
                             printed.stderr + recorded.stderr)
            outcomes = lambda output: re.findall(r"^\s*(?:PASS|FAIL) AC:AC\d+.*$", output, re.M)
            self.assertEqual(len(outcomes(printed.stdout)), 2, printed.stdout)
            self.assertEqual(outcomes(printed.stdout), outcomes(recorded.stdout))
            posts = json.loads((fixtures / "posts").read_text())
            self.assertEqual(len(posts), 1)
            payload = vt.engine.events.parse(posts[0])[1]
            self.assertEqual(payload["event"], "ticket.checked")
            self.assertEqual(payload["counts"], {"met": 1, "unmet": 1, "abandoned": 0, "total": 2})
            self.assertEqual([(c["id"], c["met"]) for c in payload["criteria"]], [("AC1", True), ("AC2", False)])
