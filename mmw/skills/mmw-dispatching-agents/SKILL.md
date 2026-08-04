---
name: mmw-dispatching-agents
description: >
  把一件活派给隔离上下文的 subagent。在要派 worker、planner、investigator、
  审查者，或别的技能写「按 /mmw-dispatching-agents 派」时用。
---

把活派给隔离上下文的 subagent。你编排；它执行。
调用方已写好角色与 task 要点时，从「步骤」做起。

## 派不派

**默认派。** 仅下面情况自己做：要跟用户来回；结论必须由你对用户负责；事先写不出 task、只能边看边定方向；一句话就做完、派发往返更慢。

subagent 内部的探路照派。只有**你**要换判断方向时才留下。

**一个方向一个人。** 多方向就多派，并行时同一条消息里多个调用。

## 角色 → agent

| 角色（调用方写的名字） | 工具参数 `agent` | 可写 |
| --- | --- | --- |
| `worker` | `mmw-worker` | 是 |
| `worker-high-risk` | `mmw-worker-high-risk` | 是 |
| `planner` | `mmw-planner` | 是 |
| `investigator` | `mmw-investigator` | 否 |
| `reviewer-gpt` | `mmw-reviewer-gpt` | 否 |
| `reviewer-claude` | `mmw-reviewer-claude` | 否 |

调用方写 `worker` 时，工具里传 `mmw-worker`，不要传 `worker`。
哪两个审查角色、何时升 `worker-high-risk`，由调用方技能决定。

## 步骤

### 1. 写 task

写清：要交付什么、去读哪些路径（或 tracker 上读什么）、边界与验收。
路径用绝对路径，或相对即将传入的 `cwd` 能打开的路径；派前确认仓库内路径存在。

task 里只放指令与路径列表。文件内容由 subagent 打开路径自读。
调用方技能若列出「task 要点名的材料」，照那份清单写。

可选留痕：同一段文字写入 worktree 下 `.dispatch/<名>.md`（审查用 `.reviews/`）。

**完成**：task 文本已定；其中每个仓库内路径存在（或已标明「无」）。

### 2. 可写角色清场

可写角色：在目标 worktree 执行 `git status --porcelain`。有输出则停，先清理。
记下该 worktree 的绝对路径，作为 `cwd`。

**完成**：可写则 porcelain 为空且已有绝对路径；只读可跳过。

### 3. 调用

使用本宿主的 **`subagent` 工具**（不要改用其它派发入口），参数仅：

- `agent`：上表第二列（如 `mmw-worker`）
- `task`：第 1 步文本
- `cwd`：可写角色必给；只读可省

型号、思考档、后台、技能注入已在 agent 定义中，调用时不传这些键。
同一轮并行：一条消息里多个 `subagent` 调用。

**完成**：每个方向已发出调用；参数键仅为上列允许项。

### 4. 收回

报告交 `/mmw-verifying-agent-output`。未经验证的句子不当事实用。

**完成**：已移交验证，或已按验证结果准备重派 task。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告已交回 | **移交**：`/mmw-verifying-agent-output` |
| 验证后要重派 | **自己继续**：task 补路径或修复说明，再走第 2–3 步（新会话） |
| 可写 worktree 不干净 | **停**：列出未提交改动 |
| task 里的路径不存在 | **自己继续**：改路径或补材料后再派 |
