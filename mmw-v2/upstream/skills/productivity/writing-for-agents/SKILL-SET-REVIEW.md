# Writing and reviewing a skill set

The branch of [`writing-for-agents`](SKILL.md) for a **skill set**: the skills one install list ships (in MMW, `mmw-v2/skills.txt`), with their references and scripts, run by agents that each load only their own part. `SKILL.md` gives the levers and the names of the failure modes; this file applies them to a set whose skills hand work to each other. The checks are also the rules for writing: whoever writes or edits a skill in the set applies them to the passage in hand. To review a set (walk its tasks, report and fix the findings), read [`REVIEWING-A-SKILL-SET.md`](REVIEWING-A-SKILL-SET.md); it applies the checks below.

Text inside an upstream subtree also follows that subtree's own `AGENTS.md`.

## What skill text is for

Every check below serves these five facts about how an agent uses a set.

1. **Scripts carry what is deterministic; text carries judgement.** A script runs the fixed procedure, checks what can be checked exactly, and says on refusal what happened and what to do next. The text tells the agent when to run it and how to decide what no script can decide: what counts as done, which of two readings applies, what the user meant. Text that narrates what a script does spends the agent's attention on work the agent does not do.
2. **Attention is the budget.** Every sentence an agent reads competes with the sentence it needs. Material read at a moment that does not use it, a rule stated twice, and a case the agent would handle by default all thin the attention left for the judgement the text exists to guide.
3. **Direct, then trust.** A skill states the goal, the constraints, the judgement calls and the completion criterion, and leaves the ordinary moves to the model. Text that scripts every move makes the flow **rigid** (the agent follows the list when the situation differs from it) and **brittle** (each enumerated case must be kept in step with the scripts, and the case nobody listed has no guidance at all). Upstream's `implement` is five lines: it names the skills it hands to (`tdd`, `code-review`) and trusts the agent with the rest. MMW's automation needs more than that, and each addition is paid for by a judgement the agent could not make without it.
4. **Progressive loading follows branches, not topics.** A file earns its own pointer when a given run can skip it. Material every run of a task reads belongs in the file that run already holds. Splitting it into pieces saves nothing and adds a jump for each piece.
5. **Skills are peers composed by name.** A skill reaches another by naming it and the job, as upstream's `grill-with-docs` ("grilling" and "domain-modeling") and `implement` do; the other skill is loaded whole and does its own job. A skill never carries a copy of another skill's files, and never restates another skill's rules.

## Checks

### Load and disclosure

A **moment** is a point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps (`SKILL.md` `## Steps and completion criteria`).

- `SKILL.md` holds what every task passes through, plus the table that sends each reader to its moment. Each reference file holds one moment whole, and is named in `SKILL.md` with the condition for opening it.
- The cut follows how often one agent enters the skill in one task. Entered once: one reference per arriving role or branch. Entered at several moments: one reference per moment, and the table that finds the reader's moment comes first in `SKILL.md`, before any step with side effects, so a re-entering agent does not repeat them.
- Once `SKILL.md` has sent the agent to its moment, the file it opened holds the rule, the format, the command, the known pitfall and the completion criterion. A step that needs a second file, of this skill or another, is a **jump**. The fix moves the material to the file the step already holds, or to the skill whose agent uses it. Handing the whole job to another skill by name (as `implement` hands the red-green loop to `tdd`) is a hand-off, not a jump.
- A reference that every run of the task opens is a **fragment**: inline it, unless `SKILL.md` would then carry material other tasks skip. A moment split across files by topic, and a file split by step when every run reads every step, are fragments too.
- A `SKILL.md` section that only one branch reads moves to that branch's reference. A task that reads a long file for one section of it is carrying load: split the file at the branch, or move the section to where the task already reads.
- A pointer is reached at or before the first step that needs its material. A rule the agent meets only after acting on the step it governs is a finding.
- A pick-one-of-N choice is a table. A numbered list reads as a pipeline to run in full.
- A rule sits in the text of the agent that must follow it. A rule for the worker written only in the main agent's skill, in a script's comment, in the glossary, in a merge-note, or in this file reaches no worker. An artifact's definition, check, explanation and use belong to one skill: the skill whose agent uses the artifact.
- Material works only from text the agent loads. A profile note, a comment thread, a conversation, or an artifact link the next agent cannot open carries nothing forward; what the next agent needs goes in what it will read (a spec's body, a ticket's fixed headings).
- The text makes sense to an agent that holds nothing else: no reference to another session, to memory, or to a word coined while writing it. A statement of fact is true: a rule the agent keeps is written as a rule, not as a fact about the system.

