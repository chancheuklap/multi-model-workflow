#!/usr/bin/env bash
# 实测：子 agent 改文件的时候，编辑后诊断到不到它手里。
#
# 为什么要这个脚本而不是读文档：没有一家宿主写过「子 agent 的工具调用会不会触发
# 父会话的 PostToolUse」。三种可能都存在——照常触发、完全不触发、触发但拿不到文件
# 路径——而三种在外面看起来一模一样（都是没有诊断出现）。按猜测去补，大概率补的是
# 不存在的洞，真洞还在。
#
# 留在仓库里是因为宿主会升级。合同变了要能当场重测，不用再把这一套推理走一遍。
#
# 测的是两件不同的事，分开报：
#   触发   hook 跑起来了，而且看见了子 agent 改的那个文件（读 MMW_DIAG_TRACE）
#   送达   诊断正文进了模型的上下文（在宿主的回答里找诊断原文的关键词）
# 只有两个都成立，这条通道才算通。触发了但没送达，是返回通道的问题；没触发，是
# 事件挂错了地方。
#
#   probe-subagent.sh              测所有认得的宿主
#   probe-subagent.sh claude grok  只测这几个
#
# 每个宿主真起一次 headless 会话，会花钱也会花时间。

set -uo pipefail

# 子 agent 要写进去的东西。两条诊断：AKIA… 命中密钥扫描，import os 命中 ruff 的 F401。
# 密钥那一条的提示语是我们自己写的一句中文，模型不会自己说出来，用它判「送达」最准。
PROBE_FILE="probe_target.py"
MARKER="明文凭证"
# 拼出来，不写字面量：写成一整串的话，这个脚本自己每次被编辑都会被密钥扫描拦下来。
FAKE_KEY="AK""IA1234567890ABCDEF"

PROMPT="这是一次工具通道测试，不要改动测试之外的任何东西。

请派一个子 agent（subagent）去做下面这件事。你自己不要动文件，必须交给子 agent：

把 ${PROBE_FILE} 的内容整个替换成这两行，用编辑或写入工具，不要用 shell 命令：

import os
KEY = \"${FAKE_KEY}\"

子 agent 做完以后，把它在写入过程中看到的任何诊断提示**原文照抄**给我。
一个字都没看到就只回答：没有诊断。"

setup_repo() {
  local dir
  dir="$(mktemp -d)"
  git -C "$dir" init -q .
  git -C "$dir" config user.email probe@mmw
  git -C "$dir" config user.name probe
  printf 'VALUE = 1\n' > "$dir/$PROBE_FILE"
  git -C "$dir" add "$PROBE_FILE"
  git -C "$dir" commit -qm base
  printf '%s' "$dir"
}

# 各宿主的 headless 入口。命令都在本机 --help 上查过，不是照抄别处。
run_host() {
  local host="$1" dir="$2"
  case "$host" in
    claude)
      (cd "$dir" && claude -p "$PROMPT" --permission-mode acceptEdits 2>&1) ;;
    codex)
      codex exec --cd "$dir" --sandbox workspace-write --skip-git-repo-check "$PROMPT" 2>&1 ;;
    cursor)
      (cd "$dir" && cursor-agent -p "$PROMPT" --force 2>&1) ;;
    grok)
      grok -p "$PROMPT" --always-approve --cwd "$dir" 2>&1 ;;
    pi)
      (cd "$dir" && pi -p "$PROMPT" 2>&1) ;;
    *)
      echo "不认得的宿主 $host" >&2; return 2 ;;
  esac
}

HOSTS=("$@")
[ "${#HOSTS[@]}" -gt 0 ] || HOSTS=(claude codex cursor grok pi)

LOGS="$(mktemp -d)"

printf '%-8s %-6s %-6s %s\n' 宿主 触发 送达 说明
printf -- '---------------------------------------------------------------\n'

rc=0
for host in "${HOSTS[@]}"; do
  dir="$(setup_repo)"
  trace="$dir/.mmw-trace.jsonl"
  : > "$trace"

  answer="$(MMW_DIAG_TRACE="$trace" run_host "$host" "$dir")"

  fired=否
  grep -q "$PROBE_FILE" "$trace" 2>/dev/null && fired=是
  delivered=否
  printf '%s' "$answer" | grep -q "$MARKER" && delivered=是

  note=""
  # 子 agent 根本没被派出去的话，这一轮什么都没测到，不能记成「不支持」。
  if ! grep -q "$FAKE_KEY" "$dir/$PROBE_FILE" 2>/dev/null; then
    note="文件没被改，这一轮没测到东西"
  elif [ "$fired" = 是 ] && [ "$delivered" = 否 ]; then
    note="hook 跑了但正文没到模型：返回通道的问题"
  elif [ "$fired" = 否 ]; then
    note="hook 没触发：事件挂错了地方"
  fi
  [ "$fired$delivered" = "是是" ] || rc=1

  printf '%-8s %-6s %-6s %s\n' "$host" "$fired" "$delivered" "$note"
  # 会话原文留在临时目录，不写进仓库。判断可疑时要能翻回去看模型到底说了什么。
  printf '%s\n' "$answer" > "$LOGS/$host.log"
  rm -rf "$dir"
done

printf -- '---------------------------------------------------------------\n'
printf '会话原文：%s\n' "$LOGS"

exit "$rc"
