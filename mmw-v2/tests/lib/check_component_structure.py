#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check component structure, not the validity of cross-file destinations.

No file arguments scans own components. File arguments restrict the check to
those components. --root is a test seam. Findings carry a source-line excerpt
(up to 80 characters, starting at the match on a long line) for counted exceptions.
Exit 0 means checked and clean, 1 means a violation or no components, 2 unchecked.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

try:
    from skill_text import (HEADING, MODE_DIR, MODE_ROOT, TextError, classify, frontmatter,
                            installed_skills, markdown_units, normalize_title,
                            read_imports, sentences)
except ImportError as exc:
    print(f'STRUCTURE UNCHECKED: {exc}\nNext: run this script with uv run.\nWhy: PyYAML is required to read component frontmatter.', file=sys.stderr)
    raise SystemExit(2)

# Stable ids. Retired ids are not reused. Each source names the controlling rule.
RULES = {
    'mode-name': {'source': 'R18 §2.1; R19 §8', 'message': 'name must equal MODE_DIR and model invocation must be enabled'},
    'mode-sections': {'source': 'R18 §2.2; R20 S-M1', 'message': 'mode H2 sections must be in the prescribed order'},
    'mode-imported-triggers': {'source': 'R18 §2.2, §8.2', 'message': 'Imported triggers belongs under Non-negotiables'},
    'mode-principle-line': {'source': 'R18 §2.2 Principles; R20 S-M3', 'message': 'principle index needs a bold display name, bold slug and applicability'},
    'mode-route-line': {'source': 'L7 A.1; R20 S-M3', 'message': 'route must begin with a bold name and end with a quoted playbook path'},
    'playbook-title': {'source': 'L7 A.2; R20 S-P1', 'message': 'playbook starts with H3 and has no frontmatter, H1 or H2'},
    'playbook-owner-line': {'source': 'R18 §3.2; R20 S-P1', 'message': 'ownership line must be the first paragraph after the title'},
    'playbook-steps': {'source': 'R18 §3.2; R20 S-O2', 'message': 'steps need a first ordered list numbered consecutively from 1; long form needs exactly one Steps section'},
    'playbook-where-table': {'source': 'R20 S-P6; #592 §7', 'message': 'Where you are needs its first-line instruction, local step destinations and final Anything else row',
                             'role_playbooks': ('run-a-night', 'land-one-ticket', 'work-a-ticket', 'review-a-ticket', 'research-a-question')},
    'step-title': {'source': 'R18 §1.3; R20 X17, S-P3', 'message': 'each step needs a unique bold title ending in a period'},
    'step-done-when': {'source': 'SKILL-SET-RULES.md Rules and completion criteria; R20 X10', 'message': 'step needs a line beginning Done when'},
    'step-names-component': {'source': 'R18 §3.2, §7.5; R20 S-P7', 'message': 'step must name a component or put (judgement) immediately after its title'},
    'playbook-reply': {'source': 'L7 A.2; R20 §5.2', 'message': 'exactly one Reply line must be the last nonempty line'},
    'principle-frontmatter': {'source': 'R18 §1.3, §5.1', 'message': 'principle frontmatter needs only name and description, named after its file'},
    'principle-applies': {'source': 'L7 A.4; R20 X7', 'message': 'description must begin Apply when/to/after/before/during/whenever and have at least two sentences'},
    'principle-body': {'source': 'L7 A.4; R20 S-R1', 'message': 'principle begins with H1, uses bold labels instead of sections and has at most one Why'},
    'principle-direction': {'source': 'L7 B.2; R20 S-R2', 'message': 'principle must not point at a playbook, script or mode'},
    'capability-next-step': {'source': 'R18 §4.5; R14 §2; R20 S-C3', 'message': 'next-step routing belongs in a playbook'},
    'capability-playbook-name': {'source': 'R18 §4.5; R20 S-C3', 'message': 'capability must not name a playbook or point into mode'},
    'numbered-cross-reference': {'source': 'R18 §7.5; R20 X9, N12; #592 §7', 'message': 'cross-file references use titles, not numbers'},
    'host-name': {'source': 'SKILL-SET-RULES.md Paths and host neutrality; R21 §4.2', 'message': 'prose must not name a host, runner or host-specific tool'},
    'no-dash': {'source': 'R20 X5, S-G5, K8; R21 §4.2', 'message': 'new components must not use en or em dashes outside fenced code'},
    'description-trigger': {'source': 'SKILL-SET-RULES.md Descriptions; Agent Skills MAX_DESCRIPTION_LENGTH', 'message': 'description needs Use triggers, at most one exclusion, at most three sentences and 1024 characters'},
    'description-content': {'source': 'SKILL-SET-RULES.md Descriptions; R21 §4.2', 'message': 'description must not contain routing to other skills, internal paths, playbooks or numbered steps'},
    'skill-name': {'source': 'Agent Skills _validate_name; R21 §4.2', 'message': 'skill name must equal its directory name and be at most 64 characters'},
}


