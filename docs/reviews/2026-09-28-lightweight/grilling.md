# grilling

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能是你 9 月 16 日亲自定过做法的：思考那一整块"只摘录原文、精确修剪，禁止二次加工、精简"，并点名"惯例不是理由"一段与 "Where the path is already clear, first principles is overkill" 保持不动。之后两次减重（`e74e0140`、`95e05b11`）按"维护者理由放 merge-note"把其中几句删了，这与你的裁定冲突。那几句也正是"灵魂"：它们让 agent 在访谈现场知道为什么要先质疑前提、先删再优化。所以恢复原文。另外，你点名启动这组访谈的 8 次里，有 5 次在参数里要求"给背景、说直白、能自己定的别问我"，这说明技能缺一段"哪些决定交给用户、问题怎么写"。

### 增加（恢复原文，出自 `adae02f2`，一字不改）

| # | 位置 | 原文 | 它改变的选择 |
| --- | --- | --- | --- |
| R1 | 第 30 行 "challenge its premise: …" 之后 | An agent can ask excellent questions and still help refine something that should not exist. | 面对一份看起来成熟、你又很投入的计划时，agent 不会因为"质疑前提不礼貌"而直接进入细化。 |
| R2 | 第 32 行段末 | Otherwise you could get the perfect answer to the wrong question. | 让"先减需求"有理由，不被当成可跳过的一步。 |
| R3 | 第 34 行段后，新起一段 | "Industry standard is...", "We've always done it like this...", "Best practice says...", "That's just how it works..." are appeals to convention, not reasons. Ask: "But WHY? What fundamental truth makes this necessary?" | 第 34 行是抽象的分类规则，这一段是访谈里真会听到的原话，agent 靠它在现场认出"这是惯例，不是约束"。你点名这一段保持不动。 |
| R4 | 第 38 行 "Only then optimize or simplify what remains." 之后 | The most common mistake of smart engineers is to optimize a thing that should not exist. | 说明"删"为什么排在"优化"之前。 |
| R5 | 第 40 行 "distinguish the symptom, the proximate cause and the root cause." 之后 | The first answer is almost never the real problem. | 没有它，"列 5–7 个来源"会被当成仪式，agent 找到第一个说得通的原因就收手。 |
| R6 | 第 28 行第一句之后（移动并恢复）；同时删去第 36 行末 "; first principles is for where the path is not already clear" | Where the path is already clear, first principles is overkill. | 放行条件原来排在程序之后，agent 按顺序读，会先在每道推荐答案上跑一遍约束分类，读到第 36 行时已经跑完了。挪到整块开头，路径清楚的问题就直接给推荐答案。只移动和恢复原文，不改写。 |

### 增加（本仓新写的一段）

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | 第 26 行（"Finding _facts_ is your job … The _decisions_ are the user's: put each to them and wait."）之后。上游这一句不改，紧跟其后收窄它 | Put to the user only the decisions that are theirs. A choice their standing instructions leave to you, usually an engineering one, you make: state it with its reason in the recommended answer it bears on, where they can overrule it, and do not ask it. Write each question for a reader who has not read what you read: what raised it, and what each option does to the product, in plain words. A question the user has to ask you to explain has cost a round. | 证据是你的原话（`~/.claude/history.jsonl`，8 次里有 5 次），例如"说清楚前因后果，直白一点""修复方法明确或者你自己能找到最佳解法的不要问我"。第 26 行把所有决定都交给用户，与你全局规则第 1 条（工程决定归 agent）冲突；agent 访谈时照的是眼前这份技能，所以全局规则单独存在压不住它（09-10 那次投诉发生在全局规则进仓之后）。这段不复述全局规则的清单，只指向 "their standing instructions"。这也补上你 09-16 裁定的前半"能自己定的写进推荐答案"，那半句当时没有落到正文。 |

### 连带改动

