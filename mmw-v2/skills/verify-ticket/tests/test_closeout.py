"""The closing gate: what a closing comment must say before the ticket may close."""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from tests._load import load

vt = load()

ME = "chancheuklap"
VERIFIED = "3f9c2e1adeadbeefcafe0123456789abcdef0123"
HEAD = "9b1d40c7feedface0011223344556677889900aa"

MET = """- [x] AC1: the importer writes six rows
  CHECK: pytest -q tests/test_import.py
  EXPECT: /\\d+ passed/
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=9"""

UNMET = """- [ ] AC2: the expiry page says the link is stale
  CHECK: pytest -q tests/test_expiry.py
  EXPECT: 2 passed
  EVIDENCE: pending"""

VERDICT_COMMENT = f"VERDICT {VERIFIED} by opus — the importer writes six rows"


def self_runs(block, rounds):
    """`rounds` self-run comments, each leaving that criterion unmet."""
    ledger = block if block.startswith("- [ ]") else block.replace("- [x]", "- [ ]")
    return ["\n".join(["self-run", "UNMET: 1", "", ledger])] * rounds


def draft(first="ALL MET", criteria=(MET,), abandons=(), counts=None,
          post_verdict="Post-verdict: None"):
    """Assemble a closing comment in the shape #60 section 9 step 5 fixes."""
    body = [first, "", "Branch: issue-77  Commit: 9b1d40c7  PR: none", ""]
    if post_verdict is not None:
        body += [post_verdict, ""]
    for i, block in enumerate(criteria):
        body.append(block)
        for line in abandons:
            if line.split()[1] == vt.parse_criteria(block)[0]["id"]:
                body.append(line)
    body += ["", "Outside Owns: None"]
    if counts is not None:
        body += ["", counts]
    return "\n".join(body) + "\n"


def counts_line(met=1, unmet=0, abandoned=0, total=1):
    return f"Counts: {met} met, {unmet} unmet, {abandoned} abandoned of {total}"


def check(text, comments=(VERDICT_COMMENT,),
          verdict_reachable=True, head=HEAD, dirty=(), main_merged=True, diff="src/app.py",
          state="OPEN", assignees=(ME,), check_only=True, repo=None):
    """Run --closeout against a made-up ticket; return (exit code, stderr, side effects)."""
    seen = {"posted": [], "closed": [], "handed": [], "told": []}

    def fake_git(*args, cwd=None):
        if args[:2] == ("rev-parse", "HEAD"):
            return head
        if args[0] == "merge-base" and "--is-ancestor" not in args:
            return "0d19a4f3"
        if args[0] == "status":
            return "\n".join(dirty)
        if args[0] == "diff":
            return diff
        return ""

    def fake_is_ancestor(commit, descendant, root=None):
        return main_merged if commit == "main" else verdict_reachable

    ticket = {"state": state, "labels": [], "assignees": [{"login": a} for a in assignees],
              "blockedBy": {"nodes": []}}
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "closeout.md"
        path.write_text(text, encoding="utf-8")
        with mock.patch.object(vt, "fetch_comments", return_value=list(comments)), \
             mock.patch.object(vt, "fetch_ticket", return_value=ticket), \
             mock.patch.object(vt, "gh_login", return_value=ME), \
             mock.patch.object(vt, "repo_root", return_value=repo), \
             mock.patch.object(vt, "git", side_effect=fake_git), \
             mock.patch.object(vt, "is_ancestor", side_effect=fake_is_ancestor), \
             mock.patch.object(vt, "dirty_tracked", side_effect=lambda root=None: list(dirty)), \
             mock.patch.object(vt, "post_comment",
                               side_effect=lambda n, b: seen["posted"].append((n, b))), \
             mock.patch.object(vt, "close_ticket",
                               side_effect=lambda n: seen["closed"].append(n)), \
             mock.patch.object(vt, "hand_back_for_triage",
                               side_effect=lambda n: seen["handed"].append(n)), \
             mock.patch.object(vt, "notify_parent",
                               side_effect=lambda t: seen["told"].append(t)):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_closeout(77, path, check_only)
    return code, err.getvalue(), seen


