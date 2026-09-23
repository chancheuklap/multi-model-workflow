---
name: retro
description: The retrospective of one completed spec night. Use right after the dispatch skill's `summary` records `spec.closed`.
---

# Retro

## Resolve `<retro>` once

`<retro>` in every command below is `python3 <absolute path to scripts/retro.py>` next to this file. Resolve it from this file's own location, but run it from the completed spec's project checkout: the entry uses the caller's Git top-level as the repository it reads, never the skill installation checkout. It derives repository Space from that checkout's origin; an explicit `NMEM_SPACE` must match that id. The **night's base commit** is the merge-base of the `spec.opened` project and base branches, before `finish` merges them; `gather` reports it as `observed.base_commit`.

The input is a completed spec number. Run `<retro> gather <spec>` and read its complete JSON inventory before analysis. Use `<retro> search <category> <cause>` for each supported current problem; reopen the original sources named by its matches. Before writing analyzed JSON, read [references/analysis.md](references/analysis.md) completely for its exact handoff fields, primary-source rule and proposal threshold. Write that one UTF-8 JSON file, then run `<retro> finalize <spec> <file>`. The script writes outputs; the agent judges causes and dispositions. Done when every inventory item and category is accounted for and the recorded receipt links the full Memory, or an unrecorded receipt names the Memory failure.

Run an evidence-first retrospective for the completed spec night. Produce
evidence-backed improvements to the coding agents' environment and workflow.
The retrospective's record is one **Retro Memory**: the Memory labelled
`mmw-retro` that `finalize` writes for this spec. Owner-approved work through
the normal spec and ticket flow applies changes to code, specs, prompts, Rules,
AGENTS.md, checks, scripts, skills, or toolbox Memory.

A problem exists only when a tracker event comment, commit, current repository
file, or observed check proves it. Attach that source to every reported problem
and drop unsupported claims. Use Memory, Thread, Working Memory, agent reports,
and issue status to discover what to verify; use primary tracker, git,
repository, and check evidence to establish what happened or landed.

Run these phases in order: Gather, Analyze, Decide, Finalize.

## Gather

1. Read the primary sources for completed spec #<spec>: Problem Statement, User
   Stories, and Out of Scope; its complete native ticket tree; every ticket's
   full event fold and the comments carrying those events; spec.closed and its
   proposed Memory record ids; and the landing and closing-pass commits from
   the night's base commit through the completed result.
2. Inventory every required source as present, missing, or unreadable and record
   the exact path, URL, id, or commit range. Carry this inventory into every
   later phase. A missing source narrows the analysis; it never means that the
   corresponding problem did not happen. The final record must distinguish
   checked and clean from never checked.
3. Read the most recent earlier Retro Memory for previous-proposal follow-
   through. Use semantic search for additional earlier Retro Memories only
   when a current problem supplies a category and cause to search for. Reopen
   every cited original event or commit before treating a Memory match as fact.

## Analyze

4. Check every earlier proposal named by the most recent Retro Memory. Record it
   as landed only when a commit, active Rule id, Memory id, or current file
   proves the change. When no such evidence is found, write "no evidence found",
   not "not done". Issue closure alone is not landing evidence.
5. Form current problems only from the gathered tracker events, commits, files,
   and observed checks. Merge duplicate representations of the same underlying
   event. Give every remaining problem its category, cause, and source. Treat a
   shared path, similar title, or category as a search lead rather than proof of
   the same cause.
6. For each current problem, search earlier Retro Memory with category plus
   cause. Count an earlier occurrence only when its original source opens, shows
   the same cause, and belongs to a different ticket, spec, or night.
7. Reconcile intent: take the expected surface from Problem Statement and User
   Stories, the observed surface from checks and events, and compare both with
   Out of Scope. Record aligned, diverged, or unverified; do not change the spec.
8. Review the review results: distinguish a finding that was invalid from one
   that was valid and fixed elsewhere. Preserve the finding's axis, category,
   path, line, claim, route reason, and source.
9. Inspect all seven categories below. Record every source-backed candidate and
   record none for each category whose checked evidence supports no candidate.
   - Navigation: how easy was it for the agent to find the right authority and
     files? Are there hidden dependencies? Would a navigation pointer help?
     Use when the evidence shows time or errors spent finding information.
   - Automated checks: could linting, typing, a test, a judge, a boundary check,
     or a repository script have caught the mistake? Use when such a check can
     deterministically detect the observed problem.
   - Coding standards: should the reviewer receive a stable rule, or should an
     existing rule be removed or clarified? Use when review missed or repeatedly
     misclassified an objective issue.
   - Global AGENTS.md: should a standing instruction move to a check, reviewer
     Rule, skill, or reference? Use when repository or user-level AGENTS.md is
     carrying detail that needlessly consumes every implementation context.
   - Tool economy: did a CLI or MCP produce repeated, expensive, or irrelevant
     calls that a tool, script, or skill could streamline? Use when the evidence
     shows the expensive call.
   - No-ops: did an instruction fail to change agent behaviour? Use when repeated
     evidence shows a steering instruction was present but ineffective.
   - Information access: was a necessary fact unavailable to the agent? Could
     an existing connector, read-only service, log, or reference expose it? Use
     when the missing information is visible in the evidence.

