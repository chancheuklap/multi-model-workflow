import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "skills/mmw-mode/scripts/session-start.py"
START = "Read the mmw-mode skill in full before anything else."
COMPACT = ("Your context was compacted: read the mmw-mode skill again in full, then the file "
           "you work by and every file its current step names, before you take that step.")


class SessionStart(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mmw glossary ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.mmw = self.root / "installed mmw"
        real = self.mmw / "mmw-v4/skills/mmw-mode/scripts/session-start.py"
        real.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, real)
        self.script = self.root / "neutral/session-start.py"
        self.script.parent.mkdir()
        self.script.symlink_to(real)
        self.repo = self.root / "product repo"
        self.repo.mkdir()
        (self.repo / ".git").write_text("gitdir: elsewhere\n")

    def run_hook(self, host, payload):
        return subprocess.run([sys.executable, str(self.script), host], input=payload,
                              cwd=self.root, capture_output=True, text=True, timeout=5)

    def context(self, host="claude", event="UserPromptSubmit", cwd=None, **fields):
        run = self.run_hook(host, json.dumps({"hook_event_name": event,
                                             "cwd": str(cwd or self.repo), **fields}))
        self.assertEqual((run.returncode, run.stderr), (0, ""))
        output = json.loads(run.stdout)
        self.assertEqual(set(output), {"hookSpecificOutput"})
        specific = output["hookSpecificOutput"]
        self.assertEqual(set(specific), {"hookEventName", "additionalContext"})
        self.assertEqual(specific["hookEventName"], event)
        self.assertEqual(len(run.stdout.splitlines()), 1)
        return specific["additionalContext"]

    def test_start_and_compaction_context_for_each_host(self):
        for host in ("claude", "codex"):
            for source in ("startup", "resume", "clear", "compact", "fork", "unknown", None):
                with self.subTest(host=host, source=source):
                    fields = {"source": source} if source is not None else {}
                    context = self.context(host, "SessionStart", **fields)
                    self.assertEqual(context, COMPACT if source == "compact" else START)

    def test_per_turn_context_matches_the_event_for_both_hosts(self):
        contexts = [self.context(host) for host in ("claude", "codex")]
        self.assertEqual(contexts[0], contexts[1])
        self.assertIn("definitions", contexts[0])
        self.assertNotIn(START, contexts[0])

    def test_entry_paths_use_event_cwd_nearest_git_and_real_mmw_location(self):
        (self.root / ".git").mkdir()
        (self.root / "CONTEXT.md").write_text("outer glossary")
        product = self.repo / "CONTEXT-MAP.md"
        product.write_text("[Selected](domain/CONTEXT.md)\n")
        (self.repo / "CONTEXT.md").write_text("not the entry")
        installed = self.mmw / "CONTEXT.md"
        installed.write_text("installed glossary")
        nested = self.repo / "src/deep"
        nested.mkdir(parents=True)
        (nested / "CONTEXT.md").write_text("not the repo entry")
        for host in ("claude", "codex"):
            for event in ("SessionStart", "UserPromptSubmit"):
                context = self.context(host, event, cwd=nested)
                self.assertEqual(context.split("\nGlossary entries:\n")[1].splitlines(),
                                 [str(product), str(installed)])
                self.assertNotIn("not the entry", context)
        (self.repo / ".git").unlink()
        (self.repo / ".git").mkdir()
        self.assertIn(str(product), self.context(cwd=nested))

    def test_outside_git_uses_only_cwd_and_map_precedes_root_glossary(self):
        (self.root / "CONTEXT.md").write_text("unrelated ancestor")
        outside = self.root / "outside"
        outside.mkdir()
        entry = outside / "CONTEXT.md"
        entry.write_text("local glossary")
        context = self.context(cwd=outside)
        self.assertEqual(context.split("\nGlossary entries:\n")[1], str(entry))
        context_map = outside / "CONTEXT-MAP.md"
        context_map.write_text("local map")
        self.assertEqual(self.context(cwd=outside).split("\nGlossary entries:\n")[1],
                         str(context_map))
        entry.unlink()
        context_map.unlink()
        self.assertNotIn(str(outside), self.context(cwd=outside))

    def test_mmw_itself_lists_one_entry_and_reads_no_glossary_content_or_state(self):
        entry = self.mmw / "CONTEXT-MAP.md"
        entry.write_bytes(b"\xff not parsed, no definitions copied")
        (self.mmw / ".git").mkdir()
        state = self.root / "state"
        state.mkdir()
        (state / "watches.json").write_text("not valid JSON")
        before = sorted(str(p) for p in self.root.rglob("*"))
        env = {**os.environ, "MMW_HOME": str(state)}
        run = subprocess.run([sys.executable, str(self.script), "codex"],
                             input=json.dumps({"hook_event_name": "UserPromptSubmit",
                                               "cwd": str(self.mmw), "prompt": {"ignored": True},
                                               "transcript_path": "missing"}),
                             env=env, capture_output=True, text=True, timeout=5)
        self.assertEqual((run.returncode, run.stderr), (0, ""))
        context = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(context.splitlines().count(str(entry)), 1)
        self.assertNotIn("not parsed", context)
        self.assertEqual(sorted(str(p) for p in self.root.rglob("*")), before)
        self.assertEqual((state / "watches.json").read_text(), "not valid JSON")

    def test_unknown_events_add_nothing(self):
        for event in ("Stop", "PreToolUse", "unknown", None):
            run = self.run_hook("codex", json.dumps({"hook_event_name": event, "cwd": "/missing"}))
            self.assertEqual((run.returncode, run.stdout, run.stderr), (0, "", ""))

    def test_errors_never_block_or_disclose_payloads(self):
        for host in ("claude", "codex", "unknown"):
            for payload in ("", "{secret", "[]", "null", '"compact"',
                            json.dumps({"hook_event_name": "SessionStart", "cwd": "/missing"}),
                            json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": 42})):
                run = self.run_hook(host, payload)
                self.assertEqual((run.returncode, run.stdout), (0, ""))
                self.assertIn("session-start:", run.stderr)
                self.assertNotIn("secret", run.stderr)
        run = subprocess.run([sys.executable, str(self.script)], input="{}",
                             capture_output=True, text=True, timeout=5)
        self.assertEqual((run.returncode, run.stdout), (0, ""))
        self.assertIn("host argument", run.stderr)

    def test_unreadable_entry_is_advisory(self):
        entry = self.repo / "CONTEXT-MAP.md"
        entry.write_text("private")
        entry.chmod(0)
        self.addCleanup(entry.chmod, 0o600)
        for host in ("claude", "codex"):
            run = self.run_hook(host, json.dumps({"hook_event_name": "UserPromptSubmit",
                                                 "cwd": str(self.repo)}))
            self.assertEqual((run.returncode, run.stdout), (0, ""))
            self.assertIn("glossary paths", run.stderr)
            self.assertNotIn("private", run.stderr)


if __name__ == "__main__":
    unittest.main()
