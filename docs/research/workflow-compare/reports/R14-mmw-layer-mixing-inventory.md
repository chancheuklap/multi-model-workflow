# R14 MMW 混层账：每段文字现在混装了什么，按类型应去哪一层

这份清点给下一轮设计新架构的人用：它逐段标出 MMW 的文字现在装着哪几类内容，以及每一类按 pstack 的分层应当住在哪一层。判据是本轮定的：**默认搬到按类型该在的层；留在原处只有一个理由，即已核实的硬约束（H1–H6）或已核实的运行故障。**「没有收益」「现在能跑」「脚本和测试按字面点名它」「改动面大」都不算留下的理由。

准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）。事实底子来自 N1–N11 与 R5–R12；R4、R12 里标「已核实」的事实直接引用（记作 R12 M<n>），它们的保守结论不采用。N11 列出的已知错误（N8 的 `NO_QUESTION`「基本一致」、N9 的 ADR 0012「同义」、N3/N6 把 `ask-matt` 当活入边等）一律不采用。

行号是本轮 `cat -n` 的读数，`SKILL.md` 的行号包含 frontmatter。N9 的部分行号比本轮读数小 1（例如 N9 写 `dispatch/SKILL.md:7`，原文在第 8 行），引用时以本轮为准。标「推断」的是根据写法得出、原文没有直接说的判断；需要实测才能定的放在第 10 节。

---

## 0. 结论（先读这里）

1. **混层是一条现行规则造成的，不是零散的写作失误。**
   - `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）`## What skill text is for` 事实 7 规定：「A skill's place follows from its own text: its description says when it starts, and its closing section says what comes next」，并用「this is why MMW ships no router skill」否定了路由层。
   - `### Hand-offs` 第 5 条又要求「Each skill ends by naming what comes next」。
   - 没有 playbook 层以后，任务顺序只能住在三种地方：
     - 被当作角色操作文件的技能正文：`implement` `## Closing steps`、`code-review/references/session.md`、`dispatch/references/night.md`；
     - 能力技能末尾的「下一步」段；
     - 脚本送进会话的文字：`watchdog.py` 的告警、`turn-guard.py` 的拦截文字、`tool-guard.py` 的 `NO_QUESTION`、`verify-ticket.py` `resume_at`。
   - 第 2 节列出 38 处任务顺序（T1–T38）。

2. **跨任务的理由有 29 条，平均每条散在 6 处以上。**
   - N9 的 PC1–PC18 逐条回原文抽查，全部成立。
   - 本轮补漏 11 条（PC19–PC29），并给 PC9 补了 1 处漏计（`to-spec/SKILL.md` 第 6 行）。
   - 重复最多的是 PC8「baseline 即合同」：15 处，分布在 9 个文件、7 个技能。
   - 至少三条的理由在不同地方写成了不同的文字：PC1、PC9、PC22。
   - pstack 的 23 条原则里，有 14 条能直接接住其中 12 条 MMW 规则；算上只部分对应的，15 条 pstack 原则接住 18 条（第 3.2 节）。

3. **把流程和理由拿掉之后，剩下的纯能力差别很大**（第 6 节）。
   - **已经是纯能力的有 20 个。**
     - 与上游 squash `5b1a4c51` 零差异：`diagnosing-bugs`、`domain-modeling`、`research`。
     - 只改了 host 中立或能力本身：`grill-me`、`handoff`、`to-questionnaire`、`wizard`、`teach`、`wait-what`、`codebase-design`、`diagram-design`。
     - 本仓自有或大幅扩展、主体是能力、流程与路由只占一小部分：`code-checkers`、`manage-agents-md`、`advisor`、`write-screen-contract`、`retro`、`design-pages`、`ui-acceptance`、`to-tickets`、`triage`。
   - **大幅缩水的有六个：**

     | 技能 | 现有行数 | 拿掉流程与理由后 |
     |---|---|---|
     | `implement` | 212 | 上游原文 15 行（本轮实测） |
     | `dispatch` | 292 | 约 35 行（推断） |
     | `code-review` | 322 | 上游原文 87 行，即上游的双轴评审；MMW 的四个 axis 文件改作评审 playbook 的子代理简报 |
     | `verify-ticket` | 59 | 约 25 行命令参考（推断） |
     | `grilling` | 46 | 上游原文 28 行 |
     | `tdd` | — | 3 句归位 |

   - **MMW 在已安装的上游技能里一共加了 +1612/−358 行**（本轮用 `git diff --shortstat` 逐个量）。
     - 其中流程与路由句分布在 11 个技能里。
     - 跨任务理由分布在 2 个技能里：`grilling`、`implement`。
     - 其余是真正的能力扩展：`to-tickets` 的五问、`cutting-interface-tickets.md`、`prototype` 的 EXP 分支、`code-review` 的各个 axis、`teach`、`wait-what` 的 `VISUAL.md`。

4. **有可核实运行故障理由的天然整体只有 7 组**（第 7 节）。
   - 这 7 组都是「要一起搬、在同一次提交里改」的单位，没有一组构成「留在原处」的理由。
   - 最典型的是「事件 → 收件人 → 动作」这条链。它现在正是因为按主题拆散，已经坏了三处：
     - worker 读不到 `## On waking` 第 1 步；
     - `night.md` `## 3` 缺 `MMW turn guard:` 这一行；
     - `watchdog.py` 的八种告警里，只有一种在 `night.md` 里有对应的行。

5. **由第 2 节的散布位置可以推出 15 份 playbook 候选**（第 8 节）。
   - 每份都有现成原文可搬，不需要新写规则。
   - 用户草图里的十二类工作流全部有了落点。
   - 另外有 8 类常驻规则的来源可以落进 mode（第 3.3 节）。

6. **本轮新发现 4 处不一致**（第 9 节）。最硬的一处：`verify-ticket.py` `resume_at` 的 docstring（第 2150–2151 行）引用的 `implement` 段落「A ticket that already carries a run of your own」已经不存在（全仓 grep 只命中这段 docstring 本身），而这个函数按编号返回续跑步骤「step 1」到「step 5」。

---

## 1. 判据、记号与硬约束

### 1.1 六类内容与默认去处

| 记号 | 类别 | 识别特征 | 默认应去层 | 依据 |
|---|---|---|---|---|
| **顺** | 任务顺序 | 一类任务里多种能力的先后、门槛、谁拥有什么、何时停、交什么回复 | playbook | L7 A.2 |
| **能** | 能力做法 | 做好一步的方法、判断标准、领域规则 | 能力技能正文。只有一个 playbook 用、并且绑定 MMW 机制的，放进那个 playbook 的规则簇 | L7 A.2「可以装做法，条件是这些做法只属于这一类任务」；C.2 第一行；C.4 |
| **理** | 跨任务理由 | 跨多个任务、带理由、能改变一个具体决定 | 原则。调用方留一句点名，加一句本地限定 | L7 A.4、C.2「调用方可以限定原则的范围」 |
| **令** | 命令与接口 | 命令、参数、退出码、输出形状 | 完整清单放脚本的 `--help` 或头注释；调用行写在调用它的那一步里 | L7 A.6「调用方式要写在正文里」；SSR `### Scripts and judgement` 第 1 条 |
| **路** | 路由与重入 | 「你是谁 → 读哪份」、下一步是哪个技能、醒来后做什么、从哪一步续 | mode 的路由表或重入协议；playbook 的入口与交接 | L7 A.1、D.1、D.2 |
| **模** | 格式模板 | 产物模板、固定标题、报告格式 | 持有该产物的能力技能（正文或 reference）。脚本按字面读的，登记进锚点表 | L7 A.3「格式持有型」、A.6「字面检查器必须持有被匹配的原文」 |

### 1.2 目标层

| 层 | 在 MMW 里指什么 |
|---|---|
| mode | 一个常驻层（R12 叫它 `mmw` 技能），装常驻规则、原则索引、playbook 路由表、重入协议 |
| playbook | 第 8 节的 PB1–PB15 |
| 能力技能 | 能脱离 MMW 流程被调用、产出一件有名字的交付物 |
| 原则 | MMW 自己的跨任务规则，结构上也能直接放进 pstack 原则 |
| reference | 条件性材料、子代理简报、模板 |
| 脚本 | lever |
| 配置 | `~/.mmw/models.json`、`.mmw/target.json`、`docs/agents/*`、frontmatter |
| 仓库文档 | ADR、`CONTEXT`、`CODING_STANDARDS.md`、`TESTING.md`、SSR、merge-notes |

### 1.3 硬约束（只有这些算约束）

- **H1** 宿主不换：Claude Code、Codex、Grok、Pi、Cursor。这些宿主都没有 Cursor 的 `mode: true` 或 `reminder` 常驻机制。
- **H2** 在 Claude Code 上，带 `disable-model-invocation: true` 的技能不出现在模型的技能列表里，模型按名也调不到（R4 V1）。技能的 description 在宿主启动时扫入，改了要开新会话才生效。
- **H3** 一个会话派出的子代理跑在本会话宿主的模型上；要换厂商的模型，只能另起一个会话。
- **H4** 脚本送进一个已经在跑的会话的文字必须是一行（`watchdog.py` 第 813 行注释，R12 M1）。
  - 本轮补核：这一条管的是 runner 的 `send`，也就是 relay 唤醒、watchdog 告警和 `resume`，不管启动提示词。
  - `runners/orca.sh` 第 25 行写明「The prompt is not typed into the terminal」，第一条提示词作为命令行参数传入。所以 `dispatch.sh` 第 1949–1951 行 worker 的多行启动提示词不受 H4 限制。
  - paseo 与 herdr 适配器怎样传第一条提示词，本轮没有逐行读（第 10 节 U9）。
- **H5** Self-hosting boundary（根 `AGENTS.md`）：一次 watch 期间冻结已安装的版本，不能在运行中从 trunk 重读。
- **H6** 夜里的会话屏幕前没人，不能向人提问。

### 1.4 天然整体

只有一种情况算天然整体：拆开会造成**可核实的运行故障**，也就是原文或脚本里能指出「拆开后哪个读者会走到错的一步」。「拆开会多一跳」「改动大」不算。天然整体的处理办法是整体搬、同一次提交里改，而不是留在原处。

---

## 2. 任务顺序散在哪里（T1–T38）

「去向」一列的 PB 编号见第 8 节。「能力内部」表示这是一项有名字交付物的能力自己的阶段步骤，按 L7 C.3 留在能力技能里。这是按类型判定的，不是因为「不值得搬」。

