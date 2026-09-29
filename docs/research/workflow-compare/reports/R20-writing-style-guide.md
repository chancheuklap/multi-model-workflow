# R20 MMW 技能写作规范：pstack 的结构，mattpocock 的写法

这份规范是 R18 第 17 节 D9 所说的「写 spec 之前定稿的写作规范」。它给三类读者用：

- 写 spec 与范本（`docs/research/workflow-compare/exemplars/`）的人或 agent：照第 5 节的模板定每份文件的骨架，照第 3 节决定哪些句子搬、哪些句子新写、哪些句子删。承载理解的新句子（所有权行、首段、立场句、`**Why:**`、`Done when`、`**Reply:**`、连接句）由这类读者事先写成整句，列进票的 `## Moves`（T5）。
- 按票搬文字、写新文字的 worker：只照票上的 `## Moves` 做。搬运只做第 3 节列出的机械改写；`new <目标> "<整句>"` 行给出的整句逐字写出；只有票上点名了范本段落的 `new <目标>` 位置，worker 才照那段范本的写法自己起草（T5）。
- 审查这些票的 reviewer（Standards 轴与写作审查）：照第 7 节的清单逐条查，按规则编号报 finding。

它合成两份材料：`R20a-pstack-text-structure.md`（下称 R20a，pstack 的文本结构）与 `R20b-mattpocock-writing-style.md`（下称 R20b，mattpocock 的写法）。两层的分工是：

- **结构层取自 pstack**：一份文件有哪些节、什么顺序、标题几级、步骤长什么样、怎样点名别的组件、多长。它让全套技能「由内而外整齐统一」，改一处时知道去哪里找（用户本轮要求 1）。
- **写法层取自 mattpocock**：每一节里怎样交出目的、立场、理由、判断标准，用什么词。它决定 agent 读完后想得多深、覆盖多广（用户本轮要求 1；R20b 第 0 节「深度」「广度」的定义）。

两者冲突的地方，第 2 节逐条裁决并写明理由。

---

## 0. 结论（先读这里）

1. **MMW 自写的文字按第 5 节七种模板写**：mode、playbook（含长形态）、角色操作文件式 playbook、原则、能力技能、reference、给子代理或另起会话的简报。每个模板的每一节都标了结构出处（pstack）、写法出处（mattpocock）、以及这一节是「搬运」还是「新写」。
2. **上游原文不套模板。** mattpocock squash 提交 `5b1a4c51` 的技能与 pstack 导入的文件保持原文，只做 R18 第 4.3、8.2 节列出的改动（SSR L106、L111；R18 第 17 节 D9）。模板只管 MMW 自有的文字，以及把上游技能接进流程的连接句。
3. **搬运、新写、删除分开（第 3 节 T1–T9）。** 搬运的句子逐字带过去，只允许五种机械改写，与 R21 的逐字搬运检查一致。承载深度与广度的新句子（所有权行、首段、立场句、`**Why:**`、`Done when`、`**Reply:**`、连接句）由写 spec 或范本的人事先写成整句，在票的 `## Moves` 里用 `new <目标> "<整句>"` 列出，worker 照抄；不带整句的 `new <目标>` 只用在范本已给出这一节写法、票上点名了范本段落的位置（T5）。每句新写都要有出处，出处种类按 SSR L140（代码、tracker、记录过的运行、用户原话），另加 R18 与原文。所有权行与 `**Why:**` 找不到出处就不写；首段、立场句与 `Done when` 找不到出处时在票上记为未满足的验收项，不静默留空（T6）。源里不搬的句子逐句写成带理由的 `drop` 行（T9）。
4. **最重要的四条裁决（第 2 节）**：
   - 理由写在规则旁边（SSR L11），不采用 pstack「Tell it to do the thing and skip the reason」（`PS:skills/poteto-mode/playbooks/authoring-a-skill.md` L10）。X1。
   - 编号步骤只用在 playbook 和确实有先后的能力技能里；靠概念驱动的能力技能保持原形态，不改写成步骤清单。X2。
   - 能力技能以它交回什么结尾，不写「下一步」；下一步归 playbook（R18 第 4.5、7.9 节，取代 SSR 事实 7 与 L92）。SSR 那两处的改写必须先于或同于第一张适用这条的票落地。X13。
   - MMW 自写 playbook 的每一步都有粗体标题，也都有一行 `Done when`（R18 第 1.3 节；SSR L124）。X10、X17。
5. **规则编号**：`T` 搬运、新写与删除；`X` 冲突裁决；`S-G`、`W-G` 通用结构与写法；`N` 点名写法；各组件的结构规则与写法规则分别是 `S-M`/`W-M`（mode）、`S-P`/`W-P`（playbook）、`S-O`/`W-O`（角色操作文件式 playbook）、`S-R`/`W-R`（原则）、`S-C`/`W-C`（能力技能）、`S-F`/`W-F`（reference）、`S-B`/`W-B`（简报）。票与审查按编号引用。
6. **机械可查的与要判断的分开标。** 第 7 节清单每项标「机查」或「判断」；每个机查项写出对应的脚本、规则 id 或类别，以及它在票的哪条 `CHECK:` 或哪个预检里跑。B0 的检查落地之前，不按本清单审查搬家票；例外表里登记且未到期的违规不报 finding。
7. **没有需要用户决定的事项。** 本文的取舍都是写作与结构上的工程决定，理由写在各条旁边。与用户有关的只有结果：按本文写的票，搬过去的句子不会被改写，承载理解的新句子在切票时已经写定，worker 不能随意改写它们，每句都能追到出处。

---

## 1. 出处写法与标注

| 缩写 | 指什么 | 怎样打开 |
|---|---|---|
| `SSR L<n>` | `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（本仓库工作树现行版本；R18 §7.9 把它搬到 `mmw/references/skill-set-rules.md`） | 直接读；本轮用 `cat -n` 核对了全文行号 |
| `WFA L<n>`、`SM L<n>` | squash 原文 `skills/productivity/writing-for-agents/SKILL.md`、`SKILL-MECHANICS.md` | `git show 5b1a4c51:skills/productivity/writing-for-agents/<file>`；本轮核对了全文行号 |
| `UP:<bucket>/<skill>/<file> L<n>` | mattpocock squash 原文 | `git show 5b1a4c51:skills/<bucket>/<skill>/<file>` |
| `PS:<path> L<n>` | pstack 快照 `docs/research/code-landing-refs/pstack/<path>` | 直接读 |
| mode | `PS:skills/poteto-mode/SKILL.md` | 同上 |
| R18 §x、R18 D<n> | `R18-mmw-architecture-v2.md` 的节与第 17 节的决定 | 无 |
| R20a <id>、R20b <id> | 两份材料里的规则编号（R20a 的 G1、P3、C3 等；R20b 的 M1–M15、冲突 C1–C12） | 无 |
| R21 §x | `R21-text-integrity-checks.md`（逐字搬运检查与结构 lint 的设计） | 无 |

标注：「推断」＝原文没有直说、由写法归纳的判断；「决定」＝本文做的工程取舍，理由写在旁边。其余都是原文。

---

## 2. 两层冲突的裁决

R20a 第 10 节与 R20b 第 2 节各列了冲突，都没有裁决。下表是本文的裁决，每条一个编号，票与审查按编号引用。

| # | 冲突 | 裁决 | 理由 |
|---|---|---|---|
| X1 | 理由写不写。pstack：「Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one.」（`PS:skills/poteto-mode/playbooks/authoring-a-skill.md` L10）。mattpocock 与 SSR：「next to a rule, the reason for it」（SSR L11） | 写。一条理由如果能说出「步骤没覆盖的某个情况，agent 有了它会怎样做得不同」，就写在规则同一句或下一句（SSR L11 句子测试）；说不出的，只是证明规则合理的句子，删。理由不另开一节，例外见 W-C3 | 理由是 agent 把规则推到没列出的情况的唯一途径（SSR L11 事实 1）。pstack 自己也写理由：`bug-fix.md` L5 整段是纪律与理由，原则有 `**Why:**`（R20a R2）。它那句政策与同段「Keep only prose that changes a decision」合起来，意思与 SSR L11 的测试相同（R20b C1）。R18 §3.3 P11 已因同一冲突改用 MMW 版 `authoring-a-skill` |
| X2 | 步骤化程度。pstack playbook 用编号步骤，并原样抄进待办（mode L117）；mattpocock「Direct, then trust」（SSR L14），`grilling` 全文没有编号步骤 | 编号步骤只用在 playbook，以及确实有先后的能力技能。靠概念驱动的能力技能（例：`UP:productivity/grilling/SKILL.md` 的 design tree、frontier、rounds）保持原形态 | 把概念驱动的技能改写成步骤，会让流程 rigid、brittle（SSR L14、L43），这是 R20b 最担心的破坏。pstack 自己的能力技能也有八种形态，不要求统一（R20a C3） |
| X3 | 禁令。pstack 多用「Never / Only / No」与「X is not Y」句（R20a G3）；mattpocock 先写正面目标（WFA L74） | 先写要做的行为。禁令只作无法正面表述的硬护栏，并在同一句或相邻句写出正面目标或理由。「X is not Y」是定义句，不是禁令，照用 | WFA L74：禁令会把被禁的行为拉进上下文。pstack 的禁令多数已带理由（`bug-fix.md` L5「Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship.」），实际差距只在没有理由的禁令串（R20b C3） |
| X4 | 比喻。pstack `unslop` 规则 26、32 禁「harness」「surface」和比喻动词；mattpocock 用 **fog of war**、**tracer bullet**、「test surface」 | 按 SSR L77：比喻除非是 leading word，否则是 finding。领域里有固定意思的术语（test harness、tracer bullet、blast radius、fog of war）保留；只为生动而用的比喻动词（「rides along」）改成直说。MMW 自写的技能文本不套用 `unslop` 的禁词表 | `unslop` 的词表会禁掉上游已用的既定术语（R20b C4）。用户 `~/.claude/CLAUDE.md` 规则 7 禁 mannered prose，与 SSR L77 的界线一致 |
| X5 | 标点。pstack 禁长破折号，也禁句中冒号（mode L101–103；`unslop` 规则 13、14）；mattpocock 用「术语: 定义」冒号句（`UP:engineering/tdd/SKILL.md` L20） | 长破折号 U+2014、短破折号 U+2013 一律不用。冒号可以用，条件是冒号后面的内容展开冒号前面那一句（列表、例子、定义、理由）；两个不相干的判断不用冒号连 | 两边都禁长破折号；本仓库的 `check_upstream_em_dashes.py` 只查上游目录（根 `AGENTS.md` `## Commands`），MMW 自有文字的检查见 K8。冒号：pstack 通过 mode L26（「Any prose surface → the **unslop** skill. … Agent-facing prose also follows the **create-skill** skill」）与 `unslop` 规则 14（`PS:skills/unslop/SKILL.md` L37「Not as mid-sentence connectors」）对技能文本同样禁句中冒号；MMW 不采用这条，因为 leading word 的定义句依赖冒号（R20b M6），SSR 自己在 L3、L11 也这样用（R20b C5） |
| X6 | 句子密度。pstack「One thought per sentence」（mode L101）；mattpocock 常把规则和理由写在一句里 | 一句一事；一条规则加它的理由算一件事，可以写成一句，超过就拆 | R20b C6；SSR L55「the body is written plainly」 |
| X7 | description。pstack 能力技能是「动作句 + Use for 触发」，原则是「Apply when … . <要点>.」；SSR L67 只写触发 | MMW 自有技能按 SSR L67：「它是什么」加各触发分支。原则的 description 保留「Apply when <情境>. <规则摘要>.」 | 原则是文件不是技能（R18 §5），它的 description 不进任何宿主的技能列表；mode 索引的「何时适用」取自它的第一句（R18 §2.2 `## Principles`，由连线检查第 5 类核对） |
| X8 | 简报放哪。mattpocock 写在调用步骤里（`UP:engineering/code-review/SKILL.md` 第 4 步）；pstack 放 `references/`，即使每次都用（R20a F1） | 几行的简报写在步骤里；要整份原样交给另一个代理的长模板单独成 reference | SSR L28：每次都读的 reference 是 fragment，应内联；但整份交给另一个代理的文件是 hand-off 的载体，不是 jump（SSR L27）。R18 §1.4 advisor 例外与审查记录第 34 条已按此处理 |
| X9 | 引用别的组件的某一步。pstack 按编号（mode「(Feature step 3)」）；SSR L81 按标题 | MMW 自写的文字一律按标题引用，文件内也一样 | 编号一重排，引用就指错（R20a P2）。MMW 自写 playbook 每步都有粗体标题（X17），按标题引用没有代价；只留一种写法，比「文件内可以用编号」更容易查 |
| X10 | 怎样写「完成」。mattpocock 每步有完成判据（WFA L45–52），MMW 写成 `Done when` 行（SSR L124）；pstack playbook 以 `**Reply:**` 收尾，步骤没有判据 | 两者都写：每一步末尾一行 `Done when <条件>.`，整份 playbook 末行 `**Reply:** …` | 两者回答不同的问题：`Done when` 说这一步何时停，`**Reply:**` 说交回什么（R20b C10）。步骤会原样抄进待办（mode L117），判据随步骤进待办，在 agent 最想宣布完成的时刻就在眼前 |
| X11 | 开头写什么。pstack 用粗体所有权行；mattpocock 开头交出目的、下游、代价（SSR L11） | 所有权行在前，然后是可选首段，写目的、下游、代价与立场句 | 所有权行说谁决定什么，首段说为了什么，两者不重叠（R20b C11）。pstack 的所有权行后本来就有可选纪律段（R20a P2 第 3 项），不必新增节（R20a C7） |
| X12 | 脚本调用写多少。pstack 写「它做什么」一句（R20a S1）；SSR 事实 2「Text that narrates what a script does spends the agent's attention on work the agent does not do」 | 写命令、何时跑、每种结果之后做什么（SSR L59）。「它做什么」只在 agent 的下一个决定依赖它时写（例：它会认领票，所以只跑一次）。脚本的输出是建议时，同一句写明判断归谁 | SSR L12、L59 是 MMW 的规则；pstack `show-me-your-work` L38「It stamps `ts`, writes the header …」这类叙述对 agent 的决定没有作用。建议与判断的分界取自 R20a S2（`PS:skills/poteto-mode/playbooks/worktree-cleanup.md` L6「The bucket is advice, not permission.」）：不写这一句，agent 会把脚本的分类当成许可直接执行 |
| X13 | 能力技能怎样结尾。SSR 事实 7（L17）与 L92：「Each skill ends by naming what comes next」；R18 §4.5：能力技能不写「下一步」「谁调用我」 | 按 R18：能力技能以交付物结尾（`## Output` 或 `**Reply:**`）；下一步写在 playbook 里。落地先后见表后「X13 的先后」 | R18 §7.9 已定把 SSR 这两处改为「一个技能的位置由 mode 路由表与 playbook 决定；能力技能以它交回什么结尾」，由 ADR 0032 记录。SSR 那两句原本防的漂移与断链，由连线检查第 2、7 类防住（R18 §7.9） |
| X14 | 标题大小写。`unslop` 规则 17 要 sentence case，pstack 23 条原则里 22 条的 H1 是 Title Case（R20a P13） | MMW 新写的标题一律用 sentence case。搬来的标题（含按 T2 第 3 种由源小节名变成的步骤标题）保持原样；确实要改成 sentence case 或祈使形式的，由写 spec 的人在清单里写 `replace`。导入原则的 H1 保持原文；mode 索引里的显示名与原则文件 H1 逐字相同 | 上游 mattpocock 的节名也是 sentence case（`## Plan, don't do`、`## Pick a branch`）。R21 §3.4 把大小写列为不允许的改写，worker 自行改大小写会被逐字检查报成 `CHANGED`，所以改动只能由 spec 写成 `replace`。显示名只有一个出处（R20a P14）；R18 §7.5 第 5 类现在只比「何时适用」与 description 第一句，显示名与 H1 相等要在写 `check_wiring.py` 时加进第 5 类（K11） |
| X15 | 步数上限。R20a 第 11 节建议 lint 查 3–9 步；R18 §3.3 P15 **Work a ticket** 有 11 步 | 不设硬上限。超过 9 步是审查问题：两步能否合并而不丢掉某个指针的目标 | P15 的第 4–8 步对应脚本记录的位置（R18 §3.3 P15「第 4–8 步是今天 `resume_at` 返回的 step 1 到 step 5」），合并会让 `where` 的输出失去目标 |
| X16 | 子代理参数。pstack 写 `subagent_type`、`readonly`、`model` 默认值（R20a C4） | 写角色与只读或可写，加一句理由；不写宿主参数名、模型名 | SSR L118 宿主中立；R18 §2.2 `## Subagents`：会话内子代理不指定模型，只读靠简报里的一句话 |
| X17 | 步骤首句加不加粗。R20a P3 建议「有一步超过三句就全部加粗」 | MMW 自写 playbook 的每一步都写 `N. **<Title>.**` | R18 §1.3：步骤标题就是指针 `mmw <slug>#<Step title>` 的锚点，跨文件按标题引用。取代 R20a P3 的条件式写法 |
| X18 | 点名 playbook 带不带路径。R20a G7 建议 `Run **<Name>** (`playbooks/<file>.md`).` | 只写粗体显示名；路径只在 mode 路由行写一次 | 名字到文件的对应只有一个家（SSR L17 事实 7）；连线检查第 2 类按路由表解析名字（R18 §7.5） |

