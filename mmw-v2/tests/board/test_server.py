from __future__ import annotations

import http.server
import re
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"
sys.path.insert(0, str(SERVER.parent))
import server as board_server  # noqa: E402
from board_process import RunningBoard  # noqa: E402


class FakeModule:
    def __init__(self):
        self.requests = []

    def handle(self, request):
        self.requests.append((request.command, request.path))
        return 204, {}, b""


class FakeGate:
    def __init__(self):
        self.requests = []

    def allow_request(self, request, token):
        self.requests.append((request.command, request.path, token))
        return True


class RunningHandler(RunningBoard):
    def __init__(self, handler):
        self.handler = handler

    def __enter__(self):
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.origin = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

class ServerTest(unittest.TestCase):
    def test_shell_carries_a_fresh_token(self):
        tokens = []
        for _ in range(2):
            with RunningBoard() as board:
                status, body = board.request("GET", "/")
                self.assertEqual(status, 200)
                self.assertIn("data-board-root", body)
                match = re.search(r'<meta name="mmw-page-token" content="([^"]+)">', body)
                self.assertIsNotNone(match)
                tokens.append(match.group(1))
        self.assertNotEqual(tokens[0], tokens[1])

    def test_api_prefix_reaches_its_family(self):
        board_family = FakeModule()
        settings_family = FakeModule()
        gate = FakeGate()
        handler = board_server.make_handler("test-token", board_family, settings_family, gate)
        with RunningHandler(handler) as board:
            self.assertEqual(board.request("GET", "/api/board/anything")[0], 204)
            self.assertEqual(board.request("POST", "/api/board/refresh")[0], 204)
            self.assertEqual(board.request("GET", "/api/settings/anything")[0], 204)
            self.assertEqual(board.request("PUT", "/api/settings")[0], 204)
            status, body = board.request("POST", "/api/other")
            self.assertEqual(status, 404)
        self.assertEqual(board_family.requests, [
            ("GET", "/api/board/anything"), ("POST", "/api/board/refresh")
        ])
        self.assertEqual(settings_family.requests, [
            ("GET", "/api/settings/anything"), ("PUT", "/api/settings")
        ])
        self.assertEqual(gate.requests, [
            ("POST", "/api/board/refresh", "test-token"),
            ("PUT", "/api/settings", "test-token"),
        ])


if __name__ == "__main__":
    unittest.main()
