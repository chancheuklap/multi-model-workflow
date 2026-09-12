"""A dirty tree `--preflight` lets through is still stopped at `--closeout`.

`--preflight` claims a ticket this account already holds even when tracked files are
uncommitted, and prints `CARRIED:` instead of refusing `dirty-tree`
(`references/claiming.md`). That is safe only because `--closeout` refuses a draft while a
tracked file is uncommitted, so the carried edits cannot reach the base branch without a
commit. `test_preflight.py` and `test_closeout.py` each prove one half against a faked tree;
this file runs both halves, and the `--draft` between them, in one real git working tree
against one tracker whose comments grow as the runs post to it.
"""

import io
import os
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import checked, event, load, started

vt = load()

ME = "chancheuklap"
CRITERION = ["- [x] AC1: the importer writes six rows",
             "  CHECK: pytest -q tests/test_import.py",
             "  EXPECT: /\\d+ passed/",
             "  EVIDENCE: exit=0; EXPECT=matched; output-bytes=9"]
BODY = "\n".join(["## Acceptance criteria", ""] + CRITERION) + "\n"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


class Tracker:
    """One ticket, #77, assigned to this account: its comments grow with every post, and
    closing it is recorded rather than done."""

    def __init__(self, base):
        self.comments = [started(base=base, into="main")]
        self.closed = []
        self.pushed = []

    def post(self, number, body):
        self.comments.append(body)

    def ticket(self, number):
        return {"state": "CLOSED" if self.closed else "OPEN",
                "labels": [{"name": "ready-for-agent"}],
                "assignees": [{"login": ME}], "blockedBy": {"nodes": []}}

    def events(self):
        return [vt.events.parse(body)[1]["event"] for body in self.comments]

    def verified_at(self, commit):
        """The verifier's run of the criteria on `commit`, and its verdict on it."""
        self.comments.append(checked("self", CRITERION, "ALL MET (1 met)", commit=commit))
        self.comments.append(checked("reverify", CRITERION, "ALL MET (1 met)", commit=commit))
        self.comments.append(event("verifier.passed", f"VERDICT {commit} by opus — six rows",
                                   commit=commit))

    def run(self, call, *args):
        """One run of `verify-ticket.py`, as `(exit code, stdout, stderr)`."""
        with mock.patch.object(vt, "fetch_comments", side_effect=lambda n: list(self.comments)), \
             mock.patch.object(vt, "fetch_body", return_value=BODY), \
             mock.patch.object(vt, "fetch_ticket", side_effect=self.ticket), \
             mock.patch.object(vt, "fetch_sub_issues", return_value=[]), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "assign_self"), \
             mock.patch.object(vt, "post_comment", side_effect=self.post), \
             mock.patch.object(vt, "close_ticket", side_effect=self.closed.append), \
             mock.patch.object(vt, "push_ticket_branch",
                               side_effect=lambda *a: self.pushed.append(a)), \
             mock.patch.object(vt, "blocker_fold", return_value=None):
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
                code = call(*args)
        return code, out.getvalue(), err.getvalue()


class TestCarriedEditsAreStoppedAtTheCloseout(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "t@t")
        git(self.root, "config", "user.name", "t")
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("rows = 0\n")
        git(self.root, "add", "src/app.py")
        git(self.root, "commit", "-q", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "-q", "-b", "issue-77")
        (self.root / "src" / "app.py").write_text("rows = 5\n")
        git(self.root, "commit", "-q", "-am", "first turn")
        # The earlier turn's work that was never committed: what `CARRIED:` is about.
        (self.root / "src" / "app.py").write_text("rows = 6\n")
        self.draft = Path(self.tmp.name) / "drafts" / "closeout-77.md"
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        self.tracker = Tracker(self.base)

    def write_draft(self):
        code, out, err = self.tracker.run(vt.run_draft, 77, self.draft)
        self.assertEqual(code, 0, err)
        self.assertIn("DRAFT: wrote", out)
        text = self.draft.read_text(encoding="utf-8")
        self.assertIn(vt.FILL, text)
        self.draft.write_text(text.replace(f"skipped: {vt.FILL}", "skipped: none")
                              .replace(vt.FILL, "None"), encoding="utf-8")

    def test_the_carried_edits_pass_preflight_and_are_refused_at_closeout_until_committed(self):
        tracker = self.tracker
        head = git(self.root, "rev-parse", "HEAD")

        code, out, err = tracker.run(vt.run_preflight, 77)
        self.assertEqual(code, 0, err)
        self.assertIn("READY: #77 claimed on issue-77", out)
        self.assertIn("CARRIED: 1 tracked files have uncommitted changes", out)
        self.assertEqual(tracker.events()[-1], "ticket.claimed")

        # Everything else the closeout asks for is in place on HEAD, so the tree is the
        # one condition left for it to refuse.
        tracker.verified_at(head)
        self.write_draft()
        posted_before = len(tracker.comments)
        code, out, err = tracker.run(vt.run_closeout, 77, self.draft, False)
        self.assertEqual(code, 1, out)
        self.assertTrue(err.startswith("closeout rejected, 1 problem: 1 tracked files have "
                                       "uncommitted changes"), err)
        self.assertEqual(tracker.closed, [])
        self.assertEqual(tracker.pushed, [])
        self.assertEqual(len(tracker.comments), posted_before)
        self.assertEqual(tracker.ticket(77)["state"], "OPEN")
        self.assertEqual(git(self.root, "status", "--porcelain", "--untracked-files=no"),
                         "M src/app.py")

        git(self.root, "commit", "-q", "-am", "carried work")
        committed = git(self.root, "rev-parse", "HEAD")
        code, _, err = tracker.run(vt.run_closeout, 77, self.draft, True)
        self.assertNotIn("uncommitted", err)

        tracker.verified_at(committed)
        self.write_draft()
        code, out, err = tracker.run(vt.run_closeout, 77, self.draft, False)
        self.assertEqual(code, 0, err)
        self.assertIn("CLOSED: #77", out)
        self.assertEqual(tracker.closed, [77])
        self.assertEqual(tracker.pushed, [(77, self.root.resolve(), committed)])
        self.assertEqual(tracker.events()[-1], "ticket.passed")
        self.assertEqual(vt.events.parse(tracker.comments[-1])[1]["commit"], committed)


if __name__ == "__main__":
    unittest.main()
