---
name: mmw-start
description: 多模型工作流的入口——认这次的活该走哪条路，起 slug，建 task worktree 进去，把用户原话记进第一个提交，然后交棒给对的技能。用户开始一件新活、提一个新需求、报一个 issue 编号、说有东西坏了、或者只说要开工时用它；不带任何内容叫起来时，它报当前任务走到哪了。
argument-hint: "<你要做的事> [bug|big]"
---

# 开工

这是多模型工作流的入口。它自己不做活，只做四件事：认路、起 slug、把任务隔离建好、交棒。

用户没带任何内容就叫起来的，走 [resuming.md](resuming.md)——那是回来接着做，不是开新活。你已经在一个 task worktree 里了，同样走那份文件。

## 1. 认路

看用户说了什么，加上他在末尾挂的标签。标签是他替你把判断钉死，有就直接用，别再猜。

| 他带来的 | 交给 |
| --- | --- |
| 一个 issue 或 PR 编号，上面还没有状态标签 | `/triage` |
| 一个 issue 编号，已经是 `ready-for-agent`，brief 里有 `**Test seam:**`，而且只碰一处 | `/implement` |
| 说有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | `/diagnosing-bugs` |
| 一大块活，路还在雾里，或者挂了 `big` | `/wayfinder` |
| 一个新需求或者对旧需求的改进 | `/grilling` |
| 没有具体的活，说想让代码库更好待 | `/improve-codebase-architecture` |

**一大块活怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得清、拆出来的 ticket 都挂在同一份 spec 底下——走 `/grilling`，谈定之后由它交给 `/to-spec`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没数——那才是 `/wayfinder`：它先把这堆决策画成一张 map，逐条散雾，再派生出各份 spec。别把一个范围清楚的功能推进 wayfinder，它慢得多也重得多。

带 issue 编号的先按 `docs/agents/issue-tracker.md` 把它读出来再判，别只看编号。

## 2. 起 slug

一个 kebab 短语，说清这次做什么，例如 `phone-login`。命名规矩在 `docs/agents/worktrees.md`。

## 3. 建树、进去、记原话

按 `docs/agents/worktrees.md` 建 worktree 并 `EnterWorktree` 进去，然后打那个记原话的空提交。

从主线开新任务；这次活是从一张 `wayfinder` 的 map 派生出来的，就从那张 map 的分支分叉。

worktree 是分支的载体，建错了重建就是，不用停下来等用户确认。报一句你起的 slug 和你要走哪条路，然后接着做——他不同意会当场打断你。

## 4. 交棒

把第 1 步选中的技能调起来，并且把用户的原话原样传过去。你在这里做的路由判断不用重复给它听——它自己会重新读这次的活。

交棒之后本技能就结束了。后面的活归那个技能，你不在这里替它做。
