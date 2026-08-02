---
name: mmw-code-review
description: 审从某个固定点到 HEAD 的改动，分三轴——Standards（合不合这个仓库写下来的编码标准）、Spec（做的是不是原始 issue 或 spec 要的那件事）、Correctness（这段代码到底能不能正确工作）。每一轴各派各的审者，每一轴至少有一路跟写这段代码的不是同一家模型。findings 逐条复核过才进报告。用户说要审一个分支、审一个 PR、审还没提交的改动，或者说「审一下从 X 以来的改动」时用它；派工人写完代码的技能也用它起审。
---

审 `HEAD` 与用户给的那个固定点之间的 diff，分三轴：

- **Standards** —— 这段代码合不合这个仓库写下来的编码标准？
- **Spec** —— 这段代码忠实实现了原始的 issue 或 spec 吗？
- **Correctness** —— 这段代码到底能不能正确工作？

每一轴各派各的审者，互相不污染上下文；然后由本技能逐条复核所有 findings，把三轴并排报出来。

issue tracker 的配置应该已经给你了，`docs/agents/issue-tracker.md` 不在就跑 `/mmw-setup`。谁审哪一轴由 `docs/agents/models.md` 定。

## 流程

### 1. 钉住固定点

用户说的那个就是固定点——一个提交号、分支名、标签、`main`、`HEAD~5` 都行。他没说就问他要。**复审时的固定点不是他第一次说的那个**，见第 7 步。

把 diff 命令一次记下来：`git diff <固定点>...HEAD`（三个点，比的是分叉点）。同时用 `git log <固定点>..HEAD --oneline` 记下提交清单。

往下走之前先确认这个固定点解析得出来（`git rev-parse <固定点>`），而且 diff 非空。引用写错或者 diff 是空的，要在这里就失败，不要等到三路审者已经派出去才发现。

### 2. 找出 spec 在哪

按这个顺序找原始的 spec：

1. 这个分支上的 `docs/specs/<slug>/`，`<slug>` 就是分支名——布局见 `docs/agents/worktrees.md`。
2. 提交信息里引用的 issue（`#123`、`Closes #45` 之类），按 `docs/agents/issue-tracker.md` 取。
3. 用户当参数传进来的路径。
4. `docs/` 或 `specs/` 下任何一份跟这个分支名或这个功能对得上的 spec 文件。
5. 全都找不到就问用户 spec 在哪。他说没有，就整个跳过 **Spec** 轴，并在报告里说明。

### 3. 找出标准写在哪

仓库里任何一份规定代码该怎么写的文档，比如 `CODING_STANDARDS.md` 或 `CONTRIBUTING.md`。

除了仓库自己写下来的那些，Standards 轴永远还带一份 **smell baseline**——一组固定的 Fowler 代码气味，仓库什么都没写时它照样适用。它在本文件旁边的 `standards.md` 里，连同约束它的两条规矩：仓库写下来的标准永远压过这份基线，而且每一条气味都是判断题，不是硬性违规。

### 4. 派审者

四个审者，一条消息发出去。机制按 `/mmw-dispatching-agents`，各自用什么模型按 `docs/agents/models.md`。

| 轴 | 谁来审 |
| --- | --- |
| Standards | 一个 Claude sub-agent |
| Spec | 一个 Claude sub-agent |
| Correctness | 一个 Claude sub-agent **加**一个 Codex 无头审者 |

代码是 Codex 工人写的，所以每一轴上至少有一路审者来自另一家——这是 `models.md` 的红线，不是偏好。Correctness 多带一个同家审者，因为它是漏掉代价最大的一轴，也是两家盲区差别最大的一轴。两个 Correctness 审者拿到的提示词完全相同。

每一份提示词都从文件里组装，不凭记忆：

1. `reviewer-brief.md` 全文——共用的纪律。
2. 正好一份轴文件——`standards.md`、`spec.md` 或 `correctness.md`——先把里面的 `<!-- Main thread: -->` 占位填掉。
3. 第 1 步记下的 diff 命令和提交清单。

