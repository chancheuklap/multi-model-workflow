# R19 MMW 改名表

本文给三类读者：你（只需看下面「用户过目」一节）；写这次升级 spec 与切票的会话（按第 4、5 节把名字写进票，按第 7 节生成 `renames.tsv`）；落地的 worker（只执行本票清单里抄入的改名行，R21 第 3.5 节）。它回答：升级后 MMW 自有的每个名字叫什么、为什么这样叫、改名要动多少东西。上游 mattpocock 与 pstack 的技能名、文件名、概念名一律不改（R18 第 17 节 D9）。

材料：清点 `R19a-name-inventory.md`（下称 R19a，方法见它第 1 节）；`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `### Vocabulary`（下称 SSR，第 74–82 行）；R18 第 1.3 节命名规则与第 17 节 D6、D7、D9；你已批准的词表决定 `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`（下称 DECISIONS，T、W 两组编号）与前一轮 `docs/reviews/2026-09-28-lightweight/vocabulary.md`（R、S 两组编号）；词表 `docs/contexts/*/CONTEXT.md`；消费仓库 `/Users/cheuklapchan/agentflow`、`/Users/cheuklapchan/xiaohuangya` 里点名 MMW 名字的文件（本轮 `grep`）。

标注：「现役 N」＝仓库去掉 `docs/research/` 后的匹配次数。标「本轮」的是本轮按 R19a 第 1 节的模式（前后不接字母、数字、`_`、`-`）在 `mmw-v2`、`docs`（去掉 `docs/research/`）、`prototypes`、`AGENTS.md` 里重数的，写成「次数/文件数」；没标的取自 R19a，R19a 之后文件已有变化，改名票动手前要重数。「新」＝R18 预定、仓库里还没有的名字，改它只改 spec 与票里的写法。「推断」＝由原文推出、原文没直接写。

---

## 用户过目

**唯一要你拍板的一项已定：mode 技能叫 `mmw`。** 你在 2026-09-29 夜间授权 Claude 完成剩余决定，这一项由 Claude 代定，记在 R18 第 17 节 D10，等你早上复核。理由：你在设计评审里对 D4 的问题写过「我直接调用新建的 mmw 技能不就可以了吗」；R18 D4 已写「人起的会话用 `/mmw`」；R20 第 5.1 节与 R21 的示例已经用 `skills/mmw/` 和指针前缀 `mmw <slug>#<Step title>`；你输入的命令也更短。放弃的备选是本表原先建议的 `mmw-mode`，它的理由是：`mmw` 同时是整套工具、`.mmw/` 目录、`mmw:` label 前缀和事件标记（R19a 第 15.1 节第 1 行），pstack 的 mode 名也带类型后缀 `poteto-mode`。留下的代价：`mmw` 一个词有几个相关的意思（工具箱、目录、label 前缀、mode），由这个技能的 description 与词表条目区分。你复核时若改为 `mmw-mode`，要改的是三处：技能目录 `skills/mmw/` 改为 `skills/mmw-mode/`，测试套件 `tests/mmw` 改为 `tests/mmw-mode`，唤醒行的指针前缀 `mmw <slug>#<Step title>` 改为 `mmw-mode <slug>#<Step title>`；你输入的命令随之变成 `/mmw-mode`。

**其余全部已按规矩定，不需要你决定。** 理由是它们不改你看到的界面、不改你记住的命令，也不改存进 GitHub 或消费仓库的东西：

- **事件名、label、`.mmw/target.json` 的键、票的 `CHECK:` 调用的判据脚本、消费仓库出包配置点名的四个 `exe-release` 脚本**：全部保留（第 5 节）。任务板上的显示名不变。
- **`dispatch.sh` 的 7 个子命令、3 个开关改名**（第 4.7、4.8 节）：只有 agent 与本仓库的脚本调用它们。任务板代码里没有这些命令名（本轮 `grep mmw-v2/board`，0 处）。你在根 `AGENTS.md` `## Commands` 里用的 `install.sh`、`models.py config` 都不改。
- **SSR 第 76 行的改写**（第 3 节）：这是技能写作规则，属于工程决定，按全局规则 1 由我定，改写文字与理由写在第 3 节，供你事后查看。
- **有一处消费仓库文档会过时**：`agentflow/docs/agents/issue-tracker.md` 第 52 行写着 `--sub-issue`。它只是说明文字，程序不读。R18 第 1.1 节已计划的那份 downstream-note 会列出这一行，不需要你操作。

---

## 0. 结论

1. **改 44 个名字，保留 261 个（另加第 5 节的全部标识符）。** 改的 44 个里，18 个是仓库里已有的名字（8 个 reference 文件、7 个 `dispatch.sh` 子命令、3 个开关），要进 `renames.tsv` 并在搬家的同一张票里改；26 个是 R18 预定、还没建的名字，只在写 spec 时换成新写法，不产生额外改动。汇总见第 8 节。
2. **mode 技能名保留 `mmw`**（R18 第 17 节 D10，由 Claude 代定，待你复核），理由与放弃的 `mmw-mode` 见上一节。
3. **改得最多的是三类最含糊的名字：**
   - 名字与内容相反或指向别的概念的（R19a 判「误导」）：`dispatch.sh wait`（它什么也不等）→ `result`；`--preflight`（它认领票并写事件）→ `--claim`；`dispatch.sh integrated`（它是一份票号清单）→ `landed-since`；`dispatch.sh open-ticket`（读作「开一张 issue」，其实是为一张票开 watch）→ `open-ticket-watch`；`edit-pages.md`（内容是建项目与记签字）→ `set-up-and-sign-off.md`；`slots.md`（与产品槽位同词）→ `pstack-names.md`。
   - 违反你已批准的词表决定的：DECISIONS W1 定裸词 interface 只指模块接口、用户界面叫 UI，所以 `design-an-interface`、`writing-interface-code.md`、`cutting-interface-tickets.md`、`interface-and-remake.md` 都改；T4 定 **release loop**、T13 定 **spec division**、T23 定 **code-writing rules**，文件名随之。
   - 同一个东西有两个名字的：认领（`--preflight` 与 **Claim**、`ticket.claimed`）、子票（`--sub-issue` 与 `child.opened`、`mmw:child`）、自己拿起的票（`adopt` 与 `self-picked-worker`、**Picked up yourself**）、出包配置（`key.md` 与 release manifest），各统一到程序已经在读的那个名字。出包配置的另外两个名字 `verify_key.py`、`.release-adapter.json` 被消费仓库点名，保留（第 5.2 节）。
4. **保留的主要理由有四种：**
   - 写进 GitHub 评论与消费仓库、改了收不回来的：全部事件名、label、`.mmw/target.json` 的键、票的 `CHECK:` 行按名字调用的判据脚本，以及消费仓库的出包配置与测试按文件名找的 `diagnose_core.py`、`fix_dispatch.py`、`release_contracts.py`、`verify_key.py`（第 5 节）。
   - 已经说得清楚的。
   - 改名收益抵不上代价的：如 `verify-ticket`，现役 717 处，还写在给消费仓库的 downstream-note 里；如 `evidence-page.md`，只是写法与邻居不同。
   - 上游用法：`<effort>` 与 `map-a-large-effort` 里的 effort 是 mattpocock 原文的「一块开发工作」（第 4.2、4.9 节），词表已有区分句。
5. **与 R18 两处不同。** (1) R18 把四份评审简报改名为 `review-axes/<axis>.md`，本表建议保留现名 `<axis>-reviewer.md`：它正是 pstack 同类文件的写法（`reflect/references/judgment-reviewer.md`），少一次改名。(2) R19a 列为「一义两名」的两对其实是两个概念，不改：lease 与 slot（词表 `docs/contexts/ui-acceptance/CONTEXT.md` `### The lease`：lease 是登记，slot 是登记分到的端口块与数据目录）；product answers 与 `.mmw/target.json`（同文件 **product answers**：`.mmw/` 下四样东西的总称，`target.json` 是其中之一）。
6. **一条旧规则要改写**（第 3 节）：SSR 第 76 行「程序、tracker、消费仓库读的名字不为文风改名」。改写后按「谁保存它」分：tracker 与消费仓库里存着的名字不改；只在本机、由本仓库程序读的名字，在它误导或一词多义时可以改，旧名留一版拒绝提示。第 4.7、4.8 节的 10 个子命令与开关改名以这条改写为前提。
7. **不需要专为本表写 downstream-note。** `downstream-notes/README.md` `## 什么改动必须写一份` 只管让消费仓库的 screen contract、票的 `CHECK:` 或 `.mmw/target.json` 失效的改动；本表把这三类读到的名字全部保留，也保留了消费仓库出包配置与测试点名的四个脚本（第 5.2 节）。本轮在两个消费仓库里 `grep` 本表要改的名字，只命中一处说明文字：`agentflow/docs/agents/issue-tracker.md` 第 52 行的 `--sub-issue`。R18 第 1.1 节已计划的那份 downstream-note（启动提示词、技能名、脚本路径）顺带列出本表改名与这一行。

---

## 1. 依据与方法

- **选词顺序**：领域既有术语（意思完全相符）＞普通词典词＞自造词并在首次出现处加粗定义（SSR 第 75 行）。借来的术语意思不符（false friend）比自造词更糟（同行）。比喻除非是 leading word，否则算问题（第 77 行）。
- **一词一义，占位符也算**（SSR 第 74 行）。
- **你已批准的词表决定优先。** DECISIONS 与前一轮的 R、S 行定了概念名，但当时把文件名、子命令、开关、事件名都划为「标识符，不动」（DECISIONS 首段「machine identifiers … stay byte for byte」）。这一轮你要求连文件名、脚本名一起改，所以本表让文件名跟上已定的概念名，而不另起新词。
- **代价按「谁读、存在哪里」分三档**（R19a 第 15.4 节）：只有人与 agent 读的，改文字即可；本机程序按字面读的，要改调用点与测试，并受 H5 约束（有 watch 开着时不发布）；写进 GitHub 评论、各仓库 issue、消费仓库文件的，改了就要别名或迁移，而且改后装回旧版本会读不懂新名字。
- **搬家时改名几乎不加成本。** R18 要搬的文件（`dispatch/` 整目录、`implement`、`code-review`、`wayfinder`、`triage` 里 MMW 加的 reference、分叉出来的 `to-spec`、`to-tickets`）本来就要改全部引用；不搬的能力技能（`design-pages`、`exe-release`、`write-screen-contract`、`ui-acceptance`）在 B1 也都有文字要搬出（R18 第 4.1 节），改名随那张票做（D9「改名在搬家的同一张票里做」）。
- **本轮自己核实的：**
  - 新名字在上述范围里的现有用法（本轮 `rg`）：`open-night`、`open-ticket-watch`、`close-night`、`landed-since`、`prepare-memory-decisions`、`resolve-child`、`--open-child`、`--closing-draft`、`--run-and-record-criteria`、`memory-records` 都是 0 处。
  - 撞上已有用法的三个：`merge-night` 撞上合并工作树名（`mmw-v2/tests/dispatch/test_dispatch.sh` 第 8523 行 `.worktrees/merge-night`），放弃；`--child` 3 处/2 个文件，是 `events.py child --child N`（`events.py` 第 13、896 行，`dispatch.sh` 第 4495 行），意思是要读的子票编号，所以开子票的开关改用 `--open-child`；`--claim` 29 处/9 个文件，全部在 vendored 的 `mmw-v2/upstream-unlazy/`（例：`templates/PLAN.md` 第 73 行「read by `--claim`」），是 gate-check 的开关，意思是认领一块 scope。判为可接受：两者都是「认领一块工作」的同一个意思；它们属于两个程序，不会出现在同一条命令行上；verify-ticket 不调用 gate-check 的 `--claim`（本轮 `rg`，`mmw-v2/skills/` 下 0 处）。
  - 判据脚本被票的 `CHECK:` 按裸名调用：`verify-ticket.py` 第 2868 行注释「name (`story-parity.py …`), and this process puts these directories on the PATH」，消费仓库票里的实例见 `downstream-notes/456-harness-markers.md` 第 11–12 行、`492-skeleton-by-data-ui-id.md`、`514-interface-tickets.md` 第 46 行。
  - 消费仓库的出包配置与测试按文件名找 `exe-release` 的脚本：`xiaohuangya/scripts/release/adapters/duck.release-adapter.json` 第 166 行 `${RELEASE_PLUGIN_DIR}/diagnose_core.py`、第 278 行 `fix_dispatch.py`；`agentflow/scripts/release/adapters/hedgehog.release-adapter.json` 第 195、314、322 行（`diagnose_core.py`、`fix_dispatch.py`、`release_contracts.py`）；`parrot.release-adapter.json` 第 264、272 行；`agentflow/tests/support/release_contracts_plugin.py` 第 47–95 行按文件名 `release_contracts.py` 找技能目录并加载模块；`agentflow/tests/contracts/test_release_key_verification_wire.py` 第 63–64 行 `load_skill_module("verify_key")`、`load_skill_module("release_contracts")`；`agentflow/scripts/release/release_event_sink.py` 第 8–10 行与 `release_key.py` 第 5 行点名这两个文件。技能一侧也写明配置会点名诊断器：`mmw-v2/skills/exe-release/scripts/release-flow.sh` 第 250–259 行 `_diagnose_argv_source`。

