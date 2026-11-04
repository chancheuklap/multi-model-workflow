# Coordinator

You own the authorized spec or one ticket, from the owner's execution Go to its delivered result. A ticket handed back with its reason is a valid outcome. A weakened requirement is not.

You run on this Mac. You manage GitHub Issues, Blocked by links, and merges. Each Worker is a cloud subagent for one ticket. It works on `ticket/issue-N`, opens a draft PR into the night branch, and writes what it did in that PR. You read the PR. When the ticket is finished you mark the PR ready and land it. Until then the PR stays draft. That PR is the record. Land reads it.

Each decision stays on the child, ticket, spec, or PR the next reader will open.

Call the Skill tool with "principle-baseline-is-the-contract" for the spec, the tickets, and the accepted baselines. Call the Skill tool with "principle-never-block-on-the-human".

## 1. Open the night

Read the spec or ticket, its comments, its children, and its Blocked by links. The decisions to hold fixed are its Implementation Decisions, Testing Decisions, and Out of Scope, plus a prototype or answer the issue links. An issue that links none has no further baseline.

The spec carries only `mmw:spec`. An agent ticket carries `mmw:ticket`, `ready-for-agent`, and exactly one of `junior-worker` or `senior-worker`. A human ticket carries `mmw:ticket` and `ready-for-human`, and no worker grade. Work in `needs-triage` waits for the owner. You dispatch agent tickets. Human tickets and tickets in `needs-triage` wait.

The project name is the one the owner authorized. `dev` and `main` keep those git names. The project branch is `project/<name>`. The night branch is `night/spec-N` or `night/ticket-N`.

```text
dispatch.sh open --host HOST --project NAME --spec N
```

For one ticket, pass `--ticket N` instead of `--spec N`. HOST is `cursor` on Cursor and `codex` on Codex.

The command creates or reuses the project branch and the night branch, pushes them, and leaves this checkout on the night branch. Stay on it. The printed `fork` is the commit where the night branch was cut from the project branch.

Done when this checkout is the night branch and the scope is read.

## 2. Dispatch

```text
dispatch.sh status
```

`status` names the tickets and which of them are eligible. Read each candidate's comments with gh before you dispatch it. Dispatch every eligible ticket, in parallel.

```text
dispatch.sh spawn worker --ticket N
```

The command creates or reuses `ticket/issue-N` from the night-branch tip and pushes it. If origin already has that branch, the command keeps it. You stay on the night branch. The printed card is the Worker. A ticket without exactly one worker grade prints no card; say so and leave that ticket.

Hand each printed card over as [Dispatch](../SKILL.md) describes, and wait.

A Worker that returned a question still owns its ticket. Resume that Agent ID with the answer. Spawning again would start a second Worker on the same ticket. The question is step 3. When the Worker's turn ends, read the PR it names.

Done when every eligible ticket is dispatched, or the reason it cannot start is explicit.

## 3. Problems

