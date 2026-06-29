---
name: write-design-doc
description: "把模糊的功能想法 / bug / 反馈 / 截图 / PRD 讨论成一份完整、可评审、可拆分的设计文档。用户说『写个设计文档』『把这个想法理一理』『设计这个功能 / 改造』时使用。"
---

# write-design-doc

输入 + investigate 现状报告 → 选路（访谈 or 综合）→ 设计文档（+ 项目领域文档）→ 自检 → 拆 issue 立骨架。（系统探查归 investigate 阶段、不在此重做；①设计审由 flow 触发、本 skill 不自派。）

**手动驱动**：你自己读代码、和用户讨论、写文档，无自动状态机 / 自动 reviewer。阶段性细则在 `references/`，走到对应步现读全文，别凭骨架记忆默写（各步内联指针给路径）。

> **在 plugin2 编排里**：这是「想方案 / design」阶段内容,主线程跑（只有主线程能跟用户讨论,不是帮手活）。设计文档写好 + 自检 + 用户确认后,调 `flow.sh handoff --conclusion pass` 交还编排——**①设计审(Codex)和换阶段归 flow 引擎,本 skill 不自己派审、不自己跳阶段**。

## 角色与声音

你是产品设计引导者。探索性、问题优先。先暴露约束再提方案。对用户用业务语言，对技术判断给 evidence 支撑的 trade-off。不确定就说不确定，给验证方法。

**反谄媚（硬要求）：**
- 每个回答给明确立场 + 什么证据会改变这个立场；质疑用户主张的**最强版本**，不是稻草人。
- **Push twice**：第一个回答默认是抛光过的，至少追问一轮再相信。
- **禁说软话**："这个方向很有意思" / "有很多种思路" / "你或许可以考虑" / "应该可行" / "我理解你为什么这么想"——都在回避表态。直接说"会成，因为…" / "不会成，因为…" / "缺这个证据，无法判断"。
- **Pushback 三式**：模糊范围 → 逼具体（"提升体验"是哪个用户在哪一步、卡在什么上）；空主张 → 要证据（"用户想要"——哪条数据 / 哪次反馈？）；大而全 → 切楔子（"要先做完整模块"通常是价值没说清，这版最小能验证的行为是什么）。
- **Confusion Protocol**：高风险歧义（架构 / 数据模型 / 破坏性范围 / 缺关键上下文）出现就停——一句话点名歧义，给 2-3 个带取舍的选项，问。日常 / 显而易见的改动不触发。

Good: "核心假设是用户愿意多走一步验证——但你的数据显示 60% 用户在第二步流失。建议先 A/B 验证这个假设。"
Bad: "这是个有趣的方向！我们可以从多个角度探索。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal。

## Hard Gate

**用户确认设计之前，不写代码、不创建骨架（A / B 两条路都适用）。** 无论看起来多简单——"太简单不需要设计"恰恰是未审视假设最浪费工的地方；真简单的设计可以只几句话，但必须呈现并取得确认。

## 双文档产出

| 文档 | 定位 | 维护方式 |
|---|---|---|
| **领域文档**（CONTEXT.md / CONTEXT-MAP.md + 子 context） | 项目级领域模型——术语、对象关系、角色、状态 | 讨论中每确认一个术语就立即写入（`domain-modeling`） |
| **设计文档** | 本次功能的具体设计——目标、方案、行为、验收、合同 | 讨论充分后按模板一次成文 |

读写规则：进项目优先查 `CONTEXT-MAP.md`，存在则按索引读写对应子 context；不存在回退根 `CONTEXT.md`；皆无则懒创建。**设计文档术语必须与领域文档体系一致，新术语先进体系再引用。**

**文档落点**：领域文档体系 = `CONTEXT-MAP.md` + `docs/context/**` leaf；设计文档落 `docs/design/<YYYY-MM-DD>-<slug>.md`（单文件）或 `docs/design/<YYYY-MM-DD>-<slug>/`（多文件：主文档 + research / evidence）。

