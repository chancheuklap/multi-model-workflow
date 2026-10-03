# Writing and reviewing a skill set

The branch of the `writing-for-agents` skill for a **skill set**: the skills one install list ships (in MMW v3, every skill directory under `mmw-v3/skills/`), with their references and scripts, run by agents that each load only their own part. That skill's `SKILL.md` gives the levers and the names of the failure modes; this file applies them to a set whose skills hand work to each other. The checks are also the rules for writing: whoever writes or edits a skill in the set applies them to the passage in hand.

Text inside an upstream subtree also follows that subtree's own `AGENTS.md`.

## Layers of the set

A set has seven kinds of component. Each is a layer of its own and answers one question.

| Component | The question it answers | Where it lives |
| --- | --- | --- |
| **mode** | Which situation calls for what, which playbook a task takes, what an unattended session may decide, and how a woken session picks up | the `SKILL.md` of the `mmw-mode` skill |
| **playbook** | The steps of one kind of task from start to finish, who owns what, and what is handed back | the `playbooks/` of the `mmw-mode` skill, one file each, opening with its `###` title, with no frontmatter; a repository's own in its `.mmw/playbooks/` |
| **principle** | A judgement that holds across tasks and changes a specific decision | the `principles/` of the `mmw-mode` skill, one file each, opening with its `#` title, with no frontmatter: a principle is not a skill, is read by path and never invoked, and its trigger is its index line in the mode's `## Principles` |
| **capability skill** | How one thing is done and what it hands back; it does not know who calls it | its own skill directory |
| reference | Material read only at the steps that point to it, or a brief handed to a subagent or to a separately started session | the `references/` of the skill that owns it |
| script | The state reads and writes, deliveries and checks that come out the same on every run | the `scripts/` of the skill that owns it |
| role and configuration | Which role reads which playbook, on which model, and which event wakes it at which step | the `roles.json` of the `mmw-mode` skill (none yet: no role runs from v3), and `~/.mmw/models.json` |

**The test.** A passage lives in the layer whose question it answers. A passage found in another layer is a finding, unless a constraint keeps it there and the change that left it names that constraint; in MMW the constraints are H1 to H6 and S in `docs/adr/0032-the-set-is-layered.md`. Staying is not justified by "no benefit", "it works today" or "the change is large".

## What skill text is for

Every check below serves these seven facts about how an agent uses a set.

