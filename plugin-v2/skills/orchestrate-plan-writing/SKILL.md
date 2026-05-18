---
name: orchestrate-plan-writing
description: "已有 reviewed source design 和 to-issues 产出的 vertical large issues / small issues 时主动使用。覆盖完整流程：前置条件确认 → 计划文档写作方法论 → 派发 plan-writer agent → Plan Entry Gate → Plan Review（单次 Codex 集成审查 + 修复）→ Git Checkpoint → 过渡到 orchestrate-execution。纯 Coordinator 线性流程：主线程按本技能逐步执行调度、review 接收、修复路由和进度追踪；plan-writer agent 通过 skills 字段自动加载本技能获取写作方法论。"
---

# Orchestrate Plan Writing

覆盖从设计文档到计划文档通过审查的完整流程。Coordinator 按本技能逐步执行——不由 Worker 或 Reviewer 消费。

**核心原则**：Source design + issue hierarchy → plan-writer 产出 vertical-slice plan → 单次 Codex 集成审查 → Coordinator 验证 + 修复 → Git Checkpoint → 进入 Execution。

**plan-writer agent 消费说明**：plan-writer 通过 `skills: ["orchestrate-plan-writing"]` 自动加载本技能。Agent 主要读取第二部分（写作方法论 + 自检）和第十部分中的修订流程 + Git 纪律 + 任务范围。

---

# 第一部分：前置条件确认

## Step 0：Re-entry 检测

检查是否存在已通过 Plan Review 的 plan 文档（来自上次执行 plan-writing 或跨会话恢复）。

| 条件 | 模式 | 下一步 |
| --- | --- | --- |
| 无已有 plan | **新建模式** | Step 1（正常流程） |
| 已有 plan + workflow 附带 `NEEDS_PLAN_REVISION` context（execution 打回） | **修订模式** | Step 0a |
| 已有 plan + 无修订 context | **新建模式**（忽略旧 plan，可能 scope 已变） | Step 1 |

### Step 0a：Plan 修订模式

Execution 返回 `NEEDS_PLAN_REVISION` 时，workflow 附带具体的 plan 问题描述。

1. 读取已有 plan 文档
2. 读取 workflow 附带的修订 context（哪些 pack 有问题、具体 findings）
3. 判断修订范围：

| 修订范围 | 路径 |
| --- | --- |
| 只需修改 plan header / coverage map / scope check / 发布风险表 | Coordinator 直接修 → 跳到 Step 11（Plan Entry Gate 重检） |
| 需修改 Task Pack 内容（implementation tasks / owned files / verification） | SendMessage 原 plan-writer（agentId 从 workflow context 获取）或新建 plan-writer，prompt 附带具体 findings + 现有 plan path → plan-writer 定向修订 → Step 11 |
| 修订揭示 design gap / issue mismatch | 返回 `NEEDS_DISCOVERY` / `NEEDS_ISSUES`（upstream backflow） |

4. 修订后重跑 Plan Entry Gate（Step 11）+ Task Pack Inventory Gate（Step 12）
5. 如果 pack_count 变化 → 更新 budget file（Step 12a）
6. 重跑 Plan Review（Step 13-18），scope 缩小到修改的部分（targeted re-review 优先）

## Step 1：验证输入完备性

派发前必须验证：
- source design / SPEC / PRD / bug brief 存在且已通过 Design Review（或等价 review）
- `to-issues` 产出的 vertical large issues 和 vertical small issues 已就绪

缺件时路由：

