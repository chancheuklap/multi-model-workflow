#!/usr/bin/env bash
# progress.sh —— 负责人可读进度板(投影,非真相源)
#
# 从 task.json(外层真相)+ loop-state.json(内层 loop,可能不存在)聚合出一份
# <worktree>/<host-state>/progress-board.md,给负责人一眼扫。
# 板永远可从真相源重建;冲突以 task.json / loop-state.json 为准。
#
#   render [--stdout]   重渲染并覆盖 board;--stdout 额外把板全文打到 stdout(供 command 的 `!` 动态注入)
#
# 无在管任务(无 task.json)→ 打 NO-ACTIVE-RUN 退 0,不伪造状态(fail-visible)。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
die() { echo "ERROR: $*" >&2; exit 1; }

top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"
MAN="$top/$STATE_SUBDIR/task.json"
LOOP="$top/$STATE_SUBDIR/loop-state.json"
BOARD="$top/$STATE_SUBDIR/progress-board.md"

stdout=false
case "${2:-}" in --stdout) stdout=true;; "") ;; *) die "未知参数 ${2:-}";; esac
[ "${1:-render}" = "render" ] || die "用法 progress render [--stdout]"

if [ ! -f "$MAN" ]; then
  echo "NO-ACTIVE-RUN(无 task.json:当前不在在管任务 worktree,无板可渲染)"
  exit 0
fi
jq -e . "$MAN" >/dev/null 2>&1 || die "task.json 损坏:$MAN"

# ---- 从 task.json 取外层事实 ----
slug=$(jq -r '.slug // "?"' "$MAN")
scenario=$(jq -r '.scenario // "?"' "$MAN")
phase=$(jq -r '.phase // "?"' "$MAN")
status=$(jq -r '.status // "?"' "$MAN")
mode=$(jq -r '.attendance // "afk"' "$MAN")
repair=$(jq -r '.repair_count // 0' "$MAN")
# 设计确认(唯一人闸)状态:来自 task.json.approval(mmw approve 写入)
approval_line="未确认"
if jq -e '.approval' "$MAN" >/dev/null 2>&1; then
  approval_line="已确认 $(jq -r '.approval.at // "?"' "$MAN")  reports=$(jq -rc '.approval.reports // []' "$MAN")"
fi
prototype_line="- Prototype：未启动"
prototype_status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$MAN")"
if [ "$prototype_status" = BROKEN ]; then
  prototype_line="- Prototype：**BROKEN** · task.json.prototype 缺 status"
elif [ -n "$prototype_status" ]; then
  prototype_line="- Prototype：**${prototype_status}** · 第 $(jq -r '.prototype.iteration' "$MAN") 轮 · $(jq -r '.prototype.log' "$MAN")"
fi

# ---- 从 loop-state 取内层事实(可能无执行账本) ----
loop_line="(当前无执行账本)"
budget_line="—"
plan_rows=""
blocked_rows=""
if [ -f "$LOOP" ] && jq -e . "$LOOP" >/dev/null 2>&1; then
  loop_line="loop=execution"
  budget_line="$(bash "$SCRIPT_DIR/loop.sh" status 2>/dev/null || echo "?")"
  # 计划进度:执行账本的 steps = plan/pack
  plan_rows=$(jq -r '.steps[]? | "| \(.plan // .id) | \(.status) | \(.id) | — | \(.desc) |"' "$LOOP")
  # 阻塞:pause 非空
  if [ "$(jq -r '.pause' "$LOOP")" != "null" ]; then
    blocked_rows="- **PAUSE**: $(jq -r '.pause.kind' "$LOOP")/$(jq -r '.pause.reason // "-"' "$LOOP") — $(jq -r '.pause.question' "$LOOP")"$'\n'
  fi
fi
[ -n "$plan_rows" ] || plan_rows="| — | — | — | — | 无落地步 |"

# task 级阻塞
case "$status" in
  blocked)      blocked_rows="${blocked_rows}- 任务 status=blocked"$'\n' ;;
  waiting-user) blocked_rows="${blocked_rows}- 任务 status=waiting-user(等用户拍板)"$'\n' ;;
esac
[ "$repair" -gt 0 ] && blocked_rows="${blocked_rows}- 当前阶段已返工 $repair 次"$'\n'
[ -n "$blocked_rows" ] || blocked_rows="- 无"

# ---- 计划外项:open_items(带 disposition) ----
side_rows=$(jq -r '
  .open_items | to_entries[]? |
  "| \(.key) | \(.value.tag) | \(.value.finding) | \(.value.disposition // "未分流") | \(if .value.disposition=="defer_issue" then "issue/open_items" elif .value.disposition=="fix_now" then "当前修复范围" else "—" end) |"
' "$MAN")
[ -n "$side_rows" ] || side_rows="| — | — | 无计划外项 | — | — |"

# ---- 组板 ----
board="$(cat <<EOF
# Progress Board · ${slug}

> 投影,非真相源。以 task.json / loop-state.json 为准,可用 \`mmw progress render\` 重建。

## 现在
- 路线 / 阶段：${scenario} / ${phase}（status=${status}）
- 值守模式：**${mode}**
- 进度度量：${budget_line}
- 当前动作：${loop_line}

## 设计确认
- approval：**${approval_line}**
${prototype_line}

## 计划进度
| Plan | 状态 | Pack | Review | 备注 |
| --- | --- | --- | --- | --- |
${plan_rows}

## 阻塞与待决
${blocked_rows}
## 计划外项
| # | 标签 | 摘要 | 选择 | 去向 |
| --- | --- | --- | --- | --- |
${side_rows}

## 下一步
- 跑 \`mmw where\` 看当前阶段 load/do
- 指挥入口：/progress /reassess /attended /unattended /side-finding
EOF
)"

# 原子写 + fail-closed:非空才落盘,不把板截空
tmp="$(mktemp)"; printf '%s\n' "$board" > "$tmp"
[ -s "$tmp" ] || { rm -f "$tmp"; die "板渲染为空,拒写,保留旧板"; }
mkdir -p "$top/$STATE_SUBDIR"
mv "$tmp" "$BOARD"

if $stdout; then
  cat "$BOARD"
else
  echo "RENDERED $BOARD"
fi
