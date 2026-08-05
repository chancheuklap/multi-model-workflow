---
name: mmw-domain-modeling
description: 把项目的领域模型建起来、磨锋利。用户要把领域术语或 ubiquitous language 定下来、要记一个架构决定时用它；别的技能需要维护领域模型时也用它。
---

# Domain Modeling

一边设计一边主动把项目的领域模型建起来、磨锋利。这是*主动*的那份纪律——挑战用词、造边界场景、一旦想清楚就当场把 glossary 和决定写下来。（只是*读*领域文档取用词不算这个技能——那是任何技能都能做的一行习惯。这个技能管的是你在改这个模型，不是消费它。）

## 读领域文档

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。运行 `mmw domain path`：返回 `map` 时，先读 Map，再读本次涉及的全部命名 leaf；返回 `single` 时，读命令返回的领域文档；返回 `none` 时，默认直接继续，不报告缺失，也不创建领域文档。只有本文「`none` 形态首次建模」一节规定的场景可以创建。

## 文件放哪

**落点是目标仓库的事实，不是这个技能的事实，不要写死。** 建任何文件之前先跑这两条：

```bash
mmw domain path    # 这个仓库现在是哪种形态：map / single / none，加对应的路径
mmw domain dirs    # 写入侧的四个落点：single、map、context、adr
```

### `none` 形态首次建模

`none` 是合法形态。只读领域文档，或者其他技能顺带调用本技能时，不创建领域文档。

只有以下两个条件同时成立时，才按需创建首份领域文档：

1. 用户当前请求本身是建立或维护领域模型。
2. 对话已经定下至少一个需要长期保留的领域术语。

条件满足后，先判断 bounded context 的数量和边界：

- 明确只有一个 bounded context：在 `mmw domain dirs` 返回的 `single` 路径创建领域文档，并写入首个长期术语。
- 明确存在多个 bounded context：先运行 `mmw domain map-init`。只有命令输出 `map-init<TAB><相对路径><TAB>created` 后才编辑它创建的 Map；禁止直接创建 Map，也禁止复制受管规则。然后在 `mmw domain dirs` 返回的 `context` 路径或其子目录创建首个命名 leaf。在 Map 中登记它的实际路径，补齐全部已确认的 `Contexts` 行，并写入至少一条已确认的 `Relationships` 关系。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。
- bounded context 的数量、术语归属或跨上下文关系不清楚：一次只问用户一个具体问题。用户明确决定之前不创建领域文档。

首次建模写完后运行 `mmw domain check`。检查失败就修正 Map、leaf 或受管规则；检查通过之前不得提交。

`mmw domain path` 给 `single` 时，术语写进命令返回的领域文档：

```
/
├── <mmw domain path 返回的 single leaf>
├── <mmw domain dirs 返回的 adr 落点>/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

给 `map`，说明有多个上下文。命令返回的 Map 是索引，指出每个上下文的命名 leaf。新 leaf 建在 `mmw domain dirs` 给的 `context` 路径或其子目录中，并使用 `.md` 扩展名：

```
/
├── <mmw domain path 返回的 Map>
├── <mmw domain dirs 返回的 adr 落点>/   ← 全系统级的决定
├── <mmw domain dirs 给的 context 落点>/
│   ├── ordering.md
│   └── billing/billing-language.md
```

Map 中的 `Leaf` 链接决定已有上下文的真实落点。不要根据上下文名推测文件名，也不要在 Map 之外另建没有登记的 leaf。

文件按需建——有东西要写了才建。Map 形态新增 leaf 时，同时登记 Map 的 `Contexts` 和 `Relationships`。没有 ADR 目录时，第一份 ADR 要写时再按 `mmw domain dirs` 返回的 `adr` 路径创建。

## 谈的过程里

### 拿 glossary 挑战他

用户用了一个跟相关 leaf 里既有说法冲突的词，当场挑明。「你的 glossary 把『取消』定义成 X，但你现在说的像是 Y——到底是哪个？」

### 把含糊的说法收紧

用户用了含糊的词，或者一个词被当成几个意思在用，提出一个精确的规范说法。「你说的『账户』——指的是 Customer 还是 User？这是两个东西。」

### 拿具体场景压

在谈领域关系时，用具体场景压它们站不站得住。造一些能戳到边界情形的场景，逼用户把概念之间的界线说清楚。

### 跟代码对一下

用户说某件事是怎么运作的，去看代码同不同意。发现矛盾就摆到明面上：「你的代码取消的是整张 Order，但你刚说可以部分取消——哪个是对的？」

### 当场更新拥有术语的 leaf

一个术语定下来，就地更新拥有这个术语的 leaf。不要攒着——想清楚一个记一个。共享术语只在权威 leaf 定义，其他 leaf 使用权威引用。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。

领域 leaf 里绝不能有实现细节。不要把 leaf 当 spec、当草稿纸、当实现决定的收纳箱。它是一份 glossary，仅此而已。

### ADR 少提

三个条件同时成立才提议写一份 ADR：

1. **难以回退** —— 以后改主意的代价是实打实的
2. **不给上下文会让人意外** —— 将来的读者会想「他们当初为什么要这么做？」
3. **是一次真取舍的结果** —— 当时真有别的选项，你为了具体理由选了这个

三条缺一条就不写。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。
