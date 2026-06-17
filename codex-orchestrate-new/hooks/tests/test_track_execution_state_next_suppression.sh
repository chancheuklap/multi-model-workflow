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

BUDGET_DIR=".codex/multi-model-workflow"
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

# Case D: Plan already reviewed (review_verdict=pass), all packs committed →
# 不能再发 review NEXT（已审完 Plan 被 commit_sha 污染重复触发的根因防线）
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"001":{"worker_agent_id":null,"review_verdict":"pass","packs":{"1.1":{"status":"committed"},"1.2":{"status":"committed"}}}}}
EOF
OUT=$(run_hook "001" "1.2")
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  FAIL: D) review_verdict=pass 的 Plan 不应再提示 Dispatch Review (actual: $OUT)"
  fail=$((fail + 1))
else
  echo "  PASS: D) review_verdict=pass → Dispatch Review NEXT 被抑制"
  pass=$((pass + 1))
fi

# Case E: Plan finalized (status=completed), all packs committed → 同样抑制
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"002":{"worker_agent_id":null,"status":"completed","packs":{"2.1":{"status":"committed"}}}}}
EOF
OUT=$(run_hook "002" "2.1")
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  FAIL: E) status=completed 的 Plan 不应再提示 Dispatch Review (actual: $OUT)"
  fail=$((fail + 1))
else
  echo "  PASS: E) status=completed → Dispatch Review NEXT 被抑制"
  pass=$((pass + 1))
fi

# Case F: plan-returns ingest 已写入 Worker worktree 的真实 SHA 后，hook cwd
# HEAD 只能作 fallback，不能覆盖 pack commit_sha 或 end_commit。
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"002":{"worker_agent_id":null,"end_commit":"worker-end-sha","packs":{"2.1":{"status":"committed","commit_sha":"worker-pack-2-1-sha"},"2.2":{"status":"committed","commit_sha":"worker-end-sha"}}}}}
EOF
OUT=$(run_hook "002" "2.1")
PACK_SHA=$(jq -r '.plans["002"].packs["2.1"].commit_sha' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
END_SHA=$(jq -r '.plans["002"].end_commit' "$BUDGET_DIR/execution-state-${RUN_ID}.json")
if [[ "$PACK_SHA" == "worker-pack-2-1-sha" ]]; then
  echo "  PASS: F) existing Worker pack commit_sha preserved"
  pass=$((pass + 1))
else
  echo "  FAIL: F) pack commit_sha was overwritten (actual: $PACK_SHA; hook output: $OUT)"
  fail=$((fail + 1))
fi
if [[ "$END_SHA" == "worker-end-sha" ]]; then
  echo "  PASS: F) existing Worker end_commit preserved"
  pass=$((pass + 1))
else
  echo "  FAIL: F) end_commit was overwritten (actual: $END_SHA; hook output: $OUT)"
  fail=$((fail + 1))
fi

# Case G: worker 自己写 worker_verdict / finished_at 仍不代表 SubagentStop
# return-handler 已完成；继续抑制 review NEXT。
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"008":{"worker_agent_id":"worker-done","worker_verdict":"pass","finished_at":"2026-06-17T00:00:00Z","packs":{"8.1":{"status":"committed","commit_sha":"worker-pack-8-1-sha"},"8.2":{"status":"committed","commit_sha":"worker-pack-8-2-sha"}}}}}
EOF
OUT=$(run_hook "008" "8.2")
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  FAIL: G) worker self-complete should not allow review dispatch before return handler (actual: $OUT)"
  fail=$((fail + 1))
else
  echo "  PASS: G) worker self-complete does not emit Dispatch Review NEXT"
  pass=$((pass + 1))
fi
if echo "$OUT" | grep -q "still in session"; then
  echo "  PASS: G) worker without return-handler marker still emits still-in-session warning"
  pass=$((pass + 1))
else
  echo "  FAIL: G) worker without return-handler marker should still emit wait warning (actual: $OUT)"
  fail=$((fail + 1))
fi

# Case H: return-handler marker is the durable final signal; retained worker_agent_id
# is now only a resumable owner and may dispatch review.
cat > "$BUDGET_DIR/execution-state-${RUN_ID}.json" <<EOF
{"run_id":"$RUN_ID","plans":{"009":{"worker_agent_id":"worker-done","worker_verdict":"pass","finished_at":"2026-06-17T00:00:00Z","return_handler_completed_at":"2026-06-17T00:00:01Z","packs":{"9.1":{"status":"committed","commit_sha":"worker-pack-9-1-sha"},"9.2":{"status":"committed","commit_sha":"worker-pack-9-2-sha"}}}}}
EOF
OUT=$(run_hook "009" "9.2")
if echo "$OUT" | grep -q "Dispatch Plan Implementation Review"; then
  echo "  PASS: H) return-handler marker allows Dispatch Review NEXT"
  pass=$((pass + 1))
else
  echo "  FAIL: H) return-handler marker should allow review dispatch (actual: $OUT)"
  fail=$((fail + 1))
fi
if echo "$OUT" | grep -q "still in session"; then
  echo "  FAIL: H) return-handler marker must not be reported as still in session (actual: $OUT)"
  fail=$((fail + 1))
else
  echo "  PASS: H) returned worker no longer emits still-in-session warning"
  pass=$((pass + 1))
fi

echo ""
echo "Result: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