### Redundancy and bloat

Each sentence is tested against what the agent would do without it (`SKILL.md` `## Pruning`). These are findings, fixed by deleting or merging:

- **Duplication**: one meaning stated in two places across the set, counting a script's `--help`, its refusal text, a start prompt it builds and a template. Keep the copy the acting agent loads at the moment it acts; delete the others. When a third thing exists to reconcile two copies (a lint that compares them, a step that counts them), that is the reason to delete a copy, not to keep the reconciler.
- **Cache** (`SKILL.md` `## Pruning`): text restating a script's `--help`, a config file, the tracker, or a skill the agent has loaded.
- **No-op**: an instruction the model already follows by default, or an attitude where an action would do ("be careful", "make sure").
- **Over-specification**: a numbered procedure for work a capable agent does unprompted; an if-then list that mirrors a script's branches; an enumeration of cases where one criterion covers them; a procedure added to enforce a rule. Replace it with the goal, the criterion and the one or two judgement calls the agent would get wrong.
- **Over-defense**: text or a mechanism that guards a path that does not occur. Judge it with four questions: has it ever fired (the tracker history, logs, state files)? Is its case reachable by normal input? Is its premise true when measured, not reasoned? If it is removed, what handles the case? When the first two answers are no, delete it and state the residual risk once in the report.
- **Sediment**: text that is not about the task at hand now.

  | In the body | Its home |
  | --- | --- |
  | a dated measurement, "tested on" | the script header or a research file |
  | the maintainer's reason for a design | an ADR |
  | what changed, what used to be true, "no longer", "now" | the commit message |
  | a source line ("from chapter 3 of …"), an issue number the reader cannot use | nowhere |
  | a branch no run can reach, a note telling the agent to ignore something | nowhere |

These stay, though a trimming pass reads them as noise: a sentence that prevents a known misuse (a script's path differs by machine and by host, which stops an agent from writing the resolved path down; keep the winning prototype running as the reference while pages are drawn); an example value that is the field's format (`conversation 2026-09-18`); a prohibition kept under `SKILL.md`'s Negation rule; a reason the agent needs to decide an edge case, or to keep a design choice it would otherwise simplify away (upstream `code-review`'s `## Why two axes`). Other agents copy the style of what they read, so the body is written plainly.

### Scripts and judgement

- Where a script decides, the text gives the command, the moment to run it, and what to do on each outcome whose next action depends on something the script cannot see. The refusal's own "what to do next" covers the rest. The complete flag list and exit-code table stay beside the script (its `--help`, its header). Text that assigns the script's writes to the agent is a finding.
- Where only understanding can decide (what counts as X, which of two readings applies, when a step is finished), the words go there: the criterion, the exact rule the script will apply when it later judges the agent's output, and a contrasting pair of examples when a misreading is likely.
- A rule a script could check exactly becomes a check (a lint, a refusal, a test), not a sentence. A numeric limit is enforced by the mechanism; models do not copy literal numbers reliably.
- A check or completion criterion that cannot fail proves nothing: it is fixed or removed.
- Programs branch on exit codes and fields; the refusal's wording is for the agent. Rewording a message changes no behaviour.

### Descriptions

- A description carries the trigger and nothing else: what the skill is, and the branches on which to load it (`SKILL.md` `## Context pointers`). Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body; a description carrying them is a finding. A branch naming the role an agent was started as ("when you were started as the advisor") is a trigger.
- Read every description in the set side by side, also in a partial review. Two descriptions that claim the same job are a conflict. A caller and the skill it hands to may share a trigger word when each description names only its own part of the job.
- A description names no host and no runner: every host scans it into its system prompt, so one name ties the skill to that host or runner. A runner that cannot start is refused by its script at run time.
- A skill this repository wrote has exactly two frontmatter keys, `name` and `description`, and no host-side manifest beside it (upstream skills keep their `agents/openai.yaml`), so its name and description have one authority. The `disable-model-invocation` pairing on upstream skills is in `mmw-v2/merge-notes/README.md`.
- A user-invoked skill (`disable-model-invocation: true`) is loaded only when the user names it, so its description is a one-line summary for the person reading the command list (`SKILL-MECHANICS.md` `## Invocation`).
- A `description` holding a colon followed by a space breaks YAML; quote it. Check it with a YAML parser, since some hosts are lenient and some are not.

### Vocabulary

