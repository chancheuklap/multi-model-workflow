# Checks for any passage

Every section here applies to any text an agent reads, written or reviewed. A passage of one of the kinds in the table of this skill's `SKILL.md` is also held to that kind's file. A check here is also a rule for writing: apply it to the passage in hand.

## Load and disclosure

A **moment** is a point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps (`writing-for-agents` `SKILL.md` `## Steps and completion criteria`).

- A skill's `SKILL.md` holds what every task passes through: when the moments share a purpose that no reference states for itself, first a few sentences on what the work is for and what depends on it; then the table that sends each reader to its moment. Each reference file holds one moment whole, and is named in `SKILL.md` with the condition for opening it.
- The table that finds the reader's moment sits before any step with side effects, so a re-entering agent does not repeat them.
- Once `SKILL.md` has sent the agent to its moment, the file it opened holds the rule, the format, the command, the known pitfall and the completion criterion. A step that needs a second file, of this skill or another, is a **jump**. The fix moves the material to the file the step already holds, or to the skill whose agent uses it. Handing the whole job to another skill by name (as `implement` hands the red-green loop to `tdd`) is a hand-off, not a jump.
- A reference that every run of the task opens is a **fragment**: inline it, unless `SKILL.md` would then carry material other tasks skip. A moment split across files by topic, and a file split by step when every run reads every step, are fragments too.
- A `SKILL.md` section that only one branch reads moves to that branch's reference. A task that reads a long file for one section of it is carrying load: split the file at the branch, or move the section to where the task already reads.
- A pointer is reached at or before the first step that needs its material. A rule the agent meets only after acting on the step it governs is a finding.
- A pick-one-of-N choice is a table. A numbered list reads as a pipeline to run in full.
- A rule sits in the text of the agent that must follow it. A rule for the worker written only in the orchestrator's skill, in a script's comment, in the glossary, in a merge-note, or in this skill reaches no worker. An artifact's definition, check, explanation and use belong to one skill: the skill whose agent uses the artifact. A reason the acting agent needs is the same: a merge-note, an ADR or the glossary may explain it to maintainers, but the sentence the agent acts on is in the skill text.
- Material works only from text the agent loads. A profile note, a comment thread, a conversation, or an artifact link the next agent cannot open carries nothing forward; what the next agent needs goes in what it will read (a spec's body, a ticket's fixed headings).
- The text makes sense to an agent that holds nothing else: no reference to another session, to memory, or to a word coined while writing it. A statement of fact is true: a rule the agent keeps is written as a rule, not as a fact about the system.

## Redundancy and bloat

Each sentence is tested against what the agent would do without it (`writing-for-agents` `SKILL.md` `## Pruning`). These are findings, fixed by deleting or merging:

- **Duplication**: one meaning stated in two places across the set, counting a script's `--help`, its refusal text, a start prompt it builds and a template. Which copy stays is decided by the `mmw-mode` skill's `principles/principle-one-home-per-meaning.md`.
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

These stay, though a trimming pass reads them as noise: a sentence that prevents a known misuse (keep the winning prototype running as the reference while pages are drawn); an example value that is the field's format (`conversation 2026-09-18`); a prohibition kept under the Negation rule of `writing-for-agents` `SKILL.md`; a reason the agent needs to decide an edge case, or to keep a design choice it would otherwise simplify away (upstream `code-review`'s `## Why two axes`); a sentence that passes the test of fact 1 in this skill's `SKILL.md` `## What skill text is for`; the name of the author or work a concept comes from (**Seam**, Michael Feathers), which calls up the theory the model already holds. A trimming pass tests each sentence against a step; these are tested against the cases no step covers. Other agents copy the style of what they read, so the body is written plainly.

## Vocabulary

