# Plan Review Codex Dispatch Template

> **流程位置**：`orchestrate-plan-writing` Steps 13-14 · Plan Review Codex 派发 · 派发后 → Steps 15-18（`plan-review-resolution.md`）

**Read** `${MMW_PLUGIN_ROOT}/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

以下是 review prompt 内容（写入 `.codex/multi-model-workflow/review-prompts/plan-review.md`）：

```markdown
## Scope
Review the implementation plan for: <feature>

## Source artifacts（路径从 Scope Contract feature slug 推导）
- Plans: docs/orchestrate/plans/<slug>/（目录，每个大 issue 一份 plan 文件）
- Cross-plan contract anchors: docs/orchestrate/design/<slug>.md#cross-plan-contract-anchors
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
- design.md `## Cross-Plan Contract Anchors` section 覆盖所有跨 plan producer / consumer / ownership 连接面
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

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`gate`（`plan-review`）、`review_intent: "baseline"`。
2. 在 `Source artifacts:` 中列出 plan 目录、design.md、issues 目录路径（reviewer 自读内容）。
3. 写 `review-prompts/plan-review.md`，运行 `dispatch-review.sh validate`，用 `spawn_agent(agent_type="codex_reviewer")` 派发 reviewer，再运行 `dispatch-review.sh record` 保存 agent id。
4. 用 `wait_agent` 等待 reviewer final message，保存到 `review-results/plan-review.md`，再运行 `complete-review-dispatch.sh` 标记 durable result 并计入 review budget；complete 成功后 `close_agent` 释放容量。
5. 读取 review-results 文件，进入 Steps 15-18 disposition 流程。

---
> **下一步**：Review 派发后 → Steps 15-18（`plan-review-resolution.md`）。
