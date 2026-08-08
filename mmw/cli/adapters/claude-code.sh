#!/usr/bin/env bash
# Claude Code 宿主：怎么把一个角色变成一次真正的派发。
#
# 这个宿主的会话内 subagent 只能是 Claude，所以派 GPT 必须走 codex exec 外部
# 进程——CLI 自己跑得完，直接跑。派 Claude 走 Agent 工具，CLI 跑不了，只能把
# 参数交给模型去调。
#
# 两条路都不用把方法论路径写进提示词：codex exec 靠 install-agent-skills.sh
# 把技能软链进它自己的技能目录，会话内的 subagent 由 subagent_type 带着技能。
#
# 本文件不做流程判断。它只回答「这个宿主管这个动作叫什么」。
#
# 入参走 MMW_D_* 环境变量，由 cli/mmw 设好。

set -euo pipefail

# 派 codex 时把三个检索工具带上。
#
# 唯一事实来源是插件根的 .mcp.json——Claude Code 直接读它，这里把同一份翻译成
# codex 的配置覆盖项。不另写一份 codex 专用配置：旧实现就是四个 harness 各写一套，
# 结果 Graphify 的接法在两份里是矛盾的，白名单抄了三份还各不相同。
#
# 用 -c 覆盖而不是往 ~/.codex/config.toml 里写：用户那份配置是他自己的，我们只在
# 自己派发的这一次进程里加工具，退出即无痕。
#
# 逐行输出 codex -c 要的 key=value，调用方读进数组。占位符怎么展开（插件根、密钥、
# 默认值）全在 mcp/resolve.py 里，本文件不自己解析——两处解析就是两处维护。
mmw_adapter_mcp_overrides() {
  [ -f "$MMW_ROOT/.mcp.json" ] || return 0
  python3 "$MMW_ROOT/mcp/resolve.py" --format codex
}

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
      # Claude Code 会话内 agent 文件仍是 agents/mmw-reviewer.md；原生多模型宿主
      # 才拆成 mmw-reviewer-gpt / mmw-reviewer-claude。
      local plugin_name roster
      plugin_name="$(jq -er .name "$MMW_ROOT/.claude-plugin/plugin.json")"
      roster="$MMW_D_ROSTER"
      case "$roster" in
        mmw-reviewer-claude) roster="mmw-reviewer" ;;
      esac

      printf 'mode: host-tool\n'
      printf 'tool: Agent\n'
      printf 'task-file: %s\n' "$MMW_D_TASK"
      # Agent 固定后台运行；task 正文进 prompt，与 Pi 的 task 同一概念。
      jq -nc --arg r "$plugin_name:$roster" --arg t "$tier" --arg e "$MMW_D_EFFORT" \
        --rawfile p "$MMW_D_TASK" \
        '{subagent_type: $r, model: $t, effort: $e, prompt: $p, run_in_background: true}' \
        | sed 's/^/params: /'
      ;;
    gpt)
      # 第一次只生成宿主 Bash 工具调用。后台 Bash 再带内部标记进来执行 Codex；
      # 这样后台属性是 adapter 的机械合同，不靠主 agent 记住额外参数。
      if [ "${MMW_INTERNAL_BACKGROUND_DISPATCH:-}" != "1" ]; then
        local command
        printf -v command \
          'cd %q && MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 %q dispatch %q --task %q --cwd %q' \
          "$MMW_D_CWD" "$MMW_ROOT/cli/mmw" "$MMW_D_ROLE" "$MMW_D_TASK" "$MMW_D_CWD"
        printf 'mode: host-tool\n'
        printf 'tool: Bash\n'
        printf 'task-file: %s\n' "$MMW_D_TASK"
        jq -nc --arg c "$command" '{command: $c, run_in_background: true}' \
          | sed 's/^/params: /'
        return
      fi

      local report_dir="$MMW_D_CWD/.dispatch"
      mkdir -p "$report_dir"
      local report
      report="$report_dir/${MMW_D_ROLE}-$(basename "$MMW_D_TASK" .md).md"
      local sandbox=(--sandbox read-only)
      if [ "$MMW_D_WRITABLE" = "yes" ]; then
        # workspace-write 默认把 .git 锁成只读，`worker` 提交会卡在 index.lock。
        sandbox=(--sandbox workspace-write
                 -c "sandbox_workspace_write.writable_roots=[\"$MMW_D_CWD/.git\"]")
      fi
      local mcp=() line
      while IFS= read -r line; do
        [ -n "$line" ] && mcp+=(-c "$line")
      done < <(mmw_adapter_mcp_overrides)
      # Codex 不读 MCP 握手交回的服务器说明（实测：问它「有没有收到说明」，答没有）。
      # 工具挂上了、说明书没到，`worker` 就不知道什么问题该问图、哪两类关系静态分析看不见。
      # 这里把两处唯一事实来源里的纪律取出来拼在提示词前面。取不出来当场失败：那说明
      # 插件自己装坏了，让 `worker` 裸跑比派发失败更糟。
      local preamble
      preamble="$(python3 "$MMW_ROOT/mcp/discipline.py")" || {
        echo "mmw: 检索纪律取不出来，拒绝派一个没有说明书的 worker" >&2
        return 1
      }

      local code=0
      # ${mcp[@]+...}：.mcp.json 缺失时数组为空，macOS 自带的 bash 3.2 在 set -u 下
      # 展开空数组会报 unbound variable，整次派发就废了。工具没有不该拖垮派发本身。
      { printf '%s\n' "$preamble"; cat "$MMW_D_TASK"; } \
      | codex exec -C "$MMW_D_CWD" --color never \
        "${sandbox[@]}" \
        ${mcp[@]+"${mcp[@]}"} \
        -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
        -o "$report" \
        - || code=$?
      printf 'mode: executed\n'
      printf 'report: %s\n' "$report"
      printf 'exit: %s\n' "$code"
      return "$code"
      ;;
    *)
      # 这个宿主只有会话内 Agent 和 codex exec 两条通道，其他模型族无处可发。
      echo "mmw: Claude Code 发不了模型族 ${MMW_D_FAMILY}（只有 claude 和 gpt）" >&2
      echo "mmw: 请在 MMW 源码的 cli/mmw.default.json 中配置该宿主可用的模型，然后重新安装" >&2
      return 1
      ;;
  esac
}
