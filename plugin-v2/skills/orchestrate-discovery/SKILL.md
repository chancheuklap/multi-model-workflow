---
name: orchestrate-discovery
description: "新功能、issue、backlog、现有 PRD、系统性 bug、wrong state、performance regression、UI / UX 反馈、截图反馈、测试反馈、系统性改造或产品讨论还没有可进入 Design Review 的设计文档时主动使用。覆盖完整流程：与用户讨论 → 生成设计文档 → Design Review（Codex 派发 + 修复）→ 过渡到 to-issues。负责读取项目上下文、持续 domain alignment、必要时联动 diagnose / prototype / improve-codebase-architecture / zoom-out / triage / grill-with-docs / frontend-design；不生成 plan、不拆 Task Pack、不派 worker。"
---

# Orchestrate Discovery

覆盖从模糊输入到设计文档通过审查的完整流程：讨论 → 文档生成 → Design Review → 过渡到 to-issues。

## 双文档产出

Discovery 产出两个同等重要的文档，由主线程 Agent 同时维护：

| 文档 | 定位 | 维护方式 |
|------|------|---------|
| **CONTEXT.md** | 项目级领域模型——术语表、对象关系、角色定义、状态机、不变量 | 通过 `grill-with-docs` 的方法论，讨论过程中每确认一个术语/关系/角色就立即写入 |
| **设计文档** | 本次功能/问题的具体设计——目标、方案、行为、验收、合同边界 | 讨论充分后按模板一次成文 |

CONTEXT.md 是项目的长期权威领域文档，设计文档是当前功能的一次性设计。两者的关系：
- 设计文档中的术语**必须**与 CONTEXT.md 一致。发现不一致时先更新 CONTEXT.md，再写入设计文档。
- 讨论中产生的新术语、新对象、新角色、新状态——先进 CONTEXT.md 确立定义，再在设计文档中引用。
- CONTEXT.md 不包含实现细节——它是纯粹的领域 glossary 和关系图。设计文档包含具体方案和实现决策。

**Hard Rule**：不能只写设计文档不维护 CONTEXT.md。讨论中每解决一个术语/领域问题，就必须同步更新两个文档。

### CONTEXT.md 格式

```markdown
# {Context Name}

{一两句话描述这个 context 是什么、为什么存在。}

## Language

**Order**:
{对术语的简洁定义}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account

## Relationships

- An **Order** produces one or more **Invoices**
- An **Invoice** belongs to exactly one **Customer**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — resolved: these are distinct concepts.
```

CONTEXT.md 规则：
- **Be opinionated**：多个词表达同一概念时，选最好的一个，其余列为"避免使用"。
- **Flag conflicts explicitly**：术语被模糊使用时，在 Flagged ambiguities 中明确解决。
- **定义简短**：一句话。定义它**是什么**，不是它做什么。
- **Show relationships**：用粗体术语名，表达关系和基数。
- **只包含项目特有的术语**。通用编程概念（timeout、error type）不属于 CONTEXT.md。
- **Example dialogue**：展示术语在对话中如何自然交互、澄清相关概念的边界。

**单 context vs 多 context**：
- 如果 `CONTEXT-MAP.md` 存在 → 读取它找到各 context
- 如果只有根 `CONTEXT.md` → 单 context
- 如果都不存在 → 第一个术语被确认时懒创建根 `CONTEXT.md`

### ADR 格式

ADR 放在 `docs/adr/`，使用顺序编号：`0001-slug.md`。目录懒创建。

