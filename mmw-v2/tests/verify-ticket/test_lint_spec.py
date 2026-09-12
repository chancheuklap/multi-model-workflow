"""`--lint` given a spec number lints every sub-issue, then the graph once.

The night's pre-batch pass (dispatch `night.md` 1b) runs `<engine> <spec> --lint`. A spec
carries no `## Acceptance criteria`, so without this it is read as a ticket with nothing
to check and comes back 0 without reading one sub-issue. What tells a spec apart from a
criteria-less ticket is its layer label `mmw:spec`; an issue carrying no layer label at
all is told apart by the shape of the tree, no parent and sub-issues of its own.
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from _load import load

vt = load()

SPEC = 216
CLEAN = ("## Parent\n\n#216\n\n## Acceptance criteria\n\n"
         "- [ ] AC1: the importer writes six rows\n"
         "  CHECK: node scripts/import.mjs fixtures/valid.json\n"
         "  EXPECT: /^6 rows$/m\n  EVIDENCE: pending\n")
MANUAL = ("## Parent\n\n#216\n\n## Acceptance criteria\n\n"
          "- [ ] AC1: the wording reads well\n  EVIDENCE: pending\n")
SPEC_BODY = "## Summary\n\nA spec.\n\n## Out of Scope\n\n- nothing\n"
LABELS = {"labels": [{"name": "ready-for-agent"}, {"name": "junior-worker"}], "state": "OPEN"}


def lint(number, bodies, children, parent=None, graph=0, labels=None):
    """`run_lint(number)` over made-up issues; returns (exit code, printed)."""
    fetched = dict(LABELS)
    if labels is not None:
        fetched["labels"] = [{"name": name} for name in labels]
    with mock.patch.object(vt, "fetch_body", side_effect=lambda n: bodies[n]), \
         mock.patch.object(vt, "fetch_ticket", side_effect=lambda n: (
             fetched if n == number else LABELS)), \
         mock.patch.object(vt, "fetch_parent", return_value=parent), \
         mock.patch.object(vt, "fetch_sub_issues", return_value=children) as subs, \
         mock.patch.object(vt, "lint_batch_graph", return_value=graph) as batch, \
         mock.patch.object(vt, "lint_ticket_graph", return_value=graph) as ticket_graph:
        with redirect_stdout(io.StringIO()) as out:
            code = vt.run_lint(number)
    return code, out.getvalue(), subs, batch, ticket_graph


class TestLintOnASpec(unittest.TestCase):
    def test_every_sub_issue_is_linted_and_a_finding_in_one_fails_the_run(self):
        code, printed, _, batch, _ = lint(
            SPEC, {SPEC: SPEC_BODY, 301: CLEAN, 302: MANUAL}, [301, 302])
        self.assertEqual(code, 1)
        self.assertIn("## #301 (OPEN)", printed)
        self.assertIn("## #302", printed)
        self.assertIn("manual-gate", printed)
        self.assertIn("tickets with findings: #302", printed)
        batch.assert_called_once_with(SPEC, [301, 302])

    def test_clean_sub_issues_and_a_clean_graph_exit_0(self):
        code, printed, _, batch, _ = lint(
            SPEC, {SPEC: SPEC_BODY, 301: CLEAN, 302: CLEAN}, [301, 302])
        self.assertEqual(code, 0)
        self.assertIn("is a spec with 2 sub-issues", printed)
        self.assertNotIn("ERROR", printed)
        batch.assert_called_once()

    def test_a_bad_graph_fails_the_run_even_when_every_ticket_is_clean(self):
        code, _, _, _, _ = lint(SPEC, {SPEC: SPEC_BODY, 301: CLEAN}, [301], graph=1)
        self.assertEqual(code, 1)

    def test_a_criteria_less_ticket_under_a_spec_is_still_a_ticket(self):
        """A `ready-for-human` ticket has no criteria either. Carrying no layer label, it
        is told apart by its parent link, which costs no second question of the tracker;
        and because the tree, not a label, is what answered, the run says so, so nobody
        takes the 0 for a batch that was checked."""
        body = "## Parent\n\n#76\n\n## Blocked by\n\n- #96\n"
        code, printed, subs, batch, ticket_graph = lint(
            77, {77: body}, [], parent=76)
        self.assertEqual(code, 0)
        self.assertIn("carries no `## Acceptance criteria`", printed)
        self.assertNotIn("is a spec", printed)
        self.assertIn("layer-label", printed)
        self.assertIn("mmw:spec", printed)
        subs.assert_not_called()
        batch.assert_not_called()
        ticket_graph.assert_called_once()

    def test_a_labelled_ticket_is_not_told_about_layer_labels(self):
        code, printed, _, _, _ = lint(
            77, {77: "## Parent\n\n#216\n"}, [], parent=216,
            labels=["mmw:ticket", "ready-for-human"])
        self.assertEqual(code, 0)
        self.assertNotIn("layer-label", printed)

    def test_a_criteria_less_issue_with_no_children_is_not_a_spec(self):
        code, printed, _, batch, ticket_graph = lint(77, {77: "## Summary\n\nx\n"}, [])
        self.assertEqual(code, 0)
        self.assertNotIn("is a spec", printed)
        batch.assert_not_called()
        ticket_graph.assert_called_once()

    def test_a_labelled_spec_attached_to_its_map_is_still_a_spec(self):
        """The layer label says which layer the issue is, so attaching the spec under
        its wayfinder map — which `docs/agents/issue-tracker.md` asks for — does not
        turn the pre-batch pass into a quiet 0 over the map's own children."""
        code, printed, _, batch, ticket_graph = lint(
            SPEC, {SPEC: SPEC_BODY, 301: CLEAN, 302: CLEAN}, [301, 302],
            parent=18, labels=["mmw:spec"])
        self.assertEqual(code, 0)
        self.assertIn("is a spec with 2 sub-issues", printed)
        self.assertIn("## #301 (OPEN)", printed)
        batch.assert_called_once_with(SPEC, [301, 302])
        ticket_graph.assert_not_called()

    def test_a_labelled_ticket_with_children_is_not_a_spec(self):
        """A `ready-for-human` ticket that opened child issues of its own carries
        `mmw:ticket`; its own children are not the batch and are not linted."""
        code, printed, _, batch, ticket_graph = lint(
            77, {77: "## Parent\n\n#216\n"}, [90, 91],
            parent=216, labels=["mmw:ticket", "ready-for-human"])
        self.assertEqual(code, 0)
        self.assertNotIn("is a spec", printed)
        batch.assert_not_called()
        ticket_graph.assert_called_once()

    def test_a_labelled_spec_with_no_batch_is_an_error_not_a_quiet_0(self):
        """The real `lint_batch_graph`, so the empty batch is the thing under test."""
        labelled = {"labels": [{"name": "mmw:spec"}], "state": "OPEN"}
        with mock.patch.object(vt, "fetch_body", return_value=SPEC_BODY), \
             mock.patch.object(vt, "fetch_ticket", return_value=labelled), \
             mock.patch.object(vt, "fetch_parent", return_value=18), \
             mock.patch.object(vt, "fetch_sub_issues", return_value=[]):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(SPEC)
        self.assertEqual(code, 1)
        self.assertIn("no-sub-issues", out.getvalue())

    def test_children_the_tracker_cannot_list_is_an_error_not_a_quiet_0(self):
        with mock.patch.object(vt, "fetch_body", return_value=SPEC_BODY), \
             mock.patch.object(vt, "fetch_ticket", return_value=LABELS), \
             mock.patch.object(vt, "fetch_parent", return_value=None), \
             mock.patch.object(vt, "fetch_sub_issues",
                               side_effect=vt.SubIssuesUnreadable("gh: Not Found")):
            with redirect_stdout(io.StringIO()) as out:
                code = vt.run_lint(SPEC)
        self.assertEqual(code, 1)
        self.assertIn("sub-issues-unreadable", out.getvalue())


if __name__ == "__main__":
    unittest.main()
