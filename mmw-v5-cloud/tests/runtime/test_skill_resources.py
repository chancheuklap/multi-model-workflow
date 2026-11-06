"""Exercise the cloud boundary: only text resources in one skill are readable."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / 'mmw-v5-cloud/skills/dispatch'


class SkillResources(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mmw-skill-resources-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / 'home'
        self.home.mkdir()
        self.cache = self.base / 'cache'
        self.project = self.base / 'consumer'
        self.project.mkdir()
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')
        self.env.pop('MMW_MODELS_JSON', None)
        script = SKILL / 'scripts/materialize.py'
        spec = importlib.util.spec_from_file_location('mmw_materialize', script)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.manifest = json.loads((SKILL / 'runtime-manifest.json').read_text())
        self.assertEqual(self.manifest['version'], json.loads((ROOT / 'mmw-v5-cloud/plugin.json').read_text())['version'])
        self.contents = {
            item['resource']: (SKILL / item['resource']).read_text(encoding='utf-8')
            for item in self.manifest['files'].values()
        }

    def prepare(self, manifest=None, contents=None):
        return self.tool.materialize(manifest or self.manifest,
                                     self.contents if contents is None else contents, self.cache)

    def command(self, runtime, *args):
        result = subprocess.run(['bash', str(runtime / 'tools/dispatch/scripts/dispatch.sh'), *args],
                                cwd=self.project, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_fresh_cloud_dispatch_uses_only_same_skill_text_resources(self):
        runtime = self.prepare()
        expected = {str(p.relative_to(SKILL / 'runtime')): p.read_bytes()
                    for p in (SKILL / 'runtime').rglob('*') if p.is_file()}
        self.assertEqual(set(self.manifest['files']), set(expected))
        for path, data in expected.items():
            self.assertEqual((runtime / path).read_bytes(), data, path)
        defaults = json.loads((runtime / 'models.json').read_text())
        for host in ('codex', 'cursor'):
            chosen = self.command(runtime, 'row', 'researcher', '--host', host)
            self.assertEqual(chosen, defaults['rows'][host]['researcher'])
        prompt = self.base / 'prompt.md'
        prompt.write_text('Read only. 保留 "$value" and `code`.\n')
        card, = self.command(runtime, 'spawn', 'researcher', '--prompt', str(prompt),
                             '--host', 'codex')['cards']
        self.assertEqual(card['prompt'], prompt.read_text())
        self.assertEqual(card['model_row'], {'role': 'researcher', **defaults['rows']['codex']['researcher']})
        self.assertEqual(json.loads((self.home / '.agents/models.json').read_text()), defaults)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_cached_runtime_is_reused_without_resources_or_model_changes(self):
        runtime = self.prepare()
        self.command(runtime, 'show', '--host', 'codex')
        config = self.home / '.agents/models.json'
        before = config.read_bytes()
        self.assertEqual(self.prepare(contents={}), runtime)
        self.assertEqual(config.read_bytes(), before)
        (runtime / 'models.json').write_text('corrupted')
        with self.assertRaisesRegex(ValueError, 'sha256'):
            self.prepare(contents={})

    def test_cloud_cli_works_without_the_plugin_filesystem(self):
        script = self.base / 'materialize.py'
        script.write_bytes((SKILL / 'scripts/materialize.py').read_bytes())
        manifest = self.base / 'manifest.json'
        manifest.write_text(json.dumps(self.manifest))
        contents = self.base / 'contents.json'
        contents.write_text(json.dumps(self.contents))
        result = subprocess.run([sys.executable, str(script), '--manifest', str(manifest),
                                 '--contents', str(contents), '--cache', str(self.cache)],
                                cwd=self.project, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        prepared = json.loads(result.stdout)
        self.assertEqual(prepared['version'], self.manifest['version'])
        self.assertTrue(Path(prepared['labels']).is_file())
        self.assertEqual(self.command(Path(prepared['runtime']), 'row', 'researcher', '--host', 'codex')['effort'], 'high')

    def test_same_skill_label_tools_create_only_missing_labels(self):
        runtime = self.prepare()
        subprocess.run(['git', 'init', '-q', str(self.project)], check=True)
        subprocess.run(['git', '-C', str(self.project), 'remote', 'add', 'origin',
                        'https://github.com/example/fixture.git'], check=True)
        bin_dir = self.base / 'bin'
        bin_dir.mkdir()
        gh = bin_dir / 'gh'
        gh.write_text('#!' + sys.executable + '\n' + '''
import json, os, pathlib, sys
state = pathlib.Path(os.environ['LABEL_STATE'])
names = json.loads(state.read_text()) if state.exists() else ['mmw:map']
args = sys.argv[1:]
if args[:2] == ['repo', 'view']:
    print('example/fixture')
elif args[0] == 'api':
    print(json.dumps([[{'name': name} for name in names]]))
elif args[:2] == ['label', 'create']:
    assert args[2] not in names
    names.append(args[2]); state.write_text(json.dumps(names))
else:
    sys.exit(2)
''')
        gh.chmod(0o755)
        env = {**self.env, 'PATH': str(bin_dir) + os.pathsep + self.env['PATH'],
               'LABEL_STATE': str(self.base / 'labels.json')}
        command = [sys.executable, str(runtime / 'tools/setup-mmw/scripts/labels.py')]
        first = subprocess.run(command, cwd=self.project, env=env, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn('mmw:ticket', first.stdout)
        self.assertNotIn('mmw:map\n', first.stdout)
        second = subprocess.run(command, cwd=self.project, env=env, capture_output=True, text=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second.stdout, '')

    def test_missing_or_corrupt_resource_does_not_publish_a_runtime(self):
        key = self.manifest['files']['tools/dispatch/scripts/models.py']['resource']
        for contents in ({k: v for k, v in self.contents.items() if k != key},
                         {**self.contents, key: self.contents[key] + '\ncorrupt'}):
            with self.subTest(missing=key not in contents):
                with self.assertRaises(ValueError):
                    self.prepare(contents=contents)
                self.assertFalse(self.cache.exists() and list(self.cache.iterdir()))
                self.assertFalse((self.home / '.agents').exists())

    def test_another_plugin_version_cannot_replace_the_resolved_runtime(self):
        original = self.prepare()
        manifest = json.loads(json.dumps(self.manifest))
        manifest['version'] = '9.0.0'
        updated = self.prepare(manifest=manifest)
        self.assertNotEqual(original, updated)
        self.assertTrue((original / 'tools/dispatch/scripts/dispatch.sh').is_file())
        self.assertEqual((original / 'models.json').read_bytes(), (updated / 'models.json').read_bytes())

    def test_manifest_cannot_escape_the_runtime_directory(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest['files']['../../outside'] = next(iter(manifest['files'].values()))
        with self.assertRaises(ValueError):
            self.prepare(manifest=manifest)
        self.assertFalse((self.base / 'outside').exists())

    def test_materialized_board_serves_page_settings_and_original_font_bytes(self):
        runtime = self.prepare()
        server = subprocess.Popen(['bash', str(runtime / 'tools/dispatch/scripts/dispatch.sh'),
                                   'board', '--host', 'codex', '--port', '0'], cwd=self.project,
                                  env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: server.poll() is None and server.kill())
        try:
            url = server.stdout.readline().strip()
            self.assertTrue(url.startswith('http://127.0.0.1:'), url)
            with urllib.request.urlopen(url) as response:
                page = response.read()
            self.assertIn(b'<html', page.lower())
            self.assertNotIn(b'__MMW_PAGE_TOKEN__', page)
            with urllib.request.urlopen(url + '/api/settings') as response:
                settings = json.load(response)
            self.assertEqual(settings['host'], 'codex')
            font = next((runtime / 'board/page/styles/fonts').glob('*.woff2'))
            with urllib.request.urlopen(url + '/styles/fonts/' + font.name) as response:
                self.assertEqual(response.read(), font.read_bytes())
        finally:
            server.terminate()
            server.wait(timeout=10)
            server.stdout.close()
            server.stderr.close()


if __name__ == '__main__':
    unittest.main()
