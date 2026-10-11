# Skill-set components

Which kind of component a text in the skill set belongs in, when a new one is warranted, the shape of each, and what registers it in the same change. The checks every passage is held to are in [`SKILL-SET-RULES.md`](SKILL-SET-RULES.md).

## The components and where they live

| Component | Where | Answers |
| --- | --- | --- |
| mode skill | `mmw-mode/SKILL.md` | The owner's way of working: what to use when, which playbook a task follows |
| playbook | `mmw-mode/playbooks/<name>.md` | How one kind of task is done, start to end |
| principle | `principle-<slug>/SKILL.md` | How to decide when a certain situation arises |
| skill | `<name>/SKILL.md` | How one thing is done, and what it hands back |
| reference | `<skill>/references/<file>.md` | Material one step needs |
| script | `<skill>/scripts/<file>` | The part a program can do or check |
| subagent | none shipped: a skill or playbook sends out its host's general-purpose subagent, with the prompt it writes | What a subagent a skill or playbook sends out is told, and what it returns |
| configuration | outside the skills (`~/.mmw/models.json`) | Which model each role runs on |
| user-level prompt | `mmw-v4/prompt/shared.md` | Who reads every reply: the facts about the owner; every session carries it, with or without the mode |

## The method

These hold for every component. They come from how pstack itself adds and changes components (course lesson 2) and from what went wrong in the two earlier attempts.

