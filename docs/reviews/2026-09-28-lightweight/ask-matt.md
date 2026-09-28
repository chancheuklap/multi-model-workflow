# ask-matt

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：上游把 ask-matt 写给自己敲命令的用户看，本仓改成了模型也能触发，但正文没有跟着改。这带来三个问题：
- 它指向的 7 个技能只能由用户点名启动，agent 读到这些路线时，不知道该怎么办。
- 做原型那一步要求用 `handoff` 开新会话来回走一趟，理由是"prototype 在别的目录"，在本仓不成立。照字面做，`to-spec` 会在一个只拿到摘要的会话里写 spec。
- 主流程第 3 步的 Yes/No 在本仓还决定了谁来检查这份工作，正文没有说。

上游讲"阶段边界"与"上下文卫生"的判断句都保留。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 第 8 行 "You don't remember every skill, so ask." 之后 | You may be the user, or an agent asking on the user's behalf. The answer is a route: the skill or sequence, and why it fits better than its nearest neighbour here. Some skills here start only when the user names them; when the route begins with one you cannot load, give the user its name and the reason, and do not rebuild it from its line here. `grill-with-docs` is the exception: it is the `grilling` and `domain-modeling` skills run together, and you can read both. | 路线的第一步是 agent 加载不了的技能（`grill-with-docs`、`handoff` 等 7 个）时：没有它，agent 要么照这里的一行介绍自己仿造一个流程，要么卡住。#538 记录过这种代价："an agent that cannot find the next step invents one"。 |
| I2 | 第 3 步 Yes/No 两条之后 | In this repository the branch also decides who checks the work: the **Yes** path gives every ticket acceptance criteria a script runs, a reviewer in its own session, and a closed ticket as the record; the **No** path has none of these. Take **No** only for a change small enough that the user will check it directly. | 原文只按"会话够不够长"来分，这句补上本仓特有的后果：走 No，就没有自动判据、没有 reviewer、没有关票记录。 |
| I3 | 第 2 步界面段末 "…prototype through contract, before **the `to-spec` skill**." 之后 | With no map, this conversation is the only record of the decisions the contract cites, and its gap list waits on the user's answers. | 给"无 map 时一个会话从原型做到合同"一个理由，agent 不会在中途开新会话把决定丢掉。 |
| I4 | 文件末（`## Standalone` 之后） | This map ends where tickets are published. Running a night, verifying and closing a ticket, a release and a retrospective belong to the `dispatch`, `verify-ticket`, `exe-release` and `retro` skills. When neither this map nor those fit, tell the user so instead of assembling a flow of your own. | 路由表的边界；最后一句防止 agent 自己拼一条流程。 |
| I5 | 第 2 步三条固定步骤（`handoff` 出去、做原型、`handoff` 回来）替换为右栏（上游原文，按 `SKILL-SET-REVIEW.md` 的例外条件修改，并在 merge-note 加一行） | Run the prototype in this session when it fits the smart zone: it lives under `prototypes/` in this checkout, and it needs the grilling as its source. Hand off only for a reason on `PHASE-BOUNDARIES.md`'s question 3, such as a host with the Claude Design tools for step 2's interface branch. | 原步骤的前提（原型在别的目录）在本仓不成立，而且与同一文件的界面段（"goes on, not back"）和 `### Context hygiene`（第 1–3 步留在同一个上下文窗口）矛盾；`handoff` 也只能由用户触发。 |

