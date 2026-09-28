# to-tickets

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这是全集写得最有"灵魂"的技能之一。第 4 步的 "A criterion is decided by a command, or it is not a criterion"、第 3 问的 "The person is the instrument, not a fallback judge"、第 5 步的 "What a ticket creates is put in service by an edit to something it did not create"、Worker 一行的 "wrong **silently**"，以及 `references/person-ticket.md` 里写读者的几句，都是改变判断的句子，全部保留。缺的只有一处：没有一句话把各处连起来，说明这一场是最后一次 spec、代码和用户同时在场。另外，发布与回读里有两块确定性的工作该交给脚本。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 第 8 行（"Break a plan, spec, or conversation into…"）之后，upstream 那句话不动 | Each ticket is read by agents who were not in this conversation and cannot ask it anything: a worker at night, a reviewer in another session. This session is the last one that holds the spec, the codebase and the user at once, so settle here what can be settled: a choice left open is made at night by a worker who cannot ask. | 遇到清单没列的模糊点（一个默认值、一种失败时的表现）时：没有它，agent 会写"由 worker 视情况决定"；有了它，会现在问用户，或写死在票里。第 5 问的 "The user is here now, so ask them" 只覆盖"选择题"这一类，这一句把它推广到全部。调查员原稿中间列举"worker 读哪几节、reviewer 读哪几节"是在复述别的技能，删去。 |
| I2 | `### 5. Give each ticket its blocking edges`，替换第一段 "Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately." | Give each ticket its **blocking edges**: the other tickets that must complete before it can start. The edges are the night's schedule: every ticket whose blockers have landed starts at once, so a missing edge sends two workers into one file or onto work not built yet, and an edge that gates nothing makes the night wait for no reason. | 这一步现在只讲"少了边会冲突"，没讲"多了边会排队"。有了后半句，agent 会删掉不必要的边。第 6 步 quiz 问用户 "does each ticket only depend on tickets that genuinely gate it?"，而出票的 agent 自己原本没有这个判据。 |
| I3 | `### 3. Draft vertical slices`，`</vertical-slice-rules>` 之后 | Split where the parts can run at the same time, or where one part's criteria can fail without the other's; keep together what would write the same files, since splitting that only adds an edge. | 粒度现在完全没有判据，只在 quiz 里问用户"粗了还是细了"。这句不设数量上限，只给两条与流水线机制挂钩的判据（能否并行、能否独立判定），与你"粒度不设机械上限"的裁定不冲突。**请你过目**：它碰到了那条裁定。 |
| I4 | 模板 `## What to build`，接在 "…each point complete with the test that decides it and the reason it is there." 之后（恢复 `e74e0140` 删掉的原句） | A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph. | 夜里 main agent 按 `dispatch` 的 `night.md` 写票时只读这个模板，读不到开头的 I1。没有这句，"numbered points" 只是格式；有了它，每一点要写成能脱离上下文单独读懂的样子。 |
| I5 | `### 5.` "**Three or more on the same files**: a chain that long works the night one ticket at a time." 改为右栏 | **Several tickets on the same registration files**, where chaining them would make a large part of the night run one ticket at a time: | "三张及以上"是一个没有依据的阈值：两张大票串行同样昂贵，三张小票串行可能无所谓。后半句（prefactor 票、按条目拆共用文件、一整段逻辑的共用文件不拆）原样保留。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `### 7.` 第二段 "Publish the approved tickets to the issue tracker…"（138 词）与 `### 8.` 前两条（标题与 **What to build** 同一片；sub-issue 数与 `mmw:ticket`） | 新增 `verify-ticket.py <spec> --publish --drafts <dir>`（`to-spec` 发布 spec 用的是同一个命令的另一种形式，见 `to-spec` 定稿 D1）：读同一批草稿，按拓扑序建 issue、挂 sub-issue、打 label、连 blocking link，打印草稿名到 issue 号的对照，再对 spec 跑 `--lint`。第 7 步第二段压成 label 规则（写进草稿的 `LABELS:`）加这一行命令；第 8 步删前两条。脚本上线前文字保留。 | 真实出过一次"8 张票标题整体错位一格"（merge-note 第 29 行）。标题和正文出自同一个文件后，这种错位不会再发生。复用 `read_draft`、`compute_levels`、`ensure_label` 与 `run_sub_issue` 的创建调用。 |
| D2 | `### 8.` 第三条 "On each ticket an agent works, **Read first** and **Seam** are present and non-empty…" | 删；不加新的 lint 规则。模板里 "No absolute path, no `..`, no bare `**`" 保留（写的那一刻读得到） | 两仓 158 张已发布票从没缺过这几节：模板本身就带着它们，发布后的人工核对没有抓到过东西。原先提议改成 lint `ERROR`，是为没发生过的事加检查，撤回。 |
| D3 | `references/person-ticket.md` 第 5 行 "It is shorter than the template below and holds **the five things** only" | 改为 "It holds **the five things** only" | 搬家残留，"the template below" 指向不存在的东西；`triage` 也读这个文件。 |
| D4 | `references/ambiguity-scan.md` `## Scan` 末句 "For each category with Partial or Missing status, add a candidate question opportunity unless…"，与同节 "mark status: Clear / Partial / Missing. Keep an internal map for prioritization (do not output it)." | 删末句；状态标记两句改为 "Walk every category below." | 过滤条件在 `## Questions` 第一条约束里原样重复；标记与内部表是在规定思考过程。分类清单保留，它提供覆盖面。 |
| D5 | `references/cutting-interface-tickets.md` `### Boundary criterion` 与 `### Harness guard criterion` 的 "run by a shell months later with no model between" 两处；`### Journey criterion` 末段关于 TIMEOUT 的几句 | "由 shell 跑、中间没有模型" 移到 `## Criterion shapes` 开头说一次；journey 那段只留 "A break journey is the slowest criterion on a ticket; give it a `TIMEOUT:` when it needs more than ten minutes." | 只在两种判据下各写一次，会让读者以为另外两种不一样；TIMEOUT 规则模板末段已完整写过。`## Criterion shapes` 这个标题被 `ui-acceptance` 五处引用，不改名。 |

