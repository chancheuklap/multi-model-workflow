---
name: mmw-dispatching-agents
description: >
  把一件活派给隔离上下文的 subagent。要启动 worker、planner、investigator
  或审查者时用。
---

把活派给隔离上下文的 subagent。你编排；它执行。
按下方「启动」四节依次做完。

## 派不派

**默认派。** 仅下列情形自己做，不启动 subagent：

- 必须和用户来回才能推进
- 结论必须由你对用户负责（不能下放）
- 事先写不出 task，只能边看边改方向
- 一句话能做完，派发往返更慢

subagent 内部的探路仍派。只有**你**要改判断方向时才留下。

**一个方向一个人。** 多个独立方向就多次启动；可并行时在同一条消息里发出多个调用。

## 角色与 agent 名

当前任务给出的是**角色名**。启动工具的 `agent` 参数必须用下表右列，不能把角色名原样当作 agent 名。

| 角色 | `agent` 参数 | 可写 worktree |
| --- | --- | --- |
| `worker` | `mmw-worker` | 是 |
| `worker-high-risk` | `mmw-worker-high-risk` | 是 |
| `planner` | `mmw-planner` | 是 |
| `investigator` | `mmw-investigator` | 否 |
| `reviewer-gpt` | `mmw-reviewer-gpt` | 否 |
| `reviewer-claude` | `mmw-reviewer-claude` | 否 |

例：任务要求派 `worker` → 工具里 `agent` 传 `mmw-worker`。

角色以当前任务说明为准（含是否改用 `worker-high-risk`、派哪个审查角色）。

## 启动

### 写 task

task 是一段给 subagent 的指令，只含：

1. 要交付什么、边界与验收  
2. **去读哪些路径**（仓库内路径派前确认存在；tracker 项写清用什么命令或 URL 读）  
3. 当前任务说明里要求写入的其它项  

路径优先写绝对路径。相对路径必须相对将传入的 `cwd` 能打开。

task **只放指令与路径**。spec、plan、纪律文件、源码的正文由 subagent 自己打开路径读取。

可选：把同一段 task 写入目标 worktree 的 `.dispatch/<名>.md`（审查类写入 `.reviews/<名>.md`）便于留痕。留痕文件不是启动所必需。

**完成判据：** task 文本已定稿；其中每个声称存在的仓库内路径用 `test -e` 或等价检查为真，或不存在的已在 task 里写明「无」。

### 可写角色：确认 worktree

若角色在「角色与 agent 名」表中「可写 worktree」为「是」：

1. 在目标 worktree 根执行 `git status --porcelain`  
2. 有任何输出 → **停**，先清理，不启动  
3. 记下该 worktree 根的**绝对路径**，启动时作 `cwd`

只读角色（表中「可写 worktree」为「否」）跳过本节。

**完成判据：** 可写角色已有干净 worktree 的绝对路径；只读角色无额外状态。

### 调用宿主工具

使用本宿主启动已安装 agent 的工具。

- **Pi：** 工具名是 `subagent`  
- **Cursor：** 使用 Cursor 启动 agent 的对应工具（agent 名与 `~/.cursor/agents/mmw-*.md` 一致）

传入参数**仅限**：

| 参数 | 值 |
| --- | --- |
| `agent` | 「角色与 agent 名」表右列，例如 `mmw-worker` |
| `task` | 「写 task」小节定稿的全文 |
| `cwd` | 可写角色：必给 worktree 绝对路径。只读角色：可省略 |

`model`、`thinking`、`context`、`async`、`skill` 已在 agent 定义里，调用时不要传。

可并行的多个方向：同一条助手消息里发出多个启动调用。

**完成判据：** 每个方向都已发出一次启动调用；每次调用的参数键集合是 `{agent, task}` 或 `{agent, task, cwd}`。

### 收回

subagent 结束后，将其报告交给 `/mmw-verifying-agent-output` 验证。  
未经验证的句子不当作事实写进交付物或对用户的结论。

**完成判据：** 已打开 `/mmw-verifying-agent-output` 并按其正文处理该报告；或已根据验证结果改好 task、准备按「启动」重新跑一遍（新会话，不续接旧 subagent）。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告已交回 | **移交**：`/mmw-verifying-agent-output` |
| 验证后要重派 | **自己继续**：改 task（补路径或修复说明），再从「可写角色：确认 worktree」做到「调用宿主工具」（新会话） |
| 可写 worktree 不干净 | **停**：列出 `git status --porcelain` 的全部输出 |
| task 中的路径不存在 | **自己继续**：改正路径或补材料后，从「写 task」重做 |
