---
name: retro
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Retro

Run `python3 scripts/retro.py` from a checkout of the spec's repository whose `HEAD` is `origin/<base branch>`, the base branch `spec.opened` records: `finalize` reads repository files from that working tree.

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

Three readers act on this record: the user, who reads `NIGHT RETRO` before
accepting the night; whoever triages each proposal, which becomes a
`needs-triage` issue in its `repository` read by someone who did not watch the
night, so its title and body stand on their own; and the next retro, which
searches these problems for repeats. A problem the evidence does not carry
costs twice: a triage decision now, and a false match later that makes one
incident look like a pattern.

Look for what in the environment let the mistake through, the discipline of a
blameless postmortem: a check that did not exist, an instruction that arrived
too late, a fact the agent could not reach.
A cause addressed to "the agent" changes nothing on the next run. A night whose
evidence supports no problem is a valid retro; record `none` rather than
stretching a weak source into a finding.

The script writes outputs; the agent judges causes and dispositions.

## Gather

1. Run `python3 scripts/retro.py gather <spec>` and save its JSON output to a temporary file
   outside the repository. Find where the night went off course in
   `tickets[].events` and `spec_events` (returns, queued workers, fault
   children, handoffs, reviewer findings), then open the comment bodies behind
   those events.
2. `gather` writes the inventory of every source as present, missing, or
   unreadable (`evidence_checked`). A missing source narrows the analysis; it
   never means that the corresponding problem did not happen.

## Analyze

3. Check every earlier proposal named by the most recent Retro Memory. Record it
   as `landed` only when a commit, Memory id, or current file proves the
   change, and give that proof as a commit SHA, a
   `https://github.com/<owner>/<name>/commit/<sha>` URL when the change landed
   in another repository, `nowledgemem://memory/<id>` or a repository-relative
   file path. When no such evidence is found, record
   `no-evidence-found`, not "not done". Issue closure alone is not landing
   evidence.
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
5. For each current problem, run `python3 scripts/retro.py search <category> <cause>` to find
   candidates. Count an earlier occurrence only when its original source opens,
   shows the same cause, and belongs to a different ticket, spec, or night. An
   earlier occurrence names the Retro Memory id the search returned and the
   original event or commit URL in that Memory; reopen both. Two event comments
   on one ticket or spec are one occurrence, not two.
6. Reconcile intent: take the expected surface from Problem Statement and User
   Stories, the observed surface from checks and events, and compare both with
   Out of Scope. Record aligned, diverged, or unverified; do not change the spec.
   It catches a night that met every criterion yet delivered something other
   than what the spec asked for.
7. Review the review results: distinguish a finding that was invalid from one
   that was valid and fixed elsewhere. A finding was invalid when the closing
   pass routed it `stale invalid`, or the worker answered it `refuted:` and
   nothing since shows the bad outcome. Record in `review_learning` each such
   finding's category, claim, route reason or refutation, and source, or `none`.
   This is how the review improves: the category of a finding is the rule of a
   `CODING_STANDARDS.md` it cites, its smell or its Spec or UI kind, so two
   invalid findings citing one rule point to that rule, to clarify or remove,
   and two valid findings of one kind with a fixed shape point to a check. A
   finding another ticket fixed was right, and does not count against the
   review.
8. Inspect all seven categories below. Record every source-backed candidate and
   record none for each category whose checked evidence supports no candidate.
   A problem in a category requires a candidate result there.
   - Navigation: how easy was it for the agent to find the right authority and
     files? Are there hidden dependencies? Would a navigation pointer help?
     Use when the evidence shows time or errors spent finding information.
   - Automated checks: could linting, typing, a test, an oracle, a boundary check,
     or a repository script have caught the mistake? Use when such a check can
     deterministically detect the observed problem.
   - Coding standards: should the review apply a new rule, or should a rule of
     a `CODING_STANDARDS.md` be clarified or removed? Classify the violation
     first: one with a fixed shape (a banned call, an import form, a file
     location) belongs to Automated checks, and only a judgement no check can
     make is a coding standard. Use when the review missed a mistake the diff
     showed, or findings citing one rule were invalid.
   - Global AGENTS.md: should a standing instruction move to a check, a coding
     standard, a skill, or a reference? Use when repository or user-level
     AGENTS.md is carrying detail that needlessly consumes every implementation
     context.
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
10. Every prevention has a standing cost: a check runs on every commit, and an
    `AGENTS.md` line or skill sentence is read by every later agent. One
    occurrence is dealt with in `Handled here`; a pattern, shown by two
    independent occurrences or by a Memory record `spec.closed` proposed, is
    worth that cost. Give a problem a `proposal` when the same cause
    has two independently verified event or commit occurrences, or when
    `spec.closed` proposed a Memory record (an id in `proposed_memory_ids`)
    whose decision's `evidence` URL is among the problem's evidence and one of
    the problem's event sources is a stall event. A **stall event** is
    one of `ticket.returned`, `child.opened` with
    `kind=fault`, or `ticket.checked` with `result=handoff`. File and
    standalone-check sources support a problem, not this threshold. The
    proposal has `repository` (`owner/name` responsible for the change),
    `title`, `body`, and optional `prompt_change`.

    A proposal already open for the same cause is added to, not opened again:
    a second issue for one decision costs the owner a second triage. When an
    earlier occurrence's Retro Memory names a proposal that is still open, give
    the proposal `repository` and `existing`, that issue's URL, in place of
    `title`, `body` and `prompt_change`; `finalize` comments this night's
    sources on it. A proposal closed without the change landing (step 3 found
    no evidence) is opened again as a new proposal that names the closed one.
