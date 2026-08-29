"""The Herdr phase token: what it publishes, and the three cases where it stays quiet."""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests._load import load

vt = load()

LIVE = {"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p2"}


class TestReportPhase(unittest.TestCase):
    def test_outside_herdr_nothing_is_reported(self):
        with mock.patch.dict(vt.os.environ, {"HERDR_ENV": "0", "HERDR_PANE_ID": "w1:p2"}, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            self.assertFalse(vt.report_phase(77, "selfcheck"))
            run.assert_not_called()

    def test_without_a_pane_id_nothing_is_reported(self):
        with mock.patch.dict(vt.os.environ, {"HERDR_ENV": "1", "HERDR_PANE_ID": ""}, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            self.assertFalse(vt.report_phase(77, "selfcheck"))
            run.assert_not_called()

    def test_a_failing_socket_is_swallowed(self):
        with mock.patch.dict(vt.os.environ, LIVE, clear=False), \
             mock.patch.object(vt.subprocess, "run", side_effect=OSError("no socket")):
            self.assertFalse(vt.report_phase(77, "selfcheck"))

    def test_the_reported_command_carries_ticket_role_phase_and_ttl(self):
        with mock.patch.dict(vt.os.environ, LIVE, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            self.assertTrue(vt.report_phase(77, "selfcheck"))
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:5], ["herdr", "pane", "report-metadata", "w1:p2", "--source"])
        self.assertEqual(cmd[5], "mmw")
        self.assertIn("ticket=77", cmd)
        self.assertIn("role=worker", cmd)
        self.assertIn("phase=selfcheck", cmd)
        self.assertEqual(cmd[cmd.index("--ttl-ms") + 1], "86400000")

    def test_extra_tokens_are_appended(self):
        with mock.patch.dict(vt.os.environ, LIVE, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            vt.report_phase(77, "selfcheck", {"ac": "1/4"})
        self.assertIn("ac=1/4", run.call_args.args[0])


class TestPhasesOfARun(unittest.TestCase):
    """A run reports at both ends, and the second report carries the count."""

    def run_ticket(self, reverify: bool):
        body = ("## Owns\n\n- src/**\n\n## Acceptance criteria\n\n"
                "- [ ] AC1: the importer writes six rows\n"
                "  CHECK: echo 'wrote 6 rows'\n"
                "  EXPECT: wrote 6 rows\n"
                "  EVIDENCE: pending\n"
                "- [ ] AC2: the empty state is judged by eye\n"
                "  MANUAL: the user reads the baseline scene\n"
                "  EVIDENCE: pending\n")
        calls = []
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "previous_ledger", return_value=[]), \
             mock.patch.object(vt, "outside_owns", return_value=[]), \
             mock.patch.object(vt, "post_comment"), \
             mock.patch.object(vt, "report_phase",
                               side_effect=lambda n, p, extra=None: calls.append((n, p, extra)) or True):
            with redirect_stdout(io.StringIO()):
                vt.run_checks(77, reverify, None)
        return calls

    def test_a_self_check_opens_and_closes_with_the_count(self):
        calls = self.run_ticket(False)
        self.assertEqual(calls[0], (77, "selfcheck", None))
        self.assertEqual(calls[-1], (77, "selfcheck", {"ac": "1/2"}))

    def test_a_reverification_reports_the_verify_phase(self):
        calls = self.run_ticket(True)
        self.assertEqual(calls[0][1], "verify")
        self.assertEqual(calls[-1][1], "verify")


if __name__ == "__main__":
    unittest.main()
