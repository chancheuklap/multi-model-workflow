---
date: 2026-10-19
amends: []
---

# 每个 effort 从开始起就有自己的 effort branch，原型和所有 brief 会话写出的文件都提交在它上面，只经主人接受的 PR 进 project branch

主人 2026-10-19 先定「所有 research 和 prototype 的产出都提交到主会话所在的分支」（#1162），随后要求「重新评估 mmw 里所有会往仓库写入的路径，系统性规划」。主会话常坐在 project branch 上，照字面执行，产出仍会直接进 project branch：agentflow 地图 #1290 的研究笔记和 #1295 的原型就这样进了 dev，主工作树还被一个 researcher 切到 `fix-1334`（#1161、#1164）。effort 定义为朝同一个 destination 的一整份开发工作：一张 wayfinder 地图连同它引出的研究、原型、spec 和夜，或一张不属于任何地图、开了 `fix-<n>` 的票。地图在开图时从 project branch 切出 effort branch 和它的 worktree，开夜时它就是 night's branch；一张单独的票，effort branch 就是 `fix-<n>`。主会话在 effort branch 的 worktree 里工作；它派出的 brief 会话在同一个 worktree 里写自己那一份文件，不跑任何 git 写命令，由主会话把它们的产出提交在 effort branch 上（#1169）。研究答案和非界面原型的结论不是仓库文件，记在票的评论里（0056），不经过这条分支。

## 边界

- 不属于任何 effort 的工作（一次单独的 Investigation、一次 code review）不提交；它派出的 brief 会话的答案只留在 state 目录。
- 一次 Investigation 中途主人说要改，从那一刻起它成为一个 effort，照所属 playbook 开票和 `fix-<n>`。
- 界面原型在 effort branch 上做（0055）不变；这份把同一条规矩推广到 effort 的全部产出，并让地图从开图起就有这条分支，而不是等原型阶段或开夜。

## Considered Options

- **照字面：产出进主会话当时所在的分支。** 否决。主会话在 project branch 上时，没经过主人的提交照样进 project branch，正是 #1162 要消掉的情形。
- **每个 brief 会话各开一个 worktree，交回时并入 effort branch。** 否决。界面原型的 candidate 把各自方向写进同一个 worktree 的 `candidates/<n>/`，没有后端的产品还共用主会话起的那一个运行实例（`mmw-v4/skills/prototype/UI.md` `### 2.`），分开的 worktree 会让这个实例看不到它们的文件。
- **研究进 base branch、原型进 night's branch（`wayfinder.md` 与 `owning-a-task.md` 原来的两句）。** 否决。两句互相矛盾，地图开夜前 night's branch 还不存在，会话只能自己猜，结果一次进了 dev、一次散在三条 `proto-<n>` 分支上。

## Consequences

- project branch 和主人的主工作树不再收到任何没经过主人 PR 的提交。
- 一个 effort 的原型和测试都在同一个 PR 里看。
- 每张地图多一个 worktree；一张地图的原型在它的 PR 合并之前，别的地图读不到。
