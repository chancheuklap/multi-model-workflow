# N5：MMW 单元清点，其他上游技能（other upstream skills）

本报告只清点事实，不做"放哪一层、拆不拆"的归置决定。单元是 `mmw-v2/upstream/skills/` 下 18 个已安装的上游技能（`mmw-v2/skills.txt` 列出），外加未安装的 `engineering/ask-matt/`，作为"上游怎样做路由"的证据。

## 0. 范围、方法、读了什么

- **上游基线**：`git log --format=%H --grep "Squashed 'mmw-v2/upstream/'" -1` 得到 `5b1a4c513d027a598a277aa45892a6823381f9a9`（2026-09-18，上游 `c55ee460`）。每个文件都用 `git show 5b1a4c51:skills/<bucket>/<skill>/<file>` 取原文，再与现状 `diff`，行数和词数都是我实测的。
- **完整读过的**：单元内每个 `SKILL.md`、reference、`agents/openai.yaml`；对应的 merge-note（`mmw-v2/merge-notes/` 下 `README.md`、`prototype.md`、`wayfinder.md`、`grilling.md`、`grill-me.md`、`grill-with-docs.md`、`domain-modeling.md`、`codebase-design.md`、`improve-codebase-architecture.md`、`resolving-merge-conflicts.md`、`wizard.md`、`handoff.md`、`teach.md`、`to-questionnaire.md`、`wait-what.md`、`setup-matt-pocock-skills.md`、`writing-for-agents.md`）；已删除的 `ask-matt.md`（取自 `06163a0f^`）；每个改动文件对上游的完整 diff。
- **脚本**：`diagnosing-bugs/scripts/hitl-loop.template.sh` 全文读过（44 行）。`wizard/template.sh` 读了文件头、第 1–40 行、每个 helper 函数的注释头（第 31–170 行只读注释头，未逐行读实现）、第 150–204 行（`set_var`、`finish`、`STAGES` 段）。两者都是给 agent 复制后改写的模板，没有 `--help`，也不能直接运行（会阻塞等人输入），所以没跑。只跑了一条只读复现命令：`/bin/bash -c 'set -u; REGION=cn; echo "区域：$REGION，下一步"'`，输出 `REGION�: unbound variable`，退出码 127；改成 `${REGION}` 后正常（验证 wizard 的 merge-note）。
- **只读检索**：`grep` 全仓；`nmem --json m search` 三次；`~/.claude/projects/*/*.jsonl` 里按 `"skill":"<名>"`（Skill 工具调用）和 `<command-name>/<名></command-name>`（斜杠调用）统计文件数（只统计项目目录顶层会话文件，不含 `subagents/` 子目录，也没查 Codex、Grok、Pi、Cursor 的会话）。
- **线索材料**：`docs/reviews/2026-09-28-lightweight/` 下本单元 19 份报告与 `汇总.md`（全部读过）、`docs/reviews/2026-09-23-skill-set/汇总.md`（第 1–80 行读过，其余按关键词检索）、`docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md`（按关键词读相关表）、`docs/research/workflow-compare/reports/M1-mmw-front.md`、`C1-front-ui.json`、`C5-toolbox.json`、`C4a-upstream.json`、`I1`、`I5`（按关键词抽取）、`docs/research/mmw-structure/2026-09-06-handoff.md`（按关键词）。凡采用的结论，下文都标"已核实"（我回到原文或文件系统看过）或"未核实"（只来自线索材料）。
- **线索已过时的地方**：`M1-mmw-front.md` 与 `C1-front-ui.json`（2026-09-24）仍把 `ask-matt` 写成入口、把 `handoff` 写成 prototype 往返的桥、把 research 结果写在 `research/<name>` 临时分支上。这三点现在都不成立（`ask-matt` 已于 `06163a0f` 从 `skills.txt` 删除；`handoff` 往返已从 ask-matt 删掉；临时分支已从 `wayfinder` 第 5 步删掉），下文不采用。

### 总览：每个技能是不是"几乎原样可用的能力技能"

"流程写入"指本仓把 MMW 流水线的交接、存放位置、label、下一步写进了上游正文；"能力改变"指改变了技能本身怎么做那件事。

| 技能 | 与上游差多少（本文件 diff 行数） | 判断 | MMW 改动的性质 |
| --- | --- | --- | --- |
| `research` | 0 | 原样 | 无改动；MMW 的接线全在调用方（`wayfinder` 第 5 步、`implement`、`to-spec`） |
| `diagnosing-bugs` | 0 | 原样 | 无改动，没有 merge-note |
| `domain-modeling` | 0 | 原样 | 无改动；本仓 ADR 形状的连接在正文之外（`docs/agents/domain.md` `## Flag ADR conflicts`、`docs/adr/README.md`） |
| `grill-me` | 1 行 | 原样 | 只是 host 中立措辞 |
| `handoff` | 1 行 | 原样 | 只是 host 中立措辞 |
| `codebase-design` | 2 处 | 几乎原样 | 一句范围限定（防止改真实命令名）+ 一句"参考不是流程"；都改变 agent 行为，都不是流程写入 |
| `wizard` | 2 句 + 模板 3 行 | 几乎原样 | 两句写作规则（写明每步目的、`${NAME}`）+ 删未用变量；属于能力修正，不是流程写入 |
| `to-questionnaire` | description + 1 句 | 几乎原样 | 改成模型可触发（补触发句）；一句改写问题的判据；能力层面 |
| `wait-what` | 2 行 + 新文件 `VISUAL.md` | 能力扩展 | 新增 `visual` 分支（新能力），交给 `diagram-design` 画页 |
| `teach` | 6 个 diff 块 | 几乎原样 | 两处修上游未关 issue、两处改交付方式（嵌入组件、起 HTTP 服务）；能力层面 |
| `resolving-merge-conflicts` | 3 步各一句 + description | 能力扩展，带流程印记 | 新增"干净合并却检查变红"的分支；第 2 步写了 `origin/<base branch>`、first-parent merge commits、closeout evidence，这些是 MMW 流水线的名词 |
| `grilling` | 新增 18 行（约 580 词，是上游的 1.8 倍） | 能力加厚 | "只问属于用户的决定"一段 + 第一性原理摘录整块；是能力改变，不是流程写入 |
| `grill-with-docs` | 1 行扩成 3 句 | 接线 | 后两句：写入 `CONTEXT.md`/ADR 属于会话内动作；下一步交给 `to-spec`（流程写入） |
| `improve-codebase-architecture` | `SKILL.md` 7 处 + `HTML-REPORT.md` 大段重写 | 能力换底 + 流程写入 | 画图从 Tailwind/Mermaid CDN 换成 `diagram-design`（能力换底）；新增 `### 4. Hand the decision on` 交给 `to-spec`（流程写入） |
| `setup-matt-pocock-skills` | `SKILL.md` 10 个 diff 块、GitHub 种子加两节 | 大量流程写入 | 写明 tracker 就是流水线存储、默认 label 被脚本写死、`AGENTS.md` 的 `## External References` 格式、重跑保留落地件；种子加 `## Three label sets`、`mmw:map`、`--limit`/`--paginate` |
| `prototype` | `SKILL.md` 六条规则改了五条、`LOGIC.md`/`UI.md` 多处、新增 `EXP.md`、`evidence-page.md` | 能力改变 + 大量流程写入 | 能力改变：原型不再用完即扔、新增 EXP 分支；流程写入：`prototypes/<effort>/<issue>/<UI\|LOGIC\|EXP>/` 路径约定、`## State list` 格式（被脚本解析）、scaffolding 交给 `design-pages`、`## Next` |
| `wayfinder` | 上游正文逐字未动的段落占多数；`SKILL.md` 9 个 diff 块 + 新增 reference | 上游灵魂原样 + 流程写入 | `mmw:map` label、`## Notes` 写 effort 目录名、界面/重做两支（新 reference）、research subagent 交代、第 6 步交给 `to-spec` |
| `writing-for-agents` | `SKILL.md` 2 行 + 新增 `SKILL-SET-RULES.md`（5,390 词）、`REVIEWING-A-SKILL-SET.md`（1,075 词） | 上游部分原样；本仓部分是整套仓库规则 | 本仓两份文件是 MMW 技能集的写作规则与复审方法，不是能力 |
| `ask-matt`（未安装） | `SKILL.md` 74 行、`PHASE-BOUNDARIES.md` 22 行、`openai.yaml` 删 `policy` | 已被本仓改写后又整体退出安装 | 改写内容几乎全是流程写入（`dispatch`、`design-pages`、`write-screen-contract`、Yes/No 决定谁检查）；目录仍在，未恢复上游原文 |

---

## 1. 部件清单

"触发"一列：模型 = 模型可触发（`SKILL.md` 无 `disable-model-invocation`，`agents/openai.yaml` 无 `policy`）；用户 = 只由用户点名（两处都有，见 `mmw-v2/merge-notes/README.md` `## disable-model-invocation`）。`agents/openai.yaml` 每份都是 Codex 读的展示名与触发开关，下文不再逐个说。

