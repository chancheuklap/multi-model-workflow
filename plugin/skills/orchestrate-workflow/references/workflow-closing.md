# Closing

> **流程位置**：`orchestrate-workflow` Steps 21-24 · 所有 Route 的终点

Architecture-draft 结论 11：提交、推送、开 PR 是兜底动作，应自动执行。

## Step 21：Final Verification

```bash
<project test command>
git status --short
```

如果有 uncommitted changes（Bug route 的 analyst/worker fix）：
```bash
git add <fixed files + test files>
git commit -m "Fix: <bug title — root cause and fix summary>"
```

Formal Orchestrate 的 pack commits 已在 execution 完成。此处只处理 Final Review repair commit（如有）。

## Step 22：Push + Open PR

临时文件由 `cleanup-before-push.sh` PreToolUse hook 自动清理——`git push` 或 `gh pr create` 执行前，hook 删除 `.claude/multi-model-workflow/` 下的 active-run-id、budget、scope 文件。

```bash
git push -u origin <branch>
gh pr list --head <branch> --json number --jq '.[0].number'
```

| 状态 | 动作 |
| --- | --- |
| PR 不存在 | `gh pr create` |
| PR 已存在 | `gh pr edit <number>` 更新 body |
| 无 remote 配置 | 提示用户配置 |

PR body：

```markdown
## Summary
- <1-3 bullets>
- Route: Formal Orchestrate / Bug Fix / Multi-PR Merge

## Artifacts
- Design / Plan / Issues created

## Test plan
- <verification commands and results>

## Review history
- Reviews dispatched / Findings / Repair rounds

🤖 Generated with [Claude Code](https://claude.com/claude-code) + multi-model-workflow
```

### Step 22a：生成运行总结

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/run-summary.sh" "<run_id>"
```

输出写入 `.claude/multi-model-workflow/run-summary-<run_id>.json`。用于后续 workflow 的 effort budget 校准。

## Step 22b：退出工作树

Push + PR 完成后，退出工作树并清理 breadcrumb：

1. `ExitWorktree({ action: "keep" })` — 保留工作树（PR 可能需要后续修改）
2. 清理 breadcrumb：
   ```bash
   rm -f .claude/multi-model-workflow/active-worktree
   rmdir .claude/multi-model-workflow 2>/dev/null
   ```

工作树保留直到 PR 合并后由 `clean_gone` 统一清理（删除工作树 + 分支 + 残留状态文件）。

## Step 23：Report to User

一到两句话汇报。不做长篇总结。

---
> **流程到此结束**。orchestrate-workflow 返回 verdict，不再读取其他 reference。
