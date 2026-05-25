# Final Review 增强型审查

> **流程位置**：`orchestrate-final-review` Steps 4-5 · 派发后 → Steps 6-8（`final-review-disposition.md`）

## 与 Plan Implementation Review 的分工

每个 Plan 已经独立通过了 spec compliance + code quality + cross-pack coherence review。Final Review 增加三层 Plan Implementation Review 结构性看不到的覆盖：

1. **Regression sweep**（全新层）：读完整 diff（starting commit → HEAD），跑完整测试套件。检查任何 pack 的改动是否破坏另一 pack 的行为或既有功能。这是"全新眼光看全局"的层。
2. **Design intent coverage**（增强层）：逐条走 design doc 和 mockup 中每个可验证 intent。已被 Plan Implementation Review 验证的 intent 只做 1 行确认（merge 后证据仍有效）；落在 Plan 之间缝隙的 gap intent 做完整验证。
3. **Cross-Plan Integration**（改名+降级）：只检查**跨 Plan** 的集成——Plan 内跨 Pack 已由 Plan Implementation Review 的 Cross-Pack Coherence 覆盖。如果所有 Plan 之间没有共享 contract / migration / state surface，Cross-Plan Integration 降级为确认独立性的 1 行声明。Regression sweep 和 Design intent coverage 仍必须执行。

**Final Review 不重复的事**：
- 不重新审查 Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为
- 不重新检查 Plan 内跨 Pack 的 coherence（已由 Plan Implementation Review 覆盖）
- 不重新检查 helper placement、命名或单 pack owned files 内的代码质量

---

## Step 4：派发 2 个 Baseline Codex Reviewer

两个 baseline 分别提交 Codex review 任务，可并行提交，结果独立返回。

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Model authority: use the registered `codex_reviewer` role model and reasoning settings from `agents/codex_reviewer.toml`; do not pass per-dispatch model overrides unless the Codex host explicitly supports changing that role.
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent --gate "<gate>"`.
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     Record the returned reviewer `agent_id`:
     `bash "${MMW_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<reviewer agent_id>"`.
   - **Targeted re-review** (gate name contains `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport send_input --gate "<gate>"`.
     Resume the baseline reviewer before sending the targeted prompt; baseline reviewers are closed after each completed wait to release subagent capacity.
     ```
     resume_agent({
       id: "<baseline reviewer agent_id>"
     })
     ```
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.
6. Complete: run `bash "${MMW_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<reviewer agent_id>" --result-file ".codex/multi-model-workflow/review-results/<gate>.md"` to mark the result durable and increment review budget exactly once.
7. Release capacity: after the result file is saved and complete-review bookkeeping succeeds, call `close_agent({ target: "<reviewer agent_id>" })`. Do this for baseline reviews and targeted re-reviews. If later targeted re-review is needed, repeat `resume_agent` -> `send_input` -> `wait_agent` -> save/complete -> `close_agent`.

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Pre-emit Verification Gate**：

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" → 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" → 引用 dict 的初始化代码
   - "race condition between A and B" → 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

**Rationalization Prevention**：
- "This looks fine" 不是 finding。要么引用证据证明确实没问题，要么标记为未验证。
- "likely handled elsewhere" → 读并引用处理代码，或标记 unknown。
- "probably tested" → 给出测试文件和方法名，或标记 unknown。

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表。证据表证明 reviewer 实际检查过什么；它不是设计意图摘要，也不能替代阅读 source artifacts。

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的 design、mockup、plan、issue、Scope Contract 或 review baseline 路径。没有对应来源时写 `不适用`，不能留空。 |
| 已检查代码或产物路径 | 实际检查的源码、生成产物、state schema、hooks、templates、文档或 runtime contract 路径。 |
| 已运行命令或验证 | 实际执行的命令、测试、build check、schema check、browser smoke 或 manual gate；未运行时写明原因。 |
| Finding 证据 | 每个 finding 的路径、行号、diff、命令输出或可观察行为；无证据的 finding 必须移入低置信度观察。 |
| 假设 | 影响 verdict 的前提，例如环境、账号、fixture、平台或 reviewer 未能直接验证的 upstream 状态。 |
| 未验证项 | 相关但未验证的内容和原因；没有未验证项时写 `无`。 |

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent; once the result is saved and bookkeeping is complete, close it. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

### Baseline 1：Regression Sweep + Intent Coverage + Cross-Plan Integration

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/final-review-baseline-1.md`：

