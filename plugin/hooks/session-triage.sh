#!/usr/bin/env bash
# SessionStart 分诊(Claude / Droid 双宿主)
set -euo pipefail
cat >/dev/null 2>&1 || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/host.sh
. "$SCRIPT_DIR/../scripts/lib/host.sh"
MMW="bash \"$SCRIPT_DIR/../scripts/mmw.sh\""
HOST="$(mmw_host)"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"

man="$top/$STATE_SUBDIR/task.json"
if [ -f "$man" ]; then
  # 在管任务 worktree 内:报身份 + 值守档 + 宿主续跑入口 + 指挥入口
  # 值守档权威在 task.json.attendance(缺省 afk);unattended 时提示续跑先读盘 mode 自我约束(不问人)。
  hint="$(mmw_enter_worktree_hint "$(jq -r .worktree_path "$man" 2>/dev/null || echo "$top")")"
  jq -r --arg mmw "$MMW" --arg host "$HOST" --arg hint "$hint" '
    (.attendance // "afk") as $mode |
    "[multi-model-workflow] host=\($host) 本目录是在管任务 worktree:\(.slug) [\(.scenario)] phase=\(.phase) status=\(.status) mode=\($mode)。" +
    "续跑:\($hint);先跑 \($mmw) where,照它报的 load/do 续。板:/progress  指挥:/reassess /attended /unattended /side-finding。" +
    (if $mode=="unattended" then "  ⚠ 强无人档:续跑按盘上 mode 自我约束,不向用户提问,遇硬停写板等人。" else "" end) +
    "  与任务无关的简单问答直接答。"' "$man" 2>/dev/null || true
  exit 0
fi

echo "[multi-model-workflow] host=$HOST 会话分诊:正式开发任务(新功能/改造/报 bug/明确小改/合并 worktree)→ 用 orchestrate skill 进流程(先跑 $MMW where);简单问答 → 直接答,不进流程。"
hdr=0
while IFS= read -r mm; do
  [ -f "$mm" ] || continue
  [ "$hdr" = 1 ] || { echo "在飞任务(续跑:进对应 worktree 后 mmw where;全量视图 mmw task team):"; hdr=1; }
  jq -r '"  - \(.slug)  [\(.scenario)] phase=\(.phase) status=\(.status)  path=\(.worktree_path)"' "$mm" 2>/dev/null || true
done < <(mmw_foreach_flying_manifest "$top")
exit 0
