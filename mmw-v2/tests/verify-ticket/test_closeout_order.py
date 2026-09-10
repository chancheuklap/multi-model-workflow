"""`--closeout` posts its event only after the state change the event announces.

`ticket.passed` is what wakes the main agent and what `advance` merges on, and
`ticket.returned` is what frees the rest of the batch; either one standing on a ticket the
tracker did not close or hand back would be read as true by every program. So the close
or the hand back comes first, and when the tracker refuses it, nothing is posted.
`ticket.returned` also says the ticket's work is over, its product slot free with it — the
relay wakes the workers queued for a slot on it — so on a hand back the slot goes back
before the event too.
"""

import unittest
from unittest import mock

import test_closeout as tc

HANDOFF = dict(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
               criteria=(tc.MET, tc.UNMET),
               abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
               counts=tc.counts_line(met=1, abandoned=1, total=2))


def with_the_slot(text, **kwargs):
    """`tc.check`, with the product slot's release recorded in `tc.CALLS` as "slot"."""
    with mock.patch.object(tc.vt, "give_slot_back",
                           side_effect=lambda root: tc.CALLS.append("slot")):
        return tc.check(text, **kwargs)


class TestTheChangeComesFirst(unittest.TestCase):
    def test_a_pass_closes_the_ticket_then_posts_ticket_passed(self):
        code, err, _ = with_the_slot(tc.draft(counts=tc.counts_line()), check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["closed", "posted"], "a pass leaves the slot to the landing")

    def test_a_hand_back_swaps_the_label_gives_the_slot_back_then_posts_ticket_returned(self):
        code, err, _ = with_the_slot(tc.draft(**HANDOFF), check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["handed", "slot", "posted"])

    def test_a_slot_that_will_not_come_back_still_lets_the_ticket_be_returned(self):
        with mock.patch.object(tc.vt, "give_slot_back", return_value="slot 2 still has a listener"):
            code, err, seen = tc.check(tc.draft(**HANDOFF), check_only=False)
        self.assertEqual(code, 0, err)
        self.assertIn("its product slot was not given back: slot 2 still has a listener", err)
        self.assertEqual(tc.posted_as(seen["posted"][0][1])[1], "ticket.returned")


class TestNoEventWhenTheTrackerRefuses(unittest.TestCase):
    def test_a_close_the_tracker_refused_posts_no_ticket_passed(self):
        code, err, seen = tc.check(tc.draft(counts=tc.counts_line()), check_only=False,
                                   tracker_fails=True)
        self.assertEqual(code, 1)
        self.assertEqual(seen["posted"], [])
        self.assertIn("did not close #77", err)
        self.assertIn("no ticket.passed event was posted", err)

    def test_a_hand_back_the_tracker_refused_posts_no_ticket_returned(self):
        code, err, seen = tc.check(tc.draft(**HANDOFF), check_only=False, tracker_fails=True)
        self.assertEqual(code, 1)
        self.assertEqual(seen["posted"], [])
        self.assertIn("did not hand back to needs-triage #77", err)
        self.assertIn("no ticket.returned event was posted", err)


CLAIMED = tc.event("ticket.claimed", "Claimed #77 on issue-77", login=tc.ME, branch="issue-77")


def after_a_lost_post(text, **kwargs):
    """--closeout on a ticket a previous run already changed, whose event was never posted."""
    return tc.check(text, comments=(tc.VERDICT_COMMENT, CLAIMED), check_only=False, **kwargs)


class TestAnEventThatCouldNotBePostedIsPostedByTheNextRun(unittest.TestCase):
    def test_a_post_that_fails_after_the_close_says_to_run_closeout_again(self):
        code, err, _ = tc.check(tc.draft(counts=tc.counts_line()), check_only=False, post_fails=True)
        self.assertEqual(code, 1)
        self.assertEqual(tc.CALLS, ["closed", "posted"])
        self.assertIn("#77 is closed, and its ticket.passed event could not be posted", err)
        self.assertIn("Run --closeout again with the same draft", err)

    def test_the_rerun_on_the_closed_ticket_posts_the_missing_ticket_passed(self):
        code, err, seen = after_a_lost_post(tc.draft(counts=tc.counts_line()), state="CLOSED",
                                            assignees=(), reason="COMPLETED")
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["posted"], "the close is not made twice")
        self.assertEqual(tc.posted_as(seen["posted"][0][1])[1], "ticket.passed")

    def test_the_rerun_on_the_handed_back_ticket_posts_the_missing_ticket_returned(self):
        with mock.patch.object(tc.vt, "give_slot_back",
                               side_effect=lambda root: tc.CALLS.append("slot")):
            code, err, seen = after_a_lost_post(tc.draft(**HANDOFF), assignees=(),
                                                labels=("needs-triage",))
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["slot", "posted"],
                         "the hand back is not made twice, and a slot still held goes back first")
        self.assertEqual(tc.posted_as(seen["posted"][0][1])[1], "ticket.returned")

    def test_a_closed_ticket_that_already_carries_its_event_is_still_refused(self):
        passed = tc.event("ticket.passed", "ALL MET", commit=tc.HEAD)
        code, err, seen = tc.check(tc.draft(counts=tc.counts_line()), state="CLOSED", assignees=(),
                                   reason="COMPLETED", check_only=False,
                                   comments=(tc.VERDICT_COMMENT, CLAIMED, passed))
        self.assertEqual(code, 1)
        self.assertIn("already CLOSED", err)
        self.assertEqual(seen["posted"], [])

    def test_a_ticket_closed_as_not_planned_is_somebody_elses_decision(self):
        code, err, seen = after_a_lost_post(tc.draft(counts=tc.counts_line()), state="CLOSED",
                                            assignees=(), reason="NOT_PLANNED")
        self.assertEqual(code, 1)
        self.assertIn("already CLOSED", err)
        self.assertEqual(seen["posted"], [])

    def test_a_round_claimed_by_someone_else_is_not_completed(self):
        theirs = tc.event("ticket.claimed", "Claimed #77 on issue-77", login="someone-else",
                          branch="issue-77")
        code, err, seen = tc.check(tc.draft(counts=tc.counts_line()), state="CLOSED", assignees=(),
                                   reason="COMPLETED", check_only=False,
                                   comments=(tc.VERDICT_COMMENT, theirs))
        self.assertEqual(code, 1)
        self.assertEqual(seen["posted"], [])


if __name__ == "__main__":
    unittest.main()
