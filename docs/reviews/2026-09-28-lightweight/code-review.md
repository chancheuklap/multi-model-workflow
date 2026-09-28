# code-review

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能的规则大多有理由，缺的是三处"为什么"，而且都被前几轮挪进了 reviewer 读不到的 merge-note：审查是第一次由非作者来读、漏报的东西会原样合进去；Tests 轴是唯一追问"绿是否证明了什么"的读者；作者很少删自己刚加的代码，所以"能不能更短"只有 Standards 轴会问。每个 axis 是一个 subagent，只读 `SKILL.md` 和自己的文件，看不到 session 的内容，所以共同的那一句放在 `SKILL.md`。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md`，`# Code review` 之后、`## Find your moment` 之前 | A worker wrote this diff and the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: what it reports, the worker fixes before the ticket closes; what it misses ships. | axis 拿不准一处是否值得报时：没有这句，会按"清单检查器"的习惯少报；有了它，知道漏报的代价是原样合入。Opus 5 的官方指南提醒过，审查提示里一旦暗示"保守"，模型就会照字面少报。 |
| I2 | `references/tests-reviewer.md`，开头那句之后（恢复 `698659e4` 删掉的原文，去掉与 I1 重复的一句） | Every other check in the landing pipeline runs these tests and believes them. You are the only reader who asks whether a green result proves anything. | 看到一个测试跑绿、写法也整齐时：没有它，会当风格检查放行；有了它，会去问"去掉被测行为，这个测试还会绿吗"。 |
| I3 | `references/standards-reviewer.md` `## 3.`，"Alongside the smells, ask of every hunk…" 之前 | An author rarely deletes what it just added, so extra code this axis does not name stays in the repository. | 把 less-code 这一问从"可有可无的附加项"变成本轴的职责。这是本仓对"代码要轻"唯一的一道检查。 |
| I4 | `references/session.md` §3 开头 | The axes read the code in slices, and some of what they report is wrong. The worker treats every in-ticket line as work to do before the ticket closes: a false finding you pass on costs a fix round and can break code that was right; a real one you withdraw ships. | 核实时两种错都有代价。没有它，session 容易照单转发，或者为省事轻易撤回。72 条评论里 43 条有 `## Withdrawn`，说明 axis 报错是常态，核实这一步是真实在用的判断。 |
| I5 | `references/session.md` §4，"A review finding is **in-ticket** when…" 之前 | The split asks whose work the repair is: in-ticket means this ticket should not close with it unfixed. | 给六个条件一个共同的原则，清单外的情况（同时碰到本票 criterion 和别的票的 `## Owns`）有了判断方向。六个条件与"已并入的票"那一段原样保留：后者已经写明修复落点决定归属。 |
| I6 | `references/tests-reviewer.md` §1，"whether they assert the four columns" 改为右栏 | whether they assert the row's four columns (`calls`, `shows`, `next`, `on_failure`). | 术语修正：Tests 轴不读定义 "four columns" 的 `ui-acceptance` 文件，只拿到这几个字无法检查。 |
| I7 | 四个 axis 文件的 `Under 400 words.`，改为右栏（数字保留，加理由） | Under 400 words: the worker reads all of it before fixing anything. | 72 条评论里 Standards 轴 56 次超过 400 词（中位数 826）。按 advisor 意见，不遵守说明的是这个数字缺理由，而不是数字无用；数字保留，补上理由。各文件已有 "One entry per review finding; nothing that is not a finding." 这一句不动。**未验证**：换成理由后报告能否变短，要在修复后的真实审查里看。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `references/spec-reviewer.md` `### Read tickets already integrated into the base branch` 第一段 "Read the newest `worker.started.base` from this ticket's events. Between that commit and…" | 新增一个只读命令，复用 `dispatch.sh` 的 `integrated_ticket_numbers` 与 `newest_worker_field`，打印本票 worker 开工以来并入的票号；这一段换成"运行它，读它列出的每张票和它的 closeout 评论"。四个审查角度与 "do not trust its verdict as proof that the combined result is correct" 保留。 | 确定性算法，且手工做出过错（mmw #413：取了第一个 base 而不是最新的）。 |
| D2 | `references/standards-reviewer.md` `## 3.` deletion test 段中 "name the module and the callers the complexity would reappear in." | 删这半句，保留 "A pass-through is a review finding." | 同文件 `## 4. Report` 第 4 条逐字同义，写报告时读的是那一处。 |
| D3 | 四个 axis 文件的第一节（`## 1. Read the diff` 与单独的 `gh issue view` 代码块） | 并成各文件开头一句："Read the ticket (`gh issue view <ticket>`, comments included) and the diff against the merge-base (`git diff <base-commit>...HEAD`)."，后面各节编号顺延。`standards-reviewer.md` §2 "Read what you find before you read the diff a second time." 保留。 | 读票、读 diff 是默认动作；唯一非默认的信息是三点 diff，留在命令里。 |

