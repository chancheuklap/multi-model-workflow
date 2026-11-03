#!/usr/bin/env python3
"""Run repository checks and identify reusable proof for an exact checkout.

The repository owns scripts/check. Exit 0 is green, 1 is red, and 2 means this machine
cannot run it. Other exits also mean cannot-run. Check output is retained in full;
failed output has a bounded excerpt and an optional worktree log.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("v5_repository_check_events", HERE / "events.py")
events = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(events)

CHECKS_ERROR_LINES = 10
CHECKS_TAIL_LINES = 30
COMMENT_BODY_LIMIT = 65536
EXCERPT_LINE_LIMIT = 8000
EXCERPT_BUDGET = 48000
REPOSITORY_CHECK = Path("scripts") / "check"
FAIL_STEP_RE = re.compile(r"^FAIL\s+(\S+)", re.M)
ERROR_LINE_RE = re.compile(r"error|fail|assert|exception|traceback", re.I)
PATH_LINE_RE = re.compile(r"(?:^|[\s\"'`(])(?:[\w.+@-]+/)*[\w.+@-]+\.[A-Za-z][\w]*:\d+\b")


def git(*args: str, cwd: Path | None = None) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return out.stdout.strip() if out.returncode == 0 else ""


def run_worktree_environment(worktree: Path, step: str) -> int:
    script = worktree / "scripts" / "env"
    if not script.exists():
        return 0
    try:
        result = subprocess.run([str(script), step, str(worktree)], cwd=worktree,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace")
    except OSError as exc:
        output, status = str(exc), 2
    else:
        output, status = result.stdout, result.returncode
    if status:
        sys.stderr.write(f"scripts/env {step} failed for {worktree} (exit {status}); "
                         "fix scripts/env and retry\n")
        sys.stderr.write("\n".join(output.splitlines()[-10:]) + "\n")
        return 2
    if output:
        sys.stderr.write(output)
    return 0


def repository_check_missing(root: Path) -> str | None:
    """Why `scripts/check` at `root` cannot be run, or None when it is an executable file."""
    path = Path(root) / REPOSITORY_CHECK
    if path.is_file() and os.access(path, os.X_OK):
        return None
    what = f"{path} is not executable" if path.exists() else f"{path} does not exist"
    return f"{what}; provide an executable scripts/check with exits 0 (green), 1 (red), 2 (cannot run)"


def _checks_excerpt(output: str) -> str:
    """First ten error or path:line lines and last thirty lines, in source order."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    hits = [i for i, line in enumerate(lines)
            if ERROR_LINE_RE.search(line) or PATH_LINE_RE.search(line)]
    kept = set(hits[:CHECKS_ERROR_LINES])
    kept.update(range(max(0, len(lines) - CHECKS_TAIL_LINES), len(lines)))
    return "\n".join(line.replace("LINT OK", "[redacted]")
                     for i, line in enumerate(lines) if i in kept)


def _cap_excerpt(text: str) -> str:
    """Keep the excerpt small enough to ride along to the bounce in the environment."""
    lines = [line[:EXCERPT_LINE_LIMIT] for line in text.splitlines()]
    while lines and sum(len(line) + 1 for line in lines) > EXCERPT_BUDGET:
        lines.pop()
    return "\n".join(lines)


def _failed_row(command: str, tail: str, exit_code: int | None = None,
                log: str | None = None) -> dict:
    row: dict = {"command": command, "tail": tail}
    if type(exit_code) is int:
        row["exit"] = exit_code
    if log:
        row["log"] = log
    return row


def _write_check_log(worktree: Path | str | None, ticket: str | int | None, seq: int,
                     raw: str, started: list[bool]) -> str | None:
    """The full output of one failed check, in the ticket worktree.

    The first failure of a run replaces `.scratch/checks/<ticket>/`. A missing worktree
    is left missing: the merge still bounces, and the excerpt is what the comment carries.
    A log that cannot be written does too — the red check is the event.
    """
    if worktree is None or ticket in (None, ""):
        return None
    root = Path(worktree)
    if not root.is_dir():
        return None
    folder = root / ".scratch" / "checks" / str(ticket)
    try:
        if not started[0]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True)
            started[0] = True
        (folder / f"{seq}.log").write_text(raw, encoding="utf-8")
    except OSError:
        return None
    return f".scratch/checks/{ticket}/{seq}.log"


def _check_heading(row: dict) -> str:
    command = " ".join(str(row.get("command") or "?").split())
    exit_code = row.get("exit")
    if type(exit_code) is int:
        command = f"{command} exit {exit_code}"
    steps = [str(step) for step in row.get("steps") or []]
    if steps:
        command = f"{command} (failed steps: {', '.join(steps)})"
    return command


