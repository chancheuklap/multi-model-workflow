# CONTEXT.md / CONTEXT-MAP.md + ADR 格式

> **使用场景**：起草 CONTEXT.md / CONTEXT-MAP.md / 子 context 文件 / ADR / scope.md 时按本文件 schema 输出 · **完成后回到**：调用方（discovery-discussion.md / discovery-design-document.md）

## CONTEXT.md / 子 context 格式

> 单一 `CONTEXT.md` 和 `CONTEXT-MAP.md` 引用的子 context 文件用同一套格式；`CONTEXT-MAP.md` 自身的索引格式见下方。

```markdown
# {Context Name}

{一两句话描述这个 context 是什么、为什么存在。}

## Language

**Order**:
{对术语的简洁定义}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account

## Relationships

- An **Order** produces one or more **Invoices**
- An **Invoice** belongs to exactly one **Customer**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — resolved: these are distinct concepts.
```

**规则**：
- **Be opinionated**：同一概念多个词时，选最好的一个，其余"避免使用"
- **Flag conflicts explicitly**：术语模糊使用时，在 Flagged ambiguities 明确解决
- **定义简短**：一句话。定义它**是什么**，不是它做什么
- **Show relationships**：粗体术语名，表达关系和基数
- **只包含项目特有术语**。通用编程概念不属于 context 文件
- **Example dialogue**：展示术语在对话中如何自然交互

**单 context vs 多 context**：
- `CONTEXT-MAP.md` 存在 → 按 map 索引读取/写入对应子 context 文件（每个子文件按上面同一格式书写）
- 只有根 `CONTEXT.md` → 单 context（直接读写根文件）
- 都不存在 → 第一个术语被确认时懒创建（默认创建 `CONTEXT.md`，当规模膨胀到难以维护时再拆为 `CONTEXT-MAP.md` + 子文件）

## CONTEXT-MAP.md 格式

`CONTEXT-MAP.md` 是大型仓库用的索引文件，本身不存术语定义，只指向各子 context 文件。

```markdown
# Context Map

{一段话说明本仓库为何拆分为多 context、各 context 的责任边界。}

## Contexts

- **Ordering**: [`docs/context/ordering.md`](docs/context/ordering.md) — 下单、购物车、订单状态机
- **Billing**: [`docs/context/billing.md`](docs/context/billing.md) — 发票、计费、结算
- **Fulfillment**: [`docs/context/fulfillment.md`](docs/context/fulfillment.md) — 履约、库存、物流

## Cross-context relationships

- **Ordering** 产生事件 → **Billing** 生成 Invoice
- **Fulfillment** 确认事件 → **Billing** 触发结算
- **Ordering** 与 **Fulfillment** 共享 `OrderId` 标识，但状态机互不依赖

## Shared vocabulary

- **OrderId** / **CustomerId** / **Money** —— 跨 context 通用标识与值对象，避免在各子 context 重复定义。
```

**规则**：
- **map 文件本身不写术语定义**，只写 context 列表、子文件路径、跨 context 关系
- **每个子 context 文件**按 "CONTEXT.md / 子 context 格式" 那一节书写
- **跨 context 关系**集中在 map，子文件不重复声明
- **共享词汇**（跨 context 通用的标识、值对象）可放在 map 顶层，子文件直接引用

## ADR 格式

放在 `docs/adr/`，顺序编号 `0001-slug.md`。目录懒创建。

```markdown
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

**什么时候建议 ADR**（三条件全部成立）：
1. **Hard to reverse** — 改变想法的代价不低
2. **Surprising without context** — 未来读者会疑惑"为什么"
3. **The result of a real trade-off** — 有真正的替代方案，选了一个有理由的

典型场景：架构形态 / 跨 context 集成 / 有 lock-in 的技术选型 / 边界和范围决策 / 对显而易见路径的刻意偏离 / 被拒绝的替代方案。

---
> **回到**：你之前正在执行的步骤继续。本文档是格式参考，不是流程步骤。
