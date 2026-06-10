#!/usr/bin/env bash
# B6/C6: recycle-plan.sh —— 真实 git 仓库夹具：依赖序合并、docs 守卫、冲突拒绝、清理
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RECYCLE="$PLUGIN_DIR/scripts/recycle-plan.sh"
STATE_SH="$PLUGIN_DIR/scripts/state.sh"

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

pass=0; fail=0
run_test() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  PASS: $name"; pass=$((pass+1)); else echo "  FAIL: $name"; fail=$((fail+1)); fi; }
run_test_expect_fail() { local name="$1"; shift; if "$@" >/dev/null 2>&1; then echo "  FAIL: $name (expected non-zero)"; fail=$((fail+1)); else echo "  PASS: $name"; pass=$((pass+1)); fi; }

echo "=== test_recycle_plan.sh ==="

RUN_ID="test-rc"
cd "$FIXTURE_DIR"
git init -q -b coordinator .
git config user.email t@t.local && git config user.name tester
mkdir -p src docs
echo "base" > src/base.txt
echo "design" > docs/design.md
printf '.claude/\n.wt/\n' > .gitignore
git add -A && git commit -qm "base"
BASE_SHA=$(git rev-parse HEAD)
mkdir -p .claude/multi-model-workflow
export STATE_BASE=".claude/multi-model-workflow"

mkesf() { cat > ".claude/multi-model-workflow/execution-state-${RUN_ID}.json" <<EOF
{ "run_id": "$RUN_ID", "plans": $1 }
EOF
}

# --- Plan 001：干净合并路径 ---
WT1="$FIXTURE_DIR/.wt/plan-001"
git worktree add -q -b plan-001 "$WT1" HEAD
( cd "$WT1" && echo "feat-001" > src/f1.txt && git add -A && git commit -qm "Pack 1.1: feat" )
mkesf "{ \"001\": { \"status\": \"completed\", \"start_commit\": \"$BASE_SHA\", \"branch\": \"plan-001\", \"worktree_path\": \"$WT1\", \"packs\": {} } }"
touch ".claude/multi-model-workflow/worker-active-001"

run_test "clean recycle merges --no-ff" bash "$RECYCLE" --run-id "$RUN_ID" --plan-id 001
run_test "merge commit is no-ff (2 parents)" \
  bash -c "[[ \$(git rev-list --parents -n1 HEAD | wc -w | tr -d ' ') == '3' ]]"
run_test "merged file landed on coordinator branch" bash -c "[[ -f src/f1.txt ]]"
run_test "isolation_status=merged recorded" \
  bash -c "[[ \$(jq -r '.plans[\"001\"].isolation_status' '.claude/multi-model-workflow/execution-state-${RUN_ID}.json') == 'merged' ]]"
run_test "worktree removed + branch deleted + marker cleaned" \
  bash -c "[[ ! -d '$WT1' ]] && ! git show-ref -q refs/heads/plan-001 && [[ ! -f '.claude/multi-model-workflow/worker-active-001' ]]"

# --- Plan 002：触碰 docs/ → 拒绝合并并 isolated（C6 守卫）---
WT2="$FIXTURE_DIR/.wt/plan-002"
git worktree add -q -b plan-002 "$WT2" HEAD
( cd "$WT2" && echo "tamper" >> docs/design.md && echo "x" > src/f2.txt && git add -A && git commit -qm "Pack 2.1: tamper docs" )
mkesf "{ \"002\": { \"status\": \"completed\", \"start_commit\": \"$(git rev-parse HEAD)\", \"branch\": \"plan-002\", \"worktree_path\": \"$WT2\", \"packs\": {} } }"
run_test_expect_fail "docs-touching branch refused (C6 guard)" \
  bash "$RECYCLE" --run-id "$RUN_ID" --plan-id 002
run_test "refused plan marked isolated, worktree preserved" \
  bash -c "[[ \$(jq -r '.plans[\"002\"].isolation_status' '.claude/multi-model-workflow/execution-state-${RUN_ID}.json') == 'isolated' ]] && [[ -d '$WT2' ]]"
run_test "coordinator docs untouched after refusal" \
  bash -c "[[ \$(cat docs/design.md) == 'design' ]]"

# --- Plan 003：冲突 → 中止合并、不污染 ---
git worktree remove --force "$WT2" 2>/dev/null; git branch -D plan-002 -q 2>/dev/null
WT3="$FIXTURE_DIR/.wt/plan-003"
git worktree add -q -b plan-003 "$WT3" HEAD
( cd "$WT3" && echo "branch-version" > src/base.txt && git add -A && git commit -qm "Pack 3.1: conflict" )
echo "main-version" > src/base.txt && git add src/base.txt && git commit -qm "main diverges"
mkesf "{ \"003\": { \"status\": \"completed\", \"start_commit\": \"$BASE_SHA\", \"branch\": \"plan-003\", \"worktree_path\": \"$WT3\", \"packs\": {} } }"
run_test_expect_fail "merge conflict → abort, exit non-zero" \
  bash "$RECYCLE" --run-id "$RUN_ID" --plan-id 003
run_test "conflict aborted cleanly (no MERGE_HEAD, src/docs clean)" \
  bash -c "[[ ! -f .git/MERGE_HEAD ]] && [[ -z \$(git status --porcelain -- src docs) ]]"

# --- 非 completed 拒绝回收 ---
mkesf "{ \"004\": { \"status\": \"in_progress\", \"start_commit\": \"$BASE_SHA\", \"branch\": \"plan-003\", \"worktree_path\": \"$WT3\", \"packs\": {} } }"
run_test_expect_fail "non-completed plan refused" \
  bash "$RECYCLE" --run-id "$RUN_ID" --plan-id 004

echo ""
echo "Results: $pass passed, $fail failed"
[[ $fail -eq 0 ]]
