#!/usr/bin/env python3
"""Import pstack components through their public command-line interface.

Mechanical patterns: principles drop the disable-model-invocation frontmatter
line and change ../principle-x/SKILL.md to principle-x.md; playbooks change
../references/X to ../references/pstack/X and scripts/X to scripts/pstack/X.
Skills register pstack/<name>, with +model-invoked when mode or playbooks name
them. Triggers and sections copy verbatim; references and scripts copy verbatim
(scripts include same-directory imports/source files); agent frontmatter keeps
only name and description. Principle indexes come from H1 and description.

Names only pstack has are not rewritten here: each one in a copied file is printed as NAME<TAB><file><TAB><line><TAB><name> before the last line, for the person importing to rewrite in MMW's words. A skill a copied file names that skills.txt lacks is such a name; it is never imported with its namer.
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

@dataclass(frozen=True)
class Layout:
    source_base: str
    source_directory: str
    source_name: str
    destination_directory: str | None
    destination_name: str
    registered_name: str
    storage: str = 'file'


LAYOUTS = {
    'playbook': Layout('mode', 'playbooks', '{name}.md', 'MODE_PLAYBOOKS_DIRECTORY', '{name}.md', 'stem'),
    'principle': Layout('subtree', 'skills', '{name}/SKILL.md', 'MODE_PRINCIPLES_DIRECTORY', '{name}.md', 'parent'),
    'skill': Layout('subtree', 'skills', '{name}/SKILL.md', None, '', 'parent', 'skill'),
    'mode-trigger': Layout('mode', '', 'SKILL.md', 'MODE_DIRECTORY', 'SKILL.md', 'line', 'fragment'),
    'mode-section': Layout('mode', '', 'SKILL.md', 'MODE_DIRECTORY', 'SKILL.md', 'anchor', 'fragment'),
    'mode-reference': Layout('mode', 'references', '{name}', 'PSTACK_REFERENCES_DIRECTORY', '{name}', 'relative'),
    'mode-script': Layout('mode', 'scripts', '{name}', 'PSTACK_SCRIPTS_DIRECTORY', '{name}', 'relative'),
    'agent': Layout('subtree', 'agents', '{name}.md', 'PSTACK_AGENTS_DIRECTORY', '{name}.md', 'stem'),
}
TYPES = tuple(LAYOUTS)
IMPORT_HEADER = 'type\tlocal\tsource\tcommit\tmechanical\tjudgement\tbatch'
REWRITE_HEADER = 'kind\told\tnew\tscope'
CHECKOUT = Path(__file__).resolve().parents[2]
# Same boundary as skill_text.SENTENCE_END; it does not require loading PyYAML.
SENTENCE_END = re.compile(r'[.?!。](?=\s*[A-Z`*(\[0-9\u3400-\u9fff])')
# (printed name, scan pattern). The printed name of 'Spawn <Agent>' is the matched text.
PSTACK_NAME_KEYWORDS = (
    ('control skill', r'\bcontrol skill\b'),
    ('Opening a PR', r'\bOpening a PR\b'),
    ('gh', r'\bgh\b'),
    ('origin', r'\borigin\b'),
    ('gt', r'\bgt\b'),
    ('subagent_type', r'\bsubagent_type\b'),
    ('generalPurpose', r'\bgeneralPurpose\b'),
    ('run_in_background', r'\brun_in_background\b'),
    ('configured … model', r'\bconfigured\b[^\n.!?]*?\bmodel\b'),
    ('pstack-models.mdc', r'\bpstack-models\.mdc\b'),
    ('poteto-mode', r'\bpoteto-mode\b'),
    ('AskQuestion', r'\bAskQuestion\b'),
    ('/loop', r'/loop\b'),
    ('/goal', r'/goal\b'),
    ('/deslop', r'/deslop\b'),
    ('cloud', r'\bcloud\b'),
    ('agent-transcripts', r'\bagent-transcripts\b'),
    ('mcps/', r'\bmcps/'),
    ('brain note', r'\bbrain notes?\b'),
    ('rebase', r'\b[Rr]ebas(?:e|ed|es|ing)\b'),
    ('Binary-search', r'\b[Bb]inary-search\b'),
    ('git show origin/main:', r'git show origin/main:'),
    ('Spawn <Agent>', r'\bSpawn[ \t]+(?:<Agent>|[A-Z][\w-]*(?:[ \t]+[A-Z][\w-]*)*)'),
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


class ImportRefusal(Exception):
    def __init__(self, code, fact, why, next_step):
        super().__init__(fact, why, next_step)
        self.code = code


def unavailable(fact, why, next_step):
    raise ImportRefusal(2, fact, why, next_step)


def refused(fact, why, next_step):
    raise ImportRefusal(1, fact, why, next_step)


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


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_locations():
    candidates = (('skills', 'mmw', 'scripts', 'locations.py'),
                  ('skills', 'dispatch', 'scripts', 'locations.py'))
    path = next((CHECKOUT.joinpath('mmw-v2', *parts) for parts in candidates
                 if CHECKOUT.joinpath('mmw-v2', *parts).is_file()), None)
    if path is None:
        raise FileNotFoundError('locations.py is absent from both checkout candidates')
    return load_module('import_locations', path)


def source_commit(root, subtree):
    trailer = 'git-subtree-dir: ' + subtree.as_posix()
    run = subprocess.run(['git', '-C', str(root), 'log', '--format=%B%x00',
                          '--grep=^' + trailer + '$'],
                         capture_output=True, text=True)
    if run.returncode:
        unavailable(f'{root}: git log failed ({run.stderr.strip()})',
                    'source provenance cannot be checked', 'Restore the git repository and rerun.')
    for message in run.stdout.split('\0'):
        if re.search('^' + re.escape(trailer) + r'\s*$', message, re.M):
            match = re.search(r'^git-subtree-split: ([0-9a-fA-F]{40})\s*$', message, re.M)
            if match:
                return match[1]
            break
    unavailable(f'{root}: no squash commit with a git-subtree-split hash for {subtree}',
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

    @property
    def layout(self):
        return LAYOUTS[self.kind]


@dataclass
class Entry:
    component: Component
    source: str
    local: str
    data: bytes
    mechanical: str = ''
    rewrites: tuple = ()
    source_lines: tuple = ()


class Importer:
    def __init__(self, root, locations, batch):
        self.root = root
        self.locations = locations
        skills = self.skills_root = root / 'mmw-v2' / 'skills'
        self.mode = skills / locations.MODE_DIRECTORY
        self.subtree = (skills / locations.PSTACK_DIRECTORY).resolve()
        self.upstream_mode = (skills / locations.PSTACK_MODE_DIRECTORY).resolve()
        self.imports = Table(skills / locations.IMPORTS_TSV, IMPORT_HEADER)
        self.rewrites = Table(skills / locations.PSTACK_REWRITES_TSV, REWRITE_HEADER)
        self.commit = source_commit(root, self.subtree.relative_to(root))
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

    def relative(self, path):
        return path.relative_to(self.root).as_posix()

    def source_path(self, component):
        kind, name = component.kind, component.name
        layout = component.layout
        if not name or any(char in name for char in ('\t', '\n', '\r')) or (
                layout.storage != 'fragment' and
                (Path(name).is_absolute() or '..' in Path(name).parts or name in ('.', '/'))):
            unavailable(f'{kind} {name!r}: invalid component name',
                        'component paths must stay inside their source directory', 'Choose a relative component name and rerun.')
        base = self.upstream_mode if layout.source_base == 'mode' else self.subtree
        return base / layout.source_directory / layout.source_name.format(name=name)

    def destination(self, component):
        layout = component.layout
        if layout.destination_directory is None:
            return self.source_path(component)
        return (self.skills_root / getattr(self.locations, layout.destination_directory) /
                layout.destination_name.format(name=component.name))

    def transformed(self, component, require_mode=True):
        source = self.source_path(component)
        if not source.resolve().is_relative_to(self.subtree):
            unavailable(f'{source}: source is outside the pstack subtree',
                        'only subtree components can be imported', 'Restore the named subtree file and rerun.')
        if not source.is_file():
            unavailable(f'{component.kind} {component.name}: {source} does not exist',
                        'there is no source component to import', 'Choose an existing subtree component and rerun.')
        data = source.read_bytes()
        local = self.destination(component)
        if component.layout.storage != 'skill' and not local.resolve().is_relative_to(self.mode):
            refused(f'{local}: destination is outside the mode directory',
                    'an import must not overwrite another component', 'Resolve the named destination before rerunning.')
        if component.layout.storage == 'fragment':
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
                source_lines = (number,)
            else:
                start, end = section_span(text, '## ' + component.name, source)
                data = text[start:end].encode('utf-8')
                source_label = self.relative(source)
                heading = component.name
                first = text.count('\n', 0, start) + 1
                source_lines = tuple(range(first, first + len(data.splitlines())))
            return Entry(component, source_label, self.relative(local) + '#' + heading, data,
                         source_lines=source_lines)
        if component.kind in ('skill', 'mode-reference', 'mode-script'):
            return Entry(component, self.relative(source), self.relative(local), data)
        text = data.decode('utf-8')
        changes = []
        rewrites = []
        removed_lines = set()
        front = frontmatter(text)
        if component.kind == 'agent' and front:
            fields = front_fields(text)
            kept = ''.join(raw for name, raw in fields.items() if name in ('name', 'description'))
            for name, raw in fields.items():
                if name not in ('name', 'description'):
                    first = text.count('\n', 0, front.start(1) + front[1].index(raw)) + 1
                    removed_lines.update(range(first, first + len(raw.splitlines())))
            if kept != front[1]:
                text = text[:front.start(1)] + kept + text[front.end(1):]
                changes.append('remove host frontmatter fields')
        if front and component.kind == 'principle':
            for match in re.finditer(r'^disable-model-invocation:[^\n]*(?:\n|$)', front[1], re.M):
                removed_lines.add(text.count('\n', 0, front.start(1) + match.start()) + 1)
            cleaned = re.sub(r'^disable-model-invocation:[^\n]*(?:\n|$)', '', front[1], flags=re.M)
            if cleaned != front[1]:
                text = text[:front.start(1)] + cleaned + text[front.end(1):]
                changes.append('remove disable-model-invocation')

        def link(match):
            old = match[0]
            if component.kind == 'principle':
                new = match[1] + '.md'
                target = self.destination(Component('principle', match[1]))
                resolved = (source.parent / old).resolve()
            elif old.startswith('../references/'):
                new = '../references/pstack/' + match[1]
                target = self.destination(Component('mode-reference', match[1]))
                resolved = (source.parent / old).resolve()
            else:
                new = 'scripts/pstack/' + match[1]
                target = self.destination(Component('mode-script', match[1]))
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
                     '; '.join(dict.fromkeys(changes)), tuple(dict.fromkeys(rewrites)),
                     tuple(n for n in range(1, len(data.splitlines()) + 1) if n not in removed_lines))

    def add(self, component):
        if component in self.visited:
            return
        self.visited.add(component)
        if component.kind == 'mode-script':
            script_root = self.upstream_mode / 'scripts'
            entries = [self.transformed(Component('mode-script', source.relative_to(script_root).as_posix()))
                       for source in self.script_files(self.source_path(component))]
        else:
            entries = [self.transformed(component)]
        for entry in entries:
            if any(old.local == entry.local and old.source == entry.source for old in self.entries):
                continue
            self.entries.append(entry)
            self.add_dependencies(entry)

    def add_dependencies(self, entry):
        source_text = (entry.data.decode('utf-8') if entry.component.layout.storage == 'fragment' else
                       (self.root / entry.source).read_bytes().decode('utf-8', errors='replace'))
        for dependency, offset in self.dependencies(source_text):
            if dependency == entry.component or dependency in self.visited or dependency.kind == 'skill':
                continue
            local = self.destination(dependency)
            if local.exists():
                continue
            if not self.source_path(dependency).exists():
                index = source_text.count('\n', 0, offset)
                line = entry.source_lines[index] if entry.component.layout.storage == 'fragment' else index + 1
                source = entry.source.split(':L', 1)[0]
                refused(f'{source}:{line}: dangling dependency {dependency.name}',
                        'neither MMW nor the subtree supplies it',
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
                try:
                    tree = ast.parse(text, filename=str(file))
                except SyntaxError as exc:
                    unavailable(f'{self.relative(file)}:{exc.lineno}: {exc.msg}',
                                'same-directory script imports cannot be read',
                                'Correct the source script syntax and rerun.')
                for node in ast.walk(tree):
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

    def skill_lines(self, writes=None):
        writes = writes or {}
        named = set()
        files = [self.mode / 'SKILL.md', *(self.skills_root / self.locations.MODE_PLAYBOOKS_DIRECTORY).rglob('*')]
        files += [self.root / e.local for e in self.entries if e.component.kind == 'playbook']
        texts = [writes[p].decode('utf-8') if p in writes else p.read_bytes().decode('utf-8')
                 for p in dict.fromkeys(files) if p in writes or p.is_file()]
        for text in texts:
            named.update(c.name for c, _ in self.dependencies(text) if c.kind == 'skill')
        candidates = {e.component.name for e in self.entries if e.component.kind == 'skill'}
        candidates.update(line.split()[0].removeprefix('pstack/') for line in self.skills_text.splitlines()
                          if line.split() and line.split()[0].startswith('pstack/') and
                          line.split()[0].removeprefix('pstack/') in named)
        return {name: 'pstack/' + name + (' +model-invoked' if name in named else '')
                for name in sorted(candidates)}

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
        lines = text[start:end].splitlines(keepends=True)
        index = self.trigger_index(entry, lines)
        return lines[index].encode('utf-8') if index is not None else None

    def trigger_index(self, entry, lines):
        records = [row for row in self.imports.rows if row[0] == 'mode-trigger' and row[1] == entry.local]
        rank = next((i for i, row in enumerate(records) if row[2] == entry.source), None)
        if rank is None:
            return None
        index = len(lines) - len(records) - 1 + rank
        if index < 2 or not lines or not lines[-1].isspace():
            refused(f'{entry.local}: imported trigger positions cannot be read',
                    'the mode region was changed manually', 'Merge the imported triggers manually and record the judgement change.')
        return index

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
            lines = block.splitlines(keepends=True)
            lines[self.trigger_index(entry, lines)] = data
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
        layout = LAYOUTS[kind]
        names = {
            'parent': lambda: path.parent.name,
            'stem': lambda: path.stem,
            'line': lambda: 'L' + source.rsplit(':L', 1)[1],
            'anchor': lambda: local.split('#', 1)[1],
            'relative': lambda: path.relative_to(Path(self.relative(self.upstream_mode)) /
                                               layout.source_directory).as_posix(),
        }
        return Component(kind, names[layout.registered_name]())

    def content_span(self, entry, text):
        if entry.component.layout.storage != 'fragment':
            return 0, len(text)
        if entry.component.kind == 'mode-section':
            return section_span(text, '## ' + entry.component.name, self.mode / 'SKILL.md')
        start, end = section_span(text, self.locations.MODE_IMPORTED_TRIGGERS, self.mode / 'SKILL.md')
        lines = text[start:end].splitlines(keepends=True)
        index = self.trigger_index(entry, lines)
        if index is None:
            wanted = entry.data.decode('utf-8')
            matches = [i for i, line in enumerate(lines) if line == wanted]
            index = matches[-1] if matches else None
        if index is None:
            return start, start
        offset = start + sum(len(line) for line in lines[:index])
        return offset, offset + len(lines[index])

    def name_lines(self, writes):
        """NAME rows for copied files, in import order, using post-import line numbers."""
        listed = []
        for entry in self.entries:
            if entry.component.kind == 'skill':
                continue
            path = self.mode / 'SKILL.md' if entry.component.layout.storage == 'fragment' else self.root / entry.local
            raw = writes.get(path, entry.data)
            text = raw.decode('utf-8', errors='replace')
            start, end = self.content_span(entry, text)
            region = text[start:end]
            label = self.relative(self.mode / 'SKILL.md') if entry.component.layout.storage == 'fragment' else entry.local
            hits = []
            for keyword, pattern in PSTACK_NAME_KEYWORDS:
                for match in re.finditer(pattern, region):
                    name = match[0] if keyword == 'Spawn <Agent>' else keyword
                    absolute = start + match.start()
                    hits.append((absolute, text.count('\n', 0, absolute) + 1, name))
            for dependency, offset in self.dependencies(region):
                if dependency.kind == 'skill' and dependency.name not in self.skills:
                    absolute = start + offset
                    hits.append((absolute, text.count('\n', 0, absolute) + 1, dependency.name))
            hits.sort(key=lambda item: item[0])
            listed += [f'NAME\t{label}\t{line}\t{name}' for _, line, name in hits]
        return listed

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
            if component.layout.storage == 'skill':
                self.entries = [entry]
                expected = self.skill_lines()[component.name]
                actual = next((line.rstrip('\r\n') for line in self.skills_text.splitlines()
                               if line.split() and line.split()[0] == 'pstack/' + component.name), None)
                different = actual != expected
            elif component.layout.storage == 'fragment':
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
        writes = {self.root / e.local: e.data for e in self.entries
                  if e.component.layout.storage == 'file'}
        for entry in self.entries:
            if entry.component.layout.storage == 'fragment':
                path = self.mode / 'SKILL.md'
                text = writes.get(path, path.read_bytes()).decode('utf-8')
                writes[path] = self.merge_mode(entry, text).encode('utf-8')
        skill_lines = self.skill_lines(writes)
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
        listed = self.name_lines(writes)
        write_files(self.root, writes, permissions, dry_run=dry_run)
        for entry, row in zip(self.entries, rows):
            if entry.component.layout.storage == 'skill':
                print('SKILLS\t' + skill_lines[entry.component.name])
            elif entry.component.layout.storage == 'fragment':
                print('MODE\t' + entry.local)
            else:
                print('COPY\t' + entry.source + '\t' + entry.local)
            print('REGISTER\t' + '\t'.join(row))
            if entry.source in indexes:
                print('INDEX\t' + '\t'.join(indexes[entry.source]))
        for rewrite in rewrite_rows:
            print('REWRITE\t' + '\t'.join(rewrite))
        for name, line in skill_lines.items():
            if not any(e.component.kind == 'skill' and e.component.name == name for e in self.entries):
                print('SKILLS\t' + line)
        for line in listed:
            print(line)
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
    refusal_message = None
    try:
        locations = load_locations()
        required = {'MODE_DIRECTORY', 'IMPORTS_TSV', 'PSTACK_REWRITES_TSV',
                    'PSTACK_DIRECTORY', 'PSTACK_MODE_DIRECTORY', 'UI_ACCEPTANCE_REFUSAL_PY',
                    'MODE_NON_NEGOTIABLES', 'MODE_IMPORTED_TRIGGERS', 'MODE_PLAYBOOKS', 'MODE_PRINCIPLES'}
        required.update(layout.destination_directory for layout in LAYOUTS.values() if layout.destination_directory)
        missing = sorted(name for name in required if not isinstance(getattr(locations, name, None), str))
        if missing:
            raise ValueError('locations.py has no string value for ' + ', '.join(missing))
        helper = CHECKOUT / 'mmw-v2' / 'skills' / locations.UI_ACCEPTANCE_REFUSAL_PY
        refusal_message = load_module('import_refusal', helper).refusal
        root = Path(args.root).resolve() if args.root else CHECKOUT
        if any(char in args.batch for char in ('\t', '\n', '\r')):
            parser.error('--batch must be one TSV cell')
        if args.refresh and (args.type or args.name or args.dry_run or args.batch != 'on-demand'):
            parser.error('--refresh takes only --root')
        if not args.refresh and args.type not in TYPES:
            unavailable(f'unknown type {args.type!r}', 'the importer knows eight component types',
                        'Choose a type from ' + ', '.join(TYPES) + ' and rerun.')
        if not args.refresh and not args.name:
            parser.error('type and name are required')
        subtree = (root / 'mmw-v2' / 'skills' / locations.PSTACK_DIRECTORY).resolve()
        if not subtree.is_dir():
            unavailable(f'{subtree}: subtree does not exist', 'there are no source components',
                        'Add the pstack squash subtree before importing.')
        importer = Importer(root, locations, args.batch)
        if args.refresh:
            return importer.refresh()
        importer.run(Component(args.type, args.name), args.dry_run)
        return 0
    except ImportRefusal as exc:
        print(refusal_message(*exc.args, limit=sys.maxsize), file=sys.stderr)
        return exc.code
    except (OSError, UnicodeError, ValueError) as exc:
        if refusal_message is None:
            print(f'Importer support could not load: {exc}; its registry or refusal helper is unreadable. '
                  'Restore the checkout support files and rerun.', file=sys.stderr)
        else:
            print(refusal_message(f'Import could not run: {exc}',
                                  'a required file or registry is unreadable.',
                                  'Restore the named file and rerun.', limit=sys.maxsize), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
