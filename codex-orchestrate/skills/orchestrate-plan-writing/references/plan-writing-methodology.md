# Plan 写作方法论

> **流程位置**：`orchestrate-plan-writing` Steps 3-8 · plan_writer 写作方法论 · Coordinator 按此构造 dispatch brief → Steps 9-10（`plan_writer-dispatch.md`）

plan_writer agent 通过 dispatch prompt 中指定的路径读取本文件执行写作。Coordinator 按本文件内容构造 plan_writer dispatch prompt。

## 核心原则

写 plan 时假设执行者**对当前代码库零上下文、对问题领域一无所知**。文档里必须包含他们需要知道的一切：每个任务该看哪些文件、改什么代码、怎么测试、相关文档在哪。给他们一份由 bite-sized task 组成的完整计划。DRY、YAGNI、TDD、频繁提交。

执行者是有经验的开发者，但几乎不了解我们的工具链和问题领域。假设他们的测试设计能力一般。

## Step 3：读取 source design + 你的 issue

**每个 plan_writer 只负责一个大 issue。** dispatch prompt 中已指定你的 issue 文件路径。

### 3a：读取 source design

提取 goal、architecture、tech stack、合同边界。理解全局设计上下文，但只关注与你的 issue 相关的部分。

### 3b：读取你的 issue 文件

Read dispatch prompt 中指定的 issue 文件。提取 What to build、Blocked by。

检查 `## Small issues` 章节：
- 如果已有完整的小 issue 列表 → 跳过 Step 3c，直接进入 Step 3d
- 如果为空或标记 `<!-- PENDING -->` → 进入 Step 3c 拆分小 issue

### 3c：拆分小 issue（大 issue 内部的实现步骤拆解）

**你负责将大 issue 的 `What to build` 拆分为小 issue。** 这不是再切一层 vertical slice——大 issue 本身已经是一个完整的 vertical slice。小 issue 是这个 slice 内部的**实现步骤拆解**，目标是让每个步骤可独立实现、可独立验证。

#### 拆分原则

- 每个小 issue 是大 issue 端到端路径中的一个可独立验证的实现单元
- 拆分维度：按功能边界（schema → API → UI）或按行为边界（创建 → 编辑 → 删除）
- 每个小 issue 必须有明确的验收标准（完成后能用测试或手动方式验证）
- 标记依赖关系：哪些小 issue 必须在其他小 issue 之前完成
- 标记 Type：AFK（可无人值守实现）或 HITL（需要人工决策/确认）

#### 拆分步骤

1. 读完 `What to build` 后，结合 Step 3a 的设计上下文和 Step 3d 的代码探索结果，识别实现单元
2. 每个实现单元写为一个小 issue，包含 Type、What to build、Acceptance criteria、Blocked by
3. 用 Edit tool 将小 issue 写回大 issue 文件的 `## Small issues` 章节，替换 `<!-- PENDING -->` 标记

#### 写回格式

```markdown
## Small issues

### 1. <Small Issue Title>
**Type:** AFK / HITL
**What to build:** <描述>
**Acceptance criteria:**
- [ ] ...
**Blocked by:** <其他 small issue 编号或 "None">

### 2. <Small Issue Title>
...
```

#### 质量自检

- [ ] 每个小 issue 可独立验证（有明确的验收标准）
- [ ] 小 issue 的并集覆盖大 issue 的 `What to build` 全部行为
- [ ] 依赖关系正确（不存在循环依赖）
- [ ] 没有过粗的小 issue（单个小 issue 不应需要超过 8 个 implementation steps）
- [ ] 没有过细的小 issue（单文件内的单函数修改不值得独立成 issue）

写回完成后，继续进入映射规则。

#### 映射规则

| source artifact | plan artifact |
| --- | --- |
| source design | plan 的全局上下文（只读参考） |
| 你的 issue 文件 | plan 的 scope |
| issue 内的 small issue | 一个 Task Pack |
| small issue acceptance criteria | Task Pack acceptance criteria |
| small issue blocked-by | Task Pack dependencies |
| issue blocked-by（大 issue 级） | plan header 记录，Coordinator 在 execution 阶段处理跨 plan 依赖 |

映射不成立时：

