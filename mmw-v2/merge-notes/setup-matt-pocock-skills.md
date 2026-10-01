# setup-matt-pocock-skills

源目录：`mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/`

这个技能只跑一次，写出三份配置文件。它在本仓的落地件是 `docs/agents/` 下与三份种子同名的文件：

| 种子 | 本仓的落地件 |
| --- | --- |
| `issue-tracker-github.md` | `docs/agents/issue-tracker.md` |
| `domain.md` | `docs/agents/domain.md` |
| `triage-labels.md` | `docs/agents/triage-labels.md` |

`docs/agents/triage-labels.md` 与 `docs/agents/domain.md` 带着本仓自己写的内容：前者表格的 Meaning 一列是本仓改写的（`ready-for-human` 写成 `reaction` / `reach` 两类，「the user」代替 maintainer 与 reporter），种子也有这张表；哪个 label 代表哪个 queue、spec 不带 label、本仓自建 ticket 不带 category，这些不写在这份文件里，由用到它的技能自己说（`triage` 的 `## Roles`、`to-spec` 第 4 步、`to-tickets` 第 7 步）；后者已经按本仓真实布局重写，并且带着本仓自己的几条规则，写在种子也有的那几节里。2026-09-28 lightweight review 之前，重跑这个技能会把这些节按种子重写；现在 `SKILL.md` 第 4 步已改为「落地件是本仓自己的记录，只改这次答案会改的、补种子有而文件缺的，其余每一行原样留着」，所以不必再手工备份这两份文件（原先这一段的警告随之删掉）。`docs/agents/issue-tracker.md` 与种子差得最少：种子本身的改动逐条记在下面，`## Three label sets` 一节与带 `mmw:map`、`mmw:spec` 的 **Map**、**Frontier query** 两行来自 `mmw` 技能的 `references/issue-tracker-pipeline-sections.md`；它另有种子没有的 `## Morning queries` 一节，两条命令同样带 `--limit 500`。根 `AGENTS.md` 里这个技能只写 `## External References` 表的行，见下面 SKILL.md 一节。

