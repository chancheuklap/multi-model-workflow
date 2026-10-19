#!/usr/bin/env python3
"""Read local skill references and session evidence without changing either."""

import argparse
import json
import re
import shlex
import string
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Target:
    skill: str
    file: str | None = None

    def existing_files(self, paths, repo):
        root = (repo / 'mmw-v4/skills' / self.skill).resolve()
        found = set()
        punctuation = (string.punctuation + ''.join(chr(ord(char) + 0xFEE0) for char in string.punctuation)
                       + '。、「」『』【】〈〉《》“”‘’…')
        for path in paths:
            if any(char in path for char in '*?[$'):
                continue
            path = re.sub(r':\d+$', '', path.rstrip(punctuation)).rstrip(punctuation)
            file = repo / 'mmw-v4' / path
            if (file.resolve().is_relative_to(root) and file.is_file()
                    and (self.file is None or path == self.file)):
                found.add(path)
        return found

    @classmethod
    def parse(cls, name, repo, parser):
        if '/' not in name and '\\' not in name:
            return cls(name)
        path = Path(name).expanduser()
        if not path.is_absolute():
            path = repo / path
        root = (repo / 'mmw-v4/skills').resolve()
        try:
            relative = path.resolve().relative_to(root)
        except ValueError:
            parser.error(f'{name} is outside {root}; give a skill name or a file under that directory')
        if not path.is_file() or len(relative.parts) < 2:
            parser.error(f'{name} is not a skill file; give an existing file under {root}')
        return cls(relative.parts[0], 'skills/' + relative.as_posix())


@dataclass
class Session:
    date: str = ''
    first_user: str = ''
    invoked: bool = False
    reads: set[str] = field(default_factory=set)
    file_reads: set[str] = field(default_factory=set)
    subagents: set[str] = field(default_factory=set)


