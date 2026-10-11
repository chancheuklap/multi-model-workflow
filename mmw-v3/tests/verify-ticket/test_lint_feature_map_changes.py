"""Publish-time `--lint` on a spec's `## Feature map changes`.

The batch is made-up issue bodies, as `test_lint_spec.py` does. A feature file
that already exists is committed on the temp repository's base branch, which is
HEAD: publish-time `--lint` runs from a checkout of that branch.
"""

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load

vt = load()

SPEC = 216
CHILD_LABELS = ["mmw:ticket", "ready-for-agent", "junior-worker"]
FEATURE = """\
# Open

The user opens the product.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: row:demo.open
  check: bash tests/guard.sh

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.

## Gotchas

- A second open reuses the same port.
"""
CONTRACT = """\
effort: demo
rows:
- id: demo.open
  component: fixture
- id: demo.new
  component: fixture
- id: demo.listed
  component: fixture
"""


def ticket(owns=(), check="node scripts/import.mjs fixtures/valid.json"):
    owned = "\n".join(f"- {path}" for path in owns) or "- None"
    return (
        "## Parent\n\n#216\n\n"
        "## Owns\n\n"
        f"{owned}\n\n"
        "## Acceptance criteria\n\n"
        "- [ ] AC1: the importer writes six rows\n"
        f"  CHECK: {check}\n"
        "  EXPECT: /^6 rows$/m\n"
        "  EVIDENCE: pending\n"
    )


def spec_body(changes, sources=""):
    extra = f"\n## Sources\n\n{sources}\n" if sources else ""
    return (
        "## Summary\n\nA spec.\n\n"
        "## Feature map changes\n\n"
        f"{changes}\n"
        f"{extra}"
        "## Out of Scope\n\n- nothing\n"
    )