@dataclass(frozen=True)
class FindingKey:
    path: str
    rule: str
    excerpt: str

    @property
    def key(self):
        return FindingKey(self.path, self.rule, self.excerpt)


@dataclass(frozen=True)
class Finding(FindingKey):
    line: int

    def render(self):
        return f'{self.path}:{self.line}: {self.rule} {RULES[self.rule]["message"]} | {self.excerpt}'


class Document:
    def __init__(self, path: str, text: str):
        self.path = path
        self.text = text
        self.lines = text.splitlines()
        try:
            self.data, self.start, self.marks = frontmatter(text)
            self.units = markdown_units(text)
        except TextError as exc:
            raise TextError(f'{path}: {exc}', exc.next_step or
                            f'correct the frontmatter in {path} and rerun.') from exc
        # All structural parsing uses the same Markdown segmentation as other text checks.
        self.hidden = {row for u in self.units if u.kind in ('code', 'html')
                       for row in range(u.line, u.end_line + 1)}
        self.body = [(i + 1, line) for i, line in enumerate(self.lines)
                     if i >= self.start and i + 1 not in self.hidden]
        self.headings = [(row, len(m[1]), normalize_title(m[2])) for row, line in self.body
                         if (m := HEADING.match(line))]
        self.findings: list[Finding] = []

    def fail(self, rule: str, row: int = 1, match: str = ''):
        raw = self.lines[row - 1] if 0 < row <= len(self.lines) else ''
        at = raw.find(match) if match else 0
        if at < 0 and match:
            # A Markdown sentence can span lines; its matching phrase may not
            # fit on the source row. Use its longest prefix on that source row.
            tokens = match.split()
            for size in range(len(tokens), 0, -1):
                prefix = re.search(r'\s+'.join(re.escape(t) for t in tokens[:size]), raw)
                if prefix:
                    at = prefix.start()
                    break
        excerpt = raw if len(raw) <= 80 else raw[max(0, at):max(0, at) + 80]
        finding = Finding(self.path, rule, excerpt, row)
        self.findings.append(finding)

    def section(self, title: str, level: int = 2):
        heading = next((h for h in self.headings if h[1:] == (level, title)), None)
        if heading is None:
            return []
        end = next((row for row, depth, _ in self.headings
                    if row > heading[0] and depth <= level), len(self.lines) + 1)
        return [(row, line) for row, line in self.body if heading[0] < row < end]

    def match_units(self, rule: str, pattern, units=None):
        for unit in self.units if units is None else units:
            if unit.kind in ('code', 'html', 'field'):
                continue
            for m in re.finditer(pattern, unit.text):
                row = unit.text_lines[m.start()] if unit.text_lines else unit.line
                self.fail(rule, row, m.group())


@dataclass
class Inventory:
    skills: dict[str, str]
    playbooks: dict[str, str]
    scripts: set[str]

    def skill_pattern(self, exclude: str = '', *, path_segment: bool = False):
        # path_segment is description-content: a name touching "." or "/" is a
        # path or file segment, not a mention of the skill.
        edge = r'\w./-' if path_segment else r'\w-'
        names = [re.escape(n) for n in self.skills if n != exclude]
        return r'(?<![' + edge + r'])(?:' + '|'.join(names or [r'(?!)']) + r')(?![' + edge + r'])'

    def playbook_pattern(self):
        names = [r'(?<![\w-])' + re.escape(n) + r'(?![\w-])' for slug, title in self.playbooks.items()
                 for n in (slug + '.md', title)]
        return r'playbooks/|' + re.escape(MODE_DIR) + r'\s+[\w-]+#|' + '|'.join(names or [r'(?!)'])


