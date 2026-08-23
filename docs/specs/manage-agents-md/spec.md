---
slug: manage-agents-md
summary: 一个跨五宿主的技能，按一套固定的文档格式新建、重写、定时增量更新仓库里的 AGENTS.md 与 CLAUDE.md；正文从四份公开参考里抄段拼接，只做精确修改。
date: 2026-08-23
branch: manage-agents-md
spec_issue: 0
artifact_refs: []
---

# manage-agents-md spec

> 来源：用户与 Claude 在 2026-08-23 的一次 grilling 会话。输入是四份公开参考的全文、五个宿主的官方文档、agentflow 仓库里 75 份 `AGENTS.override.md`（不计根 `archive/`）的统计，以及用户在六轮问答里做的全部决定。没有单独保存的 research 目录；调查员的原始报告只存在于那次会话里，本文把它们的结论写成「进一步说明」一节。

## Problem Statement

用户在五个宿主（Claude Code、Codex、Pi、Cursor、Grok Build）之间切换，每个仓库都要有一份 agent 指令文件。现状有三个问题：

1. 每次新开仓库都从零手写，没有固定格式，写出来的文件长短和段落各不相同。
2. 已有的文件（agentflow 仓库是最大的一份：根 `AGENTS.md` 加 75 份子目录 `AGENTS.override.md`，不计根 `archive/` 下的那份）用的是 `AGENTS.override.md` 这个文件名，只有 Codex 和 Pi 认它，Claude Code、Cursor、Grok Build 读不到；文件头上的「最后核对」锚点停在两个旧 commit 上，没有人更新。
3. 代码改了，指令文件不跟着改。没有一个固定的手续能定期发现「这条规则已经过时」或「这个目录出现了新的只在这里成立的规则」。

公开的四份参考各解决一部分：humanlayer 解决「文件被宿主整体忽略」，sentry 解决「文件太长、复制已有文档」，anthropic 解决「定期审计和增量追加」，mattpocock 解决「写给 agent 的文档通用写法」。它们彼此在目录图、命令表、长度、两个文件的关系上互相冲突，不能直接拿来用。

## Solution

做一个名为 `manage-agents-md` 的技能，放在 `mmw-v2/skills/manage-agents-md/`，装进五个宿主。它做三件事，由同一个入口按现场分流：

- **新建**：仓库里没有 `AGENTS.md` 时，调查整个仓库，用固定问题向维护者问出仓库里查不到的事实，按固定格式写出根文件和需要的子目录文件。
- **重写**：仓库里已有任何形式的指令文件（`AGENTS.md`、`CLAUDE.md`、`AGENTS.override.md`、嵌套文件）时，把它们迁移成固定格式，命令一条不丢，删掉不该留的内容；同样用固定问题向维护者确认只在维护者脑子里的内容；并在对话里列出删了什么、为什么。
- **定时增量**：由宿主的定时功能带一句固定提示词调用时，对每个 `AGENTS.md` 找出它最后一次提交之后所在目录下的代码改动，判断规则是否过时、是否要新增规则，在独立分支上改好并提交，结束时报告改了哪些文件。增量模式只改有代码证据的条目，不碰只有维护者知道的内容。

技能约定一套确定的文档格式（见「实现决定」第一节），三种情况写出来的文件都长这样。

技能正文的写法有一条硬约束：能从四份参考里抄的段落直接抄原文，只做适配我们决定的精确修改；只有参考的原意与我们的决定相反时才改写。技能自身的结构和措辞以 `writing-for-agents` 为准。

## User Stories

