"""Settings API family placeholder with an explicit not-implemented response."""

from __future__ import annotations


def handle(request) -> tuple[int, dict[str, str], bytes]:
    """Return the API family's explicit not-implemented response."""
    return 501, {"Content-Type": "application/json"}, b'{"family":"settings","error":"not implemented"}\n'
