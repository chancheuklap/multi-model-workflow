# N4 清点：to-spec + to-tickets + triage

本报告只做事实清点，不做归置决定。单元：`mmw-v2/upstream/skills/engineering/to-spec/`、`to-tickets/`、`triage/` 全部文件；三份 merge-note；上游原文（squash 提交 `5b1a4c513d027a598a277aa45892a6823381f9a9`，`Squashed 'mmw-v2/upstream/' changes from 6654f6b6..c55ee460`，2026-09-18）；`docs/agents/issue-tracker.md`、`triage-labels.md`、`domain.md`；`docs/contexts/tickets/CONTEXT.md`。

## 0. 读了什么、怎么读的

- 完整读过：单元内全部 15 个文件（见第 1 节）；`mmw-v2/merge-notes/README.md`、`to-spec.md`、`to-tickets.md`（65 KB，分三段读完）、`triage.md`；三份 `docs/agents/*.md`；`docs/contexts/tickets/CONTEXT.md`；上游 8 个原文件（`git show 5b1a4c51:skills/engineering/<skill>/<file>`）；`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SKILL-SET-RULES）；`mmw-v2/skills/verify-ticket/references/linting.md`、`verify-ticket/SKILL.md`。
- 部分读过（只取一个事实）：`mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` 的 `--help` 全文、`run_publish_drafts`（第 3992 行起）的 docstring 与前 40 行、`lint_undecidable_checks` docstring、`CLASS_LABELS`/`QUEUE_LABELS`/`GRADE_LABELS` 位置；`events.py --help`；`dispatch.sh` 第 4440–4470 行 `route` 的注释；`implement/SKILL.md` 第 16、22 行；`code-review/references/spec-reviewer.md` 第 11、18 行；`dispatch/references/night.md` 第 83–102、139–145 行；`wayfinder/SKILL.md` 第 126 行；`write-screen-contract/SKILL.md` 第 115–120 行；ADR 0001、0005、0011、0012、0015、0019、0023、0027、0029 的开头段与 grep 命中行。
- 只读命令：`gh issue list/view`、`gh api .../contents` 对本仓与 `agentflow-hq/agentflow` 的计数（第 6 节引用），`git log`/`git show`/`git diff --stat`。没有运行任何改状态的命令。
- 本单元**没有自己的脚本**。它调用的脚本（`verify-ticket.py`、`events.py`、`dispatch.sh route`、`issue_tree.py`）属于别的单元，这里只记它们的接口。

线索材料的采用与核实记录在第 10 节。

---

## 1. 部件清单

| 文件 | 行 / 词 | 是什么、给谁用 |
| --- | --- | --- |
| `to-spec/SKILL.md` | 127 行 / 2509 词 | 把对话、wayfinder map 或已分诊 issue 写成一份 spec 并发布成 `mmw:spec` issue 的技能正文；读者是白天与用户同在的 session（也可能是 triage session 走 `ready-for-agent` 出口时）。含 `<spec-template>`。 |
| `to-spec/references/revising-a-spec.md` | 11 行 / 282 词 | 已发布 spec 的某一节要改时的做法；读者是被 `to-tickets`、`triage`、`write-screen-contract`、`dispatch` 的 `references/night.md`（`contract` child）送回来的 agent。 |
| `to-spec/references/several-specs.md` | 5 行 / 275 词 | 一个来源要切成几份 spec（**spec division**）时的做法；只在第 1 步判出「几份」或来源已带划分时读。 |
| `to-spec/agents/openai.yaml` | 3 行 | Codex 读的技能清单（显示名、短描述）；MMW 删掉了上游的 `policy` 块。 |
| `to-tickets/SKILL.md` | 206 行 / 3750 词 | 把已发布 spec 切成一批 tracer-bullet ticket 并发布为 spec 的 sub-issue 的技能正文；读者是白天切票的 session；夜里 orchestrator 写票时读其中 `<issue-template>` 与第 4 步（`night.md` 第 141 行）；triage 走 `became-ticket` 时读 `<issue-template>`（`pipeline-issues.md` 表第二行）。 |
| `to-tickets/references/ambiguity-scan.md` | 83 行 / 498 词 | 给一个只读 subagent 的找漏清单与输出格式；每次切票的第 6 步都跑（host 不能起 subagent 时切票 agent 自己读）。 |
| `to-tickets/references/cutting-interface-tickets.md` | 152 行 / 2339 词 | spec 有 screen contract 时怎么切五种界面票、每种判据的 `CHECK:`/`EXPECT:` 形状；只在界面批次读。`ui-acceptance/SKILL.md` 第 20 行与 SKILL-SET-RULES 第 117 行也指向其 **Criterion shapes**。 |
| `to-tickets/references/person-ticket.md` | 14 行 / 415 词 | `ready-for-human` 票（`reaction`/`reach`）的定义与 **the five things**；读者是切票 agent（第 4 问第 3、4 支、第 8 步）与 triage agent（第 5 步 `ready-for-human`）。 |
| `to-tickets/agents/openai.yaml` | 3 行 | 同上，Codex 清单。 |
| `triage/SKILL.md` | 116 行 / 1228 词 | 把 issue 与外部 PR 过一遍 triage 角色状态机；读者是早上跑 `needs-triage` 队列的用户 session（`docs/agents/issue-tracker.md` `## Morning queries`）。 |
| `triage/references/pipeline-issues.md` | 29 行 / 794 词 | 本仓流水线自己产出的 issue（`mmw:child`、`mmw:ticket`、`Retro #<spec>:` 提案）怎么判、送到哪；带 `mmw:*` label 或 retro 标题时先读。 |
| `triage/AGENT-BRIEF.md` | 209 行 / 1339 词 | agent brief（调查记录评论）的原则、模板、好坏例子；只在外来 issue 判 `ready-for-agent` 时读。 |
| `triage/OUT-OF-SCOPE.md` | 105 行 / 714 词 | `.out-of-scope/` 知识库的格式与读写时机；外来 issue 第 1 步查重、`wontfix`（被拒 enhancement）时读。与上游逐字相同。 |
| `triage/agents/openai.yaml` | 3 行 | 同上，Codex 清单。 |
| `docs/agents/issue-tracker.md` | 91 行 | 本仓 tracker 的 `gh` 操作、三套 label、PR 开关、wayfinder 操作、早上两条查询；读者是 to-spec/to-tickets/triage/wayfinder 等技能的 agent（经根 `AGENTS.md` `## External References` 表），`setup-matt-pocock-skills` 写出它。 |
| `docs/agents/triage-labels.md` | 15 行 | 五个 triage 角色到本仓 label 字符串的映射；triage 与 to-tickets 的 label 来源（merge-note README `## host 中立` 末段）。 |
| `docs/agents/domain.md` | 65 行 | 探索代码前读 `CONTEXT-MAP.md`、`docs/contexts/*/CONTEXT.md`、`docs/adr/` 的约定与 `_Home_` 纪律；读者是各 engineering 技能 agent。 |
| `docs/contexts/tickets/CONTEXT.md` | 364 行 | Tickets 上下文的词表（spec、ticket、判据、label、队列、publish、lint 等 70 余词条），每条有 `_Home_`；读者是维护者与按 `domain.md` 读词表的 agent。 |
| `mmw-v2/merge-notes/to-spec.md` / `to-tickets.md` / `triage.md` | 51 / 182 / 36 行 | 各段相对上游的意图、理由、拉上游时的取舍；读者是拉 subtree 的维护者，不是运行时 agent。 |

---

## 2. 内容分类表

类型缩写：**顺序**、**做法**、**规则**（带理由的规则）、**接口**（命令与接口）、**分派**（重入与分派）、**格式**（格式与模板）、**立场**（目的与立场）、**沉积**。「Done when」行记作 顺序（完成判据）。「谁·何时·频率」一栏：每次 = 该技能每次运行都读到；分支 = 只有某条分支读。

### 2.1 `to-spec/SKILL.md`

