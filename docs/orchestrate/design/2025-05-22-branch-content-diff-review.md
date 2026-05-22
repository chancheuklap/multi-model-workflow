# Branch Content Diff Review: worktree-plugin-maturity vs main

日期：2025-05-22
范围：`plugin-v2/` 全部 Modified 文件
方法：逐文件对比 main 分支与当前分支，识别实质性提示词内容的丢失或弱化

---

## 审查结论

**总体评估**：改造保留了绝大多数核心规则和纪律内容。TDD 红-绿循环、三次失败协议、交付前自检、Return Contract、Sub-agent 隔离、Pack Brief 字段纪律、Worker scope drift 检测、Open Items 即时处置、Durable Handoff Brief、Budget 不可变规则、修复截断规则——全部完整保留。

**主要风险**：disposition-table 模板化过程中，7 条规则的细节限定词被截短。其中 1 条构成关键丢失（Coordinator 越界过滤规则），6 条为有价值内容弱化。

---

## 发现明细

### 1. Disposition 表细节截短（模板化导致）

**位置**：`plugin-v2/build/templates/disposition-table.md.tmpl`（影响所有注入该模板的文件：execution/SKILL.md、plan-review-resolution.md、final-review-disposition.md、design-review-angles.md）

**修复位置**：只需修改模板文件 `plugin-v2/build/templates/disposition-table.md.tmpl`，重新 build 即可同步到所有引用点。

#### 1a. `rejected` 规则丢失防重复进入 review 的限定 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `记录反证；不派 repair，**不让同一 finding 反复进入 review**` | `记录反证；不派 repair` |

**影响**：丢失了防止 review-thrashing 的显式规则。Coordinator 可能在后续 round 中重复出现相同 finding 而不知道应该直接跳过。

#### 1b. `out of scope` 丢失 "立即" 和 "先查重" 限定 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `从当前 scope 移出；**立即**开 GitHub issue（Durable Handoff Brief 格式，**先查重**）` | `开 GitHub issue（Durable Handoff Brief）` |

**影响**：丢失了两个操作纪律——"立即"防止堆积到后续步骤，"先查重"防止开重复 issue。

#### 1c. `needs evaluation` 丢失上下文说明 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `不在当前 pack 可修范围但需独立评估；**立即**开 GitHub issue，**标明评估要点**` | `开 GitHub issue` |

**影响**：丢失了"标明评估要点"的要求，导致开出的 issue 可能缺少评估方向。

#### 1d. `user decision` 丢失决策范围限定 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `停止执行，一次只问一个**会改变设计、计划或发布策略**的问题` | `停止执行，一次只问一个决策问题` |

**影响**：丢失了决策问题的范围限定。原规则明确只有影响设计/计划/发布策略的问题才停下来问用户，弱化后任何"决策问题"都可能触发停止，降低自动化程度。

#### 1e. `duplicate / already covered` 丢失 "不新增路线" 规则 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `链到已有 finding、pack、commit、test 或文档；**不新增路线**` | `链到已有 finding` |

**影响**：丢失了"不新增路线"的约束和链接目标的完整列表（pack、commit、test、文档）。

#### 1f. `needs evidence` 丢失 Explorer 选择指导 — 🟡

| main 原文 | 当前分支 |
|-----------|---------|
| `派 explorer 补证据（**窄范围用 code-explorer，多模块用 complex-code-explorer**）；补证前不 repair` | `派 explorer 补证据` |

**影响**：丢失了 Explorer 选型指导（窄范围 vs 多模块）和"补证前不 repair"的显式约束。注意：execution/SKILL.md Step 9 紧接着 disposition 表后面保留了一段 "needs evidence 补证"的详细说明，部分弥补了这个丢失，但模板本身缺失了这些细节。

---

### 2. Coordinator "过滤越界建议" 规则丢失 — 🔴

**main 原文**（出现在 execution/SKILL.md Step 9、plan-review-resolution.md、final-review-disposition.md）：

> 收到 finding 后，Coordinator 不是传话筒——必须亲验每条 finding 的正确性（读代码、跑测试、对照 source artifacts），然后逐条给 disposition。没有 disposition 的 finding 不能进入 repair。**过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。**

**当前分支**：这段话被 disposition-table 模板替代。模板中有"亲验纪律"块捕获了前半段内容，但 **"过滤越界建议" 规则完全丢失**。

**残留**：`merge-integration-review.md` 中仍保留了原文（因为该文件除了注入模板外，还保留了原始 prose），但这只覆盖 Multi-PR Merge 路线，不覆盖 execution、plan-review、final-review 三个主要路线。

**影响**：这是一条 Coordinator 级的关键防护规则。没有它，Coordinator 可能因为 reviewer 提到了 scope 外的文件而去修改它们，违反 Scope Contract。

**建议修复**：在 `disposition-table.md.tmpl` 的亲验纪律块末尾补上：

```
过滤越界建议：out-of-scope 文件不能因为 reviewer 提到就被修改。没有 disposition 的 finding 不能进入 repair。
```

---

### 3. Final Review Repair 路径 B 删除了 Agent dispatch 模板 — 🟡

**main 原文**（`final-review-repair.md`）：路径 B 包含完整的 `Agent({...})` dispatch 模板，含 Scope、Source design、Finding(s)、Affected files、Context、Acceptance criteria、Return contract 全部字段。还允许 "SendMessage 给原 worker 或**新建同类 agent**"。

**当前分支**：替换为 `sendmessage-resume` 模板块。路径 B 只允许 SendMessage resume 原 worker，若无 agent_id 则 BLOCKED，**不再允许新建 Agent dispatch**。

