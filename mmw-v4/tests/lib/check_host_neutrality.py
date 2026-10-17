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
    for path in sorted(skills.rglob('*.md')):
        relative = path.relative_to(skills).as_posix()
        lines = path.read_text().splitlines()
        unused.difference_update((relative, line) for line in lines)
        if relative in {'writing-for-agents/SKILL-MECHANICS.md', 'dispatch/references/editing-models.md', 'writing-for-agents/SKILL-SET-RULES.md'}:
            continue
        for number, line in enumerate(lines, 1):
            if (relative, line) in exceptions:
                continue
            if line in upstream_lines.get(path.relative_to(skills).as_posix(), set()):
                continue
            for match in re.finditer(r'(?<![\w/])(?:\.\./)+[^\s`<>\[\]()]+', line):
                word = match.group().rstrip('.,;:')
                target = Path(os.path.abspath(path.parent / word))
                if not target.is_relative_to(skills / path.relative_to(skills).parts[0]):
                    findings.append(f'{relative}:{number}: {word}')
            if 'CHECK:' in line:
                for match in re.finditer(r'(?:~/|/|\.\./)*(?:\.agents|\.claude|\.codex|\.cursor)/skills/[^\s`<>]+', line):
                    findings.append(f'{relative}:{number}: {match.group().rstrip(chr(46))}')
            line = re.sub(r'\bClaude Design\b|\bclaude\.ai\b|(?<![\w])\.?[\w-]+(?:\.[\w-]+|/)[\w./-]*', lambda m: ' ' * len(m.group()), line, flags=re.I)
            for match in re.finditer(r'\b(?:the (?:Skill|Task) tool|claude|codex|grok|cursor|orca|herdr|paseo)\b', line, re.I):
                findings.append(f'{path.relative_to(skills)}:{number}: {match.group()}')
    for key in sorted(unused):
        findings.append(f'{exception_file.name}:{exceptions[key]}: unused exception for {key[0]}')
    print('\n'.join(findings) if findings else 'HOST NEUTRALITY OK')
    return bool(findings)


if __name__ == '__main__':
    sys.exit(main())
