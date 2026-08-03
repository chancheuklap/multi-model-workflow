#!/usr/bin/env bash
# 结构候选传输合同：严格校验六字段数组，并把规范化快照写到派发状态目录。

mmw_retrieval_candidates_snapshot() { # $1=输入绝对 JSON（空=无结构问题） $2=快照落点
  local input="${1:-}" output="$2"
  mkdir -p "$(dirname "$output")"
  if [ -z "$input" ]; then printf '[]\n' >"$output"; return 0; fi
  case "$input" in /*) ;; *) echo "ERROR: --retrieval-candidates 必须是绝对路径" >&2; return 2 ;; esac
  [ -f "$input" ] || { echo "ERROR: retrieval candidates 文件不存在:$input" >&2; return 2; }
  jq -e 'type == "array" and all(.[]; type == "object" and ((keys | sort) == ["fallback_reason","locators","query","status","summary","tool"]) and (.tool == "graphify" or .tool == "serena") and (.query | type == "string") and (.status == "used" or .status == "not_available" or .status == "unsupported" or .status == "failed") and (.locators | type == "array") and all(.locators[]; type == "string") and (.summary | type == "string") and (.fallback_reason | type == "string"))' "$input" >/dev/null || { echo "ERROR: retrieval candidates 必须是精确六字段数组(tool/query/status/locators/summary/fallback_reason)" >&2; return 2; }
  jq -S '.' "$input" >"$output"
}

mmw_retrieval_candidates_prompt() {
  printf '%s\n' '## 上游结构候选（仅候选，不代表本 worker 调过工具）'
  printf '```json\n'; jq -c '.' "$1"; printf '```\n'
  printf '%s\n' '逐 locator 回目标 checkout 用源码 Read/grep/rg 亲验；unsupported、not_available、failed 和空结果都不能证明不存在。Serena 对装饰器 endpoint 完整调用方、动态 await import() 解构引用存在已知盲区，须转 Graphify 加源码检索。'
  printf '%s\n' '回执必须单列“结构候选”：分别写上游候选、worker 自己实际调用的工具、源码亲验 locator、fallback_reason；禁止把上游候选冒充 worker 工具调用。'
}
