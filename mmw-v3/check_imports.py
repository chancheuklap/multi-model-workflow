#!/usr/bin/env python3
"""Check mmw-v3/imports.tsv against mmw-v3/skills/.

Run from anywhere inside the repository: python3 mmw-v3/check_imports.py

1. Every file under mmw-v3/skills/ has one row, except the files v3 wrote
   itself (mmw-v3/skills/README.md and everything under mmw-mode/), and every
   row's `local` exists. A row whose `local` ends in `/` covers every file
   below it that has no row of its own; links are not followed.
2. Every row's `source` can be read at its `commit`. MMW's own text is read
   with `git show <commit>:<source>`; an upstream repository's text is read
   from the squash commit whose `git-subtree-split:` line names that commit.
3. A row with no mechanical edit and no judgement entry is byte-identical to
   its source, and so is every file a directory row covers. A row for one
   `## <heading>` section compares that section's text, HTML comments left out.

Exit 0 prints `IMPORTS OK <n> rows`. Exit 1 prints one finding per line.
"""
import csv
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                   check=True, cwd=pathlib.Path(__file__).parent).stdout.strip())
SKILLS = ROOT / "mmw-v3" / "skills"
OWN = "chancheuklap/multi-model-workflow"
V3_WRITTEN = ("mmw-v3/skills/README.md", "mmw-v3/skills/mmw-mode/")
# mmw-v3/upstream-pstack/ is a split of cursor/plugins' pstack/ directory, so its
# squash commit names the split, not the cursor/plugins commit. Each line maps a
# cursor/plugins commit to its split and the directory the split was cut from.
# A pull of that subtree adds its line here.
SPLITS = {
    "e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a": ("8224b490d845050775fac05f9d34652815fc361e", "pstack/"),
}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, cwd=ROOT)


def squash_commit(split):
    out = git("log", "--all", "--format=%H", f"--grep=git-subtree-split: {split}").stdout.decode().split()
    return out[0] if out else None


def read_source(row, below=""):
    source = row["source"].split("#")[0] + below
    if row["upstream"] == OWN:
        rev = row["commit"]
    else:
        split, prefix = SPLITS.get(row["commit"], (row["commit"], ""))
        rev = squash_commit(split)
        if prefix and source.startswith(prefix):
            source = source[len(prefix):]
    if rev is None:
        return None
    out = git("show", f"{rev}:{source}")
    return out.stdout if out.returncode == 0 else None


def section(text, heading):
    """The body of the `## <heading>` section, without HTML comments and surrounding blank lines."""
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip() if m else None


def main():
    with open(ROOT / "mmw-v3" / "imports.tsv", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    findings = []
    locals_ = [r["local"] for r in rows]
    dirs = [r for r in rows if r["local"].endswith("/")]
    covered = {}
    for top, _, names in os.walk(SKILLS):
        for name in sorted(names):
            rel = (pathlib.Path(top) / name).relative_to(ROOT).as_posix()
            if rel.startswith(V3_WRITTEN) or rel == V3_WRITTEN[0] or locals_.count(rel) == 1:
                continue
            owners = [r for r in dirs if rel.startswith(r["local"])]
            if len(owners) == 1 and locals_.count(rel) == 0:
                covered.setdefault(owners[0]["local"], []).append(rel)
            else:
                findings.append(f"UNREGISTERED {rel}: {locals_.count(rel)} rows, {len(owners)} directory rows")
    for row in dirs:
        if row["mechanical"] or row["judgement"]:
            findings.append(f"DIRECTORY-EDIT {row['local']}: a directory row lists no edit; give each edited file its own row")
        for rel in covered.get(row["local"], []):
            body = read_source(row, rel[len(row["local"]):])
            if body is None or (ROOT / rel).read_bytes() != body:
                findings.append(f"UNREGISTERED-EDIT {rel}: differs from {row['source']} and has no row of its own")
    for row in rows:
        if row in dirs:
            if not (ROOT / row["local"]).is_dir():
                findings.append(f"MISSING-LOCAL {row['local']}")
            continue
        local = ROOT / row["local"].split("#")[0]
        if not local.is_file():
            findings.append(f"MISSING-LOCAL {row['local']}")
            continue
        body = read_source(row)
        if body is None:
            findings.append(f"SOURCE-UNREADABLE {row['upstream']} {row['source']} @{row['commit'][:8]}")
            continue
        if not row["mechanical"] and not row["judgement"].startswith("J") and "; J" not in row["judgement"]:
            if "#" in row["local"]:
                mine = section(local.read_text(), row["local"].split("#", 1)[1])
                theirs = section(body.decode(), row["source"].split("#", 1)[1])
                same = mine is not None and mine == theirs
            else:
                same = local.read_bytes() == body
            if not same:
                findings.append(f"UNREGISTERED-EDIT {row['local']}: differs from its source and lists no edit")
    if findings:
        print("\n".join(findings))
        return 1
    print(f"IMPORTS OK {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
