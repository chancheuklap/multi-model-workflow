---
name: implement
description: 把定好的需求实现成代码。用户说要开始实现、做下一张 ticket、把这张 issue 做掉时用它；别的技能判定某张 ticket 已是 ready-for-agent、可以开工时也用它。一张 ticket 派一个 Codex 无头工人在任务 worktree 里写，验收之后起 code-review。
---

# Implement

把 spec 和它的 ticket 描述的需求实现出来。spec 已定稿，seam 已谈定；本技能执行那份计划，不重开它。

**你不写代码。** 每张 ticket 交给一个 Codex 无头工人。这不是偏好——`docs/agents/models.md` 不允许主线程成为代码的作者，因为作者没有资格裁判关于这份代码的 findings。你在这里的职责是准备简报、派发、验收、起审。

## 流程

### 1. 确认前置条件

先确认这次需求出自哪里。碰多处的需求出自 `docs/specs/<slug>/` 里的 spec；只碰一处的需求出自 issue 上那份 `ready-for-agent` 的 agent brief。两条来源都成立。

然后三件事必须满足。有一件不满足就停下，说清是哪一件。

| 检查 | 怎么查 | 不满足怎么办 |
| --- | --- | --- |
| 你在任务 worktree 里 | `git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾 | 按 `docs/agents/worktrees.md` 建一个或进去 |
| 这次需求写明了 seam | 读 spec 的 seam 一节，或读 agent brief 的 `**Test seam:**` 一栏 | spec 缺就回 `/to-spec` 第 2 步，brief 缺就回 `/triage` 补——工人问不到人，seam 只能由人先谈定 |
| ticket 存在 | 按 `docs/agents/issue-tracker.md` 查 | 先跑 `/to-tickets` |

### 2. 取下一张 ticket

在 **frontier** 上取：阻塞它的 ticket 全部关闭、没有 assignee、打着 `ready-for-agent` 的那些，按 `/to-tickets` 发布的顺序取。开工前先 claim 这张 ticket——这是落在它上面的第一个写动作，两个会话同时开工靠它挡住。

一个 worktree 一次做一张 ticket，一个 worktree 上只站一个工人。frontier 确实很宽、用户又要并行推进，就按 `docs/agents/worktrees.md` 从当前分支给每张 ticket 各分一个 worktree。

### 3. 组装工人的提示词

从文件里取，不凭记忆：

1. 本文件旁边的 `worker-brief.md`，全文。
2. TDD 纪律全文——`tdd/SKILL.md`、`tdd/tests.md`、`tdd/mocking.md`、`tdd/quality-bar.md`。
3. spec 或 agent brief 在这个 worktree 里的路径，以及它写明的 seam 清单，原文引用。
4. ticket 本身：标题、要做什么、每一条验收标准，全部写进去。工人能访问 tracker 也照样写——让它自己去取，可能取错一张，而且提示词就不再是你派发内容的完整记录。

写到 `.dispatch/<slug>-<ticket>.prompt.md`（先 `mkdir -p .dispatch`）。给工人的路径一律是被审仓库里的路径；插件内的路径它读不到，读不到就会自己编一个。

### 4. 派发

按 `dispatching-agents` 派。用可写 sandbox，并且首次派发之前工作区必须干净，否则你分不清哪些改动是工人的。模型档从 `docs/agents/models.md` 取——ticket 碰计费、权限或数据迁移时用高风险档。这个判断归你，不归工人。

### 5. 验收回执

按 `judging-agent-output`，完工报告是证据不是结论。采信之前：

- 把它说跑过的测试再跑一遍，读它的输出；
- 读它产出的 diff；
- 确认 commit 存在，并且引用了这张 ticket。

测试仍然是红的、报告却说完成，那是一次失败的运行，不是一张做完的 ticket。把你看到的发回去，续接同一个工人会话——上下文还在它那里。

工人自己停下的，先读它的尝试记录再做别的。工人卡在 ticket 与代码互相矛盾上，它报告的是 spec 的问题，不是它自己的问题；这件事交给用户，不是换一个工人再派一遍。

验收通过就关闭这张 ticket，取下一张。

### 6. 审整个改动

每张 ticket 都关闭之后，对这次整个 diff 跑 `/code-review`，固定点取分支点。审查要找的是一张 ticket 对另一张造成了什么影响，站在单张 ticket 里面看不见，所以整体审一次，不逐张审。

分支点用 `git merge-base HEAD <父分支>` 取。父分支通常是主线；这次任务从一张 `wayfinder` 的 map 分出来的，父分支就是那张 map 的分支。

采信的 findings 打包成一张修复 ticket 派给新工人，带上 `file:line` 和要改成什么。然后按 `/code-review` 第 7 步复审，那一步只看修复本身和它碰到的地方。

### 7. 交回

用业务语言向用户交代：现在什么能用了、什么证明它能用、什么搁置了、搁到哪里。分支可以合并了；合并和清理 worktree 由用户批准。

## 为什么工人每张 ticket 提交一次

Matt 原版是先审、最后一次性提交。这里改成每张 ticket 提交一次，因为工人是一个会中途停下的独立进程：工作区不提交，卡住的那张会连着已经做完的那些一起丢失。每张一提交也给了第 5 步需要的边界——一张 ticket、一份 diff、一件要验的事。审查仍然发生在任何东西合并之前。
