from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"
CATALOG = ROOT / "mmw-v2" / "tests" / "dispatch" / "catalogs" / "all.json"
sys.path.insert(0, str(SERVER.parent))
import settings_api  # noqa: E402
from board_process import RunningBoard  # noqa: E402


def config(version=1):
    return {"version": version, "runner": "orca", "rows": {
        "junior-worker": {"host": "grok", "model": "grok 4.6", "effort": "high"},
        "senior-worker": {"host": "codex", "model": "gpt 5.6 sol", "effort": "high"},
        "reviewer": {"host": "claude", "model": "opus 5", "effort": "high"},
        "verifier": {"host": "claude", "model": "sonnet 5", "effort": "high"},
        "advisor": {"host": "claude", "model": "fable 5.1", "effort": "medium"}}}


def Board(home, catalog=CATALOG, extra_env=None):
    environment = dict(extra_env or {})
    environment.update(MMW_HOME=str(home), MMW_HOST_CATALOG=str(catalog))
    return RunningBoard(environment=environment)


class SettingsApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name); (self.home / "models.json").write_text(json.dumps(config()) + "\n")

    def test_get_settings_answers_config_and_scan(self):
        catalog = self.home / "catalog.json"
        catalog.write_bytes(CATALOG.read_bytes())
        with Board(self.home, catalog) as board:
            catalog.write_text(json.dumps({"cli": {}}))
            status, raw = board.request("GET", "/api/settings")
            data = json.loads(raw)
        self.assertEqual(status, 200); self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["rows"]), 5); self.assertIn("sources", data)
        self.assertTrue(data["scan"]["scanned_at"]); self.assertEqual(data["scan"]["source"], "cli")
        self.assertEqual(data["scan"]["hosts"]["grok"]["state"], "ok")
        self.assertEqual(set(data["scan"]["hosts"]), {"cursor", "grok", "claude", "codex", "pi"})
        self.assertEqual(data["runners"], ["herdr", "orca", "paseo", "auto"])
        self.assertEqual(data["sources"], {
            "hosts": "hosts.json", "runners": "scripts/runners/*.sh"})

    def test_put_saves_with_the_read_version(self):
        proposed = config(); proposed["rows"]["reviewer"]["model"] = "sonnet 5"
        with Board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 200); self.assertEqual(json.loads(raw)["version"], 2)
        self.assertEqual(json.loads((self.home / "models.json").read_text())["rows"]["reviewer"]["model"], "sonnet 5")

    def test_put_after_a_change_elsewhere_is_409(self):
        with Board(self.home) as board:
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
        with Board(self.home) as board:
            status, raw = board.request("PUT", "/api/settings", proposed, board.write_headers)
        self.assertEqual(status, 422); self.assertEqual(json.loads(raw)["errors"][0]["cell"], "reviewer.model")
        self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_put_while_locked_is_423(self):
        scripts = ROOT / "mmw-v2" / "skills" / "dispatch" / "scripts"
        code = "import sys,time;sys.path.insert(0,sys.argv[1]);import statedir;from pathlib import Path\nwith statedir.locked(Path(sys.argv[2]),purpose='other process'): print('ready',flush=True);time.sleep(10)"
        holder = subprocess.Popen(["python3", "-c", code, str(scripts), str(self.home / "models.lock")], stdout=subprocess.PIPE, text=True)
        self.assertEqual(holder.stdout.readline().strip(), "ready")
        try:
            with Board(self.home) as board:
                status, raw = board.request("PUT", "/api/settings", config(), board.write_headers)
            self.assertEqual(status, 423)
            payload = json.loads(raw)
            self.assertEqual(payload["holder"]["pid"], holder.pid)
            self.assertIn("retry", payload["error"])
        finally:
            holder.terminate(); holder.wait(timeout=5); holder.stdout.close()

    def test_scan_answers_the_new_catalog(self):
        down = ROOT / "mmw-v2" / "tests" / "dispatch" / "catalogs" / "cli.json"
        with Board(self.home, down) as board:
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
                              "hosts": {"cursor": {"state": "ok"}}}
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


if __name__ == "__main__": unittest.main()
