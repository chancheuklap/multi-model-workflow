# Reviewing a skill set

The review is a **cognitive walkthrough** (the usability-inspection method): for each task an agent does with the set, you read and run what that agent would, in its order, holding nothing it would not hold. A **task** is one job an agent is entered into a skill to do (consult an advisor, publish a spec, work one ticket); a skill entered in the middle of a bigger task is walked from its entry to its return. A skill is judged by how an agent uses it inside its tasks and how it joins the skills before and after; a per-file defect count misses both.

Scope: the skills under review, and each upstream skill's differences from upstream. The scripts those skills call are inside the walk wherever they live, including every message a script prints for an agent (refusals, `--help`, the start prompts it builds). Other skills are read only where the scoped skills hand work to them or take it back. A review of part of the set lists the tasks it left out.

Run only commands that write nothing and start no session (`--help`, a script's read-only verbs); when you cannot tell whether a command writes, read its source instead.

Two kinds of finding need two kinds of evidence:

- A finding about **load** (material read that the step does not use, a jump, a fragment, duplication, a cache, a no-op, over-specification) happens on every run of the task. It carries the task and the numbers from the walk: the files, the words, the skills crossed.
- A finding about a **failure** (the agent ends wrong or stuck) names how it occurs where the set is actually used: the user's setup (in MMW, one machine, and the hosts and runner in `~/.mmw/models.json`), the tracker history of past runs (every event of a spec and its tickets is a comment on the issue), or an input a script receives in normal use. A path nobody takes, a state no normal input produces, and a failure that already stops with a refusal the agent acts on are not failures. Text or a mechanism written to guard such a path is itself a finding, under [Redundancy and bloat](SKILL-SET-REVIEW.md#redundancy-and-bloat).

Every finding is fixed. There are no severity levels: a finding is either established by its evidence and fixed, or it is not a finding.

1. **List the tasks.** A skill is entered three ways: a branch its description triggers on; a prompt that starts an agent into it (built by a script, or written by a model from a template); a sentence in another skill or script that sends the agent to it by name or by step. `grep` the skill's name across every skill and script in the set for the third kind, then read the scoped skills for entries described without the name.
   Done when every entry of every skill in scope maps to a task, or is listed as out of scope.
2. **Walk each task.** Start from what the agent holds at entry: the description, the start prompt, or the text that sent it. Open only what the text in front of you points to. Where the text says what a script or CLI does, accepts, reads or prints, check it against the source or `--help`. Record, per step: each file you opened and why, its word count, the skill it belongs to, and which of its sections the step used; each term you had to resolve; each choice you made without guidance; and where the text ends before the task does. Walk the outcomes that happen in use: success, and each failure the history shows or a normal input produces.
   Done when each task reaches its completion criterion or a recorded finding, and every step has its load recorded.
3. **Apply the per-task checks** in `SKILL-SET-REVIEW.md` `## Checks` (every section except Vocabulary, Hand-offs and Upstream skills) to what each task read.
   Done when each check has been applied to each task, or noted as not applying.
4. **Read across the scoped skills** for the three checks no single task shows: [Vocabulary](SKILL-SET-REVIEW.md#vocabulary), [Hand-offs](SKILL-SET-REVIEW.md#hand-offs) and [Upstream skills](SKILL-SET-REVIEW.md#upstream-skills). Read them end to end; a concept that is described instead of named does not show up in `grep`. Glossary entries are checked for the terms the walked tasks use.
   Done when every scoped skill has been read end to end.
5. **Report** before any edit, in this order:
   - The load of each task walked, one row each: who, entering from which text, to which completion criterion; files read, words read, skills crossed, and words read that the run did not use.
   - The findings, grouped by task, then the cross-set findings. Each carries the task, the evidence (the load numbers, or how the failure occurs), the address (file, heading, line numbers), the failure mode (a term from `SKILL.md`, or a heading or bold term of `SKILL-SET-REVIEW.md`), the quoted text, and the fix.
   - Findings in files no running agent reads (glossary, merge-notes, ADRs), listed apart.
   - Decisions for the user: only a choice that changes what a customer sees, what happens to money, the scope, or what cannot be undone. Any other choice is the reviewer's: make it and give the reason in the fix.
   - Not walked, not verified, and checks that did not apply.

   Done when every finding carries its evidence and its fix.
6. **Fix every finding** (see [Editing](SKILL-SET-REVIEW.md#editing)), then walk the same tasks again and report the load table after the fix beside the one before.
   Done when every finding is fixed or is a decision the user holds, and every task still reaches its completion criterion.
