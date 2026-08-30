"""Shared text helper. Called from two places in `fixture_app.queue`."""

from __future__ import annotations

import re
import unicodedata

_SEPARATORS = re.compile(r"[\s_/.]+")
_DROP = re.compile(r"[^a-z0-9-]")
_DASHES = re.compile(r"-{2,}")


def slugify(text: str) -> str:
    """Turn a display name into a lowercase ASCII slug.

    Non-ASCII characters that have no ASCII form (Chinese, for one) are dropped, so a
    name written only in those characters slugifies to the empty string.
    """
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    dashed = _SEPARATORS.sub("-", folded.strip().lower())
    return _DASHES.sub("-", _DROP.sub("", dashed)).strip("-")
