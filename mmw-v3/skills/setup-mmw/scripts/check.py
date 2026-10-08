#!/usr/bin/env python3
"""Read-only check of everything the landing pipeline needs once per repository and machine.

    python3 check.py

Run from inside a clone. Writes nothing: not to the repository, the tracker, Nowledge Mem or
the machine. One line per item, `<status> <layer> <item>: <detail>`, then one summary line:

    ok         the item is in place
    missing    the pipeline cannot use this repository until it is; the detail says what fixes it
    note       in place, with something for the owner to look at (a protected branch)
    unchecked  could not be asked (no issue to probe with, no `gh`); not counted as missing

The summary is `SETUP OK` when nothing is missing, else `SETUP INCOMPLETE <n> missing`.
Exit 0 with `SETUP OK`, 1 otherwise.

The repository layer is what the `setup-mmw` skill sets up; the machine layer is the
tools the night's scripts call, which this skill reports and does not install; the session
layer is this session's own environment, which no script can change once it has started.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPACE = HERE / "space.py"
LABELS = HERE / "labels.py"
DOCS = {
    "docs/agents/issue-tracker.md": ("## Three label sets", "## Wayfinding operations"),
    "docs/agents/triage-labels.md": (),
    "docs/agents/domain.md": (),
}
IGNORED = (".worktrees/", ".scratch/", "story-shots/")
TOOLS = ("git", "python3", "uv", "node", "nmem")
RUNNERS = ("paseo", "herdr", "orca")
FEATURE_MAP_LINT = "python3 ~/.agents/skills/verify-ticket/scripts/feature_map.py lint"


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
               "; ".join(parts) + ". The night pushes its base, the project branch and issue-<n> "
               "branches by fast-forward; a rule on any of them refuses those pushes")


def check_ignored(report: Report, root: Path):
    lacking = [d for d in IGNORED
               if run(["git", "check-ignore", "-q", f"{d}probe"], cwd=root).returncode != 0]
    if lacking:
        report.add("missing", "repository", ".gitignore",
                   f"{', '.join(lacking)} not ignored; ticket worktrees, prototype evidence and story "
                   "screenshots are written there")
    else:
        report.add("ok", "repository", ".gitignore", ", ".join(IGNORED) + " ignored")


def check_docs(report: Report, root: Path):
    for rel, headings in DOCS.items():
        path = root / rel
        if not path.is_file():
            report.add("missing", "repository", rel, "absent; the setup-mmw skill writes it from its seed")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        lacking = [h for h in headings if h not in lines]
        if lacking:
            report.add("missing", "repository", rel,
                       f"lacks {', '.join(lacking)}; the setup-mmw skill adds it from its seed")
        else:
            report.add("ok", "repository", rel, "present" + (" with " + ", ".join(headings) if headings else ""))


def check_agents_md(report: Report, root: Path):
    agents = root / "AGENTS.md"
    text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    unlisted = [rel for rel in DOCS if rel not in text]
    if not agents.is_file():
        report.add("missing", "repository", "AGENTS.md", "absent; hosts find docs/agents/ through it")
    elif unlisted:
        report.add("missing", "repository", "AGENTS.md",
                   f"names no row for {', '.join(unlisted)}")
    else:
        report.add("ok", "repository", "AGENTS.md", "points at the three docs/agents/ files")
    claude = root / "CLAUDE.md"
    if claude.is_file() and "@AGENTS.md" in claude.read_text(encoding="utf-8").splitlines():
        report.add("ok", "repository", "CLAUDE.md", "imports @AGENTS.md")
    else:
        report.add("missing", "repository", "CLAUDE.md",
                   "has no line @AGENTS.md; Claude Code reads AGENTS.md only through it")


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


def check_space(report: Report, slug: str):
    proc = run([sys.executable, str(SPACE), "--check", slug])
    if proc.returncode == 0:
        report.add("ok", "repository", "Memory Space", f"{slug} in shared mode with mmw-toolbox")
    else:
        report.add("missing", "repository", "Memory Space", reason(proc))


def check_session(report: Report, slug: str):
    """This session's NMEM_SPACE: what it writes to Memory goes there, or to Default."""
    sys.path.insert(0, str(HERE))
    import space  # noqa: E402  (beside this script)
    want = space.ident_of(slug)
    have = os.environ.get("NMEM_SPACE", "")
    if have == want:
        report.add("ok", "session", "NMEM_SPACE", want)
        return
    report.add("note", "session", "NMEM_SPACE",
               f"this session's is {have or 'not set'}, not {want}, so what it writes to Memory "
               f"lands in {have or 'Default'}, and dispatch.sh refuses to open a night from it. "
               "A terminal opened in this repository after the Space exists sets it; start the "
               "session from there")


