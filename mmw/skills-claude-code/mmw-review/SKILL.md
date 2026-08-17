---
name: mmw-review
description: Run one MMW review gate and dispose findings. Use when shared understanding, a spec, a round of plans, or final code reaches a review gate, or the user asks to review those, a branch, a PR, or uncommitted work.
---

# Review

Run one round. Review method lives in `/mmw-reviewer`. Do not read it. Do not retell it.

The author of the object does not review it. Reviewers use independent context.

③ per-ticket check and ④ contract gate are gone. Do not start them.

| Gate | When | Perspectives | Gate? |
| --- | --- | --- | --- |
| ⓪ Shared understanding | User asks after `/mmw-grilling` confirms | Shared understanding | No. Show findings with your marks. |
| ① Spec | Spec is written, before the user approves publish | Spec content, Spec alignment | No. Show findings with your marks. |
| ② Plan | This round's plans are written | Plan coverage, Plan compliance | Yes |
| ⑤ Final | Every ticket is closed | Final trace, Final fresh, Final standards | Yes |

Merged integration results also use ⑤.

Before any write:

先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


## 1. Pin the object

If ⑤ touches UI, run `/mmw-ui-qa` tagged `this-task` first, then pin HEAD. It is not a seventh gate.

| Gate | Object |
| --- | --- |
| ⓪ | `mmw artifact path scratch --sub understanding.md` (add `--issue` on a wayfinder decision ticket). Stop if the file is missing — `/mmw-grilling` writes it. |
| ① | `mmw artifact path spec` |
| ② | Each plan path from this round (run the ticket `## Plan` commands). One round, not one review per plan. |
| ⑤ | `git diff <fixed-point>...HEAD`. The fixed point is usually `git merge-base HEAD <parent-branch>`. Ask if the user called you and gave none. |

⑤: the diff must resolve and must not be empty. Record `git rev-parse HEAD` as Reviewed HEAD.

Give each perspective what it needs to judge. **Final fresh** gets only the diff. Read artifact refs as `/mmw-wayfinder` specifies for Required materials; `none` means skip.

## 2. Dispatch

`mmw artifact path review --sub <gate>.md` prints this round's record (`understanding`, `spec`, `plan`, or `final`). One file per gate.

Task fields. Goal's first sentence is the perspective name, copied exactly:

- **Goal:** `<perspective name>`. Review `<object>`.
- **Read:** the paths that perspective needs
- **Constraints:** read-only; leave the object as it is
- **Acceptance:** findings, or why the review cannot run

当前宿主使用两个审查角色。⓪ 启动一个 `reviewer-gpt`：共同理解是主 agent 自己问出来的，审查者必须换一个模型。启动：后台执行 `mmw dispatch reviewer-gpt`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。① 每个视角启动一个 `reviewer-gpt`。启动：后台执行 `mmw dispatch reviewer-gpt`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。② 每个视角启动一个 `reviewer-claude`。启动：后台执行 `mmw dispatch reviewer-claude`。把四栏 task 正文作为命令的标准输入。当前 task 属于 decision ticket 时，加 `--issue <当前 decision ticket 编号>`。命令返回 `mode: host-tool` 时，使用输出中的 `params` 调用对应宿主工具。⑤ 每个视角分别启动一个 `reviewer-gpt` 和一个 `reviewer-claude`。同一视角的两份 findings 并排比较后按 `/mmw-review` 处置。每个审查者只收到自己的四栏 task。

If a reviewer cannot run: missing materials you failed to pass — fill them and resume that perspective; missing from the artifact itself — that is a finding. If they say the problem to solve is the wrong problem, give the user their words.

## 3. Record and mark

Paste each report into the record under its perspective name. Do not rewrite. Put the fixed point and Reviewed HEAD at the top.

On ⑤, if HEAD moved since you pinned it, this round is void. Report both HEADs. Do not restart on your own.

For each finding, ask: who is hurt, in what scene? Is it worth this round, or later? Then mark one of: `accepted`, `rejected`, `duplicate`, `needs-evidence`, `waived`. Only `accepted` drives a fix. Same issue from two reviewers: one mark. `waived` or a `needs-triage` issue does not stop the rest.

Show findings with marks, by perspective. Then fix.

## 4. Fix

`accepted` items go back to whoever produced the object, in one batch. Do not send reviewers at the fix.

- Spec and shared-understanding record: you edit them. ⓪ accepted items reopen grilling branches; rewrite the record; do not review the rewrite.
- Plans: resume the `planner` who owns the file; new `planner` if the handle is dead.
- Code: resume the `worker` when every accepted item is on one ticket (merge the task branch into that result branch first). Otherwise one repair ticket and a new `worker`.

A one-line copy, number, or assertion: you may land it.

After the fix, register Repair commit as HEAD. On ⑤ that value is also Final commit. If any accepted item is still open, stop.

No `accepted` items: return to the caller. If the user invoked you, report counts and wait.