```markdown
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

ADR 可以只是一段话。价值在于记录**做了什么决定**和**为什么**——不在于填模板。

**什么时候建议 ADR**（三个条件全部成立）：
1. **Hard to reverse** — 改变想法的代价不低
2. **Surprising without context** — 未来读者会疑惑"为什么这样做"
3. **The result of a real trade-off** — 有真正的替代方案，你选了一个有具体理由的

典型 ADR 场景：架构形态 / 跨 context 集成模式 / 有 lock-in 的技术选型 / 边界和范围决策 / 对显而易见路径的刻意偏离 / 代码中看不到的约束 / 被拒绝的替代方案（理由不显然时）。

---

# 第一部分：讨论（与用户一问一答迭代）

## Hard Gate

在用户确认设计之前，不得调用任何实现技能、不写任何代码、不创建任何项目骨架、不派任何 worker。**每个项目**都走这个流程，无论看起来多简单。"简单"项目正是未经检验的假设导致最多返工的地方——设计可以短（简单需求写几句话就够），但必须呈现并获得确认。

## Anti-Pattern：水平切片

不要先写完所有设计再一次性呈现。按段确认——每确认一段再进入下一段。原因：一次性呈现导致用户无法深入审视每个部分；分段确认在每一步都能及时纠偏。

## Step 1：探索项目上下文

读取项目根目录 CLAUDE.md 及其链入的规则文档。读取相关 SPEC / ADR / GUIDE / CONTEXT.md。读取相关目录的 agents.overrides.md。浏览近期 commits 和相关代码。

目的：建立对当前项目状态、模块边界、术语、既有决策的理解，避免设计与现实脱节。

## Step 2：判断 scope

评估需求规模。如果需求描述了多个独立子系统（例如"搭一个包含聊天、文件存储、计费和分析的平台"），立即标记——不要花时间细化一个需要拆分的项目。

- 项目过大 → 帮用户拆成独立子项目。每个子项目走自己的 design → plan → execution 周期。先对第一个子项目走完整 Discovery。
- 大小合适 → 继续 Step 3。

## Step 3：澄清意图（一问一答迭代）

逐个问题澄清需求。核心规则：

- **一次只问一个问题**。如果一个话题需要更多探索，拆成多个问题分次问。
- **每个问题给推荐答案**。用户可以直接接受、修改、或拒绝。
- **优先多选题**。比开放式问题更容易回答。开放式也可以，但多选优先。
- **能从代码/文档确认的先查证**，不问用户。检查代码是否与用户说的一致。发现矛盾时指出来："你的代码做的是 X，但你刚才说的是 Y——以哪个为准？"
- **用具体场景挑战边界**，不问抽象偏好。发明探测边界和极端情况的场景，迫使用户精确定义概念之间的界限。
- **问题必须能改变设计文档、domain docs 或验收标准**。不问不影响设计的问题。

澄清维度（按输入类型选择适用项）：

**新功能 / 系统性改造 / 模糊讨论**：
- 用户是谁
- 用户现在遇到什么问题
- 完成后用户能做什么
- 系统需要新增或改变什么行为
- 哪些对象、状态、权限、生命周期参与
- 成功、失败、空状态、重复提交、权限不足、并发或回滚怎么处理
- 哪些属于本次范围
- 哪些明确不属于本次范围
- 如何验证完成

**Bug / wrong state / performance regression**：
- current behavior、desired behavior、reproduction / symptom
- confirmed / rejected hypotheses、root cause or suspected boundary
- regression check、user-visible target behavior
- contract / UI / permission / billing impact、out of scope
- 缺 feedback loop → 先调用 `diagnose` 建立反馈环和事实记录。Discovery 只消费 diagnose 产出的事实；修复交给 Direct Repair 或 Execution。
- 只是已批准 design 下的实现偏离 → 返回 `READY_FOR_REPAIR`，不新建 design。
- 出现 bad seam、shallow module、caller leakage、repeated repair、无正确测试面 → 使用 `improve-codebase-architecture`，把 architecture finding 写回设计文档。
- 需要模块地图或调用链 → 使用 `zoom-out`。
- 修复会改变正式行为、对象状态、权限、合同、UI target 或验收口径 → 必须产出或修订 design document。

**Issue / backlog / existing PRD**：
- source issue / PRD / backlog path or identifier
- problem、solution、user stories、acceptance criteria
- dependencies / blocked-by、AFK / HITL、open decisions、out of scope
- issue / existing PRD 是 source material，不是独立设计生成流程。已有 problem、solution、acceptance、dependencies、AFK / HITL 可直接写入 design document。
- source intent、acceptance、blocked-by、ready state、AFK / HITL 不清 → 调用 `triage` 或继续 Discovery 提问。

**UI / UX / 截图 / 验收反馈**：
- feedback source / screenshot / test / human acceptance note
- target state、role / viewport / copy / interaction
- visual or DOM verification、acceptance criteria
- permission / billing / lifecycle implications、prototype verdict if used、out of scope
- 主观反馈必须转成可验证行为、UI state、copy、interaction、viewport、acceptance 或 verification anchor。
- 只是偏离已批准 design / mockup / acceptance → 返回 `READY_FOR_REPAIR`。
- 反馈暴露 source design 缺口 → 修订 design document，再进入 Design Review。

## Step 4：提出方案

信息足够后，提出 2-3 个不同方案，说明 trade-off。

- 推荐方案放在第一个，解释为什么更适合当前项目。
- 以对话方式呈现，不是正式文档。
- YAGNI：无情地删除未被要求的功能。

设计要点：
- **设计隔离和清晰**：把系统拆成更小的单元，每个单元有一个明确目的、通过定义好的接口通信、可以独立理解和测试。
- **深模块优先**：寻找将大量功能封装在简单接口后面的机会。使用 `improve-codebase-architecture` 理解现有模块边界和合同表面。
- **在现有代码库中工作**：先探索现有结构再提方案。遵循既有模式。现有代码有影响工作的问题时，在设计中包含针对性改进——不提无关重构。

## Step 5：分段呈现设计

把设计按段呈现。每段的长度与其复杂度成比例：简单的几句话，复杂的 200-300 字。

- 每段呈现后问用户是否正确。
- 覆盖：架构、组件、数据流、错误处理、测试策略。
- 用户说不对就回去修订，不强行推进。

涉及视觉判断时：
- 调用 `prototype` 验证状态模型或 UI 方向——原型是回答设计问题的 throwaway 代码，不是实现。
- UI 项目可调用 `frontend-design` 生成高品质前端原型。
- 视觉结论必须转成可验收的页面状态、viewport、交互和允许偏差。

## Step 6：Domain Alignment（全程横向检查）

Domain Alignment 不是独立阶段——它贯穿整个 Discovery 过程。每一轮讨论都要检查。

**触发条件**：
- 术语模糊、过载或与项目 glossary 冲突
- 同一个词在用户语境和代码 / 文档语境中含义不同
- 新对象 / 新状态 / 新角色 / 新 lifecycle
- 对象 owner / writer / reader / verifier / cleanup responsibility 不清
- UI role / permission / billing / state transition / sync ownership / runtime boundary 不清
- 用户说法和代码 / CONTEXT.md / ADR / SPEC / GUIDE 冲突
- 后续 `to-issues` 或 `plan-writing` 会因术语或边界不清而拆错
- 某个决定 hard-to-reverse + surprising without context + real trade-off 同时成立，可能需要 ADR
- 设计文档里出现"先这样""后面再看""临时""大概"等会让 future agent 无法执行的说法

**术语挑战**：
- 用户使用的术语与 CONTEXT.md 中已有定义冲突时，立刻指出。
- 用户使用模糊或过载的术语时，提出精确的规范术语。

**双文档写回规则**（每一轮讨论都执行）：

| 内容类型 | 写回目标 | 时机 |
|---------|---------|------|
| 稳定术语、对象关系、角色、状态 | CONTEXT.md | 确认一个写一个，不攒着 |
| 术语被模糊使用、与 CONTEXT.md 冲突 | CONTEXT.md 的 Flagged ambiguities | 发现时立即 |
| 功能行为、UI 状态、接口合同、失败场景、验收 | 设计文档 | 讨论充分后写入 |
| 架构取舍满足 ADR 三条件 | docs/adr/ | 用户确认后写 ADR |
| 未解决事项 | 设计文档 Open Decisions | 当轮无法决定时 |

所有写回必须自足，不能依赖当前聊天记录。

**grill-with-docs 的角色**：不是"偶尔按需调用的辅助工具"——它是 Domain Alignment 的核心执行方式。整个讨论过程中，主线程 Agent 始终用 grill-with-docs 的方法论来挑战术语、交叉验证代码、更新 CONTEXT.md。具体来说：

- **Challenge against the glossary**：用户使用的术语与 CONTEXT.md 冲突时，立刻指出并解决
- **Sharpen fuzzy language**：用户使用模糊术语时，提出精确的规范术语
- **Discuss concrete scenarios**：用具体场景探测领域关系的边界
- **Cross-reference with code**：用户说的与代码不一致时，指出矛盾
- **Update CONTEXT.md inline**：术语被确认时立即更新 CONTEXT.md，不攒着批量处理

---

# 第二部分：设计文档生成

## Step 7：写 design document

信息足够且用户确认设计方向后，按以下模板写 design document。

```markdown
# <功能 / 问题> 设计文档

