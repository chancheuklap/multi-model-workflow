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

临时文件由 `cleanup-before-push.sh` PreToolUse hook 自动清理——`git push` 或 `gh pr create` 执行前，hook 删除 `.codex/multi-model-workflow/` 下的 active-run-id、budget、scope 文件。

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

Generated with Codex + multi-model-workflow
```

## Step 22a：退出工作树

Push + PR 完成后，退出工作树：

1. `ExitWorktree({ action: "keep" })` — 保留工作树（PR 可能需要后续修改）

工作树保留直到 PR 合并后由 `clean_gone` 统一清理（删除工作树 + 分支 + 残留状态文件）。

## Step 22b：事后补审（pending_post_push_reviews）

> **机器消费契约**：hotfix submode 先 push 后审，把"欠一次审"记成磁盘状态。Closing 必须兑付，否则不算完成。

Push + PR 完成后，读 workflow-state 的 `pending_post_push_reviews`：

```bash
jq '.pending_post_push_reviews' .codex/multi-model-workflow/workflow-state-<run_id>.json
```

| 状态 | 动作 |
| --- | --- |
| `[]`（空） | 无欠审 → 直接进 Step 23 |
| 非空（有条目） | **必须**对已 push 的 commit 派一次事后 regression review（走 `_shared/review-dispatch.md` 派发契约，Execution tier GPT-5.4 xhigh）。review 返回后由 Coordinator 验证结论（子代理必验），再清空数组：`state.sh update --run-id <run_id> --field '.pending_post_push_reviews' --value '[]'`。**数组非空时 Closing 不返回完成 verdict** |

补审发现新问题 → 按 finding 派修复并补 commit（生产已 push，修复作为后续 commit），再清空。补审清空后才进 Step 23。

## Step 23：Report to User

一到两句话汇报。不做长篇总结。

---
> **流程到此结束**。orchestrate-workflow 返回 verdict，不再读取其他 reference。
