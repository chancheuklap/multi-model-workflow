# Droid Runtime Contract

## 路径

| 项 | 固定值 |
| --- | --- |
| 状态平面 | `.factory/multi-model-workflow/` |
| worktree 根 | `.factory/worktrees/<slug>` |
| worker 分支 | `worker/<worktree-name>` |
| 插件根 | hook 内 `${DROID_PLUGIN_ROOT}`；主线程由 `mmw` 绝对路径反推 |

`task.json`(含 `note` 书签与 `approval` 设计确认)、`loop-state.json`、进度板、派发账本和 review brief 都在状态平面。

## 工具

| 语义 | Droid 工具 |
| --- | --- |
| 壳命令 | `Execute` |
| 创建或编辑文件 | `Create`、`Edit`、`ApplyPatch` |
| 结构化问用户 | `AskUser` |
| 子代理 | `Task` |
| 文件检索 | `Read`、`Grep`、`Glob`、`LS` |
| 外部检索 | `WebSearch`、`FetchUrl` |

进入 worktree 后在该路径继续并运行 `mmw where`。Droid 的 `--worktree` 只能在新会话启动时创建 worktree，所以当前 Coordinator 会话仍由 `prepare.sh` 建立并交接任务 worktree；后台 Pack worker 使用 `droid exec --worktree --worktree-dir`。Task 子代理只做当前会话内的调查、咨询和审查,不负责切换主线程工作目录。

## Custom Droids

| droid | 职责 |
| --- | --- |
| `investigate-topic` | 单 topic 取证 |
| `investigate-synthesizer` | 汇总 topic 证据 |
| `code-explorer` | 探代码边界与数据流 |
| `decision-advisor` | 实质工作前/卡住/完成后的强判断 |
| `plan-writer` | 写单份 plan |
| `pack-executor` | 按 plan TDD 落地 |
| `pack-executor-capable` | 高复杂度 plan 落地 |
| `reviewer-design-a` / `reviewer-design-b` | 设计审模型路线 A / B |
| `reviewer-plan-a` / `reviewer-plan-b` | 计划审模型路线 A / B |
| `reviewer-final-a` / `reviewer-final-b` | 终审模型路线 A / B,视角由 dispatch 指定 |

model、reasoningEffort 与工具白名单以各 droid 文件(`droids/<name>.md`)frontmatter 为准,此处不重复声明(防双写漂移)。

子代理非交互，不能调用 `AskUser`，也不能再派 Task。缺输入时返回结构化 blocker，由主线程处置。

final review 由 `mmw review start` 分档：small-change/bug 派一个 A 路 Task 覆盖两基线；develop 无 capable plan 且 diff 不超过阈值时派 A/B 各一路，其余及风险数据不全时派 A/B 各两路。

## Worker

`mmw worker dispatch` 为新 Pack 使用 Droid 原生 worktree；传入已存在任务 worktree 的返修继续使用 `--cwd`。`plan-dispatch` 沿用临时 Git worktree，边界门通过后只发布指定 plan 与 issue `Small issues`。脚本按实际模型 tool inventory 只开放读写、检索、Skill 和 Execute，关闭 Task、web、MCP、mission 与其它无关工具；账本持久化 PID、结果文件、工具策略和 session ID。

主线程轮询：

- 写码：`mmw worker status --worktree <wt>`
- 写计划：`mmw worker status --plan <plan> --worktree <wt>`

`status` 在完成时自动执行机器边界检查并打印最后回执。修复使用 `worker resume` 或 `plan-resume`，脚本通过账本 session ID 调用 `droid exec --session-id` 续接原上下文。通过后主线程再亲验 diff、提交和测试。

## 审闸

主线程运行 `mmw review start`，读取生成的 `review-brief.md` 并直接派 reviewer droids。findings 原样落盘 `docs/reviews/<slug>-<stage>.md` 并逐条亲验、文末写总 verdict；审闸 `handoff pass` 时引擎核该文件存在且含 verdict，没有留痕不放行。

## Hooks

| 事件 | matcher | 脚本 |
| --- | --- | --- |
| SessionStart | 无 | `session-triage.sh` |
| PreToolUse | `Execute` | `guard-redline.sh` |
| PostToolUse | `Execute` | `record-step.sh` |

插件 hook 只引用 `${DROID_PLUGIN_ROOT}`。脚本自行筛选命令，不依赖额外 matcher 字段。

设计确认是唯一人闸：用户敲 `/approve-design` → `mmw approve` 盖承重文档指纹、attendance 切 afk 并推进；用户口头同意不算过门。承重文档改动后审闸 pass 硬停 `approval_stale`，重跑 `mmw approve` 重盖（RE-APPROVED）。

## 安全

- Worker 禁改 `docs/`。
- 计划工人只准改自己的 plan 与对应 issue。
- 审者是劳动力，不是信源。
- 本地 merge 可自主执行；push、远端合并和部署必须经过用户权限确认。
- 无人值守时所有 agent 都不得向用户提问，硬停必须写入磁盘账本和进度板。
