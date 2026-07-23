#!/usr/bin/env bash
# Codex PreToolUse 红线：首次拦下出站发布/部署；带原生权限请求的重试交给 Codex 审批框。
set -euo pipefail

payload="$(cat)"
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[ -n "$cmd" ] || exit 0

# PreToolUse 当前不支持 permissionDecision=ask。协调者重试时显式请求 Codex 原生权限；
# hook 放行这次 tool call，随后由 Codex 自己的 PermissionRequest/approval UI 决定。
approval_route="$(printf '%s' "$payload" | jq -r '.tool_input.sandbox_permissions // empty' 2>/dev/null || true)"
[ "$approval_route" = require_escalated ] && exit 0

# heredoc 正文是数据，不把 runbook 里的发布命令当动作。
cmd="$(printf '%s\n' "$cmd" | awk '
  strip { if ($0 ~ ("^[\t]*" tag "$")) strip=0; next }
  {
    if (match($0, /<<-?[ \t]*['\''"]?[A-Za-z_][A-Za-z0-9_]*/)) {
      t=substr($0, RSTART, RLENGTH); sub(/<<-?[ \t]*/, "", t); gsub(/['\''"]/, "", t)
      tag=t; strip=1
    }
    print
  }')"

# eval / shell -c 内的字符串也是要执行的代码。
inner="$(printf '%s\n' "$cmd" \
  | grep -oE "(eval|[[:space:]]-[a-zA-Z]*c)[[:space:]]+('[^']*'|\"[^\"]*\")" 2>/dev/null \
  | sed -E "s/^[^'\"]*['\"]//; s/['\"]$//" || true)"
[ -n "$inner" ] && cmd="$cmd
$inner"

# 含空白的引号串视为参数文本；无空白引号只去引号，堵住 git "push" 这类打散。
cmd="$(printf '%s' "$cmd" \
  | sed -E "s/'[^']*[[:space:]][^']*'/ /g; s/\"[^\"]*[[:space:]][^\"]*\"/ /g; s/['\"]//g; s/\\\\//g")"

block() {
  printf '%s\n' "$1；需用户通过 Codex 原生权限框确认。请用带明确 justification 的原生权限请求重试同一命令。" >&2
  exit 2
}

word_in() {
  case " $2 " in *" $1 "*) return 0 ;; esac
  return 1
}

judge_seg() {
  set -f
  # shellcheck disable=SC2086
  set -- $1
  set +f
  while [ $# -gt 0 ]; do
    case "$1" in
      [A-Za-z_]*=*) shift ;;
      if|then|else|elif|fi|while|until|do|done|exec|eval|builtin|command|!) shift ;;
      sudo|env|nohup|time|xargs|timeout|gtimeout|nice|stdbuf|setsid|caffeinate) shift ;;
      -*|[0-9]*) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || return 0
  local command_name="$1"
  shift
  local rest="$*"

  case "$command_name" in
    git)
      while [ $# -gt 0 ]; do
        case "$1" in
          -C|-c|--git-dir|--work-tree|--namespace|--exec-path)
            shift
            [ $# -gt 0 ] && shift
            ;;
          -*) shift ;;
          *) break ;;
        esac
      done
      [ $# -gt 0 ] && [ "$1" = push ] && block "红线：git push 是出站发布"
      ;;
    gh)
      printf '%s' "$rest" | grep -Eq '(^|[[:space:]])pr[[:space:]]+merge([[:space:]]|$)' \
        && block "红线：gh pr merge 是 GitHub 侧合并"
      if word_in api "$rest" \
        && printf '%s' "$rest" | grep -Eq 'pulls/[^[:space:]]*/merge'; then
        block "红线：gh api pulls/*/merge 是 GitHub 侧合并"
      fi
      ;;
    kubectl|oc)
      if word_in apply "$rest" && ! printf '%s' "$rest" | grep -q -- '--dry-run'; then
        block "红线：集群 apply 是部署"
      fi
      ;;
    terraform)
      word_in apply "$rest" && block "红线：terraform apply 是基础设施部署"
      word_in destroy "$rest" && block "红线：terraform destroy 是基础设施销毁"
      ;;
    bash|sh|zsh|source)
      if ! printf '%s' "$rest" | grep -Eq '(^|[[:space:]])-[a-zA-Z]*n([[:space:]]|$)' \
        && printf '%s' "$rest" | grep -Eq '(^|[[:space:]])[^[:space:]]*deploy[a-z0-9._-]*\.(sh|py)([[:space:]]|$)'; then
        block "红线：deploy 脚本是部署动作"
      fi
      ;;
    ./*deploy*.sh|./*deploy*.py|cloud-deploy)
      block "红线：deploy 命令是部署动作"
      ;;
    npm|pnpm|yarn|npx|make|just|task)
      word_in deploy "$rest" && block "红线：deploy task 是部署动作"
      ;;
  esac
  return 0
}

segs="$(printf '%s\n' "$cmd" | tr ';|&(){}`' '\n')"
while IFS= read -r seg; do
  judge_seg "$seg"
done <<<"$segs"

exit 0
