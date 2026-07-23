#!/usr/bin/env bash
# SessionStart 分诊(Claude Code)
# 在管任务 worktree:三源回报(书签注记 + 最近提交流水 + 待拍板指引)+ 新鲜度(版本/时效)。
# 会话开头与 compaction 恢复各注入一次;不逐条消息注锚。
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
  # 身份 + 值守档
  jq -r --arg mmw "$MMW" '
    (.attendance // "attended") as $mode |
    "[multi-model-workflow] 在管任务 worktree:\(.slug) [\(.scenario)] phase=\(.phase) status=\(.status) mode=\($mode)。" +
    (if $mode=="unattended" then "  ⚠ 强无人档(用户显式进入):不向用户提问,遇硬停写板等人;用户回来发任意消息即恢复 attended。" else "" end)' \
    "$man" 2>/dev/null || true

  # 三源回报:①最近提交流水(上次做了什么)
  base="$(jq -r '.base_commit // ""' "$man" 2>/dev/null || echo "")"
  if [ -n "$base" ]; then
    recent="$(git -C "$top" log --format='%s' "$base"..HEAD 2>/dev/null | head -3 | paste -sd ' · ' - || true)"
    [ -n "$recent" ] && echo "上次做了:$recent"
  fi
  # ②书签注记(agent 记的一句话现场)
  note="$(jq -r '.note.text // empty' "$man" 2>/dev/null || true)"
  [ -n "$note" ] && echo "现场注记:$note"
  # prototype 内层断点来自 manifest；不靠聊天记忆或 agent 自己搜索。
  prototype_status="$(jq -r '.prototype.status // empty' "$man" 2>/dev/null || true)"
  if [ -n "$prototype_status" ]; then
    echo "prototype:${prototype_status} 第 $(jq -r '.prototype.iteration' "$man") 轮 log=$top/$(jq -r '.prototype.log' "$man")"
  fi
  # ③待拍板:设计文档 Open Decisions 节(存在才提)
  ddoc="$(jq -r '.docs.design // empty' "$man" 2>/dev/null || true)"
  if [ -n "$ddoc" ]; then
    for cand in "$top/$ddoc.md" "$top/$ddoc/$(basename "$ddoc").md"; do
      if [ -f "$cand" ] && grep -q '^#\{1,3\} *Open Decisions' "$cand" 2>/dev/null; then
        echo "待拍板:读 ${cand#$top/} 的 Open Decisions 节(未拍板项都在那)"
        break
      fi
    done
  fi

  # 新鲜度(白名单第 3 条):版本/时效不对先对表
  cur_ver="$(jq -r '.version // ""' "$SCRIPT_DIR/../.claude-plugin/plugin.json" 2>/dev/null || echo "")"
  man_ver="$(jq -r '.plugin_version // ""' "$man" 2>/dev/null || echo "")"
  if [ -n "$man_ver" ] && [ -n "$cur_ver" ] && [ "$man_ver" != "$cur_ver" ]; then
    echo "⚠ 状态由旧版 plugin($man_ver,当前 $cur_ver)写入:先 /reassess 从磁盘对表再续,别把旧指令当最新。"
  fi
  upd="$(jq -r '.updated_at // .created_at // ""' "$man" 2>/dev/null || echo "")"
  if [ -n "$upd" ]; then
    then_s="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$upd" +%s 2>/dev/null || date -u -d "$upd" +%s 2>/dev/null || echo "")"
    if [ -n "$then_s" ]; then
      age_d=$(( ($(date -u +%s) - then_s) / 86400 ))
      [ "$age_d" -ge 7 ] && echo "⚠ 状态已 ${age_d} 天没动:先 /reassess 重建真相再续。"
    fi
  fi

  echo "续跑:先跑 $MMW where,照它报的 load/do 续(接着聊就接着聊,位置只是书签不是命令)。板:/progress  指挥:/reassess /rescope /attended /unattended /approve-design。与任务无关的问答直接处理;无关写操作不要在此 worktree 执行。"
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