### 删除或改正

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | description 中间一句 "A router over the upstream skills in this repo and the `design-pages` and `write-screen-contract` skills beside them." | 改为只写触发条件："Ask which skill or flow fits your situation. Use when you know what you want to do, from an idea to published tickets, a bug or a merge conflict, but not which skill does it, or when you are choosing what to do at a phase boundary."；merge-note 第 12 行同步 | 你定过 description 只写触发条件；"upstream"是维护者用语，"in this repo"在消费仓库里也不成立。改完要开新会话才生效。 |
| D2 | 第 27 行 "A dispatched worker loads **the `implement` skill**, which builds its ticket by driving **the `tdd` skill** internally…" | 改为："A ticket is built by the `implement` skill, in a session `dispatch` started or one that adopted the ticket (the `dispatch` skill's `references/inside-a-ticket.md`); a reviewer in its own session runs the `code-review` skill on that ticket's diff. `code-review` has no use on a branch or PR without a ticket."；merge-note 第 13 行同步 | 两处不准：worker 自己不跑 `code-review`；自己接手的票（`adopt`）这条路原文漏了。 |
| D3 | `## Standalone` prototype 条目中讲原型处置方式的两句 | 压成 "What happens to the prototype and its answer is the `prototype` skill's rule 6; a winning UI variant goes on to Claude Design (step 2)."；merge-note 写明上游讲处置的那句不收 | 同一个意思写了三遍，还复述了别的技能的规则。 |

### 不采纳

- R3（`diagnosing-bugs` 并不交接给 `improve-codebase-architecture`）：这是上游两份文件之间的不一致，在本仓影响很小，登记，不改。

## 结论

`mmw-v2/upstream/skills/engineering/ask-matt/` 共两份正文：`SKILL.md` 2176 词（上游 1769 词），`PHASE-BOUNDARIES.md` 737 词（上游 699 词），另有 `agents/openai.yaml` 一份元数据，没有脚本。多出来的约 450 词，大半是 host 中立改写（`/x` 改成 `` the `x` skill ``，每处多两个词），真正新增的内容只有主流程第 2 步的界面段（152 词）和 description 的两处补充。本仓的改动基本上没有堆砌，可删的只有约 80 词，集中在三处：description 里 agent 用不上的范围说明、第 3 步末段对 `implement` 内部流程的复述、Standalone 里 prototype 条目对第 2 步的重复。

路由表逐条核对的结果：大多数路线在当前技能集里真实可走，有四处不成立或不完整。最重要的一处是本仓把 ask-matt 改成了模型可触发，但它指向的技能里有 7 个只能由用户点名启动（包括主流程的起点 `grill-with-docs`），而正文从没告诉 agent 遇到这种路线该怎么办。第二处是第 2 步用 `handoff` 往返做 prototype 的理由（"a prototype lives in its own directory"）在本仓已经不成立，而且和本仓自己加的界面段、`### Context hygiene` 互相矛盾。

这个技能的"灵魂"基本完整，主要在上游原文和 `PHASE-BOUNDARIES.md` 里，应当整体保留。缺的是三句话：读者是谁、拿到路线后怎么做；在本仓选择第 3 步 Yes 还是 No，除了会话长短还关系到有没有人检查；无 map 时为什么必须一个会话做完。

使用证据：在 `~/.claude/projects` 的全部会话记录里，Skill 工具调用 ask-matt 的次数是 0，`/ask-matt` 的斜杠调用也是 0（作为对照，`code-review` 被调用了 643 次）。`~/.codex/sessions` 里只有 2026-09-16 的一个会话打开过安装位置的 `ask-matt/SKILL.md`，而那个会话是在为移植内容调研技能集，不是用它选路线。

## 路线逐条核对

核对方法：对每条路线，打开被指向的技能，确认该技能真的做 ask-matt 说它做的事，并确认它交出去的方向与 ask-matt 写的一致。依据是 `mmw-v2/skills.txt`（决定安装哪些技能）以及每个技能的 frontmatter。

