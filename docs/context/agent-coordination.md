# Agent

这个 Context 定义 MMW 中主 agent 与 subagent 的责任和交付。

## Language

**主 agent**：
发起并协调其他 agent，作出流程判断，并验证关键断言。
_Avoid_: 主线程

**subagent**：
在独立上下文中完成一项有边界工作的 agent。
_Avoid_: 子代理、sub-agent

**角色**：
subagent 使用的稳定字面串，例如 `worker`、`planner`、`investigator` 和 `reviewer-gpt`。
_Avoid_: 中文角色别名、技能名、模型名

**task**：
主 agent 派给 subagent 的四栏表，固定包含目标、读、约束和验收。
_Avoid_: brief、agent brief、简报

**报告**：
subagent 交回的内容。
_Avoid_: 回执、笔记

**handoff**：
供另一个 agent 接续当前会话的文档。
_Avoid_: 交回评论、报告

**验证**：
主 agent 使用当前源码、diff、命令输出或一手来源检查事实。
_Avoid_: 复核、核验、亲验

**任务分支**：
承载当前 MMW 任务正式改动的分支。
_Avoid_: 结果分支、默认分支

**结果分支**：
可写 subagent 在独立 worktree 中提交结果的分支。
_Avoid_: 任务分支、临时目录

**任务 worktree**：
用户用宿主打开的 linked worktree，加上这条树上的任务分支。agent 不创建任务树。
_Avoid_: 任务工作树、Codex App 后台 Worktree 任务

**基点 SHA**：
派发结果分支前记录的任务分支提交。

**`mmw result verify`**：
验证结果分支、HEAD SHA 和基点 SHA 与报告一致的命令。
_Avoid_: 审查、集成
