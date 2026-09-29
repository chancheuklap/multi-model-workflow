# R21a 文字完整性的两道机械检查：逐字搬运检查与结构 lint

本文设计两道检查，并给出它们进 B0 的票草案。目的是：落地的 worker 在把技能文字搬到新层（mode、playbook、原则、能力技能）时，不能顺手改写句子，也不能把组件的骨架写乱。R18 第 17 节 D9 把这件事定为「搬运的句子逐字保留，由逐字搬运检查与结构 lint 强制（`R21-text-integrity-checks.md`，进 B0）」；本文就是那份设计，文件名按本轮任务取 `R21a`。

**标注。** 「原文」＝文件里写着的；「已核实」＝本轮回到文件或跑命令看到的；「推断」＝由原文推出、原文没直接写的。路径不带前缀时相对仓库根；pstack 路径相对 `docs/research/code-landing-refs/pstack/`。

---

## 0. 结论（先读这里）

1. **两道检查，两个脚本，一个共用模块，都放在 `mmw-v2/tests/lib/`。**
   - `check_verbatim_moves.py`（逐字搬运检查）：读票上的 `## Moves`（搬运清单），比对源文字（钉在一个提交上）与目标文字（`HEAD`），列出被改写、被删、被新加却不在白名单里的句子，非 0 退出。
   - `check_component_skeletons.py`（结构 lint）：按文件所属的组件类型（mode、MMW 自写 playbook、导入的 playbook、原则、MMW 自有能力技能）检查骨架与禁用句型。
   - `skill_text.py`：两者共用的 Markdown 切分、句子切分、路径规范化与组件归类。
   - 放在 `tests/lib/` 而不是 `mmw/scripts/`：它们只在本仓库搬 MMW 自己的文字时有用，消费仓库的 agent 从不运行它们（第 3.7 节）。
2. **比较粒度是句子，不是段落，也不是行。** pstack 的骨架会把一段拆成几个编号步骤、把一个小节标题变成步骤的粗体标题；按段落比会把每次合理的拆分都报成改写，按行比会被重新折行打乱。句子是 mattpocock 文字里理由与规则的最小单位（第 3.3 节）。
3. **检查回答三个问题**：源范围里的每一句都到了指定位置（carried）；指定目标位置里的每一句都有来处（accounted）；这张票在自己的分支上没有改动清单以外的技能文字（untouched）。第三问让 R18 第 10 节批次票验收条件第 1 条（每一段要么搬走、要么写明留下的理由）在文字上变成机器可判（第 3.1 节）。
4. **允许的机械改写只有五种**：空白与折行、列表符号与编号、标题与粗体步骤标题的互换、路径与链接写法（按解析到的文件比）、清单里逐行列出的改名；另外允许插入括注的原则点名 `(**principle-<slug>**)`。其余一切差异，包括加粗、标点、语序，都算改写；spec 想改的句子在清单里用 `replace` 逐条写出（第 3.4 节）。
5. **改名表不直接全局套用**：每张票的清单只抄入本票执行的改名行，`--lint-drafts` 核对这些行都来自用户过目的改名表。原因：R18 第 2.4 节要求每批的文字只点名当时存在的组件，全局套用会让 B1 的文字提前写上 B2 才有的名字（第 3.5 节）。
6. **结构 lint 与 `check_wiring.py` 分开，共用 `skill_text.py`。** 结构 lint 管「这个文件按它的类型写得对不对」，修复在同一个文件里；`check_wiring.py` 管「文件里的名字是否通到存在且允许的东西」，修复常在另一个文件。R18 第 7.5 节第 7 类（骨架）、第 3 类的句型部分、第 4 类（不按编号）移入结构 lint（第 4.4 节）。
7. **结构 lint 从 B0 起就失败，靠一张例外表过渡**：今天树上已有的违规逐条登记在 `skeleton-exceptions.tsv`，每条写到期批次；新违规立刻失败；`--batch Bn` 让到期未还的条目失败，这就是 R18 第 10 节验收条件第 2 条的机器形式（第 4.5 节）。
8. **负控**：逐字检查用一组固定种子的变异（在一份真实技能文件的副本上每次改一处）证明每一处都被报出；结构 lint 每条规则一份必须失败的夹具，外加在今天的树上必须报出第 4.3 节 `capability-next-step` 的 8 行，它们覆盖 R14 第 2 节名单里位于自有技能的 6 句（第 3.9、4.7 节）。
9. **B0 三张票**：预检入口 `preflight.sh`（前置，消除 12 个 `run.sh` 各抄三行的重复，也让 `check_wiring.py` 那张票只改一行）；逐字搬运检查；结构 lint（第 5 节）。
10. **这两道检查管不到的**：句子摆放是否仍然讲得通、理由是否还挨着它的规则（顺序检查只能部分覆盖）、新写的句子写得好不好。这些仍由评审的 Spec、Standards 两个 axis 与 `SKILL-SET-RULES.md` `## Verifying` 的「新会话实跑」判断（第 3.10 节）。

本文没有需要你决定的事项：检查的形式、位置与严格程度都是工程决定，理由与放弃的备选写在各节。唯一与你有关的是结果：落地后，spec 没写进清单的改写一律过不了票；这正是 D9 的要求。

---

## 1. 为什么要机械检查，而不是写进规范让 worker 自觉遵守

- **规则已经写着，但只靠文字。** `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（本仓自有文件，squash `5b1a4c51` 的上游原文里没有它，已核实）`## Editing` 第 2 条：「A load finding is fixed in the structure: move, merge, split at a branch, or delete whole sections, carrying each sentence that still applies across verbatim. Sentences the finding does not touch stay byte for byte.」第 5 条：「Text taken from another source keeps its authors' wording … Excerpts are quoted verbatim and collected into one block before they are placed」。本文的搬运清单就是第 5 条说的「collected into one block」，只是由 spec 在切票时写好，不留给 worker。
- **同一文件要求把能查的规则做成检查。** `### Scripts and judgement` 第 3 条：「A rule a script could check exactly becomes a check (a lint, a refusal, a test), not a sentence.」「逐字」与「骨架」都能精确判定。
- **两种写作风格在这里正面冲突，冲突点正是 worker 最可能动手的地方。** pstack `skills/poteto-mode/playbooks/authoring-a-skill.md` 第 10 行：「Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one.」`SKILL-SET-RULES.md` `## What skill text is for` 第 1 条：「beside its steps a skill says what the work is for … and, next to a rule, the reason for it」。一个照 pstack 语气整理文字的 worker 会删掉 mattpocock 式的理由句；理由句决定 agent 在规则没写到的情形里怎么做（同一条的「A sentence beside a rule passes when you can name a case the steps do not cover」）。逐字检查把每一句被删的理由都报成 `DELETED`，除非 spec 在清单里写明 `drop` 与去处。
- **骨架统一是改造的目的本身。** R18 第 3.2 节给 playbook 定了统一骨架，第 1.3 节把步骤的粗体标题定为锚点（「标题就是锚点；跨文件只按标题引用」），脚本的指针 `mmw <slug>#<Step title>` 靠它解析。骨架写错，指针就断，这是运行故障，不只是好不好看。
- **pstack 自己有先例。** `skills/poteto-mode/scripts/check-plan.mjs` 第 5–21 行把必须原样出现的句子（常量 `RULE`）与必须出现的小节名（`PROGRAM_H3`、`SUB_BLOCKS`）写成检查器里的字面，逐行报 `file:line: message`（已核实）。本文的结构 lint 沿用这种「检查器持有被匹配的字面」的做法（R13 E8 也记了这一点）。

---

## 2. 先找现成的（按全局规则 14）

本轮检索了 GitHub 与包仓库，读了每个认真候选的至少一个实现文件。星数与最后推送时间是 `gh api` 本轮看到的。