## 背景和问题
从用户视角描述当前问题、触发场景和为什么需要解决。

## 目标结果
完成后用户或系统能稳定做到什么。

## 用户场景
actor / action / benefit。覆盖 happy path、失败、空状态、权限不足、重复提交、并发、回滚。
场景列表必须广泛覆盖功能的所有方面。

## 方案设计
产品行为、系统行为、数据流、UI 状态、接口形状、错误处理。

### 业务对象、角色和状态
涉及的对象、owner、writer、reader、verifier、状态、生命周期和关键关系。

### 实现决策
讨论中做出的实现决策：模块、接口修改、技术澄清、架构决策、Schema 变更、API 合同、具体交互。
不写具体 file path 或 code snippet（prototype snippet 例外）。

## 合同边界
涉及 API / Pydantic / DB / JSON / sync / task payload / UI action / billing / permission / runtime 时填写：
boundary type / owner / provider / consumer / Pydantic model / schema_version / registry / migration / catalog / repository / read model / verification。

## 发布风险和人工门禁
涉及 migration / billing / permission / runtime / cross-service / deploy order / rollback / manual gate 时填写：风险面、风险来源、是否需提前 review、manual gate owner。

## 测试和验收
哪些行为需要测试（通过公共接口测外部行为，不测实现细节）/ 哪些模块需要测试 / 代码库中类似测试的先例 / manual gate / visual verification / regression check。

