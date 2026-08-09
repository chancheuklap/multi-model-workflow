#!/usr/bin/env bash
# PostToolUse：编辑类工具跑完之后，对被改的文件跑一遍诊断。Codex 与 Claude Code 共用这一份。
#
# Codex 没有原生 LSP——lspServers 是 Claude Code 插件 schema 的私有字段，Codex 二进制里
# 没有对应的语言服务器管理。它有的是 hooks。这个脚本就是 Codex 那一侧的推送通道，调的是
# 和 Pi 同一个 mmw toolchain check。
#
# Claude Code 有原生 LSP，但 LSP 只报类型错误，ruff 和 oxlint 的规则不在里面。Claude Code
# 也挂这个 hook，补上 LSP 不覆盖的那一半。三个宿主因此看到同一批诊断。
#
# 输入是 stdin 上的一份 JSON。文件路径的取法按工具分：
#   apply_patch  路径写在 tool_input.command 的补丁正文里，从 *** Add/Update File: 取
#   write/edit   tool_input 里的 path / filePath / file_path 三种别名之一
# 取不到路径就安静退出——不认识的工具不是错误。这一条同时充当工具过滤：Bash、Read、Grep
# 这些提不出路径的调用在这里就退出，不必依赖各宿主的 matcher 语法。
#
# 退出码 2 在 Codex 与 Claude Code 的 hook 合同里都表示"把 stderr 交回 agent"。其他情况
# 一律 0：诊断跑不起来不该挡住干活。

set -uo pipefail

payload="$(cat)"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

# 不用 mapfile：macOS 自带的是 bash 3.2，没有这个内建。
files=()
while IFS= read -r line; do
  [ -n "$line" ] && files+=("$line")
done < <(
  printf '%s' "$payload" | jq -r '
    (.tool_input // {}) as $i
    | [
        ($i.path // empty),
        ($i.filePath // empty),
        ($i.file_path // empty)
      ]
      + (
        ($i.command // "")
        | if type == "string" then
            [scan("\\*\\*\\* (?:Add|Update|Move) File: (.+)")[]?[0]]
          else [] end
      )
    | map(select(. != null and . != ""))
    | unique
    | .[]
  ' 2>/dev/null
)

[ "${#files[@]}" -gt 0 ] || exit 0

if ! command -v mmw >/dev/null 2>&1; then
  exit 0
fi

if output="$(mmw toolchain check --changed-only "${files[@]}" 2>&1)"; then
  exit 0
fi

printf '%s\n' "$output" >&2
exit 2
