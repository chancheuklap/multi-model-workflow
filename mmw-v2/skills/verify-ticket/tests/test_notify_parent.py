"""Telling the session that started this one that the ticket came to rest.

Four runs reach a resting state and call this; what each of them says is asserted
where that run is tested. Here is the call itself: who it reaches, and what it does
when there is nobody to reach.
"""

import io
import unittest
from contextlib import redirect_stderr
from unittest import mock

from tests._load import load

vt = load()

AGENT = "aaaaaaaa-1111-4222-8333-444444444444"
PARENT = "bbbbbbbb-5555-4666-8777-888888888888"


def run(text="#61 ALL MET", env=None, inspect=None, send=None):
    """Call notify_parent with the two `paseo` calls faked; return (calls, stderr)."""
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        answer = inspect if argv[1] == "inspect" else send
        if answer is None:
            answer = mock.Mock(returncode=0, stdout=f'{{"ParentAgentId": "{PARENT}"}}',
                               stderr="")
        if isinstance(answer, Exception):
            raise answer
        return answer

    environ = {"PASEO_AGENT_ID": AGENT} if env is None else env
    with mock.patch.dict(vt.os.environ, environ, clear=True), \
         mock.patch.object(vt.subprocess, "run", side_effect=fake_run), \
         redirect_stderr(io.StringIO()) as err:
        vt.notify_parent(text)
    return calls, err.getvalue()


class TestWhoItReaches(unittest.TestCase):
    def test_the_message_goes_to_the_parent_of_this_session(self):
        calls, err = run()
        self.assertEqual(calls[0][:2], ["paseo", "inspect"])
        self.assertEqual(calls[1], ["paseo", "send", "--no-wait", PARENT, "#61 ALL MET"])
        self.assertEqual(err, "")

    def test_outside_a_paseo_session_nothing_is_run(self):
        calls, err = run(env={})
        self.assertEqual(calls, [])
        self.assertEqual(err, "")

    def test_a_session_with_no_parent_sends_nothing(self):
        calls, _ = run(inspect=mock.Mock(returncode=0, stdout='{"ParentAgentId": null}',
                                         stderr=""))
        self.assertEqual(len(calls), 1)


class TestItNeverBecomesTheStory(unittest.TestCase):
    """The ticket is already posted, closed or handed back by the time this runs. A
    message that cannot be delivered is reported and nothing more: raising here would
    turn a landed ticket into a failed one."""

    def test_an_unreadable_inspect_is_silent(self):
        calls, err = run(inspect=mock.Mock(returncode=1, stdout="", stderr="no such agent"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(err, "")

    def test_inspect_printing_something_that_is_not_json_is_silent(self):
        calls, err = run(inspect=mock.Mock(returncode=0, stdout="not json", stderr=""))
        self.assertEqual(len(calls), 1)
        self.assertEqual(err, "")

    def test_paseo_missing_from_path_is_silent(self):
        calls, err = run(inspect=FileNotFoundError("paseo"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(err, "")

    def test_a_failed_send_is_named_on_stderr(self):
        _, err = run(send=mock.Mock(returncode=1, stdout="", stderr="daemon is down"))
        self.assertIn(PARENT, err)
        self.assertIn("daemon is down", err)


if __name__ == "__main__":
    unittest.main()