### 不采纳

- 调查员 B 的 ambiguity-scan 补句（"Your questions reach the user beside the proposed tickets…"）：`## Questions` 第一条约束已经是"只问会改变交付或判据的"，开头也已有 "Be skeptical, adversarial"；再加一句不改变扫描 agent 的选择。
- Worker 一行恢复 "This line is the only time the grade passes a person's eye."：quiz 已直接问用户每一级对不对，这句不改变 agent 写理由的方式。
- A6（删第 1、3 步的 Done when）、A7（压缩 `CHECK:` 取对象的一段）：收益小；A7 里的 `$MMW_TICKET` 写法是本仓自己的票确实在用的。

### 连带改动

- `dispatch` 的 `night.md` 按标题引用 "**4. Write each acceptance criterion**"；`verify-ticket.py` 第 3777 行的输出写着 "the read-back of to-tickets step 8"；`verify-ticket` 的 `references/linting.md` 第 17 行引用第 7 步标题。D1、D2 改第 7、8 步时，这三处一起改。
- `mmw-v2/merge-notes/to-tickets.md` 第 30 行 "这条理由只写在这里，模板里不写" 随 I4 改掉。

## 结论

体量：正文 7,092 词（`SKILL.md` 3,752，`references/cutting-interface-tickets.md` 2,368，`references/ambiguity-scan.md` 543，`references/person-ticket.md` 418，`agents/openai.yaml` 11）；技能自己没有脚本，它依赖 `verify-ticket` 的 `verify-ticket.py --lint`（4,020 行）。上游原版（`git show 5b1a4c51:skills/engineering/to-tickets/SKILL.md`）894 词，本仓的量约为它的 8 倍，多出的几乎全部是真实事故换来的规则（merge-note `mmw-v2/merge-notes/to-tickets.md` 逐条有出处：#216、#472/#491、agentflow #748–#752、#541/#555）。前几轮已经把历史注记、维护者理由和复述删得很干净，这一轮没有找到第 3 类（历史碎碎念）残留。

主要问题有两个。第一，第 7 步的发布和第 8 步的一半核对是 agent 手工逐条跑 `gh` 的确定性工作，应当由脚本做；草稿目录里已经有发布所需的全部信息，而且真实发生过「8 张票标题错位一格」。第二，技能缺一个开头说明：票是写给谁的、这一场是最后一次同时拥有 spec、代码和用户的机会；这层意思现在零散地落在第 4 步第 5 问、`person-ticket.md` 和第 4 问的半句里，而且上一轮删掉了其中两句最直接的话。