| 技能 | 触发 | 文件 | 是什么、给谁用 |
| --- | --- | --- | --- |
| `prototype` | 模型 | `SKILL.md` | 分三枝（逻辑/UI/实现方式）的入口与六条通用规则；做原型的 agent 每次读 |
| | | `LOGIC.md` | 单文件 HTML 状态机演示的做法；只在逻辑枝读 |
| | | `UI.md` | 多个结构不同的 UI variant 挂在一条路由上、底部切换条的做法，以及 `## State list` 格式；只在 UI 枝读 |
| | | `EXP.md` | 本仓写：最小可运行实验、leaf `README.md` 六节、证据页；只在实现方式枝读 |
| | | `evidence-page.md` | 本仓写：实验证据页的两种形状、段落顺序、HTML 骨架；只在 `EXP.md` 第 4 步写生成器时读 |
| `wayfinder` | 模型（本仓删了上游的用户触发） | `SKILL.md` | 把大工作建成 tracker 上的 map + 决策票，两种模式（画图、逐票解）；画图与解票的 agent 每次读 |
| | | `references/interface-and-remake.md` | 本仓写：目的地有界面时加 design ticket 与 alignment ticket、重做已有产品时加挑选清单；只在 `### Chart the map` 第 4 步、目的地有 UI 或是重做时读 |
| `grilling` | 模型 | `SKILL.md` | 按 design tree 一轮轮访谈的原语，外加本仓的"只问属于用户的决定"与第一性原理思考块；被 `grill-me`、`grill-with-docs`、`wayfinder`、`triage`、`improve-codebase-architecture` 调用，也可直接触发 |
| `grill-me` | 用户 | `SKILL.md` | 一句话：读 `grilling` 并照做（无仓库、无记录） |
| `grill-with-docs` | 用户 | `SKILL.md` | 读 `grilling` 与 `domain-modeling`，边谈边写 `CONTEXT.md`/ADR，结束交给 `to-spec` |
| `domain-modeling` | 模型 | `SKILL.md` | 主动建词表、写 ADR 的纪律 |
| | | `CONTEXT-FORMAT.md` | `CONTEXT.md` / `CONTEXT-MAP.md` 模板与规则；写词条时读 |
| | | `ADR-FORMAT.md` | 上游 ADR 模板与门槛；写 ADR 时读（本仓 ADR 形状另见 `docs/adr/README.md`） |
| `codebase-design` | 模型 | `SKILL.md` | 深模块词汇表（module、interface、seam 等）与原则；被 `tdd`、`improve-codebase-architecture` 点名读 |
| | | `DEEPENING.md` | 按依赖类别深化一组浅模块；按 `## Going deeper` 的条件读 |
| | | `DESIGN-IT-TWICE.md` | 并行派多个子 agent 设计不同接口再比较；按条件读 |
| `improve-codebase-architecture` | 用户 | `SKILL.md` | 扫代码找深化机会、出 HTML 报告、挑一个进 grilling、交给 `to-spec` |
| | | `HTML-REPORT.md` | 报告页的内容、卡片、图型选择、固定画法、措辞；第 2 步写报告时读 |
| `research` | 模型 | `SKILL.md` | 派后台 agent 按一手来源调研、写一份带出处的 Markdown |
| `resolving-merge-conflicts` | 模型 | `SKILL.md` | 五步解合并冲突，本仓加"干净合并但检查变红"；worker 在 `implement` 第 1、8 步和 `dispatch.sh integrate` 的 stderr 指引下使用 |
| `diagnosing-bugs` | 模型 | `SKILL.md` | 六阶段排错（先造红色回路） |
| | | `scripts/hitl-loop.template.sh` | 需要人动手复现时，agent 复制并改写的交互脚本模板 |
| `wizard` | 模型 | `SKILL.md` | 为只有人能做的配置步骤生成交互式 bash 向导 |
| | | `template.sh` | 向导库 + 示例 stage；agent 复制后只写 `STAGES` 以下部分 |
| `handoff` | 用户 | `SKILL.md` | 把当前对话压成交接文档，存 OS 临时目录 |
| `teach` | 用户 | `SKILL.md` | 在一个教学工作区里跨会话教用户一个主题 |
| | | `MISSION-FORMAT.md`、`RESOURCES-FORMAT.md`、`LEARNING-RECORD-FORMAT.md`、`GLOSSARY-FORMAT.md` | 工作区里四类文件的模板与规则；写对应文件时读 |
| `to-questionnaire` | 模型（本仓删了用户触发） | `SKILL.md` | 为掌握缺失知识的另一个人写问卷，模板内联 |
| `wait-what` | 用户 | `SKILL.md` | 让 agent 用简单语言重讲上一条；带 `visual` 参数时走 `VISUAL.md` |
| | | `VISUAL.md` | 本仓写：用一页 HTML 重讲，页面交给 `diagram-design` |
| `setup-matt-pocock-skills` | 用户 | `SKILL.md` | 一个仓库跑一次：探查、问三节、写 `docs/agents/` 三份配置与 `AGENTS.md` 的行 |
| | | `issue-tracker-github.md` | GitHub tracker 种子（本仓加 `## Three label sets`、整表读取规则、`mmw:map`）；落地为 `docs/agents/issue-tracker.md` |
| | | `issue-tracker-gitlab.md`、`issue-tracker-local.md` | GitLab、本地 markdown 种子；MMW 流水线不走这两种（`SKILL.md` Section A 本仓句） |
| | | `triage-labels.md` | 五个 triage 角色到 label 字符串的映射种子 |
| | | `domain.md` | 领域文档读法种子；本仓落地件 `docs/agents/domain.md` 已按本仓布局重写 |
| `writing-for-agents` | 模型 | `SKILL.md` | 上游：写给 agent 的文档的通用杠杆（context pointer、两种负担、信息层级、完成判据、leading word、修剪） |
| | | `SKILL-MECHANICS.md` | 上游：frontmatter、模型/用户触发、路由技能；写的是技能时读 |
| | | `SKILL-SET-RULES.md` | 本仓写：MMW 技能集的全部技能文本规则（七条事实 + 检查 + 编辑 + 验证 + 范例表）；写、改、复审、修剪集合内技能时读；根 `AGENTS.md` `## External References` 指向它 |
| | | `REVIEWING-A-SKILL-SET.md` | 本仓写：复审一组技能的六步认知走查；只在复审时由 `SKILL-SET-RULES.md` 开头指过来 |
| `ask-matt`（未安装） | 若安装为模型 | `SKILL.md` | 路由表：主流程、on-ramp、代码健康、词汇层、阶段边界、独立技能、前置条件 |
| | | `PHASE-BOUNDARIES.md` | 阶段边界五问决策树与一手/二手来源权衡 |

单元之外但与单元直接相连、下文会引用的文件：`mmw-v2/merge-notes/README.md`（merge-note 用法、`disable-model-invocation` 配对、host 中立）；`mmw-v2/tests/lib/check_upstream_em_dashes.py`（`mmw-v2/upstream/skills/` 下 `.md` 不许有破折号）；`mmw-v2/tests/lib/check_own_skill_frontmatter.py`（已安装技能 frontmatter 必须是合法 YAML）；`docs/agents/issue-tracker.md`、`docs/agents/domain.md`、`docs/agents/triage-labels.md`（`setup-matt-pocock-skills` 的落地件）。

---

## 2. 内容分类表

八类之外我只自拟了一类，**词汇定义**（术语与它的定义），因为 `codebase-design`、`writing-for-agents`、`domain-modeling` 的主体就是它，硬塞进八类会失真。description 的归类写作"重入与分派（触发）"：它决定 host 何时加载这份技能，host 每次启动都读。

"来源"：上 = 上游原文；本 = 本仓写或改。"读者与时刻"：每次 = 该技能每次运行都读；分支 = 只有某一枝读。

### 2.1 `prototype`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| `SKILL.md` description | 重入与分派（触发） | 本（加第三类触发"work out how a feature should be implemented"） | host 启动时 |
| `SKILL.md` 开头 "A prototype is **code that answers a question**…" | 目的与立场 | 本（删 throwaway，写"留在仓库、持续迭代、正式代码以它为参考"） | 每次 |
| `## Pick a branch` 三枝 + 模糊时的默认 | 重入与分派；带理由的规则（"getting this wrong wastes the whole prototype"） | 上 + 本（第三枝、默认表加 experiment） | 每次 |
| 规则 1 leaf directory `prototypes/<effort>/<issue>/<UI\|LOGIC\|EXP>/`、`<effort>` 取名顺序 | 格式与模板；命令与接口（跨技能约定，被 `design-pages`、`write-screen-contract` 引用） | 本（整条改写） | 每次 |
| 规则 2 一条命令起、逻辑演示能发布就发布 | 做法 | 上 + 本 | 每次 |
| 规则 3 不持久化 | 带理由的规则（"Persistence is the thing the prototype is _checking_"） | 上 | 每次 |
| 规则 4 不打磨、不写测试、只留一条清楚边界 | 带理由的规则 | 上 + 本（测试归正式代码、放宽"不抽象"） | 每次 |
| 规则 5 暴露状态、实验写证据页 | 做法 | 上 + 本 | 每次 |
| 规则 6 结论进 leaf `README.md`、下游读者句、UI winner 不在此折进、leaf 目录是唯一的家、链为 asset | 目的与立场（谁读 README、做浅的代价）；顺序（先记结论再折进）；带理由的规则 | 本（整条改写） | 每次 |
| `LOGIC.md` 开头、`## When this is the right shape` | 目的与立场；重入与分派（"wrong branch, use UI.md"） | 上 | 逻辑枝 |
| `LOGIC.md` `### 1`–`### 5` | 顺序；做法；第 1 步问题同时写进 README、第 3 步第二段发布成在线页、第 5 步 HTML 壳留在 leaf 目录（本） | 上 + 本 | 逻辑枝 |
| `LOGIC.md` `## Anti-patterns` | 带理由的规则 | 上 | 逻辑枝 |
| `UI.md` 开头、`## When this is the right shape` | 目的与立场；重入与分派 | 上 + 本（"the rest stay as reference"） | UI 枝 |
| `UI.md` `## Two sub-shapes`、A、B | 带理由的规则（"A prototype route on its own is a vacuum"）；重入与分派 | 上 + 本（throwaway route → prototype route） | UI 枝 |
| `UI.md` `### When there is no app yet` | 重入与分派；做法 | 本 | UI 枝，只在全新产品 |
| `UI.md` `### 1`、`### 2` | 做法；带理由的规则（"it's wallpaper"）；第 2 步末句样式用变量（本） | 上 + 本 | UI 枝 |
| `UI.md` `### 3` 切换组件伪代码 + 本仓末段（variant 住 leaf 目录、mount point 是 scaffolding、第一次 pull 后拆） | 格式与模板；做法；命令与接口（与 `design-pages` `references/pull.md` 的约定） | 上 + 本 | UI 枝 |
| `UI.md` `### 4`、`### 5` | 做法 | 上 | UI 枝 |
| `UI.md` `### 6` `## State list` 格式、scaffolding 留到第一次 pull | 格式与模板（`pull_design.py` 按 `^## State list`、`###`、列表项解析）；带理由的规则（"the winner running behind it is the reference the pages are drawn against"） | 本 | UI 枝 |
| `UI.md` `## Anti-patterns` | 带理由的规则 | 上 | UI 枝 |
| `UI.md` `## Next` | 重入与分派（交给 `design-pages`） | 本 | UI 枝 |
| `EXP.md` 开头、`## When this is the right shape` | 目的与立场；重入与分派 | 本 | 实验枝 |
| `EXP.md` `## The README` 六节 | 格式与模板 | 本 | 实验枝 |
| `EXP.md` `## Process` 1–5，每步 `Done when` | 顺序；做法；带理由的规则（"An experiment without a bar answers nothing; it just runs"） | 本 | 实验枝 |
| `EXP.md` `## Anti-patterns` | 带理由的规则 | 本 | 实验枝 |
| `evidence-page.md` 全文 | 格式与模板（两种形状、段落顺序、样式、HTML 骨架） | 本 | 实验枝第 4 步写生成器时 |

### 2.2 `wayfinder`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| description 末两句 "Use when … Not for a well-scoped feature…" | 重入与分派（触发） | 本（判据取自 `ask-matt`） | host 启动时 |
| 开头两段（fog、destination） | 目的与立场 | 上 | 每次 |
| `## Plan, don't do` | 目的与立场（"The pull to just do the work is usually the signal you've reached the edge of the map"） | 上 | 每次 |
| `## Refer by name` | 带理由的规则 | 上 | 每次 |
| `## The Map` 前两段（index not store） | 带理由的规则 | 上 + 本（加 `mmw:map`） | 每次 |
| `## The Map` 第三段（tracker 位置由 tracker 文档说；没给就让用户跑 `setup-matt-pocock-skills`） | 命令与接口（指向 `docs/agents/issue-tracker.md` `## Wayfinding operations`） | 上 + 本（host 中立措辞） | 每次 |
| `### The map body` 模板 | 格式与模板 | 上 + 本（`## Notes` 加 effort 目录名） | 画图时写，解票时读 |
| `### Tickets`（`## Question` 模板、claim、native blocking、frontier 定义） | 格式与模板；带理由的规则（"essential because it renders the frontier _visually_"）；命令与接口 | 上 | 每次 |
| `## Ticket Types` 四类 | 重入与分派（类型 → 用哪个技能）；带理由的规则（HITL 不代答） | 上 + 本（host 中立：读 `SKILL.md` / 用 host 的 general-purpose subagent） | 每次 |
| `## Fog of war`、`**Fog or ticket?**` | 目的与立场；带理由的规则（"whether you can state the question precisely now") | 上 | 每次 |
| `## Out of scope` | 带理由的规则 | 上 | 每次 |
| `## Invocation` 两种模式 + 一次只解一张票 | 重入与分派 | 上 | 每次 |
| `### Chart the map` 1–6 | 顺序；第 3 步 `mmw:map`（本）；第 4 步指向 reference（本）；第 5 步 research subagent 的完整交代（本，替换上游 throwaway 分支） | 上 + 本 | 画图分支 |
| `### Work through the map` 1–5 | 顺序；重入（用户点名的票或 frontier 第一张，先 claim） | 上 + 本（host 中立） | 解票分支 |
| `### Work through the map` 第 6 步（无开着的子票且 Not yet specified 空 → 交给 `to-spec`、map 不关） | 顺序；重入与分派（下一步交给谁） | 本 | 解票分支，地图清空时 |
| 末句 "The user may run unblocked tickets in parallel" | 带理由的规则 | 上 | 解票分支 |
| `interface-and-remake.md` `## A destination with an interface` 第一段 | 目的与立场（两处决定各自完整、不相接） | 本 | 画图第 4 步，目的地有 UI |
| 同节第二、三段（两张票的阻塞、开头一行点名技能） | 顺序；格式与模板；带理由的规则（"Their type labels would otherwise send whoever picks them up to the wrong skill"） | 本 | 同上 |
| 同节第四段（两条常设规则写进 map 的 `## Notes`） | 重入与分派（让之后每个会话都接上） | 本 | 同上 |
| `## A destination that remakes an existing product` | 带理由的规则；做法（挑选清单逐项带路径、新 effort 名、并存票） | 本 | 画图第 4 步，重做 |
| 末行 `Done when` | 完成判据（归"顺序"） | 本 | 同上 |