1. 作为一个在五个宿主间切换的用户，我想让每个仓库只维护一份 `AGENTS.md` 正文，这样改一处五个宿主都生效。
2. 作为 Claude Code 的用户，我想让 `CLAUDE.md` 只有一行 `@AGENTS.md`，这样 Claude Code 能读到 `AGENTS.md` 而不产生第二份内容。
3. 作为一个新开仓库的用户，我想说一句「建 AGENTS.md」就得到一份按固定格式写好的文件，这样不用每次从零决定写什么。
4. 作为 agentflow 的维护者，我想说一句「重写 AGENTS.md」就把根文件和 75 份子文件迁移成新格式，这样不用逐个目录手工改。
5. 作为重写的用户，我想在对话里看到「删了什么、为什么」，这样能在 git 里回退任何一条误删。
6. 作为重写的用户，我想保证原文件里的每条命令都保留在新文件里，这样 agent 不会失去它本来知道的工具。
7. 作为定时任务的设置者，我想只在宿主自带的定时功能或系统 cron 里写一句固定提示词，这样 agent 读到技能就知道自己处于增量模式。
8. 作为定时任务的接收者，我想在独立分支上看到提交和一份「改了哪些文件」的报告，这样我看完再合并。
9. 作为任何一个宿主里的 agent，我想在根文件里读到一句「进子目录前先搜并完整读取该目录的 `AGENTS.md`」，这样即使我的宿主不会自动加载子目录文件，我也知道该去读。
10. 作为 Claude Code 里的 agent，我想让只在特定任务才相关的段落包在 `<important if="…">` 里，这样宿主那句「这段上下文可能无关」不会让我忽略整份文件。
11. 作为写手 agent，我想只从调查员的报告写，每条规则在报告里有证据，这样我不会写出代码里没有的规则。
12. 作为调查员 agent，我想拿到一份专用提示词，知道查什么、报告用什么格式、证据写到哪一级，这样我的报告写手能直接用。
13. 作为用户，我想让调查按主题和按目录并行跑，这样大仓库不会因为单个 agent 的上下文装不下而漏查。
14. 作为用户，我想让根文件不超过 150 行，超了技能要拆到子目录或指向外部文档，这样文件不会长到稀释注意力，也不会逼近 Codex 的 32 KiB 合并上限。
15. 作为用户，我想让根文件不写目录图和环境变量，这样这些极易过时的内容不会出现在文件里。
16. 作为用户，我想让每条只在某个目录成立的规则放进那个目录的 `AGENTS.md`，哪怕只有一条，这样规则在它生效的地方。
17. 作为用户，我想让子目录文件只写范围和规则，不写指回根文件的话、不列 skill，这样子文件保持短。
18. 作为用户，我想让规则用正面句式写（「写一行注释」而不是「不要写多行注释」），这样 agent 不会被否定句里的概念带偏。
19. 作为用户，我想让技能有一份自查清单，写手在交付前逐条过，这样质量判断有固定的检查面而不靠临场发挥。
20. 作为用户，我想让一个脚本检查机器能判的事实（行数、桥文件、路径存在、标签闭合、那句子目录提示、不再有 `AGENTS.override.md`），失败就非零退出，这样格式错误在交付前被抓住。
21. 作为用户，我想让技能不自带调度器，这样有定时功能的宿主用自己的，没有的用系统 cron。
22. 作为用户，我想让技能不碰领域文档、不碰个人本地文件、不列 skill、不写提交署名、不写元数据，这样技能只管一件事。
23. 作为技能的维护者，我想让每段正文能回溯到四份参考的哪一段，这样上游更新时知道该同步哪里。
24. 作为技能的维护者，我想让技能的每一步都有能判定「做完了」的完成条件，这样 agent 不会提前结束。
25. 作为技能的维护者，我想让 SKILL.md 只做分流，每一步的方法在各自的 reference 里，这样 agent 做某一步时上下文里只有那一步需要的东西。
26. 作为仓库维护者，我想让 agent 在动笔前用固定的问题问我项目给谁解决什么问题、处于什么阶段、仓库管什么不管什么，这样项目身份写的是我知道而代码里没有的事实，不是技术栈。
27. 作为仓库维护者，我想让 agent 用固定的问题问我生成文件、顺序依赖、权威来源、反复踩过的坑、有意为之的反常做法、环境差异、遗留区，这样关键约定与陷阱里有我脑子里的东西，不只有代码里能看出来的。
28. 作为仓库维护者，我想让 agent 问我的每个问题都带一个从调查报告推出来的推荐答案，这样我只需要确认或纠正，不用从零回答。
29. 作为定时任务的接收者，我想让增量更新不碰项目身份、子目录范围句和没有代码证据的约定条目，这样我不在场时 agent 不会改写只有我知道的事实。

