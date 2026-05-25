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

run_test "session-start reports active version" \
  bash -c '[[ "$1" == *"$2"* ]]' bash "$OUTPUT" "$EXPECTED_ACTIVE_LINE"

run_test "session-start prints concrete MMW_PLUGIN_ROOT export" \
  bash -c '[[ "$1" == *"$2"* ]]' bash "$OUTPUT" "$EXPECTED_ROOT_LINE"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