### 2.3 `grilling`、`grill-me`、`grill-with-docs`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| `grilling` 第 6 行 design tree | 目的与立场 | 上 | 每次 |
| 第 8 行 rounds、frontier | 做法；顺序 | 上 | 每次 |
| 第 10–22 行问法格式（❓/➡️） | 格式与模板 | 上 | 每次 |
| 第 24 行重算 frontier | 顺序；带理由的规则 | 上 | 每次 |
| 第 26 行"事实归 agent、决定归用户" | 目的与立场 | 上 | 每次 |
| 第 28 行 "Put to the user only the decisions that are theirs…" | 带理由的规则（收窄第 26 行后半） | 本（本仓新写，不是摘录） | 每次 |
| 第 30 行 "Think through the paragraphs below…Where the path is already clear, first principles is overkill." | 重入与分派（这一整块只进推荐答案、不加轮次、路径清楚就跳过） | 本 | 每次 |
| 第 32–44 行（质疑前提、减需求、约束分类、"惯例不是理由"、从 primitives 重建并先删后优化、失败的三层归因） | 目的与立场 + 做法（思考方式） | 本（2026-09-16 摘录自外部参考，用户裁定逐句保留） | 每次，形成每道推荐答案时 |
| 第 46 行 "The session is done when the frontier is empty…Do not act on it until the user confirms" | 带理由的规则（完成判据） | 上 | 每次 |
| `grill-me` 第 7 行 | 重入与分派（交给 `grilling`） | 上 + 本（host 中立） | 每次 |
| `grill-with-docs` 第 7 行第一句 | 重入与分派（交给两份技能） | 上 + 本（host 中立） | 每次 |
| `grill-with-docs` 第 7 行后两句（写入属于会话内；下一步 `to-spec`，同一会话） | 带理由的规则；重入与分派 | 本 | 每次 |

### 2.4 `domain-modeling`、`codebase-design`、`improve-codebase-architecture`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| `domain-modeling` `SKILL.md` 开头（active discipline） | 目的与立场 | 上 | 每次 |
| `## File structure` | 格式与模板 | 上 | 每次 |
| `### Challenge…`、`### Sharpen…`、`### Discuss concrete scenarios`、`### Cross-reference with code` | 做法 | 上 | 每次 |
| `### Update CONTEXT.md inline` | 带理由的规则（"a glossary and nothing else"） | 上 | 每次 |
| `### Offer ADRs sparingly` 三门槛 | 带理由的规则 | 上 | 每次 |
| `CONTEXT-FORMAT.md` | 格式与模板；带理由的规则 | 上 | 写词条时 |
| `ADR-FORMAT.md` | 格式与模板；带理由的规则（`## When to offer an ADR`、`### What qualifies`） | 上 | 写 ADR 时（本仓实际形状以 `docs/adr/README.md` 为准） |
| `codebase-design` 开头段 | 目的与立场 | 上 | 每次 |
| 第 10 行 "This skill is a reference, not a process…" | 重入与分派（没有别的任务驱动时答完就停） | 本 | 每次 |
| `## Glossary` 首段（本仓加范围限定：只管设计散文，已有命令名、判据类别名、程序打印的字面量不改） | 带理由的规则 | 上 + 本 | 每次 |
| `## Glossary` 词条、`## Relationships`、`## Rejected framings` | 词汇定义（自拟）；带理由的规则 | 上 | 每次 |
| `## Deep vs shallow`、`## Principles`、`## Designing for testability` | 带理由的规则；做法 | 上 | 每次 |
| `## Going deeper` | 重入与分派（每个指针带条件） | 上 | 每次 |
| `DEEPENING.md` | 做法；带理由的规则 | 上 | 分支 |
| `DESIGN-IT-TWICE.md` | 顺序（框定 → 并行派子 agent → 比较）；格式与模板（子 agent 输出五项） | 上 | 分支 |
| `improve-codebase-architecture` 开头与"informed by" | 目的与立场；重入与分派（读 `codebase-design`） | 上 + 本（host 中立） | 每次 |
| `### 1. Explore` | 带理由的规则（"Scope before you scan: YAGNI"）；做法 | 上 | 每次 |
| `### 2.` 写临时文件、打开 | 命令与接口 | 上 | 每次 |
| `### 2.` 第二段（页面与图交给 `diagram-design`，免 §3 确认） | 重入与分派；带理由的规则 | 本 | 每次 |
| `### 2.` 卡片字段、Top recommendation、词汇、ADR 冲突、"Do NOT propose interfaces yet" | 格式与模板；带理由的规则 | 上 | 每次 |
| `### 3. Grilling loop` | 顺序；重入与分派（`grilling`、`domain-modeling`、design-it-twice） | 上 + 本（host 中立） | 用户挑中候选后 |
| `### 4. Hand the decision on` | 目的与立场（本技能不改代码）；重入与分派（交给 `to-spec`） | 本 | 用户确认决定后 |
| `HTML-REPORT.md` 开头、`## Header`、`## Candidate card` | 格式与模板 | 上 + 本（颜色换成 `diagram-design` 的角色名、页脚一行） | 第 2 步 |
| `## Candidate card` 末段 "The reader knows nothing about this topic…" | 带理由的规则（读者与图字分工） | 本（替掉上游一句） | 第 2 步 |
| `## Diagrams`（图型对照、同一 viewBox、固定画法、强调色规则） | 做法；格式与模板 | 本（替掉上游 Mermaid/手绘三节） | 第 2 步 |
| `## Top recommendation section`、`## Tone` | 格式与模板；带理由的规则 | 上 | 第 2 步 |

### 2.5 `research`、`resolving-merge-conflicts`、`diagnosing-bugs`、`wizard`、`handoff`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| `research` 第 6 行 "Spin up a background agent…" | 目的与立场（保护调用者的上下文）；重入与分派 | 上 | 每次 |
| `research` `Its job` 1–3 | 做法；带理由的规则（"Follow every claim back to the source that owns it"） | 上 | 每次 |
| `resolving-merge-conflicts` description | 重入与分派（触发） | 本（加 clean merge 变红） | host 启动时 |
| 第 1 步 | 顺序；做法；本仓加无冲突标记时抓第一条失败检查 | 上 + 本 | 每次 |
| 第 2 步 | 做法；带理由的规则（"Understand deeply why each change was made"）；本仓加 `origin/<base branch>` 的 first-parent merge commits、票与 closeout evidence | 上 + 本 | 每次（本仓句只在干净合并分支） |
| 第 3 步 | 带理由的规则（保两边意图、不发明新行为、不 `--abort`）；本仓加"沿失败路径跨票追踪" | 上 + 本 | 每次 |
| 第 4、5 步 | 顺序；命令与接口 | 上 | 每次 |
| `diagnosing-bugs` 开头 | 目的与立场 | 上 | 每次 |
| `## Redact` | 带理由的规则 | 上 | 每次 |
| `## Phase 1`（建回路、收紧、非确定性、建不出来时、完成判据） | 目的与立场（"This is the skill"、"Be aggressive. Be creative. Refuse to give up."）；做法；带理由的规则；完成判据 | 上 | 每次 |
| `## Phase 2`–`## Phase 6` | 顺序；做法；带理由的规则；完成判据清单 | 上 | 每次 |
| `hitl-loop.template.sh` | 格式与模板；命令与接口（`step`、`capture`，结尾打印 `KEY=VALUE`） | 上 | Phase 1 第 10 种回路时复制 |
| `wizard` 开头三段 | 目的与立场；带理由的规则（模板已解决 UX，"Your job is only to scope the procedure and author its stages"；默认一次性） | 上 | 每次 |
| `### 1. Scope the procedure` | 顺序；做法；完成判据 | 上 | 每次 |
| `### 2. Map each stage's journey` | 做法；带理由的规则；本仓加"写明每步要达成什么、凭记忆的路径加 `note`" | 上 + 本 | 每次 |
| `### 3. Author the wizard` | 做法；命令与接口（helper 名单）；本仓加 `${NAME}` 规则 | 上 + 本 | 每次 |
| `### 4. Verify and hand off` | 顺序；做法（静态追踪，不端到端跑） | 上 | 每次 |
| `template.sh` 库区 | 命令与接口（`stage`、`say`/`step`、`note`、`warn`、`open_url`、`pause`、`confirm`、`ask`/`ask_secret`、`write_env`、`set_secret`/`set_var`、`finish`） | 上 + 本（删未用的 `RED`、`/wizard` 改散文） | 第 3 步复制 |
| `template.sh` `STAGES` 示例 | 格式与模板 | 上 | 第 3 步替换 |
| `handoff` 全文五句 | 做法（存临时目录、suggested skills 一节、不复制已有产物、脱敏、按参数裁剪） | 上 + 本（句尾去工具名） | 每次 |

### 2.6 `teach`、`to-questionnaire`、`wait-what`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| `teach` 开头 stateful | 目的与立场 | 上 | 每次 |
| `## Teaching Workspace` 文件清单 | 格式与模板 | 上 + 本（工作区不是技能目录、在别的项目里先问；加 `GLOSSARY.md` 一项） | 每次 |
| `## Philosophy`、`### Fluency vs Storage Strength` | 目的与立场 | 上 | 每次 |
| `## Lessons` | 做法；本仓加读者段、起本地 HTTP 服务交付并说明 `file://` 的理由 | 上 + 本 | 每次 |
| `## Assets`、`### Self-contained pages` | 做法；带理由的规则（为何嵌入）；命令与接口（`<!--CSS-->`/`<!--JS-->` 标记、`./assets/build.py`） | 上 + 本（Self-contained 整节是本仓） | 每次 |
| `## The Mission`、`## Zone Of Proximal Development`、`## Knowledge`、`## Skills`、`## Acquiring Wisdom`、`## Reference Documents`、`## NOTES.md` | 目的与立场；带理由的规则；做法 | 上 | 每次 |
| 四个 `*-FORMAT.md` | 格式与模板；带理由的规则 | 上 | 写对应文件时 |
| `to-questionnaire` description | 重入与分派（触发） | 本（改成模型可触发、补 Use when） | host 启动时 |
| 开头、"Grill the send, not the subject" | 目的与立场 | 上 | 每次 |
| 步骤 1–3（每步 Done when） | 顺序；做法 | 上 | 每次 |
| "The user's open questions are rarely the ones to send…" | 带理由的规则 | 本 | 每次 |
| `## Document structure` 与内联模板 | 格式与模板 | 上 | 每次 |
| `wait-what` `SKILL.md` 重讲那一句 | 做法 | 上 | 每次 |
| `argument-hint` 与 "With the argument `visual`…" | 重入与分派 | 本 | 每次读，只有带 `visual` 时跳转 |
| `VISUAL.md` 开头两段 | 目的与立场；带理由的规则（标签用 `CONTEXT.md` 词汇） | 本 | `visual` 分支 |
| `## Put the page where the user is looking` | 重入与分派（按能力选呈现面） | 本 | `visual` 分支 |
| `## Draw the page` | 重入与分派（交 `diagram-design`，免 §3）；带理由的规则（读者段） | 本 | `visual` 分支 |