### 不采纳

- 调查员 B4（"This session ends; the ticket outlives it…"）：§2 的 "The worker that started you is asleep on your report" 已经给了必须贴评论的理由。
- B6 的后半（"Out-of-ticket findings are just as real…"）：§4 末句已写明它们变成 child、不阻塞。
- B7（UI 轴补句）：开头的问题和第 31 行 "Report only what that comparison does not cover" 已经是这个意思。
- C1 新加的判断句：`session.md` §4 第 61 行已经写了"修复落点只在别的票 `## Owns` 里就是 out-of-ticket"。
- C3（把 reviewer Rules 传给 axis）：当前生效规则为 0 条；你在 9 月 23 日的复审里定过"以后启用规则时再修"。记录，不在这一轮做。

### 连带改动

- `mmw-v2/merge-notes/code-review.md` 第 7、9、31 行写着"只写在这里""`SKILL.md` 只放那张表"。改为：I1–I4 这类理由句写在技能正文，merge-note 只记设计来历。否则下一次拉上游或修剪的人会按 merge-note 把它们再删掉。
- 草稿都没有 em-dash（`check_upstream_em_dashes.py` 会拦 `mmw-v2/upstream/skills/` 下的 em-dash）。

## 结论

体量：`mmw-v2/upstream/skills/engineering/code-review/` 装进宿主的正文约 4,410 词（`SKILL.md` 104，`references/session.md` 1,161，`references/spec-reviewer.md` 1,070，`references/standards-reviewer.md` 801，`references/tests-reviewer.md` 772，`references/ui-reviewer.md` 502），没有脚本；上游原版 `SKILL.md`（squash 提交 `5b1a4c51`）1,064 词。多出的部分几乎都对应真实功能（Tests 轴、UI 轴、finding 核实、in-ticket/out-of-ticket 分拣、`DECISIONS` 判断、已并入票的交叉审查、`--review` 通道），而且在本仓 72 条已贴出的 `REVIEW` 评论里都有使用痕迹；这个技能的主要问题不是冗余。主要问题有三个：一是"灵魂"被放错了地方，前几轮把 agent 需要的几条理由删掉或挪进了 `mmw-v2/merge-notes/code-review.md`，而 reviewer 不读 merge-note；二是四个轴文件末尾的 `Under 400 words.` 从来没被遵守（Standards 轴 72 次里 56 次超过，中位数 826 词）；三是 Spec 轴里有一段让 agent 手工完成的确定性计算（找出已并入 base branch 的票），`dispatch.sh` 里已经有同一段逻辑。可删约 120 词，建议补约 230 词，净增约 100 词，不丢功能。灵魂只有一部分完整：session 与 Spec、Tests 两个轴的"不做什么"写得很好；缺的是所有读者都会经过的那句"这次审查是为了什么"，以及 Tests 轴开头那段被删掉的话。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `references/standards-reviewer.md` `## 4. Report` 末句、`references/spec-reviewer.md` `## 4. Report`、`references/tests-reviewer.md` `## 4. Report`、`references/ui-reviewer.md` `## 3. Report`：`Under 400 words.` | 4（写成硬数字的规则，实际从未生效） | 从 `gh issue list -L 600 --label mmw:ticket` 取出 72 条 `REVIEW` 评论，按 `## ` 小节数词：Standards 72 次中 56 次超过 400 词（中位数 826，最大 1,955），Spec 47 次超过（中位数 602），Tests 30 次超过（中位数 290），UI 6 次均未超过。`SKILL-SET-REVIEW.md` `### Scripts and judgement`："A numeric limit is enforced by the mechanism; models do not copy literal numbers reliably." | 没有脚本检查长度；`verify-ticket.py` 的 `run_review` 只校验首行和 `## In-ticket` 行的形状。删掉以后，靠一句理由约束长度。剩余风险：报告长度本来就不受这个数字约束，所以不会变得更差 | 把这个数字换成它背后的理由，四个文件各一句，例如："The worker reads this whole report before it fixes anything: one entry per finding, and no restating of the diff."（`mmw-v2/merge-notes/code-review.md` 里 `Under 400 words.` 那一行写的正是这个理由，只是没写进技能） |
| A2 | `references/spec-reviewer.md` `### Read tickets already integrated into the base branch` 第一段："Read the newest `worker.started.base` from this ticket's events. Between that commit and the base commit…" | 1（脚本能做的确定性工作）+ 6（逻辑重复） | 这段是一个确定的算法：从票的事件里取最新的 `worker.started.base`，沿 first-parent 历史挑出主题恰好是 `Merge branch 'issue-<n>'` 的提交。`mmw-v2/skills/dispatch/scripts/dispatch.sh` 的 `integrated_ticket_numbers`（约第 2472 行）已经用同一条 `git log --first-parent` 和同一个 sed 模式做了 git 那一半，`newest_worker_field` 做了事件那一半。这段算法已经出过一次真实错误：`mmw-v2/merge-notes/code-review.md` `## The Spec axis reviews tickets integrated into the base branch` 记下 mmw #413，当时取了第一个 base 而不是最新的，结果把票自己之前的落地当成了兄弟票来读 | 由一个只读命令承担，它打印出"本票 worker 开工以来并入的票号"（复用上面两个函数，挂在 `dispatch.sh` 的只读子命令或 `verify-ticket.py` 上，由修改者做工程决定）。剩余风险：要新增一个子命令和它的测试；axis 的 prompt 按 session §2 只有一句话，所以这份列表只能由 Spec 轴自己运行命令取得，不能塞进 prompt | 保留四个审查角度（`Combination behavior` 等）和 "do not trust its verdict as proof that the combined result is correct"；把第一段的取数步骤换成"运行 `<command> <ticket>`，读它列出的每张票和它的 closeout 评论"。约减 60 词，并去掉一个已知的出错点 |
| A3 | `references/standards-reviewer.md` `## 3.`，deletion test 一段中的 "A pass-through is a review finding: name the module and the callers the complexity would reappear in." | 6 | 同一个文件的 `## 4. Report` 第 4 条 "Every module the deletion test calls a pass-through: name it and the callers that would carry the complexity back." 意思一样；`## 4` 前三条也分别复述了 `## 3` 里 less-code 和 smell 的报告方式。两处是同一个 agent 在同一时刻读到的 | `## 4. Report` 留着这份（写报告时读的是它） | 删掉 `## 3` 那半句，保留 "A pass-through is a review finding."。约减 15 词 |
| A4 | 四个轴文件的第一节（`standards-reviewer.md` `## 1. Read the diff`、`spec-reviewer.md` `## 1. Read the diff`，以及 `tests-reviewer.md`、`ui-reviewer.md` 第一节里单独放的 `gh issue view <ticket>` 代码块） | 2（agent 默认就会做的事）/ 4（多余的层级） | 读票、看 diff 是每个轴默认就会做的事；三条命令里唯一不是默认的信息是三点 diff（`...`）。`references/session.md` §1 已经说明了三点的理由，只是 axis 不读 session | 由开头一句承担，三点写法保留在命令里 | 把第一节并进各文件的第一段，写成一句："Read the ticket (`gh issue view <ticket>`, comments included) and the diff against the merge-base (`git diff <base-commit>...HEAD`)."；后面各节的编号顺延。四个文件合计约减 40 词，少四个标题。优先级低 |

