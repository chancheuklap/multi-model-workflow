#!/usr/bin/env bash
# Verify source/runtime parity for the installed Codex plugin and custom agents.
set -euo pipefail

PLUGIN_DIR="${1:-codex-orchestrate}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PLUGIN_NAME="multi-model-workflow"
PLUGIN_SELECTOR="multi-model-workflow@multi-model-workflow"
CONFIG_FILE="$CODEX_HOME/config.toml"

fail_count=0

fail() {
  echo "  ✗ $*"
  fail_count=$((fail_count + 1))
}

pass() {
  echo "  ✓ $*"
}

[[ -f "$PLUGIN_DIR/.codex-plugin/plugin.json" ]] || fail "missing source manifest"
VERSION=$(jq -r '.version // empty' "$PLUGIN_DIR/.codex-plugin/plugin.json")
[[ -n "$VERSION" ]] || fail "source manifest missing version"

CACHE_DIR="$CODEX_HOME/plugins/cache/$PLUGIN_NAME/$PLUGIN_NAME/$VERSION"
if [[ -d "$CACHE_DIR" ]]; then
  if diff -qr "$PLUGIN_DIR" "$CACHE_DIR" >/dev/null; then
    pass "plugin cache matches source ($CACHE_DIR)"
  else
    fail "plugin cache differs from source ($CACHE_DIR)"
  fi
else
  fail "plugin cache missing: $CACHE_DIR"
fi

for agent_file in "$PLUGIN_DIR"/agents/*.toml; do
  agent_name="$(basename "$agent_file")"
  runtime_file="$CODEX_HOME/agents/$agent_name"
  if [[ ! -f "$runtime_file" ]]; then
    fail "runtime agent missing: $runtime_file"
  elif diff -q "$agent_file" "$runtime_file" >/dev/null; then
    pass "runtime agent matches: $agent_name"
  else
    fail "runtime agent differs: $agent_name"
  fi
done

if [[ -f "$CONFIG_FILE" ]]; then
  for agent_file in "$PLUGIN_DIR"/agents/*.toml; do
    agent_name="$(basename "$agent_file" .toml)"
    if grep -q "^\[agents\\.${agent_name}\]" "$CONFIG_FILE"; then
      pass "agent registered in config: $agent_name"
    else
      fail "agent not registered in config: $agent_name"
    fi
  done
else
  fail "Codex config missing: $CONFIG_FILE"
fi

if [[ -f "$CONFIG_FILE" ]]; then
  if ! python3 - "$PLUGIN_DIR/hooks.json" "$CONFIG_FILE" "$PLUGIN_SELECTOR" <<'PY'
import json
import re
import sys
from pathlib import Path

hooks_path = Path(sys.argv[1])
config_path = Path(sys.argv[2])
selector = sys.argv[3]

event_keys = {
    "SessionStart": "session_start",
    "PreToolUse": "pre_tool_use",
    "PostToolUse": "post_tool_use",
    "SubagentStart": "subagent_start",
    "SubagentStop": "subagent_stop",
}

hooks = json.loads(hooks_path.read_text(encoding="utf-8")).get("hooks", {})
config_text = config_path.read_text(encoding="utf-8")
missing = []
for event_name, groups in hooks.items():
    event_key = event_keys.get(event_name)
    if event_key is None:
        continue
    for group_index, group in enumerate(groups):
        for hook_index, _hook in enumerate(group.get("hooks", [])):
            key = f'{selector}:hooks.json:{event_key}:{group_index}:{hook_index}'
            pattern = rf'^\[hooks\.state\."{re.escape(key)}"\]$'
            if not re.search(pattern, config_text, flags=re.MULTILINE):
                missing.append(key)

if missing:
    for key in missing:
        print(f"  ✗ hook not trusted in config: {key}")
    sys.exit(1)
print("  ✓ all plugin hooks have persisted trust records")
PY
  then
    fail "plugin hook trust records incomplete"
  fi
fi

if [[ "$fail_count" -gt 0 ]]; then
  echo "Runtime parity failed: $fail_count issue(s)"
  exit 1
fi

echo "Runtime parity passed"
