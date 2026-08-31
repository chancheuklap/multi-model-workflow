# code-review

源目录：`mmw-v2/upstream/skills/engineering/code-review/`

上游是一个文件：`SKILL.md` 里五步走完，两个轴的 brief 与 Fowler 十二条坏味道全文都排在步骤中间。我们把三个轴的 sub-agent 的判据各拆一份出去，派发者的正文留在 `SKILL.md`，并加了第三个轴。

拆的判据是读者：三个 reference 各只被一个子代理读，派发者一次也读不到；`SKILL.md` 从头到尾只有派发者一个读者，而且它每次都要读全，所以不再往外拆——拆出去只多一次跳转。

## 哪一段挪去了哪个文件

| 上游 `SKILL.md` 的段落 | 落到 | 我们的意图 |
| --- | --- | --- |
| 第 1 步 pin the fixed point（三条 git 命令、三点 diff、空 diff 要在派子代理之前失败） | `SKILL.md` 第 1 节 | 原文的判断一条没改。上游改这三条命令 → 收上游 |
| 第 2 步 identify the spec source（四级查找顺序：commit message 里的票号 → 用户给的路径 → `docs/` `specs/` `.scratch/` 下按分支名找 → 问用户） | `references/spec-reviewer.md` 第 2 节，且换掉了 | 这条流水线的票一定有 `## Parent`，四级查找的后三级是给没有票的场景用的。改成沿 `## Parent` 读 spec 指名的小节 + `## Testing Decisions` + `## Out of Scope`，读法与 `implement` 的读法收窄同一套。清单后来从三条加到四条，第四条是票 `## Read first` 里标为基线的条目，逐份读到结论；标题跟着改成「读票和它指向的东西」，因为原标题把范围框死在 spec。理由：Spec 轴问的就是「有没有做票和 spec 要的那件事」，`## Read first` 就在它已经读全的那张票里，而在此之前全流水线没有任何一个角色被要求核对基线有没有被默默偏离；基线要是挂在清单外面会读成可选项。上游那个数字（读「恰好三样」）换成「读它指向的东西，别的都不读」：清单本身就是穷举，数字每加一条要改一次，改漏了正文就自相矛盾。清单后面那句「基线记录的是已拍板的结论，所以 diff 对它负责的方式与对 spec 小节一样」是这条指令的意义，不删——少了它，子代理只知道要读，不知道读出来的分量。上游改这一步 → 不收，除非它也变成从票走 |
| 第 3 步 identify the standards sources（仓库里哪些文件算编码规范）+ smell baseline 全文十二条 + 「repo overrides」与「always a judgement call」两条规则 | `references/standards-reviewer.md` 第 2、3 节 | 十二条逐条原文保留，措辞改成对子代理说的第二人称。上游增删坏味道 → 收上游，改这个文件 |
| 无 | `references/standards-reviewer.md` 第 3 节两条规则之后的一段，与第 1 句的第二个问题 | 我们加的：每个 hunk 问一次「删掉、并进已有分支、换成仓库已有 helper，验收标准是否仍过」，写得出更短形态才算 finding。理由：reviewer 是唯一没写这段代码的读者，作者不会主动删自己加的东西；放在两条规则之后，「repo overrides」与「always a judgement call」一并约束它。上游若加同类判据 → 收上游措辞，「写不出更短形态不算」保留 |
| 第 4 步 Standards sub-agent prompt 的 brief | `references/standards-reviewer.md` 第 4 节 | 要点全在。上游改 brief → 收上游 |
| 第 4 步 Spec sub-agent prompt 的 brief（缺项、scope creep、实现得不对三类，每条引 spec 原文） | `references/spec-reviewer.md` 第 3 节 | 三类保留，引用来源从「票或 spec」扩到「票、spec 或基线」：基线既不是票也不是 spec，不扩这一句，第 2 节读出来的基线偏离会被这一节自己的引用规则否掉。加了一条我们自己的禁令，范围写死在交接包这一件东西上：不读交接包（`prototypes/<task>/<issue>/UI/`），照不照它由某条验收标准跑的 `visual-parity` 判，是像素与 ARIA 比对，不是读出来的；这条禁令的首句从「交接包不归你管」改成「交接包是那一节里唯一一件你不打开的基线」，范围钉在交接包这一件东西上。不钉，这段就是 Spec 轴关于 `## Read first` 收到的唯一一句话，读起来像整节都不许碰；钉住之后哪些基线要读由第 2 节正面说，这里不再反过来补一遍。上游改 brief → 收上游，这条禁令与它的范围限定一并保留 |
| 第 4 步「把 baseline 全文粘进子代理 prompt」 | 退场 | 上游让派发者把 smell baseline 粘进 prompt。我们让子代理自己读 reference 文件：粘贴会产生第二份副本，与 reference 里的那份各自漂移。`SKILL.md` 第 2 节明写 prompt 只含起点 commit、票号、reference 路径三个值 |
| 第 5 步 aggregate（两份报告分列、不合并不重排、末尾一行汇总） | `SKILL.md` 第 4 节 | 「不合并、不跨轴重排」原样保留。落点从「present 给用户」改成 `gh issue comment` 写到票上，首行固定 `REVIEW <base commit>..<HEAD commit>`：reviewer 的会话会结束，修它的 worker 读的是票 |
| 「Why two axes」 | `SKILL.md` 末尾，改成「Why three axes」 | 多一行 Tests 轴的对照 |
| 无 | `SKILL.md` 第 3 节（票内 / 票外分类） | 我们加的。三条算票内：碰本票验收标准、碰票指名的 spec 决策、碰票 `## Read first` 里的基线；其余是票外。派发者做这个分类而不是留给读者，因为两类的下一步不同——票内修一轮，票外开 sub-issue 且不阻塞。基线那一条与 `references/spec-reviewer.md` 第 2 节让 Spec 轴读基线是一对，拆开做无效：派发者按这一句的字面条件路由，只加读不改这里，基线偏离会被判成票外、开一个不阻塞的 sub-issue，本票照样关掉。轮数上限与怎么修不在这里，在 `implement` 的收尾段 |
| 无 | `references/tests-reviewer.md` 整个文件 | 我们加的第三个轴，见下一节 |
| frontmatter 的 `description` | `SKILL.md` 第 3 行，改写了 | 收窄成派发形态：一张票、一个起点 commit、三个轴、报告写到票上，并写出 `code-review <base-commit> #<ticket>`。上游那句招揽「review a branch / a PR / review since X」的用法在正文里没有落点——第 8 行就要票号，第 4 节只往 `gh issue comment <ticket>` 写。上游改这一行 → 收上游对三个轴的措辞，派发形态与票号保留 |
| 第 1 步「say which one it was and stop」 | `SKILL.md` 第 1 节，改写了 | 起点 commit 解析不了或 diff 为空时，也要 `gh issue comment` 到票上，首行仍是 `REVIEW <base commit>..<HEAD commit>`，正文一行说是哪一种失败。理由是同一份文件末尾自己写的原则（只存在于会话里的报告谁也读不到），而 worker 的 `dispatch.sh wait` 只认首行 `^REVIEW `，不写票就是 30 分钟静默超时。上游改这一步 → 收上游的判断，写到票上这条保留 |
| 第 2 步子代理表里的 reference 路径 | `SKILL.md` 第 2 节 | 表里写安装后的绝对路径 `~/.agents/skills/code-review/references/<轴>.md`，相对链接留在括号里。子代理拿到的 prompt 只有三个值，它没有「相对于哪个文件」这个上下文。上游改这张表 → 收上游的行，路径写法按我们的 |
| 第 3 步 identify the standards sources 的来源清单 | `references/standards-reviewer.md` 第 2 节，加了一条 | 加 `~/.agents/skills/codebase-design/SKILL.md`：`to-tickets` 把「接口是不是 pass-through」这类判断路由到 Standards 轴，路由的终点得存在，而 depth / seam / adapter 的词表只在那个技能里。上游把这份词表接进来 → 收上游措辞 |
| 无 | `references/standards-reviewer.md` 第 3 节末尾的 deletion test，与第 4 节的对应一行 | 我们加的：判 depth 的那一条，措辞照抄 `codebase-design/SKILL.md` 的 deletion test（删掉这个模块，复杂度是消失还是在 N 个调用方那里重新出现）。与坏味道同级，是判断题，「repo overrides」同样管它 |
| 无 | `references/tests-reviewer.md` 顶部一行，`tdd/tests.md` 与 `tdd/mocking.md` 顶部各一行 | 我们加的互指行：三份文件互相点名对方路径、要求同改。这份重复本身是有意的（子代理只读自己那一份 reference，跳转会失效），但对齐义务原先只写在这份 merge-note 里，没人读 merge-note 去改 `tdd/`。上游给 `tdd/` 那两份加内容 → 收上游，同时对着 `references/tests-reviewer.md` 第 2 节改一遍 |

