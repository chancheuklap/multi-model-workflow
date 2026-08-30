"""The ticket graph: cycles, dangling references, and which tickets start first.

`validate_dag` and `compute_levels` are grok-bundled's
`execute-plan/scripts/validate-plan.py` L145-280 with one change of shape: an id is
an issue number and dependencies come from the tracker's blocking links. The cases
below are the ones that file's `_detect_cycles` and `compute_levels` distinguish — the
two-node cycle Kahn's algorithm cannot drain, the longer cycle `_trace_cycle` walks
back to a path, and the diamond where a level is the longest path, not the shortest.

Every edge has two accounts on a real ticket: the blocking link the tracker records,
which is what the graph is built from, and the `## Blocked by` section a person reads.
`lint_graph` below writes both from one description so they agree, and takes `stated`
to make them disagree.
"""

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tests._load import SCRIPT, load

vt = load()


def entries(**graph):
    """`entries(a61=[], a62=[61])` reads as `{61: [], 62: [61]}` without quoting keys."""
    return [{"id": int(name[1:]), "dependencies": deps} for name, deps in graph.items()]


def body(parent=76, blockers=("None (can start immediately)",)):
    lines = ["## Parent", "", f"#{parent}, Implementation Decisions section 1", "",
             "## Blocked by", ""]
    lines += [f"- {b}" for b in blockers]
    return "\n".join(lines) + "\n"


def lint_graph(ticket=77, spec=76, batch=(), links=None, stated=None):
    """Run the graph half of --lint over a made-up batch; return (exit code, output).

    `links` is `{ticket: [blockers]}`, the blocking links the tracker records. Each
    ticket's `## Blocked by` section is written from the same numbers unless `stated`
    names it, which is how the two accounts of an edge are made to disagree.
    """
    links = dict(links or {})
    stated = dict(stated or {})

    def refs(numbers):
        return tuple(f"#{n}" for n in numbers) or ("None (can start immediately)",)

    with mock.patch.object(vt, "fetch_sub_issues", return_value=list(batch)), \
         mock.patch.object(vt, "fetch_blocked_by",
                           side_effect=lambda n: list(links.get(n, []))), \
         mock.patch.object(vt, "fetch_body",
                           side_effect=lambda n: body(
                               blockers=refs(stated.get(n, links.get(n, []))))):
        with redirect_stdout(io.StringIO()) as out:
            code = vt.lint_ticket_graph(ticket, body(parent=spec))
    return code, out.getvalue()


class TestValidateDag(unittest.TestCase):
    def test_a_clean_chain_reports_nothing(self):
        self.assertEqual(vt.validate_dag(entries(a61=[], a62=[61], a63=[62])), [])

    def test_two_tickets_blocking_each_other_are_a_cycle(self):
        errors = vt.validate_dag(entries(a61=[62], a62=[61]))
        self.assertEqual(len(errors), 1)
        self.assertIn("cycle", errors[0])
        self.assertIn("#61", errors[0])
        self.assertIn("#62", errors[0])

    def test_a_longer_cycle_is_reported_as_a_path(self):
        errors = vt.validate_dag(entries(a61=[63], a62=[61], a63=[62]))
        self.assertEqual(len(errors), 1)
        self.assertRegex(errors[0], r"cycle detected: (#\d+ -> ){2,}#\d+")

    def test_a_dependency_outside_the_batch_is_dangling(self):
        errors = vt.validate_dag(entries(a61=[], a62=[999]))
        self.assertEqual(len(errors), 1)
        self.assertIn("dangling", errors[0])
        self.assertIn("#999", errors[0])

    def test_a_dangling_reference_is_reported_instead_of_a_cycle(self):
        # Kahn's algorithm cannot tell the two apart, so references are checked first.
        errors = vt.validate_dag(entries(a61=[999], a62=[61]))
        self.assertTrue(all("cycle" not in e for e in errors))

    def test_the_same_ticket_twice_is_a_duplicate(self):
        errors = vt.validate_dag([{"id": 61, "dependencies": []},
                                  {"id": 61, "dependencies": []}])
        self.assertIn("duplicate", errors[0])
        self.assertTrue(errors[0].endswith("  [duplicate-ticket]"), errors[0])


class TestComputeLevels(unittest.TestCase):
    def test_a_ticket_nothing_blocks_starts_at_level_zero(self):
        levels = vt.compute_levels(entries(a61=[], a62=[61]))
        self.assertEqual(levels, {61: 0, 62: 1})

    def test_a_level_is_the_longest_path_not_the_shortest(self):
        # 64 waits for 63, which waits for 61 — so 64 is level 3 even though 61
        # would also let it start at level 1.
        levels = vt.compute_levels(entries(a61=[], a62=[61], a63=[62], a64=[61, 63]))
        self.assertEqual(levels[64], 3)

    def test_independent_tickets_share_a_level(self):
        levels = vt.compute_levels(entries(a61=[], a62=[], a63=[61, 62]))
        self.assertEqual(levels, {61: 0, 62: 0, 63: 1})


