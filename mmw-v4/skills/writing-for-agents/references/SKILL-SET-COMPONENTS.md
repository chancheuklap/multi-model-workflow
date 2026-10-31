# Skill-set components

Which kind of component a text in the skill set belongs in, when a new one is warranted, the shape of each, and what registers it in the same change. The checks every passage is held to are in [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md).

## The components and where they live

| Component | Where | Answers |
| --- | --- | --- |
| mode skill | `mmw-mode/SKILL.md` | The owner's way of working: what to use when, which component returns the requested result |
| playbook | `mmw-mode/playbooks/<name>.md` | How one kind of task is done, start to end |
| principle | `principle-<slug>/SKILL.md` | How to decide when a certain situation arises |
| skill | `<name>/SKILL.md` | How one thing is done, and what it hands back |
| reference | `<skill>/references/<file>.md` | Material one step needs |
| script | `<skill>/scripts/<file>` | The part a program can do or check |
| subagent | none shipped: a skill or playbook sends out its host's general-purpose subagent, with the prompt it writes | What a subagent a skill or playbook sends out is told, and what it returns |
| configuration | outside the skills (`~/.mmw/models.json`) | Which model each role runs on |
| user-level prompt | `mmw-v4/prompt/shared.md` | Who reads every reply: the facts about the owner; every session carries it, with or without the mode |

A skill's directory is symlinked whole into every host, so it holds only what the agent holding the skill, or one of its scripts, reads or runs: `SKILL.md`, its references, playbooks and assets, its scripts and the data they read, and the `agents/` file `SKILL-SET-RULES.md` `### Descriptions` allows. A test, a design note or a maintainer's record lives outside `mmw-v4/skills/`.

## The method

These hold for every component.

1. **Imitate pstack in content, not only in shape.** Before writing a component, read the upstream component of the same kind that does the closest job. Where an upstream text already covers what MMW needs, start from that text and merge MMW's specifics into it.
2. **Compare before you choose; pstack is not the default winner.** Before calling something missing from the set, read its entry in [`UPSTREAM.md`](UPSTREAM.md) and the departures in [`DESIGN-INTENTS.md`](DESIGN-INTENTS.md): a departure listed there is a decision, not a gap. Where both sides do one job, read both in full and keep the one that does more, or keep both when they do different jobs. A component only an upstream has, which nothing in MMW corresponds to, is not brought in until a task needs it, because it names other components. A sentence only an upstream has is a different case: it comes in when it overlaps and conflicts with nothing already in the set.
3. **Place each piece of text by these questions, not by what type of text it looks like.** Who needs it, at which moment? How many places use it? Does it change a decision? Can a mechanism (a script, a check, a hook) enforce it?
4. **The default is to edit an existing home or to delete, not to create.** A new component needs all three: "no existing skill is a real home, the pattern recurs, and the topic deserves its own skill" (pstack `reflect`). "When in doubt, delete. Keep only prose that changes a decision." (pstack `authoring-a-skill.md`).
5. **What can be a check is not written as prose.** Order of preference: architecture, types, a lint or check whose error names the fix, a test, and prose last (pstack `correct`). "Skill prose is for things mechanisms cannot enforce" (pstack `reflect`).
6. **Register in the same change.** A new playbook gets its route line in `mmw-mode/references/handling-a-request.md` `## Playbooks`; a new principle gets its index line in `## Principles`; a reference or script gets named, with its path or command, by the step that uses it; `python3 mmw-v4/tests/lib/check_wiring.py`, which every suite under `mmw-v4/tests/` but `lib` runs first, fails when one of these is missing or names something that is not there. A new skill needs no install entry: `mmw-v4/install.sh` installs every directory under `mmw-v4/skills/` that has a `SKILL.md`. Text brought in from anywhere else is named, with the repository that first wrote it and the commit it was read at, in the message of the commit that brings it in.
7. **What pstack does not say is labelled.** A placement that rests on an inference from pstack's examples says so, and goes to the owner.
8. **Bring in what the step needs, and check what it names.** Before copying a component, list every component its text names. A named component the set does not have, and the current step does not bring in, either costs the copy one sentence (dropped, and named in the commit message) or, when the copy depends on it, keeps the copy out until a step brings both.
9. **A correction covers its whole class.** When the owner corrects one placement, check everything brought in so far for the same mistake before reporting back.

