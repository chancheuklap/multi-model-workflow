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

进入 worktree 后在该路径继续并运行 `mmw where`。Coordinator 的任务 worktree 由 `prepare.sh` 建立；Pack worker 和 plan writer 的隔离 worktree 由 `worker.sh` 建立，工人 prompt 里钉死该 worktree 绝对路径，工人的所有操作必须落在它下面。所有工作角色都是会话内 Agent 子代理；主线程工作目录不随工人切换。

## 角色花名册

| 角色 | 职责 |
| --- | --- |
| `investigate-topic` | 单 topic 取证 |
| `investigate-synthesizer` | 汇总 topic 证据 |
| `code-explorer` | 探代码边界与数据流 |
| `plan-writer` | 写单份 plan |
| `pack-executor` | 按 plan TDD 落地 |
| `pack-executor-capable` | 高复杂度 plan 落地 |
| `reviewer-design-a` / `reviewer-design-b` | 设计审模型路线 A / B |
| `reviewer-plan-a` / `reviewer-plan-b` | 计划审模型路线 A / B |
| `reviewer-final-a` / `reviewer-final-b` | 终审模型路线 A / B,视角由 dispatch 指定 |

花名册全员已注册为 pi 正式 agent(软链进全局 agents 目录)：model、thinking 与工具白名单以 `agents-roster/<name>.md` frontmatter 为准，派发时直接 `subagent_type: <角色名>`，不另传 model。reviewer 由协调者按 review brief 派；worker/plan writer 由脚本准备 worktree 与 prompt 后由协调者以 `run_in_background` 派。强判断咨询用 advisor 工具(零参数，自动转发全对话)，不占花名册编制。

无人值守角色不能向用户提问。缺输入时返回结构化 blocker，由主线程处置。

final review 固定并行四个 Agent：A、B 两种模型分别各审基线1和基线2。

## Worker

`mmw worker dispatch` 为新 Pack 创建 Git worktree、组工人 prompt、记派发账本，并打印派发指令；协调者照指令在会话内派 `Agent(subagent_type=pack-executor,run_in_background=true)`，记下 agent id。`plan-dispatch` 同理，使用临时隔离 worktree。工具白名单由已注册角色的 frontmatter 提供，不再经命令行传递。

工人完成(会话内收到后台 agent 回执)后过机器边界门：

- 写码：`mmw worker verify --worktree <wt>`(核 docs 边界)
- 写计划：`mmw worker verify --plan <plan> --worktree <wt>`(核越界，过门才原子发布 plan 与 issue `Small issues`)

修复使用 `worker resume` 或 `plan-resume`：脚本准备 resume prompt，同会话用 `Agent(resume=<原 agent id>)` 续接原上下文；跨会话(agent id 已失效)重派同角色新 agent，靠 worktree 已有提交对齐进度。通过后主线程再亲验 diff、提交和测试。

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
