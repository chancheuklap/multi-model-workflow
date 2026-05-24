#!/usr/bin/env bash
set -euo pipefail

PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATOR="$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py"

if python3 -c 'import yaml' >/dev/null 2>&1; then
  python3 "$VALIDATOR" "$PLUGIN_DIR" >/dev/null
else
  uv run --with pyyaml --no-project python "$VALIDATOR" "$PLUGIN_DIR" >/dev/null
fi
jq empty "$PLUGIN_DIR/.codex-plugin/plugin.json"
jq empty "$PLUGIN_DIR/hooks/hooks.json"
test ! -e "$PLUGIN_DIR/hooks.json"

jq -e 'has("apps") | not' "$PLUGIN_DIR/.codex-plugin/plugin.json" >/dev/null
jq -e 'has("mcpServers") | not' "$PLUGIN_DIR/.codex-plugin/plugin.json" >/dev/null
test ! -e "$PLUGIN_DIR/.app.json"
test ! -e "$PLUGIN_DIR/.mcp.json"
jq -e '.skills == "./skills/"' \
  "$PLUGIN_DIR/.codex-plugin/plugin.json" >/dev/null
