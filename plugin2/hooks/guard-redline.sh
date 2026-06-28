#!/usr/bin/env bash
# PreToolUse 红线:唯一硬红线 = 上线发布(合并回主分支 / push / 部署)。
# 命中且无 release-approval 令牌 → deny,要主线程先取得用户批准。
set -euo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"
[ -n "$cmd" ] || exit 0

# 上线发布动作:merge / push / deploy
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+merge|git[[:space:]]+push|(^|[[:space:];&|])deploy([[:space:]]|$)'; then
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || top="."
  if [ -f "$top/.claude/multi-model-workflow/release-approval" ]; then
    exit 0   # 已批准,放行
  fi
  echo "红线:上线发布(merge 回主分支 / push / 部署)需用户亲批。先取得 release-approval 再来。" >&2
  exit 2
fi
exit 0
