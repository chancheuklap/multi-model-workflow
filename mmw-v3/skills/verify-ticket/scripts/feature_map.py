#!/usr/bin/env python3
"""Lint the feature map in the repository this process is run from.

    python3 feature_map.py lint

Reads `docs/features/<product>/` and the screen contracts at
`efforts/<effort>/screen-contract.yaml`. The same read is `lint(root)`, for a
caller that already holds the repository root.

Exit 0 prints `FEATURE MAP OK <n> features`, where n is the number of feature
files. Exit 1 prints one line per problem. Exit 2 refuses when the map cannot
be read. A `check: none:` line is a `NOTE` and does not change the exit code.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

FEATURE_SECTIONS = (
    "Sub-features",
    "How to get to it (user POV)",
    "Driving it",
    "Gotchas",
)
README_SECTIONS = (
    "Baseline preconditions",
    "Driving conventions",
    "Proof and skip reporting",
    "Feature entry contract",
    "Features",
)
SOURCE_EXPECTED = "one of #<n>, #<n> §<k>, row:<id>, ADR <number>, existing <YYYY-MM-DD>"
OPERATORS = {"&&", "||", ";", "|"}
UNITTEST_TARGET = re.compile(r"[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*){2,}")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
H1 = re.compile(r"^#\s+\S")
H2 = re.compile(r"^##\s+(.*?)\s*$")
BULLET = re.compile(r"^- ")
FIELD = re.compile(r"^[ \t]+(source|check):\s*(.*)$")
ISSUE = re.compile(r"^#\d+$")
SECTION_SOURCE = re.compile(r"^#\d+ §\d+$")
ROW_SOURCE = re.compile(r"^row:(\S+)$")
ADR_SOURCE = re.compile(r"^ADR \d+$")
EXISTING_SOURCE = re.compile(r"^existing (\d{4}-\d{2}-\d{2})$")
PY_EXT = re.compile(r"\.(?:sh|py|mjs|js|md|yaml|yml)$")

_refusal = None


def refuse(what: str, why: str, next_step: str) -> str:
    """The three-part refusal. A missing sibling says the checkout is incomplete."""
    global _refusal
    if _refusal is None:
        path = (Path(__file__).resolve().parents[2] / "ui-acceptance" / "scripts"
                / "refusal.py")
        if not path.is_file():
            def _refusal(what: str, why: str, next_step: str) -> str:
                return (f"{path} is absent, so this checkout cannot build a refusal. "
                        f"{what} {why} {next_step}")
        else:
            spec = importlib.util.spec_from_file_location("mmw_feature_map_refusal", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _refusal = module.refusal
    return _refusal(what, why, next_step)


def problem(path: str, line: int, rule: str, expected: str, actual: str) -> str:
    loc = f"{path}:{line}"
    return f"{loc}: {rule}: expected {expected}; actual {actual}; evidence {loc}"


def note_line(path: str, line: int, reason: str) -> str:
    return f"NOTE {path}:{line}: none: {reason}"


def show(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def last_line(lines: list[str]) -> int:
    return len(lines) if lines else 1


def h2_sections(lines: list[str]) -> list[tuple[int, str, list[tuple[int, str]]]]:
    """Each level-2 heading as its line, its title, and the body lines under it."""
    sections: list[tuple[int, str, list[tuple[int, str]]]] = []
    current: tuple[int, str] | None = None
    body: list[tuple[int, str]] = []
    for number, line in enumerate(lines, 1):
        match = H2.match(line)
        if match:
            if current is not None:
                sections.append((current[0], current[1], body))
            current = (number, match.group(1))
            body = []
        elif current is not None:
            body.append((number, line))
    if current is not None:
        sections.append((current[0], current[1], body))
    return sections


def feature_shape(rel: str, lines: list[str]) -> list[str]:
    findings = []
    h1 = next((number for number, line in enumerate(lines, 1) if H1.match(line)), None)
    if h1 is None:
        findings.append(problem(rel, 1, "shape", "an H1", "absent"))
    first_h2 = next((number for number, line in enumerate(lines, 1) if H2.match(line)), None)
    if h1 is not None:
        stop = (first_h2 - 1) if first_h2 else len(lines)
        paragraph = any(line.strip() and not line.startswith("#") for line in lines[h1:stop])
        if not paragraph:
            findings.append(problem(rel, min(h1 + 1, last_line(lines)), "shape",
                                    "a paragraph", "absent"))
    sections = h2_sections(lines)
    present = [title for _line, title, _body in sections if title in FEATURE_SECTIONS]
    expected_order = [title for title in FEATURE_SECTIONS if title in present]
    if present != expected_order:
        ordered = [(line, title) for line, title, _body in sections if title in FEATURE_SECTIONS]
        for (line, got), want in zip(ordered, expected_order):
            if got != want:
                findings.append(problem(rel, line, "shape", f"## {want}", f"## {got}"))
                break
    for title in FEATURE_SECTIONS:
        if title not in present:
            findings.append(problem(rel, last_line(lines), "shape", f"## {title}", "absent"))
    return findings


def readme_shape(rel: str, lines: list[str]) -> list[str]:
    present = {title for _line, title, _body in h2_sections(lines)}
    return [problem(rel, last_line(lines), "readme", f"## {title}", "absent")
            for title in README_SECTIONS if title not in present]


def index_names(product: Path, readme: Path, body: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Feature-file names the Features section links, with the line of each link."""
    named = []
    for number, line in body:
        for url in LINK.findall(line):
            path = url.split("#", 1)[0].split("?", 1)[0]
            if "://" in path or not path.endswith(".md"):
                continue
            resolved = (readme.parent / path).resolve()
            try:
                rel = resolved.relative_to(product.resolve())
            except ValueError:
                named.append((number, Path(path).name))
                continue
            if len(rel.parts) == 1 and rel.name != "README.md":
                named.append((number, rel.name))
    return named