| 段（行） | 类型 | 谁·何时·频率 | 备注 |
| --- | --- | --- | --- |
| frontmatter `description`（3） | 分派（触发） | 每个 host 启动时扫；每次 | 四支触发各对应一个入口（merge-note to-spec 第 11 行）。带引号的理由只在 merge-note。 |
| 开头段（6）前两句 | 立场 | to-spec agent；每次 | 上游句「Do NOT interview the user for facts」（上游原文无 `for facts`）。 |
| 开头段（6）其余 | 立场 + 规则 | 同上；每次 | 「A spec is the last text a person checks before agents build from it unattended…」；工程判断自己定并标 "this spec's decision"，产品/钱/范围问用户。 |
| setup 指针（8） | 接口 | 每次 | 硬依赖一行，指 `setup-matt-pocock-skills`。 |
| 第 1 步首句（12） | 分派 + 做法 | 每次 | 引用是 issue/URL/文件先读全；是已发布 spec 的一节要改 → `references/revising-a-spec.md`；是 map → 读 **Decisions so far**、每张 resolution comment、prototype/research 结论，`Out of scope` 原样带入。 |
| 第 1 步第二段（14） | 规则 | 每次 | spec division 判据：同一 **seam** 归一份；可分阶段、依赖单向不成环。 |
| 第 1 步第三段（16） | 分派 | 每次 | 一份就写；几份或已有划分 → `references/several-specs.md`。 |
| 第 1 步 Done（18） | 顺序 | 每次 | |
| 第 2 步首段（20） | 做法 | 每次 | 上游原文。 |
| 第 2 步第二段（22） | 规则 + 分派 | 分支：有 UI 的 effort | 读全 screen contract；`gap` 非 `aligned` 就停；有 map 退回 alignment ticket，无 map 退回 `write-screen-contract` 的 **Reverse sweep** → **Write the gap list and stop for the user**；无合同行的决定写 "this spec's decision"。 |
| 第 2 步 Done（24） | 顺序 | 每次（后半只在 UI 分支） | |
| 第 3 步首段（26） | 做法 + 接口 | 每次 | 上游五句 seam 原则 + 末句 `TESTING.md`（MMW）。 |
| 第 3 步「A seam says where a test observes」（28） | 规则 | 每次（UI 例子只在 UI 分支适用） | 观察与到达是两件事。 |
| 第 3 步「The seam is yours to decide」（30） | 规则 | 每次 | 不问用户确认 seam（上游原文要问）。 |
| 第 3 步 Done（32） | 顺序 | 每次 | |
| 第 4 步（34） | 接口 + 规则 | 每次 | `verify-ticket` 的 `--publish --spec-body <file> --title <t> [--map <map>]`；不打 triage label 的理由（spec 是容器）。 |
| 第 4 步 Done（36） | 顺序 | 每次 | 「Done when `--publish` exits 0.」 |
| `<spec-template>` Problem / Solution / User Stories（40–58） | 格式 | 每次 | 上游原文。 |
| Implementation Decisions 首段与清单（60–70） | 格式 | 每次 | 小节编号 `### 1.`（MMW）。 |
| 「Each subsection is read on its own」（72） | 规则 | 每次 | worker 只读票点名的小节。 |
| 「Every decision names where it came from」（74） | 规则 + 格式 | 每次 | 含 `CODING_STANDARDS.md` 规则写进小节。 |
| 「A user story's conclusion is folded…」（76） | 规则 | 每次 | |
| **API contract**（78）、**cross-component composition**（80）、**visual acceptance**（82） | 格式 + 规则 | 分支：有 screen contract | |
| 路径禁令（84） | 规则 | 每次 | 上游改窄：只禁实现路径，来源路径要写。 |
| prototype snippet 例外（86） | 规则 | 每次 | 上游原文。 |
| Testing Decisions 首段（90） | 格式 | 每次 | 大白话首句、seam 句。 |
| 「what makes a good test」「test layers … precedent」（92–93） | 格式 + 做法 | 每次 | 前者上游，后者 MMW。 |
| **How a test arrives at a state**（94） | 规则 + 接口 | 每次（后半只在 UI 分支） | 三个到达机制；`target_config.py --check`。 |
| **Critical flows**（95） | 格式 + 接口 | 分支：有 screen contract | 行形状 ``- `<flow>`: Implementation Decisions sections <n>, <n>``，`--lint` 读；`none` 与省略条件。 |
| 提交前命令（96） | 格式 | 每次 | 上游无。 |
| Out of Scope（98–100） | 格式 | 每次 | 上游原文。 |
| Sources（102–117） | 格式 | 每次 | 十二类，无则 `none`。 |
| Further Notes（119–121） | 格式 + 分派 | 每次（划分行只在非 map 多份时） | |
| `## Next`（125–127） | 分派 | 每次 | 指 `to-tickets`。 |

### 2.2 `to-spec/references/revising-a-spec.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 第 3 行 | 做法 + 规则 + 接口 | 分支：修订已发布 spec。读者：to-spec（用户要改）、to-tickets 第 4 步第 2 问与第 6 步、triage 第 5 步、`write-screen-contract` **Re-runs**、`night.md` `contract` child 的 orchestrator | 就地改不新发（新号会让 `## Parent` 指错）；`gh issue edit <n> --body-file`；改动理由进一条评论；未落地票对齐、已落地票出更正票；「只由 orchestrator 或用户在场的 session 编辑」。 |
| 第 5 行 | 做法 | 同上 | 前提消失的 criterion 移出、编号不复用、留评论。 |
| `## When the rows change`（7–9） | 做法 | 分支中的分支：`pull-report.md` 记 `增删控件或改流转` | 新行在拥有它的票上加一条 boundary criterion。 |
| Done（11） | 顺序 | 同上 | |

### 2.3 `to-spec/references/several-specs.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 第 3 行 | 顺序 + 格式 + 分派 | 分支：来源是 map 且判出几份 | 列名、问用户、写回 map `## Specs`、只写第一份、发布回填、停；已有 `## Specs` 跳过判断。 |
| 第 5 行 | 分派 + 格式 | 分支：来源不是 map | 划分写进第一份 spec 的 `## Further Notes`；再次运行时写下一份无链接的、经 `revising-a-spec.md` 回填；全部有链接即停。 |

### 2.4 `to-tickets/SKILL.md`

| 段（行） | 类型 | 谁·何时·频率 | 备注 |
| --- | --- | --- | --- |
| frontmatter（3） | 分派（触发） | host 启动 | |
| 定义句（8） | 立场 | 每次 | 上游原文。 |
| 「Each ticket is read by agents who were not in this conversation…」（10） | 立场 | 每次 | 2026-09-28 加。 |
| setup 指针（12） | 接口 | 每次 | |
| `### 1. Gather context`（16–22） | 做法 + 分派 + 顺序 | 每次 | 无已发布 spec → 先走 `to-spec`。 |
| `### 2. Explore the codebase`（24–30） | 做法 + 顺序 | 每次 | 上游有 `(optional)`，MMW 去掉。 |
| `<vertical-slice-rules>`（36–42） | 规则 | 每次 | 删了上游「single fresh context window」一条。 |
| 「Split where the parts can run at the same time…」（44） | 规则 | 每次 | 2026-09-28 加。 |
| 界面指针（46） | 分派 | 分支：spec 有 screen contract | → `references/cutting-interface-tickets.md`。 |
| Wide refactors（48） | 做法 + 规则 | 分支：宽重构 | 上游原文（从上游第 3 步末移到本位）。 |
| 第 3 步 Done（50） | 顺序 | 每次 | |
| 三条措辞规则（54–58） | 规则 | 每次 | |
| 「A criterion is decided by a command…」+ the five questions（60–68） | 立场 + 规则 + 分派 | 每次 | 五问是「停在第一个 yes」的分派表：判据 / code review / `reaction` / `reach` / 用户取舍。第 3、4 支 → `references/person-ticket.md`。 |
| 「If no command exists … return to the `to-spec` skill」（70） | 分派 | 分支 | |
| 四行形态与示例（72–79） | 格式 + 接口 | 每次 | `AC<n>`/`CHECK:`/`EXPECT:`/`EVIDENCE: pending`。 |
| `CHECK:`/`EXPECT:` 从哪来（81–84） | 做法 | 每次 | 从 Testing Decisions 的 layer/目录/precedent 推；`EXPECT:` 是 **success-only marker**。 |
| `CHECK:` 取对象（86） | 规则 + 接口 | 每次 | `$MMW_TICKET`、`issue-<n>`、`gh api …/sub_issues`；不许搜索取第一个。 |
| `CHECK:` 自带状态并还原（88） | 规则 | 每次 | 独立 shell、cwd 为仓库根、`--reverify` 再跑一遍。 |
| 「A criterion is also exposed to the rest of its own batch」（90） | 规则 | 每次 | 全仓扫描或点名会被改名之物 → 放末票或唯一 Owns。 |
| 第 4 步 Done（92） | 顺序 | 每次 | |
| 第 5 步首段（96） | 规则 | 每次 | 「The edges are the night's schedule」（2026-09-28 加）。 |
| 「put in service」段（98） | 做法 + 规则 | 每次 | 对每个 `(new)` 路径按文件名、按对外标识各 `grep` 一次。 |
| 两支（100–105） | 分派 + 做法 | 每次 | 两票 → Blocked by；多票共用登记文件 → prefactor ticket；一整段逻辑的共用文件不拆。 |
| 「Every branch above keeps one rule」（107） | 规则 | 每次 | 能同时跑的两票不写同一文件；给出「能同时跑」的定义。 |
| 第 5 步 Done（109） | 顺序 | 每次 | |
| 第 6 步 scan 段（113–119） | 做法 + 接口 | 每次 | host 通用 subagent、一句 prompt、等它返回；host 不行则自己跑。 |
| breakdown 列表（121–129） | 格式 + 规则 | 每次 | **Worker** 一行含 `senior-worker` 判据（「wrong **silently**」）；**Choices**；`ready-for-human` 票也列。 |
| 问用户（131–137）、迭代与回写（139） | 做法 | 每次 | 改 spec 的取舍经 `revising-a-spec.md`。 |
| 第 6 步 Done（141） | 顺序 | 每次 | |
| 第 7 步草稿与 lint（145） | 格式 + 接口 | 每次 | `TITLE:`/`LABELS:`/`BLOCKED BY:` 头、`---`；`--lint --drafts`。 |
| label 与发布（147） | 接口 | 每次 | `mmw:ticket`、`ready-for-agent`+grade 或 `ready-for-human`；`--publish --drafts`。 |
| 「Close no parent issue.」（149） | 规则 | 每次 | |
| 第 7 步 Done（151） | 顺序 | 每次 | |
| 第 8 步（155–160） | 做法 + 分派 | 每次 | 再跑 `--lint`、WARN 逐条看；每张 `ready-for-human` 核 the five things；夜批次交 `dispatch`。 |
| `<issue-template>` `## Parent`（164–166） | 格式 | 每次；夜里 orchestrator、triage `became-ticket` 也读 | 首个 issue 号即本票 spec。 |
| `## What to build`（168–170） | 格式 + 规则 | 同上 | 分点的理由句（2026-09-28 补回）。 |
| `## Read first`（172–174） | 格式 + 规则 | 同上 | **baseline** 定义；界面票 → `cutting-interface-tickets.md`。 |
| `## Seam`（176–178） | 格式 | 同上 | |
| `## Owns`（180–188） | 格式 + 规则 | 同上 | 仓库相对路径、`(new)`、无绝对路径/`..`/裸 `**`、粒度、并行不重叠、工具箱改动不进 Owns；删/改名把 grep 到的引用处收进 Owns。 |
| `## Acceptance criteria`（190–202） | 格式 + 接口 | 同上 | `TIMEOUT:` 语义（只抬不降）。 |
| 模板后路径规则（206） | 规则 | 每次 | 上游句改窄，两个例外（Seam、Owns）。 |