- `mmw-v2/merge-notes/grilling.md` 第 11 行删去"这几条的理由只记在这里，正文不写"和"不写「行业惯例」「一直这么做」这类说法的列举"，改为说明这几句留在正文，因为 agent 现场判断要用；并为 I1 加一条记录，写明它是本仓新写的文字、依据是你的 5 次原话，不属于"摘录原文"那一块。

### 不采纳

- 调查员考虑过、自己也不建议补的"你的结论会被 `to-spec` 抄下去"：第 42 行 "nothing left silently assumed" 已经起同样的作用。

## 结论

`mmw-v2/upstream/skills/productivity/grilling/SKILL.md` 正文约 700 词，没有脚本，没有 reference。其中上游原文约 290 词（第 6–26 行和第 42 行），本仓加的只有第 28–40 行那一整块"形成推荐答案时要跑的思考"，411 词，比上游原文还长；`mmw-v2/merge-notes/grilling.md` 对这一块有一条记录，与现文一致。这一块不是废话：它是 2026-09-16 用户亲自主导加入的第一性原理思考，改变的是 agent 给出的每一道推荐答案，属于"灵魂"。它的问题方向相反：前两轮减重（`e74e0140` 2026-09-22、`95e05b11` 2026-09-23）把其中几句"为什么"压缩或删掉、移进了 merge-note，而 Nowledge Mem 记录的用户裁定是"只做原文摘录的精确修剪，禁止总结、精简，不要大幅删减"，并且点名"惯例不是理由"那一段"保持不动"。更要紧的缺口有真实使用证据：用户点名启动这组访谈的 8 次里有 5 次在参数里要求"给上下文、说直白、能自己定的别问我"，根源是第 26 行上游原文把所有决定都交给用户，和用户全局规则"工程决定归 agent"冲突，而且问题格式没要求带背景。结论：可删的词数约为 0；建议在第 26 行后补一段约 75 词、恢复约 90 词原文；上游部分的"事实去查"完整，但"决定交给人"在 MMW 里需要收窄；本仓部分的"灵魂"被削掉了一截。

## A. 删除或改成脚本

没有可删的。逐段核过：

| # | 位置 | 核查结果 |
| --- | --- | --- |
| — | 第 28 行 `Think through the paragraphs below…They add no rounds and do not change the question format.` | 不是 no-op：它把整块限定为推荐答案里的思考，防止 agent 把后面每一段都变成新的一轮提问。保留 |
| — | 第 34 行 `Keep only the first three as binding…` 与第 36 行 `If the constraint is verified physics, hard regulation, or measured capacity, accept it and optimize within it.` | 部分重叠（两句都说物理、法规、实测是硬约束），但第 36 行多了"在约束内优化"这个动作。按用户"同义只留更硬的一句"的标准，两句各有一半对方没有的内容，不算冗余。不建议动 |
| — | 第 38 行 `if you are not forced to put back at least 10% of what you delete…`、第 40 行 `Reflect on 5–7 different possible sources…distill those down to 1–2` | 数字是用户选定的原文摘录（Musk 的删减法则、三层归因排错），是思考的尺度，不是要脚本执行的限额。`SKILL-SET-REVIEW.md` `### Scripts and judgement` 说"数字限额由机制执行"，这里没有机制可执行，也不需要。保留 |
| — | 第 6–26 行、第 42 行（上游原文） | 上游原文，在 MMW 工作流里没有让 agent 做错的证据（见"与其他技能的重复或交接问题"）。不提 |

## B. 灵魂

### 保留，勿删