1. **Imitate pstack in content, not only in shape.** Before writing a component, read the pstack component of the same kind that does the closest job. Where a pstack text already covers what MMW needs (a principle, a section of poteto-mode, a skill), start from that text and merge MMW's specifics into it. A file with pstack's headings and MMW's old text under them is not a migration.
2. **Compare before you choose; pstack is not the default winner.** Before calling something missing from the set, read its entry in [`UPSTREAM-INTENTS.md`](UPSTREAM-INTENTS.md) and the departures in [`DESIGN-INTENTS.md`](DESIGN-INTENTS.md): a departure listed there is a decision, not a gap. When v2 and pstack each have a component doing the same job, read both in full and keep the one that does more, or keep both when they do different jobs. Several v2 skills do more than their pstack counterpart (`writing-for-agents` in the place of Cursor's `create-skill`, `grilling`, which pstack has no counterpart for). Compare components, not only skills: the pstack side of a job can be a playbook (pstack writes how a skill is made in its Authoring a skill playbook; Cursor's `create-skill` is only the tool its first step names). A component only pstack has, which nothing in MMW corresponds to, is not brought in until a task needs it, because it names other components. A sentence only pstack has is a different case: it comes in when it overlaps and conflicts with nothing already in the set. The comparisons made so far are in `mmw-v3/course/` lesson 4, figure 3; where every rule of `shared.md`, and every pstack communication rule merged with MMW's, goes is in figures 4 and 5.
3. **Place each piece of text by these questions, not by what type of text it looks like.** Who needs it, at which moment? How many places use it? Does it change a decision? Can a mechanism (a script, a check, a hook already in v2) enforce it? The two earlier attempts placed text by type ("move each passage to the layer its type belongs to") and produced one situation with two different actions in two places (#880), the same rule written twice (#884) and references to things that had moved (#885). A v2 file is not one unit either. A v2 skill can carry the steps of a task, rules several steps read, and the capability itself, and each part goes where these questions put it: v2's `writing-for-agents` became the playbook Authoring or modifying a skill (its steps), `writing-for-agents/SKILL-SET-RULES.md` (the rules it reads) and a skill (the capability). Text from the earlier attempts may be the base where it is more complete than pstack's; their placement rules are followed only where lesson 2 found them agreeing with pstack.
4. **The default is to edit an existing home or to delete, not to create.** A new component needs all three: "no existing skill is a real home, the pattern recurs, and the topic deserves its own skill" (pstack `reflect`). "When in doubt, delete. Keep only prose that changes a decision." (pstack `authoring-a-skill.md`).
5. **What can be a check is not written as prose.** Order of preference: architecture, types, a lint or check whose error names the fix, a test, and prose last (pstack `correct`). "Skill prose is for things mechanisms cannot enforce" (pstack `reflect`).
6. **Register in the same change.** A new playbook gets its route line in `mmw-mode/SKILL.md` `## Playbooks`; a new principle gets its index line in `## Principles`; a reference or script gets named, with its path or command, by the step that uses it; `python3 mmw-v4/tests/lib/check_wiring.py`, which every suite under `mmw-v4/tests/` but `lib` runs first, fails when one of these is missing or names something that is not there. A new skill needs no install entry: `mmw-v4/install.sh` installs every directory under `mmw-v4/skills/` that has a `SKILL.md`. Text brought in from anywhere else is named, with the repository that first wrote it and the commit it was read at, in the message of the commit that brings it in.
7. **What pstack does not say is labelled.** pstack has no written rule for some decisions (when a new playbook is warranted, for one). A placement that rests on an inference from pstack's examples says so, and goes to the owner.
8. **Bring in what the step needs, and check what it names.** Before copying a component, list every component its text names. A named component the set does not have, and the current step does not bring in, either costs the copy one sentence (dropped, and named in the commit message) or, when the copy depends on it, keeps the copy out until a step brings both. The base of a copy is v2's version, which carries the owner's improvements; a v2 sentence that ties it to something the set does not have (a skill, a command, a script) is dropped.
9. **A correction covers its whole class.** When the owner corrects one placement, check everything brought in so far for the same mistake before reporting back.

## mode

The model to imitate, in content as well as shape, is `mmw-v3/upstream-pstack/skills/poteto-mode/SKILL.md` (2,971 words, seven sections).

### What the mode is for

The owner's way of working: in what situation to use what, and which playbook a task follows. It is loaded once and stays in context for the rest of the session. Invoking the skill is the entry: its description, which every host scans at start, says to read it in full at the start of every session. An agent that is sent is also told so in its first words: a start prompt `dispatch.sh` writes is its data, then `Read the mmw-mode skill in full, then follow <what>.` (`Dispatched: <role>, ticket #<n>, base <commit>. Read …`, or `Dispatched: <role>, brief <file>. Read …`), then `It is your whole task: what came before it is done, and you start no agent it does not name.`; a subagent's prompt opens with `Read the mmw-mode skill in full, then` and ends with that same sentence. The mode's `## Non-negotiables` opens with what that sentence changes. No hook and no line in the user-level prompt tells a session to read it.

### Frontmatter

- `name: mmw-mode`.
- `description`: what the mode is in one sentence, then the instruction to read it in full at the start of every session, before anything else.

poteto-mode's `mode`, `reminder`, `icon` and `color` are Cursor fields and are left out.

### The two rules that shape every section

1. **Sections are divided by the moment they are used, not by topic.** Choosing a route at the start of a task, a situation arising mid-task, deciding whether to ask the owner, spawning a subagent, writing the reply, writing a comment.
2. **The mode names; other components hold the how.** A trigger names a skill, an index line names a principle, a route line names a playbook. The mode carries full text only for what holds on every task and has no other home: Autonomy, Subagents, Writing the reply, Comments. "Cut ruthlessly. A mode skill is not a manual."

### Section by section

#### `## Non-negotiables`

- **Used:** at any moment of any task, as soon as the situation a line names arises, whichever playbook is running.
- **Content:** first, **An agent that was sent**: the sentence that ends every sent agent's prompt outranks `## Playbooks`, the group **The task as a whole**, and the principles that send work to another agent, because those belong to the sender, who owns the whole task; it names the group, never its lines. Then one paragraph saying that the Principles section grounds every trigger (a principle's index line is itself a trigger), and that the reply names each principle that shaped a decision and the choice it changed, citing only principles whose full `SKILL.md` was read this session. Then the triggers in two groups, each under its bold name as `## Principles` groups its entries: **The task as a whole**, for what produces something about the whole task (an understanding, a design, a split, a review, a record), which one session does once; and **Your own code and prose**, for what governs each line an agent writes itself. One line per trigger: `Situation → what to use`, where what to use is a skill, a playbook (with its path), or a reference. A line names; it does not explain how. The exception is a judgement that must be made on the spot, written into the line (poteto-mode's "classify it before you ask" line).
- **When to add a line:** it goes in the group its product puts it in. The situation can occur inside any playbook, so it cannot hang on one step ("Before commit", "Any prose surface"). A situation that belongs to one step of one playbook is written in that step instead. A situation a principle's index line already names gets no line here, unless the line adds an action the principle does not hold (poteto-mode's "Any code → name the data shape first").

#### `## Principles`

