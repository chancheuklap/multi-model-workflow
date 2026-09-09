# improve-codebase-architecture

源目录：`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 末尾那句「什么时候用我」（`Use when there is spare time for upkeep rather than feature work, or when a bug turns out to have no good seam to lock it down at.`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；后半句的判据取自 `ask-matt/SKILL.md` 讲 diagnosing-bugs 那一条（post-mortem 发现没有好 seam 时交到这份技能手上）。上游改这一行 → 收上游对前半句的措辞，末句保留 |
| 第一条 bullet 的开头、`**Use CONTEXT.md vocabulary for the domain…**` 那一句、`Once the user picks a candidate` 那一步、`Side effects happen inline as decisions crystallize` 那一句，与 `**Want to explore alternative interfaces for the deepened module?**` 一条 | host 中立：要词汇的写成读那份技能的 `SKILL.md`（`grilling` 那一处用户在场，句子自己写着 `with them`，开子会话会把用户挡在外面），要并行开多个上下文的写成问本机 host 要它自己的 general-purpose subagent（design-it-twice 那一条）。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| 第一条 bullet 里那两条禁令（`Use these terms exactly …` 与 `don't drift into "component," "service," "API," or "boundary"`） | 加了范围限定：禁令只管你自己写的设计散文，已经存在的名字不动——命令名、验收判据的类别名、程序打印的字面量各自保留原名。理由是本仓库有以这两个词命名的真东西：`boundary criterion` 这一类验收判据、`drive-target` 技能的 `scripts/boundary-check.py`、判官打印的 `BOUNDARY OK <n>/<n>`，以及合同的 `component` 列；原句不带范围限定，照做的 agent 会去改一条真命令的名字。上游再动这一句 → 收上游对词汇表与三条原则的措辞，范围限定那一句必须留着。同源的一条在 [codebase-design.md](codebase-design.md) |

### HTML-REPORT.md

| 段落 | 我们的意图 |
| --- | --- |
| Candidate card 末段（`The reader knows nothing about this topic.` 起） | 替掉上游的 `No paragraphs of explanation. If the diagram needs a paragraph to be understood, redraw the diagram.`。上游那句只限篇幅，读者仍默认懂代码；我们这段定读者（一无所知）和图、字的分工：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。上游那句的「重画」要求已含在最后一句里。上游改那句措辞 → 仍用我们的这段 |
| 三处点 `codebase-design` 的地方（Diagrams 一节的 `the glossary terms (from the …)`、Prose 一节的 `come straight from the …`、末段的 `If a term isn't in the … glossary`） | host 中立：技能名写成散文形式，不写斜杠。同一份文件的 `**Never substitute:**` 一行没改——它每一项都自带 `(for …)` 的范围限定，已经只管设计散文。共同理由见 [README.md](README.md#host-中立) |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |
