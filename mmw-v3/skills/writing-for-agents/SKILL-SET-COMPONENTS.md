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
| user-level prompt | `mmw-v3/prompt/shared.md` | Who reads every reply, and which decisions only the owner makes; every session carries it, with or without the mode |

## The method

These hold for every component. They come from how pstack itself adds and changes components (course lesson 2) and from what went wrong in the two earlier attempts.

1. **Imitate pstack in content, not only in shape.** Before writing a component, read the pstack component of the same kind that does the closest job. Where a pstack text already covers what MMW needs (a principle, a section of poteto-mode, a skill), start from that text and merge MMW's specifics into it. A file with pstack's headings and MMW's old text under them is not a migration.
2. **Compare before you choose; pstack is not the default winner.** When v2 and pstack each have a component doing the same job, read both in full and keep the one that does more, or keep both when they do different jobs. Several v2 skills do more than their pstack counterpart (`wait-what` over `bro`, `writing-for-agents` in the place of Cursor's `create-skill`, `grilling`, which pstack has no counterpart for). Compare components, not only skills: the pstack side of a job can be a playbook (pstack writes how a skill is made in its Authoring a skill playbook; Cursor's `create-skill` is only the tool its first step names). A component only pstack has, which nothing in MMW corresponds to, is not brought in until a task needs it, because it names other components. A sentence only pstack has is a different case: it comes in when it overlaps and conflicts with nothing already in v3. The comparisons made so far are in `mmw-v3/course/` lesson 4, figure 3; where every rule of `shared.md`, and every pstack communication rule merged with MMW's, goes is in figures 4 and 5.
3. **Place each piece of text by these questions, not by what type of text it looks like.** Who needs it, at which moment? How many places use it? Does it change a decision? Can a mechanism (a script, a check, a hook already in v2) enforce it? The two earlier attempts placed text by type ("move each passage to the layer its type belongs to") and produced one situation with two different actions in two places (#880), the same rule written twice (#884) and references to things that had moved (#885). A v2 file is not one unit either. A v2 skill can carry the steps of a task, rules several steps read, and the capability itself, and each part goes where these questions put it: v2's `writing-for-agents` became the playbooks Authoring or modifying a skill and Review the skill set (its steps), `writing-for-agents/SKILL-SET-RULES.md` (the rules both read) and a skill (the capability). Text from the earlier attempts may be the base where it is more complete than pstack's; their placement rules are followed only where lesson 2 found them agreeing with pstack.
4. **The default is to edit an existing home or to delete, not to create.** A new component needs all three: "no existing skill is a real home, the pattern recurs, and the topic deserves its own skill" (pstack `reflect`). "When in doubt, delete. Keep only prose that changes a decision." (pstack `authoring-a-skill.md`).
5. **What can be a check is not written as prose.** Order of preference: architecture, types, a lint or check whose error names the fix, a test, and prose last (pstack `correct`). "Skill prose is for things mechanisms cannot enforce" (pstack `reflect`).
6. **Register in the same change.** A new playbook gets its route line in `mmw-mode/SKILL.md` `## Playbooks`; a new principle gets its index line in `## Principles`; a reference or script gets named, with its path or command, by the step that uses it; `python3 mmw-v3/tests/lib/check_wiring.py`, which every test suite runs first, fails when one of these is missing or names something that is not there. A new skill needs no install entry: `mmw-v3/install.sh` installs every directory under `mmw-v3/skills/` that has a `SKILL.md`. Text brought in from anywhere else gets its row in `mmw-v3/imports.tsv`, traced to the repository that first wrote it, and `python3 mmw-v3/check_imports.py` passes.
7. **What pstack does not say is labelled.** pstack has no written rule for some decisions (when a new playbook is warranted, for one). A placement that rests on an inference from pstack's examples says so, and goes to the owner.
8. **Bring in what the step needs, and check what it names.** Before copying a component, list every component its text names. A named component the set does not have, and the current step does not bring in, either costs the copy one sentence (dropped, and listed in the copy's row) or, when the copy depends on it, keeps the copy out until a step brings both. The base of a copy is v2's version, which carries the owner's improvements; a v2 sentence that ties it to v2's pipeline (a ticket's `CHECK:` line, `models.py`, a skill the set does not have) is dropped.
9. **A correction covers its whole class.** When the owner corrects one placement, check everything brought in so far for the same mistake before reporting back.

## mode

The model to imitate, in content as well as shape, is `mmw-v3/upstream-pstack/skills/poteto-mode/SKILL.md` (2,971 words, seven sections).

### What the mode is for

The owner's way of working: in what situation to use what, and which playbook a task follows. It is loaded once and stays in context for the rest of the session. Three routes load it: the person types `/mmw-mode`; `scripts/mode-hook.py`, which `install.sh` registers at SessionStart on Claude Code and Codex, tells a session in a repository with `.mmw/` to read `SKILL.md`; the start prompt `dispatch.sh` gives a worker or reviewer opens with the same instruction and the file's path.

The hook and the start prompt tell a session to read the file rather than to use the skill, so that the mode is read whether or not the model would load it on its own.

### Frontmatter

- `name: mmw-mode`.
- `description`: the style in one phrase and the triggers (the start of any task in a repository with `.mmw/`, `/mmw-mode`).

poteto-mode's `mode`, `reminder`, `icon` and `color` are Cursor fields and are left out.

### The two rules that shape every section

1. **Sections are divided by the moment they are used, not by topic.** Choosing a route at the start of a task, a situation arising mid-task, deciding whether to ask the owner, spawning a subagent, writing the reply, writing a comment.
2. **The mode names; other components hold the how.** A trigger names a skill, an index line names a principle, a route line names a playbook. The mode carries full text only for what holds on every task and has no other home: Autonomy, Subagents, Writing the reply, Comments. "Cut ruthlessly. A mode skill is not a manual."

### Section by section

#### `## Non-negotiables`

- **Used:** at any moment of any task, as soon as the situation a line names arises, whichever playbook is running.
- **Content:** one opening paragraph saying that the Principles section grounds every trigger (a principle's index line is itself a trigger), and that the reply names each principle that shaped a decision and the choice it changed, citing only principles whose full `SKILL.md` was read this session. Then one line per trigger: `Situation → what to use`, where what to use is a skill, a playbook (with its path), or a reference. A line names; it does not explain how. The exception is a judgement that must be made on the spot, written into the line (poteto-mode's "classify it before you ask" line).
- **When to add a line:** the situation can occur inside any playbook, so it cannot hang on one step ("Before commit", "Any prose surface"). A situation that belongs to one step of one playbook is written in that step instead. A situation a principle's index line already names gets no line here, unless the line adds an action the principle does not hold (poteto-mode's "Any code → name the data shape first").

#### `## Principles`

- **Used:** the index is read when the mode loads; a principle's full text is read only when its condition arises and it is applied.
- **Content:** two sentences of usage ("Read the leaf skill in full for any principle you apply. Each entry names when it applies."), then the index in named groups (poteto-mode: Core, Architecture, Verification, Delegation, Meta). Each line holds three things: `**Name** (**principle-<slug>**). Condition. One-sentence rule.` The full text lives in `mmw-v3/skills/principle-<slug>/SKILL.md`, never in the mode.
- **When to add a line:** in the same change that adds the principle skill. When a principle is warranted is in `## principle` below.

This index is how a rule loads at the moment it applies: one line is always in context, the full text is read when the condition arises. No hook is needed for it.

#### `## Autonomy`

- **Used:** whenever the agent is deciding whether to act or to ask the owner first.
- **Content:** five paragraphs, each opening in bold, the first four as in poteto-mode:
  - **Just do it.** What proceeds without asking: reversible work, engineering decisions, and any fact you could observe by running something (behaviour, timing, layout, output), which is found by running it, not asked.
  - **Always pause** for what only the owner decides (the list is in the user-level prompt, which every session loads) and for irreversible writes.
  - **Session overrides:** what the owner's words change ("going to bed"; an approved plan or ticket is the go signal).
  - **No is an acceptable answer.** Disagreement is owed when there is a flaw, never manufactured.
  - **Unattended.** How a session a script started works with nobody to ask: which of the four paragraphs above hold for it, and what replaces asking. It is the only text a start prompt relies on for working unwatched; the start prompt itself carries no rule (lesson 5, decision 5).

#### `## Subagents`

- **Used:** before spawning any subagent.
- **Content:** the rules for a subagent a skill or playbook sends out from inside a session, one paragraph each: which subagent to use and on which model; that work needing a model of its own is a session role; what its brief states; what to do on a host that cannot run one; who owns what it returns. Every subagent in MMW is sent out by a skill or a playbook, which writes its prompt (an axis of `code-review`, the fact-finder of `grilling`, the ambiguity scanner of Cut tickets); no subagent loads this mode. Sessions a script starts (worker, reviewer, advisor, researcher, explainer, synthesizer) are not subagents; their start and their models are the `dispatch` skill's, and its `roles.json` lists every role of both kinds.

#### `## Writing the reply`

- **Used:** while writing every reply.
- **Content:** the rules every reply shares, one point per bullet, each stated as an action: evidence or its label in the same sentence; reasons and consequences rather than files and functions; plain standard vocabulary; when lists and tables help. A rule's reason stands beside it. Who reads the reply and what they can and cannot see are facts about the owner, in `mmw-v3/prompt/shared.md`, which every session carries with or without the mode. Anchored references are `principle-anchor-every-reference`'s. Close with the division of labour: each playbook's `**Reply:**` line names only what is unique to that playbook.

#### `## Comments`

- **Used:** while writing a code comment or any file's prose about the code.
- **Content:** one paragraph. A comment is kept only for a non-obvious why the code cannot show. That a file describes its subject now, never its own history, is `principle-files-describe-the-present`'s, and holds for comments too.

#### `## Playbooks`

- **Used:** at the start of a task, to choose its route.
- **Content, in this order:**
  1. Usage: match the task to a route line and open its playbook.
  2. One route line per playbook: ``**Name.** What task it is, and how it differs from the playbook most easily confused with it. `playbooks/<file>.md`.``
  3. One sentence for a session a script started: the playbook its start prompt names is its route, chosen by whoever dispatched it (`mmw-v3/course/` lesson 5, decision 3).
  4. One sentence for a task no route line matches (poteto-mode sends it to `figure-it-out`, which MMW does not carry).
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

A judgement several steps point to may follow the steps as a section of its own, opened by its name in bold (Run a night's **Routing a finding**); the two largest pstack playbooks (Orchestrate, Multi-phase plan) split into `####` subsections instead. A playbook may name a step of another playbook ("Run **Authoring or modifying a skill** on the findings").

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

- **The material is used only on one branch, or only by one subagent.** `research` opens `references/explorer.md` or `references/investigator.md` only on the branch its brief calls for, and an investigator reads only the `references/sources/<source>.md` of its category.
- **Several playbooks or triggers open the same material.** That is still a reference. `bugbot-triage.md` is opened by four playbooks and one `## Non-negotiables` line.
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

- **What there is:** MMW ships no subagent definitions (ADR 0015). A skill that needs one sends out its host's general-purpose subagent, on the session's own model, and writes its whole prompt, usually from a template in the skill's `references/` (each `code-review` axis is its axis file with the ticket and base commit written in). Such a subagent does not load `mmw-mode`; it reads only what the skill gives it. The rules every such dispatch follows are `mmw-mode/SKILL.md` `## Subagents`.
- **Not a subagent:** a session a script starts. The worker and the reviewer are started by the `dispatch` skill's `dispatch.sh start`, and the advisor, the researcher, the explainer and the synthesizer by its `dispatch.sh brief`, each as a session of its own on the row `~/.mmw/models.json` gives its role; the worker and the reviewer load `mmw-mode` through the first sentence of their start prompt and run the playbook its second sentence names (`mmw-v3/course` lesson 5). A briefed session reports its answer with `dispatch.sh report`, and the relay wakes the session that briefed it once the whole batch has reported (`mmw-v3/course` lesson 6, section 9).
- **Which kind a new agent is:** three questions, in order. Can the session do the work itself in this turn, where its own reading is good enough: then no agent. Does the work need a model of its own, or to run outside this turn: then a session role. Otherwise (several pieces at once, or a context the session's own reasoning has not touched): a subagent. Every role of either kind has a row in the `dispatch` skill's `roles.json`; `check-interfaces.py` beside `dispatch.sh` refuses an agent without a row and a row nothing uses. A new session role is a row there, a default row in `hosts.json`, and the text it opens with; a new subagent is a row there and its prompt, written in the text of the skill that sends it or, when it is long, in that skill's `references/`; a playbook that sends one keeps its prompt in `mmw-mode/references/` (`mmw-v3/course` lesson 6, section 8).
- pstack's `poteto-agent` exists because a general subagent skips reading the mode: "Substituting `generalPurpose` skips that read and drifts." In MMW the sessions that run a role playbook load the mode through their start prompt, so no definition file is needed for it.

## configuration

- **For:** a choice that differs per person or machine and must hold in every session, such as the host, model and reasoning effort of each role a script starts (junior and senior worker, reviewer, advisor, researcher). The defaults are the `defaults` of the `dispatch` skill's `hosts.json`, which the installer writes when a machine has no `models.json`; a start whose role has no row is refused, naming the row.
- **Not for:** text in the mode or a skill.
- MMW's is `~/.mmw/models.json`, changed only through `models.py`.

## user-level prompt

- **For:** what holds in every session, the mode loaded or not: who reads the reply, and which decisions only the owner makes.
- **Not for:** anything the mode, a principle or a skill holds. The mode's `## Autonomy` points to this file for the owner's decisions instead of listing them again.