估计能删约 300–350 词（约 5%），不丢功能，前提是先补两处脚本；同时建议补回约 200 词的「灵魂」段落，净减不多。这个技能谈不上臃肿，它的问题是缺开头说明和缺一个发布脚本，不是废话多。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `SKILL.md` `### 7. Publish the tickets to the configured tracker` 第二段「Publish the approved tickets to the issue tracker…」（第 143 行，138 词），以及 `### 8. Read every ticket back` 前两条「The title and **What to build** describe the same slice」「The spec's sub-issue count equals…」（第 153–154 行） | 1 | 第 7 步第一段已经要求把每张批准的票写成草稿文件，头部 `TITLE:`、`LABELS:`、`BLOCKED BY:` 加正文，这就是发布所需的全部输入。之后 agent 手工做的是：按依赖顺序逐张 `gh issue create --parent <spec>`，建缺的 `mmw:ticket` label，再给每条边查 blocker 的数据库 id、POST `dependencies/blocked_by`（`docs/agents/issue-tracker.md` 第 80 行），每条边要调两次 API。merge-note 第 29 行记着「一次真实 publish 把 8 张 ticket 的标题错位了一格」，第 8 步前两条就是为防这个而加的。可以复用的代码已经在 `verify-ticket.py` 里：`read_draft`（第 3785 行）、`compute_levels`（第 1081 行）、`ensure_label`（第 1564 行）、`run_sub_issue` 里的 `gh issue create --parent` 调用（第 1580 行起） | 新增一个 `verify-ticket.py <spec> --publish --drafts <dir>`（或放进 `dispatch` 的脚本里），读同一批草稿，按拓扑序建 issue、挂 sub-issue、打 label、连 blocking link，打印草稿名到 issue 号的对照表，再对 spec 跑一次 `--lint`。标题和正文出自同一个文件，错位不会再发生，sub-issue 数量和 label 也由脚本保证。剩余风险：脚本要有针对假 tracker 的测试（`mmw-v2/tests/verify-ticket/` 已有假 `gh` 的做法）；脚本上线之前这两段文字必须保留 | 第 7 步第二段压成：label 规则（`ready-for-agent` 加 worker label；`ready-for-human` 不带 worker；都带 `mmw:ticket`，这些写进草稿的 `LABELS:`）加一行发布命令。第 8 步删前两条。约省 130 词 |
| A2 | `SKILL.md` `### 8. Read every ticket back` 第三条「On each ticket an agent works, **Read first** and **Seam** are present and non-empty…」（第 155 行，52 词） | 1（兼 5） | 这些都是精确检查：三个节在不在、是否为空，`## Owns` 每条是不是仓库相对路径（不以 `/` 开头、不含 `..`、不是裸 `**`）。commit `95e05b11` 的说明写明留下这条是因为「no script makes them」。`SKILL-SET-REVIEW.md` `### Scripts and judgement` 第三条：「A rule a script could check exactly becomes a check」。我对两个仓库全部已发布的 158 张 `mmw:ticket`（`chancheuklap/multi-model-workflow` 84 张，`agentflow-hq/agentflow` 74 张）逐张核对，没有一张 agent 票缺这三节，`## Owns` 也没有一条绝对路径、`..` 或裸 `**`。所以这条人工核对从没有抓到过东西（有一种可能分不清：发布前已被它自己修掉了） | `lint_criteria`（`verify-ticket.py` 第 3583 行）对带 `## Acceptance criteria` 的票加一条 ERROR：缺 `## Read first` / `## Seam` / `## Owns` 或为空、`## Owns` 条目格式不对。这样 `--drafts` 在发布前就能拦下，比发布后读回更早。`owns_globs`（第 485 行）现在对绝对路径照单全收，这条检查也一并补上了这个口子。「baseline 行要标明」属于判断，模板 `## Read first` 已经写了，read-back 里不必再说 | 删第 8 步第三条；模板 `## Owns` 里的「No absolute path, no `..`, no bare `**`」保留（写的那一刻读得到）。约省 50 词 |
| A3 | `references/person-ticket.md` 第 5 行「It is shorter than the template below and holds **the five things** only」 | 3（搬家残留，而且指错了） | 这句是 commit `455667e7` 之前在 `SKILL.md` 里写的，当时下面就是模板；搬进这份 reference 后，下面只有 the five things 清单，没有模板。`triage` 的 `SKILL.md` 第 83 行也直接指向这个文件，triage 的 agent 读到「the template below」会找不到对象 | 无功能损失 | 改成「It is shorter than the `<issue-template>` in `SKILL.md` and holds…」，或者删掉「It is shorter than the template below and」，只留「It holds **the five things** only」 |
| A4 | `references/ambiguity-scan.md` `## Scan` 末句「For each category with Partial or Missing status, add a candidate question opportunity unless the answer would not change what a ticket delivers or what its criteria check.」，以及同节「mark status: Clear / Partial / Missing. Keep an internal map for prioritization (do not output it).」 | 6 / 4 | 「答案会不会改变票交付什么、判据查什么」这个过滤条件，在 `## Questions` 第一条约束里又原样出现一次。标 Clear/Partial/Missing、建内部表而且不输出，是在规定 agent 的思考过程，而这次扫描的产出只有最多 5 个问题 | `## Questions` 第一条约束承担过滤；分类清单照旧当覆盖面清单用 | 删 `## Scan` 末句，状态标记那两句改成「Walk every category below.」。约省 45 词。分类清单本身（抄自 spec-kit）保留：它给扫描提供覆盖面，数量上限由 5 个问题管着 |
| A5 | `references/cutting-interface-tickets.md` `### Boundary criterion` 首句「The **boundary criterion** is the line written onto the ticket, run by a shell months later with no model between.」与 `### Harness guard criterion` 首句「Written onto the ticket, run by a shell months later with no model between.」；`### Journey criterion` 末段「A break journey starts and stops the whole stack twice…TIMEOUT…」 | 6 | 「由 shell 跑、中间没有模型」对每一种判据都成立，却只在两种判据下各写一次，读的人会以为另外两种不一样。`TIMEOUT:` 的规则在 `SKILL.md` 模板末段已经完整写过（第 201 行） | 移到 `## Criterion shapes` 开头说一次；TIMEOUT 由模板那段承担 | journey 那段只留「A break journey is the slowest criterion on a ticket; give it a `TIMEOUT:` when it needs more than ten minutes.」。约省 50 词 |
| A6 | `SKILL.md` 第 1 步和第 3 步的 `Done when` 行（第 20、46 行） | 4 | 第 1 步那行重复了上一句「fetch it and read its full body and comments」；第 3 步那行重复了本步的规则。这些行来自审计条目 L6/TS-L7「每一步都要有 Done when」，是按格式补的。第 4、5、6、8 步的 `Done when` 确实在汇总本步的判据，应当保留 | 本步正文承担 | 删这两行，或者接受这个格式约定。约省 35 词，优先级低 |
| A7 | `SKILL.md` 第 4 步「`CHECK:` takes the object it checks from one of two places…」一段（第 82 行，94 词） | 2（仅部分） | 这段的具体写法（`$MMW_TICKET`、branch 名 `issue-<n>`、`sub_issues` API）只在被测对象就是 tracker 流水线本身时才用得上：`$MMW_TICKET` 在本仓 84 张票里出现在 33 张，在 agentflow 74 张里一张都没有。不许「搜出来取第一个」这条规则本身是通用的，而且有真实事故（merge-note 第 20 行） | 通用规则保留 | 可压成「A `CHECK:` names its object exactly (this ticket, from `$MMW_TICKET`, or a number the ticket names); it never searches and takes the first hit, which checks whatever the search returns and often cannot fail.」约省 30 词。优先级低，不做也可以 |