def inventory(root: Path, imports) -> Inventory:
    skills = installed_skills(root)
    playbooks = {}
    for directory in (MODE_ROOT + '/playbooks', '.mmw/playbooks'):
        for file in sorted((root / directory).glob('*.md')):
            if classify(str(file.relative_to(root)), imports).kind != 'playbook':
                continue
            text = file.read_text(encoding='utf-8')
            first = next((s.strip() for s in text.splitlines() if s.strip()), '')
            if first.startswith('### '):
                playbooks[file.stem] = first[4:].strip()
    scripts = {p.name for p in (root / MODE_ROOT / 'scripts').rglob('*') if p.is_file()}
    return Inventory(skills, playbooks, scripts)


def check_mode(doc: Document):
    if doc.data.get('name') != MODE_DIR or 'disable-model-invocation' in doc.data:
        doc.fail('mode-name', doc.marks.get('name', 1))
    expected = ['Non-negotiables', 'Principles', 'Autonomy', 'Re-entry', 'Subagents', 'Writing the reply', 'Playbooks']
    h2 = [name for _, level, name in doc.headings if level == 2]
    first_h2 = next((row for row, level, _ in doc.headings if level == 2), len(doc.lines) + 1)
    h1 = [row for row, level, _ in doc.headings if level == 1]
    with_comments = expected[:-1] + ['Comments', 'Playbooks']
    if h2 not in (expected, with_comments) or len(h1) > 1 or any(row > first_h2 for row in h1):
        doc.fail('mode-sections', first_h2 if first_h2 <= len(doc.lines) else 1)
    parent = ''
    for row, depth, title in doc.headings:
        if depth == 2:
            parent = title
        elif depth == 3 and title == 'Imported triggers' and parent != 'Non-negotiables':
            doc.fail('mode-imported-triggers', row)
    for row, line in doc.section('Principles'):
        if re.match(r'^\s*[-*+]\s', line) and not re.fullmatch(r'\s*- \*\*[^*]+\*\* \(\*\*principle-[\w-]+\*\*\)\. .+\.\s*', line):
            doc.fail('mode-principle-line', row)
    # Any list marker followed by a bold name is a route line. The shape
    # still requires "- **". A direct capability line does not begin with bold.
    for row, line in doc.section('Playbooks'):
        if re.match(r'^\s*[-*+]\s+\*\*', line) and not re.fullmatch(r'\s*- \*\*[^*]+\.\*\* .+ `playbooks/[^`]+\.md`\.\s*', line):
            doc.fail('mode-route-line', row)


def ordered_steps(doc: Document):
    h4 = [(row, title) for row, depth, title in doc.headings if depth == 4]
    sections = [row for row, title in h4 if title == 'Steps']
    if h4:
        if len(sections) != 1:
            doc.fail('playbook-steps', h4[0][0])
            return []
        scope = doc.section('Steps', 4)
    else:
        scope = doc.body
    start = next((i for i, (_, line) in enumerate(scope) if re.match(r'^\d+\.\s', line)), None)
    if start is None:
        doc.fail('playbook-steps', sections[0] if sections else 1)
        return []
    groups = []
    for row, line in scope[start:]:
        item = re.match(r'^(\d+)\.\s+(.*)$', line)
        if item:
            groups.append((row, int(item[1]), item[2], [(row, line)]))
        elif not line.strip() or line[0].isspace():
            groups[-1][3].append((row, line))
        else:
            break
    if [g[1] for g in groups] != list(range(1, len(groups) + 1)):
        doc.fail('playbook-steps', groups[0][0])
    return groups