class TestFirstLine(unittest.TestCase):
    def test_a_first_line_in_neither_shape_is_refused(self):
        code, err, _ = check(draft(first="done!", counts=counts_line()))
        self.assertEqual(code, 1)
        self.assertIn("first line is neither", err)

    def test_all_met_over_a_failed_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck the endpoint it checks does not exist yet",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("only `decision` may be abandoned", err)

    def test_all_met_over_a_stuck_abandon_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium is not installed; tried …",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        self.assertEqual(check(text)[0], 1)

    def test_all_met_over_a_decision_abandon_passes(self):
        """The self-run is generated from the ticket body, which carries no `ABANDON:`
        line, so the run still reports the decision criterion as unmet."""
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 decision both wordings are legal; opened #58",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        newest_run = "\n".join(["self-run", "UNMET: 1 (met: 1)", "", MET, UNMET])
        code, err, _ = check(text, comments=(VERDICT_COMMENT, newest_run))
        self.assertEqual(code, 0, err)

    def test_all_met_with_a_real_unmet_beside_the_decision_is_refused(self):
        """The draft ticks AC3 as met; the newest run says it is not. Only the run's
        own summary refuses this — the draft is well formed on its face."""
        unmet3 = UNMET.replace("AC2: the expiry page says the link is stale",
                               "AC3: the expiry page links back home")
        met3 = MET.replace("AC1: the importer writes six rows",
                           "AC3: the expiry page links back home")
        text = draft(criteria=(MET, UNMET, met3),
                     abandons=("ABANDON: AC2 decision both wordings are legal; opened #58",),
                     counts=counts_line(met=2, abandoned=1, total=3))
        newest_run = "\n".join(["self-run", "UNMET: 2 (met: 1)", "", MET, UNMET, unmet3])
        code, err, _ = check(text, comments=(VERDICT_COMMENT, newest_run))
        self.assertEqual(code, 1)
        self.assertIn("the newest run on the ticket still reports unmet", err)
        self.assertNotIn("first line is `ALL MET` but", err)

    def test_a_well_formed_handoff_first_line_passes(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text, comments=(VERDICT_COMMENT, *self_runs(UNMET, 1)))
        self.assertEqual(code, 0, err)


