"""`--lint --drafts <dir>`: a batch linted before it is published.

The drafts are files, one per ticket: `TITLE:`, `LABELS:` and `BLOCKED BY:` header lines,
a line `---`, then the issue body; a draft's file name stands in for the issue number
it does not have yet. Each draft gets the same per-ticket lint a published ticket gets,
the graph comes from the `BLOCKED BY:` headers, and the run ends by listing what only a
published batch can show. The spec is the one tracker read, and it is patched here.
"""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from _load import load

vt = load()

SPEC = 555
SPEC_BODY = ("## Implementation Decisions\n\n### 1. One\n\nx\n\n### 2. Two\n\ny\n\n"
             "## Testing Decisions\n\nnone\n")
CRITERION = ("## Acceptance criteria\n\n"
             "- [ ] AC1: the importer writes six rows\n"
             "  CHECK: node scripts/import.mjs fixtures/valid.json\n"
             "  EXPECT: /^6 rows$/m\n  EVIDENCE: pending\n")
MANUAL = ("## Acceptance criteria\n\n"
          "- [ ] AC1: the wording reads well\n  EVIDENCE: pending\n")
LABELS = "mmw:ticket, ready-for-agent, junior-worker"


def draft(blocked="(none)", parent="#555, Implementation Decisions section 1",
          criteria=CRITERION, labels=LABELS, title="A ticket"):
    return (f"TITLE: {title}\nLABELS: {labels}\nBLOCKED BY: {blocked}\n"
            f"WORKER LINE: junior, a note the lint does not read\n---\n"
            f"## Parent\n\n{parent}\n\n{criteria}")


class DraftsFixture:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        (self.dir / f"{name}.md").write_text(text, encoding="utf-8")

    def lint(self, spec_body=SPEC_BODY, outsider=None):
        def body(n):
            if n == SPEC and spec_body is not None:
                return spec_body
            raise vt.TrackerReadError(n, "body", "offline")
        with mock.patch.object(vt, "fetch_body", side_effect=body), \
             mock.patch.object(vt, "fetch_outsider",
                               side_effect=outsider or (lambda n: {"spec": None, "state": ""})), \
             mock.patch.object(vt, "fetch_sub_issues",
                               side_effect=AssertionError("drafts mode lists no sub-issues")), \
             mock.patch.object(vt, "fetch_blocked_by",
                               side_effect=AssertionError("drafts mode reads no tracker link")):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.main([str(SPEC), "--lint", "--drafts", str(self.dir)])
        return code, out.getvalue()


class TestDrafts(DraftsFixture, unittest.TestCase):
    def test_clean_drafts_are_linted_each_then_graphed_by_name(self):
        self.write("T1-contract", draft())
        self.write("T2-page", draft(blocked="T1-contract",
                                    parent="#555, Implementation Decisions section 2"))
        code, printed = self.lint()
        self.assertEqual(code, 0, printed)
        self.assertIn("## T1-contract (draft)", printed)
        self.assertIn("T2-page LINT OK", printed)
        self.assertIn("level 0: T1-contract", printed)
        self.assertIn("level 1: T2-page", printed)
        self.assertIn("sections named by a ticket: 2/2", printed)

    def test_the_run_says_what_it_could_not_check(self):
        self.write("T1", draft())
        _, printed = self.lint()
        self.assertIn("not checked on drafts", printed)
        self.assertIn("sub-issue of the spec", printed)
        self.assertIn("blocking links the tracker records", printed)

    def test_a_per_ticket_finding_fails_the_run_and_names_the_draft(self):
        self.write("T1", draft())
        self.write("T2", draft(criteria=MANUAL))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("manual-gate", printed)
        self.assertIn("drafts with findings: T2", printed)

    def test_a_cycle_between_drafts_is_named_by_draft_name(self):
        self.write("T1", draft(blocked="T2"))
        self.write("T2", draft(blocked="T1"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[cycle]", printed)
        self.assertRegex(printed, r"cycle detected: T\d -> T\d -> T\d")

    def test_a_blocker_that_is_no_draft_is_an_error(self):
        self.write("T1", draft(blocked="T9-missing"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("`T9-missing`", printed)
        self.assertIn("[unknown-draft]", printed)

    def test_a_published_blocker_is_looked_up_like_a_tracker_one(self):
        self.write("T1", draft(blocked="#42"))
        code, printed = self.lint(
            outsider=lambda n: {"spec": 318, "state": "OPEN"} if n == 42 else {})
        self.assertEqual(code, 0, printed)
        self.assertIn("T1 is blocked by #42, a ticket under spec #318", printed)
        self.assertIn("waiting on another spec: T1 ← #42", printed)

    def test_a_draft_whose_parent_names_another_spec_first_is_an_error(self):
        self.write("T1", draft(parent="#318 Implementation Decisions section 4; "
                                      "#555, Implementation Decisions section 1"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[parent-order]", printed)

    def test_a_draft_without_the_ticket_layer_label_is_an_error(self):
        self.write("T1", draft(labels="ready-for-agent, junior-worker"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("`mmw:ticket`", printed)

    def test_the_worker_label_is_read_off_the_header(self):
        self.write("T1", draft(labels="mmw:ticket, ready-for-agent, junior-worker, senior-worker"))
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[worker-label]", printed)

    def test_a_header_without_the_separator_is_an_error_not_a_skip(self):
        self.write("T1", "TITLE: x\nLABELS: mmw:ticket\nBLOCKED BY: (none)\n## Parent\n\n#555\n")
        code, printed = self.lint()
        self.assertEqual(code, 1)
        self.assertIn("[draft-unreadable]", printed)
        self.assertIn("drafts with findings: T1", printed)

    def test_an_unreadable_spec_is_said_and_the_per_ticket_checks_still_run(self):
        self.write("T1", draft(criteria=MANUAL))
        code, printed = self.lint(spec_body=None)
        self.assertEqual(code, 1)
        self.assertIn("[spec-unreadable]", printed)
        self.assertIn("manual-gate", printed)
        self.assertNotIn("sections named by a ticket", printed)

    def test_drafts_belongs_to_lint(self):
        with redirect_stdout(io.StringIO()), \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            with self.assertRaises(SystemExit):
                vt.main([str(SPEC), "--drafts", str(self.dir)])
        self.assertIn("--drafts belongs to --lint", err.getvalue())


if __name__ == "__main__":
    unittest.main()
