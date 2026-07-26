# Cursor Runtime Contract

## 路径

| 项 | 固定值 |
| --- | --- |
| 状态平面 | `.cursor/multi-model-workflow/` |
| worktree 根 | `.cursor/worktrees/<slug>`（或用户用 Cursor UI 先建的悬空 wt，经 `mmw task adopt` 挂上） |
| worker 分支 | `worker/<worktree-name>` |
| 插件根 | hook 内 `${CURSOR_PLUGIN_ROOT}`；主线程由 `mmw` 绝对路径反推 |

`task.json`(含 `note` 书签与 `approval` 设计确认)、`loop-state.json`、进度板、派发账本和 review brief 都在状态平面。

## 工具

| 语义 | Cursor 工具 |
| --- | --- |
| 壳命令 | `Shell` |
| 创建或编辑文件 | 编辑器写工具 / `ApplyPatch`（以当前 Cursor 合同为准） |
| 结构化问用户 | `AskQuestion` |
| 子代理 | `Task`（`subagent_type`=花名册角色名；多轮用同一 agent id 的 `resume`） |
| 文件检索 | `Read`、`Grep`、`Glob`、`LS` |
| 外部检索 | `WebSearch`、`WebFetch` |

任务 worktree：用户可用 Cursor UI 先建悬空 checkout，再跑 `mmw task adopt` 挂 slug 分支与 manifest；续跑时用 Open Folder / 工作区切进该路径并跑 `mmw where`。Coordinator 也可由 `prepare.sh` 建 wt。Pack worker 和 plan writer 的隔离 worktree 由 `worker.sh` 建立，工人 prompt 里钉死该 worktree 绝对路径，工人的所有操作必须落在它下面。工作角色都是会话内 Task 子代理；主线程工作目录不随工人切换。

MMW 建立上述 worktree 后，优先调用目标仓库的 `.cursor/worktree-init.sh`；没有项目 hook 时调用用户级 `pi-graphify-ensure`，按来源与目标工作树内容复用或重建原生图谱。两条初始化路径都不污染机器 stdout，失败会明确告警但不阻断任务；首次复杂检索会再次 ensure。不探测 `.pi` / `.claude` / `.factory` 宿主状态目录（`pi-graphify-ensure` 是 PATH 上的图谱生命周期 CLI）。

## 角色花名册

| 角色 | 职责 |
| --- | --- |
| `investigate-topic` | 单 topic 取证 |
| `investigate-synthesizer` | 汇总 topic 证据 |
| `code-explorer` | 探代码边界与数据流 |
| `advisor` | 强判断自由人（rpiv 提示词；不占编制） |
| `plan-writer` | 写单份 plan |
| `pack-executor` | 按 plan TDD 落地 |
| `pack-executor-capable` | 高复杂度 plan 落地 |
| `reviewer-design-a` / `reviewer-design-b` | 设计审模型路线 A / B |
| `reviewer-plan-a` / `reviewer-plan-b` | 计划审模型路线 A / B |
| `reviewer-final-a` / `reviewer-final-b` | 终审模型路线 A / B,视角由 dispatch 指定 |

花名册以插件内 `agents/<name>.md` frontmatter 为准（model / 工具白名单）；派发时 `Task({subagent_type:"<角色名>", ...})`，不另传 model。

**后台派发硬规则（mmw 角色一律不阻塞主线程前台）**：
- `plan-writer` / `pack-executor` / `pack-executor-capable`：**必须** `run_in_background: true`（脚本打印的指令已带；协调者照抄，禁止改成前台阻塞）。
- 全部 `reviewer-*`（design/plan/final 双轴）：**必须** 并行后台 Task；禁止前台串行卡住主线程。主线程收齐回执后再亲验 findings。
- 短探路（如 `code-explorer` 单次只读）可前台；一旦预估超过约一分钟或会并行多个，改后台。
- 禁止对 mmw 花名册重角色使用会阻塞主会话的前台派发。

worker/plan writer 由脚本准备 worktree 与 prompt 后打印 Task DISPATCH；协调者照抄派发，并把返回的 agent/run id 用 `mmw worker note-run-id` 落账。强判断咨询用 `advisor` Task（Cursor 无全会话自动转发，须附 handoff pack）；不占编制。

