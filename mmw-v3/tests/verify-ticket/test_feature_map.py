"""feature_map.py lint, run against a repository the test writes in a temporary directory."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[2] / "skills" / "verify-ticket" / "scripts"
          / "feature_map.py")
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "feature-map"
OPEN = "docs/features/alpha/open.md"
ALPHA_README = "docs/features/alpha/README.md"

MISSING_SECTION = """\
# Open

The user opens the product and sees it ready.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: row:demo.open
  check: bash tests/guard.sh

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.
"""

WRONG_ORDER = """\
# Open

The user opens the product and sees it ready.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: row:demo.open
  check: bash tests/guard.sh

## Driving it

Preconditions:

- The product is installed.

## How to get to it (user POV)

- Run the open command.

## Gotchas

- A second open reuses the same port.
"""

NO_PARAGRAPH = """\
# Open
## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: #901
  check: bash tests/guard.sh

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.

## Gotchas

- A second open reuses the same port.
"""

NO_H1 = """\
The user opens the product and sees it ready.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: #901
  check: bash tests/guard.sh

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.

## Gotchas

- A second open reuses the same port.
"""

BAD_SOURCE = """\
# Open

The user opens the product and sees it ready.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: banana
  check: bash tests/guard.sh
- `open-from-spec` The user follows the numbered section.
  check: node tests/guard.js
- `open-from-ticket` The user follows the ticket.
  source: #901

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.

## Gotchas

- A second open reuses the same port.
"""


def run_lint(root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "lint"],
        cwd=root, text=True, capture_output=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def lint_complete(edit=None) -> tuple[int, str]:
    """The complete fixture, after `edit` rewrites a file in the copy."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(FIXTURES / "complete", root, dirs_exist_ok=True)
        if edit is not None:
            edit(root)
        return run_lint(root)


def replace(root: Path, rel: str, text: str) -> None:
    (root / rel).write_text(text, encoding="utf-8")


def lines_of(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.strip()]


class TestFeatureMap(unittest.TestCase):
    def test_a_complete_map_is_ok(self):
        # alpha/open.md, alpha/save.md and beta/close.md. README.md is not a feature file.
        code, output = lint_complete()
        self.assertEqual(code, 0, output)
        self.assertEqual(output.strip(), "FEATURE MAP OK 3 features")

    def test_a_missing_section_is_named(self):
        code, output = lint_complete(lambda root: replace(root, OPEN, MISSING_SECTION))
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        self.assertEqual(len(lines_of(output)), 1, output)
        self.assertIn("docs/features/alpha/open.md:19:", output)
        self.assertIn("Gotchas", output)

        code, output = lint_complete(lambda root: replace(root, OPEN, WRONG_ORDER))
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        self.assertEqual(len(lines_of(output)), 1, output)
        self.assertIn("docs/features/alpha/open.md:11:", output)
        self.assertIn("How to get to it (user POV)", output)

        code, output = lint_complete(lambda root: replace(root, OPEN, NO_PARAGRAPH))
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        self.assertEqual(len(lines_of(output)), 1, output)
        self.assertIn("docs/features/alpha/open.md:2:", output)
        self.assertIn("paragraph", output)

        code, output = lint_complete(lambda root: replace(root, OPEN, NO_H1))
        self.assertEqual(code, 1, output)
        self.assertIn("docs/features/alpha/open.md:1:", output)
        self.assertIn("an H1", output)
        self.assertNotIn("FEATURE MAP OK", output)

        def drop_features(root: Path) -> None:
            readme = root / ALPHA_README
            rows = readme.read_text(encoding="utf-8").splitlines()
            cut = rows.index("## Features")
            readme.write_text("\n".join(rows[:cut]).rstrip() + "\n", encoding="utf-8")

        code, output = lint_complete(drop_features)
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        reported = lines_of(output)
        self.assertTrue(any("README.md:19:" in line and "Features" in line for line in reported), reported)
        self.assertTrue(any("open.md:1:" in line for line in reported), reported)
        self.assertTrue(any("save.md:1:" in line for line in reported), reported)

    def test_index_and_files_must_match(self):
        def edit(root: Path) -> None:
            readme = root / ALPHA_README
            readme.write_text(readme.read_text(encoding="utf-8").replace("./save.md", "./missing.md"),
                              encoding="utf-8")

        code, output = lint_complete(edit)
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        reported = lines_of(output)
        self.assertEqual(len(reported), 2, output)
        self.assertTrue(any("README.md:24:" in line and "missing.md" in line for line in reported), reported)
        self.assertTrue(any("save.md:1:" in line and "save.md" in line for line in reported), reported)

    def test_an_unknown_row_is_named(self):
        def edit(root: Path) -> None:
            path = root / OPEN
            path.write_text(path.read_text(encoding="utf-8").replace(
                "source: row:demo.open", "source: row:demo.missing"), encoding="utf-8")

        code, output = lint_complete(edit)
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        reported = lines_of(output)
        self.assertEqual(len(reported), 1, output)
        self.assertIn("docs/features/alpha/open.md:8:", reported[0])
        self.assertIn("demo.missing", reported[0])

    def test_a_missing_check_target_is_named(self):
        def edit(root: Path) -> None:
            path = root / OPEN
            text = path.read_text(encoding="utf-8")
            text = text.replace("check: bash tests/guard.sh", "check: node tests/missing.js", 1)
            text = text.replace(
                "check: python -m unittest tests.test_guard.GuardTests.test_opens",
                "check: python3 -m unittest tests.test_guard.GuardTests.test_missing",
                1)
            text = text.replace("check: journey.py run smoke", "check: journey.py run absent")
            path.write_text(text, encoding="utf-8")

        code, output = lint_complete(edit)
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        reported = lines_of(output)
        self.assertEqual(len(reported), 3, output)
        self.assertTrue(any("open.md:9:" in line and "tests/missing.js" in line for line in reported),
                        reported)
        self.assertTrue(any("open.md:15:" in line and "test_missing" in line for line in reported),
                        reported)
        self.assertTrue(any("open.md:21:" in line and ".mmw/journeys/absent/" in line for line in reported),
                        reported)

    def test_a_bad_source_is_named(self):
        code, output = lint_complete(lambda root: replace(root, OPEN, BAD_SOURCE))
        self.assertEqual(code, 1, output)
        self.assertNotIn("FEATURE MAP OK", output)
        reported = lines_of(output)
        self.assertEqual(len(reported), 3, output)
        self.assertTrue(any("open.md:8:" in line and "banana" in line for line in reported), reported)
        self.assertTrue(any("open.md:10:" in line for line in reported), reported)
        self.assertTrue(any("open.md:12:" in line for line in reported), reported)

    def test_check_none_is_a_note(self):
        def edit(root: Path) -> None:
            path = root / OPEN
            text = path.read_text(encoding="utf-8").replace(
                "check: bash tests/guard.sh",
                "check: none: no script guards a locked row",
                1)
            path.write_text(text, encoding="utf-8")

        code, output = lint_complete(edit)
        self.assertEqual(code, 0, output)
        reported = lines_of(output)
        self.assertTrue(any(line.startswith("NOTE ") and "open.md:9:" in line
                            and "no script guards a locked row" in line for line in reported), reported)
        self.assertTrue(any(line == "FEATURE MAP OK 3 features" for line in reported), reported)

    def test_no_features_dir_is_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README").write_text("no feature map\n", encoding="utf-8")
            code, output = run_lint(root)
        self.assertEqual(code, 2, output)
        self.assertNotIn("FEATURE MAP OK", output)
        self.assertIn("docs/features/", output)


if __name__ == "__main__":
    unittest.main()