## Implementation Decisions

### 一、文档格式

这是技能的产物合同，三种情况写出来的文件都必须符合。

**根目录**

- `AGENTS.md` 是唯一正文，上限 150 行。`CLAUDE.md` 是桥：一行 `@AGENTS.md`，加上仓库原有的其他 `@` 引入行，没有别的内容。不用软链接。
- 段落按顺序：
  1. 项目身份，一到四行，来自维护者而不是 manifest：给谁解决什么问题；处于什么阶段、有没有真实用户和资金；这个仓库管什么、不管什么（拆出去的仓库、冻结的目录）；agent 该怎么对待仓库里的内容。技术栈不写。
  2. 包管理器与运行时，一两行。
  3. 命令表。只写 `--help` 和 manifest 的 scripts 查不到含义的命令；优先单文件粒度的测试、lint、类型检查命令；多于一条就用表。
  4. 外部引用表：两列，「需要什么 → 仓库相对路径」。只指仓库内已有的文档（README、CONTRIBUTING、架构、API 规范、安全、发布、策略）。禁止「见 docs」这类模糊引用。
  5. 关键约定与陷阱：一条一规则。内容是 agent 从代码里查不到的事实：生成文件及其再生成命令；必须按顺序做的事；两处记录同一件事时以哪处为准；反复调试过的坑；看起来反常但有意为之的做法及其原因；机器和环境之间的差异；遗留区。理由只在能防止一个很可能的错误时才写。
  6. 只在某类任务才相关的段落，每段包在 `<important if="具体触发条件">…</important>` 里。条件要窄到一种任务（「你在新增或修改 import」），不要宽到「你在写代码」。身份、运行时、命令表、引用表、约定不包。这个标签的依据是 humanlayer 对 Claude Code 系统提示词 XML 模式的观察；对其余四个宿主它只是普通文本，无害但没有验证过的效果。
  7. 一句话：进入子目录前先搜并完整读取该目录的 `AGENTS.md`。措辞按 `writing-for-agents` 的 context pointer 规则写：触发词在前，一个分支一个触发词。
- 不写：目录图、环境变量、已安装 skill 清单、AI 提交署名、任何头部元数据、嵌套文件索引表。

**子目录**

- `AGENTS.md`（正文）加 `CLAUDE.md`（一行 `@AGENTS.md`）。不用 `AGENTS.override.md`。
- 建文件的门槛：只要该目录有一条「根没写、且只在这个目录成立」的规则，就建。
- 段落：
  1. 一句范围：本目录负责什么、不负责什么。
  2. 规则：一条一规则，必守和禁止混排。
  3. 按需：本目录专属命令，根文件已有的不重复。
  4. 按需：指向仓库内已有文档的引用。
- 不写：指回根文件的话、`<important if>` 块、skill 归属、头部元数据。
- 子文件比根文件短，只写与根不同的内容。

**两层通用禁写**：linter、formatter、typechecker 能管的规则；代码片段（改成文件路径引用）；空泛口号；一次性修复记录；从 README 或 CONTRIBUTING 复制的内容；频繁变动的版本号和计数；读代码就能看出来的东西。

**规则句式**：正面表述。禁令只在无法正面表述时保留，并配上正面目标。

### 二、技能结构

```
mmw-v2/skills/manage-agents-md/
  SKILL.md          只做分流
  create.md         新建的前序手续，末尾指向共用 reference
  rewrite.md        重写的前序手续
  incremental.md    定时增量的前序手续
  survey.md         步骤 A：派调查员、收报告
  ask.md            步骤 Q：用固定问题问维护者
  write.md          步骤 B+C：决定哪些目录建子文件；写根文件和子文件
  prune.md          步骤 D：删减清单与自查清单
  additions.md      步骤 G：增量时判断加什么
  migrate.md        步骤 H：重写时怎么处理旧文件
  verify.md         步骤 E+F：跑校验脚本；报告格式
  scripts/check.sh  机械校验
  tests/            校验脚本的测试
  agents/openai.yaml
```

