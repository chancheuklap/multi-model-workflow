# prototype

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能已经很精简。开头的 "A prototype is **code that answers a question**…The question decides the shape"、第 18 行"选错分支会浪费整个原型"，以及各条规则后面跟的理由，都是好的判断句。唯一值得补的一处有真实证据：原型目录里的 leaf `README.md` 会被 spec 引用、被 ticket 照抄精确值、被夜里的 worker 当成定论照做，而技能没说这一点。本仓任务板那几份 README 因此只写了一个"见 #546 评论"的指针。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 规则 6，接在 "Write the verdict and the question it settled into the leaf `README.md`," 所在句之后 | The leaf `README.md` outlives this session and is read by people who were not in it: a spec cites it as the source of a decision, a ticket copies its exact values, and a worker builds from its verdict at night with no one to ask. So the verdict states what was decided, with the exact names and values, and what was tried and ruled out, and why; a pointer to where the decision is discussed is not a verdict. | 写 README 时：没有它，agent 会写成给自己看的备忘（"B 赢了"），或者只放一个指向 tracker 评论的链接；有了它，会写下精确的值和排除理由。证据：`prototypes/task-board/546/UI/README.md` 到 `551` 只写了"决定的细节写在 #546 的解决评论里"，而 worker 按 **Read first** 只读 README。没有查到 worker 因此做错的实例，这一点是推断；但下游读者是谁，有 `to-tickets` 第 53 行与 `docs/contexts/tickets/CONTEXT.md` 的 **baseline** 条目为据。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | 规则 1 "On the main branch, stop and ask for a task branch first." | 删；`mmw-v2/merge-notes/prototype.md` 对应一行同步 | 上游"不进 main"的前提是原型最后推到临时分支；本仓的原型按设计长期留在默认分支的 `prototypes/` 下（`d22d15b5` 就落在 `dev` 上），前提已经不成立，也没找到它拦下过什么的记录。规则里的 "main" 在本仓指 `main` 还是 `dev` 也说不清。 |
| D2 | `UI.md` `### When there is no app yet` 末句 "so there is no scaffolding to take down after the first pull of the design." | 删这半句，保留 "Nothing outside the leaf directory mounts them." | 拆除脚手架是 `design-pages` `pull.md` 的事，那里已写。 |
| D3 | `UI.md` `## Next` "… whose first pull takes the scaffolding down." | 只留出口："… its winner goes into Claude Design through the `design-pages` skill." | 拆除时机在 `UI.md` 里写了三遍，对 UI agent 有行动意义的只有第 6 步"先别拆"。 |
| D4 | `EXP.md` 第 3 步末句 "No tests on either side: those come when the real code lands." | 删；merge-note 同步 | `SKILL.md` 规则 4 已写，agent 必先读过。 |
| D5 | `EXP.md` 第 4 步 "A 'what to look for' note per section is fine." | 删 | `evidence-page.md` 有完整的一段，写生成器时会读到。 |
| D6 | `evidence-page.md` `## Presentation` "Numbers in tables: font-variant-numeric: tabular-nums, right-aligned." | 删 | 同文件骨架 CSS 已写。 |

### 连带改动

- `write-screen-contract` 的 `## Inputs` 提到 "a logic prototype's contract file"，而 `LOGIC.md` 没有这种产物；已在 `write-screen-contract` 定稿 D8 处理。

### 不采纳

- 调查员的第二段补句（"A prototype puts a decision in front of the person who owns it…"）：`UI.md` 已写 "The user flips … and picks one"，在 wayfinder 里原型票又是 HITL；没有查到 agent 替用户定胜负的实例。
- A7（缩短规则 2 里 logic demo 的交付说明）：merge-note 说这句是刻意改的，省的词很少。

## 结论

体量：`mmw-v2/upstream/skills/engineering/prototype/` 正文五个文件共约 4,550 词（`SKILL.md` 727、`LOGIC.md` 1,093、`UI.md` 1,394、`EXP.md` 891、`evidence-page.md` 448），另有 10 词的 `agents/openai.yaml`；没有脚本。本仓自写部分约 2,150 词：对上游 `SKILL.md`、`LOGIC.md`、`UI.md` 的改动净增约 810 词（对照 `5b1a4c51` 这次 squash 的上游树），加上整份都是本仓写的 `EXP.md` 和 `evidence-page.md`。

