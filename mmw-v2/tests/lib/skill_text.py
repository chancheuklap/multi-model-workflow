#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Markdown units, locations and component paths shared by the text checks.

All line numbers are one-based source addresses, including sentences spanning
lines. GitTree reads committed snapshots, never the checker's working files.
"""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess

import yaml

MODE_DIR = 'mmw'
MODE_ROOT = f'mmw-v2/skills/{MODE_DIR}'


class TextError(ValueError):
    """A snapshot or location could not be read unambiguously."""

    def __init__(self, message: str, next_step: str | None = None):
        super().__init__(message)
        self.next_step = next_step


class LocationMissing(TextError):
    """The heading or frontmatter field a location names is not in the text."""


@dataclass(frozen=True)
class Unit:
    kind: str
    text: str
    line: int
    end_line: int
    key: str = ''
    text_lines: tuple[int, ...] = ()

    @property
    def identity(self):
        return self.kind, self.key, self.text


@dataclass(frozen=True)
class Anchor:
    title: str
    start: int
    end: int


@dataclass(frozen=True)
class Location:
    path: str
    selector: str = ''
    value: str = ''
    revision: str | None = None

    @property
    def whole(self):
        return not self.selector


@dataclass
class Selection:
    units: list[Unit]


def normalize_title(text: str) -> str:
    text = text.strip()
    if text.startswith('**') and text.endswith('**'):
        text = text[2:-2]
    text = re.sub(r'^\s*\d+[.)]\s+', '', text)
    return re.sub(r'\s+', ' ', text).rstrip('.:').strip()


# These forms protect punctuation from sentence splitting, not from comparison.
INLINE = re.compile(r'(`+)[^\n]*?\1|\[[^\]\n]*\]\([^\n)]*\)')
ABBREVIATION = re.compile(r'\b(?:e\.g\.|i\.e\.|etc\.|vs\.|cf\.)', re.I)
SENTENCE_END = re.compile(r'[.?!。](?=\s*[A-Z`*(\[0-9\u3400-\u9fff])')
LIST = re.compile(r'^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$')
HEADING = re.compile(r'^\s{0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$')
BOLD_TITLE = re.compile(r'^\*\*([^*]+[.:?])\*\*(?:\s+|$)(.*)$')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})(.*)$')


def closes_fence(line: str, marker: str) -> bool:
    return bool(re.fullmatch(r'\s*' + re.escape(marker[0]) + '{' + str(len(marker)) + r',}\s*', line))


def sentences(text: str, line: int = 1, line_map: list[int] | None = None) -> list[Unit]:
    """Split prose symmetrically, retaining the line at each sentence's start."""
    protected = list(text)
    for pattern in (INLINE, ABBREVIATION):
        for match in pattern.finditer(text):
            protected[match.start():match.end()] = 'x' * len(match.group())
    mask = ''.join(protected)
    ends = [m.end() for m in SENTENCE_END.finditer(mask)] + [len(text)]
    result = []
    start = 0
    for end in ends:
        raw = text[start:end]
        stripped = raw.strip()
        if stripped:
            first = start + len(raw) - len(raw.lstrip())
            last = end - len(raw) + len(raw.rstrip()) - 1
            normalized = ''
            rows = []
            for match in re.finditer(r'\S+|\s+', stripped):
                value = ' ' if match.group().isspace() else match.group()
                normalized += value
                if line_map:
                    rows.extend(line_map[first + match.start():first + match.end()]
                                if value != ' ' else [line_map[first + match.start()]])
                else:
                    rows.extend([line] * len(value))
            result.append(Unit('sentence', normalized,
                               line_map[first] if line_map else line,
                               line_map[last] if line_map else line,
                               text_lines=tuple(rows)))
        start = end
    return result


