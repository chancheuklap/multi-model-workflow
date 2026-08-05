# Grilling 保真方案审查

## 结论

上一版方案没有充分守住上游方法边界。它正确找到了设计树、整轮 frontier、Domain Modeling 组合和 Wayfinder 会话边界，但又增加了上游没有定义的状态、根问题协议和 frontier 改名。它还漏掉了异步事实调查、领域 leaf 的纯词汇边界和 MMW 的界面走查前置步骤。

新方案采用一条约束：`mmw-grilling` 的提问内核按 Matt Pocock 当前 `grilling` 方法做语义等价迁移；MMW 只在内核外保留已有的调查、领域文档落点、宿主动作、tracker、worktree、验证和下游移交合同。

## 方法来源

本次完整读取了当前上游的 Grilling、Domain Modeling、Grill with Docs、Wayfinder 技能及各自说明文件，也完整读取了 MMW 对应技能源、Wayfinder 四份 reference、`mmw-start`、`mmw-triage`、`mmw-to-spec` 和架构改进入口。

上游方法的唯一关系如下：

1. `grilling` 拥有设计树、frontier、round、问题格式、事实与决定分工和共同理解确认。
2. `domain-modeling` 拥有 glossary 挑战、术语收紧、边界场景、代码对照、术语即时写入和三条件 ADR。
3. `grill-with-docs` 只负责在同一场 Grilling 中应用 Domain Modeling。
4. `wayfinder` 在建图和决定 ticket 中调用 Grilling 与 Domain Modeling，不重写提问方法。

MMW 删除了单行的 `grill-with-docs` wrapper，并把组合关系吸收到 `mmw-grilling`。这项合并可以保留，但 `mmw-grilling` 必须同时完整承载上游 Grilling 方法和 Domain Modeling 调用，不能只保留两者的摘要。

## 撤回上一版新增设计

| 上一版内容 | 处置 | 原因 |
| --- | --- | --- |
| 为设计树增加“待处理、当前可问、已解决、重新打开”四种正式状态 | 撤回 | 上游把设计树定义为 Agent 判断，不定义状态机或计算图 |
| 要求每个调用方提交正式“根问题” | 撤回 | 上游以当前讨论主题或 Wayfinder ticket 的 `Question` 自然限定会话，没有调用协议 |
| 把两种 frontier 正式改名为“设计树 frontier”和“ticket frontier” | 撤回 | 上游同时使用两种尺度的 frontier；上下文已经能区分 |
| 在技能中增加逐题模式分支 | 撤回 | 上游只有一套 Grilling 方法；用户指令可以覆盖每轮展示数量 |
| 让设计树进入领域文档、ticket 或 spec | 撤回 | 设计树只存在于当前会话；下游只接收决定和术语，不接收树结构 |
| 为批量提问新增性能基准或遥测合同 | 撤回 | 上游没有可复现基准；本次只验证行为保真 |

## 保留的上游方法内核

`mmw-grilling` 应按下面顺序表达完整方法。顺序本身属于方法的一部分。

1. 把当前计划、决定或想法维护成设计树。每项决定分支出依赖它的决定。
2. 判断当前 frontier。frontier 只包含前置决定和事实都已经解决的问题。
3. 一轮提出整个 frontier。每个问题都编号，包含标题、正文、必要选项和单独列出的推荐答案。
4. 等用户回答整轮。用户答案会改变设计树；随后重新判断下一轮 frontier。
5. 同一轮中的问题不得互相依赖。后续答案暴露依赖误判时，下一轮重新打开受影响分支。
6. 环境可以回答的事实由 Agent 调查。需要调查时派 subagent；运行中的调查只暂停依赖该事实的分支，其余 frontier 当轮继续问。
7. 所有决定都由用户回答。Agent 不得替用户完成 HITL 决定。
8. frontier 为空、每个分支都已访问且没有静默假设时，给出共同理解总结，并等待用户确认总结准确。确认前不发布、不实施。

问题格式保留上游的语义结构，不机械复制图标。MMW 的全局输出规则禁止未获请求时使用 emoji，因此使用编号、标题、正文和独立的“推荐答案”行即可。

固定 15 轮上限删除。上游明确拒绝固定问题上限。用户随时可以要求收尾，但技能不能以固定轮数截断未遍历分支。