| 缺件 | 返回 | 路由 |
| --- | --- | --- |
| 无 source design | `NEEDS_DISCOVERY` | orchestrate-discovery |
| design 未 review | `NEEDS_DESIGN_REVIEW` | Design Review |
| 缺 large/small issue | `NEEDS_ISSUES` | to-issues |
| issue ready state 不清 | `NEEDS_TRIAGE` | triage |
| 业务术语或验收不清 | `NEEDS_DISCOVERY` | orchestrate-discovery |
| bug 缺复现或 hypothesis | `NEEDS_DIAGNOSIS` | diagnose |
| 需要方案比较 | `NEEDS_DECISION` | user / prototype |
| 架构摩擦反复阻塞 | `NEEDS_ARCHITECTURE` | improve-codebase-architecture |
| 模块地图不足 | `NEEDS_CONTEXT` | zoom-out / code-explorer |

## Step 2：验证 Scope Contract + Budget File

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 保存路径和 source design path。

**Budget File**：读取 `.claude/multi-model-workflow/active-run-id` 找到 budget file，记录当前 `budget_used`。Plan-writing 阶段会消耗 Plan Review dispatch（1-2 次，含修复后的 targeted re-review）。

---

# 第二部分：计划文档写作方法论

本部分描述 plan 文档的完整写作流程。Coordinator 按本部分内容构造 plan-writer dispatch prompt；plan-writer agent 通过 skills 自动加载后按本部分执行。

## 核心原则

写 plan 时假设执行者**对当前代码库零上下文、对问题领域一无所知**。文档里必须包含他们需要知道的一切：每个任务该看哪些文件、改什么代码、怎么测试、相关文档在哪。给他们一份由 bite-sized task 组成的完整计划。DRY、YAGNI、TDD、频繁提交。

执行者是有经验的开发者，但几乎不了解我们的工具链和问题领域。假设他们的测试设计能力一般。

## Step 3：读取 source design + issue hierarchy

### 3a：读取 source design

提取 goal、architecture、tech stack、行为清单、合同边界、失败场景。理解设计文档中每一个可验证 intent。

### 3b：读取 issue hierarchy

确认 large issues 和 small issues 完整。每个 small issue 必须能独立验证。

映射规则：

| source artifact | plan artifact |
| --- | --- |
| source design / SPEC / PRD | plan 的 source of truth 和 coverage checklist |
| vertical large issue | plan 一级章节 |
| parent large issue 文档内已记录的 vertical small issue | 一个 Task Pack |
| issue acceptance criteria | Task Pack acceptance criteria |
| issue blocked-by | Task Pack dependencies |
| issue out of scope | Task Pack out of scope |
| issue AFK / HITL | Task Pack AFK / HITL 和 risk flags |

映射不成立时：

| 状况 | 返回 |
| --- | --- |
| 缺 large / small issue | `NEEDS_ISSUES`："缺 issue hierarchy，需要 to-issues" |
| small issue 不可独立验证 | `NEEDS_ISSUES`："issue 粒度不足，建议用 to-issues 继续拆" |
| 术语 / 验收不清 | `NEEDS_DISCOVERY`："业务意图不清，需要 discovery" |
| scope 应拆多个 plan | `NEEDS_ISSUES`："scope 过大，应拆分 plan" |
| 架构假设与代码现实不符 | `NEEDS_ARCHITECTURE`：具体说明哪个假设不成立 |

只处理用户明确提供或 parent 确认的 issue。Design / SPEC 中提到的其它 issue 最多作为 read-only context，不进入 plan source、Task Pack inventory 或 coverage map。不要把建议拆分直接当成正式 Task Pack——必须等 to-issues 运行并写回后才能成为正式 issue。

### 3c：探索代码库

用 `rg` / `find` / `improve-codebase-architecture` 验证 source design 涉及的路径、模块、合同面、已有模式。

读取项目根目录 CLAUDE.md 及其链入的规则文档。理解模块边界、测试路由、合同墙、命名约定——plan 中的 File/Responsibility Map、verification commands、contract anchors 必须符合项目实际。

## Step 4：确定文件结构

在定义 task 之前，先规划哪些文件将被创建或修改，以及每个文件负责什么。这是分解决策锁定的地方。