**X13 的先后。** SSR 事实 7（L17「its closing section says what comes next」）与 `### Hand-offs` 第 5 条（L92「Each skill ends by naming what comes next, or the caller it returns to」）的改写（R18 §7.9 第 1 条），随 B1 把 SSR 搬进 `mmw/references/skill-set-rules.md` 落地（R18 第 10 节 B1 行；R21 §4.2 取舍末条「与 `SKILL-SET-RULES.md` 的冲突要在 B1 解决」）。它必须在第一张适用 S-C3 或 K16 的票之前落地，或者与那张票同票落地。在那之前，reviewer 不把 K16 报成 finding：Standards 轴按现行 SSR 审查（根 `AGENTS.md` `## External References`「the reviewer's Standards axis applies it」），而现行 SSR L92 与 S-C3 正好相反，两份规则会让同一句同时合规又违规。结构 lint 的 `capability-next-step` 对今天已有的句子靠例外表过渡（R21 §4.5），不受这条先后影响。

两边一致、不必裁决的（R20b 第 2 节末）：修剪（pstack「When in doubt, delete」与 WFA L81 的 no-op 测试）、环境是真相来源（WFA L79）、跳步写理由（mode L117 `skip: <reason>`）、结论带证据（mode L107）。

---

## 3. 搬运、新写与删除（T）

**T1 每一句要么是搬来的，要么是新写的，要么是登记过的删除。** 票上的 `## Moves`（搬运清单，R21 §0 第 1 条、§3.2）写明哪些源范围搬到哪里、哪些句子新写、哪些句子不搬；清单之外的句子必须由 `new` 行列出并写出处，否则逐字搬运检查报 `ADDED`。清单在切票会话里定稿，worker 不改清单（R21 §3.8 切票规则第 1 条）。

**T2 搬运只允许五种机械改写**（与 R21 §0 第 4 条一致）：
1. 空白与折行；
2. 列表符号与编号；
3. 标题与粗体步骤标题互换（源里的 `## Claim` 变成 `1. **Claim.**`），措辞与大小写照原样；
4. 路径与链接写法，前提是解析到同一个文件；
5. 票上逐行列出的改名（行取自用户过目的 `R19-naming-table.md`，R18 D9）。

另外允许在句末插入括注的原则点名 `(**principle-<slug>**)`（N2）。

**T3 以下都不是机械改写，都算新写**：改语序、改标点、改大小写、加减粗体、合并两句、拆开一句、翻译、换同义词、「润色」。spec 要改的句子，在清单里用 `replace` 逐条写出原句与新句（R21 §3.4），新句适用 T5。

**T4 规则与它的理由一起搬。** 可以把一段拆成几个步骤，不能把规则和紧跟它的理由句拆到两处（SSR L141「carrying each sentence that still applies across verbatim」；W-G2）。

**T5 新写只在模板标「新写」的位置；承载理解的句子事先写成整句；每句有出处。**

- **谁起草。** 所有权行、首段（目的、下游、代价）、立场句、`**Why:**`、`Done when`、`**Reply:**` 以及 T8 的连接句，由写 spec 或写范本的人事先写成整句，在票的 `## Moves` 里用 `new <目标> "<整句>"` 列出（R21 §3.2 `new` 行：「带整句：这一句可以新写，必须逐字出现」），worker 照抄。不带整句的 `new <目标>`（整个位置由 worker 起草）只用在范本（`exemplars/`）已经给出这一节写法的地方，并在票上点名对应的范本段落，worker 照那段的写法写。理由：这些位置正是交出 mattpocock 式深度与广度的地方（R20b M1、M3、M10），而逐字搬运检查只保证搬来的句子不被改，管不到新写的句子写得好不好（R21 §0 第 10 条）；只靠 reviewer 的 K27–K33 事后把关，等于把写法交给 worker 随意处理（用户本轮要求 1）。
- **出处种类。** 按 SSR L140：代码、tracker、记录过的运行、用户原话；另外是 R18 的某一节、某个原文文件的某一行、用户的决定（R18 第 17 节或 `shared.md`）。由写法归纳而不是原文直说的出处，标「推断」。交出目的、理由或立场的句子不需要一次失败的运行作依据，但句子本身要点名它针对的情况，情况是推断而非观察到的时在句中说明（SSR L140「it needs no failed run behind it, but it names its case, and says when that case is inferred rather than observed」）。
- **出处写在哪。** 票、`imports.tsv` 或 ADR 0032，不写进技能文件（SSR L52 的 sediment 表；R18 §5.1「出处……写进 ADR 0032，不进原则文件」）。
- **概念的作者或著作不算出处。** 它照 SSR L55、L75 写在术语定义旁（例：**Seam**, Michael Feathers），因为它能调出模型已有的理论；SSR L52 的 sediment 表明确把「the author of a concept」排除在外（W-G6）。

**T6 找不到出处时，按位置分两种处理。**

- 所有权行与 `**Why:**`：不写（R18 §3.2「所有权行只在有出处时写」；R18 §5.1「原文没有理由的不写 `**Why:**`」）。
- 首段、立场句与 `Done when`：不静默留空，也不编。写 spec 的人在票上把它记为未满足的验收项，补到出处后按 T5 写成整句。理由：这三处空着，K27（SSR L11 的开头测试）、K29、K31 必然不通过，留空等于让结构模板挤掉交出理解的句子；SSR L140 也说交出目的、理由或立场的段落只要点名它针对的情况即可，出处门槛比机制低。

两种情况共同的理由：「an agent guesses around a rule stated without its reason, but it generalises from an invented one」（SSR L140）。

**T7 上游原文不套本文的模板。** mattpocock 技能按 SSR L106–112 与 R18 §4.3 处理；导入的 pstack 文件只做 R18 §8.2 的机械改写，结构 lint 对它们只查 `### <Name>` 与 `**Reply:**`（R18 §7.5 第 7 类）。一个技能里上游的行少于一半时，就按 MMW 自有文本审（SSR L112）。

**T8 连接句是新写。** 把上游技能接进流程的句子（playbook 里点名它的那一步、它旁边的 reference、mode 触发行）按本文模板写，适用 T5，由写 spec 的人写成整句（SSR L110「Connect outside the upstream text first」）。

**T9 不搬的句子逐句登记。** 源范围里不搬的每一句，都在 `## Moves` 里写成 `drop <源> ["<句首>"] : <去处或理由>` 行（R21 §3.2；R21 §3.1 Q1「被 `drop` 的除外」）。被删的句子交出目的、理由或立场时，理由必须写出它原本指导的情况，以及删后由什么指导（SSR L142「Before cutting one, name the case it would have guided and what guides that case after the cut.」；W-G10），例如「guided a worker who picked the ticket up itself; entry Adopted ticket carries it」。只写「冗余」「重复」的 `drop` 行不能通过审查（K35）。

---

## 4. 通用规则

### 4.1 结构（S-G，取自 pstack）

**S-G1 标题层级按组件类型固定。**

| 组件 | 起始 | 下一级 | 再下一级 | 出处 |
|---|---|---|---|---|
| mode | `# <Name> mode` | `## <Section>` | 小节内用粗体段首标签；`###` 只用于 `### Imported triggers` 一处 | mode L11；R18 §2.2 |
| playbook | `### <Name>`（文件里没有 `#`、`##`） | `#### <Cluster>`（长 playbook） | 无 | R20a G1、P1；R18 §1.3 |
| 原则 | `# <Title>` | 无；小节用 `**Label:**` | 无 | R20a R2 |
| 能力技能 | `# <Name>` | `## <Section>` | `### <Sub>`（少用） | R20a C2 |
| reference | `# <Name>` | `## <Section>` | `### <Output section>` | R20a F1、F5 |

**S-G2 一句一事，句号结尾，陈述句或第二人称祈使句**（mode L101；`PS:skills/unslop/SKILL.md` L62）。一条规则加它的理由算一事（X6）。

**S-G3 用三种固定句式划界限**（R20a G3）：「X is not Y.」定义句；「Distinct from X, which ….」区分句，放在所有权行、首段或文件末尾；禁令句，写法按 X3。

**S-G4 粗体段首标签以句号结束，后面接新内容**（`PS:skills/unslop/SKILL.md` L39；mode L102）。例外：原则的小节标签以冒号结束（`**Why:**`）。

**S-G5 不用 U+2014、U+2013；冒号按 X5；正文段落不用箭头。** 箭头只用在 mode 触发行（S-M3），因为那是索引格式（R20a P8）。

**S-G6 frontmatter。** MMW 自有技能只有 `name`、`description`（根 `AGENTS.md` `## Commands` 中 `check_own_skill_frontmatter.py` 一行）；原则只有 `name`、`description`（R18 §5.1）；playbook、reference 没有 frontmatter（R20a P1、第 6 节首段）。

