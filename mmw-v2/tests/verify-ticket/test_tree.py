"""The tree of issues under a map, a spec or a ticket, read at the size that tree is.

The largest pages are the decision: 50 specs under a map, 100 tickets under a spec, 50
children under a ticket. Read against the real repository on 2026-09-10: a list over 100
is refused per list (EXCESSIVE_PAGINATION), 100 at every layer asks for a million nodes
and is refused whole (MAX_NODE_LIMIT_EXCEEDED, limit 500,000), and 50 × 100 × 50 is
255,050 structural nodes at a cost of 51 points. Specs and tickets each add labels and
blockers capped at ten items, taking the largest map to 356,050 nodes and 152 points.

The tracker priced those queries itself, through `rateLimit { cost }`, against
agentflow-hq/agentflow on 2026-09-12: a map at the largest pages is 152 points, and the
same map read in two questions — its counts, then its tree at the size those counts give
— is 1 + 10. Both answers were byte-identical. `cost()` is that price computed from the
query, and the numbers below are what the tracker charged.
"""

import importlib.util
import json
import math
import re
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "verify-ticket" / "scripts" / "tree.py"
_spec = importlib.util.spec_from_file_location("mmw_tree_under_test", SCRIPT)
tree = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tree)


def pages(query: str) -> list[int]:
    return [int(n) for n in re.findall(r"subIssues\(first:(\d+)\)", query)]


class TheQuery(unittest.TestCase):
    def test_from_a_map_the_three_layers_are_read_at_50_100_50(self):
        self.assertEqual(pages(tree.query("map")), [50, 100, 50])

    def test_from_a_spec_and_from_a_ticket_each_layer_keeps_its_own_size(self):
        self.assertEqual(pages(tree.query("spec")), [100, 50])
        self.assertEqual(pages(tree.query("ticket")), [50])

    def test_the_whole_map_stays_under_the_trackers_node_limit(self):
        query = tree.query("map")
        nodes, width = 0, 1
        for size in pages(query):
            width *= size
            nodes += width
        for connection in re.finditer(r"(?:labels|blockedBy)\(first:(\d+)\)", query):
            ancestors = [int(size) for size in
                         re.findall(r"subIssues\(first:(\d+)\)", query[:connection.start()])]
            nodes += int(connection.group(1)) * math.prod(ancestors)
        self.assertEqual(nodes, 356050)
        self.assertLess(nodes, 500000)

    def test_labels_and_blocked_by_are_on_specs_and_tickets_not_children(self):
        query = tree.query("map")
        self.assertEqual(query.count("labels(first:10) { totalCount"), 2)
        self.assertEqual(query.count("blockedBy(first:10) { totalCount"), 2)
        child_fields = query.rsplit("subIssues(first:50)", 1)[1]
        self.assertNotIn("labels(", child_fields)
        self.assertNotIn("blockedBy(", child_fields)

    def test_every_layer_with_one_below_brings_its_count(self):
        query = tree.query("map")
        self.assertEqual(query.count("subIssuesSummary { total completed }"), 3)

    def test_a_child_has_no_layer_below_it(self):
        with self.assertRaises(ValueError):
            tree.query("child")


def answer(issue):
    return lambda args: (0, json.dumps({"data": {"repository": {"issue": issue}}}), "")


