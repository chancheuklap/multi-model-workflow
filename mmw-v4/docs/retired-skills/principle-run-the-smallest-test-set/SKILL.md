---
name: principle-run-the-smallest-test-set
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Run the Smallest Test Set

A repository-wide full test suite is prohibited by default. Run the smallest relevant test set that proves the requested change.

**When the full suite is allowed:**
- An explicit release, closeout or acceptance gate requires it.
- The change crosses boundaries that targeted tests cannot cover, and you can name the specific unresolved risk.

State that reason before starting the full suite. Habit, completeness and extra confidence are not sufficient reasons.

Distinct from **principle-sequence-verifiable-units**, which says to check each unit before the next. This says how much to run when you check.
