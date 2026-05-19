# Worker Dispatch — Pack Brief Template

> **流程位置**：`orchestrate-execution` Step 5 · 构造 Pack Brief 时读取

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
  - <source docs, ADRs, project rules, mockups>
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
Risk flags: <trivial / normal / high-risk / ...>
Out of scope: <what NOT to touch>
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
```

## 条件字段（仅在相关时包含，不写 N/A 占位）

```text
Contract anchors:          # 跨边界 pack（触碰 Pydantic / registry / migration / API contract）
  - boundary type / owner / provider / consumer / verifier
Mockup anchors:            # UI pack
  - path / viewport / states / interaction / visual verification
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