| # | 位置 | 内容（原文要点） | 类别 | 去向 |
|---|---|---|---|---|
| T1 | `implement/SKILL.md` `## Claim, read in, write the code` 第 12、14、16、18 行 | 先跑 `--preflight`，`NOT_READY` 就停；自己拿票的先读 `inside-a-ticket.md`；接着前一个 worker 的 `wip` 提交继续；读入顺序是票 → 开着的子 issue → **Read first** → **Parent** 指名的 spec 小节 → 词表 → 界面票读 reference；遇到 `fault` 开子票后停 | 顺、令、路 | PB5 第 1–2 步 |
| T2 | 同文件第 30、32、34 行 | `CHECK:` 点名的用例就是第一条红测试；定期跑类型检查；最后跑仓库点名的测试；只在需要时提交测试 | 顺、能 | PB5 写码步 |
| T3 | 同文件 `## Shared experience while implementing` 第 36–68 行 | 开工前打开相关记录；遇到解释不了的行为先搜索；三项条件都成立就存 | 顺、能、令 | PB5 规则簇；`saving-memory.md` 作为 PB5 的 reference |
| T4 | 同文件 `## Closing steps` 第 70–101 行 | 续跑行（第 74 行）、三种 `ABANDON`（第 76 行）、第 1–8 步，每步有 `Done when` | 顺、令、路 | PB5 `#### Closing steps`，是天然整体 W3 |
| T5 | `implement/references/writing-interface-code.md` 四节 | 先取设计侧的值 → 写产品 → 就地修 → 设计本身错时开子票；有三处按编号写「closing step 1」（R12 M30） | 能（内部顺序是方法） | `ui-acceptance` 的 reference；「closing step 1」改成节名锚点 |
| T6 | `dispatch/SKILL.md` `## Find your moment` 第 10–21 行；`## On waking` 第 23–28 行 | 六个时刻的分派表；醒来后四步（重跑被打断的命令、读票、`ack`、照时刻文件做） | 路 | 分派表进 mode 路由表；`## On waking` 进 mode 重入协议 |
| T7 | `dispatch/references/night.md` 全文 | 角色段第 3–11 行、事实表第 13–22 行、§1 到 §6、`Suspending the night` | 顺、令、路、理 | PB4 |
| T8 | `dispatch/references/one-ticket.md` 第 3–14 行 | 四步：`open-ticket` → `start` → 醒来处理 → `land` | 顺、路 | PB7 |
| T9 | `dispatch/references/inside-a-ticket.md` | 先跑 `adopt`；关票后告诉用户去跑 `land` | 顺、路 | PB5 的入口变体 |
| T10 | `code-review/references/session.md` 第 1–5 节加 `## Active Rules` | 钉住 diff → 跑各 axis → 核实每条 finding → 分成票内与票外 → 写一份报告 | 顺、令、模 | PB6 |
| T11 | `code-review/SKILL.md` `## Find your moment` 第 10–15 行 | 按提示词里有没有 axis 名来分门 | 路 | PB6 入口；天然整体 W2 |
| T12 | `verify-ticket/SKILL.md` 第 16–21 行、`## Reached from here` 第 23–25 行 | 「A worker's claim, criteria runs and closeout are steps of the `implement` skill」；分派表；送往 `ui-acceptance` | 路 | 删掉路由句：mode 的触发行 + PB5 |
| T13 | `verify-ticket/references/sub-issues.md` 第 11 行与第 15–23 行 | 第 11 行：子票的 kind 决定谁读、何时读；第 15–23 行：五个 kind 问题 | 路（第 11 行）、能（第 15–23 行） | 第 11 行并入 W1；kind 表进 PB5 规则簇 |
| T14 | `verify-ticket/references/linting.md` 第 3 行 | 何时 lint：发布前、发布后、开夜前 | 顺 | PB1 的发布步、PB4 的 §1b |
| T15 | `ui-acceptance/SKILL.md` 表第 1、3 行，第 38 行 | 送回 `implement` 的 reference、`to-tickets` 的 reference；「A worker opens a `fault` child, as the `implement` skill says, and stops」 | 路、顺 | 第 1 行随 T5 变成本技能自己的 reference；第 38 行进 PB5 |
| T16 | `to-spec/SKILL.md` 第 1 步第 12 行、第 2 步第 22 行、第 4 步、`## Next` 第 125–127 行 | 读 map；screen contract 有未对齐的行就停，退回对齐票或 `write-screen-contract` 的 `Reverse sweep`；发布；「The `to-tickets` skill.」 | 顺、路 | PB1、PB2、PB3 |
| T17 | `to-spec/references/several-specs.md`；`revising-a-spec.md` 第 3、9 行 | 一次只写第一份 spec、停下、让用户重跑；改 spec → 写评论 → 修正未落地的票；控件行变化时按行处理 | 顺 | 拆分循环进 PB1、PB2；行变更进 PB3；改 spec 的方法本身留在能力里 |
| T18 | `to-tickets/SKILL.md` 第 1 步第 20 行、第 8 步第 160 行 | 「A plan or a conversation with no published spec goes through the `to-spec` skill first」；「hand over to the `dispatch` skill」 | 路 | PB1 |
| T19 | `triage/SKILL.md` 第 70、82、90、94 行 | 流水线来的 issue 转读 reference；`ready-for-agent` → `to-spec` → 关 issue → `to-tickets`；子票用 `dispatch.sh route` 关；快捷改标签时问要不要走流水线 | 顺、路、令 | PB11、PB8 |
| T20 | `triage/references/pipeline-issues.md` 全文 | 早上队列怎么读、每种条目问什么、`ready-for-agent` 的三个去处、下一次 `advance` 会接走 | 顺、路、令 | PB8 |
| T21 | `wayfinder/SKILL.md` 第 6 步第 126 行；`references/interface-and-remake.md` | 「in a fresh session, run `to-spec` … then `to-tickets`」；设计票与对齐票的阻塞结构；翻新旧产品时的选择清单 | 路、顺 | PB2；带界面的变体进 PB3 |
| T22 | `prototype/SKILL.md` 规则 6 第 27 行；`UI.md` 第 3 步第 83 行、第 6 步第 108–110 行、`## Next` 第 119–121 行 | 把结论并进正式代码；UI 胜出方案交给 Claude Design；脚手架留到第一次 pull；state list | 顺、路、模 | 顺、路进 PB3；state list 格式进 `design-pages` 的 reference（R12 K-14） |
| T23 | `grill-with-docs/SKILL.md` 第 7 行末句 | 「name the `to-spec` skill as the next step, in this same session」 | 路 | PB1 |
| T24 | `improve-codebase-architecture/SKILL.md` `### 4. Hand the decision on` 第 73–75 行 | 把决定交给 `to-spec` | 路 | PB1；与 PB9 衔接 |
| T25 | `design-pages/SKILL.md` 表第 12–19 行；`edit-pages.md` `## Next`；`pull.md` `## After the first pull`、`## Reached from here`、`## A contract child answered by this pull` | 拆脚手架；按 `改动分类` 分四路交接；处理 `contract` 子票（评论 → `route` → 挪票 → `resume`） | 顺、路、令 | PB3；`contract` 子票那段并进 PB4 的对应行 |
| T26 | `write-screen-contract/SKILL.md` `## Next` 第 113–120 行 | 回 `wayfinder`；首次写完走 `to-spec`；`Re-runs` 之后走 `revising-a-spec.md` | 路 | PB3、PB2。第 1–7 步是能力内部的，留在技能里 |
| T27 | `retro/SKILL.md` 第 8 行、第 186 行 | 从 `origin/<base branch>` 的 HEAD 跑；做完「return to the dispatch skill's `references/night.md` `## 5. The night is over`」 | 顺、路 | PB4。第 1–13 步是能力内部的 |
| T28 | `tdd/SKILL.md` 第 22 行、第 38 行 | 第 22 行：「Working from a ticket, the seams under test are the ones its `## Seam` section names」。第 38 行：「Working from a ticket, that pass is the round of fixes that follows its review」 | 路、顺（本仓加进上游文本） | PB5 的限定句；`tdd` 回上游原文 |
| T29 | `resolving-merge-conflicts/SKILL.md` 第 2 步 | 「After a clean merge of `origin/<base branch>`, identify each ticket …」 | 顺（本仓加） | PB5 第 1 步的限定句。「clean merge 但检查变红」是通用能力，留在技能里 |
| T30 | `exe-release/SKILL.md` 第 1–5 步；`references/driving.md` | 前置条件 → 选产品 → 每个产品一个循环 → 同一提交检查 → 用户装机实测；由 release engine 管循环 | 顺、令 | PB10；`key.md`、`new-product.md` 是能力 |
| T31 | `advisor/references/consulting.md` `## When it is worth a session`、`## Start it`、`## The answer` | 什么时候值得开一个会话；`dispatch.sh advise`；答案的处置 | 路、令、理 | 第一节进 mode 触发行；其余是能力 |
| T32 | `code-checkers/SKILL.md` 第 6、8 步 | `.mmw/target.json` 的 `checks` 跑这个命令；把结果记进 `AGENTS.md` | 顺（接入顺序） | 在 PB13 里排序；步骤本身是能力内部的 |
| T33 | `setup-matt-pocock-skills/SKILL.md` 第 51、63 行（本仓加） | 「In this toolbox the tracker is also the landing pipeline's store」；流水线仓库保留默认标签 | 理（领域）、顺 | PB13 |
| T34 | `docs/agents/issue-tracker.md` `## Morning queries` | 两份清单按顺序读：先看 `needs-triage` 并跑 triage，再看 `ready-for-human` | 顺 | PB8 |
| T35 | 根 `AGENTS.md` `## Gotchas` 第 1 条、两个 `<important if>` 块 | 发布的四步（commit dev → 快进 main → 移动已安装 checkout 并跑 `--check` → push）；夜或单票在本仓里的事实；拉上游的步骤 | 顺 | 四步进 PB14；两个块留作仓库文档（本仓私有事实，由 PB4、PB5、PB14 按名引用） |
| T36 | 残留 `upstream/skills/engineering/ask-matt/SKILL.md`（未安装）主流程第 1–3 步、`### Context hygiene`、`## On-ramps`、`## Codebase health`、`## Phase boundaries`；`PHASE-BOUNDARIES.md` | 头部判断：要不要走 spec 流水线、谁来检查；修 bug 转架构；阶段边界上的五个选项 | 顺、路、理 | mode 路由表、PB1、PB9、PB11、PB15 |
| T37 | 脚本送进会话的文字：`watchdog.py` 八种告警、`turn-guard.py` 第 306–311 行、`tool-guard.py` `NO_QUESTION` 与 `REFUSAL`、`verify-ticket.py` `resume_at`、`dispatch.sh` 第 108–109 行与第 1740 行 | 各自带着下一步，或按步骤编号续跑 | 顺、路、令 | 见第 5 节 |
| T38 | SSR 事实 7、`### Hand-offs` 第 5 条 | 规定每个技能自己写下一步、不设路由层 | 元规则 | 仓库文档，改写为「下一步住在 playbook」 |

**「下一步」句的完整名单**（T12、T15–T18、T21–T27 里属于**路**的句子）共 17 句：
- `to-spec` `## Next`；
- `to-tickets` 第 20 行、第 160 行；
- `grill-with-docs` 第 7 行；
- `improve-codebase-architecture` 第 75 行；
- `prototype` `UI.md` `## Next`；
- `design-pages` `edit-pages.md` `## Next`、`pull.md` `## Reached from here`；
- `write-screen-contract` `## Next`；
- `wayfinder` 第 126 行；
- `triage` 第 82 行；
- `retro` 第 186 行；
- `verify-ticket` 第 16 行、`## Reached from here`；
- `ui-acceptance` 表第 1 行；
- `dispatch` 表第 1 行；
- `codebase-design` 第 10 行（本仓加的「the task that brought you here decides what you do next」，内容与 pstack 的能力技能立场一致，但它是一句路由声明）。

---

## 3. 跨任务理由（PC1–PC29）与 mode 常驻规则来源

### 3.1 原则候选

「次数」写成「位置 / 文件 / 技能」，只计已安装技能的 `.md`。PC1–PC18 的次数照用 N9 的 grep 结果（N11 没有指出错误；本轮抽查了原文）。PC19–PC29 的次数是本轮 grep 的结果。「理由文字」一列说的是各处给出的理由是否是同一句话。

