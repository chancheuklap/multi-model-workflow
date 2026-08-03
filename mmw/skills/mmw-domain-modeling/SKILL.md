---
name: mmw-domain-modeling
description: 把项目的领域模型建起来、磨锋利。用户要把领域术语或 ubiquitous language 定下来、要记一个架构决定时用它；别的技能需要维护领域模型时也用它。
---

# Domain Modeling

一边设计一边主动把项目的领域模型建起来、磨锋利。这是*主动*的那份纪律——挑战用词、造边界场景、一旦想清楚就当场把 glossary 和决定写下来。（只是*读* `CONTEXT.md` 取用词不算这个技能——那是任何技能都能做的一行习惯。这个技能管的是你在改这个模型，不是消费它。）

## 读领域文档

别的技能要读领域文档时照这里做，各自不再复述：跑 `mmw domain path`——报 `map` 就读它给的那份索引，按索引取这次要碰的那几个上下文，各读各的 `CONTEXT.md`；报 `single` 就读它给的那一份；报 `none` 就直接往下走，不要停下来建。

## 文件放哪

**落点是目标仓库的事实，不是这个技能的事实，不要写死。** 建任何文件之前先跑这两条：

```bash
mmw domain path    # 这个仓库现在是哪种形态：map / single / none，加对应的路径
mmw domain dirs    # 写入侧的两个落点：新上下文的根目录、ADR 目录
```

`mmw domain path` 给 `single` 或 `none`，说明这个仓库只有一个上下文，术语全写在根 `CONTEXT.md`：

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

给 `map`，说明有多个上下文，根上那份 `CONTEXT-MAP.md` 是索引，指出每个上下文住在哪。新上下文建在 `mmw domain dirs` 给的 `context` 那一行下面：

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← 全系统级的决定
├── <mmw domain dirs 给的 context 落点>/
│   ├── ordering/CONTEXT.md
│   └── billing/CONTEXT.md
```

**多上下文的仓库没有根 `CONTEXT.md`。** 往那里写会在根上凭空造出一份不该存在的。

文件按需建——有东西要写了才建。没有 `CONTEXT.md`，第一个术语定下来时建。没有 `docs/adr/`，第一份 ADR 要写时建。

## 谈的过程里

### 拿 glossary 挑战他

用户用了一个跟 `CONTEXT.md` 里既有说法冲突的词，当场挑明。「你的 glossary 把『取消』定义成 X，但你现在说的像是 Y——到底是哪个？」

### 把含糊的说法收紧

用户用了含糊的词，或者一个词被当成几个意思在用，提出一个精确的规范说法。「你说的『账户』——指的是 Customer 还是 User？这是两个东西。」

### 拿具体场景压

在谈领域关系时，用具体场景压它们站不站得住。造一些能戳到边界情形的场景，逼用户把概念之间的界线说清楚。

### 跟代码对一下

用户说某件事是怎么运作的，去看代码同不同意。发现矛盾就摆到明面上：「你的代码取消的是整张 Order，但你刚说可以部分取消——哪个是对的？」

### 当场更新 CONTEXT.md

一个术语定下来，就地更新 `CONTEXT.md`。不要攒着——想清楚一个记一个。格式见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)。

`CONTEXT.md` 里绝不能有实现细节。不要把 `CONTEXT.md` 当 spec、当草稿纸、当实现决定的收纳箱。它是一份 glossary，仅此而已。

### ADR 少提

三个条件同时成立才提议写一份 ADR：

1. **难以回退** —— 以后改主意的代价是实打实的
2. **不给上下文会让人意外** —— 将来的读者会想「他们当初为什么要这么做？」
3. **是一次真取舍的结果** —— 当时真有别的选项，你为了具体理由选了这个

三条缺一条就不写。格式见 [ADR-FORMAT.md](./ADR-FORMAT.md)。