`SKILL.md` 的分流规则：目录里没有 `AGENTS.md` 也没有 `CLAUDE.md` → `create.md`；有任何一种且用户要求重写或迁移 → `rewrite.md`；提示词说明是定时增量 → `incremental.md`。三个入口各自只写前序手续，写完指向共用 reference。

三种情况的步骤顺序：

| 情况 | 步骤 |
| --- | --- |
| 新建 | A → Q → B+C → D → E+F |
| 重写 | A → H → Q → B+C → D → E+F |
| 增量 | A（只查变动范围）→ G → D → E+F；不走 Q |

技能是 model-invoked：`SKILL.md` 的 `description` 写三种分支的触发词（建 AGENTS.md、重写或迁移 AGENTS.md、定时增量更新）。不设 `disable-model-invocation`。

### 三、每一步抄哪份参考的哪一段

这是技能正文的来源合同。「抄」指原文拷贝，「改」列出精确改动，其余一字不动。

| 步骤 | 来源 | 抄什么 | 改什么 |
| --- | --- | --- | --- |
| A 调查 | sentry `SKILL.md`「Workflow 1. Inspect before writing」 | 四条清单（包管理器、命令、docs/specs/policies、约定） | 标为调查员的「必读重点」；加两项：`git log` 里近期改动最密集的目录；仓库里已有的全部 `AGENTS.md`、`CLAUDE.md`、`AGENTS.override.md`、`.cursor/rules`、`.github/copilot-instructions.md` |
| A 调查 | anthropic `quality-criteria.md`「Assessment Process」第 2 步 | 「对照实际代码库：跑命令、查引用文件是否存在、核对架构描述」 | 放进调查员提示词 |
| Q 问维护者 | `grilling` `SKILL.md` | 提问格式：每题编号、一句标题、正文含上下文和选项、一个推荐答案；一轮问完等答复 | 问题集固定（见第四节），不做设计树和多轮扩展；推荐答案从调查报告推出 |
| B 决定子文件 | sentry `SKILL.md`「Workflow 2. Choose scope」 | 「closest instruction file wins; keep narrower files shorter than root files」 | 建文件门槛改成「有一条只在本目录成立的规则就建」 |
| C 写根文件 | humanlayer `SKILL.md`「Principles 1、2」 | 什么裸露、什么包；条件要窄，含 Bad/Good 例子 | 「90%+ 任务相关就裸露」改成 `writing-for-agents` 的判据：所有分支都要的内联，只有部分分支要的包；Principle 1 列举的裸露内容「project identity, project map, tech stack」改成我们的裸露段（身份、运行时、命令、引用、约定），因为目录图已禁 |
| C 写根文件 | sentry `SKILL.md`「Writing Rules」 | 全部 11 条 | 删「Do not list installed skills or plugins」以外与我们冲突的条目：无。保留全部 |
| C 写根文件 | `writing-for-agents`「Context pointers」 | 指针写法三条 | 用于引用表每行和子目录提示句 |
| D 删减 | anthropic `update-guidelines.md`「What NOT to Add」 | 四类，各带 Bad 例子，第四类另有 Good 例子 | 作为底本；追加 humanlayer「Principle 4」的「cut code snippets，改成文件路径引用」「cut anything a linter can enforce」；追加 sentry「Writing Rules」的「Do not list installed skills or plugins」和「Anti-Patterns」的「不从 README/CONTRIBUTING 复制」 |
| D 删减 | `writing-for-agents`「Pruning」四条与「Negation」一段 | 原文 | 并入 `prune.md`，接受与已安装技能重复 |
| D 自查 | anthropic `SKILL.md`「Quick Assessment Checklist」六个维度 | 维度名与 Check 列 | 去掉 Weight 列和分数；每维改成一个是/否问题 |
| E 核对 | sentry `SKILL.md`「Workflow 4. Verify exact paths and commands exist」 | 原句 | 机器能判的交给 `scripts/check.sh` |
| E 核对 | anthropic `quality-criteria.md`「Red Flags」 | 七条 | 机器能判的（引用已删文件）交给脚本；其余（会失败的命令、模板未定制、泛泛建议、TODO、多文件重复）作为 agent 自查 |
| F 报告 | anthropic `SKILL.md`「Diff Format」 | `### Update: 文件` / `**Why:**` / diff 块 | 增量模式用 |
| F 报告 | humanlayer `SKILL.md`「Example」末尾 | 「What was removed and why」「What was NOT removed」两个清单 | 重写模式用 |
| G 增量加什么 | anthropic `update-guidelines.md`「What TO Add」 | 五类 | 原文 |
| G 增量加什么 | anthropic `commands/revise-claude-md.md`「Step 3 Draft Additions」 | 一行一概念；格式 `<命令或模式> - <说明>`；三条 Avoid | 原文 |
| H 重写旧文件 | humanlayer `SKILL.md`「How to Apply」 | 九步 | 第 1 步「提取一句话身份」改成「提取旧文件对身份的说法，作为 ask 步骤的推荐答案」，因为身份由维护者定；第 2 步（目录图）删；第 3 步（技术栈）改成「包管理器与运行时一行」；第 4 步保留「命令全保留」并加「能从 scripts 查到含义的不写」 |

