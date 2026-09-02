# code-review

源目录：`mmw-v2/upstream/skills/engineering/code-review/`

上游是一个文件：`SKILL.md` 里五步走完，两个 axis 的 brief 与 smell baseline 全文（Fowler 十二条 code smell）都排在步骤中间。我们把三个 axis 的 subagent 要照的规则各拆一份 reference file 出去，dispatcher 的正文留在 `SKILL.md`，并加了第三个 axis。

拆的依据是读者：三份 reference file 各只被一个 subagent 读，dispatcher 一次也读不到；`SKILL.md` 从头到尾只有 dispatcher 一个读者，而且它每次都要读全，所以不再往外拆——拆出去只多一次跳转。

## 哪一段挪去了哪个文件

| 上游 `SKILL.md` 的段落 | 落到 | 我们的意图 |
| --- | --- | --- |
| 第 1 步 pin the fixed point（三条 git 命令、三点 diff、空 diff 要在派 subagent 之前失败） | `SKILL.md` 第 1 节 | 原文的判断一条没改。上游改这三条命令 → 收上游 |
| 第 2 步 identify the spec source（四级查找顺序：commit message 里的 ticket number → user 给的路径 → `docs/` `specs/` `.scratch/` 下按分支名找 → 问 user） | `references/spec-reviewer.md` 第 2 节，且换掉了 | 这条 landing pipeline 的 ticket 一定有 `## Parent`，四级查找的后三级是给没有 ticket 的场景用的。我们的读法是沿 `## Parent` 读 spec 点名的小节 + `## Testing Decisions` + `## Out of Scope`，加第四条 ticket `## Read first` 里标为 baseline 的条目，逐份读到结论；这套读法与 `implement` 的 narrowed reading 是同一套。节标题是「读 ticket 和它指向的东西」而不是只说 spec，因为范围不止 spec。理由：Spec axis 问的就是「有没有做 ticket 和 spec 要的那件事」，`## Read first` 就在它已经读全的那张 ticket 里，而 pipeline 里没有别的角色被要求核对 baseline 有没有被默默偏离；baseline 挂在清单外面会读成可选项。上游那句写了数（读「恰好三样」），我们的清单不写数，只说「读它指向的东西，别的都不读」：清单本身就是穷举，写了数每加一条要改一次，改漏了正文就自相矛盾。清单后面那句「baseline 记录的是已拍板的结论，所以 diff 对它负责的方式与对 spec 小节一样」是这条指令的意义，不删——少了它，subagent 只知道要读，不知道读出来的分量。上游改这一步 → 不收，除非它也变成从 ticket 走 |
| 第 3 步 identify the standards sources（repository 里哪些文件算编码规范）+ smell baseline 全文十二条 + 「The repository overrides」与「Always a judgement call」两条规则 | `references/standards-reviewer.md` 第 2、3 节 | 十二条逐条原文保留，措辞改成对 subagent 说的第二人称。上游增删 code smell → 收上游，改这个文件 |
| 无 | `references/standards-reviewer.md` 第 3 节两条规则之后的一段，与第 1 句的第二个问题 | 我们加的：每个 hunk 问一次「删掉、并进已有分支、换成 repository 已有 helper，acceptance criteria 是否仍过」，写得出更短形态才算 review finding。理由：Standards axis 是唯一没写这段代码的读者，作者不会主动删自己加的东西；放在两条规则之后，「The repository overrides」与「Always a judgement call」一并约束它。上游若加同类规则 → 收上游措辞，「写不出更短形态不算」保留 |
| 第 4 步 Standards subagent prompt 的 brief | `references/standards-reviewer.md` 第 4 节 | 要点全在。上游改 brief → 收上游 |
| 第 4 步 Spec subagent prompt 的 brief（Missing、Scope creep、Built wrong 三类，每条引 spec 原文） | `references/spec-reviewer.md` 第 3 节 | 三类保留，引用来源从「ticket 或 spec」扩到「ticket、spec 或 baseline」：baseline 既不是 ticket 也不是 spec，不扩这一句，第 2 节读出来的 baseline 偏离会被这一节自己的引用规则否掉。加了一条我们自己的禁令，首句把范围钉在 handoff package 这一件东西上——「The handoff package is the one baseline you do not open」：不读 handoff package（`prototypes/<task>/<issue>/UI/`），照不照它由某条 acceptance criterion 跑的 `visual-parity.py` 判，是像素与 accessibility tree 比对，不是读出来的。范围不钉住，这段就是 Spec axis 关于 `## Read first` 收到的唯一一句话，读起来像整节都不许碰；钉住之后哪些 baseline 要读由第 2 节正面说，这里不再反过来补一遍。上游改 brief → 收上游，这条禁令与它的范围限定一并保留 |
| 第 4 步「把 smell baseline 全文粘进 subagent prompt」 | 退场 | 上游让 dispatcher 把 smell baseline 粘进 prompt。我们让 subagent 自己读 reference file：粘贴会产生第二份副本，与 reference file 里的那份各自漂移。`SKILL.md` 第 2 节明写 prompt 只含 base commit、ticket number、reference file 路径三个值 |
| 第 5 步 aggregate（两份 report 分列、不合并不重排、末尾一行汇总） | `SKILL.md` 第 4 节 | 「不合并、不跨 axis 重排」原样保留。落点从「present 给 user」改成 `gh issue comment` 写到 ticket 上，成为一条 review comment，first line 固定 `REVIEW <base commit>..<HEAD commit>`：reviewer session 会结束，修它的 worker 读的是 ticket |
| 「Why two axes」 | `SKILL.md` 末尾的「Why three axes」 | 多一行 Tests axis 的对照 |
| 无 | `SKILL.md` 第 3 节（in-ticket / out-of-ticket 分类） | 我们加的。五条算 in-ticket：碰本 ticket 的 acceptance criteria、碰 ticket 点名的 spec 决策、碰 ticket `## Read first` 里的 baseline、碰 spec 的 `## Out of Scope`、碰 spec 的 `## Testing Decisions`；其余是 out-of-ticket。后两条是白天规划的一部分，落地内容要与白天规划一致：`## Out of Scope` 是白天写的「这次不做」，列在那里却做了是 Spec axis 最清楚的 `Scope creep`，归 out-of-ticket 就只开一张不阻塞的 sub-issue、越界代码随票合并；`## Testing Decisions` 定的是测试层与 precedent，偏离它的测试同样该当晚修。dispatcher 做这个分类而不是留给读者，因为两类的下一步不同——in-ticket 修一轮，out-of-ticket 开 sub-issue 且不阻塞。baseline、`## Out of Scope`、`## Testing Decisions` 三条与 `references/spec-reviewer.md` 第 2 节让 Spec axis 读它们是一对，拆开做无效：dispatcher 按这一句的字面条件路由，只加读不改这里，baseline 偏离会被判成 out-of-ticket、开一个不阻塞的 sub-issue，本 ticket 照样关掉。three-round cap 与怎么修不在这里，在 `implement` 的 closing steps |
| 无 | `references/spec-reviewer.md` 第 2 节读 `DECISIONS` 的那一句、第 3 节的 `Decisions` 一条、第 4 节的分组；`SKILL.md` 第 3 节 `should not` 归 in-ticket 的那一段 | 我们加的：Spec axis 读票上最新的 `DECISIONS` 评论（worker 在派 reviewer 之前留的，两节：`Decisions I made on my own` 与 `Outside Owns`），对每一条给一句判断——`reasonable`（票或 spec 没写全、这是它们最可能要的补救）或 `should not`（违背票、点名 spec 小节、`## Out of Scope` 或 baseline 的某一行，引原文）；`should not` 是三类之一的 review finding，dispatcher 归 in-ticket，worker 走已有的修一轮。理由：这两类东西不一定是错，常常正说明票写得不全，该由 reviewer 判，不合理的当晚修掉而不是早上才有人看。上游若给 Spec axis 加同类判断 → 收上游措辞，读 `DECISIONS` 与 `should not` 归 in-ticket 保留 |
| 无 | `references/tests-reviewer.md` 整个文件 | 我们加的第三个 axis，见下一节 |
| 第 6 行 dispatcher 段与第 2 节标题、首段 | `SKILL.md` 第 6 行与第 2 节 | 我们改的：会话自称 `reviewer session`，三个轴 subagent 是本 toolbox 装到各 host 的 `reviewer` subagent（`mmw-v2/agents/reviewer/`），model 与 effort 来自 `models.md` 的 reviewer 行，调用时不写 model——四个 agent 同一行配置。第 8 行原有 `When either is missing, ask for it.` 删去：`dispatch.sh` 起 reviewer 时两个值必带，而 reviewer 与等它的 worker 之间只有票上 `^REVIEW ` 一条通道，问不到人，屏幕上一张 form 只会被 board 关掉。上游改这两处 → 收上游措辞，`reviewer` subagent 与不问值这两条保留 |
| frontmatter 的 `description` | `SKILL.md` 第 3 行，改写了 | 收窄成 dispatcher 形态：一张 ticket、一个 base commit、三个 axis、axis report 作一条 review comment 写到 ticket 上；末句给的是这个技能要的两个值（base commit 与 ticket number），不写调用形状（理由见末节）。上游那句招揽「review a branch / a PR / review since X」的用法在正文里没有落点——第 8 行就要 ticket number，第 4 节只往 `gh issue comment <ticket>` 写。上游改这一行 → 收上游对三个 axis 的措辞，dispatcher 形态与 ticket number 保留 |
| 第 1 步「say which one it was and stop」 | `SKILL.md` 第 1 节，改写了 | base commit 解析不了或 diff 为空时，也要 `gh issue comment` 到 ticket 上，first line 仍是 `REVIEW <base commit>..<HEAD commit>`，正文一行说是哪一种失败。理由是同一份文件末尾自己写的原则（只存在于 session 里的 report 谁也读不到），而 worker 的 `dispatch.sh wait` 只认 first line `^REVIEW `，不写 ticket 就是 30 分钟静默超时。上游改这一步 → 收上游的判断，写到 ticket 上这条保留 |
| 第 2 步 subagent 表里的 reference 路径 | `SKILL.md` 第 2 节 | 表两列 `Axis` 与 `Reference file`，路径写相对链接；绝对路径只出现在同一节 prompt 的第三个值里（理由见末节）。上游改这张表 → 收上游的行，两列与路径写法按我们的 |
| 第 3 步 identify the standards sources 的来源清单 | `references/standards-reviewer.md` 第 2 节，加了一条 | 加 `~/.agents/skills/codebase-design/SKILL.md`：`to-tickets` 把「接口是不是 pass-through」这类判断路由到 Standards axis，路由的终点得存在，而 depth / seam / adapter 这套 vocabulary 只在那个技能里。上游把这套 vocabulary 接进来 → 收上游措辞 |
| 无 | `references/standards-reviewer.md` 第 3 节末尾的 deletion test，与第 4 节的对应一行 | 我们加的：判 depth 的那一条，措辞照抄 `codebase-design/SKILL.md` 的 deletion test（删掉这个模块，复杂度是消失还是在 N 个调用方那里重新出现）。与 code smell 同级，是 judgement call，「The repository overrides」同样管它 |
| 无 | `references/tests-reviewer.md` 顶部一行，`tdd/tests.md` 与 `tdd/mocking.md` 顶部各一行 | 我们加的互指行：三份文件互相点名对方路径、要求同改。这份重复本身是有意的（subagent 只读自己那一份 reference file，跳转会失效），对齐义务写在三份文件顶部而不是只写在这份 merge-note 里，因为没人读 merge-note 去改 `tdd/`。上游给 `tdd/` 那两份加内容 → 收上游，同时对着 `references/tests-reviewer.md` 第 2 节改一遍 |