class TestBody(unittest.TestCase):
    def test_an_unknown_abandon_kind_is_refused(self):
        text = draft(criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 giveup nothing worked",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("must be one of decision, failed, stuck", err)

    def test_an_abandon_pointing_at_no_criterion_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 1",
                     criteria=(MET,), counts=counts_line())
        text += "ABANDON: AC9 stuck there is no AC9 on this ticket\n"
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("points at a criterion the draft does not list", err)

    def test_a_tick_with_pending_evidence_is_refused(self):
        ticked_but_empty = MET.replace(
            "EVIDENCE: exit=0; EXPECT=matched; output-bytes=9", "EVIDENCE: pending")
        code, err, _ = check(draft(criteria=(ticked_but_empty,), counts=counts_line(met=0, unmet=1)))
        self.assertEqual(code, 1)
        self.assertIn("is ticked but its EVIDENCE is pending", err)

    def test_counts_that_disagree_with_the_body_are_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=counts_line(met=4, total=4)))
        self.assertEqual(code, 1)
        self.assertIn("the draft reads 1 met", err)

    def test_a_missing_counts_line_is_refused(self):
        code, err, _ = check(draft(criteria=(MET,), counts=None))
        self.assertEqual(code, 1)
        self.assertIn("no `Counts:", err)

    def test_a_first_line_that_disagrees_with_counts_is_refused(self):
        text = draft(first="HANDOFF REQUIRED: 2 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck the device this needs is not on this machine",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, _ = check(text)
        self.assertEqual(code, 1)
        self.assertIn("first line says 2, `Counts:` says 1", err)


HANDOFF = "HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1"
ABANDONED = "ABANDON: AC2 stuck chromium will not start here; tried the bundled build too"
NO_VERDICT = ("self-run\nUNMET: 1 (met: 0)",)


class TestVerdict(unittest.TestCase):
    """A verdict is what a ticket needs to close as done — and only that.

    Handing the ticket to a person is the way out of everything the gate refuses,
    so nothing the worker cannot produce may stand between it and `HANDOFF REQUIRED`.
    The verifier's comment is exactly such a thing: the worker does not write it.
    """

    def handoff(self, post_verdict="Post-verdict: None", **kwargs):
        text = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                     counts=counts_line(met=0, abandoned=1, total=1),
                     post_verdict=post_verdict)
        return check(text, **kwargs)

    def test_all_met_with_no_verdict_is_still_refused(self):
        code, err, _ = check(draft(counts=counts_line()), comments=NO_VERDICT)
        self.assertEqual(code, 1)
        self.assertIn("carries no `VERDICT", err)

    def test_handing_over_needs_no_verdict(self):
        code, err, _ = self.handoff(comments=NO_VERDICT)
        self.assertEqual(code, 0, err)

    def test_the_refusal_points_at_the_way_out(self):
        _, err, _ = check(draft(counts=counts_line()), comments=NO_VERDICT)
        self.assertIn("HANDOFF REQUIRED", err)

    def test_a_verdict_commit_no_longer_in_history_falls_through_to_post_verdict(self):
        """A lost verdict commit is HEAD having moved on, told the same way as any other."""
        code, err, _ = check(draft(counts=counts_line(), post_verdict=None),
                             verdict_reachable=False)
        self.assertEqual(code, 1)
        self.assertIn("add a `Post-verdict:` line", err)
        self.assertNotIn("revert or a rebase", err)

        code, err, _ = check(draft(counts=counts_line(),
                                   post_verdict="Post-verdict: 9b1d40c7 (code-review found AC1)"),
                             verdict_reachable=False)
        self.assertEqual(code, 0, err)

    def test_handing_over_needs_no_post_verdict_line(self):
        code, err, _ = self.handoff(post_verdict=None)
        self.assertEqual(code, 0, err)

    def test_an_ancestor_verdict_passes_when_post_verdict_is_there(self):
        code, err, _ = check(draft(counts=counts_line(),
                                   post_verdict="Post-verdict: 9b1d40c7 (code-review found AC1)"))
        self.assertEqual(code, 0, err)

    def test_an_ancestor_verdict_without_post_verdict_is_refused(self):
        code, err, _ = check(draft(counts=counts_line(), post_verdict=None))
        self.assertEqual(code, 1)
        self.assertIn("add a `Post-verdict:` line", err)

    def test_a_verdict_on_head_needs_no_post_verdict(self):
        code, err, _ = check(draft(counts=counts_line(), post_verdict=None), head=VERIFIED)
        self.assertEqual(code, 0, err)

    def test_the_newest_verdict_is_the_one_checked(self):
        comments = (f"VERDICT {'0' * 40} by opus — the importer writes six rows",
                    f"VERDICT {VERIFIED} by opus — the expiry page reads right too")
        code, err, _ = check(draft(counts=counts_line()), comments=comments, head=VERIFIED)
        self.assertEqual(code, 0, err)


class TestTheNewestRunAgreesWithTheDraft(unittest.TestCase):
    """`ALL MET` is written by hand; the summary of a run is not.

    The newest `self-run` or `reverify` comment is the ticket's own last measurement of
    its criteria, so a draft claiming everything passed while that summary still says
    `UNMET:` is refused. Only the newest one is read: the worker fixes what the verifier
    found, runs again, and the run after the fix is what the gate sees.
    """

    UNMET_RUN = "reverify\nUNMET: 1 (met: 0)\n\n" + UNMET
    HANDOFF_RUN = ("self-run\nHANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 0 met of 1"
                   "\n\n" + UNMET)
    MET_RUN = "self-run\nALL MET (1)\n\n" + MET

    def test_a_newest_reverify_reporting_unmet_refuses_all_met(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(VERDICT_COMMENT, self.UNMET_RUN))
        self.assertEqual(code, 1)
        self.assertIn("the newest run on the ticket still reports unmet", err)

    def test_a_newest_run_summarising_as_handoff_refuses_all_met(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(VERDICT_COMMENT, self.HANDOFF_RUN))
        self.assertEqual(code, 1)
        self.assertIn("the newest run on the ticket still reports unmet", err)

    def test_a_later_self_run_reporting_all_met_lets_the_draft_through(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(VERDICT_COMMENT, self.UNMET_RUN, self.MET_RUN))
        self.assertEqual(code, 0, err)

    def test_a_ticket_with_no_run_comment_is_not_held_to_this(self):
        code, err, _ = check(draft(counts=counts_line()), comments=(VERDICT_COMMENT,))
        self.assertEqual(code, 0, err)

    def test_the_refusal_names_both_ways_out(self):
        _, err, _ = check(draft(counts=counts_line()),
                          comments=(VERDICT_COMMENT, self.UNMET_RUN))
        self.assertIn("`ALL MET (...)`", err)
        self.assertIn("HANDOFF REQUIRED", err)

    def test_handing_over_is_not_held_to_the_newest_run(self):
        text = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                     counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(text, comments=(VERDICT_COMMENT, self.UNMET_RUN))
        self.assertEqual(code, 0, err)


