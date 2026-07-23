## 收尾：合并 App branch，保留 App worktree

回执 `done`（`STATUS=ready-to-close`）后，先找到 `target_branch` 已有的 clean checkout。
它不存在、dirty 或正在 merge/rebase 时停止并说明缺口，不再创建 closing worktree。

在 target checkout 本地执行：

```bash
git merge --no-ff <codex/任务-branch>
```

禁止 `--squash`。本地 merge 完成并通过最终验证后，在 target checkout 运行：

```bash
mmw task cleanup --slug <slug>
```

cleanup 只删除任务 App worktree 内的 `.codex/multi-model-workflow/` 状态。App
worktree 和 App branch 都保留，由用户继续在 Codex App 中查看、handoff、archive
或管理 branch。`git push`、远端 PR merge 和部署仍须用户批准。
