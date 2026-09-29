# R20b mattpocock 的写作方式：可执行的规则

这份文件给写 R20 写作规范、写范本、写搬家票和审查搬家票的代理与人读。它回答一个问题：mattpocock 的技能文本靠哪些写法影响 agent 思考的深度与广度，每条写法怎样照着做、怎样检查、落地的 worker 最可能怎样把它毁掉。文本结构（组件类型、骨架、连线）以 pstack 为准，见 `L7-pstack-component-contract.md` 与 `R13-pstack-design-essence.md`；本文只管写法，最后一节列两者可能冲突的地方。

## 0. 出处写法与两个用词

**出处缩写**（全文只用这些）：

| 缩写 | 指什么 | 怎样打开 |
|---|---|---|
| `UP:<bucket>/<skill>/<file> L<n>` | mattpocock 上游原文，squash 提交 `5b1a4c513d027a598a277aa45892a6823381f9a9`（`git log --format=%H --grep "Squashed 'mmw-v2/upstream/'" -1` 的结果） | `git show 5b1a4c51:skills/<bucket>/<skill>/<file>`；行号是该文件自身的行号 |
| `WFA L<n>` | `UP:productivity/writing-for-agents/SKILL.md` | 同上 |
| `SM L<n>` | `UP:productivity/writing-for-agents/SKILL-MECHANICS.md` | 同上 |
| `SSR L<n>` | `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（本仓库工作树现行版本） | 直接读文件 |
| `PS:<path> L<n>` | pstack 快照 `docs/research/code-landing-refs/pstack/<path>` | 直接读文件 |

**深度**与**广度**是本文的分析用词，不是上游术语，定义来自两处原文：

- **深度**：agent 在一件事上挖多深、到什么程度才停。原文：「Demand drives **legwork** (the digging the agent does within the work, latent in the wording rather than written as its own step)」（WFA L50）；反面是 **premature completion**：「ending the step before it is genuinely done, attention slipping to _being done_」（WFA L49）。
- **广度**：agent 覆盖多少种情况，包括步骤没写到的情况，以及同时考虑多少个备选。原文：「a model given the reason carries it into cases no rule names」（SSR L11）；「Steps cover the cases their writer foresaw, and the agent meets others」（同行）。

mattpocock 对「技能控制什么」的总判断是 WFA L6：「the agent takes the same _process_ every run rather than producing the same output」。下面每条规则都服务于这句话：让过程稳定，而不是逐字规定产出。

---

## 1. 规则

每条规则写成四部分：怎样写（可执行的写法）、原文实例（至少两处）、对思考的作用、检查与常见破坏。「常见破坏」一栏是推断，依据是规则本身与 `SSR L142`「Asked to "streamline", an agent shortens and cuts function with it」。

### M1 开头交出理解：这件事为了什么、谁依赖它的产出、做浅了代价是什么

**怎样写。** 技能（或 playbook 的首段）在任何步骤之前用两到五句话说清：这项工作要达到什么，谁接着用它的产出，产出错了或浅了对那个人意味着什么。代价写成具体后果（「浪费整个原型」），不写成重要性声明（「这一步很重要」）。

**原文实例。**

- `UP:engineering/wayfinder/SKILL.md L7`：「A loose idea has arrived, too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way, not charging at the destination.」一句话给出处境、目的和要避免的反面。
- `UP:engineering/prototype/LOGIC.md L20`：「A logic prototype that answers the wrong question is pure waste, so make the question explicit so it can be checked later, whether the user is watching now or returning to it AFK.」代价与读者（稍后回来的人）都在一句里。
- `UP:engineering/prototype/SKILL.md L17`：「The two branches produce very different artifacts, so getting this wrong wastes the whole prototype.」
- `UP:engineering/triage/AGENT-BRIEF.md L3`：「It is the authoritative specification that an AFK agent will work from. The original body and discussion are context: the agent brief is the contract.」点明下游读者是谁、它把什么当依据。
- `UP:engineering/diagnosing-bugs/SKILL.md L20`：「**This is the skill.** Everything else is mechanical. If you have a **tight** pass/fail signal for the bug ... you will find the cause」，直接告诉 agent 注意力该放在哪一阶段。
- `UP:engineering/codebase-design/SKILL.md L8`：「The aim is leverage for callers, locality for maintainers, and testability for everyone.」三类受益人各配一个结果。

**对思考的作用。** 广度：目的与下游读者让 agent 在步骤没写到的情况里有依据可判断（SSR L11 事实 1）。深度：代价告诉 agent 哪里不能省（diagnosing-bugs 把「Spend disproportionate effort here」放在 L22，紧跟目的之后）。

**检查。** 用 SSR L11 的开头测试：只拿着这个技能的 agent，能不能说出这项工作为了什么、谁根据产出行动、做浅了他们付出什么；说不出来，开头就缺内容。一句只宣称重要、复述周边流水线、或者讲另一个技能的 agent 做什么的句子，按 SSR L11 是 no-op。

**常见破坏。** 被当成「背景介绍」删掉，只留步骤；或被改写成「本技能用于……」式的身份句，与 description 重复（WFA L18「Cut identity the body already carries」）。

### M2 理由写在规则旁边

**怎样写。** 一条规则后面跟一句理由，用 because、so、「X is the thing Y」这类连接，理由说的是后果或机制。只写能改变 agent 某个决定的理由：写之前说得出一个步骤没覆盖的情况，以及 agent 有了这句会在那里做得不同（SSR L11 的句子测试）。

**原文实例。**

- `UP:engineering/diagnosing-bugs/SKILL.md L82`：「Why bother: a minimal repro shrinks the hypothesis space in Phase 3 (fewer moving parts left to suspect) and becomes the clean regression test in Phase 5.」
- `UP:engineering/diagnosing-bugs/SKILL.md L90`：「Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.」
- `UP:engineering/prototype/SKILL.md L23`：「No persistence by default. State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on.」
- `UP:engineering/tdd/SKILL.md L22`：「You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.」
- `UP:engineering/code-review/SKILL.md L76` 与 `## Why two axes`（L80–87）：「Do **not** merge or rerank findings, because the two axes are deliberately separate」；整节只讲一个理由，SSR L55 与 L165 把它列为「保留」的范例：「without it the agent would merge the axes」。
- `UP:engineering/triage/OUT-OF-SCOPE.md L88`：「Do **not** write here when something is closed as `wontfix` because it's **already implemented** ... recording it would poison the dedup checks with false rejections.」
- `UP:engineering/prototype/UI.md L16`：「A throwaway route on its own is a vacuum: every variant looks fine in isolation.」这是「优先 sub-shape A」的理由。

