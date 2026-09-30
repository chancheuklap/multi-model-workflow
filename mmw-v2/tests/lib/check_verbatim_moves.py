#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Check the committed Markdown units carried by a moves manifest.

Run: uv run check_verbatim_moves.py --manifest <file> [--all]
Run: uv run check_verbatim_moves.py --ticket <n> [--base <ref>] [--all]
Run: uv run check_verbatim_moves.py --lint-drafts <dir> [--renames-table <tsv>]...
Run from the git repository being checked. Both snapshots are committed: sources
come from `from` (or their explicit revision), destinations from HEAD.

--lint-drafts reads a directory of to-tickets step 7 drafts (header lines
TITLE, LABELS and BLOCKED BY, a line ---, then the body). It checks each
draft's ## Moves manifest and does not compare carried text. A draft with no
## Moves counts and contributes no directives. --renames-table may be repeated;
a rename line may match a row in any table. m in the success line is the number
of directives other than from.

L1 location: a source location resolves once on its snapshot. A target that
matches two anchors does too. A target file or heading that is not on the
snapshot yet is a new destination, and a source line range used as a target is
rejected by the manifest grammar.
L2 stale: a replace old string, after drops on that source, and a drop sentence
prefix, each match exactly one place in the source range.
L3 provenance: replace, drop and new name a provenance. A new without a whole
sentence names R20 §5.<n> and a section name.
L4 overlap: across drafts, source ranges do not overlap and target locations
are not repeated. A whole-file location occupies that whole file.
L5 rename-table: every rename line matches one row's kind, old, new and scope.
RENAME-NOT-IN-TABLE.
L6 rename-carried: when one draft executes a rename, every other draft carries
the same line when text it carries to a target, text already at that target,
or a new sentence contains the old name. Kind and scope match the path where
the night check compares that text: the transfer's target for carried source
text, and the location's own path for existing target text and a new sentence.
RENAME-NOT-CARRIED.
L7 rename-order: of the drafts that carry one rename line, one blocks the other
directly or through a chain of BLOCKED BY edges, including drafts that do not
carry the line. Two drafts that can still run in the same batch are reported.

Exit 0: DRAFTS OK <n> drafts, <m> moves checked
Exit 1: one line per finding, each carrying its rule id.
Exit 2: the draft directory or a renames table cannot be read, a draft is not
in the step 7 shape, a manifest cannot be parsed, or a pinned commit does not
exist. DRAFTS OK is not printed.

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
ambiguous input; nothing could be judged. --ticket reads exactly one moves fence
in the ticket body's ## Moves section. Untouched units outside the manifest are
checked only on issue-$MMW_TICKET, against merge-base(HEAD, --base or MMW_BASE_REF).
Squashed subtree prefixes are excluded and named in the success line.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field, replace
import difflib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

try:
    from skill_text import (FENCE, HEADING, REFERENCE, GitTree, Location, LocationMissing,
                            Rename, TextError, Unit, anchors, closes_fence, frontmatter,
                            canonical_text, markdown_units, normalize_title,
                            parse_location, read_imports, rename_text, sentences)
except ImportError as exc:
    print(f'VERBATIM ERROR no units checked: {exc}')
    print('Next: run with uv run so the declared PyYAML dependency is available.')
    print('Why: the check needs the shared Markdown parser.')
    sys.exit(2)


@dataclass
class Replacement:
    old: str
    new: str
    line: int
    provenance: str


@dataclass
class Transfer:
    kind: str
    source: Location
    target: Location
    any_order: bool = False
    replacements: list[Replacement] = field(default_factory=list)
    line: int = 0


@dataclass
class Allowance:
    location: Location
    text: str | None
    title: bool = False
    line: int = 0
    provenance: str = ''

    def selects(self, unit: Unit, prefix: bool = False) -> bool:
        if self.text is None:
            return True
        if self.title:
            return unit.kind == 'title' and unit.text == normalize_title(self.text)
        text = re.sub(r'\s+', ' ', self.text).strip()
        return unit.kind == 'sentence' and (unit.text.startswith(text) if prefix else unit.text == text)


