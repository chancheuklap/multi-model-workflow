# setup-matt-pocock-skills

源目录：`mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/`

这个技能只跑一次，写出三份配置文件。它在本仓的落地件是 `docs/agents/` 下与三份种子同名的文件：

| 种子 | 本仓的落地件 |
| --- | --- |
| `issue-tracker-github.md` | `docs/agents/issue-tracker.md` |
| `domain.md` | `docs/agents/domain.md` |
| `triage-labels.md` | `docs/agents/triage-labels.md` |

**重跑这个技能之前先备份 `docs/agents/triage-labels.md` 与 `docs/agents/domain.md`。** 前者的 `## What carries a label here` 一节是本仓自己加的（哪个 label 代表哪个 queue、spec 不带 label、本仓自建 ticket 不带 category），种子里没有这一节，重跑会把它盖掉；后者已经按本仓真实布局重写，并且带着本仓自己的几条规则，重跑会把它整份还原成种子。`docs/agents/issue-tracker.md` 与种子差得最少，改动逐条记在下面。根 `AGENTS.md` 也不归这个技能管，理由同在下面 SKILL.md 一节。

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留。这是四个例外之一（另三个是 `grill-me`、`handoff`、`wait-what`）：它一个仓库只跑一次、会覆盖 `docs/agents/` 下三份文件，不该由模型自己认出来触发。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 3 步 Confirm and edit 的第一条草稿项 | 从「whichever of `CLAUDE.md` / `AGENTS.md` is being edited」改成固定的 `AGENTS.md`，跟第 4 步同步 |
| 第 4 步 Pick the file to edit（`CLAUDE.md` 在就改它、两个都没有就问用户、绝不在另一个已存在时新建） | 改成：要写只写 `AGENTS.md`，没有就建；`CLAUDE.md` 只放 `@AGENTS.md` 一行加它原有的其他 `@` 行，别的内容搬进 `AGENTS.md`。理由是本仓另一个技能 `manage-agents-md` 就是这个形态（它的 `references/write.md` 里 `CLAUDE.md` 只放「the line `@AGENTS.md` … Nothing else.」那一条），它的 `scripts/check.sh` 会把 `CLAUDE.md` 里每一行非 `@import` 判成错——照上游的规则跑完 setup，再跑 `manage-agents-md` 就是两个技能互相拆台。上游改这一步 → 不收，除非它自己也变成只写 `AGENTS.md` |
| 第 3、4 步要种进 `AGENTS.md` 的 `## Agent skills` 块（三个 `###` 子节各指一份 `docs/agents/` 文件） | 弃上游。根 `AGENTS.md` 的形状归 `manage-agents-md` 管，那份格式里没有 `## Agent skills` 这一节：三份配置各是 `## External References` 表里的一行，指向 `docs/agents/issue-tracker.md`、`docs/agents/triage-labels.md`、`docs/agents/domain.md`。`docs/adr/0005-docs-layer-adopted-by-v2.md` 当年把这个块落进根 `AGENTS.md`，那是历史，2026-09-12 重写根 `AGENTS.md` 之后它不在了。**重跑这个技能时不要让它把这个块重新种回去，也不要让第 4 步的写盘覆盖 `docs/agents/` 下任何一份落地件**：种回去的块会被下一次 `manage-agents-md` 当成格式外的一节。上游改这个块的内容 → 不收 |
| frontmatter 的 `description` | 值外面那对引号保留。这个值里有「冒号加空格」（`for the engineering skills: set up its issue tracker`），去掉引号 YAML 会把它当成一个 mapping 并报 `mapping values are not allowed here`，整份 frontmatter 解析失败，host 启动时读不到这份技能的描述。上游改这一行的内容 → 收上游，引号跟着值走：值里只要还有冒号加空格就必须带引号 |

### issue-tracker-github.md（种子）

