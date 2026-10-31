---
name: principle-baseline-is-the-contract
description: Use when implementing or writing from an approved prototype, spec, answer, or other settled baseline. Follow its exact decisions and surface conflicts to its owner instead of silently changing them.
---

# The Baseline Is the Contract

A baseline is a decision someone already paid for: a user's answer, a prototype that won, a page they signed off. Anything in the material you were told to follow that records a settled conclusion is a baseline, and it is a contract, not a reference.

**Why:** Rewriting a baseline from memory, or improving it, reopens that decision where nobody who made it can see.

**Pattern:**
- Copy the values, wording, states and interface shapes of every baseline from it rather than writing them again from memory.
- Copy the winner prototype's appearance and interactions exactly. Rewrite its code to production standard.
- When something you were told to follow does not hold (it lacks a state, field, interaction or case, or contradicts another source), keep going on what still holds and raise the gap where whoever owns the baseline sees it. Quote what does not hold, and state what in that same source still holds and must be preserved.
- Never quietly change a baseline, never quietly add around one.

**In a diff:**

- Behavior no line of the ticket, the named spec sections or a baseline asked for, above all something the spec's `## Out of Scope` lists: remove it, or raise the gap to whoever owns the baseline.
- Something that looks implemented but does not match what was asked (the wrong value, state name, order or error): copy it from the source.
- A baseline the ticket names under `## Read first` holds the diff exactly as the spec does.

Distinct from **principle-redesign-from-first-principles**, which redesigns around a new requirement. A baseline belongs to whoever decided it: when it looks wrong, take it back to them instead of redesigning it yourself.