这个技能已经很精简。本仓加的内容大多是 MMW 工作流的衔接：leaf directory 的存放约定被三个技能引用，`## State list` 被 `pull_design.py` 解析，另有交给 `design-pages` 的出口。能删的只有几处同一意思写了两三遍的句子和一条理由已经失效的停止规则，合计约 70 词，不丢功能。

"灵魂"基本完整：上游原文里讲意义和态度的句子都在，本仓加的 `EXP.md` 也写了为什么要设 bar、为什么证据页只写事实。缺的是一件事：技能从没告诉 agent，leaf `README.md` 会被谁读、按什么用。实际上 spec 引用它，ticket 从它复制精确值，worker 夜里按它的结论施工、身边没有人可问。补这一句大约 60 到 90 词，删减和补充相抵，总量基本不变。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `SKILL.md` `## Rules that apply to every branch` 规则 1：`On the main branch, stop and ask for a task branch first.` | 5（也可算 2） | 这条是 758016b2 加的，merge-note `prototype.md` 规则 1 那一行只写了"main 上先停"，没写理由。上游"不进 main"的前提是 prototype 最后推到 throwaway branch、main 只留决定，而本仓已经把这个前提废了：prototype 按设计长期留在默认分支的 `prototypes/` 下。实际使用中，`d22d15b5 prototypes(#553)` 就直接落在 `dev` 的 first-parent 上（这个仓库的工作分支是 `dev`，规则里的"main branch"指哪一个，文字没说清楚）。在 tracker、git 历史、Nowledge Mem 里都没找到这条规则拦下过什么的记录。 | 开分支本来就由宿主自己的 git 规则管，例如 Claude Code 的 "If on the default branch, branch first"，夜里的 `dispatch.sh check` 也会拒绝从 main 直接切出的功能分支。剩余风险：子形态 A 会改一个真实路由文件来挂 mount point。不过切换条已经按 production 门控（`UI.md` 第 4 步 `Hidden in production builds`），第一次 pull 之后 scaffolding 会被拆掉。 | 删掉这一句。如果用户确实想留，就补一句理由（例如 "the mount point edits a real route"），并写明"main"指哪个分支。 |
| A2 | `UI.md` `### When there is no app yet` 末句：`Nothing outside the leaf directory mounts them, so there is no scaffolding to take down after the first pull of the design.` | 2、6 | 拆 scaffolding 是 `design-pages` `references/pull.md` `## After the first pull` 的事，那一节已经写了 `A prototype built with no app yet has none.`。merge-note 自己也说 UI prototype 的 agent "从不执行它"。 | 由 `pull.md` 那一句承担。剩余风险：无。 | 保留 `Nothing outside the leaf directory mounts them.`，删掉 `so there is no scaffolding …` 这半句。 |
| A3 | `UI.md` `## Next`：`… whose first pull takes the scaffolding down.` | 6 | 拆除的时机在 `UI.md` 里写了三遍：第 3 步末段（`it comes down after the first pull of the design (the design-pages skill)`）、第 6 步第二段（`leave the scaffolding up until the first pull`）、`## Next`。对 UI agent 来说，有行动意义的只有第 6 步那句"别拆"。 | 由第 6 步第二段和第 3 步给 scaffolding 下定义的那句承担。剩余风险：无。 | `## Next` 只留出口：`… its winner goes into Claude Design through the design-pages skill.` |
| A4 | `EXP.md` `### 3. Draw the boundary around the reusable part` 末句：`No tests on either side: those come when the real code lands.` | 6 | `SKILL.md` 规则 4 已经写了 `No tests: those are written when the real code lands, never here.`，而 agent 读到 `EXP.md` 之前必定先读过 `SKILL.md`。merge-note `### EXP.md、evidence-page.md` 自己也用"再列一遍只是多一份要同步的副本"的理由，把 no-tests 从反模式里拿掉了。 | 由 `SKILL.md` 规则 4 承担。剩余风险：无。 | 删掉这一句，同步改 merge-note 那一段的措辞（它现在把这句当作 no-tests 的出处之一）。 |
| A5 | `EXP.md` `### 4.` 的 `**Facts only**` 条：`A "what to look for" note per section is fine.` | 6 | `evidence-page.md` `## Sections, in order` 之后已经写了 `A section may open with a one-line what to look for note. It points the eye; it does not state the result.`，而且那一版把理由写全了。写生成器的时候，agent 按 `EXP.md` 的指引会去读 `evidence-page.md`。 | 由 `evidence-page.md` 那一段承担。剩余风险：无。 | 删掉 `EXP.md` 里这半句。 |
| A6 | `evidence-page.md` `## Presentation`：`Numbers in tables: font-variant-numeric: tabular-nums, right-aligned.` | 6 | 同一文件 `## Skeleton` 里的 CSS 已经写了 `td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}`，而文件要求 agent 把骨架"embed in the generator"。 | 由骨架 CSS 承担。剩余风险：无。 | 删掉这一条。 |
| A7 | `SKILL.md` 规则 2：`A logic demo is a single HTML file, published as a live page when the host can do that, otherwise opened by double-click.` | 6（轻） | 发布或双击这个分叉，`LOGIC.md` `### 3. Build the shareable HTML file` 第二段写得更完整，agent 真正动手时读的是那一段。 | 由 `LOGIC.md` 第 3 步承担。剩余风险：无。merge-note 说这句是刻意改的，所以只算可选项。 | 可以缩成 `A logic demo is a single HTML file ([LOGIC.md](LOGIC.md) step 3 says how it is handed over).`，也可以原样保留，省下的词很少。 |

