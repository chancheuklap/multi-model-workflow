---
name: principle-sequence-verifiable-units
description: "Apply to multi-step work and commit or PR order. Verify each unit and prove repro commits fail first."
---

# Sequence work into verifiable units

Order work as small units that each end in a state you can check. Verify each unit before starting the next. For behavior-preserving edits, keep the checks green at every step.

In a sweep, migration, or run of similar edits, each unit is a bracket: known-good state, one change, run the check, proceed. Run the per-unit check even when a tool does the edits.

Deliver in the order that proves the work: the failing test first, then the fix. The repro commit must fail for the expected reason, and the fix must make it pass. The subtraction before the reshape. The baseline before the treatment. Each commit lands on its own.
