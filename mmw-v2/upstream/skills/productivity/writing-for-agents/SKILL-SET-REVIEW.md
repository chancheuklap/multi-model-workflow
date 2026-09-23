# Writing and reviewing a skill set

The branch of [`writing-for-agents`](SKILL.md) for a **skill set**: the skills one install list ships (in MMW, `mmw-v2/skills.txt`), with their references and scripts, run by agents that each load only their own part. `SKILL.md` gives the levers and the names of the failure modes; this file gives the review method and the checks that only show when you read across skills. The checks are also the rules for writing: whoever writes or edits a skill in the set applies them to the passage in hand.

In MMW this file is the only home of the rules for skill text. The repository's other written rules (install, scripts, landing, runtime) are in `AGENTS.md`, and the rules for pulling upstream subtrees are in `mmw-v2/merge-notes/README.md`; skills fit those, and text inside an upstream subtree also follows that subtree's own `AGENTS.md`. The set's glossary states no rules: its entries are reviewed like any other text (see [Vocabulary](#vocabulary)).

## The review

The review is a **cognitive walkthrough** (the usability-inspection method): for each task an agent does with the set, you read and run what that agent would, in its order, holding nothing it would not hold. A **task** is one job an agent is entered into a skill to do (consult an advisor, publish a spec, work one ticket); a skill entered in the middle of a bigger task is walked from its entry to its return. A skill is judged by how an agent uses it inside its tasks and how it joins the skills before and after; a per-file defect count misses both.

Scope: the skills under review, and each upstream skill's differences from upstream. The scripts those skills call are inside the walk wherever they live; other skills are read only where the scoped skills hand work to them or take it back. A review of part of the set lists the tasks it left out.

