# 宿主

这个 Context 定义共享 MMW 语义在 Codex App、Claude Code、Pi 和 Cursor 中的承载方式。

## Language

**技能源**：
保存共享流程语义和宿主动作的技能文件。
_Avoid_: 技能产物、安装副本

**技能产物**：
从技能源为 Pi、Claude Code 或 Codex 物化的宿主版本。
_Avoid_: 技能源、手工分叉

**物化**：
把技能源中的启动块和宿主动作块整块替换为指定宿主的原生动作。
_Avoid_: 局部字符串替换、手工改技能产物

**原生 subagent**：
由宿主自身的 agent 机制启动、并遵守 MMW 角色定义的 subagent。
_Avoid_: 外部模型 CLI、技能

**Codex App 后台 Worktree 任务**：
Codex App 为 `worker`、`worker-high-risk` 和 `prototype-worker` 创建的独立任务与 worktree。
_Avoid_: 原生只读 subagent、任务 worktree
