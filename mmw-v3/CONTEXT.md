# MMW v3

The vocabulary of the MMW v3 skill set: the kinds of text it is made of and the terms its skills use to write and review that text. A term used only in its field's ordinary sense, and a term of an upstream skill used in that skill's sense (the `writing-for-agents` skill's **context pointer**, **leading word**, **completion criterion**, **cache**, **no-op**, **sediment**), has no entry.

## Language

### The set and its components

**skill set**:
Every skill directory under `mmw-v3/skills/`, with its references, playbooks, principles and scripts.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md`, opening paragraph

**component**:
One of the seven kinds of text in the skill set, each answering one question: **mode**, **playbook**, **principle**, **capability skill**, **reference**, **script**, **role and configuration**. A passage lives in the component whose question it answers.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**mode**:
The `SKILL.md` of the `mmw-mode` skill. The question it answers: which situation calls for what, which playbook a task takes, what an unattended session may decide, and how a woken session picks up.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**playbook**:
The steps of one kind of task from start to finish, one file under the `mmw-mode` skill's `playbooks/`, opening with its `###` title.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**route line**:
A line of the route table, the list under the mode's `## Playbooks`: it names a playbook, the tasks it takes, and its file.
_Home_: `mmw-v3/skills/mmw-mode/SKILL.md` `## Playbooks`

**principle**:
A judgement that holds across tasks and belongs to no single skill, one file under the `mmw-mode` skill's `principles/`, cited by its path `principles/principle-<slug>.md` and indexed by a line in the mode's `## Principles`. Not a skill.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**capability skill**:
A skill that does one thing and hands back its result, without knowing who calls it.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**reference**:
Material that belongs to one moment of the skill that owns it and means nothing outside that skill (a brief or prompt template, a template or example, a catalogue or checklist, the rules of one branch of that skill's work), in that skill's `references/`.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**script**:
A program that does what comes out the same on every run (state reads and writes, deliveries, checks), in the `scripts/` of the skill that owns it.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**role and configuration**:
Which role reads which playbook, on which model, and which event wakes it.
_Home_: `mmw-v3/skills/mmw-mode/references/components.md` `## The seven components`

**Memory record**:
One memory in Nowledge Mem, saved and found through the `memory-records` skill, which is not yet in v3.
_Home_: `mmw-v2/skills/memory-records/SKILL.md`

**user rule**:
One of the fifteen numbered rules in the user's own instructions, which the host loads into every session; cited as user rule 1 to user rule 15.
_Home_: `mmw-v3/skills/mmw-mode/SKILL.md` `## Principles`, **User rules.**

**fact**:
One of the seven numbered facts about how an agent uses a skill set, cited as fact 1 to fact 7.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `## What skill text is for`

**upstream skill**:
A skill kept in an upstream subtree, or adapted from one; its text changes only where the change alters what the agent does.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Upstream skills`

### Reviewing text

**task**:
One job an agent is entered into a skill to do; a skill entered in the middle of a bigger task is walked from its entry to its return.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md`, opening paragraph

**load**:
What a task reads: per step, the files opened, their words, the skills crossed, and the words read that the run did not use.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md` **Walk each task**

**finding**:
A defect a review establishes with its evidence and fixes; either a finding about **load** or a **failure finding**. There are no severity levels.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md`, opening paragraphs

**failure finding**:
A finding where the agent ends wrong or stuck, named with how it occurs in real use.
_Home_: `mmw-v3/skills/mmw-mode/playbooks/review-the-skill-set.md`, opening paragraphs

**moment**:
A point in a task that needs one coherent set of material and that a run may reach without the others.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Load and disclosure`

**jump**:
A step that needs a second file, of its own skill or another, after the agent has reached its moment.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Load and disclosure`

**fragment**:
A reference that every run of the task opens, or a moment split across files.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Load and disclosure`

**over-defense**:
Text or a mechanism that guards a path that does not occur.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Redundancy and bloat`

**hand-off**:
An edge A → B: skill or agent A leaves something that B reads or waits for.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Hand-offs`

**unguided choice**:
A point where the agent must choose and the text says nothing.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Hand-offs`

**start prompt**:
The prompt that starts an agent: built by a script, or written by a model from a template, a subagent's brief included.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `### Prompts written for other agents`

**fresh agent**:
An agent started with none of the writer's context, given only a trigger and a job, that does a task so its walk shows where the text makes it guess or stop.
_Home_: `mmw-v3/skills/mmw-mode/references/skill-set-rules.md` `## Verifying`
