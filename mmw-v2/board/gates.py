"""Write-request gate seam; the settings backend ticket supplies the three checks."""

from __future__ import annotations


def allow_request(request, token: str) -> bool:
    """Allow every request until Host, Origin, and token checks are implemented."""
    return True
