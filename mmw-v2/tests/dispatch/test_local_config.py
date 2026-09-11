from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS_PY = HERE.parents[1] / "skills" / "dispatch" / "scripts" / "models.py"
ALL_CATALOG = HERE / "catalogs" / "all.json"
STATE_CATALOG = HERE / "catalogs" / "cli.json"
_spec = importlib.util.spec_from_file_location("local_config_models", MODELS_PY)
models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(models)


def base_config(version=1, runner="orca"):
    return {
        "version": version,
        "runner": runner,
        "rows": {
            "junior-worker": {"host": "grok", "model": "grok 4.6", "effort": "high"},
            "senior-worker": {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"},
            "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
            "verifier": {"host": "claude", "model": "sonnet 5", "effort": "high"},
            "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
        },
    }


class LocalConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        env = mock.patch.dict(os.environ, {
            "MMW_HOME": str(self.home),
            "MMW_HOST_CATALOG": str(ALL_CATALOG),
        })
        env.start()
        self.addCleanup(env.stop)

    def seed(self, config=None):
        config = config or base_config()
        self.home.mkdir(parents=True, exist_ok=True)
        models.models_json_path().write_text(json.dumps(config) + "\n", encoding="utf-8")
        return config

    def scan(self, runner="orca"):
        return models.scan_host_catalogs(runner)

    def test_write_raises_the_version_by_one(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        scan = self.scan()
        cursor = scan["hosts"]["cursor"]["offered"]
        self.assertEqual(cursor, [{"model": "grok 4.6", "efforts": ["high", "xhigh"]}])
        written = models.write_local_config(proposed, old["version"], scan)
        self.assertEqual(written["version"], 2)
        self.assertEqual(set(written), {"version", "runner", "rows"})
        self.assertEqual(set(written["rows"]), {
            "junior-worker", "senior-worker", "reviewer", "verifier", "advisor"})
        on_disk = json.loads(models.models_json_path().read_text(encoding="utf-8"))
        self.assertEqual(on_disk, written)
        self.assertEqual(on_disk["rows"]["reviewer"]["model"], "sonnet 5")

    def test_refuses_a_host_the_runner_cannot_start(self):
        old = self.seed()
        proposed = json.loads(json.dumps(old))
        proposed["rows"]["senior-worker"]["host"] = "pi"
        before = models.models_json_path().read_bytes()
        with self.assertRaisesRegex(models.InvalidConfig, "senior-worker.host.*orca.*pi"):
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
        with self.assertRaisesRegex(models.VersionConflict, "expected version 1.*found 2"):
            models.write_local_config(base_config(version=1), 1, self.scan())
        self.assertEqual(models.models_json_path().read_bytes(), before)

    def test_refuses_while_the_lock_is_held(self):
        self.seed()
        before = models.models_json_path().read_bytes()
        with models.config_lock(purpose="test holder"):
            holder = json.loads(models.models_lock_path().read_text(encoding="utf-8"))
            with self.assertRaisesRegex(models.ConfigLockHeld, "pid .*test holder.*retry") as caught:
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
        os.environ["MMW_HOST_CATALOG"] = str(STATE_CATALOG)
        scan = models.scan_host_catalogs("auto")
        self.assertEqual(set(scan["hosts"]), set(models.CLI_HOSTS))
        self.assertEqual(scan["hosts"]["cursor"]["state"], "missing")
        self.assertEqual(scan["hosts"]["cursor"]["label"], "本机没装")
        self.assertEqual(scan["hosts"]["grok"]["state"], "silent")
        self.assertEqual(scan["hosts"]["grok"]["label"], "没有回答")
        self.assertEqual(scan["hosts"]["claude"]["offered"], [{"model": "opus 5", "efforts": ["high"]}])

    def test_unlaunchable_comes_before_the_scan(self):
        scan = self.scan("orca")
        self.assertEqual(scan["hosts"]["pi"]["state"], "unlaunchable")
        scan = self.scan("herdr")
        self.assertEqual(scan["hosts"]["pi"]["state"], "unlaunchable")

    def test_paseo_down_marks_every_host(self):
        os.environ["MMW_HOST_CATALOG"] = str(STATE_CATALOG)
        scan = self.scan("paseo")
        self.assertEqual(scan["source"], "paseo")
        self.assertEqual({x["state"] for x in scan["hosts"].values()}, {"down"})
        self.assertEqual({x["label"] for x in scan["hosts"].values()}, {"Paseo 没开"})

    def test_refuses_when_models_json_is_missing(self):
        with self.assertRaisesRegex(models.ConfigMissing, "models.json.*install.sh"):
            models.write_local_config(base_config(), 1, self.scan())
        self.assertFalse(models.models_json_path().exists())

    def test_install_imports_a_legacy_file_without_runner_as_auto(self):
        legacy = self.home / "models.md"
        rows = base_config()["rows"]
        legacy.write_text(
            "| agent | host | model | effort |\n"
            + "".join(
                f"| {role} | {row['host']} | {row['model']} | {row['effort']} |\n"
                for role, row in rows.items()
            ),
            encoding="utf-8",
        )
        result = models.install_local_config(legacy)
        self.assertEqual((result.created, result.imported), (True, True))
        self.assertEqual(result.config["runner"], "auto")
        self.assertFalse(legacy.exists())
        self.assertEqual(models.read_local_config(), result.config)

    def test_a_malformed_role_is_reported_once(self):
        config = base_config()
        config["rows"]["reviewer"] = None
        errors = models._validate_local_config(config, self.scan())
        self.assertEqual(
            [item for item in errors if item["cell"] == "reviewer"],
            [{"cell": "reviewer", "reason": "host, model, and effort are required"}],
        )


if __name__ == "__main__":
    unittest.main()
