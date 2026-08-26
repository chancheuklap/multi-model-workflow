#!/usr/bin/env bash
# Cursor 的 postToolUse：编辑类工具跑完之后，对被改的文件跑一遍诊断。
#
# 返回通道跟 Claude Code 与 Codex 不一样，不能照抄：Cursor 的退出码 2 会挡住这次
# 工具调用。这里一律退出 0，诊断走 stdout 的 additional_context。

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

payload="$(mmw_hook_payload)"
mmw_hook_collect_files "$payload"
if mmw_hook_diagnose; then
  printf '%s\n' '{}'
  exit 0
fi

jq -nc --arg c "$MMW_HOOK_OUTPUT" '{additional_context: $c}'
exit 0