每份组装好的提示词写到 `.reviews/<slug>-code-review-<轮次>-<轴>.prompt.md` 再从那里派发（需要就先 `mkdir -p .reviews`；轮次从 1 起）。无头审者从 stdin 读它；sub-agent 则被告知去读那个路径，把它当作自己全部的简报。**绝不要给审者一个本插件内部的路径**——无头那一侧读不到，读不到就会自己编一个。

第 2 步没找到 spec，就撤掉 Spec 审者，并在报告里记一句。

### 5. findings 先落盘，再逐条裁判

把每个审者的 findings **原样**抄进 `.reviews/<slug>-code-review-<轮次>.md`，按轴分组。不要重写，不要摘要。文件顶部写一行，记下固定点的提交号。

然后按 `/mmw-judging-agent-output` 逐条过：自己重新复核每一条的锚，问不修会伤到谁、这一轮该不该花预算修，然后在每条下面标一个处置词——`accepted`、`rejected`、`duplicate`、`needs-evidence` 或 `waived`。文末写一句总结论。

只有 `accepted` 驱动返工。搁置的 findings 里说得清伤害面的开成 GitHub issue 打 `needs-triage`，其余的活在报告里、也死在报告里。

### 6. 报告

分 `## Standards`、`## Spec`、`## Correctness` 三节呈现，每条 finding 都带着它的处置词，包括被判 `rejected` 的那些。**不要跨轴合并或者重排**——三轴是刻意分开的（见「为什么是三轴」）。逐条复核 findings 不算重排，也不构成把三轴揉成一张清单的理由。

每一轴末尾给出这一轴报了几条、采信几条，以及这一轴里最严重的那条采信项。不要跨轴评出一个总冠军，那正是分轴要防的重排。最后加一行讲搁置的：搁的是什么、现在由哪张 issue 收着。

### 7. 修完之后的复审

采信的 findings 修好、分支回来时：

- 固定点变成上一轮的 `HEAD`，那一轮的留痕文件顶部记着它。审者只看这次修复的 diff。
- 告诉每个审者这是一次复审，并把上一轮留痕文件的路径给它。它的任务只有两件：采信的那些是不是真的修了，修的过程有没有弄坏别的。
- 已经标成 `rejected`、`duplicate` 或 `waived` 的，没有新证据不许再提。换个说法重提不算新证据。
- 同一条 `accepted` 修过两轮还在，停下来。自问是修错了地方，还是这条根本不该采信，然后把这件事带给用户。

## 为什么是三轴

一次改动可以过了一轴、栽在另一轴：

- 每条标准都守住了，但做的是错的事情 → **Standards 过，Spec 挂。**
- 完全按 issue 说的做了，但违背了项目的写法约定 → **Spec 过，Standards 挂。**
- 写得好、也做了要它做的事，可是在失败路径上漏了一个空值 → **Standards 过，Spec 过，Correctness 挂。**

分开报，一轴才不会遮住另一轴。第三轴存在的理由是：前两轴都是拿代码去比一份文档——一份是约定，一份是 spec——而一段 diff 可以跟两份文档都严丝合缝，却还是不能工作。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 报告写完，一条 `accepted` 都没有 | **移交**：回到把你叫起来的那个技能，由它决定合并和交回 |
| 有 `accepted` 的 findings | **移交**：回到调用方，由它把这些打包成一张修复 ticket 派给新工人；修完再回本技能第 7 步复审 |
| 用户直接叫你来审，没有调用方 | **停**：报三轴各几条、采信几条、最严重的是哪一条，让他定这一轮修不修 |
| 第 1 步的固定点解析不出来，或者 diff 是空的 | **停**：说清楚是哪一种，让用户重新给固定点。不要带着坏引用往下派审者 |
| 同一条 `accepted` 修过两轮还在 | **停**：报这条修了两轮还在，并说出你的判断——是修错了地方，还是当初不该采信 |
