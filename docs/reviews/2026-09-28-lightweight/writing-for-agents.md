# writing-for-agents

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。这个技能是全集的写作与复审标准，排在修复轮的第一步：以后每一次写技能、改技能、修剪技能，都按它来。

**判断**：调查员的诊断成立。标准没有"交接理解"这一条：文本的职责只写成"做决定"。它的方法是逐句检验、只量字数，默认修法是删或并；Sediment 表又把理由送去 ADR 和 merge-note，而标准自己承认这两处 agent 读不到。几条合在一起，讲目的、讲下游、讲立场的句子在标准里没有位置，只能被当成负担删掉。前几轮至少十一个技能的"为什么"就是这样没的。

我在调查员草稿上做了一处关键修改：原则里必须带着检验，而不是只说"要写目的"。只说"要写目的"，会招来口号和流水线复述，这正是你担心的废话。检验来自这一轮复核用的标准，与 Anthropic、OpenAI 最新的官方指南一致：
- Anthropic 的提示词指南说："Claude is smart enough to generalize from the explanation"。
- Anthropic 的 Fable 5 指南说："Give the reason, not only the request"。
- OpenAI 的 skill-creator 说："Include only information that changes its decisions"。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| F1 | `SKILL-SET-REVIEW.md` `## What skill text is for`，新的第 1 条（原五条顺延，第 9 行 "these five facts" 改为 "these six facts"） | 1. **A skill hands over understanding, not only steps.** Steps cover the cases their writer foresaw, and the agent meets others. So beside its steps a skill says what the work is for, who depends on what it produces and what a wrong or shallow result costs them, and, next to a rule, the reason for it: a model given the reason carries it into cases no rule names. Upstream's `wayfinder` does this in its opening and in `## Plan, don't do`. Such text is paid for as fact 3 says, by a judgement the agent could not make without it, and it has two tests. A sentence beside a rule passes when you can name a case the steps do not cover and what the agent does differently there with it. An opening passage passes when an agent holding only the skill could not otherwise say what the work is for, who acts on what it produces, and what a shallow result costs them. A sentence that only declares importance, retells the pipeline around the task, or tells this agent what another skill's agent does, fails both and is a no-op. One that passes is not cut for length; cutting it takes what [Editing](#editing) asks. | 以后的写作者和修剪者有了同一把尺子：讲目的的句子要过检验才留，过了检验就不因字数删。放在第 1 条，是因为第 9 行规定下面每条检查都服务于这些事实。按 advisor 意见：分出两种检验（规则旁的句子按"情况"检验，开头的定位段按"新 agent 能否说出目的"检验）；"改变的做法"要写成做法不同；引用第 3 条事实，不另造一套说法；删掉"只有步骤的技能不如脚本"这句，它本身说不出情况，而且对 `retro`、`exe-release` 不成立；把"告诉本 agent 别的技能的 agent 做什么"列入不合格；末句把删减的举证责任指向 F8。 |
| F2 | `### Load and disclosure`，"A rule sits in the text of the agent that must follow it…" 那一条末尾 | A reason the acting agent needs is the same: a merge-note, an ADR or the glossary may explain it to maintainers, but the sentence the agent acts on is in the skill text. | 堵住"理由只写在 merge-note 里"这条路。前几轮就是经这条路，把 `implement`、`code-review`、`teach`、`wayfinder`、`diagram-design`、`grilling` 的理由挪到了 agent 读不到的地方。 |
| F3 | `### Redundancy and bloat` Sediment 表两行改写 | `the maintainer's reason for a design (why a script takes a lock rather than checking a pid)` → an ADR；`where the writer's material came from (a research note, "from chapter 3 of …"), other than the author of a concept, an issue number the reader cannot use` → nowhere | 第一行加一个例子，把"维护者的理由"和"执行者需要的理由"分开；第二行不再误伤 `codebase-design` 的 `(Michael Feathers)`、`(Ousterhout)` 这类出处。 |
| F4 | 同一节 "These stay…" 段，在列举末尾加 | …; a sentence that passes the test of fact 1 of [What skill text is for](#what-skill-text-is-for); the name of the author or work a concept comes from (**Seam**, Michael Feathers), which calls up a theory the model already holds. A trimming pass tests each sentence against a step; these are tested against the cases no step covers. | 修剪者拿到检验方法：这类句子不按"哪一步用到了它"来检验。 |
| F5 | 同一节 **No-op** 条末尾 | A stance is not an attitude: it names the temptation particular to this work and what to do instead (upstream `wayfinder`: "The pull to just do the work is usually the signal you've reached the edge of the map"), and a model does not hold it by default. | 修剪者不会把 `wayfinder`、`diagnosing-bugs`（"Be aggressive. Be creative. Refuse to give up."）这类立场句当成 "be careful" 删掉。 |
| F6 | `### Load and disclosure` 第一条改为右栏；第二条 "Entered once / several moments" 的分支写法删去，只留约束（C2） | `SKILL.md` holds what every task passes through: when the moments share a purpose that no reference states for itself, first a few sentences on what the work is for and what depends on it; then the table that sends each reader to its moment. … The table sits before any step with side effects, so a re-entering agent does not repeat them. | 现在的写法会产出一开头就是路由表或 token 解析节的 `SKILL.md`（`advisor`、`dispatch`、`code-review`、`manage-agents-md`、`retro` 都是这样）。原来那条真正要约束的是"放在有副作用的步骤之前"，不是"放在第一行"。 |
| F7 | `## Editing`，"A fix removes, merges, moves or simplifies before it adds…" 之后 | A passage that hands over purpose, a reason or a stance is not a mechanism: it needs no failed run behind it, but it names its case, and says when that case is inferred rather than observed. | "先减后加、新增机制要指出出事的那次运行"是你对过度防御的裁定，保留；这一句把讲目的的文字从"机制"里分出去。 |
| F8 | 同节 "Asked to 'streamline'…" 之后 | Reaching the completion criterion on the walked path does not clear a cut to such a passage, since its effect is on the runs the walk did not take. Before cutting one, name the case it would have guided and what guides that case after the cut. | 删减的唯一检验（走查仍能完成）查不出讲目的的文字被删了，这一句补上。 |
| F9 | `REVIEWING-A-SKILL-SET.md` 第 2 步，"which of its sections the step used" 之后 | A passage that passes fact 1 is recorded as read by the task, not as unused. | 负担统计不再把这类段落算成"没用到的字"。第 5 步报告表的 "words read that the run did not use" 后面加 "(orienting passages excepted)"。 |
| F10 | `REVIEWING-A-SKILL-SET.md` 第 4 步，Done when 之前 | Read each skill also as its fresh agent: from the skill alone, can it say what the work is for, who uses what it produces, and what a shallow result costs? Where it cannot, that is a finding, fixed by writing the sentences that pass the test of fact 1. | 复审方法里第一次有了一步，专门问"这个技能有没有交代目的"。 |
| F11 | `## Upstream examples` 表加一行、恢复一行（`66089d06` 删掉的） | `What skill text is for` → `engineering/wayfinder/SKILL.md` opening, `## Plan, don't do`, `## Fog of war`; `productivity/grilling/SKILL.md` last two paragraphs → purpose and stance in a few sentences, which the agent carries into cases no step names。`Redundancy and bloat` → `engineering/code-review/SKILL.md` `## Why two axes` → the one reason kept, because without it the agent would merge the axes | 现在的范例表没有一个"讲目的"的例子；而第 13 行唯一的"好技能"范例是一份五行、不讲目的的技能。 |
| F12 | `### Rules and completion criteria` 第 123 行改为右栏（C1） | In the set's own text, a step without a completion criterion is a finding, and so are two different statements of what "done" means for one task; the set writes it on a line beginning `Done when`. | 删去 "or a section"：讲立场的一节没有天然的完成标准，照原文会被硬加一行 `Done when`，或被判成缺陷。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `### Refusals and output an agent reads` "A refusal has the three parts `AGENTS.md` names…" 及其后 "'Could not check' and 'checked, it is fine' are different messages." | 改为 "A refusal follows `CODING_STANDARDS.md`, and its next step fits the skill that receives it."；后两条保留 | 指错了文件（规则在 `CODING_STANDARDS.md`），且与之重复。 |
| D2 | `### Descriptions` 第 70 行（冒号破坏 YAML）与第 68 行"本仓技能只有两个键"的检查部分 | 在 `mmw-v2/tests/lib/` 加一个 frontmatter lint（写法照 `check_upstream_em_dashes.py`，由每个 `run.sh` 调用）：用 YAML 解析器读每个 `SKILL.md` 的 frontmatter，并检查本仓技能只有 `name`、`description`；落地后删第 70 行，第 68 行只留 "so its name and description have one authority" 的理由 | 标准自己第 59 行说能精确检查的规则应当变成检查；YAML 问题在 9 月 23 日真实出现过（`advisor`、`ui-acceptance`）。 |
| D3 | `### Rules and completion criteria` 第 124 行（被 grep 的文件里不能出现禁用 token） | 删 | grep 检查第一次运行就会暴露，这句不改变任何结果。 |
| D4 | `### Descriptions` 第 69 行（user-invoked 技能的 description） | 删；第 65 行第一句后加 "(a user-invoked skill's is a one-line summary for the person, `SKILL-MECHANICS.md` `## Invocation`)" | 与 `SKILL-MECHANICS.md` 重复，但它是第 65 行的例外，所以并过去。 |
| D5 | `## Editing` 第 144 行（merge-note 与 downstream-note） | 删 | 根 `AGENTS.md` `## Key Conventions` 已写；这是仓库规则，按你的裁定归 `AGENTS.md`。 |
| D6 | `### Hand-offs` 第 92 行末句 "A skill directory holds no copy of, or link to, another skill's files."；`## Verifying` 第 150 行首句 "Run the smallest test suite…" | 删；第 150 行只留 "Green tests prove the scripts, not that the text reads well; report them on a separate line." | 分别与第 15 行、你全局规则第 15 条和 `TESTING.md` 重复。 |
| D7 | `### Scripts and judgement` 第 59 行第二句 "A numeric limit is enforced by the mechanism; models do not copy literal numbers reliably." | 改为 "A numeric limit a program depends on is enforced by that program." | 原句是没有测量依据的断言，还与第 99 行（子 agent 的任务说明要写明长度）矛盾。 |

### 不采纳

- 调查员 A3（把第 119 行的手工 grep 清单也做成 lint）：宿主名一项需要一张允许清单（`Claude Design` 是产品名，`pi` 是常见子串），误报率没测；这一段目前保持原样。

### 验证

这些改动能不能真的改变写作者和修剪者的做法，是这一轮最需要验证的一点，要从两个方向验：修复轮完成后，一个全新的 agent 只拿着新标准去修剪一个本仓技能（例如 `implement`），看它是否保留过了检验的句子、删掉没过检验的；另一个全新的 agent 拿着新标准去给一个技能补定位文字，看有没有废话混进去。

## 结论

体量：`mmw-v2/upstream/skills/productivity/writing-for-agents/` 正文五个文件共 7,891 词。其中上游原文是 `SKILL.md` 1,819 词和 `SKILL-MECHANICS.md` 414 词：对照上游 squash 提交 `5b1a4c51`，`SKILL.md` 只改了两行（description 与第 8 行指向 `SKILL-SET-REVIEW.md` 的那句），`SKILL-MECHANICS.md` 一字未改，两处改动都有 merge-note 条目（`mmw-v2/merge-notes/writing-for-agents.md`）。本仓写的是 `SKILL-SET-REVIEW.md` 4,703 词和 `REVIEWING-A-SKILL-SET.md` 945 词。这个技能没有脚本。

主要问题不在字数，而在方向。`SKILL-SET-REVIEW.md` 是以后每一轮写技能、审技能的 agent 共同遵守的标准，它对"说明目的、背景和思考方式的文字"没有给出任何位置：它的测量工具（逐句测试、按步骤记录"用到的段落"、只统计字数）会把这类文字算成负担，它的 Sediment 表把"理由"默认送去 ADR 或 merge-note，而这两个地方它自己也承认运行中的 agent 读不到。前几轮减重正是按这条路线删掉了一些让 agent 理解目的的句子（证据见"附加任务"一节第 6 条）。标准本身另有约 220 词可删，都是与 `CODING_STANDARDS.md`、根 `AGENTS.md`、`SKILL-MECHANICS.md` 重复的内容，以及可以交给 lint 的规则；同时建议补入约 330 词，写入"灵魂"原则，并给现有的删减条款加上对照。增删相抵，净增约 110 词。上游原文部分没有要改的。

这个技能自己的"灵魂"在 `SKILL-SET-REVIEW.md` `## What skill text is for` 里基本是齐的（脚本和文本的分工、"Direct, then trust"），唯独缺了"技能是在交接理解"这一条，而这一条正是这一轮任务书要求的核心。

## A. 删除或改成脚本

行号指 `SKILL-SET-REVIEW.md`，另有说明的除外。

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `### Refusals and output an agent reads` 第 134 行：`A refusal has the three parts AGENTS.md names (what happened, …)` | 6，外加指向错误 | 根 `AGENTS.md` 里没有这条规则。三个部分写在 `CODING_STANDARDS.md` 第 10 行（`Every refusal has the three parts refusal.py builds … A check that could verify nothing says so instead of reading like a pass (ADR 0008)`），同一句的后半 `"Could not check" and "checked, it is fine" are different messages` 也与那一行重复 | `CODING_STANDARDS.md` 第 10 行和 `refusal.py`；reviewer 的 Standards axis 按它审。剩余风险：无 | 改成 `A refusal follows CODING_STANDARDS.md, and its next step fits the skill that receives it.` 保留后两条（下一步放在前几行、下一步照写可以安全执行），它们是文字层面的要求。省约 25 词 |
| A2 | `### Descriptions` 第 70 行：`A description holding a colon followed by a space breaks YAML; quote it. …` | 1 | 这是可以精确检查的规则，而标准自己在第 59 行写着 `A rule a script could check exactly becomes a check … not a sentence`。它真实触发过：`docs/reviews/2026-09-23-skill-set/汇总.md` 记录 `advisor` 和 `ui-acceptance` 的 description 都不是合法 YAML，提交 `d37a6048` 修过一批（`trigger-only descriptions, valid YAML`）。目前没有任何脚本检查它：`mmw-v2/tests/lib/` 只有 `check_module_paths.py` 和 `check_upstream_em_dashes.py`，`install.sh` 也不解析 frontmatter | 在 `mmw-v2/tests/lib/` 加一个 lint，写法照 `check_upstream_em_dashes.py`，由每个 `run.sh` 调用：用 YAML 解析器读每个 `SKILL.md` 的 frontmatter，同时检查第 68 行"本仓自写技能只有 `name`、`description` 两个键"。剩余风险：lint 落地之前这句话要留着 | lint 落地后删掉第 70 行（29 词）。第 68 行保留理由那半句 `so its name and description have one authority` |
| A3 | `### Paths, tokens and host neutrality` 第 119 行：`The check is a grep of every SKILL.md, description and reference …` | 1 | 这是写成文字、要 agent 手工去跑的 grep，同样违反第 59 行。路径、token 定义、`CHECK:` 里的路径这几项可以精确判断。宿主名一项会误报（`Claude Design` 是产品名，`pi` 是常见子串），需要一张允许清单 | 同 A2，放进同一个 lint。剩余风险：宿主名的允许清单要随新产品名更新；我没有测过误报率 | lint 落地后，这一段缩成一句 `mmw-v2/tests/lib/<lint> checks these.`，省约 65 词。用户若不想新增机制，这一段可以保持原样，这一条不是必须做的 |
| A4 | `### Rules and completion criteria` 第 124 行：`When a check greps the files it scans for a forbidden token, the token appears nowhere …` | 2 | 一个 grep 检查只要文件里出现这个 token 就会失败，第一次跑就会暴露，所以这句话不改变任何结果。它唯一服务的对象是第 119 行的手工 grep | 由检查本身承担（A3 之后由 lint 承担）。剩余风险：A3 不做的话，手工 grep 的人要自己判断否定句里出现的 token，风险低 | 删掉（25 词） |
| A5 | `### Descriptions` 第 69 行：`A user-invoked skill (disable-model-invocation: true) is loaded only when …` | 6 | 与 `SKILL-MECHANICS.md` 第 10 行（`the description becomes human-facing: a one-line summary, trigger lists stripped`）重复。但它同时是第 65 行 `A description carries the trigger and nothing else` 的例外，完全删掉，复审者会把 user-invoked 技能的摘要式 description 判成缺陷 | 由 `SKILL-MECHANICS.md` `## Invocation` 承担，例外本身并入第 65 行。剩余风险：无 | 删掉第 69 行，在第 65 行第一句后加 `(a user-invoked skill's is a one-line summary for the person, SKILL-MECHANICS.md ## Invocation)`。省约 20 词 |
| A6 | `## Editing` 第 144 行：`A changed upstream skill gets its merge-note entry rewritten in place. A change that invalidates …` | 6 | 根 `AGENTS.md` `## Key Conventions` 第 4、5 条写了同样两件事，而在这个仓库里 `AGENTS.md` 每一轮都在上下文里。`### Upstream skills` 第 105–106 行也已经要求每段改动对应一个 merge-note 条目。这两条是仓库规则，不是技能文本规则，按用户的裁定，仓库规则归 `AGENTS.md` | 由 `AGENTS.md` `## Key Conventions` 和第 105–106 行承担。剩余风险：无，改 MMW 技能只会在这个仓库里做 | 删掉（26 词） |
| A7 | 文件内部重复：`### Hand-offs` 第 92 行末句 `A skill directory holds no copy of, or link to, another skill's files.`；`## Verifying` 第 150 行首句 `Run the smallest test suite …` | 6 | 第 92 行末句与第 15 行（第 5 条事实）`A skill never carries a copy of another skill's files` 是同一个意思。第 150 行首句与用户全局提示词第 15 条（`mmw-v2/prompt/shared.md`，四个宿主都会加载）和 `TESTING.md` `## Which suites a change needs` 重复；第 153 行的 `Done when` 已经写了"覆盖改动文件的测试通过" | 第 15 行和第 153 行。剩余风险：无 | 删掉第 92 行末句；第 150 行只留 `Green tests prove the scripts, not that the text reads well; report them on a separate line.` 合计省约 25 词 |
| A8 | `### Scripts and judgement` 第 59 行第二句：`A numeric limit is enforced by the mechanism; models do not copy literal numbers reliably.` | 4 | 这是一条没有测量依据的经验断言，而标准自己的 Over-defense 四问里有一问是 `Is its premise true when measured, not reasoned?`。它还和第 99 行矛盾：第 99 行要求子 agent 的任务说明写明长度，并拿上游 `code-review` 的 `"Under 400 words"` 当正面例子。照字面执行，修剪者会把给 agent 看的数字限制都删掉 | 程序依赖的数字仍由程序检查。剩余风险：无 | 改成 `A numeric limit a program depends on is enforced by that program.`，删掉后半句 |

没有报的（查过，结论是该留）：

- `### Paths, tokens and host neutrality` 里规定的标题字面 `` ## Resolve `<token>` once `` 和那句会话命令的固定句子：没有脚本解析它们（grep 过 `mmw-v2` 下的 `.py`、`.sh`、`.mjs`），但它们是全集共用的写法约定，`implement` 等技能按这个说法指向别的技能，成本很低。
- `### Upstream skills` 全节：这一节写的是用户的裁定（上游原文能不改就不改），而且它恰好保护了上游技能里讲目的的原文，不让修剪者去删。
- `REVIEWING-A-SKILL-SET.md` 第 28 行 `Decisions for the user: only a choice that changes what a customer sees …`：与用户全局提示词第 1 条重复，但在这里它定义的是报告里的一个小节，只有 30 词，删不删无所谓，不报。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 6 行（上游）`the same levers make each one predictable, since the agent takes the same _process_ every run rather than producing the same output`：整个技能存在的理由，写文档是为了让 agent 每次走同一个过程。
- `SKILL.md` 第 25 行（上游）`Not a cost to minimise: it is the price of human agency; spend it where human judgement matters`：说明为什么有些负担是值得付的。
- `SKILL.md` 第 79 行（上游）`Cache what the agent cannot find by looking: the unwritten convention, the reason behind a choice, the gotcha no config confesses.`：整个技能里唯一一句把"理由"列为该写的内容，是"灵魂"原则在上游原文里的依据。
- `SKILL-SET-REVIEW.md` 第 11 行，第 1 条事实 `Scripts carry what is deterministic; text carries judgement.`：MMW 分工的原则本身。
- 第 13 行，第 3 条事实 `Direct, then trust.`，包括 **rigid** 和 **brittle** 的定义：这正是任务书"死板流程"的定义，删掉它，修剪者就不知道为什么不能把判断写成清单。
- 第 15 行，第 5 条事实 `Skills are peers composed by name.`
- 第 31 行 `Material works only from text the agent loads.` 和第 32 行 `The text makes sense to an agent that holds nothing else`：说明为什么放进 merge-note 或 ADR 的理由对 agent 等于不存在，是下面建议的论据。
- 第 53 行 `These stay, though a trimming pass reads them as noise`：全文唯一的反向约束，下面的建议是扩充它，不是替换它。
- 第 58 行 `Where only understanding can decide … a contrasting pair of examples when a misreading is likely`。
- 第 61 行 `Programs branch on exit codes and fields; the refusal's wording is for the agent.`
- 第 67 行 `every host scans it into its system prompt, so one name ties the skill to that host or runner`：规则后面紧跟理由的写法示范。
- 第 90 行 `A sentence written for one caller can misread under another.` 和第 91 行 unguided choices，包括 `A choice any reasonable model makes the same way is not unguided`。
- 第 128 行 `an agent reading it takes the specifics as requirements`。
- 第 142 行 `Asked to "streamline", an agent shortens and cuts function with it`：全文最明确的一句警告，提醒删减会伤到功能。
- 第 151 行 `A sentence present in the text is not a behaviour observed`。
- `REVIEWING-A-SKILL-SET.md` 第 3 行 `A skill is judged by how an agent uses it inside its tasks and how it joins the skills before and after; a per-file defect count misses both.`：这是用户的裁定（Nowledge Mem 记忆 `88b4e72c`，2026-09-21：按文件清点缺陷是机械化的）。
- `REVIEWING-A-SKILL-SET.md` 第 9–12 行，两类证据：用户对过度防御的裁定。

### 缺口与补充草稿

- **B1**：`SKILL-SET-REVIEW.md` `## What skill text is for`，新加为第 1 条，原来的五条顺延，第 9 行的 `these five facts` 改成 `these six facts`。

  缺的是：标准没有一处说技能是在交接理解。第 1 条事实把文本的职责定为 `judgement`，具体列的是 `what counts as done, which of two readings applies, what the user meant`，全是决策点。用户的两次裁定都比这宽：2026-09-11（记忆 `60e59dbe`）`当初写技能的 agent 自以为知道的工作方式必须写进技能里教给新 agent，不能假设知识会自动迁移`；2026-09-23（记忆 `e83f457b`，也就是这份标准据以重写的那次裁定）`技能文本指导 agent 的思考与判断`。写进标准时，"思考"这一半丢了。后果是：修剪者按"每句话服务哪个判断"去检验一段讲目的的文字，找不到它服务的那个判断，就把它删了。放在第一条，是因为第 9 行说下面每一条检查都服务于这些事实，这样所有检查都会按这一条来读。

  > 1. **A skill hands over understanding, not only steps.** It is how the person who owns the work passes an agent what no script can carry: what the job is for, who reads what it produces and what they do with it, what a shallow or wrong result costs further on, and how to think where the steps run out. Upstream's `wayfinder` does this in its opening and in `## Plan, don't do`: a few sentences the agent carries into every case its steps do not name. A skill that is only steps should have been a script. Such a passage is judged by what the agent would do differently off the listed path, not by whether one step uses it; one that changes nothing the agent does is a no-op like any other.

- **B2**：`### Redundancy and bloat` Sediment 表第 48 行和第 50 行，收窄这两行的写法。

  第 48 行 `the maintainer's reason for a design | an ADR` 没有说清"维护者的理由"和"执行者需要的理由"怎么区分，修剪者分不清时，会把两种都送进 ADR 或 merge-note。第 50 行 `a source line ("from chapter 3 of …") … | nowhere` 本意是删掉"这段内容是作者从哪里查来的"这类出处，但照字面读，也会删掉 `codebase-design` `SKILL.md` 第 22 行的 `**Seam** _(Michael Feathers)_` 和第 107 行的 `(Ousterhout)`。这类作者名能让模型调出它已经掌握的整套理论，作用和 `SKILL.md` `## Leading words` 讲的一样（`recruiting priors the model already holds`）。协调者转来的 `codebase-design` 调查员的发现，我核实过：这两处出处在上游原文 `5b1a4c51` 里就有，本仓现有文本也还在。

  > | the maintainer's reason for a design (why a script takes a lock rather than checking a pid) | an ADR |
  >
  > | where the writer's material came from (a research note, "from chapter 3 of …"), an issue number the reader cannot use | nowhere |

- **B3**：第 53 行 `These stay …` 段，在列举里加三项，并在段末加一句。

  现在这一段只保护两类理由：`a reason the agent needs to decide an edge case`，和 `to keep a design choice it would otherwise simplify away`。讲目的、讲下游、讲态度的文字两类都不属于。

  > …; a passage that says what the work is for, who depends on what it produces, or the stance it takes (fact 1 of [What skill text is for](#what-skill-text-is-for)); the acting agent's own reason for a step (why it comes first, who reads its output and what they do with it), which is not a maintainer's reason; the name of the author or work a concept comes from (Seam, Michael Feathers), which calls up the theory the model already holds. A trimming pass tests each sentence against a step; these are tested against the cases no step covers.

- **B4**：第 40 行 **No-op**，区分空洞的态度和具体的立场。

  `an attitude where an action would do ("be careful", "make sure")` 这句写得没错，但修剪者会把 `wayfinder` 的 `Wayfinding is about finding that way, not charging at the destination` 也当成"attitude"。

  > A stance is not an attitude: it names the temptation particular to this work and what to do instead (upstream `wayfinder`: "The pull to just do the work is usually the signal you've reached the edge of the map"), and a model does not hold it by default.

- **B5**：`### Load and disclosure` 第 23 行，写明 `SKILL.md` 开头放什么。

  现文 `SKILL.md holds what every task passes through, plus the table that sends each reader to its moment`，再加上第 24 行 `the table that finds the reader's moment comes first in SKILL.md`，写出来的技能就是一打开就是路由表，或者一打开就是 token 解析节，没有一句话说这个技能是干什么的。实际情况：`mmw-v2/skills/advisor/SKILL.md` 开头是 `Two moments, and this run is at one of them.` 然后接表；`mmw-v2/skills/dispatch/SKILL.md` 是 `Choose the moment that matches your role.`；`mmw-v2/upstream/skills/engineering/code-review/SKILL.md` 全文 104 词，只有一张表；`mmw-v2/skills/manage-agents-md/SKILL.md` 和 `mmw-v2/skills/retro/SKILL.md` 一开头就是 `## Resolve … once`。其中 advisor 原来有一句 `The two sides are asymmetric on purpose. The caller owns the decision and the evidence; the advisor owns what it reads and what it concludes.`，在 `e74e0140` 里删掉了（这个意思在 `references/advising.md` 第 7 行还部分保留着）。每个角色都会经过的那一处，正好是放整件事目的的地方。第 24 行真正要约束的是"放在任何有副作用的步骤之前"，不是"放在第一行"。

  > - `SKILL.md` holds what every task passes through: first, in a few sentences, what the work is for and what depends on it; then the table that sends each reader to its moment. …

- **B6**：`## Editing` 第 140 行和第 142 行。

  第 140 行 `A fix removes, merges, moves or simplifies before it adds. A fix that adds a mechanism … names the run in which the failure occurred.` 对机制是对的（这是用户对过度防御的裁定），但修剪者会把"补一段讲目的的话"也当成需要先有失败记录的新增。第 142 行给删减设的唯一检验是 `confirm it still reaches its completion criterion with nothing guessed`，可是讲目的的文字，作用恰恰在走查没有走到的那些情况里，所以这个检验永远查不出它被删了。

  > (after line 140) A passage that hands over purpose or stance is not a mechanism: it is added when an agent holding only the skill could not say what the work is for or who uses what it produces.
  >
  > (after line 142) Reaching the criterion on the walked path does not clear a cut purpose or stance passage, since its effect is on the runs the walk did not take. Before cutting one, name the case it would have guided and what guides that case after the cut.

- **B7**：`REVIEWING-A-SKILL-SET.md` 第 18 行（步骤 2）、第 22 行（步骤 4）、第 25 行（步骤 5 的负担表）。

  步骤 2 要记录 `which of its sections the step used`，步骤 5 要报告 `words read that the run did not use`。讲目的的段落不属于任何一个步骤，照这个统计就被算成"没用到的字"，下一步就会被删。复审方法里也没有哪一步去问"这个技能有没有交代目的"。

  > (step 2, after "which of its sections the step used") A passage that orients the whole task (its purpose, who uses its output, its stance) is recorded as read by the task, not as unused.
  >
  > (step 4, before its Done when) Read each skill also as its fresh agent: from the skill alone, can it say what the work is for, who uses what it produces, and what a shallow result costs? Where it cannot, that is a finding, fixed by writing those sentences.

  第 25 行的 `words read that the run did not use` 后面加 `(orienting passages excepted)`。

- **B8**：`## Upstream examples` 表，加一行，并恢复一行。

  这张表现在没有一个例子示范"讲目的、讲态度"。`66089d06` 删掉了原来的两行：`| What skill text is for | engineering/implement/SKILL.md, engineering/grill-with-docs/SKILL.md | … |` 和 `| Redundancy and bloat | engineering/code-review/SKILL.md ## Why two axes | the one reason kept, because without it the agent would merge the axes |`。后一行是全表唯一示范"这条理由要留"的例子，而第 53 行还在引用它。

  > | What skill text is for | `engineering/wayfinder/SKILL.md` opening, `## Plan, don't do`, `## Fog of war`; `productivity/grilling/SKILL.md` last two paragraphs | purpose and stance in a few sentences, which the agent carries into cases no step names |
  >
  > | Redundancy and bloat | `engineering/code-review/SKILL.md` `## Why two axes` | the one reason kept, because without it the agent would merge the axes |

B1 到 B8 合计新增约 330 词，都放在修剪者动手前必读的位置：第 1 节、Redundancy 一节、Editing 一节、复审方法。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `### Rules and completion criteria` 第 123 行：`a step or a section that directs action without a completion criterion is a finding … states the criterion on a line beginning Done when` | "a section that directs action"的范围太宽。讲立场的一节（比如 `wayfinder` 的 `## Plan, don't do`）也在指导行动，却没有天然的完成标准。照字面执行，写的人会给每一节硬加一行 `Done when`，审的人会把立场段判成缺陷。`Done when` 这个字面前缀没有脚本解析（grep 过 `mmw-v2` 下所有 `.py`、`.sh`、`.mjs`），它只是全集的写法习惯（29 个文件里出现 84 次） | 改成：`In the set's own text, a step without a completion criterion is a finding, and so are two different statements of what "done" means for one task; the set writes it on a line beginning Done when.` 删掉"or a section"；缺标准才算缺陷，措辞不同不算 |
| C2 | `### Load and disclosure` 第 24 行：`The cut follows how often one agent enters the skill in one task. Entered once: … Entered at several moments: …, and the table that finds the reader's moment comes first in SKILL.md` | 这是一套拆文件的算法。原则（第 14 行第 4 条事实）加上 **jump**、**fragment** 两个缺陷名已经够用了。"comes first"会被读成"放在第一行"，结果就是 B5 列的那几个只有路由表的开头 | 保留约束本身：`the table that finds the reader's moment sits before any step with side effects, so a re-entering agent does not repeat them`；删掉"Entered once / several moments"的分支写法，交给第 4 条事实。省约 20 词，和 B5 一起改 |
| C3 | `REVIEWING-A-SKILL-SET.md` 步骤 2、5、6，以及 `SKILL-SET-REVIEW.md` 第 153 行 `with its load before and after reported` | 整套复审唯一被量化的是字数，收益一项都不量。于是"修复"在报表上就等于字数下降，复审天然朝删减走。2026-09-23 那一轮，`汇总.md` 记下"没有碰臃肿，正文总量没有减少"，记忆 `e83f457b` 把这一点记为上一轮的失误，随后就有了 `slim/b2` 到 `slim/b6` 一批"cut the reading load"提交 | 保留字数统计（用户在意 token），同时按 B7 把讲目的的段落排除在"没用到的字"之外，并加上步骤 4 那一问，让"缺少目的"也能成为一条发现 |
| C4 | 第 140 行加 `REVIEWING-A-SKILL-SET.md` 第 11 行：删减只要有字数就算证据充分，新增机制却必须指出出过问题的那次运行 | 用在机制上是对的，这是用户的裁定，要留。问题在于讲目的的文字被归进了"load"这一类：删它几乎不需要证据，补它又没有归属的类别 | 按 B6 写明：讲目的的段落不是机制，补它的依据是"只拿到这个技能的 agent 说不出这件事是为了什么" |
| — | `REVIEWING-A-SKILL-SET.md` 的六个编号步骤 | 不改。先报告、再改、改完重走，这个顺序是真的有依赖（用户要求先看报告再改），每一步也都有 `Done when` | — |

## 附加任务：`SKILL-SET-REVIEW.md` 是否把删减写成了主导方向

### 判断

是，但只针对一类内容。这份标准并不反对写理由：第 13 行的 `Direct, then trust`、第 53 行的 `These stay`、第 58 行的对照例子，都在防止过度删减。它的偏向在于，所有反向约束都只保护"帮 agent 做某个具体决定"的文字，而任务书说的"灵魂"那一类（这件事的意义、谁读它的产出、做浅了对全局的影响、该用什么态度去做）在标准里没有名字，也就没有位置。没有位置的东西，在一份逐句检验、只统计字数、默认修法是"删除或合并"的标准里，只能被当作负担。对任务书而言，这就是冲突：任务书说这类内容"绝对不是冗余"，标准却没有一条能把它认出来，反倒有好几条会把它归成 no-op、sediment 或"没用到的字"。

另一个结构原因是：`### Upstream skills` 保护了上游原文（`wayfinder`、`grilling` 里讲目的的段落因此一直没动），所以这个偏向的后果集中落在本仓自写的技能上，也就是 `dispatch`、`verify-ticket`、`implement`、`code-review`、`to-tickets`、`advisor` 这些承担夜间自动化、本来就最容易写成纯步骤的技能。

### 会让修剪者误删这类内容的条款（逐条）

1. 第 9 行 `Every check below serves these five facts about how an agent uses a set.` 加第 11 行 `Scripts carry what is deterministic; text carries judgement. … how to decide what no script can decide: what counts as done, which of two readings applies, what the user meant.` 五条事实里没有"理解"这一条，文本的职责被限定为做决策。用户 2026-09-23 的裁定写的是"思考与判断"（记忆 `e83f457b`），2026-09-11 的原则写的是"写技能的 agent 自以为知道的工作方式必须写进技能里"（记忆 `60e59dbe`），这两点都没有写进标准。修法：B1。
2. 第 12 行 `Material read at a moment that does not use it, a rule stated twice, and a case the agent would handle by default all thin the attention left for the judgement the text exists to guide.` 讲目的的段落不在任何一个 moment 里"被用到"，按这句就是在消耗注意力。修法：B1 最后一句给出另一种检验。
3. 第 13 行 `Upstream's implement is five lines … and trusts the agent with the rest. MMW's automation needs more than that, and each addition is paid for by a judgement the agent could not make without it.` 全标准唯一一个"好技能"的范例是一份五行、没有一句讲目的的技能，而新增内容只能用"判断"来付账。修法：B8 把 `wayfinder` 加为范例。
4. 第 36 行 `Each sentence is tested against what the agent would do without it … These are findings, fixed by deleting or merging:` 逐句检验。讲目的的段落是作为一个整体影响整个任务的，拆成单句来看，每一句单独拿掉似乎都"不改变行为"。而且这一节给的修法只有删除和合并两种。修法：B3 最后一句。
5. 第 40 行 `No-op: … or an attitude where an action would do ("be careful", "make sure").` 讲立场的句子会被归成"attitude"。修法：B4。
6. 第 43 行 `Sediment: text that is not about the task at hand now.` 加第 48 行 `the maintainer's reason for a design | an ADR`，以及第 50 行 `a source line ("from chapter 3 of …") … | nowhere`。

   这一行和前几轮删除的关系，证据如下：
   - `e74e0140`（2026-09-22，比这份标准早一天）的提交说明：`Removed dated incidents, maintainer-facing reasons, restatements and no-ops … Reasons cut from upstream skills are kept in their merge-notes; three reasons with no other home went into CONTEXT entries`。第二天的 `0cb30cd4` 把同一个分类写成了标准的 `### Body content` 表，也就是今天的 Sediment 表。
   - 一个我核实过的实例：`implement` `SKILL.md` 原有 `It is first because nothing else in this pipeline claims a ticket, and step 8 below cannot close one you do not hold.` 和 `because advance takes the claim off a ticket it re-dispatches and step 8 refuses a ticket that is not yours`，两句都在 `e74e0140` 删掉，现在只存在于 `mmw-v2/merge-notes/implement.md` 第 13 行（`为什么排第一（…）只写在这里`）。
   - 标准自己在第 30 行写着 `A rule for the worker written only in … a merge-note, or in this file reaches no worker`，`REVIEWING-A-SKILL-SET.md` 第 27 行也把 glossary、merge-notes、ADRs 列为 `files no running agent reads`。所以这一行的实际效果是：修剪者分不清"维护者的理由"和"执行者需要的理由"时，就把后者也搬到标准自己承认 agent 读不到的地方。
   - 协调者转述，`wayfinder`、`to-tickets`、`ui-acceptance`、`teach`、`code-review` 五个技能的调查员都发现了按这条路线删掉的目的句。这五处我没有逐一核实。
   - 第 50 行对 `codebase-design` 作者名出处的误伤，见 B2。

   修法：B2、B3。
7. 第 53 行 `These stay … a reason the agent needs to decide an edge case, or to keep a design choice it would otherwise simplify away`：保护范围只到"边缘情况"和"防止被简化的设计"。修法：B3。
8. 第 23–24 行 `SKILL.md holds what every task passes through, plus the table …`、`the table … comes first in SKILL.md`：造成了只有路由表的 `SKILL.md`。修法：B5、C2。
9. 第 123 行 `a step or a section that directs action without a completion criterion is a finding`：把讲立场的一节也判成缺陷。修法：C1。
10. 第 140 行 `A fix removes, merges, moves or simplifies before it adds.`：默认方向是删。修法：B6。
11. 第 142 行 `walk the task after the edit and confirm it still reaches its completion criterion`：这是删减的唯一检验，而它查不出讲目的的文字被删掉了。修法：B6。
12. `REVIEWING-A-SKILL-SET.md` 第 18 行 `which of its sections the step used`、第 25 行 `words read that the run did not use`、第 32 行和 `SKILL-SET-REVIEW.md` 第 153 行的前后字数对比：只量成本，不量收益。修法：B7、C3。
13. 上游 `SKILL.md` `## Pruning` 第 80 行 `mere exposition`、第 81 行 `Hunt no-ops sentence by sentence … delete the whole sentence rather than trim words from it`。这是上游原文，按边界不改；但本仓标准引用了它（第 36 行），所以标准需要自带上面那些对照。上游第 79 行 `the reason behind a choice` 就是现成的依据，B3 与它方向一致。

### 这条原则写在哪里、怎么写

主体是 B1，放在 `## What skill text is for` 的第 1 条，约 120 词。选这个位置，是因为第 9 行规定下面每条检查都服务于这些事实，原则放在这里，会约束全部检查，而不只是加一条例外。B2 到 B8 是配套的收窄和对照，分别放在修剪者动手时读的那几处：Sediment 表、No-op、`These stay`、Load 第一条、Editing、复审方法、范例表。只加 B1、不改后面这些，修剪者在具体条款上仍然会按原来的字面删。

### 标准自身的过度规定、冗余和死板之处

- **可以交给脚本的规则写成了文字**，与标准自己第 59 行的规定矛盾：YAML 冒号（A2）、手工 grep 清单（A3）、被检查文件里不能出现禁用 token（A4）、本仓技能只能有两个 frontmatter 键（第 68 行，并入 A2 的 lint）。先例现成：`check_upstream_em_dashes.py` 就是把一条文字规则变成了每个套件都跑的检查。
- **与别处重复**：拒绝信息的三个部分（A1，与 `CODING_STANDARDS.md` 重复，而且指错了文件）；user-invoked 技能的 description（A5，与 `SKILL-MECHANICS.md` 重复）；merge-note 和 downstream-note（A6，与 `AGENTS.md` 重复）；文件内部重复（A7）。
- **没有依据的断言**：数字限制那句（A8），而且和第 99 行自相矛盾。
- **死板**：`Done when` 要求覆盖到每一节（C1）；拆文件的算法和"表格放第一"（C2）；只量字数的复审报表（C3）。
- **不算问题的**：约 4,700 词对一份平铺的规则参考来说不算过长，上游 `SKILL.md` 第 34 行明说 `a legitimately flat peer-set … is a fine arrangement, not a smell`。我不建议拆文件：写技能的人本来就需要看到全部检查，拆开只会增加跳转。`### Vocabulary` 对比喻和口语的限制与用户全局提示词第 6、7 条一致，要留；讲立场的句子可以用 `SKILL.md` 意义上的 leading word 来写（`fog of war` 就是），第 75 行已经允许这种写法。

## 脚本

无。这个技能没有 `scripts/`。A2、A3 建议在 `mmw-v2/tests/lib/` 新增一个 lint；它属于测试库，写法照 `check_upstream_em_dashes.py`，由每个 `run.sh` 调用。

## 与其他技能的重复或交接问题

- `mmw-v2/merge-notes/implement.md` 第 13 行记着 `implement` 开工段"为什么 claim 排第一"的理由，并写明 `只写在这里`。运行中的 worker 读不到它。要不要放回 `implement` `SKILL.md` 的 `## Claim, read in, write the code`，应由 `implement` 的调查员判断。我只记录这件事，没有评估缺了这句会不会让 worker 做错。
- `code-review`：标准第 53 行拿上游 `code-review` 的 `## Why two axes` 当"理由要留"的例子。本仓 `code-review` 的 `SKILL.md` 已经没有这一节，但理由还在 `references/session.md` 第 91 行（`the separation is what keeps a passing axis from covering a failing one`）。两边一致，不用处理。
- `codebase-design` `SKILL.md` 第 22、107 行和 `DESIGN-IT-TWICE.md` 第 3 行的作者名出处：在 B2 落地之前，是上游保护规则（`### Upstream skills`）在拦着不让删；B2 落地之后，Sediment 表本身也不会再把它们判成缺陷。本仓自写的技能如果引用了作者名，只能靠 B2 来保护。
- `mmw-v2/skills/retro/SKILL.md` 第 127 行要求写 `prompt_change` 之前读本技能的 `SKILL.md`。如果目标文件是技能，`SKILL.md` 第 8 行会把它转到 `SKILL-SET-REVIEW.md`，交接是通的。
- 根 `AGENTS.md` 的 External References 第 49 行概述了 `SKILL-SET-REVIEW.md` 的内容。B1 落地后，那一行不需要改。

## 没查到的

- B1 到 B8 的效果没有验证。按标准自己的 `## Verifying`，需要让一个全新的 agent 拿着改后的标准，真正修剪一个本仓技能，看它会不会保留讲目的的段落。这一步没做，所以"这些草稿能改变修剪者的做法"是推断。
- 协调者转述的五个技能（`wayfinder`、`to-tickets`、`ui-acceptance`、`teach`、`code-review`）里被删的目的句，我没有逐一核实。我亲自核实过的只有 `implement` 的两句、`advisor` 的一句，以及 `codebase-design` 的作者名出处。
- `e74e0140` 删掉的理由句我只抽查了几条，没有逐条判断每句对 agent 是否必要。
- A3 的宿主名 lint 会有多少误报，没有测。
- 2026-09-23 那一轮的负担测量文档（`M4`、`M6`）没有提交进仓库，所以没能对照当时每条删减的具体依据。
- 没有读上游写给人看的 `mmw-v2/upstream/docs/productivity/writing-for-agents.md`，它不会被加载。
