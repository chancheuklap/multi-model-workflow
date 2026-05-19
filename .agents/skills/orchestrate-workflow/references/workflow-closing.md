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

`PreToolUse/Bash` hook 会在 `git push` / `gh pr create` / `gh pr edit` 前自动清理本次运行的临时记录文件。清理范围只包括 `.codex/multi-model-workflow/`，不删除 design、plan、issue、report、code、test 或 commit artifacts。

```bash
git push -u origin <branch>
test ! -e .codex/multi-model-workflow
gh pr list --head <branch> --json number --jq '.[0].number'
```

如果 hooks 未启用或 publish 被 cleanup failure 拦截，运行 `bash codex/hooks/cleanup-run-state.sh --apply` 后重试 publish。

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

Generated with Codex + multi-model-workflow
```

## Step 23：Report to User

一到两句话汇报。不做长篇总结。

## Step 24：Cleanup

正常情况下 Step 22 的 PreToolUse hook 已经清理运行态。这里作为收尾幂等检查：

```bash
bash codex/hooks/cleanup-run-state.sh --apply
```

Bug / Multi-PR route 若没有 budget file，脚本仍会清理已有 scope / prompt / result 临时文件；目录不存在时直接通过。
