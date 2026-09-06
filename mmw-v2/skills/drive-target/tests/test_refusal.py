"""A refusal is a deliverable with a shape, not an error string.

Three parts, in order: what happened with a fact in it, why, and what to do next. The
third is the one that must survive, because a refusal that only diagnoses is where the
improvising starts — on 2026-09-05 three workers met one correct message and answered it
three different wrong ways.
"""

import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"mmw_{name}_under_test",
                                                  SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rf = load("refusal")


class Shape(unittest.TestCase):
    def test_the_three_parts_come_out_in_order(self):
        text = rf.refusal("Port 8794 is held by pid 12.", "It is another run's.",
                          "Report the ticket blocked and stop.")
        self.assertTrue(text.startswith("Port 8794 is held by pid 12."))
        self.assertTrue(text.endswith("Report the ticket blocked and stop."))

    def test_a_refusal_without_a_next_step_is_refused_itself(self):
        with self.assertRaises(ValueError):
            rf.refusal("Something went wrong.", "Because.", "")

    def test_the_fact_is_trimmed_first_and_the_way_out_never(self):
        """The reader can look a fact up. They cannot guess an instruction."""
        text = rf.refusal("x" * 400, "It is another run's.",
                          "Report the ticket blocked and stop.")
        self.assertLessEqual(len(text), rf.REASON_LIMIT)
        self.assertTrue(text.endswith("Report the ticket blocked and stop."))
        self.assertIn("…", text, "the fact was dropped rather than trimmed")

    def test_the_limit_is_the_one_a_host_measured(self):
        self.assertEqual(rf.REASON_LIMIT, 256)


class EveryRefusalInThePipeline(unittest.TestCase):
    """Whatever the wording, each of them has to fit and has to say what to do."""

    def texts(self) -> dict[str, str]:
        hook = load("hook")
        return {
            "closeout": hook.REFUSAL.format(n=999999),
            "question": hook.NO_QUESTION,
            "kill": hook.no_kill("kill 12345"),
            "report_blocked": rf.REPORT_BLOCKED,
        }

    def test_all_of_them_fit_what_a_host_will_show(self):
        for name, text in self.texts().items():
            with self.subTest(refusal=name):
                self.assertLessEqual(len(text), rf.REASON_LIMIT)

    def test_all_of_them_say_what_to_do_next(self):
        ways_out = ("--closeout", "Decisions I made on my own", "stop", "ABANDON")
        for name, text in self.texts().items():
            with self.subTest(refusal=name):
                self.assertTrue(any(w in text for w in ways_out),
                                f"{name} diagnoses without naming a way out")


if __name__ == "__main__":
    unittest.main()
