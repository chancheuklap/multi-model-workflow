---
name: mmw-to-plan
description: Write plans for a published spec's tracer-bullet tickets. Use after tickets are published; return here when `$mmw:mmw-implement` closes tickets and unlabeled work remains.
---

# To Plan

Turn the tickets you can plan now into plans a zero-context `worker` can execute. You do not write the plans. Dispatch one `planner` per ticket.

The caller passes `<spec issue number>`. Stop if it is missing.

Plan a ticket when the facts the plan needs — contract shape, field names, exact values — are already in the spec (`## Contract Boundaries`, `## Implementation Decisions`) or the ticket's acceptance criteria. Defer tickets that can only be planned after upstream code exists. Blocking edges decide who implements first, not who gets a plan first.

This round is the open tickets that have no `ready-for-agent` and that you can plan now. If the round is empty and open tickets remain, they are waiting on upstream code — report that and stop.

Before any write:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>`. Use the name this skill or the caller already gave; with none in hand, name it after the work in this repo's own branch-naming shape, and say which name you took |
| Task branch already there | None of the above holds | Use the current branch |

## 1. Read

`mmw artifact path spec` prints the spec path; read that file. Stop if the spec issue does not have `ready-for-agent`. `mmw issue children <spec issue number>` lists the tickets. Stop if there are none — run `$mmw:mmw-to-tickets` first.

## 2. Dispatch

For each ticket this round, run the command in its `## Plan` section. That path is the only file the `planner` writes.

Task fields:

- **Goal:** write the plan for ticket `#N` at that path
- **Read:** spec path, the ticket, and its artifact refs (`none` when there are none)
- **Constraints:** that plan file only; no commit; no source edits
- **Acceptance:** the file exists; `## Acceptance` covers every criterion on ticket `#N`

Same message, one `planner` per ticket, current task worktree:

Run `mmw launch planner --scope current` and follow the action it prints.

If a `planner` cannot write the plan, give the user the reason. Do not edit approved acceptance, spec decisions, or blocking edges unless the user says so.

## 3. Review

When every `planner` in this round has written its file, send ② plan review (`$mmw:mmw-review`). Handle findings as `$mmw:mmw-review` specifies. The objects are those plan paths (run each ticket's plan-path command), the spec path, and the ticket numbers.

## 4. Label

After ② passes, commit the plan files. For each ticket in this round:

```bash
gh issue edit <ticket number> --add-label ready-for-agent
```

Ask: start implementation, or stop here.