class TestLintTicketGraph(unittest.TestCase):
    def test_a_cycle_is_printed_and_exits_one(self):
        code, out = lint_graph(batch=(61, 62), links={61: [62], 62: [61]})
        self.assertEqual(code, 1)
        self.assertIn("cycle", out)
        self.assertTrue(out.startswith("  ERROR "), out)
        self.assertIn("  [cycle]", out)

    def test_a_dangling_reference_is_printed_and_exits_one(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: [999]})
        self.assertEqual(code, 1)
        self.assertIn("dangling", out)
        self.assertTrue(out.startswith("  ERROR "), out)
        self.assertIn("  [dangling]", out)

    def test_a_duplicate_ticket_is_printed_and_exits_one(self):
        code, out = lint_graph(batch=(61, 61), links={61: []})
        self.assertEqual(code, 1)
        self.assertEqual(out.strip(), "ERROR duplicate ticket: #61  [duplicate-ticket]")

    def test_a_clean_batch_prints_its_start_levels(self):
        code, out = lint_graph(batch=(61, 62, 63), links={61: [], 62: [61], 63: [61]})
        self.assertEqual(code, 0)
        self.assertIn("level 0: #61", out)
        self.assertIn("level 1: #62, #63", out)

    def test_the_graph_is_built_from_the_links_not_the_section(self):
        """A cycle the tracker records is a cycle even where no `## Blocked by` says so."""
        code, out = lint_graph(batch=(61, 62), links={61: [62], 62: [61]},
                               stated={61: [], 62: []})
        self.assertEqual(code, 1)
        self.assertIn("  [cycle]", out)

    def test_a_section_edge_the_tracker_does_not_link_is_not_in_the_graph(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: []},
                               stated={62: [61]})
        self.assertEqual(code, 0)
        self.assertIn("level 0: #61, #62", out)

    def test_a_ticket_with_no_parent_section_checks_nothing(self):
        with mock.patch.object(vt, "fetch_sub_issues") as fetch:
            with redirect_stdout(io.StringIO()) as out:
                code = vt.lint_ticket_graph(77, "## What to build\n\nsomething\n")
        self.assertEqual(code, 0)
        self.assertIn("no `## Parent` section", out.getvalue())
        fetch.assert_not_called()

    def test_a_spec_with_no_sub_issues_is_an_error(self):
        """The graph is read off GitHub's sub-issue links, so a spec with none is a batch
        nothing can check — silence there would read as a batch that passed."""
        code, out = lint_graph(batch=())
        self.assertEqual(code, 1)
        self.assertIn("#76 has no sub-issues", out)
        self.assertTrue(out.startswith("  ERROR "), out)
        self.assertIn("  [no-sub-issues]", out)


class TestBlockedByMismatch(unittest.TestCase):
    """The `## Blocked by` section is the copy; the tracker's links are the graph.

    A number in one and not the other is two accounts of the same edge disagreeing, and
    the reader cannot tell which one the batch was planned around. It is a WARN, not an
    ERROR: the graph itself is still checkable, and which side is wrong is a judgement.
    """

    def warnings(self, out):
        return [l for l in out.splitlines() if "[blocked-by-mismatch]" in l]

    def test_two_accounts_that_agree_warn_about_nothing(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: [61]})
        self.assertEqual(code, 0)
        self.assertEqual(self.warnings(out), [])

    def test_none_in_the_section_and_no_link_agree(self):
        code, out = lint_graph(batch=(61,), links={61: []})
        self.assertEqual(code, 0)
        self.assertEqual(self.warnings(out), [])

    def test_a_number_only_the_section_names_is_warned_about(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: []},
                               stated={62: [61]})
        line = self.warnings(out)[0]
        self.assertTrue(line.startswith("  WARN  #62: "), line)
        self.assertIn("`## Blocked by` names #61", line)
        self.assertIn("the tracker does not link", line)
        self.assertTrue(line.endswith("  [blocked-by-mismatch]"), line)

    def test_a_number_only_the_tracker_links_is_warned_about(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: [61]},
                               stated={62: []})
        line = self.warnings(out)[0]
        self.assertIn("the tracker links #61", line)
        self.assertIn("`## Blocked by` does not name", line)

    def test_both_sides_are_named_when_each_has_one_the_other_lacks(self):
        code, out = lint_graph(batch=(61, 62, 63), links={61: [], 62: [], 63: [61]},
                               stated={63: [62]})
        line = self.warnings(out)[0]
        self.assertIn("`## Blocked by` names #62", line)
        self.assertIn("the tracker links #61", line)

    def test_the_mismatch_alone_does_not_fail_the_run(self):
        code, out = lint_graph(batch=(61, 62), links={61: [], 62: []}, stated={62: [61]})
        self.assertEqual(code, 0)
        self.assertEqual(len(self.warnings(out)), 1)


