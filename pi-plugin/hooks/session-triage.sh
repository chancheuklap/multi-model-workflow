#!/usr/bin/env bash
# pi 会话分诊:只在在管任务 worktree 回报书签、最近提交、待拍板与状态新鲜度；未在管仓库静默。
# extensions/mmw-hooks.ts 在会话开头与 compaction 后经 before_agent_start 注入一次。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"
MMW="bash \"$SCRIPT_DIR/../scripts/mmw.sh\""

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"

man="$top/$STATE_SUBDIR/task.json"
if [ -f "$man" ]; then
  # 身份 + 值守档
  jq -r --arg mmw "$MMW" '
    (.attendance // "attended") as $mode |
    "[multi-model-workflow-pi] 在管任务 worktree: slug=\(.slug) scenario=\(.scenario) phase=\(.phase) status=\(.status) mode=\($mode)。" +
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
  prototype_status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$man" 2>/dev/null || true)"
  if [ "$prototype_status" = BROKEN ]; then
    echo "prototype:BROKEN task.json.prototype 缺 status"
  elif [ -n "$prototype_status" ]; then
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
  cur_ver="$(jq -r '.version // ""' "$SCRIPT_DIR/../package.json" 2>/dev/null || echo "")"
  man_ver="$(jq -r '.plugin_version // ""' "$man" 2>/dev/null || echo "")"
  if [ -n "$man_ver" ] && [ -n "$cur_ver" ] && [ "$man_ver" != "$cur_ver" ]; then
    echo "⚠ 状态由旧版 plugin($man_ver,当前 $cur_ver)写入:先 /reassess 从磁盘对表再续,别把旧指令当最新。"
  fi
  upd="$(jq -r '.updated_at // .created_at // ""' "$man" 2>/dev/null || echo "")"
  if [ -n "$upd" ]; then
    then_s="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$upd" +%s 2>/dev/null || date -u -d "$upd" +%s 2>/dev/null || echo "")"
    if [ -n "$then_s" ]; then
      age_d=$(( ($(date -u +%s) - then_s) / 86400 ))
      if [ "$age_d" -ge 7 ]; then echo "⚠ 状态已 ${age_d} 天没动:先 /reassess 重建真相再续。"; fi
    fi
  fi

  echo "续跑:先跑 $MMW where,照它报的 load/do 续(接着聊就接着聊,位置只是书签不是命令)。板:/progress  指挥:/reassess /rescope /attended /unattended /approve-design。与任务无关的问答直接处理;无关写操作不要在此 worktree 执行。"
  exit 0
fi

# 未在管仓库默认直接处理；只有 agent 主动选择 MMW 或用户明确续跑时才执行 mmw where。
exit 0
