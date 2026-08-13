#!/usr/bin/env bash
# Cursor postToolUse：编辑类工具跑完之后，对被改的文件跑一遍诊断，把结果交回 agent。
#
# 不要复用 Codex 的 post-tool-use.sh。那边退出码 2 表示「把 stderr 交回 agent」；
# Cursor 的退出码 2 会挡住这次工具调用。这里一律退出 0，诊断走 stdout 的
# additional_context。
#
# 输入是 stdin 上的一份 JSON，字段以 Cursor 官方 hooks 文档为准：tool_name、
# tool_input。文件路径从 tool_input 的 path / filePath / file_path 取。
# 取不到路径就输出空对象并退出——不认识的工具不是错误。
#
# 诊断跑不起来不该挡住干活：mmw 或 jq 不在就输出空对象。

set -uo pipefail

payload="$(cat)"

if ! command -v jq >/dev/null 2>&1; then
  printf '%s\n' '{}'
  exit 0
fi

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
    | map(select(. != null and . != ""))
    | unique
    | .[]
  ' 2>/dev/null
)

if [ "${#files[@]}" -eq 0 ]; then
  printf '%s\n' '{}'
  exit 0
fi

if ! command -v mmw >/dev/null 2>&1; then
  printf '%s\n' '{}'
  exit 0
fi

if output="$(mmw toolchain check --changed-only "${files[@]}" 2>&1)"; then
  printf '%s\n' '{}'
  exit 0
fi

jq -nc --arg c "$output" '{additional_context: $c}'
exit 0
