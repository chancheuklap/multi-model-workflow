#!/usr/bin/env python3
"""Report dead words: every `_Avoid_` item of the nearest CONTEXT.md found in a file.

Two ways to run it:

  python3 vocab-lint.py [--context CONTEXT.md] PATH...
      Lints the files (a directory means every tracked text file under it; no PATH
      means the whole repository the current directory is in). Prints one line per
      hit, `path:line: <dead word> -> <term>`, and exits 1 when there is any.

  a Claude Code PostToolUse hook on Write|Edit (stdin is the host's JSON)
      Lints the file the tool just wrote and returns the hits as
      `hookSpecificOutput.additionalContext`. Always exits 0: it adds a note, it
      never breaks a call.

What counts as a dead word: an item on an `_Avoid_:` line of CONTEXT.md, except an
item followed by a note in parentheses — that one is guidance for the writer and
not a pattern. An ASCII item matches as a whole word — case-insensitively
unless the item itself has an upper-case letter, and never as part of an identifier
(`$seat`, `seat=`, `{seat}`); an item with CJK characters matches as a substring. Only prose is searched: in a script, comment lines and docstrings;
fenced code, inline code, text inside 「」, and `_Avoid_:` lines never, and neither are `docs/adr/`, the reference and report directories under
`docs/research/` (only `docs/research/code-landing/` is linted),
`archive/`, `deprecated/`, `prototypes/`, any `tests/` directory, the subtrees under
`mmw-v2/upstream*`, `mmw-v2/skills/exe-release/` (its vocabulary is its own), and
`scripts/gate-check/`.

The CONTEXT.md used is the nearest one walking up from the file being linted (or
the one `--context` names), so a consuming repository with its own CONTEXT.md is
linted against that.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".py", ".sh", ".txt", ".html", ".toml", ".yaml", ".yml", ".mjs", ".js", ".json"}
CODE_SUFFIXES = {".py", ".sh", ".mjs", ".js", ".toml", ".yaml", ".yml", ".json"}
SKIP_DIRS = ("docs/adr", "docs/research/code-landing-refs", "docs/research/mmw-artifact-wiring",
             "docs/research/cloud-agent-landing-orchestration", "docs/research/cursor-pi-cli",
             "archive", "deprecated", "prototypes", "tests",
             "mmw-v2/upstream", "mmw-v2/upstream-diagram-design", "mmw-v2/skills/exe-release",
             "scripts/gate-check")
CJK = re.compile(r"[　-鿿＀-￯]")
FENCE = re.compile(r"^(```|~~~)")
INLINE_CODE = re.compile(r"`[^`\n]*`")
CN_QUOTE = re.compile(r"「[^」\n]*」")
NOTE = re.compile(r"\s*[（(][^）)]*[）)]\s*$")


def find_context(start: Path):
    d = start if start.is_dir() else start.parent
    d = d.resolve()
    while True:
        c = d / "CONTEXT.md"
        if c.is_file():
            return c
        if d.parent == d:
            return None
        d = d.parent


def load_avoid(context_path: Path):
    """[(pattern, term)] from the `_Avoid_:` lines, in file order."""
    items = []
    term = None
    for line in context_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\*\*(.+?)\*\*:\s*$", line)
        if m:
            term = m.group(1)
            continue
        if line.startswith("_Avoid_:") and term:
            for raw in line[len("_Avoid_:"):].split(","):
                raw = raw.strip()
                if not raw or NOTE.search(raw):
                    continue
                items.append((raw, term))
    return items


def compile_pattern(word: str):
    if CJK.search(word):
        return re.compile(re.escape(word))
    flags = 0 if any(c.isupper() for c in word) else re.IGNORECASE
    return re.compile(r"(?<![A-Za-z0-9_\-$\{.])" + re.escape(word) + r"(?![A-Za-z0-9_\-=(\[\}'])", flags)


def searchable_lines(text: str, code: bool = False):
    """(lineno, text) for every line that is prose: outside fenced code, with inline code and
    「」 blanked; in a code file only comment lines and docstring lines."""
    out = []
    fenced = False
    docstring = False
    for i, line in enumerate(text.splitlines(), 1):
        if code:
            stripped = line.strip()
            quotes = stripped.count('"""') + stripped.count("\'\'\'")
            if docstring:
                if quotes % 2 == 1:
                    docstring = False
            elif quotes % 2 == 1:
                docstring = True
            elif quotes == 0 and not stripped.startswith(("#", "//")):
                continue
        else:
            if FENCE.match(line.strip()):
                fenced = not fenced
                continue
            if fenced or line.startswith("_Avoid_:"):
                continue
        cleaned = CN_QUOTE.sub(lambda m: " " * len(m.group(0)), INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line))
        out.append((i, cleaned))
    return out


def lint_text(text: str, avoid, code: bool = False):
    patterns = [(compile_pattern(w), w, t) for w, t in avoid]
    hits = []
    for lineno, line in searchable_lines(text, code):
        for rx, word, term in patterns:
            if rx.search(line):
                hits.append((lineno, word, term))
    return hits


def git_root(path: Path):
    try:
        out = subprocess.run(["git", "-C", str(path.parent if path.is_file() else path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def skipped(path: Path, root: Path):
    root = git_root(path) or root
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    parts = rel.split("/")
    return any(rel == d or rel.startswith(d + "/") or ("/" + d + "/") in ("/" + rel) for d in SKIP_DIRS) \
        or "tests" in parts[:-1]


def lint_file(path: Path, context_path=None):
    context = context_path or find_context(path)
    if context is None or path.suffix not in TEXT_SUFFIXES or not path.is_file():
        return []
    if skipped(path, context.parent):
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    return lint_text(text, load_avoid(context), code=path.suffix in CODE_SUFFIXES)


def repo_files(root: Path):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout
        return [root / p for p in out.decode("utf-8").split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [p for p in root.rglob("*") if p.is_file()]


def expand(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            yield from (f for f in repo_files(p) if f.is_file())
        else:
            yield p


def cli(argv):
    context_path = None
    if "--context" in argv:
        i = argv.index("--context")
        context_path = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    paths = list(expand(argv)) if argv else list(expand([Path.cwd()]))
    total = 0
    for path in paths:
        for lineno, word, term in lint_file(path, context_path):
            print(f"{path}:{lineno}: {word} -> {term}")
            total += 1
    return 1 if total else 0


def hook(data):
    inp = data.get("tool_input") or {}
    target = inp.get("file_path") or inp.get("notebook_path")
    if not target:
        return None
    hits = lint_file(Path(target))
    if not hits:
        return None
    lines = [f"vocab-lint: {len(hits)} dead word(s) in {target} (the `_Avoid_` lines of CONTEXT.md):"]
    lines += [f"  line {n}: {w} -> {t}" for n, w, t in hits[:20]]
    if len(hits) > 20:
        lines.append(f"  … and {len(hits) - 20} more")
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(lines)}}


def main():
    argv = sys.argv[1:]
    if argv or sys.stdin.isatty():
        sys.exit(cli(argv))
    try:
        data = json.load(sys.stdin)
        out = hook(data) if isinstance(data, dict) else None
        if out:
            print(json.dumps(out, ensure_ascii=False))
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
