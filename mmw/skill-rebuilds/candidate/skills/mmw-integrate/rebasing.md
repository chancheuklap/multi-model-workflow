# rebase：让未完成的结果分支跟上当前任务分支

本操作只在拥有结果分支的任务 worktree 中执行。主 agent 继续留在当前任务分支的 worktree。

## 先看清楚现在停在哪

`git status` 说 rebase 已经在进行中时，**不要再跑「开始」那条命令**——那会另起一次 rebase。先取现状：`git status` 看停在第几条提交、哪些文件还冲突着，`git log --oneline` 看已经重放过哪些。然后直接从「识别两边」往下走。

没有进行中的 rebase 时，从下面「开始」起。

## 开始

```bash
git rebase <当前任务分支>
```

rebase 会逐个重放结果分支的提交。后续提交可能产生新的冲突，所以每次继续后都要重新检查状态。

## 识别两边

| 标记 | 内容 |
| --- | --- |
| `ours`、`<<<<<<< HEAD` | 当前任务分支已有的内容 |
| `theirs`、`>>>>>>>` | 结果分支正在重放的提交 |

不要沿用 merge 的直觉判断 `ours` 和 `theirs`。逐块读取双方的提交、issue、spec 和既定集成目标，再决定保留内容。只组合已有意图，不发明新行为。

## 继续与完成

```bash
git add <已经解决的文件>
git rebase --continue
```

重复到 `git status` 不再显示 rebase。rebase 中途不运行 `git commit`，否则 rebase 仍未完成。

全部重放后运行项目要求的检查，提交报告交回新的结果分支 HEAD SHA 和验证结果。主 agent 用新的 HEAD 重新运行 `mmw result verify`。

## 停止

`git rebase --abort` 会回到 rebase 开始前。只有用户取消本次集成，或现有目标无法决定冲突取舍时才停止；不要用停止代替冲突判断。

rebase 完成后不要用 `reset --hard` 回退；需要撤销时先由用户确认。

结果分支已经推送到远端时，更新远端需要 `--force-with-lease`。推送属于对外发布，必须先得到用户明确授权。
