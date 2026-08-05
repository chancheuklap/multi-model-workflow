# Agent 协作

这个上下文定义 MMW 派发独立执行者、接收结果并建立可信结论时使用的语言。

## Language

**主 agent**：
拥有当前 MMW 任务、作出流程判断并验证关键断言的 agent。
_Avoid_: 主线程、协调线程

**subagent**：
在独立上下文中完成一项有边界工作的 agent。subagent 的报告不是已验证结论。
_Avoid_: 子代理、sub-agent

**角色**：
规定一类 subagent 的责任、可写范围和交付形状的稳定名字，例如 `worker`、`planner` 和 `reviewer-gpt`。
_Avoid_: 模型、技能

**task**：
主 agent 派给 subagent 的四栏执行说明，固定包含目标、读、约束和验收。
_Avoid_: brief、agent brief、完整提示词

**报告**：
subagent 交回的产出，包括完工报告、调查报告和审查报告。
_Avoid_: 回执、已验证结论

**验证**：
主 agent 使用当前源码、diff、命令或一手来源判断关键断言是否成立的责任。
_Avoid_: 复核、核验、亲验

**结果分支**：
subagent 在独立结果 worktree 中提交产出的分支。结果分支只有通过结果验证后才能集成到任务分支。
_Avoid_: 任务分支、临时目录

**结果验证**：
主 agent 对结果分支、HEAD SHA、基点 SHA 和交付证据进行的接收检查。
_Avoid_: 审查、合并