### 2.7 `setup-matt-pocock-skills`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| 开头三项、"prompt-driven skill" | 目的与立场 | 上 | 每次 |
| 第 17 行 "What you write here is read at the moment of acting by every skill…" | 目的与立场（谁读、写错的代价） | 本 | 每次 |
| `### 1. Explore` | 做法（清单） | 上 + 本（改查 `## External References` 行） | 每次 |
| `### 2.` Section A/B/C 与推荐答案 | 重入与分派；带理由的规则 | 上 | 每次 |
| Section A 本仓句（tracker 就是流水线存储，选别的开不了夜） | 带理由的规则 | 本 | 每次 |
| Section B 本仓句（脚本写死默认 label，流水线仓库保持默认） | 带理由的规则 | 本 | Section B 跑时 |
| Section C 本仓句（已有 `CONTEXT-MAP.md` 即多 context） | 带理由的规则 | 本 | 每次 |
| `### 3. Confirm and edit` | 顺序 | 上 + 本 | 每次 |
| `### 4. Write`（`## External References` 行、`CLAUDE.md` 只放 `@AGENTS.md`、落地件是本仓记录只补不改） | 格式与模板；带理由的规则 | 本（替换上游 `## Agent skills` 块与"挑文件"规则） | 每次 |
| `### 5. Done` | 顺序 | 上 | 每次 |
| `issue-tracker-github.md` `## Conventions`（含本仓 "Every list read is a whole list"） | 命令与接口；带理由的规则 | 上 + 本 | 写落地件时；落地后由每个发布/分诊技能读 `docs/agents/issue-tracker.md` |
| `## Three label sets` | 命令与接口（layer/queue/grade 三套 label 与谁打） | 本 | 同上 |
| `## Pull requests as a triage surface`、`## When a skill says …` | 命令与接口 | 上 | 同上 |
| `## Wayfinding operations` | 命令与接口（map、child、blocking、frontier、claim、resolve 的 `gh` 命令） | 上 + 本（`mmw:map`、`--paginate`、排除 `mmw:spec`） | 同上；`wayfinder` 读 |
| `issue-tracker-gitlab.md`、`issue-tracker-local.md` | 命令与接口 | 上（只有 host 中立措辞） | 只在选这两种 tracker 时 |
| `triage-labels.md` | 格式与模板 | 上（例子换成 `ready-for-agent`） | 同上；`triage` 读落地件 |
| `domain.md` 种子 | 做法；格式与模板 | 上（只有 host 中立措辞） | 写落地件时 |

### 2.8 `writing-for-agents`

| 文件 · 段 | 类型 | 来源 | 读者与时刻 |
| --- | --- | --- | --- |
| description | 重入与分派（触发） | 本（"modifying AGENTS.md or CLAUDE.md" 放宽为 "writing any document an agent will consume"） | host 启动时 |
| 开头段 + 第 8 行两个分支指针 | 目的与立场；重入与分派 | 上 + 本（第二个指针指向 `SKILL-SET-RULES.md`） | 每次 |
| `## Context pointers`、`## The two loads`、`## Information hierarchy`、`## Steps and completion criteria`、`## When to split`、`## Leading words`、`## Pruning` | 词汇定义（自拟）；带理由的规则 | 上 | 每次 |
| `SKILL-MECHANICS.md` | 带理由的规则（模型/用户触发的取舍、路由技能"can only hint, never fire them"） | 上 | 写的是技能时 |
| `SKILL-SET-RULES.md` 开头与 `## What skill text is for` 七条事实 | 目的与立场（技能交接理解、脚本管确定的事、注意力是预算、先指挥再信任、按分支渐进加载、技能按名字组合、每样东西只有一个家） | 本 | 写/改/复审/修剪集合内技能时 |
| `## Checks`：`### Load and disclosure` | 带理由的规则（moment、jump、fragment、规则写在执行者读的文本里） | 本 | 同上 |
| `### Redundancy and bloat` | 带理由的规则（duplication、cache、no-op、over-specification、over-defense、sediment 表、"These stay"） | 本 | 同上 |
| `### Scripts and judgement` | 带理由的规则 | 本 | 同上 |
| `### Descriptions` | 带理由的规则（只写触发、不点 host 名；配对规则指回 merge-notes README） | 本 | 同上 |
| `### Vocabulary` | 带理由的规则（选词顺序、false friend、标识符不改名、英文、词表完整） | 本 | 同上 |
| `### Hand-offs` | 带理由的规则（hand-off 定义、每个结果谁读、unguided choice、点名技能的写法） | 本 | 同上 |
| `### Prompts written for other agents` | 带理由的规则 | 本 | 同上 |
| `### Upstream skills` | 带理由的规则（上游能不改就不改、先在边缘接线、改动对应 merge-note） | 本 | 同上 |
| `### Paths and host neutrality` 与其后的 grep 检查说明 | 带理由的规则；命令与接口（手工 grep 清单：host 名、工具名、runner 名） | 本 | 同上 |
| `### Rules and completion criteria`、`### Examples`、`### Refusals…` | 带理由的规则 | 本 | 同上 |
| `## Editing` | 做法；带理由的规则（先减后加、新增机制要指出出事的那次运行、讲目的的段落不是机制） | 本 | 同上 |
| `## Verifying` + `Done when` | 顺序（完成判据） | 本 | 同上 |
| `## Upstream examples` 表 | 做法（范例指针，读法：从 squash 提交读原文） | 本 | 同上 |
| `REVIEWING-A-SKILL-SET.md` 开头三段 | 目的与立场（认知走查、两类证据） | 本 | 只在复审一组技能时 |
| 第 1–6 步 | 顺序（每步 `Done when`）；格式与模板（第 5 步报告顺序） | 本 | 同上 |

### 2.9 `ask-matt`（未安装，作证据）

| 文件 · 段 | 类型 | 来源 |
| --- | --- | --- |
| 第 8、10、12 行（为什么问、读者是谁、flow/main flow/on-ramp 概念） | 目的与立场；第 10 行本仓加"路线第一步是用户点名技能时怎么办" | 上 + 本 |
| `## The main flow` 1–3、`### Context hygiene` | 重入与分派（路由）；带理由的规则（第 1–3 步留在同一上下文、smart zone） | 上 + 本（第 2 步界面段、第 3 步 Yes/No 与谁检查、`dispatch`、`implement`/`code-review` 那段） |
| `## On-ramps`、`## Codebase health`、`## Vocabulary underneath`、`## Standalone`、`## Precondition` | 重入与分派；目的与立场（每条说明何时用、何时不用） | 上 + 本（host 中立、去向改成 MMW 技能、本仓加地图边界一段） |
| `## Phase boundaries` 与 `PHASE-BOUNDARIES.md` | 带理由的规则（五问决策树、"Continue" 先排除、一手/二手来源表、"These are judgement calls"） | 上 + 本（host 中立：命令名改成动作名） |

---

## 3. 连线

### 3.1 对外交接（产出什么、谁读）

| 技能 | 产出 | 读者 |
| --- | --- | --- |
| `prototype` | leaf 目录 `prototypes/<effort>/<issue>/<UI\|LOGIC\|EXP>/` 与其 `README.md`（结论、`## State list`）；UI scaffolding；实验证据页（`.scratch/…`，不提交） | `to-spec` 第 1 步读到结论（已核实 `to-spec/SKILL.md` 第 12 行）；`to-tickets` 把原型目录放进 `## Read first`（已核实第 174 行）；`implement` 读 leaf `README.md` 到结论并当 baseline（已核实第 16 行）；`design-pages` `SKILL.md` 第 25 行读 `## State list`；`pull_design.py` 解析 `## State list`；`design-pages` `references/pull.md` 第 22 行拆 scaffolding |
| `wayfinder` | tracker 上 map issue（`wayfinder:map`、`mmw:map`）、决策子票（`wayfinder:<type>`）、阻塞边、resolution comment、map 的 `## Decisions so far`；有界面时 design ticket、alignment ticket | `to-spec`（map 清空后，读 Decisions so far 与每张关闭票的 resolution comment）；`mmw-v2/board/board_data.py`（按 `mmw:map` 列 map，已核实文件含该字串）；`design-pages`、`write-screen-contract`（两张界面票首行点名）；`docs/contexts/tickets/CONTEXT.md` **decision ticket** 把 resolution comment 定为 baseline 来源 |
| `grilling` | 与用户的共同理解（会话内）；无文件 | 调用方：`wayfinder` 票的 resolution、`triage` notes、`to-spec` |
| `grill-with-docs` | `CONTEXT.md` 词条、ADR；下一步 `to-spec` | 所有读词表的技能（`implement`、`to-spec`、`to-tickets`、`code-review`） |
| `domain-modeling` | `CONTEXT.md`、`docs/adr/*.md` | 同上；本仓 ADR 格式以 `docs/adr/README.md` 为准 |
| `codebase-design` | 无文件；词汇 | `tdd`（`SKILL.md` 第 26 行点名）、`improve-codebase-architecture`；`code-review` `references/standards-reviewer.md` 抄了 deletion test |
| `improve-codebase-architecture` | OS 临时目录 `architecture-review-<timestamp>.html`；词表/ADR；交给 `to-spec` 的决定 | 用户；`to-spec` |
| `research` | 仓库惯例目录（本仓 `docs/research/`）下一份带出处 Markdown | `to-spec`（Sources、决定句末引用）、`to-tickets` `## Read first`、`implement`（读"回答问题的那部分"，已核实第 16 行）；`wayfinder` research 票的 resolution comment |
| `resolving-merge-conflicts` | 合并提交；`Decisions I made on my own` 里的取舍 | `implement` 的 closeout；`reverify` |
| `diagnosing-bugs` | 回归测试、修复、提交信息里的正确假设 | 下一个排错的人；在票里时由 `implement` 收尾 |
| `wizard` | 一份 bash 向导脚本（默认一次性）；`.env`、GitHub secrets | 用户 |
| `handoff` | OS 临时目录里的交接文档 | 新会话 |
| `teach` | 教学工作区：`MISSION.md`、`lessons/`、`reference/`、`learning-records/`、`GLOSSARY.md`、`assets/`、`NOTES.md` | 用户与后续 teach 会话 |
| `to-questionnaire` | 当前目录 `to-questionnaire-<slug>.md` | 收件人；回答再进 `grill-with-docs` 或 `to-spec`（这句只写在已退役的 `ask-matt` 里） |
| `wait-what` | 对话里的重讲，或一页 HTML | 用户 |
| `setup-matt-pocock-skills` | `docs/agents/issue-tracker.md`、`triage-labels.md`、`domain.md`；`AGENTS.md` `## External References` 行；`CLAUDE.md` | `to-spec`、`to-tickets`、`triage`（缺配置时点名本技能）、`wayfinder`（`## Wayfinding operations`、`## Three label sets`）、每个探查代码的技能（`domain.md`） |
| `writing-for-agents` | 无文件；规则 | 写技能的 agent、`retro`（`SKILL.md` 第 145 行写 `prompt_change` 前读它）、根 `AGENTS.md` `## External References` 指向 `SKILL-SET-RULES.md`；`check_upstream_em_dashes.py`、`check_own_skill_frontmatter.py` 在文件头引用它 |

### 3.2 点名调用、运行的脚本、引用的文档

- `wayfinder` 点名 `grilling`、`domain-modeling`（读 `SKILL.md`，同一会话）、`prototype`（读 `SKILL.md`）、`research`（交给 host 自带 general-purpose subagent）、`setup-matt-pocock-skills`（缺 tracker 配置时让用户跑）、`to-spec`、`to-tickets`（第 6 步）；reference 点名 `write-screen-contract`、`design-pages`。读 `docs/agents/issue-tracker.md` 的 `## Wayfinding operations` 与 `## Three label sets`。
- `grill-me` → `grilling`；`grill-with-docs` → `grilling`、`domain-modeling`、`to-spec`。
- `improve-codebase-architecture` → `codebase-design`、`grilling`、`domain-modeling`、`diagram-design`、`to-spec`。
- `wait-what` `VISUAL.md` → `diagram-design`。
- `prototype` `UI.md` → `design-pages`。
- `diagnosing-bugs` → 自带 `scripts/hitl-loop.template.sh`。`wizard` → 自带 `template.sh`。
- 入边：`implement` 第 1、8 步与 `dispatch.sh`（第 2520 行 stderr "Resolve this merge with the resolving-merge-conflicts skill"）→ `resolving-merge-conflicts`；`tdd` → `codebase-design`；`triage` 第 4 步 → `grilling`、`domain-modeling`；`to-spec`、`to-tickets`、`triage` → `setup-matt-pocock-skills`；`write-screen-contract` `SKILL.md` 第 115 行与 `design-pages` `references/pull.md` 第 37 行 → 回到 `wayfinder` 记录结论；`retro` → `writing-for-agents`。
- 被 `diagnosing-bugs`、`research`、`to-questionnaire`、`wizard`、`teach`、`handoff`、`wait-what` 指向的调用方：除已退役的 `ask-matt` 外，没有任何已安装技能点名它们（全仓 `grep` 已核实）；它们只靠 description 或用户点名进入。