| # | 规则 | 现在的位置 | 次数 | 理由文字 | pstack 对应 | 应去层；调用方留什么 |
|---|---|---|---|---|---|---|
| PC1 | 假通过比诚实失败更坏；查不了就说查不了 | `implement` 第 22 行；`night.md` 第 7 行；`ui-acceptance` 第 10、34、36 行；`harness-guard.md`；`code-checkers` 第 58 行；`git-hooks.md`；`retro` 第 47、58 行；`session.md`（`unverified:`）；SSR 第 62、89 行。非技能处：ADR 0008、`CODING_STANDARDS.md` Skills and scripts 第 4 条 | 12 / 9 / 7 | 不一致：implement 写「An honest `HANDOFF REQUIRED` costs them one look」，night 写「a defect that lands under a green mark」，ui-acceptance 写「green can only mean the product is right」（N9 9.3） | `principle-prove-it-works`（部分） | 原则（R12 暂名 `silence-is-never-a-pass`）；调用方留一句本地后果 |
| PC2 | 检查要能证明自己会失败（negative control） | `to-tickets` 第 84、88 行；`cutting-interface-tickets.md` 第 43–46 行；`to-spec` 第 95 行；`implement` 第 30 行；`story-parity.md` 第 114–117 行；`journey.md` 第 42–53 行；`boundary-check.md` 第 15 行；`night.md` 第 127 行；`code-checkers` 第 58 行；`git-hooks.md` 第 72 行 | 12 / 11 / 7 | 各处各给本地理由 | `principle-test-behavior-not-implementation`（description 末句「If the test would still pass when every imported function…」）、`prove-it-works` | 原则；oracle 机制留在 `ui-acceptance` |
| PC3 | 拒绝要点名一个事实、说为什么、给唯一下一步；收到拒绝的 agent 照做，不即兴 | SSR 第 12、59、134–136 行；`ui-acceptance` 第 26、35 行；`night.md` 第 66 行；`consulting.md` 第 13 行；`refusal.py` 头；`CODING_STANDARDS.md` | 7 / 4 / 4 | 一致（都出自 ADR 0008） | 无（pstack 只在脚本接口约定里提到，L7 A.6） | 写脚本那一侧留在 `CODING_STANDARDS.md`；读拒绝的那一侧进原则或 mode 常驻规则 |
| PC4 | 谁都不轮询另一个 agent；起了别人就结束回合 | `night.md` 第 11、66、70 行；`dispatch/SKILL.md` 第 25–28 行；`one-ticket.md` 第 8 行；`inside-a-ticket.md` 第 5 行；`implement` 第 22、78、84 行；`ui-acceptance` 第 38 行；`sub-issues.md` 第 11 行；SSR 第 90 行 | 13 / 9 / 6 | 一致 | 无（orchestrate 的「The CLI never spawns, waits, or wakes」是脚本约定） | 原则；PB4、PB5、PB7 里留「end your turn」动作 |
| PC5 | 进度读持久记录，不读会话记忆 | `dispatch/SKILL.md` 第 8 行；`night.md` 第 5 行；`implement` 第 74、86 行；`driving.md` 第 5 行；`sub-issues.md` 第 11 行；SSR 第 33 行 | 8 / 7 / 5 | 基本一致 | `session-pickup.md`「The prior trail is authoritative input」 | 原则（R12 暂缓的 `the-tracker-is-the-state`；8 处重复，本轮判据下应建）；进 mode 重入协议的第 2 步 |
| PC6 | 协议状态只由脚本写，模型不手敲 | `implement` 第 99 行；`ui-acceptance` 第 38 行；`night.md` 第 113–120 行；`driving.md` 第 44 行；`tool-guard.py` 机械拦截；`CODING_STANDARDS.md` State 第 3 条 | 4 / 4 / 4 | 一致 | `encode-lessons-in-structure`（部分） | mode 常驻规则；hook 继续做强制 |
| PC7 | 确定性的工作交给脚本，文字只写判断 | SSR 第 12、59–63 行；`night.md` 第 3 行；`driving.md` 第 5 行；`wizard` 第 10 行 | 5 / 4 / 4 | 一致 | `encode-lessons-in-structure`、`build-the-lever` | 原则（写技能时适用）；PB14 引用 |
| PC8 | baseline 即合同；不成立就开 `contract` 子票，从不悄悄改 | `implement` 第 16、22、27、96 行；`writing-interface-code.md` 第 3、41 行；`design-pages` 第 10 行；`pull.md` 第 5、31、45–47 行；`night.md` 第 92、98 行；`pipeline-issues.md` 第 5 行；`to-tickets` 第 174 行；`write-screen-contract` 第 18 行 | 15 / 9 / 7 | 只有 implement 第 22 行给了理由（「A baseline is a decision someone already paid for」） | 无 | MMW 原则；`contract` 子票的机制留在 PB5 规则簇 |
| PC9 | 用户只决定产品事项，其余工程决定自己做并写一行理由 | `implement` 第 23、96 行；`grilling` 第 28 行（本仓加）；RSS 第 28 行；`consulting.md` 第 7、19 行；`manage-agents-md` 第 76 行；`sub-issues.md`；`person-ticket.md` 第 3 行；`triage` 第 36 行；**补漏：`to-spec` 第 6 行**（「A call on what the user sees, what happens to money, or what is in scope … is not yours」）；`shared.md` 规则 1、2；`dispatch.sh` 第 108 行 `AUTONOMOUS` | 12 / 10 / 9 | 不一致：各处列举的产品事项范围不同，有的只列顾客所见与范围，有的另加钱、对外发布、难以撤销 | `never-block-on-the-human`，加 mode `## Autonomy` | mode `## Autonomy`，外加原则；调用方留本地出路（例如 `decision` 子票） |
| PC10 | 写给看不到你上下文的读者 | `night.md` 第 5 行；`implement` 第 23 行；`sub-issues.md` 第 11 行；`grilling` 第 28 行；`ambiguity-scan.md` 第 73 行；`advising.md` 第 19 行；SSR 第 33–34、100–102、135 行 | 10 / 7 / 7 | 各写各的读者 | `minimize-reader-load`（部分），以及 mode 的 `## Writing the reply` | 原则 |
| PC11 | 线索不是证据 | `implement` 第 48–49 行；`session.md` 第 89、101 行；`spec-reviewer.md` 第 22 行；`retro` 第 58、63–66 行；`advising.md` 第 15 行；`research` 第 10 行 | 8 / 6 / 5 | 一致 | `prove-it-works`、`fix-root-causes`（部分） | 原则 |
| PC12 | 同一文件同一时刻只有一个写者 | `to-tickets` 第 44、90、107、182–184 行；`implement` 第 28、78 行；`night.md` 第 126、140 行 | 8 / 3 / 3 | implement 第 28 行给了理由 | `separate-before-serializing-shared-state` | 用 pstack 原则；`to-tickets` 保留 Owns 与 Blocked by 的领域规则（L7 C.2） |
| PC13 | 文件只写现状；改了什么进 commit | SSR 第 51、145 行；`revising-a-spec.md` 第 3、11 行；`rewrite.md` 第 36 行；`shared.md` 规则 13 | 4 / 3 / 3 | 一致 | 无 | 原则 |
| PC14 | 只跑证明本次改动的最小测试集，并引用看到的那一行 | `implement` 第 32 行；`night.md` 第 131、135 行；SSR 第 152 行；`shared.md` 规则 4、15 | 4 / 3 / 3 | 一致 | `prove-it-works`（部分） | 原则 |
| PC15 | 只读靠文字自守，宿主没有只读档 | `advising.md` 第 23 行；`consulting.md` 第 5 行；四个 axis 文件第 3 行；`session.md` 第 31 行 | 7 / 7 / 2 | 一致 | 无 | mode `## Subagents` 或原则 |
| PC16 | 一个意思只有一个权威的家 | `writing-for-agents` 第 78 行；SSR 第 17、40 行；`design-pages` 第 6 行；`pull.md` 第 49 行；`editing-models.md` 第 3 行；`new-product.md` 第 97 行 | 7 / 6 / 4 | 一致 | 无（上游 `writing-for-agents` 有「single source of truth」） | 原则 |
| PC17 | 有副作用的命令被打断后原样重跑能接上 | `dispatch/SKILL.md` 第 25 行；`night.md` 第 120、180 行；`implement` 第 74 行；SSR 第 136 行 | 5 / 4 / 3 | 一致 | `make-operations-idempotent` | 用 pstack 原则；进 mode 重入协议的第 1 步 |
| PC18 | 起不来就停下并报告，不重试、不绕过、不改环境 | `night.md` 第 66 行；`ui-acceptance` 第 35–36 行；`implement` 第 18、78 行 | 5 / 3 / 3 | ui-acceptance 第 36 行给了理由 | `fix-root-causes`（「resist nil-check guards」，部分） | 原则。与 `shared.md` 规则 11「redo it yourself」的张力由 mode 写明优先级（N9 9.3） |
| PC19 | 先质疑前提，再从第一性原理重建；区分症状、近因、根因；归咎于过程，不归咎于人 | `grilling` 第 32–44 行（本仓加，七段）；`retro` 第 30–35 行（blameless postmortem；「A cause addressed to "the agent" changes nothing」）；`diagnosing-bugs` Phase 1、3（上游）；`night.md` Step 0；`shared.md` 规则 4 | 5 / 4 / 4 | grilling 的理由只写在 merge-note（「这几条的理由只记在这里，正文不写」） | `attack-the-premise`、`redesign-from-first-principles`、`fix-root-causes` | 三条 pstack 原则；`grilling` 回上游原文 |
| PC20 | 判断交给一个没写它的读者（独立的第二个上下文） | `code-review/SKILL.md` 第 8 行；`tests-reviewer.md` 第 53 行；`to-tickets` 第 63 行（「in a session other than the one that wrote the code」）；`tdd` 第 38 行（「judged with fresh eyes」）；`consulting.md` 第 9、37 行 | 6 / 5 / 4 | 各自一句 | pstack 只在 agent 定义 Comment Sicko 的理由里有（L7 A.7），不是原则 | 原则 |
| PC21 | 先找现成的；先删再加；能用更少代码就用更少 | `implement` 第 24–26 行；`standards-reviewer.md` 第 20–22 行；`grilling` 第 42 行；SSR 第 140 行；`to-spec` 第 26 行（「Existing seams should be preferred」）；`shared.md` 规则 14 | 7 / 6 / 5 | 各自一句 | `subtract-before-you-add`、`laziness-protocol`、`migrate-callers-then-delete-legacy-apis` | pstack 原则 |
| PC22 | 检查红了改产品，不弯检查 | `implement` 第 22 行（「never by bending the baseline, the harness or the test」）；`ui-acceptance` 第 10 行；`story-parity.md` 第 109–111 行；`harness-guard.md` 第 16–19 行；`night.md` 第 7 行；`writing-interface-code.md` 第 35 行 | 6 / 6 / 3 | 不一致，三种说法 | 无（`prove-it-works` 部分） | 原则（与 PC1 同族） |
| PC23 | 在约定的 seam 上测行为，不测实现 | `tdd` 第 14、20–22、30 行（上游）；`to-tickets` 第 56 行规则 1；`to-spec` 第 92 行；`tests-reviewer.md` 第 35–42 行；`boundary-check.md` 第 34 行；`TESTING.md` `## What a test proves` | 7 / 6 / 5 | 大多出自上游 | `test-behavior-not-implementation` | pstack 原则；做法留在 `tdd` |
| PC24 | 只做被要求的；范围外的问，不做 | `night.md` 第 134 行；`advising.md` 第 25 行；`implement` 第 34 行；`grilling` 第 42 行；`standards-reviewer.md` 第 36 行（Speculative Generality）；`shared.md` 规则 1 | 6 / 6 / 5 | 各自一句 | `laziness-protocol`（部分） | 原则 |
| PC25 | 常设防线要有两次独立发生才值得建；教训要送到对的那一层 | `retro` 第 123–136 行、第 188–210 行；SSR 第 44、140 行 | 4 / 2 / 2 | 一致 | `encode-lessons-in-structure`（「Route to the right layer」）；`reflect/references/synthesizer.md` 的四项检查 | 原则；`retro` 保留 Prevention destinations 表 |
| PC26 | 报告写进文件，不靠记忆；大块工作交给子代理 | `session.md` 第 31 行；`manage-agents-md` 第 50 行；`to-tickets` 第 119 行；残留 `ask-matt` `### Context hygiene`、`PHASE-BOUNDARIES.md`（未安装） | 3 / 3 / 3（已装） | 一致 | `guard-the-context-window` | pstack 原则，外加 mode `## Subagents` |
| PC27 | 用领域词表里的词 | `implement` 第 16 行；`to-spec` 第 20 行；`to-tickets` 第 26 行；`tdd` 第 10 行；`diagnosing-bugs` 第 10 行；`triage` 第 72 行；`improve-codebase-architecture` 第 14、54 行；`wait-what` 第 8 行；SSR `### Vocabulary`；`shared.md` 规则 6、8 | 10 / 9 / 9 | 大多出自上游 | 无（`model-the-domain` 讲的是另一件事） | 原则；各技能里的「read `CONTEXT.md`」是上游原文，保留 |
| PC28 | 秘密不进产物 | `diagnosing-bugs` `## Redact`；`saving-memory.md` 第 4–5 行；`handoff` 第 14 行；`product-answers.md` `## Rules` 第 96 行 | 4 / 4 / 4 | 各自一句 | pstack 有意留在各技能里（L7 C.2 末段） | 候选原则。满足 L7 A.4 的四道门槛；pstack 的先例只是先例，不是约束 |
| PC29 | 只有人能做的步骤单列，agent 不代做，也不伪装成做了 | `ui-acceptance` 规则 3 第 34 行；`person-ticket.md` 第 3 行；`wizard` description；`exe-release` 第 5 步 | 4 / 4 / 4 | 各自一句 | 无 | 原则 |

