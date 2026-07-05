#!/usr/bin/env bash
# SessionStart 分诊:每个会话开头注入一次路由指令——正式开发任务进 orchestrate 流程,
# 简单问答给离开窗口(直接答,不进流程)。顺带注入断点恢复入口:
#   - 在管任务 worktree 内 → 报"你在哪、怎么续"
#   - 主仓库有在飞任务 → 逐行列出(界定=有 plugin manifest 的 worktree,不是野分支)
# 非 git 目录 / 无关仓库静默退出,不注入不报错。
set -euo pipefail

cat >/dev/null 2>&1 || true   # 吞 stdin payload(本 hook 不需要字段)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MMW="bash \"$SCRIPT_DIR/../scripts/mmw.sh\""
STATE_SUBDIR=".claude/multi-model-workflow"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

man="$top/$STATE_SUBDIR/task.json"
if [ -f "$man" ]; then
  # 在管任务 worktree 内:报身份 + 续跑入口
  jq -r --arg mmw "$MMW" '"[multi-model-workflow] 本目录是在管任务 worktree:\(.slug) [\(.scenario)] phase=\(.phase) status=\(.status)。要续这个任务:先跑 \($mmw) where,照它报的 load/do 续;与任务无关的简单问答直接答。"' "$man" 2>/dev/null || true
  exit 0
fi

echo "[multi-model-workflow] 会话分诊:正式开发任务(新功能/改造/报 bug/明确小改/合并 worktree)→ 用 orchestrate skill 进流程(先跑 $MMW where);简单问答/概念问题/一次性查询 → 直接答,不进流程(离开窗口)。"
hdr=0
for d in "$top/.claude/worktrees"/*/; do
  mm="$d$STATE_SUBDIR/task.json"
  [ -f "$mm" ] || continue
  [ "$hdr" = 1 ] || { echo "在飞任务(续跑:EnterWorktree({ path }) 后 mmw where;全量视图 mmw task team):"; hdr=1; }
  jq -r '"  - \(.slug)  [\(.scenario)] phase=\(.phase) status=\(.status)  path=\(.worktree_path)"' "$mm" 2>/dev/null || true
done
exit 0