### 2.5 `to-tickets/references/ambiguity-scan.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 第 3 行 | 做法（边界） | subagent；每次切票 | 只读 spec 与草稿、一轮、不写 tracker。 |
| 第 5 行 | 立场 | 同上 | 「skeptical, adversarial」（merge-note 说取自 Factory Missions 抓包提示词，未核实原文）。 |
| `## Scan`（7–59） | 做法 | 同上 | 十类清单，merge-note 说照抄 spec-kit `templates/commands/clarify.md`（commit `d848fb4e`）第 73–123 行；本次未核实 spec-kit 原文。 |
| `## Questions`（61–79） | 格式 + 规则 | 同上 | 最多 5 条；只收会改变票交付或判据的问题；每条的五项结构。 |
| 末句（81–83） | 格式 | 同上 | 无问题时原样返回的固定字符串。 |

### 2.6 `to-tickets/references/cutting-interface-tickets.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 开头（1–5） | 接口 + 规则 | 切票 agent；分支：有 screen contract | **page ticket** 定义＝`--lint` 的读法（`screen-contract.yaml rows:` 行）。 |
| `## Criterion shapes`（7–60） | 接口 + 格式 | 同上；`ui-acceptance` 也指向这里 | story / boundary / journey / harness guard 四种 `CHECK:`/`EXPECT:`；smoke journey 不带 `--break` 的理由（43–47，规则）；「A layer with no precedent yet」（60，顺序：先切 contract ticket）。 |
| `## Seam and Owns on these tickets`（62–68） | 规则 + 格式 | 同上 | 按判据形状给观察层；`## Parent` 多 spec 顺序；design page 永不进 Owns。 |
| `## design-system ticket`（70–78） | 做法 + 顺序 + 规则 | 分支：design package 带 `_ds/` 且产品缺 | 纵切第二个例外。 |
| `## contract ticket`（80–110） | 做法 + 顺序 + 规则 | 分支：有缺的到达机制 / 新产品 | 交付清单九项；只有 smoke journey 带判据，静态守卫与 harness guard 判据放末票；是 prefactor ticket。 |
| `## component page ticket`（112–125） | 做法 + 格式 + 规则 | 界面分支 | 每行判据规则；`next` 指另一页 scene 时断言到哪；Read first 两条 baseline 行与推导。 |
| `## app page ticket`（127–133） | 做法 + 格式 | 界面分支 | composition module 进 Owns。 |
| `## critical-flow ticket`（135–143） | 做法 + 顺序 | 分支：spec 有 **Critical flows** 行 | 阻塞边从流程的行推导；`senior-worker`。 |
| `## Shared journey helper`（145–147） | 做法 | 分支：两张以上 journey 票 | |
| `## reaction ticket`（149–151） | 规则 | 界面分支 | 与 code review `UI` axis 的分界。 |

### 2.7 `to-tickets/references/person-ticket.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 第 3 行 | 规则 | 切票 agent 第 4 问第 3/4 支；triage `ready-for-human` | 人做的事单开一张，被产出它的票阻塞。 |
| 第 5–13 行 the five things | 格式 + 规则 | 同上；第 8 步回读 | **Which kind** 与 **retiring line**；「这是全流水线唯一不向机器交代理由的出口」；**What to look at** 给链接（手机上读）。 |
| 第 11 行 | 做法 + 接口 | 分支：自托管仓库 | `lease.py run -- <start>` 一条命令起产品并打印地址。 |

### 2.8 `triage/SKILL.md`

| 段（行） | 类型 | 谁·何时·频率 | 备注 |
| --- | --- | --- | --- |
| frontmatter（3） | 分派（触发） | host 启动 | 两支：外来 issue/PR；流水线退回 `needs-triage` 的票。 |
| 首句（8） | 立场 | 每次 | 上游。 |
| PR 段（10） | 规则 | 分支：PR 作为请求面 | 本仓 `docs/agents/issue-tracker.md` 写 `PRs as a request surface: no`，本仓不走。 |
| 免责声明（12–16） | 格式 | 每次发评论 | 放末行（上游放首行）。 |
| `## Reference docs`（18–22） | 分派 | 每次 | 三个指针。 |
| `## Roles`（24–45） | 接口 + 规则 + 顺序 | 每次 | 两类 category、五个 state；MMW 例外「本仓自己规划的活不带 category」；状态转移。 |
| `## Invocation`（47–54） | 分派 | 每次 | 自然语言请求例子。 |
| `## Show what needs attention`（56–66） | 做法 | 分支：用户要看队列 | 三个桶。 |
| 路由句（70） | 分派 | 每次挑一张时 | 带 `mmw:child`/`mmw:ticket` 或 `Retro #<spec>:` 标题 → 先读 `references/pipeline-issues.md`。 |
| 步骤 1–4（72–78） | 顺序 + 做法 | 外来 issue 每步；流水线 issue 替换第 1 步复现 | redundancy / prior rejection 两查；先推荐再等指示；复现；grill（读 `grilling`、`domain-modeling`）。 |
| 步骤 5（80–88） | 分派 + 顺序 + 格式 | 每次 | 四个 outcome；`ready-for-agent` 外来 issue → agent brief → `to-spec`（新写或修订）→ 关 issue → `to-tickets`；`ready-for-human` → the five things；`wontfix` 三种关法。 |
| route 句（90） | 接口 + 规则 | 分支：流水线 child | `dispatch.sh route <ticket> <child> fixed` / `stale <invalid|fixed-elsewhere>`；`wontfix` 不等于「已做完」。 |
| `## Quick state override`（92–94） | 做法 + 分派 | 分支 | 末句问要不要现在走 `to-spec`→`to-tickets`。 |
| `## Needs-info template`（96–112） | 格式 + 规则 | 分支：`needs-info` | |
| `## Resuming a previous session`（114–116） | 分派 | 分支：有旧 triage notes | |

### 2.9 `triage/references/pipeline-issues.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 第 3 行 | 立场 + 接口 | triage agent；分支：流水线 issue | 队列几乎全是流水线产物；每项收成用户一句话能答的问题；读 `verify-ticket` 的 `events.py fold <n>`，不复现；「留在 needs-triage 的明天被更少上下文的人再读」。 |
| 第 5 行 | 分派 | 同上 | 按来源：child 五种 kind（`decision`/`contract`/`deferred`/`fault`/`finding`）、交回/弹回/`reverify` 重开的票、被夜搁置的票、retro 提案。 |
| `## A ticket handed back`（7–15） | 接口（事件）+ 做法 + 规则 | 分支：最新结果是 `ticket.returned`/`ticket.bounced`/`ticket.regressed` | 各读哪些事件字段（`commit`、`into`、`files`、`commands`）；`regressed` 常由后票打红、下一次 `reverify` 自会关；`ABANDON:` kind → outcome；原样送回会重演。 |
| `## ready-for-agent`（17–29） | 分派 + 接口 + 规则 | 分支：判 child 为 `ready-for-agent` | 三去向表（改挂 / `route … became-ticket` / `gh issue transfer`）；`became-ticket` 后要手动换 label 并 lint；只有未开工的票读得到改挂；退回票换回 `ready-for-agent` 后由 `advance` 或 one-ticket run 接走。 |

### 2.10 `triage/AGENT-BRIEF.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 开头三段（3–7） | 立场 | 分支：外来 issue 判 `ready-for-agent` | MMW 改：brief 是调查记录，不是工单；进 ticket pipeline。 |
| `## Principles`（9–39） | 规则 | 同上 | 耐久胜于精确、行为不写过程、完整判据、明确范围。 |
| `## Template`（41–70） | 格式 | 同上 | `## Agent Brief` 标题（`to-spec` 在评论里找它，vocabulary recheck DECISIONS 第 96 行）。 |
| `## Examples`（72–209） | 格式 | 同上 | 好（bug/enhancement/PR）与坏例子并列。 |

### 2.11 `triage/OUT-OF-SCOPE.md`

| 段 | 类型 | 谁·何时 | 备注 |
| --- | --- | --- | --- |
| 开头（3–6） | 立场 | 外来 issue 第 1 步；`wontfix` 被拒 enhancement | 机构记忆与去重。 |
| 目录结构与文件格式（8–68） | 格式 + 规则 | 同上 | 一概念一文件；理由要耐久。 |
| 何时查 / 何时写 / 更新删除（70–105） | 做法 + 顺序 | 同上 | |

### 2.12 docs 与词表

| 文件·段 | 类型 | 谁·何时 |
| --- | --- | --- |
| `issue-tracker.md` `## Conventions` | 接口 + 规则 | 每个动 tracker 的 agent；「Every list read is a whole list」带理由。 |
| `issue-tracker.md` `## Reading a tree` | 接口 | 同上；`issue_tree.py` exit 2 的含义。 |
| `issue-tracker.md` `## Three label sets` | 接口（定义） | 同上；三套 label 与谁打。 |
| `issue-tracker.md` `## Pull requests as a triage surface` | 接口（配置开关） | triage。 |
| `issue-tracker.md` `## When a skill says …`（两节） | 接口 | 上游技能的通用措辞到 `gh` 的映射。 |
| `issue-tracker.md` `## Wayfinding operations` | 接口 | wayfinder；末句区分夜的 frontier（`status.py`）。 |
| `issue-tracker.md` `## Morning queries` | 顺序 | 早上的用户 session：先 `needs-triage` 跑 triage，再 `ready-for-human`。 |
| `triage-labels.md` 全文 | 接口 | triage、to-tickets。 |
| `domain.md` 全文 | 做法 + 规则 | 各 engineering 技能探索代码前；`_Home_` 纪律。 |
| `tickets/CONTEXT.md` 全文 | 定义（词表） | 维护者；按 `domain.md` 读词表的 agent。按 SKILL-SET-RULES `### Load and disclosure`，词表里的行为规则到不了执行的 agent。 |

