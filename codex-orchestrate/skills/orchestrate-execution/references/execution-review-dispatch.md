# Plan Implementation Review Codex Dispatch Template

> **流程位置**：`orchestrate-execution` Step 8 · 同一 Plan 内所有 Pack 完成后派发

同一 Plan 内所有 Pack 完成 Open Items 处置 + Git Checkpoint 后，派发 **1 个** baseline Codex reviewer 覆盖该 Plan 全部代码变更。

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

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

以下是 review prompt 内容（写入 `.codex/multi-model-workflow/review-prompts/plan-impl-review-N.md`）：

```markdown
## Scope
Review the implementation of Plan N: <plan title>
This plan implements Issue N: <issue title> (a vertical slice of <feature>).
All Task Packs within this plan have been executed and committed.

## Source artifacts
- Plan: docs/orchestrate/plans/<slug>/00N-*.md
- Source design: docs/orchestrate/design/<slug>.md
- Source issue: docs/orchestrate/issues/<slug>/00N-*.md
- Scope Contract: .codex/multi-model-workflow/scope-<run_id>.md

## Pack summary
| Pack | Worker verdict | Repair rounds | Changed files |
<paste per-pack summary within this plan>

## Aggregate diff
git diff <plan-start-commit>..<plan-end-commit>

## Changed files (all packs combined)
<combined file list with pack ownership>

## Contract anchors
<paste all contract anchors from all packs in this plan>

## Mockup anchors
<paste if any pack in this plan has UI work>

## Review angles (single integrated review)

### Spec Compliance
验 plan 中所有 pack 的实现是否满足要求：
- 每个 pack 的 acceptance criteria 是否满足
- 每个 pack 的 goal behavior 是否可从代码确认
- pack 之间是否有遗漏的交互行为
- 是否有 missing requirements（设计中有但代码没做到的）
- 是否有 extra/unneeded work（YAGNI）

### Code Quality
验实现是否正确、可维护：
- TDD 纪律：测试测的是 public behavior 而非 mock behavior
- Mock 纪律：mock 只用在外部边界
- 合同纪律：跨边界数据用正式 Pydantic contract
- Pack 间接口一致性：Pack A 暴露的接口是否与 Pack B 消费的一致
- Forbidden shortcuts（同现有列表）：
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

### Cross-Pack Coherence（原 Final Review 的 Cross-Pack Audit 下沉到这里）
验同 Plan 内多个 Pack 合在一起是否协调：
- Shared contract surface：跨 pack 的 Pydantic model / schema_version / API 一致
- Migration 顺序：多个 migration 的执行顺序正确
- Import 关系：跨 pack 的 import 无循环
- 状态竞争：并发访问共享 state 安全
- UI 集成（如有）：跨 pack 的页面集成效果

如果 Plan 中所有 Pack 之间没有共享 contract / migration / state surface，
Cross-Pack Coherence 降级为确认独立性的 1 行声明。

### Contract & Risk
验高风险面是否正确处理：
- Contract anchors 闭合（owner / provider / consumer / verification）
- Migration / registry / catalog 完整
- 发布风险标注准确
- rollback / compatibility 考虑

## Calibration
**不要信任 worker 的报告——独立验证一切。**
只标记会导致实际问题的 issue。
措辞、风格偏好、nice-to-have 建议——不是。
除非有严重缺口，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
Plan Implementation Review 结果：
Spec compliance:
Code quality:
Cross-pack coherence:
Contract & risk:
Critical:
  - [Pack N.M] <finding>
Important:
  - [Pack N.M] <finding>
Affected packs:
低置信度观察:
Disposition required:
### Verification
### Open Items
```

Plan Implementation Review finding 必须标注 `[Pack N.M]` 归属。`Affected packs` 字段列出所有涉及 finding 的 Pack 编号，Coordinator 据此路由 repair。

---
> **回到**：SKILL.md Step 9（接收 Review Findings + Disposition）。
