#!/usr/bin/env python3
"""This repository's Nowledge Mem Space, the one its night's workers and reviewers write to.

    python3 space.py <owner/name>          create it, or repair its shape, then read it back
    python3 space.py --check <owner/name>  read only

The Space's id is `<owner>__<name>`, lowercased; its name is `<owner/name>`; it retrieves in
shared mode with `mmw-toolbox` and nothing else, so what one repository's runs learn reaches
another only through the toolbox. Only this script creates or repairs it, when the
`setup-mmw` skill sets the repository up; `dispatch.sh` runs `--check` before a night opens
and before a session starts, and refuses when it fails.

Exit 0 when the Space is there in exactly that shape. Exit 1 with one line on stderr,
starting `repository Memory unavailable:`, saying why it is not: no `nmem`, a failed or
unreadable answer, and under `--check` a Space that is absent or has another shape.
"""
import json
import shutil
import subprocess
import sys

SHARED = ["mmw-toolbox"]


def ident_of(slug: str) -> str:
    return "__".join(part.lower() for part in slug.split("/", 1))


def call(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["nmem", "--json", *args], text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def detail(proc: subprocess.CompletedProcess) -> str:
    return (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip().replace("\n", "; ")


def parse(proc: subprocess.CompletedProcess) -> dict | None:
    try:
        value = json.loads(proc.stdout)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def exact(value: dict | None, slug: str) -> bool:
    return (isinstance(value, dict) and value.get("id") == ident_of(slug)
            and value.get("name") == slug
            and value.get("defaultRetrievalMode") == "shared"
            and value.get("sharedSpaceIds") == SHARED)


def unavailable(why: str) -> int:
    sys.stderr.write(f"repository Memory unavailable: {why}\n")
    return 1


def main(argv: list[str]) -> int:
    check = argv[:1] == ["--check"]
    args = argv[1:] if check else argv
    if len(args) != 1:
        sys.stderr.write("usage: space.py [--check] <owner/name>\n")
        return 2
    slug = args[0]
    parts = slug.split("/", 1)
    if len(parts) != 2 or not all(parts):
        return unavailable(f"{slug!r} is not owner/name")
    ident = ident_of(slug)
    if shutil.which("nmem") is None:
        return unavailable("this machine has no nmem")

    shown = call(["spaces", "show", ident])
    if shown.returncode:
        missing = "404" in (shown.stderr or "") and "Unknown space:" in (shown.stderr or "")
        if not missing:
            return unavailable(f"nmem spaces show {ident} failed ({detail(shown)})")
        if check:
            return unavailable(f"this repository has no Space {ident}; the setup-mmw skill creates it")
        changed = call(["spaces", "create", slug, "--id", ident,
                        "--retrieval-mode", "shared", "--share-with", *SHARED])
        action = "create"
    else:
        value = parse(shown)
        if value is None:
            return unavailable(f"nmem spaces show {ident} did not return a JSON object ({detail(shown)})")
        if exact(value, slug):
            return 0
        if check:
            return unavailable(f"Space {ident} is not named {slug} and shared with mmw-toolbox alone; "
                               "the setup-mmw skill repairs it")
        changed = call(["spaces", "update", ident, "--name", slug, "--retrieval-mode", "shared",
                        "--clear-shared", "--share-with", *SHARED])
        action = "update"

    verified = call(["spaces", "show", ident]) if changed.returncode == 0 else changed
    if changed.returncode or verified.returncode or not exact(parse(verified), slug):
        why = (detail(changed) if changed.returncode
               else detail(verified) if verified.returncode
               else "the stored JSON has the wrong shape")
        return unavailable(f"nmem spaces {action} {ident} failed ({why})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
