# domain-modeling

## 定稿（主 agent 复核）

**判断**：技能正文与上游一字不差，不改。要改的在本仓自己的词表文档里。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `CONTEXT-MAP.md`，接在合并过来的格式说明（D1）之后 | What is written here is acted on, not just read: specs and tickets take their wording from these entries, a night worker names code after them with no one to ask, and review holds a diff to them. So write a definition only once the user has settled it or its `_Home_` bears it out, and put a word under `_Avoid_` only when it is actually wrong in this repository's text: every word listed there becomes a correction someone will make. | 有真实教训：9 月 23 日的复审发现多条 `_Avoid_` 禁掉了既有术语，还登记了约 20 个没人用的自造词条目。有了这句，写词表的 agent 知道每一条都会被当作规则执行。 |

### 删除

| # | 位置 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 六份 `docs/contexts/*/CONTEXT.md` 第 5 行逐字相同的格式说明（每份 116 词） | 只在 `CONTEXT-MAP.md` 留一份；保住 `_Home_` 行的说明（上游格式模板没有这一行） | 读任何一份 context 都先经过 `CONTEXT-MAP.md`。 |
| D2 | `mmw-v2/merge-notes/domain-modeling.md` | 缩成一行，只留"为什么不改上游 ADR 模板" | 记录的是一个没被改过的技能，其余三行都等于 README 的默认规则。 |

## 结论

