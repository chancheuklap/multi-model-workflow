"""mmw-v4/install.sh in a throwaway home (MMW_INSTALL_HOME), with fake orca, nmem, paseo and
launchctl first on PATH. The v3 machine each case starts from is made by running
mmw-v3/install.sh into the same home, so the takeover and the way back meet what v3 really
writes."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parents[2]
V3 = V4.parent / "mmw-v3"
FIXTURE_CATALOG = V4 / "tests/dispatch/catalog.json"

# Every row is one the fixture catalog offers, so models.py's validation passes; the
# role set is v3's.
V3_MODELS = {"version": 3, "runner": "orca", "rows": {
    "junior-worker": {"host": "cursor", "model": "grok 4.6", "effort": "high"},
    "senior-worker": {"host": "grok", "model": "grok 4.6", "effort": "xhigh"},
    "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
    "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
    "researcher": {"host": "claude", "model": "opus 5", "effort": "high"},
    "explainer": {"host": "claude", "model": "opus 5", "effort": "xhigh"},
    "synthesizer": {"host": "claude", "model": "opus 5", "effort": "high"},
}}

FAKES = {
    "orca": """#!/bin/sh
echo "orca $*" >> "$MMW_TEST_LOG"
case "$*" in
  "project setups --json") echo '{"result":{"setups":[{"id":"setup_1"}]}}' ;;
esac
exit 0
""",
    "nmem": """#!/bin/sh
echo "nmem $*" >> "$MMW_TEST_LOG"
case "$*" in
  *"config mcp show"*) echo '{"config":{"mcpServers":{"nowledge-mem":{"url":"http://127.0.0.1:1/mcp"}}}}' ;;
esac
exit 0
""",
    "paseo": """#!/bin/sh
echo "paseo $*" >> "$MMW_TEST_LOG"
exit 0
""",
    # Loaded jobs are files under $MMW_FAKE_LAUNCHD, so print answers what bootstrap did.
    "launchctl": """#!/bin/sh
echo "launchctl $*" >> "$MMW_TEST_LOG"
case "$1" in
  bootstrap) touch "$MMW_FAKE_LAUNCHD/$(basename "$3" .plist)" ;;
  bootout) rm -f "$MMW_FAKE_LAUNCHD/${2##*/}" ;;
  print) [ -f "$MMW_FAKE_LAUNCHD/${2##*/}" ] || exit 1 ;;
