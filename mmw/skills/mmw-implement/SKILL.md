---
name: mmw-implement
description: 把定好的需求实现成代码，一张 ticket 派一个 `worker`。用户说要开始实现、做下一张 ticket 时用它；别的技能判定某张 ticket 已是 ready-for-agent 时也用它。
---

把 spec 和它的 ticket 描述的需求实现出来。spec 已定稿，seam 已谈定；本技能执行那份计划，不重开它。

**你不写代码。** 每张 ticket 交给一个 `worker`。你的职责是准备 brief、派发、验收、发起审查。

## 流程

### 1. 确认前置条件

先确认这次需求出自哪里。碰多处的需求出自 `docs/specs/<slug>/` 里的 spec；只碰一处的需求出自 issue 上那份 `ready-for-agent` 的 agent brief。两条来源都成立。

然后下面四件事每一件都必须满足。有一件不满足就停下，说清是哪一件。

| 检查 | 怎么查 | 不满足怎么办 |
| --- | --- | --- |
| 你在任务 worktree 里 | `git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾 | `mmw task new <slug>` 建一个，或 `mmw task enter <slug>` 取路径再进去 |
| 这次需求写明了 seam | 读 spec `## Testing Decisions` 一节里那张 seam 清单表，或读 agent brief 的 `**Test seam:**` 一栏 | spec 缺就回 `/mmw-to-spec` 第 3 步，brief 缺就回 `/mmw-triage` 补 |
| ticket 存在 | `mmw issue children <spec issue 编号>` 有输出 | 先跑 `/mmw-to-tickets` |
| 这张 ticket 的 plan 写好了、过了 ② plan 审 | `docs/plans/<slug>/` 下有对应那一份 | 先跑 `/mmw-to-plan`。走 agent brief 那条路的需求没有 plan 这一层，这一行不适用 |

### 2. 取下一张 ticket

```bash
mmw issue frontier <spec issue 编号> --label ready-for-agent
```

它给出阻塞全部关闭、没人认领、带这个标签的那些，按 `/mmw-to-tickets` 的发布顺序排。**取第一行那张。**

开工前先 `mmw issue claim <编号>`。认领失败说明别的会话抢先了，取下一行。

一个 worktree 一次做一张 ticket，一个 worktree 上只站一个 `worker`。frontier 确实很宽、用户又要并行推进，就给每张 ticket 各跑一次 `mmw task new <slug>-<ticket 短语>`，它们都从你当前这条分支分叉。

### 3. 组装 `worker` 的提示词

组装规矩按 `/mmw-dispatching-agents` 的「组装与存盘」一节。装这七样：

1. 本文件旁边的 `worker-brief.md`，取 `---` 之后的全部内容。
2. TDD 纪律全文——`mmw-tdd/SKILL.md`、`mmw-tdd/tests.md`、`mmw-tdd/mocking.md`、`mmw-tdd/quality-bar.md`。
3. 目标仓库的 `TESTING.md` 全文，那是测试三层里的第三层：目录分层、哪些边界允许打桩、值从哪个权威源读。**它跟 `worker-brief.md` 以及第 2 条列出的那四个文件一起粘进去，不给路径。** 这个仓库还没有 `TESTING.md`，在 brief 里明说没有，让它按 `worker-brief.md` 加第 2 条那四个文件做。
4. spec 或 agent brief 在这个 worktree 里的路径，以及 spec `## Testing Decisions` 一节里那张 seam 清单表（agent brief 则是 `**Test seam:**` 一栏），原文引用。
5. ticket 本身：标题、要做什么、每一条验收标准，全部写进去。`worker` 能访问 tracker 也照样写。
6. **这张 ticket 对应的那份 plan，全文。** spec、ticket、plan 三样都要给：spec 给意图和合同，ticket 给边界和验收，plan 给施工权威。走 agent brief 那条路的需求没有 plan，这一条跳过。
7. 这次需求背后有原型的，给出**选中的那一版**在这个 worktree 里的路径，加上 spec 里那一节视觉契约。只给选中的那一份，`docs/prototypes/<slug>/` 下面还躺着落选变体和 TUI 壳。同时说清怎么用——逻辑原型里那个可移植模块整块搬过去，不要重写；界面变体的代码按仓库规范重写，不要照抄。

