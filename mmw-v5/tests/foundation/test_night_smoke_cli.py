import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).with_name('night_smoke.py')


class GreetingCliTests(unittest.TestCase):
    def test_greeting_is_printed(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            config.write_text('{"prefix":"Night"}', encoding='utf-8')
            result = subprocess.run([sys.executable, str(CLI), '--config', str(config), ' Ada '],
                                    capture_output=True, text=True)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, 'Night, Ada!\n', ''))

    def test_invalid_inputs_report_errors_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            for contents, name in ((None, 'Ada'), ('{invalid', 'Ada'),
                                   ('{"prefix":" "}', 'Ada'), ('{"prefix":"Night"}', '  ')):
                with self.subTest(contents=contents, name=name):
                    if contents is not None:
                        config.write_text(contents, encoding='utf-8')
                    result = subprocess.run([sys.executable, str(CLI), '--config', str(config), name],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, '')
                    self.assertTrue(result.stderr.strip())
                    self.assertNotIn('Traceback', result.stderr)
