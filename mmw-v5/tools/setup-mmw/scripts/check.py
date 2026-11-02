#!/usr/bin/env python3
"""Check v5 setup facts for the consuming repository and selected runner.

    python3 check.py [--role ROLE ...]

The repository is bound through origin. No installation, hook, prompt, tracker, Git
or resource changes are made. Selected model resolution uses the dispatch models API
and may refresh its catalog cache under statedir.home(). Only requested role hosts
are resolved; without --role, model availability is explicitly unchecked.

Rows are `<status> <layer> <item>: <detail>`. Missing requirements produce
`SETUP INCOMPLETE <n> missing` and exit 1; otherwise `SETUP OK` and exit 0.
An unchecked row states the limit of this check. Running outside Git exits 2.
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISPATCH = HERE.parents[1] / "dispatch" / "scripts"
sys.path.insert(0, str(DISPATCH))
import models
import tracker

IGNORED = (".worktrees/", ".scratch/")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        env = tracker.environment() if cmd[0] == "gh" else None
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=120)
    except (OSError, subprocess.SubprocessError, tracker.RepositoryError) as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def reason(proc: subprocess.CompletedProcess) -> str:
    return (proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}").splitlines()[-1]


class Report:
    def __init__(self):
        self.rows: list[tuple[str, str, str, str]] = []

    def add(self, status: str, layer: str, item: str, detail: str):
        self.rows.append((status, layer, item, detail))

    def missing(self) -> int:
        return sum(1 for row in self.rows if row[0] == "missing")

    def print(self):
        for status, layer, item, detail in self.rows:
            print(f"{status:<10} {layer:<10} {item}: {detail}")
        n = self.missing()
        print("SETUP OK" if n == 0 else f"SETUP INCOMPLETE {n} missing")


def repo_root() -> Path | None:
    proc = run(["git", "rev-parse", "--show-toplevel"])
    return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None


def check_tracker(report: Report) -> str | None:
    """The GitHub repository behind origin, with Issues on; its owner/name, or None."""
    proc = run(["gh", "repo", "view", "--json", "nameWithOwner,hasIssuesEnabled,defaultBranchRef"])
    if proc.returncode != 0:
        report.add("missing", "repository", "tracker",
                   f"gh cannot reach this checkout's repository on GitHub ({reason(proc)}); "
                   "check origin and GitHub access through gh")
        return None
    try:
        info = json.loads(proc.stdout)
        if not isinstance(info, dict):
            raise ValueError("repository response is not an object")
    except ValueError:
        report.add("missing", "repository", "tracker", "gh repo view did not return JSON")
        return None
    slug = info.get("nameWithOwner", "")
    branch = (info.get("defaultBranchRef") or {}).get("name") or "none"
    if not info.get("hasIssuesEnabled"):
        report.add("missing", "repository", "tracker",
                   f"{slug} has Issues turned off; the owner turns them on in the repository's "
                   "Settings, General, Features")
    else:
        report.add("ok", "repository", "tracker",
                   f"{slug} on GitHub with Issues on; default branch {branch}")
    return slug


def check_protection(report: Report, slug: str):
    """Report branch protection without imposing a branch workflow."""
    branches = run(["gh", "api", "--paginate", f"repos/{slug}/branches?protected=true&per_page=100",
                    "--jq", ".[].name"])
    rulesets = run(["gh", "api", f"repos/{slug}/rulesets",
                    "--jq", '.[] | select(.enforcement == "active") | .name'])
    if branches.returncode != 0 or rulesets.returncode != 0:
        failed = branches if branches.returncode != 0 else rulesets
        report.add("unchecked", "repository", "branch rules", reason(failed))
        return
    names = branches.stdout.split()
    rules = [line for line in rulesets.stdout.splitlines() if line.strip()]
    if not names and not rules:
        report.add("ok", "repository", "branch rules", "no protected branch, no active ruleset")
        return
    parts = []
    if names:
        parts.append("protected branches " + ", ".join(names))
    if rules:
        parts.append("active rulesets " + ", ".join(rules))
    report.add("note", "repository", "branch rules",
               "; ".join(parts) + ". Protected branches may require a pull request or additional checks")


def check_ignored(report: Report, root: Path):
    lacking = [d for d in IGNORED
               if run(["git", "check-ignore", "-q", f"{d}probe"], cwd=root).returncode != 0]
    if lacking:
        report.add("missing", "repository", ".gitignore",
                   f"{', '.join(lacking)} not ignored; worktrees and check logs use these directories")
    else:
        report.add("ok", "repository", ".gitignore", ", ".join(IGNORED) + " ignored")


def check_repository_check(report: Report, root: Path):
    """The executable repository check entrypoint; do not execute it during setup."""
    path = root / "scripts" / "check"
    if not path.is_file():
        report.add("missing", "repository", "scripts/check",
                   "absent; add the repository check entrypoint at scripts/check")
    elif not os.access(path, os.X_OK):
        report.add("missing", "repository", "scripts/check",
                   "not executable; chmod +x scripts/check and commit the mode")
    else:
        report.add("ok", "repository", "scripts/check", "present and executable")


def check_tree_features(report: Report, slug: str):
    """Read native links and the gh relation fields dispatch uses for one actual issue."""
    newest = run(["gh", "issue", "list", "--state", "all", "--limit", "1", "--json", "number"])
    if newest.returncode != 0:
        report.add("missing", "repository", "sub-issues and dependencies", reason(newest))
        return
    try:
        issues = json.loads(newest.stdout)
        if not isinstance(issues, list):
            raise ValueError("issue response is not a list")
        number = int(issues[0]["number"]) if issues else None
    except (ValueError, KeyError, TypeError):
        report.add("missing", "repository", "sub-issues and dependencies",
                   "gh issue list did not return issue identities")
        return
    if number is None:
        report.add("unchecked", "repository", "sub-issues and dependencies",
                   "the repository has no issue to ask about yet")
        return
    absent = []
    for what, endpoint in (("sub-issues", "sub_issues"),
                           ("dependencies", "dependencies/blocked_by")):
        proc = run(["gh", "api", f"repos/{slug}/issues/{number}/{endpoint}", "--silent"])
        if proc.returncode:
            absent.append(f"{what}: {reason(proc)}")
    fields = run(["gh", "issue", "view", str(number), "--json", "parent,blockedBy"])
    if fields.returncode:
        absent.append(f"gh native link fields: {reason(fields)}")
    if absent:
        report.add("missing", "repository", "sub-issues and dependencies",
                   f"GitHub refused native links on #{number}: {'; '.join(absent)}")
    else:
        report.add("ok", "repository", "sub-issues and dependencies", f"native links and gh relation fields answered on #{number}")


def check_labels(report: Report):
    spec = importlib.util.spec_from_file_location("mmw_v5_setup_labels", HERE / "labels.py")
    labels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(labels)
    table = labels.label_table()
    have = labels.existing()
    if isinstance(have, str):
        report.add("missing", "repository", "labels", have)
        return
    lacking = [name for name in table if name not in have]
    if lacking:
        report.add("missing", "repository", "labels",
                   f"{len(lacking)} of {len(table)} absent ({', '.join(lacking)}); "
                   "the adjacent labels.py creates missing labels when requested")
    else:
        report.add("ok", "repository", "labels", f"all {len(table)} present")


def check_env(report: Report, root: Path):
    """Environment entrypoint facts are optional; setup never starts repository resources."""
    path = root / "scripts/env"
    if path.is_file():
        executable = "executable" if os.access(path, os.X_OK) else "not executable"
        report.add("note", "repository", "scripts/env", f"present, {executable}; not executed")
    elif any((root / name).is_file() for name in
             ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")):
        report.add("note", "repository", "scripts/env",
                   "compose configuration present; no scripts/env entrypoint; resources were not probed")
    else:
        report.add("note", "repository", "scripts/env", "no entrypoint; resources were not probed")


def check_binary(report: Report, name: str) -> bool:
    path = shutil.which(name)
    if path:
        report.add("ok", "machine", name, path)
    else:
        report.add("missing", "machine", name, f"{name} is not executable on PATH")
    return bool(path)


def check_machine(report: Report, roles: list[str]):
    """Check dispatch's configuration shape, selected adapter and requested role resolution."""
    for name in ("git", "gh", "bash", "python3", "realpath"):
        check_binary(report, name)
    try:
        models.session_rows()
        runner = models.runner_name()
    except (ValueError, OSError, TypeError) as exc:
        report.add("missing", "machine", "models.json", str(exc))
        return
    report.add("ok", "machine", "models.json", str(models.models_json_path()))
    if not models.has_adapter(runner):
        report.add("missing", "machine", "runner", f"{runner} has no adjacent runner adapter")
        return
    try:
        description = models.runner_description(runner)
    except (ValueError, OSError) as exc:
        report.add("missing", "machine", "runner", str(exc))
        return
    report.add("ok", "machine", "runner", runner)
    if runner == "codex-app":
        available = run(["bash", str(DISPATCH / "runners/codex-app.sh"), "available"])
        if available.returncode:
            report.add("missing", "machine", "Codex App binary", reason(available))
        else:
            report.add("ok", "machine", "Codex App binary", available.stdout.strip())
    else:
        check_binary(report, runner)
    if not roles:
        report.add("unchecked", "machine", "models", "no --role supplied; model availability was not queried")
        return
    previous = os.environ.get("MMW_CATALOG_MODE")
    os.environ["MMW_CATALOG_MODE"] = description["catalog"]
    try:
        for role in dict.fromkeys(roles):
            try:
                row = models.resolve_session(role)
                host = models.load_hosts()["hosts"][row.host]
                if not models._can_start(runner, host):
                    raise ValueError(f"runner {runner} cannot start host {row.host}")
                if description["launch"] == "cli":
                    check_binary(report, host["binary"])
                report.add("ok", "machine", f"model {role}",
                           f"{row.host} {row.model} ({row.effort}) via {runner}")
            except (ValueError, OSError, TypeError, KeyError) as exc:
                report.add("missing", "machine", f"model {role}", str(exc))
    finally:
        if previous is None:
            os.environ.pop("MMW_CATALOG_MODE", None)
        else:
            os.environ["MMW_CATALOG_MODE"] = previous


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", action="append", default=[],
                        help="validate this role's model and host; repeat for the roles this run uses")
    args = parser.parse_args(argv)
    report = Report()
    root = repo_root()
    if root is None:
        print("not inside a git repository, or Git is unavailable", file=sys.stderr)
        return 2
    slug = check_tracker(report)
    if slug:
        check_tree_features(report, slug)
        check_protection(report, slug)
        check_labels(report)
    check_ignored(report, root)
    check_repository_check(report, root)
    check_env(report, root)
    check_machine(report, args.role)
    report.print()
    return 0 if report.missing() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