无人值守角色不能向用户提问。缺输入时返回结构化 blocker，由主线程处置。

final review 由 `mmw review start` 分档：small-change/bug 派一个 A 路 Task 覆盖两基线；develop 无 capable plan 且 diff 不超过阈值时派 A/B 各一路，其余及风险数据不全时派 A/B 各两路。

## Worker

`mmw worker dispatch` 为新 Pack 创建 Git worktree、组工人 prompt、记派发账本，并打印派发指令；协调者照指令派 `Task({subagent_type:"pack-executor", run_in_background:true, ...})`，并把返回的 id 用 `mmw worker note-run-id` 落账。`plan-dispatch` 同理，使用临时隔离 worktree。工具白名单由 agent frontmatter 提供。

工人完成(会话内收到后台 Task 回执)后过机器边界门：

- 写码：`mmw worker verify --worktree <wt>`(核 docs 边界)
- 写计划：`mmw worker verify --plan <plan> --worktree <wt>`(核越界，过门才原子发布 plan 与 issue `Small issues`)

修复使用 `worker resume` 或 `plan-resume`：脚本准备 resume prompt 并读账本 run id；协调者用同一 agent id 的 `Task({resume:…})` 续接——禁止另造 `supervisor-request.json` 旁路协议。仅无法 resume 时才重派同角色新 Task，靠 worktree 已有提交对齐进度。通过后主线程再亲验 diff、提交和测试。

## 主↔子多轮

Cursor 原生 **Task + resume**。工人要决策时：结构化回执回主线程 → 主线程必要时 `AskQuestion` → 再 `resume` 同一 agent id 答复。禁止 `contact_supervisor` / `supervisor-request.json` 文件协议。

## 审闸

主线程运行 `mmw review start`，读取生成的 `review-brief.md` 并直接派 reviewer Task。findings 原样落盘 `docs/reviews/<slug>-<stage>.md` 并逐条亲验、文末写总 verdict；审闸 `handoff pass` 时引擎核该文件存在且含 verdict，没有留痕不放行。

## Hooks

| 事件 | 脚本 |
| --- | --- |
| `sessionStart` / `preCompact` | `session-triage.sh` |
| `beforeShellExecution` | `guard-redline.sh`（Cursor flat `permission` + Claude nested 兼容） |
| `afterShellExecution` | `record-step.sh` |

`hooks.json` 以 `CURSOR_PLUGIN_ROOT` 解析插件根并传给脚本。用户级 `~/.cursor/hooks.json` 也可挂同一批绝对路径脚本（当前 Cursor 对 plugin hooks 加载不稳时的生效面）。红线读 `.command // .tool_input.command`；命中 → `permission=ask`（兼嵌套 `permissionDecision`）；放行必须吐 `{"permission":"allow"}`（`failClosed` 下空 stdout 会被拦）。

## Commands（控制面 slash）

插件 `commands/*.md` 声明 11 条控制面命令（`approve-design` / `progress` / `reassess` …）。每条 frontmatter 必须含 Cursor 要求的 `name` + `description`。

生效面（两道都接）：

1. 插件目录 `commands/`（需 Settings 打开 **Include third-party Plugins, Skills, and other configs**，否则 plugin commands 常不进 `/` 菜单）。
2. 用户级 `~/.cursor/commands/`——Cursor 确认会进 slash 菜单的通道。本地试装跑 `bash cursor-plugin/scripts/install-local-surface.sh` 同步插件与这 11 条命令。

设计确认是唯一人闸：用户敲 `/approve-design` → `mmw approve` 盖承重文档指纹、attendance 切 afk 并推进；用户口头同意不算过门。承重文档改动后审闸 pass 硬停 `approval_stale`，重跑 `mmw approve` 重盖（RE-APPROVED）。

## 安全

- Worker 禁改 `docs/`。
- 计划工人只准改自己的 plan 与对应 issue。
- 审者是劳动力，不是信源。
- 本地 merge 可自主执行；push、远端合并和部署必须经过用户权限确认。
- 无人值守时所有 agent 都不得向用户提问，硬停必须写入磁盘账本和进度板。
