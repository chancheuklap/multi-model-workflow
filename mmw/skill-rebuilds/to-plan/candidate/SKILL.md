---
name: mmw-to-plan
description: Write plans for a published spec's tracer-bullet tickets. Use after tickets are published; return here when `/mmw-implement` closes tickets and unlabeled work remains.
---

# To Plan

Turn the tickets you can plan now into plans a zero-context `worker` can execute. You do not write the plans. Dispatch one `planner` per ticket.

The caller passes `<spec issue number>`. Stop if it is missing.

Plan a ticket when the facts the plan needs — contract shape, field names, exact values — are already in the spec (`## Contract Boundaries`, `## Implementation Decisions`) or the ticket's acceptance criteria. Defer tickets that can only be planned after upstream code exists. Blocking edges decide who implements first, not who gets a plan first.

This round is the open tickets that have no `ready-for-agent` and that you can plan now. If the round is empty and open tickets remain, they are waiting on upstream code — report that and stop.

Before any write:

[[mmw-require-task-branch]]

## 1. Read

`mmw artifact path spec` prints the spec path; read that file. Stop if the spec issue does not have `ready-for-agent`. `mmw issue children <spec issue number>` lists the tickets. Stop if there are none — run `/mmw-to-tickets` first.

## 2. Dispatch

For each ticket this round, run the command in its `## Plan` section. That path is the only file the `planner` writes.

Task fields:

- **Goal:** write the plan for ticket `#N` at that path
- **Read:** spec path, the ticket, and its artifact refs (`none` when there are none)
- **Constraints:** that plan file only; no commit; no source edits
- **Acceptance:** the file exists; `## Acceptance` covers every criterion on ticket `#N`

Same message, one `planner` per ticket, current task worktree:

[[mmw-launch:planner:current]]

If a `planner` cannot write the plan, give the user the reason. Do not edit approved acceptance, spec decisions, or blocking edges unless the user says so.

## 3. Review

When every `planner` in this round has written its file, send ② plan review (`/mmw-review`). Handle findings as `/mmw-review` specifies. The objects are those plan paths (run each ticket's plan-path command), the spec path, and the ticket numbers.

## 4. Label

After ② passes, commit the plan files. For each ticket in this round:

```bash
gh issue edit <ticket number> --add-label ready-for-agent
```

Ask: start implementation, or stop here.
