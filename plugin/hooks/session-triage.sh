#!/usr/bin/env bash
# SessionStart 分诊(Claude Code)
set -euo pipefail
cat >/dev/null 2>&1 || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"
MMW="bash \"$SCRIPT_DIR/../scripts/mmw.sh\""

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$MMW_STATE_SUBDIR"

man="$top/$STATE_SUBDIR/task.json"
if [ -f "$man" ]; then
  # 在管任务 worktree 内:报身份 + 值守档 + 续跑入口 + 指挥入口
  # 值守档权威在 task.json.attendance(缺省 afk);unattended 时提示续跑先读盘 mode 自我约束(不问人)。
  hint="EnterWorktree({ path: \"$(jq -r .worktree_path "$man" 2>/dev/null || echo "$top")\" }) 然后 mmw where"
  jq -r --arg mmw "$MMW" --arg hint "$hint" '
    (.attendance // "afk") as $mode |
    "[multi-model-workflow] 本目录是在管任务 worktree:\(.slug) [\(.scenario)] phase=\(.phase) status=\(.status) mode=\($mode)。" +
    "续跑:\($hint);先跑 \($mmw) where,照它报的 load/do 续。板:/progress  指挥:/reassess /attended /unattended /side-finding。" +
    (if $mode=="unattended" then "  ⚠ 强无人档:续跑按盘上 mode 自我约束,不向用户提问,遇硬停写板等人。" else "" end) +
    "  与任务无关的问答、解释和只读查看直接处理;无关写操作不要在此 worktree 执行。"' "$man" 2>/dev/null || true
  exit 0
fi

echo "[multi-model-workflow] 会话分诊:需正式编排的开发任务(新功能/系统改造/根因不明的 bug/需独立任务边界的小改/合并 worktree)→ 用 orchestrate skill 进流程(先跑 $MMW where);问答、解释、只读查看和主线程可直接完成并验证的琐碎单步动作 → 直接处理,不进流程。"
hdr=0
for d in "$top/$MMW_WORKTREES_REL"/*/; do
  [ -d "$d" ] || continue
  mm="${d}${MMW_STATE_SUBDIR}/task.json"
  [ -f "$mm" ] || continue
  [ "$hdr" = 1 ] || { echo "在飞任务(续跑:进对应 worktree 后 mmw where;全量视图 mmw task team):"; hdr=1; }
  jq -r '"  - \(.slug)  [\(.scenario)] phase=\(.phase) status=\(.status)  path=\(.worktree_path)"' "$mm" 2>/dev/null || true
done
exit 0
