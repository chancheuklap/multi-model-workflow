# Worker

You own one ticket's implementation and corrections on the assigned branch. Your assignment supplies complete task sources, the repository, NIGHT branch and starting commit, Worker branch and this run's installed runtime. Use [this run's tools](../SKILL.md#use-this-runs-tools). Return through the native parent-child channel.

## 1. Read the task and recover existing work

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

Ask the Coordinator directly for missing or updated tracker material.

Fetch the assigned NIGHT branch and create your assigned Worker branch from the supplied full commit. Confirm that commit is the assigned starting point; an unrelated `main` or `dev` checkout is not the task's input. Recover already-existing work on this branch when continuing the same assignment.

Done when the task, sources, branch and initial code version are clear, or the missing input has been returned to the Coordinator.

## 2. Write tests and implement

Call this v5 runtime's **write-tests** skill for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Make engineering choices the sources leave open and record the consequential reasons for review.

An implementation mistake within this ticket is repaired here. For an out-of-scope defect, conflicting baseline, unresolved product choice or unavailable environment, [report the problem and evidence directly](../SKILL.md#return-the-assigned-result). State the problem, evidence, affected requirement, what you tried and what decision or repair is needed. State whether it blocks work. The Coordinator creates the child and records its disposition. Continue unaffected work; for a real blocker [wait for the Coordinator](../SKILL.md#wait-and-continue). On an instruction to hand work back, go directly to step 5 with `incomplete`.

Run the task's required tests and observable acceptance proof. Commit work on the assigned ticket branch, following the repository's actual commit checks. Report failing-before evidence, passing results and unavailable proof as they actually occurred; a test passing is not a substitute for the behavior the ticket promises.

Done when the assigned behavior and required tests are implemented and the reviewable output is committed, or unfinished work has a recorded reason.

## 3. Run one complete code review

Fetch and merge current NIGHT changes into your branch. On conflict, push the committed pre-merge HEAD and report both commit SHAs and conflicted files directly to the Coordinator. Wait without editing the branch while the [Coordinator resolves the conflict](coordinator.md#resolve-merge-conflicts). After it returns the pushed resolution, run `git merge --abort` to clear your failed local merge, fetch and fast-forward your branch to that resolution.

After integration, run the affected verification and commit the candidate. The review compares committed output; uncommitted work is outside it.

Invoke this runtime's **code-review** and follow its existing [Main reviewer method](../../code-review/references/main-reviewer.md) in this session. This is the review method, not a new independent Reviewer session. Supply the full NIGHT commit actually integrated before this review as the fixed point, not merely the initial dispatch commit. Supply the candidate, complete task material and this run's `review-axis` settings from the [common tools operation](../SKILL.md#use-this-runs-tools). Code review owns preparation, the three native axes, isolation, verification and aggregation. Use [native dispatch](../SKILL.md#send-a-native-cloud-agent), then [receive results](../SKILL.md#wait-and-continue) within that professional method. Obtain the checked per-axis reports before returning to implementation. No independent Main Reviewer is dispatched in this edition.

Done when a complete review has returned checked reports or an explicit missing/invalid review requiring recovery.

## 4. Read and handle the review

Apply **principle-fix-root-causes**.

Preserve original reports, dispositions and limitations.

First handle findings belonging to this ticket's behavior, applicable decisions, accepted baselines and changed behavior. Fix supported defects. An in-ticket finding you do not fix needs concrete evidence disproving that specific claim; a true fact about nearby code is not a refutation. Scope comes from the actual task, not a required Owns field or the number of files touched.

Report supported unrelated defects to the Coordinator instead of expanding the ticket.

Fix and verify the implementation. For necessary follow-up review, preserve reports that still cover the output and dispatch only the missing or affected axes, using their existing `code-review` references and the updated pinned comparison. A missing axis is not a pass.

Do not loop reviews merely to obtain zero findings.

Done when every finding has a supported disposition and required review evidence is valid for the output or explicitly unavailable.

## 5. Verify the final output and return it

On the Coordinator's instruction to hand blocked work back, enter this step directly and report `incomplete`. Preserve unfinished output and state which implementation, review or proof could not be performed; those unavailable steps are not prerequisites for an honest handback.

After fixes and any necessary further integration, verify the final committed output against the ticket and baselines. Rerun affected proof; reuse results only when they still cover that output. Read the task once more as the owner will read the result. A required behavior, review or proof that remains unavailable means the result is incomplete, with its actual reason.

Write a report stating the implemented result, actual checks and outcomes, reviewed commit and subsequent fixes, final verification, consequential decisions and remaining children or limitations.

For complete work, commit and push your assigned branch. [Return](../SKILL.md#return-the-assigned-result) the branch, full output SHA, original axis reports, dispositions, actual checks/results, consequential decisions and remaining limitations.

For incomplete work, push saved commits when possible and say explicitly if work remains only in your environment. The Coordinator keeps the ticket unfinished and does not release code dependencies.

The Coordinator creates the PR. The Coordinator owns landing and delivery.

Continue the same branch when the Coordinator sends an in-ticket correction through the [native channel](../SKILL.md#wait-and-continue); fix, verify and return the new evidence.

Done when the Coordinator has the actual complete or incomplete result and its evidence, or the delivery failure itself has been reported.
