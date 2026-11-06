"""Brief copy and result-ownership contracts ported from the v4 brief suite."""
from __future__ import annotations
import sys, os, json, subprocess, tempfile, unittest
from unittest import mock
from pathlib import Path
SCRIPTS = Path(__file__).resolve().parents[2] / "tools/dispatch/scripts"
sys.path.insert(0, str(SCRIPTS))
import briefs
PARENT = ("orca", "term_parent")

class BriefCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patch = mock.patch.dict(os.environ, {"MMW_HOME": self.tmp.name})
        patch.start()
        self.addCleanup(patch.stop)
        self.state = briefs.statedir.state_dir("o/r")
        self.batch = briefs.create(self.state, "researcher", 2, *PARENT)
        for n, session in ((1, "agt_r1"), (2, "agt_r2")):
            briefs.mark_started(self.state, self.batch, n, {
                "runner": "paseo", "session": session, "host": "codex",
                "model": "test-model", "effort": "high"})
        self.result = Path(self.tmp.name) / "answer.md"
        self.result.write_text("the findings, cited\n")

    def report(self, n, session=None):
        return briefs.report(self.state, self.batch, n, self.result, "paseo", session or f"agt_r{n}")


class CopyTest(BriefCase):
    """`briefs.py brief`: the file a child is pointed at is the brief, then how to report."""

    def test_briefs_checks_references_to_closed_batches(self):
        source = Path(self.tmp.name) / "follow-up.md"
        for batch, code in ((self.batch, 0), ("19990101-000000-abcd", 2)):
            for pointer in (f"briefs/{batch}/1/result.md",
                            str(briefs.batch_dir(self.state, batch) / "1/result.md")):
                source.write_text(f"Read [the answer]({pointer}).\n")
                run = subprocess.run(
                    [sys.executable, briefs.__file__, "check-references", "--repo", "o/r",
                     str(source)], capture_output=True, text=True)
                self.assertEqual(run.returncode, code, run.stderr)
                if code:
                    self.assertIn(str(source), run.stderr)
                    self.assertIn(batch, run.stderr)
                    self.assertIn("include the needed answer", run.stderr)
                    self.assertTrue(run.stderr.isascii(), run.stderr)
        briefs.remove(self.state, self.batch)
        source.write_text(f"Read briefs/{self.batch}/1/result.md.\n")
        run = subprocess.run(
            [sys.executable, briefs.__file__, "check-references", "--repo", "o/r",
             str(source)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn(self.batch, run.stderr)

    def test_the_copy_is_the_brief_then_the_footer(self):
        source = Path(self.tmp.name) / "brief.txt"
        source.write_text("what to find out\n\n")
        copy = briefs.write_brief(self.state, self.batch, 1, source, "---\nreport it\n")
        self.assertEqual(copy, briefs.batch_dir(self.state, self.batch) / "1" / "brief.md")
        self.assertEqual(copy.read_text(), "what to find out\n\n---\nreport it\n")

    def test_nothing_is_copied_into_a_batch_that_is_gone(self):
        briefs.remove(self.state, self.batch)
        with self.assertRaises(briefs.Refusal):
            briefs.write_brief(self.state, self.batch, 1, self.result, "---")

    def test_a_new_batch_records_the_senders_worktree(self):
        worktree = Path(self.tmp.name) / "sender"
        worktree.mkdir()
        subprocess.run(["git", "init", "-q", str(worktree)], check=True)
        subdir = worktree / "notes"
        subdir.mkdir()
        run = subprocess.run(
            [sys.executable, briefs.__file__, "new", "--repo", "o/r", "--role",
             "researcher", "--count", "1", "--runner", "orca", "--session", "sender"],
            cwd=subdir, env=os.environ.copy(),
            capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        state = briefs.statedir.state_dir("o/r")
        record = briefs.batch_record(state, run.stdout.strip())
        self.assertEqual(record.get("worktree"), str(worktree.resolve()))

class ReportTest(BriefCase):
    def test_an_empty_answer_is_refused(self):
        self.result.write_text("  \n")
        with self.assertRaises(briefs.Refusal):
            self.report(1)
        self.assertEqual(briefs.briefs_of(self.state, self.batch)[0]["state"], "open")

    def test_a_brief_marked_lost_takes_no_late_report(self):
        self.assertTrue(briefs.mark_lost(self.state, self.batch, 1, "paseo says stopped"))
        with self.assertRaises(briefs.Refusal) as caught:
            self.report(1)
        self.assertIn("lost", str(caught.exception))

    def test_a_report_to_a_closed_batch_is_refused(self):
        briefs.remove(self.state, self.batch)
        with self.assertRaises(briefs.Refusal):
            self.report(1)

class EarlyReportTest(BriefCase):
    def test_answer_waits_for_matching_startup_identity_before_completing(self):
        batch = briefs.create(self.state, "researcher", 1, *PARENT)
        kept = briefs.report(self.state, batch, 1, self.result, "paseo", "fast-child")
        self.assertEqual(kept.read_text(), "the findings, cited\n")
        self.assertFalse(briefs.complete(self.state, batch))
        self.assertEqual(briefs.briefs_of(self.state, batch)[0]["state"], "starting")
        briefs.mark_started(self.state, batch, 1, {"runner": "paseo", "session": "fast-child"})
        self.assertTrue(briefs.complete(self.state, batch))
        self.assertEqual(briefs.briefs_of(self.state, batch)[0]["state"], "reported")

    def test_an_early_answer_from_another_session_cannot_complete_the_task(self):
        batch = briefs.create(self.state, "researcher", 1, *PARENT)
        briefs.report(self.state, batch, 1, self.result, "paseo", "other-child")
        with self.assertRaisesRegex(briefs.Refusal, "different session"):
            briefs.mark_started(self.state, batch, 1, {"runner": "paseo", "session": "real-child"})
        self.assertFalse(briefs.complete(self.state, batch))
        self.assertIsNone(briefs.briefs_of(self.state, batch)[0]["result"])

    def test_lost_startup_does_not_promote_a_pending_answer_to_reported(self):
        batch = briefs.create(self.state, "researcher", 1, *PARENT)
        briefs.report(self.state, batch, 1, self.result, "paseo", "fast-child")
        self.assertTrue(briefs.mark_lost(self.state, batch, 1, "startup failed"))
        with self.assertRaisesRegex(briefs.Refusal, "already lost"):
            briefs.mark_started(self.state, batch, 1, {"runner": "paseo", "session": "fast-child"})
        self.assertEqual(briefs.briefs_of(self.state, batch)[0]["state"], "lost")
        self.assertIsNone(briefs.briefs_of(self.state, batch)[0]["result"])


if __name__ == "__main__":
    unittest.main()
