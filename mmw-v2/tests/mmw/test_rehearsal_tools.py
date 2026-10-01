"""Rehearsal boundaries against disposable tracker, runner and install state."""

import json
import os
import subprocess
import shlex
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import stand_in_agent

HERE = Path(__file__).resolve().parent


class RehearsalTools(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mmw-rehearsal-tools-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "gh.json"
        self.log = self.root / "gh.log"
        self.state.write_text(json.dumps({"repository": "sample/rehearsal", "issues": {}}))
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("MMW_", "NMEM_", "ORCA_", "HERDR_", "PASEO_"))}
        self.env.update(MMW_FAKE_GH_STATE=str(self.state), MMW_FAKE_GH_LOG=str(self.log))
        self.orca_state = self.root / "orca"
        self.env.update(MMW_FAKE_ORCA_STATE=str(self.orca_state),
                        MMW_FAKE_ORCA_LOG=str(self.root / "orca.log"))

    def orca(self, *args):
        return subprocess.run([sys.executable, str(HERE / "fake_orca.py"), *args],
                              env=self.env, capture_output=True, text=True, timeout=20)

    def start_stand_in(self):
        prompt = ("Use the mmw skill. Role worker, ticket #61, unattended: "
                  f"mmw work-a-ticket#While the product runs. Data: {self.root}/61-worker.md.")
        command = shlex.join(["exec", "env", "MMW_ROLE=worker", "MMW_TICKET=61",
                              "NMEM_SPACE=sample__rehearsal", "claude", "--dangerously-skip-permissions", prompt])
        result = self.orca("terminal", "create", "--worktree", f"path:{self.root}",
                           "--command", command, "--title", "t", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        handle = json.loads(result.stdout)["result"]["handle"]
        self.addCleanup(lambda: self.orca("terminal", "close", "--terminal", handle, "--json"))
        rows = json.loads((self.orca_state / "terminals.json").read_text())
        row = next(row for row in rows if row["handle"] == handle)
        self.assertIn("pid", row, "terminal create did not start a stand-in process")
        return prompt, handle, row

    def test_fake_orca_starts_a_stand_in_with_the_one_line_prompt(self):
        prompt, handle, row = self.start_stand_in()
        os.kill(row["pid"], 0)
        received = self.orca_state / f"{handle}.received"
        deadline = time.monotonic() + 5
        while not received.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(received.exists(), "stand-in never consumed its first input")
        self.assertEqual(received.read_text().splitlines(), [prompt])
        output = self.orca_state / f"{handle}.stdout"
        while "ACTION worker While the product runs" not in output.read_text() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertIn("ACTION worker While the product runs", output.read_text())
        self.assertEqual((self.orca_state / f"{handle}.stderr").read_text(), "")
        os.kill(row["pid"], 0)
        # Start prompts have a Data suffix; relay wakes do not. Both select the same action path.
        agent = stand_in_agent.Agent("worker", 61)
        for line, expected in (("Use the mmw skill. Role worker, ticket #61, unattended: "
                                f"mmw work-a-ticket#Claim. Data: {self.root}/61-worker.md.", "Claim"),
                               ("#61 reviewer.reported · mmw work-a-ticket#Get reviewed", "Get reviewed")):
            selected = []
            agent.step = lambda title, **kwargs: selected.append(title)
            agent.receive(line, wake=False)
            self.assertEqual(selected, [expected])

    def test_fake_orca_appends_a_delivered_line_to_the_inbox(self):
        _, handle, row = self.start_stand_in()
        os.kill(row["pid"], 0)
        line = "#61 reviewer.reported · mmw work-a-ticket#Get reviewed"
        result = self.orca("terminal", "send", "--terminal", handle, "--text", line,
                           "--enter", "--wait-submit", "30", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        receipt = json.loads(result.stdout)["result"]["send"]["prompt"]
        self.assertIn("turn_started", receipt["stages"])
        self.assertEqual((self.orca_state / f"{handle}.inbox").read_text().splitlines()[-1], line)

    def test_stand_in_refuses_a_step_it_has_no_action_for(self):
        result = subprocess.run([sys.executable, str(HERE / "stand_in_agent.py"),
                                 "--role", "worker", "--step", "No Such Step"],
                                env=self.env, capture_output=True, text=True, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NO ACTION worker No Such Step", result.stderr)

    def test_every_registered_anchor_has_an_action(self):
        scripts = HERE.parents[1] / "skills" / "mmw" / "scripts"
        locations = stand_in_agent.load("rehearsal_locations", scripts / "locations.py")
        for playbook in ("work-a-ticket", "review-a-ticket", "run-a-night", "land-one-ticket"):
            registered = set(locations.PLAYBOOK_ANCHORS[playbook])
            actions = set(stand_in_agent.ACTIONS.get(playbook, {}))
            self.assertEqual(actions, registered,
                             f"{playbook}: missing {sorted(registered - actions)}; extra {sorted(actions - registered)}")

    def test_rehearsal_builds_the_installed_clone_and_the_consuming_repository(self):
        import rehearsal
        fixture = rehearsal.Rehearsal()
        self.addCleanup(fixture.close)
        result = fixture.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        marker = fixture.home / ".mmw" / "installed-root"
        recorded = Path(marker.read_text().strip()).resolve()
        self.assertEqual(recorded, (fixture.clone / "mmw-v2").resolve())
        self.assertNotEqual(recorded, HERE.parents[1])
        self.assertTrue((fixture.scripts / "dispatch.sh").is_file())
        origin = fixture.run(["git", "remote", "get-url", "origin"])
        self.assertEqual(origin.returncode, 0, origin.stderr)
        self.assertEqual(Path(origin.stdout.strip()), fixture.origin)
        tree = fixture.gh("api", "--paginate", "--slurp",
                          f"repos/{fixture.repository}/issues/{fixture.spec}/sub_issues?per_page=100")
        self.assertEqual(tree.returncode, 0, tree.stderr)
        self.assertEqual([row["number"] for row in json.loads(tree.stdout)[0]], list(fixture.tickets))
        blockers = fixture.gh("issue", "view", str(fixture.tickets[1]), "--json", "blockedBy")
        self.assertEqual(blockers.returncode, 0, blockers.stderr)
        self.assertEqual(json.loads(blockers.stdout)["blockedBy"]["nodes"][0]["number"], fixture.tickets[0])
        committed = fixture.run(["git", "--git-dir", str(fixture.origin), "show", "project:docs/specs/rehearsal.md"])
        self.assertEqual(committed.returncode, 0, committed.stderr)
        self.assertIn(f"#{fixture.spec}", committed.stdout)
        boundary_log = fixture.root / "boundary.log"
        for program in ("nmem", "paseo", "herdr"):
            with self.subTest(program=program):
                before = boundary_log.read_text().splitlines()
                unknown = fixture.run([program, "unsupported"])
                self.assertEqual(unknown.returncode, 2, unknown.stderr)
                after = boundary_log.read_text().splitlines()
                self.assertEqual(len(after), len(before) + 1)
                self.assertEqual(after[-1], f"UNHANDLED {program} unsupported")
        prompt = ("Use the mmw skill. Role worker, ticket #61, unattended: "
                  f"mmw work-a-ticket#While the product runs. Data: {fixture.root}/61-worker.md.")
        agent = fixture.orca("terminal", "create", "--worktree", f"path:{fixture.consumer}",
                             "--command", f"exec claude '{prompt}'", "--title", "cleanup probe", "--json")
        self.assertEqual(agent.returncode, 0, agent.stderr)
        pid = json.loads(agent.stdout)["result"]["pid"]
        os.kill(pid, 0)
        root = fixture.root
        fixture.close()
        self.assertFalse(root.exists(), "rehearsal left its disposable directory")
        self.assertIn(pid, fixture.pids)
        self.assertFalse(rehearsal.process_command(pid), "rehearsal left its stand-in process")
        self.assertEqual(fixture.remaining_processes(), [])

    def gh(self, *args, input=None):
        return subprocess.run([sys.executable, str(HERE / "fake_gh.py"), *args],
                              env=self.env, input=input, capture_output=True, text=True, timeout=20)

    def test_fake_gh_refuses_an_unhandled_call_and_logs_it(self):
        for args in (("pr", "list"),
                     ("api", "-X", "PATCH", "repos/sample/rehearsal/issues/comments/5000"),
                     ("api", "-X", "PATCH", "repos/sample/rehearsal/issues/123"),
                     ("api", "repos/sample/rehearsal/issues/123/unknown")):
            with self.subTest(args=args):
                before = self.log.read_text().splitlines() if self.log.exists() else []
                result = self.gh(*args)
                self.assertEqual(result.returncode, 2, result.stderr)
                after = self.log.read_text().splitlines()
                self.assertEqual(len(after), len(before) + 1)
                self.assertEqual(after[-1], "UNHANDLED " + " ".join(args))

    def ok_gh(self, *args, input=None):
        result = self.gh(*args, input=input)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_fake_gh_round_trips_an_issue_tree_and_its_comments(self):
        spec_url = self.ok_gh("issue", "create", "--title", "Spec", "--body-file", "-",
                              "--label", "mmw:spec", input="A rehearsal spec")
        spec = int(spec_url.strip().rsplit("/", 1)[-1])
        ticket_url = self.ok_gh("issue", "create", "--title", "Ticket", "--body-file", "-",
                                "--repo", "sample/rehearsal", input="Ticket body")
        ticket = str(int(ticket_url.strip().rsplit("/", 1)[-1]))
        ident = self.ok_gh("api", f"repos/{{owner}}/{{repo}}/issues/{ticket}", "--jq", ".id").strip()
        self.ok_gh("api", "--method", "POST", f"repos/sample/rehearsal/issues/{spec}/sub_issues",
                   "-F", f"sub_issue_id={ident}")
        # Move via the actual pipeline's issue-edit call, then link back to the spec.
        other = self.ok_gh("issue", "create", "--title", "Other spec", "--body-file", "-", input="Other").strip()
        self.ok_gh("issue", "edit", ticket, "--parent", other)
        old = json.loads(self.ok_gh("api", f"repos/sample/rehearsal/issues/{spec}/sub_issues"))
        self.assertEqual(old, [])
        self.ok_gh("issue", "edit", ticket, "--parent", str(spec))
        self.ok_gh("issue", "comment", ticket, "--body", "first comment")
        first = json.loads(self.ok_gh("issue", "view", ticket, "--json", "comments"))["comments"][0]
        since = (datetime.fromisoformat(first["createdAt"].replace("Z", "+00:00"))
                 + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        comment = self.root / "comment.md"
        comment.write_text("second comment")
        self.ok_gh("issue", "comment", ticket, "--body-file", str(comment))
        self.ok_gh("issue", "edit", ticket, "--add-label", "ready")
        self.ok_gh("issue", "close", ticket, "--reason", "completed")
        kids = json.loads(self.ok_gh("api", "--paginate", "--slurp",
                                     f"repos/sample/rehearsal/issues/{spec}/sub_issues?per_page=100"))
        self.assertEqual([row["number"] for row in kids[0]], [int(ticket)])
        raw = self.ok_gh("api", "-i", f"repos/sample/rehearsal/issues/{ticket}/comments?per_page=100&since={since}")
        head, comments = raw.split("\n\n", 1)
        self.assertIn("HTTP/2 200", head)
        self.assertEqual([row["body"] for row in json.loads(comments)], ["second comment"])
        row = json.loads(self.ok_gh("issue", "view", ticket, "--json", "state,labels"))
        self.assertEqual(row, {"state": "CLOSED", "labels": [{"name": "ready"}]})
        # Exercise the production tree query, not a separate fixture projection.
        scripts = HERE.parents[1] / "skills" / "mmw" / "scripts"
        locations = stand_in_agent.load("tracker_tree_locations", scripts / "locations.py")
        tree_script = scripts.parents[1] / locations.ISSUE_TREE_PY
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " "
                                   + shlex.quote(str(HERE / "fake_gh.py")) + ' "$@"\n')
        (bin_dir / "gh").chmod(0o755)
        result = subprocess.run([sys.executable, str(tree_script), str(spec)],
                                env={**self.env, "PATH": str(bin_dir) + os.pathsep + self.env["PATH"]},
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = json.loads(result.stdout)
        self.assertEqual(tree["number"], spec)
        self.assertEqual([(child["number"], child["state"]) for child in tree["children"]],
                         [(int(ticket), "CLOSED")])
        # Small pages force the same Link/ETag protocol the relay actually reads.
        first_page = self.ok_gh("api", "-i", f"repos/sample/rehearsal/issues/{ticket}/comments?per_page=1")
        headers, rows = first_page.split("\n\n", 1)
        self.assertIn('rel="next"', headers)
        self.assertEqual([row["body"] for row in json.loads(rows)], ["first comment"])
        etag = next(line.split(": ", 1)[1] for line in headers.splitlines() if line.startswith("ETag:"))
        not_modified = self.gh("api", "-i", f"repos/sample/rehearsal/issues/{ticket}/comments?per_page=1",
                               "-H", f"If-None-Match: {etag}")
        self.assertEqual(not_modified.returncode, 1)
        self.assertIn("HTTP/2 304", not_modified.stdout)
        self.assertNotIn("UNHANDLED", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