**S-G7 技能文本用英文**（SSR L78）。**S-G8 不点宿主、工具、runner 名**，能力差异写成能力（SSR L118、L120）。

**S-G9 长度参照**（统计取自 R20a；超出上限是审查问题，不是 lint）：

| 组件 | pstack 统计 | MMW 做法 |
|---|---|---|
| mode | 143 行 | R18 §2.2 估计 B2 后约 170 行 |
| playbook | 127–913 词 | 超过约 800 词，或任何一步超过约 150 词时，改用 `####` 规则簇：角色 playbook 按 5.3，其余按 5.2 的长形态（R20a P4，阈值为推断） |
| 能力技能 | 多数 35–115 行 | 超过 115 行时，先找能按分支拆出去的节（R20a C6，推断；SSR L15） |
| 原则 | 16–34 行 | 同 pstack |
| reference | 17–144 行 | 同 pstack |

### 4.2 写法（W-G，取自 mattpocock）

**W-G1 开头交出理解。** 在任何步骤之前，用两到五句说清三件事：这项工作要达到什么，谁接着用它的产出，产出错了或浅了对那个人意味着什么（R20b M1；SSR L11 的开头测试）。代价写成具体后果，不写重要性声明。实例：「A logic prototype that answers the wrong question is pure waste, so make the question explicit」（`UP:engineering/prototype/LOGIC.md` L20）。

**W-G2 理由写在规则旁边**，通过 SSR L11 的句子测试才写，按 X1 处理。实例：「Generate **3–5 ranked hypotheses** before testing any of them. Single-hypothesis generation anchors on the first plausible idea.」（`UP:engineering/diagnosing-bugs/SKILL.md` L90）。

**W-G3 立场句同时写出诱惑和替代动作**，放在诱惑出现的那一步（SSR L42；R20b M3）。实例：「If you catch yourself reading code to build a theory before this command exists, **stop: jumping straight to a hypothesis is the exact failure this skill prevents.**」（`UP:engineering/diagnosing-bugs/SKILL.md` L66）。只有态度、没有动作的句子（「be careful」）是 no-op。

**W-G4 先定方向再信任。** 写目标、约束、agent 会判断错的一两个点、完成判据；有能力的 agent 自己会做的动作不写（SSR L14、L43；R20b M4）。

**W-G5 判断点写成能失败的是非测试**，测试用粗体命名（R20b M5；SSR L62）。实例：「**The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through.」（`UP:engineering/codebase-design/SKILL.md` L63）。

**W-G6 用领域术语与 leading word。** 选词顺序：领域既有术语，然后是词典词，最后才造词（造词加粗，并用一句话定义）（SSR L75）。一个词只有一个意思，定义后全文不换同义词（SSR L74）。词的力度不够时换一个更强的词，不加解释（WFA L81）。定义领域术语时，能调出一套理论的，在定义旁写出作者或著作（「**Seam**, Michael Feathers」，SSR L55、L75）；这不是 SSR L52 所说的出处沉积，修剪时不删。容易被同义词替换的术语，在词表里配一行 `_Avoid_` 列出禁用的近义词（`UP:engineering/codebase-design/SKILL.md` L12、L22；R20b M6）。

**W-G7 完成判据清楚且要求高。** 用 every、nothing left、removing any one 这类穷尽的措辞（WFA L50、L52）；硬闸门写成「No X, no Y.」（`UP:engineering/diagnosing-bugs/SKILL.md` L57–66 的末句「No red-capable command, no Phase 2.」）。判据必须能失败（SSR L62）。

**W-G8 禁令配正面目标**，按 X3 处理（WFA L74；R20b M13）。

**W-G9 事实归 agent，决定归人，并写明人不在场时怎么办**（R20b M14）。能查到的事实自己查；只有人能做的决定才问人；每个问人的地方写出无人时的出路（用默认值继续并写明假设，或者停下）。实例：「Don't block on it; proceed with your ranking if the user is AFK.」（`UP:engineering/diagnosing-bugs/SKILL.md` L98）。MMW 的无人出路按角色写在 mode `## Autonomy` 与各角色 playbook 的 `#### Unattended outlets` 里（R18 §2.2），两处怎样分工见 W-O3；能力技能只写通用出路（W-C2）。

**W-G10 修剪时删 no-op、重复和缓存，保留交出理解的句子**（WFA L78–81；SSR L38–55）。删一句之前，说出它原本指导的情况，以及删掉之后由什么来指导（SSR L142）；搬家票里这句话写在那一句的 `drop` 行上（T9）。

**W-G11 容易误读的地方给成对的好坏例子**，用中性领域，并标明是例子（SSR L128–130；R20b M12）。

**W-G12 平级技能按名字组合**：点名技能和要它做的事，不复述它的规则（SSR L16、L95；R20b M9）。

**W-G13 标出决定结果的那一步。** 一份文件里有一步决定整个结果时，在那一步写明为什么它决定结果，并用强度足够的词要求投入（WFA L81「the fix is a stronger word」）。实例：「**This is the skill.** Everything else is mechanical.」与「Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**」（`UP:engineering/diagnosing-bugs/SKILL.md` L20、L22；R20b M1「对思考的作用」）。不在每一步都这样写：每一步都标，等于哪一步都没标（推断）。

### 4.3 点名写法（N）

MMW 自写的文字按下表点名别的东西；导入的文字保留原样，由 mode 的解析规则与 `references/pstack-names.md` 读懂（R18 §2.2、§8.3；R19 §4.5 把 `slots.md` 改名 `pstack-names.md`）。

| # | 被点名的 | 写法 | 出处与理由 |
|---|---|---|---|
| N1 | 能力技能 | `` the `<name>` skill ``，加上要它做的事；同一段再次出现时可写 `` `<name>` ``；让人输入时写 `/<name>` | SSR L116、L118；pstack 的粗体写法（`the **how** skill`）不采用，SSR 已有定法 |
| N2 | 原则 | 句末括注 `(**principle-<slug>**)`，放在它改变的那个决定所在的句子末尾；本地限定或本地后果写在这一句本身或下一句 | R18 §1.3「MMW 自写的文字只用 `**principle-<slug>**`」；R20a G7、P3；R18 §5.1「点名一次，加一句本地限定或本地后果」 |
| N3 | playbook | 粗体显示名 `**<Display name>**`；「Run **<Name>**.」表示转交 | X18；pstack `bug-fix.md` L13「Run **Opening a PR**.」 |
| N4 | playbook 的某一步或某个规则簇 | 同一文件内：`**<Step title>**`、`` `#### <Cluster>` ``；跨文件：`**<Step title>** in **<Playbook>**` | X9；SSR L81 |
| N5 | 步骤指针 | `mmw <slug>#<Step title>` 或 `mmw#<mode 小节名>`，只出现在脚本文字、唤醒、启动提示词与 `roles.json` 里，只指向 MMW 自写的 playbook 与 mode | R18 §1.3、§7.8 |
| N6 | mode 的小节 | 在 mode 与 playbook 内写 `` mode `## <Section>` ``；能力技能与原则不点名 mode | R18 §4.5、§5.1 的方向规则（原则与能力技能不向上指） |
| N7 | 本技能的 reference | `references/<file>.md`，相对技能根目录（playbook 也相对 `mmw` 技能根目录，不写 `../`），并写明打开它的条件与用法（整份交出、填占位、只读某节） | SSR L25、L116；R20a C7 |
| N8 | 别的技能的文件 | `` the `<skill>` skill's `references/<file>.md` `` | SSR L95 |
| N9 | 脚本 | 一个文件里第一次出现时写出解释器与相对所属技能根目录的路径：`` `bash scripts/<file>.sh <subcommand> <args>` ``、`` `python3 scripts/<file>.py <args>` ``（占位用 `<name>`）；别的技能的脚本前面加 N8 式的归属（「the `verify-ticket` skill's `python3 scripts/issue_tree.py <n> --root ticket`」）。一句「Commands of <…> are named bare below.」可以代替第一次的全称，声明里同样写出解释器与路径。之后在同一文件里用短名 `` `<file> <subcommand>` ``。全称在任何位置都可以用，所以搬来的句子保留原来的全称，不为统一改短（T2）。只写这一步用到的开关；输出是建议时，同一句写明判断归谁（X12） | R20a S1、S2、S3；SSR L59（完整开关表留在脚本的 `--help`）。解释器与路径：范本 `exemplars/` 各份一致这样写（`work-a-ticket.md` 的声明句，`write-a-spec-and-tickets.md` 第 8 步，mode `## Re-entry` 第 3 步搬来的全称），声明句的来源是 `implement` L8；理由是 `mmw-v2/skills/verify-ticket/scripts/issue_tree.py` 与 `events.py` 没有执行位（`ls -l` 核实），只写路径就跑不起来，而几种写法并存时 worker 照抄会各写各的 |
| N10 | 程序读的名字（事件、label、字段、输出行、被指针指向的标题） | 逐字照抄，不为文风改名；要改就走 R19 改名表与迁移，并在同一次改动里 grep 出所有出处一起改 | SSR L76、L143；R19a §0 第 6 条 |
| N11 | 一张票下面开出的子 issue | MMW 自写的文字一律叫 child（命令 `--open-child`、规则簇 `#### Opening a child`、reference `child-issues.md`）；只有说 tracker 自身的结构时才写 native sub-issue（例：`--publish` 把票发成 spec 的 native sub-issue）。搬来的句子里指子票的「sub-issue」由 spec 逐句写 `replace` 改成「child」，不是 `rename` 行 | 范本 `work-a-ticket.md` 全文与其注解「全文通用的机械改名」表末行；`verify-ticket` 范本 `## Publish a spec or a batch` 保留 native sub-issue；R19 §4.5 `sub-issues.md` → `child-issues.md`、§4.8 `--sub-issue` → `--open-child`；W-G6 一词一义 |
| N12 | 用户的规则 | 写「`shared.md` rule N」。mode 在 `**User rules.**` 第一次出现处定义一次：宿主在每个会话开始时加载的用户规则，源文件是 `shared.md`，规则编号 1 至 15 分在 `## Who decides what`、`## How to report`、`## How to work` 三节下；playbook、原则与能力技能不重新定义，也不复述规则内容（W-M1） | 范本 `exemplars/mmw/SKILL.md` `**User rules.**` 与其注解；根 `AGENTS.md` `## Commands` 的 install 行（`~/.claude/CLAUDE.md` 指向 `mmw-v2/prompt/shared.md`，其余宿主的 AGENTS.md 由 `render.py` 生成）；理由：读 mode 的 agent 看不到叫这个名字的文件（S-G8、W-G6），文件开头另有 1 至 5 的前言编号，所以要写明节名 |

---

## 5. 模板

每个模板先给骨架，再用一张表标出每一节的三样东西：**结构**（取自 pstack 的哪里）、**写法**（取自 mattpocock 的哪里）、**来源**（搬运还是新写；新写的要写出处要求）。表里标「新写」的位置，凡属 T5 列出的承载理解的句子，都由写 spec 或范本的人写成整句进 `## Moves`，worker 不自行起草。骨架里的英文是 MMW 技能文本的实际形状；尖括号是占位；方括号是可选节。

### 5.1 mode `SKILL.md`（`skills/mmw/SKILL.md`）

```
---
name: mmw
description: <What it is>. Use in <branch>, when <branch>, or when <branch>.
---

# <Name> mode

## Non-negotiables
<Opening rule on citing principles.>
- <Observable condition> → <destination>. [<one or two qualifying sentences>] [(**principle-<slug>**)]
### Imported triggers                      (only when pstack trigger lines were imported)

## Principles
<How to read this index.> <Citation parsing rule.>
**<Group>**
- **<Display name>** (**principle-<slug>**). <When it applies>.
<User rules line: shared.md rule numbers and when each applies.>

## Autonomy
**<Bold lead-in>.** <...>

## Re-entry
1. **<Title>.** <...>

## Subagents
## Writing the reply
[## Comments]                                 (only if imported)
## Playbooks
<Execution protocol.> <Aliases.> <No match.>
- **<Name>.** <Task type>. [<User's words>.] Distinct from <Name>, which <...>. `playbooks/<file>.md`.
- <Direct capability row> → the `<name>` skill. Distinct from <...>.
<Private playbooks sentence.>
```

