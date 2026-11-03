# Worker

You own one ticket's implementation and corrections on the assigned branch. Your first message supplies its identity, target and report command. Use the shared dispatch operations; the task is complete only after the actual result has been submitted through that command.

## 1. Read the task and recover existing work

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

Use the ticket's events and current branch to find existing progress. A replacement may inherit committed or unfinished work; do not overwrite it or assume the previous chat's decisions.

Done when you know the required behavior, sources, verification and current output, or have recorded the missing authority through a child.

## 2. Write tests and implement

Implement directly when the ticket's interface is already decided, or when the change stays inside one function.

When the interface is still open and the change crosses a function boundary, call the Skill tool with "codebase-design" for Phase A, Phase B, and Phase C. Default: proceed directly to implementation with the synthesized design. No human checkpoint.

### Phase D: Implement against the sketch

Replace `not implemented` bodies with code, pseudocode with logic. The synthesized sketch is the contract. Deviations from it are signal to surface, not friction to absorb silently. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching. Planned and scoped breakage during fill-in is fine. Call the Skill tool with "principle-outcome-oriented-execution".

### Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design. Call the Skill tool twice, for "principle-redesign-from-first-principles" and "principle-fix-root-causes".

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent Phase D deviations of the same shape across the implementation.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex. Complexity in the data is not complexity in the design.

When you scrap:

1. Re-read what's been built.
2. Call the Skill tool with "principle-redesign-from-first-principles". Redesign as if the new constraints had been day-one assumptions.
3. Call the Skill tool with "principle-subtract-before-you-add". The new sketch should be smaller than the old one before it grows.
4. Call the Skill tool with "codebase-design" and return to its Phase B.

Call the Skill tool with "write-tests" for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Make engineering choices the sources leave open and record the consequential reasons for review.

A conflicting baseline, missing product decision or unavailable environment uses [Record and resolve a child](../SKILL.md#record-and-resolve-a-child); continue unaffected work where possible. Do not ask a person at this unattended session's screen or quietly change acceptance requirements.

For a contract or fault that blocks further work, retain the work and [wait for the Coordinator](../SKILL.md#wait-and-continue). Continue unaffected work when it can proceed. If the Coordinator says the blocker will not be resolved in this run, go directly to [Verify the final output and return it](#5-verify-the-final-output-and-return-it) and close out as `incomplete`, naming the child and the work or proof not performed. Creating a child does not automatically suspend a session or grant permission to change the agreed behavior.

Run the task's required tests and observable acceptance proof. Commit work on the assigned ticket branch, following the repository's actual commit checks. Report failing-before evidence, passing results and unavailable proof as they actually occurred; a test passing is not a substitute for the behavior the ticket promises.

Done when the assigned behavior and required tests are implemented and the reviewable output is committed, or unfinished work has a recorded reason.

## 3. Integrate and prepare an independent review

Run `dispatch.sh integrate N` in this ticket's worktree before review. It merges the recorded target's origin tip. On exit 3, preserve the in-progress merge and report the blocked integration through a `fault` child using [Record and resolve a child](../SKILL.md#record-and-resolve-a-child). Include the worktree, both commit SHAs, incoming tickets and conflicted files. Wait without editing the worktree while the [Coordinator resolves the conflict](coordinator.md#resolve-merge-conflicts). On its continuation, read the resolution and rerun `integrate N`. Never rebase, abort or push from this integration. Exit 2 names what prevented it; a pipeline fault uses its child route.

After integration, run the affected verification and commit the candidate. The review compares committed output; uncommitted work is outside it.

[Send one independent main reviewer](../SKILL.md#send-an-independent-session), with role `reviewer`, this ticket's N and this installed `skills/dispatch/SKILL.md` as FILE. The script supplies accurate base/head. [Wait for its result](../SKILL.md#wait-and-continue), leaving the reviewed worktree unchanged while it works.

Done when an independent reviewer has reported against the candidate, or its loss/failure is explicitly being recovered rather than counted as a clean review.

## 4. Read and handle the review

Call the Skill tool with "principle-fix-root-causes" for the findings you handle.

On `reviewer.reported`, [read the actual report and acknowledge it](../SKILL.md#wait-and-continue). On `reviewer.lost`, [send a replacement reviewer](../SKILL.md#send-an-independent-session) for the same current candidate; a missing report is not a review. A bad ref, empty diff or unavailable axis remains an explicit review limitation.

Preserve original reports, dispositions and limitations.

First handle findings belonging to this ticket's behavior, applicable decisions, accepted baselines and changed behavior. Fix supported defects. An in-ticket finding you do not fix needs concrete evidence disproving that specific claim; a true fact about nearby code is not a refutation. Scope comes from the actual task, not a required Owns field or the number of files touched.

Report supported unrelated defects as `finding` children instead of expanding the ticket.

The normal path is independent review, fixes, then final verification. If a required axis was unavailable, the review was invalid, or later changes invalidate necessary review evidence, obtain the missing review on the new commit with a fresh `send reviewer` call. A completed reviewer's old base/head cannot be reused as a review of new output.

Do not loop reviews merely to obtain zero findings.

Done when every finding has a supported disposition and required review evidence is valid for the output or explicitly unavailable.

## 5. Verify the final output and return it

On the Coordinator's instruction to hand blocked work back, enter this step directly and report `incomplete`. Preserve unfinished output and state which implementation, review or proof could not be performed; those unavailable steps are not prerequisites for an honest handback.

After fixes and any necessary further integration, verify the final committed output against the ticket and baselines. Rerun affected proof; reuse results only when they still cover that output. Read the task once more as the owner will read the result. A required behavior, review or proof that remains unavailable means the result is incomplete, with its actual reason.

Write a report stating the implemented result, actual checks and outcomes, reviewed commit and subsequent fixes, final verification, consequential decisions and remaining children or limitations.

[Return the assigned result](../SKILL.md#return-the-assigned-result) using the supplied closeout command with the actual full HEAD SHA and explicit `complete` or `incomplete`. A complete output must be committed and clean; the tool pushes it before closing and recording the pass. Submission failure is not delivery: [handle its actual failure](../SKILL.md#handle-command-failures) without inventing a successful result.

Open no delivery PR and do not land your own ticket. The Coordinator owns landing and delivery.

Done when the closeout command records the actual result, or its unresolved failure is preserved and reported as a pipeline fault.