1. **A skill hands over understanding, not only steps.** Steps cover the cases their writer foresaw, and the agent meets others. So beside its steps a skill says what the work is for, who depends on what it produces and what a wrong or shallow result costs them, and, next to a rule, the reason for it: a model given the reason carries it into cases no rule names. Upstream's `wayfinder` does this in its opening and in `## Plan, don't do`. Such text is paid for as fact 4 says, by a judgement the agent could not make without it, and it has two tests. A sentence beside a rule passes when you can name a case the steps do not cover and what the agent does differently there with it. An opening passage passes when an agent holding only the skill could not otherwise say what the work is for, who acts on what it produces, and what a shallow result costs them. A sentence that only declares importance, retells the pipeline around the task, or tells this agent what another skill's agent does, fails both and is a no-op. One that passes is not cut for length; cutting it takes what [Editing](#editing) asks.
2. **Scripts carry what is deterministic; text carries judgement.** A script runs the fixed procedure, checks what can be checked exactly, and says on refusal what happened and what to do next. The text tells the agent when to run it and how to decide what no script can decide: what counts as done, which of two readings applies, what the user meant. Text that narrates what a script does spends the agent's attention on work the agent does not do.
3. **Attention is the budget.** Every sentence an agent reads competes with the sentence it needs. Material read at a moment that does not use it, a rule stated twice, and a case the agent would handle by default all thin the attention left for the judgement the text exists to guide.
4. **Direct, then trust.** A skill states the goal, the constraints, the judgement calls and the completion criterion, and leaves the ordinary moves to the model. Text that scripts every move makes the flow **rigid** (the agent follows the list when the situation differs from it) and **brittle** (each enumerated case must be kept in step with the scripts, and the case nobody listed has no guidance at all). Upstream's `implement` is five lines: it names the skills it hands to (`tdd`, `code-review`) and trusts the agent with the rest. MMW's automation needs more than that, and each addition is paid for by a judgement the agent could not make without it.
5. **Progressive loading follows branches, not topics.** A file earns its own pointer when a given run can skip it. Material every run of a task reads belongs in the file that run already holds. Splitting it into pieces saves nothing and adds a jump for each piece.
6. **Skills are peers composed by name.** A skill reaches another by naming it and the job, as upstream's `grill-with-docs` ("grilling" and "domain-modeling") and `implement` do; the other skill is loaded whole and does its own job. A skill never carries a copy of another skill's files, and never restates another skill's rules.
7. **Everything has one home, and every skill has one place.** A method (how to interview, how to close a ticket), a concept, a piece of reference and a function each live in one skill, and another skill reaches it by naming that skill, as upstream's `grill-me` is a single call to `grilling`. A second copy is a finding however useful it looks: a flow retold as a map, a rule restated for a second reader, a definition repeated, a second entry to one function. It has to be kept in step with the first and in time contradicts it. A skill's place is set by the mode's route table and the playbooks, not by its own text: the route table sends each kind of task to one playbook, and a playbook step names the skill it uses. The order of a task therefore has one home, its playbook: a second statement of it drifts from the first, and a hop written in no playbook leaves the agent without a next step. A capability skill ends with what it hands back.

## Checks

Every subsection applies to any text an agent reads, except these, which apply only to their kind of text:

| Subsection | Applies to |
| --- | --- |
| Scripts and judgement | text about a script, and the script itself |
| Descriptions | a skill's frontmatter `description` |
| Prompts written for other agents | a start prompt, a subagent's brief, and the template either is written from |
| Upstream skills | text inside an upstream subtree, or adapted from one |
| Examples | a passage that gives an example |
| Refusals and output an agent reads | what a script prints for an agent |

### Load and disclosure

A **moment** is a point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps (`writing-for-agents` `SKILL.md` `## Steps and completion criteria`).

- A skill's `SKILL.md` holds what every task passes through: when the moments share a purpose that no reference states for itself, first a few sentences on what the work is for and what depends on it; then the table that sends each reader to its moment. Each reference file holds one moment whole, and is named in `SKILL.md` with the condition for opening it.
- The table that finds the reader's moment sits before any step with side effects, so a re-entering agent does not repeat them.
- Once `SKILL.md` has sent the agent to its moment, the file it opened holds the rule, the format, the command, the known pitfall and the completion criterion. A step that needs a second file, of this skill or another, is a **jump**. The fix moves the material to the file the step already holds, or to the skill whose agent uses it. Handing the whole job to another skill by name (as `implement` hands the red-green loop to `tdd`) is a hand-off, not a jump.
- A reference that every run of the task opens is a **fragment**: inline it, unless `SKILL.md` would then carry material other tasks skip. A moment split across files by topic, and a file split by step when every run reads every step, are fragments too.
- A `SKILL.md` section that only one branch reads moves to that branch's reference. A task that reads a long file for one section of it is carrying load: split the file at the branch, or move the section to where the task already reads.
- A pointer is reached at or before the first step that needs its material. A rule the agent meets only after acting on the step it governs is a finding.
- A pick-one-of-N choice is a table. A numbered list reads as a pipeline to run in full.
- A rule sits in the text of the agent that must follow it. A rule for the worker written only in the orchestrator's skill, in a script's comment, in the glossary, in a merge-note, or in this file reaches no worker. An artifact's definition, check, explanation and use belong to one skill: the skill whose agent uses the artifact. A reason the acting agent needs is the same: a merge-note, an ADR or the glossary may explain it to maintainers, but the sentence the agent acts on is in the skill text.
- Material works only from text the agent loads. A profile note, a comment thread, a conversation, or an artifact link the next agent cannot open carries nothing forward; what the next agent needs goes in what it will read (a spec's body, a ticket's fixed headings).
- The text makes sense to an agent that holds nothing else: no reference to another session, to memory, or to a word coined while writing it. A statement of fact is true: a rule the agent keeps is written as a rule, not as a fact about the system.

