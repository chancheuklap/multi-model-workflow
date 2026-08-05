# rebase：让未完成的结果分支跟上当前任务分支

本操作只在拥有结果分支的任务 worktree 中执行。主 agent 继续留在当前任务分支的 worktree。

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

不要沿用 merge 的直觉判断 `ours` 和 `theirs`。逐块读取双方意图，再决定保留内容。

## 继续与完成

```bash
git add <已经解决的文件>
git rebase --continue
```

重复到 `git status` 不再显示 rebase。rebase 中途不运行 `git commit`，否则 rebase 仍未完成。

全部重放后运行项目要求的检查，提交报告交回新的结果分支 HEAD SHA 和验证结果。主 agent 用新的 HEAD 重新运行 `mmw result verify`。

## 停止

rebase 进行中可运行 `git rebase --abort` 回到开始前。rebase 完成后不要用 `reset --hard` 回退；需要撤销时先由用户确认。

结果分支已经推送到远端时，更新远端需要 `--force-with-lease`。这是对外发布的人工审批关卡；批准对象是将要更新的远端分支和提交范围，批准人是用户，通过凭据是用户明确授权这次推送，通过后才允许执行 `git push --force-with-lease`。