## 第三个 axis：Tests

上游只有两个 axis，都不看测试内容。这条 landing pipeline 里，测试是 worker 自己写的，`CHECK:` 跑的是 worker 自己写的用例，verifier 重跑的是同一条命令——一个期望值按被测代码同样算法重算一遍的用例，从写到关 ticket 没有任何一步会怀疑它。Tests axis 是唯一问「这个绿色证明了什么」的读者。

它照的规则不是自造的，抄 `mmw-v2/upstream/skills/engineering/tdd/tests.md` 与 `tdd/mocking.md`：tautological、implementation-coupled 六条 red flags、绕过接口验证、测试名说 how 不说 what、mock 越过系统边界。**那两份文件与 `references/tests-reviewer.md` 第 2 节的 test smell baseline 是同一批规则的两个副本：改 `tdd/tests.md` 或 `tdd/mocking.md` 时对着 `references/tests-reviewer.md` 第 2 节看一遍，反过来也一样。** 第六条「只测了 happy path」是这里独有的，`tdd` 那边没有。

两条禁令写在文件末尾，都有出处：不报 coverage（`tdd/SKILL.md` 的「Test only at pre-agreed seams」——这条 landing pipeline 故意不追 coverage），不追加 ticket 上没有的 acceptance criterion（一个 axis 自设通过标准，正是 `## Acceptance criteria` 这一节存在要防的事）。

