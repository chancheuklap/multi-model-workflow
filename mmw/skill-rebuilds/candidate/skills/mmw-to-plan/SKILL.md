---
name: mmw-to-plan
description: 为已发布 spec 的每张 tracer bullet ticket 编排一份 plan。spec 和 tickets 已发布、下一步要写 plan 时使用。
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

`<spec issue 编号>` 由调用方移交时给你。上下文断了、手上只有 slug 时，按 `/mmw-start` 的「回来接着做」那张表反查它。

## 1. 定 plan 清单

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| spec | 始终 | 问题、方案、实现决定、合同边界和测试 seam | 其他 spec | spec 路径 |
| ticket | 始终 | 目标、验收、阻塞关系和 plan 路径 | 其他 ticket | ticket 编号和 plan 路径 |
| prototype | ticket 引用时 | 索引、选中产物、明确相关的走查或长期证据 | 整个产物目录、无关过程材料 | 精确路径；没有写「无 prototype 资产」 |
| research | ticket 引用时 | research 索引和当前 ticket 使用的精确文件 | research 的上级目录、subagent 原始报告 | 精确路径；没有写「无 research」 |

prototype 索引字段不完整时回 `/mmw-prototype` 补齐。

- `## Problem Statement`
- `## Solution`
- `## Implementation Decisions`
- `## Contract Boundaries`
- `## Testing Decisions` 中的 seam 清单表

**只读，作为派发时给 `planner` 的上下文**，不在这里展开写作。

取全部 ticket，读出各自要做什么和被谁阻塞，定下 plan 清单：**一张 ticket 一份 plan 一个 `planner`**。

落点就是每张 ticket 正文 `## Plan` 一节写着的路径：`docs/plans/<slug>/<两位编号>-<ticket-slug>.md`。编号照抄，不自己重排。ticket 正文没有这一节时，按依赖顺序自己编号，被阻塞的排在阻塞它的后面。

**轻量验证现状**：用检索确认 spec 涉及的落点目录和关键路径真实存在，够你判断派几个 `planner`、各管哪张 ticket 就行。深度探代码由 `planner` 各自做，你不抢着探全。

术语或验收标准不清楚，回 `/mmw-to-spec` 改；架构假设跟代码现实对不上，先弄清楚再派。

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
| 目标 | 为 ticket `#<编号>` 写 plan，写进 `docs/plans/<slug>/<NN>-<ticket-slug>.md`——这条路径从 ticket 正文的 `## Plan` 一节原样抄过来，**把完整路径写进这一栏**，`planner` 只认 task 里给的这一个落点 |
| 读 | 按「1. 定 plan 清单」逐行列出当前 ticket 的精确路径。方法论不用列——`planner` 自带 `/mmw-planner` |
| 约束 | 只写该 plan 文件；不提交；不认领 `## Cross-Plan Contract Anchors` 划给别人的文件；不写其他 plan 的正文 |
| 验收 | plan 文件存在且可被抽验；`## Acceptance` 覆盖 ticket `#<编号>` 的全部验收（详见 issue，不抄正文） |

派一个 `planner`，它在**当前任务 worktree** 里写 plan 文件，不另开分支。手上有名为 `mmw-planner` 的原生 subagent，就按名字调它，task 传四栏表全文，工作目录设成当前任务 worktree 的绝对路径；没有的话，把四栏表写进 `.dispatch/planner-<ticket 编号>.md`，后台跑 `mmw dispatch planner --task <这个文件的绝对路径> --cwd <当前任务 worktree 绝对路径>`。它的输出第一行是 `mode:`：`executed` 表示它已经自己跑完了，按 `report:` 那行的路径读报告；`host-tool` 表示要你来调，`tool:` 那行是宿主工具名，`params:` 那几行是 JSON 参数，原样传给它。

互不依赖的实例在同一条消息里一起启动。

