# Context Map

<!-- MMW-CONTEXT-MAP-RULES-START -->
## 使用规则

1. 根据 `Contexts` 和 `Relationships` 选择本次涉及的全部 leaf。答复用户或写入文件前读完这些 leaf。
2. 术语归属不明确时，运行 `mmw domain dirs` 取得 `context` 路径并搜索该术语。仍无法判断时询问用户。
3. 使用 leaf 定义的 canonical 术语，避开 `_Avoid_`。共享术语以标有 `authoritative` 路径的主 leaf 为准。
4. 读取 `mmw domain dirs` 返回的 `adr` 路径下与本次范围相关的 ADR。
5. 用户说法、多个 leaf、ADR 或代码现状互相冲突时，明确列出冲突，不得静默覆盖。
6. 长期术语、关系和歧义只写入拥有它们的 leaf。只有上下文集合、所有权或跨上下文关系改变时才修改本 Map。
7. 操作步骤、实施计划、发布状态和一次性调查不进入领域文档。
<!-- MMW-CONTEXT-MAP-RULES-END -->

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| 交付工作流 | [交付工作流](./docs/context/delivery-workflow.md) | 从需求定形到实现完成的正式产物、参与方式和人工审批关卡。 |
| Tracker 管理 | [Tracker 管理](./docs/context/tracker.md) | issue 与外部 PR 的角色标签、执行合同、认领和 frontier。 |
| Wayfinding | [Wayfinding](./docs/context/wayfinding.md) | 大型 effort 的 map、decision ticket、链和 fog of war。 |
| Agent 协作 | [Agent 协作](./docs/context/agent-coordination.md) | 主 agent、subagent、角色、task、报告、验证和结果分支。 |
| 审查 | [审查](./docs/context/review.md) | 审查阶段、审查视角、finding、处置、固定点和审查记录。 |
| 发布与收尾 | [发布与收尾](./docs/context/release-and-closure.md) | 产品出包、ReleaseFinding、交付记录、安装包实测、对外发布和 Wiki 收尾。 |
| 宿主运行时 | [宿主运行时](./docs/context/host-runtime.md) | 技能源、物化技能、角色定义、宿主 profile、角色模型配置和宿主动作块。 |
| 项目上下文 | [项目上下文](./docs/context/project-context.md) | 领域文档、检索图、结构候选和权威引用。 |

## Relationships

- Tracker 管理保存交付工作流和 Wayfinding 的 work item；`ready-for-agent` 只表示 agent 可以按拥有该 work item 的技能继续 AFK 推进。
- Wayfinding 通过 map 把一个 effort 收敛成一份或多份 spec issue；交付工作流拥有这些 spec 的定稿、拆分、计划和实现。
- 交付工作流通过 Agent 协作派发工作；subagent 交回报告，主 agent 验证关键断言后才采信。
- 审查读取交付工作流的 spec、plan 和实现产物；采信的 finding 返回产物拥有者处理。
- 发布与收尾只接收通过 final 终审的交付结果；安装包实测和对外发布各自遵守交付工作流定义的人工审批关卡。
- 宿主运行时把共享技能中的角色启动和宿主动作物化成各宿主的原生执行方式，不改变交付工作流语义。
- 项目上下文为其他上下文提供项目术语和结构候选；关键结论仍由 Agent 协作中的主 agent 回到当前源码验证。
- Context Map 属于项目上下文；Wayfinding 的 map 属于 Wayfinding。两者都使用 map 这个词，但不共享对象含义。
