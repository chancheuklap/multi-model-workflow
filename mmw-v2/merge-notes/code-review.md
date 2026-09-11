# code-review

源目录：`mmw-v2/upstream/skills/engineering/code-review/`

上游是一个文件：`SKILL.md` 里五步走完，两个 axis 的 brief 与 smell baseline 全文（Fowler 十二条 code smell）都排在步骤中间。我们把三个 axis 的规则各拆一份 reference file 出去，dispatcher 的步骤放在 `references/session.md`，`SKILL.md` 只做两扇门：会话走 session，轴走对应 axis 文件。轴 subagent 再调一次本技能、带上 axis 名，不读绝对路径。

拆的依据是读者：三份 axis 文件各只被一个轴读；`references/session.md` 从头到尾只有 dispatcher 一个读者，而且它每次都要读全；`SKILL.md` 被会话和三个轴共用，所以只留分门，正文不堆在门口。

## 哪一段挪去了哪个文件

| 上游 `SKILL.md` 的段落 | 落到 | 我们的意图 |
| --- | --- | --- |
| 第 1 步 pin the fixed point（三条 git 命令、三点 diff、空 diff 要在派 subagent 之前失败） | `references/session.md` 第 1 节 | 原文的判断一条没改。上游改这三条命令 → 收上游 |
| 第 2 步 identify the spec source（四级查找顺序：commit message 里的 ticket number → user 给的路径 → `docs/` `specs/` `.scratch/` 下按分支名找 → 问 user） | `references/spec-reviewer.md` 第 2 节，且换掉了 | 这条 landing pipeline 的 ticket 一定有 `## Parent`，四级查找的后三级是给没有 ticket 的场景用的。我们的读法是沿 `## Parent` 读 spec 点名的小节 + `## Testing Decisions` + `## Out of Scope`，加第四条 ticket `## Read first` 里标为 baseline 的条目，逐份读到结论；这套读法与 `implement` 的 narrowed reading 是同一套。节标题是「读 ticket 和它指向的东西」而不是只说 spec，因为范围不止 spec。理由：Spec axis 问的就是「有没有做 ticket 和 spec 要的那件事」，`## Read first` 就在它已经读全的那张 ticket 里，而 pipeline 里没有别的角色被要求核对 baseline 有没有被默默偏离；baseline 挂在清单外面会读成可选项。上游那句写了数（读「恰好三样」），我们的清单不写数，只说「读它指向的东西，别的都不读」：清单本身就是穷举，写了数每加一条要改一次，改漏了正文就自相矛盾。清单后面那句「baseline 记录的是已拍板的结论，所以 diff 对它负责的方式与对 spec 小节一样」是这条指令的意义，不删——少了它，subagent 只知道要读，不知道读出来的分量。上游改这一步 → 不收，除非它也变成从 ticket 走 |
| 第 3 步 identify the standards sources（repository 里哪些文件算编码规范）+ smell baseline 全文十二条 + 「The repository overrides」与「Always a judgement call」两条规则 | `references/standards-reviewer.md` 第 2、3 节 | 十二条逐条原文保留，措辞改成对 subagent 说的第二人称。上游增删 code smell → 收上游，改这个文件 |
| 无 | `references/standards-reviewer.md` 第 3 节两条规则之后的一段，与第 1 句的第二个问题 | 我们加的：每个 hunk 问一次「删掉、并进已有分支、换成 repository 已有 helper，acceptance criteria 是否仍过」，写得出更短形态才算 review finding。理由：Standards axis 是唯一没写这段代码的读者，作者不会主动删自己加的东西；放在两条规则之后，「The repository overrides」与「Always a judgement call」一并约束它。上游若加同类规则 → 收上游措辞，「写不出更短形态不算」保留 |
| 第 4 步 Standards subagent prompt 的 brief | `references/standards-reviewer.md` 第 4 节 | 要点全在。上游改 brief → 收上游 |
| 第 4 步 Spec subagent prompt 的 brief（Missing、Scope creep、Built wrong 三类，每条引 spec 原文） | `references/spec-reviewer.md` 第 3 节与末节 What is not yours | 三类保留，引用来源从「ticket 或 spec」扩到「ticket、spec 或 baseline」：baseline 既不是 ticket 也不是 spec，不扩这一句，第 2 节读出来的 baseline 偏离会被这一节自己的引用规则否掉。加了一条我们自己的禁令，首句把范围钉在 handoff package 这一件东西上——「The handoff package is the one baseline you do not open」：不读 handoff package（位置以 ticket 的 `## Read first` 为准），照不照它由某条 acceptance criterion 跑的 `story-parity.py` 判，是像素与 accessibility tree 比对，不是读出来的。范围不钉住，这段就是 Spec axis 关于 `## Read first` 收到的唯一一句话，读起来像整节都不许碰；钉住之后哪些 baseline 要读由第 2 节正面说，这里不再反过来补一遍。上游改 brief → 收上游，这条禁令与它的范围限定一并保留 |
| 第 4 步「把 smell baseline 全文粘进 subagent prompt」 | 退场 | 上游让 dispatcher 把 smell baseline 粘进 prompt。我们让轴 subagent 自己走技能的轴门、读 reference file：粘贴会产生第二份副本，与 reference file 里的那份各自漂移。`references/session.md` 第 2 节明写 prompt 只含技能名、ticket、base commit、axis 名 |
| 第 5 步 aggregate（两份 report 分列、不合并不重排、末尾一行汇总） | `references/session.md` 第 4 节 | 「不合并、不跨 axis 重排」原样保留。落点从「present 给 user」改成写到 ticket 上，成为一条 review comment，first line 固定 `REVIEW <base commit>..<HEAD commit>`：reviewer session 会结束，修它的 worker 读的是 ticket。写这条 comment 的是 `verify-ticket` 技能的 `--review`，不是 `gh issue comment`，理由见下面「报告和报信是同一次调用」。上游改这一步 → 收上游对 report 形状的措辞，落点与调用方式按我们的 |
| 「Why two axes」 | `references/session.md` 末尾的「Why three axes」 | 多一行 Tests axis 的对照 |
| 末节「What you do not do」的修法一句 | `references/session.md` 末节 | 改成「修法在 `implement`：in-ticket 修一轮，其余开 `finding` child」。上游写的是「three-round cap」，而 `implement` 的收尾不数轮次。上游改这句 → 收上游措辞，不带回任何轮次上限 |
| 无 | `references/session.md` 第 3 节（in-ticket / out-of-ticket 分类） | 我们加的。六条算 in-ticket：碰本 ticket 的 acceptance criteria、碰 ticket 点名的 spec 决策、碰 ticket `## Read first` 里的 baseline、碰 spec 的 `## Out of Scope`、碰 spec 的 `## Testing Decisions`、碰本 ticket `## Owns` 之内的文件；其余是 out-of-ticket。后两条是白天规划的一部分，落地内容要与白天规划一致：`## Out of Scope` 是白天写的「这次不做」，列在那里却做了是 Spec axis 最清楚的 `Scope creep`，归 out-of-ticket 就只开一张不阻塞的 sub-issue、越界代码随票合并；`## Testing Decisions` 定的是测试层与 precedent，偏离它的测试同样该当晚修。dispatcher 做这个分类而不是留给读者，因为两类的下一步不同——in-ticket 修一轮，out-of-ticket 由 worker 开成本票的 `finding` child（`--sub-issue finding`，mmw #315 第 3 节前叫 `review`）且不阻塞，不按属于谁分流；worker 开、reviewer 列。上游重写 §3 → 本票 parent 与 `--sub-issue finding` 保留，第六条与「`## Owns` 之外仍然不许改」按文末那一节取舍。baseline、`## Out of Scope`、`## Testing Decisions` 三条与 `references/spec-reviewer.md` 第 2 节让 Spec axis 读它们是一对，拆开做无效：dispatcher 按这一句的字面条件路由，只加读不改这里，baseline 偏离会被判成 out-of-ticket、开一个不阻塞的 sub-issue，本 ticket 照样关掉。怎么修不在这里，在 `implement` 的 closing steps：in-ticket 修一轮，out-of-ticket 开 sub-issue，轮次不设上限 |
| 无 | `references/spec-reviewer.md` 第 2 节读 `DECISIONS` 的那一句、第 3 节的 `Decisions` 一条、第 4 节的分组；`references/session.md` 第 3 节 `should not` 归 in-ticket 的那一段 | 我们加的：Spec axis 读票上最新的 `DECISIONS` 评论（worker 在派 reviewer 之前留的，两节：`Decisions I made on my own` 与 `Outside Owns`），对每一条给一句判断——`reasonable`（票或 spec 没写全、这是它们最可能要的补救）或 `should not`（违背票、点名 spec 小节、`## Out of Scope` 或 baseline 的某一行，引原文）；`should not` 是三类之一的 review finding，dispatcher 归 in-ticket，worker 走已有的修一轮。理由：这两类东西不一定是错，常常正说明票写得不全，该由 reviewer 判，不合理的当晚修掉而不是早上才有人看。上游若给 Spec axis 加同类判断 → 收上游措辞，读 `DECISIONS` 与 `should not` 归 in-ticket 保留 |
| 无 | `references/spec-reviewer.md` 末节「The screen contract you do open」之后的两段：「The contract's screen axis you open too」与「The story adapter you open too」；`references/tests-reviewer.md` 范围段之后确认 `boundary-check.py` 的一条 | 我们加的：Spec axis 仍审画面轴，并核对 story adapter 与合同 `shows` 的字段对应；Tests axis 确认边界测试经 `boundary-check.py`，不自判能否变红。来自 mmw #115 与 #216 第 8 节。上游改这两处 → 收上游措辞，画面轴 / adapter / boundary-check 三条保留 |
| 无 | `references/tests-reviewer.md` 整个文件 | 我们加的第三个 axis，见下一节 |
| 第 6 行 dispatcher 段与第 2 节标题、首段 | `SKILL.md` 的两扇门与 `references/session.md` 第 2 节 | 我们改的：会话自称 `reviewer session`，三个轴是 host 自带的通用 subagent，再调一次本技能并带上 axis 名（`Standards` / `Spec` / `Tests`），不写 model、不写路径。第 8 行原有 `When either is missing, ask for it.` 删去：`dispatch.sh` 起 reviewer 时两个值必带，而 reviewer 与等它的 worker 之间只有票上 `^REVIEW ` 一条通道，问不到人，屏幕上一张 form 只会被 board 关掉。上游改这两处 → 收上游措辞，通用 subagent、再调本技能、不问值这三条保留 |
| frontmatter 的 `description` | `SKILL.md` 第 3 行，改写了 | 收窄成两扇门：一张 ticket、一个 base commit、三个 axis；轴 subagent 再给一个 axis 名。末句给的是这个技能要的值，不写调用形状（理由见末节）。上游那句招揽「review a branch / a PR / review since X」的用法在正文里没有落点。上游改这一行 → 收上游对三个 axis 的措辞，两扇门与 ticket number 保留 |
| 第 1 步「say which one it was and stop」 | `references/session.md` 第 1 节，改写了 | base commit 解析不了或 diff 为空时，也要写到 ticket 上，走第 4 节同一条通道，first line 仍是 `REVIEW <base commit>..<HEAD commit>`，正文一行说是哪一种失败。理由是同一份文件末尾自己写的原则（只存在于 session 里的 report 谁也读不到），而 worker 在票上只找 first line `^REVIEW `：不写 ticket，它什么也找不到。两条失败路径与成功路径同一条通道，所以「报告落地」与「告诉 worker」在这三种结局下都不会各走各的。上游改这一步 → 收上游的判断，写到 ticket 上与走同一条通道这两条保留 |
| 无 | `references/session.md` 第 2 节末尾一段 | 我们加的：要求 dispatcher 在三个 axis subagent 都回话之前不结束回合，并对「subagent 默认后台跑」的 host 明写要等。措辞按能力说，不点 host 名。理由是第 4 节那一次调用——它贴出报告并在同一次调用里报信，那是叫醒 worker 的唯一一条路；中途结束回合时报告还没写出来，那一次调用也就还没发生，等它的 worker 只剩下反复问。上游若写明并行 subagent 的等待语义 → 收上游措辞，「不在中途结束回合」保留，理由不要写成「session 停下来本身会叫醒 worker」——那不是真的 |
| 第 2 步 subagent 表里的 reference 路径 | `SKILL.md` 的轴门与 `references/session.md` 第 2 节 | 不再把绝对路径交给 subagent。prompt 是一句 `Use the code-review skill … axis <Name>`，轴门用相对链接指向三份 reference。上游改这张表 → 收上游的行，不写路径、再调本技能按我们的 |
| 第 3 步 identify the standards sources 的来源清单 | `references/standards-reviewer.md` 第 2 节，加了一条 | 加 `codebase-design` 技能的 `SKILL.md`（按技能名点名，不写安装路径，subagent 从自己 host 装技能的位置解析）：`to-tickets` 把「接口是不是 pass-through」这类判断路由到 Standards axis，路由的终点得存在，而 depth / seam / adapter 这套 vocabulary 只在那个技能里。上游把这套 vocabulary 接进来 → 收上游措辞 |
| 无 | `references/standards-reviewer.md` 第 3 节末尾的 deletion test，与第 4 节的对应一行 | 我们加的：判 depth 的那一条，措辞照抄 `codebase-design/SKILL.md` 的 deletion test（删掉这个模块，复杂度是消失还是在 N 个调用方那里重新出现）。与 code smell 同级，是 judgement call，「The repository overrides」同样管它 |
| 每个 axis brief 末尾的字数上限 | 三份 reference file 各自的 report 段 | 我们改的：report 的长度由 finding 数决定——每条 finding 一项、带引用行，不是 finding 的不写；不设字数上限。上游改 report 格式 → 收上游格式，字数上限不收 |
| 无 | `references/tests-reviewer.md` 顶部一行，`tdd/tests.md` 与 `tdd/mocking.md` 顶部各一行 | 我们加的互指行：三份文件互相点名对方（技能名加文件名，不写安装路径）、要求同改。这份重复本身是有意的（subagent 只读自己那一份 reference file，跳转会失效），对齐义务写在三份文件顶部而不是只写在这份 merge-note 里，因为没人读 merge-note 去改 `tdd/`。上游给 `tdd/` 那两份加内容 → 收上游，同时对着 `references/tests-reviewer.md` 第 2 节改一遍 |

