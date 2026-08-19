# 宿主

这个 Context 定义共享 MMW 语义在 Codex App、Claude Code、Pi、Cursor 和 Grok Build 中的承载方式。

## Language

**技能源**：
`mmw/skills-src/`。保存共享流程语义和宿主动作的技能文件。五个宿主装的都是它，没有第二份。
_Avoid_: 技能产物、宿主版本、安装副本

**角色物化**：
把角色真源与模型档渲染成某个宿主的原生 subagent 文件。角色定义在各宿主的 frontmatter 形状不同，这一步只处理那个差异。收哪几个角色由 profile 的 `roles` 键决定：Claude Code 只收 `reviewer-claude`，因为其余角色在这个宿主上不经过 subagent。
_Avoid_: 技能物化、手工改 model 行

**软链安装**：
把技能源或角色文件软链进宿主自己的目录。升级 runtime 之后内容跟着变，不用重装。目标目录里同名的东西不是 MMW 装的就不动它。
_Avoid_: 拷贝安装、整目录重建

**宿主动作表**：
`mmw/cli/host-actions.json`。同一个角色在各宿主上怎么派、怎么续跑，只在这里定义。技能正文对所有宿主是同一句 `mmw launch …`。
_Avoid_: 在技能正文里按宿主分支、启动块

五个宿主的安装面都是用户目录，没有一个是 plugin 安装面。具体落点见 `AGENTS.md` 的组件表。

**原生 subagent**：
由宿主自身的 agent 机制启动、并遵守 MMW 角色定义的 subagent。
_Avoid_: 外部模型 CLI、技能

**Codex App 后台 Worktree 任务**：
Codex App 为 `worker` 和 `worker-high-risk` 创建的独立任务与 worktree。
_Avoid_: 原生只读 subagent、任务 worktree

**Cursor 任务树与结果树**：
Cursor 为任务和结果创建的 linked worktree，物理位置在 `~/.cursor/worktrees/<仓库>/<slug>`。任务树由用户打开；agent 在已有的树上创建任务分支。worker 结果树由 `mmw-cursor-agent --worktree` 从当前任务分支长出。`mmw worktree add` 与 `mmw worktree remove` 在这个宿主上不可用。
_Avoid_: 仓库 `paths.worktrees`、`mmw worktree add`
