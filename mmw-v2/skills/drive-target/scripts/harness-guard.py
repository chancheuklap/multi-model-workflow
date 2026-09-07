#!/usr/bin/env python3
"""Acceptance names stay in the places a consuming repository is allowed to keep them.

    harness-guard.py <repository-root>

Reads of `MMW_` variables, `/api/dev/`, `transport off`, and `__stub` may appear in
`.mmw/`, `tests/`, `scripts/dev/`, and files `leaves_machine` names. Anywhere else
is a leak.

    HARNESS LEAK <file>:<line>     exit 1
    HARNESS OK                     exit 0
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

MARKERS = ("MMW_", "/api/dev/", "transport off", "__stub")
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
}


def load_named_files(root: Path) -> set[Path]:
    path = root / ".mmw" / "target.json"
    if not path.is_file():
        return set()
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    named: set[Path] = set()
    for item in cfg.get("leaves_machine") or []:
        if not isinstance(item, str):
            continue
        candidate = (root / item).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            named.add(candidate)
    return named


def allowed(path: Path, root: Path, named: set[Path]) -> bool:
    if path.resolve() in named:
        return True
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    parts = rel.parts
    if parts[:1] == (".mmw",) or parts[:1] == ("tests",):
        return True
    if parts[:2] == ("scripts", "dev"):
        return True
    return False


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        here = Path(dirpath)
        for name in filenames:
            yield here / name


def scan(root: Path) -> list[str]:
    named = load_named_files(root)
    leaks: list[str] = []
    for path in iter_files(root):
        if allowed(path, root, named):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            if any(marker in line for marker in MARKERS):
                leaks.append(f"HARNESS LEAK {rel}:{number}")
    return leaks


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        sys.stderr.write("usage: harness-guard.py <repository-root>\n")
        return 2
    root = Path(argv[0])
    if not root.is_dir():
        print(f"no such directory: {root}", file=sys.stderr)
        return 2
    leaks = scan(root.resolve())
    if leaks:
        print("\n".join(leaks))
        return 1
    print("HARNESS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
