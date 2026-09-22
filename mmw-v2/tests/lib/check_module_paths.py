#!/usr/bin/env python3
"""Fail when a toolbox script names a Python module file that no longer exists.

Scripts across the skills load each other by file path (`HERE / "watchdog.py"`,
`load("issue_tree")`), which no import check sees: a rename that misses one caller
leaves that caller broken until something runs it. Every suite's run.sh runs this
first, so a rename is caught by whichever suite runs next.

It reads every `.py`, `.sh` and `.mjs` file under mmw-v2/skills/ and mmw-v2/board/,
collects each quoted `<name>.py` and each `load("<name>")`, and requires a file of
that name somewhere under mmw-v2/ outside tests. Exit 0 prints nothing; exit 1
prints one line per missing name with the file and line that names it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
SCANNED = (MMW / "skills", MMW / "board")
QUOTED_PY = re.compile(r"""["']([A-Za-z0-9_.-]+\.py)["']""")
LOAD_CALL = re.compile(r"""\bload\(\s*["']([A-Za-z0-9_]+)["']""")


def existing_modules() -> set[str]:
    names = set()
    for path in MMW.rglob("*.py"):
        if "tests" in path.relative_to(MMW).parts or "__pycache__" in path.parts:
            continue
        names.add(path.name)
    return names


def missing() -> list[str]:
    known = existing_modules()
    rows = []
    for root in SCANNED:
        for path in sorted(root.rglob("*")):
            if path.suffix not in (".py", ".sh", ".mjs") or "__pycache__" in path.parts:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                names = QUOTED_PY.findall(line) + [f"{name}.py" for name in LOAD_CALL.findall(line)]
                for name in names:
                    if name not in known:
                        rows.append(f"{path.relative_to(MMW.parent)}:{number}: names {name}, which no file under mmw-v2/ has")
    return rows


def main() -> int:
    rows = missing()
    for row in rows:
        print(row)
    return 1 if rows else 0


if __name__ == "__main__":
    sys.exit(main())