---

## 2. 命名规矩

每类组件一种句式。「核对」一列是能机械检查的部分，进 `check_wiring.py` 或结构 lint（R21 第 4 节）。所有句式只约束新名字与因误导而改的名字；现有名字不为统一句式改名（SSR 第 76 行改写稿「never for style」，第 3 节）。

| 组件 | 句式 | 理由 | 实例 | 核对 |
|---|---|---|---|---|
| mode | 品牌名本身，全套一个 | 你输入的命令就是品牌名（R18 D4「人起的会话用 `/mmw`」；R18 D10）；与整套工具、`.mmw/` 目录同词，由 mode 的 description 与词表条目区分。不照 pstack `poteto-mode` 加类型后缀（R18 D10） | `mmw` | frontmatter `name` 等于目录名 |
| playbook | MMW 自写的 playbook：标题是这类任务的名字，用户会怎么说就怎么写，祈使的「动词＋宾语」，只有首词大写。导入的 pstack playbook 保留原名；MMW 已有与 pstack 同一任务类型的，用 pstack 的名字。两种写法都要求 slug 是标题逐字转小写、空格换连字符，冠词保留 | 祈使句式是 MMW 自己的写法：自写 16 份里 14 份已这样写（R19a 第 15.3 节）。pstack 的标题多数是任务类型名词（`poteto-mode/SKILL.md` 第 121–143 行 `## Playbooks`；各 playbook 首行 `### Feature`、`### Investigation`、`### Orchestrate`），上游名不能改。路由表按任务描述匹配（同节「Match the task to a playbook」），两种句式并存不影响匹配。「slug＝标题」一条与 pstack 一致：23 份里 20 份满足（本轮逐份读首行，例外是 `worktree-cleanup`、`multi-phase-plan`、`authoring-a-skill`）；slug 由标题机械导出，才能检查、才不会一个东西两个名字 | **Work a ticket** · `work-a-ticket`；**Write a spec and tickets** · `write-a-spec-and-tickets`；导入的 **Feature** · `feature` | slug 等于标题转写；首行 `### <Name>` |
| 步骤 | `**<祈使短句>.**`，是锚点 | R18 第 1.3 节「标题就是锚点」；脚本指针 `mmw <slug>#<Step>` 靠它解析 | **Claim**、**Get reviewed** | 第 4 类 |
| 原则 | `principle-<slug>`；slug 读出来是一个判断（谁该怎样、什么成立），可以是祈使句或陈述句，不能只是话题名词；从 ADR 来的原则用 ADR 的 slug；只用 ASCII，不省撇号造成的歧义 | pstack 23 条里 17 条是祈使句（R19a 第 16.2 节），另 6 条话题名词（`boundary-discipline`）说不出判断；MMW 12 条多为陈述句，同样说出了判断，不为句式整批改；与 ADR 同名让 agent 能顺着名字找到理由（`silence-is-never-a-pass` 与 ADR 0008 同名） | `agents-are-woken-not-polled`（ADR 0010）；`clues-are-not-evidence` | 文件名＝frontmatter `name`（R21 `principle-frontmatter`） |
| 能力技能 | 它做的那件事（动词、`to-<产物>`、动名词）或它处理的东西（名词），用领域术语；配置技能用 `setup-<品牌>` | mattpocock 的四种句式（R19a 第 16.1 节）；配置技能对应 pstack `setup-pstack`；名字不取源文字里的小节标题（`shared-experience` 就是这样来的，说不出内容） | `ui-acceptance`、`write-screen-contract`、`memory-records`、`setup-mmw` | `install.sh` 查重 |
| reference | 小写连字符 `.md`，放 `references/`；名字说出它装的内容或它回答的问题，用词表里的名字；交给另一个 agent 的简报用 `<角色>-reviewer.md` 或 `<角色>-brief.md`；格式文件 `-format.md`；模板文件名里带 `template`；MMW 新加进 mattpocock 技能根目录的文件照 mattpocock 全大写 | pstack 的 reference 全部小写放 `references/`（R19a 第 16.2 节）；mattpocock 的技能根文件全大写（`LOGIC.md`、`UI.md`）；读者只看文件名就该知道何时打开它（R20b 第 3 节） | `release-loop.md`、`child-issues.md`、`standards-reviewer.md`、`screen-contract-format.md` | 第 2 类（指针可解析） |
| 脚本 | 名字说它执行的动作或它管理的东西，不用缩写，不用未定义的比喻；Python 新文件用下划线（能 `import`，测试不必经 `importlib` 绕路，`mmw-v2/tests/AGENTS.md` `## Key Conventions` 第 3 条）；宿主 hook 按名字调用的一族用连字符，与现有 `tool-guard.py`、`turn-guard.py` 一致。现有连字符文件不为统一写法改名；被票的 `CHECK:` 调用的、被消费仓库的配置或测试按文件名找的脚本一律不改名 | 这两类改名会让已落地票的 `--reverify`、产品的下一次出包失败（第 5.2 节）；其余连字符文件改名只换来写法一致 | `ticket_state.py`、`locations.py`、`hook-launcher.py` | 第 10 类（路径存在） |
| 子命令、开关 | 做事的子命令用动词，动词在本套里另有意思时加宾语；只读查询的子命令用它打印的东西命名；开关名说它做的事或它发出的东西；子命令不与任何开关同名 | 一词一义（SSR 第 74 行）：`open`、`route`、`summary` 各自撞上别的意思；现有的只读子命令 `status`、`findings`、`where` 都按打印的东西命名（`dispatch.sh` 第 368–395 行 usage）；子命令与开关同名时 grep 与 token 替换分不开 | 做事：`open-night`、`resolve-child`、`prepare-memory-decisions`；只读：`result`、`landed-since`；开关：`--claim`、`--closing-draft` | `check_wiring.py` 开关类 |
| 角色 | 做事的人的名词（`worker`、`reviewer`），变体加限定词 | 与 `models.json` 行名、事件 actor 一致 | `adopting-worker`、`one-ticket-orchestrator` | 第 6 类 |
| 配置、状态文件 | 名字说内容；装的是 JSON 就 `.json`，TSV 就 `.tsv` | 同 reference | `imports.tsv`、`pstack-rewrites.tsv` | — |
| 测试套件 | 被测技能的目录名，或被测子系统名 | 与现有 `tests/ui-acceptance`、`tests/relay` 一致 | `tests/mmw`、`tests/dispatch` | — |
| 事件名、label、`.mmw/target.json` 键、判据脚本名、消费仓库配置或测试点名的脚本 | 不改（第 3、5 节） | 存在 GitHub 评论、各仓库 issue、消费仓库文件里，改不回来 | — | — |

两条通用规矩：

- **改名跟着词表走。** 一个名字改了，`docs/contexts/*/CONTEXT.md` 的词条、所有引用它的技能文字一起改（SSR 第 80 行「the term, the entry and every skill using it change together」）；词表条目的 `_Home_` 指向新文件。第 6 节逐行列出要改的词条与 `_Home_` 行。
- **每批只写当时存在的名字。** 改名行按批次抄进票（R21 第 3.5 节「每张票只抄入本票要用的行」）；第 4 节每行写明批次。

---

## 3. SSR 第 76 行的改写建议

现文（`SKILL-SET-RULES.md` 第 76 行，节选）：「A name the program, the tracker or a consuming repository reads (a command, event, field, label, …) is copied verbatim and is not renamed for style.」

问题：它把两种代价差很多的名字放在一起。事件名存在 GitHub 评论里，每次 fold 从头重放，读不懂的块列为 `unreadable`，调用方拒绝判断（`events.py` 第 33–36 行）；label 贴在各仓库的 issue 上；判据脚本名写在消费仓库的票里；`exe-release` 的脚本名写在消费仓库的出包配置和测试里（第 1 节）。这些改了收不回来。而 `dispatch.sh` 的子命令、`ticket.py` 的开关只有本仓库的脚本、测试和技能文字读，改名的代价是改调用点，并且可以在一版里对旧名给出拒绝提示。按现文，`wait`、`--preflight` 这类名字与行为相反的命令也不能改。

改写为（英文，因为 SSR 是技能文字）：

> A name stored where this repository cannot rewrite it (an event or field in tracker comments, a label, a `.mmw/target.json` key, a script a ticket's `CHECK:` line calls, a script or module a consuming repository's configuration or tests name) is copied verbatim and never renamed. A name only this repository's own scripts read (a command, a flag, a file) is renamed when it misleads or gives one word two meanings, never for style; the renamed command or flag answers its old name, for one release, with a refusal naming the new one. Where the text names a concept by an identifier, the identifier is its one name.

代价：一处文字改动（SSR 属于 MMW 加进上游目录的文件，R18 第 1.1 节搬到 `mmw/references/skill-set-rules.md`，改写随那张票）。旧名的拒绝提示对第 4.7、4.8 节的 10 个名字各一行，按 **principle-refusals-name-one-next-step** 写。

---

## 4. 逐项改名表

列：现名 → 建议 → 理由（现名哪里不清楚，新名为什么更好）→ 代价（现役次数；是否程序按字面读；是否影响消费仓库；批次）→ 结论（改、保留、用户定、并入）。

### 4.1 技能名

| 现名 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `mmw`（新） | 保留 | 见「用户过目」 | 现役 2；新；你输入 `/mmw`；B1 | 保留 `mmw`（R18 D10） |
| `setup-mmw`（新） | 保留 | pstack 同职能技能叫 `setup-pstack`，description「Configure which models pstack uses per role」（pstack `skills/setup-pstack/SKILL.md` 第 3 行），与 `setup-mmw` 的主职相同；「首次安装」的误读（R19a 第 2 节）由 description 的分支句排除 | — | 保留 |
| `shared-experience`（新） | `memory-records` | 名字取自 `implement` 的小节标题，「experience」说不出 Nowledge Mem 的 Memory；词表把单条叫 Memory record（`docs/contexts/night/CONTEXT.md` **Memory closing**「every Memory record labelled `mmw-spec-<spec>`」）；同一件事的其他名字都用 memory（`saving-memory.md`、`--memory-decisions`）。不用 `shared-memory`：那是进程间通信的既有术语，会成假朋友 | 现役 1；新；B1 | 改 |
| `to-spec`、`to-tickets` | 保留 | 上游概念名（R18 第 4.1 节：分叉后仍用上游名） | — | 保留 |
| `verify-ticket` | 保留 | 升级后主职仍是跑一张票的判据（R18 第 4.1 节），lint 与发布写进 description 分支；改名要动现役 717 处，另有给消费仓库的命令 `verify-ticket.py <n> --lint`（`downstream-notes/514-interface-tickets.md` 第 46 行） | 若改：717 处＋`merge-notes/unlazy.md`＋消费仓库文档 | 保留 |
| `ui-acceptance`、`design-pages`、`write-screen-contract`、`exe-release`、`code-checkers`、`manage-agents-md`、`advisor` | 保留 | R19a 第 2 节判清楚；前三个是近期改过名的（downstream-notes 449、472、491） | — | 保留 |
| `retro` | 保留 | retrospective 是敏捷开发的既有术语（SSR 第 75 行第一顺位）；对象是一夜，写在 description 里；与上游 `skills/in-progress/retro/` 同名，但它不在 `skills.txt`，不会安装；与 pstack `reflect` 靠路由表的 Distinct from 句分开（R18 第 3.1 节） | 若改：现役 113 处＋`retro.py`、`tests/retro` | 保留 |
| `dispatch` | 解散（R18） | 名字只留在 `dispatch.sh`（第 4.7 节）、事件 stage 值（第 5 节）与 `fix_dispatch.py`（第 4.6 节）；技能不在了以后，前两处读作普通动词「派出」，与它们做的事一致 | — | — |