def check_playbook(doc: Document, imported: bool, inv: Inventory):
    first = next(((i + 1, s.strip()) for i, s in enumerate(doc.lines) if s.strip()), (1, ''))
    bad_title = not re.fullmatch(r'###\s+\S.*', first[1])
    if not imported:
        bad_title = bad_title or bool(doc.start) or any(depth < 3 for _, depth, _ in doc.headings)
    if bad_title:
        doc.fail('playbook-title', first[0])
    nonempty = [(i + 1, s.strip()) for i, s in enumerate(doc.lines) if s.strip()]
    replies = [(row, s) for row, s in doc.body if s.startswith('**Reply:**')]
    if len(replies) != 1 or not nonempty or (replies and replies[-1][0] != nonempty[-1][0]):
        doc.fail('playbook-reply', replies[0][0] if replies else nonempty[-1][0] if nonempty else 1)
    if imported:
        return
    owners = [(row, s) for row, s in doc.body if s.startswith('**You own ')]
    if owners and (len(owners) != 1 or len(nonempty) < 2 or owners[0][0] != nonempty[1][0]
                   or not re.match(r'^\*\*You own .+?\*\*', owners[0][1])):
        doc.fail('playbook-owner-line', owners[0][0])
    steps = ordered_steps(doc)
    titles = []
    for row, _, content, rows in steps:
        title = re.match(r'^\*\*([^*]+)\.\*\*(?:\s+|$)(.*)', content)
        if not title or title[1] in titles:
            doc.fail('step-title', row)
        if title:
            titles.append(title[1])
        if not any(s.lstrip().startswith('Done when') for _, s in rows):
            doc.fail('step-done-when', row)
        body = '\n'.join(s for _, s in rows)
        names_component = (re.search(inv.skill_pattern(), body) or
                           re.search(r'\*\*principle-[\w-]+\*\*|references/\S+', body) or
                           any('**' + n + '**' in body for n in inv.playbooks.values()) or
                           any(re.search(r'(?<![\w.-])' + re.escape(n) + r'(?![\w.-])', body) for n in inv.scripts))
        if not names_component and not (title and title[2].startswith('(judgement)')):
            doc.fail('step-names-component', row)
    if PurePosixPath(doc.path).stem in RULES['playbook-where-table']['role_playbooks']:
        return
    where = next(((row, s) for row, s in doc.body if s.startswith('**Where you are.**')), None)
    if not where or not any(depth == 4 for _, depth, _ in doc.headings):
        return
    row, line = where
    table = []
    for next_row, text in doc.body:
        if next_row <= row:
            continue
        if text.startswith('#### '):
            break
        if text.strip():
            table.append(text)
    instruction = line.removeprefix('**Where you are.**').strip().startswith('Take the first line whose fact holds.')
    parsed = [re.fullmatch(r'- (.+) → \*\*([^*]+)\*\*\.', s) for s in table]
    if (not instruction or not parsed or not all(parsed) or any(m[2] not in titles for m in parsed if m)
            or not titles or not parsed[-1] or parsed[-1].groups() != ('Anything else', titles[0])):
        doc.fail('playbook-where-table', row)


def check_principle(doc: Document, inv: Inventory):
    if (set(doc.data) != {'name', 'description'} or doc.data.get('name') != PurePosixPath(doc.path).stem
            or not str(doc.data.get('name', '')).startswith('principle-')):
        doc.fail('principle-frontmatter', doc.marks.get('name', 1))
    description = doc.data.get('description', '')
    if not isinstance(description, str) or not re.match(r'^Apply (when|to|after|before|during|whenever)\b', description) or len(sentences(description)) < 2:
        doc.fail('principle-applies', doc.marks.get('description', 1))
    first = next(((row, s) for row, s in doc.body if s.strip()), (1, ''))
    bad = not re.fullmatch(r'#\s+\S.*', first[1])
    for row, depth, title in doc.headings:
        exempt = PurePosixPath(doc.path).stem == 'principle-prove-it-works' and depth == 2 and title == 'Script the check when you can'
        if (depth >= 2 and not exempt) or (depth == 1 and row != first[0]):
            doc.fail('principle-body', row)
    why = [row for row, s in doc.body if s.startswith('**Why:**')]
    if bad or len(why) > 1:
        doc.fail('principle-body', first[0] if bad else why[1])
    doc.match_units('principle-direction', r'scripts/|\b' + re.escape(MODE_DIR) + r'(?:#|\s+[\w-]+#)|' + inv.playbook_pattern())


def check_description(doc: Document, inv: Inventory):
    description = doc.data.get('description', '')
    row = doc.marks.get('description', 1)
    parts = sentences(description) if isinstance(description, str) else []
    exclusions = [s for s in parts if s.text.startswith(('Not for', 'Do not use'))]
    if (not parts or not any(s.text.startswith('Use ') for s in parts) or len(parts) > 3 or len(exclusions) > 1
            or len(description) > 1024):
        doc.fail('description-trigger', row)
    if isinstance(description, str):
        names = inv.skill_pattern(str(doc.data.get('name', '')), path_segment=True)
        rest = r'references/|scripts/|SKILL\.md|' + inv.playbook_pattern() + r'|\bstep\s+\d+'
        if m := re.search(names + r'|(?i:' + rest + r')', description):
            doc.fail('description-content', row, m.group())