没有报告的项（查过，结论是该留）：

- `SKILL.md` 规则 1 里 `<effort>` 的取名顺序：`design-pages` 的 `references/design-system.md`、`references/pull.md` 和 `write-screen-contract` 都指回这里，它是跨技能的约定。
- `UI.md` 第 6 步 `## State list` 的格式：`mmw-v2/skills/design-pages/scripts/pull_design.py` 的 `state_list_section` 按 `^## State list` 截取这一节，`state_list_regions` 按 `###` 取区域、按列表项开头取状态名，格式由脚本决定。
- `UI.md` `### When there is no app yet`：来自 2c6ea8b5 "walking eight workflow scenarios"，是推演出来的，不是真实事故。但正常输入走得到它（wayfinder 做全新产品），按任务书的四问不算过度防御。
- `EXP.md` README 里的 `**Legend**` 段和证据页上的 Legend 重复。但第 5 步会删掉证据页输出，之后 README 的 Rounds 里凡是提到颜色、框的地方，只能靠 README 的 Legend 读懂，所以不算冗余。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头 `A prototype is **code that answers a question**. … The question decides the shape.`：定下整件事的性质，即 prototype 是为回答一个问题而存在，不是功能的毛坯。
- `SKILL.md` `## Pick a branch` 的 `The branches produce very different artifacts, so getting this wrong wastes the whole prototype.` 以及"默认按周边代码选分支，并在顶部写明假设"：告诉 agent 这一步选错的代价，也告诉它没人可问时怎么办。
- `SKILL.md` 规则 3 `Persistence is the thing the prototype is _checking_, not something it should depend on.`：一句话讲清为什么不接数据库。
- `SKILL.md` 规则 4 `No abstractions beyond a clear boundary around the part the real code will draw on. The point is to learn something fast.`：同时给出速度优先的态度，和唯一值得认真做的那条边界。
- `SKILL.md` 规则 6 `so the next round of the same question iterates it instead of starting over`：解释本仓为什么把 prototype 留在仓库里，这是本仓和上游最大的分歧点。
- `LOGIC.md` 开头 `looks reasonable on paper but only feels wrong once you push it through real cases`，以及 `So it speaks their language, not the code's.`：讲清这个分支存在的意义，和它的读者是谁。
- `LOGIC.md` 第 1 步 `A logic prototype that answers the wrong question is pure waste`。
- `LOGIC.md` 第 2 步 `Pick whichever shape best fits the question being asked, *not* whichever is easiest to wire to a page. … useful past its own lifetime`。
- `LOGIC.md` 第 4 步 `those are the bugs in the _idea_, which is the whole point`：告诉 agent 该看重哪种反馈。
- `UI.md` `## Two sub-shapes` 的 `butting up against the rest of the app … A prototype route on its own is a vacuum`：讲清为什么优先子形态 A。
- `UI.md` 第 2 步 `Three slightly-tweaked card grids isn't a UI prototype, it's wallpaper.`
- `UI.md` 第 5 步 `"I want the header from B with the sidebar from C", which is the actual design they want`。
- `UI.md` 第 6 步第二段 `the winner running behind it is the reference the pages are drawn against`：`SKILL-SET-REVIEW.md` `### Redundancy and bloat` 点名这句是"trimming pass reads them as noise"但必须留的例子。
- `UI.md` 第 6 步 `scene prop values reuse these names; the pull report and any decision ticket that will change a page's states match against them`：解释为什么状态名要一字不差，这是下游核对的依据。
- `EXP.md` 开头 `reads fine in the docs but only becomes clear once real code calls it with real inputs`，以及第 1 步 `An experiment without a bar answers nothing; it just runs.`：这是 EXP 分支的核心，和用户"先实测、后承诺"的一贯立场一致（Nowledge Mem"从零讨论不带预设"那条）。
- `EXP.md` `## The README` 的 `the experiment's memory across rounds`，以及 `**Conclusion**` 的 `rewritten, not appended`。
- `EXP.md` 第 4 步 `generated by the experiment's own code, so it always matches the run it came from`、`Facts only … the README.md, which outlives the page`、`the thing the docs got wrong. Facts, as observed, not conclusions yet.`
- `evidence-page.md` 的 `No verdict column: the page reports, the README.md judges.`、`How it decided … so a reader can map what they see back to code`、`Long sample names are kept … they are how the user recognises the sample`、`It points the eye; it does not state the result.`