| 候选 | 看了什么 | 覆盖多少 | 决定 |
|---|---|---|---|
| [jackchuka/mdschema](https://github.com/jackchuka/mdschema)（Go，80 星，2026-09-17 推送，MIT） | `internal/rules/structure.go`、`examples/tutorial.mdschema.yml` | 按标题层级的声明式 schema：必需/可选、`count`、顺序、`required_text`。能描述 mode 的小节序列；描述不了「编号列表项以粗体标题开头」「每步点名一个组件」「能力技能里不许出现 playbook 名」这类要跨文件清单的规则 | **不用，借它的写法**：规则表里的「可选」「次数」「顺序」三个概念照它的 schema 取。不用的理由：引入 Go 二进制，本仓库没有包管理器（根 `AGENTS.md` `## Package Manager`） |
| [DavidAnson/markdownlint](https://github.com/DavidAnson/markdownlint)（JS，6362 星，2026-09-29 推送） | `lib/md043.mjs`（MD043 required-headings） | 标题序列带 `*`、`+`、`?` 通配，正好是 mode 小节检查；自定义规则 API 可写其余规则 | **不用，借 MD043 的通配记法**写 mode 的小节序列。不用的理由：需 npm 安装（`npx` 要联网）；其余规则都要读 `skills.txt`、`imports.tsv`、playbook 清单，写成它的自定义规则并不省事 |
| [agentskills/agentskills](https://github.com/agentskills/agentskills) 的 `skills-ref`（25783 星，2026-08-09 推送） | `skills-ref/src/skills_ref/validator.py` | `name` ≤64 字符且等于目录名、`description` ≤1024 字符（规格原文见 [agentskills.io/specification](https://agentskills.io/specification)）；`ALLOWED_FIELDS` 不含 `disable-model-invocation` | **不用，抄两条限值**进结构 lint 的 `description-*`、`skill-name` 规则。不能直接跑：它会把上游技能的 `disable-model-invocation` 报成错 |
| [TheStack-ai/pulser](https://github.com/TheStack-ai/pulser)（TS，18 星） | `src/rules/description.ts` | description 是否含「Use when」类触发句、长度 | **不用**：只查有没有触发句，查不了「description 里是否夹带路由」；它的触发句正则与本文 `description-trigger` 规则同形，印证这条规则可行 |
| [PiotrTrzpil/markdown-diff-viewer](https://github.com/PiotrTrzpil/markdown-diff-viewer)（TS，15 星，MIT） | `src/core/move-detection.ts` | 两份 Markdown 之间按相似度找「搬走的段落与句子」，分块级与句级，拆分与合并另行检测 | **不用，印证粒度**：它也以句子为行内搬动的单位。它按相似度阈值（`MIN_COVER = 0.75`）认定「搬动」，一词之差正好被认成「搬了」；本文要的是相反的判定：一词之差就是改写 |
| [nipunsadvilkar/pySBD](https://github.com/nipunsadvilkar/pySBD)（Python，935 星，2024-08 推送） | `pysbd/segmenter.py` | 规则式断句，处理缩写 | **不用**：断句在两侧用同一个函数，断错不会造成漏报（第 3.3 节），标准库正则加一张缩写表足够；少一个依赖 |
| Python 标准库 `difflib` | — | `SequenceMatcher` 对句子序列做对齐与顺序检查，`get_close_matches` 给改写配对 | **照用** |
| `git diff --color-moved` | — | 同一次 diff 里搬动的行着色 | **不用做判定**：按行，重新折行即失效，不认改名与路径改写，也不产出退出码。可在评审时作人眼辅助 |

结论：没有覆盖八成需求的现成工具。两道检查自己写，用 Python 标准库（与 `mmw-v2/tests/lib/` 现有三个检查同一运行时），借上表三处的写法。

---

## 3. 逐字搬运检查 `check_verbatim_moves.py`

### 3.1 它回答的三个问题

| 问题 | 判定 | 用在哪一次运行 |
|---|---|---|
| **Q1 carried**：清单每条 `move`/`copy` 的源范围（在 `from` 提交上读）里的每一句，都出现在它指定的目标位置（在 `HEAD` 上读），顺序不变；被 `drop` 的除外 | 找不到 → `DELETED`；在别的目标文件或小节里找到 → `MISPLACED`；顺序变了 → `OUT-OF-ORDER`；`move` 的源句在源文件 `HEAD` 上还在 → `NOT-REMOVED`（成了两份，`copy` 不查这一项） | 每次 |
| **Q2 accounted**：清单点名的每个目标位置里，`HEAD` 上的每一句，要么来自某条 `move`/`copy`，要么在 `from` 时就已在同一位置，要么是 `new` 白名单 | 没有来处 → 与最接近的未匹配源句配对成 `CHANGED`（附逐词差异），配不上就是 `ADDED` | 每次 |
| **Q3 untouched**：这张票自己的分支 diff（`merge-base(HEAD, $MMW_BASE_REF)..HEAD`）里，技能文字文件在清单范围以外没有句子变化 | 变化的句子 → `UNTOUCHED-CHANGED`（清单的 `rename` 行在原处生效造成的变化除外） | worker 自己的运行；在收尾复核（closing pass）时 `HEAD` 就在 base 上，diff 为空，输出写明「untouched text: not checked, HEAD is the base」，不装作通过 |

- Q3 的「技能文字文件」＝ `mmw-v2/skills/**`、`mmw-v2/upstream*/skills/**`、`.mmw/playbooks/**` 下的 `.md`，加上清单点名的任何文件（例如根 `AGENTS.md`）。ADR、`CONTEXT.md`、spec 这类新写的文档不在范围内，由评审的 Spec axis 判。
- `$MMW_BASE_REF` 由 `verify-ticket.py` 在跑 `CHECK:` 时设为 `origin/<into>`（`mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 第 1871–1873 行，已核实）。
- Q3 的依据：`SKILL-SET-RULES.md` `## Editing` 第 2 条末句「Sentences the finding does not touch stay byte for byte」。它也实现 R18 第 10 节「每张批次票的验收条件」第 1 条的文字部分：源文件里每一句要么搬走（Q1），要么 `drop` 并写明理由，要么留在原处不动（Q3）。

### 3.2 搬运清单：放在哪、怎么写

**放在票正文的 `## Moves` 小节**，一个信息串为 `moves` 的围栏代码块。

- 理由：票是这条流水线唯一的状态（`mmw-v2/skills/verify-ticket/SKILL.md` 第 10 行「The ticket is the only state」）；评审与早上的你读的都是票；`CHECK:` 从 `$MMW_TICKET` 取自己的对象，符合 `to-tickets` `SKILL.md` 第 86 行「`CHECK:` takes the object it checks from … this ticket itself (the number comes from `$MMW_TICKET` …)」。
- 不会干扰判据运行：`verify-ticket.py` 只把 `## Acceptance criteria` 一节写成账本（第 694–704 行 `write_ledger`，已核实），`gate-check` 解析账本时跳过其余围栏（`mmw-v2/merge-notes/unlazy.md` `### scripts/lib/gates.mjs`）。
- 放弃的备选：清单做成仓库里的文件（例如 `docs/specs/<effort>/moves/<票>.moves`）。好处是离线可跑；坏处是 worker 的分支能改它，检查读到的就是被改过的清单。票正文被改会在 issue 上留下「edited」记录，文件被改只会出现在 `Outside Owns:` 一行里，两者都可见；选票正文是因为它是唯一状态。检查另接受 `--manifest <file>`，供自己的测试与白天手工使用。
- 清单行不以 `#` 开头，所以 `verify-ticket.py` 的 `section()`（第 441 行，按 `## ` 行切小节）不会被清单内容截断。

**格式：一行一条指令。**

````
```moves
from 68d90576
rename token `verify-ticket.py` -> `ticket.py`
move mmw-v2/upstream/skills/engineering/implement/SKILL.md:L12 -> mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Claim
replace "First claim the ticket: " -> "Claim the ticket: "
drop mmw-v2/upstream/skills/engineering/implement/SKILL.md:L12 "If you picked the ticket up yourself" : entry Picked up yourself carries it
new mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Claim "Done when `ticket.py <n> --preflight` printed `READY`."
new mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Where you are
copy 5b1a4c51:skills/engineering/implement/SKILL.md -> mmw-v2/upstream/skills/engineering/implement/SKILL.md
```
````

（示例值，演示语法；句子与步骤名取自 R18 第 3.3 节 P15 与今天 `implement/SKILL.md` 第 12 行，不是定稿。）

| 指令 | 含义 |
|---|---|
| `from <sha>` | 源文字的钉定提交，切票时 base 分支的 `HEAD`。必须有，且只能有一个。源范围都在这个提交上读，所以行号稳定 |
| `move <源> -> <目标>` | 源范围整体搬到目标位置，源处应不再有它 |
| `copy <源> -> <目标>` | 同上，但源处保留。源可以带修订：`<rev>:<path>`。两种用途：导入 pstack 文件（源在 `mmw-v2/upstream-pstack/` 子树，原文不动，R18 第 8 节）；上游技能「回原文」（源是 squash 提交里的上游文件，例如 `5b1a4c51:skills/engineering/implement/SKILL.md`，写法照 `SKILL-SET-RULES.md` `## Upstream examples` 的 `git show <commit>:skills/<bucket>/<skill>/<file>`） |
| `replace "<旧>" -> "<新>"` | 作用于紧挨着的上一条 `move`/`copy`：spec 决定的一处改写，旧串必须在那条的源范围里恰好出现一次。R18 里的「改动标注」都写成这一行，例如第 2.2 节 mode 首段把 pstack 的「leaf SKILL.md」改为「file」 |
| `drop <源> ["<句首>"] : <去处或理由>` | 这些句子不搬。不带引号串时是整个范围；带引号串时是范围里以它开头的那一句。理由写去处（「→ principle-the-tracker-is-the-state」「R18 第 4.1 节删」） |
| `new <目标> ["<整句>"]` | 白名单。带整句：这一句可以新写，必须逐字出现；不带：这个目标位置里整个都可以新写（用于 R18 标「新写」的段落，如 mode `## Autonomy` 的优先级句）。新写的句子逐条列进成功行的计数，评审看得到 |
| `rename <kind> <旧> -> <新>` | 本票执行的一条改名（第 3.5 节） |

**位置写法**（`<源>`、`<目标>`）：

- `path` 整个文件（含 frontmatter）；`path@description`、`path@name` 是 frontmatter 的一个字段。
- `path#<文字>`：标题文字等于它的那一节（含下级小节），或粗体标题等于它的那个编号步骤或段落（`N. **Claim.**`、`**Where you are.**`，比较时去掉末尾句点）。一个文件里匹配到两处即报错，改用行号。
- `path:L12` 或 `path:L12-L30`：行范围，只用于源（源在钉定提交上，行号不会漂）。目标只用标题或粗体标题，因为目标文件是新写的，行号在切票时不存在；R18 第 1.3 节也规定步骤标题就是锚点。

### 3.3 比较粒度：单元与规范化

**单元。** 两侧用同一个函数（`skill_text.py`）把 Markdown 切成单元：

| Markdown 块 | 单元 | 规范化 |
|---|---|---|
| 段落、引用块（去 `>`） | 句子 | 段内换行变一个空格，连续空白合一 |
| 列表项（`-` `*` `+` `1.` `1)`，任意缩进层级） | 句子；项首的粗体标题另成一个「标题」单元 | 去掉列表符号、编号与缩进；续行并入本项 |
| 标题（`#`–`######`） | 标题单元 | 去掉 `#`、行首编号（`1.`）、粗体记号、末尾 `.`/`:` |
| 粗体开头的段落或列表项 `**Title.**` | 标题单元 + 其余句子 | 同上 |
| 表格行 | 每个单元格的句子 | 去掉 `|`；分隔行忽略 |
| 围栏代码块 | 整块一个单元 | 只做改名表 `token`/`path` 行的替换，其余逐字节比 |
| frontmatter | 每个键一个单元；`description` 再切句 | — |
| HTML 注释、只有一个标签的行（`<issue-template>`） | 整体一个单元 | — |

- **标题单元的意义**：mattpocock 的 `### 1. Gather context`（`to-tickets` `SKILL.md` 第 16 行）搬进 playbook 成为 `1. **Gather context.**`，这是 R18 第 3.2 节骨架要求的形式变化，不是改写。标题只与标题比。
- **断句**：在行内代码、链接、缩写（`e.g.`、`i.e.`、`etc.`、`vs.`、`cf.`）处先占位，再在 `.`、`?`、`!`、`。` 之后、下一个字符是大写字母、反引号、`*`、`(`、`[`、数字或中文时断开。

**为什么是句子。**

- 段落：pstack 骨架会把一段拆成几步（R18 第 3.3 节 P15 的第 1–2 步来自今天 `implement` 第 12–18 行的几段），也会把几段并进一步。按段落比，每一次这样的拆并都报改写，检查就没法用。
- 行：重新折行、列表缩进一变就全部失配。
- 词：能看出改了哪个词，但说不出「整句删了」「整句挪到另一步」，而这两类才是 D9 要防的主要破坏。
- 句子：R18 与 `SKILL-SET-RULES.md` 谈搬运都以句子为单位（`## Editing`「carrying each sentence … verbatim」）；报告按句给出，逐词差异只作为 `CHANGED` 一行的附注。

**断句不准不会造成漏报。** 两侧用同一个断句函数，所以一句话若被断成两截，源和目标断法相同，照样逐一对上。改动总会改变至少一个单元的内容，所以任何改写都会以某个单元不匹配的形式出现。断句不准只会造成一种误报：worker 恰好在断句函数认不出的边界上拆了段（例如句号后跟小写字母）。这种情况下报告会给出那一句，spec 在清单里加一行 `new` 即可。所以用标准库正则就够了，不需要 pySBD（推断：由比较的对称性推出，第 3.9 节的变异测试会实测漏报率为 0）。

### 3.4 允许的机械改写与不允许的

允许（两侧规范化后比较，每一类单独计数，写进成功行）：

1. **空白与折行、列表符号与编号、标题与粗体标题互换**：见上表。
2. **路径与链接写法**：凡是指向文件的写法都解析成仓库内路径再比：
   - Markdown 链接 `[text](target)`：相对 `target` 按所在文件的目录解析；
   - 行内代码里形如路径的串（`references/x.md`、`scripts/y.py`）：按所在组件的根解析（能力技能是技能目录；mode、playbook、原则是 `mmw-v2/skills/mmw/`，与 pstack 的 `../references/X` 相对链接解析到同一处）；依据 `SKILL-SET-RULES.md` `### Paths and host neutrality` 第 1 条「a skill's own references and scripts are named by their path inside the skill」；
   - 「the `S` skill's `P`」：按 `S` 的技能根解析 `P`；依据 `### Hand-offs`「A file in another skill is named by skill and file」。
   - 解析后再经清单的 `rename path` 行映射。三种写法解析到同一个文件就相等。例：今天 `implement` 的 `` the `verify-ticket` skill's `references/sub-issues.md` `` 与 playbook 里的 `[sub-issues.md](../../verify-ticket/references/sub-issues.md)` 相等。解析不到的串按字面比，所以把路径改到另一个文件一定会被报出。
3. **改名**：只套用清单里列出的 `rename` 行（第 3.5 节）。
4. **原则点名的插入**：目标句里形如 `(**principle-<slug>**)` 或 `(**principle-a**, **principle-b**)` 的括注在比较前去掉，前提是 `mmw-v2/skills/mmw/principles/principle-<slug>.md` 在 `HEAD` 上存在；不存在就留着比，于是报成 `CHANGED`。依据 R18 第 3.2 节「原则用括注点名」与第 5.1 节「调用方：点名一次」。只允许括注这一种形式；「本地限定句」是新写的句子，要走 `new`。

不允许（都算改写，要改就写 `replace`）：加粗与斜体的增删、标点（含 em dash 与引号样式）、大小写、语序、同义替换、把表格行改写成触发行、句首的连接词（例如去掉「First」「Then」）。

句子的顺序：同一条 `move` 的源句在目标里必须保持相对顺序（`difflib.SequenceMatcher` 对齐）。理由：mattpocock 的理由句常紧跟在规则之后（`SKILL-SET-RULES.md` `## What skill text is for` 第 1 条「next to a rule, the reason for it」），调换顺序会把理由挂到别的规则上。这条不能一概而论，spec 确要重排时在那条 `move` 行尾加 `any-order`。

### 3.5 改名表怎样接入

- R18 第 17 节 D9 说 MMW 自有的技能、reference、脚本按你过目的改名表（`R19-naming-table.md`）改名，改名与搬家在同一张票里做。本轮检查时 `R19` 与 `R20` 两份文件都还不存在（`ls docs/research/workflow-compare/reports/`，已核实），所以下面的接口按 D9 的描述设计，列名是推断。
- **机器可读的改名表**：R19 定稿时同时产出 `docs/specs/<effort>/renames.tsv`，放在 spec 目录，因为它是这次改造的决定记录，不是 MMW 的常设文件（全局规则 13：只有记录决定或变化的文件可以写历史）。三列：`kind`、`old`、`new`。
- **`kind` 决定在哪里替换**（只在这些位置替换，普通英文词不动）：

  | kind | 替换位置 | 例 |
  |---|---|---|
  | `skill` | 行内代码里的技能名、「the `X` skill」、`/X`、路径段 `skills/X/`、frontmatter `name` | `dispatch` 解散后的指向 |
  | `path` | 解析后的仓库路径（第 3.4 节第 2 条） | `dispatch/references/night.md` → `mmw/playbooks/run-a-night.md` |
  | `heading` | 标题单元，以及行内代码或引号里写出的 `## <标题>` | 小节改名 |
  | `title` | 粗体步骤标题、`mmw <slug>#<title>` 指针 | 步骤改名 |
  | `token` | 行内代码与围栏代码块里的完整记号（前后不接字母、数字、`_`、`-`） | `verify-ticket.py` → `ticket.py` |

- **每张票只抄入本票执行的行**，写成清单里的 `rename` 行。不直接全局套用整张表：R18 第 2.4 节要求每一批的文字只点名当时已经存在的组件；全局套用会让 B1 搬的句子提前写上 B2 才建的脚本名（例如 `ticket.py`），反而违背 R18。
- **防止清单与改名表漂开**：切票会话跑 `check_verbatim_moves.py --lint-drafts <dir> --renames-table docs/specs/<effort>/renames.tsv`，清单里每一行 `rename` 都必须在表里有同样的一行，否则报 `RENAME-NOT-IN-TABLE`。
- **漏改会被抓到**：源句按清单改名后才与目标比，目标若还写旧名，就是 `CHANGED`，逐词差异里看得到旧名。上游 mattpocock 与 pstack 的技能名与文件名不进改名表（用户要求第 2 条），所以 `copy` 自上游的句子不会被改名。

### 3.6 输出与退出码

沿用 `mmw-v2/tests/lib/` 现有检查的形式（逐行 `path:line: …`），另按 `SKILL-SET-RULES.md` `### Refusals and output an agent reads` 第 2 条「Hosts cut long output before the agent sees it, so the next step sits in the first lines」把汇总与下一步放在最前。

- **退出 0**：打印一行，只有通过时才出现，供 `EXPECT:` 匹配：

  ```
  VERBATIM OK 5 moves, 1 copy: 143 units carried (6 path, 4 rename, 3 citation, 2 title), 2 replaced, 4 new, 3 dropped; untouched text: 4 files, 0 changes
  ```

  计数让评审一眼看出这次比了多少，也让「什么都没比」无处藏身。

- **退出 1**：有发现，或清单解析后一个单元都没有比（`VERBATIM FAIL checked nothing`，依据 `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条「A check that could verify nothing says so instead of reading like a pass」）。前三行固定：

  ```
  VERBATIM FAIL 2 changed, 1 deleted, 1 added
  Next: put each sentence below back to its source wording. If the wording cannot stand, keep it and open a `decision` sub-issue: the ticket's text is the spec's decision.
  Why: this ticket moves text verbatim; only the rewrites its ## Moves lists may differ from the source.
  mmw-v2/skills/mmw/playbooks/work-a-ticket.md:14: CHANGED from mmw-v2/upstream/skills/engineering/implement/SKILL.md:12 @68d90576
    - On `NOT_READY`, stop: the reason is already on the ticket.
    + On `NOT_READY`, stop.
  ```

  发现种类：`CHANGED`、`DELETED`、`ADDED`、`MISPLACED`、`OUT-OF-ORDER`、`NOT-REMOVED`、`UNTOUCHED-CHANGED`、`MISSING-NEW`（带整句的 `new` 没出现）。超过 40 条时只印前 40 条，末行写总数与 `--all`。
  - `Next:` 行里的 `decision` 子票是 worker 无人时的现有出口（今天是 `verify-ticket.py <n> --sub-issue decision`，R18 第 2.2 节 `## Autonomy` 把它定为 worker 的出路）。

- **退出 2**：什么都没能判定，原因写一行，不装作失败或通过：清单格式错、`from` 提交不存在、锚点找不到或匹配两处、`replace` 的旧串不在源范围里（`STALE`）、`gh` 读不到票。与 `check_own_skill_frontmatter.py` 的退出 2（「nothing could be checked」）同义。

- **`--lint-drafts <dir> [--renames-table <tsv>]`**（切票会话用，票发出之前）：对目录里每份草稿（`to-tickets` 第 7 步的草稿格式，`SKILL.md` 第 145 行）解析 `## Moves`，只查清单本身：每个锚点在 `from` 上恰好解析一次；每个 `replace` 的旧串在范围里恰好一次；同一批里两张票的源范围不重叠、目标位置不重复（第 3.8 节第 2 条）；`rename` 行都在改名表里。这是把第 3.8 节的切票规则变成检查，让清单的错在白天就暴露，而不是夜里 worker 跑判据时才暴露。

### 3.7 放在哪：`mmw-v2/tests/lib/`，不是 `mmw/scripts/`

- `mmw-v2/tests/AGENTS.md` 开头：`tests/` 「exists only in a checkout and is never symlinked into a host」。`CODING_STANDARDS.md` `## Skills and scripts` 第 1 条：技能目录「holds only what the agent holding the skill reads or runs」。消费仓库的 agent 不会搬 MMW 自己的技能文字，装到每个宿主上只是负担。
- R18 第 1.1 节把 `mmw/scripts/` 定为流水线状态脚本（只被 playbook 步骤、mode 触发行、hook 调用），文字检查不属于这一类；R18 第 7.5 节把 `check_wiring.py` 也放在 `tests/lib/`，两者同处。
- 已安装 checkout 是完整 checkout（根 `AGENTS.md` `## Key Conventions` 第 2 条），所以 `install.sh --check` 以后需要时也能从那里调用。
- 后果：P11 **Authoring or modifying a skill** 是装到所有仓库的 playbook，不能写一条只在本仓库有效的路径。本仓库切「搬文字的票」的步骤由 B1 决定放在哪（私有 playbook 或 `to-tickets` 分叉后的一份 reference）；B0 只提供脚本，清单格式的唯一出处是脚本头注释与 `--help`（`SKILL-SET-RULES.md` `### Scripts and judgement` 第 1 条：完整参数表留在脚本旁）。

### 3.8 怎样进票的 `CHECK:`

每张搬文字的票（B0 里补四处断点的票、B1、B2 的每张批次票，以后每次「Import a component」）加两条判据，写法照 `to-tickets` 第 4 步的四行格式：

```
- [ ] AC7: 本票搬的每一句逐字到位，本票新增与删去的每一句都列在 `## Moves` 里
  CHECK: python3 mmw-v2/tests/lib/check_verbatim_moves.py --ticket "$MMW_TICKET"
  EXPECT: /^VERBATIM OK \d+ /m
  EVIDENCE: pending
- [ ] AC8: 本票写的每个组件文件合它那一类的骨架
  CHECK: python3 mmw-v2/tests/lib/check_component_skeletons.py mmw-v2/skills/mmw/playbooks/work-a-ticket.md mmw-v2/skills/verify-ticket/SKILL.md
  EXPECT: /^SKELETONS OK \d+ files?/m
  EVIDENCE: pending
```

- **`EXPECT:` 是只在通过时才打印的整行开头**，合 `to-tickets` 第 84 行「a success-only marker」，也不在 `gate-lint.mjs` 的 `WEAK_EXPECT` 词表里（`ok`、`passed`、`done` 等，已核实）。两个标记 `VERBATIM OK`、`SKELETONS OK` 与 `STORY OK` 同形；B0 建 `anchors.py` 时一并登记为成功标记（R18 第 7.2 节，W5）。
- **`CHECK:` 里写仓库路径是允许的**：`SKILL-SET-RULES.md` `### Paths and host neutrality` 第 2 条禁的是给 oracle 写路径（oracle 由 `verify-ticket.py` 放上 `PATH`）；本仓库的票一直写仓库内测试的路径，例如 #589 AC5 的 `mmw-v2/tests/board/tasks.test.mjs`（已核实）。
- **切票规则（为了在收尾复核时仍然成立）**：
  1. 清单写在切票会话里，你在场时定稿；worker 不改清单。
  2. 同一批里，一个源范围只出现在一张票的清单里，一个目标位置（一节或一步）也只出现在一张票的清单里。理由：`to-tickets` 第 90 行说，一条判据若点名了后面的票会改的东西，就由那张票的工作来决定它；收尾复核会在 base 分支上重跑整批判据（第 88 行）。目标位置只有一个写者，Q1、Q2 在收尾复核时仍然只看到本票的文字。这与 `to-tickets` 第 5 步「no two tickets that can run at the same time write the same file」同一个道理，只是粒度到小节。`--lint-drafts` 检查这一条。
  3. `from` 取切票时 base 分支的 `HEAD`。同一批的票在同一次切票里写，源范围又互不重叠，所以前面的票落地不会改动后面的票要读的源范围。
- **B0 里补断点的票**（R18 第 10 节 B0：`night.md` 与脚本文字上的四处）也改技能文字，它们应被本文的逐字检查票阻塞，并带只有 `new` 行的清单：新写的句子在切票时定稿。

### 3.9 怎样证明它自己会失败（负控）

依据：`SKILL-SET-RULES.md` `### Scripts and judgement` 第 4 条「A check or completion criterion that cannot fail proves nothing」；R18 第 5.2 节 **principle-silence-is-never-a-pass** 的「新建的检查先证明它会失败」。

1. **每种发现一份夹具**：测试在 `mktemp -d` 里建一个临时 git 仓库，提交源文件，写目标文件与清单，断言退出码与发现种类（`TESTING.md` `## What a test proves`：断言退出码与程序读的输出记号，不断言措辞）。`CHANGED`、`DELETED`、`ADDED`、`MISPLACED`、`OUT-OF-ORDER`、`NOT-REMOVED`、`UNTOUCHED-CHANGED`、`MISSING-NEW`、`STALE`（退出 2）、`checked nothing`（退出 1）各一份；允许的五类改写各一份必须通过的夹具（拆段成步骤、标题改粗体标题、链接改代码路径、清单列出的改名、原则括注），以及对应的反例（没列出的改名、括注点名一个不存在的原则、把路径改到另一个存在的文件）必须失败。
2. **在真实文字上做变异**：把一份真实技能文件（`mmw-v2/skills/advisor/SKILL.md`，它有 frontmatter、列表、行内代码、链接）原样 `copy` 到临时仓库，检查必须通过；再用固定种子做 30 次单处变异，每次只改一处，每次都必须非 0 退出并报出被改的那一行。变异种类：换一个词、删一个词、加一个「not」、改一个数字、改一个行内代码里的名字、删一整句、交换相邻两句、加粗一个词、改一个标点。这一条证明检查在真实的 Markdown 形态上不是盲的；任何一次变异漏报，测试就失败。
3. **每次运行自带的非空检查**：清单解析后一个单元都没比时退出 1（第 3.6 节），所以一条写错锚点、实际什么都没比的判据不会显示为通过。

### 3.10 它不管什么

- 句子搬到指定位置后讲不讲得通、理由是否还挨着它的规则（`any-order` 以外的顺序检查只覆盖同一条 `move` 之内）：评审的 Spec axis，加 `SKILL-SET-RULES.md` `## Verifying` 的「a fresh agent given only the trigger and a real job」实跑。
- `new` 句子写得好不好：R20 写作规范与评审。
- 脚本里的文字（拒绝文字、启动提示词、唤醒行）、JSON（`roles.json`）：不是 Markdown，不在范围内；它们的锚点由 `check_wiring.py` 查（R18 第 7.5 节第 1、8 类）。
- 整目录平移的脚本：由 git 的改名检测与各套件的测试保证。

---

## 4. 结构 lint `check_component_skeletons.py`

### 4.1 怎样认出一个文件是哪类组件

按路径，加 `imports.tsv` 的登记（R18 第 1.1 节目录树、第 8.2 节导入类型）：

| 类型 | 路径 | 查不查 |
|---|---|---|
| mode | `mmw-v2/skills/mmw/SKILL.md` | 查 |
| MMW 自写 playbook | `mmw-v2/skills/mmw/playbooks/*.md` 中未登记为导入的；`.mmw/playbooks/*.md`（`INDEX.md` 除外） | 查 |
| 导入的 playbook | `imports.tsv` 类型为 `playbook` 的行 | 只查首行 `### <Name>` 与末行 `**Reply:**`（R18 第 7.5 节第 7 类原文）；`imports.tsv` 标为例外的（`opening-a-pr.md`）连这也不查 |
| 原则 | `mmw-v2/skills/mmw/principles/principle-*.md` | 查（导入的与自写的同一格式，R18 第 5.1 节） |
| MMW 自有能力技能 | `mmw-v2/skills/<name>/SKILL.md` 与它的 `references/**/*.md`（`mmw` 除外） | 查 |
| 上游子树里的技能 | `mmw-v2/upstream*/**` | 不查：`SKILL-SET-RULES.md` `### Upstream skills` 第 4 条「Checks on style … apply to the set's own text」；本仓在上游文字里加的句子由 `check_wiring.py` 第 3 类的「上游差异」一项查（R18 第 4.3 节） |
| mode 的 reference | `mmw-v2/skills/mmw/references/**` | 只查第 4.2 节表里标「全部自写文字」的规则 |

### 4.2 按类型的规则表

规则编号是稳定 id，写在输出里；删掉的规则留空号不复用（照 pstack `unslop` 的「Rule numbers are stable ids that other skills cite」，L7 A.3 规则目录型）。规则表作为数据写在脚本开头，每条带出处。

| id | 适用 | 规则 | 出处 |
|---|---|---|---|
| `mode-name` | mode | frontmatter `name: mmw`，没有 `disable-model-invocation` | R18 第 2.1 节 |
| `mode-sections` | mode | H2 依次为 `## Non-negotiables`、`## Principles`、`## Autonomy`、`## Re-entry`、`## Subagents`、`## Writing the reply`、可选 `## Comments`、`## Playbooks`；之前最多一个 H1。用 MD043 的记法写成序列，`## Comments` 记为 `?` | R18 第 1.1 节目录树注释与第 2.2 节；L7 A.1「正文模板」 |
| `mode-imported-triggers` | mode | `### Imported triggers` 只能在 `## Non-negotiables` 之下 | R18 第 2.2 节、第 8.2 节 |
| `mode-principle-line` | mode | `## Principles` 下的条目形如 `- **<Title>** (**principle-<slug>**). <文字>.` | R18 第 2.2 节 `## Principles` 第 3 条 |
| `mode-route-line` | mode | `## Playbooks` 下的路由行形如 `- **<Name>.** … \`playbooks/<file>.md\`.`（以反引号文件名收尾） | L7 A.1；R18 第 2.2 节 `## Playbooks` 第 4 条 |
| `playbook-title` | 自写与导入 playbook | 首个非空行是 `### <Name>`；没有 frontmatter，没有 H1、H2 | L7 A.2「frontmatter 与布局」 |
| `playbook-owner-line` | 自写 playbook | 有所有权行时，它是标题后的第一段，形如 `**You own …**`；不要求一定有 | R18 第 3.2 节「所有权行只在有出处时写」 |
| `playbook-steps` | 自写 playbook | 有任何 `####` 小节时，恰好一个是 `#### Steps`，步骤是它下面的第一个有序列表；没有 `####` 时，步骤是第一个顶层有序列表；编号从 1 连续 | R18 第 3.2 节；L7 A.2 `orchestrate.md` 的 `#### Steps` |
| `step-title` | 自写 playbook | 每步以 `N. **<Title>.**` 开头；同一文件里步骤标题不重复（它们是锚点） | R18 第 1.3 节「步骤」行 |
| `step-done-when` | 自写 playbook | 每步有一句以 `Done when` 开头 | `SKILL-SET-RULES.md` `### Rules and completion criteria`；R18 第 3.2 节骨架「门槛与 Done when」 |
| `step-names-component` | 自写 playbook | 每步至少点名一个组件（`skills.txt` 里的技能名、`**principle-<slug>**`、playbook 的显示名、`mmw/scripts/` 里的脚本命令、`references/…` 路径），或写 `(judgement)` | R18 第 3.2 节规则；第 7.5 节第 7 类 |
| `playbook-reply` | 自写与导入 playbook | 最后一个非空行以 `**Reply:**` 开头 | L7 A.2 第 6 条 |
| `principle-frontmatter` | 原则 | frontmatter 只有 `name`、`description`；`name` 等于文件名去掉 `.md`，以 `principle-` 开头 | R18 第 1.3 节「原则」行、第 5.1 节「格式」 |
| `principle-applies` | 原则 | `description` 第一句以 `Apply ` 开头（when、to、after、before、during、whenever），至少两句。mode 索引的「何时适用」取这第一句，所以它必须是触发情境 | L7 A.4 frontmatter；R18 第 2.2 节 `## Principles` 第 3 条 |
| `principle-body` | 原则 | 正文以 `# <Title>` 开头；小节用段首粗体标签 `**<Label>:**`，不用 `##`（登记的例外：pstack `principle-prove-it-works` 的 `## Script the check when you can`）；`**Why:**` 最多一个。**不要求有 `**Why:**`** | L7 A.4「正文模板」；R18 第 5.1 节「原文没有理由的不写 `**Why:**`（pstack 23 条里也只有 16 条有）」 |
| `principle-direction` | 原则 | 不出现 playbook 的文件名或显示名、`scripts/`、`mmw#`、`mmw <slug>#` | L7 B.2 硬规律 1；R18 第 5.1 节「方向」 |
| `capability-next-step` | 能力技能及其 reference | 不出现「下一步」「谁调用我」句型：`## Next`、`## Reached from here` 标题；「return to」后接技能名；「hand (it) over/on to」后接技能名；「goes through the `X` skill first」；「are steps of the `X` skill」；「next step」与技能名同句 | R18 第 4.5 节第 2 条；句型取自 R14 第 2 节「下一步句的完整名单」 |
| `capability-playbook-name` | 能力技能及其 reference | 不出现 playbook 的文件名、显示名、`playbooks/`、`mmw <slug>#` 指针。角色名（worker、reviewer）作为领域词可以出现 | R18 第 4.5 节第 2 条 |
| `numbered-cross-reference` | 全部自写文字 | 不出现跨文件的按编号引用：`step \d+` 前接别的文件或技能名（`` `SKILL.md` step 4 ``、「the `X` skill's step 2」）、`closing step \d`、`Phase [A-Z]`；同一文件内的编号引用不算 | R18 第 7.5 节第 4 类；`SKILL-SET-RULES.md` `### Vocabulary` 第 8 条「by title rather than by number」 |
| `host-name` | 全部自写文字 | 行内代码与链接目标之外，不出现宿主名、工具名、runner 名：`Claude Code`、`Codex`、`Grok`、`Cursor`、`Orca`、`herdr`、`Paseo`、`the Skill tool`、`the Task tool`（大小写不敏感，整词） | `SKILL-SET-RULES.md` `### Paths and host neutrality` 末段「The check is a `grep` of every `SKILL.md`, description and reference … for …」。这条检查今天只写在文字里，没有脚本实现（本轮在 `mmw-v2/tests/` 里 grep 不到，已核实）。与那份名单的差别：不查单独的 `claude` 与 `pi`，也不查行内代码。本轮按那份名单整词 grep `mmw-v2/skills/`，去掉「Claude Design」后仍有 18 行命中，全是 `CLAUDE.md` 这类文件名、`claude-design` 这类路径和 Claude Design 的功能说明（「comments sent to Claude」）；按本行的写法只剩 1 行（第 4.3 节）（已核实） |
| `description-trigger` | mode 与能力技能 | `description` 有一句以 `Use ` 开头；另外最多一句以 `Not for` 或 `Do not use` 开头的非触发句；总共不超过 3 句、1024 字符 | `SKILL-SET-RULES.md` `### Descriptions` 第 1 条；上游 `wizard`、`prototype` 的写法（同文件 `## Upstream examples` 表「Descriptions」行）；1024 取自 Agent Skills 规格与 `skills-ref` 的 `MAX_DESCRIPTION_LENGTH` |
| `description-content` | mode 与能力技能 | `description` 不点名别的技能（反引号技能名或「the `X` skill」）、不写技能内部路径（`references/`、`scripts/`、`SKILL.md`）、不写 playbook 名或步骤编号 | `SKILL-SET-RULES.md` `### Descriptions` 第 1 条「Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body」 |
| `skill-name` | 能力技能 | frontmatter `name` 等于目录名，≤64 字符 | Agent Skills 规格；`skills-ref` `_validate_name` |

几条取舍：

- **`description-content` 不禁路径本身。** 今天 `ui-acceptance` 的 description「Use when filling `.mmw/target.json`」把一个文件当触发分支，这是触发，不是路由；所以只禁技能内部路径。
- **不查能力技能的正文形态。** L7 A.3 列出 pstack 能力技能有八种形态，收尾写法「没有统一」；MMW 的能力技能多是 mattpocock 的 `## Process` 加 `### N. <Title>` 加 `Done when`。强求统一形态就等于改写 mattpocock 的文字，与 D9 相反。R18 第 4.5 节第 1 条「以交付物结尾」也不做成机器规则：收尾写法有七种，判断它是不是在说「交回什么」要读懂，交给评审的 Standards axis。
- **`step-done-when` 只对 MMW 自写 playbook。** pstack playbook 没有 `Done when` 行（`skills/poteto-mode/playbooks/bug-fix.md` 全文，已核实），导入的保持原文；mattpocock 上游原文也没有（squash `5b1a4c51` 的 `to-tickets` 原文只有标题，已核实），`Done when` 是本仓自己的写法。
- **与 `SKILL-SET-RULES.md` 的冲突要在 B1 解决。** 它的 `### Hand-offs` 第 5 条（第 92 行）「Each skill ends by naming what comes next, or the caller it returns to」与 `capability-next-step` 正好相反。R14 T38 与 R18 第 4.5 节已定下「下一步住在 playbook」；B1 把这份文件搬进 `mmw/references/skill-set-rules.md` 时要改这一条，否则文字与检查互相矛盾。

### 4.3 在今天的树上会报什么

本轮用一段临时脚本（不在仓库里）按上表的几条正则扫了 `mmw-v2/skills/` 下的 `.md`，结果如下（按行号记，推断：正式实现的正则会有出入，B0 票以实现的输出为准）：

| 规则 | 命中 | 位置 | R18 是否已排期 |
|---|---|---|---|
| `capability-next-step`（标题） | 4 | `design-pages/references/edit-pages.md:31`、`design-pages/references/pull.md:35`、`verify-ticket/SKILL.md:23`、`write-screen-contract/SKILL.md:113` | 是（第 4.1 节，B1、B2） |
| `capability-next-step`（return to） | 3 | `design-pages/references/pull.md:37`、`retro/SKILL.md:186`、`write-screen-contract/SKILL.md:115` | 是 |
| `capability-next-step`（steps of） | 1 | `verify-ticket/SKILL.md:16` | 是（B2） |
| `numbered-cross-reference` | 6 | `code-checkers/references/git-hooks.md:36`、`code-checkers/references/python.md:46`（都是「`SKILL.md` step 4」）、`design-pages/SKILL.md:25`（「`UI.md` step 6」）、`exe-release/references/driving.md:3`、`:44`、`exe-release/references/key.md:225` | 只有 `design-pages:25` 已排期（第 4.1 节）；**其余 5 处 R18 没有排期**，spec 要给它们一个批次 |
| `host-name` | 1 | `design-pages/references/edit-pages.md:27`「Handoff to Claude Code」 | 不用改：这是 Claude Design 按钮上的字，登记为永久例外 |
| `description-trigger` | 1 | `dispatch/SKILL.md`：没有 `Use ` 句 | 是（B2 解散） |
| `description-content` | 1 | `retro/SKILL.md`：点名 `dispatch` 技能 | 是（第 4.1 节，时机进 P12） |

- R14 第 2 节的 17 句名单里，8 句在 `mmw-v2/skills/` 的自有技能里，9 句在上游子树里。上表 `capability-next-step` 的 8 行覆盖自有的 6 句（`edit-pages.md` 的 `## Next`、`pull.md` 的 `## Reached from here`、`write-screen-contract` 的 `## Next`、`retro` 第 186 行、`verify-ticket` 第 16 行与它的 `## Reached from here`），另外 2 行（`pull.md:37`、`write-screen-contract/SKILL.md:115`）是这些小节里的「return to」句。漏掉的 2 句是 `ui-acceptance` 表第 1 行与 `dispatch` 表第 1 行：它们是「时刻表」里指向别的技能的 reference 的一行，与合法的技能交接（`SKILL-SET-RULES.md` `### Hand-offs`「A file in another skill is named by skill and file」）句型相同，正则区分不开，留给评审。上游子树里的 9 句由 `check_wiring.py` 第 3 类的上游差异一项负责。
- 这一节同时是正控（第 4.7 节）：B0 票要求实现在今天的树上报出这 8 行。

### 4.4 与 `check_wiring.py` 的关系：分开，共用 `skill_text.py`

**决定。** 两个脚本，一个共用模块。按「修复落在哪」划界：

| | 结构 lint `check_component_skeletons.py` | 连线检查 `check_wiring.py`（R18 第 7.5 节） |
|---|---|---|
| 问什么 | 这个文件按它的组件类型，骨架齐不齐、有没有禁用句型 | 文件里写出的名字，能不能通到一个存在的、方向允许的东西 |
| 修复在哪 | 同一个文件 | 常在另一个文件（被指向的 playbook、`roles.json`、`skills.txt`） |
| 从 R18 第 7.5 节接过来 | 第 7 类中逐文件的部分（`### <Name>`、粗体步骤、`**Reply:**`、每步点名组件）；第 3 类中的句型部分（能力技能的「下一步」「谁调用我」、原则的方向）；第 4 类（不按编号） | 保留第 1、2、5、6、8–12 类；第 3 类的脚本部分（能力技能脚本不调 mode 命令、锚点只来自 `anchors.py`、上游差异只有两类）；第 7 类中跨文件的部分（路由表每份 playbook 恰好一行、`INDEX.md` 同理） |
| 何时失败 | B0 起，靠例外表过渡（第 4.5 节） | 按 R18 第 7.5 节各类的批次 |

**理由。**

1. 失败的读者不同：结构 lint 的失败由写那个文件的 worker 在本文件里修；连线失败常要去改另一张票拥有的文件（`to-tickets` 的 **Owns**），报告要说清两端。
2. 落地时间不同：结构 lint 必须在任何搬文字的票之前就能失败（用户要求），而 `check_wiring.py` 大多数类别要等 mode、playbook 建成才有对象。合在一个脚本里，同一个文件要同时容纳「B0 就失败」与「B2 末才失败」两种开关。
3. 两者与逐字检查都要同一套 Markdown 切分、组件归类与清单（技能名、playbook 名、原则 slug），放进 `skill_text.py` 共用，避免三份各自解析、各自出错。

**放弃的备选。** 把结构规则并进 `check_wiring.py` 作为新的几类。省一个入口，但上面第 2 条的开关表会变复杂，而且 `check_wiring.py` 在 B0 的范围已经很大（R18 第 10 节 B0 行）。

**建议 `check_wiring.py` 也用例外表过渡**，代替「每类在某批之前只报告」的开关：新违规立刻失败，旧违规逐条到期。这是给 R18 第 7.5 节的建议，是否采用由写 B0 spec 时定。

### 4.5 例外表：从 B0 起就失败的办法

- 文件 `mmw-v2/tests/lib/skeleton-exceptions.tsv`，五列：`path`、`rule`、`excerpt`（被报那一行里的一段原文，用来匹配，不用行号，所以行号挪动不会让它失效）、`until`（`B1`、`B2`… 或 `permanent`）、`reason`。
- 判定：
  - 发现不在表里 → 失败。
  - 表里某行已匹配不到任何发现（文字已改好）→ 打印一行 `WARN stale exception`，不失败。理由：让「还债」的票不必同时改这张共享表，避免同批几张票都去写它（`to-tickets` 第 5 步：共享的登记文件会让并行的票在合并时冲突）；每批最后一张票或批次验收时清理。
  - `--batch Bn`：`until` 不晚于 `Bn` 且仍匹配到发现的行 → 失败。这就是 R18 第 10 节验收条件第 2 条「第 3 类的『只报告』输出里，属于本批文件的条目为零」的机器形式。
- `permanent` 行必须有 `reason`，评审读得到。worker 不应为了让自己的判据通过去加例外：它不在票的 **Owns** 里时，`Outside Owns:` 一行会报出来；失败输出的 `Next:` 行也写明「规则确实不适用时开 `decision` 子票，不改例外表」。
- 这张表钉住的是今天文字的片段，与 `TESTING.md` `## What a test proves` 反对的「钉住措辞」不是一回事：它不是测试，而是一张会缩短的待办表，文字改好之后行就过期、被删。

### 4.6 输出、放在哪、进 `CHECK:`

- 两种运行方式：
  - 不带参数：查整棵树，由预检入口在每个套件开头跑（第 5 节第 1 张票）。
  - 带文件参数：只查这些文件，用在票的 `CHECK:` 里（第 3.8 节 AC8）。
- 输出与逐字检查同形。退出 0 印一行 `SKELETONS OK <n> files (<m> exceptions in use, <k> stale)`；退出 1 前三行是汇总、`Next:`、`Why:`，然后每条 `path:line: <rule-id> <说明>`；退出 2 表示没能检查（例如 `skills.txt` 读不到）。查了 0 个文件也是退出 1。
- 放在 `mmw-v2/tests/lib/`，理由同第 3.7 节。

### 4.7 负控与正控

1. **每条规则一份必须失败的夹具**，放在 `mmw-v2/tests/text-integrity/fixtures/skeletons/`，每份只违反一条，测试断言报出的恰好是那条的 id（R18 第 7.5 节「为每一类放一个必须失败的反例」）。
2. **每种组件类型一份合格样本必须通过**：mode、自写 playbook（短的与带 `#### Steps` 的长的各一）、原则（有 `**Why:**` 的与没有的各一）、能力技能。
3. **今天的树上的正控**：带 `--no-exceptions` 运行时必须报出第 4.3 节 `capability-next-step` 那 8 行。这是一次性的判据（写在 B0 票里），不写成常驻测试，因为那 8 行会在 B1、B2 被搬走，常驻测试会随文字过期（`TESTING.md` `## What a test proves`）。

---

## 5. B0 票草案

三张票，按 `to-tickets` 的 `<issue-template>` 写（`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 162–204 行）。`#<spec>` 是 B0 spec 的编号，写 spec 时填；Implementation Decisions 的节号同理。判据的 `CHECK:` 形式照本仓库先例：套件 `run.sh -k <用例名> 2>&1 | tail -1`，`EXPECT: /^all passed$/m`（#493 各条，已核实；`run.sh` 只在全部通过时打印 `all passed`，见 `mmw-v2/tests/write-screen-contract/run.sh` 末尾）。

它们与 R18 B0 其余票的关系：
- 第 1 张是前置票：R18 的 `check_wiring.py` 票也要让每个套件先跑它（R18 第 7.5 节首句）；若没有这张票，两张 B0 票都要改同样 12 个 `run.sh`，按 `to-tickets` 第 5 步只能串行。
- B0 里改技能文字的票（补四处断点、`wayfinder` 第 5 步的过渡替换，R18 第 16 节）被第 2 张阻塞，并带只有 `new` 行的清单。

### 票 1：每个套件经一个预检入口跑仓库的文字检查

**Blocked by**：无。

**What to build**

1. 新建 `mmw-v2/tests/lib/preflight.sh`：按今天的顺序与退出行为跑 `check_module_paths.py`、`check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py`（后者经 `uv run`），任何一个非 0 就以非 0 退出。以后加一道检查只改这一个文件。AC1、AC2 判定。
2. 现有 12 个套件的 `run.sh` 把今天各自抄的三行（例 `mmw-v2/tests/retro/run.sh` 第 6–8 行）换成一行调用它。AC1 判定。
3. 新建套件 `mmw-v2/tests/text-integrity/`：`run.sh`（开头同样调用 `preflight.sh`；照 `write-screen-contract/run.sh` 的写法，经 `mmw-v2/tests/lib/run_unittests.py` 跑 `test_*.py`，支持 `-k`，全部通过才打印 `all passed`）与第一份测试 `test_preflight.py`。票 2、票 3 只往这里加测试文件，不改 `run.sh`。AC1、AC2 判定。
4. 文档：根 `AGENTS.md` `## Commands` 里「twelve of them」改为十三个并加上 `text-integrity`，「Every `run.sh` first runs …」一句改为经 `preflight.sh`；`mmw-v2/tests/AGENTS.md` `## Key Conventions` 第 2 条说明 `lib/` 里多了预检入口。由评审的 Spec axis 判，不设判据。

**Read first**

- `mmw-v2/tests/AGENTS.md`：套件、`lib/` 与隔离的约定。
- `TESTING.md` `## What a test proves`：断言退出码与记号，不断言措辞。
- 本文第 5 节：三张票的分工。

**Seam**

`mmw-v2/tests/text-integrity/`（新套件，Python `unittest` 经 `run_unittests.py`）。预检的反例测试在 `mktemp -d` 里复制一份最小的 `mmw-v2/` 树（`tests/lib/` 加一个点名不存在模块的脚本），在那份副本上跑 `preflight.sh`，因为三个检查都从自己的位置找 `mmw-v2/` 根。先例：`mmw-v2/tests/write-screen-contract/run.sh`。

**Owns**

- mmw-v2/tests/lib/preflight.sh (new)
- mmw-v2/tests/*/run.sh
- mmw-v2/tests/text-integrity/** (new)
- mmw-v2/tests/AGENTS.md
- AGENTS.md

**Acceptance criteria**

```
- [ ] AC1: 13 个套件（现有 12 个加 text-integrity）的 run.sh 都调用 preflight.sh，且没有一个还直接调用 lib/check_*.py
  CHECK: test -z "$(grep -L 'lib/preflight.sh' mmw-v2/tests/*/run.sh)" && test -z "$(grep -l 'lib/check_' mmw-v2/tests/*/run.sh)" && echo "PREFLIGHT-IN-ALL $(ls mmw-v2/tests/*/run.sh | wc -l | tr -d ' ')"
  EXPECT: /^PREFLIGHT-IN-ALL 13$/m
  EVIDENCE: pending
- [ ] AC2: 预检里任何一道检查失败时，preflight.sh 以非 0 退出
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_preflight_stops_on_a_failing_check 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
```

### 票 2：逐字搬运检查

**Blocked by**：票 1。

**What to build**

1. `mmw-v2/tests/lib/skill_text.py`：把 Markdown 切成第 3.3 节的单元（句子、标题、代码块、表格单元格、frontmatter 字段），按第 3.4 节规范化路径与链接，按第 4.1 节给文件归类，读技能名清单（`skills.txt`）。只用标准库。票 3 与以后的 `check_wiring.py` 共用它。AC1–AC4 经它判定。
2. `mmw-v2/tests/lib/check_verbatim_moves.py`：
   - 从 `--ticket <n>`（经 `gh issue view`）或 `--manifest <file>` 读 `## Moves`，指令与位置写法按第 3.2 节；
   - 回答 Q1、Q2、Q3（第 3.1 节）；
   - 输出与退出码按第 3.6 节，成功行以 `VERBATIM OK` 开头。
   - 清单格式写在脚本头注释与 `--help` 里，那是它的唯一出处。
   - AC1–AC8 判定。
3. `--lint-drafts <dir> [--renames-table <tsv>]`，查清单本身（第 3.6 节末条）。AC9 判定。
4. 在真实文字上做变异的负控（第 3.9 节第 2 条）。AC10 判定。
5. `docs/contexts/tickets/CONTEXT.md` 加 **`## Moves`** 词条（票上的搬运清单；`_Home_` 是这个脚本），`SKILL-SET-RULES.md` `### Vocabulary`「The glossary is complete」要求它。由评审的 Spec axis 判，不设判据。

**Read first**

- 本文第 3 节：baseline（检查的行为定义）。
- `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `## Editing`：搬运要逐字的规则原文。
- `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 4 步：判据写法；第 7 步：草稿目录格式。
- `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 第 1860–1880 行：`CHECK:` 运行时的 `MMW_TICKET`、`MMW_BASE_REF`。
- `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条：拒绝与失败输出的三部分。

**Seam**

`mmw-v2/tests/text-integrity/test_verbatim_moves.py`。每个用例在 `mktemp -d` 里 `git init` 一个临时仓库，提交源文件得到 `from` 提交，写目标文件与 `--manifest` 清单，断言退出码与发现种类记号。先例：`mmw-v2/tests/write-screen-contract/` 的夹具式用例。

**Owns**

- mmw-v2/tests/lib/skill_text.py (new)
- mmw-v2/tests/lib/check_verbatim_moves.py (new)
- mmw-v2/tests/text-integrity/test_verbatim_moves.py (new)
- mmw-v2/tests/text-integrity/fixtures/verbatim/** (new)
- docs/contexts/tickets/CONTEXT.md

**Acceptance criteria**

```
- [ ] AC1: 一节拆成几个带粗体标题的步骤、段内重新折行、列表符号与编号改变、标题改为粗体步骤标题时，检查通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_a_reflowed_move_is_verbatim 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: 搬过去的一句改了一个词时，报 CHANGED 并退出 1
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_one_changed_word_is_changed 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC3: 源范围里的一句没有到目标、也没有 drop 时报 DELETED；有 drop 时通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_a_missing_sentence_is_deleted_unless_dropped 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC4: 目标位置里一句没有来处、也不在 new 里时报 ADDED；在 new 里时通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_an_unlisted_sentence_is_added_unless_new 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC5: 句子搬到清单指定以外的目标时报 MISPLACED；同一条 move 内调换顺序时报 OUT-OF-ORDER，行尾有 any-order 时通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_placement_and_order 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC6: 分支上改了清单范围以外的一句技能文字时报 UNTOUCHED-CHANGED；HEAD 就是 base 时成功行写明 untouched text 没有检查
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_untouched_text 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC7: 路径改写成指向同一文件的另一种写法、清单列出的改名、括注点名一个存在的原则都通过；没列出的改名、括注点名不存在的原则、路径改指另一个存在的文件都报 CHANGED
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_mechanical_rewrites 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC8: 锚点找不到或匹配两处、replace 的旧串不在源范围里、from 提交不存在时退出 2；清单一个单元都没比时退出 1
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_nothing_checked_is_never_a_pass 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC9: --lint-drafts 报出两份草稿源范围重叠、目标位置重复、rename 行不在改名表里
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_lint_drafts 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC10: 在 mmw-v2/skills/advisor/SKILL.md 的副本上，原样 copy 通过，30 次固定种子的单处变异每一次都退出 1 并报出被改的行
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_every_seeded_mutation_of_real_text_is_reported 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
```

- AC10 在测试运行时读取真实文件，但它断言的是「每一次变异都被报出」，不是那份文件的措辞；`advisor/SKILL.md` 以后改了，测试照样成立。若 B2 删掉或改名这个文件，测试会失败，这时换一份文件即可。要避免这种耦合，也可以在票里改为读 `mmw-v2/tests/text-integrity/fixtures/verbatim/` 下提交的一份副本（推断：副本更稳，真实文件更能代表当前写法；由 worker 在 `Decisions I made on my own` 写明选了哪个）。

### 票 3：结构 lint 与例外表

**Blocked by**：票 1、票 2（用 `skill_text.py`，改 `preflight.sh`）。

**What to build**

1. `mmw-v2/tests/lib/check_component_skeletons.py`：按第 4.1 节归类，按第 4.2 节规则表逐文件检查；规则表作为数据写在脚本开头，每条带出处。不带参数查整棵树，带文件参数只查这些文件。输出与退出码按第 4.6 节，成功行以 `SKELETONS OK` 开头。AC1–AC3 判定。
2. `mmw-v2/tests/lib/skeleton-exceptions.tsv`：登记今天树上的全部发现（第 4.3 节是预估），每行写 `until`：R18 已排期的写对应批次；R18 没排期的 5 处 `numbered-cross-reference` 写 spec 定的批次；`edit-pages.md` 的「Handoff to Claude Code」写 `permanent`。支持 `--batch Bn`、`--no-exceptions`；过期的行只打印 `WARN`。AC4、AC5 判定。
3. `preflight.sh` 加一行跑它（不带参数）。AC6 判定。
4. `docs/contexts/toolbox/CONTEXT.md` 加 **skeleton lint** 与 **`skeleton-exceptions.tsv`** 词条。由评审的 Spec axis 判，不设判据。

**Read first**

- 本文第 4 节：baseline（规则表、例外表、与 `check_wiring.py` 的分工）。
- `docs/research/workflow-compare/reports/L7-pstack-component-contract.md` `### A.1 mode`、`### A.2 playbook`、`### A.4 原则`：各类的正文模板。
- `docs/research/workflow-compare/reports/R18-mmw-architecture-v2.md` 第 1.3、3.2、4.5、5.1、7.5 节。
- `docs/research/code-landing-refs/pstack/skills/poteto-mode/scripts/check-plan.mjs`：检查器持有字面的先例。

**Seam**

`mmw-v2/tests/text-integrity/test_component_skeletons.py`，夹具在 `mmw-v2/tests/text-integrity/fixtures/skeletons/`。用例把夹具放进 `mktemp -d` 里按第 4.1 节路径排好的最小树，用 `--root` 指向它（这个参数只供测试）。

**Owns**

- mmw-v2/tests/lib/check_component_skeletons.py (new)
- mmw-v2/tests/lib/skeleton-exceptions.tsv (new)
- mmw-v2/tests/lib/preflight.sh
- mmw-v2/tests/text-integrity/test_component_skeletons.py (new)
- mmw-v2/tests/text-integrity/fixtures/skeletons/** (new)
- docs/contexts/toolbox/CONTEXT.md

**Acceptance criteria**

````
- [ ] AC1: 第 4.2 节每条规则各有一份夹具，每份只报出那一条规则的 id 并退出 1
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_each_rule_fails_its_own_fixture 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: mode、短 playbook、带 #### Steps 的长 playbook、有 Why 与没有 Why 的原则、能力技能各一份合格样本都通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_well_formed_components_pass 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC3: 导入的 playbook 只查首行 ### 与末行 **Reply:**，没有粗体步骤标题也通过
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_imported_playbook_keeps_its_own_steps 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC4: 不在例外表里的发现失败；until 不晚于 --batch 所给批次且仍匹配的例外失败；已匹配不到的例外只打印 WARN
  CHECK: bash mmw-v2/tests/text-integrity/run.sh -k test_exceptions 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC5: 在今天的树上不用例外表运行时，报出 capability-next-step 的 8 行（R14 下一步句名单里自有技能的 6 句，及这些小节里的 2 行 return to）
  CHECK:
  ```
  out=$(python3 mmw-v2/tests/lib/check_component_skeletons.py --no-exceptions 2>&1)
  n=0
  for loc in verify-ticket/SKILL.md:16 verify-ticket/SKILL.md:23 write-screen-contract/SKILL.md:113 write-screen-contract/SKILL.md:115 retro/SKILL.md:186 design-pages/references/edit-pages.md:31 design-pages/references/pull.md:35 design-pages/references/pull.md:37; do
    printf '%s\n' "$out" | grep -q "^mmw-v2/skills/$loc: capability-next-step" && n=$((n+1))
  done
  test "$n" -eq 8 && echo FOUND-ALL-8
  ```
  EXPECT: /^FOUND-ALL-8$/m
  EVIDENCE: pending
- [ ] AC6: 预检入口在整棵树上通过（例外表生效）
  CHECK: bash mmw-v2/tests/lib/preflight.sh && python3 mmw-v2/tests/lib/check_component_skeletons.py --batch B0
  EXPECT: /^SKELETONS OK \d+ files/m
  EVIDENCE: pending
````

- AC5 用围栏里的多行命令（写法见 `mmw-v2/merge-notes/unlazy.md` `### scripts/lib/gates.mjs`：`CHECK:` 下紧跟的围栏代码块就是命令；`CHECK:` 同一行不能再写值，否则报 `has both a CHECK value and a fenced block`）。行号来自本轮的扫描；B0 同批里若有票改动这几个文件（R18 第 10 节 B0 行里没有），行号会动，那时改为只比路径与规则。
- AC6 是扫整棵树的判据，同批后面的票改文字可能让它变红，按 `to-tickets` 第 90 行，它放在本批最后落地的这张票上；这也是它该在的位置，因为它证明三张票合起来之后每个套件仍能开跑。

---

## 6. 本轮读了什么、没读什么

**读了**（全文或所需部分）：

- `R18-mmw-architecture-v2.md`：第 0、1、2、3.1–3.3 节中 P15–P18，第 4、5、7.1–7.6、10、16、17 节与审查记录。
- `L7-pstack-component-contract.md` A.0–A.5；`R13-pstack-design-essence.md` E4、E8；`R14-mmw-layer-mixing-inventory.md` 第 0、2 节。
- `SKILL-SET-RULES.md` 全文；`writing-for-agents/SKILL.md`、`SKILL-MECHANICS.md` 全文。
- `to-tickets/SKILL.md` 全文；`verify-ticket/SKILL.md`、`references/linting.md`；`verify-ticket.py` 第 436–470、694–719、1860–1880 行。
- `gate-lint.mjs` 规则部分、`lib/gates.mjs` 的 `parseRegex`；`merge-notes/unlazy.md` 前 80 行。
- `mmw-v2/tests/lib/` 全部五个文件；`mmw-v2/tests/AGENTS.md`；`TESTING.md`；`CODING_STANDARDS.md`；两个 `run.sh`。
- pstack `poteto-mode/SKILL.md` 的标题与第 1–8、37–45、115–125 行；`playbooks/bug-fix.md`、`authoring-a-skill.md`；`principle-attack-the-premise/SKILL.md`；`scripts/check-plan.mjs` 第 1–60 行。
- 上游 squash `5b1a4c51` 里的 `to-tickets`（只看标题与 `Done when`）与 `implement` 原文。
- 票 #589、#493 的判据写法。
- 第 2 节表里每个外部候选的一个实现文件。

**没读**：

- N1–N11 各份清点。本文只用到 R14 与 R18 已归纳的结论。
- `verify-ticket.py` 的其余部分：`--lint` 是否会对未知的 `## Moves` 小节报 WARN 没有核实（推断：它按固定小节名取内容，见第 441 行 `section()`，不列举全部小节）。
- `R19-naming-table.md`、`R20-writing-style-guide.md`、`docs/research/workflow-compare/exemplars/`：本轮检查时都还不存在，第 3.5 节的改名表列名因此是推断。
- `check_wiring.py`：尚未写，第 4.4 节的分工是对 R18 第 7.5 节文字的重新分配。

**推断清单**：

- 断句不准不会造成漏报（第 3.3 节），由比较的对称性推出，第 3.9 节第 2 条的变异测试实测。
- 第 4.3 节的命中数来自临时正则，正式实现会有出入。
- 三个新文件的规模未估算；实现后以 `wc -l` 为准。
