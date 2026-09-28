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
7. Rule seven text.
"""


def temp_file(lines=1):
    tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
    tmp.write("x\n" * lines)
    tmp.close()
    return tmp.name


def run(payload, claude_md=CLAUDE_MD):
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "CLAUDE.md"
        md.write_text(claude_md, encoding="utf-8")
        env = dict(os.environ, MMW_CLAUDE_MD=str(md))
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                              capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout) if proc.stdout.strip() else None


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

    def test_write_gets_rules_1_3_4_6_7(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Edit",
                   "tool_input": {"file_path": "/x/y.md"}})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("About to write `/x/y.md`.", ctx)
        for n in (1, 3, 4, 6, 7):
            self.assertIn(f"Ground rule {n}:", ctx)
        for n in (2, 5):
            self.assertNotIn(f"Ground rule {n}:", ctx)

    def test_agent_gets_rule_6_only(self):
        for inp in ({"prompt": "go", "subagent_type": "general-purpose"},
                    {"prompt": "go", "subagent_type": "verifier"},
                    {"prompt": "go"}):
            out = run({"hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": inp})
            o = out["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", o)
            self.assertEqual(o["additionalContext"], "Ground rule 6: Rule six text.")

    def test_other_tool_is_silent(self):
        self.assertIsNone(run({"hook_event_name": "PreToolUse", "tool_name": "Glob",
                               "tool_input": {"pattern": "*"}}))


class PostToolUse(unittest.TestCase):
    def test_partial_view_names_next_offset(self):
        path = temp_file(1533)
        text = f"...[Truncated: PARTIAL view — {path}: showing lines 1-344 of 1533 total (94698 tokens, cap 25000)...]"
        out = run({"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_response": text})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("offset=345 limit=344", ctx)
        self.assertIn("1189 lines remain", ctx)
        self.assertIn("Ground rule 2:", ctx)

    def test_partial_view_over_an_absent_file_is_silent(self):
        text = "...[Truncated: PARTIAL view — /no/such/f.txt: showing lines 1-344 of 1533 total...]"
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_response": text}))

    def test_partial_view_over_the_wrong_line_count_is_silent(self):
        path = temp_file(10)
        text = f"...[Truncated: PARTIAL view — {path}: showing lines 1-344 of 1533 total...]"
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_response": text}))

    def test_output_saved_names_file(self):
        path = temp_file()
        text = f"Output too large (200KB). Full output saved to: {path}\n\nPreview"
        out = run({"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_response": {"stdout": text}})
        self.assertIn(f"`{path}`", out["hookSpecificOutput"]["additionalContext"])

    def test_output_saved_over_an_absent_path_is_silent(self):
        text = "Output too large (200KB). Full output saved to: /no/such/abc.txt\n\nPreview"
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                               "tool_response": {"stdout": text}}))

    def test_the_hook_source_is_not_read_as_a_marker(self):
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                               "tool_response": {"stdout": HOOK.read_text(encoding="utf-8")}}))

    def test_this_test_file_is_not_read_as_a_marker(self):
        own = Path(__file__).resolve().read_text(encoding="utf-8")
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                               "tool_response": {"stdout": own}}))

    def test_token_cap_text_in_a_successful_result_is_silent(self):
        text = "File content (25582 tokens) exceeds maximum allowed tokens (25000)."
        self.assertIsNone(run({"hook_event_name": "PostToolUse", "tool_name": "Bash",
                               "tool_response": {"stdout": text}}))

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


class Robustness(unittest.TestCase):
    def test_missing_rule_number_does_not_crash(self):
        out = run({"hook_event_name": "PreToolUse", "tool_name": "Agent",
                   "tool_input": {"prompt": "go", "subagent_type": "general-purpose"}},
                  claude_md="## Ground rules\n\n1. only.\n")
        self.assertEqual(out["hookSpecificOutput"]["additionalContext"], "")

    def test_garbage_stdin_exits_zero(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
