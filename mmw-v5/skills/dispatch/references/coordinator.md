# Coordinator

You own the authorized spec batch or one ticket, from the owner's execution Go to its delivered result. The night's output is a batch the user can accept, not a count of closed tickets. A ticket handed back with its reason is a valid outcome; weakened requirements or repeated `continue` messages to manufacture a pass are not.

Each decision leaves its reason on the child, ticket or spec where the next reader will look. A reason that lives only in this session is lost when it ends. Use [Send](../SKILL.md#send-an-independent-session), [Wait](../SKILL.md#wait-read-and-acknowledge), [Return](../SKILL.md#return-the-assigned-result) and [Handle command failures](../SKILL.md#handle-command-failures) at the steps below.

## Choose the authorized scope

For a spec batch, follow steps 1–5 below. For one ticket, follow [Deliver one ticket](#deliver-one-ticket); the ticket itself is the execution object, not a container of tasks. Its parent spec supplies requirements, not permission to dispatch sibling tickets.

## Deliver one ticket

Read the authorized ticket, comments, children, applicable spec decisions and baselines. Confirm the explicit integration target within the owner's authorization. Use [this run's tools](../SKILL.md#use-this-runs-tools) and [Send an independent session](../SKILL.md#send-an-independent-session) with role `worker`, its ticket N and the installed dispatch entry as FILE, or the caller's supplied assignment. Outside an open watch, supply `--into BASE`; Send opens the single-ticket watch before starting the Worker.

[Wait, read and acknowledge](../SKILL.md#wait-read-and-acknowledge). Handle children under the authority and repair rules in [Handle a result or child](#3-handle-a-result-or-child), using [Record and resolve a child](../SKILL.md#record-and-resolve-a-child) and [Resume a session](../SKILL.md#resume-a-session); skip that step's Spec-wide status/advance actions. For a stopped Worker, preserve its recorded work and identity and decide recovery within the same ticket's authorization.

After the Worker returns `complete` or `incomplete` and related matters have a disposition, run `dispatch.sh land N`. Complete attempts landing; incomplete preserves the work and ends the ticket's hold/watch. Read the actual `landed`, `returned` or `bounced` result and watch state: exit 0 alone does not prove code was merged. A bounce remains unfinished and may need another authorized attempt on the same ticket. Report the actual output, verification and limitations through [Return](../SKILL.md#return-the-assigned-result); do not enter the Spec's advance/summary loop or start sibling work.

Done when the ticket has its actual landing or unfinished disposition, and the single-ticket watch is closed or its named recovery remains explicit.

## 1. Read and open the batch

Read the spec, its tickets and their native blocking relationships. Confirm the agreed implementation and testing decisions, accepted baselines and out-of-scope work. The spec has `mmw:spec` and no queue or worker-grade label. Agent tickets have `mmw:ticket`, `ready-for-agent` and exactly one of `junior-worker` or `senior-worker`; human tickets have `mmw:ticket`, `ready-for-human` and no worker grade. Leave work in `needs-triage` until the owner releases it; human and triage tickets are not frontier work for workers.

Choose the explicit batch integration branch (`BASE`) and receiving project branch (`PROJECT`) within the owner's authorization. Run `python3 ../../tools/setup-mmw/scripts/check.py` with the worker/reviewer roles this run needs. Resolve the script path from the dispatch skill directory before running it from the consuming repository. Repair a missing environment condition; do not invent a substitute passing check.

Open from the checkout whose wakes must receive the batch results:

```text
dispatch.sh open SPEC --into BASE --project PROJECT --worker-task DISPATCH_ENTRY --reviewer-task DISPATCH_ENTRY
```

`DISPATCH_ENTRY` is this runtime's `skills/dispatch/SKILL.md`, resolved to an absolute path. Both roles enter the same skill and use their assigned route. No per-ticket workflow file is needed. The script opens the watch and starts the existing relay and watchdog.

Done when the watch records this coordinator and the explicit target, with the shared task entry available to later sessions.

## 2. Advance the frontier

Run `dispatch.sh status SPEC`, then `dispatch.sh advance SPEC`. The script handles passed outputs, releases ended holds, reads dependencies again and starts the eligible tickets within `max_workers`. It selects each worker's configured model. Do not maintain a second frontier or merge tickets yourself alongside `advance`.

Exit 4 reports refused starts; read each reason rather than blindly retrying it. Exit 2 reports a condition that prevented some work; read the actual state before retrying because other outputs may already have landed. If workers remain active, [wait through the common operation](../SKILL.md#wait-read-and-acknowledge). If none remain, inspect why queued work cannot start.

Done when every attempted operation has a known outcome and the session is waiting for active work or handling a named obstruction.

## 3. Handle a result or child

Handle each wake in arrival order, one wake at a time. [Read and ack](../SKILL.md#wait-read-and-acknowledge), run `status SPEC`, and take every action the current state needs, not only the ticket named by the wake.

| Recorded result | Action |
| --- | --- |
| `ticket.passed` or newly eligible work | Run `advance SPEC`; it lands the exact output and recalculates dependencies. |
| `ticket.returned` | Read the unfinished result and preserve its workspace for triage; continue other work that can proceed. |
| `ticket.refused` or a refused start | Resolve its stated prerequisite within scope, then advance. |
| `worker.lost` or a stopped worker whose hold remains | Use the recorded session identity. `retract N` only releases a worker confirmed stopped and preserves its work; then advance can start its replacement. |
| `child.opened` | Read [Record and resolve a child](../SKILL.md#record-and-resolve-a-child) and the actual child. Settle the matter from existing authority or leave an owner-only choice explicit. |
| `watchdog:` alert | Read its named condition. Silence alone does not prove a worker is gone. Repair the condition or explicitly suspend; do not kill unrelated processes. |

While a worker holds a ticket, its code is the worker's: correct the requirements or baseline it works from, then tell it through `resume`; never edit its worktree or branch. A replacement has none of the instructions sent only inside the old session, so record decisions on the tracker and name them in its continuation.

For a `contract` child, use written authority to settle the conflict: owner decisions and ADRs, the spec, an accepted prototype, domain documents and the ticket. Correct lower-authority material when the source settles the matter. Edit a tracker-owned spec or ticket directly, recording the change and reason. For a repository-owned baseline, use a checkout tracking `origin/BASE`, outside the worker's worktree: fetch, commit the correction and its proof, run `MMW_BASE_REF=PARENT scripts/check` on that commit, then fast-forward push. `PARENT` is the correction commit's parent. This corrects the worker's input while it waits; the worker's output remains theirs. Correct every not-yet-landed ticket derived from the same bad statement. Record the authority, published items corrected and tickets checked on the child, route it `fixed`, then [resume the active worker](../SKILL.md#resume-a-session) with the exact correction and any commit to integrate.

When no authority settles a blocking contract, or the correction would overturn the owner's decision or expand the spec, leave the choice to the owner. Add `needs-triage` to the child. Find every not-yet-started ticket derived from the same spec decision and move it from `ready-for-agent` to `needs-triage`. Comment on the child with the unresolved options, your recommendation and the ticket numbers moved; leave it open. For a ticket already being worked, use `resume N MESSAGE` to tell its worker to preserve its work and close out as `incomplete`, with the reason pointing to this child. Read and acknowledge `ticket.returned` before treating that worker's task as handed back. Continue the batch's unaffected work.

Use the same incomplete handback for an environment fault that cannot be repaired in this run; a fault affecting the running pipeline uses Suspend and resume. A `decision` child with a default already taken needs no intervention: the worker continues within the existing scope and decisions, and the owner reads the recorded choice in delivery.

After handling the state, run `advance SPEC` once. When it leaves no frontier work and no active worker, enter the closing pass.

## 4. Close the remaining findings

Run `dispatch.sh findings SPEC`. A `finding` wakes nobody, so notifications are not an inventory of remaining work.

Check each finding against the current batch output before deciding its repair. Record a finding that never held as `stale --reason invalid`; one repaired elsewhere as `stale --reason fixed-elsewhere`. An actual repair is `fixed`, not stale. Use the [common child report and commit rules](../SKILL.md#record-and-resolve-a-child).

Judge each supported finding in order, first match wins:

1. Does its repair overlap another still-open ticket's assigned work? Make it a ticket blocked by that work; repairing alongside it risks conflicting changes.
2. Is the acceptance proof green while the behavior it names is broken or never reached? Make it a `senior-worker` ticket asking for a negative control.
3. Does the repair require coupled design across files, where how one is fixed decides how another must be fixed? Make it a `senior-worker` ticket. A name repeated through prose is mechanical work, not design coupling.
4. Nothing matched: fix it yourself. The default is to fix it, not to open a ticket.

The ones you fix: work on the batch branch after workers stop. Fetch, commit only the finding's cause and its proof, run the applicable repository checks, then fast-forward push before recording it `fixed`. Do not repair concurrently with another worker's overlapping change.

The ones that become tickets: open as few as possible. A finding that stands alone becomes a ticket in place by rewriting its body; findings with one implementation can share one destination. Use only the `<issue-template>` block in [to-tickets](../../to-tickets/SKILL.md) as the ticket format, not that skill's interactive Process. These tickets execute in the already-authorized batch. State the required behavior and acceptance criteria, preserve the applicable spec and baselines, and set native blocking relationships. Give the destination `ready-for-agent` as its only queue label and exactly one of `junior-worker` or `senior-worker`. Use `senior-worker` for the cases above; otherwise use the worker-grade selection in [To Tickets: Draft vertical slices](../../to-tickets/SKILL.md#3-draft-vertical-slices). Then use `became-ticket` with the actual destination; the route gives it `mmw:ticket`, removes the previous child or problem kind and links it to the spec, but does not write its body or queue it for you. Read the destination back to confirm its task, labels, parent and blockers. Do not turn an unresolved owner decision or a proposed expansion of the spec into ready work.

If new tickets belong in this batch, advance and continue the same loop. Leave optional future work and owner-only decisions explicitly recorded instead of silently absorbing them.

Done when every remaining finding has an evidenced resolution or an explicit destination the batch's summary can report.

## 5. Deliver the batch

Run `dispatch.sh summary SPEC` after active work, pending landings and findings are settled. It runs the repository's full checks on the actual integration output; it does not prove every prose acceptance requirement. Reuse valid evidence and obtain any product observation the spec requires that the recorded checks do not supply. Preserve unfinished, human and blocked outcomes honestly.

Create the delivery PR with `dispatch.sh pr --base PROJECT --head BASE --title TITLE --body-file FILE`. Explain the result, actual verification, limitations and owner decisions. The watch closes with summary; a later delivery repair is an explicit repair of that output, not permission to reopen the dispatch loop unnoticed.

Only after the user has accepted the pull request, run `dispatch.sh finish SPEC`. An open-ticket refusal needs the owner's disposition of that unfinished work; accepting the PR does not authorize marking it completed. Keep the delivery and unresolved tickets recorded until the existing finish conditions hold. Keep the exact checked version current when repairing a refusal. Do not merge the receiving project branch into the repository's default branch here; that remains the owner's release decision.

Done when the owner has the delivery and its limits, or acceptance has authorized finish and its actual result is reported.

## Suspend and resume

A fault in the running pipeline is a reason to suspend rather than spend more workers producing the same failures. `dispatch.sh suspend SPEC` preserves work and closes the watch. Read every resource or error it leaves. Resume through an explicit `open` with the same target and shared entry, then `advance` once the fault is repaired. Use the existing runtime to control its run; do not switch it to the version being built.