**可走，与被指技能的 description 一致（不列证据细节）**：`grill-with-docs`（它的全文就是一句"Read the `grilling` and `domain-modeling` skills' `SKILL.md`"）、`to-spec`、`to-tickets`（`### 5. Give each ticket its blocking edges` 和第 7 步发布时使用原生 blocking link，完成后交给 `dispatch`）、`dispatch`（一个 night，或 night 之外的一张票，对应其 `## Find your moment` 的第 3、4 行）、`tdd`、`triage`（`SKILL.md` 第 5 步 `ready-for-agent` 送进 `to-spec` 再送进 `to-tickets`，并处理退回 `needs-triage` 的票）、`wayfinder`（decision tickets；design ticket 与 alignment ticket 见其 `references/interface-and-remake.md`；清图后交给 `to-spec`）、界面链（`design-pages` 的 `references/edit-pages.md` `## Next` 指向 pull，`references/pull.md` `## Reached from here` 指向 `write-screen-contract`，`write-screen-contract` `## Next` 指向 `to-spec`，`to-spec` 第 2 步读 screen contract）、`prototype`（`prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/`，UI winner 交给 Claude Design）、`improve-codebase-architecture`（内部运行 `grilling`，并使用 `codebase-design` 的词汇）、`domain-modeling`、`codebase-design`（`tdd` 的 `SKILL.md` 第 26 行指向它）、`grill-me`、`grilling`（rounds、frontier，"Finding _facts_ is your job"）、`resolving-merge-conflicts`（"never `--abort`"，第二种触发与其 description 一致）、`research`（background agent）、`to-questionnaire`、`wizard`（`.env` 与 GitHub secrets）、`wait-what`（使用 `CONTEXT.md` 词汇）、`teach`、`writing-for-agents`、`setup-matt-pocock-skills`。

**不成立或不完整的四处**：

| # | 路线（`SKILL.md` 行号 + 原文开头） | 问题 | 证据 | 来源 |
| --- | --- | --- | --- | --- |
| R1 | 全文，最显眼的是第 16 行主流程第 1 步 "**the `grill-with-docs` skill** sharpens the idea… Start here" | ask-matt 本身是模型可触发的，但它指向的 `grill-with-docs`、`grill-me`、`handoff`、`teach`、`wait-what`、`improve-codebase-architecture`、`setup-matt-pocock-skills` 这 7 个技能带着 `disable-model-invocation: true`，agent 无法自己加载。正文没有说明遇到这类路线该怎么办；唯一的暗示是第 86 行 wizard 条目里的 "Model-invoked, so the agent reaches for it"，以及第 57 行的 "Two model-invoked references" | 7 个技能各自 frontmatter 里的 `disable-model-invocation: true`；本会话（Claude Code）的可用技能列表里恰好缺这 7 个。上游 `writing-for-agents` 的 `SKILL-MECHANICS.md` `## Router skills` 说路由技能 "can only hint, never fire them"，这个前提是路由技能本身由用户触发；本仓的 `mmw-v2/merge-notes/ask-matt.md` 第一行删掉了 `disable-model-invocation`，读者因此变成了 agent，正文却没有跟着改 | 本仓改动带来的后果 |
| R2 | 第 17–20 行第 2 步 "bridged by **the `handoff` skill** in both directions (a prototype lives in its own directory, which is exactly what the `handoff` skill is for…)" | 在本仓，prototype 住在同一个 checkout 的 `prototypes/` 下（`prototype/SKILL.md` 规则 1；`mmw-v2/merge-notes/prototype.md` 规则 6 一行："**没有** throwaway branch"），括号里的理由不成立。更大的问题是三处互相矛盾：本仓在第 22 行加的界面段说 UI 的答案 "goes on, not back"，而且无 map 时 "in a single session… prototype through contract, before the `to-spec` skill"；第 31 行 `### Context hygiene` 又要求第 1–3 步留在 "one unbroken context window"。按字面照做，agent 先 handoff 出去开新会话做 prototype，界面链不回原会话，`to-spec` 就会在一个没有 grilling 原文、只拿到 handoff 摘要的会话里写出来，而这正是 `PHASE-BOUNDARIES.md` 第 1 问要避免的情况 | 同左列三处原文；`handoff` 把文件写进操作系统临时目录（`handoff/SKILL.md` 第 8 行），而且 agent 无法自己触发它（见 R1） | 上游原文，被本仓的 prototype 改动变成错的 |
| R3 | 第 43 行 "Its post-mortem hands off to **the `improve-codebase-architecture` skill**" | `diagnosing-bugs` 里没有这个交接。`## Phase 5` 第 120 行只写了 "Flag this for the next phase"，`## Phase 6: Cleanup` 也没有指向任何技能。上游 5b1a4c51 那一版同样没有，所以这是上游自己路由表过期 | `grep -n "improve-codebase-architecture" mmw-v2/upstream/skills/engineering/diagnosing-bugs/` 没有结果 | 上游原文。在本仓的影响低：agent 最多是找不到一个本来就不存在的交接，而且 `improve-codebase-architecture` 由用户点名触发。建议不改，只登记 |
| R4 | 第 27 行 "A dispatched worker loads **the `implement` skill**… then closes out with **the `code-review` skill** on the ticket's diff" | 两处不准确。(a) worker 自己不跑 `code-review`：`implement` 的 `## Closing steps` 第 3 步是 `<dispatch> start <n> reviewer`，由另一个会话里的 reviewer 加载 `code-review`。(b) 不只 dispatch 起的 worker 能做票：`implement` 的 description 写了 "or picked one up yourself"，`dispatch` 的 `## Find your moment` 第 2 行（`references/inside-a-ticket.md`，`adopt`）就是这条路，而路由表没有收它 | 同左列 | 本仓改写的段落，见 A2 |

