---
name: mmw-implement
description: 把定好的需求实现成代码，一张 ticket 派一个 `worker`。用户说要开始实现、做下一张 ticket 时用它；别的技能判定某张 ticket 已是 ready-for-agent 时也用它。
---

把 spec 和它的 ticket 描述的需求实现出来。spec 已定稿，seam 已谈定；本技能执行那份计划，不重开它。

**你不写代码。** 每张 ticket 交给一个 `worker`。你的职责是写清派工 task、派发、验收、发起审查。

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

### 3. 写派工 task

给 `worker` 的 task **只写指令与路径**。`worker` 自己打开路径读文件。

task 必须包含下列各项（缺一不可）：

1. `worker-brief.md` 的绝对路径：与本技能 `SKILL.md` 同目录（插件树中为 `…/mmw-implement/worker-brief.md`）。要求 worker 进门先读。
2. 本 worktree 内 spec 路径，或 issue 上 agent brief 的读取方式；并写明 seam 位置——spec 的 `## Testing Decisions` 表，或 agent brief 的 `**Test seam:**` 栏。
3. 本张 ticket：编号、标题、要做什么、每一条验收（可写在 task 正文，或写清 tracker 上如何读到全文）。
4. 本 worktree 内对应 plan 的路径；走 agent brief、无 plan 的路线则写明「无 plan」。
5. 仓库根 `TESTING.md`：有则给绝对路径，无则写「无 TESTING.md」。
6. 若有选中原型：该版在本 worktree 的路径，并指出 spec 里视觉契约所在节；写明逻辑原型可移植模块整块搬、界面按仓库规范重写。

TDD 方法论由 worker 已安装的 `mmw-tdd` 技能提供，task 不粘贴 `mmw-tdd` 下任何文件正文。

可选留痕：将 task 全文写入本 worktree `.dispatch/<slug>-<ticket>.prompt.md`。

### 4. 派发

**先记下当前提交号**（`git rev-parse HEAD`），供验收对照。

打开并执行 `/mmw-dispatching-agents` 的「启动」四节，角色为 `worker`，`cwd` 为本任务 worktree 根的绝对路径。

ticket 涉及计费、权限、数据迁移，或改错不可逆时：角色改为 `worker-high-risk`。升档由你决定，不由 worker 自报。

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
