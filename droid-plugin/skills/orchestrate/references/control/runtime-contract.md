# Droid Runtime Contract

## 路径

| 项 | 固定值 |
| --- | --- |
| 状态平面 | `.factory/multi-model-workflow/` |
| worktree 根 | `.factory/worktrees/<slug>` |
| worker 分支 | `worker/<worktree-name>` |
| 插件根 | hook 内 `${DROID_PLUGIN_ROOT}`；主线程由 `mmw` 绝对路径反推 |

`task.json`、`loop-state.json`、进度板、design checkpoint、派发账本和 review brief 都在状态平面。

## 工具

| 语义 | Droid 工具 |
| --- | --- |
| 壳命令 | `Execute` |
| 创建或编辑文件 | `Create`、`Edit`、`ApplyPatch` |
| 结构化问用户 | `AskUser` |
| 子代理 | `Task` |
| 文件检索 | `Read`、`Grep`、`Glob`、`LS` |
| 外部检索 | `WebSearch`、`FetchUrl` |

进入 worktree 后在该路径继续并运行 `mmw where`。Droid 没有 Claude Code 的同名切换工具；等价入口是启动时 `droid --cwd <path>`、会话内 `/cwd <path>`，或让 Droid 自建隔离分支的 `droid -w <branch> [--worktree-dir <path>]`。本插件需要持久状态和固定目录,因此 worker 统一使用 `droid exec --cwd <已建 worktree>`。Task 子代理只做当前会话内的调查、咨询和审查,不负责切换主线程工作目录。

## Custom Droids

| droid | 职责 | model | 工具 |
| --- | --- | --- | --- |
| `investigate-topic` | 单 topic 取证 | `minimax-m3` | 只读、web、Execute |
| `code-explorer` | 探代码边界与数据流 | `kimi-k2.7-code` | 只读、受限 Execute |
| `decision-advisor` | 实质工作前/卡住/完成后的强判断 | `gemini-3.1-pro-preview` | 只读、web、受限 Execute |
| `plan-writer` | 写单份 plan | `gpt-5.6-terra` | 读写、检索、Execute |
| `pack-executor` | 按 plan TDD 落地 | `glm-5.2` | 读写、检索、Execute |
| `pack-executor-capable` | 高复杂度 plan 落地 | `gemini-3.1-pro-preview` | 读写、检索、Execute |
| `reviewer-design-a/b` | 设计审两轴 | `claude-opus-4-8` | 只读、受限 Execute |
| `reviewer-plan-a/b` | 计划审两轴 | `claude-opus-4-8` | 只读、受限 Execute |
| `reviewer-final-a` | 终审模型路线 A,视角由 dispatch 指定 | `gpt-5.6-terra` | 只读、受限 Execute |
| `reviewer-final-b` | 终审模型路线 B,视角由 dispatch 指定 | `claude-opus-4-8` | 只读、受限 Execute |

子代理非交互，不能调用 `AskUser`，也不能再派 Task。缺输入时返回结构化 blocker，由主线程处置。

## Worker

`mmw worker dispatch` 为落地 Pack 创建长期 worktree；`plan-dispatch` 为每个并行 writer 创建临时隔离 worktree，边界门通过后只把指定 plan 与 issue `Small issues` 发布回任务 worktree并清理。两者都记录边界基线、prompt 与派发账本，并用 `droid exec --cwd --auto medium` 后台启动对应模型。脚本按实际模型 tool inventory 只开放读写、检索、Skill 和 Execute，关闭 Task、web、MCP、mission 与其它无关工具；账本持久化 PID、结果文件、工具策略和 session ID。

主线程轮询：

- 写码：`mmw worker status --worktree <wt>`
- 写计划：`mmw worker status --plan <plan> --worktree <wt>`

`status` 在完成时自动执行机器边界检查并打印最后回执。修复使用 `worker resume` 或 `plan-resume`，脚本通过账本 session ID 调用 `droid exec --session-id` 续接原上下文。通过后主线程再亲验 diff、提交和测试。

## 审闸

主线程运行 `mmw review start`，读取生成的 `review-brief.md` 并直接派 reviewer droids。findings 原样落盘，主线程逐条亲验和收敛；`loop exit-check` 未返回 `DONE` 时不得 handoff pass。

## Hooks

| 事件 | matcher | 脚本 |
| --- | --- | --- |
| SessionStart | 无 | `session-triage.sh` |
| UserPromptSubmit | 无 | `prompt-anchor.sh` |
| PreToolUse | `Execute` | `guard-redline.sh` |
| PostToolUse | `Execute` | `record-step.sh` |

插件 hook 只引用 `${DROID_PLUGIN_ROOT}`。脚本自行筛选命令，不依赖额外 matcher 字段。

UserPromptSubmit 读取官方 hook payload 的 `prompt`。只有 prompt 精确等于 `确认设计 MMW-APPROVE:<id>` 或 token 本身，且报告指纹仍匹配时，才原子批准当前 design checkpoint；任意其它消息只注入流程锚，不构成批准。不存在公开的 `mmw checkpoint approve` 命令。

## 安全

- Worker 禁改 `docs/`。
- 计划工人只准改自己的 plan 与对应 issue。
- 审者是劳动力，不是信源。
- 本地 merge 可自主执行；push、远端合并和部署必须经过用户权限确认。
- 无人值守时所有 agent 都不得向用户提问，硬停必须写入磁盘账本和进度板。