```edges
host-startup -> prototype : reads (description)
host-startup -> wayfinder : reads (description)
skills.txt -> prototype : configured-by
skills.txt -> ask-matt : configured-by (removed in 06163a0f; not installed)
prototype/SKILL.md -> prototype/LOGIC.md : reads (logic branch)
prototype/SKILL.md -> prototype/UI.md : reads (UI branch)
prototype/SKILL.md -> prototype/EXP.md : reads (experiment branch)
prototype/EXP.md -> prototype/evidence-page.md : reads (step 4)
prototype -> prototypes/<effort>/<issue>/<UI|LOGIC|EXP>/README.md : writes
prototype/UI.md -> design-pages : hands-off-to (## Next)
design-pages/SKILL.md -> prototypes/.../README.md#State list : reads
design-pages/scripts/pull_design.py -> prototypes/.../README.md#State list : reads (parses)
design-pages/references/pull.md -> prototype UI scaffolding : removes (self-coined: tears-down)
implement -> prototypes/.../README.md : reads (Read first, baseline)
to-spec -> prototypes/.../README.md : cites
to-tickets -> prototypes/<effort>/... : cites (Read first)
wayfinder -> grilling : calls
wayfinder -> domain-modeling : calls
wayfinder -> prototype : calls
wayfinder -> research : hands-off-to (host general-purpose subagent)
wayfinder -> setup-matt-pocock-skills : cites (hard-dependency pointer)
wayfinder -> docs/agents/issue-tracker.md : reads (## Wayfinding operations, ## Three label sets)
wayfinder/SKILL.md -> wayfinder/references/interface-and-remake.md : reads (UI or remake destination)
wayfinder -> tracker:map issue : writes (labels wayfinder:map, mmw:map)
wayfinder -> tracker:decision ticket : writes (resolution comment)
wayfinder/interface-and-remake.md -> write-screen-contract : hands-off-to (alignment ticket opening line)
wayfinder/interface-and-remake.md -> design-pages : hands-off-to (design ticket opening line)
wayfinder -> to-spec : hands-off-to (map clear, fresh session)
write-screen-contract -> wayfinder : re-enters-at (record alignment ticket resolution)
design-pages/references/pull.md -> wayfinder : re-enters-at (record design ticket resolution)
mmw-v2/board/board_data.py -> tracker:map issue : reads (mmw:map)
to-spec -> tracker:map issue : reads (Decisions so far, resolution comments)
grill-me -> grilling : calls
grill-with-docs -> grilling : calls
grill-with-docs -> domain-modeling : calls
grill-with-docs -> to-spec : hands-off-to
grill-with-docs -> CONTEXT.md : writes
domain-modeling -> CONTEXT.md : writes
domain-modeling -> docs/adr/ : writes
domain-modeling/SKILL.md -> domain-modeling/CONTEXT-FORMAT.md : reads
domain-modeling/SKILL.md -> domain-modeling/ADR-FORMAT.md : reads
docs/agents/domain.md -> docs/adr/README.md : cites (ADR shape overrides ADR-FORMAT.md)
triage -> grilling : calls
triage -> domain-modeling : calls
tdd -> codebase-design : calls
codebase-design/SKILL.md -> codebase-design/DEEPENING.md : reads (conditional)
codebase-design/SKILL.md -> codebase-design/DESIGN-IT-TWICE.md : reads (conditional)
code-review/references/standards-reviewer.md -> codebase-design : cites (deletion test copied)
improve-codebase-architecture -> codebase-design : calls
improve-codebase-architecture -> grilling : calls
improve-codebase-architecture -> domain-modeling : calls
improve-codebase-architecture -> diagram-design : calls
improve-codebase-architecture/SKILL.md -> improve-codebase-architecture/HTML-REPORT.md : reads (step 2)
improve-codebase-architecture -> to-spec : hands-off-to
research -> docs/research/ : writes
to-spec -> docs/research/ : cites
implement -> docs/research/ : reads (Read first, baseline)
implement -> resolving-merge-conflicts : hands-off-to (step 1, step 8)
dispatch.sh integrate -> resolving-merge-conflicts : hands-off-to (stderr names it)
diagnosing-bugs -> diagnosing-bugs/scripts/hitl-loop.template.sh : runs-script (copied and edited)
wizard -> wizard/template.sh : runs-script (copied; agent writes STAGES only)
teach/SKILL.md -> teach/*-FORMAT.md : reads
wait-what/SKILL.md -> wait-what/VISUAL.md : reads (visual argument)
wait-what/VISUAL.md -> diagram-design : calls
to-questionnaire -> to-questionnaire-<slug>.md : writes
handoff -> OS temp handoff doc : writes
setup-matt-pocock-skills -> docs/agents/issue-tracker.md : writes
setup-matt-pocock-skills -> docs/agents/triage-labels.md : writes
setup-matt-pocock-skills -> docs/agents/domain.md : writes
setup-matt-pocock-skills -> AGENTS.md#External References : writes
setup-matt-pocock-skills -> CLAUDE.md : writes
to-spec -> setup-matt-pocock-skills : cites
to-tickets -> setup-matt-pocock-skills : cites
triage -> setup-matt-pocock-skills : cites
verify-ticket.py -> docs/agents/issue-tracker.md#Three label sets : cites (label definitions live in verify-ticket.py)
writing-for-agents/SKILL.md -> writing-for-agents/SKILL-MECHANICS.md : reads (writing a skill)
writing-for-agents/SKILL.md -> writing-for-agents/SKILL-SET-RULES.md : reads (skill in a set)
writing-for-agents/SKILL-SET-RULES.md -> writing-for-agents/REVIEWING-A-SKILL-SET.md : cites (review branch)
AGENTS.md -> writing-for-agents/SKILL-SET-RULES.md : cites
retro -> writing-for-agents : calls (before prompt_change)
tests/lib/check_upstream_em_dashes.py -> mmw-v2/upstream/skills/**/*.md : lints (self-coined)
tests/lib/check_own_skill_frontmatter.py -> SKILL.md frontmatter : lints (self-coined)
merge-notes/README.md -> merge-notes/<skill>.md : cites
merge-notes/prototype.md -> ask-matt : cites (stale: skill uninstalled)
merge-notes/wayfinder.md -> ask-matt : cites (stale: skill uninstalled)
ask-matt -> grill-with-docs : hands-off-to (routing, archival)
ask-matt -> wayfinder : hands-off-to (routing, archival)
ask-matt/SKILL.md -> ask-matt/PHASE-BOUNDARIES.md : reads
```

自拟关系：`lints`（测试库脚本检查文件）、`removes`（拆除另一技能留下的东西）。

---

## 4. 重复

全部用 `grep -rn` 在 `mmw-v2/`、`docs/`、`AGENTS.md`、`CONTEXT-MAP.md`、`CODING_STANDARDS.md` 里查过（排除 `docs/reviews/`、`docs/research/`、上游 `docs/` 页与 CHANGELOG）。

### 4.1 真重复（同一个意思写在两处以上）

| # | 内容 | 位置 | 说明 |
| --- | --- | --- | --- |
| R1 | "The reader knows nothing about this topic. Pictures show…" 整段 | `teach/SKILL.md:56`、`wait-what/VISUAL.md:18`、`improve-codebase-architecture/HTML-REPORT.md:24`（逐字相同） | 三份 merge-note 都写"改一处，三处一起改"。三个技能各自在动手时只加载自己那份 |
| R2 | leaf 目录约定与 `<effort>` 取名 | Home 在 `prototype/SKILL.md` 规则 1；`UI.md:36`、`UI.md:83` 复述 UI 路径；`docs/contexts/ui-acceptance/CONTEXT.md:131/135/138` 词条复述；`wayfinder/SKILL.md:37` 模板写 effort 目录名；`write-screen-contract/references/screen-contract-format.md:12` 注释 | 词条复述是词表设计；`wayfinder` 模板那一处是写入点，不是定义 |
| R3 | `## State list` 的格式与位置 | `prototype/UI.md` 第 6 步（定义）、`design-pages/SKILL.md:25`、`design-pages/references/design-system.md`、`pull_design.py`（解析）、`docs/contexts/ui-acceptance/CONTEXT.md` **state list** | 定义一处，读者多处 |
| R4 | `## Three label sets` 一节 | 种子 `setup-matt-pocock-skills/issue-tracker-github.md` 与落地件 `docs/agents/issue-tracker.md` | 两节逐字相同（`diff` 为空，已核实）；label 的颜色与说明只在 `verify-ticket.py` 定义 |
| R5 | "Every list read is a whole list" | 种子与落地件 | 已漂移：落地件多了 "acting on part of a set is not a short answer but a wrong one" 和指向 `## Reading a tree` 的一句（`diff` 已核实） |
| R6 | `## Wayfinding operations` | 种子与落地件 | 已漂移：落地件把 "Child ticket"、"Blocking" 改名为 "Decision ticket"、"Blocking edge"，frontier 一条多了与夜间 frontier 区分的一句；种子没跟 |
| R7 | ADR 三道门槛；"懒建目录" | `domain-modeling/SKILL.md` `### Offer ADRs sparingly` 与 `ADR-FORMAT.md` `## When to offer an ADR`；"lazily" 在 `SKILL.md`、`CONTEXT-FORMAT.md`、`ADR-FORMAT.md` 各一次 | 上游内部重复 |
| R8 | deletion test | `codebase-design/SKILL.md` `## Principles`、`improve-codebase-architecture/SKILL.md` 第 1 步、`code-review/references/standards-reviewer.md:22` | `merge-notes/code-review.md:35` 写明是照抄给 Standards axis 用的 |
| R9 | 词汇禁令（不说 component、service、API、boundary） | `codebase-design` `## Glossary`、`improve-codebase-architecture/SKILL.md:13` 与 `:54`、`HTML-REPORT.md` `## Tone` | 上游内部四处；本仓的范围限定只写在 `codebase-design`，`improve` 的 merge-note 明写靠它 |
| R10 | 保留 `disable-model-invocation` 的七个技能名单 | `mmw-v2/merge-notes/README.md` `## disable-model-invocation`，另在 `merge-notes/improve-codebase-architecture.md:11`、`merge-notes/teach.md:22` 各抄"另外六个" | README 同节写"下面每份说明只写它那个 skill 站在哪一边，不复述这条规则"；2026-09-28 定稿要求删掉这些副本，`grill-me`、`grill-with-docs`、`handoff` 已改，这两份没改（已核实） |
| R11 | 会话命令的 host 中立固定句 "Emptying a session's context and compressing it into a summary both exist on every host…" | 规则在 `SKILL-SET-RULES.md:118`；实例只在 `ask-matt/SKILL.md:65`、`ask-matt/PHASE-BOUNDARIES.md:9` | `ask-matt` 已退役，现在没有任何已安装文件带这一句 |
| R12 | `setup-matt-pocock-skills` 的 `CLAUDE.md` 形状与 `manage-agents-md` `## Write` 第 4 步 | `setup-matt-pocock-skills/SKILL.md` 第 4 步；`manage-agents-md/SKILL.md:157` | merge-note 写明是为了不让两个技能互相拆台而对齐的；同一条规则两处 |
| R13 | 词表条目复述 `SKILL-SET-RULES.md` 的术语 | `docs/contexts/toolbox/CONTEXT.md` 第 219–311 行，二十多条 `_Home_` 指向 `SKILL-SET-RULES.md` 或 `REVIEWING-A-SKILL-SET.md` | 按 `SKILL-SET-RULES.md` `### Vocabulary`"词表完整"的要求而存在 |
| R14 | "只问属于用户的决定、工程选择自己定" | `grilling/SKILL.md:28` 与用户级 prompt `mmw-v2/prompt/shared.md:15`（rule 1） | 同一个意思；merge-note 记录理由：访谈现场 agent 只照眼前技能，全局规则压不住上游第 26 行 |
| R15 | `improve-codebase-architecture` 卡片字段 | `SKILL.md` 第 2 步（叫 `Benefits`）与 `HTML-REPORT.md` `## Candidate card`（叫 `Wins`，每条 ≤6 词） | 上游内部，写法略有出入 |
| R16 | `wizard` helper 名单 | `SKILL.md` 第 35 行与 `template.sh` 函数定义 | 上游内部的 cache |
| R17 | host 中立的写法 | `mmw-v2/merge-notes/README.md` `## host 中立` 与 `SKILL-SET-RULES.md` `### Paths and host neutrality`、`### Hand-offs` | README 明说写法在 `SKILL-SET-RULES.md`，自己只记取舍规则；基本不重复 |

