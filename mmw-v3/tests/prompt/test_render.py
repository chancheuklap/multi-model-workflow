import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RENDER = Path(__file__).resolve().parents[2] / "prompt" / "render.py"
SHARED = RENDER.parent / "shared.md"
CODEX_LOCAL = RENDER.parent / "hosts" / "codex.md"


def run(home, *args):
    env = dict(os.environ, MMW_V3_HOME=str(home))
    for k in ("CODEX_HOME", "PI_HOME", "PI_CODING_AGENT_DIR"):
        env.pop(k, None)
    return subprocess.run([sys.executable, str(RENDER), *args], env=env, capture_output=True, text=True)


def grok_config(home, agents="false"):
    (home / ".grok").mkdir(exist_ok=True)
    (home / ".grok" / "config.toml").write_text(f"[compat.claude]\nskills = false\nagents = {agents}\n")


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        for d in (".codex", ".pi/agent", ".grok"):
            (self.home / d).mkdir(parents=True)
        grok_config(self.home)

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_three_targets_with_shared_body_and_codex_local(self):
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        shared = SHARED.read_text()
        for rel in (".codex/AGENTS.md", ".pi/agent/AGENTS.md", ".grok/AGENTS.md"):
            text = (self.home / rel).read_text()
            self.assertTrue(text.startswith("<!-- mmw prompt-sync:"), rel)
            self.assertTrue(text.endswith(shared), rel)
        codex_line = CODEX_LOCAL.read_text().strip()
        self.assertIn(codex_line, (self.home / ".codex/AGENTS.md").read_text())
        self.assertNotIn(codex_line, (self.home / ".pi/agent/AGENTS.md").read_text())

    def test_check_passes_after_write_and_fails_when_stale(self):
        run(self.home)
        self.assertEqual(run(self.home, "--check").returncode, 0)
        target = self.home / ".codex/AGENTS.md"
        target.write_text(target.read_text() + "\nextra\n")
        r = run(self.home, "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("被直接改过", r.stderr)

    def test_refuses_to_overwrite_hand_edited_target(self):
        run(self.home)
        target = self.home / ".pi/agent/AGENTS.md"
        target.write_text(target.read_text() + "\nhand edit\n")
        r = run(self.home)
        self.assertEqual(r.returncode, 2)
        self.assertIn("hand edit", target.read_text())
        self.assertEqual(run(self.home, "--adopt").returncode, 0)
        self.assertNotIn("hand edit", target.read_text())

    def test_refuses_foreign_file_without_adopt(self):
        target = self.home / ".grok/AGENTS.md"
        target.write_text("someone else's file\n")
        r = run(self.home)
        self.assertEqual(r.returncode, 2)
        self.assertEqual(target.read_text(), "someone else's file\n")
        self.assertEqual(run(self.home, "--adopt").returncode, 0)
        self.assertTrue(target.read_text().startswith("<!-- mmw prompt-sync:"))

    def test_skips_missing_host(self):
        shutil.rmtree(self.home / ".pi")
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.home / ".pi").exists())

    def test_grok_compat_on_is_reported(self):
        grok_config(self.home, "true")
        r = run(self.home)
        self.assertEqual(r.returncode, 1)
        self.assertIn("compat.claude", r.stderr)
        self.assertTrue((self.home / ".grok/AGENTS.md").exists())

    def test_a_file_the_previous_renderer_generated_counts_as_generated(self):
        # A target written while the header named mmw-v2/prompt carries the same mark and
        # body hash, so it is overwritten without --adopt.
        run(self.home)
        target = self.home / ".codex/AGENTS.md"
        header, body = target.read_text().split("\n", 1)
        target.write_text(header.replace("mmw-v3/prompt", "mmw-v2/prompt") + "\n" + body)
        self.assertIn("mmw-v2/prompt", target.read_text())
        r = run(self.home)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("mmw-v2/prompt", target.read_text())
        self.assertIn("generated from mmw-v3/prompt/shared.md", target.read_text())


if __name__ == "__main__":
    unittest.main()
