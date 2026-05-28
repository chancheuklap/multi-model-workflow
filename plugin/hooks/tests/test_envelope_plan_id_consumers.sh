#!/usr/bin/env bash
# Plan 005 Pack 5.13: dispatch-envelope plan_id consumption.
# Pin behavior: parse-envelope.sh passes plan_id through; all 5 consumer hooks
# can read .plan_id from the parsed JSON via `jq -r '.plan_id // empty'`.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARSER="$(cd "$SCRIPT_DIR/.." && pwd)/lib/parse-envelope.sh"

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

echo "=== test_envelope_plan_id_consumers.sh ==="

# Plan-level envelope (autonomous-mode dispatch)
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"plan-executor","repair_round":0,"idempotency_key":"k1","plan_id":"005","pack_id":null} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
PLAN_ID=$(echo "$PARSED" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$PARSED" | jq -r '.pack_id // empty')
assert_eq "plan-level envelope: plan_id parsed" "$PLAN_ID" "005"
assert_eq "plan-level envelope: pack_id null/empty" "$PACK_ID" ""

# Pack-level envelope (legacy / per-pack)
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack-executor","repair_round":0,"idempotency_key":"k2","pack_id":"5.1","plan_id":null} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
PLAN_ID=$(echo "$PARSED" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$PARSED" | jq -r '.pack_id // empty')
assert_eq "pack-level envelope: plan_id null/empty" "$PLAN_ID" ""
assert_eq "pack-level envelope: pack_id parsed" "$PACK_ID" "5.1"

# Missing plan_id and pack_id (both null) — parser still passes since not in required list
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"plan-writer","repair_round":0,"idempotency_key":"k3"} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
RC=$?
assert_eq "non-execution envelope (no plan_id/pack_id) → parse succeeds" "$RC" "0"

# Verify 5 consumer hooks reference plan_id (Pack 5.13 acceptance criteria)
HOOKS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COUNT=0
for hook in "$HOOKS_DIR"/agent-return-handler.sh \
            "$HOOKS_DIR"/track-execution-state.sh \
            "$HOOKS_DIR"/track-effort-budget.sh \
            "$HOOKS_DIR"/validate-plan-dispatch.sh \
            "$HOOKS_DIR"/enforce-plan-commit.sh; do
  if [[ -f "$hook" ]] && grep -qE 'plan_id|PLAN_ID' "$hook"; then
    COUNT=$((COUNT + 1))
  fi
done
# Note: enforce-plan-commit doesn't currently parse envelope; it's commit-driven.
# We expect at least 3 of the 5 hooks (handler/track-execution-state/track-effort-budget)
# to reference plan_id. validate-plan-dispatch will reference it after Pack 5.8 lands.
# Baseline as of Pack 5.13: track-effort-budget (Pack 5.12) and track-execution-state
# (existing) reference plan_id. Pack 5.9 lands handler reference, Pack 5.8 lands
# validate-plan-dispatch reference. This test pins the floor — 2 minimum now.
if [[ "$COUNT" -ge 2 ]]; then
  echo "  PASS: at least 2 hooks reference plan_id ($COUNT detected — track-effort-budget + track-execution-state minimum)"
  pass=$((pass + 1))
else
  echo "  FAIL: only $COUNT hooks reference plan_id (need at least 2 — track-effort-budget + track-execution-state)"
  fail=$((fail + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
