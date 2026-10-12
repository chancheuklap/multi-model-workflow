import unittest

from _load import started
from test_closeout import check, draft
from test_draft import MET_RUN, run_draft


class TestWorkerStartedFault(unittest.TestCase):
    def test_worker_started_fault_when_draft_has_no_dispatch_record(self):
        code, err, text, _ = run_draft((MET_RUN,), started_event=())
        self.assertEqual(code, 2)
        self.assertEqual(text, "")
        self.assertIn("#77 carries no readable worker.started", err)
        self.assertIn("--sub-issue fault", err)
        self.assertNotIn("dispatch.sh start", err)

    def test_worker_started_fault_when_draft_has_no_target_branch(self):
        code, err, text, _ = run_draft((MET_RUN,), started_event=started())
        self.assertEqual(code, 2)
        self.assertEqual(text, "")
        self.assertIn("#77's newest worker.started carries no `into`", err)
        self.assertIn("--sub-issue fault", err)
        self.assertNotIn("dispatch.sh start", err)

    def test_worker_started_fault_when_closeout_has_no_target_branch(self):
        code, err, seen = check(draft(), started_event=started(), check_only=False)
        self.assertEqual(code, 1)
        self.assertEqual(seen, {"posted": [], "closed": [], "handed": []})
        self.assertIn("#77's newest worker.started carries no `into`", err)
        self.assertIn("--sub-issue fault", err)
        self.assertNotIn("dispatch.sh start", err)
