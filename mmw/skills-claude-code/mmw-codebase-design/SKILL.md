---
name: mmw-codebase-design
description: deep module 的共同词汇与判据：module、interface、seam、adapter、depth。用户要设计一个 module 的 interface、要定 seam 放哪时用它；别的技能需要这套词汇时也用它。
---

# Codebase Design

设计 **deep module**：大量行为藏在一个小 interface 后面，放在一条干净的 seam 上，隔着这个 interface 就能测。凡是在设计或重构代码的地方都用这套语言和这些原则。目标是给调用方 leverage、给维护者 locality、给所有人可测性。

## 词汇表

这些词原样使用。不要换成「组件」「服务」「API」或「边界」。

| 术语 | 定义 | 不使用 |
| --- | --- | --- |
| **module** | 任何有 interface 和 implementation 的东西。规模不限：函数、类、包或跨层切片都算 | 单元、组件、服务 |
| **interface** | 调用方正确使用 module 必须知道的全部：类型签名、不变量、顺序约束、错误模式、必需配置和性能特征 | API、签名；两者只覆盖类型层面 |
| **implementation** | module 内部的代码。谈 seam 时使用 adapter，其余时候使用 implementation | 不能与 adapter 互换；两者描述不同维度 |
| **depth** | interface 上的 leverage。大量行为位于小 interface 后面是 **deep**；interface 几乎与 implementation 一样复杂是 **shallow** | implementation 的行数 |
| **seam** | Michael Feathers 所说的可替换行为位置，也就是 module 的 interface 所在位置。seam 的位置与其后内容是两个设计决定 | 边界；该词与 DDD 的 bounded context 重名 |
| **adapter** | 在 seam 上满足某个 interface 的具体东西。它描述角色，不描述内部实质 | 不能与 implementation 互换 |
| **leverage** | 调用方从 depth 获得的能力：每学习一个单位的 interface，可以驱动更多行为；一份 implementation 在多个调用点和测试上复用 | — |
| **locality** | 维护者从 depth 获得的集中性：改动、缺陷、知识和验证位于一处；修一次即可覆盖全部调用方 | — |

implementation 与 adapter 可以任意组合。例如，Postgres 仓储可以是小 adapter 加大 implementation；内存假实现可以是大 adapter 加小 implementation。

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