| 节 | 结构 | 写法 | 来源 |
|---|---|---|---|
| frontmatter | 只有 `name`、`description`（S-G6；R18 §2.1：不带开关，H2） | description 按 SSR L67：一句「是什么」加触发分支，leading word 放在最前（WFA L16） | 搬运：R18 §2.1 已定的原文 |
| `# <Name> mode` | mode L11 | 无 | `mmw`（R18 D10） |
| `## Non-negotiables` 首段 | mode L15 | 无 | 搬运：mode L15，带 R18 §2.2 标注的一处改写 |
| 触发行 | mode L19–35 的「条件 → 技能」（R20a M3） | 条件写成可观察的情况，优先用原 description 里的用户原话（R20b M7）；立场与理由留在被指向的组件里，触发行至多一两句限定（R20b 附表「mode」行） | 搬运：每行的出处见 R18 §2.2 表的「来源」列 |
| `### Imported triggers` | R18 §2.2 | 无 | 搬运：pstack 原文逐行，按需导入（R18 D6） |
| `## Principles` | mode L37–77 的分组索引 | 显示名与原则 H1 逐字相同（X14）；「何时适用」＝原则 description 的第一句，不写规则句（R18 §2.2） | 首句搬运 mode L39（带 R18 标注的改写）；解析规则与 User rules 行是新写，出处 R18 §2.2 |
| `## Autonomy` | mode L79–87 的粗体段首标签 | W-G9：人在场与无人两种情况都有出路；每个角色一个无人出路 | 新写，出处 R18 §2.2 `## Autonomy`，删去 R18 D3 去掉的 Cursor 那一条 |
| `## Re-entry` | 编号步骤，粗体标题（S-P3） | 每步有 `Done when`（X10）；第 1 步的理由点名原则 | 搬运：`dispatch/SKILL.md` `## On waking` 第 1–4 步（R18 §2.2） |
| `## Subagents` | mode L89–95 | 按 W-B 各条 | 搬运：mode L95 两句；其余新写，出处 R18 §2.2 |
| `## Writing the reply` | 只取 mode L97–109 的末段 | 无 | 搬运：mode L109（带 R18 标注的删改）；其余一句点名 `shared.md` 规则 4–9 |
| `## Playbooks` | mode L115–143：执行协议、升级路由、路由表 | 路由行的任务类型写成用户会说的话；每行一句 Distinct from（S-G3） | 执行协议搬运 mode L117；路由行按 R18 §3.1 |

**S-M1 节的名字与顺序固定为上面的骨架**（R18 §2.2），连线检查可以逐字比对（R20a 第 11 节 mode 行）。

**S-M2 mode 只装索引与跨 playbook 的规则。** 一条触发行超过三句，说明内容放错了地方，应移到被指向的组件（R20a M4）。mode 的每一行在每个任务开始时都会被读到（mode L39；R18 §2.3），所以它的长度按行计成本（SSR L13）。

**S-M3 触发行格式为** `- <condition> → <destination>.`；**原则索引行格式为** `- **<Display name>** (**principle-<slug>**). <When>.`；**路由行格式为** `- **<Name>.** <Task type>. [<User's words>.] Distinct from <Name>, which <...>. `playbooks/<file>.md`.`（R20a M3；R18 §2.2 第 4 条）。

**S-M4 路由行与 mode 正文只写真实的调用关系。** 「每份 playbook 都收尾于 X」这类全称句，只在连线检查能核对它时才写；核对不了的不写（R20a 第 9 节 P3：pstack mode L143「Invoked at the end of every other playbook.」与实际不符，23 份里只有 7 份以它收尾）。

**W-M1 mode 不复述 `shared.md`**，只点名规则号与适用时机（R18 §5.5；R18 D3 删去了为 Cursor 抄一次的产品事项清单）。

**W-M2 mode 里的立场句只写对所有 playbook 都成立的**（例：`## Autonomy` 里「导入的原则与本节冲突时以本节为准」，R18 §2.2）；只属于一类任务的立场写在那份 playbook 的首段（R20b 附表）。

### 5.2 playbook（`skills/mmw/playbooks/<slug>.md`）

**短形态：**

```
### <Name>

**You own <object>. <Verb>, <verb>.** [<Delegation stance or Distinct from sentence>.]

[<Opening paragraph: what the work is for, who acts on its output, what a shallow
result costs them; the temptation particular to this work and what to do instead.>]

[**Entry.** <One line per entry.>]

1. **<Imperative title>.** <Imperative sentence naming one component, or (judgement)>. <Gate, exception or reason.> [(**principle-<slug>**)]
   Done when <checkable, exhaustive condition>.
2. **<Imperative title>.** ...
   Done when ...
N. **<Hand-off title>.** Run **<Next playbook>**.
   Done when <the observable state the next playbook's **Entry.** reads: an event on the ticket, a file that exists>.

[<Closing paragraph: boundaries and where related work goes instead.>]

**Reply:** <Content unique to this playbook.>
```

| 节 | 结构 | 写法 | 来源 |
|---|---|---|---|
| `### <Name>` | 首行 H3，与路由行的粗体名逐字相同（R20a P2 第 1 项；mode L122 对应 `bug-fix.md` L1） | 名字是任务类型（R18 §1.3） | 名字取自 R18 §3.1 或 R19 |
| 所有权行 | 空一行后写 `**You own <对象>. <动词>, <动词>.**`（`PS:skills/poteto-mode/playbooks/bug-fix.md` L3；R20a P2 第 2 项） | 说清谁决定什么，不写态度 | **新写**，由写 spec 的人写成整句（T5），只在有出处时写（T6；R18 §3.2；R18 审查记录第 40 条；各份的出处在 R18 §3.3 的「所有权」项） |
| 首段 | pstack 的可选纪律段（R20a P2 第 3 项；`bug-fix.md` L5） | W-G1 目的、下游、代价；W-G3 立场句；W-G13 标出决定结果的那一步 | 搬运源的开头或纪律段，源是仍然存在的能力技能时按 S-P5 取舍；没有可搬的才新写，由写 spec 的人写成整句（T5），出处是 R18 §3.3 该份的来源；缺出处按 T6 记为未满足 |
| `**Entry.**` | R18 §3.2 的「MMW 多出」；写法按 S-P8 | 每个入口一行：会话怎样到这里，从哪一步进入 | 新写，出处 R18 §3.3 该份的 Entry 项 |
| 编号步骤 | `N. **<Title>.** <祈使句>`（R18 §1.3；X17）；首句是能勾掉的动作，因为步骤会原样抄进待办（mode L117）；常见 4–9 步（R20a P3；X15）；`(judgement)` 的位置按 S-P7 | 每步点名一个组件或标 `(judgement)`（R18 §3.2）；标 `(judgement)` 的步骤必须写出判断标准（W-G4、W-G5）；理由紧跟规则（W-G2） | 步骤正文搬运源原文（R18 §3.3「步骤正文从来源原文搬」）；标题按 T2 第 3 种从源小节名来，措辞与大小写照原样，要改就写 `replace`（X14）；源里没有标题的才新写，出处是 R18 §3.3 的步骤骨架 |
| `Done when` 行 | 每步最后一行，缩进在步骤下面（SSR L124「on a line beginning `Done when`」） | W-G7：穷尽、能失败；由脚本判定的步骤写退出码或输出行 | 源里有判据就搬；没有就由写 spec 的人写成整句（T5），出处是脚本行为或 R18；都没有的按 T6 记为未满足 |
| 转交步骤 | 最后一步用一句「Run **<Name>**.」（R20a P3；`bug-fix.md` L13） | `Done when` 写下一份 playbook 的 `**Entry.**` 所读的那个可观察状态（票上的某个事件、某个文件存在），不写「**<Name>** has run」这种不会失败的判据（SSR L62；W-G7）。写不出这样的状态时，把转交并进前一步，不单列一步 | 新写，出处 R18 §3.1 的入口列 |
| 尾段 | pstack 的可选尾段（R20a P2 第 5 项；`investigation.md` L12） | 边界句带理由（W-G2），或写 Distinct from | 优先搬运 |
| `**Reply:**` | 末行，全文恰好一个（R20a P2 第 6 项） | 只写本 playbook 独有的交付内容；通用写法在 mode `## Writing the reply`（mode L109） | **新写**，由写 spec 的人写成整句（T5），出处 R18 §3.3 该份的 Reply 或交付物项 |

**长形态（不属于 5.3 三类的长 playbook）。** 超过 S-G9 的阈值、又不是角色操作文件的 playbook，用 5.3 的骨架，去掉唤醒处理簇与 `#### Unattended outlets`；`**Where you are.**` 默认也去掉，跨会话的按 S-P6 写成事实表：`### <Name>` → 所有权行 → 首段 → [`**Entry.**`] → [`**Where you are.**`] → `#### Steps` → 规则簇（排序与簇名同 5.3，S-O3）→ `**Reply:**`。问人的步骤按 W-P3 写出无人出路，或点名 mode `## Autonomy`。出处：R18 §3.2 统一骨架里 `#### Steps` 标注「长 playbook 才写这一行」，不限于角色 playbook；结构 lint 的 `playbook-steps` 对所有自写 playbook 都按「有 `####` 就恰好一个 `#### Steps`」检查（R21 §4.2）。

**S-P1 playbook 没有 frontmatter；首行是 `### <Name>`；第一个非空正文行以 `**You own ` 开头（有出处时）；末行以 `**Reply:** ` 开头**（R20a P1、P2；R18 §7.5 第 7 类）。没有编号步骤的约定不放进 `playbooks/`：跨 playbook 的规则放 mode，某个时刻的材料放 reference（R20a 第 9 节 P4：pstack `opening-a-pr.md` 名为 playbook，没有所有权行、编号步骤与 Reply 行，实质是标准）。

**S-P2 playbook 只编排，不装做法。** 以下内容不装进 playbook：能力技能的做法（点名即可）、原则的内容（括注即可）、被多处引用的概念定义（放 mode 或 reference）、别的技能的输出格式（写「按 `` `how` `` 的输出格式」，不列节名）、与流程无关的技术目录（放 reference）（R20a P5、P7、P20；SSR L16）。

**S-P3 步骤格式为 `N. **<Title>.**`**：新写的标题是 sentence case 的祈使短语，搬来的标题按 X14 保持原样；句号在粗体内；子项用缩进列表，每项是粗体段首标签加句号（R20a P3；`PS:skills/poteto-mode/playbooks/feature.md` L8–11）。

**S-P4 不做的步骤不从文件里删**：执行时在待办里写 `skip: <reason>`（mode L117；R18 §6）。playbook 文本不复述这条。

**S-P5 能力技能拆分后，开头留在能力技能里。** 源是一个能力技能、拆分后它仍然存在时：说明能力本身用途的句子（W-C1 的目标段）留在能力技能里；playbook 首段只写这一类任务的目的与诱惑，并按 W-G12 点名那个能力技能。同一句话两边都需要时，保留在能力技能里，playbook 不复述。理由：用 `move` 把开头搬走，剩下的能力技能就没有 W-C1 要求的目标段；用 `copy` 两边各留一份，就是 SSR L40 的 Duplication，逐字检查也不会报（`copy` 不查 `NOT-REMOVED`，R21 §3.1）。

**S-P6 跨会话、又没有 `where` 命令的白天长 playbook，用事实表式 `**Where you are.**`。** 一份 5.2 长形态的 playbook 会跨会话（有一步结束回合等别人回来，或要用户下次再跑），又没有脚本能从事件算出位置时，在 `**Entry.**` 之后写 `**Where you are.**`：首句「Take the first line whose fact holds.」，接一句说明事实从哪里读（tracker、仓库、用户本条消息，不取会话记忆，句末点名 **principle-resume-from-durable-state**）；然后每个事实一行 `- <fact> → **<Step>**.`，末行 `- Anything else → **<first step>**.`。同一个事实只对应一个步骤，并与 `**Entry.**` 给同一种到达的步骤相同。出处：范本 `exemplars/mmw/playbooks/write-a-spec-and-tickets.md` 的 `**Where you are.**` 与其注解「用的是哪种骨架」；R18 §3.3 P1「Where you are：九行事实表」（R12 K-33、K-41）；R18 §5.2 **principle-resume-from-durable-state** 的调用方列有 P1 的这一行。理由：下一个会话只能从持久的事实找回位置（推断：没有观察到丢位置的运行）；5.3 的 `where` 命令只为角色而写（R18 §7.7 的表只有角色行）。

**S-P7 `(judgement)` 写在粗体标题之后。** 判断步骤写成 `N. **<Title>.** (judgement) <第一句>`，判断标准写在步骤正文里（W-G5）。按 R21 §3.3 的切分，标记属于标题之后的第一句；那一句若是搬来的，就不再逐字，spec 在 `## Moves` 里为它写 `replace`，新句带着 `(judgement)`。结构 lint 的 `step-names-component`（R21 §4.2）要认这个位置。出处：范本 `write-a-spec-and-tickets.md` 第 4 步、`work-a-ticket.md` 第 8 步，与两份注解改写清单里带标记的新句；R18 §3.2「每步点名一个组件或标 `(judgement)`」；R21 §3.3 的单元切分。

**S-P8 `**Entry.**` 写成列表，每个入口一项。** `**Entry.**` 单独一行，下面每种到达方式一项 `- **<Label>.** <怎样到这里，从哪一步进入>`，标签说出到达方式（例：``**Started by `start`.**``、`**Adopted ticket.**`、`**Woken.**`、`**Handed a triaged issue.**`）。人不在场时这份 playbook 怎样处理，也写成一项 `**Unattended.**`（W-P3）。5.2 与 5.3 同一种写法。出处：范本 `work-a-ticket.md` 与 `write-a-spec-and-tickets.md` 的 `**Entry.**`；R18 §3.2「MMW 多出」。理由：用户要求全套结构统一（R18 D9）；每种到达各有一个标签，唤醒指针与 `**Where you are.**` 送来的会话能认出自己属于哪一项。

