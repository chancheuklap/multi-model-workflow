---
name: grilling
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
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

Word each question so "yes" accepts your recommended answer.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), send a researcher to find it: a brief with `## Task` the fact, `## Known` what the interview has settled, `## For` the question it unblocks, sent with `dispatch.sh send researcher <brief>` of the **dispatch** skill. Don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait; ask the rest of the frontier now and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking` and bring the fact into the next round. The _decisions_ are the user's: put each to them and wait.

Put to the user only the decisions that are theirs. A choice their standing instructions leave to you, usually an engineering one, you make: state it with its reason in the recommended answer it bears on, where they can overrule it, and do not ask it. Write each question for a reader who has not read what you read: what raised it, and what each option does to the product, in plain words. A question the user has to ask you to explain has cost a round.

Think through **principle-first-principles-thinking** when forming each recommended answer. It adds no rounds and does not change the question format.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
