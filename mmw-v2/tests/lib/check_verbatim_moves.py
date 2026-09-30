#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check the committed Markdown units carried by a moves manifest.

Run: uv run check_verbatim_moves.py --manifest <file> [--all]
Run from the git repository being checked. Both snapshots are committed: sources
come from `from` (or their explicit revision), destinations from HEAD.

Manifest grammar, one directive per line (blank lines and # comments ignored):
  from <sha>                         exactly once
  move <source> -> <target> [any-order]
  copy <source> -> <target> [any-order]
  replace "<old>" -> "<new>" : <provenance>
  drop <source> ["<sentence prefix>"] : <destination or reason>
  new <target> ["<whole sentence>"] : <provenance>
  new <target> title "<Title>" : <provenance>
  rename <path|token|text> <old> -> <new> [in <glob>]

Consecutive replace lines belong to the preceding move/copy; any other directive
ends that group. Each matches exactly once in its whitespace-normalized source.
Whole-file moves/copies automatically map
the source path to the target path. Rename values may be backtick-quoted.
Locations: path (whole file), path@<frontmatter key>, path#<heading or bold
label>, path:L12 or path:L12-L30 (source only). A source may be <rev>:<location>.
Heading scopes include subordinate headings; list steps include all continuations
and nested content; bold-labelled paragraphs end at the next bold label/heading.
Provenance is required for replace/drop/new. Only a manifest's listed renames
apply. --all prints findings beyond the default limit of 40.

Exit 0: VERBATIM OK with counts, then NEW lines for open-ended new allowances.
Exit 1: findings, or VERBATIM FAIL checked nothing. Exit 2: malformed, missing or
ambiguous input; nothing could be judged. Q3/--ticket/--lint-drafts are separate
from this manifest comparison.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field, replace
import difflib
from pathlib import Path
import re
import shlex
import subprocess
import sys

try:
    from skill_text import (GitTree, Location, Rename, TextError, Unit,
                            canonical_text, markdown_units, normalize_title,
                            parse_location, read_imports, rename_text, sentences)
except ImportError as exc:
    print(f'VERBATIM ERROR no units checked: {exc}')
    print('Next: run with uv run so the declared PyYAML dependency is available.')
    print('Why: the check needs the shared Markdown parser.')
    sys.exit(2)


@dataclass
class Transfer:
    kind: str
    source: Location
    target: Location
    any_order: bool = False
    replacements: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Allowance:
    location: Location
    text: str | None
    title: bool = False


@dataclass
class Manifest:
    revision: str
    transfers: list[Transfer]
    drops: list[Allowance]
    additions: list[Allowance]
    renames: list[Rename]


def quoted_value(value: str) -> str:
    return value[1:-1] if value.startswith('`') and value.endswith('`') else value


def manifest_words(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True)
    lexer.quotes = '"'
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)


def provenance_parts(text: str) -> tuple[str, str]:
    """A colon inside a quoted sentence is text, not the provenance delimiter."""
    quoted = escaped = False
    for i, char in enumerate(text):
        if escaped:
            escaped = False
        elif char == '\\' and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and text[i:i+3] == ' : ':
            return text[:i], text[i+3:]
    raise TextError('directive requires a standalone provenance colon')