- 设计清晰边界和定义好接口的单元。每个文件一个明确职责。
- 更小、聚焦的文件优于一个做太多事的大文件。
- 一起变更的文件应该住在一起。按职责拆分，不按技术层拆分。
- 在现有代码库中，遵循既有模式。

## Step 5：写 Plan Header

```markdown
# <Feature> Implementation Plan

**Goal:** <一句话用户可见或系统可验证能力>
**Source design:** <path or tracker reference>
**Source issues:** <paths or tracker references>
**Execution owner:** Orchestrate Workflow
**Plan unit:** 一级章节 = large issue；Task Pack = small issue；细 task 只在 pack 内部。
**Completion gate:** Plan Review → Execution → Pack Review → Final Review → Release Gate (if triggered)
**Architecture:** <2-3 句实现方向、主要合同边界和数据/状态流>
**Tech stack:** <实际涉及的框架、服务、测试工具、运行时>
**Quality gate:** 进入 Plan Review 前必须通过过度设计 / 设计不足自审。

## Scope Check
**Subsystems:** ...
**Should split into multiple plans:** yes / no, with reason
**This plan covers:** ...
**This plan does not cover:** ...

## Source Coverage Map
| Source intent / requirement | Large issue | Small issue / Task Pack | Acceptance evidence |
| --- | --- | --- | --- |

## File / Responsibility Map
**Create:** `path` — responsibility
**Modify:** `path` — responsibility
**Test:** `path` — behavior covered
**Docs / rules / registry / migration / release gate:** `path or gate` — why it changes

## 发布风险和人工门禁
| 风险面 | Source issue / Task Pack | Risk flag | 提前 review | Manual gate owner |
| --- | --- | --- | --- | --- |
```

Execution owner 必须是 Orchestrate Workflow。Should split = yes 时不继续硬塞，返回 `NEEDS_ISSUES` 或 `NEEDS_DISCOVERY`。

## Step 6：写 Task Pack

每个 small issue 对应一个 Task Pack：

```markdown
### Task Pack N.M: <small issue title>

**Issue:** <path or issue reference>
**Goal behavior:** <end-to-end behavior>
**Owned files / responsibilities:**
- Create: `path`
- Modify: `path`
- Test: `path`

**Read first:**
- <source docs, ADRs, project rules, mockups>

**Contract anchors:**
- Owner / Provider / Consumer / Model / schema / Registry / migration / catalog / Verification

**Mockup anchors:**
- Path / Viewport / States / Interaction / Visual verification

**Acceptance criteria:**
- [ ] ...

**Verification commands:**
- `command` → Expected: ...

**Commit boundary:** <one atomic commit scope>
**Risk flags:** normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL
**发布风险:** <风险面 / N/A>
**AFK / HITL:** ...
**Dependencies:** ...
**Parallel safety:** ...
**Out of scope:** ...
```

## Step 7：写 Implementation Tasks

每个 step 是一个动作（2-5 分钟），TDD vertical tracer bullet：

```markdown
#### Implementation tasks
- [ ] Step 1: 定义失败的 public-behavior 测试
  - 文件 / Behavior / Key assertions / Fixtures
- [ ] Step 2: 运行测试确认失败
  - Run: `command` → Expected: FAIL because ...
- [ ] Step 3: 实现最小合同
  - 文件 / Owner / provider / consumer / Types / fields / state transitions
- [ ] Step 4: 运行测试确认通过
  - Run: `command` → Expected: PASS
- [ ] Step 5: Refactor（只在 GREEN 状态下）
- [ ] Step 6: Suggested commit boundary
```

**细 Task 规则**：
- 优先从 public behavior 检查开始（Red → Green → Refactor）
- 每个 step 只做一个动作
- 写明运行命令和 expected result
- 代码片段一旦出现必须完整，不写省略号或未定义方法
- 后续 task 引用的类型/函数/字段必须在前文定义或 existing code 中验真
- existing path 必须验真（`rg` / `find` / `ls`）；新文件写 `Create`
- 文档、agents.overrides.md、registry、migration、release gate 更新与对应行为同 pack
- 不写 `similar to previous task`——重复写出来，worker 可能不按顺序读
- DRY / YAGNI：不为未来 hypothetical slice 预建抽象

