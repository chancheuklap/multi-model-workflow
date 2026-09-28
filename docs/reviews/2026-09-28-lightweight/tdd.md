# tdd

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：`tdd` 的上游正文说理充分："Tests verify behavior through public interfaces… Code can change entirely; tests shouldn't"、三种反模式各自的 "The tell"，都是改变判断的句子，一字不动。要补的两处：
- 流水线里没有任何一步去证明"这条测试真能失败"。这一句放进 `implement`，不改上游，因为上游在文档里写明有意不加强这一点。
- 本仓改写的"重构不在循环里"这一条，只说归属不说理由，还和 `implement` 的"删掉变多余的分支"字面冲突。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | **放在 `implement` 的 `SKILL.md`**，"Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams." 之后（`implement` 定稿同步加这一条） | Where an acceptance criterion's `CHECK:` names a test case, that case is your first red test: run it before writing the code it covers and read why it fails. Red that comes from a missing file, an import error or a typo in the case name proves nothing; the test counts as red only when it fails because the behaviour is absent. No later step does this for you: the claim-time baseline ran before the test existed, and the review reads tests without running them. | worker 一次写好测试和实现、直接跑成绿，以为 red→green 已经做过了。末句说明为什么只能由它来做：认领时的基线跑在测试存在之前，Tests axis 只读不跑（`tests-reviewer.md` "run no test"）。证据：Nowledge Mem `02fc9cc5`（2026-09-09）记下四种反复出现的假绿，每一种都是故意把被测物改坏才抓出来的。顺带的好处：用例名和 `CHECK:` 对不上时当场暴露。 |
| I2 | `tdd` `## Rules of the loop` 的 "**Refactoring is not part of the loop.** …" 整条替换（本仓已改过的一条） | **Refactoring is not part of the loop.** Green means the slice is done; restructuring is a separate pass over the finished change, where it is judged with fresh eyes instead of skipped under the next red. Working from a ticket, that pass is the round of fixes that follows its review; with no ticket, it is a deliberate pass once every slice is green. Keeping the change itself correct (a caller of what you changed, a branch your change made dead) is part of the slice, not refactoring. | 原文只说重构归哪里。不带票单独使用时，它指向一个不存在的修复轮，于是结构永远不整理；带票时，worker 可能把 `implement` 要求的"删掉被本次改动变多余的分支"也当成重构推迟。改后给出理由和两种情况的去处，并化解这处字面冲突。仍然"不点 stage 的名、归 review 之后的修复轮"，merge-note 的意图不变，第 13 行条目同步改写。 |

### 删除

- 调查员 A1（该条后半句复述 `implement` 第 3 步）由 I2 整条替换吸收。

### 不采纳

- 把 I1 的意思写进 `tdd` 上游正文：上游在 `docs/engineering/tdd.md` 明写有意不加强（"forcing the point harder restricts the agent's creativity for little gain"）。在调用方 `implement` 那一行接上，就能覆盖流水线里的全部使用。

## 结论

`mmw-v2/upstream/skills/engineering/tdd/` 是一份没有脚本的上游参考型技能：`SKILL.md` 正文 576 词（上游原版 534 词，本仓净加 42 词），`tests.md` 291 词、`mocking.md` 202 词，两份 reference 与上游逐字相同。本仓只改了 `SKILL.md` 的三处（`**Test only at pre-agreed seams.**` 一段、`codebase-design` 指向句、`**Refactoring is not part of the loop.**` 一条），三处在 `mmw-v2/merge-notes/tdd.md` 各有条目，条目与现文一致。没有过度设计、没有过度防御、没有历史碎碎念；可删的只有 `**Refactoring is not part of the loop.**` 后半句约 15 词，它复述 `implement` 第 3 步。"灵魂"基本完整：好测试为什么经得起重构、为什么只在约定的 seam 上测、为什么不能横向切片、预期值为什么要有独立来源，这几段都在，都该保留。真正的缺口有两处，都和 MMW 的流水线怎么判定测试有关：一是没有一处要求"先看着新测试失败、且失败原因是你预期的那个"，而流水线里没有任何脚本或审查轴补这一步（有真实假绿记录为证）；二是 `**Refactoring is not part of the loop.**` 只说了 refactoring 归哪里，没说为什么，也没给不带票的单独使用留去处。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `SKILL.md` `## Rules of the loop`，`**Refactoring is not part of the loop.**` 的后半句 "made on the ticket under the same writing rules as the code that was reviewed" | 6 | `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 105 行（step 3）已写 "fix the in-ticket findings once, under the writing rules that governed the first write"；worker 在修复轮那一刻加载的是 `implement` 第 3 步，不是 `tdd`。对不带票的单独使用（`ask-matt` 的 No 一支，`mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 25 行），"the ticket" 与 "the code that was reviewed" 都不存在，这半句指向空处 | `implement` 第 3 步承担，原样在；无剩余风险 | 整条按 B 的第二条草稿重写；merge-note `mmw-v2/merge-notes/tdd.md` 第 13 行那一条同步改写 |

