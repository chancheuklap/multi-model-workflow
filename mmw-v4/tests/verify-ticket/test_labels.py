import unittest
from unittest import mock

from _load import load


class TestLabels(unittest.TestCase):
    def test_the_two_new_kinds_are_class_labels(self):
        vt = load()
        for name in ("mmw:lesson", "mmw:problem"):
            with self.subTest(name=name):
                self.assertIn(name, vt.CLASS_LABELS)
                self.assertEqual(vt.LABELS[name], vt.CLASS_LABELS[name])
                self.assertFalse(vt.reads_as_spec(77, [name]))

    def test_needs_info_is_gone_and_needs_triage_means_awaiting_the_owner(self):
        vt = load()
        self.assertNotIn("needs-info", vt.LABELS)
        self.assertNotIn("needs-info", vt.QUEUE_LABELS)
        with mock.patch.object(vt.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
            self.assertIsNone(vt.ensure_label("needs-triage"))
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--description") + 1],
                         "等你决定：只有主人能让它离开")


if __name__ == "__main__":
    unittest.main()
