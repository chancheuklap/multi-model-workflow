#!/usr/bin/env python3
"""Check of everything the landing pipeline needs once per repository and machine.

    python3 check.py

Run from inside a clone. The isolation probe creates and removes two temporary worktrees
and their test resources. Apart from that probe, the check writes nothing to the repository,
the tracker or the machine. Cleanup failures appear in the scripts/env row.
One line per item, `<status> <layer> <item>: <detail>`, then one summary line:

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
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IGNORED = (".worktrees/", ".scratch/")


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except OSError as exc:
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


def check_env(report: Report, root: Path):
    compose = any((root / name).is_file() for name in
                  ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"))
    if not (root / "scripts" / "env").exists():
        needed = compose
        if not needed:
            tracked = run(["git", "ls-files", "-z"], cwd=root)
            if tracked.returncode != 0:
                report.add("unchecked", "repository", "scripts/env",
                           f"git ls-files failed: {reason(tracked)}; restore access to the git index and rerun")
                return
            test_dirs = {"test", "tests", "__tests__", "spec", "e2e"}
            sources = {root / "scripts" / "check"}
            sources.update(root / name for name in tracked.stdout.split("\0")
                           if name and test_dirs.intersection(Path(name).parts[:-1]))
            for path in sources:
                if not path.is_file():
                    continue
                try:
                    words = path.read_text(errors="replace")
                except OSError as exc:
                    report.add("unchecked", "repository", "scripts/env",
                               f"cannot read {path}: {exc}; restore read access and rerun")
                    return
                if re.search(r"\b(?:postgres|postgresql|mysql|redis|docker|databases?|containers?|ports?)\b|数据库|端口|容器",
                             words, re.IGNORECASE):
                    needed = True
                    break
        if needed:
            report.add("missing", "repository", "scripts/env",
                       "测试用到数据库或容器，而没有 scripts/env；每个工作树需要自己的资源")
        else:
            report.add("ok", "repository", "scripts/env", "not needed; no database or container test resources")
        return
    resources: list[set[str]] = []
    errors: list[str] = []
    trees: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="mmw-env-probe-") as temporary:
        try:
            for name in ("one", "two"):
                tree = Path(temporary) / name
                added = run(["git", "worktree", "add", "--detach", str(tree), "HEAD"], cwd=root)
                if added.returncode != 0:
                    errors.append(f"worktree add {tree} failed: {reason(added)}")
                    continue
                trees.append(tree)
                for verb in ("setup", "up"):
                    proc = run([str(tree / "scripts" / "env"), verb, str(tree)], cwd=tree)
                    if proc.returncode != 0:
                        errors.append(f"scripts/env {verb} {tree} failed: {reason(proc)}")
                        break
                    if verb == "up":
                        names = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
                        if not names:
                            errors.append(f"scripts/env up {tree} printed no resource names; "
                                          "print one resource name per line in scripts/env")
                        resources.append(names)
            if len(resources) == 2:
                shared = resources[0] & resources[1]
                if shared:
                    errors.append("shared resources: " + ", ".join(sorted(shared)))
        finally:
            for tree in trees:
                proc = run([str(tree / "scripts" / "env"), "down", str(tree)], cwd=tree)
                if proc.returncode != 0:
                    errors.append(f"scripts/env down {tree} failed: {reason(proc)}")
                removed = run(["git", "worktree", "remove", "--force", str(tree)], cwd=root)
                if removed.returncode != 0:
                    errors.append(f"worktree remove {tree} failed: {reason(removed)}")
    if errors:
        report.add("missing", "repository", "scripts/env", "; ".join(errors))
    else:
        report.add("ok", "repository", "scripts/env", "two worktrees use separate resources; probe cleaned up")


def check_claude_md(report: Report, root: Path):
    """A root CLAUDE.md: Claude Code reads only CLAUDE.md when one exists, so a one-line
    import of AGENTS.md guarantees AGENTS.md reaches it."""
    if (root / "CLAUDE.md").is_file():
        report.add("ok", "repository", "CLAUDE.md", "present")
    else:
        report.add("missing", "repository", "CLAUDE.md",
                   "absent; setup creates it, holding the one line @AGENTS.md, so Claude Code "
                   "is sent to AGENTS.md")


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
    check_env(report, root)
    check_claude_md(report, root)
    check_install(report)
    report.print()
    return 0 if report.missing() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
