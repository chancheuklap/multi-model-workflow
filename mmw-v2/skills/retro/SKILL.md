---
name: retro
description: Retrospect one completed MMW spec night. Use right after the dispatch skill's `summary` records `spec.closed`.
---

# Retro

## Resolve `<retro>` once

`<retro>` in every command below is `python3 <absolute path to scripts/retro.py>` next to this file; resolve it from this file's own location, since the path differs by machine and by host. Run it from a checkout of the spec's repository whose `HEAD` is `origin/<base branch>`, the base branch `spec.opened` records: `finalize` reads repository files from that working tree.

Run an evidence-first retrospective of the completed spec night and produce
evidence-backed improvements to the coding agents' environment and workflow. Its
record is one **Retro Memory**: the Memory labelled `mmw-retro` that `finalize`
writes for this spec. Work the user approves applies the improvements later,
through the normal spec and ticket flow.

A problem exists only when a tracker event comment, commit, current repository
file, or observed check proves it. Attach that source to every reported problem
and drop unsupported claims. Use Memory, Thread, Working Memory, agent reports,
and issue status to discover what to verify; use primary tracker, git,
repository, and check evidence to establish what happened or landed.

The script writes outputs; the agent judges causes and dispositions.

## Gather

1. Run `<retro> gather <spec>`, save its JSON output to a temporary file
   outside the repository, and read all of it before analysis.
2. `gather` writes the inventory of every source as present, missing, or
   unreadable (`evidence_checked`). Carry its `evidence_checked`, `task_root`
   and `observed.base_commit` into the analyzed JSON unchanged, copied by
   program from its saved output. A missing source narrows the analysis; it
   never means that the corresponding problem did not happen.

## Analyze

3. Check every earlier proposal named by the most recent Retro Memory. Record it
   as `landed` only when a commit, active Rule id, Memory id, or current file
   proves the change, and give that proof as a commit SHA, `Rule: <active-id>`,
   `nowledgemem://memory/<id>` or a repository-relative file path. When no such
   evidence is found, record `no-evidence-found`, not "not done". Issue closure
   alone is not landing evidence.
4. Form current problems only from the gathered tracker events, commits, files,
   and observed checks. Merge duplicate representations of the same underlying
   event. Give every remaining problem its category, cause, and source. Treat a
   shared path, similar title, or category as a search lead rather than proof of
   the same cause.

   A current problem needs a primary source whose opened text or output states
   the cause. Use a script-written event comment URL or Git commit URL for
   running facts and repeated occurrences. A current repository file is its path
   relative to the checkout root; `finalize` opens that file. A standalone
   observed check is `check:<command>`: supply a re-runnable, read-only `rg`
   command or read-only `git diff|show|log|status|grep|rev-parse|cat-file`
   command whose actual output states the cause. `finalize` runs its arguments
   without a shell and refuses a check that prints nothing; a check already
   recorded by the pipeline uses the `ticket.checked` event URL instead.
5. For each current problem, run `<retro> search <category> <cause>`, and write
   the problem's `cause` exactly as you passed it, because `finalize` repeats
   that search. Count an earlier occurrence only when its original source opens,
   shows the same cause, and belongs to a different ticket, spec, or night. An
   earlier occurrence names the Retro Memory id the search returned and the
   original event or commit URL in that Memory; reopen both. Two event comments
   on one ticket or spec are one occurrence, not two.
6. Reconcile intent: take the expected surface from Problem Statement and User
   Stories, the observed surface from checks and events, and compare both with
   Out of Scope. Record aligned, diverged, or unverified; do not change the spec.
7. Review the review results: distinguish a finding that was invalid from one
   that was valid and fixed elsewhere. Record in `review_learning` each such
   finding's claim, route reason, and source, or `none`.
8. Inspect all seven categories below. Record every source-backed candidate and
   record none for each category whose checked evidence supports no candidate.
   A problem in a category requires a candidate result there.
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

9. Give every supported problem two independent dispositions:
   - Handled here: how this instance was fixed, deferred, or accepted as-is.
   - Prevention: the `destination` from `## Prevention destinations` below
     that would prevent the next instance, or `none`.
10. Reopen the primary source behind every subagent report, Memory match, agent
    self-assessment, or inferred outcome used by a problem. Keep the problem only
    when that source proves it.
