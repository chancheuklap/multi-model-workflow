#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check destinations and directions of MMW's cross-file connections.

Inputs are product scripts and skill text, excluding mmw-v2/tests and research.
The class policy is the batch switch, not a register of individual exceptions.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import json
import difflib
import importlib.util
import subprocess
import re

from skill_text import (MODE_DIR, MODE_ROOT, TextError, anchors, classify, frontmatter,
                        installed_skills, normalize_title, read_imports, markdown_units,
                        component_root, sentences, prose_mask, skill_mentions, skill_of_path)


@dataclass(frozen=True)
class Policy:
    fails: bool
    batch: str
    registry: Policy | None = None
    pending: Policy | None = None


# class: failure policy and the batch in which it must fail.
CLASS_POLICY = {
    1: Policy(True, 'B0'),
    2: Policy(True, 'B1'),
    3: Policy(True, 'B2 end'),
    5: Policy(True, 'B1'),
    6: Policy(True, 'B2 end'),
    7: Policy(True, 'B1', pending=Policy(True, 'B2 end')),
    8: Policy(True, 'B0'),
    9: Policy(True, 'B1'),
    10: Policy(True, 'B0', registry=Policy(True, 'B2 end')),
    11: Policy(True, 'B2 end'),
    12: Policy(True, 'B2'),
}


class RegistryError(TextError):
    """Only locations.py or roles.json cannot be read as a registry."""


def source_line(text, offset):
    return text.count('\n', 0, offset) + 1


def subtree_root(source):
    match = re.match(r'(mmw-v2/upstream[^/]*)/', source)
    return match[1] if match else 'mmw-v2'


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: int
    message: str
    report_only: bool = False
    registry_path: bool = False
    pending: bool = False


