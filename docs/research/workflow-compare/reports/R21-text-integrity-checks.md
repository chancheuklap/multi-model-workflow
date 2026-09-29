# R21 文字完整性的两道机械检查：逐字搬运检查与结构 lint

本文设计两道检查，并给出它们进 B0 的票草案。目的是：落地的 worker 把技能文字搬到新层（mode、playbook、原则、能力技能）时，不能顺手改写句子，也不能把组件的结构写乱。R18 第 17 节 D9 把这件事定为「搬运的句子逐字保留，由逐字搬运检查与结构 lint 强制（`R21-text-integrity-checks.md`，进 B0）」；本文就是那份文件。`R21a-text-integrity-checks.md` 是它的草稿，保留不动；两者不同之处以本文为准，逐条理由见文末「审查记录」。

读者有四类：写 B0 spec 的会话（第 0、4.4、5.1、7 节进 Implementation Decisions）；切票的会话（第 3.2、3.5、3.8 节是写 `## Moves` 的规则，第 5 节是票草案）；B0 的 worker（经票的 `## Read first` 读第 3、4 节，那是 baseline）；评审（第 3.10、4.4 节说明哪些归检查、哪些仍要读了判断）。

**标注。** 「原文」＝文件里写着的；「已核实」＝本轮回到文件或跑命令看到的；「推断」＝由原文推出、原文没直接写的。路径不带前缀时相对仓库根；pstack 路径相对 `docs/research/code-landing-refs/pstack/`。R19、R20、R18、L7、R14 都指 `docs/research/workflow-compare/reports/` 下同名文件。

---

## 0. 结论（先读这里）

1. **两道检查，都放在 `mmw-v2/tests/lib/`，与连线检查共用一个模块、一个测试套件。**
   - `check_verbatim_moves.py`（逐字搬运检查）：读票上的 `## Moves`（搬运清单），比对源文字（钉在一个提交上）与目标文字（`HEAD`），列出被改写、被删、被新加却不在白名单里的句子，非 0 退出。另有 `--lint-drafts`，在切票时只查清单本身。
   - `check_component_structure.py`（结构 lint）：按文件所属的组件类型（mode、MMW 自写 playbook、导入的 playbook、原则、MMW 自有能力技能）检查结构与禁用句型。今天已有的违规登记在 `structure-exceptions.tsv`，每行写到期批次。
   - `skill_text.py`：两者与 `check_wiring.py`（R18 第 7.5 节）共用的 Markdown 切分、句子切分、路径解析与组件归类。
   - `run_shared_lints.sh`：每个套件的 `run.sh` 开头只调它一行，由它跑词表里已有的 **shared lints**（`docs/contexts/toolbox/CONTEXT.md` 第 213–215 行）；结构 lint 与 `check_wiring.py` 以后各加一行。
   - 三道检查的测试都在一个新套件 `mmw-v2/tests/skill-text/`。
   - 放在 `tests/lib/` 而不是 mode 的 `scripts/`：它们只在本仓库搬 MMW 自己的文字时有用，消费仓库的 agent 从不运行它们（第 3.7 节）。
2. **比较粒度是句子，按计数一一配对。** 两侧切成同一种单元（句子、标题、代码块等），规范化后当作带计数的多重集合比较：源里出现两次的句子，目标里也要出现两次（第 3.3 节）。
3. **检查回答三个问题**：源范围里的每一句都到了指定位置（carried）；指定目标位置里的每一句都有来处（accounted）；这张票在自己的分支上没有改动清单以外的技能文字（untouched）（第 3.1 节）。
4. **允许的机械改写只有五种**：空白与折行、列表符号与编号、标题与粗体步骤标题的互换、路径与链接写法（按解析到的文件比）、清单里逐行列出的改名；另外允许插入括注的原则点名 `(**principle-<slug>**)`。其余一切差异，包括加粗、标点、语序，都算改写；spec 要改的句子在清单里用 `replace` 逐条写出，并写出处（第 3.4 节）。
5. **改名按 R19 第 7 节接入**：`renames.tsv` 的 `kind` 只有 `path`、`token`、`text` 三种，`token` 与 `text` 可带一个路径范围。每张票的清单只抄入本票执行或本票文字需要的改名行；`--lint-drafts` 核对这些行都来自改名表，并查同批票之间的改名是否衔接（第 3.5、3.8 节）。
6. **结构 lint 与 `check_wiring.py` 分开，按「修复落在哪」划界。** R18 第 7.5 节第 3 类的句型部分、第 4 类、第 7 类的逐文件部分由结构 lint 实现，`check_wiring.py` 不再实现它们；R20 第 7 节每个标「机查」的审查项由哪条检查的哪条规则判，列在第 4.4 节对照表里。B0 spec 把这张表写进 Implementation Decisions（第 4.4 节）。
7. **结构 lint 从 B0 起就失败，靠例外表过渡**：今天树上已有的违规每条一行，写到期批次；新违规立刻失败；`--batch Bn` 让到期未还的行失败。例外表按 `docs/specs/*/renames.tsv` 的 `path` 行跟随文件改名，一行只抵消一条发现（第 4.5 节）。
8. **负控**：逐字检查每种发现一份必须失败的夹具，另在两份真实技能文件的副本和一份「拆段成步骤」的搬运夹具上做固定种子的单处变异，每次都必须报出；结构 lint 每条规则一份必须失败的夹具，外加在今天的树上报出 `capability-next-step` 的 8 处（第 3.9、4.7 节）。
9. **B0 五张票**，前提是先把本文与票里引用的研究文件提交到 base 分支（第 5.1 节）：共用检查入口与套件；逐字比较；票上的清单与未动文字；切票时的清单检查；结构 lint。拆成五张是为了每张在一夜之内做得完，并让 `--lint-drafts` 在 B1 切票之前落地。
10. **这两道检查管不到的**：句子摆放后是否仍然讲得通、理由是否还挨着它的规则（顺序检查只能部分覆盖）、新写的句子写得好不好。这些仍由评审的 Spec、Standards 两个 axis 与 `SKILL-SET-RULES.md` `## Verifying` 的「新会话实跑」判断（第 3.10 节）。
11. **本文不需要你做新的决定。** 检查的形式、位置与严格程度都是工程决定，理由与放弃的备选写在各节。mode 目录名是 `mmw`（R18 第 17 节 D10），两道检查从一个常量读它（第 4.1 节）；本文新起的 7 个名字已补进 R19 第 4.6、4.9 节（第 6 节）。落地后的效果：spec 没写进清单的改写一律过不了票，这正是 D9 的要求。

---

## 1. 为什么要机械检查，而不是写进规范让 worker 自觉遵守

- **规则已经写着，但只靠文字。** `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（本仓自有文件，squash `5b1a4c51` 的上游原文里没有它，R21a 已核实）`## Editing` 第 2 条：「A load finding is fixed in the structure: move, merge, split at a branch, or delete whole sections, carrying each sentence that still applies across verbatim. Sentences the finding does not touch stay byte for byte.」第 5 条：「Text taken from another source keeps its authors' wording … Excerpts are quoted verbatim and collected into one block before they are placed」。本文的搬运清单就是第 5 条说的「collected into one block」，只是由 spec 在切票时写好，不留给 worker。
- **同一文件要求把能查的规则做成检查。** `### Scripts and judgement` 第 3 条：「A rule a script could check exactly becomes a check (a lint, a refusal, a test), not a sentence.」「逐字」与「结构」都能精确判定。
- **两种写作风格在这里正面冲突，冲突点正是 worker 最可能动手的地方。** pstack `skills/poteto-mode/playbooks/authoring-a-skill.md` 第 10 行：「Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one.」`SKILL-SET-RULES.md` `## What skill text is for` 第 1 条：「beside its steps a skill says what the work is for … and, next to a rule, the reason for it」。R20 第 2 节 X1 裁定写理由。一个照 pstack 语气整理文字的 worker 会删掉 mattpocock 式的理由句；理由句决定 agent 在规则没写到的情形里怎么做。逐字检查把每一句被删的理由都报成 `DELETED`，除非 spec 在清单里写明 `drop` 与去处。
- **结构统一是改造的目的本身。** R18 第 3.2 节给 playbook 定了统一骨架，第 1.3 节把步骤的粗体标题定为锚点（「标题就是锚点；跨文件只按标题引用」），脚本的指针 `mmw <slug>#<Step title>` 靠它解析。结构写错，指针就断，这是运行故障，不只是好不好看。
- **pstack 自己有先例。** `skills/poteto-mode/scripts/check-plan.mjs` 第 5–21 行把必须原样出现的句子（常量 `RULE`）与必须出现的小节名（`PROGRAM_H3`、`SUB_BLOCKS`）写成检查器里的字面，逐行报 `file:line: message`（R21a 已核实）。结构 lint 沿用「检查器持有被匹配的字面」的做法（R13 E8 也记了这一点）。

---

## 2. 先找现成的（按全局规则 14）

检索在 R21a 那一轮做：GitHub 与包仓库，每个认真候选读了至少一个实现文件。星数与最后推送时间是那一轮 `gh api` 看到的，本轮没有重查。

