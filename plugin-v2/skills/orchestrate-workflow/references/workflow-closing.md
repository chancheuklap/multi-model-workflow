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

## Step 23：Report to User

一到两句话汇报。不做长篇总结。

## Step 24：Cleanup

```bash
rm .claude/multi-model-workflow/active-run-id
rm .claude/multi-model-workflow/budget-<run_id>.json
rm .claude/multi-model-workflow/scope-<run_id>.md
```

Bug / Multi-PR route 只删 scope file（无 budget file）。
