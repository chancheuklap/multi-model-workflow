#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_DIR/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
MARKETPLACE_NAME="multi-model-workflow"
PLUGIN_NAME="codex-orchestrate"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) shift ;;
    -h|--help) echo "Usage: verify-runtime-parity.sh --user"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

VALIDATOR="$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py"
if python3 -c 'import yaml' >/dev/null 2>&1; then
  python3 "$VALIDATOR" "$PLUGIN_DIR" >/dev/null
elif command -v uv >/dev/null 2>&1; then
  uv run --with pyyaml --no-project python "$VALIDATOR" "$PLUGIN_DIR" >/dev/null
else
  echo "verify: PyYAML is required for plugin validation; install PyYAML or uv" >&2
  exit 2
fi

codex plugin marketplace list | awk -v n="$MARKETPLACE_NAME" -v r="$REPO_ROOT" '$1 == n && $2 == r { found=1 } END { exit(found ? 0 : 1) }'
codex plugin list --marketplace "$MARKETPLACE_NAME" | grep -q "$PLUGIN_NAME"

VERSION="$(jq -r '.version' "$PLUGIN_DIR/.codex-plugin/plugin.json")"
CACHE_DIR="$CODEX_HOME/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION"
[[ -d "$CACHE_DIR" ]] || { echo "verify: missing plugin cache: $CACHE_DIR" >&2; exit 1; }
diff -qr "$PLUGIN_DIR" "$CACHE_DIR" >/dev/null || { echo "verify: plugin cache drift: $CACHE_DIR" >&2; exit 1; }

for file in "$PLUGIN_DIR"/agents/*.toml; do
  target="$CODEX_HOME/agents/$(basename "$file")"
  [[ -f "$target" ]] || { echo "verify: missing installed agent: $target" >&2; exit 1; }
  diff -q "$file" "$target" >/dev/null || { echo "verify: agent drift: $(basename "$file")" >&2; exit 1; }
done

python3 "$SCRIPT_DIR/sync-agent-config.py" verify \
  --config-file "$CODEX_HOME/config.toml" \
  --source-agents-dir "$PLUGIN_DIR/agents" \
  --target-agents-dir "$CODEX_HOME/agents" >/dev/null

echo "verify: runtime parity passed"
