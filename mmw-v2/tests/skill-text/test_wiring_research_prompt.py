"""The wiring CLI checks the research prompt from the product's dispatch script."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIB = HERE.parent / 'lib'
DISPATCH = 'mmw-v2/skills/dispatch'
SOURCE = ROOT / DISPATCH / 'scripts/dispatch.sh'


class ResearchPromptTest(unittest.TestCase):
    def test_class_8_reads_the_research_start_prompt(self):
        with tempfile.TemporaryDirectory(prefix='mmw-research-prompt-') as tmp:
            root = Path(tmp)
            scripts = root / DISPATCH / 'scripts'
            scripts.mkdir(parents=True)
            for name in ('locations.py', 'roles.json'):
                target = scripts / name if name.endswith('.py') else root / DISPATCH / name
                shutil.copy(HERE / 'fixtures/wiring' / name, target)
            # These paths are referenced by dispatch.sh; only that script is inspected.
            for name in ('models.py', 'status.py', 'relay.py', 'statedir.py'):
                (scripts / name).touch()
            (scripts / 'runners').mkdir()
            target = scripts / 'dispatch.sh'
            original = SOURCE.read_text(encoding='utf-8')
            target.write_text(original, encoding='utf-8')
            command = [sys.executable, str(LIB / 'check_wiring.py'), '--root', str(root)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            function = re.search(r'^research_one\(\) \{.*?(?=^\})', original, re.M | re.S)
            self.assertIsNotNone(function, 'the product has no research start command')
            prompt = re.search(r'^\s*prompt="', function[0], re.M)
            self.assertIsNotNone(prompt, 'the research command has no start prompt')
            offset = function.start() + prompt.end()
            line = original.count('\n', 0, offset) + 1
            # Insert a literal newline inside the prompt, leaving its use unchanged.
            target.write_text(original[:offset] + '\n' + original[offset:], encoding='utf-8')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertRegex(result.stdout, rf'(?m)^{DISPATCH}/scripts/dispatch.sh:{line}: class 8 ')
            self.assertNotIn('Traceback', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