## 第三个 axis：Tests

上游只有两个 axis，都不看测试内容。这条 landing pipeline 里，测试是 worker 自己写的，`CHECK:` 跑的是 worker 自己写的用例，verifier 重跑的是同一条命令——一个期望值按被测代码同样算法重算一遍的用例，从写到关 ticket 没有任何一步会怀疑它。Tests axis 是唯一问「这个绿色证明了什么」的读者。

它照的规则不是自造的，抄 `mmw-v2/upstream/skills/engineering/tdd/tests.md` 与 `tdd/mocking.md`：tautological、implementation-coupled 六条 red flags、绕过接口验证、测试名说 how 不说 what、mock 越过系统边界。**那两份文件与 `references/tests-reviewer.md` 第 2 节的 test smell baseline 是同一批规则的两个副本：改 `tdd/tests.md` 或 `tdd/mocking.md` 时对着 `references/tests-reviewer.md` 第 2 节看一遍，反过来也一样。** 第六条「只测了 happy path」是这里独有的，`tdd` 那边没有。

两条禁令写在文件末尾，都有出处：不报 coverage（`tdd/SKILL.md` 的「Test only at pre-agreed seams」——这条 landing pipeline 故意不追 coverage），不追加 ticket 上没有的 acceptance criterion（一个 axis 自设通过标准，正是 `## Acceptance criteria` 这一节存在要防的事）。