- **Used:** the index is read when the mode loads; a principle's full text is read only when its condition arises and it is applied.
- **Content:** two sentences of usage ("Read the leaf skill in full for any principle you apply. Each entry names when it applies."), then the index in named groups (poteto-mode: Core, Architecture, Verification, Delegation, Meta). Each line holds three things: `**Name** (**principle-<slug>**). Condition. One-sentence rule.` The full text lives in `mmw-v4/skills/principle-<slug>/SKILL.md`, never in the mode.
- **When to add a line:** in the same change that adds the principle skill. When a principle is warranted is in `## principle` below.

This index is how a rule loads at the moment it applies: one line is always in context, the full text is read when the condition arises. No hook is needed for it.

#### `## Autonomy`

- **Used:** whenever the agent is deciding whether to act or to ask the owner first.
- **Content:** six paragraphs, each opening in bold:
  - **Just do it.** What proceeds without asking: reversible work; a decision only the owner makes is not taken, and its list is in **principle-never-block-on-the-human**.
  - **Two kinds of moment.** A question asked in discussion is answered, not acted on; an instruction to act is carried out.
  - **Always pause** for irreversible writes, and on correctness, security and money.
  - **Session overrides:** what the owner's words change ("going to bed"; an approved plan or ticket is the go signal).
  - **Unattended.** How a session whose start prompt is a `Dispatched:` line works with nobody to ask: by the file its start prompt names, and what replaces asking. It is the only text such a session relies on for working unwatched; the start prompt itself carries no rule, only that pointer.
  - **No is an acceptable answer.** Disagreement is owed when there is a flaw, never manufactured.

#### `## Subagents`

- **Used:** before spawning any subagent.
- **Content:** one paragraph each: how to send a session with `dispatch.sh send` and what a brief holds; how to send a host's general-purpose subagent, with no model named, and what to do on a host that cannot run one; that a subagent's prompt opens with reading the mode and ends with the sentence that makes it its whole task; when to ask the advisor for a second opinion; who owns what comes back; fresh subagents by default. Every subagent in MMW is sent out by a skill or a playbook, which writes its prompt (an axis of `code-review`, the judge of `arena`, the ambiguity scanner of To tickets); every subagent reads this mode first. Sessions a script starts (junior and senior worker, reviewer, researcher, candidate, advisor) are not subagents; their start and their models are the `dispatch` skill's, and its `roles.json` lists every session role.

#### `## Writing the reply`

- **Used:** while writing every reply.
- **Content:** the rules every reply shares, one point per bullet, each stated as an action: evidence or its label in the same sentence; reasons and consequences rather than files and functions; plain standard vocabulary; when lists and tables help. A rule's reason stands beside it. Who reads the reply and what they can and cannot see are facts about the owner, in `mmw-v4/prompt/shared.md`, which every session carries with or without the mode; what the owner learns from a reply (principle and effect) opens this section. Anchored references are `principle-anchor-every-reference`'s. Close with the division of labour: each playbook's `**Reply:**` line names only what is unique to that playbook.

#### `## Comments`

- **Used:** while writing a code comment or any file's prose about the code.
- **Content:** one paragraph. A comment is kept only for a non-obvious why the code cannot show. That a file describes its subject now, never its own history, is `principle-files-describe-the-present`'s, and holds for comments too.

#### `## Playbooks`

- **Used:** at the start of a task, to choose its route.
- **Content, in this order:**
  1. Usage: match the task to a route line and open its playbook.
  2. One sentence for a task no route line matches: it goes to `figure-it-out`, as in poteto-mode.
  3. One sentence that sends a ticket with acceptance criteria, given anywhere but to a worker, to **One ticket** of Run a night.
  4. One route line per playbook: ``**Name.** What task it is, and how it differs from the playbook most easily confused with it. `playbooks/<file>.md`.`` A session a script started finds its route line by its start prompt, so that line opens with what the `dispatch` skill sent it with (Work a ticket: "Sent by the dispatch skill to a ticket").
- **When to add a line:** in the same change that adds the playbook file. Whether a playbook is warranted is in `## playbook` below.

## playbook

The models to imitate are the 23 files in `mmw-v3/upstream-pstack/skills/poteto-mode/playbooks/`. Read `bug-fix.md` and `refactoring.md` before writing a first one.

### What a playbook is for

How one kind of task is done from start to end: who owns what, the steps, what is handed back. A playbook is not a skill. It has no frontmatter, cannot be invoked by name, and is opened only through a route line in the `mmw-mode` skill's `SKILL.md` `## Playbooks` or a step of another playbook.