**核实说明**：
- PC1、PC2、PC4、PC5、PC8、PC9、PC12、PC14、PC17、PC18 的位置，本轮在读全文时逐一见到了原文。
- 其余沿用 N9 的 grep，没有逐处重开。
- N11 指出的 N9 错误（ADR 0012 同义、ADR 0027 现行）不在本表内。

### 3.2 pstack 原则能直接接住的部分

- **已有同名或同义的 pstack 原则**：
  - PC12 → `separate-before-serializing-shared-state`
  - PC17 → `make-operations-idempotent`
  - PC19 → `attack-the-premise`、`redesign-from-first-principles`、`fix-root-causes`
  - PC21 → `subtract-before-you-add`、`laziness-protocol`、`migrate-callers-then-delete-legacy-apis`
  - PC23 → `test-behavior-not-implementation`
  - PC25 → `encode-lessons-in-structure`
  - PC26 → `guard-the-context-window`
  - PC9 → `never-block-on-the-human`
  - PC1、PC2、PC14 → `prove-it-works`
  - PC7 → `build-the-lever`
  - 合计：14 条 pstack 原则直接接住 12 条 MMW 规则。
- **只部分对应的**：PC6 → `encode-lessons-in-structure`；PC10 → `minimize-reader-load`；PC11、PC22 → `prove-it-works`；PC18 → `fix-root-causes`；PC24 → `laziness-protocol`。算上这 6 条，共 15 条 pstack 原则接住 18 条 MMW 规则。
- **需要 MMW 自建**：PC3（读的一侧）、PC4、PC5、PC6、PC8、PC10、PC11、PC13、PC15、PC16、PC18、PC20、PC22、PC24、PC27、PC28、PC29。
- **结构含义**：原则层需要能同时装 pstack 原文和 MMW 自建的原则，按同一模板写（L7 A.4：情境触发、规则、`**Why:**`、`**Pattern:**`）。用户以后把 pstack 原则搬进来时，就只是加一个文件、在原则索引里加一行。

### 3.3 mode 常驻规则的来源（不是原则，而是 mode 的节）

| 节（按 L7 A.1 的章节） | 现在散在哪里 | 次数 |
|---|---|---|
| `## Autonomy`（无人值守、不在屏幕上提问、只问产品事项） | `dispatch.sh` 第 108 行 `AUTONOMOUS`；`tool-guard.py` 第 76–80 行 `NO_QUESTION`；`implement` 第 23 行；`shared.md` 前言（「A session a script started with no person in it…」）与规则 1、2 | 5 |
| 重入协议（醒来 → 重跑被打断的命令 → 读票 → `ack` → 照 playbook 做；从持久记录续） | `dispatch/SKILL.md` `## On waking`；`implement` 第 74、78、84 行；`one-ticket.md` 第 3 步；`inside-a-ticket.md`；`night.md` §3 第 1 步；`driving.md` 第 5 行 | 7 |
| `## Subagents`（用宿主的通用子代理，不点名模型，一条消息同时发出，等它们都回来） | `session.md` 第 23、33 行；`to-tickets` 第 113、119 行；`manage-agents-md` 第 50 行；`wayfinder` 第 76、114 行；`improve-codebase-architecture` 第 71 行；SSR 第 95 行 | 8 |
| 阶段边界与会话卫生 | 残留 `PHASE-BOUNDARIES.md`、`ask-matt` `### Context hygiene`（都未安装）；`grill-with-docs` 第 7 行「in this same session」；`wayfinder` 第 126 行「in a fresh session」 | 4 |
| `## Writing the reply` | `shared.md` 规则 4–9 | 1（已经常驻在 4 个宿主上） |
| 产品运行中的规则指针 | `dispatch.sh` 第 109 行 `PRODUCT_RULES` | 1 |
| 触发器（「遇到 X 用 Y」） | `advisor` 的 description 与 `consulting.md` `## When it is worth a session`；`dispatch` description；`ui-acceptance` description；残留 `ask-matt` 的 description | 4 |
| 在子目录工作前先找 `AGENTS.md` | 根 `AGENTS.md` 最后一行 | 1（仓库级，留在原处） |

---

## 4. 逐技能混层账（35 个）

每个技能一张表。**原文 diff** 是本轮 `git diff --shortstat 5b1a4c51:skills/<bucket>/<name> HEAD:mmw-v2/upstream/skills/<bucket>/<name>` 的结果。

### 4.1 流水线主干

**`dispatch`**（本仓自有；SKILL 28 行，references 264 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| `SKILL.md` 第 3 行 description | 路（六种时刻并列：起 reviewer、跑夜、跑单票、改模型、开任务板） | 能力技能只留「改 host 和模型、开任务板、脚本位置」的触发；其余触发进 mode 路由表。「Start a reviewer from inside a ticket」与 `implement` 第 3 步冲突（N10 B7、R7），删掉 |
| 第 8 行 | 理（PC5）、令（脚本自己找路径） | PC5 进原则；脚本位置那一句留下 |
| `## Find your moment` | 路 | mode 路由表 |
| `## On waking` | 路、理（PC17） | mode 重入协议 |
| `references/night.md` 第 3–11 行 | 理（PC10、PC1、PC4）、顺 | PB4 的所有权行与首段；理由换成点名原则 |
| `night.md` 事实表第 13–22 行 | 路（重入索引） | PB4 的 `Where you are`；与各节一起搬（天然整体 W4） |
| §1、§1b、§2 | 顺、令 | PB4 第 1–3 步；每个退出码的处置是判断，跟着步骤走（L7 A.6） |
| §3 第 1–5 步与表 | 顺、路 | PB4 的重入表。缺 `MMW turn guard:` 行、缺 7 种 watchdog 告警行，搬的时候补齐（W1） |
| §3 `contract` 的权威顺序段第 96–100 行 | 能（只有 orchestrator 用） | PB4 规则簇 |
| §4 收口轮 | 顺、能、令、理（PC12、PC14、PC24） | PB4 规则簇 `#### Closing pass`，整块搬；理由换成点名原则 |
| §4 Memory 决定段第 151–157 行 | 顺、令 | PB4 规则簇 |
| §5、§6 | 顺、令、路（进 `retro`、`finish`） | §5 的汇总与 `retro` 进 PB4；§6 `finish` 进 PB8 |
| `Suspending the night` | 能、令 | PB4 规则簇 |
| `one-ticket.md` | 顺、路、令 | PB7 |
| `inside-a-ticket.md` | 顺、令 | PB5 入口变体 |
| `editing-models.md` | 令、能（配置操作） | 留在能力技能（改配置是可以单独调用的能力） |

- **纯能力剩余**：`editing-models.md` 27 行，加上 `board` 一行和脚本位置一句，约 35 行（推断）。
- **脚本**：`dispatch.sh`、`relay.py`、`watchdog.py`、`turn-guard.py`、`tool-guard.py`、`status.py`、`models.py` 都只被 playbook 的步骤和 hook 调用，属于 lever 层（L7 A.6）。
  - 物理位置有两种放法：挪到 mode 的 `scripts/` 下（pstack 做法，`skills/poteto-mode/scripts/`），或留在 `dispatch/scripts/`。两者都算脚本层。
  - 挪动涉及 `install.sh` 注册的 hook 路径、`board/board_data.py` 第 27 行按路径载入 `ghlist.py`（R12 M22）。这些都是字面引用，按本轮判据不构成留下的理由。

**`implement`**（上游；原文 diff 4 个文件 +203/−8；上游原文 `SKILL.md` 15 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| description 第 3 行 | 路（「Use when you were dispatched onto a ticket, or picked one up yourself」，本仓加） | mode 路由表加 PB5 入口；上游 description 回到原文 |
| 第 6、8 行 | 能（上游第一句）、令（命令名写裸名） | 第一句回上游；命令名的约定进 PB5 |
| 第 12、14、16、18 行 | 顺（T1）、令、理（PC8、PC27） | PB5 第 1–2 步；PC8 进原则 |
| 第 22 行 | 能（`contract` 子票的规则）、理（PC8、PC22、PC1，并带理由句） | 规则进 PB5 规则簇 `#### Baselines`；三条理由进原则，调用方留一句本地后果 |
| 第 23 行 | 理（PC9、PC10、H6）、能（`Decisions I made on my own` 的写法） | `## Autonomy` 进 mode；决定行的写法进 PB5 规则簇 |
| 第 24–27 行 | 理（PC21）、能 | PC21 用 pstack 原则；「keep intact」清单进 PB5 规则簇 |
| 第 28 行 | 能（Owns 两档）、理（PC12） | PB5 规则簇；PC12 用 pstack 原则 |
| 第 30 行 | 顺、理（PC2）；是对 `tdd` 的调用加本地限定 | PB5 写码步（L7 C.2 的限定句写法） |
| 第 32、34 行 | 能、理（PC14、PC24） | PB5；原则 |
| `## Shared experience while implementing` | 顺、能、令 | PB5 规则簇 `#### Memory`；`saving-memory.md` 是 PB5 的 reference（只在满足保存条件时读） |
| `## Closing steps` | 顺、令、路（续跑） | PB5 `#### Closing steps`（W3，编号与 `resume_at` 一起改） |
| `references/writing-interface-code.md` | 能（界面写码）、令、路（三处「closing step 1」） | `ui-acceptance` 的 reference（持有 oracle 的技能）。PB5 按条件指向它，同时消掉 N10 B7 的来回跳转 |

- **纯能力剩余**：上游原文 15 行（「Implement the work … Use /tdd … Run typechecking … use /code-review … Commit」）。上游原文里「full test suite once at the end」「use /code-review」与 MMW 的规则冲突。
  - 做法：PB5 不再加载上游 `implement`，而是直接调用 `tdd`，并写出本地限定句（L7 C.2「调用方可以限定原则的范围」）。
  - 上游 `implement` 回到原文，作为 MMW 之外的通用能力。要不要继续安装，见第 10 节 U8。

**`code-review`**（上游；原文 diff 7 个文件 +316/−81；上游原文 `SKILL.md` 87 行，是「Two-axis review」）

| 段落 | 混装 | 应去层 |
|---|---|---|
| `SKILL.md` 第 8 行 | 理（PC20） | 原则 |
| `## Find your moment` | 路（按提示词形状分门） | PB6 入口，与 `dispatch.sh` 第 1967 行一起改（W2） |
| `session.md` 第 1–5 节 | 顺、令、模、理（PC11、PC20） | PB6。报告格式（第 73–95 行）是 PB6 的交付物模板，留在 PB6（L7 C.4：「它就是这个 playbook 的产物」） |
| `session.md` 第 23–33 行 | mode `## Subagents` 的内容 | mode |
| `session.md` `## Active Rules` | 能、配置（Rules 来自 Nowledge） | PB6 规则簇 |
| 四个 axis 文件 | 能（每个 axis 怎么审）；`spec-reviewer.md` 第 9 行（`DECISIONS` 评论）、第 22 行（`dispatch.sh integrated`）、第 33–39 行（screen contract 行）是 MMW 的领域做法；第 3 行只读规则（PC15） | PB6 的子代理简报 reference（L7 A.5 第一行：「原样或填占位后转交给子代理的提示模板」）；PC15 进 mode |