互不依赖的 plan：同一条消息里并行启动多个 `planner`。有依赖链：按依赖顺序启动。`planner` 使用当前任务 worktree，不建独立 worktree，不提交。每个 `planner` 只写自己的 plan 文件。

## 4. 验证返回

每个 `planner` 交回 `pass` 之后，验证 plan 文件存在，ticket 的每条验收都能映射到 `## Acceptance`，再抽验至少一条源码依据。读取文件并检索源码，不认「我写完了」。

失实就把原 task 加上修复说明重派一次。交回 `needs-context` 或 `needs-repair` 的，按它说的补路径或修 spec 之后重派。

## 5. 回填精确字段，验证边界

把第 2 步标着「字段待回填」的格子补成真实的归属方、提供方、消费方和字段，写回 `## Cross-Plan Contract Anchors`。入口是每份 plan 的 `## Change Map`、`## Contracts and Seams`，以及 `planner` 报告里的 `Cross-plan touchpoints`。

- 每份 plan 的文件与职责表。
- 合同锚点、迁移与登记。
- `planner` 报告里的 `Cross-plan touchpoints`。

回填后验证两件事：

- 有没有 `planner` 认领了别人归属的文件。
- 提供方声明的接口跟消费方期望的对不对得上。

对不上就重派一个 `planner` 修那一份。

## 6. 发起 ② plan 审

**全部 plan 都验证过、合同也回填完之后，发起一次审查，不逐份发起。** 按 `/mmw-review` 走，传给它：plan 目录 `docs/plans/<slug>/` 的路径、这份 spec 的精确路径、全部 ticket 的编号，以及这批 plan 实际引用到的 prototype `README.md`、选中产物、research `README.md` 和精确文件；某一项没有就写「无」。

## 7. 提交

plan 文档和 spec 的 `## Cross-Plan Contract Anchors` 分两次提交。`planner` 不提交，改动一直是未暂存的，由你统一收。

## 8. 标记 ticket 就绪

全部 plan 通过 ② plan 审，而且第 7 步完成后，给每张 open tracer bullet ticket 幂等添加 `ready-for-agent`：

```bash
gh issue edit <ticket 编号> --add-label ready-for-agent
```

添加完成后，运行 `mmw issue children <spec issue 编号>` 重新读取全部子 issue。每张 open tracer bullet ticket 都带 `ready-for-agent`，第 8 步才完成。仍有缺失时继续留在第 8 步；重复运行添加命令会收敛到相同状态。

`ready-for-agent` 表示 ticket 的 plan 已经通过 ② plan 审。`Blocked by` 和 `mmw issue frontier` 继续决定哪张 ticket 已经无阻塞并且可以认领；只有进入 frontier 的 ticket 才能派 `worker`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 全部 plan 过审、提交，且全部 open tracer bullet ticket 都带 `ready-for-agent` | **移交**：`/mmw-implement`，从 `mmw issue frontier` 返回的 ticket 开始落地 |
| 审出了采信的 findings | **自己继续**：把全部采信项一次性重派给对应 `planner`；主 agent 逐条验证修复后直接进入第 7 步提交，不再审 |
| 第 4 步某个 `planner` 交回 `needs-context` 或 `needs-repair` | **自己继续**：按它说的补上下文或修 spec，然后带上补齐的材料重派 |
| 第 5 步发现 `planner` 认领了别人归属的文件，或者提供方跟消费方对不上 | **自己继续**：重派 `planner` 修那一份，不要自己动它的 plan |
| 前置三项有一项不满足 | **停**：说清是哪一项。缺 ticket 的回 `/mmw-to-tickets`，缺 spec 的回 `/mmw-to-spec` |
| `planner` 交回 `needs-redirection` | **停**：把它说的哪里可疑、建议怎么重新框定原样交给用户，不要自己改 spec 绕过去 |
| 同一份 plan 返修三轮还没过 | **停**：报是哪一份、卡在哪里、三轮各自改了什么，让用户定 |