### Redundancy and bloat

Each sentence is tested against what the agent would do without it (`writing-for-agents` `SKILL.md` `## Pruning`). These are findings, fixed by deleting or merging:

- **Duplication**: one meaning stated in two places across the set, counting a script's `--help`, its refusal text, a start prompt it builds and a template. Which copy stays is decided by **principle-one-home-per-meaning**.
- **Cache** (`writing-for-agents` `SKILL.md` `## Pruning`): text restating a script's `--help`, a config file, the tracker, or a skill the agent has loaded.
- **No-op**: an instruction the model already follows by default, or an attitude where an action would do ("be careful", "make sure"). A stance is not a bare attitude: it names the temptation particular to this work and what to do instead (upstream `wayfinder`: "The pull to just do the work is usually the signal you've reached the edge of the map"), and a model does not hold it by default.
- **Over-specification**: a numbered procedure for work a capable agent does unprompted; an if-then list that mirrors a script's branches; an enumeration of cases where one criterion covers them; a procedure added to enforce a rule. Replace it with the goal, the criterion and the one or two judgement calls the agent would get wrong.
- **Over-defense**: text or a mechanism that guards a path that does not occur. Judge it with four questions: has it ever fired (the tracker history, logs, state files)? Is its case reachable by normal input? Is its premise true when measured, not reasoned? If it is removed, what handles the case? When the first two answers are no, delete it and state the residual risk once in the report.
- **Sediment**: text that is not about the task at hand now.

  | In the body | Its home |
  | --- | --- |
  | a dated measurement, "tested on" | the script header or a research file |
  | the maintainer's reason for a design (why a script takes a lock rather than checking a pid) | an ADR |
  | what changed, what used to be true, "no longer", "now" | the commit message |
  | where the writer's material came from (a research note, "from chapter 3 of …"), other than the author of a concept, an issue number the reader cannot use | nowhere |
  | a branch no run can reach, a note telling the agent to ignore something | nowhere |

