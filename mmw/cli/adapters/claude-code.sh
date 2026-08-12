#!/usr/bin/env bash
# Claude Code 宿主：怎么把一个角色变成一次真正的派发。
#
# 这个宿主的会话内 subagent 只能是 Claude，所以派 GPT 必须走 codex exec 外部
# 进程——CLI 自己跑得完，直接跑。派 Claude 走 Agent 工具，CLI 跑不了，只能把
# 参数交给模型去调。
#
# 两条路都不写方法论的文件路径，只写技能名。技能已经装进对方的 harness：
# codex exec 那边由 install-agent-skills.sh 软链进它自己的技能目录，会话内
# subagent 那边由 plugin.json 的 skills 列表装好。派发只负责说清楚该调用哪个。
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
      # Agent 固定后台运行；task 正文进 prompt，与 Pi 的 task 同一概念。
      jq -nc --arg r "$plugin_name:$roster" --arg t "$tier" --arg e "$MMW_D_EFFORT" \
        --arg p "$MMW_D_TASK_TEXT" \
        '{subagent_type: $r, model: $t, effort: $e, prompt: $p, run_in_background: true}' \
        | sed 's/^/params: /'
      ;;
    gpt)
      # 第一次只生成宿主 Bash 工具调用。后台 Bash 再带内部标记进来执行 Codex；
      # 这样后台属性是 adapter 的机械合同，不靠主 agent 记住额外参数。
      if [ "${MMW_INTERNAL_BACKGROUND_DISPATCH:-}" != "1" ]; then
        local command issue_arg="" task_json
        if [ -n "${MMW_D_ISSUE:-}" ]; then
          printf -v issue_arg ' --issue %q' "$MMW_D_ISSUE"
        fi
        # Bash 3.2 的 printf %q 会破坏多字节正文。先变成只含 ASCII 的 JSON 字符串，
        # 后台命令再用 jq 解码到标准输入。jq -j 不追加换行。
        task_json="$(printf '%s' "$MMW_D_TASK_TEXT" | jq -Rsa .)"
        printf -v command \
          'cd %q && printf %%s %q | jq -rj . | MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 %q dispatch %q --cwd %q%s' \
          "$MMW_D_CWD" "$task_json" "$MMW_ROOT/cli/mmw" "$MMW_D_ROLE" "$MMW_D_CWD" "$issue_arg"
        printf 'mode: host-tool\n'
        printf 'tool: Bash\n'
        jq -nc --arg c "$command" '{command: $c, run_in_background: true}' \
          | sed 's/^/params: /'
        return
      fi

      # 进度日志是派发结束后的诊断材料。落点只由 artifact path 回答。
      # 主检出没有工作名时算不出落点。此时明确说明不写日志，并继续派发。
      local log_dir="" log="" log_tmp="" timestamp
      local -a artifact_args=(artifact path scratch --sub dispatch --absolute)
      if [ -n "${MMW_D_ISSUE:-}" ]; then
        artifact_args+=(--issue "$MMW_D_ISSUE")
      fi
      if log_dir="$(
        cd "$MMW_D_CWD" \
          && "$MMW_ROOT/cli/mmw" "${artifact_args[@]}" 2>/dev/null
      )"; then
        mkdir -p "$log_dir"
        timestamp="$(date +%Y%m%d-%H%M%S)"
        log_tmp="$(mktemp "$log_dir/${MMW_D_ROLE}-${timestamp}-XXXXXX")" || {
          echo "mmw: 不能创建派发进度日志" >&2
          return 1
        }
        log="${log_tmp}.log"
        mv "$log_tmp" "$log" || {
          echo "mmw: 不能创建派发进度日志" >&2
          return 1
        }
      else
        log_dir=""
        echo "mmw: 派发进度日志算不出落点时不写日志，派发照常进行" >&2
      fi
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

      # 方法论同理：技能装在 ~/.codex/skills 里，但没人叫它去用，它就不会用。
      # 技能名取自 roles.json 的 skill 字段。该字段为空表示这个角色没有固定
      # 方法论技能，这次用什么由 task 指定，那就不加这一句。
      if [ -n "${MMW_D_SKILL:-}" ]; then
        preamble="## Method

Call the \`$MMW_D_SKILL\` skill before you start. It holds the method for this task.

$preamble"
      fi

      # 算得出日志落点时只挡 stderr。
      #
      # codex exec 把进度流式写到 stderr，只把最终消息打到 stdout。
      # stdout 就是这次派发要交回的报告，调用方原样收下。stderr 是过程噪音，
      # 算得出日志落点时把它留作失败诊断材料。
      #
      # 别写成 2>&1：那会把报告一起吞进日志，调用方拿到的只剩状态行。
      #
      # 后台属性由上面那段定死，理由是不该指望主 agent 记住额外参数。stderr 往哪去
      # 是同一类执行细节，同样定死在这里，不写进调用方要记的参数。
      local code=0
      # ${mcp[@]+...}：.mcp.json 缺失时数组为空，macOS 自带的 bash 3.2 在 set -u 下
      # 展开空数组会报 unbound variable，整次派发就废了。工具没有不该拖垮派发本身。
      if [ -n "$log" ]; then
        { printf '%s\n' "$preamble"; printf '%s' "$MMW_D_TASK_TEXT"; } \
        | codex exec -C "$MMW_D_CWD" --color never \
          "${sandbox[@]}" \
          ${mcp[@]+"${mcp[@]}"} \
          -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
          - 2> "$log" || code=$?
      else
        { printf '%s\n' "$preamble"; printf '%s' "$MMW_D_TASK_TEXT"; } \
        | codex exec -C "$MMW_D_CWD" --color never \
          "${sandbox[@]}" \
          ${mcp[@]+"${mcp[@]}"} \
          -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
          - || code=$?
      fi
      printf 'mode: executed\n'
      # 成功的进度日志没人会看，留着只会堆积：一次两百万字节，十次就是二十兆。
      # 失败时它是唯一的诊断材料，保留并把路径交出去。
      if [ "$code" -eq 0 ] && [ -n "$log" ]; then
        rm -f "$log"
        # 这次派发没留下任何东西时把目录也收掉；里面还有别人的日志就留着。
        rmdir "$log_dir" 2>/dev/null || true
      elif [ "$code" -ne 0 ] && [ -n "$log" ]; then
        printf 'log: %s\n' "$log"
      fi
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
