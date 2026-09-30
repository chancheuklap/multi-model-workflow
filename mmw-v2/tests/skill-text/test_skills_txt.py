"""skills.txt readers: the frontmatter lint and installed_skills()."""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "lib"
FRONTMATTER = LIB / "check_own_skill_frontmatter.py"
SKILL_TEXT_PATH = LIB / "skill_text.py"

_spec = importlib.util.spec_from_file_location("skill_text_under_test", SKILL_TEXT_PATH)
skill_text = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = skill_text
_spec.loader.exec_module(skill_text)


def write_skill(root: Path, relative: str, name: str) -> None:
    path = root / relative / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        f"---\nname: {name}\ndescription: Fixture skill.\n---\n\n# {name}\n",
        encoding="utf-8",
    )


class SkillsTxt(unittest.TestCase):
    def run_frontmatter(self, skills_txt: str, plant=None) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "mmw-v2"
            lib = root / "tests" / "lib"
            lib.mkdir(parents=True)
            shutil.copy(FRONTMATTER, lib / FRONTMATTER.name)
            (root / "skills.txt").write_text(skills_txt, encoding="utf-8")
            if plant is not None:
                plant(root)
            return subprocess.run(
                [sys.executable, str(lib / FRONTMATTER.name)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_frontmatter_lint_resolves_a_pstack_line_under_the_pstack_subtree(self):
        result = self.run_frontmatter("pstack/not-a-skill\n")
        combined = result.stdout + result.stderr
        self.assertEqual(1, result.returncode, combined)
        self.assertIn("mmw-v2/upstream-pstack/skills/not-a-skill/SKILL.md", combined)

    def test_frontmatter_lint_reads_a_marked_line_as_its_skill(self):
        present = self.run_frontmatter(
            "engineering/present +model-invoked\n",
            lambda root: write_skill(root, "upstream/skills/engineering/present", "present"),
        )
        self.assertEqual(0, present.returncode, present.stdout + present.stderr)

        missing = self.run_frontmatter("engineering/missing +model-invoked\n")
        combined = missing.stdout + missing.stderr
        self.assertEqual(1, missing.returncode, combined)
        self.assertNotIn("+model-invoked", combined)
        self.assertIn("mmw-v2/upstream/skills/engineering/missing/SKILL.md", combined)

    def test_frontmatter_lint_rejects_a_line_install_would_refuse(self):
        unknown = "engineering/triage +model"
        refused = self.run_frontmatter(unknown + "\n")
        combined = refused.stdout + refused.stderr
        self.assertEqual(1, refused.returncode, combined)
        self.assertEqual(1, combined.count(unknown), combined)
        self.assertIn("1 finding(s)", combined)

        own = "self/dispatch +model-invoked"
        refused = self.run_frontmatter(own + "\n")
        combined = refused.stdout + refused.stderr
        self.assertEqual(1, refused.returncode, combined)
        self.assertEqual(1, combined.count(own), combined)
        self.assertIn("1 finding(s)", combined)

    def test_installed_skills_maps_a_pstack_line_to_the_pstack_subtree(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            listed = root / "mmw-v2"
            listed.mkdir()
            (listed / "skills.txt").write_text(
                "pstack/alpha\npstack/beta +model-invoked\n",
                encoding="utf-8",
            )
            found = skill_text.installed_skills(root)
        self.assertEqual(
            {
                "alpha": "mmw-v2/upstream-pstack/skills/alpha",
                "beta": "mmw-v2/upstream-pstack/skills/beta",
            },
            found,
        )


if __name__ == "__main__":
    unittest.main()