除此之外没有可删的。逐项核过的：

- `**Test only at pre-agreed seams.**` 一段本仓加的两句（"The agreement is something written down, never a remark in conversation." 与 "Working from a ticket, the seams under test are the ones its `## Seam` section names."）改变了夜里 worker 的做法（不再停下等用户），不是冗余。
- 这一段**没有**"票缺 `## Seam` 时怎么办"的退路，merge-note 说是有意不写。我复核了这条决定的前提：本仓 tracker 上 84 张 `mmw:ticket` 票里缺 `## Seam` 的只有 #571、#564、#342，三张都是 `ready-for-human`，没有一张 agent 票缺。另一个 tracker 没查。所以不写退路是对的，不是过度防御的反面。注意 Nowledge Mem 里有一条审查教训：`verify-ticket.py` 的 lint 不检查票上的 `## Seam`（我在 `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 里 grep `Seam` 确认 0 处命中）。所以"不会缺"靠的是 `to-tickets` 模板，不是脚本拒绝；目前的数据支持这个判断。
- `tests.md`、`mocking.md` 是上游原文，`code-review` 的 Tests axis 按小节名引用它们。我核对了 `mmw-v2/upstream/skills/engineering/code-review/references/tests-reviewer.md` `## 3. The test smell baseline` 引用的五个名字（**Tautological tests**、**Implementation-detail tests**、"Verifying through external means instead of interface"、"Test name describes HOW not WHAT"、"Don't mock"），在两份文件里都能逐字找到。这两份一个字都不该动。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 开头 "TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping … consult them before and during the loop, not after."：告诉 agent 这份技能是边写边查的标准，不是写完再对的清单。
- `## What a good test is` 的 "Code can change entirely; tests shouldn't. A good test reads like a specification …"：整份技能的价值判断都从这句推出来，agent 在清单之外碰到新情况时靠的就是它。
- `## Seams: where tests go` 的 "You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case."：解释了为什么要先约定 seam，也是 `code-review` Tests axis 的 `**Coverage.**`（"This repository tests at seams agreed before the work starts, deliberately not everywhere"）的出处。删了它，"只在约定 seam 上测"就只剩一条没有理由的禁令。
- 同段本仓加的 "The agreement is something written down, never a remark in conversation."：merge-note 明写这一层必须留；它让夜里的 worker 知道票本身就是那份约定，不用停下来找人确认。
- `codebase-design` 指向句末尾的 "it is a reference to consult, not a session to run"：防止 agent 把 `codebase-design` 当成一段要跑的流程。上游 `mmw-v2/upstream/docs/engineering/codebase-design.md` 记录过这个误用（issue #449）。
- `## Anti-patterns` 的 **Tautological** 里 "Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec."：它给了 agent 一个判据，而不只是一个坏例子。
- `## Anti-patterns` 的 **Horizontal slicing** 整条，尤其 "Bulk tests verify _imagined_ behavior" 与 "each test a **tracer bullet** that responds to what the last cycle taught you"：`implement` 的 `references/writing-interface-code.md` 第 29 行声明例外时，引用的正是这里讲的理由（"because they verify imagined behaviour"）。删掉它，那条例外就失去了依据。
- `## Rules of the loop` 的 "Don't anticipate future tests or add speculative features."：这是 minimal implementation 的理由，也和 `implement` 的 `Owns two grades` 一致。

### 缺口与补充草稿

