#!/usr/bin/env python3
"""Read and check a repository's `.mmw/target.json`.

Which keys a repository answers is declared here, once, on `FIELDS`, and printed by

    target_config.py --check [--repo <dir>] [--kind <kind> | --contract <yaml>]

which names every field still missing, with one sentence and one example each, and
exits 0 once the file is complete. `discover` prints an origin-class address plus
`instance`. `--validate` prints the first problem only; `--kinds` lists the product
kinds a contract may name. `journey.py` runs every command `.mmw/target.json` declares
through `run_command`, and imports `discover`.
"""

from __future__ import annotations

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

from lease import leased_environment, worktree_of  # noqa: E402


def load_yaml(path: Path) -> dict:
    """`pyyaml` when the interpreter has it (the scripts declare it); else through `uv`,
    which every criterion of this pipeline already relies on."""
    try:
        import yaml
    except ImportError:
        out = subprocess.run(
            ["uv", "run", "--with", "pyyaml", "python", "-c",
             "import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], "
             "encoding='utf-8')) or {}))", str(path)],
            capture_output=True, text=True)
        if out.returncode != 0:
            raise SystemExit(f"cannot read {path}: pyyaml is not importable and uv failed: "
                             f"{out.stderr.strip()}")
        return json.loads(out.stdout)
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

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
# `verify-ticket.py --closeout`, not by this file, and is listed so the file has one
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
          '"uv run python scripts/testing/target.py start"'),
    Field("stop", "command",
          "ends what start started and nothing else, and exits 0 with nothing of its own "
          "to end; the only way a run may end a process",
          '"uv run python scripts/testing/target.py stop"'),
    Field("discover", "command",
          "prints one JSON object of origin-class addresses plus `instance`, a readable "
          "name for this run",
          '"uv run python scripts/testing/target.py discover"'),
    Field("stories", "command",
          "brings up the story page service and prints its `origin`",
          '"uv run python scripts/testing/target.py stories"'),
    Field("journeys", "directory",
          "the directory of journey scripts; default .mmw/journeys",
          '".mmw/journeys"',
          required=False),
    Field("leaves_machine", "list of strings",
          "each thing this product does in a run that reaches past this machine, naming "
          "the file that records it under MMW_AUTOMATION=1; [] when nothing leaves",
          '["tools/opened.py — system browser; under MMW_AUTOMATION=1 the URL is written '
          'to $MMW_DATA_DIR/opened-urls"]'),
    Field("instance", "object {max, why}",
          "only when the product cannot move its ports (ports in a container file, a "
          "callback at a fixed port): how many runs one machine holds and what stops a "
          "second; absent means the product is isolable and the machine's own limit applies",
          '{"max": 1, "why": "the callback URL is registered at port 8000"}',
          required=False),
    Field("checks", "list",
          "the repository's own checks, run by `verify-ticket.py --closeout` before an "
          "ALL MET ticket closes; the verify-ticket skill's references/closeout.md says the "
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


def target_config(root: Path) -> dict:
    path = root / ".mmw" / "target.json"
    if not path.exists():
        raise SystemExit(f"no {path}: the repository has not said how its product is "
                         f"reached. Run `target_config.py --check --repo {root}` "
                         f"(the ui-acceptance skill) and answer what it names")
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"{path} cannot be read as JSON: {exc}")
    if not isinstance(cfg, dict):
        raise SystemExit(f"{path} must hold one JSON object")
    if not cfg.get("discover"):
        raise SystemExit(f"{path} has no `discover` command; run `target_config.py "
                         f"--check --repo {root}` and answer what it names")
    return cfg


