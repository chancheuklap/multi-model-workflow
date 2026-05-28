#!/usr/bin/env bash
# Plan 005 Pack 5.5: state.sh agent-id set/get --plan-id verification.
# Already implemented in state.sh (Plan 002 Pack 2.6 base). This test pins behavior.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$(cd "$SCRIPT_DIR/.." && pwd)/state.sh"

FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

RUN_ID="agent-id-plan-test"
pass=0
fail=0

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

echo "=== test_state_agent_id_plan_level.sh ==="

ESF="$FIXTURE_DIR/execution-state-$RUN_ID.json"
cat > "$ESF" <<EOF
{"run_id":"$RUN_ID","plans":{"001":{"packs":{"1.1":{"status":"pending"}}},"002":{"packs":{"2.1":{"status":"pending"}}}}}
EOF

# Set plan-level agent
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "001" --agent-id "worker-X" 2>/dev/null
RESULT=$(jq -r '.plans["001"].worker_agent_id' "$ESF")
assert_eq "agent-id set --plan-id writes worker_agent_id" "$RESULT" "worker-X"

# Get plan-level agent
GET=$(bash "$STATE_SH" agent-id get --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
assert_eq "agent-id get --plan-id returns the value" "$GET" "worker-X"

# Plans are independent
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "002" --agent-id "worker-Y" 2>/dev/null
GET1=$(bash "$STATE_SH" agent-id get --run-id "$RUN_ID" --plan-id "001" 2>/dev/null)
GET2=$(bash "$STATE_SH" agent-id get --run-id "$RUN_ID" --plan-id "002" 2>/dev/null)
assert_eq "plan 001 still has worker-X" "$GET1" "worker-X"
assert_eq "plan 002 has worker-Y" "$GET2" "worker-Y"

# Pack-level still works (backward compat)
bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --pack-id "1.1" --agent-id "worker-A" 2>/dev/null
PACK_AID=$(jq -r '.plans["001"].packs["1.1"].agent_id' "$ESF")
assert_eq "agent-id set --pack-id (backward compat) writes pack.agent_id" "$PACK_AID" "worker-A"

# Mutual exclusion
if bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "001" --pack-id "1.1" --agent-id "z" 2>/dev/null; then
  echo "  FAIL: --plan-id + --pack-id should be mutually exclusive"
  fail=$((fail + 1))
else
  echo "  PASS: --plan-id + --pack-id correctly rejected"
  pass=$((pass + 1))
fi

# Unknown plan_id
if bash "$STATE_SH" agent-id set --run-id "$RUN_ID" --plan-id "nonexistent" --agent-id "z" 2>/dev/null; then
  echo "  FAIL: unknown plan_id should error"
  fail=$((fail + 1))
else
  echo "  PASS: unknown plan_id correctly rejected"
  pass=$((pass + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
