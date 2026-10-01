#!/usr/bin/env python3
"""Read ticket #702's U-7 measurements without starting a host."""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import subprocess
import sys

from check_results import CONFIG_PATHS as BASE_CONFIG_PATHS, HASH_LINE

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SENTENCES_PATH = HERE / "u7-sentences.md"
BEFORE = "6d9cf01ceeeed89013d66db24eca9684712c5ccc"
HOSTS = ("claude", "codex", "grok")
PHASES = ("before", "after")
CONFIG_PATHS = (*BASE_CONFIG_PATHS, "~/.agents/skills", "~/.claude/skills")
NAME = r"[a-z0-9]+(?:-[a-z0-9]+)*"
ENTRY = re.compile(rf"(?:mmw:)?{NAME}")
CELL_LINE = re.compile(
    r"^U-7 (S\d{2}) (claude|codex|grok) (before|after) "
    r"(PASS|FAIL|NEEDS-USER-CONFIG|CANNOT-RUN-UNATTENDED) "
    r"(claude|codex|grok)=(\S+) ([0-9a-f]{40}) (\d{4}-\d{2}-\d{2}) : (\S.*)$")
LIST = rf"(?:none|{NAME}(?:,{NAME})*)"
SUBITEMS = re.compile(
    rf"^skills=({LIST}) playbooks=({LIST}); tool-calls=(\d+); "
    rf"expected=((?:mmw:)?{NAME}); exit=(-?\d+)(?:;.*)?$")


@dataclass(frozen=True)
class Sentence:
    id: str
    n10_row: int
    before: str
    after: str
    text: str

    def expected(self, phase):
        return self.before if phase == "before" else self.after


def read_sentences(path=SENTENCES_PATH):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not re.match(r"\|\s*S", line):
            continue
        columns = [value.strip() for value in line.split("|")[1:-1]]
        if (len(columns) != 5 or not re.fullmatch(r"S\d{2}", columns[0])
                or not columns[1].isdigit() or int(columns[1]) < 1
                or not ENTRY.fullmatch(columns[2]) or not ENTRY.fullmatch(columns[3])
                or not columns[4]):
            raise ValueError(f"{path}:{number}: malformed sentence row")
        rows.append(Sentence(columns[0], int(columns[1]), *columns[2:]))
    if [row.id for row in rows] != [f"S{i:02}" for i in range(1, 12)]:
        raise ValueError(f"{path}: expected S01-S11 exactly once in order")
    if len({row.n10_row for row in rows}) != len(rows):
        raise ValueError(f"{path}: duplicate N10 row")
    return rows


def reached(expected, skills, playbooks):
    if expected.startswith("mmw:"):
        return "mmw" in skills and expected.split(":", 1)[1] in playbooks
    return expected in skills


def has_playbook(commit, slug):
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:mmw-v2/skills/mmw/playbooks/{slug}.md"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def names(value):
    return [] if value == "none" else value.split(",")


def check(path, sentences_path=SENTENCES_PATH):
    try:
        rows = read_sentences(sentences_path)
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"cannot read measurements: {exc}"]
    errors, counts, hashes, after_commits = [], Counter(), {}, set()
    sentences = {row.id: row for row in rows}
    cells = {(row.id, host, phase) for row in rows for host in HOSTS for phase in PHASES}
    if not lines or lines[0] != "# U-7 measurements":
        errors.append("missing # U-7 measurements header")
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("U-"):
            match = CELL_LINE.fullmatch(line)
            if not match:
                errors.append(f"line {number}: malformed cell")
                continue
            sid, host, phase, status, version_host, version, commit, day, evidence = match.groups()
            key = sid, host, phase
            label = " ".join(key)
            counts[key] += 1
            if key not in cells:
                errors.append(f"line {number}: unexpected cell {label}")
            if version_host != host:
                errors.append(f"{label}: version belongs to {version_host}")
            try:
                date.fromisoformat(day)
            except ValueError:
                errors.append(f"{label}: invalid date {day}")
            if phase == "before" and commit != BEFORE:
                errors.append(f"{label}: before commit is not {BEFORE}")
            if phase == "after":
                after_commits.add(commit)
            if status in ("PASS", "FAIL"):
                subitems = SUBITEMS.fullmatch(evidence)
                if not subitems:
                    errors.append(f"{label}: missing or invalid evidence subitems")
                elif sid in sentences:
                    skills, playbooks, calls, expected, exit_code = subitems.groups()
                    skills, playbooks = names(skills), names(playbooks)
                    if len(set(skills)) != len(skills) or len(set(playbooks)) != len(playbooks):
                        errors.append(f"{label}: duplicate evidence names")
                    if expected != sentences[sid].expected(phase):
                        errors.append(f"{label}: expected entry differs from sentence table")
                    actual = "PASS" if reached(sentences[sid].expected(phase), skills, playbooks) else "FAIL"
                    if actual != status:
                        errors.append(f"{label}: {status} contradicts subitems")
                    if status == "PASS" and int(calls) == 0:
                        errors.append(f"{label}: PASS without a tool call")
                    if status == "FAIL" and int(exit_code) != 0:
                        errors.append(f"{label}: nonzero exit without entry must be CANNOT-RUN-UNATTENDED")
                    if version == "absent":
                        errors.append(f"{label}: absent host cannot produce {status}")
        elif line.lstrip().startswith("CHECKSUM"):
            match = HASH_LINE.fullmatch(line)
            if not match:
                errors.append(f"line {number}: malformed checksum")
                continue
            phase, filename, digest = match.groups()
            key = phase, filename
            if key in hashes:
                errors.append(f"line {number}: duplicate {phase} checksum for {filename}")
            hashes[key] = digest
            if filename not in CONFIG_PATHS:
                errors.append(f"line {number}: unexpected checksum path {filename}")
    for key in sorted(cells):
        if counts[key] != 1:
            errors.append(f"{' '.join(key)}: expected one cell, found {counts[key]}")
    if len(after_commits) != 1 or BEFORE in after_commits:
        errors.append("after cells must share one commit distinct from before")
    else:
        commit = next(iter(after_commits))
        for slug in sorted({row.after.split(":", 1)[1] for row in rows if row.after.startswith("mmw:")}):
            if not has_playbook(commit, slug):
                errors.append(f"after commit {commit} lacks playbooks/{slug}.md")
    for filename in CONFIG_PATHS:
        for phase in PHASES:
            if (phase, filename) not in hashes:
                errors.append(f"{filename}: missing {phase} checksum")
        if all((phase, filename) in hashes for phase in PHASES):
            if hashes[("before", filename)] != hashes[("after", filename)]:
                errors.append(f"{filename}: before/after checksums differ")
    return errors


def report(path):
    errors = check(path)
    if errors:
        print("U7 FAIL")
        print("\n".join(errors))
        return 1
    print("U7 OK 66 cells")
    statuses = Counter(match[4] for line in Path(path).read_text(encoding="utf-8").splitlines()
                       if (match := CELL_LINE.fullmatch(line)))
    print(f"routed {statuses['PASS'] + statuses['FAIL']}/66; "
          f"NEEDS-USER-CONFIG {statuses['NEEDS-USER-CONFIG']}; "
          f"CANNOT-RUN-UNATTENDED {statuses['CANNOT-RUN-UNATTENDED']}; "
          f"PASS {statuses['PASS']}; FAIL {statuses['FAIL']}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=HERE / "results-u7.md")
    return report(parser.parse_args().results)


if __name__ == "__main__":
    sys.exit(main())