```markdown
## Scope
Final Review for a completed implementation. All Plans have individually
passed Plan Implementation Review. Your job is to verify the COMBINED result.

## Read first
<project docs: AGENTS.md, CONTEXT.md, ADRs, relevant SPEC>

## Feature slug（从 Scope Contract 读取）
<YYYY-MM-DD-feature>

## Source design
docs/orchestrate/design/<slug>.md（已通过 Design Review）

## Plans（已通过 Plan Review）
docs/orchestrate/plans/<slug>/（目录，逐个列出所有 plan 文件路径）

## Cross-plan contract map（已通过 Plan Review）
docs/orchestrate/plans/<slug>/cross-plan-contract-map.md

## Issue hierarchy
docs/orchestrate/issues/<slug>/

## Starting commit
<commit hash>

## Full diff
git diff <starting_commit>..HEAD

## Changed files
<file list with pack ownership>

## Plan completion summary
| Plan | Plan Impl Review verdict | Repair rounds | Packs | Release gate |
<paste per-plan summary>

## Pack completion summary
| Pack | Plan | Worker verdict | Verified behaviors | Open Items |
<paste per-pack summary>

## Contract baseline
<contract anchors from plan — all boundary types touched>

## Mockup baseline（与 design doc 同等权威）
docs/orchestrate/mockups/<slug>/（如有 UI 工作）
**Reviewer 必须 Read mockup 目录中的文件**，对照实现代码和设计文档中 `## UI / UX 状态` 的视觉规格表，验证实现与 mockup 的视觉一致性。不能只看文字描述——mockup 文件是视觉约束的权威源头。

## 发布风险和人工门禁
<paste from plan>

## Validation commands
<paste from plan — all verification commands>

## Review angles

重要：每个 Plan 已独立通过 Plan Implementation Review（含 spec compliance + code quality + cross-pack coherence）。
不要重新审查 Plan 内部已验证的行为。聚焦以下三个层面：

### 1. Regression Sweep
从 starting commit 读完整 diff。跑完整测试套件。识别：
- 跨 pack 回归：pack A 的改动是否破坏 pack B 的行为或既有功能
- 既有功能回归：diff 是否破坏了 starting commit 时已有的功能
- 测试套件回归：全部测试是否通过

### 2. Intent Coverage
从 source design 和 mockup（Read mockup 文件，不只看文字描述）提取每条可验证 intent。对照 plan/pack completion summary 标出：
- covered by plan impl review — 已被 Plan Implementation Review 验证，确认 merge 后证据仍有效（1 行确认）
- gap intent — 落在 Plan 之间缝隙，做完整验证
- implementation gap — 设计合理，代码没做到
- design gap — 设计承诺不可实现或遗漏约束
- context gap — 需要术语 / owner / UI target 确认
- unverifiable — 环境 / 账号 / 生产 gate 缺失

### 3. Cross-Plan Integration
只检查**跨 Plan** 的集成（Plan 内跨 Pack 已由 Plan Implementation Review 的 Cross-Pack Coherence 覆盖）：
- Cross-plan contract map：逐行读取 `docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`，用 `git diff <starting_commit>..HEAD` 验证 producer / consumer / owner / 验证方式是否在合并结果中成立
- Shared contract surface：跨 Plan 的 Pydantic model / schema_version / API 是否一致
- Migration 顺序：跨 Plan 的 migration 执行顺序是否正确
- Import 关系：跨 Plan 的 import 是否循环
- 状态竞争：跨 Plan 并发访问共享 state 是否安全
- UI 集成（如有）：跨 Plan 的页面集成效果

如果所有 Plan 之间没有共享 contract / migration / state surface，
Cross-Plan Integration 降级为确认独立性的 1 行声明。

Final Review 发现跨 plan 合同需要实现层修复时，返回 `NEEDS_EXECUTION`，并列出 affected plans、affected packs、连接面、producer / consumer 断点和必须重跑的验证。