四份参考里明确**不用**的：anthropic 的六维打分和 A–F 等级；anthropic 的项目类型模板；sentry 的 `Commit Attribution` 段；sentry 的 `CLAUDE.md` symlink 做法；agentflow 的 `> 最后核对` 与 `> 领域上下文` 头部字段。

### 四、问维护者

调查员报告汇总之后、动笔之前，写手向维护者提问。问的是仓库里查不到的事实，不是批准。形式借 `grilling` 技能：编号、推荐答案、一轮问完等答复；推荐答案从调查报告推出，维护者只需确认或纠正。不引用任何外部技能，就是一轮问答。

项目身份四问：

1. 用一句话说：这个项目给谁、解决什么问题？
2. 它现在处于什么阶段？有没有真实用户、真实数据、真实资金在跑？
3. 这个仓库之外还有哪些相关仓库或机器？哪些东西已经拆出去、哪些目录已经冻结？
4. 仓库里有没有 agent 容易误读的内容——看起来像规则其实是产品、看起来像代码其实是用户资产？

关键约定与陷阱七问：

1. 哪些文件是生成的、不能手改？用什么命令重新生成？
2. 有没有必须按顺序做的事？
3. 哪些地方两处记录同一件事，冲突时以哪处为准？
4. 过去哪些坑让你反复调试过？
5. 哪些做法看起来不合常规，但是有意为之？原因是什么？
6. 不同机器、不同环境之间有哪些差异？
7. 哪些区域是遗留的、不要动？

子目录范围：对每个要建子文件的目录问一句「这个目录不负责什么」，推荐答案从调查员的目录组报告推出。

重写时，旧文件里已有的身份和约定先当推荐答案问一遍，维护者确认后才保留。

### 五、调查员

调查员不是正式 subagent，是 `survey.md` 里的提示词模板。宿主能派 subagent 时，由主线程用宿主的通用 subagent 并行派发，按 `CLAUDE.md` 全局规则派比主线程低一级的模型；宿主没有 subagent（Pi 明确不内建）时，主线程按同一份模板逐组自己跑，每跑完一组先把报告落到 scratch 再跑下一组。

分工：主题组固定四个——工具链与命令（manifest、Makefile、CI、scripts）、已有文档与约定（README、CONTRIBUTING、docs、SECURITY、旧 agent 文件）、git 历史热点、代码模式（测试布局、生成文件、遗留区）；目录组按顶层目录数动态派，每个顶层目录一个，各自找「只在本目录成立的规则」。调查范围是整个仓库，sentry 的四条清单只是必读重点。

报告格式固定：每条发现 = 一句事实 + 证据（`文件:行` 或命令输出）+ 建议去处（根 / 某子目录 / 不写）+ 类型（命令 / 约定 / 陷阱 / 引用）。写手只从报告写，不自己翻仓库。

增量模式的调查范围缩小为：每个 `AGENTS.md` 最后一次提交（`git log -1 -- <目录>/AGENTS.md`）之后，该目录下的非 Markdown 改动。锚点由 git 算出，不写进文件。

