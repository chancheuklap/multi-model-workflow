#!/usr/bin/env python3
"""Run a product's boundary test twice: as written, then with interaction skipped.

    boundary-check.py --run "<command>" [--run …]

For each command: first pass as-is must exit 0; second pass with `MMW_NEGATIVE=1`
must exit non-zero. Every command meeting both prints `BOUNDARY OK <n>/<n>`
(exit 0). A first pass that is red prints `MISS <command> — <last 20 lines>`
(exit 1). A second pass that is still green prints
`GREEN WITHOUT INTERACTION <command>` (exit 1). A command that cannot be
started is exit 2.

`--run` takes one command, not a shell line. Both passes share this process's
cwd and environment; the second pass adds `MMW_NEGATIVE=1` and nothing else.
The product-side convention, the criterion shape, and how to read the three
lines are the reference beside this script, `references/boundary-check.md`.
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
from lease import judge_run  # noqa: E402

SHELL_TOKENS = frozenset({"&&", "||", ";", "|"})
TAIL_LINES = 20


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="boundary-check.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run", required=True, action="append", metavar="COMMAND",
                   help="a product test command; may be repeated")
    return p


def tail(text: str) -> str:
    lines = (text or "").splitlines()
    if not lines:
        return "(no output)"
    return "\n".join(lines[-TAIL_LINES:])


def refuse(what: str, why: str, next_step: str = REPORT_BLOCKED) -> int:
    print(refusal(what, why, next_step), file=sys.stderr)
    return 2


def argv_of(command: str) -> list[str] | int:
    try:
        argv = shlex.split(command)
    except ValueError:
        return refuse(
            f"The quotes in `{command}` do not close.",
            "A command that cannot be parsed cannot be judged.",
            "Close the quotes in `--run`.",
        )
    if not argv:
        return refuse(
            "The `--run` value is empty.",
            "An empty command cannot be judged.",
            "Pass a command to `--run`.",
        )
    for token in argv:
        if token in SHELL_TOKENS:
            return refuse(
                f"`--run` contained `{token}`.",
                "The flag takes one command, not a shell line.",
                "Write the product's test as a single executable invocation.",
            )
    return argv


def run_once(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def check_one(command: str) -> int:
    parsed = argv_of(command)
    if isinstance(parsed, int):
        return parsed
    argv = parsed
    env = os.environ.copy()
    try:
        first = run_once(argv, env)
    except FileNotFoundError:
        return refuse(
            f"`{command}` was not found.",
            "A command that does not exist cannot be judged.",
        )
    except OSError as exc:
        name = exc.filename or argv[0]
        detail = exc.strerror or type(exc).__name__
        return refuse(
            f"`{command}` could not be executed: {detail}: {name}.",
            "A command that cannot be started cannot be judged.",
        )
    if first.returncode != 0:
        print(f"MISS {command} — {tail(first.stdout)}")
        print("Fix the product's test; the negative control was not reached.")
        return 1
    negative = dict(env)
    negative["MMW_NEGATIVE"] = "1"
    second = run_once(argv, negative)
    if second.returncode == 0:
        print(
            f"GREEN WITHOUT INTERACTION {command} — "
            "the second pass with MMW_NEGATIVE=1 also exited 0, so the "
            "assertion does not depend on the interaction. Make the "
            "assertion fail when the interaction helper does nothing."
        )
        return 1
    return 0


def _main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    n = len(args.run)
    for command in args.run:
        code = check_one(command)
        if code != 0:
            return code
    print(f"BOUNDARY OK {n}/{n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    with judge_run(Path.cwd(), stop=True):
        return _main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