11. Give a problem a `proposal` when the same cause has two independently
    verified event or commit occurrences, or when `spec.closed` proposed a
    Memory record (an id in `proposed_memory_ids`) whose decision's `evidence`
    URL is among the problem's evidence and one of the problem's event sources
    is a blocking event. A **blocking event** is one of `worker.queued`,
    `ticket.returned`, `child.opened` with `kind=fault`, or `ticket.checked`
    with `result=handoff`. File and standalone-check sources support a problem,
    not this threshold. The proposal has `repository` (`owner/name` responsible
    for the change), `title`, `body`, and optional `prompt_change`. Leave the
    proposed behaviour change for work the user approves, through the normal spec
    and ticket flow.
12. For a prompt change, `prompt_change` has `target_file`, `heading`, `source`
    (one of the problem's primary evidence URLs), `current_passage`,
    `proposed_passage`, `changes_made` and `expected_behavior`. `target_file` is
    a path in the checkout the retro runs in; a proposal whose `repository` is
    another repository carries no `prompt_change`. Keep every unchanged sentence
    unchanged and submit both complete passages rather than a shorter paraphrase
    or an isolated diff fragment. `changes_made` has four nonempty answers:
    `context_or_constraints` (adds missing context or constraints), `ambiguity`
    (clarifies ambiguity), `success_criteria_or_requirement` (adds success
    criteria or a specific requirement) and `timing` (frontloads information
    that arrived too late), each explaining whether that class changed or
    explicitly saying it did not. Read the `writing-for-agents` skill's
    `SKILL.md` before writing the proposed passage.

## Finalize

13. Write the analyzed JSON: one UTF-8 file in a temporary path outside the
    repository, in the shape below. `observed.at` is the actual retro time.
    Keep every source reference and missing-evidence statement in it.

    ```json
    {
      "spec": 0,
      "task_root": {"kind": "map|standalone-spec", "number": 0},
      "evidence_checked": [
        {"source": "URL|path|commit range", "status": "present|missing|unreadable", "detail": "..."}
      ],
      "previous_proposals": [
        {"url": "...", "status": "landed|no-evidence-found", "evidence": "commit|Rule id|Memory id|file|none"}
      ],
      "categories": {
        "Navigation": "none|candidate summary",
        "Automated checks": "none|candidate summary",
        "Coding standards": "none|candidate summary",
        "Global AGENTS.md": "none|candidate summary",
        "Tool economy": "none|candidate summary",
        "No-ops": "none|candidate summary",
        "Information access": "none|candidate summary"
      },
      "problems": [
        {
          "category": "...",
          "cause": "...",
          "evidence": ["event URL|commit URL|repository-relative file|check:read-only command"],
          "handled_here": "...",
          "prevention": {"destination": "check|script|repository-agents|repository-skill|reviewer-rule|mmw-skill|toolbox-memory|none", "text": "..."},
          "earlier_occurrences": [{"memory_id": "...", "evidence": "original event|commit URL"}],
          "proposal": null
        }
      ],
      "intent_reconciliation": {"expected": "...", "observed": "...", "gap": "aligned|diverged|unverified"},
      "review_learning": "...|none",
      "observed": {"at": "ISO-8601", "base_commit": "40-hex"}
    }
    ```
14. Run `<retro> finalize <spec> <file>`. It checks the file against a fresh
    `gather`, and a refusal names what to correct.

Done when `finalize` has posted `spec.retroed` with `result=recorded`; then return to the dispatch skill's `references/night.md` `## 5. The night is over`, which tells the user.

## Prevention destinations

A proposal asks for approval and changes none of these destinations. A problem's Prevention names one of them by its `destination` value:

| `destination` | What belongs there |
| --- | --- |
| `check` | a mechanical invariant a lint, test, judge or boundary check can detect |
| `script` | a mechanical step a script can carry out |
| `repository-agents` | a short repository-wide, non-inferable navigation pointer or universal instruction, in that repository's `AGENTS.md` |
| `repository-skill` | a repeated multi-step workflow specific to one repository, as a repository-local skill with a discovery test |
| `reviewer-rule` | stable cross-repository review behaviour, as an active reviewer Rule |
| `mmw-skill` | a cross-repository MMW workflow, in an MMW skill; also a change to a user-level `AGENTS.md`, whose sources are MMW's `mmw-v2/prompt/` |
| `toolbox-memory` | approved, broadly useful knowledge, copied into toolbox Memory while the source Memory remains in the repository |
| `none` | nothing would prevent the next instance |

Choose the destination whose reader acts on the lesson. A coding standard a
reviewer can check goes in a reviewer Rule rather than in text every worker reads.
