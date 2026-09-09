"""Live table, catalog match, and host argv from hosts.json.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_profiles.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
CATALOG = HERE / "catalog.json"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

TABLE_HEAD = (
    "| agent | host | model | effort |\n"
    "| --- | --- | --- | --- |\n"
)


def rows_from(text: str) -> list:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write("# Models\n\n" + TABLE_HEAD + text)
        path = Path(fh.name)
    previous = models.MODELS
    try:
        models.MODELS = path
        return models.session_rows()
    finally:
        models.MODELS = previous
        path.unlink(missing_ok=True)


class BypassArgvTest(unittest.TestCase):
    def test_cursor_junior_worker_expands_to_force_trust_approve(self):
        argv = models.bypass_argv(
            "cursor", "cursor-grok-4.6-high", "high", "issue-61")
        self.assertEqual(
            argv, ["--model", "cursor-grok-4.6-high", "--force", "--trust", "--approve-mcps"])

    def test_grok_carries_reasoning_effort_and_bypass(self):
        argv = models.bypass_argv("grok", "grok-4.6", "high", "issue-61")
        self.assertEqual(argv, [
            "-m", "grok-4.6", "--reasoning-effort", "high",
            "--permission-mode", "bypassPermissions", "--always-approve",
        ])

    def test_claude_reviewer_takes_the_herdr_name(self):
        argv = models.bypass_argv(
            "claude", "claude-opus-5", "high", "issue-61-review")
        self.assertEqual(argv, [
            "--model", "claude-opus-5", "--effort", "high",
            "--permission-mode", "bypassPermissions", "-n", "issue-61-review",
        ])

    def test_an_unknown_host_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no bypass argv"):
            models.bypass_argv("pi", "x", "low", "issue-1")


class SessionRowsTest(unittest.TestCase):
    def test_two_rows_for_one_agent_keep_primary_then_fallback(self):
        rows = rows_from(
            "| junior-worker | cursor | grok 4.6 | high |\n"
            "| junior-worker | grok | grok 4.6 | high |\n"
        )
        self.assertEqual([(r.host, r.primary) for r in rows],
                         [("cursor", True), ("grok", False)])

    def test_a_second_fallback_row_is_refused(self):
        with self.assertRaisesRegex(ValueError, "more than one fallback"):
            rows_from(
                "| junior-worker | cursor | grok 4.6 | high |\n"
                "| junior-worker | grok | grok 4.6 | high |\n"
                "| junior-worker | claude | opus 5 | high |\n"
            )

    def test_two_rows_on_the_same_host_are_refused(self):
        with self.assertRaisesRegex(ValueError, "two rows on"):
            rows_from(
                "| junior-worker | cursor | grok 4.6 | high |\n"
                "| junior-worker | cursor | grok 4.6 | high |\n"
            )

    def test_an_unknown_agent_is_refused(self):
        with self.assertRaisesRegex(ValueError, "不是派出的角色"):
            rows_from("| intern | grok | grok 4.6 | high |\n")


class CatalogMatchTest(unittest.TestCase):
    def setUp(self):
        os.environ["MMW_HOST_CATALOG"] = str(CATALOG)
        os.environ["MMW_CATALOG_MODE"] = "paseo"
        self.addCleanup(os.environ.pop, "MMW_HOST_CATALOG", None)
        self.addCleanup(os.environ.pop, "MMW_CATALOG_MODE", None)

    def test_everyday_cursor_name_picks_ordinary_not_fast(self):
        host, model, effort = models.resolve_row("cursor", "grok 4.6", "high")
        self.assertEqual((host, model, effort),
                         ("cursor", "grok-4.6", "high"))

    def test_fast_is_used_only_when_the_cell_says_fast(self):
        _, model, _ = models.resolve_row("cursor", "grok 4.6 fast", "high")
        self.assertEqual(model, "grok-4.6-fast")

    def test_a_miss_is_refused(self):
        with self.assertRaisesRegex(ValueError, "matches nothing"):
            models.resolve_row("grok", "no-such-model", "high")

    def test_opus_5_is_unique_on_claude(self):
        _, model, _ = models.resolve_row("claude", "opus 5", "high")
        self.assertEqual(model, "claude-opus-5")


class PaseoSettingsTest(unittest.TestCase):
    def test_cursor_on_paseo_turns_everyday_high_into_on(self):
        self.assertEqual(models.thinking_option("cursor", "high"), "true")
        self.assertEqual(models.thinking_option("cursor", "off"), "false")

    def test_grok_keeps_the_everyday_effort_name(self):
        self.assertEqual(models.thinking_option("grok", "high"), "high")

    def test_cursor_create_agent_settings_are_agent_mode_and_auto_accept(self):
        self.assertEqual(
            models.create_agent_settings("cursor"),
            {"modeId": "agent", "features": {"auto_accept": True}},
        )


class AdoptTest(unittest.TestCase):
    def test_missing_live_file_is_written_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / ".mmw" / "models.md"
            os.environ["MMW_LIVE_MODELS"] = str(dest)
            self.addCleanup(os.environ.pop, "MMW_LIVE_MODELS", None)
            models.MODELS = None
            self.assertTrue(models.adopt_live_table())
            self.assertTrue(dest.is_file())
            dest.write_text(dest.read_text(encoding="utf-8") + "\n# touched\n",
                            encoding="utf-8")
            self.assertFalse(models.adopt_live_table())
            self.assertIn("touched", dest.read_text(encoding="utf-8"))

    def test_defaults_include_the_five_roles(self):
        text = models.default_live_markdown()
        for name in ("junior-worker", "senior-worker", "reviewer",
                     "verifier", "advisor"):
            self.assertIn(name, text)