以下几处看上去像冗余，查过之后**不是**，不要删：

- `references/session.md` 第 1 节失败路径（"A ref that does not resolve or an empty diff…Post it as the review (step 5)…"）：72 条评论里一次也没触发过，但正常输入可以走到。`implement` 允许一张票"Green before work"，也就是 diff 可以是空的。删掉以后，reviewer 不贴评论就结束，worker 会一直等下去。
- `references/session.md` 第 2 节不能起 subagent 的分支：当前 `~/.mmw/models.json` 里 reviewer 一行是 `claude`，所以现在走不到；但 `models.py config set` 属于正常配置，改了就能走到，而且只有 50 词，保留。
- `references/session.md` `## Active Rules`：当前本仓 space 的 `nmem context read --agent-id mmw-reviewer` 返回 `status: empty`，规则数为 0，每次 reviewer prompt 里都是 `none`。但这是 retro 一批准规则就会用上的现成功能，不属于过度防御。它的问题在 C3。
- 每一步末尾的 `Done when …`：这是 `writing-for-agents/SKILL.md` `## Steps and completion criteria` 要求的完成标准，不算重复。

## B. 灵魂

### 保留，勿删

- `references/session.md` §2 "so they run at once and never see each other's findings"：这是轴之间保持独立的理由，也是上游那句 "so they don't pollute each other's context" 的延续。
- `references/session.md` §2 **Hold this turn…** 整段，连同 "The worker that started you is asleep on your report…"：它让 session 明白自己中途结束回合会让谁卡住（背后的机制见 merge-note `## 报告和报信是同一次调用`）。
- `references/session.md` §3 "Judge whether the problem is real, not whether the proposed fix is plausible. Code that loudly fails on a situation you never showed the program can reach is correct behavior, not a defect." 与 "A true fact about nearby code that does not disprove the claim does not count."：这是核实这一步的判断标准。72 条评论里 43 条有 `## Withdrawn`，说明这个标准一直在用。
- `references/session.md` §3 "You report: you do not assign severity, fix a finding, or drop one because its fix looks large."：划定 reviewer 的职责边界，防止它因为修起来麻烦就把 finding 静默丢掉。
- `references/session.md` §4 末句 "In-ticket findings get one round of fixes on this ticket; out-of-ticket findings become `finding` children…"：分拣的人要知道分拣的后果，靠的就是这一句。
- `references/session.md` §5 "Rank nothing across axes and merge nothing between them: the separation is what keeps a passing axis from covering a failing one." 以及后面三条对照：这就是上游 `## Why two axes` 在本仓的对应文字，`SKILL-SET-REVIEW.md` 第 53 行点名这类内容要保留。
- `references/session.md` `## Active Rules` "A Rule is never a finding's source, and neither are Memory, the worker's reasoning or its self-assessment…"：它规定证据只能来自当前的票、spec、仓库或检查结果。reviewer 的宿主装有 Nowledge Mem 插件，确实会注入记忆，所以这句有实际作用。
- `references/standards-reviewer.md` `## 3.` 里的 **The repository overrides.** / **Always a judgement call.**，"Report it only when you can write the shorter form; a shorter form you cannot write is a preference, not a review finding."，以及 deletion test：这几条划出了什么算 finding、什么只是个人偏好。
- `references/standards-reviewer.md` `## What is not yours` "Report what you would report if they did not exist"：防止一个轴因为"别的轴会管"而放松标准。
- `references/spec-reviewer.md` §2 "The rest of the spec covers other tickets. Reading it makes you flag work that was never this ticket's to do. A baseline records a settled decision, so the diff answers to it exactly as it answers to those spec sections."：解释了阅读范围为什么这么窄、baseline 为什么同样有约束力。merge-note 也明确写了这句不能删。
- `references/spec-reviewer.md` `### Read tickets already integrated…` "do not trust its verdict as proof that the combined result is correct"，以及四个审查角度：这是判断方法，不是步骤，A2 只把取数那部分交给脚本。
- `references/spec-reviewer.md` §3 "Quote the requirement for each review finding. A review finding with no quoted line is your opinion about the design, which is not what this axis decides."：给出了 Spec 轴 finding 的成立条件。
- `references/spec-reviewer.md` `## What is not yours` 中 design package 一段的理由（"Appearance is decided by element parity…not by reading the package"）。
- `references/tests-reviewer.md` §4 "a criterion whose test holds up is worth as much as one whose test does not"，和 `## Two things this axis never reports` 整节（不报 coverage；不追加 acceptance criteria，理由是 "this axis setting the bar it then marks against"）：这是全技能写得最好的一段。
- `references/ui-reviewer.md` §1 "A `DIFF` line or a green `STORY OK` is not this axis's verdict; look at those images."，§3 "A temp PNG is gone when the session verifies."，以及 `## What is not yours` 的 "you look at a story render, and the person looks at the product."

