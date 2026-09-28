# wayfinder

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：上游正文和当前上游逐字一致，是这一轮"灵魂"的范例，一个字不动。问题都在本仓加的 `references/interface-and-remake.md` 和第 6 步。

- 那两张界面票只有"开哪张、被谁挡"，没说它们解决什么。读者刚读过 "produce decisions, not deliverables"，可能认为这两张产出文件的票越界了。
- 两行逐字照抄的中文钉句把别的技能的内部流程抄了进来，改过三次还是过时了；它们为什么存在，理由已被删掉。
- 第 6 步判定"地图已清"比上游宽。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `references/interface-and-remake.md` `## A destination with an interface` 第一句之前 | An interface is decided in two places that never meet on their own: the user draws its look in Claude Design, and the decision tickets settle what the system does. Left apart, both are complete and the pages are wired to nothing. The two tickets below are where they meet. They produce files rather than answers, and are still decisions: the design package is the decided look, the screen contract the decided binding of each control to the backend. | 画地图的 agent 会认真对待这两张票，而不是当成越界的交付物；接线时，它知道"这个决定会不会改页面"是要认真判断的事。理由的真实来源在 merge-note（变色龙的界面因此接了空），`cb45a515` 之前正文里有半句，被当作维护者理由删掉了。 |
| I2 | 同一节，design ticket 的阻塞条件 "every decision ticket that will change a page's states" 之后 | A decision that changes what a page can show, settled after the pages are drawn, sends the user back to redraw them; one that only changes what happens behind a page does not block the design ticket. | 给出"会改变页面状态"的判据，接线时不再凭感觉。 |
| I3 | 同一节末尾 | Write two standing rules into the map's `## Notes`, which every later session reads: a ticket whose opening line names a skill is worked with that skill, whatever its type; and every decision ticket added later also blocks the alignment ticket, and blocks the design ticket too when it will change a page's states. | 功能缺口：这份 reference 只在画地图时读，之后新增决定票的会话不读它，新票不会被接成 alignment ticket 的阻塞，screen contract 可能漏掉它。唯一一次真实使用 #542 里，画地图的 agent 自己在 `## Notes` 补了一半（只有"照首行点名的技能做"，没有接线规则）。`## Notes` 是上游本来就为"每个会话都要知道的本次约定"留的位置，不改上游正文。 |
| I4 | 两行逐字中文钉句（"Its body opens with the line `用 write-screen-contract 解决：…`" 与 "`用 design-pages 解决：…`"）替换为右栏 | Each of the two opens its body, above `## Question`, with one line in the map's language naming the skill that resolves it: the `write-screen-contract` skill for the alignment ticket; the `design-pages` skill for the design ticket, whose line also says that only a session whose host has the Claude Design MCP tools can work it. Their type labels would otherwise send whoever picks them up to the wrong skill: a grilling ticket to an interview, a prototype ticket to the `prototype` skill. | 保留"首行、在 `## Question` 之上"的位置（#541 试点：放在标题下会被当普通正文）。把理由写回来（`cb45a515` 删掉的），并去掉钉句里抄来的别的技能内部流程。那段抄来的流程改过三次，#553 带的仍是作废版本。现在技能正文不再含中文，英文 tracker 的仓库也不会被贴上中文。 |
| I5 | `### Work through the map` 第 6 步 "If the **frontier** is now empty and **Not yet specified** is empty, the map is clear. On a map with an alignment ticket, clear means that ticket is closed too: …" 改为右栏（alignment ticket 那一句删掉，后半交接 `to-spec` 保留） | If no child ticket of the map is still open and **Not yet specified** is empty, the map is clear. | 原判据只看"可接的票"，别的会话认领着还没关的票不算在内；上游允许并行（"The user may run unblocked tickets in parallel"），这时 agent 会过早叫你去写 spec。改后与上游 `## Fog of war` 的 "no tickets remain" 一致，alignment ticket 的特例随之不再需要。 |
| I6 | `### Chart the map` 第 5 步，删去 "capturing its findings on a throwaway `research/<name>` branch with a context pointer from the ticket"，接为右栏（来自 `research` 定稿） | The subagent is the background agent the `research` skill asks for: it does the reading and writing itself and starts no agent of its own. Give it the ticket's question as its whole scope. It saves the file where the repository keeps research notes, posts the answer as the ticket's resolution comment with the file's path, and closes the ticket; it returns the path and the answer in three sentences, and you append each context pointer to the map's Decisions-so-far yourself, one at a time, so parallel subagents never rewrite the map body at once. | 两个真实问题：subagent 读到 `research` 第一句 "Spin up a background agent" 会再派一层（上游 issue #530 仍开着）；结果放在临时分支上，spec 引用、worker 读取时路径打不开（agentflow #592 的结论就指向一条没推送的本机分支）。唯一一次真实派发没有出错，靠的是发起的 agent 自己补写了 7 步交代，这一句把它补的内容写进技能。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `interface-and-remake.md` 同段末句 "and its leaf `README.md` carries the one state list every UI prototype ticket's winner feeds (the `prototype` skill's `UI.md` step 6)" | 删 | 画地图的 agent 不写状态清单；写它的是 `prototype` 的 `UI.md` 第 6 步，那里已写明写在 design ticket 的 leaf `README.md`。 |

