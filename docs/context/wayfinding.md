# Wayfinding

这个 Context 定义 `/mmw-wayfinder` 使用的 map 和 decision ticket。

## Language

**effort**：
超出一次 agent session，而且从当前状态到 destination 的路线仍不清楚的工作。最终形成一份或多份 spec 不影响入口判定。
_Avoid_: 大 ticket、大 spec

**destination**：
Wayfinding 的 map 要抵达的终态。destination 固定 effort 的范围。
_Avoid_: 目标列表、交付清单

**map**：
issue tracker 上一项 effort 的共享索引，带 `wayfinder:map` 标签。
_Avoid_: Context Map、plan、仓库

**产物目录**：
仓库内一个 effort 的 prototype、evidence 和 scratch 共用的单个安全路径段。它写在 map 正文中，map 创建后保持不变。Decision ticket 继承产物目录，并使用自己的 `issue-<编号>` 子目录。任务 worktree、任务 slug 和 subagent 不改变这个目录。
_Avoid_: worktree slug、任务目录

**decision ticket**：
map 下解除一个决定或其前置阻塞的子 issue，带 `wayfinder:<类型>` 标签。它继承 map 的产物目录，并记录自己的 `issue-<编号>` 子目录。
_Avoid_: tracer bullet ticket、任务包

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

## 会话边界

一个会话只解决一张 decision ticket。建图会话可以并行派发多张 `wayfinder:research` ticket，但每个调查者仍只解决一张 ticket。
