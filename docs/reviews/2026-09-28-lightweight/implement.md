# implement

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的 A/B/C 建议。每条增加都写明它改变哪种情形下的选择；说不出情形的草稿一律不采纳。

**判断**：worker 的启动 prompt 已经带着 "You are operating autonomously. The user is not watching…" 和 "Several tickets run on this machine at once"（`dispatch.sh` 第 108–109 行），所以调查员 B-1 里"没人看着你""有并行的票"两句是重复。worker 真正缺的是三样：失败时诚实比变绿重要的理由；baseline 为什么不能顺手改进；票没写到的地方该按谁的需要选。这三样各贴在它管的那条规则旁边，不写成开头的前言。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` `## Claim, read in, write the code` 第一条 bullet，接在 "…never by bending the baseline, the harness or the test." 之后 | The checks exist so the user can trust a closed ticket without reading its code. An honest `HANDOFF REQUIRED` costs them one look in the morning; a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it. | 一条标准只在 mock 或放宽的夹具下才过、或测试过了而产品里行为并不成立时：没有这句，worker 按"标准绿了"报 met；有了它，worker 知道绿勾的用途是让人不读代码也能信，会去修或写 `ABANDON`。规则本身已在，这句给的是它能推广到清单外情形的理由。 |
| I2 | 同一条 bullet，接在 "The baseline is the contract." 之后 | A baseline is a decision someone already paid for: a user's answer, a prototype that won, a page they signed off. Rewriting it from memory, or improving it, reopens that decision where nobody who made it can see; a `contract` child reopens it where they can. | baseline 里有明显"更好"的写法或一处小不一致时：没有这句，worker 顺手改进；有了它，照抄，并在认为该改时开 `contract` child。 |
| I3 | 同一条 bullet，接在 "…states what in that same source still holds and must be preserved." 之后 | When the rest of the ticket depends on the answer, end your turn: the child wakes the main agent, which corrects the source and resumes you, or leaves the question to the user. | 这是功能缺口，不是说明：剩下的工作都依赖答案时，正文只说 "keep going"，worker 会空等或绕开 baseline 继续做。`night.md` 的 `child.opened` 行和第 100 行 watchdog 行都按"worker 在等"处理。 |
| I4 | 读入那一段，把 "Then follow **Parent** to the spec and read only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope, not the whole spec." 改为右栏 | Then follow **Parent** to the spec: read its Problem Statement and Solution, the few lines that say who uses this and why, then only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope, not the whole spec. Where the ticket is silent, choose what serves the person the Problem Statement names. | 票没写到的地方（空状态的文案、默认排序、一个边界值）：没有它，worker 选技术上顺手的；有了它，按用户的目的选。代价很小：spec #555 的这两节合计 38 词。 |
| I5 | 同一段开头，把 "Then read yourself in:" 改为右栏 | Then read yourself in, until you know what this ticket delivers, what it must not contradict, and the words the repository uses for them: | 给读入一个完成标准。原文是一串 "then … then"，只有顺序，没有"读够了"的判据。 |
| I6 | "Put no question on the screen." 那条 bullet 末尾 | Write each line for the reviewer, who judges it, and for the user, who reads it in the morning without your context: a choice a user would notice in the product (a label, a default, what a page shows or hides) is the one most worth a line. | worker 替用户定了一个看得见的默认值时：没有它，会觉得太小不记；有了它，这一类最先记。reviewer 的 Spec axis 逐行判这些行（`code-review` 的 `references/spec-reviewer.md`）。 |
| I7 | `references/writing-interface-code.md` `## One code path` 段末 | Otherwise the story judge passes on a path no user ever takes, and every criterion goes green on it. | 遇到清单外的变体（"只是加一个开发开关"）时，worker 能判断它也是第二条路径。依据是 `merge-notes/implement.md` 记录的真实事故：fixtures 喂的 `scenario` 路径让每个 worker 第一次就过了验收。 |
| I8 | 第 5 步 Audit 整段，替换为右栏 | Audit: read the ticket once more against the branch, the way the user will read your closing comment. Each point under **What to build** holds in the product, not only in a test, and each baseline under **Read first** is followed where it applies. A point that does not hold is said in the closing comment; nothing is committed after the final run. Done when you can name, for each point and each baseline, where the branch follows it or the line of the closing comment that says it does not. | 原文"重读全票、追到每条 `EVIDENCE:`"是一道手续，完成标准不会失败（`EVIDENCE:` 由脚本写入）。改后给出审计的目的，并把发现的出口写清：第 4 步之后不再提交（`merge-notes/implement.md` 第 22 行：final proof 在 review fix 的最后一次 commit 之后）。调查员原稿写"fix it and make step 4's run again"，与这一设计冲突，不采纳那半句。 |
| I9 | 写码规则第 3 条，改为右栏 | Before changing a function, grep every caller and fix the shared code once; when what you add supersedes an existing branch, guard or file, delete it in the same commit. | 原文要求每加一个分支都点名一个要删的东西，worker 会硬找一个去删，或因找不到而不敢加必要的守卫。改后只在真有被取代的东西时删。仍是动作句（与 ponytail 实验的结论一致）。 |
| I10 | 写码规则第 5 条，改为右栏 | Before adding a file, a dependency or a configuration entry, write under **Decisions I made on my own** why the existing one is not enough. | 原文 "say why" 在无人会话里没有读者；改后这一句进入 reviewer 逐行判的清单。 |
| I11 | "Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams." 之后（来自 `tdd` 定稿 I1） | Where an acceptance criterion's `CHECK:` names a test case, that case is your first red test: run it before writing the code it covers and read why it fails. Red that comes from a missing file, an import error or a typo in the case name proves nothing; the test counts as red only when it fails because the behaviour is absent. No later step does this for you: the claim-time baseline ran before the test existed, and the review reads tests without running them. | 流水线里没有别的环节证明"这条测试能失败"：认领时的基线跑在测试存在之前，Tests axis 只读不跑。Nowledge Mem `02fc9cc5` 记下四种反复出现的假绿。 |
| I12 | 第 1 步，接在 "note each trade-off under `Decisions I made on my own`." 之后（来自 `resolving-merge-conflicts` 定稿） | The incoming side is closed tickets whose criteria the closing pass's `reverify` runs again on the base branch, so a resolution that drops their behaviour reopens their ticket hours later, and after a bounce no reviewer sees this merge. Where theirs and yours cannot both hold, the cut missed an edge: keep what landed and run `<engine> <n> --sub-issue contract <file>` naming both tickets. | `resolving-merge-conflicts` 第 3 步说"选符合合并目标的一边"，而 `integrate` 的合并没有目标可言。挑了自己这边，代价会在几小时后落到另一张没人在做的票上；bounce 之后的重试不经过 reviewer（ADR 0027，#915 时间线可证）。按 advisor 意见压成两句。**推断**：没有找到这样出过事的记录。 |
| I13 | 第 8 步，repo-checks 失败那一处保留的判断句（机械的下一步按 D4 移进拒绝信息） | When the repository's own checks fail and the failing check covers code an incoming ticket of your integration changed, the failure is the merge's: use the `resolving-merge-conflicts` skill. | 干净合并却让检查变红，只在 closeout 才会暴露，而第 8 步原来不指向这个技能（来自 `resolving-merge-conflicts` 定稿）。 |
| I14 | 读入段 "the last section of a research file" 改为 "the part of a research file that answers its question"；`merge-notes/implement.md` 第 14 行同步（来自 `research` 定稿） | the part of a research file that answers its question | `research` 从没要求结论放在最后一节；本仓约 30 份报告的最后一节几乎都是来源清单或未核实事项，agentflow #592 的结论在开头。照字面读，worker 会把来源清单当成要照做的结论。用词与 `docs/contexts/tickets/CONTEXT.md` **baseline** 条目的 "a research file's conclusion" 一致。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `## Closing steps` 续跑段："A ticket that already carries a run of your own…" 起，到续跑表和 "Other events do not move you…" 一段（约 333 词） | 先让 `verify-ticket.py --preflight` 在 `READY:` 之后打印 `RESUME: step <k> (<决定它的事件>)`，再把这一整块换成一句："A ticket you are prompted back into: claim it again first, `<engine> <n> --preflight`, and carry on at the step its `RESUME:` line names." | 每一行都是票上事件的确定函数（`events.py fold` 已能读出）。续跑真实发生过（agentflow #916 两次 `worker.resumed`），所以不是删功能，是把查表交给脚本。 |
| D2 | 第 7 步 "A draft with a `failed` or `stuck` line opens `HANDOFF REQUIRED: …` instead of `ALL MET`; then recount `Counts:` against the draft." 与 Done when 里的 "and `Counts:` matches it" | `--closeout`（含 `--check-only`）按草稿里的 `ABANDON:` 行自己写首行与 `Counts:`；然后删这两处。"Put each `ABANDON:` line under its criterion." 保留。 | `draft_problems` 已用 `tally()` 重算并拒绝不一致，脚本本来就是判定者。 |
| D3 | 第 8 步 "A refusal changes nothing on the ticket; its first line names the first problem and the `--check-only` command that lists the rest: fix the draft, or what it describes, and run it again." | 删 | 与 `verify-ticket.py` 拒绝首行逐字重复。 |
| D4 | 第 8 步 "When it stops because the repository's own checks failed, fix the code, run that suite yourself, commit, make step 4's final run again, and close out again." | 先把这串机械的下一步写进 repo-checks 失败的那条拒绝（`verify-ticket.py` 约第 2442 行），再删；需要判断的那一句由 I13 保留 | 下一步应在拒绝出现的那一刻给出。 |
| D5 | 读入段之后 "Then say in one sentence which **seam** this ticket is tested at, copied from the ticket's **Seam**." | 删 | 无人会话里没有读者。`tdd` 的 `## Seams: where tests go` 已写 "Working from a ticket, the seams under test are the ones its `## Seam` section names"。 |
| D6 | "Then check the ticket is coherent: its title and **What to build** describe the same vertical slice; every glob under **Owns** either matches an existing path or is marked `(new)`." | 删 | 标题与 **What to build** 的一致性在 `to-tickets` 发布回读时已查；`(new)` 不影响任何判定（`owns_globs` 的 docstring："`(new)` is a note"）；真自相矛盾的票由 `contract` 规则接住。 |
| D7 | `## Shared experience while implementing` "Evaluate the same trigger again at every meaningful milestone or handoff." | 删 | 同段第一句 "as soon as all three conditions hold" 已经是这个意思。 |
| D8 | 同段 "Save only while `MMW_TASK_SCOPE` is `mmw-map-<n>` or `mmw-spec-<n>`; an empty value means routing failed and nothing is written." | 把这个条件写进 `references/saving-memory.md` 的保存命令（scope 不是 `mmw-*` 时直接退出），再删这句 | 确定的条件交给命令；现在命令并不检查它。 |
| D9 | fault 那一句括号里的清单 "(`verify-ticket.py`, `dispatch.sh`, a judge script, `lease.py`, a hook, `.mmw/target.json`)" | 缩为 "(the pipeline's own scripts, a hook, or `.mmw/target.json`)" | 同一张清单在 `verify-ticket` 的 `references/sub-issues.md` 与 `ui-acceptance` 的 Five rules 里各有一份。 |