class TheAnswer(unittest.TestCase):
    def test_a_whole_tree_comes_back_with_its_counts(self):
        got = tree.read(18, "map", gh=answer({
            "number": 18, "title": "map", "state": "OPEN",
            "subIssuesSummary": {"total": 1, "completed": 0},
            "subIssues": {"nodes": [{
                "number": 76, "title": "spec", "state": "OPEN",
                "subIssuesSummary": {"total": 1, "completed": 1},
                "subIssues": {"nodes": [{
                    "number": 61, "title": "ticket", "state": "CLOSED",
                    "subIssuesSummary": {"total": 1, "completed": 0},
                    "subIssues": {"nodes": [{"number": 90, "title": "c",
                                             "state": "OPEN"}]}}]}}]}}))
        spec = got["children"][0]
        self.assertEqual((got["total"], spec["number"], spec["completed"]), (1, 76, 1))
        self.assertEqual(spec["children"][0]["children"][0]["number"], 90)

    def test_labels_and_blockers_are_normalised_for_existing_readers(self):
        got = tree.read(18, "map", gh=answer({
            "number": 18, "title": "map", "state": "OPEN",
            "subIssuesSummary": {"total": 1, "completed": 0},
            "subIssues": {"nodes": [{
                "number": 76, "title": "spec", "state": "OPEN",
                "labels": {"totalCount": 1, "nodes": [{"name": "mmw:spec"}]},
                "blockedBy": {"totalCount": 1,
                              "nodes": [{"number": 70, "state": "CLOSED"}]},
                "subIssuesSummary": {"total": 0, "completed": 0},
                "subIssues": {"nodes": []},
            }]},
        }))
        self.assertEqual(got["children"][0]["labels"], ["mmw:spec"])
        self.assertEqual(got["children"][0]["blockedBy"],
                         [{"number": 70, "state": "CLOSED"}])

    def test_metadata_capped_by_its_page_keeps_existing_readers_working(self):
        got = tree.read(18, "map", gh=answer({
            "number": 18, "title": "map", "state": "OPEN",
            "subIssuesSummary": {"total": 1, "completed": 0},
            "subIssues": {"nodes": [{
                "number": 76, "title": "spec", "state": "OPEN",
                "labels": {"totalCount": 11,
                           "nodes": [{"name": f"label-{n}"} for n in range(10)]},
                "blockedBy": {"totalCount": 11,
                              "nodes": [{"number": n, "state": "OPEN"}
                                        for n in range(10)]},
                "subIssuesSummary": {"total": 0, "completed": 0},
                "subIssues": {"nodes": []},
            }]},
        }))
        self.assertEqual(len(got["children"][0]["labels"]), 10)
        self.assertEqual(len(got["children"][0]["blockedBy"]), 10)

    def test_a_layer_cut_short_by_its_page_is_a_refusal_not_a_smaller_tree(self):
        with self.assertRaises(tree.TreeUnreadable) as caught:
            tree.read(76, "spec", gh=answer({
                "number": 76, "title": "spec", "state": "OPEN",
                "subIssuesSummary": {"total": 101, "completed": 0},
                "subIssues": {"nodes": [{"number": n, "title": "t", "state": "OPEN",
                                         "subIssuesSummary": {"total": 0, "completed": 0},
                                         "subIssues": {"nodes": []}}
                                        for n in range(100)]}}))
        self.assertIn("101 sub-issues and 100 came back", str(caught.exception))

    def test_the_query_goes_out_with_the_repository_placeholders(self):
        asked = []

        def gh(args):
            asked.append(args)
            return answer({"number": 76, "title": "s", "state": "OPEN",
                           "subIssuesSummary": {"total": 0, "completed": 0},
                           "subIssues": {"nodes": []}})(args)

        tree.read(76, "spec", gh=gh)
        self.assertEqual(len(asked), 1)
        self.assertEqual(asked[0][:6], ["api", "graphql", "-F", "o={owner}", "-F", "n={repo}"])
        self.assertIn("root=76", asked[0])


class ThePrice(unittest.TestCase):
    """What the tracker charges: every list counted as though it came back full, added up
    and divided by a hundred. The three numbers below are what it charged when asked."""

    def test_the_largest_pages_cost_what_the_tracker_charged_for_them(self):
        self.assertEqual(tree.cost("map"), 152)
        self.assertEqual(tree.cost("spec"), 3)
        self.assertEqual(tree.cost("ticket"), 1)

    def test_a_tree_read_at_its_own_size_costs_a_fraction_of_that(self):
        self.assertEqual(tree.cost("map", {"spec": 24, "ticket": 13, "child": 1}), 10)

    def test_only_a_read_over_the_sizing_price_is_worth_a_second_question(self):
        self.assertGreater(tree.cost("map"), tree.SIZING_WORTH)
        self.assertLessEqual(tree.cost("spec"), tree.SIZING_WORTH)
        self.assertLessEqual(tree.cost("ticket"), tree.SIZING_WORTH)


class TheSizingQuery(unittest.TestCase):
    def test_it_enumerates_every_layer_above_the_last_and_no_further(self):
        self.assertEqual(pages(tree.sizing_query("map")), [50, 100])
        self.assertEqual(pages(tree.sizing_query("spec")), [100])

    def test_it_carries_counts_and_nothing_else(self):
        query = tree.sizing_query("map")
        self.assertEqual(query.count("subIssuesSummary { total }"), 3)
        for field in ("title", "labels(", "blockedBy(", "completed"):
            self.assertNotIn(field, query)

    def test_the_page_of_a_layer_is_the_largest_count_above_it(self):
        counts = {"subIssuesSummary": {"total": 2}, "subIssues": {"nodes": [
            {"subIssuesSummary": {"total": 3}, "subIssues": {"nodes": [
                {"subIssuesSummary": {"total": 7}}]}},
            {"subIssuesSummary": {"total": 1}, "subIssues": {"nodes": [
                {"subIssuesSummary": {"total": 4}}]}}]}}
        self.assertEqual(tree._sizes(counts, ["spec", "ticket", "child"]),
                         {"spec": 2, "ticket": 3, "child": 7})

    def test_a_count_the_tracker_did_not_give_leaves_that_layer_at_its_largest(self):
        counts = {"subIssuesSummary": {"total": 2},
                  "subIssues": {"nodes": [{"subIssues": {"nodes": []}}]}}
        self.assertEqual(tree._sizes(counts, ["spec", "ticket", "child"]), {"spec": 2})
        self.assertEqual(pages(tree.query("map", {"spec": 2})), [2, 100, 50])

    def test_a_size_is_held_between_one_and_the_layers_largest_page(self):
        self.assertEqual(pages(tree.query("map", {"spec": 0, "ticket": 900, "child": 3})),
                         [1, 100, 3])