- One word, one meaning across the whole set, placeholders and tokens included. Two meanings for one word are fixed at the source (rename in the skill or script, record it in the merge-note), not by fencing each meaning inside one skill. When two upstream skills define one term differently, the set picks one meaning and records the choice.
- A term earns its place in one of three ways: it is the established term of its field, one a reader can look up (worktree, fast-forward, exit code, completion criterion); it is a name the program or tracker depends on, copied verbatim (a command, event, field, label, or a heading a reader finds by position); or it is the name an upstream skill gives its own concept. A coined word does not qualify by appearing in a heading. Everything else is ordinary dictionary words. A new term is coined only where none of these fits, and is defined in one sentence, in bold, where it first appears. A metaphor is a finding unless it is a leading word in `SKILL.md`'s sense. An undefined coinage, a colloquial phrase, a word whose meaning you cannot state in one sentence, and one word spelled two ways are findings.
- Skill text is English. Another language appears only inside a name the program uses, copied verbatim (a heading a script writes, a label).
- The glossary is held to the same standard. An entry that makes a coined or vague word official, or whose `_Avoid_` line bans the established term, is a finding: the term, the entry and every skill using it change together. An entry's facts are checked against the file it cites as `_Home_`; an entry citing a file that does not hold those facts is a finding. A behaviour rule found only in the glossary is evidence of intended behaviour (see [Load and disclosure](#load-and-disclosure)).
- A heading or step that another skill finds by position is cited by producer and reader as the same literal, by title rather than by number.
- In MMW the glossary is `CONTEXT-MAP.md` and `docs/contexts/<name>/CONTEXT.md`.

### Hand-offs

A **hand-off** is an edge A → B: skill or agent A leaves something that B reads or waits for.

- What A leaves (the artifact, where, under which name or heading) is what B reads, by the same name. The hand-off is broken where they differ, where B needs something A never produced, or where A produces something (a section, a field, a child issue) that B reads under a condition A does not share.
- For every outcome A produces in use, name who reads it and what they do next. An outcome nobody acts on, or one that reaches the reader looking like success, is a broken hand-off.
- Between two sessions, B gets a completion signal it actually receives (an event, a wake, a command that blocks until A is done).
- Each event gets one instruction across the set. Two skills or scripts that tell the agent different things about the same event (the same exit code, the same wake, the same "done") contradict each other; the fix goes in the skill that owns the event.
- Each skill ends by naming what comes next, or the caller it returns to, and the skill it returns to has an entry for an agent arriving that way.
- A sentence written for one caller can misread under another. When skill X runs inside skill Y, reread X's general statements in Y's situation.
- Read each task for **unguided choices**: points where the agent must choose and the text says nothing, which hands the choice to the model's own habits. Fill each one with the criterion, or make it an explicit branch. A choice any reasonable model makes the same way is not unguided; writing it down is a no-op.
- Invoking another skill, in MMW: name the skill and the job, never an install path; the agent holding a skill resolves its scripts. To take its vocabulary and apply it in place, read its `SKILL.md`; to run it in a separate context, ask for the host's own general-purpose subagent and have it use the skill. A file in another skill is named by skill and file ("the `ui-acceptance` skill's `references/story-parity.md`"). A skill directory holds no copy of, or link to, another skill's files.
- A hard dependency (the skill produces wrong output without some setup) gets one line naming what to run, as upstream's `to-spec` names `setup-matt-pocock-skills`; a soft one (the setup only sharpens output) gets a general mention.

### Prompts written for other agents

- A start prompt carries only what is known when the agent is started (the ticket number, a base commit, where the task came from). Rules reach the agent through the skill it loads; a ticket or spec is named and read from the tracker, not retold. A packet a model writes from a template counts as a start prompt, and the template lists everything the receiver needs.
- Everything an agent must apply reaches it by one of two means: a skill or file its prompt tells it to load, or text pasted into the prompt. A rule the prompt says the agent applies, delivered by neither, is a broken hand-off. A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data.
- A subagent's brief states what it returns and its length (upstream `code-review`: "Under 400 words"), so its report fits the caller's attention.

### Upstream skills

An **upstream skill** (one kept in an upstream subtree, or adapted from one) enters the set as its authors wrote it. The set's work is to connect it to the workflow: what reaches it, what it hands on, which repository rule it must obey. Its text changes only where the change alters what the agent does: a step, their order, where or with what it works, what it produces or hands over. A rewording for style, clarity or the set's voice is a finding, fixed by restoring the upstream text.

