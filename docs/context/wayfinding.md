# Wayfinding

这个 Context 定义 `/mmw-wayfinder` 使用的 map 和 decision ticket。

## Language

**effort**：
超出一次 agent session，而且从当前状态到 destination 的路线仍不清楚的工作。destination 是否是一份 spec 不影响入口判定。
_Avoid_: 大 ticket、大 spec

**destination**：
Wayfinding 的 map 要抵达的终态。destination 固定 effort 的范围。
_Avoid_: 目标列表、交付清单

**map**：
issue tracker 上一项 effort 的共享索引，带 `wayfinder:map` 标签。它的正文记录这项 effort 的工作名，map 创建后不再改动这个值。
_Avoid_: Context Map、plan、仓库

**decision ticket**：
map 下解除一个决定或其前置阻塞的子 issue，带 `wayfinder:<类型>` 标签。它继承 map 的工作名，并使用自己的范围段。
_Avoid_: tracer bullet ticket、任务包

**fog of war**：
范围内已经看得出会出现、但尚不能精确写成 decision ticket 的部分，保存在 `Not yet specified`。
_Avoid_: decision ticket、Out of scope

**结论评论**：
decision ticket 关闭前留下的评论，记录这张 ticket 形成的决定和它使用的资产精确路径。它是这个决定的权威副本，issue 关闭后长期保留。
_Avoid_: 交回评论、共同理解记录、过程材料

**交回评论**：
decision ticket 上记录结果分支名、HEAD SHA 和基点 SHA 的评论。map 分支上的会话用它验证并集成结果。
_Avoid_: 结论评论、集成记录

**路径形状**：
(authoritative: [路径形状](./artifact-location.md))

**名字段**：
(authoritative: [名字段](./artifact-location.md))

**工作名**：
(authoritative: [工作名](./artifact-location.md))

**范围段**：
(authoritative: [范围段](./artifact-location.md))

**权威副本**：
(authoritative: [权威副本](./tracker.md))

**frontier**：
(authoritative: [frontier](./tracker.md))

**HITL**：
(authoritative: [HITL](./delivery-workflow.md))

**AFK**：
(authoritative: [AFK](./delivery-workflow.md))

**共同理解**：
(authoritative: [共同理解](./delivery-workflow.md))

**`wayfinder:grilling`**：
用 `/mmw-grilling` 把 `Question` 谈成共同理解的 HITL decision ticket。提问方式由 `/mmw-grilling` 决定。

**`wayfinder:prototype`**：
用 `/mmw-prototype` 持续迭代可运行资产，并由用户走查来回答问题的 HITL decision ticket。

**`wayfinder:research`**：
由 `/mmw-research` 系统取证找出决定等待的事实的 AFK decision ticket。事实可以来自当前仓库源码，也可以来自文档、第三方 API 或正式规范这类外部资源；事实靠取证就能得到、不需要人参与讨论时使用。

**`wayfinder:task`**：
一个决定形成之前必须完成的手工操作。它可以是 HITL，也可以是 AFK。

## 会话边界

一个会话只解决一张 decision ticket。建图会话可以并行派发多张 `wayfinder:research` ticket，但每个 `investigator` 仍只解决一张 ticket。
