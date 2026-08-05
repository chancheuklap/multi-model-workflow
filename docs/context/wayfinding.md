# Wayfinding

这个上下文处理尚不能由一份 spec 说清的大型 effort。它用 issue tracker 上的共享索引逐个解除未知决定。

## Language

**effort**：
需要多份 spec 才能完成，而且尚不清楚这些 spec 的边界或顺序的一项大型工作。
_Avoid_: 大 ticket、大 spec

**destination**：
一张 Wayfinder map 要抵达的清晰终态。destination 固定 effort 的范围，并决定哪些 decision ticket 有关。
_Avoid_: 目标列表、交付清单

**Wayfinder map**：
issue tracker 上一项 effort 的唯一索引，带 `wayfinder:map` 标签。它只索引决定与未解问题，不复制各 decision ticket 的完整结论。
_Avoid_: Context Map、计划、仓库

**decision ticket**：
Wayfinder map 下解除一个决定或其前置阻塞的子 issue。带 `wayfinder:<类型>` 标签；收尾时切出的 spec issue 不属于 decision ticket。
_Avoid_: 实现 ticket、tracer bullet ticket

**decision chain**：
一个会话从已认领 decision ticket 开始连续解锁并处理的单链。一个会话一次只拥有一条 decision chain。
_Avoid_: 并行 ticket 列表、任务分支

**frontier**：
依赖已经解除、尚未关闭且无人认领的 work item 集合。Wayfinding 与实现排程都使用这个同一图概念。
_Avoid_: backlog、下一张固定 ticket

**HITL**：
缺少人的对话回答就无法完成的 work item 属性。HITL 描述完成方式，不表示 `/mmw-to-spec` 的人工审批关卡。
_Avoid_: `ready-for-human`、人工审批关卡

**AFK**：
agent 可以在没有人中途参与时完成的 work item 属性。人只在完成后查看结果。
_Avoid_: 全自动发布、无需验证

**`wayfinder:grilling`**：
必须通过一问一答形成决定的 HITL decision ticket。

**`wayfinder:prototype`**：
必须先让用户走查可运行产物才能形成决定的 HITL decision ticket。

**`wayfinder:research`**：
通过当前工作目录之外的可读事实形成决定的 AFK decision ticket。必须真实运行才能知道的事实改走 prototype evidence。

**`wayfinder:task`**：
为解除另一个决定的阻塞而完成的具体操作。它可能是 HITL，也可能是 AFK，本身通常不产出决定。