### 不采纳

- 调查员 B-1 整段开头：拆开后，有用的部分成了 I1、I2；"Nobody watches you work""Other tickets … run beside yours" 与启动 prompt 重复；替换上游第 6 行那一句不改变任何选择。
- B-6（seam 的理由）：`tdd` 第 14、22 行已经说了测试为什么放在公开边界、为什么先约定 seam。
- B-7（"The closing steps turn your work into evidence…"）：说不出它改变哪一个选择；I1 已经承载了"证据要能被信任"这层意思。
- B-8（最终运行为什么没有修复轮）：规则本身已经明确；我说不出一个比 merge-note 里"前面的轮次就是修复轮"更实在、又能改变选择的理由，不为凑理由而写。
- A8（删两处 "Done when … exits 0"）：命令会拒绝，这两条标准能失败；删掉只省 16 词，又和本仓"每步一行 Done when"的写法不一致。
- A10（把 Memory 保存命令做成脚本）、A12：收益小，调查员自己也倾向保留。A11（`writing-interface-code.md` 第 41 行）随 `verify-ticket` 定稿 D6 一起删：那条规则背后的 `review_problems` 被删，in-ticket 的每条 finding 已由 `review_finding_problems` 要求 `fixed` 或 `refuted:`。

### 连带改动

