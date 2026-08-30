"""Own-script layer for rule-at-moment.py: fixed stdin, fixed CLAUDE.md, no host."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "rule-at-moment.py"

CLAUDE_MD = """Intro line.

## Ground rules

1. Rule one text.
2. Rule two text.
3. Rule three text.
4. Rule four text.
5. Rule five text.
6. Rule six text.

## Subagent model

Do not give a subagent your own model.

## Before ending a turn

Check everything, then reply.
"""


def run(payload, claude_md=CLAUDE_MD):
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "CLAUDE.md"
        md.write_text(claude_md, encoding="utf-8")
        env = dict(os.environ, MMW_CLAUDE_MD=str(md))
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                              capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else None


def transcript(entries):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    for e in entries:
        tmp.write(json.dumps(e) + "\n")
    tmp.close()
    return tmp.name


class PreToolUse(unittest.TestCase):
    def test_read_reports_size_and_rule_2(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write("a\nb\nc\nd\n")
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Read",
                   "tool_input": {"file_path": f.name, "offset": 3}})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("4 lines, 8 bytes", ctx)
        self.assertIn("Reading from line 3; 2 lines remain", ctx)
        self.assertIn("Ground rule 2: Rule two text.", ctx)
        self.assertNotIn("Rule one", ctx)

    def test_bash_gets_rule_2_only(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": "ls"}})
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], "Ground rule 2: Rule two text.")

    def test_write_gets_rules_1_3_4_6(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                   "tool_input": {"file_path": "/x/y.md"}})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("About to write `/x/y.md`.", ctx)
        for n in (1, 3, 4, 6):
            self.assertIn(f"Ground rule {n}:", ctx)
        for n in (2, 5):
            self.assertNotIn(f"Ground rule {n}:", ctx)

    def test_agent_without_model_is_denied(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                   "tool_input": {"prompt": "go", "subagent_type": "general-purpose"}})
        o = out["hookSpecificOutput"]
        self.assertEqual(o["permissionDecision"], "deny")
        self.assertIn("Do not give a subagent your own model.", o["permissionDecisionReason"])

    def test_agent_with_model_gets_rule_6(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                   "tool_input": {"prompt": "go", "model": "opus"}})
        o = out["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", o)
        self.assertIn("Ground rule 6:", o["additionalContext"])

    def test_named_subagent_type_without_model_is_allowed(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                   "tool_input": {"prompt": "go", "subagent_type": "verifier"}})
        self.assertNotIn("permissionDecision", out["hookSpecificOutput"])

    def test_other_tool_is_silent(self):
        self.assertIsNone(run({"hook_event_name": "PreToolUse", "tool_name": "Glob",
                               "tool_input": {"pattern": "*"}}))


class PostToolUse(unittest.TestCase):
    def test_partial_view_names_next_offset(self):
        text = "...[Truncated: PARTIAL view — /f.txt: showing lines 1-344 of 1533 total (94698 tokens, cap 25000)...]"
        out = run({"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_response": text})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("offset=345 limit=344", ctx)
        self.assertIn("1189 lines remain", ctx)
        self.assertIn("Ground rule 2:", ctx)

    def test_output_saved_names_file(self):
        text = "Output too large (200KB). Full output saved to: /tmp/x/abc.txt\n\nPreview"
        out = run({"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_response": {"stdout": text}})
        self.assertIn("`/tmp/x/abc.txt`", out["hookSpecificOutput"]["additionalContext"])

    def test_clean_result_is_silent(self):
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                               "tool_response": {"stdout": "ok"}}))

    def test_failure_gets_rule_5(self):
        out = run({"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                   "error": "exit 1"})
        o = out["hookSpecificOutput"]
        self.assertEqual(o["hookEventName"], "PostToolUseFailure")
        self.assertEqual(o["additionalContext"], "Ground rule 5: Rule five text.")

    def test_tokens_exceeded_on_failure(self):
        out = run({"hook_event_name": "PostToolUseFailure", "tool_name": "Read",
                   "error": "File content (25582 tokens) exceeds maximum allowed tokens (25000)."})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("offset=1", ctx)
        self.assertIn("Ground rule 5:", ctx)


class Stop(unittest.TestCase):
    def test_turn_with_tools_is_blocked_once(self):
        path = transcript([
            {"type": "user", "message": {"content": "do it"}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}},
        ])
        out = run({"hook_event_name": "Stop", "stop_hook_active": False, "transcript_path": path})
        self.assertEqual(out, {"decision": "block", "reason": "Check everything, then reply."})
        again = run({"hook_event_name": "Stop", "stop_hook_active": True, "transcript_path": path})
        self.assertIsNone(again)

    def test_chat_only_turn_is_not_blocked(self):
        path = transcript([
            {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
            {"type": "user", "message": {"content": "thanks"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "np"}]}},
        ])
        self.assertIsNone(run({"hook_event_name": "Stop", "stop_hook_active": False, "transcript_path": path}))


class Robustness(unittest.TestCase):
    def test_missing_heading_is_silent(self):
        out = run({"hook_event_name": "Stop", "stop_hook_active": False,
                   "transcript_path": transcript([{"type": "user", "message": {"content": "x"}},
                                                  {"type": "assistant", "message": {"content": [{"type": "tool_use"}]}}])},
                  claude_md="## Ground rules\n\n1. only.\n")
        self.assertIsNone(out)

    def test_garbage_stdin_exits_zero(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
