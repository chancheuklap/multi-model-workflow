"""The opening guard: six conditions, and what the ticket is told when one fails."""

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import checked, event, load

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


def run(number=77, branch="issue-77", dirty=(), history=None, body="", **kwargs):
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
         mock.patch.object(vt, "fetch_body", return_value=body), \
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
    def test_the_refusal_is_posted_on_the_ticket(self):
        code, posted, err, _ = preflight(branch="main")
        self.assertEqual([n for n, _ in posted], [77])
        self.assertTrue(posted[0][1].startswith("NOT_READY:"))
        self.assertIn("main", vt.events.first_line(posted[0][1]))
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
        assign.assert_not_called()

    def test_untracked_files_alone_do_not_refuse(self):
        # dirty_tracked already excludes them; a run with none of them left is clean.
        code, _, _, assign = preflight(dirty=[])
        self.assertEqual(code, 0)
        assign.assert_called_once()

    def test_a_ticket_without_the_agent_label_is_refused(self):
        code, _, err, assign = preflight(labels=("needs-triage",))
        self.assertEqual(code, 2)
        self.assertIn("ready-for-agent", err)
        assign.assert_not_called()

    def test_an_open_blocker_is_refused_and_named(self):
        code, _, err, assign = preflight(blockers=[(62, "CLOSED"), (64, "OPEN")])
        self.assertEqual(code, 2)
        self.assertIn("#64", err)
        self.assertNotIn("#62", err)
        assign.assert_not_called()

    def test_a_ticket_someone_else_holds_is_refused(self):
        code, _, err, assign = preflight(assignees=("someone-else",))
        self.assertEqual(code, 2)
        self.assertIn("someone-else", err)
        assign.assert_not_called()

    def test_a_closed_ticket_is_refused(self):
        code, _, err, _ = preflight(state="CLOSED")
        self.assertEqual(code, 2)
        self.assertIn("CLOSED", err)


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
        self.assertIn("#62", err)
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
        self.assertIn("#62", err)

    def test_a_closed_blocker_whose_events_cannot_be_read_holds(self):
        cases = (("its events cannot be read", ["x\n\n<!-- mmw {not json} -->"]),
                 ("the tracker did not answer for it",
                  subprocess.CalledProcessError(1, ["gh", "issue", "view", "62"])))
        for why, comments in cases:
            with self.subTest(why=why):
                code, _, err, assign = self.blocked("CLOSED", comments)
                self.assertEqual(code, 2)
                self.assertIn("#62", err)
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
        self.assertIn("--closeout", out)

    def test_a_dirty_tree_on_a_ticket_nobody_holds_is_still_refused(self):
        code, posted, err, assign = preflight(dirty=[" M src/app.py"])
        self.assertEqual(code, 2)
        self.assertEqual(event_of(posted[0][1])[1]["reason"], "dirty-tree")
        assign.assert_not_called()


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


