#!/usr/bin/env python3
"""Read and check a repository's `.mmw/target.json`.

The old layout answers one product in that file. `FIELDS` lists its keys, and
`--check` names every field still missing. The new layout keeps `checks`,
`products` and `needs` on the root, and one product in `.mmw/<product>/target.json`.
`--product <name>` selects that product. With one product the name can be omitted.
`--check` exits 0 when the layout in front of it is complete. `--validate` prints
the first problem only. `discover` prints an origin-class address plus `instance`.
`journey.py` runs every command the selected product declares through `run_command`,
and imports `discover`.
"""

from __future__ import annotations

import graphlib
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from lease import (  # noqa: E402
    PORT_STRIDE,
    PRODUCT_NAME,
    TargetJSONError,
    leased_environment,
    product_gap,
    product_layout,
    read_target_json,
    worktree_of,
)


# ---------------------------------------------------------------- repository config
@dataclass(frozen=True)
class Field:
    """One key a repository answers in `.mmw/target.json`: its name, the shape the
    value takes, what it does in one sentence, and one example."""

    key: str
    shape: str
    what: str
    example: str
    required: bool = True


# The keys every repository answers, whatever kind of product it has. `discover`
# prints an origin-class address plus `instance`. `checks` is read by
# `verify-ticket.py`'s `target_json_checks` for `dispatch.sh`'s merge, not by this file, and is listed so the file has one
# account.
DISCOVER_PRINTS: tuple[tuple[str, str], ...] = (
    ("origin", "where the product is served, e.g. http://127.0.0.1:8000"),
    ("instance", "a readable name for this run"),
)

FIELDS: tuple[Field, ...] = (
    Field("start", "command",
          "brings the product up with everything it needs — backing service, data "
          "directory, log — chosen inside the command from the lease in its environment, "
          "and returns once the product answers and can be driven; idempotent: leaves its "
          "own current product alone, clears its own stale one, refuses over anyone else's",
          '"uv run python .mmw/harness/target.py start"'),
    Field("stop", "command",
          "ends what start started and nothing else, and exits 0 with nothing of its own "
          "to end; the only way a run may end a process",
          '"uv run python .mmw/harness/target.py stop"'),
    Field("discover", "command",
          "prints one JSON object of origin-class addresses plus `instance`, a readable "
          "name for this run",
          '"uv run python .mmw/harness/target.py discover"'),
    Field("stories", "command",
          "brings up the story service and prints its `origin`",
          '"uv run python .mmw/harness/target.py stories"'),
    Field("journeys", "directory",
          "the directory of journey scripts; default .mmw/journeys",
          '".mmw/journeys"',
          required=False),
    Field("leaves_machine", "list of strings",
          "each thing this product does in a run that reaches past this machine, naming "
          "the file that records it under MMW_AUTOMATION=1; [] when nothing leaves",
          '["tools/opened.py — system browser; under MMW_AUTOMATION=1 the URL is written '
          'to $MMW_DATA_DIR/opened-urls"]'),
    Field("harness_markers", "list of strings",
          "the strings this product uses only to make itself drivable; [] when it has none",
          '["/api/dev/", "transport off", "__stub"]'),
    Field("checks", "list",
          "the repository's own checks, run by `dispatch.sh` on each ticket's merge result "
          "before it pushes; the ui-acceptance skill's references/product-answers.md says the "
          "shape",
          '["uv run ruff check .", {"run": "uv run pytest -q", "timeout": 1800}]',
          required=False),
)


def repo_root(start: Path | None = None) -> Path:
    """The directory that holds `.mmw/target.json`, else the git worktree.

    A fixture or a path inside a consuming repository is the repository that
    answered. The worktree is the fallback when nobody has answered yet.
    """
    here = (start or Path.cwd()).resolve()
    for path in (here, *here.parents):
        if (path / ".mmw" / "target.json").is_file():
            return path
    return worktree_of(start)


