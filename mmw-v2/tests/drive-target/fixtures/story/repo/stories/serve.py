#!/usr/bin/env python3
"""Serve the fixture story page and print origin=http://127.0.0.1:<port>.

Reads MMW_PORT_BASE from the lease. STORY_MUTATE=copy|color patches the bytes
this process serves, so the product side can be made to differ from the design.
"""
from __future__ import annotations

import http.server
import os
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = (HERE / "index.html").read_text(encoding="utf-8")
VALID_PAGES = {"demo"}
VALID_SCENES = {"alpha", "beta", "gamma"}


def body_for(mutate: str) -> str:
    html = PAGE
    if mutate == "copy":
        html = html.replace("Alpha scene copy", "Alpha scene COPY")
    elif mutate == "color":
        html = html.replace("#2f6fed", "#ff2d55")
    return html


class Handler(http.server.BaseHTTPRequestHandler):
    html = PAGE

    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path not in ("/", "/index.html"):
            self.send_error(404)
            return
        qs = urllib.parse.parse_qs(parsed.query)
        page = (qs.get("page") or [""])[0]
        scene = (qs.get("scene") or [""])[0]
        if page or scene:
            if page not in VALID_PAGES or scene not in VALID_SCENES:
                self.send_error(404)
                return
        raw = self.html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def main() -> int:
    raw = os.environ.get("MMW_PORT_BASE")
    if not raw:
        sys.stderr.write(
            "stories/serve.py has no MMW_PORT_BASE.\n"
            "story-parity.py puts the lease in the environment of this command.\n"
            "Run story-parity.py --contract … --pages … from the repository; "
            "do not start this script by hand.\n"
        )
        return 2
    try:
        port = int(raw)
    except ValueError:
        sys.stderr.write(f"MMW_PORT_BASE is not an int: {raw!r}\n")
        return 2
    Handler.html = body_for(os.environ.get("STORY_MUTATE", ""))
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        sys.stderr.write(f"could not bind 127.0.0.1:{port}: {exc}\n")
        return 2
    print(f"origin=http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
