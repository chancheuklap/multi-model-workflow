from __future__ import annotations

import re
import subprocess
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVER = ROOT / "mmw-v2" / "board" / "server.py"


class RunningBoard:
    def __enter__(self):
        self.process = subprocess.Popen(
            ["python3", "-u", str(SERVER), "--port", "0"], cwd=ROOT,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.origin = self.process.stdout.readline().strip()
        if not self.origin.startswith("http://127.0.0.1:"):
            raise RuntimeError(self.process.stderr.read())
        return self

    def __exit__(self, *args):
        self.process.terminate()
        self.process.wait(timeout=5)
        self.process.stdout.close()
        self.process.stderr.close()

    def get(self, path: str) -> tuple[int, str]:
        try:
            response = urllib.request.urlopen(self.origin + path, timeout=3)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, response.read().decode("utf-8")


class ServerTest(unittest.TestCase):
    def test_shell_carries_a_fresh_token(self):
        tokens = []
        for _ in range(2):
            with RunningBoard() as board:
                status, body = board.get("/")
                self.assertEqual(status, 200)
                self.assertIn("data-board-root", body)
                match = re.search(r'<meta name="mmw-page-token" content="([^"]+)">', body)
                self.assertIsNotNone(match)
                tokens.append(match.group(1))
        self.assertNotEqual(tokens[0], tokens[1])

    def test_api_prefix_reaches_its_family(self):
        with RunningBoard() as board:
            status, body = board.get("/api/board/anything")
            self.assertEqual(status, 501)
            self.assertIn('"family":"board"', body)
            status, body = board.get("/api/settings/anything")
            self.assertEqual(status, 501)
            self.assertIn('"family":"settings"', body)
            status, body = board.get("/api/other")
            self.assertEqual(status, 404)
            self.assertNotIn('"family"', body)


if __name__ == "__main__":
    unittest.main()