These stay, though a trimming pass reads them as noise: a sentence that prevents a known misuse (keep the winning prototype running as the reference while pages are drawn); an example value that is the field's format (`conversation 2026-09-18`); a prohibition kept under the Negation rule of `writing-for-agents` `SKILL.md`; a reason the agent needs to decide an edge case, or to keep a design choice it would otherwise simplify away (upstream `code-review`'s `## Why two axes`); a sentence that passes the test of fact 1 of [What skill text is for](#what-skill-text-is-for); the name of the author or work a concept comes from (**Seam**, Michael Feathers), which calls up the theory the model already holds. A trimming pass tests each sentence against a step; these are tested against the cases no step covers. Other agents copy the style of what they read, so the body is written plainly.

### Scripts and judgement

- Where a script decides, the text gives the command, the moment to run it, and what to do on each outcome whose next action depends on something the script cannot see. The refusal's own "what to do next" covers the rest. The complete flag list and exit-code table stay beside the script (its `--help`, its header). Text that assigns the script's writes to the agent is a finding.
- Where only understanding can decide (what counts as X, which of two readings applies, when a step is finished), the words go there: the criterion, the exact rule the script will apply when it later judges the agent's output, and a contrasting pair of examples when a misreading is likely.
- A rule a script could check exactly becomes a check (a lint, a refusal, a test), not a sentence. A numeric limit a program depends on is enforced by that program.
- A check or completion criterion that cannot fail proves nothing: it is fixed or removed.
- Programs branch on exit codes and fields; the refusal's wording is for the agent. Rewording a message changes no behaviour.

### Descriptions

- A description carries the trigger and nothing else: what the skill is, and the branches on which to load it (`writing-for-agents` `SKILL.md` `## Context pointers`); a user-invoked skill's is a one-line summary for the person (`writing-for-agents` `SKILL-MECHANICS.md` `## Invocation`). Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body; a description carrying them is a finding. A branch naming the role an agent was started as ("when you were started as the advisor") is a trigger.
- Read every description in the set side by side, also in a partial review. Two descriptions that claim the same job are a conflict. A caller and the skill it hands to may share a trigger word when each description names only its own part of the job.
- A description names no host and no runner: every host scans it into its system prompt, so one name ties the skill to that host or runner. A runner that cannot start is refused by its script at run time.
- A skill this repository wrote has no host-side manifest beside it (upstream skills keep their `agents/openai.yaml`), so its name and description have one authority. The `disable-model-invocation` pairing on upstream skills is in `mmw-v2/merge-notes/README.md`.

### Vocabulary

- One word, one meaning across the whole set, placeholders and tokens included. Two meanings for one word are fixed at the source (rename in the skill or script, record it in the merge-note), not by fencing each meaning inside one skill. When two upstream skills define one term differently, the set picks one meaning and records the choice.
- A concept's name is chosen, in this order: the established term of its field whose meaning matches exactly (a configuration **baseline**, a test **oracle**, a **Gateway**, **fault injection**, an **orchestrator** and its workers); failing that, ordinary dictionary words that describe it; failing that, a coined term, defined in one sentence, in bold, where it first appears. An established term is a leading word (`writing-for-agents` `SKILL.md` `## Leading words`): it brings in what the model already knows about it, so the term's source is named where it is defined when that calls up a theory (**Seam**, Michael Feathers), and a borrowed term whose meaning differs from the concept (a false friend) is a finding, worse than a plain coinage, because it brings in the wrong behaviour. Look for the established term before coining one: in the field's canonical books and standards (upstream draws on *The Pragmatic Programmer*, Evans's *Domain-Driven Design*, Fowler's *Refactoring* and *Patterns of Enterprise Application Architecture*, Ousterhout, Feathers, Brooks) and, for agent work, Matt Pocock's *Dictionary of AI Coding*.
- A name stored where this repository cannot rewrite it (an event or field in tracker comments, a label, a `.mmw/target.json` key, a script a ticket's `CHECK:` line calls, a script or module a consuming repository's configuration or tests name) is copied verbatim and never renamed. A name only this repository's own scripts read (a command, a flag, a file) is renamed when it misleads or gives one word two meanings, never for style; the renamed command or flag answers its old name, for one release, with a refusal naming the new one. Where the text names a concept by an identifier, the identifier is its one name. A concept with its own prose name keeps the identifier beside it in the glossary. The name an upstream skill gives its own concept is used in upstream's sense.
- A coined word does not qualify by appearing in a heading. A metaphor is a finding unless it is a leading word. An undefined coinage, a colloquial phrase, a word whose meaning you cannot state in one sentence, and one word spelled two ways are findings.
- Skill text is English. Another language appears only inside a name the program uses, copied verbatim (a heading a script writes, a label).
- The glossary is complete: every concept of the set's own text that an agent reasons with has one entry, and a term the text uses as a concept with no entry is a finding. A family of identifiers (the lines a script prints, the tags a lint uses, the columns of a row) is one entry naming the family, what it is for, and its `_Home_`; a term used only in its field's ordinary sense, and an upstream skill's term used in upstream's sense, get none.
- The glossary is held to the same standard. An entry that makes a coined or vague word official, or whose `_Avoid_` line bans the established term, is a finding: the term, the entry and every skill using it change together. An entry's facts are checked against the file it cites as `_Home_`; an entry citing a file that does not hold those facts is a finding. A behaviour rule found only in the glossary is evidence of intended behaviour (see [Load and disclosure](#load-and-disclosure)).
- A heading or step that another skill finds by position is cited by producer and reader as the same literal, by title rather than by number.
- In MMW v3 the glossary is `mmw-v3/CONTEXT.md`.

### Hand-offs

A **hand-off** is an edge A → B: skill or agent A leaves something that B reads or waits for.

- What A leaves (the artifact, where, under which name or heading) is what B reads, by the same name. The hand-off is broken where they differ, where B needs something A never produced, or where A produces something (a section, a field, a child issue) that B reads under a condition A does not share.
- For every outcome A produces in use, name who reads it and what they do next. An outcome nobody acts on, or one that reaches the reader looking like success, is a broken hand-off.
- Between two sessions, B gets a completion signal it actually receives (an event, a wake, a command that blocks until A is done).
- Each event gets one instruction across the set. Two skills or scripts that tell the agent different things about the same event (the same exit code, the same wake, the same "done") contradict each other; the fix goes in the skill that owns the event.
- A sentence in a capability skill that names its caller or the step that follows is a finding: those are written in the mode and the playbooks.
- A sentence written for one caller can misread under another. When skill X runs inside skill Y, reread X's general statements in Y's situation.
- Read each task for **unguided choices**: points where the agent must choose and the text says nothing, which hands the choice to the model's own habits. Fill each one with the criterion, or make it an explicit branch. A choice any reasonable model makes the same way is not unguided; writing it down is a no-op.
- Invoking another skill, in MMW: name the skill and the job, never an install path; the agent holding a skill resolves its scripts. To take its vocabulary and apply it in place, read its `SKILL.md`; to run it in a separate context, ask for the host's own general-purpose subagent and have it use the skill. A file in another skill is named by skill and file ("the `ui-acceptance` skill's `references/story-parity.md`").
- A hard dependency (the skill produces wrong output without some setup) gets one line naming what to run, as upstream's `to-spec` names `setup-matt-pocock-skills`; a soft one (the setup only sharpens output) gets a general mention.

### Prompts written for other agents

- A start prompt carries only what is known when the agent is started (the ticket number, a base commit, where the task came from). Rules reach the agent through the skill it loads; a ticket or spec is named and read from the tracker, not retold. A brief a model writes from a template counts as a start prompt, and the template lists everything the receiver needs.
- Everything an agent must apply reaches it by one of two means: a skill or file its prompt tells it to load, or text pasted into the prompt. A rule the prompt says the agent applies, delivered by neither, is a broken hand-off. A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data.
- A subagent's brief states what it returns and its length (upstream `code-review`: "Under 400 words"), so its report fits the caller's attention.

### Upstream skills

An **upstream skill** (one kept in an upstream subtree, or adapted from one) enters the set as its authors wrote it. The set's work is to connect it to the workflow: what reaches it, what it hands on, which repository rule it must obey. Its text changes only where the change alters what the agent does: a step, their order, where or with what it works, what it produces or hands over. A rewording for style, clarity or the set's voice is a finding, fixed by restoring the upstream text.

- Diff the skill against upstream (the squash-commit command is in `mmw-v2/merge-notes/README.md`). A pstack file imported into a skill is recorded instead as a row of that skill's `imports.tsv`: its `source` and `commit` give the upstream text, and its `mechanical` and `judgement` columns are its merge-note. Every changed paragraph maps to a merge-note entry stating the behaviour it changes. A paragraph with no entry, or whose entry states only wording, goes back to upstream's text. A skill adapted from upstream without a merge-note is a finding.
- The merge-note's entries agree with each other and with the current text. An entry that still states a replaced rule is a finding: the next upstream pull would restore that rule.
- Connect outside the upstream text first: in the set's own skills, in a reference file added beside the upstream ones, in the line a caller reads. An upstream sentence changes only when an agent reading it would act wrongly in this workflow even with the connecting text in place.
- Checks on style (completion-criterion lines, the shape of a description, vocabulary preferences) apply to the set's own text. Upstream sentences are judged on whether they work in the workflow.
- When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text. Its upstream original remains the measure of length: an addition earns its words by a judgement the workflow needs that upstream did not.

### Paths and host neutrality

- MMW is itself a skill collection loaded into the agent's runtime: naming another skill (`` the `X` skill ``) hands off the work, and a skill's own references and scripts are named by their path inside the skill (`references/<name>.md`, `scripts/<name>.py`), resolved by the agent already holding it. Skill text carries no absolute path and no explanation that a script's location differs by machine or by host: the agent knows where a loaded skill lives.
- A ticket's `CHECK:` line names no path: a shell runs it with no agent in between, `verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on that shell's `PATH`, so an oracle is named bare. Its shapes are in the `to-tickets` skill's `references/screen-contract-tickets.md` **Criterion shapes**.
- One text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability ("a host that cannot hold a turn open", "a host that can run subagents"). The runner is the one `models.py runner` selects; the text states that and assumes nothing past it. A skill is named by its name, as `/X` or `the X skill`; a host's tool for invoking skills is not named (`the Skill tool` exists on one host only). A session command (emptying a session's context, compressing it into a summary) is written as the action, and the file that names one carries this sentence once: `Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.`

