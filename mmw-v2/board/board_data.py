"""Placeholder for the board-data API owned by the board-data ticket."""

from __future__ import annotations


def handle(request) -> tuple[int, dict[str, str], bytes]:
    """Identify this API family while its real implementation is not installed."""
    return 501, {"Content-Type": "application/json"}, b'{"family":"board","error":"not implemented"}\n'
