# improve-codebase-architecture

源目录：`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，与上游一致；`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` 一起保留。理由：它的 description 与 `codebase-design` 的「find deepening opportunities」抢同一个请求；而且它写报告、问用户挑哪一个、跑 grilling、改 `CONTEXT.md`，worker 在 ticket 里用 `diagnosing-bugs` 查到「没有好 seam」时若自己触发它，night 里没有人回答。另外六个保留这一行的是 `setup-matt-pocock-skills`、`grill-me`、`handoff`、`wait-what`、`grill-with-docs`、`teach`。上游改这一行 → 收上游，两处一起跟。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 收上游原文：user 点名才触发的技能，description 是给读命令列表的人看的一行摘要（`writing-for-agents` 技能的 `SKILL-MECHANICS.md` `## Invocation`），不写「什么时候用我」。上游改这一行 → 收上游 |
| 第一条 bullet 的开头、`**Use CONTEXT.md vocabulary for the domain…**` 那一句、`Once the user picks a candidate` 那一步、`Side effects happen inline as decisions crystallize` 那一句，与 `**Want to explore alternative interfaces for the deepened module?**` 一条 | host 中立：要词汇的写成读那份技能的 `SKILL.md`（`grilling` 那一处用户在场，句子自己写着 `with them`，开子会话会把用户挡在外面），要并行开多个上下文的写成问本机 host 要它自己的 general-purpose subagent（design-it-twice 那一条）。共同理由见 [README.md](README.md#host-中立)，写法见 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Paths, tokens and host neutrality` 与 `### Hand-offs` |
| 第一条 bullet 里那两条禁令（`Use these terms exactly …` 与 `don't drift into "component," "service," "API," or "boundary"`） | 加了范围限定：禁令只管你自己写的设计散文，已经存在的名字不动——命令名、验收判据的类别名、程序打印的字面量各自保留原名。理由是本仓库有以这两个词命名的真东西：`boundary criterion` 这一类验收判据、`ui-acceptance` 技能的 `scripts/boundary-check.py`、判官打印的 `BOUNDARY OK <n>/<n>`，以及合同的 `component` 列；原句不带范围限定，照做的 agent 会去改一条真命令的名字。上游再动这一句 → 收上游对词汇表与三条原则的措辞，范围限定那一句必须留着。同源的一条在 [codebase-design.md](codebase-design.md) |
| 第 2 步第二段（上游写 Tailwind 与 Mermaid 的那段）与该步末句 `See [HTML-REPORT.md]…` | 我们的：页面样子和每张图交给 `diagram-design` 技能，让本仓库所有向用户解释的 HTML 用同一套设计系统；这句只写在这一步，`HTML-REPORT.md` 不重复，因为每次运行都经过这一步；上游那套从 CDN 加载 Tailwind、Mermaid，与 `diagram-design` 只许 Google Fonts 一个外部资源、把照搬 Mermaid 布局列为反面做法直接冲突。同段点名免掉 `diagram-design` §3 的「Confirm before drawing」：一份报告有好几张卡、每张两张图，逐张确认会把报告拖成一连串提问，而报告本身就是用户审阅的地方。上游改这段 → 收上游对卡片与 before/after 要求的措辞，样式与画图仍交给 `diagram-design` |

### HTML-REPORT.md

| 段落 | 我们的意图 |
| --- | --- |
| 开头一段 | 收上游第一句（单个自包含 HTML、放系统临时目录），其余是我们的：本文件只定页面上放什么、从上到下的顺序；`diagram-design` §0 要的那行「用了哪套配色」放页脚，因为页头规定不写引言。上游的 `## Scaffold`（Tailwind 与 Mermaid 的 CDN 骨架）、`## Diagram patterns`、`## Style guidance` 三节不收，理由同 `SKILL.md` 第 2 步那条。上游改这三节 → 不收 |
| `## Header` | 收上游的「仓库名、日期、不写引言」。上游写在这里的图例（实框＝module、虚线＝seam、红箭头＝leakage、深色粗框＝deep module）移到 `## Diagrams` 末尾，改成固定画法，见下面 `## Diagrams` 那条。上游改图例内容 → 收它要标的那几样东西，放进 `## Diagrams` |
| `## Candidate card` 里的颜色与字体 | 推荐强度标签的 emerald／amber／slate 换成 `diagram-design` 的 `accent`／`ink`／`muted`；ADR 提示框的 amber 换成 `accent-tint`；Files 列表去掉 Tailwind 的类名。上游改这几处颜色 → 仍用 `diagram-design` 的颜色角色 |
| `## Candidate card` 末段（`The reader knows nothing about this topic.` 起） | 替掉上游的 `No paragraphs of explanation. If the diagram needs a paragraph to be understood, redraw the diagram.`。上游那句只限篇幅，读者仍默认懂代码；我们这段定读者（一无所知）和图、字的分工：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。上游那句的「重画」要求已含在最后一句里。同一段也在 `teach/SKILL.md` 的 `## Lessons` 与 `wait-what/VISUAL.md` 的 `## Draw the page`，改一处，三处一起改。上游改那句措辞 → 仍用我们的这段 |
| `## Diagrams` | 我们的，接替上游 `## Diagram patterns`。图型列表：上游五种图的用意（依赖乱麻、往返次数、层层转手、调用树收拢、接口与实现一样宽）各对到 `diagram-design` 的一种图型，另加一条「同一份规则或词表被手抄进几个 module」；上游的 mass diagram（两个矩形比高度）`diagram-design` 没有，用 Nested 表达。尺寸：改前改后用同一个 `viewBox`、按栏宽缩放，因为 `diagram-design` 模板给 svg 定了 900px 最小宽度，两栏并排放不下。固定画法：module 用 Backend / API / Step 节点、deep module 用 Focal 节点、seam 是 `muted` 虚线、leakage 是实线 `accent` 连线；强调色在改前图给 leakage、在改后图给 deep module，压过各图型 reference 自己的强调色分配，但每张图最多两处强调色的上限不变；Sequence 里经由返回值的泄漏保持该图型的虚线返回线，只改成 `accent`（Sequence 规定返回线不许实线）。图宽约 560：`diagram-design` 的尺寸预设最窄 960，放进半页宽的栏里 12px 字会缩到约 7px。`diagram-design` 本身没有 seam 和 leakage 的画法，不写死的话每次运行各画各的，还会撞上图型自己的规定（Dependency graph 把强调色留给环，Sequence 的返回线是虚线）。上游加新的图式 → 收它的用意，对到 `diagram-design` 最近的图型 |
| 三处点 `codebase-design` 的地方（`## Candidate card` 的 `the glossary terms (from the …)`、`## Tone` 的 `come straight from the …` 与末段的 `If a term isn't in the … glossary`） | host 中立：技能名写成散文形式，不写斜杠。`## Tone` 的 `**Never substitute:**` 一行没改——它每一项都自带 `(for …)` 的范围限定，已经只管设计散文。共同理由见 [README.md](README.md#host-中立) |

### docs/engineering/improve-codebase-architecture.md

上游这份说明页的 `## Common questions` 里有一问「The report opened as unstyled raw HTML with no diagrams」，讲 CDN 被拦时报告变成无样式纯文本。报告不再从 CDN 加载任何东西，这一问删掉。上游改这一问 → 仍删。

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 保留，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
