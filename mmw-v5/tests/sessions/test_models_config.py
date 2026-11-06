from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "tools" / "dispatch" / "scripts" / "models.py"
OFFERINGS = {
    "claude": {"offerings": [
        {"id": "claude-opus-5", "name": "Opus 5", "thinkingOptionIds": ["high"]},
        {"id": "claude-sonnet-5", "name": "Sonnet 5", "thinkingOptionIds": ["high"]},
        {"id": "claude-fable-5-1", "name": "Fable 5.1", "thinkingOptionIds": ["medium"]},
    ]},
    "codex": {"offerings": [
        {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol", "thinkingOptionIds": ["high"]},
    ]},
}
CATALOGS = {
    "all": {"cli": OFFERINGS, "paseo": OFFERINGS},
    "cli": {
        "cli": {
            "claude": {"offerings": [
                {"id": "claude-opus-5", "name": "Opus 5", "thinkingOptionIds": ["high"]},
            ]},
            "codex": {"state": "missing"},
        },
        "paseo": {"state": "down"},
    },
}
_spec = importlib.util.spec_from_file_location("local_config_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)


def without_launch_block(host, block="cli"):
    """hosts.json as it is, except that `host` has no `block`: a host that runner cannot start."""
    data = models.load_hosts()
    data["hosts"][host].pop(block)
    return mock.patch.object(models, "load_hosts", return_value=data)


def base_config(version=1, runner="orca"):
    """The four rows the cases change by name; every other role of roles.json on one row the
    test catalog offers, so a role added to the table needs no change here."""
    rows = {
        "junior-worker": {"host": "claude", "model": "sonnet 5", "effort": "high"},
        "senior-worker": {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"},
        "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
        "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
    }
    for role in models.ALLOWED_AGENTS:
        rows.setdefault(role, {"host": "claude", "model": "opus 5", "effort": "high"})
    return {"version": version, "runner": runner, "rows": rows}


def isolate_models(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.home = Path(self.tmp.name)
    env = mock.patch.dict(os.environ, {
        "MMW_HOME": str(self.home),
        "MMW_HOST_CATALOG": str(self.home / "all.json"),
        "MMW_CATALOG_MODE": "cli", "MMW_RUNNER": "",
        "HERDR_ENV": "", "TERM_PROGRAM": "", "CODEX_THREAD_ID": "",
        "CODEX_APP_RUNTIME_CLI_PATH": "", "CODEX_APP_TOOLS_PIPE_PATH": "",
    })
    for name, catalog in CATALOGS.items():
        (self.home / f"{name}.json").write_text(json.dumps(catalog))
    self.adapters = self.home / "runners"
    self.adapters.mkdir()
    for name, capability in (("orca", "cli"), ("herdr", "cli"), ("paseo", "paseo")):
        (self.adapters / f"{name}.sh").write_text(
            "# MMW_RUNNER: " + json.dumps({"catalog": "paseo" if name == "paseo" else "cli", "launch": capability}) + "\n")
    runners = mock.patch.object(models, "RUNNERS_DIR", self.adapters)
    runners.start()
    self.addCleanup(runners.stop)
    env.start()
    self.addCleanup(env.stop)


class LocalConfigTest(unittest.TestCase):
    def setUp(self):
        isolate_models(self)

    def seed(self, config=None):
        config = config or base_config()
        self.home.mkdir(parents=True, exist_ok=True)
        models.models_json_path().write_text(json.dumps(config) + "\n", encoding="utf-8")
        return config

    def scan(self, runner="orca"):
        return models.scan_host_catalogs(runner)

    def test_a_write_refuses_an_invalid_max_workers(self):
        for value in (0, -1, True, False, "3", 1.5):
            with self.subTest(value=value):
                old = self.seed()
                before = models.models_json_path().read_bytes()
                proposed = {**old, "max_workers": value}
                with self.assertRaises(models.InvalidConfig) as caught:
                    models.write_local_config(proposed, 1, self.scan())
                self.assertEqual([error["cell"] for error in caught.exception.errors], ["max_workers"])
                self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_the_default_configuration_sets_max_workers_to_3(self):
        models.init_local_config()
        self.assertEqual(models.read_local_config()["max_workers"], 3)

    def test_max_workers_reads_3_when_models_json_does_not_set_it(self):
        self.seed()
        before = models.models_json_path().read_bytes()
        self.assertEqual(models.max_workers(), 3)
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_max_workers_reads_the_saved_value_without_checking_roles(self):
        self.seed({"max_workers": 2, "rows": None})
        self.assertEqual(models.max_workers(), 2)

    def test_max_workers_refuses_an_unreadable_configuration(self):
        self.seed()
        models.models_json_path().write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            models.max_workers()

    def test_max_workers_refuses_a_missing_configuration(self):
        with self.assertRaises(models.ConfigMissing):
            models.max_workers()

    def test_max_workers_refuses_an_invalid_saved_value(self):
        for value in (0, True):
            with self.subTest(value=value):
                self.seed({**base_config(), "max_workers": value})
                with self.assertRaises(models.InvalidConfig) as caught:
                    models.max_workers()
                self.assertEqual([error["cell"] for error in caught.exception.errors], ["max_workers"])

    def test_a_write_without_max_workers_keeps_the_saved_value(self):
        self.seed({**base_config(), "max_workers": 2})
        written = models.write_local_config(base_config(), 1, self.scan())
        self.assertEqual(written.get("max_workers"), 2)
        self.assertEqual(models.read_local_config()["max_workers"], 2)

    def test_a_write_without_max_workers_keeps_an_invalid_saved_value(self):
        for value in (0, True):
            with self.subTest(value=value):
                self.seed({**base_config(), "max_workers": value})
                written = models.write_local_config(base_config(), 1, self.scan())
                self.assertEqual(written["max_workers"], value)
                self.assertEqual(models.read_local_config()["max_workers"], value)

    def test_setting_max_workers_refuses_an_invalid_version(self):
        for value in ("2", 0, None):
            with self.subTest(value=value):
                self.seed(base_config(version=value))
                before = models.models_json_path().read_bytes()
                out, err = StringIO(), StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    code = models.main(["config", "set", "max_workers", "2"])
                self.assertEqual((code, out.getvalue()), (2, ""))
                self.assertTrue(err.getvalue().startswith("models.py: version: "))
                self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_cli_sets_max_workers(self):
        self.seed()
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = models.main(["config", "set", "max_workers", "2"])
        self.assertEqual((code, err.getvalue()), (0, ""))
        expected = {**base_config(version=2), "max_workers": 2}
        self.assertEqual(json.loads(out.getvalue()), expected)
        self.assertEqual(models.read_local_config(), expected)

    def test_cli_refuses_a_max_workers_that_is_not_a_whole_number_of_at_least_1(self):
        self.seed()
        before = models.models_json_path().read_bytes()
        for value in ("0", "-1", "true", "1.5", "x"):
            with self.subTest(value=value):
                out, err = StringIO(), StringIO()
                with redirect_stdout(out), redirect_stderr(err):
                    code = models.main(["config", "set", "max_workers", value])
                self.assertEqual((code, out.getvalue()), (2, ""))
                self.assertTrue(err.getvalue().startswith("models.py: max_workers: "))
                self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_setting_a_role_keeps_max_workers(self):
        self.seed({**base_config(), "max_workers": 2})
        with redirect_stdout(out := StringIO()):
            self.assertEqual(models.main(
                ["config", "set", "reviewer", "claude", "sonnet 5", "high"]), 0)
        self.assertEqual(json.loads(out.getvalue())["max_workers"], 2)
        self.assertEqual(models.read_local_config()["max_workers"], 2)

    def test_setting_the_runner_keeps_max_workers(self):
        self.seed({**base_config(), "max_workers": 2})
        with redirect_stdout(out := StringIO()):
            self.assertEqual(models.main(["config", "runner", "herdr"]), 0)
        self.assertEqual(json.loads(out.getvalue())["max_workers"], 2)
        self.assertEqual(models.read_local_config()["max_workers"], 2)

    def test_setting_max_workers_scans_no_catalog(self):
        os.environ["MMW_HOST_CATALOG"] = str(self.home / "cli.json")
        old = self.seed({**base_config(), "rows": None, "runner": "unavailable"})
        with redirect_stdout(out := StringIO()):
            self.assertEqual(models.main(["config", "set", "max_workers", "2"]), 0)
        expected = {**old, "version": 2, "max_workers": 2}
        self.assertEqual(json.loads(out.getvalue()), expected)
        self.assertEqual(models.read_local_config(), expected)
        os.environ["MMW_HOST_CATALOG"] = str(self.home / "missing-catalog.json")
        with redirect_stdout(out := StringIO()):
            self.assertEqual(models.main(["config", "set", "max_workers", "1"]), 0)
        self.assertEqual(json.loads(out.getvalue())["max_workers"], 1)
        self.assertEqual(models.read_local_config()["max_workers"], 1)

    def test_an_invalid_max_workers_does_not_stop_a_session_start(self):
        self.seed({**base_config(), "max_workers": 0})
        rows = models.session_rows()
        self.assertEqual([tuple(row) for row in rows], [
            (role, "claude", "sonnet 5", "high") if role == "junior-worker" else
            (role, "codex", "gpt 5.6 sol", "high") if role == "senior-worker" else
            (role, "claude", "fable 5.1", "medium") if role == "advisor" else
            (role, "claude", "opus 5", "high") for role in models.ALLOWED_AGENTS])

    def test_write_raises_the_version_by_one(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        scan = self.scan()
        written = models.write_local_config(proposed, old["version"], scan)
        self.assertEqual(written["version"], 2)
        self.assertEqual(set(written), {"version", "runner", "rows"})
        self.assertEqual(set(written["rows"]), set(models.ALLOWED_AGENTS))
        on_disk = json.loads(models.models_json_path().read_text(encoding="utf-8"))
        self.assertEqual(on_disk, written)
        self.assertEqual(on_disk["rows"]["reviewer"]["model"], "sonnet 5")

    def test_refuses_a_host_the_runner_cannot_start(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        before = models.models_json_path().read_bytes()
        with without_launch_block("codex"), \
                self.assertRaisesRegex(models.InvalidConfig, "senior-worker.host.*orca.*codex"):
            models.write_local_config(proposed, 1, self.scan())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_refuses_a_cell_the_catalog_lacks(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["reviewer"]["model"] = "retired model"
        before = models.models_json_path().read_bytes()
        with self.assertRaisesRegex(models.InvalidConfig, "reviewer.model.*retired model"):
            models.write_local_config(proposed, 1, self.scan())
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["reviewer"]["effort"] = "xhigh"
        with self.assertRaisesRegex(models.InvalidConfig, "reviewer.effort.*xhigh"):
            models.write_local_config(proposed, 1, self.scan())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_refuses_an_unknown_runner(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old)); proposed["runner"] = "tmux"
        before = models.models_json_path().read_bytes()
        with self.assertRaisesRegex(models.InvalidConfig, "runner.*tmux"):
            models.write_local_config(proposed, 1, self.scan())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_refuses_a_stale_version(self):
        self.seed(base_config(version=2))
        before = models.models_json_path().read_bytes()
        with self.assertRaisesRegex(models.VersionConflict, r"\b1\b.*\b2\b"):
            models.write_local_config(base_config(version=1), 1, self.scan())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_refuses_while_the_lock_is_held(self):
        self.seed()
        before = models.models_json_path().read_bytes()
        with models.config_lock(purpose="test holder"):
            holder = json.loads(models.models_lock_path().read_text(encoding="utf-8"))
            with self.assertRaisesRegex(models.ConfigLockHeld, "pid .*test holder") as caught:
                models.write_local_config(base_config(), 1, self.scan())
            self.assertEqual(caught.exception.holder["pid"], holder["pid"])
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_lock_sits_beside_models_json(self):
        self.seed()
        with models.config_lock(purpose="location"):
            record = json.loads(models.models_lock_path().read_text(encoding="utf-8"))
            self.assertEqual(record["pid"], os.getpid())
            self.assertTrue(record["identity"])
        self.assertEqual(models.models_lock_path().parent, models.models_json_path().parent)
        self.assertEqual(models.models_json_path().parent, self.home)

    def test_models_json_follows_mmw_home(self):
        elsewhere = self.home / "elsewhere"
        elsewhere.mkdir()
        other = elsewhere / "models.json"
        other.write_text(json.dumps(base_config(version=40)) + "\n", encoding="utf-8")
        other_before = other.read_bytes()
        self.seed()
        written = models.write_local_config(base_config(), 1, self.scan())
        self.assertEqual(written["version"], 2)
        self.assertTrue((self.home / "models.json").is_file())
        self.assertEqual(other.read_bytes(), other_before)

    def test_cli_sets_one_row(self):
        self.seed()
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = models.main(["config", "set", "reviewer", "claude", "sonnet 5", "high"])
        self.assertEqual((code, err.getvalue()), (0, ""))
        self.assertEqual(json.loads(out.getvalue())["version"], 2)
        self.assertEqual(models.read_local_config()["rows"]["reviewer"]["model"], "sonnet 5")
        before = models.models_json_path().read_bytes()
        with redirect_stdout(StringIO()), redirect_stderr(err := StringIO()):
            code = models.main(["config", "set", "reviewer", "claude", "not there", "high"])
        self.assertNotEqual(code, 0)
        self.assertIn("reviewer.model", err.getvalue())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_cli_sets_the_runner(self):
        self.seed()
        with redirect_stdout(StringIO()) as out:
            self.assertEqual(models.main(["config", "runner", "herdr"]), 0)
        self.assertEqual(json.loads(out.getvalue())["version"], 2)
        with redirect_stdout(StringIO()) as out:
            self.assertEqual(models.main(["config", "show"]), 0)
        self.assertEqual(json.loads(out.getvalue())["runner"], "herdr")

    def test_auto_and_paseo_are_valid_saved_runners(self):
        for runner in ("auto", "paseo"):
            self.seed()
            proposed = base_config(runner=runner)
            written = models.write_local_config(proposed, 1, self.scan(runner))
            self.assertEqual(written["runner"], runner)

    def test_every_scanned_cell_resolves_for_start(self):
        for runner in ("orca", "paseo"):
            scan = self.scan(runner)
            os.environ["MMW_CATALOG_MODE"] = scan["source"]
            self.assertEqual(set(scan["hosts"]), set(models.CLI_HOSTS))
            for host, result in scan["hosts"].items():
                for offered in result["offered"]:
                    for effort in offered["efforts"]:
                        resolved = models.resolve_row(host, offered["model"], effort)
                        self.assertEqual((resolved[0], resolved[2]), (host, effort))

    def test_scan_tells_missing_from_silent(self):
        os.environ["MMW_HOST_CATALOG"] = str(self.home / "cli.json")
        scan = models.scan_host_catalogs("auto")
        self.assertEqual(set(scan["hosts"]), {"claude", "codex"})
        self.assertEqual(scan["hosts"]["codex"]["state"], "missing")
        self.assertEqual(scan["hosts"]["claude"]["offered"], [{"model": "opus 5", "efforts": ["high"]}])
        silent = json.loads((self.home / "cli.json").read_text())
        silent["cli"]["claude"] = {"state": "silent"}
        catalog = Path(self.tmp.name) / "silent.json"
        catalog.write_text(json.dumps(silent))
        os.environ["MMW_HOST_CATALOG"] = str(catalog)
        self.assertEqual(models.scan_host_catalogs("auto")["hosts"]["claude"]["state"], "silent")

    def test_unlaunchable_comes_before_the_scan(self):
        with without_launch_block("codex"):
            for runner in ("orca", "herdr"):
                self.assertEqual(self.scan(runner)["hosts"]["codex"]["state"], "unlaunchable")

    def test_paseo_down_marks_every_host(self):
        os.environ["MMW_HOST_CATALOG"] = str(self.home / "cli.json")
        scan = self.scan("paseo")
        self.assertEqual(scan["source"], "paseo")
        self.assertEqual({x["state"] for x in scan["hosts"].values()}, {"down"})

    def test_refuses_when_models_json_is_missing(self):
        with self.assertRaisesRegex(models.ConfigMissing, "models.json.*models.py init"):
            models.write_local_config(base_config(), 1, self.scan())
        self.assertFalse(models.models_json_path().exists())

    def test_init_preserves_an_incomplete_existing_configuration(self):
        old = base_config()
        del old["rows"]["researcher"]
        self.seed(old)
        before = models.models_json_path().read_bytes()
        result = models.init_local_config()
        self.assertFalse(result.created)
        self.assertEqual(result.config, old)
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_a_malformed_role_is_reported_once(self):
        config = base_config()
        config["rows"]["reviewer"] = None
        errors = models.check_local_config(config)[2]
        self.assertEqual([item["cell"] for item in errors if item["cell"].startswith("reviewer")],
                         ["reviewer"])

    def test_a_claude_bracket_suffix_the_catalog_does_not_list_is_checked_by_its_name(self):
        scan = self.scan()
        offered = scan["hosts"]["claude"]["offered"][0]
        config = base_config()
        config["rows"]["reviewer"] = {"host": "claude", "model": offered["model"] + "[1m]",
                                      "effort": offered["efforts"][0]}
        errors = models.check_local_config(config)[2]
        self.assertEqual([item for item in errors if item["cell"].startswith("reviewer")], [])
        config["rows"]["reviewer"]["model"] = "no such model[1m]"
        errors = models.check_local_config(config)[2]
        self.assertEqual([item["cell"] for item in errors if item["cell"].startswith("reviewer")],
                         ["reviewer.model"])

    def test_init_command_creates_config_without_scanning_or_installing(self):
        os.environ["MMW_HOST_CATALOG"] = str(self.home / "absent.json")
        with redirect_stdout(out := StringIO()), redirect_stderr(err := StringIO()):
            code = models.main(["init"])
        self.assertEqual((code, err.getvalue()), (0, ""))
        config = json.loads(out.getvalue())
        self.assertEqual(models.read_local_config(), config)
        self.assertEqual(config["rows"]["junior-worker"],
                         {"host": "codex", "model": "gpt 6.1 sol", "effort": "medium"})
        self.assertNotIn("retro-analyst", config["rows"])
        self.assertFalse((self.home / "catalog.json").exists())

    def test_init_keeps_user_settings_and_version_exactly(self):
        self.seed({**base_config(version=29), "max_workers": 1, "subagents": {
            "reader": {"claude": {"model": "haiku", "effort": "high"}}}})
        before = models.models_json_path().read_bytes()
        with redirect_stdout(out := StringIO()):
            self.assertEqual(models.main(["init"]), 0)
        self.assertEqual(models.models_json_path().read_bytes(), before)
        self.assertEqual(json.loads(out.getvalue())["version"], 29)

    def test_init_refuses_corrupt_config_without_replacing_it(self):
        models.models_json_path().write_text("{not json")
        before = models.models_json_path().read_bytes()
        with redirect_stdout(out := StringIO()), redirect_stderr(err := StringIO()):
            code = models.main(["init"])
        self.assertEqual((code, out.getvalue()), (2, ""))
        self.assertIn("cannot read", err.getvalue())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_init_refuses_an_active_configuration_writer(self):
        with models.config_lock(purpose="another config writer"):
            with redirect_stdout(out := StringIO()), redirect_stderr(err := StringIO()):
                code = models.main(["init"])
        self.assertEqual((code, out.getvalue()), (2, ""))
        self.assertIn("another config writer", err.getvalue())
        self.assertFalse(models.models_json_path().exists())

    def test_missing_config_does_not_read_an_old_mmw_home(self):
        legacy = self.home / ".mmw"
        legacy.mkdir()
        (legacy / "models.json").write_text(json.dumps(base_config(version=73)))
        with mock.patch.object(models.statedir.Path, "home", return_value=self.home):
            with mock.patch.dict(os.environ):
                os.environ.pop("MMW_HOME", None)
                with self.assertRaisesRegex(models.ConfigMissing, r"\.mmw-v5.*models.py init"):
                    models.read_local_config()
                with redirect_stdout(out := StringIO()):
                    self.assertEqual(models.main(["init"]), 0)
                self.assertEqual(models.models_json_path(), self.home / ".mmw-v5" / "models.json")
                self.assertEqual(json.loads(out.getvalue())["version"], 1)
        self.assertEqual(json.loads((legacy / "models.json").read_text())["version"], 73)

    def test_scan_command_returns_catalog_without_requiring_config(self):
        with redirect_stdout(out := StringIO()), redirect_stderr(err := StringIO()):
            code = models.main(["scan", "cli"])
        self.assertEqual((code, err.getvalue()), (0, ""))
        self.assertEqual(json.loads(out.getvalue())["hosts"]["codex"]["offered"],
                         [{"model": "gpt 5.6 sol", "efforts": ["high"]}])
        self.assertFalse(models.models_json_path().exists())

    def test_scan_refuses_unknown_runner_without_creating_config(self):
        with redirect_stdout(out := StringIO()), redirect_stderr(err := StringIO()):
            code = models.main(["scan", "unknown"])
        self.assertEqual((code, out.getvalue()), (2, ""))
        self.assertIn("unknown", err.getvalue())
        self.assertFalse(models.models_json_path().exists())

    def test_fresh_cli_config_can_select_and_resolve_a_role(self):
        def command(*args):
            result = subprocess.run([sys.executable, str(MODELS_PY), *args],
                                    capture_output=True, text=True, env=os.environ.copy())
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

        self.assertEqual(json.loads(command("init"))["version"], 1)
        selected = json.loads(command("config", "set", "senior-worker", "codex",
                                      "gpt 5.6 sol", "high"))
        self.assertEqual(selected["version"], 2)
        self.assertEqual(command("row", "senior-worker"), "codex\tgpt-5.6-sol\thigh\n")
        self.assertEqual(command("runner"), "orca\n")


if __name__ == "__main__":
    unittest.main()
