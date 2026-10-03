---
name: mmw-mode
description: "How work runs in a repository that uses MMW: routes a task to its playbook, indexes the principles, and says which rule wins when two conflict. Use in a repository that has a `.mmw/` directory, or when a prompt names the mmw-mode skill."
---

# MMW mode

## Non-negotiables

<!-- Situations that always route to one named skill, script or principle, whichever playbook is running: one line each, "situation → what to use". -->

## Principles

Read the principle file in full for any principle you apply. Each entry names when it applies.

**Core**

- **Laziness Protocol** (`principles/principle-laziness-protocol.md`). Apply when refactoring, evaluating diff size, changing a function other code calls, about to write a helper, or tempted to add abstractions, layers, or signal threading.
- **Redesign From First Principles** (`principles/principle-redesign-from-first-principles.md`). Apply when integrating a new requirement into an existing design.
- **Attack the Premise** (`principles/principle-attack-the-premise.md`). Apply when two or more fixes that share one premise have failed the same gate.
- **Subtract Before You Add** (`principles/principle-subtract-before-you-add.md`). Apply when sequencing an addition, refactor, or rewrite, or when what you add replaces an existing branch, guard or file.
- **Build the Lever** (`principles/principle-build-the-lever.md`). Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks.

**Architecture**

- **Migrate Callers Then Delete Legacy APIs** (`principles/principle-migrate-callers-then-delete-legacy-apis.md`). Apply when introducing a new internal API while old callers still exist.
- **Make Operations Idempotent** (`principles/principle-make-operations-idempotent.md`). Apply when designing commands, lifecycle steps, or processing loops that run amid crashes, restarts, and retries.

**Verification**

- **Prove It Works** (`principles/principle-prove-it-works.md`). Apply after completing a task, before declaring done.
- **Fix Root Causes** (`principles/principle-fix-root-causes.md`). Apply when debugging.
- **Test Behavior, Not Implementation** (`principles/principle-test-behavior-not-implementation.md`). Apply when you write, change, or keep a test.

**Meta**

- **Encode Lessons in Structure** (`principles/principle-encode-lessons-in-structure.md`). Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction.

**Pipeline**

- **Silence is never a pass** (`principles/principle-silence-is-never-a-pass.md`). Apply when a check, gate, oracle or test is written, changed, run, or read as a result.
- **A second reader judges** (`principles/principle-a-second-reader-judges.md`). Apply when a piece of work needs judging: a diff, a batch of tickets, a decision.
- **One home per meaning** (`principles/principle-one-home-per-meaning.md`). Apply when a rule, a term or a fact is about to be written where it already lives elsewhere.
- **Human steps stay human** (`principles/principle-human-steps-stay-human.md`). Apply when a step can only be taken by a person.
- **Resume from durable state** (`principles/principle-resume-from-durable-state.md`). Apply when a session wakes, is compacted, or picks up work already begun.
- **Decide at phase boundaries** (`principles/principle-decide-at-phase-boundaries.md`). Apply when a phase of the session ends.

**User rules.** The user's own instructions are already in your context: your host loads them at the start of every session. They number their rules 1 to 15 under `## Who decides what`, `## How to report` and `## How to work`, and this skill names them user rule 1 to user rule 15. Read the rule there, in your context, when its moment comes. Rule 1 when a decision may be the user's to make. Rule 6 when you name a concept. Rule 10 before you write anything another reader picks up. Rule 11 when a step of yours fails or is cut short. Rule 13 when you edit a file. Rule 14 before you design or write non-trivial code. Rule 15 before you run tests.

## Autonomy

**Precedence.** The user rules come first, then this mode, then the playbook you serve (its local qualification of a principle included), then a principle. A human gate a capability skill carries is not in this order. With the user present, stop at it when it asks for a decision user rule 1 leaves to the user. A gate that asks the user an engineering question (which seam a test goes at, how to name a module) you answer yourself, and the reply names your choice and the alternative you set aside.

**With the user present.** User rules 1 to 3 say who decides what.

## Re-entry

<!-- How a session that was woken, compacted or resumed finds the step it is at, before it does anything else. -->

## Subagents

Use your host's general-purpose subagent. Its brief opens with "Read the `mmw-mode` skill's `## Principles` and the step you serve." A brief that is read-only and whole in itself, such as the fresh agent's in the `writing-skill-sets` skill's `references/walkthrough.md`, does not open with that sentence.

Start the subagents of one step in one message, and wait for all of them.

A subagent that must write nothing is told so in its brief: "You are read-only: write nothing." There is no read-only setting to rely on instead.

A subagent in this session names no model: it runs on this session's.

You own every subagent's work. Read its output and write your own summary, don't pass through what it said.

## Writing the reply

A reply to the user follows user rules 4 to 9. Every playbook ends with a reply written this way. Each playbook's `**Reply:**` line names only the content unique to that playbook. An unattended session's reply is its playbook's deliverable.

## Playbooks

The list below is the route table, and each of its lines a route line. Match the task to a playbook below and open its file. Open a todolist whose first items are that playbook's numbered steps, each copied in verbatim with its title and its `Done when` line, before any task-specific todos; the rest of the file (its opening, any `####` section, its **Reply:** line) is read, not copied. A step you choose not to do stays in the list with a one-line `skip: <reason>`. When a step runs another playbook, that playbook's steps go into the list under the step, the same way. With no todo tool, list the step titles and `skip:` lines at the top of your reply.

When no playbook below fits, say so, then open a todolist of the steps you will take, each naming the component it uses, before any work; the same `skip:` rule applies. The deliverable before any code is the workflow itself.

- **Authoring or modifying a skill.** Writing or editing a skill, a playbook, a principle, this mode, or any text an agent reads; a change to the product's code goes to `playbooks/make-a-small-change.md` or `playbooks/bug-fix.md`. `playbooks/authoring-a-skill.md`.
- **Review the skill set.** Reviewing the text of the whole skill set, or of some of its skills, by walking the tasks agents do with it ("review the skills", "audit the skill set"). Distinct from the `code-review` skill, which reviews a code diff, and from `playbooks/authoring-a-skill.md`, which changes the text. `playbooks/review-the-skill-set.md`.
- **Make a small change.** A change small enough that the user will check it directly: no tickets, no night. A change that needs several sessions, criteria a script runs and a reviewer of its own goes to `playbooks/write-a-spec-and-tickets.md`. `playbooks/make-a-small-change.md`.
- **Write a spec and tickets.** A conversation, an idea or a cleared map has to become a published spec and tickets that pass lint ("make this a spec", "cut the tickets"). Distinct from `playbooks/make-a-small-change.md`, which the user checks on the spot. `playbooks/write-a-spec-and-tickets.md`.
- **Bug fix.** Something is broken or throws ("debug", "diagnose"). `playbooks/bug-fix.md`.
- **Deliver a change.** Handing over a finished change the way this repository takes changes; the last step of `playbooks/make-a-small-change.md`, `playbooks/bug-fix.md` and `playbooks/authoring-a-skill.md`. `playbooks/deliver-a-change.md`.
