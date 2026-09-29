# R9 MMW 归置：standalone and tooling skills

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4，引用写成「R4 D2.2」「R4 §15」）逐项归置五个技能：`exe-release`、`code-checkers`、`manage-agents-md`、`diagram-design`、`writing-for-agents`（含 `SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md`、`SKILL-MECHANICS.md`）。准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）第 C 节。`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` 下称 SSR，`REVIEWING-A-SKILL-SET.md` 下称 RSS。

标注：「已核实」＝本轮回到原文或跑只读命令看到的；「推断」＝由原文推出；做不出判断的放第 8 节。本文不改任何仓库文件。

---

## 0. 结论

1. **五个技能都是能力技能，归置结果几乎全是「不动」。** 它们各自产出一个可命名的交付物（安装包；一套检查器与一个 checker command；固定格式的 `AGENTS.md`；一张图；一份写给 agent 的文档），入口是自己的 description 或别的能力技能按名调用，没有一段是「交付物之后按任务类型做什么」的顺序（本轮 grep 核实，第 1 节 R9-V8）。本单元不产生 playbook，不产生原则。
2. **真正要改的只有三处，都由新架构引起：**
   - **SSR 与 RSS 改写**（第 1.5 节，要点逐条列出）。SSR 由「MMW ships no router skill」改为「路由只有一个家，是 `mmw` 的 `## Routes`」，并收下新组件（mode、playbook、角色操作文件、原则）的写法、a–f 分类、分叉规则、调用开关推导规则、外来技能进门检查。净增约 40 行，全部放在 SSR 现有文件里，不新建文件。
   - **`manage-agents-md` 加一句**：`## External References` 里「File 列是一个技能名、由那个技能自己加的指针行」保留，不当成 `### What NOT to Add` 第 9 条「Installed skills and plugins」删掉。否则 R4 D1.4 在消费仓库 `AGENTS.md` 加的那一行，会在下一次 rewrite 时被删（已核实两处文字冲突，第 1 节 R9-V3）。
   - **`exe-release` 不进 `mmw` 的 `## Routes`。** 这与 R4 D2.2 的路由草案不同：那一行没有独有门槛，只是把 `exe-release` description 的触发再写一遍，而 R4 自己排除 `research`、`diagram-design` 等的理由正是「同一个触发写两处」。我改为在 SSR `### Descriptions` 加一条规则来管住这类行（第 1.5 节 W-SSR-9），并建议 `mmw` 的 `## Routes` 用一句兜底行接住「某个技能的 description 已经认领的任务」（交给 mode 单元落实）。
3. **R4 U4（接入新仓库时谁写 `AGENTS.md` 那一行）从本单元看是工程决定，我定为：`manage-agents-md` 不写这一行，只保留它。** 写入由 `mmw` 的 `## Where you are` (c) 行与 `dispatch.sh check` 的缺行警告负责（R4 D1.4 的倾向）。理由：`manage-agents-md` 被不接 MMW 的仓库使用（2026-09-28 复审记录的唯一一次真实加载在 `~/ERP`，N7 §6，未核实），让它写 MMW 专有的行就是把 MMW 流程写进一个通用能力。
4. **a–f 分类（R4 D5.3）对本单元的两个上游技能都得出「没有要移走的句子」**：`diagram-design` 的 MMW 改动全是 a 类或 e 类；`writing-for-agents` 的两处改动是 b 类触发句（本能力自己的触发）和 d 类连接句（指向旁加的 SSR）。没有 c 类（点名下一步）、没有 f 类（行数过半）。
5. **顺路核实到的六个现有缺陷**，都不是架构问题，按 R4 §15 的做法另开普通票（第 5 节 F1–F6）。其中一条是 owner 的范围决定（第 7 节）：agentflow 与 xiaohuangya 的 release manifest 仍带着已删的四个字段，下一次出包会被拒（推断）。

---

## 0.1 读了什么、核实了什么

完整读过：L7 第 0 节、A.3–A.5、C 节全文；R4 全文（任务附带）；N7 全文；N5 第 0、2.8、2.9 节与涉及本单元的第 3–9 节段落；`writing-for-agents` 的 `SKILL.md`、`SKILL-MECHANICS.md`、SSR、RSS、`agents/openai.yaml`；`mmw-v2/merge-notes/writing-for-agents.md`、`mmw-v2/merge-notes/diagram-design.md`、`mmw-v2/merge-notes/README.md` 第 18–40 行；`exe-release/SKILL.md`、`references/driving.md`，`release-flow.sh` 的 `cmd_init`；`code-checkers/SKILL.md`；`manage-agents-md/SKILL.md` 第 1–40、124–330 行、`references/rewrite.md`、`scripts/check.sh` 的路径检查段；`diagram-design/SKILL.md` 第 1–40 行；`mmw-v2/tests/lib/check_own_skill_frontmatter.py`、`check_upstream_em_dashes.py` 的文件头；`mmw-v2/downstream-notes/release-self-heal-removed.md` 前半。

只读标题或按需检索：`exe-release/references/new-product.md`、`key.md`，`code-checkers/references/*.md`，`manage-agents-md` 第 40–124 行，`diagram-design` 第 40 行以后与 56 份 reference，`docs/contexts/toolbox/CONTEXT.md` 第 225–245 行。依赖这些未读部分的结论都标了推断。

本轮核实（R9-V 编号在后文引用）：

| # | 事实 | 出处与方法 | 结果 |
|---|---|---|---|
| R9-V1 | 指向 SSR 的运行时入口只有三处：根 `AGENTS.md` `## External References` 第 49 行（本仓库）；`writing-for-agents/SKILL.md` 第 8 行（任何仓库）；`retro/SKILL.md` 第 145 行让 retro 先读 `writing-for-agents` 的 `SKILL.md`，再经第 8 行到 SSR。其余命中是 merge-note、词表 `_Home_`、两个 lint 的文件头 | `grep -rln 'SKILL-SET-RULES'`（排除 `archive/`、`deprecated/`、`docs/research`、`docs/reviews`） | 已核实 |
| R9-V2 | `writing-for-agents` 相对上游 squash `5b1a4c51` 只改了 `SKILL.md` 两行（description、第 8 行），另加 SSR（176 行）与 RSS（33 行）；`SKILL-MECHANICS.md`、`agents/openai.yaml` 逐字节相同 | `git diff --stat 5b1a4c51:skills/productivity/writing-for-agents HEAD:mmw-v2/upstream/skills/productivity/writing-for-agents` | 已核实 |
| R9-V3 | `manage-agents-md/SKILL.md` 第 150 行：「Other skills add rows under `## Commands`, `## External References` and `## Key Conventions` by those headings」；第 138 行 `### What NOT to Add` 第 9 条「Installed skills and plugins — a list of what is installed」；根模板 External References 的 File 列写「`<repository-relative path, from entries of type reference>`」；`references/rewrite.md` `## Migrate` 第 5 步把命中 `### What NOT to Add` 的旧行记为 `removed: <reason>`。R4 D1.4 那一行的 File 列是「the `mmw` skill」，不是路径 | 原文 | 已核实。`check.sh` 第 92–104 行只检查含斜杠的反引号词，裸名 `mmw` 不会被判为缺失路径，所以冲突只在文字规则，不在脚本 |
| R9-V4 | `exe-release/SKILL.md` 第 16 行说「`bash scripts/release-flow.sh init` refuses to start on a dirty tree」，而 `cmd_init`（`release-flow.sh` 第 401–445 行）只校验 manifest、拒绝第二个 loop、清 artifacts、写状态，没有工作树检查；全脚本唯一的 `git diff --quiet HEAD` 在 P2 预检（第 282–283 行） | 读 `cmd_init` 全文 | 已核实（N7 §9 缺陷 1 成立） |
| R9-V5 | `diagram-design/SKILL.md` 现为 41,198 字节，上游 `8a85636a` 为 39,085 字节；上游 `docs/adr/0004-skill-md-byte-cap-and-trigger-rich-description.md` 第 14 行定上限 40,000 字节，由上游 `scripts/verify-semantic-motion.py` 执行 | `wc -c`；`git show 8a85636a:… \| wc -c`；读 ADR 0004 | 已核实。N7 §5.1 引的「40,404」（N11 thin_claims）不准，实测 41,198。本仓没有跑 `verify-semantic-motion.py`，它会不会因此失败是推断 |
| R9-V6 | 「先嵌套」改动漏了三处仍写拆图：`references/output-spec.md` 第 137、219 行，`SKILL.md` 第 556 行 | `grep` | 已核实（N7 §9 缺陷 4 成立） |
| R9-V7 | `diagram-design` 的 frontmatter 没有 `disable-model-invocation`（上游默认模型可触发，与 `merge-notes/README.md` 第 22 行一致）；调用它的是两个能力技能：`wait-what` 的 `VISUAL.md`（「Read the `diagram-design` skill's `SKILL.md`」）与 `improve-codebase-architecture/SKILL.md` 第 41 行 | 原文 | 已核实 |
| R9-V8 | 本单元四个技能里出现 MMW 流水线名词的只有两处：`code-checkers` 第 6 步（`.mmw/target.json` 的 `checks`、`MMW_BASE_REF`）与 `manage-agents-md` `### Code and test rules`（reviewer 的 Standards、Tests 轴，worker 经 spec 和 ticket 拿规则）；`diagram-design/SKILL.md` 零处 | `grep -i 'ticket\|night\|spec\|mmw\|worker\|orchestrator'` | 已核实 |
| R9-V9 | 「代码规则归 `CODING_STANDARDS.md`、测试规则归 `TESTING.md`」这条放置规则只在 `manage-agents-md`（`SKILL.md` 第 155、208 行，`rewrite.md` 第 23 行按名回指）；`to-spec`、`to-tickets`、`standards-reviewer.md`、SSR 只是使用这两个文件，没有复述放置规则 | `grep -rn CODING_STANDARDS mmw-v2/skills mmw-v2/upstream/skills` | 已核实。N7 §4 记的「至少部分真重复，需逐句再核」结论为：不是重复 |
| R9-V10 | `~/agentflow`（`dev`）的 `hedgehog`、`parrot` 与 `~/xiaohuangya`（当前分支 `2026-09-07-agent-setup-alignment`）的 `duck` release manifest 各仍带 `fix_executor`、`editable_paths`、`protection_source`、`post_fix_gate` 四个字段；`release_contracts.py` 以 `extra="forbid"` 拒绝多余字段（downstream-note 原文） | `grep -c` 四个字段名 | 已核实字段仍在；「下次出包会被拒」是推断，未运行 |
| R9-V11 | 没有任何已安装技能按名调用 `exe-release`；唯一命中是未安装、将恢复上游原文的 `ask-matt/SKILL.md` 第 92 行 | `grep -rn exe-release mmw-v2/skills mmw-v2/upstream/skills` | 已核实 |
| R9-V12 | `playbook` 一词在 `mmw-v2/skills`、`mmw-v2/upstream/skills` 零命中，只出现在 `diagram-design` 的 loop 图例子内容里（`references/type-loop.md` 与四份 `assets/example-loop*.html`）；`mode` 已有 `wayfinder` 的「Two modes」（上游含义）与词表 `permission mode` | `grep -rli playbook`；`grep -w mode` | 已核实。R4 §9「grep 为 0」对技能文本成立 |
| R9-V13 | `check_own_skill_frontmatter.py` 只解析 `skills.txt` 各项的 `SKILL.md`，本仓自有技能只许有 `name`、`description` 两个键 | 文件头 | 已核实。所以 `mmw`（自有技能）不可能带 `disable-model-invocation`；`playbooks/`、`principles/` 下没有 frontmatter 的文件不受影响 |

