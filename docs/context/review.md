# 审查

这个 Context 定义 `/mmw-review` 和 `/mmw-reviewer` 使用的语言。

## Language

**六道审**：
spec 审、plan 审、逐份验收、合同门、final 终审和合并集成审。
_Avoid_: 人工审批关卡

**视角（任务名）**：
一名审查者在独立上下文中检查的一个角度；task 的目标栏第一句使用表中任务名。
_Avoid_: 六道审、自定义任务名、视角摘要

**finding**：
审查者报告的一个可定位问题候选。
_Avoid_: 已确认缺陷、ReleaseFinding、建议清单

**处置**：
主 agent 对 finding 使用的五个标记：`accepted`、`rejected`、`duplicate`、`needs-evidence` 和 `waived`。
_Avoid_: finding、修复状态

**固定点**：
final 终审或合并集成审用于限定 diff 范围的提交。
_Avoid_: 当前 HEAD、分支名

**审查记录**：
保存在 `.reviews/` 中的审查者原始报告和主 agent 处置。
_Avoid_: subagent 报告、聊天摘要

**合同门**：
主 agent 在全部实现合入任务分支后检查跨 plan 合同是否兑现的第四道审。
_Avoid_: 人工审批关卡、final 终审
