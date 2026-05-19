# External Review Lanes

> **Lookup**：任意 phase 准备派发 baseline review 或 release review 前读取。

Codex 有三条 review lane。Coordinator 必须按成本和独立性选择，并在 gate 结果里写明实际使用了哪条。

| Lane | 用途 | 计费/额度 | 使用方式 |
| --- | --- | --- | --- |
| External Claude subscription runner | 默认 cross-model review lane；固定 `claude-opus-4-7` + `--effort high` | 普通 Claude Code CLI subscription path；不使用 `-p` / Agent SDK | `codex/reviewers/claude-subscription-review.sh` |
| Internal Codex reviewer | Claude runner 不可用时兜底 | Codex 当前会话额度 | `spawn_agent` 派 `code_reviewer` / `release_reviewer` |
| Claude non-interactive | 用户明确授权 Agent SDK credits / Extra Usage；固定 `claude-opus-4-7` + `--effort high` | Agent SDK / usage credits，不是 normal subscription pool | `codex/reviewers/claude-review.sh --allow-extra-usage` |

## 选择规则

- 默认自动执行：External Claude subscription runner。
- Claude reviewer lane 必须使用 `claude-opus-4-7` 和 `--effort high`；不得降级模型或 effort。
- External Claude runner 失败或 `claude` 不可用：回落到 Internal Codex reviewer，并在 gate 结果里写明未执行 cross-model review。Internal Codex reviewer 完成后由 Coordinator 手动调用 `codex/hooks/track-review-budget.sh`，`MULTI_MODEL_WORKFLOW_REVIEW_LANE=internal-codex`，`MULTI_MODEL_WORKFLOW_REVIEW_NAME=<gate>`。
- 用户明确授权 usage credits / Extra Usage：可以用 `claude-review.sh --allow-extra-usage` 自动调用。
- 不得调用 `claude -p`，除非用户明确授权 Agent SDK credits / Extra Usage。
- `claude ultrareview` 不是默认替代项；它是 usage credits 路径，只能在用户明确授权时使用。

## External Claude Subscription Runner

把当前 review dispatch prompt 写成文件后运行：

```bash
bash codex/reviewers/claude-subscription-review.sh \
  --prompt-file .codex/multi-model-workflow/review-prompts/<gate>.md \
  --output .codex/multi-model-workflow/review-results/<gate>-claude.md \
  --review-name <gate>
```

Runner 默认只给 Claude `Read,Grep,Glob`，不启用写文件或 shell 命令。成功返回后 runner 会调用 `codex/hooks/track-review-budget.sh` 递增 `budget_used` 并写入 dispatch ledger。Claude findings 返回后，Coordinator 按当前 phase 的 disposition rules 亲验每条 finding。外部 reviewer 的结论不能直接变成 repair。

## Internal Codex Fallback Budget Recording

Internal Codex reviewer fallback 不经过 external runner。收到 `code_reviewer` / `release_reviewer` 结果后，Coordinator 立刻运行：

```bash
MULTI_MODEL_WORKFLOW_REVIEW_LANE=internal-codex \
MULTI_MODEL_WORKFLOW_REVIEW_NAME=<gate> \
  bash codex/hooks/track-review-budget.sh
```

## Reporting

每个 review gate 汇报：

- Lane used: external Claude subscription runner / internal Codex / Claude non-interactive extra usage。
- Reviewer result path 或 internal reviewer transcript。
- 是否执行 cross-model review。
- 如果 fallback 到 internal Codex，写明原因：no Claude findings / no user authorization / Claude bridge failed / cost policy.
