---
name: principle-sequence-verifiable-units
description: "Apply to multi-step work and the order of commits and PRs. Check each unit before the next. Keep behavior-preserving steps green. A repro commit must fail for the expected reason before the fix makes it pass."
disable-model-invocation: true
---

# Sequence work into verifiable units

Order work as a sequence of small units, each ending in a state you can check. Verify each unit before starting the next. For behavior-preserving edits, keep the checks green at every step.

**Why:** A break caught at the unit that caused it is cheap to localize. A break caught after a batch is buried, and you have already built further on a broken base. Sequencing those same units into a delivery a reviewer can replay turns "trust me" into "watch it go red, then green."

**Execution.** In a sweep, migration, or any run of similar edits, verify each change before starting the next. Each unit is a before/after bracket: known-good state, one change, run the check, then proceed. Rebase onto clean trunk first so every check measures against the real baseline. When a lever does the edits, the per-unit check is nearly free. Run it anyway.

**Delivery.** Stack commits and PRs in the order that proves the work. The canonical shape is the failing test first, then the fix on top. Check the state each commit is meant to establish. The repro commit must fail for the expected reason, and the fix must make it pass. Other story orders are a subtraction before the reshape, a baseline capture before the treatment, the scaffold before the feature. Each commit lands on its own and the sequence reads as an argument.

The sequencing complement to the [principle-prove-it-works](../principle-prove-it-works/SKILL.md) principle skill, which keeps each check real, and the [principle-build-the-lever](../principle-build-the-lever/SKILL.md) principle skill, which makes the per-unit check cheap.