**对思考的作用。** 广度：理由让 agent 把规则推到没列出的情况（例如 OUT-OF-SCOPE 的理由也能判断「已部分实现」时要不要写）。深度：理由防止 agent 在觉得规则多余时把它简化掉（SSR L55「a reason the agent needs ... to keep a design choice it would otherwise simplify away」）。

**检查。** 对每条理由做 SSR L11 的句子测试。理由必须能在代码、tracker、记录过的运行或用户原话里找到依据，找不到就不写：「an agent guesses around a rule stated without its reason, but it generalises from an invented one」（SSR L140）。

**常见破坏。** 按 pstack「Tell it to do the thing and skip the reason」（`PS:skills/poteto-mode/playbooks/authoring-a-skill.md L10`）把理由整句删掉；或反过来给每条规则补一句凭空编的理由。两种都破坏本规则，裁决见第 2 节冲突 C1。

### M3 立场句：点名这项工作特有的诱惑，并给出替代动作

**怎样写。** 找出这项工作里 agent 最可能滑向的错误方向，写一句话认出它，再写一句该做什么。立场句不是态度（「要仔细」），它有具体的诱惑和具体的动作（SSR L42：「A stance is not a bare attitude: it names the temptation particular to this work and what to do instead」）。

**原文实例。**

- `UP:engineering/wayfinder/SKILL.md L13`（`## Plan, don't do`）：「The pull to just do the work is usually the signal you've reached the edge of the map and it's time to hand off.」
- `UP:engineering/diagnosing-bugs/SKILL.md L66`：「If you catch yourself reading code to build a theory before this command exists, **stop: jumping straight to a hypothesis is the exact failure this skill prevents.**」
- `UP:productivity/grilling/SKILL.md L26`：「Finding _facts_ is your job, never the user's. ... The _decisions_ are the user's: put each to them and wait.」
- `UP:engineering/codebase-design/DESIGN-IT-TWICE.md L44`：「Be opinionated: the user wants a strong read, not a menu.」
- `UP:productivity/to-questionnaire/SKILL.md L9`：「**Grill the send, not the subject.**」
- `UP:engineering/wizard/SKILL.md L10`：「**Your job is only to scope the procedure and author its stages.**」

**对思考的作用。** 深度：立场句放在诱惑出现的那一刻（diagnosing-bugs 放在 Phase 1 的完成判据旁边），把 agent 拉回还没做完的工作，直接对抗 premature completion。广度：它给的是一类情况的认出方法（「the pull to just do the work」），不是一个情况的规则。

**检查。** 立场句必须同时有「诱惑」和「替代动作」；只有一半的是 no-op。模型默认就有的倾向不用写（WFA L81 no-op 测试）。

**常见破坏。** 被当成修辞删掉；或改写成泛泛的「保持专注」。

### M4 先定方向再信任：写目标、约束、判断点和完成判据，普通动作交给模型

**怎样写。** 技能写目标、约束、agent 会判断错的一两个点、完成判据；有能力的 agent 不用提示就会做的动作不写。需要 agent 按不同情况选择时，写判断的标准或一个默认值，而不是枚举每种情况。

**原文实例。**

- `UP:engineering/implement/SKILL.md L7–15`：全文五行，点名交给 `tdd`、`code-review`，其余信任 agent。SSR L14（事实 4）以它为例。
- `UP:engineering/research/SKILL.md L6–12`：三步，每步只写目标与标准（「Follow every claim back to the source that owns it」「match the existing convention, and if there is none, put it somewhere sensible and say where」）。
- `UP:engineering/improve-codebase-architecture/SKILL.md L27`：「Don't follow rigid heuristics; explore organically and note where you experience friction」，后面给五个问题引导注意力，不给检查清单。
- `UP:engineering/triage/SKILL.md L49`：「The maintainer invokes `/triage` and describes what they want in natural language. Interpret the request and act.」
- 判断点被钉死的例子：`UP:engineering/prototype/UI.md L38`「Default to **3 variants**. More than 5 stops being radically different and starts being noise, so cap there.」；`UP:engineering/prototype/SKILL.md L17` 用户不在场时按周边代码选分支并「state the assumption at the top of the prototype」。

**对思考的作用。** 广度：不枚举情况，agent 在列表外的情况里仍按目标判断；枚举会让 flow 变得 rigid 和 brittle（SSR L14）。深度：精力省下来放在被点名的判断点上。

**检查。** SSR L43 over-specification 四种形态：给能力足够的 agent 写编号流程、镜像脚本分支的 if-then 列表、一个判据就能覆盖的情况枚举、为强制一条规则加的流程。SSR L94 的反向检查：找出 agent 必须选择而文本沉默的地方（unguided choice），补判据或显式分支；任何合理模型都会同样选择的点不补。

**常见破坏。** 为「严谨」把一段目标描述展开成十几步编号流程；或把 grilling 这种以概念驱动的技能改写成步骤清单（见冲突 C2）。

### M5 判断点写成一个可检验的测试

**怎样写。** 模糊的判断（「够不够浅」「是不是该开票」）改写成一个 agent 能对自己执行、结果是二值的测试，用粗体命名，一句话说明怎样做、结果怎样读。

