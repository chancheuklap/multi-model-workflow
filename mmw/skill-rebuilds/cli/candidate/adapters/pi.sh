#!/usr/bin/env bash
# pi 宿主 adapter。
#
# 主路径：宿主技能产物已写死 subagent({ agent, task, cwd })；本文件仅在有人仍调用
# `mmw dispatch` 时给出兼容返回。型号/thinking/async/context/skill 在 agents-pi
# frontmatter，不进 params。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

# 这个宿主的 subagent 工具自己解析 skill 参数并注入，不用把路径写进提示词。
mmw_adapter_skill_path() {
  :
}

mmw_adapter_dispatch() {
  # 仍校验模型族能映射，避免 .mmw.json 配了 Pi 接不住的族却静默写出坏 agent。
  case "$MMW_D_FAMILY" in
    gpt|claude|grok) ;;
    *)
      echo "mmw: 认不出模型族 ${MMW_D_FAMILY}（只有 claude、gpt 和 grok）" >&2
      return 1
      ;;
  esac

  printf 'mode: host-tool\n'
  printf 'tool: subagent\n'
  printf 'task-file: %s\n' "$MMW_D_TASK"
  printf 'native: agents-pi\n'
  printf 'note: model/thinking/context/async/skill 已在 agent 定义里；params 含 task 正文\n'

  # 策略字段不进 params：省略时由原生 agent 默认值生效。
  # task 正文进 params，与直调 subagent({ task }) 同一字段、同一四栏内容。
  jq -nc \
    --arg a "$MMW_D_ROSTER" \
    --arg c "$MMW_D_CWD" \
    --rawfile t "$MMW_D_TASK" \
    '{agent: $a, cwd: $c, task: $t}' \
    | sed 's/^/params: /'
}
