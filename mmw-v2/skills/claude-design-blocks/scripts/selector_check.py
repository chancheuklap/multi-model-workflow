"""Report every selector the Claude Design editor cannot direct-edit.

Usage: selector_check.py <css files...>
Prints one line per selector it cannot resolve (`<file>: <selector>  <why>`) and a
count. Exit 1 when there is any, 0 when there is none.

The rule is the one `get_claude_design_prompt` states under Styling: a single class
`.a`, a two-class compound `.a.b`, a two-class descendant `.a .b` — nothing deeper,
pseudo-classes allowed. A selector past that renders fine; it is the editor that
cannot reach the element, so the page arrives in Claude Design unpolishable.

A lone element selector (`body`, `button`) is a reset nobody edits from the panel and
passes. `@keyframes` and `@font-face` bodies are skipped; other at-rules (`@media`)
are walked into.
"""
from __future__ import annotations

import pathlib
import re
import sys

# A bare element selector that only ever carries a reset.
RESET_ELEMENTS = {
    "html", "body", "button", "input", "select", "textarea", "a", "h1", "h2", "h3",
    "h4", "h5", "h6", "p", "ul", "ol", "li", "dl", "dt", "dd", "small", "strong", "b",
    "em", "i", "span", "output", "label", "svg", "img", "table", "tr", "td", "th",
    "figure", "hr", "*",
}
PSEUDO = re.compile(r"::?[a-zA-Z-]+(\([^)]*\))?")
COMBINATOR = re.compile(r"\s*[>+~]\s*|\s+")


def why(selector: str) -> str | None:
    """The reason the editor cannot resolve this selector, or None when it can."""
    base = PSEUDO.sub("", selector).strip()
    if not base:
        return None  # `:root`, `::selection` — no element to click
    if "[" in base:
        return "attribute selector"
    if "#" in base:
        return "id selector"
    parts = [p for p in COMBINATOR.split(base) if p]
    if len(parts) == 1 and parts[0] in RESET_ELEMENTS:
        return None
    if any(re.match(r"^[a-zA-Z*]", p) for p in parts):
        return "element in the selector"
    if len(parts) > 2:
        return f"{len(parts)} levels deep"
    if sum(p.count(".") for p in parts) > 2:
        return "more than two classes"
    return None


def selectors(css: str):
    """Every selector in the file, at-rule bodies walked into."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def walk(text: str):
        pos = 0
        while pos < len(text):
            brace = text.find("{", pos)
            if brace < 0:
                return
            head = text[pos:brace].strip()
            depth, j = 1, brace + 1
            while j < len(text) and depth:
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                j += 1
            body = text[brace + 1:j - 1]
            if head.startswith("@keyframes") or head.startswith("@font-face"):
                pass
            elif head.startswith("@"):
                yield from walk(body)
            else:
                for sel in head.split(","):
                    sel = sel.strip()
                    if sel:
                        yield sel
            pos = j

    return walk(css)


def main() -> int:
    files = [pathlib.Path(a) for a in sys.argv[1:]]
    if not files:
        sys.stderr.write("usage: selector_check.py <css files...>\n")
        return 2
    found = 0
    for path in files:
        try:
            css = path.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"{path}: {exc}\n")
            return 2
        for sel in selectors(css):
            reason = why(sel)
            if reason:
                found += 1
                print(f"{path}: {sel}  ({reason})")
    if found:
        print(f"{found} selectors the editor cannot reach")
        return 1
    print(f"every selector is editor-resolvable ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
