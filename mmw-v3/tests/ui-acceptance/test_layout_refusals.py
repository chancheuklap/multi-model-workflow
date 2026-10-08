import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "skills/ui-acceptance/scripts"


class LayoutRefusals(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "repo"
        (self.root / ".mmw").mkdir(parents=True)
        self.home = Path(self.tmp.name) / "home"
        self.env = dict(os.environ, MMW_HOME=str(self.home))

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                              cwd=self.root, env=self.env, capture_output=True,
                              text=True, timeout=30)

    def test_an_old_layout_is_refused_with_the_migration_command(self):
        for key in ("start", "stop", "discover", "doctor", "ports", "stories",
                    "journeys", "leaves_machine", "harness_markers"):
            (self.root / ".mmw/target.json").write_text(json.dumps({key: "true"}))
            commands = (
                ("target_config.py", "--check"),
                ("target_config.py", "--validate"),
                ("lease.py", "claim"),
                ("lease.py", "run", "--", "touch", "command-ran"),
                ("journey.py", "run", "notes/open"),
                ("harness-guard.py", str(self.root)),
            )
            for command in commands:
                with self.subTest(key=key, command=command):
                    proc = self.cli(*command)
                    self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                    self.assertIn(".mmw/target.json", proc.stderr)
                    self.assertIn("old layout", proc.stderr)
                    self.assertIn("python3 ~/.agents/skills/setup-mmw/scripts/"
                                  "migrate_products.py <产品名>", proc.stderr)
                    self.assertNotIn("complete:", proc.stdout)
                    self.assertNotIn("JOURNEY OK", proc.stdout)
                    self.assertNotIn("HARNESS OK", proc.stdout)
                    self.assertNotIn("Traceback", proc.stderr)
                    self.assertFalse((self.root / "command-ran").exists())
                    self.assertFalse(self.home.exists())

    def test_story_parity_refuses_the_old_layout_before_starting_the_service(self):
        fixture = Path(__file__).resolve().parent / "fixtures/story/repo"
        shutil.copytree(fixture, self.root, dirs_exist_ok=True)
        (self.root / ".git").mkdir()
        (self.root / ".mmw/target.json").write_text(json.dumps({
            "stories": "touch command-ran",
        }))
        proc = subprocess.run([
            "uv", "run", "--quiet", str(SCRIPTS / "story-parity.py"),
            "--contract", "efforts/story/screen-contract.yaml", "--pages", "demo",
        ], cwd=self.root, env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("migrate_products.py <产品名>", proc.stderr)
        self.assertNotIn("STORY OK", proc.stdout)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertFalse((self.root / "command-ran").exists())
        self.assertFalse(self.home.exists())

    def test_a_journey_name_without_product_is_refused(self):
        (self.root / ".mmw/target.json").write_text(json.dumps({"products": ["notes"]}))
        product = self.root / ".mmw/notes"
        product.mkdir()
        (product / "target.json").write_text(json.dumps({"ports": 0, "discover": "true"}))
        proc = self.cli("journey.py", "run", "open")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("<product>/<flow>", proc.stderr)
        self.assertNotIn("JOURNEY OK", proc.stdout)
        self.assertFalse(self.home.exists())
