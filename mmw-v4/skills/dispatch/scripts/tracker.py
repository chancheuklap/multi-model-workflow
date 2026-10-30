#!/usr/bin/env python3
"""Resolve the consuming repository from origin, independently of gh's default."""

import functools
import os
import re
import subprocess
import sys


class RepositoryError(ValueError):
    pass


@functools.lru_cache(maxsize=16)
def _repository(remote: str) -> str:
    proc = subprocess.run(
        ["gh", "repo", "view", remote, "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        capture_output=True, text=True,
        env={k: v for k, v in os.environ.items()
             if k not in ("GH_REPO", "CLICOLOR", "CLICOLOR_FORCE")}, timeout=120)
    slug = proc.stdout.strip()
    if proc.returncode or not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+", slug):
        raise RepositoryError("gh cannot resolve origin to owner/repo; check origin and GitHub access")
    return slug


def repository(cwd=None) -> str:
    try:
        proc = subprocess.run(["git", "remote", "get-url", "origin"], cwd=cwd,
                              capture_output=True, text=True, timeout=30)
        if proc.returncode or not proc.stdout.strip():
            raise RepositoryError("cannot read origin; set this checkout's origin to its GitHub repository")
        return _repository(proc.stdout.strip())
    except (OSError, subprocess.SubprocessError) as exc:
        raise RepositoryError(f"cannot resolve the repository behind origin: {exc}") from None


def environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("CLICOLOR", "CLICOLOR_FORCE")}
    env["GH_REPO"] = repository()
    return env


if __name__ == "__main__":
    try:
        print(repository())
    except RepositoryError as exc:
        print(f"tracker: {exc}", file=sys.stderr)
        sys.exit(2)