**原文实例。**

- `UP:engineering/codebase-design/SKILL.md L63`：「**The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.」
- `UP:engineering/wayfinder/SKILL.md L88`：「**Fog or ticket?** The test is whether you can state the question precisely now, _not_ whether you can answer it now.」
- `UP:engineering/diagnosing-bugs/SKILL.md L96`：「If you cannot state the prediction, the hypothesis is a vibe: discard or sharpen it.」
- `UP:engineering/codebase-design/SKILL.md L65`：「One adapter means a hypothetical seam. Two adapters means a real one.」
- `UP:engineering/prototype/UI.md L30`：「Before committing to sub-shape B, sanity-check: is there really no existing page this could be embedded in?」
- `WFA L70`：把「a loop you believe in」换成 _red_，「turning a fuzzy gate into a binary observable state」。

**对思考的作用。** 深度：二值测试让 agent 真的去做一次检验，而不是凭感觉放行。广度：测试不绑定具体情况，每遇到一个候选都能套用。

**检查。** 测试能不能失败：SSR L62「A check or completion criterion that cannot fail proves nothing」。

**常见破坏。** 把测试压缩成形容词（「确保模块足够深」），丢掉操作方法。

### M6 用领域术语和 leading word 锚定行为

**怎样写。** 给一类行为找一个模型预训练里已有的词（出自本领域经典的术语优先），定义一次，此后全文只用这个词，不换同义词；需要时写 `_Avoid_` 列出禁用的近义词，并注明术语的作者或出处。找不到现成词才造词，造词必须一句话定义。强度不够的词（_be thorough_）换成更强的词（_relentless_），而不是加一段解释。

**原文实例。**

- `UP:engineering/to-tickets/SKILL.md L27–40`：**tracer bullet**、**blast radius**、**expand–contract**，一个词带出一整套切分方式；SSR L171 引作范例（**tracer bullet** 出自 *The Pragmatic Programmer*）。
- `UP:engineering/wayfinder/SKILL.md L84`：**fog of war**；`L69` 的 **frontier**；`UP:productivity/grilling/SKILL.md L6–8` 的 **design tree**、**rounds**、**frontier**。
- `UP:engineering/diagnosing-bugs/SKILL.md L20`、`L47`：**tight**、**red**（「a 2-second deterministic one is tight」）；WFA L69–70 把这两个词当作 leading word 的示范。
- `UP:engineering/codebase-design/SKILL.md L12`：「Use these terms exactly: don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point.」每个术语带 `_Avoid_`，**Seam** 注明 _(Michael Feathers)_（L22）。
- `UP:engineering/improve-codebase-architecture/HTML-REPORT.md L110–112`：「**Use exactly:** ...」「**Never substitute:** ...」。
- `UP:engineering/code-review/SKILL.md L38`：smell baseline 用 Fowler《Refactoring》第 3 章的名字（Feature Envy、Shotgun Surgery……），每项「*what it is* → *how to fix*」。
- 强度词：`UP:productivity/grilling/SKILL.md L6`「Interview the user relentlessly」；`UP:engineering/diagnosing-bugs/SKILL.md L22`「**Be aggressive. Be creative. Refuse to give up.**」；WFA L81：「a word too weak to beat the default (_be thorough_ ...) is a no-op, and the fix is a stronger word (_relentless_)」。

**对思考的作用。** 广度：词会调出模型已知的整套做法（WFA L63「by recruiting priors the model already holds」），一个 **tracer bullet** 带来「每片贯穿所有层、可演示」这一整组约束。深度：同一个词每次出现，agent 都回到同一种行为（WFA L65 _execution_ 锚定），在平铺的规则里把注意力聚焦到一类要找的东西上。

**检查。** SSR L75 的选词顺序（领域既有术语 → 词典词 → 造词加粗定义）；SSR L77：比喻除非是 leading word，否则是 finding；一个词一个意思（SSR L74）。一个假朋友式的借词（字面是术语、意思不同）比造词更糟（SSR L75）。

**常见破坏。** 为「通俗」把术语换成描述性短语，或同一概念前后用三个说法（pstack `PS:skills/unslop/SKILL.md L31` rule 11 Synonym cycling 也禁止这一点）；或按反比喻规则把 **fog of war**、**tracer bullet** 当修辞删掉（见冲突 C4）。

### M7 description 只写触发

**怎样写。** 模型调用的技能：description 写「它是什么」加上加载它的各个分支，领头放 leading word，每个分支一个触发，重名同义的触发合并；可以写一条明确的非触发。用法、流程、产出、路由都写进正文。用户调用的技能：description 是一行给人看的摘要。

**原文实例。**

- `UP:engineering/diagnosing-bugs/SKILL.md L3`：「Diagnosis loop for hard bugs and performance regressions. Use when the user says "diagnose"/"debug this", or reports something broken/throwing/failing/slow.」触发用用户原话。
- `UP:engineering/wizard/SKILL.md L3`：四个触发分支加一条非触发「Don't invoke this for steps the agent can perform itself.」；SSR L161 引作范例。
- `UP:engineering/codebase-design/SKILL.md L3`：最后一个分支「or when another skill needs the deep-module vocabulary」，给别的技能调用留入口（SM L9：模型调用的技能也可以是共享 reference 的家）。
- 用户调用的一行摘要：`UP:productivity/grill-me/SKILL.md L3`「A relentless interview to sharpen a plan or design.」；`UP:productivity/to-questionnaire/SKILL.md L3`。
- 规则原文：WFA L14–18（「Front-load the leading word」「One trigger per branch」「Cut identity the body already carries」）；SM L9–12。
- 上游自己的偏离：`UP:engineering/code-review/SKILL.md L3` 的 description 带了流程（「Runs both reviews in parallel sub-agents and reports them side by side」），按 SSR L67 是 finding。这说明规则以 SSR 为准，不以任一上游文件的实际写法为准。

