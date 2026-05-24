# Plan Review Codex Dispatch Template

> **流程位置**：`orchestrate-plan-writing` Steps 13-14 · Plan Review Codex 派发 · 派发后 → Steps 15-18（`plan-review-resolution.md`）

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Reviewer model and reasoning come from `agents/codex_reviewer.toml`. Do not pass per-phase model overrides in the dispatch call; the TOML agent config is the source of truth.
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent`.
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     Record the returned reviewer `agent_id` into `.codex/multi-model-workflow/review-agents/<gate>.agent-id`.
   - **Targeted re-review** (gate name contains `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport send_input`.
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Budget: after `wait_agent` returns for either baseline review or targeted re-review, run `bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget increment-review --run-id "<run_id>"`.
6. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.

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

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

以下是 review prompt 内容（写入 `.codex/multi-model-workflow/review-prompts/plan-review.md`）：

```markdown
## Scope
Review the implementation plan for: <feature>

## Source artifacts（路径从 Scope Contract feature slug 推导）
- Plans: docs/orchestrate/plans/<slug>/（目录，每个大 issue 一份 plan 文件）
- Source design: docs/orchestrate/design/<slug>.md
- Source issues: docs/orchestrate/issues/<slug>/
- Scope Contract: .codex/multi-model-workflow/scope-<run_id>.md

## Review angles (single integrated review)

### Issue Quality（小 issue 拆分审查）
**Read 每个 issue 文件**（`docs/orchestrate/issues/<slug>/00N-*.md`），审查 plan_writer 产出的小 issue 拆分质量：
- 小 issue 的并集是否覆盖大 issue `What to build` 的全部行为（无遗漏）
- 粒度是否合理（单个小 issue 不应需要超过 8 个 implementation steps；单文件内单函数修改不值得独立成 issue）
- 每个小 issue 的 acceptance criteria 是否可独立验证
- 小 issue 之间的依赖关系是否正确（无循环、无遗漏）
- AFK / HITL 标记是否正确（需要人工决策的标 HITL，其余标 AFK）

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
高风险缺迁移回滚 / task 间逻辑矛盾 / 循环依赖 /
小 issue 遗漏大 issue 行为 / 小 issue 不可独立验证 / 小 issue 依赖关系错误

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
### Result
Plan Review 结果：
Issue Quality:
Coverage & Task Quality:
Compliance & Verification:
Cross-Verification:
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
### Open Items
```

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction。

---
> **下一步**：Review 派发后 → Steps 15-18（`plan-review-resolution.md`）。