**W-P1 首段写这一类任务特有的诱惑**（W-G3）。实例：「Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix.」（`bug-fix.md` L5）。

**W-P2 点名原则时，旁边写本地后果**，不复述原则（R18 §5.1；L7 C.2）。实例（R18 §3.3 P15 `#### While writing code`）：「a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it」。

**W-P3 问人的步骤要写出无人出路**，或点名 mode `## Autonomy`（W-G9）。

### 5.3 角色操作文件式 playbook（`run-a-night`、`land-one-ticket`、`work-a-ticket`、`review-a-ticket`、`research-a-question` 这类）

适用于三类 playbook：会跨会话的、会被唤醒或在压缩后重入的、由脚本起的角色所读的（R18 §1.4；R18 §3.2「跨会话、会被唤醒的 playbook（H6）」）。不属于这三类的长 playbook 用 5.2 的长形态。

```
### <Name>

**You own <object>. <What you never own>.**

<Opening paragraph: who reads the output cold, what it is for, what a wrong result costs;
the temptation particular to this role and what to do instead.>

**Entry.** <One item per arrival (S-P8): start prompt, adopted ticket, wake pointer, compaction.>
**Where you are.** Run `<where command>` and go to the step it prints.

#### Steps
1. **<Title>.** <...>
   Done when <...>.
...

#### <Rule cluster>                       (standing rules; steps name it by heading; in the order
                                         steps first name them, S-O3)
#### Unattended outlets                   (a rule cluster like the others: placed where a step
                                         first names it)
<Where this role writes a decision nobody is there to make.>
#### When <event or sender> wakes you    (only when roles.json registers it as the handler;
                                         after every cluster a step names)

**Reply:** <Deliverable: the closeout comment, the report, the event.>
```

| 节 | 结构 | 写法 | 来源 |
|---|---|---|---|
| 所有权行 | `PS:skills/poteto-mode/playbooks/orchestrate.md` L3「**You own the program, never the code. …**」：拥有什么，从不拥有什么 | 角色边界写成一句能用来判断的话 | **新写**，由写 spec 的人写成整句（T5），出处 R18 §3.3 各份的「所有权」项（P12 取 `night.md` L3、L96；P15 取 `implement` L99；P16 取 `code-review/SKILL.md` L8） |
| 首段 | `orchestrate.md` L5–11 的纪律段与总纲 | W-G1：读者是冷读的人或 agent（R18 §3.3 P12 首段「早上的读者是冷读」，出处 `night.md` L5）；W-G13 | 搬运源的开头段；源是仍然存在的能力技能时按 S-P5 |
| `**Entry.**`、`**Where you are.**` | R18 §3.2 骨架里「MMW 多出」的两行 | Where you are 只点名脚本，不复述它的输出（SSR L41 cache） | 新写，出处 R18 §3.3 各份与 §7.7 |
| `#### Steps` | `orchestrate.md` L58；只有这些步骤抄进待办（R20a P4） | 同 5.2 | 同 5.2 |
| 规则簇 | `orchestrate.md` 的 `####` 簇（L13、L68 等）。MMW 统一放在 `#### Steps` 之后，按步骤第一次点名它的顺序排（决定：读者先看到要抄进待办的步骤；指针在需要它的那一步出现，满足 SSR L30） | 簇名写这组规则生效的时刻：`While <activity>`、`When <event> wakes you`、`After <event>`，或者名词短语（R18 §3.3 的 `#### While writing code`、`#### Closing pass`） | 搬运源的对应节 |
| 唤醒处理簇 | R18 §3.2、§7.1 | 每个（角色，事件）在全套里只有一个处理处（SSR L91；R18 §7.5 第 6 类） | 搬运源的唤醒说明 |
| `#### Unattended outlets` | R18 §3.3 P12、P16 | W-G9：写明写到哪里（closeout 的 `Decisions I made on my own`、报告里的 `unverified:`），而不是「自行判断」 | 搬运源；出处 R18 §2.2 `## Autonomy` 的三个角色 |
| `**Reply:**` | 同 5.2 | 无人会话的回复就是交付物（R18 §2.2 `## Writing the reply`） | **新写**，由写 spec 的人写成整句（T5），出处 R18 §3.3 的交付物项 |

**S-O1 被指针或 `roles.json` 指向的步骤标题与簇名是标识符**（N10）：改名时，在同一次改动里改 `roles.json`、`locations.py`（R18 的 `anchors.py`，R19 §4.6 改名）与所有引用处（SSR L143；R18 §7.1、§7.2）。

**S-O2 一份文件里 `#### Steps` 恰好一个**（R20a 第 11 节）。

**S-O3 规则簇的顺序。** `#### Steps` 之后先写步骤点名的规则簇，按步骤第一次点名它的顺序排，`#### Unattended outlets` 也按它第一次被点名的位置排；然后写 `roles.json` 登记的唤醒处理簇（`#### When <event> wakes you`、`#### After <event>` 式的簇），它们没有步骤点名，排在最后。出处：范本 `exemplars/mmw/playbooks/work-a-ticket.md`（`#### Unattended outlets` 在第 3 步第一次被点名，排在 `#### While the product runs` 之后；`#### When the orchestrator resumes you` 与 `#### After the closeout of an adopted ticket` 在最后）；本节表「规则簇」行。理由：读者先看到要抄进待办的步骤，每个指针指向的簇在它出现之后不远处（SSR L30）；唤醒处理簇由唤醒行的指针直接进入，不依赖步骤的顺序。

**W-O1 每一步的 `Done when` 优先写脚本的可观察结果**（退出码、输出的某一行、票上的某个事件），因为「这一步做到了哪里」由 `where` 从事件判断（R18 §7.7）。判据与脚本的判断不一致，会让重入的会话重复或跳过一步（推断）。

**W-O3 无人出路分两处写。** mode `## Autonomy` 的 `**Unattended.**` 写一次判定与通用做法（屏幕上不放问题；取票、baseline、spec 最可能的选项；写一行；继续）。同一节的 `**Where each role records a decision.**` 每个角色一行，只写去处，并指向那个角色 playbook 的 `#### Unattended outlets`；没有 playbook 的角色按名点名它自己的 reference（例：advisor 的 `references/advising.md`）。角色 playbook 的 `#### Unattended outlets` 只写本角色独有的内容：写到哪里、写给谁看、本角色的格式要求（例：worker 的 `skip:` 行带步骤标题，因为 closeout 按标题核对）。`skip: <reason>` 的通用格式只在 mode `## Playbooks` 定一次。出处：范本 `exemplars/mmw/SKILL.md` `## Autonomy` 与 `work-a-ticket.md` `#### Unattended outlets`，两份注解对应的行；R18 §2.2 `## Autonomy`（「屏幕上不放问题……写一行进本角色的决定记录」与各角色的出路）、R18 第 6 节无人表。理由：每个角色都读 mode，通用做法再写进每份 playbook 就是同一意思的两份（SSR L40）；每个角色的去处又各不相同，只能在它自己的 playbook 里写全。

**W-O2 角色不做的事写成边界句加理由**，放在所有权行或它生效的那一步（W-G8）。实例：「a dispatched worker never runs `design-pages`」（R18 §3.3 P15，出处 `design-pages` L21）。

### 5.4 原则（`skills/mmw/principles/principle-<slug>.md`）

```
---
name: principle-<slug>
description: "Apply when <observable situation>. <Rule summary as an imperative>."
---

# <Title>

<Rule: one to three sentences naming the situation and the decision it changes.>

**Why:** <One to three sentences: the consequence or cost.>

**Pattern:**
- **<Imperative label>.** <One or two sentences.>

[**The test:** <A yes-or-no check the agent runs on itself.>]
[**Stop:** / **Boundaries:** <...>]

[Distinct from **principle-<slug>**, which <...>.]
```

| 节 | 结构 | 写法 | 来源 |
|---|---|---|---|
| frontmatter | 两个键（R18 §5.1；导入时删掉开关行，R18 §8.2） | X7：「Apply when」后面写可观察的情境；第一句会成为 mode 索引里的「何时适用」 | 搬运：取自出处原文（R18 §5.2 表的「出处」列）；情境句是新写，出处同上 |
| `# <Title>` | `PS:skills/principle-attack-the-premise/SKILL.md` L7 | sentence case（X14）；名字待 R19 | 无 |
| 规则 | 同文件 L9 | 一条能改变具体决定的规则（L7 A.4 的门槛） | 搬运（R18 §5.1「规则与理由逐字取自……原文」） |
| `**Why:**` | L11 | W-G2 | 搬运；原文没有理由的不写（R18 §5.1；T6） |
| `**Pattern:**` | L13–17，粗体祈使标签加句号 | W-G4：只写 agent 会做错的做法；W-G6：用领域术语 | 搬运 |
| `**The test:**` / `**Stop:**` / `**Boundaries:**` | L19–21；R18 §5.1 列出的可选标签 | W-G5：写成是非测试，或写「你跳过了它的迹象」（R20a R3，`principle-model-the-domain` L26） | 搬运 |
| 区分句 | L23，放在最后 | S-G3 | 搬运；两条原则都属 MMW 自有时可以新写，出处是两条原则的原文 |

**S-R1 小节标签只用 `**Why:**`、`**Pattern:**`、`**The test:**`、`**Stop:**`、`**Boundaries:**`**，不用 `##`（R18 §5.1；R20a P15）。导入的原则保留原标签。

**S-R2 原则不装命令、参数、输出格式、工具细节，也不装只属于某一步的规则**（R20a R4）；只指向原则或能力技能，不指向 playbook、脚本、mode（R18 §5.1）。MMW 自写的原则之间用 `**principle-<slug>**` 互相点名，不用 Markdown 链接（R18 §1.3）。

**S-R3 出处不写进原则文件**，写进 ADR 0032（R18 §5.1；SSR L52）。概念的作者或著作不算出处，照 SSR L55 写在术语定义旁（W-G6）。

**W-R1 原则的每一句都要跨任务成立**（L7 A.4）。一句话只在一类任务里成立时，它是那份 playbook 的本地限定（W-P2）。

### 5.5 能力技能 `SKILL.md`（MMW 自有，`skills/<name>/SKILL.md`）

```
---
name: <directory name>
description: <What it is>. Use when <branch>, when <branch>, or <branch>. [Not for <non-trigger>.]
---

# <Name>

<Goal paragraph: what this does and hands back, who acts on it, what a shallow result costs.>

[<Division sentence: Distinct from the `<name>` skill, which <...>.>]

[## <Stance, in the work's own words>]

[## Pick a branch
| When | Read |
| <condition> | `references/<file>.md` |]

## <Method: a main form, see S-C2>

## Output
<Named fixed sections of what is handed back; details may live in references/.>

[## Composing this skill
<How another skill uses this one by name, and which part this skill owns.>]

[**Reply:** <What the reply adds beyond ## Output.>]
```

| 节 | 结构 | 写法 | 来源 |
|---|---|---|---|
| frontmatter | `name` 等于目录名（R20a C1） | SSR L67：只写「是什么」和触发分支，同义触发合并（WFA L17），可以有一条非触发（`UP:engineering/wizard/SKILL.md` L3）；用户触发的技能写一行给人看的摘要（SM L10） | 搬运现有 description；按 SSR L67 删去的流程与输出移进正文 |
| `# <Name>` | R20a C2 第 1 项 | 无 | 无 |
| 目标段 | R20a C2 第 2 项（`how/SKILL.md` L9） | W-G1 | 搬运源的开头（拆分时留在这里，S-P5）；没有才新写，由写 spec 的人写成整句（T5），出处 R18 §4.1 |
| 分工句 | R20a C2 第 3 项（`blast-radius/SKILL.md` L11） | S-G3 | 优先搬运 |
| 立场节 | R20a C2 第 4 项（`blast-radius` `## Don't trust your own writeup`） | W-G3；节名直接写这项工作的立场（`UP:engineering/wayfinder/SKILL.md` `## Plan, don't do`） | 搬运 |
| `## Pick a branch` | 无 | 多选一写成表，每行是条件与文件（SSR L31；`UP:engineering/prototype/SKILL.md` L10–17） | 搬运源的分支说明 |
| 做法 | 按 S-C2 选一种主形态 | W-G4、W-G5、W-G13；步骤型与阶段型的每步有 `Done when` | 搬运 |
| `## Output` | R20a P12 裁定的两种收尾之一（写产物结构） | 即使细节在 reference 里，这里也要列出节名（R20a F5） | 搬运源的输出格式 |
| `## Composing this skill` | R20a C2 第 8 项（`PS:skills/show-me-your-work/SKILL.md` L79–81） | 写别的技能怎样按名字使用它、哪部分由它持有（W-G12；原文「Reference it by name and let it own the format. Don't restate the columns.」）；不点名具体的调用方，不写下一步（S-C3） | 优先搬运；新写按 T5 |
| `**Reply:**` | R20a C2 第 7 项 | 只写 `## Output` 之外的内容 | 优先搬运 |

**S-C1 frontmatter 只有 `name`、`description`**（S-G6）。

