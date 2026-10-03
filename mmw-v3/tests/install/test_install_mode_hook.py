"""Host registrations and trust in an isolated installation."""

import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path

from install_home import INSTALLER, commands_in, run_install, write_fakes


EVENTS = {"SessionStart": ("session-start", 30),
          "SubagentStart": ("subagent-start", 10),
          "UserPromptSubmit": ("prompt-submit", 10)}


class InstallModeHookTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        root = Path(scratch.name)
        self.home = root / "home"
        self.bin = root / "bin"
        for directory in (".claude", ".codex", ".grok/hooks", ".cursor", ".pi/agent"):
            (self.home / directory).mkdir(parents=True)
        (self.home / ".grok/config.toml").write_text("[compat.claude]\nagents = false\n")
        write_fakes(self.bin)
        result = run_install(INSTALLER, self.home, self.bin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HOOKS-INSTALLED", result.stdout.splitlines())

    def registrations(self, host):
        path = self.home / (".claude/settings.json" if host == "claude" else ".codex/hooks.json")
        hooks = json.loads(path.read_text())["hooks"]
        for event, (argument, timeout) in EVENTS.items():
            found = [(gi, hi, group, handler)
                     for gi, group in enumerate(hooks.get(event, []))
                     for hi, handler in enumerate(group["hooks"])
                     if " mode-hook " in handler.get("command", "")]
            self.assertEqual(len(found), 1, (host, event, hooks))
            gi, hi, group, handler = found[0]
            self.assertNotIn("matcher", group)
            self.assertEqual(handler["timeout"], timeout)
            yield event, argument, gi, hi, handler

    def test_install_registers_the_mode_hook_on_claude_and_codex_for_three_events(self):
        # Reinstallation must update the owned entry, not append a duplicate.
        result = run_install(INSTALLER, self.home, self.bin)
        self.assertEqual(result.returncode, 0, result.stderr)
        launcher = self.home / ".mmw/bin/hook-launcher"
        prefix = '[ -z "${GROK_AGENT:-}${GROK_HOOK_EVENT:-}" ] || exit 0; '
        for host in ("claude", "codex"):
            for _, argument, _, _, handler in self.registrations(host):
                self.assertEqual(handler["type"], "command")
                self.assertEqual(handler["command"], (prefix if host == "claude" else "") +
                                 f"exec python3 '{launcher}' mode-hook {argument} {host}")

    def test_the_mode_hook_is_the_only_registration_on_any_host(self):
        # First prove that this installation actually contains the hook.
        self.assertEqual(len(list(self.registrations("claude"))), 3)
        for host in ("claude", "codex"):
            path = self.home / (".claude/settings.json" if host == "claude" else ".codex/hooks.json")
            commands = commands_in(path)
            self.assertEqual(3, len(commands), commands)
            self.assertTrue(all(" mode-hook " in command for command in commands), commands)
        self.assertEqual([], list((self.home / ".grok/hooks").iterdir()))
        self.assertFalse((self.home / ".cursor/hooks.json").exists())
        self.assertFalse((self.home / ".pi/agent/extensions").exists())

    def test_every_codex_mode_hook_handler_gets_its_trusted_hash(self):
        path = self.home / ".codex/hooks.json"
        trust = tomllib.loads((self.home / ".codex/config.toml").read_text())["hooks"]["state"]
        labels = {"SessionStart": "session_start", "SubagentStart": "subagent_start",
                  "UserPromptSubmit": "user_prompt_submit"}
        for event, _, gi, hi, _ in self.registrations("codex"):
            digest = trust[f"{path}:{labels[event]}:{gi}:{hi}"]["trusted_hash"]
            self.assertIsNotNone(re.fullmatch(r"sha256:[0-9a-f]{64}", digest))


if __name__ == "__main__":
    unittest.main()
