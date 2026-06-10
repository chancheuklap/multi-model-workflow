#!/usr/bin/env bash
# B6/C6: 并行 Plan 轻量回收 —— 按依赖顺序逐个调用本脚本合并 plan 分支回 Coordinator 分支。
#
# 步骤（全机械，按序）：
#   1. C6 docs 守卫：start_commit..<branch> 的 diff 触碰 docs/ → 拒绝合并，
#      该 Plan 标 isolated（Worker 禁改 docs；Codex 不经 Claude hook，此处兜底）
#   2. git merge --no-ff <branch>（冲突 → 中止合并并提示走 multi-pr-merge 借鉴的
#      冲突发现/RCA 方法论，不自动解决）
#   3. execution-plan finish --status merged（isolation_status=merged）
#   4. git worktree remove + 删除分支 + 清 per-plan marker
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_SH="$SCRIPT_DIR/state.sh"
STATE_BASE="${STATE_BASE:-.claude/multi-model-workflow}"

RUN_ID="" PLAN_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --plan-id) PLAN_ID="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$RUN_ID" || -z "$PLAN_ID" ]]; then
  echo "Usage: recycle-plan.sh --run-id <id> --plan-id <NNN>" >&2
  exit 2
fi

ESF="$STATE_BASE/execution-state-${RUN_ID}.json"
if [[ ! -f "$ESF" ]]; then
  echo "Error: execution-state not found: $ESF" >&2; exit 2
fi

BRANCH=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].branch // empty' "$ESF")
WORKTREE=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].worktree_path // empty' "$ESF")
START=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].start_commit // empty' "$ESF")
STATUS=$(jq -r --arg pid "$PLAN_ID" '.plans[$pid].status // empty' "$ESF")

if [[ -z "$BRANCH" ]]; then
  echo "Error: plan $PLAN_ID has no branch recorded (serial run? nothing to recycle)" >&2
  exit 2
fi
if [[ "$STATUS" != "completed" ]]; then
  echo "Error: plan $PLAN_ID status='$STATUS'，只回收 completed（Plan Implementation Review 通过）的 Plan" >&2
  exit 2
fi

# 1. C6 docs 守卫(安全边界,fail-closed)
if [[ -n "$START" ]]; then
  # 分离退出码与输出:git diff 失败(START/BRANCH ref 异常)= 无法核验 = 拒绝合并。
  # 不能用 `|| true` 把"验不了"误当成"没碰 docs"而放行——那会让带 docs 改动的分支被合并。
  if ! DOCS_TOUCHED=$(git diff --name-only "$START" "$BRANCH" -- docs/ 2>&1); then
    echo "[multi-model-workflow] BLOCKED: plan $PLAN_ID docs 守卫无法核验（git diff 失败，ref 异常）：" >&2
    echo "$DOCS_TOUCHED" >&2
    bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id "$PLAN_ID" --status isolated
    echo "已标 isolated；人工裁决后再处理。" >&2
    exit 2
  fi
  if [[ -n "$DOCS_TOUCHED" ]]; then
    echo "[multi-model-workflow] BLOCKED: plan $PLAN_ID 分支触碰了 docs/（Worker 禁区）：" >&2
    echo "$DOCS_TOUCHED" >&2
    bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id "$PLAN_ID" --status isolated
    echo "已标 isolated；人工裁决 docs 改动后再处理。" >&2
    exit 2
  fi
fi

# 2. 合并（冲突不自动解决）
if ! git merge --no-ff "$BRANCH" -m "merge(plan-${PLAN_ID}): 回收并行 Plan ${PLAN_ID}（${BRANCH}）"; then
  git merge --abort 2>/dev/null || true
  echo "[multi-model-workflow] BLOCKED: plan $PLAN_ID 合并冲突。按 B6：派 explorer 做冲突发现；系统性冲突走 root-cause-analyst（借鉴 multi-pr-merge 方法论，不套整套）。冲突期间不影响已合并 Plan。" >&2
  exit 2
fi

# 3. 状态收口
bash "$STATE_SH" execution-plan finish --run-id "$RUN_ID" --plan-id "$PLAN_ID" --status merged

# 4. 清理
if [[ -n "$WORKTREE" && -d "$WORKTREE" ]]; then
  git worktree remove "$WORKTREE" --force 2>/dev/null || \
    echo "Warning: worktree remove failed for $WORKTREE（手工清理）" >&2
fi
git branch -d "$BRANCH" 2>/dev/null || \
  echo "Warning: branch $BRANCH not deleted（未完全合并？人工确认）" >&2
rm -f "$STATE_BASE/worker-active-${PLAN_ID}"

echo "[multi-model-workflow] RECYCLED: plan $PLAN_ID merged via --no-ff, worktree cleaned, marker removed."
