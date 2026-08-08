# Context Map

<!-- MMW-CONTEXT-MAP-RULES-START -->
> 下面是这个仓库的领域模型索引。答复用户、撰写文档或写代码之前，先读完本次涉及的全部 leaf，再全程使用它们定义的术语。
<!-- MMW-CONTEXT-MAP-RULES-END -->

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| 交付工作流 | [交付工作流](./docs/context/delivery-workflow.md) | prototype、prototype 资产、research、research 索引、research 报告、research 配套文件、research 目录、research 路径、共同理解、spec、tracer bullet ticket、plan、任务包、HITL、AFK 和人工审批关卡。 |
| Tracker | [Tracker](./docs/context/tracker.md) | 类别角色、状态角色、agent brief、认领、frontier 和 `.out-of-scope/`。 |
| Wayfinding | [Wayfinding](./docs/context/wayfinding.md) | effort、destination、map、decision ticket、会话边界和 fog of war。 |
| Agent | [Agent](./docs/context/agent-coordination.md) | 主 agent、subagent、角色、task、报告、验证、任务分支和结果分支。 |
| 审查 | [审查](./docs/context/review.md) | 五道审、视角（任务名）、finding、处置、固定点、被审 HEAD、终审提交和审查记录。 |
| 出包与收尾 | [出包与收尾](./docs/context/release-and-closure.md) | 产品、出包配置、`mmw release`、交付记录、用户实测、对外发布和 Wiki 页面。 |
| 宿主 | [宿主](./docs/context/host-runtime.md) | 技能源、技能产物、物化、原生 subagent 和 Codex App 后台 Worktree 任务。 |
| 领域上下文与检索 | [领域上下文与检索](./docs/context/project-context.md) | 领域模型、Context Map、leaf、ADR、权威引用、结构图谱和结构候选。 |

## Relationships

- Tracker 保存交付工作流的 spec issue 和 tracer bullet ticket，也保存 Wayfinding 的 map 和 decision ticket。
- Wayfinding 把 effort 收敛成一张路线已经清楚的 map；destination 是 spec 时，交付工作流把 map 中已经谈定的内容综合成一份 spec，并发布对应的 spec issue。
- 交付工作流通过 Agent 派发 task；subagent 交回报告，主 agent 验证关键断言。
- 审查读取 spec、plan、实现改动和集成结果；`accepted` finding 交回产物拥有者处理。
- 出包与收尾接收通过 final 终审的结果；用户实测通过后，有 spec 的任务进入 `/mmw-closing`。
- 宿主把共享技能源物化为技能产物；宿主差异不改变共享流程语义。
- 领域上下文与检索向其他 Context 提供 canonical 术语和结构候选；关键结论由主 agent 回到当前源码验证。
- Context Map 与 Wayfinding 的 map 是两个现有对象。Context Map 索引 bounded context；Wayfinding 的 map 索引一个 effort 的决定。