- 第 6 行 `Interview the user relentlessly until you reach a shared understanding.` 与 design tree 的定义：整个技能的目标句，结束条件（第 42 行）从这里推出来。上游原文。
- 第 8 行、第 24 行 frontier 与 rounds 的定义，特别是 `the questions you can ask _now_ without guessing at answers you haven't heard yet` 和 `A question whose answer depends on another question still open in this round belongs to a _later_ round`：告诉 agent 为什么一轮只问 frontier，而不是一个问题一个问题地问或一次问完。上游原文。
- 第 26 行 `Finding _facts_ is your job, never the user's…The _decisions_ are the user's: put each to them and wait.`：任务书点名的灵魂，事实去查、决定交给人。`SKILL-SET-REVIEW.md` `## Upstream examples` 也把这一段当 Hand-offs 的范例。上游原文。它的后半句在 MMW 里需要收窄（见下方缺口和 C2），但整句不删不改。
- 第 42 行 `nothing left silently assumed` 与 `Do not act on it until the user confirms…`：调用方（`wayfinder` 的结论评论、`triage` 的 triage notes、之后的 `to-spec`）都靠这一句保证拿到的是明说过的决定。上游原文。
- 第 28 行（见 A 表）：划定整块只进推荐答案、不加轮次。本仓加的，是用户 2026-09-16 的裁定"作为形成每一道推荐答案时要跑的检查，而不是新的一轮必答题"的落点。
- 第 30 行 `Should this exist at all?`、第 32 行 `so the question being answered is the least wrong one possible`、第 36 行 `first principles is for where the path is not already clear`、第 38 行 `Design for observed usage: no speculative edge cases, abstractions, or guards…`、第 40 行 `let a failure surface rather than adding a guard that silences it` 与 `If an answer blames a person, redirect to the process behind them.`：每句都直接改变推荐答案的内容（先问该不该存在、先减需求、不做推测性设计、不用守卫掩盖失败）。本仓加的，下一轮修剪最容易把它们当"态度句"删掉，它们不是。

### 缺口与补充草稿

**背景（证据）。** 这一块最初由 `adae02f2`（2026-09-16）加入。Nowledge Mem 里同日的几条用户裁定（标题"grilling改造须原文摘录精确修剪后整块组装，禁止二次加工""grilling改造硬约束：不改工作流、只摘录原文、加深思维""grilling覆盖全部调用场景并排除Working Backwards"）要求：新增内容只能是原文摘录的精确修剪，"禁止二次加工、曲解、总结改写、精简"，"不要走极端大幅删减"，并明写"「惯例不是理由」以及 Where the path is already clear, first principles is overkill 等整段适用的句子保持不动"。之后 `e74e0140`（提交说明："Removed … maintainer-facing reasons … Reasons cut from upstream skills are kept in their merge-notes"）和 `95e05b11`（M4 load measurement）把下列原文删去或改写，merge-note 第 11 行随之写成"这几条的理由只记在这里，正文不写"。两次提交说明里都没有这一块经用户同意的记录（我只查了提交说明和 Nowledge Mem，没查当时的会话记录）。

