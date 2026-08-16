---
name: mmw-implement
description: Dispatch a worker per ready-for-agent ticket. Use when plans have passed review, or for a single ready-for-agent agent brief.
---

# Implement

You do not write the code. One `worker` per ticket, each on its own result worktree.

The caller passes `<spec issue number>` for spec work.

**No spec.** If `mmw artifact path spec` does not point at a spec file, the work is one `ready-for-agent` agent brief on the issue you were given. Skip the loop: no frontier, no plan, one `worker`, integrate, then ⑤. Task Read is this skill's `worker-brief.md`, the issue, and `TESTING.md` when it exists.

Before dispatch:

先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


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

启动：先运行 `mmw worktree add <结果分支>`，使用命令返回的 worktree 绝对路径。后台执行 `mmw dispatch worker --cwd <结果 worktree 绝对路径>`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。

Billing, permissions, data migration, or irreversible mistakes: use

启动：先运行 `mmw worktree add <结果分支>`，使用命令返回的 worktree 绝对路径。后台执行 `mmw dispatch worker-high-risk --cwd <结果 worktree 绝对路径>`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。

instead. You choose the upgrade.

Integrate one result at a time: `mmw result integrate <result-branch> <HEAD SHA> <base SHA>`. Conflicts: `/mmw-integrate`. Then `gh issue close <ticket number>` and `mmw worktree remove <result-branch>`. Host-created trees: the host removes them.

**Done** or **Done with concerns**: integrate, then close. Give concerns to the user. Any other outcome: stop and give the user what the `worker` said.

After the claimed tickets are closed, run children again and follow the loop.

## Final

When children has no open tickets, send ⑤ final review (`/mmw-review`). The fixed point is `git merge-base HEAD <parent-branch>` — the branch this task was created from, or the map branch when this task came from `/mmw-wayfinder`. Handle findings as `/mmw-review` specifies.

Accepted findings on one ticket: merge the task branch into that result branch (`git merge --no-ff`), then

恢复：后台执行 `mmw dispatch worker --resume <句柄原文> --cwd <原结果 worktree 绝对路径>`。把修复 task 正文作为命令的标准输入。句柄是原派发输出里的 `session:` 或 `handle:` 行原文。那一行不在手上时，运行 `mmw artifact path scratch --sub dispatch` 取得派发进度目录，读其中以 `worker-` 开头的那个 `.session` 文件。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。句柄取不到或命令失败时退回重派：按对应的启动动作重派新实例，task 正文带上原 task 全文、原报告全文和本轮修复指令。

Conflict, missing worktree, or dead handle: one new repair ticket and a new `worker`. Findings that span tickets: the same. After repair, register the commits as `/mmw-review` specifies.

Ask: release, or stop here.