**description 重复检查**：ask-matt 的 description（"Use when you know what you want to do but not which skill does it, or when you are choosing what to do at a phase boundary"）与 `mmw-v2/skills.txt` 里任何一个技能的 description 都不重叠。唯一与它争同一类触发的是本机的 `find-skills`（`~/.agents/skills/find-skills`，不属于 MMW，"how do I do X"），这一点只登记。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `SKILL.md` 第 3 行 description 中间一句 "A router over the upstream skills in this repo and the `design-pages` and `write-screen-contract` skills beside them." | 2 | "upstream" 是维护者才懂的 subtree 用词，加载技能的 agent 分辨不出哪些技能算 upstream。"in this repo" 在消费仓库里是假的：技能是 symlink，指向 MMW 的 `.worktrees/mmw-installed`，并不在当前仓库里。用户已裁定 description 只写触发条件。`mmw-v2/merge-notes/ask-matt.md` 第 12 行说加这句是为了不做"假承诺"，这个目的放进触发条件里说也能达到 | 范围改由触发条件本身来限定；正文 `## The main flow` 各节已经列出覆盖了什么。剩余风险：没有 | 改成一句：`Ask which skill or flow fits your situation. Use when you know what you want to do, from an idea to published tickets, a bug or a merge conflict, but not which skill does it, or when you are choosing what to do at a phase boundary.` 同时改 merge-note 第 12 行的"取舍规则"。约省 15–20 词 |
| A2 | `SKILL.md` 第 27 行 "A dispatched worker loads **the `implement` skill**, which builds its ticket by driving **the `tdd` skill** internally…" | 2、6（外加 R4 的不准确） | 这段复述了 `implement` 的内部步骤：驱动 `tdd`，收尾经 `code-review`。选路线的读者并不启动 worker，worker 的路线由它的启动 prompt 和 `implement` 给出。真正有用的只有后半句 "it has no use on a branch or PR without a ticket"，它防止一种真实的误用：`code-review` 被调用过 643 次，拿去审分支是很自然的误读 | `implement`、`dispatch` 自己的正文。剩余风险：没有 | 改成：`A ticket is built by the `implement` skill, in a session `dispatch` started or one that adopted the ticket (the `dispatch` skill's `references/inside-a-ticket.md`); a reviewer in its own session runs the `code-review` skill on that ticket's diff. `code-review` has no use on a branch or PR without a ticket.` 字数大致不变，主要是纠正错误。同步 merge-note 第 13 行第 (3) 项，以及它的理由"只有 `dispatch` 起的 worker 进得去"（这与 `adopt` 矛盾） |
| A3 | `SKILL.md` 第 83 行 Standalone 的 prototype 条目，"A logic or implementation answer folds into the real code, rewritten to production standard; a winning UI variant does not… iterated the next time the same question comes up." | 6 | 同一个意思出现了三遍：第 22 行的界面段、`prototype/SKILL.md` 规则 6，以及这里。路由读者要知道的是什么时候去找 prototype，prototype 怎么处置是那个技能自己的规则（`SKILL-SET-REVIEW.md` `## What skill text is for` 第 5 条："never restates another skill's rules"） | `prototype/SKILL.md` 规则 6 和第 22 行。剩余风险：上游这一句原本也在讲处置方式（throwaway branch），整句删掉以后，下次拉 upstream 时上游那一句可能被自动合回来 | 把这两句压成 `What happens to the prototype and its answer is the `prototype` skill's rule 6; a winning UI variant goes on to Claude Design (step 2).`，并在 `mmw-v2/merge-notes/ask-matt.md` 第 17 行写明"上游讲处置的那句不收"。约省 45 词。优先级低 |

