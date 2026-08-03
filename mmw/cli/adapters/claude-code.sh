#!/usr/bin/env bash
# Claude Code 宿主：怎么把一个角色变成一次真正的派发。
#
# 这个宿主的会话内 subagent 只能是 Claude，所以派 GPT 必须走 codex exec 外部
# 进程——CLI 自己跑得完，直接跑。派 Claude 走 Agent 工具，CLI 跑不了，只能把
# 参数交给模型去调。
#
# 方法论怎么到派出去的那个模型手里，两条路也不同：codex exec 看不见插件文件，
# 靠 install-agent-skills.sh 软链进它自己的技能目录；会话内的 subagent 读得到
# 插件原件，所以给绝对路径，由调用方写进提示词。
#
# 本文件不做流程判断。它只回答「这个宿主管这个动作叫什么」。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

mmw_adapter_dispatch() {
  case "$MMW_D_FAMILY" in
    claude)
      # Agent 工具的 model 参数只认档位名，不认完整型号。
      local tier
      case "$MMW_D_MODEL_ID" in
        *opus*) tier="opus" ;;
        *sonnet*) tier="sonnet" ;;
        *haiku*) tier="haiku" ;;
        *fable*) tier="fable" ;;
        *)
          echo "mmw: $MMW_D_MODEL_ID 不在 Agent 工具认识的档位里" >&2
          return 1
          ;;
      esac
      # 这个宿主给插件带来的角色加插件名前缀，形如 mmw:mmw-reviewer。插件名
      # 从 plugin.json 读，改名时跟着变。
      local plugin_name
      plugin_name="$(jq -er .name "$MMW_ROOT/.claude-plugin/plugin.json")"

      printf 'mode: host-tool\n'
      printf 'tool: Agent\n'
      printf 'brief: %s\n' "$MMW_D_BRIEF"
      [ -n "$MMW_D_SKILL_PATH" ] && printf 'skill-path: %s\n' "$MMW_D_SKILL_PATH"
      jq -nc --arg r "$plugin_name:$MMW_D_ROSTER" --arg t "$tier" --arg e "$MMW_D_EFFORT" \
        '{subagent_type: $r, model: $t, effort: $e}' \
        | sed 's/^/params: /'
      ;;
    gpt)
      local report_dir="$MMW_D_CWD/.dispatch"
      mkdir -p "$report_dir"
      local report="$report_dir/${MMW_D_ROLE}-$(basename "$MMW_D_BRIEF" .md).md"
      local sandbox=(--sandbox read-only)
      if [ "$MMW_D_WRITABLE" = "yes" ]; then
        # workspace-write 默认把 .git 锁成只读，工人提交会卡在 index.lock。
        sandbox=(--sandbox workspace-write
                 -c "sandbox_workspace_write.writable_roots=[\"$MMW_D_CWD/.git\"]")
      fi
      local code=0
      codex exec -C "$MMW_D_CWD" --color never \
        "${sandbox[@]}" \
        -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
        -o "$report" \
        - < "$MMW_D_BRIEF" || code=$?
      printf 'mode: executed\n'
      printf 'report: %s\n' "$report"
      printf 'exit: %s\n' "$code"
      return "$code"
      ;;
    *)
      echo "mmw: 认不出模型族 $MMW_D_FAMILY（只有 claude 和 gpt）" >&2
      return 1
      ;;
  esac
}