@dataclass
class Manifest:
    revision: str
    transfers: list[Transfer]
    drops: list[Allowance]
    additions: list[Allowance]
    renames: list[Rename]
    rename_lines: list[tuple[int, Rename]] = field(default_factory=list)

    def checked_directives(self) -> int:
        return (len(self.transfers) + len(self.drops) + len(self.additions)
                + len(self.rename_lines)
                + sum(len(transfer.replacements) for transfer in self.transfers))


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
        elif not quoted and text[i:i+2] == ' :' and text[i+2:].strip() == '':
            return text[:i], ''
    raise TextError('directive requires a standalone provenance colon')


def joined_unit_text(units) -> str:
    """Normalized range text a replace old string is counted in."""
    return ' '.join(unit.text for unit in units)


def parse_manifest(text: str, *, lenient_provenance: bool = False) -> Manifest:
    revisions = []
    transfers = []
    drops = []
    additions = []
    renames = []
    rename_lines = []
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
                                    parse_location(target), bool(any_order), line=number)
                transfers.append(previous)
                continue
            elif verb == 'replace':
                if previous is None:
                    raise TextError('replace requires a preceding move/copy and provenance')
                try:
                    declaration, provenance = provenance_parts(line)
                except TextError:
                    if not lenient_provenance:
                        raise TextError('replace requires a preceding move/copy and provenance') from None
                    declaration, provenance = line, ''
                directive = manifest_words(declaration)
                if len(directive) != 4 or directive[0] != 'replace' or directive[2] != '->':
                    raise TextError('replace requires a preceding move/copy and provenance')
                if not directive[1]:
                    raise TextError('replace old text cannot be empty')
                if not provenance.strip() and not lenient_provenance:
                    raise TextError('replace requires a preceding move/copy and provenance')
                previous.replacements.append(
                    Replacement(directive[1], directive[3], number, provenance.strip()))
                continue
            elif verb in ('drop', 'new'):
                try:
                    declaration, provenance = provenance_parts(line)
                except TextError:
                    if not lenient_provenance:
                        raise
                    declaration, provenance = line, ''
                if not provenance.strip() and not lenient_provenance:
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
                allowance = Allowance(
                    parse_location(' '.join(manifest_words(location)), verb == 'drop'),
                    value, title, number, provenance.strip())
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
                rule = Rename(kind, old, new, scope)
                renames.append(rule)
                rename_lines.append((number, rule))
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
    return Manifest(revisions[0], transfers, drops, additions, renames, rename_lines)


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
                items = [i for i in items if allowance.selects(i.unit, prefix=True)]
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
            for replacement in transfer.replacements:
                old, new = replacement.old, replacement.new
                joined = joined_unit_text(item.unit for item in src)
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
                match = next((d for d in dest if d.id not in self.used and addition.selects(d.unit)), None)
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


def ticket_manifest(number: str) -> str:
    result = subprocess.run(['gh', 'issue', 'view', number, '--json', 'body'],
                            capture_output=True, text=True)
    if result.returncode:
        raise TextError(f'gh issue view {number}: {result.stderr.strip()}',
                        f'restore tracker access for ticket #{number} and rerun.')
    try:
        body = json.loads(result.stdout)['body']
    except (ValueError, KeyError, TypeError) as exc:
        raise TextError(f'gh issue view {number}: response has no readable body',
                        f'restore tracker access to a readable body for ticket #{number} and rerun.') from exc
    if not isinstance(body, str):
        raise TextError(f'gh issue view {number}: response body is not text',
                        f'restore tracker access to a text body for ticket #{number} and rerun.')
    text, _line = moves_manifest(body)
    return text