## Decide

10. Give every supported problem two independent dispositions:
    - Handled here: how this instance was fixed, deferred, or accepted as-is.
    - Prevention: the destination from `## Owner-approved destinations` below
      that would prevent the next instance, or `none`.
11. Reopen the primary source behind every subagent report, Memory match, agent
    self-assessment, or inferred outcome used by a problem. Keep the problem only
    when that source proves it.
12. Give a problem a `proposal` when the same cause has two independently
    verified event or commit occurrences, or when spec.closed proposed a Memory
    record backed by two occurrences or one actual blocking event. A blocking
    event is one of `worker.queued`, `ticket.returned`, `child.opened` of kind
    `fault`, or `ticket.checked` with result `handoff`. The proposal names the
    responsible repository, a title and a body. Leave the proposed behaviour
    change for owner-approved work through the normal spec and ticket flow.
13. For a prompt change, include the target file and heading, supporting event
    or commit, the complete current passage, the complete proposed passage,
    every Changes Made item, and the expected behaviour change. State whether it
    adds missing context or constraints, clarifies ambiguity, adds success
    criteria or a specific requirement, or frontloads information that arrived
    too late. Keep every unchanged sentence unchanged and submit both complete
    passages rather than a shorter paraphrase or an isolated diff fragment.
    Write a proposed passage for a prompt or a skill as the `writing-for-agents`
    skill's `SKILL.md` says, and one for an `AGENTS.md` as the
    `manage-agents-md` skill says.

## Finalize

14. Record the whole retro in the analyzed JSON: Spec, Task root, Evidence
    checked, Previous proposals, Problems observed, the seven category results,
    Intent reconciliation, Review learning, and Observed; for every problem
    include Evidence, Handled here, Prevention, Earlier occurrences, and
    Proposal. Keep every source reference and missing-evidence statement in it.
15. Run `<retro> finalize <spec> <file>`. `finalize` checks the file against a
    fresh `gather`, then creates one `needs-triage` issue per proposal, or
    reuses an open one whose body holds this spec and every source, carrying its
    sources, Handled here, Prevention, this spec and the Retro Memory id above
    its body; writes the fixed-id Retro Memory in the repository Space from the
    file; and only after that write succeeds posts the `spec.retroed` receipt
    with the Memory id, problem count, proposal links and evidence completeness.
    When the Memory write fails, the receipt says result=unrecorded with the
    specific reason. A completed retro changes no ticket verdict and wakes no
    agent.
16. Report the Retro Memory id, problem count, proposals or none, and whether
    the evidence inventory was complete. Completion requires every inventory
    item to have a status, every retained problem to have primary evidence and
    both dispositions, all seven categories to have a result, and every output
    field above to be present. When no supported improvement exists, record and
    report none.

Implementation agents use the most context because they explore, implement,
and debug. Reviewers receive a diff and use less context. Put stable coding
standards in the reviewer's Rules, not in every worker prompt.
Use AGENTS.md sparingly, mainly for navigation pointers; use docs as referenced
detail; use a skill only for a repeatable multi-step workflow with a discoverable
trigger, inputs, outputs, and Done when.

`gather` supplies `evidence_checked`, `task_root`, `observed.base_commit` and `proposed_memory_ids`. Use its source references verbatim. `finalize` refuses missing sections or invented sources. Keep the analyzed JSON in a temporary path outside the repository.

## Owner-approved destinations

A proposal asks for approval and changes none of these destinations. A problem's Prevention names one of them by its `destination` value:

| `destination` | What belongs there |
| --- | --- |
| `check` | a mechanical invariant a lint, test, judge or boundary check can detect |
| `script` | a mechanical step a script can carry out |
| `repository-agents` | a short repository-wide, non-inferable navigation pointer or universal instruction, in that repository's `AGENTS.md` |
| `repository-skill` | a repeated multi-step workflow specific to one repository, as a repository-local skill with a discovery test |
| `reviewer-rule` | stable cross-repository review behaviour, as an active reviewer Rule |
| `mmw-skill` | a cross-repository MMW workflow, in an MMW skill |
| `toolbox-memory` | approved, broadly useful knowledge, copied into toolbox Memory while the source Memory remains in the repository |
| `none` | nothing would prevent the next instance |

Done when each proposal names one responsible repository, its supported destination and the owner decision still required.