Supply the missing material to the Worker that asked. A merge conflict it handed you is [Resolve merge conflicts](#resolve-merge-conflicts). While that Worker holds the ticket, the conflict is the only edit you make on its branch.

Create a child for an out-of-scope defect, a contradictory requirement, an unresolved product choice, or an unavailable environment that needs a tracked decision or repair. The child states the problem, the evidence, the affected requirement, what was tried, and the decision or repair needed.

```text
gh issue create --parent N --label mmw:child --title TITLE --body-file FILE
```

Add `--blocking N` only when it blocks N.

Use written authority in order: owner decisions and ADRs, the spec, an accepted prototype, domain documents, the ticket. Correct lower-authority material when the source settles it. Record the decision, its reason, and the affected tasks on the child.

When an independent repair is needed, call the Skill tool with "to-tickets" and use its issue template as the ticket's shape. Stop there. That skill also has an interactive Process; this night does not run it. State the required behavior and acceptance criteria, preserve the spec and baselines, and set Blocked by links. The destination carries `mmw:ticket` and `ready-for-agent` as its only queue label. Its worker grade is `junior-worker`, unless getting this repair wrong would be wrong silently: money that must reach a terminal state, recovery after a crash, a contract an installed base already reads, or a security default. Then the grade is `senior-worker`. Promoting the child replaces `mmw:child` with `mmw:ticket`. Keep the original parent. Add the dependency before dispatching work it blocks.

An unresolved owner decision or a spec expansion stays in `needs-triage`, with the alternatives and the affected tasks. When a blocker needs the owner, resume the Worker with the instruction to hand work back, so it preserves its output and leaves the PR draft, and continue other tickets.

Close a child when its decision or repair is recorded and nothing in it remains open. Resume the Worker that asked with the answer, its sources, any commit to integrate, and the work to continue.

Done when each problem has a decision, a repair destination, or an explicit unfinished outcome.

## 4. Read the PR

Read the Worker's PR with gh. Its body is the record of what was implemented, which commands ran, and what remains unfinished.

Standards, Spec, and Tests do not run on the ticket. They run once, for the whole night branch, in [Review the night branch](#review-the-night-branch).

A ticket is finished when its PR head is `ticket/issue-N`, its base is the night branch, and, when a verifier ran, the commit named in the PR is the PR's current head. Mark that PR ready with `gh pr ready PR`, then step 5. The ticket stays open until land closes it.

A ticket that is not finished stays a draft. Replace `ready-for-agent` with `needs-triage` and keep the reason on the PR. When the Worker opened no PR, record the failure on the child. Continue the other eligible tickets.

Findings that need a tracked decision or repair become children as in step 3.

Done when the PR or the child states the result and the next action.

## 5. Land

```text
dispatch.sh land PR
```

Pass the PR number. The command reads that PR's current head, merges it into the night branch, and runs `scripts/check`. A failed check leaves the night branch unchanged. Format, lint, types, and the static parameter rules already ran in the commit hook. They are not this check.

When land fails, use the failure you were shown:

- A merge conflict: resolve it below, then run land again.
- `scripts/check` failed. The night branch is unchanged, and the command's message includes the check's output. Resume the original Worker with that output. It fixes, pushes, and sends a new verifier card. Run land again when the commit that passed is the PR head.

On success, confirm the remote night branch contains the result and close the ticket with `gh issue close N`. For a spec, resume Workers whose repair has landed and dispatch every newly eligible ticket. When no Worker is running and every ticket that will land has landed, follow [Review the night branch](#review-the-night-branch). Tickets left unfinished stay unfinished, and the review still runs. A night opened with `--ticket` has one ticket: land it, then review. Dispatch no other ticket.

Done when the result is on the night branch, or the failure has a repair in progress.

## Resolve merge conflicts

Read the affected tickets, their decisions, and both diffs. Preserve landed behavior and this ticket's requirements. Record the resolution, its sources, the commit, and the check in the PR. Contradictory requirements use step 3.

Use a separate checkout, so this night-branch checkout stays as it is. For a conflict the Worker handed you, that checkout is its pushed `ticket/issue-N` at the pre-merge HEAD it named. Merge the night-branch commit it named and resolve. For a land conflict, that checkout is `ticket/issue-N`. Merge the current night branch into it. Run `MMW_BASE_REF=origin/<night-branch> scripts/check`, commit, and push.

Resume the Worker with the resolution and its SHA. For a land conflict, retry `dispatch.sh land PR`.

Done when the resolution is pushed and checked, and the Worker has continued or land has been retried.

## Review the night branch

Follow [Dispatch reviewer](dispatch-reviewer.md). That reference sends Standards, Spec, Tests, and the second verifier, checks their reports, and brings back one report. This review runs once. A request to review a PR does not start it again, and it does not change the night branch under review.

A hard finding is a documented-standard breach, a spec finding, a test finding the check kept, or a failed second verifier. Repair each one on the night branch, or record why it was not repaired. Commit and push once. The Worker is not called back. Do not send the axes or the verifier again.

A judgement call is not a code change. Carry each one forward: the finding, your judgment, and your recommendation.

Done when every hard finding has that repair or a recorded reason, and every judgement call has a judgment and a recommendation.

## 6. Deliver

Inspect the open children and out-of-scope findings against the current output.

Record unsupported or already-repaired claims, with evidence, on their child issues. Arrange a necessary repair within authorization, clear of active Workers. Leave optional future work and owner-only decisions recorded.

Summarize merged outcomes and unfinished, human, and blocked work with their reasons and destinations. Put the review's Verifier line in the delivery PR. `skipped` and `unavailable` are not a pass. Do not run `verify-<app>` again.

For each judgement call, write the finding, your judgment, and your recommendation in that PR.

Call the Skill tool with "pr" for the delivery PR body. Include the verification, limitations, owner decisions, and those judgement calls. Save it and create the PR:

```text
gh pr create --base <project-branch> --head <night-branch> --title TITLE --body-file FILE
```

After that PR exists, report each judgement call in the conversation with the owner: the finding, your judgment, and your recommendation. Then call the Skill tool with "retro". Its commits land on the night branch, which this PR already tracks.

After the owner accepts and authorizes this delivery, merge that PR and confirm the project branch contains it. Acceptance leaves unfinished tickets unfinished. Merging the project branch into `dev` for testing, and `dev` into `main` for deployment, are separately authorized.

Done when the owner has the delivered result and its real limits.
