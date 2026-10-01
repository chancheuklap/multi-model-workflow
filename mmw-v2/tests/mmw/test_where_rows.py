"""dispatch.sh where prints the registered line for every position and runner.

Each row of WHERE_ROWS is reached through the real where command, once under each
runner's self. The expected line is composed here from that row. It is not taken from
status.py, so a formatter bug cannot hide inside the function under test.
"""

import importlib.util
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILLS = Path(__file__).resolve().parents[2] / "skills"
DISPATCH = SKILLS / "mmw" / "scripts" / "dispatch.sh"
EVENTS_PY = SKILLS / "mmw" / "scripts" / "events.py"
RUNNERS = ("orca", "paseo", "herdr")
TICKET = 61
SPEC = 76
AT = "2026-09-10T01:00:00Z"

GH = r"""#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
fixture = json.load(open(os.environ["WHERE_FIXTURE"]))
if args[:2] == ["repo", "view"]:
    print("o/r")
    raise SystemExit(0)
if args[:2] == ["issue", "view"]:
    raw = fixture["issues"][args[2]]
    print(json.dumps({
        "state": raw["state"],
        "title": raw.get("title", "fixture"),
        "body": "",
        "createdAt": "2026-09-10T01:00:00Z",
        "closedAt": None,
        "labels": [{"name": name} for name in raw.get("labels", [])],
        "assignees": [],
        "blockedBy": {"nodes": []},
        "comments": [{"body": body} for body in raw.get("comments", [])],
    }))
    raise SystemExit(0)
if args[:2] == ["api", "graphql"]:
    root = next(int(a.split("=", 1)[1]) for a in args if a.startswith("root="))
    issues = fixture["issues"]
    children = {int(k): v for k, v in fixture.get("children", {}).items()}

    def node(number, depth):
        raw = issues.get(str(number), {})
        out = {"number": number, "title": raw.get("title", "fixture"),
               "state": raw.get("state", "OPEN")}
        if depth:
            kids = children.get(number, [])
            out["subIssuesSummary"] = {"total": len(kids), "completed": 0}
            out["subIssues"] = {"nodes": [node(kid, depth - 1) for kid in kids]}
        return out

    print(json.dumps({"data": {"repository": {"issue": node(root, 2)}}}))
    raise SystemExit(0)
sys.stderr.write("unhandled gh " + " ".join(args) + "\n")
raise SystemExit(1)
"""

HERDR = r"""#!/usr/bin/env python3
import json, sys
if sys.argv[1:3] == ["agent", "list"]:
    print(json.dumps({"result": {"agents": [{"name": "me", "pane_id": "pane_me"}]}}))
    raise SystemExit(0)
raise SystemExit(1)
"""