The check is a `grep` of every `SKILL.md`, description and reference (this file excepted) for: a relative path that climbs out of the skill directory; a path in a `CHECK:` line; a host name (`claude`, `codex`, `grok`, `cursor`, `pi`), a tool name (`the Skill tool`, `the Task tool`), or a runner name (`orca`, `herdr`, `paseo`).

### Rules and completion criteria

- In the set's own text, a step without a completion criterion is a finding, and so are two different statements of what "done" means for one task; the set writes it on a line beginning `Done when`.

### Examples

- An example uses a neutral domain (a notes app). An example naming a real product, a spec or issue number, or a past run is a finding: an agent reading it takes the specifics as requirements.
- An example value is labelled as an example; the rule it illustrates is the authority.
- A good and a bad example side by side are used where a misreading is likely.

### Refusals and output an agent reads

- A refusal follows `CODING_STANDARDS.md`, and its next step fits the skill that receives it.
- Hosts cut long output before the agent sees it, so the next step sits in the first lines.
- The suggested next step is safe to run as written.

## Editing

- A fix removes, merges, moves or simplifies before it adds. A fix that adds a mechanism (a check, a field, an exit code, a verb, or a sentence telling the agent what to do in a case) names, in the Reply and the commit message, the run in which the failure occurred, or the user's words asking for it. That run is one the mechanism would have prevented, not a nearby incident that shares a word with it. A passage that hands over purpose, a reason or a stance (what the work is for, why a rule holds, the temptation particular to this work) is not a mechanism: it needs no failed run behind it, but it names its case, and says when that case is inferred rather than observed. A reason or criterion nobody can ground in the code, the tracker, a recorded run or the user's words is not written to fill the gap: an agent guesses around a rule stated without its reason, but it generalises from an invented one.
- Fix at the level of the finding. A wording finding is fixed in the sentence: improve the sentence that misled, since a new sentence added to correct an old one leaves both. A load finding is fixed in the structure: move, merge, split at a branch, or delete whole sections, carrying each sentence that still applies across verbatim. Sentences the finding does not touch stay byte for byte.
- Asked to "streamline", an agent shortens and cuts function with it, so every deletion is tested against the agent's behaviour: walk the task after the edit and confirm it still reaches its completion criterion with no new guess (`writing-for-agents` `SKILL.md` `## Pruning`). Reaching the completion criterion on the walked path does not clear a cut to such a passage, since its effect is on the runs the walk did not take. Before cutting one, name the case it would have guided and what guides that case after the cut.
- Before a rename, move or deletion, `grep` the set for the heading, file name, token and term you are changing, and change every file that states it in the same edit: skills, references, scripts, templates, tests, merge-notes. Callers cite sections by name.
- Text taken from another source keeps its authors' wording (see [Upstream skills](#upstream-skills)). Excerpts are quoted verbatim and collected into one block before they are placed; finding places for them first splits the source apart.
- The file states what is true now; what changed and why goes to the commit message and the report.