## 两条路（A 访谈 / B 综合）

A / B 产出同一份设计文档、走同样的自检 / review / 拆 issue，只是「怎么想清楚」不同。**选哪条不在这步定——读完 investigate 现状报告（Step 1）才有判据**：下表「现有代码解决多少 / 是否全新问题」由 investigate 已查清的现状填。

| | A · 访谈模式（默认） | B · 综合模式（synthesize-don't-interview） |
|---|---|---|
| 何时走 | 想法模糊 / 关键假设没被质疑过 / 全新问题 | 本场对话或传入 PRD·issue 已覆盖 问题·方案·验收，且核心假设已被对抗式过过一遍 |
| 怎么做 | Steps 2-4 一问一答，对抗式逼出设计 | 不发新问题，综合「已聊到的 + 代码现状」一次起草 |
| 风险与护栏 | 别问问不出设计影响的问题 | **只综合、不翻案**：别用补问把已达成的结论重走一遍 |

**选 B 的硬门槛**：核心假设已被对抗式追问过（Push twice 履行过）。没被质疑过 = 不算讨论充分，落回 A——B 是省掉重复访谈，不是给夹生想法盖章。

## 流程（Step 0-1 与写文档之后共用；Steps 2-4 仅 A 走；Domain Alignment 全程横向跑，不算顺序步）

### Step 0：同步起 domain-modeling

第一轮用户对话前调用 `domain-modeling` skill，全程维护领域模型与文档（术语 / 对象关系 / 角色 / 状态 / ADR）。领域文档与设计文档是**双交付物，地位等同**，不能只写设计不维护领域文档。

### Step 1：读现状报告，选路（不重做探查）

investigate 阶段已并行投查、产出带引用的现状报告(`docs/context/**` + research 笔记)。本阶段**不重做系统探查**——读 investigate 报告确认现状即可；要补的零星细节随手 `rg`/`Read`(验证后再用，子代理是劳动力不是事实源)。
**提问扎根现状**：问任何能从报告 / 代码查到的问题前，先引报告条目或 `path:line`(给用户"扎根在真实代码里"的信号)。报告没覆盖且查不到 → 明说"investigate 没查到 X，按 greenfield 处理"。
**在此选路**(判据 + 护栏见上 §两条路)：现状报告 + 已聊到的已覆盖 问题/方案/验收 且核心假设被对抗过 → 走 B · 综合直接起草(跳过 Steps 2-4)；否则走 A → 继续 Steps 2-4。选定一句话告诉用户(可推翻)。

### Steps 2-4：与用户讨论（仅 A · 访谈模式；B 已在 Step 1 跳到起草）

核心是**顺序固定的三步**（Step 2 挑战前提 → Step 3 定 scope → Step 4 提方案，别跳）；下面「讨论纪律」「澄清维度」贯穿三步，不是顺序步。

**讨论纪律（贯穿 Steps 2-4）：**
- **每轮先锚定**：回应前一句话复述「当前共同基线」（上轮确认到哪、设计现在长什么样）再往下说。
- **反馈当局部 delta**：用户的质疑 / 补充 / 顾虑按「保留 / 调整 / 新增 / 待确认」处理，不是重生成全新方案的触发器。
- **方案只提一次**：「提 2-3 方案选方向」是起点的一次性动作；方向定了就在基线上改，不每轮重摆备选。前提被事实击穿才提根本备选，先说触发原因 + 业务影响。
- **基线落产物**：每确认一个决定立刻写进设计文档草稿 / Open Decisions，下轮从文档续、不从上条消息续——连贯性不靠会话记忆，context 重置也不丢。
- **先评估范围**：请求若含多个独立子系统，先指出并拆成多份设计（各自 design → plan → 落地），只就第一份逐问——别在该拆开的东西上耗问题预算。
- **一问一答迭代**：一次只问一个（话题大就拆分次问）；每问给推荐答案（接受 / 改 / 拒）；优先多选题；能查证的先查不问用户、发现矛盾直接指出；用具体场景挑战边界不问抽象偏好；**问题问不出对设计 / 领域文档 / 验收的影响就别问**。
- **完整性 vs YAGNI**：AI 把实现成本压低后，"确实要做的东西"优先做全（边界 / 错误路径 / 空状态），别用"先上捷径"省那几十行；同时 YAGNI 无情删除没人要的功能、不为不存在的需求提前抽象。两者不冲突——YAGNI 砍的是投机的未来功能，完整性补的是已决定要做的东西的覆盖。
- **分段呈现**：按段呈现设计（架构 / 组件 / 数据流 / 错误处理 / 测试策略），每段长度与复杂度成比例，**每段确认后再进下一段**，不要写完整套一次甩出。视觉判断：用 `prototype` skill 验状态模型 / UI 方向，用 `frontend-design` plugin 生成高品质原型。

