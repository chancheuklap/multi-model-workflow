#!/usr/bin/env python3
"""Bundle the production board's page logic into one classic script for the design pages.

    python3 bundle_logic.py <out.js>

The Claude Design pages cannot import ES modules, so the modules under
`mmw-v2/board/page/` that compute what the board shows (`shared`, `board-logic`,
`local-config`, and the view builders of `topbar`, `tasks`, `canvas`, `detail`,
`settings`) are wrapped one function scope each. Each module's exports sit on
`window.MMW[<module>]`; the first three, which the others import, also sit on `window.MMW`. The
design pages call the same functions the product calls, so a page and the product
disagree only where the markup does. The clock is frozen at `window.MMW_NOW` when a
page sets it, so elapsed times read the same on every render.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PAGE = Path(__file__).resolve().parents[4] / "mmw-v2" / "board" / "page"
SHARED = {"shared", "board-logic", "local-config"}
MODULES = ["shared", "board-logic", "local-config", "topbar", "tasks", "canvas", "detail", "settings"]
IMPORT = re.compile(r'^import \{([^}]*)\} from "\./([\w-]+)\.mjs";\n', re.M)
EXPORT = re.compile(r"^export (async function|function|const) (\w+)", re.M)


def wrap(name: str) -> str:
    text = (PAGE / f"{name}.mjs").read_text(encoding="utf-8")
    heads = []
    for names, source in IMPORT.findall(text):
        if source not in MODULES:
            continue
        parts = [p.strip() for p in names.split(",") if p.strip()]
        heads.append("const {" + ", ".join(p.replace(" as ", ": ") for p in parts) + "} = MMW;")
    text = IMPORT.sub("", text)
    if name == "shared":
        text = text.replace("to = new Date()", "to = (window.MMW_NOW ? new Date(window.MMW_NOW) : new Date())")
    exported = [m.group(2) for m in EXPORT.finditer(text)]
    text = EXPORT.sub(lambda m: f"{m.group(1)} {m.group(2)}", text)
    return (f"// ── {name}.mjs ──\n(function () {{\n" + "\n".join(heads) + "\n" + text
            + f"\nMMW[{name!r}] = {{{', '.join(exported)}}};\n"
            + (f"Object.assign(MMW, MMW[{name!r}]);\n" if name in SHARED else "")
            + "})();\n")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Run: python3 bundle_logic.py <out.js>")
    body = "window.MMW = window.MMW || {};\nconst MMW = window.MMW;\n" + "".join(wrap(m) for m in MODULES)
    body = "(function () {\n" + body + "})();\n"
    Path(sys.argv[1]).write_text(body, encoding="utf-8")
    print(f"wrote {sys.argv[1]} ({len(body)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
