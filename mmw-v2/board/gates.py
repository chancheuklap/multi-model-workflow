"""Write-request gate seam for the board process skeleton."""

from __future__ import annotations


def allow_request(request, token: str) -> bool:
    """Allow every request in the process skeleton."""
    return True