**对思考的作用。** 决定技能会不会被加载，也就是 agent 有没有机会得到上面所有的深度与广度；每个词在每一轮都占上下文（WFA L14），多写的流程会挤占其他技能的触发。

**检查。** SSR L67–69：只写触发；并排读全套 description，两个 description 声称同一件事是冲突；不写宿主名、runner 名。

**常见破坏。** 为「说清楚」把正文第一段搬进 description；或写三个同义触发。

### M8 按分支渐进加载，每个分支文件自成一体

**怎样写。** 每次运行都要读的内容留在 `SKILL.md`（包括每次都要填的模板）；只有某个分支才读的内容放进单独文件，在 `SKILL.md` 里用带条件的指针点名。分支文件里放齐这个分支需要的规则、格式和完成判据，并点名另一个分支，给走错的读者一个出口。一选一的选择写成表或按问题分的列表，不写成编号流程。

**原文实例。**

- `UP:engineering/prototype/SKILL.md L10–17`（`## Pick a branch`）按问题分两支；`UP:engineering/prototype/LOGIC.md L14`「If the question is "what should this look like," this is the wrong branch. Use [UI.md](UI.md).」；`UP:engineering/prototype/UI.md L5` 反向同理。SSR L162 引作范例。
- `UP:engineering/codebase-design/SKILL.md L111–114`（`## Going deeper`）：每个指针以条件开头（「**Deepening a cluster given its dependencies**, see DEEPENING.md」）。
- `WFA L8`：「When the document you're writing is a skill, read `SKILL-MECHANICS.md`」，指针即条件。
- 模板内联：`UP:engineering/to-spec/SKILL.md L21–75` 的 `<spec-template>`、`UP:productivity/to-questionnaire/SKILL.md L22–54`，每次运行都写一份，所以不拆（SSR L164）。
- 规则原文：WFA L39「Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach.」；SSR L15（事实 5）；SSR L28 fragment、L31「A pick-one-of-N choice is a table」。

**对思考的作用。** 深度：走进的分支里没有别的分支的材料分散注意力（WFA L39「turns attending to them into a coin-flip」）。广度不受损：`SKILL.md` 里的分支列表让 agent 知道所有路径存在。

**检查。** 每个 reference 是否有某次运行可以跳过；每次都读的 reference 是 fragment，内联（SSR L28）。一个步骤要打开第二个文件才能做完是 jump（SSR L27）。

**常见破坏。** 按主题而不是按分支拆文件（「规则」「格式」「示例」各一份），每次运行都要打开全部；或把分支文件的出口句删掉。

### M9 平级技能按名字组合

**怎样写。** 需要另一项能力时，点名那个技能和要它做的事，让它整份加载、按自己的规则做；不复制它的文件，不复述它的规则。只是一次调用的技能，可以整份就是一行点名。

**原文实例。**

- `UP:engineering/grill-with-docs/SKILL.md L7`：「Call the Skill tool twice, for "grilling" and "domain-modeling".」全文一行。`UP:productivity/grill-me/SKILL.md L7` 同样一行。
- `UP:engineering/implement/SKILL.md L9、L13`：「Use /tdd where possible, at pre-agreed seams.」「Once done, use /code-review to review the work.」
- `UP:engineering/tdd/SKILL.md L26`：调用 `codebase-design`「for the vocabulary ... it is a reference to consult, not a session to run」，同时说清调用的方式（查词汇，不跑一轮会话）。
- `UP:engineering/wayfinder/SKILL.md L77–80`：四种票各由一个技能解决（research、prototype、grilling + domain-modeling）。
- `UP:engineering/codebase-design/DEEPENING.md L3`：「Assumes the vocabulary in SKILL.md」，只点名，不重述。
- 规则原文：SSR L16（事实 6）、L17（事实 7）；SSR L95 在 MMW 里写成「name the skill and the job, never an install path」；SSR L118 要求不写「the Skill tool」这类宿主工具名（上游原文不改，连接文字按 MMW 规则写）。

**对思考的作用。** 广度：一项能力只在一个地方被写到最好，所有调用方都拿到同一个深度。深度：被调用的技能整份加载，它自己的立场句、判据、例子都随之生效；复述的版本通常只剩步骤。

**检查。** SSR L40 duplication：同一意思在全套里出现两次就是 finding。SSR L27：整份交给另一个技能是 hand-off，不是 jump。

**常见破坏。** 为「自足」把被调用技能的几条规则抄进调用方；抄过去的版本随后与原版分叉（SSR L17「in time contradicts it」）。

### M10 完成判据：每一步都有一个清楚且要求高的「完成」

**怎样写。** 每一步以一个 agent 能分辨做完与没做完的判据收尾，措辞要求穷尽（every、nothing left、removing any one）。判据模糊而 agent 又确实会赶进度时，才把后面的步骤藏到另一个上下文里（WFA L49 的顺序：先把判据写清，再考虑拆分）。硬闸门写成「没有 X，就不进入 Y」。MMW 自有文本以 `Done when` 开头写这一行（SSR L124）。

**原文实例。**

- `UP:engineering/diagnosing-bugs/SKILL.md L57–66`（`### Completion criterion: a tight loop that goes red`）：一条已经跑过的命令，四个可勾选条件，末尾「No red-capable command, no Phase 2.」
- `UP:engineering/diagnosing-bugs/SKILL.md L84`：「Done when **every remaining element is load-bearing**: removing any one of them makes the loop go green.」
- `UP:productivity/grilling/SKILL.md L28`：「The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed.」
- `UP:engineering/wizard/SKILL.md L25`：「**Done when:** every stage is named in order, and for each captured value you know (a) where the human gets it, (b) where it's written ..., and (c) whether it's secret」；`L31`「every stage traces to concrete instructions a stranger could follow」。
- `UP:productivity/to-questionnaire/SKILL.md L16`：「Done when the file exists and every item the user named in step 2 is covered by a question.」
- `UP:engineering/triage/AGENT-BRIEF.md L28–33`：交给下游 agent 的简报必须有「concrete, testable acceptance criteria」，并给出好坏对照。
- 规则原文：WFA L45–52（clarity、demand，「The strongest criteria are both checkable and exhaustive」）。

