---
name: mmw-dispatching-agents
description: >
  把一件活派给隔离上下文的 subagent。在要派 worker、planner、investigator、
  审查者，或别的技能写「按 /mmw-dispatching-agents 派」时用。
---

把活派给隔离上下文的 subagent。你编排；它执行。

## 派不派

**默认派。** 仅下面情况自己做：要跟用户来回；结论必须由你对用户负责；事先写不出 brief、只能边看边定方向；一句话就做完、派发往返更慢。

subagent 内部的探路照派。只有**你**要换判断方向时才留下。

**一个方向一个人。** 多方向就多派，并行时同一条消息里多个调用。

## 角色 → agent

| 角色 | agent | 可写 |
| --- | --- | --- |
| `worker` | `mmw-worker` | 是 |
| `worker-high-risk` | `mmw-worker-high-risk` | 是 |
| `planner` | `mmw-planner` | 是 |
| `investigator` | `mmw-investigator` | 否 |
| `reviewer-gpt` | `mmw-reviewer-gpt` | 否 |
| `reviewer-claude` | `mmw-reviewer-claude` | 否 |

哪两个审查角色、何时升 `worker-high-risk`，由调用你的技能决定。

## 步骤

### 1. 写 task

task 只含：要交付什么、**去读哪些路径**（或 tracker 上读什么）、边界与验收。
路径用 subagent 工作目录里能打开的地址。仓库内路径先确认存在。

**不要**把文件正文写进 task。subagent 自己读。
**不要**传 model、thinking、context、async、skill——agent 定义里已有。

调用方技能若列出「task 里要点名的路径/材料」，照那份清单写，不在这里重复。

可选：把同一段 task 存成 worktree 下 `.dispatch/<名>.md`（审查用 `.reviews/`）便于留痕；派发时 task 仍是这段文字，或写「先读该文件再执行」。

### 2. 可写角色清场

可写角色：在目标 worktree 跑 `git status --porcelain`。有输出就停，先清理。
并记下该 worktree 的绝对路径，派发时作 `cwd`。

### 3. 调用

用宿主的 subagent 工具，传入：

- `agent`：上表名字
- `task`：第 1 步那段
- `cwd`：可写角色必给 worktree 绝对路径

同一轮并行就发多个调用。

### 4. 收回

完成后把报告交 `/mmw-verifying-agent-output`。未验证不当事实用。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告已交回 | **移交**：`/mmw-verifying-agent-output` |
| 验证后要重派 | **自己继续**：task 补上缺的路径或修复说明，再走第 2–3 步（新会话，不续接） |
| 可写 worktree 不干净 | **停**：列出未提交改动 |
| task 里的路径不存在 | **自己继续**：改路径或补材料后再派 |
