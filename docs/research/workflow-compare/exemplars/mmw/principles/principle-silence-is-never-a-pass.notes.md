# 原则范本注解：`exemplars/mmw/principles/principle-silence-is-never-a-pass.md`

这份范本是 MMW 自有原则 `silence-is-never-a-pass`（R18 §5.2 表第 1 行）按 R20 5.4 模板写成的样子，给写 B1 原则票的会话当基准。名字按 R19 §4.3 保留（与 ADR `0008-silence-is-never-a-pass.md` 同名），没有用户定的名字。

R18 §5.1 要求「规则与理由逐字取自原文」。这条原则的主要原文 ADR 0008 是中文，而技能文本必须是英文（SSR L78「Skill text is English」）。所以能逐字搬的只有英文来源里的句子，ADR 0008 的句子只能翻译。下表逐句标明。

## 逐段来源

| 段 | 来源 | 结构依据（pstack） | 写法依据（mattpocock） |
|---|---|---|---|
| frontmatter `name` | 搬运：R18 §5.2 slug | S-R1、S-G6（R18 §5.1：两个键） | 无 |
| frontmatter `description` | 新写。第 1 句「Apply when …」是可观察的情境，出处 R18 §5.2 表「被谁点名」列（写检查的 P12、P15、`code-checkers`，读结果的 `ui-acceptance`、`retro`）；第 2 句是规则摘要，出处同表「规则」列。第 1 句与 mode `## Principles` 的索引行逐字相同 | X7；R20 5.4 frontmatter 行（`PS:skills/principle-attack-the-premise/SKILL.md` L3） | X7 |
| `# Silence is never a pass` | 新写：slug 转 sentence case（X14） | `principle-attack-the-premise` L7 | 无 |
| 规则第 1 句 | 搬运：`CODING_STANDARDS.md` L10 第 2 句「A check that could verify nothing says so instead of reading like a pass (ADR 0008).」，删去括注「(ADR 0008)」（S-R3：出处不进原则文件；见改写清单） | 同文件 L9 | W-R1（跨任务成立） |
| 规则第 2 句 | 新写，英译 R18 §5.2 规则列前半「一道检查跑了却什么都没做、或绿灯可能来自产品正确之外的原因，就是失败」；R18 注明该列归并自 ADR 0008 L8、`night.md` L127、`ui-acceptance` L10 | 同上 | W-G6（用 check、green 这类领域词） |
| `**Why:**` 第 1 句 | 翻译：ADR 0008 L8「一道既没干活也没出声的闸口，读起来和一道通过了的闸口完全一样。」 | L11 | W-G2 |
| `**Why:**` 第 2 句 | 翻译：ADR 0008 L14 末句「「查不了」和「查过了，没问题」是两个答案，其中只有一个是沉默。」译作「only the second may be quiet」，把原文「其中只有一个」的所指写明 | 同上 | W-G2 |
| `**Pattern:**` 第 1 条 | 翻译：ADR 0008 L14「跑不动的时候——没数据、没应答、没网络——它要大声说跑不动并失败。」 | L13–17 粗体祈使标签 | W-G7 |
| 第 2 条第 1 句 | 翻译：ADR 0008 L36「新增闸口时多一步自检：把它的失败路径跑一遍，确认它在「跑不动」时会红，而不是静默放行。」 | 同上 | W-G7 |
| 第 2 条第 2 句 | 搬运：`mmw-v2/skills/ui-acceptance/scripts/journey.py` L16–17「An oracle that cannot go red is not an oracle」，逐字（原文后接 ADR 路径括注，按 S-R3 不带） | 同上 | W-G6（oracle 是测试领域的既定术语，SSR L75） |
| 第 3 条 | 改写：`mmw-v2/skills/ui-acceptance/SKILL.md` L10 第 2 句的通用形式（见改写清单第 3 条）。R18 §4.1 `ui-acceptance` 行：L10 的理由移到这条原则；原句里 story、journey、screen contract 的版本留在 `ui-acceptance`，作为它点名这条原则时的本地后果（W-P2） | 同上 | X3：禁令「never the check」与正面动作「change the product」同句；W-R1（每句跨任务成立） |
| 第 4 条 | 改写：`mmw-v2/skills/dispatch/references/night.md` L127 的条件句「a `CHECK:` that is already green while the thing it names is broken or never reached」与结论「it asks for a negative control」，重组成一句，并把票的专有词换成通用词（见改写清单第 4 条） | 同上 | W-G6（negative control 是测试领域的既定术语，也在词表 `docs/contexts/ui-acceptance/CONTEXT.md` **negative control**）；W-R1 |
| 四个粗体标签 | 新写：R20 5.4 `**Pattern:**` 行要求粗体祈使标签加句号；源里没有标签 | S-R1 | W-G5 |
| `**The test:**` | 翻译：ADR 0008 L8 第 1 句「改动或新增流水线的任何一道闸口时，要问它的问题不是「坏情况它抓不抓得住」，而是：它跑了一遍却什么都没做，有人会发现吗？」；「闸口」译作 check，原则跨出流水线闸口，覆盖测试与 oracle（R18 §5.2 调用方列）。这一问只写在这里：它原本同时是 `**Pattern:**` 第 1 条与 `**The test:**`，两处重复（SSR L40），删去的是 Pattern 那一条（见删去的句子） | L19–21（R20 5.4 可选节） | W-G5（是非测试） |
| 区分句 | 搬运：R18 §5.4 第 2 条给出的英文原句，逐字 | L23，放在最后（S-G3） | S-G3 |

