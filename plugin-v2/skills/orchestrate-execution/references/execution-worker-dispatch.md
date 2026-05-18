# Worker Dispatch — Pack Brief Template

> **流程位置**：`orchestrate-execution` Step 5 · 构造 Pack Brief 时读取

Dispatch prompt 必须自足——worker 不读 SKILL.md、不读 references、不读 plan 文件。Coordinator 从 plan 中提取并在 prompt 中写全以下所有字段：

```text
Pack: <pack number + title>
Issue: <issue reference>
Scope: <editable artifacts for this pack>
Goal behavior: <end-to-end behavior description>
Implementation tasks:
  <paste ALL tasks with full text — don't让 worker 读 plan 文件>
Owned files:
  - Create: <path — responsibility>
  - Modify: <path — responsibility>
  - Test: <path — behavior covered>
Read first:
  - <source docs, ADRs, project rules, mockups>
Contract anchors:
  - boundary type / owner / provider / consumer / verifier
  - Pydantic model / schema_version / compatibility
  - registry / migration / catalog
  - repository / read model
  - tests / release gate
  - forbidden shortcuts
Mockup anchors:
  - path / viewport / states / interaction / visual verification
Acceptance criteria:
  - [ ] <each criterion>
Verification commands:
  - <command> → Expected: <result>
Commit boundary: <one atomic commit scope>
Risk flags: <normal / high-risk / production-risk / billing / permission / migration / runtime / UI / HITL>
发布风险: <risk surface / N/A>
AFK / HITL: <manual gate requirements>
Dependencies: <pack dependencies>
Parallel safety: <can parallel with which packs / why>
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

**关键规则**：
- Pack Brief 必须来自已通过 Plan Review 的 plan。无效 pack 先修回 plan，不在 dispatch prompt 里临场重切。
- 所有 task 完整文本直接贴在 prompt 中——不让 worker 读 plan 文件（节省 worker 上下文，确保 worker 拿到的是完整信息）。
- Coordinator 提供场景上下文（where this fits, dependencies, architectural context），让 worker 理解这个 pack 在整体中的位置。