| 候选 | 看了什么 | 覆盖多少 | 决定 |
|---|---|---|---|
| [jackchuka/mdschema](https://github.com/jackchuka/mdschema)（Go，80 星，2026-09-17 推送，MIT） | `internal/rules/structure.go`、`examples/tutorial.mdschema.yml` | 按标题层级的声明式 schema：必需与可选、`count`、顺序、`required_text`。能描述 mode 的小节序列；描述不了「编号列表项以粗体标题开头」「每步点名一个组件」「能力技能里不许出现 playbook 名」这类要跨文件清单的规则 | **不用，借它的写法**：规则表里「可选」「次数」「顺序」三个概念照它的 schema 取。不用的理由：引入 Go 二进制，本仓库没有包管理器（根 `AGENTS.md` `## Package Manager`） |
| [DavidAnson/markdownlint](https://github.com/DavidAnson/markdownlint)（JS，6362 星，2026-09-29 推送） | `lib/md043.mjs`（MD043 required-headings） | 标题序列带 `*`、`+`、`?` 通配，正好是 mode 小节检查；自定义规则 API 可写其余规则 | **不用，借 MD043 的通配记法**写 mode 的小节序列。不用的理由：需 npm 安装；其余规则都要读 `skills.txt`、`imports.tsv`、playbook 清单，写成它的自定义规则并不省事 |
| [agentskills/agentskills](https://github.com/agentskills/agentskills) 的 `skills-ref`（25783 星，2026-08-09 推送） | `skills-ref/src/skills_ref/validator.py` | `name` ≤64 字符且等于目录名、`description` ≤1024 字符（规格原文见 [agentskills.io/specification](https://agentskills.io/specification)）；`ALLOWED_FIELDS` 不含 `disable-model-invocation` | **不用，抄两条限值**进 `description-trigger`、`skill-name` 规则。不能直接跑：它会把上游技能的 `disable-model-invocation` 报成错 |
| [TheStack-ai/pulser](https://github.com/TheStack-ai/pulser)（TS，18 星） | `src/rules/description.ts` | description 是否含「Use when」类触发句、长度 | **不用**：只查有没有触发句，查不了 description 里是否夹带路由；它的触发句正则与本文 `description-trigger` 同形，印证这条规则可行 |
| [PiotrTrzpil/markdown-diff-viewer](https://github.com/PiotrTrzpil/markdown-diff-viewer)（TS，15 星，MIT） | `src/core/move-detection.ts` | 两份 Markdown 之间按相似度找搬走的段落与句子，分块级与句级 | **不用，印证粒度**：它也以句子为行内搬动的单位。它按相似度阈值（`MIN_COVER = 0.75`）认定「搬动」，一词之差正好被认成「搬了」；本文要的是相反的判定：一词之差就是改写 |
| [nipunsadvilkar/pySBD](https://github.com/nipunsadvilkar/pySBD)（Python，935 星，2024-08 推送） | `pysbd/segmenter.py` | 规则式断句，处理缩写 | **不用**：断句在两侧用同一个函数，断错不会造成漏报（第 3.3 节），标准库正则加一张缩写表足够 |
| Python 标准库 `difflib` | — | `SequenceMatcher` 对句子序列做对齐与顺序检查，`get_close_matches` 给改写配对 | **照用** |
| `git diff --color-moved` | — | 同一次 diff 里搬动的行着色 | **不用做判定**：按行，重新折行即失效，不认改名与路径改写，也不产出退出码。评审时可作人眼辅助 |

结论：没有覆盖八成需求的现成工具。两道检查自己写，用 Python 标准库加 PyYAML（frontmatter 解析，与 `mmw-v2/tests/lib/check_own_skill_frontmatter.py` 相同，经 PEP 723 块与 `uv run` 取得），借上表三处的写法。

---

## 3. 逐字搬运检查 `check_verbatim_moves.py`

### 3.1 它回答的三个问题

| 问题 | 判定 | 用在哪一次运行 |
|---|---|---|
| **Q1 carried**：清单每条 `move`/`copy` 的源范围（在 `from` 提交上读）里的每个单元，按计数一一对到它指定的目标位置（在 `HEAD` 上读），顺序不变；被 `drop` 的除外 | 目标位置里配不上 → `DELETED`（若在同一文件或本票别的目标位置里找到，附注「found in `<位置>`」）；同一条的顺序变了 → `OUT-OF-ORDER`；`move` 的源句在源文件 `HEAD` 上的出现次数，大于 `from` 上的次数减去搬走的次数 → `NOT-REMOVED`（`copy` 不查这一项） | 每次 |
| **Q2 accounted**：清单点名的每个目标位置里，`HEAD` 上的每个单元，要么配给了某条 `move`/`copy` 的一个源单元，要么是 `from` 时就已在这个位置的单元（按计数；整文件目标不适用），要么是一条 `new` | 没有来处 → 与最接近的未配对源单元配成 `CHANGED`（附逐词差异），配不上就是 `ADDED`；带整句的 `new` 没出现 → `MISSING-NEW` | 每次 |
| **Q3 untouched**：这张票自己的分支 diff（`merge-base(HEAD, <base>)..HEAD`）里，技能文字文件在清单范围以外没有单元变化 | 变化的单元 → `UNTOUCHED-CHANGED`。本票清单里的 `rename` 行（三种 kind，含范围）在原处生效造成的变化不算 | 只在当前分支是本票的 `issue-<n>` 时跑；否则输出写明「untouched text: not checked, not on this ticket's branch」，不装作通过 |

- **一一配对。** 所有判定都在规范化后的单元上按多重集合做：每个源单元实例只能配一个目标单元实例。所以源里两句相同的 `Stop.`、目标里只剩一句，就报一次 `DELETED`；目标里把一句写成两份，多出的那份报 `ADDED`。
- **整文件目标没有「原本就在」的豁免。** 目标是整个文件（`copy <上游原文> -> <path>`，即上游技能「回原文」）时，`from` 上这份文件里原有的句子不算来处，否则本仓加进上游文字、正要被回原文去掉的句子会被放过。目标是一节或一步时，这个位置在 `from` 上已有的单元（例如在一节里新加一步时原有的几步）算来处。
- **Q3 的「技能文字文件」**＝ `mmw-v2/skills/**`、`mmw-v2/upstream*/skills/**`、`.mmw/playbooks/**` 下的 `.md`，加上清单点名的任何文件（例如根 `AGENTS.md`）。ADR、`CONTEXT.md`、spec 这类新写的文档不在范围内，由评审的 Spec axis 判。
- **Q3 的 base**：先取 `--base <ref>`，再取 `$MMW_BASE_REF`。`verify-ticket.py` 在跑 `CHECK:` 时把它设为 `origin/<into>`，`into` 取自票上最新的 `worker.started`（`mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 第 1856、1871–1872 行，已核实）；夜里起的 worker 与 `dispatch.sh adopt` 都写 `into`（`mmw-v2/skills/dispatch/scripts/dispatch.sh` 第 871、1017 行，已核实）。在本票分支上而两者都没有 → 退出 2，一行写明要 `--base`，不打印 `VERBATIM OK`。
- **Q3 只在本票分支上跑**，因为收尾复核（closing pass）在 base 分支上重跑判据，那时 `merge-base..HEAD` 要么为空，要么（base 领先 `origin/<into>` 时）含整批票的改动，两种都不是这张票的 diff。认本票分支的依据是分支名 `issue-<n>` 等于 `$MMW_TICKET`（`to-tickets` `SKILL.md` 第 86 行「the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>`」）。
- **子树拉取不算 Q3 的变化。** `merge-base..HEAD` 里有提交信息以 `Squashed '<prefix>/'` 开头的提交（`git subtree … --squash` 的固定写法；本仓已有 `5b1a4c51 Squashed 'mmw-v2/upstream/' changes from …`、`c0faf4d7 Squashed 'mmw-v2/upstream-unlazy/' content from commit …`，已核实）时，`<prefix>/` 下的文件整体不做 Q3，成功行写出「subtree pulled: `<prefix>`」让评审看到。同一分支在这个前缀下手改的句子，由 `check_wiring.py` 第 3 类的「上游技能与 squash 原文的差异只能是 merge-note 登记过的两类」判（R18 第 7.5 节表第 3 类）。
- **Q3 的依据**：`SKILL-SET-RULES.md` `## Editing` 第 2 条末句「Sentences the finding does not touch stay byte for byte」。它也实现 R18 第 10 节「每张批次票的验收条件」第 1 条的文字部分：源文件里每一句要么搬走（Q1），要么 `drop` 并写明理由，要么留在原处不动（Q3）。

### 3.2 搬运清单：放在哪、怎么写

**放在票正文的 `## Moves` 小节，位于 `## Owns` 之后、`## Acceptance criteria` 之前**，小节里一个信息串为 `moves` 的围栏代码块。

- 理由：票是这条流水线唯一的状态（`mmw-v2/skills/verify-ticket/SKILL.md` 第 10 行「The ticket is the only state」）；评审与早上的你读的都是票；`CHECK:` 从 `$MMW_TICKET` 取自己的对象，符合 `to-tickets` `SKILL.md` 第 86 行。
- 位置的理由：`verify-ticket.py` 的 `section()` 取 `## <heading>` 到下一个 `## ` 行之间（第 441–460 行，已核实），所以放在前后都不会截断判据账本；放在 `## Acceptance criteria` 之前，判据仍是票的最后一节（与 `<issue-template>` 一致），清单挨着同样说「这张票写哪里」的 `## Owns`。
- 不会干扰判据运行：`verify-ticket.py` 只把 `## Acceptance criteria` 一节写成账本（第 694–704 行 `write_ledger`，已核实），判据运行的结果写进事件，不回写票正文（第 1882–1911 行，已核实）；`--lint` 不列举票的小节（本轮 grep：按标题列举的 `markdown_h2` 只在第 1346 行的 `--decisions` 里用），多一个 `## Moves` 不会被报。
- `## Moves` 是程序按字面找的小节名，与 `## Parent`、`## Owns` 等一起登记进 `locations.py`（R18 第 928 行，W4）。
- 放弃的备选：清单做成仓库里的文件。坏处是 worker 的分支能改它，检查读到的就是被改过的清单。选票正文是因为它是唯一状态；检查另接受 `--manifest <file>`，供自己的测试与白天手工使用。
- 清单行都以指令词开头，不以 `#` 开头，所以不会被 `section()` 当成小节边界。

**格式：一行一条指令。**

````
```moves
from 68d90576
rename token `sub-issues.md` -> `child-issues.md`
move mmw-v2/upstream/skills/engineering/implement/SKILL.md:L12 -> mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Claim
replace "First claim the ticket: " -> "Claim the ticket: " : R18 §3.3 P15 step Claim
drop mmw-v2/upstream/skills/engineering/implement/SKILL.md:L12 "If you picked the ticket up yourself" : entry Adopted ticket carries it (R18 §3.3 P15)
new mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Claim "Done when the claim printed `READY`." : R18 §3.3 P15 step Claim
new mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Claim title "Claim" : R18 §3.3 P15 step skeleton
new mmw-v2/skills/mmw/playbooks/work-a-ticket.md#Where you are : R20 §5.3 **Where you are.**
copy 5b1a4c51:skills/engineering/implement/SKILL.md -> mmw-v2/upstream/skills/engineering/implement/SKILL.md
```
````

（示例值，演示语法，不是定稿。句子与步骤名取自 R18 第 3.3 节 P15 与今天 `implement/SKILL.md` 第 12 行；改名行取自 R19 第 7 节；mode 目录是 `mmw`（R18 D10）。）

| 指令 | 含义 |
|---|---|
| `from <sha>` | 源文字的钉定提交，切票时 base 分支的 `HEAD`。必须有，且只能有一个。源范围都在这个提交上读，所以行号稳定 |
| `move <源> -> <目标> [any-order]` | 源范围整体搬到目标位置，源处应不再有它。整文件 `move` 自动带一条从源路径到目标路径的 `path` 映射，不必另写 `rename path` |
| `copy <源> -> <目标> [any-order]` | 同上，但源处保留。源可以带修订：`<rev>:<path>`。两种用途：导入 pstack 文件（源在 `mmw-v2/upstream-pstack/` 子树，原文不动，R18 第 8 节）；上游技能「回原文」（源是 squash 提交里的上游文件，写法照 `SKILL-SET-RULES.md` `## Upstream examples` 的 `git show <commit>:skills/<bucket>/<skill>/<file>`）。整文件 `copy` 同样自动带路径映射 |
| `replace "<旧>" -> "<新>" : <出处>` | 作用于紧挨着的上一条 `move`/`copy`：spec 决定的一处改写。旧串在那条源范围**规范化后的文字**上匹配（段内换行已变成一个空格，所以跨行折断不影响），必须恰好出现一次；新句的出处必填（R20 第 3 节 T3、T5）。R18 里的「改动标注」都写成这一行 |
| `drop <源> ["<句首>"] : <去处或理由>` | 这些单元不搬。不带引号串时是整个范围；带引号串时是范围里以它开头的那一句，在规范化文字上匹配；匹配到不止一句时退出 2，改写更长的句首 |
| `new <目标> ["<整句>"] : <出处>` | 白名单，出处必填（R20 第 3 节 T5）。带整句：这一句可以新写，必须逐字出现。不带整句：这个目标位置里的句子都可以新写，只允许用于 R20 第 5 节模板标「新写」的节，出处要写出那一节（`R20 §5.x <节名>`），`--lint-drafts` 查这个写法；spec 切票时尽量把句子写定。凡经不带整句的 `new` 放行的句子，成功输出逐行列出 `NEW <path>:<line>: <句子>`，评审读得到 |
| `new <目标> title "<Title>" : <出处>` | 放行一个新写的标题单元（R20 第 5.2 节表「编号步骤」行：「源里没有标题的新写」） |
| `rename <kind> <旧> -> <新> [in <路径 glob>]` | 本票套用的一条改名，kind 为 `path`、`token`、`text`（第 3.5 节） |

**位置写法**（`<源>`、`<目标>`）：

- `path`：整个文件（含 frontmatter）；`path@description`、`path@name` 是 frontmatter 的一个字段。
- `path#<文字>`：标题文字等于它的那一节，或粗体标题等于它的那个编号步骤或段落（`N. **Claim.**`、`**Where you are.**`），比较时按第 3.3 节标题单元的规范化。一个文件里匹配到两处即退出 2，改用行号（只对源）或更长的标题。范围：
  - 标题：到下一个同级或更高级标题为止，含下级小节。
  - 编号步骤：这个列表项及其全部子内容（续行、嵌套列表、缩进段落、缩进的围栏代码块），到同一列表的下一项或列表结束为止。
  - 粗体开头的段落：这一段，加上其后的段落，到下一个以粗体标签开头的块（前面是空行）或下一个标题为止。
- `path:L12` 或 `path:L12-L30`：行范围，只用于源（源在钉定提交上，行号不会漂）。目标只用标题或粗体标题，因为目标文件是新写的，行号在切票时不存在；R18 第 1.3 节也规定步骤标题就是锚点。

### 3.3 比较粒度：单元、规范化与计数

**单元。** 两侧用同一个函数（`skill_text.py`）把 Markdown 切成单元：

| Markdown 块 | 单元 | 规范化 |
|---|---|---|
| 段落、引用块（去 `>`） | 句子 | 段内换行变一个空格，连续空白合一 |
| 列表项（`-` `*` `+` `1.` `1)`，任意缩进层级） | 句子；项首的粗体标题另成一个标题单元 | 去掉列表符号、编号与缩进；续行并入本项 |
| 标题（`#`–`######`） | 标题单元 | 去掉 `#`、行首编号（`1.`）、粗体记号、末尾 `.`/`:` |
| 粗体开头的段落或列表项：`**...**` 包住的文字以 `.`、`:` 或 `?` 结尾 | 标题单元 + 其余句子 | 同上 |
| 表格行 | 每个单元格的句子 | 去掉 `|`；分隔行忽略 |
| 围栏代码块 | 整块一个单元 | 只套用本票 `rename` 行，其余逐字节比 |
| frontmatter | 每个键一个单元；`description` 再切句 | 用 PyYAML 解析（pstack 原则的 description 是带引号的字符串，`skills/principle-*/SKILL.md`，已核实） |
| HTML 注释、只有一个标签的行（`<issue-template>`） | 整体一个单元 | — |

- **计数。** 每个位置的单元是一个多重集合；第 3.1 节的三问都按计数判，`NOT-REMOVED` 比较的是这句在源文件里 `HEAD` 与 `from` 上的出现次数，不只看有没有。所以一句通用句（`Stop.`）在源文件别处合法出现，不会造成误报。
- **标题单元的意义**：mattpocock 的 `### 1. Gather context`（`to-tickets` `SKILL.md` 第 16 行）搬进 playbook 成为 `1. **Gather context.**`，这是 R18 第 3.2 节骨架要求的形式变化，不是改写。标题只与标题比。
- **断句**：在行内代码、链接、缩写（`e.g.`、`i.e.`、`etc.`、`vs.`、`cf.`）处先占位，再在 `.`、`?`、`!`、`。` 之后、下一个字符是大写字母、反引号、`*`、`(`、`[`、数字或中文时断开。

**为什么是句子。**

- 段落：pstack 骨架会把一段拆成几步（R18 第 3.3 节 P15 的第 1–2 步来自今天 `implement` 第 12–18 行的几段），也会把几段并进一步。按段落比，每一次这样的拆并都报改写，检查就没法用。
- 行：重新折行、列表缩进一变就全部失配。
- 词：能看出改了哪个词，但说不出「整句删了」「整句挪到另一步」，而这两类才是 D9 要防的主要破坏。
- 句子：R18 与 `SKILL-SET-RULES.md` 谈搬运都以句子为单位（`## Editing`「carrying each sentence … verbatim」）；报告按句给出，逐词差异只作为 `CHANGED` 一行的附注。

**断句不准不会造成漏报。** 两侧用同一个断句函数，一句话若被断成两截，源和目标断法相同，照样逐一对上。改动总会改变至少一个单元的内容，所以任何改写都会以某个单元配不上的形式出现。断句不准只会造成一种误报：worker 恰好在断句函数认不出的边界上拆了段（例如句号后跟小写字母）；报告会给出那一句，spec 在清单里加一行 `new` 即可（推断：由比较的对称性推出，第 3.9 节的变异测试实测漏报为 0）。

### 3.4 允许的机械改写与不允许的

允许（两侧规范化后比较，每一类单独计数，写进成功行）：

1. **空白与折行、列表符号与编号、标题与粗体标题互换**：见上表。
2. **路径与链接写法**：凡是指向文件的写法都解析成仓库内路径再比：
   - Markdown 链接 `[text](target)`：相对 `target` 按所在文件的目录解析；
   - 行内代码里形如路径的串（`references/x.md`、`scripts/y.py`）：按所在组件的根解析（能力技能是技能目录；mode、playbook、原则是 mode 目录，与 pstack 的 `../references/X` 相对链接解析到同一处）；依据 `SKILL-SET-RULES.md` `### Paths and host neutrality` 第 1 条「a skill's own references and scripts are named by their path inside the skill」；
   - 「the `S` skill's `P`」：按 `S` 的技能根解析 `P`；依据 `### Hand-offs`「A file in another skill is named by skill and file」。
   - 解析后再经本票的 `path` 映射（`rename path` 行与整文件 `move`/`copy` 自动带的那条）。
   - 判定：两侧都解析到存在的文件，且映射后是同一个文件，相等；两侧都解析不到，按字面比；**只有一侧解析得到，判 `CHANGED`**。所以一个搬到 mode 之后已指向不存在文件的 `references/x.md`，会被报出。断掉的路径本身由 `check_wiring.py` 第 2 类报（R18 第 7.5 节）。
   - 例：今天 `implement` 的 `` the `verify-ticket` skill's `references/sub-issues.md` `` 与 playbook 里的 `[sub-issues.md](../../verify-ticket/references/sub-issues.md)` 相等。
3. **改名**：只套用本票清单里列出的 `rename` 行（第 3.5 节）。
4. **原则点名的插入**：目标句里形如 `(**principle-<slug>**)` 或 `(**principle-a**, **principle-b**)` 的括注在比较前去掉，前提是 mode 目录的 `principles/principle-<slug>.md` 在 `HEAD` 上存在；不存在就留着比，于是报成 `CHANGED`。依据 R18 第 3.2 节「原则用括注点名」与第 5.1 节「调用方：点名一次」。只允许括注这一种形式；「本地限定句」是新写的句子，要走 `new`。

不允许（都算改写，要改就写 `replace`）：加粗与斜体的增删、标点（含 em dash、en dash 与引号样式）、大小写、语序、同义替换、把表格行改写成触发行、句首的连接词（例如去掉「First」「Then」）。R20 第 2 节 X5 规定 MMW 自写文字不用 U+2014、U+2013；源句带这两个字符而目标是 mode、playbook、原则时，spec 为每处写一行 `replace`，否则结构 lint 的 `no-dash` 与本检查必有一个报错。

句子的顺序：同一条 `move` 的源单元在目标里必须保持相对顺序（`difflib.SequenceMatcher` 对齐）。理由：mattpocock 的理由句常紧跟在规则之后（`SKILL-SET-RULES.md` `## What skill text is for` 第 1 条「next to a rule, the reason for it」），调换顺序会把理由挂到别的规则上。spec 确要重排时在那条 `move` 行尾加 `any-order`。

### 3.5 改名表怎样接入

- **来源**：R19 第 7 节（`R19-naming-table.md` 第 314–369 行，已核实）给出 `renames.tsv` 的内容；文件由写 spec 的会话建在 `docs/specs/<effort>/renames.tsv`（占位符 `<effort>` 按 R19 第 4.9 节保留），因为它是这次改造的决定记录，不是 MMW 的常设文件（全局规则 13）。只放仓库里已有、被搬运文字会提到的名字；R18 预定、还没建的名字不进表，spec 与票直接写新名（R19 第 7 节首段）。
- **列**：`kind`、`old`、`new`，可选第 4 列 `scope`（路径 glob）。
- **`kind` 只有三种，决定在哪里替换**：

  | kind | 替换位置 | 例（取自 R19 第 7 节） |
  |---|---|---|
  | `path` | 解析后的仓库路径（第 3.4 节第 2 条） | `mmw-v2/skills/verify-ticket/references/sub-issues.md` → `…/child-issues.md` |
  | `token` | 行内代码与围栏代码块里的完整记号（前后不接字母、数字、`_`、`-`、`.`） | `sub-issues.md` → `child-issues.md`；`key.md` → `release-manifest.md`，`scope` 为 `mmw-v2/skills/exe-release/**`（R19 第 7 节注意事项第 1 条：`upstream-diagram-design` 另有一个无关的 `key.md`） |
  | `text` | 所有单元的文字里的完整片段（前后不接字母、数字、`_`、`-`），全部出现处都替换 | `dispatch.sh wait` → `dispatch.sh result` |

  `dispatch.sh` 的 7 个子命令改名（R19 第 7 节）意思是「按表整批替换」，而清单的 `replace` 指令只改紧挨着的一条搬运里恰好一处，两者不是一回事；这 7 行在 `renames.tsv` 里的 kind 是 `text`。R19 注意事项第 2 条说的「单写的子命令由切票会话逐处列成 `replace`」，就是清单的 `replace` 指令，带出处 `R19 §4.7`。
- **`scope`**：只对 `HEAD` 上位于范围内的文件生效（搬运比较时看目标文件，Q3 时看原处文件）。不带 `scope` 就对全部被比较的文件生效。
- **生效处**：本票所有被比较的单元（源单元先套用再与目标比）与 Q3（base 上的单元先套用再与 `HEAD` 比），所以一张票在原处执行子命令改名，不会被报成 `UNTOUCHED-CHANGED`。
- **每张票只抄入本票要用的行**，写成清单里的 `rename` 行。不直接全局套用整张表：R18 第 2.4 节要求每一批的文字只点名当时已经存在的组件；全局套用会让 B1 搬的句子提前写上 B2 才改的名字（例如 `--claim`）。
- **防止清单与改名表漂开**：切票会话跑 `--lint-drafts <dir> --renames-table docs/specs/<effort>/renames.tsv`，清单里每一行 `rename` 都必须在表里有 kind、old、new、scope 都相同的一行，否则报 `RENAME-NOT-IN-TABLE`（第 3.6 节）。
- **导入票**：`import_component.py` 按 `pstack-rewrites.tsv`（R19 第 4.6 节，今天名为 `pstack.map`，R18 第 189 行）做的机械改写，在清单里同样写成 `rename` 行；`--renames-table` 可给两次，行在任一表里即可（推断：那张表的格式由建它的 B1 票定，R19 第 4.6 节「不是 TSV 就换扩展名」；不是这三列时，B1 那张票让 `--lint-drafts` 读它的格式）。
- **漏改会被抓到**：源单元按清单改名后才与目标比，目标若还写旧名，就是 `CHANGED`，逐词差异里看得到旧名。上游 mattpocock 与 pstack 的技能名与文件名不进改名表（用户要求第 2 条），所以 `copy` 自上游的句子不会被改名。

### 3.6 输出与退出码

沿用 `mmw-v2/tests/lib/` 现有检查的形式（逐行 `path:line: …`），另按 `SKILL-SET-RULES.md` `### Refusals and output an agent reads` 第 2 条「Hosts cut long output before the agent sees it, so the next step sits in the first lines」把汇总与下一步放在最前。

- **退出 0**：第一行只有通过时才出现，供 `EXPECT:` 匹配；其后是 `NEW` 行（若有）：

  ```
  VERBATIM OK 5 moves, 1 copy: 143 units carried (6 path, 4 rename, 3 citation, 2 title), 2 replaced, 4 new, 3 dropped; untouched text: 4 files, 0 changes; subtree pulled: none
  NEW mmw-v2/skills/mmw/playbooks/work-a-ticket.md:9: Run `dispatch.sh where` and go to the step it prints.
  ```

  计数让评审一眼看出这次比了多少，也让「什么都没比」无处藏身。不在本票分支上时，`untouched text:` 之后写 `not checked, not on this ticket's branch`。

- **退出 1**：有发现，或清单解析后一个单元都没有比（`VERBATIM FAIL checked nothing`，依据 `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条「A check that could verify nothing says so instead of reading like a pass」）。前三行固定：

  ```
  VERBATIM FAIL 2 changed, 1 deleted, 1 added
  Next: put each sentence below back to its source wording. If the wording cannot stand, keep it and open a `decision` child: the ticket's text is the spec's decision.
  Why: this ticket moves text verbatim; only the rewrites its ## Moves lists may differ from the source.
  mmw-v2/skills/mmw/playbooks/work-a-ticket.md:14: CHANGED from mmw-v2/upstream/skills/engineering/implement/SKILL.md:12 @68d90576
    - On `NOT_READY`, stop: the reason is already on the ticket.
    + On `NOT_READY`, stop.
  ```

  发现种类：`CHANGED`、`DELETED`（找到别处时附 `found in <位置>`）、`ADDED`、`OUT-OF-ORDER`、`NOT-REMOVED`、`UNTOUCHED-CHANGED`、`MISSING-NEW`。超过 40 条时只印前 40 条，末行写总数与 `--all`。
  - `Next:` 行里的 `decision` 子票是 worker 无人时的现有出口（今天是 `verify-ticket.py <n> --sub-issue decision`，B2 起按 R19 第 4.8 节是 `--child`；R18 第 2.2 节 `## Autonomy` 把它定为 worker 的出路）。输出文字不写开关名，只写「open a `decision` child」，所以改名不必改这一行。

- **退出 2**：什么都没能判定，原因写一行，不装作失败或通过：清单格式错；`from` 提交不存在；位置找不到或匹配两处；`replace` 旧串不在范围里或不止一处、`drop` 句首匹配不止一句（`STALE`）；`gh` 读不到票；票里没有 `## Moves` 或其中没有、或有两个 `moves` 围栏；在本票分支上而没有 base。与 `check_own_skill_frontmatter.py` 的退出 2（「nothing could be checked」）同义。

- **`--lint-drafts <dir> [--renames-table <tsv>]…`**（切票会话用，票发出之前）：对目录里每份草稿（`to-tickets` 第 7 步的草稿格式，`SKILL.md` 第 145 行：头行 `TITLE:`、`LABELS:`、`BLOCKED BY:`，一行 `---`，然后是正文）解析 `## Moves`，只查清单本身，发现逐行以规则 id 报出：
  - `L1 location`：每个位置在 `from` 上恰好解析一次。
  - `L2 stale`：每个 `replace` 旧串、`drop` 句首在范围的规范化文字里恰好一处。
  - `L3 provenance`：每个 `replace`、`drop`、`new` 的出处非空；不带整句的 `new` 的出处写的是 `R20 §5.<n>` 加一个节名。
  - `L4 overlap`：同一批里两张票的源范围不重叠、目标位置不重复；整文件目标与同一文件里任何 `path#…` 目标算重叠。
  - `L5 rename-table`：`rename` 行都在改名表里（`RENAME-NOT-IN-TABLE`）。
  - `L6 rename-carried`：同一批里一张票执行某行改名时，另一张票的源范围、目标位置在 `from` 上已有的文字、或 `new` 句里含这行改名的旧名（按 kind 与 scope 匹配），那张票也必须在清单里带这一行（`RENAME-NOT-CARRIED`）。
  - `L7 rename-order`：带同一行改名的几张票之间必须有 `BLOCKED BY:` 边（直接或经链），不能同时跑。
  
  L4、L6、L7 为什么需要，见第 3.8 节。退出 0 印 `DRAFTS OK <n> drafts, <m> moves checked`；有发现退出 1；草稿目录读不到、`from` 不存在退出 2。

### 3.7 放在哪：`mmw-v2/tests/lib/`，不是 mode 的 `scripts/`

- `mmw-v2/tests/AGENTS.md` 开头：`tests/` 「exists only in a checkout and is never symlinked into a host」。`CODING_STANDARDS.md` `## Skills and scripts` 第 1 条：技能目录「holds only what the agent holding the skill reads or runs」。消费仓库的 agent 不会搬 MMW 自己的技能文字，装到每个宿主上只是负担。
- R18 第 1.1 节把 mode 的 `scripts/` 定为流水线状态脚本（只被 playbook 步骤、mode 触发行、hook 调用），文字检查不属于这一类；R18 第 7.5 节把 `check_wiring.py` 也放在 `tests/lib/`，三者同处。
- 已安装 checkout 是完整 checkout（根 `AGENTS.md` `## Key Conventions` 第 2 条），所以 `install.sh --check` 以后需要时也能从那里调用。
- 后果：P11 **Authoring or modifying a skill** 是装到所有仓库的 playbook，不能写一条只在本仓库有效的路径。本仓库切「搬文字的票」的步骤由 B1 决定放在哪（私有 playbook 或 `to-tickets` 分叉后的一份 reference）；B0 只提供脚本，清单格式的唯一出处是脚本头注释与 `--help`（`SKILL-SET-RULES.md` `### Scripts and judgement` 第 1 条：完整参数表留在脚本旁）。

### 3.8 怎样进票：`## Moves` 的位置、`CHECK:` 与同批规则

每张搬文字的票（B0 里补四处断点的票与 `wayfinder` 第 5 步的过渡替换、B1、B2 的每张批次票、以后每次 **Import a component**）带 `## Moves`（位置见第 3.2 节），并加两条判据，写法照 `to-tickets` 第 4 步的四行格式：

```
- [ ] AC7: 本票搬的每一句逐字到位，本票新增与删去的每一句都列在 `## Moves` 里
  CHECK: uv run --quiet mmw-v2/tests/lib/check_verbatim_moves.py --ticket "$MMW_TICKET"
  EXPECT: /^VERBATIM OK \d+ /m
  EVIDENCE: pending
- [ ] AC8: 本票写的每个组件文件合它那一类的结构
  CHECK: uv run --quiet mmw-v2/tests/lib/check_component_structure.py mmw-v2/skills/mmw/playbooks/work-a-ticket.md mmw-v2/skills/verify-ticket/SKILL.md
  EXPECT: /^STRUCTURE OK \d+ files?/m
  EVIDENCE: pending
```

- **`uv run`**：两个脚本带 PEP 723 块取 PyYAML，与 `check_own_skill_frontmatter.py` 同法；根 `AGENTS.md` `## Commands` 已写明每个套件都需要 `uv`。
- **`EXPECT:` 是只在通过时才打印的整行开头**，合 `to-tickets` 第 84 行「a success-only marker」，也不在 `gate-lint.mjs` 的 `WEAK_EXPECT` 词表里（`mmw-v2/upstream-unlazy/scripts/gate-lint.mjs` 第 114 行，已核实）。`VERBATIM OK`、`STRUCTURE OK`、`DRAFTS OK` 与 `STORY OK` 同形；B0 建 `locations.py` 时一并登记为成功标记（R18 第 928 行，W5）。
- **`CHECK:` 里写仓库路径是允许的**：`SKILL-SET-RULES.md` `### Paths and host neutrality` 第 2 条禁的是给 oracle 写路径（oracle 由 `verify-ticket.py` 放上 `PATH`）；本仓库的票一直写仓库内测试的路径，例如 #589 AC5 的 `mmw-v2/tests/board/tasks.test.mjs`（R21a 已核实）。
- **切票规则（为了在收尾复核时仍然成立）**。收尾复核在 base 分支上重跑整批判据（`to-tickets` 第 88、90 行），所以一张票的判据会被同批后落地的票影响：「a criterion that names something a later ticket may change is decided by that ticket's work rather than by its own」（第 90 行）。下面每条规则防一种这样的影响，`--lint-drafts` 查括号里的那条：
  1. 清单写在切票会话里，你在场时定稿；worker 不改清单。
  2. 同一批里，一个源范围只出现在一张票的清单里，一个目标位置（一节或一步）也只出现在一张票的清单里；整文件目标占住这个文件的全部位置（L4）。否则票 B 往票 A 的整文件目标里另写一节，A 的 Q2 在收尾复核时报 `ADDED`。这与 `to-tickets` 第 5 步「no two tickets that can run at the same time write the same file」同一个道理，只是粒度到小节。
  3. 一张票的文字（源范围、目标位置原有的文字、`new` 句）含有同批某条改名的旧名时，它自己也带这行改名（L6）。否则票 B 在原处执行 `rename token X -> Y`，改到了票 A 已经落地的目标句，A 的清单里没有这条改名，收尾复核报 `CHANGED`。带上之后，A 的目标里本来就是新名，B 的替换碰不到它；A 的检查套用同一行，两侧一致。
  4. 带同一行改名的几张票不能同时跑，切票会话让执行改名（改文件或脚本本身）的那张排在最前（L7）。否则先落地的票会点名一个还不存在的新名字，`check_wiring.py` 第 2 类报断链。
  5. `from` 取切票时 base 分支的 `HEAD`。同一批的票在同一次切票里写，源范围又互不重叠，所以前面的票落地不会改动后面的票要读的源范围（它们都在 `from` 上读）。
- **放弃的备选**：收尾复核时把同批已落地票的改名行一并套用。它要在判据运行时经 tracker 找出同批票并解析它们的清单，多一层会失败的读取；上面第 3、4 条在切票时就能查，判据运行时只读本票。

### 3.9 怎样证明它自己会失败（负控）

依据：`SKILL-SET-RULES.md` `### Scripts and judgement` 第 4 条「A check or completion criterion that cannot fail proves nothing」；R18 第 5.2 节 **principle-silence-is-never-a-pass** 的「新建的检查先证明它会失败」。

1. **每种发现一份夹具**：测试在 `mktemp -d` 里建一个临时 git 仓库，提交源文件，写目标文件与 `--manifest` 清单，断言退出码与发现种类（`TESTING.md` `## What a test proves`：断言退出码与程序读的输出记号，不断言措辞）。`CHANGED`、`DELETED`（含 `found in`）、`ADDED`、`OUT-OF-ORDER`、`NOT-REMOVED`、`UNTOUCHED-CHANGED`、`MISSING-NEW`、`STALE`（退出 2）、`checked nothing`（退出 1）各一份；计数各一份：源里重复的一句在目标里只留一份报 `DELETED`，目标里一句写成两份报 `ADDED`，源文件别处合法出现的同一句不报 `NOT-REMOVED`；允许的五类改写各一份必须通过的夹具（拆段成带粗体标题的步骤、标题改粗体标题、链接改代码路径、清单列出的改名、原则括注），以及对应的反例（没列出的改名、括注点名一个不存在的原则、路径改指另一个存在的文件、路径改成解析不到的写法）必须失败。
2. **在真实文字上做变异**：把两份真实技能文件（`mmw-v2/skills/advisor/SKILL.md`：frontmatter、表格、链接；`mmw-v2/skills/retro/SKILL.md`：210 行，编号步骤、标题、表格）在切票时的内容提交为夹具副本，整文件 `copy` 必须通过；再用固定种子做 30 次单处变异，每次只改一处，每次都必须非 0 退出并报出被改的那一行。另对第 1 条「拆段成带粗体标题的步骤」那份 `move` 夹具做 20 次同样的变异。
   - 变异种类：换一个词、删一个词、加一个「not」、改一个数字、改一个行内代码里的名字、删一整句、交换相邻两句、加粗一个词、改一个标点。
   - 变异位置只取句子单元的正文，且不取一个块的第一个词：不碰列表符号与编号、标题记号、标题与粗体标题末尾的标点、步骤编号。理由：这些位置按第 3.3 节规范化后本来就不参与比较，变异落在那里被合法地抹掉，测试会误报失败；块首的词加粗后可能变成一个标题单元，改变的是单元种类而不是文字。
   - 用夹具副本而不是直接读真实文件：B2 会剥离 `advisor` 的文字（R18 第 10 节 B2 行），副本让测试不随它变。测试断言的是「每一次变异都被报出」，不是文件的措辞。
3. **每次运行自带的非空检查**：清单解析后一个单元都没比时退出 1（第 3.6 节），所以一条写错位置、实际什么都没比的判据不会显示为通过。
4. **`--ticket` 这一段也要测**：在 `PATH` 前面放一个假的 `gh`（沿用本仓库测试的做法，例如 `mmw-v2/tests/retro/test_retro.py`、`mmw-v2/tests/dispatch/test_status.py`，已核实），让它返回一份带 CRLF 换行、前后还有 `## Owns`、`## Acceptance criteria` 等小节的票正文，断言切出的清单与同一份清单经 `--manifest` 读到的结果相同。

### 3.10 它不管什么

- 句子搬到指定位置后讲不讲得通、理由是否还挨着它的规则（`any-order` 以外的顺序检查只覆盖同一条 `move` 之内）：评审的 Spec axis，加 `SKILL-SET-RULES.md` `## Verifying` 的「a fresh agent given only the trigger and a real job」实跑。
- `new` 句子写得好不好、出处是否真的支持它：R20 写作规范（第 3 节 T5、T6）与评审；本检查只保证出处字段非空、新句逐行可见。
- 脚本里的文字（拒绝文字、启动提示词、唤醒行）、JSON（`roles.json`）：不是 Markdown，不在范围内；它们的锚点由 `check_wiring.py` 查（R18 第 7.5 节第 1、8 类）。
- 整目录平移的脚本：由 git 的改名检测与各套件的测试保证。

---

## 4. 结构 lint `check_component_structure.py`

### 4.1 怎样认出一个文件是哪类组件

按路径，加 `imports.tsv` 的登记（R18 第 1.1 节目录树、第 8.2 节导入类型）。mode 目录名 `mmw`（R18 第 17 节 D10）写在 `skill_text.py` 的一个常量 `MODE_DIR` 里；两道检查与 `check_wiring.py` 都从这个常量取，将来改名只改一处。下表写作 `<mode>`。

| 类型 | 路径 | 查不查 |
|---|---|---|
| mode | `mmw-v2/skills/<mode>/SKILL.md` | 查 |
| MMW 自写 playbook | `mmw-v2/skills/<mode>/playbooks/*.md` 中未登记为导入的；`.mmw/playbooks/*.md`（`INDEX.md` 除外） | 查 |
| 导入的 playbook | `imports.tsv` 类型为 `playbook` 的行 | 只查首行 `### <Name>` 与末行 `**Reply:**`（R18 第 7.5 节第 7 类原文）；`imports.tsv` 标为例外的（`opening-a-pr.md`）连这也不查 |
| 原则 | `mmw-v2/skills/<mode>/principles/principle-*.md` | 查（导入的与自写的同一格式，R18 第 5.1 节） |
| mode 的 reference | `mmw-v2/skills/<mode>/references/**` 中未登记为导入的 | 只查第 4.2 节表里适用于「全部自写文字」与「新组件」的规则 |
| MMW 自有能力技能 | `mmw-v2/skills/<name>/SKILL.md` 与它的 `references/**/*.md`（`<mode>` 除外） | 查 |
| 上游子树里的技能 | `mmw-v2/upstream*/**` | 不查：`SKILL-SET-RULES.md` `### Upstream skills` 第 4 条「Checks on style … apply to the set's own text」；本仓在上游文字里加的句子由 `check_wiring.py` 第 3 类的「上游差异」一项查（R18 第 4.3 节） |

「新组件」＝ mode、MMW 自写 playbook、原则、mode 的 reference：这次改造才建的文件，没有旧债。

### 4.2 按类型的规则表

规则 id 是稳定编号，写在输出里；删掉的规则留空号不复用（照 pstack `unslop` 的「Rule numbers are stable ids that other skills cite」，L7 A.3 规则目录型）。规则表作为数据写在脚本开头，每条带出处。frontmatter 用 PyYAML 解析（第 2 节末）。

| id | 适用 | 规则 | 出处 |
|---|---|---|---|
| `mode-name` | mode | frontmatter `name` 等于 `MODE_DIR`，没有 `disable-model-invocation` | R18 第 2.1 节；R19 第 8 节 |
| `mode-sections` | mode | H2 依次为 `## Non-negotiables`、`## Principles`、`## Autonomy`、`## Re-entry`、`## Subagents`、`## Writing the reply`、可选 `## Comments`、`## Playbooks`；之前最多一个 H1。用 MD043 的记法写成序列，`## Comments` 记为 `?` | R18 第 1.1 节目录树注释与第 2.2 节；R20 第 5.1 节 S-M1 |
| `mode-imported-triggers` | mode | `### Imported triggers` 只能在 `## Non-negotiables` 之下 | R18 第 2.2 节、第 8.2 节 |
| `mode-principle-line` | mode | `## Principles` 下的条目形如 `- **<Title>** (**principle-<slug>**). <文字>.` | R18 第 2.2 节 `## Principles` 第 3 条；R20 S-M3 |
| `mode-route-line` | mode | `## Playbooks` 下的路由行形如 `- **<Name>.** … \`playbooks/<file>.md\`.`（以反引号文件名收尾） | L7 A.1；R18 第 2.2 节 `## Playbooks` 第 4 条；R20 S-M3 |
| `playbook-title` | 自写与导入 playbook | 首个非空行是 `### <Name>`；没有 frontmatter，没有 H1、H2 | L7 A.2；R20 S-P1 |
| `playbook-owner-line` | 自写 playbook | 有所有权行时，它是标题后的第一段，形如 `**You own …**`；不要求一定有 | R18 第 3.2 节「所有权行只在有出处时写」；R20 S-P1 |
| `playbook-steps` | 自写 playbook | 有任何 `####` 小节时，恰好一个是 `#### Steps`，步骤是它下面的第一个有序列表；没有 `####` 时，步骤是第一个顶层有序列表；编号从 1 连续 | R18 第 3.2 节；R20 S-O2 |
| `step-title` | 自写 playbook | 每步以 `N. **<Title>.**` 开头；同一文件里步骤标题不重复（它们是锚点） | R18 第 1.3 节「步骤」行；R20 X17、S-P3 |
| `step-done-when` | 自写 playbook | 每步有一行以 `Done when` 开头 | `SKILL-SET-RULES.md` `### Rules and completion criteria`；R20 X10 |
| `step-names-component` | 自写 playbook | 每步至少点名一个组件（`skills.txt` 里的技能名、`**principle-<slug>**`、playbook 的显示名、mode `scripts/` 里的脚本命令、`references/…` 路径），或在粗体标题之后写 `(judgement)`（R20 S-P7） | R18 第 3.2 节；第 7.5 节第 7 类 |
| `playbook-reply` | 自写与导入 playbook | 最后一个非空行以 `**Reply:**` 开头，且全文恰好一行以 `**Reply:**` 开头 | L7 A.2 第 6 条；R20 第 5.2 节表 `**Reply:**` 行「全文恰好一个」 |
| `principle-frontmatter` | 原则 | frontmatter 只有 `name`、`description`；`name` 等于文件名去掉 `.md`，以 `principle-` 开头 | R18 第 1.3 节「原则」行、第 5.1 节「格式」 |
| `principle-applies` | 原则 | `description` 第一句以 `Apply ` 开头（when、to、after、before、during、whenever），至少两句。mode 索引的「何时适用」取这第一句，所以它必须是触发情境 | L7 A.4；R18 第 2.2 节 `## Principles` 第 3 条；R20 X7 |
| `principle-body` | 原则 | 正文以 `# <Title>` 开头；小节用段首粗体标签 `**<Label>:**`，不用 `##`（登记的例外：pstack `principle-prove-it-works` 的 `## Script the check when you can`）；`**Why:**` 最多一个。**不要求有 `**Why:**`** | L7 A.4；R18 第 5.1 节「原文没有理由的不写 `**Why:**`」；R20 S-R1 |
| `principle-direction` | 原则 | 不出现 playbook 的文件名或显示名、`scripts/`、`mmw#`、`mmw <slug>#`（按 `MODE_DIR`） | L7 B.2 硬规律 1；R18 第 5.1 节「方向」；R20 S-R2 |
| `capability-next-step` | 能力技能及其 reference | 不出现「下一步」「谁调用我」句型：`## Next`、`## Reached from here` 标题；「return to」后接技能名；「hand (it) over/on to」后接技能名；「goes through the X skill first」；「are steps of the X skill」；「next step」与技能名同句。技能名指 `skills.txt` 里的名字，带不带反引号都认（`retro/SKILL.md` 第 186 行写的是没有反引号的「the dispatch skill's」，已核实） | R18 第 4.5 节第 2 条；句型取自 R14 第 2 节「下一步句的完整名单」；R20 S-C3 |
| `capability-playbook-name` | 能力技能及其 reference | 不出现 playbook 的文件名、显示名、`playbooks/`、`mmw <slug>#` 指针。角色名（worker、reviewer）作为领域词可以出现 | R18 第 4.5 节第 2 条；R20 S-C3 |
| `numbered-cross-reference` | 全部自写文字 | 不出现跨文件的按编号引用：`step \d+` 或 `## \d+` 前面在同一句里点名了别的文件或技能（`` `SKILL.md` step 4 ``、「the `X` skill's step 2」、`` `night.md` `## 5. The night is over` ``）、`closing step \d`、`Phase [A-Z]`、`rules? \d+( and \d+)? of` 后接别的技能或文件（「rules 3 and 4 of the `ui-acceptance` skill's …」）；同一文件内的编号引用不算 | R18 第 7.5 节第 4 类（含 `## N`）；`SKILL-SET-RULES.md` `### Vocabulary` 第 8 条「by title rather than by number」；R20 X9 |
| `host-name` | 全部自写文字 | 行内代码与链接目标之外，不出现宿主名、工具名、runner 名：`Claude Code`、`Codex`、`Grok`、`Cursor`、`Orca`、`herdr`、`Paseo`、`the Skill tool`、`the Task tool`（大小写不敏感，整词） | `SKILL-SET-RULES.md` `### Paths and host neutrality` 末段的 grep 名单。这条检查今天只写在文字里，没有脚本实现（R21a 在 `mmw-v2/tests/` 里 grep 不到）。与那份名单的差别：不查单独的 `claude` 与 `pi`，也不查行内代码；R21a 按那份名单整词 grep `mmw-v2/skills/`，去掉「Claude Design」后仍有 18 行命中，全是 `CLAUDE.md` 这类文件名、`claude-design` 这类路径和 Claude Design 的功能说明；按本行的写法只剩 1 行（第 4.3 节） |
| `no-dash` | 新组件（mode、自写 playbook、原则、mode 的 reference） | 围栏代码块之外不出现 U+2014、U+2013 | R20 X5、S-G5、K8；今天的 `check_upstream_em_dashes.py` 只查 `mmw-v2/upstream/skills/`（文件头，已核实）。只查新组件的理由见下 |
| `description-trigger` | mode 与能力技能 | `description` 有一句以 `Use ` 开头；另外最多一句以 `Not for` 或 `Do not use` 开头的非触发句；总共不超过 3 句、1024 字符 | `SKILL-SET-RULES.md` `### Descriptions` 第 1 条；上游 `wizard`、`prototype` 的写法；1024 取自 Agent Skills 规格与 `skills-ref` 的 `MAX_DESCRIPTION_LENGTH` |
| `description-content` | mode 与能力技能 | `description` 不点名别的技能（`skills.txt` 里的名字，带不带反引号都认，「the X skill」同理）、不写技能内部路径（`references/`、`scripts/`、`SKILL.md`）、不写 playbook 名或步骤编号 | `SKILL-SET-RULES.md` `### Descriptions` 第 1 条「Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body」 |
| `skill-name` | 能力技能 | frontmatter `name` 等于目录名，≤64 字符 | Agent Skills 规格；`skills-ref` `_validate_name` |

几条取舍：

- **`no-dash` 只查新组件。** 本轮 grep `mmw-v2/skills/` 下的 `.md`，U+2014 与 U+2013 共 160 处、分布在 25 个文件（例：`mmw-v2/skills/code-checkers/references/git-hooks.md` 第 36 行「A formatter in the hook is right in principle — its output is deterministic」）。去掉它们是改文字，按 D9 要由 spec 在清单里逐处写 `replace`；在 B0 就对这 25 个文件报错，会把 160 处旧债塞进例外表，而且每张碰到这些文件的票都要处理与自己无关的破折号。新组件没有旧债，从第一天起就不许有；搬进新组件的句子带破折号时，spec 写 `replace`（第 3.4 节末段）。能力技能里的旧破折号留给以后一张专门的清理票，由它的清单逐处 `replace`，这张票不在 B0–B2 的范围里。
- **`description-content` 不禁路径本身。** 今天 `ui-acceptance` 的 description「Use when filling `.mmw/target.json`」把一个文件当触发分支，这是触发，不是路由；所以只禁技能内部路径。
- **不查能力技能的正文形态。** L7 A.3 列出 pstack 能力技能有八种形态，R20 S-C2 也给了七种，一份文件用哪一种要读懂内容才能判（R20 K17 标为「判断」）。强求统一形态就等于改写 mattpocock 的文字，与 D9 相反。R18 第 4.5 节第 1 条「以交付物结尾」同理交给评审的 Standards axis。
- **`step-done-when` 只对 MMW 自写 playbook。** pstack playbook 没有 `Done when` 行（`skills/poteto-mode/playbooks/bug-fix.md` 全文，R21a 已核实），导入的保持原文；`Done when` 是本仓自己的写法（R20 X10）。
- **不设简报模板的规则。** R20 第 5.7 节 S-B1 要求简报模板首行 `# <Role> prompt template`；今天仅有的四份评审简报首行是 `# Spec axis` 等（`mmw-v2/upstream/skills/engineering/code-review/references/*-reviewer.md`，已核实），R19 第 4.5 节保留它们现名，B2 才搬。为四个文件加一条规则再加四行例外，不如交给评审（第 4.4 节 K18）。
- **与 `SKILL-SET-RULES.md` 的冲突要在 B1 解决。** 它的 `### Hand-offs` 第 5 条（第 92 行）「Each skill ends by naming what comes next, or the caller it returns to」与 `capability-next-step` 正好相反。R14 T38、R18 第 4.5 节、R20 X13 已定下「下一步住在 playbook」；B1 把这份文件搬进 mode 的 `references/skill-set-rules.md` 时要改这一条，否则文字与检查互相矛盾。

### 4.3 在今天的树上会报什么

R21a 用一段临时脚本（不在仓库里）按上表的几条正则扫了 `mmw-v2/skills/` 下的 `.md`；本轮重读了下表每一处的原文，确认仍在原行，并补扫了 `## \d` 形式（推断：正式实现的正则会有出入，B0 的例外表以实现的输出为准）。`until` 列是例外表该写的到期批次，依据是 R18 把该处文字搬走的那一批，worker 照抄，不必再判断。

| 规则 | 位置与原文片段 | `until` | 依据 |
|---|---|---|---|
| `capability-next-step` | `verify-ticket/SKILL.md:16`「are steps of the `implement` skill」；`verify-ticket/SKILL.md:23`「## Reached from here」 | B2 | R18 第 10 节 B2 行票 a「`verify-ticket` … 剥离」 |
| `capability-next-step` | `write-screen-contract/SKILL.md:113`「## Next」；`:115`「return to the `wayfinder` skill」 | B1 | R18 第 4.1 节表该行「`## Next` → P3、P1」，P1–P11 在 B1 |
| `capability-next-step` | `design-pages/references/edit-pages.md:31`「## Next」；`design-pages/references/pull.md:35`「## Reached from here」；`pull.md:37`「return to the `wayfinder` skill」 | B1 | R18 第 4.1 节表 `design-pages` 行「→ P3」；R19 第 4.5 节 `edit-pages.md` 行「B1（`design-pages` 搬出 `## Next` 的同票）」 |
| `capability-next-step` | `retro/SKILL.md:186`「return to the dispatch skill」 | B2 | R18 第 4.1 节 `retro` 的时机进 P12，P12 在 B2（R18 第 10 节 B2 行） |
| `numbered-cross-reference` | `retro/SKILL.md:186`「`## 5. The night is over`」 | B2 | 同上一行，同一句 |
| `numbered-cross-reference` | `design-pages/SKILL.md:25`「`UI.md` step 6」 | B1 | R18 第 4.1 节 `design-pages` 行「第 25 行按编号引用 … → 同技能内的 `state-list-format.md`」 |
| `numbered-cross-reference` | `code-checkers/references/git-hooks.md:36`、`code-checkers/references/python.md:46`「`SKILL.md` step 4」 | B1 | R18 没有单列这两处；`code-checkers` 第 6、8 步在 B1 搬进 P9（R18 第 4.1 节表 `code-checkers` 行），这两处随那张票改成按标题引用（`git-hooks.md` 第 36 行已写出标题 **The formatter, by one rule**） |
| `numbered-cross-reference` | `exe-release/references/driving.md:3`「`exe-release` step 3」、`:44`「step 4」；`exe-release/references/key.md:225`「`SKILL.md` step 3」 | B1 | R18 没有单列；R19 第 4.5 节 `driving.md` → `release-loop.md`、`key.md` → `release-manifest.md` 都在 B1，按引用随那张改名票改 |
| `host-name` | `design-pages/references/edit-pages.md:27`「Handoff to Claude Code」 | `permanent` | Claude Design 按钮上的字，照录；`reason` 列写这一句 |
| `description-trigger` | `dispatch/SKILL.md`：没有 `Use ` 句 | B2 | R18 第 10 节 B2 行「`dispatch` 解散」 |
| `description-content` | `retro/SKILL.md` description「the dispatch skill's `summary`」 | B2 | R18 第 4.1 节，时机进 P12 |

- R14 第 2 节的 17 句名单里，8 句在 `mmw-v2/skills/` 的自有技能里，9 句在上游子树里。上表 `capability-next-step` 的 8 处覆盖自有的 6 句（`edit-pages.md` 的 `## Next`、`pull.md` 的 `## Reached from here`、`write-screen-contract` 的 `## Next`、`retro` 第 186 行、`verify-ticket` 第 16 行与它的 `## Reached from here`），另外 2 处（`pull.md:37`、`write-screen-contract/SKILL.md:115`）是这些小节里的「return to」句。漏掉的 2 句是 `ui-acceptance` 表第 1 行与 `dispatch` 表第 1 行：它们是「时刻表」里指向别的技能的 reference 的一行，与合法的技能交接（`SKILL-SET-RULES.md` `### Hand-offs`「A file in another skill is named by skill and file」）句型相同，正则区分不开，留给评审。上游子树里的 9 句由 `check_wiring.py` 第 3 类的上游差异一项负责。
- `edit-pages.md`、`driving.md`、`key.md` 会在 B1 改名；例外表的行按 `renames.tsv` 的 `path` 行跟着走（第 4.5 节），改名票不必改例外表。
- 这一节同时是正控（第 4.7 节）：B0 票要求实现在今天的树上报出 `capability-next-step` 的 8 处，按路径、规则 id 与原文片段比，不按行号。

### 4.4 与 `check_wiring.py` 的分工，及 R20 审查清单的对照

**决定。** 两个脚本，一个共用模块，一个共用套件。按「修复落在哪」划界：

| | 结构 lint `check_component_structure.py` | 连线检查 `check_wiring.py`（R18 第 7.5 节） |
|---|---|---|
| 问什么 | 这个文件按它的组件类型，结构齐不齐、有没有禁用句型 | 文件里写出的名字，能不能通到一个存在的、方向允许的东西 |
| 修复在哪 | 同一个文件 | 常在另一个文件（被指向的 playbook、`roles.json`、`skills.txt`） |
| 从 R18 第 7.5 节接过来 | 第 3 类中的句型部分（能力技能的「下一步」「谁调用我」、原则的方向）；第 4 类（不按编号，含 `## N`）；第 7 类中逐文件的部分（`### <Name>`、粗体步骤、`**Reply:**`、每步点名组件） | 保留第 1、2、5、6、8–12 类；第 3 类的脚本部分（能力技能脚本不调 mode 命令、锚点只来自 `locations.py`、上游差异只有两类）；第 7 类中跨文件的部分（路由表每份 playbook 恰好一行、`INDEX.md` 同理） |
| 何时失败 | B0 起，靠例外表过渡（第 4.5 节） | 按 R18 第 7.5 节各类的批次 |

**理由。**

1. 失败的读者不同：结构 lint 的失败由写那个文件的 worker 在本文件里修；连线失败常要去改另一张票拥有的文件（`to-tickets` 的 **Owns**），报告要说清两端。
2. 落地时间不同：结构 lint 必须在任何搬文字的票之前就能失败，而 `check_wiring.py` 大多数类别要等 mode、playbook 建成才有对象。合在一个脚本里，同一个文件要同时容纳「B0 就失败」与「B2 末才失败」两种开关。
3. 三道检查都要同一套 Markdown 切分、组件归类与清单（技能名、playbook 名、原则 slug），放进 `skill_text.py` 共用，测试放进同一个套件 `tests/skill-text`，避免三份各自解析、各自出错。

**与 R18 的差别，B0 spec 要写明。** R18 第 7.5 节把第 3、4 类定为「B2 末」转为失败、第 7 类「B1」；本文把其中移给结构 lint 的部分改为 B0 起就失败，旧违规按例外表逐条到期。R18 第 50 行「连线检查（第 7.5 节 `check_wiring.py`）保证它们不回流」说的「下一步」句，由结构 lint 的 `capability-next-step` 保证。R20 第 7 节把 K13、K16、K22 标为「连线检查第 x 类」，以下表为准。B0 spec 把上面的分工表与下面的对照表写进 Implementation Decisions，`check_wiring.py` 那张票据此不实现移走的部分；否则写 spec 的会话照 R18 第 7.5 节原文，会在两张票里各实现一遍。

**放弃的备选。** 把结构规则并进 `check_wiring.py` 作为新的几类。省一个入口，但上面第 2 条的开关会变复杂，而且 `check_wiring.py` 在 B0 的范围已经很大（R18 第 10 节 B0 行）。

**建议 `check_wiring.py` 也用例外表过渡**，代替「每类在某批之前只报告」的开关：新违规立刻失败，旧违规逐条到期。这是给 R18 第 7.5 节的建议，是否采用由写 B0 spec 时定。

**R20 第 7 节审查清单 → 由谁判。** 「机查」＝检查通过即可，评审只核对它跑过且干净；「判断」＝评审读了判。

| K | 查什么（R20 原文摘要） | 由谁判 |
|---|---|---|
| K1 | 每句到位、每句有来处、清单外文字没改 | 逐字检查 Q1、Q2、Q3 |
| K2 | 只有五种机械改写 | 逐字检查（`CHANGED`） |
| K3 | 规则与理由句没被拆开 | 判断；逐字检查的 `OUT-OF-ORDER` 覆盖同一条 `move` 之内 |
| K4 | 新句在「新写」位置、有出处 | 出处非空与不带整句的 `new` 只用于 R20 第 5 节的节：`--lint-drafts` L3；出处是否支持这句：判断 |
| K5 | 没有编出无出处的所有权行、首段、`**Why:**`、`Done when` | 判断 |
| K6 | 上游原文没按模板改写 | `check_wiring.py` 第 3 类（上游差异） |
| K7 | 标题层级合组件类型 | mode、playbook、原则：结构 lint `mode-sections`、`playbook-title`、`principle-body`；能力技能与 reference 的层级：判断（第 4.2 节「不查能力技能的正文形态」） |
| K8 | 没有 U+2014、U+2013 | 新组件：结构 lint `no-dash`；上游子树：`check_upstream_em_dashes.py`；能力技能：判断，旧债见第 4.2 节 |
| K9 | frontmatter 只有 `name`、`description`，`name` 等于目录名 | `check_own_skill_frontmatter.py`（键）；结构 lint `skill-name`、`principle-frontmatter`（名字） |
| K10 | 不点宿主、工具、runner 名 | 结构 lint `host-name` |
| K11 | mode 节名与顺序、原则索引行格式、显示名等于原则 H1 | 结构 lint `mode-sections`、`mode-principle-line`；显示名与 H1：`check_wiring.py` 第 5 类 |
| K12 | 每步粗体标题、点名组件、`Done when`、`**Reply:**` 恰好一个 | 结构 lint `step-title`、`step-names-component`、`step-done-when`、`playbook-reply` |
| K13 | 恰好一个 `#### Steps`；被指针指向的标题存在 | 结构 lint `playbook-steps`；指针：`check_wiring.py` 第 1 类 |
| K14 | 每个（角色，事件）一个处理处 | `check_wiring.py` 第 6 类 |
| K15 | 原则只用固定标签、没有 `##`、不指向 playbook、脚本、mode | 结构 lint `principle-body`、`principle-direction` |
| K16 | 能力技能没有「下一步」「谁调用我」、没有 playbook slug | 结构 lint `capability-next-step`、`capability-playbook-name` |
| K17 | 做法一种形态、与内容相符 | 判断 |
| K18 | 简报模板首行、分隔线、占位；启动提示词一行 | 启动提示词一行：`check_wiring.py` 第 8 类；简报模板：判断（第 4.2 节「不设简报模板的规则」） |
| K19–K21 | playbook 不装做法；reference 内联与不按主题拆；长度 | 判断 |
| K22 | 跨文件不按编号（`step \d`、`Phase X`、`## N`） | 结构 lint `numbered-cross-reference` |
| K23 | 原则引用只用括注，slug 存在 | `check_wiring.py` 第 5 类 |
| K24 | 点名的技能、reference、子命令、playbook 都存在 | `check_wiring.py` 第 2 类 |
| K25 | reference 指针带条件；脚本调用写何时跑与各结果 | 判断 |
| K26 | 程序读的名字没为文风改；改名处同票改完 | 判断，辅以 `grep`；清单与改名表一致：`--lint-drafts` L5、L6 |
| K27–K38 | 写法各项 | 判断 |

### 4.5 例外表 `structure-exceptions.tsv`

- 文件 `mmw-v2/tests/lib/structure-exceptions.tsv`，五列：`path`、`rule`、`excerpt`（被报那一行里的一段原文，用来匹配，不用行号，所以行号挪动不会让它失效）、`until`（`B1`、`B2`… 或 `permanent`）、`reason`。第一版由结构 lint 的 `--write-exceptions` 从今天树上的输出生成，`until` 与 `reason` 按第 4.3 节填。
- **路径跟随改名**：读表时，结构 lint 读仓库里所有 `docs/specs/*/renames.tsv` 的 `path` 行，把表里的旧路径映射到新路径（链式改名依次映射）。所以 B1 把 `edit-pages.md` 改名为 `set-up-and-sign-off.md` 后，那条 `permanent` 行照样生效，改名票不必改这张共享表，也就不必把它放进自己的 **Owns**。
- **一行只抵消一条发现**：同一 `path`（映射后）、`rule`、`excerpt` 的发现数多于这样的行数，多出的发现失败。所以同一文件以后新写一句同样的违规，不会被旧行掩盖。
- 判定：
  - 发现没有行可抵消 → 失败。
  - 表里某行已抵消不到任何发现（文字已改好）→ 打印一行 `WARN stale exception`，不失败。理由：让「还债」的票不必同时改这张共享表，避免同批几张票都去写它（`to-tickets` 第 5 步：共享的登记文件会让并行的票在合并时冲突）；每批最后一张票或批次验收时清理。
  - `--batch Bn`：`until` 不晚于 `Bn` 且仍抵消着发现的行 → 失败。这就是 R18 第 10 节验收条件第 2 条「第 3 类的『只报告』输出里，属于本批文件的条目为零」的机器形式。
- `permanent` 行必须有 `reason`，评审读得到。worker 不应为了让自己的判据通过去加例外：这张表不在搬文字的票的 **Owns** 里，改了会在 `Outside Owns:` 一行报出；失败输出的 `Next:` 行也写明「规则确实不适用时开 `decision` 子票，不改例外表」。
- 这张表钉住的是今天文字的片段，与 `TESTING.md` `## What a test proves` 反对的「钉住措辞」不是一回事：它不是测试，而是一张会缩短的待办表，文字改好之后行就过期、被删。

### 4.6 输出、放在哪、进 `CHECK:`

- 两种运行方式：
  - 不带文件参数：查整棵树，由 `run_shared_lints.sh` 在每个套件开头跑。
  - 带文件参数：只查这些文件，用在票的 `CHECK:` 里（第 3.8 节 AC8）。
- 输出与逐字检查同形。退出 0 印一行 `STRUCTURE OK <n> files (<m> exceptions in use, <k> stale)`；退出 1 前三行是汇总、`Next:`、`Why:`，然后每条 `path:line: <rule-id> <说明> | <那一行的原文，最多 80 字符>`（原文片段供例外表匹配与判据按片段比）；退出 2 表示没能检查（例如 `skills.txt` 读不到、PyYAML 缺失）。查了 0 个文件也是退出 1。
- 放在 `mmw-v2/tests/lib/`，理由同第 3.7 节。

### 4.7 负控与正控

1. **每条规则一份必须失败的夹具**，放在 `mmw-v2/tests/skill-text/fixtures/structure/`，每份只违反一条，测试断言报出的恰好是那条的 id（R18 第 7.5 节「为每一类放一个必须失败的反例」）。
2. **每种组件类型一份合格样本必须通过**：mode、自写 playbook（短的与带 `#### Steps` 的长的各一）、原则（有 `**Why:**` 的与没有的各一）、能力技能。
3. **今天的树上的正控**：带 `--no-exceptions` 运行时必须报出第 4.3 节 `capability-next-step` 那 8 处，按路径、规则 id 与原文片段比。这是一次性的判据（写在 B0 票里），不写成常驻测试，因为那 8 处会在 B1、B2 被搬走，常驻测试会随文字过期（`TESTING.md` `## What a test proves`）。

---

## 5. B0 票草案

### 5.1 切票前提与与 B0 其余票的关系

**前提：先把研究文件提交到 base 分支。** 夜里的 worker 在从 base 分支切出的 `.worktrees/issue-<n>` 里工作，只读得到已提交的文件；本轮 `git status --short docs/research/workflow-compare/reports` 显示 L7、R12、R13、R14、R18、R19、R19a、R20、R20a、R20b、R21a 都是未跟踪（`??`）。B0 spec 写一条前置要求：切票前把本文与下面各票 `## Read first` 引用的 `R18-mmw-architecture-v2.md`、`R19-naming-table.md`、`R20-writing-style-guide.md`、`L7-pstack-component-contract.md` 提交到 base 分支。pstack 快照 `docs/research/code-landing-refs/pstack/` 已在仓库里（`git ls-files` 有它，已核实）。票的 `## Read first` 按 `to-tickets` 模板（`SKILL.md` 第 172–174 行）写完整路径加节名，因为「The implementer reads these and nothing else from the spec's Sources」。

**五张票。** 拆法的理由：R21a 的三张里，逐字检查一张有 10 条判据，一个 worker 一夜很可能做不完；`--lint-drafts` 要在 B1 切票前落地，而它与 Q3、`--ticket` 都不影响核心比较，分开后各自小而独立。

| 草稿名 | 做什么 | BLOCKED BY | worker |
|---|---|---|---|
| `b0-shared-lints` | 每个套件经 `run_shared_lints.sh` 跑共用检查；建套件 `tests/skill-text` | (none) | junior |
| `b0-verbatim-compare` | 逐字比较：单元、规范化、计数、Q1、Q2、`--manifest` | `b0-shared-lints` | senior |
| `b0-verbatim-ticket` | 票上的清单与未动文字：`--ticket`、Q3 | `b0-verbatim-compare` | senior |
| `b0-verbatim-lint-drafts` | 切票时查清单：`--lint-drafts` L1–L7 | `b0-verbatim-ticket` | junior |
| `b0-structure-lint` | 结构 lint 与例外表，接进 `run_shared_lints.sh` | `b0-shared-lints`、`b0-verbatim-compare` | senior |

- worker 等级按 `to-tickets` 第 6 步：一道检查做错时是「静默通过」，正是「wrong silently」，所以三张实现判定逻辑的票给 `senior-worker`；两张是入口与清单格式校验，做错会在夜里大声失败，给 `junior-worker`。这是提给你在切票提问时确认的建议。
- `b0-verbatim-lint-drafts` 被 `b0-verbatim-ticket` 阻塞，是因为两者都改 `check_verbatim_moves.py`（`to-tickets` 第 5 步：能同时跑的两张票不写同一个文件）。
- **与 B0 其余票的边**（写 B0 spec 时补上）：
  - `check_wiring.py` 那张票被 `b0-structure-lint` 阻塞：两张都往 `run_shared_lints.sh` 加一行，而且它用 `skill_text.py`；它的测试放进 `tests/skill-text`，不另开 `tests/wiring`（第 6 节）。
  - B0 里改技能文字的票（`night.md` 与脚本文字上补四处断点，R18 第 10 节 B0 行；`wayfinder` 第 5 步的过渡替换，R18 第 16 节）被 `b0-verbatim-ticket` 阻塞，带只有 `from` 与 `new` 行的清单，新写的句子在切票时定稿。它们与本组票同一次切出，`--lint-drafts` 那时还不存在，所以它们的清单由切票会话按第 3.6 节 L1–L3 手查；B1 起一律跑 `--lint-drafts`。
  - **B0 最后落地的那张票**加两条全树判据：`bash mmw-v2/tests/lib/run_shared_lints.sh && uv run --quiet mmw-v2/tests/lib/check_component_structure.py --batch B0`，`EXPECT: /^STRUCTURE OK \d+ files/m`。按 `to-tickets` 第 90 行，扫全树的判据放在本批最后一张票上，同批其他票改文字不会让它在收尾复核时误判到别的票头上；它证明整批合起来之后每个套件仍能开跑。
- 下面的 `#<spec>` 与 Implementation Decisions 的节号在写 spec 时填。判据的 `CHECK:` 形式照本仓库先例：套件 `run.sh -k <用例名> 2>&1 | tail -1`，`EXPECT: /^all passed$/m`（#493 各条，R21a 已核实；`run.sh` 只在全部通过时打印 `all passed`，见 `mmw-v2/tests/write-screen-contract/run.sh` 末尾）。新套件照 `write-screen-contract/run.sh` 第 27–33 行，经 `uv run --quiet --with pyyaml python -u …/run_unittests.py` 跑 `test_*.py`（已核实）。

### 5.2 票 `b0-shared-lints`

````
TITLE: 每个测试套件经一个入口跑共用检查，并建文字检查的套件
LABELS: mmw:ticket, ready-for-agent, junior-worker
BLOCKED BY: (none)
---
## Parent

#<spec>, Implementation Decisions sections <n>

## What to build

1. 新建共用检查入口 `run_shared_lints.sh`：按今天的顺序与退出行为跑词表 **shared lints** 的三道检查（`check_module_paths.py`、`check_upstream_em_dashes.py`、经 `uv run` 的 `check_own_skill_frontmatter.py`），任何一道非 0 就以非 0 退出。以后加一道共用检查只改这一个文件。AC2 判定。
2. 现有每个套件的 `run.sh` 把今天各自抄的三行换成一行调用它。AC1 判定。
3. 新建套件 `skill-text`：`run.sh` 开头同样调用入口，经 `run_unittests.py` 跑 `test_*.py`，支持 `-k`，全部通过才打印 `all passed`。以后的逐字搬运检查、结构 lint、连线检查只往这里加测试文件，不改 `run.sh`。AC1、AC2 判定。
4. 文档：根 `AGENTS.md` `## Commands` 的套件数与名单加上 `skill-text`，「Every `run.sh` first runs …」一句改为经入口；`mmw-v2/tests/AGENTS.md` 说明 `lib/` 里多了入口；`docs/contexts/toolbox/CONTEXT.md` **shared lints** 词条的 `_Home_` 改为入口。由评审的 Spec axis 判，不设判据。

## Read first

- `docs/research/workflow-compare/reports/R21-text-integrity-checks.md` `## 0. 结论（先读这里）` 第 1 条与 `### 5.1 切票前提与与 B0 其余票的关系`：baseline，入口与套件在整组检查里的位置。
- `mmw-v2/tests/AGENTS.md`：套件、`lib/` 与隔离的约定。
- `TESTING.md` `## What a test proves`：断言退出码与记号，不断言措辞。

## Seam

`mmw-v2/tests/skill-text/`（新套件，Python `unittest` 经 `run_unittests.py`）。入口的反例测试在 `mktemp -d` 里复制一份最小的 `mmw-v2/` 树（`tests/lib/` 加一个点名不存在模块的脚本），在那份副本上跑入口，因为三道检查都从自己的位置找 `mmw-v2/` 根。先例：`mmw-v2/tests/write-screen-contract/run.sh`。

## Owns

- mmw-v2/tests/lib/run_shared_lints.sh (new)
- mmw-v2/tests/*/run.sh
- mmw-v2/tests/skill-text/run.sh (new)
- mmw-v2/tests/skill-text/test_shared_lints.py (new)
- mmw-v2/tests/AGENTS.md
- AGENTS.md
- docs/contexts/toolbox/CONTEXT.md

## Acceptance criteria

- [ ] AC1: 每个套件的 run.sh 都调用共用检查入口，且没有一个还直接调用 lib/check_*.py
  CHECK: n=$(ls mmw-v2/tests/*/run.sh | wc -l | tr -d ' '); c=$(grep -l 'lib/run_shared_lints.sh' mmw-v2/tests/*/run.sh | wc -l | tr -d ' '); test "$n" -gt 12 && test "$c" -eq "$n" && test -z "$(grep -l 'lib/check_' mmw-v2/tests/*/run.sh)" && echo "SHARED-LINTS-IN-ALL $c of $n"
  EXPECT: /^SHARED-LINTS-IN-ALL \d+ of \d+$/m
  EVIDENCE: pending
- [ ] AC2: 入口里任何一道检查失败时，入口以非 0 退出
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_shared_lints_stop_on_a_failing_check 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
````

- AC1 不写死套件数：`n > 12` 断言新套件已加上（今天是 12 个，`ls mmw-v2/tests/*/run.sh`，已核实），`c = n` 断言没有一个漏掉。它扫的是全部 `run.sh`；B0 里没有别的票新建套件（`check_wiring.py` 用 `tests/skill-text`，R18 第 16 节的调研角色测试加在已有套件里），所以同批不会让它变红。B0 spec 若另加套件，就把 AC1 移到本批最后一张票上。

### 5.3 票 `b0-verbatim-compare`

````
TITLE: 逐字搬运检查：按句比对搬运清单的源与目标
LABELS: mmw:ticket, ready-for-agent, senior-worker
BLOCKED BY: b0-shared-lints
---
## Parent

#<spec>, Implementation Decisions sections <n>

## What to build

1. 共用模块 `skill_text.py`：把 Markdown 切成句子、标题、代码块、表格单元格、frontmatter 字段等单元并规范化，按计数配对；解析文件路径的三种写法；给文件归组件类型；读 `skills.txt`；mode 目录名是一个常量。结构 lint 与连线检查以后共用它。AC1–AC7 经它判定。
2. 逐字搬运检查 `check_verbatim_moves.py`，本票只做 `--manifest <file>` 读清单（读票与 Q3 是下一张票）：清单的指令、位置写法、`replace`/`drop` 的匹配、`new` 的三种写法、`rename` 的三种 kind 与范围；回答 Q1、Q2；输出与退出码，成功行以 `VERBATIM OK` 开头，经不带整句的 `new` 放行的句子逐行列为 `NEW`。清单格式写在脚本头注释与 `--help` 里，那是它的唯一出处。AC1–AC8 判定。
3. 负控：在两份真实技能文件的夹具副本与「拆段成步骤」的搬运夹具上做固定种子的单处变异。AC9 判定。
4. `docs/contexts/tickets/CONTEXT.md` 加 **`## Moves`** 词条（票上的搬运清单；`_Home_` 是这个脚本）。由评审的 Spec axis 判，不设判据。

## Read first

- `docs/research/workflow-compare/reports/R21-text-integrity-checks.md` `### 3.1 它回答的三个问题` 至 `### 3.6 输出与退出码`、`### 3.9 怎样证明它自己会失败（负控）`：baseline，检查的行为定义。Q3、`--ticket`、`--lint-drafts` 不在本票。
- `docs/research/workflow-compare/reports/R19-naming-table.md` `## 7. 机器可读的改名行（供 renames.tsv）`：三种改名 kind 的真实行。
- `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `## Editing`：搬运要逐字的规则原文。
- `CODING_STANDARDS.md` `## Skills and scripts` 第 4 条：拒绝与失败输出的三部分。
- `mmw-v2/tests/lib/check_own_skill_frontmatter.py` 文件头：PEP 723 取 PyYAML、经 `uv run` 的先例。

## Seam

`mmw-v2/tests/skill-text/test_verbatim_compare.py`，夹具在 `mmw-v2/tests/skill-text/fixtures/verbatim/`。每个用例在 `mktemp -d` 里 `git init` 一个临时仓库，提交源文件得到 `from` 提交，写目标文件与 `--manifest` 清单，断言退出码与发现种类记号。先例：`mmw-v2/tests/write-screen-contract/` 的夹具式用例。

## Owns

- mmw-v2/tests/lib/skill_text.py (new)
- mmw-v2/tests/lib/check_verbatim_moves.py (new)
- mmw-v2/tests/skill-text/test_verbatim_compare.py (new)
- mmw-v2/tests/skill-text/fixtures/verbatim/** (new)
- docs/contexts/tickets/CONTEXT.md

## Acceptance criteria

- [ ] AC1: 一节拆成几个带粗体标题的步骤、段内重新折行、列表符号与编号改变、标题改为粗体步骤标题时，检查通过
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_a_reflowed_move_is_verbatim 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: 搬过去的一句改了一个词时，报 CHANGED 并退出 1
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_one_changed_word_is_changed 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC3: 源范围里的一句没有到目标、也没有 drop 时报 DELETED，在别处找到时附 found in；有 drop 时通过
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_a_missing_sentence_is_deleted_unless_dropped 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC4: 目标位置里一句没有来处、也不在 new 里时报 ADDED；带整句的 new、title 形式的 new 放行各自那一个单元；不带整句的 new 放行的句子逐行打印为 NEW；带整句的 new 没出现时报 MISSING-NEW
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_an_unlisted_sentence_is_added_unless_new 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC5: 按计数配对：源里重复的一句在目标里只留一份报 DELETED，目标里一句写成两份报 ADDED，move 的源句在源文件里多于应剩次数报 NOT-REMOVED，源文件别处合法出现的同一句不报；同一条 move 内调换顺序报 OUT-OF-ORDER，行尾有 any-order 时通过
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_units_are_matched_by_count_and_order 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC6: 路径改写成指向同一文件的另一种写法、整文件 move 后的路径、清单列出的三种 kind 的改名（含 scope 之内与之外）、括注点名一个存在的原则都通过；没列出的改名、括注点名不存在的原则、路径改指另一个存在的文件、只有一侧解析得到的路径都报 CHANGED
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_mechanical_rewrites 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC7: 整文件 copy 到已有文件时，那份文件原有而源里没有的句子报 ADDED；在一节里加一步时，那一节原有的句子不报
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_whole_file_targets_have_no_prior_text_allowance 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC8: 位置找不到或匹配两处、replace 旧串不在范围里或不止一处、drop 句首匹配不止一句、from 提交不存在、清单格式错时退出 2 且不打印 VERBATIM OK；清单一个单元都没比时退出 1
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_nothing_checked_is_never_a_pass 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC9: 两份真实技能文件的夹具副本原样 copy 通过，30 次固定种子的单处变异每一次都退出 1 并报出被改的行；拆段成步骤的 move 夹具上 20 次同样的变异也是如此
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_every_seeded_mutation_is_reported 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
````

### 5.4 票 `b0-verbatim-ticket`

````
TITLE: 逐字搬运检查读票上的 ## Moves，并查分支上清单以外的文字没被改
LABELS: mmw:ticket, ready-for-agent, senior-worker
BLOCKED BY: b0-verbatim-compare
---
## Parent

#<spec>, Implementation Decisions sections <n>

## What to build

1. `--ticket <n>`：经 `gh issue view` 取票正文，换行规范为 LF，从 `## Moves` 小节里取唯一一个 `moves` 围栏；小节或围栏没有、围栏有两个时退出 2。结果与同一份清单经 `--manifest` 读到的相同。AC2 判定。
2. Q3 untouched：当前分支是本票的 `issue-<n>` 时，比较 `merge-base(HEAD, <base>)..HEAD` 里技能文字文件在清单范围以外的单元变化，报 `UNTOUCHED-CHANGED`；本票的 `rename` 行在原处造成的变化不算；分支上有 `Squashed '<prefix>/'` 提交时这个前缀整体不查并写进成功行；base 取 `--base`，再取 `MMW_BASE_REF`，都没有时退出 2；不在本票分支上时成功行写明没有检查。AC1 判定。

## Read first

- `docs/research/workflow-compare/reports/R21-text-integrity-checks.md` `### 3.1 它回答的三个问题`（Q3 一行及其下各条）、`### 3.2 搬运清单：放在哪、怎么写`（`## Moves` 的位置）、`### 3.9 怎样证明它自己会失败（负控）` 第 4 条：baseline。
- `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` `_run_checks`：`CHECK:` 运行时的 `MMW_TICKET`、`MMW_BASE_REF` 从哪来。
- `mmw-v2/tests/retro/test_retro.py`：在 `PATH` 上放假的 `gh` 的先例。

## Seam

`mmw-v2/tests/skill-text/test_verbatim_ticket.py`。Q3 的用例在临时仓库里建 base 分支与 `issue-<n>` 分支（含一次 `git subtree add --squash` 的用例）；`--ticket` 的用例在 `PATH` 前面放一个假的 `gh`，返回带 CRLF 与 `## Owns`、`## Acceptance criteria` 等小节的正文。

## Owns

- mmw-v2/tests/lib/check_verbatim_moves.py
- mmw-v2/tests/skill-text/test_verbatim_ticket.py (new)
- mmw-v2/tests/skill-text/fixtures/verbatim-ticket/** (new)

## Acceptance criteria

- [ ] AC1: 本票分支上改了清单范围以外的一句技能文字时报 UNTOUCHED-CHANGED；本票 rename 行在原处的改动、子树拉取带进来的改动不报，后者写进成功行；本票分支上没有 base 时退出 2 且不打印 VERBATIM OK；不在本票分支上时成功行写明 untouched text 没有检查
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_untouched_text 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: --ticket 从一份带 CRLF、前后还有别的小节的票正文里切出的清单，与同一份清单经 --manifest 读到的结果相同；没有 ## Moves、没有或有两个 moves 围栏时退出 2
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_ticket_body_gives_the_same_manifest 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
````

### 5.5 票 `b0-verbatim-lint-drafts`

````
TITLE: 切票时检查一批草稿的搬运清单
LABELS: mmw:ticket, ready-for-agent, junior-worker
BLOCKED BY: b0-verbatim-ticket
---
## Parent

#<spec>, Implementation Decisions sections <n>

## What to build

1. `--lint-drafts <dir> [--renames-table <tsv>]…`：读 `to-tickets` 第 7 步格式的草稿目录，只查每份草稿 `## Moves` 里的清单本身，按规则 L1–L7 报出（位置、旧串与句首、出处、同批重叠、改名表、改名随带、改名顺序）；成功行以 `DRAFTS OK` 开头。它在 B1 切第一批搬文字的票之前落地，让清单的错在白天暴露。AC1–AC3 判定。

## Read first

- `docs/research/workflow-compare/reports/R21-text-integrity-checks.md` `### 3.6 输出与退出码`（`--lint-drafts` 一条）与 `### 3.8 怎样进票：## Moves 的位置、CHECK: 与同批规则`：baseline，L1–L7 与每条防的是什么。
- `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` `### 7. Publish the tickets to the configured tracker`：草稿文件的头行与 `---`。
- `docs/research/workflow-compare/reports/R19-naming-table.md` `## 7. 机器可读的改名行（供 renames.tsv）`：改名表的真实行，含带范围的 `key.md` 一行。

## Seam

`mmw-v2/tests/skill-text/test_verbatim_lint_drafts.py`。每个用例在临时仓库里提交源文件，在 `mktemp -d` 里写几份草稿与一份 `renames.tsv`，断言退出码与规则 id。

## Owns

- mmw-v2/tests/lib/check_verbatim_moves.py
- mmw-v2/tests/skill-text/test_verbatim_lint_drafts.py (new)

## Acceptance criteria

- [ ] AC1: 位置解析不到或匹配两处、replace 旧串或 drop 句首不是恰好一处、replace/drop/new 缺出处、不带整句的 new 的出处没写 R20 第 5 节的节，各报对应规则 id
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_lint_drafts_locations_and_provenance 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: 两份草稿源范围重叠、目标位置重复、整文件目标与同文件的一节目标并存时报 L4
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_lint_drafts_batch_overlap 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC3: rename 行不在改名表里报 L5；一份草稿的文字含同批另一份执行的改名旧名而自己没带这一行报 L6；带同一行改名的两份草稿之间没有 BLOCKED BY 边报 L7；三种情形都改正后退出 0 并打印 DRAFTS OK
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_lint_drafts_renames 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
````

### 5.6 票 `b0-structure-lint`

````
TITLE: 结构 lint：按组件类型查结构与禁用句型，今天的违规登记为到期例外
LABELS: mmw:ticket, ready-for-agent, senior-worker
BLOCKED BY: b0-shared-lints, b0-verbatim-compare
---
## Parent

#<spec>, Implementation Decisions sections <n>

## What to build

1. 结构 lint `check_component_structure.py`：按组件类型归类，按规则表逐文件检查；规则表作为数据写在脚本开头，每条带出处。不带文件参数查整棵树，带文件参数只查这些文件；成功行以 `STRUCTURE OK` 开头，每条发现带那一行的原文片段。AC1–AC3 判定。
2. 例外表 `structure-exceptions.tsv`：由 `--write-exceptions` 从今天树上的输出生成，`until` 与 `reason` 按基准文件第 4.3 节的表填（这张表已经给出每一处的批次，不必再判断）。读表时按 `docs/specs/*/renames.tsv` 的 `path` 行跟随改名；一行只抵消一条发现；支持 `--batch Bn`、`--no-exceptions`；抵消不到发现的行只打印 `WARN`。AC4、AC5 判定。
3. 共用检查入口加一行跑它（不带参数）。AC6 判定。
4. `docs/contexts/toolbox/CONTEXT.md` 加 **structure lint** 与 **`structure-exceptions.tsv`** 词条。由评审的 Spec axis 判，不设判据。

## Read first

- `docs/research/workflow-compare/reports/R21-text-integrity-checks.md` `## 4. 结构 lint check_component_structure.py`（全节）：baseline，规则表、今天的发现与批次、例外表、与连线检查的分工。
- `docs/research/workflow-compare/reports/L7-pstack-component-contract.md` `### A.1 mode`、`### A.2 playbook`、`### A.4 原则`：各类的正文模板。
- `docs/research/workflow-compare/reports/R18-mmw-architecture-v2.md` `### 7.5 连线检查 mmw-v2/tests/lib/check_wiring.py`：本票接过来的第 3、4、7 类原文。
- `docs/research/workflow-compare/reports/R20-writing-style-guide.md` `## 5. 模板`：各规则对应的模板原文。
- `docs/research/code-landing-refs/pstack/skills/poteto-mode/scripts/check-plan.mjs`：检查器持有字面的先例。

## Seam

`mmw-v2/tests/skill-text/test_component_structure.py`，夹具在 `mmw-v2/tests/skill-text/fixtures/structure/`。用例把夹具放进 `mktemp -d` 里按组件路径排好的最小树，用 `--root` 指向它（这个参数只供测试）。

## Owns

- mmw-v2/tests/lib/check_component_structure.py (new)
- mmw-v2/tests/lib/structure-exceptions.tsv (new)
- mmw-v2/tests/lib/skill_text.py
- mmw-v2/tests/lib/run_shared_lints.sh
- mmw-v2/tests/skill-text/test_component_structure.py (new)
- mmw-v2/tests/skill-text/fixtures/structure/** (new)
- docs/contexts/toolbox/CONTEXT.md

## Acceptance criteria

- [ ] AC1: 规则表的每条规则各有一份夹具，每份只报出那一条规则的 id 并退出 1
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_each_rule_fails_its_own_fixture 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC2: mode、短 playbook、带 #### Steps 的长 playbook、有 Why 与没有 Why 的原则、能力技能各一份合格样本都通过
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_well_formed_components_pass 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC3: 导入的 playbook 只查首行 ### 与末行 **Reply:**，没有粗体步骤标题也通过
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_imported_playbook_keeps_its_own_steps 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC4: 没有行可抵消的发现失败；同一片段的发现多于行数时多出的失败；renames.tsv 改名后的文件仍被旧路径的行抵消；until 不晚于 --batch 的仍在抵消的行失败；抵消不到发现的行只打印 WARN
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_exceptions 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
- [ ] AC5: 在今天的树上不用例外表运行时，报出 capability-next-step 的 8 处（R14 下一步句名单里自有技能的 6 句，及这些小节里的 2 处 return to），按路径、规则 id 与原文片段比
  CHECK:
  ```
  out=$(uv run --quiet mmw-v2/tests/lib/check_component_structure.py --no-exceptions 2>&1)
  n=0
  while IFS='|' read -r path excerpt; do
    printf '%s\n' "$out" | grep -F "mmw-v2/skills/$path:" | grep -F ' capability-next-step ' | grep -qF "$excerpt" && n=$((n+1))
  done <<'EOF'
  verify-ticket/SKILL.md|are steps of the `implement` skill
  verify-ticket/SKILL.md|## Reached from here
  write-screen-contract/SKILL.md|## Next
  write-screen-contract/SKILL.md|return to the `wayfinder` skill
  retro/SKILL.md|return to the dispatch skill
  design-pages/references/edit-pages.md|## Next
  design-pages/references/pull.md|## Reached from here
  design-pages/references/pull.md|return to the `wayfinder` skill
  EOF
  test "$n" -eq 8 && echo FOUND-ALL-8
  ```
  EXPECT: /^FOUND-ALL-8$/m
  EVIDENCE: pending
- [ ] AC6: 共用检查入口在一份最小树副本里遇到一处没有例外行可抵消的结构违规时以非 0 退出
  CHECK: bash mmw-v2/tests/skill-text/run.sh -k test_shared_lints_run_the_structure_lint 2>&1 | tail -1
  EXPECT: /^all passed$/m
  EVIDENCE: pending
````

- AC5 用围栏里的多行命令（写法见 `mmw-v2/merge-notes/unlazy.md` `### scripts/lib/gates.mjs`：`CHECK:` 下紧跟的围栏代码块就是命令；`CHECK:` 同一行不能再写值）。按原文片段比，不按行号，所以同批别的票改动这些文件的其他行不会让它失效；B0 里没有票搬走这 8 处（R18 第 10 节 B0 行）。
- 全树通过（`--batch B0`）不在本票，写在 B0 最后一张票上（第 5.1 节）。

---

## 6. 新名字（待补进 R19）

R19 第 2 节「脚本」「测试套件」「配置、状态文件」的命名规矩适用于本文新起的名字。下表按那些规矩起名，下次编辑 R19 时补进第 4.6、4.9 节，随 R19 一起给你过目；B0 spec 写的是这些名字。

| 名字 | 是什么 | 理由 | 放弃的写法 |
|---|---|---|---|
| `check_verbatim_moves.py` | 逐字搬运检查 | 说出它查的东西：清单里的搬运是否逐字；与 `tests/lib/` 现有 `check_*.py` 同句式 | — |
| `check_component_structure.py`、**structure lint** | 结构 lint | 本文中文一直叫「结构 lint」；组件的结构是 R18 第 3.2 节、R20 第 5 节的用词 | `check_component_skeletons.py`、「skeleton lint」：skeleton 在词表里已指 `extract_skeleton.py` 写出的 JSON（`docs/contexts/ui-acceptance/CONTEXT.md` 第 302–303 行 **skeleton**），违反 SSR 第 74 行「One word, one meaning」 |
| `structure-exceptions.tsv` | 结构 lint 的例外表 | 同上；装的是 TSV 就 `.tsv`（R19 第 2 节「配置、状态文件」） | `skeleton-exceptions.tsv`：同上 |
| `skill_text.py` | 三道检查共用的 Markdown 切分与归类 | 说出它管的东西：技能文字；Python 新文件用下划线（R19 第 2 节「脚本」） | — |
| `run_shared_lints.sh` | 每个套件开头调的共用检查入口 | 词表已有 **shared lints**（`docs/contexts/toolbox/CONTEXT.md` 第 213–215 行），入口与概念同名；动词说出它做的事 | `preflight.sh`：R19 第 4.7 节为 `dispatch.sh check` 放弃过 preflight，「`--preflight` 在历史评论、Memory、旧文档里指认领，复用会造成本套自己的假朋友」 |
| `tests/skill-text` | 三道文字检查（含 `check_wiring.py`）共用的测试套件 | 被测子系统名，与共用模块同名（R19 第 2 节「测试套件」） | `tests/text-integrity`（R21a）与 `tests/wiring`（R19 第 4.6 节）各开一个：两个套件测同一个共用模块。R19 第 4.6 节 `check_wiring.py` 一行的 `tests/wiring` 改为本名 |
| **`## Moves`** | 票上的搬运清单小节 | 程序按字面找的小节名，与 `## Owns` 同类，登记进 `locations.py`（R18 第 928 行 W4） | — |

另两处沿用 R19 已定的名字：本文写 `locations.py`，不写 `anchors.py`（R19 第 4.6 节）；占位符写 `<effort>`（R19 第 4.9 节保留它）。

---

## 7. 对其他文件的待改项

本轮只写本文。下列文件与本文不一致的地方，以本文为准，由下次编辑那些文件的会话改；B0 spec 在写 Implementation Decisions 时按本文写，不照抄旧说法。

| 文件与位置 | 现文 | 应改为 | 依据 |
|---|---|---|---|
| R18 第 7.5 节表第 3、4、7 类与首段「每一类在它所查的对象建成的那一批转为不通过就失败」；第 50 行 | 这几类归 `check_wiring.py`，按批次转为失败 | 句型部分、第 4 类、第 7 类的逐文件部分归结构 lint，B0 起失败、靠例外表到期 | 本文第 4.4 节 |
| R19 第 7 节子命令 6 行的 kind `replace` 与首段「写成 `replace` 行（R21a 第 3.4 节）」 | `replace` | `renames.tsv` 里写 kind `text` | 本文第 3.5 节 |
| R19 第 7 节注意事项第 1 条「`token key.md` 只在 `exe-release` 的文字里替换」 | 只是说明 | `renames.tsv` 那一行第 4 列写 `mmw-v2/skills/exe-release/**` | 本文第 3.5 节 |
| R19 第 4.6 节 `check_wiring.py` 行的 `tests/wiring`；第 4.6、4.9 节 | — | `tests/skill-text`；补第 6 节各名 | 本文第 6 节 |
| R20 第 3 节 T1 末句「清单之外、出现在目标文件里的句子都算新写」 | 清单外的句子算新写 | 「清单之外的句子必须由 `new` 行列出并写出处，否则逐字搬运检查报 `ADDED`」 | 本文第 3.1、3.2 节 |
| R20 第 7 节 K8、K12、K13、K16、K18、K22 的「方式」列 | 连线检查某类，或机查 | 本文第 4.4 节对照表 | 本文第 4.4 节 |
| R19、R20 里的「R21a §x」 | 指草稿 | 指本文；两份文件引用的第 0 节第 1、4 条，第 3.4、3.5 节，本文保留了同样的节号与话题 | — |

R18 第 17 节 D9 引用的文件名 `R21-text-integrity-checks.md` 就是本文，不必改。

---

## 8. 本轮读了什么、没读什么

**读了**（全文或所需部分）：

- R21a 全文（本文的草稿）。
- `R19-naming-table.md` 全文。
- `R20-writing-style-guide.md` 第 0–3 节、第 5 节（第 188–547 行）、第 7 节。
- `R18-mmw-architecture-v2.md` 第 48–52 行、第 7.5 节（第 952–975 行）、第 928 行、第 10 节 B0–B2 行、第 16 节、第 17 节与审查记录开头、第 4.1 节表中 `ui-acceptance`、`design-pages`、`write-screen-contract`、`retro`、`exe-release`、`code-checkers` 各行。
- `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 60–206 行（第 4 步末、第 5–8 步与 `<issue-template>`）。
- `verify-ticket.py` 第 436–500、690–720、1215–1230、1325–1365、1820–1911 行；`grep` 其中 `section(`、`markdown_h2` 的全部调用。
- `dispatch.sh` 中 `into` 的全部出现（`grep`）。
- `SKILL-SET-RULES.md` `### Vocabulary`（第 72–82 行）；`docs/contexts/toolbox/CONTEXT.md` 第 210–215 行；`docs/contexts/ui-acceptance/CONTEXT.md` 第 297–302 行。
- `mmw-v2/tests/lib/` 全部文件的文件头；12 个 `run.sh` 里调用共用检查的行；`write-screen-contract/run.sh` 第 1–40 行。
- 第 4.3 节表里每一处的原文行；`retro/SKILL.md` description 与第 186 行；四份 `*-reviewer.md` 的首行；pstack `skills/principle-*/SKILL.md` 的 description 行。
- `git log` 中 `Squashed '` 与 `as 'mmw-v2/upstream` 的提交信息；`git status` 与 `git ls-files` 对研究文件与 pstack 快照的结果。
- 票 #589 的标题与正文开头（本仓票的语言与小节写法）。

**本轮自己跑的计数**：`mmw-v2/skills/` 下 `.md` 的 U+2014 与 U+2013（160 处、25 个文件）；`## \d` 形式的跨文件引用（1 处，另 1 处是同文件引用）；今天的套件数（12）。

**没读**：

- N1–N11 各份清点、R12、R13 全文；本文只用到 R14 与 R18 已归纳的结论，R13 E8 取自 R21a 的阅读。
- `verify-ticket.py` 的其余部分；`gate-check` 的账本解析取自 R21a 的阅读（`mmw-v2/merge-notes/unlazy.md` `### scripts/lib/gates.mjs`）。
- `docs/research/workflow-compare/exemplars/`：仍不存在。
- `check_wiring.py`、`locations.py`、`pstack-rewrites.tsv`：尚未写，第 3.5 节导入票一条与第 4.4 节的分工是对 R18、R19 文字的推断与重新分配。
- 第 2 节外部候选：沿用 R21a 那一轮读的实现文件与数字，本轮没有重查。

**推断清单**：

- 断句不准不会造成漏报（第 3.3 节），由比较的对称性推出，第 3.9 节第 2 条的变异测试实测。
- 第 4.3 节的命中来自临时正则，正式实现会有出入；`until` 批次按 R18、R19 该处文字的去向推出，其中 `code-checkers` 两处与 `exe-release` 三处 R18 没有单列。
- 收尾复核时 base 可能领先 `origin/<into>`（第 3.1 节 Q3 只在本票分支上跑的理由之一）；本轮没有核实 `advance` 何时推送。
- `pstack-rewrites.tsv` 的格式（第 3.5 节）。

---

## 审查记录

第一轮审查共 17 条，逐条回原文或跑命令核实。

1. **B0 票的 Read first 读不到未跟踪的研究文件，「本文」没有路径**（blocking）——属实，采纳。核实：`git status --short docs/research/workflow-compare/reports` 显示 L7、R14、R18、R19、R20、R21a 都是 `??`（另有 R12、R13、R19a、R20a、R20b 也是）；pstack 快照已跟踪。改在第 5.1 节「前提」：切票前把本文与 R18、R19、R20、L7 提交到 base 分支；五张票的 `## Read first` 都写完整路径加节名，不写「本文」。
2. **票草案用粗体标签，不合 `<issue-template>`；缺 `## Parent`；Blocked by 写进正文；What to build 满是实现路径**——属实，采纳。核实：`verify-ticket.py` 第 441–460 行 `section()` 只认 `## <heading>` 行，第 496 行附近 `owns_globs` 用 `section(body, "Owns")`；`to-tickets` 第 145 行草稿头行含 `BLOCKED BY:`，第 162–204 行模板，第 206 行「Avoid implementation file paths」。改法：第 5.2–5.6 节五张草稿都按草稿文件原样写（头行 `TITLE:`、`LABELS:`、`BLOCKED BY:`，`---`，正文六个 `## ` 小节）；What to build 只写行为与命令名，路径留在 `## Owns` 与 `## Seam`。第 3.2 节写明 `## Moves` 放在 `## Owns` 之后、`## Acceptance criteria` 之前，并核实两种顺序都不截断账本、判据结果不回写正文（第 1882–1911 行）、`--lint` 不列举小节。
3. **改名接口与 R19 第 7 节对不上**——属实，采纳。核实：R19 第 7 节（第 314–369 行；审查意见写的第 387 行超出该节，节内容不受影响）kind 只有 `path`、`token`、`replace`，注意事项写明 `key.md` 只在 `exe-release` 替换。改在第 3.5 节：kind 收成 `path`、`token`、`text`，`token` 与 `text` 可带 `scope`；R19 的 `replace` 行在 `renames.tsv` 里写作 `text`，与清单的 `replace` 指令分开（第 3.5 节说明两者含义不同）；删去 `skill`、`heading`、`title` 三种；Q3 豁免本票全部 `rename` 行。R19 的相应改动列入第 7 节。
4. **同批改名与整文件目标在收尾复核时误报**——属实，采纳。核实：`to-tickets` 第 90 行原文；R21a 第 3.8 节只列源范围与目标位置不重叠。改在第 3.8 节第 2–4 条与 `--lint-drafts` L4、L6、L7：整文件目标占住该文件全部位置；文字含同批改名旧名的票必须自己带那行改名；带同一行改名的票不能同时跑。选这一种而不是「收尾复核时套用同批改名」，理由写在第 3.8 节「放弃的备选」。
5. **重复句子没有一一配对**——属实，采纳。核实：R21a 第 3.1 节只写「出现」「来自」。改在第 3.1、3.3 节：按多重集合一一配对，`NOT-REMOVED` 比较出现次数；第 3.9 节第 1 条与票 `b0-verbatim-compare` AC5 加计数夹具。同时发现并改了一处相关漏洞：整文件 `copy` 到已有文件（回原文）时，「`from` 时已在这个位置」的豁免会放过本该删去的句子，第 3.1 节改为整文件目标不适用该豁免，AC7 判定。
6. **变异与规范化矛盾；变异只做在整文件 copy 上**——属实，采纳。核实：R21a 第 3.3 节标题规范化去掉粗体、编号、末尾标点，第 3.9 节变异清单含「加粗」「改标点」「改数字」。改在第 3.9 节第 2 条：变异只取句子单元正文、不取块首词，写明理由；另加 20 次变异施加在「拆段成步骤」的 `move` 夹具上。夹具改用提交的副本（`advisor/SKILL.md` 只有 13 行，另加 `retro/SKILL.md`），不再留给 worker 选。
7. **清单语法里 worker 要猜的六处**——属实，采纳。逐处定了规则（第 3.2、3.4 节）：`replace` 在规范化文字上匹配；`drop` 句首匹配多于一句退出 2；三种位置的范围；`new <目标> title "<Title>"`；整文件 `move`/`copy` 自动带路径映射；只有一侧能解析的路径判 `CHANGED`。
8. **`new` 没有出处字段；R20 T1 与 R21a 说法相反**——属实，采纳。核实：R20 第 97 行 T5、第 99 行 T6、第 82 行 T1。改在第 3.2 节：`new`、`replace`、`drop` 都带必填出处；不带整句的 `new` 只用于 R20 第 5 节标「新写」的节，出处须写出那一节，`--lint-drafts` L3 查；经它放行的句子逐行打印为 `NEW`。R20 T1 的改写列入第 7 节，因为本轮只写本文。
9. **结构 lint 与连线检查的分工在各文件里互相矛盾；K8、K12、K18、`## N` 没覆盖**——属实，采纳。核实：R18 第 954–969 行与第 50 行、R20 第 7 节 K8、K12、K13、K16、K18、K22。改在第 4.4 节：加 R20 K1–K38 → 检查与规则的对照表，并要求 B0 spec 写进 Implementation Decisions、`check_wiring.py` 那张票不实现移走的部分；K12 由 `playbook-reply` 查「恰好一个」；`## N` 并入 `numbered-cross-reference`（本轮补扫到 `retro/SKILL.md` 第 186 行一处，已列入第 4.3 节）；K8 加 `no-dash` 规则，只查新组件，理由是本轮数出能力技能里已有 160 处、25 个文件，写在第 4.2 节；K18 标为判断，理由写在第 4.2 节。
10. **例外表按路径匹配，改名后失效；按片段匹配会掩盖新违规**——属实，采纳。核实：R19 第 4.5 节 `edit-pages.md`、`driving.md`、`key.md` 都在 B1 改名。改在第 4.5 节：读 `docs/specs/*/renames.tsv` 的 `path` 行映射旧路径；一行只抵消一条发现。
11. **Q3 会把子树拉取报出来；`MMW_BASE_REF` 未设时走向不明**——属实，采纳。核实：`verify-ticket.py` 第 1871–1872 行只在 `into` 为字符串时设 `MMW_BASE_REF`；`git log` 里子树提交信息都以 `Squashed '<prefix>/'` 开头。改在第 3.1 节：分支上有这类提交时该前缀不做 Q3 并写进成功行；base 取 `--base` 再取环境变量，都没有时退出 2。另核实 `dispatch.sh` 第 871、1017 行夜里起的 worker 与 `adopt` 都写 `into`，所以流水线里的运行都有 base。同时把 R21a「收尾复核时 HEAD 就在 base 上、diff 为空」这一推断换成可核实的判据：Q3 只在当前分支是本票 `issue-<n>` 时跑。
12. **票 1 的 AC1 写死 13，且是全树扫描**——属实，采纳。核实：今天 12 个 `run.sh`；R19 第 188 行 `tests/wiring`。改在票 `b0-shared-lints` AC1：不写定数，断言数目大于 12 且每个都调用入口；说明 B0 里没有别的票新建套件（`check_wiring.py` 并入 `tests/skill-text`），若 B0 spec 另加套件就把它移到最后一张票。`check_wiring.py` 那张票被 `b0-structure-lint` 阻塞的边写入第 5.1 节。另把 R21a 票 3 的全树 `--batch B0` 判据移到 B0 最后一张票上，同一条 `to-tickets` 第 90 行的理由。
13. **复杂度**——属实，采纳。删去 R19 没用到的三种改名 kind；`MISPLACED` 并入 `DELETED` 的附注；三道检查共用一个套件 `tests/skill-text`；`--lint-drafts` 拆成单独一张票，并把 Q3 与 `--ticket` 也拆出，逐字比较那张票的判据从 10 条减到 9 条且不再含读票与分支比较。票数由 3 张变 5 张，每张更小；拆法理由写在第 5.1 节。
14. **新名字没经 R19，skeleton 撞义；`anchors.py` 已改名；R18 D9 引用的文件名悬空**——属实，采纳。核实：`docs/contexts/ui-acceptance/CONTEXT.md` 第 302–303 行 **skeleton**；SSR 第 74 行；R19 第 184 行。改名：结构 lint 为 `check_component_structure.py`、例外表 `structure-exceptions.tsv`、词条 **structure lint**；套件 `tests/skill-text`；另发现 R21a 的 `preflight.sh` 与 R19 第 4.7 节放弃 preflight 的理由冲突，改为与词表 **shared lints** 同名的 `run_shared_lints.sh`。这些名字列在第 6 节，待补进 R19。全文改用 `locations.py`。本文以 `R21-text-integrity-checks.md` 定稿，R18 D9 的引用因此成立。
15. **规则表与命中数有出入；mode 路径写死；frontmatter 只用标准库**——属实，采纳。核实：`retro/SKILL.md` description 写「the dispatch skill's」，无反引号；R19 第 8 节待定；`check_own_skill_frontmatter.py` 文件头用 PyYAML 经 `uv run`；pstack 原则 description 带引号。改在第 4.1、4.2 节：`description-content` 与 `capability-next-step` 都认不带反引号的技能名；mode 目录取自常量 `MODE_DIR`，注明依赖 R19 第 8 节；frontmatter 用 PyYAML，两个脚本带 PEP 723 块，`CHECK:` 用 `uv run`。
16. **负控覆盖不到 `--ticket`**——属实，采纳。核实：R21a 第 3.9 节与票 2 Seam 只走 `--manifest`；本仓 `tests/retro/test_retro.py`、`tests/dispatch/test_status.py` 有假 `gh` 的先例。改在第 3.9 节第 4 条与票 `b0-verbatim-ticket` AC2。
17. **票 3 留给 worker 的未决项：5 处编号引用的批次、AC5 写死行号**——属实，采纳，批次与审查意见的例子不同。核实：R19 第 4.5 节 `driving.md`、`key.md` 的改名批次是 B1，不是 B2；`code-checkers` 第 6、8 步在 B1 搬进 P9（R18 第 4.1 节）。改在第 4.3 节：表里给出每一处的 `until` 与依据，5 处都是 B1；AC5 改为按路径、规则 id 与原文片段比，不比行号。