### 4.2 playbook 与被程序点名的步骤

全部是 R18 新定的名字（现役 0，除注明外），改名不产生额外改动；`roles.json` 的 `playbook` 字段、`locations.py` 的步骤登记、路由表、别的 playbook 里的「交给 X」、路由表各行的 Distinct from 句随 spec 一起写成新名。R18 里点名下表要改的旧 slug 或旧标题的行（本轮 `grep`）：第 123、124、127、202、203、303、307、435、468–472、479、481、482、491、492、498、527、533、535、540、549、553、557、564、565、569、580、585、592、639、642、650、911、919、1461、1465 行。例：第 498 行 B3 加的 **Feature** 行「Distinct from Direct change」、第 535 行 P1 **Decide who checks** 的去处「→ **Direct change**」、第 564 行 prototype 所有权行的「走 **Define a change** 或 **Direct change**」。写 spec 的会话照这张行号表逐处换成新名。

| 现名 · 标题 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `define-a-change` · **Define a change** | `write-a-spec-and-tickets` · **Write a spec and tickets** | 名字不提它交出的 spec 与票（R19a 第 6 节）；用户的原话是「把这个做成 spec」「切票」（R18 第 3.1 节 P1 行）；两件产物进名字，路由时一眼对上 | 新；P2、P3、P4、P6、P7 的交接句随改；B1 | 改 |
| `map-a-large-effort` · **Map a large effort** | 保留 | 现名出自上游原句：wayfinder 的 `agents/openai.yaml` 第 3 行 `short_description: "Map a large effort as decision tickets"`（`git show 5b1a4c51:skills/engineering/wayfinder/agents/openai.yaml`）；上游 wayfinder 正文第 9、13、34、38、86、97、99 行、`ask-matt` 第 44 行「A huge, foggy effort」都在「一块开发工作」的意思上用 effort，这些上游文字照装不改，所以 MMW 这一处改名消不掉这个意思。DECISIONS W6 只把「reasoning level」改成 **reasoning effort**（第 65 行），没有给开发工作另起名；词表 ui-acceptance **effort** 已有 Distinct-from 句区分两者（`docs/contexts/ui-acceptance/CONTEXT.md` 第 138–140 行）。按 SSR 第 76 行末句，照上游的意思用 | — | 保留 |
| `design-an-interface` · **Design an interface** | `design-a-ui` · **Design a UI** | DECISIONS W1：裸词 interface 只指模块接口（上游 `codebase-design`），用户界面叫 UI | 现役 4（R19a 第 6 节）；B1 | 改 |
| `direct-change` · **Direct change** | `make-a-small-change` · **Make a small change** | 「direct」可读成「直接动手改」；这份 playbook 的判据原文是「a change small enough that the user will check it directly」（残留 `ask-matt` 第 26 行，R18 第 3.3 节 P5 所有权行） | 新；P1 **Decide who checks** 的去处、B3 **Feature** 行的 Distinct from 句随改；B1 | 改 |
| `run-one-ticket` · **Run one ticket** | `land-one-ticket` · **Land one ticket** | 与 `work-a-ticket` 只差动词，名字说不出一个是编排、一个是亲手做（R19a 第 6 节）；这份流程的终点是 `dispatch.sh land <n>`（词表 night **land**），用 land 说出它的职责 | 新；角色名随改（第 4.9 节）；B2 | 改 |
| `run-a-night` · **Run a night**、`accept-the-night` · **Accept the night** | 保留 | night 保留的理由见第 5.4 节 | — | 保留 |
| `prototype`、`bug-fix`、`authoring-a-skill`、`session-pickup`、`pause-safely` | 保留 | pstack 同名任务类型（R18 第 1.3 节） | — | 保留 |
| `triage-an-issue`、`research-a-question`、`onboard-a-repository`、`deliver-a-change`、`work-a-ticket`、`review-a-ticket` | 保留 | R19a 判清楚；「change」在 `deliver-a-change`、`promote-a-change` 里指同一个东西（一次对仓库的改动），动词区分阶段，不算一词多义 | — | 保留 |
| 私有 `promote-a-change`、`pull-an-upstream`、`import-a-component`、`INDEX.md` | 保留 | 清楚；promote 是发布工程的既有词（前一轮 S4 **the four promotion steps**） | — | 保留 |
| 入口 **Picked up yourself**（`work-a-ticket`） | **Adopted ticket** | 同一概念另有命令 `adopt`（词表 night **adopt**）、字段 `adopted`（`dispatch.sh` 第 1017 行）、角色 `self-picked-worker`；程序读的是 `adopt`，按 SSR 第 76 行末句「the identifier is its one name」统一到 adopt | 新；`roles.json`、`locations.py` 随之；B2 | 改 |
| `#### After the closeout, picked up yourself` | `#### After the closeout of an adopted ticket` | 同上；现名用逗号连起两个短语，读不出是一个情形 | 新；`roles.json` 的（`adopting-worker`，`ticket.passed`/`ticket.returned`）登记指向它；B2 | 改 |
| **Claim**、**Get reviewed**、**Close out**、**Handle each wake**、**Closing pass**、`#### When the orchestrator resumes you`、**Active Rules** | 保留 | 清楚；**Claim** 与事件 `ticket.claimed` 同词，开关随之改为 `--claim`（第 4.8 节） | — | 保留 |

### 4.3 原则（MMW 自有 12 条）

全部新（R18 第 5.2 节），文件是 `mmw/principles/principle-<slug>.md`；改名只动 spec 写法。pstack 的 23 条不改。

| 现名 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `silence-is-never-a-pass` | 保留 | 与 ADR `0008-silence-is-never-a-pass.md` 同名，五个脚本的文件头引它（R19a 第 7 节） | — | 保留 |
| `the-tracker-is-the-state` | `resume-from-durable-state` | 规则管的是「续跑读持久记录，不读会话记忆」，记录还包括提交与出包引擎的状态（R18 第 5.2 节该行；`exe-release/references/driving.md` 第 5 行「Progress … come from release engine state」），`exe-release` 引用它时名字里的 tracker 对不上。durable 是「持久化」的既有术语；不用 record，因为词表里 record 已指 Memory record | 现役 0；B1 | 改 |
| `woken-not-polled` | `agents-are-woken-not-polled` | 规则来自 ADR `0010-agents-are-woken-not-polled.md`（R18 第 5.2 节理由出处列）；与 ADR 同名，同 `silence-is-never-a-pass` 的做法；现名是分词短语，缺主语 | 现役 3；B1 | 改 |
| `route-faults-dont-bypass` | `report-faults-through-the-pipeline` | `dont` 缺撇号，读不出是一句还是两句；「route」已指 mode 的任务路由与 `dispatch.sh route`（R19a 第 7 节） | 现役 0；B1 | 改 |
| `the-baseline-is-a-contract` | 保留 | DECISIONS W2 定裸词 contract 只指「票被要求遵守的东西」、`contract` 子票，本原则正是这个意思；screen contract 一律写全称 | — | 保留 |
| `no-secrets-in-artifacts` | `no-secrets-or-personal-data-in-artifacts` | 规则也管个人数据（R18 第 5.2 节：「凭据与个人数据不进任何产物」），名字只说 secrets；secret 在安全领域指凭据，不含个人数据 | 现役 0；B1 | 改 |
| `refusals-name-one-next-step`、`a-second-reader-judges`、`clues-are-not-evidence`、`one-home-per-meaning`、`human-steps-stay-human`、`decide-at-phase-boundaries` | 保留 | 各自读出一个判断（R19a 第 7 节判清楚） | — | 保留 |

### 4.4 mode 的节名与 playbook 骨架标记

| 现名 | 建议 | 理由 | 结论 |
|---|---|---|---|
| `## Non-negotiables`、`## Principles`、`## Autonomy`、`## Subagents`、`## Writing the reply`、`## Comments`、`## Playbooks` | 保留 | pstack mode 节名（`poteto-mode/SKILL.md`），导入的文字按它们找位置 | 保留 |
| `## Re-entry`、`**Entry.**`、`**Where you are.**`、`#### Steps`、`**Reply:**` | 保留 | 清楚（R19a 第 8 节） | 保留 |
| `### Imported triggers` | 保留 | R19a 判它「说来历不说作用」；但这一小节对读者要紧的正是来历：原文复制、由 `import_component.py` 按 mode-trigger 类型写入、不手改（R18 第 8.2 节） | 保留 |
| `## On waking`、`## Find your moment`、`## Next`、`## Reached from here` | 随 R18 去掉 | — | — |

### 4.5 reference 文件名