结构依据的总出处：R20 5.4 模板（`PS:skills/principle-attack-the-premise/SKILL.md`）；S-R1 固定标签；S-R2 不装命令与只属于某一步的规则；S-R3 出处不进文件。写法依据的总出处：W-R1 每句跨任务成立；W-G2 理由在规则旁；W-G5 判断点写成能失败的测试。长度 20 行，在 pstack 原则的 16–34 行之内（S-G9）。

## 必须改写、做不到逐字搬运的地方

1. **ADR 0008 L8、L14、L36 的五句只能翻译**：ADR 是中文，原则文件必须是英文（SSR L78）。这五句是 R18 §5.1「逐字取自原文」做不到的地方，逐句是：`**Why:**` 第 1 句（L8）、`**Why:**` 第 2 句（L14）、`**Pattern:**` 第 1 条（L14）、`**Pattern:**` 第 2 条第 1 句（L36）、`**The test:**`（L8 第 1 句）。建议把这五句英文译文先写进 ADR 0008 的一个英文段落，或写进 ADR 0032 的出处记录，再由原则逐字搬运；否则逐字搬运检查只能把它们登记为五行 `new`。
2. `CODING_STANDARDS.md` L10 第 2 句删去括注「(ADR 0008)」：出处不进原则文件（S-R3）。这是句内删字，不属于 T2 的五种机械改写，要在票上写成 `replace`。
3. `ui-acceptance` L10 第 2 句「So write the story, the test, the journey and the harness so that green can only mean the product is right; when an oracle is red, change the product, or open a child when the design or the screen contract is wrong, never the check.」→「Write each check so that green can only mean the product is right; when it is red, change the product, or say the specification is wrong, never the check.」写成 `replace`。原句的 story、journey、harness、oracle、screen contract、「open a child」只在界面验收与票里成立（W-R1、S-R2），而这条原则的调用方还有 `code-checkers` 与 `retro`（R18 §5.2），在非界面任务里第一次读的 agent 不知道 story、journey 指什么。句首「So」承接的前一句「During a night these oracles are the only eyes on a UI …」同样只对界面与夜里成立，留在 `ui-acceptance`。原句整句留在 `ui-acceptance` 原处（copy，不是 move），作为本地后果。
4. `night.md` L127 的问句（「Is it a gap in the criteria themselves — … → a ticket, `senior-worker`, and it asks for a negative control.」）改写成陈述句「A check that is already green while the thing it names is broken or never reached is a gap in the checks themselves, and its fix asks for a negative control.」：原句是 orchestrator 分拣 finding 的第 2 问，结论「a ticket, `senior-worker`」只属于 closing pass（W-R1）。原则只取「已经绿着却什么都没证明，就是检查本身的缺口，修法要带 negative control」这一层；「a `CHECK:`」「the criteria」是票的写法，换成「a check」「the checks」，票上的版本留在 `to-tickets` 与 `run-a-night`。原句还带一个长破折号（U+2014），改写时去掉（S-G5）。

