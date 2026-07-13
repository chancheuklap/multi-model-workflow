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

进入 worktree 后在该路径继续并运行 `mmw where`。Task 只用于当前会话内的短只读调查、咨询和审查，按当前工具合同同步返回结果，不假设后台任务、task ID 或 resume。

## Custom Droids

| droid | 职责 | model | 工具 |
| --- | --- | --- | --- |
| `investigate-topic` | 单 topic 取证 | `minimax-m3` | 只读、web、Execute |
| `code-explorer` | 探代码边界与数据流 | `kimi-k2.7-code` | read-only |
| `decision-advisor` | 关键分叉第二意见 | `gemini-3.1-pro-preview` | read-only |
| `plan-writer` | 写单份 plan | `gpt-5.6-terra` | 读写、检索、Execute |
| `pack-executor` | 按 plan TDD 落地 | `glm-5.2` | 读写、检索、Execute |
| `pack-executor-capable` | 高复杂度 plan 落地 | `gemini-3.1-pro-preview` | 读写、检索、Execute |
| `reviewer-design-a/b` | 设计审两轴 | `claude-opus-4-8` | read-only |
| `reviewer-plan-a/b` | 计划审两轴 | `claude-opus-4-8` | read-only |
| `reviewer-final-a` | 最终审基线 A | `gpt-5.6-terra` | read-only |
| `reviewer-final-b` | 最终审基线 B | `claude-opus-4-8` | read-only |

子代理非交互，不能调用 `AskUser`，也不能再派 Task。缺输入时返回结构化 blocker，由主线程处置。

## Worker

`mmw worker dispatch` 和 `plan-dispatch` 创建 worktree、边界基线、prompt 与派发账本，并用 `droid exec --cwd` 后台启动对应模型。账本持久化 PID、结果文件和 session ID。

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
