# Delivery Planning

这个上下文把定稿 spec 变成可独立排程、实现和验证的 ticket 与 plan。

## Language

**实现 ticket**：
一条窄而完整的端到端交付切片，由一个 `worker` 独立实现和验收。它不同于 Wayfinding 的 decision ticket。
_Avoid_: decision ticket、任务包、横向层任务

**tracer bullet**：
穿过交付所需各层并产生一个可演示或可验证行为的实现 ticket 形状。
_Avoid_: 按 schema、API、界面分别拆分

**prefactor**：
在目标行为之前完成、让后续改动更容易的结构调整。prefactor 必须服务当前 spec，并作为独立实现 ticket 验收。
_Avoid_: 顺手重构、未来基础设施

**plan**：
一张实现 ticket 的可执行实施合同，供零上下文 `worker` 使用。一张实现 ticket 恰好对应一份 plan。
_Avoid_: spec、ticket 正文、路线图

**任务包**：
plan 内可以独立实现、独立验证并值得单独审查的最小交付单元。任务包是实现 ticket 内部的步骤集合，不是 tracker work item。
_Avoid_: ticket、阶段、代码层

**跨 plan 合同锚点**：
spec 中约束多份 plan 之间文件归属、提供方、消费方与共享接口的合同骨架。精确字段由 plan 形成后回填并验证。
_Avoid_: 重复接口说明、隐式依赖

**验收标准**：
判断一个实现 ticket 或任务包是否完成的可执行行为判据。每条标准必须能独立判定真假。
_Avoid_: 正常工作、实现完成

**阻塞边**：
表示一个 work item 必须等待另一个 work item 完成的 issue dependency。阻塞边决定 frontier 与发布顺序。
_Avoid_: 文本顺序、编号顺序

**`ready-for-agent`**：
(authoritative: [`ready-for-agent`](./intake-and-triage.md))

**frontier**：
(authoritative: [frontier](./wayfinding.md))
