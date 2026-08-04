---
name: mmw-to-plan
description: 把已发布的 ticket 写成 plan，一张 ticket 一份，派 `planner` 写。用户说要写 plan、要把 ticket 展开成可落地的实施步骤时用它；刚把 spec 拆完 ticket 的技能也移交这里。
---

把每张 ticket 写成一份 plan，供后面派 `worker` 照着落地。

**你不写 plan。** 写作全部下放给 `planner`，一张 ticket 一个。你的职责是定清单、划合同边界、派发、验证、回填、发起审查。

## 前置条件

三件事必须满足，缺一件就停下说清是哪一件。

| 检查 | 怎么查 |
| --- | --- |
| 你在任务 worktree 里 | 当前 checkout 是已绑定 `codex/<slug>` 分支的 linked worktree；不满足就停下，让用户新建 Codex App Worktree 任务并用 `$mmw:mmw-start` 绑定分支 |
| spec 已定稿并过了人工审批关卡 | `docs/specs/<slug>/<slug>.md` 存在，对应的 spec issue 已发布并带着 `ready-for-agent` |
| ticket 已发布 | `mmw issue children <spec issue 编号>` 列得出这批 ticket；列不出先跑 `$mmw:mmw-to-tickets` |

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
| 读 | ① 本 worktree 内 spec 路径；② ticket issue 编号；③ plan 落点路径（ticket `## Plan` 或本技能「1. 定 plan 清单」所定）；④ 选中原型路径（无则写「无原型」）；⑤ `mmw skill-path planner` 有输出则写入该方法论路径，无输出写「无（宿主已注入）」 |
| 约束 | 只写该 plan 文件；不提交；不认领 `## Cross-Plan Contract Anchors` 划给别人的文件；不写其它 plan 的正文 |
| 验收 | plan 文件存在且可被抽验；任务包覆盖 ticket `#<编号>` 的验收（详见 issue，不抄正文） |



启动：先调用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`；target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型设为 `gpt-5.6-sol`，思考档设为 `high`。把四栏 task 全文作为任务提示，并要求后台任务先用 `$mmw:mmw-start` 的绑定脚本创建独立 `codex/<slug>` 分支，再完整读取 `$mmw:mmw-planner` 后工作。后台任务必须提交改动，并交回分支名、HEAD SHA 与测试结果；`create_thread` 交回 threadId 后，主 agent 用 `wait_threads` 等它完成。如果只交回 clientThreadId，先等 App 完成 worktree 设置，不能把 clientThreadId 传给 `wait_threads`。

互不依赖的 plan：同一条消息里创建多个 Codex App 后台 Worktree 任务。有依赖链：按依赖顺序创建。每个 `planner` 只写自己的 plan、提交自己的分支并交回分支名与 HEAD SHA；主 agent 逐个验证后用 `$mmw:mmw-integrate` 合入当前任务分支。

## 4. 验证返回

每个 `planner` 交回 `pass` 之后，对它声明的事实至少抽验一条再采信：plan 文件真的存在、任务包数量对得上、它引用的 `文件:行号` 引得出来。用读文件和检索验证，不认「我写完了」。

失实就把原 task 加上修复说明重派一次。交回 `needs-context`、`needs-repair` 或 `blocked` 的，按它说的补路径或修 spec 之后重派。

## 5. 回填精确字段，验证边界

把第 2 步标着「字段待回填」的格子补成真实的归属方、提供方、消费方和字段，写回 `## Cross-Plan Contract Anchors`。入口是每份 plan 的文件与职责表、合同锚点、迁移与登记，以及 `planner` 报告里的 `Cross-plan touchpoints`。

验证两件事：有没有 `planner` 认领了别人归属的文件；提供方声明的接口跟消费方期望的对不对得上。对不上就重派一个 `planner` 修那一份。

## 6. 发起 ② plan 审

**全部 plan 都验证过、合同也回填完之后，发起一次审查，不逐份发起。** 按 `$mmw:mmw-review` 走。

## 7. 提交

plan 文档和 spec 的 `## Cross-Plan Contract Anchors` 分两次提交。每个 `planner` 在自己的结果分支提交；主 agent 验证并合入后，再分别提交 plan 文档与合同回填。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| plan 审过了 | **移交**：`$mmw:mmw-implement`，一张 ticket 一个 `worker` 开始落地 |
| 审出了采信的 findings | **自己继续**：重派 `planner` 改 findings 点名的那份 plan 路径，改完回第 6 步复审 |
| 第 4 步某个 `planner` 交回 `needs-context` 或 `needs-repair` | **自己继续**：按它说的补上下文或修 spec，然后带上补齐的材料重派 |
| 第 5 步发现 `planner` 认领了别人归属的文件，或者提供方跟消费方对不上 | **自己继续**：重派 `planner` 修那一份，不要自己动它的 plan |
| 前置三项有一项不满足 | **停**：说清是哪一项。缺 ticket 的回 `$mmw:mmw-to-tickets`，缺 spec 的回 `$mmw:mmw-to-spec` |
| `planner` 交回 `needs-redirection` | **停**：把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去 |
| `planner` 交回 `blocked`，或者同一份 plan 返修三轮还没过 | **停**：报是哪一份、卡在哪里、三轮各自改了什么，让用户定 |