**对思考的作用。** 深度：要求高的判据驱动 legwork（WFA L50：「"Every modified model accounted for" forces thorough work where "produce a change list" does not」）。广度：穷尽措辞（every branch visited）要求 agent 回头扫一遍所有分支，而不是做完眼前一个就停。

**检查。** 判据能不能失败（SSR L62）；同一任务是否只有一种「完成」的说法（SSR L124）。

**常见破坏。** 改成「完成后进入下一步」这类无法失败的判据；或把穷尽词删成「列出变更」。

### M11 给子代理的简报：输入给全、任务说清、返回什么、多长

**怎样写。** 子代理只有简报。简报里：它需要的材料全文粘贴（它没有别的途径拿到）；它要回答的问题；返回的结构和长度上限。并行多个子代理时给每个一个不同的约束，让结果真正不同。会让所有子代理白跑的错误，放在派发之前检查。子代理还在跑时，只让依赖它结果的问题等待。

**原文实例。**

- `UP:engineering/code-review/SKILL.md L63`：Standards 子代理拿到「**plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it)」；`L64`、`L70` 各有一段带引号的任务，以「Under 400 words」结束，并要求每条 finding 引出处（「cite the standard (file + the rule)」「Quote the spec line for each finding」）。
- `UP:engineering/code-review/SKILL.md L23`：「A bad ref or empty diff should fail here, not inside two parallel sub-agents.」SSR L168 引作范例。
- `UP:engineering/codebase-design/DESIGN-IT-TWICE.md L21–38`：3 个以上子代理各带一个约束（「Minimize the interface」「Maximise flexibility」「Optimise for the most common caller」），简报里放两套词汇，每个子代理按同一五项结构返回。
- `UP:productivity/grilling/SKILL.md L26`：「Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report」。
- `UP:engineering/research/SKILL.md L6–12`：后台代理的简报三项：去哪里查（primary sources）、写成什么（一个 Markdown 文件，每条带出处）、放在哪。
- `UP:engineering/triage/AGENT-BRIEF.md L9–26`：给 AFK agent 的简报写接口与行为，不写路径与行号（「Durability over precision」「Behavioral, not procedural」）。
- 规则原文：SSR L100–102（「A subagent's brief states what it returns and its length」）。

**对思考的作用。** 深度：子代理的深度上限就是简报给它的材料和判据；长度上限保护调用方的注意力（SSR L102「so its report fits the caller's attention」）。广度：不同约束让并行结果覆盖设计空间的不同角落，而不是三份相似答案。

**检查。** 简报里说子代理要应用的每条规则，是粘贴进去了，还是让它加载某个技能；两者都不是就是断掉的 hand-off（SSR L101）。

**常见破坏。** 把「pasted in full」改成「参考某文件」；删掉字数上限；并行子代理用同一份简报。

### M12 容易误读的地方给成对的好坏例子

**怎样写。** 只在 agent 容易理解错的地方给例子；好例子和坏例子并排，坏例子后面写它坏在哪。例子用中性领域，不用真实产品、issue 号或过去的运行（SSR L128）。例子标明是例子，规则才是依据（SSR L129）。

**原文实例。**

- `UP:engineering/tdd/tests.md L7–76`：`// GOOD` 与 `// BAD` 成对出现，每对后面列 Characteristics 或 Red flags；「BAD: Expected value is recomputed the way the code computes it」对「GOOD: Expected value is an independent, known literal」。
- `UP:engineering/triage/AGENT-BRIEF.md L185–207`：一份坏简报，后面「This is bad because:」六条。
- `UP:engineering/triage/AGENT-BRIEF.md L23–26`：「**Good:** "The `SkillConfig` type should accept ..."」对「**Bad:** "Open src/types/skill.ts and add a schedule field on line 42"」。
- `UP:engineering/codebase-design/SKILL.md L71–95`：「// Testable」对「// Hard to test」。
- `UP:engineering/triage/OUT-OF-SCOPE.md L75`：「Matching is by concept similarity, not keyword: "night theme" matches `dark-mode.md`」，一个例子把规则的边界画出来。

**对思考的作用。** 深度：例子校准判断的边界，agent 在灰色地带知道线划在哪。广度有风险：具体例子会被当成要求（SSR L128），所以用中性领域。

**检查。** SSR L128–130。

**常见破坏。** 删掉坏例子只留好例子（失去边界）；或把例子换成本仓库的真实票，agent 把细节当需求。

### M13 禁令配正面目标和理由

**怎样写。** 先写要做的行为；禁令只用作无法正面表述的硬护栏，并且和正面目标、理由写在一起。

**原文实例。**

- 规则原文：`WFA L74`：「steering by prohibition drags the forbidden behaviour into context and makes it _more_ available ... Prompt the **positive** ... A prohibition earns its place only as a hard guardrail you cannot phrase positively; even then, pair it with the positive target」。
- `UP:engineering/tdd/SKILL.md L36`：「**Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.」正面动作在前，禁令在后。
- `UP:engineering/to-spec/SKILL.md L55–57`：「Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.」接着写例外「if a prototype produced a snippet that encodes a decision more precisely than prose can」。
- `UP:engineering/prototype/LOGIC.md L65`：「**Don't blur the logic and the page together.** If the pure module references the DOM ... it's no longer liftable. Keep the page as a thin shell over a pure module.」禁令、理由、正面目标三件齐全。
- `UP:engineering/tdd/mocking.md L3–14`：先列「Mock at **system boundaries** only」，再列「Don't mock」。

**对思考的作用。** 深度：注意力落在要做的事上。广度：理由让护栏覆盖同类情况。

