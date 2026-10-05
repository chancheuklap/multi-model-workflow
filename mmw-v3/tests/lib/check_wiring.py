#!/usr/bin/env python3
"""Check that the skill set's text points only at things that exist.

    python3 mmw-v3/tests/lib/check_wiring.py [<skills dir>]

Adding a playbook, a principle or a skill means writing its name in more than one
place, and a name written in one place and missing from the other fails silently: an
agent told to read a file or run a skill that is not there guesses. Four kinds of
pointer are checked, in the text of every `.md` under `mmw-v3/skills/` (HTML comments
and fenced code left out):

1. **Routes.** Each file in the mmw-mode skill's `playbooks/` (its README aside) has
   exactly one route line in `## Playbooks` of its `SKILL.md`, every route line names
   a file that exists, and the bold name of the line is the file's `# ` title.
2. **Principles.** Each `principle-*` skill has exactly one index line in `## Principles`,
   every index line names one that exists, and the bold name is that skill's `# ` title.
3. **Skills and files named.** A skill named as "the `x` skill", "the **x** skill",
   "`x` skill's" or "skill `x`", and a principle named in bold or code
   (`**principle-x**`), is a directory under `mmw-v3/skills/`, unless the name follows
   "pstack" or "pstack's", whose skills MMW does not carry. A file path starting
   `references/`, `scripts/`, `playbooks/` or `agents/` resolves in a skill named earlier
   in its paragraph, in the skill the text belongs to, beside the file, in the mmw-mode
   skill, or, for a skill copied from a vendored upstream, in that upstream's tree. A path
   ending in `/` is a directory of the repository being worked on, and a one-letter name
   (`references/x.md`) is an example; neither is checked.
4. **dispatch.sh commands.** Each `dispatch.sh <command>` is a command `dispatch.sh` has.

Text about MMW v2 (a line naming it, or a section whose heading does) records where
something came from and is not checked.

It reads files and writes nothing. `<skills dir>` defaults to `mmw-v3/skills/` beside this
script; its own test passes a broken copy. Exit 0 prints `WIRING OK`; exit 1 prints one
finding per line, each naming the file and line to change.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKILLS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "skills"
MODE_DIR = SKILLS / "mmw-mode"
MODE = MODE_DIR / "SKILL.md"
DISPATCH_SH = SKILLS / "dispatch" / "scripts" / "dispatch.sh"

ROUTE_LINE = re.compile(r"^- \*\*(.+?)\.\*\* .*`(playbooks/[a-z0-9-]+\.md)`", re.M)
INDEX_LINE = re.compile(r"^- \*\*(.+?)\*\* \(\*\*(principle-[a-z0-9-]+)\*\*\)", re.M)
SKILL_NAMED = [
    re.compile(r"(?<!pstack's )the `([a-z0-9-]+)` skill"),
    re.compile(r"(?<!pstack's )the \*\*([a-z0-9-]+)\*\* skill"),
    re.compile(r"(?<!pstack's )`([a-z0-9-]+)` skill's"),
    re.compile(r"\bskill `([a-z0-9-]+)`"),
    re.compile(r"(?<!pstack's )(?<!pstack )(?<![`*])[`*]+(principle-[a-z0-9-]+)[`*]"),
]
PATH_NAMED = re.compile(r"`((?:references|scripts|playbooks|agents)/[A-Za-z0-9_./-]+)`")
NAME_BEFORE = re.compile(r"[`*]([a-z0-9-]+)[`*]")
DISPATCH_CMD = re.compile(r"dispatch\.sh ([a-z][a-z-]+)")


def readable(path: Path) -> str:
    """The text an agent acts on: HTML comments and fenced code blanked, line count kept."""
    text = path.read_text(encoding="utf-8")
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    text = re.sub(r"^## [^\n]*MMW v2.*?(?=^## |\Z)", blank, text, flags=re.M | re.S)
    return re.sub(r"^.*(?:MMW v2|mmw-v2/).*$", blank, text, flags=re.M)


def section(text: str, heading: str) -> tuple[str, int]:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return (m.group(1), text[:m.start(1)].count("\n")) if m else ("", 0)


def title(path: Path) -> str | None:
    m = re.search(r"^#{1,3} (.+)$", path.read_text(encoding="utf-8"), re.M)
    return m.group(1).strip() if m else None


def where(path: Path, text: str, offset: int) -> str:
    return f"{path.relative_to(SKILLS.parent.parent)}:{text[:offset].count(chr(10)) + 1}"


def check_routes(mode: str) -> list[str]:
    body, first = section(mode, "Playbooks")
    found, named = [], {}
    for m in ROUTE_LINE.finditer(body):
        line = f"{MODE.relative_to(SKILLS.parent.parent)}:{first + body[:m.start()].count(chr(10)) + 1}"
        name, rel = m.group(1), m.group(2)
        named.setdefault(rel, []).append(line)
        path = MODE_DIR / rel
        if not path.is_file():
            found.append(f"{line}: the route line for **{name}.** names {rel}, which does not exist")
        elif title(path) != name:
            found.append(f"{line}: the route line says **{name}.**, and {rel} is titled {title(path)!r}")
    for path in sorted((MODE_DIR / "playbooks").glob("*.md")):
        rel = f"playbooks/{path.name}"
        if path.name == "README.md":
            continue
        if rel not in named:
            found.append(f"{MODE.relative_to(SKILLS.parent.parent)}: `## Playbooks` has no route line for {rel}")
        elif len(named[rel]) > 1:
            found.append(f"{', '.join(named[rel])}: {rel} has {len(named[rel])} route lines")
    return found


def check_principles(mode: str) -> list[str]:
    body, first = section(mode, "Principles")
    found, named = [], {}
    for m in INDEX_LINE.finditer(body):
        line = f"{MODE.relative_to(SKILLS.parent.parent)}:{first + body[:m.start()].count(chr(10)) + 1}"
        name, skill = m.group(1), m.group(2)
        named.setdefault(skill, []).append(line)
        path = SKILLS / skill / "SKILL.md"
        if not path.is_file():
            found.append(f"{line}: the index line names {skill}, which is not a skill")
        elif title(path) != name:
            found.append(f"{line}: the index line says **{name}**, and {skill} is titled {title(path)!r}")
    for path in sorted(SKILLS.glob("principle-*/SKILL.md")):
        skill = path.parent.name
        if skill not in named:
            found.append(f"{MODE.relative_to(SKILLS.parent.parent)}: `## Principles` has no index line for {skill}")
        elif len(named[skill]) > 1:
            found.append(f"{', '.join(named[skill])}: {skill} has {len(named[skill])} index lines")
    return found


def dispatch_commands() -> set[str]:
    text = DISPATCH_SH.read_text(encoding="utf-8")
    labels = re.findall(r"^\s{2}([a-z][a-z|-]*)\)", text, re.M)
    return {name for label in labels for name in label.split("|")}


def upstream_roots(skill: str) -> list[Path]:
    """The root of each vendored upstream tree that carries this skill under its skills/."""
    return [skills.parent for skills in SKILLS.parent.glob("upstream-*/skills")
            if (skills / skill).is_dir()]


def check_names(path: Path, commands: set[str]) -> list[str]:
    text = readable(path)
    own = path.relative_to(SKILLS).parts[0]
    found = []
    for rx in SKILL_NAMED:
        for m in rx.finditer(text):
            if not (SKILLS / m.group(1)).is_dir():
                found.append(f"{where(path, text, m.start())}: names the {m.group(1)} skill, which is not a skill")
    for m in PATH_NAMED.finditer(text):
        rel = m.group(1).split("#")[0].rstrip(".,;:)")
        if rel.endswith("/") or len(Path(rel).stem) == 1:
            continue
        paragraph = text[text.rfind("\n\n", 0, m.start()) + 1:m.start()]
        places = [SKILLS / name for name in NAME_BEFORE.findall(paragraph)
                  if (SKILLS / name).is_dir()]
        places += [SKILLS / own, path.parent, MODE_DIR, *upstream_roots(own)]
        if not any((place / rel).exists() for place in places):
            found.append(f"{where(path, text, m.start())}: names {rel}, which is not there")
    for m in DISPATCH_CMD.finditer(text):
        if m.group(1) not in commands:
            found.append(f"{where(path, text, m.start())}: names `dispatch.sh {m.group(1)}`, "
                         f"which dispatch.sh does not have")
    return found


def main() -> int:
    mode = readable(MODE)
    findings = check_routes(mode) + check_principles(mode)
    commands = dispatch_commands()
    for path in sorted(SKILLS.rglob("*.md")):
        if "__pycache__" not in path.parts:
            findings += check_names(path, commands)
    for finding in findings:
        print(finding)
    if findings:
        return 1
    print("WIRING OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