def moves_manifest(body: str, required: bool = True) -> tuple[str, int] | None:
    """The moves fence text, and the 1-based line of its first directive within `body`."""
    lines = body.replace('\r\n', '\n').replace('\r', '\n').splitlines(keepends=True)
    sections = 0
    in_moves = False
    manifests = []
    i = 0
    while i < len(lines):
        fence = FENCE.match(lines[i])
        if fence:
            marker, info = fence.groups()
            end = i + 1
            while end < len(lines) and not closes_fence(lines[end], marker):
                end += 1
            if in_moves and info.strip() == 'moves':
                if end == len(lines):
                    raise TextError('## Moves has an unclosed moves fence')
                manifests.append((''.join(lines[i+1:end]), i + 2))
            i = end + 1
            continue
        heading = HEADING.match(lines[i])
        if heading and len(heading.group(1)) <= 2:
            in_moves = heading.groups() == ('##', 'Moves')
            sections += int(in_moves)
        i += 1
    if not required and sections == 0 and not manifests:
        return None
    if sections != 1 or len(manifests) != 1:
        raise TextError(f'ticket needs one ## Moves section with one moves fence; '
                        f'found {sections} sections and {len(manifests)} fences',
                        'have the ticket author supply exactly one moves fence in ## Moves and rerun.')
    return manifests[0]


def untouched_text(comparison: Comparison, tree: GitTree, item: Item, source: bool) -> str:
    """In-place units allow listed renames, not the reformatting allowed by moves."""
    text = item.unit.text
    if item.unit.kind == 'code':
        return rename_text(text, 'code', comparison.manifest.renames, item.path) if source else text
    path_rules = [r for r in comparison.manifest.renames if r.kind == 'path']

    def reference(match):
        value = match.group()
        unit = replace(item.unit, text=value)
        canonical = canonical_text(unit, tree, item.path, item.path,
                                   path_rules, source, comparison.head)
        # Normalize only references affected by a declared path mapping.
        if any('\x00path:' + r.new + '\x00' in canonical for r in path_rules):
            form = 'link' if value.startswith('[') else 'named' if value.startswith('the ') else 'code'
            return '\x00' + form + ':' + canonical
        return value

    text = REFERENCE.sub(reference, text)
    return rename_text(text, item.unit.kind, comparison.manifest.renames, item.path) if source else text


