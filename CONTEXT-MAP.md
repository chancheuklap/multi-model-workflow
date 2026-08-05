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
| Workflow Orchestration | [Workflow Orchestration](./docs/context/workflow-orchestration.md) | MMW 任务、slug、任务 worktree、任务分支、结果分支与移交。 |
| Intake and Triage | [Intake and Triage](./docs/context/intake-and-triage.md) | issue 与外部 PR 的分诊状态、agent brief 和 `ready-for-agent`。 |
| Wayfinding | [Wayfinding](./docs/context/wayfinding.md) | effort、destination、Wayfinder map、decision ticket、chain 与 frontier。 |
| Product Definition | [Product Definition](./docs/context/product-definition.md) | grilling、prototype、walkthrough、spec、视觉合同与人工审批关卡。 |
| Delivery Planning | [Delivery Planning](./docs/context/delivery-planning.md) | tracer bullet ticket、plan、任务包与跨 plan 合同。 |
| Agent Operation | [Agent Operation](./docs/context/agent-operation.md) | 主 agent、subagent、角色、task、报告、取证与验证。 |
| Implementation Quality | [Implementation Quality](./docs/context/implementation-quality.md) | 诊断 loop、TDD、回归测试、mock 与测试质量门。 |
| Review and Integration | [Review and Integration](./docs/context/review-and-integration.md) | 六道审查、finding、处置、固定点、结果验证与分支集成。 |
| Codebase Design | [Codebase Design](./docs/context/codebase-design.md) | module、interface、implementation、depth、seam 与 adapter。 |
| Knowledge and Domain | [Knowledge and Domain](./docs/context/knowledge-and-domain.md) | 调查、检索图、领域模型、Context Map、leaf 与 ADR。 |
| Release and Closure | [Release and Closure](./docs/context/release-and-closure.md) | 产品出包、release engine、安装包实测、Wiki 归档与任务收尾。 |
| Skill Authoring | [Skill Authoring](./docs/context/skill-authoring.md) | 技能源、物化技能、调用方式、信息层级、steering 与 pruning。 |

## Relationships

- Workflow Orchestration 为一项工作建立 MMW 任务，并把请求路由到 Intake and Triage、Wayfinding、Product Definition、Knowledge and Domain 或 Review and Integration。
- Intake and Triage 把已分诊需求交给 Product Definition 或 Delivery Planning；`ready-for-agent` 只表示当前 work item 的下一步 agent 合同已经完整。
- Wayfinding 把一个 effort 逐步收敛成一份或多份 spec issue；Product Definition 把每份 spec issue 写成经过人工审批关卡的 spec。
- Product Definition 定义 spec 与测试 seam；Delivery Planning 把 spec 拆成实现 ticket 和 plan。
- Delivery Planning 通过 task 把 plan 交给 Agent Operation 中的 `planner` 或 `worker`；Agent Operation 只交回报告，关键断言由主 agent 验证。
- Implementation Quality 约束 `worker` 的诊断、TDD 和测试；测试 seam 使用 Codebase Design 的权威定义。
- Review and Integration 审查 spec、plan、实现与合并结果；采信的 finding 返回产物拥有者修复。
- Codebase Design 为 Product Definition、Delivery Planning 与 Implementation Quality 提供 module、interface、seam 和 adapter 的共同语言。
- Knowledge and Domain 为所有上下文提供验证过的仓库事实、外部事实与领域术语；Context Map 与 Wayfinder map 是两个不同对象。
- Release and Closure 只接收通过 final 终审的任务；安装包实测通过后，spec 与 plan 才进入 Wiki 并从任务分支移除。
- Skill Authoring 规定前述工作流如何写成技能并物化到各宿主；它不拥有任何产品工作流的业务语义。
