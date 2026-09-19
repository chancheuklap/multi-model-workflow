#!/usr/bin/env python3
"""Acceptance names stay in the places a consuming repository is allowed to keep them.

    harness-guard.py <repository-root>

Reads of `MMW_` variables, and the strings `.mmw/target.json`'s `harness_markers`
lists, may appear in `.mmw/`, `tests/`, `scripts/dev/`, a test file that ships with
no release (`__tests__/`, `__mocks__/`, `*.test.*`, `*.spec.*`), and files
`leaves_machine` names. Anywhere else is a leak. `[]` is a legal answer: this
product has no back-door markers. Missing or unusable `harness_markers` is a
refusal, not a default.

Story-service files — everything under `.mmw/stories/`, and files the `stories`
command names — may reference `scenes.json` and must not reference `.dc.html`.

What is read is what the repository tracks, or would track — `git ls-files --cached
--others --exclude-standard`.

    HARNESS LEAK <file>:<line>          exit 1
    HARNESS DESIGN PAGE <file>:<line>   exit 1
    HARNESS OK                          exit 0
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refusal import refusal  # noqa: E402

READ_MMW = re.compile(
    r"os\.environ(?:\.get)?\(\s*['\"]MMW_"
    r"|os\.getenv\(\s*['\"]MMW_"
    r"|process\.env\.MMW_"
    r"|\$\{?MMW_[A-Z0-9_]+"
    r"|env\[['\"]MMW_"
)
PATH_TOKEN = re.compile(r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
}
# A test that lives beside the code it tests rather than under `tests/`. It reads the
# acceptance names for the same reason a file under `tests/` does, and no release
# carries it. Naming one in `leaves_machine` would say it reaches past this machine,
# which is not what it does, so a repository that keeps its tests this way was left
# writing `process.env["MMW_" + "NEGATIVE"]` to get past this check — an evasion that
# hides every real leak beside it.
TEST_DIRS = {"__tests__", "__mocks__"}
TEST_FILE_RE = re.compile(r".+\.(?:test|spec)\.[A-Za-z0-9]+$")
DESIGN_PAGE = ".dc.html"


def is_leak(line: str, markers: tuple[str, ...]) -> bool:
    if READ_MMW.search(line):
        return True
    return any(marker in line for marker in markers)


def load_target(root: Path) -> dict | None:
    path = root / ".mmw" / "target.json"
    if not path.is_file():
        return None
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return cfg if isinstance(cfg, dict) else None


def markers_of(cfg: dict) -> tuple[str, ...] | None:
    if "harness_markers" not in cfg:
        return None
    value = cfg["harness_markers"]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return tuple(item for item in value if item)


def refuse_markers(root: Path) -> int:
    path = root / ".mmw" / "target.json"
    print(refusal(
        f"{path} has no harness_markers.",
        "The guard does not fall back to built-in markers.",
        "Run `target_config.py --check` and answer harness_markers "
        "([] if this product has none).",
    ), file=sys.stderr)
    return 2


def load_named_files(root: Path, cfg: dict) -> set[Path]:
    """Files each `leaves_machine` entry names — the whole string, or a path in it."""
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


def files_named_in(root: Path, command: str) -> set[Path]:
    """Existing files under `root` that a command string names as a path."""
    named: set[Path] = set()
    root_r = root.resolve()
    for raw in PATH_TOKEN.findall(command):
        candidate = (root / raw).resolve()
        try:
            candidate.relative_to(root_r)
        except ValueError:
            continue
        if candidate.is_file():
            named.add(candidate)
    return named


def story_service_files(root: Path, cfg: dict, files: list[Path]) -> list[Path]:
    """Tracked files under `.mmw/stories/`, plus files the `stories` command names."""
    stories_root = (root / ".mmw" / "stories").resolve()
    named: set[Path] = set()
    command = cfg.get("stories")
    if isinstance(command, str):
        named = files_named_in(root, command)
    chosen: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        try:
            resolved.relative_to(stories_root)
            under_stories = True
        except ValueError:
            under_stories = False
        if under_stories or resolved in named:
            seen.add(resolved)
            chosen.append(path)
    return chosen


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
    if TEST_DIRS.intersection(parts[:-1]):
        return True
    return bool(TEST_FILE_RE.match(rel.name))


def tracked(root: Path) -> list[Path] | None:
    """Every file this repository tracks or could track, or None outside a repository.

    `--others --exclude-standard` adds the files that are there and not committed yet —
    the work a ticket is being judged on — and leaves out what `.gitignore` covers.
    Walking the directory instead read whatever happened to be lying there: a log the
    product wrote while the criteria ran, a scratch copy of a ticket. The same commit
    was then green or red depending on how recently anyone had run the product, which
    is what agentflow #703 and #704 hit on 2026-09-08.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--others",
             "--exclude-standard", "-z"],
            capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    found = []
    for name in out.stdout.split("\0"):
        if not name or SKIP_DIRS.intersection(Path(name).parts):
            continue
        path = root / name
        # A submodule is one entry and is not this repository's file; a path listed and
        # then removed is gone by now.
        if path.is_file():
            found.append(path)
    return found


def iter_files(root: Path):
    found = tracked(root)
    if found is not None:
        yield from found
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        here = Path(dirpath)
        for name in filenames:
            yield here / name


def scan_leaks(root: Path, files: list[Path], named: set[Path],
               markers: tuple[str, ...]) -> list[str]:
    leaks: list[str] = []
    root_r = root.resolve()
    for path in files:
        if allowed(path, root, named):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.resolve().relative_to(root_r).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            if is_leak(line, markers):
                leaks.append(f"HARNESS LEAK {rel}:{number}")
    return leaks


def scan_design_pages(root: Path, files: list[Path]) -> list[str]:
    hits: list[str] = []
    root_r = root.resolve()
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.resolve().relative_to(root_r).as_posix()
        for number, line in enumerate(text.splitlines(), 1):
            if DESIGN_PAGE in line:
                hits.append(f"HARNESS DESIGN PAGE {rel}:{number}")
                break
    return hits


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        sys.stderr.write("usage: harness-guard.py <repository-root>\n")
        return 2
    root = Path(argv[0])
    if not root.is_dir():
        print(f"no such directory: {root}", file=sys.stderr)
        return 2
    root = root.resolve()
    cfg = load_target(root)
    markers = None if cfg is None else markers_of(cfg)
    if cfg is None or markers is None:
        return refuse_markers(root)
    files = list(iter_files(root))
    leaks = scan_leaks(root, files, load_named_files(root, cfg), markers)
    pages = scan_design_pages(root, story_service_files(root, cfg, files))
    lines = leaks + pages
    if lines:
        print("\n".join(lines))
        return 1
    print("HARNESS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
