# 任务隔离

正式任务在独立 git worktree 里做。主线程和 Codex 工人不在同一棵树上，工人正在改的文件不会在主线程读它时变形。

## 粒度

默认**一份设计一个 worktree**：设计拆出的几张子 issue 全在里面按顺序做完，整体合并一次、终审一次、Wiki 写一次。设计是原子交付单元。

确实能并行的切片才另开子 worktree：从当前 worktree 的 HEAD 分叉（因此继承已完成的进度），扁平挂在 `.worktrees/` 下，不做目录嵌套。合并顺序自己理清。

## 命名

`<父 issue 编号>-<主题 kebab>`，例如 `42-phone-login`。worktree 目录名和分支名相同。

编号让 GitHub 自动把分支、PR 和 issue 串起来，你在编辑器里也能一眼看出这个 worktree 在做哪张 issue。所以**先建父 issue 拿编号，再建 worktree**。

## 落点与建法

仓库内 `.worktrees/`，已进 `.gitignore`。

```bash
git worktree add -b <name> .worktrees/<name> <base>
```

然后 `EnterWorktree({ path: ".worktrees/<name>" })` 进去——只有这一步能切会话工作目录，脚本切不了。

**会话限制**：`EnterWorktree` 从主仓库按路径进没问题；但同一个会话里从一个 worktree 直接跳到另一个 worktree 时，它只认 `.claude/worktrees/` 下的目标。我们是一个任务一个会话，正常撞不上；真要跳先回主仓库。

## 清理

worktree 在使用期持久，可以跨天，中途别删。

合并进主线后向用户报一句、等他点头，再删 worktree、删分支、清掉里面的临时文件。删目录不可逆，而且里面可能还有没提交的东西，所以不自动清。
