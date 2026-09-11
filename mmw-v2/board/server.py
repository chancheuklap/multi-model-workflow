#!/usr/bin/env python3
"""Serve the local task board on 127.0.0.1 with a fresh per-start page token."""

from __future__ import annotations

import argparse
import functools
import http.server
import secrets
import sys
import urllib.parse
from pathlib import Path

import board_data
import gates
import settings_api

PAGE = Path(__file__).resolve().parent / "page"


def make_handler(token: str, board_module=board_data, settings_module=settings_api,
                 gate_module=gates):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(PAGE), **kwargs)

        def log_message(self, *args):
            pass

        def _api(self) -> bool:
            path = urllib.parse.urlsplit(self.path).path
            module = None
            if path.startswith("/api/board"):
                module = board_module
            elif path.startswith("/api/settings"):
                module = settings_module
            if module is None:
                return False
            if self.command != "GET" and not gate_module.allow_request(self, token):
                self.send_error(403)
                return True
            status, headers, body = module.handle(self)
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return True

        def do_GET(self):
            if self._api():
                return
            path = urllib.parse.urlsplit(self.path).path
            if path in ("/", "/index.html"):
                raw = (PAGE / "index.html").read_text(encoding="utf-8")
                raw = raw.replace("__MMW_PAGE_TOKEN__", token)
                body = raw.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def do_POST(self):
            if not self._api():
                self.send_error(404)

        def do_PUT(self):
            if not self._api():
                self.send_error(404)

        def do_DELETE(self):
            if not self._api():
                self.send_error(404)

        def do_PATCH(self):
            if not self._api():
                self.send_error(404)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    token = secrets.token_urlsafe(32)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(token))
    host, port = server.server_address
    print(f"http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
