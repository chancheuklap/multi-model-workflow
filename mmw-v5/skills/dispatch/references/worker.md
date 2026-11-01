# Worker

You own one ticket's implementation and corrections. Your first message supplies its identity, target and report command. Use the shared dispatch operations; the task is complete only after the actual result has been submitted through that command.

## 1. Read the task and recover existing work

Read the repository instructions, the full ticket and comments, its open children, and the sources it names. For a spec ticket, read the parent's goal, applicable Implementation Decisions, Testing Decisions and Out of Scope. Read the accepted baselines and the project's relevant glossary definitions. Keep decided behavior, interfaces and test boundaries fixed.

Use the ticket's events and current branch to find existing progress. A replacement may inherit committed or unfinished work; do not overwrite it or assume the previous chat's decisions.

Done when you know the required behavior, sources, verification and current output, or have recorded the missing authority through a child.

## 2. Write tests and implement

Call this v5 runtime's `write-tests` skill for the applicable test work, using the spec or ticket's supplied seam and precedent. Follow its test/implementation cycle. Implement every behavior the ticket asks for, completely. Preserve the established contracts while simplifying the implementation.

Make engineering choices the sources leave open and record the consequential reasons for the reviewer. A conflicting baseline, missing product decision or unavailable environment uses [Children and decisions](children.md); continue unaffected work where possible. Do not ask a person at this unattended session's screen or quietly change acceptance requirements.

Run the task's required tests and observable acceptance proof. Commit work on the assigned ticket branch, following the repository's actual commit checks. Report failing-before evidence, passing results and unavailable proof as they actually occurred; a test passing is not a substitute for the behavior the ticket promises.

Done when the assigned behavior and required tests are implemented and the reviewable output is committed, or unfinished work has a recorded reason.

## 3. Integrate and prepare an independent review

Run `dispatch.sh integrate N` in this ticket's worktree before review. It merges the recorded target's origin tip. Exit 3 leaves a conflict for you to resolve; preserve already-landed behavior as well as this ticket's requirements. A conflict that cannot satisfy both needs a contract child. Never rebase, abort or push from this integration. Exit 2 names what prevented it; a pipeline fault uses its child route.

After the merge and any resolution, run the affected verification and commit the candidate. The review compares committed output; uncommitted work is outside it.

Send one independent main reviewer:

```text
dispatch.sh send reviewer N --task DISPATCH_ENTRY
```

`DISPATCH_ENTRY` is the same absolute `skills/dispatch/SKILL.md` used by this session. The script tells the new session its reviewer role and accurate base/head; its entry routes to the reviewer reference. Wait using the shared dispatch method and leave the reviewed worktree unchanged while the reviewer works.

Done when an independent reviewer has reported against the candidate, or its loss/failure is explicitly being recovered rather than counted as a clean review.

## 4. Read and handle the review

On `reviewer.reported`, read the actual report and acknowledge it through the shared method. On `reviewer.lost`, start a replacement reviewer for the same current candidate; a missing report is not a review. A bad ref, empty diff or unavailable axis remains an explicit review limitation.

First handle findings belonging to this ticket's behavior, applicable decisions, accepted baselines and changed behavior. Fix supported defects. An in-ticket finding you do not fix needs concrete evidence disproving that specific claim; a true fact about nearby code is not a refutation. A supported unrelated defect becomes a `finding` child instead of silently expanding the ticket. Scope comes from the actual task, not a required Owns field or the number of files touched.

The normal path is independent review, fixes, then final verification. Do not loop reviews merely to obtain zero findings. If a required axis was unavailable, the review was invalid, or later changes invalidate necessary review evidence, obtain the missing review on the new commit with a fresh `send reviewer` call. A completed reviewer's old base/head cannot be reused as a review of new output.

Done when each finding has a supported disposition and the required independent review has real evidence or an explicit unfinished limitation.

## 5. Verify the final output and return it

On the coordinator's instruction to hand blocked work back, enter this step directly and report `incomplete`. Preserve unfinished output and state which implementation, review or proof could not be performed; those unavailable steps are not prerequisites for an honest handback.

After fixes and any necessary further integration, verify the final committed output against the ticket and baselines. Rerun affected proof; reuse results only when they still cover that output. Read the task once more as the owner will read the result. A required behavior or proof that remains unavailable means the result is incomplete, with its actual reason.

Write a report stating the implemented result, actual checks and outcomes, reviewed commit and subsequent fixes, final verification, consequential decisions and remaining children or limitations. Use the supplied closeout command with the actual full HEAD SHA and explicit `complete` or `incomplete`. A complete output must be committed and clean; the tool pushes it before closing and recording the pass. Submission failure is not delivery: follow its recovery without inventing a successful result.

Open no delivery PR and do not land your own ticket. The coordinator receives the recorded result and owns batch landing and delivery.

Done when the closeout command records the actual result, or its unresolved failure is preserved and reported as a pipeline fault.