def index_findings(root: Path, product: Path, readme: Path | None,
                   sections: list[tuple[int, str, list[tuple[int, str]]]],
                   files: list[Path]) -> list[str]:
    on_disk = {path.name for path in files}
    if readme is None:
        return [problem(show(root, path), 1, "index",
                        f"a Features entry for {path.name}", "absent")
                for path in files]
    body: list[tuple[int, str]] = []
    for _line, title, section_body in sections:
        if title == "Features":
            body.extend(section_body)
    linked = index_names(product, readme, body)
    linked_names = {name for _line, name in linked}
    findings = []
    for line, name in linked:
        if name not in on_disk:
            findings.append(problem(show(root, readme), line, "index",
                                    f"{name} in {product.name}/", "absent"))
    for path in files:
        if path.name not in linked_names:
            findings.append(problem(show(root, path), 1, "index",
                                    f"a Features entry for {path.name}", "absent"))
    return findings


def source_kind(value: str) -> tuple[str, str | None]:
    """`ok`, `row` plus its id, or `bad`."""
    if ISSUE.match(value) or SECTION_SOURCE.match(value) or ADR_SOURCE.match(value):
        return "ok", None
    match = ROW_SOURCE.match(value)
    if match:
        return "row", match.group(1)
    match = EXISTING_SOURCE.match(value)
    if match:
        try:
            datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            return "bad", None
        return "ok", None
    return "bad", None


def subfeature_rows(body: list[tuple[int, str]]) -> list[dict]:
    items: list[dict] = []
    current: dict | None = None
    for number, line in body:
        if BULLET.match(line):
            if current is not None:
                items.append(current)
            current = {"line": number, "source": None, "check": None}
        elif current is not None and (match := FIELD.match(line)):
            key = match.group(1)
            if current[key] is None:
                current[key] = (number, match.group(2).strip())
    if current is not None:
        items.append(current)
    return items