def check_untouched(comparison: Comparison, base: str | None,
                    number: str | None = None) -> str:
    """Compare only this ticket's diff, excluding its declared unit scopes."""
    head = comparison.head
    branch = head.git('branch', '--show-current').strip()
    ticket = os.environ.get('MMW_TICKET')
    if not ticket or branch != f'issue-{ticket}' or number is not None and number != ticket:
        return "not checked, not on this ticket's branch"
    if not base:
        raise TextError('untouched text needs --base (MMW_BASE_REF is not set)',
                        'pass --base <ref> for this ticket\'s base branch and rerun.')
    revision = head.git('merge-base', 'HEAD', base).strip()
    before = head.at_revision(revision)
    subjects = head.git('log', '--format=%s', f'{revision}..HEAD')
    prefixes = sorted(set(re.findall(r"^Squashed '(.+?)/'", subjects, re.M)))
    manifest = comparison.manifest
    scopes = ([(Allowance(t.source, None), False) for t in manifest.transfers] +
              [(Allowance(t.target, None), False) for t in manifest.transfers] +
              [(a, True) for a in manifest.drops] +
              [(a, False) for a in manifest.additions])
    named = {allowance.location.path for allowance, _ in scopes}
    named.update(value for rule in manifest.renames if rule.kind == 'path'
                 for value in (rule.old, rule.new))

    def outside(tree: GitTree, path: str) -> list[Item]:
        if not tree.exists(path):
            return []
        excluded = set()
        for allowance, prefix in scopes:
            location = allowance.location
            if location.path != path:
                continue
            try:
                # Explicit source revisions define scopes, not the Q3 snapshot.
                if location.selector == 'lines':
                    # Source line numbers belong to the pinned snapshot. A move
                    # shifts later units into those lines without authorizing them.
                    pinned = (comparison.before.at_revision(location.revision)
                              if location.revision else comparison.before)
                    selected = [item for item in comparison.items(pinned, location)
                                if allowance.selects(item.unit, prefix)]
                    available = comparison.items(tree, Location(path))
                    items = []
                    for prior in selected:
                        value = untouched_text(comparison, pinned, prior, True)
                        match = next((item for item in available
                                      if item.unit.kind == prior.unit.kind and item.unit.key == prior.unit.key and
                                      untouched_text(comparison, tree, item, tree is before) == value), None)
                        if match:
                            items.append(match)
                            available.remove(match)
                else:
                    items = [item for item in comparison.items(tree, replace(location, revision=None))
                             if allowance.selects(item.unit, prefix)]
            except LocationMissing:
                continue  # A moved/dropped section need not survive.
            excluded.update(item.id for item in items)
        result = []
        for item in comparison.items(tree, Location(path)):
            if item.id not in excluded:
                result.append(replace(item, canonical=untouched_text(comparison, tree, item, tree is before)))
        return result

    paths = head.git('diff', '--name-only', '--no-renames', '-z', revision, 'HEAD').split('\x00')
    checked = 0
    for path in filter(None, paths):
        skill = (path.endswith('.md') and
                 (path.startswith(('mmw-v2/skills/', '.mmw/playbooks/')) or
                  re.match(r'mmw-v2/upstream[^/]*/skills/', path)))
        if not (skill or path in named) or any(path.startswith(p + '/') for p in prefixes):
            continue
        checked += 1
        prior, current = outside(before, path), outside(head, path)
        # Pair instances, not unique strings: a repeated sentence is not free.
        for item in prior:
            match = next((other for other in current if item.matches(other)), None)
            if match:
                current.remove(match)
            else:
                comparison.findings.append(Finding('UNTOUCHED-CHANGED', item,
                                                   detail='removed or changed outside the manifest'))
        comparison.findings.extend(Finding('UNTOUCHED-CHANGED', item,
                                           detail='added or changed outside the manifest')
                                   for item in current)
    return f'{checked} files, 0 changes; subtree pulled: {", ".join(prefixes) or "none"}'


OPEN_NEW = re.compile(r'^R20 §5\.\d+ \S')


@dataclass(frozen=True, order=True)
class DraftFinding:
    draft: str
    line: int
    rule: str
    detail: str = ''

    def render(self) -> str:
        message = f'{self.draft}.md:{self.line}: {self.rule}'
        if self.detail:
            message += ' ' + self.detail
        return message


@dataclass(frozen=True)
class Span:
    start: int
    end: int


@dataclass
class Place:
    draft: str
    line: int
    role: str
    location: Location
    span: Span | None
    units: list[Unit] | None
    tree: GitTree
    lands_at: str | None


@dataclass
class Draft:
    name: str
    blocked_by: tuple[str, ...]
    manifest: Manifest | None
    manifest_start: int


def repository_root(next_step: str) -> Path:
    result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if result.returncode:
        raise TextError('not in a git repository', next_step)
    return Path(result.stdout.strip())


def failure_next_step(exc: BaseException, fallback: str, missing_name: str, encoding: str) -> str:
    if isinstance(exc, TextError) and exc.next_step:
        return exc.next_step
    if isinstance(exc, OSError):
        return f'restore read access to {exc.filename or missing_name} and rerun.'
    if isinstance(exc, UnicodeError):
        return encoding
    return fallback


def refuse(prefix: str, fact: str, next_step: str, why: str) -> int:
    print(f'{prefix} {fact}')
    print('Next: ' + next_step)
    print('Why: ' + why)
    return 2


