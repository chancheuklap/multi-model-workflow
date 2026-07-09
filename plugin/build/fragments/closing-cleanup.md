## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并是红线:回主仓库直接跑 `git merge --no-ff <branch>`(禁 `--squash`)——`guard-redline` 对"合并进主分支"弹权限框,**用户在框里亲批**(无令牌可代批,不分在场/无人值守)。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug> # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + 宿主状态平面(`.claude/` 或 `.factory/`,见 host-contract)临时状态一并清除。
