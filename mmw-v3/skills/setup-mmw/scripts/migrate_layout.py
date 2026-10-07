#!/usr/bin/env python3
"""Move one checkout's development-effort files from the earlier layouts into `efforts/<effort>/`.

    python3 migrate_layout.py

Run from inside a clone, on the branch to migrate; each branch is migrated on its own,
when work on it starts. The earlier layouts kept one effort's files in several trees;
they move with `git mv`, so history follows them:

    docs/specs/<effort>/<entry>                  efforts/<effort>/<entry>
    prototypes/<effort>/claude-design/           efforts/<effort>/claude-design/
    prototypes/<effort>/example-data/            efforts/<effort>/example-data/
    prototypes/<effort>/README.md                efforts/<effort>/README.md
    prototypes/<effort>/<other entry>            efforts/<effort>/prototypes/<other entry>
    docs/prototypes/<effort>/...                 as prototypes/<effort>/...
    docs/research/<effort>/<entry>               efforts/<effort>/research/<entry>, only for an
                                                 <effort> one of the trees above also holds

A screen contract whose `look:` names a design package inside a prototype directory, of
its own effort or another, has that package moved to its own `efforts/<effort>/claude-design/`.
Every moved `screen-contract.yaml` has its `look:` rewritten to the new path.

Every change is staged and nothing is committed. Prints one `MOVED <from> -> <to>` line per
move and one `REWROTE <contract> baselines.look` line per rewritten baseline, then
`STILL NAMED <n>` when tracked lines outside `efforts/` still name an old path: the
`git grep` it names lists them, for the agent to judge (a history file such as an ADR keeps
the path it was written with). Last comes `LAYOUT MIGRATED <n> changes`, or `LAYOUT OK`
when there was nothing to move. Exit 0 on either. Exit 1, with nothing changed, when a
destination already exists or two sources would land on one destination.
"""
import re
import subprocess
import sys
from pathlib import Path

EFFORT_LEVEL = ("claude-design", "example-data", "README.md")
PROTOTYPE_TREES = ("prototypes", "docs/prototypes")
LOOK = re.compile(r"^([ \t]*look:[ \t]*)(\S+)[ \t]*$", re.M)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check)


def subdirs(path: Path) -> list[Path]:
    return sorted(p for p in path.iterdir() if p.is_dir()) if path.is_dir() else []


def look_of(contract: Path) -> str | None:
    match = LOOK.search(contract.read_text(encoding="utf-8"))
    return match.group(2).strip("'\"").rstrip("/") if match else None


def plan(root: Path) -> list[tuple[str, str]]:
    moves = []
    efforts = set()
    for effort in subdirs(root / "docs" / "specs"):
        efforts.add(effort.name)
        contract = effort / "screen-contract.yaml"
        look = look_of(contract) if contract.is_file() else None
        own = f"prototypes/{effort.name}/claude-design"
        if (look and look.endswith("/claude-design") and look.split("/")[0] in ("prototypes", "docs")
                and look not in (own, "docs/" + own) and (root / look).is_dir()):
            moves.append((look, f"efforts/{effort.name}/claude-design"))
        for entry in sorted(effort.iterdir()):
            moves.append((f"docs/specs/{effort.name}/{entry.name}", f"efforts/{effort.name}/{entry.name}"))
    for tree in PROTOTYPE_TREES:
        for effort in subdirs(root / tree):
            efforts.add(effort.name)
            for entry in sorted(effort.iterdir()):
                old = f"{tree}/{effort.name}/{entry.name}"
                where = "" if entry.name in EFFORT_LEVEL else "prototypes/"
                moves.append((old, f"efforts/{effort.name}/{where}{entry.name}"))
    for effort in subdirs(root / "docs" / "research"):
        if effort.name in efforts:
            for entry in sorted(effort.iterdir()):
                moves.append((f"docs/research/{effort.name}/{entry.name}",
                              f"efforts/{effort.name}/research/{entry.name}"))
    return moves


def tracked(root: Path, rel: str) -> bool:
    return bool(git(root, "ls-files", "--", rel).stdout.strip())


def rewrite_look(path: Path, moves: list[tuple[str, str]]) -> bool:
    text = path.read_text(encoding="utf-8")

    def new_path(match: re.Match) -> str:
        value = match.group(2).strip("'\"").rstrip("/")
        for old, new in moves:
            if value == old or value.startswith(old + "/"):
                return match.group(1) + new + value[len(old):]
        return match.group(0)

    updated = LOOK.sub(new_path, text)
    if updated != text:
        path.write_text(updated, encoding="utf-8")
    return updated != text


def main() -> int:
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0:
        print("not inside a git repository", file=sys.stderr)
        return 2
    root = Path(top.stdout.strip())
    moves = plan(root)
    if not moves:
        print("LAYOUT OK")
        return 0
    targets = [new for _, new in moves]
    refused = [f"{new} already exists" for new in targets if (root / new).exists()]
    refused += [f"two sources would move to {new}" for new in sorted(set(targets)) if targets.count(new) > 1]
    if refused:
        for reason in refused:
            print(f"refused: {reason}; move or merge it by hand, then run this again", file=sys.stderr)
        return 1
    done = []
    for old, new in moves:
        source = root / old
        if not source.exists() or (source.is_dir() and not any(p.is_file() for p in source.rglob("*"))):
            continue
        (root / new).parent.mkdir(parents=True, exist_ok=True)
        if tracked(root, old):
            git(root, "mv", "--", old, new)
        else:
            (root / old).rename(root / new)
        done.append((old, new))
        print(f"MOVED {old} -> {new}")
    for contract in sorted((root / "efforts").glob("*/screen-contract.yaml")):
        if rewrite_look(contract, done):
            git(root, "add", "--", str(contract.relative_to(root)))
            print(f"REWROTE {contract.relative_to(root)} baselines.look")
    for parent in ("docs/specs", "docs/research", *PROTOTYPE_TREES):
        for leftover in sorted((root / parent).rglob("*"), reverse=True) if (root / parent).is_dir() else []:
            if leftover.is_dir() and not any(leftover.iterdir()):
                leftover.rmdir()
        if (root / parent).is_dir() and not any((root / parent).iterdir()):
            (root / parent).rmdir()
    patterns = ["docs/specs/", "docs/prototypes/", "(^|[^/[:alnum:]_-])prototypes/"]
    patterns += sorted({f"docs/research/{old.split('/')[2]}/" for old, _ in done if old.startswith("docs/research/")})
    grep = ["grep", "-n", "-I", "-E"] + [arg for p in patterns for arg in ("-e", p)]
    hits = git(root, *grep, "--", ".", ":!efforts", check=False).stdout.splitlines()
    if hits:
        shown = " ".join(f"'{a}'" if " " in a or "(" in a else a for a in grep)
        print(f"STILL NAMED {len(hits)}: git {shown} -- . ':!efforts' lists them")
    print(f"LAYOUT MIGRATED {len(done)} changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
