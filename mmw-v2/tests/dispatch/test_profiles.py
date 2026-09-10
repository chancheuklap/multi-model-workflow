"""Live table, catalog match, and host argv from hosts.json.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_profiles.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import shlex
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

    def test_claude_reviewer_takes_the_session_name(self):
        argv = models.bypass_argv(
            "claude", "claude-opus-5", "high", "issue-61-review")
        self.assertEqual(argv, [
            "--model", "claude-opus-5", "--effort", "high",
            "--permission-mode", "bypassPermissions", "-n", "issue-61-review",
        ])

    def test_a_host_without_a_cli_block_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no bypass argv for host pi: .*`cli` block"):
            models.bypass_argv("pi", "x", "low", "issue-1")

    def test_the_command_line_block_is_named_cli(self):
        hosts = models.load_hosts()["hosts"]
        self.assertEqual(
            sorted(h for h, spec in hosts.items() if "cli" in spec),
            ["claude", "codex", "cursor", "grok"])
        self.assertEqual([h for h, spec in hosts.items() if "herdr" in spec], [])


class LaunchLineTest(unittest.TestCase):
    PROMPT = "Use the implement skill on #61. Don't ask 'Shall I…?'"

    def launch_line(self, *args: str) -> tuple[int, str, str]:
        from io import StringIO
        from unittest.mock import patch
        with patch("sys.stdout", new_callable=StringIO) as out, \
                patch("sys.stderr", new_callable=StringIO) as err:
            code = models.main(["launch-line", *args])
        return code, out.getvalue(), err.getvalue()

    def test_the_prompt_is_the_last_argument_quoted(self):
        code, out, _ = self.launch_line("grok", "grok-4.6", "high", "issue-61", self.PROMPT)
        self.assertEqual(code, 0)
        argv = shlex.split(out)
        self.assertEqual(argv, [
            "grok", *models.bypass_argv("grok", "grok-4.6", "high", "issue-61"),
            self.PROMPT,
        ])
        self.assertTrue(out.rstrip("\n").endswith(" " + shlex.quote(self.PROMPT)), out)

    def test_without_a_prompt_the_line_ends_with_the_flags(self):
        code, out, _ = self.launch_line("grok", "grok-4.6", "high", "issue-61")
        self.assertEqual(code, 0)
        self.assertEqual(shlex.split(out), [
            "grok", *models.bypass_argv("grok", "grok-4.6", "high", "issue-61")])

    def test_a_prompt_that_reads_as_a_flag_is_refused(self):
        code, out, err = self.launch_line("grok", "grok-4.6", "high", "issue-61", "--help")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("cannot build the launch line for grok", err)


class SessionRowsTest(unittest.TestCase):
    def test_two_rows_for_one_agent_are_refused(self):
        with self.assertRaisesRegex(ValueError, "junior-worker has two rows"):
            rows_from(
                "| junior-worker | cursor | grok 4.6 | high |\n"
                "| junior-worker | grok | grok 4.6 | high |\n"
            )

    def test_one_row_per_agent_is_read_in_order(self):
        rows = rows_from(
            "| junior-worker | cursor | grok 4.6 | high |\n"
            "| reviewer | claude | opus 5 | high |\n"
        )
        self.assertEqual([(r.agent, r.host) for r in rows],
                         [("junior-worker", "cursor"), ("reviewer", "claude")])

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


class CliCatalogParseTest(unittest.TestCase):
    def test_cursor_line_carries_the_effort_inside_the_id(self):
        rows = models._parse_cursor_models(
            "Available models\n"
            "cursor-grok-4.6-high - Cursor Grok 4.6\n"
            "cursor-grok-4.6-high-fast - Cursor Grok 4.6 Fast\n"
        )
        self.assertEqual(rows[0]["id"], "cursor-grok-4.6-high")
        self.assertEqual(rows[0]["thinkingOptionIds"], ["high"])

    def test_grok_stars_are_model_ids(self):
        rows = models._parse_grok_models(
            "Available models:\n  * grok-4.6 (default)\n  - grok-4.5\n")
        self.assertEqual([r["id"] for r in rows], ["grok-4.6", "grok-4.5"])

    def test_claude_help_lists_aliases_and_effort(self):
        aliases, efforts = models._parse_claude_help(
            "  --model <model>                       Model for the current session. Provide\n"
            "                                        an alias for the latest model (e.g.\n"
            "                                        'fable', 'opus', or 'sonnet') or a\n"
            "                                        model's full name (e.g.\n"
            "                                        'claude-fable-5').\n"
            "  --effort <level>                      Effort level for the current session\n"
            "                                        (low, medium, high, xhigh, max)\n"
        )
        self.assertIn("opus", aliases)
        self.assertIn("claude-fable-5", aliases)
        self.assertEqual(efforts, ["low", "medium", "high", "xhigh", "max"])

    def test_codex_debug_json_keeps_slug_and_effort(self):
        raw = json.dumps({"models": [{
            "slug": "gpt-5.6-sol",
            "display_name": "GPT-5.6-Sol",
            "supported_reasoning_levels": [
                {"effort": "low"}, {"effort": "high"}],
        }]})
        rows = models._parse_codex_debug_models(raw)
        self.assertEqual(rows[0]["id"], "gpt-5.6-sol")
        self.assertEqual(rows[0]["thinkingOptionIds"], ["low", "high"])

    def test_pi_list_models_uses_provider_slash_model(self):
        rows = models._parse_pi_models(
            "provider      model                         context  max-out  thinking  images\n"
            "xai           grok-4.6                      500K     500K     yes       yes   \n"
        )
        self.assertEqual(rows[0]["id"], "xai/grok-4.6")
        self.assertIn("high", rows[0]["thinkingOptionIds"])

    def test_fillable_rows_are_the_cells_to_copy(self):
        rows = models.fillable_rows("cursor", [
            {"id": "cursor-grok-4.6-high", "name": "Cursor Grok 4.6"},
            {"id": "cursor-grok-4.6-low", "name": "Cursor Grok 4.6 Low"},
            {"id": "cursor-grok-4.6-high-fast", "name": "Cursor Grok 4.6 Fast"},
        ])
        by_model = [(m, e) for m, e in rows]
        self.assertIn(("grok 4.6", "high"), by_model)
        self.assertIn(("grok 4.6", "low"), by_model)
        self.assertIn(("grok 4.6 fast", "high"), by_model)
        self.assertNotIn(("grok 4.6", "low, high"), by_model)


class OfferingsBlockTest(unittest.TestCase):
    def setUp(self):
        os.environ["MMW_HOST_CATALOG"] = str(CATALOG)
        self.addCleanup(os.environ.pop, "MMW_HOST_CATALOG", None)

    def test_a_catalog_table_below_the_rows_is_not_read_as_an_agent(self):
        rows = rows_from(
            "| junior-worker | grok | grok 4.6 | high |\n"
            "\n"
            "<!-- mmw-offerings -->\n"
            "| intern | grok | nope | high |\n"
            "<!-- /mmw-offerings -->\n"
        )
        self.assertEqual([r.agent for r in rows], ["junior-worker"])

    def test_refresh_rewrites_the_catalog_and_keeps_the_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "models.md"
            dest.write_text(
                "# Models\n\n" + TABLE_HEAD
                + "| junior-worker | grok | grok 4.6 | high |\n"
                + "\n# touched\n",
                encoding="utf-8")
            os.environ["MMW_LIVE_MODELS"] = str(dest)
            self.addCleanup(os.environ.pop, "MMW_LIVE_MODELS", None)
            models.MODELS = dest
            models.refresh_live_offerings()
            text = dest.read_text(encoding="utf-8")
            self.assertIn("touched", text)
            self.assertIn("<!-- mmw-offerings -->", text)
            self.assertIn("| model | effort |", text)
            self.assertIn("| grok 4.6 |", text)
            self.assertIn("| gpt 5.6 sol |", text)
            self.assertIn("Copy one whole row", text)
            self.assertNotIn("| grok 4.6 | low, high |", text)
            again = models.session_rows()
            self.assertEqual([(r.agent, r.host) for r in again],
                             [("junior-worker", "grok")])

    def test_offerings_command_prints_the_live_path(self):
        from io import StringIO
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "models.md"
            os.environ["MMW_LIVE_MODELS"] = str(dest)
            self.addCleanup(os.environ.pop, "MMW_LIVE_MODELS", None)
            models.MODELS = None
            with patch("sys.stdout", new_callable=StringIO) as out:
                self.assertEqual(models.main(["offerings"]), 0)
            self.assertEqual(out.getvalue().strip(), str(dest))
            self.assertTrue(dest.is_file())
            self.assertIn("junior-worker", dest.read_text(encoding="utf-8"))
            self.assertIn("<!-- mmw-offerings -->", dest.read_text(encoding="utf-8"))