- **缺口 1：`**Red before green.**` 只说"先写失败的测试"，没说要跑一次、亲眼看它失败，并且失败原因是缺了那个行为，而不是测试本身跑不起来。** 在 MMW 里没有任何机制补这一步：
  - `verify-ticket.py` 的 `run_baseline`（约第 1985 行起）在认领时对 base commit 跑一遍各条判据。那时本票要新增的测试文件或用例还不存在，判据变红只说明"文件或用例不存在"，证明不了这条测试能对缺失的行为变红。它只抓得到"动工前就已经绿了"（`green_before_work_block`）。
  - Tests axis 明写 "You are read-only and run no test"（`tests-reviewer.md` 第 3 行），只能靠读代码去判断一条测试"could ever have failed"。
  - 真实代价有记录：Nowledge Mem 记录 `02fc9cc5-bba3-4460-a0c6-f6a374653393`（2026-09-09，"假绿测试：判据看似通过实则从未运行"）列了四种在落地审计中反复出现的假绿，"每一条都是先写成绿，靠故意把被测物改坏、看它会不会变红才抓出来"。
  - 本仓自己的文字已经默认了这一步：`writing-interface-code.md` 第 29 行写 "write it against the row, watch it fail, wire that row, watch it pass"，而 `tdd` 本身没有这句话。

  agent 因此会怎么做错：它会一次写好测试和实现，直接跑成绿，然后以为 red → green 已经做过了。上游在 `mmw-v2/upstream/docs/engineering/tdd.md` 的 "It wrote the implementation before the test" 一问里承认这种情况，并**有意**不在技能里加强要求（"forcing the point harder restricts the agent's creativity for little gain"）。所以按 `SKILL-SET-REVIEW.md` `### Upstream skills` 第 107 行"先在调用方读的那一行接"，这句建议放在 `mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 36 行（"Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams."）之后，不改 `tdd` 上游原文：

  > Where an acceptance criterion's `CHECK:` names a test case, that case is your first red test: run it before writing the code it covers and read why it fails. Red that comes from a missing file, an import error or a typo in the case name proves nothing; the test counts as red only when it fails because the behaviour is absent. No later step does this for you: the claim-time baseline ran before the test existed, and the review reads tests without running them.

  它改变做法的地方有两处：worker 写的第一条测试就是 `CHECK:` 要跑的那个用例，用例名对不上的问题当场暴露，不会拖到 step 1；而且流水线里唯一能证明"这条测试能失败"的观察，由唯一在场的人做了。如果用户希望不带票的单独使用也受益，另一种放法是在 `tdd` 的 `**Red before green.**` 后面加一句 "Run it and watch it fail for the reason you expect before writing the code."，但这就是新增一处上游改动，要在 `mmw-v2/merge-notes/tdd.md` 加条目，并且和上游在文档里写明的取舍相反。我倾向只放在 `implement` 里。

- **缺口 2：`**Refactoring is not part of the loop.**` 只说了 refactoring 归哪里，没说为什么，而且不带票时它指向一个不存在的修复轮。** 上游删掉 refactor 阶段的理由写在 `mmw-v2/upstream/docs/engineering/tdd.md`（"agents essentially never performed it, and … review and implementation work better as separate sessions"），但这些文档不随技能装进宿主，agent 看不到。agent 因此可能做错两件事：不带票单独用时，它永远不会整理结构；带票时，它可能把 `implement` 第 30 行要求的"删掉被本次改动变多余的分支"也当成 refactoring 推迟。建议整条改为：

  > - **Refactoring is not part of the loop.** Green means the slice is done; restructuring is a separate pass over the finished change, where it is judged with fresh eyes instead of skipped under the next red. Working from a ticket, that pass is the round of fixes that follows its review; with no ticket, it is a deliberate pass once every slice is green. Keeping the change itself correct (a caller of what you changed, a branch your change made dead) is part of the slice, not refactoring.

  放在原位，替换现有一条。它保留了 merge-note 要的"不点 stage 的名"和"归 review 之后的修复轮"，删掉了复述 `implement` 的那半句（A #1），并补上了不带票时的去处。merge-note 第 13 行的条目要同步改写。

没有发现前几轮减重删掉的思想性段落：本目录只有五次提交碰过，`git log -p` 逐条看过，改动是 host 中立、seam 载体、互指行的加上和撤掉，以及一条票缺 `## Seam` 时的退路被删（理由见 A 之后的说明）。没有删掉解释性段落。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| — | — | 无。技能本身没有编号流程和模板；`No test is written at an unconfirmed seam` 与 `**One slice at a time.**` 是方法本身，不是作者的偏好，而且 `implement` 在界面票上已经用 `writing-interface-code.md` 第 29 行显式声明了例外，说明规则在需要时是可以放开的 | 不改 |

