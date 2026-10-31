import hashlib
import json
import tomllib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parents[2]
FIXTURE_CATALOG = V4 / "tests/dispatch/catalog.json"

# Every row is one the fixture catalog offers, so models.py's validation passes; the
# role set is v3's.
V3_MODELS = {"version": 3, "runner": "orca", "rows": {
    "junior-worker": {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"},
    "senior-worker": {"host": "claude", "model": "sonnet 5", "effort": "xhigh"},
    "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
    "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
    "researcher": {"host": "claude", "model": "opus 5", "effort": "high"},
    "explainer": {"host": "claude", "model": "opus 5", "effort": "xhigh"},
    "synthesizer": {"host": "claude", "model": "opus 5", "effort": "high"},
}}

FAKES = {
    # Orca's setups live in the JSON list at $MMW_FAKE_ORCA_SETUPS; setup-update changes it.
    "orca": """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["MMW_TEST_LOG"], "a") as log:
    log.write("orca " + " ".join(args) + "\\n")
path = os.environ["MMW_FAKE_ORCA_SETUPS"]
setups = json.load(open(path))
if args == ["project", "setups", "--json"]:
    print(json.dumps({"result": {"setups": setups}}))
elif args[:2] == ["project", "setup-update"]:
    ident = args[args.index("--setup") + 1]
    for row in setups:
        if row["id"] == ident:
            row["worktreeBasePath"] = args[args.index("--worktree-base-path") + 1]
    json.dump(setups, open(path, "w"))
""",
    # `gh auth status` answers $MMW_FAKE_GH_AUTH, 0 (logged in) when unset.
    "gh": """#!/bin/sh
echo "gh $*" >> "$MMW_TEST_LOG"
if [ "$*" = "auth status" ] && [ "${MMW_FAKE_GH_AUTH:-0}" != 0 ]; then
  echo "You are not logged into any GitHub hosts. To log in, run: gh auth login" >&2
  exit 1
fi
exit 0
""",
    "node": """#!/bin/sh
exit 0
""",
    "nmem": """#!/bin/sh
echo "nmem $*" >> "$MMW_TEST_LOG"
case "$*" in
  *"config mcp show"*) echo '{"config":{"mcpServers":{"nowledge-mem":{"url":"http://127.0.0.1:1/mcp"}}}}' ;;
esac
exit 0
""",
    "herdr": """#!/bin/sh
echo "herdr $*" >> "$MMW_TEST_LOG"
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
  bootout)
    [ "${MMW_FAKE_LAUNCHD_STUCK:-}" != "${2##*/}" ] || exit 1
    rm -f "$MMW_FAKE_LAUNCHD/${2##*/}" ;;
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
        self.v4 = root / "checkout/mmw-v4"
        self.v4.mkdir(parents=True)
        for child in V4.iterdir():
            (self.v4 / child.name).symlink_to(child, target_is_directory=child.is_dir())
        (self.v4 / "prompt").unlink()
        shutil.copytree(V4 / "prompt", self.v4 / "prompt")
        self.legacy = self.v4.parent / "mmw-v3"
        self.legacy.mkdir()
        (self.legacy / "install.sh").write_text(
            'python3 - <<\'STUB\'\n'
            'import json, os\n'
            'from pathlib import Path\n'
            'home = Path(os.environ["MMW_INSTALL_HOME"])\n'
            'target = Path(os.environ.get("CODEX_HOME", home / ".codex")) / "AGENTS.md"\n'
            'target.write_text("synthetic v3 prompt")\n'
            '(home / "legacy-called.json").write_text(json.dumps({"cwd": os.getcwd(), '
            '"models": json.loads((home / ".mmw/models.json").read_text())}))\n'
            'STUB\nexit 23\n')
        roles = self.legacy / "skills/dispatch/roles.json"
        roles.parent.mkdir(parents=True)
        roles.write_text(json.dumps({"roles": [{"name": name, "kind": "session"}
                                               for name in V3_MODELS["rows"]]}))
        self.bin = root / "bin"
        self.paseo_app = root / "Paseo.app/Contents/Resources/bin/paseo"
        self.paseo_app.parent.mkdir(parents=True)
        self.paseo_app.symlink_to(self.bin / "paseo")
        installer = self.v4 / "install.sh"
        installer.unlink()
        installer.write_text((V4 / "install.sh").read_text().replace(
            "/Applications/Paseo.app/Contents/Resources/bin/paseo", str(self.paseo_app)))
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
        # (its default in roles.json, `opus`) resolves against on a real machine.
        catalog = json.loads(FIXTURE_CATALOG.read_text())
        for family in ("opus", "sonnet", "fable"):
            catalog["claude"].append({"id": family, "name": family.title(),
                                      "thinkingOptionIds": ["low", "medium", "high", "xhigh"]})
        catalog["codex"].append({"id": "gpt-6.1-sol", "name": "GPT-6.1-Sol",
                                 "thinkingOptionIds": ["low", "medium", "high", "xhigh"]})
        self.catalog = root / "catalog.json"
        self.catalog.write_text(json.dumps(catalog))
        self.orca_setups = root / "orca-setups.json"
        self.orca_setups.write_text(json.dumps([{"id": "setup_1", "path": "/repos/first"}]))

    def tearDown(self):
        self.tmp.cleanup()

    def env(self):
        for tool in ("python3", "uv", "git"):
            if not (self.bin / tool).exists():
                (self.bin / tool).symlink_to(shutil.which(tool))
        env = {k: v for k, v in os.environ.items()
               if k not in ("CODEX_HOME", "PI_CODING_AGENT_DIR", "PI_HOME", "MMW_HOME",
                            "MMW_CATALOG_MODE", "MMW_RUNNER", "HERDR_ENV",
                            "PASEO_AGENT_ID", "PASEO_WORKSPACE_ID", "TERM_PROGRAM") and not k.startswith("NMEM_")}
        env.update(MMW_INSTALL_HOME=str(self.home), MMW_HOST_CATALOG=str(self.catalog),
                   MMW_TEST_LOG=str(self.log), PATH=f"{self.bin}:/usr/bin:/bin",
                   MMW_FAKE_LAUNCHD=str(self.launchd), MMW_FAKE_ORCA_SETUPS=str(self.orca_setups))
        return env

    def run_install(self, version, *args, env=None):
        if version != "v4":
            raise AssertionError("tests execute only the v4 installer and the synthetic rollback stub")
        script = self.v4 / "install.sh"
        return subprocess.run(["bash", str(script), *args], env=env or self.env(),
                              capture_output=True, text=True)

    def seed_legacy_install(self):
        for where in (".agents/skills", ".claude/skills"):
            for name in ("dispatch", "mmw-mode", "triage"):
                target = self.legacy / "skills" / name
                target.mkdir(parents=True, exist_ok=True)
                (self.home / where).mkdir(parents=True, exist_ok=True)
                (self.home / where / name).symlink_to(target)
        prompt = self.legacy / "prompt/shared.md"
        prompt.parent.mkdir()
        prompt.write_text("synthetic legacy prompt")
        (self.home / ".claude/CLAUDE.md").symlink_to(prompt)
        for host, config in (("claude", self.home / ".claude/settings.json"),
                             ("codex", self.home / ".codex/hooks.json")):
            data = json.loads(config.read_text()) if config.exists() else {}
            command = f"python3 '{self.home}/.agents/skills/mmw-mode/scripts/mode-hook.py' {host}"
            data.setdefault("hooks", {}).setdefault("Stop", []).append({"hooks": [
                {"type": "command", "command": command}]})
            config.write_text(json.dumps(data))
        (self.home / ".codex/config.toml").write_text('model = "keep-model"\n')
        (self.home / ".mmw/installed-root").write_text(f"{self.legacy}\n")
        (self.home / ".zshrc").write_text("unrelated shell settings")
        (self.home / ".cursor/mcp.json").write_text('{"unrelated": true}')
        board = self.home / "Library/LaunchAgents/com.mmw.board.plist"
        board.parent.mkdir(parents=True)
        board.write_text(str(self.legacy / "board/supervisor.py"))

    def link(self, name, where=".agents/skills"):
        return os.readlink(self.home / where / name)

    def generated_prompt(self, version="v4"):
        body = "synthetic old shared body\n"
        digest = hashlib.sha256(body.encode()).hexdigest()
        return (f"<!-- mmw prompt-sync: generated from mmw-{version}/prompt/shared.md; "
                f"edit that, not this file. body-sha256={digest} -->\n" + body)

    def test_prompt_links_read_one_source_and_follow_changes_without_install(self):
        source = self.v4 / "prompt/shared.md"
        targets = [self.home / ".claude/CLAUDE.md", self.home / ".codex/AGENTS.md"]
        for _ in range(2):
            run = self.run_install("v4")
            self.assertEqual(run.returncode, 0, run.stderr)
        for target in targets:
            self.assertEqual(os.readlink(target), str(source))
            self.assertEqual(target.read_bytes(), source.read_bytes())
        source.write_text("new shared instructions\n")
        self.assertEqual([p.read_text() for p in targets], [source.read_text()] * 2)
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)
        self.assertFalse((self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist").exists())

    def test_generated_codex_files_are_reported_then_migrated(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        target = self.home / ".codex/AGENTS.md"
        for version in ("v2", "v3", "v4"):
            with self.subTest(version=version):
                target.unlink()
                original = self.generated_prompt(version)
                target.write_text(original)
                check = self.run_install("v4", "--check")
                self.assertEqual(check.returncode, 1)
                self.assertIn(f"{target} 还是生成文件", check.stderr)
                self.assertFalse(target.is_symlink())
                self.assertEqual(target.read_text(), original)
                run = self.run_install("v4")
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(os.readlink(target), str(self.v4 / "prompt/shared.md"))

    def test_prompt_migration_preserves_foreign_and_edited_files(self):
        target = self.home / ".codex/AGENTS.md"
        source = self.v4 / "prompt/shared.md"
        source_before = source.read_bytes()
        for contents in (b"personal instructions\n", b"\xff\xfe", self.generated_prompt().encode() + b"hand edit\n"):
            with self.subTest(contents=contents):
                target.write_bytes(contents)
                for args in ((), ("--check",)):
                    run = self.run_install("v4", *args)
                    self.assertEqual(run.returncode, 1, run.stderr)
                    self.assertIn(f"冲突  {target}", run.stderr)
                    self.assertFalse(target.is_symlink())
                    self.assertEqual(target.read_bytes(), contents)
                    self.assertEqual(source.read_bytes(), source_before)

    def test_prompt_links_from_other_checkouts_are_reported_then_retargeted(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        for rel in (".claude/CLAUDE.md", ".codex/AGENTS.md"):
            target = self.home / rel
            target.unlink()
            old = Path(self.tmp.name) / "old/mmw-v4/prompt/shared.md"
            target.symlink_to(old)
            check = self.run_install("v4", "--check")
            self.assertEqual(check.returncode, 1)
            self.assertIn(f"{target} 指向别的 checkout", check.stderr)
            self.assertEqual(os.readlink(target), str(old))
            run = self.run_install("v4")
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(os.readlink(target), str(self.v4 / "prompt/shared.md"))

    def test_foreign_prompt_links_and_files_are_preserved_for_both_hosts(self):
        foreign = Path(self.tmp.name) / "personal.md"
        foreign.write_text("personal instructions")
        for rel in (".claude/CLAUDE.md", ".codex/AGENTS.md"):
            target = self.home / rel
            if target.is_symlink():
                target.unlink()
            target.write_text("personal instructions")
            run = self.run_install("v4")
            self.assertEqual(run.returncode, 1)
            self.assertEqual(target.read_text(), "personal instructions")
            target.unlink()
            target.symlink_to(foreign)
            for args in ((), ("--check",)):
                run = self.run_install("v4", *args)
                self.assertEqual(run.returncode, 1)
                self.assertIn(f"冲突  {target}", run.stderr)
                self.assertEqual(os.readlink(target), str(foreign))
                self.assertEqual(foreign.read_text(), "personal instructions")
            target.unlink()

    def test_codex_home_override_is_used_for_install_check_and_back(self):
        codex_home = Path(self.tmp.name) / "custom-codex"
        codex_home.mkdir()
        env = dict(self.env(), CODEX_HOME=str(codex_home))
        default = self.home / ".codex/AGENTS.md"
        default.write_text("do not use this Codex home")
        target = codex_home / "AGENTS.md"
        target.write_text(self.generated_prompt())
        run = self.run_install("v4", env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(os.readlink(target), str(self.v4 / "prompt/shared.md"))
        self.assertEqual(self.run_install("v4", "--check", env=env).returncode, 0)
        before = (self.v4 / "prompt/shared.md").read_bytes()
        self.assertEqual(self.run_install("v4", "--back", env=env).returncode, 23)
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_text(), "synthetic v3 prompt")
        self.assertEqual((self.v4 / "prompt/shared.md").read_bytes(), before)
        self.assertEqual(default.read_text(), "do not use this Codex home")

    def test_missing_hosts_are_skipped(self):
        shutil.rmtree(self.home / ".codex")
        shutil.rmtree(self.home / ".claude")
        run = self.run_install("v4")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse((self.home / ".claude").exists())
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_prompt_sync_plist_is_reported_without_changes_then_removed(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        plist = self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist"
        plist.write_text("old job definition")
        self.log.write_text("")
        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("残留  com.mmw.prompt-sync", check.stderr)
        self.assertEqual(plist.read_text(), "old job definition")
        self.assertNotIn("launchctl", self.log.read_text())
        run = self.run_install("v4")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(plist.exists())
        self.assertNotIn("launchctl", self.log.read_text())

    def test_advisory_hooks_are_merged_trusted_and_checked(self):
        other = {"matcher": "startup", "hooks": [
            {"type": "command", "command": "other-context-hook"}]}
        configs = (("claude", self.home / ".claude/settings.json"),
                   ("codex", self.home / ".codex/hooks.json"))
        for host, config in configs:
            data = json.loads(config.read_text()) if config.exists() else {}
            for event in ("SessionStart", "UserPromptSubmit"):
                data.setdefault("hooks", {})[event] = [other]
            config.write_text(json.dumps(data))
        for _ in range(2):
            install = self.run_install("v4")
            self.assertEqual(install.returncode, 0, install.stderr)
        for host, config in configs:
            for event, label in (("SessionStart", "session_start"),
                                 ("UserPromptSubmit", "user_prompt_submit")):
                data = json.loads(config.read_text())
                groups = data["hooks"][event]
                self.assertIn(other, groups)
                expected = f"python3 '{self.home}/.agents/skills/mmw-mode/scripts/session-start.py' {host}"
                ours = [(i, g) for i, g in enumerate(groups)
                        if any(h["command"] == expected for h in g["hooks"])]
                self.assertEqual(len(ours), 1, groups)
                index, group = ours[0]
                self.assertIsNone(group.get("matcher"))
                self.assertEqual(group["hooks"], [
                    {"type": "command", "command": expected, "timeout": 2}])
                if host == "codex":
                    key = f"{config}:{label}:{index}:0"
                    trust_path = self.home / ".codex/config.toml"
                    trusted = trust_path.read_text()
                    trust = tomllib.loads(trusted)
                    self.assertRegex(trust["hooks"]["state"][key]["trusted_hash"], r"^sha256:[0-9a-f]{64}$")
                    trust_path.write_text(trusted.replace(
                        f'[hooks.state."{key}"]\ntrusted_hash = "sha256:',
                        f'[hooks.state."{key}"]\ntrusted_hash = "invalid:'))
                    check = self.run_install("v4", "--check")
                    self.assertEqual(check.returncode, 1, check.stderr)
                    self.assertIn(key, check.stderr)
                    trust_path.write_text(trusted)
                data["hooks"][event].remove(group)
                config.write_text(json.dumps(data))
                before = config.read_bytes()
                check = self.run_install("v4", "--check")
                self.assertEqual(check.returncode, 1, check.stderr)
                self.assertIn(event, check.stderr)
                self.assertEqual(config.read_bytes(), before)
                data["hooks"][event].append(group)
                config.write_text(json.dumps(data))
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_reply_checks_migrate_without_touching_other_hooks_or_state(self):
        old_script = self.home / ".agents/skills/mmw-mode/scripts/reply-check.py"
        context_script = self.home / ".agents/skills/mmw-mode/scripts/session-start.py"
        configs = (("claude", self.home / ".claude/settings.json"),
                   ("codex", self.home / ".codex/hooks.json"))
        for host, config in configs:
            old = lambda gate: {"type": "command", "command": f"python3 '{old_script}' {gate} {host}",
                                "timeout": 30}
            hooks = {"Stop": [{"hooks": [old("stop"), {"type": "command", "command": "other-stop"}]}],
                     "PreToolUse": [{"matcher": "Artifact", "hooks": [old("artifact"),
                                    {"type": "command", "command": "other-artifact"}]}],
                     "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [
                         {"type": "command", "command": f"python3 '{context_script}' {host}", "timeout": 10}]}],
                     "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "other-prompt"}]}]}
            config.write_text(json.dumps({"hooks": hooks, "unrelated": "keep"}))
        state = self.home / ".mmw/state/reply-check/checklist.md"
        state.parent.mkdir(parents=True)
        state.write_text("keep this existing state")
        for _ in range(2):
            run = self.run_install("v4")
            self.assertEqual(run.returncode, 0, run.stderr)
        for host, config in configs:
            data = json.loads(config.read_text())
            commands = hook_commands(config)
            self.assertFalse([c for c in commands if "reply-check.py" in c])
            self.assertEqual(data["unrelated"], "keep")
            for command in ("other-stop", "other-artifact", "other-prompt"):
                self.assertEqual(commands.count(command), 1)
            self.assertEqual(sum("turn-guard.py' stop" in c for c in commands), 1)
            self.assertEqual(sum("tool-guard.py' pretool" in c for c in commands), 1)
            self.assertEqual(sum("tool-guard.py' question" in c for c in commands), 1)
        self.assertEqual(state.read_text(), "keep this existing state")
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_takes_over_a_v3_machine(self):
        self.seed_legacy_install()
        board = self.home / "Library/LaunchAgents/com.mmw.board.plist"
        self.assertIn(str(self.legacy / "board/supervisor.py"), board.read_text())
        untouched = {p: p.read_bytes() for p in (self.home / ".zshrc", self.home / ".cursor/mcp.json")}
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(str(self.v4 / "board/supervisor.py"), board.read_text())

        for where in (".agents/skills", ".claude/skills"):
            self.assertEqual(self.link("dispatch", where), str(self.v4 / "skills/dispatch"))
            self.assertEqual(self.link("mmw-mode", where), str(self.v4 / "skills/mmw-mode"))
            # A skill only v3 has is removed: the two versions are never installed together.
            self.assertFalse((self.home / where / "triage").is_symlink(), where)
        self.assertEqual(os.readlink(self.home / ".claude/CLAUDE.md"), str(self.v4 / "prompt/shared.md"))
        self.assertEqual(os.readlink(self.home / ".codex/AGENTS.md"), str(self.v4 / "prompt/shared.md"))

        for config in (self.home / ".claude/settings.json", self.home / ".codex/hooks.json"):
            commands = hook_commands(config)
            self.assertFalse([c for c in commands if "mode-hook.py" in c], commands)
            self.assertEqual(len([c for c in commands if "tool-guard.py' pretool" in c]), 1, commands)
            self.assertEqual(len([c for c in commands if "turn-guard.py' stop" in c]), 1, commands)
        self.assertIn("someone-elses-hook", hook_commands(self.home / ".claude/settings.json"))

        models = json.loads((self.home / ".mmw/models.json").read_text())
        self.assertEqual(sorted(models["rows"]), sorted(
            ["junior-worker", "senior-worker", "reviewer", "advisor", "researcher", "candidate", "retro-analyst"]))
        self.assertEqual(models["rows"]["reviewer"], V3_MODELS["rows"]["reviewer"])
        backups = list((self.home / ".mmw").glob("models.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertIn("explainer", json.loads(backups[0].read_text())["rows"])

        self.assertEqual((self.home / ".mmw/installed-root").read_text().strip(), str(self.v4))
        for path, before in untouched.items():
            self.assertEqual(path.read_bytes(), before, path)

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("HOOKS-INSTALLED", check.stdout.splitlines())
        self.assertNotIn("triage", check.stdout + check.stderr)

    def test_a_second_install_changes_nothing(self):
        self.seed_legacy_install()
        self.assertEqual(self.run_install("v4").returncode, 0)
        models = (self.home / ".mmw/models.json").read_bytes()
        backups = sorted((self.home / ".mmw").glob("models.json.bak-*"))
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.home / ".mmw/models.json").read_bytes(), models)
        self.assertEqual(sorted((self.home / ".mmw").glob("models.json.bak-*")), backups)

    def test_back_restores_shared_state_then_delegates_and_preserves_exit_code(self):
        self.seed_legacy_install()
        self.assertEqual(self.run_install("v4").returncode, 0)
        untouched = {path: path.read_bytes() for path in (
            self.home / ".zshrc", self.home / ".cursor/mcp.json",
            self.home / ".claude/settings.json", self.home / ".codex/hooks.json",
            self.v4 / "prompt/shared.md")}
        run = self.run_install("v4", "--back")
        self.assertEqual(run.returncode, 23, run.stderr)
        called = json.loads((self.home / "legacy-called.json").read_text())
        self.assertEqual(called["models"]["rows"], V3_MODELS["rows"])
        self.assertIn(str(self.legacy / "install.sh"), run.stdout)
        for where in (".agents/skills", ".claude/skills"):
            for link in (self.home / where).iterdir():
                self.assertNotIn("mmw-v4/skills/", os.readlink(link))
        self.assertFalse((self.home / ".claude/CLAUDE.md").exists())
        self.assertFalse((self.home / ".claude/CLAUDE.md").is_symlink())
        self.assertFalse((self.home / ".codex/AGENTS.md").is_symlink())
        self.assertEqual((self.home / ".codex/AGENTS.md").read_text(), "synthetic v3 prompt")
        for path, before in untouched.items():
            self.assertEqual(path.read_bytes(), before)

    def test_hooks_left_in_cursor_and_grok_are_reported_then_removed(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        scripts = self.home / ".agents/skills/dispatch/scripts"
        cursor_hooks = self.home / ".cursor/hooks.json"
        cursor_hooks.write_text(json.dumps({"version": 1, "hooks": {
            "beforeShellExecution": [
                {"command": "orca-hook", "timeout": 5},
                {"command": f"python3 '{scripts}/tool-guard.py' pretool cursor", "timeout": 10}],
            "stop": [{"command": f"python3 '{scripts}/turn-guard.py' stop cursor",
                      "timeout": 30, "loop_limit": 3}]}}))
        grok_hooks = self.home / ".grok/hooks/mmw-turn-guard.json"
        grok_hooks.parent.mkdir(parents=True)
        grok_hooks.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": f"python3 '{scripts}/turn-guard.py' stop grok",
             "timeout": 30}]}]}}))

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn(f"残留  {cursor_hooks}  beforeShellExecution", check.stderr)
        self.assertIn(f"残留  {cursor_hooks}  stop", check.stderr)
        self.assertIn(f"残留  {grok_hooks}  Stop", check.stderr)

        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(cursor_hooks.read_text()), {"version": 1, "hooks": {
            "beforeShellExecution": [{"command": "orca-hook", "timeout": 5}]}})
        self.assertFalse(grok_hooks.exists())
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_grok_and_cursor_paseo_providers_are_reported_then_removed(self):
        models = self.home / ".mmw/models.json"
        models.write_text(json.dumps(dict(V3_MODELS, runner="paseo")))
        self.assertEqual(self.run_install("v4").returncode, 0)
        config = self.home / ".paseo/config.json"
        data = json.loads(config.read_text())
        data.setdefault("agents", {})["providers"] = {
            "grok": {"extends": "acp", "label": "Grok", "command": ["grok", "agent", "stdio"]},
            "cursor": {"extends": "acp", "label": "Cursor", "command": ["cursor-agent", "acp"]},
            "pi": {"extends": "acp", "label": "Pi", "command": ["pi", "acp"]}}
        config.write_text(json.dumps(data))

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn(f"残留  {config} agents.providers.grok", check.stderr)
        self.assertIn(f"残留  {config} agents.providers.cursor", check.stderr)

        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(config.read_text())["agents"]["providers"],
                         {"pi": {"extends": "acp", "label": "Pi", "command": ["pi", "acp"]}})
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_unused_paseo_is_untouched_for_effective_runner(self):
        config = self.home / ".paseo/config.json"
        link = self.home / ".local/bin/paseo"
        models = self.home / ".mmw/models.json"
        cases = (
            ("orca", {}, False),
            ("herdr", {}, True),
            ("auto", {"TERM_PROGRAM": "orca"}, False),
            ("auto", {"HERDR_ENV": "1", "TERM_PROGRAM": "orca"}, True),
            ("auto", {"PASEO_AGENT_ID": "unused"}, False),
            ("paseo", {"MMW_RUNNER": "orca"}, True),
            ("paseo", {"MMW_RUNNER": "herdr"}, False),
            ("paseo", {"MMW_RUNNER": "auto", "HERDR_ENV": "1"}, True),
        )
        for runner, overrides, available in cases:
            for existing in (False, True):
                with self.subTest(runner=runner, overrides=overrides,
                                  available=available, existing=existing):
                    if link.is_symlink():
                        link.unlink()
                    if config.parent.exists():
                        shutil.rmtree(config.parent)
                    fake = self.bin / "paseo"
                    if available:
                        fake.write_text(FAKES["paseo"])
                        fake.chmod(0o755)
                    elif fake.exists():
                        fake.unlink()
                    if existing:
                        config.parent.mkdir()
                        config.write_bytes(b"{invalid unrelated Paseo settings\n")
                        link.parent.mkdir(parents=True, exist_ok=True)
                        link.symlink_to(fake)
                    before = (config.read_bytes() if existing else None,
                              os.readlink(link) if existing else None)
                    models.write_text(json.dumps(dict(V3_MODELS, runner=runner,
                                                       custom={"keep": True})))
                    env = dict(self.env(), **overrides)
                    self.log.write_text("")
                    for args in ((), ("--check",)):
                        run = self.run_install("v4", *args, env=env)
                        self.assertEqual(run.returncode, 0, run.stderr)
                        self.assertEqual((config.read_bytes() if config.exists() else None,
                                          os.readlink(link) if link.is_symlink() else None), before)
                        self.assertEqual(list(config.parent.glob("config.json*")),
                                         [config] if existing else [])
                    saved = json.loads(models.read_text())
                    self.assertEqual(saved["rows"]["reviewer"], V3_MODELS["rows"]["reviewer"])
                    self.assertIn("candidate", saved["rows"])
                    self.assertNotIn("explainer", saved["rows"])
                    self.assertEqual(saved["custom"], {"keep": True})
                    self.assertNotIn("paseo ", self.log.read_text())

    def test_unused_paseo_catalog_is_not_required_with_runner_override(self):
        models = self.home / ".mmw/models.json"
        models.write_text(json.dumps(dict(V3_MODELS, runner="paseo")))
        catalog = json.loads(self.catalog.read_text())
        catalog["paseo"] = {"state": "down"}
        self.catalog.write_text(json.dumps(catalog))
        env = dict(self.env(), MMW_RUNNER="orca")
        for args in ((), ("--check",)):
            run = self.run_install("v4", *args, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(models.read_text())["runner"], "paseo")
        self.assertFalse((self.home / ".paseo").exists())
        self.assertNotIn("paseo ", self.log.read_text())

    def test_paseo_first_install_bootstraps_command_before_catalog_scan(self):
        self.paseo_app.unlink()
        self.paseo_app.write_text('''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["MMW_TEST_LOG"], "a") as log:
    log.write("paseo-app " + " ".join(args) + "\\n")
if args[:2] == ["provider", "models"]:
    print(json.dumps(json.load(open(os.environ["MMW_APP_CATALOG"]))[args[2]]))
else:
    print('[{"id":"claude"},{"id":"codex"}]')
''')
        self.paseo_app.chmod(0o755)
        (self.bin / "paseo").unlink()
        local_bin = self.home / ".local/bin"
        local_bin.mkdir(parents=True)
        for host in ("claude", "codex"):
            binary = local_bin / host
            binary.write_text("#!/bin/sh\necho fake-host-1\n")
            binary.chmod(0o755)
        models = self.home / ".mmw/models.json"
        models.write_text(json.dumps(dict(V3_MODELS, runner="paseo")))
        env = dict(self.env(), HOME=str(self.home), MMW_HOME=str(self.home / ".mmw"),
                   CODEX_HOME=str(self.home / ".codex"), MMW_APP_CATALOG=str(self.catalog))
        env.pop("MMW_HOST_CATALOG")
        self.assertIsNone(shutil.which("paseo", path=env["PATH"]))
        for args in ((), ("--check",)):
            run = self.run_install("v4", *args, env=env)
            self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(os.readlink(local_bin / "paseo"), str(self.paseo_app))
        self.assertIn("paseo-app provider models codex", self.log.read_text())

    def test_paseo_override_sets_up_checks_and_reloads_only_selected_runner(self):
        catalog = json.loads(self.catalog.read_text())
        self.catalog.write_text(json.dumps({"paseo": catalog, "cli": {
            "claude": {"state": "missing"}, "codex": {"state": "missing"}}}))
        config = self.home / ".paseo/config.json"
        config.parent.mkdir()
        config.write_text('{"unrelated": {"keep": true}, "worktrees": {"other": 7}}')
        env = dict(self.env(), MMW_RUNNER="paseo", HOME=str(self.home))
        run = self.run_install("v4", env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(os.readlink(self.home / ".local/bin/paseo"),
                         str(self.paseo_app))
        self.assertEqual(json.loads(config.read_text()), {
            "unrelated": {"keep": True}, "worktrees": {
                "other": 7, "root": str(self.home / "paseo-worktrees")}, "version": 1})
        self.assertIn("paseo reload --json", self.log.read_text())
        self.assertEqual(len(list(config.parent.glob("config.json.bak-*"))), 1)
        self.assertEqual(self.run_install("v4", "--check", env=env).returncode, 0)
        (self.bin / "paseo").unlink()
        check = self.run_install("v4", "--check", env=env)
        self.assertEqual(check.returncode, 1)
        self.assertIn("缺    command -v paseo", check.stderr)

    def test_common_models_initialize_and_validate_without_paseo(self):
        models = self.home / ".mmw/models.json"
        models.unlink()
        (self.bin / "paseo").unlink()
        run = self.run_install("v4")
        self.assertEqual(run.returncode, 0, run.stderr)
        defaults = json.loads(models.read_text())
        self.assertEqual(defaults["runner"], "orca")
        self.assertEqual(defaults["rows"]["junior-worker"], {
            "host": "codex", "model": "gpt 6.1 sol", "effort": "medium"})
        self.assertFalse((self.home / ".paseo").exists())
        defaults["rows"]["junior-worker"]["model"] = "unavailable-model"
        models.write_text(json.dumps(defaults))
        before = models.read_bytes()
        for args in ((), ("--check",)):
            run = self.run_install("v4", *args)
            self.assertEqual(run.returncode, 1)
            self.assertIn("junior-worker.model", run.stderr)
            self.assertEqual(models.read_bytes(), before)

    def test_check_from_another_checkout_hands_over(self):
        other = Path(self.tmp.name) / "installed/mmw-v4"
        other.mkdir(parents=True)
        (other / "install.sh").write_text('echo "installed one checked: $*"\nexit 0\n')
        (self.home / ".mmw/installed-root").write_text(f"{other}\n")
        r = self.run_install("v4", "--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("installed one checked: --check", r.stdout)

    def test_an_orca_setup_added_after_install_is_reported_then_set(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        self.assertIn("orca project setup-update --setup setup_1 --worktree-base-path .worktrees --json",
                      self.log.read_text())
        setups = json.loads(self.orca_setups.read_text())
        setups.append({"id": "setup_2", "path": "/repos/new", "worktreeBasePath": "../worktrees"})
        self.orca_setups.write_text(json.dumps(setups))
        self.log.write_text("")

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("缺    orca setup setup_2（/repos/new）的 worktree-base-path 是 '../worktrees'，"
                      "要 .worktrees：跑一次 install.sh", check.stderr)
        self.assertNotIn("setup_1", check.stderr)
        self.assertNotIn("setup-update", self.log.read_text(), "--check writes nothing to Orca")

        self.assertEqual(self.run_install("v4").returncode, 0)
        updates = [line for line in self.log.read_text().splitlines() if "setup-update" in line]
        self.assertEqual(updates, ["orca project setup-update --setup setup_2 "
                                   "--worktree-base-path .worktrees --json"])
        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("已装  orca 的 2 个 setup，worktree-base-path 都是 .worktrees", check.stdout)

    def test_check_reports_a_gh_that_is_not_logged_in(self):
        self.assertEqual(self.run_install("v4").returncode, 0)
        env = self.env()
        env["MMW_FAKE_GH_AUTH"] = "1"
        check = self.run_install("v4", "--check", env=env)
        self.assertEqual(check.returncode, 1)
        self.assertIn("缺    gh 没登录（You are not logged into any GitHub hosts. To log in, run: "
                      "gh auth login）：跑 gh auth login", check.stderr)
        self.assertEqual(self.run_install("v4", "--check").returncode, 0)

    def test_check_names_each_missing_base_tool_and_how_to_get_it(self):
        # PATH is a directory holding only python3, uv, git and the fake gh, then the
        # system's own /usr/bin and /bin, which carry no node and no runner.
        bare = Path(self.tmp.name) / "bare-bin"
        bare.mkdir()
        for tool in ("python3", "uv", "git"):
            (bare / tool).symlink_to(shutil.which(tool))
        (bare / "gh").symlink_to(self.bin / "gh")
        env = self.env()
        env["PATH"] = f"{bare}:/usr/bin:/bin"
        check = self.run_install("v4", "--check", env=env)
        self.assertEqual(check.returncode, 1)
        self.assertIn("缺    node 不在 PATH 上：brew install node", check.stderr)
        self.assertIn("缺    runner：paseo、herdr、orca 都不在 PATH 上", check.stderr)
        for present in ("python3", "uv", "git", "gh"):
            self.assertNotIn(f"缺    {present} 不在 PATH 上", check.stderr)
        self.assertNotIn("gh 没登录", check.stderr)

    def test_check_reports_v3_rows_before_install(self):
        self.seed_legacy_install()
        (self.home / ".mmw/installed-root").write_text(f"{self.v4}\n")
        r = self.run_install("v4", "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("explainer", r.stderr)
        self.assertIn("mode-hook.py", r.stderr)

    def test_every_host_gets_subagent_depth_two_and_keeps_its_other_settings(self):
        self.seed_legacy_install()
        (self.home / ".grok").mkdir()
        grok = self.home / ".grok/config.toml"
        grok.write_text("[compat.claude]\nagents = false\n")
        codex = self.home / ".codex/config.toml"
        codex.write_text(codex.read_text() + '\n[agents]\nmax_threads = 12\nmax_depth = 1\n')
        (self.home / ".mmw/installed-root").write_text(f"{self.v4}\n")
        before = self.run_install("v4", "--check")
        self.assertEqual(before.returncode, 1)
        for host in ("claude", "codex"):
            self.assertIn(f"缺    {host} 子代理层数", before.stderr)
        self.assertNotIn("grok", before.stderr)

        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        settings = json.loads((self.home / ".claude/settings.json").read_text())
        self.assertEqual(settings["env"]["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"], "2")
        self.assertIn("someone-elses-hook", hook_commands(self.home / ".claude/settings.json"))
        agents = tomllib.loads(codex.read_text())["agents"]
        self.assertEqual(agents, {"max_threads": 12, "max_depth": 2})
        self.assertEqual(grok.read_text(), "[compat.claude]\nagents = false\n",
                         "Grok's config is not v4's to change")

        check = self.run_install("v4", "--check")
        self.assertEqual(check.returncode, 0, check.stderr)
        self.assertIn("已装  codex 子代理层数 2", check.stdout)

    @unittest.skipUnless(os.uname().sysname == "Darwin", "launchd is macOS only")
    def test_loaded_prompt_sync_is_stopped_before_migration_even_without_plist(self):
        env = dict(self.env(), HOME=str(self.home))
        target = self.home / ".codex/AGENTS.md"
        original = self.generated_prompt()
        target.write_text(original)
        job = self.launchd / "com.mmw.prompt-sync"
        for has_plist in (True, False):
            with self.subTest(has_plist=has_plist):
                if target.is_symlink():
                    target.unlink()
                target.write_text(original)
                job.touch()
                plist = self.home / "Library/LaunchAgents/com.mmw.prompt-sync.plist"
                if has_plist:
                    plist.parent.mkdir(parents=True, exist_ok=True)
                    plist.write_text("old job definition")
                self.log.write_text("")
                check = self.run_install("v4", "--check", env=env)
                self.assertEqual(check.returncode, 1)
                self.assertIn("残留  com.mmw.prompt-sync", check.stderr)
                self.assertTrue(job.exists())
                self.assertEqual(target.read_text(), original)
                self.assertNotIn("launchctl bootout", self.log.read_text())
                run = self.run_install("v4", env=env)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn("/com.mmw.prompt-sync", self.log.read_text())
                self.assertNotIn("launchctl bootstrap gui/" + str(os.getuid()) + " " + str(plist), self.log.read_text())
                self.assertFalse(job.exists())
                self.assertFalse(plist.exists())
                self.assertTrue(target.is_symlink())
                self.assertEqual(self.run_install("v4", "--check", env=env).returncode, 0)

    @unittest.skipUnless(os.uname().sysname == "Darwin", "launchd is macOS only")
    def test_prompt_migration_stops_if_the_old_job_cannot_stop(self):
        env = dict(self.env(), HOME=str(self.home), MMW_FAKE_LAUNCHD_STUCK="com.mmw.prompt-sync")
        target = self.home / ".codex/AGENTS.md"
        original = self.generated_prompt()
        target.write_text(original)
        (self.launchd / "com.mmw.prompt-sync").touch()
        run = self.run_install("v4", env=env)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn("com.mmw.prompt-sync 仍在运行", run.stderr)
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_text(), original)

    def test_never_touches_memory_and_writes_the_board_job(self):
        r = self.run_install("v4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("nmem", self.log.read_text())
        self.assertNotIn("launchctl", self.log.read_text())
        board = self.home / "Library/LaunchAgents/com.mmw.board.plist"
        self.assertIn(str(self.v4 / "board/supervisor.py"), board.read_text())
        self.assertFalse((self.home / ".zshrc").exists())
        self.assertFalse((self.home / ".cursor/mcp.json").exists())


if __name__ == "__main__":
    unittest.main()
