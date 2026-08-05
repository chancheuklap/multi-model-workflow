# Wayfinding

这个 Context 定义 `/mmw-wayfinder` 使用的 map 和 decision ticket。

## Language

**effort**：
大到要拆成多份 spec，而且尚未看清这些 spec 边界或顺序的工作。
_Avoid_: 大 ticket、大 spec

**destination**：
Wayfinding 的 map 要抵达的终态。destination 固定 effort 的范围。
_Avoid_: 目标列表、交付清单

**map**：
issue tracker 上一项 effort 的共享索引，带 `wayfinder:map` 标签。
_Avoid_: Context Map、plan、仓库

**decision ticket**：
map 下解除一个决定或其前置阻塞的子 issue，带 `wayfinder:<类型>` 标签。
_Avoid_: tracer bullet ticket、任务包

**链**：
一个会话从已认领 decision ticket 开始连续处理的单链。一个会话只解一条链。
_Avoid_: decision chain、并行 ticket 列表、任务分支

**fog of war**：
范围内已经看得出会出现、但尚不能精确写成 decision ticket 的部分，保存在 `Not yet specified`。
_Avoid_: decision ticket、Out of scope

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
用 `/mmw-prototype` 做出粗糙可运行产物并由用户走查的 HITL decision ticket。

**`wayfinder:research`**：
需要当前工作目录之外的知识，由 `/mmw-research` 调查的 AFK decision ticket。

**`wayfinder:task`**：
一个决定形成之前必须完成的手工操作。它可以是 HITL，也可以是 AFK。