### 连带改动

- `mmw-v2/merge-notes/wayfinder.md` 中 "正文只写「It is the last ticket to close」与这一行本身，不附这两条理由" 与钉句原文的记录，按 I1、I4 改写；第 6 步的条目按 I5 改写；为 I6 新加一条：删去上游第 5 步的 "throwaway `research/<name>` branch"，理由是 spec 与 worker 要读到 research 文件（agentflow #592），上游再改这一句时照此取舍。

### 不采纳

- `## A destination that remakes an existing product` 末句改为指向 `design-pages` 的 "An existing product" 那条路：调查员自己标了"去向是推断，改之前请确认"。这是一个路由声明，写错了会把 agent 引到错的流程；没有确认之前不写。

## 结论

体量：`mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 2190 词（上游原文 2000 词，本仓加 190 词），`references/interface-and-remake.md` 386 词（全是本仓写的；两句中文固定句 `wc` 只算作几个词，实际约 130 个汉字），`agents/openai.yaml` 3 行，没有脚本。本仓加的部分约 576 词，占全部文本的 22%。上游正文与当前上游 `mattpocock/skills` 主干逐字一致（2026-09-28 用 `gh api` 取回比对，无差异），上游的"灵魂"段落（开头两段、`## Plan, don't do`、`## Refer by name`、`## Fog of war`、`## Out of scope`、`## Ticket Types` 里 HITL 那句）全部完好，本仓没有碰。

主要问题不在冗余，而在本仓加的部分写法和上游相反：上游每条规则都带着"为什么"（`essential because it renders the frontier _visually_`、`issues need ids before they can reference each other`），本仓加的 reference 是一段不带理由的规则堆叠，前几轮减重（`cb45a515`、`e74e0140`）还把仅有的两条理由删了；两句中文固定句是逐字模板，已随 `design-pages` 改动重写过三次。另有两处本仓加的内容会让 agent 做错：`### Work through the map` 第 6 步用"frontier 为空"判定 map 已清，这比上游自己的判据（`no tickets remain`）弱，并行会话下会误判；reference 里的接线规则只在画地图那一次被读到，之后从迷雾里长出来的新决定票不会挡住 alignment ticket。

估计可删约 70 词加两句中文固定句，同时应补约 110 词的理由与交接文字，净体量基本不变。这个技能要的是"补魂"，不是减重。

## 本仓加的部分对照上游