def frontmatter(text: str) -> tuple[dict, int, dict[str, int]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}, 0, {}
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
    if end is None:
        raise TextError('frontmatter has no closing ---')
    block = '\n'.join(lines[1:end])
    try:
        data = yaml.safe_load(block) or {}
        node = yaml.compose(block)
    except yaml.YAMLError as exc:
        raise TextError(f'frontmatter is not YAML: {exc}') from exc
    if not isinstance(data, dict):
        raise TextError('frontmatter is not a mapping')
    marks = {str(k.value): k.start_mark.line + 2 for k, _ in node.value} if node else {}
    return data, end + 1, marks


def prose_mask(text: str) -> str:
    """Hide metadata, fenced code and comments without moving source addresses."""
    masked = list(text)

    def hide(start, end):
        masked[start:end] = [' ' if c not in '\r\n' else c for c in text[start:end]]

    _, end, _ = frontmatter(text)
    hide(0, sum(len(line) for line in text.splitlines(keepends=True)[:end]))
    marker = None
    in_comment = False
    offset = 0
    for line in ''.join(masked).splitlines(keepends=True):
        fence = FENCE.match(line)
        if marker:
            hide(offset, offset + len(line))
            if closes_fence(line, marker):
                marker = None
        elif fence and not in_comment:
            marker = fence.group(1)
            hide(offset, offset + len(line))
        else:
            position = 0
            while position < len(line):
                start = position if in_comment else line.find('<!--', position)
                if start == -1:
                    break
                end = line.find('-->', start if in_comment else start + 4)
                in_comment = end == -1
                position = len(line) if in_comment else end + 3
                hide(offset + start, offset + position)
        offset += len(line)
    return ''.join(masked)


@dataclass(frozen=True)
class SkillMention:
    name: str
    line: int
    offset: int
    form: str

    @property
    def by_model(self) -> bool:
        return self.form != 'slash'


QUALIFIED_SKILL = re.compile(
    r"(?<![\w-])(?:the|The)\s+"
    r"(?:`([^`\n]+)`|([a-z][\w-]*))\s+skill(?![\w-])")
CODE_SPAN = re.compile(r'(?<!`)(`+)(?!`)([^\n]*?)(?<!`)\1(?!`)')


def _qualified_skills(masked: str, names):
    """Yield prose matches and their skill names, excluding inline examples."""
    code_spans = [(match.start(), match.end()) for match in CODE_SPAN.finditer(masked)]
    for match in QUALIFIED_SKILL.finditer(masked):
        if any(start <= match.start() < end for start, end in code_spans):
            continue
        name = match[1] or match[2]
        if match[1] or name in names:
            yield match, name


def skill_mentions(text: str, names, steps: bool = True) -> list[SkillMention]:
    """Recognize skill names in invocation prose, retaining the written form."""
    masked = prose_mask(text)
    result = []
    qualified = []
    for match, name in _qualified_skills(masked, names):
        qualified.append((match.start(), match.end()))
        result.append(SkillMention(name, masked.count('\n', 0, match.start()) + 1,
                                   match.start(), 'qualified'))
    offset = 0
    step_indent = None
    for line_number, line in enumerate(masked.splitlines(keepends=True), 1):
        step = re.match(r'^(\s*)\d+\.\s+\*\*[^*\n]+\.\*\*(?:\s|$)', line)
        if steps and step:
            step_indent = len(step[1])
        elif line.strip() and step_indent is not None:
            if len(line) - len(line.lstrip()) <= step_indent:
                step_indent = None
        route = re.match(r'^\s*-\s+.*?→', line)
        for match in CODE_SPAN.finditer(line):
            position = offset + match.start()
            if any(start <= position < end for start, end in qualified):
                continue
            value = match[2]
            if re.fullmatch(r'/[^\s/]+', value):
                name, form = value[1:], 'slash'
            elif value in names and route and match.start() >= route.end():
                name, form = value, 'route'
            elif value in names and steps and step_indent is not None:
                name, form = value, 'step'
            else:
                continue
            result.append(SkillMention(name, line_number, position, form))
        offset += len(line)
    return sorted(result, key=lambda mention: mention.offset)


