#!/usr/bin/env bash
# grok 宿主 adapter。
#
# 主路径：宿主技能产物已写死原生 subagent。本文件仅在有人仍调用
# `mmw dispatch` 时给出兼容返回。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

mmw_adapter_dispatch() {
  if [ -n "${MMW_D_RESUME:-}" ]; then
    echo "mmw: grok 宿主的 resume 走原生 resume_from 或 grok --resume，不走 dispatch" >&2
    return 1
  fi
  case "$MMW_D_FAMILY" in
    gpt|claude|grok) ;;
    *)
      echo "mmw: 认不出模型族 ${MMW_D_FAMILY}（只有 claude、gpt 和 grok）" >&2
      return 1
      ;;
  esac

  printf 'mode: host-tool\n'
  printf 'tool: spawn_subagent\n'
  printf 'native: ~/.grok/agents\n'
  printf 'note: model 已在 agent 定义里；params 含 task 正文\n'

  jq -nc \
    --arg a "$MMW_D_ROSTER" \
    --arg c "$MMW_D_CWD" \
    --arg t "$MMW_D_TASK_TEXT" \
    '{subagent_type: $a, cwd: $c, prompt: $t}' \
    | sed 's/^/params: /'
}
