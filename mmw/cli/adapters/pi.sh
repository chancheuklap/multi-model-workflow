#!/usr/bin/env bash
# pi 宿主：怎么把一个角色变成一次真正的派发。
#
# 型号、思考档、async、context、skill 已物化进 agents-pi 原生 agent 的
# frontmatter（mmw agents materialize --host pi）。这里只回 agent 名与 cwd，
# 主 agent 再补 task=brief 全文。禁止在调用时重拼策略字段。
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
  printf 'brief: %s\n' "$MMW_D_BRIEF"
  printf 'native: agents-pi\n'
  printf 'note: model/thinking/context/async/skill 已在 agent 定义里；只传 params，并另附 task=brief 全文\n'

  # 策略字段不进 params：省略时由原生 agent 默认值生效，避免主 agent 手抄漏字段。
  jq -nc \
    --arg a "$MMW_D_ROSTER" \
    --arg c "$MMW_D_CWD" \
    '{agent: $a, cwd: $c}' \
    | sed 's/^/params: /'
}