没有发现第 1 类（脚本可以代替）和第 3 类（历史碎碎念）的内容。`SKILL.md` 第 64 行与 `PHASE-BOUNDARIES.md` 第 9 行那句一模一样的 host 中立说明，不算冗余：`SKILL-SET-REVIEW.md` `### Paths, tokens and host neutrality` 要求凡是点名 Clear 或 Compact 的文件都各带一次这句话，这两份文件都点名了。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 8 行 "You don't remember every skill, so ask."：一句话说清这个技能存在的原因。
- `SKILL.md` 第 10 行 flow / main flow / on-ramps / standalone 这一组概念：读者靠它判断自己处在地图的哪一层，而不是去找一个技能名。
- 第 16 行第 1 步括号里的理由 "`grill-with-docs` is the one that leaves a paper trail, which makes it the better of the two whenever a repo is there"：agent 靠它在两个入口之间做判断。
- 第 22 行本仓加的界面段，尤其是 "A UI question's answer goes on, not back"、"Only then does step 3 have something to write a spec from"、"Each of those skills' closing section names the next, so you do not come back here between them"。无 map 的界面走法全工具箱只写在这里（`b64c2d3a` 的提交说明和 #538 记录了缺这一段时发生过什么）。
- 第 29–33 行 `### Context hygiene` 两段：说明为什么 grilling、spec、tickets 要在同一段思考里完成，以及接近 smart zone 时不要硬撑。
- 第 41 行 "Triage is for issues **you didn't create**… **don't triage them**"：防止一个真实的误用，即把自己切的票再 triage 一遍。
- 第 43 行 "It refuses to theorise until it has a **tight feedback loop**"：一句话告诉读者 diagnosing-bugs 的思考方式。
- 第 45–47 行 wayfinder 条目："decisions, not deliverables"、"never a well-scoped feature"、"**it hands off, it doesn't build**"、"Building straight from the map skips that collapse and throws the linked detail away"。这几句说的是选错路线的代价。
- 第 53 行 "It's the survey that finds the candidates; **the `codebase-design` skill** is the bench"，以及第 57 行 "when the **words**, not the process, are the problem"：用来区分两个相邻技能的判据。
- 第 84 行 "research feeds the thinking rather than replacing it"、第 86 行 "If the agent could just do it itself, it should"、第 87 行 "the `grill-with-docs` skill is the upfront cure"：各自说明了一个技能该用在哪里、不该用在哪里。
- `PHASE-BOUNDARIES.md` 整份，特别是：第 5 行 "Compacting mid-phase makes the agent lose the thread"；第 23 行 "the implementation wants the reasoning verbatim, not a summary of it… rule it out before anything else"；第 27 行 "The cost of getting this wrong is one-way… no amount of reading the diff back gets it returned"；第 42 行 "a fresh session that is confidently wrong about a decision the summary flattened"；`## Primary and secondary sources` 那张表；`## These are judgement calls` 整节。这份文件用道理说明一个判断，而不是给出一套 SOP。

`git log -p --since=2026-09-15` 查过 `ask-matt` 目录：前几轮只改了路线的去向和措辞，没有删掉思想性段落，没有需要恢复的原文。

### 缺口与补充草稿