技能正文三份文件共约 1,260 词（`SKILL.md` 493、`CONTEXT-FORMAT.md` 335、`ADR-FORMAT.md` 432，`wc -w`，含代码块），没有脚本。它与上游 mattpocock/skills `c55ee460` 逐字节相同：`git diff 5b1a4c51:skills/engineering/domain-modeling HEAD:mmw-v2/upstream/skills/engineering/domain-modeling` 输出为空；本仓唯一一次改动（commit `9766d7f7`，删掉"用 readable-docs 写并跑 claim check"那半句）是把正文改回上游原样。所以技能正文本身没有可删的，灵魂完整（主动建模、词表只是词表、ADR 三条门槛、与代码对质，四样都在）。本仓为它加的东西都在正文之外：`docs/agents/domain.md`、`CONTEXT-MAP.md`、六份 `docs/contexts/*/CONTEXT.md` 的格式说明段、`docs/adr/README.md` 的 ADR 形状，以及 merge-note。这些地方有重复：六份 `CONTEXT.md` 里同一段 116 词的格式说明逐字相同，`domain.md` 里有一棵与技能正文重复的通用目录树，还有一段与 `CONTEXT-MAP.md` 近乎逐字相同的设计理由。估计在不丢功能的前提下可删约 650 到 700 词，全部在本仓文档里，技能正文 0 词。上游原文与本仓约定之间有三处真实分歧（ADR 形状、`_Home_` 行、ADR 索引），我查了 31 份 ADR 和 6 份 context，没有找到其中任何一处让 agent 实际做错的证据，现有的连接文字已经接住了它们。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `docs/contexts/{toolbox,tickets,ticket-run,night,ui-acceptance,task-board}/CONTEXT.md` 第 5 行，`How to read an entry: the bold line is the term's name…` | 6 冗余 | 六份逐字相同（`md5` 都是 `5c382730…`，每份 116 词，合计 696 词）。`CONTEXT-MAP.md` 开头一段已写了其中核心一句（`its _Home_ line names the file that states the fact, and that file is right when the two disagree`） | 把这一段完整放进 `CONTEXT-MAP.md` 开头，与那句合并，只存一份。读 context 的每条路都先经过地图：`implement` `SKILL.md` 第 20 行（"the `CONTEXT.md` of each context `CONTEXT-MAP.md` lists"）、`code-review` `references/standards-reviewer.md` 第 15 行、本技能 `CONTEXT-FORMAT.md` `## Single vs multi-context repos`（"If `CONTEXT-MAP.md` exists, read it to find contexts"）、根 `AGENTS.md` `## External References`（"`CONTEXT-MAP.md`, then `docs/contexts/<name>/CONTEXT.md`"）。剩余风险：绕过地图、按路径直接打开某份 context 的 agent 看不到格式说明，但 `_Avoid_` 与 `_Home_` 两个标记名字本身已能读懂，最要紧的"`_Home_` 为准"在地图第一段 | 删六份，只在 `CONTEXT-MAP.md` 留一份。注意这一段接住了上游 `CONTEXT-FORMAT.md` 模板里没有 `_Home_` 这一分歧（见下文"上游原文"第 2 条），合并时不能丢 |
| 2 | `docs/agents/domain.md` `## File structure` 的前半：`Single-context repo (most repos):` 那棵通用树，加 `Multi-context repo (presence of CONTEXT-MAP.md at the root): the map names…` 那一句 | 6 冗余，兼 2 | 这是 `setup-matt-pocock-skills/domain.md` 种子的通用内容，与本技能 `SKILL.md` `## File structure` 的两棵树、`CONTEXT-FORMAT.md` `## Single vs multi-context repos` 说的是同一件事；而 `domain.md` 只服务本仓，本仓是多 context，单 context 那棵树对它的读者没有用 | 写 context 的 agent 由技能正文的树承担；读本仓的 agent 由同一节后半 `This repository is multi-context…` 那棵本仓树承担。无剩余风险 | 删前半，从 `This repository is multi-context` 起留（约 70 词） |
| 3 | `docs/agents/domain.md` `## File structure` 末段 `The contexts live under docs/contexts/ rather than beside their code because…` | 6 冗余 | 与 `CONTEXT-MAP.md` 第一段后半（`The contexts live under docs/contexts/ rather than beside their code because the code of most of them is a skill directory symlinked whole into every host…`）近乎逐字相同 | 留 `CONTEXT-MAP.md` 那份：新增 context 的 agent 按 `CONTEXT-FORMAT.md` 先读地图，那是它决定把新 `CONTEXT.md` 放哪的时刻；这条理由阻止它照上游"放在代码旁边"做（属于 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` "These stay" 里"keep a design choice it would otherwise simplify away"那一类，所以留一份，不全删）。剩余风险无 | 删 `domain.md` 那段（约 60 词） |
| 4 | `docs/agents/domain.md` `## Before exploring, read these` 第 8、9 行两处本仓补句：`In this repository the map is the root CONTEXT-MAP.md and the contexts it points at are docs/contexts/<name>/CONTEXT.md.` 与 `this repository keeps every ADR system-wide in docs/adr/.` | 6 冗余 | 同一文件 20 行以下的本仓树逐项标注了同样两件事（`← every ADR, all of them system-wide`、`docs/contexts/<name>/CONTEXT.md` 六行） | 由同文件那棵树承担；无剩余风险 | 二选一。建议留这两句（读者在"开工前先读"那一刻就看到），把树缩成只列地图、`docs/adr/`、`docs/contexts/` 三行（约 30 词）。收益小，可不做 |
| 5 | `docs/agents/domain.md` 第 11 行括号 `(reached via grill-with-docs and improve-codebase-architecture)` | 2 不需要知道（且在本仓不准确） | 本仓里还会拉起本技能的有 `wayfinder` `SKILL.md` 第 78、110、123 行和 `triage` `SKILL.md` 第 78 行；本技能 description 也在"writing or editing a CONTEXT.md"时直接触发。这句话从种子照抄而来 | 删掉后读者只少一个不完整的列表；句子其余部分（"creates them lazily when terms or decisions actually get resolved"）照旧成立 | 删括号（6 词）。上游种子 `setup-matt-pocock-skills/domain.md` 第 11 行同样写法，不动 |
| 6 | `mmw-v2/merge-notes/domain-modeling.md` 全文三行（141 词） | 6 冗余 | 技能正文与上游完全相同（见结论），三行都写"文件本身没改……上游改 → 收上游"，而这正是 `mmw-v2/merge-notes/README.md` `## 上游更新时怎么用` 第 2 步的默认规则（"说明里没覆盖的段落：我们没改过，取上游"）；"本仓 ADR 形状在 `docs/adr/README.md`，连接放在 `domain.md`"这件事又在 `mmw-v2/merge-notes/setup-matt-pocock-skills.md` 第 53 行和 `docs/agents/domain.md` `## Flag ADR conflicts` 各写了一遍。第 3 行自己也写"同上一条那处残余" | 只有一样东西别处没有：为什么不直接改上游 `ADR-FORMAT.md` 去贴本仓形状（"改上游正文换来一句话，代价是每次 subtree pull 都在这一行冲突"）。缩成一行保住它。剩余风险：无 | 缩成一行，约 50 词：正文未改；本仓 ADR 形状以 `docs/adr/README.md` `## 一份 ADR 长什么样` 为准，连接在 `docs/agents/domain.md` `## Flag ADR conflicts`；不改上游模板的理由那一句。可省约 90 词 |
| 7 | `docs/adr/README.md` `## 一份 ADR 长什么样` 末行 `篇幅：0008 至 0022 在 20 到 55 行之间，多数在 26 到 39 行。` | 3 实测记录 | 这是某次对 0008–0022 量出来的数；现在有 31 份，我量了全部，都在 20 到 55 行之间 | 这行本身有用：它让 agent 不照上游 `ADR-FORMAT.md` 的 "An ADR can be a single paragraph" 写一段了事。只去掉编号范围 | 改成"篇幅在 20 到 55 行之间，多数 26 到 39 行" |

