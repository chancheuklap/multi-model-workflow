# Plan Review Codex Dispatch Template

> **流程位置**：`orchestrate-plan-writing` Steps 13-14 · Plan Review Codex 派发 · 派发后 → Steps 15-18（`plan-review-resolution.md`）

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (`CODEX_SCRIPT` unset: `CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"`)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review}` -> `--model gpt-5.4 --effort xhigh`
3. Dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
   - **Targeted re-review** (gate name contains `-repair-`):
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
   -> record JOB_ID into `review-prompts/<gate>.job-id`
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.job-id` present but no `review-results/` -> resume from Step 4.
<!-- END: review-dispatch -->

以下是 review prompt 内容（写入 `.claude/multi-model-workflow/review-prompts/plan-review.md`）：

```markdown
## Scope
Review the implementation plan for: <feature>

## Source artifacts（路径从 Scope Contract feature slug 推导）
- Plans: docs/orchestrate/plans/<slug>/（目录，每个大 issue 一份 plan 文件）
- Source design: docs/orchestrate/design/<slug>.md
- Source issues: docs/orchestrate/issues/<slug>/
- Scope Contract: .claude/multi-model-workflow/scope-<run_id>.md

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
```

Plan finding 必须说明是 plan 自身问题、design-plan mismatch、source design gap、issue-plan mismatch、context ambiguity，还是 architecture friction。