| 本仓加的部分 | 与上游写法的关系 | 判断 |
| --- | --- | --- |
| frontmatter `description` 末两句、删 `disable-model-invocation` 与 `policy` | 只动触发条件 | 合规，不动 |
| `mmw:map` 标签（`## The Map` 第一句、`### Chart the map` 第 3 步） | 与上游 `wayfinder:map` 并列，一个词不多 | 合规；第 3 步括号保留（理由见 B） |
| `### The map body` 模板 `## Notes` 一行末尾的目录名 | 用上游自己的 Notes 机制承载，只加一个短语 | 合规，有真实事故依据（#541 试点报告第 3 条：目录名各起各的） |
| `### Chart the map` 第 4 步末尾指向 reference 的一句 | 按分支渐进加载，上游原文不动 | 合规 |
| `references/interface-and-remake.md` | 上游写"为什么"，这里只写"做什么"；两句中文逐字模板；与 `## Plan, don't do` 的张力（这两张票产出文件而不是决定）没有交代 | 稀释了上游写法，见 B、C |
| `### Work through the map` 第 6 步 | 交接 `to-spec` 的部分很好；但"clear"的判据比上游 `## Fog of war` 的 `no tickets remain` 弱，又为 alignment ticket 单独打了补丁 | 违背上游判据，见 A-4 |

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `references/interface-and-remake.md` `## A destination with an interface`，design ticket 的固定句后半 `按 design-pages 技能的 references/edit-pages.md 建 Claude Design 项目，…按 references/pull.md 拉回` | 6 | `design-pages/SKILL.md` `## Find your moment` 表已经按时机把 agent 分到 `edit-pages.md` / `pull.md`。这句是那张表的副本，而且会过期：`git log -p` 显示它在 `567bbc41`、`f70b9224`/`e163231c`、`1be66475` 三次随 `design-pages` 改写；实际票 #553 的首行还是已作废的版本（`design system 入口先建设计系统`） | `design-pages` 自己的路由表。无剩余风险：ticket 首行只需点名 `design-pages` 技能 | 与 C-1 一起改写 |
| 2 | 同段，alignment ticket 固定句后半 `每行 gap 都 aligned 后关票` | 6 | 与 `write-screen-contract/SKILL.md` `## Done when`（`every row's gap is aligned`）同一个完成标准 | `write-screen-contract` 的 `## Done when` | 与 C-1 一起改写 |
| 3 | 同段末句 `and its leaf README.md carries the one state list every UI prototype ticket's winner feeds (the prototype skill's UI.md step 6)` | 2、6 | 画地图的 agent 不写状态清单，读这句不改变它的任何动作。写清单的是 `prototype/UI.md` `### 6. Capture the answer`（原文已写 `On a wayfinder map it is written in the design ticket's leaf README.md`），读清单的是 `design-pages` 的 `references/edit-pages.md` 第 3 步与 `references/pull.md` 第 2 步 | `prototype/UI.md` 第 6 步。无剩余风险 | 删掉这一分句（约 25 词）；merge-note 对应条目同步 |
| 4 | `SKILL.md` `### Work through the map` 第 6 步 `If the **frontier** is now empty and **Not yet specified** is empty, the map is clear. On a map with an alignment ticket, clear means that ticket is closed too: …` | 4（为一条弱判据再加一条补丁） | frontier 在 `### Tickets` 里定义为 `the open, unblocked, unclaimed children`。别的会话认领着还没关的票（`SKILL.md` 末句明说 `The user may run unblocked tickets in parallel`），以及被它挡住的票，都不在 frontier 上，此时 frontier 为空但 map 并没有清，agent 会叫用户去跑 `to-spec`。alignment ticket 那句就是为这个漏洞中的一个特例打的补丁。上游 `## Fog of war` 的判据是 `until the way to the destination is clear and no tickets remain`。未见真实触发（#542 试点里一个会话解多张票，是 #541 规则 6 允许的偏离），但正常输入能走到 | 改后的判据本身覆盖 alignment ticket；它的完成标准在 `write-screen-contract` `## Done when` | 改为 `If no decision ticket on the map is still open and **Not yet specified** is empty, the map is clear.`，删掉 alignment ticket 那一句（约 25 词）。后半句交接 `to-spec` 保留 |

没有列入的：`### Chart the map` 第 3 步括号 `create mmw:map as docs/agents/issue-tracker.md ## Three label sets gives, when the repository lacks it`。它看起来像 no-op（`gh issue create` 缺标签会报错），但一个 agent 遇到"标签不存在"时常见的做法是去掉这个标签再建，于是 map 就不出现在任务板上（`mmw-v2/board/board_data.py` `_read_trees` 只按 `mmw:map` 列出 map）。保留。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头两段（`A loose idea has arrived…`、`The destination varies per effort…`）：定下"找路，不冲向终点"，并说明终点决定每一张票。上游原文。
- `## Plan, don't do`：`The pull to just do the work is usually the signal you've reached the edge of the map`，告诉 agent 什么时候该停手交出去。上游原文。
- `## Refer by name`：规定人读到的是名字不是编号，理由写在里面。上游原文。
- `## The Map` 第二段 `The map is an **index**, not a store…`：一个决定只存在一个地方，这决定了第 4 步怎么记结论。上游原文。
- `## Ticket Types` 首段 `the agent never stands in for the human's side of it (a grilling agent that answers its own questions has broken this)`：HITL 的底线。上游原文。
- `**Task**` 条目 `it earns its place by unblocking a decision, not by delivering the destination`：给"唯一一种做事的票"划了边界。上游原文。
- `## Fog of war` 整节与 `**Fog or ticket?**` 的判据 `whether you can state the question precisely now, _not_ whether you can answer it now`：整个技能最难的判断点。上游原文。
- `## Out of scope` 整节：范围与清晰度是两回事。上游原文。
- `### Chart the map` 第 3 步 `mmw:map` 与建标签的括号：理由见 A 表下方。本仓加的。
- `### Work through the map` 第 6 步后半 `(to-spec judges how many specs its decisions divide into)`：挡住 agent 在 wayfinder 里替 `to-spec` 分卷。本仓加的。
- 同一步 `Leave the map open: it stays this effort's index of decisions.`：`to-spec` 的 `references/several-specs.md` 还要把分卷写回 map 的 `## Specs`，map 关了这一步就没有落点。本仓加的。
- `references/interface-and-remake.md` `## A destination that remakes an existing product` 里带理由的几句：`write them finely, or a worker will move a whole old directory`、`the new flow produces them again`、`so the new screen contract and specs do not land on the old paths`、`If the product is live with paying customers, open one more decision ticket…`。每句都给了判断依据，不是空话。本仓加的。

