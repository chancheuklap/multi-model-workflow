"""Which worker a ticket gets.

`dispatch.sh` reads the label and nothing else, so the label is the answer, and this is
where a ticket in the agent queue carrying two is an error, and one carrying none a warning:
it starts on the default row.
"""

import unittest

from _load import load

vt = load()

AGENT = ["ready-for-agent"]


class TestLintWorker(unittest.TestCase):
    def clean(self, labels):
        self.assertEqual(vt.lint_worker(labels), ([], []))

    def test_one_worker_label_is_clean(self):
        self.clean(AGENT + ["junior-worker"])

    def test_no_worker_label_is_a_warning_naming_both_choices(self):
        errors, warnings = vt.lint_worker(AGENT)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("junior-worker", warnings[0])
        self.assertIn("senior-worker", warnings[0])

    def test_two_worker_labels_are_an_error_that_counts_them(self):
        errors, _ = vt.lint_worker(AGENT + ["junior-worker", "senior-worker"])
        self.assertEqual(len(errors), 1)
        self.assertIn("2 worker labels", errors[0])

    def test_a_ticket_a_person_works_needs_no_worker(self):
        self.clean(["ready-for-human"])


if __name__ == "__main__":
    unittest.main()
