#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Fail when a skill's SKILL.md frontmatter is not valid YAML, carries a key the set
does not allow, or says a skill is started only by the person in one host's form and
not the other's.

Every host scans a skill's frontmatter into its system prompt at start, and nothing
else parses it, so an invalid block is caught only here or by a host at start. It
happened for real: `advisor` and `ui-acceptance` both shipped a `description` with an
unquoted colon and space, which breaks a strict YAML parser though a lenient one
accepts it (docs/reviews/2026-09-23-skill-set, fixed in d37a6048).

The rule is the `writing-for-agents` skill's SKILL-SET-RULES.md `### Descriptions`:
the frontmatter holds `name` and `description`, `argument-hint` when the skill takes
an argument the person types, and `disable-model-invocation: true` on a skill only the
person starts. Claude Code reads that key and Codex reads only
`policy.allow_implicit_invocation: false` in the skill's `agents/openai.yaml`, so the
two are held to agree: one without the other leaves the skill model-invoked on half
the hosts.

It reads every mmw-v3/skills/<name>/SKILL.md and parses the text between its first
two `---` lines with PyYAML. Every suite's run.sh runs this after
check_module_paths.py, through `uv run` so PyYAML comes from this file's own PEP 723
block above. Exit 0 prints nothing; exit 1 prints one line per finding, then why and
what to do. Exit 2 means PyYAML itself is missing and nothing could be checked.
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
SKILLS = MMW / "skills"
ALLOWED = {"name", "description", "argument-hint", "disable-model-invocation"}


def frontmatter_text(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return None


def implicit_off(skill: Path) -> tuple[bool, str | None]:
    """Whether agents/openai.yaml turns implicit invocation off, or why it cannot be read."""
    path = skill / "agents" / "openai.yaml"
    if not path.is_file():
        return False, None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return False, f"agents/openai.yaml is not valid YAML ({exc})"
    policy = data.get("policy") if isinstance(data, dict) else None
    return isinstance(policy, dict) and policy.get("allow_implicit_invocation") is False, None


def findings() -> list[str]:
    rows = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        rel = path.relative_to(MMW.parent)
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
        extra = sorted(set(data) - ALLOWED)
        missing = sorted({"name", "description"} - set(data))
        if extra:
            rows.append(f"{rel}: frontmatter has a key the set does not allow: {', '.join(extra)}")
        if missing:
            rows.append(f"{rel}: frontmatter is missing {', '.join(missing)}")
        if data.get("name") not in (None, path.parent.name):
            rows.append(f"{rel}: `name` is {data.get('name')!r}, not its directory name {path.parent.name!r}")
        user_only = data.get("disable-model-invocation") is True
        if "disable-model-invocation" in data and not user_only:
            rows.append(f"{rel}: `disable-model-invocation` is set to something other than true")
        off, problem = implicit_off(path.parent)
        if problem:
            rows.append(f"{rel.parent}/{problem}")
        elif user_only and not off:
            rows.append(f"{rel}: `disable-model-invocation: true` without "
                        "`policy.allow_implicit_invocation: false` in agents/openai.yaml")
        elif off and not user_only:
            rows.append(f"{rel}: agents/openai.yaml sets `allow_implicit_invocation: false` without "
                        "`disable-model-invocation: true` here")
    return rows


def main() -> int:
    rows = findings()
    if not rows:
        return 0
    for row in rows:
        print(row)
    print(f"{len(rows)} finding(s) in a skill's SKILL.md frontmatter.")
    print("Why: a host parses this block as YAML at start, and a skill started only by the "
          "person has to say so to Claude Code and to Codex alike.")
    print("Next: quote any value holding a colon followed by a space; keep only the keys "
          "the writing-for-agents skill's SKILL-SET-RULES.md `### Descriptions` allows; set or remove "
          "`disable-model-invocation: true` and agents/openai.yaml's policy together.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