**S-C2 做法主体选一种主形态，用这种形态的标题写法。** 分支表（`## Pick a branch`）、立场节、规则小节可以与主形态并存；主形态内部可以有编号列表与 leading word。实例：`UP:engineering/diagnosing-bugs/SKILL.md` L12 是规则节 `## Redact`，L18 起是阶段型的 `## Phase 1: Build a feedback loop`，L24–32 是阶段内的编号列表，L20 用 **tight** 这样的 leading word 驱动；`UP:engineering/prototype/SKILL.md` 是分支表加规则节。不为统一形态而重排已有技能的节：R20a C3 只说「做法部分按形态选一种标题写法」，没有要求一份文件只用一种形态；R21 §4.2 取舍第 3 条也写明「强求统一形态就等于改写 mattpocock 的文字，与 D9 相反」（W-G4）。

| 主形态 | 写法 | 何时用 | 出处 |
|---|---|---|---|
| 步骤型 | `## Steps`，下面是 `N. **<Title>.**` 编号列表，每步有 `Done when` | 做法有真实的先后 | R20a C3（`blast-radius/SKILL.md` L31）；步骤格式同 S-P3 |
| 阶段型 | 先写 `## Start`（列出各阶段），然后每个阶段一个 `## Phase A: <Verb phrase>`，每个阶段末尾写 `Done when` | 阶段之间有闸门，而且后面的阶段会诱使 agent 赶工 | R20a C3（`arena/SKILL.md` L11–22）；WFA L49 |
| 子代理编排型 | `## Step N. <Title>`，派子代理的步骤带参数块（S-C4） | 每一步派出一组子代理 | R20a C3（`how/SKILL.md` L11） |
| 规则目录型 | `## Process`（两三步）加按类分组的规则；规则编号是稳定 id，删掉的规则留下空号 | 一组平级的规则逐条套用 | R20a C3（`unslop/SKILL.md` L18）；WFA L34 |
| 格式持有型 | 按「格式 → 怎样写一行 → 放哪 → 规则 → 审计 → 供组合」分 `##`，末节是 `## Composing this skill` | 技能持有一种格式（一行记录、一份报告、一份契约），别的技能按名字使用它而不复述格式 | R20a C3（`PS:skills/show-me-your-work/SKILL.md` L11、34、42、48、53、79）。MMW 自有技能里持有格式的（`ui-acceptance` 持有 `.mmw/target.json` 与 oracle 输出行的读法，`write-screen-contract` 持有 `screen-contract.yaml`）今天按分支型或步骤型组织（`ui-acceptance` `## Find your moment`、`write-screen-contract` `## Steps`），不为套这一形态而重排 |
| 概念驱动型 | 不编号；用加粗定义的 leading word 组织，末尾一句穷尽的完成判据 | 做法是一种持续的判断，不是一串动作（X2） | `UP:productivity/grilling/SKILL.md` L6–28 |
| 分支型 | `## Pick a branch` 表，每个分支一个 reference（第 5.6 节分支文件） | 不同运行走不同路径，而且各路径的材料不重叠 | `UP:engineering/prototype/SKILL.md`；SSR L15 |
| 单条指令型 | 没有标题，frontmatter 后只有一段 | 整个技能是一次点名或一条规则 | R20a C3（`bro/SKILL.md` L7）；`UP:productivity/grill-me/SKILL.md` L7 |

**S-C3 能力技能不写「下一步」「谁调用我」**：没有 `## Next`、`## Reached from here`，不写任何 playbook slug，也不按编号引用别的文件里的步骤；角色名作为领域词可以出现（R18 §4.5；X13，落地先后见「X13 的先后」）。

**S-C4 子代理参数块写三样**：「在本会话派一个通用子代理」或「另起会话的角色名」；只读或可写；一句理由（X16；R18 §2.2 `## Subagents`）。只读靠简报里的一句「You are read-only: write nothing.」（R18 §2.2）。简报的首句按 5.7 形式一后的限定，不写 mode 那一句。

**S-C5 引用自己的 reference 时，放在用到它的那一步**，写明打开的条件与用法（N7；SSR L25、L30）。

**W-C1 目标段必须能通过 SSR L11 的开头测试**：只拿着这个技能的 agent，能说出这项工作为了什么、谁根据产出行动、做浅了代价是什么。只有「This skill does X」式身份句的，不算通过（WFA L18）。

**W-C2 技能自带的人工闸门写在它生效的那一步**，并写出通用的无人出路，例如「If no one is there to answer, <default>, and state the assumption in <where>」（R20a C5；`UP:engineering/prototype/SKILL.md` L17；W-G9）。角色专属的出路不写在这里，由 mode `## Autonomy` 覆盖（R18 §2.2 的优先级句）。

**W-C3 一条理由管住整个技能时，可以单列一节**，节名说出这条理由（`UP:engineering/code-review/SKILL.md` `## Why two axes`，SSR L55、L165 列为保留范例）。这是 X1「理由不另开一节」的唯一例外。

**W-C4 例子成对**（W-G11），只放在容易误读的判断旁边。

### 5.6 reference（`references/<file>.md`）

所有 reference 共用以下规则：没有 frontmatter；`# <Name>` 下的第一句说明谁在什么时候读它、怎样用（R20a F5）；在技能正文或 playbook 里用带条件的指针点名（SSR L25）；打开它的那个时刻需要的规则、格式、命令、已知陷阱与完成判据都在这一份里（SSR L27）。按用途分以下几种：

| 形态 | 骨架 | 结构出处 | 写法出处 |
|---|---|---|---|
| 分支文件 | `# <Name>` → 一句谁在什么时候读 → [目的段（W-G1）：这个分支要回答什么、产出给谁、答错了代价是什么] → [`## When this is the right shape` 式的条件列表] → 出口句「If <other case>, this is the wrong branch. Read `references/<other>.md`.」，紧跟在条件列表之后，没有条件列表时紧跟首句或目的段 → 这个分支的规则（立场句按 W-G3 放在诱惑出现的那一条旁边，带理由） → 格式与完成判据 | pstack 没有对应形态；首句取 R20a F5 的规则 | 目的与读者：`UP:engineering/prototype/LOGIC.md` L3–5（「you can hand it to a non-developer … So it speaks their language」）；适用形状与出口：同文件 L7–14、`UI.md` L5–12（SSR L162）；代价句：`LOGIC.md` L20「A logic prototype that answers the wrong question is pure waste」；带理由的立场句：`UI.md` L14–16「A throwaway route on its own is a vacuum: every variant looks fine in isolation」；R20b M8 |
| 判断框架或清单 | `# <Name>` → 一句何时用、怎样用 → [一段目的（W-G1）] → 每一项一个 `##` | R20a F3（`architect/references/design-red-flags.md` L1–5） | 每项写成 W-G5 的测试或 W-G11 的成对例子 |
| 检索或操作指南（按外部来源替换的一族） | `## What this source contains` → `## How to search it` → `## What good evidence looks like here` → `## Common pitfalls` → `## What to return` | R20a F2（`why/references/sources/slack.md`） | W-G7 |
| 产物模板 | `# <Name> template` → 一句用法 → 产物的各节 | R20a F4 | 每节写它要回答的问题，不写示例内容（SSR L129） |
| 会增长的目录 | 首句写谁在什么时候读、何时追加；末尾是追加区 | R20a F4（`bugbot-triage.md` L3） | 无 |
| 简报模板 | 见 5.7 | R20a F1 | R20b M11 |

**S-F1 一份 reference 装一个时刻的全部材料**；按主题拆（规则、格式、例子各一份）就是 fragment（SSR L28）。

**S-F2 每次运行都要读的 reference 内联回正文**，唯一的例外是整份交给另一个代理的简报模板（X8；R20a P17）。

**S-F3 文件名说出它承载的分支或产物**，读者只看文件名就知道什么时候该打开它（R20b §3，推断）。MMW 自有的 reference 用小写连字符（R18 §1.1 的现有写法）；具体名字由 R19 定。

**W-F1 分支文件要能单独读懂**：不依赖另一个分支文件里的定义；共用的词汇放在技能正文里（`UP:engineering/codebase-design/DEEPENING.md` L3「Assumes the vocabulary in SKILL.md」）。

**W-F2 分支文件的目的段与立场句不被骨架挤掉。** 目的段与适用形状段是可选节，但源里有就搬，不当成骨架之外的背景删掉（T9；第 7.5 节第 1 条）。

### 5.7 给子代理或另起会话的简报

有三种形式，按接收方手里有什么来选。

**形式一：写在步骤里的短简报（同一会话的子代理，几行）。**

```
N. **<Title>.** Spawn <one | one per <item>> general-purpose subagent<s> in one message and wait for all.
   Brief: "Read the `mmw` skill's `## Principles` and the playbook step you serve. <Task, as the question to answer.>
   <Material it cannot otherwise reach, pasted in full.> <Distinct constraint, when parallel.>
   You are read-only: write nothing. Return <structure>, under <N> words."
   Done when every subagent has returned and <check on the returns>.
```

形式一的首句只用在 mode 与 playbook 派出的子代理上（R18 §2.2 `## Subagents`）。能力技能自己派的子代理，简报从任务句开始；要用到的规则按 W-B1 粘贴进简报，或者让子代理加载某个技能。理由：能力技能不点名 mode（N6、S-C3），而且能力技能要能脱离 mode 使用（R18 §4.5 末条，那里作为推断理由写出），脱离 mode 运行时「the playbook step you serve」不存在。

**形式二：简报模板 reference（整份原样交出）。**

```
# <Role> prompt template

<One sentence to the dispatcher: fill the placeholders and pass the rest verbatim.>

---

<Second-person paragraph: who you are, what others are doing in parallel, who reads your
output and what they do with it, so what to favour.>

## <Input section>
{UPPER_SNAKE_PLACEHOLDER}

## <Instructions>
<...>

## Output
### <Fixed section>
<...> If you found nothing here, say so.
<Length limit.>
```

**形式三：另起会话的启动提示词（由脚本写，一行）。**

```
Use the mmw skill. Role <role>, ticket #<n>, unattended: mmw <slug>#<Step title>. Data: <absolute path>.
```

| 部分 | 结构 | 写法 | 来源 |
|---|---|---|---|
| 首句「Read the `mmw` skill's …」 | R18 §2.2 `## Subagents` | 无 | 搬运 R18 原句；只用于 mode 与 playbook 派出的子代理；自足的只读简报（评审 axis）不加这一句（R18 审查记录第 34 条）；能力技能派的子代理不加（见上） |
| 任务 | pstack F1 的输入节（用 `{UPPER_SNAKE}` 占位，R20a P10） | 写成要回答的问题；写接口与行为，不写路径与行号（`UP:engineering/triage/AGENT-BRIEF.md` L9–26） | 新写，出处是调用它的那一步 |
| 材料 | 无 | 子代理拿不到的材料全文粘贴，并说明原因（`UP:engineering/code-review/SKILL.md` L63「pasted in full (the sub-agent has no other access to it)」） | 搬运被粘贴的原文 |
| 角色与处境段 | R20a F1 第 4 项（`how/references/explorer-prompt.md` L7–9） | W-G1：告诉接收方它的产出给谁，因此该偏重什么 | 搬运源模板 |
| 并行约束 | 无 | 并行派多个子代理时，每个一个不同的约束（`UP:engineering/codebase-design/DESIGN-IT-TWICE.md` L21–38） | 新写，出处是调用它的那一步 |
| `## Output` | R20a F1 第 7 项；固定小节用 `###` | 写明「没有发现也要说」与长度上限（SSR L102；`UP:engineering/code-review/SKILL.md` L64「Under 400 words」） | 搬运源模板 |
| 启动提示词 | R18 §2.3；必须一行（R18 §7.5 第 8 类，H4） | 只带启动时已知的数据；规则经技能到达，不写进提示词（SSR L100–101） | 由脚本从 `roles.json`、`locations.py` 生成（R18 §7.8；R19 §4.6 改名） |

**S-B1 简报模板文件的首行匹配 `# <Role> prompt template`，有 `---` 分隔线，占位只用 `{UPPER_SNAKE}`**（R20a F1、P10）。

**S-B2 送进活会话的一切内容都是一行**（R18 §7.8）。

**W-B1 简报要求子代理应用的每条规则，要么粘贴进简报，要么让它加载某个技能**；两者都不是，就是断掉的 hand-off（SSR L101）。

**W-B2 会让所有子代理白跑的错误，在派发之前检查**（`UP:engineering/code-review/SKILL.md` 第 1 步「A bad ref or empty diff should fail here, not inside two parallel sub-agents.」，SSR L168）。

**W-B3 子代理还在跑时，只让依赖它结果的问题等待**（`UP:productivity/grilling/SKILL.md` L26）。

**W-B4 你对子代理的产出负责**：读它的产出，写自己的总结，不原样转述（mode L95，按 R18 §2.2 搬运）。

---

## 6. 命名在这份规范里的位置

实际名字由 `R19-naming-table.md` 定（R18 D9）。本文只定名字在文本里怎样出现（第 4.3 节 N1–N10），另加三条命名时要守的写作约束：

