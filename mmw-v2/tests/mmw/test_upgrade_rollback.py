"""Real installs across the pre-B0/new-version boundary in one disposable checkout."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
REPO = MMW.parent
OLD = "abdf8feb2ca969cc7a58afa27cd8b00546de5d29"
ROLES = ("junior-worker", "senior-worker", "reviewer", "advisor")
SWEPT = (
    ".claude/settings.json", ".codex/hooks.json", ".cursor/hooks.json",
    ".grok/hooks/mmw-verify-ticket.json", ".grok/hooks/mmw-turn.json",
    ".grok/hooks/mmw-discipline.json", ".grok/hooks/mmw-turn-guard.json",
)

FAKE = '''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['ROLLBACK_CALLS'], 'a') as log:
    log.write(json.dumps([name, *args]) + '\\n')
plain = [arg for arg in args if arg != '--json']
result = None
if name == 'nmem':
    if plain == ['spaces', 'show', 'mmw-toolbox']:
        result = {'id': 'mmw-toolbox', 'name': 'MMW Toolbox',
                  'defaultRetrievalMode': 'strict', 'sharedSpaceIds': []}
    elif plain[:2] == ['agents', 'show'] and plain[2] in ('mmw-worker', 'mmw-reviewer'):
        role = plain[2].removeprefix('mmw-')
        result = {'id': plain[2], 'displayName': 'MMW ' + role.title(),
                  'role': role, 'defaultSpaceId': 'mmw-toolbox'}
    elif plain == ['config', 'mcp', 'show', '--host', 'cursor']:
        result = {'config': {'mcpServers': {'nowledge-mem': {
            'url': 'http://nowledge.invalid/mcp', 'headers': {}}}}}
elif name == 'orca':
    if plain[:2] == ['project', 'setups']:
        result = {'ok': True, 'result': {'setups': []}}
    elif plain[:2] == ['repo', 'list']:
        result = {'ok': True, 'result': {'repos': []}}
    elif plain == ['agent-context']:
        uses = json.loads(Path(os.environ['ROLLBACK_USES']).read_text())['orca']
        result = {'commands': [{'command': cmd, 'flags': flags}
                               for cmd, flags in uses.items()]}
elif name in ('paseo', 'herdr') and args and args[-1] in ('--help', '-h'):
    cmd = ' '.join(args[:-1])
    flags = json.loads(Path(os.environ['ROLLBACK_USES']).read_text())[name].get(cmd, [])
    print('Usage: ' + name + (' ' + cmd if cmd else '') + ' ' + ' '.join(flags))
if result is not None:
    print(json.dumps(result))
'''


def remove_tree(path):
    last = None
    for _ in range(8):
        if not path.exists():
            return
        try:
            shutil.rmtree(path)
        except OSError as exc:
            last = exc
            time.sleep(0.1)
            continue
        if not path.exists():
            return
    raise AssertionError(f"could not remove {path}: {last}")


class UpgradeRollback(unittest.TestCase):
    def setUp(self):
        found = subprocess.run(["git", "-C", str(REPO), "cat-file", "-e", f"{OLD}^{{commit}}"],
                               capture_output=True, text=True)
        if found.returncode:
            self.fail(f"required rollback commit is missing: {OLD}")
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(remove_tree, self.root)
        self.home = self.root / "home"
        self.user_home = self.root / "user-home"
        self.user_home.mkdir()
        self.clone = self.root / "clone"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.jsonl"
        self.new = self.git(REPO, "rev-parse", "HEAD").stdout.strip()
        self.git(REPO, "clone", "--local", "--no-checkout", str(REPO), str(self.clone))
        catalog, uses = {}, {name: {} for name in ("orca", "paseo", "herdr")}
        for ref, skill in ((OLD, "dispatch"), (self.new, "mmw")):
            hosts = json.loads(self.git(REPO, "show", f"{ref}:mmw-v2/skills/{skill}/hosts.json").stdout)
            for row in hosts["defaults"]:
                model = row["model"].split("[", 1)[0]
                offering = {"id": model.replace(" ", "-"), "name": model,
                            "thinkingOptionIds": ["off", "low", "medium", "high", "xhigh", "max"]}
                entries = catalog.setdefault(row["host"], [])
                if offering not in entries:
                    entries.append(offering)
            for runner in uses:
                source = self.git(REPO, "show", f"{ref}:mmw-v2/skills/{skill}/scripts/runners/{runner}.sh").stdout
                for line in source.splitlines():
                    if not line.startswith("# MMW_USES:"):
                        continue
                    tokens = line.split(":", 1)[1].split()
                    cmd = " ".join(token for token in tokens if not token.startswith("-"))
                    flags = uses[runner].setdefault(cmd, [])
                    for token in tokens:
                        if token.startswith("-") and token not in flags:
                            flags.append(token)
        self.catalog = self.root / "catalog.json"
        self.catalog.write_text(json.dumps(catalog))
        self.uses = self.root / "uses.json"
        self.uses.write_text(json.dumps(uses))
        for name in ("nmem", "orca", "paseo", "herdr", "launchctl", "gh",
                     "claude", "codex", "grok", "cursor-agent", "pi"):
            path = self.bin / name
            path.write_text(FAKE)
            path.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        uv = shutil.which("uv")
        self.assertIsNotNone(uv, "uv is required for the install wiring check")
        (self.bin / "uv").symlink_to(uv)
        cache = subprocess.run([uv, "cache", "dir"], check=True, capture_output=True, text=True).stdout.strip()
        self.env = {
            "HOME": str(self.user_home), "MMW_V2_HOME": str(self.home),
            "MMW_HOME": str(self.home / ".mmw"), "MMW_HOST_CATALOG": str(self.catalog),
            "PATH": str(self.bin) + os.pathsep + os.defpath, "UV_CACHE_DIR": cache,
            "PYTHONDONTWRITEBYTECODE": "1", "ROLLBACK_CALLS": str(self.log),
            "ROLLBACK_USES": str(self.uses),
        }
        for name in (".claude", ".codex", ".grok", ".cursor"):
            (self.home / name).mkdir(parents=True)
        (self.home / ".codex/config.toml").write_text("")
        (self.home / ".grok/config.toml").write_text("[compat.claude]\nagents = false\n")
        self.installed = self.clone / "mmw-v2"
        self.steps = 0

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                              text=True, capture_output=True)

    def checkout(self, ref):
        self.git(self.clone, "checkout", "--detach", ref)

    def command(self, *args, expected=0):
        result = subprocess.run([str(arg) for arg in args], cwd=self.clone, env=self.env,
                                text=True, capture_output=True, timeout=120)
        self.assertEqual(result.returncode, expected,
                         f"{args}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
        self.assertEqual((self.home / ".mmw/installed-root").read_text().strip(), str(self.installed))
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        forbidden = {"launchctl", "claude", "codex", "grok", "cursor-agent", "pi"}
        self.assertFalse(any(call[0] in forbidden or call[:2] == ["paseo", "reload"] for call in calls), calls)
        return result

    def install(self, ref, check=False, expected=0):
        self.checkout(ref)
        result = self.command("bash", self.installed / "install.sh",
                              *(["--check"] if check else []), expected=expected)
        if check and expected == 0:
            self.assertTrue(any(line.startswith("齐了：") for line in result.stdout.splitlines()), result.stdout)
        self.steps += 1
        return result

    def upgraded(self):
        self.install(OLD)
        self.install(OLD, check=True)
        self.install(self.new)
        self.install(self.new, check=True)
        self.command("python3", self.installed / "skills/mmw/scripts/models.py",
                     "config", "set", "researcher", "codex", "gpt 6 sol", "high")
        self.steps += 1

    def copied_links(self):
        copies = (self.home / ".mmw/skill-copies").resolve()
        return {str(path) for folder in (".agents/skills", ".claude/skills")
                for path in (self.home / folder).iterdir()
                if path.is_symlink() and path.resolve().is_relative_to(copies)}

    def handlers(self, relative):
        path = self.home / relative
        if not path.exists():
            return {}
        hooks = json.loads(path.read_text()).get("hooks", {})
        return {event: [handler.get("command", "")
                        for entry in entries
                        for handler in ([entry] if relative == ".cursor/hooks.json" else entry.get("hooks", []))]
                for event, entries in hooks.items()}

    def prepare(self, expected=0):
        return self.command("python3", self.installed / "migrations/prepare-rollback.py", expected=expected)

    def test_upgrade_rollback_full_path(self):
        self.upgraded()
        plist = (self.home / "Library/LaunchAgents/com.mmw.board.plist").read_bytes()
        config = json.loads((self.home / ".mmw/models.json").read_text())
        trusted = (self.home / ".codex/config.toml").read_bytes()
        links = self.copied_links()
        self.assertTrue(links)
        self.prepare()
        self.steps += 1
        self.assertEqual(self.copied_links(), set())
        after = json.loads((self.home / ".mmw/models.json").read_text())
        self.assertEqual(after, {**config, "rows": {key: value for key, value in config["rows"].items() if key != "researcher"}})
        self.assertEqual(json.loads((self.home / ".mmw/models-researcher-before-rollback.json").read_text()), config["rows"]["researcher"])
        self.assertEqual((self.home / ".codex/config.toml").read_bytes(), trusted)
        self.assertFalse((self.home / ".mmw/board-bootstrapped-commit").exists())
        self.assertTrue((self.home / ".mmw/bin/hook-launcher").is_file())
        self.assertTrue((self.home / ".mmw/skill-copies").is_dir())
        for relative in SWEPT:
            self.assertFalse(any("hook-launcher" in command for commands in self.handlers(relative).values() for command in commands))
            path = self.home / relative
            if path.exists():
                self.assertTrue(list(path.parent.glob(path.name + ".bak-*")), relative)
        snapshot = {str(path.relative_to(self.home)): (path.read_bytes(), path.stat().st_mtime_ns)
                    for path in self.home.rglob("*") if path.is_file() and not path.is_symlink()}
        rerun = self.prepare()
        self.assertEqual(rerun.stdout, "")
        self.assertEqual(snapshot, {str(path.relative_to(self.home)): (path.read_bytes(), path.stat().st_mtime_ns)
                                    for path in self.home.rglob("*") if path.is_file() and not path.is_symlink()})
        self.install(OLD)
        self.assertEqual((self.home / "Library/LaunchAgents/com.mmw.board.plist").read_bytes(), plist)
        self.install(OLD, check=True)
        for relative in SWEPT:
            self.assertFalse(any("hook-launcher" in command for commands in self.handlers(relative).values() for command in commands))
        for role in ROLES:
            self.command("python3", self.installed / "skills/dispatch/scripts/models.py", "row", role)
        self.steps += 1
        result = self.install(self.new)
        self.assertTrue(any(line.startswith("重载  com.mmw.board") for line in result.stdout.splitlines()), result.stdout)
        self.install(self.new, check=True)
        self.assertEqual(self.steps, 11)
        print(f"UPGRADE ROLLBACK OK {self.steps} steps")


if __name__ == "__main__":
    unittest.main()