FENCED = """- [x] AC4: install.sh 装完五处配置
  CHECK:
  ```sh
  T=$(mktemp -d) && MMW_V2_HOME="$T" bash mmw-v2/install.sh >/dev/null
  python3 - <<'EOF'
  print("HOOKS-INSTALLED")
  EOF
  ```
  EXPECT: HOOKS-INSTALLED
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=16"""

UNFENCED = """- [x] AC4: install.sh 装完五处配置
  CHECK: python3 - <<'EOF'
print("HOOKS-INSTALLED")
EOF
  EXPECT: HOOKS-INSTALLED
  EVIDENCE: exit=0; EXPECT=matched; output-bytes=16"""


class TestACheckThatNeededAFence(unittest.TestCase):
    """A draft carries its criteria verbatim, so it carries their fences too.

    Both readers of a ledger have to agree on where a command ends. `gates.mjs`
    refuses a bare line under a `CHECK:`; if the closing gate read the same ledger as
    fine, a ticket could close on criteria the engine would not even parse.
    """

    def test_a_fenced_command_does_not_hide_its_evidence(self):
        criteria = vt.parse_criteria(FENCED)
        self.assertEqual(len(criteria), 1)
        self.assertIn("EXPECT=matched", criteria[0]["evidence"])
        self.assertFalse(criteria[0]["stray"])

    def test_a_draft_whose_criterion_is_fenced_can_close(self):
        code, err, _ = check(draft(criteria=(FENCED,), counts=counts_line()))
        self.assertEqual(code, 0, err)

    def test_a_bare_line_under_a_check_is_refused_here_too(self):
        code, err, _ = check(draft(criteria=(UNFENCED,), counts=counts_line()))
        self.assertEqual(code, 1)
        self.assertIn("fenced block", err)

    def test_one_criterion_does_not_swallow_the_next(self):
        criteria = vt.parse_criteria(FENCED + "\n" + UNMET)
        self.assertEqual([c["id"] for c in criteria], ["AC4", "AC2"])
        self.assertEqual(criteria[1]["evidence"], "pending")


class TestEveryRefusalHasAWayOut(unittest.TestCase):
    """A refusal that names a next step has to accept that step when the worker takes it.

    `--closeout` is the one command a worker must get through to finish a ticket, and
    the loop it sits in has no cap: refused, edit the draft, run it again. A refusal
    whose advice the same gate then refuses is that loop with no exit at all.
    """

    def test_the_advice_in_a_refusal_is_a_draft_the_gate_accepts(self):
        code, err, _ = check(draft(counts=counts_line()), comments=NO_VERDICT)
        self.assertEqual(code, 1)
        self.assertIn("HANDOFF REQUIRED", err)

        # Now do exactly what it said, against the same ticket.
        advised = draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                        counts=counts_line(met=0, abandoned=1, total=1))
        code, err, _ = check(advised, comments=NO_VERDICT)
        self.assertEqual(code, 0, err)

    def test_no_refusal_asks_for_something_only_someone_else_can_write(self):
        """The worker writes the draft and the commits. It does not write the verdict."""
        for label, kwargs in (("no verdict", {"comments": NO_VERDICT}),
                              ("verdict commit lost", {"verdict_reachable": False}),
                              ("head moved on", {})):
            with self.subTest(ticket=label):
                code, err, _ = check(
                    draft(first=HANDOFF, criteria=(UNMET,), abandons=(ABANDONED,),
                          counts=counts_line(met=0, abandoned=1, total=1), post_verdict=None),
                    **kwargs)
                self.assertEqual(code, 0, err)


