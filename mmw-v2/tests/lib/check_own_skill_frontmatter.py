#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Fail when a listed skill's SKILL.md frontmatter is not valid YAML, or a
skill this repository wrote carries a frontmatter key beyond name and description.

Every host scans a skill's frontmatter into its system prompt at start
(mmw-v2/install.sh header comment), and install.sh itself never parses it
(`writing-for-agents`'s SKILL-SET-RULES.md `### Descriptions`), so an invalid
block is caught only here or by a host at start. It happened for real: `advisor`
and `ui-acceptance` both shipped a `description` with an unquoted colon and
space, which breaks a strict YAML parser though a lenient one accepts it
(docs/reviews/2026-09-23-skill-set, fixed in d37a6048). A skill this repository
wrote also carries no host-side manifest beside SKILL.md, so its frontmatter has
exactly two keys, `name` and `description`, for its name and description to have
one authority; an upstream skill may legitimately carry a third
(`disable-model-invocation`, see mmw-v2/merge-notes/README.md) and is not held
to that second check.

It reads mmw-v2/skills.txt for the installed set, resolves each entry's
SKILL.md, and parses the text between its first two `---` lines with PyYAML.
The shared-lint entry `mmw-v2/tests/lib/run_shared_lints.sh` runs this after
check_upstream_em_dashes.py, through `uv run` so PyYAML comes from this file's
own PEP 723 block above; run directly with a plain `python3` on a machine that
already has PyYAML on its path too.
Exit 0 prints nothing; exit 1 prints one line per finding, then why and what to
do. Exit 2 means PyYAML itself is missing and nothing could be checked.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("could not import the `yaml` module (PyYAML); no frontmatter was checked")
    print("Why: this check parses SKILL.md frontmatter with a real YAML parser, and the "
          "standard library has none.")
    print("Next: run this file with `uv run` (it declares pyyaml in its own PEP 723 block), "
          "or install pyyaml for this python3 and run it directly.")
    sys.exit(2)

MMW = Path(__file__).resolve().parents[2]
SKILLS_TXT = MMW / "skills.txt"
OWN_SKILLS = MMW / "skills"


def installed_skill_md_paths() -> list[Path]:
    paths = []
    for raw in SKILLS_TXT.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("self/"):
            base = OWN_SKILLS / line[len("self/"):]
        elif line.startswith("dd/"):
            base = MMW / "upstream-diagram-design" / "skills" / line[len("dd/"):]
        else:
            base = MMW / "upstream" / "skills" / line
        paths.append(base / "SKILL.md")
    return paths


def frontmatter_text(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return None


def findings() -> list[str]:
    rows = []
    for path in installed_skill_md_paths():
        rel = path.relative_to(MMW.parent)
        if not path.is_file():
            rows.append(f"{rel}: mmw-v2/skills.txt names this skill, but the file does not exist")
            continue
        block = frontmatter_text(path)
        if block is None:
            rows.append(f"{rel}: no `---`-delimited frontmatter block at the top of the file")
            continue
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            rows.append(f"{rel}: frontmatter is not valid YAML ({exc})")
            continue
        if not isinstance(data, dict):
            rows.append(f"{rel}: frontmatter does not parse to a mapping")
            continue
        if path.is_relative_to(OWN_SKILLS):
            extra = sorted(set(data) - {"name", "description"})
            missing = sorted({"name", "description"} - set(data))
            if extra:
                rows.append(f"{rel}: frontmatter has a key beyond name and description: {', '.join(extra)}")
            if missing:
                rows.append(f"{rel}: frontmatter is missing {', '.join(missing)}")
    return rows


def main() -> int:
    rows = findings()
    if not rows:
        return 0
    for row in rows:
        print(row)
    print(f"{len(rows)} finding(s) in a listed skill's SKILL.md frontmatter.")
    print("Why: a host parses this block as YAML at start, and a skill this repository wrote "
          "carries no host-side manifest beside it, so name and description have one authority.")
    print("Next: quote any value holding a colon followed by a space and re-check; for a skill "
          "this repository wrote, remove any frontmatter key beyond `name` and `description`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
