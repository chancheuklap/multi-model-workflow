# Tracker 管理

这个上下文定义 MMW 在 issue tracker 中保存 work item 身份、状态和并发归属时使用的语言。

## Language

**类别角色**：
表示 issue 或外部 PR 属于缺陷还是改进的标签角色，取值是 `bug` 或 `enhancement`。
_Avoid_: 状态角色、类型字段

**`bug`**：
当前行为与预期行为冲突的类别角色。

**`enhancement`**：
请求新增能力或改进现有能力的类别角色。

**状态角色**：
表示 issue 或外部 PR 当前由谁继续以及是否具备继续条件的标签角色。
_Avoid_: 类别角色、流程阶段

**`needs-triage`**：
当前 work item 等待维护者评估。

**`needs-info`**：
当前 work item 等待报告人补充完成分诊所需的信息。

**`ready-for-agent`**：
当前 work item 的合同已足以让 agent 按拥有该 work item 的技能继续 AFK 推进。它不指定下一项技能，也不豁免该技能自己的前置条件。
_Avoid_: 已完成、人工审批关卡、可以无条件派 `worker`

**`ready-for-human`**：
当前 work item 的下一步由人承担，agent 不得代替这个人完成。
_Avoid_: HITL、人工审批关卡、等待用户批准

**`wontfix`**：
当前 work item 无需实现：维护者已经决定不做，或者当前行为已经存在。
_Avoid_: `ready-for-human`、暂缓处理

**agent brief**：
已分诊 issue 或外部 PR 的行为合同，记录当前行为、目标行为、验收标准、范围边界和测试 seam。
_Avoid_: task、plan、brief

**认领**：
把一个尚未分配的 work item 指派给当前执行者，从而取得该 work item 的并发执行权。
_Avoid_: 读取、开始调查

**frontier**：
同一父 work item 下所有 open、未阻塞、未认领并满足查询标签的子 work item 集合。
_Avoid_: issue 顺序、全部未完成项

**`.out-of-scope/` 文件**：
按领域概念保存已明确否决的 enhancement 及其理由，供后续分诊识别同一需求。
_Avoid_: 范围外记录、判出范围的知识库、backlog、已实现行为、`wontfix` issue 副本
