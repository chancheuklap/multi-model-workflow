### Review the skill set

**You own the review. Nothing but the report is written until the user says go.**

A review walks each task an agent does with the set, then holds what each task read to the checks in the `writing-for-agents` skill's `SKILL-SET-RULES.md`.

Scope: what the user names (skills, files inside one, or a workflow: its playbooks, the mode's route lines and sections their steps rely on, every file their steps name, and the scripts those files run), or the whole set when they name nothing; and each upstream skill's differences from upstream. The scripts those skills call are inside the walk wherever they live, including every message a script prints for an agent (refusals, `--help`, the start prompts it builds). Other skills are read only where the scoped skills hand work to them or take it back. A review of part of the set lists the tasks it left out.

Until **Fix every finding** runs, run only commands that write nothing and start no session (`--help`, a script's read-only verbs); when you cannot tell whether a command writes, read its source instead.

Two kinds of finding need two kinds of evidence:

- A finding about **load** (material read that the step does not use, a jump, a fragment, duplication, a cache, a no-op, over-specification) happens on every run of the task. It carries the task and the numbers from the walk: the files, the words, the skills crossed.
- A **failure finding** (the agent ends wrong or stuck) names how it occurs where the set is actually used: the user's setup, the tracker history of past runs, or an input a script receives in normal use. A path nobody takes, a state no normal input produces, and a failure that already stops with a refusal the agent acts on are not failures. Text or a mechanism written to guard such a path is itself a finding, under `### Redundancy and bloat` of the `writing-for-agents` skill's `SKILL-SET-RULES.md`.

Every finding is fixed. There are no severity levels: a finding is either established by its evidence and fixed, or it is not a finding.

1. **List and walk the tasks.** List the tasks in scope and walk each, as the `writing-for-agents` skill's `WALKING-A-SKILL-SET.md` `### List the tasks` and `### Walk each task` say.
   Done when the `Done when` lines of both those sections hold.
2. **Apply the per-task checks.** Hold what each task read to the `writing-for-agents` skill's `SKILL-SET-RULES.md` `## Checks`; `### Vocabulary`, `### Hand-offs` and `### Upstream skills` are read across in **Read across the scoped skills**.
   Done when each check has been applied to each task, or noted as not applying.
3. **Read across the scoped skills.** Read them for the three checks no single task shows: `### Vocabulary`, `### Hand-offs` and `### Upstream skills`. Read them end to end; a concept that is described instead of named does not show up in `grep`. Glossary entries are checked for the terms the walked tasks use. Check each passage against the `writing-for-agents` skill's `SKILL-SET-COMPONENTS.md`: one that sits in a component other than the one its question assigns is a finding. Read across the set for fact 7 of `## What skill text is for`: a method, rule, definition, map or function stated in a second place is a finding, and the mode's route lines and the playbooks, read in the order a task takes, leave no gap and no moment claimed twice. List the terms the scoped skills use as concepts against the glossary: every concept has one entry, one name, and a name chosen as `### Vocabulary` orders. Read each skill also as its fresh agent: from the skill alone, can it say what the work is for, who uses what it produces, and what a shallow result costs? Where it cannot, that is a finding, fixed by writing the sentences that pass the test of fact 1. Then trace each intent of the `writing-for-agents` skill's `DESIGN-INTENTS.md` that bears on the scope (its `Home:` line names a file in scope, or a walked step does the work the intent governs): (1) which file carries it; (2) at which step the acting agent reads it; (3) whether a script enforces what a script could check; (4) whether the hand-off it relies on has one shape; (5) whether every file states it the same way. An intent nothing in scope carries, and text or a script that does the opposite, are findings; a departure that file lists is not.
   Done when every scoped skill has been read end to end, and every intent bearing on the scope has been traced.
4. **Report.** Before any edit, write the review into the file `docs/reviews/<YYYY-MM-DD>-<slug>/README.md` of the repository, the slug naming what was reviewed, in this order:
   - The load table: one row per task walked: who, entering from which text, to which completion criterion; files read, words read, skills crossed, and words read that the run did not use.
   - The findings, grouped by task, then the cross-set findings. Each carries the task, the evidence (the load numbers, or how the failure occurs), the address (file, heading, line numbers), the failure mode (a term from the `writing-for-agents` skill's `SKILL.md`, or a heading or bold term of the `writing-for-agents` skill's `SKILL-SET-RULES.md`), the intent of its `DESIGN-INTENTS.md` it breaks, the quoted text, and the fix.
   - Findings in files no running agent reads (glossary, ADRs), listed apart.
   - Decisions for the user: only a choice that changes what a customer sees, what happens to money, the scope, or what cannot be undone. Any other choice is the reviewer's: make it and give the reason in the fix.
   - Not walked, not verified, and checks that did not apply.

   Done when that `README.md` holds these parts in this order, and every finding carries its evidence and its fix.
5. **Fix every finding.** Run this step when the user asked for the fixes, or has read the report and said go; otherwise the review ends at **Report**, and this step is skipped. Run **Authoring or modifying a skill** on the findings, each with the address, the failure mode and the fix the report gives it. Its **Walk a real task** is skipped: the review's walk is the walk of these fixes, and no task is walked again. Its **Deliver** commits the fixes. A finding that waits on a decision the user holds stays in the report and does not hold the delivery back.
   Done when every finding is fixed or is a decision the user holds, and the fixes are committed.

**Reply:** the report's path; the load table; each finding with its fix, or the decision it waits on; what was not walked or not verified.