- **纯能力剩余**：上游原文 87 行，是一项不需要票的通用评审能力。
- MMW 现在的版本要求提示词里有票号与 base commit（`SKILL.md` 表第 1 行），通用能力因此没有安装在任何地方。残留 `ask-matt` 第 28 行明写「`code-review` has no use on a branch or PR without a ticket」。这是「能力技能能脱离 MMW 流程被复用」这项收益的直接实例。

**`verify-ticket`**（本仓自有；59 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| description | 路（「Use when something has to be cut out of a ticket, and when a batch is about to be published」） | 只留触发 |
| 第 8–10 行 | 能、理（PC5、PC6） | 能力正文；理由换成点名原则 |
| 第 12 行 | 令（`PATH`） | 能力正文 |
| 第 16–21 行、`## Reached from here` | 路（T12） | 删；由 mode 与 PB5 承担 |
| `sub-issues.md` 第 5–9 行 | 令 | 能力正文 |
| `sub-issues.md` 第 11 行 | 路（kind → 读者 → 何时） | 事件链（W1），与 `relay.py` `WAKES` 和 PB4 的表一起登记 |
| `sub-issues.md` 第 13–23 行 | 能（五问） | PB5 规则簇（只有 worker 用） |
| `linting.md` | 令、顺（何时 lint） | 命令留在能力里；「何时」进 PB1 与 PB4 |

- **纯能力剩余**：约 25 行命令参考（推断），加上 `verify-ticket.py`、`events.py`、`issue_tree.py`。

**`ui-acceptance`**（本仓自有；381 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| 第 8 行 | 能、模（术语） | 能力正文 |
| 第 10 行 | 理（PC1、PC22） | 原则；留一句本地后果 |
| `## Find your moment` 第 1 行、第 3 行 | 路（送去 `implement` 与 `to-tickets` 的 reference） | 第 1 行：`writing-interface-code.md` 搬进本技能后，变成本技能自己的行。第 3 行：`cutting-interface-tickets.md` 是 `to-tickets` 的能力，保留这个指针（能力之间横向引用，L7 B.2 常规） |
| `## Five rules while the product is running` 规则 1、2 | 能（租约、进程，领域规则） | 能力正文 |
| 规则 3、4、5 | 理（PC29、PC18）并带本地机制 | 原则，加本地限定 |
| 第 38 行 | 顺、路（worker 开 `fault` 子票后停） | PB5 |
| 五份 references | 能、令、模 | 留在能力里 |

- **纯能力剩余**：约 370 行，加上接收过来的 `writing-interface-code.md` 57 行（推断）。

### 4.2 白天头部

**`to-spec`**（上游；原文 diff 4 个文件 +82/−16；上游原文 75 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| description | 路（本仓加的触发句） | 回上游，路由交给 mode |
| 第 6 行 | 理（PC9、PC10）、能 | 原则，加本地一句 |
| 第 1 步读 map 的部分 | 能（怎样读 map 这种输入） | 能力 |
| 第 1 步「一份还是几份」、`several-specs.md` | 能（判断）、顺（一次只写一份、停下、让用户重跑） | 判断留在能力里；循环进 PB1、PB2 |
| 第 2 步第 22 行 screen contract 闸门 | 顺、路（退回对齐票或 `Reverse sweep`） | PB3 的闸门；能力只留「有未对齐的行就停」 |
| 第 3 步 seam 与状态可达的段落 | 能（本仓扩展） | MMW 能力扩展 |
| 第 4 步 `--publish` | 令 | 能力（发布就是这份交付物的最后一步） |
| 模板里 API contract、cross-component、visual acceptance、Critical flows、Sources | 模（本仓扩展） | MMW 能力扩展 |
| `revising-a-spec.md` | 能；第 3 行末句「only by the orchestrator or by a session the user is working in」是 PC8 的一个实例 | 能力 |
| `## Next` | 路 | PB1 |

- **纯能力剩余**：上游 75 行，加上 MMW 的 spec 能力扩展约 60 行（推断）。
- 本仓扩展属于 MMW 自有能力。它是放进 fork，还是作为上游旁边的 reference，是实现选择。R12 选了 fork；本轮不重判，只标明它的类型是能力。

**`to-tickets`**（上游；原文 diff 5 个文件 +383/−35；上游原文 105 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| 第 10 行 | 理（PC10、H6） | 原则，加本地一句 |
| 第 1 步第 20 行 | 路 | PB1 |
| 第 3–5 步（切片、五问、四行判据、blocking edges、Owns） | 能（MMW 的核心能力扩展）、理（PC2、PC12，就地写了理由） | 留在能力里；理由换成「点名原则 + 本地一句」 |
| 第 6 步问用户 | 能力自带的人工闸门（L7 A.3 允许） | 能力 |
| 第 6 步第 113–119 行子代理段 | mode `## Subagents` | mode |
| 第 7 步 lint 与发布 | 令 | 能力 |
| 第 8 步第 160 行 | 路 | PB1 |
| `<issue-template>` | 模（被脚本按字面读，W4） | 能力持有；登记进锚点表 |
| `cutting-interface-tickets.md`、`ambiguity-scan.md`、`person-ticket.md` | 能、模 | 能力 |

- **纯能力剩余**：约 450 行（推断）。它是一项真能力：一批票就是有名字的交付物。

**`triage`**（上游；原文 diff 4 个文件 +58/−25）

| 段落 | 混装 | 应去层 |
|---|---|---|
| description | 路（本仓加） | 回上游 |
| 第 41 行 | 能（本仓的标签约定） | 配置（`docs/agents/triage-labels.md`） |
| 第 70 行 | 路（流水线来的 issue 转读 reference） | PB8 |
| 第 5 步 `ready-for-agent` 第 82 行 | 顺、路 | PB11 |
| 第 90 行 `dispatch.sh route` | 令、顺 | PB8 |
| `references/pipeline-issues.md` | 顺、路、令、能 | PB8（早上的队列就是它的主体） |
| `AGENT-BRIEF.md` 本仓改写部分 | 路（「`to-spec` reads the agent brief」）、能 | 能力；路由句进 PB11 |

- **纯能力剩余**：上游 112 + 207 + 105 行，加上本仓对 brief 的定位句（推断）。

**`wayfinder`**（上游；原文 diff 3 个文件 +30/−15）

| 段落 | 混装 | 应去层 |
|---|---|---|
| description 与调用方式 | 路（本仓改成模型可触发，并加了触发句） | 回上游；由 mode 路由 |
| 第 20、112 行的 `mmw:map` 标签 | 配置 | `docs/agents/issue-tracker.md` `## Three label sets` 已经持有；技能正文只点名 |
| 第 37 行 `<effort>` 目录名 | 配置、约定 | 放进一份约定文件，由 PB2、PB3 与 `prototype` 规则 1 共同引用 |
| 第 76–78、114 行 | host 中立改写、mode `## Subagents` | 能力（host 中立必须保留）；子代理默认值进 mode |
| 第 6 步第 126 行 | 路 | PB2 |
| `interface-and-remake.md` | 顺（带界面的地图结构）、能 | PB2 与 PB3（地图变体的规则簇） |

**`prototype`**（上游；原文 diff 5 个文件 +166/−23）

| 段落 | 混装 | 应去层 |
|---|---|---|
| EXP 分支（`EXP.md`、`evidence-page.md`、`SKILL.md` 第 16 行） | 能（本仓扩展） | MMW 能力扩展，放在上游目录旁 |
| 规则 1 `prototypes/<effort>/…` | 配置、约定 | 约定文件（同 `wayfinder` 第 37 行） |
| 规则 6 | 能（记录 verdict）、顺（并进正式代码；UI 胜出方案交给 Claude Design） | 记录方法留下；「之后做什么」进 PB1 与 PB3（同时补上 N10 B4：LOGIC、EXP 分支没有下一步） |
| `UI.md` 第 3 步第 83 行、`### When there is no app yet` | 能（本仓扩展）、顺（脚手架留到第一次 pull） | 能力；「何时拆」进 PB3 |
| `UI.md` 第 6 步 `## State list` | 模（被 `pull_design.py` 第 983 行按字面读，R12 M21） | `design-pages` 的 reference（R12 K-14），属于 W6 |
| `UI.md` `## Next` | 路 | PB3 |

**`grill-with-docs`**（上游；+1/−1）：第 7 行末句「name the `to-spec` skill as the next step, in this same session」是路和 mode 的阶段边界内容，去 PB1。纯能力剩余是上游原文。

**`improve-codebase-architecture`**（上游；+36/−86）
- `HTML-REPORT.md` 改用 `diagram-design`：能。
- 第 41 行免掉 `diagram-design` 的 §3：调用方限定被调能力，属于 L7 C.2 的正当写法，留下。
- `### 4. Hand the decision on`：路，去 PB1 与 PB9。

**`grilling`**（上游；+18/−0；上游原文 28 行）
- 第 28 行：理（PC9、PC10），去 mode `## Autonomy` 与原则。
- 第 30–44 行：理（PC19、PC21、PC24），去三条 pstack 原则加 PC21、PC24。
- 纯能力剩余：上游 28 行。
- merge-note 自己也写了「上游若自己写入形成推荐答案时的思考 … 删掉我们这一段」，说明作者本来就把这段当作外加的判断，而不是 grilling 的能力。

**`tdd`**（上游；+3/−3）
- 第 22 行、第 38 行的票相关句（T28）：去 PB5 的限定句。
- 第 26 行的 host 中立改写：留下。
- 纯能力剩余：上游原文 174 行。

**`resolving-merge-conflicts`**（上游；+4/−4）
- 「clean merge 但检查变红」的扩展：能，留下。
- 「After a clean merge of `origin/<base branch>`, identify each ticket…」：顺，去 PB5 第 1 步。

**`to-questionnaire`、`grill-me`、`handoff`、`wait-what`、`teach`**（上游；小改）
- 改动都是 host 中立措辞或能力本身，包括 `wait-what` 的 `VISUAL.md`（+22）和 `teach` 的工作区规则（+11）。
- 没有顺、路、理。纯能力。

**`research`、`diagnosing-bugs`、`domain-modeling`**（上游；零差异）
- 纯能力。
- `diagnosing-bugs` Phase 5「Flag this for the next phase」是上游自带的「交给下一阶段」，没有点名技能（N10 B6）。修 bug 之后的去向由 PB9 承担，技能本身不动。

**`codebase-design`**（上游；+3/−1）
- 第 10 行「This skill is a reference, not a process … the task that brought you here decides what you do next」：路（本仓加）。有了 mode 与 playbook 以后，这是一句声明，删掉能回到原文。
- 第 16 行术语规则的放宽：能，留下。

**`wizard`**（上游；+5/−5）：bash 3.2 细节等，是能力。纯能力。

**`setup-matt-pocock-skills`**（上游；6 个文件 +55/−42）
- 第 17、51、63 行（本仓加）：理（领域）和顺，去 PB13。
- 第 82–84 行写进 `AGENTS.md` 的 `## External References` 与 `CLAUDE.md`：能（本仓的仓库格式），留在能力里或去 PB13。
- 种子文件：配置模板，留下。

**`writing-for-agents`**（上游；3 个文件 +211/−2）

| 段落 | 混装 | 应去层 |
|---|---|---|
| `SKILL.md` 第 8 行（本仓加的指向 SSR 的一句） | 路 | 回上游原文 |
| SSR 事实 1–6 | 理（PC7、PC16，以及写技能用的原则） | 原则（写作类），或者作为仓库文档里的写作规范 |
| SSR 事实 7、`### Hand-offs` 第 5 条 | 元规则（T38） | 改写为：下一步住在 playbook；能力技能不写调用方 |
| SSR `### Checks` 各节 | 能（写技能与审技能的判据） | 仓库文档（R12 K-38 的 `docs/skill-set/`）；PB14 点名 |
| SSR `## Editing`、`## Verifying` | 顺、理（PC21、PC25） | PB14 的步骤，加原则 |
| `REVIEWING-A-SKILL-SET.md` | 顺、能 | PB14 的规则簇，或 PB14 的 reference |

