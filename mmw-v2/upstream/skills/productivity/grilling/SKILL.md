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

Think this when forming each recommended answer. It does not add rounds, and it does not change the question format.

Before challenging the plan, decision, or idea, challenge the premise: invalid assumptions, conflicting prior decisions, or simpler existing solutions. An agent can ask excellent questions and still help refine something that should not exist. Surface any fundamental objections before refining the plan. Question the direction, not just the execution. Ask "Should this exist at all?"

First question the requirements, make the requirements less dumb. The requirements are always dumb to some degree, so start off by reducing the number of requirements. Otherwise you could get the perfect answer to the wrong question. Try to make the question the least wrong possible.

The premise is the one sentence that every failed attempt assumed. When two or more attempts that share one premise have failed, suspect the premise, not the attempts. Remove the asymmetry instead of compensating for it.

Strip assumed constraints to independently supported primitives, then rebuild. Escape analogy when convention fails or looks artificially expensive. Classify each claimed constraint as physics/math, regulation/contract, measured fact, or convention/analogy/authority. Keep only the first three as binding unless evidence upgrades a convention. Demand independent support (measurement, derivation, primary requirement)—not precedent alone. For each convention, state a falsifier. Drop or renegotiate anything lacking support.

"Industry standard is...", "We've always done it like this...", "Best practice says...", "That's just how it works..." — none of these are REASONS. They're appeals to convention. Ask: "But WHY? What fundamental truth makes this necessary?"

If the constraint is verified physics, hard regulation, or measured capacity, accept it and optimize within it. If a proven standard, protocol, or known-good pattern already fits, use it; do not re-derive. If a standard solution is already optimal under verified constraints, do not rebuild for novelty. Where the path is already clear, first principles is overkill.

Rebuild from remaining primitives only. Choose the simplest solution that meets the requirements; avoid overengineering and speculative abstractions. Prefer fewer moving parts over analogy. Then try to delete whatever the step is, the part, or the process step. People often forget to try deleting it entirely. And if you're not forced to put back at least 10% of what you delete, you're not deleting enough. And only the third thing is to try to optimize it or simplify it. The most common mistake of smart engineers is to optimize a thing that should not exist.

Is anything here unnecessary, overly complicated, or based on weak assumptions? Challenge them. Design for observed usage, not speculative edge cases. No speculative guards beyond what the requirements demand. If the proposed path adds layers, stop and look for a more direct path.

Do not fix symptoms. Trace every problem to its root cause. Prefer removing enabling conditions over only patching the proximate symptom. Do not add guards that silence a failure. If a workaround needs a paragraph-long comment to justify it, it is wrong.

When the subject is a failure, a recurrence, or a proposed patch: Distinguish 表层现象, 直接诱因, 根本原因. The first answer is almost never the real problem. Reflect on 5–7 different possible sources of the problem, distill those down to 1–2 most likely, and validate assumptions. Chain why with evidence; name and rule out alternatives. Stop on speculation. Branch before descending: ask what else could produce the same effect; keep every evidenced independent pathway rather than forcing one root. Would removing this cause block this pathway? Do not invent depth without data. If evidence is thin, say so. Challenge vague answers, reject "because that's how it is." If an answer blames a person, redirect to the process behind them.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
