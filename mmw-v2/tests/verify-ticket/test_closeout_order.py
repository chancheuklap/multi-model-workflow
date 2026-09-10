"""`--closeout` posts its event only after the state change the event announces.

`ticket.passed` is what wakes the main agent and what `advance` merges on, and
`ticket.returned` is what frees the rest of the batch; either one standing on a ticket the
tracker did not close or hand back would be read as true by every program. So the close
or the hand back comes first, and when the tracker refuses it, nothing is posted.
"""

import unittest

import test_closeout as tc

HANDOFF = dict(first="HANDOFF REQUIRED: 1 abandoned (stuck), 0 unmet, 1 met of 2",
               criteria=(tc.MET, tc.UNMET),
               abandons=("ABANDON: AC2 stuck chromium will not start here; tried the bundled build too",),
               counts=tc.counts_line(met=1, abandoned=1, total=2))


class TestTheChangeComesFirst(unittest.TestCase):
    def test_a_pass_closes_the_ticket_then_posts_ticket_passed(self):
        code, err, _ = tc.check(tc.draft(counts=tc.counts_line()), check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["closed", "posted"])

    def test_a_hand_back_swaps_the_label_then_posts_ticket_returned(self):
        code, err, _ = tc.check(tc.draft(**HANDOFF), check_only=False)
        self.assertEqual(code, 0, err)
        self.assertEqual(tc.CALLS, ["handed", "posted"])


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


if __name__ == "__main__":
    unittest.main()
