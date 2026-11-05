#!/usr/bin/env python3
"""Prepare a version on dev; package committed files; publish only on a main push.

Python standard library, Git and (for publish only) gh. No tests or source writes
run during publication. Plugin installation remains the host's responsibility.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ("mmw-v5-cloud/plugin.json", "mmw-v5-cloud/.cursor-plugin/plugin.json")
PACKAGE_PATHS = ("plugin.json", ".cursor-plugin/plugin.json", "models.json", "skills", "tools", "board")
VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*))?")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"{args[0]} exited {result.returncode}")
    return result


def manifests(committed: bool = False) -> tuple[list[dict], str]:
    rows = [json.loads(run("git", "show", f"HEAD:{path}").stdout if committed
                       else (ROOT / path).read_text(encoding="utf-8")) for path in MANIFESTS]
    version = rows[0]["version"]
    match = VERSION.fullmatch(version) if isinstance(version, str) else None
    if not match or any(part.isdigit() and len(part) > 1 and part.startswith("0")
                        for part in (match[4] or "").split(".")):
        raise ValueError(f"invalid plugin version: {version}")
    if any(row.get("name") != "mmw-v5-cloud" or row.get("version") != version for row in rows):
        raise ValueError("portable and Cursor plugin manifests must have the same name and version")
    return rows, version


def bump() -> str:
    if run("git", "branch", "--show-current").stdout.strip() != "dev":
        raise ValueError("prepare the release version on dev, not on main or a feature branch")
    rows, old = manifests()
    match = VERSION.fullmatch(old)
    if match[4]:
        parts = match[4].split(".")
        if parts[-1].isdigit():
            parts[-1] = str(int(parts[-1]) + 1)
        else:
            parts.append("1")
        new = f"{match[1]}.{match[2]}.{match[3]}-" + ".".join(parts)
    else:
        new = f"{match[1]}.{match[2]}.{int(match[3]) + 1}"
    for path, row in zip(MANIFESTS, rows):
        row["version"] = new
        (ROOT / path).write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f"{old} -> {new}; run local checks and commit the edition manifests with the release on dev"


def package(output: Path) -> str:
    _, version = manifests(committed=True)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    run("git", "archive", "--format=zip", "--prefix=mmw-v5-cloud/", f"--output={output}",
        "HEAD:mmw-v5-cloud", *PACKAGE_PATHS)
    return version


def publish() -> str:
    if (os.environ.get("GITHUB_EVENT_NAME"), os.environ.get("GITHUB_REF")) != ("push", "refs/heads/main"):
        raise ValueError("publication runs only for a push to main")
    repo = os.environ["GITHUB_REPOSITORY"]
    commit = run("git", "rev-parse", "HEAD").stdout.strip()
    if commit != os.environ.get("GITHUB_SHA"):
        raise ValueError("checkout HEAD does not match the main push being published")
    _, version = manifests(committed=True)
    tag = f"v{version}"
    refs = run("git", "ls-remote", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}").stdout.splitlines()
    targets = dict(line.split()[::-1] for line in refs)
    tagged = targets.get(f"refs/tags/{tag}^{{}}", targets.get(f"refs/tags/{tag}"))
    if tagged and tagged != commit:
        raise ValueError(f"{tag} already belongs to another commit; prepare a new version on dev")
    existing = run("gh", "release", "view", tag, "--repo", repo, "--json", "url", check=False)
    if existing.returncode and not any(text in existing.stderr.lower() for text in ("release not found", "http 404")):
        raise RuntimeError(existing.stderr.strip() or "could not read release state")
    with tempfile.TemporaryDirectory(prefix="mmw-v5-release-") as directory:
        archive = Path(directory) / "mmw-v5-cloud.zip"
        package(archive)
        if existing.returncode == 0:
            run("gh", "release", "upload", tag, str(archive), "--repo", repo, "--clobber")
        else:
            args = ["gh", "release", "create", tag, str(archive), "--repo", repo,
                    "--target", commit, "--title", f"MMW v5 {version}",
                    "--notes", f"MMW v5 cloud edition at commit {commit}.\n\nInstallation and cloud environment setup: https://github.com/{repo}#codex\nInstall the native mmw-v5-cloud plugin from the MMW marketplace in Codex or Cursor. Skills, tools and board ship together; user models stay outside the plugin."]
            if "-" in version:
                args.append("--prerelease")
            run(*args)
    return run("gh", "release", "view", tag, "--repo", repo, "--json", "url", "--jq", ".url").stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("bump", help="increment dev's prerelease counter, or patch for a stable version")
    pack = commands.add_parser("package", help="archive the committed cloud edition; never install it")
    pack.add_argument("--output", type=Path, required=True)
    commands.add_parser("publish", help="publish the existing committed version from the main-push workflow")
    args = parser.parse_args()
    try:
        if args.command == "bump":
            print(bump())
        elif args.command == "package":
            print(json.dumps({"version": package(args.output), "archive": str(args.output.resolve())}))
        else:
            print(publish())
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        parser.exit(2, f"release-mmw-v5: {error}\n")


if __name__ == "__main__":
    main()
