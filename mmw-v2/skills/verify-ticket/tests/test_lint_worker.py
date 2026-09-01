"""Which worker a ticket gets, said on the tracker and again in the body.

`dispatch.sh` reads the label, so the label is the answer. The `## Worker` section is
the reader's copy of it, and this is where the two are held against each other.
"""

import unittest

from tests._load import load

vt = load()

AGENT = ["ready-for-agent"]


def body(worker=None, extra=""):
    out = "## Parent\n\n#535\n"
    if worker is not None:
        out += f"\n## Worker\n\n{worker}\n"
    return out + extra


class TestStatedWorker(unittest.TestCase):
    def test_it_reads_the_worker_out_of_a_sentence(self):
        text = body("senior-worker —— 一次生成任务对应一次鸭豆预扣和一次结算，错了几天后才看得见。")
        self.assertEqual(vt.stated_worker(text), "senior-worker")

    def test_a_section_naming_none_reads_as_none(self):
        self.assertEqual(vt.stated_worker(body("whichever is free")), "")

    def test_no_section_reads_as_none(self):
        self.assertEqual(vt.stated_worker(body()), "")


class TestLintWorker(unittest.TestCase):
    def clean(self, labels, text):
        self.assertEqual(vt.lint_worker(labels, text), ([], []))

    def test_a_label_the_section_agrees_with_is_clean(self):
        self.clean(AGENT + ["junior-worker"],
                   body("junior-worker —— Seam 已点先例，照抄即可。"))

    def test_no_worker_label_is_an_error_naming_both_choices(self):
        errors, warnings = vt.lint_worker(AGENT, body())
        self.assertEqual(warnings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("junior-worker", errors[0])
        self.assertIn("senior-worker", errors[0])

    def test_two_worker_labels_are_an_error_that_counts_them(self):
        errors, warnings = vt.lint_worker(
            AGENT + ["junior-worker", "senior-worker"], body("junior-worker"))
        self.assertEqual(warnings, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("2 worker labels", errors[0])

    def test_a_label_with_no_section_is_a_warning(self):
        errors, warnings = vt.lint_worker(AGENT + ["senior-worker"], body())
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("senior-worker", warnings[0])

    def test_a_section_naming_the_other_worker_is_a_warning_naming_both(self):
        errors, warnings = vt.lint_worker(AGENT + ["senior-worker"],
                                          body("junior-worker —— 照抄先例。"))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("senior-worker", warnings[0])
        self.assertIn("junior-worker", warnings[0])

    def test_a_ticket_a_person_works_needs_no_worker(self):
        self.clean(["ready-for-human"], body())


if __name__ == "__main__":
    unittest.main()
