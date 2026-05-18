---
name: orchestrate-plan-writing
description: "已有 reviewed source design / design document / SPEC / existing PRD / explicit requirements，并且已有 to-issues 产出的 vertical large issues / small issues，或用户要求把 design、PRD、issues 转成 implementation plan、Task Pack plan、issue-backed plan 时主动使用。负责生成可进入 Phase 0b 的 plan：large issue 映射 plan section，small issue 映射 Task Pack，pack 内写细 task；缺 source design 时返回 NEEDS_DISCOVERY，缺 issue hierarchy 时返回 NEEDS_ISSUES。"
---

# Orchestrate Plan Writing

生成或修复 plan。Plan 生成后交回 `orchestrate-workflow` 进入 Phase 0b。

## 身份确认

- **Coordinator（主线程）**：读取 `references/coordinator-dispatch.md`。
- **plan-writer（subagent）**：读取 `references/plan-writing-flow.md`。
