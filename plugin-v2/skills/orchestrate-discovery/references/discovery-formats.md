# CONTEXT.md + ADR 格式

> **参考文档**：`orchestrate-discovery` 全程可查阅 · CONTEXT.md + ADR 格式参考 · 非流程步骤

## CONTEXT.md 格式

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
- **只包含项目特有术语**。通用编程概念不属于 CONTEXT.md
- **Example dialogue**：展示术语在对话中如何自然交互

**单 context vs 多 context**：
- `CONTEXT-MAP.md` 存在 → 读取找到各 context
- 只有根 `CONTEXT.md` → 单 context
- 都不存在 → 第一个术语被确认时懒创建

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
