# 审查

这个 Context 定义 `/mmw-review` 和 `/mmw-reviewer` 使用的语言。

## Language

**六道审**：
共同理解审、spec 审、plan 审和 final 终审。编号为 ⓪①②⑤。逐份验收和合同门已取消，不要发起。多分支集成结果也进入 final 终审；集成调查属于 `/mmw-integrate`。
_Avoid_: 五道审、人工审批关卡、把③或④当成关卡

**共同理解审**：
审共同理解记录的第一道审，由用户在 `/mmw-grilling` 里要求才发起，不是关卡。
_Avoid_: spec 审、走查

**共同理解记录**：
(authoritative: [共同理解记录](./delivery-workflow.md))

**视角（任务名）**：
一名审查者在独立上下文中检查的一个角度；task 的目标栏第一句使用表中任务名。
_Avoid_: 五道审、自定义任务名、视角摘要

**finding**：
审查者或[界面 QA](./ui-qa.md) 报告的一个可定位问题候选。两个来源都由主 agent 处置，处置都用下面五个标记。
_Avoid_: 已确认缺陷、违规项、ReleaseFinding、建议清单

**处置**：
主 agent 对 finding 使用的五个标记：`accepted`、`rejected`、`duplicate`、`needs-evidence` 和 `waived`。
_Avoid_: finding、修复状态

**固定点**：
final 终审用于限定 diff 范围的提交。
_Avoid_: 当前 HEAD、分支名

**被审 HEAD**：
某轮审查实际检查的被审分支 HEAD。它用于发现审查期间的内容漂移，不表示该轮已经通过。
_Avoid_: 固定点、终审提交

**终审提交**：
一次 final 终审完成时的分支 HEAD。没有采信项时等于被审 HEAD；有采信项时等于全部采信项修复后的 `修复提交`。
_Avoid_: 固定点、被审 HEAD、当前 HEAD、分支名

**修复提交**：
一次审查的全部采信项修复完成时的分支 HEAD。修复不派审查者。
_Avoid_: 被审 HEAD

**审查记录**：
审查者原始报告和主 agent 处置。它的位置按[路径形状](./artifact-location.md)确定，类别根是 reviews 根。
_Avoid_: subagent 报告、聊天摘要

**路径形状**：
(authoritative: [路径形状](./artifact-location.md))

**逐份验收**：
已取消的第三道审。`worker` 交回完成后，主 agent 直接把结果分支合入任务分支。
_Avoid_: 三关、亲手验证

**合同门**：
已取消的第四道审。不要发起。
_Avoid_: 人工审批关卡、final 终审
