# `codebase-design` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:1-4 -->

```yaml
---
name: codebase-design
description: 设计 deep module 的共享词汇。用户想要设计或改进 module 的 interface、寻找 deepening opportunity、决定 seam 的位置、提高代码的可测试性或 AI 可导航性，或者其他技能需要 deep module 词汇时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:6-12 -->

# Codebase Design

设计 **deep module**：把大量行为放在一个小型 interface 后面，将它放在干净的 seam 上，并能通过该 interface 测试。只要正在设计或重构代码，就使用这套语言和这些原则。目标是让调用方获得 leverage，让维护者获得 locality，并让所有人都获得可测试性。

## 术语表

必须准确使用这些术语，不要替换成 `component`、`service`、`API` 或 `boundary`。重点就在于语言一致。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:14-28 -->

**Module**——任何具有 interface 和 implementation 的内容。有意不限定规模：它可以是 function、class、package，也可以是跨 tier 的切片。_避免使用_：unit、component、service。

**Interface**——调用方为了正确使用 module 而必须知道的一切：包括 type signature，也包括 invariant、顺序约束、错误模式、必需配置和性能特征。_避免使用_：API、signature。后两者过于狭窄，只指 type 层面的表面。

**Implementation**——module 内部的内容，也就是它的代码主体。它不同于 **Adapter**：一个对象可以是小型 adapter，却有大型 implementation，例如 Postgres repo；也可以是大型 adapter，却有小型 implementation，例如 in-memory fake。讨论 seam 时使用 `adapter`，其他时候使用 `implementation`。

**Depth**——interface 上的 leverage：调用方或测试每学习一个单位的 interface，能够使用多少行为。当大量行为位于小型 interface 后面时，module 是 **deep** 的；当 interface 几乎与 implementation 一样复杂时，module 是 **shallow** 的。

**Seam**（Michael Feathers）——无需在某个位置编辑，就能改变行为的位置；也就是 module interface 所处的**位置**。seam 放在哪里本身就是一项设计决定，不同于 seam 后面放什么。_避免使用_：boundary，因为它与 DDD 的 bounded context 含义重叠。

**Adapter**——在一个 seam 上满足某个 interface 的具体对象。它描述的是**角色**，也就是填补哪个位置，不是实质，也就是内部有什么。

**Leverage**——调用方从 depth 中得到的价值：每学习一个单位的 interface，就能获得更多能力。一份 implementation 能够在 N 个调用位置和 M 个测试中重复产生回报。

**Locality**——维护者从 depth 中得到的价值：改动、bug、知识和验证集中在一个位置，不会散布到各个调用方。修复一次，处处修复。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:30-58 -->

## Deep 与 shallow

**Deep module** = 小型 interface + 大量 implementation：

```
┌─────────────────────┐
│   Small Interface   │  ← 方法少，参数简单
├─────────────────────┤
│                     │
│  Deep Implementation│  ← 隐藏复杂逻辑
│                     │
└─────────────────────┘
```

**Shallow module** = 大型 interface + 少量 implementation，应避免：

```
┌─────────────────────────────────┐
│       Large Interface           │  ← 方法多，参数复杂
├─────────────────────────────────┤
│  Thin Implementation            │  ← 只做透传
└─────────────────────────────────┘
```

设计 interface 时，询问：

- 能否减少方法数量？
- 能否简化参数？
- 能否把更多复杂性隐藏在内部？

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:60-65 -->

## 原则

- **Depth 是 interface 的属性，不是 implementation 的属性。** deep module 的内部可以由小型、可 mock、可替换的部分组成；这些部分只是不属于 interface。module 可以有 **internal seam**，由自己的测试使用，并且只在 implementation 内部可见；也可以在 interface 上有 **external seam**。
- **删除检验。** 想象删除这个 module。如果复杂性消失了，它原本只是透传。如果复杂性重新出现在 N 个调用方中，它原本发挥了应有价值。
- **Interface 就是测试表面。** 调用方和测试穿过同一个 seam。如果你想越过 interface 进行测试，这个 module 的形状可能有误。
- **一个 adapter 意味着假设性的 seam；两个 adapter 意味着真实 seam。** 除非确实有内容会跨越 seam 发生变化，否则不要引入 seam。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:67-95 -->

## 为可测试性而设计

良好的 interface 会让测试变得自然：

1. **接收依赖，不要创建依赖。**

   ```typescript
   // 可测试
   function processOrder(order, paymentGateway) {}

   // 难以测试
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **返回结果，不要产生副作用。**

   ```typescript
   // 可测试
   function calculateDiscount(cart): Discount {}

   // 难以测试
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **较小的表面积。** 方法越少，需要的测试越少。参数越少，测试设置越简单。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/SKILL.md:97-114 -->

## 关系

- 一个 **Module** 恰好有一个 **Interface**，也就是它向调用方和测试呈现的表面。
- **Depth** 是 **Module** 的属性，并相对于它的 **Interface** 衡量。
- **Seam** 是 **Module** 的 **Interface** 所处的位置。
- **Adapter** 位于 **Seam** 上，并满足 **Interface**。
- **Depth** 为调用方产生 **Leverage**，并为维护者产生 **Locality**。

## 不采用的表述

- 把 **Depth 表述为 implementation 行数与 interface 行数之比**（Ousterhout）：这会奖励填充 implementation。我们改用“depth 即 leverage”的表述。
- 把 **Interface** 表述为 TypeScript 的 `interface` 关键字或 class 的 public method：过于狭窄；这里的 interface 包含调用方必须知道的每一项事实。
- **Boundary**：与 DDD 的 bounded context 含义重叠。使用 **seam** 或 **interface**。

## 深入阅读

- **根据依赖对一组 module 执行 deepening**——参见 [DEEPENING.md](DEEPENING.md)：依赖分类、seam 纪律，以及“替换而非叠加”的测试方法。
- **探索备选 interface**——参见 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)：并行启动 subagent，以若干种截然不同的方式设计 interface，随后比较 depth、locality 和 seam 位置。

## `DEEPENING.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DEEPENING.md:1-7 -->