### 4.2 只是同词（意思不同）

| 词 | 各处意思 | 位置 |
| --- | --- | --- |
| frontier | `grilling`：前提已定的一批决定；`wayfinder`：map 下 open、unblocked、unclaimed 的子票；夜间：`status.py` 算出的可派票 | `grilling/SKILL.md:8`；`wayfinder/SKILL.md` `### Tickets`；`docs/contexts/tickets/CONTEXT.md:238`（词条只区分 wayfinder 与夜间，没提 grilling） |
| round | `grilling`：一批 frontier 问题；`wayfinder` 第 78、110 行 "run this round as both describe"：指整场访谈（这是本仓 host 中立改写时引入的措辞）；tickets 词条：修一条判据并重跑的一轮；`EXP.md`：**experiment round** | `docs/reviews/2026-09-29-vocabulary-recheck/DECISIONS.md` W3 把 bare round 留给 tickets 的意思；`wayfinder` 的"run this round"在 2026-09-28 `grilling` 报告里已记录为冲突，未改（已核实第 78、110 行原文） |
| effort | `<effort>`：开发工作的目录名；`models.json` 的 `effort`：推理强度 | `docs/contexts/ui-acceptance/CONTEXT.md:138` 与 toolbox **`effort`** 互相点名（DECISIONS W6） |
| seam | `codebase-design`（Feathers 定义）与 `tdd` "the public boundary you test at" | 词表 `docs/contexts/tickets/CONTEXT.md:79` 取 `codebase-design` 的定义并把两份列为 `_Home_`（DECISIONS "seam takes codebase-design's whole definition"） |
| prototype | 本单元的原型 vs `diagnosing-bugs` Phase 6 "Throwaway prototypes deleted"（调试临时代码） | 两个上游语境，不冲突 |
| handoff | `handoff` 技能 vs 本机非 MMW 技能 `orca-cli` 的 "handoff" 触发 vs 历史用词 "handoff package"（已改名 design package） | 2026-09-28 `handoff` 报告；DECISIONS 残留清单 |
| 失败分析的数字 | `grilling` "5–7 different possible sources…1–2"；`diagnosing-bugs` "3–5 ranked hypotheses" | 场景不同（访谈推荐答案 vs 有复现回路的排错） |

---

## 5. 上游差异

行数：`git show 5b1a4c51:…` 与现文件 `wc -l`；diff 行数是 `diff` 输出里以 `<`/`>` 开头的行数。下表之外的文件与上游逐字节相同：`domain-modeling` 的三份 `.md`、`codebase-design/DEEPENING.md` 与 `DESIGN-IT-TWICE.md`、`research/SKILL.md`、`diagnosing-bugs/SKILL.md` 与 `scripts/hitl-loop.template.sh`、`teach` 的四个 `*-FORMAT.md`、`writing-for-agents/SKILL-MECHANICS.md`，以及除下表列出的四份（`wayfinder`、`to-questionnaire`、`wait-what`、`ask-matt`）之外的全部 `agents/openai.yaml`。

### 5.1 行数

| 文件 | 上游行 | 现行 | diff 行 | 词数（上游 → 现） |
| --- | --- | --- | --- | --- |
| `prototype/SKILL.md` | 26 | 27 | 19 | 487 → 795 |
| `prototype/LOGIC.md` | 67 | 69 | 10 | 1,025 → 1,093 |
| `prototype/UI.md` | 112 | 121 | 29 | 1,118 → 1,372 |
| `prototype/EXP.md`、`evidence-page.md` | 无 | 67、64 | 新增 | 0 → 874、442 |
| `wayfinder/SKILL.md` | 128 | 128 | 26 | 2,000 → 2,249 |
| `wayfinder/references/interface-and-remake.md` | 无 | 17 | 新增 | 0 → 572 |
| `wayfinder/agents/openai.yaml` | 5 | 3 | 2（删 `policy`） | |
| `grilling/SKILL.md` | 28 | 46 | 18 | 319 → 902 |
| `grill-me/SKILL.md` | 7 | 7 | 2 | 22 → 28 |
| `grill-with-docs/SKILL.md` | 7 | 7 | 2 | 35 → 94 |
| `codebase-design/SKILL.md` | 114 | 116 | 4 | 851 → 930 |
| `improve-codebase-architecture/SKILL.md` | 71 | 75 | 18 | 899 → 995 |
| `improve-codebase-architecture/HTML-REPORT.md` | 123 | 69 | 104 | 924 → 802 |
| `resolving-merge-conflicts/SKILL.md` | 14 | 14 | 8 | 133 → 217 |
| `wizard/SKILL.md` | 44 | 44 | 4 | 673 → 774 |
| `wizard/template.sh` | 204 | 204 | 6 | |
| `handoff/SKILL.md` | 16 | 16 | 2 | 138 → 135 |
| `teach/SKILL.md` | 140 | 147 | 15 | 1,488 → 1,721 |
| `to-questionnaire/SKILL.md` | 54 | 55 | 5 | 470 → 541 |
| `to-questionnaire/agents/openai.yaml` | 5 | 3 | 2（删 `policy`） | |
| `wait-what/SKILL.md` | 7 | 10 | 3 | 60 → 85 |
| `wait-what/VISUAL.md` | 无 | 18 | 新增 | 0 → 263 |
| `wait-what/agents/openai.yaml` | 5 | 5 | 2 | |
| `setup-matt-pocock-skills/SKILL.md` | 116 | 100 | 44 | 1,008 → 1,246 |
| `setup-matt-pocock-skills/issue-tracker-github.md` | 45 | 74 | 41 | 553 → 852 |
| `setup-matt-pocock-skills/issue-tracker-gitlab.md`、`-local.md`、`domain.md`、`triage-labels.md` | 46、30、51、15 | 同 | 4、2、4、2 | |
| `writing-for-agents/SKILL.md` | 81 | 81 | 4 | 1,777 → 1,819 |
| `writing-for-agents/SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` | 无 | 176、33 | 新增 | 0 → 5,390、1,075 |
| `ask-matt/SKILL.md` | 90 | 96 | 74 | 1,769 → 2,319 |
| `ask-matt/PHASE-BOUNDARIES.md` | 55 | 57 | 22 | 699 → 737 |
| `ask-matt/agents/openai.yaml` | 5 | 3 | 2（删 `policy`） | |

另有两份上游文档页被本仓改过（不装进 host）：`mmw-v2/upstream/docs/engineering/resolving-merge-conflicts.md`（12 行）、`improve-codebase-architecture.md`（4 行），各自 merge-note 有记。

### 5.2 每处改动：类型、merge-note、性质

"能力"= 改变技能怎么做那件事；"流程"= 把 MMW 的交接、位置、label、下一步写进上游；"中立"= host 中立措辞（`the Skill tool`、`/名字` 改成散文点名）。

| 技能 · 改动 | 内容类型 | merge-note 条目 | 性质 |
| --- | --- | --- | --- |
| `prototype` description 第三类触发 | 触发 | `prototype.md` frontmatter 行 | 能力（新增实现方式一枝） |
| `prototype` 开头去 throwaway、`LOGIC.md`/`UI.md` 多处去 throwaway | 目的与立场 | `总原则`、各行 | 能力（处置方式从"推临时分支"改为"留在仓库迭代"） |
| `prototype` Pick a branch 第三枝、`EXP.md`、`evidence-page.md` | 分派；顺序；格式 | `Pick a branch` 行、`### EXP.md、evidence-page.md` | 能力 |
| `prototype` 规则 1 leaf 目录与 `<effort>` | 格式；命令与接口 | 规则 1 行 | 流程（跨技能路径约定，被 `design-pages`、`write-screen-contract` 读） |
| `prototype` 规则 2、5 覆盖三枝、发布在线页 | 做法 | 规则 2、5 行 | 能力 |
| `prototype` 规则 4 测试归正式代码、边界放宽 | 带理由的规则 | 规则 4 行 | 能力 |
| `prototype` 规则 6 下游读者句、UI winner 交 Claude Design、链为 asset | 目的与立场；分派 | 规则 6 行、`SKILL.md 第 6 条` 行 | 流程（spec/ticket/worker 如何用 README；Claude Design 路线） |
| `UI.md` `### When there is no app yet` | 分派 | 对应行 | 能力（全新产品的做法） |
| `UI.md` 第 2 步末句样式用变量 | 做法 | 第 2 步末句行 | 流程（为 design system 准备） |
| `UI.md` 第 3 步 leaf 目录 + scaffolding | 做法；接口 | 第 3 步末尾新增段 | 流程（与 `design-pages` 拆除对接） |
| `UI.md` 第 6 步 `## State list` 与保留 scaffolding | 格式 | 第 6 步各行 | 流程（`pull_design.py` 解析格式） |
| `UI.md` `## Next` | 分派 | `## Next` 行 | 流程 |
| `wayfinder` 删 `disable-model-invocation`、`policy` | 触发 | frontmatter 行、`openai.yaml` 行 | 触发方式 |
| `wayfinder` description 末两句 | 触发 | description 行 | 触发条件 |
| `wayfinder` `mmw:map`（`## The Map`、第 3 步） | 命令与接口 | label 行 | 流程（任务板四层分类） |
| `wayfinder` `## Notes` 写 effort 目录名 | 格式 | `The map body` 行 | 流程 |
| `wayfinder` 第 4 步指向 reference + 整份 reference | 分派；顺序；目的 | reference 三行 | 流程（与 `design-pages`、`write-screen-contract` 对接） |
| `wayfinder` 第 5 步 research subagent 交代、删 throwaway 分支 | 顺序；做法 | 第 5 步行 | 能力 + 流程（防嵌套派发；结果落在仓库供 spec 引用） |
| `wayfinder` 第 6 步 | 顺序；分派 | 第 6 步行 | 流程（交给 `to-spec`） |
| `wayfinder` Ticket Types、第 1 步、解票第 3 步、tracker 指针 | 分派 | host 中立行 | 中立 |
| `grilling` 第 28 行 | 带理由的规则 | 唯一一行（第一部分） | 能力（收窄"决定都归用户"） |
| `grilling` 第 30–44 行 | 目的与立场；做法 | 唯一一行（第二部分） | 能力（思考方式） |
| `grill-me`、`handoff` 各一处 | 分派 | 正文行 | 中立 |
| `grill-with-docs` 后两句 | 规则；分派 | "正文那一句之后新增两句" | 能力（写入时机）+ 流程（交给 `to-spec`） |
| `codebase-design` 范围限定 | 带理由的规则 | `## Glossary` 行 | 能力（防止改真实名字） |
| `codebase-design` "reference, not a process" | 分派 | 开头段之后行 | 能力（防当流程跑，上游 issue #449） |
| `improve-codebase-architecture` 第 2 步交 `diagram-design`、`HTML-REPORT.md` 删 Scaffold/Diagram patterns/Style guidance、加 `## Diagrams`、颜色角色 | 分派；做法；格式 | 第 2 步行、`HTML-REPORT.md` 各行 | 能力换底（出图机制换成本仓的设计系统） |
| `HTML-REPORT.md` 读者段 | 带理由的规则 | `## Candidate card` 末段行 | 能力 |
| `improve-codebase-architecture` `### 4.` | 目的；分派 | `### 4.` 行 | 流程（交给 `to-spec`，不在此重构） |
| `improve-codebase-architecture` 几处点名 | 分派 | host 中立行 | 中立 |
| `resolving-merge-conflicts` description 与第 1–3 步 clean-merge 分支 | 触发；做法 | 两行（#340） | 能力扩展，措辞含流程名词（`origin/<base branch>`、closeout evidence） |
| `wizard` 第 2、3 步各一句、`template.sh` 删 `RED`、去 `/` | 规则；接口 | 三行（agentflow #594） | 能力 |
| `teach` 工作区位置句、`GLOSSARY.md` 一项 | 规则；格式 | 两行（上游 #377、#559） | 能力（修上游未关 issue） |
| `teach` 读者段、HTTP 交付、`### Self-contained pages`、删 "and link to it" 等 | 规则；做法 | `总原则` 与各行 | 能力 |
| `to-questionnaire` 删 `policy`/`disable-model-invocation`、description | 触发 | frontmatter、description 行 | 触发方式 |
| `to-questionnaire` 改写问题一句 | 带理由的规则 | 第 3 步之后新增行 | 能力 |
| `wait-what` `argument-hint`、`visual` 分支句、`VISUAL.md`、`openai.yaml` 描述 | 分派；目的；做法 | 三段 + `VISUAL.md` 表 | 能力（新分支） |
| `setup-matt-pocock-skills` 第 17 行 | 目的与立场 | "prompt-driven…之后" 行 | 流程（这些文件被流水线读） |
| Section A、B 本仓句 | 规则 | 两行 | 流程（只认 GitHub 与默认 label） |
| Section C 本仓句 | 规则 | Section C 行 | 能力（按已有 `CONTEXT-MAP.md` 判断） |
| 第 1、3、4 步 `## External References`、`CLAUDE.md`、指针替换、落地件只补不改 | 格式；规则 | 四行 | 流程（`manage-agents-md` 的 `AGENTS.md` 格式） |
| 种子 `issue-tracker-github.md` 整表读取、`--limit 500`、`--paginate`、`## Three label sets`、`mmw:map`、排除 `mmw:spec` | 命令与接口；规则 | 种子表各行 | 流程（整表读取也是能力修正：agentflow spec #537 只看到 30/37 张子票） |
| 种子 `triage-labels.md` 例子 | 格式 | 对应行 | 中立措辞修正 |
| 种子 `gitlab`、`local`、`domain.md` 点名 | 分派 | host 中立行 | 中立 |
| `writing-for-agents` description 放宽 | 触发 | description 行 | 触发条件 |
| `writing-for-agents` 第 8 行指向 `SKILL-SET-RULES.md` | 分派 | 对应行 | 流程（接到本仓规则） |
| `SKILL-SET-RULES.md`、`REVIEWING-A-SKILL-SET.md` | 见 2.8 | 两节 | 本仓整份规则 |
| `ask-matt` 全部改写 | 分派；规则 | 已随 `06163a0f` 删除（原文见 `06163a0f^:mmw-v2/merge-notes/ask-matt.md`） | 流程（几乎全部） |

