---
name: orchestrate-design-review
description: "Phase 0a 设计审查。由 orchestrate-workflow coordinator 在 Discovery 产出 design document 后调用。派发 2 个 Codex baseline reviewer 审查设计完整性和项目对齐。内部 phase skill，不由用户直接触发。"
---

# Orchestrate Design Review (Phase 0a)

审 design document，确认能被 issue 拆分、plan、Task Pack 和实现承接。不做文字润色、不派 worker、不写 plan。

## Flow

```
Step 1: Read references/design-review-angles.md.
        Build dispatch prompt for 2 baseline codex-reviewers.

Step 2: Dispatch reviewers.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md for Return Contract + Finding Shape.
        Read ${CLAUDE_PLUGIN_ROOT}/references/review-budget.md for budget check.
        Dispatch 2 baseline codex-reviewers via codex:codex-rescue --model gpt-5.4.

Step 3: Receive results.
        Disposition each finding per dispatch-primitives.md Reception Rules.
        Coordinator must independently verify — not relay reviewer claims.

Step 4: Route.
        pass → check issue hierarchy; missing → to-issues → orchestrate-plan-writing.
        Backflow and upstream skills (Skill tool; write back before continuing):
        - domain / UX / ownership ambiguity → Skill: orchestrate-discovery → 写回 design document
        - terminology conflict → Skill: grill-with-docs → 写回 domain docs + design document
        - issue gap → Skill: to-issues → 写回 Issue recording target
        - user decision needed → 停止，问用户一个问题
```

## Pass 条件

两个 baseline review 通过 + 无 Critical finding。最多 2 个 repair rounds。

## Reception

- accepted document repair → coordinator / docs-worker 修 design。
- accepted domain / UX / ownership ambiguity → orchestrate-discovery。
- accepted issue gap → Phase 0a 通过后 route to-issues。
- rejected / out of scope / duplicate → 记录，不 repair。

修复后 targeted re-review changed sections + 受影响 angle。

## Release Gate

只在 release strategy / migration-deploy order / rollback / manual gate 必须提前判定时追加 `codex:codex-rescue --model gpt-5.5`。普通 production-risk 由 baseline 转成 risk flags。
