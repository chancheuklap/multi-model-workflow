---
name: principle-run-the-smallest-test-set
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Run the Smallest Test Set

A repository-wide full test suite is prohibited by default. Run the smallest relevant test set that proves the requested change.

**Why:** A full suite spends time and attention on code the change did not touch, and its green result proves nothing more about the change than the tests that cover it.

**Rule:**
- Run the full suite only when an explicit release, closeout, or acceptance gate requires it, or when the change crosses boundaries that targeted tests cannot cover and you can name the specific unresolved risk.
- State that reason before starting the full suite.
- Habit, completeness, and extra confidence are not reasons.

Distinct from **principle-prove-it-works**: a passing test is one proof among others, and the change still has to be checked on the real artifact.