- **名字说出这项工作或它产出的东西。** 技能名是动作、产物或一个 leading word；reference 名是它承载的分支或产物；脚本名说出它是什么（R20b §3，推断）。
- **playbook 与 pstack 是同一任务类型时，用 pstack 的文件名**，这样以后导入同名文件是合并，不是并存（R18 §1.3）。上游 mattpocock 与 pstack 的技能名、文件名不改（R18 D9）。
- **改名在搬家的同一张票里做**（R18 D9），并按 SSR L143 在同一次改动里改掉每个引用处；程序、tracker、消费仓库读的名字按 N10 走迁移（SSR L76）。

---

## 7. 审查清单

供 reviewer 的 Standards 轴与写作审查使用。每项写出规则编号，并标出检查方式：

- 「机查」：R21 的逐字搬运检查（`check_verbatim_moves.py`）、结构 lint（`check_component_structure.py`），或 R18 §7.5 的连线检查（`check_wiring.py`）能判；「对应检查」一列写出脚本、判定或规则 id、类别，以及它在哪里跑。reviewer 只核对它们跑过且结果干净。
- 「判断」：要 reviewer 读了才能判。

**在哪里跑。** 逐字搬运检查与结构 lint 写进每张搬文字的票的 `## Acceptance criteria`，照 R21 §3.8 的两条判据：`CHECK: uv run --quiet mmw-v2/tests/lib/check_verbatim_moves.py --ticket "$MMW_TICKET"`，`EXPECT: /^VERBATIM OK \d+ /m`（下称「票的 VERBATIM 判据」）；`CHECK: uv run --quiet mmw-v2/tests/lib/check_component_structure.py <本票写的组件文件>`，`EXPECT: /^STRUCTURE OK \d+ files?/m`（下称「票的 STRUCTURE 判据」；批次票另按 R21 §4.5 加 `--batch Bn`）。两个脚本带 PEP 723 块取 PyYAML，所以经 `uv run`。`check_wiring.py` 与 `check_own_skill_frontmatter.py` 在每个套件 `run.sh` 开头的预检 `run_shared_lints.sh` 里跑（R18 §7.5 首段；R21 §5.2、§6）。

**何时生效。**
- B0 的五张检查票（R21 §0 第 9 条）落地之前，不按本清单审查搬家票：那时机查项没有工具可跑，「只核对跑过且干净」无从谈起。
- 结构 lint 的例外表 `mmw-v2/tests/lib/structure-exceptions.tsv` 里登记且未到期的违规，不报 finding；到期未还的（`--batch Bn` 失败的），报 finding（R21 §0 第 7 条、§4.5）。
- 连线检查的某一类在 R18 §7.5 表「转为失败」列的批次之前只报告；那之前 reviewer 读它的报告，只把本票新增的违规报成 finding（推断：与例外表「新违规立刻失败」同一个意思，R21 §4.4「建议 `check_wiring.py` 也用例外表过渡」一段）。

报 finding 时写「规则编号 + 文件 + 句子」。

### 7.1 搬运、新写与删除

| # | 查什么 | 规则 | 方式 | 对应检查 |
|---|---|---|---|---|
| K1 | 清单里的每一句都到了指定位置；目标里的每一句都有来处；清单外的技能文字没被改 | T1 | 机查 | 票的 VERBATIM 判据：Q1 carried、Q2 accounted、Q3 untouched（R21 §3.1） |
| K2 | 搬来的句子只有五种机械改写（含大小写未被改） | T2、T3 | 机查 | 票的 VERBATIM 判据的 `CHANGED` 判定（R21 §3.4） |
| K3 | 规则与它的理由句没被拆到两处 | T4 | 判断 | 顺序检查（`OUT-OF-ORDER`）只能部分覆盖（R21 §0 第 10 条） |
| K4 | 每个新句子都在模板的「新写」位置，并在票或 `imports.tsv` 里有出处；T5 列出的承载理解的位置用的是票上 `new <目标> "<整句>"` 的整句；不带整句的 `new <目标>` 都点名了范本段落 | T5 | 机查＋判断 | 整句逐字出现：票的 VERBATIM 判据的 `new` 行；位置、出处、范本点名：判断 |
| K5 | 所有权行与 `**Why:**` 没有出处的没被编出来；首段、立场句、`Done when` 缺出处的已在票上记为未满足，没有静默留空 | T6 | 判断 | 无 |
| K6 | 上游原文没有按本文模板改写 | T7 | 机查 | `check_wiring.py` 第 3 类：与 squash 原文的差异只能是 merge-note 登记过的两类（B2 末转为失败）；本票分支上的改动另由票的 VERBATIM 判据 Q3 报出 |
| K35 | 源范围里不搬的每一句都有 `drop` 行；交出目的、理由或立场的句子，其 `drop` 行写明了它原本指导的情况与删后由什么指导，没有只写「冗余」的 | T9、W-G10 | 机查＋判断 | 有没有 `drop` 行：票的 VERBATIM 判据 Q1 报 `DELETED`；理由是否合格：判断（SSR L142），读票的 `## Moves` |

### 7.2 结构

| # | 查什么 | 规则 | 方式 | 对应检查 |
|---|---|---|---|---|
| K7 | 标题层级符合组件类型；playbook 首行是 `### `，没有 `#`、`##` | S-G1、S-P1 | 机查（mode、playbook、原则）；判断（能力技能、reference） | 票的 STRUCTURE 判据：`mode-sections`、`playbook-title`、`principle-body`。能力技能与 reference 的标题层级不在 lint 规则表里（R21 §4.2「不查能力技能的正文形态」） |
| K8 | 没有 U+2014、U+2013 | S-G5 | 机查（新组件：mode、自写 playbook、原则、mode 的 reference）；判断，辅以 `grep -rn $'—\|–'`（能力技能） | 新组件：票的 STRUCTURE 判据 `no-dash`；上游子树：`check_upstream_em_dashes.py`（只查 `mmw-v2/upstream/skills/`，根 `AGENTS.md` `## Commands`）；能力技能：没有脚本，已有的旧债留给专门的清理票（R21 §4.2 取舍第 1 条）。搬来的句子里破折号的增删由票的 VERBATIM 判据报 `CHANGED`（R21 §3.4） |
| K9 | MMW 自有技能的 frontmatter 只有 `name`、`description`，`name` 等于目录名 | S-G6、S-C1 | 机查 | 预检里的 `check_own_skill_frontmatter.py`；票的 STRUCTURE 判据：`skill-name`、`principle-frontmatter` |
| K10 | 不点宿主、工具、runner 名 | S-G8 | 机查 | 票的 STRUCTURE 判据：`host-name`（SSR L120 那条 grep 的脚本形式） |
| K11 | mode 的节名与顺序等于 S-M1；原则索引行格式正确；显示名等于原则的 H1 | S-M1、S-M3、X14 | 机查（显示名等于 H1 一项在加进第 5 类之前靠判断） | 票的 STRUCTURE 判据：`mode-sections`、`mode-imported-triggers`、`mode-principle-line`、`mode-route-line`；`check_wiring.py` 第 5 类（B1）比「何时适用」与 description 第一句，也比显示名与原则 H1（R21 §4.4）。显示名与 H1 相等不在第 5 类现在的定义里（R18 §7.5），写 `check_wiring.py` 时要加进去（X14），加进去之前靠判断 |
| K12 | playbook 每步是 `N. **<Title>.**`，每步点名一个组件或标 `(judgement)`（标记在粗体标题之后），每步有 `Done when` 行，末行 `**Reply:**` 恰好一个 | S-P1、S-P3、S-P7、X10、X17 | 机查 | 票的 STRUCTURE 判据：`step-title`、`step-names-component`、`step-done-when`、`playbook-reply`、`playbook-owner-line`（原连线检查第 7 类的逐文件部分，R21 §4.4 移入结构 lint） |
| K13 | 有 `####` 的 playbook（角色 playbook 与 5.2 长形态）恰好有一个 `#### Steps`；被指针指向的标题存在；5.2 长形态若有 `**Where you are.**`，它是 S-P6 的事实表（末行 `Anything else`） | S-O1、S-O2、S-P6、5.2 长形态 | 机查 | 票的 STRUCTURE 判据：`playbook-steps`；`check_wiring.py` 第 1 类（B0） |
| K14 | 每个（角色，事件）只有一个处理处 | 5.3 唤醒处理簇 | 机查 | `check_wiring.py` 第 6 类（B2 末） |
| K15 | 原则只用固定标签，没有 `##`，不指向 playbook、脚本、mode | S-R1、S-R2 | 机查 | 票的 STRUCTURE 判据：`principle-body`、`principle-direction` |
| K16 | 能力技能里没有「下一步」「谁调用我」句型，也没有 playbook slug | S-C3 | 机查 | 票的 STRUCTURE 判据：`capability-next-step`、`capability-playbook-name`（R21 §0 第 6 条把连线检查第 3 类的句型部分移进结构 lint）。SSR 事实 7 与 L92 改写之前不报 finding（「X13 的先后」） |
| K17 | 只查两件事：概念驱动的技能没有被改写成编号步骤；同一种形态内部的标题写法一致 | S-C2、X2 | 判断 | 无（R21 §4.2 不查能力技能的正文形态） |
| K18 | 简报模板的首行、分隔线、占位写法正确；启动提示词是一行 | S-B1、S-B2 | 机查（一行）；判断（首行、分隔线、占位） | `check_wiring.py` 第 8 类（B0）查一行；S-B1 不在任何检查的规则表里 |
| K19 | playbook 里没有装能力的做法、原则的内容、共享概念的定义、别的技能的输出格式；没有编号步骤的约定不在 `playbooks/` 下 | S-P1、S-P2 | 判断 | 无 |
| K20 | 每次都读的 reference 已内联；reference 没有按主题拆 | S-F1、S-F2 | 判断 | 无 |
| K21 | 长度超过 S-G9 参照值的，已考虑改用规则簇或按分支拆 | S-G9 | 判断 | 无 |

### 7.3 点名

| # | 查什么 | 规则 | 方式 | 对应检查 |
|---|---|---|---|---|
| K22 | 跨文件不按编号引用（`step \d`、`Phase X`、`## N`） | X9、N4 | 机查 | 票的 STRUCTURE 判据：`numbered-cross-reference`（原连线检查第 4 类，R21 §0 第 6 条移入结构 lint） |
| K23 | 原则引用只用 `(**principle-<slug>**)` 一种写法，且 slug 存在 | N2 | 机查 | `check_wiring.py` 第 5 类（B1） |
| K24 | 点名的技能、reference、脚本子命令、playbook 都存在 | N1、N3、N7、N9 | 机查 | `check_wiring.py` 第 2 类（B1） |
| K25 | reference 指针带打开条件与用法；脚本调用写了何时跑、各种结果之后做什么，没有叙述脚本内部；脚本输出是建议时写明了判断归谁 | N7、N9、X12 | 判断 | 无 |
| K26 | 程序读的名字没有为文风改动；改名处的所有引用在同一张票里改掉 | N10 | 判断，辅以 `grep` | 无 |

### 7.4 写法

| # | 查什么 | 规则 | 方式 |
|---|---|---|---|
| K27 | 开头能通过 SSR L11 的开头测试：说得出为了什么、谁用、做浅了的代价 | W-G1、W-C1 | 判断 |
| K28 | 每条理由能通过 SSR L11 的句子测试；没有凭空编的理由 | W-G2、X1 | 判断 |
| K29 | 立场句同时写了诱惑与替代动作；没有「be careful」式的态度句 | W-G3 | 判断 |
| K30 | 没有这三种过度规定：能力足够的 agent 自己会做的编号流程、镜像脚本分支的 if-then 列表、可以用一个判据覆盖的枚举。也没有 agent 必须选择而文本沉默的地方 | W-G4 | 判断（SSR L43、L94） |
| K31 | 每个 `Done when` 都能失败，措辞穷尽；转交步骤的 `Done when` 写的是下一份 playbook 入口所读的状态 | W-G7、5.2 转交步骤 | 判断 |
| K32 | 每个 Never、Don't 旁边都有正面目标或理由 | W-G8、X3 | 判断 |
| K33 | 问人的地方问的是决定而不是事实，并写了无人出路 | W-G9、W-C2、W-P3 | 判断 |
| K34 | 术语一词一义，没有同义词轮换；能调出理论的术语在定义旁写了作者或著作，没被当成出处删掉；比喻只作 leading word 用 | W-G6、X4 | 判断 |
| K36 | 例子成对、用中性领域、标明是例子 | W-G11 | 判断 |
| K37 | 点名技能后没有复述它的规则；拆分后的能力技能与 playbook 没有同一句话的两份 | W-G12、S-P5 | 判断（SSR L40） |
| K38 | 简报粘贴了子代理要用的材料，并写了返回结构与长度上限；能力技能派的子代理简报没有 mode 那一句首句 | W-B1、5.7 | 判断 |
| K39 | 决定整个结果的那一步写明了为什么它决定结果，并要求了投入；没有每一步都这样写 | W-G13 | 判断 |

### 7.5 最可能的破坏（审查时先看这几处）

依据：SSR L142「Asked to "streamline", an agent shortens and cuts function with it」，以及 R20b 每条规则的「常见破坏」（推断）。