esac
exit 0
""",
}


def hook_commands(path):
    data = json.loads(path.read_text())
    return [h["command"] for groups in data.get("hooks", {}).values()
            for g in groups for h in g.get("hooks", [])]


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.home = root / "home"
        self.bin = root / "bin"
        self.log = root / "calls.log"
        self.bin.mkdir()
        for name, body in FAKES.items():
            (self.bin / name).write_text(body)
            (self.bin / name).chmod(0o755)
        for d in (".claude", ".codex", ".cursor", ".mmw", ".agents/skills"):
            (self.home / d).mkdir(parents=True)
        (self.home / ".claude/settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "someone-elses-hook"}]}]}}))
        (self.home / ".mmw/models.json").write_text(json.dumps(V3_MODELS))
        self.log.write_text("")
        self.launchd = root / "launchd"
        self.launchd.mkdir()
        # The dispatch suite's catalog, plus the `opus` family a fresh candidate row
        # (hosts.json's default, `opus[1m]`) resolves against on a real machine.
        catalog = json.loads(FIXTURE_CATALOG.read_text())
        catalog["claude"].append({"id": "opus", "name": "Opus",
                                  "thinkingOptionIds": ["low", "medium", "high", "xhigh"]})
        self.catalog = root / "catalog.json"
        self.catalog.write_text(json.dumps(catalog))

    def tearDown(self):
        self.tmp.cleanup()

    def env(self):
        env = {k: v for k, v in os.environ.items()
               if k not in ("CODEX_HOME", "PI_CODING_AGENT_DIR", "PI_HOME", "MMW_HOME",
                            "MMW_CATALOG_MODE", "MMW_RUNNER") and not k.startswith("NMEM_")}
        env.update(MMW_INSTALL_HOME=str(self.home), MMW_HOST_CATALOG=str(self.catalog),
                   MMW_TEST_LOG=str(self.log), PATH=f"{self.bin}:{env['PATH']}",
                   MMW_FAKE_LAUNCHD=str(self.launchd))
        return env

    def run_install(self, version, *args):
        script = (V4 if version == "v4" else V3) / "install.sh"
        return subprocess.run(["bash", str(script), *args], env=self.env(),
                              capture_output=True, text=True)

    def install_v3(self):
        r = self.run_install("v3")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def link(self, name, where=".agents/skills"):
        return os.readlink(self.home / where / name)

    def test_takes_over_a_v3_machine(self):
        self.install_v3()
        board = self.home / "Library/LaunchAgents/com.mmw.board.plist"
        untouched = {p: p.read_bytes() for p in (board, self.home / ".zshrc", self.home / ".cursor/mcp.json")}
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)

        for where in (".agents/skills", ".claude/skills"):
            self.assertEqual(self.link("dispatch", where), str(V4 / "skills/dispatch"))
            self.assertEqual(self.link("mmw-mode", where), str(V4 / "skills/mmw-mode"))
            # A skill only v3 has stays, pointing where v3 put it.
            self.assertEqual(self.link("retro", where), str(V3 / "skills/retro"))
        self.assertEqual(os.readlink(self.home / ".claude/CLAUDE.md"), str(V4 / "prompt/shared.md"))
        self.assertIn("generated from mmw-v4/prompt/shared.md",
                      (self.home / ".codex/AGENTS.md").read_text().splitlines()[0])

        for config in (self.home / ".claude/settings.json", self.home / ".codex/hooks.json"):
            commands = hook_commands(config)
            self.assertFalse([c for c in commands if "mode-hook.py" in c], commands)
            self.assertEqual(len([c for c in commands if "tool-guard.py' pretool" in c]), 1, commands)
            self.assertEqual(len([c for c in commands if "turn-guard.py' stop" in c]), 1, commands)
        self.assertIn("someone-elses-hook", hook_commands(self.home / ".claude/settings.json"))

        models = json.loads((self.home / ".mmw/models.json").read_text())
        self.assertEqual(sorted(models["rows"]), sorted(
            ["junior-worker", "senior-worker", "reviewer", "advisor", "researcher", "candidate"]))
        self.assertEqual(models["rows"]["reviewer"], V3_MODELS["rows"]["reviewer"])
        backups = list((self.home / ".mmw").glob("models.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertIn("explainer", json.loads(backups[0].read_text())["rows"])

        self.assertEqual((self.home / ".mmw/installed-root").read_text().strip(), str(V4))
        for path, before in untouched.items():
            self.assertEqual(path.read_bytes(), before, path)

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("HOOKS-INSTALLED", check.stdout.splitlines())
        self.assertIn(str(self.home / ".agents/skills/retro"), check.stdout)

    def test_a_second_install_changes_nothing(self):
        self.install_v3()
        self.assertEqual(self.run_install("v4").returncode, 0)
        models = (self.home / ".mmw/models.json").read_bytes()
        backups = sorted((self.home / ".mmw").glob("models.json.bak-*"))
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.home / ".mmw/models.json").read_bytes(), models)
        self.assertEqual(sorted((self.home / ".mmw").glob("models.json.bak-*")), backups)

    def test_back_returns_the_machine_to_v3(self):
        self.install_v3()
        self.assertEqual(self.run_install("v4").returncode, 0)
        r = self.run_install("v4", "--back")
        self.assertEqual(r.returncode, 0, r.stderr)

        for where in (".agents/skills", ".claude/skills"):
            self.assertEqual(self.link("dispatch", where), str(V3 / "skills/dispatch"))
            self.assertEqual(self.link("retro", where), str(V3 / "skills/retro"))
            self.assertFalse((self.home / where / "control-cli").is_symlink(),
                             "a skill only v4 has goes with --back")
        self.assertEqual(os.readlink(self.home / ".claude/CLAUDE.md"), str(V3 / "prompt/shared.md"))
        models = json.loads((self.home / ".mmw/models.json").read_text())
        self.assertEqual(models["rows"], V3_MODELS["rows"])
        self.assertTrue([c for c in hook_commands(self.home / ".claude/settings.json") if "mode-hook.py" in c])
        self.assertEqual((self.home / ".mmw/installed-root").read_text().strip(), str(V3))

        check = self.run_install("v3", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_check_from_another_checkout_hands_over(self):
        other = Path(self.tmp.name) / "installed/mmw-v4"
        other.mkdir(parents=True)
        (other / "install.sh").write_text('echo "installed one checked: $*"\nexit 0\n')
        (self.home / ".mmw/installed-root").write_text(f"{other}\n")
        r = self.run_install("v4", "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("installed one checked: --check", r.stdout)

    def test_orca_setups_get_the_worktree_base_path_and_check_asks_orca_nothing(self):
        self.run_install("v4")
        self.assertIn("orca project setup-update --setup setup_1 --worktree-base-path .worktrees --json",
                      self.log.read_text())
        self.log.write_text("")
        self.run_install("v4", "--check")
        self.assertNotIn("orca", self.log.read_text())

    def test_check_reports_v3_rows_before_install(self):
        self.install_v3()
        (self.home / ".mmw/installed-root").write_text(f"{V4}\n")
        r = self.run_install("v4", "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("explainer", r.stderr)
        self.assertIn("mode-hook.py", r.stderr)

    @unittest.skipUnless(os.uname().sysname == "Darwin", "launchd is macOS only")
    def test_prompt_sync_job_is_written_and_loaded_on_a_real_home(self):
        # With HOME pointing at the throwaway home too, install takes the branch that
        # writes the launchd job, which a test home alone skips.
        env = self.env()
        env["HOME"] = str(self.home)
        r = subprocess.run(["bash", str(V4 / "install.sh")], env=env, capture_output=True, text=True)
        self.assertNotIn("command not found", r.stderr)
        plist = self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist"
        self.assertIn(str(V4 / "prompt/render.py"), plist.read_text())
        self.assertIn("launchctl bootstrap", self.log.read_text())
        check = subprocess.run(["bash", str(V4 / "install.sh"), "--check"], env=env,
                               capture_output=True, text=True)
        self.assertNotIn("com.mmw.prompt-sync", check.stderr)

    def test_never_touches_memory_or_the_board(self):
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("nmem", self.log.read_text())
        self.assertNotIn("launchctl", self.log.read_text())
        self.assertFalse((self.home / "Library/LaunchAgents/com.mmw.board.plist").exists())
        self.assertFalse((self.home / ".zshrc").exists())
        self.assertFalse((self.home / ".cursor/mcp.json").exists())


if __name__ == "__main__":
    unittest.main()
