# `improve-codebase-architecture` 1.2.2 中文翻译基线

## `SKILL.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md:1-5 -->

```yaml
---
name: improve-codebase-architecture
description: 扫描代码库以寻找 deepening opportunity，把它们呈现为可视化 HTML 报告，然后围绕你选中的候选项进行 grilling。
disable-model-invocation: true
---
```

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md:7-16 -->

# Improve Codebase Architecture

呈现架构摩擦，并提出 **deepening opportunity**，也就是把 shallow module 变成 deep module 的重构。目标是可测试性和 AI 可导航性。

这条命令以项目的领域模型为依据，并建立在共享设计词汇上：

- 运行 `/codebase-design` 技能，取得架构词汇（**module**、**interface**、**depth**、**seam**、**adapter**、**leverage**、**locality**）和对应原则（`deletion test`、“interface 是 test surface”、“一个 adapter 是假设性 seam，两个才是真实 seam”）。在每条建议中准确使用这些术语；不要漂移到 `component`、`service`、`API` 或 `boundary`。
- `CONTEXT.md` 中的领域语言为良好的 seam 命名；`docs/adr/` 中的 ADR 记录本命令不应重新争论的决定。

## 流程

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md:18-35 -->

### 1. 探索

**扫描前先确定范围——YAGNI。** 对 module 执行 deepening 的回报，是让未来对它的改动更容易，因此要额外重视代码库最近改动的部分。开始查看前，先决定**查看哪里**：

- 如果用户指定了方向，例如一个 module、子系统或痛点，就采用该方向，并跳过下方推断。
- 否则，沿提交历史向前查看足够长的一段（`git log --oneline`），找出代码库热点，也就是反复出现的文件和区域；先让这些路径吸引你的注意。如果改动分散，没有清晰热点，就扩大范围。

先读取项目的领域术语表（`CONTEXT.md`）和本次涉及区域内的全部 ADR。

随后使用 Agent 工具，并设置 `subagent_type=Explore` 来探索代码库。不要遵循僵化的启发法；自然探索，并记录你遇到摩擦的位置：

- 理解一个概念时，哪些位置要求在许多小型 module 之间反复跳转？
- 哪些 module 很 **shallow**，也就是 interface 几乎与 implementation 一样复杂？
- 哪些纯函数只是为了可测试性而被提取，但真正的 bug 隐藏在调用方式中，因而没有 **locality**？
- 哪些紧密耦合的 module 会跨越 seam 泄漏？
- 代码库的哪些部分没有测试，或者难以通过当前 interface 测试？

对你怀疑 shallow 的任何对象应用 **`deletion test`**：删除它会集中复杂性，还是只会移动复杂性？你要寻找的信号是“会集中”。

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md:37-60 -->

### 2. 把候选项呈现为 HTML 报告

把一个自包含 HTML 文件写入操作系统临时目录，使仓库中不会留下任何内容。从 `$TMPDIR` 解析临时目录；不存在时回退到 `/tmp`，Windows 则使用 `%TEMP%`。写入 `<tmpdir>/architecture-review-<timestamp>.html`，使每次运行都得到新文件。为用户打开它：Linux 使用 `xdg-open <path>`，macOS 使用 `open <path>`，Windows 使用 `start <path>`；并把绝对路径告诉用户。

报告使用 **CDN 上的 Tailwind** 完成布局和样式，并在图、流程或序列能够可靠表达结构时使用 **CDN 上的 Mermaid** 绘图。混合使用 Mermaid 和手工 CSS 或 SVG 图示：关系具有图结构时使用 Mermaid，例如调用图、依赖和序列；需要更具编辑设计感的内容时，使用手工 div 或 SVG，例如 `mass diagram`、剖面图和折叠动画。每个候选项都要有**改动前与改动后的图示**。报告必须以视觉内容为主。

为每个候选项渲染一张卡片，其中包含：

- **文件**——涉及哪些文件或 module
- **问题**——当前架构为何产生摩擦
- **方案**——用直白语言说明会改变什么
- **收益**——用 locality 和 leverage 解释，并说明测试如何改进
- **改动前/后图示**——并排、手工绘制，展示 shallow 状态和 deepening 后状态
- **推荐强度**——`Strong`、`Worth exploring`、`Speculative` 三者之一，渲染为徽章