def check_capability(doc: Document, inv: Inventory):
    if PurePosixPath(doc.path).name == 'SKILL.md':
        name = doc.data.get('name')
        if not isinstance(name, str) or name != PurePosixPath(doc.path).parent.name or len(name) > 64:
            doc.fail('skill-name', doc.marks.get('name', 1))
        check_description(doc, inv)
    for row, depth, title in doc.headings:
        if depth == 2 and title in ('Next', 'Reached from here'):
            doc.fail('capability-next-step', row)
    skill = inv.skill_pattern()
    target = r'(?:the\s+)?`?' + skill + r'`?'
    routing = re.compile(r'\b(?:return to|hand (?:it )?(?:over|on) to)\s+' + target +
                         r'(?:\s+skill)?|\bgoes through\s+' + target +
                         r'\s+skill\s+first\b|\bare steps of\s+' + target + r'\s+skill', re.I)
    doc.match_units('capability-next-step', routing)
    for unit in doc.units:
        if unit.kind == 'sentence' and re.search(skill, unit.text) and (m := re.search(r'\bnext step\b', unit.text, re.I)):
            doc.fail('capability-next-step', unit.text_lines[m.start()] if unit.text_lines else unit.line, m.group())
    doc.match_units('capability-playbook-name', inv.playbook_pattern())


def check_own_prose(doc: Document, inv: Inventory):
    hosts = re.compile(r'(?<![\w.-])(?:Claude Code|Codex|Grok|Cursor|Orca|herdr|Paseo|the Skill tool|the Task tool)(?![\w.-])', re.I)
    # Preserve offsets while masking inline code and link targets, not link labels.
    for row, raw in doc.body:
        masked = re.sub(r'(`+).*?\1|(?<=\]\()[^)]*(?=\))', lambda m: ' ' * len(m.group()), raw)
        for m in hosts.finditer(masked):
            doc.fail('host-name', row, raw[m.start():m.end()])
    numbered = re.compile(r'\bclosing step\s+\d+|\bPhase\s+[A-Z]\b|\bstep\s+\d+|##\s+\d+|\brules?\s+\d+(?:\s+and\s+\d+)?', re.I)
    own = PurePosixPath(doc.path).name
    own_skill = doc.path.split('/')[2] if doc.path.startswith('mmw-v2/skills/') and own == 'SKILL.md' else ''
    file_source = r'(?P<file>[\w./-]+\.(?:md|py|sh))'
    skill_source = inv.skill_pattern(own_skill)
    source = r'(?:' + file_source + '|' + skill_source + r'(?:`?\s+skill)?)'
    before = re.compile(source + r"`?(?:['’]s)?\s+`?$", re.I)
    after = re.compile(r'^\s+of\s+(?:the\s+)?`?' + source, re.I)
    for unit in doc.units:
        if unit.kind != 'sentence':
            continue
        for m in numbered.finditer(unit.text):
            if re.match(r'closing step|Phase', m.group(), re.I):
                cross = True
            else:
                # A source modifies its step/heading, or follows "rules N of".
                # Merely mentioning a command, output file or destination in the
                # same sentence does not change a reference to this file's steps.
                named = before.search(unit.text[:m.start()])
                if not named and re.match(r'rules?\b', m.group(), re.I):
                    named = after.match(unit.text[m.end():])
                cross = bool(named and named['file'] != own)
            if re.fullmatch(r'rules?\s+\d+(?:\s+and\s+\d+)?', m.group(), re.I) and re.search(r'`(?:[^`]+/)?shared\.md`\s*$', unit.text[:m.start()]):
                continue
            if cross:
                row = unit.text_lines[m.start()] if unit.text_lines else unit.line
                doc.fail('numbered-cross-reference', row, m.group())


