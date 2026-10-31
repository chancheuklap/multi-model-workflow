from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v4" / "board" / "server.py"
CATALOG = ROOT / "mmw-v4" / "tests" / "dispatch" / "catalogs" / "all.json"
sys.path.insert(0, str(SERVER.parent))
import settings_api  # noqa: E402
from board_process import RunningBoard  # noqa: E402
sys.path.insert(0, str(ROOT / "mmw-v4" / "tests" / "dispatch"))
from test_catalog import fake_host  # noqa: E402


def config(version=1):
    return {"version": version, "runner": "orca", "rows": {
        "junior-worker": {"host": "claude", "model": "sonnet 5", "effort": "high"},
        "senior-worker": {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"},
        "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
        "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"},
        "researcher": {"host": "claude", "model": "opus 5", "effort": "high"},
        "candidate": {"host": "claude", "model": "opus 5", "effort": "high"},
        "retro-analyst": {"host": "claude", "model": "opus 5", "effort": "high"}}}


def running_board(home, catalog=CATALOG):
    return RunningBoard(environment={
        "MMW_HOME": str(home), "MMW_HOST_CATALOG": str(catalog),
    })


class SettingsApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name); (self.home / "models.json").write_text(json.dumps(config()) + "\n")

    def test_get_settings_answers_config_and_scan(self):
        catalog = self.home / "fixture-catalog.json"
        catalog.write_bytes(CATALOG.read_bytes())
        with running_board(self.home, catalog) as board:
            catalog.write_text(json.dumps({"cli": {}}))
            status, raw = board.request("GET", "/api/settings")
            data = json.loads(raw)
        self.assertEqual(status, 200); self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["rows"]), 7); self.assertIn("sources", data)
        self.assertTrue(data["scan"]["scanned_at"]); self.assertEqual(data["scan"]["source"], "cli")
        self.assertEqual(data["scan"]["hosts"]["codex"]["state"], "ok")
        self.assertEqual(set(data["scan"]["hosts"]), {"claude", "codex"})
        self.assertEqual(data["runners"], ["codex-app", "herdr", "orca", "paseo", "auto"])
        self.assertEqual(data["sources"], {
            "hosts": "hosts.json", "runners": "scripts/runners/*.sh"})

    def test_put_saves_with_the_read_version(self):
        proposed = config(); proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 200); self.assertEqual(json.loads(raw)["version"], 2)
        self.assertEqual(json.loads((self.home / "models.json").read_text())["rows"]["reviewer"]["model"], "sonnet 5")

    def test_app_settings_preserve_runner_capability_through_scan_and_save(self):
        catalog = self.home / 'fixture-app-catalog.json'
        data = json.loads(CATALOG.read_text())
        data['codex-app'] = data['cli']
        catalog.write_text(json.dumps(data))
        proposed = config()
        proposed['runner'] = 'codex-app'
        for row in proposed['rows'].values():
            row.update(host='codex', model='gpt 5.6 sol', effort='high')
        with running_board(self.home, catalog) as board:
            status, raw = board.request('POST', '/api/settings/scan',
                                        {'runner': 'codex-app'}, board.write_headers)
            self.assertEqual(status, 200, raw)
            self.assertEqual(json.loads(raw)['hosts']['claude']['state'], 'unlaunchable')
            status, raw = board.request('PUT', '/api/settings', proposed, board.write_headers)
            self.assertEqual(status, 200, raw)
            status, raw = board.request('GET', '/api/settings')
            self.assertEqual(status, 200, raw)
            saved = json.loads(raw)
            self.assertEqual(saved['runner'], 'codex-app')
            self.assertEqual(saved['scan']['source'], 'codex-app')
            self.assertEqual(saved['runner_options']['codex-app']['launch'], 'codex-app')
            self.assertEqual(saved['scan']['hosts']['claude']['state'], 'unlaunchable')
            rejected = {**proposed, 'version': 2,
                        'rows': {**proposed['rows'], 'reviewer': config()['rows']['reviewer']}}
            before = (self.home / 'models.json').read_bytes()
            status, raw = board.request('PUT', '/api/settings', rejected, board.write_headers)
            self.assertEqual(status, 422, raw)
            self.assertIn('cannot start host claude', raw)
            self.assertEqual((self.home / 'models.json').read_bytes(), before)

    def test_a_put_without_subagents_keeps_them(self):
        saved = {**config(), "subagents": {"reader": {"claude": {
            "model": "haiku", "effort": "medium"}}}}
        (self.home / "models.json").write_text(json.dumps(saved))
        proposed = config()
        proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
            self.assertEqual(status, 200, raw)
            self.assertEqual(json.loads(raw)["version"], 2)
            status, raw = board.request("GET", "/api/settings")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["subagents"]["reader"], {
            "claude": {"model": "haiku", "effort": "medium"},
            "codex": {"model": "inherit", "effort": "inherit"}})
        self.assertEqual(json.loads((self.home / "models.json").read_text())["subagents"],
                         {"reader": {"claude": {"model": "haiku", "effort": "medium"}}})

    def test_a_put_with_subagents_saves_them(self):
        proposed = {**config(), "subagents": {"reader": {"claude": {
            "model": "haiku", "effort": "medium"}}}}
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
            self.assertEqual(status, 200, raw)
            status, raw = board.request("GET", "/api/settings")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["subagents"]["reader"], {
            "claude": {"model": "haiku", "effort": "medium"},
            "codex": {"model": "inherit", "effort": "inherit"}})

    def test_a_put_with_invalid_subagents_refuses_without_writing(self):
        proposed = {**config(), "subagents": {"reader": {"claude": {
            "model": "opus[1m]", "effort": "medium"}}}}
        before = (self.home / "models.json").read_bytes()
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(raw)["errors"][0]["cell"], "subagents.reader.claude.model")
        self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_put_after_a_change_elsewhere_is_409(self):
        with running_board(self.home) as board:
            elsewhere = config(2); elsewhere["runner"] = "herdr"
            (self.home / "models.json").write_text(json.dumps(elsewhere) + "\n")
            stamp = 1_700_000_000
            os.utime(self.home / "models.json", (stamp, stamp))
            status, raw = board.request("PUT", "/api/settings", config(), board.write_headers)
        self.assertEqual(status, 409)
        self.assertEqual(json.loads(raw)["modified_at"],
                         datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertEqual(json.loads((self.home / "models.json").read_text())["runner"], "herdr")

    def test_put_invalid_cell_is_422(self):
        proposed = config(); proposed["rows"]["reviewer"]["model"] = "missing"
        before = (self.home / "models.json").read_bytes()
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 422); self.assertEqual(json.loads(raw)["errors"][0]["cell"], "reviewer.model")
        self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_put_while_locked_is_423(self):
        scripts = ROOT / "mmw-v4" / "skills" / "dispatch" / "scripts"
        code = "import sys,time;sys.path.insert(0,sys.argv[1]);import statedir;from pathlib import Path\nwith statedir.locked(Path(sys.argv[2]),purpose='other process'): print('ready',flush=True);time.sleep(10)"
        holder = subprocess.Popen(["python3", "-c", code, str(scripts), str(self.home / "models.lock")], stdout=subprocess.PIPE, text=True)
        self.assertEqual(holder.stdout.readline().strip(), "ready")
        try:
            with running_board(self.home) as board:
                status, raw = board.request("PUT", "/api/settings", config(), board.write_headers)
            self.assertEqual(status, 423)
            payload = json.loads(raw)
            self.assertEqual(payload["holder"]["pid"], holder.pid)
            self.assertIn("retry", payload["error"])
        finally:
            holder.terminate(); holder.wait(timeout=5); holder.stdout.close()

    def test_scan_answers_the_new_catalog(self):
        down = ROOT / "mmw-v4" / "tests" / "dispatch" / "catalogs" / "cli.json"
        with running_board(self.home, down) as board:
            status, raw = board.request(
                "POST", "/api/settings/scan", {"source": "paseo"}, board.write_headers,
            )
        data = json.loads(raw); self.assertEqual(status, 200); self.assertEqual(data["source"], "paseo")
        self.assertEqual({v["state"] for v in data["hosts"].values()}, {"down"})
        self.assertEqual({v["label"] for v in data["hosts"].values()}, {"Paseo 没开"})

    def test_get_observes_scanning_while_rescan_is_running(self):
        started = threading.Event()
        release = threading.Event()

        def slow_scan(source):
            started.set()
            release.wait(timeout=3)
            return {"source": source, "scanned_at": "done", "scanning": False, "hosts": {}}

        settings_api._scan = {"source": "cli", "scanned_at": "old", "scanning": False,
                              "hosts": {"codex": {"state": "ok"}}}
        with mock.patch.object(settings_api.models, "scan_host_catalogs", side_effect=slow_scan):
            worker = threading.Thread(target=settings_api._replace_scan, args=("paseo",))
            worker.start()
            self.assertTrue(started.wait(timeout=2))
            current = settings_api._cached_scan("orca")
            self.assertTrue(current["scanning"])
            self.assertEqual(current["source"], "paseo")
            release.set()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive())