## 保留的 MMW 外层合同

| MMW 合同 | 放置位置 | 与上游方法的关系 |
| --- | --- | --- |
| 开问前调查当前实现、读取领域文档和相关 ADR | Grilling 内核之前 | 为设计树提供事实，不改提问方法 |
| 对调查报告验证关键出处 | Grilling 内核之前或事实返回时 | MMW 的报告可信度合同 |
| 需要看现有界面才能决定时先执行 `present-ui-review` | 第一轮之前 | MMW 的宿主动作例外；完成走查后再启动第一轮 |
| `mmw domain path` 与 `mmw domain dirs` | Domain Modeling 写入时 | 决定文件落点，不改变 glossary 和 ADR 方法 |
| `none` 形态下，嵌入调用不创建领域文档 | Domain Modeling 写入时 | MMW 的目标仓库领域文档合同 |
| 主线路径检查 `/mmw-to-spec` 所需内容是否已有答案 | 判断设计树是否遗漏分支时 | 只作为覆盖检查，不能取代 frontier 为空和无静默假设 |
| 谈定后移交 `/mmw-to-spec`；嵌入调用回到调用方 | Grilling 完成之后 | 下游编排，不改 Grilling 完成判据 |
| Wayfinder 的 tracker、worktree、claim、结果验证和集成 | Grilling 外层 | 多会话调度，不进入设计树 |

Grilling 的共同理解确认和 `/mmw-to-spec` 的人工审批关卡承担不同责任。前者只确认 Agent 对问答的总结准确。后者批准一份经过综合和审查的正式 spec 对外发布。MMW 文档需要把“唯一人工审批关卡”收紧为“唯一正式发布审批关卡”，避免用流程术语删除上游的完成确认。

## Domain Modeling 的最小调整

Domain Modeling 的主体方法不重写。只处理 wrapper 被吸收后留下的路由和出口问题。

1. 保留直接调用：用户目标是建立领域模型、确定术语、维护 ubiquitous language 或记录 ADR 时，继续执行 `/mmw-domain-modeling`。
2. 修正误路由：用户目标是追问整项计划、决定或未成形想法时，移交 `/mmw-grilling`。不能以“存在多个相互依赖决定”作为误路由判据，因为建立多个 bounded context 本身也需要相互依赖的领域判断。
3. 保留嵌入调用：`/mmw-grilling` 在同一主 agent 会话中应用 `/mmw-domain-modeling`，不启动两个并行 Agent。
4. 保留纯词汇边界：只有已解决的领域术语进入拥有它的 leaf。产品决定和实现决定留在对话，随后由 spec 或调用方承接。
5. 保留三条件 ADR：难以回退、缺少上下文会令人意外、存在真实取舍三项必须同时成立。`mmw-grilling` 不再写一份缩减摘要，只引用 `/mmw-domain-modeling` 的判据。
6. 为 `mmw-domain-modeling` 补齐仓库要求的 `## 下一步`。嵌入调用完成后回到调用方；直接建模完成后报告写入结果。

所有调用方都只引用 `/mmw-domain-modeling` 的 ADR 判据。`mmw-wayfinder/walking.md`、`mmw-wayfinder/closing.md` 和 `mmw-improve-codebase-architecture/SKILL.md` 中现有的单条件或双条件摘要全部删除。Wayfinder 的草稿文件名和最终编号规则继续保留，它们是并行分支的写入协调，不是 ADR 资格判据。

## Wayfinder 的最小调整

Wayfinder 不新增批量提问逻辑。它只调用 `/mmw-grilling`，因此会自动获得整轮 frontier 方法。

1. `drawing.md` 保持先确定 destination，再做广度优先 Grilling，随后建 map 和 ticket。建图会话不解决 ticket。
2. `walking.md` 仍以当前 `wayfinder:grilling` ticket 的 `Question` 作为讨论主题。设计树中的依赖选择用于形成这一个结论，不单独登记为 tracker ticket。
3. 当前问答发现不属于本 ticket 结论的另一项问题时，由 Wayfinder 在 Grilling 返回后登记为 ticket 或 fog of war。Grilling 不直接操作 map。
4. 删除 `map-anatomy.md` 和 `walking.md` 中“一次问一个问题”的重复规定。调用方不得复制 Grilling 的轮次协议。
5. 不新增 frontier 改名、根问题字段或设计树持久化。