**检查。** 每个 Don't / Never 旁边有没有正面目标；能不能整句改成正面表述。

**常见破坏。** 把一段解释压缩成一串「Never …」。

### M14 事实归 agent，决定归人，并写清人不在场时怎么办

**怎样写。** 能从环境查到的事实由 agent 自己查（必要时派子代理），只有人能做的决定才问人。每个需要人参与的点写明人不在场时的做法：用默认值继续、写明假设、或停下。

**原文实例。**

- `UP:productivity/grilling/SKILL.md L26`：「don't ask the user for anything you could look up yourself ... The _decisions_ are the user's」。SSR L173 引作 hand-off 范例。
- `UP:engineering/wayfinder/SKILL.md L75`：「A HITL ticket only resolves through that live exchange; the agent never stands in for the human's side of it (a grilling agent that answers its own questions has broken this).」
- `UP:engineering/diagnosing-bugs/SKILL.md L98`：「**Show the ranked list to the user before testing.** ... Don't block on it; proceed with your ranking if the user is AFK.」
- `UP:engineering/prototype/UI.md L44`：「This works whether the user is here to push back or not.」；`UP:engineering/prototype/SKILL.md L17`「If the question is genuinely ambiguous and the user isn't reachable, default to ...」。
- `UP:engineering/wizard/SKILL.md L29`：「Where you don't actually know the current UI or the exact command, say so and ask the user or check the docs: never invent steps that may not exist.」

**对思考的作用。** 深度：agent 不把查事实的工作推给人，自己挖到底。广度：同一个技能在人在场和夜间无人两种情况下都有出路。对 MMW 的夜间流水线尤其相关（推断：MMW 的 worker、reviewer 在无人会话里运行，R18 审查记录第 40 条已要求「能力技能的人工闸门在无人会话里走本角色的无人出路」）。

**检查。** 每个问人的点：问的是事实还是决定；人不在场时文本有没有给出路。

**常见破坏。** 把「proceed if AFK」删掉，技能在夜间卡住；或反过来让 agent 替人回答决定。

### M15 修剪：删 no-op、删重复、删缓存，保留交出理解的句子

**怎样写。** 逐句问：没有这句，模型的行为会不会不同。不会，就整句删。同一意思只留一个家。环境里一条命令就能查到的事实不抄进文本。交出目的、理由、立场的句子不按篇幅删，按 M1–M3 的测试判断。

**原文实例。**

- `WFA L78–81`：single source of truth、environment as cache、relevance 与 sediment、no-op 测试（「When a sentence fails, delete the whole sentence rather than trim words from it」）。
- `UP:productivity/handoff/SKILL.md L12`：「Do not duplicate content already captured in other artifacts ... Reference them by path or URL instead.」
- `UP:engineering/wizard/SKILL.md L10`：界面细节已经在 `template.sh` 里，技能只说「Your job is only to scope the procedure and author its stages」，不复述模板做了什么；SSR L166 引作「Scripts and judgement」范例。
- `UP:engineering/wayfinder/SKILL.md L23`：「The map is an **index**, not a store ... a decision lives in exactly one place, its ticket, so the map never restates it」。
- 保留的一侧：SSR L55 列出修剪时会被误当噪音、但要留下的句子；SSR L142「Before cutting one, name the case it would have guided and what guides that case after the cut.」

**对思考的作用。** 注意力是预算（SSR L13）：删掉 no-op，留下的判断句得到更多注意，深度增加。只删 no-op 不删理解，广度不减。

**检查。** SSR L38–55（duplication、cache、no-op、over-specification、over-defense、sediment）。

**常见破坏。** 按字数一刀切，把理由和立场当作「冗余」一起删掉；这正是 SSR L142 描述的情况。

### 附：按组件放哪条规则（建议）

pstack 的组件类型见 L7 第 A 节。下表是本文的建议，不是任何一方的原文，供 R20 取舍。

| pstack 组件（L7） | 主要落位的规则 | 说明 |
|---|---|---|
| mode | M6（索引里的术语统一）、M7（description）、M13 | mode 的触发行是条件 → 名字（L7 A.1），立场与理由多数属于它指向的组件 |
| playbook | M1 与 M3 放在所有权行后面的可选首段（L7 A.2 模板第 3 项）；M9（点名技能）；M10（每步的判据）；M14 | playbook 只编排（R13 E4），做法留在能力技能 |
| 能力技能 | M1–M13 全部 | mattpocock 的技能都属这一类，它们的形态多样，L7 A.3 也承认多种形态 |
| 原则 | M2（`**Why:**`）、M5（`**The test:**`、`**Stop:**`）、M6 | pstack 原则已有 `**Why:**` 位置（L7 A.4：23 条里 16 条有） |
| reference | M8（一个分支一整份）、M11（交给子代理的模板）、M12 | |
| 子代理简报 | M11 | 放在正文还是 reference，见冲突 C8 |

---

## 2. 与 pstack 写作风格可能冲突的地方

「建议裁决」一列是本文的建议，供 R20 定稿，不是已定规则。上游原文（mattpocock 与 pstack）一律逐字保留，不因下面任何一条改写（SSR L106；R18 第 17 节 D9「搬运的句子逐字保留」）；冲突只影响 MMW 自写的文本和连接文字。