def skill_of_path(text: str, offset: int, names, *, already_masked: bool = False) -> str | None:
    """Resolve a path's explicit skill owner or its same-line skill antecedent."""
    masked = text if already_masked else prose_mask(text)
    prefix = masked[:offset]
    for match, name in _qualified_skills(masked, names):
        if match.end() > offset:
            break
        if re.fullmatch(r"'s\s*`?", prefix[match.end():]):
            return name
    prefix = prefix[prefix.rfind('\n') + 1:]
    reference = re.search(r"\bthat skill's\s*`?$", prefix)
    if reference is None:
        return None
    antecedent = prefix[:reference.start()]
    candidates = [(mention.offset, mention.name)
                  for mention in skill_mentions(antecedent, names) if mention.by_model]
    candidates.extend((match.start(), match[2]) for match in CODE_SPAN.finditer(antecedent)
                      if match[2] in names)
    return max(candidates)[1] if candidates else None


def markdown_units(text: str, first_line: int = 1) -> list[Unit]:
    lines = text.splitlines(keepends=True)
    result = []
    data, start, marks = frontmatter(text)
    for key, value in data.items():
        row = first_line + marks[str(key)] - 1
        if key == 'description' and isinstance(value, str):
            result.extend(Unit(u.kind, u.text, u.line, u.end_line, str(key), u.text_lines)
                          for u in sentences(value, row))
        else:
            result.append(Unit('field', json.dumps(value, ensure_ascii=False, sort_keys=True),
                               row, row, str(key)))
    buffer: list[tuple[str, int]] = []

    def flush():
        if not buffer:
            return
        combined = ''
        mapping = []
        for part, row in buffer:
            if combined:
                combined += ' '
                mapping.append(row)
            combined += part
            mapping.extend([row] * len(part))
        result.extend(sentences(combined, line_map=mapping))
        buffer.clear()

    i = start
    while i < len(lines):
        raw = lines[i]
        row = first_line + i
        stripped = raw.strip()
        fence = FENCE.match(raw)
        if fence:
            flush()
            j = i + 1
            marker = fence.group(1)
            while j < len(lines):
                if closes_fence(lines[j], marker):
                    j += 1
                    break
                j += 1
            result.append(Unit('code', ''.join(lines[i:j]), row, first_line + j - 1,
                               text_lines=tuple(r for k in range(i, j)
                                                for r in [first_line + k] * len(lines[k]))))
            i = j
            continue
        if stripped.startswith('<!--'):
            flush()
            j = i + 1
            while '-->' not in ''.join(lines[i:j]) and j < len(lines):
                j += 1
            result.append(Unit('html', ''.join(lines[i:j]).rstrip('\r\n'), row, first_line + j - 1))
            i = j
            continue
        if re.fullmatch(r'</?[\w-]+(?:\s+[^<>]*)?>', stripped):
            flush()
            result.append(Unit('html', stripped, row, row))
            i += 1
            continue
        heading = HEADING.match(raw)
        if heading:
            flush()
            result.append(Unit('title', normalize_title(heading.group(2)), row, row))
            i += 1
            continue
        if not stripped:
            flush()
            i += 1
            continue
        content = re.sub(r'^\s*(?:>\s*)+', '', raw.rstrip('\r\n'))
        item = LIST.match(content)
        if item:
            flush()
            content = item.group(2)
        content = content.strip()
        bold = BOLD_TITLE.match(content)
        if bold:
            flush()
            result.append(Unit('title', normalize_title(bold.group(1)), row, row))
            content = bold.group(2)
        if '|' in content and (content.startswith('|') or re.search(r'\s\|\s', content)):
            flush()
            cells = re.split(r'(?<!\\)\|', content.strip('|'))
            if not all(re.fullmatch(r'\s*:?-+:?\s*', c) for c in cells):
                for cell in cells:
                    result.extend(sentences(cell, row))
        elif content:
            buffer.append((content, row))
        i += 1
    flush()
    return result