**影响**：这是有意的设计收窄（与 `feedback_executor_no_doc_edit` memory 和 SendMessage-resume 策略一致），但删除了一个有价值的 dispatch 模板作为参考。如果确实需要在 Final Review 修复中首次派发 worker（无前序 agent_id 的场景），当前版本会硬停 BLOCKED，需要人工介入。

**建议**：确认这是期望行为。如果 Final Review 可能发现跨 Pack 的新问题（不属于任何已有 agent），可能需要一个"首次派发"的 escape hatch。

---

### 4. Execution State 文件 plan-level 字段缩减 — 🟢

**main 原文**（`execution-preparation.md`）：execution-state JSON 包含 plan-level 字段 `current_plan_id`、每个 plan 的 `status`、`start_commit`、`end_commit`、`review_gate`、`review_verdict`、`repair_round`、`release_gate_triggered`、`expected_pack_ids`。

**当前分支**：execution-state 只保留 pack-level 数据（status, agent_id, commit_sha, worker_verdict）。Plan-level 数据移到了 `workflow-state-<run_id>.json`。

**评估**：这是双文件模型的设计决策（architecture-draft.md Ruling 2），有明确的竞态避免理由。plan-level 数据没有丢失，只是迁移了位置。变更合理。

---

### 5. Budget File 重构为 Workflow State — 🟢

**main 原文**（`workflow-infrastructure.md`）：创建独立的 `budget-<run_id>.json`，包含 budget_total、budget_used、pack_count、dispatches 等完整字段。

**当前分支**：统一为 `workflow-state-<run_id>.json`，通过 `state.sh init` 创建，budget 作为 workflow-state 的子结构。

**评估**：Budget 不可变规则保留（"budget 一旦初始化，review_total 和 effort_total 不可变"）。核心逻辑未丢失，只是存储位置和初始化方式改变。变更合理。

---

### 6. Review Dispatch 模板化增强 — 🟢

**所有 review dispatch 位置**（7 处）的 Codex 派发步骤被替换为统一的 `review-dispatch` 模板块。

**新增内容**（main 没有）：
- DISPATCH_ENVELOPE 前缀要求
- 信任边界标记（`--- BEGIN UNTRUSTED CODE DIFF ---`）
- 按 phase 选择模型（discovery/plan-writing 用 gpt-5.5，execution/final-review 用 gpt-5.4）
- Baseline vs targeted re-review 区分（`--resume` 标志）
- Confidence rubric 强制要求
- Bias indicators 强制要求

**评估**：增强了 review 质量控制，没有丢失原有内容。变更合理。

---

### 7. Agent 文件增加 guard-doc-edit 规则和 SendMessage 禁止场景 — 🟢

**pack-executor.md** 和 **complex-pack-executor.md** 新增：
- "禁止修改设计文档和计划文档"规则 + `guard-doc-edit.sh` hook 强制执行
- 模式 2b 增加"禁止场景"说明（review finding 修复必须通过 SendMessage resume 原 worker）

**评估**：增强了纪律边界，核心内容完全保留。变更合理。

---

### 8. SKILL.md 新增注入块 — 🟢

所有 SKILL.md 新增了以下模板注入块：
- `<!-- BEGIN: preamble -->` — 包含 Hard Gate、Compaction Recovery、State Read/Write 等
- `<!-- BEGIN: voice-directive -->` — 角色声音定义 + 禁止词
- `<!-- BEGIN: signpost -->` — Phase 过渡标记
- `<!-- BEGIN: forbidden-shortcuts -->` — 禁止捷径清单
- `<!-- BEGIN: control-envelope -->` — DISPATCH_ENVELOPE 格式
- `<!-- BEGIN: state-write -->` — State 操作参考
- `<!-- BEGIN: trust-boundary -->` — 信任边界声明

**评估**：全部是新增内容，不替代原有规则。原有的 "Only stop for" / "Never stop for" / 步骤描述 / 返回格式全部保留。变更合理。

---

### 9. 所有 Agent 文件末尾新增 voice-directive — 🟢

7 个 agent 定义文件末尾都新增了 `<!-- BEGIN: voice-directive -->` 块，定义角色声音和禁止词。

**评估**：纯新增内容，不替代任何原有规则。所有原有内容（核心纪律、方法论、TDD、三次失败协议、自检、Return Contract、Memory 策略）完整保留。

---

## 需要修复的项汇总

| # | 严重程度 | 修复位置 | 修复内容 |
|---|----------|----------|----------|
| 2 | 🔴 关键 | `build/templates/disposition-table.md.tmpl` | 补回 "过滤越界建议" + "没有 disposition 的 finding 不能进入 repair" |
| 1a | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `rejected` 补回 "不让同一 finding 反复进入 review" |
| 1b | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `out of scope` 补回 "立即" + "先查重" |
| 1c | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `needs evaluation` 补回 "标明评估要点" |
| 1d | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `user decision` 补回 "会改变设计、计划或发布策略" 限定 |
| 1e | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `duplicate` 补回完整链接目标和 "不新增路线" |
| 1f | 🟡 弱化 | `build/templates/disposition-table.md.tmpl` | `needs evidence` 补回 Explorer 选型 + "补证前不 repair" |
| 3 | 🟡 确认 | `final-review-repair.md` | 确认无 agent_id 时 BLOCKED 是期望行为（不允许首次派发 worker） |

**7 项 disposition 修复只需编辑 1 个模板文件** + 重新运行 `build.sh`。

**注意**：修完模板后，需从 `merge-integration-review.md` 移除原 prose 中的"过滤越界建议"句（该文件同时保留了原文 prose 和模板注入块，修复模板后会产生重复）。