### 六、定时增量

技能提供完整的增量工作流（`incremental.md`）。调度由宿主自带的定时功能开启；宿主没有定时功能时用系统 cron 启动一次会话。提示词固定为一句「按 `manage-agents-md` 技能做定时增量更新」。技能不带调度脚本。

写入方式：在独立分支上改并提交，结束时报告改了哪些文件，用户看完合并。

改动范围：只改能指到代码证据的条目——命令表、引用表、约定与陷阱里证据在代码中的条目、子目录的规则和命令。根文件的项目身份段、子目录的范围句、约定与陷阱里没有代码证据的条目，整段不动；发现它们疑似过时，写进报告的「待维护者裁决」一节，不改文件。

### 七、机械校验

`scripts/check.sh` 只判六项，失败非零退出：

1. 根 `AGENTS.md` 存在且不超过 150 行。
2. 每个 `AGENTS.md` 同目录有 `CLAUDE.md`，内容只有 `@` 引入行，其中一行是 `@AGENTS.md`。
3. 反引号里形如仓库相对路径的引用在仓库里存在。
4. `<important if>` 标签成对闭合。
5. 根 `AGENTS.md` 含「进入子目录先读 `AGENTS.md`」那句。
6. 仓库里不再存在 `AGENTS.override.md`。

内容质量、删减是否到位、规则句式，由 `prune.md` 的自查清单交给写手判断，不进脚本。

### 八、技能自身的写法

- 以 `writing-for-agents` 为准：每一步写完成条件；指针措辞按它的规则；正面句式；无操作句删掉。
- 先抄再改再拼接。每个 reference 里抄来的段落保持原文，改动只限第三节表里列出的那些。
- `agents/openai.yaml` 只写 `interface.display_name` 和 `short_description`，不设 `policy.allow_implicit_invocation: false`（技能是 model-invoked）。
- 加进 `mmw-v2/skills.txt` 的 `self/manage-agents-md`。

## Testing Decisions

技能正文是自然语言，能自动测的只有 `scripts/check.sh`。测试走 `exe-release` 的 shell 用例做法：`tests/run.sh` 一键跑本机能跑的全部，跑不了的显式报出；每个用例是一个 `mktemp -d` 加 `git init` 的临时仓库目录加一条期望（通过或失败及原因）。

用例覆盖六项校验各自的通过和失败：151 行的根文件；缺 `CLAUDE.md`；`CLAUDE.md` 多一行；反引号里指向不存在的路径；未闭合的 `<important if>`；缺子目录提示句；残留的 `AGENTS.override.md`。另加一个「全部通过」的样例仓库。

技能正文的验收按 sentry `SPEC.md`「Evaluation」的 holdout 做法，手工跑三种仓库，每次都走完问维护者那一步：一个单包仓库、一个需要嵌套的 monorepo、一个已有大量文档要列进引用表的仓库。agentflow 是第二种的真实对象，也是重写模式的首个消费者。

## Out of Scope

- 会话收尾时「回顾本次会话缺了什么上下文」的追加（anthropic `/revise-claude-md` 那种）。增量只看代码改动。
- 领域语义文档（agentflow 的 `docs/context/`、`CONTEXT-MAP.md`）。仓库里已有 `domain-modeling` 技能管它们；本技能只把已有的领域文档列进引用表。
- 个人本地文件（`CLAUDE.local.md` 等）。
- 头部元数据（commit 锚点、范围 glob、日期、负责人）。
- 派 `claim-checker`。这是对本仓库 `AGENTS.md`「会产出文档的技能写完派 `claim-checker`」规则的有意例外：那条规则针对写给人的文档；AGENTS.md 的内容按 `claim-checker` 正文的定义多是操作步骤而非断言，它能核的路径引用已由脚本第 3 项覆盖，「代码怎么运作」类陈述由调查员报告的证据字段兜底。用户在 grilling 里决定不派。
- 质量打分。
- 调度器。
- 其他 agent 工具的专有规则文件（`.cursor/rules`、`.github/copilot-instructions.md` 等）的生成。重写时只把它们当原料读。

## Sources

