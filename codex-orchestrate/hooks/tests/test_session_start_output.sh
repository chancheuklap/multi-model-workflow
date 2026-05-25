#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION_START="$SCRIPT_DIR/../session-start.sh"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0

run_test() {
  local name="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name"
    fail=$((fail + 1))
  fi
}

echo "=== test_session_start_output.sh ==="

OUTPUT="$(bash "$SESSION_START")"
EXPECTED_ACTIVE_LINE="[multi-model-workflow] Codex workflow override active (version 3.6.2)"
EXPECTED_ROOT_LINE="\`export MMW_PLUGIN_ROOT=\"$PLUGIN_ROOT\"\`"

run_test "session-start emits valid JSON" \
  bash -c 'printf "%s" "$1" | jq empty' bash "$OUTPUT"

CONTEXT="$(printf '%s' "$OUTPUT" | jq -r '.hookSpecificOutput.additionalContext')"
EVENT="$(printf '%s' "$OUTPUT" | jq -r '.hookSpecificOutput.hookEventName')"

run_test "session-start JSON declares SessionStart event" \
  bash -c '[[ "$1" == "SessionStart" ]]' bash "$EVENT"

run_test "session-start context reports active version" \
  bash -c '[[ "$1" == *"$2"* ]]' bash "$CONTEXT" "$EXPECTED_ACTIVE_LINE"

run_test "session-start context prints concrete MMW_PLUGIN_ROOT export" \
  bash -c '[[ "$1" == *"$2"* ]]' bash "$CONTEXT" "$EXPECTED_ROOT_LINE"

run_test "session-start names current Matt Pocock skill namespace" \
  bash -c '[[ "$1" == *"mattpocock-skills:diagnose"* && "$1" == *"mattpocock-skills:grill-with-docs"* ]]' bash "$CONTEXT"

run_test "session-start does not advertise stale short-name skill namespace" \
  bash -c '[[ "$1" != *"User-level skills (short name, NO prefix)"* ]]' bash "$CONTEXT"

run_test "session-start scopes no-production-code gate to formal workflow" \
  bash -c '[[ "$1" == *"在 Orchestrate formal workflow 中，Coordinator 不直接写生产代码"* ]]' bash "$CONTEXT"

run_test "session-start includes direct final-review and multi-pr routing" \
  bash -c '[[ "$1" == *"multi-model-workflow:orchestrate-final-review"* && "$1" == *"multi-model-workflow:orchestrate-multi-pr-merge"* ]]' bash "$CONTEXT"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
