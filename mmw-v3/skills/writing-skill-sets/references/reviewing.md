# Reviewing a skill set

A review walks each task an agent does with the set, as `references/walkthrough.md` says, then holds what each task read to the checks.

Scope: what the user names (skills, files inside one, or a workflow: its playbooks, the mode's route lines and sections their steps rely on, every file their steps name, and the scripts those files run), or the whole set when they name nothing; and each upstream skill's differences from upstream. The scripts those skills call are inside the walk wherever they live, including every message a script prints for an agent (refusals, `--help`, the start prompts it builds). Other skills are read only where the scoped skills hand work to them or take it back. A review of part of the set lists the tasks it left out.

Reviewing writes nothing: run only commands that write nothing and start no session (`--help`, a script's read-only verbs), and hand back the review; when you cannot tell whether a command writes, read its source instead.

Two kinds of finding need two kinds of evidence:

- A finding about **load** (material read that the step does not use, a jump, a fragment, duplication, a cache, a no-op, over-specification) happens on every run of the task. It carries the task and the numbers from the walk: the files, the words, the skills crossed.
- A **failure finding** (the agent ends wrong or stuck) names how it occurs where the set is actually used: the user's setup (in MMW, one machine, and the hosts and runner in `~/.mmw/models.json`), the tracker history of past runs (every event of a spec and its tickets is a comment on the issue), or an input a script receives in normal use. A path nobody takes, a state no normal input produces, and a failure that already stops with a refusal the agent acts on are not failures. Text or a mechanism written to guard such a path is itself a finding, under `references/checks.md` `## Redundancy and bloat`.

Every finding is fixed. There are no severity levels: a finding is either established by its evidence and fixed, or it is not a finding.

1. **List and walk the tasks.** List the tasks in scope and walk each, as `references/walkthrough.md` says.
   Done when both `Done when` lines of `references/walkthrough.md` hold.
2. **Apply the per-task checks** of `references/checks.md` to what each task read, and of the file for each kind of text it read, in the second table of this skill's `SKILL.md`; `## Vocabulary`, `## Hand-offs` and the upstream checks are read across in **Read across the scoped skills**.
   Done when each check has been applied to each task, or noted as not applying.
3. **Read across the scoped skills** for the three checks no single task shows: `## Vocabulary` and `## Hand-offs` of `references/checks.md`, and `references/checks-upstream.md`. Read them end to end; a concept that is described instead of named does not show up in `grep`. Glossary entries are checked for the terms the walked tasks use. Check each passage against `references/components.md`: one that sits in a component other than the one its question assigns is a finding. Read across the set for fact 7 of this skill's `SKILL.md`: a method, rule, definition, map or function stated in a second place is a finding, and the mode's route table and the playbooks, read in the order a task takes, leave no gap and no moment claimed twice. List the terms the scoped skills use as concepts against the glossary: every concept has one entry, one name, and a name chosen as `## Vocabulary` orders. Read each skill also as its fresh agent: from the skill alone, can it say what the work is for, who uses what it produces, and what a shallow result costs? Where it cannot, that is a finding, fixed by writing the sentences that pass the test of fact 1.
   Done when every scoped skill has been read end to end.

**Hand back**, in this order:

- The load of each task walked, one row each: who, entering from which text, to which completion criterion; files read, words read, skills crossed, and words read that the run did not use.
- The findings, grouped by task, then the cross-set findings. Each carries the task, the evidence (the load numbers, or how the failure occurs), the address (file, heading, line numbers), the failure mode (a term from the `writing-for-agents` skill's `SKILL.md`, or a heading or bold term of this skill's `references/checks*.md`), the quoted text, and the fix.
- Findings in files no running agent reads (glossary, merge-notes, ADRs), listed apart.
- Decisions for the user: only a choice user rule 1 leaves to the user. Any other choice is the reviewer's: make it and give the reason in the fix.
- Not walked, not verified, and checks that did not apply.