对清点报告的更正：N7 §4「`CODING_STANDARDS.md` 归属规则至少部分真重复」→ 不是重复（R9-V9）；N7 §5.1 字节数 → 41,198（R9-V5）。

---

## 1. 归置表

动作取值：不动 / 移动 / 拆分 / 合并 / 回到上游原文 / 删除 / 新建 / 改写。收益只写用户要求 2 的六种之一，缩写如下：**重复**＝去掉一处经 grep 核实的真重复；**安家**＝给无处安放的内容一个家；**上游原文**＝把 MMW 流程移出上游文本；**复用**＝被两个以上调用方复用；**外来**＝以后加外来技能时不必改现有文字；**断点**＝消除一处已核实的断点或冲突。「不动」行的理由集中在第 5 节，表里只写编号。

### 1.1 `exe-release`（自有，`self/exe-release`）

| # | 部件（现在位置） | 新位置 · 层 | 动作与具体小节 | 收益（证据） | 体量 | 被取代的旧规则 · 原意 |
|---|---|---|---|---|---|---|
| E1 | `SKILL.md` frontmatter description | 原位 · 能力技能的触发 | 不动 | 第 5 节 #1 | 0 | — |
| E2 | `SKILL.md` 开头两段（第 8、10 行：完成线、「Ship what is on the current branch now」） | 原位 · 能力技能正文 | 不动 | #2 | 0 | — |
| E3 | `SKILL.md` `## 1. Preconditions` | 原位 | 不动（位置）；第 16 行末句与脚本不符，另开普通票（第 5 节 F1） | 票的收益：**断点**（R9-V4） | 票：0 或 −1 行 | — |
| E4 | `SKILL.md` `## 2. Name the products for this run` | 原位 | 不动 | #2、#3 | 0 | — |
| E5 | `SKILL.md` `## 3.`、`## 4.`、`## 5.` | 原位 | 不动 | #2（L7 C.3：一条链服务一个交付物） | 0 | — |
| E6 | `references/driving.md`（四节：`## State table: do what where says`、`## Pause: missing context`、`## Close`、`## An interrupted build`） | 原位 · 能力技能 reference | 不动 | #4 | 0 | — |
| E7 | `references/new-product.md` | 原位 · reference（新产品分支） | 不动；第 35–36 行代码例里的中文注释另开票（F4） | — | 0 | — |
| E8 | `references/key.md` | 原位 · reference（写 manifest 分支） | 不动；缺 `build_machine`、`diagnose`、`diagnose_branches`、`diagnose_core_exe_glob` 四个字段另开票（F3） | — | 0 | — |
| E9 | 脚本组：`release-flow.sh`；`release_contracts.py`；`verify_key.py`；`release_script_assembler.py` + `builders/nuitka.py` + `release_templates/nuitka_electron.ps1.tmpl`；`diagnose_core.py`；`fix_dispatch.py` | 原位 · 脚本 | 不动；`release-flow.sh` 第 133–135、1160–1162 行两处注释与代码不符，另开票（F2） | — | 0 | — |
| E10 | `mmw-v2/tests/exe-release/`（11 个测试文件与 PowerShell 检查） | 原位 · 测试 | 不动 | #5 | 0 | — |
| E11 | `docs/contexts/release/CONTEXT.md`（168 行） | 原位 · 仓库文档（词表） | 不动；`diagnoser` 条目 `_Home_` 指向不含该字段的 `key.md`，随 F3 一起修 | — | 0 | — |
| E12 | `mmw-v2/downstream-notes/release-self-heal-removed.md` | 原位 · 仓库文档 | 不动 | #5 | 0 | — |
| E13 | R4 D2.2 草案中 `mmw` `## Routes` 的「出安装包 → `exe-release`」行 | 不建这一行 | 删除（从草案中） | **重复**：该行的情境「出安装包」与 `exe-release` description「Use when the user asks to ship, to package, or to build an installer」是同一个触发，行里没有独有门槛（R4 D2.2 表该行门槛列为「—」）；R4 D2.2 排除 `research`、`diagram-design` 等的理由正是「列进来就是同一个触发写两处」 | `mmw` −1 行 | 取代：R4 D2.2 草案的这一行。原意（人说「出包」时去对地方）由 `exe-release` description 保住；mode 单元另加一句兜底行（第 8 节 U-R9-1） |

### 1.2 `code-checkers`（自有，`self/code-checkers`）

| # | 部件 | 新位置 · 层 | 动作 | 收益 | 体量 | 旧规则 · 原意 |
|---|---|---|---|---|---|---|
| C1 | description | 原位 · 触发 | 不动 | #1 | 0 | — |
| C2 | 开头一段、`## The rule that decides where a tool goes`、`## What to install`（含 Settled choices）、`## Pin the formatter exactly, the checkers loosely` | 原位 · 能力技能正文 | 不动 | #2、#6 | 0 | — |
| C3 | `## Steps` 第 1–3 步 | 原位 | 不动 | #2 | 0 | — |
| C4 | 第 4 步（首跑分拣四级、checker baseline、只看改动行、反向探针）与第 5 步（三种静默失效与逐目录探针） | 原位 | 不动；不加对原则 `silence-is-never-a-pass` 的括注 | 第 3.2 节 | 0 | — |
| C5 | 第 6 步（一个 checker command；在有 `.mmw/target.json` 的仓库里它就是 `checks`；`MMW_BASE_REF`） | 原位 | 不动 | #7 | 0 | — |
| C6 | 第 7 步 → `references/git-hooks.md` | 原位 | 不动 | #4 | 0 | — |
| C7 | 第 8 步（写进 `AGENTS.md` 的 `## Commands` 与 `## Key Conventions`，照 `manage-agents-md` 的格式） | 原位 | 不动 | #8 | 0 | — |
| C8 | 末尾总 `Done when` | 原位 | 不动 | #2 | 0 | — |
| C9 | `references/python.md`、`references/typescript.md` | 原位 · reference（语言分支） | 不动 | #4 | 0 | — |
| C10 | `references/git-hooks.md`（每次都读） | 原位 · reference | 不动 | #4 | 0 | — |

### 1.3 `manage-agents-md`（自有，`self/manage-agents-md`）