def split_command(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def join_path(root: Path, cwd: Path, token: str) -> Path | None:
    """A repository path named by `token`, or None when `token` is not one."""
    if token.startswith("-") or "://" in token:
        return None
    if "/" not in token and not PY_EXT.search(token):
        return None
    path = Path(token)
    if path.is_absolute():
        resolved = path
    else:
        base = cwd if cwd.is_absolute() else root / cwd
        resolved = base / path
    try:
        resolved.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return resolved


def unittest_defined(text: str, class_name: str, case_name: str) -> bool:
    lines = text.splitlines()
    start = None
    class_indent = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(\s*)class\s+" + re.escape(class_name) + r"\b", line)
        if match:
            start = index
            class_indent = len(match.group(1))
            break
    if start is None:
        return False
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent <= class_indent and stripped.startswith("class "):
            return False
        if indent > class_indent and re.match(r"(?:async\s+)?def\s+" + re.escape(case_name) + r"\b",
                                              stripped):
            return True
    return False


def inspect_check(root: Path, command: str) -> list[tuple[str, str]]:
    """`(expected, actual)` for every target of `command` that is not there.

    A journey directory is resolved from the repository root. `journey.py run`
    names that directory, and the `cd` earlier in the command does not move it.
    """
    tokens = split_command(command)
    missing: list[tuple[str, str]] = []
    seen: set[str] = set()
    cwd = Path(".")
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in OPERATORS:
            index += 1
            continue
        if token == "cd" and index + 1 < len(tokens) and tokens[index + 1] not in OPERATORS:
            dest = Path(tokens[index + 1])
            cwd = dest if dest.is_absolute() else cwd / dest
            index += 2
            continue
        segment: list[str] = []
        while index < len(tokens) and tokens[index] not in OPERATORS:
            segment.append(tokens[index])
            index += 1
        if not segment:
            continue
        missing.extend(segment_targets(root, cwd, segment, seen))
    return missing


def remember(seen: set[str], label: str) -> bool:
    if label in seen:
        return False
    seen.add(label)
    return True


def segment_targets(root: Path, cwd: Path, segment: list[str], seen: set[str]) -> list[tuple[str, str]]:
    missing = []
    command = segment[0]
    for cursor, token in enumerate(segment):
        if token == "journey.py" or token.endswith("/journey.py"):
            if cursor + 2 < len(segment) and segment[cursor + 1] == "run":
                name = segment[cursor + 2]
                if name.startswith("-"):
                    continue
                label = f".mmw/journeys/{name}/"
                if remember(seen, label) and not (root / ".mmw" / "journeys" / name).is_dir():
                    missing.append((label, "absent"))
        if token in ("python", "python3") or token.endswith(("/python", "/python3")):
            if cursor + 2 < len(segment) and segment[cursor + 1] == "-m" and segment[cursor + 2] == "unittest":
                for target in segment[cursor + 3:]:
                    if not UNITTEST_TARGET.fullmatch(target):
                        continue
                    missing.extend(unittest_target(root, cwd, target, seen))
    if command in ("node", "nodejs") or command.endswith(("/node", "/nodejs")):
        arguments = [token for token in segment[1:] if not token.startswith("-")]
        if arguments:
            missing.extend(path_target(root, cwd, arguments[0], seen))
    for token in segment[1:]:
        if token.startswith("-") or token in ("python", "python3", "node", "nodejs"):
            continue
        if "/" not in token and not PY_EXT.search(token):
            continue
        missing.extend(path_target(root, cwd, token, seen))
    return missing


def path_target(root: Path, cwd: Path, token: str, seen: set[str]) -> list[tuple[str, str]]:
    resolved = join_path(root, cwd, token)
    if resolved is None:
        return []
    label = show(root, resolved) if resolved.exists() else _display(root, cwd, token)
    if not remember(seen, label):
        return []
    if resolved.exists():
        return []
    return [(label, "absent")]


def _display(root: Path, cwd: Path, token: str) -> str:
    path = Path(token)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return token
    base = cwd if cwd.is_absolute() else Path(cwd)
    return (base / path).as_posix()


def unittest_target(root: Path, cwd: Path, target: str, seen: set[str]) -> list[tuple[str, str]]:
    parts = target.split(".")
    module, class_name, case_name = parts[:-2], parts[-2], parts[-1]
    relative = Path(*module).with_suffix(".py")
    resolved = join_path(root, cwd, relative.as_posix())
    if resolved is None:
        return []
    label = _display(root, cwd, relative.as_posix())
    if not resolved.is_file():
        if not remember(seen, label):
            return []
        return [(label, "absent")]
    text = read_text(resolved)
    if text is None:
        return [(label, "unreadable")]
    qualified = f"{class_name}.{case_name} defined in {label}"
    if not remember(seen, qualified):
        return []
    if unittest_defined(text, class_name, case_name):
        return []
    return [(qualified, "absent")]


def load_yaml(path: Path):
    """The document, `{}` when it is empty, or None when it cannot be read.

    `pyyaml` when this interpreter has it, otherwise `uv run --with pyyaml`, the
    same fallback `verify-ticket.py` uses for a screen contract.
    """
    text = read_text(path)
    if text is None:
        return None
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError:
            return None
    try:
        out = subprocess.run(
            ["uv", "run", "--with", "pyyaml", "python", "-c",
             "import json,sys,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()) or {}, "
             "default=str))"],
            input=text, capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        loaded = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else {}


def row_ids(root: Path) -> tuple[set[str], str | None]:
    """Every row id under `efforts/*/screen-contract.yaml`, or the file that did not read."""
    efforts = root / "efforts"
    found: set[str] = set()
    if not efforts.is_dir():
        return found, None
    for path in sorted(efforts.glob("*/screen-contract.yaml")):
        document = load_yaml(path)
        if document is None:
            return found, show(root, path)
        rows = document.get("rows") if isinstance(document, dict) else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("id"), str):
                found.add(row["id"])
    return found, None


def lint_product(root: Path, product: Path, rows: set[str],
                  judge_rows: bool) -> tuple[list[str], list[str], int, bool, str | None]:
    findings: list[str] = []
    notes: list[str] = []
    saw_row = False
    readme_path = product / "README.md"
    readme_text = read_text(readme_path) if readme_path.is_file() else None
    if readme_path.is_file() and readme_text is None:
        return [], [], 0, False, refuse_unreadable(show(root, readme_path))
    files = sorted(path for path in product.glob("*.md") if path.name != "README.md" and path.is_file())
    sections: list[tuple[int, str, list[tuple[int, str]]]] = []
    if readme_text is None:
        rel = show(root, readme_path)
        findings.extend(problem(rel, 1, "readme", f"## {title}", "absent")
                        for title in README_SECTIONS)
    else:
        readme_lines = readme_text.splitlines()
        sections = h2_sections(readme_lines)
        findings.extend(readme_shape(show(root, readme_path), readme_lines))
    findings.extend(index_findings(root, product, readme_path if readme_text is not None else None,
                                   sections, files))
    for path in files:
        text = read_text(path)
        rel = show(root, path)
        if text is None:
            return [], [], 0, False, refuse_unreadable(rel)
        lines = text.splitlines()
        findings.extend(feature_shape(rel, lines))
        for _line, title, body in h2_sections(lines):
            if title != "Sub-features":
                continue
            for item in subfeature_rows(body):
                source = item["source"]
                check = item["check"]
                if source is None:
                    findings.append(problem(rel, item["line"], "source", "a source", "absent"))
                else:
                    line, value = source
                    kind, row_id = source_kind(value)
                    if kind == "bad":
                        findings.append(problem(rel, line, "source", SOURCE_EXPECTED,
                                                value if value else "absent"))
                    elif kind == "row":
                        saw_row = True
                        if judge_rows and row_id not in rows:
                            findings.append(problem(
                                rel, line, "source",
                                f"row id {row_id} in a screen contract", "absent"))
                if check is None:
                    findings.append(problem(rel, item["line"], "check", "a check", "absent"))
                    continue
                line, value = check
                if value.startswith("none:"):
                    notes.append(note_line(rel, line, value[len("none:"):].strip()))
                    continue
                if not value:
                    findings.append(problem(rel, line, "check", "a command", "absent"))
                    continue
                for expected, actual in inspect_check(root, value):
                    findings.append(problem(rel, line, "check", expected, actual))
    return findings, notes, len(files), saw_row, None


def refuse_unreadable(rel: str) -> str:
    return refuse(
        f"{rel} is not readable text (0 feature files read from it).",
        "The lint cannot judge a file it cannot read.",
        "Next: save it as UTF-8 text and run feature_map.py lint again.",
    )


def refuse_features(what: str) -> str:
    return refuse(
        what,
        "The lint has no feature map to read.",
        "Next: read mmw-v3/skills/mmw-mode/references/feature-map.md "
        "and add docs/features/<product>/.",
    )


def lint(root: Path | str) -> tuple[int, list[str]]:
    """Exit code and report lines for the feature map in `root`."""
    root = Path(root)
    features = root / "docs" / "features"
    if not features.exists():
        return 2, [refuse_features("docs/features/ is absent (0 files read).")]
    if not features.is_dir():
        return 2, [refuse_features("docs/features/ is not a directory (0 files read).")]
    rows, unreadable = row_ids(root)
    findings: list[str] = []
    notes: list[str] = []
    count = 0
    saw_row = False
    products = sorted(path for path in features.iterdir()
                      if path.is_dir() and not path.name.startswith("."))
    for product in products:
        product_findings, product_notes, product_count, product_row, blocked = lint_product(
            root, product, rows, unreadable is None)
        if blocked is not None:
            return 2, [blocked]
        findings.extend(product_findings)
        notes.extend(product_notes)
        count += product_count
        saw_row = saw_row or product_row
    if saw_row and unreadable is not None:
        return 2, [refuse(
            f"{unreadable} is not readable (its row ids were not read).",
            "A row: source cannot be checked against a contract that did not parse.",
            "Next: correct that screen-contract.yaml and run feature_map.py lint again.",
        )]
    if findings:
        return 1, findings + notes
    return 0, notes + [f"FEATURE MAP OK {count} features"]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv != ["lint"]:
        print(refuse(
            "feature_map.py was started without lint.",
            "The only command is lint, from the repository root.",
            "Next: run feature_map.py lint from the repository root.",
        ), file=sys.stderr)
        return 2
    code, lines = lint(Path.cwd())
    stream = sys.stderr if code == 2 else sys.stdout
    for line in lines:
        print(line, file=stream)
    return code


if __name__ == "__main__":
    sys.exit(main())
