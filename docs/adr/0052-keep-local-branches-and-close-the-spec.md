---
date: 2026-10-15
amends: [0023, 0025]
---

# 落地和 `finish` 只删 origin 上的票分支与 base branch，本机副本留档并指向落地时的提交；`finish` 成功时关闭 spec

主人第二天要从本机找到某张票或某一夜的提交（2026-10-15：「那我不需要你删夜分支和任务分支，但是要把它们拉回本地，这样我才能方便找到他们，同时关掉 spec 就行了」，#1063）。落地清理在删除 `origin/issue-<n>` 之前，把本机 `issue-<n>` 放到取回的 origin 末端：缺失就在那里建出，落后就快进；`finish` 在删除 `origin/<base branch>` 之前对本机 base branch 做同样的事。两处都不再删除本机副本。`finish` 每条成功路径都在清理完成后以 completed 关闭 spec；spec 关不上或清理没做完时退出 2，重跑补齐。

## 边界

- 0023 的 origin 权威不变：落地仍合并 `ticket.passed.commit`，在合并结果上检查，fast-forward 推送，删除 origin 副本仍以取回时的末端作租约，保护别人后来推上去的提交。本机副本只是留档，从不作为合并目标。
- 本机副本带着 origin 不含的提交，或者被某个工作区签出时，原样保留，stderr 说明原因；签出 base branch 的工作区仍由主人在 session 结束后自行移走（0025）。
- 一张落地后又被重开的票再开工时，本机 `issue-<n>` 已全部包含在 `origin/<base branch>` 里，先移到 `origin/<base branch>` 的末端再建工作区，起点与本机副本已删除时相同。

## Considered Options

- **照旧删除本机副本，要找时从 `ticket.landed` 的 `commit` 手工重建。** 否决。2026-10-15 夜里正是这样重建了 night-1025 和 issue-1026 至 issue-1031，主人明确不要这一步。
- **连 origin 副本也保留。** 否决。origin 上的分支是集成状态，落地后留着只会让远端堆满已合并的分支；本机留档已经满足「找得到」。
- **spec 由主人或总指挥手工关闭。** 否决。`spec.merged` 已经证明这一夜合回 project branch，关闭是它的机械后果；手工关闭在 2026-10-15 前留下了五个已合并却开着的 spec。

## Consequences

- 每张落地票和每一夜在本机都有同名分支，指向落地时的提交；origin 只剩未落地的分支。
- 0023「workspace 归档后，本机与 origin 的 `issue-<n>` 在保护条件满足时删除」中关于本机的部分不再成立。0025「本地 base branch 只在没有 worktree 签出它时删除」和 stderr 给出删除本地 base branch 的命令不再成立。
- `finish` 的清理失败不再是警告：退出 2、spec 保持打开，直到重跑把清理和关闭做完。
