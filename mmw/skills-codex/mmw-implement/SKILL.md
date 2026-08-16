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

- Open tickets with no `ready-for-agent`: `$mmw:mmw-to-plan`, then return here.
- Else run `mmw issue frontier <spec issue number> --label ready-for-agent`. Claim every line (`mmw issue claim`). Dispatch one `worker` per claimed ticket.
- No open tickets: ⑤ below.

Commit the task branch first. Name a result branch. Record `git rev-parse HEAD` as the base. Both go in the task.

Task fields:

- **Goal:** complete ticket `#N`; return the result-branch HEAD SHA
- **Read:** this skill's `worker-brief.md`, spec, ticket, plan path (run the ticket's `## Plan` command), `TESTING.md` when it exists, and the plan's artifact refs
- **Constraints:** source and tests in this worktree; leave `docs/` as they are; stay inside the ticket
- **Acceptance:** the ticket's criteria; HEAD SHA on the result branch

启动：用 `list_projects` 取得当前仓库的 projectId，并调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-terra`，思考档使用 `xhigh`。任务提示包含四栏 task、完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 完成工作并提交，并在工作前完整读取 `$mmw:mmw-tdd`。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告。报告交回后不重做整个 task。

Billing, permissions, data migration, or irreversible mistakes: use

启动：用 `list_projects` 取得当前仓库的 projectId，并调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-sol`，思考档使用 `medium`。任务提示包含四栏 task、完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 完成工作并提交，并在工作前完整读取 `$mmw:mmw-tdd`。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告。报告交回后不重做整个 task。

instead. You choose the upgrade.

Integrate one result at a time: `mmw result integrate <result-branch> <HEAD SHA> <base SHA>`. Conflicts: `$mmw:mmw-integrate`. Then `gh issue close <ticket number>` and `mmw worktree remove <result-branch>`. Host-created trees: the host removes them.

**Done** or **Done with concerns**: integrate, then close. Give concerns to the user. Any other outcome: stop and give the user what the `worker` said.

After the claimed tickets are closed, run children again and follow the loop.

## Final

When children has no open tickets, send ⑤ final review (`$mmw:mmw-review`). The fixed point is `git merge-base HEAD <parent-branch>` — the branch this task was created from, or the map branch when this task came from `$mmw:mmw-wayfinder`. Handle findings as `$mmw:mmw-review` specifies.

Accepted findings on one ticket: merge the task branch into that result branch (`git merge --no-ff`), then

这个宿主没有续跑通道：按对应的启动动作重派新实例，task 正文带上原 task 全文、原报告全文和本轮修复指令。

Conflict, missing worktree, or dead handle: one new repair ticket and a new `worker`. Findings that span tickets: the same. After repair, register the commits as `$mmw:mmw-review` specifies.

Ask: release, or stop here.
