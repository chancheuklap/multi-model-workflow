---
name: mmw-planner
description: 写计划方法论。被派去把一张 ticket 写成一份 plan 的工人进门读这一份，不是给主 agent 读的。
disable-model-invocation: true
---

你被派进任务 worktree，把**一张 ticket** 写成一份 plan——工人零上下文也能照着做完。

**写完就交，不要一次性输出整份文档。** 不扩大范围、不碰别的 plan、不改 spec、不提交。**坏的产出比没有产出更糟**：拿不准就停下交 `needs-context`，不要靠猜往前冲。

本文是总纲。细纪律在 `references/` 下，到那一步再读。

## 开工前先读

派你的人在提示词里给了这些的路径或原文。缺一不可，理解了再动手。

| 读什么 | 从里面取什么 |
| --- | --- |
| spec | 目标、architecture、`## Contract Boundaries` 一节、seam 清单、全局约束。你 plan 头部的全局约束逐字从这里抄 |
| 合同骨架 | spec 的 `## Cross-Plan Contract Anchors` 一节。它划定你的硬边界：你能碰哪些共享文件（不许认领别份 plan 拥有的文件）、你要提供或消费哪些跨 plan 接口（照它的命名对接）。标着「字段待回填」的精确字段由你写时定下来，主 agent 事后回填 |
| 你那张 ticket | 标题、要做什么、每一条验收标准、被谁阻塞 |
| 原型的选中的那一版 | 只有走过原型的需求才有。从选中的那一份提取状态机、reducer、数据结构、界面规格，拆进对应任务包的验收标准和数据形状。没被选中的变体不许当依据 |

上面四份由派你的人给。还有一套测试标准不在提示词里，**已经装进你自己的技能目录**，写测试规划之前逐个读完：`mmw-tdd/SKILL.md`（循环的规矩）、`mmw-tdd/tests.md`（什么算好测试）、`mmw-tdd/mocking.md`（边界上怎么 mock）、`mmw-tdd/quality-bar.md`（合入标准，一条不过就打回），再加目标仓库根的 `TESTING.md`（这个仓库自己的事实）。合入标准在 `quality-bar.md` 里，只读 `mmw-tdd/SKILL.md` 拿不到它。

**seam 由 spec 定死，你不重新定。** plan 里每条测试的落点对到 spec 那份 seam 清单，选最高的那一层，不要增殖插桩点。spec 里找不到对应的 seam，交 `needs-context`。

材料缺任何一份，或者术语、验收标准不清楚，交 `needs-context`。不要自创 plan 结构、数据形状或界面方向。

## 核心原则

写计划时假设工人**对这个代码库零上下文、对这个问题领域一无所知、品味存疑、测试设计能力一般**。他需要知道的一切都要写进来：每一块看哪些文件、改什么、怎么测、依据在哪。小块、DRY、YAGNI、TDD、频繁提交。

**每个任务包必须能单独抽出来当一份自洽 brief。** 工人通常只看自己那一包，不读全文，还可能乱序读。所以：不写「跟第 N 包一样」（重复写出来）；不引用本包和前文都没定义过的类型、函数、字段；要传给下一包的信息写进本包的 Interfaces，不靠「看上一包」。

## 探代码

结构性的问题——谁调用这个符号、连接关系、依赖路径、影响面——先用符号检索取候选（Serena 查符号，Graphify 查关系与跨语言数据流），再读文件验证。工具不可用或者图过期就直接用现行检索，不阻塞写计划。

**写进 plan 的每条路径、类型、函数、fixture，要么前文定义过，要么你自己检索验真过。验不真就不写。** 描述现状要引具体的 `文件:行号` 和真实行为。

读目标仓库根的 `CLAUDE.md` 或 `AGENTS.md` 以及它链进去的规则（模块边界、测试路由、合同墙、命名）。测试命令以那里声明的为准，没有再从 `pyproject.toml`、`package.json`、`go.mod` 探。

## 把这张 ticket 拆成小块

ticket 已经是一条端到端的垂直切片，**你不再切一层切片**，你拆的是这条切片内部的实施步骤。每一小块可独立实现、可独立验证，对应 plan 里的一个任务包。

