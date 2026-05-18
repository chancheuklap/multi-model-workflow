---
name: orchestrate-direct-repair
description: "Direct Repair 执行。由 orchestrate-workflow coordinator 在 Entry Gate 选择 Direct Repair 时调用。派 worker → 分级 review → 完成。内部 phase skill，不由用户直接触发。"
---

# Orchestrate Direct Repair

Entry Gate 选择 Direct Repair 时加载。条件：已有批准 design / plan / mockup / acceptance / failing test，目标行为清楚。

## Flow

```
Step 1: Read references/repair-grading.md.
        Determine review tier: skip / lightweight / full.

Step 2: Dispatch worker.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md at dispatch.
        Read ${CLAUDE_PLUGIN_ROOT}/references/custom-agents.md for agent selection.
        When contract boundary touched: read ${CLAUDE_PLUGIN_ROOT}/references/contract-boundary.md.

Step 3: Worker returns.
        Apply review tier from Step 1.
        Full review: dispatch codex-reviewer.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md + review-budget.md.

Step 4: Receive review (if dispatched).
        Disposition per dispatch-primitives.md Reception Rules.
        Routing:
        - needs repair → repair per dispatch-primitives.md 修复归属
        - desired behavior unclear → Skill: orchestrate-discovery → 写回 design document
        - bug needs reproduction → Skill: diagnose → 写回 bug brief
        - release gate triggered → read review-budget.md
        Done.
```

## Brief

用 Pack Brief 字段（见 `dispatch-primitives.md`），做以下适配：

- `Pack` 写 `Targeted repair`。
- `Issue` 写 accepted reviewer finding、failing test、批准 design / plan / mockup / acceptance 的 locator，或用户明确 repair brief。
- `Implementation tasks` 只写修复 accepted finding 或 failing behavior 所需步骤；不临场扩展 issue hierarchy。
- 缺目标行为、合同边界、UI target 或验收口径时，返回 Discovery / user decision，不让 worker 自行决定。

## Reception

- pass → 完成。
- needs repair → 按 `dispatch-primitives.md` 修复归属判断。
- release gate 触发 → 读 `review-budget.md` Release Gate 条件。
