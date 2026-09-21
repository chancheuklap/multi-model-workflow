#!/usr/bin/env python3
"""Run the real board with one journey-only API break armed when requested."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / "mmw-v2" / "board"
if str(BOARD) not in sys.path:
    sys.path.insert(0, str(BOARD))

import server  # noqa: E402


def route_pattern(pattern: str) -> re.Pattern[str]:
    parts = re.split(r"(\{[^/{}]+\})", pattern)
    expression = "".join("[^/]+" if part.startswith("{") else re.escape(part)
                         for part in parts)
    return re.compile(f"^{expression}$")


def arm(module, method: str, route: str) -> None:
    original = module.handle
    pattern = route_pattern(route)

    def handle(request):
        path = urllib.parse.urlsplit(request.path).path
        if request.command == method and pattern.fullmatch(path):
            body = json.dumps({"error": f"interface broken by MMW_BREAK: {method} {route}"})
            return 503, {"Content-Type": "application/json; charset=utf-8"}, body.encode()
        return original(request)

    module.handle = handle


def main() -> int:
    value = os.environ.get("MMW_BREAK", "").strip()
    if value:
        method, route = value.split(maxsplit=1)
        arm(server.board_data, method, route)
        arm(server.settings_api, method, route)
    return server.main()


if __name__ == "__main__":
    sys.exit(main())
