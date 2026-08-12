# Context Map

<!-- MMW-CONTEXT-MAP-RULES-START -->
> 下面是这个仓库的领域模型索引。答复用户、撰写文档或写代码之前，先读完本次涉及的全部 leaf，再全程使用它们定义的术语。
<!-- MMW-CONTEXT-MAP-RULES-END -->

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| 交付工作流 | [交付工作流](./docs/context/delivery-workflow.md) | prototype、prototype 资产、解释 HTML、research、research 索引、research 报告、research 配套文件、research 目录、research 路径、章节指引、共同理解、共同理解记录、spec、spec issue、tracer bullet ticket、plan、任务包、点名、HITL、AFK 和人工审批关卡。 |
| Tracker | [Tracker](./docs/context/tracker.md) | 类别角色、状态角色、agent brief、认领、frontier、权威副本、tracker 索引和否决记录。 |
| Wayfinding | [Wayfinding](./docs/context/wayfinding.md) | effort、destination、map、decision ticket、必读材料声明、结论评论、材料使用记录、交回评论、会话边界和 fog of war。 |
| Agent | [Agent](./docs/context/agent-coordination.md) | 主 agent、subagent、角色、task、报告、handoff、验证、任务分支、结果分支和任务 worktree。 |
| 审查 | [审查](./docs/context/review.md) | 六道审、共同理解审、视角（任务名）、finding、处置、固定点、被审 HEAD、终审提交和审查记录。 |
| 出包与收尾 | [出包与收尾](./docs/context/release-and-closure.md) | 产品、出包配置、`mmw release`、stage、出包状态、出包阶段产物、交付记录、用户实测和对外发布。 |
| 宿主 | [宿主](./docs/context/host-runtime.md) | 技能源、技能产物、物化、原生 subagent 和 Codex App 后台 Worktree 任务。 |
| 领域上下文与检索 | [领域上下文与检索](./docs/context/project-context.md) | 领域模型、Context Map、leaf、ADR、ADR 索引、权威引用、结构图谱和结构候选。 |
| 产物落点 | [产物落点](./docs/context/artifact-location.md) | 路径形状、类别根、固定类别根、工作目录根、名字段、工作名、范围段、类别内细分、当场取名、产物引用、撞名、安全路径段、工作名重复和不落盘判据。 |
| 界面 QA | [界面 QA](./docs/context/ui-qa.md) | 界面 QA、检查项、违规项、判据自检结果、界面全图和覆盖报告。 |

## Relationships

- Tracker 保存交付工作流的 spec issue 和 tracer bullet ticket，也保存 Wayfinding 的 map 和 decision ticket。
- 同一份内容在 Tracker 和仓库文件两处都有时，权威副本在生产它的那一侧，另一侧是 tracker 索引。
- agent 从 Tracker 进入：先读 issue 取得父子关系、阻塞关系、frontier 和认领状态，再沿 tracker 索引里的精确路径打开权威副本。父子关系、阻塞关系、frontier 和认领状态只存在于 Tracker；权威副本的细节只存在于它自己那一侧。两侧都不单独作为行动依据。
- Wayfinding 把 effort 收敛成一张路线已经清楚的 map；destination 是 spec 时，交付工作流把 map 中已经谈定的内容综合成一份 spec，并发布对应的 spec issue。
- 交付工作流通过 Agent 派发 task；subagent 交回报告，主 agent 验证关键断言。
- 审查读取共同理解记录、spec、plan、实现改动和集成结果；`accepted` finding 交回产物拥有者处理。
- 出包与收尾接收通过 final 终审的结果；用户实测通过后，有 spec 的任务进入 `/mmw-closing`。
- 宿主把共享技能源物化为技能产物；宿主差异不改变共享流程语义。
- 领域上下文与检索向其他 Context 提供 canonical 术语和结构候选；关键结论由主 agent 回到当前源码验证。
- Context Map 与 Wayfinding 的 map 是两个现有对象。Context Map 索引 bounded context；Wayfinding 的 map 索引一个 effort 的决定。
- 产物落点向其他 Context 提供路径形状；交付工作流、Wayfinding、审查和 Agent 的产物按它确定位置。
- 交付工作流的每一跳用产物引用点名下游要读的产物，不写路径字面值。产物引用由产物落点定义，路径由 `mmw artifact path` 解析。
- 工作名由产物落点定义，与 Agent 的任务分支名是两个值。一次交付只有一个工作名，可以有多条任务分支；Wayfinding 的 map 正文记录这项 effort 的工作名，它的每张 decision ticket 继承这个值。
- 界面 QA 不是六道审的任何一道，它在 prototype 迭代中和落地之后都可以单独发起。审查定义 finding 与处置；界面 QA 的 B 类结果是 finding 的第二个来源，用同一套处置标记。A 类结果是违规项，不是 finding。
- 界面 QA 的判据与接线跨交付累积，不带工作名，位置由产物落点定义。它的报告不写进仓库，界面全图也不落文件。
