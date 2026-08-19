#!/usr/bin/env bash
# Cursor 的 postToolUse：编辑类工具跑完之后，对被改的文件跑一遍检查器。
#
# 返回通道跟 Claude Code 与 Codex 不一样，不能照抄：Cursor 的退出码 2 等同于
# permission deny，会挡住这次工具调用。这里一律退出 0，诊断走 stdout 的
# additional_context。
#
# 为什么不用 afterFileEdit——它更贴题（直接给 file_path 和 edits），但官方文档写明
# 它没有任何输出字段，诊断在那里交不回去。

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
mmw_collect_files "$payload"
if mmw_trace cursor "$payload"
mmw_diagnose; then
  printf '%s\n' '{}'
  exit 0
fi

jq -nc --arg c "刚改过的文件有诊断问题，先看一遍再继续：
$MMW_OUTPUT" '{additional_context: $c}'
exit 0