| # | 冲突 | mattpocock 一侧 | pstack 一侧 | 建议裁决 |
|---|---|---|---|---|
| C1 | 理由写不写 | 理由写在规则旁（M2）；SSR L11 事实 1、L55 列为保留 | `PS:skills/poteto-mode/playbooks/authoring-a-skill.md L10`：「Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one.」 | 冲突比字面小。pstack 自己的做法也写理由：原则有 `**Why:**`（L7 A.4，23 条中 16 条）；playbook「理由紧跟在规则后面」（L7 A.2 语气）；`PS:skills/poteto-mode/playbooks/bug-fix.md L5` 整段是纪律与理由；`PS:skills/how/references/explorer-prompt.md` 告诉子代理「A separate agent will write the human-facing explanation from your findings, so favor thoroughness」。同一段 authoring-a-skill 还写「Keep only prose that changes a decision」，与 SSR L11 的测试同义。统一为一条：理由通过 SSR L11 的句子测试就留，只是在证明规则合理、不改变任何决定的就删 |
| C2 | 步骤化程度 | 先定方向再信任（M4）；grilling 全文没有编号步骤，靠 design tree、frontier、rounds 三个概念驱动（`UP:productivity/grilling/SKILL.md L6–28`） | playbook 编号步骤，每步首句是可勾掉的祈使动作，原文抄进 todo（L7 A.2 模板第 4 项；`PS:skills/poteto-mode/SKILL.md` `## Playbooks` 第一段） | 编号步骤只用在 playbook 与确实有先后的能力技能里；概念驱动的能力技能保持原形态（L7 A.3 列出八种形态，pstack 自己也不要求统一）。把 mattpocock 式的技能改写成编号步骤，是本文最担心的破坏 |
| C3 | 禁令的写法 | WFA L74 Negation：先写正面目标，禁令配正面目标（M13） | playbook 语气「大量 "Never / Only / X is not Y" 式的禁令和定义句」（L7 A.2）；`PS:skills/tdd/SKILL.md L28–34` `## Guardrails` 五条都以 Do not / Avoid 开头 | MMW 自写文本按 M13：每个禁令旁边有正面目标或理由。pstack 的禁令多数已跟着理由（bug-fix L5「Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship.」），实际差距在无理由的禁令串 |
| C4 | 比喻与 leading word | leading word 可以是比喻性的词：**fog of war**、**tracer bullet**、**tight**、**red**（M6）；也有装饰性比喻：`UP:engineering/prototype/LOGIC.md L58`「the HTML shell rides along」、`UP:engineering/prototype/UI.md L54`「it's wallpaper」 | `PS:skills/unslop/SKILL.md L66` rule 32 点名禁止「figurative verbs ("rides along", "stands on")」；L57 rule 26 禁止「harness (as metaphor)」「surface (as in "API surface")」「gold-plating」，而 mattpocock 用「Throwaway harness」（diagnosing-bugs L31）、「The interface is the test surface」（codebase-design L64）、「prevents the agent from gold-plating」（AGENT-BRIEF L37） | 以 SSR L77 为界：「A metaphor is a finding unless it is a leading word」。领域里有固定意思的术语（test harness、tracer bullet、fog of war、blast radius）是 leading word，保留；只为生动的比喻动词（rides along）在 MMW 自写文本里换成直说。用户 `~/.claude/CLAUDE.md` 规则 7 也禁止 mannered prose，与此一致 |
| C5 | 冒号与破折号 | 用冒号引出定义是 mattpocock 的基本句式（`UP:engineering/tdd/SKILL.md L20`「A **seam** is the public boundary you test at: the interface where you observe behavior」）；上游 `mmw-v2/upstream/CLAUDE.md` 末段禁 em-dash，改用「a comma, colon, period, parentheses」 | `PS:skills/unslop/SKILL.md L37` rule 14「Colons are fine before a list or example. Not as mid-sentence connectors」；L36 rule 13 连括号也不许；`PS:skills/poteto-mode/SKILL.md L26` 要求任何 prose surface 走 unslop | 需要 R20 定。建议：技能文本允许「术语: 定义」式冒号，因为 leading word 的定义句（M6）依赖它，禁掉就要重写每一个定义（推断）；禁 em-dash 两边一致，本仓库已由 `check_upstream_em_dashes.py` 检查上游目录（AGENTS.md `## Commands`） |
| C6 | 句子密度 | 规则与理由常在一句里（`UP:engineering/improve-codebase-architecture/SKILL.md L20`「Deepening a module pays off by making future changes to it easier, so put extra weight on the parts of the codebase that have recently changed.」） | `PS:skills/poteto-mode/SKILL.md L101`「Short declarative sentences. One thought per sentence」（写回复的规则）；`PS:skills/unslop/SKILL.md L62` rule 28 | 一条规则加它的理由算一个意思，可以一句；超过这个就拆。SSR L55「the body is written plainly」 |
| C7 | description 的内容 | 只写触发（M7；SSR L67） | 原则的 description 写「Apply when <情境>. <规则摘要>」（`PS:skills/principle-attack-the-premise/SKILL.md L3`）；mode 的 description 两句，第一句是身份（L7 A.1） | 导入的 pstack 组件 description 逐字保留（上游名字与原文不改）；MMW 自写组件按 SSR L67。pstack 的原则和 playbook 都是 `disable-model-invocation: true`，按 SM L10 它们的 description 本来就是给人看的摘要，冲突只在 MMW 自写的模型调用技能上 |
| C8 | 子代理简报放哪 | 简报写在调用步骤里（`UP:engineering/code-review/SKILL.md L60–70`；DESIGN-IT-TWICE L23–38）；SSR L15 事实 5「Material every run of a task reads belongs in the file that run already holds」 | 子代理提示模板放 `references/`，即使每次都用（L7 A.5 表第一行；`PS:skills/how/references/explorer-prompt.md` 开头「Build each explorer subagent's prompt from this template」）；而 pstack 自己的 `PS:skills/principle-guard-the-context-window/SKILL.md L15` 说常用内容应内联（L7 E.1 第 28 条记为不一致） | 短简报（几行任务加字数上限）留在步骤里；整份原样转交的长模板可以单独成文件。R18 审查记录第 34 条已按此处理 axis 简报 |
| C9 | 跨文件引用方式 | 按名字或标题引用（`UP:engineering/prototype/LOGIC.md L58`「the way the [SKILL](SKILL.md) describes」）；文件内按 Phase 编号（diagnosing-bugs L128「Re-run the Phase 1 feedback loop」） | 跨文件按步骤编号（`PS:skills/poteto-mode/playbooks/bug-fix.md L8`「before the step-3 architect/interrogate fan-out」；mode「(Feature step 3)」），L7 A.1 把它列为写错 | 跨文件一律按标题（SSR L81），文件内的编号引用可以保留 |
| C10 | 完成怎样写 | 每步 `Done when` 与穷尽判据（M10） | playbook 末行 `**Reply:**` 写回复内容（L7 A.2 模板第 6 项）；原则的 `**Stop:**`（`PS:skills/principle-attack-the-premise/SKILL.md L19–21`） | 不冲突，两者回答不同的问题：`Done when` 说何时停，`**Reply:**` 说交回什么。MMW 自写 playbook 两者都写 |
| C11 | 开头写什么 | 目的、下游、代价（M1） | 粗体所有权行「**You own this task. Plan, review, verify.**」（`PS:skills/poteto-mode/playbooks/bug-fix.md L3`） | 不冲突：所有权行说谁决定，M1 的开头说为了什么。顺序建议：所有权行在前，M1/M3 的内容放进 L7 A.2 模板第 3 项的可选首段 |
| C12 | 调用别的技能 | 点名技能（M9）；上游原文写「Call the Skill tool」 | 「Delegate to other skills by path」（authoring-a-skill L10）；原文写 Cursor 专有的 `/loop`、`AskQuestion`（bug-fix L8，mode L20） | 两边都有宿主专有写法，都不在上游原文里改；MMW 自写文本按 SSR L95、L118：技能按名字点名，自己的 reference 用技能内路径，宿主工具写成能力 |