### When a new playbook is warranted

- **A new kind of task appears whose deliverable differs from every existing playbook's.** The test is the `**You own …**` line and the `**Reply:**` line: if both would read the same as an existing playbook's, it is the same task, and that playbook is edited instead. pstack added Hillclimb beside Perf issue because one is "sustained" improvement of a metric and the other a "one-off fix" (commit `b64f02a`).
- **Not for a task that happens once.** A playbook is saved here because the same kind of task comes back.
- **Not for handing one thing to one skill.** Name the skill in a `## Non-negotiables` line or in a step.

In the same change as the new file: add its route line to the `mmw-mode` skill's `SKILL.md` `## Playbooks`. A playbook that starts a session role of its own adds that role as `## subagent` below says.

### The shape of the file, top to bottom

1. `### <Name>`: the title, identical to the name in the route line.
2. `**You own …**` in bold on the first line: what this run owns, and what goes to subagents.
3. One paragraph: the stance for the whole playbook, and how it differs from the playbook most easily confused with it.
4. Numbered steps, one action each. Each step names the skill, principle, reference or script it uses, by name or path. A principle is named on the step where it applies, including a step every run takes.
5. Optionally one paragraph of rules that hold across all the steps.
6. `**Reply:**` the content of the reply unique to this playbook. The rules every reply shares are in the `mmw-mode` skill's `SKILL.md` `## Writing the reply` and are not repeated here.

