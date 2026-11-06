#!/usr/bin/env python3
"""Serve the shared board UI with cloud-native data and user model settings."""
from __future__ import annotations
import argparse
import http.server
import json
from pathlib import Path
import secrets
import subprocess
import sys
import urllib.parse
import board_data
import gates
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/dispatch/scripts'))
import models
PAGE = Path(__file__).resolve().parent / 'page'


def handler(token):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(PAGE), **kwargs)

        def send_json(self, status, value):
            self.respond(status, {'Content-Type': 'application/json; charset=utf-8'}, (json.dumps(value, ensure_ascii=False) + '\n').encode())

        def respond(self, status, headers, body):
            self.send_response(status)
            for name, value in headers.items(): self.send_header(name, value)
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)

        def api(self):
            path = urllib.parse.urlsplit(self.path).path
            if not path.startswith('/api/'): return False
            if self.command != 'GET' and not gates.allow_request(self, token):
                self.send_error(403); return True
            try:
                if (self.command, path) in (('GET', '/api/board'), ('POST', '/api/board/refresh')):
                    self.respond(*board_data.handle(self))
                elif self.command == 'GET' and path == '/api/settings':
                    self.send_json(200, {**models.read_config(), 'store': str(models.config_path()), 'host': models.native_host()})
                elif self.command == 'PUT' and path == '/api/settings':
                    data = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
                    models.write_config(data); self.send_json(200, {'saved': True})
                else: self.send_json(404, {'error': 'unknown operation'})
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                self.send_json(400, {'error': str(exc)})
            return True

        def do_GET(self):
            if self.api(): return
            if urllib.parse.urlsplit(self.path).path in ('/', '/index.html'):
                self.respond(200, {'Content-Type': 'text/html; charset=utf-8'},
                             (PAGE / 'index.html').read_text().replace('__MMW_PAGE_TOKEN__', token).encode())
            else: super().do_GET()

        def do_PUT(self):
            if not self.api(): self.send_error(404)
        def do_POST(self):
            if not self.api(): self.send_error(404)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=47100)
    parser.add_argument('--host', choices=('cursor', 'codex'), required=True)
    args = parser.parse_args()
    models.HOST = args.host
    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler(secrets.token_urlsafe(32)))
    print(f'http://127.0.0.1:{server.server_port}', flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__':
    main()