class TestGit(unittest.TestCase):
    def test_uncommitted_changes_to_tracked_files_are_refused(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[" M src/app.py"])
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes", err)

    def test_a_branch_that_does_not_contain_main_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), main_merged=False)
        self.assertEqual(code, 1)
        self.assertIn("does not contain its base main", err)

    def test_a_branch_that_changed_no_files_only_warns(self):
        code, err, _ = check(draft(counts=counts_line()), diff="")
        self.assertEqual(code, 0)
        self.assertIn("warning: this branch changes no files", err)

    def test_untracked_files_alone_do_not_refuse(self):
        code, err, _ = check(draft(counts=counts_line()), dirty=[])
        self.assertEqual(code, 0, err)


class TestFailedNeedsNoRoundCount(unittest.TestCase):
    """`failed` and `stuck` are told apart for whoever reads the ticket in the morning —
    it ran and did not pass, or it would not run — and the closeout holds neither to a
    number of self-runs: how many rounds a criterion gets is the worker's judgement,
    said on the `ABANDON:` line."""

    HANDOFF = "HANDOFF REQUIRED: 1 abandoned (failed), 0 unmet, 1 met of 2"

    def failed_draft(self, kind="failed"):
        return draft(first=self.HANDOFF.replace("failed", kind),
                     criteria=(MET, UNMET),
                     abandons=(f"ABANDON: AC2 {kind} chromium kept crashing; tried …",),
                     counts=counts_line(met=1, abandoned=1, total=2))

    def test_failed_with_no_self_run_at_all_passes(self):
        code, err, _ = check(self.failed_draft(), comments=(VERDICT_COMMENT,))
        self.assertEqual(code, 0, err)

    def test_failed_after_one_self_run_passes(self):
        code, err, _ = check(self.failed_draft(),
                             comments=(VERDICT_COMMENT, *self_runs(UNMET, 1)))
        self.assertEqual(code, 0, err)

    def test_stuck_passes_the_same_way(self):
        code, err, _ = check(self.failed_draft(kind="stuck"), comments=(VERDICT_COMMENT,))
        self.assertEqual(code, 0, err)


class TestTheFirstLineCarriesTheWholeRefusal(unittest.TestCase):
    """The first line says how many problems there are and how to read the rest, so a
    worker takes in the whole set at once. Naming only the first would have it fix one
    per run, and nothing caps that loop."""

    def three_problems(self):
        return draft(criteria=(MET,), counts=counts_line(met=9, total=9), post_verdict=None)

    def test_the_first_line_counts_the_problems(self):
        code, err, _ = check(self.three_problems())
        first = err.strip().splitlines()[0]
        self.assertTrue(first.startswith("closeout rejected, "), first)
        self.assertRegex(first, r"closeout rejected, \d+ problems?: ")

    def test_the_first_line_says_how_to_read_the_rest(self):
        code, err, _ = check(self.three_problems())
        self.assertIn("--check-only", err.strip().splitlines()[0])

    def test_a_single_problem_does_not_point_at_a_second(self):
        code, err, _ = check(draft(criteria=(MET,), counts=counts_line(met=4, total=4)))
        first = err.strip().splitlines()[0]
        self.assertIn("1 problem:", first)
        self.assertNotIn("--check-only", first)

    def test_the_later_problems_are_still_printed(self):
        code, err, _ = check(self.three_problems())
        lines = err.strip().splitlines()
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(l.startswith("also: ") for l in lines[1:]), lines)


