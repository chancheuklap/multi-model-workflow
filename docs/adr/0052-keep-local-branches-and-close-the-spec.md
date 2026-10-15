---
date: 2026-10-15
amends: [0025]
---

# `finish` 后本机留着夜分支和任务分支，指向合并时的提交；`finish` 成功时关闭 spec

主人要从本机找到一夜的分支和它合进的任务分支（2026-10-15：「那我不需要你删夜分支和任务分支，但是要把它们拉回本地，这样我才能方便找到他们，同时关掉 spec 就行了」；同日更正：「我从来没要求过保留票分支，我要求保留的是开夜分支和它上级的任务分支」，#1073）。夜分支是 base branch，任务分支是 project branch。`finish` 在删除 `origin/<base branch>` 之前，把本机 base branch 放到取回的 origin 末端：缺失就在那里建出，落后就快进，不再删除本机副本。`finish` 把夜合进 `origin/<project branch>` 之后，把本机 project branch 放到同一个末端：缺失就建出，落后就快进。`finish` 每条成功路径都在清理完成后以 completed 关闭 spec；spec 关不上或清理没做完时退出 2，重跑补齐。票分支 `issue-<n>` 照 0023 处理：落地后本机与 origin 的副本在保护条件满足时都删除。

## 边界

- 0023 的 origin 权威不变：`finish` 在合并结果上检查，fast-forward 推送 `origin/<project branch>`，删除 `origin/<base branch>` 仍以取回时的末端作租约。本机副本只是留档，从不作为合并目标。
- 本机 base branch 或 project branch 带着 origin 不含的提交时，原样保留，stderr 说明原因。
- 被某个工作区签出的本机 base branch，工作区和分支都不动，由主人在 session 结束后自行移走工作区（0025）。被某个工作区签出的本机 project branch，那个工作区没有未提交的改动时在工作区里快进；有未提交的改动时原样保留，stderr 说明原因。

## Considered Options

- **照旧删除本机夜分支、不碰本机任务分支，要找时手工重建或拉取。** 否决。2026-10-15 夜里正是这样手工重建了 night-1025，主人明确不要这一步。
- **连票分支也在本机留档。** 否决。主人没有要求，一夜留下十几个票分支只会让本机堆满；票的提交在任务分支的合并历史里找得到。
- **连 origin 上的夜分支也保留。** 否决。origin 上的分支是集成状态，合并后留着只会让远端堆满已合并的分支；本机留档已经满足「找得到」。
- **spec 由主人或总指挥手工关闭。** 否决。`spec.merged` 已经证明这一夜合回 project branch，关闭是它的机械后果；手工关闭在 2026-10-15 前留下了五个已合并却开着的 spec。

## Consequences

- 每一夜在本机都有它的夜分支和任务分支，分别指向夜分支最后的提交和合并后的任务分支；origin 只剩未合并的分支。
- 0025「本地 base branch 只在没有 worktree 签出它时删除」和 stderr 给出删除本地 base branch 的命令不再成立。
- `finish` 的清理失败不再是警告：退出 2、spec 保持打开，直到重跑把清理和关闭做完。
