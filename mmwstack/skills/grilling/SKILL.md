---
name: grilling
description: "Relentlessly stress-test a plan, decision, or idea while updating glossary and ADRs via domain-modeling. Use on plan stress-tests or 'grill' triggers."
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Identify the whole frontier. Ask one question at a time and give your recommended answer. Wait for the operator’s answer before asking the next question.

Use this format for each question.

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Word each question so "yes" accepts your recommended answer.

Each answer reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier before asking the next question. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), give a fresh general-purpose subagent the lookup, its context and the work issue URL. Follow [Subagents](../mmw-mode/SKILL.md#subagents). Use the model and settings from the current host's `judgment and prose` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). Ask for the fact and its source. Don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report. Ask the next independent question while it runs. The _decisions_ are the user's: put each to them and wait.

If a decision you need in this round depends on the operator trying the options, run the [Prototype playbook](../mmw-mode/playbooks/prototype.md) in this chat. Resume the interview with their answer.

Use [principle-first-principles-thinking](../principle-first-principles-thinking/SKILL.md) and think through it when forming each recommended answer. It adds no rounds and does not change the question format.

When working in a repository, load and use [domain-modeling](../domain-modeling/SKILL.md) throughout the interview. Update the project's glossary inline as terms settle and offer an ADR when a trade-off meets its criteria. It adds no rounds and does not change the question format. Skip it when no repository is in scope or the caller asks for a stateless interview.

When a playbook sets a narrower goal, return as soon as that goal is met. Otherwise, the session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