没有找到第 3 类的日期、「no longer」、issue 号残留。第 5 类（过度防御）只有 A2 那一条，而且它的修法是改成脚本，不是直接删。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 4 步「**A criterion is decided by a command, or it is not a criterion.** … that is what makes "it passed" a fact rather than the opinion of whoever wrote the code.」：整个 `## Acceptance criteria` 为什么存在，就是这一句。
- 第 4 步第 3 问「The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured.」：这句划清了 reaction 票和「让 agent 代看」之间的界线。
- 第 4 步第 4 问「That ticket builds it: a criterion that assumes a mechanism nobody builds fails on the night it first runs.」：把「到达状态」当成需要有人负责建造的工作，而不是默认存在的前提。
- 第 4 步第 5 问「The user is here now, so ask them」：出票这一场的角色定位全靠这半句撑着（见下面缺口 1）。
- 第 4 步「**A criterion is also exposed to the rest of its own batch.**」一段：告诉 agent 一条判据会被同一批后面的票判定，这是从单张票走到整批视角的唯一一处。
- 第 4 步 `EXPECT:` 的「**success-only marker** … `ok`, `passed` or `done` on their own also appear in failing output」：`gate-lint` 的 `weak-expect` 也会报，但写判据那一刻 agent 需要的就是这个理由。
- 第 6 步 `Worker` 一行「wrong **silently** … because none of those fail on the day they are written」：给出分级的判据，而不是一个标签名。
- 第 5 步「**What a ticket creates is put in service by an edit to something it did not create**」：agentflow #748–#752 那一夜得出的结论，任何清单都代替不了。
- 第 3 步 wide refactor / expand–contract 一段（上游原文）与第 2 步「Make the change easy, then make the easy change.」（上游原文）。
- 模板 `## Owns`「this section says where this ticket may write, not where its own code lives」「Find those places by grepping the name, not by listing from memory」「the toolbox is improved in use, and the change is made there at once」（最后这句是用户的既定决定，见 Nowledge Mem「mmw 当场改、走自身队列，产品票不塞流程工具活」）。
- 模板 `## Read first`「a **baseline**: a contract, not a reference」。
- `references/person-ticket.md`：「This is the only exit in the pipeline that owes no account to a machine, so it attracts whatever the writer did not want to think about; being unable to name the kind is the sign…」「read later, on a phone, by someone carrying none of your context」「so the answer can be something other than "I couldn't say"」「This is the edge that matters most in the batch」。这四句是整个技能里写读者和写动机写得最好的地方。
- `references/ambiguity-scan.md`「It is very likely that important decisions are missing or ambiguous, even if the spec looks good on the surface. Be skeptical, adversarial…」。
- `references/cutting-interface-tickets.md`：`### Journey criterion` 中 smoke journey 不带 `--break` 的理由；`## acceptance ticket`「A journey drives the real product with nothing mocked, so an operation that does not exist yet fails it at the first write, and the blockers are derived from the flow's rows, not from the list of ticket kinds」；`## design-system ticket`「A design system built from an existing product's code counts: … copying it back changes the product」；`## reaction ticket`「judges what no story render shows」。