def check_checks(report: Report, root: Path):
    path = root / ".mmw" / "target.json"
    checks = None
    if not path.is_file():
        report.add("missing", "repository", ".mmw/target.json checks",
                   "no .mmw/target.json; a ticket closes and lands with no repository check run")
    else:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            report.add("missing", "repository", ".mmw/target.json checks", f"not JSON ({exc})")
        else:
            checks = data.get("checks") if isinstance(data, dict) else None
            if isinstance(checks, list) and checks:
                report.add("ok", "repository", ".mmw/target.json checks", f"{len(checks)} command(s)")
            else:
                report.add("missing", "repository", ".mmw/target.json checks",
                           "no `checks`; a ticket closes and lands with no repository check run")
    recorded = isinstance(checks, list) and any(
        isinstance(item, str) and item.strip() == FEATURE_MAP_LINT for item in checks)
    if (root / "docs" / "features").is_dir() and not recorded:
        report.add("missing", "repository", "feature map lint",
                   f"add `{FEATURE_MAP_LINT}` to `checks`")


def check_testing(report: Report, root: Path):
    if (root / "TESTING.md").is_file():
        report.add("ok", "repository", "TESTING.md", "present")
    else:
        report.add("missing", "repository", "TESTING.md",
                   "absent; a spec's seam and Testing Decisions have no test facts to draw on, "
                   "and the reviewer's Tests axis says there is none")


def check_layout(report: Report, root: Path):
    earlier = [rel for rel in ("docs/specs", "prototypes", "docs/prototypes")
               if (root / rel).is_dir() and any(p.is_dir() for p in (root / rel).iterdir())]
    if earlier:
        report.add("missing", "repository", "effort layout",
                   f"{', '.join(earlier)} hold effort files in the earlier layout, where no "
                   "playbook reads them; run python3 scripts/migrate_layout.py of the "
                   "setup-mmw skill on this branch")
    else:
        report.add("ok", "repository", "effort layout", "each effort's files under efforts/<effort>/")


def check_machine(report: Report):
    auth = run(["gh", "auth", "status"])
    report.add("ok" if auth.returncode == 0 else "missing", "machine", "gh login",
               "logged in" if auth.returncode == 0 else f"not logged in ({reason(auth)}); run gh auth login")
    absent = [tool for tool in TOOLS if shutil.which(tool) is None]
    report.add("missing" if absent else "ok", "machine", "tools",
               f"not on PATH: {', '.join(absent)}" if absent else ", ".join(TOOLS) + " on PATH")
    runners = [r for r in RUNNERS if shutil.which(r)]
    report.add("ok" if runners else "missing", "machine", "runner",
               ", ".join(runners) + " on PATH" if runners
               else f"none of {', '.join(RUNNERS)} on PATH; a night starts its sessions through one")
    models = Path(os.environ.get("MMW_HOME") or Path.home() / ".mmw") / "models.json"
    report.add("ok" if models.is_file() else "missing", "machine", "models.json",
               str(models) if models.is_file()
               else f"no {models}; it says which host and model each role runs on")
    if shutil.which("nmem"):
        toolbox = run(["nmem", "--json", "spaces", "show", "mmw-toolbox"])
        report.add("ok" if toolbox.returncode == 0 else "missing", "machine", "mmw-toolbox Space",
                   "present" if toolbox.returncode == 0
                   else f"nmem cannot show it ({reason(toolbox)}); every repository Space shares it")


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
    check_docs(report, root)
    check_agents_md(report, root)
    check_labels(report)
    if slug:
        check_space(report, slug)
    check_checks(report, root)
    check_testing(report, root)
    check_layout(report, root)
    check_machine(report)
    if slug:
        check_session(report, slug)
    report.print()
    return 0 if report.missing() == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
