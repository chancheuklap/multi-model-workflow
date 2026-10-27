import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from test_lint_drafts import CRITERION, LABELS, DraftsFixture, draft, vt


class TestReadFirst(DraftsFixture, unittest.TestCase):
    def lint_published(self, body):
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_ticket", return_value={
                 "labels": [{"name": x.strip()} for x in LABELS.split(",")]}), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main(["77", "--lint"])
        return code, out.getvalue()

    def test_read_first_claude_link_is_an_error(self):
        lines = [
            "- [Winner](https://claude.ai/artifact/winner), baseline.",
            "- https://claude.ai/code/artifact/second, baseline.",
            "- <https://claude.ai/chat/third>, decision.",
        ]
        body = ("## What to build\n\n1. Import the rows. AC1.\n\n"
                "## Read first\n\n" + "\n".join(lines) + "\n\n" + CRITERION)
        code, printed = self.lint_published(body)
        self.assertEqual(code, 1, printed)
        errors = [line for line in printed.splitlines()
                  if "[unreadable-read-first]" in line]
        self.assertEqual(len(errors), len(lines), printed)
        for source, error in zip(lines, errors):
            self.assertIn("ERROR", error)
            self.assertIn("#77", error)
            self.assertIn(source, error)
            self.assertIn("copy what the page settles into a file in the repository", error)
            self.assertIn("commit it", error)
            self.assertIn("cite that path", error)

    def test_read_first_claude_link_fails_a_draft(self):
        source = "- [Winner](https://claude.ai/code/artifact/winner), baseline."
        self.write("T1", draft(criteria="## Read first\n\n" + source + "\n\n" + CRITERION))
        code, printed = self.lint()
        self.assertEqual(code, 1, printed)
        errors = [line for line in printed.splitlines()
                  if "[unreadable-read-first]" in line]
        self.assertEqual(len(errors), 1, printed)
        self.assertIn("ERROR T1", errors[0])
        self.assertIn(source, errors[0])
        self.assertIn("drafts with findings: T1", printed)

    def test_claude_link_outside_read_first_is_fine(self):
        body = ("## Problem\n\nSource https://claude.ai/artifact/quoted\n\n"
                "## Read first\n\n- `efforts/owner-page.md`, baseline.\n"
                "- [Other site](https://claude.ai.example.org/artifact/winner).\n\n"
                "## What to build\n\n1. Import the rows. AC1.\n\n"
                "Quoted source https://claude.ai/code/artifact/quoted\n\n" + CRITERION)
        code, printed = self.lint_published(body)
        self.assertEqual(code, 0, printed)
        self.assertNotIn("[unreadable-read-first]", printed)
        self.write("T1", draft(criteria=body))
        code, printed = self.lint()
        self.assertEqual(code, 0, printed)
        self.assertNotIn("[unreadable-read-first]", printed)


if __name__ == "__main__":
    unittest.main()
