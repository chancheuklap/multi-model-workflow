#!/usr/bin/env python3
"""Run the real task board page against a frozen payload, with the prototype variants
mounted on the detail column.

    python3 prototypes/board-orchestration/sidebar-events/UI/serve.py

Serves `mmw-v2/board/page/` as it is, this directory under `/proto/`, and `/api/board`
from `fixture.json` beside this file. The fixture is one answer of a live board, fetched
once from 127.0.0.1:<--board-port> and kept out of git; the frozen payload is the point,
since three variants can only be compared against the same events.
"""

from __future__ import annotations

import argparse
import http.server
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE.parents[3] / "mmw-v2" / "board" / "page"
FIXTURE = HERE / "fixture.json"


def fetch_fixture(port: int) -> None:
    url = f"http://127.0.0.1:{port}/api/board"
    print(f"reading one board answer from {url}", flush=True)
    with urllib.request.urlopen(url, timeout=120) as answer:
        payload = json.loads(answer.read().decode("utf-8"))
    if not payload.get("tasks"):
        raise SystemExit(f"{url} answered with no tasks; start that repository's board first")
    FIXTURE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {FIXTURE.name}: {len(payload['tasks'])} task(s) of {payload.get('repo')}", flush=True)


def make_handler(body: bytes):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(PAGE), **kwargs)

        def log_message(self, *args):
            pass

        def _send(self, status, content_type, payload):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def translate_path(self, path):
            split = urllib.parse.urlsplit(path).path
            if split.startswith("/proto/"):
                return str(HERE / split[len("/proto/"):])
            return super().translate_path(path)

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            if path == "/api/board":
                self._send(200, "application/json; charset=utf-8", body)
                return
            if path in ("/", "/index.html"):
                raw = (PAGE / "index.html").read_text(encoding="utf-8")
                raw = raw.replace("__MMW_PAGE_TOKEN__", "prototype")
                self._send(200, "text/html; charset=utf-8", raw.encode("utf-8"))
                return
            super().do_GET()

        def do_POST(self):
            if urllib.parse.urlsplit(self.path).path == "/api/board/refresh":
                self._send(200, "application/json; charset=utf-8", body)
                return
            self.send_error(404)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=47190)
    parser.add_argument("--board-port", type=int, default=47101,
                        help="the live board the fixture is read from, once")
    parser.add_argument("--refetch", action="store_true", help="read the fixture again")
    parser.add_argument("--sel", type=int, default=729, help="the ticket the link opens on")
    args = parser.parse_args(argv)

    if args.refetch or not FIXTURE.exists():
        try:
            fetch_fixture(args.board_port)
        except (urllib.error.URLError, TimeoutError) as failure:
            raise SystemExit(f"no board answered on 127.0.0.1:{args.board_port} ({failure}); "
                             f"start it with `dispatch.sh board` in that repository") from failure

    body = FIXTURE.read_bytes()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(body))
    base = f"http://127.0.0.1:{args.port}/?sel={args.sel}&variant="
    print(f"A · {base}A\nB · {base}B\nC · {base}C\n(← → switch variants)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
