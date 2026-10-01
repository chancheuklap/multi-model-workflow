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

# Captured verbatim: Claude Code 2.1.286, 2026-10-01, S07 after.
CLAUDE_S07_EVENTS = (
    '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"msg_011CfbKBvEuPqnqNFnLuBtYE","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_017ZVU7S4AUr3JDPSsRh38vg","name":"Glob","input":{"pattern":"{.mmw/**,docs/agents/**,AGENTS.md,CLAUDE.md,.claude/**}"},"caller":{"type":"direct"}}],"container":null,"stop_reason":null,"stop_sequence":null,"stop_details":null,"usage":{"input_tokens":2,"cache_creation_input_tokens":6921,"cache_read_input_tokens":3624,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":6921},"output_tokens":8,"service_tier":"standard","inference_geo":"not_available"},"input_transformations":[],"diagnostics":null,"context_management":null},"parent_tool_use_id":null,"session_id":"bc9866da-c9e5-4633-8f92-337a0dab9c5e","uuid":"3286b059-2bad-4dfb-b089-3441f3eeb4c8","timestamp":"2026-10-01T09:54:10.554Z","request_id":"req_011CfbKBur6T3SdM5Jq2yWML","wire_tool_inputs":{"toolu_017ZVU7S4AUr3JDPSsRh38vg":{"pattern":"{.mmw/**,docs/agents/**,AGENTS.md,CLAUDE.md,.claude/**}"}}}',
    '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"msg_011CfbKC7KAHp79t98w9wjxC","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01LRN32LzzC19VEUQ6czxto1","name":"Skill","input":{"skill":"dispatch","args":"night spec #12"},"caller":{"type":"direct"}}],"container":null,"stop_reason":null,"stop_sequence":null,"stop_details":null,"usage":{"input_tokens":2,"cache_creation_input_tokens":2790,"cache_read_input_tokens":10545,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":2790},"output_tokens":17,"service_tier":"standard","inference_geo":"not_available"},"input_transformations":[],"diagnostics":null,"context_management":null},"parent_tool_use_id":null,"session_id":"bc9866da-c9e5-4633-8f92-337a0dab9c5e","uuid":"282f99e2-e57f-4abf-8485-ae1c12357086","timestamp":"2026-10-01T09:54:12.705Z","request_id":"req_011CfbKC6q8vg1FBrm6KNqjP","wire_tool_inputs":{"toolu_01LRN32LzzC19VEUQ6czxto1":{"skill":"dispatch","args":"night spec #12"}}}',
    '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"msg_011CfbKCGJQsSaYwQcc6Z44M","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01NYqCfJ4ijpJtx7QsP5GEnW","name":"Read","input":{"file_path":"/private/var/folders/z5/k4mmh1596q96pv5fkgpsq4yr0000gn/T/tmp.T4Hx3X6iDE/claude-after/.claude/skills/dispatch/references/night.md"},"caller":{"type":"direct"}}],"container":null,"stop_reason":null,"stop_sequence":null,"stop_details":null,"usage":{"input_tokens":2,"cache_creation_input_tokens":991,"cache_read_input_tokens":13335,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":991},"output_tokens":16,"service_tier":"standard","inference_geo":"not_available"},"input_transformations":[],"diagnostics":null,"context_management":null},"parent_tool_use_id":null,"session_id":"bc9866da-c9e5-4633-8f92-337a0dab9c5e","uuid":"f8d6fd92-af5c-481e-aa1a-b944cca3cbf0","timestamp":"2026-10-01T09:54:14.934Z","request_id":"req_011CfbKCFtMf811iWW72Gjee","wire_tool_inputs":{"toolu_01NYqCfJ4ijpJtx7QsP5GEnW":{"file_path":"/private/var/folders/z5/k4mmh1596q96pv5fkgpsq4yr0000gn/T/tmp.T4Hx3X6iDE/claude-after/.claude/skills/dispatch/references/night.md"}}}',
    '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"msg_011CfbKCRqPMAmoLrjvUCS9u","type":"message","role":"assistant","content":[{"type":"tool_use","id":"toolu_01BGnXgJVfMQVa8ifS5kAZcf","name":"Glob","input":{"pattern":"{.mmw/*,docs/agents/*,CLAUDE.md,AGENTS.md}"},"caller":{"type":"direct"}}],"container":null,"stop_reason":null,"stop_sequence":null,"stop_details":null,"usage":{"input_tokens":2,"cache_creation_input_tokens":8998,"cache_read_input_tokens":14326,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":8998},"output_tokens":10,"service_tier":"standard","inference_geo":"not_available"},"input_transformations":[],"diagnostics":null,"context_management":null},"parent_tool_use_id":null,"session_id":"bc9866da-c9e5-4633-8f92-337a0dab9c5e","uuid":"832f2c94-e4e1-4795-acc7-772fa0870e42","timestamp":"2026-10-01T09:54:17.720Z","request_id":"req_011CfbKCRVJsjStNrmz2NxTx","wire_tool_inputs":{"toolu_01BGnXgJVfMQVa8ifS5kAZcf":{"pattern":"{.mmw/*,docs/agents/*,CLAUDE.md,AGENTS.md}"}}}',
)


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

    def test_claude_captured_s07_tools_not_reply(self):
        records = [json.loads(line) for line in CLAUDE_S07_EVENTS]
        filename = next(block["input"]["file_path"] for record in records
                        for block in record["message"]["content"] if block.get("name") == "Read")
        # A synthetic assistant claim is a negative control, not a captured event.
        claim = json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "LOADED: mmw playbooks/prototype.md"}]}})
        parsed = run_u7.parse_events("claude", "\n".join((*CLAUDE_S07_EVENTS, claim)),
                                    Path(filename).parents[5], {"mmw", "dispatch"})
        self.assertEqual(parsed["skills"], ["dispatch"])
        self.assertEqual(parsed["playbooks"], [])
        self.assertEqual(parsed["tool_calls"], 4)
        self.assertEqual(parsed["leaks"], [])

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
                with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"HOME": directory}), \
                     patch.object(run_u7.shutil, "which", return_value="host"), patch.object(
                        run_u7, "run", return_value=response) as invoke:
                    gate = run_u7.catalog_gate(host, Path("/scratch"), {}, {"dispatch"},
                                               "2.1.286_(Claude_Code)" if host == "claude" else "test")
                self.assertEqual(gate[0], "NEEDS-USER-CONFIG")
                self.assertEqual(invoke.call_count, 1)
                self.assertIn("no session started", gate[1])


