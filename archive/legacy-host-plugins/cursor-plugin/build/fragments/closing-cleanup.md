## 收尾 · 合并后删干净

回执 `done`(STATUS=ready-to-close)= 末阶段过。合并进主分支是自主收尾动作(本地可逆、不出站,不拦):用 Cursor **File → Open Folder** 打开主仓库(与进 worktree 对称;**没有 `exit_worktree(...)` 这个工具**),在该窗口跑 `git merge --no-ff <branch>`(禁 `--squash`),无人值守也自主推进;要发布到远端再 `git push`——那时 `guard-redline` 经 `beforeShellExecution` hook(failClosed)拦下来让用户亲批。任务分支 merge 进主线后,worktree 连同里面的临时状态一起删:

```bash
mmw task cleanup --slug <slug> # 回主仓库执行
```

worktree 在**使用期**持久(可跨天,别中途删);**合并后**才 cleanup,worktree + 分支 + `.cursor/multi-model-workflow/` 临时状态一并清除。
