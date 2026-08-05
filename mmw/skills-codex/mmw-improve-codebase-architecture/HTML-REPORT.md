# 报告怎么写

这份架构走查渲染成一个自包含的 HTML 文件，落系统临时目录。Tailwind 和 Mermaid 都走 CDN。Mermaid 画图结构的东西很稳；手搭的 div 和内联 SVG 负责更有编排感的那些视觉（体量图、剖面图）。两种混用，不要什么都交给 Mermaid。

## 骨架

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
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

## 页头

仓库名、日期，加一个紧凑的图例：实线框是 module，虚线是 seam，红箭头是漏出去的耦合，粗深色框是 deep module。不写引言段落，直接进候选。

## 候选卡片

图承担主要信息，文字稀疏、平实，直接用 `$mmw:mmw-codebase-design` 定义的词，不加修饰。

一个候选一个 `<article>`：

- **标题**——短，说清这次做深的是什么（例如 "Collapse the Order intake pipeline"）。
- **徽章行**——推荐强度（`Strong` 用 emerald、`Worth exploring` 用 amber、`Speculative` 用 slate），再加一个依赖类别的标签（`in-process`、`local-substitutable`、`ports & adapters`、`mock`）。
- **文件**——等宽列表，`font-mono text-sm`。
- **Before / After 图**——整张卡片的重心。两列并排，画法见本文「图的几种画法」一节。
- **Problem**——一句话。哪里疼。
- **Solution**——一句话。改什么。
- **Wins**——列点，每条不超过六个词。例如 "Tests hit one interface"、"Pricing logic stops leaking"、"Delete 4 shallow modules"。
- **ADR 提示**（如果撞上了）——琥珀色底的一行。

不写解释性的段落。一张图需要一段话才看得懂，就把图重画。

## 图的几种画法

按候选的情况挑，混着用，不要每张图都长一个样。

### Mermaid 图（画依赖和调用流的主力）

重点是「X 调 Y 调 Z，你看这一团」时，用 Mermaid 的 `flowchart` 或 `graph`。用 Tailwind 卡片包一层。用 classDef 把漏出去的那条边标红、把 deep module 标深。「before 六次往返、after 一次」这种用序列图效果很好。

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

### 手搭的方框加箭头（Mermaid 的自动布局不听话时）

module 用带边框和标签的 `<div>`，箭头用内联 SVG 的 `<line>` 或 `<path>`，绝对定位盖在相对定位的容器上。想让 after 那张图呈现成一个粗边框的 deep module、内部件灰掉时用这个。

### 剖面图（适合分层式的 shallow）

用横向色带堆叠（`h-12 border-l-4`），表示一次调用穿过了几层。before：六层薄的，每层什么都没做。after：一条厚带，标上合并之后的那个职责。

### 体量图（适合「interface 和 implementation 一样宽」）

一个 module 画两个矩形，一个是 interface 的表面积，一个是 implementation。before：interface 的矩形高得几乎和 implementation 一样（shallow）。after：interface 矩形变矮，implementation 矩形变高（deep）。

### 调用图坍缩

before：一棵函数调用树，画成嵌套的方框。after：同一棵树收进一个方框，里面那些现在变成内部调用的用淡色显示。

## 风格

- 偏编排感，不要企业仪表盘感。留白给足。标题用衬线（`font-serif`）配 stone / slate 很好看。
- 颜色克制：一个强调色（emerald 或 indigo），加红色标漏出去的耦合、琥珀色标警告。
- 图控制在 320px 高左右，让 before/after 并排时不用滚动就看得完。
- 图里的 module 标签用 `text-xs uppercase tracking-wider`。
- 只有 Tailwind CDN 和 Mermaid ESM 这两个脚本。报告本身是静态的，除了 Mermaid 自己的渲染之外没有任何交互。

## Top recommendation 一节

一张更大的卡片。候选名字、一句话说为什么、一个锚链接跳到它的卡片。就这些。

## 语气

平实、简洁，架构上的名词和动词直接取自 `$mmw:mmw-codebase-design`。

**只用**：module、interface、implementation、depth、deep、shallow、seam、adapter、leverage、locality。

**不要换成**：component、service、unit（当你指 module 时）· API、signature（当你指 interface 时）· boundary（当你指 seam 时）· layer、wrapper（当你指 module 时）。

**符合 `$mmw:mmw-codebase-design` 的说法**：

- "Order intake module is shallow — interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Wins 那几条**用 `$mmw:mmw-codebase-design` 定义的词说收益，例如 *"locality: bugs concentrate in one module"*、*"leverage: one interface, N call sites"*、*"interface shrinks; implementation absorbs the shallow modules"*。不要写 *"easier to maintain"* 或 *"cleaner code"*，这些词不在 `$mmw:mmw-codebase-design` 中。

不要模棱两可，不要清嗓子，不要「值得一提的是……」。一句话能写成一条列点就写成列点，一条列点能删就删。一个词不在 `$mmw:mmw-codebase-design` 中，先找一个在里面的，再考虑发明新词。
