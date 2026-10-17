#!/usr/bin/env python3
"""Classify upstream changes and check their local copies without changing files.

Only Python's standard library and git are required. Exit 0 means comparison
completed or all take hunks passed, 1 means a carry is missing, and 2 means the
refs, files or tables cannot be used. Default tables live beside this script.
"""

import argparse
import difflib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Hunk:
    base_start: int
    base_end: int
    new_start: int
    new_end: int
    marker: str
    first_line: str
    merge: bool
    old_lines: tuple


@dataclass
class Copy:
    upstream: str
    local: str
    hunks: list[Hunk]
    differences: list[tuple]
    current: list[str]


def edits(before, after):
    return [op for op in difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
            if op[0] != 'equal']


def overlaps(start, end, other_start, other_end):
    return start < max(other_end, other_start + 1) and other_start < max(end, start + 1)


def keeps_old_text(hunk, copy):
    # An insertion beside the new text touches no line of it, so the overlap test misses
    # replaced upstream lines left in the copy next to their replacement.
    return any(tag == 'insert' and a in (hunk.new_start, hunk.new_end)
               and set(hunk.old_lines).intersection(copy.current[c:d])
               for tag, a, _, c, d in copy.differences)


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def lines_at(repo, ref, path):
    return git(repo, 'show', f'{ref}:{path}').splitlines()


def table(path, columns):
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line or line.startswith('#'):
            continue
        fields = line.split('\t')
        if len(fields) != columns:
            raise ValueError(f'{path}:{number}: expected {columns} tab-separated columns')
        rows.append((number, fields))
    return rows


def compare(args, repo):
    copies = []
    for number, (source, upstream, local) in table(args.map, 3):
        if source != args.upstream:
            continue
        upstream_path = f'upstream/{source}/{upstream}'
        base = lines_at(repo, args.base, upstream_path)
        previous = lines_at(repo, args.mmw, local)
        newest = (repo / upstream_path).read_text().splitlines()
        current = (repo / local).read_text().splitlines()
        local_edits = edits(base, previous)
        hunks = []
        for _, i, end, j, new_end in edits(base, newest):
            marker_lines = base[i:end] if i != end else newest[j:new_end]
            marker = next((line for line in marker_lines if line.strip()), '')
            first_line = next((line for line in newest[j:new_end] if line.strip()), '')
            merge = any(overlaps(i, end, a, b) for _, a, b, _, _ in local_edits)
            old_lines = tuple(line for line in base[i:end] if line.strip() and line not in newest[j:new_end])
            hunks.append(Hunk(i, end, j, new_end, marker, first_line, merge, old_lines))
        copies.append(Copy(upstream, local, hunks, edits(newest, current), current))
    if not copies:
        raise ValueError(f'{args.map}: no copies mapped for upstream {args.upstream}')
    return copies


def kept_hunks(args, copies):
    exceptions = set()
    for number, (source, upstream, marker, reason, explanation) in table(args.keep, 5):
        if source != args.upstream:
            continue
        location = f'{args.keep}:{number}: {upstream}'
        if reason not in {'rule-3', 'rule-4', 'absent', 'wiring', 'owner'} or not explanation.strip():
            raise ValueError(f'{location}: expected an allowed reason code and explanation')
        matches = [(copy.local, hunk) for copy in copies if copy.upstream == upstream
                   for hunk in copy.hunks if not hunk.merge and hunk.marker == marker]
        if len(matches) != 1:
            raise ValueError(f'{location}: marker matches {len(matches)} take hunks; expected exactly 1')
        exceptions.add(matches[0])
    return exceptions


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('upstream')
    parser.add_argument('--base', required=True)
    parser.add_argument('--mmw', required=True)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--map', type=Path, default=here / 'upstream-map.tsv')
    parser.add_argument('--keep', type=Path, default=here / 'upstream-keep.tsv')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        repo = Path(git(args.repo, 'rev-parse', '--show-toplevel').strip())
        copies = compare(args, repo)
        take = merge = carried = kept = missing = 0
        exceptions = kept_hunks(args, copies) if args.check else set()
        for copy in copies:
            take_count = sum(not h.merge for h in copy.hunks)
            merge_count = len(copy.hunks) - take_count
            take += take_count
            merge += merge_count
            print(f'{copy.local}: {take_count} take, {merge_count} merge')
            for hunk in copy.hunks:
                if hunk.merge:
                    print(f'MERGE {copy.local}:{hunk.base_start + 1} {hunk.marker}')
                elif args.check:
                    if (copy.local, hunk) in exceptions:
                        kept += 1
                    elif any(overlaps(hunk.new_start, hunk.new_end, a, b)
                             for _, a, b, _, _ in copy.differences) or keeps_old_text(hunk, copy):
                        print(f'MISSING {copy.local}:{hunk.new_start + 1} {hunk.first_line}')
                        missing += 1
                    else:
                        carried += 1
        if args.check:
            if missing:
                return 1
            print(f'UPSTREAM OK {carried} carried, {kept} kept, {merge} merge')
        else:
            print(f'{len(copies)} files, {take + merge} hunks: {take} take, {merge} merge')
        return 0
    except (OSError, ValueError) as error:
        print(f'UPSTREAM ERROR: {error}; correct the named ref, path or table and rerun.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
