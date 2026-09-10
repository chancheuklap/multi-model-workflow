"""Ledger behaviour, run against fixed ticket bodies. Never calls the tracker.

A run of the criteria is one `ticket.checked` event on the ticket: its prose is the
updated ledger for a person, and its payload — run, commit, result, counts, each
criterion's outcome, the files outside `## Owns`, the product slot it held — is what
every later reader decides on.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import SCRIPT, checked, load

vt = load()

DRIVE = SCRIPT.parents[2] / "drive-target" / "scripts"
HEAD_RE = r"^[0-9a-f]{40}$"


def ticket(*criteria: str, owns: str = "- src/**") -> str:
    return "## Owns\n\n" + owns + "\n\n## Acceptance criteria\n\n" + "\n".join(criteria) + "\n"


def payload_of(comment: str) -> dict:
    what, payload = vt.events.parse(comment)
    assert what == "event", (what, payload, comment)
    return payload


class LedgerRun(unittest.TestCase):
    """Runs the real gate-check against a fixed body and captures what it posts."""

    def run_ticket(self, body: str, reverify: bool = False, comments: list[str] | None = None,
                   actor: str | None = None, outside=()):
        posted: list[str] = []
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_comments", return_value=list(comments or [])), \
             mock.patch.object(vt, "outside_owns", return_value=list(outside)), \
             mock.patch.object(vt, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_checks(1, reverify, None, actor)
        self.posted = posted
        return code, (posted[0] if posted else ""), out.getvalue()


class TestACheckMaySpanLines(LedgerRun):
    """A CHECK is a shell command; a command longer than a line goes in a fenced block."""

    def test_the_lines_inside_the_fence_are_the_command(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"",
            "rows = 6",
            "print('wrote', rows, 'rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)

    def test_the_evidence_lands_after_the_closing_fence(self):
        _, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK:",
            "  ```sh",
            "  python3 -c \"print('wrote 6 rows')\"",
            "  ```",
            "  EXPECT: wrote 6 rows",
        ))
        body = comment.splitlines()
        evidence = next(i for i, l in enumerate(body) if l.strip().startswith("EVIDENCE:"))
        command = next(i for i, l in enumerate(body) if "wrote 6 rows" in l and "print" in l)
        self.assertGreater(evidence, command)

    def test_a_bare_line_under_a_check_says_to_use_a_fence(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: python3 -c \"",
            "print('wrote 6 rows')\"",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 2)
        self.assertEqual(comment, "", "a ledger it could not read is not a result to post")
        self.assertIn("fenced block", printed)


class TestDoubleCondition(LedgerRun):
    def test_expected_text_does_not_pass_a_failed_process(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer reports the row count it wrote",
            "  CHECK: echo ok; exit 3",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)
        # The failure is recorded, not left `pending`, and it says which of the two
        # conditions failed: the output matched, the exit code did not.
        self.assertIn("exit=3", comment)
        self.assertIn("EXPECT=matched", comment)
        self.assertNotIn("EVIDENCE: pending", comment)
        self.assertEqual(payload_of(comment)["criteria"][0]["met"], False)

    def test_exit_zero_with_unmatched_output_does_not_pass(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 5 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("- [ ] AC1:", comment)

    def test_exit_zero_and_matching_output_passes_with_evidence(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("- [x] AC1:", comment)
        self.assertIn("EVIDENCE: exit=0;", comment)

    def test_a_criterion_with_no_check_is_never_run_and_never_ticked(self):
        code, comment, printed = self.run_ticket(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
            "- [ ] AC2: the empty-state copy matches the baseline word for word",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertNotIn("RUN  AC:AC2", printed)
        self.assertIn("- [ ] AC2:", comment)
        self.assertEqual(payload_of(comment)["failed"], ["AC2"])


class TestTheRunIsOneTicketCheckedEvent(LedgerRun):
    """The worker's own run and a reverify each post exactly one `ticket.checked`, and
    everything a later reader decides on is in its payload, never in its first line."""

    BODY = ticket(
        "- [ ] AC1: the importer writes six rows",
        "  CHECK: echo 'wrote 6 rows'",
        "  EXPECT: wrote 6 rows",
        "  EVIDENCE: pending",
        "- [ ] AC2: the importer refuses an empty file",
        "  CHECK: echo 'accepted'",
        "  EXPECT: refused",
        "  EVIDENCE: pending",
    )

    def test_the_workers_own_run_carries_its_result_counts_outcomes_and_outside_owns(self):
        code, comment, _ = self.run_ticket(self.BODY, outside=["docs/stray.md"])
        self.assertEqual(code, 1)
        self.assertEqual(len(self.posted), 1)
        payload = payload_of(comment)
        self.assertEqual((payload["event"], payload["run"], payload["actor"],
                          payload["stage"], payload["result"]),
                         ("ticket.checked", "self", "worker", "work", "unmet"))
        self.assertRegex(payload["commit"], HEAD_RE)
        self.assertEqual(payload["counts"],
                         {"met": 1, "unmet": 1, "abandoned": 0, "total": 2})
        self.assertEqual([(c["id"], c["met"]) for c in payload["criteria"]],
                         [("AC1", True), ("AC2", False)])
        self.assertTrue(payload["criteria"][0]["evidence"].startswith("exit=0"))
        self.assertEqual(payload["failed"], ["AC2"])
        self.assertEqual(payload["outside_owns"], ["docs/stray.md"])
        self.assertEqual(payload["shape"],
                         vt.shape_digest(vt.section(self.BODY, "Acceptance criteria")))
        self.assertNotIn("slot", payload)
        self.assertIn("Outside Owns: docs/stray.md", comment)

    def test_all_met_is_result_met(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        code, comment, _ = self.run_ticket(body)
        self.assertEqual((code, payload_of(comment)["result"], payload_of(comment)["failed"]),
                         (0, "met", []))

    def test_a_reverify_by_the_main_agent_says_so(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        code, comment, _ = self.run_ticket(body, reverify=True, actor="main")
        self.assertEqual(code, 0)
        payload = payload_of(comment)
        self.assertEqual((payload["run"], payload["actor"], payload["stage"]),
                         ("reverify", "main", "regress"))
        self.assertNotIn("outside_owns", payload)
        self.assertNotIn("Outside Owns:", comment)

    def test_a_reverify_left_to_its_default_is_the_verifiers(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        _, comment, _ = self.run_ticket(body, reverify=True)
        payload = payload_of(comment)
        self.assertEqual((payload["actor"], payload["stage"]), ("verifier", "verify"))

    def test_a_head_that_is_not_a_commit_is_refused_before_anything_runs(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        with mock.patch.object(vt, "git", return_value=""), \
             redirect_stderr(io.StringIO()) as err:
            code, comment, printed = self.run_ticket(body)
        self.assertEqual((code, comment), (2, ""))
        self.assertIn("could not read HEAD", err.getvalue())
        self.assertNotIn("ALL MET", printed)


class TestMmwTicketInCheckEnv(LedgerRun):
    """The CHECK shell sees the ticket number, not an empty leftover from the host."""

    def test_mmw_ticket_in_check_env(self):
        code, comment, _ = self.run_ticket(ticket(
            "- [ ] AC1: the check shell sees the ticket number",
            "  CHECK: echo T=$MMW_TICKET",
            "  EXPECT: T=1",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0, comment)
        self.assertIn("- [x] AC1:", comment)


class TestNoRoundCap(LedgerRun):
    """How many rounds a criterion gets is the worker's own judgement: no run names a
    limit, however many runs of its own the ticket already carries."""

    FAILING = ("- [ ] AC1: the importer writes six rows\n"
               "  CHECK: echo 'wrote 4 rows'; exit 1\n"
               "  EXPECT: wrote 6 rows\n"
               "  EVIDENCE: pending")

    def prior_runs(self, rounds: int) -> list[str]:
        return [checked("self", self.FAILING, "UNMET: 1", ticket=1)] * rounds

    def test_no_run_names_a_limit(self):
        for rounds in (0, 2, 5):
            with self.subTest(rounds=rounds):
                _, comment, _ = self.run_ticket(ticket(self.FAILING),
                                                comments=self.prior_runs(rounds))
                self.assertNotIn("ROUND LIMIT", comment)
                self.assertNotIn("ABANDON", comment)


class TestCheckTimeout(LedgerRun):
    """One number per ticket, read off the ticket body, never lowered."""

    def body(self, *timeouts: str) -> str:
        lines = []
        for i, t in enumerate(timeouts, 1):
            lines += [f"- [ ] AC{i}: thing {i}", f"  CHECK: echo ok{i}", f"  EXPECT: ok{i}",
                      "  EVIDENCE: pending"]
            if t:
                lines.append(f"  TIMEOUT: {t}")
        return ticket(*lines)

    def test_the_default_is_ten_minutes(self):
        self.assertEqual(vt.check_timeout(self.body(""), None), 600)

    def test_a_ticket_raises_it_with_the_largest_timeout_line(self):
        self.assertEqual(vt.check_timeout(self.body("900", "", "1500"), None), 1500)

    def test_a_ticket_cannot_lower_it(self):
        self.assertEqual(vt.check_timeout(self.body("30"), None), 600)

    def test_the_command_line_raises_it_too(self):
        self.assertEqual(vt.check_timeout(self.body("900"), 2000), 2000)
        self.assertEqual(vt.check_timeout(self.body("900"), 100), 900)

    def test_the_ledger_handed_to_gate_check_carries_no_timeout_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = vt.write_ledger(self.body("900"), Path(tmp))
            text = ledger.read_text(encoding="utf-8")
        self.assertNotIn("TIMEOUT", text)
        self.assertIn("CHECK: echo ok1", text)

    def test_gate_check_is_always_given_the_number(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            code, comment, _ = self.run_ticket(self.body("1200"))
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertIn("--timeout", gate)
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")
        self.assertEqual(code, 0)
        self.assertIn("[x] AC1", comment)

    def test_a_reverify_reads_the_same_number_off_the_body(self):
        seen: list[list[str]] = []
        real = vt.subprocess.run

        def spy(cmd, *a, **kw):
            seen.append(list(cmd))
            return real(cmd, *a, **kw)

        body = self.body("1200")
        previous = checked("self", ["- [x] AC1: thing 1", "  CHECK: echo ok1", "  EXPECT: ok1",
                                    "  TIMEOUT: 1200",
                                    "  EVIDENCE: exit=0; EXPECT=matched"], ticket=1)
        with mock.patch.object(vt.subprocess, "run", side_effect=spy):
            self.run_ticket(body, reverify=True, comments=[previous])
        gate = next(c for c in seen if any(str(x).endswith("gate-check.mjs") for x in c))
        self.assertEqual(gate[gate.index("--timeout") + 1], "1200")

    def test_lint_refuses_a_timeout_that_is_not_seconds(self):
        for bad in ("0", "-5", "ten", "1.5"):
            with self.subTest(value=bad):
                findings = vt.lint_timeouts(self.body(bad))
                self.assertEqual(len(findings), 1)
                self.assertIn("AC1", findings[0])
        self.assertEqual(vt.lint_timeouts(self.body("120")), [])


class TestReverify(LedgerRun):
    def test_reverify_reruns_what_the_last_run_ticked(self):
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: pending",
        )
        previous = checked("self", [
            "- [x] AC1: the importer writes six rows",
            "  CHECK: echo 'wrote 6 rows'",
            "  EXPECT: wrote 6 rows",
            "  EVIDENCE: exit=0; shell=/bin/sh; cwd=.; EXPECT=matched",
        ], ticket=1)
        code, comment, printed = self.run_ticket(body, reverify=True, comments=[previous])
        self.assertEqual(code, 0)
        self.assertEqual(payload_of(comment)["run"], "reverify")
        self.assertIn("previously met reverified: 1", printed)

    def test_a_first_line_saying_self_run_carries_nothing_forward(self):
        """The old ledger comment, typed by hand, is prose: nothing is carried from it."""
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        typed = "self-run\nALL MET (1 met)\n\n- [x] AC1: a\n  CHECK: echo ok\n  EXPECT: ok\n" \
                "  EVIDENCE: exit=0; EXPECT=matched"
        _, _, printed = self.run_ticket(body, reverify=True, comments=[typed])
        self.assertIn("previously met reverified: 0", printed)


class TestLedgerWithResults(unittest.TestCase):
    """A run's ticks and evidence written back onto the criteria the body states."""

    LINES = ["- [ ] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: pending",
             "- [ ] AC2: b", "  CHECK: false", "  EXPECT: b", "  EVIDENCE: pending"]

    def test_ticks_and_evidence_come_from_the_run(self):
        out = vt.ledger_with_results(self.LINES, [
            {"id": "AC1", "met": True, "evidence": "exit=0; EXPECT=matched"},
            {"id": "AC2", "met": False, "evidence": "exit=1"}])
        self.assertEqual(out, [
            "- [x] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: exit=0; EXPECT=matched",
            "- [ ] AC2: b", "  CHECK: false", "  EXPECT: b", "  EVIDENCE: exit=1"])

    def test_a_criterion_the_run_does_not_name_is_left_as_the_body_has_it(self):
        out = vt.ledger_with_results(self.LINES, [{"id": "AC2", "met": True, "evidence": "e"}])
        self.assertEqual(out[:4], self.LINES[:4])
        self.assertEqual(out[4], "- [x] AC2: b")

    def test_evidence_is_written_after_the_last_attribute_when_the_body_has_none(self):
        out = vt.ledger_with_results(
            ["- [ ] AC1: a", "  CHECK: true", "  EXPECT: a", "", "- [ ] AC2: b",
             "  CHECK: true", "  EXPECT: b"],
            [{"id": "AC1", "met": True, "evidence": "e1"},
             {"id": "AC2", "met": True, "evidence": "e2"}])
        self.assertEqual(out, ["- [x] AC1: a", "  CHECK: true", "  EXPECT: a", "  EVIDENCE: e1",
                               "", "- [x] AC2: b", "  CHECK: true", "  EXPECT: b",
                               "  EVIDENCE: e2"])

    def test_a_criterion_shaped_line_inside_a_fenced_check_is_the_command(self):
        lines = ["- [ ] AC1: a", "  CHECK:", "  ```sh", "  cat <<'EOF'",
                 "- [ ] AC9: printed, not a criterion", "  EOF", "  ```", "  EXPECT: AC9"]
        out = vt.ledger_with_results(lines, [{"id": "AC1", "met": True, "evidence": "e"},
                                             {"id": "AC9", "met": True, "evidence": "x"}])
        self.assertEqual(out[0], "- [x] AC1: a")
        self.assertIn("- [ ] AC9: printed, not a criterion", out)
        self.assertEqual(out[-1], "  EVIDENCE: e")
        self.assertEqual([c["id"] for c in vt.parse_criteria("\n".join(out))], ["AC1"])


