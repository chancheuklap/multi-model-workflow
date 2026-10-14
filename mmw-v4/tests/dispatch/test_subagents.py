from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from test_local_config import ALL_CATALOG, base_config, models


class SubagentsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        env = mock.patch.dict(os.environ, {
            "MMW_HOME": str(self.home), "MMW_HOST_CATALOG": str(ALL_CATALOG),
        })
        env.start()
        self.addCleanup(env.stop)

    def seed(self, config=None):
        (self.home / "models.json").write_text(json.dumps(config or base_config()) + "\n")

    def command(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = models.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def catalog(self):
        (self.home / "catalog.json").write_text(json.dumps({"cli": {"codex": {
            "offerings": [
                {"id": "gpt-6-luna", "name": "GPT-6-Luna", "thinkingOptionIds": ["low", "high", "ultra"]},
                {"id": "gpt-5.6-terra", "name": "GPT-5.6-Terra", "thinkingOptionIds": ["low", "high"]},
            ], "version": "codex 0.162.1", "read_at": "2026-10-14T00:00:00Z",
        }}}))

    def test_an_unset_row_prints_inherit(self):
        self.assertEqual(self.command("subagent", "review-axis", "claude"),
                         (0, "model=inherit effort=inherit\n", ""))
        self.assertFalse((self.home / "models.json").exists())
        for subagents in ({}, {"review-axis": {}}, {"reader": {"claude": {
                "model": "haiku", "effort": "medium"}}}):
            self.seed({**base_config(), "subagents": subagents})
            before = (self.home / "models.json").read_bytes()
            self.assertEqual(self.command("subagent", "review-axis", "claude"),
                             (0, "model=inherit effort=inherit\n", ""))
            self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_a_claude_row_set_is_read_back_and_shown(self):
        self.seed()
        code, out, err = self.command("config", "subagent", "reader", "claude", "haiku", "medium")
        self.assertEqual((code, err), (0, ""))
        written = json.loads(out)
        self.assertEqual(written["version"], 2)
        self.assertEqual(written["subagents"], {"reader": {"claude": {
            "model": "haiku", "effort": "medium"}}})
        self.assertEqual(self.command("subagent", "reader", "claude"),
                         (0, "model=haiku effort=medium\n", ""))
        code, out, err = self.command("config", "show")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), written)

    def refused(self, *args):
        before = (self.home / "models.json").read_bytes()
        code, out, err = self.command(*args)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual((self.home / "models.json").read_bytes(), before)
        return err

    def test_a_claude_model_the_spawn_call_does_not_take_is_refused(self):
        self.seed()
        err = self.refused("config", "subagent", "reader", "claude", "opus[1m]", "high")
        for choice in ("sonnet", "opus", "haiku", "fable", "inherit"):
            self.assertIn(choice, err)

    def test_a_claude_effort_outside_low_to_max_is_refused(self):
        self.seed()
        err = self.refused("config", "subagent", "reader", "claude", "opus", "ultra")
        for choice in ("low", "medium", "high", "xhigh", "max", "inherit"):
            self.assertIn(choice, err)

    def test_a_codex_model_missing_from_the_catalog_is_refused_with_the_choices(self):
        self.seed()
        self.catalog()
        err = self.refused("config", "subagent", "default", "codex", "gpt-9", "high")
        for choice in ("gpt-6-luna", "gpt-5.6-terra", "inherit"):
            self.assertIn(choice, err)

    def test_an_inherited_codex_model_refuses_an_effort_not_every_model_offers(self):
        self.seed()
        self.catalog()
        err = self.refused("config", "subagent", "default", "codex", "inherit", "ultra")
        for choice in ("low", "high", "inherit"):
            self.assertIn(choice, err)

    def test_a_codex_row_set_from_the_catalog_is_read_back(self):
        self.seed()
        self.catalog()
        for model in ("gpt-6-luna", "gpt-5.6-terra"):
            code, out, err = self.command("config", "subagent", "default", "codex", model, "high")
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["subagents"]["default"]["codex"],
                             {"model": model, "effort": "high"})
            self.assertEqual(self.command("subagent", "default", "codex"),
                             (0, f"model={model} effort=high\n", ""))

    def test_an_inherited_codex_model_takes_an_effort_every_model_offers(self):
        self.seed()
        self.catalog()
        code, out, err = self.command("config", "subagent", "default", "codex", "inherit", "high")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["subagents"]["default"]["codex"],
                         {"model": "inherit", "effort": "high"})
        self.assertEqual(self.command("subagent", "default", "codex"),
                         (0, "model=inherit effort=high\n", ""))

    def test_an_unknown_row_is_refused_with_the_three_rows(self):
        code, out, err = self.command("subagent", "writer", "claude")
        self.assertEqual((code, out), (2, ""))
        for row in ("review-axis", "reader", "default"):
            self.assertIn(row, err)
        self.assertFalse((self.home / "models.json").exists())

    def test_setting_a_role_keeps_the_subagent_rows(self):
        self.seed()
        fixture = json.loads(ALL_CATALOG.read_text())
        fixture["cli"]["claude"]["offerings"].append({
            "id": "sonnet", "name": "sonnet", "thinkingOptionIds": ["high"]})
        path = self.home / "role-catalog.json"
        path.write_text(json.dumps(fixture))
        os.environ["MMW_HOST_CATALOG"] = str(path)
        self.assertEqual(self.command("config", "subagent", "reader", "claude", "haiku", "medium")[0], 0)
        code, out, err = self.command("config", "set", "reviewer", "claude", "sonnet", "high")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["rows"]["reviewer"],
                         {"host": "claude", "model": "sonnet", "effort": "high"})
        self.assertEqual(json.loads(out)["subagents"], {"reader": {"claude": {
            "model": "haiku", "effort": "medium"}}})
        self.assertEqual(self.command("subagent", "reader", "claude"),
                         (0, "model=haiku effort=medium\n", ""))

    def test_other_configuration_commands_keep_codex_settings_without_a_catalog(self):
        for args in (("config", "set", "reviewer", "claude", "sonnet 5", "high"),
                     ("config", "runner", "herdr"), ("config", "set", "max_workers", "2")):
            with self.subTest(args=args):
                self.seed({**base_config(), "subagents": {"default": {"codex": {
                    "model": "gpt-6-luna", "effort": "high"}}}})
                code, out, err = self.command(*args)
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["subagents"], {"default": {"codex": {
                    "model": "gpt-6-luna", "effort": "high"}}})

    def test_a_codex_row_without_a_stored_catalog_only_takes_inherit(self):
        self.seed()
        err = self.refused("config", "subagent", "default", "codex", "gpt-6-luna", "high")
        self.assertIn("catalog.json", err)
        self.assertIn("重新扫描", err)
        self.assertIn("install.sh --check", err)
        self.refused("config", "subagent", "default", "codex", "inherit", "high")
        self.assertEqual(self.command("config", "subagent", "default", "codex", "inherit", "inherit")[0], 0)
        self.assertEqual(self.command("subagent", "default", "codex"),
                         (0, "model=inherit effort=inherit\n", ""))

    def test_a_selected_codex_model_only_takes_its_own_efforts(self):
        self.seed()
        self.catalog()
        self.refused("config", "subagent", "default", "codex", "gpt-5.6-terra", "ultra")
        self.assertEqual(self.command("config", "subagent", "default", "codex", "gpt-6-luna", "ultra")[0], 0)
        self.assertEqual(self.command("subagent", "default", "codex"),
                         (0, "model=gpt-6-luna effort=ultra\n", ""))

    def test_a_subagent_write_uses_the_existing_lock(self):
        self.seed()
        with models.config_lock(purpose="other settings writer"):
            err = self.refused("config", "subagent", "reader", "claude", "haiku", "medium")
        self.assertIn("other settings writer", err)
        self.assertEqual(self.command("config", "subagent", "reader", "claude", "haiku", "medium")[0], 0)

    def test_unknown_rows_and_hosts_are_refused_before_writing(self):
        self.seed()
        self.refused("config", "subagent", "writer", "claude", "haiku", "medium")
        err = self.refused("config", "subagent", "reader", "grok", "haiku", "medium")
        self.assertIn("claude", err)
        self.assertIn("codex", err)
        code, out, err = self.command("subagent", "reader", "grok")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("claude", err)

    def test_a_subagent_write_keeps_other_rows_hosts_and_settings(self):
        self.seed({**base_config(), "max_workers": 2, "subagents": {
            "reader": {"claude": {"model": "haiku", "effort": "medium"}},
            "default": {"claude": {"model": "opus", "effort": "high"}}}})
        self.catalog()
        code, out, err = self.command("config", "subagent", "reader", "codex", "gpt-6-luna", "high")
        self.assertEqual((code, err), (0, ""))
        written = json.loads(out)
        self.assertEqual(written["max_workers"], 2)
        self.assertEqual(written["rows"], base_config()["rows"])
        self.assertEqual(written["subagents"], {
            "reader": {"claude": {"model": "haiku", "effort": "medium"},
                       "codex": {"model": "gpt-6-luna", "effort": "high"}},
            "default": {"claude": {"model": "opus", "effort": "high"}}})

    def test_a_query_refuses_a_malformed_saved_subagent_setting_without_writing(self):
        for value in (None, [], {"reader": None}, {"reader": {"claude": "haiku"}},
                      {"reader": {"claude": {"model": False, "effort": "high"}}}):
            with self.subTest(value=value):
                self.seed({**base_config(), "subagents": value})
                self.assertIn("subagents", self.refused("subagent", "reader", "claude"))

    def test_a_subagent_write_keeps_unrelated_stale_codex_cells(self):
        for cache in (False, True):
            with self.subTest(cache=cache):
                self.seed({**base_config(), "subagents": {
                    "default": {"codex": {"model": "retired-model", "effort": "high"}},
                    "reader": {"codex": {"model": "retired-model", "effort": "high"}}}})
                if cache:
                    self.catalog()
                code, out, err = self.command("config", "subagent", "reader", "claude", "haiku", "medium")
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["subagents"], {
                    "default": {"codex": {"model": "retired-model", "effort": "high"}},
                    "reader": {"codex": {"model": "retired-model", "effort": "high"},
                               "claude": {"model": "haiku", "effort": "medium"}}})
                code, out, err = self.command("config", "subagent", "default", "codex", "inherit", "inherit")
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["subagents"], {
                    "default": {"codex": {"model": "inherit", "effort": "inherit"}},
                    "reader": {"codex": {"model": "retired-model", "effort": "high"},
                               "claude": {"model": "haiku", "effort": "medium"}}})

    def test_a_damaged_subagent_cell_can_be_repaired(self):
        for value in ("haiku", {"model": 5, "effort": "high"}):
            with self.subTest(value=value):
                self.seed({**base_config(), "subagents": {"reader": {"claude": value}}})
                code, out, err = self.command("config", "subagent", "reader", "claude", "haiku", "medium")
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["version"], 2)
                self.assertEqual(self.command("subagent", "reader", "claude"),
                                 (0, "model=haiku effort=medium\n", ""))


if __name__ == "__main__":
    unittest.main()