def anchors(text: str) -> list[Anchor]:
    """Heading sections, list steps, and bold-labelled paragraph scopes."""
    lines = text.splitlines()
    starts = []
    in_fence = None
    in_comment = False
    _, frontmatter_end, _ = frontmatter(text)
    for i in range(frontmatter_end, len(lines)):
        line = lines[i]
        if in_comment:
            in_comment = '-->' not in line
            continue
        if line.strip().startswith('<!--'):
            in_comment = '-->' not in line
            continue
        fence = FENCE.match(line)
        if in_fence:
            if closes_fence(line, in_fence):
                in_fence = None
            continue
        if fence:
            in_fence = fence.group(1)
            continue
        h = HEADING.match(line)
        if h:
            starts.append((normalize_title(h.group(2)), i, 'heading', len(h.group(1))))
            continue
        item = LIST.match(line)
        bold = BOLD_TITLE.match(item.group(2) if item else line.strip())
        if bold:
            starts.append((normalize_title(bold.group(1)), i,
                           'step' if item else 'bold', len(item.group(1)) if item else 0))
    result = []
    for title, start, kind, level in starts:
        end = len(lines)
        for _, j, next_kind, next_level in starts:
            if j <= start:
                continue
            if kind == 'heading' and next_kind == 'heading' and next_level <= level:
                end = j
                break
            if kind == 'bold' and (next_kind == 'heading' or next_kind == 'bold'):
                end = j
                break
        if kind == 'step':
            for j in range(start + 1, len(lines)):
                if not lines[j].strip():
                    continue
                indent = len(lines[j]) - len(lines[j].lstrip())
                if indent <= level:
                    end = j
                    break
        result.append(Anchor(title, start + 1, end))
    return result


def parse_location(raw: str, source: bool = False) -> Location:
    revision = None
    # A revision prefix is distinct from :L<n> line selectors.
    match = re.match(r'^([^:#@]+):(.+)$', raw)
    if source and match and not re.match(r'^L\d', match.group(2)):
        revision, raw = match.groups()
    selector = value = ''
    if '#' in raw:
        raw, value = raw.split('#', 1)
        selector = 'heading'
    elif '@' in raw:
        raw, value = raw.rsplit('@', 1)
        selector = 'field'
    elif ':L' in raw:
        raw, value = raw.rsplit(':L', 1)
        selector = 'lines'
        if not source or not re.fullmatch(r'\d+(?:-(?:L)?\d+)?', value):
            raise TextError('line ranges are source-only: ' + raw)
    if not raw or raw.startswith('/') or '..' in PurePosixPath(raw).parts or (selector and not value):
        raise TextError('invalid location: ' + raw)
    return Location(raw, selector, value, revision)


def select(text: str, location: Location) -> Selection:
    if location.whole:
        return Selection(markdown_units(text))
    if location.selector == 'field':
        data, _, _ = frontmatter(text)
        if location.value not in data:
            raise LocationMissing(f'{location.path}@{location.value}: field not found')
        units = [u for u in markdown_units(text) if u.key == location.value]
        return Selection(units)
    if location.selector == 'heading':
        hits = [a for a in anchors(text) if a.title == normalize_title(location.value)]
        if len(hits) != 1:
            error = TextError if hits else LocationMissing
            raise error(f'{location.path}#{location.value}: matched {len(hits)} locations')
        start, end = hits[0].start, hits[0].end
    else:
        bounds = re.split(r'-(?:L)?', location.value)
        start, end = int(bounds[0]), int(bounds[-1])
        if start < 1 or end < start or end > len(text.splitlines()):
            raise TextError(f'{location.path}:L{location.value}: line range not found')
    fragment = ''.join(text.splitlines(keepends=True)[start-1:end])
    return Selection(markdown_units(fragment, start))


