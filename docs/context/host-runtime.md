# 宿主

这个 Context 定义共享 MMW 语义在 Codex App、Claude Code、Pi、Cursor 和 Grok Build 中的承载方式。

## Language

**技能源**：
保存共享流程语义和宿主动作的技能文件。
_Avoid_: 技能产物、安装副本

**技能产物**：
从技能源为 Pi、Claude Code、Codex、Cursor 或 Grok 物化的宿主版本。
_Avoid_: 技能源、手工分叉

**物化**：
把技能源渲染成各宿主的技能产物。只处理宿主之间无法共用的字面差异。派发动作不在这一步，它由 `mmw launch` 按宿主动作表在运行期回答。
_Avoid_: 局部字符串替换、手工改技能产物

**宿主动作表**：
`mmw/cli/host-actions.json`。同一个角色在各宿主上怎么派、怎么续跑，只在这里定义。技能正文对所有宿主是同一句 `mmw launch …`。
_Avoid_: 在技能正文里按宿主分支、启动块

Grok Build 的安装面是用户目录：技能产物落到 `~/.grok/skills/`，角色落到 `~/.grok/agents/`。它不是 plugin 安装面。

**原生 subagent**：
由宿主自身的 agent 机制启动、并遵守 MMW 角色定义的 subagent。
_Avoid_: 外部模型 CLI、技能

**Codex App 后台 Worktree 任务**：
Codex App 为 `worker` 和 `worker-high-risk` 创建的独立任务与 worktree。
_Avoid_: 原生只读 subagent、任务 worktree

**Cursor 任务树与结果树**：
Cursor 为任务和结果创建的 linked worktree，物理位置在 `~/.cursor/worktrees/<仓库>/<slug>`。任务树由用户打开；agent 在已有的树上创建任务分支。worker 结果树由 `mmw-cursor-agent --worktree` 从当前任务分支长出。`mmw worktree add` 与 `mmw worktree remove` 在这个宿主上不可用。
_Avoid_: 仓库 `paths.worktrees`、`mmw worktree add`
