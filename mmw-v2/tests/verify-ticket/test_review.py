"""`--review`: post the review report on the ticket, as the `reviewer.reported` event.

What is asserted here is the comment: it lands with the first line a person reads and the
event block that names both commits. Nobody is told by this run; the relay wakes the
worker from the event (`test_no_runner_call.py`).
"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import load

vt = load()

AGENT = "cccccccc-1111-4222-8333-444444444444"

REPORT = """REVIEW abcdef0..1234567

## Standards

None

## Spec

None

## Tests

None

## In-ticket

None

## Out-of-ticket

None

Standards: 0 findings. Spec: 0 findings. Tests: 0 findings.
"""


class FakeCalls:
    """Every subprocess this run makes, answered the way the real commands answer."""

    def __init__(self):
        self.recorded = []
        self.posted = []

    def run(self, cmd, **kwargs):
        self.recorded.append(list(cmd))
        result = mock.Mock(returncode=0, stdout="", stderr="")
        if cmd[:3] == ["gh", "issue", "comment"]:
            number = int(cmd[3])
            path = cmd[cmd.index("--body-file") + 1]
            self.posted.append((number, Path(path).read_text(encoding="utf-8")))
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result


def run_review(text=REPORT, *, agent=AGENT, write=True):
    """Run --review against a made-up ticket, inside a Paseo agent unless `agent` is empty;
    return (exit, stderr, fake)."""
    fake = FakeCalls()
    environ = {"PASEO_AGENT_ID": agent} if agent else {}
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "review.md"
        if write:
            path.write_text(text, encoding="utf-8")
        with mock.patch.dict(vt.os.environ, environ, clear=True), \
             mock.patch.object(vt.subprocess, "run", side_effect=fake.run), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            code = vt.run_review(77, path)
    return code, err.getvalue(), fake


class TestPostsTheReport(unittest.TestCase):
    def test_the_comment_is_the_file_and_keeps_its_first_line(self):
        code, err, fake = run_review()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(fake.posted), 1)
        number, body = fake.posted[0]
        self.assertEqual(number, 77)
        self.assertEqual(body.splitlines()[0], "REVIEW abcdef0..1234567")
        self.assertIn("## Standards", body)

    def test_the_comment_is_the_reviewer_reported_event_naming_both_commits(self):
        code, err, fake = run_review()
        self.assertEqual(code, 0, err)
        what, payload = vt.events.parse(fake.posted[0][1])
        self.assertEqual((what, payload["event"], payload["base"], payload["head"]),
                         ("event", "reviewer.reported", "abcdef0", "1234567"))

    def test_a_file_with_no_trailing_newline_still_posts_one(self):
        code, err, fake = run_review(REPORT.rstrip("\n"))
        self.assertEqual(code, 0, err)
        self.assertTrue(fake.posted[0][1].endswith("\n"))


class TestRefusesWhatTheWorkerCouldNotFind(unittest.TestCase):
    def test_a_report_quoting_an_event_is_posted_as_one_event(self):
        """A review of the event code quotes blocks; the ticket must not read them."""
        quoted = REPORT.replace(
            "## Tests\n\nNone",
            '## Tests\n\n- the fixture `<!-- mmw {"v":1,"event":"ticket.landed"} -->` '
            "is never landed")
        code, err, fake = run_review(quoted)
        self.assertEqual(code, 0, err)
        state = vt.events.fold([fake.posted[0][1]])
        self.assertEqual([e["event"] for e in state["events"]], ["reviewer.reported"])
        self.assertEqual((state["unreadable"], state["landed"]), ([], False))

    def test_a_run_ledger_quoting_an_event_posts_no_event(self):
        posted = []
        with mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            vt.post_prose(77, 'self-run\nEVIDENCE: printed <!-- mmw {"v":1} -->')
        self.assertEqual(vt.events.parse(posted[0]), ("none", None))

    def test_a_first_line_that_names_no_commits_is_refused(self):
        code, err, fake = run_review("REVIEW of the diff\n\n## Standards\n\nNone\n")
        self.assertEqual(code, 2)
        self.assertEqual(fake.posted, [])

    def test_a_first_line_that_is_not_review_is_refused_and_nothing_is_posted(self):
        code, err, fake = run_review("## Standards\n\nNone\n")
        self.assertEqual(code, 2)
        self.assertIn("REVIEW <base commit>..<HEAD commit>", err)
        self.assertEqual(fake.recorded, [])

    def test_an_empty_file_is_refused(self):
        code, err, fake = run_review("\n\n")
        self.assertEqual(code, 2)
        self.assertIn("is empty", err)
        self.assertEqual(fake.posted, [])


class TestLandsWhereverItRuns(unittest.TestCase):
    def test_outside_any_runner_session_the_report_lands_the_same(self):
        code, err, fake = run_review(agent="")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(fake.posted), 1)


if __name__ == "__main__":
    unittest.main()