审哪些测试文件不由 dispatcher 告诉它：subagent 自己 `gh issue view`，从每条 `CHECK:` 里点名的测试文件与用例名取出清单，清单之外的测试文件仍可报但归 out-of-ticket。

## 报告和报信是同一次调用

`references/session.md` 第 1 节与第 4 节都不用 `gh issue comment`，改用 `verify-ticket` 技能的
`<engine> <ticket> --review <file>`：它贴出评论，并在同一次调用里告诉起这个 reviewer 的
session 报告已经落地。记号与另外三个调用方一致，都写 `<engine>`、都说从 `verify-ticket` 技能自己的
`SKILL.md` 解析它。这一条 run 的行为与它的 exit code 写在那份技能的 `references/reporting.md`；
`session.md` 留下的是固定首行 `REVIEW <base commit>..<HEAD commit>` 与它的理由，那是调用方要照着写的政策。

这是本仓 `docs/adr/0010-agents-are-woken-not-polled.md` 已经为 worker 定下的那条规矩，reviewer
同样适用：状态落地和「告诉需要知道的人」拆成两步就会漏。漏的方式是具体的——Paseo 一个 session 只有
一次终结通知，花在它第一次结束回合的时刻，而 dispatcher 是否在派完 subagent 之后结束回合由模型临场
决定；花错了就没有第二次，worker 只能反复问。

