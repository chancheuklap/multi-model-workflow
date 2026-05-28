# Worker Dispatch — Pack Brief Template

> **流程位置**：`orchestrate-execution` Step 5 · 构造 Pack Brief 时读取

## Self-Read Protocol

你是 pack-executor 或 complex-pack-executor。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`pack_id`、`plan_id`。
2. 读 `DISPATCH_ENVELOPE` 中 `Read first:` 列出的所有源文件（design.md、ADR、mockup 目录等）。
3. 读本文件（你正在读的这份手册），理解 Pack Brief 字段含义与 Return Contract 格式。
4. 进入 Worker Loop：按 `Implementation tasks:` 逐条执行，TDD 红绿循环，每 task 完成后提交 commit。
5. 完成所有 task 后写 durable return JSON，再输出最终 Verdict。

<!-- BEGIN: control-envelope -->
## DISPATCH_ENVELOPE (required prefix for every Agent dispatch)

Every `Agent({...})` dispatch and every `SendMessage({...})` repair MUST begin its `prompt` with:

```
<!-- DISPATCH_ENVELOPE
{
  "protocol_version": "1",
  "run_id": "<run_id>",
  "phase": "<discovery|plan-writing|execution|final-review|bug-investigation|direct-repair|multi-pr-merge|hotfix|quickfix|maintenance>",
  "agent_role": "<pack-executor|complex-pack-executor|plan-writer|codex-reviewer|root-cause-analyst|code-explorer|complex-code-explorer>",
  "agent_id": "<existing agent_id or null for first dispatch>",
  "pack_id": "<N.M or null>",
  "plan_id": "<plan id (e.g. '001') or null>",
  "repair_round": 0,
  "idempotency_key": "<run_id>/<pack_id>/r<repair_round>",
  "disposition_refs": null,
  "review_intent": null,
  "exception_code": null,
  "correlation_id": "<run_id>/<pack_id>"
}
-->
```

For repair (repair_round >= 1): set `disposition_refs` to array of accepted finding IDs or route-worker follow-up references.
For codex-reviewer dispatches: set `review_intent` and `exception_code` for targeted-re-review.
For plan-level autonomous worker first dispatch: set `plan_id` to the plan id (e.g. "001") and leave `pack_id` null; for pack-level dispatch leave `plan_id` null. Exactly one of {pack_id, plan_id} must be non-null during execution.

Coordinator validates this block with an explicit dispatch script before `Agent({...})` / `SendMessage({...})`. Missing/malformed envelope = dispatch BLOCKED.
<!-- END: control-envelope -->

你（worker）按 `Self-Read Protocol` 自读本手册与 envelope 中的 `Read first:` 路径，不依赖 Coordinator 粘贴所有字段。Coordinator 只需在 envelope 中写明 `plan_id`（或 `pack_id`），其余上下文由你自读获取。

## 必需字段（每个 pack 都写）

```text
Pack: <pack number + title>
Goal behavior: <end-to-end behavior description>
Implementation tasks:
  <列出本 pack 的所有 task 标题；worker 自读 plan 文件获取完整文本>
Owned files:
  - Create: <path — responsibility>
  - Modify: <path — responsibility>
  - Test: <path — behavior covered>
Read first:
  - <source docs, ADRs, project rules, docs/orchestrate/mockups/<slug>/ (如有)>
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
Verification discipline:
  - For code behavior: use focused public-behavior tests, with RED/GREEN when risk is normal or higher.
  - For trivial docs/config/style sync: use proof-oriented checks such as `git diff --check`, build/generator check, manifest/schema validation, or path/link verification. Do not add tests that only assert wording exists unless that wording is a generated artifact or runtime contract anchor.
Risk flags: <trivial / normal / high-risk / ...>
Out of scope: <what NOT to touch>
Context hint: Your code will be reviewed alongside packs <N.1..N.M> within Plan N.
State directory: <absolute path to .claude/multi-model-workflow — Coordinator 用 $(pwd)/.claude/multi-model-workflow 填入>
Return contract:
  ### Verdict
  pass / blocked / needs repair / needs context
  ### Evidence
  ### Result
  - Changed files
  - Completed behavior (each with verification evidence)
  - Known gaps
  - Needs review
  ### Verification
  ### Open Items
  每条标记一个分类标签：
  - [out-of-scope] 不属于当前 pack 或整个 scope 的问题
  - [needs-evaluation] 需要独立评估才能判断是否修复的问题
  - [bug] 执行中发现的已有代码 bug（非本次引入）
  格式：`- [标签] 简述问题 — 发现位置 — 影响判断`

  ## Durable return（必须在最终 verdict 之前执行）
  写入 `<STATE_DIR>/pack-returns/<run_id>/<pack-id>.json`（绝对路径，Coordinator 在 dispatch 时填入）：
  {
    "pack_id": "<N.M>",
    "verdict": "<pass | blocked | needs repair | needs context>",
    "changed_files": ["<path1>", "<path2>"],
    "open_items": [{"tag": "<out-of-scope|needs-evaluation|bug>", "summary": "..."}],
    "concerns": "<如有>"
  }
  注意：必须使用此绝对路径写入（不是相对路径），确保 Coordinator 和 hooks 能读到该文件。
```

## 条件字段（仅在相关时包含，不写 N/A 占位）

```text
Contract anchors:          # 跨边界 pack（触碰 Pydantic / registry / migration / API contract）
  - boundary type / owner / provider / consumer / verifier
Mockup specs:              # mockup 目录存在时必填（从 plan 的 Mockup specs 字段原样复制）
  - 目录 / 涉及页面 / 视觉规格 / 交互行为 / 状态变体 / 验证方式
Dependencies:              # 有前置 pack 依赖
  - <pack N.M must complete first — reason>
发布风险:                   # high-risk / production-risk / migration / billing / permission / runtime
  - <risk surface + mitigation>
AFK / HITL:                # 有人工门禁
  - <manual gate requirements>
```

## 关键规则

- Pack Brief 必须来自已通过 Plan Review 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。
- 你自读 `Read first:` 路径中的 plan 文件获取 task 完整文本；Coordinator 只需列出 task 标题作为索引。
- 条件字段只在 plan 中该 pack 有对应内容时才包含——不写空字段和 N/A，减少无效 token 消耗。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Worker 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`（或 `pack_id`）、`phase`、`agent_role`。
2. 在 `Read first:` 中列出 plan 文件路径（worker 自读 task 全文）。
3. 触发 `state.sh` 记录 pack 开始状态。
4. 等待 `SubagentStop` hook 回收 worker 返回值。
5. 读取 `pack-returns/<run_id>/<pack_id>.json`，推进下一步编排。

---
> **回到**：SKILL.md Step 5b 继续填充 Pack Brief → Step 6 派发 Worker。
