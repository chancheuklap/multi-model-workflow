# Worker Dispatch — Pack Brief Template

> **流程位置**：`orchestrate-execution` Step 5 · 构造 Pack Brief 时读取

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

Coordinator validates this block with an explicit dispatch script before `Agent({...})` / `SendMessage({...})`. Missing/malformed envelope = dispatch BLOCKED.
<!-- END: control-envelope -->

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全所有字段。

## 必需字段（每个 pack 都写）

```text
Pack: <pack number + title>
Goal behavior: <end-to-end behavior description>
Implementation tasks:
  <paste ALL tasks with full text — 不让 worker 读 plan 文件>
Owned files:
  - Create: <path — responsibility>
  - Modify: <path — responsibility>
  - Test: <path — behavior covered>
Read first:
  - <source docs, ADRs, project rules>
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
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
- 所有 task 完整文本直接贴在 prompt 中——不让 worker 读 plan 文件。
- 条件字段只在 plan 中该 pack 有对应内容时才包含——不写空字段和 N/A，减少 worker 的无效 token 消耗。

---
> **回到**：SKILL.md Step 5b 继续填充 Pack Brief → Step 6 派发 Worker。
