---
name: principle-baseline-is-the-contract
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# The Baseline Is the Contract

A baseline is a decision someone already paid for: the owner's answer, the prototype that won, the page they signed, the section of a spec. Copy its values, wording, states and interface shapes from it. Do not write them again from memory, and do not improve them.

**Why:** Rewriting a baseline from memory, or improving it, reopens that decision where nobody who made it can see. Raising the problem where its owner sees it lets them decide again.

**Pattern:**
- When a baseline does not hold (it lacks a state, a field or a case, contradicts another source, or cannot be built as written), keep working on what does not depend on it, and say so where its owner sees it: quote what does not hold, and state what in the same source still holds and must be kept. On a ticket that place is a `contract` child.
- Never quietly change a baseline, and never quietly add around one.
- A reviewer reads the baseline itself, not the account of it given by whoever built against it.

Distinct from **principle-start-from-what-exists**, which chooses what to build on; a baseline is what was already chosen.