### 缺口与补充草稿

- **`SKILL.md` 开头（第 8–10 行之后、`## Process` 之前）**：缺一段说明票的读者，以及这一场在流水线里的位置。现在开头只有上游那一句「Break a plan, spec, or conversation into a set of tickets」。一个全新的 agent 读完不知道：做票的 worker 看不到这段对话、夜里没人可问；判据由 shell 机械地跑；边决定当晚哪些票并行；这是最后一次三方（spec、代码、用户）都在场。后果是 agent 把切票当成「写任务列表」，把「这个到时候 worker 自己看着办」留在票里。第 5 问、第 4 问和 `person-ticket.md` 各自说了一小块，但没有一处把它们连成出票的态度。上一轮 `e74e0140` 删掉的第 5 问末句「nothing the ticket writer chose is left for the night」就是这层意思，删掉后没有别处再说。
  > A ticket is read by people and agents who were not in this conversation and cannot ask it anything. A worker picks it up at night, reads this ticket and what its **Read first** names, writes only inside its **Owns**, and is done when every `CHECK:` under it passes in a shell with no model in between. A reviewer in another session judges it against the spec sections its **Parent** names. The user reads the `ready-for-human` ones in the morning. This session is the last one that holds the spec, the codebase and the user at once, so decide here what can be decided: a choice left open is made at night by a worker who cannot ask, a missing edge becomes a merge conflict or a worker building on something that does not exist yet, and a criterion that cannot fail lets wrong work close.

  放在这里，第 4 步第 5 问、第 5 步和第 6 步的每条规则都有了共同的理由。它会改变 agent 的做法：遇到清单外的模糊点，它知道应该现在去问用户，而不是写进票里交给别人。