| 现名（所在处） | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `slots.md`（mode references，新） | `pstack-names.md` | 「slot」已指产品槽位（词表 ui-acceptance **slot**、事件 `worker.queued`），R18 中文两处都写「槽位」；内容是 pstack 里的名字（Cursor 工具、槽位、别名）在 MMW 读作什么（R18 第 8.3 节） | 新；`import_component.py` 与 `check_wiring.py` 第 2 类按文件名读；B1 | 改 |
| `orchestrator-events.md`（新） | `orchestrator-wakes.md` | 表里还有八种 `watchdog:` 告警、`MMW turn guard:` 行、`resume` 退出码，都不是事件（R18 第 3.3 节 P12）；它们共同的名字是 wake（词表 night **wake**） | 新；`roles.json` 的 `*` 唤醒登记与 `check_wiring.py` 第 6 类；B2 | 改 |
| `writing-code.md`（新） | `code-writing-rules.md` | DECISIONS T23 把这组规则定名 **code-writing rules** | 新；B2 | 改 |
| `tracker-additions.md`（新） | `issue-tracker-pipeline-sections.md` | 现名说来历（「加的东西」）；内容是写进消费仓库 `docs/agents/issue-tracker.md` 的流水线段落（三组 label 等，R18 第 3.3 节 P9），新名同时说出目标文件与内容 | 新；B1 | 改 |
| `review-axes/{standards,spec,tests,ui}.md`（R18 预定） | 保留现名 `standards-reviewer.md`、`spec-reviewer.md`、`tests-reviewer.md`、`ui-reviewer.md`，平放在 mode references | 现名就是 pstack 给评审简报的写法（`reflect/references/judgment-reviewer.md` 等三份）；现名已被 `mmw-v2/merge-notes/code-review.md`、`mmw-v2/upstream/skills/engineering/code-review/SKILL.md`、`mmw-v2/tests/verify-ticket/test_draft.py` 引用（本轮 `grep -rln standards-reviewer mmw-v2`；另有 `merge-notes/to-tickets.md`、`tdd.md`） | 比 R18 少一次改名；B2 | 保留 |
| `ps/`（mode `references/ps/`、`scripts/ps/`，新） | `pstack/` | 缩写，与 PowerShell 文件（`tests/exe-release/ps-syntax-check.ps1`）、Unix `ps` 同形（R19a 第 9 节） | 新；`import_component.py` 机械改写目标、`install.sh`、`check_own_skill_frontmatter.py`；B1 | 改 |
| `subagent-brief.md`、`skill-set-rules.md`、`reviewing-a-skill-set.md`、`pipeline-issues.md` | 保留 | 清楚；brief 是前一轮 R2 定的词 | — | 保留 |
| `interface-and-remake.md`（`wayfinder/references/` → mode references） | `ui-and-remake-tickets.md` | DECISIONS W1；文件标题是「Tickets for an interface or a remake」，名字漏了「票」 | 现役 28/10（本轮）；词表 3 个 `_Home_`（第 6 节）；搬家同票；B1 | 改 |
| `session.md`（`code-review/references/`） | 并入 **Review a ticket**，名字消失 | `dispatch.sh` 第 1747–1751 行的 Rules 包改从 `locations.py` 取 `review-a-ticket#Active Rules`（R18 第 7.6 节） | B2 | 并入 |
| `night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md`（`dispatch/references/`） | 并入 playbook 与 `setup-mmw`，名字消失 | `watchdog.py` 第 735、780 行点名 `night.md` 的告警文字随 R18 改成步骤指针 | B2 | 并入 |
| `advising.md`、`consulting.md`（`advisor`） | 保留 | 成对：被问方与提问方 | — | 保留 |
| `git-hooks.md`、`python.md`、`typescript.md`（`code-checkers`） | 保留 | 清楚 | — | 保留 |
| `design-system.md`、`pull.md`、两份 `template-*-claude-md.md`（`design-pages`） | 保留 | 清楚；`pull.md` 被 `contract` 子票正文按字面点名（`pull.md` 第 3 行） | — | 保留 |
| `draw.md`（`design-pages`） | 保留 | 两个情形（照排队的评论改页面、按要求画新页面）做的都是画，动词说对了 | — | 保留 |
| `edit-pages.md`（`design-pages`） | `set-up-and-sign-off.md` | 文件的节是 `## Create the project`、`## Talking to the agent inside Claude Design`、`## Sign-off`、`## Next`（本轮 `grep '^## '`），改页面在 `draw.md`；词表 **edit pages** 已按 DECISIONS「Definitions corrected」改为描述建项目与签字。`docs/adr/README.md` 第 54 行点名它的 `## Sign-off`，第 23、25 行经「见表下注」指向第 54 行；DECISIONS「Found on the way」第 112 行记的「把一项截图检查记在它名下」，在第 54 行现文里已看不到（本轮只读这三行，推断已更正） | 现役 52/17（本轮）；程序不读；词表 7 个 `_Home_`（第 6 节）；`design-pages/SKILL.md` 分支名同改；B1（`design-pages` 搬出 `## Next` 的同票） | 改 |
| `state-list-format.md`（新） | 保留 | 与 `screen-contract-format.md` 同句式 | — | 保留 |
| `driving.md`（`exe-release`） | `release-loop.md` | 「driving」是比喻；DECISIONS T4 把一个产品从 `init` 到 `close`/`abort` 的一次运行定名 **release loop** | 现役 67/11（本轮）；`release-flow.sh` 第 1338 行与 `fix_dispatch.py` 第 4 行按字面点名；消费仓库 0 处（本轮 `grep`）；词表 7 个 `_Home_`（第 6 节）；B1 | 改 |
| `key.md`（`exe-release`） | `release-manifest.md` | 文件标题是「Write a release manifest」；词表 release **release manifest**；「key」让人先想到签名密钥。第三个名字 adapter 是程序字面（`.release-adapter.json`、`--adapter`），保留在程序里 | 现役 76/8（本轮；含 `upstream-diagram-design` 里无关的 `key.md`）；程序不读；消费仓库 0 处（本轮 `grep`）；词表 16 个 `_Home_`（第 6 节）；B1 | 改 |
| `new-product.md`（`exe-release`） | 保留 | 清楚 | — | 保留 |
| `create.md`、`rewrite.md`（`manage-agents-md`） | 保留 | 放在技能目录里时清楚 | — | 保留 |
| `boundary-check.md`、`harness-guard.md`、`journey.md`、`story-parity.md`（`ui-acceptance`） | 保留 | 与同名判据脚本成对；脚本名不能改（第 5.2 节），reference 随脚本 | — | 保留 |
| `product-answers.md`（`ui-acceptance`） | 保留 | 与 `.mmw/target.json` 不是一义两名（第 0 节第 5 条） | — | 保留 |
| `writing-interface-code.md`（`implement/references/` → `ui-acceptance/references/`） | `writing-ui-code.md` | DECISIONS W1 | 现役 53/19（本轮）；搬家同票；`merge-notes/implement.md` 的条目随 `implement` 回原文删除；B2 | 改 |
| `linting.md`（`verify-ticket`） | 保留 | 清楚 | — | 保留 |
| `sub-issues.md`（`verify-ticket`） | `child-issues.md` | 同一概念在事件与 label 里叫 child（`child.opened`、`mmw:child`、`CHILD_KINDS`），这些是写进 GitHub 的名字，不能改；词表把 sub-issue 定为 tracker 自带的父子关系（tickets **sub-issue**），把票下面带 kind 的 issue 叫 child（ticket-run **child kind**）；新名取 child 并保留 issue 一词 | 现役 49/18（本轮）；词表 3 个 `_Home_`（第 6 节）；与开关 `--open-child` 同批，B2 | 改 |
| `screen-contract-format.md`（`write-screen-contract`） | 保留 | 清楚；`lint_screen_contract.py`、`story-parity.py` 的拒绝文字按字面点名 | — | 保留 |
| `saving-memory.md`（→ `memory-records/references/`） | 保留 | 与 DECISIONS T17 **save conditions** 同义 | — | 保留 |
| `revising-a-spec.md`（`to-spec`） | 保留 | 清楚 | — | 保留 |
| `several-specs.md`（`to-spec`） | `spec-division.md` | DECISIONS T13 定名 **spec division** | 现役 13/8（本轮）；词表 1 个 `_Home_`（第 6 节）；分叉搬家同票；B1 | 改 |
| `ambiguity-scan.md`、`person-ticket.md`（`to-tickets`） | 保留 | 清楚；person 与 human 两词指同一类事，但 `ready-for-human` 是上游 label、`person` 出自上游 `triage-labels.md`，不值得为统一改文件名 | — | 保留 |
| `cutting-interface-tickets.md`（`to-tickets`） | `screen-contract-tickets.md` | 文件标题「Tickets from a screen contract」，内容是一份 screen contract 产生的五种票；DECISIONS W1 与 T14（**page ticket** 取代 interface ticket） | 现役 100/21（本轮）；程序不读；词表 8 个 `_Home_`（第 6 节）；分叉搬家同票；`merge-notes/to-tickets.md` 随分叉处理；B1 | 改 |
| `EXP.md`、`VISUAL.md`（MMW 加进 `prototype`、`wait-what` 技能根） | 保留 | 照 mattpocock 全大写 | — | 保留 |
| `evidence-page.md`（MMW 加进 `prototype` 技能根） | 保留 | 现名说清了内容，不误导，也不一词多义；同目录的 `LOGIC.md`、`UI.md`、`EXP.md` 全大写，只有它小写（R19a 第 15.3 节），但这只是写法不同，按第 3 节改写稿「never for style」不改。另有两项代价：本机 macOS 默认文件系统不分大小写，只改大小写的 git 改名要分两步做；路径检查会把大小写写错的链接当作存在，掩盖漏改 | 若改：22/10（本轮，其中 `docs/reviews/` 18 处、`prototypes/code-landing/ui-gate/EXP/README.md` 1 处） | 保留 |

### 4.6 脚本文件名

| 现名（升级后位置） | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `dispatch.sh`（mode scripts） | 保留 | 词表 night **`dispatch.sh`** 定义为流水线的命令行；技能解散后它是唯一叫 dispatch 的组件，读作普通动词；改名要动现役 746 处 | 若改：746 处＋`tests/dispatch`＋宿主 hook 拒绝文字 | 保留 |
| `relay.py`、`watchdog.py`、`statedir.py`、`ghlist.py`、`events.py`、`runners/{orca,paseo,herdr}.sh`、`turn-guard.py`、`mode-hook.py`（新） | 保留 | 清楚（R19a 第 4 节） | — | 保留 |
| `status.py` | 保留 | 它是一张 spec 的只读视图；计划与位置都是从状态算出来的，名字没说错 | 若改：131 处 | 保留 |
| `models.py` | 保留 | 管的是每个角色用哪个模型、在哪个宿主上以什么 effort 起（词表 **model-and-level pair**，DECISIONS T1）；你用它的命令写在根 `AGENTS.md` `## Commands`；runner 按同目录路径找它（R18 第 1 节） | 若改：114 处＋本机习惯 | 保留 |
| `tool-guard.py` | 保留 | 与 `turn-guard.py` 成对，各按它检查的对象命名：每次工具调用、每次回合结束；改名要重登记宿主 hook 并重算 Codex `trusted_hash`（根 `AGENTS.md` `## Gotchas` 第 3 条） | 若改：宿主配置＋44 处 | 保留 |
| `ticket.py`（新） | `ticket_state.py` | 与 `verify-ticket.py` 都「操作一张票」（R19a 第 4 节）；它的每个命令都往票上写事件、`fold` 从事件算出票的状态（ADR 0019 `ticket-state-is-a-fold-of-events`），新名说出它管的是票的状态。`verify-ticket.py` 跑判据只打印结果、不写事件（R18 第 719 行）；`ticket_state.py` 的判据开关是「跑并记录」，开关名说出这一点（第 4.8 节） | 新；`tool-guard.py` 的 `REFUSAL`、P15 各步、`tests/mmw`；B2 | 改 |
| `anchors.py`（新） | `locations.py` | 登记的有三样：文字锚点、跨目录路径、事件到步骤的 `where` 表（R18 第 7.2、7.7 节）；anchor 只说得出第一样。三样都是「一个东西在哪里」 | 新；`dispatch.sh`、`relay.py`、`board/`、`retro.py`、`install.sh`、`check_wiring.py` 按名导入；B0 | 改 |
| `mmw-hook.py` → `~/.mmw/bin/mmw-hook`（新） | `hook-launcher.py` → `~/.mmw/bin/hook-launcher` | 它是按名字启动全部 hook 的启动器（R18 第 7.3 节），`mmw-hook` 读作「一个 hook」，与 `mode-hook.py` 并列时分不清 | 新；五个宿主的 hook 命令字符串；B0 首次登记就用新名，避免 Codex 再弹一次「hooks need review」 | 改 |
| `import_component.py`（新） | 保留 | 清楚 | — | 保留 |
| `pstack.map`（新） | `pstack-rewrites.tsv` | 「map」已指 wayfinder 的地图（`mmw:map`、`--map N`）；内容是机械改写表；扩展名按格式（推断为 TSV，同 `imports.tsv`；格式由建它的票定，不是 TSV 就换扩展名） | 新；`import_component.py`；B1 | 改 |
| `check_wiring.py`（新；测试在 `tests/skill-text`，第 4.9 节） | 保留 | wiring 在依赖注入里指把组件互相连上（如 Spring 的 autowiring，推断：本轮未查原始文献），12 类检查里 10 类是连线；在 toolbox 词表加一条定义 | — | 保留 |
| `check_verbatim_moves.py`（R21 新起） | 无 | 逐字搬运检查；名字说出它查的东西：清单里的搬运是否逐字；与 `tests/lib/` 现有 `check_*.py` 同句式 | 新；B0 | 新（R21 第 6 节） |
| `check_component_structure.py`（R21 新起），词条 **structure lint** | 无 | 结构 lint；组件的结构是 R18 第 3.2 节、R20 第 5 节的用词。不用 `check_component_skeletons.py`、「skeleton lint」：skeleton 在词表里已指 `extract_skeleton.py` 写出的 JSON（ui-acceptance **skeleton**），违反 SSR 第 74 行一词一义 | 新；B0 | 新（R21 第 6 节） |
| `skill_text.py`（R21 新起） | 无 | 逐字搬运检查、结构 lint、`check_wiring.py` 共用的 Markdown 切分与组件归类；名字说出它管的东西：技能文字；Python 新文件用下划线（第 2 节「脚本」） | 新；B0 | 新（R21 第 6 节） |
| `run_shared_lints.sh`（R21 新起） | 无 | 每个套件 `run.sh` 开头调的共用检查入口；与词表已有的 **shared lints**（`docs/contexts/toolbox/CONTEXT.md`）同名。不用 `preflight.sh`：第 4.7 节为 `dispatch.sh check` 放弃 preflight 的理由同样适用 | 新；B0 | 新（R21 第 6 节） |
| `verify-ticket.py`、`issue_tree.py` | 保留 | 见第 4.1 节；`issue_tree.py` 清楚 | — | 保留 |
| `boundary-check.py`、`harness-guard.py`、`journey.py`、`story-parity.py` | 保留 | 票的 `CHECK:` 按裸名调用，消费仓库里已落地的票在 `--reverify` 时还会调用（第 5.2 节） | — | 保留 |
| `lease.py`、`target_config.py`、`design_render.py`、`pixel_diff.py`、`refusal.py` | 保留 | `lease` 是词表概念；`target_config.py --check` 写在给消费仓库的 downstream-note 450 与 `onboard-a-repository` 步骤里；其余清楚 | — | 保留 |
| `check_editable_selectors.py`、`pull_design.py`（`design-pages`） | 保留 | 清楚 | — | 保留 |
| `diagnose_core.py`（`exe-release`） | 保留 | 消费仓库的出包配置按文件名调用它：`duck.release-adapter.json` 第 166 行、`hedgehog.release-adapter.json` 第 195 行（第 1 节）；改名后这些产品下一次出包的 diagnose 步骤找不到脚本。「core」说不出内容的问题由正文与词表解决：正文一律叫它 **diagnoser**（词表 release **diagnoser** 的定义已是「`diagnose_core.py`, the skill's general rule table …」） | 若改：现役 27＋消费仓库两个配置＋downstream-note＋旧名留一版 | 保留 |
| `fix_dispatch.py`（`exe-release`） | 保留 | 消费仓库的出包配置按文件名调用它做 P1 修复：`duck` 第 278 行、`hedgehog` 第 314 行、`parrot` 第 264 行。正文一律叫它写的东西 **fix brief**（词表 release **fix brief**，输出行 `FIX-BRIEF=<path>`）；文件名里的 dispatch 在 `dispatch` 技能解散后读作普通动词「分派修复」 | 若改：现役 27＋三个配置 | 保留 |
| `release_contracts.py`（`exe-release`） | 保留 | 消费仓库按文件名找它：`hedgehog` 第 322 行、`parrot` 第 272 行的 event sink 参数；`agentflow/tests/support/release_contracts_plugin.py` 第 47–95 行按这个文件名找技能目录并加载模块；`agentflow/scripts/release/release_event_sink.py` 第 8–10 行。文件名里的 contract 与 DECISIONS W2（裸词 contract 只指票的 contract）不一致，由正文统一叫它的三个数据结构名（`ReleaseAdapterManifest`、`ReleaseFinding`、`ReleaseLoopEvent`）解决 | 若改：现役 44＋两个配置＋agentflow 测试 | 保留 |
| `verify_key.py`（`exe-release`） | 保留 | 消费仓库的测试按模块名加载它（`agentflow/tests/contracts/test_release_key_verification_wire.py` 第 63 行 `load_skill_module("verify_key")`），`agentflow/scripts/release/release_key.py` 第 5 行点名它。另外 `verify_key` 还是出包引擎的保留阶段名：`release_contracts.py` 第 68–71 行 `ENGINE_STAGE_NAMES = ("verify_key", "assemble", "build")`、第 90–92 行拒绝产品配置用这个名字，`release-flow.sh` 第 388–389 行生成这个阶段，第 879 行的日志目录名是 `a0-verify_key`，`key.md` 第 49 行把它当阶段名。改名会让旧出包循环的目录与日志名对不上。正文一律叫它检查的东西 release manifest | 若改：现役 19＋agentflow 测试＋阶段名与日志目录 | 保留 |
| `builders/nuitka.py`、`release_script_assembler.py`、`release_templates/nuitka_electron.ps1.tmpl`、`release-flow.sh` | 保留 | 清楚 | — | 保留 |
| `check.sh`（`manage-agents-md`） | 保留 | 放在技能目录里时说得出对象，同 `create.md` | 若改：58 处 | 保留 |
| `retro.py`、`dump_openapi.py`、`lint_screen_contract.py` | 保留 | 清楚 | — | 保留 |
| `extract_skeleton.py` | 保留 | 消费仓库票的 `CHECK:` 调用它（`downstream-notes/492-skeleton-by-data-ui-id.md`「调用 `extract_skeleton.py` … 的 ticket `CHECK:`」）；skeleton 在词表有定义（ui-acceptance **skeleton**） | — | 保留 |
| `tests/lib/` 各检查、`parse_k.sh`、`run_unittests.py`、`migrations/remove-verifier.py`、`install.sh`、`prompt/render.py` | 保留 | 清楚 | — | 保留 |

