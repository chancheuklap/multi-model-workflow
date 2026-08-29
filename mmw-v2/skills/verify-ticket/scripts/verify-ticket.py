#!/usr/bin/env python3
"""Run a ticket's acceptance criteria and post the result back to the ticket.

The ticket is the only state. Every run reads the `## Acceptance criteria` and
`## Owns` sections fresh from the issue, writes them to a throwaway ledger, hands
that ledger to unlazy's `gate-check.mjs`, and posts the updated ledger back as one
comment. Nothing is cached and no file is left behind.

    verify-ticket.py <n>              run the unmet criteria, comment `self-run`
    verify-ticket.py <n> --reverify   re-run every criterion, comment `reverify`
    verify-ticket.py <n> --lint       audit how the criteria are written; print only

Exit code follows gate-check: 0 all met, 1 unmet or abandoned, 2 usage or
infrastructure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE_CHECK = HERE / "gate-check" / "gate-check.mjs"
GATE_LINT = HERE / "gate-check" / "gate-lint.mjs"
APPROVAL_DIR = Path.home() / ".mmw" / "verify-ticket-approvals"
LEDGER_NAME = "AC.md"
SUMMARY_RE = re.compile(r"^(ALL MET|UNMET:|HANDOFF REQUIRED:)")
GATE_LINE_RE = re.compile(r"^- \[( |x|X)\] ([A-Za-z0-9][A-Za-z0-9._-]*):")
TTL_MS = "86400000"


# ----------------------------------------------------------------- ticket text

def fetch_body(number: int) -> str:
    """The issue body, straight from the tracker. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "body", "-q", ".body"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def fetch_comments(number: int) -> list[str]:
    """Every comment body on the ticket, oldest first. Patched out in tests."""
    out = subprocess.run(
        ["gh", "issue", "view", str(number), "--json", "comments"],
        capture_output=True, text=True, check=True,
    )
    return [c.get("body", "") for c in json.loads(out.stdout).get("comments", [])]


def post_comment(number: int, body: str) -> None:
    """One comment per run. Patched out in tests."""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
        path = fh.name
    try:
        subprocess.run(["gh", "issue", "comment", str(number), "--body-file", path], check=True)
    finally:
        os.unlink(path)


def section(body: str, heading: str) -> list[str]:
    """The lines under `## <heading>`, up to the next `## ` heading."""
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def owns_globs(body: str) -> list[str]:
    """The paths this ticket is allowed to write, from `## Owns`. `(new)` is a note."""
    globs = []
    for line in section(body, "Owns"):
        m = re.match(r"^\s*-\s+(\S+)", line)
        if not m:
            continue
        value = m.group(1)
        if value.lower().startswith("none"):
            continue
        globs.append(value)
    return globs


# ------------------------------------------------------------------------ git

def git(*args: str, cwd: Path | None = None) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_root() -> Path:
    top = git("rev-parse", "--show-toplevel")
    return Path(top) if top else Path.cwd()


def outside_owns(globs: list[str], root: Path) -> list[str]:
    """Files changed since the branch left main that no `## Owns` glob covers."""
    base = git("merge-base", "main", "HEAD", cwd=root)
    if not base:
        return []
    args = ["diff", "--name-only", f"{base}..HEAD", "--", "."]
    args += [f":(glob,exclude){g}" for g in globs]
    out = git(*args, cwd=root)
    return [line for line in out.splitlines() if line.strip()]


# ------------------------------------------------------------------- ledger

def ledger_from_comment(comment: str) -> list[str]:
    """The ledger a previous run posted: from its first gate line to `Outside Owns:`."""
    lines = comment.splitlines()
    start = next((i for i, l in enumerate(lines) if GATE_LINE_RE.match(l)), None)
    if start is None:
        return []
    end = next((i for i, l in enumerate(lines[start:], start)
                if l.startswith("Outside Owns:")), len(lines))
    out = lines[start:end]
    while out and not out[-1].strip():
        out.pop()
    return out


def previous_ledger(number: int) -> list[str]:
    """The ledger from the newest `self-run` / `reverify` comment, if there is one.

    A re-verification re-runs what the last run ticked, and the ticket body is never
    edited, so the previous run's comment is where that state lives.
    """
    for comment in reversed(fetch_comments(number)):
        first = comment.strip().splitlines()[0].strip() if comment.strip() else ""
        if first in ("self-run", "reverify"):
            ledger = ledger_from_comment(comment)
            if ledger:
                return ledger
    return []


