"""Local configuration, catalog match, and host argv from hosts.json.

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
from unittest import mock

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
CATALOG = HERE / "catalog.json"
_spec = importlib.util.spec_from_file_location("mmw_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)

def config_with(rows: dict) -> dict:
    return {"version": 1, "runner": "orca", "rows": rows}


def rows_from(rows: dict) -> list:
    with tempfile.TemporaryDirectory() as tmp, \
            mock.patch.dict(os.environ, {"MMW_HOME": tmp}):
        models.models_json_path().write_text(json.dumps(config_with(rows)) + "\n")
        return models.session_rows()


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


class RowCommandTest(unittest.TestCase):
    def row(self, role: str) -> tuple[int, str, str]:
        from io import StringIO
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"MMW_HOME": tmp}), \
                mock.patch.object(models, "fetch_offerings", return_value=[
                    {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol"}]), \
                mock.patch("sys.stdout", new_callable=StringIO) as out, \
                mock.patch("sys.stderr", new_callable=StringIO) as err:
            rows = dict(models.default_local_config()["rows"])
            rows["senior-worker"] = {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"}
            models.models_json_path().write_text(json.dumps(config_with(rows)) + "\n")
            code = models.main(["row", role])
        return code, out.getvalue(), err.getvalue()

    def test_the_everyday_name_is_printed_as_the_host_id(self):
        self.assertEqual(self.row("senior-worker"), (0, "codex\tgpt-5.6-sol\thigh\n", ""))

    def test_an_unknown_role_is_refused(self):
        code, out, err = self.row("planner")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("cannot resolve the planner row", err)


class SessionRowsTest(unittest.TestCase):
    def test_one_row_per_agent_is_read_in_fixed_order(self):
        config = models.default_local_config()
        shuffled = {role: config["rows"][role] for role in reversed(models.ALLOWED_AGENTS)}
        rows = rows_from(shuffled)
        self.assertEqual(
            [r.agent for r in rows],
            ["junior-worker", "senior-worker", "reviewer", "advisor"])

    def test_an_unknown_agent_is_refused(self):
        config = models.default_local_config()["rows"]
        config["intern"] = {"host": "grok", "model": "grok 4.6", "effort": "high"}
        with self.assertRaisesRegex(ValueError, "unknown intern"):
            rows_from(config)


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


class DefaultsTest(unittest.TestCase):
    def test_defaults_include_the_five_roles(self):
        config = models.default_local_config()
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["runner"], "orca")
        self.assertEqual(set(config["rows"]), set(models.ALLOWED_AGENTS))


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

    # The control_response line of `list_models`, Claude Code 2.1.280, 2026-09-23,
    # trimmed to the fields read and one disabled placeholder row added.
    CLAUDE_LIST = json.dumps({"type": "control_response", "response": {
        "subtype": "success", "request_id": "mmw-model-list", "response": {"models": [
            {"value": "default", "displayName": "Default (recommended)",
             "description": "Opus 5.5 with 1M context · Best for everyday, complex tasks",
             "supportsEffort": True, "supportedEffortLevels": ["low", "high"]},
            {"value": "opus[1m]", "displayName": "Opus (1M context)",
             "description": "Opus 5.5 with 1M context · Best for everyday, complex tasks",
             "supportsEffort": True, "supportedEffortLevels": ["low", "medium", "high", "xhigh", "max"]},
            {"value": "claude-fable-5-1[1m]", "displayName": "Fable",
             "description": "Fable 5.1 · Most capable for your hardest and longest-running tasks",
             "supportsEffort": True, "supportedEffortLevels": ["low", "medium", "high"]},
            {"value": "sonnet", "displayName": "Sonnet",
             "description": "Sonnet 5 · Efficient for routine tasks",
             "supportsEffort": True, "supportedEffortLevels": ["low", "medium", "high"]},
            {"value": "cc-update-required-1", "displayName": "Fable 6 (disabled)",
             "disabled": True},
        ]}}})

    def test_claude_picker_rows_are_family_aliases_with_todays_model(self):
        rows = models._parse_claude_model_list(
            '{"type":"system","subtype":"init"}\n' + self.CLAUDE_LIST + "\n")
        self.assertEqual([r["id"] for r in rows], ["opus[1m]", "fable[1m]", "sonnet"])
        self.assertEqual(rows[0]["note"], "Opus 5.5 with 1M context")
        self.assertEqual(rows[1]["note"], "Fable 5.1")
        self.assertEqual(rows[1]["thinkingOptionIds"], ["low", "medium", "high"])

    def test_claude_without_list_models_offers_nothing(self):
        # A CLI that predates the request answers subtype error and still exits 0.
        self.assertEqual(models._parse_claude_model_list(
            '{"type":"control_response","response":{"subtype":"error"}}\n'), [])

    def test_claude_offered_rows_carry_the_note_and_resolve_to_the_alias(self):
        offerings = models._parse_claude_model_list(self.CLAUDE_LIST)
        offered = models._offered_rows("claude", offerings, "cli")
        self.assertEqual(offered[1], {"model": "fable[1m]", "efforts": ["low", "medium", "high"],
                                      "note": "Fable 5.1"})
        self.assertEqual(models._resolve_from_offerings(
            "claude", "fable[1m]", "high", offerings, "cli")[1], "fable[1m]")

    def test_codex_hidden_models_are_not_offered(self):
        raw = json.dumps({"models": [
            {"slug": "gpt-6-sol", "visibility": "list"},
            {"slug": "codex-auto-review", "visibility": "hide"},
            {"slug": "gpt-reserve", "visibility": "hide"},
        ]})
        self.assertEqual([r["id"] for r in models._parse_codex_debug_models(raw)], ["gpt-6-sol"])

    def test_every_grok_model_the_cli_lists_is_offered(self):
        rows = models.fillable_rows("grok", models._parse_grok_models(
            "Available models:\n  - grok-4.7\n  * grok-4.6 (default)\n  - grok-4.5\n"))
        self.assertEqual([m for m, _ in rows], ["grok 4.7", "grok 4.6", "grok 4.5"])

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


class RetiredCommandTest(unittest.TestCase):
    def test_offerings_is_a_usage_error(self):
        from io import StringIO
        from unittest.mock import patch
        with patch("sys.stderr", new_callable=StringIO) as err:
            self.assertEqual(models.main(["offerings"]), 2)
        self.assertIn("usage: models.py config show", err.getvalue())
