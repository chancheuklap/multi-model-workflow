from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "results" / "test_results.py"
spec = importlib.util.spec_from_file_location("route_result_fixtures", path)
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class ChildRoutes(unittest.TestCase):
    setUp = fixtures.TicketResults.setUp
    git = fixtures.TicketResults.git
    save = fixtures.TicketResults.save
    reload = fixtures.TicketResults.reload
    add_event = fixtures.TicketResults.add_event
    run_tool = fixtures.TicketResults.run_tool
    assert_ok = fixtures.TicketResults.assert_ok

    def child(self, number=80, *, spec=60, parent=61):
        self.state["issues"][str(number)] = {
            "number": number, "state": "OPEN", "stateReason": None,
            "labels": [{"name": "mmw:child"}, {"name": "needs-triage"}],
            "parent": {"number": parent} if parent else None, "comments": [], "assignees": [],
            "body": "A follow-up finding", "blockedBy": {"nodes": [{"number": 77, "state": "OPEN"}]},
        }
        self.state["issues"]["61"]["comments"].append({"id": self.state["next_comment"],
            "body": fixtures.events.build("child.opened", ticket=61, spec=spec,
                                           line="Opened finding", child=number, kind="finding")})
        self.state["next_comment"] += 1
        self.save()
        return number

    def route(self, child=80, target=80):
        return self.run_tool("--route", child, "became-ticket", "--became", target,
                             "--report", self.report)

    def test_child_becomes_a_native_ticket_without_losing_its_existing_dependencies(self):
        self.child()
        self.assert_ok(self.route())
        original = self.reload()
        child = self.state["issues"]["80"]
        self.assertEqual((child["state"], child["parent"]), ("OPEN", {"number": 60}))
        self.assertEqual({label["name"] for label in child["labels"]}, {"mmw:ticket", "needs-triage"})
        self.assertEqual(child["blockedBy"]["nodes"], [{"number": 77, "state": "OPEN"}])
        route = fixtures.events.fold(original["comments"])["children"]["80"]
        self.assertEqual((route["resolution"], route["ticket"], route["spec"]), ("became-ticket", 80, 60))
        self.assertIn(self.report.read_text().strip(), original["comments"][-1]["body"])
        mutations = list(self.state["mutations"])
        self.assert_ok(self.route())
        self.reload()
        self.assertEqual(self.state["mutations"], mutations)

    def test_another_target_is_reclassified_and_the_original_child_closes_as_duplicate(self):
        self.child()
        self.state["issues"]["81"] = {**self.state["issues"]["80"], "number": 81,
                                        "labels": [{"name": "mmw:problem"}], "parent": {"number": 99}}
        self.save()
        self.assert_ok(self.route(target=81))
        self.reload()
        self.assertEqual(self.state["issues"]["81"]["parent"], {"number": 60})
        self.assertEqual(self.state["issues"]["81"]["labels"], [{"name": "mmw:ticket"}])
        self.assertEqual((self.state["issues"]["80"]["state"], self.state["issues"]["80"]["duplicateOf"]),
                         ("CLOSED", 81))

    def test_standalone_child_loses_its_parent_when_it_becomes_a_ticket(self):
        self.state["issues"]["61"]["parent"] = None
        self.child(spec=None)
        self.assert_ok(self.route())
        self.reload()
        self.assertIsNone(self.state["issues"]["80"]["parent"])
        self.assertIsNone(fixtures.events.fold(self.state["issues"]["61"]["comments"])["children"]["80"]["spec"])

    def test_standalone_duplicate_target_keeps_its_parent_and_becomes_a_ticket(self):
        self.state["issues"]["61"]["parent"] = None
        self.child(spec=None)
        self.state["issues"]["81"] = {**self.state["issues"]["80"], "number": 81,
                                        "labels": [{"name": "mmw:problem"}], "parent": {"number": 99}}
        self.save()
        self.assert_ok(self.route(target=81))
        self.reload()
        self.assertEqual(self.state["issues"]["81"]["parent"], {"number": 99})
        self.assertEqual(self.state["issues"]["81"]["labels"], [{"name": "mmw:ticket"}])
        self.assertEqual(self.state["issues"]["80"]["duplicateOf"], 81)

    def test_conversion_retry_after_move_preserves_the_spec_recorded_when_child_opened(self):
        self.child()
        self.state["issues"]["61"]["parent"] = {"number": 99}
        self.state["fail_comment"] = 1
        self.save()
        self.assertEqual(self.route().returncode, 1)
        self.reload()
        self.assertEqual(self.state["issues"]["80"]["parent"], {"number": 60})
        self.assert_ok(self.route())
        original = self.reload()
        last = fixtures.events.newest(original["comments"], "child.closed")
        self.assertEqual(last["payload"]["spec"], 60)
        self.assertEqual(self.state["mutations"].count("edit"), 1)

    def test_duplicate_close_failure_can_be_retried_without_duplicating_the_route(self):
        self.child()
        self.state["issues"]["81"] = {**self.state["issues"]["80"], "number": 81}
        self.state["fail_close"] = 1
        self.save()
        self.assertEqual(self.route(target=81).returncode, 1)
        self.reload()
        self.assertEqual(self.state["issues"]["81"]["parent"], {"number": 60})
        self.assertEqual(self.state["issues"]["80"]["state"], "OPEN")
        self.assert_ok(self.route(target=81))
        self.reload()
        self.assertEqual(self.state["mutations"].count("close"), 1)

    def test_maps_specs_and_incomplete_origin_events_are_refused_before_writes(self):
        for kind in ("mmw:map", "mmw:spec"):
            with self.subTest(kind=kind):
                self.child()
                self.state["issues"]["81"] = {**self.state["issues"]["80"], "number": 81,
                                                "labels": [{"name": kind}]}
                self.save()
                self.assertEqual(self.route(target=81).returncode, 2)
                self.reload()
                self.assertEqual(self.state["mutations"], [])
        self.child(spec=None)
        self.assertEqual(self.route().returncode, 2)
        self.reload()
        self.assertEqual(self.state["mutations"], [])

    def test_conflicting_target_or_report_cannot_replace_a_recorded_route(self):
        self.child()
        self.assert_ok(self.route())
        mutations = list(self.reload()["comments"])
        self.assertEqual(self.route(target=81).returncode, 2)
        self.report.write_text("A different resolution report\n")
        self.assertEqual(self.route().returncode, 2)
        self.assertEqual(self.reload()["comments"], mutations)

    def test_missing_target_or_origin_record_cannot_make_tracker_changes(self):
        self.child()
        self.assertEqual(self.run_tool("--route", "80", "became-ticket", "--report", self.report).returncode, 2)
        self.assertEqual(self.route(child=99).returncode, 2)
        self.reload()
        self.assertEqual(self.state["mutations"], [])