## Verifying

- Green tests prove the scripts, not that the text reads well; report them on a separate line.
- The text is proven by a run: a fresh agent given only the trigger and a real job (one the tracker or the repository's history shows was done with this text; for a skill a ticket runs, one real ticket; where history has none, one the user would plausibly give, which the Reply calls made up) does the task. Watch which files it opens, where it guesses, and where it stops before the completion criterion; which of those send the text back to be rewritten is said by the step that runs the walk. A sentence present in the text is not a behaviour observed; a claim that the text now changes behaviour is unverified until such a run shows it.
- The fresh agent's brief carries the trigger (the user's words or the start prompt), the job (the smallest real instance of the task that reaches the changed text), that it opens only what the text in front of it points to and does the job on paper (it writes nothing, and walks a step that would write as far as deciding what it would write), the record **Walk each task** in the `mmw-mode` skill's `playbooks/review-the-skill-set.md` asks for, and a length limit on its report.


## Upstream examples

mattpocock's own skills show several checks done well. The in-repository copies under `mmw-v2/upstream/skills/` carry this repository's edits; read the original from the latest squash commit (found as `mmw-v2/merge-notes/README.md` says), with `git show <commit>:skills/<bucket>/<skill>/<file>`. The in-progress `retro` below is upstream's, not MMW's own `retro` skill.