class GitTree:
    def __init__(self, root: Path, revision: str, trees: dict | None = None):
        self.root = root
        self.revision = self.git('rev-parse', '--verify', revision + '^{commit}').strip()
        self._texts: dict[str, str | None] = {}
        self._trees = {} if trees is None else trees
        self._trees[revision] = self._trees[self.revision] = self

    def at_revision(self, revision: str) -> GitTree:
        if revision not in self._trees:
            GitTree(self.root, revision, self._trees)
        return self._trees[revision]

    def git(self, *args: str) -> str:
        result = subprocess.run(['git', '-C', str(self.root), *args],
                                capture_output=True, text=True)
        if result.returncode:
            raise TextError(f'git {" ".join(args)}: {result.stderr.strip()}')
        return result.stdout

    def exists(self, path: str) -> bool:
        if path not in self._texts:
            result = subprocess.run(['git', '-C', str(self.root), 'show',
                                     f'{self.revision}:{path}'], capture_output=True)
            self._texts[path] = result.stdout.decode('utf-8') if result.returncode == 0 else None
        return self._texts[path] is not None

    def read(self, path: str) -> str:
        if not self.exists(path):
            raise TextError(f'{path}: file not found at {self.revision}')
        return self._texts[path]  # type: ignore[return-value]

    def selection(self, location: Location) -> Selection:
        tree = self.at_revision(location.revision) if location.revision else self
        return select(tree.read(location.path), location)


def installed_skills(root: Path | GitTree) -> dict[str, str]:
    if isinstance(root, GitTree):
        if not root.exists('mmw-v2/skills.txt'):
            return {}
        text = root.read('mmw-v2/skills.txt')
    else:
        file = root / 'mmw-v2/skills.txt'
        if not file.exists():
            return {}
        text = file.read_text(encoding='utf-8')
    result = {}
    for raw in text.splitlines():
        entry = raw.strip()
        if not entry or entry.startswith('#'):
            continue
        entry = entry.split()[0]
        if entry.startswith('self/'):
            path = 'mmw-v2/skills/' + entry[5:]
        elif entry.startswith('dd/'):
            path = 'mmw-v2/upstream-diagram-design/skills/' + entry[3:]
        elif entry.startswith('pstack/'):
            path = 'mmw-v2/upstream-pstack/skills/' + entry[len('pstack/'):]
        else:
            path = 'mmw-v2/upstream/skills/' + entry
        result[PurePosixPath(path).name] = path
    return result


@dataclass(frozen=True)
class Component:
    kind: str
    imported: bool = False
    structure_exempt: bool = False


