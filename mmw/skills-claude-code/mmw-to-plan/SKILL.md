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

先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


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

启动：后台执行 `mmw dispatch planner --cwd <当前工作树绝对路径>`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。

If a `planner` cannot write the plan, give the user the reason. Do not edit approved acceptance, spec decisions, or blocking edges unless the user says so.

## 3. Review

When every `planner` in this round has written its file, send ② plan review (`/mmw-review`). Handle findings as `/mmw-review` specifies. The objects are those plan paths (run each ticket's plan-path command), the spec path, and the ticket numbers.

## 4. Label

After ② passes, commit the plan files. For each ticket in this round:

```bash
gh issue edit <ticket number> --add-label ready-for-agent
```

Ask: start implementation, or stop here.
