#!/usr/bin/env python3
"""Fail when a Markdown file under mmw-v2/upstream/skills/ carries an em-dash in its prose.

mmw-v2/upstream/ is a subtree of mattpocock/skills, and its own AGENTS.md rules out
em-dashes in prose; `writing-for-agents`' SKILL-SET-REVIEW.md makes that rule bind this
repository's text inside the subtree too. Upstream's own text there has none, so every
hit is a sentence this repository wrote. Every suite's run.sh runs this after
check_module_paths.py.

It reads every `.md` under mmw-v2/upstream/skills/ and reports each line outside a fenced
code block that contains U+2014. A fenced block is exempt because what it holds is a
format a program reads, copied verbatim (the review comment's finding row, which
verify-ticket.py parses by its separators), not prose. Exit 0 prints nothing; exit 1
prints one line per hit, then why and what to do.
"""

from __future__ import annotations

import sys
from pathlib import Path

MMW = Path(__file__).resolve().parents[2]
SCANNED = MMW / "upstream" / "skills"
DASH = "—"


def hits() -> list[str]:
    rows = []
    for path in sorted(SCANNED.rglob("*.md")):
        fenced = False
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if not fenced and DASH in line:
                at = line.index(DASH)
                excerpt = line[max(0, at - 40):at + 40].strip()
                rows.append(f"{path.relative_to(MMW.parent)}:{number}: em-dash in \"{excerpt}\"")
    return rows


def main() -> int:
    rows = hits()
    if not rows:
        return 0
    for row in rows:
        print(row)
    print(f"{len(rows)} line(s) under mmw-v2/upstream/skills/ carry an em-dash outside a fenced code block.")
    print("Why: mmw-v2/upstream/AGENTS.md allows no em-dash in the subtree's prose, and upstream's own text has none.")
    print("Next: rewrite each sentence with a comma, colon, period, parentheses or a conjunction, whichever it wants; "
          "never swap the character blindly. A format a program reads goes in a fenced code block.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
