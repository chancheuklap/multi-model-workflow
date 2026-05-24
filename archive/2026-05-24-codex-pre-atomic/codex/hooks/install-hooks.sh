#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/codex/hooks"
SOURCE_HOOKS_JSON="$SOURCE_DIR/hooks.json"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST_DIR="$CODEX_HOME/hooks/multi-model-workflow"
HOOKS_JSON="$CODEX_HOME/hooks.json"
APPLY=0

usage() {
  cat <<'EOF'
Usage:
  bash codex/hooks/install-hooks.sh [--dry-run|--apply]

Installs multi-model-workflow Codex hooks at user level:
  ~/.codex/hooks/multi-model-workflow/session-start.sh
  ~/.codex/hooks/multi-model-workflow/guard-premature-push.sh
  ~/.codex/hooks/multi-model-workflow/guard-budget-immutable.sh
  ~/.codex/hooks/multi-model-workflow/track-review-budget.sh
  ~/.codex/hooks/multi-model-workflow/cleanup-run-state.sh
  ~/.codex/hooks.json

The user-level hooks.json is generated from codex/hooks/hooks.json with hook
script commands rewritten to the installed user-level paths.

Default mode is --dry-run.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    --dry-run)
      APPLY=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

for script in session-start.sh guard-premature-push.sh guard-budget-immutable.sh track-review-budget.sh cleanup-run-state.sh; do
  if [ ! -f "$SOURCE_DIR/$script" ]; then
    echo "ERROR: missing source hook script: $SOURCE_DIR/$script" >&2
    exit 1
  fi
done

if [ ! -f "$SOURCE_HOOKS_JSON" ]; then
  echo "ERROR: missing source hooks JSON: $SOURCE_HOOKS_JSON" >&2
  exit 1
fi

python3 -m json.tool "$SOURCE_HOOKS_JSON" >/dev/null

echo "Source:      $SOURCE_DIR"
echo "Source JSON: $SOURCE_HOOKS_JSON"
echo "Destination: $DEST_DIR"
echo "Hooks JSON:  $HOOKS_JSON"

if [ "$APPLY" -ne 1 ]; then
  echo "Dry run only. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$DEST_DIR"
cp "$SOURCE_DIR/session-start.sh" "$DEST_DIR/session-start.sh"
cp "$SOURCE_DIR/guard-premature-push.sh" "$DEST_DIR/guard-premature-push.sh"
cp "$SOURCE_DIR/guard-budget-immutable.sh" "$DEST_DIR/guard-budget-immutable.sh"
cp "$SOURCE_DIR/track-review-budget.sh" "$DEST_DIR/track-review-budget.sh"
cp "$SOURCE_DIR/cleanup-run-state.sh" "$DEST_DIR/cleanup-run-state.sh"
chmod +x "$DEST_DIR/session-start.sh" "$DEST_DIR/guard-premature-push.sh" "$DEST_DIR/guard-budget-immutable.sh" "$DEST_DIR/track-review-budget.sh" "$DEST_DIR/cleanup-run-state.sh"

TMP_JSON="$(mktemp)"
python3 - "$SOURCE_HOOKS_JSON" "$DEST_DIR" > "$TMP_JSON" <<'PY'
from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

source_json = Path(sys.argv[1])
dest = Path(sys.argv[2]).resolve()
payload = json.loads(source_json.read_text())


def rewrite_command(command: str) -> str:
    parts = shlex.split(command)
    if len(parts) >= 2 and parts[0] == "bash" and parts[1].startswith("codex/hooks/"):
        script = Path(parts[1]).name
        installed = dest / script
        if not installed.exists():
            raise SystemExit(f"hooks.json references missing installed hook script: {script}")
        return " ".join(shlex.quote(part) for part in ["bash", str(installed), *parts[2:]])
    return command


for entries in payload.values():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        hooks = entry.get("hooks", [])
        if not isinstance(hooks, list):
            continue
        for hook in hooks:
            if isinstance(hook, dict) and hook.get("type") == "command" and isinstance(hook.get("command"), str):
                hook["command"] = rewrite_command(hook["command"])

print(json.dumps(payload, ensure_ascii=False, indent=2))
PY

mv "$TMP_JSON" "$HOOKS_JSON"
python3 -m json.tool "$HOOKS_JSON" >/dev/null
echo "Installed user-level Codex hooks."
