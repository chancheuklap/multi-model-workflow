from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path

from board_process import RunningBoard
from test_board_data import FAKE_BIN
from test_settings_api import config, ROOT, CATALOG
from test_server import RunningHandler

sys.path.insert(0, str(ROOT / "mmw-v2" / "board"))
import gates  # noqa: E402
import server as board_server  # noqa: E402


class TouchModule:
    def __init__(self, marker):
        self.marker = marker

    def handle(self, request):
        self.marker.touch()
        return 204, {}, b""


def running_board(home):
    """A board whose GitHub is the fixture `gh` with nothing on it: these tests judge the
    gates, so no request may depend on the real tracker or its speed."""
    path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
    return RunningBoard(environment={"MMW_HOME": str(home), "MMW_HOST_CATALOG": str(CATALOG), "PATH": path},
                        fixture={"maps": [], "specs": [], "trees": [], "comments": {}})


class GatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name); (self.home / "models.json").write_text(json.dumps(config()) + "\n")

    def test_listens_on_loopback_only(self):
        with running_board(self.home) as board:
            parsed = urllib.parse.urlparse(board.origin)
            host = parsed.hostname
            self.assertEqual(host, "127.0.0.1")
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                probe.connect(("192.0.2.1", 9))
                non_loopback = probe.getsockname()[0]
            finally:
                probe.close()
            self.assertNotEqual(non_loopback, "127.0.0.1")
            with self.assertRaises(OSError):
                socket.create_connection((non_loopback, parsed.port), timeout=0.2)

    def test_foreign_origin_is_403(self):
        before = (self.home / "models.json").read_bytes()
        with running_board(self.home) as board:
            status, _ = board.request("PUT", "/api/settings", config(), {"Origin": "https://evil.example", "X-MMW-Token": board.token})
        self.assertEqual(status, 403); self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_missing_or_wrong_token_is_403(self):
        before = (self.home / "models.json").read_bytes()
        with running_board(self.home) as board:
            statuses = [board.request("PUT", "/api/settings", config(), {"Origin": board.origin})[0],
                        board.request("PUT", "/api/settings", config(), {"Origin": board.origin, "X-MMW-Token": "wrong"})[0]]
        self.assertEqual(statuses, [403, 403]); self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_foreign_host_is_403(self):
        with running_board(self.home) as board:
            status, _ = board.request("PUT", "/api/settings", config(), {"Host": "evil.example", "Origin": board.origin, "X-MMW-Token": board.token})
        self.assertEqual(status, 403)

    def test_refresh_and_scan_need_the_token(self):
        board_marker = self.home / "board-handler-ran"
        settings_marker = self.home / "settings-handler-ran"
        handler = board_server.make_handler(
            "test-token", TouchModule(board_marker), TouchModule(settings_marker), gates)

        with RunningHandler(handler) as board:
            self.assertEqual(board.request("POST", "/api/board/refresh", {}, {})[0], 403)
            self.assertEqual(board.request("POST", "/api/settings/scan", {}, {})[0], 403)
            self.assertFalse(board_marker.exists())
            self.assertFalse(settings_marker.exists())
            headers = {"Origin": board.origin, "X-MMW-Token": "test-token"}
            self.assertEqual(board.request("POST", "/api/board/refresh", {}, headers)[0], 204)
            self.assertEqual(board.request("POST", "/api/settings/scan", {}, headers)[0], 204)
        self.assertTrue(board_marker.exists())
        self.assertTrue(settings_marker.exists())

    def test_gets_need_no_token(self):
        with running_board(self.home) as board:
            a = board.request("GET", "/api/board")[0]
            b = board.request("GET", "/api/settings")[0]
        self.assertNotEqual(a, 403); self.assertNotEqual(b, 403)


if __name__ == "__main__": unittest.main()
