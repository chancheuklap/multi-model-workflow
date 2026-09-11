"""Placeholder for the local-settings API owned by the settings backend ticket."""

from __future__ import annotations


def handle(request) -> tuple[int, dict[str, str], bytes]:
    """Identify this API family while its real implementation is not installed."""
    return 501, {"Content-Type": "application/json"}, b'{"family":"settings","error":"not implemented"}\n'
