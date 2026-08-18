---
name: mmw-implement
description: Dispatch a worker per ready-for-agent ticket. Use when plans have passed review, or for a single ready-for-agent agent brief.
---

# Implement

You do not write the code. One `worker` per ticket, each on its own result worktree.

The caller passes `<spec issue number>` for spec work.

**No spec.** If `mmw artifact path spec` does not point at a spec file, the work is one `ready-for-agent` agent brief on the issue you were given. Skip the loop: no frontier, no plan, one `worker`, integrate, then ⑤. Task Read is this skill's `worker-brief.md`, the issue, and `TESTING.md` when it exists.

Before dispatch:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>` with the task-branch name decided above |
| Task branch already there | None of the above holds | Use the current branch |


## Loop

`mmw issue children <spec issue number>`.

- Open tickets with no `ready-for-agent`: `/mmw-to-plan`, then return here.
- Else run `mmw issue frontier <spec issue number> --label ready-for-agent`. Claim every line (`mmw issue claim`). Dispatch one `worker` per claimed ticket.
- No open tickets: ⑤ below.

Commit the task branch first. Name a result branch. Record `git rev-parse HEAD` as the base. Both go in the task.

Task fields:

- **Goal:** complete ticket `#N`; return the result-branch HEAD SHA
- **Read:** this skill's `worker-brief.md`, spec, ticket, plan path (run the ticket's `## Plan` command), `TESTING.md` when it exists, and the plan's artifact refs
- **Constraints:** source and tests in this worktree; leave `docs/` as they are; stay inside the ticket
- **Acceptance:** the ticket's criteria; HEAD SHA on the result branch

Launch: in the background, run `mmw-cursor-agent --mmw-role worker -p --force --trust --approve-mcps --worktree <result branch> --worktree-base <current task branch>`. Pass the four-field task body as the command's standard input. The worker enters the result tree, completes the work, and commits. It returns the result-branch name, the HEAD SHA, and the base SHA.

Billing, permissions, data migration, or irreversible mistakes: use

Launch: in the background, run `mmw-cursor-agent --mmw-role worker-high-risk -p --force --trust --approve-mcps --worktree <result branch> --worktree-base <current task branch>`. Pass the four-field task body as the command's standard input. The worker enters the result tree, completes the work, and commits. It returns the result-branch name, the HEAD SHA, and the base SHA.

instead. You choose the upgrade.

Integrate one result at a time: `mmw result integrate <result-branch> <HEAD SHA> <base SHA>`. Conflicts: `/mmw-integrate`. Then `gh issue close <ticket number>`. If this result tree was created with `mmw worktree add`, run `mmw worktree remove <result-branch>`. Otherwise the host removes it.

**Done** or **Done with concerns**: integrate, then close. Give concerns to the user. Any other outcome: stop and give the user what the `worker` said.

After the claimed tickets are closed, run children again and follow the loop.

## Final

When children has no open tickets, send ⑤ final review (`/mmw-review`). The fixed point is `git merge-base HEAD <parent-branch>` — the branch this task was created from, or the map branch when this task came from `/mmw-wayfinder`. Handle findings as `/mmw-review` specifies.

Accepted findings on one ticket: merge the task branch into that result branch (`git merge --no-ff`), then

Resume: in the background, run `mmw-cursor-agent --resume <handle text>`. Pass the repair task body as the command's standard input. The handle is the session id from the original dispatch output. If the handle cannot be found or the command fails, re-dispatch a new instance with the matching launch action, and let the task body carry the original task in full, the original report in full, and this round's repair instruction.

Conflict, missing worktree, or dead handle: one new repair ticket and a new `worker`. Findings that span tickets: the same. After repair, register the commits as `/mmw-review` specifies.

Ask: release, or stop here.
