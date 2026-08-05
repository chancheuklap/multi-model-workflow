# 宿主运行时

这个上下文定义一套共享 MMW 语义如何在 Codex App、Claude Code、Pi 和 Cursor 中形成可执行入口。

## Language

**技能源**：
`mmw/skills/` 中保存共享流程语义和宿主动作占位块的权威技能文件。
_Avoid_: 物化技能、安装副本

**物化技能**：
从技能源为指定宿主生成的完整技能文件，其中宿主动作占位块已经替换为原生动作。
_Avoid_: 技能源、手工分叉

**宿主动作块**：
技能源中由物化器整块替换的角色启动或宿主操作声明。
_Avoid_: 自然语言分支、局部字符串替换

**角色 profile**：
指定角色在一个宿主中的 agent 结构、模型和思考档配置。
_Avoid_: 技能、task

**原生 subagent**：
由宿主自身的 agent 机制启动、并遵守 MMW 角色合同的 subagent。
_Avoid_: 外部模型 CLI、技能

**后台 Worktree 任务**：
Codex App 为可写角色创建的独立任务和 worktree 执行环境。
_Avoid_: 原生只读 subagent、任务 worktree