### 缺口与补充草稿

草稿都不用 em-dash，因为 `mmw-v2/tests/lib/check_upstream_em_dashes.py` 会拦 `mmw-v2/upstream/skills/` 下的 em-dash。

- **B1 `SKILL.md`，`# Code review` 之后、`## Find your moment` 之前**：缺一句"这次审查是为了什么"。session 和每个轴都先读 `SKILL.md`，可现在这里只有一张路由表。轴的 subagent 从表跳到自己的文件，永远看不到 session §5 那三条对照，所以它不知道自己是这段代码第一个非作者读者，也不知道漏报意味着这段代码会原样合进去。结果是轴只把自己当成一个清单检查器。`SKILL-SET-REVIEW.md` 第 23 行本来就说 "`SKILL.md` holds what every task passes through"。与之冲突的是 merge-note 的"`SKILL.md` 只留那张表"，按本任务书，应以本条为准。
  > A worker wrote this diff, wrote the tests that prove it, and watched them pass. This review is the first reading by anyone who did not write it: the worker fixes what it reports tonight, before the ticket closes, and what it misses ships. Each axis answers one question on its own, because one change can pass one question and fail another, and a pass on one must not cover a fail on another.

- **B2 `references/tests-reviewer.md`，开头那句之后（恢复原文）**：commit `698659e4`（2026-09-23 "cut duplicated and dead text"）删掉了下面这段。它是 Tests 轴存在的全部理由，而且是别处没有的信息，同样的意思只留在 merge-note `## 第三个 axis：Tests` 里。少了这段，agent 会把 Tests 轴当成风格检查，看到"测试跑绿了"就放行，而这个轴要追问的正是"这个绿说明了什么"。
  > Every other check in the landing pipeline runs these tests and believes them. The worker who wrote them also wrote the code they test, ran them, and recorded that they passed. You are the only reader who asks whether a green result proves anything.

