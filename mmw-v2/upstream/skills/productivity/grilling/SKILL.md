---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

Think through the paragraphs below when forming each recommended answer. They add no rounds and do not change the question format.

Before refining the plan, decision, or idea, challenge its premise: invalid assumptions, conflicting prior decisions, or simpler existing solutions. Surface any fundamental objection first, and ask "Should this exist at all?"

Then question the requirements and reduce their number, so the question being answered is the least wrong one possible.

The premise is the one sentence that every failed attempt assumed. When two or more attempts that share one premise have failed, suspect the premise, not the attempts. Remove the asymmetry instead of compensating for it.

Strip assumed constraints to independently supported primitives, then rebuild. Escape analogy when convention fails or looks artificially expensive. Classify each claimed constraint as physics/math, regulation/contract, measured fact, or convention/analogy/authority. Keep only the first three as binding unless evidence upgrades a convention. Demand independent support (measurement, derivation, primary requirement)—not past practice alone. For each convention, state a falsifier. Drop or renegotiate anything lacking support.

"Industry standard is...", "We've always done it like this...", "Best practice says...", "That's just how it works..." are appeals to convention, not reasons. Ask: "But WHY? What fundamental truth makes this necessary?"

If the constraint is verified physics, hard regulation, or measured capacity, accept it and optimize within it. If a proven standard, protocol, or known-good pattern already fits the verified constraints, use it as it is; first principles is for where the path is not already clear.

Rebuild from remaining primitives only. Choose the simplest solution that meets the requirements, with the fewest moving parts. Design for observed usage: no speculative edge cases, abstractions, or guards beyond what the requirements demand. Then try to delete each step, part, or process step entirely; if you are not forced to put back at least 10% of what you delete, you are not deleting enough. Only then optimize or simplify what remains. If the proposed path adds layers, look for a more direct path.

Trace every problem to its root cause. Prefer removing enabling conditions over only patching the proximate symptom, and let a failure surface rather than adding a guard that silences it. If a workaround needs a paragraph-long comment to justify it, it is wrong.

When the subject is a failure, a recurrence, or a proposed patch: distinguish the symptom, the proximate cause and the root cause. Reflect on 5–7 different possible sources of the problem, distill those down to 1–2 most likely, and validate assumptions. Chain why with evidence; name and rule out alternatives. Branch before descending: ask what else could produce the same effect; keep every evidenced independent pathway rather than forcing one root. Would removing this cause block this pathway? Go only as deep as the evidence reaches; where it is thin, say so. Challenge vague answers. If an answer blames a person, redirect to the process behind them.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
