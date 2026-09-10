"""The opening guard: six conditions, and what the ticket is told when one fails."""

import io
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from _load import event, load

vt = load()

ME = "chancheuklap"


def event_of(body):
    """The event a posted comment carries, as `(name, payload)`."""
    what, payload = vt.events.parse(body)
    assert what == "event", (what, payload, body)
    return payload["event"], payload


def ticket(state="OPEN", labels=("ready-for-agent",), assignees=(), blockers=()):
    return {
        "state": state,
        "labels": [{"name": name} for name in labels],
        "assignees": [{"login": login} for login in assignees],
        "blockedBy": {"nodes": [{"number": n, "state": s} for n, s in blockers],
                      "totalCount": len(blockers)},
    }


def preflight(number=77, branch="issue-77", dirty=(), history=None, **kwargs):
    """Run --preflight against a made-up ticket; return (exit code, what it posted).

    `history` is each blocker's comments by number, read when that blocker is closed; a
    blocker it does not name has none, and one it maps to an exception is a blocker the
    tracker did not answer for."""
    posted = []
    history = history or {}

    def comments_of(n):
        found = history.get(n, [])
        if isinstance(found, Exception):
            raise found
        return list(found)

    with mock.patch.object(vt, "fetch_ticket", return_value=ticket(**kwargs)), \
         mock.patch.object(vt, "fetch_comments", side_effect=comments_of), \
         mock.patch.object(vt, "gh_login", return_value=ME), \
         mock.patch.object(vt, "current_branch", return_value=branch), \
         mock.patch.object(vt, "dirty_tracked", return_value=list(dirty)), \
         mock.patch.object(vt, "repo_root", return_value=None), \
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
        self.assertTrue(posted[0][1].startswith("NOT_READY: branch is main, not issue-77"))
        self.assertEqual(vt.events.first_line(posted[0][1]), err.strip())
        name, payload = event_of(posted[0][1])
        self.assertEqual((name, payload["reason"]), ("ticket.refused", "wrong-branch"))

    def test_the_right_branch_passes(self):
        code, _, _, assign = preflight(branch="issue-77")
        self.assertEqual(code, 0)
        assign.assert_called_once_with(77)


class TestRefusals(unittest.TestCase):
    def test_uncommitted_changes_to_tracked_files_are_refused(self):
        code, posted, err, assign = preflight(dirty=[" M src/app.py", " M src/other.py"])
        self.assertEqual(code, 2)
        self.assertIn("2 tracked files already have uncommitted changes", err)
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


PASSED = event("ticket.passed", "ALL MET", ticket=62, commit="a" * 40)
LANDED = event("ticket.landed", "Landed #62 on main", ticket=62)


class TestABlockerLetsGoOnceItHasLanded(unittest.TestCase):
    """The ticket is cut from the base branch and has to find its blocker's work there, so
    a blocker lets go when it lands, not when it closes — the rule the dispatch skill's
    frontier starts tickets by. A preflight that let go on the close would claim a ticket
    whose base does not carry the work it builds on."""

    def blocked(self, state, comments=()):
        return preflight(blockers=[(62, state)], history={62: comments})

    def test_a_blocker_that_passed_and_has_not_landed_holds(self):
        code, posted, err, assign = self.blocked("CLOSED", [PASSED])
        self.assertEqual(code, 2)
        self.assertEqual(event_of(posted[0][1])[1]["reason"], "blocked")
        self.assertIn("blocked by #62 (passed, not landed)", err)
        self.assertIn("once those land", err)
        assign.assert_not_called()

    def test_the_same_blocker_lets_go_once_it_has_landed(self):
        code, posted, err, assign = self.blocked("CLOSED", [PASSED, LANDED])
        self.assertEqual(code, 0, err)
        self.assertEqual(event_of(posted[0][1])[0], "ticket.claimed")
        assign.assert_called_once_with(77)

    def test_a_blocker_closed_without_a_pass_lets_go(self):
        code, _, err, assign = self.blocked("CLOSED")
        self.assertEqual(code, 0, err)
        assign.assert_called_once_with(77)

    def test_an_open_blocker_holds_and_is_named_plainly(self):
        code, posted, err, _ = self.blocked("OPEN")
        self.assertEqual(code, 2)
        self.assertEqual(event_of(posted[0][1])[1]["reason"], "blocked")
        self.assertIn("blocked by #62;", err)

    def test_a_closed_blocker_whose_events_cannot_be_read_holds(self):
        cases = (("its events cannot be read", ["x\n\n<!-- mmw {not json} -->"]),
                 ("the tracker did not answer for it",
                  subprocess.CalledProcessError(1, ["gh", "issue", "view", "62"])))
        for why, comments in cases:
            with self.subTest(why=why):
                code, _, err, assign = self.blocked("CLOSED", comments)
                self.assertEqual(code, 2)
                self.assertIn(f"#62 ({why})", err)
                assign.assert_not_called()


class TestEveryRefusalSaysStop(unittest.TestCase):
    """Each of the six conditions is set up before a worker exists — the host opens the
    worktree on `issue-<n>`, `dispatch.sh` checks state, labels and blockers — so every
    refusal is a fault upstream of the worker, and the only correct next move is to stop.
    A refusal that reads like a repair invites the worker to switch branches, commit
    someone else's work, or take someone else's ticket."""

    ALL_SIX = (
        {"branch": "main"},
        {"dirty": [" M src/app.py"]},
        {"state": "CLOSED"},
        {"labels": ("needs-triage",)},
        {"blockers": [(64, "OPEN")]},
        {"assignees": ("someone-else",)},
    )

    def test_every_refusal_tells_the_worker_to_stop(self):
        for case in self.ALL_SIX:
            with self.subTest(**case):
                _, _, err, _ = preflight(**case)
                self.assertIn("stop", err.lower(), f"no stop in: {err.strip()}")

    def test_no_refusal_tells_the_worker_to_change_the_branch_or_the_tree(self):
        for case in self.ALL_SIX:
            with self.subTest(**case):
                _, _, err, _ = preflight(**case)
                for repair in ("git checkout", "switch to", "create the branch"):
                    self.assertNotIn(repair, err.lower(), f"repair advice in: {err.strip()}")

    def test_every_refusal_is_posted_on_the_ticket_before_exiting(self):
        for case in self.ALL_SIX:
            with self.subTest(**case):
                code, posted, err, assign = preflight(**case)
                self.assertEqual(code, 2)
                self.assertEqual(len(posted), 1)
                self.assertEqual(vt.events.first_line(posted[0][1]), err.strip())
                self.assertEqual(event_of(posted[0][1])[0], "ticket.refused")
                assign.assert_not_called()

    def test_each_refusal_names_its_own_reason_on_the_event(self):
        reasons = [event_of(preflight(**case)[1][0][1])[1]["reason"] for case in self.ALL_SIX]
        self.assertEqual(reasons, list(vt.events.REFUSALS))


class TestIdempotence(unittest.TestCase):
    """Redispatching the same ticket to the same account must not refuse it."""

    def test_a_ticket_already_held_by_me_still_passes(self):
        code, posted, _, assign = preflight(assignees=(ME,))
        self.assertEqual(code, 0)
        self.assertEqual(len(posted), 1)
        name, payload = event_of(posted[0][1])
        self.assertEqual((name, payload["login"], payload["ticket"]),
                         ("ticket.claimed", ME, 77))
        assign.assert_called_once_with(77)


if __name__ == "__main__":
    unittest.main()
