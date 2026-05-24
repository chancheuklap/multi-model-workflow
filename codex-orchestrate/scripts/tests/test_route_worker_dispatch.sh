#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
VALIDATE_SH="$SCRIPT_DIR/../validate-route-worker-dispatch.sh"
RECORD_SH="$SCRIPT_DIR/../record-route-worker-dispatch.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected failure)"; fail=$((fail+1)); else echo "  PASS: $name (expected failure)"; pass=$((pass+1)); fi; }

echo "=== test_route_worker_dispatch.sh ==="

RUN_ID="route-worker-001"
bash "$STATE_SH" init --run-id "$RUN_ID" --slug "bug-route" --route "bug-investigation" >/dev/null

PROMPT="$FIXTURE_DIR/worker-prompt.md"
cat > "$PROMPT" <<'PROMPT'
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "route-worker-001",
  "phase": "bug-investigation",
  "agent_role": "pack_executor",
  "agent_id": null,
  "pack_id": null,
  "repair_round": 0,
  "idempotency_key": "route-worker-001/bug-fix-worker/r0",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "route-worker-001/bug-fix-worker"
}
-->

## Scope
Fix a bug found by root_cause_analyst.
PROMPT

AGENT_FILE="$FIXTURE_DIR/worker-agents/bug-fix-worker.agent-id"

run_test "route worker dispatch validates" \
  bash "$VALIDATE_SH" --prompt-file "$PROMPT"

run_test "record route worker dispatch writes agent id" \
  bash "$RECORD_SH" --prompt-file "$PROMPT" --agent-id "agent-123" --agent-file "$AGENT_FILE"

run_test "recorded route worker agent id is readable" \
  bash -c "[[ \$(cat '$AGENT_FILE') == 'agent-123' ]]"

run_test_expect_fail "duplicate route worker dispatch is blocked" \
  bash "$VALIDATE_SH" --prompt-file "$PROMPT"

EXEC_PROMPT="$FIXTURE_DIR/execution-worker-prompt.md"
sed 's/"pack_id": null/"pack_id": "1.1"/' "$PROMPT" > "$EXEC_PROMPT"

run_test_expect_fail "route worker validator rejects execution pack_id" \
  bash "$VALIDATE_SH" --prompt-file "$EXEC_PROMPT"

REPAIR_PROMPT="$FIXTURE_DIR/worker-repair-prompt.md"
cat > "$REPAIR_PROMPT" <<'PROMPT'
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "route-worker-001",
  "phase": "bug-investigation",
  "agent_role": "pack_executor",
  "agent_id": "agent-123",
  "pack_id": null,
  "repair_round": 1,
  "idempotency_key": "route-worker-001/bug-fix-worker/r1",
  "disposition_refs": ["worker-followup"],
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "route-worker-001/bug-fix-worker"
}
-->

## Scope
Continue the original bug worker with corrected context.
PROMPT

run_test "route worker send_input repair validates" \
  bash "$VALIDATE_SH" --prompt-file "$REPAIR_PROMPT" --transport send_input

NO_AGENT_REPAIR="$FIXTURE_DIR/worker-repair-no-agent.md"
sed 's/"agent_id": "agent-123"/"agent_id": null/' "$REPAIR_PROMPT" > "$NO_AGENT_REPAIR"

run_test_expect_fail "route worker repair requires original agent_id" \
  bash "$VALIDATE_SH" --prompt-file "$NO_AGENT_REPAIR" --transport send_input

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
