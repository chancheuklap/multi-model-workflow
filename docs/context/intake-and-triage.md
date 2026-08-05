# Intake and Triage

这个上下文定义 issue 与外部 PR 如何成为可执行的已分诊需求。它拥有 tracker 状态，不拥有 spec、plan 或实现步骤。

## Language

**已分诊需求**：
经过事实验证、类别判断和状态判断的 issue 或外部 PR。原始正文与评论保留背景，当前行为合同由 agent brief 或已发布 spec 承载。
_Avoid_: ticket、spec

**类别角色**：
表示需求属于缺陷还是改进的标签角色，取值是 `bug` 或 `enhancement`。一张已分诊 work item 恰好有一个类别角色。
_Avoid_: 类型标签

**状态角色**：
表示 work item 当前可由谁继续以及还缺什么的标签角色。一张已分诊 work item 恰好有一个状态角色。
_Avoid_: 阶段、进度标签

**`ready-for-agent`**：
当前 work item 已有完整合同，agent 可以执行它的下一次流程转换。已分诊 issue 或 PR 依赖完整 agent brief；spec issue 依赖已批准 spec；新建实现 ticket 依赖验收标准进入 plan，plan 审通过后才具备 `worker` 实现合同。
_Avoid_: 已实现、已完成、等同于可以立即派 `worker`

**`ready-for-human`**：
当前 work item 的下一步必须由人完成，因为它需要人的判断、权限、设计决定或人工操作。
_Avoid_: 人工审批关卡、HITL

**agent brief**：
一张已分诊需求的权威行为合同，记录当前行为、目标行为、验收标准、范围边界与一个测试 seam。它只适用于整项工作可作为一张实现 ticket 独立验收的路径。
_Avoid_: brief、plan、task

**范围外记录**：
被明确否决的 enhancement 所对应的长期概念记录，用于以后按概念识别同一需求。已实现行为、bug 和普通搁置项不进入范围外记录。
_Avoid_: backlog、wontfix issue 副本

**旁路发现**：
分诊或交付过程中发现、但不属于当前任务范围的独立问题。旁路发现进入新的 `needs-triage` issue，不改变当前任务。
_Avoid_: 顺手修复、当前 finding
