#!/usr/bin/env python3
"""Check that the skill set's text points only at things that exist.

    python3 mmw-v4/tests/lib/check_wiring.py [<skills dir>]

Adding a playbook, a principle or a skill means writing its name in more than one
place, and a name written in one place and missing from the other fails silently: an
agent told to read a file or run a skill that is not there guesses. Seven kinds of
pointer are checked. Checks 3-5 scan every `.md` under `mmw-v4/skills/`; the others
read the files named below. HTML comments and fenced code are left out.

1. **Routes.** Each file in the mmw-mode skill's `playbooks/` has
   exactly one route line in `## Playbooks` of its `references/owning-a-task.md`, every
   route line names a file that exists, and the bold name of the line is the file's `# `
   title.
2. **Principles.** Each `principle-*` skill has exactly one index line in `## Principles`,
   and every index line names one that exists.
3. **Skills and files named.** A skill named as "the `x` skill", "the **x** skill",
   "`x` skill's" or "skill `x`", and a principle named in bold or code
   (`**principle-x**`), is a directory under `mmw-v4/skills/`, unless the name follows
   "pstack" or "pstack's", whose skills MMW does not carry. A bare `.md` file named
   as "the `x` skill's `FILE.md`" is a file in that skill's directory. A file path starting
   `references/`, `scripts/`, `playbooks/` or `agents/` resolves in a skill named earlier
   in its paragraph, in the skill the text belongs to, beside the file, in the mmw-mode
   skill, or, for a skill copied from a vendored upstream, in that upstream's tree. A path
   ending in `/` is a directory of the repository being worked on, and a one-letter name
   (`references/x.md`) is an example; neither is checked.
4. **dispatch.sh commands.** Each `dispatch.sh <command>` is a command `dispatch.sh` has.
5. **Subagent rows.** Each "on the `<row>` row" names a row in the dispatch skill's
   `roles.json` `subagents` section, and every row there is named at least once.
6. **Intent homes.** Each `Home:` in `DESIGN-INTENTS.md` names existing skills,
   files, routed playbooks and their bold step titles. Intent 41 explicitly has no home.
7. **Upstream destinations.** Each entry in an `UPSTREAM.md` `MMW` cell starts
   with an existing intent number, or `Departure` for an id in `## Departures`.

Text about MMW v2 (a line naming it, or a section whose heading does) records where
something came from and is not checked.

It reads files and writes nothing. `<skills dir>` defaults to `mmw-v4/skills/` beside this
script; its own test passes a broken copy. Exit 0 prints `WIRING OK`; exit 1 prints one
finding per line, each naming the file and line to change.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKILLS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "skills"
MODE_DIR = SKILLS / "mmw-mode"
MODE = MODE_DIR / "SKILL.md"
ROUTES = MODE_DIR / "references" / "owning-a-task.md"
DISPATCH_SH = SKILLS / "dispatch" / "scripts" / "dispatch.sh"
ROLES = SKILLS / "dispatch" / "roles.json"

ROUTE_LINE = re.compile(r"^- \*\*(.+?)\.\*\* .*`(playbooks/[a-z0-9-]+\.md)`", re.M)
INDEX_LINE = re.compile(r"^- \*\*(principle-[a-z0-9-]+)\*\*\.", re.M)
SKILL_NAMED = [
    re.compile(r"(?<!pstack's )the `([a-z0-9-]+)` skill"),
    re.compile(r"(?<!pstack's )the \*\*([a-z0-9-]+)\*\* skill"),
    re.compile(r"(?<!pstack's )`([a-z0-9-]+)` skill's"),
    re.compile(r"\bskill `([a-z0-9-]+)`"),
    re.compile(r"(?<!pstack's )(?<!pstack )(?<![`*])[`*]+(principle-[a-z0-9-]+)[`*]"),
]
PATH_NAMED = re.compile(r"`((?:references|scripts|playbooks|agents)/[A-Za-z0-9_./-]+)`")
# The consuming repository's own check command, which a skill names but no skill carries.
REPO_CHECK = "scripts/check"
BARE_SKILL_FILE = re.compile(r"(?<!pstack's )the `([a-z0-9-]+)` skill's `([A-Za-z0-9_.-]+\.md)`")
NAME_BEFORE = re.compile(r"[`*]([a-z0-9-]+)[`*]")
DISPATCH_CMD = re.compile(r"dispatch\.sh ([a-z][a-z-]+)")
SUBAGENT_ROW = re.compile(r"on the `([^`\n]+)` row")


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


def check_routes(routes: str) -> list[str]:
    body, first = section(routes, "Playbooks")
    found, named = [], {}
    for m in ROUTE_LINE.finditer(body):
        line = f"{ROUTES.relative_to(SKILLS.parent.parent)}:{first + body[:m.start()].count(chr(10)) + 1}"
        name, rel = m.group(1), m.group(2)
        named.setdefault(rel, []).append(line)
        path = MODE_DIR / rel
        if not path.is_file():
            found.append(f"{line}: the route line for **{name}.** names {rel}, which does not exist")
        elif title(path) != name:
            found.append(f"{line}: the route line says **{name}.**, and {rel} is titled {title(path)!r}")
    for path in sorted((MODE_DIR / "playbooks").glob("*.md")):
        rel = f"playbooks/{path.name}"
        if rel not in named:
            found.append(f"{ROUTES.relative_to(SKILLS.parent.parent)}: `## Playbooks` has no route line for {rel}")
        elif len(named[rel]) > 1:
            found.append(f"{', '.join(named[rel])}: {rel} has {len(named[rel])} route lines")
    return found


def check_principles(mode: str) -> list[str]:
    body, first = section(mode, "Principles")
    found, named = [], {}
    for m in INDEX_LINE.finditer(body):
        line = f"{MODE.relative_to(SKILLS.parent.parent)}:{first + body[:m.start()].count(chr(10)) + 1}"
        skill = m.group(1)
        named.setdefault(skill, []).append(line)
        path = SKILLS / skill / "SKILL.md"
        if not path.is_file():
            found.append(f"{line}: the index line names {skill}, which is not a skill")
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
    """The root of each vendored upstream tree that carries this skill under its skills/,
    and the tree its own `repo-root` link names, where it has one."""
    roots = [skills.parent for skills in (SKILLS.parents[1] / "upstream").glob("*/skills")
             if (skills / skill).is_dir()]
    link = SKILLS / skill / "repo-root"
    return roots + ([link] if link.is_dir() else [])


def check_names(path: Path, commands: set[str]) -> list[str]:
    text = readable(path)
    own = path.relative_to(SKILLS).parts[0]
    found = []
    for rx in SKILL_NAMED:
        for m in rx.finditer(text):
            if not (SKILLS / m.group(1)).is_dir():
                found.append(f"{where(path, text, m.start())}: names the {m.group(1)} skill, which is not a skill")
    for m in BARE_SKILL_FILE.finditer(text):
        skill, filename = m.groups()
        if (SKILLS / skill).is_dir() and not (SKILLS / skill / filename).is_file():
            found.append(f"{where(path, text, m.start())}: names {skill}/{filename}, which is not there")
    for m in PATH_NAMED.finditer(text):
        rel = m.group(1).split("#")[0].rstrip(".,;:)")
        if rel == REPO_CHECK or rel.endswith("/") or len(Path(rel).stem) == 1:
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


def check_subagent_rows() -> list[str]:
    roles_text = ROLES.read_text(encoding="utf-8")
    rows = {row["name"] for row in json.loads(roles_text)["subagents"]}
    found, named = [], set()
    for path in sorted(SKILLS.rglob("*.md")):
        text = readable(path)
        for m in SUBAGENT_ROW.finditer(text):
            named.add(m.group(1))
            if m.group(1) not in rows:
                found.append(f"{where(path, text, m.start())}: names subagent row {m.group(1)}, "
                             "which is not in dispatch/roles.json `subagents`")
    start = roles_text.index('"subagents"')
    for row in sorted(rows - named):
        m = re.search(r'"name"\s*:\s*' + re.escape(json.dumps(row)), roles_text[start:])
        found.append(f"{where(ROLES, roles_text, start + m.start())}: "
                     f"subagent row {row} is not named by any step")
    return found


def check_intent_homes() -> list[str]:
    path = SKILLS / "writing-for-agents/DESIGN-INTENTS.md"
    text = readable(path)
    homes = list(re.finditer(r"^ +Home: (.+)$", text, re.M))
    if not homes:
        return [f"{where(path, text, 0)}: no Home: lines matched; "
                "restore the Home: entries in DESIGN-INTENTS.md"]
    routes = {name: MODE_DIR / rel for name, rel in ROUTE_LINE.findall(readable(ROUTES))}
    repository = Path(__file__).resolve().parents[3]
    found = []
    for home in homes:
        body = home.group(1)
        skill = path.parent
        playbook = None
        previous = ""
        for token in re.finditer(r"`([^`]+)`|\*\*(.+?)\*\*", body):
            code, bold = token.groups()
            prefix = body[:token.start()]
            if bold:
                if re.search(r"(?:step |'s )$", prefix):
                    steps = (re.findall(r"^(?:\d+\. )?\*\*(.+?)\*\*", readable(playbook), re.M)
                             if playbook and playbook.is_file() else [])
                    if bold not in {step.rstrip(".") for step in steps}:
                        found.append(f"{where(path, text, home.start())}: Home names step **{bold}**, "
                                     "which its playbook does not have; correct DESIGN-INTENTS.md")
                elif bold in routes:
                    playbook = routes[bold]
                elif not (body[token.end():].startswith(" rule") or prefix.endswith("(")):
                    found.append(f"{where(path, text, home.start())}: Home names playbook **{bold}**, "
                                 "which has no route; correct DESIGN-INTENTS.md")
                continue
            if code.startswith("#") or body[token.end():].startswith(" section"):
                continue
            if " " in code or previous.startswith("dispatch.sh "):
                previous = code
                continue
            previous = code
            if "<" in code:
                continue
            if "/" in code or "." in code:
                if code.startswith("mmw-v4/skills/"):
                    target = SKILLS / code.removeprefix("mmw-v4/skills/")
                elif code.startswith("mmw-mode/"):
                    target = SKILLS / code
                elif (code.startswith(("mmw-v4/", "docs/")) or code == "AGENTS.md"
                      or prefix.endswith("repository's ")):
                    target = repository / code
                elif body[token.end():].startswith("]("):
                    target = path.parent / code
                else:
                    target = skill / code
            else:
                skill = SKILLS / code
                target = skill / "SKILL.md"
            if not target.exists():
                found.append(f"{where(path, text, home.start())}: Home names {code}, "
                             "which does not exist; correct DESIGN-INTENTS.md")
    return found


def check_upstream_destinations() -> list[str]:
    directory = SKILLS / "writing-for-agents"
    path = directory / "UPSTREAM.md"
    if not path.exists():
        return [f"{path.relative_to(SKILLS.parent.parent)}:1: upstream destinations file "
                "does not exist; restore UPSTREAM.md"]
    design = readable(directory / "DESIGN-INTENTS.md")
    intents = set(re.findall(r"^(\d+)\. \*\*", design, re.M))
    departures, _ = section(design, "Departures")
    departed = {identifier for cell in re.findall(r"^\| ([MP]\d+.*?) \|", departures, re.M)
                for identifier in re.findall(r"[MP]\d+", cell)}
    text = readable(path)
    rows = list(re.finditer(r"^\| ([MP]\d+) \|.*$", text, re.M))
    if not rows:
        return [f"{where(path, text, 0)}: no upstream intent rows matched; "
                "restore the | M<n> | and | P<n> | rows in UPSTREAM.md"]
    found = []
    for row in rows:
        cells = row.group().strip("|").split("|")
        entries = cells[4].strip().split("; ") if len(cells) == 5 else [""]
        for entry in entries:
            leading = re.match(r"^(\d+|Departure)\b", entry.strip())
            token = leading.group(1) if leading else None
            if token in intents or (token == "Departure" and row.group(1) in departed):
                continue
            found.append(f"{where(path, text, row.start())}: {row.group(1)} MMW entry {entry!r} "
                         "must start with an existing intent number or Departure for an id in "
                         "DESIGN-INTENTS.md `## Departures`; correct this MMW cell")
    return found


def main() -> int:
    mode = readable(MODE)
    findings = (check_routes(readable(ROUTES)) + check_principles(mode)
                + check_subagent_rows() + check_intent_homes() + check_upstream_destinations())
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