## mode

The model to imitate, in content as well as shape, is `upstream/pstack/skills/poteto-mode/SKILL.md` (3,153 words, seven sections).

### What the mode is for

The owner's way of working: in what situation to use what, and which playbook a task follows. It is loaded once and stays in context for the rest of the session. Invoking the skill is the entry: its description, which every host scans at start, says to read it in full at the start of every session. No hook and no line in the user-level prompt tells a session to read it.

It is read in two layers, split by whether the session holds a request or an assignment. `SKILL.md` holds what every agent judges with and keeps all seven section headings below, in their order. `references/handling-a-request.md` holds what only a session holding a request uses, under the headings of the sections it holds a part of, and is read by a session whose first message names no file to follow. What to do is named by whoever sends an agent; which skill and which principle to use stays each agent's judgement, through the first layer.

### Frontmatter

- `name: mmw-mode`.
- `description`: what the mode is in one sentence, the instruction to read it in full at the start of every session, before anything else, and which session goes on to `references/handling-a-request.md`.

### The two rules that shape every section

1. **Sections are divided by the moment they are used, not by topic.** Choosing an entry for a new request or a recorded continuation, a situation arising mid-task, deciding whether to ask the owner, spawning a subagent, writing the reply, writing a comment.
2. **The mode names; other components hold the how.** A trigger names a skill, an index line names a principle, a route line names the component that returns the requested result. The mode carries full text only for what holds on every task and has no other home: Autonomy, Subagents, Writing the reply, Comments. "Cut ruthlessly. A mode skill is not a manual."

### Section by section

#### `## Non-negotiables`

- **Used:** at any moment of any task, as soon as the situation a line names arises, whichever playbook is running.
- **Content:** one line per trigger: `Situation → what to use`, where what to use is a skill, a playbook (with its path), or a reference.
- **When to add a line:** under the name that fits it. The situation can occur inside any playbook, so it cannot hang on one step ("Before commit", "Any prose surface"). A situation that belongs to one step of one playbook is written in that step instead. A situation a principle's index line already names gets no line here, unless the line adds an action the principle does not hold.

#### `## Principles`

- **Used:** the index is read when the mode loads; a principle's full text is read only when its condition arises and it is applied.
- **Content:** each index line holds three things: `**principle-<slug>**. Condition. One-sentence rule.`
- **When to add a line:** in the same change that adds the principle skill. When a principle is warranted is in `## principle` below.

This index is how a rule loads at the moment it applies: one line is always in context, the full text is read when the condition arises. No hook is needed for it.

#### `## Autonomy`

- **Used:** whenever the agent is deciding whether to act or to ask the owner first.

#### `## Subagents`

- **Used:** before spawning any subagent.

#### `## Writing the reply`

- **Used:** while writing every reply, and any comment the owner reads.

#### `## Comments`

- **Used:** while writing a code comment or any file's prose about the code.

#### `## Playbooks`

- **Used:** at the start of a task, to choose its route.
- **Content:** one route line per playbook, with direct skill routes for independently requested outputs: ``**Name.** What task it is, and how it differs from the playbook most easily confused with it. `playbooks/<file>.md`.``
- **When to add a line:** in the same change that adds the playbook file. Whether a playbook is warranted is in `## playbook` below.

## playbook

The models to imitate are the 23 files in `upstream/pstack/skills/poteto-mode/playbooks/`. Read `bug-fix.md` and `refactoring.md` before writing a first one.

### What a playbook is for

How one kind of task reaches its requested result: who is responsible, the steps, what is handed back. A usable preparation, diagnosis or plan can be that result; code merge is not every playbook's ending. A playbook is not a skill. It has no frontmatter, cannot be invoked by name, and is opened only through a route line in the `mmw-mode` skill's `references/handling-a-request.md` `## Playbooks`, a step of another playbook, or the start prompt of an agent sent to it.

### When a new playbook is warranted

- **A new kind of task appears whose deliverable differs from every existing playbook's.** The test is the `**You own …**` line and the `**Reply:**` line: if both would read the same as an existing playbook's, it is the same task, and that playbook is edited instead. pstack added Hillclimb beside Perf issue because one is "sustained" improvement of a metric and the other a "one-off fix" (commit `b64f02a`).
- **Not for a task that happens once.** A playbook is saved here because the same kind of task comes back.
- **Not for handing one thing to one skill.** Name the skill in a `## Non-negotiables` line or in a step.

