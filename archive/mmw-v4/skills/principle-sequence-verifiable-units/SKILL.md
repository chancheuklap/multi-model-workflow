---
name: principle-sequence-verifiable-units
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Sequence work into verifiable units

Order work as small units with explicit checks. Advance when the current unit meets its declared criterion.

**Why:** A break caught at the unit that caused it is cheap to localize. A break caught after a batch is buried, and you have already built further on a broken base. Sequencing those same units into a delivery a reviewer can replay turns "trust me" into "watch it go red, then green."

**Execution.** Prepare shared types, setup and test infrastructure before the work that depends on them. In a sweep or migration, declare units around changes that can be checked together. Each unit records the baseline, the change and its check before the next unit begins. Merge the latest project branch in first so every check measures against the real baseline. A lever that performs the edits still runs the per-unit check.

**Delivery.** Stack commits and PRs in the order that proves the work. The canonical shape is the failing test first, then the fix on top. Other story orders are a subtraction before the reshape, a baseline capture before the treatment, the scaffold before the feature. Check the state each commit is meant to establish: the test commit demonstrates the expected failure, and the fix demonstrates the pass. Temporary migration commits follow **principle-outcome-oriented-execution** at their declared boundaries; final verification belongs at plan completion.

The sequencing complement to **principle-prove-it-works**, which keeps each check real, and **principle-build-the-lever**, which makes the per-unit check cheap.
