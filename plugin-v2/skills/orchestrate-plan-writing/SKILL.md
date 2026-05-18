---
name: orchestrate-plan-writing
description: "已有 reviewed source design 和 to-issues 产出的 vertical large issues / small issues 时主动使用。覆盖完整流程：前置条件确认 → 派发 plan-writer agent → 计划文档生成 → Plan Review（Codex 派发 + 修复）→ 过渡到 orchestrate-execution。多消费方技能：Coordinator 读取本技能执行调度和 review；plan-writer agent 通过 skills 字段自动加载本技能获取写作方法论。"
---

# Orchestrate Plan Writing

覆盖从设计文档到计划文档通过审查的完整流程：前置确认 → 派发 plan-writer → 计划生成 → Plan Review → 过渡到 Execution。

**多消费方**：
- **Coordinator（主线程）**：读取第一部分（前置确认）、第三部分（派发 plan-writer）、第四部分（Plan Review）、第五部分（过渡）
- **plan-writer agent**：通过 `skills: ["orchestrate-plan-writing"]` 自动加载，读取第二部分（计划文档写作方法论）

---

# 第一部分：前置条件确认（Coordinator）

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

---

# 第二部分：计划文档写作方法论（plan-writer agent 消费）

## 核心原则

写 plan 时假设执行者**对当前代码库零上下文、对问题领域一无所知**。文档里必须包含他们需要知道的一切：每个任务该看哪些文件、改什么代码、怎么测试、相关文档在哪。给他们一份由 bite-sized task 组成的完整计划。DRY、YAGNI、TDD、频繁提交。

执行者是有经验的开发者，但几乎不了解我们的工具链和问题领域。假设他们的测试设计能力一般。

## Step 2a：读取 source design

提取 goal、architecture、tech stack、行为清单、合同边界、失败场景。理解设计文档中每一个可验证 intent。

## Step 2b：读取 issue hierarchy

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

## Step 2c：探索代码库

用 `rg` / `find` / `improve-codebase-architecture` 验证 source design 涉及的路径、模块、合同面、已有模式。

读取项目根目录 CLAUDE.md 及其链入的规则文档。理解模块边界、测试路由、合同墙、命名约定——plan 中的 File/Responsibility Map、verification commands、contract anchors 必须符合项目实际。

## Step 2d：确定文件结构

在定义 task 之前，先规划哪些文件将被创建或修改，以及每个文件负责什么。这是分解决策锁定的地方。

- 设计清晰边界和定义好接口的单元。每个文件一个明确职责。
- 更小、聚焦的文件优于一个做太多事的大文件。
- 一起变更的文件应该住在一起。按职责拆分，不按技术层拆分。
- 在现有代码库中，遵循既有模式。

## Step 2e：写 Plan Header

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

## Step 2f：写 Task Pack

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

## Step 2g：写 Implementation Tasks

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

## 无 Placeholder 规则

以下内容出现在 plan 中就是 plan failure，保存前必须修掉：
- `TBD` / `TODO` / `later` / `defer` / `implement later`
- `add validation` / `handle edge cases` / `appropriate error handling`
- `write tests` 但没有行为描述
- `similar to Task N`（重复写出来）
- 引用未定义、未验真的 type / function / field / fixture
- 描述该做什么但没展示怎么做的 step
- 只写最终大套测试，不写 pack-local focused command

## 串行与并行边界

**默认同 pack 或串行**：同一文件 / 同一 Pydantic model / 同一 DB migration tree / 同一 JSON registry / billing / permission / auth / runtime / deployment / rollback / release gate / 同一 UI action contract。

允许并行的 pack 必须能独立验证且不竞争同一 contract surface。

## 验证语言

verification 必须证明 pack 行为：
- API / contract：route test、Pydantic parse、client adapter test
- DB / migration：migration test、repository test、downgrade 说明
- JSON / registry：validator test、unknown-field test
- billing / permission：service test、用户可见 gate test
- runtime / browser：focused unit test + log evidence
- UI / UX：DOM assertion、screenshot、responsive viewport check、manual visual gate