MMW 当前允许一个链任务继续处理新解锁的 AFK ticket，而上游只允许 research ticket 作为单会话单 ticket 的例外。这是现有 Wayfinder 调度定制。本次修改只保证批量 Grilling 不扩大这项定制，不借本次修改重写链策略。

## 修改范围

| 文件 | 只允许的变化 |
| --- | --- |
| `mmw/skills/mmw-grilling/SKILL.md` | 恢复完整上游提问内核；保留 MMW 前置调查、界面走查、Domain Modeling 组合和下游移交；删除逐题默认、15 轮上限和 ADR 单条件摘要 |
| `mmw/skills/mmw-domain-modeling/SKILL.md` | 增加基于用户目标的误路由判断，闭合 `none` 和 `## 下一步`；主体方法不改 |
| `mmw/skills/mmw-triage/SKILL.md` | 删除调用点对逐题方法的复制，只保留为什么调用 `/mmw-grilling` 和期望得到什么答案 |
| `mmw/skills/mmw-wayfinder/map-anatomy.md` | 删除 Grilling 的逐题复制；澄清正式发布审批与共同理解确认的责任 |
| `mmw/skills/mmw-wayfinder/walking.md` | 删除 Grilling 的逐题复制和 ADR 双条件摘要；保留 ticket、HITL、链、ADR 草稿名和结果记录合同 |
| `mmw/skills/mmw-wayfinder/closing.md` | 删除 ADR 单条件或双条件补漏判据，统一引用 `/mmw-domain-modeling` |
| `mmw/skills/mmw-improve-codebase-architecture/SKILL.md` | 保留选中候选后调用 `/mmw-grilling`；被否候选是否写 ADR 统一使用 `/mmw-domain-modeling` 三条件 |
| `mmw/skills/mmw-to-spec/SKILL.md` | 把“全流程唯一人工审批关卡”收紧为“spec 发布审批关卡”，不改变用户点头后才发布的行为 |
| `mmw-skill-map.html` | 更新 Grilling、Wayfinder、ADR 和审批关卡说明；删除逐题、15 轮和缩减 ADR 判据 |
| 三套宿主物化产物 | 由技能源重新物化，只同步上述共享行为，不增加宿主分支 |

## 验证标准

方法验收直接采用上游可观察行为，不新增另一套标准：

1. 一轮问题可以按编号整体回答，每个问题有独立推荐答案。
2. 同轮任何问题都不依赖同轮另一个问题的答案。
3. 后续轮提出的内容确实由前一轮答案解锁。
4. 可查事实由 Agent 或 subagent 调查，不转问用户。
5. 后台调查只暂停依赖分支，不阻塞其余 frontier。
6. 结束时先总结共同理解并等待确认，不直接实施。
7. 已解决术语即时进入正确 leaf；领域 leaf 没有产品或实现决定。
8. ADR 同时满足三个条件；不满足时不创建。
9. Wayfinder 建图会话不解决 ticket；一张 Grilling ticket 只形成一个结论；新问题回到 map。
10. 三套宿主物化结果的共享语义一致，Codex 物化检查和仓库静态检查通过。

### 验收场景