class TestTheVerdictCommitIsWrittenInFull(unittest.TestCase):
    """`VERDICT <full 40-character commit> by <model> — <one line>`.

    A ticket closes on that commit being the commit at HEAD, and an abbreviation cannot
    carry that: two commits share a seven-character prefix often enough that a draft
    could pass against a verdict on neither of them.
    """

    def test_a_shortened_commit_is_not_read_as_a_verdict(self):
        code, err, _ = check(draft(counts=counts_line()),
                             comments=(f"VERDICT {VERIFIED[:8]} by opus — six rows",))
        self.assertEqual(code, 1)
        self.assertIn("carries no `VERDICT", err)

    def test_the_full_forty_characters_is_read_as_a_verdict(self):
        self.assertEqual(vt.last_verdict([VERDICT_COMMENT]), VERIFIED)

    def test_words_between_the_commit_and_by_do_not_hide_the_verdict(self):
        """Only the commit is read off the line, so anything else on it is free text."""
        code, err, _ = check(
            draft(counts=counts_line()),
            comments=(f"VERDICT {VERIFIED} unit-test-verified by opus",))
        self.assertEqual(code, 0, err)
        self.assertEqual(
            vt.last_verdict([f"VERDICT {VERIFIED} unit-test-verified by opus"]), VERIFIED)


class TestHandingBackReleasesTheTicket(unittest.TestCase):
    """`status.py`'s frontier takes only unassigned tickets, so a ticket handed back still held
    by the worker that gave up is one nothing picks up again."""

    def test_the_label_swap_also_drops_the_assignee(self):
        with mock.patch.object(vt.subprocess, "run") as run:
            vt.hand_back_for_triage(77)
        args = run.call_args.args[0]
        self.assertEqual(args[:4], ["gh", "issue", "edit", "77"])
        self.assertEqual(args[args.index("--remove-assignee") + 1], "@me")
        self.assertEqual(args[args.index("--add-label") + 1], "needs-triage")
        self.assertEqual(args[args.index("--remove-label") + 1], "ready-for-agent")