- `mmw-v2/merge-notes/implement.md` 第 16 行 "措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效" 改为："规则写成动作 + 票字段。那次对照实验（ponytail，记录在 Nowledge Mem）比较的是同一条纪律写成散文与写成动作，证明的是规则要写成动作；它没有测规则旁边的一句理由。理由句只在能改变清单外情形下的选择时才写，贴在它管的规则旁边。" I1、I2、I6、I7 正是这种句子。
- `verify-ticket` 的 `references/sub-issues.md` 第 23 行引用了本技能的标题与 bullet 名；本定稿不改标题，不受影响。

## 结论

`implement` 现在正文 3,986 词：`SKILL.md` 2,785 词 / 122 行，`references/writing-interface-code.md` 919 词，`references/saving-memory.md` 282 词。上游原版（`git show 5b1a4c51:skills/engineering/implement/SKILL.md`）正文约 50 词，现在是它的约 80 倍。技能没有自己的脚本，它驱动的是 `verify-ticket.py`（4,020 行）和 `dispatch.sh`（4,613 行）。

多出来的部分大多有依据：收尾八步的顺序是脚本定死的，写码规则每条都对应一次真实的误用。真正能删的集中在四处：
- 续跑表：一张由票上事件推出"从哪一步接着做"的查找表，脚本能算。
- 第 7 步：手工改首行并重数 `Counts:`，而脚本本来就会算这两样。
- 第 8 步：复述了拒绝信息本身已经说的话。
- 三处"说一句 / 核对一下"：没有读者，也没有失败时该怎么办。

估计能删 500–650 词而不丢功能，约占正文 15%。

"灵魂"几乎是空的。git 历史里也从没写过（见 B 末尾），所以没有可恢复的原文，只能新写。worker 读完只知道照什么顺序跑哪些命令，不知道以下四件事：
- 这张票是某个 spec 的一片，已经和用户定过；
- 今夜还有并行的票，也有排在它后面、要在它之上继续建的票；
- 早上读它收尾评论的是不读代码的产品主人；
- 一个诚实的 `HANDOFF REQUIRED` 代价很小，一个假的 `ALL MET` 代价很大。

