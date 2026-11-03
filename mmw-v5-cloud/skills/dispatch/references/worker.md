# Worker

You own one ticket's implementation and corrections on the assigned branch. Your assignment supplies complete task sources, the repository, NIGHT branch and starting commit, Worker branch and this run's installed runtime. Use [this run's tools](../SKILL.md#use-this-runs-tools). Return through the native parent-child channel.

## 1. Read the task and recover existing work

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

If required tracker material is missing or outdated, [return a request for it](../SKILL.md#return-the-assigned-result). Continue from this step when the Coordinator resumes you with the material.

Fetch the assigned NIGHT branch and create your assigned Worker branch from the supplied full commit. Confirm that commit is the assigned starting point; an unrelated `main` or `dev` checkout is not the task's input. Recover already-existing work on this branch when continuing the same assignment.

Done when the task, sources, branch and initial code version are clear, or the missing input has been returned to the Coordinator.

## 2. Write tests and implement

Call the Skill tool with "write-tests" for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Make engineering choices the sources leave open and record the consequential reasons for review.

An implementation mistake within this ticket is repaired here. For an out-of-scope defect, conflicting baseline, unresolved product choice or unavailable environment, state the problem, evidence, affected requirement, what you tried and what decision or repair is needed. When it needs the Coordinator's action before you can continue, [return the problem](../SKILL.md#return-the-assigned-result) and continue from this step after its reply. Include non-blocking findings in the final work report. On an instruction to hand work back, go directly to step 5 with `incomplete`.

Run the task's required tests and observable acceptance proof. Commit work on the assigned ticket branch, following the repository's actual commit checks. Report failing-before evidence, passing results and unavailable proof as they actually occurred; a test passing is not a substitute for the behavior the ticket promises.

After the first implementation commit, push `issue-N` and create its draft PR with `issue-N` as head and the assigned NIGHT branch as base. Put the ticket link in the PR body. Use the host's native PR tool; in Cursor, use `ManagePullRequest`'s `create_pr` with `draft` enabled, `branch_name` set to `issue-N` and `base_branch` set to NIGHT. Continue using this PR as you push later commits.

Done when the assigned behavior and required tests are implemented, the candidate is pushed and the draft PR exists, or unfinished work has a recorded reason.

## 3. Run one complete code review

Fetch and merge current NIGHT changes into your branch. On conflict, push the committed pre-merge HEAD and [return both commit SHAs and conflicted files](../SKILL.md#return-the-assigned-result) for the [Coordinator to resolve](coordinator.md#resolve-merge-conflicts). After it resumes you with the pushed resolution, run `git merge --abort` to clear your failed local merge, fetch and fast-forward your branch to that resolution.

After integration, run the affected verification, commit and push the candidate. The review compares committed output; uncommitted work is outside it.

Call the Skill tool with "code-review" for the main reviewer in this session. Perform preparation and aggregation here. Supply the full NIGHT commit actually integrated before this review as the fixed point, not merely the initial dispatch commit. Supply the pushed candidate, task material and this run's `review-axis` settings from the [common tools operation](../SKILL.md#use-this-runs-tools). Each axis assignment includes the repository, Worker branch and pushed candidate SHA through [Prepare an assignment](../SKILL.md#prepare-an-assignment), together with its assigned review instructions. Code review owns the three axes, isolation, verification and aggregation. Use [native dispatch](../SKILL.md#send-a-native-cloud-agent), then [receive results](../SKILL.md#wait-and-continue) within that professional method. Obtain the checked per-axis reports before returning to implementation.

Done when a complete review has returned checked reports or an explicit missing/invalid review requiring recovery.

## 4. Read and handle the review

Call the Skill tool with "principle-fix-root-causes" for the findings you handle.

Preserve original reports, dispositions and limitations.

First handle findings belonging to this ticket's behavior, applicable decisions, accepted baselines and changed behavior. Fix supported defects. An in-ticket finding you do not fix needs concrete evidence disproving that specific claim; a true fact about nearby code is not a refutation. Scope comes from the actual task, not a required Owns field or the number of files touched.

Include supported unrelated defects in the work report instead of expanding the ticket.

Fix and verify the implementation. For necessary follow-up review, preserve reports that still cover the output and dispatch only the missing or affected axes, using their existing `code-review` references and the updated pinned comparison. A missing axis is not a pass.

Do not loop reviews merely to obtain zero findings.

Done when every finding has a supported disposition and required review evidence is valid for the output or explicitly unavailable.

## 5. Verify the final output and return it

On the Coordinator's instruction to hand blocked work back, enter this step directly and report `incomplete`. Preserve unfinished output and state which implementation, review or proof could not be performed; those unavailable steps are not prerequisites for an honest handback.

After fixes and any necessary further integration, verify the final committed output against the ticket and baselines. Rerun affected proof; reuse results only when they still cover that output. Read the task once more as the owner will read the result. Report `incomplete` if any required behavior, review or verification is unfinished or failed, and state the reason; otherwise report `complete`.

For `complete`, commit and push the final output to the assigned branch. For `incomplete`, push saved commits when possible and state any work that remains only in your environment.

Write the work report for the Coordinator. Include:

- The ticket number and `complete` or `incomplete`.
- The PR address, if created, the Worker branch and full output SHA.
- What you implemented, which commit was reviewed, and how you fixed or rejected the review findings, with the supporting evidence.
- The verification commands actually run and their results, consequential decisions, unrelated findings, and any unfinished work with its reason.

[Return the report to the Coordinator](../SKILL.md#return-the-assigned-result), with its evidence in the reply text so the local Coordinator can write the PR body.

The Coordinator writes the final PR body and owns landing and delivery.

Continue the same branch when the Coordinator sends an in-ticket correction through the [native channel](../SKILL.md#wait-and-continue); fix, verify and return the new evidence.

Done when your final reply has returned the ticket's work report and actual code location, or has reported the delivery failure and the work it left unfinished.