### 5.3 merge-note 与现文不一致、或已过时的地方（已核实）

1. `merge-notes/wayfinder.md` 第 20 行把"issue tracker 没给你"那一句放在 `## Plan, don't do` 里；实际在 `wayfinder/SKILL.md` `## The Map` 第 24 行。
2. `merge-notes/setup-matt-pocock-skills.md` `### domain.md（种子）`（第 50–59 行）三行"弃上游"描述的是落地件 `docs/agents/domain.md`，种子 `domain.md` 对上游只有两处 host 中立改动。2026-09-28 报告已指出，未改。
3. `merge-notes/improve-codebase-architecture.md:11`、`merge-notes/teach.md:22` 仍抄七技能名单（见 R10）。
4. `merge-notes/prototype.md:59`、`wayfinder.md:21`、`triage.md:12` 仍以 `ask-matt` 作依据或"一致"对象，而 `ask-matt` 已退出安装。
5. `06163a0f` 的提交说明称 `ask-matt/` 目录是 "an unmodified copy of the mattpocock/skills subtree"。实际 `SKILL.md` diff 74 行、`PHASE-BOUNDARIES.md` 22 行、`openai.yaml` 删了 `policy`；且 merge-note 已删，下次 subtree pull 时这些本仓改写按 README 默认"取上游"处理。
6. `SKILL-SET-RULES.md` `### Paths and host neutrality` 要求"点名会话命令的文件带一次固定句"，唯一带它的文件是已退役的 `ask-matt`。
7. `improve-codebase-architecture/SKILL.md` 第 71 行说 design-it-twice "asks your host for its own general-purpose subagents"，而 `codebase-design/DESIGN-IT-TWICE.md` 原文是 "Spawn 3+ sub-agents"，并没有 "general-purpose" 的说法。两句不矛盾，但前者描述了后者没写的东西。

---

## 6. 价值证据

使用量（Claude Code，`~/.claude/projects/*/*.jsonl` 顶层会话文件数，已核实；未含 subagent 子目录与其他 host）：

| 技能 | Skill 工具调用文件数 | 斜杠调用文件数 |
| --- | --- | --- |
| `writing-for-agents` | 20 | 13 |
| `wayfinder` | 4 | 20 |
| `grilling` | 19 | 0 |
| `domain-modeling` | 15 | 1 |
| `wait-what` | 0 | 11 |
| `handoff` | 0 | 10 |
| `prototype` | 7 | 0 |
| `resolving-merge-conflicts` | 4 | 2 |
| `grill-with-docs` | 3 | 2 |
| `teach` | 2 | 0 |
| `grill-me` | 0 | 2 |
| `wizard`、`codebase-design` | 各 1 | 0 |
| `research`、`diagnosing-bugs`、`improve-codebase-architecture`、`to-questionnaire`、`setup-matt-pocock-skills`、`ask-matt` | 0 | 0 |

`diagnosing-bugs` 在 Codex 上有使用：`~/.codex/sessions/2026/09/18/rollout-2026-09-18T19-43-44-…jsonl`（agentflow #997 的夜间 worker）存在，含 "diagnosing-bugs" 11 处（已核实存在与命中数；会话内容未读，"worker 写了 4 条可证伪假设"来自 2026-09-28 报告，未核实）。

| 部件或段落 | 防的是什么失败 | 证据 | 核实 |
| --- | --- | --- | --- |
| `prototype` 规则 6 下游读者句 | leaf `README.md` 只写指针，worker 读不到决定 | `prototypes/task-board/546/UI/README.md` 至 `551`、`547`、`548` 各 13 行，写"决定的细节写在 #546 的解决评论里"；worker 因此出错的实例没有 | 指针写法已核实；失败是推断 |
| `prototype` leaf 目录约定、`## State list` | 各会话各起目录名；pull 与 contract 对不上状态 | 仓库现有 9 个 leaf 目录（8 个 UI、1 个 EXP、0 个 LOGIC）；5 份 README 有 `## State list`；`pull_design.py` 解析它；merge-note 引任务板试点 #541 | 目录与文件已核实；#541 未核实 |
| `prototype` 处置方式（留在仓库） | 原型推到本地临时分支后 spec/worker 读不到 | Memory `6512963a`（2026-08-26）记录用户改造决定；`758016b2`（2026-08-21）"原型改为仓库内长期迭代的研究件" | 已核实 |
| `UI.md` `### When there is no app yet` | 全新产品时 agent 自造顶层路由 | `2c6ea8b5` 提交说明 "Gaps found walking eight workflow scenarios: prototype UI.md: variants for a product with no app yet"；是推演出的缺口，不是真实事故 | 来源已核实；失败未发生过 |
| `wayfinder` 上游灵魂段（开头、Plan don't do、Fog of war、Out of scope） | agent 冲向终点、预切迷雾、把范围外的当迷雾 | `SKILL-SET-RULES.md` 把它们当"技能交接理解"的范例；2026-09-28 报告与上游主干逐字比对一致 | 范例引用已核实；效果无直接证据 |
| `wayfinder` 第 6 步"无开着的子票" | 并行会话下用 frontier 判清空会过早交给 `to-spec` | 从 frontier 定义推出；没有真实并行的记录 | 推断 |
| `wayfinder` 第 5 步 research 交代 | subagent 再派一层；结果在未推送分支上 | 上游 issue #530、agentflow #592（2026-09-28 报告） | 未核实 |
| `wayfinder` `mmw:map` | 任务板看不到 map | `board_data.py` 含 `mmw:map` | 代码引用已核实 |
| `interface-and-remake.md` 两张界面票 + `## Notes` 常设规则 | 设计与后端决定各自完成却不相接；后来的决定票没接成阻塞 | merge-note 引"变色龙的界面因此接了空"、#541/#542 试点 | 未核实 |
| `interface-and-remake.md` 重做一节 | 旧产物留在原路径、新合同写到旧目录 | 同一 `2c6ea8b5` 说明 "wayfinder: the remake's selection list names old artifacts to delete; new effort name"；推演得出，从未真实走过 | 来源已核实；无运行证据 |
| `grilling` 第一性原理块 | 优化一个不该存在的东西；把惯例当约束；找到第一个原因就收手 | Memory `09af4c99`、`9c133aa5`、`eb828995`（2026-09-16 用户裁定：原文摘录、精确修剪、不改工作流、"惯例不是理由"一段不动） | 裁定已核实；效果无运行证据 |
| `grilling` 第 28 行 | 把工程问题抛给用户；问题没有背景 | `~/.claude/history.jsonl` 里 8 次点名访谈中 5 次用户要求"给背景、说直白、能自己定的别问"（2026-09-28 报告） | 未核实 |
| `grill-with-docs` 后两句 | 只加载一半没留记录；结束后不知下一步 | 上游文档页称"most reported problem"；本仓无观察 | 推断 |
| `grill-with-docs` 等 7 个保持用户触发 | 与 `grilling`/`codebase-design` 抢触发；夜里无人回答 | 2026-09-23 汇总"恢复成上游原样"一条 | 已核实（汇总原文） |
| `codebase-design` 范围限定 | agent 为了用词纪律改真实命令名 `boundary-check.py`、`BOUNDARY OK` | 无事故；正常输入可达 | 推断 |
| `codebase-design` "reference, not a process" | 当流程跑、派 subagent、重探已知代码 | 上游 issue #449；本仓未发生 | 未核实 |
| `improve-codebase-architecture` 出图规则 | 各图各画、与图型规则相撞；半栏宽字太小 | `b898a009`、`6702fd42`（2026-09-18，两次冷启动试跑） | 提交主题已核实 |
| `improve-codebase-architecture` `### 4.` | 同一会话直接重构、绕过 spec 与验收 | 无运行记录（Claude 会话 0 次调用，已核实） | 推断 |
| `resolving-merge-conflicts` clean-merge 分支 | 两张票各自绿、合并后红 | #340 立项；`reason` 为 `checks` 的 bounce 未见；agentflow #915 冲突链走通（2026-09-28 报告） | 未核实 |
| `diagnosing-bugs` 全文 | 没有红色回路就开始猜 | agentflow #997 会话（见上） | 部分核实 |
| `wizard` `${NAME}` 句 | 中文文案让 bash 3.2 在 `set -u` 下退出 | 本次复现：`$REGION，` 退出码 127，`${REGION}` 正常 | 已核实 |
| `wizard` "写明每步目的"句、删 `RED` | 控制台改版后人找不到按钮；agent 为消 shellcheck 警告改库区 | agentflow #594（2026-09-28 报告与汇总） | 未核实 |
| `teach` 工作区位置句、`GLOSSARY.md` 项 | 课件写进技能目录（即冻结的安装工作树）；词汇表无入口 | 上游 issue #377、#559；learn-jev 工作区（2026-09-28 报告） | 未核实 |
| `teach` 自足页面、HTTP 交付 | 单独预览时无样式；`file://` 跨目录链接失效 | merge-note 自述 `file://` 行为"未实测" | 无证据（未实测） |
| `to-questionnaire` 模型触发 + description | host 判断不了何时加载 | 无使用（Claude 会话 0 次） | 推断 |
| `wait-what` `VISUAL.md` 标签句 | 页面用 agent 自起的名字 | 两轮改写丢失后恢复；无失败观察 | 推断 |
| `setup-matt-pocock-skills` 本仓句 | 选了本地 markdown 开不了夜；label 改名分叉；重跑覆盖手工维护的节；旧指针块重复 | xiaohuangya 缺 label（2026-09-28 报告）；Memory `610dbea8` 提醒重跑先备份（报告引）；重跑从未发生 | 未核实；重跑相关为推断 |
| 种子"Every list read is a whole list" | 读一半的集合看起来完整 | agentflow spec #537 37 张子票只见 30 张（merge-note） | 未核实 |
| `SKILL-SET-RULES.md` 全文 | 技能文本漂移、重复、过度防御、删掉"为什么" | 2026-09-23 复审 441 条发现、162 条第二轮仍成立（I5 引汇总）；2026-09-28 定稿 F1–F13 已全部落在现文（我逐条比对了 F1、F2、F4、F5、F7、F8、F12、F13 的原句）；frontmatter lint 的真实事故（`advisor`、`ui-acceptance` 描述非法 YAML，`d37a6048`）写在 `check_own_skill_frontmatter.py` 文件头 | 已核实 |
| `ask-matt` | 用户记不住技能 | Claude 会话 0 次调用；2026-09-28 报告称 Codex 只有一次调研时打开；`06163a0f` 以"description 已在 runtime、各技能结尾点名下一步"为由删除 | 调用次数已核实 |

