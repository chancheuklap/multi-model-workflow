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
# relative to skills/, and the first candidate is absent until that directory exists.
_CANDIDATES = (
    ("skills", "mmw", "scripts", "locations.py"),
    ("skills", "dispatch", "scripts", "locations.py"),
)
_DISPATCH_SCRIPTS = ("ghlist.py", "models.py", "statedir.py")
_REGISTERED = ("DISPATCH_SCRIPTS", "EVENTS_PY", "ISSUE_TREE_PY")


class LocationsMissing(RuntimeError):
    """Neither candidate `locations.py` is on disk, or the one found cannot be read."""


def candidate_paths(root: Path | None = None) -> tuple[Path, Path]:
    root = ROOT if root is None else root
    return tuple(root.joinpath(*parts) for parts in _CANDIDATES)


def locations_path(root: Path | None = None) -> Path:
    found = [path for path in candidate_paths(root) if path.is_file()]
    if found:
        return found[0]
    first, second = candidate_paths(root)
    raise LocationsMissing(
        f"neither {first} nor {second} exists; the task board cannot load its scripts: "
        "run bash mmw-v2/install.sh --check"
    )


def resolved_scripts(root: Path | None = None) -> dict[str, Path]:
    """Paths of `locations.py` and the scripts the board loads through it."""
    path = locations_path(root)
    spec = importlib.util.spec_from_file_location("mmw_board_locations", path)
    if spec is None or spec.loader is None:
        raise LocationsMissing(
            f"{path} cannot be loaded; the task board cannot load its scripts: "
            "run bash mmw-v2/install.sh --check"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing = [name for name in _REGISTERED if not isinstance(getattr(module, name, None), str)]
    if missing:
        raise LocationsMissing(
            f"{path} does not register {', '.join(missing)}; the task board cannot load "
            "its scripts: run bash mmw-v2/install.sh --check"
        )
    skills = path.parents[2]
    dispatch = skills / module.DISPATCH_SCRIPTS
    resolved = {
        "locations": path,
        "events": skills / module.EVENTS_PY,
        "issue_tree": skills / module.ISSUE_TREE_PY,
        "dispatch_scripts": dispatch,
    }
    for name in _DISPATCH_SCRIPTS:
        resolved[name.removesuffix(".py")] = dispatch / name
    return resolved


def require_scripts(root: Path | None = None) -> dict[str, Path]:
    """The resolved scripts, or a refusal on stderr and exit 1 when they cannot be found."""
    try:
        return resolved_scripts(root)
    except LocationsMissing as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(1) from None


def fingerprint() -> str:
    digest = hashlib.sha256()
    resolved = resolved_scripts()
    watched = (
        *BOARD.glob("*.py"),
        resolved["locations"],
        resolved["events"],
        resolved["issue_tree"],
        resolved["ghlist"],
        resolved["models"],
        resolved["statedir"],
    )
    for path in sorted(set(watched)):
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