### 4.7 `dispatch.sh` 子命令与参数

子命令随 `dispatch.sh` 在 B2 整目录搬进 mode 时改。这一批只在没有 watch 开着时发布（D5），所以不会有正在跑的夜读到新名字。旧名保留一版，只打印一行拒绝并点名新命令（第 3 节）。

| 现名 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `open <spec>` | `open-night <spec>` | 与 GitHub 的 open issue 同词，不说开的是夜；与 `close-night` 成对，也与任务板对 `spec.opened`、`spec.closed` 的显示名「Night opened / Night closed」对上 | 现役 22；`turn-guard.py` 第 25 行、`install.sh` 第 1625 行等处写成不带参数的 `dispatch.sh open`（本轮核对这两处），`relay.py`、`watchdog.py` 另有命中（推断是提示句）；词表 night **open** | 改 |
| `open-ticket <n>` | `open-ticket-watch <n>` | R19a 第 176 行判它含糊：读作「开一张票（issue）」，撞 GitHub open issue 比 `open` 更直接；它做的是为夜外的一张票开一个 relay watch，本会话成为该票的 orchestrator（`dispatch/references/one-ticket.md` 第 7 行；词表 night **open-ticket**）。新名说出开的是 watch（词表 night **watch**）。不用 `watch-ticket`：它读作「盯着一张票」，漏了「开」这个动作，也与 `open-night` 不成对 | 现役 7（R19a）；词表 night **open-ticket**；`land-one-ticket` playbook 的第一步随改 | 改 |
| `summary <spec> --memory-decisions <file>` | `close-night <spec> --memory-decisions <file>` | 它发 `NIGHT SUMMARY`、关 watch、写 `spec.closed`，主要效果是关掉一夜；与 `status.py --summary`（只打印）同名不同事 | 现役 10；只在 `dispatch.sh` 与测试；词表 night **summary** | 改 |
| `wait <n> worker\|reviewer` | `result <n> worker\|reviewer` | 注释原文「It waits for nothing」（`dispatch.sh` 第 2284–2290 行），词表已按 DECISIONS 更正为「does not block」；它只读一次结果事件，是只读查询，按第 2 节规矩用它打印的东西命名；与 `events.py result` 做的是同一件事（`events.py` 第 47 行「`result` prints the event's name and its key fields」） | 现役 10；词表 night **wait** | 改 |
| `integrated <n>` | `landed-since <n>` | 读作「是否已集成」；它列出本票开始后合进 base 的兄弟票（`dispatch.sh` 第 2480–2483 行），是只读查询；land 是词表里「合进 base」的动词 | 现役 11；Spec axis 简报点名；词表 night **`dispatch.sh integrated`** | 改 |
| `memory-list <spec>` | `prepare-memory-decisions <spec>` | 它写出一个待填的 **`--memory-decisions` file** 骨架（词表 night **memory-list**），是做事的命令，按规矩用动词加宾语。不用 `memory-decisions`：与 `close-night` 的开关 `--memory-decisions` 完全同名，grep 与 token 替换分不开；不用 `draft-memory-decisions`：draft 在本套已指 closing-comment draft（`--closing-draft`）与票草稿（`--drafts`） | 现役 7 | 改 |
| `route <ticket> <child> …` | `resolve-child <ticket> <child> …` | 「route」同时是 mode 的任务路由；它做的是登记一个子票的结局，代码里叫 resolution（`events.py` `CHILD_RESOLUTIONS`） | 现役 28；词表 night **route**、**closing pass** 定义随改 | 改 |
| `finish <spec>` | 保留 | R19a 第 195 行判含糊：不说合并。仍保留：它是一夜的最后一步，词表 night **`dispatch.sh finish`** 已写明它合并并写 `spec.merged`；考虑过 `merge-night`，与合并工作树 `.worktrees/merge-<branch>` 在分支名为 night 时同名（`tests/dispatch/test_dispatch.sh` 第 8523 行），放弃 | — | 保留 |
| `check <spec>` | 保留 | R19a 第 174 行判含糊。仍保留：它与 `install.sh --check`、`target_config.py --check` 是「只读检查」同一个意思（第 5.3 节），词表 night **check** 列出它查什么；考虑过 `preflight`（开夜前的只读检查正是 preflight 的本义），放弃：`--preflight` 在历史评论、Memory、旧文档里指认领，复用会造成本套自己的假朋友 | — | 保留 |
| `advance <spec>` | 保留 | R19a 第 180 行判含糊（`advance`、`land`、`finish` 三个动词都做合并）。仍保留：它做的不只是合并，还交还到期的认领、启动 frontier（词表 night **advance**「lands the batch's passed tickets on origin, gives back claims whose holds ended, then starts the frontier」），「推进一批」正是 advance 的本义；三个合并动词的范围不同，词表 **land** 已写明它是「the one-ticket form of **advance**」 | — | 保留 |
| `adopt <n>` | 保留 | R19a 第 178 行判含糊。仍保留：它是「自己拿起的票」这一概念程序已在读的名字（字段 `adopted`），第 4.2、4.9 节把另外几个名字统一到它 | — | 保留 |
| `suspend`、`land`、`integrate`、`start`、`advise`、`retract`、`ack`、`resume`、`status`、`findings`、`reverify`、`board`、`self`、`where`（新）、`panel`、`panel-wait`（新，按需）、`research`（新） | 保留 | R19a 第 5.1 节判清楚，或词表已定义 | — | 保留 |
| `--into`、`--memory-decisions`、`became-ticket`、`fixed-elsewhere` | 保留 | 清楚；后两个是 `events.py` 的取值，写进历史 | — | 保留 |
| `--tools <dir>` | 保留 | 读者是程序与测试（现役 69），改名收益小 | — | 保留 |

### 4.8 `verify-ticket.py`、`ticket_state.py` 的开关；其他脚本的子命令

开关随 R18 第 4.1 节搬进 `ticket_state.py` 时改（B2）；`verify-ticket.py` 上的旧开关回一行拒绝，点名 `ticket_state.py` 的新开关。

| 现名 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `--preflight` | `--claim` | preflight 通常指只读预检；它认领票并写 `ticket.claimed` 或 `ticket.refused`（`verify-ticket.py` 第 4143 行 help）；步骤叫 **Claim**、事件叫 `ticket.claimed`，统一到程序已写进历史的那个词。与 vendored gate-check 的 `--claim` 同词，判为可接受（第 1 节） | 现役 60；词表 ticket-run **preflight** 并入 **claim**；打印行 `NOT_READY:`、`READY:` 不变 | 改 |
| `--draft [out]` | `--closing-draft [out]` | 与 `--drafts <dir>`（票草稿目录）只差一个字母；前一轮 R9 已把它的产物定名 **closing-comment draft** | 现役 21 | 改 |
| `--sub-issue <kind> <file>` | `--open-child <kind> <file>` | 它开一个带 kind 的 child，写 `child.opened`（见 `sub-issues.md` 一行）；动词加宾语，与 `resolve-child`、`child.opened` 一致。不用 `--child`：`events.py child --child N` 已用它表示要读的子票编号（`events.py` 第 13、896 行），`events.py` 会随 `ticket_state.py` 搬进同一个 `scripts/` 目录，同一目录里两个 `--child` 意思与参数形状都不同 | 现役 53；消费仓库 `agentflow/docs/agents/issue-tracker.md` 第 52 行点名旧名（说明文字，进 R18 第 1.1 节的 downstream-note） | 改 |
| `ticket.py <n> --check`（新） | `ticket_state.py <n> --run-and-record-criteria` | `--check` 与 `--check-only`、`install.sh --check`、`target_config.py --check` 同词；它跑全部判据并把这次运行记为 `ticket.checked`（R18 第 657、660 行 P15 第 4、7 步；第 719 行）。与 `verify-ticket.py <n>` 的区别在「记录」：后者跑同样的判据，只打印、不写事件。开关名只说「跑」，agent 可能直接调 `verify-ticket.py`，运行就没被记下。词表加一句区分：「`ticket_state.py <n> --run-and-record-criteria` runs the same criteria as `verify-ticket.py <n>` and records the run as `ticket.checked`; `verify-ticket.py <n>` only prints」 | 新 | 改 |
| `--reverify`、`--lint`、`--drafts`、`--publish`、`--spec-body`、`--title`、`--map N`、`--closeout`、`--check-only`、`--decisions`、`--review`、`--touched`、`--actor worker\|main`、`--tools`、`fold`、`--where`（`status.py`） | 保留 | 清楚或已在词表定义；`--touched` 发的是 `worker.touched`（第 5.1 节），名字说出了「被碰到的票」；`--actor` 的 `main` 是事件 actor 值（第 5.1 节） | — | 保留 |
| `relay.py`、`watchdog.py`、`turn-guard.py`、`tool-guard.py`、`status.py`、`events.py`、`retro.py`、`lease.py` 的子命令 | 保留 | R19a 第 5.3 节判清楚；`status.py --summary` 与 `dispatch.sh summary` 的撞名随 `close-night` 消失 | — | 保留 |
| `models.py runner` 与 `models.py config runner` | 保留 | 一读一写，只差前缀，读者主要是程序；R18 新加的 `config get <label>` 在 spec 里写成 `config get <role>` | — | 保留 |