**垂直切片，不水平切片**：
```
错误：RED: test1,test2,test3 → GREEN: impl1,impl2,impl3
正确：RED→GREEN: test1→impl1 → RED→GREEN: test2→impl2
```

### 串行与并行边界

**默认同 pack 或串行**：同一文件 / 同一 Pydantic model / 同一 DB migration tree / 同一 JSON registry / billing / permission / auth / runtime / deployment / rollback / release gate / 同一 UI action contract。

允许并行的 pack 必须能独立验证且不竞争同一 contract surface。

### 验证语言

verification 必须证明 pack 行为：
- API / contract：route test、Pydantic parse、client adapter test
- DB / migration：migration test、repository test、downgrade 说明
- JSON / registry：validator test、unknown-field test
- billing / permission：service test、用户可见 gate test
- runtime / browser：focused unit test + log evidence
- UI / UX：DOM assertion、screenshot、responsive viewport check、manual visual gate

### 无 Placeholder 规则

以下内容出现在 plan 中就是 plan failure，保存前必须修掉：
- `TBD` / `TODO` / `later` / `defer` / `implement later`
- `add validation` / `handle edge cases` / `appropriate error handling`
- `write tests` 但没有行为描述
- `similar to Task N`（重复写出来）
- 引用未定义、未验真的 type / function / field / fixture
- 描述该做什么但没展示怎么做的 step
- 只写最终大套测试，不写 pack-local focused command

### 不合格 Pack 信号

- worker 必须自行决定 desired behavior / 文案 / 角色 / billing meaning / permission meaning / schema shape
- pack 只写"实现 mockup"但没有 states / viewport / interaction / visual verification
- 把未验证路径 / fixture / class 写成现有事实
- 把真实依赖隐藏成"可以并行"
- 只产出 schema 或 helper，没有 public behavior verification
- 需要人工决策 / 真实账号 / 生产确认，却标成 AFK

## Step 8：自检

保存 plan 前做三项自审。

### 过度设计检查（删减）
- [ ] 为一个 small issue 新增多个长期对象但 source issue 只要求一个可验证行为
- [ ] 提前塞入未来功能（消息中心 / 历史页 / dashboard / 复杂权限 / 运营后台）
- [ ] 因多个 pack 触碰同一文件就抽 shared helper，但没有当前重复复杂度证据
- [ ] verification 变成大而全矩阵，pack-local 行为没 focused command
- [ ] Scope Check 写 yes split 但仍硬塞多个大 issue

### 设计不足检查（补齐）
- [ ] pack 只写"实现功能"，无行为 / 结果 / failure state
- [ ] 只写路径和文件，无 owner / provider / consumer / contract anchors
- [ ] UI 工作无 states / viewport / interaction / visual verification
- [ ] issue acceptance 没进 pack acceptance
- [ ] blocked-by 没进 dependencies，或真串行写成并行
- [ ] pack 改 shared contract 却无 consumer 同步和 migration gate
- [ ] RED / GREEN expected result 不清楚

### Coverage 检查
- [ ] 每条 source design intent 映射到 Task Pack
- [ ] 每个 small issue 映射到一个 Task Pack
- [ ] File / Responsibility Map 每个路径被 Task Pack 消费
- [ ] 后文引用 type / field / fixture / command / path 与前文一致（类型一致性：Task 3 叫 `clearLayers()` 但 Task 7 叫 `clearFullLayers()` 就是 bug）
- [ ] 发布风险覆盖所有 production-risk pack

发现问题直接修正。如果发现 spec 需求没有对应 task，补上。

---

# 第三部分：Plan-writer 派发协议