- **B3 `references/standards-reviewer.md` `## 3.`，"Alongside the smells, ask of every hunk…" 这句之前**：less-code 这一问的理由只写在 merge-note（"Standards axis 是唯一没写这段代码的读者，作者不会主动删自己加的东西"）。少了它，agent 会把"能不能更短"当成可有可无的附加项，而这其实是本仓对"轻"的唯一一道检查。
  > You are the one reader of this code who did not write it, and an author rarely deletes what it just added; extra code this axis does not name stays in the repository.

- **B4 `references/session.md` §5，"Write the report to a file…" 之前（恢复原文，稍作改写）**：commit `e74e0140` 删掉了 "The reviewer session ends; the ticket outlives it, and the worker who fixes these review findings reads the ticket, not your transcript. A report that exists only in this conversation reaches nobody."，merge-note 第 31 行说这条原则"只写在这里"。§1 的失败路径要求在"没东西可审"时也贴评论，缺了这句理由，agent 会觉得那是多此一举。
  > This session ends; the ticket outlives it. The worker reads the ticket, not your transcript, so a report, a failure report included, exists only once `--review` has posted it.

- **B5 `references/session.md` §3 开头**：只写了怎么核实，没写为什么要核实。按 `implement` 第 3 步，worker 会把每条 in-ticket finding 当作当晚必须修的活。没有这句，session 容易把核实做成走过场，照单转发。已有数据显示 axis 会报错，43 条评论里一共撤回了 42 条。
  > The axes read the code in slices, and some of what they report is wrong. The worker takes every in-ticket line as work for tonight, so a false finding you pass on costs a fix round and can break code that was right, and a real one you withdraw ships.

- **B6 `references/session.md` §4，"A review finding is **in-ticket** when…" 之前**：六个条件只是罗列，没有给出它们共同依据的原则。遇到清单外的情况，例如同时满足第 1 条和"已并入的票"那一段，agent 就没有方向。补一句原则，六条保留（merge-note 说明分拣要按字面条件路由，所以清单不能换掉）。
  > The split asks whose work the repair is. In-ticket means this ticket should not close with it unfixed: it breaks what this ticket promised or the planning it answers to, or it sits in code this ticket owns. Out-of-ticket findings are just as real; they become children so they are kept, not dropped.

