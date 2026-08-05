# Product Definition

这个上下文把未定形需求收敛成经过用户批准的 spec。它拥有用户可见行为的决定与正式人工审批关卡。

## Language

**grilling**：
一次只追问一个关键问题，直到需求足以实施的需求收敛过程。grilling 同时收紧领域术语，但不编写 spec。
_Avoid_: 采访、需求清单

**prototype**：
为回答一个仅靠讨论无法决定的问题而制作的可运行粗糙产物。prototype 是决策证据，不是生产实现。
_Avoid_: MVP、正式代码、视觉稿

**prototype round**：
围绕一个明确问题制作、运行、走查并记录结论的一次原型迭代。一轮只能回答一个问题。
_Avoid_: 版本、实现阶段

**walkthrough**：
用户基于真实运行结果选择、拒绝或要求修改 prototype 的人工走查。walkthrough 形成设计证据，但不替代 spec 的人工审批关卡。
_Avoid_: 人工审批关卡、自动验收

**selected variant**：
用户在 walkthrough 中明确接受、可进入 spec 和视觉合同的 prototype 变体。未选变体只保留为原型历史。
_Avoid_: 最新变体、默认变体

**spec**：
一项交付的定稿设计合同，记录现状、目标行为、实现决定、失败路径、测试决定、合同边界与明确范围。spec 不保留未决设计。
_Avoid_: 需求草稿、plan、Wiki 页面

**人工审批关卡**：
用户批准定稿 spec、允许 MMW 进入自动拆 ticket 与实施阶段的正式关卡。MMW 全流程只有 `/mmw-to-spec` 发布前这一道正式关卡。
_Avoid_: walkthrough、人工浏览器验收、安装包实测、HITL

**视觉合同**：
由 selected variant 固化的布局、状态、交互、文案与可观察结果。它必须指向持久的 prototype 产物或截图证据。
_Avoid_: 与原型一致、临时浏览器状态

**测试 seam**：
(authoritative: [seam](./codebase-design.md))

**实现决定**：
spec 中已经拍板、实现时不得重新开启的技术或产品方向。需要用户判断的实现决定必须有 walkthrough 证据，或明确符合免除条件。
_Avoid_: TODO、建议、开放问题
