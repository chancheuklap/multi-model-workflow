---
name: mmw-codebase-design
description: deep module 的设计判据。用于设计或比较 module interface、选择 seam 或 adapter，或评估 module depth。
---

# Codebase Design

设计 **deep module**：大量行为藏在一个小 interface 后面，放在一条干净的 seam 上，隔着这个 interface 就能测。凡是在设计或重构代码的地方都用这套语言和这些原则。目标是给调用方 leverage、给维护者 locality、给所有人可测性。

## 词汇表

这些词原样用——不要换成「组件」「服务」「API」「边界」。用词一致本身就是全部意义所在。

**module** —— 任何有 interface 和 implementation 的东西。刻意不限规模：一个函数、一个类、一个包、一片跨层的切片都算。*不要用*：单元、组件、服务。

**interface** —— 调用方要正确使用这个 module 必须知道的全部：类型签名，还有不变量、顺序约束、错误模式、必需的配置、性能特征。*不要用*：API、签名（太窄——它们只指类型层面那一面）。

**implementation** —— module 内部的东西，它的代码本体。跟 **adapter** 是两回事：一个东西可以是小 adapter 配大 implementation（一个 Postgres 仓储），也可以是大 adapter 配小 implementation（一个内存假实现）。谈 seam 的时候用 adapter，其余时候用 implementation。

**depth** —— interface 上的 leverage：调用方（或测试）每学一个单位的 interface，能驱动多少行为。大量行为坐在一个小 interface 后面就是 **deep**，interface 复杂得几乎跟 implementation 一样就是 **shallow**。

**seam**（Michael Feathers 的说法）—— 能在别处改变行为而不用改动这个地方的位置；也就是一个 module 的 interface 所在的*位置*。seam 放哪是一个独立的设计决定，跟 seam 后面装什么是两件事。*不要用*：边界（跟 DDD 的 bounded context 重名）。

**adapter** —— 在一条 seam 上满足某个 interface 的具体东西。它描述的是*角色*（填哪个槽），不是实质（里面装什么）。

**leverage** —— 调用方从 depth 里拿到的东西：每学一个单位的 interface 换来更多能力。一份 implementation 在 N 个调用点和 M 个测试上回本。

**locality** —— 维护者从 depth 里拿到的东西：改动、缺陷、知识和验证都集中在一处，不散到各个调用方。修一次，处处修好。

## deep 与 shallow

**deep module** = 小 interface + 大量 implementation：

```
┌─────────────────────┐
│   小 interface      │  ← 方法少，参数简单
├─────────────────────┤
│                     │
│  深的 implementation│  ← 复杂逻辑藏在里面
│                     │
└─────────────────────┘
```

**shallow module** = 大 interface + 少量 implementation（要避免）：

```
┌─────────────────────────────────┐
│       大 interface              │  ← 方法多，参数复杂
├─────────────────────────────────┤
│  薄 implementation              │  ← 只是转手
└─────────────────────────────────┘
```

设计一个 interface 时问自己：

- 方法数还能不能再少？
- 参数还能不能再简单？
- 还能不能把更多复杂度藏进去？

## 原则

- **depth 是 interface 的属性，不是 implementation 的属性。** 一个 deep module 内部完全可以由小的、可 mock 的、可替换的零件组成——它们只是不属于 interface。一个 module 可以有**内部 seam**（私有的，只给它自己的测试用），也有 interface 上那条**外部 seam**。
- **deletion test。** 设想把这个 module 删掉。复杂度跟着消失，它就是个转手的。复杂度在 N 个调用方身上重新冒出来，它就在挣自己的饭钱。
- **interface 就是测试面。** 调用方和测试跨的是同一条 seam。你想测到 interface *后面*去，多半是这个 module 形状不对。
- **一个 adapter 是假 seam，两个才是真 seam。** 没有东西真的在这条线两侧变化，就不要开这条 seam。

## 为可测性设计

好 interface 让测试变自然：

1. **接收依赖，不要自己造依赖。**

   ```typescript
   // 好测
   function processOrder(order, paymentGateway) {}

   // 难测
   function processOrder(order) {
     const gateway = new StripeGateway();
   }
   ```

2. **返回结果，不要产生副作用。**

   ```typescript
   // 好测
   function calculateDiscount(cart): Discount {}

   // 难测
   function applyDiscount(cart): void {
     cart.total -= discount;
   }
   ```

3. **表面积要小。** 方法越少，要写的测试越少；参数越少，测试的准备工作越简单。

## 这几个词之间的关系

- 一个 **module** 恰好有一个 **interface**（它呈现给调用方和测试的那一面）。
- **depth** 是 **module** 的属性，量它的尺子是它的 **interface**。
- **seam** 是一个 **module** 的 **interface** 所在的位置。
- **adapter** 坐在 **seam** 上，满足那个 **interface**。
- **depth** 给调用方产出 **leverage**，给维护者产出 **locality**。

## 被否掉的几种说法

- **把 depth 说成 implementation 行数与 interface 行数之比**（Ousterhout）：这会奖励往 implementation 里灌水。我们用 depth 即 leverage。
- **把 interface 说成 TypeScript 的 `interface` 关键字，或者一个类的公开方法**：太窄——这里的 interface 包含调用方必须知道的每一条事实。
- **「边界」**：跟 DDD 的 bounded context 重名。说 **seam** 或者 **interface**。

## 再往下

- **给定依赖情况，怎么 deepen 一簇 module** —— 见 [DEEPENING.md](DEEPENING.md)：依赖分类、seam 纪律、以替换代替叠加的测试策略。
- **探索几种不同的 interface** —— 见 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)：并行派 subagent 把这个 interface 设计成几种截然不同的样子，再按 depth、locality 和 seam 位置比较。
