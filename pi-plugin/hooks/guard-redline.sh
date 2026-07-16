#!/usr/bin/env bash
# pi tool_call 红线:唯一硬红线 = 出站发布 / 部署 —— push / GitHub 侧合并 / deploy。
# 命中以 exit 2 + stderr 原因回给 extensions/mmw-hooks.ts；扩展有 UI 时弹窗人批，
# headless 时 fail-closed。本地 git merge 可逆，不拦。
set -euo pipefail

cmd="${1:-${MMW_TOOL_COMMAND:-}}"
[ -n "$cmd" ] || exit 0

# 1) 剥 heredoc 正文——文档/脚本正文里的 push/deploy 行是数据不是动作
cmd="$(printf '%s\n' "$cmd" | awk '
  strip { if ($0 ~ ("^[\t]*" tag "$")) strip=0; next }
  {
    if (match($0, /<<-?[ \t]*['\''"]?[A-Za-z_][A-Za-z0-9_]*/)) {
      t=substr($0, RSTART, RLENGTH); sub(/<<-?[ \t]*/, "", t); gsub(/['\''"]/, "", t)
      tag=t; strip=1
    }
    print
  }')"

# 2) eval / bash -c 等引号里的字符串是代码不是数据:提取出来一并判
inner="$(printf '%s\n' "$cmd" | grep -oE "(eval|[[:space:]]-[a-zA-Z]*c)[[:space:]]+('[^']*'|\"[^\"]*\")" 2>/dev/null | sed -E "s/^[^'\"]*['\"]//; s/['\"]$//" || true)"
[ -n "$inner" ] && cmd="$cmd
$inner"

# 3) 引号归一:含空白的引号串 = 数据(commit message 等),删;不含空白的只剥引号/反斜杠字符,
#    还原被打散的动词(git "push"、pu''sh、pu\sh)
cmd="$(printf '%s' "$cmd" | sed -E "s/'[^']*[[:space:]][^']*'/ /g; s/\"[^\"]*[[:space:]][^\"]*\"/ /g; s/['\"]//g; s/\\\\//g")"

ask() {
  printf '%s\n' "$1" >&2
  exit 2
}

# rest 中含独立单词 $1?
word_in() { case " $2 " in *" $1 "*) return 0 ;; esac; return 1; }

# 每段只认**命令位**的动词——关键词落在参数位(echo/printf 文本、grep 模式)不是动作,不拦。
judge_seg() {
  set -f
  # shellcheck disable=SC2086
  set -- $1
  set +f
  # 剥前导:环境变量赋值 / shell 关键字与结构符 / 常见包装器及其选项、数值参数
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
  c="$1"; shift
  rest="$*"

  case "$c" in
    git)
      # 剥 git 全局选项取子命令;只有**子命令位**的 push 才是出站(stash push / log --grep push 不拦)
      while [ $# -gt 0 ]; do
        case "$1" in
          -C|-c|--git-dir|--work-tree|--namespace|--exec-path) shift; [ $# -gt 0 ] && shift ;;
          -*) shift ;;
          *) break ;;
        esac
      done
      if [ $# -gt 0 ] && [ "$1" = "push" ]; then ask "红线:git push(出站发布)需用户亲批。"; fi ;;
    gh)
      if printf '%s' "$rest" | grep -Eq '(^|[[:space:]])pr[[:space:]]+merge([[:space:]]|$)'; then
        ask "红线:gh pr merge(GitHub 侧合并)需用户亲批。"
      fi
      if word_in api "$rest" && printf '%s' "$rest" | grep -Eq 'pulls/[^[:space:]]*/merge'; then
        ask "红线:gh api pulls/*/merge(GitHub 侧合并)需用户亲批。"
      fi ;;
    kubectl|oc)
      if word_in apply "$rest" && ! printf '%s' "$rest" | grep -q -- '--dry-run'; then
        ask "红线:集群/基础设施部署(apply/destroy)需用户亲批。"
      fi ;;
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

segs="$(printf '%s\n' "$cmd" | tr ';|&(){}`' '\n')"
while IFS= read -r seg; do
  judge_seg "$seg"
done <<< "$segs"

# 本地 git merge(含进 main)不拦——可逆、不出站;真正红线是之后的 push。
exit 0