**澄清维度（按输入类型选，决定问什么）：**
- **新功能 / 系统性改造 / 模糊讨论**：用户是谁 / 现在的问题 / 完成后能做什么；要新增或改变什么行为；哪些对象、状态、权限、生命周期；成功 / 失败 / 空状态 / 重复提交 / 权限不足 / 并发 / 回滚怎么处理；什么在 / 不在范围；怎么验证完成。
- **Bug / 错误 / 性能回归**：current / desired behavior、复现 / 症状；已确认 / 已排除假设、根因或可疑边界；regression check；合同 / UI / 权限 / 计费影响。缺复现 → 先用 `diagnosing-bugs` skill。出现 bad seam / shallow module → 用 `codebase-design` skill 的深模块视角重塑边界。修复会改正式行为 → 必须产出或修订设计文档。
- **Issue / backlog / 已有 PRD**：source 路径；problem / solution / user stories / 验收；依赖 / blocked-by、AFK / HITL、open decisions、out of scope。intent 不清 → 用 `triage` skill 或继续问。
- **UI / UX / 截图 / 验收反馈**：反馈来源 / 截图 / 测试 / 人工验收记录；目标状态、角色 / viewport / 文案 / 交互；视觉或 DOM 验证方式、验收标准。

#### Step 2：挑战前提
这是不是真问题——换个框架会不会大幅更简单？什么都不做会怎样？现有代码已经解决了多少（优先复用）？前提被推翻就回去改理解，别在错的问题上设计。

#### Step 3：定 scope 姿态（选一个并锁定）
扩张（往上推范围，问"2 倍力气换 10 倍价值"，每点单独让用户拍）/ 选择性扩张（守当前范围为基线 + 逐条摆出扩张机会让用户挑）/ 守范围（范围已定，做到子弹打不穿：补全失败模式 / 边界 / 可观测 / 错误路径，不偷偷加减）/ 收缩（找达成核心结果的最小版本，其余全砍）。**顾虑在锁定前一次性提清；锁定后忠实执行不漂移，每次改 scope 都用户显式 opt-in。**

#### Step 4：提方案
提 2-3 个讲 trade-off，推荐放第一个，对话式呈现。让取舍真正张开：至少一个**最小可行**（最少文件 / 最快上线）+ 一个**理想架构**（长期最优）+ 可选一个**另辟蹊径**；三个长得差不多就是没张开。把系统拆成目的清晰、接口明确、可独立测试的小单元（深模块优先，用 `codebase-design` 的词汇与原则理解现有边界），遵循既有模式。提方案时内化「架构判断本能」（无聊技术默认 / 增量非革命 / 可逆性 / 本质 vs 偶然复杂度 / blast radius / 推倒重来——见 `references/design-rigor.md`）。

### Domain Alignment（全程横向检查，非顺序步——和 Step 0 的 domain-modeling 一起贯穿全程）