- **模板 `## What to build`（第 169 行）**：上一轮 `e74e0140` 删了「A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph.」，理由记在 merge-note 第 30 行「这条理由只写在这里，模板里不写」。但 `dispatch` 的 `references/night.md` 第 149 行的 main agent 夜里写票时只读这个模板，它读不到 merge-note。删掉以后，「numbered points, one thing per point」就只剩一条格式要求，没有了目的：agent 会照格式分点，但不会意识到每一点都要能脱离上下文单独读懂。建议恢复原句（24 词）。

- **第 5 步开头（第 92 行之后）**：缺一句「边就是当晚的排程」。现在这一步讲的都是怎样避免写同一个文件，没有说边的另一面代价：多一条不必要的边，就会让夜里本可并行的票排队。第 6 步 quiz 问用户「does each ticket only depend on tickets that genuinely gate it?」，但出票的 agent 自己拿不到判断这件事的依据。
  > The edges are the night's schedule: every ticket whose blockers have landed starts at once. A missing edge sends two workers into the same file or one onto work that is not there yet; an edge that gates nothing makes the night wait for no reason.

- **第 3 步 `<vertical-slice-rules>` 之后**：没有任何关于粒度的判断依据。上游的「sized to fit in a single fresh context window」按用户裁定删掉了（merge-note 第 40 行：尺寸不设机械上限，由 quiz 问用户）。草稿不设上限，只给一个与边相关的判断，和那条裁定不冲突，但因为它碰到了这条裁定，写在这里请用户过目：
  > Split where the parts can run at the same time or where one part's criteria can fail without the other's; keep together what would write the same files, since splitting that only adds an edge.

- **`references/ambiguity-scan.md` 开头第二段之后**：扫描的 agent 不知道自己的问题最后给了谁、为什么要一次问完。文件里有「Present every question in this pass. This is not a sequential loop.」，但没有理由。Nowledge Mem「切票前找漏一次给全问且只读」记着这条理由：用户当时在看切分清单，不是在接受访谈。有了理由，扫描 agent 才会按「这个问题值不值得占用户一行」来挑问题，而不是凑满 5 个。
  > Your questions reach the user beside the proposed tickets, in one list, and each answer is written into a ticket before anything is published. What you do not ask is decided later by a worker who cannot ask anyone, so spend your five questions where a wrong guess would change what gets built or what its criteria check.

- **第 6 步 `Worker` 一行（可选，约 10 词）**：`e74e0140` 删了「This line is the only time the grade passes a person's eye.」。恢复这句，agent 会把那一行理由写成用户能据以判断的内容，而不是随手一写。

与 `SKILL-SET-REVIEW.md` 的冲突：`### Redundancy and bloat` 把「the maintainer's reason for a design」归到 ADR。上一轮据此删了 `## What to build` 的读者句和 Worker 一行的理由句，但这两句说的是产出的读者是谁，会改变写作行为，属于该段后半「a reason the agent needs to decide an edge case」那一类。按任务书，这两句应当恢复。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `SKILL.md` 第 5 步「**Three or more on the same files**: a chain that long works the night one ticket at a time. Cut a **prefactor ticket**…」 | 「三张及以上」是一个编出来的阈值。真正要判断的是：这条链会不会把夜里相当大一部分工作排成单线。两张票如果都很大，串行代价同样高；三张小票串行可能无所谓 | 「When several tickets must write the same registration files and chaining them would make a large part of the night run one ticket at a time, cut a prefactor ticket…」。后半句（按条目拆共用文件、一整段逻辑的共用文件不拆）保留 |
| C2 | 真正依赖顺序、必须保留的部分 | 第 4 步写判据要在第 5 步连边之前（连边要知道每条判据得看见什么）；第 5 步要在第 6 步 quiz 之前（prefactor 票要让用户看到）；第 6 步先扫描、再列清单（问题要进 **Choices**）；第 7 步先 lint 草稿、再发布；第 8 步最后对 spec 跑 lint（只有这次看得见 tracker）。the five questions 的顺序也是真实的：第 2 问排在第 3 问前，这是 reaction 票与 code-review UI axis 的分界（merge-note 第 129 行） | 保留编号和顺序，不必放开 |