审哪些测试文件不由 dispatcher 告诉它：subagent 自己 `gh issue view`，从每条 `CHECK:` 里点名的测试文件与用例名取出清单，清单之外的测试文件仍可报但归 out-of-ticket。

## 下次拉上游怎么合

上游有 `SKILL.md` 与 `agents/openai.yaml` 两个文件，我们有五个，冲突落在这两个上。

1. 拿到冲突后，先看上游改的是哪一步，对着上表第一列找到它现在住在哪里。落在某个 axis 的 reference file 里的，把改动搬进那个文件；落在 `SKILL.md` 里的，就地改。
2. 上游给 `SKILL.md` 加了新的一步：它是 dispatcher 的动作就留在 `SKILL.md`，是某一个 axis 要照的规则就进那个 axis 的 reference file。
3. 上游加了第三个 axis：与我们的 Tests axis 合并还是并列，看它问的是不是同一个问题；并列的话 `SKILL.md` 第 2 节的表要加一行。
4. `SKILL.md` 有硬上限：正文不超过 70 行非空行，且不含 smell baseline 正文与任何 subagent brief 原文。收上游时超了，就是有 axis 要照的规则没搬进 reference file。
5. 四个 Markdown 文件一律英文，不写出处、不写落地记录。`references/` 下只放 axis 要照的规则，一个 axis 一份：dispatcher 的正文没有第二个读者，不单独成文件。

## What the caller gives, not what the call looks like

`description` and the line under it name the two values this skill needs — the base commit the
diff starts from and the ticket number — rather than an argument order. `dispatch.sh` sends
a sentence naming the skill, so any wording that carries both values is a correct call, and
a fixed shape written here would describe something that does not happen. Upstream writes an
`Invoked as …` line → replace it with the two values again.

`references/` is reached by relative link, the way every other skill in MMW reaches its own
files. The absolute path stays in one place only: the subagent prompt in §2, because a
subagent's working directory is the repository, not the skill directory, so the dispatcher
has to resolve the link before it hands it over.

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改成「一张 ticket 的 diff」加三个 axis，与 `SKILL.md` 的 `description` 同一个形态。上游改这一行 → 收上游措辞，axis 数与 ticket 按我们的 |