在报告末尾加入**首要推荐**章节：说明你会最先处理哪个候选项，以及原因。

**领域内容使用 `CONTEXT.md` 词汇，架构内容使用 `/codebase-design` 词汇。** 如果 `CONTEXT.md` 定义了 `Order`，就说 `Order intake module`，不要说 `FooBarHandler`，也不要说 `Order service`。

**ADR 冲突**：如果候选项与现有 ADR 冲突，只有摩擦真实到足以重新审视 ADR 时才呈现它。在卡片中明确标记，例如使用警告说明：“与 ADR-0007 冲突，但值得重新讨论，因为……”。不要列出 ADR 禁止的每一项理论重构。

完整 HTML scaffold、图示模式和样式指引参见 [HTML-REPORT.md](HTML-REPORT.md)。

此时**不要**提出 interface。文件写完后询问用户：“你想探索其中哪一项？”

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md:62-71 -->

### 3. Grilling 循环

用户选择候选项后，运行 `/grilling` 技能，与用户一起走过决策树，包括约束、依赖、deepening 后 module 的形态、seam 后面的内容和保留哪些测试。

决定逐渐明确时，就地执行副作用；运行 `/domain-modeling` 技能，使领域模型随流程保持最新：

- **按照 `CONTEXT.md` 中不存在的概念为 deepening 后的 module 命名？** 把该术语加入 `CONTEXT.md`。如果文件不存在，就按需创建。
- **在对话中明确一个含混术语？** 立即更新 `CONTEXT.md`。
- **用户以一项起关键作用的理由否决候选项？** 提议一份 ADR，并这样表达：“要我把它记录为 ADR，使未来的架构审查不会再次建议它吗？”只有未来探索者确实需要这项理由来避免重复建议时才提议。跳过短暂理由，例如“现在不值得”，也跳过不言自明的理由。
- **想为 deepening 后的 module 探索备选 interface？** 运行 `/codebase-design` 技能，并使用其 design-it-twice 并行 subagent 模式。

## `HTML-REPORT.md`

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:1-5 -->

# HTML 报告格式

架构审查被渲染为操作系统临时目录中的单一自包含 HTML 文件。Tailwind 和 Mermaid 都来自 CDN。Mermaid 能够可靠处理具有图结构的图示；手工 div 和内联 SVG 用于更具编辑设计感的视觉内容，例如 `mass diagram` 和剖面图。混合使用二者；不要让 Mermaid 承担一切，否则报告会开始显得千篇一律。

## Scaffold

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:7-34 -->

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>架构审查 — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* Tailwind 无法干净覆盖的内容使用这一小层自定义样式：
         seam 虚线、具有手绘感的箭头等。 */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:36-55 -->

## 页头

仓库名称、日期和一份紧凑图例：实线框代表 module，虚线代表 seam，红色箭头代表泄漏，粗深色框代表 deep module。不要写介绍段落；直接进入候选项。

## 候选项卡片

图示承担主要说明责任。文字稀少、直白，并自然使用 `/codebase-design` 技能中的术语表词汇。

每个候选项对应一个 `<article>`：

- **标题**——简短，为 deepening 命名，例如“归并 Order 接收管线”。
- **徽章行**——推荐强度（`Strong` 使用 emerald，`Worth exploring` 使用 amber，`Speculative` 使用 slate），并加上依赖分类标记（`in-process`、`local-substitutable`、`ports & adapters`、`mock`）。
- **文件**——使用等宽字体的清单，样式为 `font-mono text-sm`。
- **改动前/后图示**——核心内容。两列并排。参见下方模式。
- **问题**——一句话。说明哪里造成困难。
- **方案**——一句话。说明什么会改变。
- **收益**——项目符号，每项不超过 6 个词。例如“测试只经过一个 interface”“Pricing 逻辑不再泄漏”“删除 4 个 shallow wrapper”。
- **ADR 提示框**（如果适用）——amber 浅色框中的一行文字。

不要写解释段落。如果图示需要一个段落才能理解，就重画图示。

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:57-76 -->

## 图示模式

