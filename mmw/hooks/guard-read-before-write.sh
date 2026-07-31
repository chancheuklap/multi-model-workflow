#!/usr/bin/env bash
# 适配层。Codex 侧的 PreToolUse：改一个已存在的文件之前，必须先把它读过。
#
# 为什么只在这一侧：Claude Code 的 Edit 与 Write 工具本身就强制先 Read，宿主内置。
# 无头那一侧没有这条，工人抓一眼 grep 结果就动手改是常态，改出来的东西经常
# 与文件里已有的写法打架。
#
# 判据故意收得紧：只有真正把文件内容打出来的命令才算读过（cat、sed -n、head、
# tail、nl、bat、less、more）。grep 与 rg 不算——它们只给出匹配行，
# 而「只看到匹配行就动手改」正是这个钩子要挡的事。
#
# 不做反规避。`>` 重定向、tee、sed -i、python 写文件都绕得过去，一概不追：
# 守不住的清单只会给人虚假的安全感。它挡的是没读就改，不是有意绕开。
#
# Codex 的 PreToolUse 只认 deny：allow 与 ask 都会被判为不支持的取值，
# 所以这里要么放行（静默退 0），要么挡掉并说清楚怎么补救。

set -euo pipefail

input="$(cat)"
jqr() { printf '%s' "$input" | jq -r "$1 // \"\"" 2>/dev/null || true; }

tool="$(jqr '.tool_name')"
sid="$(jqr '.session_id')"
cwd="$(jqr '.cwd')"
cmd="$(jqr '.tool_input.command')"
[ -n "$cmd" ] || exit 0

ledger="${TMPDIR:-/tmp}/mmw-read-${sid:-nosession}.txt"

deny() {
  jq -n --arg r "$1" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $r
    }
  }'
  exit 0
}

# 相对路径按被派进程的工作目录补全。不走 realpath：新建的文件还不存在。
abspath() {
  local p="${1#./}"
  case "$p" in /*) printf '%s' "$p" ;; *) printf '%s/%s' "${cwd%/}" "$p" ;; esac
}

case "$tool" in
  apply_patch|Edit|Write)
    # patch 正文里的目标行：*** Update File: / *** Delete File: 要求先读过，
    # *** Add File: 放行——新建的文件没有旧内容可读。
    missing=""
    while IFS= read -r target; do
      [ -n "$target" ] || continue
      full="$(abspath "$target")"
      # 盘上还没有的文件不拦：patch 头写成 Update 但文件其实不存在时，
      # 拦下来只会让工人卡在一个读不到的文件上。
      [ -f "$full" ] || continue
      grep -Fxq "$full" "$ledger" 2>/dev/null || missing="${missing}${missing:+、}${target}"
    done < <(printf '%s\n' "$cmd" | sed -nE 's/^\*\*\* (Update|Delete) File: //p')

    [ -z "$missing" ] || deny "改之前没读过：${missing}。先把整个文件打印出来看一遍（cat 或 sed -n 打全文；grep 和 rg 只给匹配行，不算读过），再改。"
    ;;

  Bash)
    # 记账面。逐段拆，只认命令位的动词，参数位出现的文件名不算读。
    while IFS= read -r seg; do
      [ -n "$seg" ] || continue
      # 引号里含空白的是数据不是路径，先摘掉再分词。
      bare="$(printf '%s' "$seg" | sed -E "s/'[^']*[[:space:]][^']*'/ /g; s/\"[^\"]*[[:space:]][^\"]*\"/ /g")"
      # shellcheck disable=SC2086
      set -f; set -- $bare; set +f
      while [ $# -gt 0 ]; do
        case "$1" in [A-Za-z_]*=*|sudo) shift ;; *) break ;; esac
      done
      [ $# -gt 0 ] || continue
      verb="${1##*/}"; shift

      case "$verb" in
        cat|nl|bat|less|more|head|tail) ;;
        sed)
          # sed -i 是改不是读；没有 -n 的 sed 也在打印全文，同样算读过。
          case " $* " in *" -i "*|*" -i."*|*" --in-place"*) continue ;; esac
          # 跳过脚本参数（第一个非选项词），剩下的才是文件。
          while [ $# -gt 0 ]; do case "$1" in -*) shift ;; *) shift; break ;; esac; done ;;
        *) continue ;;
      esac

      for a in "$@"; do
        case "$a" in -*) continue ;; esac
        f="$(abspath "$a")"
        [ -f "$f" ] || continue
        grep -Fxq "$f" "$ledger" 2>/dev/null || printf '%s\n' "$f" >> "$ledger"
      done
    done < <(printf '%s\n' "$cmd" | tr ';|&' '\n\n\n')
    ;;
esac

exit 0