In the same change as the new file: add its route line to the `mmw-mode` skill's `references/handling-a-request.md` `## Playbooks`. A playbook that starts a session role of its own adds that role as `## subagent` below says.

### The shape of the file, top to bottom

1. `### <Name>`: the title, identical to the name in the route line.
2. `**You own …**` in bold on the first line: what this run owns, and what goes to subagents.
3. One paragraph: the stance for the whole playbook, and how it differs from the playbook most easily confused with it.
4. Numbered steps, one action each. Each step names the skill, principle, reference or script it uses, by name or path. A principle is named on the step where it applies, including a step every run takes.
5. Optionally one paragraph of rules that hold across all the steps.
6. `**Reply:**` the content of the reply unique to this playbook. The rules every reply shares are in the `mmw-mode` skill's `references/handling-a-request.md` `## Writing the reply` and are not repeated here.

Ordinary code changes enter Develop a change for the missing preparation. Its result is an independent ticket or spec batch, written with the to-tickets and to-spec skills, then handed to One ticket or Run a night under the existing authority. Specialist methods return to their caller. Execution verification rules live in the method or product verification source and are invoked by the execution step that needs them, rather than found by position in a preparation playbook. Authoring or modifying a skill keeps its dedicated evidence, authorship and proof responsibilities; the relevant execution step reads the **mmw-mode** skill's `references/prove-skill-change.md`. A missing prerequisite returns to the caller instead of silently opening another task.