## UI / UX 状态
mockup path / 页面 / viewport / states / copy / interaction / 视觉允许偏差 / 验证方式。

## 失败场景和异常处理
错误 / 权限不足 / 空状态 / 重复提交 / 并发 / 重试 / 回滚 / 兼容 / 降级。

## 不在本次范围
影响执行边界的排除项。

## Open Decisions
无法当前确认但影响后续 plan / implementation 的问题。
```

**设计文档要求**：
- 使用项目正式术语（与 CONTEXT.md 一致）
- 不写当前聊天才能理解的句子
- 不用 TODO / TBD / later / defer 掩盖缺口
- 不写具体 file path 作为长期实现指令（mockup path、existing module anchor、confirmed contract anchor 除外）
- 不写 Task Pack、worker 指令或 implementation plan

## Step 8：自检

写完 design document 后，用全新的眼光审视它。

**内容完整性**：
- [ ] 无 TODO / TBD / placeholder / vague wording
- [ ] 不和 CONTEXT.md / PROJECT / SPEC / ADR / GUIDE / 代码事实冲突
- [ ] 每个目标行为都能转成验收或测试
- [ ] 对象 / 状态 / 合同有 owner / writer / reader / verifier
- [ ] 没有混入 implementation plan / Task Pack / worker 指令
- [ ] 没有把多个独立系统塞进一个 design document
- [ ] 每个保留的设计元素都有明确理由（YAGNI）

**按输入类型检查**：
- Bug：有 current behavior / desired behavior / reproduction / symptom / regression check
- Issue：有 source / acceptance / dependencies / AFK-HITL
- Feedback：有 target state / role / copy / interaction / verification anchor
- UI/UX：有 mockup path / viewport / states / interaction / visual verification

**内部一致性**：
- [ ] 各 section 之间无矛盾
- [ ] 架构描述与功能描述一致
- [ ] 需求之间无歧义——任何可能被两种方式解读的需求，选定一种并写明

**合同与发布**：
- [ ] 涉及 API / Pydantic / DB / JSON / sync / billing / permission / runtime 时，有 Contract anchors
- [ ] 涉及 migration / billing / permission / runtime / deploy order / rollback / manual gate 时，有发布风险面和 manual gate owner

发现问题直接修正，不需要重新自检。

## Step 9：用户确认设计文档

自检通过后，请用户审阅写好的设计文档。

> "设计文档已写入 `<path>`，请审阅。如果需要修改，告诉我；确认后我们进入 Design Review。"

等用户回复。用户要求修改 → 修改后重做自检。用户确认 → 进入第三部分。

---

# 第三部分：Design Review（一轮 Codex Review + 修复）

用户确认设计文档后，Coordinator 派发 Codex 独立审查。目的是听取设计的第二意见——审设计自身是否完整、可测试、可执行，以及是否符合项目事实和约束。不做文字润色、不派 worker、不写 plan。

## Step 10：派发 2 个 baseline Codex reviewer

读取 `references/design-review-angles.md` 构建 dispatch prompt。两个 review angle 通过 `codex:codex-rescue --model gpt-5.4` 派发，可并行不可合并。

- **Baseline 1: Design Content Review** — 审设计自身是否完整、可测试、可执行
- **Baseline 2: Project Alignment Review** — 审设计是否符合项目事实和约束

**Budget check**：per-phase allowance（4 dispatches），不依赖 budget_total。每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Step 11：接收 findings + 修复（一轮）

Coordinator 接收 reviewer findings 后，**不是传话筒**——必须主动验证 finding 的正确性（读代码、跑测试、对照 source artifacts），用自己的判断力质疑和确认，然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。

### Disposition 定义

| disposition | 动作 |
| --- | --- |
| `accepted` | 转成 repair payload；写明 affected artifacts 和 repair scope |
| `rejected` | 记录反证；不 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 code-explorer 或让 reviewer 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding 或文档；不新增路线 |
| `out of scope` | 从当前 scope 移出 |
| `user decision` | 停止执行，一次只问一个会改变设计的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

### 修复归属

Design document 是 Coordinator 写的，Coordinator 拥有完整的用户上下文和设计意图——**Coordinator 直接修**。不派 worker。

### 修复后处理

修复后做 targeted re-review：只重审 accepted findings 涉及的变更部分 + 受影响 angle。不做 full review rerun。

**只做一轮 review + 修复**。Design Review 结束后直接进入过渡阶段。

### Finding 路由

- accepted document repair → Coordinator 直接修设计文档
- accepted domain / UX / ownership ambiguity → 回到第一部分（Discovery 讨论），重新与用户澄清后修订
- accepted issue gap → Design Review 通过后 route to-issues
- rejected / out of scope / duplicate → 记录，不 repair

## Pass 条件

两个 baseline review 通过 + 无 Critical finding。最多 2 个 repair rounds。

## Release Gate

只在 release strategy / migration-deploy order / rollback / manual gate 必须提前判定时追加 `codex:codex-rescue --model gpt-5.5`。普通 production-risk 由 baseline 转成 risk flags 写入设计文档。

---

# 第四部分：过渡到 to-issues

## Step 12：检查 issue hierarchy

Design Review 通过后，检查是否已有 issue hierarchy。

- 已有 vertical large issues + small issues → 直接返回，进入 plan-writing
- 缺 issue hierarchy → 调用 `to-issues`（外部 Skill）拆分设计文档为 vertical large issues → small issues

## 配合使用的外部 Skill

### 核心伴随技能（与 Discovery 同等地位，全程使用）

| Skill | 角色 | 产出 |
|-------|------|------|
| `grill-with-docs` | CONTEXT.md 的核心维护方式——术语挑战、glossary 交叉验证、domain alignment 执行 | 更新 CONTEXT.md（术语表 + 关系 + Flagged ambiguities + ADR） |

### 按需调用技能（各自独立运行）

| Skill | 调用时机 | 做什么 |
|-------|---------|--------|
| `prototype` | 需要验证状态模型、UI 方向、接口形态时 | 生成 throwaway 原型回答设计问题 |
| `frontend-design` | UI 项目需要高品质前端原型时 | 生成前端界面原型 |
| `improve-codebase-architecture` | 需要理解现有模块边界、发现 bad seam 时 | 架构分析 + deepening 建议 |
| `zoom-out` | 需要代码地图、调用链、模块关系时 | 模块地图 + 边界上下文 |
| `diagnose` | Bug/regression 需要构建反馈循环和事实记录时 | reproduce → hypothesise → instrument |
| `triage` | Issue 的 source intent、ready state、AFK/HITL 不清时 | issue 分类 + ready state 判定 |
| `to-issues` | Design Review 通过后，缺 issue hierarchy 时 | 设计文档 → vertical large issues → small issues |

### 调用规则
- 每个 skill 的结论必须写回 design document 或 CONTEXT.md，不停留在聊天记录
- upstream skill 如需发布 issue 或改代码，先交回 Orchestrate parent 确认 scope
- Discovery 只消费这些 skill 的产出，不执行它们的副作用

## 边界规则

- 没有可 review 的 design document 前，不进入 plan-writing、Execution 或 worker 派发
- 已批准 design 下的明确实现偏离 → 返回 `READY_FOR_REPAIR`，不新建 design
- 用户已有 PRD → 当 source material 消费，不重新生成
- 设计问题太大 → 先拆成多个 design document
- 已有 design 足够清楚 → 直接返回 `DISCOVERY_NOT_NEEDED`

## 返回格式

```text
### Verdict
DISCOVERY_READY | DISCOVERY_NOT_NEEDED | READY_FOR_REPAIR | NEEDS_USER_DECISION | BLOCKED

### Design path
- <path or not created>

### Design Review
- Baseline 1: pass / needs repair / blocked
- Baseline 2: pass / needs repair / blocked
- Findings dispositioned: <count>
- Repairs applied: <count>

### Discovery result
- Problem:
- Target behavior:
- Key decisions:
- Acceptance:
- Out of scope:
- Domain alignment resolved:
- Remaining ambiguity:

### Issue hierarchy
- Status: ready / needs to-issues / not applicable
- Large issues: <paths or "pending">
- Small issues: <count or "pending">

### Next route
- plan-writing / to-issues → plan-writing / Direct Repair / user decision / blocked
```
