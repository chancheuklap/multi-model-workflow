"""Same-origin and per-start token gate for every board write request."""

from __future__ import annotations

import secrets


def allow_request(request, token: str) -> bool:
    """Accept a write only from this process's page at this process's address."""
    host, port = request.server.server_address[:2]
    expected_host = f"{host}:{port}"
    expected_origin = f"http://{expected_host}"
    actual_token = request.headers.get("X-MMW-Token") or ""
    return (request.headers.get("Host") == expected_host
            and request.headers.get("Origin") == expected_origin
            and secrets.compare_digest(actual_token, token))