def target_config(root: Path, product: str | None = None) -> dict:
    path = root / ".mmw" / "target.json"
    try:
        cfg = read_target_json(root, product=product)
    except TargetJSONError as exc:
        raise SystemExit(str(exc))
    gap = product_gap(cfg, product)
    if gap == "absent":
        raise SystemExit(f"no {path}: the repository has not said how its product is "
                         f"reached. Run `target_config.py --check --repo {root}` "
                         f"(the ui-acceptance skill) and answer what it names")
    if gap == "error":
        raise SystemExit(cfg.error)
    if gap == "not-selected":
        raise SystemExit(f"{path} has no product {product}. "
                         f"Run `target_config.py --check --repo {root}` "
                         f"(the ui-acceptance skill) and answer what it names")
    if gap == "many":
        listed = cfg.root.get("products")
        names = ", ".join(listed) if isinstance(listed, list) else ""
        raise SystemExit(f"{path} names more than one product ({names}); "
                         f"pass --product <name>. "
                         f"Run `target_config.py --check --repo {root}`")
    if gap == "missing":
        raise SystemExit(f"no .mmw/{cfg.name}/target.json. "
                         f"Run `target_config.py --check --repo {root}` "
                         f"(the ui-acceptance skill) and answer what it names")
    if gap == "old-named":
        raise SystemExit(f"{path} is the old layout and has no named product {product}. "
                         f"Run `target_config.py --check --repo {root}`")
    if not cfg.get("discover"):
        raise SystemExit(f"{path} has no `discover` command; run `target_config.py "
                         f"--check --repo {root}` and answer what it names")
    return cfg


def command_env(cwd: Path) -> dict[str, str]:
    """This process's environment plus this run's lease.

    Every command `.mmw/target.json` declares is run through here, so a repository is
    told which run it is in rather than having to work it out — and never has to invent
    an allocation of its own. Inventing one is how a machine ended up with five worktrees
    sharing three fixed ports (2026-09-05): `.mmw/target.json`'s seven questions were all
    in the singular, so nobody was ever asked.

    The variables reach the declared command and stop there. A repository translates
    them at the moment it starts a process, never into the session or the test
    environment: a suite that asserts its product's registered port number is right to,
    and a derived port leaking into it turns a correct suite red.
    """
    env = dict(os.environ)
    env.update(leased_environment(Path(cwd)))
    return env


def run_command(command: str, cwd: Path, env: dict[str, str] | None = None,
                check: bool = True) -> subprocess.CompletedProcess:
    """Run one command a repository declared, and hand back what it printed.

    `env` is the environment to run under; omitted, the leased one for `cwd` is built
    here. `check` decides what a non-zero exit means: raise `SystemExit` wrapping the
    `CompletedProcess` (the default, for a command whose failure stops the run), or
    return it for the caller to read (`stop`, which runs while something has already
    gone wrong). A refusal from the lease is handed back in the same shape as a failed
    command, so one caller reads one thing."""
    argv = shlex.split(command)
    try:
        resolved = command_env(cwd) if env is None else env
    except SystemExit as exc:
        raise SystemExit(subprocess.CompletedProcess(
            args=argv, returncode=2, stdout="", stderr=f"{exc}\n",
        )) from None
    proc = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, env=resolved,
    )
    if check and proc.returncode != 0:
        raise SystemExit(proc)
    return proc


# The note `discover` appends to stderr when its command printed no JSON object;
# `journey.py` reads a stderr made only of these as a silent command.
DISCOVER_NOTES = ("discover printed no JSON object", "discover must print one JSON object")


def discover(cfg: dict, root: Path, env: dict[str, str] | None = None) -> dict:
    """One JSON object of addresses, or SystemExit wrapping that command's CompletedProcess.

    `env` is the caller's environment, so `discover` runs under the same one `start` did;
    omitted, `run_command` builds the leased one."""
    proc = run_command(cfg["discover"], root, env=env)
    out = proc.stdout.strip()
    why = ""
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        why = f"{DISCOVER_NOTES[0]}: {out[:200]!r} ({exc})"
    else:
        if not isinstance(data, dict):
            why = DISCOVER_NOTES[1]
    if why:
        proc.stderr += why + "\n"
        raise SystemExit(proc)
    return data


# ---------------------------------------------------------------- --check

def target_problems(cfg: dict) -> list[tuple[str, str]]:
    """What `.mmw/target.json` still has to answer: `(key, problem)` pairs, in the
    order `FIELDS` lists them. Empty when the file is complete."""
    problems: list[tuple[str, str]] = []
    for f in FIELDS:
        if f.key not in cfg:
            if f.required:
                problems.append((f.key, f"is missing — {f.what} — e.g. {f.example}"))
            continue
        value = cfg[f.key]
        if f.shape in ("command", "directory"):
            if not isinstance(value, str) or not value.strip():
                problems.append((f.key, f"must be a non-empty {f.shape} string — e.g. {f.example}"))
        elif f.key == "leaves_machine":
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                problems.append((f.key, f"must be a list of strings ([] when nothing leaves) "
                                        f"— e.g. {f.example}"))
        elif f.key == "harness_markers":
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                problems.append((f.key, f"must be a list of strings — e.g. {f.example}"))
    return problems