CODEX_CATALOG = {"offerings": [
    {"id": "gpt-6.1-sol", "name": "GPT-6.1-Sol", "thinkingOptionIds": ["low", "medium", "high", "xhigh"]},
    {"id": "gpt-6-luna", "name": "GPT-6-Luna", "thinkingOptionIds": ["low", "medium", "high"]},
], "read_at": "2026-10-17T03:19:02Z", "version": "codex-cli 0.162.1"}
CLAUDE_CATALOG = {"offerings": [
    {"id": "sonnet", "name": "sonnet", "note": "Most efficient for simpler tasks",
     "thinkingOptionIds": ["low", "medium", "high"]},
], "read_at": "2026-10-17T03:18:59Z", "version": "2.1.0"}


class SubagentAnswerTest(unittest.TestCase):
    """GET /api/settings gives the 本机配置 sheet its subagent cells, their choices and names (#1055)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        (self.home / "models.json").write_text(json.dumps(config()) + "\n")
        (self.home / "catalog.json").write_text(json.dumps({"cli": {
            "codex": CODEX_CATALOG, "claude": CLAUDE_CATALOG}}))

    def get(self):
        with running_board(self.home) as board:
            status, raw = board.request("GET", "/api/settings")
        self.assertEqual(status, 200, raw)
        return json.loads(raw)

    def test_every_subagent_cell_is_answered_and_unset_cells_are_inherit(self):
        data = self.get()
        self.assertEqual(list(data["subagents"]), ["review-axis", "reader", "default"])
        self.assertEqual(data["subagents"]["default"], {
            "claude": {"model": "inherit", "effort": "inherit"},
            "codex": {"model": "inherit", "effort": "inherit"}})
        self.assertNotIn("subagents", json.loads((self.home / "models.json").read_text()))

    def test_the_choices_are_claudes_fixed_values_and_the_stored_codex_catalog(self):
        options = self.get()["subagent_options"]
        self.assertEqual(options["rows"], ["review-axis", "reader", "default"])
        self.assertEqual(options["claude"], {"models": ["sonnet", "opus", "haiku", "fable"],
                                             "efforts": ["low", "medium", "high", "xhigh", "max"]})
        self.assertEqual(options["codex"], {
            "models": [{"model": "gpt-6.1-sol", "efforts": ["low", "medium", "high", "xhigh"]},
                       {"model": "gpt-6-luna", "efforts": ["low", "medium", "high"]}],
            "inherit_efforts": ["low", "medium", "high"]})

    def test_each_model_id_is_named_as_the_agent_rows_name_it(self):
        labels = self.get()["subagent_options"]["labels"]
        self.assertEqual(labels["codex"], {"gpt-6.1-sol": "gpt 6.1 sol", "gpt-6-luna": "gpt 6 luna"})
        self.assertEqual(labels["claude"]["sonnet"], "sonnet · Most efficient for simpler tasks")
        self.assertEqual(labels["claude"]["opus"], "opus")

    def test_a_subagent_codex_cell_is_saved_as_the_catalog_id(self):
        proposed = {**config(), "subagents": {"reader": {"codex": {"model": "gpt-6-luna", "effort": "high"}}}}
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
            self.assertEqual(status, 200, raw)
            status, raw = board.request("GET", "/api/settings")
        self.assertEqual(json.loads((self.home / "models.json").read_text())["subagents"],
                         {"reader": {"codex": {"model": "gpt-6-luna", "effort": "high"}}})
        self.assertEqual(json.loads(raw)["subagents"]["reader"]["codex"], {"model": "gpt-6-luna", "effort": "high"})

    def test_a_codex_name_in_place_of_its_id_is_refused_on_its_cell(self):
        proposed = {**config(), "subagents": {"reader": {"codex": {"model": "gpt 6 luna", "effort": "high"}}}}
        with running_board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(raw)["errors"][0]["cell"], "subagents.reader.codex.model")

    def test_a_saved_subagent_model_the_catalog_lacks_is_stale_and_named(self):
        saved = {**config(), "subagents": {"review-axis": {"codex": {"model": "gpt-5.5-sol", "effort": "high"}}}}
        (self.home / "models.json").write_text(json.dumps(saved))
        data = self.get()
        self.assertIn({"cell": "subagents.review-axis.codex.model", "host": "codex", "stored": "gpt-5.5-sol",
                       "offered": ["gpt-6.1-sol", "gpt-6-luna"]}, data["stale"])
        self.assertEqual(data["subagent_options"]["labels"]["codex"]["gpt-5.5-sol"], "gpt 5.5 sol")

    def test_an_agent_row_model_the_scan_lacks_is_stale(self):
        saved = config(); saved["rows"]["reviewer"]["model"] = "opus 3"
        (self.home / "models.json").write_text(json.dumps(saved))
        stale = {item["cell"]: item for item in self.get()["stale"]}
        self.assertEqual((stale["rows.reviewer.model"]["host"], stale["rows.reviewer.model"]["stored"]),
                         ("claude", "opus 3"))
        self.assertIn("opus 5", stale["rows.reviewer.model"]["offered"])
        self.assertNotIn("rows.candidate.model", stale)

    def test_a_test_catalog_entry_carries_its_read_time_and_failure(self):
        catalog = self.home / "fixture.json"
        catalog.write_text(json.dumps({"cli": {"codex": {
            "offerings": CODEX_CATALOG["offerings"], "read_at": "2026-10-17T03:19:02Z",
            "failure": {"kind": "timeout", "detail": "30 s", "at": "2026-10-17T09:05:11Z"}}}}))
        with running_board(self.home, catalog) as board:
            status, raw = board.request("GET", "/api/settings")
        codex = json.loads(raw)["scan"]["hosts"]["codex"]
        self.assertEqual(codex["read_at"], "2026-10-17T03:19:02Z")
        self.assertEqual(codex["failure"]["kind"], "timeout")


class StoredCatalogApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        (self.home / "models.json").write_text(json.dumps(config()))
        for host in ("claude", "codex"):
            fake_host(self.home, host)
        self.seed = {"offerings": [{"id": "stored-sol", "name": "Stored Sol",
                                  "thinkingOptionIds": ["high"], "isDefault": True}],
                     "read_at": "2026-10-14T00:00:00Z", "version": "codex old"}
        (self.home / "catalog.json").write_text(json.dumps({"cli": {"codex": self.seed}}))

    def board(self):
        return RunningBoard(environment={"HOME": str(self.home), "MMW_HOME": str(self.home),
                                         "MMW_HOST_CATALOG": ""})

    def test_the_first_get_answers_the_stored_catalog(self):
        (self.home / "codex.mode").write_text("slow")
        with self.board() as board:
            status, raw = board.request("GET", "/api/settings")
            host = json.loads(raw)["scan"]["hosts"]["codex"]
            self.wait_for(lambda: self.calls() >= 1)
            self.wait_for(self.finished)
        self.assertEqual(status, 200)
        self.assertEqual(host["offered"], [{"model": "stored sol", "efforts": ["high"]}])
        self.assertEqual(host["read_at"], "2026-10-14T00:00:00Z")
        self.assertIn("app-server", (self.home / "codex.log").read_text())

    def calls(self):
        path = self.home / "codex.log"
        return path.read_text().splitlines().count("app-server") if path.exists() else 0

    def wait_for(self, predicate):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.02)
        self.fail("background catalog read did not reach the expected state")

    def finished(self):
        return json.loads((self.home / "catalog.json").read_text())["cli"]["codex"]["version"] == "codex 1.0"

    def test_a_failed_rescan_keeps_the_stored_catalog_and_says_why(self):
        with self.board() as board:
            self.wait_for(self.finished)
            before = json.loads((self.home / "catalog.json").read_text())["cli"]["codex"]
            count = self.calls()
            (self.home / "codex.mode").write_text("exit")
            status, raw = board.request("POST", "/api/settings/scan", {"source": "cli"}, board.write_headers)
            host = json.loads(raw)["hosts"]["codex"]
            self.assertEqual(self.calls(), count + 1)
        self.assertEqual(status, 200)
        self.assertEqual(host["offered"], [{"model": "gpt 6 sol", "efforts": ["low", "high"]}])
        self.assertEqual(host["read_at"], before["read_at"])
        self.assertEqual(host["failure"]["kind"], "exit")
        self.assertIn("boom", host["failure"]["detail"])

    def test_each_get_starts_one_background_read_at_a_time(self):
        with self.board() as board:
            self.wait_for(self.finished)
            status, _ = board.request("POST", "/api/settings/scan", {"source": "cli"}, board.write_headers)
            self.assertEqual(status, 200)
            (self.home / "codex.mode").write_text("slow")
            before = self.calls()
            read_at = json.loads((self.home / "catalog.json").read_text())["cli"]["codex"]["read_at"]
            status, raw = board.request("GET", "/api/settings")
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(raw)["scan"]["scanning"])
            self.wait_for(lambda: self.calls() == before + 1)
            second_status, raw = board.request("GET", "/api/settings")
            self.assertEqual(second_status, 200)
            self.assertFalse(json.loads(raw)["scan"]["scanning"])
            self.wait_for(lambda: json.loads((self.home / "catalog.json").read_text())["cli"]["codex"]["read_at"] != read_at)
            self.assertEqual(self.calls(), before + 1)

    def test_the_first_save_waits_for_the_initial_read_without_starting_another(self):
        saved = config()
        for row in saved["rows"].values():
            row.update(host="codex", model="gpt 6 sol", effort="high")
        (self.home / "models.json").write_text(json.dumps(saved))
        (self.home / "catalog.json").unlink()
        (self.home / "codex.mode").write_text("slow")
        with self.board() as board:
            self.wait_for(lambda: self.calls() == 1)
            status, raw = board.request("PUT", "/api/settings", saved, board.write_headers)
            self.assertEqual(status, 200, raw)
            self.assertEqual(json.loads(raw)["version"], 2)
            self.assertEqual(self.calls(), 1)



if __name__ == "__main__": unittest.main()