**两者一致的地方**（R20 不必再裁决）：

- 修剪：pstack「When in doubt, delete. Keep only prose that changes a decision」「Don't restate」（authoring-a-skill L10）与 WFA L78–81 的 no-op 测试、single source of truth 相同。
- 环境是真相来源：pstack「Point at structural sources (types, READMEs, config)」（同上）与 WFA L79 environment as cache 相同。
- 跳步写理由：pstack「A step you choose not to do stays in the list with a one-line `skip: <reason>`」（mode `## Playbooks`）与 `UP:engineering/diagnosing-bugs/SKILL.md L8`「Skip phases only when explicitly justified」相同。
- 结论带证据：pstack mode L107「Every claim carries its evidence or its label in the same sentence」与 mattpocock code-review 要求每条 finding 引出处（L64、L70）同向。

---

## 3. 对改名的观察（供 R19）

以下只是从上游文件名归纳出的做法，不是规则；上游名字本身不改。

- 技能名说出这项工作：动作或动名词（`to-spec`、`to-tickets`、`diagnosing-bugs`、`writing-for-agents`、`grilling`），或这项工作产出的东西（`prototype`、`wizard`），或一个 leading word（`wayfinder`）。出处：squash 提交的 `git ls-tree` 列表。
- reference 文件名说出它承载的分支或产物，全大写：`LOGIC.md`、`UI.md`（prototype 的两个分支），`DEEPENING.md`、`DESIGN-IT-TWICE.md`（codebase-design 的两个深入方向），`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`（triage 的两种产物），`HTML-REPORT.md`，`SKILL-MECHANICS.md`。读者只看文件名就知道什么时候打开它，这与 M8「指针即条件」一致（推断）。
- 脚本名说出它是什么：`template.sh`（wizard）、`hitl-loop.template.sh`（diagnosing-bugs，名字里带 `.template` 表明要复制后改）。
- 给人读的地方按名字而不是编号称呼：`UP:engineering/wayfinder/SKILL.md L15–17`（`## Refer by name`）「A wall of `#42, #43, #44` is illegible; names read at a glance.」

---

## 4. 本文读了什么、没读什么

**读全文的**：squash 提交里的 `wayfinder`、`grilling`、`grill-with-docs`、`grill-me`、`to-spec`、`to-tickets`、`tdd`（含 `tests.md`、`mocking.md`）、`code-review`、`prototype`（含 `LOGIC.md`、`UI.md`）、`codebase-design`（含 `DEEPENING.md`、`DESIGN-IT-TWICE.md`）、`improve-codebase-architecture/SKILL.md`、`diagnosing-bugs/SKILL.md`、`triage`（含 `AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`）、`wizard/SKILL.md`、`implement`、`research`、`to-questionnaire`、`handoff`、`writing-for-agents/SKILL.md` 与 `SKILL-MECHANICS.md`；本仓库 `SKILL-SET-RULES.md` 全文；pstack 的 `authoring-a-skill.md`、`bug-fix.md`、`principle-attack-the-premise`、`principle-guard-the-context-window`、`tdd/SKILL.md`、`unslop/SKILL.md`、mode `SKILL.md` 第 1–40 行与第 97–125 行、`how/references/explorer-prompt.md` 前 12 行；L7 第 0 节与第 A.0–A.5 节；R18 第 17 节与审查记录。

**只读了片段或没读的**：`improve-codebase-architecture/HTML-REPORT.md` 只读了 `## Tone`；`wizard/template.sh`、`diagnosing-bugs/scripts/hitl-loop.template.sh` 没读；各技能的 `agents/openai.yaml` 没读；本仓库工作树里上游技能的现行副本（带 MMW 改动）没有逐一与原文比对，本文的上游引文一律取自 squash 原文；R13 只读了标题，引用的 R13 结论（E4）经 L7 与 R18 转述；pstack 其余能力技能与 playbook 没有逐份读，第 2 节关于 pstack 整体写法的说法来自 L7 的归纳。

**未经验证的**：本文说每条写法「对深度与广度起什么作用」，依据是 WFA 与 SSR 的原文论断，没有做过对照运行；按 SSR L150，一段文本是否真的改变 agent 行为，要由一个只拿到触发和真实任务的新 agent 跑一次才能确认。