## 不合格 Pack 信号

- worker 必须自行决定 desired behavior / 文案 / 角色 / billing meaning / permission meaning / schema shape
- pack 只写"实现 mockup"但没有 states / viewport / interaction / visual verification
- 把未验证路径 / fixture / class 写成现有事实
- 把真实依赖隐藏成"可以并行"
- 只产出 schema 或 helper，没有 public behavior verification
- 需要人工决策 / 真实账号 / 生产确认，却标成 AFK

## Step 2h：自检

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

## 修订流程（收到 Plan Review findings 后）

1. 读完所有 findings
2. 按优先级修订：结构性问题 → 内容缺失 → 精度问题
3. 重跑自检
4. 保存修订后的 plan
5. 返回修订摘要

如果 finding 不正确，说明技术原因推回。

## Git 纪律

**不要运行 git commit、git merge 或 git push。** 所有改动保持 unstaged。Coordinator 在 review 通过后统一提交。

## 任务范围

- 任务范围 = parent dispatch prompt 中给出的内容。不扩大 scope。
- 不为 source design 没要求的能力预留 pack。
- 不自创 issue——issue hierarchy 由 to-issues 产出，只消费它。

---

# 第三部分：派发 plan-writer agent（Coordinator）

## Step 3：Coordinator 派发 plan-writer

按以下方式调度：

```
Agent({
  subagent_type: "plan-writer",
  description: "Write implementation plan: <feature>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## 输入
    - Source design: <path>（已通过 Design Review）
    - Issue hierarchy:
      - Large issues: <path(s)>
      - Small issues: <listed in large issue docs, or separate paths>
    - Plan 保存路径: docs/orchestrate/plans/YYYY-MM-DD-<feature>.md

    ## 补充上下文（如有）
    <coordinator 在 Design Review 中积累的重要决策、reviewer 的重点建议、用户偏好>

    ## Return contract
    pass / blocked / needs context
  "
})
```

## Step 4：处理 plan-writer 返回

plan-writer verdict 映射：

| Verdict | 下一步 |
| --- | --- |
| `PLAN_CREATED` | 进入第四部分（Plan Review） |
| `NEEDS_DISCOVERY` | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 调用 to-issues |
| `NEEDS_TRIAGE` | 调用 triage |
| `NEEDS_DIAGNOSIS` | 调用 diagnose |
| `NEEDS_DECISION` | 询问用户 / 调用 prototype |
| `NEEDS_ARCHITECTURE` | 调用 improve-codebase-architecture |
| `NEEDS_CONTEXT` | 派 code-explorer / 调用 zoom-out |
| `BLOCKED` | 报告用户 |

---

# 第四部分：Plan Review（一轮 Codex Review + 修复）

## Step 5：Plan Entry Gate（派 review 前检查）

Plan 必须包含：Source design / Source issues / Execution owner: Orchestrate Workflow / Plan unit / Completion gate / 发布风险和人工门禁 / large→small→pack mapping。

缺 Execution owner 或有额外 handoff → needs repair。声称 issue-backed 但缺 issues → needs context → to-issues。

## Task Pack Inventory Gate

每个 pack 必须：对应 confirmed small issue / vertical slice 可独立验证 / 有 owned files / 有 verification / 有 Contract anchors（触碰合同时）/ 有 Mockup anchors（UI 时）/ 有 Commit boundary。

不进入 Execution 的 pack：横切 pack / 前后端分层不能单独验证 / UI 只写"实现 mockup"无状态 / 缺目标行为需 worker 猜 / 多 worker 写同一文件 / 只写 helper 无 public behavior。

## Step 6：派发 Codex reviewer

通过 `codex:codex-rescue --model gpt-5.4` 派发。每次 review 是全新 Codex task，可并行不可合并。派发前检查 review-budget.md 全局预算。

Prompt 中要求 reviewer 使用 Return Contract（同 Design Review 格式）。

### Baseline 1: Coverage And Task Quality

审 plan 是否覆盖 source design/issues，Task Pack 是否可执行。

