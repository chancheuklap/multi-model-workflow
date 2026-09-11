"""A snapshot line Playwright writes in single quotes is a node like any other.

Playwright quotes a node's key (`role "name" [attrs]`) as YAML when it would not read
plain — a name holding " #" or ": " is enough — and doubles any quote inside it. The
skeleton's row inventory (`extract_skeleton.controls`), the judges' normaliser
(`screen_driver.normalize_aria`) and the option naming (`name_options_from_dom`) all
read those lines; a reader that skips them loses the control from the inventory and the
node from both sides of every tree comparison.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "drive-target" / "scripts"
HOME = tempfile.mkdtemp(prefix="mmw-extract-skeleton-home-")


def load(name: str, modname: str):
    with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
        spec = importlib.util.spec_from_file_location(modname, SCRIPTS / name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[modname] = module
        spec.loader.exec_module(module)
    return module


sd = load("screen_driver.py", "screen_driver")
es = load("extract_skeleton.py", "extract_skeleton")


def tearDownModule():
    shutil.rmtree(HOME, ignore_errors=True)


# Lines as Playwright printed them for the task board's handoff package.
QUOTED = (
    '- navigation "任务":\n'
    "  - text: 任务 3\n"
    "  - 'button \"需要你 #98 · wayfinder 落地流水线改造 6/18 落地\"': \"#98 · wayfinder 落地流水线改造 6/18 落地\"\n"
    "  - 'button \"收起 #98\"': ▾\n"
    "  - 'button \"it''s: here\" [disabled]'\n"
    "- 'dialog \"本机配置: 这台机器\"':\n"
    '  - button "保存"\n'
)


class TestQuotedLines(unittest.TestCase):
    def test_controls_reads_a_quoted_key(self):
        with mock.patch.dict(os.environ, {"MMW_HOME": HOME}, clear=False):
            found = es.controls(QUOTED)
        self.assertEqual(found, [
            ("button", "需要你 #98 · wayfinder 落地流水线改造 6/18 落地"),
            ("button", "收起 #98"),
            ("button", "it's: here"),
            ("button", "保存"),
        ])

    def test_normaliser_reads_a_quoted_key_as_it_reads_a_plain_one(self):
        self.assertEqual(sd.normalize_aria(QUOTED), [
            "- text: 任务 3",
            '- button: "#98 · wayfinder 落地流水线改造 6/18 落地"',
            "- button: ▾",
            "- button \"it's: here\" [disabled]",
            '- dialog "本机配置: 这台机器"',
            '- button "保存" < dialog "本机配置: 这台机器"',
        ])

    def test_a_quoted_option_is_named_from_the_dom(self):
        aria = '- combobox "runner":\n  - \'option "a: b" [selected]\'\n  - option "orca"'
        self.assertEqual(sd.name_options_from_dom(aria, ["a: b", "orca"]).splitlines(), [
            '- combobox "runner":',
            '  - option "a: b" [selected]',
            '  - option "orca"',
        ])


if __name__ == "__main__":
    unittest.main()
