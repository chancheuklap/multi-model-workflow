# Context Map

<!-- MMW-CONTEXT-MAP-RULES-START -->
> 下面是这个仓库的领域模型索引。答复用户、撰写文档或写代码之前，先读完本次涉及的全部 leaf，再全程使用它们定义的术语。
<!-- MMW-CONTEXT-MAP-RULES-END -->

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| 交付工作流 | [交付工作流](./docs/context/delivery-workflow.md) | prototype、prototype 资产、prototype 索引、挂载接线、解释 HTML、research、research 索引、research 目录、research 路径、shared understanding、shared-understanding record、spec、spec issue、tracer bullet ticket、plan、批次、点名、HITL、AFK 和人工审批关卡。 |
| Tracker | [Tracker](./docs/context/tracker.md) | 类别角色、状态角色、agent brief、认领、frontier、权威副本、tracker 索引和否决记录。 |
| Wayfinding | [Wayfinding](./docs/context/wayfinding.md) | effort、destination、map、decision ticket、Required materials、fog of war、resolution comment、Materials used 和会话边界。 |
| Agent | [Agent](./docs/context/agent-coordination.md) | 主 agent、subagent、角色、task、报告、handoff、验证、任务分支、结果分支和任务 worktree。 |
| 审查 | [审查](./docs/context/review.md) | 六道审、共同理解审、视角（任务名）、finding、处置、固定点、Reviewed HEAD、Final commit、Repair commit、审查记录、逐份验收和合同门。 |
| 出包与收尾 | [出包与收尾](./docs/context/release-and-closure.md) | product、release config、`mmw release`、stage、release state、stage artifact、delivery record、user install test 和 external publish。 |
| 宿主 | [宿主](./docs/context/host-runtime.md) | 技能源、技能产物、物化、宿主动作表、原生 subagent、Codex App 后台 Worktree 任务和 Cursor 任务树与结果树。 |
| 领域上下文与检索 | [领域上下文与检索](./docs/context/project-context.md) | domain model、Context Map、leaf、ADR、ADR 索引、authoritative reference、structure graph 和 structure candidate。 |
| 产物落点 | [产物落点](./docs/context/artifact-location.md) | 路径形状、类别根、固定类别根、工作目录根、名字段、工作名、范围段、类别内细分、当场取名、产物引用、撞名、安全路径段、工作名重复和不落盘判据。 |
| 界面 QA | [界面 QA](./docs/context/ui-qa.md) | UI QA、check、violation、criterion self-check、screen map、coverage report 和范围。 |

## Relationships

- Tracker 保存交付工作流的 spec issue 和 tracer bullet ticket，也保存 Wayfinding 的 map 和 decision ticket。
- 同一份内容在 Tracker 和仓库文件两处都有时，权威副本在生产它的那一侧，另一侧是 tracker 索引。
- agent 从 Tracker 进入：先读 issue 取得父子关系、阻塞关系、frontier 和认领状态，再沿 tracker 索引里的精确路径打开权威副本。父子关系、阻塞关系、frontier 和认领状态只存在于 Tracker；权威副本的细节只存在于它自己那一侧。两侧都不单独作为行动依据。
- Wayfinding 把 effort 收敛成一张路线已经清楚的 map；destination 是 spec 时，交付工作流把 map 中已经谈定的内容综合成一份 spec，并发布对应的 spec issue。
- 交付工作流通过 Agent 派发 task；subagent 交回报告，主 agent 按报告继续流程。独立审查者仍派。
- 审查读取 shared-understanding record、spec、plan、实现改动和集成结果；`accepted` finding 交回产物拥有者处理。
- 出包与收尾接收通过 final 终审的结果。user install test 通过后，任务结束。
- 宿主把共享技能源物化为技能产物；宿主差异不改变共享流程语义。
- 领域上下文与检索向其他 Context 提供 canonical term 和 structure candidate；关键结论由主 agent 回到当前源码验证。
- Context Map 与 Wayfinding 的 map 是两个现有对象。Context Map 索引 bounded context；Wayfinding 的 map 索引一个 effort 的决定。
- 产物落点向其他 Context 提供路径形状；交付工作流、Wayfinding、审查和 Agent 的产物按它确定位置。
- 交付工作流的每一跳用产物引用点名下游要读的产物，不写路径字面值。产物引用由产物落点定义，路径由 `mmw artifact path` 解析。
- 名字段由产物落点定义，取这次交付的任务分支 slug。一次交付只有一个名字段，可以有多条任务分支；Wayfinding 的 map 正文记录 map 分支，它的每张 decision ticket 继承这个名字段。
- UI QA 不是六道审的任何一道，它在 prototype 迭代中和落地之后都可以单独发起。审查定义 finding 与处置；UI QA 的 B 类结果是 finding 的第二个来源，用同一套处置标记。A 类结果是 violation，不是 finding。
- UI QA 的判据与接线跨交付累积，不带名字段，位置由产物落点定义。它的报告不写进仓库，screen map 也不落文件。