def load_rename_table(path: Path) -> set[Rename]:
    text = path.read_text(encoding='utf-8')
    keys = set()
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        cells = [cell.strip() for cell in raw.split('\t')]
        if cells and cells[0] == 'kind':
            continue
        if len(cells) < 3 or not cells[0] or not cells[1] or not cells[2]:
            raise TextError(f'{path}:{number}: a rename row needs kind, old and new',
                            f'correct the row at {path}:{number} and rerun.')
        kind, old, new = cells[:3]
        scope = cells[3] if len(cells) > 3 and cells[3] else None
        if kind not in ('path', 'token', 'text'):
            raise TextError(f'{path}:{number}: rename kind must be path, token or text',
                            f'correct the kind at {path}:{number} and rerun.')
        if kind == 'path' and scope:
            raise TextError(f'{path}:{number}: a path rename has no scope',
                            f'remove the scope at {path}:{number} and rerun.')
        keys.add(Rename(kind, old, new, scope))
    return keys


def read_draft(path: Path) -> Draft:
    lines = path.read_text(encoding='utf-8').replace('\r\n', '\n').replace('\r', '\n').splitlines()
    header = {}
    split = None
    for index, raw in enumerate(lines):
        if raw.strip() == '---':
            split = index
            break
        if not raw.strip():
            continue
        if ':' not in raw:
            raise TextError(f'{path.name}: header line has no key',
                            'rewrite the draft in the to-tickets step 7 header shape and rerun.')
        key, value = raw.split(':', 1)
        header[key.strip()] = value.strip()
    missing = [key for key in ('TITLE', 'LABELS', 'BLOCKED BY') if key not in header]
    if split is None or missing:
        raise TextError(f'{path.name}: a draft needs TITLE, LABELS, BLOCKED BY and a --- line',
                        'rewrite the draft in the to-tickets step 7 header shape and rerun.')
    blocked = tuple(part.strip() for part in header['BLOCKED BY'].split(',')
                    if part.strip() and part.strip() != '(none)')
    body = '\n'.join(lines[split + 1:])
    try:
        found = moves_manifest(body, required=False)
    except TextError as exc:
        raise TextError(f'{path.name}: {exc}', exc.next_step) from exc
    if found is None:
        return Draft(path.stem, blocked, None, 0)
    manifest_text, body_line = found
    manifest_start = split + 1 + body_line
    try:
        manifest = parse_manifest(manifest_text, lenient_provenance=True)
    except TextError as exc:
        raise TextError(f'{path.name}: {exc}', exc.next_step) from exc
    return Draft(path.stem, blocked, manifest, manifest_start)


def file_line(draft: Draft, manifest_line: int) -> int:
    return draft.manifest_start + manifest_line - 1


def pinned_revisions(manifest: Manifest) -> set[str]:
    found = {manifest.revision}
    for transfer in manifest.transfers:
        if transfer.source.revision:
            found.add(transfer.source.revision)
    for drop in manifest.drops:
        if drop.location.revision:
            found.add(drop.location.revision)
    return found


def inspect_location(tree: GitTree, location: Location, source: bool) -> tuple[str | None, list[Unit] | None]:
    """A missing target file or heading is a new destination; a second anchor is not."""
    if location.selector == 'lines' and not source:
        return f'{location.path}: line ranges are source-only', None
    at = tree.at_revision(location.revision) if location.revision else tree
    if not at.exists(location.path):
        if source:
            return f'{location.path} not found at {at.revision}', None
        return None, None
    try:
        units = at.selection(location).units
    except LocationMissing as exc:
        return (str(exc), None) if source else (None, None)
    except TextError as exc:
        return str(exc), None
    return None, units


def location_span(tree: GitTree, location: Location) -> Span | None:
    at = tree.at_revision(location.revision) if location.revision else tree
    if not at.exists(location.path):
        return None
    text = at.read(location.path)
    total = len(text.splitlines())
    if location.whole:
        return Span(1, total + 1)
    if location.selector == 'lines':
        bounds = re.split(r'-(?:L)?', location.value)
        start, end = int(bounds[0]), int(bounds[-1])
        if start < 1 or end < start or end > total:
            return None
        return Span(start, end + 1)
    if location.selector == 'heading':
        hits = [anchor for anchor in anchors(text) if anchor.title == normalize_title(location.value)]
        if len(hits) != 1:
            return None
        # Anchor.end is the line index where the next heading starts. The span
        # is that anchor, half-open at the following line, so adjacent sections
        # do not overlap. Blank lines inside the section are part of the span
        # and are not units, so the span is not the unit list select() returns.
        return Span(hits[0].start, hits[0].end + 1)
    if location.selector == 'field':
        try:
            _, _, marks = frontmatter(text)
        except TextError:
            return None
        line = marks.get(location.value)
        if line is None:
            return None
        return Span(line, line + 1)
    return None


