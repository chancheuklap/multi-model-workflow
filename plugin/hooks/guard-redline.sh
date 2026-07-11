#!/usr/bin/env bash
# PreToolUse 红线:唯一硬红线 = 出站发布 / 部署 —— push / GitHub 侧合并(gh pr merge)/ deploy。
# 命中 → permissionDecision=ask:由用户在权限框亲批。真人批准由平台保证,
# 不再用 release-approval 令牌(令牌 agent 自己就能铸,守不住"要人批")。
# **本地 git merge(含合并进 main)不拦**:可逆、不出站,真正红线是它之后的 push;
# 拦本地 merge 只会打断无人值守的自动推进(用户明确要求放行)。
set -euo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")"
[ -n "$cmd" ] || exit 0

# 误拦防线 1:剥引号串——commit message / 引号文本里的 push/deploy 是数据不是动作。
cmd="$(printf '%s' "$cmd" | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")"

ask() {
  jq -n --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse", permissionDecision:"ask", permissionDecisionReason:$r}}'
  exit 0
}

# rest 中含独立单词 $1?
word_in() { case " $2 " in *" $1 "*) return 0 ;; esac; return 1; }

# 误拦防线 2:按命令边界拆段(; | & 换行 括号 反引号),每段只认**命令位**的动词——
# 关键词落在参数位(如 echo/printf 的文本、grep 的模式)不是动作,不拦。
judge_seg() {
  set -f
  # shellcheck disable=SC2086
  set -- $1
  set +f
  # 剥前导环境变量赋值与常见包装器,取真实命令词
  while [ $# -gt 0 ]; do
    case "$1" in
      [A-Za-z_]*=*) shift ;;
      sudo|env|command|nohup|time|xargs) shift ;;
      timeout|gtimeout) shift; if [ $# -gt 0 ]; then shift; fi ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || return 0
  c="$1"; shift
  rest="$*"

  case "$c" in
    git)
      if word_in push "$rest"; then ask "红线:git push(出站发布)需用户亲批。"; fi ;;
    gh)
      if printf '%s' "$rest" | grep -Eq '(^|[[:space:]])pr[[:space:]]+merge([[:space:]]|$)'; then
        ask "红线:gh pr merge(GitHub 侧合并)需用户亲批。"
      fi ;;
    kubectl|oc)
      if word_in apply "$rest"; then ask "红线:集群/基础设施部署(apply/destroy)需用户亲批。"; fi ;;
    terraform)
      if word_in apply "$rest"; then ask "红线:集群/基础设施部署(apply/destroy)需用户亲批。"; fi
      if word_in destroy "$rest"; then ask "红线:集群/基础设施部署(apply/destroy)需用户亲批。"; fi ;;
    bash|sh|zsh|source)
      # bash -n 语法检查不是发布;跑 *deploy*.sh|.py 才是
      if ! printf '%s' "$rest" | grep -Eq '(^|[[:space:]])-[a-zA-Z]*n([[:space:]]|$)'; then
        if printf '%s' "$rest" | grep -Eq '(^|[[:space:]])[^[:space:]]*deploy[a-z0-9._-]*\.(sh|py)([[:space:]]|$)'; then
          ask "红线:部署动作(deploy)需用户亲批。"
        fi
      fi ;;
    ./*deploy*.sh|./*deploy*.py)
      ask "红线:部署动作(deploy)需用户亲批。" ;;
    cloud-deploy)
      ask "红线:部署动作(deploy)需用户亲批。" ;;
    npm|pnpm|yarn|npx|make|just|task)
      if word_in deploy "$rest"; then ask "红线:部署动作(deploy)需用户亲批。"; fi ;;
  esac
  return 0
}

segs="$(printf '%s\n' "$cmd" | tr ';|&()`' '\n')"
while IFS= read -r seg; do
  judge_seg "$seg"
done <<< "$segs"

# 本地 git merge(含进 main)不拦——可逆、不出站;真正红线是之后的 push。
exit 0
