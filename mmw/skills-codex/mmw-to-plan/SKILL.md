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

先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


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

启动：按名称调用 Codex 原生 subagent `mmw-planner`，task 传四栏表全文；该 subagent 使用当前工作树，不另开结果树。互不依赖的实例在同一条消息中并行启动，全部完成后再汇总。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告。报告交回后不重做整个 task。

If a `planner` cannot write the plan, give the user the reason. Do not edit approved acceptance, spec decisions, or blocking edges unless the user says so.

## 3. Review

When every `planner` in this round has written its file, send ② plan review (`$mmw:mmw-review`). Handle findings as `$mmw:mmw-review` specifies. The objects are those plan paths (run each ticket's plan-path command), the spec path, and the ticket numbers.

## 4. Label

After ② passes, commit the plan files. For each ticket in this round:

```bash
gh issue edit <ticket number> --add-label ready-for-agent
```

Ask: start implementation, or stop here.
