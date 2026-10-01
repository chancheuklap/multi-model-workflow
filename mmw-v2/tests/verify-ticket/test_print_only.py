"""Criteria printing and retired state commands leave the tracker unchanged."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from _load import load

vt = load()
BODY = """## Acceptance criteria

- [ ] AC1: the command reports its result
  CHECK: echo result
  EXPECT: result
  EVIDENCE: pending
"""


class TestPrintOnly(unittest.TestCase):
    def test_print_only_run_posts_no_event(self):
        with mock.patch.object(vt, "fetch_body", return_value=BODY), \
                mock.patch.object(vt, "fetch_comments", return_value=[]), \
                mock.patch.object(vt, "post_comment") as post, \
                redirect_stdout(io.StringIO()) as output:
            code = vt.main(["1"])
        self.assertEqual(code, 0, output.getvalue())
        self.assertIn("PASS AC:AC1", output.getvalue())
        post.assert_not_called()

    def test_old_state_flags_are_refused_with_the_ticket_state_command(self):
        commands = {
            "--preflight": "--claim", "--draft": "--closing-draft",
            "--sub-issue": "--open-child", "--closeout": "--closeout",
            "--check-only": "--closeout", "--decisions": "--decisions",
            "--review": "--review", "--touched": "--touched",
            "--actor": "--run-and-record-criteria --reverify --actor",
        }
        for flag, command in commands.items():
            with self.subTest(flag=flag), \
                    mock.patch.object(vt.subprocess, "run") as external, \
                    redirect_stderr(io.StringIO()) as err:
                code = vt.main(["1", flag])
                self.assertEqual(code, 2)
                self.assertEqual(len(err.getvalue().splitlines()), 1)
                self.assertIn("ticket_state.py 1 " + command, err.getvalue())
                external.assert_not_called()

    def test_print_only_run_without_a_free_slot_exits_3(self):
        import json
        import tempfile
        from pathlib import Path
        from _load import git_repo, lease_in, SCRIPT

        with tempfile.TemporaryDirectory() as tmp:
            main = Path(tmp) / "main"
            main.mkdir()
            sh = git_repo(main)
            (main / ".mmw").mkdir()
            (main / ".mmw" / "target.json").write_text(json.dumps({"instance": {"max": 1}}))
            sh("add", ".mmw/target.json")
            sh("commit", "-qm", "base")
            root = main / ".worktrees" / "issue-1"
            other = main / ".worktrees" / "issue-2"
            sh("worktree", "add", "-q", "-b", "issue-1", str(root))
            sh("worktree", "add", "-q", "-b", "issue-2", str(other))
            lease = lease_in(Path(tmp) / "home")
            lease.try_claim(other.resolve())
            marker = root / "criterion-ran"
            product = BODY.replace("echo result", f"touch '{marker}'; echo journey.py")
            with mock.patch.object(vt, "fetch_body", return_value=product), \
                    mock.patch.object(vt, "fetch_comments", return_value=[]), \
                    mock.patch.object(vt, "load_lease", return_value=lease), \
                    mock.patch.object(vt, "post_comment") as post, \
                    mock.patch.object(vt, "repo_root", return_value=root), \
                    mock.patch.object(vt, "TOOLS", [SCRIPT.parents[2] / "ui-acceptance" / "scripts"]), \
                    redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = vt.run_checks(1, False)
            self.assertEqual(code, 3, err.getvalue())
            self.assertFalse(marker.exists(), "the criterion ran without a free product slot")
            self.assertNotIn("AC:AC1", out.getvalue())
            self.assertEqual([record["worktree"] for record in lease.claimed()], [str(other.resolve())])
            post.assert_not_called()
