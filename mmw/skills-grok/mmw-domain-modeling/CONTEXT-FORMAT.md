# 领域文档格式

## 结构

```md
# {bounded context 名称}

{用一两句话说明该 bounded context 是什么，以及它为何存在。}

## Language

**Order**：
{用一两句话描述该术语}
_Avoid_: Purchase, transaction

**Invoice**：
交付后发送给 customer 的付款请求。
_Avoid_: Bill, payment request

**Customer**：
下订单的人或组织。
_Avoid_: Client, buyer, account
```

## 规则

- **要有明确主张。** 同一个概念存在多个词时，选出最合适的一个，并把其他词列在 `_Avoid_` 下。
- **定义必须紧凑。** 最多一两句话。定义它**是什么**，不要定义它做什么。
- **只加入本项目 bounded context 特有的术语。** 通用编程概念，例如超时、错误类型、工具模式，即使项目大量使用也不应加入。增加术语前，先问：这是当前 bounded context 独有的概念，还是通用编程概念？只有当前 bounded context 独有的概念可以加入。
- 自然形成集群时，**用副标题组织术语**。如果所有术语都属于一个紧密统一的领域，扁平清单也可以。

## 单 bounded context 与多 bounded context 仓库

开始前按 [SKILL.md 的「文件结构」](SKILL.md#文件结构)判定形态。只有 `CONTEXT.md` 时，按本文件 `## 结构` 维护它。有 `CONTEXT-MAP.md` 时，先读 Map，再读本次涉及的全部 leaf。两个都没有时，完整读取那一节，在第一个需要长期保留的领域术语得到解决后，根据 bounded context 的数量创建 `CONTEXT.md`，或者创建 Context Map 和首个 leaf。

多个 bounded context 使用 Context Map。Context Map 的 `Contexts` 使用固定三列表格，`Relationships` 使用非空的自然语言列表。

以下 Context Map 中的 `./docs/context/` 只展示相对链接的写法。每个 leaf 的实际路径必须位于 `docs/context/` 中：

```md
# Context Map

## Contexts

| Context | Leaf | Owns |
| --- | --- | --- |
| Ordering | [Ordering](./docs/context/ordering.md) | 接收并跟踪 customer order，定义 Customer。 |
| Billing | [Billing](./docs/context/billing.md) | 生成 invoice 并处理 payment。 |
| Fulfillment | [Fulfillment](./docs/context/fulfillment.md) | 管理仓库拣货和发货。 |

## Relationships

- Ordering 发出 `OrderPlaced` event。Fulfillment 消费这些 event 并开始拣货。
- Fulfillment 发出 `ShipmentDispatched` event。Billing 消费这些 event 并生成 invoice。
- Ordering 定义 Customer。Billing 使用权威引用指向 Ordering 的定义。
```

Context Map 遵守以下合同：

- `Context` 是非空且唯一的 bounded context 名称。
- `Leaf` 整格是一个 Markdown 链接。链接相对 Context Map 解析，目标位于 `docs/context/` 中，并以 `.md` 结尾。
- `Owns` 是非空的自然语言所有权说明。
- `Relationships` 至少包含一个 Markdown 列表项。bounded context 之间的关系使用自然语言。
- `mmw domain sync` 管理规则标记之间的完整正文。项目只维护 `Contexts` 和 `Relationships`。

存在多个 bounded context 时，判断当前主题属于哪个 bounded context。如果无法判断，当场询问用户。

## 权威引用

共享术语只在一个 leaf 中定义。其他 leaf 使用以下格式引用权威定义：

```md
**Customer**：
(authoritative: [Customer](../ordering.md))
```

路径相对当前 leaf 解析。引用目标必须是同一 Context Map 已登记的 leaf。