def command_env(cwd: Path) -> dict[str, str]:
    """This process's environment plus this run's lease.

    Every command `.mmw/target.json` declares is run through here, so a repository is
    told which run it is in rather than having to work it out — and never has to invent
    an allocation of its own. Inventing one is how a machine ended up with five worktrees
    sharing three fixed ports (2026-09-05): the contract's seven questions were all in
    the singular, so nobody was ever asked.

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
        why = f"discover printed no JSON object: {out[:200]!r} ({exc})"
    else:
        if not isinstance(data, dict):
            why = "discover must print one JSON object"
    if why:
        proc.stderr += why + "\n"
        raise SystemExit(proc)
    return data


# ---------------------------------------------------------------- product kinds
# Named in the contract as `target.kind`. Fields of `.mmw/target.json` are the
# same for every kind; journeys connect with Playwright themselves.
KINDS = ("electron", "web-spa", "web-server-rendered", "chrome-extension")

# ---------------------------------------------------------------- --check

def contract_kind(repo: Path, contract: Path | None) -> str:
    """The `target.kind` of the repository's screen contract: the one given, else the
    single `docs/specs/*/screen-contract.yaml` under the repository."""
    if contract is None:
        found = sorted((repo / "docs" / "specs").glob("*/screen-contract.yaml"))
        if len(found) != 1:
            raise SystemExit(f"{len(found)} screen contracts under {repo / 'docs' / 'specs'}; "
                             f"name one with --contract or the kind with --kind")
        contract = found[0]
    return str((load_yaml(contract).get("target") or {}).get("kind") or "")


def target_problems(kind: str, cfg: dict) -> list[tuple[str, str]]:
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
        elif f.key == "instance":
            ok = (isinstance(value, dict) and isinstance(value.get("max"), int)
                  and value["max"] > 0 and isinstance(value.get("why"), str))
            if not ok:
                problems.append((f.key, f"must be {{\"max\": <n>, \"why\": \"<text>\"}} "
                                        f"— e.g. {f.example}"))
    if kind and kind not in KINDS:
        problems.insert(0, ("target.kind", f"{kind!r} is not one of {list(KINDS)}"))
    return problems


def target_main(argv: list[str]) -> int:
    """`target_config.py …`: the setup-time bar for one repository.

    `--check` prints every field of `.mmw/target.json` as `ok` or `missing`, so a
    person filling the file reads one screen and nothing else; exit 0 complete, 1
    something missing, 2 the repository or the contract cannot be read.
    `--validate` prints the first problem only. `--kinds` prints the product kinds.
    """
    import argparse
    parser = argparse.ArgumentParser(prog="target_config.py")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="print every field, ok or missing")
    mode.add_argument("--validate", action="store_true", help="print the first problem only")
    mode.add_argument("--kinds", action="store_true", help="list the product kinds a contract may name")
    parser.add_argument("--repo", type=Path, default=None,
                        help="the repository (default: the one the working directory is in)")
    parser.add_argument("--kind", default=None, help="the product kind, instead of reading the contract")
    parser.add_argument("--contract", type=Path, default=None,
                        help="the screen contract to read the kind from")
    args = parser.parse_args(argv)
    if args.kinds:
        for kind in KINDS:
            print(kind)
        return 0
    repo = (args.repo or repo_root()).resolve()
    if not repo.is_dir():
        print(f"no such directory: {repo}", file=sys.stderr)
        return 2
    try:
        kind = args.kind or contract_kind(repo, args.contract)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2
    path = repo / ".mmw" / "target.json"
    cfg: dict = {}
    if path.exists():
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"{path} cannot be read as JSON: {exc}", file=sys.stderr)
            return 2
        if not isinstance(cfg, dict):
            print(f"{path} must hold one JSON object", file=sys.stderr)
            return 2
    problems = target_problems(kind, cfg)
    if args.validate:
        if problems:
            key, why = problems[0]
            print(f"{path}: {key} {why}" + (f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""))
            return 1
        print(f"{path}: complete for target.kind {kind}")
        return 0
    print(f"target.kind: {kind or '(none)'}")
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
    if kind and kind not in KINDS:
        print(f"  target.kind {kind!r} is not one of {list(KINDS)}")
    print("rules:")
    print("  automation uses placeholder keys, vendor stubs, and local accounts")
    print("  start refuses a Gateway address that points elsewhere")
    print("  leaves_machine actions record under MMW_AUTOMATION=1")
    if problems:
        print(f"{len(problems)} to answer; run this again when the file is filled")
        return 1
    print("complete: the judges can drive this repository")
    return 0


if __name__ == "__main__":
    sys.exit(target_main(sys.argv[1:]))