B 节补的草稿约 250 词，删和补相抵后净减约 300–400 词。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `SKILL.md` `## Closing steps`，第 82–95 行："A ticket that already carries a run of your own…"、续跑表 8 行、"Other events do not move you…"（共 333 词） | 1、4 | 表里每一行都是票上事件的确定函数（`ticket.checked` 的 run、`worker.decided`、`reviewer.started/reported/lost`、`ticket.returned/bounced/passed`）。`events.py` 已经有 `fold`，能读出这些事件。这条路径真实发生过：agentflow #981、#980、#916 的事件序列里都有 `worker.resumed`，#916 有两次，所以它**不是**过度防御。问题只在于：这是一次查表，却让 agent 自己去翻评论、对照 8 行条件 | `verify-ticket.py --preflight`（`run_preflight`，第 2063 行）。每次重新进票第一件事就是跑它（第 82 行 "Claim it again first"），可在 `READY:` 之后多打印一行 `RESUME: step <k> (<哪个事件决定的>)`。剩余风险：要写这段逻辑和它的测试（`mmw-v2/tests/verify-ticket/test_preflight.py`）；`night.md` 里 watchdog 那句 resume 消息 "Carry on from where its events say you are" 仍然成立 | 正文只留一句："On re-entry, `--preflight` prints `RESUME: step <k>`; carry on there." 表格和那一段搬进脚本。那两个需要动作的事件（`repo-checks` unmet、`worker.queued`）已经写在第 8 步和第 1 步，不必另写 |
| A2 | `SKILL.md` 第 7 步："A draft with a `failed` or `stuck` line opens `HANDOFF REQUIRED: …` instead of `ALL MET`; then recount `Counts:` against the draft."，以及 Done when 里的 "and `Counts:` matches it" | 1 | `verify-ticket.py` 的 `draft_problems`（第 851–900 行）已经用 `tally()` 从草稿的 `ABANDON:` 行和勾选状态重算计数，对不上就拒绝，而且能算出首行应是什么。`run_draft`（第 1492 行）也会算首行，但它读的是自跑事件里的 `abandons`。那些 `abandons` 来自 `write_ledger`（第 688 行）从**票面**生成的 ledger，worker 补进草稿的 `ABANDON:` 行不在其中（据代码推断；agentflow 五张票的 `ticket.checked` 事件都没有 `abandons` 字段）。结果是：一个确定的计算让 agent 手工做，再由脚本核对 | `--closeout`（含 `--check-only`）照草稿里的 `ABANDON:` 行重写首行和 `Counts:`，不再为这两行拒绝。剩余风险：无，脚本本来就是判定者 | 删掉这一句和 Done when 的后半句（约 45 词）。`ABANDON:` 行放到对应 criterion 下面这一句保留，那是判断 |
| A3 | `SKILL.md` 第 8 步："A refusal changes nothing on the ticket; its first line names the first problem and the `--check-only` command that lists the rest: fix the draft, or what it describes, and run it again." | 6 | `verify-ticket.py` 第 2427–2431 行的拒绝首行就是 `closeout rejected, N problems: … Run … --check-only to see the other …`，逐字相同 | 拒绝信息本身。剩余风险：无 | 删（约 35 词） |
| A4 | `SKILL.md` 第 8 步："When it stops because the repository's own checks failed, fix the code, run that suite yourself, commit, make step 4's final run again, and close out again." | 1、6 | 这句话是必要的：closeout 只接受 `HEAD` 上的 worker reverify，所以顺序不能错。但第 2442 行的拒绝只说 `closeout stopped: the repository's checks did not pass (…)`，没说接下来做什么。这件事该在拒绝的那一刻说 | 把这串下一步写进第 2442 行的 stderr，然后删掉正文这句（约 30 词）。剩余风险：要改一处拒绝文本和它的测试 | 先改脚本，再删文 |
| A5 | `SKILL.md` `## Claim, read in, write the code` 第 22 行："Then say in one sentence which **seam** this ticket is tested at, copied from the ticket's **Seam**." | 2 | 自主会话里没有人读这句话，它只是把票上的一个字段抄到屏幕上。真正起作用的是"测试写在 **Seam**"，而第 36 行 tdd 那句已经说了 "at pre-agreed seams" | 第 36 行改为 "…follow it where possible, at the seam the ticket's **Seam** names"，理由见 B-6 | 删这一句（约 20 词），并入第 36 行 |
| A6 | `SKILL.md` 第 18 行："Then check the ticket is coherent: its title and **What to build** describe the same vertical slice; every glob under **Owns** either matches an existing path or is marked `(new)`." | 5、6 | ①标题与 **What to build** 是否一致，`to-tickets` 发布后的回读（`to-tickets/SKILL.md` 第 152 行 "The title and **What to build** describe the same slice"）已经查过。②这句话没说查出问题后怎么办；自相矛盾的票，第 28 行的 `contract` 那条已经覆盖（"contradicts another such source"）。③`(new)` 只是注记，`owns_globs`（`verify-ticket.py` 第 486 行）的 docstring 写 "`(new)` is a note."：没标 `(new)` 的 glob 照样匹配新建文件，不影响任何判定。触发过没有：没找到任何因此开的 child（未穷举，是推断） | `to-tickets` 的回读，加上第 28 行的 `contract` 规则。剩余风险：一张发布后被人手改坏的票；由写码时的 `contract` 规则接住 | 删（约 35 词） |
| A7 | `SKILL.md` 第 24 行："A fault in the pipeline itself (`verify-ticket.py`, `dispatch.sh`, a judge script, `lease.py`, a hook, `.mmw/target.json`)…" | 6 | 同一张清单出现三次：这里、`verify-ticket/references/sub-issues.md` 表第 1 行、`ui-acceptance/SKILL.md` `## Five rules while the product is running` 第 5 条。worker 三份都会读：start prompt 的 `PRODUCT_RULES`（`dispatch.sh` 第 109 行）要它读 Five rules | 保留 `implement` 这一份，因为这是 worker 行动的那一刻；清单可缩成 "the pipeline's own scripts, a hook, or `.mmw/target.json`"。`ui-acceptance` 那份给 reviewer 和 main agent 用，保留 | 缩写（省约 15 词）。跨技能部分见后文 |
| A8 | `SKILL.md` 第 2 步 "Done when `--decisions` exits 0."，第 6 步 "Done when `--touched` exits 0." | 2 | 完成标准就是命令本身的退出码，不会给出新信息；`SKILL-SET-REVIEW.md` `### Scripts and judgement` 把"不会失败的完成标准"列为问题 | 命令的退出码 | 删（约 16 词） |
| A9 | `SKILL.md` `## Shared experience while implementing` 第 74–76 行："Evaluate the same trigger again at every meaningful milestone or handoff." 和 "Save only while `MMW_TASK_SCOPE` is … an empty value means routing failed and nothing is written." | 2（前句）、1（后句） | 前句：同一段第一句 "Save a Memory as soon as all three conditions hold" 已经说了"一成立就存"，这句是空转。后句是确定的条件，而 `saving-memory.md` 的命令并不检查它：`MMW_TASK_SCOPE` 为空时照样写 | 前句删。后句挪进保存命令，在 `label_args` 之前加一行 `[[ "$MMW_TASK_SCOPE" == mmw-* ]] \|\| exit 0`（或 A10 的脚本） | 删约 35 词 |
| A10 | `references/saving-memory.md` 第 13–35 行，"Write this exact body:" 后面那段 bash | 1 | 这是一段要 agent 逐字照抄的程序：`mmw-v2/tests/dispatch/test_memory_skill_commands.py` 第 20–24 行把这段文字当作 bash 直接执行来测。一个"被当程序测试的段落"就是住在正文里的脚本 | 可选：做成一个小脚本（放 `dispatch` 的 `scripts/` 下，已有 `<dispatch>` token 可达），标题作参数、五行正文走 stdin，并在里面做 A9 的 scope 检查。剩余风险：多一个脚本入口要解析；worker 仍要自己写那五行正文，那是判断 | 这是可选项。收益约 100 词，外加消除一处手抄出错的机会。不做也不丢功能 |
| A11 | `references/writing-interface-code.md` `## Fix in place` 第 41 行："When the review's Spec axis reports a `Missing` that names one of this ticket's screen-contract rows, the closing comment names that row id too…" | 6 | `verify-ticket.py` `review_problems`（第 2112–2135 行）按这条拒绝草稿，拒绝文本逐字说明缺什么 | closeout 的拒绝。剩余风险：worker 多撞一次拒绝 | 可选。留着能省一轮拒绝，删掉省约 40 词。倾向保留 |
| A12 | `SKILL.md` 第 8 步："Never close the ticket or swap its labels yourself: a hook blocks the command." | 6 | `dispatch/scripts/tool-guard.py` 第 69–71 行的拒绝会说明应当走 `--closeout` | hook 的拒绝。剩余风险：worker 白试一次 | 可选。这是一条禁止句，`SKILL-SET-REVIEW.md` 允许保留；删掉只省约 15 词，倾向保留 |

