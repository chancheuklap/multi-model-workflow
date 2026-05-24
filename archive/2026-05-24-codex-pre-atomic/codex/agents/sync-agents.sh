#!/usr/bin/env bash
set -euo pipefail

MODE="--dry-run"
UPDATE_CONFIG=0
CONFIG_FILE="${CODEX_HOME:-$HOME/.codex}/config.toml"

usage() {
  cat <<'USAGE'
Usage:
  bash codex/agents/sync-agents.sh [--dry-run|--apply] [--update-config] [--config PATH]

Copies this repository's Codex agent templates into ~/.codex/agents/.

Options:
  --dry-run        Show copy actions without changing runtime files.
  --apply          Copy templates into the Codex agent runtime.
  --update-config  Register managed agent_type entries in ~/.codex/config.toml.
  --config PATH    Use a different Codex config path when updating config.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run|--apply)
      MODE="$1"
      shift
      ;;
    --update-config)
      UPDATE_CONFIG=1
      shift
      ;;
    --config)
      CONFIG_FILE="${2:-}"
      if [ -z "$CONFIG_FILE" ]; then
        echo "ERROR: --config requires a path" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/agents"

templates_file="$(mktemp)"
trap 'rm -f "$templates_file"' EXIT
find "$SCRIPT_DIR" -maxdepth 1 -type f -name '*.toml' | sort > "$templates_file"
if [[ ! -s "$templates_file" ]]; then
  echo "No templates found in $SCRIPT_DIR" >&2
  exit 1
fi

echo "Target: $TARGET_DIR"
while IFS= read -r src; do
  dst="$TARGET_DIR/$(basename "$src")"
  if [[ "$MODE" == "--dry-run" ]]; then
    echo "DRY-RUN copy $src -> $dst"
  else
    mkdir -p "$TARGET_DIR"
    cp "$src" "$dst"
    echo "Copied $src -> $dst"
  fi
done < "$templates_file"

if [[ "$UPDATE_CONFIG" -eq 1 ]]; then
  if [[ "$MODE" == "--dry-run" ]]; then
    echo "DRY-RUN update managed agent entries in $CONFIG_FILE"
  else
    python3 - "$CONFIG_FILE" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1]).expanduser()
config_path.parent.mkdir(parents=True, exist_ok=True)
text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""

agents = [
    ("coding_worker", "Code implementation worker for scoped implementation, tests, bug fixes, and local refactors.", "agents/coding-worker.toml", ["Builder", "Coder", "Patch"]),
    ("complex_coding_worker", "High-judgment implementation worker for cross-module changes, migrations, billing, auth, runtime, or architecture-sensitive code.", "agents/complex-coding-worker.toml", ["Engineer", "Integrator", "Builder"]),
    ("plan_writer", "Implementation plan writer for reviewed designs and issue hierarchies.", "agents/plan-writer.toml", ["Planner", "Architect", "Writer"]),
    ("root_cause_analyst", "Root-cause analyst for unknown bugs, failed repair loops, and systemic multi-PR conflicts.", "agents/root-cause-analyst.toml", ["Investigator", "Analyst", "Debugger"]),
    ("code_reviewer", "Code and spec reviewer for design, plan, pack, final, and integration review gates.", "agents/code-reviewer.toml", ["Reviewer", "Auditor", "Inspector"]),
    ("release_reviewer", "Release or production-risk reviewer for migrations, billing, permissions, cross-service contracts, and final merge gates.", "agents/release-reviewer.toml", ["Gatekeeper", "Auditor", "Inspector"]),
    ("code_explorer", "Focused codebase explorer for narrow file, symbol, call-chain, and test-location questions.", "agents/code-explorer.toml", ["Scout", "Mapper", "Reader"]),
    ("complex_code_explorer", "Broad codebase explorer for multi-module relationships, historical behavior, migration chains, and architecture context.", "agents/complex-code-explorer.toml", ["Architect", "Mapper", "Investigator"]),
    ("docs_worker", "Documentation and mechanical synthesis worker for low-risk docs edits, summaries, and structured cleanup.", "agents/docs-worker.toml", ["Writer", "Editor", "Scribe"]),
]

for name, *_ in agents:
    pattern = re.compile(
        rf"\n?\[agents\.{re.escape(name)}\]\n.*?(?=\n\[agents\.|\n\[[^\]]+\]|\Z)",
        re.S,
    )
    text = pattern.sub("\n", text)

if "[agents]" not in text:
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n[agents]\nmax_threads = 6\nmax_depth = 1\n"

blocks = []
for name, description, config_file, nicknames in agents:
    quoted = ", ".join(f'"{nickname}"' for nickname in nicknames)
    blocks.append(
        f"[agents.{name}]\n"
        f'description = "{description}"\n'
        f'config_file = "{config_file}"\n'
        f"nickname_candidates = [{quoted}]\n"
    )
managed = "\n" + "\n".join(blocks)

header = re.search(r"(\[agents\]\n(?:[^\n\[]|\n(?!\[))*)", text)
if not header:
    raise SystemExit("ERROR: failed to locate or create [agents] section")

insert_at = header.end()
text = text[:insert_at].rstrip() + "\n" + managed + text[insert_at:]
text = re.sub(r"\n{4,}", "\n\n\n", text).rstrip() + "\n"

config_path.write_text(text, encoding="utf-8")
print(f"Updated managed agent entries in {config_path}")
PY
  fi
fi

if [[ "$MODE" == "--dry-run" ]]; then
  echo "Dry run complete. Re-run with --apply to copy files."
else
  echo "Sync complete. Restart Codex if updated agent instructions are not visible."
fi
