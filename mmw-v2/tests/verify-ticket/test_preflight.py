"""The opening guard: six conditions, and what the ticket is told when one fails."""

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
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
    """A run of `run_preflight`, as `(exit code, what it posted, stderr, the assign mock)`.

    `stdout` says the same thing again for the runs that print there: `run` returns it as
    a fifth value, and everything else about the two is the same.
    """
    return run(number=number, branch=branch, dirty=dirty, history=history, **kwargs)[:4]


def run(number=77, branch="issue-77", dirty=(), history=None, **kwargs):
    """Run --preflight against a made-up ticket; return (exit code, what it posted,
    stderr, the assign mock, stdout).

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
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = vt.run_preflight(number)
    return code, posted, err.getvalue(), assign, out.getvalue()


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
    """Each of the six conditions, once it refuses, is a fault upstream of the worker —
    the host opens the worktree on `issue-<n>`, `dispatch.sh` checks state, labels and
    blockers, and a tree the worker's own claim does not account for was dirty before it
    arrived — so the only correct next move is to stop. A refusal that reads like a repair
    invites the worker to switch branches, commit someone else's work, or take someone
    else's ticket."""

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


class TestTheTreeOnATicketThisAccountAlreadyHolds(unittest.TestCase):
    """A worker enters the ticket through `--preflight` every time, the turn it is
    prompted back into after a review included (the `implement` skill's claim and resume). On that turn
    the uncommitted tracked changes are its own work from an earlier turn, so refusing
    them as `dirty-tree` ends a live worker's hold: the ticket then reads `live: false`
    while the session goes on posting events, and `advance` offers to retract a worker
    that is working. The claim is what tells the two trees apart."""

    def test_a_dirty_tree_is_claimed_again_when_this_account_already_holds_the_ticket(self):
        code, posted, err, assign = preflight(
            assignees=(ME,), dirty=[" M src/app.py", " M src/other.py"])
        self.assertEqual(code, 0, err)
        self.assertEqual(event_of(posted[0][1])[0], "ticket.claimed")
        assign.assert_called_once_with(77)

    def test_it_says_the_changes_are_the_worker_s_own_and_have_to_be_committed(self):
        _, _, _, _, out = run(assignees=(ME,), dirty=[" M src/app.py", " M src/other.py"])
        self.assertIn("2 tracked files", out)
        self.assertIn("commit", out.lower())
        self.assertIn("--closeout", out)

    def test_a_dirty_tree_on_a_ticket_nobody_holds_is_still_refused(self):
        code, posted, err, assign = preflight(dirty=[" M src/app.py"])
        self.assertEqual(code, 2)
        self.assertEqual(event_of(posted[0][1])[1]["reason"], "dirty-tree")
        self.assertIn("#77 is claimed by nobody", err)
        assign.assert_not_called()

    def test_a_clean_tree_says_nothing_about_uncommitted_changes(self):
        _, _, _, _, out = run(assignees=(ME,), dirty=[])
        self.assertNotIn("uncommitted", out)


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