def records(path):
    with path.open() as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def file_paths(value, target, complete_paths=False):
    if isinstance(value, dict):
        return set().union(*(file_paths(v, target, complete_paths) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(file_paths(v, target, complete_paths) for v in value))
    if not isinstance(value, str):
        return set()
    brackets = '' if complete_paths else r'\[\]'
    found = set(re.findall(rf'skills/{re.escape(target.skill)}/[^\s\x22\x27`;,(){{}}{brackets}<>]+', value))
    return {path for path in found if complete_paths or target.file is None or path == target.file}


def claude_sessions(root, target):
    sessions = {}
    for path in sorted(root.rglob('*.jsonl')):
        session = Session()
        for row in records(path):
            if not session.date:
                session.date = str(row.get('timestamp', ''))[:10]
            message = row.get('message', {})
            content = message.get('content', [])
            if row.get('type') == 'user' and not session.first_user:
                if isinstance(content, str):
                    session.first_user = content.splitlines()[0][:80] if content else ''
                elif isinstance(content, list):
                    text = next((b.get('text', '') for b in content if b.get('type') == 'text'), '')
                    session.first_user = text.splitlines()[0][:80] if text else ''
            if row.get('type') != 'assistant' or not isinstance(content, list):
                continue
            for block in content:
                if block.get('type') == 'tool_use':
                    session.reads |= file_paths(block.get('input', {}), target)
                    session.file_reads |= file_paths(block.get('input', {}), target, complete_paths=True)
                if block.get('type') == 'tool_use' and block.get('name') == 'Skill':
                    session.invoked |= target.file is None and block.get('input', {}).get('skill') == target.skill
        sessions[path] = session
    for path in list(sessions):
        if path.parent.name != 'subagents' or not path.name.startswith('agent-'):
            continue
        child = sessions.pop(path)
        parent_path = path.parent.parent.with_suffix('.jsonl')
        parent = sessions.setdefault(parent_path, Session())
        parent.invoked |= child.invoked
        parent.reads |= child.reads
        parent.file_reads |= child.file_reads
        if child.invoked or child.reads:
            parent.subagents.add(str(path))
        if not parent.date:
            parent.date = child.date
    return sessions


def javascript_string(literal):
    escapes = {'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v', '0': '\0'}

    def replace(match):
        value = match.group(1)
        if value.startswith(('u', 'x')) and len(value) > 1:
            return chr(int(value[1:].strip('{}'), 16))
        if value in ('\n', '\r\n'):
            return ''
        return escapes.get(value, value)

    return re.sub(r'\\(u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|\r?\n|.)',
                  replace, literal[1:-1])


def commands(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('cmd', 'command') and isinstance(item, str):
                yield item
            elif isinstance(item, (dict, list)):
                yield from commands(item)
    elif isinstance(value, list):
        for item in value:
            yield from commands(item)
    elif isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = None
        if isinstance(decoded, (dict, list)):
            yield from commands(decoded)
        else:
            embedded = re.findall(r'''(?:cmd|command)\s*:\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''', value)
            if embedded:
                for command in embedded:
                    yield javascript_string(command)
            else:
                yield value


def segment_reads(segment, target, complete_paths=False):
    arguments = []
    skip = False
    for argument in segment:
        if skip:
            skip = False
        elif argument in ('>', '>>', '>|', '>&', '&>', '&>>', '<<', '<<-', '<<<'):
            skip = True
        else:
            arguments.append(argument)
    while arguments and re.match(r'^[A-Za-z_]\w*=', arguments[0]):
        arguments.pop(0)
    if not arguments:
        return set()
    program = Path(arguments[0]).name
    if program in ('sh', 'bash', 'zsh', 'dash', 'ksh'):
        for index, argument in enumerate(arguments[1:-1], 1):
            if re.fullmatch(r'-[a-z]*c[a-z]*', argument):
                return codex_reads(arguments[index + 1], target, complete_paths)
    if program in ('cat', 'nl', 'head', 'tail') or (program == 'sed' and '-n' in arguments[1:]):
        return file_paths(arguments[1:], target, complete_paths)
    return set()


def codex_reads(value, target, complete_paths=False):
    found = set()
    for command in commands(value):
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|()<>\n')
        lexer.whitespace = ' \t\r'
        lexer.whitespace_split = complete_paths
        tokens = []
        try:
            for token in lexer:
                tokens.append(token)
        except ValueError:
            tokens = tokens[:max((i + 1 for i, t in enumerate(tokens)
                                  if t and all(c in ';&|()\n' for c in t)), default=0)]
        segment = []
        for token in [*tokens, ';']:
            if token and all(c in ';&|()\n' for c in token):
                if segment:
                    found |= segment_reads(segment, target, complete_paths)
                segment = []
            else:
                segment.append(token)
    return found


def codex_sessions(root, target):
    sessions = {}
    for path in sorted(root.rglob('*.jsonl')):
        session = Session()
        for row in records(path):
            payload = row.get('payload', {})
            if not session.date:
                session.date = str(row.get('timestamp', payload.get('timestamp', '')))[:10]
            if row.get('type') == 'event_msg' and payload.get('type') == 'user_message' and not session.first_user:
                message = payload.get('message', '')
                session.first_user = message.splitlines()[0][:80] if message else ''
            if payload.get('type') == 'message' and payload.get('role') == 'user' and not session.first_user:
                text = next((b.get('text', '') for b in payload.get('content', [])
                             if b.get('type') == 'input_text'), '')
                session.first_user = text.splitlines()[0][:80] if text else ''
            if payload.get('type') in ('function_call', 'custom_tool_call'):
                value = payload.get('arguments', payload.get('input', ''))
                session.reads |= codex_reads(value, target)
                session.file_reads |= codex_reads(value, target, complete_paths=True)
        sessions[path] = session
    return sessions


def text_entries(repo, target):
    root = repo / 'mmw-v4/skills'
    name = re.escape(target.skill)
    named = re.compile(rf'the {name} skill|\*\*{name}\*\*|`{name}`|(?<![\w/])/{name}(?![\w-])|skills/{name}/')
    if target.file:
        named = re.compile(rf'(?<![\w.-]){re.escape(Path(target.file).name)}(?![\w.-])')
    entries = {}
    for path in sorted([*root.rglob('*'), repo / 'AGENTS.md', repo / 'CLAUDE.md']):
        if not path.is_file() or (root / target.skill) in path.parents:
            continue
        try:
            lines = path.read_text().splitlines()
        except UnicodeDecodeError:
            continue
        matches = [i for i, line in enumerate(lines, 1) if named.search(line)]
        if matches:
            entries[path.relative_to(repo).as_posix()] = matches
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument('--claude', type=Path, default=Path.home() / '.claude/projects')
    parser.add_argument('--codex', type=Path, default=Path.home() / '.codex/sessions')
    parser.add_argument('--since', type=date.fromisoformat, metavar='YYYY-MM-DD',
                        help='include sessions started on or after this date')
    args = parser.parse_args()
    for flag in ('repo', 'claude', 'codex'):
        path = getattr(args, flag)
        if not path.is_dir():
            parser.error(f'--{flag} directory {path} does not exist; usage cannot be measured; '
                         f'pass --{flag} with an existing directory')
    if not (args.repo / 'mmw-v4/skills').is_dir():
        parser.error(f'--repo {args.repo} has no mmw-v4/skills directory; '
                     'pass --repo with the MMW repository root')
    target = Target.parse(args.skill, args.repo, parser)
    entries = text_entries(args.repo, target)
    claude = claude_sessions(args.claude, target)
    codex = codex_sessions(args.codex, target)
    if args.since:
        since = args.since.isoformat()
        claude = {p: s for p, s in claude.items() if s.date >= since}
        codex = {p: s for p, s in codex.items() if s.date >= since}
    invoked = sum(s.invoked for s in claude.values())
    read = sum(bool(s.reads) for s in claude.values())
    subagents = sum(len(s.subagents) for s in claude.values())
    codex_read = sum(bool(s.reads) for s in codex.values())
    print(f'usage {args.skill}: {len(entries)} text entries; claude {invoked} invoked, {read} read, {subagents} by subagents; codex {codex_read} read')
    for host, sessions in [('claude', claude), ('codex', codex)]:
        counted = [s for s in sessions.values() if s.invoked or s.reads]
        dates = sorted(s.date for s in counted if s.date)
        print(f'{host} dates: {dates[0] + " to " + dates[-1] if dates else "-"}')
        counts = Counter(file for session in sessions.values()
                         for file in target.existing_files(session.file_reads, args.repo))
        for file, count in sorted(counts.items()):
            print(f'{host} file {file}: {count} sessions')
    for path, lines in entries.items():
        for line in lines:
            print(f'{path}:{line}')
    for host, sessions in [('claude', claude), ('codex', codex)]:
        for path, session in sessions.items():
            if session.invoked or session.reads:
                files = ', '.join(sorted(session.reads)) or '-'
                print(f'{host} {path.stem} {session.date} invoked={session.invoked}; files: {files}; {session.first_user}')


if __name__ == '__main__':
    main()
