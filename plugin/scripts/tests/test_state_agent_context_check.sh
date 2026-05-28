#!/usr/bin/env bash
# Plan 005 Pack 5.4: state.sh agent-context-check subcommand.
# Threshold (Decision 4): packs_in_session >= 5 AND remaining_packs >= 2 → need-fresh-worker; otherwise ok.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="ctx-check-run"
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

assert_eq() {
  local name="$1" actual="$2" expected="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  PASS: $name"
    pass=$((pass + 1))
  else
    echo "  FAIL: $name — expected '$expected', got '$actual'"
    fail=$((fail + 1))
  fi
}

echo "=== test_state_agent_context_check.sh ==="

# Build a fixture execution-state with one plan, mix of statuses.
build_state() {
  local plan_id="$1"; shift
  local statuses=("$@")  # list like "committed" "committed" "pending" "pending" "pending"
  local esf="$FIXTURE_DIR/execution-state-${RUN_ID}.json"
  local packs="{}"
  local i=1
  for st in "${statuses[@]}"; do
    packs=$(echo "$packs" | jq --arg k "${plan_id}.${i}" --arg s "$st" \
      '. + {($k): {"status": $s}}')
    i=$((i+1))
  done
  jq -n --arg rid "$RUN_ID" --arg pid "$plan_id" --argjson packs "$packs" \
    '{run_id: $rid, plans: {($pid): {packs: $packs}}}' > "$esf"
}

# --- Case 1: 5 committed, 2 pending → need-fresh-worker
build_state "001" committed committed committed committed committed pending pending
OUT=$(bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
VERDICT=$(echo "$OUT" | jq -r '.verdict')
assert_eq "5 committed + 2 pending → need-fresh-worker" "$VERDICT" "need-fresh-worker"

# --- Case 2: 3 committed, 2 pending → ok (under threshold)
build_state "001" committed committed committed pending pending
OUT=$(bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
VERDICT=$(echo "$OUT" | jq -r '.verdict')
assert_eq "3 committed + 2 pending → ok" "$VERDICT" "ok"

# --- Case 3: 5 committed, 1 pending → ok (remaining < 2, not worth churn)
build_state "001" committed committed committed committed committed pending
OUT=$(bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
VERDICT=$(echo "$OUT" | jq -r '.verdict')
assert_eq "5 committed + 1 pending → ok (remaining<2)" "$VERDICT" "ok"

# --- Case 4: 6 committed, 3 pending → need-fresh-worker (above threshold both)
build_state "001" committed committed committed committed committed committed pending pending pending
OUT=$(bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
VERDICT=$(echo "$OUT" | jq -r '.verdict')
assert_eq "6 committed + 3 pending → need-fresh-worker" "$VERDICT" "need-fresh-worker"

# --- Case 5: JSON output is well-formed
build_state "001" committed pending
OUT=$(bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
run_test "output is valid JSON" bash -c "echo '$OUT' | jq empty"
HAS_REASON=$(echo "$OUT" | jq -r 'has("reason")')
assert_eq "output has 'reason' field" "$HAS_REASON" "true"
HAS_COMPLETED=$(echo "$OUT" | jq -r 'has("packs_in_session")')
assert_eq "output has 'packs_in_session' field" "$HAS_COMPLETED" "true"

# --- Case 6: missing plan_id → error
run_test_expect_fail() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  FAIL: $name (expected failure)"
    fail=$((fail + 1))
  else
    echo "  PASS: $name (expected failure)"
    pass=$((pass + 1))
  fi
}
run_test_expect_fail "missing --plan-id errors" \
  bash "$STATE_SH" agent-context-check --run-id "$RUN_ID"

# --- Case 7: nonexistent plan → error
run_test_expect_fail "nonexistent plan_id errors" \
  bash "$STATE_SH" agent-context-check --run-id "$RUN_ID" --plan-id "nonexistent"

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
