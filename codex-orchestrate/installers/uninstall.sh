#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_DIR/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
MARKETPLACE_NAME="multi-model-workflow"
PLUGIN_NAME="codex-orchestrate"
APPLY=false

usage() {
  echo "Usage: uninstall.sh --user [--dry-run|--apply]"
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) shift ;;
    --dry-run) APPLY=false; shift ;;
    --apply) APPLY=true; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown argument: $1" >&2; usage ;;
  esac
done

run() {
  if [[ "$APPLY" == "true" ]]; then
    "$@" || true
  else
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  fi
}

for file in "$PLUGIN_DIR"/agents/*.toml; do
  [[ -f "$file" ]] || continue
  run rm -f "$CODEX_HOME/agents/$(basename "$file")"
done

run python3 "$SCRIPT_DIR/sync-agent-config.py" remove --config-file "$CODEX_HOME/config.toml"
run codex plugin remove "${PLUGIN_NAME}@${MARKETPLACE_NAME}"

if codex plugin marketplace list 2>/dev/null | awk -v n="$MARKETPLACE_NAME" -v r="$REPO_ROOT" '$1 == n && $2 == r { found=1 } END { exit(found ? 0 : 1) }'; then
  run codex plugin marketplace remove "$MARKETPLACE_NAME"
fi

echo "uninstall: complete"
