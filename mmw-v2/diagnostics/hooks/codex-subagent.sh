#!/usr/bin/env bash
# Codex 的 SubagentStop：子 agent 停下来的时候，对工作树里动过的文件跑一遍检查器。
#
# 为什么要单独一份而不是复用 claude-codex.sh：2026-08-19 实测，Codex 的子 agent
# （它叫 collab）改文件时，父会话的 PostToolUse **不触发**。子 agent 写完文件、父
# agent 回答「没有诊断」，而文件里就躺着一个明文密钥。
#
# 这一侧拿不到工具输入，只能扫工作树，跟 Grok 那一份同一个道理。所以不能把这段逻辑
# 塞回 claude-codex.sh：那一份挂在 PostToolUse 上，「载荷里没有文件路径」在那里的含义
# 是「这次调用不是编辑」（Bash、Read、Grep 都会走到那里），加上工作树兜底就等于每次
# 读文件都全仓库扫一遍。
#
# 返回通道跟 Codex 的 PostToolUse 一样：退出码 2 加 stderr。
#
# stop_hook_active 必须读，理由跟 Grok 那一份一样：停下来的 hook 一旦回了内容，宿主
# 可能再跑一轮，跑完又停又触发，同一段话来回送。

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

# 已经是我们上一次拉起来的这一轮，不再说第二遍。
active="$(printf '%s' "$payload" | jq -r '.stop_hook_active // .stopHookActive // false' 2>/dev/null || echo false)"
[ "$active" = true ] && exit 0

mmw_collect_files "$payload"
[ "${#MMW_FILES[@]}" -gt 0 ] || mmw_collect_worktree_files "$(mmw_payload_cwd "$payload")"
mmw_trace codex-subagent "$payload"
mmw_diagnose && exit 0

printf '%s\n' "$MMW_OUTPUT" >&2
exit 2