| 状况 | 返回 |
| --- | --- |
| 术语 / 验收不清 | `NEEDS_DISCOVERY`："业务意图不清，需要 discovery" |
| 架构假设与代码现实不符 | `NEEDS_ARCHITECTURE`：具体说明哪个假设不成立 |

只处理你的 issue 文件中的内容。其他 issue 不属于你的 scope。

### 3d：探索代码库

用 `rg` / `find` / `Skill({ skill: "improve-codebase-architecture" })` 验证 source design 涉及的路径、模块、合同面、已有模式。

读取项目根目录 AGENTS.md 及其链入的规则文档。理解模块边界、测试路由、合同墙、命名约定——plan 中的 File/Responsibility Map、verification commands、contract anchors 必须符合项目实际。

## Step 4：确定文件结构

在定义 task 之前，先规划哪些文件将被创建或修改，以及每个文件负责什么。这是分解决策锁定的地方。

- 设计清晰边界和定义好接口的单元。每个文件一个明确职责。
- 更小、聚焦的文件优于一个做太多事的大文件。
- 一起变更的文件应该住在一起。按职责拆分，不按技术层拆分。
- 在现有代码库中，遵循既有模式。

## Step 5：写 Plan Header

```markdown
# <Issue Title> Implementation Plan

**Goal:** <这个 issue 的一句话目标>
**Source design:** docs/orchestrate/design/<slug>.md
**Source issue:** docs/orchestrate/issues/<slug>/00N-<issue-slug>.md
**Execution owner:** Orchestrate Workflow
**Blocked by:** <从 issue 文件的 Blocked by 节复制，Coordinator 在 execution 阶段处理跨 plan 依赖>
**Architecture:** <与本 issue 相关的实现方向>
**Tech stack:** <实际涉及的框架、服务、测试工具>
**Quality gate:** 进入 Plan Review 前必须通过过度设计 / 设计不足自审。

## File / Responsibility Map
**Create:** `path` — responsibility
**Modify:** `path` — responsibility
**Test:** `path` — behavior covered
**Docs / rules / registry / migration / release gate:** `path or gate` — why it changes

## 发布风险和人工门禁
| 风险面 | Task Pack | Risk flag | 提前 review | Manual gate owner |
| --- | --- | --- | --- | --- |
```

Execution owner 必须是 Orchestrate Workflow。

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
- <source docs, ADRs, project rules, docs/orchestrate/mockups/<slug>/ (如有)>

**Contract anchors:**
- Owner / Provider / Consumer / Model / schema / Registry / migration / catalog / Verification

**Mockup anchors:**
- 目录: docs/orchestrate/mockups/<slug>/ · Viewport / States / Interaction / Visual verification

**Acceptance criteria:**
- [ ] ...

**Verification commands:**
- `command` → Expected: ...

**Commit boundary:** <one atomic commit scope>
**Risk flags:** normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL
**发布风险:** <风险面 / N/A>
**AFK / HITL:** ...
**Dependencies:** ...
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

所有 pack 严格串行执行，按 Dependencies 字段排序。

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
- pack 只写"实现 mockup"但没有 mockup 目录路径 / states / viewport / interaction / visual verification
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

## 修订流程（plan_writer 收到 findings 后执行）

Plan-writer 通过 send_input 收到 accepted findings 后：

1. 读完所有 findings
2. 按优先级修订：结构性问题 → 内容缺失 → 精度问题
3. 重跑 Step 8 自检
4. 保存修订后的 plan
5. 返回修订摘要

如果 finding 不正确，说明技术原因推回。

## Git 纪律

**不要运行 git commit、git merge 或 git push。** 所有改动保持 unstaged。Coordinator 在 review 通过后统一提交。

## 任务范围

- 任务范围 = parent dispatch prompt 中给出的内容。不扩大 scope。
- 不为 source design 没要求的能力预留 pack。
- 不创建新的大 issue——大 issue 由 Coordinator 在 Discovery 阶段产出。你只负责在已有大 issue 内拆分小 issue 并映射为 Task Pack。

---
> **下一步**：方法论指导完成 → Steps 9-10（`plan_writer-dispatch.md`）派发 plan_writer。