11. For a prompt change, `prompt_change` has `target_file`, `heading`, `source`
    (one of the problem's primary evidence URLs), `current_passage`,
    `proposed_passage`, `changes_made` and `expected_behavior`. `target_file` is
    a path in the checkout the retro runs in; a proposal whose `repository` is
    another repository carries no `prompt_change`. Keep every unchanged sentence
    unchanged and submit both complete passages rather than a shorter paraphrase
    or an isolated diff fragment. `changes_made` is one sentence naming which of
    missing context, ambiguity, success criteria or late information the change
    addresses. Read the `writing-for-agents` skill's `SKILL.md` before writing
    the proposed passage.

## Finalize

12. Write the analyzed JSON: one UTF-8 file in a temporary path outside the
    repository, in the shape below.

    ```json
    {
      "previous_proposals": [
        {"url": "...", "status": "landed|no-evidence-found", "evidence": "commit SHA|GitHub commit URL|Memory id|file|none"}
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
          "prevention": {"destination": "check|script|repository-agents|repository-skill|coding-standard|mmw-skill|toolbox-memory|none", "text": "..."},
          "earlier_occurrences": [{"memory_id": "...", "evidence": "original event|commit URL"}],
          "proposal": null
        }
      ],
      "intent_reconciliation": {"expected": "...", "observed": "...", "gap": "aligned|diverged|unverified"},
      "review_learning": "...|none"
    }
    ```
13. Run `python3 scripts/retro.py finalize <spec> <analysis> <gather>`, `<gather>` the file step 1
    saved. It checks that file against a fresh `gather`, and a refusal names
    what to correct.

Done when `finalize` has posted `spec.retroed` with `result=recorded`.

## Prevention destinations

A problem's Prevention names one of them by its `destination` value:

| `destination` | What belongs there |
| --- | --- |
| `check` | a mechanical invariant a lint, test, oracle or boundary check can detect |
| `script` | a mechanical step a script can carry out |
| `repository-agents` | a short repository-wide, non-inferable navigation pointer or universal instruction, in that repository's `AGENTS.md` |
| `repository-skill` | a repeated multi-step workflow specific to one repository, as a repository-local skill with a discovery test |
| `coding-standard` | a judgement the review applies to every later diff, as a row of a `CODING_STANDARDS.md`: the `code-review` skill's when it holds in every repository, the repository's root file (created by this proposal when absent) when it holds only there |
| `mmw-skill` | a cross-repository MMW workflow or rule, in the MMW skill set: a playbook or a section of the `mmw-mode` skill, a principle, or a skill, wherever the mode's Authoring or modifying a skill playbook places it; also a change to a user-level `AGENTS.md`, whose sources are MMW's `mmw-v3/prompt/` |
| `toolbox-memory` | approved, broadly useful knowledge, copied into toolbox Memory while the source Memory remains in the repository |
| `none` | nothing would prevent the next instance |

Choose the destination whose reader acts on the lesson. Workers carry the
heaviest context: they explore, implement and debug; the reviewer receives a
diff and has room to spare. So a standard only judgement can apply goes to a
`CODING_STANDARDS.md` the review applies; a violation with a fixed shape (a
banned call, an import form, a file location) goes to a `check`, which no one
has to remember; and `AGENTS.md` keeps only short pointers nearly every task
needs. Before proposing
a check, look at the repository's existing check commands: one that exists but
is not wired in, or is silently broken, is the finding.

A row of a `CODING_STANDARDS.md` is applied to every review from then on, so
it is proposed only when all of these hold: a diff shows the mistake; no check
could catch it; the rule would change what a later review reports; no rule,
smell of the Standards axis, or check already covers it; and it stays true as
the code changes. The proposal gives the row as it would stand (the rule's
name, the finding it describes, its details) and the file it goes in. A row is
reworded or removed on the same kind of evidence the other way: invalid
findings that cite it.
