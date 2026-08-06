---
name: mmw-to-plan
description: 把已发布的 ticket 写成 plan，一张 ticket 一份，派 `planner` 写。用户说要写 plan、要把 ticket 展开成可落地的实施步骤时用它；刚把 spec 拆完 ticket 的技能也移交这里。
---

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

把每张 ticket 写成一份 plan，供后面派 `worker` 照着落地。

**你不写 plan。** 写作全部下放给 `planner`，一张 ticket 一个。你的职责是定清单、划合同边界、派发、验证、回填、发起审查。

## 前置条件

三件事必须满足，缺一件就停下说清是哪一件。

| 检查 | 怎么查 |
| --- | --- |
| 你在已绑定的任务 worktree 里 | `mmw task state` 输出以 `bound` 开头；不满足就回 `$mmw:mmw-start` 建立或绑定任务 worktree |
| spec 已定稿并过了人工审批关卡 | `docs/specs/<slug>/<slug>.md` 存在，对应的 spec issue 已发布并带着 `ready-for-agent` |
| ticket 已发布 | `mmw issue children <spec issue 编号>` 列得出这批 ticket；列不出先跑 `$mmw:mmw-to-tickets` |

## 0. 收敛旧状态

开始写 plan 前，重新读取全部子 issue，并逐张读取评论和标签。第 8 步定义的 `<!-- mmw:plan-review-passed -->` 是 plan 过审的 tracker 凭据。凡是带 `ready-for-agent`、但没有该标记的 tracer bullet ticket，都是升级前旧状态；先移除标签：

```bash
gh issue edit <ticket 编号> --remove-label ready-for-agent
```

只对当前带标签但缺少标记的 ticket 运行移除命令。移除后重新读取对应 ticket，确认旧标签已经消失。plan 文件存在或旧标签存在都不能证明 ② plan 审通过。

然后独立确认这批 ticket 是否已经全部通过 ② plan 审。已经通过，只因 tracker 状态不齐而重新进入本技能时，直接走第 8 步。仍未通过时，确认全部缺少标记的 tracer bullet ticket 都不再带 `ready-for-agent`，再进入第 1 步。

## 1. 定 plan 清单

读 spec，取出 `## Problem Statement`、`## Solution`、`## Implementation Decisions`、`## Contract Boundaries`、`## Testing Decisions` 一节里那张 seam 清单表。**只读，作为派发时给 `planner` 的上下文**，不在这里展开写作。

取全部 ticket，读出各自要做什么和被谁阻塞，定下 plan 清单：**一张 ticket 一份 plan 一个 `planner`**。落点就是每张 ticket 正文 `## Plan` 一节写着的那个路径（`docs/plans/<slug>/<两位编号>-<ticket-slug>.md`），编号照抄，不自己重排。ticket 正文没有这一节，按依赖顺序自己编号，被阻塞的排在阻塞它的后面。

**轻量验证现状**：用检索确认 spec 涉及的落点目录和关键路径真实存在，够你判断派几个 `planner`、各管哪张 ticket 就行。深度探代码由 `planner` 各自做，你不抢着探全。

术语或验收标准不清楚，回 `$mmw:mmw-to-spec` 改；架构假设跟代码现实对不上，先弄清楚再派。

## 2. 把合同落到 plan 头上

**这一步在派 `planner` 之前做**，多份 plan 时必做，只有一份 plan 时跳过。

在 spec 里新增一节 `## Cross-Plan Contract Anchors`，**不改已有的 `## Contract Boundaries`**。

从 `## Contract Boundaries`、`## Implementation Decisions` 两节和 ticket 的依赖关系判断有没有跨 plan 的连接面——共享文件、共享模块、共享数据结构，或者一份 plan 产出、另一份 plan 消费的接口。有就把**骨架**写进刚新增的 `## Cross-Plan Contract Anchors`：

- **文件归属**：哪份 plan 可以碰哪些共享文件。一个文件一个归属方。
- **跨 plan 接口**：按 plan 编号写清谁提供、谁消费（比如「01 提供鉴权令牌接口，02 消费」）。命名要到位，**精确字段和签名先标「字段待回填」**，第 5 步补实。

没有跨 plan 连接面就在这一节写明「无跨 plan 共享合同」。

这一节随 spec 进入 `planner` 的上下文：`planner` 不许认领别份 plan 归属的文件。

## 3. 派 `planner`

一张 ticket 一个 `planner`。按 **四栏表**（目标 / 读 / 约束 / 验收）填写：

| 栏 | 本角色填写 |
| --- | --- |
| 目标 | 为 ticket `#<编号>` 写 plan，落到指定路径 |
| 读 | ① 本 worktree 内 spec 路径；② ticket issue 编号；③ plan 落点路径（ticket `## Plan` 或本技能「1. 定 plan 清单」所定）；④ prototype 资产目录 `docs/prototypes/<slug>/`，并点名用户选中的版本和对应逐轮记录路径（无则写「无 prototype 资产」）；⑤ `mmw skill-path planner` 有输出则写入该方法论路径，无输出写「无（宿主已注入）」 |
| 约束 | 只写该 plan 文件；不提交；不认领 `## Cross-Plan Contract Anchors` 划给别人的文件；不写其它 plan 的正文 |
| 验收 | plan 文件存在且可被抽验；任务包覆盖 ticket `#<编号>` 的验收（详见 issue，不抄正文） |

