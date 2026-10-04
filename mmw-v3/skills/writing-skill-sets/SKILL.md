---
name: writing-skill-sets
description: "Where a passage of a skill set's text goes, the checks it is held to, and how a task is walked through it; a skill set is skills that hand work to each other, with their playbooks, principles, references and scripts. Use when writing, editing or reviewing text an agent reads in such a set."
---

# Writing skill sets

The branch of the `writing-for-agents` skill for a **skill set**: the skills one install list ships (in MMW v3, every skill directory under `mmw-v3/skills/`), with their references and scripts, run by agents that each load only their own part. The `writing-for-agents` skill's `SKILL.md` gives the levers and the names of the failure modes; this skill applies them to a set whose skills hand work to each other. The checks are also the rules for writing: whoever writes or edits a skill in the set applies them to the passage in hand.

Text inside an upstream subtree also follows that subtree's own `AGENTS.md`.

## What skill text is for

Every check in this skill serves these seven facts about how an agent uses a set.

1. **A skill hands over understanding, not only steps.** Steps cover the cases their writer foresaw, and the agent meets others. So beside its steps a skill says what the work is for, who depends on what it produces and what a wrong or shallow result costs them, and, next to a rule, the reason for it: a model given the reason carries it into cases no rule names. Upstream's `wayfinder` does this in its opening and in `## Plan, don't do`. Such text is paid for as fact 4 says, by a judgement the agent could not make without it, and it has two tests. A sentence beside a rule passes when you can name a case the steps do not cover and what the agent does differently there with it. An opening passage passes when an agent holding only the skill could not otherwise say what the work is for, who acts on what it produces, and what a shallow result costs them. A sentence that only declares importance, retells the pipeline around the task, or tells this agent what another skill's agent does, fails both and is a no-op. One that passes is not cut for length; cutting it takes what `references/editing.md` asks.
2. **Scripts carry what is deterministic; text carries judgement.** A script runs the fixed procedure, checks what can be checked exactly, and says on refusal what happened and what to do next. The text tells the agent when to run it and how to decide what no script can decide: what counts as done, which of two readings applies, what the user meant. Text that narrates what a script does spends the agent's attention on work the agent does not do.
3. **Attention is the budget.** Every sentence an agent reads competes with the sentence it needs. Material read at a moment that does not use it, a rule stated twice, and a case the agent would handle by default all thin the attention left for the judgement the text exists to guide.
4. **Direct, then trust.** A skill states the goal, the constraints, the judgement calls and the completion criterion, and leaves the ordinary moves to the model. Text that scripts every move makes the flow **rigid** (the agent follows the list when the situation differs from it) and **brittle** (each enumerated case must be kept in step with the scripts, and the case nobody listed has no guidance at all). Upstream's `implement` is five lines: it names the skills it hands to (`tdd`, `code-review`) and trusts the agent with the rest. MMW's automation needs more than that, and each addition is paid for by a judgement the agent could not make without it.
5. **Progressive loading follows branches, not topics.** A file earns its own pointer when a given run can skip it. Material every run of a task reads belongs in the file that run already holds. Splitting it into pieces saves nothing and adds a jump for each piece.
6. **Skills are peers composed by name.** A skill reaches another by naming it and the job, as upstream's `grill-with-docs` ("grilling" and "domain-modeling") and `implement` do; the other skill is loaded whole and does its own job. A skill never carries a copy of another skill's files, and never restates another skill's rules.
7. **Everything has one home, and every skill has one place.** A method (how to interview, how to close a ticket), a concept, a piece of reference and a function each live in one skill, and another skill reaches it by naming that skill, as upstream's `grill-me` is a single call to `grilling`. A second copy is a finding however useful it looks: a flow retold as a map, a rule restated for a second reader, a definition repeated, a second entry to one function. It has to be kept in step with the first and in time contradicts it. A skill's place is set by the mode's route table and the playbooks, not by its own text: the route table sends each kind of task to one playbook, and a playbook step names the skill it uses. The order of a task therefore has one home, its playbook: a second statement of it drifts from the first, and a hop written in no playbook leaves the agent without a next step. A capability skill ends with what it hands back.

## Where to go

| Moment | Open |
| --- | --- |
| deciding where a passage goes | `references/components.md` |
| writing or checking any passage | `references/checks.md` |
| adding to or changing text that already exists: a fix, a new passage, a rename, a move, a deletion | `references/editing.md` |
| the passage is about a script, or is a script | `references/checks-scripts.md` |
| the passage is a skill's `description` | `references/checks-descriptions.md` |
| the passage is a start prompt, a subagent's brief, or the template either is written from | `references/checks-prompts.md` |
| the passage is inside an upstream subtree, or adapted from one (its skill's `imports.tsv` or merge-note says which) | `references/checks-upstream.md` |
| the passage gives an example | `references/checks-examples.md` |
| the passage is what a script prints for an agent | `references/checks-refusals.md` |
| walking a task as the agent that does it would | `references/walkthrough.md` |
| looking for an upstream skill that does a check well | `references/upstream-examples.md` |
