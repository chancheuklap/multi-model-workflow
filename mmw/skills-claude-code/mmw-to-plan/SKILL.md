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
| 你在已绑定的任务 worktree 里 | `mmw task state` 输出以 `bound` 开头；不满足就回 `/mmw-start` 建立或绑定任务 worktree |
| spec 已定稿并过了人工审批关卡 | `docs/specs/<slug>/<slug>.md` 存在，对应的 spec issue 已发布并带着 `ready-for-agent` |
| ticket 已发布 | `mmw issue children <spec issue 编号>` 列得出这批 ticket；列不出先跑 `/mmw-to-tickets` |

## 1. 定 plan 清单

读取 spec 中的以下内容，作为派发给 `planner` 的只读上下文：

- `## Problem Statement`
- `## Solution`
- `## Implementation Decisions`
- `## Contract Boundaries`
- `## Testing Decisions` 中的 seam 清单表

本步骤不展开 plan 写作。

读取全部 ticket 的目标和阻塞关系，形成 plan 清单。每张 ticket 对应一份 plan 和一个 `planner`。

优先使用 ticket 正文 `## Plan` 中的路径：`docs/plans/<slug>/<两位编号>-<ticket-slug>.md`。照抄已有编号，不重新排序。ticket 没有 `## Plan` 时，按依赖顺序编号；被阻塞的 ticket 排在阻塞方之后。

**轻量验证现状**：用检索确认 spec 涉及的落点目录和关键路径真实存在，够你判断派几个 `planner`、各管哪张 ticket 就行。深度探代码由 `planner` 各自做，你不抢着探全。

术语或验收标准不清楚，回 `/mmw-to-spec` 改；架构假设跟代码现实对不上，先弄清楚再派。

## 2. 把合同落到 plan 头上

**这一步在派 `planner` 之前做**，多份 plan 时必做，只有一份 plan 时跳过。

在 spec 里新增一节 `## Cross-Plan Contract Anchors`，**不改已有的 `## Contract Boundaries`**。

从 `## Contract Boundaries`、`## Implementation Decisions` 和 ticket 依赖中识别跨 plan 连接面：

- 共享文件或共享 module：写明文件归属，一个文件只归一份 plan。
- 共享数据结构或跨 plan interface：写明提供方、消费方和命名；精确字段与签名先标「字段待回填」。

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

启动：把四栏表写入 task 文件，后台执行 `mmw dispatch planner --task <task 文件绝对路径> --cwd <当前任务 worktree 绝对路径>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。

互不依赖的 plan：同一条消息里并行启动多个 `planner`。有依赖链：按依赖顺序启动。`planner` 使用当前任务 worktree，不建独立 worktree，不提交。每个 `planner` 只写自己的 plan 文件。

## 4. 验证返回

每个 `planner` 交回 `pass` 之后，对它声明的事实至少抽验一条再采信：plan 文件真的存在、任务包数量对得上、它引用的 `文件:行号` 引得出来。读取文件并检索源码，不认「我写完了」。

失实就把原 task 加上修复说明重派一次。交回 `needs-context`、`needs-repair` 或 `blocked` 的，按它说的补路径或修 spec 之后重派。

## 5. 回填精确字段，验证边界

根据以下来源回填「字段待回填」：

- 每份 plan 的文件与职责表。
- 合同锚点、迁移和登记。
- `planner` 报告的 `Cross-plan touchpoints`。

回填后验证：

- 文件归属没有冲突。
- 提供方 interface 与消费方预期一致。
- 迁移和登记位置完整。

验证失败时，重派拥有对应 plan 的 `planner`。

## 6. 发起 ② plan 审

**全部 plan 都验证过、合同也回填完之后，发起一次审查，不逐份发起。** 按 `/mmw-review` 走。

## 7. 提交

plan 文档和 spec 的 `## Cross-Plan Contract Anchors` 分两次提交。`planner` 不提交，改动一直是未暂存的，由你统一收。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| plan 审过了 | **移交**：`/mmw-implement`，一张 ticket 一个 `worker` 开始落地 |
| 审出了采信的 findings | **自己继续**：重派 `planner` 改 findings 点名的那份 plan 路径，改完回第 6 步复审 |
| 第 4 步某个 `planner` 交回 `needs-context` 或 `needs-repair` | **自己继续**：按它说的补上下文或修 spec，然后带上补齐的材料重派 |
| 第 5 步发现 `planner` 认领了别人归属的文件，或者提供方跟消费方对不上 | **自己继续**：重派 `planner` 修那一份，不要自己动它的 plan |
| 前置三项有一项不满足 | **停**：说清是哪一项。缺 ticket 的回 `/mmw-to-tickets`，缺 spec 的回 `/mmw-to-spec` |
| `planner` 交回 `needs-redirection` | **停**：把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去 |
| `planner` 交回 `blocked`，或者同一份 plan 返修三轮还没过 | **停**：报是哪一份、卡在哪里、三轮各自改了什么，让用户定 |
