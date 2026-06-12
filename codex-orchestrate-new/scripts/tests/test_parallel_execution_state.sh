#!/usr/bin/env bash
# B1/B3/B5/C4: dep-batches 批次计算 + active_plan_ids 生命周期 + 失败隔离 + session 记账
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/../state.sh"
FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
export STATE_BASE="$FIXTURE_DIR"

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected non-zero)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

echo "=== test_parallel_execution_state.sh ==="

RUN_ID="test-par"

# --- B1: dep-batches ---
PLANS_DIR="$FIXTURE_DIR/plans"
mkdir -p "$PLANS_DIR"
cat > "$PLANS_DIR/001-alpha.md" <<'EOF'
# Alpha Implementation Plan
**Blocked by:** None
EOF
cat > "$PLANS_DIR/002-beta.md" <<'EOF'
# Beta Implementation Plan
**Blocked by:** Plan 001
EOF
cat > "$PLANS_DIR/003-gamma.md" <<'EOF'
# Gamma Implementation Plan
**Blocked by:** None
EOF

run_test "no-dep plans land in level 0 together, dependent in level 1" \
  bash -c "[[ \$(bash '$STATE_SH' dep-batches --run-id '$RUN_ID' --plans-dir '$PLANS_DIR' | jq -c '.levels') == '[[\"001\",\"003\"],[\"002\"]]' ]]"

# 单 Plan 退化
SOLO_DIR="$FIXTURE_DIR/solo"; mkdir -p "$SOLO_DIR"
cp "$PLANS_DIR/001-alpha.md" "$SOLO_DIR/001-alpha.md"
run_test "single plan degenerates to one level" \
  bash -c "[[ \$(bash '$STATE_SH' dep-batches --run-id '$RUN_ID' --plans-dir '$SOLO_DIR' | jq -c '.levels') == '[[\"001\"]]' ]]"

# 非 plan 编号值 → 报错不猜测
BAD_DIR="$FIXTURE_DIR/bad"; mkdir -p "$BAD_DIR"
cat > "$BAD_DIR/001-x.md" <<'EOF'
**Blocked by:** issue-007
EOF
run_test_expect_fail "non-plan-id Blocked-by token rejected (no guessing)" \
  bash "$STATE_SH" dep-batches --run-id "$RUN_ID" --plans-dir "$BAD_DIR"

# 环 → 报错
CYC_DIR="$FIXTURE_DIR/cyc"; mkdir -p "$CYC_DIR"
printf '**Blocked by:** 002\n' > "$CYC_DIR/001-a.md"
printf '**Blocked by:** 001\n' > "$CYC_DIR/002-b.md"
run_test_expect_fail "dependency cycle rejected" \
  bash "$STATE_SH" dep-batches --run-id "$RUN_ID" --plans-dir "$CYC_DIR"

# --- B3: active_plan_ids 生命周期 ---
ESF="$FIXTURE_DIR/execution-state-${RUN_ID}.json"
cat > "$ESF" <<'EOF'
{
  "run_id": "test-par",
  "plans": {
    "001": { "status": "pending", "packs": { "1.1": { "status": "pending" } } },
    "002": { "status": "pending", "packs": { "2.1": { "status": "pending" } } },
    "003": { "status": "pending", "packs": { "3.1": { "status": "pending" } } }
  }
}
EOF

bash "$STATE_SH" execution-plan start --run-id "$RUN_ID" --plan-id 001 --start-commit aaa111 \
  --worktree-path /tmp/wt-001 --branch plan-001 >/dev/null
bash "$STATE_SH" execution-plan start --run-id "$RUN_ID" --plan-id 003 --start-commit aaa111 \
  --worktree-path /tmp/wt-003 --branch plan-003 >/dev/null

run_test "two parallel starts → active_plan_ids has both" \
  bash -c "[[ \$(jq -c '.active_plan_ids' '$ESF') == '[\"001\",\"003\"]' ]]"
run_test "worktree_path / branch / isolation_status=active recorded" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].worktree_path + \"|\" + .plans[\"001\"].branch + \"|\" + .plans[\"001\"].isolation_status' '$ESF') == '/tmp/wt-001|plan-001|active' ]]"
run_test "current_plan_id no longer written (deleted, no compat)" \
  bash -c "[[ \$(jq 'has(\"current_plan_id\")' '$ESF') == 'false' ]]"

# 终态前各自挂一个 worker-active marker（guard-doc-edit 据此拦 docs/ 编辑）
echo /tmp/wt-001 > "$FIXTURE_DIR/worker-active-001"
echo /tmp/wt-003 > "$FIXTURE_DIR/worker-active-003"

# B5: 003 失败隔离 → 不影响 001 在飞
bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id 003 --status isolated >/dev/null
run_test "isolated plan removed from active, marked isolated" \
  bash -c "[[ \$(jq -c '.active_plan_ids' '$ESF') == '[\"001\"]' && \$(jq -r '.plans[\"003\"].isolation_status' '$ESF') == 'isolated' ]]"
run_test "other in-flight plan untouched by isolation" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].status' '$ESF') == 'in_progress' ]]"
run_test "isolated 终态清除 003 的 worker-active marker（guard 放行 docs）" \
  bash -c "[[ ! -f '$FIXTURE_DIR/worker-active-003' ]]"
run_test "001 仍在飞 → 其 marker 不被 003 隔离误删" \
  bash -c "[[ -f '$FIXTURE_DIR/worker-active-001' ]]"

# 001 完成 → active 清空；B6 回收后标 merged
bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id 001 --status completed >/dev/null
run_test "completed plan removed from active" \
  bash -c "[[ \$(jq -c '.active_plan_ids' '$ESF') == '[]' && \$(jq -r '.plans[\"001\"].status' '$ESF') == 'completed' ]]"
run_test "completed 终态清除 001 的 worker-active marker" \
  bash -c "[[ ! -f '$FIXTURE_DIR/worker-active-001' ]]"
bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id 001 --status merged >/dev/null
run_test "merged marks isolation_status=merged" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].isolation_status' '$ESF') == 'merged' ]]"

# C4: session 记账
bash "$STATE_SH" execution-plan session --run-id "$RUN_ID" --plan-id 002 --session-id sess-abc123 >/dev/null
run_test "codex session_id recorded per plan" \
  bash -c "[[ \$(jq -r '.plans[\"002\"].session_id' '$ESF') == 'sess-abc123' ]]"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