## Step 9：构造 Plan-writer Dispatch Brief

Dispatch prompt 必须自足——plan-writer 通过 skills 自动加载读取第二部分方法论，但 Coordinator 仍需在 prompt 中写清所有输入 artifact 路径和上下文。

```
Agent({
  subagent_type: "plan-writer",
  description: "Write implementation plan: <feature>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## Source artifacts
    - Source design: <path>（已通过 Design Review）
    - Issue hierarchy:
      - Large issues: <path(s) + titles>
      - Small issues: <listed in large issue docs, or separate paths>
    - Scope Contract: <path>
    - CLAUDE.md: <project root>/CLAUDE.md

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/YYYY-MM-DD-<feature>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    - Design Review 中 reviewer 的重点建议: <paste if any>
    - 用户偏好 / 架构决策: <paste if any>
    - 已知 gotcha / 路径变更: <paste if any>

    ## Out of scope
    - <explicitly list what NOT to include>
    - 不自创 issue——只消费 to-issues 产出的 issue hierarchy

    ## Return contract
    ### Verdict
    PLAN_CREATED / NEEDS_DISCOVERY / NEEDS_ISSUES / NEEDS_TRIAGE /
    NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE / NEEDS_CONTEXT / BLOCKED
    ### Plan path
    ### Issue mapping
    ### Quality gate
    ### Open items
  "
})
```

**记录返回的 agentId**——后续修复可能需要 SendMessage 继续该 plan-writer（保有 design + issue 上下文）。

## Step 10：处理 Plan-writer 返回

Plan-writer 返回以下状态：

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | plan 写完，自检通过 | 进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺 issue / issue 粒度不足 / scope 过大 | 调用 to-issues |
| `NEEDS_TRIAGE` | issue ready state 不清 | 调用 triage |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | 调用 diagnose |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | 调用 improve-codebase-architecture |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 code-explorer / 调用 zoom-out，补充后 SendMessage 给原 plan-writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan-writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 SendMessage 给原 plan-writer 继续。

---

# 第四部分：Plan Entry Gate + Task Pack Inventory Gate

## Step 11：Plan Entry Gate

Plan 必须包含以下字段，缺失则 needs repair（SendMessage plan-writer 修复）：
- Source design（path + 已 reviewed 确认）
- Source issues（paths）
- Execution owner: Orchestrate Workflow
- Plan unit 定义
- Completion gate
- Source Coverage Map（每条 source intent 有对应 Task Pack）
- File / Responsibility Map
- 发布风险和人工门禁表

声称 issue-backed 但缺 issues → `NEEDS_ISSUES` → to-issues。
多余 handoff owner / 非 Orchestrate Workflow 的 execution owner → needs repair。

## Step 12：Task Pack Inventory Gate

每个 pack 必须满足：

| 必须有 | 不能进 Execution 的 pack |
| --- | --- |
| 对应 confirmed small issue | 横切 pack（不是 vertical slice） |
| vertical slice 可独立验证 | 前后端分层不能单独验证 |
| owned files + 每文件职责 | UI 只写"实现 mockup"无状态/交互 |
| acceptance criteria（从 issue 映射） | 缺目标行为需 worker 猜 |
| verification commands（pack-local） | 多 worker 写同一文件 |
| contract anchors（触碰合同时） | 只写 helper 无 public behavior |
| mockup anchors（UI 时） | 需人工决策却标 AFK |
| commit boundary | — |
| risk flags | — |
| dependencies + parallel safety | — |

不通过的 pack → SendMessage 给 plan-writer 修复 → 重新检查。

## Step 12a：更新 Budget File

Task Pack Inventory Gate 通过后，pack_count 已确认。立即更新 budget file：

```json
{
  "pack_count": N,
  "budget_total": "2N + 12"
}
```

公式推导：`(Discovery baseline: 2 + Plan-writing baseline: 1 + Pack Reviews: N + Final Review: 2) × 2 + Release gate max: 2 = 2N + 12`。

