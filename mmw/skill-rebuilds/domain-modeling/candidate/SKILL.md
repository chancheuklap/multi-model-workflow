---
name: mmw-domain-modeling
description: 构建并明确项目的领域模型。用户想要明确领域术语、通用语言或 bounded context、记录一项架构决定，或者其他技能需要维护领域模型时使用。
---

# Domain Modeling

在设计过程中主动构建并明确项目的领域模型。这是一项**主动**实践：质疑术语、构造边界场景，并在术语和决定刚刚明确时就把它们写入术语表和决定记录。（仅仅为了取得词汇而**读取**领域文档不属于本技能；任何技能都可以把它作为一行操作习惯。本技能用于改变模型，不用于只消费模型。）

## 选择入口

- 用户想把整个计划、决定或未成形的想法追问清楚时，移交 `/mmw-grilling`。它会在同一段对话中应用本技能。
- 用户想定义或修正领域术语、通用语言、bounded context、上下文关系或 ADR 时，继续本技能。
- 其他技能为了维护领域模型而调用时，继续本技能；维护完成后交回调用方。

## 文件结构

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。运行：

```bash
mmw domain path
mmw domain dirs
```

`mmw domain path` 返回当前领域文档形态和读取路径：

| 返回 | 处理方式 |
| --- | --- |
| `single` | 读取命令返回的领域文档。该仓库只有一个 bounded context |
| `map` | 先读取命令返回的 Context Map，再读取本次涉及的全部 leaf |
| `none` | 当前没有领域文档。继续讨论；第一个长期术语得到解决时按需创建 |

`mmw domain dirs` 返回 `single`、`map`、`context` 和 `adr` 的写入位置。文件位置属于目标仓库合同，不在技能中写死。

多数仓库只有一个 bounded context：

```
/
├── <single 领域文档>
├── <adr 路径>/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

如果 `mmw domain path` 返回 `map`，该仓库有多个 bounded context。Context Map 会指向每个 leaf 的实际位置：

```
/
├── <Context Map>
├── <adr 路径>/                    ← 全系统决定
├── <context 路径>/
│   ├── ordering.md
│   └── billing.md
└── src/
```

按需创建文件，也就是只有在确实有内容要写时才创建。如果当前形态是 `none`，就在第一个需要长期保留的领域术语得到解决时创建领域文档。直接运行本技能和 `/mmw-grilling` 应用本技能遵守同一条规则。如果尚未形成长期领域结论，不创建文件。

创建首份领域文档前，先判断项目有一个还是多个 bounded context：

- 明确只有一个 bounded context：在 `mmw domain dirs` 返回的 `single` 路径创建领域文档，并写入已经解决的首个术语。
- 明确存在多个 bounded context：运行 `mmw domain map-init`。命令成功创建 Context Map 后，在 `context` 路径创建首个 leaf，并在 Context Map 中登记实际路径、所有权和已经确认的关系。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。
- bounded context 的数量、术语归属或关系仍不明确：当场询问用户。取得答案后继续当前步骤。

创建或修改 Context Map 和 leaf 后运行 `mmw domain check`。检查通过后，这一步才完成。

如果不存在 ADR 路径，就在需要第一份 ADR 时按需创建。

## Session 期间

### 对照术语表提出质疑

用户使用的术语与相关领域文档中的现有语言冲突时，立即指出。“你的术语表把 cancellation 定义为 X，但你现在表达的意思似乎是 Y；到底是哪一个？”

### 明确含混语言

用户使用含混或承担多重含义的术语时，提出一个准确的规范术语。“你说的是 account；你指 Customer 还是 User？二者是不同事物。”

### 讨论具体场景

讨论领域关系时，用具体场景进行压力测试。构造能够探查边界情况的场景，迫使用户准确说明概念之间的边界。

### 与代码交叉检查

用户说明某项内容如何运行时，检查代码是否一致。如果发现矛盾，就把它呈现出来：“你的代码会取消整个 Order，但你刚才说可以部分取消；哪一个才正确？”

### 就地更新领域文档

一个术语得到解决时，立即更新拥有该术语的领域文档。不要成批积攒；在术语明确时就记录。单 bounded context 仓库更新 `single` 文档。多 bounded context 仓库更新拥有该术语的 leaf。使用 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md) 中的格式。

共享术语只在一个 leaf 中定义。其他 leaf 使用权威引用指向拥有该术语的 leaf。

领域文档必须完全不包含实现细节。不要把领域文档当作 spec、scratch pad 或存放实现决定的仓库。它只是术语表，没有其他用途。

### 谨慎提议 ADR

只有在以下三项全部成立时，才提议创建 ADR：

1. **难以逆转**——以后改变主意的成本不可忽略
2. **缺少上下文时令人意外**——未来读者会疑惑：“他们为什么这样做？”
3. **来自真实取舍**——确实存在其他选项，而且你因为具体理由选择了其中一个

缺少其中任何一项，都不要创建 ADR。使用 [ADR-FORMAT.md](./ADR-FORMAT.md) 中的格式。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 其他技能调用了本技能，而且领域模型维护已经完成 | **移交**：把更新的术语、关系和 ADR 交回调用方 |
| 用户直接要求维护领域模型，而且领域模型维护已经完成 | **停**：报告更新的术语、关系和 ADR |