### 缺口与补充草稿

- `references/interface-and-remake.md` `## A destination with an interface` 开头：缺"为什么要这两张票"。读这份 reference 的 agent 只知道要多开两张票，不知道它们解决什么问题，于是：(a) 它刚读过 `## Plan, don't do`（`produce decisions, not deliverables`），而这两张票产出的是文件，一个认真的 agent 可能认为它们越界；(b) 它不知道 design package 和后端决定会"各自完整、互不相接"，所以不会把"这张决定票会不会改页面"当成要认真判断的事。merge-note 里有这条理由的真实来源（`变色龙的界面因此接了空`），`cb45a515` 之前正文里也有半句（`because it is where the interface and the decisions are laid side by side`），被当作维护者理由删掉了。建议放在该节第一句之前：
  > An interface is decided in two places that never meet on their own: the user draws its look in Claude Design, and the decision tickets settle what the system does. Left apart, both are complete and the pages are wired to nothing. These two tickets are where the two meet. They produce files rather than answers, and are still decisions: the design package is the decided look, the screen contract the decided binding of every control to the backend, and the spec and every interface ticket are cut from them.

- 同一节，design ticket 的阻塞条件 `blocked by … every decision ticket that will change a page's states`：怎么判断"会改变页面状态"没有依据。补一句理由，agent 接线时就能自己判断：
  > A decision that changes what a page can show, settled after the pages are drawn, sends the user back to redraw them; one that only changes what happens behind a page does not block the design ticket.

- 同一节（写给画地图的 agent，但作用在之后每个会话）：缺交接。这份 reference 只在 `### Chart the map` 第 4 步被读到，`### Work through the map` 第 5 步（`Add newly-surfaced tickets (create-then-wire)`）的 agent 不读它，于是：(a) 之后从 `Not yet specified` 长出来的决定票不会被接成 alignment ticket 的阻塞，alignment ticket 可能在这个决定之前就被解掉，screen contract 漏掉它；(b) 接手 design/alignment ticket 的 agent 看到的是 `## Ticket Types` 的 `Always read the grilling and domain-modeling skills'`，与票首行点名的技能冲突。真实证据：#542 的 `## Notes` 里画地图的 agent 自己补了一行 `界面相关的票照票首行点名的技能做`，说明它感到了这个缺口，但只补了一半（没有接线规则）。上游本来就有承载"每个会话都要知道的本次约定"的地方（`## Notes`），用它接，不改上游正文。建议放在该节末尾：
  > Write two standing rules into the map's `## Notes`, which every later session reads: a ticket whose opening line names a skill is worked with that skill, whatever its type; and every decision ticket added later also blocks the alignment ticket, and blocks the design ticket too when it will change a page's states.