- One word, one meaning across the whole set, placeholders and tokens included. Two meanings for one word are fixed at the source (rename in the skill or script, record it in the merge-note), not by fencing each meaning inside one skill. When two upstream skills define one term differently, the set picks one meaning and records the choice.
- A concept's name is chosen, in this order: the established term of its field whose meaning matches exactly (a configuration **baseline**, a test **oracle**, a **Gateway**, **fault injection**, an **orchestrator** and its workers); failing that, ordinary dictionary words that describe it; failing that, a coined term, defined in one sentence, in bold, where it first appears. An established term is a leading word (`writing-for-agents` `SKILL.md` `## Leading words`): it brings in what the model already knows about it, so the term's source is named where it is defined when that calls up a theory (**Seam**, Michael Feathers), and a borrowed term whose meaning differs from the concept (a false friend) is a finding, worse than a plain coinage, because it brings in the wrong behaviour. Look for the established term before coining one: in the field's canonical books and standards (upstream draws on *The Pragmatic Programmer*, Evans's *Domain-Driven Design*, Fowler's *Refactoring* and *Patterns of Enterprise Application Architecture*, Ousterhout, Feathers, Brooks) and, for agent work, Matt Pocock's *Dictionary of AI Coding*.
- A name stored where this repository cannot rewrite it (an event or field in tracker comments, a label, a `.mmw/target.json` key, a script a ticket's `CHECK:` line calls, a script or module a consuming repository's configuration or tests name) is copied verbatim and never renamed. A name only this repository's own scripts read (a command, a flag, a file) is renamed when it misleads or gives one word two meanings, never for style; the renamed command or flag answers its old name, for one release, with a refusal naming the new one. Where the text names a concept by an identifier, the identifier is its one name. A concept with its own prose name keeps the identifier beside it in the glossary. The name an upstream skill gives its own concept is used in upstream's sense.
- A coined word does not qualify by appearing in a heading. A metaphor is a finding unless it is a leading word. An undefined coinage, a colloquial phrase, a word whose meaning you cannot state in one sentence, and one word spelled two ways are findings.
- Skill text is English. Another language appears only inside a name the program uses, copied verbatim (a heading a script writes, a label).
- The glossary is complete: every concept of the set's own text that an agent reasons with has one entry, and a term the text uses as a concept with no entry is a finding. A family of identifiers (the lines a script prints, the tags a lint uses, the columns of a row) is one entry naming the family, what it is for, and its `_Home_`; a term used only in its field's ordinary sense, and an upstream skill's term used in upstream's sense, get none.
- The glossary is held to the same standard. An entry that makes a coined or vague word official, or whose `_Avoid_` line bans the established term, is a finding: the term, the entry and every skill using it change together. An entry's facts are checked against the file it cites as `_Home_`; an entry citing a file that does not hold those facts is a finding. A behaviour rule found only in the glossary is evidence of intended behaviour (see `## Load and disclosure` above).
- A heading or step that another skill finds by position is cited by producer and reader as the same literal, by title rather than by number.
- In MMW v3 the glossary is `mmw-v3/CONTEXT.md`.

## Hand-offs

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

## Paths and host neutrality

- MMW is itself a skill collection loaded into the agent's runtime: naming another skill (`` the `X` skill ``) hands off the work, and a skill's own references and scripts are named by their path inside the skill (`references/<name>.md`, `scripts/<name>.py`), resolved by the agent already holding it. Skill text carries no absolute path and no explanation that a script's location differs by machine or by host: the agent knows where a loaded skill lives.
- A ticket's `CHECK:` line names no path: a shell runs it with no agent in between, `verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on that shell's `PATH`, so an oracle is named bare. Its shapes are in the `to-tickets` skill's `references/screen-contract-tickets.md` **Criterion shapes**.
- One text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability ("a host that cannot hold a turn open", "a host that can run subagents"). The runner is the one `models.py runner` selects; the text states that and assumes nothing past it. A skill is named by its name, as `/X` or `the X skill`; a host's tool for invoking skills is not named (`the Skill tool` exists on one host only). A session command (emptying a session's context, compressing it into a summary) is written as the action, and the file that names one carries this sentence once: `Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.`

The check is a `grep` of every `SKILL.md`, description and reference (this skill's `references/checks*.md` excepted) for: a relative path that climbs out of the skill directory; a path in a `CHECK:` line; a host name (`claude`, `codex`, `grok`, `cursor`, `pi`), a tool name (`the Skill tool`, `the Task tool`), or a runner name (`orca`, `herdr`, `paseo`).

## Rules and completion criteria

- In the set's own text, a step without a completion criterion is a finding, and so are two different statements of what "done" means for one task; the set writes it on a line beginning `Done when`.