def _comment_size(prefix_len: int, summary: str, rest: str, commands: list) -> int:
    """How long the bounce comment is, using a payload no smaller than a real one."""
    line = prefix_len + len(events.neutralise(f" Failed checks: {summary}."))
    cleaned = events.neutralise(rest or "").strip("\n")
    prose = line + (2 + len(cleaned) if cleaned else 0)
    payload = {
        "v": events.VERSION,
        "event": "ticket.bounced",
        "stage": "land",
        "actor": "main",
        "spec": 10**9,
        "ticket": 10**9,
        "at": "2026-01-01T00:00:00Z",
        "reason": "checks",
        "commit": "f" * 40,
        "into": "x" * 80,
        "commands": commands,
    }
    return prose + 2 + len(events.block(payload)) + 1


def _summary_of(rows: list[dict]) -> str:
    return "; ".join(_check_heading(row) for row in rows)


def _rest_of(rows: list[dict], excerpts: list[list[str]]) -> str:
    blocks = []
    for row, lines in zip(rows, excerpts):
        parts = [_check_heading(row)]
        log = row.get("log")
        if isinstance(log, str) and log:
            parts.extend(["", log])
        if lines:
            parts.extend(["", *lines])
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def _commands_of(rows: list[dict], excerpts: list[list[str]]) -> list[dict]:
    commands = []
    for row, lines in zip(rows, excerpts):
        item: dict = {"command": row.get("command", "?"), "tail": "\n".join(lines)}
        if type(row.get("exit")) is int:
            item["exit"] = row["exit"]
        if row.get("log"):
            item["log"] = row["log"]
        if row.get("steps"):
            item["steps"] = list(row["steps"])
        commands.append(item)
    return commands


def _fit_last_line(rows: list[dict], excerpts: list[list[str]], index: int,
                   prefix_len: int) -> None:
    original = excerpts[index][0]

    def size_with(text: str) -> int:
        excerpts[index] = [text] if text else []
        return _comment_size(prefix_len, _summary_of(rows), _rest_of(rows, excerpts),
                             _commands_of(rows, excerpts))

    if size_with(original) <= COMMENT_BODY_LIMIT:
        excerpts[index] = [original]
        return
    if size_with("") > COMMENT_BODY_LIMIT:
        excerpts[index] = []
        return
    lo, hi, best = 0, len(original), 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if size_with(original[:mid]) <= COMMENT_BODY_LIMIT:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    excerpts[index] = [original[:best]] if best else []


