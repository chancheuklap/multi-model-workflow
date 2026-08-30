# code-review

源目录：`mmw-v2/upstream/skills/engineering/code-review/`

上游是一个文件：`SKILL.md` 里五步走完，两个轴的 brief 与 Fowler 十二条坏味道全文都排在步骤中间。我们拆成一个路由 + 四个 reference，并加了第三个轴。

## 哪一段挪去了哪个文件

| 上游 `SKILL.md` 的段落 | 落到 | 我们的意图 |
| --- | --- | --- |
| 第 1 步 pin the fixed point（三条 git 命令、三点 diff、空 diff 要在派子代理之前失败） | `references/dispatch.md` 第 1 节 | 原文的判断一条没改。上游改这三条命令 → 收上游 |
| 第 2 步 identify the spec source（四级查找顺序：commit message 里的票号 → 用户给的路径 → `docs/` `specs/` `.scratch/` 下按分支名找 → 问用户） | `references/spec-reviewer.md` 第 2 节，且换掉了 | 这条流水线的票一定有 `## Parent`，四级查找的后三级是给没有票的场景用的。改成沿 `## Parent` 读 spec 指名的小节 + `## Testing Decisions` + `## Out of Scope`，读法与 `implement` 的读法收窄同一套。上游改这一步 → 不收，除非它也变成从票走 |
| 第 3 步 identify the standards sources（仓库里哪些文件算编码规范）+ smell baseline 全文十二条 + 「repo overrides」与「always a judgement call」两条规则 | `references/standards-reviewer.md` 第 2、3 节 | 十二条逐条原文保留，措辞改成对子代理说的第二人称。上游增删坏味道 → 收上游，改这个文件 |
| 第 4 步 Standards sub-agent prompt 的 brief | `references/standards-reviewer.md` 第 4 节 | 要点全在。上游改 brief → 收上游 |
| 第 4 步 Spec sub-agent prompt 的 brief（缺项、scope creep、实现得不对三类，每条引 spec 原文） | `references/spec-reviewer.md` 第 3 节 | 三类保留。加了一条我们自己的禁令：不读 `prototypes/` 下的基线目录——照不照基线由某条验收标准跑的 `visual-parity` 判，是像素与 ARIA 比对，不是读出来的。上游改 brief → 收上游，这条禁令保留 |
| 第 4 步「把 baseline 全文粘进子代理 prompt」 | 退场 | 上游让派发者把 smell baseline 粘进 prompt。我们让子代理自己读 reference 文件：粘贴会产生第二份副本，与 reference 里的那份各自漂移。`SKILL.md` 与 `references/dispatch.md` 都明写 prompt 只含起点 commit、票号、reference 路径三个值 |
| 第 5 步 aggregate（两份报告分列、不合并不重排、末尾一行汇总） | `references/dispatch.md` 第 4 节 | 「不合并、不跨轴重排」原样保留。落点从「present 给用户」改成 `gh issue comment` 写到票上，首行固定 `REVIEW <base commit>..<HEAD commit>`：reviewer 的会话会结束，修它的 worker 读的是票 |
| 「Why two axes」 | `SKILL.md`，改成「Why three axes」 | 多一行 Tests 轴的对照 |
| 无 | `references/dispatch.md` 第 3 节（票内 / 票外分类） | 我们加的。发现分两类：碰本票验收标准或 spec 决策的是票内，其余是票外。派发者做这个分类而不是留给读者，因为两类的下一步不同——票内修一轮，票外开 sub-issue 且不阻塞。轮数上限与怎么修不在这里，在 `implement` 的收尾段 |
| 无 | `references/tests-reviewer.md` 整个文件 | 我们加的第三个轴，见下一节 |

## 第三个轴：Tests

上游只有两个轴，都不看测试内容。这条流水线里，测试是 worker 自己写的，`CHECK:` 跑的是 worker 自己写的用例，verifier 重跑的是同一条命令——一个期望值按被测代码同样算法重算一遍的用例，从写到关票没有任何一步会怀疑它。Tests 轴是唯一问「这个绿色证明了什么」的读者。

判据不是自造的，抄 `mmw-v2/upstream/skills/engineering/tdd/tests.md` 与 `tdd/mocking.md`：tautological、implementation-coupled 六条 red flags、绕过接口验证、测试名说 how 不说 what、mock 越过系统边界。**这两份文件是同一批判据的另一个副本：改 `tdd/tests.md` 或 `tdd/mocking.md` 时对着 `references/tests-reviewer.md` 第 2 节看一遍，反过来也一样。** 第六条「只测了 happy path」是这里独有的，`tdd` 那边没有。

两条禁令写在文件末尾，都有出处：不报覆盖率（`tdd/SKILL.md` 的「Test only at pre-agreed seams」——这条流水线故意不追覆盖率），不追加票上没有的测试标准（reviewer 自设通过标准，正是验收标准这一节存在要防的事）。

审哪些测试文件不由派发者告诉它：子代理自己 `gh issue view`，从每条 `CHECK:` 里点名的测试文件与用例名取出清单，清单之外的测试文件仍可报但归票外。

## 下次拉上游怎么合

上游只有 `SKILL.md` 一个文件，我们有五个，冲突一定落在 `SKILL.md` 上。

1. 拿到冲突后，先看上游改的是哪一步，对着上表第一列找到它现在住在哪个 reference 文件里，把改动搬进那个文件，`SKILL.md` 保持只有路由。
2. 上游给 `SKILL.md` 加了新的一步：判断它是派发者的动作（进 `references/dispatch.md`）还是某一个轴的判据（进那个轴的 reference）。两者都不是才留在 `SKILL.md`。
3. 上游加了第三个轴：与我们的 Tests 轴合并还是并列，看它问的是不是同一个问题；并列的话 `references/dispatch.md` 的子代理表与 `SKILL.md` 的路由列表都要加一行。
4. `SKILL.md` 有硬上限：正文不超过 40 行非空行，且不含 smell baseline 正文与任何子代理 brief 原文。收上游时超了，就是有东西没搬进 reference。
5. 四个文件一律英文，不写出处、不写落地记录。

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改成三个轴。上游改这一行 → 收上游措辞，轴数按我们的 |
