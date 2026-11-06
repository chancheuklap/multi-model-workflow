# Worker

You own one ticket's implementation and corrections on `ticket/issue-N`. Your assignment names the ticket, the night branch, and your issue-N branch. Follow steps 1–4 in order; a question resumes the step that raised it. On an instruction to hand work back, go directly to step 4 and preserve the unfinished result.

## Report problems during any step

During any step, repair implementation mistakes within this ticket through step 2. Immediately report other defects, conflicting baselines, unresolved product choices, and unavailable execution conditions to the Coordinator: the problem, evidence, affected requirement, what you tried, and whether it blocks implementation, verification, or landing. Non-blocking reports are sent while you continue; they do not wait for the final PR. A blocking report ends the turn until the Coordinator supplies an answer or directs you to hand work back. The Coordinator owns registration and disposition through [Problems](coordinator.md#3-problems); you keep the Worker role and do not create child issues.

## 1. Name the branch and read the task

Start from the assigned branch and commit in your own checkout. Rename its branch to the assigned `ticket/issue-N` before any commit or push. When origin already has that branch, fast-forward to it, then rename. When the current branch already has that name, keep it.

Use **principle-baseline-is-the-contract** for the ticket and its baselines. Use **principle-never-block-on-the-human**.

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

If required tracker material is missing or outdated, return a request for it to the sender and end the turn. Continue from this step when the Coordinator resumes you with the material.

When this branch already contains commits for this ticket, continue from those commits.

Done when this branch is named `ticket/issue-N`, and the task, sources, and code version are clear, or the missing input has been returned.

## 2. Write tests and implement

When the ticket is sustained improvement of one metric against a target, use **hillclimb**. After that skill returns, continue at [Complete the implementation](#complete-the-implementation). Each attempt stays on this ticket.

When the ticket preserves behavior and changes structure, use **refactoring**. After that skill returns, continue at [Complete the implementation](#complete-the-implementation).

Use **write-tests** for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Implement directly when the ticket's interface is already decided, or when the change stays inside one function. When a surrounding subsystem exists, use **how** for that subsystem before writing the change.

When the interface is still open and the change crosses a function boundary, use **codebase-design** for Phase A, Phase B, and Phase C. Default: proceed directly to implementation with the synthesized design. No human checkpoint.

Phase D and Phase E apply only after that call has returned a sketch. hillclimb, refactoring, and direct implementation do not enter them.

### Phase D: Implement against the sketch

Replace `not implemented` bodies with code, pseudocode with logic. The synthesized sketch is the contract. Deviations from it are signal to surface, not friction to absorb silently. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching. Planned and scoped breakage during fill-in is fine. Use **principle-outcome-oriented-execution**.

### Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design. Use **principle-redesign-from-first-principles** and **principle-fix-root-causes**.

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent Phase D deviations of the same shape across the implementation.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex. Complexity in the data is not complexity in the design.

When you scrap:

1. Use **how** to re-read what's been built.
2. Use **principle-redesign-from-first-principles**. Redesign as if the new constraints had been day-one assumptions.
3. Use **principle-subtract-before-you-add**. The new sketch should be smaller than the old one before it grows.
4. Use **codebase-design** and return to its Phase B.

### Complete the implementation

All implementation paths return here, including hillclimb, refactoring, direct implementation, and the sketch phases above. Make engineering choices the sources leave open and record the consequential reasons for review.

When the ticket names a feature file and the sentence to show, write the drive script after the surface works. Read the `verify-<app>` skill that owns the ticket's feature file. Copy the ticket's sentence into the page unchanged and write the script the way that skill's Drive section already drives the app. The script checks for the same sentence. Put the script in that skill, next to the page. Correct failures caused by your implementation, and commit the passing script and page. Report other failures through [Report problems](#report-problems-during-any-step). `write-tests` writes seam tests, not this script. `maintain-verification-skill` is a later pass over the whole map, not this ticket. When the ticket names neither a feature file nor a sentence, do not write them.

Run the task's required tests. Use **principle-prove-it-works**. Commit on `ticket/issue-N`. Keep failing-before evidence, passing results, and unavailable proof as they occurred. A passing test does not stand in for the behavior the ticket promises.

After the first implementation commit, push and open the draft PR: head `ticket/issue-N`, base the night branch, ticket linked in the body. Later commits use this PR.

Done when every required behavior and applicable test is complete and pushed, and the draft PR exists: continue to step 3. If the Coordinator directs an unfinished handback, continue to step 4 instead.

## 3. Send the verifier

Enter after the complete implementation in step 2, or after a correction or restored verification condition requires a new run. An unfinished handback goes directly to step 4.

Fetch and merge the current night branch into `ticket/issue-N`, so the verifier runs on a head that already contains what this night has landed. On conflict, push the committed pre-merge HEAD and return both SHAs and the conflicted files for the [Coordinator to resolve](coordinator.md#resolve-merge-conflicts). End the turn. After the resume, run `git merge --abort`, then fetch and fast-forward to the resolution.

If that merge changed the feature file this ticket named, update the drive script, run it, commit, and push before the verifier. Use **no-comments** for this diff and commit what it changes before the verifier. Push that commit too. The verifier runs the pushed head, and the PR head has to be that same commit.

Run `dispatch.sh spawn verifier --host HOST`. Send each card to a **FRESH AGENT** as [Dispatch](../SKILL.md) describes. Wait for the result. Resuming an older verifier would rerun the old commit. An explicit `skipped` result with no card means this ticket has no verifier: go to step 4 and record the skip. When the command says the head is not pushed, push and run the command again. Any other error from the command: return that error to the Coordinator and end the turn. Do not write the PR as verified.

Done when the verifier has returned or dispatch explicitly skipped it; continue at step 4. A command error waits for the Coordinator at this step.

## 4. Write the result in the PR

On an instruction to hand work back, commit and push any preservable changes, open or update the draft PR when possible, and write the unfinished result below immediately. This path does not start another repair or verification attempt.

Otherwise handle the verification result:

- **Pass:** it covers only the assigned commit. If the PR head moved, send the current complete, pushed head through step 3 before claiming verification.
- **Fail:** use **principle-fix-root-causes** for an implementation error or regression in this ticket. Correct it through step 2, then verify the complete new head in step 3. Send unrelated findings or uncertain causes to the Coordinator through [Report problems](#report-problems-during-any-step).
- **Unavailable:** return the result and missing condition to the Coordinator and end the turn. Resume step 3 only after the condition is restored; otherwise write the unfinished result when asked. A new verifier alone does not restore the condition.
- **Skipped by dispatch:** record the skip and the tests that did run; it is not a verifier pass.

If the same failure persists without a relevant correction, new evidence, or a changed execution condition, return it to the Coordinator for disposition instead of repeating the attempt. A failed landing check also returns through the Coordinator's Problems procedure; carry out only the correction it assigns within this ticket.

Use **pr** for the PR body. Include the ticket, what you implemented, commands and results, consequential decisions, links to reported problems and their dispositions, and any unfinished work with its reason. Name the current head and, when applicable, the commit the verifier passed. Distinguish implementation complete, verification blocked, and landing blocked. An unfinished ticket stays draft. With no PR, return the reason to the Coordinator.

Return the PR number and that commit to the sender, or the no-PR reason. The Coordinator reads the result and decides whether it can land.

Done when the PR holds that result and the reply names it, or the unfinished reason has been returned.
