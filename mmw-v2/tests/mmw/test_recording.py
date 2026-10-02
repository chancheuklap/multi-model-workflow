"""Ledger behaviour, run against fixed ticket bodies. Never calls the tracker.

A run of the criteria is one `ticket.checked` event on the ticket: its prose is the
updated ledger for a person, and its payload — run, commit, result, counts, each
criterion's outcome, the files outside `## Owns`, the product slot it held — is what
every later reader decides on.
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _load import SCRIPT, checked, event, load, started, current_evidence, ticket, payload_of, git_repo, lease_in

vt = load()

UI_ACCEPTANCE = SCRIPT.parents[2] / "ui-acceptance" / "scripts"
HEAD_RE = r"^[0-9a-f]{40}$"


STARTED = started(ticket=1, into="spec-337")


class LedgerRun(unittest.TestCase):
    """Runs the real gate-check against a fixed body and captures what it posts."""

    def run_ticket(self, body: str, reverify: bool = False, comments: list[str] | None = None,
                   actor: str | None = None, outside=(), started_event=STARTED):
        posted: list[str] = []
        history = ([] if started_event is None else [started_event]) + (comments or [])
        with mock.patch.object(vt.engine, "fetch_body", return_value=body), \
             mock.patch.object(vt.engine, "fetch_comments", return_value=history), \
             mock.patch.object(vt.engine, "outside_owns", return_value=list(outside)), \
             mock.patch.object(vt.engine, "current_branch", return_value="issue-1"), \
             mock.patch.object(vt.engine, "post_comment", side_effect=lambda n, b: posted.append(b)):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_and_record_criteria(1, reverify, actor)
        self.posted = posted
        return code, (posted[0] if posted else ""), out.getvalue()

    def test_worker_run_without_started_leaves_outside_owns_unchecked(self):
        code, comment, _ = self.run_ticket(PLAIN, started_event=None)
        self.assertEqual(code, 0, comment)
        payload = payload_of(comment)
        self.assertEqual(payload["outside_owns_unchecked"], "issue-1")


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

    def test_run_and_record_posts_one_ticket_checked(self):
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
        self.assertTrue(payload["criteria"][0]["evidence"].startswith("automatic-evidence=v1; "))
        self.assertEqual(payload["failed"], ["AC2"])
        self.assertEqual(payload["outside_owns"], ["docs/stray.md"])
        self.assertEqual(payload["shape"],
                         "c7372b84151d44b1b68e0bb2bbe172efe09476519cf17309166810a28f654dc0")
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

    def test_a_worker_reverify_has_the_verify_stage(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        _, comment, _ = self.run_ticket(body, reverify=True, actor="worker")
        payload = payload_of(comment)
        self.assertEqual((payload["actor"], payload["stage"]), ("worker", "verify"))

    def test_a_head_that_is_not_a_commit_is_refused_before_anything_runs(self):
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        with mock.patch.object(vt.engine, "git", return_value=""), \
             redirect_stderr(io.StringIO()) as err:
            code, comment, printed = self.run_ticket(body)
        self.assertEqual((code, comment), (2, ""))
        self.assertIn("could not read HEAD", err.getvalue())
        self.assertNotIn("ALL MET", printed)


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
            "  EVIDENCE: " + current_evidence("echo 'wrote 6 rows'", "wrote 6 rows"),
        ], ticket=1)
        code, comment, printed = self.run_ticket(body, reverify=True, comments=[previous])
        self.assertEqual(code, 0)
        self.assertEqual(payload_of(comment)["run"], "reverify")
        self.assertIn("previously met reverified: 1", printed)

    def test_evidence_written_before_the_definition_digest_is_rerun_not_trusted(self):
        """A run recorded by the gate-check before evidence named its definition: the
        reverify still re-runs it and it passes, but it does not count as previously met."""
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
        self.assertEqual(payload_of(comment)["result"], "met")
        self.assertIn("reran: 1, previously met reverified: 0", printed)

    def test_a_first_line_saying_self_run_carries_nothing_forward(self):
        """The old ledger comment, typed by hand, is prose: nothing is carried from it."""
        body = ticket("- [ ] AC1: a", "  CHECK: echo ok", "  EXPECT: ok", "  EVIDENCE: pending")
        typed = "self-run\nALL MET (1 met)\n\n- [x] AC1: a\n  CHECK: echo ok\n  EXPECT: ok\n" \
                "  EVIDENCE: exit=0; EXPECT=matched"
        _, _, printed = self.run_ticket(body, reverify=True, comments=[typed])
        self.assertIn("previously met reverified: 0", printed)


PRODUCT = ticket("- [ ] AC1: the journey through the importer runs",
                 "  CHECK: echo journey.py import",
                 "  EXPECT: journey.py import",
                 "  EVIDENCE: pending")


PLAIN = ticket("- [ ] AC1: the importer writes six rows",
               "  CHECK: echo 'wrote 6 rows'",
               "  EXPECT: wrote 6 rows",
               "  EVIDENCE: pending")


TARGET_CHECK = ticket("- [ ] AC1: the target file is complete",
                      "  CHECK: python3 mmw-v2/skills/ui-acceptance/scripts/target_config.py --check",
                      "  EXPECT: complete: the oracles can drive this repository",
                      "  EVIDENCE: pending")


class TestTheProductSlot(unittest.TestCase):
    """Writing code takes no slot. The first run of the criteria that needs the product
    acquires one before anything runs; with none free it waits, visibly, on the ticket."""

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
        """A main worktree, with `.mmw/target.json` declaring `instance.max` when given,
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

    def run_in(self, root: Path, body: str, comments=(), tools=(UI_ACCEPTANCE,), lease="patched",
               reverify=False, actor=None, post=None, wait_s=0):
        posted: list[str] = []
        real_run = vt.subprocess.run

        def spy(cmd, *a, **kw):
            if any(str(x).endswith("gate-check.mjs") for x in cmd):
                self.order.append("gate")
            return real_run(cmd, *a, **kw)

        patches = [mock.patch.object(vt.engine, "repo_root", return_value=root),
                   mock.patch.object(vt.engine, "fetch_body", return_value=body),
                   mock.patch.object(vt.engine, "fetch_comments", return_value=[STARTED, *comments]),
                   mock.patch.object(vt.engine, "outside_owns", return_value=[]),
                   mock.patch.object(vt.engine, "post_comment",
                                     side_effect=post or (lambda n, b: posted.append(b))),
                   mock.patch.object(vt.engine, "TOOLS", [Path(t) for t in tools]),
                   mock.patch.object(vt, "SLOT_WAIT_S", wait_s),
                   mock.patch.object(vt.subprocess, "run", side_effect=spy)]
        if lease == "patched":
            patches.append(mock.patch.object(vt.engine, "load_lease", return_value=self.lease))
        for p in patches:
            p.start()
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = vt.run_and_record_criteria(1, reverify, actor)
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

        # Asked again while the wait is already on the ticket: no second event.
        code, again, _ = self.run_in(root, PRODUCT, comments=posted)
        self.assertEqual((code, again), (3, []))

        # The other ticket lands and gives its slot back: this run claims and runs, and
        # its ticket.checked ends the wait.
        self.lease.slot_file(self.lease.claimed()[0]["slot"]).unlink()
        code, done, err = self.run_in(root, PRODUCT, comments=posted)
        self.assertEqual(code, 0, err)
        self.assertEqual([payload_of(b)["event"] for b in done], ["ticket.checked"])
        state = vt.engine.events.fold(posted + done)
        self.assertIsNone(state["waiting"])
        self.assertIsNotNone(state["slot"])

    def test_the_main_checkout_waits_for_the_limit_like_any_ticket(self):
        """The night's reverify runs the product in the main worktree; the limit counts
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
        self.assertEqual(self.lease.claimed(), [], "the main worktree kept its slot")
        self.assertTrue(stopped.exists(), "the product was not stopped before the release")

    def test_a_workers_reverify_keeps_the_worktrees_slot(self):
        _, root = self.main_repo(instance_max=1)
        code, _, err = self.run_in(root, PRODUCT, reverify=True, actor="worker")
        self.assertEqual(code, 0, err)
        self.assertEqual([r["worktree"] for r in self.lease.claimed()], [str(root)])

    def test_run_and_record_exits_4_when_the_event_cannot_be_written(self):
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
                self.assertEqual(code, 4, err)
                self.assertNotIn(code, (0, 1))

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

    def test_a_product_criterion_with_no_lease_py_reachable_is_refused(self):
        _, root = self.main_repo()
        judges = self.tmp / "judges"
        judges.mkdir()
        (judges / "journey.py").write_text("")
        code, posted, err = self.run_in(root, PRODUCT, tools=(judges,), lease="real")
        self.assertEqual((code, posted), (2, []))
        self.assertNotIn("gate", self.order)
        self.assertIn("lease.py", err)


class TestReverifyActorIsExplicit(unittest.TestCase):
    def test_reverify_without_actor_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as caught:
            vt.main(["1", "--run-and-record-criteria", "--reverify"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--reverify requires --actor worker|main", err.getvalue())

    def test_actor_without_reverify_is_a_usage_error(self):
        with redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit) as caught:
            vt.main(["1", "--run-and-record-criteria", "--actor", "worker"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--actor belongs to --reverify", err.getvalue())


class TestExitCodesHelp(unittest.TestCase):
    """The exit codes of `--claim`, `--open-child` and `--review` are printed by
    `ticket_state.py --help` together with the rest of `EXIT_CODES`. No reference
    file keeps a second copy."""

    def test_claim_open_child_and_review_are_documented(self):
        for flag in ("--claim", "--open-child", "--review"):
            with self.subTest(flag=flag):
                self.assertIn(flag, vt.EXIT_CODES)

    def test_help_prints_the_exit_codes(self):
        with redirect_stdout(io.StringIO()) as out, self.assertRaises(SystemExit) as caught:
            vt.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn(vt.EXIT_CODES.strip(), out.getvalue())