## Calibration
**不要信任 plan/pack completion summary——独立验证。** Worker 和 Plan Implementation Review 可能遗漏了跨 Plan 交互问题、遗漏了 gap intent、或对已验证行为的判断在 merge 后不再成立。你的 review 必须基于代码和测试事实。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
Plan Implementation Review 已验证且 regression sweep 确认 intact 的行为——不是 finding。
措辞、风格偏好、nice-to-have 建议——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands
### Result
Regression Sweep:
Critical:
Important:

Intent Coverage:
通过: X / Y
Gap intents verified:
Covered by plan impl review (confirmed intact):
Implementation Gaps:
Design Gaps:
Context Gaps:
Unverifiable:

Cross-Plan Integration:
Critical:
Important:
NEEDS_EXECUTION:

Release Risk:
Blockers:
Manual verification:
Rollback concerns:

Phase Summary:
可以完成 / 阻塞
Disposition required:
### Verification
### Open Items
```

### Baseline 2：Independent Code-Level Audit

独立第二视角对最终实现做正确性、回归和集成审查。两个 baseline 角度互不重叠——Baseline 1 聚焦 design intent 和跨 pack 完整性，Baseline 2 聚焦代码级正确性和安全性。

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/final-review-baseline-2.md`：

```markdown
## Scope
Independent code-level audit for a completed implementation.
All Plans have individually passed Plan Implementation Review.
You are the second reviewer — your perspective is independent of Baseline 1.

## Starting commit
<commit hash>

## Full diff
git diff <starting_commit>..HEAD

## Source design
docs/orchestrate/design/<slug>.md（已通过 Design Review）

## Plans（已通过 Plan Review）
docs/orchestrate/plans/<slug>/（目录，逐个列出所有 plan 文件路径）

## Plan completion summary
| Plan | Plan Impl Review verdict | Repair rounds | Packs | Release gate |
<paste per-plan summary>

## Pack completion summary
| Pack | Plan | Worker verdict | Verified behaviors |
<paste per-pack summary>

## Review steps

对 starting commit 到 HEAD 的完整 diff 做以下审查：

1. **Correctness**：逻辑错误、off-by-one、null/undefined 处理、类型不匹配、边界条件。
2. **Regression**：变更是否破坏既有功能。跑完整测试套件并报告结果。
3. **Security**：injection、auth bypass、敏感数据泄漏、insecure defaults、OWASP top 10。
4. **Integration**：跨文件变更是否协调一致；模块间接口是否一致。
5. **Design alignment**：实现是否匹配 design doc 的 stated intents。
6. **二阶故障**：如果 A 失败，B 是否优雅处理（error propagation、retry、rollback）。
7. **Edge cases**：空状态、错误路径、retry/rollback、竞态、测试未覆盖的边缘场景。
8. **Forbidden shortcuts**（以下默认是 finding；影响验收/数据/权限/账务/runtime/发布时是 Critical）：
   · bare dict 作跨模块长期合同
   · route/host 内临时拼 nested dict 绕过正式 contract
   · 新增 route-local schema/helper 而不放 domain service/shared contract
   · public API 返回 dict[str, Any]
   · silent unknown-field drop / extra=allow 无版本策略
   · 直接写 JSONB/SQLite JSON 不注册不走 validator
   · 新 DB 字段没有 migration/repository/read model/回归测试
   · 新 port/command/chargeable action/capability 没进 registry/catalog
   · 测试 mock 仓库内部业务模块
   · helper 只为绕过边界而存在

## Calibration
**不要信任 worker 的报告和 Plan Implementation Review 结论——独立验证。** 代码可能在 merge 后产生新问题，测试可能不覆盖你正在审查的边界情况。你的审计必须基于代码事实。

只标记会导致实际问题的 issue。每个 finding 必须有 evidence。
Plan Implementation Review 已验证的代码质量问题——不再重复。
措辞、命名偏好、nice-to-have 建议——不是 finding。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands
### Result
Code-Level Audit:
Critical:
Important:
低置信度观察:

Disposition required:
### Verification
### Open Items
```

## Step 5：并行提交

两个 baseline 可同时提交（两个 Codex background task）。Budget 消耗 2。

---
> **下一步**：两个 baseline 提交后 → Steps 6-8（final-review-disposition.md）。
