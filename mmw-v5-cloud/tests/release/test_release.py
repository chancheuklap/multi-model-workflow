from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/release-mmw-v5.py"


class ReleaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mmw-release-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "--bare", "--quiet", str(self.remote)], check=True)
        self.git("init", "--quiet", "--initial-branch=dev")
        self.git("config", "user.name", "Release test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("remote", "add", "origin", str(self.remote))
        self.write("scripts/release-mmw-v5.py", SCRIPT.read_text())
        for path in ("plugin.json", ".cursor-plugin/plugin.json"):
            self.write("mmw-v5-cloud/" + path, json.dumps({"name": "mmw-v5-cloud", "version": "5.0.0-beta.2"}))
        for path, text in {
            "models.json": '{"rows":{}}',
            "skills/example/SKILL.md": "Original skill",
            "tools/dispatch/scripts/dispatch.sh": "#!/bin/sh\nexit 0\n",
            "board/page/index.html": "Board", "tests/private.txt": "not installed", "AGENTS.md": "development only",
        }.items():
            self.write("mmw-v5-cloud/" + path, text)
        (self.root / "mmw-v5-cloud/tools/dispatch/scripts/dispatch.sh").chmod(0o755)
        self.commit("initial")
        self.bin = Path(self.temp.name) / "bin"
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        GITHUB_REPOSITORY="example/mmw", GITHUB_EVENT_NAME="push", GITHUB_REF="refs/heads/main",
                        GITHUB_SHA=self.git("rev-parse", "HEAD").stdout.strip(), GH_TOKEN="test-only")
        self.log = Path(self.temp.name) / "gh.jsonl"
        self.env["RELEASE_TEST_LOG"] = str(self.log)
        self.write_gh()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", message)

    def command(self, *args, **env):
        return subprocess.run([sys.executable, str(self.root / "scripts/release-mmw-v5.py"), *args],
                              cwd=self.root, env=dict(self.env, **env), capture_output=True, text=True)

    def write_gh(self):
        gh = self.bin / "gh"
        gh.write_text("#!" + sys.executable + "\n" + '''
import json,os,pathlib,subprocess,sys,zipfile
a=sys.argv[1:]
log=pathlib.Path(os.environ['RELEASE_TEST_LOG'])
with log.open('a') as out:out.write(json.dumps(a)+'\\n')
state=log.with_suffix('.state')
if a[:2]==['release','view']:
 if os.environ.get('RELEASE_TEST_NETWORK_ERROR'):
  print('network unavailable',file=sys.stderr);sys.exit(1)
 if not state.exists():print('release not found',file=sys.stderr);sys.exit(1)
 print('https://example.invalid/release' if '--jq' in a else json.dumps({'url':'https://example.invalid/release'}))
elif a[:2] in (['release','create'],['release','upload']):
 archive=pathlib.Path(a[3])
 with zipfile.ZipFile(archive) as z:
  data={'version':json.loads(z.read('mmw-v5-cloud/plugin.json'))['version'],'files':z.namelist()}
 log.with_suffix('.archive').write_text(json.dumps(data))
 if a[1]=='create':
  subprocess.run(['git','push','--quiet','origin', 'HEAD:refs/tags/'+a[2]],check=True)
 state.write_text('published')
else:
 print('unexpected gh command '+repr(a),file=sys.stderr);sys.exit(2)
''')
        gh.chmod(0o755)

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_both_host_marketplaces_select_the_same_plugin(self):
        for name in ('.agents/plugins/marketplace.json', '.cursor-plugin/marketplace.json'):
            entries = json.loads((ROOT / name).read_text())['plugins']
            self.assertEqual([entry['name'] for entry in entries], ['mmw-v5-cloud'])
            source = entries[0]['source']
            path = source['path'] if isinstance(source, dict) else source
            self.assertEqual((ROOT / path).resolve(), ROOT / 'mmw-v5-cloud')

    def test_bump_prepares_dev_without_committing_or_publishing(self):
        before = self.git("rev-parse", "HEAD").stdout
        result = self.command("bump")
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in ("plugin.json", ".cursor-plugin/plugin.json"):
            self.assertEqual(json.loads((self.root / "mmw-v5-cloud" / path).read_text())["version"], "5.0.0-beta.3")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        self.assertEqual(self.calls(), [])

    def test_stable_version_increments_patch(self):
        for path in ("plugin.json", ".cursor-plugin/plugin.json"):
            self.write("mmw-v5-cloud/" + path, json.dumps({"name": "mmw-v5-cloud", "version": "5.0.4"}))
        self.assertEqual(self.command("bump").returncode, 0)
        self.assertEqual(json.loads((self.root / "mmw-v5-cloud/plugin.json").read_text())["version"], "5.0.5")

    def test_bump_on_main_changes_nothing(self):
        self.git("switch", "--quiet", "-c", "main")
        result = self.command("bump")
        self.assertEqual(result.returncode, 2)
        self.assertIn("on dev", result.stderr)
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_package_uses_committed_files_and_preserves_tools(self):
        self.write("mmw-v5-cloud/skills/example/SKILL.md", "uncommitted edit")
        self.write("mmw-v5-cloud/tools/untracked-secret.txt", "not committed")
        output = Path(self.temp.name) / "plugin.zip"
        result = self.command("package", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read("mmw-v5-cloud/skills/example/SKILL.md"), b"Original skill")
            self.assertIn("mmw-v5-cloud/plugin.json", archive.namelist())
            self.assertIn("mmw-v5-cloud/.cursor-plugin/plugin.json", archive.namelist())
            self.assertIn("mmw-v5-cloud/board/page/index.html", archive.namelist())
            info = archive.getinfo("mmw-v5-cloud/tools/dispatch/scripts/dispatch.sh")
            self.assertTrue((info.external_attr >> 16) & 0o111)
            self.assertFalse(any("private.txt" in p or "AGENTS.md" in p or "secret" in p for p in archive.namelist()))

    def complete_cloud_fixture(self):
        for path, text in {
            "plugin.json": '{"name":"mmw-v5-cloud","version":"5.0.0-beta.2"}',
            ".cursor-plugin/plugin.json": '{"name":"mmw-v5-cloud","version":"5.0.0-beta.2"}',
            "skills/example/SKILL.md": "Original skill",
            "skills/dispatch/SKILL.md": "Cloud dispatch",
            "models.json": '{"max_workers":3,"rows":{}}',
            "tools/dispatch/scripts/dispatch.sh": "#!/bin/bash\nexit 0\n",
            "board/page/index.html": "Cloud board",
            "board/page/board-layout.mjs": "cloud edition geometry",
            "board/page/board-logic.mjs": "native cloud facts",
        }.items():
            self.write("mmw-v5-cloud/" + path, text)

    def test_bump_updates_the_cloud_edition_and_leaves_the_retired_tree(self):
        self.write("mmw-v5/plugin.json", json.dumps({"name": "mmw-v5", "version": "5.0.0-beta.2"}))
        result = self.command("bump")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.root / "mmw-v5-cloud/plugin.json").read_text())["version"], "5.0.0-beta.3")
        self.assertEqual(json.loads((self.root / "mmw-v5/plugin.json").read_text())["version"], "5.0.0-beta.2")

    def test_cloud_archive_uses_only_its_own_complete_directory(self):
        self.complete_cloud_fixture()
        self.write("mmw-v5-cloud/skills/dispatch/SKILL.md", "Cloud dispatch")
        self.write("mmw-v5-cloud/models.json", '{"max_workers":3,"rows":{}}')
        self.write("mmw-v5-cloud/tools/dispatch/scripts/dispatch.sh", "#!/bin/bash\nexit 0\n")
        self.write("mmw-v5/skills/dispatch/SKILL.md", "Local dispatch")
        self.write("mmw-v5/tools/dispatch/scripts/relay.py", "local only")
        self.write("mmw-v5/board/page/board-logic.mjs", "shared geometry")
        self.write("mmw-v5-cloud/board/page/board-logic.mjs", "native cloud facts")
        self.commit("cloud edition")
        self.write("mmw-v5-cloud/models.json", "uncommitted data")
        self.git("rm", "-rq", "mmw-v5")
        self.git("commit", "--quiet", "-m", "cloud edition stands alone")
        output = Path(self.temp.name) / "cloud.zip"
        result = self.command("package", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertEqual(archive.read("mmw-v5-cloud/skills/example/SKILL.md"), b"Original skill")
            self.assertEqual(archive.read("mmw-v5-cloud/skills/dispatch/SKILL.md"), b"Cloud dispatch")
            self.assertEqual(archive.read("mmw-v5-cloud/board/page/board-layout.mjs"), b"cloud edition geometry")
            self.assertEqual(archive.read("mmw-v5-cloud/board/page/board-logic.mjs"), b"native cloud facts")
            self.assertEqual(json.loads(archive.read("mmw-v5-cloud/models.json"))["max_workers"], 3)
            self.assertEqual(json.loads(archive.read("mmw-v5-cloud/plugin.json"))["version"], "5.0.0-beta.2")
            self.assertFalse(any("relay" in name or "runners" in name or "private.txt" in name for name in names))

    def test_publication_attaches_the_cloud_archive_without_tests(self):
        self.complete_cloud_fixture()
        self.write("mmw-v5-cloud/skills/dispatch/SKILL.md", "Cloud dispatch")
        self.write("mmw-v5-cloud/models.json", '{"max_workers":3,"rows":{}}')
        self.commit("cloud edition")
        result = self.command("publish", GITHUB_SHA=self.git("rev-parse", "HEAD").stdout.strip())
        self.assertEqual(result.returncode, 0, result.stderr)
        create = next(row for row in self.calls() if row[:2] == ["release", "create"])
        self.assertTrue(any(arg.endswith("mmw-v5-cloud.zip") for arg in create))
        self.assertFalse(any(arg.endswith("mmw-v5-5.0.0-beta.2.zip") for arg in create))
        self.assertFalse(any(row[:2] == ["workflow", "run"] for row in self.calls()))

    def test_mismatched_committed_versions_are_not_packaged(self):
        self.write("mmw-v5-cloud/.cursor-plugin/plugin.json", '{"name":"mmw-v5-cloud","version":"5.0.0-beta.1"}')
        self.commit("mismatch")
        result = self.command("package", "--output", str(Path(self.temp.name) / "bad.zip"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("same name and version", result.stderr)

    def test_dev_and_pr_events_cannot_publish(self):
        for changes in ({"GITHUB_REF": "refs/heads/dev"}, {"GITHUB_EVENT_NAME": "pull_request"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.command("publish", **changes).returncode, 2)
        self.assertEqual(self.calls(), [])

    def test_main_publishes_prepared_version_and_retry_reuses_release(self):
        before = self.git("rev-parse", "HEAD").stdout
        result = self.command("publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        create = next(row for row in self.calls() if row[:2] == ["release", "create"])
        self.assertEqual(create[2], "v5.0.0-beta.2")
        self.assertIn("--prerelease", create)
        self.assertEqual(create[create.index("--target") + 1], before.strip())
        archive = json.loads(self.log.with_suffix(".archive").read_text())
        self.assertEqual(archive["version"], "5.0.0-beta.2")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, before)
        result = self.command("publish")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(row[:2] == ["release", "create"] for row in self.calls()), 1)
        self.assertTrue(any(row[:2] == ["release", "upload"] for row in self.calls()))

    def test_existing_version_at_another_commit_cannot_be_overwritten(self):
        self.git("push", "--quiet", "origin", "HEAD:refs/tags/v5.0.0-beta.2")
        self.write("mmw-v5-cloud/skills/example/SKILL.md", "changed without a version bump")
        self.commit("next code")
        result = self.command("publish", GITHUB_SHA=self.git("rev-parse", "HEAD").stdout.strip())
        self.assertEqual(result.returncode, 2)
        self.assertIn("another commit", result.stderr)
        self.assertEqual(self.calls(), [])

    def test_failed_release_lookup_does_not_attempt_a_write(self):
        result = self.command("publish", RELEASE_TEST_NETWORK_ERROR="1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("network unavailable", result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.calls()[0][:2], ["release", "view"])


if __name__ == "__main__":
    unittest.main()
