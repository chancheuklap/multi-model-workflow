# The components of the set

For a step that decides where a passage of skill text goes, or checks whether it is there. Where a passage lives decides when an agent reads it: put it where the agent that needs it is already reading at the moment it needs it, and nowhere that every run opens without needing it. A passage in the wrong component is either missing at its moment or read on runs that do not use it.

## The seven components

Each component answers one question and is reached in one way.

| Component | The question it answers | When an agent reads it | Where it lives |
| --- | --- | --- | --- |
| **mode** | Which situation calls for what, which playbook a task takes, what an unattended session may decide, and how a woken session picks up | At the start of every task in a repository that has a `.mmw/` directory, or when a prompt names the `mmw-mode` skill. Its sections are used at their moments: `## Non-negotiables` whenever one of its situations comes up, whatever playbook is running; `## Playbooks` to pick the task's playbook, `## Principles` when a decision comes up, `## Autonomy` when a decision may be the user's, `## Subagents` before starting one, `## Writing the reply` before the reply | the `SKILL.md` of the `mmw-mode` skill |
| **playbook** | The steps of one kind of task from start to finish, who owns what, and what is handed back | When its route line in the mode matches the task, or when a step of another playbook runs it. Its numbered steps are copied into the todolist; the rest of the file is read, not copied | the `playbooks/` of the `mmw-mode` skill, one file each, opening with its `###` title, with no frontmatter; a repository's own in its `.mmw/playbooks/` |
| **principle** | A judgement that holds across tasks and changes a specific decision. It belongs to no single skill and can be said as "when X, do Y, because Z" | Only when its condition fits the situation in front of the agent: the condition on its index line in the mode's `## Principles`, or a condition a step states. Then it is read in full. A run whose situations never meet the condition never opens it | the `principles/` of the `mmw-mode` skill, one file each, opening with its `#` title, with no frontmatter: a principle is not a skill and is never invoked |
| **capability skill** | How one thing is done and what it hands back; it does not know who calls it | When a step hands it a whole job by name, when its `description` matches what the user asks, or when the user invokes it | its own skill directory |
| **reference** | Material that belongs to one moment of the skill that owns it and means nothing outside that skill: a brief or prompt template handed to a subagent or a separately started session, a template or example to fill, a catalogue or checklist to look things up in, or the rules of one branch of that skill's work that a run may not reach | When the step that points to it reaches the condition the pointer states | the `references/` of the skill that owns it |
| **script** | The state reads and writes, deliveries and checks that come out the same on every run | Run by the step that gives its command; the agent reads what it prints, not its source | the `scripts/` of the skill that owns it |
| **role and configuration** | Which role reads which playbook, on which model, and which event wakes it at which step | Read by the scripts that start sessions, not by the agent | the `roles.json` of the `mmw-mode` skill (none yet: no role runs from v3), and `~/.mmw/models.json` |

**The test.** A passage lives in the component whose question it answers. A passage found in another component is a finding, unless a constraint keeps it there and the change that left it names that constraint; in MMW the constraints are H1 to H6 and S in `docs/adr/0032-the-set-is-layered.md`. Staying is not justified by "no benefit", "it works today" or "the change is large".

## How one component reaches another

- **What every run needs is where the run already is.** A sentence every run of a step acts on is written in the step, or in the one file the step hands its job to. A second file the step must open is a jump (`references/skill-set-rules.md` `### Load and disclosure`). When steps of several playbooks need the same sentence on every run, it goes into the capability skill they all hand the job to, not into each step: a copy per step is a second home.
- **A principle is named with its condition.** A step names a principle only for a situation some runs meet: "when two fixes that share one premise have failed, `principles/principle-attack-the-premise.md`". A principle named on a step every run takes is read on every run, so it is no longer working as a principle: write the sentence the step acts on into the step, and drop the name. A principle no step names is reached by its index line alone.
- **A caller may narrow a principle for its own case**, in its own text ("the smallest change the evidence justifies ships"). The mode's `## Autonomy` ranks that narrowing above the principle.
- **Directions.** The mode reaches playbooks by route line, capability skills by its `## Non-negotiables`, and principles by its index. A playbook reaches another playbook by running it at a step, a capability skill by handing it a job by name, a principle by naming it with its condition, and its references and scripts by path. A capability skill reaches another capability skill by name, its own references and scripts by path, and a principle by naming it with its condition. A principle names another principle only to mark a distinction ("Distinct from …"). Nothing names a step number inside another component. A capability skill names no playbook, and a script calls nothing above it.
- **A capability skill carries its own human gates**, since it can run outside any playbook. Whether a gate stops a given run is the mode's `## Autonomy`.

## Where a passage goes

Ask in order; the first yes decides.

1. Does it need judgement, cannot be undone, or need a person's decision? It is text, not a script; the questions below decide which text.
2. Does it come out the same on every run, so a program can perform it or check it exactly? A script, with its command given in the step that runs it (`principles/principle-encode-lessons-in-structure.md`).
3. Is it the order of several capabilities and judgements for one kind of task, with a deliverable of its own? A playbook. Being run by other playbooks keeps it a playbook.
4. Is it one capability with a result you can name, used beyond one playbook (the user invokes it, or several steps hand it a job)? A capability skill, with its own steps inside it.
5. Is it a judgement that holds across tasks, with a short name and an observable trigger, that changes a specific decision? The test: it can be said as "when X, do Y, because Z", and it stays true in a task other than the one in hand. A principle. A judgement that applies in one step of one task stays in that step.
6. Does it belong to one moment of one skill and mean nothing outside it: a brief or prompt template for another agent, a template or example to fill, a catalogue or checklist to look things up in, or the rules of one branch of that skill's work that a run may not reach? A reference of that skill. Material every run of a step reads stays in the file that step already holds.
7. Otherwise, or when moving it gives it no second caller and removes no duplication, it stays where it is.

## Signs a passage is in the wrong component

- A reference that every run of its caller opens, when the reader is the caller itself and not a subagent.
- A reference that steps of several playbooks open: what several tasks share is a principle or a capability skill, not a reference.
- A principle that names no decision it changes, or that only one step of one task uses.
- A principle named on a step every run takes.
- A playbook that only hands one job to one skill, with no ownership, gate or **Reply:** of its own.
- A citation of a step number inside another component.
- A capability skill that names a playbook.
