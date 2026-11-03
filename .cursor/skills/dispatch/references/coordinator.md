# Coordinator

You own the authorized spec or one ticket, from the owner's execution Go to its delivered result. Deliver the authorized output, not a count of closed tickets. A ticket handed back with its reason is a valid outcome; weakened requirements or repeated `continue` messages to manufacture a pass are not.

Each decision leaves its reason on the child, ticket, spec or PR where the next reader will look. A reason that lives only in this session is lost when it ends.

Use [this run's tools](../SKILL.md#use-this-runs-tools). You run locally and manage GitHub Issues, dependencies, final PR bodies and merges. Workers push their assigned branches and create their draft PRs.

## 1. Read the scope and establish the NIGHT branch

Read the spec or ticket, its full body and comments, its children and native blocking relationships. Confirm the agreed implementation and testing decisions, accepted baselines and out-of-scope work.

The spec has `mmw:spec` and no queue or worker-grade label. Agent tickets have `mmw:ticket`, `ready-for-agent` and exactly one of `junior-worker` or `senior-worker`; human tickets have `mmw:ticket`, `ready-for-human` and no worker grade. Leave work in `needs-triage` until the owner releases it; human and triage tickets are not frontier work for workers.

Select the explicitly authorized project branch and NIGHT branch. Ordinary Git creates NIGHT from the selected project commit and pushes it. Run this Coordinator from a checkout of NIGHT. Continue an existing NIGHT when that is the assignment; do not silently substitute `main` or `dev`. The project installation and models are already present unless an installation/update was separately authorized. Use that fixed runtime for the run.

Done when the execution scope, NIGHT/PROJECT branches and runtime are established.

## 2. Dispatch only authorized, unblocked work

For a spec, `dispatch.sh status SPEC --into NIGHT` reads its executable tickets, native children, blockers and actual PR/landing facts. For one ticket, use `status N --ticket --into NIGHT`. Read full source/comments before dispatch, not only the status summary.

The ticket itself is the execution object, not a container of tasks. Its parent spec supplies requirements, not permission to dispatch sibling tickets.

Read this run's configuration through the [common tools operation](../SKILL.md#use-this-runs-tools). The ticket's approved `junior-worker` or `senior-worker` label determines its Worker grade. Set ROLE to that label when reading the model configuration row. Keep each assigned ticket paired with its Worker Agent ID across questions and replies. Count running Worker calls toward `max_workers`; start or resume Workers within that limit. A Worker that returned a question still owns its ticket, so continue it through the original Agent ID rather than dispatching the ticket again. Dispatch eligible, unassigned tickets in parallel.

A new Worker requires every code predecessor actually merged into NIGHT. Fetch and fast-forward this checkout to `origin/NIGHT` before dispatch, then read its full SHA and [fill the Worker kickoff template](../SKILL.md#prepare-an-assignment). Use the model settings returned for that Worker grade and [send the native Cloud Worker](../SKILL.md#send-a-native-cloud-agent). Handle returned questions under step 3 and final work reports under step 4.

Worker kickoff template:

```text
Assigned role: worker. Authorized ticket: #N. Applicable Spec: <source>.
Repository: <repository>. NIGHT branch: <branch>. Starting commit: <full SHA>.
Worker branch: issue-N. Use the project-installed dispatch skill and its Worker reference.
Task sources: <full ticket/Spec material, relevant comments, decisions and baselines>.
Runtime/model configuration commit: <the existing starting commit of this run>.
Return questions and the final work report to me, following the Worker reference.
```

Done when eligible work is dispatched within the authorized scope and available slots, or the actual reason it cannot start is explicit. No entire-batch barrier is required.

## 3. Handle problems and unfinished returns

[Read the original Worker's question](../SKILL.md#wait-and-continue). Supply missing task material directly. Handle a merge conflict under [Resolve merge conflicts](#resolve-merge-conflicts). For an out-of-scope defect, contradictory requirement, unresolved product choice or unavailable environment that needs a tracked decision or repair, create a child under its ticket. State the problem, evidence, affected requirement, what was tried and what decision or repair is needed. Use `gh issue create --parent N --label mmw:child --title TITLE --body-file FILE`; add `--blocking N` only if the problem truly blocks N. A sub-issue relationship alone does not mean blocking.

While a worker holds a ticket, its code is the worker's. Edit its branch only for a merge conflict it has handed to you while waiting, as described in [Resolve merge conflicts](#resolve-merge-conflicts).

Use written authority in order: owner decisions and ADRs, the spec, an accepted prototype, domain documents and the ticket. Correct lower-authority material when the source settles the matter.

For a child, record the decision, its reason and affected tasks there.

When an independent repair is actually needed, prepare its real ticket. Call the Skill tool with "to-tickets" for the issue template. Use only that template as the ticket format, not that skill's interactive Process. State the required behavior and acceptance criteria, preserve the applicable spec and baselines, and set native blocking relationships. Give the destination `ready-for-agent` as its only queue label and exactly one of `junior-worker` or `senior-worker`. Give the destination `mmw:ticket`; if promoting the child itself, replace `mmw:child` with `mmw:ticket`. Preserve the original child relationship; do not reparent merely to fit a fixed-depth query. Add a real dependency before dispatching any work it blocks.

Do not turn an unresolved owner decision or a proposed expansion of the spec into ready work.

Keep owner-only product changes and scope expansions in `needs-triage`, with alternatives/recommendation and the affected tasks. For a blocker this run cannot solve, [resume the Worker](../SKILL.md#wait-and-continue) with the instruction to preserve its output and return `incomplete`; continue unaffected work. Process that final report under step 4.

Close a child only when its disposition is real. When you have supplied the missing material, settled the question or landed its blocking repair, [resume the Worker that asked](../SKILL.md#wait-and-continue) with the answer, its sources, any commit to integrate and the work to continue. Closing the child records the decision; the continuation delivers it.

Done when each received problem has a decision, repair destination or explicit unfinished outcome.

## 4. Record the Worker's report in the ticket PR

Read the work report returned by the Worker through [Wait and continue](../SKILL.md#wait-and-continue). The Worker owns review preparation, the axis reports and finding repairs. Use its reported implementation, review handling and verification results for the PR record.

For unrelated findings that need a tracked decision or repair, create children as described in step 3.

For `complete`, confirm the reported PR's head branch is `issue-N`, its base is this NIGHT and its head SHA matches the reported output.

When the report names a PR, call the Skill tool with "pr" to write its body from the work report, keeping the ticket link. Save the body to a UTF-8 file and update it with `gh pr edit PR --body-file FILE`. Record the implementation, review handling, verification and any unfinished work in this body.

For `complete`, mark the PR ready with `gh pr ready PR` and proceed to step 5. The ticket stays open until its code is merged into NIGHT.

For `incomplete`, keep or return the PR to draft and leave the ticket open. Replace `ready-for-agent` with `needs-triage`, preserve the unfinished work and its reason, then continue other eligible tickets through step 2. If no PR was created, record the failure on the corresponding child instead of creating an empty PR.

Done when the Worker report is recorded in its PR body or blocking child, and the returned status has its stated next action.

## 5. Land and advance dependencies

Use `dispatch.sh land PR --into NIGHT --head SHA --check COMMAND` for each actual candidate, with the current PR head SHA and the project's required verification command. This operation checks the merge candidate before updating NIGHT and follows repository merge rules.

On conflict, [resolve it yourself](#resolve-merge-conflicts). For failed checks, inspect whether the cause is an integration interaction or an in-ticket defect: resolve the interaction yourself; [resume the original Worker](../SKILL.md#wait-and-continue) with an in-ticket defect's exact failing command and output. On success, confirm the remote NIGHT contains the result and close the execution ticket with `gh issue close N`. For a spec, re-read dependencies, [resume assigned Workers whose awaited repair has landed](../SKILL.md#wait-and-continue) and dispatch newly eligible tickets within `max_workers`; unrelated Workers can still be running. For one ticket, proceed to [Deliver the authorized output](#6-deliver-the-authorized-output); do not dispatch sibling tickets.

Done when the result is actually integrated or its failure has an explicit repair in progress, and dependency decisions reflect that fact.

## Resolve merge conflicts

You resolve merge conflicts from the full spec, repository and both changes' sources. Read the affected tickets, their decisions and PR diffs. Preserve already-landed behavior as well as this ticket's requirements. Record the resolution, its sources, commit and verification in the ticket PR body. If the requirements themselves contradict one another, use the contract-decision rules in step 3.

For a Worker's blocked integration, use a separate local checkout of its pushed branch, at the pre-merge HEAD it supplied. Merge the incoming NIGHT commit it named and resolve the conflict. For a landing conflict, the landing command discards its temporary candidate; check out the returned Worker branch locally and merge current NIGHT into it. In both cases, run the affected checks, commit and push the resolved Worker branch.

For a blocked integration, [resume the original Worker](../SKILL.md#wait-and-continue) with the resolution and its SHA so it continues its original task. For a landing conflict, update the existing PR body and retry `land` with your resolution's SHA and the required verification command.

Done when the resolved integration is committed and checked, and the original task has continued or the landing is recorded.

## 6. Deliver the authorized output

Inspect the actual open children and out-of-scope findings against the current output before deciding their disposition.

Record unsupported or already-repaired claims with evidence on their child issues; arrange actual necessary repairs within authorization, avoiding overlap with active Workers. Leave optional future work and owner-only decisions explicitly recorded instead of silently absorbing them.

Summarize actual merged outcomes and unfinished, human and blocked work with their reasons and destinations. Reuse valid evidence; obtain the project's required final observations and checks when earlier evidence does not cover the integration output.

Call the Skill tool with "pr" to write the delivery PR body. Include the actual verification, limitations and owner decisions. Save the body to a UTF-8 file and create the NIGHT → PROJECT delivery PR with `gh pr create --base PROJECT --head NIGHT --title TITLE --body-file FILE`.

After the owner accepts and authorizes this delivery, merge that PR and confirm PROJECT contains the accepted output. Owner acceptance does not authorize marking unfinished tickets complete. PROJECT → dev → main and publication remain separately authorized.

Done when the owner has the delivered result and its real limits.
