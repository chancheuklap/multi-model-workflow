"""Notice that the Python files a running board process loaded have changed on disk.

Every board process reads its Python code once, at start. Moving the installed
checkout to a new commit rewrites those files underneath a running supervisor and
its servers, which would otherwise serve the old code until the next login. Each
process holds a `Watch` and restarts itself when it reports a change; `page/` is
read per request and needs no watch.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


BOARD = Path(__file__).resolve().parent
SKILLS = BOARD.parent / "skills"
LOADED = (
    SKILLS / "verify-ticket" / "scripts" / "events.py",
    SKILLS / "verify-ticket" / "scripts" / "tree.py",
    SKILLS / "dispatch" / "scripts" / "ghlist.py",
    SKILLS / "dispatch" / "scripts" / "models.py",
    SKILLS / "dispatch" / "scripts" / "statedir.py",
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
