#!/usr/bin/env python3
"""A one-page fixture product with a write/read API and one route break switch."""

from __future__ import annotations

import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ["MMW_PORT_BASE"])
DATA = Path(os.environ["MMW_DATA_DIR"])
BREAK = os.environ.get("MMW_BREAK", "")


def broken(method: str, path: str) -> bool:
    if not BREAK:
        return False
    expected_method, route = BREAK.split(" ", 1)
    route_pattern = re.escape(route)
    route_pattern = re.sub(r"\\\{[^{}]+\\\}", "[^/]+", route_pattern)
    return method == expected_method and re.fullmatch(route_pattern, path) is not None


class Product(BaseHTTPRequestHandler):
    def answer(self, status: int, body: str) -> None:
        encoded = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's interface
        if broken("GET", self.path):
            self.answer(503, "broken\n")
            return
        if self.path == "/health":
            self.answer(200, "ok\n")
            return
        found = re.fullmatch(r"/result/([^/]+)", self.path)
        if found:
            result = DATA / f"result-{found.group(1)}"
            if result.is_file():
                self.answer(200, result.read_text(encoding="utf-8"))
            else:
                self.answer(404, "missing\n")
            return
        self.answer(404, "missing\n")

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's interface
        if broken("POST", self.path):
            self.answer(503, "broken\n")
            return
        found = re.fullmatch(r"/write/([^/]+)", self.path)
        if not found:
            self.answer(404, "missing\n")
            return
        length = int(self.headers.get("Content-Length", "0"))
        value = self.rfile.read(length).decode()
        (DATA / f"result-{found.group(1)}").write_text(value, encoding="utf-8")
        self.answer(200, "saved\n")

    def log_message(self, _format: str, *_args: object) -> None:
        pass


ThreadingHTTPServer(("127.0.0.1", PORT), Product).serve_forever()