这个技能只留下面逐条记的能力改动。流水线对 tracker 的要求不写进这个技能：tracker 选 GitHub Issues、label 保留默认，以及「这里写的文件在每次发布、分诊时被照做」那一段，在 `mmw` 技能 **Onboard a repository** 的开头段与 **Set up the tracker** 一步；`## Three label sets` 一节与带 `mmw:map`、`mmw:spec` 的 **Map**、**Frontier query** 两行，在 `mmw` 技能的 `references/issue-tracker-pipeline-sections.md`，由那一步写进仓库的 `docs/agents/issue-tracker.md`。上游改到这几处附近 → 取上游，流水线的文字不接回这个技能。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留。这是 [README.md](README.md#disable-model-invocation) 列出的例外之一：它一个仓库只跑一次、会覆盖 `docs/agents/` 下三份文件，不该由模型自己认出来触发。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| Section C「Offer multi-context…Then confirm which layout they want.」那句之后（不改上游原文） | 我们加的一句：已经有 `CONTEXT-MAP.md` 的仓库就按 multi-context 处理，不论是不是 monorepo，照它现有的布局描述。理由：上游只在看到 monorepo 信号时才给多 context 布局；本仓和 `agentflow` 都有 `CONTEXT-MAP.md`，却都没有 `pnpm-workspace.yaml`、`package.json` 的 `workspaces` 字段或 `packages/*`（`ls` 核实过），照字面重跑会写出与实际布局相反的 `domain.md`。上游改这一段 → 收上游措辞，这一句仍接在后面 |
| 第 4 步「Add one row per written `docs/agents/` file…」那句中段 | 我们加的：另一种形状的指针（`## Agent skills` 块、`## Issue tracker` 一节）算作那份文件的那一行，替换它而不是再加一个指针。理由：`agentflow`、`xiaohuangya`、`mmw-e2e-lab` 用的都是旧格式的指针块，重跑时字面读会把旧块当成「user edits to the surrounding sections」原样留着，再加一组新行，同一份文件被指了两次（推断，还没有重跑的记录）。上游改这一句 → 收上游措辞，这一句接回去 |
| 第 4 步 Pick the file to edit（`CLAUDE.md` 在就改它、两个都没有就问用户、绝不在另一个已存在时新建） | 改成：要写只写 `AGENTS.md`，没有就建；`CLAUDE.md` 只放 `@AGENTS.md` 一行加它原有的其他 `@` 行，别的内容搬进 `AGENTS.md`。理由是本仓另一个技能 `manage-agents-md` 就是这个形态（它的 `SKILL.md` `## Write` 里 `CLAUDE.md` 只放「the line `@AGENTS.md` … Nothing else.」那一条），它的 `scripts/check.sh` 会把 `CLAUDE.md` 里每一行非 `@import` 判成错——照上游的规则跑完 setup，再跑 `manage-agents-md` 就是两个技能互相拆台。上游改这一步 → 不收，除非它自己也变成只写 `AGENTS.md` |
| 第 1 步探查 `AGENTS.md` 的那一条、第 3 步的第一条草稿项、第 4 步开头一段（上游的 `## Agent skills` 块） | 弃上游的块。根 `AGENTS.md` 的形状归 `manage-agents-md` 管（它的 `SKILL.md` `## Write`：根文件只有那几节），那份格式里没有 `## Agent skills` 这一节，文档一律是 `## External References` 表（`Need`、`File` 两列）的一行。所以三处都改成这张表：第 1 步看 `AGENTS.md` 是否已有指向 `docs/agents/` 的行；第 3 步给 user 看的草稿是要加的行，每份写出的 `docs/agents/` 文件一行；第 4 步每份写出的文件加一行，文件或这一节不存在就建，已有指向同一文件的行就更新、不重复加；`docs/agents/triage-labels.md` 与它那一行只在 `triage` 已安装且 Section B 跑过时写。上游那句「Don't overwrite user edits to the surrounding sections」原样留着。上游改这个块的内容 → 不收，仍写 `## External References` 的行 |
| 第 4 步「Then write the docs files using the seed templates」那一句的后半句 | 2026-09-28 lightweight review 改写：原来只说「就地更新，保留种子没有的节」，字面读下来种子也有的那几节会被种子重写——落地件恰恰在这些节里写了本仓自己的规则（`triage-labels.md` 的 Meaning 列，`domain.md` 的 `## Before exploring, read these`、`## File structure`、`## Use the vocabulary in CONTEXT.md`）。现在写成：落地件是本仓自己的记录，种子只是它的起点；这次答案改的就改，种子有而文件缺的就补，其余每一行原样留着；种子的其它差异报给用户，不自己去消。理由：Nowledge Mem 一条记忆（`610dbea8`，2026-09-01）记着重跑这个技能之前要先备份，因为字面读旧文字会把落地件按种子重写；补上这句之后备份不再必要。落地件会长出种子没有的节（本仓 `docs/agents/issue-tracker.md` 的 `## Reading a tree` 与 `## Morning queries`）也在「补种子有而文件缺的」这条规则内被保留。上游改这一句 → 收上游措辞，这一段接回去 |

### issue-tracker-github.md（种子）

| 段落 | 我们的意图 |
| --- | --- |
| Conventions 开头新增的 **Every list read is a whole list** | 本仓加的，种子里没有。`gh issue list` 不带 `-L` 停在 30 条，`gh api` 的列表端点不带 `--paginate` 只回第一页，两者都不在输出里留任何标记，所以读了一半的集合看起来和完整的一模一样。agent 照这份文件写命令，看不见的票它当作不存在。正文只留这两个事实与命令要求，不加修辞句。上游若自己加了同义的一条 → 收上游措辞；上游改这一段 → 保留本仓这条，它是行为要求不是文风 |
| **List issues**、**Frontier query** 的命令 | 一律补 `--limit 500`。上游改这几条命令 → 收上游的其余部分，`--limit` 必须留着 |
| **Child ticket** 里读子票的命令 | 从 `gh api` on the sub-issues endpoint 写成完整的 `gh api --paginate repos/<owner>/<repo>/issues/<map>/sub_issues?per_page=100`。理由同上：2026-09-06 在 agentflow 上，spec #537 有 37 个子票，不分页只看得到 30 个，7 张票在读的人眼里不存在 |
| `## Wayfinding operations` 的 **Map** 一条 | 本仓改的：正文写成「holding the map body the `wayfinder` skill writes」，代替上游的「holding the Notes / Decisions-so-far / Fog body」。理由：map 正文的几节只在 `wayfinder` 技能的 `### The map body` 一处定义，上游那里已是 Destination、Notes、Decisions so far、Not yet specified、Out of scope 五节，种子照列节名就会随它过期。上游改这一条 → 收上游其余措辞，「指向 `wayfinder` 写的正文」保留 |

### triage-labels.md（种子）

| 段落 | 我们的意图 |
| --- | --- |
| 表格下面那句举例「apply the AFK-ready triage label」 | 例子换成 `ready-for-agent`。这句教读者「技能提到 triage role → 来这张表取本仓真实的 label」，而 `AFK-ready` 在表里没有对应行，全仓也没有一个技能这么写——`triage/SKILL.md` 从头到尾直接写 `ready-for-agent`。上游改这句 → 收上游措辞，例子必须用表里真有的 label |

### domain.md（种子）

这份落地件不再是种子的近似副本：布局那两段与规则那一节由本仓手工维护。上游改通用文字 → 收上游措辞；下表这几段 → 弃上游，本仓的留着。

| 段落 | 我们的意图 |
| --- | --- |
| `## Before exploring, read these` 的第二、三条，与 `## File structure` 里本仓那棵树加它下面那段理由 | 弃上游。种子的 multi-context 示例树把每个 context 的 `CONTEXT.md` 放进 `src/<context>/`、ADR 按 context 分目录；本仓不是这个形状：一份根 `CONTEXT-MAP.md` 加六份 `docs/contexts/<名>/CONTEXT.md`（toolbox、tickets、ticket-run、night、ui-acceptance、task-board），ADR 全部 system-wide 待在 `docs/adr/`，没有 context 级的 ADR 目录。理由写在树下面那一段：多数 context 的代码就是一个技能目录，而技能目录被整个软链进每个 host、只装拿着这份技能的 agent 要读要跑的东西，`CONTEXT.md` 摆在代码边上就会跟着技能发到每个 host。通用的 single-context 树与 multi-context 的解释保留，上游改它们 → 收上游措辞，本仓这棵树与这段理由不动 |
| `## Flag ADR conflicts` 开头那一句（本仓的 ADR 照 `docs/adr/README.md` `## 一份 ADR 长什么样` 写，不照 `domain-modeling` 技能的 `ADR-FORMAT.md`） | 本仓加的，种子里没有。`domain-modeling` 的 `SKILL.md` 把写 ADR 的人指到上游模板，本仓的形状不同（见 [domain-modeling.md](domain-modeling.md)）；这一句是上游正文之外的连接。上游改这一节 → 收上游措辞，这一句留着 |
| `## Use the vocabulary in CONTEXT.md` 整节（标题、`_Avoid_` 一句、`_Home_` 冲突一句、「说得比 `_Home_` 少不是缺陷，说得多才是」一段、系统性更新一句） | 弃上游。种子这一节叫 `## Use the glossary's vocabulary`，只有两段（概念命名、缺词是信号）；`_Home_`、`_Avoid_`、一条条目该说多少，是本仓 `CONTEXT.md` 自己的读法（见任一份 `docs/contexts/<名>/CONTEXT.md` 开头的「How to read an entry」），种子里没有。系统性更新那一句说的是同一条规则怎么逐条用：打开每条的 `_Home_`、照那份文件现在写的重写这条，`_Home_` 不再定义它就挪到真定义它的文件或删掉。上游改那两段通用文字 → 收上游措辞，本仓这几条留着 |