1. 首段或分支文件的目的段被当成背景删掉，只剩步骤（K27、K35）。
2. 理由句被当成冗余删掉；或者反过来，给每条规则补一句编出来的理由（K28）。
3. 概念驱动的技能被改写成编号清单，或者为统一形态重排了已有技能的节（K17、K2）。
4. 「pasted in full」被改成「参考某文件」，字数上限被删（K38）。
5. 「proceed if AFK」被删，技能在夜里卡住（K33）。
6. 穷尽的判据被缩成「列出变更」（K31）。
7. 搬运时顺手「润色」，包括改大小写（K2，机查会报出）。
8. 术语旁的作者署名被当成出处删掉（K34）。

---

## 8. 本文读了什么、没验证什么

**读了全文的**：R20a、R20b（随任务附来）；`SKILL-SET-RULES.md` 的现行版（逐行核对了行号）；squash 原文 `writing-for-agents/SKILL.md`、`SKILL-MECHANICS.md`（逐行核对了行号）；R18 的第 1–3.3 节、第 4 节与第 5 节的开头、5.1、第 7.5、7.8、7.9、8.2、8.3 节、第 16、17 节与审查记录。

**抽查了原文的**：pstack `authoring-a-skill.md`、`bug-fix.md` 全文；mode 第 11–40、97–121 行；`principle-attack-the-premise/SKILL.md` 全文；`how/references/explorer-prompt.md` 前 12 行；`orchestrate.md` 前 20 行与 `####` 列表；squash 原文 `code-review/SKILL.md` 第 55–90 行。这些与 R20a、R20b 的引文一致。审查轮另读了：SSR L3、L11、L17、L40、L52、L55、L62、L75、L92、L140、L142；squash 原文 `diagnosing-bugs/SKILL.md` L10–32、`prototype/LOGIC.md` L1–22、`prototype/UI.md` L1–18、`writing-for-agents/SKILL.md` L81；pstack mode L24–28、L101–107，`unslop/SKILL.md` L37，`show-me-your-work/SKILL.md` L75–81；R20a C2 第 8 项、C3 表、S2、第 9 节 P3 与 P4；R20b M1、M6 与冲突 C5；R21a 第 0 节、§3.1–3.4、§3.8、§4.2；R18 §2.2 `## Subagents`、§3.2、§4.5 末条、§7.5 表、第 10 节 B0 与 B1 行；`mmw-v2/skills/ui-acceptance/SKILL.md` 前 12 行与 `write-screen-contract/SKILL.md` 的 `##` 标题列表。

**没有逐条回原文核对的**：R20a、R20b 里其余 pstack 与 mattpocock 引文的行号，本文照录，标为出自这两份材料；R21a 的 §3.5–3.7、§3.9–3.10、§4.1、§4.3、§4.6–4.7 与第 5 节票 2、票 3 的正文没有读；R19a 只读了开头；R18 的第 6、7.1–7.4、7.6、7.7 节，以及 8.4 以后各节没有读。

**未经验证的**：本文各条写法对 agent 行为的作用，依据是 WFA 与 SSR 原文里的论断，没有做过对照运行。按 SSR L150，要让一个只拿到触发和真实任务的新 agent 跑一次才能确认。第一份范本（`exemplars/`）写成后，应当这样跑一次。

---

## 审查记录

本轮收到 16 条审查意见，逐条回原文核对，全部属实，均已修改。下面按意见顺序写出核对结果与改动位置。

1. **新写句子由谁起草（major）**。属实：R21a §3.2 `new` 行有带整句与不带整句两种，R21a §0 第 10 条承认两道检查管不到新写句子的质量，原文 T5 只要求出处。改动：T5 加「谁起草」一项，所有权行、首段、立场句、`**Why:**`、`Done when`、`**Reply:**` 与 T8 连接句都由写 spec 或范本的人写成整句，用 `new <目标> "<整句>"` 列出；不带整句的 `new` 只用在范本已给出写法并在票上点名范本段落的地方。开头「worker」一条、「spec 与范本」一条、第 0 节第 3、7 条、第 5 节引言、5.2/5.3/5.5 表里各「新写」格、T8、K4 同步改。
2. **出处种类与 T6（major）**。属实：SSR L140 认代码、tracker、记录过的运行、用户原话，并说交出目的、理由或立场的段落「needs no failed run behind it」；原 T6 与 K27 冲突。改动：T5「出处种类」按 SSR L140 补齐，允许标「推断」并要求句子本身在情况是推断时说明；T6 分两种，所有权行与 `**Why:**` 维持无出处不写，首段、立场句、`Done when` 缺出处时在票上记为未满足；K5 同步改。
3. **S-C2 一份文件一种形态（major）**。属实：`diagnosing-bugs/SKILL.md` L12 `## Redact` 规则节、L18 `## Phase 1`、L24–32 编号列表、L20 **tight** 均已核对；R20a C3 标题只说「选一种标题写法」。另发现 R21a §4.2 取舍第 2 条「强求统一形态就等于改写 mattpocock 的文字，与 D9 相反」同样支持这条意见，已引入。改动：S-C2 改为主形态加可并存的节，不为统一而重排；K17 改成只查两件事；第 7.5 节第 3 条加「重排已有技能的节」。
4. **分支文件骨架（major）**。属实：`LOGIC.md` L3–5、L7–14、L20 与 `UI.md` L14–16 已核对。改动：5.6 分支文件骨架加可选目的段与 `## When this is the right shape` 式条件列表，立场句按 W-G3 放在诱惑旁，写法出处逐项列出；「判断框架」一行加可选目的段；新增 W-F2。一处与意见不同：意见把出口句放在骨架最后，但 `LOGIC.md` L14 与 `UI.md` L5 都把出口句放在开头部分、紧跟适用形状或首段，让走错分支的读者立刻离开；本文按原文位置放，理由写在骨架里。
5. **删除怎样登记（major）**。属实：R21a §3.2 有 `drop` 行，§3.1 Q1 对 `drop` 豁免，R20 没有接上；SSR L142 原句已核对。改动：新增 T9；T1 改为「搬来、新写或登记过的删除」；W-G10 指向 T9；K35 移到 7.1，核对 `drop` 行与其理由；第 0 节第 3 条同步。
6. **术语作者与出处（minor）**。属实：SSR L52「other than the author of a concept」、L55「the name of the author or work a concept comes from」、L75 均已核对；R20b M6 的 `_Avoid_` 与作者两项原文 W-G6 漏写。改动：T5 加「概念的作者或著作不算出处」；S-R3 加一句；W-G6 补两项；K34 与第 7.5 节第 8 条同步。
7. **大小写（minor）**。属实：R21a §3.4 把大小写列为不允许的改写。改动：X14 裁决与理由写明搬来的标题保持原样、要改由 spec 写 `replace`；T2 第 3 项与 T3 注明大小写；S-P3 与 5.2 表编号步骤一行只约束新写标题；K2 注明含大小写。
8. **长的非角色 playbook（minor）**。属实：R18 §3.2 骨架里 `#### Steps` 标「长 playbook 才写这一行」，不限角色；R21a §4.2 `playbook-steps` 对所有自写 playbook 生效。改动：5.2 加「长形态」，用 5.3 骨架去掉 `**Where you are.**`、唤醒处理簇与 `#### Unattended outlets`；5.3 引言、S-G9、K13 同步。
9. **转交步骤的 `Done when`（minor）**。属实：SSR L62 已核对。改动：5.2 骨架与表中转交步骤写明判据取下一份 playbook `**Entry.**` 所读的可观察状态，写不出就并进前一步；K31 同步。
10. **拆分后的开头归属（minor）**。属实：R21a §3.1 `move` 的 `NOT-REMOVED` 与 `copy` 不查这一项已核对，SSR L40 Duplication 已核对。改动：新增 S-P5；5.2、5.3 首段格与 5.5 目标段格指向它；K37 同步。
11. **pstack 结构要点的覆盖（minor）**。属实：R20a C3「格式持有型」、C2 第 8 项、S2、第 9 节 P3 与 P4 均已核对，`show-me-your-work/SKILL.md` L79–81 原文已读。改动：S-C2 表加「格式持有型」；5.5 骨架与表加可选 `## Composing this skill`，并限定不点名调用方；X12 与 N9 加「建议写明判断归谁」；S-P1 加 P4；新增 S-M4 管 P3 的全称句。一处与意见不同：意见说 `ui-acceptance`、`write-screen-contract`「正是这种形态」，本轮看了两者的 `##` 标题（`## Find your moment`、`## Steps`），它们持有格式，但今天按分支型或步骤型组织；表里如实写出，并按 S-C2 不为套形态而重排。
12. **形式一首句用在能力技能里（minor）**。属实：R18 §2.2 `## Subagents` 首条已核对。补充：R18 §4.5 末条的「能力技能要能脱离 mode 使用」是 R18 为脚本方向规则写的推断理由，本文引用时注明了这一点。改动：5.7 形式一后加限定段；表中首句一行、S-C4、K38 同步。
13. **精力分配（minor）**。属实：`diagnosing-bugs/SKILL.md` L20、L22 与 WFA L81 已核对。改动：新增 W-G13；5.2、5.3 首段格与 5.5 做法格点名它；新增 K39。
14. **X5 的理由（minor）**。属实：pstack mode L26 把任何 prose surface 交给 `unslop`，`unslop` L37 规则 14 禁句中冒号，已核对。改动：X5 理由改为 pstack 对技能文本同样禁句中冒号，MMW 不采用的理由是 leading word 的定义句依赖冒号、SSR L3 与 L11 也这样用；同时注明 `check_upstream_em_dashes.py` 只查上游目录。
15. **机查项的可执行性（minor）**。属实：R21a §0 第 7、9 条、§3.8 的 AC7 与 AC8 形式、§4.2 规则表、R18 §7.5 表均已核对。改动：第 7 节加「在哪里跑」「何时生效」两段；7.1–7.3 每个机查项加「对应检查」一列，写出规则 id、Q1/Q2/Q3、连线检查类别与转为失败的批次。核对中另发现三处原文把判断项标成了机查，一并更正：K8（MMW 自有文字没有破折号检查，改为判断辅以 grep）；K11 的「显示名等于 H1」（R18 §7.5 第 5 类只比「何时适用」，X14 理由里「由连线检查第 5 类核对」同步改为「要加进第 5 类」）；K18 的 S-B1（不在任何规则表里）。K7 对能力技能与 reference 也改为判断。K16、K22 的对应检查按 R21a §0 第 6 条改为结构 lint。
16. **X13 依赖 SSR 先改（minor）**。属实：SSR L17、L92 原句与 R18 §7.9 第 1 条已核对；R21a §4.2 取舍末条也写明这处冲突「要在 B1 解决」。改动：第 2 节表后新增「X13 的先后」段；第 0 节第 4 条、S-C3、K16 同步。
17. **定稿对齐（不是审查意见）**：按 R21 第 7 节第 5、6、7 行改入。T1 中「清单之外」一句改为 R21 给的写法；第 7 节的结构 lint 改用 R21 的名字（`check_component_structure.py`、`STRUCTURE OK`、「票的 STRUCTURE 判据」、`structure-exceptions.tsv`），`CHECK:` 例子改为 `uv run --quiet`，预检写作 `run_shared_lints.sh`；K8、K11、K12 的方式与对应检查按 R21 第 4.4 节对照表改（K13、K16、K22 与对照表已一致，只换名字）；「B0 的三张检查票」改为五张。指 R21a 某节的引用改指 R21 同一节，S-C2 引的取舍条目按 R21 的编号改为第 3 条（第 8 节与本记录第 1 至 16 条记的是当时读 R21a 的情形，不改）。另：开头一条的 `exemplars/` 已建，去掉「尚未建」；5.1 表 `# <Name> mode` 一行的来源写 `mmw`（R18 第 17 节 D10）。

18. **从范本补写的约定（不是审查意见）**：`exemplars/README.md` `## 范本共用的约定` 列出五份范本一致执行、本文还没有写明的做法；范本审查（verbatim、style、consistency 三个角度）核实这些做法成立后，逐条补成规则，每条写出范本里的实例与它背后的原文：N9 改写为带解释器与技能根路径的写法（`issue_tree.py`、`events.py` 没有执行位）；新增 N11「child」、N12「`shared.md` rule N」、S-P6 事实表式 `**Where you are.**`、S-P7 `(judgement)` 的位置、S-P8 `**Entry.**` 的列表写法、S-O3 规则簇的顺序（5.3 骨架的注释随之改成与表一致）、W-O3 无人出路在 mode 与角色 playbook 之间的分工（W-G9 指向它）。5.2 长形态一段、5.2 表的 `**Entry.**` 与编号步骤两行、K12、K13 同步改。另按 R19 与 R18 第 17 节改掉几处旧名：`references/slots.md` → `pstack-names.md`，`anchors.py` → `locations.py`，5.3 标题里的 `run-one-ticket` → `land-one-ticket`，T9 例句与 5.3 骨架里的 Picked up yourself → Adopted ticket。

其他：原文末行「文件：<路径>」是上一轮返回格式留下的，不属于规范内容，已去掉。第 8 节补记了本轮为核对而读的原文范围。
