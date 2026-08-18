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
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>`. Use the name this skill or the caller already gave; with none in hand, name it after the work in this repo's own branch-naming shape, and say which name you took |
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

Launch: run `mmw worktree add <result branch>` first and use the worktree absolute path it returns. In the background, run `mmw dispatch worker --cwd <result worktree absolute path>`. Pass the four-field task body as the command's standard input. Add `--issue <current decision ticket number>` when this task belongs to a decision ticket. When the command returns `mode: host-tool`, call the matching host tool with the `params` in its output.

Billing, permissions, data migration, or irreversible mistakes: use

Launch: run `mmw worktree add <result branch>` first and use the worktree absolute path it returns. In the background, run `mmw dispatch worker-high-risk --cwd <result worktree absolute path>`. Pass the four-field task body as the command's standard input. Add `--issue <current decision ticket number>` when this task belongs to a decision ticket. When the command returns `mode: host-tool`, call the matching host tool with the `params` in its output.

instead. You choose the upgrade.

Integrate one result at a time: `mmw result integrate <result-branch> <HEAD SHA> <base SHA>`. Conflicts: `/mmw-integrate`. Then `gh issue close <ticket number>`. If this result tree was created with `mmw worktree add`, run `mmw worktree remove <result-branch>`. Otherwise the host removes it.

**Done** or **Done with concerns**: integrate, then close. Give concerns to the user. Any other outcome: stop and give the user what the `worker` said.

After the claimed tickets are closed, run children again and follow the loop.

## Final

When children has no open tickets, send ⑤ final review (`/mmw-review`). The fixed point is `git merge-base HEAD <parent-branch>` — the branch this task was created from, or the map branch when this task came from `/mmw-wayfinder`. Handle findings as `/mmw-review` specifies.

Accepted findings on one ticket: merge the task branch into that result branch (`git merge --no-ff`), then

Resume: in the background, run `mmw dispatch worker --resume <handle text> --cwd <original result worktree absolute path>`. Pass the repair task body as the command's standard input. The handle is the `session:` or `handle:` line from the original dispatch output, verbatim. When that line is not in hand, run `mmw artifact path scratch --sub dispatch` for the dispatch progress directory, and read the `.session` file there that starts with `worker-`. When the command returns `mode: host-tool`, call the matching host tool with the `params` in its output. If the handle cannot be found or the command fails, re-dispatch a new instance with the matching launch action, and let the task body carry the original task in full, the original report in full, and this round's repair instruction.

Conflict, missing worktree, or dead handle: one new repair ticket and a new `worker`. Findings that span tickets: the same. After repair, register the commits as `/mmw-review` specifies.

Ask: release, or stop here.