---

## 3. 连线

### 3.1 对外交接（产出什么、谁读）

- **to-spec 产出**：一张 `mmw:spec` issue，正文为 `<spec-template>` 形状（`verify-ticket.py --publish --spec-body` 打 label；带 `--map` 时建成 map 的 native sub-issue 并读回 `parent.number`，`--help` `--publish` 退出码段）。读者：`to-tickets`（第 1 步读全正文与评论）；worker（`implement/SKILL.md` 第 16 行：Problem Statement、Solution、票点名的 Implementation Decisions 小节、Testing Decisions、Out of Scope）；reviewer 的 Spec axis（`code-review/references/spec-reviewer.md` 第 11 行：`## Parent` 点名的小节）；`verify-ticket.py --lint`（读 **Critical flows** 行，`CRITICAL_FLOWS_RE` 第 2913 行）；用户（spec 是「人最后看的一份文本」）。多份划分时写 map 的 `## Specs` 或首份 spec 的 `## Further Notes`。修订时写一条改动评论。
- **to-tickets 产出**：一批 `mmw:ticket` sub-issue（`ready-for-agent`+`junior-worker|senior-worker`，或 `ready-for-human`），native blocking edge；草稿目录（`mktemp -d`，临时）；ambiguity scan 结果文件（临时）。读者：`dispatch` 的 `status.py`/`advance`（frontier 取自 sub-issue、label、blocking edge）；worker（`implement` 读 `## Read first`/`## Seam`/`## Owns`/`## Parent`/criteria）；`verify-ticket.py`（criteria、`## Parent` 首号、`rows:` 行、Owns glob）；用户（`ready-for-human` 队列，早上第二条查询）。
- **triage 产出**：label 变化；`## Agent Brief` 评论（外来 issue，读者 `to-spec` 的 `## Sources` Originating issue）；`## Triage Notes` 评论；`.out-of-scope/<concept>.md`（本仓与 agentflow 从未建过，见第 6 节）；关闭 issue；经 `dispatch.sh route` 在原票写 `child.closed` 事件（`dispatch.sh` 第 4447–4450 行注释）；把票换回 `ready-for-agent` 后由下一次 `advance` 重派（`pipeline-issues.md` 第 29 行）。
- **triage 的输入队列由谁喂**（本单元不写这些事件，只读）：`verify-ticket.py --sub-issue`（`mmw:child` + `needs-triage`，第 1600–1622 行）；`verify-ticket.py --closeout` 交回（`HANDED BACK`，第 2613 行）；`dispatch.sh` 第二次 bounce 与 `reverify`（第 2840、3685 行附近）；`retro.py` 建 `Retro #…` 提案（第 610 行，`--label needs-triage`）；`night.md` 第 100 行把未开工票移到 `needs-triage`。

### 3.2 点名调用与被调用

- to-spec 点名：`setup-matt-pocock-skills`（硬依赖）、`write-screen-contract`（**Reverse sweep** 回退）、`wayfinder`（经 map 与 alignment ticket）、`verify-ticket`（`--publish`）、`ui-acceptance`（`target_config.py --check`、story oracle，不复述）、`to-tickets`（`## Next`）。
- to-tickets 点名：`setup-matt-pocock-skills`、`to-spec`（无 spec、第 2 问、无命令时、第 6 步回写）、`verify-ticket`（`--lint --drafts`、`--publish --drafts`、`--lint`）、host 通用 subagent（ambiguity scan）、`dispatch`（第 8 步末）、`code-review`（第 2 问、reaction 分界）、`ui-acceptance`（界面 reference：`story-parity.md`、`journey.md`、`product-answers.md`、`boundary-check.md`、`lease.py`）。
- triage 点名：`setup-matt-pocock-skills`、`grilling`、`domain-modeling`、`to-spec`（及 `revising-a-spec.md`）、`to-tickets`（`<issue-template>`、`person-ticket.md`）、`dispatch`（`route`、`advance`、one-ticket run）、`verify-ticket`（`events.py fold`、`--lint`）。
- 点名本单元的：`ask-matt/SKILL.md`（第 23、40–42、48 行）、`wayfinder/SKILL.md` 第 126 行、`write-screen-contract/SKILL.md` 第 115–120 行、`improve-codebase-architecture/SKILL.md` 第 75 行、`dispatch/references/night.md` 第 98、141 行、`ui-acceptance/SKILL.md` 第 20 行、`verify-ticket/references/linting.md`（不点名，但同一批「发布前/后」时刻）、`docs/agents/issue-tracker.md` `## Morning queries`。

```edges
wayfinder -> to-spec : hands-off-to
ask-matt -> to-spec : hands-off-to
ask-matt -> triage : hands-off-to
improve-codebase-architecture -> to-spec : hands-off-to
write-screen-contract -> to-spec : hands-off-to
write-screen-contract -> to-spec/references/revising-a-spec.md : hands-off-to
triage -> to-spec : hands-off-to
triage -> to-spec/references/revising-a-spec.md : hands-off-to
triage -> to-tickets : hands-off-to
triage -> to-tickets/references/person-ticket.md : reads
triage -> to-tickets/SKILL.md#issue-template : reads
triage -> grilling : calls
triage -> domain-modeling : calls
triage -> verify-ticket/scripts/events.py : runs-script
triage -> dispatch/scripts/dispatch.sh#route : runs-script
dispatch/scripts/dispatch.sh#route -> ticket : writes-event
triage -> verify-ticket/scripts/verify-ticket.py#--lint : runs-script
triage -> .out-of-scope/ : reads
triage -> .out-of-scope/ : writes-artifact
triage -> issue#Agent-Brief-comment : writes-artifact
triage -> triage/references/pipeline-issues.md : reads
triage -> triage/AGENT-BRIEF.md : reads
triage -> triage/OUT-OF-SCOPE.md : reads
triage -> dispatch#advance : re-enters-at
triage -> dispatch/references/one-ticket.md : re-enters-at
triage -> docs/agents/triage-labels.md : configured-by
triage -> docs/agents/issue-tracker.md : configured-by
verify-ticket/scripts/verify-ticket.py#--sub-issue -> triage : feeds-queue
verify-ticket/scripts/verify-ticket.py#--closeout -> triage : feeds-queue
dispatch/scripts/dispatch.sh#reverify -> triage : feeds-queue
dispatch/scripts/dispatch.sh#advance -> triage : feeds-queue
retro/scripts/retro.py -> triage : feeds-queue
dispatch/references/night.md -> triage : feeds-queue
docs/agents/issue-tracker.md#Morning-queries -> triage : cites
to-spec -> setup-matt-pocock-skills : cites
to-spec -> to-spec/references/revising-a-spec.md : reads
to-spec -> to-spec/references/several-specs.md : reads
to-spec -> write-screen-contract#Reverse-sweep : re-enters-at
to-spec -> wayfinder#alignment-ticket : re-enters-at
to-spec -> map#Decisions-so-far : reads
to-spec -> docs/specs/<effort>/screen-contract.yaml : reads
to-spec -> TESTING.md : reads
to-spec -> CODING_STANDARDS.md : reads
to-spec -> docs/agents/domain.md : configured-by
to-spec -> verify-ticket/scripts/verify-ticket.py#--publish--spec-body : runs-script
to-spec -> ui-acceptance/scripts/target_config.py#--check : cites
to-spec -> spec-issue : writes-artifact
to-spec -> map#Specs : writes-artifact
to-spec -> to-tickets : hands-off-to
to-tickets -> to-spec : re-enters-at
to-tickets -> to-spec/references/revising-a-spec.md : calls
to-tickets -> to-tickets/references/ambiguity-scan.md : calls
to-tickets -> to-tickets/references/cutting-interface-tickets.md : reads
to-tickets -> to-tickets/references/person-ticket.md : reads
to-tickets -> verify-ticket/scripts/verify-ticket.py#--lint--drafts : runs-script
to-tickets -> verify-ticket/scripts/verify-ticket.py#--publish--drafts : runs-script
to-tickets -> verify-ticket/scripts/verify-ticket.py#--lint : runs-script
to-tickets -> ticket-issues : writes-artifact
to-tickets -> dispatch/references/night.md : hands-off-to
to-tickets -> code-review : cites
to-tickets -> docs/agents/triage-labels.md : configured-by
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/boundary-check.md : cites
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/story-parity.md : cites
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/journey.md : cites
to-tickets/references/cutting-interface-tickets.md -> ui-acceptance/references/product-answers.md : cites
to-tickets/references/person-ticket.md -> ui-acceptance/scripts/lease.py : cites
ui-acceptance -> to-tickets/references/cutting-interface-tickets.md : cites
dispatch/references/night.md -> to-tickets/SKILL.md#issue-template : reads
dispatch/references/night.md -> to-spec/references/revising-a-spec.md : reads
implement -> ticket-issues : reads
implement -> spec-issue : reads
code-review/references/spec-reviewer.md -> spec-issue : reads
dispatch/scripts/status.py -> ticket-issues : reads
verify-ticket/scripts/verify-ticket.py#--lint -> spec-issue : reads
to-spec -> verify-ticket/scripts/verify-ticket.py : configured-by
to-tickets -> verify-ticket/scripts/verify-ticket.py : configured-by
```

自拟关系：`writes-artifact`＝写 tracker issue、label、评论或仓库文件，但不是 `<!-- mmw -->` 事件；`feeds-queue`＝脚本或技能把 issue 放进 `needs-triage`，triage 早上读（不唤醒 session，早上由用户按 `## Morning queries` 启动）。最后两行 `configured-by verify-ticket.py`：三套 label 的颜色与说明只在 `verify-ticket.py` `CLASS_LABELS`/`QUEUE_LABELS`/`GRADE_LABELS`（第 59–79 行）定义（`issue-tracker.md` `## Three label sets` 末段）。

