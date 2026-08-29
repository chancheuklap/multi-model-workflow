"""The opening guard: four conditions, and what the ticket is told when one fails."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from tests._load import load

vt = load()

ME = "chancheuklap"


def ticket(state="OPEN", labels=("ready-for-agent",), assignees=(), blockers=()):
    return {
        "state": state,
        "labels": [{"name": name} for name in labels],
        "assignees": [{"login": login} for login in assignees],
        "blockedBy": {"nodes": [{"number": n, "state": s} for n, s in blockers],
                      "totalCount": len(blockers)},
    }


def preflight(number=77, branch="issue-77", dirty=(), **kwargs):
    """Run --preflight against a made-up ticket; return (exit code, what it posted)."""
    posted = []
    with mock.patch.object(vt, "fetch_ticket", return_value=ticket(**kwargs)), \
         mock.patch.object(vt, "gh_login", return_value=ME), \
         mock.patch.object(vt, "current_branch", return_value=branch), \
         mock.patch.object(vt, "dirty_tracked", return_value=list(dirty)), \
         mock.patch.object(vt, "repo_root", return_value=None), \
         mock.patch.object(vt, "report_phase", return_value=False), \
         mock.patch.object(vt, "assign_self") as assign, \
         mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append((n, b))):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
            code = vt.run_preflight(number)
    return code, posted, err.getvalue(), assign


class TestBranch(unittest.TestCase):
    def test_a_branch_that_is_not_the_ticket_is_refused(self):
        code, posted, err, assign = preflight(branch="worktree-upstream-pull")
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("NOT_READY: branch "))
        assign.assert_not_called()

    def test_the_refusal_is_posted_on_the_ticket(self):
        code, posted, err, _ = preflight(branch="main")
        self.assertEqual([n for n, _ in posted], [77])
        self.assertTrue(posted[0][1].startswith("NOT_READY: branch main is not issue-77"))
        self.assertEqual(posted[0][1], err.strip())

    def test_the_right_branch_passes(self):
        code, _, _, assign = preflight(branch="issue-77")
        self.assertEqual(code, 0)
        assign.assert_called_once_with(77)


class TestRefusals(unittest.TestCase):
    def test_uncommitted_changes_to_tracked_files_are_refused(self):
        code, posted, err, assign = preflight(dirty=[" M src/app.py", " M src/other.py"])
        self.assertEqual(code, 2)
        self.assertIn("2 tracked files have uncommitted changes", err)
        assign.assert_not_called()

    def test_untracked_files_alone_do_not_refuse(self):
        # dirty_tracked already excludes them; a run with none of them left is clean.
        code, _, _, assign = preflight(dirty=[])
        self.assertEqual(code, 0)
        assign.assert_called_once()

    def test_a_ticket_without_the_agent_label_is_refused(self):
        code, _, err, assign = preflight(labels=("needs-triage",))
        self.assertEqual(code, 2)
        self.assertIn("no ready-for-agent label", err)
        assign.assert_not_called()

    def test_an_open_blocker_is_refused_and_named(self):
        code, _, err, assign = preflight(blockers=[(62, "CLOSED"), (64, "OPEN")])
        self.assertEqual(code, 2)
        self.assertIn("blocked by #64", err)
        self.assertNotIn("#62", err)
        assign.assert_not_called()

    def test_a_ticket_someone_else_holds_is_refused(self):
        code, _, err, assign = preflight(assignees=("someone-else",))
        self.assertEqual(code, 2)
        self.assertIn("assigned to someone-else", err)
        assign.assert_not_called()

    def test_a_closed_ticket_is_refused(self):
        code, _, err, _ = preflight(state="CLOSED")
        self.assertEqual(code, 2)
        self.assertIn("is CLOSED, not OPEN", err)


class TestIdempotence(unittest.TestCase):
    """Redispatching the same ticket to the same account must not refuse it."""

    def test_a_ticket_already_held_by_me_still_passes(self):
        code, posted, _, assign = preflight(assignees=(ME,))
        self.assertEqual(code, 0)
        self.assertEqual(posted, [])
        assign.assert_called_once_with(77)


if __name__ == "__main__":
    unittest.main()
