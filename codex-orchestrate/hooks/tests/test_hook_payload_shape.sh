#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0

run_test() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

echo "=== test_hook_payload_shape.sh ==="

run_test "SessionStart returns hook JSON" bash -c "
  PLUGIN_ROOT='$PLUGIN_DIR' bash '$PLUGIN_DIR/hooks/session-start.sh' \
    | jq -e '.hookSpecificOutput.hookEventName == \"SessionStart\" and (.hookSpecificOutput.additionalContext | contains(\"[codex-orchestrate] Runtime active\"))'
"

for payload in '\"string-payload\"' '[]' 'null'; do
  run_test "PostToolUse dispatcher skips $payload" bash -c \
    "printf '%s' '$payload' | bash '$PLUGIN_DIR/hooks/bash-posttool-dispatcher.sh'"
  run_test "PreToolUse Bash dispatcher skips $payload" bash -c \
    "printf '%s' '$payload' | bash '$PLUGIN_DIR/hooks/bash-pretool-dispatcher.sh'"
  run_test "PreToolUse edit dispatcher skips $payload" bash -c \
    "printf '%s' '$payload' | bash '$PLUGIN_DIR/hooks/edit-pretool-dispatcher.sh'"
  run_test "SubagentStart skips $payload" bash -c \
    "printf '%s' '$payload' | bash '$PLUGIN_DIR/hooks/subagent-start.sh'"
  run_test "SubagentStop skips $payload" bash -c \
    "printf '%s' '$payload' | bash '$PLUGIN_DIR/hooks/subagent-stop.sh'"
done

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