### 4.9 配置、登记值、角色、状态文件、任务板、测试套件

| 现名 | 建议 | 理由 | 代价 | 结论 |
|---|---|---|---|---|
| `+model`（`skills.txt` 行尾标记，新） | `+model-invoked` | 旁边的 `models.json`、`models.py` 里 model 都指 LLM，现名读作「加一个模型」；model-invoked 是 mattpocock 的术语（`SKILL-MECHANICS.md` 第 9 行「A **model-invoked** skill keeps a `description`」） | 新；`install.sh`、`check_own_skill_frontmatter.py`、`check_wiring.py` 第 9 类；B1 | 改 |
| `skills.txt` 前缀 `ps/`（新） | `pstack/` | 同第 4.5 节 `ps/` | 新；B1 | 改（与第 4.5 节同一项，汇总只计一次） |
| `skills.txt` 前缀 `dd/`、`self/`、`engineering/`、`productivity/` | 保留 | 已在用；`dd/` 只出现在 `skills.txt` 一行，文件头注释写明它是 diagram-design | — | 保留 |
| `~/.mmw/skills/<name>/`（新） | `~/.mmw/skill-copies/<name>/` | 与 `~/.agents/skills`、`~/.claude/skills` 并存，现名说不出它是去掉了调用开关的安装副本（R18 第 4.3 节） | 新；`install.sh`；B1 | 改 |
| 角色 `self-picked-worker`（新） | `adopting-worker` | 统一到 adopt（第 4.2 节） | 新；`roles.json`、`relay.py` 取角色；B0 | 改 |
| 角色 `ticket-orchestrator`（新） | `one-ticket-orchestrator` | 夜的 orchestrator 也处理票；新名说出「只管一张票」，与 playbook **Land one ticket** 对上 | 新；`roles.json`；B0 | 改 |
| watch 的 `kind` 值 `adopt`（新） | `adopted-ticket` | 另两个值 `night`、`ticket` 是它看住的东西，`adopt` 是命令名 | 新；`relay.py`、`watchdog.py`、`turn-guard.py`；B0 | 改 |
| 角色 `worker`、`reviewer`、`advisor`、`researcher`、`night-orchestrator`；行 `junior-worker`、`senior-worker` | 保留 | 清楚；night 见第 5.4 节 | — | 保留 |
| `roles.json`、`imports.tsv`、`hosts.json`、`skills.txt`、`upstream-pstack/`、`.mmw/playbooks/`、步骤指针格式、`where` 的四种输出、导入类型名、`roles.json` 的键 | 保留 | 清楚或只有程序读、收益小（`hosts.json` 的 `defaults` 放了角色默认值，但文件在仓库内、读者只有 `models.py`） | — | 保留 |
| `~/.mmw/models.json` 及其行键 `agent`、`ALLOWED_AGENTS` | 保留 | 每台机器上一份，改键要迁移本机文件，`models.py` 第 139–143 行要求恰好四行；`agent` 键与常量名一致，词表里写明「a row's `agent` is a role」即可 | — | 保留 |
| `slots.md`、`anchors.py` | 见第 4.5、4.6 节 | — | — | — |
| `~/.mmw/bin/mmw-hook` | `~/.mmw/bin/hook-launcher` | 见第 4.6 节 | — | 改（与第 4.6 节同一项，汇总只计一次） |
| 其余状态目录与文件（`installed-root`、`state/<owner>__<name>/`、`watches.json`、`relay.json`、`beat.json`、`gap.json`、`seen.json`、`queue.*`、`watchdog.*`、`guard.log`、`leases/`、`instances/`、`prompts/`、`panels/`、工作树名） | 保留 | R19a 判含糊的几个（`beat.json` 与 `watchdog.json` 两种起名法、`gap.json`、`guard.log`）只有程序与排障的人读；改名要在没有 watch 开着时发布，并清理旧文件，收益小于代价；工作树名 `issue-<n>` 是 `tool-guard.py` 判定受管会话的依据 | — | 保留 |
| `board/` 全部文件（`gates.py`、`board-logic.mjs`、`local-config.mjs` 等） | 保留（本次升级不动） | D8 定任务板只改路径来源，新功能另开 spec；R19a 判含糊的 `board-logic.mjs`（内容是 phase 与 lamp，词表 task-board **lamp**）与 `local-config.mjs`（内容是 `models.json` 的目录）留给那份 spec | — | 保留 |
| `tests/mmw`（新） | 保留 | 套件名＝被测技能目录名，mode 名是 `mmw`（R18 D10） | 新 | 保留 |
| `tests/dispatch`、`tests/verify-ticket`、`tests/retro` 等现有套件 | 保留 | `tests/dispatch` 主要测 `dispatch.sh`，脚本名保留则套件名成立；其余与被测技能同名 | — | 保留 |
| `tests/wiring`（新） | 并入 `tests/skill-text`，名字消失 | 三道文字检查共用 `skill_text.py`，测试放一个套件，避免两个套件测同一个共用模块（R21 第 6 节） | 新 | 并入 |
| `tests/skill-text`（R21 新起） | 无 | 逐字搬运检查、结构 lint、`check_wiring.py` 共用的测试套件；按被测子系统命名，与共用模块 `skill_text.py` 同名（第 2 节「测试套件」） | 新；B0 | 新（R21 第 6 节） |
| `structure-exceptions.tsv`（R21 新起） | 无 | 结构 lint 的例外表，放在 `mmw-v2/tests/lib/`；装的是 TSV 就 `.tsv`（第 2 节「配置、状态文件」）。不用 `skeleton-exceptions.tsv`，理由同第 4.6 节 `check_component_structure.py` 一行 | 新；B0 | 新（R21 第 6 节） |
| **`## Moves`**（R21 新起） | 无 | 票上的搬运清单小节；程序按字面找的小节名，与 `## Owns` 同类，登记进 `locations.py` | 新；B0 | 新（R21 第 6 节） |
| 占位符 `<effort>`（`docs/specs/<effort>/`、`prototypes/<effort>/`）与词表 ui-acceptance **effort** | 保留 | 它是上游同一类目录的占位符：mattpocock `setup-matt-pocock-skills/issue-tracker-local.md` 第 25–28 行给 `.scratch/` 下的地图与子票目录用的正是 `.scratch/<effort>/`（`git show 5b1a4c51:skills/engineering/setup-matt-pocock-skills/issue-tracker-local.md`；同一上游的 `SKILL.md` 第 46 行与 `issue-tracker-local.md` 第 7–15 行另用 `<feature>`、`<feature-slug>`，上游自己两种都用）。它与 screen contract 的顶层键 `effort:` 同名（`write-screen-contract/references/screen-contract-format.md` 第 12 行「the effort's directory name, as in docs/specs/<effort>/」；`docs/specs/task-board/screen-contract.yaml` 第 1 行；`lint_screen_contract.py` 第 47 行键表含 `"effort"`），这个键存在消费仓库里，不能改，占位符改了就成了一个概念两个名字。`<feature>` 也已另有意思：`to-spec/SKILL.md` 第 52 行「As an <actor>, I want a <feature>」，`prototype/SKILL.md` 第 22 行 `<issue>` 在没有票时写成「a short feature name」。DECISIONS W6（第 65 行）只把「reasoning level」改成 **reasoning effort**，没有给开发 effort 另起名；词表 **effort** 条目已有 Distinct-from 句区分两者（`docs/contexts/ui-acceptance/CONTEXT.md` 第 138–140 行）。按 SSR 第 76 行末句照上游的意思用 | 若改：90 处/35 个文件＋screen contract 的键（消费仓库，要 downstream-note）＋`write-screen-contract` description（新会话生效，H2） | 保留 |

---

## 5. 程序读、写进历史的标识符：全部保留

这些名字存放在本仓库改不了的地方。改名要在读者一侧加旧名到新名的别名表（`events.py` 今天没有这种机制，本轮 `grep` 无 `alias`），而且一旦 GitHub 评论里写进了新名字，装回旧版本的已安装 checkout 会把它们列为 `unreadable` 并拒绝判断（`events.py` 第 33–36 行；推断）。这是一项难以撤销的改动。本表对它们一律保留，用词表条目、`roles.json` 的（角色，事件）登记和任务板的显示名消除误读。

### 5.1 事件名与字段值

| 现名 | R19a 的判断 | 结论与理由 |
|---|---|---|
| `spec.opened`、`spec.closed` | 误导：读作 spec issue 被打开或关闭，实际记的是一夜的开始与结束 | 保留。它们是 `spec.*` 一族五个事件里的两个（`events.py` 第 107–116 行，stage 都是 `night` 或 `land`），改就要整族改；agent 收到唤醒后按 `roles.json` 登记的步骤行事，不按名字猜；任务板已把它们显示为「Night opened / Night closed」（DECISIONS `## For the owner` 第 1 条）；词表 night 条目写明含义 |
| `worker.touched` | 误导：主语是 worker，实际是「别的票改了本票 `## Owns` 覆盖的文件」 | 保留。若改，合适的新名是 `ticket.touched`（发在被碰到的票上，主语就对了）；代价是一个事件的别名与上面的回退风险，现役 17。词表条目加一句说明方向 |
| actor 值 `judge` | 误导：`judge` 在别处指判据脚本 | 保留。前一轮已把正文里的 judge 全部改为 watchdog 或 oracle，并明确这个值留下（`verify/d.md` 第 3 部分第 7 行「Stay: the `actor` value `"judge"`」） |
| actor 值 `main`、`--actor main` | 含糊 | 保留。正文统一叫 orchestrator（前一轮 R1）；`main` 只作程序值 |
| stage 值 `dispatch` | 含糊 | 保留。`dispatch` 技能解散后，它读作普通动词「派出」，与 `worker.started`、`worker.retracted` 的含义一致 |
| `spec.retroed`、`ticket.released`、`ticket.bounced`、`ticket.checked` 及其余事件、`relay.recovered`、`watchdog:` 前缀、`MMW turn guard:` 行 | 含糊或清楚 | 保留。含糊的几个在词表各有定义与区分句（例：ui-acceptance **release** (lease) 写明「Distinct from `ticket.released`」） |
| 子票 kind `finding`、`deferred`、`decision`、`fault`、`contract` | `contract` 含糊 | 保留。kind 写在子票正文首行（`pipeline-issues.md` 第 3 行）；DECISIONS W2 已把裸词 contract 定为这个意思 |
| `NIGHT SUMMARY` 行首 | — | 保留 |

### 5.2 label、消费仓库读的键与脚本名