四份参考（全文已读，本地副本在会话 scratchpad 的 `refs/` 下）：

- https://github.com/humanlayer/skills/blob/main/plugins/improve-claude-md/skills/improve-claude-md/SKILL.md
- https://github.com/getsentry/skills/tree/main/skills/agents-md （`SKILL.md`、`SPEC.md`、`SOURCES.md`）
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-md-management （`README.md`、`commands/revise-claude-md.md`、`skills/claude-md-improver/SKILL.md` 及 `references/` 三份）
- https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents （`SKILL.md`、`SKILL-MECHANICS.md`；本仓库 `mmw-v2/upstream/skills/productivity/writing-for-agents/` 是同一份）

五宿主官方文档：

- Claude Code：https://code.claude.com/docs/en/memory 、https://code.claude.com/docs/en/best-practices 、https://code.claude.com/docs/en/large-codebases
- Codex：https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Pi：https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/usage.md
- Cursor：https://cursor.com/docs/context/rules
- Grok Build：https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/12-project-rules.md
- agents.md 官网：https://agents.md

本地对象：

- `/Users/cheuklapchan/agentflow/AGENTS.md`、`CLAUDE.md`、`docs/context-loading.md`、`tests/guards/test_override_structure.py`、`scripts/dev/knowledge_graph/override_review_due.py`，以及主树 75 份 `AGENTS.override.md`（不计根 `archive/`）。
- 本仓库 `mmw-v2/agents/claim-checker/body.md`、`mmw-v2/skills/readable-docs/SKILL.md`、`mmw-v2/install.sh`、`mmw-v2/skills/exe-release/tests/`。

## Further Notes

**五宿主读嵌套文件的官方行为**，这是格式决定的依据：

| 宿主 | 认的文件名 | 子目录文件 |
| --- | --- | --- |
| Claude Code | 只认 `CLAUDE.md`；`@path` 导入最多 4 跳；单文件上限 4 MiB，超过整个跳过 | 进入该目录读文件时按需加载，叠加 |
| Codex | 每目录按 `AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames` 的顺序只取一个；链合计上限 32 KiB（`project_doc_max_bytes`） | 启动时从仓库根走到工作目录；工作目录之下不读 |
| Pi | `AGENTS.md` 或 `CLAUDE.md`；同目录有 `AGENTS.override.md` 则只读它 | 全局 + 上级目录 + 当前目录；不向下读 |
| Cursor | 根和嵌套的 `AGENTS.md`；`.cursor/rules/*.mdc` | 处理该目录文件时按需，叠加，更具体者优先 |
| Grok Build | `AGENTS.md` 家族和 `CLAUDE.md` 家族，同目录两个都读；不认 `AGENTS.override.md`；无上限 | 按需，叠加 |

由此得出的两条：`AGENTS.override.md` 只有 Codex 和 Pi 认，只放一份正文时它不比 `AGENTS.md` 多任何能力，所以不用；Codex 和 Pi 从根启动时看不到子目录文件，所以根文件要有那句「进子目录先读」。

**agentflow 现状**（重写模式的首个对象）：主树 75 份 `AGENTS.override.md`（不计根 `archive/`），中位 17 行，最长 73 行；抽样 8 份读完，内容以必守规则为主，其次是禁止句和范围说明，命令只有 1 条；`> 最后核对` 只有 2 个值且都不是 HEAD；`> 复核范围` 0 份落地；抽样内有 5 条路径引用断链，全仓更多。根 `CLAUDE.md` 是三行 `@PROJECT.md`、`@ENGINEERING-RULES.md`、`@AGENTS.md`，`PROJECT.md` 和 `ENGINEERING-RULES.md` 不在本技能范围内，重写时保留这两行引入。

**公开仓库的嵌套文件**（sentry、airflow、cloudflare/workers-sdk、vscode、next.js、openai/codex、superset）：没有一家在 `AGENTS.md` 头部放 commit 锚点；嵌套文件的内容以不变量、禁止事项、本目录专属命令、指向已有文档为主；行数多数落在两端：一端 3–30 行只装一两条规则，另一端 60 行以上是该目录的架构说明，中间也有零星样本。
