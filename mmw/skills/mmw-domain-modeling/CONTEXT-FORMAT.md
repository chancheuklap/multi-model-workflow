# CONTEXT.md 的格式

## 结构

```md
# {上下文名}

{一两句话说明这个上下文是什么、为什么存在。}

## Language

**Order**：
{一两句话说明这个术语}
_Avoid_: Purchase, transaction

**Invoice**：
交付之后发给客户的付款请求。
_Avoid_: Bill, payment request

**Customer**：
下单的个人或组织。
_Avoid_: Client, buyer, account
```

## 规则

- **要有立场。** 同一个概念有好几个说法时，挑最好的那个，其余的列进 `_Avoid_`。
- **定义要紧。** 最多一两句。定义它*是*什么，不是它*做*什么。
- **只收这个项目上下文特有的术语。** 通用编程概念（超时、错误类型、工具模式）不属于这里，哪怕项目里到处在用。加一个术语之前先问：这是这个上下文独有的概念，还是一个通用编程概念？只有前者才收。
- **自然聚成簇时用小标题分组。** 所有术语本来就属于一个内聚的领域，平铺一个列表就够。

## 单上下文与多上下文

**单上下文（多数仓库）：** 仓库根一份 `CONTEXT.md`。

**多上下文：** 仓库根一份 `CONTEXT-MAP.md`，列出有哪几个上下文、各自住在哪、彼此什么关系。**每个上下文的路径跑 `mmw domain dirs` 取 `context` 那一行**——例子里用 `docs/context/` 只是为了展示形状：

```md
# Context Map

## Contexts

- [Ordering](./docs/context/ordering/CONTEXT.md) —— 受理并跟踪客户订单
- [Billing](./docs/context/billing/CONTEXT.md) —— 生成发票、处理付款
- [Fulfillment](./docs/context/fulfillment/CONTEXT.md) —— 管理仓库拣货和发货

## Relationships

- **Ordering → Fulfillment**：Ordering 发出 `OrderPlaced` 事件，Fulfillment 消费它开始拣货
- **Fulfillment → Billing**：Fulfillment 发出 `ShipmentDispatched` 事件，Billing 消费它生成发票
- **Ordering ↔ Billing**：共用 `CustomerId` 和 `Money` 这两个类型
```

这个技能自己判断适用哪一种：

- 有 `CONTEXT-MAP.md`，读它找到各个上下文
- 只有一份根 `CONTEXT.md`，就是单上下文
- 两个都没有，等第一个术语定下来时按需建一份根 `CONTEXT.md`

有多个上下文时，判断当前话题属于哪一个。判断不了就问。
