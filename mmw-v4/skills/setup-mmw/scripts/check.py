#!/usr/bin/env python3
"""Read-only check of everything the landing pipeline needs once per repository and machine.

    python3 check.py

Run from inside a clone. Writes nothing: not to the repository, the tracker or the machine. One line per item, `<status> <layer> <item>: <detail>`, then one summary line:

    ok         the item is in place
    missing    the pipeline cannot use this repository until it is; the detail says what fixes it
    note       usable as it is, with something for the owner to look at (a protected branch)
    unchecked  could not be asked (no issue to probe with, no `gh`); not counted as missing

The summary is `SETUP OK` when nothing is missing, else `SETUP INCOMPLETE <n> missing`.
Exit 0 with `SETUP OK`, 1 otherwise.

The repository layer is what the `setup-mmw` skill sets up; the machine layer is one row,
the toolbox's own install as the installed `install.sh --check` reads it, the machine's base
tools (gh logged in, git, python3, uv, node, a runner) among it. This skill reports it and
installs nothing on the machine.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IGNORED = (".worktrees/", ".scratch/")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def reason(proc: subprocess.CompletedProcess) -> str:
    return (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip().splitlines()[-1]


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
                   "the pipeline's store is GitHub Issues, reached through gh")
        return None
    try:
        info = json.loads(proc.stdout)
    except ValueError:
        report.add("unchecked", "repository", "tracker", "gh repo view did not return JSON")
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


def check_tree_features(report: Report, slug: str):
    """Sub-issues and issue dependencies, probed read-only on the newest issue."""
    newest = run(["gh", "api", f"repos/{slug}/issues?state=all&per_page=1", "--jq", ".[0].number"])
    number = newest.stdout.strip() if newest.returncode == 0 else ""
    if not number or number == "null":
        report.add("unchecked", "repository", "sub-issues and dependencies",
                   "the repository has no issue to ask about yet")
        return
    absent = []
    for what, path in (("sub-issues", f"repos/{slug}/issues/{number}/sub_issues"),
                       ("dependencies", f"repos/{slug}/issues/{number}/dependencies/blocked_by")):
        if run(["gh", "api", path, "--silent"]).returncode != 0:
            absent.append(what)
    if absent:
        report.add("missing", "repository", "sub-issues and dependencies",
                   f"GitHub refused {' and '.join(absent)} on #{number}; maps, specs and tickets "
                   "are linked by both")
    else:
        report.add("ok", "repository", "sub-issues and dependencies", f"both answered on #{number}")


def check_protection(report: Report, slug: str):
    """Protected branches and active rulesets: a push the night makes may be refused."""
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
               "; ".join(parts) + ". The pipeline pushes the base branch, the project branch, and issue-<n> "
               "and fix-<n> branches by fast-forward; a rule on any of them refuses those pushes")


def check_ignored(report: Report, root: Path):
    lacking = [d for d in IGNORED
               if run(["git", "check-ignore", "-q", f"{d}probe"], cwd=root).returncode != 0]
    if lacking:
        report.add("missing", "repository", ".gitignore",
                   f"{', '.join(lacking)} not ignored; ticket worktrees, and the logs of criteria and check runs, "
                   "are written there")
    else:
        report.add("ok", "repository", ".gitignore", ", ".join(IGNORED) + " ignored")




def check_labels(report: Report):
    sys.path.insert(0, str(HERE))
    import labels  # noqa: E402  (beside this script)
    table = labels.label_table()
    have = labels.existing()
    if isinstance(have, str):
        report.add("unchecked", "repository", "labels", have)
        return
    lacking = [name for name in table if name not in have]
    if lacking:
        report.add("missing", "repository", "labels",
                   f"{len(lacking)} of {len(table)} absent ({', '.join(lacking)}); "
                   "scripts/labels.py of the setup-mmw skill creates them")
    else:
        report.add("ok", "repository", "labels", f"all {len(table)} present")




def check_repository_check(report: Report, root: Path):
    """`scripts/check`, which every landing runs on the merged tree and refuses to land
    without."""
    path = root / "scripts" / "check"
    if not path.is_file():
        report.add("missing", "repository", "scripts/check",
                   "absent; no ticket lands without it. The Set up code checkers playbook writes it")
    elif not os.access(path, os.X_OK):
        report.add("missing", "repository", "scripts/check",
                   "not executable; no ticket lands until it is: chmod +x scripts/check and commit the mode")
    else:
        report.add("ok", "repository", "scripts/check", "present and executable")


def check_testing(report: Report, root: Path):
    if (root / "TESTING.md").is_file():
        report.add("ok", "repository", "TESTING.md", "present")
    else:
        report.add("missing", "repository", "TESTING.md",
                   "absent; a spec's or a ticket's seam has no test facts to draw on, "
                   "and the reviewer's Tests axis reads none")


def check_verification_skills(report: Report, root: Path):
    for design in sorted((root / "design").glob("*")):
        if not design.is_dir():
            continue
        name = f"verify-{design.name}"
        skill = Path(".agents") / "skills" / name / "SKILL.md"
        if (root / skill).is_file():
            report.add("ok", "repository", name, f"{skill} present for design/{design.name}/")
        else:
            report.add("missing", "repository", name,
                       f"no {skill} for design/{design.name}/; "
                       "the owner names the create-verification-skill skill to generate it")


def check_install(report: Report):
    """The toolbox's install, as its own --check reads it: skills, hooks, prompt, models.json,
    and the machine's base tools."""
    recorded = Path(os.environ.get("MMW_HOME") or Path.home() / ".mmw") / "installed-root"
    if not recorded.is_file():
        report.add("missing", "machine", "install",
                   f"no {recorded}; MMW is not installed on this machine: "
                   "run bash mmw-v4/install.sh from a checkout of the toolbox")
        return
    script = Path(recorded.read_text().strip()) / "install.sh"
    if not script.is_file():
        report.add("missing", "machine", "install",
                   f"{recorded} names {script.parent}, which has no install.sh; "
                   "run bash mmw-v4/install.sh again from a checkout of the toolbox")
        return
    proc = run(["bash", str(script), "--check"])
    if proc.returncode == 0:
        report.add("ok", "machine", "install", f"{script} --check passes")
        return
    gaps = [line for line in proc.stderr.splitlines() if line.strip()]
    report.add("missing", "machine", "install",
               f"{script} --check exits {proc.returncode}, {len(gaps)} line(s) on stderr, first: "
               f"{gaps[0].strip() if gaps else reason(proc)}; run bash {script} to repair it")


def main() -> int:
    report = Report()
    root = repo_root()
    if root is None:
        print("not inside a git repository", file=sys.stderr)
        return 2
    slug = check_tracker(report)
    if slug:
        check_tree_features(report, slug)
        check_protection(report, slug)
    check_ignored(report, root)
    check_labels(report)
    check_repository_check(report, root)
    check_testing(report, root)
    check_verification_skills(report, root)
    check_install(report)
    report.print()
    return 0 if report.missing() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
