import json
import tempfile
import unittest
from pathlib import Path

from night_smoke import greet


class GreetingTests(unittest.TestCase):
    def test_greeting_trims_outer_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            config.write_text(json.dumps({'prefix': ' Night '}), encoding='utf-8')
            before = config.read_bytes()
            self.assertEqual(greet(' Ada ', config), 'Night, Ada!')
            self.assertEqual(config.read_bytes(), before)

    def test_blank_name_is_rejected_without_changing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            config.write_text('{"prefix":"Night"}', encoding='utf-8')
            before = config.read_bytes()
            with self.assertRaisesRegex(ValueError, '^name must not be blank$'):
                greet('  ', config)
            self.assertEqual(config.read_bytes(), before)

    def test_invalid_prefix_is_rejected_without_changing_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            for data in ({}, {'prefix': '  '}, {'prefix': 42}, []):
                with self.subTest(data=data):
                    config.write_text(json.dumps(data), encoding='utf-8')
                    before = config.read_bytes()
                    with self.assertRaisesRegex(ValueError, '^prefix must be a non-empty string$'):
                        greet('Ada', config)
                    self.assertEqual(config.read_bytes(), before)

    def test_unicode_case_and_internal_spaces_are_preserved_and_config_reloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            config.write_text('{"prefix":"你好"}', encoding='utf-8')
            self.assertEqual(greet('  Éva  李  ', config), '你好, Éva  李!')
            config.write_text('{"prefix":"Hello"}', encoding='utf-8')
            self.assertEqual(greet('  Éva  李  ', config), 'Hello, Éva  李!')

    def test_missing_config_and_invalid_json_remain_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'greeting.json'
            with self.assertRaises(FileNotFoundError):
                greet('Ada', config)
            self.assertFalse(config.exists())
            config.write_text('{invalid', encoding='utf-8')
            before = config.read_bytes()
            with self.assertRaises(json.JSONDecodeError):
                greet('Ada', config)
            self.assertEqual(config.read_bytes(), before)