class TestCarriedLedger(unittest.TestCase):
    """`--reverify` carries the newest run's ticks and evidence, unless the ticket has
    rewritten its criteria since."""

    BODY = ("## Acceptance criteria\n\n"
            "- [ ] AC1: the importer writes six rows\n"
            "  CHECK: pytest test_importer_v5.py\n"
            "  EXPECT: /^\\d+ passed/m\n"
            "  EVIDENCE: pending\n\n"
            "## Blocked by\n")
    SAME = ["- [x] AC1: the importer writes six rows",
            "  CHECK: pytest test_importer_v5.py",
            "  EXPECT: /^\\d+ passed/m",
            "  EVIDENCE: exit=0; EXPECT=matched"]

    def test_a_run_of_the_same_criteria_is_carried(self):
        self.assertEqual(vt.carried_ledger(self.BODY, [checked("self", self.SAME)]), self.SAME)

    def test_a_run_whose_command_the_ticket_has_rewritten_is_dropped(self):
        """The old command names a file a later decision renamed: the body wins."""
        stale = [line.replace("v5", "v4") for line in self.SAME]
        self.assertEqual(vt.carried_ledger(self.BODY, [checked("self", stale)]), [])

    def test_the_newest_of_the_workers_run_and_a_reverify_is_carried(self):
        unmet = [self.SAME[0].replace("[x]", "[ ]")] + self.SAME[1:3] + ["  EVIDENCE: exit=1"]
        comments = [checked("self", unmet), checked("reverify", self.SAME)]
        self.assertEqual(vt.carried_ledger(self.BODY, comments), self.SAME)
        comments = [checked("reverify", self.SAME), checked("self", unmet)]
        self.assertEqual(vt.carried_ledger(self.BODY, comments)[0], unmet[0])

    def test_no_run_and_the_repository_checks_carry_nothing(self):
        self.assertEqual(vt.carried_ledger(self.BODY, []), [])
        repo = vt.events.build("ticket.checked", ticket=77, line="checks", run="repo-checks",
                               commit="0" * 40, result="met")
        self.assertEqual(vt.carried_ledger(self.BODY, [repo]), [])