### 缺口与补充草稿

- `SKILL.md` 规则 6（或者紧跟规则列表的一小段）。缺的是：leaf `README.md` 的下游读者是谁。技能只说"write the verdict and the question it settled"。但在 MMW 里：`to-spec` 把 prototype 路径当作决定的出处引用；`to-tickets` 第 53 行要求 ticket 从"the chosen prototype artifact"复制精确值；`docs/contexts/tickets/CONTEXT.md` 的 **baseline** 条目把"a prototype's chosen artifact"列为 worker "follows rather than consults"的定论；`docs/contexts/ui-acceptance/CONTEXT.md` 的 **leaf directory** 条目写明 README "is read to its verdict as a `## Read first` item"。一个 agent 不知道这些，写出来的 README 就可能只是给自己看的备忘（"B 赢了"），而下游需要的是精确的名字和值、排除了什么、为什么排除。

  实际使用有好有坏：`prototypes/code-landing/ui-gate/EXP/README.md` 和 `prototypes/board-orchestration/sidebar-events/UI/README.md` 写得完整，而 `prototypes/task-board/546/UI/README.md` 到 `551` 这几份只写了"决定的细节写在 #546 的解决评论里"，把定论推给了 tracker 评论。worker 如果只按 **Read first** 读 README，就读不到决定本身。这一点是推断：我没有查到 worker 因此做错的实例。

  > The leaf `README.md` outlives this session and is read by people who were not in it: a spec cites it as the source of a decision, a ticket copies its exact values, and a worker builds from its verdict at night with no one to ask. Write the verdict for that reader: what was decided, with the exact names and values; what was tried and ruled out, and why. A pointer to where the decision is discussed is not a verdict.