- Diff the skill against upstream (the squash-commit command is in `mmw-v2/merge-notes/README.md`). Every changed paragraph maps to a merge-note entry stating the behaviour it changes. A paragraph with no entry, or whose entry states only wording, goes back to upstream's text. A skill adapted from upstream without a merge-note is a finding.
- The merge-note's entries agree with each other and with the current text. An entry that still states a replaced rule is a finding: the next upstream pull would restore that rule.
- Connect outside the upstream text first: in the set's own skills, in a reference file added beside the upstream ones, in the line a caller reads. An upstream sentence changes only when an agent reading it would act wrongly in this workflow even with the connecting text in place.
- Checks on style (completion-criterion lines, the shape of a description, vocabulary preferences) apply to the set's own text. Upstream sentences are judged on whether they work in the workflow.
- When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text. Its upstream original remains the measure of length: an addition earns its words by a judgement the workflow needs that upstream did not.

### Paths, tokens and host neutrality

- A skill's scripts are resolved by the agent holding the skill, from its own `SKILL.md`, as `scripts/<…>`.
- A skill refers to its own or a sibling skill's scripts through a **script token**, a `<name>` standing for an executable or a script directory. Each token is defined once, in a section headed `` ## Resolve `<token>` once `` that says what the token expands to in every command below and resolves it from the file's own location, and says the path differs by machine and by host; one section may define several tokens. The body carries no bare relative path and no token used before or without its definition. A token naming an executable (`<engine>`, `<dispatch>`, `<events.py>`, `<lease.py>`, `<release>`) resolves to exactly one file across the set, because an agent holding several skills reads all their vocabulary as one. The directory token `<scripts>` is each skill's own; a skill reaching into another skill's directory names it (`<ui-acceptance scripts>`). Placeholders for values (`<n>`, `<spec>`) are not script tokens.
- An absolute path in skill text is legal in three cases: a fixed user-level location (`~/.mmw/models.json`, `~/.agents/skills`, `~/.claude/skills`), which has no relative spelling; a token's runtime expansion, which stays a token in the text; a path the run made itself with `mktemp`. Any other absolute path is a finding.
- A ticket's `CHECK:` line names no path: a shell runs it with no agent in between, `verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on that shell's `PATH`, so a judge is named bare. Its shapes are in the `ui-acceptance` skill's `references/boundary-check.md` and `references/story-parity.md`.
- One text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability ("a host that cannot hold a turn open", "a host that can run subagents"). The runner is the one `models.py runner` selects; the text states that and assumes nothing past it. A skill is named in prose by its directory name, as `the X skill`; a `/X` slash invocation is one host's syntax. A session command (emptying a session's context, compressing it into a summary) is written as the action, and the file that names one carries this sentence once: `Emptying a session's context and compressing it into a summary both exist on every host, under a different name on each; use the one your host gives you.`

The check is a `grep` of every `SKILL.md`, description and reference (this file excepted) for: an absolute path outside the three cases, and any `~/.agents/skills` path in prose; a relative path that climbs out of the skill directory; a script token without its definition; a path in a `CHECK:` line; a host name (`claude`, `codex`, `grok`, `cursor`, `pi`), a tool name (`the Skill tool`, `the Task tool`), a `/name` slash invocation, or a runner name (`orca`, `herdr`, `paseo`).

### Rules and completion criteria

- In the set's own text, a step or a section that directs action without a completion criterion is a finding, and so are two different statements of what "done" means for one task. A skill this repository wrote states the criterion on a line beginning `Done when`.
- When a check `grep`s the files it scans for a forbidden token, the token appears nowhere in those files, including negated sentences and comments.

### Examples

- An example uses a neutral domain (a notes app). An example naming a real product, a spec or issue number, or a past run is a finding: an agent reading it takes the specifics as requirements.
- An example value is labelled as an example; the rule it illustrates is the authority.
- A good and a bad example side by side are used where a misreading is likely.

### Refusals and output an agent reads

- A refusal has the three parts `AGENTS.md` names (what happened, with one checkable fact; why; what to do next), and the next step fits the skill that receives it. "Could not check" and "checked, it is fine" are different messages.
- Hosts cut long output before the agent sees it, so the next step sits in the first lines.
- The suggested next step is safe to run as written.

## Editing

