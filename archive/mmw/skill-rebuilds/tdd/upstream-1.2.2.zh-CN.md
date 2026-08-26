# `tdd` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md:1-4 -->

```yaml
---
name: tdd
description: 测试驱动开发。用户想以测试优先方式构建功能或修复 bug、提到“red-green-refactor”，或者想要集成测试时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md:6-16 -->

# 测试驱动开发

TDD 是 red → green 循环。本技能是一份参考内容，使该循环产出值得保留的测试：它说明什么是良好测试、测试写在哪里、有哪些反模式，以及循环规则。每个章节都适用于每次循环；在循环开始前和进行中查阅，不要等结束后再看。

探索代码库时，读取 `CONTEXT.md`（如果存在），使测试名称和 interface 词汇符合项目领域语言；同时遵守本次涉及区域内的 ADR。

## 什么是良好测试

测试通过公开 interface 验证行为，不验证 implementation 细节。代码可以完全改变；测试不应改变。良好测试读起来像 spec，例如“用户可以使用有效购物车结账”会准确说明存在什么能力；由于测试不关心内部结构，它能够承受重构。

例子参见 [tests.md](tests.md)，mock 指引参见 [mocking.md](mocking.md)。

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md:18-26 -->

## Seam——测试写在哪里

**Seam** 是执行测试的公开边界：你在该 interface 上观察行为，不伸入内部。测试位于 seam 上，绝不针对内部实现。

**只在预先商定的 seam 上测试。** 编写任何测试前，写下要测试的 seam，并与用户确认。不要在未经确认的 seam 上编写测试。你不可能测试一切；预先商定 seam，能使测试精力落在关键路径和复杂逻辑上，不会落在每个边界情况上。

询问：“公开 interface 是什么？我们应该测试哪些 seam？”

如果该 interface 的形态本身仍然存在问题，例如 module 应该有多 deep、seam 应该位于哪里、interface 应该暴露什么，就使用 `/codebase-design` 技能取得词汇。它是 module、interface、depth、seam、adapter、leverage 和 locality 词汇的共享来源；它是一份需要查阅的参考内容，不是一次需要运行的 session。

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/SKILL.md:28-38 -->

## 反模式

- **与 implementation 耦合**——mock 内部协作者、测试私有方法，或通过旁路验证，例如不使用 interface，而是查询数据库。识别信号是：重构后行为没有改变，测试却损坏。
- **同义反复**——断言使用与代码相同的方式重新计算期望值，例如 `expect(add(a, b)).toBe(a + b)`、以相同方式手工推导的快照，或者断言一个常量等于自身；因此测试按照构造方式必然通过，永远无法与代码产生分歧。期望值必须来自独立的唯一事实来源，例如已知正确的字面值、完整推导过的例子或 spec。
- **横向切片**——先编写所有测试，再编写所有 implementation。批量测试验证的是**想象出来的**行为：你测试事物的**形状**，不测试面向用户的行为；测试会对真实变化变得不敏感；你还会在理解 implementation 前就承诺测试结构。改用**垂直切片**：一个测试 → 一份 implementation → 重复；每个测试都是一枚 **tracer bullet**，会响应上一轮学到的内容。

## 循环规则

- **先 red，后 green。** 先编写失败测试，然后只编写足以让它通过的代码。不要预判未来测试，也不要加入推测性功能。
- **每次一个切片。** 每轮一个 seam、一个测试、一份最小 implementation。
- **重构不属于循环。** 它属于审查阶段，参见 `code-review` 技能；不属于 red → green implementation 循环。

## `mocking.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/mocking.md:1-18 -->

# 何时使用 Mock

只在**系统边界**使用 mock：

- 外部 API，例如支付、电子邮件等
- 数据库，有时使用；优先使用测试数据库
- 时间或随机性
- 文件系统，有时使用

不要 mock：

- 自己的类或 module
- 内部协作者
- 你能够控制的任何内容

## 为可 Mock 性而设计

在系统边界上，设计容易 mock 的 interface：

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/mocking.md:20-35 -->

**1. 使用依赖注入**

把外部依赖传入，不要在内部创建：

```typescript
// 容易 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难以 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/mocking.md:37-59 -->

**2. 优先使用 SDK 风格的 interface，不要使用通用 fetcher**

为每项外部操作创建具体函数，不要使用一个带条件逻辑的通用函数：

```typescript
// 好：每个函数都能独立 mock
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// 差：mock 时需要在 mock 内部使用条件逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

SDK 方式意味着：
- 每个 mock 返回一种具体形状
- 测试设置中没有条件逻辑
- 更容易看出一项测试执行了哪些端点
- 每个端点都有类型安全

## `tests.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/tests.md:1-23 -->

# 良好测试与不良测试

## 良好测试

**集成风格**：通过真实 interface 测试，不 mock 内部部分。

```typescript
// 好：测试可观察行为
test("用户可以使用有效购物车结账", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

特征：

- 测试用户或调用方关心的行为
- 只使用公开 API
- 能够承受内部重构
- 描述**做什么**，不描述**如何做**
- 每项测试只有一项逻辑断言

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/tests.md:25-45 -->

## 不良测试

**Implementation 细节测试**：与内部结构耦合。

```typescript
// 差：测试 implementation 细节
test("checkout 调用 paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

危险信号：

- mock 内部协作者
- 测试私有方法
- 断言调用次数或顺序
- 重构没有改变行为，测试却损坏
- 测试名称描述**如何做**，不描述**做什么**
- 不通过 interface，而通过外部手段验证

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/tests.md:47-61 -->

```typescript
// 差：绕过 interface 进行验证
test("createUser 把用户保存到数据库", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// 好：通过 interface 验证
test("createUser 使用户可以被取得", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/tests.md:63-77 -->

**同义反复测试**：期望值重新陈述 implementation，因此测试按照构造方式必然通过。

```typescript
// 差：使用与代码相同的方式重新计算期望值
test("calculateTotal 对各明细项求和", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// 好：期望值是独立的已知字面值
test("calculateTotal 对各明细项求和", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/tdd/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "TDD"
  short_description: "测试驱动的 red-green-refactor"
```
