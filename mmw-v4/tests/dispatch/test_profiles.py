"""Local configuration, catalog match, and host argv from hosts.json.

    python3 -m unittest discover -s mmw-v4/tests/dispatch -p test_profiles.py
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
    def test_claude_reviewer_takes_the_session_name(self):
        argv = models.bypass_argv(
            "claude", "claude-opus-5", "high", "issue-61-review")
        self.assertEqual(argv, [
            "--model", "claude-opus-5", "--effort", "high",
            "--permission-mode", "bypassPermissions", "-n", "issue-61-review",
        ])

    def test_a_host_without_a_cli_block_is_refused(self):
        data = models.load_hosts()
        data["hosts"]["codex"].pop("cli")
        with mock.patch.object(models, "load_hosts", return_value=data), \
                self.assertRaisesRegex(ValueError, "codex.*cli"):
            models.bypass_argv("codex", "x", "low", "issue-1")

    def test_the_command_line_block_is_named_cli(self):
        hosts = models.load_hosts()["hosts"]
        self.assertEqual(
            sorted(h for h, spec in hosts.items() if "cli" in spec),
            ["claude", "codex"])
        self.assertEqual([h for h, spec in hosts.items() if "herdr" in spec], [])


class LaunchLineTest(unittest.TestCase):
    PROMPT = "Use the implement skill on #61. Don't ask 'Shall I…?'"
    FLAGS = ["-m", "gpt-5.6-sol", "-c", 'model_reasoning_effort="high"',
             "--dangerously-bypass-approvals-and-sandbox"]

    def launch_line(self, *args: str) -> tuple[int, str, str]:
        from io import StringIO
        from unittest.mock import patch
        with patch("sys.stdout", new_callable=StringIO) as out, \
                patch("sys.stderr", new_callable=StringIO) as err:
            code = models.main(["launch-line", *args])
        return code, out.getvalue(), err.getvalue()

    def test_the_prompt_is_the_last_argument_quoted(self):
        code, out, _ = self.launch_line("codex", "gpt-5.6-sol", "high", "issue-61", self.PROMPT)
        self.assertEqual(code, 0)
        self.assertEqual(shlex.split(out), ["codex", *self.FLAGS, self.PROMPT])
        self.assertTrue(out.rstrip("\n").endswith(" " + shlex.quote(self.PROMPT)), out)

    def test_without_a_prompt_the_line_ends_with_the_flags(self):
        code, out, _ = self.launch_line("codex", "gpt-5.6-sol", "high", "issue-61")
        self.assertEqual(code, 0)
        self.assertEqual(shlex.split(out), ["codex", *self.FLAGS])

    def test_a_prompt_that_reads_as_a_flag_is_refused(self):
        code, out, _ = self.launch_line("codex", "gpt-5.6-sol", "high", "issue-61", "--help")
        self.assertEqual((code, out), (2, ""))


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
        self.assertIn("planner", err)


class SessionRowsTest(unittest.TestCase):
    def test_one_row_per_agent_is_read_in_fixed_order(self):
        config = models.default_local_config()
        shuffled = {role: config["rows"][role] for role in reversed(models.ALLOWED_AGENTS)}
        rows = rows_from(shuffled)
        self.assertEqual([r.agent for r in rows], list(models.ALLOWED_AGENTS))
        self.assertEqual(list(models.ALLOWED_AGENTS)[:3], ["junior-worker", "senior-worker", "reviewer"])

    def test_an_unknown_agent_is_refused(self):
        config = models.default_local_config()["rows"]
        config["intern"] = {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"}
        with self.assertRaisesRegex(ValueError, "intern"):
            rows_from(config)


class CatalogMatchTest(unittest.TestCase):
    def setUp(self):
        os.environ["MMW_HOST_CATALOG"] = str(CATALOG)
        os.environ["MMW_CATALOG_MODE"] = "paseo"
        self.addCleanup(os.environ.pop, "MMW_HOST_CATALOG", None)
        self.addCleanup(os.environ.pop, "MMW_CATALOG_MODE", None)

    def test_the_everyday_name_resolves_to_the_catalog_id(self):
        self.assertEqual(models.resolve_row("codex", "gpt 5.6 sol", "high"),
                         ("codex", "gpt-5.6-sol", "high"))

    def test_a_partial_name_takes_the_ordinary_offering_unless_it_says_fast(self):
        offerings = [{"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol"},
                     {"id": "gpt-5.6-sol-fast", "name": "GPT-5.6-Sol Fast"}]
        self.assertEqual(models.match_offering("5.6 sol", offerings)["id"], "gpt-5.6-sol")
        self.assertEqual(models.match_offering("5.6 sol fast", offerings)["id"],
                         "gpt-5.6-sol-fast")

    def test_a_miss_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no-such-model"):
            models.resolve_row("codex", "no-such-model", "high")

    def test_opus_5_is_unique_on_claude(self):
        _, model, _ = models.resolve_row("claude", "opus 5", "high")
        self.assertEqual(model, "claude-opus-5")

    def test_a_bracket_suffix_absent_from_the_catalog_passes_through(self):
        # The `/model` picker stopped listing a `[1m]` row of its own (Claude Code
        # 2.1.283); the catalog here carries only the plain family alias.
        offerings = [{"id": "opus", "name": "opus",
                      "thinkingOptionIds": ["low", "medium", "high"]}]
        host, model, effort = models._resolve_from_offerings(
            "claude", "opus[1m]", "high", offerings, "cli")
        self.assertEqual((host, model, effort), ("claude", "opus[1m]", "high"))

    def test_ultracode_is_not_a_claude_effort(self):
        # Claude Code 2.1.284 made Ultracode a switch of its own beside `/effort`; the
        # picker's effort levels end at max, and `claude --effort` lists no ultracode.
        offerings = [{"id": "opus", "name": "opus",
                      "thinkingOptionIds": ["low", "medium", "high", "xhigh", "max"]}]
        with self.assertRaisesRegex(ValueError, "effort 'ultracode'"):
            models._resolve_from_offerings("claude", "opus", "ultracode", offerings, "cli")
        self.assertNotIn("ultracode", ", ".join(
            effort for _, effort in models.fillable_rows("claude", [{"id": "opus"}])))


class PaseoSettingsTest(unittest.TestCase):
    def test_the_everyday_effort_name_is_the_thinking_option(self):
        self.assertEqual(models.thinking_option("codex", "high"), "high")
        self.assertIsNone(models.thinking_option("codex", "—"))

    def test_codex_create_agent_settings_are_full_access(self):
        self.assertEqual(models.create_agent_settings("codex"), {"modeId": "full-access"})


class DefaultsTest(unittest.TestCase):
    def test_defaults_include_every_session_role(self):
        config = models.default_local_config()
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["runner"], "orca")
        self.assertEqual(set(config["rows"]), set(models.ALLOWED_AGENTS))


class CliCatalogParseTest(unittest.TestCase):
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

    def test_fillable_rows_are_the_cells_to_copy(self):
        rows = models.fillable_rows("codex", [
            {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol", "thinkingOptionIds": ["high", "low"]},
        ])
        self.assertEqual(rows, [("gpt 5.6 sol", "low, high")])


class RetiredCommandTest(unittest.TestCase):
    def test_offerings_is_a_usage_error(self):
        from io import StringIO
        from unittest.mock import patch
        with patch("sys.stderr", new_callable=StringIO):
            self.assertEqual(models.main(["offerings"]), 2)