选择适合候选项的模式。混合使用。不要让每张图看起来相同；多样性本身就是目的之一。

### Mermaid 图：依赖或调用流程的主力

当重点是“X 调用 Y，Y 调用 Z，看看有多混乱”时，使用 Mermaid `flowchart` 或 `graph`。把它包在 Tailwind 样式卡片内，使它不像突然空降进来。通过 classDef 把泄漏 edge 设为红色，把 deep module 设为深色。序列图很适合“改动前需要 6 次往返，改动后只需 1 次”。

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:78-92 -->

### 手工方框与箭头：Mermaid 布局妨碍表达时

用带边框和标签的 `<div>` 表示 module。用内联 SVG `<line>` 或 `<path>` 元素表示箭头，并在相对定位容器上绝对定位。当你希望“改动后”图示呈现一个带粗边框的 deep module，内部对象以灰色淡化时使用；Mermaid 无法用合适的视觉重量渲染这种效果。

### 剖面图：适合分层的 shallow 状态

堆叠水平带（`h-12 border-l-4`），展示一次调用经过的各层。改动前：6 个没有实际作用的薄层。改动后：1 个粗带，并用归并后的职责作为标签。

### Mass diagram：适合“interface 与 implementation 一样宽”

每个 module 使用两个矩形：一个表示 interface 表面积，一个表示 implementation。改动前：interface 矩形几乎与 implementation 矩形一样高，也就是 shallow。改动后：interface 矩形较矮，implementation 矩形较高，也就是 deep。

### 调用图归并

改动前：用嵌套方框渲染函数调用树。改动后：把同一棵树归并到一个方框中；原本的调用现在成为内部调用，以淡化样式显示在方框内。

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:94-104 -->

## 样式指引

- 使用克制的编辑设计风格，不要企业仪表盘风格。留出宽松空白。标题可以选用衬线字体，例如 `font-serif` 与 stone 或 slate 配合良好。
- 谨慎使用颜色：一种强调色，例如 emerald 或 indigo；泄漏使用 red，警告使用 amber。
- 图示高度保持在约 320px，使改动前与改动后能够舒适地并排显示，无需滚动。
- 图示内的 module 标签使用 `text-xs uppercase tracking-wider`，使它们读起来像示意图，不像 UI。
- 仅使用 Tailwind CDN 和 Mermaid ESM import 两项脚本。报告其余部分保持静态；没有应用代码，除了 Mermaid 自身渲染以外没有交互。

## Top recommendation 章节

使用一张较大的卡片。写候选项名称、一句原因和指向候选项卡片的锚点链接。仅此而已。

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/HTML-REPORT.md:106-123 -->

## 语气

使用直白语言，并保持简洁；但架构名词和动词必须直接来自 `/codebase-design` 技能。简洁不能成为术语漂移的借口。

**必须准确使用：** module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality。

**绝不替换成：** component、service、unit（代替 module）；API、signature（代替 interface）；boundary（代替 seam）；layer、wrapper（本意是 module 时）。

**符合这种风格的措辞：**

- “Order intake module 很 shallow；interface 几乎与 implementation 相同。”
- “Pricing 跨越 seam 泄漏。”
- “执行 deepening：一个 interface，一个测试位置。”
- “两个 adapter 证明这条 seam 成立：生产环境使用 HTTP，测试使用内存实现。”

**收益项目符号**要使用术语表中的词说明收益，例如“locality：bug 集中在一个 module 中”“leverage：一个 interface，N 个调用位置”“interface 缩小；implementation 吸收 wrapper”。不要写“更容易维护”或“代码更干净”；这些词不在术语表中，不值得出现。

不要含糊，不要先说空话，不要写“值得注意的是……”。一句话能变成项目符号，就改成项目符号。一个项目符号能够删掉，就删掉。如果某个术语不在 `/codebase-design` 术语表中，先寻找术语表里可用的词，再考虑创造新词。

## `agents/openai.yaml`

<!-- source: vendor/mattpocock-skills/skills/engineering/improve-codebase-architecture/agents/openai.yaml:1-5 -->

```yaml
interface:
  display_name: "Improve Codebase Architecture"
  short_description: "寻找架构改进并进行 grilling"
policy:
  allow_implicit_invocation: false
```
