#!/usr/bin/env python3
"""Report what a local design-system directory still lacks before it is uploaded.

Usage: check_design_system.py <design-system dir>

The requirements are Claude Design's own for a design system, plus the rules MMW adds;
`references/design-system.md` lists both. Every miss is one line
(`<path>: <what is missing>`). Exit 0 when nothing is missing, 1 when something is,
2 when the directory cannot be read.

What it checks:
- `styles.css` is `@import` lines only, every import resolves, the closure declares
  custom properties on `:root`, and every `@font-face` `url()` resolves;
- `readme.md` has each required heading; `SKILL.md` has `name` and `description`;
- foundation cards: at least twelve `.html` files whose first line is an `@dsCard`
  comment in a group other than Components or a UI kit's;
- every `<Name>.jsx` has `export function <Name>`, a sibling `<Name>.d.ts` that
  declares a `data-ui` prop and a sibling `<Name>.prompt.md`, and its directory holds
  one `@dsCard` file in group Components;
- each `ui_kits/<surface>/` has an `index.html` tagged `@dsCard`; `@startingPoint`
  screens are counted, not required;
- nothing Claude Design generates is written by hand (`_ds_manifest.json`,
  `_adherence.oxlintrc.json`). `_ds_bundle.js` is `build_ds_bundle.py`'s output and passes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

README_HEADINGS = ("Sources", "CONTENT FUNDAMENTALS", "VISUAL FOUNDATIONS", "ICONOGRAPHY",
                   "Index", "Intentional additions")
MIN_FOUNDATION_CARDS = 12
GENERATED = ("_ds_manifest.json", "_adherence.oxlintrc.json")
IMPORT = re.compile(r"""^@import\s+(?:url\()?["']([^"']+)["']\)?\s*;$""")
URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
FONT_FACE = re.compile(r"@font-face\s*{([^}]*)}", re.S)
ROOT_VAR = re.compile(r":root\s*{[^}]*--[\w-]+\s*:", re.S)
TAG = re.compile(r"^\s*<!--\s*@(dsCard|startingPoint)\b([^>]*)-->")
ATTR = re.compile(r'(\w+)="([^"]*)"')
COMMENT = re.compile(r"/\*.*?\*/", re.S)


def first_tag(path: Path) -> tuple[str, dict[str, str]] | None:
    try:
        line = path.read_text(encoding="utf-8").split("\n", 1)[0]
    except (OSError, UnicodeDecodeError):
        return None
    m = TAG.match(line)
    return (m.group(1), dict(ATTR.findall(m.group(2)))) if m else None


def css_closure(root: Path, misses: list[str]) -> list[Path]:
    entry = root / "styles.css"
    if not entry.is_file():
        misses.append("styles.css: missing")
        return []
    for n, raw in enumerate(COMMENT.sub("", entry.read_text(encoding="utf-8")).splitlines(), 1):
        line = raw.strip()
        if line and not IMPORT.match(line):
            misses.append(f"styles.css:{n}: not an @import line: {line[:60]}")
    seen: list[Path] = []
    pending = [entry]
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.append(path)
        text = COMMENT.sub("", path.read_text(encoding="utf-8"))
        for line in text.splitlines():
            m = IMPORT.match(line.strip())
            if not m or re.match(r"^[a-z]+:", m.group(1)):
                continue
            target = (path.parent / m.group(1)).resolve()
            if target.is_file():
                pending.append(target)
            else:
                misses.append(f"{path.relative_to(root)}: @import {m.group(1)} does not resolve")
    return seen


def check_css(root: Path, misses: list[str]) -> None:
    closure = css_closure(root, misses)
    texts = {p: COMMENT.sub("", p.read_text(encoding="utf-8")) for p in closure}
    if closure and not any(ROOT_VAR.search(t) for t in texts.values()):
        misses.append("styles.css: no custom property on :root anywhere it imports")
    for path, text in texts.items():
        for block in FONT_FACE.findall(text):
            for ref in URL.findall(block):
                if re.match(r"^[a-z]+:", ref):
                    continue
                if not (path.parent / ref).resolve().is_file():
                    misses.append(f"{path.relative_to(root)}: font file {ref} does not resolve")


def check_docs(root: Path, misses: list[str]) -> None:
    readme = root / "readme.md"
    if not readme.is_file():
        misses.append("readme.md: missing")
    else:
        headings = {h.strip().lower() for h in re.findall(r"^##\s+(.+)$", readme.read_text(encoding="utf-8"), re.M)}
        for want in README_HEADINGS:
            if want.lower() not in headings:
                misses.append(f"readme.md: no `## {want}` heading")
    skill = root / "SKILL.md"
    if not skill.is_file():
        misses.append("SKILL.md: missing")
    else:
        head = skill.read_text(encoding="utf-8").split("---")
        front = head[1] if len(head) > 2 else ""
        for key in ("name", "description"):
            if not re.search(rf"^{key}:\s*\S", front, re.M):
                misses.append(f"SKILL.md: frontmatter has no `{key}`")


def check_components(root: Path, misses: list[str]) -> int:
    count = 0
    for jsx in sorted(root.glob("components/**/*.jsx")):
        name = jsx.stem
        if not name[:1].isupper():
            continue
        count += 1
        rel = jsx.relative_to(root)
        if not re.search(rf"export\s+function\s+{name}\b", jsx.read_text(encoding="utf-8")):
            misses.append(f"{rel}: no `export function {name}`")
        dts = jsx.with_suffix(".d.ts")
        if not dts.is_file():
            misses.append(f"{rel}: no sibling {name}.d.ts")
        elif '"data-ui"' not in dts.read_text(encoding="utf-8"):
            misses.append(f"{dts.relative_to(root)}: props declare no \"data-ui\"")
        if not jsx.with_name(f"{name}.prompt.md").is_file():
            misses.append(f"{rel}: no sibling {name}.prompt.md")
    for directory in sorted({p.parent for p in root.glob("components/**/*.jsx")}):
        cards = [p for p in directory.glob("*.html")
                 if (t := first_tag(p)) and t[0] == "dsCard" and t[1].get("group") == "Components"]
        if len(cards) != 1:
            misses.append(f"{directory.relative_to(root)}: {len(cards)} @dsCard files in group Components, want 1")
    return count


def check_cards(root: Path, misses: list[str]) -> tuple[int, int]:
    kit_groups = set()
    starting = 0
    kits = [d for d in sorted((root / "ui_kits").glob("*")) if d.is_dir()]
    if not kits:
        misses.append("ui_kits/: no UI kit")
    for kit in kits:
        index = first_tag(kit / "index.html") if (kit / "index.html").is_file() else None
        if not index or index[0] != "dsCard":
            misses.append(f"{kit.relative_to(root)}/index.html: missing or not tagged @dsCard")
        else:
            kit_groups.add(index[1].get("group", ""))
        starting += sum(1 for p in kit.glob("*.html")
                        if (t := first_tag(p)) and t[0] == "startingPoint")
    foundations = 0
    for html in root.rglob("*.html"):
        tag = first_tag(html)
        if tag and tag[0] == "dsCard" and tag[1].get("group") not in ("Components", *kit_groups):
            foundations += 1
    if foundations < MIN_FOUNDATION_CARDS:
        misses.append(f"foundation cards: {foundations}, want at least {MIN_FOUNDATION_CARDS}")
    return foundations, starting


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not Path(argv[1]).is_dir():
        print("Run: check_design_system.py <design-system dir>", file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve()
    misses: list[str] = []
    for name in GENERATED:
        if (root / name).exists():
            misses.append(f"{name}: generated by Claude Design; remove it from the directory")
    check_css(root, misses)
    check_docs(root, misses)
    components = check_components(root, misses)
    foundations, starting = check_cards(root, misses)
    for line in misses:
        print(line)
    if misses:
        print(f"{len(misses)} missing")
        return 1
    print(f"design system complete: {components} components, {foundations} foundation cards, "
          f"{starting} starting points")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
