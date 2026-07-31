#!/usr/bin/env bash
# 适配层。唯一的机器硬检查：出站发布——推送、远端侧合并、部署。命中即弹权限框，由用户亲批。
# 本地 merge 不拦：可逆、不出站，真红线是它之后的推送；拦它只会打断无人值守的推进。
#
# 宿主的 if 前筛已经按 bash 语法分好段（剥前导环境变量赋值、拆 && 与 ;、连 $() 里的也查），
# 所以这里不再自己写一套解析。前筛无法解析命令时会放行到这里，那种命令本来就更该让人看一眼。
#
# 不做反规避：刻意绕开这里的写法（换个等价命令、heredoc 里藏命令）一概不追。守不住，
# 追下去只会长成一张永远不全的清单，给人虚假的安全感。它挡的是顺手敲出去，不是有意绕过。
# 同理，误报（heredoc 正文提到推送命令）也不加剥离层——最后防线本就是权限框，点一下就过。

set -euo pipefail

cmd="$(jq -r '.tool_input.command // ""' 2>/dev/null || true)"
[ -n "$cmd" ] || exit 0

ask() {
  jq -n --arg r "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: $r
    }
  }'
  exit 0
}

# 逐段看：拆开后每段剥掉前导包装器，只认命令位的动词。
# 关键词落在参数位（echo 的文本、grep 的模式）不是动作，不拦。
while IFS= read -r seg; do
  [ -n "$seg" ] || continue
  # 引号里含空白的是数据不是命令（提交信息、grep 模式），先摘掉再分词。
  # 这不是反规避层——不还原被刻意打散的动词，只是别把文本当动作。
  bare="$(printf '%s' "$seg" | sed -E "s/'[^']*[[:space:]][^']*'/ /g; s/\"[^\"]*[[:space:]][^\"]*\"/ /g")"
  # shellcheck disable=SC2086
  set -f; set -- $bare; set +f
  while [ $# -gt 0 ]; do
    case "$1" in
      [A-Za-z_]*=*|sudo) shift ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || continue
  tool="$1"
  # 看子命令位而不是「命令里出现过这个词」：`git commit -m "add push handler"` 的 push
  # 在提交信息里，不是动作。剥掉 git / gh 自己的选项后，第一个非选项词才算子命令。
  if [ "$tool" = "git" ] || [ "$tool" = "gh" ]; then
    shift
    while [ $# -gt 0 ]; do
      case "$1" in
        -C|-c|-R|--repo) shift 2 || break ;;
        -*) shift ;;
        *) break ;;
      esac
    done
  fi
  rest=" $* "
  case "$tool" in
    git)
      [ "${1:-}" = "push" ] && ask "要往远端推送：${seg}" ;;
    gh)
      case "$rest" in
        " pr merge "*)      ask "要在远端合并：${seg}" ;;
        " release create"*) ask "要发布 release：${seg}" ;;
      esac ;;
    *deploy*)
      ask "看着像部署动作：${seg}" ;;
  esac
  # 部署的入口太发散（npm run deploy、make deploy、just deploy…），命令位判不完。
  # 再看一眼参数位有没有独立的 deploy 词；带引号的文本（如提交信息）分词后不是独立词，不会命中。
  case "$rest" in
    *" deploy "*|*" deploy:"*) ask "看着像部署动作：${seg}" ;;
  esac
done < <(printf '%s\n' "$cmd" | tr ';|&' '\n\n\n')

exit 0
