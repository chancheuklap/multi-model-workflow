#!/usr/bin/env bash
# PreToolUse 红线:唯一硬红线 = 上线发布(合并回主分支 / push / GitHub 侧合并 / 部署)。
# 命中 → permissionDecision=ask:由用户在权限框亲批。真人批准由平台保证,
# 不再用 release-approval 令牌(令牌 agent 自己就能铸,守不住"要人批")。
# git merge 只拦"合并进主分支"——任务分支 / 子 worktree 分支间的合并是流程内自主动作,放行。
set -euo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"
[ -n "$cmd" ] || exit 0

# 误拦防线:动词匹配前剥掉引号串——commit message / echo 文本里出现 push/deploy/merge 不是动作。
# 只影响下面的 grep 判定,不改真实命令;跨行引号剥不干净时残余误拦朝 ask 方向(fail-closed 可接受)。
cmd="$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")"

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

# 部署:只拦"真正执行部署",不拦只读引用 deploy 命名文件。
# 命中前:cat/grep/ls/sed/chmod/plutil 看一眼、bash -n 语法检查都不是发布,放行。
# 命中:跑 *deploy*.sh|.py 脚本 / cloud-deploy 子命令 / 包管理器 deploy 任务。
run_deploy_re='(^|[[:space:];&|])(bash|sh|zsh|source)[[:space:]]+[^;&|]*deploy[a-z0-9._-]*\.(sh|py)([[:space:]]|$)'
dotslash_deploy_re='(^|[[:space:];&|])\./[^;&|]*deploy[a-z0-9._-]*\.(sh|py)([[:space:]]|$)'
subcmd_deploy_re='(^|[[:space:];&|])cloud-deploy([[:space:]]|$)'
pkg_deploy_re='(^|[[:space:];&|])(npm|pnpm|yarn|npx|make|just|task)[^;&|]*[[:space:]]deploy([[:space:]]|$)'
syntax_check_re='(^|[[:space:];&|])(bash|sh|zsh)[[:space:]]+-[a-zA-Z]*n([[:space:]]|$)'
if { printf '%s' "$cmd" | grep -Eq "$run_deploy_re" \
       && ! printf '%s' "$cmd" | grep -Eq "$syntax_check_re"; } \
   || printf '%s' "$cmd" | grep -Eq "$dotslash_deploy_re" \
   || printf '%s' "$cmd" | grep -Eq "$subcmd_deploy_re" \
   || printf '%s' "$cmd" | grep -Eq "$pkg_deploy_re"; then
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