| # | 部件 | 新位置 · 层 | 动作 | 收益 | 体量 | 旧规则 · 原意 |
|---|---|---|---|---|---|---|
| M1 | description | 原位 · 触发 | 不动 | #1 | 0 | — |
| M2 | 开头两段（「An `AGENTS.md` is loaded into every session …」） | 原位 | 不动 | #2 | 0 | — |
| M3 | `## Find your situation` | 原位 | 不动 | #2 | 0 | — |
| M4 | `## Survey`（`### Groups`、`### Dispatch`、提示模板、`### Collect`） | 原位 | 不动（提示模板不移进 reference） | #9 | 0 | — |
| M5 | `## Ask the user`（`### Format`、两组问题、`### Nested purpose, one table`、`### Record`） | 原位 | 不动 | #2 | 0 | — |
| M6 | `## Write` `### What NOT to Add` 第 9 条「Installed skills and plugins」 | 原位 | **改写：加一句**，大意「A row that another skill adds so that sessions here load it (its Need is the situation, its File names the skill) is a pointer, not a list of installed skills: it stays under `## External References`.」不点名 `mmw` | **断点**：R4 D1.4 的行（File 列是技能名）与第 9 条、根模板 File 列「repository-relative path」、`rewrite.md` `## Migrate` 第 5 步三处冲突（R9-V3）；不改，则消费仓库下一次 rewrite 会删掉这一行，`mmw` 退回只靠 description 加载 | +1 行 | 不取代任何规则：第 9 条原意（不列技能清单，因为 description 已在运行时）保住，因为一行指针不是清单 |
| M7 | 根模板 `## External References` 占位的 File 列 | 原位 | **改写半句**：「`<repository-relative path, …>`」后加「or the skill a pointer row loads」 | 同 M6（**断点**） | +0 行（同一行加字） | 同上 |
| M8 | `### What NOT to Add` 其余 11 条、`### Language`、`### Steps`、根模板其余部分、`### Code and test rules`、`### Nested template`、`` ### `<important if>` blocks ``、`### Writing rules`、`### Pointers` | 原位 | 不动 | #2、#10 | 0 | — |
| M9 | `## Prune`、`## Verify and report` | 原位 | 不动 | #2 | 0 | — |
| M10 | `references/create.md`、`references/rewrite.md` | 原位 · reference（两个情形） | 不动（M6 的那一句已经覆盖 `## Migrate` 第 5 步，`rewrite.md` 不必另写） | #4 | 0 | — |
| M11 | `scripts/check.sh` | 原位 · 脚本 | 不动（裸名不查，R9-V3） | #5 | 0 | — |
| M12 | `mmw-v2/tests/manage-agents-md/test_check.sh` | 原位 · 测试 | 不动 | #5 | 0 | — |
| M13 | R4 U4「接入新仓库时写 `AGENTS.md` 那一行的一步归哪个技能」 | 不归 `manage-agents-md` | 决定（工程）：写入由 `mmw` `## Where you are` (c) 与 `dispatch.sh check` 警告负责；`manage-agents-md` 只保留（M6） | **上游原文**（不改上游 `setup-matt-pocock-skills` 第 4 步）；不把 MMW 专有步骤写进一个非 MMW 仓库也用的通用能力 | 0 | 原意（每个接 MMW 的仓库都有这一行）由 R4 D1.4 的三处保证保住 |

### 1.4 `diagram-design`（上游 `cathrynlavery/diagram-design`，subtree `mmw-v2/upstream-diagram-design/`）

每一处本仓改动按 R4 D5.3 归类（改动清单取自 `mmw-v2/merge-notes/diagram-design.md` `### SKILL.md` 表，与 N7 §5.1 的 diff 核对一致）。

| # | 部件 | 新位置 · 层 | a–f 类 | 动作 | 收益 | 体量 | 旧规则 · 原意 |
|---|---|---|---|---|---|---|---|
| D1 | frontmatter（description、`license`、`metadata`） | 原位 · 上游能力技能 | 未改；b 类推导：被 `wait-what`、`improve-codebase-architecture` 按名调用 → 两个开关都不在，与上游现状相同 | 不动 | #11 | 0 | — |
| D2 | §0 标题、粗体首句、「Name the one you used beside the deliverable」 | 原位 | e（行为：gate 改为「定下配色并在交付物旁写明」） | 不动（保留本仓改动，merge-note 有行） | #12 | 0 | — |
| D3 | §0「For a markerless project …」（不停下问品牌，用默认配色画） | 原位 | e（改变默认行为；用户直接斜杠进入时也要生效，所以不能搬到调用方） | 不动 | #12 | 0 | — |
| D4 | §0「When the artifact is going to a client …」与「Keep the result out of the installed `style-guide.md` …」 | 原位 | e（防错：品牌串到本机所有仓库；句中无 MMW 名词） | 不动 | #12 | 0 | — |
| D5 | §0 末段半句「all-default tokens … take the default path above」 | 原位 | e（随 D3） | 不动 | #12 | 0 | — |
| D6 | §1 末句、§3 Rules of thumb 第三条、§7 复杂度预算末两段、§6 rule 3 括号「see §7」、`references/output-spec.md` §3 条件 3 与 Degrade ladder 第 6 步（「先嵌套、按层计、独立问题才拆」） | 原位 | e（改变超预算时的动作；merge-note `## 总原则` 的用户立场） | 不动；R9-V6 的三处漏改另开票（F5） | 票：**断点**（同一技能内两种相反指令） | 票：≈0（改三句） | — |
| D7 | §6「When one page carries several diagrams, prefix each marker `id` …」 | 原位 | e（能力修正：一页多图时 `id` 重复、HTML 不合法；句中无 MMW 名词） | 不动 | **复用**：`wait-what` 与 `improve-codebase-architecture` 两个调用方都靠它；搬到调用方就要写两遍 | 0 | — |
| D8 | §6 rule 6、§9 两条检查：`repo-root/` 路径、从技能目录运行 | 原位 | a（安装后可运行；按技能自身目录写路径） | 不动 | #12 | 0 | — |
| D9 | §9 新增「Opened the rendered file and looked at every diagram in it?」 | 原位 | e（防错：只读源码的检查看不到裁切与交叉） | 不动 | #12 | 0 | — |
| D10 | §2、§3 选型表、§4、§5、§8、§10、§11、§12 | 原位 | 未改（上游原文） | 不动 | #11 | 0 | — |
| D11 | 56 份 `references/`（55 份原样，`output-spec.md` 两处见 D6） | 原位 · reference | 未改 | 不动 | #11 | 0 | — |
| D12 | `assets/`、技能内 `scripts/`（`self_check.py`、三个 `*_extract.py`） | 原位 · 脚本与模板 | 未改 | 不动 | #11 | 0 | — |
| D13 | `repo-root -> ../..` symlink | 原位 | a（安装拓扑） | 不动；merge-note 与 `docs/contexts/toolbox/CONTEXT.md` 第 429 行写的理由不准（N7 §9 缺陷 7），另开票（F6） | — | 0 | — |
| D14 | subtree 根 `scripts/verify-geometry.py` 与 `test-verify-geometry.py` 的本仓改动（按顶层 `<svg>` 分坐标系；16px CJK 底板） | 原位 · 脚本 | e（能力本身） | 不动 | #12 | 0 | — |
| D15 | subtree 根 `commands/`、`prompts/`、插件清单 | 原位 · 未安装 | 未改 | 不动（ADR 0003 不走插件） | #11 | 0 | — |
| D16（已被 R12 第 6 节不动清单 改定） | `mmw-v2/merge-notes/diagram-design.md` | 原位 · 仓库文档 | — | 改写（随 R4 D5.3 的新格式）：每行标上 a 或 e 类；不改内容 | 与 merge-notes 单元共同的格式变更，本单元只是套用 | ≈+0（每行加一个类标记） | 取代：merge-note 各行只写「意图」。原意（每处改动说出它改变的行为）不变 |
| D17 | `SKILL.md` 41,198 字节，超出上游 ADR 0004 的 40,000 字节上限（R9-V5） | 原位 | — | 另开票（与 F5 同票）：压缩本仓加的句子，不动上游句子与 description | 票：**断点**（本仓改动让上游自己的检查失败，推断） | 票：−约 1.2 KB | — |

### 1.5 `writing-for-agents`（上游 mattpocock，`mmw-v2/upstream/skills/productivity/writing-for-agents/`）

#### 1.5.1 上游部分与连接句

| # | 部件 | 新位置 · 层 | a–f 类 | 动作 | 收益 | 体量 | 旧规则 · 原意 |
|---|---|---|---|---|---|---|---|
| W1 | description（「or writing any document an agent will consume」） | 原位 · 上游能力技能的触发 | b（触发句），但属于本能力自己的触发：正文第 6 行与上游 `CHANGELOG.md` 第 90 行都说本技能覆盖任何写给 agent 的文档；不是为 MMW 流程分支加的 | 不动（merge-note 已有行） | #13 | 0 | — |
| W2 | 第 8 行句末「When the skill you are writing … belongs to a set …, read `SKILL-SET-RULES.md` …」 | 原位 | d（连接到旁加的 MMW reference） | 不动 | #14 | 0 | — |
| W3 | 其余正文：`## Context pointers`、`## The two loads`、`## Information hierarchy`、`## Steps and completion criteria`、`## When to split`、`## Leading words`、`## Pruning` | 原位 | 上游原文 | 不动 | #11 | 0 | — |
| W4 | `SKILL-MECHANICS.md`（含 `## Router skills`：路由技能是用户触发的、「can only hint, never fire them」） | 原位 | 上游原文 | 不动。MMW 的 `mmw` 是模型可触发的路由，与这一节不同；差异与理由只写在 SSR 新节（W-SSR-3），不改上游 | **上游原文**（SSR `### Upstream skills`「Connect outside the upstream text first」） | 0 | — |
| W5 | `agents/openai.yaml` | 原位 | 上游原文 | 不动 | #11 | 0 | — |
| W6 | `mmw-v2/merge-notes/writing-for-agents.md` | 原位 · 仓库文档 | — | 改写 `### SKILL-SET-RULES.md` 一段：加「按名引用 `mmw` 技能的 `SKILL.md`、`playbooks/`、`principles/` 作范例；这些改名时同改」，并记下 SSR 与上游 `SKILL-MECHANICS.md` `## Router skills` 的有意分歧 | **断点**（否则 `mmw` 改名时没有人知道要改 SSR） | +2 行 | — |
| W7（已被 R12 K-38 改定） | 根 `AGENTS.md` `## External References` 第 49 行（指向 SSR） | 原位 · 仓库文档 | — | 不动 | #15 | 0 | — |
| W8 | `mmw-v2/tests/lib/check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py` 文件头对 SSR 的引用 | 原位 · lint | — | 不动（引用的 `### Descriptions` 等节名保留） | #16 | 0 | — |
| W9 | `docs/contexts/toolbox/CONTEXT.md` 中 `_Home_` 指向 SSR 的二十多条 | 原位 · 词表 | — | 不改现有条目；新增 **mode**、**playbook**、**principle** 三条的 `_Home_` 写 SSR `## Layers of the set`（**role pointer** 的 `_Home_` 归 dispatch 单元）；**mode** 条目的 `_Avoid_` 写「router skill（上游 `SKILL-MECHANICS.md` 里指用户触发的路由，含义不同）」 | **安家**（SSR `### Vocabulary`「The glossary is complete」） | +约 12 行 | — |

