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


def missing(name: str, fact: str) -> int:
    if name == "mode-hook" or (name == "tool-guard" and not governed()):
        return 0
    fact = fact.replace("\n", " ").replace("\r", " ")
    if name == "tool-guard":
        next_step = ("a governed session cannot run commands without an available tool guard; "
                     "do not retry, end this turn; the orchestrator must check the installation "
                     "from a session outside ticket worktrees with bash mmw-v2/install.sh --check")
    else:
        next_step = "run bash mmw-v2/install.sh --check"
    sys.stderr.write(f"MMW hook {name} {fact}: {next_step}\n")
    return 2 if name == "tool-guard" else 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] not in ("tool-guard", "turn-guard", "mode-hook"):
        sys.stderr.write("usage: hook-launcher <tool-guard|turn-guard|mode-hook> <args>\n")
        return 0
    marker = Path(os.environ.get("MMW_HOME") or Path.home() / ".mmw") / "installed-root"
    try:
        root = marker.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return missing(args[0], f"installed-root marker {marker} is missing")
    except (OSError, UnicodeError):
        return missing(args[0], f"installed-root marker {marker} is unreadable")
    if not root:
        return missing(args[0], f"installed-root marker {marker} is empty")
    for component in ("mmw", "dispatch"):
        target = Path(root).joinpath("skills", component, "scripts", args[0] + ".py")
        if target.is_file():
            os.execv(sys.executable, [sys.executable, str(target), *args[1:]])
    return missing(args[0], f"not found under {root}")


if __name__ == "__main__":
    sys.exit(main())
