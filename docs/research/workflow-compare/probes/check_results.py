#!/usr/bin/env python3
"""Read the 13 measurements from ticket #611 without starting a host."""

import argparse
from collections import Counter
from datetime import date
from pathlib import Path
import re
import sys

CELLS = {(probe, host) for probe in ("U-1", "U-2", "U-3", "U-17")
         for host in ("claude", "codex", "grok")} | {("U-9", "herdr")}
CONFIG_PATHS = ("~/.claude/settings.json", "~/.codex/config.toml",
                "~/.grok/config.toml", "~/.mmw/models.json", "~/.mmw/installed-root")
CELL_LINE = re.compile(
    r"^(U-\d+) (\S+) (PASS|FAIL|NEEDS-USER-CONFIG|CANNOT-RUN-UNATTENDED) "
    r"(\S+) (\d{4}-\d{2}-\d{2}) : (\S.*)$")
HASH_LINE = re.compile(r"^CHECKSUM (before|after) (\S+) (absent|[0-9a-f]{64})$")
SUBITEMS = {
    "U-2": (("session-start", "yes"), ("subagent-start", "yes"), ("prompt-submit", "yes")),
    "U-3": (("nested-md-scanned", "no"), ("symlink-copy-readable", "yes")),
}


def check(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return [f"cannot read {path}: {exc}"]
    errors = []
    counts = Counter()
    hashes = {}
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("U-"):
            match = CELL_LINE.fullmatch(line)
            if not match:
                errors.append(f"line {number}: malformed cell")
                continue
            probe, host, status, version, day, evidence = match.groups()
            key = (probe, host)
            counts[key] += 1
            if key not in CELLS:
                errors.append(f"line {number}: unexpected cell {probe} {host}")
            try:
                date.fromisoformat(day)
            except ValueError:
                errors.append(f"{probe} {host}: invalid date {day}")
            if status in ("PASS", "FAIL") and probe in SUBITEMS:
                pattern = " ".join(re.escape(name) + r"=(yes|no)"
                                   for name, _ in SUBITEMS[probe])
                subitems = re.match(pattern + r"(?=;|\s|$)", evidence)
                if not subitems:
                    errors.append(f"{probe} {host}: missing or invalid subitems at evidence start")
                else:
                    expected = tuple(value for _, value in SUBITEMS[probe])
                    passing = subitems.groups() == expected
                    if (status == "PASS") != passing:
                        errors.append(f"{probe} {host}: {status} contradicts subitems")
        elif line.lstrip().startswith("CHECKSUM"):
            match = HASH_LINE.fullmatch(line)
            if not match:
                errors.append(f"line {number}: malformed checksum")
                continue
            phase, filename, digest = match.groups()
            filename = str(Path(filename).expanduser())
            key = (phase, filename)
            if key in hashes:
                errors.append(f"line {number}: duplicate {phase} checksum for {filename}")
            hashes[key] = digest
    for key in sorted(CELLS):
        if counts[key] != 1:
            errors.append(f"{' '.join(key)}: expected one cell, found {counts[key]}")
    expected_paths = {str(Path(p).expanduser()) for p in CONFIG_PATHS}
    for filename in sorted(expected_paths):
        for phase in ("before", "after"):
            if (phase, filename) not in hashes:
                errors.append(f"{filename}: missing {phase} checksum")
        if ("before", filename) in hashes and ("after", filename) in hashes:
            if hashes[("before", filename)] != hashes[("after", filename)]:
                errors.append(f"{filename}: before/after checksums differ")
    for _, filename in hashes:
        if filename not in expected_paths:
            errors.append(f"unexpected checksum path {filename}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path(__file__).with_name("results.md"))
    args = parser.parse_args()
    errors = check(args.results)
    if errors:
        print("PROBES FAIL")
        print("\n".join(errors))
        return 1
    print(f"PROBES OK {len(CELLS)} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