class CatalogTests(unittest.TestCase):
    def run_catalog(self, version, catalog):
        rows = check_u7.read_sentences()
        stdout = json.dumps({"type": "system", "subtype": "init", "skills": catalog})
        def response(argv, *args, **kwargs):
            return subprocess.CompletedProcess(argv, 0, version if "--version" in argv else stdout, "")
        parsed = {"skills": ["dispatch"], "playbooks": [], "leaks": [], "tool_calls": 1}
        raw = subprocess.CompletedProcess([], 0, "", "")
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"HOME": directory}), \
                 patch.object(run_u7, "install_set", return_value=(Path(directory), {"code-review", "dispatch"})), \
                 patch.object(run_u7, "prepare"), patch.object(run_u7.shutil, "which", return_value="host"), \
                 patch.object(run_u7, "run", side_effect=response), \
                 patch.object(run_u7, "measure", return_value=(("PASS", "fixture"), raw, parsed)) as session, \
                 contextlib.redirect_stdout(io.StringIO()):
                lines = run_u7.measure_sets(["claude"], rows, {"before": check_u7.BEFORE, "after": "a" * 40})
        return lines, session.call_count

    def test_measured_builtin_same_version_starts_all_22_sessions(self):
        lines, sessions = self.run_catalog("2.1.286 (Claude Code)", ["code-review"])
        self.assertEqual(sessions, 22)
        self.assertEqual(len(lines), 22)
        self.assertTrue(all(" PASS " in line for line in lines))

    def test_unmeasured_version_blocks_all_22_cells(self):
        lines, sessions = self.run_catalog("2.1.287 (Claude Code)", ["code-review"])
        self.assertEqual(sessions, 0)
        self.assertTrue(all(" NEEDS-USER-CONFIG " in line for line in lines))
        self.assertTrue(all("built-in list not measured for this version" in line for line in lines))

    def test_nonbuiltin_measured_name_blocks_all_22_cells(self):
        lines, sessions = self.run_catalog("2.1.286 (Claude Code)", ["code-review", "dispatch"])
        self.assertEqual(sessions, 0)
        self.assertEqual(len(lines), 22)
        self.assertTrue(all(" NEEDS-USER-CONFIG " in line and "dispatch from user level" in line for line in lines))


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