def _shrink_until_it_fits(rows: list[dict], excerpts: list[list[str]], prefix_len: int) -> None:
    for _ in range(64):
        if _comment_size(prefix_len, _summary_of(rows), _rest_of(rows, excerpts),
                         _commands_of(rows, excerpts)) <= COMMENT_BODY_LIMIT:
            return
        index = max(range(len(rows)), key=lambda i: len(str(rows[i].get("command") or "")))
        command = " ".join(str(rows[index].get("command") or "").split())
        if len(command) > 8:
            rows[index]["command"] = command[: max(8, len(command) // 2)]
            continue
        if rows[index].get("log"):
            rows[index]["log"] = ""
            continue
        return


def checks_bounce_prose(rows: list | None, prefix_len: int = 0) -> dict:
    """The checks bounce: one summary line, one paragraph per command, and the JSON.

    `prefix_len` is the merge sentence already written before ` Failed checks:`. The
    returned `commands` carry the excerpt that still fits, so the posted comment stays
    inside `COMMENT_BODY_LIMIT`. The full output stays in the log the paragraph names.
    """
    copied = [dict(row) for row in (rows or []) if isinstance(row, dict)]
    excerpts = [(row.get("tail") or "").splitlines() for row in copied]
    original = [len(lines) for lines in excerpts]

    def over() -> bool:
        return _comment_size(prefix_len, _summary_of(copied), _rest_of(copied, excerpts),
                             _commands_of(copied, excerpts)) > COMMENT_BODY_LIMIT

    while over():
        index = next((i for i in range(len(excerpts) - 1, -1, -1) if excerpts[i]), None)
        if index is None:
            break
        if len(excerpts[index]) == 1:
            _fit_last_line(copied, excerpts, index, prefix_len)
            break
        excerpts[index].pop()
    _shrink_until_it_fits(copied, excerpts, prefix_len)
    summary = _summary_of(copied)
    rest = _rest_of(copied, excerpts)
    commands = _commands_of(copied, excerpts)
    dropped = sum(max(0, original[i] - len(excerpts[i])) for i in range(len(copied)))
    if dropped:
        note = f"+{dropped} more"
        candidate = rest + ("\n\n" if rest else "") + note
        if _comment_size(prefix_len, summary, candidate, commands) <= COMMENT_BODY_LIMIT:
            rest = candidate
    return {"summary": summary, "rest": rest, "commands": commands}


def _run(path: Path, root: Path, env: dict, *args: str) -> tuple[int, str]:
    """`(exit code, combined output)` of one run, however long it takes: no time limit
    turns a slow test into a failure."""
    proc = subprocess.run([str(path), *args], cwd=root, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace")
    return proc.returncode, proc.stdout or ""


def run_repository_check(root: Path | str, base_ref: str,
                         worktree: Path | str | None = None,
                         ticket: str | int | None = None) -> dict:
    """Run `scripts/check` at `root` with `MMW_BASE_REF=base_ref` and no further arguments.

    Returns `{"status", "failed", "detail", "proof", "output"}`. `output` is the combined
    stdout and stderr of the check, or empty when it did not start. `proof` identifies a green or red run,
    the fields of its record (`proof_fields`), or None: a run on a tree with uncommitted
    or untracked files proved nothing about any commit. `status` is `pass` (exit 0), `red` (exit 1), `cannot-run`
    (exit 2, any other exit, or the script would not start: this machine cannot run
    it, which says nothing about the tree) or `missing` (no executable `scripts/check`).
    `failed` is one row for a red run: `command`, `tail` (the excerpt), `exit`, `steps`
    (the `FAIL <step>` lines it printed), and `log` when the full output was written
    under `worktree`'s `.scratch/checks/<ticket>/`. `detail` says what happened, with
    the last lines and the log's path, for every status but `pass`.
    """
    root = Path(root)
    missing = repository_check_missing(root)
    if missing:
        return {"status": "missing", "failed": [], "detail": missing, "proof": None, "output": ""}
    path = root / REPOSITORY_CHECK
    env = os.environ.copy()
    env["MMW_BASE_REF"] = base_ref
    before = tree_identity(root, base_ref)
    try:
        code, output = _run(path, root, env)
    except OSError as exc:
        return {"status": "cannot-run", "failed": [],
                "detail": f"{path} could not be started: {exc}", "proof": None, "output": ""}
    proof = None
    if code in (0, 1) and before is not None and tree_identity(root, base_ref) == before:
        steps = re.findall(r"^(?:PASS|FAIL)\s+(\S+)", output, re.M)
        proof = proof_fields("default", *before, steps)
    if code == 0:
        return {"status": "pass", "failed": [], "detail": "", "proof": proof, "output": output}
    log = _write_check_log(worktree, ticket, 1, output, [False])
    excerpt = _cap_excerpt(_checks_excerpt(output))
    where = f"; full output in {Path(worktree) / log}" if log else ""
    if code == 1:
        row = _failed_row(str(REPOSITORY_CHECK), excerpt, code, log)
        row["steps"] = FAIL_STEP_RE.findall(output)
        heading = _check_heading(row)
        return {"status": "red", "failed": [row], "proof": proof,
                "detail": f"{heading} in {root}{where}:\n{excerpt}".rstrip(), "output": output}
    what = ("exited 2: this machine cannot run it" if code == 2 else
            f"exited {code}, which is none of 0 (green), 1 (red) and 2 (cannot run)")
    return {"status": "cannot-run", "failed": [], "proof": None,
            "detail": f"{path} {what}{where}:\n{excerpt}".rstrip(), "output": output}


def tree_identity(root: Path, base_ref: str) -> tuple[str, str] | None:
    """`(commit, base commit)` of a clean checkout at `root`, or None: a checkout with
    uncommitted or untracked files is a tree no commit names, and an unreadable ref
    names nothing."""
    try:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                                capture_output=True, text=True, check=True).stdout
        head = git("rev-parse", "HEAD", cwd=root)
        base = git("rev-parse", "--verify", f"{base_ref}^{{commit}}", cwd=root)
    except (OSError, subprocess.CalledProcessError):
        return None
    if status.strip() or not all(re.fullmatch(r"[0-9a-f]{40}", v or "") for v in (head, base)):
        return None
    return head, base


def proof_fields(tier: str, commit: str, base: str, steps: list[str]) -> dict:
    return {"tier": tier, "commit": commit, "base": base,
            "machine": socket.gethostname(), "steps": steps}


def covering_proof(comments: list, commit: str, base: str) -> dict | None:
    """The newest green `spec.checked` record that proves the scoped check of `commit`
    against `base` on this machine: a default-tier record of that exact commit and base,
    or an `all` record of that commit with any base, since a full run of that commit
    covers every selection. None when no record covers it; the step then runs.
    Unreadable event blocks raise ValueError: incomplete records cannot authorize reuse."""
    machine = socket.gethostname()
    found = None
    for comment in events.normalise(comments):
        what, payload = events.parse(comment["body"])
        if what == "unreadable":
            label = comment["id"] if comment["id"] is not None else comment["position"]
            raise ValueError(f"cannot reuse repository-check proof: comment {label} carries "
                             f"an unreadable event ({payload})")
        if what != "event" or payload["event"] != "spec.checked":
            continue
        if (payload.get("result") == "met" and payload.get("commit") == commit
                and payload.get("machine") == machine
                and (payload.get("tier") == "all"
                     or (payload.get("tier") == "default" and payload.get("base") == base))):
            found = payload
    return found