| Check | Upstream file | What to look at |
| --- | --- | --- |
| What skill text is for | `engineering/wayfinder/SKILL.md` opening, `## Plan, don't do`, `## Fog of war`; `productivity/grilling/SKILL.md` last two paragraphs | purpose and stance in a few sentences, which the agent carries into cases no step names |
| Descriptions | `engineering/wizard/SKILL.md`, `engineering/prototype/SKILL.md` | the trigger branches; one explicit non-trigger |
| Load and disclosure | `engineering/prototype/SKILL.md` with `LOGIC.md` and `UI.md` | each branch file whole, each naming the other branch for a reader who took the wrong one |
| Load and disclosure | `engineering/codebase-design/SKILL.md` `## Going deeper` | each pointer carries its condition |
| Load and disclosure | `productivity/to-questionnaire/SKILL.md`, `engineering/to-spec/SKILL.md` | the template stays inline because every run writes one |
| Redundancy and bloat | `engineering/code-review/SKILL.md` `## Why two axes` | the one reason kept, because without it the agent would merge the axes |
| Scripts and judgement | `engineering/wizard/SKILL.md` | "The delightful UX is already solved by template.sh ... Your job is only to scope the procedure and author its stages" |
| Scripts and judgement | `engineering/code-review/SKILL.md` `### 3. Identify the standards sources` | the smell baseline: each item is what it is and how to fix it, marked "always a judgement call" |
| Scripts and judgement | `engineering/code-review/SKILL.md` `### 1. Pin the fixed point` | "A bad ref or empty diff should fail here, not inside two parallel sub-agents": one early check, placed where it saves the most |
| Scripts and judgement | `in-progress/retro/SKILL.md` | a mechanical violation gets a deterministic check; the standards document keeps only judgement calls |
| Vocabulary | `engineering/codebase-design/SKILL.md` `## Glossary`; `engineering/improve-codebase-architecture/HTML-REPORT.md` `## Tone` | "Use these terms exactly"; "Use exactly" / "Never substitute"; each term with its `_Avoid_` line, and its source where it has one (**Seam** _(Michael Feathers)_) |
| Vocabulary | `engineering/to-tickets/SKILL.md` `### 3. Draft vertical slices` | **tracer bullet**, a term from *The Pragmatic Programmer*, carrying a whole way of cutting work in two words |
| What skill text is for (fact 7) | `productivity/grill-me/SKILL.md`, `engineering/grill-with-docs/SKILL.md` | the whole skill is one line naming the skill that owns the method |
| Hand-offs | `productivity/grilling/SKILL.md` | facts (look them up) kept apart from decisions (put them to the user); the end stated as "the frontier is empty" |
| Hand-offs | `engineering/to-spec`, `to-tickets`, `triage` against `tdd`, `diagnosing-bugs` | a hard dependency names `setup-matt-pocock-skills` in one line; a soft one only says to read the domain glossary if it exists |
| Prompts | `engineering/code-review/SKILL.md` `### 4. Spawn both sub-agents in parallel` | the Standards subagent gets the smell baseline "pasted in full (the sub-agent has no other access to it)", and a length limit |
| Examples | `engineering/triage/AGENT-BRIEF.md` | good and bad briefs side by side, with why the bad one fails |