def write_ledger(body: str, directory: Path, lines: list[str] | None = None) -> Path:
    """The `## Acceptance criteria` section, verbatim, as a ledger file."""
    criteria = lines if lines is not None else section(body, "Acceptance criteria")
    path = directory / LEDGER_NAME
    path.write_text("\n".join(criteria) + "\n", encoding="utf-8")
    return path


def count_gates(ledger: Path) -> tuple[int, int]:
    """(met, total) read off the ledger: a met gate is ticked with real evidence."""
    met = total = 0
    lines = ledger.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = GATE_LINE_RE.match(line)
        if not m:
            continue
        total += 1
        if m.group(1) == " ":
            continue
        evidence = ""
        for follow in lines[i + 1:]:
            if not follow.startswith((" ", "\t")):
                break
            if follow.strip().startswith("EVIDENCE:"):
                evidence = follow.split("EVIDENCE:", 1)[1].strip()
                break
        if evidence and evidence != "pending":
            met += 1
    return met, total


# -------------------------------------------------------------------- herdr

def report_phase(ticket: int, phase: str, extra: dict[str, str] | None = None) -> bool:
    """Publish where this ticket stands to the Herdr pane. Never fails a run."""
    if os.environ.get("HERDR_ENV") != "1":
        return False
    pane = os.environ.get("HERDR_PANE_ID")
    if not pane:
        return False
    cmd = [
        "herdr", "pane", "report-metadata", pane, "--source", "mmw",
        "--token", f"ticket={ticket}", "--token", "role=worker",
        "--token", f"phase={phase}", "--ttl-ms", TTL_MS,
    ]
    for key, value in (extra or {}).items():
        cmd += ["--token", f"{key}={value}"]
    try:
        subprocess.run(cmd, capture_output=True, timeout=10, check=False)
    except Exception:
        return False
    return True


# ----------------------------------------------------------------- subcommands

def approval_dir() -> Path:
    """gate-check refuses an approval directory that is group- or world-readable."""
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    APPROVAL_DIR.parent.chmod(0o700)
    APPROVAL_DIR.chmod(0o700)
    return APPROVAL_DIR


def run_checks(number: int, reverify: bool, timeout: int | None) -> int:
    phase = "verify" if reverify else "selfcheck"
    report_phase(number, phase)
    body = fetch_body(number)
    root = repo_root()
    carried = previous_ledger(number) if reverify else []
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp), carried or None)
        cmd = ["node", str(GATE_CHECK), "--approve", "--cwd", str(root)]
        if reverify:
            cmd.append("--reverify")
        if timeout:
            cmd += ["--timeout", str(timeout)]
        cmd.append(str(ledger))
        env = {**os.environ, "UNLAZY_APPROVAL_DIR": str(approval_dir())}
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
        printed = (result.stdout or "") + (result.stderr or "")
        sys.stdout.write(printed)
        if result.returncode == 2:
            report_phase(number, phase)
            return 2
        summary = [l for l in printed.splitlines() if SUMMARY_RE.match(l)]
        updated = ledger.read_text(encoding="utf-8").rstrip("\n")
        met, total = count_gates(ledger)

    outside = outside_owns(owns_globs(body), root)
    comment = "\n".join([
        "reverify" if reverify else "self-run",
        *summary,
        "",
        updated,
        "",
        "Outside Owns: " + (", ".join(outside) if outside else "None"),
    ])
    post_comment(number, comment)
    report_phase(number, phase, {"ac": f"{met}/{total}"})
    return result.returncode


def run_lint(number: int) -> int:
    body = fetch_body(number)
    with tempfile.TemporaryDirectory(prefix="verify-ticket-") as tmp:
        ledger = write_ledger(body, Path(tmp))
        result = subprocess.run(
            ["node", str(GATE_LINT), "--strict", str(ledger)],
            capture_output=True, text=True,
        )
    sys.stdout.write((result.stdout or "") + (result.stderr or ""))
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ticket", type=int)
    parser.add_argument("--reverify", action="store_true",
                        help="re-run every criterion, including the ones already ticked")
    parser.add_argument("--lint", action="store_true",
                        help="audit how the criteria are written; runs no CHECK, posts no comment")
    parser.add_argument("--timeout", type=int, help="per-CHECK timeout in seconds")
    args = parser.parse_args(argv)
    if args.lint and args.reverify:
        parser.error("--lint and --reverify are different jobs; pick one")
    if args.lint:
        return run_lint(args.ticket)
    return run_checks(args.ticket, args.reverify, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