`--review` 无条件报信：没有守卫去问跑它的 session 是不是 Paseo 起的那个 reviewer，也没有「reviewer 没留下
报告时 worker 自己起 subagent 重跑一份评审」那条兜底。reviewer 停了没留评论就是 `wait` 退 1，此外什么都不补。

上游把落点写成别的命令 → 收上游对 report 形状的措辞，调用改回 `--review`。

## 下次拉上游怎么合

上游有 `SKILL.md` 与 `agents/openai.yaml` 两个文件，我们有六个，冲突落在这两个上。

1. 拿到冲突后，先看上游改的是哪一步，对着上表第一列找到它现在住在哪里。落在某个 axis 的 reference file 里的，把改动搬进那个文件；落在 dispatcher 步骤里的，改 `references/session.md`；落在门口分门上的，改 `SKILL.md`。
2. 上游给 `SKILL.md` 加了新的一步：它是 dispatcher 的动作就进 `references/session.md`，是某一个 axis 要照的规则就进那个 axis 的 reference file。
3. 上游加了第三个 axis：与我们的 Tests axis 合并还是并列，看它问的是不是同一个问题；并列的话 `SKILL.md` 的轴门和 `references/session.md` 第 2 节都要加一行。
4. `SKILL.md` 只做分门，不含 smell baseline 正文与任何 subagent brief 原文。收上游时这些进了门口，就是有 axis 要照的规则没搬进 reference file。
5. frontmatter 的 `description` 不带引号（值里没有冒号加空格）。Markdown 文件一律英文，不写出处、不写落地记录。`references/` 下 axis 各一份，dispatcher 的步骤在 `references/session.md`，门口在 `SKILL.md`。

