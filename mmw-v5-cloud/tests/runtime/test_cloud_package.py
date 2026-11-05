from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[3]


class InstalledCloudPackage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mmw-cloud-package-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
                        PYTHONDONTWRITEBYTECODE='1')
        source = self.base / 'source'
        shutil.copytree(ROOT / 'mmw-v5-cloud', source / 'mmw-v5-cloud',
                        ignore=shutil.ignore_patterns('__pycache__'))
        (source / 'scripts').mkdir()
        shutil.copy2(ROOT / 'scripts/release-mmw-v5.py', source / 'scripts')
        self.init_repo(source)
        self.git(source, 'add', '.')
        self.git(source, 'commit', '-qm', 'candidate')
        self.archive = self.base / 'cloud.zip'
        result = self.run_command(source, sys.executable, str(source / 'scripts/release-mmw-v5.py'),
                                  'package', '--output', str(self.archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.snapshot = self.base / 'snapshot.zip'
        self.git(source, 'archive', '--format=zip', '--prefix=snapshot/', f'--output={self.snapshot}', 'HEAD')
        shutil.rmtree(source)
        self.project = self.base / 'consumer'
        self.project.mkdir()
        self.init_repo(self.project)
        binary = self.base / 'bin'
        binary.mkdir()
        curl = binary / 'curl'
        curl.write_text('#!' + sys.executable + '\n' + '''import os,pathlib,shutil,sys,zipfile
output=pathlib.Path(sys.argv[sys.argv.index('-o')+1])
if any(arg.endswith('/plugin.json') for arg in sys.argv):
 with zipfile.ZipFile(os.environ['CLOUD_TEST_ARCHIVE']) as archive:
  output.write_bytes(archive.read('mmw-v5-cloud/plugin.json'))
elif any('/zipball/' in arg for arg in sys.argv):
 shutil.copyfile(os.environ['CLOUD_TEST_SNAPSHOT'],output)
else:
 shutil.copyfile(os.environ['CLOUD_TEST_ARCHIVE'],output)
''')
        curl.chmod(0o755)
        self.env.update(PATH=str(binary) + os.pathsep + self.env['PATH'],
                        CLOUD_TEST_ARCHIVE=str(self.archive), CLOUD_TEST_SNAPSHOT=str(self.snapshot))

    def run_command(self, cwd, *args):
        return subprocess.run(args, cwd=cwd, env=self.env, capture_output=True, text=True)

    def git(self, cwd, *args):
        result = self.run_command(cwd, 'git', *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_repo(self, path):
        self.git(path, 'init', '-q', '-b', 'night/test')
        self.git(path, 'config', 'user.name', 'Package test')
        self.git(path, 'config', 'user.email', 'test@example.invalid')

    def install(self, host, *options, cwd=None):
        result = self.run_command(cwd or self.project, 'bash', str(ROOT / 'scripts/install-mmw-v5-cloud.sh'),
                                  '--host', host, *options)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.project / ('.agents' if host == 'codex' else '.cursor')

    def test_cloud_edition_includes_research_and_current_roles(self):
        names = {p.parent.name for p in (ROOT / 'mmw-v5-cloud/skills').glob('*/SKILL.md')}
        self.assertTrue({'dispatch', 'research', 'how', 'code-review'} <= names)

    def test_complete_runtime_installs_for_both_hosts_and_uses_its_own_config(self):
        installations = [self.install('cursor'), self.install('codex')]
        snapshots = {}
        for installation in installations:
            with self.subTest(installation=installation.name):
                host = 'codex' if installation.name == '.agents' else 'cursor'
                config = installation / 'models.json'
                settings = json.loads(config.read_text())
                settings['rows'][host]['review-axis']['model'] = 'chosen-' + host
                config.write_text(json.dumps(settings))
                snapshots[host] = settings['rows'][host]['review-axis'].copy()
                for relative in ['skills/dispatch/SKILL.md', 'skills/dispatch/references/dispatch-reviewer.md',
                                 'skills/write-tests/SKILL.md', 'board/page/app.mjs', 'board/gates.py']:
                    self.assertTrue((installation / relative).is_file(), relative)
                self.assertTrue(os.access(installation / 'tools/dispatch/scripts/dispatch.sh', os.X_OK))
                for skill in ['dispatch', 'code-review']:
                    for path in (installation / 'skills' / skill).rglob('*.md'):
                        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                            if '://' not in target and not target.startswith('#'):
                                self.assertTrue((path.parent / target.split('#')[0]).is_file(), f'{path}: {target}')
                for path in (installation / 'board/page').rglob('*'):
                    if path.suffix not in ('.mjs', '.css'): continue
                    for target in re.findall(r'(?:from\s*|@import\s*)["\'](\.[^"\']+)["\']', path.read_text()):
                        self.assertTrue((path.parent / target).is_file(), f'{path}: {target}')
        self.git(self.project, 'add', '.')
        self.git(self.project, 'commit', '-qm', 'installed runtimes')
        fixed = self.git(self.project, 'rev-parse', 'HEAD')
        for installation, host in zip(installations, ['cursor', 'codex']):
            config = installation / 'models.json'
            changed = json.loads(config.read_text())
            changed['rows'][host]['review-axis']['model'] = 'next-run-only'
            config.write_text(json.dumps(changed))
            result = self.run_command(self.project, sys.executable,
                                      str(installation / 'tools/dispatch/scripts/models.py'),
                                      'row', 'review-axis', '--at', fixed)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), snapshots[host])
            self.check_board_settings(installation, host)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertTrue(all(name.startswith('mmw-v5-cloud/') for name in archive.namelist()))
            self.assertFalse(any(x in name for name in archive.namelist()
                                 for x in ['/runners/', '/relay.py', '/events.py', '/children.md']))

    def check_board_settings(self, installation, host):
        process = subprocess.Popen([sys.executable, str(installation / 'board/server.py'), '--port', '0'],
                                   cwd=self.project, env=self.env, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL, text=True)
        try:
            address = process.stdout.readline().strip()
            self.assertTrue(address.startswith('http://127.0.0.1:'), address)
            with urllib.request.urlopen(address, timeout=5) as response:
                page = response.read().decode()
            token = re.search(r'name="mmw-page-token" content="([^"]+)"', page).group(1)
            with urllib.request.urlopen(address + '/api/settings', timeout=5) as response:
                settings = json.load(response)
            self.assertEqual(settings['host'], host)
            self.assertEqual(settings['store'], str(installation / 'models.json'))
            previous = json.loads((installation / 'models.json').read_text())
            other_install = self.project / ('.cursor' if host == 'codex' else '.agents') / 'models.json'
            other_bytes = other_install.read_bytes()
            settings['rows'][host]['review-axis']['model'] = 'saved-' + host
            payload = {'rows': {host: settings['rows'][host]}}
            request = urllib.request.Request(address + '/api/settings', method='PUT',
                                             data=json.dumps(payload).encode(),
                                             headers={'Content-Type': 'application/json', 'Origin': address,
                                                      'X-MMW-Token': token})
            with urllib.request.urlopen(request, timeout=5) as response:
                self.assertTrue(json.load(response)['saved'])
            saved = json.loads((installation / 'models.json').read_text())
            other_host = 'cursor' if host == 'codex' else 'codex'
            self.assertEqual(saved['rows'][host]['review-axis']['model'], 'saved-' + host)
            self.assertEqual(saved['rows'][other_host], previous['rows'][other_host])
            self.assertNotIn('max_workers', saved)
            self.assertEqual(other_install.read_bytes(), other_bytes)
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()

    def test_codex_migrates_legacy_choices_once_and_updates_preserve_project_files(self):
        legacy = self.install('cursor') / 'models.json'
        previous = json.loads(legacy.read_text())
        previous['rows']['codex']['senior-worker']['model'] = 'legacy-codex-choice'
        legacy.write_text(json.dumps(previous))
        before = legacy.read_bytes()
        installation = self.install('codex')
        settings = installation / 'models.json'
        migrated = json.loads(settings.read_text())
        self.assertEqual(migrated['rows']['codex'], previous['rows']['codex'])
        self.assertEqual(legacy.read_bytes(), before)
        migrated['rows']['codex']['senior-worker']['model'] = 'kept-existing-choice'
        settings.write_text(json.dumps(migrated))
        custom = installation / 'skills/owner/SKILL.md'
        custom.parent.mkdir()
        custom.write_text('Keep owner skill\n')
        nested = self.project / 'src'
        nested.mkdir()
        self.install('codex', '--ref', 'candidate', cwd=nested)
        self.assertEqual(json.loads(settings.read_text()), migrated)
        self.assertEqual(custom.read_text(), 'Keep owner skill\n')
        self.assertEqual(legacy.read_bytes(), before)

    def test_cursor_updates_preserve_configuration_and_rules(self):
        installation = self.install('cursor', '--ref', 'candidate')
        config = installation / 'models.json'
        settings = json.loads(config.read_text())
        settings['rows']['cursor']['senior-worker']['model'] = 'kept-cursor-choice'
        config.write_text(json.dumps(settings))
        rules = installation / 'rules/owner.mdc'
        rules.parent.mkdir()
        rules.write_text('Keep project rules\n')
        self.install('cursor')
        self.assertEqual(json.loads(config.read_text()), settings)
        self.assertEqual(rules.read_text(), 'Keep project rules\n')
        self.assertFalse((self.project / '.agents').exists())

    def test_installer_requires_a_known_explicit_host(self):
        for args in [[], ['--host', 'unknown'], ['--host'], ['--ref', 'candidate']]:
            result = self.run_command(self.project, 'bash', str(ROOT / 'scripts/install-mmw-v5-cloud.sh'), *args)
            self.assertEqual(result.returncode, 2, args)
        self.assertFalse((self.project / '.cursor').exists())
        self.assertFalse((self.project / '.agents').exists())


if __name__ == '__main__':
    unittest.main()
