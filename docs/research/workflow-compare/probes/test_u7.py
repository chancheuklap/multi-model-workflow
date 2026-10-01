#!/usr/bin/env python3
"""Isolated U-7 checks; no host or installer processes."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import check_u7
import run_u7
import json
import contextlib
import io
import os
import subprocess
import sys


class ResultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "results.md"
        self.rows = check_u7.read_sentences()
        self.after = "a" * 40
        self.lines = ["# U-7 measurements", ""]
        for row in self.rows:
            for host in check_u7.HOSTS:
                for phase in check_u7.PHASES:
                    expected = row.expected(phase)
                    skill, _, playbook = expected.partition(":")
                    evidence = (f"skills={skill} playbooks={playbook or 'none'}; "
                                f"tool-calls=1; expected={expected}; exit=0")
                    commit = check_u7.BEFORE if phase == "before" else self.after
                    self.lines.append(f"U-7 {row.id} {host} {phase} PASS {host}=test "
                                      f"{commit} 2026-10-01 : {evidence}")
        self.lines.extend(f"CHECKSUM {phase} {name} {'b' * 64}"
                          for phase in check_u7.PHASES for name in check_u7.CONFIG_PATHS)

    def checked(self, lines=None):
        self.path.write_text("\n".join(self.lines if lines is None else lines) + "\n")
        with patch.object(check_u7, "has_playbook", return_value=True):
            return check_u7.check(self.path)

    def test_complete_consistent_results(self):
        self.assertEqual([row.id for row in self.rows], [f"S{i:02}" for i in range(1, 12)])
        self.assertEqual(self.checked(), [])

    def test_missing_cell(self):
        errors = self.checked([line for line in self.lines if not line.startswith("U-7 S03 grok after ")])
        self.assertTrue(any("S03 grok after" in error for error in errors))

    def test_contradictory_pass(self):
        lines = [line.replace("playbooks=write-a-spec-and-tickets", "playbooks=prototype")
                 if line.startswith("U-7 S01 claude after ") else line for line in self.lines]
        self.assertTrue(any("contradicts" in error for error in self.checked(lines)))

    def test_unknown_status(self):
        self.assertTrue(any("malformed cell" in error for error in
                            self.checked([line.replace(" PASS ", " UNKNOWN ", 1) for line in self.lines])))

    def test_wrong_before_commit(self):
        self.assertTrue(any("before commit is not" in error for error in
                            self.checked([line.replace(check_u7.BEFORE, "c" * 40) for line in self.lines])))

    def test_changed_checksum(self):
        self.assertTrue(any("~/.agents/skills: before/after checksums differ" in error for error in
                            self.checked([line.replace("b" * 64, "c" * 64)
                                          if line.startswith("CHECKSUM after ~/.agents/skills ") else line
                                          for line in self.lines])))

    def test_missing_after_playbook(self):
        self.path.write_text("\n".join(self.lines) + "\n")
        with patch.object(check_u7, "has_playbook", return_value=False):
            self.assertTrue(any("lacks playbooks/" in error for error in check_u7.check(self.path)))

    def test_report_distinguishes_complete_records_from_unverified_routing(self):
        lines = [line.replace(" PASS ", " NEEDS-USER-CONFIG ").split(" : ")[0] + " : catalog blocked"
                 if line.startswith("U-7 ") else line for line in self.lines]
        self.path.write_text("\n".join(lines) + "\n")
        output = io.StringIO()
        with patch.object(check_u7, "has_playbook", return_value=True), contextlib.redirect_stdout(output):
            self.assertEqual(check_u7.report(self.path), 0)
        self.assertIn("routed 0/66; NEEDS-USER-CONFIG 66", output.getvalue())

    def test_empty_results_are_not_a_measurement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text("# U-7 measurements\n")
            self.assertTrue(check_u7.check(path))


class EventTests(unittest.TestCase):
    def parse(self, host, records):
        return run_u7.parse_events(host, "\n".join(json.dumps(r) for r in records),
                                   Path("/scratch/u7"), {"mmw", "dispatch", "advisor"})

    def test_claude_tools_not_reply(self):
        records = [{"type": "assistant", "message": {"content": [
            {"type": "text", "text": "LOADED: dispatch"},
            {"type": "tool_use", "id": "1", "name": "Skill", "input": {"skill": "mmw"}},
            {"type": "tool_use", "id": "2", "name": "Read", "input": {
                "file_path": ".claude/skills/mmw/playbooks/prototype.md"}}]}}]
        parsed = self.parse("claude", records)
        self.assertEqual(parsed["skills"], ["mmw"])
        self.assertEqual(parsed["playbooks"], ["prototype"])
        self.assertEqual(parsed["tool_calls"], 2)

    def test_codex_tools_not_output(self):
        item = {"id": "1", "type": "command_execution",
                "command": "cat .agents/skills/advisor/references/consulting.md",
                "aggregated_output": ".agents/skills/dispatch/SKILL.md"}
        parsed = self.parse("codex", [{"type": "item.started", "item": item},
                                     {"type": "item.completed", "item": item},
                                     {"type": "item.completed", "item": {
                                         "type": "agent_message", "text": "LOADED: dispatch"}}])
        self.assertEqual(parsed["skills"], ["advisor"])
        self.assertEqual(parsed["tool_calls"], 1)

    def test_grok_tools_not_reply(self):
        records = [{"sessionUpdate": "tool_call", "toolCallId": "1", "title": "read_file",
                    "rawInput": {"path": ".agents/skills/mmw/SKILL.md"}},
                   {"sessionUpdate": "tool_call_update", "toolCallId": "1", "title": "read_file",
                    "locations": [{"path": "/scratch/u7/repo/.agents/skills/mmw/playbooks/prototype.md"}]},
                   {"sessionUpdate": "agent_message_chunk", "content": {"text": "LOADED: dispatch"}}]
        parsed = self.parse("grok", records)
        self.assertEqual(parsed["skills"], ["mmw"])
        self.assertEqual(parsed["playbooks"], ["prototype"])
        self.assertEqual(parsed["tool_calls"], 1)

    def test_user_and_checkout_paths_are_leaks(self):
        for filename in ("~/.agents/skills/dispatch/SKILL.md",
                         "$HOME/.claude/skills/dispatch/SKILL.md",
                         "/installed/mmw-v2/skills/dispatch/references/night.md",
                         "~/.mmw/skill-copies/dispatch/SKILL.md",
                         "~/.codex/skills/dispatch/SKILL.md"):
            with self.subTest(filename=filename):
                parsed = self.parse("codex", [{"type": "item.completed", "item": {
                    "type": "command_execution", "id": "1", "command": f"cat {filename}"}}])
                self.assertEqual(parsed["skills"], [])
                self.assertEqual(len(parsed["leaks"]), 1)


    def test_claude_skill_result_exposes_user_level_provenance(self):
        records = [{"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "1", "name": "Skill", "input": {"skill": "dispatch"}}]}},
                   {"type": "user", "message": {"content": [{"type": "tool_result", "content": [
                       {"type": "text", "text": "Base directory for this skill: ~/.claude/skills/dispatch\n"}]}]}}]
        self.assertTrue(self.parse("claude", records)["leaks"])

    def test_catalog_gates_do_not_start_routing_sessions(self):
        outputs = {
            "claude": json.dumps({"type": "system", "subtype": "init", "skills": ["dispatch"]}),
            "codex": json.dumps({"prompt": "/user/.agents/skills/dispatch/SKILL.md"}),
            "grok": json.dumps({"skills": [{"name": "dispatch", "source": {
                "path": "/user/.agents/skills/dispatch/SKILL.md"}}]})}
        for host, output in outputs.items():
            with self.subTest(host=host):
                response = subprocess.CompletedProcess([], 0, output, "")
                with patch.object(run_u7.shutil, "which", return_value="/bin/host"), patch.object(
                        run_u7, "run", return_value=response) as invoke:
                    gate = run_u7.catalog_gate(host, Path("/scratch"), {}, {"dispatch"})
                self.assertEqual(gate[0], "NEEDS-USER-CONFIG")
                self.assertEqual(invoke.call_count, 1)
                self.assertIn("no session started", gate[1])


class IsolationTests(unittest.TestCase):
    def test_install_environment_is_private_and_stubs_external_programs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            env = run_u7.install_env(root / "home", root / "target", root / "bin")
            self.assertEqual(set(env), {"HOME", "MMW_V2_HOME", "MMW_HOME", "PATH", "LANG"})
            self.assertNotEqual(env["HOME"], env["MMW_V2_HOME"])
            self.assertTrue((root / "target/.claude").is_dir())
            for name in ("launchctl", "orca", "nmem", "claude", "codex", "grok"):
                binary = Path(env["PATH"].split(":")[0]) / name
                self.assertFalse(binary.is_symlink())
                result = subprocess.run([str(binary), "--not-a-real-option"], capture_output=True)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout + result.stderr, b"")
            self.assertTrue((root / "bin/python3").is_symlink())
            self.assertTrue((root / "bin/git").is_symlink())

    def test_copy_materializes_skills_but_preserves_internal_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            original = root / "source/advisor"
            original.mkdir(parents=True)
            (original / "SKILL.md").write_text("skill")
            (original / "reference.md").symlink_to("SKILL.md")
            (original / "repo-root").symlink_to("../..")
            installed = root / "installed"
            installed.mkdir()
            (installed / "advisor").symlink_to(original)
            dest = root / "repo/.agents/skills"
            run_u7.copy_skills(installed, dest)
            self.assertTrue((dest / "advisor").is_dir())
            self.assertFalse((dest / "advisor").is_symlink())
            self.assertTrue((dest / "advisor/reference.md").is_symlink())
            self.assertEqual(os.readlink(dest / "advisor/reference.md"), str(original / "SKILL.md"))
            self.assertEqual((dest / "advisor/reference.md").read_text(), "skill")
            self.assertTrue((dest / "advisor/repo-root").is_symlink())
            self.assertEqual(os.readlink(dest / "advisor/repo-root"), str(root))

    def test_owner_restores_on_exception_and_leaves_other_links(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            for relative in (".agents/skills", ".claude/skills"):
                skills = home / relative
                skills.mkdir(parents=True)
                (skills / "mmw").symlink_to("/checkout/mmw-v2/skills/mmw")
                (skills / "copy").symlink_to(str(home / ".mmw/skill-copies/copy"))
                (skills / "other").symlink_to("/unrelated/skills/other")
                (skills / "ordinary").mkdir()
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, "deliberate"):
                    with run_u7.moved_skills(home):
                        for relative in (".agents/skills", ".claude/skills"):
                            self.assertFalse((home / relative / "mmw").is_symlink())
                            self.assertFalse((home / relative / "copy").is_symlink())
                            self.assertTrue((home / relative / "other").is_symlink())
                            self.assertTrue((home / relative / "ordinary").is_dir())
                        raise RuntimeError("deliberate")
            for relative in (".agents/skills", ".claude/skills"):
                self.assertEqual(os.readlink(home / relative / "mmw"), "/checkout/mmw-v2/skills/mmw")
                self.assertEqual(os.readlink(home / relative / "copy"), str(home / ".mmw/skill-copies/copy"))

    def test_invalid_owner_arguments_exit_before_creating_directories(self):
        for args in (["--owner"], ["--owner", "--ticket", "0"], ["--ticket", "703"]):
            with self.subTest(args=args):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    home, temporary, stubs = [root / name for name in ("home", "tmp", "bin")]
                    for path in (home, temporary, stubs):
                        path.mkdir()
                    log = root / "external-programs"
                    for name in (*run_u7.STUBS, "git", "mktemp", "tar", "env", "bash"):
                        binary = stubs / name
                        binary.write_text(f"#!/bin/sh\nprintf '%s\\n' invoked >> '{log}'\nexit 91\n")
                        binary.chmod(0o755)
                    result = subprocess.run([sys.executable, "-B", str(check_u7.HERE / "run_u7.py"), *args],
                                            capture_output=True, text=True, env={
                                                "HOME": str(home), "TMPDIR": str(temporary),
                                                "PATH": str(stubs), "LANG": "en_US.UTF-8"})
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(list(home.iterdir()), [])
                    self.assertEqual(list(temporary.iterdir()), [])
                    self.assertFalse(log.exists(), "argument rejection called an external program")


if __name__ == "__main__":
    result = unittest.main(exit=False).result
    if result.wasSuccessful():
        print(f"U7 TESTS OK {result.testsRun}")
    raise SystemExit(0 if result.wasSuccessful() else 1)
