#!/usr/bin/env bash
# Plan 005 Pack 5.13: dispatch-envelope plan_id consumption.
# Pin behavior: parse-envelope.sh passes plan_id through; current Codex hook
# consumers that route Plan-level execution must read plan_id explicitly.
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
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack_executor","repair_round":0,"idempotency_key":"k1","plan_id":"005","pack_id":null} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
PLAN_ID=$(echo "$PARSED" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$PARSED" | jq -r '.pack_id // empty')
assert_eq "plan-level envelope: plan_id parsed" "$PLAN_ID" "005"
assert_eq "plan-level envelope: pack_id null/empty" "$PACK_ID" ""

# Pack-level envelope (legacy / per-pack)
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"pack_executor","repair_round":0,"idempotency_key":"k2","pack_id":"5.1","plan_id":null} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
PLAN_ID=$(echo "$PARSED" | jq -r '.plan_id // empty')
PACK_ID=$(echo "$PARSED" | jq -r '.pack_id // empty')
assert_eq "pack-level envelope: plan_id null/empty" "$PLAN_ID" ""
assert_eq "pack-level envelope: pack_id parsed" "$PACK_ID" "5.1"

# Missing plan_id and pack_id (both null) — parser still passes since not in required list
PROMPT=$(printf '<!-- DISPATCH_ENVELOPE {"protocol_version":"1","run_id":"r1","phase":"execution","agent_role":"plan_writer","repair_round":0,"idempotency_key":"k3"} -->')
PARSED=$(echo "$PROMPT" | bash "$PARSER" 2>/dev/null)
RC=$?
assert_eq "non-execution envelope (no plan_id/pack_id) → parse succeeds" "$RC" "0"

# Verify current consumer hooks reference plan_id. Every listed file must exist;
# this test must not silently count removed hooks.
HOOKS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
for hook_name in agent-return-handler.sh track-execution-state.sh validate-plan-dispatch.sh; do
  hook="$HOOKS_DIR/$hook_name"
  if [[ ! -f "$hook" ]]; then
    echo "  FAIL: required consumer hook missing: $hook_name"
    fail=$((fail + 1))
  elif grep -qE 'plan_id|PLAN_ID' "$hook"; then
    echo "  PASS: consumer hook references plan_id: $hook_name"
    pass=$((pass + 1))
  else
    echo "  FAIL: consumer hook lacks plan_id reference: $hook_name"
    fail=$((fail + 1))
  fi
done

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