A judgement several steps point to may follow the steps as a section of its own, opened by its name in bold (To spec's **Seams**); the two largest pstack playbooks (Orchestrate, Multi-phase plan) split into `####` subsections instead. A playbook may name a step of another playbook ("Run **Authoring or modifying a skill** on the findings").

## principle

- **For:** one judgement that many tasks need. "One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle." (pstack `principle-encode-lessons-in-structure`). In pstack every principle is named by at least two files besides the mode's index.
- **Not for:** a judgement only one playbook needs (it stays in that playbook's step), or a repeated mistake a script can stop.
- **Loading:** the mode's `## Principles` holds one line per principle and is always in context once the mode loads; the full text is read only when the condition arises. This is how a rule loads at the moment it applies, without a hook.
- **Shape** (models: `upstream/pstack/skills/principle-*/SKILL.md`):
  - Frontmatter: `name: principle-<slug>`; `description` is the one sentence every skill reached only by name has: `Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.` A principle is reached through its line in the mode's index, so its condition and rule are written there and not in the description (pstack sets `disable-model-invocation: true` on principles for the same reason).
  - `# <Title>` and the rule in one or two sentences.
  - `**Why:**` one sentence.
  - The checkable practice, one point per bullet, under a label such as `**Pattern:**`, `**Rule:**` or `**The test:**`.
  - `**Stop:**` when to stop going further, where it applies.
  - A closing line separating it from the principle most easily confused with it, linking to that one.
- **Register:** its line in `mmw-mode/SKILL.md` `## Principles`, and its name on every step where it applies.

## skill

- **For:** one thing that recurs and that nothing else handles. "A workflow you keep hitting but isn't captured → propose a new skill." It is either used by many steps, or worth invoking directly.
- **Not for:** what an existing skill can hold. Edit that skill.
- **Shape** (models: `arena` and `how` under `upstream/pstack/skills/`):
  - Frontmatter: `name`, `description` (what it does, then `Use for …` or `Use when …` with the words someone would use), and `argument-hint` when the skill takes an argument the person types.
  - `# <Title>` and one paragraph: what it does and what it hands back.
  - When it sends out subagents, the prompt each is given, or the `references/` template it is built from; it names the subagent row to use (`mmw-mode/SKILL.md` `## Subagents`).
  - The phases or steps; a step that needs a template names `references/<file>`.
  - What it hands back, and in what form.
- **A skill the steps that make one kind of output name**, the way Opening a PR names **technical-writing** and **unslop**: it holds the rules that kind of output shares, and the step that names it says only what this output carries.

## reference

The model to imitate: `upstream/pstack/skills/how/references/explorer-prompt.md` (a prompt template).

### What a reference is for

Material that one step needs and the skill's main text does not: the prompt handed to a subagent, or a table consulted to make one kind of judgement. It is read when the step that names it runs, and not before.

A reference belongs to one skill and sits under its references/ directory. Branch documents and format guides live there; SKILL.md remains the entry. There is no directory of references shared across skills. The `mmw-mode` skill's `references/` directory holds what the mode's triggers and playbooks open.

### When a new reference is warranted

- **The material is used only on one branch, or only by one subagent.** `research` opens `references/explorer.md` or `references/investigator.md` only when its start prompt has it follow that file, and an investigator reads only the `references/sources/<source>.md` of its category.
- **Several playbooks or triggers open the same material.** That is still a reference.
- **Not for material every invocation uses.** That goes in the skill file itself: "Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time."

In the same change: the step or trigger that opens it names its path.

### The shape of the file

- **A prompt template:** a title, one or two sentences on what the template is and how to fill it, then the full prompt with placeholders in braces (`{QUESTION}`).
- **A lookup table:** a title, what judgement it serves, then the table or the decision rules.

## script

The models to imitate: `upstream/pstack/skills/poteto-mode/scripts/worktree-audit.sh` (a small read-only program) and `upstream/pstack/skills/poteto-mode/scripts/orch/` (a larger one with tests).

### What a script is for

The part of the work that comes out the same every time and that a program can do or check. The agent runs it and reads its output; judgement stays with the agent.

### When a new script is warranted

- **An instruction is about to be written a second time** (pstack's `principle-encode-lessons-in-structure`, `upstream/pstack/skills/principle-encode-lessons-in-structure/SKILL.md`): "If the fix is structural, only use the structural fix. The instruction is the symptom."
- **The work is not done at a glance** (pstack's `principle-build-the-lever`, `upstream/pstack/skills/principle-build-the-lever/SKILL.md`): "The tool is the artifact a reviewer can rerun."
- **A repeated mistake can be made impossible** (pstack's `correct` skill's order, `upstream/pstack/skills/correct/SKILL.md`: architecture, then types, then a lint or CI check whose error names the fix, then a test; prose last). A check is proven by making it fail on a real past mistake.
- **Not for a decision that needs judgement.** That stays in prose: written prominently, with an example of the failure.

In the same change: the step or trigger that runs it gives the exact command.

### The shape of the file

- A header comment: what the program does, and what it never does ("Never deletes anything; deletion stays a human-gated step in the playbook").
- Ordinary code, written by the principles (`mmw-mode` `## Principles`) and checked by the repository's `scripts/check`.
- Tests beside the larger programs.

## subagent

- **What there is:** MMW ships no subagent definitions (ADR 0015).
- **Which kind a new agent is:** three questions, in order. Can the session do the work itself in this turn, where its own reading is good enough: then no agent. Does the work need a model of its own, or to run outside this turn, or is it a different job from the sender's: then a session role. Otherwise (several pieces of the same job at once, or a context the session's own reasoning has not touched): a subagent. Every session role has a row in the `dispatch` skill's `roles.json`, which carries its `default` host, model and effort; `check-interfaces.py` beside `dispatch.sh` refuses a role without a default a fresh machine can start, a `send` of a role `roles.json` does not have, and a brief role nothing sends. A subagent has no `default` like a session role. Its model comes from the subagent row the sending step names, registered in the `dispatch` skill's `roles.json` `subagents` section. Its prompt is written in that step or, when it is long, in the sending skill's `references/`.

## configuration

- **For:** a choice that differs per person or machine and must hold in every session, such as the host, model and reasoning effort of each role a script starts (junior and senior worker, reviewer, researcher, candidate, retro-analyst, advisor). The defaults are each role's `default` in the `dispatch` skill's `roles.json`, which the installer writes when a machine has no `models.json`, or has one without that role's row; a start whose role has no row is refused, naming the row.
- **Not for:** text in the mode or a skill.
- MMW's is `~/.mmw/models.json`, changed only through `models.py`.

## user-level prompt

- **For:** what holds in every session, the mode loaded or not: the facts about the owner who reads every reply.
- **Not for:** anything the mode, a principle or a skill holds. Which decisions only the owner makes is **principle-never-block-on-the-human**'s, and the mode's `## Autonomy` points there.