A judgement several steps point to may follow the steps as a section of its own, opened by its name in bold (To spec's **Seams**); the two largest pstack playbooks (Orchestrate, Multi-phase plan) split into `####` subsections instead. A playbook may name a step of another playbook ("Run **Authoring or modifying a skill** on the findings").

## principle

- **For:** one judgement that many tasks need. "One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle." (pstack `principle-encode-lessons-in-structure`). In pstack every principle is named by at least two files besides the mode's index.
- **Not for:** a judgement only one playbook needs (it stays in that playbook's step), or a repeated mistake a script can stop.
- **Loading:** the mode's `## Principles` holds one line per principle and is always in context once the mode loads; the full text is read only when the condition arises. This is how a rule loads at the moment it applies, without a hook.
- **Shape** (models: `mmw-v3/upstream-pstack/skills/principle-*/SKILL.md`):
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
- **Shape** (models: `swarm`, `how`, `figure-it-out` under `mmw-v3/upstream-pstack/skills/`):
  - Frontmatter: `name`, `description` (what it does, then `Use for …` or `Use when …` with the words someone would use), and `argument-hint` when the skill takes an argument the person types.
  - `# <Title>` and one paragraph: what it does and what it hands back.
  - When it sends out subagents, the prompt each is given, or the `references/` template it is built from; it names no model (`mmw-mode/SKILL.md` `## Subagents`).
  - The phases or steps; a step that needs a template names `references/<file>`.
  - What it hands back, and in what form.

## reference

The models to imitate: `mmw-v3/upstream-pstack/skills/how/references/explorer-prompt.md` (a prompt template) and `mmw-v3/upstream-pstack/skills/poteto-mode/references/bugbot-triage.md` (a lookup table).

### What a reference is for

Material that one step needs and the skill's main text does not: the prompt handed to a subagent, or a table consulted to make one kind of judgement. It is read when the step that names it runs, and not before.

A reference belongs to one skill and sits under it. There is no directory of references shared across skills. The `mmw-mode` skill's `references/` directory holds what the mode's triggers and playbooks open.

### When a new reference is warranted

- **The material is used only on one branch, or only by one subagent.** `research` opens `references/explorer.md` or `references/investigator.md` only when its start prompt has it follow that file, and an investigator reads only the `references/sources/<source>.md` of its category.
- **Several playbooks or triggers open the same material.** That is still a reference. `bugbot-triage.md` is opened by a playbook and a `## Non-negotiables` line.
- **Not for material every invocation uses.** That goes in the skill file itself: "Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time."

In the same change: the step or trigger that opens it names its path.

### The shape of the file

- **A prompt template:** a title, one or two sentences on what the template is and how to fill it, then the full prompt with placeholders in braces (`{QUESTION}`).
- **A lookup table:** a title, what judgement it serves, then the table or the decision rules.

## script

The models to imitate: `mmw-v3/upstream-pstack/skills/poteto-mode/scripts/worktree-audit.sh` (a small read-only program) and `mmw-v3/upstream-pstack/skills/poteto-mode/scripts/orch/` (a larger one with tests).

### What a script is for

The part of the work that comes out the same every time and that a program can do or check. The agent runs it and reads its output; judgement stays with the agent.

### When a new script is warranted

- **An instruction is about to be written a second time** (pstack's `principle-encode-lessons-in-structure`, `mmw-v3/upstream-pstack/skills/principle-encode-lessons-in-structure/SKILL.md`): "If the fix is structural, only use the structural fix. The instruction is the symptom."
- **The work is not done at a glance** (pstack's `principle-build-the-lever`, `mmw-v3/upstream-pstack/skills/principle-build-the-lever/SKILL.md`): "The tool is the artifact a reviewer can rerun."
- **A repeated mistake can be made impossible** (pstack's `correct` skill's order, `mmw-v3/upstream-pstack/skills/correct/SKILL.md`: architecture, then types, then a lint or CI check whose error names the fix, then a test; prose last). A check is proven by making it fail on a real past mistake.
- **Not for a decision that needs judgement.** That stays in prose: written prominently, with an example of the failure.

In the same change: the step or trigger that runs it gives the exact command.

### The shape of the file

- A header comment: what the program does, and what it never does ("Never deletes anything; deletion stays a human-gated step in the playbook").
- Ordinary code under `CODING_STANDARDS.md` at the repository root.
- Tests beside the larger programs.

## subagent

- **What there is:** MMW ships no subagent definitions (ADR 0015). A skill that needs one sends out its host's general-purpose subagent, on the session's own model, and writes its whole prompt, usually from a template in the skill's `references/` (each `code-review` axis is its axis file with the ticket and base commit written in). Its prompt opens with `Read the mmw-mode skill in full, then`, so it works under the same rules as the session that sent it, and ends with `It is your whole task: …`, so the triggers that work on the task as a whole stay with that session; past the mode, it reads only what the skill gives it. The rules every such dispatch follows are `mmw-mode/SKILL.md` `## Subagents`.
- **Not a subagent:** a session a script starts. Every one is started by the `dispatch` skill's `dispatch.sh send <role> <ticket number>` or `dispatch.sh send <role> --follow "<what>" <brief file>`, as a session of its own on the row `~/.mmw/models.json` gives its role: a worker or reviewer with a ticket number, a researcher, candidate or advisor with a brief. Its start prompt is one line: its data, then `Read the mmw-mode skill in full, then follow <what>. It is your whole task: …`, <what> being its role's `follows` in `roles.json` for a ticket, or the `--follow` the sending step writes for a brief. It matches no route line. A briefed session reports its answer with `dispatch.sh report`, and the relay wakes the session that sent the brief once the whole batch has reported.
- **Which kind a new agent is:** three questions, in order. Can the session do the work itself in this turn, where its own reading is good enough: then no agent. Does the work need a model of its own, or to run outside this turn, or is it a different job from the sender's: then a session role. Otherwise (several pieces of the same job at once, or a context the session's own reasoning has not touched): a subagent. Every session role has a row in the `dispatch` skill's `roles.json` and a default row in `hosts.json`; `check-interfaces.py` beside `dispatch.sh` refuses a role without both rows, a `send` of a role `roles.json` does not have, and a brief role nothing sends. A subagent has no row: it is the prompt the sending step writes, in the text of that step or, when it is long, in the sending skill's `references/`.
- pstack's `poteto-agent` exists because a general subagent skips reading the mode: "Substituting `generalPurpose` skips that read and drifts." MMW has no definition file for it: every prompt that starts an agent, subagent or session, opens with reading the mode, on any host.

## configuration

- **For:** a choice that differs per person or machine and must hold in every session, such as the host, model and reasoning effort of each role a script starts (junior and senior worker, reviewer, researcher, candidate, advisor). The defaults are the `defaults` of the `dispatch` skill's `hosts.json`, which the installer writes when a machine has no `models.json`; a start whose role has no row is refused, naming the row.
- **Not for:** text in the mode or a skill.
- MMW's is `~/.mmw/models.json`, changed only through `models.py`.

## user-level prompt

- **For:** what holds in every session, the mode loaded or not: the facts about the owner who reads every reply.
- **Not for:** anything the mode, a principle or a skill holds. Which decisions only the owner makes is **principle-never-block-on-the-human**'s, and the mode's `## Autonomy` points there.