def parse_manifest(text: str) -> Manifest:
    revisions = []
    transfers = []
    drops = []
    additions = []
    renames = []
    previous = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        try:
            # shlex preserves the punctuation in locations and quoted sentences.
            parts = manifest_words(line)
            if not parts:
                continue
            verb = parts[0]
            if verb == 'from' and len(parts) == 2:
                revisions.append(parts[1])
            elif verb in ('move', 'copy'):
                match = re.fullmatch(r'(?:move|copy)\s+(.+?)\s+->\s+(.+?)(\s+any-order)?', line)
                if not match:
                    raise TextError('invalid transfer')
                source, target, any_order = match.groups()
                source = ' '.join(manifest_words(source))
                target = ' '.join(manifest_words(target))
                previous = Transfer(verb, parse_location(source, True),
                                    parse_location(target), bool(any_order))
                transfers.append(previous)
                continue
            elif verb == 'replace':
                if previous is None or len(parts) < 6 or parts[2] != '->' or parts[4] != ':':
                    raise TextError('replace requires a preceding move/copy and provenance')
                if not parts[1]:
                    raise TextError('replace old text cannot be empty')
                previous.replacements.append((parts[1], parts[3]))
                continue
            elif verb in ('drop', 'new'):
                declaration, provenance = provenance_parts(line)
                if not provenance.strip():
                    raise TextError(f'{verb} requires a location and provenance')
                location = declaration[len(verb):].strip()
                sentence = re.search(r'\s+"((?:\\.|[^"\\])*)"$', location)
                value = None
                title = False
                if sentence:
                    value = manifest_words(sentence.group().strip())[0]
                    location = location[:sentence.start()]
                    if verb == 'new' and location.endswith(' title'):
                        title = True
                        location = location[:-6]
                elif '"' in location and not (location.startswith('"') and location.endswith('"')):
                    raise TextError(f'invalid {verb} sentence')
                allowance = Allowance(parse_location(' '.join(manifest_words(location)), verb == 'drop'), value, title)
                (drops if verb == 'drop' else additions).append(allowance)
            elif verb == 'rename':
                match = re.fullmatch(r'rename\s+(path|token|text)\s+(.+?)\s+->\s+(.+?)(?:\s+in\s+(\S+))?', line)
                if not match:
                    raise TextError('invalid rename')
                kind, old, new, scope = match.groups()
                if scope and kind == 'path':
                    raise TextError('scope is only for token/text renames')
                old, new = (quoted_value(' '.join(manifest_words(value))) for value in (old, new))
                if not old or not new:
                    raise TextError('rename values cannot be empty')
                renames.append(Rename(kind, old, new, scope))
            else:
                raise TextError('invalid directive')
            previous = None
        except (ValueError, TextError) as exc:
            raise TextError(f'manifest:{number}: {exc}: {line}') from exc
    if len(revisions) != 1:
        raise TextError(f'manifest needs exactly one from; found {len(revisions)}')
    for transfer in transfers:
        if transfer.source.whole and transfer.target.whole:
            renames.append(Rename('path', transfer.source.path, transfer.target.path))
    return Manifest(revisions[0], transfers, drops, additions, renames)


@dataclass(frozen=True)
class Item:
    path: str
    unit: Unit
    ordinal: int
    canonical: str

    @property
    def address(self):
        return f'{self.path}:{self.unit.line}'

    @property
    def key(self):
        text = re.sub(r'\x00label:[^\x00]*\x00', '', self.canonical)
        return self.unit.kind, self.unit.key if self.unit.kind == 'field' else '', text

    def matches(self, other: Item) -> bool:
        # Labels must survive link-to-link comparison. An inline-code path has
        # no label, so its allowed conversion to a link compares just the path.
        if self.key != other.key:
            return False
        refs = r'(?:\x00label:([^\x00]*)\x00)?\x00path:[^\x00]*\x00'
        labels = lambda value: [m.group(1) for m in re.finditer(refs, value)]
        return all(a is None or b is None or a == b
                   for a, b in zip(labels(self.canonical), labels(other.canonical)))

    @property
    def id(self):
        return self.path, self.ordinal


@dataclass
class Finding:
    kind: str
    at: Item
    source: Item | None = None
    detail: str = ''

    def render(self) -> str:
        address = self.at.address
        if self.kind == 'CHANGED' and self.source and self.at.unit.text_lines:
            matcher = difflib.SequenceMatcher(None, self.source.unit.text, self.at.unit.text, autojunk=False)
            changed = next((j for tag, _, _, j, _ in matcher.get_opcodes() if tag != 'equal'), 0)
            rows = self.at.unit.text_lines
            address = f'{self.at.path}:{rows[min(changed, len(rows)-1)]}'
        message = f'{address}: {self.kind}'
        if self.source:
            message += f' from {self.source.address}'
        if self.detail:
            message += ' ' + self.detail
        if self.kind == 'CHANGED' and self.source:
            diff = ' '.join(difflib.ndiff(self.source.unit.text.split(), self.at.unit.text.split()))
            message += '\n  ' + diff
        return message


