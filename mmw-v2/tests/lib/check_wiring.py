#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check destinations and directions of MMW's cross-file connections.

Only product scripts and skill text are inputs; tests and research are not.
The class policy is the batch switch, not a register of individual exceptions.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import json
import difflib
import subprocess
import re

from skill_text import (MODE_DIR, MODE_ROOT, TextError, anchors, classify, frontmatter,
                        installed_skills, normalize_title, read_imports, markdown_units,
                        component_root, sentences)

# class: (fail now, batch in which it must fail)
CLASS_POLICY = {
    1: (True, 'B0'),
    2: (False, 'B1'),
    3: (False, 'B2 end'),
    5: (False, 'B1'),
    6: (False, 'B2 end'),
    7: (False, 'B1'),
    8: (True, 'B0'),
    9: (False, 'B1'),
    10: (True, 'B0'),
    '10 registry': (False, 'B2 end'),
    11: (False, 'B2 end'),
    12: (False, 'B2'),
}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: int
    message: str
    report_only: bool = False
    policy: int | str | None = None


class Wiring:
    def __init__(self, root, test_root=False):
        self.root = root.resolve()
        self.test_root = test_root
        self.mode = self.root / MODE_ROOT
        self.findings = []
        self.edges = set()
        self.objects = set()
        self.session_templates = []
        self.imports = read_imports(self.root)
        self.skills = installed_skills(self.root)
        candidates = [self.mode / 'scripts/locations.py',
                      self.root / 'mmw-v2/skills/dispatch/scripts/locations.py']
        registry = next((p for p in candidates if p.is_file()), None)
        if registry is None:
            raise TextError('locations.py not found in either candidate')
        self.registry = registry
        tree = ast.parse(registry.read_text(encoding='utf-8'))
        self.registry_lines = {n.value: n.lineno for n in ast.walk(tree)
                               if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        # Evaluate data-only assignments; no product imports or calls.
        allowed = (ast.Module, ast.Expr, ast.Constant, ast.Assign, ast.Dict, ast.Tuple,
                   ast.List, ast.Set, ast.Name, ast.Load, ast.Store, ast.Subscript,
                   ast.Starred, ast.UnaryOp, ast.USub, ast.BinOp, ast.Add)
        if any(not isinstance(n, allowed) for n in ast.walk(tree)):
            raise TextError('locations.py is not a data-only registry')
        self.data = {}
        exec(compile(tree, str(registry), 'exec'), {'__builtins__': {}}, self.data)
        self.playbooks = self.data.get('PLAYBOOK_ANCHORS')
        if not isinstance(self.playbooks, dict) or any(
                not isinstance(k, str) or not isinstance(v, (tuple, list)) or
                any(not isinstance(x, str) for x in v) for k, v in self.playbooks.items()):
            raise TextError('locations.py has no valid PLAYBOOK_ANCHORS')
        self.sections = self.data.get('MODE_SECTIONS', self.data.get('MODE_ANCHORS', ()))
        if not isinstance(self.sections, (tuple, list)) or any(not isinstance(s, str) for s in self.sections):
            raise TextError('locations.py mode sections are not a sequence of titles')
        positions = self.data.get('WHERE_ROWS', {})
        if not isinstance(positions, dict) or any(
                not isinstance(rows, dict) or any(not isinstance(row, dict) for row in rows.values())
                for rows in positions.values()):
            raise TextError('locations.py WHERE_ROWS is not a role/position mapping')
        roles_path = self.root / 'mmw-v2/skills/dispatch/roles.json'
        self.roles_text = roles_path.read_text(encoding='utf-8')
        self.roles = json.loads(self.roles_text)
        if not isinstance(self.roles, dict) or not self.roles or any(
                not isinstance(v, dict) or not isinstance(v.get('wakes', {}), dict) or
                not isinstance(v.get('playbook', v.get('skill')), str)
                for v in self.roles.values()):
            raise TextError('roles.json is not a role mapping')
        self.files = self.scan_files()

    def scan_files(self):
        result = {}
        mmw = self.root / 'mmw-v2'
        for path in sorted(mmw.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if 'tests' in path.relative_to(mmw).parts or '__pycache__' in path.parts:
                continue
            skill_md = bool(re.match(r'mmw-v2/(?:skills|upstream[^/]*/skills)/', rel))
            if path.suffix in ('.py', '.sh') or (path.suffix == '.md' and skill_md):
                result[rel] = path.read_text(encoding='utf-8')
        for path in sorted((self.root / '.mmw/playbooks').rglob('*.md')):
            result[path.relative_to(self.root).as_posix()] = path.read_text(encoding='utf-8')
        result['mmw-v2/skills/dispatch/roles.json'] = self.roles_text
        return result

    def add(self, path, line, category, message, report_only=False, policy=None):
        self.objects.add(category)
        finding = Finding(path, line, category, message, report_only, policy)
        if finding not in self.findings:
            self.findings.append(finding)

    def edge(self, path, target, category):
        self.objects.add(category)
        self.edges.add((path, target, category))

    def pointer(self, path, line, slug, title):
        target = f'{MODE_DIR} {slug}#{title}' if slug else f'{MODE_DIR}#{title}'
        self.edge(path, target, 1)
        registered = self.playbooks.get(slug, ()) if slug else self.sections
        if title not in registered:
            self.add(path, line, 1, f'{target} is not registered in locations.py')
            return
        file = self.mode / 'playbooks' / (slug + '.md') if slug else self.mode / 'SKILL.md'
        rel = file.relative_to(self.root).as_posix()
        if classify(rel, self.imports).imported:
            self.add(path, line, 1, f'{target} points to an imported playbook')
        elif not file.is_file():
            self.add(path, line, 1, f'pending {slug or MODE_DIR} (not built yet)', True)
        else:
            text = file.read_text(encoding='utf-8')
            valid = {a.title for a in anchors(text) if
                     (not slug or re.match(r'\s*(?:#### |(?:\d+[.)] )?\*\*)',
                                          text.splitlines()[a.start-1]))}
            if normalize_title(title) not in valid:
                self.add(path, line, 1, f'{target} has no step or section in {rel}')

    def pointers(self):
        pattern = re.compile(r'\b' + re.escape(MODE_DIR) +
                             r'(?: ([a-z][a-z0-9-]*))?#([^`"\'\n<>}]+)')
        for path, text in self.files.items():
            for match in pattern.finditer(text):
                slug = match.group(1) or ''
                raw = match.group(2).strip()
                if any(c in raw for c in ('{', '$')):
                    continue
                # A literal may be followed by BETWEEN's range or a note.
                raw = re.split(r' \.\. #| · |[.;]', raw)[0].strip()
                title = raw
                self.pointer(path, text.count('\n', 0, match.start()) + 1, slug, title)
        path = 'mmw-v2/skills/dispatch/roles.json'
        for role, row in self.roles.items():
            slug = row.get('playbook')
            if not slug:
                continue
            if slug not in self.playbooks:
                self.add(path, 1, 1, f'{role} playbook {slug} is not registered')
            for title in [row['entry']] if 'entry' in row else []:
                self.pointer(path, 1, slug, title)
            for event, title in row.get('wakes', {}).items():
                if not isinstance(title, str):
                    raise TextError(f'roles.json {role}/{event} has no step title')
                line = next((i for i, s in enumerate(self.roles_text.splitlines(), 1)
                             if json.dumps(event) in s), 1)
                self.pointer(path, line, slug, title)
        for role, rows in self.data.get('WHERE_ROWS', {}).items():
            for row in rows.values():
                slug = row.get('playbook', self.roles.get(role, {}).get('playbook'))
                for key in ('step', 'until'):
                    if slug and key in row:
                        self.pointer(self.registry.relative_to(self.root).as_posix(),
                                     self.registry_lines.get(row[key], 1), slug, row[key])

    @staticmethod
    def python_text(node, values=None):
        values = values or {}
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return ''.join(Wiring.python_text(v, values) for v in node.values)
        if isinstance(node, ast.FormattedValue):
            return Wiring.python_text(node.value, values) or '<value>'
        if isinstance(node, ast.Name):
            return values.get(node.id, '<value>')
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return Wiring.python_text(node.left, values) + Wiring.python_text(node.right, values)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == 'join' and node.args:
                sep = Wiring.python_text(node.func.value, values)
                arg = node.args[0]
                if isinstance(arg, (ast.List, ast.Tuple)):
                    return sep.join(Wiring.python_text(v, values) for v in arg.elts)
                return '<value>' + sep + '<value>'
            if node.func.attr == 'format':
                return Wiring.python_text(node.func.value, values)
        return '<value>'

    def template(self, path, line, text, legacy=False):
        self.edge(path, 'live session', 8)
        self.session_templates.append((path, line, text))
        if '\n' in text or '\r' in text:
            self.add(path, line, 8, 'session template contains a newline' +
                     (' (B2 startup conversion)' if legacy else ''), legacy)

    def templates(self):
        for path, text in self.files.items():
            if path.endswith('.py'):
                tree = ast.parse(text)
                values = {}
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value:
                        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                        for target in targets:
                            if isinstance(target, ast.Name):
                                values[target.id] = self.python_text(node.value, values)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'wake_text':
                        for child in ast.walk(node):
                            if isinstance(child, ast.Return) and child.value:
                                self.template(path, child.lineno, self.python_text(child.value, values))
                    if isinstance(node, ast.Dict) and Path(path).name in ('relay.py', 'watchdog.py', 'turn-guard.py'):
                        for key, value in zip(node.keys, node.values):
                            if isinstance(key, ast.Constant) and key.value == 'text':
                                self.template(path, value.lineno, self.python_text(value, values))
                    if isinstance(node, ast.Call) and Path(path).name in ('relay.py', 'watchdog.py'):
                        callee = node.func.id if isinstance(node.func, ast.Name) else (
                            node.func.attr if isinstance(node.func, ast.Attribute) else '')
                        if callee in ('send', 'send_text') and len(node.args) >= 3:
                            self.template(path, node.lineno, self.python_text(node.args[-1], values))
                    if isinstance(node, (ast.Constant, ast.JoinedStr)):
                        value = self.python_text(node, values)
                        if value.startswith('MMW turn guard:'):
                            self.template(path, node.lineno, value)
            elif path.endswith('/dispatch.sh'):
                self.shell_templates(path, text)

    @staticmethod
    def shell_words(text, base_line=1):
        """Lex shell words without running substitutions or reading heredoc bodies.

        Command substitutions are also lexed, so a start_session in $(...) is
        inspected exactly like a bare call. Quotes remain part of each word.
        """
        words, substitutions = [], []
        i, line = 0, base_line
        while i < len(text):
            if text.startswith('\\\n', i):
                line += 1
                i += 2
                continue
            if text[i].isspace() or text[i] in ';|&()':
                if text[i] == '\n':
                    words.append(('\n', line))
                    line += 1
                i += 1
                continue
            if text[i] == '#':
                end = text.find('\n', i)
                i = len(text) if end == -1 else end
                continue
            start, start_line, quote = i, line, None
            while i < len(text):
                char = text[i]
                if char == '\\':
                    line += text[i:i+2].count('\n')
                    i += 2
                    continue
                if text.startswith('$(', i) and quote != "'":
                    j, depth, inner_quote = i+2, 1, None
                    while j < len(text) and depth:
                        c = text[j]
                        if c == '\\':
                            j += 2
                            continue
                        if c in "\"'":
                            inner_quote = None if inner_quote == c else c if inner_quote is None else inner_quote
                        elif inner_quote is None:
                            if c == '(':
                                depth += 1
                            elif c == ')':
                                depth -= 1
                        j += 1
                    substitutions.extend(Wiring.shell_words(text[i+2:j-1], line))
                    line += text[i:j].count('\n')
                    i = j
                    continue
                if char in "\"'":
                    quote = None if quote == char else char if quote is None else quote
                elif quote is None and (char.isspace() or char in ';|&()'):
                    break
                if char == '\n':
                    line += 1
                i += 1
            if i == start:
                i += 1
            else:
                words.append((text[start:i], start_line))
        return words + substitutions

    @staticmethod
    def shell_value(raw, variables):
        raw = raw.replace('\\\n', '')
        raw = re.sub(r"\$'([^']*)'", lambda m: m[1].replace('\\n', '\n').replace('\\r', '\r'), raw)
        raw = re.sub(r'\$\(.*?\)', '<value>', raw, flags=re.S)
        raw = raw.replace('"', '').replace("'", '')
        refs = list(re.finditer(r'\$(?:\{([A-Za-z_][\w]*)\}|([A-Za-z_][\w]*))', raw))
        results = [(raw, None)]
        for ref in reversed(refs):
            options = variables.get(ref[1] or ref[2], [('<value>', None)])
            results = [(value[:ref.start()] + replacement + value[ref.end():], source or origin)
                       for value, origin in results for replacement, source in options]
        return results

    def shell_templates(self, path, text):
        words = self.shell_words(text)
        functions = [(text.count('\n', 0, m.start()) + 1, m[1]) for m in re.finditer(r'^([a-zA-Z_]\w*)\(\)\s*\{', text, re.M)]
        def function_at(line):
            return next((name for pos, name in reversed(functions) if pos <= line), '')
        scopes = {}
        for word, line in words:
            assignments = scopes.setdefault(function_at(line), {})
            match = re.match(r'^(?:local )?([A-Za-z_]\w*)=(.*)$', word, re.S)
            if match:
                for value, origin in self.shell_value(match[2], assignments):
                    assignments.setdefault(match[1], []).append((value, line))
        legacy_sources = {}
        for function, variables in scopes.items():
            for value, source in variables.get('prompt', []):
                for expected_function, prefix in (
                        ('start_one', 'Use the implement skill'),
                        ('start_one', 'Use the code-review skill'),
                        ('advise_one', 'Use the advisor skill')):
                    if function == expected_function and value.startswith(prefix):
                        key = (function, prefix)
                        legacy_sources[key] = min(source, legacy_sources.get(key, source))
        for i, (word, line) in enumerate(words):
            if word not in ('start_session', 'runner'):
                continue
            function = function_at(line)
            assignments = scopes.get(function, {})
            if word == 'start_session':
                index = i + 5
            elif i+1 < len(words) and words[i+1][0] == 'send' and function == 'resume_one':
                index = i + 3
            else:
                continue
            if index >= len(words):
                continue
            for value, source in self.shell_value(words[index][0], assignments):
                legacy = any(function == f and value.startswith(prefix) and source == origin
                             for (f, prefix), origin in legacy_sources.items())
                self.template(path, source or line, value, legacy)

    def path_literal(self, source, line, target):
        target = target.resolve()
        label = target.relative_to(self.root).as_posix() if target.is_relative_to(self.root) else str(target)
        self.edge(source, label, 10)
        if not target.exists():
            self.add(source, line, 10, f'{label} does not exist')
        elif (self.root / source).resolve() != self.registry:
            self.add(source, line, 10, f'{label} is not obtained through locations.py', policy='10 registry')
            origin = component_root(source)
            if origin != component_root(label):
                self.add(source, line, 3, f'{label} is a cross-directory path not obtained through locations.py')

    def paths(self):
        quoted_chain = r'(?:\s*/\s*["\'][a-zA-Z0-9_./-]+["\'])+'
        patterns = [
            (re.compile(r'["\']skills["\']' + quoted_chain), 'skills'),
            (re.compile(r'\b_?HERE\.parents\[(\d+)\]' + quoted_chain), 'parents'),
            (re.compile(r'(?<![\w/])(?:mmw-v2/)?skills/([a-zA-Z0-9_.-]+)/scripts(?:/[a-zA-Z0-9_./-]+)?'), 'literal'),
            (re.compile(r'\$\(dirname\s+["\']?\$HERE["\']?\)/([a-zA-Z0-9_./-]+)'), 'dirname'),
            (re.compile(r'\$(?:SKILL_ROOT|\{SKILL_ROOT\})/scripts/([a-zA-Z0-9_./-]+)'), 'skillroot'),
        ]
        for source, text in self.files.items():
            if not source.endswith(('.py', '.sh')):
                continue
            file = self.root / source
            skill = re.match(r'(mmw-v2/skills/[^/]+)/', source)
            for pattern, kind in patterns:
                for match in pattern.finditer(text):
                    parts = re.findall(r'/\s*["\']([^"\']+)["\']', match[0])
                    if kind == 'skills':
                        subtree = re.match(r'(mmw-v2/upstream[^/]*)/', source)
                        target = self.root / (subtree[1] if subtree else 'mmw-v2') / 'skills'
                        for part in parts:
                            target /= part
                    elif kind == 'parents':
                        target = file.parent.parents[int(match[1])]
                        for part in parts:
                            target /= part
                    elif kind == 'literal':
                        subtree = re.match(r'(mmw-v2/upstream[^/]*)/', source)
                        base = self.root / (subtree[1] if subtree else 'mmw-v2')
                        target = base / match[0].removeprefix('mmw-v2/')
                    elif kind == 'dirname':
                        target = file.parent.parent / match[1]
                    elif skill:
                        target = self.root / skill[1] / 'scripts' / match[1]
                    else:
                        continue
                    self.path_literal(source, text.count('\n', 0, match.start()) + 1, target)

    def component_files(self):
        return {p: t for p, t in self.files.items() if p.endswith('.md') and
                classify(p, self.imports).kind in ('mode', 'playbook', 'mode-reference')}

    def resolve_components(self):
        for path, text in self.component_files().items():
            for match in re.finditer(r'`((?:playbooks|principles|references|scripts)/[^`\s]+)(?:\s+([^`]+))?`', text):
                literal = match[1].rstrip('.')
                target = (self.mode if path.startswith(MODE_ROOT) else (self.root / path).parent) / literal
                self.edge(path, target.relative_to(self.root).as_posix(), 2)
                if not target.is_file():
                    self.add(path, text.count('\n', 0, match.start())+1, 2, f'{literal} does not exist')
                elif match[2] and literal.startswith('scripts/'):
                    command = match[2].split()[0]
                    names = {name for _, name in self.public_commands(str(target), target.read_text(encoding='utf-8'))}
                    if re.fullmatch(r'[a-z][\w-]*', command) and command not in names:
                        self.add(path, text.count('\n', 0, match.start())+1, 2,
                                 f'{literal} has no subcommand {command}')
            for match in re.finditer(r'(?:the\s+`?([a-z][\w-]*)`?\s+skill|(?:use|Use) /([a-z][\w-]*))', text):
                name = match[1] or match[2]
                self.edge(path, name, 2)
                if name not in self.skills:
                    names_file = self.mode / 'references/pstack-names.md'
                    mapped = False
                    if classify(path, self.imports).imported and names_file.is_file():
                        for row in names_file.read_text(encoding='utf-8').splitlines():
                            cells = [c.strip().strip('`') for c in row.strip('|').split('|')]
                            if cells and cells[0] == name and any(c in self.skills for c in cells[1:]):
                                mapped = True
                    if not mapped:
                        self.add(path, text.count('\n', 0, match.start())+1, 2, f'{name} is not in skills.txt or pstack-names.md')
                elif not (self.root / self.skills[name] / 'SKILL.md').is_file():
                    self.add(path, text.count('\n', 0, match.start())+1, 2, f'{name}/SKILL.md does not exist')

    def directions(self):
        constants = [v for k, v in self.data.items() if isinstance(v, (str, tuple)) and
                     k not in ('PLAYBOOK_ANCHORS', 'MODE_SECTIONS', 'MODE_ANCHORS')]
        literal_anchors = {x for v in constants for x in (v if isinstance(v, tuple) else [v])
                           if isinstance(x, str) and (x.startswith('## ') or x.endswith(' OK'))}
        for path, text in self.files.items():
            if not path.endswith(('.py', '.sh')) or (self.root / path).resolve() == self.registry:
                continue
            capability = bool(re.match(r'mmw-v2/skills/(?!' + re.escape(MODE_DIR) + r'/)[^/]+/scripts/', path))
            if capability:
                for match in re.finditer(r'(?:mmw/scripts/(?:dispatch\.sh|ticket_state\.py)|\bmmw\s+[a-z][a-z-]*\b)', text):
                    self.edge(path, match[0], 3)
                    self.add(path, text.count('\n', 0, match.start())+1, 3,
                             'capability script calls a mode command directly')
            for literal in literal_anchors:
                for match in re.finditer(re.escape(literal), text):
                    self.edge(path, 'locations.py#' + literal, 3)
                    self.add(path, text.count('\n', 0, match.start())+1, 3,
                             f'{literal} is a text anchor not obtained through locations.py')
            if capability and re.search(r'["\']events\.py["\']', text):
                self.add(path, 1, 3, 'events.py path is not obtained through locations.py')

    def principles(self):
        path = MODE_ROOT + '/SKILL.md'
        text = self.files.get(path, '')
        for line, raw in enumerate(text.splitlines(), 1):
            match = re.match(r'\s*- \*\*([^*]+)\*\* \(\*\*(principle-[\w-]+)\*\*\)\.\s*(.*)', raw)
            if not match:
                continue
            display, slug, applies = match.groups()
            file = self.mode / 'principles' / (slug + '.md')
            self.edge(path, file.relative_to(self.root).as_posix(), 5)
            if not file.is_file():
                self.add(path, line, 5, f'{slug} has no principle file')
                continue
            content = file.read_text(encoding='utf-8')
            data, _, _ = frontmatter(content)
            first = next((u.text for u in sentences(data.get('description', ''))), '')
            h1 = re.search(r'^# (.+)$', content, re.M)
            if not h1 or display != h1[1] or applies != first:
                self.add(path, line, 5, f'{slug} display or applicability does not match H1 and description')
        for path, text in self.component_files().items():
            for match in re.finditer(r'\((principle-[\w-]+)\)', text):
                slug = match[1]
                self.edge(path, slug, 5)
                if not (self.mode / 'principles' / (slug + '.md')).is_file():
                    self.add(path, text.count('\n', 0, match.start())+1, 5, f'{slug} has no principle file')

    def routes(self):
        collections = [(self.mode / 'playbooks', self.mode / 'SKILL.md'),
                       (self.root / '.mmw/playbooks', self.root / '.mmw/playbooks/INDEX.md')]
        for directory, index in collections:
            books = sorted(directory.glob('*.md'))
            if not books:
                continue
            content = index.read_text(encoding='utf-8') if index.is_file() else ''
            for book in books:
                if book.name == 'INDEX.md':
                    continue
                source = index.relative_to(self.root).as_posix()
                self.edge(source, book.relative_to(self.root).as_posix(), 7)
                rows = [i for i, row in enumerate(content.splitlines(), 1)
                        if re.search(r'(?<![\w-])' + re.escape(book.name) + r'(?![\w.-])', row)]
                if len(rows) != 1:
                    self.add(source, rows[0] if rows else 1, 7,
                             f'{book.name} has {len(rows)} routing rows; expected 1')

    def invocation(self):
        entries = (self.root / 'mmw-v2/skills.txt').read_text(encoding='utf-8') if (self.root / 'mmw-v2/skills.txt').exists() else ''
        for source, text in self.component_files().items():
            for name, skill_path in self.skills.items():
                if not re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', text):
                    continue
                if '/upstream' not in skill_path:
                    continue
                self.edge(source, skill_path, 9)
                entry = next((s for s in entries.splitlines() if s.split() and
                              s.split()[0].rsplit('/', 1)[-1] == name), '')
                if '+model-invoked' not in entry:
                    self.add(source, 1, 9, f'{name} needs +model-invoked in skills.txt')
                # Copies are a product tree, not the current machine's installation.
                copy_home = self.root if self.test_root else Path.home()
                for copy in (copy_home / '.mmw/skill-copies' / name,):
                    if not copy.is_dir():
                        continue
                    skill = copy / 'SKILL.md'
                    if skill.is_file() and 'disable-model-invocation' in frontmatter(skill.read_text())[0]:
                        self.add(source, 1, 9, f'{copy.name} installation copy still has invocation switch')
                    policy = copy / 'agents/openai.yaml'
                    if policy.is_file() and re.search(r'^policy:', policy.read_text(), re.M):
                        self.add(source, 1, 9, f'{copy.name} installation copy still has policy')
        for name, skill_path in self.skills.items():
            if not skill_path.startswith('mmw-v2/skills/'):
                continue
            file = self.root / skill_path / 'SKILL.md'
            if file.is_file() and 'disable-model-invocation' in frontmatter(file.read_text())[0]:
                self.add(skill_path + '/SKILL.md', 1, 9, 'owned skill has an invocation switch')

    def events(self):
        relay = next((t for p, t in self.files.items() if p.endswith('/relay.py')), '')
        emitted = []
        if relay:
            tree = ast.parse(relay)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if any(isinstance(t, ast.Name) and t.id == 'WAKES' for t in targets) and isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if not isinstance(key, ast.Constant) or not isinstance(value, ast.Dict):
                                continue
                            recipient = next((ast.unparse(v).strip("'\"") for k, v in zip(value.keys, value.values)
                                              if isinstance(k, ast.Constant) and k.value == 'to'), '')
                            roles = ('worker', 'adopting-worker') if recipient == 'WORKER' else (
                                'night-orchestrator', 'one-ticket-orchestrator', 'adopting-worker')
                            emitted.extend((r, key.value, key.lineno) for r in roles if r in self.roles)
        main_roles = [r for r in ('night-orchestrator', 'one-ticket-orchestrator', 'adopting-worker')
                      if r in self.roles]
        if 'relay.recovered' in relay:
            emitted.extend((r, 'relay.recovered', 1) for r in main_roles)
        for path, content in self.files.items():
            if path.endswith('/watchdog.py'):
                for node in ast.walk(ast.parse(content)):
                    if not isinstance(node, ast.Dict):
                        continue
                    for key, value in zip(node.keys, node.values):
                        if isinstance(key, ast.Constant) and key.value == 'text':
                            template = self.python_text(value)
                            if template.startswith('watchdog:'):
                                emitted.extend((r, template.split(';', 1)[0], 1) for r in main_roles)
            elif path.endswith('/turn-guard.py') and 'MMW turn guard:' in content:
                emitted.extend((r, 'MMW turn guard:', 1) for r in main_roles)
            elif path.endswith('/dispatch.sh') and 'resume_one()' in content:
                emitted.extend((r, 'resume', 1) for r in ('worker', 'adopting-worker') if r in self.roles)
        for role, row in self.roles.items():
            emitted.extend((role, event, 1) for event in row.get('wakes', {}) if event != '*')
        for role, event, line in sorted(set(emitted)):
            row = self.roles[role]
            wakes = row.get('wakes', {})
            step = wakes.get(event, wakes.get('*'))
            target = self.mode / 'playbooks' / (row.get('playbook', '') + '.md')
            self.edge(f'{role}/{event}', f'{row.get("playbook")}/{step}', 6)
            if step is None:
                self.add('mmw-v2/skills/dispatch/roles.json', line, 6,
                         f'{role}/{event} has no registered handler')
            elif not target.is_file():
                self.add('mmw-v2/skills/dispatch/roles.json', line, 6,
                         f'{role}/{event} handler {step} is not built')
            else:
                content = target.read_text(encoding='utf-8')
                handlers = [a for a in anchors(content) if a.title == normalize_title(step)]
                if len(handlers) != 1:
                    self.add(target.relative_to(self.root).as_posix(), 1, 6,
                             f'{role}/{event} has {len(handlers)} handlers; expected 1')

    @staticmethod
    def public_commands(path, text):
        if path.endswith('/dispatch.sh'):
            headers = list(re.finditer(r'case\s+["\']?\$(?:1|\{1:-\})["\']?\s+in', text))
            if not headers:
                return []
            start = headers[-1].end()
            depth = 1
            result = []
            offset = start
            for row in text[start:].splitlines(keepends=True):
                branch = re.match(r'^\s*([\w|-]+)\)', row)
                if depth == 1 and branch:
                    result.extend((offset + branch.start(), name) for name in branch[1].split('|'))
                depth += len(re.findall(r'\bcase\b[^\n;]*?\bin\b', row))
                depth -= len(re.findall(r'\besac\b', row))
                if depth == 0:
                    break
                offset += len(row)
            return result
        if path.endswith('.py'):
            return [(m.start(), m[1]) for m in re.finditer(r'add_parser\(["\']([\w-]+)', text)]
        return []

    def commands(self):
        components = self.component_files()
        for path, text in self.files.items():
            if not path.endswith(('/dispatch.sh', '/ticket_state.py')):
                continue
            for offset, name in self.public_commands(path, text):
                self.edge(path + '#' + name, 'command consumers', 11)
                pattern = re.compile(re.escape(Path(path).name) + r'["\'`\s]+(?:<[^>]+>\s+)?' + re.escape(name) + r'\b')
                consumers = [p for p, t in self.files.items() if p != path and
                             (p.endswith(('.py', '.sh')) or p in components) and pattern.search(t)]
                if not consumers:
                    self.add(path, text.count('\n', 0, offset)+1, 11, f'{name} has no command consumer')

    def frozen_paths(self):
        marker = (Path.home() / '.mmw/installed-root' if
                  not self.test_root else
                  self.root / '.mmw/installed-root')
        installed = Path(marker.read_text(encoding='utf-8').strip()).expanduser().resolve() if marker.is_file() else None
        inputs = self.session_templates + [('mmw-v2/skills/dispatch/roles.json', 1, self.roles_text)]
        for path, line, text in inputs:
            for match in re.finditer(r'(?:/|~/)[^\s"\'`<>]*mmw-v2/[^\s"\'`<>]+', text):
                literal = match[0].rstrip('.,;')
                target = Path(literal).expanduser().resolve()
                self.edge(path, literal, 12)
                if installed is None or not target.is_relative_to(installed):
                    self.add(path, line, 12, f'{literal} is not under the installed-root checkout')

    def upstream_differences(self):
        """Compare skill units with the last squash's upstream tree.

        A merge-note registers a file/section, not a blanket permission granted
        merely by the presence of a note. Invocation-switch pairing is registered
        by merge-notes/README.md. Content-owning skills are registered there too.
        """
        for subtree in sorted((self.root / 'mmw-v2').glob('upstream*')):
            paths = [(p, t) for p, t in self.files.items()
                     if p.startswith(subtree.relative_to(self.root).as_posix() + '/skills/') and p.endswith('.md')]
            if not paths:
                continue
            relative = subtree.relative_to(self.root).as_posix()
            result = subprocess.run(['git', '-C', str(self.root), 'log', '-1', '--format=%H',
                                     '--grep', f"Squashed '{relative}/'"], capture_output=True, text=True)
            if result.returncode or not result.stdout.strip():
                for path, _ in paths:
                    self.add(path, 1, 3, f'{relative} has no squash original to compare')
                continue
            revision = result.stdout.strip()
            for path, content in paths:
                upstream_path = path.removeprefix(relative + '/')
                original = subprocess.run(['git', '-C', str(self.root), 'show',
                                           f'{revision}:{upstream_path}'], capture_output=True, text=True)
                if original.returncode:
                    self.add(path, 1, 3, f'{upstream_path} has no squash original')
                    continue
                old = markdown_units(original.stdout)
                new = markdown_units(content)
                if [u.identity for u in old] == [u.identity for u in new]:
                    continue
                root = component_root(path)
                name = Path(root).name
                note = self.root / 'mmw-v2/merge-notes' / (name + '.md')
                notes = note.read_text(encoding='utf-8') if note.is_file() else ''
                general = self.root / 'mmw-v2/merge-notes/README.md'
                registry = general.read_text(encoding='utf-8') if general.is_file() else ''
                file_name = str(Path(path).relative_to(root))
                owns_content = name in ('code-review', 'implement', 'to-tickets') and name in registry
                registered_file = file_name in notes or Path(path).name in notes
                file_notes = notes
                headings = list(re.finditer(r'^(#{2,4}) (.+)$', notes, re.M))
                file_heading = next((h for h in headings if file_name in h[2] or Path(path).name in h[2]), None)
                if file_heading:
                    end = next((h.start() for h in headings if h.start() > file_heading.start() and
                                len(h[1]) <= len(file_heading[1])), len(notes))
                    file_notes = notes[file_heading.end():end]
                section_titles = [a for a in anchors(content)]
                old_sections = anchors(original.stdout)
                matcher = difflib.SequenceMatcher(a=[u.identity for u in old], b=[u.identity for u in new], autojunk=False)
                for operation, a, b, c, d in matcher.get_opcodes():
                    if operation == 'equal':
                        continue
                    changed = new[c:d] or old[a:b]
                    line = new[c].line if c < len(new) else len(content.splitlines()) or 1
                    self.edge(path, f'{revision}:{upstream_path}', 3)
                    # The switch removal is the documented host-neutral pairing.
                    switches = all(u.key == 'disable-model-invocation' for u in changed)
                    scopes = section_titles if new[c:d] else old_sections
                    title = next((s.title for s in reversed(scopes) if s.start <= changed[0].line), '')
                    section_registered = bool(title and title in file_notes)
                    whole_file = bool(re.search(r'(全文|所有段落|whole file|entire file)', file_notes))
                    if not (owns_content or (switches and 'disable-model-invocation' in registry) or
                            (registered_file and (section_registered or whole_file))):
                        self.add(path, line, 3, f'upstream difference at {file_name}#{title} is not registered in its merge-note')

    def run(self):
        self.pointers()
        self.templates()
        self.paths()
        self.resolve_components()
        self.directions()
        self.upstream_differences()
        self.principles()
        self.events()
        self.routes()
        self.invocation()
        self.commands()
        self.frozen_paths()
        return self.findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='test fixture tree; machine installation state is not read')
    parser.add_argument('--graph', action='store_true')
    args = parser.parse_args()
    try:
        check = Wiring(args.root or Path(__file__).resolve().parents[3], test_root=args.root is not None)
        findings = check.run()
    except (OSError, ValueError, SyntaxError, TypeError, KeyError, NameError) as exc:
        print(f'wiring check cannot read its registry: {' '.join(str(exc).splitlines())}; run bash mmw-v2/install.sh --check')
        return 2
    failures = [f for f in findings if not f.report_only and
                CLASS_POLICY[f.policy or f.category][0]]
    if args.graph:
        for source, target, category in sorted(check.edges):
            print(f'{source} -> {target} : {category}')
        return 1 if failures else 0
    if failures:
        print(f'wiring check failed: {len(failures)} connections do not resolve')
        print('Next: correct the named connection or its registered destination and rerun.')
        print('Why: a session must reach an existing, permitted component.')
    for f in findings:
        report = f not in failures
        print(f'{"report: " if report else ""}{f.path}:{f.line}: class {f.category} {f.message}')
    for category in CLASS_POLICY:
        if isinstance(category, int) and category not in check.objects:
            print(f'report: class {category}: no objects yet')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
