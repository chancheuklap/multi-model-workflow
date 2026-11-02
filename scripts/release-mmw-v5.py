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
import zipfile


ROOT = Path(__file__).resolve().parent.parent
MANIFESTS = ("mmw-v5/plugin.json", "mmw-v5/.cursor-plugin/plugin.json")
PACKAGE_PATHS = (
    "plugin.json", "README.md", ".agents/plugins/marketplace.json",
    ".cursor-plugin/plugin.json", "skills", "tools", "board",
)
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
    if any(row.get("name") != "mmw-v5" or row.get("version") != version for row in rows):
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
    return f"{old} -> {new}; run local checks and commit both manifests with the release on dev"


def package(output: Path, edition: str = "local") -> str:
    _, version = manifests(committed=True)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if edition == "local":
        run("git", "archive", "--format=zip", "--prefix=mmw-v5/", f"--output={output}",
            "HEAD:mmw-v5", *PACKAGE_PATHS)
    else:
        entries = run("git", "ls-tree", "-r", "-z", "HEAD").stdout.split("\0")
        files = {}
        for entry in filter(None, entries):
            metadata, source = entry.split("\t", 1)
            mode, kind, blob = metadata.split()
            if kind != "blob":
                continue
            target = None
            if source.startswith("mmw-v5/skills/") and not source.startswith("mmw-v5/skills/dispatch/"):
                target = source.removeprefix("mmw-v5/")
            elif source.startswith("mmw-v5/board/page/"):
                target = source.removeprefix("mmw-v5/")
                if target.endswith("/board-logic.mjs"):
                    target = "board/page/board-layout.mjs"
                elif target.endswith("/detail.mjs"):
                    target = "board/page/detail-layout.mjs"
                elif target.endswith("/settings.mjs"):
                    continue
                elif target.endswith("/topbar.mjs"):
                    target = "board/page/topbar-layout.mjs"
                elif target.endswith("/styles/settings.css"):
                    target = "board/page/styles/settings-layout.css"
            elif source in ("mmw-v5/board/gates.py", "mmw-v5/tools/verify-ticket/scripts/labels.py", "mmw-v5/plugin.json"):
                target = source.removeprefix("mmw-v5/")
            elif source.startswith("mmw-v5-cloud/"):
                relative = source.removeprefix("mmw-v5-cloud/")
                if relative.startswith(("skills/", "tools/", "board/")) or relative in ("models.json", "README.md"):
                    target = relative
            if target:
                files[target] = (source, mode, blob)
        if "skills/dispatch/SKILL.md" not in files or "models.json" not in files:
            raise ValueError("commit the cloud edition before packaging it")
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for target, (source, mode, blob) in sorted(files.items()):
                info = zipfile.ZipInfo(".agents/" + target)
                info.create_system = 3
                info.external_attr = int(mode, 8) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                content = subprocess.run(["git", "cat-file", "blob", blob], cwd=ROOT, capture_output=True, check=True).stdout
                archive.writestr(info, content)
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
        archive = Path(directory) / f"mmw-v5-{version}.zip"
        package(archive)
        archives = [str(archive)]
        if run("git", "cat-file", "-e", "HEAD:mmw-v5-cloud/skills/dispatch/SKILL.md", check=False).returncode == 0:
            cloud_archive = Path(directory) / f"mmw-v5-cloud-{version}.zip"
            package(cloud_archive, "cloud")
            archives.append(str(cloud_archive))
        if existing.returncode == 0:
            run("gh", "release", "upload", tag, *archives, "--repo", repo, "--clobber")
        else:
            args = ["gh", "release", "create", tag, *archives, "--repo", repo,
                    "--target", commit, "--title", f"MMW v5 {version}",
                    "--notes", f"MMW v5 plugin at commit {commit}.\n\nInstall from this repository's main-branch plugin marketplace. The local ZIP contains the complete plugin; the cloud ZIP contains the self-contained project .agents runtime when present."]
            if "-" in version:
                args.append("--prerelease")
            run(*args)
    return run("gh", "release", "view", tag, "--repo", repo, "--json", "url", "--jq", ".url").stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("bump", help="increment dev's prerelease counter, or patch for a stable version")
    pack = commands.add_parser("package", help="archive only the committed plugin; never install it")
    pack.add_argument("--output", type=Path, required=True)
    pack.add_argument("--edition", choices=("local", "cloud"), default="local")
    commands.add_parser("publish", help="publish the existing committed version from the main-push workflow")
    args = parser.parse_args()
    try:
        if args.command == "bump":
            print(bump())
        elif args.command == "package":
            print(json.dumps({"version": package(args.output, args.edition), "edition": args.edition, "archive": str(args.output.resolve())}))
        else:
            print(publish())
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        parser.exit(2, f"release-mmw-v5: {error}\n")


if __name__ == "__main__":
    main()
