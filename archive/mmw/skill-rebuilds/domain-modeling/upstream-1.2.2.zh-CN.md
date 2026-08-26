# `domain-modeling` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:1-4 -->

```yaml
---
name: domain-modeling
description: 构建并明确项目的领域模型。用户想要明确领域术语或通用语言、记录一项架构决定，或者其他技能需要维护领域模型时使用。
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:6-12 -->

# Domain Modeling

在设计过程中主动构建并明确项目的领域模型。这是一项**主动**实践：质疑术语、构造边界场景，并在术语和决定刚刚明确时就把它们写入术语表和决定记录。（仅仅为了取得词汇而**读取** `CONTEXT.md` 不属于本技能；任何技能都可以把它作为一行操作习惯。本技能用于改变模型，不用于只消费模型。）

## 文件结构

多数仓库只有一个 context：

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:14-22 -->

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:24-40 -->

如果仓库根目录存在 `CONTEXT-MAP.md`，该仓库就有多个 context。map 会指向每个 context 的所在位置：

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 系统级决定
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context 专属决定
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

按需创建文件，也就是只有在确实有内容要写时才创建。如果不存在 `CONTEXT.md`，就在第一个术语得到解决时创建。如果不存在 `docs/adr/`，就在需要第一份 ADR 时创建。

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:42-64 -->

## Session 期间

### 对照术语表提出质疑

用户使用的术语与 `CONTEXT.md` 中的现有语言冲突时，立即指出。“你的术语表把 cancellation 定义为 X，但你现在表达的意思似乎是 Y；到底是哪一个？”

### 明确含混语言

用户使用含混或承担多重含义的术语时，提出一个准确的规范术语。“你说的是 account；你指 Customer 还是 User？二者是不同事物。”

### 讨论具体场景

讨论领域关系时，用具体场景进行压力测试。构造能够探查边界情况的场景，迫使用户准确说明概念之间的边界。

### 与代码交叉检查

用户说明某项内容如何运行时，检查代码是否一致。如果发现矛盾，就把它呈现出来：“你的代码会取消整个 Order，但你刚才说可以部分取消；哪一个才正确？”

### 就地更新 CONTEXT.md

一个术语得到解决时，立即更新 `CONTEXT.md`。不要成批积攒；在术语明确时就记录。使用 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 中的格式。

`CONTEXT.md` 必须完全不包含实现细节。不要把 `CONTEXT.md` 当作 spec、scratch pad 或存放实现决定的仓库。它只是术语表，没有其他用途。

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/SKILL.md:66-74 -->

### 谨慎提议 ADR

只有在以下三项全部成立时，才提议创建 ADR：

1. **难以逆转**——以后改变主意的成本不可忽略
2. **缺少上下文时令人意外**——未来读者会疑惑：“他们为什么这样做？”
3. **来自真实取舍**——确实存在其他选项，而且你因为具体理由选择了其中一个

缺少其中任何一项，都不要创建 ADR。使用 [ADR-FORMAT.md](./ADR-FORMAT.md) 中的格式。

## `ADR-FORMAT.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md:1-15 -->

# ADR 格式

ADR 位于 `docs/adr/` 中，并使用连续编号，例如 `0001-slug.md`、`0002-slug.md`。

按需创建 `docs/adr/` 目录，也就是只在需要第一份 ADR 时创建。

## 模板

```md
# {决定的简短标题}

{1 至 3 句话：上下文是什么、我们作出了什么决定，以及为什么。}
```

就这些。一份 ADR 可以只有一个段落。价值在于记录**确实作出了一项决定**以及**作出决定的原因**，不在于填满各个章节。

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md:17-27 -->

## 可选章节

只在这些章节确实能增加价值时加入。大多数 ADR 不需要它们。

- **Status** frontmatter（`proposed | accepted | deprecated | superseded by ADR-NNNN`）——重新审视决定时有用
- **Considered Options**——只有被否决的选项值得记住时才加入
- **Consequences**——只有需要明确说明不明显的下游影响时才加入

## 编号

扫描 `docs/adr/`，找到现有最大编号，然后加一。

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md:29-37 -->

## 何时提议 ADR

以下三项必须全部成立：

1. **难以逆转**——以后改变主意的成本不可忽略
2. **缺少上下文时令人意外**——未来读者会查看代码并疑惑：“他们到底为什么这样做？”
3. **来自真实取舍**——确实存在其他选项，而且你因为具体理由选择了其中一个

