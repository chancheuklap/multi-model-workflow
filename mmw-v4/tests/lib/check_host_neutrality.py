#!/usr/bin/env python3
"""Check Markdown under a skill tree for host-specific instructions.

    python3 mmw-v4/tests/lib/check_host_neutrality.py [<skills dir>]

Exit 0 prints HOST NEUTRALITY OK. Exit 1 prints path:line: word findings.
Exceptions bind an exact line to its path and reason; unused rows fail the check.
"""

from pathlib import Path
import os
import sys
import re


def main():
    skills = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'skills'
    paths = sorted(skills.rglob('*.md'))
    if not paths:
        print(f'{skills}:1: no Markdown files to check; supply a populated skills directory')
        return 1
    upstream_lines = {}
    mapping = skills / 'writing-for-agents/scripts/upstream-map.tsv'
    if mapping.exists():
        upstream = skills.parents[1] / 'upstream'
        if not upstream.is_dir():
            upstream = Path(__file__).resolve().parents[3] / 'upstream'
        for row in mapping.read_text().splitlines():
            if not row or row.startswith('#'):
                continue
            source, original, local = row.split('\t')
            relative = Path(local).relative_to('mmw-v4/skills').as_posix()
            upstream_lines[relative] = set((upstream / source / original).read_text().splitlines())
    exception_file = Path(__file__).with_name('host-neutrality-exceptions.tsv')
    exceptions = {}
    if exception_file.exists():
        for number, row in enumerate(exception_file.read_text().splitlines(), 1):
            if not row or row.startswith('#'):
                continue
            name, text, reason = row.split('\t', 2)
            if not reason.strip():
                raise ValueError(f'{exception_file.name}:{number}: exception needs a reason')
            exceptions[(name, text)] = number
    unused = set(exceptions)
    findings = []
    for path in paths:
        relative = path.relative_to(skills).as_posix()
        text = path.read_text()
        lines = text.splitlines()
        unused.difference_update((relative, line) for line in lines)
        if relative in {'writing-for-agents/references/SKILL-MECHANICS.md', 'dispatch/references/editing-models.md', 'writing-for-agents/references/SKILL-SET-RULES.md'}:
            continue
        checked_lines = set()
        for number, line in enumerate(lines, 1):
            if (relative, line) in exceptions or line in upstream_lines.get(relative, set()):
                continue
            checked_lines.add(number)
            for match in re.finditer(r'\bmcp__codex_app__\w+', line):
                findings.append(f'{relative}:{number}: {match.group()}')
            tokens = list(re.finditer(r'[~\w./-]+', line))
            for token in tokens:
                word = token.group()
                if word.endswith('.') and not word.endswith('..'):
                    word = word[:-1]
                if '..' in word.split('/'):
                    target = Path(os.path.abspath(path.parent / word))
                    if not target.is_relative_to(skills / path.relative_to(skills).parts[0]):
                        findings.append(f'{relative}:{number}: {word}')
                if 'CHECK:' in line and re.search(r'(?:^|/)skills/[^/]+', word):
                    findings.append(f'{relative}:{number}: {word}')
            masked = re.sub(r'\bClaude Design\b|\bclaude\.ai\b',
                            lambda m: ' ' * len(m.group()), line, flags=re.I)
            for token in tokens:
                word = token.group().rstrip('.')
                file_name = re.search(r'\.(?:md|txt|py|sh|json|jsonl|yaml|yml|toml|html|css|js|mjs|ts|tsx|tsv|exe)$', word, re.I)
                directory = token.group().endswith('/') or any(
                    part.startswith('.') and part not in {'.', '..'} for part in word.split('/'))
                if file_name or directory:
                    masked = masked[:token.start()] + ' ' * len(token.group()) + masked[token.end():]
            for match in re.finditer(r'\b(?:claude|codex|grok|cursor|orca|herdr|paseo)\b', masked, re.I):
                findings.append(f'{relative}:{number}: {match.group()}')
        for match in re.finditer(r'\bthe\s+[`*]*(Skill|Task)[`*]*\s+tool\b', text, re.I):
            first = text.count('\n', 0, match.start()) + 1
            last = first + match.group().count('\n')
            if checked_lines.intersection(range(first, last + 1)):
                findings.append(f'{relative}:{first}: the {match.group(1)} tool')
    for key in sorted(unused):
        findings.append(f'{exception_file.name}:{exceptions[key]}: unused exception for {key[0]}')
    print('\n'.join(findings) if findings else 'HOST NEUTRALITY OK')
    return bool(findings)


if __name__ == '__main__':
    sys.exit(main())
