---
name: principle-attack-the-premise
description: "Apply after two or more fixes sharing one premise fail the same gate, or when patches and rules accumulate without improving quality."
---

# Attack the Premise

When two or more fixes that share one premise fail the same gate, or when patches and rules accumulate, collide, or stop improving quality, suspect the premise or the layer you are editing rather than adding another patch.

- Write the premise down as the one sentence every failed attempt assumed.
- Test it before the next fix. Find an observation that would come out differently if the premise were false, and make it. Look at how the failures are distributed, not only at how large they are.
- If the evidence contradicts the premise, look for what the failures share that it did not predict. If one part always lands on the losing side, change what puts it there instead of adding a mechanism that cleans up after it.

When repeated edits at one level stop converging, step up one rung on the escalation ladder instead of patching at the same rung:

1. **Parameter.** Tune values, thresholds, or wording.
2. **Rules and structure.** Reorder competing rule priorities or split mixed responsibilities.
3. **Goal and standard.** Define an observable acceptance bar, or lock a reference example before editing further.
4. **Premise.** Reframe the problem itself under [principle-first-principles-thinking](../principle-first-principles-thinking/SKILL.md).

Do not start the next fix before the shared premise is tested or the escalation rung changes.
