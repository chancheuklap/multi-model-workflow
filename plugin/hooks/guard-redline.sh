#!/usr/bin/env bash
# PreToolUse 红线:唯一硬红线 = 上线发布(合并回主分支 / push / GitHub 侧合并 / 部署)。
# 命中 → permissionDecision=ask:由用户在权限框亲批。真人批准由平台保证,
# 不再用 release-approval 令牌(令牌 agent 自己就能铸,守不住"要人批")。
# git merge 只拦"合并进主分支"——任务分支 / 子 worktree 分支间的合并是流程内自主动作,放行。
set -euo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"
[ -n "$cmd" ] || exit 0

ask() {
  jq -n --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse", permissionDecision:"ask", permissionDecisionReason:$r}}'
  exit 0
}

# 出站发布:push / GitHub 侧合并,一律要人批(git 与动词间允许插参数,如 git -c x push)
if printf '%s' "$cmd" | grep -Eq '(^|[[:space:];&|])git[^;&|]*[[:space:]]push([[:space:]]|$)'; then
  ask "红线:git push(出站发布)需用户亲批。"
fi
if printf '%s' "$cmd" | grep -Eq '(^|[[:space:];&|])gh[[:space:]]+pr[[:space:]]+merge'; then
  ask "红线:gh pr merge(GitHub 侧合并)需用户亲批。"
fi

# 部署:deploy 词(含 deploy.sh / deploy-prod / npm run deploy)+ 常见部署工具动词
if printf '%s' "$cmd" | grep -Eq '(^|[[:space:];&|/])deploy([._-]|[[:space:]]|$)'; then
  ask "红线:部署动作(deploy)需用户亲批。"
fi
if printf '%s' "$cmd" | grep -Eq '(^|[[:space:];&|])(kubectl|oc)[^;&|]*[[:space:]]apply([[:space:]]|$)|(^|[[:space:];&|])terraform[^;&|]*[[:space:]](apply|destroy)([[:space:]]|$)'; then
  ask "红线:集群/基础设施变更(apply/destroy)需用户亲批。"
fi

# git merge:只拦合并进主分支。当前分支判不出(detached / -C 指到别处看不见)也 fail-closed 问。
if printf '%s' "$cmd" | grep -Eq '(^|[[:space:];&|])git[^;&|]*[[:space:]]merge([[:space:]]|$)'; then
  if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+(-C|--git-dir)'; then
    ask "红线:带 -C/--git-dir 的 git merge 无法就地判目标分支,需用户亲批(fail-closed)。"
  fi
  cur="$(git branch --show-current 2>/dev/null || echo "")"
  def="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')" || def=""
  if [ -z "$cur" ] || [ "$cur" = "main" ] || [ "$cur" = "master" ] || { [ -n "$def" ] && [ "$cur" = "$def" ]; }; then
    ask "红线:合并进主分支(当前分支=${cur:-detached})需用户亲批。"
  fi
fi
exit 0
