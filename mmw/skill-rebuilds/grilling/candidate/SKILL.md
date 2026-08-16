---
name: mmw-grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, uses any grill trigger, a new need or change is not yet settled, or another skill hits an unresolved product or design trade-off.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

When a term, bounded context, relationship between bounded contexts, or ADR-worthy decision appears, invoke `/mmw-domain-modeling` in this same conversation, then return to the current round. Do not save them up.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Each question should be formatted like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. Don't ask the user for anything you could look up yourself. Don't block the frontier on a running lookup: only questions downstream of it wait; ask the rest now. The _decisions_ are the user's: put each to them and wait.

If the caller passed Required materials, resolve them as `/mmw-wayfinder` specifies. Facts already in those materials go into the tree; fetch the rest as follows:

- One file, one symbol, or one command: do it yourself.
- Several independent angles: `/mmw-research`. It returns a README path. Read that index and the files it lists. Put those facts back in the tree.
- Talk cannot decide it, or the fact only exists once something is running: `/mmw-prototype`. Pause only the branch that waits on that walkthrough.
- Another person holds the fact and this user cannot answer: `/mmw-to-questionnaire`. Put the answer back in the tree when it returns.
- The user must see existing pages: open each page in its own view so they can compare.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

Write the **shared-understanding record** before you ask for that confirmation. `mmw artifact path scratch --sub understanding.md` prints the path; write there. On a wayfinder decision ticket, add `--name` and `--issue` as `/mmw-wayfinder` specifies for that ticket.

Write `## Round Q&A` first, then `## Shared understanding`. The shared understanding is transcribed from the Q&A — that section keeps the user's reasons, figures, and corrections.

```markdown
## Round Q&A

<one subsection per round. Paste that round's questions as sent; under each, the user's words.>

## Shared understanding

### Scope

- What this settles. What it explicitly does not.

### Decisions

| What was decided | The user's reason | Options considered and rejected |

### Constraints

- One line each: the constraint, and whether it came from the user, the repo, or outside.

### Trade-offs

- One line each: between what, which side, what was given up.

## Supporting materials

| Kind | What to list |
| --- | --- |
| research facts | facts from the findings files the README lists |
| research directory | artifact ref for the `README.md`, when later tickets will cite them |
| prototype | artifact refs for the prototype `README.md`, walkthrough conclusions, and the chosen artifact |
```

Write `none` in a supporting-materials row that has no artifact. Then check: every visited branch has a Decisions row; every correction the user made landed in its row. Paste the `## Shared understanding` section into the chat and wait.

A yes here confirms this shared understanding only. A later spec still needs its own confirmation.

If they stop early, report what is settled, which decisions are still open, and which facts are still waiting. No shared understanding yet.

After they confirm, ask whether to send an independent reviewer for ⓪ shared-understanding review (`/mmw-review`). Wait. If they say yes, the object is this record; `## Round Q&A` is what the reviewer uses to catch contradictions. Accepted findings reopen the affected branches, then rewrite the record. Do not send the rewrite to review again.

If another skill invoked this one, return the record's path. If the user invoked it, report the path and ask: write a spec, start a prototype, or stop here.