## 第三个轴：Tests

上游只有两个轴，都不看测试内容。这条流水线里，测试是 worker 自己写的，`CHECK:` 跑的是 worker 自己写的用例，verifier 重跑的是同一条命令——一个期望值按被测代码同样算法重算一遍的用例，从写到关票没有任何一步会怀疑它。Tests 轴是唯一问「这个绿色证明了什么」的读者。

判据不是自造的，抄 `mmw-v2/upstream/skills/engineering/tdd/tests.md` 与 `tdd/mocking.md`：tautological、implementation-coupled 六条 red flags、绕过接口验证、测试名说 how 不说 what、mock 越过系统边界。**这两份文件是同一批判据的另一个副本：改 `tdd/tests.md` 或 `tdd/mocking.md` 时对着 `references/tests-reviewer.md` 第 2 节看一遍，反过来也一样。** 第六条「只测了 happy path」是这里独有的，`tdd` 那边没有。

两条禁令写在文件末尾，都有出处：不报覆盖率（`tdd/SKILL.md` 的「Test only at pre-agreed seams」——这条流水线故意不追覆盖率），不追加票上没有的测试标准（reviewer 自设通过标准，正是验收标准这一节存在要防的事）。

审哪些测试文件不由派发者告诉它：子代理自己 `gh issue view`，从每条 `CHECK:` 里点名的测试文件与用例名取出清单，清单之外的测试文件仍可报但归票外。

