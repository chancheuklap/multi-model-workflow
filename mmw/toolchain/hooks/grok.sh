#!/usr/bin/env bash
# Grok 的 Stop 与 SubagentStop：把诊断交回模型。
#
# 触发点跟别的宿主不一样，这不是选择：Grok 的 PostToolUse 忽略 stdout，诊断在那里
# 交不回去。所以改在会话与 subagent 停下来的时候跑，用工作树里动过的文件。
#
# 返回通道也不一样：走 stdout 的 hookSpecificOutput.additionalContext，退出码一律 0。

set -uo pipefail

self="${BASH_SOURCE[0]}"
if [ -L "$self" ]; then
  target="$(readlink "$self")"
  case "$target" in
    /*) ;;
    *) target="$(dirname "$self")/$target" ;;
  esac
  self="$target"
fi
# shellcheck disable=SC1091  # 路径在运行期算出来，静态跟不进去
. "$(cd "$(dirname "$self")" && pwd -P)/core.sh"

payload="$(mmw_hook_payload)"
command -v jq >/dev/null 2>&1 || exit 0

# 同一份 hook 挂在多个事件上时，只有这两个事件该跑。
event="$(printf '%s' "$payload" | jq -r '.hookEventName // empty' 2>/dev/null || true)"
case "$event" in
  stop|subagent_stop|Stop|SubagentStop) ;;
  *) exit 0 ;;
esac

mmw_hook_collect_files "$payload"
[ "${#MMW_HOOK_FILES[@]}" -gt 0 ] || mmw_hook_collect_worktree_files
mmw_hook_diagnose && exit 0

context="$(printf '刚改过的文件有诊断问题，先看一遍再继续：\n%s' "$MMW_HOOK_OUTPUT")"
jq -nc --arg c "$context" \
  '{hookSpecificOutput: {hookEventName: "Stop", additionalContext: $c}}'
exit 0
