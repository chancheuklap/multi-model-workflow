# UI Mockup

UI mockup 用可运行页面理顺页面、状态和操作路径。它是持续迭代的 prototype 资产。

## 1. 确定本轮验证问题

读取 `README.md`、`mockup/current/` 和当前问题需要的文档、变体、真实数据及设计系统。把验证问题、保持不变的部分和本轮路径写入 `README.md`。

| 不确定范围 | 本轮路径 |
| --- | --- |
| 没有不确定方向 | 没有当前 mockup 时直接创建 `mockup/current/`；已有当前 mockup 时直接修改它 |
| 整个页面或操作流程不确定 | 以相关文档和已有当前 mockup 为依据，生成多个完整变体 |
| 某个页面、组件、状态或操作路径不确定 | 保持其他部分不变，只为这一部分生成多个局部变体 |

没有 current 但只有局部不确定时，先建立明确部分作为 current。开始比较后，选择前保持 current 不变。

## 2. 选择承载形态

| 项目情况 | 承载形态 |
| --- | --- |
| 已有成熟应用，而且 prototype 天然属于某个页面或流程 | 挂入已有页面。保留真实页头、侧边栏、数据密度、取数、参数和鉴权，只替换正在验证的界面部分 |
| 没有合适前端宿主 | 使用独立 HTML；current 入口为 `mockup/current/index.html` |
| 已有应用，但没有任何现有页面能够承载一个新的顶层界面 | 按项目现有路由约定建立明确标记的 prototype 路由 |

UI mockup 的持久资产必须保存在 `mockup/`。应用源码中确实需要 route 或挂载文件时，只保留让 mockup 运行所需的薄接线。把接线文件和 `mockup/` 内资产的精确对应关系写进 `README.md`。

变体组使用 `mockup/variants/<问题 slug>/`。它包含 `preview/` 和每个 `<变体 key>/`。独立 HTML 使用 `preview/index.html` 与 `<变体 key>/index.html`；已有应用在 `README.md` 写明统一入口和薄 adapter。

## 3. 创建当前 mockup 或变体

方向明确时，只创建或修改 `mockup/current/` 和必要薄接线。需要变体时，为每个方向分配一个 `kebab-case` key；目录名、`?variant=` 和 preview 映射使用同一个 key。

完整变体可以改变整页结构。局部变体保留 current 已确认的部分，只改变本轮比较范围。每个变体必须有真实结构差异，并能由 preview 加载。

并行有明显收益时，可以派 `prototype-worker`。派发前，主 agent 建立并提交共享 preview、key 映射和入口合同。

每份 task 使用以下四栏表：

| 栏 | 内容 |
| --- | --- |
| 目标 | 验证问题、变体类型、方向和 key |
| 读 | 页面、数据、设计系统、现有资产和入口合同的精确路径 |
| 约束 | 只修改对应 key 目录，并遵守入口合同 |
| 验收 | preview 能加载变体；交回 URL、key 和 HEAD SHA |

启动：先用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-sol`，思考档使用 `medium`。任务提示包含四栏 task、主 agent 已确定的完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 先运行 `mmw task bind <完整结果分支名> <目标栏原文> --from <基点 SHA>`，然后完成工作并提交。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告；报告交回后只按 `$mmw:mmw-verifying-agent-output` 验证关键断言，不重做整个 task。

结果交回后运行 `mmw result verify`，读取报告和 diff，并按 `$mmw:mmw-verifying-agent-output` 验证。通过后运行 `mmw result integrate`。全部集成后，主 agent 验收整组变体。

## 4. 连接和验收

preview 用显式映射加载 key。缺少 key 时写入第一个 key；未知 key 显示错误。切换器提供上一个、当前和下一个变体，并同步 URL。只有一个方向时移除切换器。

交给用户前，主 agent 必须启动页面、操作本轮路径、检查相关状态与 console，并截图。变体还要确认每个 key、刷新、切换和结构差异都正确。

## 5. 连接后端行为

在 `README.md` 记录本轮功能使用的 `frontend`、`stub`、`contract` 或 `backend` 路径；跨层功能记录多项。stub 必须在页面中可见。必须验证真实写操作时，下一轮先完成后端 prototype，再接回同一份 UI mockup。

呈现本轮需要判断的加载、空、错误、成功和部分完成状态。

## 6. 走查和保存

按 [SKILL.md](SKILL.md) 的浏览器规则打开页面。用户反馈后，先按 [capture.md](capture.md) 记录原话，再继续：

| 用户意见 | 动作 | 本轮何时完成 |
| --- | --- | --- |
| 继续修改 | 修改同一资产，再验收和走查 | 用户确认结果时 |
| 接受 current | 保留 current | 用户明确接受时 |
| 选择一个变体 | 独立写入 current，移除切换器和变体运行依赖，再走查 | 用户确认一致时 |
| 组合多个变体 | 把指定部分独立写入 current，再走查 | 用户确认组合结果时 |
| 否定整个方向 | 保持现有资产，记录击穿方向的事实 | 事实已经写进 `README.md` 时 |

选择或组合后，必须形成并重新确认 current。随后按 [capture.md](capture.md) 提交和交回。保留变体组作为 prototype 资产，但只把确认后的 current 列为可复用内容。
