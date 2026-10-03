#!/usr/bin/env python3
"""Check the text of every skill in the set (each skill directory beside this one): what a script can check
exactly, so a reader can rerun it.

- Each `SKILL.md` has frontmatter with exactly `name` and `description`, and `name` matches its skill directory;
  one its skill's `imports.tsv` lists as copied from upstream may also keep upstream's other frontmatter keys.
- A skill directory that is a symlink is an upstream subtree's skill, used as upstream keeps it; it is listed as
  not checked.
- In a file its skill's `imports.tsv` lists, a path or link that the listed source file already names is the
  source's to keep, and is not checked.
- A principle file opens with its `#` title and a playbook file with its `###` title; neither has frontmatter.
- Every `references/`, `playbooks/`, `principles/` and `scripts/` path a skill's text names exists in that skill;
  one introduced as "the `X` skill's" exists in skill X when X is in the set, and is listed as not checked
  when it is not. A path with a `<placeholder>` or a `*` names no one file.
- Every relative Markdown link resolves.
- A principle is cited by its path, never as a bare `**principle-<slug>**`.
- In the `mmw-mode` skill: every principle file has its index line in `## Principles`; every playbook routed in
  `## Playbooks` has its file, and every playbook file is routed; a playbook is cited by its path, its bold title
  appearing only in its own file and its route line; a step named after "Run", "through", "in", "to" or "from"
  in its `SKILL.md` or a playbook exists as a step title.

Prints one line per problem, one `NOT CHECKED` line per path it could not check, then `OK` or `FAIL` with the counts. Exit 0 when there is no problem, 1 otherwise.
Usage: python3 scripts/check_skill_text.py
"""
import pathlib
import re
import sys

SET = pathlib.Path(__file__).resolve().parent.parent.parent
MODE = SET / "mmw-mode"
problems = []
unchecked = set()


def where(f):
    return f.relative_to(SET)


def frontmatter(f, text, want, upstream):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{where(f)}: has no frontmatter")
        return
    fields = dict(re.findall(r'^([\w-]+):\s*"?(.*?)"?\s*$', m.group(1), re.M))
    if not (set(fields) >= {"name", "description"} if upstream else set(fields) == {"name", "description"}):
        problems.append(f"{where(f)}: frontmatter keys are {sorted(fields)}, not name and description")
    if fields.get("name") != want:
        problems.append(f"{where(f)}: frontmatter name is {fields.get('name')!r}, not {want!r}")
    if not fields.get("description"):
        problems.append(f"{where(f)}: frontmatter description is empty")


mode_text = (MODE / "SKILL.md").read_text() if (MODE / "SKILL.md").exists() else ""
playbooks_part = mode_text.split("## Playbooks", 1)[1] if "## Playbooks" in mode_text else ""
routed = set(re.findall(r"^- \*\*([^*]+?)\.\*\* ", playbooks_part, re.M))
playbook_titles, step_titles = {}, set()
for f in sorted((MODE / "playbooks").glob("*.md")):
    text = f.read_text()
    playbook_titles[text.splitlines()[0].lstrip("# ").strip()] = f
    step_titles |= set(re.findall(r"^\d+\. \*\*(.+?)\.\*\*", text, re.M))

skills = sorted(d for d in SET.iterdir() if (d / "SKILL.md").exists() and not d.is_symlink())
unchecked |= {f"NOT CHECKED {d.name}: links to {d.resolve().relative_to(SET.parent.parent.resolve())}, an upstream subtree's skill"
              for d in SET.iterdir() if d.is_symlink()}
files = []
for skill in skills:
    imports = skill / "imports.tsv"
    source = {}
    if imports.exists():
        for line in imports.read_text().splitlines()[1:]:
            cells = line.split("\t")
            source[cells[1]] = cells[2]
    for f in sorted(skill.rglob("*.md")):
        files.append(f)
        text = f.read_text()
        local = str(f.relative_to(SET.parent.parent))
        if f == skill / "SKILL.md":
            frontmatter(f, text, skill.name, local in source)
        origin = SET.parent.parent / source.get(local, "-")
        kept = origin.read_text() if origin.is_file() else ""
        opening = {"principles": "# ", "playbooks": "### "}.get(f.parent.name)
        if opening and not (text.startswith(opening) and not text.startswith(opening + "#")):
            problems.append(f"{where(f)}: does not open with its {opening.strip()} title")
        for other, ref in re.findall(r"(?:`([\w-]+)` skill's )?`((?:references|playbooks|principles|scripts)/[^`\s]+\.\w+)`", text):
            if "<" in ref or "*" in ref or ref in kept:
                continue
            home = SET / other if other else skill
            if other and not home.is_dir():
                unchecked.add(f"NOT CHECKED {where(f)}: names {other}'s {ref}; {other} is not in this set")
            elif not (home / ref).exists():
                problems.append(f"{where(f)}: names {other + chr(39) + 's ' if other else ''}{ref}, which does not exist")
        for link in re.findall(r"\]\(([^)#:\s]+\.md)(?:#[\w-]+)?\)", text):
            if link not in kept and not (f.parent / link).exists():
                problems.append(f"{where(f)}: links {link}, which does not exist")
        for slug in sorted(set(re.findall(r"\*\*(principle-[\w-]+)\*\*", text))):
            problems.append(f"{where(f)}: cites **{slug}** by name; cite it as principles/{slug}.md")
        if skill == MODE and (f.name == "SKILL.md" or f.parent.name == "playbooks"):
            for name in sorted(set(re.findall(r"\b(?:Run|through|in|to|from) \*\*([A-Z][^*]*?)\*\*", text))):
                if name not in playbook_titles and name not in step_titles and not name.startswith("principle-"):
                    problems.append(f"{where(f)}: names **{name}**, which is no playbook or step in this skill")
            for name, home in playbook_titles.items():
                uses = text.count(f"**{name}**")
                if f.name == "SKILL.md":
                    uses -= len(re.findall(r"^- \*\*" + re.escape(name) + r"\.\*\* ", text, re.M))
                if f != home and uses > 0:
                    problems.append(f"{where(f)}: cites **{name}** by title; cite it as {home.relative_to(MODE)}")

for name in sorted(routed - set(playbook_titles)):
    problems.append(f"mmw-mode/SKILL.md: routes to **{name}**, which has no playbook file")
for name, f in sorted(playbook_titles.items()):
    if name not in routed:
        problems.append(f"{where(f)}: **{name}** has no line in ## Playbooks")
indexed = set(re.findall(r"\(`principles/(principle-[\w-]+)\.md`\)", mode_text))
for f in sorted((MODE / "principles").glob("*.md")):
    if f.stem not in indexed:
        problems.append(f"{where(f)}: has no index line in mmw-mode/SKILL.md ## Principles")

print("\n".join(problems + sorted(unchecked))) if problems or unchecked else None
print(f"{'FAIL' if problems else 'OK'} {len(files)} files, {len(problems)} problems")
sys.exit(1 if problems else 0)
