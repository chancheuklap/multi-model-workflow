---
name: principle-baseline-is-the-contract
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# The Baseline Is the Contract

A baseline is a decision someone already paid for: a user's answer, a prototype that won, a page they signed off. Anything in the material you were told to follow that records a settled conclusion is a baseline, and it is a contract, not a reference.

**Why:** Rewriting a baseline from memory, or improving it, reopens that decision where nobody who made it can see.

**Pattern:**
- Copy the values, wording, states and interface shapes of every baseline from it rather than writing them again from memory.
- A design package is copied exactly. A prototype is rewritten to production standard, keeping the shape its verdict settled on.
- When something you were told to follow does not hold (it lacks a state, field, interaction or case, or contradicts another source), keep going on what still holds and raise the gap where whoever owns the baseline sees it. Quote what does not hold, and state what in that same source still holds and must be preserved.
- Never quietly change a baseline, never quietly add around one.

Distinct from **principle-redesign-from-first-principles**, which redesigns around a new requirement. A baseline belongs to whoever decided it: when it looks wrong, take it back to them instead of redesigning it yourself.