技能正文内部也有重复，按任务书对上游原文的边界，不提删改，只记录：ADR 三条门槛在 `SKILL.md` `### Offer ADRs sparingly` 和 `ADR-FORMAT.md` `## When to offer an ADR` 各写一遍；"lazily 建文件"在 `SKILL.md` `## File structure`、`CONTEXT-FORMAT.md` 末尾、`ADR-FORMAT.md` 开头各写一遍。

### 上游原文在 MMW 工作流里与本仓约定分歧的地方（单列，均不建议改）

1. **ADR 形状。** `ADR-FORMAT.md` `## Template`（一到三句，"That's it"）、`## Optional sections`（`Considered Options` 与 `Consequences` 可选，`Status` frontmatter）与 `docs/adr/README.md` `## 一份 ADR 长什么样`（`date`、`amends` frontmatter 必需，两节必需，不写 `status`）相反。接住它的是根 `AGENTS.md` `## External References`（"ADR shape, the index…" → `docs/adr/README.md`）和 `docs/agents/domain.md` `## Flag ADR conflicts` 第一句。实际证据：31 份 ADR 全都以 frontmatter 开头，全都有 `## Considered Options` 和 `## Consequences`，没有一份写 `status:` 或 `## Decision`。没有触发过，不改。
2. **`_Home_` 行。** `CONTEXT-FORMAT.md` `## Structure` 的模板没有 `_Home_`，本仓 284 条词条每条都有。接住它的是每份 context 自己的格式说明段（A1 建议把它并进地图，并进去之后由地图接）。没有找到漏写 `_Home_` 的词条（六份文件里词条数与 `_Home_` 行数相等：58/8/60/66/39/53）。
3. **ADR 索引。** `ADR-FORMAT.md` `## Numbering` 只说"取最大号加一"，没说要在 `docs/adr/README.md` 的索引表加一行，也没说要回填旧 ADR 的"被哪几份改写"一格。按 `git log --diff-filter=A` 查，0012、0017、0021 三份是在没碰 `README.md` 的提交里加进来的，但索引现在是全的（31 行）。由 `docs/adr/README.md` 第一句"新增 ADR 时追加一行"接住，不改。
4. **"totally devoid of implementation details"**（`SKILL.md` `### Update CONTEXT.md inline`）。本仓的词条大量用脚本名、事件名做术语。这里不矛盾：本仓的领域就是这套工具，`docs/contexts/toolbox/CONTEXT.md` 格式说明段已写明"a term that is a literal string in a file, a command or a comment is named by that string exactly"。没有找到误删或拒写的证据。
5. **向用户发问的几个动作**（`### Challenge against the glossary`、`### Sharpen fuzzy language` 的 "Which is it?"）与用户全局提示词 `mmw-v2/prompt/shared.md`（即 `~/.claude/CLAUDE.md`）第 1 条"如何命名模块归 agent 定"有张力。那份提示词对所有宿主生效，并且自称优先于默认行为，冲突已有裁决，不需要再加文字。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头段 `Actively build and sharpen the project's domain model as you design…` 连同括号里 `Merely *reading* CONTEXT.md … is not this skill`：它区分"改模型"与"用模型"，告诉 agent 这个技能的责任是打断对话、当场逼出精确的词，而不是事后整理词表。
- `SKILL.md` `### Update CONTEXT.md inline` 第二段 `CONTEXT.md should be totally devoid of implementation details … It is a glossary and nothing else.`：上游文档 `mmw-v2/upstream/docs/engineering/domain-modeling.md` `## Two artifacts, two bars` 说这是这个技能在实际使用中被报告最多的失败（`CONTEXT.md` 变成持续增长的 spec），这一句就是防它的。
- `SKILL.md` `### Cross-reference with code`：让词汇与代码当场对齐，这是本技能区别于"写词表"的地方。
- `SKILL.md` `### Offer ADRs sparingly` 的三条门槛，以及 `ADR-FORMAT.md` `## When to offer an ADR` 那句解释 `If a decision is easy to reverse, skip it: you'll just reverse it…`：门槛本身是判断标准，解释句给了每条门槛背后的理由，让 agent 在清单外的情况也能判断。
- `ADR-FORMAT.md` `### What qualifies` 里 `The explicit no-s are as valuable as the yes-s` 与 `These stop the next engineer from "fixing" something that was deliberate`：说明 ADR 是写给未来会想"修掉它"的人看的。
- `ADR-FORMAT.md` `## Template` 的 `The value is in recording *that* a decision was made and *why*, not in filling out sections.`：本仓的 ADR 形状比上游长，但这句的意思仍然适用，本仓那两节必需的节也是为"why"服务的。
- `CONTEXT-FORMAT.md` `## Rules` 的 `Be opinionated`、`Define what it IS, not what it does`，以及 `Before adding a term, ask: is this a concept unique to this context…` 那个自问：它们是决定一条词条写不写、怎么写的判断点。
- `docs/agents/domain.md` `## Use the vocabulary in CONTEXT.md` 里 `rewrite the entry from what that file says now, never from memory of what the term used to mean` 和 `So an entry saying less than its _Home_ is not a defect; saying more is.`：这是本仓给上游模板补的判断标准，防止词表变成凭记忆写的、自称权威的说法；记忆库里有两条 review 就是按这两句判的（"词条 _Home_ 与 out-of-scope skill 不一致时加第二份 Home"、"DESIGN.md 词条 _Home_ 指 ADR 0029"）。
- `docs/agents/domain.md` 同节 `If the concept you need isn't in CONTEXT.md yet, that's a signal — either you're inventing language…`：告诉读者缺词是信号，不是自己造词的许可。
- `CONTEXT-MAP.md` 第一段 `A term is defined in one of them; its _Home_ line names the file that states the fact, and that file is right when the two disagree.`：本仓整套词表可信，靠的就是这条优先级。

