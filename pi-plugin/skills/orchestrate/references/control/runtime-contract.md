# pi Runtime Contract

## 路径

| 项 | 固定值 |
| --- | --- |
| 状态平面 | `.pi/multi-model-workflow/` |
| worktree 根 | `.pi/worktrees/<slug>` |
| worker 分支 | `worker/<worktree-name>` |
| 插件根 | hook 内 `${MMW_PLUGIN_ROOT}`；主线程由 `mmw` 绝对路径反推 |

`task.json`(含 `note` 书签与 `approval` 设计确认)、`loop-state.json`、进度板、派发账本和 review brief 都在状态平面。

## 工具

| 语义 | pi 工具 |
| --- | --- |
| 壳命令 | `bash` |
| 创建或编辑文件 | `write`、`edit` |
| 结构化问用户 | `ask_user` |
| 子代理 | `Agent`（pi-subagents） |
| 文件检索 | `read`、`grep`、`find`、`ls` |
| 外部检索 | `web_search`、`fetch_content` |

进入 worktree 后在该路径继续并运行 `mmw where`。Coordinator 的任务 worktree 由 `prepare.sh` 建立；后台 Pack worker 和 plan writer 的隔离 worktree 由 `worker.sh` 建立，再以该目录为 cwd 启动 `pi -p`。Agent 子代理只做当前会话内的咨询和审查，不负责切换主线程工作目录。

## 角色花名册

| 角色 | 职责 |
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

model、reasoning effort 与工具白名单以 `agents-roster/<name>.md` frontmatter 为准，此处不重复声明。worker/plan writer 由脚本把角色正文渲染进无头系统提示词；reviewer 由协调者按 review brief 用 Agent 工具派发，并显式传花名册中的 model。

无人值守角色不能向用户提问。缺输入时返回结构化 blocker，由主线程处置。

final review 固定并行四个 Agent：A、B 两种模型分别各审基线1和基线2。

## Worker

`mmw worker dispatch` 为新 Pack 创建 Git worktree；返修从派发账本找到原 worktree。`plan-dispatch` 使用临时 Git worktree，边界门通过后只发布指定 plan 与 issue `Small issues`。脚本通过 pi 的 `-t` 工具白名单只开放读写、检索和 bash；账本持久化 PID、结果文件、工具策略和 session ID。

主线程轮询：

- 写码：`mmw worker status --worktree <wt>`
- 写计划：`mmw worker status --plan <plan> --worktree <wt>`

`status` 在完成时自动执行机器边界检查并打印最后回执。修复使用 `worker resume` 或 `plan-resume`，脚本通过账本 session ID 调用 `pi -p --session-id` 续接原上下文。通过后主线程再亲验 diff、提交和测试。

## 审闸

主线程运行 `mmw review start`，读取生成的 `review-brief.md` 并直接派 reviewer Agent。findings 原样落盘 `docs/reviews/<slug>-<stage>.md` 并逐条亲验、文末写总 verdict；审闸 `handoff pass` 时引擎核该文件存在且含 verdict，没有留痕不放行。

## Hooks

| 事件 | matcher | 脚本 |
| --- | --- | --- |
| `session_start` / `session_compact` → `before_agent_start` | 无 | `session-triage.sh`（每次开场或压缩后注入一次） |
| `tool_call` | `bash` | `guard-redline.sh` |
| `tool_result` | `bash` | `record-step.sh` |

扩展从自身 `import.meta.url` 解析插件根，并以 `MMW_PLUGIN_ROOT` 环境变量传给脚本。脚本自行筛选命令。

设计确认是唯一人闸：用户敲 `/approve-design` → `mmw approve` 盖承重文档指纹、attendance 切 afk 并推进；用户口头同意不算过门。承重文档改动后审闸 pass 硬停 `approval_stale`，重跑 `mmw approve` 重盖（RE-APPROVED）。

## 安全

- Worker 禁改 `docs/`。
- 计划工人只准改自己的 plan 与对应 issue。
- 审者是劳动力，不是信源。
- 本地 merge 可自主执行；push、远端合并和部署必须经过用户权限确认。
- 无人值守时所有 agent 都不得向用户提问，硬停必须写入磁盘账本和进度板。