---

## 7. 约束

| 约束 | 出处 | 约束了什么 |
| --- | --- | --- |
| 上游能不改就不改，只接线；为文风改的恢复原文；接线先在边缘做 | `SKILL-SET-RULES.md` `### Upstream skills`；Memory `411750f5`（2026-09-23 用户裁定） | `research`、`diagnosing-bugs`、`domain-modeling` 保持逐字节相同；`resolving-merge-conflicts` 的缺口改在 `implement` 调用行；`domain-modeling` 的 ADR 形状差异放在 `docs/agents/domain.md` |
| 改了上游必须有 merge-note，条目说行为 | `SKILL-SET-RULES.md` `### Upstream skills` 第一条；`mmw-v2/merge-notes/README.md` | 每处本仓改动的记录；`ask-matt` 删 merge-note 后其改写失去保护 |
| 事实 7：一件事只有一个家；MMW 不带路由技能 | `SKILL-SET-RULES.md:17` | `ask-matt` 退出安装（`06163a0f`）；每个技能用结尾一节点名下一步（`UI.md` `## Next`、`wayfinder` 第 6 步、`improve` `### 4.`、`grill-with-docs` 末句） |
| 事实 6：技能按名字组合，不带另一个技能的副本 | `SKILL-SET-RULES.md:16` | `grill-me`、`grill-with-docs` 只点名；R1 三份读者段是已知例外，靠 merge-note 同步 |
| description 只写触发；用户触发技能的 description 是一行摘要 | `SKILL-SET-RULES.md` `### Descriptions`；`SKILL-MECHANICS.md` `## Invocation`；Memory `411750f5` | `wayfinder`、`to-questionnaire` 补 "Use when"；`grill-with-docs`、`handoff`、`improve` 收回上游原文 |
| `disable-model-invocation` 与 `openai.yaml` `policy` 同增同删；七个保留用户触发 | `merge-notes/README.md` `## disable-model-invocation` | `wayfinder`、`to-questionnaire` 两处一起删；七个两处一起留 |
| host 与 runner 中立 | `SKILL-SET-RULES.md` `### Paths and host neutrality`；`merge-notes/README.md` `## host 中立` | 所有 `the Skill tool`、`/名字` 改成散文；`VISUAL.md` 按能力选呈现面；`wayfinder`/`improve` 用"host 自带 general-purpose subagent" |
| 不交付自定义 subagent | ADR `0015-no-custom-subagents.md` | 同上 |
| 技能文本是英文，另一种语言只能出现在程序读的名字里 | `SKILL-SET-RULES.md` `### Vocabulary` | `interface-and-remake.md` 删掉两句中文固定句（2026-09-28 定稿 I4） |
| `mmw-v2/upstream/skills/` 下 `.md` 不许有破折号 | 上游 `mmw-v2/upstream/CLAUDE.md` 末段；`check_upstream_em_dashes.py`（每个套件都跑） | 本仓在上游文件里写的每一句 |
| 已安装技能 frontmatter 必须是合法 YAML | `check_own_skill_frontmatter.py` | `setup-matt-pocock-skills` description 保留外层引号（merge-note 最后一行） |
| `mmw-v2/upstream/` 自己的 `AGENTS.md`、`CLAUDE.md`、`CONTEXT.md` 原样不动 | 根 `AGENTS.md` `## Key Conventions`；`merge-notes/README.md` `## host 中立` 末段 | `ready-for-afk` 偏差保留 |
| tracker 与仓库文件的权威归属；决策票结论只在 resolution comment | ADR `0001-tracker-repo-authority.md` | `wayfinder` 的 map 是索引、决定在票里；`to-spec` 读 resolution comment |
| docs 层过继：`docs/agents/` 三件配置照 setup 种子落地 | ADR `0005-docs-layer-adopted-by-v2.md` | `setup-matt-pocock-skills` 的落地件；ADR 里写的 `## Agent skills` 块后来被 `## External References` 行取代 |
| Claude Design 是设计唯一源头 | ADR `0029-claude-design-is-the-design-source.md`、`0030` | `prototype` UI winner 不直接折进代码，交给 `design-pages`；scaffolding 在第一次 pull 后拆 |
| 用户 2026-09-16 对 `grilling` 的裁定 | Memory `09af4c99`、`9c133aa5`、`eb828995` | 第一性原理块只能是原文摘录、不改工作流与问法、"惯例不是理由"与 "first principles is overkill" 不动 |
| 用户 2026-08-26 对 prototype 的改造 | Memory `6512963a` | 原型留在仓库迭代，不推临时分支 |
| `wizard` 修复不提交上游 | 2026-09-28 汇总 `## 二` 表 | 只改本仓副本 |
| 技能复审只读、按任务走查、发现要有真实发生方式 | `REVIEWING-A-SKILL-SET.md`；Memory `88b4e72c`（2026-09-28 报告引，未核实） | 本单元所有 2026-09 修改 |

---

## 8. 天然整体

1. **`grilling` 整份**：rounds、frontier、问法格式、事实/决定分工、完成判据互相定义（frontier 的定义决定每轮问什么，完成判据是"frontier 为空"）。本仓的第一性原理块被用户裁定为"整块组装"的原文摘录（Memory `09af4c99`），并用第 30 行一句限定为"只进推荐答案、不加轮次"；把它拆到别处，那句限定就失去对象。
2. **`wayfinder` `SKILL.md` 主体**：map 模板、ticket 类型、fog of war、out of scope、两种模式是同一套概念（destination、frontier、fog、decision ticket）的不同面；`SKILL-SET-RULES.md` 把它的开头与 `## Plan, don't do`、`## Fog of war` 当作"交接理解"的范例。`interface-and-remake.md` 已经是按分支拆出的一块，它本身又是一个整体：两张票的目的、阻塞条件、首行点名、`## Notes` 常设规则缺一不可（缺常设规则则后来的决定票不阻塞 alignment ticket）。
3. **`prototype` 的 `SKILL.md` + 一个分支文件**：每次运行读 `SKILL.md` 加一份分支文件；规则 6 与 `UI.md` 第 6 步互相引用（"the way the SKILL describes"、"`UI.md` step 6"）。`EXP.md` 与 `evidence-page.md` 是一对（第 4 步写生成器时才读后者）。
4. **`prototype` leaf 目录约定、`UI.md` `## State list` 格式、`design-pages` 的读取与拆除、`pull_design.py` 的解析**：跨技能的一份接口，格式由脚本决定。任何一端单独改都会断。
5. **`wizard` 的 `SKILL.md` + `template.sh`**：`SKILL.md` 明说 UX 已由模板解决、agent 只写 stage；helper 名单、`TOTAL_STAGES`、`STAGES` 标记是两边共享的接口。
6. **`diagnosing-bugs` 六阶段**：每阶段的完成判据是下一阶段的输入（红色回路 → 最小复现 → 假设 → 探针 → 回归测试 → 清理）。`hitl-loop.template.sh` 是第 1 阶段第 10 种回路的附件。
7. **`domain-modeling` 三份文件**：`SKILL.md` 定何时写、两份 FORMAT 定写成什么样，互相链接；本仓的 ADR 形状差异放在技能之外，没有打破这个整体。
8. **`codebase-design` 的词汇表与原则**：术语、Relationships、Rejected framings 互相定义；`improve-codebase-architecture`、`HTML-REPORT.md` `## Tone`、`code-review` 的 deletion test 都依赖同一组词。
9. **`setup-matt-pocock-skills` 的 `SKILL.md` + 种子 + 落地件**：种子是落地件的起点，落地件是被流水线读的那份；本仓规则"落地件只补不改"就是为了让两者能分开演化。`## Three label sets` 需要种子与落地件同文（R4），整表读取规则已经漂移（R5）。
10. **`writing-for-agents` 的上游部分 与 本仓两份文件**：`SKILL-SET-RULES.md` 按名字引用 `SKILL.md` 的 `## Context pointers`、`## Steps and completion criteria`、`## Pruning` 与 **Negation**；`REVIEWING-A-SKILL-SET.md` 逐条应用 `SKILL-SET-RULES.md` 的检查。三者是一套：上游给杠杆和失败模式的名字，本仓把它应用到一组互相交接的技能。`SKILL-SET-RULES.md` 内部 `## What skill text is for` 七条事实被第 9 行宣布为"下面每条检查都服务于它们"，拆开会失去检查的依据。
11. **`improve-codebase-architecture` 的 `SKILL.md` 第 2 步 + `HTML-REPORT.md` + `diagram-design`**：页面规则、固定画法与强调色规则压过 `diagram-design` 各图型自己的规则，只有三者一起读才成立（`merge-notes/diagram-design.md:28` 记录这层依赖）。
12. **`ask-matt` 的 `SKILL.md` 与 `PHASE-BOUNDARIES.md`**（上游路由的证据）：`## Phase boundaries` 一节只给五个选项，决策顺序和"为什么 Continue 先排除"全在 `PHASE-BOUNDARIES.md`；上游 `mmw-v2/upstream/CLAUDE.md` 第 21 行要求每次增删改用户可达技能都回头改 ask-matt，"a router that lies" 是它的已知维护代价。本仓没有保留这条维护规则，改为事实 7（每个技能结尾点名下一步）。

---

## 9. 上游怎样做路由（`ask-matt` 证据）

- 上游 `ask-matt` 是**用户触发**的路由技能（上游 frontmatter `disable-model-invocation: true`，`openai.yaml` `policy.allow_implicit_invocation: false`，已核实）。上游 `SKILL-MECHANICS.md` `## Router skills`："one user-invoked skill that names the others and when to reach for each… It can only hint, never fire them"。
- 路由形态：一条主流程（grill-with-docs → 可选 prototype → 多会话则 to-spec → to-tickets → implement，否则直接 implement）、`## On-ramps` 下三条（triage、diagnosing-bugs、wayfinder；正文开头说"two on-ramps"，与条目数不一致，上游原文如此）、代码健康、词汇层、独立技能、阶段边界（`PHASE-BOUNDARIES.md` 五问）、前置条件（setup）。每条路线写"何时用、为什么比最近的邻居合适"。
- 上游用维护规则保持它准确：`mmw-v2/upstream/CLAUDE.md` 第 21 行。
- 本仓历程：先删用户触发改成模型可触发（已删 merge-note 第一行）；改写主流程去向为 `dispatch`、界面链、Yes/No 决定谁检查；2026-09-28 调查显示 Claude 会话 0 次调用（本次复核也是 0）；`06163a0f`（2026-09-28）从 `skills.txt` 删除，理由"every MMW skill's description already reaches the agent's runtime, and each skill's closing section names the next step"。目录与改写后的文本仍留在 subtree 里。

---

## 未确定

- `~/.claude/projects` 只统计了顶层会话文件，没统计 `subagents/`；Codex、Grok、Pi、Cursor 的调用次数没查。表中 0 次只对 Claude Code 顶层会话成立。
- 2026-09-28 报告引用的 agentflow #592、#594、#915、#997（会话内容）、#537、xiaohuangya label 现状、上游 issue #377、#449、#530、#559、`~/.claude/history.jsonl` 的 8 次访谈原话，我都没有回到 tracker 或原始记录核实。
- `wizard/template.sh` 第 40–150 行的实现没有逐行读，只读了每个函数的注释头；"没有过度防御"的判断来自 2026-09-28 报告的实测，未核实。
- `teach` 的 `file://` 跨目录链接行为：merge-note 自述未实测，我也没测。
- `docs/agents/domain.md` 落地件全文没有逐行与种子比对，只读了 merge-note 描述与 2026-09-28 报告。
- `mmw-v2/upstream/docs/` 下的人读文档页（不装进 host）只统计了 diff 行数，没有读内容。
- 上游 `mattpocock/skills` 在 `c55ee460` 之后是否又改过这些技能，没有联网查。