def check_document(doc: Document, component, inv: Inventory):
    if component.structure_exempt or component.imported and component.kind == 'mode-reference':
        return []
    if component.kind == 'mode':
        check_mode(doc)
        check_description(doc, inv)
    elif component.kind == 'playbook':
        check_playbook(doc, component.imported, inv)
        if component.imported:
            return doc.findings
    elif component.kind == 'principle':
        check_principle(doc, inv)
    elif component.kind == 'capability':
        check_capability(doc, inv)
    if not component.imported:
        check_own_prose(doc, inv)
    if component.kind in ('mode', 'playbook', 'principle', 'mode-reference'):
        for row, raw in enumerate(doc.lines, 1):
            if row not in doc.hidden:
                for m in re.finditer('[\u2013\u2014]', raw):
                    doc.fail('no-dash', row, m.group())
    return doc.findings


EXCEPTION_PATH = 'mmw-v2/tests/lib/structure-exceptions.tsv'
EXCEPTION_FIELDS = ['path', 'rule', 'excerpt', 'until', 'reason']


@dataclass(frozen=True)
class ExceptionRow(FindingKey):
    until: str
    reason: str


def read_tsv(file: Path, fields: list[str]):
    with file.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader((line for line in stream if not line.lstrip().startswith('#') and line.strip()), delimiter='\t')
        if reader.fieldnames is None or any(f not in reader.fieldnames for f in fields):
            raise TextError(f'{file}: expected tab-separated columns {", ".join(fields)}')
        for row in reader:
            if None in row or any(row[f] is None for f in fields):
                raise TextError(f'{file}:{reader.line_num}: malformed tab-separated row')
            yield row


def path_renames(root: Path):
    edges = {}
    for file in sorted((root / 'docs/specs').glob('*/renames.tsv')):
        for row in read_tsv(file, ['kind', 'old', 'new']):
            if row['kind'] == 'path':
                if row['old'] in edges and edges[row['old']] != row['new']:
                    raise TextError(f'{file}: conflicting path rename for {row["old"]}')
                edges[row['old']] = row['new']
    return edges


def renamed_path(root: Path, path: str, edges):
    seen = set()
    while not (root / path).exists() and path in edges:
        if path in seen:
            raise TextError(f'path rename cycle at {path}')
        seen.add(path)
        path = edges[path]
    return path


def read_exceptions(root: Path):
    file = root / EXCEPTION_PATH
    if not file.exists():
        return []
    edges = path_renames(root)
    rows = []
    for row in read_tsv(file, EXCEPTION_FIELDS):
        if row['rule'] not in RULES or not row['path'] or not re.fullmatch(r'B\d+|permanent', row['until']):
            raise TextError(f'{file}: invalid exception rule, path or until: {row}')
        if row['until'] == 'permanent' and not row['reason'].strip():
            raise TextError(f'{file}: permanent exception for {row["path"]} needs a reason')
        rows.append(ExceptionRow(renamed_path(root, row['path'], edges), row['rule'], row['excerpt'], row['until'], row['reason']))
    return rows


def apply_exceptions(findings: list[Finding], rows: list[ExceptionRow], batch: str | None):
    available = list(rows)
    remaining = []
    used = 0
    for finding in findings:
        match = next((i for i, row in enumerate(available)
                      if row.key == finding.key), None)
        if match is None:
            remaining.append(finding)
            continue
        row = available.pop(match)
        used += 1
        if batch and row.until != 'permanent' and int(row.until[1:]) <= int(batch[1:]):
            remaining.append(finding)
    return remaining, used, available


def debt_assignment(finding: Finding):
    """Bootstrap assignments from R21 §4.3, then R18 §10, then #602's fallback."""
    r18 = 'docs/research/workflow-compare/reports/R18-mmw-architecture-v2.md'
    r21 = 'docs/research/workflow-compare/reports/R21-text-integrity-checks.md'
    path, rule = finding.path.removeprefix('mmw-v2/skills/'), finding.rule
    if path == 'design-pages/references/edit-pages.md' and rule == 'host-name':
        return 'permanent', r21 + ' §4.3: Claude Design 按钮上的字，照录。'
    if rule == 'capability-next-step' and path.startswith(('write-screen-contract/', 'design-pages/')):
        return 'B1', r21 + ' §4.3; ' + r18 + ' §4.1: 下一步进 P3/P1，§10 B1 搬白天 playbook。'
    b1_numbered_paths = {'design-pages/SKILL.md', 'code-checkers/references/git-hooks.md',
                         'code-checkers/references/python.md', 'exe-release/references/driving.md',
                         'exe-release/references/key.md'}
    if rule == 'numbered-cross-reference' and path in b1_numbered_paths:
        return 'B1', r21 + ' §4.3; ' + r18 + ' §4.1, §10 B1: 白天步骤与 reference 改名时改编号引用。'
    if path.startswith(('verify-ticket/', 'dispatch/', 'retro/', 'advisor/', 'ui-acceptance/', 'exe-release/SKILL.md')):
        return 'B2', r18 + ' §10 B2 票 a: 夜间流程与能力技能剥离。'
    if path.startswith('design-pages/'):
        return 'B2', r18 + ' §10 B2 票 a: design-pages 剥离。'
    return 'B2', 'R18 未排批次，取本次改造的最后一批（#602 What to build 6）。'


