"""Notice that the Python files a running board process loaded have changed on disk.

Every board process reads its Python code once, at start. Moving the installed
checkout to a new commit rewrites those files underneath a running supervisor and
its servers, which would otherwise serve the old code until the next login. Each
process holds a `Watch` and restarts itself when it reports a change; `page/` is
read per request and needs no watch.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path


BOARD = Path(__file__).resolve().parent
ROOT = BOARD.parent
# locations.py lives at skills/<component>/scripts/. The strings it registers are
# relative to skills/.
_LOCATIONS = ("skills", "mmw", "scripts", "locations.py")
_MODE_SCRIPTS = ("ghlist.py", "models.py", "statedir.py")
_REGISTERED = ("MODE_SCRIPTS", "EVENTS_PY", "ISSUE_TREE_PY")


class LocationsMissing(RuntimeError):
    """The registered `locations.py` is absent or cannot be loaded."""


def locations_path() -> Path:
    path = ROOT.joinpath(*_LOCATIONS)
    if path.is_file():
        return path
    raise LocationsMissing(
        f"{path} does not exist; the task board cannot load its scripts: "
        "run bash mmw-v2/install.sh --check"
    )


def resolved_scripts() -> dict[str, Path]:
    """Paths of `locations.py` and the scripts the board loads through it."""
    path = locations_path()
    spec = importlib.util.spec_from_file_location("mmw_board_locations", path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise LocationsMissing(
            f"{path} cannot be loaded ({exc}); the task board cannot load its scripts: "
            "run bash mmw-v2/install.sh --check"
        ) from None
    missing = [name for name in _REGISTERED if not isinstance(getattr(module, name, None), str)]
    if missing:
        raise LocationsMissing(
            f"{path} does not register {', '.join(missing)}; the task board cannot load "
            "its scripts: run bash mmw-v2/install.sh --check"
        )
    skills = path.parents[2]
    mode_scripts = skills / module.MODE_SCRIPTS
    resolved = {
        "locations": path,
        "events": skills / module.EVENTS_PY,
        "issue_tree": skills / module.ISSUE_TREE_PY,
        "mode_scripts": mode_scripts,
    }
    for name in _MODE_SCRIPTS:
        resolved[name.removesuffix(".py")] = mode_scripts / name
    return resolved


def require_scripts() -> dict[str, Path]:
    """The resolved scripts, or a refusal on stderr and exit 1 when they cannot be loaded."""
    try:
        return resolved_scripts()
    except LocationsMissing as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from None


def _hash_path(digest, path: Path) -> None:
    digest.update(str(path).encode() + b"\0")
    try:
        digest.update(path.read_bytes())
    except OSError:
        digest.update(b"<missing>")
    digest.update(b"\0")


def fingerprint() -> str:
    digest = hashlib.sha256()
    try:
        resolved = resolved_scripts()
    except LocationsMissing:
        # Registry bytes, so two reads agree only once the file has settled.
        digest.update(b"<locations-missing>\0")
        _hash_path(digest, ROOT.joinpath(*_LOCATIONS))
        watched = list(BOARD.glob("*.py"))
    else:
        watched = [
            *BOARD.glob("*.py"),
            *(path for path in resolved.values() if path.suffix == ".py"),
        ]
    for path in sorted(set(watched)):
        _hash_path(digest, path)
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