#### 1.5.2 `SKILL-SET-RULES.md`（SSR，176 行，d 类旁加文件，位置不动，内容改写）

位置不动的理由：它是 R4 D5.3 d 类的现成实例（上游目录旁新加、上游没有同名文件、拉取不冲突）；搬进 `mmw` 会让上游文本里的第 8 行（W2）去点名 `mmw` 的文件，`writing-for-agents` 从此依赖 `mmw`，拿不到任何一种收益。（已被 R12 K-38 改定：SSR、RSS 搬到 `docs/skill-set/`，第 8 行恢复上游原文。）

| # | SSR 小节（原标题） | 动作 | 改写要点（最终措辞实现时定） | 收益（证据） | 体量 | 被取代的旧规则 · 原意如何保住 |
|---|---|---|---|---|---|---|
| W-SSR-1 | 标题 `# Writing and reviewing a skill set` 与第 3 行开头段 | 改写（加一句） | 集合除技能外还有：`mmw` 技能（mode）与它目录里的 `playbooks/`、`principles/`，以及角色操作文件；写法见 `## Layers of the set` | **安家**（下文新节的入口） | +1 | — |
| W-SSR-2 | 第 5 行「Text inside an upstream subtree also follows that subtree's own `AGENTS.md`.」 | 不动 | — | #17a | 0 | — |
| W-SSR-3 | 新节 `## Layers of the set`（放在 `## What skill text is for` 之后、`## Checks` 之前） | 新建 | 约 22 行，分五段：① **mode**：全集只有 `mmw`，路由人带来的任务（`## Routes`）、把被唤醒或压缩的会话送回位置（`## Where you are`）、索引原则；模型可触发，与 `SKILL-MECHANICS.md` `## Router skills` 不同，理由是 playbook 的一步必须能点燃它点名的技能（在 Claude Code 上用户触发的技能对模型不可见，R4 V1）；篇幅上限由 `check_wiring.py` 执行，不写数字。② **playbook**：`mmw/playbooks/<task>.md`，R4 D3.2 的格式（H1、所有权行、可重入时 `## Where you are`、每步粗体名与 `Done when`、`**Reply:**`）；只在它排定两个以上能力的先后、有自己的门槛与交付物时才建，只调一个技能的是 `## Routes` 的一行。③ **角色操作文件**：`implement`、`code-review` 的 `references/session.md`、`advisor` 的 `references/advising.md`、`dispatch` 的 `references/night.md` 与 `one-ticket.md`；它们就是各角色的 playbook，不拆成三层；无人值守的以 `**Leaves:**` 收尾。④ **principle**：`mmw/principles/<slug>.md`，R4 D4.1 的格式、D4.3 的七条门槛、D4.2 的写法（具体规则留在调用方的步骤里，句末括注）；从外部合集引入的原则照录正文、去 frontmatter、description 改写成 `**Applies when:**`（R4 D7.4）。⑤ **登记表**：加一个组件只动 `skills.txt`、`## Routes`、`## Principles` 三处（原则另加调用方的括注），`check_wiring.py` 核对三者与实际一致（R4 D7.1） | **安家**：这些写法今天只在研究报告 R4 里，写组件的 agent 读不到（SSR `### Load and disclosure`「A rule sits in the text of the agent that must follow it」）；**外来**：登记表让新组件不改现有文字 | +22 | 取代：无（新内容）。与事实 7 的关系见 W-SSR-9 |
| W-SSR-4 | 事实 1–5 | 不动 | 事实 4 的「Upstream's `implement` is five lines」在分叉后仍成立（上游那份恢复原文） | #17b | 0 | — |
| W-SSR-5 | 事实 6「Skills are peers composed by name.」 | 改写（加方向规则） | 能力技能之间仍是按名组合的平级件；能力技能不点名 playbook 的顺序；playbook 与原则是 `mmw` 目录里的文件，别的技能按「the `mmw` skill's `playbooks/x.md`」「the `mmw` skill's principle `slug`」点名，这不是嵌套技能 | **断点**：事实 6 原文只有「平级」，与 R4 §12 的方向规则（playbook → 能力技能是单向的）冲突 | +2 | 被改写：「peers」只适用于能力技能之间。原意（不嵌套、不复制别人的文件、不复述别人的规则）原句保留；与 Memory `fe94802d`「平级调用、禁止嵌套」不冲突（R4 §9） |
| W-SSR-6 | 事实 7 第一、二句（「Everything has one home …」到「… contradicts it」） | 不动 | — | #17c | 0 | — |
| W-SSR-7 | 事实 7「this is why MMW ships no router skill, since every description is already in the agent's runtime」 | 删除，换成一句 | 换成：路由只有一个家，是 `mmw` 的 `## Routes`；它只列会改变去处或带门槛的行，别的由各自 description 负责（与 W-SSR-9 同一条规则） | **断点**：与 R4 已定的 `mmw` 直接冲突（R4 §9 表「SSR 事实 7『MMW ships no router skill』→ 废止」） | ±0 | 废止「no router」。它原本防两件事（R4 §9）：第二份地图漂移（`ask-matt` 的漂移，`docs/reviews/2026-09-23-skill-set/汇总.md` 第 44 行）；一跳找不到下一步（#538）。新做法：地图只有一份；行与 playbook 的一致由 `check_wiring.py` 第 3–5 类保证；「一件东西第二份就是 finding」的原句（W-SSR-6）不动，所以任何第二张地图仍是 finding |
| W-SSR-8 | 事实 7「A skill's place follows from its own text: its description says when it starts, and its closing section says what comes next. Read in pipeline order, the closing sections walk from an idea to a closed ticket with no gap, and no two skills claim one moment.」 | 改写 | description 仍只说何时开始；一类任务的顺序只有一个家（一份 playbook 或一个角色操作文件）；能力技能结尾只说交回什么；「从想法走到关票没有缺口」改成「从 `mmw` 出发，路由加 playbook 步骤与角色操作文件连起来走到关票，没有缺口，一个时刻不被两处认领」 | **断点**：原句让每个技能的结尾承担顺序，与 R4 D5.4（顺序只有一个家、固定返回句）冲突 | ±0 | 原意（#538：一跳找不到下一步）由「从 `mmw` 出发走得通」加 RSS 第 4 步的走查保住 |
| W-SSR-9 | `### Descriptions` 第 2 条（并排读所有 description） | 改写（加一句） | 并排读时连同 `mmw` 的 `## Routes` 一起读：一行路由的情境已被某个 description 认领、行里又没有自己的门槛，就是重复，删掉这一行 | **重复**：给 E13 这类行一个判据；**断点**：否则 R4 D2.2 草案的 `exe-release` 行会与 description 双重认领 | +1 | — |
| W-SSR-10 | `### Descriptions` 第 1、3、4 条 | 不动 | 第 4 条末句「The `disable-model-invocation` pairing on upstream skills is in `mmw-v2/merge-notes/README.md`」保留（配对规则仍在那里） | #17d | 0 | — |
| W-SSR-11 | `### Load and disclosure` 全节 | 不动 | 第 1、2 条（`SKILL.md` 的找时刻表、表在有副作用的步骤之前）照样适用于能力技能；头部任务的重入表由 W-SSR-3 的 playbook 格式（`## Where you are`）给出，不必在这里重写 | #17e | 0 | R4 §9 说「保留，分两类」；两类分别由本节与 W-SSR-3 承载，不必改本节文字 |
| W-SSR-12 | `### Redundancy and bloat` 第 1 条「Duplication」 | 改写（加一句） | `mmw` `## Principles` 的索引行（标题、何时适用、一句规则）是原则的指针，不是副本；索引行与原则文件冲突时以原则文件为准 | **断点**：R4 D2.2 的索引行格式「`**<Title>** (slug). <when>. <one-sentence rule>.`」按本条现文就是「one meaning stated in two places」，两份已定文字互相冲突（本轮对读两处原文） | +1 | 本条原意（一个意思只有一份）保住：索引行只作为触发指针，规则的权威是原则文件 |
| W-SSR-13 | `### Redundancy and bloat` 其余、`### Scripts and judgement` 全节 | 不动 | R4 §9 建议在 `### Scripts and judgement` 加「脚本印出的锚点由 lint 核对」。不加：每个套件的 `run.sh` 都先跑 `check_wiring.py`，写技能的人跑套件时就会碰到它的拒绝；再写一句是 SSR 自己说的 over-specification（事实 2：可检查的规则做成检查，不写成句子） | #17f | 0 | — |
| W-SSR-14 | `### Vocabulary` | 不动 | 最后一条「A heading or step that another skill finds by position is cited … by title rather than by number」已经是 `RESUME:` 改印步骤名（R4 D3.5 a）的依据。新词条写进词表（W9） | #17g | 0 | — |
| W-SSR-15（已被 R12 K-7 改定） | `### Hand-offs`「Each skill ends by naming what comes next, or the caller it returns to, and the skill it returns to has an entry for an agent arriving that way.」 | 改写 | playbook 的步骤点名下一步；能力技能结尾写交回什么；下一步只取决于本技能自身输出时（例：`design-pages` `references/pull.md` `## Reached from here`）才在结尾分支点名；分叉技能里只重述 playbook 顺序的结尾换成固定返回句，原文逐字写在这里一次：「Then return to the playbook that sent you; with none, the `mmw` skill routes what follows.」 | **断点**：原句与 R4 D5.4 冲突；**重复**：固定返回句的原文只在一处，`to-spec`、`to-tickets`、`retro` 照抄，`check_wiring.py` 按它识别 | +2 | 原意（产出无人接手）保住：playbook 步骤与固定返回句都保证下一跳有去处 |
| W-SSR-16 | `### Hand-offs`「Invoking another skill, in MMW: …」 | 改写（补写法） | 列出 `check_wiring.py` 只认的几种写法：调用技能「the `X` skill」；技能内文件「the `X` skill's `references/y.md`」；playbook「the `mmw` skill's `playbooks/x.md` **Step**」；原则括注「(principle `slug`)」（`mmw` 目录内）与「(the `mmw` skill's principle `slug`)」（其他技能）；不要求模型可触发的「tell the user to run `/X`」 | **断点**：R4 K9（写法多种时 lint 漏报）；这是 lint 与写作者之间的接口，不写就无处可查 | +2 | — |
| W-SSR-17 | `### Hand-offs` 其余各条（含「Each event gets one instruction」） | 不动 | 「Each event gets one instruction」仍需文字：`check_wiring.py` 第 2 类只覆盖 `WAKES` 事件，退出码、拒绝文字等其他事件仍靠判断 | #17h | 0 | — |
| W-SSR-18 | `### Prompts written for other agents` | 改写（加一条） | 脚本送进活会话的消息，末行可以带一行来自 `dispatch` 指针表的角色指针：技能、文件、小节，是地址，不是规则，也不含 tracker 数据 | **安家**：ADR 0020 修订后的规则（R4 D1.2）在写作侧没有家；SSR 自己规定「the sentence the agent acts on is in the skill text」 | +1 | 修订 ADR 0020「文字只带 `#<n> <event>`」的原意（不复述 tracker 内容）由「指针不含 tracker 数据」保住 |
| W-SSR-19 | `### Upstream skills` 开头段与前四条 | 改写（并入 a–f 表） | 保留开头段；加 R4 D5.3 的 a–f 分类表（f 分叉、a 宿主中立、b 调用开关与触发句、c 下一步、d MMW 存放位置与格式、e 改变能力或防错、其他→恢复原文），第一个命中的决定去处。现有第 3 条「Connect outside the upstream text first」并入 d 行；现有「rewording for style … restoring the upstream text」并入「其他」行；「Every changed paragraph maps to a merge-note entry」并入 e 行 | **上游原文**：a–f 是把 MMW 流程移出上游文本的判据；**外来**：同一张表适用于以后从 pstack 引入的技能 | +8 | 原有四条的意思都在表里，只是按类排列 |
| W-SSR-20 | `### Upstream skills` b 行的调用开关推导规则（R4 D1.3） | 新建（在 b 行里） | 一个技能被 `mmw` 的 `## Routes`、某份 playbook 的一步、某个角色操作文件、某个启动提示词，**或另一个技能**按名调用（包括「读它的 `SKILL.md` 并照做」），就不带两个开关；否则保持上游设置；「告诉用户运行 `/X`」不算调用；`check_wiring.py` 检查。加粗部分是我对 R4 D1.3 的扩展，见第 8 节 U-R9-2 | **重复**：取代 `merge-notes/README.md` `## disable-model-invocation` 第二段手写的 7 个名单（那段改成指向这里，由 merge-notes 单元改）；**断点**：D1.3 原文不数能力技能之间的调用，而 `diagram-design`、`writing-for-agents` 正是被能力技能调用的（R9-V7、R9-V1） | +2（在表内） | 取代手写名单。原意（不抢触发、夜里不被 worker 误触发、不往产品根目录写文件）由「没被调用的保持上游设置」保住；今天推导结果与现状相同 |
| W-SSR-21 | `### Upstream skills` 末条「When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text. Its upstream original remains the measure of length …」 | 改写 | 上游行不到一半的技能分叉进 `mmw-v2/skills/`（名字不变），上游那份恢复原文、不安装；分叉后是集合自己的文本；分叉起点的上游原文仍是篇幅的尺子。搬家与拉取步骤写在 `merge-notes/README.md` 的分叉表，这里不写 | **上游原文**（R4 D5.3 f） | ±0 | 取代「按自有文本审」。原意（上游被改写后无法跟进；新增要以上游没有的判断为代价）保住：前者由分叉解决，后者保留原句 |
| W-SSR-22 | `### Upstream skills` 新增一条：从别的合集引入能力技能的进门检查 | 新建 | R4 D7.3 四条：产出可命名交付物、能脱离 mode 调用（否则是 playbook）；用到的 Cursor 专有机制都有替代（R4 D7.5，替代不了的不收）；与已装技能的 description 并排读不抢同一件事；夜里会被点名的必须模型可触发。四种引入方式（subtree、subtree split、钉提交快照、分叉）属维护者步骤，放 `merge-notes/README.md` | **外来**；**安家**（这些门槛今天只在 R4） | +5 | — |
| W-SSR-23 | `### Paths and host neutrality` 与其后的 grep 说明 | 改写（扩范围） | grep 范围从「every `SKILL.md`, description and reference」扩到 `mmw` 的 `playbooks/` 与 `principles/`；检查项加「指向 `mmw-v2/` 的路径」（运行时读已安装的技能目录，不读工作树，Self-hosting boundary） | **断点**：新文件类型不在现有 grep 范围里（R4 T7） | +1 | — |
| W-SSR-24 | `### Rules and completion criteria`、`### Examples`、`### Refusals and output an agent reads` | 不动 | playbook 属于「the set's own text」，第一条已要求 `Done when` | #17i | 0 | — |
| W-SSR-25 | `## Editing` | 不动 | 第 4 条（改名前 grep 全集）已覆盖 playbook 步骤名与原则 slug；lint 在套件里自动跑 | #17j | 0 | — |
| W-SSR-26 | `## Verifying` 第 2 条「a fresh agent given only the trigger and a real job」 | 改写（半句） | 人带来的任务，走查从消费仓库 `AGENTS.md` 那一行到 `mmw` 开始，而不是从被路由到的技能的 description 开始 | **断点**：否则走查跳过路由这一跳，R4 T8 测不到 `mmw` 的效果 | +0.5 | — |
| W-SSR-27 | `## Upstream examples` 表 | 不动 | 表按 squash 提交读原文，分叉后仍然成立 | #17k | 0 | — |

SSR 合计：约 +40 行、−3 行（176 → 约 213）。

#### 1.5.3 `REVIEWING-A-SKILL-SET.md`（RSS，33 行，d 类旁加文件，位置不动）

| # | RSS 小节 | 动作 | 改写要点 | 收益 | 体量 | 旧规则 · 原意 |
|---|---|---|---|---|---|---|
| W-RSS-1 | 开头三段（认知走查、Scope、只读命令）、两类证据、「Every finding is fixed」 | 不动 | Scope 的「every message a script prints for an agent」已包括角色指针与 `RESUME:` 行 | #17l | 0 | — |
| W-RSS-2 | 第 1 步 **List the tasks** | 不动 | 三种入口里的「a sentence in another skill or script that sends the agent to it」已包括 `## Routes` 行、playbook 步骤与角色指针 | #17l | 0 | — |
| W-RSS-3 | 第 2 步 **Walk each task** | 改写（加一句） | 人带来的任务从 `mmw` 起步（消费仓库 `AGENTS.md` 那一行加载它）；被唤醒的会话从唤醒行加它末尾的角色指针起步 | **断点**：否则走查的起点不是 agent 实际的起点 | +1 | — |
| W-RSS-4 | 第 3 步 | 不动 | — | #17l | 0 | — |
| W-RSS-5 | 第 4 步 **Read across the scoped skills** 中「the closing sections read in pipeline order leave no gap and no moment claimed twice」 | 改写 | 从 `mmw` 出发，路由、playbook 步骤与角色操作文件连起来走到关票，没有缺口；一个时刻不被 description 与路由行、或两个 playbook 步骤同时认领；先跑 `check_wiring.py` 并记录结果，它查过的名字、锚点、登记表不再手查 | **断点**：随 W-SSR-8；**重复**：不让复审重做 lint 已做的检查 | +1 | 原意（走得通、不双重认领）不变，只换了起点与承载者 |
| W-RSS-6 | 第 5、6 步 | 不动 | — | #17l | 0 | — |

RSS 合计：约 +2 行。

---

## 2. playbook 草图

**本单元不产生 playbook，也不是任何头部 playbook 的一步。** 参与的唯一流程边是：orchestrator 的角色操作文件 `dispatch` `references/night.md` `## 5` 调 `retro`，`retro` 第 11 步（`retro/SKILL.md` 第 145 行）在写 `prompt_change` 前读 `writing-for-agents`。这条边原样保留，见第 4 节。

考虑过、没有建的三份 playbook：

| 候选 | 为什么不建 |
|---|---|
| `authoring-a-component.md`（pstack `authoring-a-skill.md` 的对应物：grep → 按 SSR 写 → 跑套件 → 走查 → 四步提升） | 它只调一个技能（`writing-for-agents`）就是 L7 C.6 信号 5；顺序已在 SSR `## Editing`、`## Verifying` 与本仓 `AGENTS.md` `## Gotchas` 的四步提升里；本仓对技能的修改本来就走 `idea-to-tickets` → 夜 → worker（本仓 `AGENTS.md`「This repository's own changes are numbered tickets」），worker 经 `AGENTS.md` 第 49 行读到 SSR |
| `adopting-a-repo.md`（`setup-matt-pocock-skills` → `manage-agents-md` → `code-checkers` → `ui-acceptance` 填 `.mmw/target.json` → 加 `mmw` 那一行） | R4 §6 已否决 R3 的 `adopting-mmw.md`（一次性步骤）；`docs/research/mmw-structure/2026-09-06-handoff.md` 第 110 行记录的判断「三者由不同的人在不同时刻触发，合并只是把路由再散一次」（讨论结论，N7 §7 已核实原文）；把它们排成一条顺序会给一个今天不存在的任务类型造 playbook（信号 1、2） |
| `shipping.md`（出包） | `exe-release` 本身就是单入口、单任务的能力（L7 C.1 第 7 问、C.3），步骤全在它的 `SKILL.md` 里；拆成 playbook 加能力技能是信号 10 |

---

## 3. 原则候选

### 3.1 够格的原则

本单元没有够格的新原则（R4 D4.3 七条门槛）。原因逐条见 3.2。

### 3.2 看起来像原则、应留在原处的规则

| 规则（原文位置） | 为什么留在原处 |
|---|---|
| 「A tool whose version changes what the repository produces belongs to the repository.」（`code-checkers` `## The rule that decides where a tool goes`） | 只有一个调用方；绑定具体机制（依赖清单、全局安装）；L7 C.2 第 1 行 |
| 「Pin the formatter exactly, the checkers loosely」（`code-checkers`） | 同上，领域参数 |
| 第 4、5 步「useful on day one」「每个检查器要证明自己会失败」（`code-checkers`） | 是 `mmw` 原则 `silence-is-never-a-pass` 的一个具体应用。不加括注：具体规则和理由（「each reports the same zero as a clean repository」）已在步骤里，括注不改变任何决定（L7 C.6 信号 2）；而且会让一个非 MMW 仓库也用的能力依赖 `mmw` |
| 「The paths are evidence, not the rule … including one it did not costs one build」（`exe-release` `## 2.`） | 单一调用方；绑定 release manifest |
| 「Adding a product means writing a release manifest. It does not mean writing Python.」与 `## What belongs where`（`exe-release` `references/key.md`） | 单一调用方；领域专属（值归 manifest、动作归技能、业务归产品仓库） |
| 「The release engine owns the loop … Do not resume from session memory」（`exe-release` `references/driving.md`） | 与 `the-tracker-is-the-state` 同源（状态在持久存储里，不在会话记忆里），但它的存储是 `.release/release-state.json`，不是 tracker，原则名套不上；具体规则已在文中。若原则单元把这条原则放宽成「状态在会话之外」，这里可以加括注；今天不加（信号 2） |
| 「An `AGENTS.md` is loaded into every session … each line is obeyed as fact」（`manage-agents-md` 开头） | 单一调用方；它是这个能力的目的段（SSR 事实 1），不是跨任务判断 |
| 「The highest-quality move is usually deletion.」（`diagram-design` §1，上游）与「先嵌套、读一次就看懂一个系统」（本仓改动） | 前者是上游原文；后者只在一个技能里（虽然写了四处），属于该能力的做法；D4.3 第 4、5 条不满足 |
| SSR 事实 1–7 | D4.3 第 7 条：它们的读者群（写技能的人）已有家，就是 SSR 本身；R4 D7.4 已说明 pstack 的 `encode-lessons-in-structure` 对应 SSR 事实 2，不另建 |

---

## 4. 连线

组件名写法：`mode:mmw`、`role:<skill>/<file>`（角色操作文件）、`skill:<name>`、`ref:<skill>/<file>`、`script:<skill>/<file>`、`lint:tests/lib/<file>`、`suite:tests/<name>/run.sh`、`config:`、`artifact:`、`entry:description(<skill>)`（宿主扫描 description 触发）、`user`。标「新」的是新架构加的边，标「相邻」的是别的单元持有、本单元一端参与的边。`mode:mmw -> skill:exe-release : routes-to` 不在其中（E13）。

```edges
entry:description(exe-release) -> skill:exe-release : routes-to
skill:exe-release -> script:exe-release/release-flow.sh : runs-script
skill:exe-release -> ref:exe-release/references/driving.md : reads-reference
skill:exe-release -> ref:exe-release/references/new-product.md : reads-reference
ref:exe-release/references/new-product.md -> ref:exe-release/references/key.md : reads-reference
ref:exe-release/references/driving.md -> script:exe-release/release-flow.sh : re-enters-at
ref:exe-release/references/key.md -> script:exe-release/verify_key.py : runs-script
ref:exe-release/references/key.md -> script:exe-release/release_script_assembler.py : runs-script
script:exe-release/release-flow.sh -> script:exe-release/release_contracts.py : runs-script
script:exe-release/release-flow.sh -> script:exe-release/verify_key.py : runs-script
script:exe-release/release-flow.sh -> script:exe-release/release_script_assembler.py : runs-script
script:exe-release/release_script_assembler.py -> script:exe-release/builders/nuitka.py : calls
script:exe-release/release_script_assembler.py -> script:exe-release/release_templates/nuitka_electron.ps1.tmpl : reads-reference
script:exe-release/release-flow.sh -> script:exe-release/diagnose_core.py : runs-script
script:exe-release/release-flow.sh -> script:exe-release/fix_dispatch.py : runs-script
script:exe-release/release-flow.sh -> config:<product>.release-adapter.json : configured-by
script:exe-release/release-flow.sh -> config:remote-build.json : configured-by
skill:exe-release -> user : hands-off-to
entry:description(code-checkers) -> skill:code-checkers : routes-to
skill:code-checkers -> ref:code-checkers/references/python.md : reads-reference
skill:code-checkers -> ref:code-checkers/references/typescript.md : reads-reference
skill:code-checkers -> ref:code-checkers/references/git-hooks.md : reads-reference
skill:code-checkers -> skill:manage-agents-md : reads-reference
skill:code-checkers -> artifact:checker command : hands-off-to
artifact:checker command -> config:.mmw/target.json#checks : configured-by
script:verify-ticket/verify-ticket.py -> artifact:checker command : runs-script
script:dispatch/dispatch.sh -> artifact:checker command : runs-script
artifact:git commit -> artifact:prek pre-commit hook : enforced-by-hook
entry:description(manage-agents-md) -> skill:manage-agents-md : routes-to
skill:manage-agents-md -> script:manage-agents-md/check.sh : runs-script
skill:manage-agents-md -> ref:manage-agents-md/references/create.md : reads-reference
skill:manage-agents-md -> ref:manage-agents-md/references/rewrite.md : reads-reference
ref:manage-agents-md/references/create.md -> skill:manage-agents-md : re-enters-at
ref:manage-agents-md/references/rewrite.md -> skill:manage-agents-md : re-enters-at
skill:manage-agents-md -> artifact:host general-purpose subagent (survey) : starts-with-prompt
skill:manage-agents-md -> skill:code-checkers : hands-off-to
skill:manage-agents-md -> artifact:AGENTS.md, CLAUDE.md, CODING_STANDARDS.md, TESTING.md : hands-off-to
artifact:consumer AGENTS.md#External References -> mode:mmw : routes-to
mode:mmw -> artifact:consumer AGENTS.md#External References : hands-off-to
script:dispatch/dispatch.sh -> artifact:consumer AGENTS.md#External References : reads-reference
role:code-review/references/standards-reviewer.md -> artifact:CODING_STANDARDS.md : reads-reference
entry:description(diagram-design) -> skill:diagram-design : routes-to
skill:wait-what -> skill:diagram-design : calls
skill:improve-codebase-architecture -> skill:diagram-design : calls
skill:diagram-design -> ref:diagram-design/references/* : reads-reference
skill:diagram-design -> script:diagram-design/scripts/self_check.py : runs-script
skill:diagram-design -> script:diagram-design/scripts/*_extract.py : runs-script
skill:diagram-design -> script:diagram-design/repo-root/scripts/verify-geometry.py : runs-script
skill:diagram-design -> script:diagram-design/repo-root/scripts/verify-motion.py : runs-script
skill:diagram-design -> script:diagram-design/repo-root/scripts/lint-skin.py : runs-script
skill:diagram-design -> config:.diagram-design marker and profile : configured-by
entry:description(writing-for-agents) -> skill:writing-for-agents : routes-to
skill:writing-for-agents -> ref:writing-for-agents/SKILL-MECHANICS.md : reads-reference
skill:writing-for-agents -> ref:writing-for-agents/SKILL-SET-RULES.md : reads-reference
ref:writing-for-agents/SKILL-SET-RULES.md -> ref:writing-for-agents/REVIEWING-A-SKILL-SET.md : reads-reference
artifact:this-repo AGENTS.md#External References -> ref:writing-for-agents/SKILL-SET-RULES.md : routes-to
role:dispatch/references/night.md -> skill:retro : calls
skill:retro -> skill:writing-for-agents : calls
ref:writing-for-agents/SKILL-SET-RULES.md -> mode:mmw : reads-reference
ref:writing-for-agents/REVIEWING-A-SKILL-SET.md -> lint:tests/lib/check_wiring.py : runs-script
suite:tests/<name>/run.sh -> lint:tests/lib/check_wiring.py : runs-script
suite:tests/<name>/run.sh -> lint:tests/lib/check_own_skill_frontmatter.py : runs-script
suite:tests/<name>/run.sh -> lint:tests/lib/check_upstream_em_dashes.py : runs-script
suite:tests/exe-release/run.sh -> script:exe-release/release-flow.sh : runs-script
suite:tests/manage-agents-md/run.sh -> script:manage-agents-md/check.sh : runs-script
```

说明：

- 新：`artifact:consumer AGENTS.md#External References -> mode:mmw`、`mode:mmw -> artifact:consumer AGENTS.md…`、`script:dispatch/dispatch.sh -> artifact:consumer AGENTS.md…`（这三条的持有者是 mode 与 dispatch 单元，本单元只保证 `manage-agents-md` 不删这一行）；`ref:…/SKILL-SET-RULES.md -> mode:mmw`（W-SSR-3 以 `mmw` 的文件为范例）；`ref:…/REVIEWING-A-SKILL-SET.md -> lint:…/check_wiring.py`（W-RSS-5）；`suite:… -> lint:…/check_wiring.py`（R4 D3.6）。
- 相邻：`role:dispatch/references/night.md -> skill:retro`、两条 `script:… -> artifact:checker command`、`role:code-review/…`。
- `skill:code-checkers -> skill:manage-agents-md : reads-reference` 表示第 8 步按 `manage-agents-md` 定的标题写行，不是调用。`skill:manage-agents-md -> skill:code-checkers : hands-off-to` 是「在报告里建议用户用 `code-checkers`」，属于「告诉用户」的写法，不要求模型可触发。
- 没有 `cites-principle`、`wakes`、`enforced-by-hook`（宿主 hook）边：本单元的技能不被夜里的脚本唤醒，不被 `tool-guard.py`、`turn-guard.py` 拦截的规则约束，也不引用原则（第 3 节）。唯一的 `enforced-by-hook` 是消费仓库的 git pre-commit hook，由 `code-checkers` 装。

---

## 5. 不动清单

| # | 部件或段落 | 理由 |
|---|---|---|
| 1 | 四个自有技能与 `diagram-design` 的 description | 只写触发（SSR `### Descriptions`）；本轮并排读过五条，没有两条认领同一件事。`writing-for-agents` 与 `manage-agents-md` 都涉及 `AGENTS.md`，但各自只写自己那部分（写作杠杆 / 固定格式），属 SSR 允许的「caller and the skill it hands to may share a trigger word」 |
| 2 | 五个技能的正文主体（`exe-release` `## 1.`–`## 5.`；`code-checkers` 全部小节；`manage-agents-md` `## Find your situation` 到 `## Verify and report`） | 天然整体：每一份都是一个能力服务一个可命名交付物的内部步骤（L7 C.3，N7 §8 已逐一核实各自的硬依赖）；没有一段是「交付物之后按任务类型做什么」（R9-V8） |
| 3 | `exe-release` 第 2 步「Show this list once and continue」、第 5 步「Stop and wait for the user」 | 能力技能自带的人工闸门（L7 A.3），能脱离 mode 调用时必须自带 |
| 4 | 各 reference（`driving.md`、`new-product.md`、`key.md`；`python.md`、`typescript.md`、`git-hooks.md`；`create.md`、`rewrite.md`） | 分支 reference 天然按分支读。`driving.md` 与 `git-hooks.md` 每次运行都读，按 SSR 事实 5 算 fragment，但内联只减少一次跳转，不在用户要求 2 的六种收益里，所以不动（第 8 节 U-R9-4） |
| 5 | 全部脚本、测试、`downstream-notes`、`docs/contexts/release/CONTEXT.md` 的位置 | 已跑通；脚本与状态表是同一接口（N7 §8：`f1752183` 就是两边不一致时修的）；移动拿不到任何收益 |
| 6 | `code-checkers` Settled choices 里的时效事实 | 自带「Re-check both facts against the tools' own release pages」；是内容维护，不是架构 |
| 7 | `code-checkers` 第 6 步的 `.mmw/target.json` / `MMW_BASE_REF` 句 | 这是交付物（checker command）的接口：写命令的 agent 在这一刻必须知道命令会被 `checks` 以 `MMW_BASE_REF` 调用（SSR「A rule sits in the text of the agent that must follow it」）。另一端 `ui-acceptance` `references/product-answers.md` 第 77–78 行定义 `checks` 字段，读者是填 `.mmw/target.json` 的 agent；两端读者不同，L7 C.5 允许。也不是「任务顺序」，所以不进 playbook（R4 D5.1） |
| 8 | `code-checkers` 第 8 步按 `## Commands`、`## Key Conventions` 加行 | 生产方与消费方的同一约定两端（N7 §4），`manage-agents-md` `### Language` 是另一端 |
| 9 | `manage-agents-md` survey 提示模板留在 `SKILL.md` | L7 A.5 的做法（子代理提示模板放 reference）与 SSR 事实 5（每次都读的内联）指向相反；两边都拿不到六种收益之一，维持现状 |
| 10 | `manage-agents-md` `### Code and test rules` | 放置规则只在这里（R9-V9，不是重复）；句中的 reviewer 轴与 worker 是目的说明（SSR 事实 1），不是流程顺序 |
| 11 | `diagram-design` 与 `writing-for-agents` 的上游原文部分（D1、D10–D12、D15、W3–W5） | 上游原文，没有 MMW 改动，按 SSR `### Upstream skills` 原样 |
| 12 | `diagram-design` 的 a 类与 e 类改动（D2–D5、D7–D9、D14） | 按 R4 D5.3 留在上游文本、各有 merge-note 行；逐条都不含 MMW 流程名词（R9-V8）；D3 若搬到调用方，用户直接斜杠进入时会失去「不停下问品牌」 |
| 13 | `writing-for-agents` description（W1） | 本能力自己的触发，不是为 MMW 流程分支加的；恢复上游的「modifying AGENTS.md or CLAUDE.md」反而会与 `manage-agents-md` 认领同一时刻（merge-note 原意） |
| 14 | `writing-for-agents` 第 8 行连接句（W2） | 是在其他仓库到达 SSR 的唯一入口（R9-V1），retro 在消费仓库写 `prompt_change` 时也经这里；删掉就是断点。它已是 d 类连接的最小形态（一句话指向旁加文件） |
| 15 | 根 `AGENTS.md` 第 49 行 | Need 列「Every rule for the text of a skill (`SKILL.md`, references, descriptions, prompts a script builds for an agent)」已覆盖 `mmw` 目录下的 playbook 与原则（它们是技能目录里的文本）和脚本送出的角色指针 |
| 16 | 两个 lint 的文件头 | 引用的 SSR 节名不变 |
| 17 | SSR 与 RSS 中未列入改写的小节（a 第 5 行；b 事实 1–5；c 事实 7 前两句；d `### Descriptions` 其余；e `### Load and disclosure`；f `### Scripts and judgement` 与 `### Redundancy and bloat` 其余；g `### Vocabulary`；h `### Hand-offs` 其余；i `### Rules …`、`### Examples`、`### Refusals …`；j `## Editing`；k `## Upstream examples`；l RSS 开头与第 1、3、5、6 步） | 新架构下仍然成立，逐条理由见第 1.5.2、1.5.3 节对应行；改它们说不出收益 |
| 18 | SSR 与 RSS 的文件位置 | d 类旁加文件的现成实例；搬进 `mmw` 会让上游第 8 行点名 `mmw`，没有收益 |
| 19 | 不新建 `SKILL-SET-LAYERS.md` 之类的分支文件 | W-SSR-3 只有写 mode、playbook、原则的人需要，按 SSR 事实 5 可以拆出；但拆分只减少读量，不在六种收益里，所以并入 SSR（第 8 节 U-R9-4） |

顺路发现、另开普通票的现有缺陷（不属于架构，不改变任何部件的位置）：

| # | 缺陷 | 核实 | 票的收益 |
|---|---|---|---|
| F1 | `exe-release/SKILL.md` 第 16 行称 `init` 拒绝脏工作树，`cmd_init` 没有这项检查。修法（工程决定）：给 `cmd_init` 加脏树检查并配测试，文字不动（SSR 事实 2：能检查的规则做成检查；2026-09-28 复审 D6 定的也是 `init` 拒绝，N7 §10） | R9-V4 已核实 | 断点：agent 以为脚本会拦，脚本不拦，用户可能装到与眼前代码不一致的包 |
| F2 | `release-flow.sh` 第 133–135 行（预算记账）、第 1160–1162 行（`fix_dispatch.py` 退出码）两处注释与代码不符 | N7 §9 缺陷 2、3 已核实；本轮未复核 | 维护者注释，agent 不读 |
| F3 | `key.md` 未写 `build_machine`、`diagnose`、`diagnose_branches`、`diagnose_core_exe_glob`；`release/CONTEXT.md` `diagnoser` 的 `_Home_` 指向 `key.md` | N7 §9 缺陷 5 已核实；本轮未复核 | 断点：写 manifest 的 agent 读不到四个字段；词表条目与 Home 不符（SSR `### Vocabulary`） |
| F4 | `new-product.md` 第 35–36 行代码例里的中文注释 | N7 §9 缺陷 6 已核实 | SSR `### Vocabulary`「Skill text is English」 |
| F5 | `diagram-design` 三处「split」漏改（R9-V6）；`SKILL.md` 超出上游 40,000 字节上限（R9-V5） | 已核实 | 断点：同一技能内两种相反指令；本仓改动让上游自己的检查超限（推断会失败） |
| F6 | `repo-root` symlink 的理由写得不准（merge-note `### repo-root（symlink）`、`toolbox/CONTEXT.md` 第 429 行） | N7 §9 缺陷 7 已核实 | 维护者文档，agent 不读 |

---

## 6. 形式拆散自查（L7 C.6 十一个信号）

| # | 信号 | 结果 |
|---|---|---|
| 1 | 没有先确认已有组件不是合适的归宿 | 未触发。新增内容全部放进已有文件：SSR（新节与各条改写）、RSS、`manage-agents-md` 第 9 条、词表；没有新文件 |
| 2 | 新增内容不改变决定 | 未触发。W-SSR-3 改变写组件的人把内容放在哪、写成什么格式；W-SSR-9 决定一行路由删不删；W-SSR-15/16 决定结尾写什么、调用怎么写；M6 决定 rewrite 时那一行留不留。拒绝了三处只让 agent 多读的新增：`code-checkers` 与 `driving.md` 的原则括注（第 3.2 节）、SSR `### Scripts and judgement` 的 lint 句（W-SSR-13） |
| 3 | 重复已有的、位置得当的指引 | 未触发，两处说明：① W-SSR-3 与新 ADR 都写 mode、playbook、原则：ADR 给维护者记决定与取舍，SSR 写 agent 行动时依据的那句，SSR `### Load and disclosure` 明确要求这样分；② `mmw` `## Principles` 的索引行与原则文件并存，由 W-SSR-12 把索引行定为指针，而不是承认一份副本 |
| 4 | 本可由机制强制的规则写成了文字 | 未触发。mode 的行数上限、调用写法、开关推导、登记表一致都交给 `check_wiring.py`，SSR 只说「由它执行」，不写数字、不复述检查项。保留为文字的都是判断：原则的七条门槛、a–f 分类、进门检查 |
| 5 | playbook 只调一个技能 | 未触发。本单元不建 playbook（第 2 节列了三个没建的候选） |
| 6 | reference 每次都读、只有一个调用方、读者是本代理 | 未触发。没有新 reference；现有的 `driving.md`、`git-hooks.md` 符合这个描述，但它们是现状，本方案没有拆出它们，也不合并（第 5 节 #4） |
| 7 | 原则说不出改变哪个决定 | 未触发。不建原则，也不加括注 |
| 8 | 拆完需要按步骤编号引用 | 未触发。W-SSR-16 规定按名引用；`driving.md` 里的「`exe-release` step 3」「step 4」是同一技能内按标题引用（标题本身带编号），不是拆分造成的 |
| 9 | 拆出的内容没有第二个调用方、也不减少重复 | 未触发。没有拆出任何内容；`diagram-design` §6 marker 句正因为有两个调用方才留在能力里（D7） |
| 10 | 单入口固定流程拆成三层 | 未触发。`exe-release` 保持单一能力技能，不拆成 mode 行加 playbook 加技能；连 `## Routes` 行也去掉（E13） |
| 11 | 只在流程之间复用的内容做成能力技能 | 未触发 |

---

## 7. 待用户决定

只有一件，且不属于这次重构，是顺路核实到的：

- **agentflow 与 xiaohuangya 的 release manifest 仍带着已删的四个字段**（R9-V10：`~/agentflow` `dev` 上的 `hedgehog`、`parrot`，`~/xiaohuangya` 分支 `2026-09-07-agent-setup-alignment` 上的 `duck`）。`mmw-v2/downstream-notes/release-self-heal-removed.md` 已写明要删什么；不删的话，这些产品下一次出包时 `init` 会被 `release_contracts.py` 以多余字段拒绝（推断，没有运行）。影响：这三个产品在删掉字段之前出不了包。可以撤回：删字段是 git 里的普通提交。要你定的是范围与顺序：什么时候在那两个仓库执行这份 downstream-note。

本单元其余的决定都是工程决定，已在上文做出并写明理由：`exe-release` 不进 `## Routes`（E13）；U4 由 `mmw` 与 `dispatch.sh check` 负责、`manage-agents-md` 只保留那一行（M13）；SSR 与 RSS 留在原位并在原位改写。

---

## 8. 未确定

| # | 问题 | 为什么定不了 | 需要什么才能定 |
|---|---|---|---|
| U-R9-1 | 去掉 `exe-release` 路由行后，读了 `mmw` 的会话听到「出包」会不会误走 `## Head judgement` | `mmw` 的 `## Where you are` (e) 把「一个人带来一件任务」送去 `## Head judgement` 与 `## Routes`；没有一行兜底时，agent 可能把「出包」当成要拆票的工作（推断） | mode 单元在 `## Routes` 加一句兜底：「某个已安装技能的 description 认领的任务，交给那个技能；本表只列会改变去处或带门槛的行」。然后在 R4 T1 的六个提示里加一个「出包」提示，看会话是否直接进 `exe-release` |
| U-R9-2 | W-SSR-20 把「另一个技能按名调用」也算进开关推导 | R4 D1.3 原文只数 `## Routes`、playbook、角色操作文件、启动提示词。今天被能力技能调用的 `diagram-design`、`writing-for-agents` 都是模型可触发，推导结果不变；这条扩展只防将来上游把它们改成用户触发时调用方断链（Claude Code 上用户触发的技能对模型不可见，R4 V1）。「读它的 `SKILL.md` 并照做」在别的宿主上是否也需要模型可触发，没有核实 | lint 单元确认 `check_wiring.py` 第 3 类的扫描范围包括能力技能正文；R4 T4 的实测顺带验证 `wait-what` → `diagram-design` |
| U-R9-3 | SSR 第 8 行（W2）在消费仓库里到底有没有被用到 | 只在本仓库的 Claude Code 会话里能查；Codex、Grok、Pi、Cursor 的会话记录和其他仓库都没查 | 在各宿主会话记录里搜在本仓库之外打开 `SKILL-SET-RULES.md` 的记录。结果只影响对 W2 价值的判断，不改变「不动」：删掉它的收益（上游原文）小于风险 |
| U-R9-4 | SSR 增长约 40 行后，写能力技能的人多读的量是否值得拆出一个分支文件 | SSR 事实 5 按分支会建议拆（mode、playbook、原则的格式只有写这三类的人需要）；用户要求 2 不承认「减少读量」这种收益，所以本文不拆。同理 `driving.md`、`git-hooks.md` 不内联 | R4 T8 的走查量出写一个能力技能时 SSR 被读了多少、用了多少；若 owner 愿意把「读量」加进收益清单，再按分支拆 |
| U-R9-5 | `diagram-design` 超出 40,000 字节会不会让上游 `verify-semantic-motion.py` 失败，以及压回上限要删哪些本仓句子 | 只量了字节数，没有在隔离检出里跑上游脚本 | 在临时检出跑 `python3 mmw-v2/upstream-diagram-design/scripts/verify-semantic-motion.py`；随第 5 节 F5 的票一起做 |
| U-R9-6 | 词表新条目 **mode** 与现有用法的关系 | `wayfinder` 的「Two modes」按上游含义使用（SSR `### Vocabulary` 允许），`permission mode` 是复合词，本仓 `AGENTS.md` 说 `install.sh` 有「two modes」。建议技能文本一律写「the `mmw` skill」，`mode` 只出现在 SSR 与词表 | 词表单元按 SSR `### Vocabulary` 并排检查后定；若判为一词多义，改用「router」并在 `_Avoid_` 行注明上游 `SKILL-MECHANICS.md` 的不同含义 |