class TestBaselineRun(unittest.TestCase):
    """After a successful claim, `--preflight` runs non-slot criteria at the base commit."""

    BODY = """## Parent

#118, Implementation Decisions section 11

## Acceptance criteria

- [ ] AC1: a file the base already has
  CHECK: cat ok.txt
  EXPECT: ok
  EVIDENCE: pending
- [ ] AC2: a file only this ticket adds
  CHECK: cat later.txt
  EXPECT: later
  EVIDENCE: pending
- [ ] AC3: a story
  CHECK: story-parity.py --pages unused
  EXPECT: PARITY OK
  EVIDENCE: pending
- [ ] AC4: a journey
  CHECK: journey.py run unused
  EXPECT: JOURNEY OK unused
  EVIDENCE: pending
"""

    def repo(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.test",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.test"}
        subprocess.run(["git", "init", "-b", "issue-77"], cwd=root, check=True,
                       capture_output=True, env=env)
        (root / "ok.txt").write_text("ok\n", encoding="utf-8")
        subprocess.run(["git", "add", "ok.txt"], cwd=root, check=True,
                       capture_output=True, env=env)
        subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True,
                       capture_output=True, env=env)
        base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True).strip()
        (root / "later.txt").write_text("later\n", encoding="utf-8")
        subprocess.run(["git", "add", "later.txt"], cwd=root, check=True,
                       capture_output=True, env=env)
        subprocess.run(["git", "commit", "-m", "later"], cwd=root, check=True,
                       capture_output=True, env=env)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                       text=True).strip()
        return root, base, head

    def claim(self, root, base, comments=None, body=None):
        from _load import started
        history = comments if comments is not None else [
            started(ticket=77, base=base, into="spec-337",
                    worktree=str(root), branch="issue-77")]
        posted = []
        with mock.patch.object(vt, "fetch_ticket", return_value=ticket()), \
             mock.patch.object(vt, "fetch_comments", return_value=history), \
             mock.patch.object(vt, "fetch_body", return_value=body or self.BODY), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "current_branch", return_value="issue-77"), \
             mock.patch.object(vt, "dirty_tracked", return_value=[]), \
             mock.patch.object(vt, "repo_root", return_value=root), \
             mock.patch.object(vt, "assign_self") as assign, \
             mock.patch.object(vt, "post_comment",
                               side_effect=lambda n, b: posted.append((n, b))):
            with redirect_stdout(io.StringIO()) as out, \
                    redirect_stderr(io.StringIO()) as err:
                code = vt.run_preflight(77)
        return code, posted, err.getvalue(), out.getvalue(), assign

    def test_a_criterion_already_true_on_the_base_is_met_and_the_new_one_is_not(self):
        root, base, head = self.repo()
        code, posted, err, out, assign = self.claim(root, base)
        self.assertEqual(code, 0, err)
        assign.assert_called_once_with(77)
        self.assertIn("READY:", out)
        names = [event_of(body)[0] for _, body in posted]
        self.assertEqual(names[0], "ticket.claimed")
        self.assertIn("ticket.checked", names)
        payload = event_of(posted[1][1])[1]
        self.assertEqual(payload["run"], "baseline")
        self.assertEqual(payload["commit"], base)
        self.assertEqual(payload["actor"], "worker")
        self.assertEqual(payload["stage"], "claim")
        self.assertEqual(payload["result"], "unmet")
        by_id = {c["id"]: c for c in payload["criteria"]}
        self.assertTrue(by_id["AC1"]["met"], by_id)
        self.assertFalse(by_id["AC2"]["met"], by_id)
        self.assertEqual(sorted(payload["skipped"]), ["AC3", "AC4"])
        self.assertEqual(head, subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip())
        self.assertTrue((root / "later.txt").is_file())
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)

    def test_a_red_baseline_does_not_refuse_the_claim(self):
        root, base, _ = self.repo()
        code, posted, err, out, assign = self.claim(root, base)
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("READY:"), out)
        self.assertEqual(event_of(posted[0][1])[0], "ticket.claimed")
        assign.assert_called_once()

    def test_the_same_base_is_not_run_twice(self):
        from _load import started, checked
        root, base, _ = self.repo()
        already = checked("baseline",
                          ["- [x] AC1: a file the base already has",
                           "  CHECK: cat ok.txt", "  EXPECT: ok",
                           "  EVIDENCE: exit=0"],
                          ticket=77, commit=base)
        history = [started(ticket=77, base=base, into="spec-337",
                           worktree=str(root), branch="issue-77"), already]
        code, posted, err, _, _ = self.claim(root, base, comments=history)
        self.assertEqual(code, 0, err)
        self.assertEqual([event_of(b)[0] for _, b in posted], ["ticket.claimed"])

    def test_a_newer_base_runs_again(self):
        from _load import started, checked
        root, base, head = self.repo()
        already = checked("baseline",
                          ["- [x] AC1: a file the base already has",
                           "  CHECK: cat ok.txt", "  EXPECT: ok",
                           "  EVIDENCE: exit=0"],
                          ticket=77, commit=base)
        history = [started(ticket=77, base=head, into="spec-337",
                           worktree=str(root), branch="issue-77"), already]
        code, posted, err, _, _ = self.claim(root, head, comments=history)
        self.assertEqual(code, 0, err)
        names = [event_of(b)[0] for _, b in posted]
        self.assertEqual(names[0], "ticket.claimed")
        self.assertIn("ticket.checked", names)
        payload = event_of(posted[1][1])[1]
        self.assertEqual(payload["run"], "baseline")
        self.assertEqual(payload["commit"], head)

    def test_no_worker_started_skips_the_baseline_run(self):
        root, base, _ = self.repo()
        code, posted, err, _, _ = self.claim(root, base, comments=[])
        self.assertEqual(code, 0, err)
        self.assertEqual([event_of(b)[0] for _, b in posted], ["ticket.claimed"])
        self.assertIn("baseline run did not start", err)
        self.assertIn("no worker.started.base commit", err)

    def test_a_missing_base_commit_does_not_refuse_the_claim(self):
        root, _, _ = self.repo()
        missing = "a" * 40
        code, posted, err, out, assign = self.claim(root, missing)
        self.assertEqual(code, 0, err)
        self.assertIn("READY:", out)
        assign.assert_called_once()
        self.assertEqual(event_of(posted[0][1])[0], "ticket.claimed")
        payload = event_of(posted[1][1])[1]
        self.assertEqual(payload["run"], "baseline")
        self.assertEqual(payload["commit"], missing)
        self.assertEqual(payload["result"], "unmet")
        self.assertEqual(sorted(payload["skipped"]), ["AC1", "AC2", "AC3", "AC4"])
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)

    def test_gate_check_exit_2_is_not_a_criteria_result(self):
        self.assertIsNone(vt.check_run_outcome(2, "ALL MET (1 met)"))
        self.assertEqual(vt.check_run_outcome(0, "ALL MET (1 met)"), "met")
        self.assertEqual(vt.check_run_outcome(1, "UNMET: 1 (met: 0)"), "unmet")

    def test_every_criterion_skipped_is_not_a_pass(self):
        body = """## Acceptance criteria

- [ ] AC1: a journey
  CHECK: journey.py run unused
  EXPECT: JOURNEY OK unused
  EVIDENCE: pending
"""
        root, base, _ = self.repo()
        code, posted, err, out, _ = self.claim(root, base, body=body)
        self.assertEqual(code, 0, err)
        self.assertIn("READY:", out)
        payload = event_of(posted[1][1])[1]
        self.assertEqual(payload["run"], "baseline")
        self.assertEqual(payload["result"], "unmet")
        self.assertEqual(payload["skipped"], ["AC1"])
        self.assertIn("nothing ran", posted[1][1])
        self.assertNotIn("ALL MET", posted[1][1])


if __name__ == "__main__":
    unittest.main()
