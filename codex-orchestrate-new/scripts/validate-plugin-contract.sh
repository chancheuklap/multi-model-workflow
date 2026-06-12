#!/usr/bin/env bash
# Validate the Codex plugin manifest contract used by this repository.
set -euo pipefail

PLUGIN_DIR="${1:-codex-orchestrate-new}"
MANIFEST="$PLUGIN_DIR/.codex-plugin/plugin.json"

fail() {
  echo "Plugin contract validation failed: $*" >&2
  exit 1
}

require_jq() {
  command -v jq >/dev/null 2>&1 || fail "jq is required"
}

require_jq

[[ -f "$MANIFEST" ]] || fail "missing .codex-plugin/plugin.json"
python3 -m json.tool "$MANIFEST" >/dev/null || fail "plugin.json is not valid JSON"

NAME=$(jq -r '.name // empty' "$MANIFEST")
VERSION=$(jq -r '.version // empty' "$MANIFEST")
DESCRIPTION=$(jq -r '.description // empty' "$MANIFEST")
SKILLS_PATH=$(jq -r '.skills // empty' "$MANIFEST")
HOOKS_PATH=$(jq -r '.hooks // empty' "$MANIFEST")

[[ -n "$NAME" ]] || fail "plugin.json field name is required"
[[ -n "$VERSION" ]] || fail "plugin.json field version is required"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+([+-][0-9A-Za-z.-]+)?$ ]] || fail "version must be semver"
[[ -n "$DESCRIPTION" ]] || fail "plugin.json field description is required"

[[ "$SKILLS_PATH" == "./skills/" || "$SKILLS_PATH" == "./skills" ]] || fail "skills must point to ./skills/"
[[ -d "$PLUGIN_DIR/skills" ]] || fail "skills directory not found"

[[ "$HOOKS_PATH" == ./* ]] || fail "hooks must be a ./-prefixed path"
HOOKS_FILE="$PLUGIN_DIR/${HOOKS_PATH#./}"
[[ -f "$HOOKS_FILE" ]] || fail "hooks file not found: $HOOKS_FILE"
python3 -m json.tool "$HOOKS_FILE" >/dev/null || fail "hooks file is not valid JSON"

jq -e '.hooks | type == "object"' "$HOOKS_FILE" >/dev/null || fail "hooks file must contain hooks object"
jq -e '
  [
    .hooks
    | to_entries[]
    | .value[]
    | .hooks[]
    | select(.type != "command" or (.command | type != "string") or (.command | length == 0))
  ]
  | length == 0
' "$HOOKS_FILE" >/dev/null || fail "all hook handlers must be non-empty command hooks"

for field in displayName shortDescription longDescription developerName category; do
  jq -e --arg field "$field" '.interface[$field] | type == "string" and length > 0' "$MANIFEST" >/dev/null \
    || fail "interface.$field is required"
done

jq -e '.interface.capabilities | type == "array" and length > 0' "$MANIFEST" >/dev/null \
  || fail "interface.capabilities must be a non-empty array"

jq -e '(.interface.defaultPrompt // .interface.default_prompt) | type == "array" and length > 0' "$MANIFEST" >/dev/null \
  || fail "interface.defaultPrompt must be a non-empty array"

echo "Plugin contract validation passed: $PLUGIN_DIR"
