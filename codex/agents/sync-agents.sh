#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  bash codex/agents/sync-agents.sh --dry-run
  bash codex/agents/sync-agents.sh --apply

Copies this repository's Codex agent templates into ~/.codex/agents/.
The script does not edit ~/.codex/config.toml and does not remove unrelated agents.
USAGE
}

MODE="${1:---dry-run}"
case "$MODE" in
  --dry-run|--apply) ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/agents"
STAMP="$(date +%Y%m%d%H%M%S)"

python3 "$SCRIPT_DIR/validate-agents.py"

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
    if [[ -f "$dst" ]] && ! cmp -s "$src" "$dst"; then
      backup="$dst.bak-$STAMP"
      cp "$dst" "$backup"
      echo "Backed up existing $dst -> $backup"
    fi
    cp "$src" "$dst"
    echo "Copied $src -> $dst"
  fi
done < "$templates_file"

if [[ "$MODE" == "--dry-run" ]]; then
  echo "Dry run complete. Re-run with --apply to copy files."
else
  echo "Sync complete. Restart Codex if updated agent instructions are not visible."
fi