## 下次拉上游怎么合

上游有 `SKILL.md` 与 `agents/openai.yaml` 两个文件，我们有五个，冲突落在这两个上。

1. 拿到冲突后，先看上游改的是哪一步，对着上表第一列找到它现在住在哪里。落在某个 reviewer 的 reference 里的，把改动搬进那个文件；落在 `SKILL.md` 里的，就地改。
2. 上游给 `SKILL.md` 加了新的一步：它是派发者的动作就留在 `SKILL.md`，是某一个轴的判据就进那个轴的 reference。
3. 上游加了第三个轴：与我们的 Tests 轴合并还是并列，看它问的是不是同一个问题；并列的话 `SKILL.md` 第 2 节的子代理表要加一行。
4. `SKILL.md` 有硬上限：正文不超过 70 行非空行，且不含 smell baseline 正文与任何子代理 brief 原文。收上游时超了，就是有判据没搬进 reference。
5. 四个 Markdown 文件一律英文，不写出处、不写落地记录。`references/` 下只放轴的判据，一个轴一份：派发者的正文没有第二个读者，不单独成文件。

## What the caller gives, not what the call looks like

`description` and the line under it name the two values this skill needs — the commit the
diff starts from and the ticket number — rather than an argument order. `dispatch.sh` sends
a sentence naming the skill, so any wording that carries both values is a correct call, and
a fixed shape written here would describe something that does not happen. Upstream writes an
`Invoked as …` line → replace it with the two values again.

`references/` is reached by relative link, the way every other skill in this repository
reaches its own files. The absolute path stays in one place only: the sub-agent prompt in
§2, because a sub-agent's working directory is the repository, not the skill directory, so
the dispatcher has to resolve the link before it hands it over.

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改成「一张票的 diff」加三个轴，与 `SKILL.md` 的 `description` 同一个形态。上游改这一行 → 收上游措辞，轴数与票号按我们的 |
