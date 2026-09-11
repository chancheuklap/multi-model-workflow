from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from test_settings_api import Board, config, ROOT


class GatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name); (self.home / "models.json").write_text(json.dumps(config()) + "\n")

    def test_listens_on_loopback_only(self):
        with Board(self.home) as board:
            host = urllib.request.urlparse(board.origin).hostname
            self.assertEqual(host, "127.0.0.1")

    def test_foreign_origin_is_403(self):
        before = (self.home / "models.json").read_bytes()
        with Board(self.home) as board:
            status, _ = board.request("PUT", "/api/settings", config(), {"Origin": "https://evil.example", "X-MMW-Token": board.token})
        self.assertEqual(status, 403); self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_missing_or_wrong_token_is_403(self):
        before = (self.home / "models.json").read_bytes()
        with Board(self.home) as board:
            statuses = [board.request("PUT", "/api/settings", config(), {"Origin": board.origin})[0],
                        board.request("PUT", "/api/settings", config(), {"Origin": board.origin, "X-MMW-Token": "wrong"})[0]]
        self.assertEqual(statuses, [403, 403]); self.assertEqual((self.home / "models.json").read_bytes(), before)

    def test_foreign_host_is_403(self):
        with Board(self.home) as board:
            status, _ = board.request("PUT", "/api/settings", config(), {"Host": "evil.example", "Origin": board.origin, "X-MMW-Token": board.token})
        self.assertEqual(status, 403)

    def test_refresh_and_scan_need_the_token(self):
        marker = self.home / "external-command-ran"
        fake_bin = self.home / "bin"; fake_bin.mkdir()
        for name in ("gh", "cursor-agent", "grok", "claude", "codex", "pi", "paseo"):
            script = fake_bin / name
            script.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 99\n")
            script.chmod(0o755)
        with Board(self.home, extra_env={"PATH": f"{fake_bin}:{os.environ.get('PATH', '')}"}) as board:
            a = board.request("POST", "/api/board/refresh", {})[0]
            b = board.request("POST", "/api/settings/scan", {"source": "cli"})[0]
        self.assertEqual((a, b), (403, 403))
        self.assertFalse(marker.exists())

    def test_gets_need_no_token(self):
        with Board(self.home) as board:
            a = board.request("GET", "/api/board")[0]
            b = board.request("GET", "/api/settings")[0]
        self.assertNotEqual(a, 403); self.assertNotEqual(b, 403)


if __name__ == "__main__": unittest.main()