**`diagram-design`**（第二个上游；merge-note 记的是「画完给谁看」的取舍）：能。调用方免掉 §3，是 L7 C.2 的正当写法。纯能力。

### 4.3 MMW 自有的其他能力技能

**`design-pages`**（264 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| 标题与第 8–10 行 | 理（PC16、PC8） | 原则，加本地一句 |
| `## Find your moment` | 路（能力内部的分支表） | 留下。它分的是这项能力内部的四种做法，不是任务之间的顺序 |
| 第 21 行（只有带 Claude Design 工具的会话能做；派出的 worker 从不做） | 能力自带的闸门、路 | 闸门留下；「worker 从不做」进 PB5 规则 |
| `## The state list` | 模 | 与 `state-list-format` 一起放（W6） |
| `edit-pages.md` `## Next`；`pull.md` `## After the first pull`、`## Reached from here`、`## A contract child answered by this pull` | 顺、路、令 | PB3（与 PB4 的 `contract` 行） |
| `pull.md` 第 1–4 步、`draw.md`、`design-system.md`、两份模板 | 能、令、模 | 能力 |

- **纯能力剩余**：约 235 行（推断）。

**`write-screen-contract`**（259 行）
- 第 8–10 行：理（PC8、PC10），并带本地理由。原则，加本地一句。
- 第 1–7 步与 `Re-runs`：能力内部。
- `## Next`：路，去 PB3 与 PB2。
- 纯能力剩余：约 250 行。

**`retro`**（210 行）
- 第 8 行：顺，去 PB4。
- 第 16–35 行：理（PC11、PC19）加这项能力的立场。原则，加本地一句。
- 第 1–13 步：能力内部。
- 第 10 步门槛与 `## Prevention destinations`：理（PC25）加领域规则。原则，加本地表。
- 第 186 行：路，去 PB4。
- 纯能力剩余：约 205 行。

**`advisor`**（75 行）
- description 与 `consulting.md` `## When it is worth a session`：触发（路）和理（PC20），去 mode 触发器与原则。
- `## Start it`：令。
- `## The answer`：理（PC9）。
- `## The brief`：模。
- `advising.md`：能，外加 PC15、PC24。
- 纯能力剩余：约 65 行。

**`exe-release`**（447 行）

| 段落 | 混装 | 应去层 |
|---|---|---|
| `SKILL.md` 第 1–5 步 | 顺、令、能 | PB10 |
| 第 10 行「Ship what is on the current branch now」 | 理（PC9、PC24 的本地实例） | PB10 所有权行 |
| `driving.md` | 顺、令、理（PC5：「Do not resume from session memory」） | PB10 规则簇 |
| `key.md`、`new-product.md` | 能、模 | 能力（写 release manifest、把产品接进出包系统），可以单独调用 |

- **纯能力剩余**：约 320 行（推断）。

**`code-checkers`**（299 行）
- 第 6、8 步：顺（接入顺序），去 PB13 排序；步骤本身是能力内部的。
- 第 5 步探测：理（PC2），原则加本地一句。
- 纯能力剩余：约 295 行。

**`manage-agents-md`**（387 行）
- 第 8 行：理（这项能力的立场），留下。
- 第 50 行：mode `## Subagents`。
- 其余：能、模。
- 纯能力剩余：约 385 行。

---

## 5. 技能之外的文字

### 5.1 `dispatch.sh` 拼出的启动提示词

| 位置 | 原文 | 混装 | 应去层 |
|---|---|---|---|
| 第 108 行 `AUTONOMOUS` | 「You are operating autonomously. The user is not watching …」 | 理（PC9、H6） | mode `## Autonomy`。提示词写上 mode 名以后，这一句是第二份（SSR `### Prompts written for other agents` 第 2 条）。它现在留在提示词里，是因为 Cursor 收不到 `shared.md`（N9 D2，推断）；mode 加载之后，这个理由不再成立 |
| 第 109 行 `PRODUCT_RULES` | 「Several tickets run on this machine at once. Before you start, reach or stop the product, read 'Five rules …' in the ui-acceptance skill.」 | 路（字面指针）、理 | PB5 的规则簇指针；「Five rules while the product is running」登记进锚点表（R12 M19：测试不钉这句） |
| 第 1949 行 worker 提示词 | 「Use the implement skill to work ticket #$number.」 | 路（入口） | 改为「用 mode，跑 PB5，票号 n」。多行不受 H4 限制（1.3 节）。测试钉着首句（R12 M19：`test_dispatch.sh` 第 2830、6984、7199 行），测试跟着改 |
| 第 1729–1740 行 Memory 索引尾句 | 「the implement skill's `## Shared experience while implementing` says how to use them」 | 路（字面锚点） | 锚点表 |
| 第 1967 行 reviewer 提示词 | 「Use the code-review skill to review ticket #$number from base commit $base.」 | 路（W2） | 与 PB6 入口一起改 |
| 第 1833 行 reviewer Rules 包 | 数据 | 配置 | 留下 |
| 第 2072 行 advisor 提示词 | 「Use the advisor skill.」加简报 | 路 | 留下（能力入口） |
| 第 79 行头注释 | 「`ack` is in SKILL.md under `## On waking`, which every moment shares」 | 路（维护者注释） | 锚点表 |
| 第 2344–2360 行 `check` 自动重装（R12 M7） | 行为，不是文字 | 与根 `AGENTS.md`「`install.sh` runs only when the user explicitly authorises it」冲突（R12 U-5） | 待用户决定，第 10 节 |

### 5.2 hook 拒绝文字

| 位置 | 混装 | 说明与去向 |
|---|---|---|
| `tool-guard.py` 第 71–75 行 `REFUSAL` | 令、顺（关票只走 `--closeout`） | 下一步写在拒绝里是 `CODING_STANDARDS.md` 的三段要求，留在脚本；它指向 PB5 第 8 步 |
| `tool-guard.py` 第 76–80 行 `NO_QUESTION` | 理（H6）、顺（只写了 worker 的出路） | 与 `implement` 第 23 行不一致：hook 要求写 `ABANDON: AC<n> decision` 并开 needs-triage 子票，implement 只开 `decision` 子票然后继续（N11，本轮两处原文都读过，确认不一致）。它还管 reviewer：`tool-guard.py` 头注释第 33–37 行写「worker and reviewer」，但 `code-review` 里没有承接的文字。规则去 mode `## Autonomy`；出路去 PB5，PB6 也要有；hook 文字只指向一处。测试限制总长 ≤ 256 字符（R12 M2） |
| `tool-guard.py` 第 234–246 行 `no_kill` | 能（`ui-acceptance` 规则 1）、令 | 留在脚本；规则的家是 `ui-acceptance` |
| `turn-guard.py` 第 306–311 行 | 顺（`arm` → 照输出做 → 退出非零就开 `fault` 子票 → 结束回合）、路 | `night.md` §3 没有这一行，而 `one-ticket.md` 第 3 步和 `night.md` 事实表第 19 行都把 `MMW turn guard:` 送到 §3（N11，本轮再核）。PB4 的重入表补上这一行；脚本保留命令 |

### 5.3 watchdog 与 relay 送进会话的文字

- **`relay.py` 第 385–389 行 `wake_text`**：只有「#<n> <event>」，是路（纯数据）。收件人由第 291–299 行的 `WAKES` 按角色决定：reviewer.reported、reviewer.lost、worker.queued 发给 worker；ticket.passed、returned、refused、`child.opened`（contract、fault、decision）、worker.lost 发给 orchestrator（`relay.py` 头注释第 37–44 行）。
  - 这是事件链的脚本那一半（W1），留在脚本层。
  - 动作那一半要按角色集中：worker 的在 PB5，orchestrator 的在 PB4 与 PB7。
- **`watchdog.py` 八种告警**（第 94–109 行，R12 M16）：
  - 每种都在文字里带了下一步，其中两种按节名引用「night.md's Exit codes of resume」。
  - `night.md` §3 只有 `watchdog: #<n> silent since …` 一行。
  - 做法：
    - 脚本的一行文字保留命令（H4，必须一行）；
    - PB4 的重入表每种告警一行，写清什么时候判断用哪条命令；
    - 节名引用登记进锚点表。

### 5.4 `verify-ticket.py` `resume_at`（第 2148–2182 行）

- 这个函数按编号返回续跑点，从「step 1」到「step 5 (worker reverify on HEAD)」，例如「step 1, then step 4 onward」「step 3 (worker.decided, no reviewer.reported)」，由 `--preflight` 打印成 `RESUME:` 行。`implement` 第 74 行让 worker「carry on at the step its `RESUME:` line names」。
- 所以 PB5 `#### Closing steps` 的编号与这个函数是一个整体（W3）。
- 它的 docstring 引用的段落「A ticket that already carries a run of your own」在 `implement` 里已经不存在（第 9 节第 1 条）。
- R12 K-47 已经指出：没有自己的运行记录时它返回 `None`，不打印 `RESUME:`。

### 5.5 `mmw-v2/prompt/shared.md`

本轮用 `diff` 确认它与 `~/.claude/CLAUDE.md` 逐字相同。它是用户级提示词，经 `install.sh` 发给 Claude、Codex、Pi、Grok 四个宿主；Cursor 的用户级提示词在应用里维护，不从这里来（根 `AGENTS.md` `## Key Conventions`）。

| 段 | 混装 | 类型对应 |
|---|---|---|
| 前言「Five facts」 | 理（全部规则的理由来源） | 用户的立场，不属于 MMW |
| 前言末段「A session a script started with no person in it …」 | 路（无人会话怎样套用这些规则） | 与 mode `## Autonomy` 同类 |
| 规则 1–3 | 理（PC9、不制造异议） | mode `## Autonomy` 同类 |
| 规则 4–9 | 能（回复写法） | mode `## Writing the reply` 同类（pstack mode 有这一节） |
| 规则 10–15 | 理（PC10、「失败自己重做」、先读再改、PC13、先搜现成、PC14） | 原则同类 |

**判定**：
- `shared.md` 是 H1 条件下 4 个宿主上唯一常驻的通道，结构上最接近 pstack 的 `reminder` 加 mode 常驻节。
- 它同时装着 mode 类和原则类内容，而这些规则在技能里各有一份翻版（N9 D1、D4、D5、D6、D16、D17）。
- 去重的方向有两个：
  - 技能里的翻版改为点名原则或 `shared.md` 的规则号；
  - 或者原则文件持有全文，`shared.md` 保留一行索引。
- 这个文件是用户本人写给所有会话的话，改它的结构属于用户的决定（第 10 节 U5）。
- 与 PC18 的张力（规则 11「redo it yourself」对 `ui-acceptance` 规则 4、5 的「停下」）需要在 mode 里写明优先级（N9 9.3）。

### 5.6 根 `AGENTS.md`

| 段 | 混装 | 应去层 |
|---|---|---|
| 开头三段（身份、目录、自消费） | 仓库文档 | 留下 |
| `## Self-hosting boundary` | 理（仓库级，H5 的出处） | 留在仓库文档（每个会话都加载它）；PB4、PB5、PB14 按名点它 |
| `## Package Manager`、`## Commands`、`## External References` | 令、路（指针） | 留下；将来路由表加一行指向 mode |
| `## Key Conventions` | 配置事实 | 留下 |
| `## Gotchas` 第 1 条发布四步 | 顺（T35） | PB14 的步骤；`AGENTS.md` 留指针和「watch 期间不做第三步」这一条（H5） |
| 其余 Gotchas | 能（环境陷阱） | 留下 |
| `<important if … night …>` | 能（本仓私有事实） | 留下，由 PB4、PB5 引用（L7 A.11「项目私有组件」同类） |
| `<important if … upstream …>` | 顺 | PB14，加 `merge-notes/README.md` |
| 最后一行「Before working in a subdirectory …」 | 常驻规则（仓库级） | 留下 |

