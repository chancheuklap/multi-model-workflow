#!/usr/bin/env bash
# UserPromptSubmit 相位锚(Droid 原生):在管任务 worktree 内,每轮用户输入注入一行锚,
# 防长会话 / context 压缩后流程位置蒸发。非在管目录零输出,不打扰简单问答;失败静默降级不阻塞输入。
set -euo pipefail
cat >/dev/null 2>&1 || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"

top="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"
man="$top/$STATE_SUBDIR/task.json"
[ -f "$man" ] || exit 0

jq -r '(.attendance // "afk") as $mode |
  "[mmw ⚓ \(.slug) phase=\(.phase) status=\(.status) mode=\($mode)] 按本 phase 的 load/do 干;换步 / 交接 / 不确定位置先跑 mmw where,不凭记忆跳步。"' \
  "$man" 2>/dev/null || true
exit 0