---

## 4. 重复（grep 核实）

范围：`mmw-v2/`、`docs/`（不含 `docs/reviews/`、`docs/research/`）、根 `AGENTS.md`、`CODING_STANDARDS.md`、`TESTING.md`。merge-note 里对同一规则的记录是设计上的「意图记录」，不逐条列为重复。

| # | 条目 | 本单元位置 | 另一处 | 判定 |
| --- | --- | --- | --- | --- |
| R1 | 「已发布的 spec、票正文、判据只由 orchestrator 或用户在场的 session 编辑」 | `revising-a-spec.md` 第 3 行末句 | `implement/SKILL.md` 第 22 行「Once a batch is published, only its orchestrator or the user edits a spec, ticket body or acceptance criterion.」 | 真重复，读者不同（修订者 / worker）。 |
| R2 | 发布后再跑 `--lint`、ERROR 为零、WARN 逐条看过 | `to-tickets/SKILL.md` 第 8 步第一条（157） | ① `verify-ticket/references/linting.md` 第 11 行「The batch is ready when `ERROR` is at zero and every `WARN` has been looked at…」；② `verify-ticket.py` `run_publish_drafts` docstring「then run `--lint` on the published spec once」，`--help`「--drafts: 0 every draft published … and --lint on the published spec reported no ERROR」 | 真重复。第 7 步 `--publish --drafts` 已在发布末尾跑过同一个 `lint_spec`（代码已核实），第 8 步再跑一遍是重复执行；独有的只剩「WARN 逐条看」。 |
| R3 | 能同时跑的两张票不写同一文件；「能同时跑」＝谁也不阻塞谁，直接或经链 | `to-tickets/SKILL.md` 第 107 行 | `implement/SKILL.md` 第 28 行「A file owned by a ticket that can run beside this one (neither blocks the other, directly or down a chain) is never changed from here」；`verify-ticket/references/sub-issues.md` 第 5 问（merge-note to-tickets 记载，未开读 sub-issues.md 全文） | 同一规则的两侧（出票侧 / worker 侧），真重复的定义句；merge-note 记为有意的对应。 |
| R4 | the five things 清单 | `person-ticket.md` 第 5–13 行 | `docs/contexts/tickets/CONTEXT.md` **the five things** 词条列出五项；`to-tickets` 第 8 步、`triage` 第 5 步只指过去 | 词表与 `_Home_` 同义，其余是指针，不算重复。 |
| R5 | `ready-for-human` 的含义 | `triage/SKILL.md` `## Roles` 第 36 行「one thing only a person can do, of kind `reaction` or `reach`」 | `docs/agents/triage-labels.md` 第 10 行同句；`CONTEXT.md` **`ready-for-human`** | 真重复（同一句话三处）。 |
| R6 | `senior-worker` 判据（错了会静默地错：钱到终态、崩溃恢复、已装基数在读的 contract、安全默认） | `to-tickets/SKILL.md` 第 126 行 | `CONTEXT.md` **`senior-worker`** 词条同一清单 | 真重复（词表复述 `_Home_`，`domain.md` 允许不多于 `_Home_`）。 |
| R7 | `EXPECT:` 是 success-only marker | `to-tickets/SKILL.md` 第 84 行 | `CONTEXT.md` **`EXPECT:`**；`mmw-v2/upstream-unlazy/references/gates.md` 第 100 行、`templates/gates-leaf.md` 第 29 行 | 同一概念；unlazy 是另一上游的原文，属同义不同读者。 |
| R8 | 「Every list read is a whole list」 | `docs/agents/issue-tracker.md` 第 7 行 | `setup-matt-pocock-skills/issue-tracker-github.md` 第 7 行 | 模板与实例；实例多了 `## Reading a tree`、`Re-parent`、`Transfer`、`## Morning queries`。按设计的种子副本，但两份已分叉（diff 已核实）。 |
| R9 | 五个 label 的映射表 | `docs/agents/triage-labels.md` | `setup-matt-pocock-skills/triage-labels.md` | 同上，模板与实例；含义列已分叉（实例 `ready-for-human` 改成 reaction/reach）。 |
| R10 | 三套 label 定义 | `issue-tracker.md` `## Three label sets` | `verify-ticket.py` `CLASS_LABELS`/`QUEUE_LABELS`/`GRADE_LABELS`；`CONTEXT.md` **label**、**layer label**、**queue** | 程序是权威副本，文档是说明；同义。 |
| R11 | 免责声明位置 | `triage/SKILL.md` 第 12 行「on its own last line」 | `mmw-v2/upstream/docs/engineering/triage.md` 第 95 行「opens with」 | 同词反义：说明页是上游原文（2026-09-28 按 triage 定稿 D6 恢复），不装进 host，与技能正文矛盾。 |
| R12 | spec 打不打 `ready-for-agent` | `to-spec/SKILL.md` 第 4 步「Give it no triage label」 | `mmw-v2/upstream/docs/engineering/to-spec.md` 第 42 行「Why does the spec get the `ready-for-agent` label?」 | 同词反义：上游说明页，不装进 host。merge-note to-spec `### docs page` 只记了 native parent 两处，没提这一问。 |
| R13 | 「only `ready-for-agent` moves a child」与四个 outcome | `pipeline-issues.md` 第 19 行、`triage/SKILL.md` 第 80 行 | `CONTEXT.md` **triage**、**`needs-info`**、**`wontfix`** 词条（「one of triage's four outcomes」） | 词表同义。 |
| R14 | `route … fixed/stale/became-ticket` 的行为 | `triage/SKILL.md` 第 90 行、`pipeline-issues.md` 表第二行 | `dispatch.sh` 第 25–27、393–395、4447–4470 行注释；`night.md` 第 139 行 | 本单元只给命令，行为说明在脚本；非重复（2026-09-28 已删复述，triage 定稿 D1）。 |
| R15 | 「setup 没给就去装」一句 | to-spec 第 8 行、to-tickets 第 12 行、triage 第 43 行 | `wayfinder/SKILL.md`；上游 `.agents/adr/0001-explicit-setup-pointer-only-for-hard-dependencies.md` | 有意的同句（SKILL-SET-RULES `### Hand-offs` 末条把它作为范例）。 |
| R16 | `## Owns` 定义 | `<issue-template>` `## Owns` | `CONTEXT.md` **`## Owns`**；ADR 0012 引用 | 词表同义。 |
| R17 | 四行判据形态 | `to-tickets` 第 72–79 行 与 模板第 190–200 行（同一文件两处） | `CONTEXT.md` **acceptance criterion**；`night.md` 第 141 行只指向第 4 步 | 同文件内两处：第 4 步示例与模板示例；模板那份是夜里 orchestrator 读的（night.md 指第 4 步标题，故两处都有读者）。 |
| R18 | 夜的 frontier 定义 | to-tickets 不写（merge-note 记删除理由） | `issue-tracker.md` 第 82 行末句、`CONTEXT.md` **frontier** | 无重复。 |

「只是同词」：`contract`（`contract` child / contract ticket / screen contract / API contract），vocabulary recheck T14 已把 screen contract 写全；`interface`（module interface / UI），同上。`acceptance ticket`、`interface ticket`、`Cross-ticket flows`、`Test surfaces` 在活文本中已 grep 不到（只留在 merge-note 与 `mmw-v2/downstream-notes/514-interface-tickets.md`，后者是变更记录）。

---

## 5. 上游差异

行数（非空行中与上游逐字相同的行数由脚本比对得出）：

| 文件 | 上游行 / 词 | 现状行 / 词 | 上游非空行保留原样 |
| --- | --- | --- | --- |
| `to-spec/SKILL.md` | 75 / 493 | 127 / 2509 | 45 行中 31 行（多为标题与模板短句） |
| `to-spec/references/*` | 无 | 16 / 557 | — |
| `to-tickets/SKILL.md` | 105 / 894 | 206 / 3750 | 60 行中 30 行 |
| `to-tickets/references/*` | 无 | 249 / 3252 | — |
| `triage/SKILL.md` | 112 / 990 | 116 / 1228 | 71 行中 56 行 |
| `triage/references/pipeline-issues.md` | 无 | 29 / 794 | — |
| `triage/AGENT-BRIEF.md` | 207 / 1232 | 209 / 1339 | 153 行中 145 行 |
| `triage/OUT-OF-SCOPE.md` | 105 / 714 | 105 / 714 | 逐字相同 |
| 三个 `agents/openai.yaml` | 5 行 | 3 行 | 删 `policy` 块 |

地位：`mmw-v2/merge-notes/README.md` `## 本仓自有正文的技能` 把 `to-tickets` 列为「拉 upstream 时不合并」；`to-spec` 不在其中，但 merge-note to-spec 第 31 行写「这份技能不到一半的行是上游的，按本仓自己的文本审」。按 SKILL-SET-RULES `### Upstream skills` 末条，两者都应「reviewed as the set's own text」；只有 to-tickets 在 README 里被声明为不合并上游。triage 以上游为主。

### 5.1 to-spec：逐段

