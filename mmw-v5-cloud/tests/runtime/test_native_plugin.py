"""Exercise Codex's native plugin consumer in an isolated user home."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[3]


@unittest.skipUnless(shutil.which('codex'), 'native Codex CLI is not installed')
class NativePlugin(unittest.TestCase):
    def test_native_install_discovers_skills_and_executes_bundled_dispatch(self):
        with tempfile.TemporaryDirectory(prefix='mmw-native-plugin-') as tmp:
            home = Path(tmp).resolve()
            (home / '.codex').mkdir()
            env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home / '.codex'))
            env.pop('MMW_MODELS_JSON', None)

            def command(*args):
                result = subprocess.run(args, cwd=home, env=env, capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            command('codex', 'plugin', 'marketplace', 'add', str(ROOT), '--json')
            installed = command('codex', 'plugin', 'add', 'mmw-v5-cloud@mmw-v5', '--json')
            plugin = Path(installed['installedPath'])
            listing = command('codex', 'plugin', 'list', '--json')['installed']
            self.assertTrue(next(p for p in listing if p['pluginId'] == installed['pluginId'])['enabled'])
            self.assertTrue((plugin / 'board/page/index.html').is_file())
            messages = queue.Queue()
            with tempfile.TemporaryFile(mode='w+') as log:
                server = subprocess.Popen(['codex', 'app-server', '--stdio'], cwd=home, env=env,
                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True)

                def read():
                    for line in server.stdout:
                        try:
                            messages.put(json.loads(line))
                        except ValueError:
                            pass

                reader = threading.Thread(target=read, daemon=True)
                reader.start()

                def rpc(number, method, params):
                    server.stdin.write(json.dumps({'id': number, 'method': method, 'params': params}) + '\n')
                    server.stdin.flush()
                    while True:
                        message = messages.get(timeout=30)
                        if message.get('id') == number:
                            self.assertNotIn('error', message)
                            return message['result']

                try:
                    rpc(1, 'initialize', {'clientInfo': {'name': 'mmw-plugin-test', 'version': '1.0'},
                                          'capabilities': {'experimentalApi': True}})
                    server.stdin.write('{"method":"initialized","params":{}}\n')
                    server.stdin.flush()
                    data = rpc(2, 'skills/list', {'cwds': [str(home)], 'forceReload': True})['data'][0]
                    skills = [s for s in data['skills'] if s.get('pluginId') == installed['pluginId']]
                    expected = {p.parent.name for p in (ROOT / 'mmw-v5-cloud/skills').glob('*/SKILL.md')}
                    self.assertEqual({Path(s['path']).parent.name for s in skills}, expected)
                    self.assertTrue(all(s['enabled'] for s in skills))
                    self.assertEqual(data['errors'], [])
                    dispatch = next(s for s in skills if Path(s['path']).parent.name == 'dispatch')
                    script = Path(dispatch['path']).parent / '../../tools/dispatch/scripts/dispatch.sh'
                    for host in ('codex', 'cursor'):
                        chosen = command('bash', str(script), 'row', 'researcher', '--host', host)
                        defaults = json.loads((plugin / 'models.json').read_text())
                        self.assertEqual(chosen, defaults['rows'][host]['researcher'])
                    before = (home / '.agents/models.json').read_bytes()
                    command('codex', 'plugin', 'remove', 'mmw-v5-cloud@mmw-v5', '--json')
                    self.assertEqual((home / '.agents/models.json').read_bytes(), before)
                finally:
                    server.terminate()
                    server.wait(timeout=10)
                    reader.join(timeout=5)
                    server.stdin.close()
                    server.stdout.close()


if __name__ == '__main__': unittest.main()
