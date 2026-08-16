#!/usr/bin/env bash
# Cursor 宿主 adapter。
#
# 只读角色与当前任务 worktree 上的可写角色（planner）：技能产物
# 已经写死原生 Task；本文件只在有人仍调用 `mmw dispatch` 时给出兼容返回。
#
# worker / worker-high-risk 必须走 `mmw-cursor-agent --worktree`，由隔离包装拉起
# 独立 CLI。mmw dispatch 不代劳这一条，避免主 agent 在当前会话里把可写实现跑完。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

mmw_adapter_dispatch() {
  case "$MMW_D_FAMILY" in
    gpt|claude|grok) ;;
    *)
      echo "mmw: 认不出模型族 ${MMW_D_FAMILY}（只有 claude、gpt 和 grok）" >&2
      return 1
      ;;
  esac

  case "$MMW_D_ROLE" in
    worker|worker-high-risk)
      echo "mmw: Cursor 的 ${MMW_D_ROLE} 用 mmw-cursor-agent --mmw-role ${MMW_D_ROLE} -p --force --trust --approve-mcps --worktree <结果分支> --worktree-base <当前任务分支> 启动，不走 mmw dispatch" >&2
      return 1
      ;;
  esac

  if [ -n "${MMW_D_RESUME:-}" ]; then
    echo "mmw: Cursor 续跑请执行 mmw-cursor-agent --resume ${MMW_D_RESUME}，并把修复 task 作为提示词" >&2
    return 1
  fi

  printf 'mode: host-tool\n'
  printf 'tool: Task\n'
  printf 'native: ~/.cursor/agents\n'
  printf 'note: model/readonly/is_background 已在 agent 定义里；params 含 prompt 正文\n'
  jq -nc \
    --arg a "$MMW_D_ROSTER" \
    --arg t "$MMW_D_TASK_TEXT" \
    '{subagent_type: $a, prompt: $t}' \
    | sed 's/^/params: /'
}