class Comparison:
    """One comparison owns the target instances so no unit is counted twice."""
    def __init__(self, root: Path, manifest: Manifest):
        self.manifest = manifest
        read_imports(root)
        self.before = GitTree(root, manifest.revision)
        self.head = self.before.at_revision('HEAD')
        self.findings: list[Finding] = []
        self.new_lines: list[Item] = []
        self.counts = Counter()
        self.targets: dict[tuple, Item] = {}
        self.used: set[tuple] = set()
        self.expected = []
        self.target_scopes: dict[Location, list[Item]] = {}
        self.removals: dict[tuple, list[Item]] = {}

    def items(self, tree: GitTree, location: Location, target: str | None = None,
              source: bool = False) -> list[Item]:
        if location.revision:
            tree = tree.at_revision(location.revision)
        selection = tree.selection(location)
        full = markdown_units(tree.read(location.path))
        # Range parses preserve source addresses, including exact line ranges.
        occurrences = Counter()
        result = []
        for unit in selection.units:
            matches = [i for i, u in enumerate(full) if u.identity == unit.identity and u.line == unit.line]
            occurrence = occurrences[(unit.identity, unit.line)]
            occurrences[(unit.identity, unit.line)] += 1
            ordinal = matches[occurrence] if occurrence < len(matches) else ('range', unit.line, occurrence, unit.identity)
            canonical = canonical_text(unit, tree, location.path, target or location.path,
                                       self.manifest.renames, source, self.head)
            result.append(Item(location.path, unit, ordinal, canonical))
        return result

    def target(self, location: Location) -> list[Item]:
        if location not in self.target_scopes:
            items = self.items(self.head, location)
            self.target_scopes[location] = items
            for item in items:
                self.targets[item.id] = item
        return self.target_scopes[location]

    def run(self):
        drops = set()
        for allowance in self.manifest.drops:
            items = self.items(self.before, allowance.location)
            if allowance.text is not None:
                items = [i for i in items if i.unit.kind == 'sentence' and i.unit.text.startswith(allowance.text)]
                if len(items) != 1:
                    raise TextError(f'STALE drop {allowance.location.path}: prefix matched {len(items)} sentences')
            tree = (self.before.at_revision(allowance.location.revision).revision
                    if allowance.location.revision else self.before.revision)
            drops.update((tree, i.id) for i in items)
        self.counts['dropped'] = len(drops)
        for transfer in self.manifest.transfers:
            dest = self.target(transfer.target)
            src = self.items(self.before, transfer.source, transfer.target.path, True)
            rev = self.before.at_revision(transfer.source.revision).revision if transfer.source.revision else self.before.revision
            src = [i for i in src if (rev, i.id) not in drops]
            if transfer.kind == 'move':
                self.removals.setdefault((rev, transfer.source.path), []).extend(src)
            for old, new in transfer.replacements:
                joined = ' '.join(i.unit.text for i in src)
                if joined.count(old) != 1:
                    raise TextError(f'STALE replace {transfer.source.path}: old text matched {joined.count(old)} times')
                start = joined.index(old)
                end = start + len(old)
                offsets = []
                cursor = 0
                for item in src:
                    offsets.append((cursor, cursor + len(item.unit.text)))
                    cursor += len(item.unit.text) + 1
                affected = [i for i, (a, b) in enumerate(offsets) if a < end and b > start]
                first, last = affected[0], affected[-1]
                prototype = src[first]
                mixed = any((src[i].unit.kind, src[i].unit.key) !=
                            (prototype.unit.kind, prototype.unit.key) for i in affected)
                a, _ = offsets[first]
                _, b = offsets[last]
                replacement_text = joined[a:start] + new + joined[end:b]
                units = ([Unit('replacement', replacement_text, prototype.unit.line,
                               src[last].unit.end_line)] if mixed else
                         sentences(replacement_text, prototype.unit.line)
                         if prototype.unit.kind == 'sentence' else
                         [replace(prototype.unit, text=replacement_text)])
                changed = []
                tree = self.before.at_revision(rev)
                for i, unit in enumerate(units):
                    unit = replace(unit, key=prototype.unit.key)
                    canonical = canonical_text(unit, tree, prototype.path, transfer.target.path,
                                               self.manifest.renames, True, self.head)
                    changed.append(Item(prototype.path, unit,
                                        (prototype.ordinal, 'replace', i), canonical))
                src = src[:first] + changed + src[last+1:]
                self.counts['replaced'] += 1
            self.expected.append((transfer, src, dest))
        for addition in self.manifest.additions:
            self.target(addition.location)
        # Q1: pair exact source instances first, across all target scopes.
        leftovers = []
        for transfer, src, dest in self.expected:
            order = []
            for item in src:
                if item.unit.kind == 'replacement':
                    span = []
                    for start in range(len(dest)):
                        for end in range(start + 1, len(dest) + 1):
                            candidates = dest[start:end]
                            if (all(d.id not in self.used for d in candidates) and
                                    ' '.join(d.canonical for d in candidates) == item.canonical):
                                span = candidates
                                break
                        if span:
                            break
                    if span:
                        self.used.update(d.id for d in span)
                        order.append(dest.index(span[0]))
                        self.counts['carried'] += len(span)
                    else:
                        leftovers.append((transfer, item, dest))
                    continue
                match = next((d for d in dest if d.id not in self.used and d.matches(item)), None)
                if match:
                    self.used.add(match.id)
                    order.append(dest.index(match))
                    self.counts['carried'] += 1
                    self.counts['path'] += item.canonical.count('\x00path:')
                    self.counts['rename'] += int(rename_text(item.unit.text, item.unit.kind,
                                                           self.manifest.renames, match.path) != item.unit.text)
                    self.counts['citation'] += int('(**principle-' in match.unit.text and
                                                  '(**principle-' not in match.canonical)
                    self.counts['title'] += int(item.unit.kind == 'title')
                    self.counts['format'] += int(item.unit.end_line != item.unit.line or
                                                 match.unit.end_line != match.unit.line)
                else:
                    leftovers.append((transfer, item, dest))
            if not transfer.any_order and order != sorted(order):
                involved = [index for a, b in enumerate(order) for c in order[a+1:]
                            if b > c for index in (b, c)]
                self.findings.append(Finding('OUT-OF-ORDER', dest[min(involved)]))
        # Q2: prior text is an allowance only for scoped targets, never files.
        for location, dest in self.target_scopes.items():
            if location.whole or not self.before.exists(location.path):
                continue
            try:
                prior = self.items(self.before, location, location.path, True)
            except TextError:
                continue  # This is a newly introduced heading/step.
            for item in dest:
                match = next((p for p in prior if p.matches(item)), None)
                if item.id not in self.used and match:
                    self.used.add(item.id)
                    prior.remove(match)
                    self.counts['prior'] += 1
        for addition in self.manifest.additions:
            dest = self.target(addition.location)
            if addition.text is None:
                for item in dest:
                    if item.id not in self.used:
                        self.used.add(item.id)
                        self.new_lines.append(item)
                        self.counts['new'] += 1
            else:
                text = normalize_title(addition.text) if addition.title else re.sub(r'\s+', ' ', addition.text).strip()
                match = next((d for d in dest if d.id not in self.used and d.unit.text == text and
                              (d.unit.kind == 'title' if addition.title else d.unit.kind == 'sentence')), None)
                if match:
                    self.used.add(match.id)
                    self.counts['new'] += 1
                else:
                    marker = dest[0] if dest else Item(addition.location.path, Unit('sentence', text, 1, 1), -1, text)
                    self.findings.append(Finding('MISSING-NEW', marker, detail=text))
        for transfer, item, dest in leftovers:
            # A sentence carried to the wrong scope is missing here, even when
            # unrelated new prose occupies its expected destination.
            elsewhere = self.items(self.head, Location(transfer.target.path))
            elsewhere.extend(self.targets.values())
            scoped_ids = {d.id for d in dest}
            found = next((d for d in elsewhere if d.id not in scoped_ids and d.matches(item)), None)
            candidates = [d for d in dest if d.id not in self.used and d.key[:2] == item.key[:2]]
            best = max(candidates, key=lambda d: difflib.SequenceMatcher(None, item.canonical, d.canonical, autojunk=False).ratio(), default=None)
            if found:
                self.findings.append(Finding('DELETED', item, detail=f'found in {found.address}'))
            elif best:
                self.used.add(best.id)
                self.findings.append(Finding('CHANGED', best, item))
            else:
                self.findings.append(Finding('DELETED', item))
        for item in self.targets.values():
            if item.id not in self.used:
                self.findings.append(Finding('ADDED', item))
        for (revision, path), moved in self.removals.items():
            tree = self.before.at_revision(revision)
            original = Counter(u.identity for u in markdown_units(tree.read(path)))
            remaining_units = markdown_units(self.head.read(path)) if self.head.exists(path) else []
            remaining = Counter(u.identity for u in remaining_units)
            removed = Counter(i.unit.identity for i in moved)
            for key, count in removed.items():
                excess = remaining[key] - (original[key] - count)
                if excess > 0:
                    representative = next(i for i in moved if i.unit.identity == key)
                    self.findings.append(Finding('NOT-REMOVED', representative,
                                                 detail=f'{excess} excess source instance(s)'))
        self.counts['checked'] = (sum(len(src) for _, src, _ in self.expected) +
                                  self.counts['new'] + self.counts['prior'])
        return self


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args(argv)
    try:
        root_result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        if root_result.returncode:
            raise TextError('not in a git repository', 'run from the git repository containing the manifest source and target files.')
        manifest = parse_manifest(args.manifest.read_text(encoding='utf-8'))
        comparison = Comparison(Path(root_result.stdout.strip()), manifest).run()
    except (TextError, OSError, UnicodeError) as exc:
        print(f'VERBATIM ERROR no units checked: {exc}')
        if isinstance(exc, TextError):
            next_step = exc.next_step or 'correct the reported manifest directive, location or pinned revision and rerun.'
        elif isinstance(exc, OSError):
            next_step = f'restore read access to {exc.filename or args.manifest} and rerun.'
        else:
            next_step = f'correct the UTF-8 encoding of {args.manifest} or the reported snapshot file and rerun.'
        print('Next: ' + next_step)
        print('Why: comparison requires readable, unambiguous snapshots and directives.')
        return 2
    if not comparison.counts['checked'] or comparison.findings:
        counts = Counter(f.kind for f in comparison.findings)
        print('VERBATIM FAIL ' + (', '.join(f'{v} {k}' for k, v in counts.items()) if comparison.counts['checked'] else 'checked nothing'))
        print('Next: restore each source sentence; if its wording cannot stand, open a `decision` child.')
        print('Why: only the mechanical rewrites and allowances listed in the manifest may differ.')
        for finding in comparison.findings if args.all else comparison.findings[:40]:
            print(finding.render())
        if len(comparison.findings) > 40 and not args.all:
            print(f'{len(comparison.findings)} findings total; use --all to show every finding.')
        return 1
    c = comparison.counts
    moves = sum(t.kind == 'move' for t in manifest.transfers)
    copies = sum(t.kind == 'copy' for t in manifest.transfers)
    print(f'VERBATIM OK {moves} moves, {copies} copies: {c["carried"]} units carried '
          f'({c["path"]} path, {c["rename"]} rename, {c["citation"]} citation, '
          f'{c["title"]} title, {c["format"]} reflow), '
          f'{c["replaced"]} replaced, {c["new"]} new, {c["dropped"]} dropped; '
          f'{c["prior"]} prior units accounted; '
          'untouched text: not checked (manifest comparison)')
    for item in comparison.new_lines:
        print(f'NEW {item.address}: {item.unit.text}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