class TestBlockedBy(unittest.TestCase):
    def test_none_reads_as_no_blockers(self):
        self.assertEqual(vt.blocked_by(body()), [])

    def test_each_referenced_ticket_is_a_blocker(self):
        self.assertEqual(vt.blocked_by(body(blockers=("#61", "#62"))), [61, 62])

    def test_the_parent_spec_is_read_off_the_parent_section(self):
        self.assertEqual(vt.parent_spec(body(parent=60)), 60)



class TestBorrowedFromUpstream(unittest.TestCase):
    """The four functions are grok-bundled's, function for function.

    What may differ: the signature (type annotations), the docstring, and any line
    carrying a message — those name issues rather than `pr-<n>` entries. What may not:
    the control flow. Strip the docstrings and every line with a string literal in it,
    and the two files have to read identically.
    """

    UPSTREAM = (SCRIPT.parents[4]
                / "docs/research/code-landing-refs/grok-bundled/execute-plan/scripts/validate-plan.py")
    # The three that carry no message at all: their lines have to match exactly.
    PURE = ("_detect_cycles", "_trace_cycle", "compute_levels")
    # `validate_dag` is where the shape of an entry shows: upstream spends four lines
    # turning `pr-3` back into `PR 3` for its message, so it is checked by structure.
    SHAPED = "validate_dag"

    @staticmethod
    def logic(path, name):
        """A function's lines with the signature, docstring, comments and messages gone."""
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith(f"def {name}("))
        body, in_doc = [], False
        for line in lines[start + 1:]:
            if line.startswith("def ") or line.startswith("# ---"):
                break
            stripped = line.strip()
            if stripped.startswith('"""'):
                in_doc = not (in_doc or stripped.count('"""') == 2)
                continue
            if in_doc or not stripped or stripped.startswith("#"):
                continue
            if '"' in stripped or "'" in stripped:
                continue
            body.append(stripped)
        return body

    def test_the_upstream_file_is_where_the_ticket_says(self):
        self.assertTrue(self.UPSTREAM.is_file(), self.UPSTREAM)

    def test_the_control_flow_is_identical_line_for_line(self):
        for name in self.PURE:
            with self.subTest(function=name):
                theirs = self.logic(self.UPSTREAM, name)
                ours = self.logic(SCRIPT, name)
                self.assertTrue(theirs, f"{name} not found upstream")
                self.assertEqual(theirs, ours)

    def test_validate_dag_keeps_the_same_three_passes_in_the_same_order(self):
        ours = self.source(SCRIPT, self.SHAPED)
        theirs = self.source(self.UPSTREAM, self.SHAPED)
        for step in ("seen = set()", "for entry in entries:", 'seen.add(entry["id"])',
                     'for dep in entry["dependencies"]:', "if dep not in seen:",
                     "if not errors:", "errors.extend(_detect_cycles(entries))",
                     "return errors"):
            with self.subTest(step=step):
                self.assertIn(step, theirs, f"upstream lost {step}")
                self.assertIn(step, ours, f"ours lost {step}")
        # Cycles are looked for only once every reference resolves — Kahn's algorithm
        # cannot tell a cycle from a dangling id, so the order of the two is the point.
        for text in (theirs, ours):
            self.assertLess(text.index("if dep not in seen:"), text.index("if not errors:"))

    @staticmethod
    def source(path, name):
        """A function's own lines, verbatim."""
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next(i for i, l in enumerate(lines) if l.startswith(f"def {name}("))
        out = []
        for line in lines[start:]:
            if out and (line.startswith("def ") or line.startswith("# ---")):
                break
            out.append(line)
        return "\n".join(out)

    def test_what_differs_is_only_the_shape_of_an_entry(self):
        # Upstream translates `pr-3` back into `PR 3` for its messages; an issue number
        # needs no translation, and that is the whole of the eight-line difference.
        theirs = self.source(self.UPSTREAM, "validate_dag")
        ours = self.source(SCRIPT, "validate_dag")
        self.assertIn('replace("pr-", "PR ", 1)', theirs)
        self.assertNotIn("pr-", ours)
        self.assertIn("#{entry['id']}", ours)

if __name__ == "__main__":
    unittest.main()
