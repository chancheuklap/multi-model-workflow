"""The opening guard: six conditions, and what the ticket is told when one fails."""

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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


class TestBaselineRun(unittest.TestCase):
    """After a successful claim, `--preflight` runs the criteria at the base commit."""

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
        self.assertNotIn("skipped", payload)
        self.assertEqual(head, subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip())
        self.assertTrue((root / "later.txt").is_file())
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)

    def test_the_baseline_worktree_gets_its_environment(self):
        for failure in ("", "setup", "up", "down"):
            with self.subTest(failure=failure):
                root, _, _ = self.repo()
                script = root / "scripts" / "env"
                script.parent.mkdir()
                script.write_text("""#!/usr/bin/env bash
printf '\\377\\376\\n'
printf '%s %s %s\\n' "$1" "$2" "$PWD" >> "$MMW_TEST_ENV_LOG"
if [ "$1" = "$MMW_TEST_ENV_FAIL" ]; then
  echo "fixture environment failure for $1" >&2
  exit 7
fi
case "$1" in
  setup) touch "$2/.setup-ready" ;;
  up) test -f "$2/.setup-ready" && touch "$2/.env-ready" ;;
esac
""")
                script.chmod(0o755)
                subprocess.run(["git", "add", "scripts/env"], cwd=root, check=True,
                               capture_output=True)
                subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t",
                                "commit", "-m", "environment"], cwd=root, check=True,
                               capture_output=True)
                base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                               text=True).strip()
                log = root / "calls.log"
                body = """## Acceptance criteria

- [ ] AC1: the baseline environment is ready for tests
  CHECK: test -f .env-ready && printf 'check\\n' >> "$MMW_TEST_ENV_LOG" && echo ready
  EXPECT: ready
  EVIDENCE: pending
"""
                with mock.patch.dict(os.environ, {"MMW_TEST_ENV_LOG": str(log),
                                                  "MMW_TEST_ENV_FAIL": failure}):
                    code, posted, err, _, _ = self.claim(root, base, body=body)
                tree = root.resolve() / ".worktrees" / "baseline-77"
                expected = [f"setup {tree} {tree}"]
                if failure != "setup":
                    expected.append(f"up {tree} {tree}")
                if failure not in ("setup", "up"):
                    expected.append("check")
                expected.append(f"down {tree} {tree}")
                self.assertTrue(log.exists(), "the environment script never ran")
                self.assertEqual(log.read_text().splitlines(), expected)
                self.assertFalse(tree.exists())
                if failure in ("setup", "up"):
                    self.assertEqual(code, 2, err)
                    self.assertIn(f"scripts/env {failure}", err)
                    self.assertIn(str(tree), err)
                    self.assertIn(f"fixture environment failure for {failure}", err)
                    self.assertEqual([event_of(b)[0] for _, b in posted], ["ticket.claimed"])
                else:
                    self.assertEqual(code, 0, err)
                    payload = event_of(posted[1][1])[1]
                    self.assertTrue(payload["criteria"][0]["met"], payload)
                    if failure == "down":
                        self.assertIn("fixture environment failure for down", err)

    def test_the_baseline_run_sets_the_base_ref(self):
        root, base, _ = self.repo()
        body = """## Acceptance criteria

- [ ] AC1: the baseline receives the ticket and its base branch
  CHECK: printf '%s %s' "$MMW_TICKET" "$MMW_BASE_REF"
  EXPECT: 77 origin/spec-337
  EVIDENCE: pending
"""
        with mock.patch.dict(os.environ, {"MMW_BASE_REF": "wrong-branch"}):
            code, posted, err, _, _ = self.claim(root, base, body=body)
        self.assertEqual(code, 0, err)
        payload = event_of(posted[1][1])[1]
        self.assertTrue(payload["criteria"][0]["met"], payload)

    def test_the_baseline_checkout_is_baseline_n_under_the_main_checkout(self):
        root, base, _ = self.repo()
        ticket_root = root / ".worktrees" / "issue-77"
        subprocess.run(["git", "worktree", "add", "--detach", str(ticket_root), base],
                       cwd=root, check=True, capture_output=True)
        body = """## Acceptance criteria

- [ ] AC1: the baseline checkout is under the main checkout
  CHECK: pwd
  EXPECT: .worktrees/baseline-77
  EVIDENCE: pending
"""
        code, posted, err, _, _ = self.claim(ticket_root, base, body=body)
        self.assertEqual(code, 0, err)
        name, payload = event_of(posted[1][1])
        self.assertEqual(name, "ticket.checked")
        self.assertEqual(payload["run"], "baseline")
        self.assertEqual(payload["result"], "met")
        self.assertTrue(payload["criteria"][0]["met"], payload)
        self.assertIn(f"cwd={root.resolve()}/.worktrees/baseline-77;",
                      payload["criteria"][0]["evidence"])
        subprocess.run(["git", "worktree", "remove", "--force", str(ticket_root)],
                       cwd=root, check=True, capture_output=True)
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)
        self.assertFalse((root / ".worktrees" / "baseline-77").exists())

    def test_a_baseline_checkout_left_by_a_crash_is_removed_first(self):
        root, base, _ = self.repo()
        worktree = root / ".worktrees" / "baseline-77"
        subprocess.run(["git", "worktree", "add", "--detach", str(worktree), base],
                       cwd=root, check=True, capture_output=True)
        (worktree / "later.txt").write_text("later\n", encoding="utf-8")
        subprocess.run(["git", "worktree", "lock", "--reason", "initializing",
                        str(worktree)], cwd=root, check=True, capture_output=True)
        code, posted, err, _, _ = self.claim(root, base)
        self.assertEqual(code, 0, err)
        name, payload = event_of(posted[1][1])
        self.assertEqual(name, "ticket.checked")
        self.assertEqual(payload["run"], "baseline")
        by_id = {c["id"]: c for c in payload["criteria"]}
        self.assertIn("AC1", by_id, payload)
        self.assertTrue(by_id["AC1"]["met"], payload)
        self.assertFalse(by_id["AC2"]["met"], payload)
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)
        self.assertFalse(worktree.exists())

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
        self.assertIn("worker.started.base", err)

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
        self.assertEqual(sorted(payload["skipped"]), ["AC1", "AC2"])
        listed = subprocess.check_output(
            ["git", "worktree", "list", "--porcelain"], cwd=root, text=True)
        self.assertEqual(listed.count("worktree "), 1, listed)

    def test_gate_check_exit_2_is_not_a_criteria_result(self):
        self.assertIsNone(vt.check_run_outcome(2, "ALL MET (1 met)"))
        self.assertEqual(vt.check_run_outcome(0, "ALL MET (1 met)"), "met")
        self.assertEqual(vt.check_run_outcome(1, "UNMET: 1 (met: 0)"), "unmet")


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



if __name__ == "__main__":
    unittest.main()
