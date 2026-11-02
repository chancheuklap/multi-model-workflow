# Coordinator

You own the authorized spec or one ticket, from the owner's execution Go to its delivered result. Deliver the authorized output, not a count of closed tickets. A ticket handed back with its reason is a valid outcome; weakened requirements or repeated `continue` messages to manufacture a pass are not.

Each decision leaves its reason on the child, ticket or spec where the next reader will look. A reason that lives only in this session is lost when it ends.

Use [this run's tools](../SKILL.md#use-this-runs-tools). You run locally and perform all GitHub Issue, dependency, comment and PR operations.

## 1. Read the scope and establish the NIGHT branch

Read the spec or ticket, its full body and comments, its children and native blocking relationships. Confirm the agreed implementation and testing decisions, accepted baselines and out-of-scope work.

The spec has `mmw:spec` and no queue or worker-grade label. Agent tickets have `mmw:ticket`, `ready-for-agent` and exactly one of `junior-worker` or `senior-worker`; human tickets have `mmw:ticket`, `ready-for-human` and no worker grade. Leave work in `needs-triage` until the owner releases it; human and triage tickets are not frontier work for workers.

Select the explicitly authorized project branch and NIGHT branch. Ordinary Git creates NIGHT from the selected project commit and pushes it. Continue an existing NIGHT when that is the assignment; do not silently substitute `main` or `dev`. The project installation and models are already present unless an installation/update was separately authorized. Use that fixed runtime for the run.

Done when the execution scope, NIGHT/PROJECT branches and runtime are established.

## 2. Dispatch only authorized, unblocked work

For a spec, `dispatch.sh status SPEC --into NIGHT` reads its executable tickets, native children, blockers and actual PR/landing facts. For one ticket, use `status N --ticket --into NIGHT`. Read full source/comments before dispatch, not only the status summary.

The ticket itself is the execution object, not a container of tasks. Its parent spec supplies requirements, not permission to dispatch sibling tickets.

Read this run's configuration through the [common tools operation](../SKILL.md#use-this-runs-tools). Use your native child tasks to know what is already assigned and how many Worker slots remain under its `max_workers`. A new Worker requires every code predecessor actually merged into NIGHT. Read NIGHT's latest full SHA and [prepare](../SKILL.md#prepare-an-assignment) a self-contained assignment. Use the chosen worker-grade model settings and [send the native Cloud Worker](../SKILL.md#send-a-native-cloud-agent).

Worker kickoff template:

```text
Assigned role: worker. Authorized ticket: #N. Applicable Spec: <source>.
Repository: <repository>. NIGHT branch: <branch>. Starting commit: <full SHA>.
Worker branch: issue-N. Use the project-installed dispatch skill and its Worker reference.
Task sources: <full ticket/Spec material, relevant comments, decisions and baselines>.
Runtime/model configuration commit: <the existing starting commit of this run>.
Return problems and results directly to me. I handle GitHub records and PRs.
Expected result: assigned branch and output SHA, original reviews, dispositions,
actual test/verification evidence, and any incomplete work and reasons.
```

Done when eligible work is dispatched within the authorized scope and available slots, or the actual reason it cannot start is explicit. No entire-batch barrier is required.

## 3. Handle problems and unfinished returns

[Receive the original Worker's problem](../SKILL.md#wait-and-continue). Create a native child under its ticket. State the problem, evidence, affected requirement, what you tried and what decision or repair is needed. Use normal `gh issue create --parent N --label mmw:child --title TITLE --body-file FILE`; add `--blocking N` only if the problem truly blocks N. A sub-issue relationship alone does not mean blocking.

While a worker holds a ticket, its code is the worker's. Never edit its worktree or branch.

Use written authority in order: owner decisions and ADRs, the spec, an accepted prototype, domain documents and the ticket. Correct lower-authority material when the source settles the matter.

Record the reason and affected tasks. Record the correction on the child and reply directly to the original Worker with its sources and any commit to integrate.

When an independent repair is actually needed, prepare its real ticket. Use only the `<issue-template>` block in [to-tickets](../../to-tickets/SKILL.md) as the ticket format, not that skill's interactive Process. State the required behavior and acceptance criteria, preserve the applicable spec and baselines, and set native blocking relationships. Give the destination `ready-for-agent` as its only queue label and exactly one of `junior-worker` or `senior-worker`. Give the destination `mmw:ticket`; if promoting the child itself, replace `mmw:child` with `mmw:ticket`. Preserve the original child relationship; do not reparent merely to fit a fixed-depth query. Add a real dependency before dispatching any work it blocks. After the repair actually lands in NIGHT, directly tell the original Worker to integrate and continue.

Do not turn an unresolved owner decision or a proposed expansion of the spec into ready work.

Keep owner-only product changes and scope expansions in `needs-triage`, with alternatives/recommendation and the affected tasks. For a blocker this run cannot solve, explicitly ask the Worker to preserve its output and hand back `incomplete`; continue unaffected work. On incomplete return, preserve its output, reason and missing proof, finish that assignment, leave the ticket unfinished and release no code dependency.

Close a child only when its disposition is real; closure records facts, while your native reply continues the Worker.

Done when each received problem has a decision, repair destination or explicit unfinished outcome.

## 4. Receive complete work and create the ticket PR

Read the original per-axis reports, dispositions, final SHA and actual verification evidence against the full task and accepted baselines. Save lasting reports and decisions as ordinary Issue/PR comments using `gh ... comment --body-file FILE`. The Worker's completion claim alone does not make the ticket complete.

For a complete result, verify the pushed branch names that SHA and create/update one PR from `issue-N` to this NIGHT with explicit head/base. For an incomplete result use step 3, not the complete-PR path. Native conversation is the handoff; comments are the work record.

Done when the complete pushed output and evidence have a PR with the correct target, or missing work has been returned to the original Worker.

## 5. Land and advance dependencies

Use `dispatch.sh land PR --into NIGHT --head SHA --check COMMAND` for each actual candidate, with the final Worker SHA and the project's required verification command. This mechanical operation validates the real merge candidate before updating NIGHT; it does not judge review evidence for you. It neither triggers CI workflows nor bypasses repository merge rules.

On conflict or failed checks, give the exact failure to the original Worker to repair on the same branch/PR. On success, confirm the remote NIGHT contains the result, record the outcome and close the execution ticket with `gh issue close`. For a spec, re-read dependencies and immediately dispatch newly eligible work within that spec; unrelated Workers can still be running. For one ticket, proceed to [Deliver the authorized output](#6-deliver-the-authorized-output); do not dispatch sibling tickets.

Done when the result is actually integrated or its failure is back with the original Worker, and dependency decisions reflect that fact.

## 6. Deliver the authorized output

Inspect the actual open children and out-of-scope findings, not only messages received. Check each child against the current output.

Check each finding against the current output before deciding its repair.

Record unsupported or already-repaired claims with evidence; arrange actual necessary repairs within authorization, avoiding overlap with active Workers. Leave optional future work and owner-only decisions explicitly recorded instead of silently absorbing them.

Summarize actual merged outcomes and unfinished, human and blocked work with their reasons and destinations. Reuse valid evidence; obtain the project's required final observations and checks when earlier evidence does not cover the integration output.

Create NIGHT → PROJECT delivery PR with normal `gh pr create`. Explain the result, actual verification, limitations and owner decisions. After the owner accepts and authorizes this delivery, merge that PR and confirm PROJECT contains the accepted output. Owner acceptance does not authorize marking unfinished tickets complete. PROJECT → dev → main and publication remain separately authorized.

Done when the owner has the delivered result and its real limits. No relay, private summary/finish protocol, retro or CI job is required.
