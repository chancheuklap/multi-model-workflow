#!/usr/bin/env python3
"""Run a product's boundary test twice: as written, then with interaction skipped.

    boundary-check.py --run "<command>" [--run …]

For each command: first pass as-is must exit 0; second pass with `MMW_NEGATIVE=1`
must exit non-zero. Every command meeting both prints `BOUNDARY OK <n>/<n>`
(exit 0). A first pass that is red prints `MISS <command> — <last 20 lines>`
(exit 1). A second pass that is still green prints
`GREEN WITHOUT INTERACTION <command>` (exit 1). A command that does not exist
is exit 2.

Both passes share this process's cwd and environment; the second pass adds
`MMW_NEGATIVE=1` and nothing else. The product-side convention, the criterion
shape, and how to read the three lines are the reference beside this script,
`references/boundary-check.md`.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from refusal import REPORT_BLOCKED, refusal  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="boundary-check.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", required=True, action="append", metavar="COMMAND",
                   help="a product test command; may be repeated")
    return p


def tail(text: str, n: int = 20) -> str:
    lines = (text or "").splitlines()
    if not lines:
        return "(no output)"
    return "\n".join(lines[-n:])


def missing(command: str) -> int:
    print(refusal(
        f"`{command}` was not found.",
        "A command that does not exist cannot be judged.",
        REPORT_BLOCKED,
    ), file=sys.stderr)
    return 2


def run_once(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def check_one(command: str) -> int:
    try:
        argv = shlex.split(command)
    except ValueError:
        return missing(command)
    if not argv:
        return missing(command)
    env = os.environ.copy()
    try:
        first = run_once(argv, env)
    except FileNotFoundError:
        return missing(command)
    if first.returncode != 0:
        print(f"MISS {command} — {tail(first.stdout)}")
        return 1
    negative = dict(env)
    negative["MMW_NEGATIVE"] = "1"
    try:
        second = run_once(argv, negative)
    except FileNotFoundError:
        return missing(command)
    if second.returncode == 0:
        print(f"GREEN WITHOUT INTERACTION {command}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    n = len(args.run)
    for command in args.run:
        code = check_one(command)
        if code != 0:
            return code
    print(f"BOUNDARY OK {n}/{n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
