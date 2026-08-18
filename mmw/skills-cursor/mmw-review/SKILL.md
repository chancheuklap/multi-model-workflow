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

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>` with the task-branch name decided above |
| Task branch already there | None of the above holds | Use the current branch |


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

This host uses two reviewer roles. ⓪ launches one `reviewer-gpt`: the shared understanding is what the main agent interviewed out itself, so the reviewer must be a different model.Launch: call the native Task tool with agent `mmw-reviewer-gpt` and the four-field task table in full as prompt. Instances that do not depend on each other launch in the same message.① launches one `reviewer-gpt` per perspective.Launch: call the native Task tool with agent `mmw-reviewer-gpt` and the four-field task table in full as prompt. Instances that do not depend on each other launch in the same message.② launches one `reviewer-claude` per perspective.Launch: call the native Task tool with agent `mmw-reviewer-claude` and the four-field task table in full as prompt. Instances that do not depend on each other launch in the same message.⑤ launches one `reviewer-gpt` and one `reviewer-claude` per perspective. Compare the two sets of findings for the same perspective side by side, then dispose as `/mmw-review` specifies. Each reviewer receives only its own four-field task.

If a reviewer cannot run: missing materials you failed to pass — fill them and resume that perspective; missing from the artifact itself — that is a finding. If they say the problem to solve is the wrong problem, give the user their words.

## 3. Record and mark

Paste each report into the record under its perspective name. Do not rewrite. Head the record with these labels, one per line, spelled exactly — `/mmw-release` reads them back:

```
Fixed point: <the fixed point>
Reviewed HEAD: <git rev-parse HEAD>
```

On ⑤, if HEAD moved since you pinned it, this round is void. Report both HEADs. Do not restart on your own.

For each finding, ask: who is hurt, in what scene? Is it worth this round, or later? Then mark one of: `accepted`, `rejected`, `duplicate`, `needs-evidence`, `waived`. Only `accepted` drives a fix. Same issue from two reviewers: one mark. `waived` or a `needs-triage` issue does not stop the rest.

Show findings with marks, by perspective. Then fix.

## 4. Fix

`accepted` items go back to whoever produced the object, in one batch. Do not send reviewers at the fix.

- Spec and shared-understanding record: you edit them. ⓪ accepted items reopen grilling branches; rewrite the record; do not review the rewrite.
- Plans: resume the `planner` who owns the file; new `planner` if the handle is dead.
- Code: resume the `worker` when every accepted item is on one ticket (merge the task branch into that result branch first). Otherwise one repair ticket and a new `worker`.

A one-line copy, number, or assertion: you may land it.

After the fix, add `Repair commit: <git rev-parse HEAD>` to the record head. On ⑤ add `Final commit: <that same value>`. Same spelling; `/mmw-release` checks both. If any accepted item is still open, stop.

No `accepted` items: return to the caller. If the user invoked you, report counts and wait.