ROOT_KEYS = ("checks", "products", "needs")


def _line(expected: str, actual: str, change: str, evidence: str) -> str:
    """One problem a worker can act on without this session.

    The reader is fixing `.mmw/` after `--check` failed. The line names the check,
    what was expected, what was there, the file to change, and where the evidence is.
    """
    return (f"target_config.py --check: expected {expected}; actual {actual}. "
            f"Change {change}. Evidence {evidence}.")


def layout_problems(root: Path, product: str | None = None) -> list[str]:
    """One line per problem in a new-layout repository. Empty when it is complete."""
    read = read_target_json(root)
    shown = ".mmw/target.json"
    if read is None:
        return [_line(shown, "no file", shown, shown)]
    data = read.root
    problems: list[str] = []
    missing = [key for key in ROOT_KEYS if key not in data]
    extra = sorted(set(data) - set(ROOT_KEYS))
    if missing or extra:
        parts = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if extra:
            parts.append("also " + ", ".join(extra))
        problems.append(_line(
            "root keys checks, products, needs", "; ".join(parts), shown, shown))
    names = data.get("products")
    seen: set[str] = set()
    counted: list[tuple[str, int]] = []
    if not isinstance(names, list):
        problems.append(_line(
            "products to be a list of product names", type(names).__name__, shown, shown))
        names = []
    for name in names:
        if not isinstance(name, str) or PRODUCT_NAME.fullmatch(name) is None:
            label = name if isinstance(name, str) else type(name).__name__
            problems.append(_line(
                "a product name of lowercase letters, digits and hyphens",
                label, shown, shown))
            continue
        if name in seen:
            problems.append(_line(
                f"{name} once in products", f"{name} repeated", shown, shown))
            continue
        seen.add(name)
        file_shown = f".mmw/{name}/target.json"
        one = read_target_json(root, product=name)
        if one is not None and one.error:
            problems.append(_line(
                f"{file_shown} to be one JSON object", one.error, file_shown, file_shown))
            continue
        if one is None or not one.present:
            problems.append(_line(file_shown, "no file", file_shown, file_shown))
            continue
        value = _ports_value(problems, name, one, file_shown)
        if value is not None:
            counted.append((name, value))
    if seen and len(counted) == len(seen):
        total = sum(count for _, count in counted)
        if total > PORT_STRIDE:
            actual = ", ".join(f"{name} {count}" for name, count in counted)
            evidence = ", ".join(f".mmw/{name}/target.json" for name, _ in counted)
            problems.append(_line(
                f"ports to sum to at most {PORT_STRIDE}",
                f"{actual}, sum {total}",
                evidence,
                evidence,
            ))
    _needs_problems(problems, data, seen, shown)
    if product is not None and product not in seen:
        problems.append(_line(
            "the named product to be in products", product, shown, shown))
    return problems


def _ports_value(problems: list[str], name: str, one: dict, file_shown: str) -> int | None:
    """The product's `ports` integer, or None after recording why it is not one.

    A JSON boolean is an int in Python and is not a port count.
    """
    if "ports" not in one:
        problems.append(_line(f"ports on {name}", "no ports", file_shown, file_shown))
        return None
    value = one["ports"]
    if isinstance(value, bool) or not isinstance(value, int):
        problems.append(_line(
            f"ports on {name} to be an integer", json.dumps(value), file_shown, file_shown))
        return None
    return value


def _needs_problems(problems: list[str], data: dict, seen: set[str], shown: str) -> None:
    """Names in `needs` that are not listed products, and one cycle when there is one."""
    if "needs" not in data:
        return
    needs = data["needs"]
    if not isinstance(needs, dict):
        problems.append(_line(
            "needs to be an object of product name to a list of product names",
            type(needs).__name__, shown, shown))
        return
    outside: list[str] = []
    graph: dict[str, list[str]] = {}
    for key, value in needs.items():
        label = key if isinstance(key, str) else type(key).__name__
        if not isinstance(key, str) or key not in seen:
            if label not in outside:
                outside.append(label)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            problems.append(_line(
                f"needs of {label} to be a list of product names",
                json.dumps(value), shown, shown))
            continue
        if isinstance(key, str):
            graph[key] = list(value)
        for item in value:
            if item not in seen and item not in outside:
                outside.append(item)
    for name in outside:
        problems.append(_line("needs to name a product in products", name, shown, shown))
    cycle = _one_cycle(graph)
    if cycle:
        problems.append(_line("needs to have no cycle", ", ".join(cycle), shown, shown))


