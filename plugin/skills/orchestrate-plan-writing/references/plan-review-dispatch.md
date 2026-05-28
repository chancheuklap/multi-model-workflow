# Plan Review Codex Dispatch Template

> **流程位置**：`orchestrate-plan-writing` Steps 13-14 · Plan Review Codex 派发 · 派发后 → Steps 15-18（`plan-review-resolution.md`）

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (`CODEX_SCRIPT` unset: `CODEX_SCRIPT="$(find ~/.claude/plugins -path '*/codex/scripts/codex-companion.mjs' -type f 2>/dev/null | head -1)"`)

Claude-native flow split-of-concerns:
- Coordinator runs `codex-companion.mjs` via Bash; the PostToolUse hook
  `hooks/track-review-budget.sh` auto-counts review budget the moment the
  `result` command fires (cap-guarded — won't double-count past exhaustion).
- The validate / record / complete scripts handle envelope checks, registry
  durability, and disposition recovery anchors — they do *not* touch budget
  counting (that's the hook's job on Claude).

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex-reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `--model gpt-5.5 --effort xhigh`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `--model gpt-5.4 --effort xhigh`
3. Validate envelope and dispatch (baseline vs targeted re-review — derived from `review_intent`):
   - **Baseline review** (envelope `review_intent: "baseline"`; gate name does not contain `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`
     Then write the registry entry: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<JOB_ID>"`.
   - **Targeted re-review** (envelope `review_intent: "targeted-re-review"`; gate name contains `-repair-`):
     Run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".claude/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>"`.
     `node "$CODEX_SCRIPT" task --background --resume --prompt-file <path> <model flags>`
     -> record JOB_ID into `review-prompts/<gate>.job-id`. The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer's recorded JOB_ID.
   - **Over-budget escape hatch**: if Review Budget is exhausted and the user explicitly authorizes another review, append `--allow-over-budget --override-reason "<brief user authorization>"` to the validate command (lets the dispatch through) and to the later complete command (records the override in the registry). Do not use this flag for convenience or for Effort Budget.
4. Wait: `node "$CODEX_SCRIPT" status "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)" --wait --timeout-ms 600000` (run_in_background: true)
5. Result: `node "$CODEX_SCRIPT" result "$(cat .claude/multi-model-workflow/review-prompts/<gate>.job-id)"` -> `review-results/<gate>.md`
   - The `track-review-budget` hook auto-increments review_used here (cap-guarded).
6. Mark durable: `bash "${CLAUDE_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<JOB_ID>" --result-file ".claude/multi-model-workflow/review-results/<gate>.md"`. If Step 3 used the over-budget escape hatch, pass the same `--allow-over-budget --override-reason "<brief user authorization>"` here to record the override in the registry.
6b. Disposition recovery anchor: before reading findings for disposition, run `bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status started`; after all findings have disposition records, run the same command with `--status completed`.

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

Compaction recovery:
- `.job-id` present but no `review-results/<gate>.md` -> resume from Step 4 (status + result) using that JOB_ID; once the result is saved and bookkeeping is complete, proceed to Step 6.
- `review-registry/<gate>.json` status is `completed` or `disposition_started`, and `review-results/<gate>.md` exists -> Read that exact result file and continue Coordinator disposition. Do not re-dispatch review and do not proceed to repair until `record-review-disposition.sh --status completed` has been recorded.
- If the `.job-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

以下是 review prompt 内容（写入 `.claude/multi-model-workflow/review-prompts/plan-review.md`）：

```markdown
## Scope
Review the implementation plan for: <feature>

## Source artifacts（路径从 Scope Contract feature slug 推导）
- Plans: docs/orchestrate/plans/<slug>/（目录，每个大 issue 一份 plan 文件）
- Cross-plan contract anchors: docs/orchestrate/design/<slug>.md#cross-plan-contract-anchors （前移自独立 cross-plan-contract-map.md；老 run 若仍有此文件请人工迁移）
- Source design: docs/orchestrate/design/<slug>.md
- Source issues: docs/orchestrate/issues/<slug>/
- Scope Contract: .claude/multi-model-workflow/scope-<run_id>.md

## Review angles (single integrated review)

### Issue Quality（小 issue 拆分审查）
**Read 每个 issue 文件**（`docs/orchestrate/issues/<slug>/00N-*.md`），审查 plan-writer 产出的小 issue 拆分质量：
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
- design.md `## Cross-Plan Contract Anchors` section 覆盖所有跨 plan producer / consumer / ownership 连接面（前移自独立 cross-plan-contract-map.md 文件）
- read-only context 未误纳入 editable scope
- mockup 已拆解为具体视觉规格写入 pack acceptance criteria（不是只给目录路径）
- 无含混行为（worker 需猜 desired behavior）
- 无 scope creep / 过度设计 / 设计不足
- 细 task 有短反馈循环（Red→Green→Refactor）
- 依赖真实、分组合理
- 高风险 pack 有对应验证

### Compliance & Verification
验路径、命令、合同、项目规则是否真实：
- 文件路径用 grep/find 逐条验真
- mockup 目录和文件存在 / fixtures / 命令存在
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
- 跨 plan 合同图没有 producer 缺失、consumer 缺失、ownership 冲突或 verification 空洞
- 项目工程规则违反

## Calibration
只标记会导致实际问题的 issue。实现者做出错误的东西或卡住——这是 issue。
措辞、风格偏好、nice-to-have 建议——不是。
除非有严重缺口（spec 需求缺失、步骤矛盾、placeholder 内容、task 模糊到无法执行），否则 approve。

Critical：intent 无覆盖 / source intent 不清却直接实现 / pack 不可执行 /
依赖错误 / 缺 Task Pack inventory / mockup 未拆解为具体视觉规格（只有目录路径） / 合同缺 anchors /
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
