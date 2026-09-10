"""`--review`: post the review report on the ticket and tell the worker in one call.

The report and the telling are one act, so the two things asserted here are that the
comment lands with the first line the worker matches on, and that the session that started
this one is told in the same run.
"""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from _load import load

vt = load()

AGENT = "cccccccc-1111-4222-8333-444444444444"
PARENT = "dddddddd-5555-4666-8777-888888888888"

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

    def __init__(self, *, send_fails=False):
        self.send_fails = send_fails
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
        if cmd[:2] == ["paseo", "inspect"]:
            result.stdout = json.dumps({"ParentAgentId": PARENT})
            return result
        if cmd[:2] == ["paseo", "send"]:
            if self.send_fails:
                result.returncode = 1
                result.stderr = "SEND_FAILED"
            return result
        result.returncode = 1
        result.stderr = "unexpected command: " + " ".join(cmd)
        return result

    def sent(self):
        return [c for c in self.recorded if c[:2] == ["paseo", "send"]]


def run_review(text=REPORT, *, agent=AGENT, send_fails=False, write=True):
    """Run --review against a made-up ticket; return (exit, stderr, fake)."""
    fake = FakeCalls(send_fails=send_fails)
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
        self.assertEqual(fake.posted, [])
        self.assertEqual(fake.sent(), [])

    def test_an_empty_file_is_refused(self):
        code, err, fake = run_review("\n\n")
        self.assertEqual(code, 2)
        self.assertIn("is empty", err)
        self.assertEqual(fake.posted, [])


class TestTellsTheSessionThatStartedIt(unittest.TestCase):
    def test_the_reviewer_tells_its_parent_the_review_landed(self):
        code, err, fake = run_review()
        self.assertEqual(code, 0, err)
        sent = fake.sent()
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][-2], PARENT)
        self.assertEqual(sent[0][-1], "#77 reviewer.reported")

    def test_the_comment_is_posted_before_the_message_goes_out(self):
        code, err, fake = run_review()
        self.assertEqual(code, 0, err)
        order = [c[:3] for c in fake.recorded]
        self.assertLess(order.index(["gh", "issue", "comment"]),
                        order.index(["paseo", "send", "--no-wait"]))

    def test_outside_paseo_the_report_still_lands(self):
        code, err, fake = run_review(agent="")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(fake.posted), 1)
        self.assertEqual(fake.sent(), [])

    def test_a_send_that_fails_says_so_and_leaves_the_exit_code_alone(self):
        code, err, fake = run_review(send_fails=True)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.posted), 1)
        self.assertIn("could not tell", err)


if __name__ == "__main__":
    unittest.main()
