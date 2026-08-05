# 领域上下文文档的格式

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

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则，并运行 `mmw domain path`。返回 `single` 时，按上面的结构维护命令返回的领域文档。返回 `map` 时，先读 Map，再读本次涉及的全部命名 leaf。

多上下文 Map 的 `Contexts` 使用固定三列表格。`Relationships` 使用非空的自然语言列表。每个 leaf 位于 `mmw domain dirs` 返回的 `context` 路径或其子目录中，并使用 `.md` 扩展名。例子里的 `docs/context/` 只展示形状：

```md
# Context Map

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| Ordering | [Ordering](./docs/context/ordering.md) | 受理并跟踪客户订单，定义 Customer。 |
| Billing | [Billing](./docs/context/billing/billing-language.md) | 生成发票并处理付款。 |
| Fulfillment | [Fulfillment](./docs/context/fulfillment.md) | 管理仓库拣货和发货。 |

## Relationships

- Ordering 发出 `OrderPlaced` 事件。Fulfillment 消费该事件并开始拣货。
- Fulfillment 发出 `ShipmentDispatched` 事件。Billing 消费该事件并生成发票。
- Ordering 定义 Customer。Billing 使用权威引用指向 Ordering 的定义。
```

`mmw domain sync` 拥有 `<!-- MMW-CONTEXT-MAP-RULES-START -->` 与 `<!-- MMW-CONTEXT-MAP-RULES-END -->` 之间的完整正文。本格式不复制受管规则。项目只维护 `Contexts` 和 `Relationships`。

三列表格遵守以下合同：

- `Context` 是非空且唯一的上下文名称。
- `Leaf` 整格是一个 Markdown 链接。链接相对 Map 解析，目标必须位于 `context` 路径内，并以 `.md` 结尾。
- `Owns` 是非空的自然语言所有权说明。
- `Relationships` 至少包含一个 Markdown 列表项。关系使用自然语言，不另建端点或所有权机器语法。

## 权威引用

共享术语只在一个 leaf 中定义。例如，`billing/billing-language.md` 使用以下固定格式引用 `ordering.md` 的权威定义：

```md
**Customer**：
付款请求关联的下单方。(authoritative: [Customer](../ordering.md))
```

路径相对当前 leaf 解析。引用目标必须是同一 Map 的 `Contexts` 已登记 leaf。
