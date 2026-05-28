#!/usr/bin/env bash
# Plan 005 Pack 5.10: track-execution-state.sh NEXT message suppression.
# When worker_agent_id is set (autonomous-mode Worker in flight), suppress
# the "Dispatch Plan Implementation Review" NEXT — Worker will return via
# agent-return-handler.sh and that is the authoritative routing point.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$(cd "$SCRIPT_DIR/.." && pwd)/track-execution-state.sh"

WORKSPACE="$(mktemp -d)"
trap 'rm -rf "$WORKSPACE"' EXIT
cd "$WORKSPACE"

# Init git so HEAD SHA is resolvable
git init -q
git config user.email "t@t"
git config user.name "t"
echo "stub" > stub.txt
git add stub.txt
git commit -q -m "init"

BUDGET_DIR=".claude/multi-model-workflow"
mkdir -p "$BUDGET_DIR"
RUN_ID="tes-test"
echo "$RUN_ID" > "$BUDGET_DIR/active-run-id"

pass=0
fail=0

run_hook() {
  local plan_id="$1" pack_id="$2"
  local input
  input=$(jq -n --arg c "git commit -m \"Pack ${pack_id}: foo\"" \
    '{tool_input:{command:$c},tool_response:{exit_code:0}}')
  echo "$input" | bash "$HOOK" 2>&1
}

echo "=== test_track_execution_state_next_suppression.sh ==="

# Case A: Worker autonomous mode — worker_agent_id is set, all packs committed →
# expect "Worker still in session" NOT "Dispatch Plan Implementation Review"
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"005":{"worker_agent_id":"worker-X","packs":{"5.1":{"status":"committed"},"5.2":{"status":"pending"}}}}}
EOF
OUT=$(run_hook "005" "5.2")
if echo "$OUT" | grep -q "still in session"; then
  echo "  PASS: A) worker_agent_id non-empty → NEXT suppressed ('still in session')"
  pass=$((pass + 1))
else
  echo "  FAIL: A) suppression message missing (actual: $OUT)"
  fail=$((fail + 1))
fi
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  FAIL: A) NEXT 'Dispatch Plan Implementation Review' should NOT appear when Worker active"
  fail=$((fail + 1))
else
  echo "  PASS: A) NEXT 'Dispatch Plan Implementation Review' correctly omitted"
  pass=$((pass + 1))
fi

# Case B: worker_agent_id null (legacy / no autonomous Worker), all packs committed →
# expect "Dispatch Plan Implementation Review"
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"006":{"worker_agent_id":null,"packs":{"6.1":{"status":"committed"},"6.2":{"status":"pending"}}}}}
EOF
OUT=$(run_hook "006" "6.2")
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  PASS: B) worker_agent_id null → NEXT 'Dispatch Plan Implementation Review' emitted"
  pass=$((pass + 1))
else
  echo "  FAIL: B) NEXT 'Dispatch Plan Implementation Review' missing (actual: $OUT)"
  fail=$((fail + 1))
fi

# Case C: pack committed mid-plan (not all done) — STATE not NEXT
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"007":{"worker_agent_id":"worker-Z","packs":{"7.1":{"status":"pending"},"7.2":{"status":"pending"},"7.3":{"status":"pending"}}}}}
EOF
OUT=$(run_hook "007" "7.1")
if echo "$OUT" | grep -q "STATE: Pack 7.1 committed"; then
  echo "  PASS: C) mid-plan commit emits STATE not NEXT"
  pass=$((pass + 1))
else
  echo "  FAIL: C) mid-plan STATE message missing (actual: $OUT)"
  fail=$((fail + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