这几句被当成"维护者的设计理由"处理了，这是误用：`SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 Sediment 表把"the maintainer's reason for a design"送去 ADR，但同一节"These stay"一段明确保留"a reason the agent needs to decide an edge case"。这些句子是 agent 在访谈当下判断"这一步该不该先做"的依据，属于后者。这里 `SKILL-SET-REVIEW.md` 的偏删倾向和任务书的"灵魂"要求冲突，以任务书为准。

- 第 30 行（质疑前提）：只剩命令，没有理由。缺了理由，agent 遇到一份看起来成熟、用户很投入的计划时，会觉得质疑前提不礼貌、多余，直接进入细化。恢复 `adae02f2` 原文一句，接在 `challenge its premise:` 那句之后：
  > An agent can ask excellent questions and still help refine something that should not exist.
- 第 32 行（减需求）：同上。恢复原文一句，接在段末：
  > Otherwise you could get the perfect answer to the wrong question.
- 第 38 行（先删后优化）：`Only then optimize or simplify what remains` 只给了顺序，没说为什么删必须排在优化之前。恢复原文一句，接在 `Only then optimize…` 之后：
  > The most common mistake of smart engineers is to optimize a thing that should not exist.
- 第 40 行（失败分析）：`Reflect on 5–7 different possible sources` 没有理由时，agent 会把它当仪式，找到第一个说得通的原因就收手。恢复原文一句，放在 `distinguish the symptom, the proximate cause and the root cause.` 之后：
  > The first answer is almost never the real problem.
- 第 34 行之后（惯例不是理由）：`95e05b11` 删掉的整段，merge-note 给的理由是"约束分类那一段已经要求惯例拿出独立的支持"。但第 34 行是抽象的分类规则，这一段给的是用户在访谈里真会说出口的原话，是 agent 在现场认出"这是惯例、不是约束"的线索；用户裁定它"保持不动"。按 `e74e0140` 修剪后的版本恢复为一段：
  > "Industry standard is...", "We've always done it like this...", "Best practice says...", "That's just how it works..." are appeals to convention, not reasons. Ask: "But WHY? What fundamental truth makes this necessary?"
- **第 26 行之后（最重要的缺口，有真实使用证据）：哪些决定交给用户，以及每个问题要带什么背景。** 证据：`~/.claude/history.jsonl` 里用户直接点名启动这组访谈共 8 次（`/grill-with-docs` 5 次、`/grill-me` 3 次，2026-08-20 至 09-10；`~/.codex/history.jsonl` 没有）。其中 5 次在参数里提同一类要求：
  - 08-24 `/grill-with-docs`："你在向我提问的时候，一定要记得向我提供相关的上下文……不要给我一些我根本看不懂的、虚无缥缈的东西"
  - 08-27 `/grill-with-docs`："重新问一遍你的问题，我看不懂你的问题，说清楚前因后果，直白一点"
  - 09-02 `/grill-me`："向我直白地解释所有需要我拍板的决定……注意修复方法明确或者你自己能找到最佳解法的不要问我"
  - 09-02 `/grill-with-docs`："从业务意图和功能设计的角度去向我解释、提问和给出建议，只向我解释最必要的技术性细节"
  - 09-10 `/grill-me`："重新向我说明需要我决定的事情并给出建议"

  另外 3 次（08-20、08-23、08-27 13:40）说的是先调查、一个个讨论，和第 26 行已有的"事实自己查"一致。（调度方转来的说法是"5 次都在要求"；核实结果是 8 次里有 5 次。）

  这说明两件事在本技能里缺了。第一，**谁来决定**：第 26 行 `The _decisions_ are the user's: put each to them and wait.` 把所有决定都交给用户，而用户的全局规则 `mmw-v2/prompt/shared.md` 第 15 行（rule 1）是"Engineering decisions are yours; product decisions are mine"。两者冲突时，agent 在访谈里照的是眼前这份技能，于是把本该自己定的工程问题也抛给用户。09-10 那次投诉发生在 `shared.md` 进仓（`6fc8857e`，09-05）之后，说明全局规则单独存在时压不住本技能这一句。用户 09-16 的裁定"能自己定的写进➡️，只有用户必须拍板的才升成 frontier 问题"（Nowledge Mem"思考规程并入同一份grilling SKILL.md，作为推荐答案检查"）说的也是这件事，但现文没有落下来：第 28 行只写了后半 `They add no rounds`。第二，**问题带什么背景**：第 13 行的格式只说 `question body, might be multiple paragraphs`，没说问题写给谁读。用户没读过 agent 读过的材料，拿到的是一道缺前因后果、满是技术细节的题。

  建议在第 26 行之后加一段本仓自己的文字（不改第 26 行上游原文，按 `SKILL-SET-REVIEW.md` `### Upstream skills`"Connect outside the upstream text first"，紧跟在它后面收窄它），并在 `mmw-v2/merge-notes/grilling.md` 加一条：
  > Put to the user only the decisions that are theirs. A choice their standing instructions leave to you, usually an engineering one, you make: state it with its reason in the recommended answer it bears on, where they can overrule it, and do not ask it. Write each question for a reader who has not read what you read: what raised it, and what each option does to the product, in plain words. A question the user has to ask you to explain has cost a round.

  这段不复述 `shared.md` rule 1 的清单（客户可见、钱、范围、不可撤回），只指向"their standing instructions"，避免两份清单各改各的。它也同时覆盖用户 09-16 裁定的前半，所以第 28 行不用再改。它改变的做法是：工程选择不再成为问题，而是写进推荐答案，用户能看到、能否决；每道问题先交代来由和后果再问。剩余风险：在没有这类全局规则的 host（Cursor 的用户级 prompt 在应用里维护，我没核对）上，"their standing instructions leave to you"找不到依据，agent 会按第 26 行原样把决定都交给用户，这就是现状，不会更坏。

