"""The Herdr phase token: what it publishes, and the three cases where it stays quiet."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests._load import load

vt = load()

LIVE = {"HERDR_ENV": "1", "HERDR_PANE_ID": "w1:p2"}
COMMIT = "3f9c2e1adeadbeefcafe0123456789abcdef0123"


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
        self.assertIn("kind=worker", cmd)
        self.assertIn("phase=selfcheck", cmd)
        self.assertEqual(cmd[cmd.index("--ttl-ms") + 1], "86400000")

    def test_extra_tokens_are_appended(self):
        with mock.patch.dict(vt.os.environ, LIVE, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            vt.report_phase(77, "selfcheck", {"ac": "1/4"})
        self.assertIn("ac=1/4", run.call_args.args[0])

    def test_a_token_can_be_cleared(self):
        with mock.patch.dict(vt.os.environ, LIVE, clear=False), \
             mock.patch.object(vt.subprocess, "run") as run:
            vt.report_phase(77, "closed", clear=["ac"])
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[cmd.index("--clear-token") + 1], "ac")


class TestPhasesOfARun(unittest.TestCase):
    """A run reports at both ends, and the second report carries the count."""

    def run_ticket(self, reverify: bool):
        body = ("## Owns\n\n- src/**\n\n## Acceptance criteria\n\n"
                "- [ ] AC1: the importer writes six rows\n"
                "  CHECK: echo 'wrote 6 rows'\n"
                "  EXPECT: wrote 6 rows\n"
                "  EVIDENCE: pending\n"
                "- [ ] AC2: the empty state carries the placeholder line\n"
                "  CHECK: echo 'placeholder shown'\n"
                "  EXPECT: placeholder shown\n"
                "  EVIDENCE: pending\n")
        calls = []
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "previous_ledger", return_value=[]), \
             mock.patch.object(vt, "outside_owns", return_value=[]), \
             mock.patch.object(vt, "post_comment"), \
             mock.patch.object(vt, "fetch_comments", return_value=[]), \
             mock.patch.object(vt, "report_phase",
                               side_effect=lambda n, p, extra=None: calls.append((n, p, extra)) or True):
            with redirect_stdout(io.StringIO()):
                vt.run_checks(77, reverify, None)
        return calls

    def test_a_self_check_opens_and_closes_with_the_count(self):
        calls = self.run_ticket(False)
        self.assertEqual(calls[0], (77, "selfcheck", None))
        self.assertEqual(calls[-1], (77, "selfcheck", {"ac": "2/2"}))

    def test_a_reverification_reports_the_verify_phase(self):
        calls = self.run_ticket(True)
        self.assertEqual(calls[0][1], "verify")
        self.assertEqual(calls[-1][1], "verify")


class TestPreflightCloseout(unittest.TestCase):
    """Where a ticket stands after the guard at each end of the work."""

    def preflight(self, refused: bool):
        calls = []
        with mock.patch.object(vt, "fetch_ticket", return_value={
                "state": "OPEN", "labels": [{"name": "ready-for-agent"}],
                "assignees": [], "blockedBy": {"nodes": []}}), \
             mock.patch.object(vt, "gh_login", return_value="chancheuklap"), \
             mock.patch.object(vt, "current_branch",
                               return_value="main" if refused else "issue-77"), \
             mock.patch.object(vt, "dirty_tracked", return_value=[]), \
             mock.patch.object(vt, "repo_root", return_value=None), \
             mock.patch.object(vt, "assign_self"), \
             mock.patch.object(vt, "post_comment"), \
             mock.patch.object(vt, "report_phase",
                               side_effect=lambda n, p, extra=None, clear=None:
                               calls.append((n, p, extra, clear)) or True):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = vt.run_preflight(77)
        return code, calls

    DRAFTS = {
        "closed": ("ALL MET",
                   "- [x] AC1: the importer writes six rows",
                   '  EVIDENCE: exit=0; matched "6 passed"',
                   "Counts: 1 met, 0 unmet, 0 abandoned of 1"),
        "handoff": ("HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1",
                    "- [ ] AC1: the importer writes six rows\n"
                    "  EVIDENCE: exit 1; \"0 rows\"\n"
                    "ABANDON: AC1 stuck the fixture database is not on this machine",
                    "",
                    "Counts: 0 met, 0 unmet, 1 abandoned of 1"),
        "rejected": ("ALL MET",
                     "- [x] AC1: the importer writes six rows",
                     "  EVIDENCE: pending",
                     "Counts: 1 met, 0 unmet, 0 abandoned of 1"),
    }

    def closeout(self, outcome: str):
        calls = []
        first, criterion, evidence, counts = self.DRAFTS[outcome]
        draft = "\n".join([
            first, "", f"Branch: issue-77  Commit: {COMMIT}  PR: none", "",
            criterion, evidence,
            "", "Outside Owns: None", "", "Sub-issues opened: none", "", counts,
        ]) + "\n"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "closeout.md"
            path.write_text(draft, encoding="utf-8")
            with mock.patch.object(vt, "fetch_comments",
                                   return_value=[f"VERDICT {COMMIT} by opus — the importer writes six rows"]), \
                 mock.patch.object(vt, "fetch_ticket", return_value={
                     "state": "OPEN", "labels": [],
                     "assignees": [{"login": "chancheuklap"}], "blockedBy": {"nodes": []}}), \
                 mock.patch.object(vt, "gh_login", return_value="chancheuklap"), \
                 mock.patch.object(vt, "repo_root", return_value=None), \
                 mock.patch.object(vt, "git", return_value=COMMIT), \
                 mock.patch.object(vt, "is_ancestor", return_value=True), \
                 mock.patch.object(vt, "dirty_tracked", return_value=[]), \
                 mock.patch.object(vt, "post_comment"), \
                 mock.patch.object(vt, "close_ticket"), \
                 mock.patch.object(vt, "hand_back_for_triage"), \
                 mock.patch.object(vt, "report_phase",
                                   side_effect=lambda n, p, extra=None, clear=None:
                                   calls.append((n, p, extra, clear)) or True):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = vt.run_closeout(77, path, False)
        return code, calls

    def test_a_claimed_ticket_moves_to_implement(self):
        code, calls = self.preflight(refused=False)
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(77, "implement", None, None)])

    def test_a_refused_claim_reports_no_phase(self):
        code, calls = self.preflight(refused=True)
        self.assertEqual(code, 2)
        self.assertEqual(calls, [])

    def test_a_closed_ticket_clears_the_criteria_count(self):
        code, calls = self.closeout("closed")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(77, "closed", None, ["ac"])])

    def test_a_handed_off_ticket_reports_handoff_and_clears_the_count(self):
        code, calls = self.closeout("handoff")
        self.assertEqual(code, 0)
        self.assertEqual(calls, [(77, "handoff", None, ["ac"])])

    def test_a_refused_draft_reports_closeout_rejected(self):
        code, calls = self.closeout("rejected")
        self.assertEqual(code, 1)
        self.assertEqual(calls, [(77, "closeout-rejected", None, None)])


if __name__ == "__main__":
    unittest.main()