检查：intent 覆盖 / issue acceptance 进入 pack / large→small→pack 映射 / read-only context 未误纳入 / mockup 转化 / 含混行为 / scope creep / 过度设计 / 设计不足 / 细 task 短反馈循环 / 依赖真实性 / 分组合理 / 高风险有验证。

Critical：intent 无覆盖 / source intent 不清却直接实现 / pack 不可执行 / 依赖错误 / 缺 Task Pack inventory / mockup 未转化 / 合同缺 anchors。

### Baseline 2: Compliance And Verification

审路径、命令、合同、项目规则是否真实。

逐条验真：文件路径 / mockup / fixtures / 命令存在 / 新文件标 Create / agents.overrides.md 同步 / migration tree / 注册位置 / Pydantic contract / JSON registry / DB 闭合 / helper placement。

Critical：引用不存在的路径 / 违反项目规则 / 允许 bare dict 进入实现 / 高风险缺迁移回滚。

### Baseline 3: Cross-Verification

独立第三视角验证 plan 的正确性和可执行性。用 grep/find 逐条验真 plan 中引用的路径、函数名、类名。

检查：file paths / function names / class names 实际存在 / task descriptions 足够清晰可执行 / tasks 之间无逻辑矛盾 / 无遗漏 task / 无风险假设 / 无循环依赖 / 修改同一文件的 tasks 分布在不同 section（merge conflict 风险）/ 隐式顺序依赖未在 plan 标注 / 项目工程规则违反。

Critical：引用不存在的路径或符号 / task 间逻辑矛盾 / 循环依赖 / 关键遗漏 task。

### Calibration

只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。措辞、风格偏好、"nice to have"建议——不是。除非有严重缺口（spec 需求缺失、步骤矛盾、placeholder 内容、task 模糊到无法执行），否则 approve。

### Result Payload

```text
Review: 计划文档审查 - <Coverage And Task Quality / Compliance And Verification / Cross-Verification>
Phase summary: 可执行 / 需修正
设计与 issue 覆盖:
Grep / rg 验真:
Task Pack inventory:
Critical:
Important:
低置信度观察:
Disposition required:
```

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction。

## Step 7：接收 findings + 修复（一轮）

Coordinator 接收 reviewer findings 后，逐条 disposition（规则同 Design Review）。

### 修复归属

Plan 的修复有两种路径：
- **Coordinator 直接修**：Plan 结构、coverage map、scope check、发布风险表等框架性内容
- **SendMessage 给 plan-writer agent**：Task Pack 内容、implementation tasks、verification commands 等写作细节（plan-writer 保有 design + issue 上下文，SendMessage 保持上下文连续；未启用 Agent Teams 时新建同类 agent）

### Finding 路由

- accepted plan repair → Coordinator 或 plan-writer 修
- accepted design gap → 回到 orchestrate-discovery → Design Review → plan
- accepted issue-plan mismatch → to-issues → plan-writing
- accepted architecture friction → improve-codebase-architecture → 回写后 re-review
- rejected / out of scope / duplicate → 记录，不 repair

修复后做 targeted re-review：只重审 changed sections + affected packs + 受影响 angle。**只做一轮 review + 修复**。

## Pass 条件

所有 baseline review 通过 + 无 invalid pack / source mismatch / 虚构路径。最多 2 个 repair rounds。

## Release Gate

只在 release order / rollback / manual gate 必须提前判定时追加 `codex:codex-rescue --model gpt-5.5`。

---

# 第五部分：过渡到 Execution

## Step 8：Plan Review 通过

Plan Review 通过后，返回 verdict，orchestrate-workflow 将路由到 orchestrate-execution。

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

## 返回格式

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES | NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE | NEEDS_CONTEXT | BLOCKED

### Plan path
- <保存路径>

### Plan Review
- Baseline 1: pass / needs repair
- Baseline 2: pass / needs repair
- Baseline 3: pass / needs repair
- Findings dispositioned: <count>
- Repairs applied: <count>

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

### Open items
- Blockers / HITL:
- Needs context: <具体缺什么>

### Next route
- orchestrate-execution / upstream route / user decision / blocked
```
