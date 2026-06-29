## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并是红线:用户确认后 `mmw release-approve`(造一次性令牌)→ `git merge --no-ff <branch>`(禁 `--squash`),`guard-redline` 放行后即消费令牌。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug>   # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.claude/` 临时状态一并清除。