def same_place(left: Location, right: Location) -> bool:
    if left.selector != right.selector:
        return False
    if left.selector == 'heading':
        return normalize_title(left.value) == normalize_title(right.value)
    return left.value == right.value


def places_overlap(left: Place, right: Place) -> bool:
    if left.location.path != right.location.path:
        return False
    if left.location.whole or right.location.whole:
        return True
    if same_place(left.location, right.location):
        return True
    if left.span and right.span and left.span.start < right.span.end and right.span.start < left.span.end:
        return True
    return False


def place_mentions(place: Place, rule: Rename) -> bool:
    if not place.lands_at or not place.units:
        return False
    path = place.location.path
    for unit in place.units:
        if rule.kind == 'path':
            if rule.old in unit.text:
                return True
            try:
                canon = canonical_text(unit, place.tree, path, path, [], False, place.tree)
            except TextError:
                continue
            if f'\x00path:{rule.old}\x00' in canon:
                return True
        elif rename_text(unit.text, unit.kind, [rule], place.lands_at) != unit.text:
            return True
    return False


def addition_mentions(addition: Allowance, rule: Rename) -> bool:
    path = addition.location.path
    if rule.kind == 'path':
        return bool(addition.text and rule.old in addition.text)
    if not addition.text or not rule.applies(path):
        return False
    if rename_text(addition.text, 'sentence', [rule], path) != addition.text:
        return True
    # The sentence text was judged above. A sentence that is not a Markdown
    # document (a line that is only ---) cannot be split; that is not a draft error.
    try:
        units = markdown_units(addition.text + '\n')
    except TextError:
        return False
    for unit in units:
        if rename_text(unit.text, unit.kind, [rule], path) != unit.text:
            return True
    return False


def mention_line(draft: Draft, places: list[Place], rule: Rename) -> int | None:
    for place in places:
        if place_mentions(place, rule):
            return place.line
    if draft.manifest is None:
        return None
    for addition in draft.manifest.additions:
        if addition_mentions(addition, rule):
            return file_line(draft, addition.line)
    return None


def reaches(blocked: dict[str, set[str]], start: str, goal: str) -> bool:
    seen = set()
    frontier = [start]
    while frontier:
        current = frontier.pop()
        for name, blockers in blocked.items():
            if name == current or name in seen or current not in blockers:
                continue
            if name == goal:
                return True
            seen.add(name)
            frontier.append(name)
    return False


