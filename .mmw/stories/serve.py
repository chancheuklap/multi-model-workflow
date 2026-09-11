#!/usr/bin/env python3
"""Serve component stories on a port of their own and print their origin.

The port is whatever the machine hands out (`127.0.0.1:0`), because a story page renders
presentational components from scene data and has no backend, no seed and no route
behind it: nothing here has to be reachable at an address anyone agreed in advance, and
a port picked this way collides with no other run. Taking one from the lease instead
would spend one of the product's `instance.max` slots for the length of a ticket.
"""

from __future__ import annotations

import http.server
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PAGE = ROOT / "mmw-v2" / "board" / "page"
SCENES = ROOT / "prototypes" / "board-orchestration" / "task-board" / "UI" / "work" / "scenes.json"
ADAPTERS = HERE / "adapters"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path in ("/", "/index.html"):
            query = urllib.parse.parse_qs(parsed.query)
            page = (query.get("page") or [""])[0]
            if page and not (ADAPTERS / f"{page}.mjs").is_file():
                self.send_error(404)
                return
            return self.send_file(HERE / "index.html", "text/html; charset=utf-8")
        if path == "/story.mjs":
            return self.send_file(HERE / "story.mjs", "text/javascript; charset=utf-8")
        if path == "/scenes.json":
            return self.send_file(SCENES, "application/json")
        if path.startswith("/adapters/"):
            target = (HERE / path.removeprefix("/")).resolve()
            if target.parent == ADAPTERS.resolve():
                return self.send_file(target, "text/javascript; charset=utf-8")
        if path.startswith("/product/"):
            target = (PAGE / path.removeprefix("/product/")).resolve()
            if target.parent == PAGE.resolve():
                return self.send_file(target, "text/javascript; charset=utf-8")
        if path.startswith("/styles/"):
            target = (PAGE / path.removeprefix("/")).resolve()
            if target.parent == (PAGE / "styles").resolve():
                return self.send_file(target, "text/css; charset=utf-8")
        self.send_error(404)

    def send_file(self, path: Path, content_type: str):
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    print(f"origin=http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
