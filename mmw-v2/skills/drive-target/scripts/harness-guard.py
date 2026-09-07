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
import re
import sys
from pathlib import Path

READ_MMW = re.compile(
    r"os\.environ(?:\.get)?\(\s*['\"]MMW_"
    r"|os\.getenv\(\s*['\"]MMW_"
    r"|process\.env\.MMW_"
    r"|\$\{?MMW_[A-Z0-9_]+"
    r"|env\[['\"]MMW_"
)
MARKERS = ("/api/dev/", "transport off", "__stub")
PATH_TOKEN = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
}


def is_leak(line: str) -> bool:
    if READ_MMW.search(line):
        return True
    return any(marker in line for marker in MARKERS)


def load_named_files(root: Path) -> set[Path]:
    """Files each `leaves_machine` entry names — the whole string, or a path in it."""
    path = root / ".mmw" / "target.json"
    if not path.is_file():
        return set()
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    named: set[Path] = set()
    root_r = root.resolve()
    for item in cfg.get("leaves_machine") or []:
        if not isinstance(item, str):
            continue
        candidates = [item.strip(), *PATH_TOKEN.findall(item)]
        for raw in candidates:
            candidate = (root / raw).resolve()
            try:
                candidate.relative_to(root_r)
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
            if is_leak(line):
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