- A fix removes, merges, moves or simplifies before it adds. A fix that adds a mechanism (a check, a field, an exit code, a verb, a guarding sentence) names the run in which the failure occurred.
- Fix at the level of the finding. A wording finding is fixed in the sentence: improve the sentence that misled, since a new sentence added to correct an old one leaves both. A load finding is fixed in the structure: move, merge, split at a branch, or delete whole sections, carrying each sentence that still applies across verbatim. Sentences the finding does not touch stay byte for byte.
- Asked to "streamline", an agent shortens and cuts function with it, so every deletion is tested against the agent's behaviour: walk the task after the edit and confirm it still reaches its completion criterion with nothing guessed (`SKILL.md` `## Pruning`).
- Before a rename, move or deletion, `grep` the set for the heading, file name, token and term you are changing, and change every file that states it in the same edit: skills, references, scripts, templates, tests, merge-notes. Callers cite sections by name, tests assert on refusal text and on skill text, and `mmw-v2/board/` imports some scripts by file path.
- A changed upstream skill gets its merge-note entry rewritten in place. A change that invalidates a consuming repository's contract, `CHECK:` or `.mmw/target.json` gets a downstream-note.
- Text taken from another source keeps its authors' wording (see [Upstream skills](#upstream-skills)). Excerpts are quoted verbatim and collected into one block before they are placed; finding places for them first splits the source apart.
- The file states what is true now; what changed and why goes to the commit message and the report.

## Verifying

- Run the smallest test suite that covers the scripts and texts you touched (`mmw-v2/tests/<name>/run.sh`). Green tests prove the scripts, not that the text reads well; report them on a separate line.
- The text is proven by a run: a fresh agent given only the trigger and a real job (one real ticket) does the task. Watch which files it opens, where it guesses, and where it stops before the completion criterion. A sentence present in the text is not a behaviour observed; a claim that the text now changes behaviour is unverified until such a run shows it.

Done when the suites covering the touched files pass, and every changed task, walked again, still reaches its completion criterion, with its load before and after reported.

## Upstream examples

mattpocock's own skills show several checks done well. The in-repository copies under `mmw-v2/upstream/skills/` carry this repository's edits; read the original from the latest squash commit (found as `mmw-v2/merge-notes/README.md` says), with `git show <commit>:skills/<bucket>/<skill>/<file>`. The in-progress `retro` below is upstream's, not MMW's own `retro` skill.

| Check | Upstream file | What to look at |
| --- | --- | --- |
| Descriptions | `engineering/wizard/SKILL.md`, `engineering/prototype/SKILL.md` | the trigger branches; one explicit non-trigger |
| Load and disclosure | `engineering/prototype/SKILL.md` with `LOGIC.md` and `UI.md` | each branch file whole, each naming the other branch for a reader who took the wrong one |
| Load and disclosure | `engineering/codebase-design/SKILL.md` `## Going deeper` | each pointer carries its condition |
| Load and disclosure | `productivity/to-questionnaire/SKILL.md`, `engineering/to-spec/SKILL.md` | the template stays inline because every run writes one |
| Scripts and judgement | `engineering/wizard/SKILL.md` | "The delightful UX is already solved by template.sh ... Your job is only to scope the procedure and author its stages" |
| Scripts and judgement | `engineering/code-review/SKILL.md` step 3 | the smell baseline: each item is what it is and how to fix it, marked "always a judgement call" |
| Scripts and judgement | `engineering/code-review/SKILL.md` step 1 | "A bad ref or empty diff should fail here, not inside two parallel sub-agents": one early check, placed where it saves the most |
| Scripts and judgement | `in-progress/retro/SKILL.md` | a mechanical violation gets a deterministic check; the standards document keeps only judgement calls |
| Vocabulary | `engineering/codebase-design/SKILL.md` `## Glossary`; `engineering/improve-codebase-architecture/HTML-REPORT.md` `## Tone` | "Use these terms exactly"; "Use exactly" / "Never substitute" |
| Hand-offs | `productivity/grilling/SKILL.md` | facts (look them up) kept apart from decisions (put them to the user); the end stated as "the frontier is empty" |
| Hand-offs | `engineering/to-spec`, `to-tickets`, `triage` against `tdd`, `diagnosing-bugs` | a hard dependency names `setup-matt-pocock-skills` in one line; a soft one only says to read the domain glossary if it exists |
| Prompts | `engineering/code-review/SKILL.md` step 4 | the Standards subagent gets the smell baseline "pasted in full (the sub-agent has no other access to it)", and a length limit |
| Examples | `engineering/triage/AGENT-BRIEF.md` | good and bad briefs side by side, with why the bad one fails |
