#!/usr/bin/env python3
"""Check the text of the mmw-mode skill: what a script can check exactly, so a reader can rerun it.

- `SKILL.md` and every principle file have frontmatter with exactly `name` and `description`, and `name` matches the file.
- Every `references/`, `playbooks/`, `principles/` and `scripts/` path the text names exists in this skill
  (a path with a `<placeholder>`, or one introduced as another skill's, is not this skill's file).
- Every relative Markdown link resolves.
- Every `**principle-<slug>**` cited has its file, and every principle file has its index line in `## Principles`.
- Every playbook routed in `## Playbooks` has its file, and every playbook file is routed.
- Every playbook or step named after "Run", "through", "in", "to" or "from" exists as a playbook title or a step title.

Prints one line per problem, then `OK` or `FAIL` with the counts. Exit 0 when there is no problem, 1 otherwise.
Usage: python3 scripts/check_skill_text.py
"""
import pathlib
import re
import sys

MODE = pathlib.Path(__file__).resolve().parent.parent
problems = []


def where(f):
    return f.relative_to(MODE)


def frontmatter(f, text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        problems.append(f"{where(f)}: has no frontmatter")
        return
    fields = dict(re.findall(r'^([\w-]+):\s*"?(.*?)"?\s*$', m.group(1), re.M))
    if set(fields) != {"name", "description"}:
        problems.append(f"{where(f)}: frontmatter keys are {sorted(fields)}, not name and description")
    want = MODE.name if f.name == "SKILL.md" else f.stem
    if fields.get("name") != want:
        problems.append(f"{where(f)}: frontmatter name is {fields.get('name')!r}, not {want!r}")
    if not fields.get("description"):
        problems.append(f"{where(f)}: frontmatter description is empty")


mode_text = (MODE / "SKILL.md").read_text()
playbooks_part = mode_text.split("## Playbooks", 1)[1] if "## Playbooks" in mode_text else ""
routed = set(re.findall(r"^- \*\*([^*]+?)\.\*\* ", playbooks_part, re.M))
playbook_titles, step_titles = {}, set()
for f in sorted((MODE / "playbooks").glob("*.md")):
    text = f.read_text()
    playbook_titles[text.splitlines()[0].lstrip("# ").strip()] = f
    step_titles |= set(re.findall(r"^\d+\. \*\*(.+?)\.\*\*", text, re.M))

files = sorted(MODE.rglob("*.md"))
for f in files:
    text = f.read_text()
    if f.name == "SKILL.md" or f.parent.name == "principles":
        frontmatter(f, text)
    for before, ref in re.findall(r"(.{0,8})`((?:references|playbooks|principles|scripts)/[^`\s]+\.\w+)`", text):
        if "<" not in ref and not before.endswith("skill's ") and not (MODE / ref).exists():
            problems.append(f"{where(f)}: names {ref}, which does not exist")
    for link in re.findall(r"\]\(([^)#:\s]+\.md)(?:#[\w-]+)?\)", text):
        if not (f.parent / link).exists():
            problems.append(f"{where(f)}: links {link}, which does not exist")
    for slug in sorted(set(re.findall(r"\*\*(principle-[\w-]+)\*\*", text))):
        if not (MODE / "principles" / f"{slug}.md").exists():
            problems.append(f"{where(f)}: cites {slug}, which has no file")
    if f.name == "SKILL.md" or f.parent.name == "playbooks":
        for name in sorted(set(re.findall(r"\b(?:Run|through|in|to|from) \*\*([A-Z][^*]*?)\*\*", text))):
            if name not in playbook_titles and name not in step_titles and not name.startswith("principle-"):
                problems.append(f"{where(f)}: names **{name}**, which is no playbook or step in this skill")

for name in sorted(routed - set(playbook_titles)):
    problems.append(f"SKILL.md: routes to **{name}**, which has no playbook file")
for name, f in sorted(playbook_titles.items()):
    if name not in routed:
        problems.append(f"{where(f)}: **{name}** has no line in ## Playbooks")
indexed = set(re.findall(r"\(\*\*(principle-[\w-]+)\*\*\)", mode_text))
for f in sorted((MODE / "principles").glob("*.md")):
    if f.stem not in indexed:
        problems.append(f"{where(f)}: has no index line in SKILL.md ## Principles")

print("\n".join(problems)) if problems else None
print(f"{'FAIL' if problems else 'OK'} {len(files)} files, {len(problems)} problems")
sys.exit(1 if problems else 0)