class TestNoSideEffectOnFail(unittest.TestCase):
    """A refused draft leaves the ticket exactly as it was."""

    def test_a_refused_draft_posts_nothing_and_closes_nothing(self):
        text = draft(criteria=(MET,), counts=counts_line(met=9, total=9))
        code, _, seen = check(text, check_only=False)
        self.assertEqual(code, 1)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": [], "told": []})

    def test_check_only_passes_without_touching_the_ticket(self):
        code, err, seen = check(draft(counts=counts_line()), check_only=True)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": [], "told": []})

    def test_all_met_posts_the_draft_and_closes(self):
        text = draft(counts=counts_line())
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["posted"], [(77, text)])
        self.assertEqual(seen["closed"], [77])
        self.assertEqual(seen["handed"], [])
        self.assertEqual(seen["told"], ["#77 ALL MET"])

    def test_handoff_posts_the_draft_and_swaps_the_label(self):
        text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                     criteria=(MET, UNMET),
                     abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                     counts=counts_line(met=1, abandoned=1, total=2))
        code, err, seen = check(text, check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["posted"], [(77, text)])
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [77])
        self.assertEqual(seen["told"], ["#77 HANDOFF REQUIRED"])

    def test_a_ticket_someone_else_holds_is_refused(self):
        code, err, seen = check(draft(counts=counts_line()), assignees=("someone-else",),
                                check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("not assigned to you", err)
        self.assertEqual(seen["posted"], [])

    def test_an_already_closed_ticket_is_refused(self):
        code, err, _ = check(draft(counts=counts_line()), state="CLOSED", check_only=False)
        self.assertEqual(code, 1)
        self.assertIn("already CLOSED", err)


def write_checks(root: Path, commands):
    """A consuming repository's `.mmw/target.json` with only the `checks` key."""
    (root / ".mmw").mkdir(parents=True, exist_ok=True)
    (root / ".mmw" / "target.json").write_text(
        json.dumps({"checks": commands}), encoding="utf-8")


class TestTargetJsonChecks(unittest.TestCase):
    """After the draft is accepted and before the ticket closes, `checks` in
    `.mmw/target.json` run at the repository root. They are the consuming repository's
    own 'run the tests' rule, made a gate; `--reverify` and `--lint` never run them."""

    def test_failing_checks_do_not_close_and_the_comment_starts_checks_failed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [
                "python3 -c \"import sys; [print(i) for i in range(1, 26)]; sys.exit(1)\"",
                "python3 -c \"raise SystemExit(2)\"",
            ])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [])
        self.assertEqual(len(seen["posted"]), 1)
        body = seen["posted"][0][1]
        self.assertEqual(body.splitlines()[0], "CHECKS FAILED")
        self.assertEqual(body.count("python3 -c"), 2)
        self.assertIn("raise SystemExit(2)", body)
        self.assertNotIn("\n1\n", "\n" + body)
        self.assertIn("\n6\n", "\n" + body)
        self.assertIn("\n25\n", "\n" + body)
        self.assertNotIn(text.strip(), body)

    def test_passing_checks_close_with_checks_ok_on_the_closing_comment(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, ["true", "true"])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["closed"], [77])
        posted = seen["posted"][0][1]
        self.assertTrue(posted.startswith(text.rstrip("\n")))
        self.assertIn("CHECKS OK 2/2", posted.splitlines())
        self.assertEqual(posted.splitlines()[0], "ALL MET")

    def test_an_entry_with_its_own_timeout_is_held_to_it(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [
                {"run": "python3 -c \"import time; time.sleep(5)\"", "timeout": 1},
                "true",
            ])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        body = seen["posted"][0][1]
        self.assertEqual(body.splitlines()[0], "CHECKS FAILED")
        self.assertIn("timed out after 1s", body)

    def test_an_entry_that_is_neither_string_nor_run_object_does_not_close(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, [{"cmd": "true"}])
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["posted"][0][1].splitlines()[0], "CHECKS FAILED")

    def test_no_checks_key_leaves_closeout_unchanged(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(
                json.dumps({"reach": "echo"}), encoding="utf-8")
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["posted"], [(77, text)])
        self.assertEqual(seen["closed"], [77])
        self.assertNotIn("CHECKS OK", seen["posted"][0][1])

    def test_reverify_and_lint_do_not_run_the_target_json_checks(self):
        body = ("## Worker\n\njunior-worker\n\n## Acceptance criteria\n\n"
                "- [ ] AC1: something a stranger could judge\n"
                "  CHECK: python3 -c \"print('ok')\"\n"
                "  EXPECT: ok\n  EVIDENCE: pending\n")
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "ran.marker"
            write_checks(root, [f"touch '{marker}'"])
            with mock.patch.object(vt, "repo_root", return_value=root), \
                 mock.patch.object(vt, "fetch_body", return_value=body), \
                 mock.patch.object(vt, "fetch_ticket",
                                   return_value={"labels": [{"name": "ready-for-agent"},
                                                            {"name": "junior-worker"}],
                                                 "state": "OPEN"}), \
                 mock.patch.object(vt, "fetch_comments", return_value=[]), \
                 mock.patch.object(vt, "fetch_parent", return_value=None), \
                 mock.patch.object(vt, "post_comment"), \
                 mock.patch.object(vt, "outside_owns_line",
                                   return_value="Outside Owns: None"):
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    vt.run_lint(77)
                    vt.run_checks(77, True, None)
            self.assertFalse(marker.exists())

    def test_malformed_checks_do_not_close(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".mmw").mkdir()
            (root / ".mmw" / "target.json").write_text(
                json.dumps({"checks": "pytest -q"}), encoding="utf-8")
            text = draft(counts=counts_line())
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 1, err)
        self.assertEqual(seen["closed"], [])
        body = seen["posted"][0][1]
        self.assertEqual(body.splitlines()[0], "CHECKS FAILED")
        self.assertIn("not a list", body)

    def test_handoff_does_not_run_checks(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_checks(root, ["false"])
            text = draft(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
                         criteria=(MET, UNMET),
                         abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
                         counts=counts_line(met=1, abandoned=1, total=2))
            code, err, seen = check(text, check_only=False, repo=root)
        self.assertEqual(code, 0, err)
        self.assertEqual(seen["closed"], [])
        self.assertEqual(seen["handed"], [77])
        self.assertEqual(seen["posted"][0][1], text)
        self.assertNotIn("CHECKS FAILED", seen["posted"][0][1])


if __name__ == "__main__":
    unittest.main()
