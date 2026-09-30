from __future__ import annotations

import importlib.util
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2] / "board" / "codeversion.py"


class CodeversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "mmw-v2"
        board = self.root / "board"
        board.mkdir(parents=True)
        shutil.copy(SOURCE, board / "codeversion.py")
        picked = self.root / "skills" / "picked"
        (picked / "scripts").mkdir(parents=True)
        self.models = picked / "scripts" / "models.py"
        self.models.write_text("models = 1\n", encoding="utf-8")
        (picked / "events.py").write_text("events = 1\n", encoding="utf-8")
        (picked / "issue_tree.py").write_text("tree = 1\n", encoding="utf-8")
        (picked / "scripts" / "ghlist.py").write_text("gh = 1\n", encoding="utf-8")
        (picked / "scripts" / "statedir.py").write_text("state = 1\n", encoding="utf-8")
        scripts = self.root / "skills" / "dispatch" / "scripts"
        scripts.mkdir(parents=True)
        self.locations = scripts / "locations.py"
        self.locations.write_text(
            'DISPATCH_SCRIPTS = "picked/scripts"\n'
            'EVENTS_PY = "picked/events.py"\n'
            'ISSUE_TREE_PY = "picked/issue_tree.py"\n',
            encoding="utf-8",
        )
        self.module = self.load()

    def load(self):
        path = self.root / "board" / "codeversion.py"
        spec = importlib.util.spec_from_file_location("codeversion_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_fingerprint_changes_when_locations_changes(self):
        before = self.module.fingerprint()
        self.locations.write_text(
            self.locations.read_text(encoding="utf-8") + "\nANCHOR = 'changed'\n",
            encoding="utf-8",
        )
        self.assertNotEqual(self.module.fingerprint(), before)

    def test_fingerprint_changes_when_a_script_locations_names_changes(self):
        before = self.module.fingerprint()
        self.models.write_text("models = 2\n", encoding="utf-8")
        self.assertNotEqual(self.module.fingerprint(), before)

    def test_a_locations_file_that_cannot_be_loaded_settles_instead_of_raising(self):
        watch = self.module.Watch()
        self.locations.write_text("DISPATCH_SCRIPTS = {\n", encoding="utf-8")
        self.assertFalse(watch.changed())
        self.assertTrue(watch.changed())
        broken = self.module.fingerprint()
        self.locations.write_text(self.locations.read_text(encoding="utf-8") + "\n",
                                  encoding="utf-8")
        self.assertNotEqual(self.module.fingerprint(), broken)

    def test_require_scripts_refuses_when_locations_cannot_be_loaded(self):
        self.locations.write_text("import not_a_real_module_615\n", encoding="utf-8")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as caught:
                self.module.require_scripts()
        self.assertEqual(caught.exception.code, 1)
        message = stderr.getvalue()
        self.assertIn(str(self.locations), message)
        self.assertIn("cannot be loaded", message)
        self.assertIn("bash mmw-v2/install.sh --check", message)


if __name__ == "__main__":
    unittest.main()
