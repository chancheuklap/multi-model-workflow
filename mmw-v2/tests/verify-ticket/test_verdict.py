"""`--verdict`: the verifier's one line becomes `verifier.passed` or `verifier.failed`.

Which of the two it is, and the commit it covers, are read by the script — off HEAD and
off the verifier's own newest `reverify` run — never typed by the verifier.
"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from _load import load

vt = load()

HEAD = "9b1d40c7feedface0011223344556677889900aa"

REVERIFY_MET = "\n".join([
    "reverify", "ALL MET (1 met)", "",
    "- [x] AC1: the importer writes six rows",
    "  EVIDENCE: exit=0; EXPECT=matched", "", "Outside Owns: None"])
REVERIFY_UNMET = "\n".join([
    "reverify", "UNMET: 1 (met: 1)", "",
    "- [x] AC1: the importer writes six rows",
    "  EVIDENCE: exit=0; EXPECT=matched",
    "- [ ] AC2: the expiry page says the link is stale",
    "  EVIDENCE: exit=1", "", "Outside Owns: None"])


def verdict(line, comments, model="sonnet-5", head=HEAD):
    """Run --verdict against a made-up ticket; return (exit, stderr, posted)."""
    posted = []
    with mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
         mock.patch.object(vt, "git", side_effect=lambda *a, cwd=None: head
                           if a == ("rev-parse", "HEAD") else ""), \
         mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append((n, b))):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            code = vt.run_verdict(77, line, model)
    return code, err.getvalue(), posted


def event_of(body):
    what, payload = vt.events.parse(body)
    assert what == "event", (what, payload)
    return payload


class TestTheRunDecides(unittest.TestCase):
    def test_an_all_met_reverify_is_a_pass_on_head(self):
        code, err, posted = verdict("commands only; all passed", [REVERIFY_MET])
        self.assertEqual(code, 0, err)
        self.assertEqual([n for n, _ in posted], [77])
        payload = event_of(posted[0][1])
        self.assertEqual((payload["event"], payload["commit"], payload["model"], payload["ran"]),
                         ("verifier.passed", HEAD, "sonnet-5", True))
        self.assertEqual(posted[0][1].splitlines()[0],
                         f"VERDICT {HEAD} by sonnet-5 — commands only; all passed")

    def test_a_reverify_with_unmet_criteria_is_a_failure_naming_them(self):
        code, err, posted = verdict("commands only; AC2 failed", [REVERIFY_UNMET])
        self.assertEqual(code, 0, err)
        payload = event_of(posted[0][1])
        self.assertEqual((payload["event"], payload["failed"]), ("verifier.failed", ["AC2"]))

    def test_the_line_cannot_turn_a_failed_run_into_a_pass(self):
        code, err, posted = verdict("commands only; all passed", [REVERIFY_UNMET])
        self.assertEqual(code, 0, err)
        self.assertEqual(event_of(posted[0][1])["event"], "verifier.failed")

    def test_could_not_start_is_a_failure_whose_criteria_never_ran(self):
        code, err, posted = verdict("could not start: chromium is missing", [REVERIFY_MET])
        self.assertEqual(code, 0, err)
        payload = event_of(posted[0][1])
        self.assertEqual((payload["event"], payload["ran"]), ("verifier.failed", False))
        self.assertNotIn("failed", payload)


class TestRefusals(unittest.TestCase):
    def test_no_reverify_run_is_refused_and_nothing_is_posted(self):
        code, err, posted = verdict("commands only; all passed", ["self-run\nALL MET (1 met)"])
        self.assertEqual(code, 2)
        self.assertIn("no `reverify` comment", err)
        self.assertEqual(posted, [])

    def test_no_model_is_refused(self):
        code, err, posted = verdict("commands only; all passed", [REVERIFY_MET], model=" ")
        self.assertEqual(code, 2)
        self.assertEqual(posted, [])

    def test_an_unreadable_head_is_refused(self):
        code, err, posted = verdict("commands only; all passed", [REVERIFY_MET], head="")
        self.assertEqual(code, 2)
        self.assertEqual(posted, [])

    def test_model_without_verdict_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            vt.main(["77", "--model", "sonnet-5"])


if __name__ == "__main__":
    unittest.main()