**这是 budget_total 的首次有效赋值**——workflow entry gate 创建时写 0（pack_count 未知），此处确认。Workflow 在 plan-writing 返回后做确认性写入。

---

# 第五部分：Plan Review

## Step 13：Budget Check

派发前读 budget file，确认 `budget_used + 1 ≤ budget_total`。达到 80% 时触发 Direction Check（重述 current phase / 剩余工作 / 累计 findings / 是否继续）。超过预算时停止并报告用户。

## Step 14：派发 Codex Reviewer

通过 `codex:codex-rescue --model gpt-5.4` 派发 **1 个** baseline Codex reviewer，整合三个审查角度：

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Plan Review: <feature>",
  prompt: "
    --model gpt-5.4

    ## Scope
    Review the implementation plan for: <feature>

    ## Source artifacts
    - Plan: <path>
    - Source design: <path>
    - Source issues: <paths>
    - Scope Contract: <path>

    ## Review angles (single integrated review)

    ### Coverage & Task Quality
    验 plan 是否覆盖 source design/issues，Task Pack 是否可执行：
    - 每条 source intent 映射到 Task Pack
    - issue acceptance 进入 pack acceptance
    - large→small→pack 映射完整
    - read-only context 未误纳入 editable scope
    - mockup 转化为 states/viewport/interaction/visual verification
    - 无含混行为（worker 需猜 desired behavior）
    - 无 scope creep / 过度设计 / 设计不足
    - 细 task 有短反馈循环（Red→Green→Refactor）
    - 依赖真实、分组合理
    - 高风险 pack 有对应验证

    ### Compliance & Verification
    验路径、命令、合同、项目规则是否真实：
    - 文件路径用 grep/find 逐条验真
    - mockup / fixtures / 命令存在
    - 新文件标 Create
    - agents.overrides.md 同步
    - migration tree / 注册位置 / Pydantic contract / JSON registry / DB 闭合
    - helper placement 符合项目规则

    ### Cross-Verification
    独立第三视角验证 plan 正确性：
    - function names / class names / file paths 实际存在
    - task descriptions 足够清晰可执行
    - tasks 之间无逻辑矛盾、无循环依赖
    - 修改同一文件的 tasks 分布是否有 merge conflict 风险
    - 隐式顺序依赖是否在 plan 标注
    - 项目工程规则违反

    ## Calibration
    只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。
    措辞、风格偏好、nice-to-have 建议——不是。
    除非有严重缺口（spec 需求缺失、步骤矛盾、placeholder 内容、task 模糊到无法执行），否则 approve。

    Critical：intent 无覆盖 / source intent 不清却直接实现 / pack 不可执行 /
    依赖错误 / 缺 Task Pack inventory / mockup 未转化 / 合同缺 anchors /
    引用不存在的路径 / 违反项目规则 / 允许 bare dict /
    高风险缺迁移回滚 / task 间逻辑矛盾 / 循环依赖

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    Plan Review 结果：
    Coverage & Task Quality:
    Compliance & Verification:
    Cross-Verification:
    Critical:
    Important:
    低置信度观察:
    Disposition required:
    ### Verification
    ### Open Items
  "
})
```

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction。

---

# 第六部分：Coordinator 验证 + Disposition

## Step 15：接收 Review Findings

**Coordinator 不是传话筒**——必须主动验证 finding 的正确性：

1. **读 plan + 代码**：检查 reviewer 说的是否与 plan 内容和代码事实一致
2. **对照 source artifacts**：reviewer 说 coverage 缺失 → 对照 source design 和 issue hierarchy 确认
3. **跑 grep/find**：reviewer 说路径不存在 → 自己验真
4. **用自己的判断力质疑和确认**：不因为 reviewer 说了就当真

逐条 disposition：

| Disposition | 动作 |
| --- | --- |
| `accepted — plan repair` | Coordinator 直接修 plan 框架性内容（header、coverage map、scope check、发布风险表），或 SendMessage plan-writer 修 Task Pack 内容 |
| `accepted — design gap` | 回到 orchestrate-discovery → Design Review → 写回后 re-review plan |
| `accepted — issue-plan mismatch` | 调用 to-issues → 写回后 re-review plan |
| `accepted — architecture friction` | 调用 improve-codebase-architecture → 写回后 re-review |
| `rejected` | 记录反证；不 repair，不让同一 finding 反复进入 review |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 补证据；补证前不 repair |
| `duplicate / already covered` | 链到已有 finding / issue / commit；不新增路线 |
| `out of scope` | 从当前 scope 移出；只有用户授权时才写 durable issue |
| `user decision` | 停止执行，一次只问一个会改变设计/计划/发布策略的问题 |

冲突按 evidence quality 判断，不按 reviewer 数量投票。

**Plan Review 通过**（全部 finding 为 rejected / out of scope / duplicate，或无 finding）→ 跳到 Step 19（Git Checkpoint）。

**Plan Review needs repair**（有 accepted finding）→ 进入 Step 16。

---

# 第七部分：修复分流

## Step 16：修复路由

所有 repair prompt 只携带 accepted findings，不夹带 rejected / out-of-scope / low-confidence observations。

### 路径 A：Coordinator 直接修复

**条件**：Plan header、coverage map、scope check、发布风险表、dependency chain 等框架性内容。

1. Coordinator 读 finding、对照 source artifacts
2. 直接修改 plan 文档
3. 验证修改与 source design / issues 一致
4. 进入 Step 17（Targeted Re-Review）

### 路径 B：SendMessage 给 plan-writer agent

**条件**：Task Pack 内容、implementation tasks、verification commands、owned files、contract anchors 等写作细节——plan-writer 保有 design + issue 上下文。

1. 检查 SendMessage 是否可用（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）
2. 可用 → SendMessage 给 saved agentId，附 accepted findings + 修复方向
3. 不可用 → 新建 `plan-writer` agent，prompt 含 accepted findings + plan path + source design path + issue paths
4. Plan-writer 修复后返回 → 重跑 Plan Entry Gate + Task Pack Inventory Gate → 进入 Step 17

### 路径 C：Upstream Backflow

**条件**：finding 揭示的不是 plan 问题，而是 source artifact 问题。

| Finding 类型 | Upstream | 写回目标 | 回到 |
| --- | --- | --- | --- |
| design gap / 需求不清 | orchestrate-discovery | design document | Plan Review re-review |
| issue-plan mismatch | to-issues | issue hierarchy | Plan-writing re-run |
| architecture friction | improve-codebase-architecture | design doc / plan anchors | Plan Review re-review |
| domain 术语冲突 | grill-with-docs | CONTEXT.md + design document | Plan Review re-review |

upstream skill 结论写回后，根据影响范围决定是 re-review plan 还是 re-run plan-writing。

### 修复归属快速判定

| 信号 | 路径 |
| --- | --- |
| "coverage map 缺 intent X" / "发布风险表遗漏 pack Y" | A（Coordinator 直接修） |
| "Task Pack 3.1 的 verification command 不存在" / "owned files 遗漏 migration" | B（SendMessage plan-writer） |
| "source design 没定义这个行为" / "issue acceptance 与 design intent 矛盾" | C（Upstream backflow） |
| accepted finding 涉及 migration / billing / permission / shared contract | B（用 plan-writer 修，因为涉及 pack 写作细节） |

---

# 第八部分：Targeted Re-Review + 修复截断

## Step 17：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 14，但 scope 缩小到：
- changed sections（修复涉及的 plan 章节）
- accepted findings（原 finding 是否解决）
- 受影响 angle（coverage / compliance / cross-verification 中与修复相关的）

## Step 18：修复预算 + 截断

**修复预算**：Plan Review 最多 **2 个 repair round**（含 Coordinator 直接修和 plan-writer 修复）。这是 per-phase 上限；全局 review budget 优先——Direction Check 在 80% 时触发，可能在 plan 用满 2 轮之前就要求停下来评估方向。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2（截断） | 仍 needs repair → **截断**。判定原因 |

**截断路由**：

| 判定 | 下一步 |
| --- | --- |
| Plan 层面问题（结构、coverage、task quality） | BLOCKED，报告用户附 2 轮 findings 汇总 |
| Source artifact 问题（design gap / issue mismatch） | 强制 upstream backflow（路径 C） |
| 项目规则 / 代码现实 mismatch | 调用 improve-codebase-architecture 或 zoom-out 补充上下文后 re-run |

2 轮修复后仍 needs repair 通常意味着 plan 的基础输入（design / issues）有问题，继续在 plan 层修补无意义。

---

# 第九部分：Git Checkpoint

## Step 19：提交 Plan 文档

Plan Review 通过后（+ 所有 Gate 通过）：

1. `git add <plan doc path>`——stage plan 文档
2. `git commit -m "Plan: <feature> — reviewed implementation plan"`
3. Commit boundary = 回退边界：如果后续 execution 阶段需要回到 plan，可以 revert 到这个 commit

**规则**：
- Plan-writer 不 commit；Coordinator 在 Plan Review 通过后统一 commit
- 不 stage 不属于当前 scope 的 dirty files
- Design doc repair（如有）和 plan doc 分别提交——不混在一个 commit 里

---

# 第十部分：过渡到 Execution + 返回格式

## Step 20：Plan Review 通过

Plan Review 通过 + Git Checkpoint 完成后，返回 verdict。orchestrate-workflow 将路由到 orchestrate-execution。

## 上游 Route Payload

需要交回 `to-issues` 时：

```text
Upstream route: to-issues
Source design:
Parent large issue:
Issue recording target:
Why current issue boundary is insufficient:
Suggested vertical slices:
这些 slices 只是建议；必须等 to-issues 运行并写回后，才能成为正式 issue / Task Pack。
```

## 修订流程（plan-writer 收到 findings 后执行）

Plan-writer 通过 SendMessage 收到 accepted findings 后：

1. 读完所有 findings
2. 按优先级修订：结构性问题 → 内容缺失 → 精度问题
3. 重跑 Step 8 自检
4. 保存修订后的 plan
5. 返回修订摘要

如果 finding 不正确，说明技术原因推回。

## Git 纪律（plan-writer 遵守）

**不要运行 git commit、git merge 或 git push。** 所有改动保持 unstaged。Coordinator 在 review 通过后统一提交。

## 任务范围（plan-writer 遵守）

- 任务范围 = parent dispatch prompt 中给出的内容。不扩大 scope。
- 不为 source design 没要求的能力预留 pack。
- 不自创 issue——issue hierarchy 由 to-issues 产出，只消费它。

## 返回格式

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES | NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE | NEEDS_CONTEXT | BLOCKED

### Plan path
- <保存路径>

### Plan Review
- Review dispatched: <count>
- Findings dispositioned: <count>
- Repairs applied: <count>
- Repair rounds used: <N> / 2

### Issue mapping
- Large issues: <count and titles>
- Task Packs: <count>
- Dependencies: <dependency chain summary>

### Quality gate
- Overdesign checked: yes + findings or clean
- Underdesign checked: yes + findings or clean
- Coverage checked: yes + findings or clean
- Type consistency checked: yes + findings or clean
- Largest remaining risk:

### Git state
- Commits: <plan commit hash>
- Branch: <current branch>
- Clean: yes / no

### Open items
- Blockers / HITL:
- Needs context: <具体缺什么>

### Next route
- orchestrate-execution / upstream route / user decision / blocked
```
