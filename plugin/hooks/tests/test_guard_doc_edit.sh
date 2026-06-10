#!/usr/bin/env bash
# B2/B3: guard-doc-edit 四规则路径守卫 + per-plan marker
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GUARD="$SCRIPT_DIR/../guard-doc-edit.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT
mkdir -p "$FIXTURE_DIR/.claude/multi-model-workflow"
mkdir -p "$FIXTURE_DIR/docs/orchestrate/plans" "$FIXTURE_DIR/src"
WT="$FIXTURE_DIR/.claude/worktrees/plan-001"
mkdir -p "$WT/src" "$WT/docs"

pass=0; fail=0
# guard 在 fixture 目录里执行（hook cwd = 项目根）
invoke() { # $1=file_path → exit code
  local fp="$1"
  (cd "$FIXTURE_DIR" && echo "{\"tool_input\":{\"file_path\":\"$fp\"}}" | bash "$GUARD")
}
run_allow() { local name="$1" fp="$2"; if invoke "$fp" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_block() { local name="$1" fp="$2"; if invoke "$fp" >/dev/null 2>&1; then echo "  FAIL: $name (expected block)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

echo "=== test_guard_doc_edit.sh ==="

# --- 无 marker：Coordinator 自由 ---
run_allow "no marker → docs/ edit allowed (Coordinator)" "$FIXTURE_DIR/docs/orchestrate/plans/p.md"
run_allow "no marker → main-tree src edit allowed" "$FIXTURE_DIR/src/app.py"

# --- 飞行中（per-plan marker，内容=worktree 路径）---
echo "$WT" > "$FIXTURE_DIR/.claude/multi-model-workflow/worker-active-001"

run_block "rule① docs/ blocked in main tree" "$FIXTURE_DIR/docs/orchestrate/plans/p.md"
run_block "rule① docs/ blocked even inside worktree" "$WT/docs/design.md"
run_allow "rule② control plane allowed (plan-returns)" "$FIXTURE_DIR/.claude/multi-model-workflow/plan-returns/r/001/plan-return.json"
run_allow "rule③ registered worktree src allowed" "$WT/src/app.py"
run_block "rule④ main tree src read-only during flight" "$FIXTURE_DIR/src/app.py"
run_allow "outside main tree allowed (/tmp scratch)" "/tmp/scratch-$$.txt"
run_allow "relative path in control plane allowed" ".claude/multi-model-workflow/open-items.json"
run_block "relative path main-tree src blocked" "src/app.py"

# --- 多 marker：第二个 Worker 的 worktree 同样放行；删一个 marker 不影响另一个 ---
WT2="$FIXTURE_DIR/.claude/worktrees/plan-002"
mkdir -p "$WT2/src"
echo "$WT2" > "$FIXTURE_DIR/.claude/multi-model-workflow/worker-active-002"
run_allow "second registered worktree allowed" "$WT2/src/mod.py"
rm "$FIXTURE_DIR/.claude/multi-model-workflow/worker-active-001"
run_allow "after 001 marker removed, 002 worktree still allowed" "$WT2/src/mod.py"
run_block "after 001 marker removed, flight still on (002) → main tree still read-only" "$FIXTURE_DIR/src/app.py"
rm "$FIXTURE_DIR/.claude/multi-model-workflow/worker-active-002"
run_allow "all markers gone → main tree writable again" "$FIXTURE_DIR/src/app.py"

# --- 串行退化：marker 内容=主树路径 → 主树源码放行（与旧行为等价），docs 仍拦 ---
echo "$FIXTURE_DIR" > "$FIXTURE_DIR/.claude/multi-model-workflow/worker-active-001"
run_allow "serial mode (worktree=main tree) → src allowed" "$FIXTURE_DIR/src/app.py"
run_block "serial mode → docs/ still blocked" "$FIXTURE_DIR/docs/x.md"

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