# Deepening

说明如何根据依赖对一组 shallow module 安全地执行 deepening。本文假定读者使用 [SKILL.md](SKILL.md) 中的词汇：**module**、**interface**、**seam**、**adapter**。

## 依赖分类

评估一个 deepening 候选项时，对它的依赖进行分类。分类决定如何跨越 seam 测试 deepening 后的 module。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DEEPENING.md:9-25 -->

### 1. 进程内

纯计算、in-memory 状态、没有 I/O。始终可以执行 deepening：合并这些 module，并直接通过新的 interface 测试。不需要 adapter。

### 2. 可在本地替代

具有本地测试替代物的依赖，例如用 PGLite 代替 Postgres、使用 in-memory filesystem。存在替代物时可以执行 deepening。测试套件运行该替代物，并用它测试 deepening 后的 module。seam 位于内部；module 的 external interface 上没有 port。

### 3. 远程但自有（Ports & Adapters）

跨越 network boundary 的自有 service，例如 microservice 或 internal API。在 seam 上定义一个 **port**，也就是 interface。deep module 拥有逻辑；transport 以 **adapter** 形式注入。测试使用 in-memory adapter。production 使用 HTTP、gRPC 或 queue adapter。

建议采用以下形状：“在 seam 上定义 port，为 production 实现 HTTP adapter，并为测试实现 in-memory adapter。这样，即使逻辑跨网络部署，它仍然位于一个 deep module 中。”

### 4. 真正的外部依赖（Mock）

你无法控制的第三方 service，例如 Stripe 或 Twilio。deepening 后的 module 把外部依赖作为注入的 port；测试提供 mock adapter。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DEEPENING.md:27-37 -->

## Seam 纪律

