#!/usr/bin/env python3
"""Move one checkout's old root `.mmw/` layout into `.mmw/<product>/`.

    python3 migrate_products.py <product>

Run from inside a clone, on the branch to migrate. `<product>` is given by the
person running the command and uses only lowercase letters, digits and hyphens.

`git mv` moves `.mmw/harness/`, `.mmw/stories/` and `.mmw/journeys/` into
`.mmw/<product>/`. Product keys in the root `.mmw/target.json` move into
`.mmw/<product>/target.json`. A command string that names `.mmw/harness/`,
`.mmw/stories/` or `.mmw/journeys` names the new path. The root file keeps
`checks` and `needs`, and its `products` list becomes `[<product>]`.
`.mmw/AGENTS.md` and `.mmw/CLAUDE.md` stay at the root.

Each `efforts/*/screen-contract.yaml` gains a top-level `product` key.
Under `docs/features/`, `journey.py run <flow>` becomes
`journey.py run <product>/<flow>`.

Every change is staged and nothing is committed. One `MOVED <from> -> <to>`
line per directory, one `REWROTE <file> product` or `REWROTE <file> journeys`
line per rewritten file, then `STILL NAMED <n>` when a tracked line still names
an old path (the `git grep` on that line lists them) and `CLIMBS <n>` when a
moved file still finds the repository root by counting parents (`parents[2]`,
`../..`). The count on `CLIMBS` is the number of files, which the same line
lists. Last is `PRODUCTS MIGRATED <n> changes`, where `<n>` is the moved
directories, plus one for the `target.json` split, plus each rewritten file.
`PRODUCTS OK` when there was nothing to move. Exit 0 on either. Exit 2, with
nothing changed, when the name is not allowed, the checkout is not a git
repository, or `.mmw/<product>/` already exists while the old layout is still
at the root.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

DIRS = ("harness", "stories", "journeys")
ROOT_KEYS = ("checks", "needs")
KEPT = {"checks", "needs", "products"}
NAME = re.compile(r"^[a-z0-9-]+$")
OLD_PATH = re.compile(r"\.mmw/(harness/|stories/|journeys(?=/|$|[\s\"']))")
JOURNEY_RUN = re.compile(r"(journey\.py run )([A-Za-z0-9][A-Za-z0-9_-]*)(?![A-Za-z0-9_/-])")
TOP_PRODUCT = re.compile(r"(?m)^product:")
CLIMB = re.compile(r"parents\[\d+\]|(\.\./){2,}")
GREP = [
    "grep", "-n", "-I", "-E",
    "-e", r"\.mmw/harness(/|[^A-Za-z0-9_./-]|$)",
    "-e", r"\.mmw/stories(/|[^A-Za-z0-9_./-]|$)",
    "-e", r"\.mmw/journeys(/|[^A-Za-z0-9_./-]|$)",
]


def refusal():
    path = Path(__file__).resolve().parents[2] / "ui-acceptance" / "scripts" / "refusal.py"
    spec = importlib.util.spec_from_file_location("mmw_refusal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.refusal


def git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check)


def refuse(say, what, why, next_step):
    print(say(what, why, next_step), file=sys.stderr)
    return 2


def rewrite_text(text, product):
    return OLD_PATH.sub(lambda match: f".mmw/{product}/{match.group(1)}", text)


def rewrite_value(value, product):
    if isinstance(value, str):
        return rewrite_text(value, product)
    if isinstance(value, list):
        return [rewrite_value(item, product) for item in value]
    if isinstance(value, dict):
        return {key: rewrite_value(item, product) for key, item in value.items()}
    return value


def split_target(doc, product):
    root_doc = {key: doc[key] for key in ROOT_KEYS if key in doc}
    root_doc["products"] = [product]
    product_doc = {}
    for key, value in doc.items():
        if key in KEPT:
            continue
        product_doc[key] = rewrite_value(value, product)
    return root_doc, product_doc


def old_layout(root, doc, had_file):
    if any((root / ".mmw" / name).exists() for name in DIRS):
        return True
    if not had_file:
        return False
    return any(key not in KEPT for key in doc)


def tracked(root, rel):
    return bool(git(root, "ls-files", "--", rel).stdout.strip())


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def add_product_key(path, product):
    text = read_text(path)
    if text is None or TOP_PRODUCT.search(text):
        return False
    path.write_text(f"product: {product}\n{text}", encoding="utf-8")
    return True


def rewrite_journeys(path, product):
    text = read_text(path)
    if text is None:
        return False
    updated = JOURNEY_RUN.sub(lambda match: f"{match.group(1)}{product}/{match.group(2)}", text)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def climbing_files(root, moved):
    found = []
    for rel in moved:
        base = root / rel
        files = [base] if base.is_file() else [path for path in base.rglob("*") if path.is_file()]
        for path in files:
            text = read_text(path)
            if text is not None and CLIMB.search(text):
                found.append(path.relative_to(root).as_posix())
    return sorted(found)


def shell_join(args):
    shown = []
    for arg in args:
        if any(char in arg for char in " ()\\$|"):
            shown.append("'" + arg.replace("'", "'\\''") + "'")
        else:
            shown.append(arg)
    return " ".join(shown)


def main():
    say = refusal()
    script = Path(__file__).resolve()
    if len(sys.argv) != 2 or not NAME.fullmatch(sys.argv[1]):
        given = sys.argv[1] if len(sys.argv) == 2 else " ".join(sys.argv[1:]) or "(none)"
        return refuse(
            say,
            f"product name {given} is not lowercase letters, digits and hyphens",
            "a product directory is named that way.",
            f"Run python3 {script} <product> with a name of that shape.",
        )
    product = sys.argv[1]
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode != 0:
        return refuse(
            say,
            "this directory is not inside a git repository",
            "the move uses git mv, so history follows the files.",
            "Run this from inside a clone, on the branch to migrate.",
        )
    root = Path(top.stdout.strip())
    target = root / ".mmw" / "target.json"
    had_file = target.is_file()
    doc = json.loads(target.read_text(encoding="utf-8")) if had_file else {}
    if not old_layout(root, doc, had_file):
        print("PRODUCTS OK")
        return 0
    destination = root / ".mmw" / product
    if destination.exists():
        return refuse(
            say,
            f".mmw/{product}/ already exists",
            "the old layout is still at the root, and this command will not overwrite a product directory.",
            f"Move .mmw/{product} aside, then run python3 {script} {product} again.",
        )
    destination.mkdir(parents=True)
    moves = []
    for name in DIRS:
        old = f".mmw/{name}"
        new = f".mmw/{product}/{name}"
        source = root / old
        if not source.exists():
            continue
        if tracked(root, old):
            git(root, "mv", "--", old, new)
        else:
            source.rename(destination / name)
        moves.append((old, new))
        print(f"MOVED {old} -> {new}")
    root_doc, product_doc = split_target(doc, product)
    target.write_text(json.dumps(root_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "target.json").write_text(
        json.dumps(product_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rewritten = []
    for contract in sorted((root / "efforts").glob("*/screen-contract.yaml")):
        rel = contract.relative_to(root).as_posix()
        if add_product_key(contract, product):
            rewritten.append(rel)
            print(f"REWROTE {rel} product")
    features = root / "docs" / "features"
    if features.is_dir():
        for path in sorted(item for item in features.rglob("*") if item.is_file()):
            rel = path.relative_to(root).as_posix()
            if rewrite_journeys(path, product):
                rewritten.append(rel)
                print(f"REWROTE {rel} journeys")
    add = [".mmw/target.json", f".mmw/{product}/target.json", *[new for _, new in moves], *rewritten]
    git(root, "add", "--", *add)
    hits = git(root, *GREP, "--", ".", check=False).stdout.splitlines()
    if hits:
        print(f"STILL NAMED {len(hits)}: git {shell_join(GREP)} -- . lists them")
    climbing = climbing_files(root, [new for _, new in moves])
    if climbing:
        print(f"CLIMBS {len(climbing)}: {' '.join(climbing)}")
    print(f"PRODUCTS MIGRATED {len(moves) + 1 + len(rewritten)} changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