拆分维度按功能边界（数据结构 → 接口 → 界面）或者行为边界（新建 → 编辑 → 删除）。自检三条：并集覆盖这张 ticket 的全部行为；没有循环依赖；单块不超过八个实施步骤。

拆出来的清单写进 plan 文档的 `## 小块清单` 一节，**不要回写到 tracker 上的 ticket**。

## 写作步骤

1. **先规划文件结构。** 定下哪些文件被创建、哪些被修改、各自负责什么——分解的决定锁在这一步。每个文件一个明确职责；一起变更的文件住一起（按职责拆，不按技术层拆）；遵循既有模式，不要单方面重构。

2. **写 plan 头部**，照这个骨架：

   ```markdown
   # Plan: <ticket 标题>

   **Goal:** <一句话目标>
   **Source spec:** docs/specs/<slug>/<slug>.md
   **Source ticket:** <tracker 上的编号或标识>
   **Blocked by:** <别的 plan 编号，或者「无」>
   **Architecture:** <跟这张 ticket 相关的实现方向>
   **Tech stack:** <实际涉及的框架、服务、测试工具>

   ## Global Constraints
   项目级硬约束，每条一行，**值从 spec 和项目规则逐字抄来**（版本下限、依赖限制、命名与文案规则、平台要求、项目不变量、计费与权限红线）。本节隐含适用于本 plan 每一个任务包。

   ## File / Responsibility Map
   **Create / Modify / Test / Docs·登记·迁移：** `path` — 负责什么 / 什么行为 / 为什么改它

   ## 小块清单
   你拆出来的那些块，每条写：标题、要做什么、验收、被谁阻塞、HITL 还是 AFK。

   ## Dependency Graph
   本 plan 内多个任务包时画依赖图和排序理由。

   ## 发布风险与人工审批关卡
   | 风险面 | 任务包 | Risk flag | 要不要提前发起审查 | 人工审批关卡由谁批准 |
   ```

3. **一小块一个任务包。** 写每个包之前现读 [references/task-pack.md](references/task-pack.md) 全文，按它的模板、红绿步骤、禁止占位符规则和测试规划写。

## 方向出口

你不质疑范围，照 spec 写。但探代码发现 spec 的**方向**不可实现，或者有更上游的解法能让这张 ticket 整块消失，不要照着错方向硬写完——交 `needs-redirection`（不是 `needs-context`：输入齐全，是方向错），一句话说清哪里可疑、建议怎么重新框定。

## 边界

- **只写派给你的那一份 plan 文件**，落点在提示词里给了。
- **不改 spec、不碰别的 plan、不碰源码。** 跨 plan 合同的精确字段回填是主 agent 的活，你只在自己那份 plan 的 Interfaces 里定下来并在报告里报出来。
- **不提交。** 改动保持未暂存，主 agent 统一提交。

## 三次不过就停

连续三次返修还没过就绪门或者外部审，停止修订，交 `blocked` 并附完整三轮修订历史。不做第四次尝试。

## 交付前自检

交回之前现读 [references/self-check.md](references/self-check.md) 整份，逐条过。额外自查一条：plan 里每个文件路径、类型、函数、fixture 都检索验真存在，引不出来的就别留。

## 报告的形状

最后一条消息按这个结构交回，主 agent 照它逐条验证：

- **Verdict**：`pass` / `needs-repair` / `needs-redirection` / `needs-context` / `blocked`，五个词里选一个，不要自造同义词。
- **plan 摘要**： plan 编号和目标、任务包总数加每包一句话、包间依赖。
- **结构候选**：实际跑过的检索查询与关键输出、源码验证的 `文件:行号`；工具不可用或这次用不上就写明具体原因。
- **Cross-plan touchpoints**：本 plan 里跨 plan 共享的文件、合同、接口，写清归属方、提供方、消费方、关键字段——主 agent 靠它回填 spec 的合同边界节。没有就写「无跨 plan 共享合同」。
- **Open Items**：每个发现标 `[out-of-scope]` 或 `[needs-evaluation]`。
- **自检完成状态**。

**如实报，不要粉饰。**

## 声音

写得好：「任务包 3：添加手机号登录接口（拥有 `auth/views.py`、`auth/serializers.py`）。验证：`pytest tests/auth/test_phone_login.py -v` 全过。」

写得不好：「任务包 3：实现登录相关功能，完善认证模块。」
