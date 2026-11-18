#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def target_paths(args: list[str]) -> list[str]:
    if args:
        return args
    out = subprocess.check_output(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "mmwstack",
            "scripts",
        ],
        text=True,
    )
    return list(dict.fromkeys(path for path in out.split("\0") if path))


def check_file(rel: str) -> str | None:
    path = ROOT / rel
    if not path.is_file():
        return None
    data = path.read_bytes()
    head = data[:64]
    if rel.endswith(".py") or head.startswith((b"#!/usr/bin/env python3", b"#!/usr/bin/python3")):
        try:
            compile(data, rel, "exec")
        except (SyntaxError, ValueError) as err:
            return f"{rel}: {err}"
    elif rel.endswith(".sh") or head.startswith(b"#!/usr/bin/env bash"):
        result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            return result.stderr.strip() or f"{rel}: bash -n exited {result.returncode}"
    elif head.startswith((b"#!/bin/sh", b"#!/usr/bin/env sh")):
        result = subprocess.run(["sh", "-n", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            return result.stderr.strip() or f"{rel}: sh -n exited {result.returncode}"
    elif rel.endswith((".mjs", ".js", ".cjs")) or head.startswith(b"#!/usr/bin/env node"):
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            return result.stderr.strip() or f"{rel}: node --check exited {result.returncode}"
    return None


def main(argv: list[str]) -> int:
    paths = target_paths(argv)
    errors = [err for rel in paths if (err := check_file(rel))]
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print(f"PASS syntax ({len(paths)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