- `## A destination that remakes an existing product` 末句 `keeping the old look is not a remake`：说了"不是什么"，没说"那该走哪条路"。一个用户要"换掉内部实现、保留外观"的目的地，agent 读到这句只知道本节不适用，不知道去哪。建议改为（去向是我根据 `design-pages/references/design-system.md` `## An existing product` 的内容推断的，改之前请确认这就是本仓的意图）：
  > …keeping the old look is not a remake: that is an existing product brought into Claude Design as it stands (the `design-pages` skill's `references/design-system.md`, **An existing product**), and this section does not apply.

与 `SKILL-SET-REVIEW.md` 的冲突：`### Redundancy and bloat` 的 Sediment 表把"the maintainer's reason for a design"归到 ADR，merge-note `wayfinder.md` 也明写 `正文只写「It is the last ticket to close」与这一行本身，不附这两条理由`。上面第一、第三条草稿要恢复的正是这类理由。按任务书，这里以"灵魂"为准：这两条理由改变 agent 的接线判断和对票的理解，属于同一节"These stay"段落里的 `a reason the agent needs to decide an edge case, or to keep a design choice it would otherwise simplify away`，不是维护者理由。merge-note 对应的那一句需要一起改。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| 1 | `references/interface-and-remake.md` 两句逐字固定句 `Its body opens with the line 用 write-screen-contract 解决：…` 与 `Its body opens with the line 用 design-pages 解决：…` | 规定逐字抄一句中文，而这句的用途（让接手的人去对的技能，而不是按类型标签去访谈或做 prototype）一个字没写，前几轮把理由删了（`cb45a515` 删掉 `because its grilling type would otherwise send whoever picks it up into an interview rather than into that skill`）。后果：句子里夹带了别的技能的内部流程（A-1、A-2），每次那些技能一改就要跟着改；英文 tracker 的仓库也会被贴上中文；也违反 `SKILL-SET-REVIEW.md` `### Vocabulary` 的 `Skill text is English. Another language appears only inside a name the program uses`，没有任何脚本读这两句（全仓 `grep` 只命中 merge-note 与本文件） | 保留"首行、在 `## Question` 之上"这个位置（#541 试点报告第 1 条：放在标题下面会被当成普通正文），把内容换成目标加理由：<br>`Each of the two opens its body, above ## Question, with one line in the map's language naming the skill that resolves it: the write-screen-contract skill for the alignment ticket, the design-pages skill for the design ticket, whose line also says that only a session whose host has the Claude Design MCP tools can work it. Their type labels would otherwise send whoever picks them up to the wrong skill: a grilling ticket to an interview, a prototype ticket to the prototype skill.` |

`## A destination that remakes an existing product` 里的枚举（`those four, and the .mmw/target.json fields that name them`）看过，不算死板：每一项都对应一个会被错误保留的真实产物，且写了理由。该段来自 `2c6ea8b5` 提交信息所说的"walking eight workflow scenarios"（推演，不是真实使用；#541 试点明确 `不开 selection list ticket`），所以它从未真实触发过；但重做已有产品是正常输入能走到的路径，不符合"过度防御"前两问都是"否"的条件，保留。

## 脚本

无。技能目录只有 `SKILL.md`、`references/interface-and-remake.md` 与 `agents/openai.yaml`。map、票、阻塞、frontier 的 `gh` 命令在消费仓的 `docs/agents/issue-tracker.md` `## Wayfinding operations`，技能正文没有复述，这是对的。

## 与其他技能的重复或交接问题

- design ticket 固定句里的"须在能调用 Claude Design MCP 工具的会话里做"与 `design-pages/SKILL.md` 第 19 行 `Only a session whose host has the Claude Design MCP tools can do this skill's work` 重复。两边都留：票首行是给"挑哪个会话去接这张票"的那一刻看的，`design-pages` 那句是加载之后的拒绝。C-1 的草稿保留了这一半。
- 固定句里的 `edit-pages.md` / `pull.md` 路由：留 `design-pages` `## Find your moment` 那份，删 wayfinder 这份（A-1）。
- `每行 gap 都 aligned` 与第 6 步 `with every gap aligned`：留 `write-screen-contract` `## Done when`，删 wayfinder 的两份（A-2、A-4）。
- 状态清单的位置：留 `prototype/UI.md` `### 6. Capture the answer`，删 wayfinder 这份（A-3）。
- 交付之后谁关 map：没有任何技能写。第 6 步让 map 在交给 `to-spec` 时保持打开，这是对的；但 spec 落地之后，#542 是用户手动关的（评论 `终点（spec #555 与屏幕合同）已交付并落地`）。任务板只列打开的 map（`board_data.py` `_read_trees`），没人关的 map 会一直挂在板上。这不是 wayfinder 那一刻的事，只记录；该由收尾的一方（`dispatch` 的 `finish`，或 `to-spec` 发布最后一卷之后）认领，由主 agent 决定归属。
- `to-spec/SKILL.md` 第 16 行读 map 的 `## Specs` 一节，而 wayfinder 的 map 模板没有这一节。查过：它由 `to-spec` 的 `references/several-specs.md` 写回 map，不是断链。

## 没查到的

- 没有真实数据验证 A-4 的误判：唯一一次真实使用（#542）是单人、一次会话解多张票，没有并行认领。判据弱于上游是从定义推出来的。
- 重做分支从未真实走过，其中的判断（新旧 effort 名、删除清单）是否够用无法验证。
- "a destination with an interface"指什么，正文没定义（命令行工具、纯 API 算不算）。没有找到误用证据，没列为缺口。
- 没读上游 `mmw-v2/upstream/docs/engineering/wayfinder.md`（上游给人看的说明文档，不进 agent 的加载路径）。
- 没查 `setup-matt-pocock-skills` 的 `issue-tracker-github.md` 种子里 `## Wayfinding operations` 与本仓 `docs/agents/issue-tracker.md` 是否逐字一致；merge-note `setup-matt-pocock-skills.md` 说一致，未核对。
