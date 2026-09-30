#!/usr/bin/env python3
"""Import pstack components through their public command-line interface.

Mechanical patterns: principles drop the disable-model-invocation frontmatter
line and change ../principle-x/SKILL.md to principle-x.md; playbooks change
../references/X to ../references/pstack/X and scripts/X to scripts/pstack/X.
Skills register pstack/<name>, with +model-invoked when mode or playbooks name
them. Triggers and sections copy verbatim; references and scripts copy verbatim
(scripts include same-directory imports/source files); agent frontmatter keeps
only name and description. Principle indexes come from H1 and description.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

TYPES = ('playbook', 'principle', 'skill', 'mode-trigger', 'mode-section',
         'mode-reference', 'mode-script', 'agent')
IMPORT_HEADER = 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch'
REWRITE_HEADER = 'kind\told\tnew\tscope'
SUBTREE = Path('mmw-v2/upstream-pstack')
CHECKOUT = Path(__file__).resolve().parents[1]
# Same boundary as skill_text.SENTENCE_END; it does not require loading PyYAML.
SENTENCE_END = re.compile(r'[.?!。](?=\s*[A-Z`*(\[0-9\u3400-\u9fff])')
# (R18 section 8.3 first-column literal, keyword, scan pattern).
SLOT_KEYWORDS = (
    ('control 槽位（「the matching control skill」、`control-ui`、`control-cli`）', 'control skill', r'\bcontrol skill\b'),
    ('delivery 槽位（「Run **Opening a PR**」）', 'Opening a PR', r'\bOpening a PR\b'),
    ('forge 槽位（`gh`、`command -v origin`、`gt`）', 'gh', r'\bgh\b'),
    ('forge 槽位（`gh`、`command -v origin`、`gt`）', 'origin', r'\borigin\b'),
    ('forge 槽位（`gh`、`command -v origin`、`gt`）', 'gt', r'\bgt\b'),
    ('`subagent_type: "poteto-agent"` / `generalPurpose`', 'subagent_type', r'\bsubagent_type\b'),
    ('「your configured <label> model (default …)」；`~/.cursor/rules/pstack-models.mdc` 的 `<label>` 行',
     'configured … model', r'\bconfigured\b[^\n.!?]*?\bmodel\b'),
    ('「your configured <label> model (default …)」；`~/.cursor/rules/pstack-models.mdc` 的 `<label>` 行',
     'pstack-models.mdc', r'\bpstack-models\.mdc\b'),
    ('`AskQuestion`', 'AskQuestion', r'\bAskQuestion\b'),
    ("Cursor's `/loop`、`/goal`", '/loop', r'/loop\b'),
    ("Cursor's `/loop`、`/goal`", '/goal', r'/goal\b'),
    ('cloud agent', 'cloud', r'\bcloud\b'),
    ('`agent-transcripts/`、`~/.cursor/projects/`', 'agent-transcripts', r'\bagent-transcripts\b'),
    ('运行中从 trunk 重读 playbook（`autopilot-full.md` 第 6 步、`multi-phase-plan.md` 模板）',
     'git show origin/main:', r'git show origin/main:'),
    ('「Spawn Comment Sicko」', 'Spawn <Agent>', r'\bSpawn[ \t]+(?:<Agent>|[A-Z][\w-]*(?:[ \t]+[A-Z][\w-]*)*)'),
)


def frontmatter(text):
    return re.match(r'\A---\r?\n(.*?)^---(?:\r?\n|$)', text, re.M | re.S)


def front_fields(text):
    front = frontmatter(text)
    if not front:
        return {}
    fields = list(re.finditer(r'^([\w-]+):[ \t]*(.*)', front[1], re.M))
    return {field[1]: front[1][field.start():fields[i + 1].start() if i + 1 < len(fields) else len(front[1])]
            for i, field in enumerate(fields)}


def scalar(field):
    value = field.split(':', 1)[1].strip()
    if value.startswith(('>', '|')):
        lines = value.splitlines()[1:]
        return ' '.join(line.strip() for line in lines).strip()
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def heading_offsets(text):
    result = []
    marker = None
    offset = 0
    for line in text.splitlines(keepends=True):
        fence = re.match(r'^ {0,3}(`{3,}|~{3,})(.*?)\r?\n?$', line)
        if fence:
            if marker is None:
                marker = fence[1]
            elif fence[1][0] == marker[0] and len(fence[1]) >= len(marker) and not fence[2].strip():
                marker = None
        elif marker is None:
            found = re.match(r'^(#{1,6})[ \t]+(.+?)\s*$', line)
            if found:
                title = re.sub(r'[ \t]+#+$', '', found[2])
                result.append((found[1] + ' ' + title, offset))
        offset += len(line)
    return result


def section_span(text, heading, path):
    headings = heading_offsets(text)
    matches = [(label, offset) for label, offset in headings if label == heading]
    if len(matches) != 1:
        unavailable(f'{path}#{heading.lstrip("# ")}: found {len(matches)} sections',
                    'a unique section is required', 'Restore the named section and rerun.')
    start = matches[0][1]
    level = len(heading.split()[0])
    end = next((offset for label, offset in headings
                if offset > start and len(label.split()[0]) <= level), len(text))
    return start, end


class ImportErrorDetail(Exception):
    def __init__(self, code, fact, why, next_step):
        super().__init__(f'{fact}; {why}. {next_step}')
        self.code = code


def unavailable(fact, why, next_step):
    raise ImportErrorDetail(2, fact, why, next_step)


def refused(fact, why, next_step):
    raise ImportErrorDetail(1, fact, why, next_step)


def write_files(root, writes, permissions, dry_run=False):
    """Stage every changed file before replacement; restore the tree on I/O failure."""
    changes = {}
    for path, data in writes.items():
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            refused(f'{path}: destination escapes its checkout or is a symlink',
                    'the import must not overwrite another file through an alias',
                    'Resolve the named destination before rerunning.')
        old = path.read_bytes() if path.exists() else None
        status = path.stat() if path.exists() else None
        mode = permissions.get(path, status.st_mode & 0o777 if status else 0o644)
        if old == data and status and status.st_mode & 0o777 == mode:
            continue
        ancestor = path.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        if not ancestor.is_dir():
            unavailable(f'{ancestor}: destination parent is not a directory',
                        'the planned files cannot all be written', 'Restore the named destination directory and rerun.')
        changes[path] = (data, old, status, mode)
    if dry_run:
        return
    staged = {}
    created = []
    replaced = []
    try:
        for path, (data, _, _, mode) in changes.items():
            missing = []
            parent = path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created.append(directory)
            fd, name = tempfile.mkstemp(prefix='.import-', dir=path.parent)
            staged[path] = Path(name)
            with os.fdopen(fd, 'wb') as file:
                file.write(data)
                file.flush()
                os.fsync(file.fileno())
            staged[path].chmod(mode)
        for path, stage in staged.items():
            os.replace(stage, path)
            replaced.append(path)
    except OSError:
        for path in reversed(replaced):
            _, old, status, _ = changes[path]
            if old is None:
                path.unlink()
            else:
                path.write_bytes(old)
                path.chmod(status.st_mode & 0o777)
                os.utime(path, ns=(status.st_atime_ns, status.st_mtime_ns))
        raise
    finally:
        for path in staged.values():
            if path.exists():
                path.unlink()
        for directory in reversed(created):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()


def load_locations():
    candidates = (('skills', 'mmw', 'scripts', 'locations.py'),
                  ('skills', 'dispatch', 'scripts', 'locations.py'))
    path = next((CHECKOUT.joinpath(*parts) for parts in candidates
                 if CHECKOUT.joinpath(*parts).is_file()), None)
    if path is None:
        unavailable('locations.py is absent from both candidates',
                    'the importer cannot locate its destinations', 'Restore the checkout registry and rerun.')
    spec = importlib.util.spec_from_file_location('import_locations', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_commit(root):
    run = subprocess.run(['git', '-C', str(root), 'log', '--format=%B%x00',
                          '--grep=^git-subtree-dir: mmw-v2/upstream-pstack$'],
                         capture_output=True, text=True)
    if run.returncode:
        unavailable(f'{root}: git log failed ({run.stderr.strip()})',
                    'source provenance cannot be checked', 'Restore the git repository and rerun.')
    for message in run.stdout.split('\0'):
        if re.search(r'^git-subtree-dir: mmw-v2/upstream-pstack\s*$', message, re.M):
            match = re.search(r'^git-subtree-split: ([0-9a-fA-F]{40})\s*$', message, re.M)
            if match:
                return match[1]
            break
    unavailable(f'{root}: no squash commit with a git-subtree-split hash for {SUBTREE}',
                'source provenance cannot be checked', 'Add the pstack squash subtree before importing.')


class Table:
    def __init__(self, path, header):
        self.path = path
        self.text = path.read_bytes().decode('utf-8')
        self.rows = []
        self.line_numbers = []
        first = True
        for number, line in enumerate(self.text.splitlines(), 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if first:
                if line != header:
                    unavailable(f'{path}:{number}: invalid TSV header',
                                'the registry cannot be read', 'Correct the table header and rerun.')
                first = False
                continue
            row = line.split('\t')
            if len(row) != len(header.split('\t')):
                unavailable(f'{path}:{number}: invalid TSV row',
                            'the registry cannot be read', 'Correct the table row and rerun.')
            self.rows.append(row)
            self.line_numbers.append(number)
        if first:
            unavailable(f'{path}: no TSV header', 'the registry cannot be read',
                        'Restore the table header and rerun.')

    def contents(self, replacements=(), additions=()):
        replacements = dict(replacements)
        lines = self.text.splitlines(keepends=True)
        for index, row in replacements.items():
            number = self.line_numbers[index]
            if row != self.rows[index]:
                lines[number - 1] = '\t'.join(row) + '\n'
        text = ''.join(lines)
        if additions:
            if text and not text.endswith('\n'):
                text += '\n'
            text += ''.join('\t'.join(row) + '\n' for row in additions)
        return text.encode('utf-8')


@dataclass(frozen=True)
class Component:
    kind: str
    name: str


@dataclass
class Entry:
    component: Component
    source: str
    local: str
    data: bytes
    mechanical: str = ''
    rewrites: tuple = ()


class Importer:
    def __init__(self, root, locations, batch):
        self.root = root
        self.locations = locations
        skills = root / 'mmw-v2' / 'skills'
        self.mode = skills / locations.MODE_DIRECTORY
        self.upstream_mode = (skills / locations.PSTACK_MODE_DIRECTORY).resolve()
        self.imports = Table(skills / locations.IMPORTS_TSV, IMPORT_HEADER)
        self.rewrites = Table(skills / locations.PSTACK_REWRITES_TSV, REWRITE_HEADER)
        self.names_path = skills / locations.PSTACK_NAMES_MD
        self.commit = source_commit(root)
        self.batch = batch
        self.entries = []
        self.visited = set()
        self.skills_path = root / 'mmw-v2' / 'skills.txt'
        self.skills_text = self.skills_path.read_bytes().decode('utf-8')
        identities = set()
        for number, row in zip(self.imports.line_numbers, self.imports.rows):
            identity = tuple(row[:3])
            valid = (row[0] in TYPES and all(row[:4]) and identity not in identities and
                     row[1] != self.relative(self.mode / 'SKILL.md'))
            if row[0] == 'mode-trigger':
                valid = valid and bool(re.search(r':L[1-9]\d*$', row[2])) and row[1].endswith(
                    '#' + locations.MODE_IMPORTED_TRIGGERS.removeprefix('### '))
            if row[0] == 'mode-section':
                valid = valid and '#' in row[1] and bool(row[1].split('#', 1)[1])
            if not valid:
                unavailable(f'{self.imports.path}:{number}: invalid registration row',
                            'the component or source position cannot be read', 'Correct the named registration row and rerun.')
            identities.add(identity)
        self.skills = {line.split()[0].split('/')[-1] for line in self.skills_text.splitlines()
                       if line.strip() and not line.lstrip().startswith('#')}
        self.mapped = []
        if self.names_path.is_file():
            for line in self.names_path.read_text(encoding='utf-8').splitlines():
                if line.lstrip().startswith('|'):
                    self.mapped.append(line.strip().strip('|').split('|')[0].strip())

    def relative(self, path):
        return path.relative_to(self.root).as_posix()

    def source_path(self, component):
        kind, name = component.kind, component.name
        if not name or any(char in name for char in ('\t', '\n', '\r')) or (
                kind not in ('mode-section', 'mode-trigger') and
                (Path(name).is_absolute() or '..' in Path(name).parts or name in ('.', '/'))):
            unavailable(f'{kind} {name!r}: invalid component name',
                        'component paths must stay inside their source directory', 'Choose a relative component name and rerun.')
        source = self.root / SUBTREE
        if kind in ('principle', 'skill'):
            return source / 'skills' / name / 'SKILL.md'
        if kind == 'agent':
            return source / 'agents' / (name + '.md')
        mode = self.upstream_mode
        if kind == 'playbook':
            return mode / 'playbooks' / (name + '.md')
        if kind == 'mode-reference':
            return mode / 'references' / name
        if kind == 'mode-script':
            return mode / 'scripts' / name
        if kind in ('mode-trigger', 'mode-section'):
            return mode / 'SKILL.md'
        unavailable(f'{kind} {name}: unsupported import planner',
                    'this type has no planner', 'Implement the component planner and rerun.')

    def destination(self, component):
        kind, name = component.kind, component.name
        if kind == 'skill':
            return self.source_path(component)
        if kind == 'principle':
            return self.mode / 'principles' / (name + '.md')
        if kind == 'playbook':
            return self.mode / 'playbooks' / (name + '.md')
        if kind == 'mode-reference':
            return self.mode / 'references' / 'pstack' / name
        if kind == 'mode-script':
            return self.mode / 'scripts' / 'pstack' / name
        if kind == 'agent':
            return self.mode / 'references' / 'pstack' / 'agents' / (name + '.md')
        if kind in ('mode-trigger', 'mode-section'):
            return self.mode / 'SKILL.md'

    def transformed(self, component, require_mode=True):
        source = self.source_path(component)
        if not source.resolve().is_relative_to(self.root / SUBTREE):
            unavailable(f'{source}: source is outside the pstack subtree',
                        'only subtree components can be imported', 'Restore the named subtree file and rerun.')
        if not source.is_file():
            unavailable(f'{component.kind} {component.name}: {source} does not exist',
                        'there is no source component to import', 'Choose an existing subtree component and rerun.')
        data = source.read_bytes()
        local = self.destination(component)
        if component.kind != 'skill' and not local.resolve().is_relative_to(self.mode):
            refused(f'{local}: destination is outside the mode directory',
                    'an import must not overwrite another component', 'Resolve the named destination before rerunning.')
        if component.kind in ('mode-trigger', 'mode-section'):
            if require_mode and not local.is_file():
                unavailable(f'{component.kind} {component.name}: {local} does not exist',
                            'mode fragments require an existing mode', 'Create the mode file before importing this fragment.')
            text = data.decode('utf-8')
            if component.kind == 'mode-trigger':
                if not re.fullmatch(r'L[1-9]\d*', component.name):
                    unavailable(f'{source}: invalid line {component.name}',
                                'a trigger is selected by L<n>', 'Choose an existing source line and rerun.')
                number = int(component.name[1:])
                lines = text.splitlines(keepends=True)
                if number > len(lines):
                    unavailable(f'{source}: {component.name} does not exist',
                                'there is no source trigger line', 'Choose an existing source line and rerun.')
                data = lines[number - 1].encode('utf-8')
                source_label = self.relative(source) + ':' + component.name
                heading = self.locations.MODE_IMPORTED_TRIGGERS.removeprefix('### ')
            else:
                start, end = section_span(text, '## ' + component.name, source)
                data = text[start:end].encode('utf-8')
                source_label = self.relative(source)
                heading = component.name
            return Entry(component, source_label, self.relative(local) + '#' + heading, data)
        if component.kind in ('skill', 'mode-reference', 'mode-script'):
            return Entry(component, self.relative(source), self.relative(local), data)
        text = data.decode('utf-8')
        changes = []
        rewrites = []
        front = frontmatter(text)
        if component.kind == 'agent' and front:
            fields = front_fields(text)
            kept = ''.join(raw for name, raw in fields.items() if name in ('name', 'description'))
            if kept != front[1]:
                text = text[:front.start(1)] + kept + text[front.end(1):]
                changes.append('remove host frontmatter fields')
        if front and component.kind == 'principle':
            cleaned = re.sub(r'^disable-model-invocation:[^\n]*(?:\n|$)', '', front[1], flags=re.M)
            if cleaned != front[1]:
                text = text[:front.start(1)] + cleaned + text[front.end(1):]
                changes.append('remove disable-model-invocation')

        def link(match):
            old = match[0]
            if component.kind == 'principle':
                new = match[1] + '.md'
                target = self.mode / 'principles' / new
                resolved = (source.parent / old).resolve()
            elif old.startswith('../references/'):
                new = '../references/pstack/' + match[1]
                target = self.mode / 'references' / 'pstack' / match[1]
                resolved = (source.parent / old).resolve()
            else:
                new = 'scripts/pstack/' + match[1]
                target = self.mode / 'scripts' / 'pstack' / match[1]
                resolved = self.upstream_mode / old
            in_reference = any(ref.start() <= match.start() and match.end() <= ref.end()
                               for ref in re.finditer(r'`+[^`]*`+|\[[^\]]*\]\([^\s)]+\)', text))
            if resolved.is_file() and in_reference:
                rewrites.append(('path', self.relative(resolved),
                                 self.relative(target), ''))
            else:
                rewrites.append(('token', old, new, self.relative(local)))
            changes.append(old + ' -> ' + new)
            return new

        if component.kind == 'principle':
            text = re.sub(r'\.\./(principle-[a-zA-Z0-9][\w-]*)/SKILL\.md', link, text)
        elif component.kind == 'playbook':
            text = re.sub(r'\.\./references/([\w./-]*[\w/-])', link, text)
            text = re.sub(r'(?<![\w/])scripts/([\w./-]*[\w/-])', link, text)
        return Entry(component, self.relative(source), self.relative(local), text.encode('utf-8'),
                     '; '.join(dict.fromkeys(changes)), tuple(dict.fromkeys(rewrites)))

    def add(self, component):
        if component in self.visited:
            return
        self.visited.add(component)
        if component.kind == 'mode-script':
            script_root = self.upstream_mode / 'scripts'
            entries = [self.transformed(Component('mode-script', self.relative(source)[len(self.relative(script_root)) + 1:]))
                       for source in self.script_files(self.source_path(component))]
        else:
            entries = [self.transformed(component)]
        for entry in entries:
            if any(old.local == entry.local and old.source == entry.source for old in self.entries):
                continue
            self.entries.append(entry)
            self.add_dependencies(entry)

    def add_dependencies(self, entry):
        source_text = (entry.data.decode('utf-8') if entry.component.kind in ('mode-trigger', 'mode-section') else
                       (self.root / entry.source).read_bytes().decode('utf-8', errors='replace'))
        for dependency, offset in self.dependencies(source_text):
            if dependency == entry.component or dependency in self.visited:
                continue
            local = self.destination(dependency)
            if ((dependency.kind != 'skill' and local.exists()) or
                    (dependency.kind == 'skill' and dependency.name in self.skills) or
                    any(dependency.name in cell for cell in self.mapped)):
                continue
            if not self.source_path(dependency).exists():
                line = source_text.count('\n', 0, offset) + 1
                refused(f'{entry.source}:{line}: dangling dependency {dependency.name}',
                        'neither MMW, pstack-names.md nor the subtree supplies it',
                        'Resolve the named dependency before rerunning.')
            self.add(dependency)

    def script_files(self, source):
        if not source.exists():
            unavailable(f'mode-script {source}: source does not exist',
                        'there is no script to copy', 'Choose an existing script and rerun.')
        pending = sorted(p for p in source.rglob('*') if p.is_file()) if source.is_dir() else [source]
        found = set()
        while pending:
            file = pending.pop(0)
            if file in found:
                continue
            found.add(file)
            text = file.read_bytes().decode('utf-8', errors='replace')
            siblings = []
            if file.suffix == '.py':
                for node in ast.walk(ast.parse(text, filename=str(file))):
                    if isinstance(node, ast.Import):
                        siblings += [file.parent / (alias.name.split('.')[0] + '.py') for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        names = [node.module.split('.')[0]] if node.module else [a.name for a in node.names]
                        siblings += [file.parent / (name + '.py') for name in names]
            for line in text.splitlines():
                shell = re.match(r'\s*(?:source|\.)\s+(.+)', line)
                if shell:
                    names = re.findall(r'([\w.-]+\.sh)\b', shell[1])
                    siblings += [file.parent / name for name in names]
            for match in re.finditer(r'(?:from\s*|import\s*|require\(\s*)[\'"]\./([^\'"/]+)[\'"]', text):
                sibling = file.parent / match[1]
                if not sibling.exists() and not sibling.suffix:
                    sibling = next((sibling.with_suffix(ext) for ext in ('.ts', '.js', '.mjs')
                                    if sibling.with_suffix(ext).is_file()), sibling)
                if not sibling.is_file():
                    refused(f'{self.relative(file)}: missing same-directory import {match[1]}',
                            'the copied script would have a dangling import', 'Restore the named script dependency and rerun.')
                siblings.append(sibling)
            pending += [p for p in siblings if p.is_file() and p not in found]
        return sorted(found)

    @staticmethod
    def dependencies(text):
        found = []
        for pattern, kind in ((r'\b(principle-[a-zA-Z0-9][\w-]*)\b', 'principle'),
                              (r'the\s+\*\*([\w-]+)\*\*\s+principle', 'principle'),
                              (r'the\s+(?:\*\*|`)([\w-]+)(?:\*\*|`)\s+skill', 'skill'),
                              (r'(?<![\w/])playbooks/([\w-]+)\.md', 'playbook'),
                              (r'\.\./references/([\w./-]*[\w/-])', 'mode-reference'),
                              (r'(?<![\w/])scripts/([\w./-]*[\w/-])', 'mode-script')):
            for match in re.finditer(pattern, text):
                name = match[1]
                if kind == 'principle' and not name.startswith('principle-'):
                    name = 'principle-' + name
                found.append((Component(kind, name), match.start()))
        return sorted(found, key=lambda pair: pair[1])

    def index_line(self, entry):
        text = (self.root / entry.source).read_bytes().decode('utf-8')
        title = re.search(r'^# (.+?)\r?$', text, re.M)
        fields = front_fields(text)
        if title is None or 'description' not in fields:
            unavailable(f'{entry.source}: H1 or description is missing',
                        'the principle index cannot be generated', 'Restore the source metadata and rerun.')
        description = scalar(fields['description'])
        boundary = SENTENCE_END.search(description)
        first = description[:boundary.end()] if boundary else description
        source_mode = self.upstream_mode / 'SKILL.md'
        mode_text = source_mode.read_bytes().decode('utf-8')
        start, end = section_span(mode_text, self.locations.MODE_PRINCIPLES, source_mode)
        group = ''
        for line in mode_text[start:end].splitlines():
            label = re.fullmatch(r'\*\*([^*]+)\*\*', line.strip())
            if label:
                group = label[1]
            if '**' + entry.component.name + '**' in line and group:
                return group, f'- **{title[1]}** (**{entry.component.name}**). {first}'
        unavailable(f'{source_mode}: {entry.component.name} has no principle group',
                    'the index needs its source group', 'Restore the source principle index and rerun.')

    def skill_lines(self):
        named = set()
        files = [self.mode / 'SKILL.md', *(self.mode / 'playbooks').rglob('*')]
        texts = [p.read_bytes().decode('utf-8') for p in files if p.is_file()]
        texts += [e.data.decode('utf-8') for e in self.entries if e.component.kind == 'playbook']
        for text in texts:
            named.update(c.name for c, _ in self.dependencies(text) if c.kind == 'skill')
        return {e.component.name: 'pstack/' + e.component.name +
                (' +model-invoked' if e.component.name in named else '')
                for e in self.entries if e.component.kind == 'skill'}

    def same_rows(self, entry):
        return [(i, row) for i, row in enumerate(self.imports.rows)
                if row[0] == entry.component.kind and row[1] == entry.local and row[2] == entry.source]

    def mode_fragment(self, entry, text):
        heading = self.locations.MODE_IMPORTED_TRIGGERS if entry.component.kind == 'mode-trigger' else '## ' + entry.component.name
        if heading not in dict(heading_offsets(text)):
            return None
        start, end = section_span(text, heading, self.mode / 'SKILL.md')
        if entry.component.kind == 'mode-section':
            return text[start:end].encode('utf-8')
        records = [row for row in self.imports.rows if row[0] == 'mode-trigger' and row[1] == entry.local]
        same = next((i for i, row in enumerate(records) if row[2] == entry.source), None)
        if same is None:
            return None
        lines = text[start:end].splitlines(keepends=True)
        index = len(lines) - len(records) - 1 + same
        if index < 2 or not lines[-1].isspace():
            refused(f'{entry.local}: imported trigger positions cannot be read',
                    'the mode region was changed manually', 'Merge the imported triggers manually and record the judgement change.')
        return lines[index].encode('utf-8')

    def merge_mode(self, entry, text):
        data = entry.data.decode('utf-8')
        if entry.component.kind == 'mode-section':
            heading = '## ' + entry.component.name
            if heading in dict(heading_offsets(text)):
                start, end = section_span(text, heading, self.mode / 'SKILL.md')
                return text[:start] + data + text[end:]
            start, _ = section_span(text, self.locations.MODE_PLAYBOOKS, self.mode / 'SKILL.md')
            return text[:start] + data + text[start:]
        heading = self.locations.MODE_IMPORTED_TRIGGERS
        if heading not in dict(heading_offsets(text)):
            _, end = section_span(text, self.locations.MODE_NON_NEGOTIABLES, self.mode / 'SKILL.md')
            text = text[:end] + heading + '\n\n\n' + text[end:]
        start, end = section_span(text, heading, self.mode / 'SKILL.md')
        old = self.mode_fragment(entry, text)
        block = text[start:end]
        if old is not None:
            if old == entry.data:
                return text
            records = [row for row in self.imports.rows if row[0] == 'mode-trigger' and row[1] == entry.local]
            rank = next(i for i, row in enumerate(records) if row[2] == entry.source)
            lines = block.splitlines(keepends=True)
            lines[len(lines) - len(records) - 1 + rank] = data
            block = ''.join(lines)
        else:
            if len(block.splitlines()) < 3:
                block = block.rstrip('\r\n') + '\n\n'
            elif block.endswith('\n\n'):
                block = block[:-1]
            elif not block.endswith('\n'):
                block += '\n'
            block += data + ('\n' if data.endswith('\n') else '\n\n')
        return text[:start] + block + text[end:]

    def registered_component(self, row):
        kind, local, source = row[:3]
        path = Path(source.split(':L', 1)[0])
        if kind in ('principle', 'skill'):
            name = path.parent.name
        elif kind in ('playbook', 'agent'):
            name = path.stem
        elif kind == 'mode-trigger':
            name = 'L' + source.rsplit(':L', 1)[1]
        elif kind == 'mode-section':
            name = local.split('#', 1)[1]
        elif kind in ('mode-reference', 'mode-script'):
            directory = 'references' if kind == 'mode-reference' else 'scripts'
            base = Path(self.relative(self.upstream_mode)) / directory
            name = path.relative_to(base).as_posix()
        else:
            unavailable(f'{self.imports.path}: unknown registered type {kind}',
                        'the registry row cannot be refreshed', 'Correct the registered type and rerun.')
        return Component(kind, name)

    def check_keywords(self):
        missing = []
        for entry in self.entries:
            source = entry.source.split(':L', 1)[0]
            text = entry.data.decode('utf-8', errors='replace')
            offset = 0
            if entry.component.kind == 'mode-trigger':
                offset = int(entry.component.name[1:]) - 1
            elif entry.component.kind == 'mode-section':
                full = (self.root / source).read_bytes().decode('utf-8')
                start, _ = section_span(full, '## ' + entry.component.name, source)
                offset = full.count('\n', 0, start)
            for _, keyword, pattern in SLOT_KEYWORDS:
                for match in re.finditer(pattern, text):
                    literal = match[0] if keyword == 'Spawn <Agent>' else keyword
                    mapped = (any(re.search(pattern, cell) for cell in self.mapped)
                              if keyword == 'configured … model' else
                              any(literal in cell for cell in self.mapped))
                    if not mapped:
                        line = offset + text.count('\n', 0, match.start()) + 1
                        missing.append(f'{source}:{line}: {literal}')
        if missing:
            refused('\n'.join(missing), 'slot keywords have no pstack-names.md mapping',
                    f'Add the named mappings to {self.names_path} before rerunning.')

    def refresh(self):
        stale = review = 0
        for row in self.imports.rows:
            if row[5]:
                if row[3] != self.commit:
                    print('REVIEW\t' + row[1] + '\t' + row[2])
                    review += 1
                continue
            component = self.registered_component(row)
            entry = self.transformed(component, require_mode=False)
            if component.kind == 'skill':
                self.entries = [entry]
                expected = self.skill_lines()[component.name]
                actual = next((line.rstrip('\r\n') for line in self.skills_text.splitlines()
                               if line.split() and line.split()[0] == 'pstack/' + component.name), None)
                different = actual != expected
            elif component.kind in ('mode-trigger', 'mode-section'):
                mode_file = self.mode / 'SKILL.md'
                different = not mode_file.is_file() or self.mode_fragment(
                    entry, mode_file.read_bytes().decode('utf-8')) != entry.data
            else:
                local = self.root / entry.local
                different = not local.is_file() or local.read_bytes() != entry.data
            if different:
                print('STALE\t' + row[1] + '\t' + row[2])
                stale += 1
        print(f'REFRESH\t{len(self.imports.rows)}\t{stale}\t{review}')
        return 1 if stale or review else 0

    def run(self, component, dry_run):
        self.add(component)
        self.check_keywords()
        writes = {self.root / e.local: e.data for e in self.entries
                  if e.component.kind not in ('skill', 'mode-trigger', 'mode-section')}
        skill_lines = self.skill_lines()
        if skill_lines:
            remaining = dict(skill_lines)
            lines = self.skills_text.splitlines(keepends=True)
            for index, line in enumerate(lines):
                words = line.split()
                if words and words[0].startswith('pstack/'):
                    name = words[0].split('/')[-1]
                    if name in remaining:
                        want = remaining.pop(name)
                        if line.rstrip('\r\n') != want:
                            lines[index] = want + '\n'
            text = ''.join(lines)
            if remaining:
                text += ('' if not text or text.endswith('\n') else '\n') + '\n'.join(remaining.values()) + '\n'
            writes[self.skills_path] = text.encode('utf-8')
        rows = [[e.component.kind, e.local, e.source, self.commit, e.mechanical, '', self.batch]
                for e in self.entries]
        replacements = []
        additions = []
        for entry, row in zip(self.entries, rows):
            existing = [(i, old) for i, old in enumerate(self.imports.rows)
                        if old[1] == entry.local]
            same = self.same_rows(entry)
            if same:
                index, old = same[0]
                if old[5]:
                    refused(f'{self.imports.path}:{self.imports.line_numbers[index]}: {entry.local} has judgement changes',
                            'mechanical refresh cannot merge manual changes', 'Merge the named row manually before rerunning.')
                row[6] = old[6]
                replacements.append((index, row))
            elif (existing and entry.component.kind != 'mode-trigger') or (
                    entry.component.kind == 'mode-section' and '## ' + entry.component.name in dict(
                        heading_offsets((self.mode / 'SKILL.md').read_bytes().decode('utf-8')))) or (
                    entry.component.kind not in ('skill', 'mode-trigger', 'mode-section') and (self.root / entry.local).exists()) or (
                    entry.component.kind == 'skill' and entry.component.name in self.skills):
                conflict = self.relative(self.skills_path) if entry.component.kind == 'skill' else entry.local
                refused(f'{entry.component.kind} {entry.component.name}: {conflict} already exists',
                        'it is not registered from this source', 'Resolve the same-name component manually before rerunning.')
            else:
                additions.append(row)
        for entry in self.entries:
            if entry.component.kind in ('mode-trigger', 'mode-section'):
                path = self.mode / 'SKILL.md'
                text = writes.get(path, path.read_bytes()).decode('utf-8')
                writes[path] = self.merge_mode(entry, text).encode('utf-8')
        rewrite_rows = []
        for entry in self.entries:
            for rewrite in entry.rewrites:
                row = list(rewrite)
                if row not in self.rewrites.rows and row not in rewrite_rows:
                    rewrite_rows.append(row)
        indexes = {e.source: self.index_line(e) for e in self.entries if e.component.kind == 'principle'}
        writes[self.imports.path] = self.imports.contents(replacements, additions)
        writes[self.rewrites.path] = self.rewrites.contents(additions=rewrite_rows)
        permissions = {self.root / e.local: (self.root / e.source).stat().st_mode & 0o777
                       for e in self.entries if e.component.kind == 'mode-script'}
        write_files(self.root, writes, permissions, dry_run=dry_run)
        for entry, row in zip(self.entries, rows):
            if entry.component.kind == 'skill':
                print('SKILLS\t' + skill_lines[entry.component.name])
            elif entry.component.kind in ('mode-trigger', 'mode-section'):
                print('MODE\t' + entry.local)
            else:
                print('COPY\t' + entry.source + '\t' + entry.local)
            for rewrite in entry.rewrites:
                print('REWRITE\t' + '\t'.join(rewrite))
            print('REGISTER\t' + '\t'.join(row))
            if entry.source in indexes:
                print('INDEX\t' + '\t'.join(indexes[entry.source]))
        print(('DRY-RUN' if dry_run else 'IMPORTED') + '\t' + str(len(self.visited)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('type', nargs='?')
    parser.add_argument('name', nargs='?')
    parser.add_argument('--root')
    parser.add_argument('--batch', default='on-demand')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    try:
        root = Path(args.root).resolve() if args.root else CHECKOUT.parent
        if any(char in args.batch for char in ('\t', '\n', '\r')):
            parser.error('--batch must be one TSV cell')
        if args.refresh and (args.type or args.name or args.dry_run or args.batch != 'on-demand'):
            parser.error('--refresh takes only --root')
        if not args.refresh and args.type not in TYPES:
            unavailable(f'unknown type {args.type!r}', 'the importer knows eight component types',
                        'Choose a type from ' + ', '.join(TYPES) + ' and rerun.')
        if not args.refresh and not args.name:
            parser.error('type and name are required')
        if not (root / SUBTREE).is_dir():
            unavailable(f'{root / SUBTREE}: subtree does not exist', 'there are no source components',
                        'Add the pstack squash subtree before importing.')
        importer = Importer(root, load_locations(), args.batch)
        if args.refresh:
            return importer.refresh()
        importer.run(Component(args.type, args.name), args.dry_run)
        return 0
    except ImportErrorDetail as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except (OSError, UnicodeError, ValueError, AttributeError, SyntaxError) as exc:
        print(f'Import could not run: {exc}; a required file or registry is unreadable. Restore the named file and rerun.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