def load_events():
    spec = importlib.util.spec_from_file_location("events_for_where_rows", EVENTS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_locations():
    spec = importlib.util.spec_from_file_location(
        "locations_for_where_rows", SKILLS / "mmw" / "scripts" / "locations.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


events = load_events()


def ev(name, line, ticket=TICKET, **fields):
    return events.build(name, ticket=ticket, line=line, at=AT, **fields)


def worker_started(runner, session="me", adopted=False, ticket=TICKET):
    fields = dict(session=session, runner=runner, machine="mac-1", host="codex",
                  model="gpt-6.1-sol", effort="high", grade="senior-worker",
                  worktree=f"/repo/.worktrees/issue-{ticket}", branch=f"issue-{ticket}",
                  base="0" * 40)
    if adopted:
        fields["adopted"] = True
    return ev("worker.started", "started", ticket=ticket, **fields)


def reviewer_started(runner, session, ticket=TICKET):
    return ev("reviewer.started", "reviewer started", ticket=ticket,
              session=session, runner=runner, machine="mac-1")


def checked(run, head, ticket=TICKET):
    return ev("ticket.checked", f"{run} run", ticket=ticket, run=run, commit=head, result="met")


def claimed(ticket=TICKET):
    return ev("ticket.claimed", f"Claimed #{ticket}", ticket=ticket)


def decided(ticket=TICKET):
    return ev("worker.decided", "decisions", ticket=ticket)


def reported(ticket=TICKET):
    return ev("reviewer.reported", "review", ticket=ticket)


def returned(ticket=TICKET):
    return ev("ticket.returned", "returned", ticket=ticket)


def passed(ticket=TICKET):
    return ev("ticket.passed", "ALL MET", ticket=ticket)


def landed(ticket=TICKET):
    return ev("ticket.landed", "landed", ticket=ticket)


def opened_spec(runner):
    return ev("spec.opened", "opened", ticket=None, spec=SPEC, runner=runner, session="me")


def closed_spec():
    return ev("spec.closed", "closed", ticket=None, spec=SPEC)


def recorded_retro():
    return ev("spec.retroed", "retro", ticket=None, spec=SPEC, result="recorded",
              retro_memory="mem-1", problem_count=0, proposals=[], evidence="complete",
              unreadable_sources=[])


def issue(state="OPEN", labels=(), comments=(), title="fixture"):
    return {"state": state, "labels": list(labels), "comments": list(comments), "title": title}


def format_line(role, number, row, roles):
    """The where line, in the form status.py documents for one registered row."""
    playbook = row.get("playbook", roles[role]["playbook"])
    pointer = f"mmw {playbook}#{row['step']}"
    if "until" in row:
        pointer += f" .. #{row['until']}"
    if "note" in row:
        pointer += f" · {row['note']}"
    return f"{row['kind']} {role} #{number} · {pointer}"


def scene(role, key, runner, head):
    """The tracker answers and watch that put this session on one where row."""
    if role in ("worker", "adopting-worker"):
        start = worker_started(runner, adopted=role == "adopting-worker")
        review = reviewer_started(runner, "review")
        own = checked("self", head)
        final = checked("reverify", head)
        steps = {
            "fresh": [start],
            "claimed": [start, claimed()],
            "checked": [start, claimed(), own],
            "decided": [start, claimed(), own, decided()],
            "waiting": [start, claimed(), own, decided(), review],
            "reported": [start, claimed(), own, decided(), review, reported()],
            "reviewed": [start, claimed(), own, decided(), review, reported(), own],
            "returned": [start, claimed(), returned()],
            "final": [start, claimed(), own, decided(), review, reported(), final],
            "closed": [start, claimed(), own, decided(), review, reported(), final, passed()],
        }
        return {"number": TICKET, "watch": None, "children": {},
                "issues": {str(TICKET): issue(comments=steps[key])}}
    if role == "reviewer":
        return {"number": TICKET, "watch": None, "children": {},
                "issues": {str(TICKET): issue(comments=[reviewer_started(runner, "me")])}}
    if role == "one-ticket-orchestrator":
        comments = {
            "fresh": [],
            "working": [worker_started(runner, session="worker")],
            "finished": [worker_started(runner, session="worker"), passed()],
        }
        return {"number": TICKET, "watch": "ticket", "children": {},
                "issues": {str(TICKET): issue(comments=comments[key])}}
    opened = opened_spec(runner)
    child = worker_started(runner, session="worker")
    finding = ev("child.opened", "finding", child=90, kind="finding")
    done = [child, passed(), landed(), finding]
    bare = [child, passed(), landed()]
    night = {
        "fresh": {"watch": None, "comments": [], "children": {}, "extra": {}},
        "opened": {"watch": "night", "comments": [opened], "children": {str(SPEC): []}, "extra": {}},
        "working": {"watch": "night", "comments": [opened], "children": {str(SPEC): [TICKET]},
                    "extra": {str(TICKET): issue(comments=[child])}},
        "findings": {"watch": "night", "comments": [opened],
                     "children": {str(SPEC): [TICKET], str(TICKET): [90]},
                     "extra": {str(TICKET): issue(state="CLOSED", comments=done),
                               "90": issue(title="finding")}},
        "closing": {"watch": "night", "comments": [opened], "children": {str(SPEC): [TICKET]},
                    "extra": {str(TICKET): issue(state="CLOSED", comments=bare)}},
        "closed": {"watch": None, "comments": [opened, closed_spec()], "children": {}, "extra": {}},
        "retroed": {"watch": None, "comments": [opened, closed_spec(), recorded_retro()],
                    "children": {}, "extra": {}},
    }
    row = night[key]
    issues = {str(SPEC): issue(labels=("mmw:spec",), comments=row["comments"], title="spec")}
    issues.update(row["extra"])
    return {"number": SPEC, "watch": row["watch"], "children": row["children"], "issues": issues}


class WhereRowsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        for name, text in (("gh", GH), ("herdr", HERDR)):
            path = self.bin / name
            path.write_text(text)
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        self.head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.roles = json.loads((SKILLS / "mmw" / "roles.json").read_text())
        self.locations = load_locations()

    def test_where_prints_the_registered_line_for_every_row_and_runner(self):
        fresh = self.locations.WHERE_ROWS["worker"]["fresh"]
        self.assertEqual(format_line("worker", TICKET, fresh, self.roles),
                         "FRESH worker #61 · mmw work-a-ticket#Claim")
        for role, rows in self.locations.WHERE_ROWS.items():
            for key, row in rows.items():
                for runner in RUNNERS:
                    with self.subTest(role=role, key=key, runner=runner):
                        built = scene(role, key, runner, self.head)
                        expected = format_line(role, built["number"], row, self.roles)
                        line = self.where(built, runner)
                        self.assertEqual(line, expected)
                        self.assertFalse(line.startswith("UNKNOWN"))

    def where(self, built, runner):
        home = tempfile.mkdtemp(dir=self.tmp.name)
        fixture = Path(home) / "fixture.json"
        fixture.write_text(json.dumps({
            "issues": built["issues"], "children": built["children"]}))
        if built["watch"]:
            number = SPEC if built["watch"] == "night" else TICKET
            path = Path(home) / "state" / "o__r" / "watches.json"
            path.parent.mkdir(parents=True)
            row = {"runner": runner, "session": "me", "kind": built["watch"]}
            row.update({"spec": number} if built["watch"] == "night" else {"tickets": [number]})
            path.write_text(json.dumps({"fixture": row}))
        env = os.environ.copy()
        for name in ("PASEO_AGENT_ID", "ORCA_TERMINAL_HANDLE", "HERDR_PANE_ID", "HERDR_ENV",
                     "TERM_PROGRAM", "MMW_EVENTS_PY", "MMW_SPEC", "MMW_TICKET", "MMW_TASK_SCOPE",
                     "MMW_KIND", "CLICOLOR_FORCE", "CLICOLOR"):
            env.pop(name, None)
        env["MMW_HOME"] = home
        env["WHERE_FIXTURE"] = str(fixture)
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        if runner == "paseo":
            env["PASEO_AGENT_ID"] = "me"
        elif runner == "orca":
            env["ORCA_TERMINAL_HANDLE"] = "me"
        else:
            env["HERDR_ENV"] = "1"
            env["HERDR_PANE_ID"] = "pane_me"
        proc = subprocess.run(
            ["bash", str(DISPATCH), "where", str(built["number"])],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        return lines[0]


if __name__ == "__main__":
    unittest.main()