第 3 类（历史碎碎念）：三份文件里都没有。`grep -n -i -E "no longer|\bnow\b|used to|#[0-9]{2,}|20[0-9]{2}-"` 只命中 `saving-memory.md` 里 "a record … no longer applies"，说的是记录本身的状态，不是改动历史。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 20 行 "A baseline in **Read first** is anything there that records a settled conclusion, and it is a contract, not a reference. A design package is copied exactly; a prototype is rewritten to production standard, keeping the shape its verdict settled on."：告诉 worker 哪些东西不归它重新决定，以及两类 baseline 该怎么对待。
- 第 20 行 "read only the Implementation Decisions sections the ticket names, … not the whole spec"：防止整份 spec 淹没票点名的决定（Nowledge 记录 27df9478 有同样的结论）。B-2 只在这里补两小节，不推翻它。
- 第 28 行整条 "The baseline is the contract… Never quietly change a baseline, never quietly add around one. A check that will not pass is answered by fixing the code or abandoning the criterion, never by bending the baseline, the harness or the test."：这是整个技能最接近"做人原则"的一句，守的是验收的诚实。
- 第 29 行 "Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it…"：把"没人可问"变成一条判断路径，而不是一条禁令。
- 第 33 行 "Whatever you simplify, keep intact: security, error handling that prevents data loss, accessibility, and anything the ticket explicitly asks for"：给"简化"划出底线。
- 第 34 行末 "because one file has one writer at a time and the cut missed an edge"：一句理由，worker 由此能自己判断清单外的情况。
- 第 40 行 "This is about extras only: implement every behavior the ticket asks for, completely."：防止把"少写测试"读成"少做事"。
- 第 53–55 行 "Current artifacts, verified evidence, … override Memory. Verify every Memory against current repository evidence before acting on it."：说明 Memory 的地位。
- 第 60–63 行 "keep `--` before it: Nowledge returns nothing for a query that names something no record holds…"：一个已知误用的理由，删了 agent 会用长句搜索，结果什么都搜不到。
- 第 72–74 行 capture gate 的三个条件：什么值得留给下一名 worker，这是判断。
- 第 97 行 "Three `ABANDON` kinds, and the machine branches on each" 以及 `decision` 的 "a UI difference never goes here"：写出了每种放弃在下游引起什么。
- 第 99 行 "the closeout counts no rounds, so that line is the whole record of the trying"：告诉 worker 这一行是写给后来的人看的记录。
- 第 102 行 "It is posted here, before the reviewer starts, so the review judges every line of it"：解释了顺序的原因，防止被人重排。
- 第 105 行 "Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count."：`refuted:` 的判据。
- `writing-interface-code.md` 第 3 行两份 baseline 各管一块（"each binding its own domain … so the two never compete"）。
- `writing-interface-code.md` 第 29 行 "**The story criterion is the exception to red before green.**" 整段：它说明为什么这里可以违背 `tdd`，没有它 worker 会在两套纪律之间无所适从。
- `writing-interface-code.md` 第 37–39 行 "check that the design value itself is plausible" 和 "The pixel difference image is evidence, not a verdict"：对应 chameleon #548 一名 worker 跑了十六轮的真实教训。

