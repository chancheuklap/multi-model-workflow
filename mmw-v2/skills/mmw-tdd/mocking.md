# 什么时候可以 mock

**只在系统边界上 mock**：

- 外部 API（支付、邮件之类）
- 数据库（有时候；能用测试库就用测试库）
- 时间与随机数
- 文件系统（有时候）

这些不许 mock：

- 你自己的类和模块
- 内部协作者
- 任何由你掌控的东西

**这条边界画在哪，最终由目标仓库的 `TESTING.md` 说了算**：哪些依赖算外部供应商、哪些算自家，只有那个仓库自己知道。它没写就按本节「可以 mock」和「不许 mock」两组判断。

## 让边界好 mock

在系统边界上，把接口设计成容易 mock 的样子。

**一、用依赖注入**

外部依赖从外面传进来，不要在函数内部造：

```typescript
// 好 mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// 难 mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**二、宁可写成 SDK 那样的接口，也不要一个通用 fetcher**

每一个外部操作各写一个具体函数，不要一个通用函数内部再分支：

```typescript
// 好：每个函数各自都能独立 mock
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// 坏：mock 里面还得写分支逻辑
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

写成 SDK 那样有四处好处：

- 每个 mock 只返回一种确定的形状
- 测试的准备代码里没有分支
- 一眼看得出这个测试碰了哪几个端点
- 每个端点各有各的类型