### 5.7 其他仓库文档

- **`CODING_STANDARDS.md`**：`## Skills and scripts` 第 4 条是 PC3 加 PC1；`## State and configuration` 第 3 条是 PC4、PC5、PC6；第 4 条是 ADR 0023 的机制（N9 D7–D10）。
  - 它由 Standards axis 整份读，属于仓库文档。
  - 应保留本仓的代码规则，把跨任务立场换成点名原则。
  - 它与 ADR 0027 的冲突见 N11。
- **`TESTING.md`**：`## What a test proves` 是 PC23；`## Which suites a change needs` 是 PC14 在本仓的实例。仓库文档。
- **`docs/agents/issue-tracker.md`**：配置（tracker 操作、三组标签），加 `## Morning queries`（顺，去 PB8）。
- **`docs/agents/domain.md`、`triage-labels.md`**：配置。
- **`CONTEXT-MAP.md` 与七份 `CONTEXT.md`**：仓库文档。按 SSR `### Vocabulary` 最后一条，行为规则不该只住在词表里。本轮没有逐条清点词表里的行为句（第 10 节 U10）。

---

## 6. 纯能力剩余汇总

| 技能 | 现有行数（`.md`） | 拿掉顺、路、理后的纯能力 | 约行数 | 核实 |
|---|---|---|---|---|
| `implement` | 212 | 上游原文 | 15 | 实测（`git show 5b1a4c51`） |
| `dispatch` | 292 | 改 host、模型、runner；开任务板；脚本位置 | ~35 | 推断 |
| `code-review` | 322 | 上游双轴评审原文 | 87 | 实测 |
| `verify-ticket` | 59 | 命令参考（外加脚本） | ~25 | 推断 |
| `grilling` | 46 | 上游原文 | 28 | 实测 |
| `tdd` | 174 | 上游原文 | 174 | 实测（只差 3 句） |
| `to-spec` | 143 | 上游 75 行，加 MMW 的 spec 扩展 | ~135 | 推断 |
| `to-tickets` | 455 | 基本全部 | ~450 | 推断 |
| `triage` | 459 | 上游三份，加 brief 定位 | ~425 | 推断 |
| `wayfinder` | 145 | 上游，加 host 中立 | ~128 | 推断 |
| `prototype` | 348 | 上游，加 EXP 与证据页 | ~330 | 推断 |
| `design-pages` | 264 | pull、draw、edit、design-system、模板 | ~235 | 推断 |
| `write-screen-contract` | 259 | 第 1–7 步、`Re-runs`、格式 | ~250 | 推断 |
| `retro` | 210 | 第 1–13 步、目的地表 | ~205 | 推断 |
| `ui-acceptance` | 381 | 全部，加接收过来的 `writing-interface-code.md` | ~430 | 推断 |
| `exe-release` | 447 | `key.md`、`new-product.md` | ~320 | 推断 |
| `advisor` | 75 | 两个角色文件 | ~65 | 推断 |
| `code-checkers` | 299 | 全部 | ~295 | 推断 |
| `manage-agents-md` | 387 | 全部 | ~385 | 推断 |
| `writing-for-agents` | 312 | 上游 `SKILL.md` 与 `SKILL-MECHANICS.md` | ~103 | 实测（SSR 176 + RSS 33 行是本仓加的） |
| `setup-matt-pocock-skills` | 316 | 上游，加 `AGENTS.md` 写法 | ~300 | 推断 |
| `resolving-merge-conflicts` | 14 | 上游，加「clean merge 变红」的扩展 | 14 | 实测 |
| `improve-codebase-architecture` | 144 | 上游，加 `diagram-design` 的用法 | ~140 | 推断 |
| `grill-with-docs` | 7 | 上游 | 7 | 实测 |
| `codebase-design` | 197 | 上游 | ~195 | 实测（差 3 行） |
| `diagnosing-bugs`、`domain-modeling`、`research` | 138、181、12 | 全部 | 同左 | 实测（零差异） |
| `grill-me`、`handoff`、`to-questionnaire`、`wait-what`、`teach`、`wizard`、`diagram-design` | — | 全部 | 同左 | 实测（差异只在 host 中立或能力本身） |

**离开能力技能的内容总量**（推断，数量级）：
- `implement` 约 197 行，分给 PB5、`ui-acceptance` 和原则；
- `dispatch` 约 257 行，分给 PB4、PB5、PB7 和 mode；
- `code-review` 约 101 行进 PB6，另有 206 行 axis 文件改作 PB6 的 reference；
- 各技能的「下一步」句 17 句；
- `grilling` 18 行进原则；
- `verify-ticket`、`ui-acceptance`、`to-spec`、`to-tickets`、`triage`、`wayfinder`、`prototype`、`design-pages`、`write-screen-contract`、`retro` 合计约 150 行。
- 这些是估计值，实际搬完再量（第 10 节 U6）。

---

## 7. 天然整体

### 7.1 有可核实运行故障理由的整体（都要一起搬，没有一组要求留在原处）

| # | 整体 | 组成 | 拆开时哪个读者会走错 | 证据 | 处理 |
|---|---|---|---|---|---|
| W1 | 事件 → 收件人 → 动作 | `relay.py` `WAKES`（谁醒）；共同的醒来协议（重跑、读票、`ack`）；每个角色一张「事件 → 动作」表 | 协议与动作分住在不同文件时，拿不到协议的角色会漏步。这已经发生了三处：(a) worker 走 `dispatch` 表第 1 行直接进 `implement`，读不到 `## On waking` 第 1 步「Run that command again first」（N10 B9）；(b) `one-ticket.md` 把 `MMW turn guard:` 送到 `night.md` §3，§3 没有这一行（N11）；(c) 八种 watchdog 告警只有一种在 §3 有行（R12 M16） | 本轮读过 `dispatch/SKILL.md`、`night.md` §3、`one-ticket.md`、`relay.py` 第 37–44 行、`watchdog.py` 第 94–109 行 | 醒来协议进 mode；每个角色的全部事件行进它自己的 playbook（worker 进 PB5，orchestrator 进 PB4 与 PB7）；脚本保留收件人映射；`sub-issues.md` 第 11 行的 kind → 读者与 `WAKES` 对齐 |
| W2 | 启动提示词的形状 ↔ 接收方的入口行 | `dispatch.sh` 第 1967 行 ↔ `code-review` 表「names no axis」；第 2072 行 ↔ `advisor` 表「your prompt is a brief and nothing else」；第 1949 行 ↔ `implement` description | 改了一边，另一边的会话会读错文件（reviewer 被当成 axis，或反过来） | 两边原文 | 同一次提交里改；PB6 入口按提示词形状写 |
| W3 | 收尾步骤编号 ↔ 续跑 | PB5 `#### Closing steps` 的编号 ↔ `verify-ticket.py` `resume_at` 的字面「step N」 ↔ `writing-interface-code.md` 三处「closing step 1」 ↔ `tool-guard.py` `REFUSAL` 指向的第 8 步 | 只改编号不改脚本，续跑的 worker 会从错的一步开始 | `verify-ticket.py` 第 2164–2181 行返回字面步骤号（step 1 到 step 5） | 编号与脚本同一次提交改，或脚本改为返回节名；docstring 同时修正 |
| W4 | 票模板的标题 ↔ 解析器 | `to-tickets` `<issue-template>` 的 `## Parent`、`## Owns`、`## Read first`、`## Seam`、`## Acceptance criteria` ↔ `verify-ticket.py`（`## Parent` 19 处、`## Owns` 9 处、`## Read first` 7 处、`## Acceptance criteria` 5 处）、`events.py`、`dispatch.sh` | 模板改了而解析器没改，lint 与 `--preflight` 会误读或拒绝 | 本轮 grep 计数 | 模板由 `to-tickets` 持有；标题常量登记进锚点表 |
| W5 | 判据形状 ↔ oracle 成功标记 | `cutting-interface-tickets.md` `## Criterion shapes` 的 `EXPECT:`（`STORY OK`、`BOUNDARY OK`、`JOURNEY OK`、`HARNESS OK`）↔ 四个 oracle 的输出 | 两边不一致，票永远过不了 | 原文 | 同一次提交里改 |
| W6 | `## State list` 标题 ↔ `pull_design.py` | `prototype` `UI.md` 第 6 步、`design-pages` `## The state list` ↔ `pull_design.py` 第 983 行 `^## State list` | pull 会找不到 state list | R12 M21 | 格式由 `design-pages` 的 reference 持有；标题登记进锚点表 |
| W7 | 告警一行 | `watchdog.py` 的告警（包括它的下一步）必须在同一行 | 换行就提交，后半句成了第二条输入 | H4、R12 M1 | 留在脚本；PB4 的行只写判断 |

**配置层的成对项**（不属于文字混层，照样必须成对改）：
- `SKILL.md` 的 `disable-model-invocation` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation`（N10 §9）；
- `.mmw/target.json` 的字段与 `target_config.py --check`、`product-answers.md`；
- `retro` 第 12 步的 JSON 形状与 `retro.py finalize`。

### 7.2 看起来像整体、其实可以按类型拆开的

| 段 | 为什么可以拆 |
|---|---|
| `implement/SKILL.md` 全文 | 四节各是一种类型：读入与收尾是顺，写码规则是能加理，Memory 是能加令。各节之间只按节名互引，没有运行时共享的编号（W3 的编号除外，编号跟着收尾一起搬） |
| `dispatch/SKILL.md` 的表与 `## On waking` | `## On waking` 本来就是「every moment shares」（`dispatch.sh` 第 79 行），属于 mode 的重入协议，不属于 dispatch 的某一个时刻 |
| `night.md` 开头第 3–7 行 | 是理（PC10、PC1），换成点名原则加本地一句 |
| `night.md` §4 收口轮 | 整块都是 PB4 的规则簇，同一种类型，整块搬，不必再切。这是按类型判定，不是「不值得」 |
| `ui-acceptance` 的五条规则 | 规则 1、2 是领域能力，规则 3–5 是原则的实例 |
| `sub-issues.md` | 第 11 行（读者）属于 W1，第 13–23 行（kind 表）属于 PB5 |
| `pull.md` | 第 1–4 步是能力；`Reached from here` 与处理 `contract` 子票的段落是 PB3 |
| `shared.md` | N9 §8 说它是整体，理由是规则号互引、五个事实是理由来源。这只说明「按规则号引用它」是稳定的，不妨碍技能里的翻版改成点名它 |

---

## 8. playbook 候选（由第 2 节推出，每份都有现成原文）

「所有权行」和「Reply 行」按 L7 A.2 的模板取自原文。列出的原文就是可搬的材料，不需要新写规则。