## 删去的句子（写成 `drop` 行时用）

- ADR 0008 L8 第 1 句作为 `**Pattern:**` 的一条（原第 1 条「**Ask whether anyone would notice.**」）：它指导「新增或改动一道检查时问什么」，与 `**The test:**` 是同一问。删后由 `**The test:**` 指导，它的译文保留了「When you add or change a check」这个时机。
- ADR 0008 L38「测试套件自己也在这条规则之下：verify-ticket 的测试用自己的租约注册表与端口段，并有守卫反向验证守卫本身没有失效。」：它指导 MMW 自己的测试套件怎样守这条规则，只对 MMW 仓库成立（W-R1）。删后由 `**Pattern:**` 第 2 条「Prove a new check can fail」指导通用的做法；MMW 测试套件的具体做法留在 ADR 0008 原处。
- ADR 0008 L10–13 的前两条（点名事实、说出唯一出路）：它们指导「写一条拒绝」的情形，归 **principle-refusals-name-one-next-step**（R18 §5.2 第 6 行）。
- `implement` L22 末三句（「A check that will not pass is answered by … never by bending the baseline, the harness or the test. The checks exist … An honest `HANDOFF REQUIRED` …」）：R18 §5.2 把它们列为这条原则的出处，但它们说的是 ticket、`ALL MET`、`HANDOFF REQUIRED`，只在票里成立（W-R1）。它们留在 `work-a-ticket` 的 `#### While writing code`，作为点名这条原则时的本地后果（W-P2；R18 §3.3 P15 已这样写）。原则里的「change the product, never the check」由 `**Pattern:**` 第 3 条（`ui-acceptance` L10 那一句的通用形式）承担同一个意思。
- `night.md` L7「a criterion loosened, … to make one close is a defect that lands under a green mark」：只对 orchestrator 成立，留在 `run-a-night` 首段（R18 §3.3 P12）。
- `to-tickets` L86 末句「A `CHECK:` must not search for its own object; … often cannot fail at all.」：它指导「写一条判据」时对象从哪来，是写判据的领域规则，留在 `to-tickets`（R18 §5.4 第 1 条：领域参数留在原处）。原则的 `**The test:**` 覆盖它的意思。

## 与 R18 的偏离

- **R18 §5.1「规则与理由逐字取自原文」只做到一部分**：ADR 0008 的五句是中文，只能翻译（改写清单第 1 条）；`CODING_STANDARDS.md` L10 与 `ui-acceptance` L10、`night.md` L127 的句子各有一处 `replace`（改写清单第 2 至 4 条）。逐字搬运的只有 `journey.py` L16 至 L17 与 R18 §5.4 的区分句。
- **R18 §5.2 列为出处的 `implement` L22 末三句没有用**：它们只在票里成立，留在 `work-a-ticket` 作本地后果（见删去的句子）。

## 没有核对的

- R18 §5.2 列的其余出处（`ui-acceptance` 规则 3–5、`code-checkers` 第 5 步探针理由）没有逐句读；它们在 R18 §4.1 里是「点名原则加本地一句」，不进原则正文。
- 译文的措辞没有请用户或另一位读者核对是否忠于 ADR 0008 原意。