### 缺口与补充草稿

**B-1　开头：这张票在整体里的位置和分量（最大的缺口）**

位置：`SKILL.md` 第 6 行，替换上游那句 "Implement the work described by the user in the spec or tickets."。

对一名被派来的 worker，这句话还有误导："described by the user" 不成立，票是 `to-tickets` 写的。

worker 目前拿到的只有 start prompt 的 "Use the implement skill to work ticket #N" 加一句 "operating autonomously"（`dispatch.sh` 第 108 行、第 1946 行）。技能正文从第一行就进了命令。以下几件事它不知道：
- 票背后的决定已经和用户定过；
- 有并行的票，也有排在它后面、要在它之上继续建的票；
- 早上读收尾评论的人不读代码；
- 绿勾本身不是目标。

缺了这些，它在清单外的情况下只能凭"让检查变绿"去判断：放宽断言、把"做不到"写成"已完成"、在空白处替用户做产品决定。仓库里其实已经有这个思路，只是放在给人看的文档里：`mmw-v2/upstream/docs/engineering/implement.md` `## What it does` 写着 "It never reopens the plan … Whatever was settled upstream is the input"；`tool-guard.py` 第 7 行写着 "a closed ticket nobody can read in the morning"。两处都不在 worker 会加载的文本里。

> You are building one slice of a spec whose what and why were already settled with the user: in the spec, its decision tickets, prototypes and design. Build what was decided; do not reopen it. Other tickets of the same spec run beside yours on this machine, and the ones blocked by yours will build on what you land. Nobody watches you work. What the user sees is the product and this ticket's closing comment, read the next morning without the context you have now. So the job is not to make the checks green; it is to make the behaviour the ticket describes true, and to say exactly what is and is not true when you stop. An honest `HANDOFF REQUIRED` costs the user one look in the morning; a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on it inherits the fault.

它改变做法的地方：遇到过不去的检查时，worker 会倾向于 abandon，而不是弯测试；遇到空白时，会意识到那是用户的产品，而不只是一个技术选项。

**B-2　读入：不知道为谁、为什么而做**

位置：`SKILL.md` 第 20 行 "Then follow **Parent** to the spec and read only the Implementation Decisions sections…" 之后。

现在 worker 只读 Implementation Decisions、Testing Decisions、Out of Scope，spec 的 `## Problem Statement` 和 `## Solution`（`to-spec/SKILL.md` 第 44–50 行，"from the user's perspective"）被排除在外。这是 worker 唯一能看到"谁在用、为什么要"的地方。**What to build** 每一点虽然写了理由（例：agentflow #976 第 1 点的 "因为救援工具 `recharge` 与预扣都在锁定后先读余额再写"），但那是工程理由，不是用户理由。`## User Stories` 按模板是 "LONG"，不必读全，所以只加两个短节，"只读点名小节"的原则不动。

> Read its Problem Statement and Solution too: they are a few lines, and the only place that says who uses what you build and why. Where the ticket and criteria are silent, that is what your choices answer to.

**B-3　baseline 为什么是合同**

位置：第 28 行 "The baseline is the contract." 之后。

现在只有规则，没有原因。worker 可能把"照抄 baseline"当成死规定，看到 baseline 有明显更好的写法就"顺手改进"。

> A baseline is a decision someone already paid for: a user's answer, a prototype that won, a page they signed off. Rewriting it from memory, or improving it, reopens that decision where nobody who made it can see; a `contract` child reopens it where they can.

**B-4　`Decisions I made on my own` 是给谁看的**

位置：第 29 行 "Put no question on the screen…" 那条末尾。

worker 现在不知道这些行会被 reviewer 的 Spec axis 逐行判 `reasonable` 或 `should not`（`code-review/references/spec-reviewer.md` 第 57 行），也会被用户早上读到，因此不会特意把"用户在产品里看得到的选择"写出来。agentflow #976 的 DECISIONS 里有一行 "The platform organization-wallet ledger maps only `silver_expiry`; existing transaction types retain their previous display"，就是一个客户可见的选择，写得很好，但这靠的是 worker 自觉。

> These lines are where your judgement becomes visible: the reviewer judges each one, and the user reads them. A choice a user would notice in the product (a label, a default, what a page shows or hides) is the one most worth a line.

**B-5　`contract` child 之后没有路：一个功能缺口**

位置：第 28 行 "keep going and run `<engine> <n> --sub-issue contract <file>`" 之后。

正文只说 "keep going"，没说剩下的工作全都依赖那个答案时怎么办。实际机制是：`contract` child 会叫醒 main agent（`night.md` 第 118 行 "the three kinds that wake you are `contract`, `fault` and `decision`"），main agent 裁决或交给用户，再 resume 这名 worker；`night.md` 第 106 行 "A ticket already being worked stays held at the contract question"。worker 不知道这些，就可能一直等，或者绕过 baseline 继续做。

> When the rest of the ticket depends on the answer, end your turn: the child wakes the main agent, which settles it or leaves it to the user and resumes you.

**B-6　seam 的意义**

位置：第 36 行（与 A5 合并）。