启动：按名称调用 Codex 原生 subagent `mmw-planner`，task 传四栏表全文；该 subagent 直接使用当前任务 worktree，不创建后台 worktree 任务。互不依赖的实例在同一条消息中并行启动，全部完成后再汇总。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的调查、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告；报告交回后只按 `$mmw:mmw-verifying-agent-output` 验证关键断言，不重做整个 task。

互不依赖的 plan：同一条消息里并行启动多个 `planner`。有依赖链：按依赖顺序启动。`planner` 使用当前任务 worktree，不建独立 worktree，不提交。每个 `planner` 只写自己的 plan 文件。

## 4. 验证返回

每个 `planner` 交回 `pass` 之后，对它声明的事实至少抽验一条再采信：plan 文件真的存在、任务包数量对得上、它引用的 `文件:行号` 引得出来。读取文件并检索源码，不认「我写完了」。

失实就把原 task 加上修复说明重派一次。交回 `needs-context`、`needs-repair` 或 `blocked` 的，按它说的补路径或修 spec 之后重派。

## 5. 回填精确字段，验证边界

把第 2 步标着「字段待回填」的格子补成真实的归属方、提供方、消费方和字段，写回 `## Cross-Plan Contract Anchors`。入口是每份 plan 的文件与职责表、合同锚点、迁移与登记，以及 `planner` 报告里的 `Cross-plan touchpoints`。

验证两件事：有没有 `planner` 认领了别人归属的文件；提供方声明的接口跟消费方期望的对不对得上。对不上就重派一个 `planner` 修那一份。

## 6. 发起 ② plan 审

**全部 plan 都验证过、合同也回填完之后，发起一次审查，不逐份发起。** 按 `$mmw:mmw-review` 走。

## 7. 提交

plan 文档和 spec 的 `## Cross-Plan Contract Anchors` 分两次提交。`planner` 不提交，改动一直是未暂存的，由你统一收。

## 8. 标记 ticket 就绪

全部 plan 通过 ② plan 审，而且第 7 步完成后，重新读取全部子 issue。plan 过审的结构化评论标记只在这里定义，固定字面串是 `<!-- mmw:plan-review-passed -->`。

逐张读取 ticket 评论，先确认标记是否已经存在：

```bash
gh issue view <ticket 编号> --json comments --jq '.comments[].body' | \
  grep -F '<!-- mmw:plan-review-passed -->'
```

只有查不到标记时，才评论一次。评论同时记录第 7 步完成后的当前提交，供恢复时定位当时已经提交的 plan：

```bash
plan_commit=$(git rev-parse HEAD)
gh issue comment <ticket 编号> --body "<!-- mmw:plan-review-passed -->
② plan 审已通过。
plan commit: ${plan_commit}"
```

确认评论已经包含标记后，再给该 ticket 幂等添加 `ready-for-agent`：

```bash
gh issue edit <ticket 编号> --add-label ready-for-agent
```

每次进入第 8 步都检查全部 tracer bullet ticket。已有标记的不重复评论；标签可以重复执行添加命令。中断后重跑同一步会收敛到相同状态。

添加完成后，再运行 `mmw issue children <spec issue 编号>` 重新读取全部子 issue，并逐张读取 open ticket 的评论和标签。所有 open tracer bullet ticket 都同时有 `<!-- mmw:plan-review-passed -->` 和 `ready-for-agent`，第 8 步才完成。仍有缺失时继续留在第 8 步补齐和重新检查，不得移交实现。

`ready-for-agent` 表示 ticket 的 plan 已经通过 ② plan 审。`Blocked by` 和 `mmw issue frontier` 继续决定哪张 ticket 已经无阻塞并且可以认领；只有进入 frontier 的 ticket 才能派 `worker`。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 全部 plan 过审、提交，且全部 open tracer bullet ticket 已确认同时有 `<!-- mmw:plan-review-passed -->` 和 `ready-for-agent` | **移交**：`$mmw:mmw-implement`，从 `mmw issue frontier` 返回的 ticket 开始落地 |
| 审出了采信的 findings | **自己继续**：重派 `planner` 改 findings 点名的那份 plan 路径，改完回第 6 步复审 |
| 第 4 步某个 `planner` 交回 `needs-context` 或 `needs-repair` | **自己继续**：按它说的补上下文或修 spec，然后带上补齐的材料重派 |
| 第 5 步发现 `planner` 认领了别人归属的文件，或者提供方跟消费方对不上 | **自己继续**：重派 `planner` 修那一份，不要自己动它的 plan |
| 前置三项有一项不满足 | **停**：说清是哪一项。缺 ticket 的回 `$mmw:mmw-to-tickets`，缺 spec 的回 `$mmw:mmw-to-spec` |
| `planner` 交回 `needs-redirection` | **停**：把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去 |
| `planner` 交回 `blocked`，或者同一份 plan 返修三轮还没过 | **停**：报是哪一份、卡在哪里、三轮各自改了什么，让用户定 |
