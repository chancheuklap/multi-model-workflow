# Dispatch reviewer

You remain the Coordinator. Enter only from [Review the night branch](coordinator.md#6-review-the-night-branch), after every authorized ticket is landed or explicitly unfinished and no Worker is running or waiting for an answer. This procedure returns one report to that step; it does not dispatch implementation work.

## 1. Send

Run `dispatch.sh spawn review --host HOST`. Send each card to a **FRESH AGENT** as [Dispatch](../SKILL.md) describes. Run them in parallel and wait for all results.

One command prints this night's cards: Standards, Spec, and Tests, and the second verifier. Each subagent starts in its own cloud checkout at the night branch's reviewed commit. Spec is omitted when the night has no spec. Roles listed under `skipped` do not run. A command error is a limitation of this review, not a pass.

Each card's prompt names what that reviewer uses: the diff, the pinned comparison, the reviewed commit, the spec or `Spec: none`, the landed tickets, any standards files, and, for the verifier, the feature files. The reviewer does not choose a different range.

Done when every printed card has returned, or a missing result is recorded as a limitation.

## 2. Check

You are checking the reports you were handed, against the reviewed commit named in them. You are not reviewing the diff again from scratch.

Check each finding against that commit. Read the cited rule or requirement and the code. Keep a finding the commit supports. Drop one it does not, and write the reason. Keep a runtime claim when a rerun shows the failure it names. When a reproduction cannot be rerun, mark it unverified and write the reason.

For each kept finding, identify the affected approved requirement and whether the evidence shows a defect introduced by this work, an existing defect, or an uncertain cause. A valid finding does not by itself authorize a repair.

Done when every finding is kept with that attribution, dropped with a reason, or unverified with a reason.

## 3. Aggregate

Write the checked reports under `## Standards`, `## Spec`, and `## Tests`. Keep each axis's own evidence and its judgement-call labels. Leave the three axes separate. A pass on one axis leaves the others as they are. Under each axis, give the dropped count and the reasons, and any unverified limitation. When none of that axis's findings survive, write "no verified findings" and the limitations. A missing axis is a limitation in its own section.

End with the count of supported findings in each axis.

Then state the verifier result separately from the three axes: `Verifier: pass`, `Verifier: fail`, `Verifier: skipped`, or `Verifier: unavailable`. When a verifier ran, include the commands and results. A judgement call stays under its axis with that label. It is not a hard finding.

Return this report to [Review the night branch](coordinator.md#6-review-the-night-branch) for disposition within the approved scope. Judgement calls are carried to the delivery result. The report covers the named night commit, not unlanded ticket PRs.

