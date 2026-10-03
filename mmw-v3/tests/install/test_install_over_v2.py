"""install.sh on a home that holds an mmw-v2 install, and --check handed between checkouts."""

import json
import os
import tempfile
import tomllib
import unittest
from pathlib import Path

import v2_home
from install_home import (INSTALLER, MMW, calls, commands_in, copy_mmw, listed_skills,
                          mode_hook_command, run_install, snapshot, write_fakes)

EVENTS = {"SessionStart": "session-start", "SubagentStart": "subagent-start",
          "UserPromptSubmit": "prompt-submit"}


class InstallOverV2(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)
        self.home = self.scratch / "home"
        self.old = self.scratch / "old" / "mmw-v2"
        self.bin = self.scratch / "bin"
        write_fakes(self.bin)
        self.kept = v2_home.build(self.home, self.old)
        self.log = self.scratch / "services.log"
        self.launcher = self.home / ".mmw" / "bin" / "hook-launcher"
        self.env = {"MMW_TEST_SERVICE_LOG": str(self.log),
                    "MMW_TEST_LAUNCHD_STATE": str(self.scratch / "launchd.json"),
                    "MMW_V3_LAUNCHCTL": str(self.bin / "launchctl")}

    def run_installer(self, *args):
        return run_install(INSTALLER, self.home, self.bin, *args, env_overrides=self.env)

    def our_links(self, dest):
        return {path.name: os.readlink(path) for path in dest.iterdir()
                if path.is_symlink() and path.name not in ("someone-else",)}

    def test_check_on_the_v2_home_fails_names_each_leftover_and_changes_nothing(self):
        before = snapshot(self.home)
        result = self.run_installer("--check")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        err = result.stderr
        expected = [
            f"残留  {self.home}/.mmw/installed-root 记的是 {self.old}",
            f"残留  {self.home}/.mmw/skill-copies 是安装副本目录",
            f"残留  {self.home}/.agents/skills/triage 指进 {self.home}/.mmw/skill-copies",
            f"残留  {self.home}/.claude/skills/wayfinder 指进 {self.home}/.mmw/skill-copies",
            f"残留  {self.home}/.agents/skills/tdd 指向 mmw-v2 的 {self.old}/upstream/skills/engineering/tdd",
            f"残留  {self.home}/.cursor/skills 是 retired 的位置",
            f"残留  {self.home}/.codex/skills 是 retired 的位置",
            f"残留  {self.home}/.claude/CLAUDE.md 指向 mmw-v2 的",
            f"残留  {self.home}/.pi/agent/extensions/mmw-verify-ticket.ts",
            f"残留  {self.home}/.pi/agent/extensions/mmw-turn-guard.ts",
        ]
        for name in v2_home.GONE_NAMES:
            expected.append(f"残留  {self.home}/.agents/skills/{name} 指回本仓库，skills.txt 里却没有它")
        for line in expected:
            self.assertIn(line, err)
        for path, hook in ((".claude/settings.json", "tool-guard pretool claude"),
                           (".claude/settings.json", "tool-guard question claude"),
                           (".claude/settings.json", "turn-guard stop claude"),
                           (".codex/hooks.json", "tool-guard pretool codex"),
                           (".codex/hooks.json", "turn-guard stop codex"),
                           (".cursor/hooks.json", "tool-guard pretool cursor"),
                           (".cursor/hooks.json", "turn-guard stop cursor"),
                           (".grok/hooks/mmw-verify-ticket.json", "tool-guard question grok"),
                           (".grok/hooks/mmw-turn-guard.json", "turn-guard stop grok")):
            with self.subTest(path=path, hook=hook):
                self.assertTrue([line for line in err.splitlines()
                                 if line.startswith(f"残留  {self.home / path}") and hook in line], err)
        # The v2 checkout's install.sh was not handed the check, and nothing on disk moved.
        self.assertNotIn("装自", result.stdout)
        self.assertFalse((self.old / "install-sh-ran").exists())
        self.assertEqual(before, snapshot(self.home))
        self.assertFalse([c for c in calls(self.log) if c[0] == "launchctl" and c[1] != "print"])

    def test_install_leaves_only_v3_links_and_mode_hooks_then_check_passes(self):
        result = self.run_installer()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("HOOKS-INSTALLED", result.stdout.splitlines())
        names = listed_skills()

        # Skills: exactly the listed names, each at mmw-v3/skills/<name>; others' entries untouched.
        for dest in (self.home / ".agents/skills", self.home / ".claude/skills"):
            with self.subTest(dest=dest):
                self.assertEqual({name: str(MMW / "skills" / name) for name in names},
                                 self.our_links(dest))
                self.assertEqual("/elsewhere/skills/someone-else",
                                 os.readlink(dest / "someone-else"))
                self.assertEqual("mine\n", (dest / "my-own-skill" / "SKILL.md").read_text())
        self.assertEqual([], list((self.home / ".cursor/skills").iterdir()))
        self.assertEqual([], list((self.home / ".codex/skills").iterdir()))
        self.assertFalse((self.home / ".mmw/skill-copies").exists())

        # Hooks: no tool-guard or turn-guard anywhere; one mode-hook per event on claude and codex.
        hook_files = [self.home / ".claude/settings.json", self.home / ".codex/hooks.json",
                      self.home / ".cursor/hooks.json",
                      *sorted((self.home / ".grok/hooks").glob("*.json"))]
        for path in hook_files:
            for command in commands_in(path):
                self.assertNotIn("tool-guard", command, path)
                self.assertNotIn("turn-guard", command, path)
        self.assertFalse((self.home / ".grok/hooks/mmw-verify-ticket.json").exists())
        self.assertFalse((self.home / ".grok/hooks/mmw-turn-guard.json").exists())
        self.assertEqual(["someone-else.ts"],
                         [p.name for p in (self.home / ".pi/agent/extensions").iterdir()])
        for host, path in (("claude", self.home / ".claude/settings.json"),
                           ("codex", self.home / ".codex/hooks.json")):
            commands = commands_in(path)
            for argument in EVENTS.values():
                self.assertEqual(1, commands.count(mode_hook_command(self.launcher, host, argument)))
            self.assertEqual(3, len([c for c in commands if "hook-launcher" in c]), commands)
            self.assertIn("herdr hook pretool", commands)
        self.assertIn("nmem hook session-start", commands_in(self.home / ".claude/settings.json"))
        self.assertEqual(["someone-else format"], commands_in(self.home / ".cursor/hooks.json"))
        settings = json.loads((self.home / ".claude/settings.json").read_text())
        self.assertEqual({"allow": ["Bash(ls:*)"]}, settings["permissions"])
        self.assertEqual((MMW / "hook-launcher.py").read_bytes(), self.launcher.read_bytes())
        config = tomllib.loads((self.home / ".codex/config.toml").read_text())
        self.assertEqual("gpt-5", config["model"])
        hooks_json = self.home / ".codex/hooks.json"
        trusted = {name for name in config["hooks"]["state"] if name.startswith(str(hooks_json))}
        for label in ("session_start", "subagent_start", "user_prompt_submit"):
            self.assertTrue([name for name in trusted if f":{label}:" in name], trusted)

        # Prompts and the record of what is installed.
        self.assertEqual(str(MMW / "prompt/shared.md"), os.readlink(self.home / ".claude/CLAUDE.md"))
        self.assertEqual(str(MMW / "prompt/hosts/claude.md"),
                         os.readlink(self.home / ".claude/rules/mmw-claude.md"))
        for target in (".codex/AGENTS.md", ".pi/agent/AGENTS.md", ".grok/AGENTS.md"):
            self.assertIn("generated from mmw-v3/prompt/shared.md",
                          (self.home / target).read_text().splitlines()[0])
        plist = (self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist").read_text()
        self.assertIn(str(MMW / "prompt" / "render.py"), plist)
        self.assertEqual(str(MMW), (self.home / ".mmw/installed-root").read_text().strip())

        # What v3 does not manage is left as it was, and its services are not called.
        for path, text in self.kept.items():
            self.assertEqual(text, path.read_text(), path)
        made = calls(self.log)
        self.assertFalse([c for c in made if c[0] == "nmem"], made)
        self.assertFalse([c for c in made if "com.mmw.board" in " ".join(c)], made)
        self.assertEqual(["bootout", "print", "bootstrap"],
                         [c[1] for c in made if c[0] == "launchctl"])
        self.assertFalse((self.old / "install-sh-ran").exists())

        check = self.run_installer("--check")
        self.assertEqual(0, check.returncode, check.stdout + check.stderr)
        self.assertIn("HOOKS-INSTALLED", check.stdout.splitlines())
        self.assertIn(f"齐了：技能 2 处 × {len(names)} 个，hook 见上", check.stdout)

    def test_after_install_each_single_v2_leftover_alone_fails_the_check(self):
        installed = self.run_installer()
        self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
        root = self.home / ".mmw/installed-root"
        claude_md = self.home / ".claude/CLAUDE.md"
        cases = {
            "installed-root": (lambda: root.write_text(f"{self.old}\n"),
                               lambda: root.write_text(f"{MMW}\n"),
                               f"残留  {root} 记的是 {self.old}"),
            "prompt link": (lambda: (claude_md.unlink(),
                                     claude_md.symlink_to(self.old / "prompt/shared.md")),
                            lambda: (claude_md.unlink(),
                                     claude_md.symlink_to(MMW / "prompt/shared.md")),
                            f"残留  {claude_md} 指向 mmw-v2 的"),
            "skill-copies": (lambda: (self.home / ".mmw/skill-copies/x").mkdir(parents=True),
                             lambda: ((self.home / ".mmw/skill-copies/x").rmdir(),
                                      (self.home / ".mmw/skill-copies").rmdir()),
                             f"残留  {self.home}/.mmw/skill-copies 是安装副本目录"),
        }
        for label, (break_it, mend_it, line) in cases.items():
            with self.subTest(leftover=label):
                break_it()
                result = self.run_installer("--check")
                mend_it()
                self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                self.assertIn(line, result.stderr)
                self.assertNotIn("装自", result.stdout)
        self.assertFalse((self.old / "install-sh-ran").exists())
        self.assertEqual(0, self.run_installer("--check").returncode)

    def test_a_second_install_changes_nothing(self):
        first = self.run_installer()
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        after_first = snapshot(self.home)
        self.log.write_text("")
        second = self.run_installer()
        self.assertEqual(0, second.returncode, second.stdout + second.stderr)
        self.assertEqual(after_first, snapshot(self.home))
        self.assertNotIn("摘掉", second.stdout)
        self.assertEqual(["print"], [c[1] for c in calls(self.log) if c[0] == "launchctl"])


class CheckHandover(unittest.TestCase):
    def test_check_from_another_checkout_is_handed_to_the_installed_mmw_v3(self):
        with tempfile.TemporaryDirectory() as raw:
            scratch = Path(raw)
            installed = copy_mmw(scratch, "installed")
            other = copy_mmw(scratch, "other")
            home, bin_dir = scratch / "home", scratch / "bin"
            (home / ".claude").mkdir(parents=True)
            write_fakes(bin_dir)
            result = run_install(installed / "install.sh", home, bin_dir)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            # Run locally, other's check would find every link pointing at the installed copy.
            check = run_install(other / "install.sh", home, bin_dir, "--check")
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            self.assertEqual(f"装自  {installed}（本 checkout {other} 只核对，不接管）",
                             check.stdout.splitlines()[0])
            self.assertIn("齐了", check.stdout)


if __name__ == "__main__":
    unittest.main()
