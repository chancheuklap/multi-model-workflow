#!/usr/bin/env bash
# Grok 的 Stop 与 SubagentStop：把诊断交回模型。
#
# 触发点跟别的宿主不一样，这不是选择。2026-08-19 在 Grok 1.0.4 上实测：PostToolUse
# 的 hook 会触发（载荷收得到），但它写到 stdout 的 additionalContext 到不了模型——
# 同一个探针挂到 Stop 上，模型逐字读到了。所以改在会话与 subagent 停下来的时候跑，
# 用工作树里动过的文件。
#
# 返回通道也不一样：走 stdout 的 hookSpecificOutput.additionalContext，退出码一律 0。
#
# stopHookActive 必须读。Stop hook 一旦回了内容，Grok 就再跑一轮 agent，跑完又停、
# 又触发这个 hook。同一次实测里 marker 被送回了 8 次。这个字段为真就表示「这一轮
# 本来就是上一次 Stop hook 拉起来的」，此时闭嘴：诊断已经说过一遍了。

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

payload="$(cat)"
command -v jq >/dev/null 2>&1 || exit 0

# 同一份 hook 挂在多个事件上时，只有这两个事件该跑。
event="$(printf '%s' "$payload" | jq -r '.hookEventName // empty' 2>/dev/null || true)"
case "$event" in
  stop|subagent_stop|Stop|SubagentStop) ;;
  *) exit 0 ;;
esac

# 已经是我们上一次拉起来的这一轮，不再说第二遍。
active="$(printf '%s' "$payload" | jq -r '.stopHookActive // .stop_hook_active // false' 2>/dev/null || echo false)"
[ "$active" = true ] && exit 0

mmw_collect_files "$payload"
[ "${#MMW_FILES[@]}" -gt 0 ] || mmw_collect_worktree_files "$(mmw_payload_cwd "$payload")"
mmw_trace grok "$payload"
mmw_diagnose && exit 0

context="$(printf '刚改过的文件有诊断问题，先看一遍再继续：\n%s' "$MMW_OUTPUT")"
jq -nc --arg c "$context" \
  '{hookSpecificOutput: {hookEventName: "Stop", additionalContext: $c}}'
exit 0
