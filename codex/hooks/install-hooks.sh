#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="$ROOT_DIR/codex/hooks"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST_DIR="$CODEX_HOME/hooks/multi-model-workflow"
HOOKS_JSON="$CODEX_HOME/hooks.json"
APPLY=0

usage() {
  cat <<'EOF'
Usage:
  codex/hooks/install-hooks.sh [--dry-run|--apply]

Installs multi-model-workflow Codex hooks at user level:
  ~/.codex/hooks/multi-model-workflow/session-start.sh
  ~/.codex/hooks/multi-model-workflow/guard-premature-push.sh
  ~/.codex/hooks.json

Default mode is --dry-run. Existing ~/.codex/hooks.json is backed up before
replacement when it differs.
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

for script in session-start.sh guard-premature-push.sh; do
  if [ ! -f "$SOURCE_DIR/$script" ]; then
    echo "ERROR: missing source hook script: $SOURCE_DIR/$script" >&2
    exit 1
  fi
done

echo "Source:      $SOURCE_DIR"
echo "Destination: $DEST_DIR"
echo "Hooks JSON:  $HOOKS_JSON"

if [ "$APPLY" -ne 1 ]; then
  echo "Dry run only. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$DEST_DIR"
cp "$SOURCE_DIR/session-start.sh" "$DEST_DIR/session-start.sh"
cp "$SOURCE_DIR/guard-premature-push.sh" "$DEST_DIR/guard-premature-push.sh"
chmod +x "$DEST_DIR/session-start.sh" "$DEST_DIR/guard-premature-push.sh"

TMP_JSON="$(mktemp)"
python3 - "$DEST_DIR" > "$TMP_JSON" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

dest = Path(sys.argv[1]).resolve()
payload = {
    "SessionStart": [
        {
            "matcher": "startup|resume|clear",
            "hooks": [
                {
                    "type": "command",
                    "command": f"bash {dest / 'session-start.sh'}",
                }
            ],
        }
    ],
    "PreToolUse": [
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": f"bash {dest / 'guard-premature-push.sh'}",
                }
            ],
        }
    ],
}

print(json.dumps(payload, ensure_ascii=False, indent=2))
PY

if [ -e "$HOOKS_JSON" ] && ! diff -q "$HOOKS_JSON" "$TMP_JSON" >/dev/null 2>&1; then
  STAMP="$(date +%Y%m%d%H%M%S)"
  cp "$HOOKS_JSON" "$HOOKS_JSON.bak-$STAMP"
  echo "Backed up existing hooks JSON to $HOOKS_JSON.bak-$STAMP"
fi

mv "$TMP_JSON" "$HOOKS_JSON"
python3 -m json.tool "$HOOKS_JSON" >/dev/null
echo "Installed user-level Codex hooks."