| 现名 | 结论与理由 |
|---|---|
| `mmw:map`、`mmw:spec`、`mmw:ticket`、`mmw:child`；`needs-triage`、`needs-info`、`ready-for-agent`、`ready-for-human`、`wontfix`；`junior-worker`、`senior-worker` | 保留。贴在各仓库已有的 issue 上；队列 label 是 mattpocock 的名字 |
| `.mmw/target.json` 及其键（`checks`、`stop`、`leaves_machine`、`instance`、`harness_markers`、`delivery` 等）与 `delivery` 的取值；screen contract 的顶层键（`effort` 等） | 保留。在消费仓库里，由 `target_config.py`、`lint_screen_contract.py` 与 agent 按字面读 |
| `<product>.release-adapter.json`、`--adapter`、出包配置里的键（如 `diagnose_core_exe_glob`） | 保留。产品仓库里的文件名与键；正文统一叫 release manifest（第 4.5 节 `key.md` 一行） |
| `exe-release` 脚本 `diagnose_core.py`、`fix_dispatch.py`、`release_contracts.py`、`verify_key.py`，以及阶段名 `verify_key` | 保留。消费仓库的出包配置用 `${RELEASE_PLUGIN_DIR}/<文件名>` 调用，消费仓库的测试按文件名或模块名加载（第 1 节逐行出处）；阶段名写在引擎生成的阶段定义与日志目录里（第 4.6 节）。正文用概念名 **diagnoser**、**fix brief**、release manifest |
| 判据脚本 `story-parity.py`、`boundary-check.py`、`journey.py`、`harness-guard.py`、`extract_skeleton.py`，以及 `verify-ticket.py`、`target_config.py` | 保留。消费仓库票的 `CHECK:` 或给消费仓库的迁移说明按名字调用；已落地的票在 `dispatch.sh reverify` 时还会原样再跑（第 1 节） |
| 工作树名 `issue-<n>`、`merge-<branch>`、`research-<n>` | 保留。名字归流水线，`tool-guard.py` 按 `issue-<n>` 判定 |

### 5.3 一词多义里保留不动的几组

R19a 第 15.1 节的 19 组里，本表改名消掉了 slot、interface、map（`pstack.map`）、summary、draft、open、route、ps；以下几组保留，理由各一句：

- **mmw**：整套工具、`.mmw/` 目录、`mmw:` label 前缀与 mode 技能同名；由 mode 的 description 与词表条目区分（R18 第 17 节 D10）。
- **effort**：开发工作与 reasoning effort 两个意思都保留。前者是 mattpocock 原文的用法（`<effort>`、`map-a-large-effort`，第 4.2、4.9 节），后者是 `models.json` 的字段；词表 ui-acceptance **effort** 的 Distinct-from 句分开两者。
- **contract**：`release_contracts.py` 的文件名被消费仓库点名（第 5.2 节）；正文按 DECISIONS W2 只把裸词 contract 用于票的 contract。
- **dispatch**：`fix_dispatch.py` 的文件名被消费仓库点名；`dispatch.sh` 与 stage 值见第 4.1、5.1 节，都读作普通动词「派出」。
- **check**：`dispatch.sh check`、`install.sh --check`、`target_config.py --check` 都是「只读检查」这一个意思；`CHECK:` 行、`ticket.checked`、`checks` 键写在历史或消费仓库里；本表只改了意思不同的 `ticket.py --check`。
- **judge**、**main**、**queue**、**release**、**gate**：程序值或词表已区分（第 5.1 节；词表 night **wake queue**；`gates.py` 与 gate-check 都是「放行或拦下」同一个意思，DECISIONS W7）。
- **claim**：MMW 的 `--claim` 与 vendored gate-check 的 `--claim` 都是「认领一块工作」（第 1 节）。
- **run / work**：`run-one-ticket` 改名后，`run-a-night` 的 run 与 `relay.py run` 都是「运行」的普通义（DECISIONS W4）。
- **change**：见第 4.2 节，一个意思。

### 5.4 night

night 出现 2775 次、现役 1123 次（R19a 第 15.1 节），是全套最核心的自造词。保留，理由：词表给了它定义，并借来一个既有概念作 leading word：「One run of a spec's published tickets under one orchestrator, from `open` to `summary`, at any hour, read the way a nightly build is」（`docs/contexts/night/CONTEXT.md` 第 255–257 行）；它出现在 `NIGHT SUMMARY`、stage 值 `night` 这些写进历史的地方；本表新起的 `open-night`、`close-night` 也用它。词表那一行里的 `open`、`summary` 随第 4.7 节改为 `open-night`、`close-night`。

---

## 6. 随改的文档

改名票里同时改这些，否则词表与技能文字对不上（SSR 第 80 行）。R21 第 3.6 节成功行要求没有搬运的文字「untouched text: … 0 changes」，所以下面每一处都要在对应的改名票里写成清单行；没写的，检查会判为改写。

- **词表条目的定义与名字：**
  - night（`docs/contexts/night/CONTEXT.md`）：**`dispatch.sh integrated`**（第 83 行）、**open**（第 141 行）、**open-ticket**（第 149 行）、**wait**（第 169 行）、**summary**（第 189 行）、**memory-list**（第 197 行）、**closing pass**（第 259 行）、**route**（第 263 行）、**night**（第 255–257 行，定义里的命令名）。
  - ticket-run：**preflight**（第 288 行，并入第 296 行 **claim**）；**child kind**（第 157 行）。
  - tickets：**sub-issue**（第 242 行）。
  - ui-acceptance：**edit pages**（第 33 行，改为 **set up and sign off**）。
  - R18 第 1.1 节计划新增的词条（mode、playbook、principle、role、slot、step pointer、where line）里，slot 一条删去（第 4.5 节），改为 **pstack names**；另加 `--run-and-record-criteria` 与 `verify-ticket.py <n>` 的区分句（第 4.8 节）。
- **词表的 `_Home_` 行**（本轮 `grep '_Home_' docs/contexts/*/CONTEXT.md`，只列指向本表要改名文件的行）：
  - `docs/contexts/ui-acceptance/CONTEXT.md`：第 11、15、19、23、35、51、59 行（`edit-pages.md`）；第 71、292 行（`interface-and-remake.md`）。
  - `docs/contexts/tickets/CONTEXT.md`：第 73 行（`several-specs.md`）；第 119、123、127、131、135、139、143、147 行（`cutting-interface-tickets.md`）；第 244 行（`sub-issues.md`）；第 322 行（`interface-and-remake.md`）。
  - `docs/contexts/ticket-run/CONTEXT.md`：第 159、164 行（`sub-issues.md`）。
  - `docs/contexts/release/CONTEXT.md`：第 15、68、76、88、110、115、119、125、129、133、137、141、145、149、158、162 行（`key.md`）；第 29、33、37、41、45、57、104 行（`driving.md`）。第 64、72、80、84 行只指向保留的脚本，不改。
  - `writing-interface-code.md` 没有 `_Home_` 行指向它。
- **根 `AGENTS.md`**：`## External References` 里「The night runbook: `check`, `open`, `advance`, the closing pass, `reverify`, `summary`, then `retro`, `finish`, `suspend`」一行随子命令改名；R18 已要求这一行改指 playbook。
- **`docs/contexts/night/how-it-works.md`**：子命令名。
- **merge-note**：本身是变化记录，引用旧文字的地方保留旧名（DECISIONS `## Leftovers` 末句）；描述现状的行随文件名改。
- **ADR**：正文是决定记录，不改；`docs/adr/README.md` 第 54 行点名 `references/edit-pages.md` 的 `## Sign-off`，随文件名改。
- **消费仓库**：`agentflow/docs/agents/issue-tracker.md` 第 52 行的 `--sub-issue`，列进 R18 第 1.1 节的 downstream-note。
- **Memory**：Nowledge Mem 里的旧记录会提到旧命令名；不改，由旧名的拒绝提示（第 3 节）与 **principle-clues-are-not-evidence** 兜住。

---

## 7. 机器可读的改名行（供 `renames.tsv`）

R21 第 3.5 节规定 spec 目录里的 `docs/specs/<effort>/renames.tsv`：列为 `kind`、`old`、`new`，可选第 4 列 `scope`（路径 glob）；`kind` 只有 `path`、`token`、`text` 三种，`token` 与 `text` 可带 `scope`。本文只列出内容，文件由写 spec 的会话建。这里只放**仓库里已有、被搬运文字会提到**的 18 个名字；R18 预定、还没建的 26 个名字不进表，spec 与票直接写新名。

```tsv
kind	old	new	scope
path	mmw-v2/skills/design-pages/references/edit-pages.md	mmw-v2/skills/design-pages/references/set-up-and-sign-off.md
path	mmw-v2/skills/exe-release/references/driving.md	mmw-v2/skills/exe-release/references/release-loop.md
path	mmw-v2/skills/exe-release/references/key.md	mmw-v2/skills/exe-release/references/release-manifest.md
path	mmw-v2/skills/verify-ticket/references/sub-issues.md	mmw-v2/skills/verify-ticket/references/child-issues.md
path	mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md	mmw-v2/skills/to-tickets/references/screen-contract-tickets.md
path	mmw-v2/upstream/skills/engineering/to-spec/references/several-specs.md	mmw-v2/skills/to-spec/references/spec-division.md
path	mmw-v2/upstream/skills/engineering/wayfinder/references/interface-and-remake.md	mmw-v2/skills/mmw/references/ui-and-remake-tickets.md
path	mmw-v2/upstream/skills/engineering/implement/references/writing-interface-code.md	mmw-v2/skills/ui-acceptance/references/writing-ui-code.md
token	edit-pages.md	set-up-and-sign-off.md
token	driving.md	release-loop.md
token	key.md	release-manifest.md	mmw-v2/skills/exe-release/**
token	sub-issues.md	child-issues.md
token	cutting-interface-tickets.md	screen-contract-tickets.md
token	several-specs.md	spec-division.md
token	interface-and-remake.md	ui-and-remake-tickets.md
token	writing-interface-code.md	writing-ui-code.md
token	--preflight	--claim
token	--draft	--closing-draft
token	--sub-issue	--open-child
text	dispatch.sh open	dispatch.sh open-night
text	dispatch.sh open-ticket	dispatch.sh open-ticket-watch
text	dispatch.sh summary	dispatch.sh close-night
text	dispatch.sh wait	dispatch.sh result
text	dispatch.sh integrated	dispatch.sh landed-since
text	dispatch.sh memory-list	dispatch.sh prepare-memory-decisions
text	dispatch.sh route	dispatch.sh resolve-child
```

`dispatch.sh` 的 7 个子命令改名写成 kind `text`（上表末 7 行）。`text` 在全部文字里只替换前后不接字母、数字、`_`、`-` 的完整片段（R21 第 3.5 节），所以 `dispatch.sh open` 不会命中 `dispatch.sh open-ticket`，旧值带着 `dispatch.sh` 前缀也碰不到普通英文里的 `open`、`route`、`wait`，`turn-guard.py` 第 25 行、`install.sh` 第 1625 行这种不带参数的写法同样被替换。

注意：

- `token	key.md` 一行的 `scope` 写 `mmw-v2/skills/exe-release/**`，只在 `exe-release` 的文字里替换；`upstream-diagram-design/scripts/verify-sankey.py` 另有一个无关的 `key.md`（本轮 `rg`），那个目录不在任何搬家票里。
- 子命令在正文里常常单写（`advance`、`open`），`text` 行只覆盖带 `dispatch.sh` 前缀的写法；单写的出现由切票会话在搬运清单里逐处写成 `replace` 指令，出处写 `R19 §4.7`（R21 第 3.5 节）。
- `verify-ticket.py <n> --preflight` 这类搬到 `ticket_state.py` 的调用，按 R18 第 7.6 节的拆分票整句 `replace`，不靠 `token	--preflight` 单独完成。
- `exe-release` 的四个脚本与它们的测试文件（`tests/exe-release/test_diagnose_core.py`、`test_fix_dispatch.py`、`test_release_contracts.py`、`test_verify_key.py`、`test_minimal_key.py`）都不改名，所以表里没有它们的 `path` 或 `token` 行。

---

## 8. 汇总

按名字计：一行里并列的几个名字分别计，同一名字在两节出现只计一次，第 5 节的标识符全部保留、不逐个计数；R21 第 6 节新起的名字（第 4.6、4.9 节结论为「新」的行）不是改名也不是保留，不计数。

| 类别 | 改（仓库已有） | 改（R18 预定） | 保留 | 用户定 | 并入后消失 |
|---|---|---|---|---|---|
| 技能名（4.1） | 0 | 1 | 13 | 0 | 0（`dispatch` 解散另计） |
| playbook 与步骤（4.2） | 0 | 6 | 25 | 0 | 0 |
| 原则（4.3） | 0 | 4 | 8 | 0 | 0 |
| mode 节名与骨架（4.4） | 0 | 0 | 13 | 0 | 4 |
| reference（4.5） | 8 | 5 | 36 | 0 | 5 |
| 脚本文件（4.6） | 0 | 4 | 50 | 0 | 0 |
| 子命令与开关（4.7、4.8） | 10 | 1 | 50 | 0 | 0 |
| 配置、角色、状态、任务板、测试套件、占位符（4.9） | 0 | 5 | 66 | 0 | 1 |
| **合计** | **18** | **26** | **261** | **0** | **10** |