def judge_drafts(args) -> int:
    root = repository_root('run from the git repository the drafts read with from.')
    directory = args.lint_drafts
    if not directory.is_dir():
        raise TextError(f'{directory} is not a readable draft directory',
                        'pass the directory of to-tickets step 7 drafts and rerun.')
    table_keys: set[Rename] = set()
    for path in args.renames_table or []:
        table_keys |= load_rename_table(path)
    drafts = [read_draft(path) for path in sorted(directory.iterdir())
              if path.is_file() and path.suffix == '.md']
    cache: dict = {}

    def tree_for(revision: str) -> GitTree:
        if revision not in cache:
            GitTree(root, revision, cache)
        return cache[revision]

    for draft in drafts:
        if draft.manifest is None:
            continue
        for revision in sorted(pinned_revisions(draft.manifest)):
            try:
                tree_for(revision)
            except TextError as exc:
                raise TextError(f'{draft.name}.md: {revision} is not a commit',
                                'pin from to a commit that exists in this repository and rerun.') from exc
    findings: list[DraftFinding] = []
    places: list[Place] = []
    places_of: dict[str, list[Place]] = {draft.name: [] for draft in drafts}
    for draft in drafts:
        manifest = draft.manifest
        if manifest is None:
            continue
        base = tree_for(manifest.revision)
        dropped: set[tuple] = set()

        def consider(location: Location, role: str, manifest_line: int,
                     lands_at: str | None, hide: set[tuple] | None = None) -> list[Unit] | None:
            tree = base.at_revision(location.revision) if location.revision else base
            fault, units = inspect_location(tree, location, role == 'source')
            span = None if fault else location_span(tree, location)
            stored = None if units is None else [
                unit for unit in units
                if hide is None or (location.path, unit.line, unit.identity) not in hide]
            place = Place(draft.name, file_line(draft, manifest_line), role, location,
                          span, stored, tree, lands_at)
            places.append(place)
            places_of[draft.name].append(place)
            if fault:
                findings.append(DraftFinding(draft.name, place.line, 'L1', fault))
            return units

        for drop in manifest.drops:
            units = consider(drop.location, 'source', drop.line, None)
            if not drop.provenance.strip():
                findings.append(DraftFinding(draft.name, file_line(draft, drop.line), 'L3',
                                             'provenance is empty'))
            if units is None:
                continue
            if drop.text is None:
                chosen = units
            else:
                chosen = [unit for unit in units if drop.selects(unit, prefix=True)]
                if len(chosen) != 1:
                    findings.append(DraftFinding(
                        draft.name, file_line(draft, drop.line), 'L2',
                        f'drop prefix matched {len(chosen)} sentences'))
            dropped.update((drop.location.path, unit.line, unit.identity) for unit in chosen)
        for transfer in manifest.transfers:
            source_units = consider(transfer.source, 'source', transfer.line,
                                    transfer.target.path, dropped)
            consider(transfer.target, 'target', transfer.line, transfer.target.path)
            if source_units is None:
                for replacement in transfer.replacements:
                    if not replacement.provenance.strip():
                        findings.append(DraftFinding(
                            draft.name, file_line(draft, replacement.line), 'L3',
                            'provenance is empty'))
                continue
            kept = [unit for unit in source_units
                    if (transfer.source.path, unit.line, unit.identity) not in dropped]
            joined = joined_unit_text(kept)
            for replacement in transfer.replacements:
                count = joined.count(replacement.old)
                if count != 1:
                    findings.append(DraftFinding(
                        draft.name, file_line(draft, replacement.line), 'L2',
                        f'replace old text matched {count} times'))
                if not replacement.provenance.strip():
                    findings.append(DraftFinding(
                        draft.name, file_line(draft, replacement.line), 'L3',
                        'provenance is empty'))
        for addition in manifest.additions:
            consider(addition.location, 'target', addition.line, addition.location.path)
            open_new = addition.text is None and not addition.title
            if not addition.provenance.strip():
                detail = 'provenance is empty'
            elif open_new and not OPEN_NEW.match(addition.provenance.strip()):
                detail = 'open new provenance must name an R20 section'
            else:
                detail = ''
            if detail:
                findings.append(DraftFinding(draft.name, file_line(draft, addition.line), 'L3', detail))
        for manifest_line, rule in manifest.rename_lines:
            if rule not in table_keys:
                findings.append(DraftFinding(draft.name, file_line(draft, manifest_line), 'L5',
                                             'RENAME-NOT-IN-TABLE'))

    for role in ('source', 'target'):
        group = [place for place in places if place.role == role]
        for index, left in enumerate(group):
            for right in group[index + 1:]:
                if left.draft == right.draft or not places_overlap(left, right):
                    continue
                later, other = (right, left) if (right.draft, right.line) >= (left.draft, left.line) else (left, right)
                findings.append(DraftFinding(later.draft, later.line, 'L4', f'overlaps {other.draft}.md'))

    reported_carries: set[tuple] = set()
    for draft in drafts:
        if draft.manifest is None:
            continue
        for _line, rule in draft.manifest.rename_lines:
            for other in drafts:
                if other.name == draft.name:
                    continue
                if other.manifest and any(other_rule == rule
                                           for _other_line, other_rule in other.manifest.rename_lines):
                    continue
                mark = (other.name, rule)
                if mark in reported_carries:
                    continue
                line = mention_line(other, places_of[other.name], rule)
                if line is None:
                    continue
                reported_carries.add(mark)
                findings.append(DraftFinding(other.name, line, 'L6', 'RENAME-NOT-CARRIED'))

    blocked = {draft.name: set(draft.blocked_by) for draft in drafts}
    carriers: dict[Rename, list[tuple[Draft, int]]] = {}
    for draft in drafts:
        if draft.manifest is None:
            continue
        seen: set[Rename] = set()
        for manifest_line, rule in draft.manifest.rename_lines:
            if rule in seen:
                continue
            seen.add(rule)
            carriers.setdefault(rule, []).append((draft, manifest_line))
    for _rule, group in carriers.items():
        for index, (left, left_line) in enumerate(group):
            for right, right_line in group[index + 1:]:
                if reaches(blocked, left.name, right.name) or reaches(blocked, right.name, left.name):
                    continue
                later, later_line, other = ((right, right_line, left)
                                            if right.name >= left.name else (left, left_line, right))
                findings.append(DraftFinding(
                    later.name, file_line(later, later_line), 'L7',
                    f'can run in the same batch as {other.name}.md'))

    checked = sum(draft.manifest.checked_directives() for draft in drafts if draft.manifest)
    count = len(drafts)
    if findings:
        print(f'DRAFTS FAIL {len(findings)} findings, {count} drafts, {checked} moves checked')
        print('Next: correct each reported draft line before publishing the batch.')
        print('Why: a later ticket in this batch would otherwise fail its own verbatim check.')
        for finding in sorted(findings):
            print(finding.render())
        return 1
    print(f'DRAFTS OK {count} drafts, {checked} moves checked')
    return 0