恢复原文和新增一段合计，正文约增加 165 词。同时要改 `mmw-v2/merge-notes/grilling.md` 第 11 行：删掉"这几条的理由只记在这里，正文不写"和"不写「行业惯例」「一直这么做」这类说法的列举"两处，改为说明这几句留在正文、理由是 agent 现场判断要用；并为第 26 行之后新增的一段加一条记录。

考虑过但不建议补的：一句"你的结论会被 `to-spec`、结论评论、triage notes 抄下去"。第 42 行 `nothing left silently assumed` 已经起到同样的作用，再补是空话。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| 1 | 第 34 行 `Classify each claimed constraint as…For each convention, state a falsifier.`，而放行条件在其后的第 36 行末 `first principles is for where the path is not already clear` | 放行条件出现在程序之后。按顺序读的 agent 先读到"对每条约束分类、每条惯例给证伪条件"，会在每一道推荐答案上都跑一遍，包括那些路径早已清楚的问题；读到第 36 行时已经跑完了。用户裁定原话是"路径已经清楚时 first principles 是 overkill，不是每轮必走的仪式" | 把放行条件提到整块开头，用 `adae02f2` 的原文（用户点名"保持不动"的那句），放在第 28 行第一句之后：`Where the path is already clear, first principles is overkill.`；第 36 行末的 `; first principles is for where the path is not already clear` 随之删掉，避免说两遍。只移动和恢复原文，不改写，符合用户对这一块"只摘录不改写"的要求 |

| 2（上游原文，单独列出） | 第 26 行 `The _decisions_ are the user's: put each to them and wait.` | 一条不区分决定种类的硬规则：每个决定都要问、都要等。在 MMW 里它确实让 agent 做错了（B 节第 26 行之后那一条的 5 次用户原话），因为它和用户全局规则 rule 1 冲突，而 agent 访谈时照的是本技能 | 不改这句上游原文，在它后面接 B 节草稿那一段收窄它：只有属于用户的决定才问，其余写进推荐答案。若接上之后仍观察到 agent 把工程问题抛给用户，再按 `SKILL-SET-REVIEW.md` `### Upstream skills`"An upstream sentence changes only when an agent reading it would act wrongly … even with the connecting text in place"改这一句本身 |

其余没有死板的结构：rounds、frontier、问法格式都是上游原文，合并说明规定"上游改就收上游"；本仓的一整块是思考方式，不是编号步骤。

## 脚本

无。

## 与其他技能的重复或交接问题

调用方逐个核过（`grep -rn grilling mmw-v2/ docs/agents/`）：

