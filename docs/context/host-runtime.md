# 宿主运行时

这个上下文定义一套共享 MMW 语义如何在 Codex App、Claude Code、Pi 和 Cursor 中形成可执行入口。

## Language

**技能源**：
保存共享流程语义和宿主动作块的权威技能文件。
_Avoid_: 物化技能、安装副本

**物化技能**：
从技能源为指定宿主生成的完整技能文件，其中宿主动作占位块已经替换为原生动作。
_Avoid_: 技能源、手工分叉

**宿主动作块**：
技能源中由物化器整块替换的角色启动或宿主操作声明。
_Avoid_: 自然语言分支、局部字符串替换

**角色定义**：
规定一个角色的稳定字面串、责任、可写范围和交付形状的共享合同。
_Avoid_: 宿主 profile、角色模型配置、技能

**宿主 profile**：
指定共享角色在一个宿主中如何物化为原生 agent 文件的结构配置。
_Avoid_: 角色定义、角色模型配置、物化技能

**角色模型配置**：
指定一个角色默认模型、思考档和宿主覆盖值的配置。
_Avoid_: 宿主 profile、角色定义、agent frontmatter

**原生 subagent**：
由宿主自身的 agent 机制启动、并遵守 MMW 角色合同的 subagent。
_Avoid_: 外部模型 CLI、技能

**后台 Worktree 任务**：
Codex App 为可写角色创建的独立任务和 worktree 执行环境。
_Avoid_: 原生只读 subagent、任务 worktree
