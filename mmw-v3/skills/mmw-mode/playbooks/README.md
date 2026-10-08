# playbooks/: how a playbook is written

Read `../../README.md` first: it holds the method every component follows. This file covers playbooks. Every other `.md` file in this directory is a playbook; this one is not, and has no route line.

The models to imitate are the 23 files in `mmw-v3/upstream-pstack/skills/poteto-mode/playbooks/`. Read `bug-fix.md` and `refactoring.md` before writing a first one.

## What a playbook is for

How one kind of task is done from start to end: who owns what, the steps, what is handed back. A playbook is not a skill. It has no frontmatter, cannot be invoked by name, and is opened only through a route line in `../SKILL.md` `## Playbooks` or a step of another playbook.

## When a new playbook is warranted

- **A new kind of task appears whose deliverable differs from every existing playbook's.** The test is the `**You own …**` line and the `**Reply:**` line: if both would read the same as an existing playbook's, it is the same task, and that playbook is edited instead. pstack added Hillclimb beside Perf issue because one is "sustained" improvement of a metric and the other a "one-off fix" (commit `b64f02a`).
- **Not for a task that happens once.** A playbook is saved here because the same kind of task comes back.
- **Not for handing one thing to one skill.** Name the skill in a `## Non-negotiables` line or in a step.

In the same change as the new file: add its route line to `../SKILL.md` `## Playbooks`. A playbook that starts a session role of its own adds that role as `../../README.md` `## subagent` says.

## The shape of the file, top to bottom

1. `### <Name>`: the title, identical to the name in the route line.
2. `**You own …**` in bold on the first line: what this run owns, and what goes to subagents.
3. One paragraph: the stance for the whole playbook, and how it differs from the playbook most easily confused with it.
4. Numbered steps, one action each. Each step names the skill, principle, reference or script it uses, by name or path. A principle is named on the step where it applies, including a step every run takes.
5. Optionally one paragraph of rules that hold across all the steps.
6. `**Reply:**` the content of the reply unique to this playbook. The rules every reply shares are in `../SKILL.md` `## Writing the reply` and are not repeated here.

A judgement several steps point to may follow the steps as a section of its own, opened by its name in bold (Run a night's **Routing a finding**); the two largest pstack playbooks (Orchestrate, Multi-phase plan) split into `####` subsections instead. A playbook may name a step of another playbook ("Run **Authoring or modifying a skill** on the findings").

## Sources in MMW v2

Numbered procedures that already have this shape: `implement`'s `## Closing steps` (eight steps, each ending in "Done when"), `dispatch`'s `references/night.md` (sections 1 to 6), `dispatch`'s `references/one-ticket.md`, and the routing rows of the `## Find your moment` tables that point to them. Decide each one by the tests above, not by its current location.