- **B7 `references/ui-reviewer.md`，开头那句之后**：开头的问题（"does it show a problem that element parity does not cover?"）说了查什么，没说为什么只有这个轴能查到。补一句，agent 就知道该往哪里看。
  > Element parity reads only elements that carry a `data-ui` id. Anything else a person would see on this screen has no other machine reader before the owner opens the product, so look first at what the ids leave out.

- **B8 `references/tests-reviewer.md` §1 boundary 一段 "whether they assert the four columns"**：术语没有解释。"four columns" 定义在 `ui-acceptance` 技能的 `references/boundary-check.md` `## The four-column boundary test`，Tests 轴不读那个文件，只拿到这几个字的 agent 无从检查。改成：
  > whether they assert the row's four columns (`calls`, `shows`, `next`, `on_failure`).

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `references/session.md` §4 六条 in-ticket 条件，加上后面 "For a finding about a ticket merged into the base branch…" 一段 | 分拣被写成了按条件逐条对照，但两段之间有实际冲突：一个因已并入的兄弟票而打破本票 acceptance criteria 的 finding，按六条算 in-ticket（碰到了 acceptance criteria），按第二段却算 out-of-ticket（修复落在兄弟票的 `## Owns` 里）。按旧文本 "do not move it into the current ticket merely because the interaction exposed it"，意图是以修复落点为准，但现在的文字没有说出这一层 | 先写原则（B6 草稿），再列六条；然后把第二段写成那个唯一的判断点："When a finding touches this ticket but its repair lies only inside another ticket's `## Owns`, the repair target decides: out-of-ticket." 这是 agent 最容易判错的地方 |
| C2 | 四个轴文件的 `Under 400 words.` | 数字上限在实践中不生效（见 A1） | 换成理由（见 A1） |
| C3 | `references/session.md` §2 "Nothing else: the skill is what they read…" 与 `## Active Rules` "Apply each Rule…to decide what to inspect" | 按 §2，axis 的 prompt 只有一句话，Rule 行传不到真正做检查的轴；session 自己只在 §3 核实已报出的 finding，没有地方"决定检查什么"。`## Active Rules` 又放在 "Done when `--review` exits 0." 之后，处于步骤流之外。现在规则数为 0，所以还没出过问题；retro 第一次批准规则时，这条规则会落空（这是推断，没有实测） | 工程上二选一，由修改者决定：(a) Rule 行不是 `none` 时，session 把它们原样附在每个 axis prompt 的那一句之后（作为数据），各轴文件加一句 "Apply any reviewer Rules your prompt lists, within their scope, to decide what to inspect; a Rule is never a finding's source."；(b) 在 §3 核实之后加一次由 session 自己做的 Rule 检查。建议选 (a)，因为检查本来就在轴里做。同时把 `## Active Rules` 挪到 §2 之前 |
| C4 | `references/spec-reviewer.md` `### Read tickets already integrated…` 第一段 | 把确定性算法写成了 agent 的手工步骤（见 A2） | 改成一条命令，外加判断方法 |
| C5 | 四个轴文件的 `## 1.`…`## 4.` 编号标题 | 读票、读 diff、读规范、报告的顺序是作者的习惯，只有"先读规范再读第二遍 diff"（`standards-reviewer.md` §2）真正依赖顺序 | 见 A4；保留 standards §2 那句先后要求。优先级低 |

**必须保留的顺序和格式**（脚本依赖它们，不能放开）：

- 首行 `REVIEW <base>..<HEAD>`：`verify-ticket.py` `run_review` 用 `REVIEW_HEAD_RE` 校验，不符合就拒绝。
- `## Standards`、`## Spec`、`## Tests` 的先后（"in that order"）：`spec_judgement` 和 `review_problems` 用 "`## Tests` 之前、`## Spec` 之后" 切出 Spec 轴那一段，如果 Tests 排在 Spec 前面，`--touched` 和 closeout 就读不到 Spec 轴的判断。
- `## In-ticket` 的行格式：`in_ticket_findings` 用 `CAT_IN_TICKET_ITEM_RE` 匹配。
- `DECISIONS` 判断行必须把路径和 `should not`/`reasonable` 写在同一行：`spec_judgement` 按行匹配。
- `Missing` 行要以 row id 开头：`review_problems` 用它拦 closeout draft。
- `refuted` 这个词：与 `implement` 第 3 步用的是同一个词。
- axis 词必须是 `Standards`/`Spec`/`Tests`/`UI` 之一：它决定走 `SKILL.md` 表里的哪一行。

