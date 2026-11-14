---
name: principle-baseline-is-the-contract
description: "Apply when implementing or documenting a settled decision from a spec, prototype, or the operator. Preserve the values, wording, and behavior the decision fixes. A prototype binds the question it settled."
---

# The Baseline Is the Contract

A settled baseline records a decision someone already paid for: the operator's answer, a choice settled by a prototype, a page they signed off. Anything in the material you were told to follow that records a settled conclusion is a baseline, and it is a contract, not a reference.

**Why:** Rewriting a baseline from memory, or improving it, reopens that decision where nobody who made it can see.

**Pattern:**
- Copy approved values, wording, states and interface shapes from the baseline rather than writing them again from memory.
- A prototype settles the question it was built to answer. Match its appearance and interactions exactly when those are the approved target.
- Settle open details as the active playbook directs. If a change would overturn a settled decision, raise the conflict with whoever owns it. Quote what conflicts and say which decisions still hold.
- Never quietly change a baseline, never quietly add around one.

Distinct from [principle-redesign-from-first-principles](../principle-redesign-from-first-principles/SKILL.md), which redesigns around a new requirement. A baseline belongs to whoever decided it: when it looks wrong, take it back to them instead of redesigning it yourself.