def write_exceptions(root: Path, findings: list[Finding]):
    file = root / EXCEPTION_PATH
    file.parent.mkdir(parents=True, exist_ok=True)
    # Replace a complete table, never leave a partially written register.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=file.parent, delete=False) as stream:
        temporary = Path(stream.name)
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(EXCEPTION_FIELDS)
        for finding in findings:
            until, reason = debt_assignment(finding)
            writer.writerow([finding.path, finding.rule, finding.excerpt, until, reason])
    try:
        temporary.replace(file)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--no-exceptions', action='store_true')
    parser.add_argument('--batch', type=str, help='fail exceptions expiring at or before Bn')
    parser.add_argument('--write-exceptions', action='store_true', help='bootstrap a complete table from all current findings')
    args = parser.parse_args()
    try:
        args.root = args.root.resolve()
        if args.batch and not re.fullmatch(r'B\d+', args.batch):
            raise TextError('--batch must be B followed by an integer')
        if args.write_exceptions and args.files:
            raise TextError('--write-exceptions requires a whole-tree run')
        (args.root / 'mmw-v2/skills.txt').read_text(encoding='utf-8')
        imports = read_imports(args.root)
        inv = inventory(args.root, imports)
        paths = args.files or [str(p.relative_to(args.root)) for directory in
                               ('mmw-v2/skills', '.mmw/playbooks')
                               for p in (args.root / directory).rglob('*.md')]
        paths = [str((args.root / p).resolve().relative_to(args.root)) for p in paths]
        paths = sorted(set(p for p in paths if classify(p, imports).kind not in ('other', 'upstream')))
        findings = []
        for path in paths:
            findings.extend(check_document(Document(path, (args.root / path).read_text(encoding='utf-8')),
                                           classify(path, imports), inv))
        used, stale = 0, []
        if args.write_exceptions and paths:
            write_exceptions(args.root, findings)
            print(f'EXCEPTIONS WROTE {len(findings)} rows to {EXCEPTION_PATH}')
        if not args.no_exceptions or args.write_exceptions:
            rows = read_exceptions(args.root)
            if args.files:
                rows = [r for r in rows if r.path in paths]
            findings, used, stale = apply_exceptions(findings, rows, args.batch)
        failed = not paths or bool(findings)
        if failed:
            print(f'STRUCTURE FAILED: {len(findings)} findings in {len(paths)} files')
            print('Next: fix the named component; if a rule does not apply, open a decision child, do not edit the exception table.')
            print('Why: component structure and routing direction must hold; checking nothing cannot establish them.')
            for finding in findings:
                print(finding.render())
        for row in stale:
            print(f'WARN stale exception {row.path}: {row.rule} | {row.excerpt}')
        if failed:
            return 1
        print(f'STRUCTURE OK {len(paths)} files ({used} exceptions in use, {len(stale)} stale)')
        return 0
    except (OSError, TextError, UnicodeError, ValueError) as exc:
        if isinstance(exc, TextError):
            next_step = exc.next_step or 'correct the reported component path, TSV row or command option and rerun.'
        elif isinstance(exc, OSError):
            next_step = f'restore read access to {exc.filename or args.root} and rerun.'
        elif isinstance(exc, UnicodeError):
            next_step = f'correct the UTF-8 encoding of the component or TSV file under {args.root} and rerun.'
        else:
            next_step = f'give component paths inside {args.root} and rerun.'
        print(f'STRUCTURE UNCHECKED: {exc}\nNext: {next_step}\nWhy: the checker could not read its inputs.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
