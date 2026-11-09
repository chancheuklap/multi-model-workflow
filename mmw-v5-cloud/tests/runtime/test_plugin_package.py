from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[3]


class PluginPackage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mmw-plugin-package-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')
        self.env.pop('MMW_MODELS_JSON', None)
        source = self.base / 'source'
        shutil.copytree(ROOT / 'mmw-v5-cloud', source / 'mmw-v5-cloud',
                        ignore=shutil.ignore_patterns('__pycache__'))
        (source / 'scripts').mkdir()
        shutil.copy2(ROOT / 'scripts/release-mmw-v5.py', source / 'scripts')
        self.init_repo(source)
        self.git(source, 'add', '.')
        self.git(source, 'commit', '-qm', 'candidate')
        archive = self.base / 'plugin.zip'
        result = self.run_command(source, sys.executable, str(source / 'scripts/release-mmw-v5.py'),
                                  'package', '--output', str(archive))
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(archive) as packaged:
            packaged.extractall(self.base / 'unpacked')
        self.plugin = self.base / 'unpacked/mmw-v5-cloud'
        self.runtime = self.plugin / 'skills/dispatch/runtime'
        self.config = self.home / '.agents/models.json'
        self.project = self.base / 'consumer'
        self.project.mkdir()
        self.init_repo(self.project)

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

    def dispatch(self, host, *args, cwd=None):
        result = self.run_command(cwd or self.project, 'bash',
                                  str(self.runtime / 'tools/dispatch/scripts/dispatch.sh'),
                                  *args, '--host', host)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_complete_package_has_both_manifests_and_bundled_tools(self):
        portable = json.loads((self.plugin / 'plugin.json').read_text())
        cursor = json.loads((self.plugin / '.cursor-plugin/plugin.json').read_text())
        self.assertEqual((portable['name'], portable['version']), (cursor['name'], cursor['version']))
        self.assertTrue((self.plugin / 'skills/research/SKILL.md').is_file())
        self.assertTrue((self.plugin / 'skills/advisor/SKILL.md').is_file())
        self.assertTrue((self.plugin / 'skills/dispatch/references/advisor.md').is_file())
        self.assertTrue((self.runtime / 'board/page/app.mjs').is_file())
        self.assertTrue((self.plugin / 'skills/dispatch/runtime/tools/dispatch/scripts/dispatch.sh').is_file())
        self.assertTrue((self.plugin / portable['extensions']['com.openai']['onboardingSkill']).is_file())
        self.assertFalse((self.runtime / 'tests').exists())

    def test_first_dispatch_creates_user_defaults_for_both_hosts(self):
        for host in ('codex', 'cursor'):
            if self.config.exists(): self.config.unlink()
            result = self.dispatch(host, 'row', 'researcher')
            defaults = json.loads((self.runtime / 'models.json').read_text())
            self.assertEqual(result, defaults['rows'][host]['researcher'])
            self.assertEqual(json.loads(self.config.read_text()), defaults)
            self.assertFalse((self.project / '.agents').exists())

    def test_environment_seeds_models_once_and_preserves_owner_bytes(self):
        chosen = json.loads((self.runtime / 'models.json').read_text())
        chosen['rows']['codex']['researcher']['model'] = 'owner-choice'
        self.env['MMW_MODELS_JSON'] = json.dumps(chosen)
        self.dispatch('codex', 'show')
        self.assertEqual(json.loads(self.config.read_text()), chosen)
        before = self.config.read_bytes()
        self.env['MMW_MODELS_JSON'] = '{invalid stale environment value'
        other = self.base / 'second repository'; other.mkdir(); self.init_repo(other)
        for project in (self.project, other):
            self.assertEqual(self.dispatch('codex', 'row', 'researcher', cwd=project)['model'], 'owner-choice')
            self.dispatch('cursor', 'row', 'researcher', cwd=project)
            self.assertEqual(self.config.read_bytes(), before)
            self.assertEqual(self.git(project, 'status', '--porcelain'), '')

    def test_invalid_seed_does_not_create_a_user_file(self):
        self.env['MMW_MODELS_JSON'] = '{invalid'
        result = self.run_command(self.project, 'bash', str(self.runtime / 'tools/dispatch/scripts/dispatch.sh'),
                                  'show', '--host', 'codex')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.config.exists())

    def test_prompt_dispatch_adds_advisor_instructions_and_preserves_brief_and_row(self):
        self.dispatch('codex', 'show')
        selected = {}
        for host in ('cursor', 'codex'):
            config = json.loads(self.config.read_text())
            for role in ('researcher', 'advisor'):
                config['rows'][host][role]['model'] = 'selected-' + role + '-' + host
                selected[host, role] = config['rows'][host][role].copy()
            self.config.write_text(json.dumps(config))
        self.git(self.project, 'add', '.')
        self.git(self.project, 'commit', '--allow-empty', '-qm', 'researcher settings')
        text = '\nAssigned task: 保留原任务\n\nReturn the literal text: "$value" and `code`.\n\n'
        prompt = self.base / 'research prompt.md'
        prompt.write_text(text, encoding='utf-8')
        for host, role in selected:
            with self.subTest(host=host, role=role):
                result = self.run_command(self.project, 'bash',
                                          str(self.runtime / 'tools/dispatch/scripts/dispatch.sh'),
                                          'spawn', role, '--prompt', str(prompt), '--host', host)
                self.assertEqual(result.returncode, 0, result.stderr)
                card, = json.loads(result.stdout)['cards']
                if role == 'advisor':
                    instructions, separator, brief = card['prompt'].partition('\n\n')
                    self.assertIn('Assigned role: advisor.', instructions)
                    self.assertIn('Load the installed advisor skill.', instructions)
                    self.assertIn('Return your answer to the caller.', instructions)
                    self.assertEqual(separator, '\n\n')
                    self.assertEqual(brief, text)
                else:
                    self.assertEqual(card['prompt'], text)
                self.assertEqual(card['model_row'], {'role': role, **selected[host, role]})


if __name__ == '__main__': unittest.main()