> Read the `tdd` skill's `SKILL.md` and follow it where possible, at the seam the ticket's **Seam** names: tests at an agreed boundary survive the rewrites of the code beneath them, and the tickets after yours reuse that boundary.

后半句的来源是 `upstream/docs/engineering/implement.md` `## Pre-agreed seams` 的 "Working at a seam agreed before any code is written is what keeps the tests durable"。

**B-7　收尾八步为什么存在**

位置：`## Closing steps` 第 80 行 "Once done, commit…" 之后。

现在八步读起来像八道手续，worker 会把它们当作要过的关，而不是要交出的证据。

> The closing steps turn your work into evidence someone can check without trusting you: your own run, a separate reviewer, a final run on the exact commit that lands, and a closing comment the main agent and the user act on.

**B-8　第 4 步最终运行为什么没有修复轮**

位置：第 108 行 "this final run gets no fix round" 之后。

这个理由原来写在正文里，`e74e0140` 删掉了，删之前的原文是 "…because the earlier own run and review fix were the repair rounds."。建议恢复，但换成更直接的说法：

> …: your own runs and the review fix were the repair rounds; this one is the proof of what lands.

**B-9　`writing-interface-code.md` `## One code path` 没有理由**

位置：第 63 行末。

merge-note（`merge-notes/implement.md` `## Two baselines with separate jurisdictions, and one code path`）写了真实事故："a `scenario` path fed from fixtures beside a `live` path … every worker satisfied the acceptance criteria on the first"。正文却只有禁令。worker 不知道原因，遇到"只是加一个开发开关"这种清单外的变体时就判断不出来。

> Otherwise the story judge passes on a path no user ever takes, and every criterion goes green on it.

**前几轮删过什么**：`git log -p` 查了 implement 目录全部 96 个提交（最早是 `32f207c4`），删除行里没有任何"意义 / 读者 / 产品"类段落；`grep -E "morning|nobody is watching|reads it cold|the user reads"` 在每个历史版本里都没有命中。被删的只有几句局部理由：
- B-8 那句；
- 认领为什么第一步："It is first because nothing else in this pipeline claims a ticket, and step 8 below cannot close one you do not hold."（`e74e0140`）；
- 续跑为什么先重新认领："because `advance` takes the claim off a ticket it re-dispatches"（`e74e0140`）。

后两句已移进 merge-note。如果 A1 把续跑交给脚本，它们就不需要回到正文。

**与写作标准的冲突**：
- `merge-notes/implement.md` 第 16 行写着 "措辞全部是动作 + 票字段，不写原则散文——散文措辞在对照实验里无效"，与本任务书直接冲突。仓库里搜不到这次"对照实验"的任何记录（`grep -rn "对照实验"` 只命中 `merge-notes/to-tickets.md` 里一次关于 `## Owns` 的实验，与散文措辞无关）。
- `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 的 **No-op**（"an attitude where an action would do"）和 **Sediment**（"the maintainer's reason for a design → ADR"），在修剪时可能把 B-1 读成空态度。

B-1 和 B-3 不是态度句：它们改变的是 worker 在"弯测试还是 abandon""空白处替谁做决定"上的选择。以本任务书为准。采纳 B 节时，那一行 merge-note 要一起改。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` 第 20 行读入段，一连串 "Then … then … then …" | 读的顺序不依赖任何脚本，却写成了必须照走的链条。真正有价值的是其中的判断：每类来源的"结论在哪"、baseline 是合同、spec 只读点名小节 | 写成目标加要点："Before the first line, know what this ticket delivers, what it must not contradict, and the words the repository uses for them." 然后列那几个判断点（各类来源的结论位置、baseline 两种处理、spec 读哪几节、词汇表去哪找），不规定顺序 |
| C2 | 第 30 行 "before adding a branch or guard to an existing flow, name the branch or file it makes unnecessary and delete it in the same commit" | 预设了每个新分支都会让某处变得多余。worker 照做时可能硬找一个东西去删，或者因为找不到而不敢加必要的守卫 | "One behaviour, one path: when what you add supersedes an existing branch, guard or file, delete it in the same commit." |
| C3 | 第 32 行 "Before adding a file, a dependency or a configuration entry, say why the existing one is not enough." | "say" 对谁说？自主会话里没有读者，这是一个仪式 | "…write why the existing one is not enough under **Decisions I made on my own**"，这样 reviewer 的 Spec axis 会判它 |
| C4 | 续跑表（同 A1） | 8 行条件表把 agent 变成了查表器 | 交给 `--preflight` 输出 |
| C5 | 第 5 步 Audit（第 111–113 行）："re-read the whole ticket and every item under **Read first**, trace every criterion to its latest `EVIDENCE:`" | 前半句是仪式；后半句的完成标准（"you can name each criterion's latest `EVIDENCE:` line"）不会失败，因为 `EVIDENCE:` 已经由脚本写进了事件。真正有价值的是 "where the branch follows" 每条 **Read first** | 换成目的："Read the ticket once more as the person who wrote it, against the branch: each point under **What to build** is true in the product, not only in a test, and each baseline is followed where it applies. What you find is still yours: fix it and make step 4's run again, or name it in the closing comment." |
| C6 | 收尾八步的顺序本身 | **不死板，必须留**。依赖顺序的有：DECISIONS 在 reviewer 之前，因为 Spec axis 要判它，而且 `--decisions` 不接受第二次；`--touched` 在 review 之后，因为它读 review 评论；最终 reverify 在最后一个写 commit 的步骤之后，因为 closeout 只认 `HEAD` 上 actor 为 worker 的 reverify；draft → closeout | 在 `## Closing steps` 开头用 B-7 那句交代目的即可；这些依赖只在 merge-note 里记，下一轮修剪的人不要把顺序放开 |

