---
date: 2026-08-15
amends: [5]
---

# 名字段复用这次交付的任务分支 slug

ADR 0005 把工作名和任务分支名做成两个值，并把工作名写进 git worktree 配置。一项 Wayfinder effort 有多条任务分支，用各条 ticket 分支名当产物目录会把同一项 effort 的 research、prototype 和 spec 散开。这个理由仍成立。不成立的是「所以必须另存一个工作名」。

现在名字段取这次交付的任务分支去掉最后一个 `/` 之后的部分。普通任务就是当前任务分支的 slug。Wayfinder 整项工作用 map 那条分支的 slug；decision ticket 自己的分支只承载那次会话的 git 改动，写产物时传 `--name <map 分支 slug>`。任务工作树由用户用宿主创建。agent 不建任务树，不往 git 配置写 `mmw.task.*`，也不为空提交记用户原话。

## Considered Options

**继续把工作名存在 git worktree 配置里**（否决）。它强制每棵树走 `mmw task bind` / `mmw task new`。Cursor、Codex、Grok 已经自己建树，这套认领手续是第二份事实来源，而且会把宿主给目录起的临时名当成任务身份。

**用每条当前分支的 slug 当名字段，Wayfinder ticket 也不例外**（否决）。这就是 ADR 0005 否决过的散开问题：同一项 effort 的产物会落到多个目录。

**名字段等于这次交付的那一条任务分支 slug**（采纳）。一次交付仍只有一个名字段。Wayfinder 的那一条是 map 分支。ticket 分支不进入产物路径。

## Consequences

- `mmw artifact path` / `list` 未给 `--name` 时，从 `git symbolic-ref --short HEAD` 取最后一个 `/` 之后作为名字段。当前在主检出里，或没有分支，则非零退出。
- 删除 `mmw task` 的 state / name / bind / new / cleanup。Pi 与 Claude Code 的工人树改用 `mmw worktree add` / `remove`，不写 git 配置。
- map 正文不再有 `## 工作名`。后来的会话从 `## 分支` 计算名字段。
- 历史 `docs/specs/<旧工作名>/` 不搬家。新任务走新规则。