### 缺口与补充草稿

技能正文的灵魂是完整的，对上游原文我不提补充。本仓特有的一点，技能正文和它的连接文字都没说清：本仓的词表会被照着执行，不只是被读。读它的人是 `to-spec` `SKILL.md` 第 20 行、`to-tickets` `SKILL.md` 第 24 行（票的标题和正文用词表的词）、`implement` `SKILL.md` 第 20 行（夜里的 worker 按词表命名，无法回头问人），以及 `code-review` 的 standards 轴。一个在访谈里随手写进去的定义，或一个过宽的 `_Avoid_` 词，第二天会变成一批票里的命名和一批 review 意见。上游文档 `## Common questions` 的最后一个问题里有同样的意思（"an unreviewed, agent-authored glossary is worse than none: it becomes confident-sounding lore that later sessions treat as truth"），但它不在 agent 加载的文件里。

- 位置：`CONTEXT-MAP.md` 第一段之后（不放进上游正文，免得每次 subtree pull 冲突；地图是写词条的 agent 按 `CONTEXT-FORMAT.md` 必读的那一份）。缺了它，agent 会把 `_Avoid_` 当作文风偏好随手加词，或者把访谈中没定下来的说法写成定义。这段话的作用是让它在加 `_Avoid_` 词、写定义之前，先对照 `_Home_` 核实，并想一想下游会怎么用。收益中等偏小，因为 `_Home_` 规则已经挡住了大部分情况；用户可以决定不加。
  > What is written here is acted on, not just read. Specs and tickets take their wording from these entries, a night worker names code after them without anyone to ask, and review holds a diff to them. So write a definition only once the user has settled it or its `_Home_` bears it out, and put a word under `_Avoid_` only when it is actually wrong in this repository's text: every word listed there becomes a correction someone will make.

