"""Fingerprint the modules a board process loads once; page files are read per request."""

from __future__ import annotations

import hashlib
from pathlib import Path


BOARD = Path(__file__).resolve().parent
TOOLS = BOARD.parent / "tools"
LOADED = (
    TOOLS / "verify-ticket" / "scripts" / "events.py",
    TOOLS / "verify-ticket" / "scripts" / "issue_tree.py",
    TOOLS / "dispatch" / "scripts" / "ghlist.py",
    TOOLS / "dispatch" / "scripts" / "models.py",
    TOOLS / "dispatch" / "scripts" / "statedir.py",
    TOOLS / "dispatch" / "scripts" / "tracker.py",
    TOOLS / "dispatch" / "roles.json",
)


def fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted({*BOARD.glob("*.py"), *LOADED}):
        digest.update(str(path).encode() + b"\0")
        try:
            digest.update(path.read_bytes())
        except OSError:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


class Watch:
    """Report a change only once two reads in a row agree, so a checkout that is
    still writing files does not restart a process onto half of the new code."""

    def __init__(self) -> None:
        self.start = fingerprint()
        self.last = self.start

    def changed(self) -> bool:
        current = fingerprint()
        settled = current == self.last
        self.last = current
        return settled and current != self.start
