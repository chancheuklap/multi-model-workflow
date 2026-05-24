#!/usr/bin/env bash
# Verifies that architecture-draft.md reflects the Codex orchestrate source tree.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 - "$PLUGIN_DIR" <<'PY'
import json
import re
import sys
import tomllib
from pathlib import Path

plugin_dir = Path(sys.argv[1])
arch_path = plugin_dir / "architecture-draft.md"
arch = arch_path.read_text()
errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def require_contains(needle: str, label: str) -> None:
    if needle not in arch:
        fail(f"architecture missing {label}: {needle}")


def require_not_contains(needle: str, label: str) -> None:
    if needle in arch:
        fail(f"architecture contains stale {label}: {needle}")


def markdown_table_after(header: str) -> list[list[str]]:
    lines = arch.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() != header:
            continue
        rows: list[list[str]] = []
        for raw in lines[idx + 1 :]:
            if not raw.strip():
                if rows:
                    break
                continue
            if not raw.startswith("|"):
                if rows:
                    break
                continue
            cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
            rows.append(cells)
        return rows[2:] if len(rows) >= 2 else []
    fail(f"architecture missing table header: {header}")
    return []


# Plugin version.
plugin_json = json.loads((plugin_dir / ".codex-plugin/plugin.json").read_text())
version_match = re.search(r"Codex Plugin 版本\*\*：([0-9.]+)", arch)
if not version_match:
    fail("architecture missing plugin version")
elif version_match.group(1) != plugin_json["version"]:
    fail(f"plugin version mismatch: architecture={version_match.group(1)} source={plugin_json['version']}")


# Internal skills.
skill_rows = markdown_table_after("### 内部 Skill（6 个 workflow phase + 1 个 ad-hoc review）")
documented_skills = sorted(row[0].strip("`") for row in skill_rows if row)
actual_skills = sorted(p.name for p in (plugin_dir / "skills").iterdir() if p.is_dir())
if documented_skills != actual_skills:
    fail(f"skill table mismatch: architecture={documented_skills} source={actual_skills}")


# Agent TOML table.
agent_rows = markdown_table_after("### Codex Subagent（8 个 TOML agent）")
documented_agents = sorted(
    (row[0].strip("`"), row[1].strip("`"), row[2].strip("`"), row[3].strip("`"))
    for row in agent_rows
    if len(row) >= 4
)
actual_agents = []
for path in sorted((plugin_dir / "agents").glob("*.toml")):
    data = tomllib.loads(path.read_text())
    if "name" not in data:
        continue
    actual_agents.append(
        (
            data.get("name", ""),
            data.get("model", ""),
            data.get("model_reasoning_effort", ""),
            data.get("sandbox_mode", ""),
        )
    )
actual_agents = sorted(actual_agents)
if documented_agents != actual_agents:
    fail(f"agent table mismatch: architecture={documented_agents} source={actual_agents}")


# Hooks table must match hooks.json command handlers. The table must avoid raw
# pipe characters inside cells, otherwise Markdown parsing lies about columns.
hook_rows = markdown_table_after("### Hooks（5 类事件 / 8 个 command handler）")
documented_hook_handlers = sorted(row[2].strip("`") for row in hook_rows if len(row) >= 3)
hooks_json = json.loads((plugin_dir / "hooks.json").read_text())["hooks"]
actual_hook_handlers: list[str] = []
for entries in hooks_json.values():
    for entry in entries:
        for hook in entry.get("hooks", []):
            command = hook.get("command", "")
            match = re.search(r"\$\{PLUGIN_ROOT\}/([^\" ]+)", command)
            if match:
                actual_hook_handlers.append(match.group(1))
actual_hook_handlers = sorted(actual_hook_handlers)
if documented_hook_handlers != actual_hook_handlers:
    fail(f"hook table mismatch: architecture={documented_hook_handlers} source={actual_hook_handlers}")


# Build templates and test counts.
for template in sorted((plugin_dir / "build/templates").glob("*.tmpl")):
    require_contains(f"`{template.name}`", f"build template {template.name}")

test_counts = {
    "build/tests/": len(list((plugin_dir / "build/tests").glob("test_*.sh"))),
    "hooks/tests/": len(list((plugin_dir / "hooks/tests").glob("test_*.sh"))),
    "scripts/tests/": len(list((plugin_dir / "scripts/tests").glob("test_*.sh"))),
}
for directory, count in test_counts.items():
    require_contains(f"| `{directory}` | {count} |", f"{directory} test count")


# State schema files.
for schema in sorted((plugin_dir / "state-schema").glob("*.json")):
    require_contains(f"`{schema.name}`", f"state schema {schema.name}")
require_contains("`state-transition-matrix.md`", "state transition matrix")


# Route extension files exist in both documented directories.
for route_name in ("route-4-hotfix.md", "route-5-quickfix.md", "route-6-spike.md", "route-7-maintenance.md"):
    for directory in (
        plugin_dir / "skills/orchestrate-workflow/references/route-extensions",
        plugin_dir / "skills/orchestrate-execution/references/route-extensions",
    ):
        if not (directory / route_name).is_file():
            fail(f"missing route extension: {directory / route_name}")


# Explicit runtime contracts that previously drifted.
closing = (plugin_dir / "skills/orchestrate-workflow/references/workflow-closing.md").read_text()
if "run-summary.sh\" --run-id \"<run_id>\"" not in closing:
    fail("workflow-closing must call run-summary.sh with --run-id")
if "run-summary-<run_id>.md" not in arch or "run-summary-<run_id>.md" not in closing:
    fail("run-summary artifact must be documented as Markdown .md")

signpost = (plugin_dir / "build/templates/signpost.md.tmpl").read_text()
if "`workflow` → `discovery` → `plan-writing` → `execution` → `final-review` → `closed`" not in signpost:
    fail("signpost phase sequence must match state transition matrix")

review_dispatch = (plugin_dir / "build/templates/review-dispatch.md.tmpl").read_text()
if "model:" in review_dispatch or "gpt-5.4" in review_dispatch:
    fail("review-dispatch must not override codex_reviewer TOML model")

require_contains('agent_type: "codex_reviewer"', "codex reviewer dispatch")
require_contains('`git worktree add -b "$BRANCH" "$WT_PATH" HEAD`', "worktree creation contract")

for stale, label in [
    ("run-summary-<run_id>.json", "run summary JSON artifact"),
    ("frontend-design", "old frontend skill name"),
    ("Codex worktree 迁移", "worktree migration wording"),
    ("startup|resume|clear|compact", "unescaped hook matcher"),
    ("Edit|Write|apply_patch", "unescaped hook matcher"),
    ("model: \"<phase model>\"", "phase model override"),
    ("plan-writing_done", "invalid plan-writing done state"),
    ("final-review_done", "invalid final-review done state"),
]:
    require_not_contains(stale, label)

checked_paths = [arch_path]
checked_paths.extend((plugin_dir / "skills").rglob("*.md"))
checked_paths.extend((plugin_dir / "build/templates").glob("*.tmpl"))
for stale in ("frontend-design", "gpt-5.4", "model: \"<phase-selected model>\"", "execution_done"):
    for path in checked_paths:
        text = path.read_text(errors="ignore")
        if stale in text:
            fail(f"stale token {stale!r} in {path.relative_to(plugin_dir)}")

if errors:
    for error in errors:
        print(f"FAIL: {error}")
    sys.exit(1)

print("architecture draft verified")
PY