- **`SKILL.md` 第 8 行之后：读者是谁、拿到路线后做什么（对应 R1）。** 上游的读者是用户本人，看完自己敲命令。本仓让模型可以触发它，读者就可能是正在干活的 agent。这时第一条路线 `grill-with-docs` 它加载不了，`handoff`、`improve-codebase-architecture` 等也一样，于是 agent 要么照着这里的一行介绍自己仿造一个流程，要么卡住。#538 记录过这种代价："an agent that cannot find the next step invents one"。
  > You may be the user, or an agent asking on the user's behalf. The answer is a route: the skill or sequence, and why it fits better than its nearest neighbour here. Some skills here start only when the user names them. When the route begins with one you cannot load, give the user its name and the reason; do not rebuild it from its line here. `grill-with-docs` is the exception: it is the `grilling` and `domain-modeling` skills run together, and you can read both.

- **`SKILL.md` 第 23–25 行第 3 步：在本仓，Yes 和 No 的差别不只在会话长短。** 现在的判据是 "is this a multi-session build?"。在本仓，Yes 这条路还带来 No 那条路完全没有的东西：脚本执行的验收条件（`verify-ticket`）、另一个会话里的 reviewer（`code-review`）、一张关掉的票作为记录。一个一次会话就能写完、但会影响付费客户的改动，按现在的判据会走 No，也就没有人检查它。
  > In this repository the branch also decides who checks the work: the **Yes** path gives every ticket acceptance criteria a script runs, a reviewer in its own session, and a closed ticket as the record; the **No** path has none of these. Take **No** only for a change small enough that the user will check it directly.

- **`SKILL.md` 第 22 行界面段末句：说出无 map 时必须一个会话做完的原因。** 现在只写了 "they run in a single session with the user present"，没有理由。agent 读到 `PHASE-BOUNDARIES.md` 鼓励在阶段边界 compact 或 clear，就可能在 prototype 和 contract 之间切换会话。我推断的理由（#538 与 `b64c2d3a` 都没有写明）是：没有 map 时，contract 各行引用的后端决定只存在于这段对话里（`write-screen-contract` 的 `references/screen-contract-format.md` 里 `source` 列的 `conversation <YYYY-MM-DD>` 形态），而 gap list 需要用户当场回答（`write-screen-contract` 第 6 步）。
  > …they run in one session with the user present, prototype through contract, before **the `to-spec` skill**: with no map, this conversation is the only record of the decisions the contract cites, and its gap list waits on the user's answers.

- **`SKILL.md` 第 10 行之后或 `## Precondition` 之前：地图的边界。** description 把范围限定在规划链上，正文却没有说清地图在哪里结束。问"怎么验收 / 怎么发布 / night 跑完之后做什么"的 agent 在这里找不到答案，也不知道该到别处去找。
  > This map ends where tickets are published. Running a night, verifying and closing a ticket, a release and a retrospective belong to the `dispatch`, `verify-ticket`, `exe-release` and `retro` skills; their descriptions route you there. When neither this map nor those fit, tell the user so instead of assembling a flow of your own.

以上四段合计约 170 词。与 A 节约 80 词的删减相抵，正文会净增约 90 词。

与 `SKILL-SET-REVIEW.md` 的冲突：`### Upstream skills` 要求 "Connect outside the upstream text first"。上面第 1、4 段属于本仓的衔接文字，放在上游正文之外的新段落里，不冲突。第 2 段改的是本仓已经改写过的第 3 步，也不冲突。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` 第 17–20 行，第 2 步的三条固定步骤 "**the `handoff` skill** out, then open a fresh session… **the `prototype` skill**… **the `handoff` skill** back" | 把"要不要换会话"写成了固定动作，而这件事本来应该由 `PHASE-BOUNDARIES.md` 的五问来判断。在本仓，这个固定动作的前提（prototype 在别的目录）不成立，还与第 22 行、第 31 行冲突（见 R2）。另外 `handoff` 只能由用户触发，agent 执行不了这三步 | 把三条步骤换成一个判断：`Run the prototype in this session when it fits the smart zone: it lives under `prototypes/` in this checkout and needs the grilling as its primary source. Hand off only for a reason on `PHASE-BOUNDARIES.md`'s question 3, such as a host with the Claude Design tools for step 2's interface branch.` 这是上游原文，改它符合 `SKILL-SET-REVIEW.md` `### Upstream skills` 的例外条件（即使有衔接文字，agent 照做仍会做错）。需要在 `mmw-v2/merge-notes/ask-matt.md` 加一行 |