| # | 名字 | 对应用户草图里的哪一类 | 原文来源（T 编号） | 调用的能力与 lever | 自有的闸门与交付物 |
|---|---|---|---|---|---|
| PB1 | `define-a-change` | 白天定义 | T16–T18、T22–T24、T14、T36 主流程第 1–3 步（包括「要不要走 spec 流水线」与「谁来检查」，N10 B3） | `grilling`、`domain-modeling`、`prototype`、`to-spec`、`to-tickets`、`verify-ticket --lint/--publish` | 交付物是已发布并通过 lint 的票；问用户的只有产品事项 |
| PB2 | `map-a-large-effort` | 大型、路线看不清的工作 | T21、T17、T36 on-ramp 第 3 条 | `wayfinder`、`research`、`to-spec`（按拆分循环） | 地图清空以后才进 PB1 |
| PB3 | `design-an-interface` | 白天定义的界面分支 | T22、T25、T26、T16 第 2 步、`interface-and-remake.md` | `prototype` UI、`design-pages`、`write-screen-contract`、`to-spec`（`revising-a-spec.md`） | 按 `改动分类` 分四路；拆脚手架的时机 |
| PB4 | `run-a-night` | 夜间编排 | T7、T27、T37 的 orchestrator 部分、`turn-guard` 与 watchdog 的行 | `dispatch.sh`（open、advance、status、route、findings、memory-list、reverify、summary、suspend）、`retro` | 交付物是 `NIGHT SUMMARY` 与 `spec.retroed` |
| PB5 | `work-a-ticket` | 做一张票 | T1–T5、T9、T13、T15、T28、T29、T37 的 worker 部分 | `verify-ticket.py`、`dispatch.sh`（integrate、start reviewer、wait、ack、adopt）、`tdd`、`resolving-merge-conflicts`、`ui-acceptance` | 交付物是 `--closeout` 过的收尾评论；续跑按 `RESUME:`（W3） |
| PB6 | `review-a-ticket` | 评审一轮 | T10、T11 | 四个 axis 简报（reference）、`verify-ticket.py --review` | 交付物是 `REVIEW` 报告 |
| PB7 | `run-one-ticket` | 单票 | T8 | `dispatch.sh`（open-ticket、start、resume、land） | `land` 退出 0 |
| PB8 | `morning-acceptance` | 早上验收与 finish | T20、T19 的第 90 行、T34、`night.md` §5 末段与 §6 | `triage`、`dispatch.sh route`、`finish` | 只有用户验收之后才 `finish` |
| PB9 | `fix-a-bug` | 修 bug | T36 on-ramp「Something's broken」、T24（N10 B6 的缺口） | `diagnosing-bugs`，按有没有 seam 转 `improve-codebase-architecture` 或 `tdd` 或 PB1 | 先有能变红的循环 |
| PB10 | `ship-a-release` | 出包 | T30 | `release-flow.sh`、`exe-release` 能力（manifest） | 用户装机实测（PC29） |
| PB11 | `triage-an-issue` | 分诊（外来 issue） | T19 第 82、94 行，T36 on-ramp 第 1 条 | `triage`、`to-spec`、`to-tickets` | 结论是四种结果之一 |
| PB12 | `investigate` | 调研 | `research` 三步、`wayfinder` 第 5 步（结果放哪里、怎样回到地图）、`to-spec` 模板 `## Sources`、根 `AGENTS.md`「a spec may cite」、`implement` 第 16 行「the part of a research file that answers its question」 | `research`（后台代理） | 研究文件落在仓库里，并被一个决定引用 |
| PB13 | `onboard-a-repository` | 给仓库接入 MMW | T32、T33、`target_config.py --check`（`night.md` §1b 第 54–56 行）、`to-spec` Testing Decisions 里的 contract ticket 说法 | `setup-matt-pocock-skills`、`manage-agents-md`、`code-checkers`、`ui-acceptance` | `.mmw/target.json` 完整；`check` 退出 0 |
| PB14 | `authoring-a-skill` | 写技能 | T35、T38、SSR `## Editing` 与 `## Verifying`、`merge-notes/README.md`、`downstream-notes/README.md` | `writing-for-agents`、测试套件、`install.sh --check` | 发布四步；watch 期间不移动已安装 checkout（H5） |
| PB15 | `session-pickup` | 暂停与接续（阶段边界） | T36 `PHASE-BOUNDARIES.md`、`### Context hygiene`，T6 `## On waking`，`implement` 第 74 行，`driving.md` 第 5 行 | `handoff` | 不从会话记忆续跑（PC5） |

**不单列 playbook、由 mode 路由表一行直接指向能力的**：
- 咨询 advisor（`advisor` 是有交付物的能力，L7 C.3）；
- 改模型或 runner（`dispatch` 的 `editing-models.md`）；
- 开任务板；
- 画图（`diagram-design`）；
- 写 AGENTS.md（`manage-agents-md`）；
- 教学（`teach`）；
- 问卷（`to-questionnaire`）；
- 向导（`wizard`）。

这些都是用户直接调用的单一能力，没有跨能力的顺序可装。判据是 L7 C.3 与 C.6 信号 5：只调用一个技能、没有自己的门槛或交付物的 playbook，是形式上的拆散。

**本仓私有的流程**（拉上游 subtree）：留作仓库文档 `merge-notes/README.md`，由根 `AGENTS.md` 的 `<important if>` 指向。它只对本仓维护者适用，不随 MMW 发给消费仓库（L7 A.11 同类）。

---

## 9. 本轮新发现的不一致

1. **`verify-ticket.py` 第 2150–2151 行的 docstring 已经过时。** 它引用 `implement` 里「the paragraph starting "A ticket that already carries a run of your own"」，全仓 grep 只命中这段 docstring 本身；现在的原文是第 74 行「A ticket you are prompted back into: …」。函数行为没有受影响，但 W3 的两端已经靠 docstring 对不上了。
2. **`NO_QUESTION` 管得到 reviewer，却只给 worker 出路。** `tool-guard.py` 头注释第 33–37 行说 `issue-<n>` 目录里的「worker and reviewer」都受管；`NO_QUESTION` 给的出路（`Decisions I made on my own`、`ABANDON: AC<n> decision`）只有 worker 有；`code-review` 各文件没有任何承接。N11 已经列为缺边，本轮读原文再次确认。
3. **PC9 漏计。** `to-spec/SKILL.md` 第 6 行把「what the user sees, what happens to money, or what is in scope」列为不归 agent 决定的事，N9 PC9 的位置清单没有列它。
4. **N9 行号偏移。** N9 部分行号比本轮 `cat -n` 小 1，例如 PC5 的「`dispatch/SKILL.md:7`」原文在第 8 行。只影响按行号跳转，不影响结论。

N10 B7（三处「凭 description 进来又被送回 `implement`」）与 N11 的 turn guard 缺行，本轮读原文确认仍然存在，已经并入 W1 与 T12、T15。

---

## 10. 未确定与实测方法

| # | 问题 | 为什么要定 | 怎么测 |
|---|---|---|---|
| U1 | mode 在五个宿主上怎样被加载：`AGENTS.md` 里一行、`shared.md` 里一行，还是启动提示词点名 | H1：没有 `mode: true`；R12 T1 | 在隔离的 home 里，每个宿主各开一个会话，给一个模糊请求，看它是否读 mode 并按路由表选 playbook |
| U2 | 原则做成 mode 目录下的文件（按路径读），还是做成技能 | H2：做成带 `disable-model-invocation` 的技能，在 Claude Code 上按名也读不到；做成模型可触发的技能，每个宿主的系统提示要多 29 条 description | 在隔离的 home 里，从 worker 会话按路径读 `…/principles/x.md`，五个宿主各一次；另外量出 29 条 description 的 token 数 |
| U3 | 技能目录下不带 frontmatter 的 playbook 文件，会不会被某个宿主当作技能扫进去 | 会的话，playbook 就会出现在技能列表里 | 在隔离的 home 里放一份假的 `playbooks/x.md`，看五个宿主的技能列表 |
| U4 | 启动提示词点名「mode + PB5」以后，worker 是否真的读 PB5，而不是去加载上游 `implement` | 上游 `implement` 回到原文以后，如果还装着，description 会竞争 | 在隔离的 home 里用假 tracker 跑一张票（`TESTING.md` 的隔离做法），看它打开了哪些文件 |
| U5 | `shared.md` 与原则文件谁持有全文 | `shared.md` 是用户自己写给所有会话的话 | 用户决定 |
| U6 | 第 6 节的「约行数」 | 都是推断 | 搬完以后用 `wc -l` 重量 |
| U7 | `NO_QUESTION` 在 reviewer 会话里实际拦截过没有 | 决定 PB6 要不要写出路 | 在 `~/.claude/projects` 等处的会话记录里 grep reviewer 会话中的「Nobody is at the screen」 |
| U8 | 上游 `implement`、`code-review` 回到原文后还装不装 | 装着会与 PB5、PB6 的入口竞争（U4）；不装则通用能力消失 | 先做 U4；要不要装影响用户看到的技能列表，交给用户确认 |
| U9 | paseo 与 herdr 的第一条提示词是不是作为参数传入 | 决定 H4 管不管启动提示词 | 读 `runners/paseo.sh`、`runners/herdr.sh` 的 `start` 实现体（N11 列为未读） |
| U10 | 七份 `CONTEXT.md` 里有没有只住在词表里的行为规则 | SSR 认定这是一种混层 | 逐份读 `docs/contexts/*/CONTEXT.md`，对每条词条的 `_Home_` 核对 |
| U11 | `dispatch.sh check` 的自动重装与「`install.sh` 只在用户授权时跑」之间的冲突 | 新架构发布后的第一次开夜就会触发（R12 U-5） | 用户决定：改成只报告，还是修改 `AGENTS.md` 里的规则 |

---

## 11. 本轮读了什么

**全文读过（`cat -n`）**：
- `dispatch`：`SKILL.md`、`night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md`；
- `implement`：`SKILL.md`、`saving-memory.md`、`writing-interface-code.md`；
- `code-review`：`SKILL.md` 与五份 references；
- `tdd/SKILL.md`；
- `verify-ticket`：`SKILL.md` 与两份 references；
- `ui-acceptance`：`SKILL.md` 与五份 references；
- `to-spec` 及其两份 references；
- `to-tickets` 及其三份 references；
- `triage/SKILL.md` 与 `pipeline-issues.md`；
- `wayfinder` 与 `interface-and-remake.md`；
- `prototype/SKILL.md` 与 `UI.md`；
- `grill-with-docs`、`grill-me`、`grilling`、`handoff`、`wait-what`、`to-questionnaire`、`research`、`resolving-merge-conflicts`、`wizard`、`diagnosing-bugs`、`improve-codebase-architecture`、`domain-modeling`；
- `design-pages` 的 `SKILL.md` 与 `pull`、`draw`、`edit-pages`、`design-system`；
- `write-screen-contract/SKILL.md`；
- `retro/SKILL.md`；
- `advisor` 三份；
- `exe-release/SKILL.md` 与 `driving.md`；
- `code-checkers/SKILL.md`；
- `writing-for-agents/SKILL.md` 与 SSR；
- `setup-matt-pocock-skills/SKILL.md`；
- 残留 `ask-matt/SKILL.md` 前 80 行与 `PHASE-BOUNDARIES.md` 前 30 行；
- 根 `AGENTS.md`；`CODING_STANDARDS.md`；
- `docs/agents/issue-tracker.md` `## Morning queries`；
- merge-notes 的 `grilling.md` 与 `implement.md`。

**部分读过**：
- `manage-agents-md/SKILL.md` 第 1–130、285–330 行；
- `codebase-design/SKILL.md`、`teach/SKILL.md` 前 40 行；
- `exe-release` 的 `key.md`、`new-product.md`，`code-checkers` 的 references，`write-screen-contract` 的 format 文件，`triage` 的 `AGENT-BRIEF.md`、`OUT-OF-SCOPE.md`，`prototype` 的 `LOGIC.md`、`EXP.md`：只看了标题结构。
- 这些地方「纯能力、无顺路理」的判定依据是标题结构与 merge-note 的描述，属于推断。

**脚本（按需读）**：
- `dispatch.sh` 第 100–125、1700–1745、1820–1840、1935–1975 行；
- `tool-guard.py` 第 1–120、230–289 行；
- `turn-guard.py` 第 1–80、296–320 行；
- `watchdog.py` 头注释与告警文字、第 805–820 行；
- `relay.py` 第 20–120 行；
- `verify-ticket.py` 第 2140–2175 行；
- `runners/orca.sh` 头注释。

**测量**：
- 上游已装技能与 squash `5b1a4c51` 的 `git diff --shortstat`，逐个技能；
- `git show 5b1a4c51` 取原文行数；
- 各项 grep 计数；
- `shared.md` 与 `~/.claude/CLAUDE.md` 的 `diff`。

**报告**：
- L7 第 0、A、B.1–B.2、C 节与 D.1–D.3 节；
- N9 第 4、8、9 节；N10 第 1、3、4、8、9、10 节；N11 全文；
- R12 第 0、1 节（M1–M30）。
- 其余 N、R、L 报告只按引用取事实，没有重读全文。
