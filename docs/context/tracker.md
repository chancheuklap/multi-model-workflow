# Tracker

这个 Context 定义 issue tracker 中的角色、行为合同和并发归属。

## Language

**类别角色**：
表示 work item 是 bug 还是 enhancement 的标签角色。
_Avoid_: 状态角色、类型字段

**`bug`**：
有东西坏了的类别角色。

**`enhancement`**：
新功能或改进的类别角色。

**状态角色**：
表示 work item 当前由谁继续的标签角色。
_Avoid_: 类别角色、流程阶段

**`needs-triage`**：
等待维护者评估。

**`needs-info`**：
等待报告人补信息。

**`ready-for-agent`**：
状态角色，其具体条件由 work item 的种类决定。分诊 issue 或 PR 要有完整 agent brief；spec issue 表示 `/mmw-to-spec` 第 7 步已经通过；tracer bullet ticket 表示 plan 已经通过 ② plan 审。tracer bullet ticket 还要进入 frontier，才能认领并派 `worker`。
_Avoid_: 已完成、可以无条件派 `worker`

**`ready-for-human`**：
需要人来实现；对 PR 表示可以由人来合。
_Avoid_: HITL、人工审批关卡

**`wontfix`**：
不做。
_Avoid_: `ready-for-human`、暂缓处理

**agent brief**：
已分诊 issue 或 PR 的行为合同，包含当前行为、目标行为、验收标准、范围边界和 Test seam。spec 发布之后，同一件事以 spec 为准，agent brief 成为背景材料。
_Avoid_: task、plan、brief

**权威副本**：
一份内容的正本。同一份内容在 issue tracker 和仓库文件两处都有时，说法冲突以它为准。
_Avoid_: 主副本、正式版本、最新版本

**tracker 索引**：
issue tracker 上指向权威副本的一条记录，说明这是什么、权威副本在哪。它是写下那一刻的快照，不跟随权威副本演进。
_Avoid_: research 索引、摘要、副本

**认领**：
把 work item 指派给当前执行者。认领成功之前不开始工作。
_Avoid_: 读取、开始 research

**frontier**：
一个父 issue 下 open、无阻塞、未认领的子 issue。
_Avoid_: issue 顺序、全部未完成项

**`.out-of-scope/`**：
保存已明确否决的 enhancement 及理由。
_Avoid_: backlog、`wontfix` issue 副本、已实现行为
