#!/usr/bin/env bash
# Claude Code 与 Codex 的 PostToolUse：编辑类工具跑完之后，对被改的文件跑一遍诊断。
#
# 这两家的 hook 合同一样：退出码 2 加 stderr 表示「把这段话交回 agent」。其他情况
# 一律 0——诊断跑不起来不该挡住干活。
#
# Codex 没有原生 LSP，这个 hook 是它那一侧唯一的诊断推送通道。Claude Code 有 LSP，
# 但 LSP 只报类型错误，ruff 与 oxlint 的规则不在里面，这个 hook 补上另一半。四个
# 宿主因此看到同一批诊断。
#
# 提不出文件路径就退出。这一条同时充当工具过滤：Bash、Read、Grep 这些调用在这里
# 就退出，不必依赖各宿主的 matcher 语法。

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
mmw_hook_diagnose && exit 0

printf '%s\n' "$MMW_HOOK_OUTPUT" >&2
exit 2
