---
name: mmw-mode
description: "How work runs in a repository that uses MMW: routes a task to its playbook, indexes the principles, says what an unattended session may decide and how a woken session picks up. Use in a repository that has a `.mmw/` directory, when a prompt names the mmw-mode skill, or when a message carries an `mmw <playbook>#<step>` pointer."
---

# MMW mode

## Non-negotiables

<!-- Situations that always route to one named skill, script or principle, whichever playbook is running: one line each, "situation → what to use". -->

## Principles

Read the principle file in full for any principle you apply. Each entry names when it applies. `principle-<slug>`, `**principle-<slug>**`, "the **<slug>** principle", "the **<slug>** principle skill" and a link to `principle-<slug>.md` all name the file `principles/principle-<slug>.md`.

**Core**

- **Laziness Protocol** (**principle-laziness-protocol**). Apply when refactoring, evaluating diff size, or tempted to add abstractions, layers, or signal threading.
- **Build the Lever** (**principle-build-the-lever**). Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks.

**Verification**

- **Prove It Works** (**principle-prove-it-works**). Apply after completing a task, before declaring done.

**Meta**

- **Encode Lessons in Structure** (**principle-encode-lessons-in-structure**). Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction.

**Pipeline**

- **Silence is never a pass** (**principle-silence-is-never-a-pass**). Apply when a check, gate, oracle or test is written, changed, run, or read as a result.
- **A second reader judges** (**principle-a-second-reader-judges**). Apply when a piece of work needs judging: a diff, a batch of tickets, a decision.
- **One home per meaning** (**principle-one-home-per-meaning**). Apply when a rule, a term or a fact is about to be written where it already lives elsewhere.

**User rules.** The user's own instructions are already in your context: your host loads them at the start of every session. They number their rules 1 to 15 under `## Who decides what`, `## How to report` and `## How to work`, and this skill names them user rule 1 to user rule 15. Read the rule there, in your context, when its moment comes. Rule 1 when a decision may be the user's to make. Rule 6 when you name a concept. Rule 10 before you write anything another reader picks up. Rule 11 when a step of yours fails or is cut short. Rule 13 when you edit a file. Rule 14 before you design or write non-trivial code. Rule 15 before you run tests.

## Autonomy

**Precedence.** The user rules come first, then this mode, then the playbook you serve (its local qualification of a principle included), then a principle. A human gate a capability skill carries is not in this order: with the user present, stop at it.

**With the user present.** User rules 1 to 3 say who decides what.

## Re-entry

<!-- How a session that was woken, compacted or resumed finds the step it is at, before it does anything else. -->

## Subagents

<!-- When to start a subagent, what its brief carries, and who owns its output. -->

## Writing the reply

A reply to the user follows user rules 4 to 9. Every playbook ends with a reply written this way. Each playbook's `**Reply:**` line names only the content unique to that playbook. An unattended session's reply is its playbook's deliverable.

## Playbooks

Match the task to a playbook below and open its file. Open a todolist whose first items are that playbook's numbered steps, each copied in verbatim with its title and its `Done when` line, before any task-specific todos; the rest of the file (its opening, any `####` section, its **Reply:** line) is read, not copied. A step you choose not to do stays in the list with a one-line `skip: <reason>`. When a step runs another playbook, that playbook's steps go into the list under the step, the same way. With no todo tool, list the step titles and `skip:` lines at the top of your reply.

When no playbook below fits, say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies. The deliverable before any code is the workflow itself.

- **Authoring or modifying a skill.** Writing or editing a skill, a playbook, a principle, this mode, or any text an agent reads; a change to the product's code is not this playbook's. `playbooks/authoring-a-skill.md`.
- **Review the skill set.** Reviewing the text of the whole skill set, or of some of its skills, by walking the tasks agents do with it ("review the skills", "audit the skill set"). Distinct from the `code-review` skill, which reviews a code diff, and from **Authoring or modifying a skill**, which changes the text. `playbooks/review-the-skill-set.md`.