除这两条外，没有找到把判断写成硬流程的地方。第 4 步的三条措辞规则和 the five questions 本身就是判断框架，不是 SOP。`cutting-interface-tickets.md` 里那些看起来机械的规则（每个 `calls` 不为 `none` 的行一条 boundary criterion、每个 mount 进 story criterion），`--lint` 的 `lint_screen_contract` 会逐条执行，所以它们是「脚本之后会拿来判定的精确规则」，按 `### Scripts and judgement` 第二条就应该写在文本里。

## 脚本

技能自己没有脚本。它依赖的 `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 由 verify-ticket 的调查员负责，这里只记和本技能有关的三点：

1. **缺一个发布命令**（见 A1）。`lint_drafts`（第 3816 行）已经能读草稿、建图、查 label，再往前一步就是按同一份草稿发布。现有的 `DRAFTS_NOT_CHECKED`（第 3773–3778 行）列出了草稿阶段查不到的三样（sub-issue 与 label、blocking link、标题对 `## What to build`），发布脚本能让前两样和第三样里的「错位」不再可能发生。
2. **`lint_criteria` 不查 `## Read first` / `## Seam` / `## Owns` 在不在、格式对不对**（见 A2）。`owns_globs`（第 485 行）接受任何非空的首个词，包括绝对路径。
3. 可选，未见触发证据：「能同时跑的两张票 `## Owns` 不相交」可以在 `lint_batch_graph` 里做保守检查（完全相同的路径，或一条 glob 的固定前缀覆盖另一条）。它有图（`compute_levels`）也有各票的 `owns_globs`。我没有找到已发布批次里 `## Owns` 重叠的实例；agentflow #748–#752 的冲突恰恰是因为 `## Owns` 没写全而不重叠，这个检查抓不到那一类。所以只作为选项，不作为删除第 5 步文字的前提。

没有看到本技能相关的死代码或重复校验。

## 与其他技能的重复或交接问题

- `mmw-v2/skills/dispatch/references/night.md` 第 149 行按标题「**4. Write each acceptance criterion**」引用第 4 步；`verify-ticket.py` 第 3777 行的输出文字写着「the read-back of to-tickets step 8」；`mmw-v2/skills/verify-ticket/references/linting.md` 第 17 行引用「step 7 **Publish the tickets to the configured tracker**」。按 A1/A2 改第 7、8 步时，这三处要一起改。
- `## Owns` 的两条规则（让新文件投入使用的文件归本票；能同时跑的两张票不重叠、否则加 **Blocked by**）在第 5 步和模板 `## Owns` 各写一次。两处都应保留：night.md 的 main agent 只读模板，切票的 agent 在第 5 步按整批来做。这是两个读者各在自己动手的那一刻读到，不算冗余。
- `references/person-ticket.md` 同时服务本技能和 `triage`（`triage/SKILL.md` 第 83 行）。A3 那句指错的话对 triage 的读者影响更大。
- 描述（frontmatter `description`）写「Break a plan, spec, or the current conversation」，而第 1 步要求没有已发布 spec 的计划先走 `to-spec`。这不矛盾（计划触发本技能，本技能再把它转去 `to-spec`），不需要改。
- `references/cutting-interface-tickets.md` `## Criterion shapes` 是 `ui-acceptance` 四份 reference 指过来的唯一出处（`ui-acceptance/SKILL.md` 第 20 行，`boundary-check.md` 第 7 行，`harness-guard.md` 第 23 行，`journey.md` 第 41 行，`story-parity.md` 第 99 行）。按 A5 改动时不要改动这个标题。

## 没查到的

- 没有读 `verify-ticket.py` 的 `lint_screen_contract`（第 3328–3566 行）全文，也没有读 `gate-lint.mjs` 的 `WEAK_EXPECT` 集合的定义；关于它们查什么，我依据的是 `references/linting.md` 和函数签名。
- 没能验证 A2 那条核对是否曾在发布前抓到过缺节：我看到的只是 158 张票的最终状态。
- 「8 张票标题错位一格」只见于 merge-note 第 29 行，没有找到对应的 issue 或日志。
- 没有核实 ambiguity scan 在真实出票时是否返回过问题、这些问题是否进了 **Choices**（quiz 只出现在会话里，tracker 上没有痕迹）。
- `reaction` 票是否每批界面票都必须有一张（`## reaction ticket`「One extra *reaction* ticket」），我当作用户的产品决定，没有评价。