class Wiring:
    def __init__(self, root, test_root=False):
        self.root = root.resolve()
        self.test_root = test_root
        self.mode = self.root / MODE_ROOT
        self.findings = []
        self.edges = set()
        self.objects = set()
        self.session_templates = []
        self.python_trees = {}
        self.alert_templates = []
        try:
            self.read_registries()
        except (OSError, UnicodeError, ValueError, SyntaxError, TypeError, KeyError, NameError) as exc:
            raise RegistryError(str(exc)) from exc
        self.imports = read_imports(self.root)
        self.skills = installed_skills(self.root)
        self.files = self.scan_files()

    def read_registries(self):
        registry = self.mode / 'scripts/locations.py'
        if not registry.is_file():
            raise TextError(f'locations.py not found at {registry}')
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
        self.sections = self.data.get('MODE_SECTIONS', ())
        if not isinstance(self.sections, (tuple, list)) or any(not isinstance(s, str) for s in self.sections):
            raise TextError('locations.py mode sections are not a sequence of titles')
        positions = self.data.get('WHERE_ROWS', {})
        if not isinstance(positions, dict) or any(
                not isinstance(rows, dict) or any(not isinstance(row, dict) or any(key in row and not isinstance(row[key], str)
                                                   for key in ('step', 'until', 'playbook'))
                                               for row in rows.values())
                for rows in positions.values()):
            raise TextError('locations.py WHERE_ROWS is not a role/position mapping')
        roles_path = self.root / 'mmw-v2/skills/mmw/roles.json'
        self.roles_text = roles_path.read_text(encoding='utf-8')
        self.roles = json.loads(self.roles_text)
        if not isinstance(self.roles, dict) or not self.roles or any(
                not isinstance(v, dict) or not isinstance(v.get('wakes', {}), dict) or
                not isinstance(v.get('playbook', v.get('skill')), str) or
                ('entry' in v and not isinstance(v['entry'], str)) or
                any(not isinstance(k, str) or not isinstance(t, str) for k, t in v.get('wakes', {}).items())
                for v in self.roles.values()):
            raise TextError('roles.json is not a role mapping')

    def scan_files(self):
        result = {}
        mmw = self.root / 'mmw-v2'
        for path in sorted(mmw.rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if path.relative_to(mmw).parts[0] == 'tests' or '__pycache__' in path.parts:
                continue
            skill_md = bool(re.match(r'mmw-v2/(?:skills|upstream[^/]*/skills)/', rel))
            if path.suffix in ('.py', '.sh') or (path.suffix == '.md' and skill_md):
                result[rel] = path.read_text(encoding='utf-8')
        for path in sorted((self.root / '.mmw/playbooks').rglob('*.md')):
            result[path.relative_to(self.root).as_posix()] = path.read_text(encoding='utf-8')
        result['mmw-v2/skills/mmw/roles.json'] = self.roles_text
        return result

    def add(self, path, line, category, message, report_only=False, registry_path=False, pending=False):
        self.objects.add(category)
        finding = Finding(path, line, category, message, report_only, registry_path, pending)
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
                     (not slug or re.match(r'\s*(?:#### |(?:(?:\d+[.)]|[-*+]) )?\*\*)',
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
                self.pointer(path, source_line(text, match.start()), slug, raw)
        path = 'mmw-v2/skills/mmw/roles.json'
        for role, row in self.roles.items():
            slug = row.get('playbook')
            if not slug:
                continue
            if slug not in self.playbooks:
                self.add(path, 1, 1, f'{role} playbook {slug} is not registered')
            if 'entry' in row:
                self.pointer(path, 1, slug, row['entry'])
            for event, title in row.get('wakes', {}).items():
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

    def python_tree(self, path, text):
        if path not in self.python_trees:
            try:
                self.python_trees[path] = ast.parse(text, filename=path)
            except SyntaxError as exc:
                raise TextError(f'{path}:{exc.lineno}: cannot inspect invalid Python: {exc.msg}') from exc
        return self.python_trees[path]

    @cached_property
    def state_home(self):
        if self.test_root:
            return self.root / '.mmw'
        scripts = self.root / 'mmw-v2/skills' / self.data['MODE_SCRIPTS']
        spec = importlib.util.spec_from_file_location('wiring_statedir', scripts / 'statedir.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.home()

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
                tree = self.python_tree(path, text)
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
                                template = self.python_text(value, values)
                                self.alert_templates.append((path, value.lineno, template))
                                self.template(path, value.lineno, template)
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
            self.resume_templates(path, text)

    def resume_templates(self, path, text):
        # The public command's text argument is supplied by the caller, not by
        # resume_one's positional $2. Read written calls in scripts and skill text.
        for match in re.finditer(r'\bdispatch\.sh["\'`\s]+resume\s+(?:<[^>]+>|[^\s`]+)\s+', text):
            words = self.shell_words(text[match.end():], source_line(text, match.end()))
            if words:
                raw, line = words[0]
                for value, _ in self.shell_value(raw, {}):
                    self.template(path, line, value)

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
        functions = [(source_line(text, m.start()), m[1]) for m in re.finditer(r'^([a-zA-Z_]\w*)\(\)\s*\{', text, re.M)]
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
            if (component_root(source) == component_root(label) or
                    (subtree_root(source) != 'mmw-v2' and
                     subtree_root(source) == subtree_root(label))):
                return
            self.add(source, line, 10, f'{label} is not obtained through locations.py', registry_path=True)
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
                        target = self.root / subtree_root(source) / 'skills'
                        for part in parts:
                            target /= part
                    elif kind == 'parents':
                        target = file.parent.parents[int(match[1])]
                        for part in parts:
                            target /= part
                    elif kind == 'literal':
                        base = self.root / subtree_root(source)
                        target = base / match[0].removeprefix('mmw-v2/')
                    elif kind == 'dirname':
                        target = file.parent.parent / match[1]
                    elif skill:
                        target = self.root / skill[1] / 'scripts' / match[1]
                    else:
                        continue
                    self.path_literal(source, source_line(text, match.start()), target)

    def component_files(self):
        return {p: t for p, t in self.files.items() if p.endswith('.md') and
                classify(p, self.imports).kind in ('mode', 'playbook', 'mode-reference')}

    def model_mentions(self, path, text):
        steps = classify(path, self.imports).kind in ('mode', 'playbook')
        return [mention for mention in skill_mentions(text, self.skills, steps) if mention.by_model]

    def resolve_components(self):
        for path, text in self.component_files().items():
            masked = prose_mask(text)
            for match in re.finditer(r'`((?:playbooks|principles|references|scripts)/[^`\s]+)(?:\s+([^`]+))?`', masked):
                literal = match[1].rstrip('.')
                if '<' in literal or re.fullmatch(r'[A-Za-z]', Path(literal).stem):
                    continue
                name = skill_of_path(masked, match.start(), self.skills, already_masked=True)
                if name is not None and name not in self.skills:
                    continue
                base = (self.root / self.skills[name] if name is not None else
                        self.mode if path.startswith(MODE_ROOT) else (self.root / path).parent)
                target = base / literal
                label = target.relative_to(self.root).as_posix() if name is not None else literal
                self.edge(path, target.relative_to(self.root).as_posix(), 2)
                if not target.is_file():
                    self.add(path, source_line(text, match.start()), 2, f'{label} does not exist')
                elif match[2] and literal.startswith('scripts/'):
                    command = match[2].split()[0]
                    names = {name for _, name in self.public_commands(str(target), target.read_text(encoding='utf-8'))}
                    if re.fullmatch(r'[a-z][\w-]*', command) and command not in names:
                        self.add(path, source_line(text, match.start()), 2,
                                 f'{literal} has no subcommand {command}')
            mentions = [(mention.name, mention.line) for mention in self.model_mentions(path, text)]
            mentions.extend((match[1], source_line(text, match.start())) for match in
                            re.finditer(r'\b(?:use|Use) /([a-z][\w-]*)', masked))
            for name, line in mentions:
                self.edge(path, name, 2)
                if name not in self.skills:
                    self.add(path, line, 2, f'{name} is not in skills.txt')
                elif not (self.root / self.skills[name] / 'SKILL.md').is_file():
                    self.add(path, line, 2, f'{name}/SKILL.md does not exist')

    def directions(self):
        constants = [v for k, v in self.data.items() if isinstance(v, (str, tuple)) and
                     k not in ('PLAYBOOK_ANCHORS', 'MODE_SECTIONS')]
        literal_anchors = {x for v in constants for x in (v if isinstance(v, tuple) else [v])
                           if isinstance(x, str) and (x.startswith('## ') or x.endswith(' OK'))}
        for path, text in self.files.items():
            if not path.endswith(('.py', '.sh')):
                continue
            capability = bool(re.match(r'mmw-v2/skills/(?!' + re.escape(MODE_DIR) + r'/)[^/]+/scripts/', path))
            if capability:
                for match in re.finditer(r'(?:mmw/scripts/(?:dispatch\.sh|ticket_state\.py)|\bmmw\s+[a-z][a-z-]*\b)', text):
                    self.edge(path, match[0], 3)
                    self.add(path, source_line(text, match.start()), 3,
                             'capability script calls a mode command directly')
            # The registry declares anchors; only its consumers must obtain them there.
            if (self.root / path).resolve() == self.registry:
                continue
            for literal in literal_anchors:
                for match in re.finditer(re.escape(literal), text):
                    self.edge(path, 'locations.py#' + literal, 3)
                    self.add(path, source_line(text, match.start()), 3,
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
        for path, text in self.files.items():
            if not path.endswith('.md'):
                continue
            component = classify(path, self.imports)
            if component.kind not in (
                    'mode', 'playbook', 'mode-reference', 'principle'):
                continue
            masked = prose_mask(text)
            citations = list(re.finditer(r'\*\*(principle-[\w-]+)\*\*', masked))
            if component.imported:
                citations.extend(re.finditer(r'\((principle-[\w-]+)\)', masked))
            for match in citations:
                slug = match[1]
                self.edge(path, slug, 5)
                if not (self.mode / 'principles' / (slug + '.md')).is_file():
                    self.add(path, source_line(text, match.start()), 5, f'{slug} has no principle file')
            if component.imported:
                continue
            other_forms = []
            for match in re.finditer(r'(?<![\w/-])principle-[\w-]+', masked):
                if not any(citation.start() <= match.start() < citation.end()
                           for citation in citations):
                    other_forms.append(match)
            other_forms.extend(re.finditer(r'\bthe \*\*[^*<>\n]+\*\* principle(?![\w-])', masked))
            other_forms.extend(re.finditer(r'\]\([^\s)<>]*?/principle-[\w-]+\.md\)', masked))
            for match in sorted(other_forms, key=lambda match: match.start()):
                self.add(path, source_line(text, match.start()), 5,
                         f'{match[0]} is not the citation form **principle-<slug>**')

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
                    # Registered and unrouted is pending. Failure is the sub-policy,
                    # not a fixed report, so the same finding can start failing later.
                    if (not rows and directory == self.mode / 'playbooks'
                            and book.stem in self.playbooks):
                        self.add(source, 1, 7,
                                 f'pending route for {book.name} (not routed yet)', pending=True)
                    else:
                        self.add(source, rows[0] if rows else 1, 7,
                                 f'{book.name} has {len(rows)} routing rows; expected 1')

    def invocation(self):
        entries = (self.root / 'mmw-v2/skills.txt').read_text(encoding='utf-8') if (self.root / 'mmw-v2/skills.txt').exists() else ''
        for source, text in self.component_files().items():
            seen = set()
            for mention in self.model_mentions(source, text):
                name = mention.name
                if name not in self.skills or name in seen:
                    continue
                seen.add(name)
                skill_path = self.skills[name]
                if '/upstream' not in skill_path:
                    continue
                self.edge(source, skill_path, 9)
                entry = next((s for s in entries.splitlines() if s.split() and
                              s.split()[0].rsplit('/', 1)[-1] == name), '')
                original = self.root / skill_path / 'SKILL.md'
                switched = original.is_file() and 'disable-model-invocation' in frontmatter(
                    original.read_text(encoding='utf-8'))[0]
                if switched and '+model-invoked' not in entry:
                    self.add(source, mention.line, 9,
                             f'{name} is named for the model and has disable-model-invocation; '
                             'it needs +model-invoked in skills.txt')
                copy = self.state_home / 'skill-copies' / name
                if not copy.is_dir():
                    continue
                skill = copy / 'SKILL.md'
                if skill.is_file() and 'disable-model-invocation' in frontmatter(skill.read_text())[0]:
                    self.add(source, mention.line, 9, f'{copy.name} installation copy still has invocation switch')
                policy = copy / 'agents/openai.yaml'
                if policy.is_file() and re.search(r'^policy:', policy.read_text(), re.M):
                    self.add(source, mention.line, 9, f'{copy.name} installation copy still has policy')
        for name, skill_path in self.skills.items():
            if not skill_path.startswith('mmw-v2/skills/'):
                continue
            file = self.root / skill_path / 'SKILL.md'
            if file.is_file() and 'disable-model-invocation' in frontmatter(file.read_text())[0]:
                self.add(skill_path + '/SKILL.md', 1, 9, 'owned skill has an invocation switch')

    def events(self):
        relay_path = next((p for p in self.files if p.endswith('/relay.py')), '')
        relay = self.files.get(relay_path, '')
        emitted = []
        if relay:
            tree = self.python_tree(relay_path, relay)
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
                            emitted.extend((r, key.value, relay_path, key.lineno) for r in roles if r in self.roles)
        main_roles = [r for r in ('night-orchestrator', 'one-ticket-orchestrator', 'adopting-worker')
                      if r in self.roles]
        if 'relay.recovered' in relay:
            emitted.extend((r, 'relay.recovered', relay_path, source_line(relay, relay.index('relay.recovered')))
                           for r in main_roles)
        for path, line, template in self.alert_templates:
            if path.endswith('/watchdog.py') and template.startswith('watchdog:'):
                emitted.extend((r, template.split(';', 1)[0], path, line) for r in main_roles)
        for path, content in self.files.items():
            if path.endswith('/turn-guard.py') and 'MMW turn guard:' in content:
                emitted.extend((r, 'MMW turn guard:', path, source_line(content, content.index('MMW turn guard:')))
                               for r in main_roles)
            elif path.endswith('/dispatch.sh') and 'resume_one()' in content:
                emitted.extend((r, 'resume', path, source_line(content, content.index('resume_one()')))
                               for r in ('worker', 'adopting-worker') if r in self.roles)
        for role, row in self.roles.items():
            emitted.extend((role, event, 'mmw-v2/skills/mmw/roles.json', 1)
                           for event in row.get('wakes', {}) if event != '*')
        for role, event, source, line in sorted(set(emitted)):
            row = self.roles[role]
            wakes = row.get('wakes', {})
            step = wakes.get(event, wakes.get('*'))
            target = self.mode / 'playbooks' / (row.get('playbook', '') + '.md')
            self.edge(f'{role}/{event}', f'{row.get("playbook")}/{step}', 6)
            if step is None:
                self.add(source, line, 6,
                         f'{role}/{event} has no registered handler')
            elif not target.is_file():
                self.add(source, line, 6,
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
                self.objects.add(11)
                pattern = re.compile(re.escape(Path(path).name) + r'["\'`\s]+(?:<[^>]+>\s+)?' + re.escape(name) + r'\b')
                consumers = [p for p, t in self.files.items() if p != path and
                             (p.endswith(('.py', '.sh')) or p in components or
                              (p.startswith('mmw-v2/skills/') and p.endswith('.md'))) and
                             pattern.search(t)]
                for consumer in consumers:
                    self.edge(consumer, path + '#' + name, 11)
                if not consumers:
                    self.add(path, source_line(text, offset), 11, f'{name} has no command consumer')

    def frozen_paths(self):
        marker = self.state_home / 'installed-root'
        installed = Path(marker.read_text(encoding='utf-8').strip()).expanduser().resolve() if marker.is_file() else None
        inputs = self.session_templates + [('mmw-v2/skills/mmw/roles.json', 1, self.roles_text)]
        for path, line, text in inputs:
            for match in re.finditer(r'(?:/|~/)[^\s"\'`<>]*mmw-v2/[^\s"\'`<>]+', text):
                literal = match[0].rstrip('.,;')
                target = Path(literal).expanduser().resolve()
                self.edge(path, literal, 12)
                if installed is None or not target.is_relative_to(installed):
                    self.add(path, line, 12, f'{literal} is not under the installed-root checkout')

    def upstream_differences(self):
        """Compare skill units with the last squash's upstream tree.

        Registration forms are defined in mmw-v2/merge-notes/README.md under
        上游目录只允许两类改动; a note's presence is not blanket permission.
        Invocation-switch pairing is registered
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
                root = component_root(path)
                name = Path(root).name
                note = self.root / 'mmw-v2/merge-notes' / (name + '.md')
                notes = note.read_text(encoding='utf-8') if note.is_file() else ''
                file_name = str(Path(path).relative_to(root))
                headings = list(re.finditer(r'^(#{2,4}) (.+)$', notes, re.M))
                file_heading = next((h for h in headings if file_name in h[2] or Path(path).name in h[2]), None)
                original = subprocess.run(['git', '-C', str(self.root), 'show',
                                           f'{revision}:{upstream_path}'], capture_output=True, text=True)
                if original.returncode:
                    if not file_heading:
                        self.add(path, 1, 3, f'{upstream_path} has no squash original')
                    continue
                old = markdown_units(original.stdout)
                new = markdown_units(content)
                if [u.identity for u in old] == [u.identity for u in new]:
                    continue
                general = self.root / 'mmw-v2/merge-notes/README.md'
                registry = general.read_text(encoding='utf-8') if general.is_file() else ''
                owners = next((a for a in anchors(registry) if a.title == '本仓自有正文的技能'), None)
                owner_text = '\n'.join(registry.splitlines()[owners.start:owners.end]) if owners else ''
                owns_content = name in re.findall(r'`([^`]+)`', owner_text)
                registered_file = file_name in notes or Path(path).name in notes
                file_notes = notes
                if file_heading:
                    end = next((h.start() for h in headings if h.start() > file_heading.start() and
                                len(h[1]) <= len(file_heading[1])), len(notes))
                    file_notes = notes[file_heading.end():end]
                section_titles = anchors(content)
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
                    if title:
                        section_registered = title in file_notes
                        location = f'{file_name}#{title}'
                    elif changed[0].key:
                        missing = next((u for u in changed if u.key and f'`{u.key}`' not in file_notes), None)
                        section_registered = missing is None
                        unit = missing or changed[0]
                        location = f'{file_name}@{unit.key}'
                        line = unit.line
                    else:
                        opening = ' '.join(changed[0].text.split()[:3])
                        section_registered = bool(opening and opening in file_notes)
                        location = f'{file_name}#"{opening}"'
                    whole_file = bool(re.search(r'(全文|所有段落|whole file|entire file)', file_notes))
                    if not (owns_content or (switches and 'disable-model-invocation' in registry) or
                            (registered_file and (section_registered or whole_file))):
                        self.add(path, line, 3, f'upstream difference at {location} is not registered in its merge-note')

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
    except RegistryError as exc:
        detail = ' '.join(str(exc).splitlines())
        print(f'wiring check cannot read its registry: {detail}; run bash mmw-v2/install.sh --check')
        return 2
    except (OSError, UnicodeError, TextError) as exc:
        print('wiring check failed: a product input cannot be inspected')
        print('Next: correct the named product input and rerun.')
        print('Why: connections cannot be checked in an unreadable or invalid source.')
        print(str(exc))
        return 1
    failures = [f for f in findings if not f.report_only and
                (CLASS_POLICY[f.category].pending if f.pending else
                 CLASS_POLICY[f.category].registry if f.registry_path else
                 CLASS_POLICY[f.category]).fails]
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
        if category not in check.objects:
            print(f'report: class {category}: no objects yet')
    if not failures:
        print(f'WIRING OK {len(check.edges)} checks')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