def _one_cycle(graph: dict[str, list[str]]) -> list[str]:
    """The names in one cycle of `needs`, or an empty list when there is none.

    A `needs` value lists the products that start first, which is the predecessor
    direction `graphlib` walks. The raised list repeats its first name at the end.
    """
    try:
        graphlib.TopologicalSorter(graph).prepare()
    except graphlib.CycleError as exc:
        cycle = list(exc.args[1])
        if len(cycle) > 1 and cycle[0] == cycle[-1]:
            cycle.pop()
        return cycle
    return []


def _report_product_layout(root: Path, product: str | None, validate: bool) -> int:
    path = root / ".mmw" / "target.json"
    problems = layout_problems(root, product)
    if validate:
        if problems:
            more = f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""
            print(f"{path}: {problems[0]}{more}")
            return 1
        print(f"{path}: complete")
        return 0
    print(f"{path}: read")
    for line in problems:
        print(line)
    if problems:
        print(f"{len(problems)} to answer; run this again when the file is filled")
        return 1
    print("complete: the oracles can drive this repository")
    return 0


def target_main(argv: list[str]) -> int:
    """`target_config.py …`: the setup-time bar for one repository.

    `--check` prints every field of `.mmw/target.json` as `ok` or `missing`, so a
    person filling the file reads one screen and nothing else; exit 0 complete, 1
    something missing, 2 the repository cannot be read. `--validate` prints the first
    problem only. Keys outside `FIELDS` are stale and reported without changing exit.
    """
    import argparse
    parser = argparse.ArgumentParser(prog="target_config.py")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="print every field, ok or missing")
    mode.add_argument("--validate", action="store_true", help="print the first problem only")
    parser.add_argument("--repo", type=Path, default=None,
                        help="the repository (default: the one the working directory is in)")
    parser.add_argument("--product", default=None,
                        help="which product, when the repository has several")
    args = parser.parse_args(argv)
    repo = (args.repo or repo_root()).resolve()
    if not repo.is_dir():
        print(f"no such directory: {repo}", file=sys.stderr)
        return 2
    path = repo / ".mmw" / "target.json"
    try:
        read = read_target_json(repo)
    except TargetJSONError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if read is not None and product_layout(read.root):
        return _report_product_layout(repo, args.product, args.validate)
    cfg = read or {}
    problems = target_problems(cfg)
    old_name = None
    if args.product is not None and read is not None and not product_layout(read.root):
        old_name = _line(
            "no product name, because this file is the old layout",
            args.product,
            ".mmw/target.json",
            ".mmw/target.json",
        )
    if args.validate:
        shown = []
        if problems:
            key, why = problems[0]
            shown.append(f"{key} {why}")
        if old_name:
            shown.append(old_name)
        if shown:
            extra = len(problems) + (1 if old_name else 0) - 1
            more = f" (+{extra} more)" if extra else ""
            print(f"{path}: {shown[0]}{more}")
            return 1
        print(f"{path}: complete")
        return 0
    print("  discover prints:")
    for key, what in DISCOVER_PRINTS:
        print(f"    {key} — {what}")
    print(f"{path}: {'not there yet' if not path.exists() else 'read'}")
    named = {key for key, _ in problems}
    for f in FIELDS:
        if f.key in named:
            why = next(w for k, w in problems if k == f.key)
            if why.startswith("is missing"):
                print(f"  missing  {f.key} ({f.shape}) — {f.what} — e.g. {f.example}")
            else:
                print(f"  wrong    {f.key} ({f.shape}) {why}")
        elif f.key in cfg:
            print(f"  ok       {f.key}")
        else:
            print(f"  absent   {f.key} ({f.shape}, optional) — {f.what}")
    field_keys = {f.key for f in FIELDS}
    for key in sorted(set(cfg) - field_keys):
        print(f"  stale  {key} — no MMW script reads it; delete it")
    print("rules:")
    print("  automation uses placeholder keys, vendor stubs, and local accounts")
    print("  leaves_machine actions record under MMW_AUTOMATION=1")
    if old_name:
        print(old_name)
    if problems or old_name:
        print(f"{len(problems) + (1 if old_name else 0)} to answer; "
              "run this again when the file is filled")
        return 1
    print("complete: the oracles can drive this repository")
    return 0


if __name__ == "__main__":
    sys.exit(target_main(sys.argv[1:]))