写到 `.dispatch/<slug>-<ticket>.prompt.md`。给 `worker` 的路径一律是它工作的那个仓库里的路径，插件内的路径它读不到。

### 4. 派发

**先记下当前提交号**（`git rev-parse HEAD`）。

然后按 `/mmw-dispatching-agents` 派 `worker` 角色，`--cwd` 给这棵任务 worktree 的路径。ticket 碰计费、权限、数据迁移，或者别的改错了不可逆的地方时，改派 `worker-high-risk`。**这个判断归你，不归 `worker`**——`worker` 不会自己要求升档。

### 5. 验收：亲手验证三关

按 `/mmw-review` 的 **③ 逐份验收**，三关都过才允许合并回任务分支：做漏没有、测试达不达标、有没有偏离。三关各自的判据、三关不过时的返工升级策略，都在 `/mmw-review` 目录里的 `self-review.md`——**这一道不派审查者**，`/mmw-review` 正文其余各节跟它无关。报告按 `/mmw-verifying-agent-output` 采信，它交回的四档怎么读也在那里。

三关之外还要确认一件本阶段特有的事：commit 存在，并且引用了这张 ticket。

三关都过就关闭这张 ticket，取下一张。

### 6. 全部落地后验证合同

每张 ticket 都关闭、改动都在任务分支上之后，按 `/mmw-review` 的 **④ 合同门**验证一次：spec 的 `## Cross-Plan Contract Anchors` 一节里每条跨 plan 合同，在合并后的代码里真兑现了。逐条要查什么、合同条数多时怎么把取证派出去，在 `/mmw-review` 目录里的 `self-review.md`——**这一道也不派审查者**。

**grep 不到行号就不算兑现**，回去补，不要留给终审。这是本阶段特有的一句：终审那一道审的是代码本身，不替你补合同。

### 7. 发起 ⑤ final 终审

合同门过了之后，按 `/mmw-review` 发起一轮 **⑤ final 终审**，固定点取分支点。整体审一次，不逐张审。

分支点用 `git merge-base HEAD <父分支>` 取。父分支通常是主线；这次任务从一张 `/mmw-wayfinder` 的 map 分出来的，父分支就是那张 map 的分支。

采信的 findings 打包成一张修复 ticket 派给新 `worker`，带上 `file:line` 和要改成什么。然后按 `/mmw-review` 第 7 步复审。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 5 步三关都过，frontier 上还有 ticket | **自己继续**：回第 2 步取下一张 |
| 所有 ticket 都关闭了 | **自己继续**：走第 6 步验证合同，过了再走第 7 步发起 ⑤ final 终审 |
| 第 6 步有合同 grep 不到行号 | **停**：报是哪条合同、提供方或消费方缺在哪 |
| 审出了采信的 findings | **自己继续**：打包成一张修复 ticket 派新 `worker`，然后按 `/mmw-review` 第 7 步复审 |
| 审完没有采信项，或者修复已经复审通过，而且这次改动碰了带出包配置的产品 | **移交**：`/mmw-release`，先把安装包出出来。仓库里有没有出包配置，跑 `grep -rl '"product"' --include='*.release-adapter.json' .` |
| 审完没有采信项，或者修复已经复审通过，这次不用出包 | **移交**：`/mmw-closing`，把 spec 与 plan 归档到 Wiki、删掉本地的 `docs/specs/<slug>/` 与 `docs/plans/<slug>/`，再交回用户合并 |
| 第 1 步四项前置有一项不满足 | **停**：说清是哪一项。缺 seam 的按第 1 步那张表回 `/mmw-to-spec` 第 3 步或 `/mmw-triage`，不要自己替用户定 seam |
| `worker` 卡在 ticket 与代码互相矛盾上 | **停**：把矛盾交给用户，不要换一个 `worker` 再派一遍 |
| `worker` 交回的不是「完成」，也不是因为矛盾 | **自己继续**：按 `/mmw-verifying-agent-output` 的四档读它交回的东西，再按返工升级策略接着走 |
