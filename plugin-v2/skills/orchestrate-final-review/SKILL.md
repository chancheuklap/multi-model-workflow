---
name: orchestrate-final-review
description: "Phase B + C 最终审查和收尾。由 orchestrate-workflow coordinator 在所有 pack review 通过后调用。增强型审查：regression sweep + full intent coverage + cross-pack audit + 业务汇报 + 分支收尾。内部 phase skill，不由用户直接触发。"
---

# Orchestrate Final Review (Phase B + Phase C)

验证所有 pack 合并后是否满足 design intent，确认无 release blocker。Phase B 通过后进入 Phase C 业务汇报和收尾。

## Flow

```
Step 1: Read references/final-review-angles.md.
        Build dispatch prompt for 2 baseline codex-reviewers.
        Augmented review: regression sweep + full intent coverage + cross-pack audit.
        Read ${CLAUDE_PLUGIN_ROOT}/references/dispatch-primitives.md for Return Contract + Finding Shape.
        Read ${CLAUDE_PLUGIN_ROOT}/references/review-budget.md for budget check.

Step 2: Receive results.
        Disposition each finding.
        Repair per dispatch-primitives.md 修复归属.
        第 2 轮 targeted re-review 仍 needs repair → 截断 worker 循环：
          dispatch root-cause-analyst (Agent tool, 始终新建).
          Route by analyst Result.Resolution:
            - fixed → targeted re-review (消耗第 3 轮).
            - root cause found, not fixed → 用 analyst findings dispatch worker (消耗第 3 轮).
            - root cause in design/plan → 写回 design doc / plan, re-enter Phase 0a/0b.
            - unable to determine → BLOCKED, 报告用户附排除路径.
        Backflow and upstream skills (Skill tool; write back before continuing):
        - implementation gap → orchestrate-execution targeted repair
        - design / context gap → Skill: orchestrate-discovery → 写回 design document
        - plan gap → Skill: orchestrate-plan-writing → 写回 plan
        - architecture friction → Skill: improve-codebase-architecture → 写回 design doc / plan anchors
        If release gate triggered:
          read review-budget.md for release gate rules.
          Dispatch codex:codex-rescue --model gpt-5.5.

Step 3: Phase B passes.
        Read references/business-report.md.
        Assemble Phase C business report.

Step 4: Branch finishing.
        Clean up budget file + active-run-id + scope file.
        Commit, report to user. Done.
        只有用户明确要求才 merge / PR / push / cleanup。
```

## Pass 条件

两个 baseline review 通过 + release-risk gate 通过（或不触发）。每个 gap 最多 3 个 repair rounds（第 2 轮失败后由 root-cause-analyst 介入，第 3 轮为最终验证）。Phase B 内部 review dispatch 上限 10（2 baseline + 最多 3 gaps × 2 worker rounds + analyst round + final re-review；release gate 有独立预算见 `review-budget.md`）。

## Reception

- accepted implementation gap → orchestrate-execution targeted repair。
- accepted design / context gap → orchestrate-discovery → 必要 Phase 0a / plan。
- accepted plan gap → orchestrate-plan-writing / Phase 0b repair。
- accepted release blocker → complex-pack-executor / user decision → targeted release re-review。
