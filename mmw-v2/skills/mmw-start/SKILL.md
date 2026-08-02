---
name: mmw-start
description: 多模型工作流的入口——判定这次的任务走哪条路，定 slug，建 worktree 并进去，把用户原话记进第一个提交，然后移交给对应技能。用户开始一件新任务、提一个新需求、报一个 issue 编号、说有东西坏了、或者只说要开工时用它；没有交代任何内容时，它报当前任务的进度。
argument-hint: "[bug|big] [要做的事]"
---

# 开工

这是多模型工作流的入口。它自己不实现任何东西，只做四件事：判定路线、定 slug、建立任务隔离、移交。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)——那是回来接着做，不是开新任务。已经在一个任务 worktree 里的，同样走那份文件。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。标签是他替你把判断钉死的，有就直接用，不要再推断。

| 他带来的 | 移交给 |
| --- | --- |
| 一个 issue 或 PR 编号，上面还没有状态角色 | `/triage` |
| 一个 issue 编号，已是 `ready-for-agent`，brief 写明 `**Test seam:**`，而且只碰一处 | `/implement` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | `/diagnosing-bugs` |
| 一个 effort，还不知道要拆成哪几份 spec，或者挂了 `big` | `/wayfinder` |
| 一个新需求，或对已有需求的改进 | `/grilling` |
| 没有具体需求，只说想让代码库更好维护 | `/improve-codebase-architecture` |

**effort 怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得完、拆出的 ticket 都挂在这份 spec 底下，走 `/grilling`，谈定之后由它移交 `/to-spec`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没有答案，才是 `/wayfinder`——它先把这堆决策画成一张 map，逐条散掉 fog of war，再派生出各份 spec。范围已经清楚的功能不要推进 `/wayfinder`，它慢得多也重得多。

带 issue 编号的，先按 `docs/agents/issue-tracker.md` 把这张 issue 读出来再判，不要只看编号。

## 2. 定 slug

形状是 `<类型>-<短语>`，例如 `feat-phone-login`、`fix-refund-rounding`。类型取自第 1 步的判定结果：走 `/diagnosing-bugs` 的用 `fix`，新需求用 `feat`，`/improve-codebase-architecture` 用 `refactor`。完整规则在 `docs/agents/worktrees.md`。

## 3. 建树、进去、记原话

按 `docs/agents/worktrees.md` 建 worktree、用 `EnterWorktree` 进去，然后打那个记原话的空提交。

从主线开新任务；这次任务是从一张 `wayfinder` 的 map 派生出来的，就从那张 map 的分支分叉。

worktree 是分支的载体，建错了重建即可，不用停下来等用户确认。报一句你定的 slug 和你要走的路线，然后接着做——他不同意会当场打断你。

## 4. 移交

调起第 1 步选中的技能，把用户原话原样传过去。你在这里做的路由判断不用重复给它——它会自己重读这次的需求。

移交之后本技能结束。后面的事归那个技能，你不在这里替它做。