- **一个 adapter 意味着假设性的 seam；两个 adapter 意味着真实 seam。** 除非至少有两个合理的 adapter，通常是 production 和 test，否则不要引入 port。只有一个 adapter 的 seam 只是一层间接调用。
- **Internal seam 与 external seam。** deep module 可以有 internal seam，由自身测试使用，并且只在 implementation 内部可见；也可以在 interface 上有 external seam。不要只因为测试使用 internal seam，就通过 interface 暴露它们。

## 测试策略：替换，不要叠加

- 一旦 deepening 后的 module interface 上已经存在测试，原先针对 shallow module 的 unit test 就变成了浪费；删除它们。
- 在 deepening 后的 module interface 上编写新测试。**Interface 就是测试表面。**
- 测试通过 interface 断言可观察结果，不要断言内部状态。
- 测试应当能承受内部 refactor：测试描述行为，不描述 implementation。如果 implementation 改变时测试也必须改变，说明测试越过了 interface。

## `DESIGN-IT-TWICE.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DESIGN-IT-TWICE.md:1-7 -->

# Design It Twice

用户想要为一个选定的 deepening 候选项探索备选 interface 时，使用这种并行 subagent 模式。它以 Ousterhout 的 `Design It Twice` 为基础：你的第一个想法不太可能是最好的想法。

使用 [SKILL.md](SKILL.md) 中的词汇：**module**、**interface**、**seam**、**adapter**、**leverage**。

## 流程

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DESIGN-IT-TWICE.md:9-17 -->

### 1. 界定问题空间

派出 subagent 前，为选中的候选项编写一份面向用户的问题空间说明：

- 任何新 interface 都需要满足的约束
- 它会依赖的对象，以及这些对象所属的分类，参见 [DEEPENING.md](DEEPENING.md)
- 一份粗略的说明性代码草图，用于让约束具有具体依据；它不是提案，只是让约束变得具体的方法

向用户展示这份说明，然后立即进入第 2 步。subagent 并行工作时，用户可以阅读和思考。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DESIGN-IT-TWICE.md:19-30 -->

### 2. 派出 subagent

使用 Agent 工具并行派出至少 3 个 subagent。每个 subagent 都必须为 deepening 后的 module 产出一个**截然不同**的 interface。

向每个 subagent 提供一份独立的技术 task，包括文件路径、耦合细节、[DEEPENING.md](DEEPENING.md) 中的依赖分类，以及 seam 后面的内容。这份 task 独立于第 1 步中面向用户的问题空间说明。为每个 agent 指定不同的设计约束：

- Agent 1：“让 interface 最小化，最多只提供 1 至 3 个入口。让每个入口的 leverage 最大化。”
- Agent 2：“让灵活性最大化，支持许多使用场景和扩展方式。”
- Agent 3：“为最常见的调用方进行优化，让默认情况变得简单。”
- Agent 4（如果适用）：“围绕 Ports & Adapters 设计跨 seam 依赖。”

在 task 中同时包含 [SKILL.md](SKILL.md) 词汇和 `CONTEXT.md` 词汇，使每个 subagent 的命名都同时符合架构语言和项目领域语言。

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DESIGN-IT-TWICE.md:32-38 -->

每个 subagent 输出：

1. Interface，包括 type、method、parameter，以及 invariant、顺序和错误模式
2. 展示调用方如何使用它的使用示例
3. implementation 在 seam 后面隐藏的内容
4. 依赖策略和 adapter，参见 [DEEPENING.md](DEEPENING.md)
5. 取舍：哪些位置 leverage 高，哪些位置较低

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/DESIGN-IT-TWICE.md:40-44 -->

### 3. 展示并比较

依次展示各项设计，使用户能够逐一理解；随后用文字比较它们。按照 **depth**，也就是 interface 上的 leverage；**locality**，也就是改动集中的位置；以及 **seam 位置**进行对比。

比较后，给出你自己的建议：说明你认为哪项设计最强，以及理由。如果不同设计中的元素适合组合，就提出混合方案。明确表达判断；用户需要的是有力的解读，不是一份选项菜单。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/codebase-design/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Codebase Design"
  short_description: "deep module 设计词汇"
```