def read_imports(root: Path) -> dict[str, Component]:
    file = root / MODE_ROOT / 'imports.tsv'
    if not file.exists():
        return {}
    result = {}
    header = True
    for line, raw in enumerate(file.read_text(encoding='utf-8').splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        cols = raw.split('\t')
        if len(cols) < 2:
            raise TextError(f'{file}:{line}: imports.tsv needs at least two columns',
                            f'correct the tab-separated type and local path at {file}:{line} and rerun.')
        if header:
            header = False
            continue
        kind, path = cols[:2]
        judgment = cols[5] if len(cols) > 5 else ''
        result[path] = Component(kind, True, kind == 'playbook' and
                                 bool(re.search(r'\bstructure-exempt\b', judgment)))
    return result


def classify(path: str, imports: dict[str, Component] | None = None) -> Component:
    if re.match(r'mmw-v2/upstream[^/]*/', path):
        return Component('upstream', True)
    if imports and path in imports:
        return imports[path]
    if path == MODE_ROOT + '/SKILL.md':
        return Component('mode')
    if re.fullmatch(re.escape(MODE_ROOT) + r'/playbooks/[^/]+\.md', path):
        return Component('playbook')
    if re.fullmatch(r'\.mmw/playbooks/[^/]+\.md', path) and PurePosixPath(path).name != 'INDEX.md':
        return Component('playbook')
    if re.fullmatch(re.escape(MODE_ROOT) + r'/principles/principle-[^/]+\.md', path):
        return Component('principle')
    if path.startswith(MODE_ROOT + '/references/'):
        return Component('mode-reference')
    if re.fullmatch(r'mmw-v2/skills/[^/]+/(?:SKILL\.md|references/.+\.md)', path):
        return Component('capability')
    return Component('other')


def component_root(path: str) -> str:
    if path.startswith(MODE_ROOT + '/'):
        return MODE_ROOT
    match = re.match(r'(mmw-v2/(?:skills|upstream[^/]*/skills)/(?:(?:engineering|productivity)/)?[^/]+)', path)
    return match.group(1) if match else str(PurePosixPath(path).parent)


@dataclass(frozen=True)
class Rename:
    kind: str
    old: str
    new: str
    scope: str | None = None

    def applies(self, target: str) -> bool:
        return not self.scope or fnmatchcase(target, self.scope)


def rename_text(text: str, kind: str, renames: list[Rename], target: str) -> str:
    for rule in renames:
        if rule.kind == 'path' or not rule.applies(target):
            continue
        edge = r'\w.\-' if rule.kind == 'token' else r'\w\-'
        pattern = re.compile(r'(?<![' + edge + '])' + re.escape(rule.old) + r'(?![' + edge + '])')
        if rule.kind == 'text' or kind == 'code':
            text = pattern.sub(lambda _: rule.new, text)
        elif rule.kind == 'token':
            text = re.sub(r'(`+)(.*?)\1', lambda m: m.group(1) + pattern.sub(lambda _: rule.new, m.group(2)) + m.group(1), text)
    return text


# The three ways skill text writes a path: a skill-qualified path, a Markdown
# link, and inline code. REFERENCE matches any of them, the skill-qualified form
# first because it contains inline code.
NAMED_REFERENCE = re.compile(r"the `([^`]+)` skill's `([^`]+)`")
LINK_REFERENCE = re.compile(r'\[([^\]]*)\]\(([^\s)]+)\)')
CODE_REFERENCE = re.compile(r'`([^`\n]+)`')
REFERENCE = re.compile('|'.join(
    p.pattern for p in (NAMED_REFERENCE, LINK_REFERENCE, CODE_REFERENCE)))


def canonical_text(unit: Unit, tree: GitTree, path: str, target: str,
                   renames: list[Rename], source: bool = False,
                   head: GitTree | None = None) -> str:
    """Canonicalize only the explicitly permitted mechanical differences."""
    text = unit.text
    if unit.kind == 'code':
        return rename_text(text, unit.kind, renames, target) if source else text
    citation = re.compile(r'\s*\(\*\*principle-[\w-]+\*\*(?:,\s*\*\*principle-[\w-]+\*\*)*\)')

    def cite(match):
        names = re.findall(r'\*\*(principle-[\w-]+)\*\*', match.group())
        current = head or tree.at_revision('HEAD')
        return '' if all(current.exists(f'{MODE_ROOT}/principles/{n}.md') for n in names) else match.group()

    text = citation.sub(cite, text)

    def resolve(value: str, base: str, literal: str):
        value = value.split('#', 1)[0]
        resolved = posixpath.normpath(posixpath.join(base, value))
        if resolved.startswith('../') or not tree.exists(resolved):
            return literal
        for rule in renames if source else []:
            if rule.kind == 'path' and resolved == rule.old:
                resolved = rule.new
        return '\x00path:' + resolved + '\x00'

    # Resolve skill-qualified paths before standalone inline-code paths.
    skills = installed_skills(tree)
    text = NAMED_REFERENCE.sub(lambda m: resolve(m.group(2), skills.get(m.group(1), 'mmw-v2/skills/' + m.group(1)), m.group()), text)
    def link(m):
        resolved = resolve(m.group(2), str(PurePosixPath(path).parent), m.group())
        return '\x00label:' + m.group(1) + '\x00' + resolved if resolved.startswith('\x00path:') else resolved
    text = LINK_REFERENCE.sub(link, text)
    def code_path(m):
        value = m.group(1)
        if '/' not in value:
            return m.group()
        base = '' if value.startswith(('mmw-v2/', '.mmw/')) else component_root(path)
        return resolve(value, base, m.group())
    text = CODE_REFERENCE.sub(code_path, text)
    if source:
        # Resolved paths use path renames only; token/text rules apply to the
        # remaining literal text, after resolution against the source snapshot.
        pieces = re.split(r'(\x00path:[^\x00]*\x00)', text)
        text = ''.join(piece if piece.startswith('\x00path:') else
                       rename_text(piece, unit.kind, renames, target)
                       for piece in pieces)
    return re.sub(r'\s+', ' ', text).strip()