有一句上游原文可能让 worker 做错，单独列出：`## Seams: where tests go` 的 `Ask: "What's the public interface, and which seams should we test?"`。它排在"有票看 `## Seam`、无票跟用户确认"之后，但没有限定只在无票时用，按字面读是对所有情况的一句固定提问。夜里的 worker 如果照做，会把问题留在屏幕上，而 `turn-guard.py` 只管 main agent，不会拦住 worker 结束回合（`mmw-v2/skills/dispatch/scripts/turn-guard.py` 头部注释的 "Whose turn" 一段）。抵消它的是 `implement` 第 22 行（"copied from the ticket's **Seam**"）和第 29 行（"Put no question on the screen"）。我没有找到它真的触发过的记录。按 `SKILL-SET-REVIEW.md` 第 107 行，调用方的文字已经接住了，**不建议改上游原文**；只是如果以后发现 worker 在 seam 上提问，原因就在这里。

## 脚本

无。这个技能没有 `scripts/` 目录；`agents/openai.yaml` 是上游的宿主清单，两行，不涉及 `disable-model-invocation`。

## 与其他技能的重复或交接问题

- `implement` → `tdd`：`implement/SKILL.md` 第 36 行按名字交接，写法符合 `### Hand-offs`。缺口 1 的草稿建议放在这里。
- `implement` 第 105 行（step 3）与 `tdd` 的 `**Refactoring is not part of the loop.**` 后半句重复，留 `implement` 那份（A #1）。
- `implement` 第 30 行（"delete it in the same commit"）与 `tdd` 的 "Refactoring is not part of the loop" 字面上有张力，缺口 2 的草稿在 `tdd` 这边用一句话化解，`implement` 不用改。
- `implement` 第 20 行已经把 worker 带到领域词汇表（root `CONTEXT.md` 或 `CONTEXT-MAP.md` 列出的各份）。`tdd` 第 10 行的 "read `CONTEXT.md` (if it exists)" 对 worker 是重复的，对使用 `CONTEXT-MAP.md` 的仓库（例如本仓，根目录没有 `CONTEXT.md`）又写得不全。这是上游原文，`diagnosing-bugs/SKILL.md` 第 10 行是同一句话，上游 ADR `mmw-v2/upstream/.agents/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md` 把它定为有意写得模糊的软依赖。不改。
- `code-review` Tests axis 读 `tests.md` 与 `mocking.md`：引用的五个名字都能逐字找到，merge-note 两边（`tdd.md` 第 19 行、`code-review.md` 第 37 行）都指 "第 3 节"，与现文一致。
- `tests-reviewer.md` 第 19 行把"没有 `CHECK:` 点名的测试文件"算作一条 finding，而 `tdd` 鼓励一刀一条测试。worker 如果把每一刀的测试都写进新文件并提交，就会被审出来。管这件事的是 `implement` 第 40 行（"Commit tests only where the ticket asks for them …"），应该留在 `implement`，`tdd` 不需要知道。缺口 1 的草稿让第一条测试就落在 `CHECK:` 点名的用例上，也减少了这种情况。
- `ask-matt` 的 No 一支把用户送到不带票的单独 `tdd`：这时 refactoring 没有去处，由缺口 2 的草稿补上。

## 没查到的

- merge-note 说"两个 tracker 的 154 张 agent 票"都有 `## Seam`，我只核了本仓 tracker（84 张 `mmw:ticket`），另一个 tracker 没查。
- 没有读 worker 的会话记录，所以不知道 `Ask:` 那句和"先写实现后补测试"在夜里实际发生过多少次。缺口 1 的证据是审计记录里的假绿模式，以及"没有任何机制观察测试变红"这一事实，而不是 worker 跳过 red 的直接观察。
- `verify-ticket.py` 只读了 baseline 相关的函数（`baseline_skipped`、`run_baseline_if_needed`、`run_baseline` 开头、`green_before_work_block`）和第 72–80 行的常量，其余部分没读。