- **仓库已有、要改的 18 个**：8 个 reference（`edit-pages.md`、`driving.md`、`key.md`、`sub-issues.md`、`cutting-interface-tickets.md`、`several-specs.md`、`interface-and-remake.md`、`writing-interface-code.md`）；7 个 `dispatch.sh` 子命令（`open`、`open-ticket`、`summary`、`wait`、`integrated`、`memory-list`、`route`）；3 个开关（`--preflight`、`--draft`、`--sub-issue`）。第 7 节把它们写成 `renames.tsv` 的行，子命令 7 行的 kind 是 `text`。
- **R18 预定、要换写法的 26 个**：`memory-records`；4 份 playbook 与 2 处步骤名；4 条原则；5 个 mode reference（含 `ps/`）；4 个 mode 脚本或导入文件；开关 `--run-and-record-criteria`；`+model-invoked`、`~/.mmw/skill-copies/`、两个角色名、一个 watch `kind` 值。
- **mode 技能名**：保留 `mmw`，`tests/mmw` 随它（R18 第 17 节 D10，由 Claude 代定，待你复核；见「用户过目」）。
- **已按规矩定、记录在此供你查看的工程决定**：SSR 第 76 行的改写（第 3 节）；全部事件名保留（第 5 节；若你想改 `worker.touched` 或 `spec.opened`、`spec.closed`，代价与回退风险写在第 5.1 节）；`exe-release` 四个脚本保留（第 4.6 节）；子命令改名在 `renames.tsv` 里用 kind `text`（第 7 节，R21 第 3.5 节）。

---

## 9. 本轮读了什么、没读什么

- **读全文或相关段落的**：R19a 全文（任务正文给出）与第 176、174、178、180、195 行、第 15.3 节；R18 第 0 节、第 1 节全文、第 3.1–3.3 节（P1、P5–P16 与私有 playbook）、第 4.1 节、第 5.2 节、第 16–17 节与审查记录，以及第 498、535、564、657、660、719 行；SSR `### Vocabulary` 全文（第 72–82 行）；`writing-for-agents/SKILL.md` `## Leading words`；`SKILL-MECHANICS.md` 第 9–10 行；R20a、R20b、R21a 中关于命名与改名表接口的段落（R21a 第 3.4 节表、第 3.5 节全文、第 3.6 节成功行）；`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` 全文、`APPLY-BRIEF.md`、`BRIEF.md`、`VERIFY-BRIEF.md` 开头、`verify/d.md` 中含 judge、interface、effort 的行；`docs/reviews/2026-09-28-lightweight/vocabulary.md` 的 R、S 两张改名表；词表 night 的 `### The night's commands`、`### The night`、branch 条目与 **check**、**advance**、**land**、**adopt**、**watch**、**open-ticket** 条目，ticket-run 的 **child kind**、**preflight**、**claim**，tickets 的 **sub-issue**，ui-acceptance 的 **effort**、**product answers**、`### The lease`、**skeleton**，toolbox 的 **`effort`**，release 的条目名单；各 `CONTEXT.md` 的全部 `_Home_` 行（`grep`）；`events.py` 第 1–70、100–180、890–900 行；`dispatch.sh` 第 368–395 行 usage 与第 4495 行；`dispatch/references/` 四份、`design-pages` 的 `edit-pages.md`（节标题）、`draw.md`，`exe-release` 的 `key.md`、`driving.md`，`ui-acceptance` 的三份 reference、`verify-ticket` 的两份 reference、三份 interface 命名的 reference 的开头；`exe-release` 的 `release-flow.sh` 第 245–260、388–389 行、`release_contracts.py` 第 65–95 行，`manage-agents-md`、`write-screen-contract` 几个脚本的文件头；`board/gates.py`、`board-logic.mjs`、`local-config.mjs` 开头；`hosts.json` 前几行；`downstream-notes/README.md`、`449-skill-renamed-ui-acceptance.md`、`492-skeleton-by-data-ui-id.md` 开头；`docs/adr/README.md` 第 23、25、54 行；pstack 23 份 playbook 的首行、mode `## Playbooks` 一节（第 121–143 行）、`setup-pstack/SKILL.md` 开头；上游原文（squash `5b1a4c51`）`to-tickets/SKILL.md` 第 143–147 行、`setup-matt-pocock-skills/SKILL.md` 与 `issue-tracker-local.md` 里含 `.scratch` 的行、`wayfinder/agents/openai.yaml`、`wayfinder/SKILL.md` 与 `ask-matt/SKILL.md` 里含 effort 的行；squash 之后 MMW 在 `mmw-v2/upstream/` 里新增的文件清单（`git diff --diff-filter=A`）；消费仓库 `agentflow`、`xiaohuangya` 的出包配置里点名技能脚本的行、`agentflow/tests/support/release_contracts_plugin.py` 里的文件名查找、`agentflow/tests/contracts/test_release_key_verification_wire.py` 与 `release_event_sink.py` 里点名技能脚本的行。
- **本轮自己跑的计数**：新名字的现有用法（第 1 节）；第 4.5 节标「本轮」的 reference 次数；`<effort>` 的 90 处、35 个文件；exe-release 与 `dispatch.sh` 改名项在脚本里的字面出现（`rg --type py --type sh`）；两个消费仓库里本表要改的名字（只命中 `agentflow/docs/agents/issue-tracker.md` 第 52 行）。其余次数取自 R19a，没有重数。
- **没有读全文的**：多数被改名文件只读了开头，理由列据此与 R19a、词表写成；`dispatch.sh open` 在 `relay.py`、`watchdog.py` 的出现只按 `rg` 命中文件判断为提示句（推断），改名票要逐处核对；消费仓库只查了 `agentflow`、`xiaohuangya` 两个（本机带 `.mmw/` 的只有 `agentflow` 与本仓库），其他用 `exe-release` 出包的仓库若存在，没有查；`edit-pages.md` 全文没有读，第 4.5 节「ADR README 的记错已更正」是推断；`wiring` 作为依赖注入用语的出处没有查原始文献（第 4.6 节标了推断）。

---

## 审查记录

本轮逐条核实了 12 条审查意见，全部属实（第 1 条比意见说的范围更大），都已按下述方式改入正文。

1. **exe-release 四个脚本改名（blocking）**：属实。核实了意见列出的全部配置行，另查到 `agentflow/tests/contracts/test_release_key_verification_wire.py` 第 63 行按模块名加载 `verify_key`，`verify_key` 还是引擎保留阶段名。所以意见 (a) 说的「`verify_key.py` 只被文档点名，可以单独改」不成立，四个脚本全部保留。改动：第 4.6 节四行改为保留；第 5.2 节新增一行；第 3 节 SSR 改写稿的 never-renamed 清单加入「a script or module a consuming repository's configuration or tests name」；第 2 节脚本行与末行补上这一类；第 0 节第 3、4、7 条与第 5.3 节更正；第 7 节删去 4 行 `path`、8 行 `token`。
2. **`<effort>`→`<feature>`（major）**：属实。screen contract 键 `effort`、`lint_screen_contract.py` 第 47 行、`to-spec` 第 52 行、`prototype` 第 22 行、上游 `issue-tracker-local.md` 第 25–28 行、DECISIONS 第 65 行、词表第 138–140 行均已核对。另发现原文引的上游 `setup-matt-pocock-skills/SKILL.md` 行号应为第 46 行，不是第 48 行。改动：第 4.9 节改为保留；第 7 节删去 `token <effort> <feature>`；第 0、5.3 节更正。
3. **`renames.tsv` 的 `replace` 行（major）**：属实。R21a 第 104 行与第 3.5 节 kind 表已核对，`turn-guard.py` 第 25 行、`install.sh` 第 1625 行是不带参数的写法。改动：第 7 节选择让 R21a 加 kind `command`，写明匹配规则与不选另一方案的理由；这 7 行单列，不放进 `renames.tsv`。
4. **`open-ticket` 保留与 `open` 改名标准不一（major）**：属实。R19a 第 174、176、178、180、195 行已核对。改动：`open-ticket` 改为 `open-ticket-watch`（没有采用 `watch-night`/`watch-ticket`，理由写在第 4.7 节该行）；`finish`、`check`、`advance`、`adopt` 各给出「R19a 判含糊、仍保留」的理由；统计里的子命令改名从 6 个变为 7 个。
5. **`verify_key` 的替换范围与测试文件（major）**：属实。`ENGINE_STAGE_NAMES`、`release-flow.sh` 第 388–389、879 行、`key.md` 第 49 行、五个测试文件均已核对。第 1 条的结论是四个脚本都保留，这一条随之不需要补 `path` 行；第 4.6 节 `verify_key.py` 行写明了阶段名，第 7 节注意事项写明测试文件不改。
6. **`--child`、`--claim` 已被占用（minor）**：属实。计数与意见一致：`--claim` 29 处/9 个文件，全在 `mmw-v2/upstream-unlazy/`；`--child` 3 处/2 个文件。改动：开关改为 `--open-child`；第 1 节换成实际计数，并写明 `--claim` 判为可接受的理由；第 5.3 节加 **claim**。
7. **`evidence-page.md` 为写法改名（minor）**：属实。本轮计数 22 处/10 个文件。改动：第 4.5 节改为保留，写明大小写改名在 macOS 上的两项代价；第 7 节删去对应的 `path` 与 `token` 行；第 2 节 reference 行删去这个实例，把「全大写」限定为新文件。
8. **`map-a-large-effort` 出自上游原句（minor）**：属实。`openai.yaml` 第 3 行与 wayfinder、`ask-matt` 的用法已核对。改动：采用 (a)，改为保留，并写明上游来源。
9. **子命令句式规矩与新名不符（minor）**：属实。改动：第 2 节规矩改为「做事的用动词（加宾语），只读查询的用它打印的东西命名，子命令不与开关同名」；`result`、`landed-since` 按只读查询保留为名词；`memory-list` 的新名改为 `prepare-memory-decisions`。没有采用意见给的 `draft-memory-decisions`，因为 draft 已指 closing-comment draft 与票草稿。
10. **`--run-criteria` 没说出「记录」（minor）**：属实。R18 第 657、660、719 行已核对。改动：开关改为 `--run-and-record-criteria`；第 4.8、6 节写明词表里与 `verify-ticket.py <n>` 的区分句；第 4.6 节 `ticket.py` 行补一句。
11. **playbook 句式错引 pstack（minor）**：属实。pstack 路由表与 23 份首行已核对。改动：第 2 节 playbook 行的理由改为「MMW 自写用祈使句式，导入的 pstack playbook 保留原名，两者并存不影响匹配」，删去「与 pstack 一致」的说法；第 4.2 节开头列出 R18 里点名旧 playbook 名的全部行号（本轮 `grep`），其中包括第 498、535、564 行。
12. **第 6 节清单不全与三处出处不准（minor）**：属实。改动：第 6 节逐文件列出全部受影响的 `_Home_` 行，并写明它们要在改名票里写成清单行；`review-axes` 一行的引用处改为本轮 `grep` 的实际结果（不含 `dispatch.sh`）；`edit-pages.md` 一行改为「第 54 行点名，第 23、25 行经表下注指向第 54 行」；reference 次数按本轮重数改写并标「本轮」。
13. **定稿对齐（不是审查意见）**：按 R21 第 7 节第 2、3、4、7 行改入。第 7 节：子命令 7 行并入 `renames.tsv` 主块，kind 用 R21 的 `text`，删去本表原先提议的 kind `command`；`key.md` 的 `token` 行加第 4 列 `scope`；`kind` 的说明改为 R21 的三种。第 4.6、4.9 节补 R21 第 6 节的新名字，`tests/wiring` 并入 `tests/skill-text`。指 R21a 某节的引用改指 R21 同一节（第 9 节与本记录第 3 条记的是当时读 R21a 的情形，不改）。mode 技能名按 R18 第 17 节 D10 定为 `mmw`：「需要用户拍板」一节改为「用户过目」，第 0、2、3、4.1、4.3、4.6、4.9、5.3、7、8 节随之改。