## 脚本

`implement` 自己没有脚本。与它的正文直接耦合的脚本问题如下（完整的脚本审查属于 `verify-ticket` 和 `dispatch` 的调查员）：

- `verify-ticket.py` `run_preflight`（第 2063 行）：成功时只打印 `READY:` 和可能的 `CARRIED:`，不说重新进票后该从哪一步接着做，所以正文要靠 333 词的续跑表补上（A1）。建议它输出 `RESUME:`。
- `verify-ticket.py` `run_draft`（第 1492 行）从自跑事件的 `abandons` 算首行，而 `abandons` 来自由票面生成的 ledger（`write_ledger` 第 688 行）。正常流程下 worker 的 `ABANDON:` 行只存在于草稿里，所以骨架首行总是 `ALL MET`，要 worker 手改；随后 `draft_problems`（第 851–900 行）又用 `tally()` 精确核对。算的是脚本，却要 agent 先手算一遍（A2，这一点是据代码推断）。
- `verify-ticket.py` 第 2442 行 repo-checks 失败的拒绝没有下一步，正文第 8 步只好替它写（A4）。
- `saving-memory.md` 的 bash 块是被测试直接执行的程序（`tests/dispatch/test_memory_skill_commands.py` 第 20–24 行），而且没有做 `MMW_TASK_SCOPE` 为空时的检查（A9、A10）。
- 没发现与本技能相关的死代码或多余校验。

## 与其他技能的重复或交接问题

- **sub-issue 五种 kind**：`implement` 写码规则里的定义（第 24、28、29、34 行）与 `verify-ticket/references/sub-issues.md` 的 "Which kind it is" 表重复（`contract` 的定义、`fault` 清单、`deferred`）。`grep` 结果显示，`sub-issues.md` 的读者只有 worker：`verify-ticket/SKILL.md` 的路由表和 `implement` 第 24 行指向它，`design-pages/references/pull.md` 只用到命令本身。建议：各 kind 的时机留在 `implement`，因为 worker 在那一刻加载它；`sub-issues.md` 只留那张带 "Not this kind" 对照列的判别表和退出码。`implement` 第 24 行 "Every `--sub-issue` run below is in …" 这个指针可以保留。
- **"不要在屏幕上提问"写了三处**：`implement` 第 29 行、`tool-guard.py` 第 74–79 行的拒绝、`dispatch.sh` 第 108 行 `AUTONOMOUS` 这句 start prompt。技能正文和 hook 都留：前者在行动之前说，后者兜底。start prompt 那句 reviewer 也要用，也留。只记录，不建议删。
- **pipeline fault 清单写了三处**：见 A7。`ui-acceptance` 的 Five rules 那份留，它管三种角色。
- **`mmw-v2/upstream/docs/engineering/implement.md`** 是给人看的文档页，不装进任何宿主。它已经过时：仍写 `disable-model-invocation: true` 和 "You invoke this by typing `/implement` yourself"，而本仓已删掉这两处开关；"A run is five beats" 下面列了 6 条。它的 `## What it does` 两段恰好是 B-1 的思想来源。建议修掉过时的部分；B-1 的内容进 `SKILL.md`，因为 worker 读不到这个文档页。
- **`contract` child 之后 worker 等待**：`night.md` 第 106 行说 main agent 让票"停在 contract 问题上"，`implement` 却只说 "keep going"。两边要对齐，由 `implement` 补 B-5。
- **改标题的连带影响**：若按 C1 或 A1 改动，`docs/contexts/ticket-run/CONTEXT.md` 的 **writing rules**、**closing steps**、**`Audit`** 三个词条的 _Home_ 仍指向 `implement`，词条名不变就不用动；`verify-ticket/references/sub-issues.md` 第 23 行引用了 `implement` 的 bullet 名 "For a file outside **Owns**" 和标题 `## Claim, read in, write the code`，改标题时要同步。

## 没查到的

- `verify-ticket.py` 与 `dispatch.sh` 只读了本报告点名的函数（`refusals`、`run_preflight`、`run_baseline_if_needed`、`draft_problems`、`tally`、`run_draft`、`_run_checks` 的前半段、`write_ledger`、closeout 的拒绝与 repo-checks 分支、worker prompt 的拼装），没有通读。
- `tdd`、`code-review` 只读了被引用的段落（`spec-reviewer.md` 第 57 行、`standards-reviewer.md` 第 26–28 行），没有通读。
- A2 "worker 补的 `ABANDON:` 行不会进入自跑事件"是从代码推断的。在 agentflow #979–983 的事件里没见到 `abandons` 字段，但这几张票可能本来就没有 abandon，所以不算实证。
- A1 用来证明续跑真实发生的 `worker.resumed` 只抽查了 agentflow 三张票。GitHub 全文搜索（`gh search issues`）的计数是模糊匹配，没拿来当证据。
- A6 "这项核对从未触发过"没能穷举验证，是推断。
- merge-note 里 "散文措辞在对照实验里无效" 那次实验，没找到任何记录。
