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
        self.project = self.base / 'consumer'
        self.project.mkdir()
        self.init_repo(self.project)
        binary = self.base / 'bin'
        binary.mkdir()
        curl = binary / 'curl'
        curl.write_text('#!' + sys.executable + '\n' + '''import json,os,pathlib,shutil,sys
url=next(arg for arg in sys.argv if arg.startswith('https://'))
with open(os.environ['CLOUD_TEST_CURL_LOG'],'a') as log:log.write(json.dumps(url)+'\\n')
if url.endswith('/scripts/install-mmw-v5-cloud.sh'):
 sys.stdout.write(pathlib.Path(os.environ['CLOUD_TEST_INSTALLER']).read_text())
elif url.endswith('/releases/latest/download/mmw-v5-cloud.zip'):
 if os.environ.get('CLOUD_TEST_DOWNLOAD_FAIL'):
  print('download failed',file=sys.stderr);sys.exit(22)
 output=pathlib.Path(sys.argv[sys.argv.index('-o')+1])
 shutil.copyfile(os.environ['CLOUD_TEST_ARCHIVE'],output)
else:
 print('unexpected download '+url,file=sys.stderr);sys.exit(2)
''')
        curl.chmod(0o755)
        self.env.update(PATH=str(binary) + os.pathsep + self.env['PATH'],
                        CLOUD_TEST_ARCHIVE=str(self.archive),
                        CLOUD_TEST_INSTALLER=str(ROOT / 'scripts/install-mmw-v5-cloud.sh'),
                        CLOUD_TEST_CURL_LOG=str(self.base / 'curl.jsonl'))

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
        return self.project / '.agents'

    def test_cloud_edition_includes_research_and_current_roles(self):
        names = {p.parent.name for p in (ROOT / 'mmw-v5-cloud/skills').glob('*/SKILL.md')}
        self.assertTrue({'dispatch', 'research', 'how', 'code-review'} <= names)

    def test_researcher_dispatch_preserves_each_callers_prompt(self):
        installations = {host: self.install(host) for host in ('cursor', 'codex')}
        selected = {}
        for host, installation in installations.items():
            path = installation / 'models.json'
            config = json.loads(path.read_text())
            config['rows'][host]['researcher']['model'] = 'selected-researcher-' + host
            selected[host] = config['rows'][host]['researcher'].copy()
            path.write_text(json.dumps(config))
        self.git(self.project, 'add', '.')
        self.git(self.project, 'commit', '-qm', 'researcher settings')
        sources = ROOT / 'mmw-v5-cloud/skills'
        prompts = {
            'grilling': 'Find which process owns the project port. Return the PID and command; keep interviewing independent questions.',
            'codebase-design': (sources / 'codebase-design/references/runner-prompt.md').read_text(),
            'no-comments': (sources / 'no-comments/references/comment-sicko.md').read_text(),
            'to-tickets': (sources / 'to-tickets/references/ambiguity-scan.md').read_text(),
            'maintain-verification-skill': 'Read login.md and its source. Report feature summary / source entry points / likely drift or none / one recipe. Never edit or drive the app.',
            'improve-codebase-architecture': 'Walk the selected subsystem. Find shallow modules and coupling. Apply the deletion test and return findings.',
            'wayfinder': 'Use research for ticket #7 in an isolated checkout from map-3. Save findings on research/service-api, push the branch, and open no PR.',
        }
        for host, installation in installations.items():
            for caller, body in prompts.items():
                with self.subTest(host=host, caller=caller):
                    text = f'\nAssigned task: {caller} — 保留原任务\n\n{body}\n\n'
                    prompt = self.base / f'{caller} prompt.md'
                    prompt.write_text(text, encoding='utf-8')
                    result = self.run_command(self.project, 'bash',
                                              str(installation / 'tools/dispatch/scripts/dispatch.sh'),
                                              'spawn', 'researcher', '--prompt', str(prompt), '--host', host)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    card, = json.loads(result.stdout)['cards']
                    self.assertEqual(card['prompt'], text)
                    self.assertEqual(card['model_row'], {'role': 'researcher', **selected[host]})

    def test_complete_runtime_installs_for_both_hosts_and_uses_its_own_config(self):
        installations = {host: self.install(host) for host in ('cursor', 'codex')}
        snapshots = {}
        for host, installation in installations.items():
            with self.subTest(host=host):
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
        for host, installation in installations.items():
            config = installation / 'models.json'
            changed = json.loads(config.read_text())
            changed['rows'][host]['review-axis']['model'] = 'next-run-only'
            config.write_text(json.dumps(changed))
            result = self.run_command(self.project, sys.executable,
                                      str(installation / 'tools/dispatch/scripts/models.py'),
                                      'row', 'review-axis', '--at', fixed, '--host', host)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), snapshots[host])
            self.check_board_settings(installation, host)
        with zipfile.ZipFile(self.archive) as archive:
            self.assertTrue(all(name.startswith('mmw-v5-cloud/') for name in archive.namelist()))
            self.assertFalse(any(x in name for name in archive.namelist()
                                 for x in ['/runners/', '/relay.py', '/events.py', '/children.md']))

    def check_board_settings(self, installation, host):
        process = subprocess.Popen([sys.executable, str(installation / 'board/server.py'), '--port', '0', '--host', host],
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
        finally:
            process.terminate()
            process.wait(timeout=5)
            process.stdout.close()

    def test_shared_install_migrates_both_legacy_rows_and_preserves_project_files(self):
        legacy = self.project / '.cursor/models.json'
        legacy.parent.mkdir()
        previous = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        previous['rows']['codex']['senior-worker']['model'] = 'legacy-codex-choice'
        previous['rows']['cursor']['senior-worker']['model'] = 'legacy-cursor-choice'
        legacy.write_text(json.dumps(previous))
        before = legacy.read_bytes()
        installation = self.install('cursor', '--cloud')
        settings = installation / 'models.json'
        migrated = json.loads(settings.read_text())
        self.assertEqual(migrated['rows']['codex'], previous['rows']['codex'])
        self.assertEqual(migrated['rows']['cursor'], previous['rows']['cursor'])
        environment = json.loads((self.project / '.cursor/environment.json').read_text())
        self.assertEqual(environment['install'], 'bash .agents/cloud-setup.sh')
        self.assertEqual(legacy.read_bytes(), before)
        migrated['rows']['codex']['senior-worker']['model'] = 'kept-existing-choice'
        settings.write_text(json.dumps(migrated))
        custom = installation / 'skills/owner/SKILL.md'
        custom.parent.mkdir()
        custom.write_text('Keep owner skill\n')
        nested = self.project / 'src'
        nested.mkdir()
        self.install('codex', cwd=nested)
        self.assertEqual(json.loads(settings.read_text()), migrated)
        self.assertEqual(custom.read_text(), 'Keep owner skill\n')
        self.assertEqual(legacy.read_bytes(), before)

    def test_cursor_updates_preserve_configuration_and_rules(self):
        installation = self.install('cursor')
        config = installation / 'models.json'
        settings = json.loads(config.read_text())
        settings['rows']['cursor']['senior-worker']['model'] = 'kept-cursor-choice'
        config.write_text(json.dumps(settings))
        rules = self.project / '.cursor/rules/owner.mdc'
        rules.parent.mkdir(parents=True)
        rules.write_text('Keep project rules\n')
        self.install('cursor')
        self.assertEqual(json.loads(config.read_text()), settings)
        self.assertEqual(rules.read_text(), 'Keep project rules\n')
        self.assertTrue((self.project / '.agents/skills/dispatch/SKILL.md').is_file())
        self.assertFalse((self.project / '.cursor/plugin.json').exists())

    def test_installer_requires_a_known_explicit_host(self):
        for args in [[], ['--host', 'unknown'], ['--host'], ['--ref', 'candidate'],
                     ['--host', 'codex', '--ref', 'v5.0.7']]:
            result = self.run_command(self.project, 'bash', str(ROOT / 'scripts/install-mmw-v5-cloud.sh'), *args)
            self.assertEqual(result.returncode, 2, args)
        self.assertFalse((self.project / '.cursor').exists())
        self.assertFalse((self.project / '.agents').exists())

    def update_archive(self, version, *, extra=None, remove=()):
        with zipfile.ZipFile(self.env['CLOUD_TEST_ARCHIVE']) as archive:
            files = {name: archive.read(name) for name in archive.namelist() if name not in remove}
        manifest = json.loads(files['mmw-v5-cloud/plugin.json'])
        manifest['version'] = version
        files['mmw-v5-cloud/plugin.json'] = json.dumps(manifest).encode()
        files.update(extra or {})
        output = self.base / f'cloud-{version}.zip'
        with zipfile.ZipFile(output, 'w') as archive:
            for name, value in files.items():
                archive.writestr(name, value)
        self.env['CLOUD_TEST_ARCHIVE'] = str(output)

    def test_runtime_is_local_and_legacy_tracked_files_are_retired(self):
        for host in ('codex', 'cursor'):
            with self.subTest(host=host):
                installation = self.install(host)
                custom = installation / 'skills/owner/SKILL.md'
                custom.parent.mkdir(parents=True, exist_ok=True)
                custom.write_text('project-owned skill\n')
                self.git(self.project, 'add', '.')
                indexed = self.git(self.project, 'ls-files').splitlines()
                self.assertIn(f'{installation.name}/models.json', indexed)
                self.assertIn(custom.relative_to(self.project).as_posix(), indexed)
                self.assertNotIn(f'{installation.name}/skills/dispatch/SKILL.md', indexed)
                self.assertNotIn(f'{installation.name}/plugin.json', indexed)
                cache = installation / 'tools/dispatch/scripts/__pycache__/status.cpython.pyc'
                cache.parent.mkdir(exist_ok=True)
                cache.write_bytes(b'generated runtime cache')
                self.assertNotIn('__pycache__', self.git(self.project, 'status', '--porcelain'))
                # Reproduce the retired installation that committed its runtime.
                legacy = installation / 'skills/dispatch/SKILL.md'
                self.git(self.project, 'add', '-f', str(legacy), str(installation / 'plugin.json'))
                self.git(self.project, 'commit', '-qm', 'old tracked installation')
                config = (installation / 'models.json').read_bytes()
                self.install(host)
                self.assertTrue(legacy.is_file())
                indexed = self.git(self.project, 'ls-files').splitlines()
                self.assertNotIn(legacy.relative_to(self.project).as_posix(), indexed)
                self.assertIn(custom.relative_to(self.project).as_posix(), indexed)
                self.assertEqual((installation / 'models.json').read_bytes(), config)
                self.assertFalse((installation / 'cloud-setup.sh').exists())
                self.git(self.project, 'commit', '-qm', 'retire tracked runtime ' + host)

    def test_cloud_configuration_bootstraps_independent_clones(self):
        for host in ('codex', 'cursor'):
            with self.subTest(host=host):
                installation = self.install(host, '--cloud')
                if host == 'codex':
                    self.assertIn('Install script', (self.project / 'AGENTS.md').read_text())
                    self.assertIn('Start skill', (self.project / 'AGENTS.md').read_text())
                self.git(self.project, 'add', '.')
                self.git(self.project, 'commit', '-qm', 'cloud preparation ' + host)
                for name in ('agent-one', 'agent-two'):
                    clone = self.base / f'{host}-{name}'
                    self.git(self.project, 'clone', '-q', str(self.project), str(clone))
                    runtime = clone / installation.name
                    self.assertFalse((runtime / 'skills/dispatch/SKILL.md').exists())
                    before = (runtime / 'models.json').read_bytes()
                    result = self.run_command(clone, 'bash', str(runtime / 'cloud-setup.sh'))
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue((runtime / 'skills/dispatch/SKILL.md').is_file())
                    self.assertEqual((runtime / 'models.json').read_bytes(), before)
                    self.assertEqual(self.git(clone, 'status', '--porcelain'), '')

    def test_cursor_cloud_setup_preserves_and_runs_existing_commands(self):
        environment = self.project / '.cursor/environment.json'
        environment.parent.mkdir()
        old = {'build': {'dockerfile': 'Dockerfile'},
               'install': "printf 'dependencies\\n' >> setup.log",
               'start': "printf 'services\\n' >> setup.log"}
        environment.write_text(json.dumps(old))
        installation = self.install('cursor', '--cloud')
        first = environment.read_bytes()
        self.install('cursor', '--cloud')
        self.assertEqual(environment.read_bytes(), first)
        settings = json.loads(first)
        self.assertEqual(settings['build'], old['build'])
        self.git(self.project, 'add', '.')
        self.git(self.project, 'commit', '-qm', 'cloud settings')
        for field in ('install', 'start'):
            result = self.run_command(self.project, 'bash', '-c', settings[field])
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.project / 'setup.log').read_text(), 'dependencies\nservices\n')
        self.assertEqual(settings['start'].count('bash .agents/cloud-setup.sh'), 1)
        self.assertTrue((installation / 'skills/dispatch/SKILL.md').is_file())

    def test_codex_cloud_setup_preserves_project_instructions_and_is_idempotent(self):
        instructions = self.project / 'AGENTS.md'
        original = '# Project rules\n\nKeep the product contract.\n'
        instructions.write_text(original)
        self.install('codex', '--cloud')
        first = instructions.read_bytes()
        self.install('codex', '--cloud')
        self.assertEqual(instructions.read_bytes(), first)
        self.assertTrue(instructions.read_text().startswith(original))
        self.assertFalse((self.project / '.codex').exists())

    def test_startup_gets_latest_release_and_removes_only_previous_package_files(self):
        retired = 'mmw-v5-cloud/skills/dispatch/references/retired.txt'
        self.update_archive('5.0.8', extra={retired: b'old runtime file'})
        installation = self.install('codex', '--cloud')
        custom = installation / 'skills/dispatch/owner-note.md'
        custom.write_text('Keep my note\n')
        config = (installation / 'models.json').read_bytes()
        self.update_archive('5.0.9', remove=[retired])
        result = self.run_command(self.project, 'bash', str(installation / 'cloud-setup.sh'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((installation / 'plugin.json').read_text())['version'], '5.0.9')
        self.assertFalse((installation / 'skills/dispatch/references/retired.txt').exists())
        self.assertEqual(custom.read_text(), 'Keep my note\n')
        self.assertEqual((installation / 'models.json').read_bytes(), config)
        requests = [json.loads(line) for line in Path(self.env['CLOUD_TEST_CURL_LOG']).read_text().splitlines()]
        self.assertTrue(all('/releases/latest/download/mmw-v5-cloud.zip' in url or
                            '/main/scripts/install-mmw-v5-cloud.sh' in url for url in requests))

    def test_failed_download_does_not_rewrite_configuration_or_use_cached_runtime(self):
        installation = self.install('cursor', '--cloud')
        before = (installation / 'plugin.json').read_bytes()
        environment = self.project / '.cursor/environment.json'
        settings = environment.read_bytes()
        self.env['CLOUD_TEST_DOWNLOAD_FAIL'] = '1'
        result = self.run_command(self.project, 'bash', str(installation / 'cloud-setup.sh'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('download failed', result.stderr)
        self.assertEqual((installation / 'plugin.json').read_bytes(), before)
        self.assertEqual(environment.read_bytes(), settings)

    def test_shared_installation_uses_committed_gitignore(self):
        ignore = self.project / '.gitignore'
        ignore.write_text('owner-build/\n')
        self.install('codex')
        first = ignore.read_bytes()
        self.install('cursor')
        self.assertEqual(ignore.read_bytes(), first)
        self.assertTrue(ignore.read_text().startswith('owner-build/\n'))
        self.assertFalse((self.project / '.cursor').exists())
        self.assertTrue((self.project / '.agents/skills/research/SKILL.md').is_file())
        # Ignore rules must survive a fresh clone, not depend on this machine.
        self.git(self.project, 'add', '.')
        self.git(self.project, 'commit', '-qm', 'shared installation configuration')
        clone = self.base / 'ignore-only-clone'
        self.git(self.project, 'clone', '-q', str(self.project), str(clone))
        runtime = clone / '.agents/skills/dispatch/SKILL.md'
        runtime.parent.mkdir(parents=True)
        runtime.write_text('local runtime file\n')
        result = self.run_command(clone, 'git', 'check-ignore', '-v', str(runtime))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('.gitignore:'), result.stdout)
        self.assertEqual(self.git(clone, 'status', '--porcelain'), '')

    def test_old_local_exclusions_migrate_and_retire_only_owned_runtime_files(self):
        old = self.project / '.cursor/skills/dispatch/SKILL.md'
        old.parent.mkdir(parents=True)
        old.write_text('old MMW runtime\n')
        custom = self.project / '.cursor/skills/owner/SKILL.md'
        custom.parent.mkdir(parents=True)
        custom.write_text('keep project skill\n')
        exclude = self.project / '.git/info/exclude'
        exclude.write_text('owner-cache/\n# MMW cloud cursor BEGIN\n/.cursor/skills/dispatch/SKILL.md\n# MMW cloud cursor END\n')
        self.install('cursor')
        self.assertFalse(old.exists())
        self.assertEqual(custom.read_text(), 'keep project skill\n')
        self.assertEqual(exclude.read_text(), 'owner-cache/\n')
        result = self.run_command(self.project, 'git', 'check-ignore', '-v', '.agents/skills/dispatch/SKILL.md')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('.gitignore:'), result.stdout)


if __name__ == '__main__':
    unittest.main()