- `SKILL.md` `## Pick a branch` 之后（或 `UI.md` 第 6 步开头）。缺的是：谁来定胜负。`UI.md` 开头写了 `The user flips … and picks one`，`LOGIC.md` 第 4 步也暗含是用户在点，但全技能没有一句明说：UI 和 logic 的结论属于用户，agent 只负责把选择摆到用户面前。wayfinder 把 Prototype 票定为 HITL，并写了 `the agent never stands in for the human's side of it`，可是走 `ask-matt` 路线、没有 map 的时候，这句话不会被加载。后果是：用户不在场时，agent 可能凭自己的品味写下"B wins"，接着就进了 Claude Design。这个缺口的优先级低于上一条：`UI.md` 第 5 步已经暗示要等用户，我也没有查到出错的实例。

  > A prototype puts a decision in front of the person who owns it; it does not make it. For a UI or a logic prototype, the user picks the winner and says what feels wrong; an experiment is judged by the bar written before it ran. When the user is not there, hand the prototype over and stop; a verdict you reached on your own is an assumption, and is recorded as one.

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| — | 无 | 本仓加的结构都有原因。`EXP.md` 五步各带一行 `Done when`，这正是任务书要的"目标加完成标准"，而且五步有真实的先后依赖：先有 bar 才能跑，先跑才有证据页，先有观察才有结论。`EXP.md` README 固定六段，唯一一次真实使用（`prototypes/code-landing/ui-gate/EXP/README.md`）按它写出来清楚好读。`evidence-page.md` 的段落顺序每一项都带理由（例如 legend 必须先于它解释的标记出现）。`UI.md` 的 `## State list` 格式由 `pull_design.py` 解析，必须留。规则 1 的取名顺序是跨技能约定，必须留。上游原文里的编号步骤（UI 默认 3 个 variant、最多 5 个等）按边界不改。 | — |

## 脚本

无。这个技能没有 `scripts/`。`evidence-page.md` 的 `## Skeleton` 是让 agent 嵌进它自己生成器里的 HTML 模板，不是可执行脚本。和本技能产出相关的唯一脚本是 `design-pages` 的 `pull_design.py`，它读取 `## State list`，属于那个技能的审查范围。

## 与其他技能的重复或交接问题

- `mmw-v2/skills/write-screen-contract/SKILL.md` `## Inputs` 第二条写 `a logic prototype's contract file`，但 `LOGIC.md` 没有"contract file"这个产物，它的产物是 HTML 里的一个纯模块和 leaf `README.md`。这个词全仓只出现在这一处。应改的是 `write-screen-contract` 那一侧，改成 `a logic prototype's leaf README.md and its pure module`。
- "UI 的 winner 进 Claude Design，不直接折进真实代码"这个意思出现在 `SKILL.md` 规则 6、`UI.md` 第 6 步和 `## Next`、`ask-matt` `SKILL.md` 第 2 步和第 83 行，共五处。`ask-matt` 是路由器，需要一句概述，该留。`SKILL.md` 规则 6 那句也该留，因为 `UI.md` 第 6 步说"the way the SKILL describes"，UI agent 读规则 6 时需要这个例外。本技能内部能去的只有 A3 那一处。
- 拆 scaffolding：唯一执行方是 `design-pages` `references/pull.md` `## After the first pull`，这一点正确。本技能内部重复提及的部分见 A2、A3。
- `wayfinder` `SKILL.md` `## Ticket Types` 的 Prototype 条写 `(an outline, a rough take, a stub, or UI/logic code)`。本技能只有三个代码分支，没有"outline / rough take"的形态，EXP 分支也没被提到。wayfinder 是上游原文，记录下来，不建议改。
- `diagnosing-bugs` `SKILL.md` 第 137 行 `Throwaway prototypes deleted` 说的是调试用的临时代码，和本技能的 prototype 是两件事。它是上游原文，没有冲突，不用处理。

## 没查到的

- 没有读上游 `mmw-v2/upstream/docs/engineering/prototype.md`（上游写给人看的文档，不会被加载）。
- 没有查其他 consuming repository 里的 `prototypes/`。真实使用证据只来自本仓库的 `prototypes/`：9 个 UI、1 个 EXP、0 个 LOGIC。所以 `LOGIC.md` 里本仓加的部分（发布成在线页等）有没有被真实用过，我不知道。
- A1"从没拦下过什么"是根据没找到记录得出的推断。宿主会话记录没有全部翻查。
- B 第一条的后果（worker 因 README 只写指针而做错）是推断，没有找到实例。