| 被加/改的段 | 类型 | merge-note 条目（`merge-notes/to-spec.md`） | 改变能力 / 写入 MMW 流程 |
| --- | --- | --- | --- |
| `description` 末句触发 | 分派 | 第 11 行 | MMW 流程（四个入口）。 |
| 删 `disable-model-invocation` 与 yaml `policy` | 接口 | 第 12、41 行 | 调用方式，不改能力。 |
| 开头「for facts」+ 整段立场 | 立场 + 规则 | 第 23 行 | **改变能力**：上游「Do NOT interview the user」绝对不问；现在产品/钱/范围决定发布前问用户。 |
| setup 句 host 中立 | 接口 | 第 24 行 | 措辞。 |
| 新第 1 步（读引用、map、spec division）+ `several-specs.md` | 分派 + 规则 + 顺序 | 第 16 行 | **改变能力**：多来源综合与切分；map 回写属 MMW 流程。 |
| `revising-a-spec.md` 与指向句 | 做法 + 规则 | 第 17、21 行 | **改变能力**（就地修订）；「谁能编辑」属 MMW 流程。 |
| 第 2 步 screen contract 段 | 规则 + 分派 | 第 25、26 行；`## 没有合同行的决定` | MMW UI 流程。 |
| 第 3 步：删「Check with the user that these seams match」、加「seam is yours」 | 规则 | 第 13 行 | **改变能力**（谁定 seam）。 |
| 第 3 步：观察/到达段 | 规则 | 第 13 行 | **改变能力**（新增「到达」问题）。 |
| 第 3 步 `TESTING.md` 句 | 接口 | 第 14 行 | MMW 仓库规则接线（用户决定）。 |
| 第 4 步 `--publish`、不打 `ready-for-agent` | 接口 + 规则 | 第 15 行 | MMW 流程；不打 label 同时改变能力（spec 不再是可取工单）。 |
| 模板 Implementation Decisions：编号、出处、`CODING_STANDARDS` 规则、story 折入、路径禁令收窄 | 格式 + 规则 | 第 18、26 行 | MMW 流程（票按节号指回、worker 只读点名小节）。 |
| 「Each subsection is read on its own」 | 规则 | **无条目**（grep 未见） | MMW 流程。 |
| API contract / cross-component composition / visual acceptance | 格式 | 第 25、27、28 行 | MMW UI 流程。 |
| Testing Decisions：大白话首句、seam 句、layer+precedent、提交前命令 | 格式 | 第 19 行 | 部分改变能力（seam 对用户透明）；`precedent` 词统一属 MMW 词汇。 |
| **How a test arrives at a state** | 规则 + 接口 | 第 13、29 行 | **改变能力**（到达机制），UI 后半是 MMW 流程。 |
| **Critical flows** | 格式 + 接口 | 第 20 行；`## Critical flows 每一行的形状` | MMW UI 流程（lint 读）。 |
| `## Sources` 十二类 | 格式 | 第 22 行 | MMW 流程。 |
| `## Further Notes` 划分行 | 格式 | 第 16 行 | MMW 流程。 |
| `## Next` | 分派 | 第 30 行 | MMW 流程。 |
| 各步 `Done when` | 顺序 | 第 31 行 | 本仓文本规则。 |

merge-note 与现状不一致（已核实）：第 22 行说「`implement` 技能靠这个节名（`## Sources`）往回读，改名要同步改 `implement`」，但 `implement/SKILL.md` 第 16 行读的是 Problem Statement、Solution、点名的 Implementation Decisions、Testing Decisions、Out of Scope，全仓 grep `Sources` 在 implement 与 code-review 中无命中。第 31 行说第 4 步 Done 判据是「spec 带 `mmw:spec` 发布，从 map 来时读回的 native `parent.number` 是 map」，现文是「Done when `--publish` exits 0.」（行为由脚本承担，意思等价，措辞条目未更新）。

### 5.2 to-tickets：逐段

merge-note 声明：正文为本仓文本，上游 pull 不合进来（`merge-notes/to-tickets.md` 第 5 行）。

| 被加/改的段 | 类型 | merge-note 条目 | 改变能力 / 写入 MMW 流程 |
| --- | --- | --- | --- |
| `description` 改写（去掉本地文件形态） | 分派 | 第 13 行 | MMW 流程。 |
| 开头「Each ticket is read by agents…」 | 立场 | **无条目** | 立场（2026-09-28 lightweight 定稿 I1）。 |
| 第 1 步「no published spec → to-spec」、删 `## Parent` 省略分支 | 分派 | 第 14 行 | MMW 流程（所有步骤要 spec 号）。 |
| 第 2 步去 `(optional)` | 顺序 | 第 16 行 | 小。 |
| 删「single fresh context window」 | 规则 | 第 39 行 | **改变能力**（用户裁定：粒度不设机械上限）。 |
| 「Split where the parts can run at the same time…」 | 规则 | **无条目**；来源是 2026-09-28 lightweight 定稿 I3（汇总第 38–50 行问过用户） | 改变能力（给出拆分判据）。 |
| 第 3/4 步拆分 | 顺序 | 第 17 行 | 结构。 |
| 第 4 步全部（三规则、五问、四行、推导、取对象、状态、批次） | 规则 + 分派 + 格式 + 接口 | 第 18–20、27、31 行；`## 一条判据不被同批次后面的 ticket 弄红` | **改变能力**：判据必须可由命令判定；五问分流。四行形态与 `$MMW_TICKET` 是 MMW 接口。 |
| 第 5 步独立成步 | 顺序 | 第 26 行 | 结构（边在判据之后连）。 |
| 「The edges are the night's schedule…」 | 规则 | **无条目**（lightweight 定稿 I2） | 改变能力（多余边也有代价）。 |
| put-in-service、prefactor、共用逻辑文件、one rule | 做法 + 规则 | 第 32 行；`## 让新文件跑起来的那几处改动归本票`；第 41 行（part 3 表） | **改变能力**（Owns 推导）。 |
| 第 6 步 scan、Worker、Choices、`ready-for-human` 列出、回写 | 做法 + 格式 | 第 21、22、42、43 行 | 改变能力（找漏、分级）；grade label 属 MMW 流程。 |
| 第 7 步：草稿 + `--lint --drafts` + `--publish --drafts`；删 Local files 与 `<local-ticket-template>`；删「Work the frontier」；「Close no parent issue」 | 接口 + 规则 | 第 23、24、25、37 行；part 3 第 40 行 | MMW 流程；删本地形态收窄能力。 |
| 第 8 步 | 做法 + 分派 | 第 28 行 | MMW 流程。 |
| `<issue-template>` 新节（Parent 小节号、What to build 分点、Read first/baseline、Seam、Owns、四行判据、TIMEOUT）；删 `## Blocked by` 节 | 格式 + 规则 | 第 29、30、33、34 行；`## 删除或改名的票收进引用处` | **改变能力**（Owns 写权限、baseline）；节名是 `implement`/`verify-ticket.py` 读的接口。 |
| 模板后路径规则收窄 | 规则 | 第 36 行 | 改变能力（Owns/Seam 例外）。 |
| `ambiguity-scan.md` | 做法 + 格式 | `## 找漏 reference` | 改变能力（新增找漏环节）。 |
| `cutting-interface-tickets.md` | 全部类型 | `## 界面 ticket 的规则`、`## 一个概念一个名字`、`## 界面 ticket 接回模板的 Seam、Owns 与五问`、`## contract ticket …` 两节、`## 任务板试点 #541 …`、`## 走真实流程补的四处缺口`、`## … 只写切票那一刻用得上的话` | MMW UI 流程。 |
| `person-ticket.md` | 格式 + 规则 | 第 35 行；part 3 第 43 行 | 改变能力（`reaction`/`reach` 两类）；自托管分支属 MMW 流程。 |

merge-note 与现状不一致（已核实）：
- 第 28 行（第 8 步）说 lint「那次 run 读什么、报什么、退什么码见 `references/linting.md`」；part 3 表第 40 行说「`verify-ticket` 的 `references/linting.md` 只写 lint 对草稿做什么，指回第 7 步」；part 3 表第 42 行说「`references/linting.md` 只留 `[parent-order]` 那一句」。现 `linting.md` 只有 11 行，没有退出码（在 `--help`）、没有指回第 7 步、没有 `[parent-order]`。
- `## 让新文件跑起来…` 一节写「第 5 步永远排在 acceptance criterion 之后…在 quiz 之前」，与现状一致。
- Nowledge Mem 记忆 `d06fc6c2-…`（「子票膨胀应在分拣层用 Owns 修」）说删改名收进 Owns 的规则「明确不并入 main」；现 `to-tickets/SKILL.md` 第 184 行有这一段。记忆过时。

### 5.3 triage：逐段

| 被加/改的段 | 类型 | merge-note 条目（`merge-notes/triage.md`） | 改变能力 / 写入 MMW 流程 |
| --- | --- | --- | --- |
| `description` 删产出列举、加两支触发 | 分派 | 第 11、12 行 | MMW 流程。 |
| `## Reference docs` AGENT-BRIEF 一条 | 分派 | 第 11 行 | 随 brief 性质改。 |
| 删 `disable-model-invocation` / `policy` | 接口 | 第 15、36 行 | 调用方式。 |
| 免责声明移到末行 | 格式 | 第 16 行 | MMW 流程（首行留给人扫）。 |
| `ready-for-human`（Roles 与第 5 步）改成 reaction/reach + the five things | 规则 + 格式 | 第 17 行 | **改变能力**（删上游四个理由，队列只收两类）。 |
| Roles 例外（本仓规划的活不带 category） | 规则 | 第 18 行 | MMW 流程。 |
| host 中立四处 | 接口 | 第 13 行 | 措辞。 |
| 路由句（第 70 行）+ `pipeline-issues.md` | 分派 | 第 19、20 行 | MMW 流程。**条目过时**：第 19 行描述路由条件为「worker 开的 `mmw:child`，以及最新结果是 `ticket.returned` 或 `ticket.bounced` 的 `mmw:ticket`」；现文按 label（`mmw:child`/`mmw:ticket`）与 `Retro #<spec>:` 标题路由（2026-09-28 triage 定稿 I1）。 |
| 第 5 步 `ready-for-agent` 进 pipeline、关 issue | 顺序 + 分派 | 第 21 行 | **改变能力**：上游只贴 brief 改 label；现在必经 `to-spec`→`to-tickets`。 |
| 第 5 步「four outcomes」、删 `needs-triage` 条 | 规则 | 第 23 行 | 小。 |
| 第 5 步末 route 句（第 90 行） | 接口 + 规则 | **无条目** | MMW 流程（agentflow #620–#629 误用 `wontfix`）。 |
| `## Quick state override` 末句 | 分派 | 第 22 行 | MMW 流程。 |
| `pipeline-issues.md` 开头立场段、来源清单中的 retro / 被搁置票、`ticket.regressed` 段、`ABANDON:` 段、表第二行 label 说明、「Only a ticket not yet started reads it」、「With no night open…」 | 立场 + 分派 + 做法 | **大部分无条目**（grep「regressed」「ABANDON」「Retro」「retro」均无命中）；第 20、21 行只覆盖旧的来源清单与三去向 | MMW 流程。 |
| `AGENT-BRIEF.md` 性质改为调查记录、原则里对 agent 说话的句子 | 立场 | 第 29、30 行 | **改变能力**：brief 不再是工单合同。 |