## 脚本

无。本技能目录下只有文本和 `agents/openai.yaml`。它调用的脚本分别属于 `verify-ticket`（`--review`）、`ui-acceptance`（`story-parity.py`）和 `dispatch`（启动 reviewer、`reviewer_rules_packet`），由那几个技能各自的调查员负责。与本技能直接相关的只有一条，已写在 A2：`dispatch.sh` 的 `integrated_ticket_numbers` 与 Spec 轴文本描述的是同一段逻辑。

## 与其他技能的重复或交接问题

- `refuted` 的定义句（"Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count."）在 `references/session.md` §3 和 `implement/SKILL.md` 第 3 步各有一份，两处原文相同。两边各自在行动时读到自己那份，一份给 reviewer，一份给 worker，**两份都留**。
- In-ticket 行格式在 `references/session.md` §5 写了一次，`verify-ticket.py` `run_review` 的拒绝信息里又写了一次。**留 session.md 那份**；拒绝信息只是兜底，按 `SKILL-SET-REVIEW.md` 的 Duplication 规则可以接受。
- Tests 轴第 3 节要读 `tdd` 技能的 `tests.md`、`mocking.md`：按 `SKILL-SET-REVIEW.md` 第 25 行的定义，这是一次 **jump**（第 25 行建议把内容搬到当前文件）；而按同一文件 `### Redundancy and bloat` 的 Duplication 规则，内容应该只在一处。两条规则在这里互相冲突。commit `e6b932bd` 选了"只在一处"。评论里有 Tautological 22 次、Only the happy path 30 次，说明现在的做法能用。只记录，**不建议改**。
- `mmw-v2/merge-notes/code-review.md` 里存着几条 agent 需要、却被明确写成"只写在这里"的理由：Tests 轴存在的理由、less-code 的理由、"ticket outlives the session"、DECISIONS 判断的用意。B2–B4 建议把前三条写回技能；merge-note 里对应的"只写在这里""`SKILL.md` 只放那张表"（第 7、9、31 行）要同步改，否则下次拉上游的人会按 merge-note 再把它们删掉。merge-note 本身约 215 行，属于维护者文档，不在 agent 的阅读路径上，这一轮不查它的冗余。
- 与 `to-tickets` 技能的 `references/cutting-interface-tickets.md`（reaction ticket 的边界）、`implement` 收尾第 2 步（`DECISIONS` 的格式）、`verify-ticket` 的 `references/sub-issues.md` 第 4 问（`finding` 只用于 `## Owns` 以外），交接都一致，没有发现矛盾。

## 没查到的

- 只看了本仓（`chancheuklap/multi-model-workflow`）的 72 条 `REVIEW` 评论，没有看消费方仓库（例如 merge-note 提到的 Chameleon）的评论。
- "Spec 轴确实在做已并入票的交叉审查"这个判断来自一个宽松的正则（72 条中 46 条的 Spec 段出现相关词），没有逐条读。撤回数据（43 条评论共 42 条撤回、605 条保留）是按列表行计数得到的，`None` 之类的行可能影响个别计数。
- `references/spec-reviewer.md` 里 "story page" 一段要求 `[data-story-root]` 放在根元素上，不能放在外层包装元素或子元素上。`story-parity.py` 只在找不到可见的 `[data-story-root]` 时拒绝，但放错位置是否一定会产生 `DIFF` 行（使这段检查变成机械就能覆盖）我没有验证，所以没把它列为可删。
- 没有验证 reviewer 会话只是结束回合、没贴报告时，watchdog 会不会发出 `reviewer.lost`。这决定了 session §1 失败路径删掉后的后果到底有多重；我按"worker 会一直等"来判断，这是推断。
- 没有读 `mmw-v2/upstream/docs/engineering/code-review.md`（给人看的文档页，不在 agent 的阅读路径上）。
- 没有运行任何测试或脚本；除了 `gh issue list`、`nmem --json context read`、`nmem --json m search` 和 `git show`/`git log` 这些只读命令，什么都没执行。
