#!/usr/bin/env bash
# Codex PostToolUse：编辑类工具跑完之后，对被改的文件跑一遍诊断。
#
# Codex 没有原生 LSP——lspServers 是 Claude Code 插件 schema 的私有字段，Codex 二进制里
# 没有对应的语言服务器管理。它有的是 hooks。这个脚本就是 Codex 那一侧的推送通道，调的是
# 和 Pi 同一个 mmw toolchain check，所以两家看到的诊断和 Claude Code 原生 LSP 报的是
# 同一批。
#
# 输入是 stdin 上的一份 JSON。文件路径的取法按工具分：
#   apply_patch  路径写在 tool_input.command 的补丁正文里，从 *** Add/Update File: 取
#   write/edit   tool_input 里的 path / filePath / file_path 三种别名之一
# 取不到路径就安静退出——不认识的工具不是错误。
#
# 退出码 2 是 Codex hook 合同里"把 stderr 交回 agent"的意思。其他情况一律 0：诊断跑不起来
# 不该挡住 Codex 干活。

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