SKILL-SET-RULES `### Upstream skills` 第 2、3 条：「Every changed paragraph maps to a merge-note entry」「An entry that still states a replaced rule is a finding」。上面标「无条目」「条目过时」的各处按这两条是待补项（本报告只记录，不修）。

---

## 6. 价值证据

证据状态：**已核实**＝本次回到原文、提交或 tracker 看过；**引述**＝只在 merge-note / 复审里看到，未回到一手来源；**无证据**。

| 部件或段 | 防的失败 | 证据 | 状态 |
| --- | --- | --- | --- |
| to-spec 开头立场段（产品决定问用户） | spec 带着没人定的产品空缺发布，到切票或夜里才暴露 | spec #555 修订评论「第 2 节补上顶栏读失败时时间的写法与"从未读成功"时的写法：用户对切票时扫出的两处歧义的决定」（`gh issue view 555`） | 已核实 |
| to-spec 第 1 步 spec division | 分阶段交付被强塞一份没人读得懂 | merge-note to-spec 第 16 行（判据推理）；无具体事故编号 | 无证据（事故层面） |
| to-spec 第 2 步 `gap` 非 aligned 就停、两条退回路径 | 围绕未决定写 spec | merge-note 第 25 行引 #446 第 4 节、#447 第 6 节、「变色龙的界面因此接了空」 | 引述 |
| to-spec 第 3 步「到达」与 **How a test arrives at a state** | 判据假定一个无人建的机制，首夜即红；界面批次整批判不了第 4 问 | merge-note 第 29 行引 #539、#541 | 引述 |
| to-spec `--publish` 与 native parent 读回 | 手工 `gh` 建 issue 挂错或漏挂 parent | `test_publish.py` `TestPublishSpec` 两个用例存在（已核实）；lightweight to-spec 复审 A1 引 Memory：#77、#78 只写 `## Parent` 无 native 链接，#68 AC8 零次循环 `LINT-CLEAN` | 测试已核实；事故为引述 |
| to-spec **Critical flows** 行形状 | lint 读不出节号、误把下一条 bullet 当流程 | merge-note `## Critical flows 每一行的形状` 引 #541/#555；#555 修订评论「Critical flows 一行改为 `Implementation Decisions 6, 8, 9`：verify-ticket 的 lint 只认这种写法」 | 已核实 |
| to-tickets 五问与四行判据 | 「过了」只是写代码者的看法；判据不可判定 | I5-P1：#444–#447 连续四夜有不可满足或不可判定的 `CHECK:`；`lint_undecidable_checks` docstring 记 #449 AC9、#472 AC6 两个实测形状（已读代码） | 已核实（代码 docstring）；夜记录为引述 |
| to-tickets「A criterion is also exposed to the rest of its own batch」 | 后票把已落地前票判红 | 提交 `d195e2a3` 说明：#472 AC4 全仓扫描被后票写回旧名；#491 AC5 点名用例被 #493 改名 | 已核实 |
| to-tickets 第 5 步 put-in-service 与 prefactor | 同层并发票 Owns 互不重叠但都要改公共文件，只有一张能合 | issue #408（本仓）：agentflow #748/#750/#751 bounced，#752 合入；串成直线后「三张票的代码一行没改，全部一次过」 | 已核实 |
| `## Owns` 删/改名收引用处 | 删一个文件后别处还指着它，产生大量子票 | merge-note 引 #216 夜 #230–#252 十张子票；ADR 0012 记 #216 夜每票约 3 张子票、71% 落在本票 Owns 内 | ADR 已核实；十张子票为引述 |
| to-tickets 第 7 步草稿与发布命令 | 标题与正文错位；发布后才能修 | merge-note 与复审称「一次真实 publish 把 8 张 ticket 的标题错位了一格」（未给 issue 号）；#541 需要自己写包装脚本（引述） | 引述 |
| to-tickets 第 8 步 read-back | 发布后 tracker 状态不对 | 删掉的两条「从未抓到过东西」（158 张票核对，复审）；现存 `--lint` 与 `--publish` 内部 lint 重复（第 4 节 R2） | 引述；重复已核实 |
| ambiguity scan | 切票时才发现的歧义 | #555 的两处产品歧义「切票时扫出」（修订评论已核实）；是否由 scan 本身扫出未知 | 部分核实 |
| `cutting-interface-tickets.md` 各段 | 界面批次的各类出票错误 | merge-note 引 #447、#443、#539、#540、#541、#555；#555 修订评论已核实与 lint 写法、视口相关 | 部分核实 |
| `person-ticket.md` 两类与 the five things | 人做的事塞进 agent 票使其无法结束；早上的人说不上来 | 本仓 `ready-for-human` 共 15 张、agentflow 16 张（`gh` 计数） | 使用量已核实；失败事故无证据 |
| triage 外来 issue 主线（上游步骤 1–4、`AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`、PR 分支） | 外来请求的误判、重复讨论 | 本仓 585 张 issue、agentflow 717 张 issue 作者全是 `chancheuklap`（`gh issue list --state all -L 2000` 统计）；两仓默认分支都没有 `.out-of-scope/`（本仓 `ls`、agentflow `gh api …/contents/.out-of-scope` 404）；本仓 `PRs as a request surface: no` | 已核实：**这条分支在两仓从未发生** |
| triage `pipeline-issues.md` | 早上把流水线产物当陌生人报告；`reverify` 重开的票被关掉另写 spec | `needs-triage` 历史：本仓带 `mmw:child` 112 张、无层 label 155 张（抽样为 retro 提案与早期 finding）；agentflow 106 / 167；lightweight triage 复审称 #472、#491、agentflow #731 发生过重开票被当外来 issue | 队列构成已核实；误判事故为引述 |
| triage route `fixed`/`stale` 句 | `wontfix` 被当成「已做完」 | agentflow `wontfix` 5 张：#620、#621、#622、#629、#565（标题为已处理的整理项，`gh` 已核实存在与标签） | 已核实（标签与标题）；「已直接改完」的评论内容未读 |
| triage 免责声明末行 | 首行留给人扫（`status` 的 note 列、night summary 抄首行） | `status.py` 第 364–365 行对 `needs-triage` 票以 `head[:60]` 作 note 列显示（已核实代码；`head` 的来源未往上读） | 已核实 |
| `issue-tracker.md` 「whole list」 | 静默截断当成完整集合 | 无具体事故编号（ `retro.py` 第 596 行注释提到默认 30 条） | 无证据（事故） |
| `issue-tracker.md` `## Morning queries` | 早上漏掉夜里倒下的东西 | 无 | 无证据 |
| `domain.md` | 词汇漂移 | 无具体事故 | 无证据 |

---

## 7. 约束