class TestClaimRunsNoCriteria(unittest.TestCase):
    BODY = """## Acceptance criteria

- [ ] AC1: a criterion that must not run during claim
  CHECK: touch "$MMW_TEST_CLAIM_MARKER" && echo ran
  EXPECT: ran
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

    def claim(self, root, base):
        from _load import started
        history = [started(ticket=77, base=base, into="spec-337",
                           worktree=str(root), branch="issue-77")]
        posted, commands = [], []
        real_run = subprocess.run

        def fake_gh(cmd, **kwargs):
            commands.append(list(cmd))
            if cmd[0] != "gh":
                return real_run(cmd, **kwargs)
            output = ""
            if cmd[1:3] == ["api", "user"]:
                output = ME
            elif cmd[1:3] == ["issue", "view"]:
                fields = cmd[cmd.index("--json") + 1]
                if fields == "body":
                    output = self.BODY
                elif fields == "comments":
                    output = json.dumps({"comments": [{"body": b} for b in history]})
                else:
                    output = json.dumps(ticket())
            elif cmd[1:3] == ["issue", "comment"]:
                body = Path(cmd[cmd.index("--body-file") + 1]).read_text()
                posted.append((77, body))
                history.append(body)
            elif cmd[1:3] != ["issue", "edit"]:
                raise AssertionError(f"unexpected tracker command: {cmd}")
            return subprocess.CompletedProcess(cmd, 0, output, "")

        with chdir(root), mock.patch.object(vt.subprocess, "run", side_effect=fake_gh), \
                redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = vt.main(["77", "--preflight"])
        return code, posted, err.getvalue(), out.getvalue(), commands

    def test_claim_starts_no_criteria_or_baseline_checkout(self):
        root, base, head = self.repo()
        marker = root / "criterion-ran"
        with mock.patch.dict(os.environ, {"MMW_TEST_CLAIM_MARKER": str(marker)}):
            code, posted, err, out, commands = self.claim(root, base)
        self.assertEqual(code, 0, err)
        self.assertIn(["gh", "issue", "edit", "77", "--add-assignee", "@me"], commands)
        self.assertIn("READY:", out)
        self.assertFalse(marker.exists(), "claim executed a criterion")
        self.assertFalse((root / ".worktrees" / "baseline-77").exists())
        self.assertFalse(any(cmd[:3] == ["git", "worktree", "add"] for cmd in commands))
        self.assertEqual([event_of(body)[0] for _, body in posted], ["ticket.claimed"])
        self.assertEqual(head, subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip())



SELF_LEDGER = "- [x] AC1: it works\n  CHECK: true\n  EXPECT: ok\n  EVIDENCE: exit=0"
HEAD = "a" * 40


class TestResume(unittest.TestCase):
    """`--preflight` prints `RESUME:` after `READY:` for a ticket that already carries a
    run of the worker's own, a `reviewer.reported`, a `worker.decided`, or a worker
    reverify — the resume table in the `implement` skill's `## Closing steps`."""

    def resume(self, comments, body="## Acceptance criteria\n\n" + SELF_LEDGER):
        with mock.patch.object(vt, "git", return_value=HEAD):
            code, posted, err, _, out = run(number=77, history={77: comments}, body=body)
        self.assertEqual(code, 0, err)
        return out

    def assertResumes(self, out, step, *events):
        """The `RESUME:` line opens with the step's title and names the events it read."""
        line = next(row for row in out.splitlines() if row.startswith("RESUME:"))
        self.assertTrue(line.startswith(f"RESUME: {step}"), line)
        for name in events:
            self.assertIn(name, line)

    def test_a_fresh_ticket_prints_no_resume_line(self):
        self.assertNotIn("RESUME", self.resume([]))

    def test_a_recut_ticket_prints_no_resume_line(self):
        current = SELF_LEDGER.replace("it works", "the recut contract")
        for later in ([],
                      [event("ticket.returned", "HANDOFF REQUIRED", ticket=77)],
                      [checked("baseline", current, ticket=77),
                       checked("reverify", current, ticket=77, commit=HEAD)]):
            with self.subTest(later=later):
                comments = [checked("self", current, ticket=77),
                            checked("self", SELF_LEDGER, ticket=77),
                            event("worker.decided", "DECISIONS", ticket=77), *later]
                with mock.patch.object(vt, "git", return_value=HEAD):
                    code, _, err, _, out = run(
                        history={77: comments}, body="## Acceptance criteria\n\n" + current)
                self.assertEqual(code, 0, err)
                self.assertIn("READY:", out)
                self.assertFalse(any(row.startswith("RESUME:") for row in out.splitlines()), out)
                self.assertTrue(err.strip())
                self.assertIn("#77", err)

    def test_an_unchanged_shape_still_resumes(self):
        current = SELF_LEDGER.replace("[x]", "[ ]").replace("exit=0", "pending")
        for expected, comments in (
            ("Start the reviewer",
             [checked("self", SELF_LEDGER, ticket=77),
              event("worker.decided", "DECISIONS", ticket=77)]),
            ("Start the reviewer",
             [checked("self", SELF_LEDGER.replace("it works", "old contract"), ticket=77),
              checked("self", SELF_LEDGER, ticket=77),
              event("worker.decided", "DECISIONS", ticket=77),
              checked("baseline", SELF_LEDGER.replace("it works", "other contract"), ticket=77)]),
            ("Integrate and run every criterion",
             [event("worker.decided", "DECISIONS", ticket=77)]),
        ):
            with self.subTest(comments=comments):
                out = self.resume(comments, body="## Acceptance criteria\n\n" + current)
                self.assertResumes(out, expected)

    def test_a_run_of_your_own_with_no_decision_resumes_at_step_2(self):
        out = self.resume([checked("self", SELF_LEDGER, ticket=77)])
        self.assertResumes(out, "Post the decisions comment", "worker.decided")

    def test_a_decision_with_no_reviewer_resumes_at_step_3(self):
        out = self.resume([checked("self", SELF_LEDGER, ticket=77),
                           event("worker.decided", "DECISIONS", ticket=77)])
        self.assertResumes(out, "Start the reviewer", "worker.decided", "reviewer.reported")

    def test_a_live_reviewer_resumes_asleep_at_step_3(self):
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("reviewer.started", "Reviewer started", ticket=77,
                  session="rv-1", runner="paseo", machine="mac-1"),
        ])
        self.assertResumes(out, "Read the review", "reviewer.started", "reviewer.reported")

    def test_commits_after_your_run_since_the_report_resume_at_the_audit(self):
        out = self.resume([
            event("reviewer.reported", "REVIEW aaa..bbb\n\n## In-ticket\n\nNone\n",
                  ticket=77, base="a" * 7, head="b" * 7),
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
        ])
        self.assertIn("RESUME: Audit (", out)

    def test_a_report_newer_than_your_own_run_resumes_at_its_fix_round(self):
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("reviewer.reported", "REVIEW aaa..bbb\n\n## In-ticket\n\nNone\n",
                  ticket=77, base="a" * 7, head="b" * 7),
        ])
        self.assertResumes(out, "Read the review", "reviewer.reported")

    def test_a_worker_reverify_on_head_with_nothing_newer_resumes_at_step_5(self):
        out = self.resume([
            event("worker.decided", "DECISIONS", ticket=77),
            event("reviewer.reported", "REVIEW aaa..bbb\n\n## In-ticket\n\nNone\n",
                  ticket=77, base="a" * 7, head="b" * 7),
            checked("self", SELF_LEDGER, ticket=77),
            checked("reverify", SELF_LEDGER, ticket=77, actor="worker", commit=HEAD),
        ])
        self.assertIn("RESUME: Run every criterion one final time (", out)

    def test_a_returned_ticket_resumes_at_step_1_then_4(self):
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("reviewer.reported", "REVIEW aaa..bbb\n\n## In-ticket\n\nNone\n",
                  ticket=77, base="a" * 7, head="b" * 7),
            checked("reverify", SELF_LEDGER, ticket=77, actor="worker", commit=HEAD),
            event("ticket.returned", "HANDOFF REQUIRED", ticket=77),
        ])
        self.assertResumes(out, "Integrate and run every criterion", "ticket.returned")

    def test_resume_quotes_failed_checks(self):
        failed = "Failed checks: python3 -c 'import sys; sys.exit(1)' exit 1."
        line = ("Tried to merge issue-77 into origin/main at " + "a" * 40
                + " and handed it to triage. No sibling landing after this ticket "
                + "started was found. " + failed)
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("ticket.bounced", line, ticket=77, reason="checks", commit="b" * 40),
        ])
        lines = out.splitlines()
        resume = next(i for i, row in enumerate(lines) if row.startswith("RESUME:"))
        self.assertResumes(out, "Integrate and run every criterion", "ticket.bounced")
        following = lines[resume + 1] if resume + 1 < len(lines) else ""
        self.assertEqual(following, failed)

    def test_a_conflict_bounce_adds_no_failed_checks_line(self):
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("ticket.bounced", "Tried to merge and handed it to triage. Conflicted files: shared.txt.",
                  ticket=77, reason="conflict", commit="b" * 40),
        ])
        lines = out.splitlines()
        resume = next(i for i, row in enumerate(lines) if row.startswith("RESUME:"))
        self.assertTrue(lines[resume].endswith("(ticket.bounced)"))
        self.assertFalse(any(row.startswith("Failed checks:") for row in lines))

    def test_preflight_quotes_broken_landed_criteria(self):
        broken = "Broken landed criteria: #52 AC3, #60 AC1."
        out = self.resume([
            checked("self", SELF_LEDGER, ticket=77),
            event("worker.decided", "DECISIONS", ticket=77),
            event("ticket.bounced", "Tried to merge issue-77. " + broken,
                  ticket=77, reason="breaks-landed-criterion", commit="b" * 40,
                  broken=[{"ticket": 52, "ac": "AC3"}, {"ticket": 60, "ac": "AC1"}]),
        ])
        lines = out.splitlines()
        resume = next(i for i, row in enumerate(lines) if row.startswith("RESUME:"))
        self.assertEqual(lines[resume + 1], broken)


if __name__ == "__main__":
    unittest.main()