| 场景 | 必须观察到的结果 |
| --- | --- |
| 一项含三个互不依赖决定的新需求 | 第一轮同时出现三个编号问题，每题有独立推荐答案 |
| 第四个问题依赖第一题答案 | 第四题只在下一轮出现，内容反映第一题答案 |
| 后续答案暴露同轮两题实际有依赖 | 受影响分支在下一轮重新打开，不沿用已经失效的答案 |
| 一个分支需要查文件或环境事实 | 派 subagent 调查；同轮继续询问不依赖该事实的问题 |
| 需求必须先看已有页面才能决定 | 调查和出处验证完成后先执行 `present-ui-review`；用户反馈前没有第一轮问题 |
| 用户明确要求一次只问一题 | 仍维护同一棵设计树和 frontier，但每次只展示一个当前可问问题 |
| Agent 误路由到 Domain Modeling，用户实际要谈整项方案 | Domain Modeling 移交 `/mmw-grilling`，并由 Grilling 同时应用 Domain Modeling |
| 用户直接要求建立多个 bounded context | 保持在 Domain Modeling；按现有首次建模合同逐题确认边界，不误转 Grilling |
| `mmw domain path` 返回 `none`，Domain Modeling 由 Grilling 嵌入调用 | 不创建领域文档；术语和决定留在当前对话供下游综合 |
| 已有 leaf 中形成新术语 | 术语定下时立即写入拥有它的 leaf；普通产品或实现决定不进入 leaf |
| 一个决定只满足“难以回退” | 不创建 ADR；三个条件全部成立时才创建 |
| Wayfinder 建图 | destination Grilling 和广度优先 Grilling 可以按 frontier 批量，但建图会话不解决任何 ticket |
| 一张 `wayfinder:grilling` ticket 有多个依赖选择 | 依赖选择在设计树中完成，ticket 最终只记录一个问题结论 |
| ticket 问答发现另一项不属于当前结论的问题 | 当前 Grilling 不继续解决；Wayfinder 把它登记为 ticket 或 fog of war |
| frontier 为空 | Agent 总结共同理解并等用户确认；确认前不发布或实施 |
| 主线路径进入 `/mmw-to-spec` | Grilling 确认只确认对话总结；spec 经过综合和审查后仍需独立的发布审批 |

## 实施顺序

1. 先修改 `mmw-domain-modeling` 的路由、`none`、ADR 唯一事实来源和 `## 下一步`，保证 Grilling 可以引用一个完整且闭合的领域合同。
2. 再按上游顺序重写 `mmw-grilling` 的方法内核，并把 MMW 的调查、界面走查和下游移交放在内核外层。
3. 删除 Triage、Wayfinder、架构改进和 Wayfinder 收尾中的提问方法与 ADR 判据副本。
4. 修正 `/mmw-to-spec` 与 Wayfinder 对正式发布审批的称呼，不改变任何审批动作。
5. 更新 `mmw-skill-map.html`，随后运行三套宿主技能物化。
6. 先做静态与物化检查，再逐项运行本报告的验收场景。任何场景失败都回到技能源修正，不直接手改物化产物。

## 审查处置

### 设计内容审

| finding | 处置 | 判定 |
| --- | --- | --- |
| 已确认决定可能污染只用于词汇的领域 leaf | `accepted` | 上游明确规定 leaf 只保存 glossary |
| 事实调查缺少异步 subagent 步骤 | `accepted` | 上游明确要求派 subagent，并继续询问不依赖该事实的 frontier |
| Wayfinder 会话边界只保护新解锁的 HITL ticket | `waived` | 上游出处成立，但 MMW 的 AFK 链是本次修改前已经存在的调度定制；本次只保证批量 Grilling 不扩大它 |

设计内容审报告三条，采信两条。最严重的采信项是领域 leaf 可能混入产品或实现决定。

### 项目一致性审

| finding | 处置 | 判定 |
| --- | --- | --- |
| 空 frontier 取代 MMW 的下游产出覆盖检查 | `accepted` | `/mmw-to-spec` 不采访；覆盖检查应保留，但只能补充上游完成判据 |
| 共同理解确认会形成第二道人工审批关卡 | `accepted` | 保留上游确认，同时把它与正式 spec 发布审批明确分开 |
| 设计树的依赖选择都必须登记成独立 Wayfinder ticket | `rejected` | 上游明确要求在一张决定 ticket 内运行 Grilling；依赖选择属于形成该 ticket 结论的会话过程 |
| 非阻塞事实调查绕过 MMW 的界面走查前置动作 | `accepted` | `present-ui-review` 是已写明的 MMW 宿主合同 |
| 用“多个相互依赖决定”判断 Domain Modeling 误路由 | `accepted` | 多 bounded context 建模本身也会产生相互依赖的领域判断；路由应看用户目标 |
| Domain Modeling 修改后仍缺少成功出口 | `accepted` | 仓库要求流程技能以固定 `## 下一步` 表收尾 |

项目一致性审报告六条，采信五条。最严重的采信项是完成判据只剩空 frontier 后，可能遗漏 `/mmw-to-spec` 需要综合的内容。

搁置项只有现有 Wayfinder AFK 链与上游单 ticket 会话合同的差异。本次没有创建 issue，因为它是明确超出 Grilling 修改范围的既有调度合同，不是本轮新增缺陷。