如果一项决定容易逆转，就不要记录；你以后只会直接逆转它。如果它并不令人意外，就没有人会疑惑原因。如果不存在真实的其他选项，除了“我们采用了显然的做法”以外，没有其他值得记录的内容。

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/ADR-FORMAT.md:39-47 -->

### 符合条件的内容

- **架构形状。** “我们使用 monorepo。”“write model 采用 event sourcing，read model 被投影到 Postgres。”
- **context 之间的集成模式。** “Ordering 和 Billing 通过 domain event 通信，不使用同步 HTTP。”
- **带来 lock-in 的技术选择。** 数据库、消息总线、鉴权提供方、部署目标。不是每个库；只记录那些更换需要一个季度的选择。
- **边界和范围决定。** “Customer data 由 Customer context 拥有；其他 context 只通过 ID 引用它。”明确说明“不采用什么”与明确说明“采用什么”同样有价值。
- **有意偏离显然路径。** “因为 X，我们使用手写 SQL，不使用 ORM。”任何理性读者都会假定相反做法的情形都属于这一类。它们能防止下一位 engineer 去“修复”一项有意为之的内容。
- **代码中不可见的约束。** “由于合规要求，我们不能使用 AWS。”“由于 partner API contract，响应时间必须低于 200ms。”
- **否决理由并不明显的备选方案。** 如果你考虑过 GraphQL，却因为细微理由选择 REST，就记录它；否则，六个月后还会有人再次提议 GraphQL。

## `CONTEXT-FORMAT.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/CONTEXT-FORMAT.md:1-23 -->

# CONTEXT.md 格式

## 结构

```md
# {Context 名称}

{用一两句话说明该 context 是什么，以及它为何存在。}

## 语言

**Order**:
{用一两句话描述该术语}
_Avoid_：Purchase、transaction

**Invoice**:
交付后发送给 customer 的付款请求。
_Avoid_：Bill、payment request

**Customer**:
下订单的人或组织。
_Avoid_：Client、buyer、account
```

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/CONTEXT-FORMAT.md:25-36 -->

## 规则

- **要有明确主张。** 同一个概念存在多个词时，选出最合适的一个，并把其他词列在 `_Avoid_` 下。
- **定义必须紧凑。** 最多一两句话。定义它**是什么**，不要定义它做什么。
- **只加入本项目 context 特有的术语。** 通用编程概念，例如超时、错误类型、工具模式，即使项目大量使用也不应加入。增加术语前，先问：这是当前 context 独有的概念，还是通用编程概念？只有前者可以加入。
- 自然形成集群时，**用副标题组织术语**。如果所有术语都属于一个紧密统一的领域，扁平清单也可以。

## 单 context 与多 context 仓库

**单 context，多数仓库：** 仓库根目录只有一个 `CONTEXT.md`。

**多个 context：** 仓库根目录的 `CONTEXT-MAP.md` 会列出各个 context、所在位置和相互关系：

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/CONTEXT-FORMAT.md:38-52 -->

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — 接收并跟踪 customer order
- [Billing](./src/billing/CONTEXT.md) — 生成 invoice 并处理 payment
- [Fulfillment](./src/fulfillment/CONTEXT.md) — 管理仓库拣货和发货

## Relationships

- **Ordering → Fulfillment**: Ordering 发出 `OrderPlaced` event；Fulfillment 消费它们并开始拣货
- **Fulfillment → Billing**: Fulfillment 发出 `ShipmentDispatched` event；Billing 消费它们并生成 invoice
- **Ordering ↔ Billing**: 共享 `CustomerId` 和 `Money` 类型
```

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/CONTEXT-FORMAT.md:54-60 -->

本技能推断应使用哪种结构：

- 如果存在 `CONTEXT-MAP.md`，读取它以找出各个 context
- 如果只存在根 `CONTEXT.md`，使用单 context
- 如果二者都不存在，在第一个术语得到解决时按需创建根 `CONTEXT.md`

存在多个 context 时，推断当前主题属于哪个 context。如果无法判断，就询问用户。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/domain-modeling/agents/openai.yaml:1-3 -->

```yaml
interface:
  display_name: "Domain Modeling"
  short_description: "构建并明确领域模型"
```
