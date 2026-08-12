#!/usr/bin/env bash
# Grok Stop / SubagentStop：把 mmw toolchain check 的诊断交回模型。
# 不要复用 Codex/Claude 的退出码 2 合同。Grok 的 PostToolUse 忽略 stdout。

set -uo pipefail

payload="$(cat)"

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

event="$(printf '%s' "$payload" | jq -r '.hookEventName // empty' 2>/dev/null || true)"
case "$event" in
  stop|subagent_stop|Stop|SubagentStop) ;;
  *) exit 0 ;;
esac

files=()
while IFS= read -r line; do
  [ -n "$line" ] && files+=("$line")
done < <(
  printf '%s' "$payload" | jq -r '
    ((.toolInput // .tool_input // {}) as $i
    | [
        ($i.path // empty),
        ($i.filePath // empty),
        ($i.file_path // empty)
      ]
    | map(select(. != null and . != ""))
    | unique
    | .[])
  ' 2>/dev/null
)

if [ "${#files[@]}" -eq 0 ] && command -v git >/dev/null 2>&1 \
   && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  while IFS= read -r line; do
    [ -n "$line" ] && files+=("$line")
  done < <(git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)
fi

[ "${#files[@]}" -gt 0 ] || exit 0

if ! command -v mmw >/dev/null 2>&1; then
  exit 0
fi

if output="$(mmw toolchain check --changed-only "${files[@]}" 2>&1)"; then
  exit 0
fi
rc=$?
[ "$rc" -eq 2 ] || exit 0

context="$(printf '刚改过的文件有诊断问题，先看一遍再继续：\n%s' "$output")"
jq -nc --arg c "$context" \
  '{hookSpecificOutput: {hookEventName: "Stop", additionalContext: $c}}'
exit 0