| 段落 | 我们的意图 |
| --- | --- |
| Conventions 开头新增的 **Every list read is a whole list** | 本仓加的，种子里没有。`gh issue list` 不带 `-L` 停在 30 条，`gh api` 的列表端点不带 `--paginate` 只回第一页，两者都不在输出里留任何标记，所以读了一半的集合看起来和完整的一模一样。agent 照这份文件写命令，看不见的票它当作不存在。上游若自己加了同义的一条 → 收上游措辞；上游改这一段 → 保留本仓这条，它是行为要求不是文风 |
| **List issues**、**Frontier query**、两条 Morning queries 的命令 | 一律补 `--limit 500`。上游改这几条命令 → 收上游的其余部分，`--limit` 必须留着 |
| **Child ticket** 里读子票的命令 | 从 `gh api` on the sub-issues endpoint 写成完整的 `gh api --paginate repos/<owner>/<repo>/issues/<map>/sub_issues?per_page=100`。理由同上：2026-09-06 在 agentflow 上，spec #537 有 37 个子票，不分页只看得到 30 个，7 张票在读的人眼里不存在 |
| `## Pull requests as a triage surface` 的 `**PRs as a request surface: no.**` 一句括号里，与 `## Wayfinding operations` 的 `Used by …` 一句 | host 中立：两处技能点名写成散文形式。共同理由见 [README.md](README.md#host-中立) |

### triage-labels.md（种子）

| 段落 | 我们的意图 |
| --- | --- |
| 表格下面那句举例「apply the AFK-ready triage label」 | 例子换成 `ready-for-agent`。这句教读者「技能提到 triage role → 来这张表取本仓真实的 label」，而 `AFK-ready` 在表里没有对应行，全仓也没有一个技能这么写——`triage/SKILL.md` 从头到尾直接写 `ready-for-agent`。上游改这句 → 收上游措辞，例子必须用表里真有的 label |

### domain.md（种子）

这份落地件不再是种子的近似副本：布局那两段与规则那一节由本仓手工维护。上游改通用文字 → 收上游措辞；下表这几段 → 弃上游，本仓的留着。

| 段落 | 我们的意图 |
| --- | --- |
| `## Before exploring, read these` 里 `If any of these files don't exist` 那一句，与 `## Use the glossary's vocabulary` 的末句 | host 中立：三处技能点名写成散文形式。共同理由见 [README.md](README.md#host-中立) |
| `## Before exploring, read these` 的第二、三条，与 `## File structure` 里本仓那棵树加它下面那段理由 | 弃上游。种子的 multi-context 示例树把每个 context 的 `CONTEXT.md` 放进 `src/<context>/`、ADR 按 context 分目录；本仓不是这个形状：一份根 `CONTEXT-MAP.md` 加六份 `docs/contexts/<名>/CONTEXT.md`（toolbox、tickets、ticket-run、night、ui-acceptance、task-board），ADR 全部 system-wide 待在 `docs/adr/`，没有 context 级的 ADR 目录。理由写在树下面那一段：多数 context 的代码就是一个技能目录，而技能目录被整个软链进每个 host、只装拿着这份技能的 agent 要读要跑的东西，`CONTEXT.md` 摆在代码边上就会跟着技能发到每个 host。通用的 single-context 树与 multi-context 的解释保留，上游改它们 → 收上游措辞，本仓这棵树与这段理由不动 |
| `## Use the vocabulary in CONTEXT.md` 整节（标题、`_Avoid_` 一句、`_Home_` 冲突一句、「说得比 `_Home_` 少不是缺陷，说得多才是」一段、系统性更新一句） | 弃上游。种子这一节叫 `## Use the glossary's vocabulary`，只有两段（概念命名、缺词是信号）；`_Home_`、`_Avoid_`、一条条目该说多少，是本仓 `CONTEXT.md` 自己的读法（见任一份 `docs/contexts/<名>/CONTEXT.md` 开头的「How to read an entry」），种子里没有。系统性更新那一句说的是同一条规则怎么逐条用：打开每条的 `_Home_`、照那份文件现在写的重写这条，`_Home_` 不再定义它就挪到真定义它的文件或删掉。上游改那两段通用文字 → 收上游措辞，本仓这几条留着 |

### issue-tracker-gitlab.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Merge requests as a triage surface` 的 `**MRs as a request surface: no.**` 一句括号里，与 `## Wayfinding operations` 的 `Used by …` 一句 | host 中立：两处技能点名写成散文形式。同一节 **Blocking** 一条里的 `/blocked_by #<n>` 与 `"/blocked_by #<blocker>"` 没动：那是 GitLab 自己的 quick action，是一条真要打出去的命令，不是技能名。共同理由见 [README.md](README.md#host-中立) |

### issue-tracker-local.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Wayfinding operations` 的 `Used by …` 一句 | host 中立：技能点名写成散文形式。共同理由见 [README.md](README.md#host-中立) |