def run_lint(args) -> int:
    try:
        return judge_drafts(args)
    except (TextError, OSError, UnicodeError) as exc:
        return refuse(
            'DRAFTS ERROR', str(exc),
            failure_next_step(
                exc, 'correct the draft batch and rerun.', str(args.lint_drafts),
                'correct the file to UTF-8 and rerun.'),
            'a draft batch that cannot be read cannot be judged.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--manifest', type=Path)
    inputs.add_argument('--ticket')
    inputs.add_argument('--lint-drafts', type=Path)
    parser.add_argument('--renames-table', type=Path, action='append')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--base')
    args = parser.parse_args(argv)
    if args.lint_drafts:
        return run_lint(args)
    if args.renames_table:
        print('VERBATIM ERROR no units checked: --renames-table belongs to --lint-drafts')
        print('Next: pass --lint-drafts <dir> or drop --renames-table.')
        print('Why: a comparison reads renames from the manifest, not from a table.')
        return 2
    try:
        root = repository_root('run from the git repository containing the manifest source and target files.')
        text = (ticket_manifest(args.ticket) if args.ticket else
                args.manifest.read_text(encoding='utf-8'))
        manifest = parse_manifest(text)
        comparison = Comparison(root, manifest).run()
        untouched = check_untouched(comparison, args.base or os.environ.get('MMW_BASE_REF'), args.ticket)
    except (TextError, OSError, UnicodeError) as exc:
        input_name = str(args.manifest or f'ticket #{args.ticket}')
        return refuse(
            'VERBATIM ERROR no units checked:', str(exc),
            failure_next_step(
                exc,
                'correct the reported manifest directive, location or pinned revision and rerun.',
                input_name,
                f'correct the UTF-8 encoding of {input_name} or the reported snapshot file and rerun.'),
            'comparison requires readable, unambiguous snapshots and directives.')
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
          f'untouched text: {untouched}')
    for item in comparison.new_lines:
        print(f'NEW {item.address}: {item.unit.text}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
