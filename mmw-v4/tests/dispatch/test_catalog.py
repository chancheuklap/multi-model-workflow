"""Host catalog reads against executable fakes in an isolated home."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from test_local_config import models

CODEX_ROWS = [
    {"id": "gpt-6-sol", "displayName": "GPT-6-Sol", "hidden": False,
     "supportedReasoningEfforts": [{"reasoningEffort": "low"}, {"reasoningEffort": "high"}],
     "isDefault": True},
    {"id": "codex-auto-review", "displayName": "Codex Auto Review", "hidden": True,
     "supportedReasoningEfforts": [{"reasoningEffort": "low"}], "isDefault": False},
]


def fake_host(home: Path, host: str) -> Path:
    binary = home / ".local" / "bin" / host
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(f"#!{sys.executable}\n" + '''import json, sys, time
from pathlib import Path
home = Path.home()
host = Path(sys.argv[0]).name
with (home / (host + '.log')).open('a') as log:
    log.write(' '.join(sys.argv[1:]) + '\\n')
if sys.argv[1:] == ['--version']:
    print((home / (host + '.version')).read_text().strip())
    sys.exit(0)
mode = (home / (host + '.mode')).read_text().strip()
if mode == 'exit':
    print('boom\\nsecond line', file=sys.stderr)
    sys.exit(3)
if mode == 'timeout':
    time.sleep(10)
if host == 'codex':
    assert sys.argv[1:] == ['app-server'], sys.argv
    init = json.loads(sys.stdin.readline())
    assert init['method'] == 'initialize'
    print(json.dumps({'id': init['id'], 'result': {}}), flush=True)
    initialized = json.loads(sys.stdin.readline())
    assert initialized == {'method': 'initialized'}
    request = json.loads(sys.stdin.readline())
    assert request['method'] == 'model/list' and request['params'] == {}
    if mode == 'slow':
        time.sleep(1)
    if mode == 'unparseable':
        print('not model JSON', flush=True)
        sys.exit(0)
    rows = [] if mode == 'empty' else json.loads((home / 'codex.rows').read_text())
    print(json.dumps({'id': request['id'], 'result': {'data': rows, 'nextCursor': None}}), flush=True)
    sys.stdin.read()
else:
    assert '-p' in sys.argv
    request = json.loads(sys.stdin.readline())
    assert request['request']['subtype'] == 'list_models'
    print((home / 'claude.response').read_text())
''')
    binary.chmod(0o755)
    (home / f"{host}.version").write_text(f"{host} 1.0")
    (home / f"{host}.mode").write_text("ok")
    (home / "codex.rows").write_text(json.dumps(CODEX_ROWS))
    (home / "claude.response").write_text(json.dumps({"type": "control_response", "response": {
        "subtype": "success", "response": {"models": [
            {"value": "opus", "supportsEffort": True, "supportedEffortLevels": ["low", "high"]}]}}}))
    return binary


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        env = {k: v for k, v in os.environ.items() if k not in
               ("MMW_HOST_CATALOG", "MMW_CATALOG_MODE", "MMW_RUNNER")}
        env.update(HOME=str(self.home), MMW_HOME=str(self.home))
        patch = mock.patch.dict(os.environ, env, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        for host in ("codex", "claude"):
            fake_host(self.home, host)

    def scan(self, host="codex", runner="orca"):
        result = models.scan_host_catalogs(runner, [host])
        self.assertTrue((self.home / f"{host}.log").exists(), f"fake {host} was not called")
        return result

    def stored(self, source="cli", host="codex"):
        path = self.home / "catalog.json"
        self.assertTrue(path.exists(), "a successful read must persist its catalog")
        return json.loads(path.read_text())[source][host]

    def test_a_codex_read_stores_models_time_and_version(self):
        self.scan()
        entry = self.stored()
        self.assertEqual(entry["offerings"], [{"id": "gpt-6-sol", "name": "GPT-6-Sol",
                         "thinkingOptionIds": ["low", "high"], "isDefault": True}])
        self.assertRegex(entry["read_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertEqual(entry["version"], "codex 1.0")
        self.assertNotIn("failure", entry)

    def test_codex_hidden_models_are_not_stored_and_debug_models_is_not_run(self):
        self.scan()
        self.assertEqual([row["id"] for row in self.stored()["offerings"]], ["gpt-6-sol"])
        calls = (self.home / "codex.log").read_text().splitlines()
        self.assertIn("app-server", calls)
        self.assertNotIn("debug models", calls)

    def test_a_claude_read_stores_models_and_version(self):
        self.scan("claude")
        entry = self.stored(host="claude")
        self.assertEqual(entry["offerings"], [{"id": "opus", "name": "opus",
                         "thinkingOptionIds": ["low", "high"], "note": ""}])
        self.assertEqual(entry["version"], "claude 1.0")
        self.assertRegex(entry["read_at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertIn("-p", (self.home / "claude.log").read_text())

    def failed_read(self, mode, kind, detail=None):
        self.scan()
        before = self.stored()
        (self.home / "codex.mode").write_text(mode)
        scan = self.scan()
        after = self.stored()
        self.assertEqual(after["offerings"], before["offerings"])
        self.assertEqual(after["read_at"], before["read_at"])
        self.assertEqual(after["version"], before["version"])
        self.assertEqual(after["failure"]["kind"], kind)
        self.assertRegex(after["failure"]["at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertEqual(scan["hosts"]["codex"]["read_at"], before["read_at"])
        if detail:
            self.assertIn(detail, after["failure"]["detail"])
        return after

    def test_a_failed_read_keeps_the_stored_models_and_records_exit(self):
        after = self.failed_read("exit", "exit", "boom")
        self.assertIn("3", after["failure"]["detail"])
        self.assertNotIn("second line", after["failure"]["detail"])
        (self.home / "codex.mode").write_text("ok")
        self.scan()
        self.assertNotIn("failure", self.stored())

    def test_a_timed_out_read_keeps_the_stored_models_and_records_timeout(self):
        with mock.patch.object(models, "CATALOG_TIMEOUT", 0.15):
            self.failed_read("timeout", "timeout", "0.15")

    def test_an_unparseable_answer_keeps_the_stored_models_and_records_unparseable(self):
        self.failed_read("unparseable", "unparseable", "not model JSON")

    def test_an_empty_answer_keeps_the_stored_models_and_records_empty(self):
        self.failed_read("empty", "empty")

    def test_a_missing_binary_is_recorded_as_missing_with_the_folders_searched(self):
        self.scan()
        before = self.stored()
        (self.home / ".local" / "bin" / "codex").unlink()
        with mock.patch.object(models, "_search_folders", return_value=[str(self.home / ".local" / "bin")]):
            self.scan()
        entry = self.stored()
        self.assertEqual(entry["offerings"], before["offerings"])
        self.assertEqual(entry["failure"]["kind"], "missing")
        self.assertIn("codex", entry["failure"]["detail"])
        self.assertIn(str(self.home / ".local" / "bin"), entry["failure"]["detail"])

    def row(self):
        config = models.default_local_config()
        config["rows"]["senior-worker"] = {"host": "codex", "model": "gpt 6 sol", "effort": "high"}
        (self.home / "models.json").write_text(json.dumps(config))
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = models.main(["row", "senior-worker"])
        self.assertTrue((self.home / "codex.log").exists())
        return code, out.getvalue(), err.getvalue()

    def test_row_with_an_unchanged_version_reads_the_stored_catalog(self):
        self.scan()
        (self.home / "codex.log").write_text("")
        self.assertEqual(self.row(), (0, "codex\tgpt-6-sol\thigh\n", ""))
        self.assertEqual((self.home / "codex.log").read_text().splitlines(), ["--version"])

    def test_row_with_a_changed_version_reads_the_host_again(self):
        self.scan()
        (self.home / "codex.version").write_text("codex 2.0")
        (self.home / "codex.log").write_text("")
        self.assertEqual(self.row(), (0, "codex\tgpt-6-sol\thigh\n", ""))
        self.assertEqual((self.home / "codex.log").read_text().splitlines(), ["--version", "app-server"])
        self.assertEqual(self.stored()["version"], "codex 2.0")

    def test_row_falls_back_to_the_stored_catalog_and_says_why(self):
        self.scan()
        before = self.stored()
        (self.home / "codex.version").write_text("codex 2.0")
        (self.home / "codex.mode").write_text("exit")
        code, out, err = self.row()
        self.assertEqual((code, out), (0, "codex\tgpt-6-sol\thigh\n"))
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn("exit", err)
        self.assertIn(before["read_at"], err)

    def test_row_with_no_catalog_and_a_failed_read_refuses_with_the_reason(self):
        (self.home / "codex.mode").write_text("exit")
        code, out, err = self.row()
        self.assertEqual((code, out), (2, ""))
        self.assertIn("exit", err)
        self.assertIn("boom", err)

    def test_check_local_config_reads_again_whatever_the_version(self):
        self.scan()
        (self.home / "codex.log").write_text("")
        config = models.default_local_config()
        config["rows"]["senior-worker"] = {"host": "codex", "model": "gpt 6 sol", "effort": "high"}
        _, scan, _ = models.check_local_config(config)
        self.assertEqual(scan["hosts"]["codex"]["offered"], [{"model": "gpt 6 sol", "efforts": ["low", "high"]}])
        self.assertIn("app-server", (self.home / "codex.log").read_text().splitlines())

    def test_a_saved_model_gone_from_the_catalog_names_the_row_the_name_and_the_choices(self):
        config = models.default_local_config()
        config["rows"]["senior-worker"] = {"host": "codex", "model": "gpt-9", "effort": "high"}
        _, _, errors = models.check_local_config(config)
        reason = next(e["reason"] for e in errors if e["cell"] == "senior-worker.model")
        self.assertIn("senior-worker", reason)
        self.assertIn("gpt-9", reason)
        self.assertIn("gpt-6-sol", reason)
        self.assertIn("app-server", (self.home / "codex.log").read_text().splitlines())

    def test_a_paseo_failure_leaves_the_cli_entry_alone(self):
        self.scan()
        cli_before = self.stored()
        paseo = self.home / ".local" / "bin" / "paseo"
        paseo.write_text(f"#!{sys.executable}\n" + '''import json, sys
from pathlib import Path
home = Path.home()
with (home / 'paseo.log').open('a') as log:
    log.write(' '.join(sys.argv[1:]) + '\\n')
if sys.argv[1:3] == ['provider', 'ls']:
    print('[{"id":"codex"}]')
else:
    if (home / 'paseo.fail').exists():
        print('paseo boom', file=sys.stderr)
        sys.exit(3)
    print('[{"id":"paseo-sol","model":"Paseo Sol","thinkingOptionIds":["high"]}]')
''')
        paseo.chmod(0o755)
        with mock.patch.dict(os.environ, {"PATH": str(paseo.parent) + os.pathsep + os.environ["PATH"]}):
            self.scan(runner="paseo")
            before = self.stored("paseo")
            self.assertEqual([r["id"] for r in before["offerings"]], ["paseo-sol"])
            (self.home / "paseo.fail").touch()
            self.scan(runner="paseo")
        after = self.stored("paseo")
        self.assertEqual(self.stored(), cli_before)
        self.assertEqual(after["offerings"], before["offerings"])
        self.assertEqual(after["read_at"], before["read_at"])
        self.assertEqual(after["failure"]["kind"], "exit")
        self.assertIn("paseo boom", after["failure"]["detail"])
        self.assertIn("provider models codex --json", (self.home / "paseo.log").read_text())
