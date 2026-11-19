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

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), find it through the **Investigation** playbook of the **mmw-mode** skill, with the fact as its question, what the interview has settled as what you know, and the question it unblocks as what the answer is for. Don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait; when Investigation has sent sessions out, ask the rest of the frontier now and end your turn. Once its answer is back, bring the fact into the next round. The _decisions_ are the user's: put each to them and wait.

Put to the user only the decisions that are theirs. A choice their standing instructions leave to you, usually an engineering one, you make: state it with its reason in the recommended answer it bears on, where they can overrule it, and do not ask it. Write each question as the **mmw-mode** skill's `references/handling-a-request.md` `## Writing the reply` says. A question the user has to ask you to explain has cost a round.

Think through **principle-first-principles-thinking** when forming each recommended answer. It adds no rounds and does not change the question format.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
