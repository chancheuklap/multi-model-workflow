---
name: orchestrate-plan-review
description: "Phase 0b 计划审查。由 orchestrate-workflow coordinator 在 plan-writing 产出 plan 后调用。派发 3 个 Codex baseline reviewer 审查覆盖度、合规性和交叉验证。内部 phase skill，不由用户直接触发。"
---

# Orchestrate Plan Review (Phase 0b)

审 issue-backed plan，确认完整承接 source design 和 source issues，Task Pack inventory 可进入 Phase A。

## Flow

```
Step 1: Read references/plan-review-angles.md.
        Check Plan Entry Gate and Task Pack Inventory Gate.
        Build dispatch prompt for 3 baseline codex-reviewers.

Step 2: Dispatch reviewers.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md for Return Contract + Finding Shape.
        Read ${CLAUDE_PLUGIN_ROOT}/references/review-budget.md for budget check.
        Update budget_total and pack_count in budget file.
        Dispatch 3 baseline codex-reviewers via codex:codex-rescue --model gpt-5.4.

Step 3: Receive results.
        Disposition each finding per dispatch-primitives.md Reception Rules.

Step 4: Route.
        pass → orchestrate-execution.
        Backflow and upstream skills (Skill tool; write back before continuing):
        - design gap → Skill: orchestrate-discovery → 写回 design document
        - issue gap → Skill: to-issues → 写回 Issue recording target
        - plan gap → Skill: orchestrate-plan-writing → 写回 plan
        - architecture friction → Skill: improve-codebase-architecture → 写回 design doc / plan anchors
        - module map / call chain needed → Skill: zoom-out → 写回 design doc / plan anchors
```

## Pass 条件

三个 baseline review 通过 + 无 invalid pack / source mismatch / 虚构路径。最多 2 个 repair rounds。

## Reception

- accepted plan repair → orchestrate-plan-writing 或 coordinator 修。
- accepted design gap → orchestrate-discovery → Phase 0a → plan。
- accepted issue-plan mismatch → to-issues → plan-writing。
- accepted architecture friction → improve-codebase-architecture → 回写后 re-review。

修复后 targeted re-review changed sections + affected packs + 受影响 angle。

## Release Gate

只在 release order / rollback / manual gate 必须提前判定时追加 `codex:codex-rescue --model gpt-5.5`。
