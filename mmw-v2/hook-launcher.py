#!/usr/bin/env python3
"""Launch a host hook from the checkout recorded in installed-root."""

import os
import re
import sys
from pathlib import Path

TICKET_DIR = re.compile(r"^issue-(\d+)$")


def governed() -> bool:
    for directory in (os.getcwd(), os.environ.get("PASEO_AGENT_CWD", "").strip()):
        if directory and TICKET_DIR.fullmatch(os.path.basename(os.path.normpath(directory))):
            return True
    return False


def missing(name: str, root: str) -> int:
    if name == "mode-hook" or (name == "tool-guard" and not governed()):
        return 0
    root = root.replace("\n", " ").replace("\r", " ")
    sys.stderr.write(f"MMW hook {name} not found under {root}: "
                     "run bash mmw-v2/install.sh --check\n")
    return 2 if name == "tool-guard" else 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] not in ("tool-guard", "turn-guard", "mode-hook"):
        sys.stderr.write("usage: hook-launcher <tool-guard|turn-guard|mode-hook> <args>\n")
        return 0
    marker = Path(os.environ.get("MMW_HOME") or Path.home() / ".mmw") / "installed-root"
    try:
        root = marker.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        root = ""
    if root:
        for component in ("mmw", "dispatch"):
            target = Path(root).joinpath("skills", component, "scripts", args[0] + ".py")
            if target.is_file():
                os.execv(sys.executable, [sys.executable, str(target), *args[1:]])
    return missing(args[0], root or str(marker))


if __name__ == "__main__":
    sys.exit(main())
