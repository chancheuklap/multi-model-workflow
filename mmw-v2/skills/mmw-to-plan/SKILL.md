---
name: mmw-to-plan
description: 把已发布的 ticket 写成 plan——一张 ticket 一份 plan，派 Codex 工人写，主线程只做编排、亲验和合同回填。用户说要写 plan、要把 ticket 展开成可落地的步骤时用它；刚把 spec 拆完 ticket 的技能也移交这里。
---

把每张 ticket 写成一份 plan，供后面派写码工人照着落地。

**你不写 plan。** 写作全部下放给 Codex 无头工人，一张 ticket 一个。你的职责是定清单、划合同边界、派发、亲验、回填、起审。

## 前置条件

三件事必须满足，缺一件就停下说清是哪一件。

| 检查 | 怎么查 |
| --- | --- |
| 你在任务 worktree 里 | `git rev-parse --show-toplevel` 以 `.worktrees/<slug>` 结尾；不在就按 `../../conventions/worktrees.md` 建一个或进去 |
| spec 已定稿并过了人闸 | `docs/specs/<slug>/<slug>.md` 存在，对应的 spec issue 已发布并带着 `ready-for-agent` |
| ticket 已发布 | 按 `../../conventions/issue-tracker.md` 取得到这批 ticket；取不到先跑 `/mmw-to-tickets` |

## 1. 定 plan 清单

读 spec，取出目标、architecture、`## Contract Boundaries` 一节、seam 清单。**只读，作为派发时给工人的上下文**，不在这里展开写作。

取全部 ticket，读出各自要做什么和被谁阻塞，定下 plan 清单：**一张 ticket 一份 plan 一个工人**。落点就是每张 ticket 正文 `## Plan` 一节写着的那个路径（`docs/plans/<slug>/<两位编号>-<ticket-slug>.md`），编号照抄，不自己重排——工人和后面的写码工人都按那个路径找。ticket 正文没有这一节，按依赖顺序自己编号，被阻塞的排在阻塞它的后面。

**轻量核现状**：用检索确认 spec 涉及的落点目录和关键路径真实存在，够你判断派几个工人、各管哪张 ticket 就行。深度探代码由工人各自做，你不抢着探全。

术语或验收标准不清楚，回 `/mmw-to-spec` 改；架构假设跟代码现实对不上，先弄清楚再派。

## 2. 把合同落到 plan 头上

**这一步在派工人之前做**，多份 plan 时必做，只有一份 plan 时跳过。

在 spec 里新增一节 `## Cross-Plan Contract Anchors`，**不改已有的 `## Contract Boundaries`**。

从合同边界那一节、architecture 和 ticket 的依赖关系判断有没有跨 plan 的连接面——共享文件、共享模块、共享数据结构，或者一份 plan 产出、另一份 plan 消费的接口。有就把**骨架**写进新那一节：

- **文件归属**：哪份 plan 可以碰哪些共享文件。一个文件一个归属方。
- **跨 plan 接口**：按 plan 编号写清谁提供、谁消费（比如「01 提供鉴权令牌接口，02 消费」）。命名要到位，**精确字段和签名先标「字段待回填」**，第 5 步补实。

没有跨 plan 连接面就在这一节写明「无跨 plan 共享合同」。

这一节随 spec 进入工人的上下文，是它的硬边界：工人不许认领别份 plan 归属的文件。

## 3. 派写计划工人

一张 ticket 一个 Codex 无头工人，按 `/mmw-dispatching-agents` 派。模型档从 `../../conventions/models.md` 的写计划工人那一行取。

派之前确认方法论装了：

```bash
ls "${CODEX_HOME:-$HOME/.codex}/skills/mmw-planner/SKILL.md"
```

不在就先跑 `/mmw-dispatching-agents` 旁边的 `install-agent-skills.sh` 装，再派。

提示词从文件里取，不凭记忆，写到 `.dispatch/<slug>-plan-<编号>.prompt.md` 再从那里派（先 `mkdir -p .dispatch`）：

1. spec 在这个 worktree 里的路径，加上它的 seam 清单原文引用。
2. **这张 ticket 的正文**：标题、要做什么、每一条验收标准、被谁阻塞，全部抄进去。工人能访问 tracker 也照样抄——让它自己去取可能取错一张，而且提示词就不再是你派发内容的完整记录。
3. plan 文件的落点路径。
4. 这次需求背后有原型的，给出**选中产物**的路径，加上 spec 里那一节视觉契约。只给选中的那一份。
5. 告诉它去自己技能目录里读 `mmw-planner`。

**每个派发只装这五样。** 别的工人的历史、别份 plan 的内容、前面几轮的完成总结，一律不进。

互不依赖的 plan 一条消息里并行发出去；有依赖链的按依赖顺序发。**不开子 worktree、不提交**：各份 plan 写不同文件，在任务 worktree 内并行是安全的。

## 4. 亲验返回

每个工人交回 `pass` 之后，对它声明的事实至少抽验一条再采信：plan 文件真的存在、任务包数量对得上、它引用的 `文件:行号` 引得出来。用读文件和检索复核，不认「我写完了」。

失实就写修复指令续接原会话打回。交回 `needs-context`、`needs-repair` 或 `blocked` 的，按它说的补上下文或者修 spec 之后续接。

## 5. 回填精确字段，核边界

把第 2 步标着「字段待回填」的格子补成真实的归属方、提供方、消费方和字段，写回 `## Cross-Plan Contract Anchors`。入口是每份 plan 的文件与职责表、合同锚点、迁移与登记，以及工人回执里的 `Cross-plan touchpoints`。

核两件事：有没有工人认领了别人归属的文件；提供方声明的接口跟消费方期望的对不对得上。对不上就续接对应工人修。

## 6. 起 ② plan 审

**全部 plan 都亲验过、合同也回填完之后，起一次审，不逐份起。** 按 `/mmw-review` 走。

采信的 findings 续接对应工人改，改完按 `/mmw-review` 复审。

## 7. 提交

plan 文档和 spec 新增那一节分两次提交。工人不提交，改动一直是未暂存的，由你统一收。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| plan 审过了 | **移交**：`/mmw-implement`，一张 ticket 一个写码工人开始落地 |
| 审出了采信的 findings | **自己继续**：续接对应工人改，改完回第 6 步复审 |
| 第 4 步某个工人交回 `needs-context` 或 `needs-repair` | **自己继续**：按它说的补上下文或修 spec，续接同一个工人会话——上下文还在它那里 |
| 第 5 步发现工人认领了别人归属的文件，或者提供方跟消费方对不上 | **自己继续**：续接对应工人修，不要自己动它的 plan |
| 前置三项有一项不满足 | **停**：说清是哪一项。缺 ticket 的回 `/mmw-to-tickets`，缺 spec 的回 `/mmw-to-spec` |
| 工人交回 `needs-redirection` | **停**：它探代码撞破了 spec 的方向。把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去 |
| 工人交回 `blocked`，或者同一份 plan 返修三轮还没过 | **停**：报是哪一份、卡在哪里、三轮各自改了什么，让用户定 |