class FeatureMapChangesLint(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(self.root)],
            check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, files):
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "add", "-A"], check=True,
                       capture_output=True)
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-qm", "base"],
            check=True, capture_output=True)

    def empty_base(self):
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "--allow-empty", "-m", "base"],
            check=True, capture_output=True)

    def lint(self, body, tickets, blocked=None, state="OPEN"):
        """`run_lint` over `tickets`, a list of `(number, body)`."""
        numbers = [number for number, _ in tickets]
        bodies = {SPEC: body, **{number: text for number, text in tickets}}
        spec_ticket = {"labels": [{"name": "mmw:spec"}], "state": "OPEN"}
        child = {"labels": [{"name": name} for name in CHILD_LABELS], "state": state}
        blockers = blocked or {}

        def fetch_ticket(number):
            return spec_ticket if number == SPEC else child

        with mock.patch.object(vt, "repo_root", return_value=self.root), \
             mock.patch.object(vt, "fetch_body", side_effect=lambda n: bodies[n]), \
             mock.patch.object(vt, "fetch_ticket", side_effect=fetch_ticket), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             mock.patch.object(vt, "fetch_sub_issues", return_value=numbers), \
             mock.patch.object(vt, "fetch_blocked_by",
                               side_effect=lambda n: blockers.get(n, [])), \
             mock.patch.object(vt, "lint_batch_graph", return_value=0):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(SPEC)
        return code, out.getvalue()

    def test_an_unhomed_row_is_an_error(self):
        self.commit({
            "efforts/demo/screen-contract.yaml": CONTRACT,
            "docs/features/demo/open.md": FEATURE,
        })
        changes = (
            "- `docs/features/demo/open.md` (changed)\n"
            "  - added `open-extra` source: row:demo.listed\n"
        )
        code, printed = self.lint(
            spec_body(changes, "Screen contract: `efforts/demo/screen-contract.yaml`"),
            [(301, ticket(("docs/features/demo/open.md",), check="bash tests/guard.sh"))])
        self.assertEqual(code, 1, printed)
        self.assertIn("[unhomed-row]", printed)
        self.assertIn("demo.new", printed)
        self.assertNotIn("demo.listed", printed)
        self.assertNotIn("demo.open", printed)

        code, bare = self.lint(
            spec_body("none", "Screen contract: `efforts/demo/screen-contract.yaml`"),
            [(301, ticket())])
        self.assertEqual(code, 1, bare)
        self.assertIn("demo.new", bare)
        self.assertIn("demo.listed", bare)
        self.assertNotIn("demo.open", bare)

    def test_an_unowned_feature_file_is_an_error(self):
        self.empty_base()
        changes = (
            "- `docs/features/demo/save.md` (new)\n"
            "  - added `save-note` source: #12 §2\n"
        )
        code, printed = self.lint(spec_body(changes), [(301, ticket())])
        self.assertEqual(code, 1, printed)
        self.assertIn("[unowned-feature]", printed)
        self.assertIn("docs/features/demo/save.md", printed)

    def test_two_concurrent_owners_is_an_error(self):
        self.empty_base()
        changes = (
            "- `docs/features/demo/open.md` (changed)\n"
            "  - changed `open-from-command` source: existing 2026-01-15\n"
        )
        owned = ticket(("docs/features/demo/open.md",))
        code, printed = self.lint(spec_body(changes), [(301, owned), (302, owned)])
        self.assertEqual(code, 1, printed)
        self.assertIn("[concurrent-owners]", printed)
        self.assertIn("#301", printed)
        self.assertIn("#302", printed)

        code, quiet = self.lint(
            spec_body(changes), [(301, owned), (302, owned)], blocked={302: [301]})
        self.assertEqual(code, 0, quiet)
        self.assertNotIn("[concurrent-owners]", quiet)
        self.assertNotIn("ERROR", quiet)

    def test_a_changed_feature_needs_a_pin(self):
        self.commit({"docs/features/demo/open.md": FEATURE})
        changes = (
            "- `docs/features/demo/open.md` (changed)\n"
            "  - added `open-extra` source: #12 §2\n"
        )
        owned = ("docs/features/demo/open.md",)
        code, printed = self.lint(
            spec_body(changes), [(301, ticket(owned))])
        self.assertEqual(code, 1, printed)
        self.assertIn("[missing-pin]", printed)
        self.assertIn("docs/features/demo/open.md", printed)

        code, quiet = self.lint(
            spec_body(changes),
            [(301, ticket(owned, check="bash tests/guard.sh"))])
        self.assertEqual(code, 0, quiet)
        self.assertNotIn("[missing-pin]", quiet)
        self.assertNotIn("ERROR", quiet)

    def test_an_old_spec_is_a_warning(self):
        self.empty_base()
        body = "## Summary\n\nA spec.\n\n## Out of Scope\n\n- nothing\n"
        code, printed = self.lint(body, [(301, ticket())])
        self.assertEqual(code, 0, printed)
        self.assertIn("[no-feature-map-changes]", printed)
        self.assertIn("WARN", printed)
        self.assertNotIn("ERROR", printed)

    def test_a_closed_ticket_missing_pin_does_not_stop_the_batch(self):
        self.commit({"docs/features/demo/open.md": FEATURE})
        changes = (
            "- `docs/features/demo/open.md` (changed)\n"
            "  - added `open-extra` source: #12 §2\n"
        )
        code, printed = self.lint(
            spec_body(changes),
            [(301, ticket(("docs/features/demo/open.md",)))],
            state="CLOSED")
        self.assertEqual(code, 0, printed)
        self.assertIn("[missing-pin]", printed)
        self.assertIn("[closed-ticket]", printed)

    def test_a_changed_sub_feature_is_not_a_pin_candidate(self):
        self.commit({"docs/features/demo/open.md": FEATURE})
        changes = (
            "- `docs/features/demo/open.md` (changed)\n"
            "  - changed `open-from-command` source: row:demo.open\n"
        )
        code, printed = self.lint(
            spec_body(changes),
            [(301, ticket(("docs/features/demo/open.md",)))])
        self.assertEqual(code, 0, printed)
        self.assertNotIn("[missing-pin]", printed)
        self.assertNotIn("ERROR", printed)


if __name__ == "__main__":
    unittest.main()
