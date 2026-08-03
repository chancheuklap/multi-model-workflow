# 好测试与坏测试

## 好测试

**走集成的写法**：通过真实接口测，不给内部零件打桩。

```typescript
// 好：测的是外部可观察的行为
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

它有这几个特征：

- 测的是用户或者调用方真正在乎的行为
- 只用公开接口
- 内部重构之后它还活着
- 讲的是「做到了什么」，不是「怎么做到的」
- 一个测试一条逻辑断言

## 坏测试

**跟实现细节绑死**：黏在内部结构上。

```typescript
// 坏：测的是实现细节
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

看到这几种就要警觉：

- 给内部协作者打桩
- 测私有方法
- 断言调用次数或者调用顺序
- 重构之后测试挂了，可行为根本没变
- 测试名讲的是「怎么做」而不是「做到了什么」
- 绕开接口，从别的通道去验证

```typescript
// 坏：绕开接口去验证
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// 好：通过接口验证
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**同义反复的测试**：预期值把实现又算了一遍，所以它按构造必然通过。

```typescript
// 坏：预期值是用代码那套算法重算出来的
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// 好：预期值是一个独立的、已知正确的字面量
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```

代码示例保持英文：它们是要粘进测试文件的形态，测试名本身也按项目自己的语言写。
