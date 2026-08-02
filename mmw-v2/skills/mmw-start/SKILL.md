---
name: mmw-start
description: 多模型工作流的入口——判定这次的任务走哪条路，定 slug，建 worktree 并进去，把用户原话记进第一个提交，然后移交给对应技能。用户开始一件新任务、提一个新需求、报一个 issue 编号、说要接着做某张 map、说有东西坏了、或者只说要开工时用它；没有交代任何内容时，它报当前任务的进度。
argument-hint: "[bug|big] [要做的事，或者一张 map 的编号]"
---

本技能只做路由，这次任务本身一个字都不实现。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)——那是回来接着做，不是开新任务。已经在一个任务 worktree 里的，同样走 [resuming.md](resuming.md)。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。标签是他替你把判断定死的，有就直接用，不要再推断。

| 情况 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，带着某个 `wayfinder:` 类型标签——那是一张 map 上的一条 decision ticket | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，挂在一张带 `wayfinder:map` 标签的 issue 底下、自己不带 `wayfinder:` 标签——那是收尾时切出来的一份 spec | **移交**：`/mmw-to-spec` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`/mmw-triage` |
| 一个 issue 编号，已是 `ready-for-agent`，brief 写明 `**Test seam:**`，而且只碰一处 | **移交**：`/mmw-implement` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`/mmw-diagnosing-bugs` |
| 一个 effort，还不知道要拆成哪几份 spec，或者挂了 `big` | **移交**：`/mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`/mmw-prototype` |
| 只要一条查得清的事实，比如某个库或某个外部接口的官方说法 | **移交**：`/mmw-research`。这不是一件要建 worktree 的任务，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`/mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`/mmw-improve-codebase-architecture`。要动哪里还没定，跳过第 2、3 步 |
| 几条并行分支要合到一起，或者合并冲突要解 | **移交**：`/mmw-review` 的 ⑥ 合并集成审。这条路线不建任务 worktree，跳过第 2、3 步 |

三种情况都通向 `/mmw-wayfinder`，但进去之后走的不是同一条路：报了 map 编号或某条 decision ticket 编号的，是回来认领一条链；报了一个还不知道要拆成几份 spec 的 effort，是要建一张新 map。判定归 `/mmw-wayfinder`，你只要把用户原话原样传过去。

**同一张 map 底下的两种 issue 靠标签分**：带 `wayfinder:` 类型标签的是还没解开的决定，归 `/mmw-wayfinder`；不带的是收尾时切出来、可以开始做的一份 spec，归 `/mmw-to-spec`（见 `docs/agents/triage-labels.md`）。这两种都不要送去分诊——它们已经评估过了。

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `/mmw-prototype`；他要的是先把这件事说清楚，走 `/mmw-grilling`。分不出来时走 `/mmw-grilling`，它问到定不下来时会自己转过去。

**effort 怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得完、拆出的 ticket 都挂在这份 spec 底下，走 `/mmw-grilling`，谈定之后由它移交 `/mmw-to-spec`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没有答案，才是 `/mmw-wayfinder`——它先把这堆决定画成一张 map，逐条散掉 fog of war，再派生出各份 spec。范围已经清楚的功能不要推进 `/mmw-wayfinder`，它慢得多也重得多。

带 issue 编号的，先按 `docs/agents/issue-tracker.md` 把这张 issue 读出来再判，不要只看编号。

## 2. 定 slug

形状是 `<类型>-<短语>`，例如 `feat-phone-login`、`fix-refund-rounding`。类型取自第 1 步的判定结果：走 `/mmw-diagnosing-bugs` 的用 `fix`，新需求和先做原型的用 `feat`。完整规则在 `docs/agents/worktrees.md`。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。这个会话要做的是认领 map 上的一条链，那棵 worktree 叫什么名字，要等读完 map、选中链首 ticket 才知道，slug 由 `/mmw-wayfinder` 定。
- 判定走 `/mmw-improve-codebase-architecture`。他只说了想让代码库更好维护，要动哪一块还没定，等它扫完、用户挑中一个候选才知道，slug 由它定，类型固定用 `refactor`。
- 判定走 `/mmw-research`。查一条事实不改代码，没有要隔离的东西。
- 判定走 `/mmw-review` 的 ⑥ 合并集成审。合并在已有的分支上做，不另建一棵。

## 3. 建 worktree、进去、记原话

按 `docs/agents/worktrees.md` 建 worktree、用 `EnterWorktree` 进去，然后打那个记原话的空提交。

从主线开新任务；这次任务是从一张 `/mmw-wayfinder` 的 map 派生出来的，就从那张 map 的分支分叉。

worktree 是分支的载体，建错了重建即可，不用停下来等用户确认。报一句你定的 slug 和你要走的路线，然后接着做——他不同意会当场打断你。

**第 2 步列出的那四条路线，这一步同样跳过**，留在主仓库直接移交。`/mmw-wayfinder` 会先在主仓库读完 map，再建它自己那棵；`/mmw-improve-codebase-architecture` 扫描阶段全程只读，等用户挑中候选才建。一个会话只能进一次 worktree，在这里替它们建了 worktree，它们就没法再进自己那棵。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走——路线选错，整棵 worktree 和后面每一步都建在错的技能上 |

你在这里做的路由判断不用重复给它，它会自己重读这次的需求。
