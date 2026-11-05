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
        self.home = self.base / 'home'
        self.home.mkdir()
        self.skills = self.home / '.agents/skills/mmw'
        self.env = dict(os.environ, HOME=str(self.home), GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
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
        self.config = self.project / '.agents/models.json'
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

    def run_command(self, cwd, *args, env=None):
        return subprocess.run(args, cwd=cwd, env=env or self.env, capture_output=True, text=True)

    def git(self, cwd, *args):
        result = self.run_command(cwd, 'git', *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def init_repo(self, path):
        self.git(path, 'init', '-q', '-b', 'night/test')
        self.git(path, 'config', 'user.name', 'Package test')
        self.git(path, 'config', 'user.email', 'test@example.invalid')

    def install(self, host, *options, cwd=None):
        result = self.run_command(cwd or self.project, 'bash', str(ROOT / 'scripts/install-mmw-v5-cloud.sh'), '--host', host, *options)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.home / '.agents/mmw'

    def commit_config(self, project=None):
        project = project or self.project
        self.git(project, 'add', '.')
        self.git(project, 'commit', '-qm', 'project configuration')

    def test_user_install_is_shared_and_project_configuration_is_separate(self):
        instructions = self.project / 'AGENTS.md'
        instructions.write_text('# Project rules\nKeep this project contract.\n')
        ignore = self.project / '.gitignore'
        ignore.write_text('owner-build/\n')
        original = instructions.read_bytes(), ignore.read_bytes()
        runtime = self.install('cursor')
        self.assertTrue((runtime / 'plugin.json').is_file())
        self.assertTrue((self.skills / 'research/SKILL.md').is_file())
        self.assertTrue((runtime / 'board/page/app.mjs').is_file())
        self.assertFalse((self.project / '.agents/skills').exists())
        self.assertFalse((self.project / '.agents/tools').exists())
        self.assertEqual((instructions.read_bytes(), ignore.read_bytes()), original)
        first = json.loads(self.config.read_text())
        first['rows']['cursor']['researcher']['model'] = 'first-project-cursor'
        self.config.write_text(json.dumps(first))
        self.commit_config()
        other = self.base / 'other-project'
        other.mkdir(); self.init_repo(other)
        self.assertEqual(self.install('codex', cwd=other), runtime)
        second_path = other / '.agents/models.json'
        second = json.loads(second_path.read_text())
        second['rows']['codex']['researcher']['model'] = 'other-project-codex'
        second_path.write_text(json.dumps(second)); self.commit_config(other)
        for project, host, expected in [(self.project, 'cursor', 'first-project-cursor'), (other, 'codex', 'other-project-codex')]:
            result = self.run_command(project, 'bash', str(runtime / 'tools/dispatch/scripts/dispatch.sh'), 'row', 'researcher', '--host', host)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['model'], expected)
        indexed = self.git(self.project, 'ls-files').splitlines()
        self.assertEqual(indexed, ['.agents/models.json', '.gitignore', 'AGENTS.md'])

    def test_updates_preserve_models_and_other_personal_and_project_skills(self):
        runtime = self.install('codex')
        settings = json.loads(self.config.read_text())
        settings['rows']['codex']['senior-worker']['model'] = 'owner-choice'
        self.config.write_text(json.dumps(settings))
        before = self.config.read_bytes()
        personal = self.home / '.agents/skills/owner/SKILL.md'
        project = self.project / '.agents/skills/owner/SKILL.md'
        for path in (personal, project):
            path.parent.mkdir(parents=True); path.write_text('Keep owner skill\n')
        self.install('cursor')
        self.assertEqual(self.config.read_bytes(), before)
        for path in (personal, project): self.assertEqual(path.read_text(), 'Keep owner skill\n')
        self.assertTrue((runtime / 'tools/dispatch/scripts/dispatch.sh').is_file())

    def update_archive(self, version, *, extra=None, remove=()):
        with zipfile.ZipFile(self.env['CLOUD_TEST_ARCHIVE']) as archive:
            files = {name: archive.read(name) for name in archive.namelist() if name not in remove}
        manifest = json.loads(files['mmw-v5-cloud/plugin.json']); manifest['version'] = version
        files['mmw-v5-cloud/plugin.json'] = json.dumps(manifest).encode()
        files.update(extra or {})
        output = self.base / f'cloud-{version}.zip'
        with zipfile.ZipFile(output, 'w') as archive:
            for name, value in files.items(): archive.writestr(name, value)
        self.env['CLOUD_TEST_ARCHIVE'] = str(output)

    def test_startup_updates_owned_directories_and_accepts_new_runtime_content(self):
        retired = 'mmw-v5-cloud/tools/dispatch/scripts/retired.txt'
        self.update_archive('5.0.10', extra={retired: b'retired runtime'})
        runtime = self.install('codex', '--cloud')
        before = self.config.read_bytes()
        future = 'mmw-v5-cloud/new-component/new-file.json'
        future_skill = 'mmw-v5-cloud/skills/future-skill/SKILL.md'
        self.update_archive('5.0.11', remove=[retired], extra={future: b'new release content', future_skill: b'new skill'})
        result = self.run_command(self.project, 'bash', str(self.project / '.agents/cloud-setup.sh'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((runtime / 'plugin.json').read_text())['version'], '5.0.11')
        self.assertFalse((runtime / 'tools/dispatch/scripts/retired.txt').exists())
        self.assertEqual((runtime / 'new-component/new-file.json').read_bytes(), b'new release content')
        self.assertEqual(self.config.read_bytes(), before)
        self.assertTrue((self.skills / 'future-skill/SKILL.md').is_file())
        self.assertFalse((self.project / '.agents/mmw').exists())
        self.assertFalse((self.project / '.agents/skills/mmw').exists())
        self.assertFalse((self.project / '.gitignore').exists())

    def test_cloud_bootstrap_prepares_separate_machine_homes(self):
        for host in ('codex', 'cursor'):
            self.install(host, '--cloud'); self.commit_config()
            for number in (1, 2):
                clone = self.base / f'{host}-checkout-{number}'
                home = self.base / f'{host}-machine-{number}'; home.mkdir()
                self.git(self.project, 'clone', '-q', str(self.project), str(clone))
                models = (clone / '.agents/models.json').read_bytes()
                result = self.run_command(clone, 'bash', str(clone / '.agents/cloud-setup.sh'), host, env={**self.env, 'HOME': str(home)})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue((home / '.agents/skills/mmw/dispatch/SKILL.md').is_file())
                self.assertTrue((home / '.agents/mmw/tools/dispatch/scripts/dispatch.sh').is_file())
                self.assertFalse((clone / '.agents/mmw').exists())
                self.assertEqual((clone / '.agents/models.json').read_bytes(), models)
                self.assertEqual(self.git(clone, 'status', '--porcelain'), '')

    def test_cloud_setup_never_creates_or_changes_project_instructions(self):
        for existing in (False, True):
            instructions = self.project / 'AGENTS.md'
            if existing:
                instructions.write_text('# Owner instructions\n')
            self.install('codex', '--cloud')
            first = (self.project / '.agents/cloud-setup.sh').read_bytes()
            self.install('codex', '--cloud')
            self.assertEqual((self.project / '.agents/cloud-setup.sh').read_bytes(), first)
            if existing:
                self.assertEqual(instructions.read_text(), '# Owner instructions\n')
            else:
                self.assertFalse(instructions.exists())

    def test_cursor_environment_preserves_and_runs_existing_commands(self):
        environment = self.project / '.cursor/environment.json'; environment.parent.mkdir()
        old = {'build': {'dockerfile': 'Dockerfile'}, 'install': "printf 'dependencies\\n' >> setup.log", 'start': "printf 'services\\n' >> setup.log"}
        environment.write_text(json.dumps(old))
        self.install('cursor', '--cloud'); first = environment.read_bytes()
        self.install('cursor', '--cloud'); self.assertEqual(environment.read_bytes(), first)
        settings = json.loads(first); self.assertEqual(settings['build'], old['build'])
        for field in ('install', 'start'):
            result = self.run_command(self.project, 'bash', '-c', settings[field])
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.project / 'setup.log').read_text(), 'dependencies\nservices\n')
        self.assertEqual(settings['start'].count('bash .agents/cloud-setup.sh'), 1)
        self.assertFalse((self.project / 'AGENTS.md').exists())

    def test_cloud_multi_repo_installs_once_and_keeps_repositories_clean(self):
        other = self.base / 'other repository'; other.mkdir(); self.init_repo(other)
        for host in ('codex', 'cursor'):
            (self.base / 'curl.jsonl').write_text('')
            runtime = self.install(host, '--cloud', str(self.project), str(other), cwd=self.base)
            downloads = (self.base / 'curl.jsonl').read_text().splitlines()
            self.assertEqual(len(downloads), 1)
            self.assertTrue((runtime / 'tools/dispatch/scripts/dispatch.sh').is_file())
            for project in (self.project, other):
                self.assertFalse((project / '.agents/mmw').exists())
                self.assertFalse((project / '.agents/skills/mmw').exists())
                self.assertTrue((project / '.agents/models.json').is_file())
                self.assertFalse((project / '.gitignore').exists())
                self.assertNotIn('--cloud', (project / '.agents/cloud-setup.sh').read_text())
            self.assertEqual((self.project / '.agents/cloud-setup.sh').read_bytes(), (other / '.agents/cloud-setup.sh').read_bytes())

    def test_install_outside_repository_prepares_user_runtime_only(self):
        runtime = self.install('codex', cwd=self.base)
        self.assertTrue((runtime / 'plugin.json').is_file())
        self.assertFalse((self.base / '.agents').exists())
        self.assertFalse(self.config.exists())

    def test_migration_removes_project_runtime_and_managed_ignores(self):
        self.install('codex', '--cloud')
        original = self.config.read_bytes()
        for relative in ('.agents/mmw/retired', '.agents/skills/mmw/retired/SKILL.md'):
            path = self.project / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('old')
        own = self.project / '.agents/skills/owner/SKILL.md'
        own.parent.mkdir(parents=True); own.write_text('owner')
        ignore = self.project / '.gitignore'
        ignore.write_text('owner-build/\n\n# MMW cloud BEGIN\n/.agents/mmw/\n/.agents/skills/mmw/\n# MMW cloud END\n')
        cursor = self.project / '.cursor'
        (cursor / 'skills/research').mkdir(parents=True)
        (cursor / 'skills/research/SKILL.md').write_text('retired MMW')
        (cursor / 'skills/owner').mkdir()
        (cursor / 'skills/owner/SKILL.md').write_text('project skill')
        (cursor / 'plugin.json').write_text(json.dumps({'name': 'mmw-v5-cloud'}))
        self.install('cursor', '--cloud')
        self.assertFalse((cursor / 'plugin.json').exists())
        self.assertFalse((cursor / 'skills/research').exists())
        self.assertEqual((cursor / 'skills/owner/SKILL.md').read_text(), 'project skill')
        self.assertEqual(self.config.read_bytes(), original)
        self.assertEqual(own.read_text(), 'owner')
        self.assertEqual(ignore.read_text(), 'owner-build/\n')
        self.assertFalse((self.project / '.agents/mmw').exists())
        self.assertFalse((self.project / '.agents/skills/mmw').exists())

    def test_shared_user_board_keeps_each_project_and_host_settings_separate(self):
        runtime = self.install('cursor')
        before = json.loads(self.config.read_text())
        for host in ('cursor', 'codex'):
            process = subprocess.Popen([sys.executable, str(runtime / 'board/server.py'), '--port', '0', '--host', host], cwd=self.project, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            try:
                address = process.stdout.readline().strip()
                with urllib.request.urlopen(address, timeout=5) as response: page = response.read().decode()
                token = re.search(r'name="mmw-page-token" content="([^"]+)"', page).group(1)
                with urllib.request.urlopen(address + '/api/settings', timeout=5) as response: settings = json.load(response)
                self.assertEqual(settings['host'], host)
                self.assertEqual(settings['store'], str(self.config))
                settings['rows'][host]['researcher']['model'] = 'saved-' + host
                request = urllib.request.Request(address + '/api/settings', method='PUT', data=json.dumps({'rows': {host: settings['rows'][host]}}).encode(), headers={'Content-Type': 'application/json', 'Origin': address, 'X-MMW-Token': token})
                with urllib.request.urlopen(request, timeout=5) as response: self.assertTrue(json.load(response)['saved'])
                saved = json.loads(self.config.read_text()); other = 'codex' if host == 'cursor' else 'cursor'
                self.assertEqual(saved['rows'][host]['researcher']['model'], 'saved-' + host)
                self.assertEqual(saved['rows'][other], before['rows'][other]); before = saved
            finally:
                process.terminate(); process.wait(timeout=5); process.stdout.close()

    def test_failed_download_keeps_installed_runtime_and_configuration(self):
        runtime = self.install('codex', '--cloud')
        before, models = (runtime / 'plugin.json').read_bytes(), self.config.read_bytes()
        self.env['CLOUD_TEST_DOWNLOAD_FAIL'] = '1'
        result = self.run_command(self.project, 'bash', str(self.project / '.agents/cloud-setup.sh'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('download failed', result.stderr)
        self.assertEqual((runtime / 'plugin.json').read_bytes(), before)
        self.assertEqual(self.config.read_bytes(), models)

    def test_legacy_models_migrate_without_replacing_owner_configuration(self):
        legacy = self.project / '.cursor/models.json'; legacy.parent.mkdir()
        choices = json.loads((ROOT / 'mmw-v5-cloud/models.json').read_text())
        choices['rows']['codex']['senior-worker']['model'] = 'legacy-codex'
        choices['rows']['cursor']['senior-worker']['model'] = 'legacy-cursor'
        legacy.write_text(json.dumps(choices)); previous = legacy.read_bytes()
        self.install('cursor', '--cloud')
        self.assertEqual(json.loads(self.config.read_text()), choices)
        self.install('codex'); self.assertFalse(legacy.exists())
        self.assertEqual(json.loads(self.config.read_text()), choices)

    def test_installer_requires_known_explicit_host(self):
        for args in [[], ['--host'], ['--host', 'unknown'], ['--host', 'codex', '--ref', 'v5.0.9']]:
            result = self.run_command(self.project, 'bash', str(ROOT / 'scripts/install-mmw-v5-cloud.sh'), *args)
            self.assertEqual(result.returncode, 2, args)
        self.assertFalse(self.config.exists())
    def test_researcher_dispatch_preserves_each_callers_prompt(self):
        installations = {host: self.install(host) for host in ('cursor', 'codex')}
        selected = {}
        for host, installation in installations.items():
            path = self.config
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


if __name__ == '__main__': unittest.main()