| 约束来源 | 内容 | 约束了什么 |
| --- | --- | --- |
| ADR 0001 `tracker 与仓库文件的权威归属` | agent brief 只存在于 tracker；spec 发布或修订后原 issue 以链接评论关闭并列入 `## Sources` | triage 第 5 步关 issue、to-spec `## Sources` 的 Originating issue 一类。 |
| ADR 0005 | `docs/agents/` 三件配置落地；engineering 技能（to-spec、to-tickets、triage、code-review）的 tracker 前置检查成立 | 三份 `docs/agents/*.md` 的存在与位置。 |
| ADR 0012 `review-finding-routing` | out-of-ticket finding 按四步门槛路由；第 1 步落在另一张开着票的 `## Owns` → 开票并 `Blocked by` | `## Owns` 的写权限含义、Blocked by 规则。 |
| ADR 0015 `no-custom-subagents` | 用 host 自带通用 subagent | ambiguity scan 的起法。 |
| ADR 0019 `ticket-state-is-a-fold-of-events` | 票的状态是事件折叠；首行不再是协议 | triage 免责声明可移到末行；`pipeline-issues.md` 读 `events.py fold`。 |
| ADR 0023、0027 | bounce 交 triage；同夜第一次 bounce 回 worker 队列，第二次才 `needs-triage` | `pipeline-issues.md` `## A ticket handed back`。 |
| ADR 0011 | 界面等价在组件级判定；合同缺陷以判官红裁决交回 triage | `cutting-interface-tickets.md` 的 story/boundary/journey 分工。 |
| ADR 0029 | handoff package 只由 pull 写入 | 模板 `## Read first`「pulled into the repository」（merge-note to-tickets part 2 第 1 段）。 |
| SKILL-SET-RULES 事实 1 | 技能交代目的、依赖者、做浅的代价 | to-spec、to-tickets 开头立场段、`pipeline-issues.md` 开头段（2026-09-28 按此补）。 |
| 事实 2、`### Scripts and judgement` | 确定性工作交脚本 | 发布改成 `--publish`；第 8 步删掉两条人工核对。 |
| 事实 5、`### Load and disclosure` | 按分支拆 reference；每次都读的不拆 | `several-specs.md`、`revising-a-spec.md`、`cutting-interface-tickets.md`、`person-ticket.md`、`pipeline-issues.md` 都是分支文件；`<spec-template>` 留在 `SKILL.md`（`## Upstream examples` 表明写「the template stays inline because every run writes one」）。 |
| 事实 6、7 | 技能按名组合、一处一家 | the five things 只在 `person-ticket.md`；判据形状只在 `cutting-interface-tickets.md`；triage 不复述票的节数。 |
| `### Descriptions` | description 只写触发 | 三份 description 的写法。 |
| `### Upstream skills` | 上游文本只在改变 agent 行为处改；每段改动对应 merge-note | 三份 merge-note 的存在；`OUT-OF-SCOPE.md` 未改。 |
| `### Paths and host neutrality` | 不写 `the Skill tool`、`/name` | triage 第 4 步改成「read the `grilling` and `domain-modeling` skills' `SKILL.md`」。 |
| `### Rules and completion criteria` | 本仓文本每步有 `Done when` | to-spec、to-tickets 各步。 |
| `mmw-v2/merge-notes/README.md` `## disable-model-invocation` | 两处同增同删 | 三个技能模型可触发。 |
| `merge-notes/README.md` `## 本仓自有正文的技能` | to-tickets 不合并上游 | to-tickets 的演化自由度。 |
| 用户决定（merge-note to-tickets 第 39 行） | vertical slice 不设机械尺寸上限，粒度由 quiz 定 | 删上游「single fresh context window」。 |
| 用户决定（lightweight 汇总 `### 2.`） | 加「Split where the parts can run at the same time…」判据 | 第 3 步第 44 行（汇总列为待用户选择，现文已落地；用户选择记录本次未找到单独条目）。 |
| 用户决定（lightweight 汇总 `## 二、你已经定下的（2026-09-28）`） | 早上 triage 不当场修小问题，只判出口 | triage 无改代码权限；route 句。 |
| 用户决定（merge-note to-spec 第 14 行） | 仓库规则分 `CODING_STANDARDS.md` 与 `TESTING.md`，worker 只经 spec 与票拿相关条目 | spec 模板要求抄规则进小节；票 `## Read first` 列节。Nowledge Mem `0ac93ab8-…`「规则唯一出处设计（用户定）」同义（已读记忆）。 |
| `AGENTS.md` `## Self-hosting boundary` | 自托管仓库的常驻产品是冻结版本 | `person-ticket.md` 第 11 行的命令分支。 |

---

## 8. 天然整体

| 整体 | 理由 |
| --- | --- |
| `<spec-template>` 与 to-spec 第 3、4 步 | 每次运行都写一份 spec；模板的 `## Testing Decisions` 首句、seam 句、**How a test arrives at a state** 直接承载第 3 步的判断结果。SKILL-SET-RULES `## Upstream examples` 把它列为「template stays inline」的范例。 |
| to-tickets 第 4 步（三规则 + 五问 + 四行 + 推导 + 取对象 + 状态 + 批次） | 五问决定一句话能否成为判据，后面几段决定判据怎么写；拆开后写判据的 agent 在同一时刻要跳文件。merge-note to-tickets 第 17 行记录过「一个标题下两个概念来回跳」的教训，现结构正是为此分出。 |
| to-tickets 第 5 步（put-in-service 推导 + 两支 + one rule + Done） | 推导结果决定走哪一支，one rule 是两支共同的不变量；Done 判据引用两条规则。 |
| `<issue-template>` 与 `## Owns` 的删/改名段、`TIMEOUT:` 说明 | 夜里 orchestrator 与 triage `became-ticket` 只读模板（`night.md` 第 141 行、`pipeline-issues.md` 表第二行），规则必须在模板里才能到达写票的那一刻。 |
| `person-ticket.md` the five things | 五项缺一票就无法被人执行（第 8 步因此逐项核）；triage 与 to-tickets 共用同一份。 |
| `cutting-interface-tickets.md` 的五种票 + criterion shapes + Seam/Owns 节 | 五种票之间有阻塞序（design-system → contract → component → app → critical-flow），判据归属跨票（静态守卫、harness guard 在末票，先例由后票首次判定）；拆开会丢掉这些跨票关系。 |
| `revising-a-spec.md` 一整份 | 修订四件事（就地改、理由评论、对齐未落地票、已落地出更正票）是一个事务；被五个不同调用方在不同时刻送来，放在一个文件里正符合「一个 moment 一个文件」。 |
| triage `## Roles` + 状态转移 + 第 5 步四个 outcome | 状态机本身：角色、转移、出口三者互相定义。 |
| `pipeline-issues.md` `## A ticket handed back` + `## ready-for-agent` | 前者判断、后者执行；`ready-for-agent` 表的三去向只对 child 成立，退回票的去向写在同一节末段。 |
| `AGENT-BRIEF.md` 模板与好坏例子 | SKILL-SET-RULES `### Examples` 与 `## Upstream examples` 引它为「好坏并列」的范例。 |
| `docs/agents/issue-tracker.md` `## Three label sets` 与 `verify-ticket.py` 的 label 定义 | 文档说「颜色与说明只在 `verify-ticket.py` 定义一次」；两者是说明与权威副本的关系，不宜再各自扩写。 |

---

## 9. 未确定

- `verify-ticket/references/sub-issues.md` 的「第 5 问」全文未读；R3 的对应关系只核实了 `implement` 一侧。
- `ambiguity-scan.md` 声称的 spec-kit `clarify.md`（`d848fb4e` 第 73–138 行）与 Factory Missions 提示词出处未回到原文核对。
- 「8 张票标题错位一格」没有 issue 号，未能核实。
- `verify-ticket.py --lint` 是否检查「`CHECK:` 搜索自己的对象」（`gh issue list --search … | head -1`）：grep 规则名未见专门规则（见到的规则名有 `bad-timeout`、`dollar-without-m`、`parent-order`、`screen-contract`、`shared-state`、`undecidable-check`、`worker-label`），未读完 lint 全部实现。
- ambiguity scan 在真实运行中返回过多少条问题、是否正是它扫出 #555 的两处歧义：未找到运行记录。
- 用户是否明确批准了 to-tickets 第 44 行的拆分判据：lightweight 汇总 `### 2.` 列为待选，现文已落地，但没找到记录用户选择的条目。
- triage 外来 issue 分支在 xiaohuangya 等其他消费仓是否发生过：只查了本仓与 agentflow。
- agentflow #620–#629 的关闭评论内容（「已直接改完」）未读，只核实了 label 与标题。

---

## 10. 线索材料核实记录

| 线索 | 采用的结论 | 状态 |
| --- | --- | --- |
| `M1-mmw-front.md` 第 25–29 行（front 各阶段表） | to-spec/to-tickets/publish/dispatch 交接顺序 | 已核实（与现文一致）。但第 27 行仍写 `acceptance` ticket 与标题 `# Cutting interface tickets`，已被 2026-09-29 vocabulary recheck T14/T15 改为 critical-flow ticket 与 `# Tickets from a screen contract`，线索过时。 |
| `T1-front.json` 组件 `spec` | 说 to-spec 模板「正文与上游逐字或近乎逐字一致」 | 不采用：按第 5 节比对，上游 493 词、现状 2509 词，模板 Implementation Decisions/Testing Decisions 均大改。 |
| `T1-front.json` 组件 `ambiguity` | 把 ambiguity scan 溯源到上游 quiz | 部分采用：quiz 是上游；scan 本身按 merge-note 来自 spec-kit，不是 mattpocock。 |
| `I5-mmw-field-evidence.json` I5-P1、P2、P4 | 判据不可判定、批次内互相打红、Owns 不足导致 bounce | P2 经提交 `d195e2a3` 核实；P4 经 issue #408 核实；P1 经 `lint_undecidable_checks` docstring 部分核实。 |
| `docs/reviews/2026-09-28-lightweight/to-spec.md` 定稿 | #555 两处产品空缺切票才发现 | 经 #555 修订评论核实。 |
| `docs/reviews/2026-09-28-lightweight/to-tickets.md` 定稿 | 158 张票从没缺过三节；标题错位 | 票数 85+74=159（`gh` 计数，与 158 相差一张，可能是其后新增）；三节未缺未逐张复查；标题错位未核实。 |
| `docs/reviews/2026-09-28-lightweight/triage.md` 结论 | 两仓 1300 张 issue 作者全是 `chancheuklap`；外来分支从未发生 | 已核实（585 + 717）。 |
| `docs/reviews/2026-09-28-lightweight/汇总.md` | 用户已定「triage 不当场修」；拆分判据待选 | 前者已读原文；后者见第 9 节。 |
| `docs/reviews/2026-09-23-skill-set/汇总.md` 第 45、46、98 行 | to-tickets 必须先有 spec；自有技能不合并上游 | 已核实（现文第 20 行、merge-note README）。 |
| `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` T13–T15、第 96 行 | spec division、page ticket、critical-flow ticket；`## Agent Brief` 不改名 | 已核实（现文与 CONTEXT 一致）。 |
| `docs/research/mmw-structure/2026-09-06-handoff.md` 第 56、129 行 | 引用 `to-tickets/SKILL.md:38`、`to-spec/SKILL.md:87` | 不采用：行号与内容已过时（2026-09-06 之后多次改写）。 |
| Nowledge Mem `77b341b7-…`「隔夜结果经早间分诊分流，to-spec 不必读子票」 | 夜的结果经 triage 回流，不由 to-spec 直接读 | 结论与现文一致（to-spec 不读 NIGHT SUMMARY）；记忆里的「to-spec 第 5 步修订」已过时（现为 `references/revising-a-spec.md`）。 |
| Nowledge Mem `d06fc6c2-…` | 删/改名 Owns 规则「不并入 main」 | 与现文不符（第 184 行已有），见第 5.2 节。 |