除此之外没有死板的流程。`PHASE-BOUNDARIES.md` 的 "The first **yes** wins" 看上去像硬规则，但同一文件的 `## These are judgement calls` 已经把它说成判断的顺序，这是上游的设计，应当保留。

## 脚本

无。`agents/openai.yaml` 只有 `display_name` 和 `short_description` 两个字段。

## 与其他技能的重复或交接问题

- `writing-for-agents` 与 `manage-agents-md`：ask-matt 第 89 行把 "skills, AGENTS.md, pointed-at docs" 都指给 `writing-for-agents`，但在本仓，仓库 `AGENTS.md` 的格式归 `manage-agents-md` 管（它的 `scripts/check.sh` 会判错）。实际影响小，因为 `manage-agents-md` 的 description 自己就会被 "create AGENTS.md" 触发。如果要改，在 ask-matt 这一行加半句指向 `manage-agents-md` 即可；两个技能本身都不用动。
- `diagnosing-bugs` 与 `improve-codebase-architecture`：见 R3。这是上游两份文件之间不一致，留给上游，本仓不改。
- `setup-matt-pocock-skills`：ask-matt 第 93 行 "Custom issue trackers also work." 与本仓流水线不符。`verify-ticket.py`（20 处）、`dispatch.sh`（7 处）以及 `relay.py`、`status.py` 等都直接调用 `gh`，而 `setup-matt-pocock-skills/SKILL.md` 第 42–46 行仍然提供 GitLab 和 local markdown 两个选项。选了它们的用户会在 `to-tickets` 或 `dispatch` 那一步失败。这句话是上游原文，问题应该在 `setup-matt-pocock-skills` 那边处理（由那个技能的调查员判断），ask-matt 这一句可以跟着改。
- `mmw-v2/merge-notes/ask-matt.md` 第 13 行的理由 "只有 `dispatch` 起的 worker 进得去" 与 `dispatch` 的 `references/inside-a-ticket.md`（`adopt`）、`implement` 的 description "or picked one up yourself" 矛盾，改 A2 时一起改。
- 维护规则缺口：上游 `mmw-v2/upstream/CLAUDE.md` 第 21 行规定"增删改任何用户可达技能都要回头检查 ask-matt"，但这条规则只约束上游仓库。本仓加进路由表的 `design-pages`、`write-screen-contract` 改动时，没有任何规则提醒回头核对 ask-matt。这次 R1、R4 就属于这类漂移。只登记，归属应在 `SKILL-SET-REVIEW.md` 里定。
- `find-skills`（本机技能，不属于 MMW）与 ask-matt 的 description 争同一类触发，只登记。

## 没查到的

- 被指向的各技能没有逐一通读全文，只读了与路线声明有关的段落（上文逐条标了位置）。`design-pages` 读了 `SKILL.md`、`references/edit-pages.md`、`references/design-system.md`，以及 `references/pull.md` 的标题和 `## Reached from here`。
- B 节第 3 段给出的"一个会话做完"的理由是推断，#538 正文与 `b64c2d3a` 提交说明都没有写明。
- 使用证据只查了 Claude Code 的 `~/.claude/projects` 和 Codex 的 `~/.codex/sessions`，Grok、Pi、Cursor 的会话记录没有查。Codex 那边用命令特征筛选，可能漏掉用其他方式读取文件的会话。
- 除 Claude Code 以外，其他 host 怎样对待 `disable-model-invocation`（Codex 看 `policy.allow_implicit_invocation`，Grok 与 Cursor 没有验证），R1 的结论在 Claude Code 上是亲眼看到的，在其他 host 上是推断。
- 没有测试套件覆盖 ask-matt（`AGENTS.md` 的命令表里也没有），所以没有跑任何测试。
