# Agent Operation

这个上下文定义主 agent 与 subagent 的职责、派发材料和报告可信度。它不把 subagent 当作可信信源。

## Language

**主 agent**：
拥有当前 MMW 任务、作出流程判断并验证关键断言的 agent。主 agent 可以派取证，但不能外包最终判定。
_Avoid_: 主线程、协调线程

**subagent**：
在独立上下文中完成一项有边界工作的 agent。subagent 的报告必须由主 agent 验证后才能成为结论。
_Avoid_: 子代理、sub-agent

**角色**：
规定一类 subagent 的责任、可写范围与交付形状的稳定名字，例如 `worker`、`planner`、`investigator` 和 `reviewer-gpt`。
_Avoid_: 模型、技能

**`worker`**：
在独立结果 worktree 中实现一张 ticket 并提交验证结果的写代码角色。

**`planner`**：
在当前任务 worktree 中把一张 ticket 写成一份 plan、但不提交和不改源码的计划角色。

**`investigator`**：
只读调查并逐条提供出处的事实取证角色。

**审查者**：
在独立上下文中按一个指定视角只读审查产物的角色。Codex 的角色字面串是 `reviewer-gpt`。
_Avoid_: 审者、review worker

**task**：
主 agent 派给 subagent 的四栏执行说明，固定包含目标、读、约束和验收。task 引用权威材料并补充本次运行边界。
_Avoid_: brief、agent brief、提示词全文

**报告**：
subagent 交回的产出，包括完工报告、调查报告和审查报告。报告中的自述不是已验证结论。
_Avoid_: 回执、结论

**取证**：
读取出处原文或运行指定命令并原样返回结果的动作。条目很多时可以派给 subagent。
_Avoid_: 判定、验证结论

**验证**：
主 agent 使用当前源码、diff、命令或一手来源判断关键断言是否成立的责任。
_Avoid_: 复核、核验、亲验

**verdict**：
一个角色按其合同交回的有限状态词。verdict 只描述该角色的完成状态，不自动证明产物正确。
_Avoid_: 最终结论、通过证明