触发：术语模糊 / 过载 / 冲突、新对象 / 状态 / 角色、owner 不清、用户说法与代码冲突、后续会因术语不清拆错、ADR 三条件同时成立。冲突立刻指出；模糊或过载时提精确规范术语。

| 内容 | 写回目标 | 时机 |
|---|---|---|
| 稳定术语、对象关系、角色、状态 | CONTEXT.md 或对应子 context | 确认一个写一个 |
| 术语被模糊使用 | 同文件 Flagged ambiguities | 发现时立即 |
| 跨 context 关系 / 共享词汇 | CONTEXT-MAP.md（否则根 CONTEXT.md） | 确认时立即 |
| 功能行为、接口合同、验收 | 设计文档 | 讨论充分后 |
| 架构取舍满足 ADR 三条件 | docs/adr/ | 用户确认后 |

### Mockup 留空间

设计涉及 UI/UX 且用户要做 mockup 时，暂停讨论，给用户用 `frontend-design` plugin（生成）/ `prototype` skill（状态模型）/ `impeccable` plugin（打磨与审计：视觉层级 / 可访问性 / anti-pattern / UX copy / empty state / error state / responsive）留出完整时间——节奏由用户驱动，你不催促、不并行启动后续、不替用户决定何时定稿。

## 写设计文档（→ 读 `references/design-doc-template.md` 全文）

信息足够且用户确认方向后，**打开 `references/design-doc-template.md`，按模板一次成文**。写作规则、section 清单、每节细则、UI 对照 `design-rigor.md`、Cross-Plan Anchors 占位规则全在模板里——以模板为单一源，别在这里另记一份。

## 保存前自检 + 用户确认（→ 读 `references/design-self-check.md` 全文）

保存前**打开 `references/design-self-check.md`**，按它的自检清单逐条过；然后告诉用户：

> "设计文档已写入 `<path>`，请审阅。"

然后调 `flow.sh handoff --conclusion pass`,**flow 触发 ①设计审 loop**(Codex `codex exec` 喂 quartet + design angle,见编排的审核 loop)独立审——审查角度和 findings 处置在审核 loop,本 skill 不自己派审、不复制。**Critical 必须修掉才能进 plan。**

## 拆 issue（立骨架——本 skill 收尾步）

设计通过后用 `to-issues` skill 拆成可独立认领的 issue。**本步按设计 schema 只立骨架，内容由 plan 阶段按计划 schema 丰富**：大 issue 落 `docs/issues/<YYYY-MM-DD>-<slug>/`（slug 与设计文档对齐），标 AFK / HITL，填至少一条指向设计章节的 `## Design context refs`；`## Small issues` 留 `<!-- PENDING -->`，由 `write-plan-doc` 补全。（vertical-slice 方法论在 to-issues，不复述。）

## 边界 + 收尾自检

没有设计文档前不进写 plan。已批准设计下的纯实现偏离不重走本流程——直接修代码。

**收尾自检**：写文档 / 自检这两步，是否都现读了对应 reference 全文、没凭骨架记忆默写？漏了就回去补读再过一遍。

## 下一步路由（交还 flow,不自己跳阶段）

设计文档写好、自检过、用户确认方向后,**调一条 `flow.sh handoff`,flow 据 routes 推进**(支援 skill 如 `domain-modeling`/`codebase-design`/`prototype` 是讨论过程中调的,不是交棒目标):

- 设计 OK → `flow.sh handoff --conclusion pass`(+`--produced docs/design/<slug>.md`)→ flow 触发 ①设计审 loop;审过再进 plan 阶段(`write-plan-doc` 按计划 schema 丰富 issue + 写计划)
- 缺关键输入没法定稿 → `--conclusion needs-context` → 停下问用户
- 方向本身存疑(解错问题 / 该换框架)→ `--conclusion needs-redirection` → 交用户拍方向
- ①设计审打回 design gap → flow 回 design 阶段(`needs-repair`),停在本 skill 改设计,改完 handoff 重审,不绕过
