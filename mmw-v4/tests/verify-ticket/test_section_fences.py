import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from _load import load
from test_lint_drafts import CRITERION, LABELS


vt = load()


class TestSectionFences(unittest.TestCase):
    def test_unclosed_fence_cannot_hide_review_findings(self):
        report = ("REVIEW a..b\n\n## Spec\n\nquote:\n```python\nx = 1\n\n"
                  "## In-ticket\n\n- Spec [x] a.py:3 claim\n")
        with self.assertRaisesRegex(ValueError, "--sub-issue fault"):
            vt.require_in_ticket(report, 1, 1348)

    def test_read_first_lint_sees_past_a_fenced_example(self):
        source = "- https://claude.ai/artifact/real-baseline"
        body = ("## Problem\n\n```markdown\n## Read first\n\n"
                "- `example.md`\n```\n\n## Read first\n\n" + source + "\n\n"
                "## What to build\n\n1. Import the rows. AC1.\n\n" + CRITERION)
        with mock.patch.object(vt, "fetch_body", return_value=body), \
             mock.patch.object(vt, "fetch_ticket", return_value={
                 "labels": [{"name": name.strip()} for name in LABELS.split(",")]}), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             redirect_stdout(io.StringIO()) as out:
            code = vt.main(["77", "--lint"])
        printed = out.getvalue()
        self.assertEqual(code, 1, printed)
        errors = [line for line in printed.splitlines()
                  if "[unreadable-read-first]" in line]
        self.assertEqual(len(errors), 1, printed)
        self.assertIn(source, errors[0])

    def test_section_skips_fenced_headings(self):
        for opening, closing in (("```markdown", "```"), ("~~~~markdown", "~~~~")):
            with self.subTest(opening=opening):
                body = (f"## Problem\n\n{opening}\n## Read first\n\n"
                        f"- `example.md`\n{closing}\n\n## Read first\n\n"
                        f"- `real.md`\n{opening}\n## Seam\nexample\n"
                        f"{closing}\nAfter.\n\n## Seam\nNone\n")
                self.assertEqual(vt.section(body, "Read first"), [
                    "- `real.md`", opening, "## Seam", "example", closing, "After."])
        body = ("## Problem\n- item\n    ```\n    ## Read first\n"
                "    ```\n## Read first\n- real\n")
        self.assertEqual(vt.section(body, "Read first"), ["- real"])

    def test_section_keeps_its_own_fenced_block(self):
        body = "## Read first\n\nBefore.\n```python\nprint('baseline')\n```\nAfter.\n\n## Seam\nNone\n"
        self.assertEqual(vt.section(body, "Read first"), [
            "Before.", "```python", "print('baseline')", "```", "After."])


if __name__ == "__main__":
    unittest.main()
