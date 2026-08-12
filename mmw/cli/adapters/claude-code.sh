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

# 可写角色要能提交，`writable_roots` 就得覆盖 git 真正要写的目录。
#
# 不要拼 `<cwd>/.git`。那一行只对「`.git` 是目录」的普通仓库成立，而 MMW 派活的主
# 路径是 `mmw task new` 建的 linked worktree：那里的 `.git` 是个文件，里面写着
# `gitdir: <主仓库>/.git/worktrees/<名字>`。`git commit` 的 `index.lock` 落在那个
# 目录里，既不在工作目录下也不在拼出来的路径下，于是每一次提交都被沙箱拒掉。
#
# 改成问 git 自己要两条绝对路径：`--absolute-git-dir` 是这棵树的 Git 目录，`index`
# 与 `HEAD` 在那里；`--git-common-dir` 是共用的，`objects` 与 `refs` 在那里。普通
# 仓库里两条指到同一个 `.git`，那时只输出一条。
#
# 输出是一行 JSON 数组，直接嵌进 codex 的 `-c` 覆盖值。
mmw_adapter_writable_roots() {
  local cwd="$1" gitdir commondir
  gitdir="$(cd "$cwd" && git rev-parse --absolute-git-dir 2>/dev/null)" || {
    echo "mmw: $cwd 里问不出 Git 目录，可写角色提交会被沙箱拒" >&2
    return 1
  }
  commondir="$(cd "$cwd" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
    echo "mmw: $cwd 里问不出共用 Git 目录，可写角色提交会被沙箱拒" >&2
    return 1
  }
  if [ "$gitdir" = "$commondir" ]; then
    jq -nc --arg d "$gitdir" '[$d]'
  else
    jq -nc --arg d "$gitdir" --arg c "$commondir" '[$d, $c]'
  fi
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

      # 句柄让这个 subagent 可寻址：修复轮 SendMessage 到同名即恢复原生产者。
      # 名字由角色加 task 正文摘要确定性生成。旧接口用 task 文件名，新接口没有 task
      # 文件，正文摘要同样确定性——同一份 task 永远算出同一个名字，上下文压缩后
      # 只要还有那份正文就能重建，不用存盘。
      local handle
      handle="${MMW_D_ROLE}-$(printf '%s' "$MMW_D_TASK_TEXT" | shasum -a 256 | cut -c1-12)"

      # 恢复：把修复 task 用 SendMessage 发回原 subagent，上下文完整续跑。
      # 收件名用调用方给的句柄，那是原派发返回的 handle: 行原文。
      if [ -n "${MMW_D_RESUME:-}" ]; then
        printf 'mode: host-tool\n'
        printf 'tool: SendMessage\n'
        jq -nc --arg to "$MMW_D_RESUME" --arg m "$MMW_D_TASK_TEXT" \
          '{to: $to, message: $m}' \
          | sed 's/^/params: /'
        return
      fi

      printf 'mode: host-tool\n'
      printf 'tool: Agent\n'
      printf 'handle: %s\n' "$handle"
      # Agent 固定后台运行；task 正文进 prompt，与 Pi 的 task 同一概念。
      jq -nc --arg r "$plugin_name:$roster" --arg t "$tier" --arg e "$MMW_D_EFFORT" \
        --arg n "$handle" \
        --arg p "$MMW_D_TASK_TEXT" \
        '{subagent_type: $r, model: $t, effort: $e, name: $n, prompt: $p, run_in_background: true}' \
        | sed 's/^/params: /'
      ;;
    gpt)
      # 第一次只生成宿主 Bash 工具调用。后台 Bash 再带内部标记进来执行 Codex；
      # 这样后台属性是 adapter 的机械合同，不靠主 agent 记住额外参数。
      if [ "${MMW_INTERNAL_BACKGROUND_DISPATCH:-}" != "1" ]; then
        local command issue_arg="" resume_arg="" task_json
        if [ -n "${MMW_D_ISSUE:-}" ]; then
          printf -v issue_arg ' --issue %q' "$MMW_D_ISSUE"
        fi
        if [ -n "${MMW_D_RESUME:-}" ]; then
          printf -v resume_arg ' --resume %q' "$MMW_D_RESUME"
        fi
        # Bash 3.2 的 printf %q 会破坏多字节正文。先变成只含 ASCII 的 JSON 字符串，
        # 后台命令再用 jq 解码到标准输入。jq -j 不追加换行。
        task_json="$(printf '%s' "$MMW_D_TASK_TEXT" | jq -Rsa .)"
        printf -v command \
          'cd %q && printf %%s %q | jq -rj . | MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 %q dispatch %q --cwd %q%s%s' \
          "$MMW_D_CWD" "$task_json" "$MMW_ROOT/cli/mmw" "$MMW_D_ROLE" "$MMW_D_CWD" "$issue_arg" "$resume_arg"
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
      local sandbox=(--sandbox read-only) writable_roots=""
      if [ "$MMW_D_WRITABLE" = "yes" ]; then
        # workspace-write 默认把 Git 目录锁成只读，`worker` 提交会卡在 index.lock。
        writable_roots="$(mmw_adapter_writable_roots "$MMW_D_CWD")" || return 1
        sandbox=(--sandbox workspace-write
                 -c "sandbox_workspace_write.writable_roots=$writable_roots")
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
      # 句柄是 codex 的 thread_id，修复轮 `--resume` 用它恢复原生产者。它不像 claude
      # 族的名字那样算得出来，所以必须存盘：主 agent 的上下文压缩之后，派发输出里那一行
      # 就没了。落在派发进度目录，与进度日志同一类过程材料；文件名用角色加 task 正文
      # 摘要，同一份 task 永远指向同一个句柄文件。算不出落点时不存，只在输出里给一次。
      local handle_stem session_file=""
      handle_stem="${MMW_D_ROLE}-$(printf '%s' "$MMW_D_TASK_TEXT" | shasum -a 256 | cut -c1-12)"
      if [ -n "$log_dir" ]; then
        session_file="$log_dir/${handle_stem}.session"
      fi

      # --json 把事件流打到标准输出，第一个事件 thread.started 带 thread_id。
      # 标准输出这条通道于是被事件流占了，报告改由 -o 的临时文件承载，读出来再原样
      # 打到标准输出——对调用方来说合同没变，报告仍然走标准输出，仓库里也不留文件。
      # 两个临时文件都在系统临时目录，用完就删。
      local report_tmp events_tmp
      report_tmp="$(mktemp "${TMPDIR:-/tmp}/mmw-dispatch-report.XXXXXX")" || {
        echo "mmw: 不能创建派发报告的临时文件" >&2
        return 1
      }
      events_tmp="$(mktemp "${TMPDIR:-/tmp}/mmw-dispatch-events.XXXXXX")" || {
        rm -f "$report_tmp"
        echo "mmw: 不能创建派发事件流的临时文件" >&2
        return 1
      }

      local code=0
      # ${mcp[@]+...}：.mcp.json 缺失时数组为空，macOS 自带的 bash 3.2 在 set -u 下
      # 展开空数组会报 unbound variable，整次派发就废了。工具没有不该拖垮派发本身。
      if [ -n "${MMW_D_RESUME:-}" ]; then
        # 恢复原生产者。`codex exec resume` 没有 -C、--sandbox、--color 三个参数，
        # 所以工作目录靠 cd 进去，sandbox 用 -c 配置覆盖传同一档。选项必须排在
        # 句柄之前，排后面会被当成提示词。修复 task 从标准输入进；不再拼 preamble，
        # 上下文还在，那份纪律它已经读过。
        local resume_cfg=(-c 'sandbox_mode="read-only"')
        if [ "$MMW_D_WRITABLE" = "yes" ]; then
          resume_cfg=(-c 'sandbox_mode="workspace-write"'
                      -c "sandbox_workspace_write.writable_roots=$writable_roots")
        fi
        cd "$MMW_D_CWD" || { rm -f "$report_tmp" "$events_tmp"; return 1; }
        if [ -n "$log" ]; then
          printf '%s' "$MMW_D_TASK_TEXT" \
          | codex exec resume --json \
            "${resume_cfg[@]}" \
            ${mcp[@]+"${mcp[@]}"} \
            -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
            -o "$report_tmp" \
            "$MMW_D_RESUME" - > "$events_tmp" 2> "$log" || code=$?
        else
          printf '%s' "$MMW_D_TASK_TEXT" \
          | codex exec resume --json \
            "${resume_cfg[@]}" \
            ${mcp[@]+"${mcp[@]}"} \
            -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
            -o "$report_tmp" \
            "$MMW_D_RESUME" - > "$events_tmp" || code=$?
        fi
      elif [ -n "$log" ]; then
        { printf '%s\n' "$preamble"; printf '%s' "$MMW_D_TASK_TEXT"; } \
        | codex exec -C "$MMW_D_CWD" --color never --json \
          "${sandbox[@]}" \
          ${mcp[@]+"${mcp[@]}"} \
          -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
          -o "$report_tmp" \
          - > "$events_tmp" 2> "$log" || code=$?
      else
        { printf '%s\n' "$preamble"; printf '%s' "$MMW_D_TASK_TEXT"; } \
        | codex exec -C "$MMW_D_CWD" --color never --json \
          "${sandbox[@]}" \
          ${mcp[@]+"${mcp[@]}"} \
          -m "$MMW_D_MODEL_ID" -c "model_reasoning_effort=\"$MMW_D_EFFORT\"" \
          -o "$report_tmp" \
          - > "$events_tmp" || code=$?
      fi

      # 报告原样打到标准输出，位置与顺序跟以前一样：报告在前，状态行在后。
      cat "$report_tmp"

      local thread_id=""
      thread_id="$(jq -r 'select(.type == "thread.started") | .thread_id' "$events_tmp" 2>/dev/null | head -1)"
      rm -f "$report_tmp" "$events_tmp"

      printf 'mode: executed\n'
      if [ -n "$thread_id" ]; then
        if [ -n "$session_file" ]; then
          printf '%s\n' "$thread_id" > "$session_file"
        fi
        printf 'session: %s\n' "$thread_id"
      else
        echo "mmw: 这次派发没取到 thread_id，修复轮恢复不了这个生产者" >&2
      fi
      # 成功的进度日志没人会看，留着只会堆积：一次两百万字节，十次就是二十兆。
      # 失败时它是唯一的诊断材料，保留并把路径交出去。
      if [ "$code" -eq 0 ] && [ -n "$log" ]; then
        rm -f "$log"
        # 句柄文件是修复轮要用的材料，不跟着日志一起删，所以成功的派发通常仍在这个
        # 目录里留下一份 `.session`——那时下面这行收不掉目录，也不该收掉。只有连
        # thread_id 都没取到、目录确实空了的时候它才生效。
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
