#!/usr/bin/env bash
# pi 宿主：怎么把一个角色变成一次真正的派发。
#
# 这个宿主两种模型都是同一个工具，只有 model 字段不同——GPT 走 openai-codex，
# Claude 走 claude-provider（它把推理请求转给本机的 claude 可执行文件）。CLI
# 跑不了会话内工具，所以两种都只给参数。
#
# 方法论走 skill 参数，从包声明的技能目录解析，不必软链。
#
# 本文件不做流程判断。它只回答「这个宿主管这个动作叫什么」。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

# 这个宿主的 subagent 工具自己解析 skill 参数并注入，不用把路径写进提示词。
mmw_adapter_skill_path() {
  :
}

mmw_adapter_dispatch() {
  local provider
  case "$MMW_D_FAMILY" in
    gpt) provider="openai-codex" ;;
    claude) provider="claude-provider" ;;
    *)
      echo "mmw: 认不出模型族 ${MMW_D_FAMILY}（只有 claude 和 gpt）" >&2
      return 1
      ;;
  esac

  printf 'mode: host-tool\n'
  printf 'tool: subagent\n'
  printf 'brief: %s\n' "$MMW_D_BRIEF"

  # context 固定 fresh：MMW 要的是上下文隔离，不要从父会话分叉。
  jq -nc \
    --arg a "$MMW_D_ROSTER" \
    --arg m "$provider/$MMW_D_MODEL_ID" \
    --arg t "$MMW_D_EFFORT" \
    --arg c "$MMW_D_CWD" \
    --arg s "$MMW_D_SKILL" \
    '{agent: $a, model: $m, thinking: $t, cwd: $c, context: "fresh"}
     + (if $s == "" then {} else {skill: $s} end)' \
    | sed 's/^/params: /'
}