def two_answers(counts, tree_payload, *rest):
    """A `gh` that answers each call with the next payload, and keeps the queries asked."""
    payloads = [counts, tree_payload, *rest]
    asked = []

    def gh(args):
        asked.append(next(value for value in args if value.startswith("query="))[len("query="):])
        payload = payloads[min(len(asked) - 1, len(payloads) - 1)]
        return 0, json.dumps({"data": {"repository": {"issue": payload}}}), ""

    return gh, asked


def spec_node(number, tickets):
    return {"number": number, "title": "spec", "state": "OPEN",
            "subIssuesSummary": {"total": len(tickets), "completed": 0},
            "subIssues": {"nodes": [
                {"number": n, "title": "ticket", "state": "OPEN",
                 "subIssuesSummary": {"total": 0, "completed": 0},
                 "subIssues": {"nodes": []}} for n in tickets]}}


class TwoQuestions(unittest.TestCase):
    """A map is read twice: its counts, then its tree at the size those counts give. A
    spec is read once — its largest pages already cost less than asking twice."""

    def test_a_map_is_asked_for_its_counts_and_then_at_that_size(self):
        counts = {"subIssuesSummary": {"total": 2}, "subIssues": {"nodes": [
            {"subIssuesSummary": {"total": 3}, "subIssues": {"nodes": [
                {"subIssuesSummary": {"total": 0}}] * 3}},
            {"subIssuesSummary": {"total": 1}, "subIssues": {"nodes": [
                {"subIssuesSummary": {"total": 0}}]}}]}}
        whole = {"number": 18, "title": "map", "state": "OPEN",
                 "subIssuesSummary": {"total": 2, "completed": 0},
                 "subIssues": {"nodes": [spec_node(76, [1, 2, 3]), spec_node(77, [4])]}}
        gh, asked = two_answers(counts, whole)

        got = tree.read(18, "map", gh=gh)
        self.assertEqual(len(asked), 2)
        self.assertEqual(pages(asked[0]), [50, 100])
        self.assertEqual(pages(asked[1]), [2, 3, 1])
        self.assertEqual([spec["number"] for spec in got["children"]], [76, 77])

    def test_a_spec_is_asked_once_at_its_largest_pages(self):
        whole = {"number": 76, "title": "spec", "state": "OPEN",
                 "subIssuesSummary": {"total": 0, "completed": 0},
                 "subIssues": {"nodes": []}}
        gh, asked = two_answers(whole, whole)

        tree.read(76, "spec", gh=gh)
        self.assertEqual(len(asked), 1)
        self.assertEqual(pages(asked[0]), [100, 50])

    def test_a_tree_that_grew_between_the_two_questions_is_read_at_the_largest_pages(self):
        counts = {"subIssuesSummary": {"total": 1},
                  "subIssues": {"nodes": [{"subIssuesSummary": {"total": 0},
                                           "subIssues": {"nodes": []}}]}}
        grown = {"number": 18, "title": "map", "state": "OPEN",
                 "subIssuesSummary": {"total": 2, "completed": 0},
                 "subIssues": {"nodes": [spec_node(76, [])]}}
        whole = {"number": 18, "title": "map", "state": "OPEN",
                 "subIssuesSummary": {"total": 2, "completed": 0},
                 "subIssues": {"nodes": [spec_node(76, []), spec_node(77, [])]}}
        gh, asked = two_answers(counts, grown, whole)

        got = tree.read(18, "map", gh=gh)
        self.assertEqual(len(asked), 3)
        self.assertEqual(pages(asked[2]), [50, 100, 50])
        self.assertEqual([spec["number"] for spec in got["children"]], [76, 77])

    def test_a_tree_still_short_at_the_largest_pages_is_a_refusal(self):
        counts = {"subIssuesSummary": {"total": 1},
                  "subIssues": {"nodes": [{"subIssuesSummary": {"total": 0},
                                           "subIssues": {"nodes": []}}]}}
        short = {"number": 18, "title": "map", "state": "OPEN",
                 "subIssuesSummary": {"total": 2, "completed": 0},
                 "subIssues": {"nodes": [spec_node(76, [])]}}
        gh, asked = two_answers(counts, short, short)

        with self.assertRaises(tree.TreeUnreadable) as caught:
            tree.read(18, "map", gh=gh)
        self.assertIn("2 sub-issues and 1 came back", str(caught.exception))
        self.assertEqual(len(asked), 3)

    def test_counts_that_cannot_be_read_are_a_refusal_not_a_second_question(self):
        def gh(args):
            return 1, "", "gh: Could not resolve to a Repository\n"

        with self.assertRaises(tree.TreeUnreadable) as caught:
            tree.read(18, "map", gh=gh)
        self.assertIn("Could not resolve", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