## What the caller gives, not what the call looks like

`description` names the values this skill needs — a base commit and a ticket number for
the session, plus an axis name for an axis subagent — rather than an argument order.
`dispatch.sh` sends a sentence naming the skill, so any wording that carries both values
is a correct call, and a fixed shape written here would describe something that does not
happen. Upstream writes an `Invoked as …` line → replace it with the values again.

`references/` is reached by relative link, the way every other skill in MMW reaches its own
files. The axis subagent is told to use this skill and which axis; it is not handed a path.

## The Spec axis opens the screen contract

`references/spec-reviewer.md`, under "What is not yours": one paragraph added after the handoff-package rule. The handoff package stays closed to this axis; the screen contract (`screen-contract.yaml`, row ids named in the ticket's `## Read first`) is opened, and each row is read as a requirement — `calls`, `shows`, `next`, `on_failure`. A `Missing` against a row's `calls` is worded row id first, because `verify-ticket --closeout` refuses a draft that does not answer it. Reason: on Chameleon's #549 this axis reported "the desktop never talks to the backend" and the ticket closed `ALL MET` anyway; the row id is what lets a script hold the two together. If upstream rewrites that section, keep the handoff-package rule as the Spec-brief table row words it, and put this paragraph back after it.

## The Spec axis opens the story page and the story adapter

`references/spec-reviewer.md`, same section, two more paragraphs after the screen-contract
one. **The story page**: every mount the ticket's story criterion names under `--pages` is
declared by the contract's `pages`, and the diff puts `[data-story-root]` on the root of
that design page's block. **The story adapter**: every field a row's `shows` column names
appears in the product's adapter from `scenes.json` to the surface component's props,
pointing at the same source field. Reason: `story-parity.py` compares a rendered story
against the design page offline, so a mount the contract does not declare and an adapter
reading the wrong field both come back as a pixel or tree difference with no name on it;
this axis is where they get one. Neither paragraph mentions `--mount`, the contract's
`open` chain, the addressing self-check or interface parity — those are retired words
(`docs/adr/0011-component-story-not-whole-product.md`), and an axis file that names them
sends every later review down a path the tools no longer have. If upstream rewrites that
section, put both paragraphs back after the screen-contract one.

## A file inside Owns is in-ticket

`references/session.md` section 3 gained a sixth in-ticket condition, isomorphic with the five: the file the review finding points at sits inside this ticket's `## Owns`. The sentence that in-ticket review findings get one round of fixes on this ticket is unchanged — the sixth condition uses that round. The condition does not widen where the worker may write: a file outside `## Owns` is still not written.

Reason, in the numbers from #277 Problem Statement: on the #216 night, 38 review sub-issues; 27 of them (71%) had a fix target that sat entirely inside that ticket's own `## Owns`, and the worker was forbidden to touch them.

If upstream rewrites section 3 → take its wording and put the sixth condition back, with the sentence that a file outside `## Owns` is still not written.

## The Spec axis reviews tickets integrated into the base branch

`references/spec-reviewer.md` reads the first `worker.started.base`, then the first-parent
`Merge branch 'issue-<n>'` commits through the base commit. It reads each ticket those
commits name and its closeout evidence and checks four interactions: combination behavior,
contract consistency, migration completeness and shared state. Another ticket's verdict
is evidence of what ran, not proof that the combination is correct.

`references/session.md` keeps the ownership boundary when it sorts those findings: a
repair inside the current ticket's `## Owns` is in-ticket; one only inside another ticket's
`## Owns` is out-of-ticket and becomes a `finding` child. Upstream rewrites the Spec axis
or the sorting step → keep both the four-angle pass and this ownership rule.

### docs page

`mmw-v2/upstream/docs/engineering/code-review.md` describes the same first-parent range, four interaction angles and ownership boundary without introducing other names for the base commit or `origin/<base branch>`.

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改成「一张 ticket 的 diff」加三个 axis，与 `SKILL.md` 的 `description` 同一个形态。上游改这一行 → 收上游措辞，axis 数与 ticket 按我们的 |

## A host that cannot run subagents

`references/session.md` section 2 gained the capability branch, in the form `manage-agents-md/references/survey.md` § Dispatch already uses: a host that can run subagents starts three at once; one that cannot runs the three axis files itself, one after another, writing each axis report to a file before opening the next, so no report depends on memory of the previous one. The opening paragraph states the same branch. The section heading is `Run the three axes`. The launch and prompt sentences are marked as the can-run path. Hold-the-turn waits until all three axis reports exist. The axis file's read-only rule binds the axis pass; step 4 still writes the review comment. Reason: a reviewer session on a host without subagents had no path (spec #374 Implementation Decisions section 3). If upstream rewrites section 2 → take its wording and put the capability branch back.
