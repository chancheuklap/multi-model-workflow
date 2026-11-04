# Worker

You own one ticket's implementation and corrections on `ticket/issue-N`. The card names the ticket, the night branch, and that branch name.

## 1. Name the branch and read the task

Rename the current branch to the card's `ticket/issue-N` before any commit or push. When origin already has that branch, fast-forward to it, then rename. When the current branch already has that name, keep it.

Call the Skill tool with "principle-baseline-is-the-contract" for the ticket and its baselines. Call the Skill tool with "principle-never-block-on-the-human".

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

If required tracker material is missing or outdated, return a request for it to the sender and end the turn. Continue from this step when the Coordinator resumes you with the material.

When this branch already contains commits for this ticket, continue from those commits.

Done when this branch is named `ticket/issue-N`, and the task, sources, and code version are clear, or the missing input has been returned.

## 2. Write tests and implement

When the ticket is sustained improvement of one metric against a target, call the Skill tool with "hillclimb". That skill completes this step. Each attempt stays on this ticket.

When the ticket preserves behavior and changes structure, call the Skill tool with "refactoring". That skill completes this step.

Call the Skill tool with "write-tests" for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Implement directly when the ticket's interface is already decided, or when the change stays inside one function. When a surrounding subsystem exists, call the Skill tool with "how" for that subsystem before writing the change.

When the interface is still open and the change crosses a function boundary, call the Skill tool with "codebase-design" for Phase A, Phase B, and Phase C. Default: proceed directly to implementation with the synthesized design. No human checkpoint.

Phase D and Phase E apply only after that call has returned a sketch. hillclimb, refactoring, and direct implementation do not enter them.

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

1. Call the Skill tool with "how" to re-read what's been built.
2. Call the Skill tool with "principle-redesign-from-first-principles". Redesign as if the new constraints had been day-one assumptions.
3. Call the Skill tool with "principle-subtract-before-you-add". The new sketch should be smaller than the old one before it grows.
4. Call the Skill tool with "codebase-design" and return to its Phase B.

Make engineering choices the sources leave open and record the consequential reasons for review.

An implementation mistake within this ticket is repaired here. For an out-of-scope defect, conflicting baseline, unresolved product choice or unavailable environment, state the problem, evidence, affected requirement, what you tried and what decision or repair is needed. When it needs the Coordinator's action before you can continue, return the problem to the sender and end the turn. Continue from this step after its reply. Write non-blocking findings in the PR. On an instruction to hand work back, go directly to step 4 and leave the PR draft.

When the ticket names a feature file and the sentence to show, write the drive script after the surface works. That file is a page under `.cursor/skills/verify-<app>/features/`. Copy the ticket's sentence into the page unchanged. Read that verify skill and write the script the way its Drive section already drives the app. The script checks for the same sentence. Put the script in that skill, next to the page. Run it until it passes, and commit the script and the page. `write-tests` writes seam tests, not this script. `maintain-verification-skill` is a later pass over the whole map, not this ticket. When the ticket names neither a feature file nor a sentence, do not write them.

Run the task's required tests. Call the Skill tool with "principle-prove-it-works". Commit on `ticket/issue-N`. Keep failing-before evidence, passing results, and unavailable proof as they occurred. A passing test does not stand in for the behavior the ticket promises.

After the first implementation commit, push and open the draft PR: head `ticket/issue-N`, base the night branch, ticket linked in the body. In Cursor, `ManagePullRequest` `create_pr` with `draft` enabled. Later commits use this PR.

Done when that behavior is pushed and the draft PR exists, or the unfinished reason is ready for the PR.

## 3. Send the verifier

Fetch and merge the current night branch into `ticket/issue-N`, so the verifier runs on a head that already contains what this night has landed. On conflict, push the committed pre-merge HEAD and return both SHAs and the conflicted files for the [Coordinator to resolve](coordinator.md#resolve-merge-conflicts). End the turn. After the resume, run `git merge --abort`, then fetch and fast-forward to the resolution.

If that merge changed the feature file this ticket named, update the drive script, run it, commit, and push before the verifier. Call the Skill tool with "no-comments" for this diff and commit what it changes before the verifier. Push that commit too. The verifier runs the pushed head, and the PR head has to be that same commit.

Run `dispatch.sh spawn verifier`. A printed card is a new Task: hand it over as [Dispatch](../SKILL.md) describes and wait. Resuming an older verifier would rerun the old commit. No card means this ticket has no verifier: go to step 4 and write the PR. When the command says the head is not pushed, push and run the command again. Any other error from the command: return that error to the Coordinator and end the turn. Do not write the PR as verified.

Done when the verifier has returned. No card continues at step 4.

## 4. Write the result in the PR

Call the Skill tool with "principle-fix-root-causes" for a failure you handle.

When the verifier returns unavailable, do not change the product. Check out the commit the card named and send a new verifier card. If HEAD cannot be that commit, return the verifier's message to the Coordinator and end the turn.

When the verifier fails, the head has moved since the pass, or the Coordinator resumes you with the output of a failed `scripts/check`, fix, push, and run `dispatch.sh spawn verifier` again. Send that as a new card. A pass covers only the commit it ran.

When the passing commit is the PR head, or there was no verifier, write the PR. Call the Skill tool with "pr" for the PR body. Include the ticket, what you implemented, the commands and results, consequential decisions, findings outside this ticket, and any unfinished work with its reason. Name the commit a verifier passed. An unfinished ticket stays draft, with the reason in the PR. With no PR, return the reason to the Coordinator. You do not create the child issue.

On an instruction to hand work back, enter here. Preserve unfinished output and name the proof that could not be run.

Return the PR number and that commit to the sender. With no PR, return the reason.

Done when the PR holds that result and the reply names it, or the unfinished reason has been returned.
