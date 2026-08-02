---
name: mmw-start
description: 多模型工作流的入口——判定这次的任务走哪条路，定 slug，建 worktree 并进去，把用户原话记进第一个提交，然后移交给对应技能。用户开始一件新任务、提一个新需求、报一个 issue 编号、说要接着做某张 map、说有东西坏了、或者只说要开工时用它；没有交代任何内容时，它报当前任务的进度。
argument-hint: "[bug|big] [要做的事，或者一张 map 的编号]"
---

# 开工

这是多模型工作流的入口。它自己不实现任何东西，只做四件事：判定路线、定 slug、建立任务隔离、移交。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)——那是回来接着做，不是开新任务。已经在一个任务 worktree 里的，同样走那份文件。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。标签是他替你把判断钉死的，有就直接用，不要再推断。

| 他带来的 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`/mmw-wayfinder` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`/mmw-triage` |
| 一个 issue 编号，已是 `ready-for-agent`，brief 写明 `**Test seam:**`，而且只碰一处 | **移交**：`/mmw-implement` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`/mmw-diagnosing-bugs` |
| 一个 effort，还不知道要拆成哪几份 spec，或者挂了 `big` | **移交**：`/mmw-wayfinder` |
| 一个新需求，或对已有需求的改进 | **移交**：`/mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`/improve-codebase-architecture` |

第一行和第四行都通向 `/mmw-wayfinder`，但进去之后走的不是同一条路：报了 map 编号的是回来认领一条链，报了新想法的是要建一张新 map。判定归那个技能，你只要把用户原话原样传过去。

**effort 怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得完、拆出的 ticket 都挂在这份 spec 底下，走 `/mmw-grilling`，谈定之后由它移交 `/to-spec`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没有答案，才是 `/mmw-wayfinder`——它先把这堆决定画成一张 map，逐条散掉 fog of war，再派生出各份 spec。范围已经清楚的功能不要推进 `/mmw-wayfinder`，它慢得多也重得多。

带 issue 编号的，先按 `docs/agents/issue-tracker.md` 把这张 issue 读出来再判，不要只看编号。

## 2. 定 slug

形状是 `<类型>-<短语>`，例如 `feat-phone-login`、`fix-refund-rounding`。类型取自第 1 步的判定结果：走 `/mmw-diagnosing-bugs` 的用 `fix`，新需求用 `feat`，`/improve-codebase-architecture` 用 `refactor`。完整规则在 `docs/agents/worktrees.md`。

**用户报的是一张已有 map 的编号或链接，跳过这一步。** 这个会话要做的是认领 map 上的一条链，那棵 worktree 叫什么名字，要等读完 map、选中链首 ticket 才知道，由 `/mmw-wayfinder` 自己定。

## 3. 建树、进去、记原话

按 `docs/agents/worktrees.md` 建 worktree、用 `EnterWorktree` 进去，然后打那个记原话的空提交。

从主线开新任务；这次任务是从一张 `mmw-wayfinder` 的 map 派生出来的，就从那张 map 的分支分叉。

worktree 是分支的载体，建错了重建即可，不用停下来等用户确认。报一句你定的 slug 和你要走的路线，然后接着做——他不同意会当场打断你。

**用户报的是一张已有 map 的编号或链接，同样跳过这一步**，留在主仓库直接移交。`/mmw-wayfinder` 会先在主仓库读完 map 再建它自己那棵 worktree。一个会话只能进一次 worktree，在这里建了树，它就没法再进自己那棵。

## 4. 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起那个技能，把用户原话原样传过去 |

你在这里做的路由判断不用重复给它，它会自己重读这次的需求。移交之后本技能结束，后面的事归那个技能，你不在这里替它做。
