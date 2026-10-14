import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RENDER = Path(__file__).resolve().parents[1] / "render.py"
SHARED = RENDER.parent / "shared.md"


def run(home, *args):
    env = dict(os.environ, MMW_INSTALL_HOME=str(home))
    for k in ("CODEX_HOME",):
        env.pop(k, None)
    return subprocess.run([sys.executable, str(RENDER), *args], env=env, capture_output=True, text=True)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".codex").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_the_codex_target_with_the_shared_body(self):
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = (self.home / ".codex/AGENTS.md").read_text()
        self.assertTrue(text.startswith("<!-- mmw prompt-sync:"))
        self.assertEqual(text.split("\n", 1)[1], SHARED.read_text())

    def test_replaces_a_file_mmw_v3_generated_without_adopt(self):
        body = "the v3 shared body\n"
        digest = hashlib.sha256(body.encode()).hexdigest()
        target = self.home / ".codex/AGENTS.md"
        target.write_text("<!-- mmw prompt-sync: generated from mmw-v3/prompt/shared.md; "
                          f"edit that, not this file. body-sha256={digest} -->\n" + body)
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(target.read_text().startswith("<!-- mmw prompt-sync: generated from mmw-v4/"))
        self.assertTrue(target.read_text().endswith(SHARED.read_text()))

    def test_check_passes_after_write_and_fails_when_stale(self):
        run(self.home)
        self.assertEqual(run(self.home, "--check").returncode, 0)
        target = self.home / ".codex/AGENTS.md"
        target.write_text(target.read_text() + "\nextra\n")
        self.assertEqual(run(self.home, "--check").returncode, 1)

    def test_refuses_to_overwrite_hand_edited_target(self):
        run(self.home)
        target = self.home / ".codex/AGENTS.md"
        target.write_text(target.read_text() + "\nhand edit\n")
        r = run(self.home)
        self.assertEqual(r.returncode, 2)
        self.assertIn("hand edit", target.read_text())
        self.assertEqual(run(self.home, "--adopt").returncode, 0)
        self.assertNotIn("hand edit", target.read_text())

    def test_refuses_foreign_file_without_adopt(self):
        target = self.home / ".codex/AGENTS.md"
        target.write_text("someone else's file\n")
        r = run(self.home)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(target.read_text(), "someone else's file\n")
        self.assertEqual(run(self.home, "--adopt").returncode, 0)
        self.assertTrue(target.read_text().startswith("<!-- mmw prompt-sync:"))

    def test_skips_missing_host(self):
        shutil.rmtree(self.home / ".codex")
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.home / ".codex").exists())

    def test_a_grok_home_is_left_alone(self):
        (self.home / ".grok").mkdir()
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(list((self.home / ".grok").iterdir()), [])
        self.assertEqual(run(self.home, "--check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