class TestOwns(unittest.TestCase):
    def test_globs_drop_the_new_marker_and_the_none_line(self):
        body = "## Owns\n\n- src/import/**\n- src/import/ui/** (new)\n\n## Acceptance criteria\n"
        self.assertEqual(vt.owns_globs(body), ["src/import/**", "src/import/ui/**"])
        self.assertEqual(vt.owns_globs("## Owns\n\n- None\n\n## Blocked by\n"), [])

    def test_globs_drop_wrapping_backticks(self):
        body = ("## Owns\n\n- `src/import/**`\n- `src/import/ui/**` (new)\n\n"
                "## Acceptance criteria\n")
        self.assertEqual(vt.owns_globs(body), ["src/import/**", "src/import/ui/**"])


class TestLint(unittest.TestCase):
    def lint(self, body: str, labels=()):
        """`--lint` on a ticket whose text is `body` and whose labels are `labels`.

        The tracker is reached for three things and all three are answered here: the
        body, the parent link, and the labels the worker rule reads. Left unpatched,
        `fetch_ticket` runs `gh issue view` against the real repository, which makes
        a unit test wait on the network and fail when it is not there."""
        ticket_json = {"state": "OPEN", "labels": [{"name": name} for name in labels],
                       "assignees": [], "blockedBy": []}
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             mock.patch.object(vt, "fetch_ticket", return_value=ticket_json):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(1)
        return code, out.getvalue()

    def test_the_worker_label_the_tracker_carries_is_what_the_rule_reads(self):
        """A ticket in the agent queue with no worker label is the one worker ERROR,
        and it is the labels that decide it, not anything in the body."""
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: /wrote 6 rows/",
            "  EVIDENCE: pending",
        )
        code, printed = self.lint(body, labels=["ready-for-agent"])
        self.assertEqual(code, 1)
        self.assertIn("worker-label", printed)
        self.assertEqual(self.lint(body, labels=["needs-triage"])[0], 0)

    def test_a_weak_expectation_is_reported_without_failing_the_run(self):
        """A warning is for a person to weigh, so it must not decide the exit code."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("weak-expect", printed)

    def test_a_ticket_with_no_criteria_section_is_not_a_finding(self):
        """A `ready-for-human` ticket holds one thing to look at, and no criteria."""
        body = "## Parent\n\n#76\n\n## Blocked by\n\n- #96\n"
        with mock.patch.object(vt, "lint_ticket_graph", return_value=0):
            code, printed = self.lint(body)
        self.assertEqual(code, 0)
        self.assertIn("carries no `## Acceptance criteria`", printed)
        self.assertNotIn("zero live gates", printed)

    def test_a_criterion_with_no_command_fails_the_run(self):
        """Nobody but the ticket's own author decides it, which the section forbids."""
        code, printed = self.lint(ticket(
            "- [ ] AC1: the wording reads well",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("ERROR", printed)

    def test_lint_runs_no_check_and_posts_no_comment(self):
        posted: list[str] = []
        body = ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: echo LINT-MUST-NOT-RUN-THIS",
            "  EXPECT: ok",
            "  EVIDENCE: pending",
        )
        with mock.patch.object(vt, "post_comment", side_effect=lambda n, b: posted.append(b)):
            _, printed = self.lint(body)
        self.assertNotIn("LINT-MUST-NOT-RUN-THIS\n", printed.replace("CHECK: echo LINT-MUST-NOT-RUN-THIS", ""))
        self.assertEqual(posted, [])

    def test_a_sound_ledger_is_clean(self):
        code, printed = self.lint(ticket(
            "- [ ] AC1: the importer writes six rows",
            "  CHECK: node scripts/import.mjs fixtures/valid.json",
            "  EXPECT: /wrote 6 rows/",
            "  EVIDENCE: pending",
        ))
        self.assertEqual(code, 0)
        self.assertIn("LINT OK", printed)


def git_repo(root: Path):
    """A repository with one commit at `root`; returns a function running git there."""
    def sh(*args, cwd=root):
        subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

    sh("init", "-q", "-b", "main")
    sh("config", "user.email", "t@t")
    sh("config", "user.name", "t")
    return sh


class TestOutsideOwns(unittest.TestCase):
    """`outside_owns` counts this ticket's own commits, not what a merge rides in."""

    def repo(self, tmp):
        sh = git_repo(tmp)
        (tmp / "base.txt").write_text("base\n")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        return sh

    def test_a_merged_branch_does_not_count_as_this_tickets_work(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            # The earlier ticket's branch commits its own file.
            sh("checkout", "-qb", "issue-2")
            (tmp / "theirs.txt").write_text("theirs\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-2 work")
            # This ticket's branch commits one file inside Owns, one outside...
            sh("checkout", "-q", "main")
            sh("checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            # ...then merges the earlier ticket's branch to build on it.
            sh("merge", "-q", "--no-ff", "-m", "merge issue-2", "issue-2")
            self.assertEqual(vt.outside_owns(["mine.txt"], tmp), ["stray.txt"])

    def test_backticked_owns_that_cover_the_commit_report_none(self):
        """A `## Owns` bullet written `` `path` `` still excludes that path."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "issue-4")
            (tmp / "mine.txt").write_text("mine\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            globs = vt.owns_globs("## Owns\n\n- `mine.txt`\n")
            self.assertEqual(globs, ["mine.txt"])
            fields = vt.outside_owns_fields(4, globs, tmp)
            self.assertEqual(fields, {"outside_owns": []})
            self.assertEqual(vt.outside_owns_text(fields), "Outside Owns: None")

    def test_the_list_is_answered_on_the_tickets_own_branch(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "issue-4")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "issue-4 work")
            fields = vt.outside_owns_fields(4, ["mine.txt"], tmp)
            self.assertEqual(fields, {"outside_owns": ["stray.txt"]})
            self.assertEqual(vt.outside_owns_text(fields), "Outside Owns: stray.txt")

    def test_the_list_is_left_unanswered_on_the_branch_tickets_merge_into(self):
        """A re-run there is walking every ticket's commits, which answers nothing."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            sh = self.repo(tmp)
            sh("checkout", "-qb", "spec-branch")
            (tmp / "stray.txt").write_text("stray\n")
            sh("add", "-A")
            sh("commit", "-qm", "somebody else's work")
            fields = vt.outside_owns_fields(4, ["mine.txt"], tmp)
            self.assertEqual(fields, {"outside_owns_unchecked": "spec-branch"})
            self.assertEqual(
                vt.outside_owns_text(fields),
                "Outside Owns: not checked on spec-branch, which carries more than "
                "this ticket")


def lease_in(home: Path):
    """`lease.py` of the drive-target skill, its registry under `home`, not ~/.mmw."""
    spec = importlib.util.spec_from_file_location(f"lease_for_tests_{id(home)}",
                                                  DRIVE / "lease.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REGISTRY = home / "leases"
    module.INSTANCES = home / "instances"
    return module


PRODUCT = ticket("- [ ] AC1: the journey through the importer runs",
                 "  CHECK: echo journey.py import",
                 "  EXPECT: journey.py import",
                 "  EVIDENCE: pending")
PLAIN = ticket("- [ ] AC1: the importer writes six rows",
               "  CHECK: echo 'wrote 6 rows'",
               "  EXPECT: wrote 6 rows",
               "  EVIDENCE: pending")


class TestTheProductSlot(unittest.TestCase):
    """Writing code takes no slot. The first run of the criteria that needs the product
    claims one before anything runs; with none free it waits, visibly, on the ticket."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.tmp)])
        self.lease = lease_in(self.tmp / "home")
        self.order: list[str] = []
        real_claim = self.lease.try_claim

        def claim(worktree):
            self.order.append("claim")
            return real_claim(worktree)

        self.lease.try_claim = claim

    def main_repo(self, instance_max=None):
        """A main checkout, with `.mmw/target.json` declaring `instance.max` when given,
        and a ticket worktree `.worktrees/issue-1` cut from it."""
        main = self.tmp / "main"
        main.mkdir()
        sh = git_repo(main)
        if instance_max is not None:
            (main / ".mmw").mkdir()
            (main / ".mmw" / "target.json").write_text(
                '{"instance": {"max": %d, "why": "fixed host ports"}}' % instance_max)
        (main / "base.txt").write_text("base\n")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        sh("worktree", "add", "-q", "-b", "issue-1", str(main / ".worktrees" / "issue-1"))
        return main, (main / ".worktrees" / "issue-1").resolve()

    def run_in(self, root: Path, body: str, comments=(), tools=(DRIVE,), lease="patched",
               reverify=False, actor=None, post=None, wait_s=0):
        posted: list[str] = []
        real_run = vt.subprocess.run

        def spy(cmd, *a, **kw):
            if any(str(x).endswith("gate-check.mjs") for x in cmd):
                self.order.append("gate")
            return real_run(cmd, *a, **kw)

        patches = [mock.patch.object(vt, "repo_root", return_value=root),
                   mock.patch.object(vt, "fetch_body", return_value=body),
                   mock.patch.object(vt, "fetch_comments", return_value=list(comments)),
                   mock.patch.object(vt, "outside_owns", return_value=[]),
                   mock.patch.object(vt, "post_comment",
                                     side_effect=post or (lambda n, b: posted.append(b))),
                   mock.patch.object(vt, "TOOLS", [Path(t) for t in tools]),
                   mock.patch.object(vt, "SLOT_WAIT_S", wait_s),
                   mock.patch.object(vt.subprocess, "run", side_effect=spy)]
        if lease == "patched":
            patches.append(mock.patch.object(vt, "load_lease", return_value=self.lease))
        for p in patches:
            p.start()
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_checks(1, reverify, None, actor)
        finally:
            for p in reversed(patches):
                p.stop()
        return code, posted, err.getvalue()

    def test_a_ticket_whose_criteria_never_run_the_product_claims_no_slot(self):
        _, root = self.main_repo()
        code, posted, err = self.run_in(root, PLAIN)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.order, ["gate"])
        self.assertEqual(self.lease.claimed(), [])
        self.assertNotIn("slot", payload_of(posted[0]))

    def test_the_first_run_that_needs_the_product_claims_before_anything_runs(self):
        _, root = self.main_repo()
        code, posted, err = self.run_in(root, PRODUCT)
        self.assertEqual(code, 0, err)
        self.assertEqual(self.order, ["claim", "gate"])
        held = self.lease.claimed()
        self.assertEqual([r["worktree"] for r in held], [str(root)])
        payload = payload_of(posted[-1])
        self.assertEqual((payload["event"], payload["slot"], payload["port_base"]),
                         ("ticket.checked", held[0]["slot"], held[0]["port_base"]))

    def test_a_second_run_finds_the_slot_it_already_holds(self):
        _, root = self.main_repo(instance_max=1)
        self.run_in(root, PRODUCT)
        code, posted, err = self.run_in(root, PRODUCT)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.lease.claimed()), 1)
        self.assertEqual([payload_of(b)["event"] for b in posted], ["ticket.checked"])

    def test_a_full_product_queues_the_run_on_the_ticket_and_runs_nothing(self):
        main, root = self.main_repo(instance_max=1)
        other = main / ".worktrees" / "issue-2"
        other.mkdir()
        self.lease.try_claim(other.resolve())
        self.order.clear()

        code, posted, err = self.run_in(root, PRODUCT)
        self.assertEqual(code, 3, err)
        self.assertNotIn("gate", self.order)
        self.assertEqual(len(posted), 1)
        queued = payload_of(posted[0])
        self.assertEqual((queued["event"], queued["reason"], queued["run"], queued["limit"]),
                         ("worker.queued", "product-full", "self", 1))
        self.assertEqual(queued["holders"], [str(other.resolve())])
        self.assertIn("Run the same command again", err)

        # Asked again while the wait is already on the ticket: no second event.
        code, again, _ = self.run_in(root, PRODUCT, comments=posted)
        self.assertEqual((code, again), (3, []))

        # The other ticket lands and gives its slot back: this run claims and runs, and
        # its ticket.checked ends the wait.
        self.lease.slot_file(self.lease.claimed()[0]["slot"]).unlink()
        code, done, err = self.run_in(root, PRODUCT, comments=posted)
        self.assertEqual(code, 0, err)
        self.assertEqual([payload_of(b)["event"] for b in done], ["ticket.checked"])
        state = vt.events.fold(posted + done)
        self.assertIsNone(state["waiting"])
        self.assertIsNotNone(state["slot"])

    def test_the_main_checkout_waits_for_the_limit_like_any_ticket(self):
        """The night's reverify runs the product in the main checkout; the limit counts
        that run as it counts a ticket's."""
        main, _ = self.main_repo(instance_max=1)
        other = main / ".worktrees" / "issue-2"
        other.mkdir()
        self.lease.try_claim(other.resolve())
        code, posted, err = self.run_in(main.resolve(), PRODUCT, reverify=True, actor="main")
        self.assertEqual(code, 3, err)
        self.assertEqual(payload_of(posted[0])["event"], "worker.queued")
        self.assertNotIn("gate", self.order)

    def test_the_main_agents_reverify_gives_its_slot_back_when_it_ends(self):
        main, _ = self.main_repo(instance_max=1)
        stopped = self.tmp / "stopped"
        (main / ".mmw" / "target.json").write_text(json.dumps(
            {"instance": {"max": 1}, "stop": f"touch '{stopped}'"}))
        code, posted, err = self.run_in(main.resolve(), PRODUCT, reverify=True, actor="main")
        self.assertEqual(code, 0, err)
        self.assertEqual(payload_of(posted[-1])["actor"], "main")
        self.assertIsNotNone(payload_of(posted[-1])["slot"])
        self.assertEqual(self.lease.claimed(), [], "the main checkout kept its slot")
        self.assertTrue(stopped.exists(), "the product was not stopped before the release")

    def test_a_verifiers_reverify_keeps_the_worktrees_slot(self):
        _, root = self.main_repo(instance_max=1)
        code, _, err = self.run_in(root, PRODUCT, reverify=True)
        self.assertEqual(code, 0, err)
        self.assertEqual([r["worktree"] for r in self.lease.claimed()], [str(root)])

    def test_a_run_whose_result_could_not_be_written_is_not_red(self):
        """A red run and an unrecorded one must never share an exit: the night's
        reverify reopens a landed ticket on 1."""
        _, root = self.main_repo()

        def tracker_down(number, body):
            raise vt.subprocess.CalledProcessError(1, ["gh", "issue", "comment"])

        failing = ticket("- [ ] AC1: fails", "  CHECK: false", "  EXPECT: x",
                         "  EVIDENCE: pending")
        for body in (PLAIN, failing):
            with self.subTest(body=body[:40]):
                code, _, err = self.run_in(root, body, post=tracker_down)
                self.assertEqual(code, vt.NOT_RECORDED, err)
                self.assertNotIn(code, (0, 1))
                self.assertIn("could not be written", err)

    def test_a_full_machine_queues_the_run_the_same_way(self):
        _, root = self.main_repo()

        def full(worktree):
            raise self.lease.Full("machine-full", 8, ["/a", "/b"])

        self.lease.try_claim = full
        code, posted, _ = self.run_in(root, PRODUCT)
        self.assertEqual(code, 3)
        self.assertEqual(payload_of(posted[0])["reason"], "machine-full")

    def every_slot_held(self):
        def full(worktree):
            raise self.lease.Full("machine-full", 8, ["/a", "/b"])

        self.lease.try_claim = full

    def test_a_workers_own_run_hands_back_3_at_once_and_is_woken_for_the_slot(self):
        """A wait inside the command would cost the worker a turn every `SLOT_WAIT_S` for
        as long as the slots stay held. It is the relay that wakes it, with
        `#<n> worker.queued`, when a slot is given back."""
        _, root = self.main_repo()
        self.every_slot_held()
        with mock.patch.object(vt.time, "sleep") as sleep:
            code, posted, err = self.run_in(root, PRODUCT, wait_s=90)
            self.assertEqual(code, 3, err)
            sleep.assert_not_called()
            self.assertEqual([payload_of(b)["event"] for b in posted], ["worker.queued"])
            self.assertIn("Nothing was run", err)
            self.assertIn("`#1 worker.queued`", err)

            # Woken, run again, and the slots are still held: the same wait, no second event.
            code, again, err = self.run_in(root, PRODUCT, comments=posted, wait_s=90)
            self.assertEqual((code, again), (3, []), err)
            sleep.assert_not_called()
        self.assertNotIn("gate", self.order)

    def test_a_reverify_with_every_slot_held_still_waits_in_the_command(self):
        _, root = self.main_repo()
        self.every_slot_held()
        with mock.patch.object(vt.time, "sleep") as sleep, \
             mock.patch.object(vt, "SLOT_BEAT_S", 10):
            code, posted, err = self.run_in(root, PRODUCT, reverify=True, wait_s=20)
        self.assertEqual(code, 3, err)
        self.assertEqual([c.args for c in sleep.call_args_list], [(10,), (10,)])
        queued = payload_of(posted[0])
        self.assertEqual((queued["event"], queued["run"]), ("worker.queued", "reverify"))
        self.assertIn("Run the same command again to keep waiting", err)

    def test_a_product_criterion_with_no_lease_py_reachable_is_refused(self):
        _, root = self.main_repo()
        judges = self.tmp / "judges"
        judges.mkdir()
        (judges / "journey.py").write_text("")
        code, posted, err = self.run_in(root, PRODUCT, tools=(judges,), lease="real")
        self.assertEqual((code, posted), (2, []))
        self.assertNotIn("gate", self.order)
        self.assertIn("lease.py", err)


if __name__ == "__main__":
    unittest.main()
