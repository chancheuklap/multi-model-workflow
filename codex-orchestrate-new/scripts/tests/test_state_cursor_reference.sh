#!/usr/bin/env bash
# test_state_cursor_reference.sh
# Pack 6.4: verify workflow-state.cursor.reference accepts and round-trips merge-brief paths.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="test-cursor-ref"
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

run_test_value() {
  local name="$1"; local expected="$2"; shift 2
  local actual
  actual=$("$@" 2>/dev/null) || actual="ERROR"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name (expected='$expected' actual='$actual')"
    fail=$((fail + 1))
  fi
}

echo "=== test_state_cursor_reference.sh ==="

# Setup
run_test "init workflow state" \
  bash "$STATE_SH" init --run-id "$RUN_ID" --slug "cursor-test" --route "multi-pr-merge"

# cursor.reference is null by default
run_test_value "cursor.reference is null by default" "null" \
  bash "$STATE_SH" read --run-id "$RUN_ID" --field ".cursor.reference"

# Write merge-brief path to cursor.reference using state.sh update
MERGE_BRIEF_PATH=".codex/multi-model-workflow/merge-brief-${RUN_ID}.md"
run_test "set cursor.reference to merge-brief path" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field ".cursor.reference" --value "\"${MERGE_BRIEF_PATH}\""

# Read back — must be exactly the same path
run_test_value "cursor.reference round-trips merge-brief path" "$MERGE_BRIEF_PATH" \
  bash "$STATE_SH" read --run-id "$RUN_ID" --field ".cursor.reference"

# cursor.reference accepts null reset
run_test "reset cursor.reference to null" \
  bash "$STATE_SH" update --run-id "$RUN_ID" --field ".cursor.reference" --value "null"

run_test_value "cursor.reference is null after reset" "null" \
  bash "$STATE_SH" read --run-id "$RUN_ID" --field ".cursor.reference"

# State file remains valid JSON after updates
run_test "state file is valid JSON after cursor.reference writes" \
  python3 -m json.tool "$FIXTURE_DIR/workflow-state-${RUN_ID}.json"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