## C. 死板的流程

技能正文里没有死板的流程。`### Offer ADRs sparingly` 的编号列表是三条判断门槛，不是操作步骤；`ADR-FORMAT.md` `## Numbering` 是一件确定性的小事，一句话写完。

`docs/adr/README.md` `## 一份 ADR 长什么样` 是一份六步的固定模板，我看过后判断不算过度死板：第 2、3 步（"决定本身就写在 `# ` 标题里"、"标题加下一段就是决定"）是下游读取所依赖的格式，`implement` `SKILL.md` 第 20 行按 "an ADR's decision in the untitled paragraph under its title" 去读；第 5、6 步两节必需是用户定下的本仓写法（与上游相反，merge-note 有记录），不重开。0 条。

## 脚本

无。

## 与其他技能的重复或交接问题

- `docs/agents/domain.md` 是 `setup-matt-pocock-skills` 的种子 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/domain.md` 在本仓的改写版，A2 到 A5 改的是这份本仓文件，种子不动。本轮如有人审 `setup-matt-pocock-skills`，这几条以本报告为准，不要重复提。
- "本仓 ADR 照 `docs/adr/README.md` 写"这一连接写了三处：`docs/agents/domain.md` `## Flag ADR conflicts`（agent 的读取路径上，留）、`mmw-v2/merge-notes/setup-matt-pocock-skills.md` 第 53 行（维护者读，留，因为它记的是种子里没有的那一句）、`mmw-v2/merge-notes/domain-modeling.md`（按 A6 缩成一行）。
- 调用方都按"read the `grilling` and `domain-modeling` skills' `SKILL.md`"来点名本技能（`grill-with-docs`、`triage`、`wayfinder`、`improve-codebase-architecture`），写法统一，交接没问题。上游文档 `## When to reach for it` 记录了一个已知问题：模型常常只加载 `grilling`、漏掉本技能。本仓没有找到发生过的证据，也没有加守卫，这是合理的。

## 没查到的

- 没有找到本技能在本仓真实会话中被加载的记录（没翻 `~/.claude/projects` 下的会话日志）。所以"漏加载"和"夜间 worker 编辑 `CONTEXT.md` 时被 description 触发、按技能去向不在场的用户发问"这两种情况，我只能说既没见过触发，也没见过没触发，都是推断。
- 0009、0013 两份 ADR 用 `git log --diff-filter=A` 查不到新增提交（多半是改名过来的），它们新增时有没有同时改索引，没查。
- 用户全局提示词 `mmw-v2/prompt/shared.md` 只核对了它就是 `~/.claude/CLAUDE.md` 这份内容；它通过 `render.py` 生成的其他宿主 AGENTS.md 里是否逐字包含第 1 条，没有打开核对。
- 六份 `CONTEXT.md` 的词条正文没有逐条读，只统计了词条数和 `_Home_` 行数。