| 调用方 | 位置 | 交接是否成立 |
| --- | --- | --- |
| `grill-with-docs` | `mmw-v2/upstream/skills/engineering/grill-with-docs/SKILL.md` 第 7 行 `Read the grilling and domain-modeling skills' SKILL.md and run this session as both describe.` | 成立 |
| `grill-me` | `mmw-v2/upstream/skills/productivity/grill-me/SKILL.md` 第 7 行 | 成立，见 `grill-me.md` 报告 |
| `triage` | `mmw-v2/upstream/skills/engineering/triage/SKILL.md` 第 78 行 第 4 步 `Grill (if needed)` | 成立；grilling 结束后回到第 5 步 `Apply the outcome`，triage notes 模板第 110 行接住 grilling 的结果 |
| `improve-codebase-architecture` | `mmw-v2/upstream/skills/engineering/improve-codebase-architecture/SKILL.md` 第 64 行 `### 3. Grilling loop` | 成立 |
| `wayfinder` | `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` 第 78、110、123 行 | 有两处问题，见下 |
| `write-screen-contract` | `mmw-v2/skills/write-screen-contract/SKILL.md` 第 87 行 `it is a grilling, not a form` | 用作普通名词，没有要求加载本技能；在 alignment ticket 里本技能已经由 `wayfinder` 第 78 行加载。不算问题 |
| `ask-matt` | `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 16、80、81 行 | 路由描述与本技能一致 |

1. **`wayfinder` 用 "round" 指整场访谈，和本技能的术语冲突。** 第 78 行 `run this round as both describe`、第 110 行 `run this round as both describe, to pin down what this map is finding its way to`。本技能第 8 行把 **round** 定义为"一批 frontier 问题"，一场访谈有很多轮。一个同时加载两份技能的 agent 可能把"run this round"读成"问一轮就收"。这两处措辞是本仓为 host 中立改写时引入的（上游原文是 `Call the Skill tool twice, for "grilling" and "domain-modeling"`，见 `mmw-v2/merge-notes/wayfinder.md` 第 19 行）。改在 `wayfinder` 一侧：写成 `run this session as both describe`（与 `grill-with-docs` 第 7 行一致）。本技能不动。本批 `wayfinder.md` 报告没有记这一条。
2. **`wayfinder` 画地图时，本技能的结束条件会把 agent 往"全部解决"方向推。** 本技能第 42 行 `The session is done when the frontier is empty: every branch of the design tree visited`；而 `wayfinder` `### Chart the map` 第 2 步要的是广度优先地"surfacing the open decisions"，把它们变成票，第 6 步才说 `charting…hand-resolves nothing`，这条规则排在 agent 已经访谈完之后。这是上游两份原文放在一起的效果，没有找到真实出错的证据（本仓只有两张地图 #18、#542，#542 的决定票是试点，答案取自生产版）。按 `SKILL-SET-REVIEW.md` `### Hand-offs`"A sentence written for one caller can misread under another"，如要处理，改在 `wayfinder` 第 2 步加半句（例如 `each open decision becomes a ticket rather than being settled here`），本技能不动。
3. **失败分析的数字和 `diagnosing-bugs` 不同。** 本技能第 40 行 `5–7 different possible sources…distill those down to 1–2`，`mmw-v2/upstream/skills/engineering/diagnosing-bugs/SKILL.md` 第 90 行 `Generate 3–5 ranked hypotheses`。两者场景不同（一个是访谈里给推荐答案，一个是真在排错，有复现回路），同一个 agent 一般不会同时加载。只记录，两边都留。
4. **问法格式的副本。** `mmw-v2/skills/manage-agents-md/SKILL.md` `### Format` 抄了本技能第 12–22 行的问法格式，`manage-agents-md.md` 报告 A9 已记录，并说明为什么那边留副本。本技能这边保留原件。

## 没查到的

- 用户原话的证据只来自 `~/.claude/history.jsonl` 里斜杠命令的参数，没有读那几场会话里 agent 实际问了什么；"问题缺背景、把工程问题抛给用户"是从用户的纠正反推的。8 次都发生在 09-16 第一性原理那一块加入之前，之后没有点名记录，所以那一块对这个问题是好是坏没有证据。
- 没有找到本技能在真实会话里运行这一块思考的记录（没有读会话记录；tracker 上的 grilling 类型票 #543–#554 是试点，结论评论里看不出推荐答案是怎么形成的）。所以"第 34 行会被跑成仪式"（C1）是按文本推断的，不是观察到的。
- `e74e0140`、`95e05b11` 两次删减是否经用户当面同意：只查了提交说明和 Nowledge Mem，没查当时的会话。如果用户当时同意过，B 里恢复原文的几条就降为建议，而不是按既定裁定恢复。
- 没有核对各 host（Codex、Grok、Pi）对第 26 行 `dispatch a sub-agent` 的支持情况；这是上游原文。
