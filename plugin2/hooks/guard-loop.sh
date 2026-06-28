#!/usr/bin/env bash
# SubagentStop 看守:落地/审 loop 没做完不让帮手停下。
# 读 loop-state → exit-check;NOT-DONE → exit 2 顶回去续;DONE/PAUSED → 放停。
# 只在有 loop-state 时生效(普通 subagent 无 state 直接放行)。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/../scripts/loop.sh"

cat >/dev/null 2>&1 || true   # 吞掉 stdin payload(本 hook 不需要它的字段)

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
f="$top/.claude/multi-model-workflow/loop-state.json"
[ -f "$f" ] || exit 0

res="$(cd "$top" && bash "$LOOP" exit-check 2>/dev/null)" || exit 0
case "$res" in
  DONE|PAUSED:*) exit 0 ;;                                  # 放它停
  NOT-DONE:*) echo "内层未完成($res),做完再停。" >&2; exit 2 ;;   # 顶回去续
  *) exit 0 ;;
esac
