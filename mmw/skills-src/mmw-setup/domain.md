# 领域文档

> 已过时的背景材料，不参与行为判断；作废范围和当前做法见 [legacy-setup.md](legacy-setup.md)。

技能探索代码前该怎么读本仓库的领域文档。

## 开工前先读这两处

- **`CONTEXT.md`**（仓库根）——glossary。项目自己的话怎么说。
- **`docs/adr/`**——ADR（Architecture Decision Record，ADR）。只读跟本次要动的地方相关的那几份。

**文件不存在就默默继续。** 不要提它们缺失，不要建议先建。

## 布局

单上下文，一份根 `CONTEXT.md` 加一个 `docs/adr/`：

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-<kebab-标题>.md
│   └── 0002-<kebab-标题>.md
└── ...
```

ADR 编号四位、从 `0001` 起、只增不改。

多上下文，仓库根放一份 `CONTEXT-MAP.md` 当索引，每个上下文一份自己的 `CONTEXT.md`，**一律落在 `docs/context/<上下文名>/CONTEXT.md`**：

```
/
├── CONTEXT-MAP.md          ← 索引：有哪几个上下文、各自在哪、彼此什么关系
├── docs/context/
│   ├── ordering/CONTEXT.md
│   └── billing/CONTEXT.md
├── docs/adr/
└── ...
```

`docs/context/**` 是本仓库的落点。`/mmw-domain-modeling` 建文件之前会来读本文件取落点和 ADR 编号方案，格式和写法照它自己的。

读的顺序：先查仓库根有没有 `CONTEXT-MAP.md`。有就按它的索引找到这次要碰的那几个上下文，读它们各自的 `CONTEXT.md`；没有就回退根 `CONTEXT.md`；两个都没有就直接往下走。

**几条分支同时写 ADR 时先用草稿名。** 跑 `/mmw-wayfinder` 时，好几个会话各在自己的分支上解一张 decision ticket，同时写 ADR 必定撞号，所以在这类分支上先写成 `docs/adr/draft-<ticket 编号>-<kebab-标题>.md`，等这张 decision ticket 的结果分支合回上一层分支时再统一改成正式编号。单条分支独占的场景不用绕这一道，直接取下一个编号。

## 用 glossary 里的词

输出里提到一个领域概念时（issue 标题、重构提案、假设、测试名），用 `CONTEXT.md` 里定下的那个词，不要漂到它明确避开的近义词。

要用的概念还不在 glossary 里，这本身是信号：要么你在发明项目不用的语言（重新想），要么是真缺一条（记下来交给 `/mmw-domain-modeling`）。

## 撞上既有决定要摆到明面

输出跟某份 ADR 矛盾时说出来，不要默默覆盖：

> 与 ADR-0007（事件溯源的订单模型）矛盾——但值得重开，因为……

## 两者留在仓库里，跟代码同一个提交演进

glossary 和 ADR 不上 Wiki，一直留在仓库里。spec 和计划文档走的是另一条路（落地后上 Wiki，见 `issue-tracker.md`）。