Run only commands that write nothing and start no session (`--help`, a script's read-only verbs); when you cannot tell whether a command writes, read its source instead.

1. **List the tasks.** A skill is entered three ways: a branch its description triggers on; a prompt that starts an agent into it (built by a script, or written by a model from a template); a sentence in another skill or script that sends the agent to it by name or by step. `grep` the skill's name across every skill and script in the set for the third kind, then read the scoped skills for entries described without the name. Done when every entry of every skill in scope maps to a task, or is listed as out of scope.
2. **Walk each task.** Start from what the agent holds at entry: the description, the start prompt, or the text that sent it. Open only what the text in front of you points to. Where the text says what a script or CLI does, accepts, reads or prints, check it against the source or `--help`. Record each file you had to open and why, each term you had to resolve, each choice you made without guidance, and where the text ends before the task does. Walk every outcome, not only success: each refusal and exit code, a failure reported under a success exit code, a retry, a resume, a re-entry later in the task. Done when each task reaches its completion criterion or a recorded finding.
3. **Apply the per-task checks** below (every section except Vocabulary, Hand-offs and Upstream skills) to what each task read.
4. **Read across the scoped skills** for the three checks no single task shows: [Vocabulary](#vocabulary), [Hand-offs](#hand-offs) and [Upstream skills](#upstream-skills). Read them end to end; a concept that is described instead of named does not show up in `grep`. Glossary entries are checked for the terms the walked tasks use.
5. **Report** before any edit; each finding carries its fix as a proposal. In this order:
   - Tasks walked, one line each: who, entering from which text, to which completion criterion.
   - Findings by severity, judged by effect. **High**: an agent following the text ends wrong or stuck. **Medium**: the agent ends right but at extra reading or work, or will stop ending right when one copy of a duplicated rule changes. **Low**: wording that misleads no current run. An unguided choice is rated by its worst likely guess. Each finding carries the task, the address (file, heading, line numbers), the failure mode (a term from `SKILL.md`, or a heading or bold term of this file), the quoted evidence, and the fix; a file you had to open is listed under the finding it caused.
   - Findings in files no running agent reads (glossary, merge-notes, ADRs), listed apart.
   - Decisions for the user: what an end user sees, what happens to money, scope, what cannot be undone, what an unattended agent may change on the machine, and whether an upstream skill is still treated as upstream.
   - Not walked, not verified, and checks that did not apply.

## Checks

### Descriptions

- A description carries the trigger and nothing else: what the skill is, and the branches on which to load it (`SKILL.md` `## Context pointers`). Routing (which role's file, which row of a command table, which reference), usage, process and outputs belong to the body; a description carrying them is a finding. A branch naming the role an agent was started as ("when you were started as the advisor") is a trigger.
- Read every description in the set side by side, also in a partial review. Two descriptions that claim the same job are a conflict. A caller and the skill it hands to may share a trigger word when each description names only its own part of the job.
- A description names no host and no runner: every host scans it into its system prompt, so one name ties the skill to that host or runner. A runner that cannot start is refused by its script at run time.
- A skill this repository wrote has exactly two frontmatter keys, `name` and `description`, and no host-side manifest beside it (upstream skills keep their `agents/openai.yaml`), so its name and description have one authority. The `disable-model-invocation` pairing on upstream skills is in `mmw-v2/merge-notes/README.md`.
- A `description` holding a colon followed by a space breaks YAML; quote it. Check it with a YAML parser, since some hosts are lenient and some are not.

### Disclosure: split by moment

A **moment** is a point in a task that needs one coherent set of material and that a given run may reach without the others: a role arriving, one branch of a choice, a re-entry later in the same task. Inside a moment the agent follows steps (`SKILL.md` `## Steps and completion criteria`).

- `SKILL.md` holds what every task passes through, plus the table that sends each reader to its moment. Each reference file holds one moment whole, and is named in `SKILL.md` with the condition for opening it.
- Count how many times one agent enters the skill in one task. Entered once: one reference per arriving role. Entered at several moments: one reference per moment, and the table that finds the reader's moment comes first in `SKILL.md`, before any step with side effects, so a re-entering agent does not repeat them.
- A pointer is reached at or before the first step that needs its material. A rule the agent meets only after acting on the step it governs is a finding.
- A pick-one-of-N choice is a table. A numbered list reads as a pipeline to run in full.
- Findings: a reference every task opens (inline it, unless `SKILL.md` would then sprawl); a `SKILL.md` section only one branch reads (move it to a reference); a task that opens three files because the references were split by topic (merge them by task).

### Co-location: one moment, one file

- Once `SKILL.md` has sent the agent to its moment, the file it opened holds the rule, the format, the command, the known pitfall and the completion criterion. Opening a second file of the same skill for that moment is a finding. Opening another skill is a hand-off, checked under [Hand-offs](#hand-offs).
- A rule sits in the text of the agent that must follow it. A rule for the worker written only in the main agent's skill, in a script's comment, in the glossary, in a merge-note, or in this file reaches no worker.
- An artifact's definition, check, explanation and use belong to one skill: the skill whose agent uses the artifact. A step that says "read two documents in another skill" is fixed by moving them there.
- Material works only from text the agent loads. A profile note, a comment thread, a conversation, or an artifact link the next agent cannot open carries nothing forward; what the next agent needs goes in what it will read (a spec's body, a ticket's fixed headings).
- The text makes sense to an agent that holds nothing else: no reference to another session, to memory, or to a word coined while writing it. A statement of fact is true: a rule the agent keeps is written as a rule, not as a fact about the system.

### Vocabulary

- One word, one meaning across the whole set, placeholders and tokens included. Two meanings for one word are fixed at the source (rename in the skill or script, record it in the merge-note), not by fencing each meaning inside one skill. When two upstream skills define one term differently, the set picks one meaning and records the choice.
- A term earns its place in one of three ways: it is the established term of its field, one a reader can look up (worktree, fast-forward, exit code, completion criterion); it is a name the program or tracker depends on, copied verbatim (a command, event, field, label, or a heading a reader finds by position); or it is the name an upstream skill gives its own concept. A coined word does not qualify by appearing in a heading. Everything else is ordinary dictionary words. A new term is coined only where none of these fits, and is defined in one sentence, in bold, where it first appears. A metaphor is a finding unless it is a leading word in `SKILL.md`'s sense. An undefined coinage, a colloquial phrase, a word whose meaning you cannot state in one sentence, and one word spelled two ways are findings.
- The glossary is held to the same standard. An entry that makes a coined or vague word official, or whose `_Avoid_` line bans the established term, is a finding: the term, the entry and every skill using it change together. An entry's facts are checked against the file it cites as `_Home_`; an entry citing a file that does not hold those facts is a finding. A behaviour rule found only in the glossary is evidence of intended behaviour (see Co-location).
- A heading or step that another skill finds by position is cited by producer and reader as the same literal, by title rather than by number.
- In MMW the glossary is `CONTEXT-MAP.md` and `docs/contexts/<name>/CONTEXT.md`.

### Hand-offs

A **hand-off** is an edge A → B: skill or agent A leaves something that B reads or waits for.

- What A leaves (the artifact, where, under which name or heading) is what B reads, by the same name. The hand-off is broken where they differ, where B needs something A never produced, or where A produces something (a section, a field, a child issue) that B reads under a condition A does not share.
- For every outcome A can produce (success, each refusal or exit code, a failure reported inside a success exit code, a report that it could not do its job), name who reads it and what they do next. An outcome nobody acts on, or one that reaches the reader looking like success, is a broken hand-off. When the reader answers from a closed list (for example `accepted` or `rejected` for each item), the list covers every state A can create.
- Between two sessions, B gets a completion signal it actually receives (an event, a wake, a command that blocks until A is done), and the text names who stops the session A runs in.
- A retry works from the state the first attempt left: a script that refuses input its own earlier write changed, or a retry step nobody states, is a finding.
- Each event gets one instruction across the set. Two skills or scripts that tell the agent different things about the same event (the same exit code, the same wake, the same "done") contradict each other; the fix goes in the skill that owns the event.
- Each skill ends by naming what comes next, or the caller it returns to, and the skill it returns to has an entry for an agent arriving that way.
- A sentence written for one caller can misread under another. When skill X runs inside skill Y, reread X's general statements in Y's situation.
- Read each task for **unguided choices**: points where the agent must choose and the text says nothing, which hands the choice to the model's own habits. The fix fills each one or makes it an explicit branch.
- Invoking another skill, in MMW: name the skill and the job, never an install path; the agent holding a skill resolves its scripts. To take its vocabulary and apply it in place, read its `SKILL.md`; to run it in a separate context, ask for the host's own general-purpose subagent and have it use the skill (`mmw-v2/merge-notes/README.md` `## host 中立`). A file in another skill is named by skill and file ("the `ui-acceptance` skill's `references/story-parity.md`").
- A hard dependency (the skill produces wrong output without some setup) gets one line naming what to run; a soft one (the setup only sharpens output) gets a general mention.

### Prompts written for other agents

- A start prompt carries only what is known when the agent is started (the ticket number, a base commit, where the task came from). Rules reach the agent through the skill it loads; a ticket or spec is named and read from the tracker, not retold. A packet a model writes from a template counts as a start prompt, and the template lists everything the receiver needs.
- Everything an agent must apply reaches it by one of two means: a skill or file its prompt tells it to load, or text pasted into the prompt. A rule the prompt says the agent applies, delivered by neither, is a broken hand-off. A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data.

### Upstream skills

An **upstream skill** (one kept in an upstream subtree, or adapted from one) enters the set as its authors wrote it. The set's work is to connect it to the workflow: what reaches it, what it hands on, which house rule it must obey. Its text changes only where the change alters what the agent does: a step, their order, where or with what it works, what it produces or hands over. A rewording for style, clarity or the set's voice is a finding, fixed by restoring the upstream text.

- Diff the skill against upstream (the squash-commit command is in `mmw-v2/merge-notes/README.md`). Every changed paragraph maps to a merge-note entry stating the behaviour it changes. A paragraph with no entry, or whose entry states only wording, goes back to upstream's text. A skill adapted from upstream without a merge-note is a finding.
- The merge-note's entries agree with each other and with the current text. An entry that still states a replaced rule is a finding: the next upstream pull would restore that rule.
- Connect outside the upstream text first: in the set's own skills, in a reference file added beside the upstream ones, in the line a caller reads. An upstream sentence changes only when an agent reading it would act wrongly in this workflow even with the connecting text in place.
- Checks on style (completion-criterion lines, the shape of a description, vocabulary preferences) apply to the set's own text. Upstream sentences are judged on whether they work in the workflow.
- When fewer than half of a skill's lines are upstream's, it is reviewed as the set's own text, and the report asks the user whether it is still treated as upstream.

### Scripts and prose

- A script does the deterministic work; the agent makes the judgement. Where a script decides, the text gives the command, the moment to run it, and what to do on each outcome that needs a different action. The complete flag list and exit-code table stay beside the script (its `--help`, its header, the skill that owns it). Text that assigns the script's writes to the agent is a finding.
- Where only understanding can decide (what counts as X, which of two readings applies, when a step is finished), the words go there: the criterion, the exact rule the script will apply when it later judges the agent's output, and a contrasting pair of examples when a misreading is likely.
- A rule a script could check exactly becomes a check (a lint, a refusal, a test), not a sentence. A numeric limit is enforced by the mechanism; models do not copy literal numbers reliably.
- Programs branch on exit codes and fields; the refusal's wording is for the agent. Rewording a message changes no behaviour.
- The text states which revision or checkout a script reads when that can differ from the one the agent is looking at, and where a file the agent writes for a script goes.

### Paths, tokens and host neutrality

- A skill's scripts are resolved by the agent holding the skill, from its own `SKILL.md`, as `scripts/<…>`.
- A skill refers to its own or a sibling skill's scripts through a **script token**, a `<name>` standing for an executable or a script directory. Each token is defined once, in a section headed `` ## Resolve `<token>` once `` that says what the token expands to in every command below and resolves it from the file's own location, and says the path differs by machine and by host; one section may define several tokens. The body carries no bare relative path and no token used before or without its definition. A token naming an executable (`<engine>`, `<dispatch>`, `<events.py>`, `<lease.py>`, `<release>`) resolves to exactly one file across the set, because an agent holding several skills reads all their vocabulary as one. The directory token `<scripts>` is each skill's own; a skill reaching into another skill's directory names it (`<ui-acceptance scripts>`). Placeholders for values (`<n>`, `<spec>`) are not script tokens.
- An absolute path in skill text is legal in three cases: a fixed user-level location (`~/.mmw/models.json`, `~/.agents/skills`, `~/.claude/skills`), which has no relative spelling; a token's runtime expansion, which stays a token in the text; a path the run made itself with `mktemp`. Any other absolute path is a finding.
- A ticket's `CHECK:` line names no path: a shell runs it with no agent in between, `verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on that shell's `PATH`, so a judge is named bare. Its shapes are in the `ui-acceptance` skill's `references/boundary-check.md` and `references/story-parity.md`.
- One text serves every host and every runner: no host is the default, nothing branches on a host's or runner's name, and a difference in capability is written as the capability ("a host that cannot hold a turn open", "a host that can run subagents"). Tonight's runner is the one `models.py runner` selects; the text states that and assumes nothing past it. A skill is named in prose by its directory name, as `the X skill`; a `/X` slash invocation is one host's syntax. The three rewrites this forces on upstream text are in `mmw-v2/merge-notes/README.md` `## host 中立`.

The check is a `grep` of every `SKILL.md`, description and reference for: an absolute path outside the three cases, and any `~/.agents/skills` path in prose; a relative path that climbs out of the skill directory; a script token without its definition; a path in a `CHECK:` line; a host name (`claude`, `codex`, `grok`, `cursor`, `pi`), a tool name (`the Skill tool`, `the Task tool`), a `/name` slash invocation, or a runner name (`orca`, `herdr`, `paseo`).

### Body content

A skill body carries what the agent will execute now. These belong elsewhere:

| In the body | Its home |
| --- | --- |
| a dated measurement, "tested on" | the script header or a research file |
| the maintainer's reason for a design | an ADR |
| what changed, what used to be true, "no longer", "now" | the commit message |
| a source line ("from chapter 3 of …"), an issue number the reader cannot use | nowhere |
| a branch no run can reach, a note telling the agent to ignore something | nowhere |

These stay, though a trimming pass reads them as noise: a sentence that prevents a known misuse (a script's path differs by machine and by host, which stops an agent from writing the resolved path down; keep the winning prototype running as the reference while pages are drawn); an example value that is the field's format (`conversation 2026-09-18`); a prohibition that guards against real damage, paired with its positive target; a reason the agent needs to decide an edge case. Other agents copy the style of what they read, so the body is written plainly.

### Rules and completion criteria

- A rule states a fact, or changes what counts as done. A procedure added to enforce it gets skipped. When a rule fails in use, rewrite the text that set the agent's starting point.
- An action beats a description of an attitude: "`grep` every caller" is carried out where "trace the flow end to end" is not.
- In the set's own text, a step or a section that directs action without a completion criterion is a finding, and so are two different statements of what "done" means for one task. A skill this repository wrote states the criterion on a line beginning `Done when`.
- When a check `grep`s the files it scans for a forbidden token, the token appears nowhere in those files, including negated sentences and comments.

### Examples

- An example uses a neutral domain (a notes app). An example naming a real product, a spec or issue number, or a past run is a finding: an agent reading it takes the specifics as requirements.
- An example value is labelled as an example; the rule it illustrates is the authority.
- A good and a bad example side by side earn their place where a misreading is likely.

### Refusals and output an agent reads

- A refusal has the three parts `AGENTS.md` names (what happened, with one checkable fact; why; what to do next), and the next step fits the skill that receives it. "Could not check" and "checked, it is fine" are different messages.
- Hosts cut long output before the agent sees it, so the next step sits in the first lines.
- The suggested next step is safe as written in every state that produces the refusal, including an unattended run with nobody to ask.

## Editing

- Change the passage, not the file: most findings are fixed by a precise edit. Improve the sentence that misled; a new sentence added to correct an old one leaves both.
- Asked to "streamline", an agent shortens and cuts function with it, so every deletion is tested against the agent's behaviour (`SKILL.md` `## Pruning`).
- Before a rename, move or deletion, `grep` the set for the heading, file name, token and term you are changing, and change every file that states it in the same edit: skills, references, scripts, templates, tests, merge-notes. Callers cite sections by name (the `manage-agents-md` skill cites this skill's `## Context pointers`, `## Pruning` and `## Leading words`), tests assert on refusal text, and `mmw-v2/board/` imports some scripts by file path.
- A changed upstream skill gets its merge-note entry rewritten in place. A change that invalidates a consuming repository's contract, `CHECK:` or `.mmw/target.json` gets a downstream-note.
- Text taken from another source keeps its authors' wording (see [Upstream skills](#upstream-skills)). Excerpts are quoted verbatim and collected into one block before they are placed; finding places for them first splits the source apart.
- The file states what is true now; what changed and why goes to the commit message and the report.
- In MMW, an edit reaches no host until it is released (`AGENTS.md` `## Gotchas`), and `install.sh` runs only when the user explicitly authorises it.

## Verifying

- Run the smallest test suite that covers the scripts you touched (`mmw-v2/tests/<name>/run.sh`). Green tests prove the scripts, not that the text reads well; report them on a separate line.
- The text is proven by a run: a fresh agent given only the trigger and a real job (one real ticket) does the task. Watch which files it opens, where it guesses, and where it stops before the completion criterion.

## Upstream examples

mattpocock's own skills show several checks done well. The in-repository copies under `mmw-v2/upstream/skills/` carry this repository's edits; read the original from the latest squash commit (`git log --oneline --grep "Squashed 'mmw-v2/upstream/'"`, then `git show <commit>:skills/<bucket>/<skill>/<file>`). The in-progress `retro` below is upstream's, not MMW's own `retro` skill.

| Check | Upstream file | What to look at |
| --- | --- | --- |
| Descriptions | `engineering/wizard/SKILL.md`, `engineering/prototype/SKILL.md` | the trigger branches; one explicit non-trigger |
| Disclosure | `engineering/prototype/SKILL.md` with `LOGIC.md` and `UI.md` | each branch file whole, each naming the other branch for a reader who took the wrong one |
| Disclosure | `engineering/codebase-design/SKILL.md` `## Going deeper` | each pointer carries its condition |
| Disclosure | `productivity/to-questionnaire/SKILL.md` | the template stays inline because every run writes one |
| Vocabulary | `engineering/codebase-design/SKILL.md` `## Glossary`; `engineering/improve-codebase-architecture/HTML-REPORT.md` `## Tone` | "Use these terms exactly"; "Use exactly" / "Never substitute" |
| Hand-offs | `productivity/grilling/SKILL.md` | facts (look them up) kept apart from decisions (put them to the user), so the interview still works when another skill runs it inside a ticket |
| Hand-offs | `engineering/to-spec`, `to-tickets`, `triage` against `tdd`, `diagnosing-bugs` | a hard dependency names `setup-matt-pocock-skills`; a soft one only says to read the domain glossary if it exists |
| Prompts | `engineering/code-review/SKILL.md` step 4 | the Standards subagent gets the smell baseline "pasted in full (the sub-agent has no other access to it)" |
| Scripts and prose | `engineering/wizard/SKILL.md` | "The delightful UX is already solved by template.sh ... Your job is only to scope the procedure and author its stages" |
| Scripts and prose | `in-progress/retro/SKILL.md` | a mechanical violation gets a deterministic check; the standards document keeps only judgement calls |
| Examples | `engineering/triage/AGENT-BRIEF.md` | good and bad briefs side by side, with why the bad one fails |
